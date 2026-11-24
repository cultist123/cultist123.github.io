# Agent Lightning：Agent 执行与 RL 训练解耦

论文：https://arxiv.org/abs/2508.03680
##### 1. 研究问题：Agent 与 RL 训练的耦合
现有 Agent RL 训练存在两个主要问题：
**① Training-Agent Tight Coupling（紧耦合）**
- RL 训练代码需要了解 Agent 的执行逻辑、工具调用和状态变化。
- 更换 Agent 框架或 RL 算法时，可能需要重新修改训练流程。
- 复杂 Agent 涉及多轮工具调用、动态工作流和环境反馈，难以直接集成传统 RL 框架。
**② Sequence Concatenation & Masking（序列拼接与掩码）**
传统多轮 RL 通常将整条交互轨迹拼成一个长序列：
$$
\text{Action}_1\rightarrow\text{Observation}_1
\rightarrow\text{Action}_2\rightarrow\cdots
$$
训练时需要 Mask 环境生成的 Observation Token，只对 LLM 输出计算策略损失。
这种方法存在长上下文、位置编码、复杂工作流适配等问题。
**Agent Lightning 的核心思想：将 Agent Execution 与 RL Training 解耦，通过统一数据接口连接两者。**
<img src="/images/obsidian/1907dfd98b66.png" alt="AgentLightning_图1_整体思想.png" width="680" />
Figure 1：Agent Lightning 整体思想。Agent 执行任务 → 收集 Training Trajectories → RL Engine 更新模型 → Agent 使用更新后的模型。
##### 2. 核心架构：Training-Agent Disaggregation
Agent Lightning 将执行和训练划分为两个独立部分：

| 模块 | 主要职责 |
|---|---|
| Agent Client | 执行任务、调用工具、处理环境反馈、产生轨迹和奖励 |
| RL Server | 提供 LLM 推理 API、管理训练、更新模型参数 |

两者通过接口通信：
$$
\text{Agent Execution}
\xrightarrow{\text{Rewarded Traces}}
\text{RL Trainer}
$$
$$
\text{RL Trainer}
\xrightarrow{\text{Updated Model API}}
\text{Agent Execution}
$$
**独立运行**指两边不依赖对方的内部实现，而不是完全不通信。
- LangChain、AutoGen 或自定义 Agent 可以使用同一套训练服务。
- 更换 PPO、GRPO 等训练算法，不必重写 Agent 的工具调用逻辑。
- Agent 可运行在普通服务器，模型推理和训练可运行在 GPU 服务器。
这种设计也用于缓解 **Sampling Bottleneck（采样瓶颈）**：复杂 Agent Rollout 包含多次推理、工具调用和环境交互，生成训练数据可能比模型参数更新更慢。
##### 3. Unified Data Interface：统一执行数据表示
统一接口是解耦的基础：不要求 RL 系统理解 Agent 内部代码，而是统一记录执行状态、组件调用及奖励。
###### 3.1 State：语义变量构成的执行快照
Agent 的执行过程使用 MDP 表示：
$$
s_t\xrightarrow{a_t}s_{t+1}
$$
其中 State 是某个时刻的 **Execution Snapshot（执行快照）**。
$$
\boxed{
\operatorname{state}_t(x,k)
=\{\operatorname{variable}_i^{x,k,t}\}_{i=1}^{V}
}
\tag{1}
$$
- $x$：任务。
- $k$：任务的第 $k$ 次执行（Rollout）。
- $t$：当前执行时刻。
- $V$：语义变量数量。
**Semantic Variable（语义变量）** 指影响任务执行的关键变量，而不是所有程序内部变量。
例如 RAG Agent：
$$
\operatorname{state}=\{U,Q,P,A\}
$$
- $U$：User Input。
- $Q$：Query。
- $P$：Passages。
- $A$：Answer。
变量随着组件执行逐渐被赋值或修改。
###### 3.2 Call：组件调用
一次完整执行由多次组件调用组成：
$$
\boxed{
\operatorname{execution}(x,k)
=\{\operatorname{call}_i^{x,k}\}_{i=1}^{N}
}
\tag{2}
$$
每次调用定义为：
$$
\boxed{
\operatorname{call}_i=(\operatorname{meta}_i,\operatorname{input}_i,\operatorname{output}_i)
}
$$
- `meta`：组件名称、类型、版本、API、温度等运行信息。
- `input`：组件输入。
- `output`：组件输出。
- $N$：本次执行的组件调用总数。
组件可以是 LLM，也可以是 Search、数据库等工具。
输入输出来自不同时刻的状态：
$$
\operatorname{input}_i\in\operatorname{state}_{t_1},
\qquad
\operatorname{output}_i\in\operatorname{state}_{t_2}
\tag{4}
$$
一次调用只需读取或更新部分语义变量，不需要访问整个 State。
###### 3.3 Rewarded Execution：为组件调用关联奖励
$$
\boxed{
\operatorname{execution}^{R}(x,k)
=\{(\operatorname{call}_i^{x,k},r_i^{x,k})\}_{i=1}^{N}
}
\tag{5}
$$
即从：
$$
(\text{meta},\text{input},\text{output})
$$
变成：
$$
(\text{meta},\text{input},\text{output},r)
$$
奖励可以是：
- **Intermediate Reward**：中间步骤奖励，例如工具调用成功。
- **Terminal Reward**：任务完成后获得的奖励。
实际任务经常只有终局奖励，即 Sparse Reward。
训练数据集 $\mathcal X$ 是任务集合，同一任务可以执行多次，形成不同的 Rollout。
###### 3.4 示例：RAG Agent
一个 RAG Agent 的执行流程：
$$
U\xrightarrow{\mathrm{LLM}}Q
\xrightarrow{\mathrm{Search}}P
\xrightarrow{\mathrm{LLM}}A
$$
最后通过奖励函数评价答案：
$$
R=\operatorname{RAG\_F1}(A,x)
$$
完整调用记录：

| Component | Input | Output | Reward |
|---|---|---|---|
| LLM | U | Q | NA |
| Search | Q | P | NA |
| LLM | (U,P) | A | R |

`NA` 表示没有单独提供奖励，不等于奖励为 0。
<img src="/images/obsidian/0bcff2231962.png" alt="AgentLightning_图2_统一数据接口.png" width="680" />
Figure 2：统一数据接口。左侧：U、Q、P、A 随执行逐渐更新；中间：记录所有组件的调用和奖励；右侧：提取需要训练的 LLM 调用。
##### 4. LightningRL：从复杂轨迹到独立训练样本
###### 4.1 RL Data Extraction
针对待优化模型 $\pi_\theta$，从完整记录中只提取该模型的调用：
$$
\boxed{
\operatorname{execution}^{RL}(x,k)
=\{(\operatorname{input}_t^{x,k},
\operatorname{output}_t^{x,k},
r_t^{x,k})\}_{t=1}^{T}
}
\tag{6}
$$
$$
\operatorname{output}_t^{x,k}
=\pi_\theta(\operatorname{input}_t^{x,k})
\tag{7}
$$
其中 $T$ 是本次执行中待优化 LLM 的调用次数。
对于上述 RAG：
$$
(U,Q,\mathrm{NA})
$$
$$
((U,P),A,R)
$$
Search 调用不作为 LLM 训练样本，但检索结果 $P$ 仍保留在后续 LLM 输入中。
**Training Trajectory 与 CoT 的区别：**
- CoT：模型生成的推理过程。
- Training Trajectory：完整执行记录，包含动作、环境反馈、组件调用及奖励，也可能包含 CoT。
###### 4.2 与传统 Multi-turn GRPO 的区别
**传统 Multi-turn GRPO：**
- 将多轮 LLM 输出和环境反馈拼成一条长序列。
- 使用 Mask 排除环境产生的 Token。
- 整条轨迹作为训练数据组织单位。
**LightningRL：**
- 将完整执行拆分为独立 LLM 调用。
- 每条训练样本都有自己的 Input、Output 和 Reward。
- 环境反馈保留在下一次调用的 Input 中。
- Loss 只针对 LLM Output，不必再将环境反馈拼进去然后 Mask。
这里的**独立**指训练样本可以分别处理，不代表执行时各轮没有依赖关系。下一轮 Input 仍可包含先前的环境反馈。
<img src="/images/obsidian/91da5e8fa937.png" alt="AgentLightning_图3_LightningRL对比.png" width="680" />
Figure 3：Single-call GRPO / Previous Multi-turn GRPO / LightningRL
- (a) 单次调用：同一任务生成多个回答，按奖励分组。
- (b) 多轮拼接：绿色是 LLM 输出，虚线方块是被 Mask 的环境反馈。
- (c) 拆分调用：橙色 Input 包含所需上下文，绿色 Output 表示不同调用，颜色深浅用于区分输出。
- `state(x,0)`、`state(x,1)`、`state(x,2)`：同一任务的不同 Rollout 编号，不是时间步。
###### 4.3 Two-stage Credit Assignment（两阶段信用分配）
LightningRL 将信用分配拆为两步：
$$
\boxed{
\text{Episode Reward}
\rightarrow
\text{LLM Call Reward}
\rightarrow
\text{Token Advantage}
}
$$
**第一步：Episode → Call**
把完整任务的回报分配给不同 LLM 调用。
本文当前实现采用简单方案：同一条轨迹内各次调用共享最终回报 $R$。
**第二步：Call → Token**
使用已有单轮 RL 算法，计算 Token Advantage 并更新模型。
好处：
- 复用 GRPO、PPO、REINFORCE++ 等训练方法。
- Input 可灵活采用历史摘要、Prompt 模板或角色指令。
- 不依赖复杂的长序列拼接和额外掩码。
- 将长轨迹拆成调用批次，便于批量训练和梯度累积。
###### 4.4 策略梯度优化目标
$$
\boxed{
\mathcal L(\theta)=
-\mathbb E\left[
\sum_{j=1}^{N}
\log\pi_\theta(y_j\mid x,y_{<j})A_j
\right]
}
\tag{8}
$$
- $y_j$：第 $j$ 个 Token。
- $\pi_\theta(y_j\mid x,y_{<j})$：模型生成该 Token 的概率。
- $A_j$：该 Token 的优势。
当 $A_j>0$ 时，训练倾向于提高该 Token 的概率；反之降低。
不同算法的主要区别之一是优势估计：
- **PPO**：使用 Critic 和价值函数。
- **GRPO**：通过同组采样奖励的均值、标准差归一化。
- **REINFORCE++**：使用整个 Batch 的平均奖励作为基线。
实际算法还可能包含 Clipping 等机制。
##### 5. System Design：训练与执行的工程实现
###### 5.1 Client–Server 架构
<img src="/images/obsidian/9f303c581acd.png" alt="AgentLightning_图4_训练执行解耦架构.png" width="680" />
Figure 4：Training-Agent Disaggregation Architecture
- RL Server：LLM Engine、Trainer、任务调度和数据通信。
- Agent Client：运行 LangChain、AutoGen 或自定义 Agent。
- Server → Client：更新后的模型 API。
- Client → Server：Rewarded Traces。
Server 管理任务分发；Client 独立运行 Agent，收集数据，再返回训练端。
###### 5.2 Agent Runtime
**Data Parallelism**
- 节点内：一个 Client 启动多个 Worker。
- 节点间：多台机器分别运行 Worker。
- 目的：提高 Rollout 吞吐量，缓解采样瓶颈。
**Automatic Instrumentation（自动插桩）**
- 利用 OpenTelemetry、AgentOps 自动记录 Trace、LLM 调用及环境交互。
- 减少对原有 Agent 代码的修改。
- 也可以通过 API 端点进行轻量追踪。
**Error Handling**
- 检测程序崩溃、网络中断和超时。
- 失败任务可以重试或重新分配。
- 避免单个异常拖垮整个训练过程。
**AIR（Automatic Intermediate Reward）**
- 将执行监控信息转换为中间奖励。
- 用更频繁的反馈缓解终局奖励稀疏的问题。
**Environment & Reward Service**
- 简单环境和奖励计算可以与 Worker 同机运行。
- 高成本模拟器或复杂奖励函数可以使用共享服务。
##### 6. 扩展到不同 Agent
**单 LLM、多角色**
同一个模型通过不同 Prompt 承担搜索、回答等角色。
可以选择性优化特定角色对应的调用。
**多 LLM、多 Agent**
多个模型有独立的策略参数。
- 独立训练：分别优化模型，但可能忽略相互依赖。
- Multi-Agent RL：联合考虑 Agent 之间的合作与竞争。
**任务适用性**
- Coding RL：通过代码修改、测试反馈和奖励训练编程 Agent。
- RAG：通过奖励优化检索词生成和回答策略。
- 复杂交互任务：包含多轮动作、工具调用和动态环境反馈。
MCP 负责标准化 Agent 与工具的连接；Agent Lightning 关注 Agent 执行数据如何连接 RL 训练，两者解决的问题不同。
##### 7. 核心总结
Agent Lightning 的贡献可以归纳为三个层次：
1. **统一数据抽象**：用 State、Call、Rewarded Execution 表示不同 Agent 的执行过程。
2. **LightningRL**：将复杂多轮轨迹提取为独立 LLM 调用，并通过两阶段信用分配复用单轮 RL 算法。
3. **Training-Agent Disaggregation**：通过 Client–Server 架构，解耦 Agent 工作流与 RL 模型训练。
**核心思想：不必为了 RL 重写 Agent，也不必把整个多轮工作流拼成一条长序列；通过标准化执行数据、拆分训练样本和独立部署，让现有 RL 训练方法适用于不同的 Agent。**
