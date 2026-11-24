# Flow Matching：从噪声到数据的速度场

论文：https://arxiv.org/abs/2210.02747
##### 1. 核心思想：学习从噪声到数据的速度场
Flow Matching（FM）是一种训练 Continuous Normalizing Flow（CNF）的方法。
CNF 利用连续时间的速度场，将简单分布 $p_0$ 转换为 $p_1$，使 $p_1\approx q$（$q$ 为真实数据分布）：
$$
\frac{d}{dt}\phi_t(x)=v_t(\phi_t(x)),\qquad \phi_0(x)=x
$$
其中：
- $v_t(x)$：向量场，决定位置 $x$ 在时间 $t$ 的移动速度。
- $\phi_t(x)$：流映射，表示初始位置 $x$ 经过连续运动后的新位置。
- $p_t=[\phi_t]_*p_0$：样本经过流映射后产生的概率分布。
概率密度通过变量变换公式计算：
$$
p_t(x)=p_0(\phi_t^{-1}(x))
\left|\det J_{\phi_t^{-1}}(x)\right|
$$
逆映射找到样本原来的位置，Jacobian 行列式修正局部空间拉伸或压缩造成的密度变化，保证概率质量守恒。
**CNF 定义连续生成过程，FM 负责学习其中的速度场。**
##### 2. 核心问题：如何监督全局速度场？
理想的 FM 训练目标为：
$$
\mathcal L_{\mathrm{FM}}(\theta)
=\mathbb E_{t,x\sim p_t}
\|v_\theta(x,t)-u_t(x)\|^2
\tag{5}
$$
- $v_\theta(x,t)$：神经网络预测的速度。
- $u_t(x)$：目标概率路径对应的真实速度场。
难点：全局概率路径 $p_t$ 和对应的全局速度 $u_t(x)$ 通常难以直接计算。
###### Conditional Flow Matching（CFM）
作者不直接构造全局速度场，而是先固定一个真实样本 $x_1\sim q$，构造：
- $p_t(x\mid x_1)$：给定目标样本 $x_1$ 时，当前位置 $x$ 的条件概率密度。
- $u_t(x\mid x_1)$：对应的条件速度场。
全局分布是条件分布的边缘化：
$$
p_t(x)=\int p_t(x\mid x_1)q(x_1)\,dx_1
\tag{6}
$$
全局速度是条件速度的加权平均：
$$
u_t(x)=\mathbb E[u_t(x\mid x_1)\mid x,t]
\tag{8}
$$
因此可以使用更容易计算的 CFM 目标：
$$
\boxed{
\mathcal L_{\mathrm{CFM}}(\theta)
=\mathbb E_{t,x_1\sim q,x\sim p_t(\cdot\mid x_1)}
\|v_\theta(x,t)-u_t(x\mid x_1)\|^2
}
\tag{9}
$$
**定理 2**：FM 与 CFM 的损失相差一个与 $\theta$ 无关的常数，因此：
$$
\nabla_\theta\mathcal L_{\mathrm{FM}}
=\nabla_\theta\mathcal L_{\mathrm{CFM}}
$$
即：**用条件速度作为监督，可以学习同一个全局速度场。**
直观理解：MSE 的最优解是条件期望。例如同一位置 $x$ 处两个条件速度分别为 2 和 8、概率各 0.5，最小化 $0.5(v-2)^2+0.5(v-8)^2$ 得到 $v=5$，正好等于式 (8) 的全局速度。
注意：模型输入只有 $(x,t)$，$x_1$ 用于训练时构造监督信号，并不是模型必须知道的目标位置。
##### 3. 如何构造条件路径：高斯分布
作者将条件概率路径定义为：
$$
p_t(x\mid x_1)
=\mathcal N(x\mid\mu_t(x_1),\sigma_t^2(x_1)I)
\tag{10}
$$
其中 $\mu_t$ 控制分布中心，$\sigma_t$ 控制分布宽度。
边界条件：
- $t=0$：$\mu_0=0,\sigma_0=1$，标准高斯噪声。
- $t=1$：$\mu_1=x_1,\sigma_1=\sigma_{\min}$，集中在目标样本附近。
通过仿射流生成条件分布：
$$
\psi_t(x_0)=\sigma_t x_0+\mu_t,\qquad x_0\sim\mathcal N(0,I)
\tag{11}
$$
对时间求导并消去 $x_0$，得到条件速度场：
$$
\boxed{
u_t(x\mid x_1)
=\frac{\sigma'_t}{\sigma_t}(x-\mu_t)+\mu'_t
}
\tag{15}
$$
两部分含义：
- $\mu'_t$：分布中心的平移速度。
- $\frac{\sigma'_t}{\sigma_t}(x-\mu_t)$：分布收缩或扩张对应的速度。
因此，**只需要设计 $\mu_t$ 和 $\sigma_t$ 随时间的变化方式，就能构造条件概率路径和目标速度。**
##### 4. OT 条件概率路径：论文的关键构造
相比从扩散过程推导概率路径，作者直接让均值和标准差线性变化：
$$
\mu_t=tx_1,\qquad
\sigma_t=1-(1-\sigma_{\min})t
\tag{20}
$$
###### 4.1 路径：公式 (22)
代入仿射流：
$$
\boxed{
x_t=\psi_t(x_0)
=[1-(1-\sigma_{\min})t]x_0+tx_1
}
\tag{22}
$$
当 $\sigma_{\min}=0$ 时：
$$
\boxed{x_t=(1-t)x_0+tx_1}
$$
这是线性插值：对两个样本位置按比例组合，使样本沿直线从噪声点移动到真实数据点。
注意：
- 这里插值的是样本位置，不是对 $p_0$ 和 $p_1$ 的概率密度直接加权混合。
- 论文实际使用较小的 $\sigma_{\min}$，终点保留少量噪声。
###### 4.2 目标速度：公式 (23)
对公式 (22) 求导：
$$
\boxed{
\frac{dx_t}{dt}
=x_1-(1-\sigma_{\min})x_0
}
$$
对于固定的 $(x_0,x_1)$，该速度不随时间变化。
因此 CFM Loss 变为：
$$
\boxed{
\mathcal L_{\mathrm{CFM}}(\theta)
=\mathbb E_{t,x_0,x_1}
\left\|
v_\theta(x_t,t)
-\big[x_1-(1-\sigma_{\min})x_0\big]
\right\|^2
}
\tag{23}
$$
当 $\sigma_{\min}=0$ 时：
$$
\boxed{
\mathcal L_{\mathrm{CFM}}
=\mathbb E\|v_\theta(x_t,t)-(x_1-x_0)\|^2
}
$$
**训练流程**：
采样 $x_0,x_1,t$ → 构造 $x_t$ → 计算目标速度 → 网络预测速度 → MSE → 更新参数。
例如 $x_0=2,x_1=10,t=0.5$：
$$
x_t=6,\qquad u=8
$$
如果预测速度为 7，则 Loss 为 $(7-8)^2=1$。
###### 4.3 为什么称为 Optimal Transport？
对于本文构造的两个条件高斯分布，式 (22) 对应 Wasserstein-2 最优传输的位移插值。
特点：
- 每条条件轨迹是直线。
- 沿该轨迹的速度恒定。
- 条件向量场方向在固定位置和目标时不随时间改变。
<img src="/images/obsidian/08d7510fc688.png" alt="FlowMatching_图2_扩散Score与OT向量场.png" width="680" />
Figure 2：左为扩散路径的条件 Score，右为 OT 路径的条件向量场，各列对应不同时间；OT 向量场方向不随时间改变，只改变大小。
<img src="/images/obsidian/5317cb5a3156.png" alt="FlowMatching_图3_扩散与OT轨迹.png" width="360" />
Figure 3：扩散条件轨迹可能弯曲、折返；OT 条件轨迹沿直线移动。
**重要限制：条件路径是 OT，不代表边缘速度场对应的全局生成过程一定也是 OT。**
##### 5. Flow Matching 与 Diffusion 的本质区别
| | 典型 Diffusion | Flow Matching |
|---|---|---|
| 训练目标 | 预测噪声或 Score | 预测速度 |
| 监督信号 | 已知添加的噪声 | 条件路径的目标速度 |
| 路径选择 | 通常使用扩散噪声路径 | 支持扩散和 OT 等路径 |
| 生成 | 逐步求解反向动力学 | 求解学习到的 ODE |

典型扩散噪声预测损失：
$$
\mathcal L_{\mathrm{diff}}
=\mathbb E\|\epsilon_\theta(x_t,t)-\epsilon\|^2
$$
OT-CFM 速度预测损失：
$$
\mathcal L_{\mathrm{CFM}}
=\mathbb E\|v_\theta(x_t,t)-(x_1-x_0)\|^2
$$
FM 不代表一步生成。它的 **Simulation-Free** 是指训练时不必反复求解完整 ODE。
生成时仍从噪声开始，根据模型预测的速度数值积分：
$$
x_{t+\Delta t}
\approx x_t+v_\theta(x_t,t)\Delta t
$$
##### 6. 核心贡献
1. **Simulation-Free Training**：将 CNF 训练转换为速度场的监督回归，不必在训练中求解完整 ODE。
2. **Conditional Flow Matching**：利用容易构造的条件速度场监督模型，并证明其参数梯度与原始 FM 相同。
3. **OT Probability Path**：选择均值、标准差线性变化的高斯条件路径，使训练位置与目标速度都有简单的闭式表达。
**核心公式：**
$$
\underbrace{x_t=(1-t)x_0+tx_1}_{\text{构造训练位置}}
\qquad
\underbrace{u=x_1-x_0}_{\text{构造目标速度}}
$$
$$
\boxed{\mathcal L=\mathbb E\|v_\theta(x_t,t)-u\|^2}
$$
**一句话总结：Flow Matching 的关键是用条件概率路径构造可计算的速度监督，将连续生成模型的训练转化为简单的速度回归；OT 路径则进一步简化了训练目标的构造。**
