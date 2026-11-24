# PCBWorld：原生 PCB 设计自动化环境

论文：2026，arXiv:2607.05915
##### 1. 研究背景与问题
PCB（Printed Circuit Board，印刷电路板）布线需要连接不同电子元件的焊盘，同时满足设计规则并优化线路质量。
传统自动布线器（Autorouter）主要使用规则和启发式搜索算法，例如优先选择短路径、遇到障碍绕行、调整布线层等。
传统方法能够自动完成大量常规走线，但复杂、高约束的量产 PCB 通常仍需要人工调整与验证。
现有 AI 布线方法主要分为两类：
- **直接布线（Direct Routing）**：Agent 自己决定局部走线动作，例如在二维网格中逐格移动。问题是动作序列长、几何表达有限，与真实 PCB 工具存在差距。
- **间接布线（Indirect Routing）**：Agent 只决定网络顺序、布线模式或扇出位置，具体几何全部交给固定自动布线器。性能受到该布线器能力和搜索空间的限制。
**核心问题**：如何让 RL 和 LLM Agent 直接使用真实 PCB 设计引擎，并在统一环境中训练、交互和评测？
##### 2. PCBWorld 的核心贡献
PCBWorld 并没有重新实现一个 PCB 布线引擎，而是将真实的 KiCad 引擎封装为 Agent 可以调用的交互环境。
主要贡献：
- **Engine-Grounded Environment**：使用 KiCad 原生 C++ 引擎执行实际布线操作和设计规则检查。
- **统一 Agent 接口**：支持传统搜索算法、RL Agent 和 Tool-Using LLM Agent。
- **PCBWorld-Bench**：提供合成和真实 PCB 任务，支持使用统一协议和工程指标比较不同策略。
- **闭环交互**：每一步操作后返回更新的 PCB 状态和反馈，允许 Agent 持续修正布线。
**Engine-Grounded** 的关键不只是调用工具，而是让每一步状态变化和设计规则验证都由真实工程引擎完成。
##### 3. Engine-Grounded 交互机制
<img src="/images/obsidian/4769e1c289bb.png" alt="PCBWorld_图1_总览.png" width="680" />
> 论文图 1：Agent 观察 PCB，通过 GUI 或 API 调用 KiCad 引擎，获得更新后的电路板状态，并根据逐步反馈继续布线。左侧未连接数为 2（P3、P4），调用 `make_track(P3,P4)` 后未连接数变为 0。

基本流程：
Observation → Agent Decision → Native API Action → KiCad Engine → Updated Board / Feedback → Next Observation
例如：
1. PCB 上 P1、P2 已连接，P3、P4 未连接。
2. Agent 选择连接 P3 和 P4。
3. 调用 `make_track(P3, P4)` 一类原生操作。
4. KiCad 引擎尝试布线并更新设计。
5. Agent 根据结果决定下一步。
###### 3.1 Engine、GUI 与 API
- **Engine**：软件内部实际执行布线、几何计算和设计规则检查的核心程序。
- **GUI**：人类通过鼠标和键盘操作软件的图形界面。
- **Native API**：程序直接调用软件提供的功能接口。
GUI 与 API 可以操作同一套底层引擎。原生 API 交互不需要模拟鼠标，也不需要重新实现引擎。
###### 3.2 Grid 与 Gridless
- **Grid**：把 PCB 离散为格子，Agent 逐格选择移动方向。
- **Gridless**：使用真实引擎的几何坐标与布线机制，不强制沿固定网格移动。
PCBWorld 的 RL Agent 可以从有限候选点中选择动作，但底层几何仍然是 Gridless。
###### 3.3 DRC 与 DRV
<img src="/images/obsidian/28c5b5c454bf.png" alt="PCBWorld_图2_PCB核心概念.png" width="560" />
> 论文图 2：PCB 布线核心概念。同一网络（Net）的焊盘（Pad）必须连通；不同网络的走线靠得太近或交叉就产生 DRV（图中圆圈处）；过孔（Via）让走线换到另一层以避开冲突（Net 3 经 Layer 2 绕行）。

- **DRC（Design Rule Check）**：设计规则检查，例如线宽、间距及不允许的连接冲突。
- **DRV（Design Rule Violation）**：违反设计规则的情况。
理想布线结果应尽可能完成全部连接，并达到零 DRV。
##### 4. PCB 布线的约束优化建模
论文将 PCB 布线表示为：
$$
s^*=\arg\min_{s\in\mathcal R}
\lambda_w\ell(s)+\lambda_v n_{\mathrm{via}}(s)
$$
$$
\text{subject to }n_{\mathrm{drv}}(s)=0
$$
符号含义：
- $s$：PCB 的一种布线状态。
- $\mathcal R$：候选电路板状态集合。
- $\ell(s)$：总走线长度。
- $n_{\mathrm{via}}(s)$：过孔数量。
- $n_{\mathrm{drv}}(s)$：设计规则违规数量。
- $\lambda_w,\lambda_v$：线长与过孔的权重。
- $\arg\min$：寻找使目标函数最小的布线方案。
**Constrained Optimization（约束优化）**：在满足硬性约束的前提下，寻找目标函数最优的方案。
这里：
- **硬约束**：$n_{\mathrm{drv}}(s)=0$，不能存在 DRV。
- **优化目标**：线路尽可能短、过孔尽可能少。
过孔（Via）用于连接 PCB 不同铜层，增加过孔通常会增加制造成本及相关电气设计负担。
##### 5. MDP 建模
PCBWorld 将布线过程建模为 Markov Decision Process：
$$
\mathcal M=(S,A,P,R,\gamma)
$$
- **State $S$**：当前 PCB 状态，包括元件、焊盘、走线、过孔、网络连通性等。
- **Action $A$**：选择网络、开始布线、延伸线路、放置过孔等。
- **Transition $P$**：KiCad 引擎执行动作后产生的状态变化。
- **Reward $R$**：根据布线质量改善情况计算奖励。
- **Discount Factor $\gamma$**：控制未来奖励的权重。
MDP 是通用的序贯决策框架，PCBWorld 的关键是使用真实 KiCad 引擎实现状态转移，而非自己构造简化规则。
##### 6. Action Space：六种原生布线动作
| 动作 | 含义 |
| --- | --- |
| `net_select(net_id)` | 选择需要布线的电气网络 |
| `net_end` | 释放当前网络 |
| `start_route(p_start)` | 从指定点开始布线 |
| `make_line(p_end, routing_mode)` | 将当前走线延伸到目标点 |
| `make_via(p_end, routing_mode)` | 延伸走线，并在终点放置过孔 |
| `finish(routing_mode)` | 尝试自动连接最近的未连接焊盘 |

Agent 负责选择高层布线动作，KiCad 引擎负责具体几何实现。
###### 6.1 Routing Modes
<img src="/images/obsidian/bee1d5cc699f.png" alt="PCBWorld_图4_make_line三种模式.png" width="680" />
> 论文图 4：同一个 `make_line` 动作，`routing_mode` 不同，KiCad 引擎生成的走线几何也不同。

<img src="/images/obsidian/6e7f7a1e8301.png" alt="PCBWorld_图15_障碍交互策略.png" width="680" />
> 论文附录图 15：`set_routing_mode` 的三种障碍交互策略对比——`mark_as_obstacles` 碰到间距冲突就中止，`push_n_shove` 推开相邻走线，`walkaround` 保持已有走线不动并绕行。

- **Mark as Obstacles**：将现有线路视为障碍，不主动移动它们。
- **Push and Shove**：尝试推动已有线路，为新线路腾出空间。
- **Walkaround**：保留已有线路，让新线路绕过障碍。
例如：
`start_route(P1)` → `make_line(P2, walkaround)`
Agent 只需要指定目标位置与模式，不需要自己计算所有拐角。
###### 6.2 候选动作点
KiCad 引擎可以暴露有限候选终点，例如焊盘中心、走线端点和过孔端点。
- RL Agent 通常从候选集合中选择目标点。
- LLM Agent 也可以在接口允许时输出自由坐标。
这种设计减少了直接生成完整连续几何路径的难度，同时保留真实 PCB 的空间结构。
##### 7. Reward Function：奖励设计
###### 7.1 Potential Function（势函数）
论文定义电路板质量分数：
$$
\Phi(s)=-
\left(
f_{\mathrm{drv}}(s)+
\lambda_w\ell(s)+
\lambda_v n_{\mathrm{via}}(s)
\right)
$$
其中：
- $f_{\mathrm{drv}}(s)$：DRC 违规惩罚函数。
- $\ell(s)$：走线长度。
- $n_{\mathrm{via}}(s)$：过孔数量。
**理解**：违规、线长和过孔都是成本，因此取负号。成本越小，$\Phi(s)$ 越大。
论文使用非线性的 DRV 惩罚，尤其强调接近零违规时的改善。
原来的零 DRV 硬约束在奖励中被转化为惩罚项，较大惩罚可以鼓励合法布线，但不数学保证零违规。
###### 7.2 Terminal Reward（终局奖励）
只有任务结束时提供质量改善奖励：
$$
r_T=\Phi(s_T)-\Phi(s_0)
$$
其中 $s_0$ 为初始 PCB，$s_T$ 为最终 PCB。
问题：多次布线之后才得到奖励，很难知道哪个动作带来了改善。
###### 7.3 Per-Step Reward（逐步奖励）
每次动作后给出：
$$
r_t=\Phi(s_{t+1})-\Phi(s_t)
$$
如果 PCB 质量提高，奖励为正；质量下降，奖励为负。
例如：
- 初始分数 $-100$。
- 第一步变成 $-70$，奖励 $+30$。
- 第二步变成 $-80$，奖励 $-10$。
###### 7.4 Telescoping（望远镜求和）
当 $\gamma=1$ 时：
$$
\sum_{t=0}^{T-1}r_t
=\sum_{t=0}^{T-1}
[\Phi(s_{t+1})-\Phi(s_t)]
=\Phi(s_T)-\Phi(s_0)
$$
中间状态的分数相互抵消，因此累计逐步奖励等于终局奖励。
**Credit Assignment（信用分配）**：判断哪些动作对最终结果产生了贡献。
逐步奖励为 PPO 等强化学习算法提供更密集的反馈，通常比只在终局提供一个分数更容易学习。
##### 8. Environment Wrapper：统一 Agent 接口
<img src="/images/obsidian/6fff6269267f.png" alt="PCBWorld_图10_系统架构.png" width="680" />
> 论文附录图 10：左侧是 Search-Based Router、RL Agent、LLM Agent；右侧环境分成 L1–L4 四层，动作向下传递，状态与奖励向上返回。L1（虚线框）是未修改的 KiCad C++ 引擎，L2–L4 是论文的贡献。
###### 8.1 系统四层架构
- **L1：KiCad C++ Engine**：负责真实 PCB 数据、Push-and-Shove 增量布线、DRC。
- **L2：Python ↔ C++ Binding**：让 Python 能调用底层 C++ 功能。
- **L3：Python Wrapper**：封装 58 个步骤级 API，将引擎数据转换成结构化 Python 对象。
- **L4：Gymnasium Environment**：提供统一的动作分发、状态观察、奖励计算和动作合法性过滤。
典型交互：
`Agent → env.step(action) → KiCad → observation / reward → Agent`
**Wrapper（包装器）**：负责将复杂引擎功能转换成 Agent 可以使用的接口，本身不是新的决策模型。
<img src="/images/obsidian/867bc6b11f41.png" alt="PCBWorld_图3_Gym包装器.png" width="680" />
> 论文图 3：两个 Gym 包装器共享同一个引擎和统一的状态字典，再分别重新编码——RL 得到 token 序列，LLM 得到 S 表达式加工具调用格式。
###### 8.2 RL Wrapper
RL 需要适合神经网络处理的数值输入。
论文将焊盘、走线、过孔、点等对象转换为特征：
- **Fourier Feature Mapping**：将空间坐标映射为更丰富的位置特征。
- **Entity-Type Embedding**：编码对象类型，例如焊盘、走线或过孔。
- **Pointer Network**：从引擎提供的候选点或动作参数中选择目标。
这样避免让 RL 直接生成所有自由坐标，降低动作空间复杂度。
###### 8.3 LLM Wrapper
LLM 使用结构化文本表示 PCB。
论文采用 **S-expression（S 表达式）**，以嵌套括号表达 PCB 对象和关系。
主要保留：
- 坐标。
- 网络连接关系。
- 布线层。
- 有效设计规则约束。
- 紧凑动作历史及失败操作记录。
目的：减少无关 Token，同时让 LLM 能理解环境状态和工具反馈。
###### 8.4 两种 Wrapper 的区别
| | RL Wrapper | LLM Wrapper |
| --- | --- | --- |
| 输入 | 数值特征向量 | 结构化文本 |
| 决策模型 | RL 策略网络 | 大语言模型 |
| 动作生成 | 从候选动作中选择 | 生成结构化工具调用 |
| 反馈使用 | 状态与奖励 | 状态及工具执行结果 |

两者使用相同底层 KiCad 引擎。
##### 9. Benchmark 与 Baseline
###### 9.1 Benchmark 数据
PCBWorld-Bench 包括：
- **Synthetic PCB**：程序自动生成的合成电路板，可以控制规模与复杂度，适合大量训练。
- **Real PCB**：679 块真实开源电路板，用于测试真实设计实例上的表现与迁移能力。
<img src="/images/obsidian/f0d6a38ef5a0.png" alt="PCBWorld_图5c_D2合成板.png" width="320" /> <img src="/images/obsidian/126218bb3aef.png" alt="PCBWorld_图5e_D3-B真实板.png" width="360" />
> 论文图 5 节选：左为 D2 合成无网格板（4–6 个网络），右为 D3-B 真实开源板（5–42 个网络）。

合成数据适合训练和控制实验变量；真实数据有助于检查策略是否只适应简单的人工生成任务。
###### 9.2 不同类型的 Agent
- **Traditional Search-Based Router**：通过人工设计的搜索和启发式规则选择布线动作。
- **Grid-Action RL**：在离散网格中逐格决策。
- **Engine-Grounded RL**：学习调用真实引擎的布线动作。
- **Open-Loop LLM**：一次性生成布线方案，执行过程中不利用中间反馈修改决策。
- **Tool-Using LLM Agent**：反复调用工具，根据真实引擎反馈决定下一步。
**Open-Loop vs Closed-Loop**：
- 开环：生成方案 → 执行 → 最后检查。
- 闭环：观察 → 动作 → 引擎反馈 → 再观察 → 再动作。
PCBWorld 的重要特点是支持使用真实引擎反馈进行闭环决策。
<img src="/images/obsidian/1156f0ddcaba.png" alt="PCBWorld_图8b_LLM引擎参与.png" width="680" />
> 论文图 8(b)：D3-A 真实板上 LLM Agent 三种引擎参与方式对比——interactive（闭环）> plan-and-execute（开环，但动作经引擎执行）> engine-free（直接写 `.kicad_pcb` 线段），在 CP 和 Pot. 上对所有 GPT 模型都成立。
###### 9.3 评测关注点
论文通过引擎计算的工程指标评价布线质量，核心关注：
- 连通性及未完成连接。
- DRC / DRV。
- 总走线长度。
- 过孔数量。
- 合成 PCB 与真实 PCB 上的表现。
评测不只是判断是否画出一条线，还要衡量设计是否符合工程约束及其质量。
<img src="/images/obsidian/1b3501d1c9f3.png" alt="PCBWorld_图7_D3-A布线对比.png" width="680" />
> 论文图 7：三块 D3-A 真实板上各方法的布线结果，每列一种方法；红、蓝分别为两层铜上的走线。
##### 10. 总结
**PCBWorld = PCB 布线的 MDP 建模 + KiCad 原生引擎封装 + RL/LLM 交互接口 + 标准化 Benchmark。**
理解这篇论文需要区分：
- **MDP** 是序贯决策的理论框架。
- **KiCad Engine** 执行真实布线与状态转移。
- **Action Space** 决定 Agent 能控制哪些操作。
- **Reward Function** 衡量动作如何改善 PCB 质量。
- **Wrapper** 将环境转换成 RL 或 LLM 可使用的形式。
- **Benchmark** 提供统一的任务、数据与指标来比较不同方法。
**核心思想**：让 Agent 不再只操作简化网格或调整传统布线器的高层配置，而是能够通过原生 API 逐步控制真实 PCB 设计引擎，并根据每一步的反馈持续改进布线结果。
