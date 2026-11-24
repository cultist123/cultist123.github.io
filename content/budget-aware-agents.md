# 预算感知 Agent：多轮决策与资源约束奖励

论文：https://arxiv.org/abs/2610.28409
##### 1. 研究问题与核心思想
传统 Multi-Turn Agent 主要优化任务成功率，但实际执行受到 Token、工具调用次数和环境交互步数等资源预算限制。
论文研究两个递进问题：
1. **可行性**：能否只通过 RL，让 Agent 自主管理跨轮资源预算，而不依赖外部预算分配控制器？
2. **奖励设计**：哪种 Reward 能让 Agent 在不同预算下主动遵守约束，同时最大化任务成功率？
核心思想是 **Budget-Conditioned Policy（预算条件策略）**：让预算成为每一步策略决策的显式输入。
- **External Budget Controller**：外部模块替 Agent 决定如何分配或限制资源。
- **Natural Budget Compliance**：Agent 通过训练主动遵守预算，而非依靠硬性截断。
- **Dynamic Budget**：不同 Episode 可以指定不同预算；同一 Episode 的剩余预算持续变化。
训练设置：
- 每个环境与资源类型训练一个策略。
- 同一策略在训练时接收不同的初始预算。
- 每轮通过自然语言提供总预算和剩余预算。
- 测试策略能否适应训练中未出现过的预算。
**目标不是单纯减少资源消耗，而是在给定预算内尽可能完成任务。**
##### 2. Budget-Augmented POMDP：将预算纳入决策
###### 2.1 基础 POMDP
任务建模为：
$$
\mathcal M=\langle S,A,\mathcal T,\Omega,\mathcal O,R,\gamma,\mu_0\rangle
$$
- $S$：环境状态空间。
- $A$：动作空间。
- $\mathcal T$：状态转移分布。
- $\Omega$：观察空间。
- $\mathcal O$：观察分布。
- $R$：奖励函数。
- $\gamma$：折扣因子。
- $\mu_0$：初始状态分布。
Agent 无法直接访问完整状态 $s_t$，需要根据观察历史决策：
$$
h_t=(o_1,a_1,\ldots,a_{t-1},o_t)
$$
###### 2.2 状态增强与资源成本
将剩余预算加入原始状态：
$$
\boxed{\tilde s_t=(s_t,b_t)}
$$
其中 $b_t$ 为当前剩余预算。
每个动作的资源成本由 $\kappa$ 衡量：
- **Step Cost**：每执行一步，成本为 1。
- **Token Cost**：动作生成的 Token 数，包括思考 Token。
- **API Cost**：实际执行的 API 调用次数。
预算更新：
$$
\boxed{b_{t+1}=b_t-\kappa(a_t)}
\tag{3.1}
$$
增强状态转移：
$$
\boxed{
\tilde{\mathcal T}(s_{t+1},b_{t+1}\mid s_t,b_t,a_t)
=
\mathcal T(s_{t+1}\mid s_t,a_t)
\mathbf 1[b_{t+1}=b_t-\kappa(a_t)]
}
\tag{3.2}
$$
- $\mathcal T$：原环境状态如何变化。
- $\mathbf 1[\cdot]$：指示函数，保证预算按照真实成本更新。
**状态转移同时包含环境变化和预算消耗。**
###### 2.3 预算增强观察与策略
Agent 接收到的观察包含环境反馈和剩余预算：
$$
\boxed{
\tilde{\mathcal O}(o_{t+1},b\mid s_{t+1},b_{t+1},a_t)
=
\mathcal O(o_{t+1}\mid s_{t+1},a_t)
\mathbf 1[b=b_{t+1}]
}
\tag{3.3}
$$
对应预算条件策略：
$$
\boxed{
a_t\sim\pi(\cdot\mid x,h_t,b_t,B_0)
}
\tag{3.4}
$$
- $x$：任务。
- $h_t$：交互历史。
- $B_0$：初始总预算。
- $b_t$：当前剩余预算。
例如：
```text
<budget>
Budget remaining: 3400 of 8000 tokens
</budget>
```
同时提供 $b_t$ 和 $B_0$，使 Agent 能判断剩余预算比例：
$$
\frac{b_t}{B_0}
$$
**同一任务、相同环境历史下，预算不同，策略可以采取不同动作。**
<img src="/images/obsidian/bb3030984fa1.png" alt="Budget_图2_预算增强POMDP.png" width="680" />
Figure 2：Budget-Augmented POMDP。Agent 接收任务、历史、初始预算与剩余预算；环境执行动作后更新状态并扣除成本，再将新的预算信息以自然语言反馈给 Agent。
##### 3. Episode 与预算条件训练
###### 3.1 Episode 初始化和终止
每次 Episode 分别采样任务和预算：
$$
x\sim p_{\mathcal X},\qquad B_0\sim p_{\mathcal B}
$$
初始剩余预算：
$$
b_1=B_0
$$
Episode 可以通过三种方式结束：
1. Agent 主动执行 `complete_task`。
2. 环境自身终止。
3. 达到最大步数 $T_{\max}$。
停止时间：
$$
\boxed{
\tau=\min\left(
\inf\{t\geq1:a_t=a_\perp\},
\tau_{\mathrm{env}},
T_{\max}
\right)
}
$$
其中 $a_\perp$ 是主动结束动作，$\inf$ 表示最早满足条件的时刻。
**预算耗尽不一定导致 Episode 结束。**
允许 $b_t<0$，即超预算执行，以便通过惩罚信号学习自主遵守预算。
###### 3.2 标准化成本
完整轨迹：
$$
\zeta=(o_1,a_1,\ldots,o_\tau,a_\tau,o_{\tau+1})
$$
任务成功奖励：
$$
R(\zeta)\in\{0,1\}
$$
总资源消耗：
$$
C(\zeta)=\sum_{t\leq\tau}\kappa(a_t)
$$
标准化成本：
$$
\boxed{
\bar C(\zeta,B_0)=\frac{C(\zeta)}{B_0}
}
\tag{3.6}
$$
- $\bar C\leq1$：预算内。
- $\bar C>1$：超预算。
例如 $B_0=10$、$C=12$：
$$
\bar C=1.2
$$
表示超支 20%。
标准化成本让不同大小的预算可以使用统一的奖励设计。
###### 3.3 训练目标
将二元任务奖励转换为预算条件奖励 $\tilde R$：
$$
\boxed{
\max_{\pi\in\Pi}
\mathbb E_{
x\sim p_{\mathcal X},
B_0\sim p_{\mathcal B},
\zeta\sim\pi(\cdot\mid x,B_0)
}
[\tilde R(\zeta,B_0)]
}
\tag{3.5}
$$
**核心：在不同任务和预算下最大化平均预算条件回报。**
论文采用 Dr. GRPO 训练：
- 保留组内奖励均值作为 Baseline。
- 去掉奖励标准差归一化。
- 去掉响应长度归一化。
简化优势：
$$
A_i=R_i-\bar R
$$
目的是减少归一化机制可能造成的长度偏差，避免干扰预算使用行为的学习。
##### 4. Reward Design：如何教会 Agent 管理预算？
###### 4.1 奖励函数的设计维度
论文比较不同预算条件奖励，重点区分六种性质：
- **Hard Cutoff**：达到预算上限就停止。
- **Budget Jump**：超预算时奖励突然下降。
- **Within-Budget Cost**：预算内也惩罚资源消耗。
- **Overspend Magnitude**：超支越多，惩罚越重。
- **Negative Failure Return**：任务失败可能得到负奖励。
- **Learned Price**：学习预算对应的资源惩罚系数。
###### 4.2 主要奖励形式
| Reward | 核心机制 |
|---|---|
| Trunc | 到达预算后强制截断 |
| Gate | 超预算后奖励变为 0 |
| Gate-Neg | 超预算给予负奖励 |
| Rate | 超预算扣除固定幅度、可学习的惩罚 |
| Linear-Mag | 根据超支幅度惩罚 |
| Linear-Cost | 从预算内就开始按成本线性惩罚 |
| Sigmoid-Gate | 超预算后采用平滑惩罚 |
| Sigmoid | 预算内外均进行平滑成本惩罚 |
| Exp-Mag | 超预算后成功奖励指数衰减 |
| Dual | 组合超支惩罚与成本惩罚，并学习价格 |

其中几个代表性公式：
**Gate：**
$$
G=R\mathbf 1[C\le B]
$$
超过预算直接将奖励设为 0，不区分超支多少。
**Linear-Cost：**
$$
G=R-\min\left(1,\frac{C}{2B}\right)
$$
预算内也会随着资源消耗增加而降低奖励。
**Exp-Mag：**
$$
G=R\exp\left(-\frac{2(C-B)_+}{B}\right)
$$
其中 $(C-B)_+=\max(C-B,0)$。
预算内不扣分，超预算越多，成功奖励越低。
<img src="/images/obsidian/d510152f0101.png" alt="Budget_图1_奖励形状与性质.png" width="680" />
Figure 1：不同预算条件奖励的形状。横轴为 Episode Cost $C$，纵轴为塑形后的回报 $G$；蓝色实线为成功（$R=1$）、橙色虚线为失败（$R=0$），灰色阴影为超预算区域（$C>B$），Rate 和 Dual 的色带表示学习价格 $\Lambda_b\in[0,1]$ 的范围。
##### 5. 实验发现与评价标准
作者不只评价任务成功，还比较：
- **In-Budget Success**：在预算内完成任务的比例。
- **Natural Compliance**：无需外部截断，Agent 主动遵守预算的比例。
- **Utility**：综合任务结果与预算成本的评价。
- **Generalization**：对未见预算及不同任务条件的适应能力。
讨论过的主要发现：
- 预算塑形奖励能够改善预算内成功率和自然遵守表现。
- **Dual**：跨预算的平均效用较稳健，与逐预算最佳方法的平均效用差距较小。
- **Sigmoid-Gate**：在单个预算上经常取得最高效用。
- **Gate-Neg**：通常具有较高的自然预算遵守率。
<img src="/images/obsidian/4092c870e34c.png" alt="Budget_图3_预算效用与遵守率.png" width="680" />
Figure 3：域内表现。不同预算 $b$ 下的预算效用 $\mathcal U(b)$ 与遵守率 $\mathrm{Comp}(b)$，依次为 AppWorld 的步数、Token、API 调用预算和 BabyAI 轮次预算；竖虚线为训练预算，其余点为训练时未见过的预算。
**核心结论：不存在在成功率、效用、预算遵守率等所有指标上都最优的单一 Reward。**
这也是论文强调比较多种奖励函数，而不是只提出一个新奖励的原因。
##### 6. 工程扩展讨论：多个资源约束
以下是阅读过程中讨论的工程推论，不是论文已经验证的多资源联合训练结果。
论文当前设置是每个环境、每种资源类型分别训练策略，并让单个策略适应不同预算。
如果工程上同时考虑 Token、时间和 API 调用，可以将标量预算扩展为向量：
$$
\mathbf b_t=
\begin{bmatrix}
b_t^{\mathrm{token}}\\
b_t^{\mathrm{time}}\\
b_t^{\mathrm{API}}
\end{bmatrix}
$$
预算更新：
$$
\boxed{
\mathbf b_{t+1}
=\mathbf b_t-\boldsymbol\kappa(a_t)
}
$$
相应策略：
$$
a_t\sim\pi_\theta(\cdot\mid h_t,\mathbf b_t,\mathbf B_0)
$$
但多种资源单位不同，如何平衡奖励权重仍是额外问题。
工程上可区分：
- **RL Policy**：学习如何高效使用资源。
- **External Guardrails**：强制执行不可违反的时间、费用或安全限制。
**RL 学习主动遵守预算，不代表实际系统不再需要硬约束。**
##### 7. 核心总结
这篇论文的关键不是提出新 Agent 架构，而是研究如何通过 Reward Design 训练可适应动态预算的 Multi-Turn Agent。
核心机制：
$$
\boxed{
\text{Budget-Conditioned POMDP}
+\text{Budget-Shaped Reward}
+\text{RL}
}
$$
主要洞察：
1. **预算作为状态和观察的一部分**：Agent 每轮根据总预算、剩余预算及环境反馈调整决策。
2. **预算作为奖励约束**：通过成本惩罚和超支反馈，让 Agent 学会资源分配与主动停止。
3. **奖励形状影响行为**：不同惩罚机制在任务成功、资源效率和自然遵守之间存在权衡。
4. **单策略跨预算适应**：不必为每个预算分别训练策略，可以通过动态预算训练学习条件化行为。
**一句话总结：通过预算增强 POMDP 和预算条件奖励，让多轮 Agent 从单纯追求任务成功，转变为在不同资源约束下自主决定如何分配计算与交互预算。**
