# ReTool：学习策略性工具调用

##### 1. 研究问题
ReTool 研究如何通过强化学习，让 LLM 学会策略性使用外部工具。传统 Text-Based RL 主要训练 LLM 通过文字推理解决问题。ReTool 在 Rollout 中加入真实 Python 执行，使模型能够结合文字推理、代码计算和工具反馈完成任务。
**核心区别**：不是完全用代码替代文字推理，而是通过 RL 学习什么时候自己推理，什么时候调用 Python，以及如何处理工具反馈。

##### 2. 基础概念
**Reasoning 与 Inference**
- **Reasoning（逻辑推理）**：根据已知信息进行分析、计算和推导，得到结论。
- **Inference（模型推断）**：运行训练完成的模型，通过前向传播生成输出 Token。Reasoning 可以发生在 Inference 过程中，但两者不等价。
**Structured Problem Solving**：结构化问题求解是将复杂问题拆解为有明确逻辑关系的步骤，逐步得到答案。例如数学题可以经过公式推导、数值计算、结果验证三个阶段。
**Text-Only Reasoning**：纯文本推理指模型主要通过自身生成的文本和数学表达式解决问题，不调用外部计算工具。
**Metacognitive Control**：元认知控制是对自身推理过程进行判断和管理。在 ReTool 中表现为：判断是否需要调用 Python；决定哪些步骤自己推理；根据代码执行结果调整后续步骤；判断何时停止并输出答案。

##### 3. Tool Use 的相关概念
**Strategic Tool Use**：策略性工具使用指模型能够规划工具的调用时机、调用方式、调用次数及反馈处理。例如：文字分析 → 判断需要计算 → 调用 Python → 检查结果 → 继续推理 → 最终答案。
**Adaptive Tool Selection**：自适应工具选择指根据当前任务和已有反馈动态决定下一步是否使用工具。ReTool 主要提供 Python 解释器，因此重点是选择“继续文字推理”还是“调用 Python”，而不是在大量不同工具之间选择。
**Heuristic Strategy**：启发式策略是人工预先制定的经验规则，例如“遇到复杂计算就调用 Python”“工具报错后最多重试三次”。这种规则通常不需要学习，但不保证最优。ReTool 则通过 RL 从最终任务奖励中学习工具使用策略，而不是完全依赖固定规则。

##### 4. Prompt、SFT 与 RL
**Prompt**：Prompt 告诉 LLM 可以使用什么工具，以及应该如何调用。例如规定 Python 代码必须写在 `<code>` 标签中，工具结果使用 `<interpreter>` 标签，最终答案使用 `<answer>` 标签。Prompt 本身不更新模型参数。
**Supervised Fine-Tuning（SFT）**：SFT 使用示范训练模型，更新 LLM 权重。例如训练样本包含：问题 → 文字推理 → Python 代码 → 执行结果 → 最终答案。模型通过模仿示范，学习工具调用格式和常见行为。**局限**：模型容易受到示范数据分布的影响。
**模仿专门整理的数据分布**：数据分布是训练数据中不同问题、动作和工具使用方式的统计规律。如果示范中大部分数学题都会调用 Python，模型可能学到过度调用工具的倾向。SFT 能够泛化，但主要优化的是模仿示范，而不是直接优化最终任务成功率。
**Tool-Integrated RL**：工具集成强化学习允许 LLM 在训练期间真正调用工具，并根据最终答案的奖励更新策略参数。**SFT 学习示范行为，RL 优化任务表现。**

##### 5. 工具集成学习与集成学习
- **Tool-Integrated Learning**：将外部工具调用及反馈融入训练过程。
- **Ensemble Learning（集成学习）**：组合多个模型的预测，例如 Bagging、Boosting、Random Forest。两者不是同一概念。

##### 6. 冷启动数据与数据构造
<img src="/images/obsidian/46b6c2a30456.png" alt="ReTool_图8_数据整理模板.png" width="560" />
> Data Curation Prompt：将已有纯文本数学推理转换成包含 Python 代码、真实解释器输出和最终答案的训练示范。
**Cold-Start Data**：冷启动数据是 RL 开始前，用于让模型掌握初始能力的训练示范。ReTool 先利用这些数据进行 SFT，再进入 RL 阶段。
**Synthetic Data**：合成数据可以由程序或其他模型自动生成，不要求人类逐条标注。例如可以：
1. 准备数学问题和已有推理。
2. 将适合计算的部分转换成 Python。
3. 实际执行代码。
4. 检查执行结果与答案。
5. 保留合格示范。
合成数据可以提供有效训练信号，但需要控制正确性、多样性和数据质量。
**Code-Augmented Reasoning**：代码增强推理指在文本推理过程中加入可执行代码，例如：文字分析 → Python 计算 → 读取输出 → 文字推导答案。它不是把全部推理转换成代码，而是让代码处理适合执行的步骤。
**Long Reasoning Trajectory**：长篇推理轨迹记录从输入问题到最终答案的完整过程，包括多轮文字分析、代码调用和反馈。轨迹不只是最终答案，而是整个交互过程。

##### 7. Code Interpreter 与 Sandbox
**Code Interpreter（CI）**：CI = Code Interpreter，代码解释器。它负责执行 LLM 生成的 Python 代码，并返回计算结果或错误信息。这里的 CI 不是 Continuous Integration。
**Sandbox（沙箱）**：沙箱是受到安全和资源限制的代码执行环境。它限制文件、网络、内存、运行时间等权限，但不代表只能使用固定函数。LLM 可以在允许范围内调用 Python 内置函数、使用可用的 Python 库、编写自定义函数。**LLM 决定写什么代码，Sandbox 只负责执行。**
**与固定工具 API 的区别**
- **Code Interpreter**：LLM 可以自由组合代码及函数，但受到运行环境约束。
- **固定 Tool API**：LLM 必须调用预先定义的工具及参数。

##### 8. Policy LLM 与 Agent Loop
Policy LLM 就是正在训练的 LLM，概念上对应 Actor。同一个 Policy LLM 负责：
1. 文字推理。
2. 生成 Python 代码。
3. 接收解释器反馈。
4. 继续推理或再次调用。
5. 输出最终答案。
不是一个 LLM 推理，另一个 Policy LLM 学习。简化执行逻辑：
```python
for step in range(max_steps):
    response = llm.generate(messages)
    if response.type == "tool_call":
        result = sandbox.execute(response.code)
        messages.append(result)
    elif response.type == "final":
        return response.answer
    else:
        messages.append(response.text)
```
这里是 Agent Loop 的逻辑示意，实际需要接入 LLM 和沙箱。**关键区别**：人工启发式由程序写死什么时候调用 Python；ReTool 由 Policy LLM 通过学习决定调用时机和代码内容。

##### 9. Rollout（轨迹采样）
<img src="/images/obsidian/01de4711eee1.png" alt="ReTool_图2_文本RL与ReTool_RL.png" width="680" />
> Text-Based RL vs ReTool RL：普通 RL 只生成文本；ReTool 在生成期间调用 Python 沙箱，将执行结果插入上下文，并继续生成。
Rollout 是使用当前策略实际执行一次任务，记录完整交互过程。
- 普通 Text-Based RL：Question → Text Reasoning → Answer → Reward。
- ReTool：Question → Text Reasoning → Code → Interpreter Feedback → Text Reasoning → Answer → Reward。
同一道题可能生成不同的 Rollout：直接推理并回答；调用一次 Python 后回答；代码报错、修复后再回答。Rollout 主要负责采样和收集训练轨迹；模型权重在后续训练更新阶段改变。

##### 10. PPO 与 ReTool 的区别
ReTool 主要改变的是 **PPO 的 Rollout 生成方式**，而不是 PPO 的核心优化公式。PPO 目标：
$$J_{\mathrm{PPO}}(\theta)=\mathbb E\left[\min\left(r_t(\theta)\hat A_t,\,\operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)\hat A_t\right)\right]$$
其中 $r_t(\theta)$ 是当前策略与旧策略生成动作的概率比，$\hat A_t$ 是 Advantage，$\epsilon$ 是 PPO 的裁剪参数。ReTool 让策略的条件上下文包含真实工具反馈。**训练时需要区分两类 Token**：
- LLM 生成的文字、代码、答案：属于 Policy 的输出，可以参与策略优化。
- Python 返回的执行结果：属于环境反馈，不应该作为 LLM 自己生成的动作来计算策略损失。

##### 11. Reward、Advantage、Actor-Critic
**Reward**：Reward 评价最终任务结果，例如答案正确得到正奖励，错误得到负奖励。它可以通过规则计算，不一定需要 Reward Model。
**Advantage**：Advantage 衡量当前动作或轨迹相对于基准表现的好坏，指导策略更新。
**Actor 与 Critic**
- **Actor**：Policy LLM，负责生成推理内容和工具调用。
- **Critic**：如果训练算法使用价值网络，则负责估计状态价值。
- **Reward**：外部提供的任务表现评价。
Policy LLM 在 Rollout 中生成最终答案后，由训练程序计算 Reward 和 Advantage，再通过 PPO 更新同一个 Policy LLM 的权重。

##### 12. verl 框架
verl 是用于大语言模型强化学习的开源训练框架，负责组织 Rollout、Reward 与 Advantage 计算、PPO / GRPO 等训练算法、模型参数更新与分布式训练。需要区分：
- **PPO**：强化学习优化算法。
- **vLLM**：高性能 LLM 推理引擎。
- **verl**：组织强化学习训练流程的框架。
- **Code Sandbox**：实际执行代码的工具环境。

##### 13. 两种 Prompt 的区别
<img src="/images/obsidian/506a0bcaecf6.png" alt="ReTool_图7_RL_Rollout模板.png" width="480" />
> RL Rollout Prompt Template：规定训练期间模型如何生成代码、接收反馈以及输出最终答案。Data Curation Prompt Template 见第 6 节图，用于构建冷启动数据，将已有文字推理转换成代码增强的示范轨迹。
- **Data Curation Prompt**：用于准备 SFT 训练数据。
- **RL Rollout Prompt**：用于 RL 阶段的实时生成与工具交互。
两者本身都只是 Prompt，不直接更新模型权重。

##### 14. 总结
**ReTool = 合成冷启动数据 + SFT + 工具集成 Rollout + PPO。** 核心机制：
1. 通过合成示范和 SFT，让 LLM 初步掌握 Python 工具使用。
2. RL 期间，同一个 Policy LLM 既可以文字推理，也可以生成代码。
3. Python 沙箱执行代码，将真实结果返回 LLM。
4. LLM 根据反馈继续推理，最终输出答案。
5. 训练程序根据答案计算 Reward、Advantage，并更新 Policy LLM 权重。
**主要区别不在 PPO 算法，而在训练时真正将工具交互接入 Rollout。**
一句话总结：ReTool 让 LLM 不再只能通过文字推理完成任务，而是通过强化学习获得文字推理与 Python 工具调用相结合的决策能力。
