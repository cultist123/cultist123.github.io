# 实时推理 Agent：Token Clock 与双线程推理

论文：https://arxiv.org/abs/2511.04898
##### 1. 研究问题：动态环境中的实时推理
传统 Agent 评测通常假设环境在模型推理时暂停，因此可以使用大量 Token 进行思考。
但在真实动态环境中，环境不会等待 Agent：
- **Reactive Agent（反应式）**：推理速度快，但容易忽略长期风险。
- **Planning Agent（规划式）**：能够进行深入推理，但可能错过行动时机。
- **核心矛盾**：推理质量（Reasoning Quality）与反应延迟（Latency）之间的权衡。
论文的核心贡献：
1. **Real-Time Reasoning Gym**：将推理耗时纳入动态环境评测。
2. **Token Clock**：利用生成 Token 数量模拟推理时间。
3. **AgileThinker**：并行运行规划与反应线程，兼顾长期规划和实时决策。
##### 2. Real-Time Reasoning Gym 与 Token Clock
###### 2.1 传统 Gym 与实时 Gym
传统环境：
```python
obs, done = env.reset()
while not done:
    agent.observe(obs)
    agent.think()  # 等待推理完成
    action = agent.act()
    obs, done, reward = env.step(action)
```
实时环境：
```python
obs, done = env.reset()
while not done:
    agent.observe(obs)
    agent.think(timeout=T_E)
    action = agent.act() or DEFAULT_ACTION
    obs, done, reward = env.step(action)
```
- `observe(obs)`：Agent 接收环境观察。
- `think()`：Agent 进行推理。
- `act()`：输出动作。
- `env.step(action)`：执行动作，返回新观察和奖励。
- `T_E`：环境每一步的时间预算。
- `DEFAULT_ACTION`：Agent 未及时输出有效动作时使用的默认动作。
**核心区别**：传统 Gym 等待 Agent 思考结束；Real-Time Gym 要求 Agent 在环境规定的时间内行动。
###### 2.2 Token Clock
Token Clock 用生成 Token 数量近似推理耗时：
$$
T_{\text{reasoning}}\approx N_{\text{tokens}}\times TPOT
$$
- $N_{\text{tokens}}$：生成 Token 数量。
- $TPOT$：每个输出 Token 的平均耗时。
- $T_{\text{reasoning}}$：推理耗时。
用 Token 预算表示环境时间，可以减少不同 GPU 速度对评测的影响。
**关键思想：思考不再是免费的，推理消耗的计算预算会影响 Agent 的行动时机。**
##### 3. AgileThinker：并行反应与长期规划
###### 3.1 双线程架构
AgileThinker 同时运行两个线程：
**Planning Thread（规划线程）**
- 使用较长推理分析未来风险。
- 可以跨多个环境步骤持续思考。
- 将已有的推理信息提供给反应线程参考。
**Reactive Thread（反应线程）**
- 每个环境步骤都需要及时输出动作。
- 根据当前 Observation 和 Planning Reference 决策。
- 不必等待完整规划结束。
整体关系：
$$
\text{Current Observation}+\text{Planning Reference}
\rightarrow\text{Reactive Action}
$$
规划线程负责长期判断，反应线程负责及时执行。
###### 3.2 时间与计算预算分配
每个环境步骤的总时间为：
$$
\boxed{T_E=(T_E-T_R)+T_R}
$$
- $T_E$：环境每一步的总时间预算。
- $T_R$：预留给 Reactive Thread 的时间。
- $T_E-T_R$：反应线程启动前用于规划推理的时间。
规划可以持续多个环境步骤，反应线程必须按环境节奏生成动作。
<img src="/images/obsidian/6a8239928868.png" alt="RealTime_图4_AgileThinker双线程.png" width="680" />
Figure 4：AgileThinker 的并行线程与时间调度。黄色表示持续规划，蓝色表示每步反应，橙色箭头表示规划信息被反应线程引用。
##### 4. 为什么需要两种推理？
###### 4.1 Freeway 案例
在车辆持续移动的环境中：
- Reactive Agent 可能认为当前 DOWN 安全，却忽略未来碰撞。
- Planning Agent 能识别未来风险，但长时间思考会使决策过时。
- AgileThinker 利用规划信息及时选择 STAY、UP 等动作。
<img src="/images/obsidian/4652800ceac1.png" alt="RealTime_图3_静态与动态环境.png" width="680" />
Figure 3：静态与动态环境下的 Agent 对比（Freeway 示例）。
###### 4.2 Snake 案例
图 6 的关键是 Step 3：

| 方法 | 决策 | 问题 |
|---|---|---|
| Reactive | R（右） | 追逐最近食物，忽略后续被困风险 |
| Planning | 根据旧状态规划 | 能识别陷阱，但推理结果可能过时 |
| AgileThinker | U（上） | 结合当前环境与长期规划，避开风险 |

Reactive 认为 $(5,2)$ 的食物距离近、当前可达。
Planning 发现该食物可能导致贪吃蛇被困，但它仍在处理较早的状态。
AgileThinker 将 Planning 的风险判断与当前 Observation 结合，选择 U。
<img src="/images/obsidian/373bd2159000.png" alt="RealTime_图6_Snake决策轨迹.png" width="680" />
Figure 6：Snake 中三类 Agent 的决策与推理轨迹。
**核心：及时的动作不一定长期正确；长期正确的规划也可能因为延迟而失效。**
##### 5. 如何分配反应与规划的计算资源？
###### 5.1 Reactive Token Budget
设每个环境步骤的总预算为：
$$
N_{T_E}=8k
$$
其中 $N_{T_R}$ 表示分配给反应线程的 Token 预算。
- **预算过小**：反应线程来不及充分利用规划信息。
- **预算过大**：反应线程可能早已完成动作生成，剩余预算闲置，同时挤占规划时间。
因此，预算不是越大越好。
###### 5.2 使用 Token Usage CDF 估计预算
CDF（累积分布函数）：
$$
\boxed{F(n)=P(N_{\text{used}}\leq n)}
$$
表示反应线程自然生成的 Token 数量不超过 $n$ 的概率。
当 $F(n)$ 接近 1 时，说明该预算足以让绝大多数反应推理自然完成。
实验中较优的预算：

| 环境 | Reactive Budget |
|---|---|
| Freeway | 约 5k Token |
| Snake | 约 2k Token |
| Overcooked | 约 2k Token |

<img src="/images/obsidian/6758694943cf.png" alt="RealTime_图7_TokenBudget与CDF.png" width="680" />
Figure 7：Token Budget 对性能的影响及 Token Usage CDF。
**结论：根据反应线程自然的 Token 使用分布分配预算，尽量减少提前截断和计算空闲。**
##### 6. Token Clock 的实际时间验证
###### 6.1 Token 数量与 Wall-Clock Time
作者通过 DeepSeek API 测量推理耗时，并进行线性拟合：
$$
\boxed{T=\alpha N+\beta}
$$
- $T$：总运行时间。
- $N$：生成 Token 数量。
- $\alpha=0.0473$ 秒/Token。
- $\beta=334.55$ 秒：拟合截距。
- $R^2=0.9986$：拟合优度，表明实验数据与线性模型高度吻合。
因此，Token 数量可以作为推理耗时的近似指标。
###### 6.2 Wall-Clock Time 下的实验
作者使用约 $0.047$ 秒/Token 的估计，将环境每一步设为约 6 分钟，对应约 8k Token 的时间尺度。

| 环境 | Reactive | Planning | AgileThinker |
|---|---:|---:|---:|
| Freeway | 0.24 | 0.12 | **0.88** |
| Snake | 0.37 | 0.04 | **0.45** |
| Overcooked | 0.57 | 0.00 | **0.89** |

三个环境中，AgileThinker 均优于单独的 Reactive 和 Planning。
这说明：
- Token Clock 的时间抽象具有实验依据。
- AgileThinker 的优势在真实 API 耗时约束下仍然存在。
注意：这里的实时性是相对于环境更新周期而言，不等于已经验证了毫秒级机器人控制能力。
##### 7. 核心总结
这篇论文研究的重点不是单纯提高模型推理能力，而是让推理适应持续变化的环境。
**研究问题：**
$$
\text{Reasoning Quality}\quad\text{vs.}\quad\text{Reaction Latency}
$$
**评测方法：**
$$
\text{Token Clock}\rightarrow\text{推理消耗环境时间}
$$
**解决方法：**
$$
\boxed{
\text{AgileThinker}
=\text{Reactive Thread}+\text{Planning Thread}
}
$$
最重要的三个洞察：
1. **推理时间影响决策质量**：环境持续变化时，过时的正确规划也可能失效。
2. **快速反应与长期规划互补**：通过并行线程和中间推理参考，同时兼顾及时行动与长期决策。
3. **计算预算需要合理划分**：反应预算应接近自然推理需求，而不是简单地分配更多 Token。
**核心贡献：将推理耗时纳入实时 Agent 评测，并提出通过异步规划与及时反应协同决策的 AgileThinker 架构。**
