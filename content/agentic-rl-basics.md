# Agentic RL：任务建模与传统 RL 的区别

**Agentic RL 不是一种全新的 RL 算法，而是把强化学习应用到能够自主规划、调用工具、与环境交互的 AI Agent 上。**
##### 1. 传统 RL 的数学形式
传统强化学习通常使用 MDP：
$$
\boxed{a_t\sim\pi_\theta(\cdot\mid s_t)}
$$
- $s_t$：当前环境状态。
- $a_t$：Agent 选择的动作。
- $\pi_\theta$：需要训练的策略。
目标是最大化累计奖励：
$$
\boxed{
J(\theta)=\mathbb E_{\tau\sim\pi_\theta}
\left[\sum_{t=0}^{T}\gamma^t r_t\right]
}
$$
例如机器人学习走路，每一步根据身体状态选择动作，并最大化行走奖励。
##### 2. Agentic RL 的数学形式
对于 LLM Agent，策略通常根据**交互历史**决定下一步：
$$
\boxed{a_t\sim\pi_\theta(\cdot\mid h_t)}
$$
其中：
$$
h_t=(x,o_0,a_0,o_1,a_1,\ldots,o_t)
$$
- $x$：用户任务。
- $o_t$：环境观察，例如工具返回的信息。
- $a_t$：LLM 生成的动作，例如搜索、修改代码。
- $h_t$：截至当前的完整交互历史。
环境执行动作后产生反馈：
$$
(o_{t+1},r_t)\sim P(\cdot\mid h_t,a_t)
$$
训练目标仍然是：
$$
\boxed{
J_{\mathrm{Agentic}}(\theta)=\mathbb E_{\tau\sim\pi_\theta}
\left[\sum_{t=0}^{T}\gamma^t r_t\right]
}
$$
注意，**目标函数几乎没变**。区别主要是策略、动作和交互过程的具体形式。
##### 3. 两者到底有什么区别？
| 对比   | 一般 RL          | LLM Agentic RL  |
| ---- | -------------- | --------------- |
| 策略   | 神经网络等          | 通常是 LLM         |
| 输入   | 状态 $s_t$ 或观察历史 | 任务与交互历史 $h_t$   |
| 动作   | 移动、控制等         | 文本、工具调用、代码操作等   |
| 环境   | 游戏、机器人等        | 网页、代码库、工具、模拟环境等 |
| 奖励   | 即时或延迟          | 经常是任务完成后的稀疏奖励   |
| 优化目标 | 最大化累计奖励        | 最大化累计奖励         |

实际上，传统 RL 也可以处理长时程任务、部分可观测环境和稀疏奖励。这些不是 Agentic RL 独有的特征。
##### 4. 为什么 LLM Agentic RL 训练更复杂？
因为一次动作 $a_t$ 通常不是一个简单的离散动作，而是一整段 Token：
$$
a_t=(y_{t,1},y_{t,2},\ldots,y_{t,n})
$$
它的生成概率可以分解为：
$$
\boxed{
\pi_\theta(a_t\mid h_t)=
\prod_{j=1}^{n}
\pi_\theta(y_{t,j}\mid h_t,y_{t,<j})
}
$$
也就是说，**Agent 不仅要学习每一轮应该采取什么动作，还要通过 Token 生成这些动作。**
如果最终任务只获得一个奖励 $R$，训练还要考虑如何将奖励分配给不同轮次、不同 Token。
这正是下面三篇论文研究的问题：
- **GiGPO**：如何更准确地进行步骤级信用分配？
- **Practitioner's Guide**：多轮 Agent RL 如何建模和训练？
- **Agent Lightning**：如何把复杂 Agent 的执行过程转换成 RL 训练数据？
**一句话总结：RL 是底层数学框架；Agentic RL 是将这个框架用于多轮交互式 AI Agent。优化目标仍是最大化累计奖励，但策略通常由 LLM 表示，动作由 Token 生成，训练还需要处理工具反馈、多轮轨迹和信用分配。**
