# FanoutNet：强化学习与 PCB 扇出自动化

论文：AAAI 2023
##### 1. 研究背景与核心问题
PCB（Printed Circuit Board）包含大量需要相互连接的元件引脚。在高密度 PCB 中，芯片引脚排列紧密，直接进行完整布线容易出现空间不足、线路交叉及过孔过多等问题。**Fanout（扇出）**：在正式布线前，先为密集引脚确定合适的出口位置，必要时利用过孔将线路引到其他层，为后续布线创造空间。**Router（布线器）**：根据引脚和扇出位置，计算真正的铜线路径，完成不同网络之间的连接。两者区别：**Fanout** 决定线路从哪里引出来；**Routing** 决定线路如何经过 PCB，最终连接到哪里。
<img src="/images/obsidian/0d6e166cd9c6.png" alt="FanoutNet_图1_扇出与布线.png" width="560" />
> 论文图 1：(a) 未布线布局与网络连线；(b) 扇出结果（Fanout location）；(c) 完整布线结果（Wire、Via）。

传统扇出方法依赖人工经验或启发式规则。由于扇出位置会影响后续完整布线的质量，论文希望使用深度强化学习自动优化扇出决策。**核心问题**：如何学习合适的 PCB 扇出位置，使传统自动布线器更容易完成全部连接，并减少线长与过孔？
##### 2. Fanout 与 Routing 的数学建模
###### 2.1 PCB Fanout Problem
给定：$L$ 多层 PCB 的布局；$N$ 网络（Net）集合；$P$ 引脚（Pin）集合；$C$ 布线约束。**Net（网络）**：电气上需要相互连接的一组引脚，一个网络可以包含多个引脚。论文使用 MST（Minimum Spanning Tree，最小生成树）表示多引脚网络的连接拓扑，将其组织为便于处理的连接关系。Fanout 的目标是为引脚选择扇出位置，同时减少网络的拓扑交叉：
$$\min \sum_{n\in N}T_c(n)\quad \text{s.t. }C$$
$T_c(n)$：网络 $n$ 的拓扑交叉数量；$\sum_{n\in N}T_c(n)$：所有网络的拓扑交叉总量；$\text{s.t. }C$：必须满足设计约束。**Topological Crossing（拓扑交叉）**：网络连接关系在布局上出现交叉，不一定等同于真实铜线短路，但会增加后续布线难度。Fanout 不直接优化完整线路，而是先选择合理出口，尽量减少交叉。
###### 2.2 PCB Routing Problem
给定多层 PCB 和已经确定的扇出结果 $F$，Router 必须完成网络连接，并满足约束。论文写为：
$$\max\quad Routability-Viacount-Wirelength\quad \text{s.t. }C$$
**Routability**：布通率或可布通性，越高越好；**Via Count**：过孔数量，越少越好；**Wirelength**：总走线长度，越短越好；**$C$**：线宽、间距等设计约束。该式表达多目标优化意图，没有在这里展开各指标的权重或归一化细节。**关系**：PCB Layout → FanoutNet 生成扇出方案 $F$ → Router 执行完整布线 → 评价最终布线质量。因此 FanoutNet 属于 **Indirect Routing（间接布线）**：RL 负责前期扇出决策，完整线路由固定的 Router 生成。
##### 3. FanoutNet 整体架构
<img src="/images/obsidian/756951c2f488.png" alt="FanoutNet_图2_整体架构.png" width="680" />
> 论文图 2：上方是 PCB 状态、FanoutNet 动作、状态更新、Multi-Constraint Router 和 Reward 的完整流程；左下是 Attention + CNN + Policy/Value MLP，右下是多约束 A* 布线器。
###### 3.1 完整工作流程
1. 将原始 PCB Design 转换为状态 $state_0$。2. FanoutNet 根据当前状态输出扇出动作。3. 执行动作，更新 PCB 状态。4. 重复决策，直到得到完整扇出结果 $F$。5. Multi-Constraint Router 根据扇出位置完成实际布线。6. 根据最终布线结果计算 Reward，用于训练 FanoutNet。可以表示为：
$$s_0\xrightarrow{a_0}s_1\xrightarrow{a_1}\cdots\xrightarrow{a_{T-1}}s_T\xrightarrow{\mathrm{Router}}R$$
**关键点**：强化学习学习的是扇出策略，最终布通效果需要通过 Router 来验证。
###### 3.2 Multi-Constraint Router
论文中的传统布线器主要执行：**Initialize Routing Map**（初始化布线地图）→ **Set Fanout Locations**（将扇出位置设为布线起点或终点）→ **A\* Path Searching**（利用 A* 搜索实际连接路径）→ **Output Routing Result**（输出最终布线结果）。A* 是启发式路径搜索算法，利用路径代价和到目标的估计代价选择搜索方向。Router 不由 FanoutNet 的 Policy MLP 代替，而是一个独立的布线阶段。
##### 4. State Representation（状态表示）
FanoutNet 使用两类特征共同表示 PCB：**Spatial Feature** 描述空间布局；**Structured Feature** 描述网络的坐标、连接关系与扇出状态。
###### 4.1 Spatial Feature（空间特征）
定义 $S\in\mathbb{R}^{L\times H\times W}$，其中 $L$ 为 PCB 层数，$H,W$ 为每层二维表示的高度和宽度，相当于把多层 PCB 表示成多通道二维图像。图像包含：引脚、边界和障碍物、已经生成的导线、已经放置的过孔。随着 Agent 执行新动作，新的走线与过孔会被更新到空间表示中。**处理方式**：将图像输入 CNN，提取 PCB 空间布局特征。
###### 4.2 Structured Feature（结构化特征）
论文将网络信息表示为向量序列 $M\in\mathbb{R}^{T\times6}$，并列出单个网络向量：
$$m_t=(x_t^1,y_t^1,z_t^1,x_t^2,y_t^2,z_t^2,b)$$
$(x_t^1,y_t^1,z_t^1)$：第一个位置的三维坐标；$(x_t^2,y_t^2,z_t^2)$：第二个位置的三维坐标；$b$：是否已完成扇出的标志位。当 $b=0$ 时，坐标描述引脚位置；当 $b=1$ 时，坐标描述扇出位置。初始时各网络尚未完成扇出，$b$ 均为 0。**注意**：原文写 $T\times6$，但随后列出的向量包含 6 个坐标和 1 个布尔值，共 7 项，存在维度描述不一致的问题。**处理方式**：结构化特征经过 Embedding 和 Attention Network，学习网络之间的关系。
###### 4.3 为什么需要两种特征？
**Spatial Feature + CNN**：学习哪里有空间、哪里有障碍、现有线路怎样分布。**Structured Feature + Attention**：学习哪些网络需要扇出、引脚在哪里、网络之间存在什么关系。两种特征互补，最终拼接后用于决策。
##### 5. 神经网络结构与强化学习
###### 5.1 网络结构
<img src="/images/obsidian/961f054c21b0.png" alt="FanoutNet_图2局部_神经网络.png" width="560" />
> 论文图 2 左下：结构化特征经过 Embedding 和 Attention，空间特征经过 CNN，两路输出拼接后分别送入 Policy MLP 和 Value MLP。

整体流程：Structured Features → Attention Network；Spatial Features → CNN；两路特征拼接（Concatenation）→ Policy MLP / Value MLP。**Policy Network（Actor）**：输出不同扇出动作的概率，决定下一步动作。**Value Network（Critic）**：评估当前状态的未来预期回报，辅助强化学习训练。这是典型的 Actor-Critic 结构。
###### 5.2 动作选择
FanoutNet 为候选扇出动作分配概率，形成策略分布 $\pi_\theta(a\mid s)$，表示在当前状态 $s$ 下选择动作 $a$ 的概率。每一步从策略分布中采样动作，并更新状态。论文指出，在给定当前状态和所选动作后，环境转移是确定性的；动作选择本身则来自策略的概率分布。
##### 6. Reward：布通率
论文根据完整布线结果计算奖励：
$$R=\frac{N_{\mathrm{succ}}}{N_{\mathrm{total}}}$$
$N_{\mathrm{succ}}$：成功完成布线的网络数量；$N_{\mathrm{total}}$：需要布线的网络总数量；$R$：布通率（Routability），范围为 $[0,1]$。例如共有 100 个网络，其中 90 个成功连接：$R=\frac{90}{100}=0.9$，即布通率为 90%。
###### 6.1 为什么用布通率作为 Reward？
FanoutNet 只选择扇出位置，无法单独判断这些位置能否让完整 PCB 成功布线。因此必须：1. 先产生完整扇出结果；2. 调用 Router 尝试连接网络；3. 使用最终布通率评价扇出方案。**扇出方案越有利于 Router 完成连接，Reward 越高。**
###### 6.2 Reward 的特点
这里的 Reward 主要来自最终完整布线结果，而不是每选择一个扇出位置就直接计算一次完整布通率。这种反馈能够对齐最终任务目标，但奖励相对稀疏，模型需要学习前期扇出动作对后续整体布线结果的影响。**注意**：布通率达到 100% 表示全部网络完成连接，但不代表线长、过孔和所有工程质量指标都已经最优。
##### 7. FanoutNet 与 PCBWorld 的区别
| 维度 | FanoutNet | PCBWorld |
| --- | --- | --- |
| 研究目标 | 学习更好的扇出策略 | 构建统一的 PCB Agent 交互与评测环境 |
| Agent 控制内容 | 引脚扇出位置 | 原生布线动作 |
| 完整走线 | 交给固定的传统 Router | 通过 KiCad 原生引擎逐步执行 |
| 方法特点 | 间接布线 | Engine-Grounded 交互 |
| 强化学习任务 | 优化 Fanout 决策 | 优化完整布线过程的动作决策 |

FanoutNet 体现了 **AI 决定高层布线前置条件，传统算法完成底层路径规划** 的思路。PCBWorld 则进一步让 Agent 参与具体布线阶段的逐步操作。
##### 8. 总结
**FanoutNet 的核心思想**：使用深度强化学习自动选择 PCB 扇出位置，通过后续传统自动布线器的实际布通表现，反向优化扇出策略。关键技术：**Fanout**——为密集引脚规划出口位置；**Routing**——完成所有网络的实际走线；**Topological Crossing**——扇出阶段希望减少的网络拓扑交叉；**Spatial Feature + CNN**——提取 PCB 的空间几何信息；**Structured Feature + Attention**——提取网络连接和扇出状态信息；**Policy / Value Network**——分别负责动作选择和状态价值估计；**Multi-Constraint Router + A\***——基于扇出结果完成布线；**Routability Reward**——根据成功布通网络的比例训练强化学习策略。
**一句话总结：FanoutNet 不直接学习整个 PCB 的线路怎么画，而是学习如何把引脚合理地引出来，让传统 Router 更容易完成后续布线。**
