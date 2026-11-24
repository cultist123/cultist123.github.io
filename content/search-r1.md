# Search-R1：用强化学习学习搜索

#### 1. 研究背景
传统 LLM 主要依赖**参数化推理（Parametric Reasoning）**，即利用模型参数中已经学到的知识进行推理，缺点是知识可能过时或不完整。因此需要结合**先进推理能力（Advanced Reasoning）** 和外部信息检索能力，让模型不仅能够多步思考，还能主动搜索最新信息。
- **SFT、PPO**：训练模型的方法。
- **Reasoning**：模型进行逻辑思考和解决复杂问题的能力。
- **Training vs. Inference**：前者更新模型参数，后者利用已有参数生成结果。
#### 2. RAG 与 Search-as-a-Tool
**RAG（Retrieval-Augmented Generation）**：传统流程是用户问题 → 检索资料 → 拼接到 Prompt → LLM 生成答案。通常采用**一轮检索 + 顺序生成**，缺点是首次检索信息不足时，难以主动补充。
**Search-as-a-Tool**：将搜索引擎作为 LLM 可以调用的工具。模型能够在推理过程中自主决定什么时候搜索、搜索什么，以及是否需要再次搜索。流程是问题 → 思考 → 搜索 → 阅读结果 → 继续思考 → 回答。
**核心区别**：传统 RAG 通常先检索再生成；Search-as-a-Tool 支持推理过程中的动态、多轮搜索。两者并不互斥。
#### 3. 相关工作及局限
- **IRCoT**：推理与检索交替进行，主要通过 Prompt 引导。
- **ReAct**：通过 Prompt 实现思考 → 行动 → 观察的循环。
- **Toolformer**：通过训练让 LLM 学习工具调用。
现有方法主要分为两类：
- **Prompt-based**：使用提示引导搜索，缺点是对陌生任务的泛化能力有限。
- **Training-based**：训练模型学习搜索策略，缺点是需要大量高质量的执行轨迹（问题 → 搜索 → 阅读 → 再搜索 → 回答）。
**搜索不可微**：搜索引擎不是可直接求导的神经网络模块，无法将最终 Loss 通过搜索引擎反向传播。因此需要其他训练方法来优化搜索行为。
#### 4. Search-R1 核心思想
Search-R1 引入**搜索增强的强化学习（Search-Augmented RL）**，让 LLM 通过最终任务的奖励反馈，学习如何与搜索引擎交互，而不是完全依赖人工标注的搜索步骤。
主要学习四种能力：什么时候搜索、搜索什么、如何利用检索结果、什么时候停止搜索并回答。
**核心思想**：通过 RL 同时优化模型的推理能力与搜索决策。
#### 5. 训练架构：PPO 与 GRPO
<img src="/images/obsidian/dfbe8f6ebdd9.png" alt="Screenshot 2026-11-08 at 15.45.29.png" width="521" />
整体流程：**Query → Rollout → Reward → Advantage → Policy Update**
- **Query（q）**：输入问题。
- **Policy LLM**：正在训练的模型，负责推理、搜索和回答。
- **Search Engine**：执行检索并返回信息。
- **Rollout（o）**：从输入问题到最终回答的完整执行轨迹，包括搜索交互。
- **Reward（r）**：评价结果的好坏。
- **Advantage（A）**：衡量一次生成相对基准的表现，用于指导参数更新。
**PPO**：使用 Policy LLM 生成轨迹，通过 Reward、Value LLM 和 GAE 计算 Advantage，再更新 Policy。Reference LLM 用于 KL 约束，避免模型偏离参考策略太远。
**GRPO**：不需要 Value LLM。同一问题生成 $G$ 条不同轨迹，通过组内奖励比较计算 Advantage。表现高于组内平均水平的轨迹获得正向训练信号，低于平均水平的获得负向信号。
**主要区别**：PPO 依靠 Value LLM 估计价值，GRPO 通过同组多个回答的奖励比较计算相对优势。
#### 6. Search-R1 优化目标
$$
\max_{\pi_\theta}\mathbb{E}_{x\sim\mathcal D,\ y\sim\pi_\theta(\cdot\mid x;\mathcal R)}[r_\phi(x,y)]-\beta D_{\mathrm{KL}}[\pi_\theta(\cdot\mid x;\mathcal R)\|\pi_{\mathrm{ref}}(\cdot\mid x;\mathcal R)]
$$
- $\pi_\theta$：正在训练的 Policy LLM。
- $\mathcal D$：训练问题的数据集。
- $x$：输入问题。
- $y$：生成的回答或执行轨迹。
- $\mathcal R$：搜索引擎。
- $r_\phi$：奖励函数。
- $\pi_{\mathrm{ref}}$：冻结的参考模型。
- $D_{\mathrm{KL}}$：衡量当前策略与参考策略的差异。
- $\beta$：控制 KL 惩罚强度。
**公式含义**：最大化回答质量和搜索效果，同时通过 KL 惩罚限制模型过度偏离原始策略。
**与传统 PPO 的区别**：
传统模型：$y\sim\pi_\theta(\cdot\mid x)$
Search-R1：$y\sim\pi_\theta(\cdot\mid x;\mathcal R)$
增加搜索引擎 $\mathcal R$，使模型能够在 Rollout 中进行多轮搜索。**主要改变的是交互环境和轨迹生成方式，并不是 PPO 的核心优化算法。** 该公式是总体 RL 目标，而不是 PPO 专有的具体损失函数。
#### 7. 检索 Token 的损失掩码（Loss Masking）
训练时区分两种 Token：
- **LLM 自己生成的 Token**：Loss Mask = 1，参与 RL Loss 计算。
- **搜索引擎返回的 Token**：Loss Mask = 0，不直接参与 RL Loss 计算。
例如：LLM 生成搜索请求（Mask=1）→ 搜索引擎返回网页（Mask=0）→ LLM 根据结果继续推理并回答（Mask=1）。
**原因**：搜索结果来自外部工具，不是 LLM 自己生成的动作，因此不应该要求 LLM 学习预测这些 Token。但搜索结果仍作为上下文影响后续推理，并间接影响训练效果。
#### 8. Agentic RL 与传统 LLM RL 的区别
Search-R1 本质上没有改变 PPO/GRPO 的核心算法，而是将普通 LLM RL 扩展成了支持工具交互的 Agentic RL，主要体现在三个方面：
- **Rollout 加入搜索工具**：模型可以自主决定什么时候搜索、搜索什么，并根据搜索结果继续推理。
- **Loss Masking**：搜索引擎返回的 Token 不参与 Loss 计算，只对 LLM 自己生成的 Token 计算训练损失。
- **RL 优化搜索策略**：通过最终答案的 Reward，不仅优化回答质量，还间接优化搜索时机、查询内容和工具使用行为。
**核心区别**：加入搜索工具让模型具备与环境交互的能力，Loss Masking 保证训练时正确处理外部信息，而 RL 让模型通过奖励反馈学习更有效的搜索策略。
#### 9. 未来改进方向
- **更复杂的 Reward**：同时考虑答案正确性、搜索质量和调用成本。
- **不确定性驱动的动态检索**：模型不确定时增加搜索，有把握时减少搜索。
- **结合更多工具**：使用代码执行器、计算器等工具辅助推理。
- **多信息源融合**：结合网页、论文数据库、知识图谱等信息源。
#### 10. 总结
**Search-R1 的核心贡献**是将搜索引擎交互纳入 LLM 的强化学习过程，让模型通过最终任务奖励学习搜索策略，减少对人工标注搜索轨迹的依赖。
相比传统 RAG，它支持推理过程中的主动检索；相比 ReAct、IRCoT，它通过 RL 进一步优化搜索行为；相比普通 LLM RL，它将搜索交互纳入 Rollout。
**一句话：不仅训练 LLM 如何回答问题，还训练它为了回答问题应该如何主动获取信息。**

---
