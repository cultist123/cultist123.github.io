# PPO：重要性采样、约束与 Clip

### 1. 为什么需要 PPO：On-policy vs Off-policy
**On-policy**：和环境互动的 actor 就是正在学的那个 actor，自己玩、自己学。
**Off-policy**：和环境互动的是另一个 actor，要学的 actor 在旁边看别人玩来学。
**比喻（棋灵王）**：阿光自己下棋自己学是 On-policy；佐为下、阿光在旁边看是 Off-policy。
<img src="/images/obsidian/a7873f0b569c.png" alt="Pasted image 20261031151745.png" width="384" />
前面的 Policy Gradient 是 On-policy：
$$\nabla \bar{R}_\theta = E_{\tau \sim p_\theta(\tau)}\big[R(\tau)\,\nabla \log p_\theta(\tau)\big]$$
**问题**：期望是对当前 $\theta$ 采样的轨迹算的。一旦 $\theta$ 更新，旧数据的分布就不对了，必须重新采样。所以每批数据只能用一次，大量时间花在收集数据上。
**目标**：用另一个 actor $\theta'$ 收集的数据来训练 $\theta$。因为 $\theta'$ 固定不变，同一批数据可以拿来更新 $\theta$ 很多次。
**工具**：Importance Sampling（重要性采样）。

---
### 2. Importance Sampling
<img src="/images/obsidian/d6c4b0471b15.png" alt="Pasted image 20261031151926.png" width="368" />
想算 $x$ 服从分布 $p$ 时 $f(x)$ 的期望，通常用采样平均来近似：
$$E_{x\sim p}[f(x)] \approx \frac{1}{N}\sum_{i=1}^{N} f(x^i),\quad x^i \sim p$$
**但如果没法从 $p$ 采样，只能从 $q$ 采样**，就做一个变形：
$$E_{x\sim p}[f(x)] = \int f(x)p(x)\,dx = \int f(x)\frac{p(x)}{q(x)}q(x)\,dx = E_{x\sim q}\Big[f(x)\frac{p(x)}{q(x)}\Big]$$
- 从 $q$ 采样，但每个样本乘上权重 $\dfrac{p(x)}{q(x)}$，用来修正两个分布的差异
- 理论上 $q$ 可以是任何分布（只要 $p$ 有值的地方 $q$ 也有值）
---
### 3. Importance Sampling 的问题：方差
<img src="/images/obsidian/0213945e537f.png" alt="Pasted image 20261031151945.png" width="367" />
期望相等，**方差不一定相等**。用 $\mathrm{Var}[X] = E[X^2] - (E[X])^2$ 算一下：
$$\mathrm{Var}_{x\sim p}[f(x)] = E_{x\sim p}[f(x)^2] - \big(E_{x\sim p}[f(x)]\big)^2$$
$$\mathrm{Var}_{x\sim q}\Big[f(x)\frac{p(x)}{q(x)}\Big] = E_{x\sim p}\Big[f(x)^2\frac{p(x)}{q(x)}\Big] - \big(E_{x\sim p}[f(x)]\big)^2$$
差别在第一项多乘了 $\dfrac{p(x)}{q(x)}$。如果 $p$ 和 $q$ 差很多，这个比值就会很大，方差就会很大。
**直观例子**：$p$ 的概率集中在左边，那里 $f(x)<0$；$q$ 的概率集中在右边，那里 $f(x)>0$。
- 采样很少时，从 $q$ 抽到的几乎全在右边，估出来的期望是正的，但真实答案是负的
- 只有偶然抽到一个左边的点，它的权重 $p/q$ 极大，才能把结果拉回负的
- 所以**样本够多时没问题，样本不够时结果可能差很多**
**结论**：$p$ 和 $q$ 不能差太多。
<img src="/images/obsidian/a51bf22bb5ff.png" alt="Pasted image 20261031151859.png" width="329" />

---
### 4. 把 Importance Sampling 用到 Policy Gradient
<img src="/images/obsidian/22de91c12929.png" alt="Pasted image 20261031152007.png" width="400" />
**轨迹层面**：用 $\theta'$ 和环境互动采样轨迹，再乘上权重：
$$\nabla \bar{R}_\theta = E_{\tau \sim p_{\theta'}(\tau)}\Big[\frac{p_\theta(\tau)}{p_{\theta'}(\tau)}R(\tau)\,\nabla \log p_\theta(\tau)\Big]$$
$\theta'$ 的工作就是"示范"给 $\theta$ 看，它收集的数据可以反复使用。
**实际按每个 (s, a) 算**（上一篇讲过，不是整局给同样的分数）：
On-policy 写法：
$$E_{(s_t,a_t)\sim\pi_\theta}\big[A^\theta(s_t,a_t)\,\nabla \log p_\theta(a_t|s_t)\big]$$
改成 Off-policy：
$$E_{(s_t,a_t)\sim\pi_{\theta'}}\Big[\frac{p_\theta(a_t|s_t)}{p_{\theta'}(a_t|s_t)}\frac{p_\theta(s_t)}{p_{\theta'}(s_t)}A^{\theta'}(s_t,a_t)\,\nabla \log p_\theta(a_t|s_t)\Big]$$
**注意 1**：advantage 要换成 $A^{\theta'}$，因为现在和环境互动的是 $\theta'$。
**注意 2**：$\dfrac{p_\theta(s_t)}{p_{\theta'}(s_t)}$ 直接删掉。理由：
- 假设两个 actor 看到某个画面的概率差不多
- 而且 $p_\theta(s_t)$ 本来就很难算
**得到新的目标函数**：利用 $\nabla f(x) = f(x)\nabla \log f(x)$，把上面的梯度"反推"回去：
$$J^{\theta'}(\theta) = E_{(s_t,a_t)\sim\pi_{\theta'}}\Big[\frac{p_\theta(a_t|s_t)}{p_{\theta'}(a_t|s_t)}A^{\theta'}(s_t,a_t)\Big]$$
- $\theta$：要优化的参数
- $\theta'$：真正去和环境互动、收集数据的参数
**但第 3 节说过**：$\theta$ 和 $\theta'$ 不能差太多，否则结果不准。PPO 就是在处理这件事。
---
### 5. PPO / TRPO：加约束
<img src="/images/obsidian/550dd4e150ba.png" alt="Pasted image 20261031152031.png" width="389" />
**PPO**：把"别差太多"直接写进目标函数，当作惩罚项：
$$J^{\theta'}_{PPO}(\theta) = J^{\theta'}(\theta) - \beta\,KL(\theta,\theta')$$
然后照常用 gradient ascent 最大化。
**TRPO**（PPO 的前身）：把 KL 当成额外的约束条件：
$$J^{\theta'}_{TRPO}(\theta) = J^{\theta'}(\theta),\quad KL(\theta,\theta') < \delta$$
带约束的优化在基于梯度的方法里不好处理，所以实现起来麻烦。
**结论**：两者效果差不多，但 PPO 好实现得多。
**特别注意**：$KL(\theta,\theta')$ **不是参数之间的距离，而是行为上的距离**。
- 给同一个 state，两个 actor 各输出一个动作的概率分布
- 算这两个分布的 KL divergence，再对所有 state 平均
- **为什么不看参数距离**：参数变一点点，行为可能变很多，也可能几乎不变。我们真正在意的是动作分布差多少
---
### 6. PPO 算法流程
<img src="/images/obsidian/022dee7f8f56.png" alt="Pasted image 20261031152049.png" width="356" />
1. 初始化 policy 参数 $\theta^0$
2. 每次迭代：
   3. 用 $\theta^k$ 和环境互动，收集一堆 $(s_t,a_t)$，算出 $A^{\theta^k}(s_t,a_t)$
   4. 优化目标函数，**可以用同一批数据更新 $\theta$ 很多次**：
   $$J^{\theta^k}_{PPO}(\theta) = J^{\theta^k}(\theta) - \beta\,KL(\theta,\theta^k)$$
   5. 动态调整 $\beta$（**Adaptive KL Penalty**）：
      - 如果 $KL(\theta,\theta^k) > KL_{max}$：惩罚不够，**加大** $\beta$
      - 如果 $KL(\theta,\theta^k) < KL_{min}$：惩罚太强，**减小** $\beta$
---
### 7. PPO2：用 Clip 代替 KL
<img src="/images/obsidian/ce70538f6c9f.png" alt="Pasted image 20261031152110.png" width="338" />
**动机**：PPO 还要算 KL divergence，有点麻烦。PPO2 公式看起来复杂，但实现很简单：
$$J^{\theta^k}_{PPO2}(\theta) \approx \sum_{(s_t,a_t)}\min\Big(\frac{p_\theta(a_t|s_t)}{p_{\theta^k}(a_t|s_t)}A^{\theta^k}(s_t,a_t),\ \mathrm{clip}\Big(\frac{p_\theta(a_t|s_t)}{p_{\theta^k}(a_t|s_t)},1-\epsilon,1+\epsilon\Big)A^{\theta^k}(s_t,a_t)\Big)$$
**clip 的作用**：把比值限制在 $[1-\epsilon,\,1+\epsilon]$ 里
- 比值 $< 1-\epsilon$ → 输出 $1-\epsilon$
- 比值 $> 1+\epsilon$ → 输出 $1+\epsilon$
- 在中间 → 原样输出
- $\epsilon$ 是超参数，比如 0.1 或 0.2
**直观意思**（记比值为 $r = p_\theta / p_{\theta^k}$）：
- **$A > 0$（好动作）**：希望 $p_\theta(a_t|s_t)$ 越大越好，但 $r$ 一旦超过 $1+\epsilon$ 就没好处了，不会再往上推
- **$A < 0$（坏动作）**：希望 $p_\theta(a_t|s_t)$ 越小越好，但 $r$ 一旦低于 $1-\epsilon$ 就没好处了，不会再往下压
- **min 的作用**：如果 $\theta$ 往"错误方向"走了（比如好动作的概率反而变小），min 会取没被截断的那一项，保留梯度把它拉回来
一句话：**每次更新只能小步改，不让 $\theta$ 离 $\theta^k$ 太远。**
---
### 8. 公式演进总结

| 版本 | 目标 / 梯度 | 解决的问题 |
|---|---|---|
| Policy Gradient | $E_{\pi_\theta}\big[A^\theta\,\nabla\log p_\theta(a_t\vert s_t)\big]$ | — |
| + Importance Sampling | $E_{\pi_{\theta'}}\Big[\frac{p_\theta(a_t\vert s_t)}{p_{\theta'}(a_t\vert s_t)}A^{\theta'}\Big]$ | 数据只能用一次，太费时间 |
| TRPO | 同上，且 $KL(\theta,\theta')<\delta$ | 两个分布差太多，估计不准 |
| PPO | $J^{\theta'}(\theta)-\beta\,KL(\theta,\theta')$ | TRPO 的约束难优化 |
| PPO2 | $\min(r\,A,\ \mathrm{clip}(r,1\pm\epsilon)\,A)$ | 不用算 KL，更简单 |
整条线的核心：**想重复利用数据 → 引入 importance sampling → 但分布不能差太多 → 用 KL 或 clip 把更新限制住。**
