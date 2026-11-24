# CADET：可执行示范与 PCB 布线数据构造

论文：2026，arXiv:2611.16913
##### 1. 研究背景与核心问题
PCB 自动布线需连接每个网络的所有焊盘（Pad），满足 DRC，并尽量减少线长与过孔数。现有 PCB 数据只给最终布线结果，缺少完整的状态—动作轨迹：
- **最终 PCB**：告诉模型布完后长什么样；**Executable Demonstration**：告诉模型怎样一步步操作得到它。
- RL 从零训练布线策略探索量大、大量随机动作无效；BC 可借专家示范加速，但前提是有大量可靠示范。

**研究问题：如何自动生成大量有合法解的 PCB 任务，并同步生成能在真实布线引擎中回放的动作示范？**
##### 2. 核心贡献与定位
主要贡献是 **数据生成方法**，不是新 RL 算法：① **Inductive Construction**：逐个生成焊盘，每加一个就验证能否合法布线；② **Executable Demonstrations**：用传统启发式搜索生成布线动作，记录动作序列与状态；③ **Replay Verification**：从所有焊盘固定的初始状态重新执行示范，确保可复现；④ **大规模数据集**：约 100,000 块合成 PCB 及示范；⑤ **BC + PPO 验证**：用数据预训练再 RL 微调，检验数据价值。
**关键澄清：数据生成阶段不使用 RL**。生成数据 = 随机采样 + 启发式搜索 + PCB 引擎 + 回放验证；训练模型 = BC 预训练 + PPO 微调。**卖点**：把传统布线算法变成可大规模生产可靠任务与动作示范的数据系统。
##### 3. 整体框架
<img src="/images/obsidian/9dfc1964a33d.png" alt="CADET_fig2.png" />
(a) 采样 PCB 属性 → 生成新焊盘 → TryConnect 搜索 → 接受或重试 → 保存示范；(b) RouteDemos → BC → PPO → 在真实 PCB 上评测。
- **阶段一（生成数据，不涉及 RL）**：参考 PCB → 采样参数 → 逐步加焊盘 → TryConnect 搜合法线路 → 记录动作 → Replay 验证 → 数据集。
- **阶段二（训练策略）**：示范 → BC（学状态—动作映射）→ PPO（与环境交互按奖励改进）→ 最终策略。策略负责解新的布线任务，而不是生成训练板。
##### 4. PCB 任务与可执行示范
<img src="/images/obsidian/d0f875466518.png" alt="CADET_fig1.png" />
Figure 1：与 EDA 引擎交互布线。策略观察板状态 $s_t$，从合法动作集 $\mathcal A(s_t)$ 选一个动作 $a_t$（如 `make_line(P4)`）调用 KiCad 操作；引擎执行（walkaround/shove 绕障放线和过孔），返回 $s_{t+1}$ 及连通性、DRC 结果；奖励 $r_t=\Phi(s_{t+1})-\Phi(s_t)$。
**Pad** 连接元件引脚的金属区；**Trace** 连接焊盘的铜线；**Via** 连接不同铜层的导电孔。构造阶段程序可增加、拒绝、剪枝焊盘；布线任务阶段所有焊盘位置、网络、约束已固定，Agent 只能布线。
示范轨迹 $\tau=(s_0,a_0,s_1,\ldots,a_{T-1},s_T)$：$s_0$ 布线前状态，$a_t$ 引擎级操作，$s_T$ 最终结果；$F(s,\tau)$ 表示从 $s$ 依次执行 $\tau$ 得到的状态。
**为什么要动作轨迹？** 同一最终 PCB 可由不同过程得到：$\tau_1\neq\tau_2,\ F(s_0,\tau_1)=F(s_0,\tau_2)$，只有最终 PCB 无法唯一还原专家操作；CADET 保存可直接用于 BC 的状态—动作序列。##### 5. Inductive Construction（归纳式构造）
<img src="/images/obsidian/567436af68c0.png" alt="CADET_alg1.png" />
**5.1 采样属性**：从真实参考数据集 $D_{\mathrm{ref}}$ 估计分布 $q_\psi$，采样板尺寸 $W,H$、网络数 $N$、各网络焊盘数 $P_i$、网络属性与设计约束，使合成板在规模、焊盘密度上接近真实板。
**5.2 逐步加焊盘**（对第 $i$ 个网络）：随机生成 $p_0$，$S_i=\{p_0\}$ → 在已有焊盘附近提出新焊盘 $p$ → TryConnect 尝试接入 → 成功则 $S_i\leftarrow S_i\cup\{p\}$，$D\leftarrow D\cup\{\tau_p\}$（$\tau_p$ 为连接 $p$ 的轨迹），失败则重采样。
**意义**：直接法是"随机生成整板 → 搜索布线 → 可能整板无解"；CADET 是"生成一个焊盘 → 立即搜合法连接 → 成功才接受"，**构造问题时同步构造了解**，大幅减少无解任务。
##### 6. TryConnect：传统启发式搜索生成示范
<img src="/images/obsidian/9c5791076d53.png" alt="CADET_alg2.png" />
TryConnect 是数据生成用的搜索算法，不是 RL 策略。目标：给定新焊盘 $p$ 和已有网络 $S_i$，找到将 $p$ 接入 $S_i$ 的合法动作序列。
**流程**：初始化优先队列 → 弹出估计代价最低的动作序列 → 引擎执行 → 检查连通性与 DRC → 已连通且零 DRV 则返回轨迹，否则扩展合法且未访问的状态 → 预算耗尽返回 FAIL。
**代价**：$f(\tau_p,a)=2(|\tau_p|+1)+\mathbf1_{\mathrm{via}}(a)+\begin{cases}0,&x_a\in S_i\\h(x_a),&\text{否则}\end{cases}$
其中 $|\tau_p|+1$ 为动作数，$\mathbf1_{\mathrm{via}}$ 表示是否用过孔，$x_a$ 为动作终点，$h(x_a)$ 由网格 Dijkstra 估计剩余连接成本。即偏好动作少、过孔少、离目标近。**注意**：这是人工启发式，不是 RL 学到的价值函数；示范合法但不保证全局最优。
##### 7. Replay Verification（回放验证）
**为什么需要？** 构造时焊盘逐个加入（加 P1 时 P2、P3 还不存在，加 P2 后原线路可能受影响），而真实任务要求所有焊盘一开始就存在，构造时合法的动作在最终板上未必可执行。
**过程**：收集所有已接受焊盘构建 $s_0$ → 新开引擎实例、固定全部焊盘 → 依次回放记录动作 → 失效则尝试修复，必要时剪枝相关焊盘 → 检查全网连通与 DRV → 通过者进入 BC 数据：$D_{BC}=\operatorname{Replay}(s_0,D)$。
**价值**：数据不仅有合法最终板，还有能从固定初始状态实际执行的动作。
##### 8. 焊盘数校准
合法性检查、重试预算、Replay 剪枝会使实际焊盘数低于目标：$\hat P=\sum_i\hat P_i<P=\sum_iP_i$。因此放大网络数 $\bar N=\operatorname{round}(\alpha N)$，$\alpha$ 通过试运行对比生成板与参考板的焊盘密度估计，目的是减轻生成偏差、贴近真实分布。
##### 9. 用生成数据训练 Agent：BC + PPO
**9.1 BC**：$\mathcal L_{BC}(\theta)=-\mathbb E_{(s,a)\sim D_{BC}}\log\pi_\theta(a\mid s)$，提高选择示范动作的概率。**BC 学的是 TryConnect 产生的布线行为，不是学它如何搜索或生成焊盘。**
**9.2 Reward**：势函数 $\Phi(s)=\Phi_{\mathrm{con}}(s)-[f_{\mathrm{drv}}(s)+\lambda_w\ell(s)+\lambda_v n_{\mathrm{via}}(s)]$，即 连通收益 − 违规惩罚 − 线长成本 − 过孔成本；逐步奖励 $r_t=\Phi(s_{t+1})-\Phi(s_t)$，改善 PCB 质量得正奖励。
**9.3 PPO 微调**：从 $\pi_{\theta_{BC}}$ 出发，加 KL 惩罚 $J(\theta)=J_{\mathrm{PPO}}(\theta)-\beta\mathbb E_s D_{\mathrm{KL}}\left(\pi_\theta(\cdot\mid s)\parallel\pi_{\theta_{BC}}(\cdot\mid s)\right)$，$\beta=0.05$；允许改进同时防止过度偏离 BC 学到的有效行为。
**9.4 Critic Warm-up**：BC 没训练价值网络，故先预热 Critic，并阻断 Critic 对共享编码器的梯度，避免破坏已学表示。**RL 学的是布线策略，不是生成数据的方法。**
##### 10. 为什么不直接用 TryConnect？
TryConnect 遇到新板要不断展开、评估候选；策略网络学 $\pi_\theta(a\mid s)$，直接由状态预测下一步动作。

| 方法 | 主要作用 |
| --- | --- |
| TryConnect | 搜索合法走线，生成专家示范 |
| BC | 模仿示范中的布线动作 |
| PPO | 自主交互，按奖励改善策略 |
| 最终策略 $\pi_\theta$ | 在新 PCB 上直接布线决策 |

学习策略潜在优势是省去每次从头搜索、通过训练得到更好决策；是否更快更优需实验验证，不能仅凭架构断言。
##### 11. 实验结果与数据价值
真实 PCB 测试中完整布通且零 DRV 成功率：**随机初始化 PPO 38.0% → CADET BC+PPO 67.2%（+29.2 pp）**，支持"CADET 示范做 BC 预训练能为 PPO 提供更好初始化"。
需注意：BC+PPO 有额外的数据生成与预训练成本；成功示范不一定最优；合成任务与复杂工业 PCB 仍有差距；不等于 RL 已全面超过传统布线器。
##### 12. 局限与创新性分析
- **传统算法依赖**：模型可能继承搜索器偏好；数据受搜索器可解范围限制；搜索成功≠最优。CADET 没有消除对传统布线器的依赖，而是把它用来生产数据。
- **训练成本**：合成构造 + TryConnect + Replay + BC + PPO 交互，评估效率不能只算 PPO 阶段。
- **泛化**：统计特征相似≠覆盖工业设计全部复杂约束；真实板提升是泛化证据，但不证明能处理所有工业级 PCB。
- **算法创新 vs 系统贡献**：组件（随机采样、Best-First/Dijkstra、BC、PPO、KL 正则）都是已有技术，创新在于组合成可靠的大规模数据生成流水线。
##### 13. 与相关 PCB 论文的区别

| 论文 | 主要研究内容 |
| --- | --- |
| FanoutNet | 用 RL 优化芯片引脚扇出位置 |
| PCBWorld | 将 KiCad 封装成真实引擎驱动的 Agent 训练与评测环境 |
| PCBRouteAgent | 多模态 LLM 做全局规划、详细执行协调与失败重规划 |
| CADET | 传统搜索构造 PCB 与可执行示范，再用于 BC + PPO |

CADET 定位是 **数据与训练方法**，不是新的 LLM Agent 架构或 PCB 引擎。
##### 14. 总结
**CADET = Inductive Construction + TryConnect + Replay Verification + BC + PPO。** ① 数据怎么来：随机采样 + 传统启发式搜索逐步生成焊盘与合法动作，再 Replay 验证；② RL 的作用：不参与数据生成，只在 BC 初始化后在环境中自主布线、按奖励优化。
**一句话：CADET 不是用 RL 生成数据，而是用传统搜索构造大量有解的 PCB 和动作示范，再用 BC + PPO 把示范转化为可泛化的学习型布线策略。**
