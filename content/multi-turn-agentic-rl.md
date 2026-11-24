# 多轮 Agentic RL：奖励、信用分配与实践

论文：https://arxiv.org/abs/2510.01132
##### 1. Multi-turn Agentic RL：任务建模
多轮 Agent RL 的核心是让 LLM 在环境中持续决策，而不是只完成一次静态问答。
涉及三种能力：
- **Long-Horizon Planning**：为长期目标规划多个相互关联的步骤。
- **Sequential Decision-Making**：根据环境反馈动态决定下一步动作。
- **Multi-turn Reward Optimization**：优化一系列动作的长期累计奖励。
需要区分：一次用户查询中多次调用工具，也可能被称为多轮交互，但真正的 Multi-turn Agentic RL 更强调跨步骤决策和长期奖励优化。
<img src="/images/obsidian/78ff4db4b936.png" alt="MultiTurnRL_图1_研究框架.png" width="680" />
Figure 1：Multi-turn Agentic RL 研究框架，从 Environment、Multi-turn Policy、Reward 三个维度提出七个研究问题。
###### 1.1 策略与动作采样
$$
\boxed{a_t\sim\pi_\theta(\cdot\mid h_t)}
$$
- $h_t$：当前交互历史，包括任务、之前的动作和环境反馈。
- $\pi_\theta(\cdot\mid h_t)$：给定历史时所有可能动作的概率分布。
- $\pi_\theta(a_t\mid h_t)$：选择具体动作 $a_t$ 的概率。
- $\sim$：按概率采样，不一定选择概率最高的动作。
###### 1.2 LLM 与环境的交互形式
多轮交互可以表示为 Chat Template：
```text
User: Task + Observation 0
Assistant: Action 0
User: Observation 1
Assistant: Action 1
...
```
每轮模型生成动作，环境执行后返回新的 Observation、Reward 和 Done，再继续下一轮。
**训练时：**
- Observation 来自环境，不是模型生成的动作，需要 Mask。
- 环境奖励可以分配到动作结束 Token `<|im_end|>`。
- 一次完整交互形成一条 Rollout（Trajectory）。
<img src="/images/obsidian/299bc2dfec2e.png" alt="MultiTurnRL_图3_TextWorld示例.png" width="600" />
Figure 3：TextWorld w2-o3-q4 任务示例。灰色为提示词，粗体为目标，蓝色为观测（User），橙色为动作（Assistant）。
##### 2. 多轮 RL 的奖励与信用分配
###### 2.1 Reward Density
- **Sparse Reward**：奖励稀疏，可能只有任务结束时才有奖励。
- **Dense Reward**：奖励稠密，中间步骤也能获得反馈。
稀疏奖励的问题是：最终任务成功或失败，无法直接说明具体哪一步动作值得奖励或惩罚。
这就是 **Credit Assignment** 问题。
###### 2.2 Token-Level Credit Assignment
多轮 PPO 通过 Critic 和 GAE，将后续奖励转化为各个 Token 的 Advantage。
**TD Error：**
$$
\boxed{
\delta_t^i=r_t^i+\gamma V(h_t^{i+1})-V(h_t^i)
}
\tag{2}
$$
- $r_t^i$：当前 Token 的奖励。
- $V(h_t^i)$：Critic 预测的当前价值。
- $\gamma$：折扣因子。
TD Error 表示当前价值预测与一步奖励加下一状态估计价值之间的差异。
**GAE（Generalized Advantage Estimation）：**
$$
\boxed{
\hat A_t^i=\sum_{l=0}^{L-i}(\gamma\lambda)^l\delta_t^{i+l}
}
\tag{3}
$$
- $\hat A_t^i$：当前 Token 的优势。
- $\lambda$：控制后续 TD Error 的衰减程度。
**核心：即使奖励只出现在动作末尾，GAE 也能将奖励信号传递给前面的 Token。**
##### 3. 策略优化：PPO、GRPO、RLOO
###### 3.1 PPO：Critic + GAE + Clipping
PPO 使用 Critic 和 GAE 估计优势，再通过 Clipped Objective 更新策略：
$$
\boxed{
L^{CLIP}
=\mathbb E\left[
\sum_{t,i}
\min\left(
\rho_t^i\hat A_t^i,
\operatorname{clip}(\rho_t^i,1-\epsilon,1+\epsilon)\hat A_t^i
\right)
\right]
}
\tag{4}
$$
新旧策略的概率比：
$$
\boxed{
\rho_t^i=
\frac{\pi_\theta(a_t^i\mid h_t,a_t^{<i})}
{\pi_{\theta_{\mathrm{old}}}(a_t^i\mid h_t,a_t^{<i})}
}
\tag{5}
$$
- $a_t^i$：当前轮的第 $i$ 个 Token。
- $a_t^{<i}$：当前轮此前生成的 Token。
- $\rho_t^i$：新旧策略生成该 Token 的概率比。
- Clipping：限制策略更新幅度。
###### 3.2 GRPO：Group Relative Advantage
GRPO 不使用独立 Critic，而是在同一任务下采样多条 Rollout，通过组内奖励统计计算优势：
$$
A_i=\frac{R_i-\bar R}{\sigma_R}
$$
问题：当前轨迹的奖励也参与组内均值和标准差的计算，可能引入梯度估计偏差。
###### 3.3 RLOO：Leave-One-Out
RLOO 使用其他 Rollout 的平均奖励作为基线：
$$
\boxed{
A_i=R_i-\frac{1}{N-1}\sum_{j\ne i}R_j
}
$$
该基线不包含当前轨迹的奖励，因此在独立采样的标准 REINFORCE 设置下，能够保持策略梯度估计无偏。
###### 3.4 Biased vs. Unbiased
这里的偏差指 **Policy Gradient Estimation Bias**，即估计梯度的期望是否等于目标的真实梯度。
| 算法 | 主要特点 |
|---|---|
| PPO | Clipping 等机制可能引入偏差 |
| GRPO | 组内奖励归一化可能引入偏差 |
| RLOO | Leave-One-Out 基线支持无偏梯度估计 |

**有偏不一定效果差**：适当偏差可能降低方差，提高优化稳定性。
##### 4. 模型先验与训练效果归因
###### 4.1 Model Prior 与 Multi-turn SFT
- **Model Prior**：模型在 RL 前已有的知识、推理和工具使用能力。
- **Multi-turn SFT**：使用专家的多轮交互轨迹进行模仿学习。
- **Multi-turn RL**：利用环境反馈和奖励进一步优化策略。
论文关注：RL 的收益与初始模型能力、先前的 SFT 训练有什么关系。
###### 4.2 Multi-turn Formulation vs. Algorithmic Heuristics
**Multi-turn Formulation**：将连续环境交互、历史信息和长期奖励建模为统一的 RL 训练问题。
**Algorithmic Heuristics**：PPO、GRPO 等算法中的 Clipping、优势归一化和价值估计等优化技巧。
关键问题：性能提升来自多轮 RL 建模本身，还是特定算法技巧？
我们讨论的实验结论：
- RLOO 也能带来学习收益，说明多轮 RL 的有效性不完全依赖 PPO 的特殊技巧。
- PPO 表现更强、更稳定，说明算法的稳定化机制仍然重要。
<img src="/images/obsidian/32ab403db546.png" alt="MultiTurnRL_PPO与RLOO训练曲线.png" width="600" />
附录图：Qwen-2.5-1.5B 在 TextWorld w2-o3-q4 上用 PPO 与 RLOO 训练的奖励曲线。PPO 接近 1.0，RLOO 稳定在约 0.4，高于初始水平但明显弱于 PPO。
**结论：多轮 RL 建模本身有效，但具体策略优化算法会显著影响训练效果。**
##### 5. 任务难度与结果验证
###### 5.1 Solving Complexity vs. Verification Complexity
- **Solving Complexity**：找到正确解决方案的难度。
- **Verification Complexity**：验证已有解决方案是否正确的难度。
例如：修复程序 Bug 可能很难，但验证修复结果可以直接运行测试。
###### 5.2 Executable Unit Tests vs. Model-Based Proxy Signals
- **Executable Unit Tests**：实际执行测试，判断代码是否满足测试条件。
- **Model-Based Proxy Signals**：依赖另一个模型预测或评价结果是否正确。
区别：前者基于实际执行结果，后者基于近似评价。单元测试也受测试覆盖率限制。
<img src="/images/obsidian/1e96517c5477.png" alt="MultiTurnRL_图5_SWEGym示例.png" width="600" />
Figure 5：SWE-Gym getmoto 任务示例，Agent 通过多轮读代码、改代码完成修复，最终由单元测试验证。
##### 6. 核心总结
这篇论文重点讨论了 Multi-turn Agentic RL 的实际训练机制：
1. **多轮建模**：Agent 根据历史和环境反馈进行连续决策。
2. **信用分配**：通过 TD Error 和 GAE，将长期奖励转化为 Token-Level Advantage。
3. **策略优化**：PPO、GRPO、RLOO 在优势估计、偏差和训练稳定性方面存在差异。
4. **性能归因**：多轮 RL 本身能够带来学习收益，但算法技巧也会影响训练效果。
**核心洞察：多轮 Agent RL 不只是对单轮语言模型应用 RL，而是要处理连续环境交互、跨步骤奖励以及长期决策的策略优化问题。**
