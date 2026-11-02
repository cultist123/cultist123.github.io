# RoPE 与 YaRN：位置编码与长度外推

## RoPE 与 YaRN 的实现

RoPE: 位置编码,attention没有位置信息,需要把词的顺序放到模型里面.位置编码有相对和绝对位置编码,ROPE现在最长使用,对token进行旋转之后能包含位置信息

YaRN:外推,超出长度的序列,i是一对,2048的长度,给4000的长度就理解不了,参数不匹配,出现混乱的问题.解决这个问题的:方法1:把5000压缩至4096(乘一个0.5的系数的压缩,会损失一定的信息) 方法2: yarn是对高低频使用不同的方法,将注意力可覆盖的地方视作一个钟表,高频转的快,低频转的慢,YaRN让高频,不缩放,保持原样;中频,使用线性差值,平滑过渡,低频,线形缩放,是一种对超出长度的压缩分频率算法,引入了温度系数,softmax的时候会出现注意力稀释,引入温度系数,关键的保持高注意力,不关键进行缩放
$$
 \text{freqs}_i=\frac{1}{\text{rope\_base}^{\,2i/\text{dim}}}
$$
### 手撕RoPE
```python
def precompute_freqs_cis(dim:int,end:int=32*1024,rope_base:float=1e6,rope_scaling:Optional[dict]=None):
    #初始化rope频率
    freqs,attn_factor=(1.0/(rope_base**(torch.arange(0,dim,2)[:(dim//2)].float()/dim))),1.0
    #需要用到yarn
    if rope_scaling is not None:
        orig_max,factor,beta_fast,beta_slow=(
            rope_scaling["original_max_position_embeddings"],
            rope_scaling["factor"],
            rope_scaling["beta_fast"],
            rope_scaling["beta_slow"],
        )
        #推断的长度大于训练长度, 使用缩放
        if end > orig_max:
            #波长b到i的映射
            inv_dim=lambda b :(dim*math.log(orig_max/(b*2*math.pi)))/(2*math.log(rope_base))
            #划分高低维度
            #fast:不需要缩放的高频部分
            #slow:需要缩放的低频部分
            fast=max(math.floor(inv_dim(beta_fast)),0)
            slow=min(math.ceil(inv_dim(beta_slow)),dim//2 -1)
            #计算缩放因子
            #fast之前,ramp为0,在slow之后,ramp为1,在(fast,slow)之间,线性过渡
            ramp = torch.clamp(
                (torch.arange(dim//2,device=freqs.device).float()-fast)
                /max(slow-fast,0.001),
                0,
                1,
            )
            # 当 ramp=0 时（高频/快组）：系数为 1，保持原频率不变
            # 当 ramp=1 时（低频/慢组）：系数为 1/factor，频率缩小 factor 倍（波长拉长），即位置插值
            # 当 ramp 在 0~1 之间时：在两者之间线性过渡
            freqs=freqs*(1-ramp+ramp/factor)
    #根据end,生成位置索引t
    t=torch.arange(end,device=freqs.device).float()
    #计算外积,将t和频率部分相乘,得到每个位置的旋转角度
    freqs=torch.outer(t,freqs).float()
    freqs_cos=torch.cat([torch.cos(freqs),torch.cos(freqs)],dim=-1)*attn_factor
    freqs_sin=torch.cat([torch.sin(freqs),torch.sin(freqs)],dim=-1)*attn_factor
    return freqs_cos,freqs_sin
#编写RoPE
def apply_rotary_pos_emb(q,k,cos,sin,position_ids=None,unsqueeze_dim=1):
    #[a,b]->[-b,a]
    def rotate_half(x):
        #x.shape[-1]取最后一个维度的大小
        #x[...,x.shape[-1]//2:]取出x的后半部分
        #x[...,:x.shape[-1]//2]取出x的前半部分
        return torch.cat(
            [-x[...,x.shape[-1]//2:],x[...,:x.shape[-1]//2]],dim=-1
            )
    #x_rotated=x*cos+rotate_half(x)*sin
    q_embed = (q * cos.unsqueeze(unsqueeze_dim)) + (rotate_half(q) * sin.unsqueeze(unsqueeze_dim))
    k_embed = (k * cos.unsqueeze(unsqueeze_dim)) + (rotate_half(k) * sin.unsqueeze(unsqueeze_dim))

    return q_embed,k_embed
```

## 旋转、频率与长度外推

#### 二维向量旋转
向量 $\mathbf{x}=[x,\ y]^T$ 逆时针旋转 $\theta$：$\mathbf{x}'=R_\theta\mathbf{x}$，其中
$$
R_\theta=\begin{bmatrix}\cos\theta & -\sin\theta\\ \sin\theta & \cos\theta\end{bmatrix},\qquad
\begin{cases}x'=x\cos\theta-y\sin\theta\\ y'=x\sin\theta+y\cos\theta\end{cases}
$$
旋转只改变方向，不改变长度。(这个式子可以画图)
#### RoPE 中 Q 和 K 的旋转
位置 $m$ 的 query、位置 $n$ 的 key 分别旋转：$q'_m=R_mq$，$k'_n=R_nk$。Attention 点积为：
$$
\begin{aligned}
\langle q'_m,k'_n\rangle = (q'_m)^Tk'_n &= (R_mq)^T(R_nk) && (AB)^T=B^TA^T\\
&= q^TR_m^TR_nk && R_m^T=R_{-m}\\
&= q^TR_{-m}R_nk \\
&= \boxed{q^TR_{n-m}k}
\end{aligned}
$$
点积只取决于相对位置 $n-m$，而不是单独的 $m$ 和 $n$。RoPE 正是通过旋转 Q 和 K，把绝对位置转换成 attention 中的相对位置信息。

#### RoPE 频率
**分组**：$d$ 维向量两两配对成 $d/2$ 组，组号 $i$：
$$
[\underbrace{x_1,x_2}_{i=0},\ \underbrace{x_3,x_4}_{i=1},\ \dots,\ \underbrace{x_{d-1},x_d}_{i=d/2-1}]
$$
**转速**（固定，不学习，组号越大越慢）：
$$
\theta_i=10000^{-2i/d}
$$
**位置 $m$ 第 $i$ 组的旋转角度**：
$$
\theta_{m,i}=m\cdot\theta_i=m\cdot10000^{-2i/d}
$$
**点积时的角度差**（只剩相对距离）：
$$
n\theta_i-m\theta_i=(n-m)\,\theta_i
$$
**转满一圈所需距离**：
$$
L_i=\frac{2\pi}{\theta_i}=2\pi\cdot10000^{2i/d}
$$

| $i$（$d=8$） | $\theta_i$            | $L_i=2\pi/\theta_i$ | 6000 token 内圈数 | 覆盖范围   | 精度         |
| ---------- | --------------------- | ------------------- | -------------- | ------ | ---------- |
| 0          | $10000^{0}=1$         | ≈ 6                 | ≈ 1000         | 6 以内   | 高（类比秒针）距离近 |
| 1          | $10000^{-0.25}=0.1$   | ≈ 63                | ≈ 95           | 63 以内  | ↓          |
| 2          | $10000^{-0.5}=0.01$   | ≈ 628               | ≈ 10           | 628 以内 | ↓          |
| 3          | $10000^{-0.75}=0.001$ | ≈ 6283              | < 1            | 全部     | 低（类比时针）距离远 |

**要点**
- 一组能看清的范围 ≈ 它转一圈的距离 $L_i$。慢组一圈覆盖整个上下文，每个距离角度唯一，所以能"看到全部"，但相邻 token 角度只差 $\theta_i$，精度低。
- 距离超过 $L_i$ 后第 $i$ 组无法区分；能区分的最远距离 ≈ 最慢组的 $L_{d/2-1}$。
- 快组远距离会"乱"，但所有组合起来看，每个距离组合唯一，不会混（类比钟表的时针分针）。
- 底数 10000 越大，$L_i$ 越长，可区分距离越远（长上下文模型会调大）。
- 角度差只编码位置，不编码语义。

#### RoPE 高效实现与点积示例
##### 1. 逐元素实现（不构造旋转矩阵）

$$
q_m^{\text{rope}}=
\begin{bmatrix}q_0\\q_1\\q_2\\q_3\\\vdots\end{bmatrix}\odot
\begin{bmatrix}\cos m\theta_0\\\cos m\theta_0\\\cos m\theta_1\\\cos m\theta_1\\\vdots\end{bmatrix}+
\begin{bmatrix}-q_1\\q_0\\-q_3\\q_2\\\vdots\end{bmatrix}\odot
\begin{bmatrix}\sin m\theta_0\\\sin m\theta_0\\\sin m\theta_1\\\sin m\theta_1\\\vdots\end{bmatrix}
$$

每组结果与旋转矩阵相同：$(q_0\cos m\theta_0-q_1\sin m\theta_0,\ \ q_1\cos m\theta_0+q_0\sin m\theta_0)$
##### 2. 点积示例：$q=k=$ 全 1
$q$ 在位置 $0$（不旋转），$k$ 在位置 $n$。$k$ 每组旋转后为 $(\cos n\theta_i-\sin n\theta_i,\ \cos n\theta_i+\sin n\theta_i)$，与 $(1,1)$ 点积得 $2\cos n\theta_i$：
$$
\langle q_0^{\text{rope}},k_n^{\text{rope}}\rangle=\sum_{i=0}^{d/2-1}2\cos(n\theta_i)
$$
$d=4$（$\theta_0=1,\ \theta_1=0.01$）：
$$
f(n)=2\cos n+2\cos(0.01n)
$$
很明显看出分出来快慢组

| 分量 | 作用 |
|---|---|
| $2\cos n$（快） | 约 6 token 一个周期，只描述近距离 |
| $2\cos(0.01n)$（慢） | 约 628 token 一个周期，决定整体走势 |
**结论**：$n=0$ 时最大（$=d$），距离增大整体下降 → **远程衰减**，离得越远注意力越弱；$d$ 越大，远处快组相互抵消，衰减越平滑。


### 问题与思路
训练长度 $L$，想扩展到 $L'=sL$（$s$ 为扩展倍数）。超出 $L$ 后，**慢组**（训练时不到一圈）出现没见过的角度，模型失效；**快组**（已转很多圈）角度都见过，本身没问题。

| 方法        | 做法                                | 快组            | 慢组               |
| --------- | --------------------------------- | ------------- | ---------------- |
| PI（位置插值）  | 所有组 $\theta_i\to\theta_i/s$       | ❌ 被误伤，近距离精度下降 | ✅ 映射回见过的区间       |
| NTK-aware | 增大底数 $\text{base}\to\text{base}'$ | ✅ 基本不变        | ⚠️ 调整不精确，部分仍越界   |
| **YaRN**  | 按圈数分组处理                           | ✅ 不变          | ✅ 按比例放慢，映射回见过的区间 |
所以解决方法是：快组不变（角度都见过），慢组按比例放慢，映射回训练时见过的区间。比暴力地把所有指针都放慢更精细。

### YaRN 做法 1：按组区别对待（NTK-by-parts）
**波长**（第 $i$ 组转一圈需要的 token 数）与**训练长度内的圈数**：
$$
\lambda_i=\frac{2\pi}{\theta_i}=2\pi\cdot\text{base}^{2i/d},\qquad r_i=\frac{L}{\lambda_i}
$$
**论文版**（对圈数 $r_i$ 线性过渡）：
$$
\theta_i'=(1-\gamma_i)\frac{\theta_i}{s}+\gamma_i\,\theta_i,\qquad
\gamma_i=\begin{cases}0 & r_i<\alpha\\[2pt] \dfrac{r_i-\alpha}{\beta-\alpha} & \alpha\le r_i\le\beta\\[4pt] 1 & r_i>\beta\end{cases}
$$
（LLaMA 取 $\alpha=1,\ \beta=32$）
- 圈数多（快组）：$\gamma=1$，不变
- 不到一圈（慢组）：$\gamma=0$，完全插值 $\theta_i/s$
- 中间：线性过渡

**代码版**（对组号 $i$ 线性过渡，官方实现与 HF 均用此版）：
令 $r_i=b$ 反解 $i$（代码中的 `inv_dim`）：
$$
i(b)=\frac{d\cdot\ln\dfrac{L}{2\pi b}}{2\ln(\text{base})},\qquad
\rho_i=\text{clamp}\!\left(\frac{i-\lfloor i(32)\rfloor}{\lceil i(1)\rceil-\lfloor i(32)\rfloor},0,1\right),\qquad
\theta_i'=\theta_i\Big(1-\rho_i+\frac{\rho_i}{s}\Big)
$$
即 $\rho=1-\gamma$（代码 `ramp`），两版只在过渡区不同。
**例子**：$d=8$，$L=2048\to8192$（$s=4$），边界 $i(32)\approx1.0$，$i(1)\approx2.5$

| $i$ | $\theta_i$ | $r_i$ | 论文 $\theta_i'$ | 代码 $\theta_i'$ |
|---|---|---|---|---|
| 0 | 1 | ≈ 326 | 1 | 1 |
| 1 | 0.1 | ≈ 32.6 | 0.1 | 0.1 |
| 2 | 0.01 | ≈ 3.3 | ≈ 0.0030 | 0.00625 |
| 3 | 0.001 | ≈ 0.33 | 0.00025 | 0.00025 |
### YaRN 做法 2：注意力温度
插值后点积分布变平，给 logits 乘缩放因子：
$$
\text{softmax}\!\left(\frac{q^Tk}{t\sqrt{d}}\right),\qquad \sqrt{1/t}=0.1\ln s+1
$$
代码中 $\sqrt{1/t}$ 即 `attn_factor`，乘在 cos、sin 上（当前代码固定为 1.0，未启用）。
**秒针不动，时针放慢**：快组保留近距离精度，慢组按倍数变慢以覆盖新长度，再用温度修正注意力分布。
