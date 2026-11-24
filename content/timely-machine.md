# Timely Machine：时间感知的测试时扩展

论文：https://arxiv.org/abs/2601.16486
##### 1. 研究问题：时间感知的 Test-Time Scaling
###### 1.1 Test-Time Scaling（测试时扩展）
**Test-Time Scaling（TTS）**：模型参数保持不变，在推理阶段投入更多计算资源，以提升任务表现。
常见方法：
- 增加推理 Token，进行更深入的思考。
- 生成多个候选答案，再进行选择或验证。
- 使用搜索算法探索不同推理路径。
与 Training-Time Scaling 不同，TTS 不需要更新模型参数。
###### 1.2 Agent 中的时间成本
传统 TTS 主要关注模型推理计算量，但 Agent 还需要调用外部工具。
因此总时间不仅包含推理耗时：
$$
T_{\text{total}}
=T_{\text{reasoning}}+T_{\text{tools}}
$$
例如，生成少量 Token 却调用高延迟工具，可能比长时间直接推理更慢。
**核心问题：Agent 如何根据时间预算，决定继续推理、调用工具，还是结束任务？**
##### 2. 相关技术：推理能力的训练与扩展
###### 2.1 RLVR 与 GRPO
**RLVR（Reinforcement Learning with Verifiable Rewards）**：利用可客观验证的结果作为奖励，通过 RL 提升 LLM 推理能力。
例如数学题：
$$
R(y)=
\begin{cases}
1,&\text{答案正确}\\
0,&\text{答案错误}
\end{cases}
$$
训练目标：
$$
\max_\theta\mathbb E_{y\sim\pi_\theta(\cdot\mid x)}[R(y)]
$$
**GRPO（Group Relative Policy Optimization）** 通过同一任务的多个 Rollout 计算组内相对优势：
$$
A_i=\frac{R_i-\bar R}{\sigma_R+\epsilon}
$$
###### RLHF + GRPO 与 RLVR + GRPO
| | RLHF + GRPO | RLVR + GRPO |
|---|---|---|
| 奖励来源 | 人类偏好训练的奖励模型 | 正确答案、规则或执行测试 |
| 典型任务 | 对话质量、偏好对齐 | 数学、代码和可验证推理 |
| 优化算法 | GRPO | GRPO |

**RLHF/RLVR 决定奖励来源，GRPO 决定如何根据奖励优化策略。**
###### 2.2 Monte Carlo Tree Search（MCTS）
MCTS 通过搜索树探索多条可能的推理路径，而非只沿单一路径生成。
包含四个阶段：
1. **Selection**：选择值得探索的节点。
2. **Expansion**：生成新的推理分支。
3. **Simulation**：继续模拟或评估推理结果。
4. **Backpropagation**：将结果回传，更新分支价值。
MCTS 属于 Test-Time Scaling 的一种方式：通过增加测试时搜索计算量，提高找到优质答案的机会。
###### 2.3 Knowledge Distillation（知识蒸馏）
知识蒸馏通过 Teacher Model 指导 Student Model，使学生学习教师的输出行为。
**方法一：概率分布蒸馏**
$$
\boxed{
\mathcal L_{\mathrm{KD}}
=D_{\mathrm{KL}}(p_T\|p_\theta)
}
$$
展开：
$$
\mathcal L_{\mathrm{KD}}
=\sum_y p_T(y\mid x)
\log\frac{p_T(y\mid x)}{p_\theta(y\mid x)}
$$
- $p_T(y\mid x)$：教师输出 $y$ 的概率。
- $p_\theta(y\mid x)$：学生输出 $y$ 的概率。
目标是让学生输出分布接近教师分布。
**方法二：教师生成数据的 SFT 蒸馏**
$$
\boxed{
\mathcal L_{\mathrm{SFT}}
=-\mathbb E_{(x,y_T)}
\log p_\theta(y_T\mid x)
}
$$
其中 $y_T$ 是教师生成的答案。
对于多 Token 输出：
$$
\mathcal L_{\mathrm{SFT}}
=-\sum_{i=1}^{n}
\log p_\theta(y_i\mid x,y_{<i})
$$
两者的关系：
$$
D_{\mathrm{KL}}(p_T\|p_\theta)
=\mathbb E_{y\sim p_T}[-\log p_\theta(y\mid x)]-H(p_T)
$$
教师固定时，$H(p_T)$ 不依赖学生参数。
**区别：KL 蒸馏学习教师的概率分布；SFT 蒸馏模仿教师实际生成的答案。**
##### 3. Timely-RL：时间感知的 Agent 训练
###### 3.1 执行流程
<img src="/images/obsidian/0c52d52f94dc.png" alt="Timely_图1_TimelyRL流程.png" width="680" />
Figure 1：Timely-RL Pipeline。左：模型回答中的 `<tool_call>` 与工具返回的 Tool Response；右：Model 与 Tool Server 循环交互，Timer 累计时间，按时完成得到 Answer，否则 timeout。
Agent System 包含：
- **Model**：生成推理、回答及工具调用。
- **Tool Server**：执行工具请求，返回环境反馈。
- **Timer**：累计推理和工具执行耗时。
一次交互：
$$
\text{Model Response}
\rightarrow\text{Tool Call}
\rightarrow\text{Tool Response}
\rightarrow\text{Next Decision}
$$
工具调用包含：
- `tool_call`：指定调用哪个工具。
- `arguments`：传给工具的具体参数。
- `Tool Response`：工具执行后返回的观察或结果。
时间耗尽前完成任务得到 Answer，否则发生 Timeout。
###### 3.2 时间计算
每轮时间反馈为：
$$
\boxed{
t^{(i)}
=\alpha t_{\mathrm{gen}}^{(i)}
+t_{\mathrm{tool}}^{(i)}
}
$$
- $t_{\mathrm{gen}}^{(i)}$：第 $i$ 轮 LLM 推理耗时。
- $t_{\mathrm{tool}}^{(i)}$：工具执行耗时。
- $\alpha$：推理时间缩放系数，用于模拟不同推理速度。
模型不仅要考虑生成多少 Token，还要考虑工具调用实际消耗多少时间。
##### 4. 时间感知奖励设计
###### 4.1 Timely-RL Reward：公式 (9)
$$
\boxed{
R(t,r)=
\begin{cases}
0,&t>T_{\max}\\
r_f,&t\leq T_{\max},\ r=0\\
r_f+r+\lambda U(t),&t\leq T_{\max},\ r>0
\end{cases}
}
\tag{9}
$$
- $t$：任务总耗时。
- $T_{\max}$：最大时间预算。
- $r$：任务正确率奖励。
- $r_f$：格式正确且按时完成的固定奖励。
- $\lambda$：时间奖励的权重。
- $U(t)$：时间利用率函数。
三种情况：
1. **超时**：奖励为 0。
2. **按时完成但答案错误**：获得 $r_f$。
3. **按时完成且答案正确**：获得 $r_f+r+\lambda U(t)$。
###### 4.2 时间利用率函数：公式 (10)
$$
\boxed{
U(t)=\sin\left(
\frac{\pi}{2}
\min\left(\frac{t}{T_{\max}},1\right)
\right)
}
\tag{10}
$$
其中 $t/T_{\max}$ 是已使用时间的比例，$\min$ 将比例限制在 1 以内。
例如：
$$
U(0)=0
$$
$$
U(0.5T_{\max})\approx0.707
$$
$$
U(T_{\max})=1
$$
函数特点：
- 随时间增加而增加。
- 越接近时间上限，增长速度越慢。
- 使用正弦函数减小截止时间附近奖励变化的敏感度。
**特别注意：公式 (10) 并不是直接奖励更快完成。**
当 $\lambda>0$ 且任务同样正确、均未超时时，较长耗时反而对应较高的 $U(t)$。
因此必须区分论文希望模型具备的时间感知行为，与该公式实际提供的优化信号。
##### 5. 核心总结
传统 Test-Time Scaling 主要通过增加推理计算量提升性能，而 Timely Machine 将工具延迟和时间预算也纳入 Agent 决策。
**核心思路：**
$$
\boxed{
\text{Agent Execution}
+\text{Time Feedback}
+\text{Time-Aware Reward}
\rightarrow\text{RL Optimization}
}
$$
关键点：
1. **时间感知**：同时计算模型推理和工具执行的耗时。
2. **时间约束**：超过截止时间的任务直接获得零奖励。
3. **Timely-RL**：通过时间相关的奖励信号，训练模型适应不同时间预算。
**核心洞察：Agent 的测试时计算不仅是推理 Token，还包含工具调用成本，因此时间应当成为策略决策与强化学习优化的一部分。**
