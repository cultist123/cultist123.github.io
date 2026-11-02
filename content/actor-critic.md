# Actor-Critic：从策略梯度到 A2C 与 A3C

### 1. 回顾：Policy Gradient 的问题
$$\nabla \bar{R}_\theta \approx \frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T_n}\Big(\sum_{t'=t}^{T_n}\gamma^{t'-t} r_{t'}^n - b\Big)\nabla \log p_\theta(a_t^n|s_t^n)$$
把括号里的累积奖励记作 $G_t^n$：
$$G_t^n = \sum_{t'=t}^{T_n}\gamma^{t'-t} r_{t'}^n$$
**问题**：$G$ 是一个**随机变量**。环境有随机性，actor 采样动作也有随机性，所以同一个 $(s_t, a_t)$ 玩很多次，得到的 $G$ 可能差很多。
- 我们每次只采样到 $G$ 的一个值，就拿它来更新参数
- 样本不够多时，这个值很不稳定（方差大），训练就会抖
**想法**：别用采样到的 $G$，直接估计 $G$ 的**期望值**来代替它。
---
### 2. 回顾：Value-based 方法
估计期望值正是 value-based 方法（Q-learning）在做的事：
- **State value function $V^\pi(s)$**：输入 $s$，输出一个数。表示从 $s$ 开始，一直用 $\pi$ 玩到结束，期望能拿多少累积奖励
- **State-action value function $Q^\pi(s,a)$**：在 $s$ 先做 $a$，之后都用 $\pi$，期望能拿多少累积奖励
  - 离散动作时，可以写成输入 $s$、输出每个动作各自的 Q 值
**估计方法**：
- **MC**：玩完整局再算，估计是准的（无偏），但方差大
- **TD**：只看一步 $r_t + V(s_{t+1})$，方差小、比较稳，但依赖 V 本身估得准不准
---
### 3. Actor-Critic：用 Q 和 V 换掉 G 和 b
**$G$ 的期望就是 Q**：
$$E\big[G_t^n\big] = Q^{\pi_\theta}(s_t^n, a_t^n)$$
**baseline 用 V**：
$$b = V^{\pi_\theta}(s_t^n)$$
所以权重变成：
$$Q^{\pi_\theta}(s_t^n, a_t^n) - V^{\pi_\theta}(s_t^n)$$
**为什么 V 适合当 baseline**：V 不考虑具体做了哪个动作，等于 Q 对所有动作取平均。所以 $Q - V$ 有正有负：
- 这个动作比平均好 → 正 → 提高它的概率
- 比平均差 → 负 → 降低它的概率
**缺点**：要同时估计 Q 和 V 两个网络，估不准的风险变成两倍。
---
### 4. Advantage Actor-Critic（A2C）：只估一个 V
**把 Q 用 V 表示**：在 $s_t$ 做 $a_t$，会拿到奖励 $r_t$，跳到 $s_{t+1}$，之后的期望就是 $V(s_{t+1})$：
$$Q^\pi(s_t^n, a_t^n) = E\big[r_t^n + V^\pi(s_{t+1}^n)\big]$$
外面要取期望，是因为 $r_t$ 和 $s_{t+1}$ 都有随机性。
**直接把期望拿掉**：
$$Q^\pi(s_t^n, a_t^n) - V^\pi(s_t^n) \approx r_t^n + V^\pi(s_{t+1}^n) - V^\pi(s_t^n)$$
这一项就是 **Advantage Function**，也就是上一篇最后说的 $A^\theta(s_t, a_t)$。
- **好处**：只需要估计 V 一个网络
- **代价**：$r_t$ 是随机的，拿掉期望会引入一些方差。但 $r_t$ 只是**一步**的奖励，$G$ 是**之后所有步**的奖励总和，所以它的方差比 $G$ 小得多
**特别注意**：为什么拿掉期望可以，**不是严格推导出来的**。A3C 原论文试过各种写法，这种效果最好，是实验结果。
---
### 5. A2C 训练流程
1. 用当前的 actor $\pi$ 和环境互动，收集数据
2. **先用这批数据估计 $V^\pi$**（可以用 TD 或 MC）
3. 用 V 算出每一步的权重，更新 actor $\pi \rightarrow \pi'$：
$$\nabla \bar{R}_\theta \approx \frac{1}{N}\sum_{n=1}^{N}\sum_{t=1}^{T_n}\big(r_t^n + V^\pi(s_{t+1}^n) - V^\pi(s_t^n)\big)\nabla \log p_\theta(a_t^n|s_t^n)$$
4. 用 $\pi'$ 重新收集数据，回到第 2 步
**和普通 Policy Gradient 的区别**：普通 PG 拿到数据直接更新 actor；A2C 先训练 critic（V），再让 critic 来给 actor 的每个动作打分。
---
### 6. 实现技巧
**Tip 1：共享前面几层**
- 有两个网络：actor 输入 $s$、输出动作的概率分布；critic 输入 $s$、输出一个数 $V(s)$
- 输入都是 $s$，所以前面几层可以共用
- 如果输入是画面，共用的几层负责把像素变成比较高级的特征，后面再分成两个头
**Tip 2：鼓励探索**
- 和 Q-learning 一样需要 exploration
- 常见做法：对 actor 输出的分布加约束，**不让它的 entropy 太小**
- entropy 大 = 各动作的概率比较平均 = 会多尝试不同的动作
---
### 7. A3C（Asynchronous Advantage Actor-Critic）
**比喻（火影）**：鸣人用影分身修炼，每个分身各自练，最后经验全部汇总回本体。
**流程**：
1. 有一个 **global network**，包含 actor 和 V，参数是 $\theta^1$
2. 开很多个 **worker**（影分身），每个 worker 开工前先复制 global 的参数
3. 每个 worker 各自和环境互动，收集数据
   - 要收集到多样的数据，每个 worker 的初始设置要不一样
4. worker 用自己的数据算梯度 $\Delta\theta$
5. 把梯度传回 global network 更新：$\theta^1 \leftarrow \theta^1 + \eta\,\Delta\theta$
**注意**：原投影片这里把梯度写成 $\nabla\theta$，符号不太对，意思就是 worker 算出来的那份梯度。
**Asynchronous（异步）的意思**：
- 所有 worker 同时并行跑，谁算完谁就回传
- worker 开工时复制的是 $\theta^1$，回传时 global 可能已经被别人更新成 $\theta^2$ 了
- **没关系，照样直接加上去**
- 好处是快：多个 worker 同时收集数据
---
### 8. 和 GAN 的联系
论文：*Connecting Generative Adversarial Networks and Actor-Critic Methods*（Pfau & Vinyals, 2016）
- GAN 和 actor-critic 都出了名的难训练
- 论文整理了两边各有哪些训练技巧，哪些在另一边还没试过，可以互相借鉴
---
### 9. 公式演进总结

| 方法                     | 每个动作的权重 / 做法                        | 解决的问题                                 |
| ---------------------- | ----------------------------------- | ------------------------------------- |
| Policy Gradient        | $G_t^n - b$                         | —                                     |
| Actor-Critic           | $Q^\pi(s_t,a_t) - V^\pi(s_t)$       | $G$ 是采样值，方差大 → 用期望代替                  |
| A2C                    | $r_t + V^\pi(s_{t+1}) - V^\pi(s_t)$ | 要估 Q、V 两个网络 → 只估 V                    |
| A3C                    | 多个 worker 并行、异步回传梯度                 | 收集数据太慢                                |
整条线的核心：**$G$ 太随机 → 用 critic 估计的期望值代替 → actor 负责做动作，critic 负责打分（甚至直接指导方向）。**
