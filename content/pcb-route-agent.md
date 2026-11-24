# PCBRouteAgent：大模型驱动的分层布线

论文：2026，arXiv:2611.08175
##### 1. 研究背景与核心问题
<img src="/images/obsidian/ddbf4c160f4f.png" alt="PCBRouteAgent_图1_布线任务.png" width="520" />
> 论文图 1：PCB 布线任务。输入是已放置元件、焊盘和飞线（Guide line）；输出是满足线宽、间距规则的铜线，红为正面铜、蓝为背面铜，Via 连接两层。

PCB 自动布线需要连接所有目标网络，同时满足线宽、间距、层切换等设计约束，并尽量减少走线长度、过孔数量和设计规则违规。传统自动布线器主要依赖：**Heuristic Search**——利用路径长度、目标距离指导搜索而非穷举；**Net Ordering**——决定网络布线先后；**Congestion-Aware Cost**——避开拥挤区域，避免占据后续网络所需空间；**Geometric Constraints**——满足线宽、间距、障碍物和层间连接规则。
复杂 PCB 中不同网络竞争有限空间，某条线的局部最优路径可能导致其他网络无法连接，因此仍需参数调整、Rip-up and Reroute（拆线重布）及人工干预。现有学习方法探索了 **Global Routing**（线路大致经过哪些区域）、**Net Ordering**（布线顺序）、**Fanout**（密集引脚扇出位置），但通常只针对部分决策。
**核心问题**：能否让多模态 LLM Agent 同时承担全局规划、工具执行协调和失败后的重新规划，构建更完整的自动 PCB 布线系统？
##### 2. 核心思想
分层闭环：**Global Routing Planner → Detailed Routing Executor → Execution Feedback → Replanning**。**Global Planner**：LLM 根据图像和结构化信息决定连接拓扑、网络顺序、布线走廊和换层区域；**Detailed Executor**：调用 KiCad 原生布线引擎生成实际铜线；**Execution Feedback**：报告失败位置、原因、障碍物和已完成连接；**Replanning**：LLM 生成局部规划补丁再交执行器。
**核心设计**：LLM 负责高层决策，传统引擎负责精确几何；局部问题优先局部修复，复杂问题再调用 LLM 重规划。
##### 3. 整体系统架构
<img src="/images/obsidian/525d5855f2ac.png" alt="PCBRouteAgent_图2_总览.png" width="720" />
> 论文图 2：从左到右为 Inputs（未布线板、设计规则、四种板视图、结构化 Sidecar）、Global Routing Planner（MST 拓扑与网络排序、走廊与过孔区域、反馈驱动重规划）、Detailed Executor（Source Anchor → Waypoint → Via → Target）、Output（保存的 PCB 与 CP/Routability/Wire Length/Via Count/DRV 评估）；底部箭头是执行反馈回路。

###### 3.1 Inputs
**Visual Board Views**：整体布局（Context）、顶层与底层视图、待布线需求（Demand）。**Textual Structured Sidecar**：焊盘坐标、Netlist、层信息、设计规则。图像提供空间背景，结构化信息提供精确连接与几何数据。
###### 3.2 Output
实际布线后的 PCB 文件，由官方评估器检查：**CP（Clean Pass）**——完整布通且满足合法性检查；**Routability**——布通网络比例；**Wire Length**——走线总长；**Via Count**——过孔数；**DRV**——设计规则违规数。
##### 4. Global Routing Planner
###### 4.1 Connection Topology（连接拓扑）
一个 Net 含多个焊盘，原始 PCB 只规定必须电气连通，不规定连接顺序（P1–P2–P3–P4 或其他拓扑均可）。论文用 **MST** 生成初始拓扑：对网络 $n$ 构建 $G_n=(C_n,E_n,w_n)$，$C_n$ 为已连通焊盘簇，$E_n$ 为候选簇间连接，$w_n(e)$ 为两簇焊盘中心最小欧氏距离，并对不兼容焊盘层加惩罚。$K_n$ 个簇选 $K_n-1$ 条连接使总权重最小。
**注意**：MST 只决定哪些簇相连，不生成铜线路径，实际布线仍可能因障碍调整。
###### 4.2 Net Ordering（网络排序）
按初始预计布线长度排序，先短后长（A 10mm → B 25mm → C 50mm）。这是启发式初始化，不保证全局最优，可按反馈调整。**区别**：Topology 管一个网络内部哪些簇相连；Ordering 管多个网络之间先布谁。
##### 5. Spatial and Layer Planning（空间与层规划）
采用 **Coarse-to-Fine**，把高层空间指导与底层精确执行分开。
###### 5.1 Routing Corridor（布线走廊）
对候选连接 $e$ 给出有序矩形走廊 $Q_e=(Q_{e,1},\ldots,Q_{e,m_e})$：以端点包围盒为基础向四周扩展 $\delta$，作为允许搜索路径的区域。走廊给方向，但不限定固定坐标或拐角。
###### 5.2 Via Region（过孔候选区域）
两端点无法同层连接时需 Via 换层。Planner 不给精确坐标，而是以连接中点为中心扩展 $\delta$ 得到区域 $V_e$，执行器在其中找满足尺寸与间距的位置。**区别**：Corridor 指导线在哪里走；Via Region 指导大概在哪里换层。
##### 6. Detailed Routing Executor
<img src="/images/obsidian/5650f34fd5f8.png" alt="PCBRouteAgent_图2局部_执行器.png" width="380" />
> 论文图 2 局部：F.Cu 上从 Source Anchor 出发，在两个走廊重叠处生成 Waypoint，于 Via Region 换到 B.Cu，再到达 Target Anchor；下方为逐段执行顺序。

###### 6.1 Guided Routing Execution
输入：源/目标簇、有序走廊 $Q_e$、可选过孔区域 $V_e$、层约束与设计规则。流程：① 从源簇选合法起始焊盘；② 按当前与下一走廊的重叠区生成候选 Waypoint；③ 调用 KiCad PNS 布到候选点；④ 成功则提交线段进入下一走廊；⑤ 必要时在规划区域放过孔换层；⑥ 到达目标簇后检查是否真正电气连接。**Waypoint** 只引导中间阶段，不是必须严格遵循的折线。
###### 6.2 PNS（Push-and-Shove Router）
KiCad 交互式布线引擎：**Walkaround** 绕开障碍；**Push and Shove** 推动可调整的已有线；**规则约束检查** 处理线宽、间距。分工：LLM 决定大致走哪里，Executor 选候选点和执行顺序，PNS 负责合法铜线几何。
###### 6.3 为什么需要最终连通性验证？
中间点成功 ≠ 整个 Net 连通（如 P1 → Waypoint 成功，Waypoint → P2 失败），必须验证源簇与目标簇真正电气连通。
##### 7. Local Recovery（局部恢复）
失败后不立即调用 LLM，先做有限局部恢复：**Walkaround / Shove**；**Alternative Waypoints**——换走廊内候选点；**A\* Search**——为困难同层障碍搜索新路径再交 PNS 实现；**Backtracking**——退回之前成功阶段换候选点或端点（P1 → A → B → P2 中 A → B 失败，改试 P1 → A → C → P2，仍失败再往前回退）。**目的**：保留整体规划和已成功线路，减少昂贵的全局重规划。
##### 8. Feedback-Driven Replanning
###### 8.1 触发条件
局部恢复预算耗尽、连接始终无法完成、或规划的换层无法实现时，Executor 生成结构化反馈交给 Planner。
###### 8.2 Structured Execution Feedback
对未解决连接 $e$ 构建反馈包 $F_e$：已尝试的操作、最后成功到达的位置、潜在障碍和冲突、受影响的走廊、规划与执行的偏差。**作用**：把失败变成下一轮规划的证据，而不只是失败标志。
###### 8.3 LLM 生成局部规划补丁
$$\Delta G_t=M_\theta(I,S,G_t,D_t,K_t;P_{\mathrm{sys}},P_{\mathrm{replan}})$$
$M_\theta$ 多模态 LLM；$I$ 初始 PCB 图像；$S$ 结构化板信息；$G_t$ 当前规划；$D_t$ 未解决连接的反馈集合；$K_t$ 更新后的连通性摘要；$P_{\mathrm{sys}}$、$P_{\mathrm{replan}}$ 系统与重规划提示模板；$\Delta G_t$ 规划补丁。**$I$ 为何不变？** 它提供稳定的原始板级背景，执行中的变化由反馈和连通性摘要反映。
###### 8.4 局部规划补丁
例：原计划 P1 → 上方走廊 → P2，反馈"上方走廊阻塞"，补丁改走下方走廊并按需调整 Via Region。补丁只改受影响的高层决策（连接端点、Corridor、Via Region、Net Ordering），尽量保留已成功连接。
###### 8.5 补丁验证
检查补丁是否对应当前规划版本、涉及的连接是否有效、走廊和过孔区域是否合法、是否误伤已接受连接。无效则要求 LLM 修正；连续失败或预算耗尽则停止重规划。
##### 9. 分层错误恢复机制
| 层级 | 负责模块 | 处理方式 |
| --- | --- | --- |
| 局部恢复 | Detailed Executor | 绕行、Shove、换 Waypoint、A*、回溯 |
| 全局重规划 | Global Planner | 根据结构化反馈修改走廊、过孔区域或连接顺序 |

闭环：Global Plan → Detailed Execution → Local Recovery → Structured Feedback → LLM Replanning → Patch Validation → Continued Execution。**优势**：简单问题不反复调用 LLM，复杂问题利用执行证据调整高层策略。
##### 10. 终止条件与结果评估
终止：所有目标连接完成、没有剩余任务或恢复尝试、执行预算耗尽。结束时回滚失败的连接尝试，保留一致 PCB 状态并报告未完成连接，最后由官方评估器判断完整性、合法性及线长、过孔、违规情况。
##### 11. PCBWorld-Bench 评测数据
| 划分 | 数量 | 类型 |
| --- | ---: | --- |
| D2 | 128 | 合成 PCB |
| D3-A | 99 | 小型真实 PCB |
| D3-B | 10 | 中型真实 PCB |
| D3-C | 10 | 大型真实 PCB |

共 247 块（128 合成 + 119 真实）。不应只按板数评价规模，每块板可能含大量网络和连续布线动作；但中、大型真实板样本少，解释其成功率时要注意统计波动。
##### 12. 与前两篇论文的区别
| 论文 | 核心方法 | Agent 主要负责 |
| --- | --- | --- |
| FanoutNet | 深度强化学习 + 传统布线器 | 选择扇出位置 |
| PCBWorld | KiCad 原生引擎 + 统一交互环境 | 提供 RL/LLM Agent 训练与评测基础设施 |
| PCBRouteAgent | 多模态 LLM + 分层规划与执行 | 全局布线规划、执行协调和失败重规划 |

**FanoutNet** 学习某个布线子问题的决策；**PCBWorld** 建立使用真实布线引擎的 Agent 环境；**PCBRouteAgent** 构建在这种工程环境中工作的完整闭环 LLM Agent。
##### 13. 总结
**Multimodal Input**——图像 + 精确结构化信息；**MST**——初始化网络内部拓扑；**Net Ordering**——多网络先后；**Routing Corridor**——高层空间引导；**Via Region**——候选换层区域；**KiCad PNS**——真实、合规的局部布线；**Local Recovery**——绕行、搜索、回溯解决局部失败；**Structured Feedback**——失败转为重规划证据；**LLM Replanning**——只改受影响的高层规划。
**核心思想**：不让 LLM 计算每段铜线的精确坐标，而让它负责全局规划和失败后的策略调整，由成熟 EDA 引擎完成精确布线。
**一句话总结：PCBRouteAgent 将多模态 LLM 的高层规划能力与 KiCad 的确定性几何执行能力结合，通过局部恢复和反馈驱动重规划，实现面向真实 PCB 布线任务的分层闭环 Agent。**
