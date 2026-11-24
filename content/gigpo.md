# GiGPO：多步 Agent 的分组与信用分配

论文：https://arxiv.org/abs/2505.10978
##### 1. 研究问题：多步 Agent 的信用分配
LLM Agent 通过与环境交互完成多步任务，一次完整 Rollout 表示为：
$$
\tau=(s_1,a_1,r_1,\ldots,s_T,a_T,r_T)
$$
- $s_t$：环境状态；$a_t$：动作；$r_t$：即时奖励。
- $\tau$：一条完整交互轨迹（Trajectory / Rollout）。
**核心问题：Credit Assignment（信用分配）**
- Agent 的奖励通常稀疏，可能只在任务结束时获得。
- 最终任务成功或失败，不能直接说明每一步动作是否正确。
- 需要更细粒度的训练信号，区分不同动作的贡献。
##### 2. 基础：Group-Based RL
###### 2.1 回合级分组
对同一任务 $x$，使用旧策略 $\pi_{\theta_{\mathrm{old}}}$ 采样 $N$ 条完整轨迹：
$$
\{\tau_1,\tau_2,\ldots,\tau_N\}
$$
每条轨迹获得总体奖励 $R(\tau_i)$。
传统 PPO 通常使用独立 Critic 估计价值函数；GRPO 则根据同组轨迹的奖励计算相对优势：
$$
A^E(\tau_i)
=\frac{R(\tau_i)-\mu_R}{\sigma_R+\epsilon}
$$
其中 $\mu_R,\sigma_R$ 分别是组内奖励的均值和标准差。
**优势**：无需独立训练价值网络，节省显存与计算开销。
**局限**：同一轨迹的不同步骤共享回合级优势，难以区分具体动作的好坏。
##### 3. GiGPO：Group-in-Group
GiGPO 在 Episode-Level Grouping 之外，利用已有轨迹构造 Step-Level Grouping。
###### 3.1 Anchor State Grouping（锚点状态分组）
核心观察：不同 Rollout 可能在不同时间遇到相同的环境状态。
设 $\tilde{s}$ 为共享的锚点状态，则：
$$
G^S(\tilde{s})
=\{(a_t^{(i)},r_t^{(i)})
\mid s_t^{(i)}=\tilde{s}\}
\tag{4}
$$
- $\tilde{s}$：不同轨迹中重复出现的环境状态。
- $a_t^{(i)}$：在该状态采取的动作。
- $r_t^{(i)}$：对应即时奖励。
GiGPO 使用轻量级哈希分组，收集相同状态下的动作实例。
**关键创新**：直接复用已有 Rollout，不需要为中间状态额外采样新轨迹。
<img src="/images/obsidian/8e18676d93f8.png" alt="GiGPO_图2_整体架构.png" width="680" />
Figure 2：同一任务生成多条 Rollout；上方计算 Episode-Level Advantage，下方把相同颜色的环境状态组成 Anchor State Groups，计算 Step-Level Advantage。
###### 3.2 从即时奖励到折扣回报
即时奖励 $r_t$ 只能反映当前反馈，而动作可能通过后续步骤影响任务结果。
因此使用 Discounted Return（折扣回报）：
$$
\boxed{
R_t^{(i)}
=\sum_{k=t}^{T}\gamma^{k-t}r_k^{(i)}
}
\tag{5}
$$
- $R_t^{(i)}$：从当前步骤开始的未来累计折扣奖励。
- $\gamma\in(0,1]$：折扣因子，控制未来奖励的重要性。
例如：
$$
r=[0,0,1],\quad\gamma=0.9
$$
则：
$$
R_1=0.81,\quad R_2=0.9,\quad R_3=1
$$
即使前两步即时奖励为 0，也能利用后续成功奖励提供训练信号。
步骤组因此变为：
$$
G^S(\tilde{s})
=\{(a_t^{(i)},R_t^{(i)})
\mid s_t^{(i)}=\tilde{s}\}
\tag{6}
$$
###### 3.3 Step-Level Relative Advantage
对相同锚点状态下的动作，比较其未来折扣回报：
$$
\boxed{
A^S(a_t^{(i)})
=\frac{R_t^{(i)}-\operatorname{mean}(\mathcal R_{\tilde{s}})}
{F_{\mathrm{norm}}(\mathcal R_{\tilde{s}})}
}
\tag{7}
$$
其中：
- $\mathcal R_{\tilde{s}}$：锚点状态 $\tilde{s}$ 对应组内所有折扣回报的集合。
- $\operatorname{mean}$：组内平均回报。
- $F_{\mathrm{norm}}$：归一化函数，如标准差。
**核心：在相同环境状态下，根据不同动作的长期回报估计相对优势。**
<img src="/images/obsidian/984c268f2a7d.png" alt="GiGPO_图3_WebShop步骤级分组.png" width="600" />
Figure 3：两条轨迹多次经过同一个搜索结果页面（红框），但后续动作不同：
- $\tau_1$：先点第 2 件商品，返回后再点第 1 件商品，最终成功。
- $\tau_2$：选择下一页，最终失败。
GiGPO 通过步骤级回报得到动作偏好：
$$
\text{第 1 件商品}>\text{第 2 件商品}>\text{下一页}
$$
说明即使动作属于同一条成功轨迹，也可以具有不同的长期效用。
这种方法既能利用稀疏终局奖励，也能利用稠密的逐步奖励。
##### 4. Group-in-Group Policy Optimization
###### 4.1 两级优势融合
$$
\boxed{
A(a_t^{(i)})
=A^E(\tau_i)+\omega A^S(a_t^{(i)})
}
\tag{8}
$$
- $A^E$：Episode-Level Advantage，评价整条轨迹。
- $A^S$：Step-Level Advantage，评价相同状态下的具体动作。
- $\omega\geq0$：控制步骤级优势权重。
例如：
$$
A^E=0.5,\quad A^S=-0.8,\quad\omega=1
$$
则：
$$
A=-0.3
$$
即使整条轨迹表现较好，局部表现较差的动作仍可能获得负优势。
###### 4.2 策略优化
GiGPO 沿用 PPO 风格的 Clipped Objective，将原本的优势替换为融合后的 $A$：
$$
\mathcal J_{\mathrm{GiGPO}}
=\mathbb E\left[
\min\left(
\rho_\theta A,\,
\operatorname{clip}(\rho_\theta,1-\epsilon,1+\epsilon)A
\right)
\right]
-\beta D_{\mathrm{KL}}(\pi_\theta\|\pi_{\mathrm{ref}})
$$
其中：
$$
\rho_\theta
=\frac{\pi_\theta(a_t\mid s_t,x)}
{\pi_{\theta_{\mathrm{old}}}(a_t\mid s_t,x)}
$$
- $\rho_\theta$：新旧策略采取同一动作的概率比。
- $\operatorname{clip}$：限制策略更新幅度。
- $\beta D_{\mathrm{KL}}$：限制策略偏离参考模型。
**GiGPO 的主要改进在 Advantage Estimation，而不是重新设计 PPO 优化器。**
##### 5. 核心贡献
1. **Hierarchical Credit Assignment**：结合回合级与步骤级优势，提供更细粒度的训练信号。
2. **Anchor State Grouping**：利用不同轨迹中的共享环境状态比较动作的长期效用。
3. **Efficient Group-Based RL**：无需独立 Critic，也无需针对中间状态额外生成 Rollout。
**核心总结**
传统 GRPO：
$$
\text{同一任务的 Rollouts}
\rightarrow \text{Episode Advantage}
$$
GiGPO：
$$
\text{Rollouts}
\rightarrow
\begin{cases}
\text{Episode Group}\\
\text{Anchor State Groups}
\end{cases}
\rightarrow A^E+\omega A^S
$$
GiGPO 通过在原有 Rollout 组内进一步构建共享状态的步骤组，实现更细粒度的信用分配，在保持分组 RL 训练效率的同时改善多步 Agent 的策略优化。
