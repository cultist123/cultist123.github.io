# RAGEN：多轮 Agent 强化学习与训练稳定性

论文：https://arxiv.org/abs/2504.20073
#### 1. 研究背景与核心问题
传统 LLM 强化学习主要针对数学、代码等静态任务，通常通过单轮生成答案并计算 Reward 来优化模型。但交互式智能体（Interactive Agent）需要在动态环境中连续做出决策，并根据环境反馈调整行为。
主要挑战包括：
- **Long-Horizon Decision Making（长时程决策）**：需要连续执行多个步骤，前面的决策影响后续结果。
- **Stochastic Environment Feedback（随机环境反馈）**：同一个动作可能得到不同结果，智能体必须根据反馈调整策略。
- **Memory Across Turns（跨轮记忆）**：需要保留之前的观察、推理、动作和反馈。
- **Self-Evolution（自我演化）**：通过成功和失败的经验改善未来的决策策略，而不仅是完成当前任务。
**核心问题**：如何让 LLM 通过多轮环境交互进行 RL 训练，同时避免长轨迹和随机反馈造成训练不稳定、策略退化和推理能力下降？
#### 2. Agentic RL 的基本概念
**Interactive Agent（交互式智能体）**：能够持续观察环境、做出决策、执行动作，并根据反馈调整行为的 AI 系统。
**Reasoning（推理）**：利用已有信息进行多步分析、规划和判断，不等同于简单生成 `<think>` 文字。
**Adaptation（自适应）**：根据当前环境变化调整行动。
**Self-Evolution（自我演化）**：利用积累的经验改进未来行为，可以通过参数更新或策略、记忆更新实现。
RL 训练通常包含三个环节：
- **Rollout Generation**：让 Agent 与环境交互，生成执行轨迹。
- **Reward Assignment**：根据执行结果给轨迹或中间步骤分配奖励。
- **Trajectory Optimization**：通过 PPO、GRPO 等算法优化产生轨迹的策略。
整体流程：**生成轨迹 → 计算奖励 → 更新策略 → 生成新轨迹**。
RL 可以通过奖励反馈强化有效行为，但最终答案正确不代表中间推理正确，因此 RL 不保证一定学到真正有效的推理。
#### 3. 现有 Agent 方法与局限
- **ReAct、Reflexion**：通过思考、行动、观察和反思实现交互式任务执行。
- **结构化 Agent**：引入明确的规划、执行和反馈机制。
- **Multi-Agent Systems**：多个 Agent 分工协作处理复杂任务。
- **通用 Agent 系统**：应用于网页搜索、编程、GUI、游戏和机器人等任务。
常见测试环境包括：
- **Bandit**：单轮随机环境，测试对不确定奖励的适应。
- **Sokoban（推箱子）**：多轮确定性环境，测试长时程规划和动作决策。
- **FrozenLake（冰湖）**：多轮随机环境，同一个动作可能产生不同结果，测试随机反馈下的决策能力。
**现有问题**：大多数 LLM RL 方法主要针对静态任务，多轮 Agent RL 中的训练稳定性、推理退化和自我纠错问题仍不充分明确。
#### 4. StarPO 与 RAGEN 的关系
<img src="/images/obsidian/3e340ee43117.png" alt="Pasted image 20261108175708.png" />
**StarPO（State-Thinking-Actions-Reward Policy Optimization）** 是面向多轮 Agent 的轨迹级 RL 框架，将状态、推理、动作和奖励组成完整轨迹进行联合优化。
**RAGEN** 是实现 StarPO 的模块化训练系统，负责环境交互、Rollout 生成、Reward 计算、模型更新和实验评估。
RAGEN 支持更换环境、奖励函数和 Rollout 策略，用于研究多轮 Agent RL 的稳定性、泛化能力与学习动态。
**核心区别**：StarPO 定义训练方式，RAGEN 提供实际运行和研究训练过程的系统。
#### 5. StarPO：轨迹级强化学习
##### 5.1 与传统单轮 RL 的区别
传统单轮 RL：
$$
J_{\mathrm{step}}(\theta)=\mathbb E_{x\sim\mathcal D,\;y\sim\pi_\theta(\cdot\mid x)}[R(x,y)]
$$
给模型一个问题，生成一次回答，根据回答结果计算奖励。
StarPO：
$$
J_{\mathrm{StarPO}}(\theta)=\mathbb E_{\mathcal M,\;\tau\sim\pi_\theta}[R(\tau)]
$$
- $\theta$：LLM 的模型参数。
- $\mathcal M$：MDP（马尔可夫决策过程），表示交互环境。
- $\tau$：完整的多轮交互轨迹。
- $\pi_\theta$：LLM 的决策策略。
- $R(\tau)$：整条轨迹的累计奖励。
- $\mathbb E$：不同环境与轨迹上的期望奖励。
**核心区别**：传统单轮 LLM RL 优化一次回答的结果，StarPO 优化多轮交互轨迹的整体表现。PPO 本身也可以处理多轮任务，StarPO 的重点是将这种轨迹级优化组织成适用于 LLM Agent 的统一框架。
##### 5.2 State-Thinking-Action-Reward
每一轮交互包含：
- **State（$s_t$）**：当前环境状态。
- **Thinking**：LLM 根据环境状态及历史记录生成推理过程。
- **Action（$a_t$）**：LLM 输出能够被环境执行的动作。
- **Reward（$r_t$）**：环境提供的奖励反馈。
LLM 的完整输出为：
$$
a_t^T=\texttt{<think>...</think><answer>}a_t\texttt{</answer>}
$$
其中 $a_t^T$ 包含推理文本和动作文本，$a_t$ 是实际被环境执行的动作。
执行后环境返回新状态 $s_{t+1}$ 与奖励 $r_t$，进入下一轮。
##### 5.3 多轮轨迹构造
完整的 $K$ 轮轨迹为：
$$
\tau=\{s_0,a_0^T,r_0,s_1,\ldots,a_{K-1}^T,r_{K-1},s_K\}
$$
累计奖励：
$$
R(\tau)=\sum_{t=0}^{K-1}r_t
$$
**重要区别**：推理和动作由 LLM 生成，状态和奖励由环境返回。虽然评价的是整条轨迹，但训练仍通过 LLM 生成 Token 的概率更新模型参数。
#### 6. StarPO 的训练流程
<img src="/images/obsidian/62d293ba9364.png" alt="Pasted image 20261108175734.png" />
##### 6.1 Rollout 生成与模型更新
每次训练从初始状态 $s_0$ 出发，生成 $N$ 条完整轨迹，计算奖励和 Advantage，再更新 Policy。
整体流程：**Initial State → K-turn Rollout → Trajectory Reward → Advantage Estimation → Policy Update**。
支持两种轨迹来源：
- **On-policy**：用当前策略 $\pi_\theta$ 生成新的 Rollout。
- **Replay Buffer**：复用旧策略 $\pi_{\mathrm{old}}$ 生成的历史轨迹，减少重新采样成本，但需要注意新旧策略的数据分布差异。
训练循环中，Rollout 生成和策略更新交替执行。
##### 6.2 训练数量
- $P$：每个训练循环的初始状态数量。
- $N$：每个初始状态生成的轨迹数量。
- $E$：每次梯度更新使用的轨迹 Batch Size。
- $L$：训练循环次数。
总轨迹数量为 $LPN$，假设全部轨迹参与训练且 Batch 能整除，则梯度更新次数：
$$
S=\frac{LPN}{E}
$$
例如 $L=10,P=4,N=8,E=16$，总共生成 320 条轨迹，对应 20 次更新。
#### 7. StarPO 的模块化优化：PPO 与 GRPO
StarPO 不需要重新设计一种 RL 优化算法，而是可以使用 PPO、GRPO 等方法对多轮轨迹进行 Token 级更新。
##### 7.1 PPO：Critic 估计 Advantage
PPO 使用 Critic（Value Model）估计状态价值，为不同 Token 计算 Advantage $A_{i,t}$，其中 $i$ 表示第 $i$ 条轨迹，$t$ 表示其中第 $t$ 个 Token。
新旧策略的概率比值：
$$
\rho_{i,t}=\frac{\pi_\theta(\tau_{i,t}\mid\tau_{i,<t})}{\pi_{\mathrm{old}}(\tau_{i,t}\mid\tau_{i,<t})}
$$
PPO 核心优化项：
$$
\min\left(\rho_{i,t}A_{i,t},\operatorname{clip}(\rho_{i,t},1-\epsilon,1+\epsilon)A_{i,t}\right)
$$
**Clip** 限制策略更新幅度，避免新旧策略之间发生过大变化。PPO 可以为不同 Token 估计不同的 Advantage，但不保证能够准确识别每一步推理的贡献。
##### 7.2 GRPO：组内奖励计算 Advantage
GRPO 不需要额外训练 Critic，而是对同一个初始状态生成 $G$ 条轨迹，比较它们的累计奖励：
$$
\hat A_{i,t}=\frac{R(\tau_i)-\operatorname{mean}(\{R(\tau_1),\ldots,R(\tau_G)\})}{\operatorname{std}(\{R(\tau_1),\ldots,R(\tau_G)\})}
$$
- $R(\tau_i)$：第 $i$ 条轨迹的累计奖励。
- Mean：组内平均奖励。
- Std：组内奖励标准差。
同一条轨迹中参与训练的所有 Token 使用相同的归一化 Advantage。
例如一组轨迹奖励为 $[10,5,0]$，第一条高于平均奖励，第二条等于平均奖励，第三条低于平均奖励。
**PPO 与 GRPO 的区别**：PPO 使用 Critic 估计 Token 级 Advantage，GRPO 使用轨迹级奖励在组内计算相对 Advantage。
**GRPO 的局限**：高奖励轨迹中的错误中间步骤，也可能被整体正向 Advantage 强化，存在 Credit Assignment（贡献归因）问题。
#### 8. Echo Trap：训练退化现象
论文发现，多轮 Agent RL 训练容易进入 **Echo Trap（回声陷阱）**：模型逐渐重复相似的推理或行动模式，缺乏有效探索与调整。
典型现象：
- **Reward Variance Collapse（奖励方差坍缩）**：不同 Rollout 的奖励突然变得接近，模型难以通过奖励差异区分不同策略。例如奖励从 $[0,1,0,1]$ 变成 $[0,0,0,0]$。
- **Gradient Spike（梯度尖峰）**：梯度突然变得很大，导致模型参数更新不稳定。
- **Shallow Reasoning（浅层推理）**：模型重复固定推理模板，甚至生成与实际环境不一致的思考内容。
奖励方差坍缩和梯度尖峰可能同时出现，但不能简单认为前者必然直接导致后者。
**核心问题**：轨迹趋于同质化后，RL 的有效比较信号减少，模型可能陷入重复行为和不稳定更新。
#### 9. StarPO-S：稳定化训练
StarPO-S 是 StarPO 的稳定化改进，针对 Echo Trap 和训练不稳定问题进行优化。
##### 9.1 基于奖励方差的轨迹过滤
对同一个初始状态生成多条 Rollout，计算奖励标准差：
$$
U(s_0)=\operatorname{Std}(R(\tau_1),\ldots,R(\tau_N))
$$
例如：
- $[1,1,1,1]$：所有轨迹都成功，奖励方差为 0。
- $[0,0,0,0]$：所有轨迹都失败，奖励方差为 0。
- $[1,0,1,0]$：存在成功与失败，奖励方差较高。
**方法**：根据奖励方差对初始状态对应的轨迹组排序，优先保留高方差的组参与训练，过滤缺乏奖励差异的组。
**为什么有效？** 高方差意味着同一任务下不同 Rollout 的结果不同，通常能够提供更有区分度的学习信号。但奖励方差只是一个近似指标，并不等于直接测量模型的不确定性。
##### 9.2 Critic 与 Advantage 估计
引入 Critic 估计价值，可以为轨迹中的不同 Token 提供更有区分度的 Advantage，并帮助降低训练信号的方差。
与 GRPO 为整条轨迹分配相同 Advantage 不同，Critic 可以尝试估计不同决策的价值，但仍不能保证准确定位推理错误。
##### 9.3 调整 KL 与 Clipping
- **KL Term Removal**：在相关 PPO 稳定化实验中移除 KL 惩罚，减少策略过度受原始模型约束的情况，鼓励探索。
- **Clip-Higher / Asymmetric Clipping**：采用不对称裁剪范围，提高上界，让模型能够更积极地提高有利行为的概率，同时保留下界约束。
这些方法用于改善训练稳定性和学习效果，但不是所有任务都必然适用。
**核心思想**：StarPO-S 不改变轨迹级 RL 的基本目标，而是通过提高训练数据的信息量、改进优势估计和调整更新约束来缓解训练退化。
#### 10. Rollout 设计对训练效果的影响
论文通过实验发现，Rollout 的构造方式会显著影响多轮 Agent RL：
- **Diverse Initial States（多样化初始状态）**：从不同位置、环境状态和任务条件开始训练，避免模型只记住固定行为模式。
- **Moderate Interaction Granularity（中等交互粒度）**：每轮允许适量动作，避免动作过细造成过多交互成本，或过粗而缺少中间反馈。
- **Frequent Sampling（频繁采样）**：更频繁地使用当前策略生成新 Rollout，减少训练数据与当前策略不匹配的问题。
**核心结论**：Agent RL 不仅依赖优化算法，还高度依赖 Rollout 的初始状态分布、交互粒度和采样频率。
#### 11. 为什么轨迹级 RL 不一定提升推理能力？
论文发现，仅仅使用 `<think>` 标记要求模型推理，再通过 StarPO 优化最终任务奖励，并不能保证真正有效的推理出现。
例如机器人推箱子时：
- 第一步：正确判断方向。
- 第二步：错误地分析箱子位置。
- 第三步：碰巧完成任务。
最终奖励为 1，但中间推理并不完全正确。
**问题**：Trajectory-Level Reward 主要评价最终结果，难以判断中间每一步推理的质量，因此可能奖励碰巧成功或推理不一致的轨迹。
**Fine-Grained, Reasoning-Aware Reward（细粒度、感知推理的奖励）**：不仅评价任务是否完成，还要考虑中间状态理解、逻辑判断和动作规划是否合理。
**重要结论**：RL 可以提高任务成功率，但成功率提高不等于模型一定学会了更可靠的推理。细粒度推理奖励是论文指出的重要研究方向，而非已经彻底解决的问题。
#### 12. 论文贡献与局限
主要贡献：
- **StarPO**：建立统一的多轮轨迹级 Agent RL 框架。
- **RAGEN**：提供可扩展的 Agent RL 训练与评估系统。
- **Echo Trap**：识别多轮 RL 中奖励方差坍缩、梯度尖峰和重复行为等退化现象。
- **StarPO-S**：通过轨迹过滤、Critic 和优化约束调整缓解训练不稳定。
- **Rollout 分析**：说明初始状态多样性、交互粒度和采样频率的重要性。
主要局限：
- 训练稳定性改善不意味着完全消除 Echo Trap。
- 长时程任务仍存在中间步骤的 Credit Assignment 问题。
- 轨迹级奖励无法保证推理内容正确，模型可能生成表面合理但实际无效的思考。
- 随机环境中的学习和泛化仍具有挑战性。
#### 13. 总结
**RAGEN 的主要贡献不是提出一种完全替代 PPO/GRPO 的新算法，而是搭建多轮 Agent RL 的训练与研究框架，分析其退化现象，并提出稳定化改进。**
三个关键层次：
- **StarPO：解决如何进行多轮 Agent RL 训练。**
- **RAGEN：解决如何运行、扩展和研究这一训练过程。**
- **StarPO-S：针对 Echo Trap 等退化现象改善训练稳定性。**
最重要的实验发现是：多轮 Agent RL 的效果不仅取决于 PPO/GRPO，还取决于轨迹是否有信息量、Rollout 如何构造，以及奖励是否能有效评价中间推理。
**一句话：RAGEN 将 LLM RL 扩展到多轮环境交互，揭示了训练退化与推理质量问题，并通过 StarPO-S 和 Rollout 设计改进训练稳定性，但没有彻底解决长时程推理与随机环境反馈中的所有问题。**
