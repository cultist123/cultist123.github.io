# Thinkless：学习何时思考与 DeGRPO

论文：https://arxiv.org/abs/2505.13379
##### 1. 研究问题：Overthinking 与混合推理
Reasoning LLM 通常通过生成较长的 Chain-of-Thought（CoT）提升推理能力，但简单问题也可能产生大量不必要的推理 Token，造成 **Overthinking（过度思考）**。
现有推理效率优化包括：
- **Latent Reasoning**：在隐藏状态空间中执行推理，减少显式推理 Token。
- **Self-Consistency Optimization**：采样多条推理路径，通过答案一致性提高可靠性，并尝试减少不必要的采样。
- **Hybrid Reasoning（混合推理）**：根据任务难度选择短回答或长链推理。
Anthropic 的 Claude 3.7 Sonnet 将标准回答与 Extended Thinking 统一在同一个模型中，但主要由外部控制是否开启扩展思考。
**Thinkless 的核心问题：能否通过 RL，让模型自己决定什么时候应该深入思考？**
##### 2. Thinkless：自动选择推理模式
Thinkless 使用两个控制 Token：
- `<think>`：长链推理模式（Long Reasoning）。
- `<short>`：短推理模式（Short Reasoning）。
模型根据输入 $x$ 自动选择控制 Token，再生成回答。
###### 2.1 模式选择的概率表示
$$
\boxed{
\pi_\theta(c,a\mid x)
=\pi_\theta(c\mid x)\pi_\theta(a\mid x,c)
}
\tag{2}
$$
- $x$：输入问题。
- $c\in\{\texttt{<think>},\texttt{<short>}\}$：模式控制 Token。
- $a$：后续生成的回答序列。
- $\pi_\theta(c\mid x)$：选择推理模式的概率。
- $\pi_\theta(a\mid x,c)$：在该模式下生成回答的概率。
这是条件概率的链式法则，表示两个连续决策：
1. 选择推理模式。
2. 在选定模式下生成回答。
完整输出表示为：
$$
a_i=(a_{i,0},a_{i,1},\ldots,a_{i,T_i})
$$
其中 $a_{i,0}=c$ 是控制 Token，其余 $T_i$ 个 Token 是响应内容。
##### 3. 第一阶段：Distillation Warm-up
模型需要先具备生成长、短两种回答的能力，才能进一步学习自主选择。
###### 3.1 构造配对蒸馏数据
对于同一个问题 $x_i$，分别使用长推理模型和短回答模型生成结果：
$$
a_i^{\mathrm{think}}=\pi_{\mathrm{long}}(x_i)
$$
$$
a_i^{\mathrm{short}}=\pi_{\mathrm{short}}(x_i)
$$
构造蒸馏数据：
$$
\boxed{
\mathcal D_{\mathrm{distill}}
=
\left\{
(x_i,\texttt{<think>}a_i^{\mathrm{think}},
\texttt{<short>}a_i^{\mathrm{short}})
\right\}_{i=1}^{N}
}
\tag{1}
$$
每个问题对应两种风格的回答，通过 SFT 训练统一模型。
**蒸馏阶段的目标：让模型学会在给定控制 Token 时，生成对应风格的回答。**
注意，蒸馏并没有教会模型自主选择最佳模式，只是提供两种模式的基础能力。
##### 4. 第二阶段：RL 学习模式选择
###### 4.1 Reward Design
Thinkless 希望模型在保证答案正确的同时，减少不必要的长推理。

| 推理模式 | 回答结果 | Reward |
|---|---|---|
| `<think>` | 正确 | $1-\gamma$ |
| `<think>` | 错误 | $-1$ |
| `<short>` | 正确 | $1$ |
| `<short>` | 错误 | $-1$ |

其中 $\gamma$ 表示正确长推理的奖励折扣。
**关键设计：同样回答正确时，短回答的奖励高于长推理。**
这鼓励模型在能够正确回答时优先使用 `<short>`，但困难问题仍可以通过 `<think>` 争取更高的正确率。
###### 4.2 普通 GRPO 的训练目标
对于同一个问题，从旧策略采样 $G$ 条回答。
普通 GRPO 的 Token-Level 目标：
$$
\mathcal J_{\mathrm{GRPO}}(\theta)
=\mathbb E\left[
\frac1G\sum_{i=1}^{G}
\left(
\frac1{T_i+1}\sum_{t=0}^{T_i}\mathcal L_{i,t}(\theta)
-\beta D_{\mathrm{KL}}(\pi_\theta\|\pi_{\mathrm{ref}})
\right)
\right]
$$
其中单个 Token 的策略优化项为：
$$
\mathcal L_{i,t}(\theta)=
\min\left(
\rho_{i,t}\hat A_{i,t},
\operatorname{clip}(\rho_{i,t},1-\epsilon,1+\epsilon)\hat A_{i,t}
\right)
$$
$$
\rho_{i,t}
=
\frac{
\pi_\theta(a_{i,t}\mid x,a_{i,<t})
}{
\pi_{\theta_{\mathrm{old}}}(a_{i,t}\mid x,a_{i,<t})
}
$$
- $\rho_{i,t}$：新旧策略生成当前 Token 的概率比。
- $\hat A_{i,t}$：当前 Token 的优势。
- $\epsilon$：PPO 风格的裁剪范围。
- $\beta D_{\mathrm{KL}}$：限制策略偏离参考模型。
**问题：普通 GRPO 将控制 Token 和大量响应 Token 一起进行长度归一化。**
##### 5. DeGRPO：解耦模式选择与回答优化
###### 5.1 普通 GRPO 的两种不平衡
将原始目标拆开：
$$
\frac1{T_i+1}\sum_{t=0}^{T_i}\mathcal L_{i,t}
=
\underbrace{\frac1{T_i+1}\mathcal L_{i,0}}_{\text{Control Token}}
+
\underbrace{\frac1{T_i+1}\sum_{t=1}^{T_i}\mathcal L_{i,t}}_{\text{Response Tokens}}
\tag{3}
$$
**问题一：模式—准确率不平衡**
每条回答只有一个控制 Token，却存在大量响应 Token。
控制 Token 的贡献被 $1/(T_i+1)$ 缩小，模式选择可能得不到充分优化。
**问题二：长思考—短回答不平衡**
因为：
$$
T_i^{\mathrm{think}}\gg T_i^{\mathrm{short}}
$$
例如长推理有 1000 个 Token，短回答有 10 个：
$$
\texttt{<think>}:\frac1{1001}
$$
$$
\texttt{<short>}:\frac1{11}
$$
长推理控制 Token 的梯度贡献受到更强的长度归一化削弱，可能导致模式选择学习不稳定甚至 Mode Collapse。
**Mode Collapse（模式坍塌）**：模型逐渐只使用一种模式，不能再根据问题难度灵活切换。
<img src="/images/obsidian/6c55820318a8.png" alt="Thinkless_图3_模式坍塌与U形曲线.png" width="680" />
Figure 3：普通 GRPO 与 DeGRPO 的训练对比。(a) 普通 GRPO：约 120 步内 Think 样本数从约 480 降到接近 0，发生模式坍塌；(b) DeGRPO 的 U 形曲线：Think 样本先升后降、Short 样本先降后升，中间为两种模式的准确率，右为全部采样都正确的样本数；(c) 坍塌后的策略在四个数据集上 100% 选 `<short>`，AIME 2024 的 P@1 只有 8.7%；(d) DeGRPO 学到的策略按难度分配模式（即图 1 右侧的结果）。
注意 (b) 中段 Think 准确率下降并不是推理能力退化：难题逐渐被分给 `<think>`，长推理模式的平均难度变高，所以它的平均准确率变低。
###### 5.2 DeGRPO 的解决方法
DeGRPO（Decoupled GRPO）将控制 Token 与响应 Token 分别加权：
$$
\boxed{
\mathcal J_{\mathrm{DeGRPO}}(\theta)
=
\mathbb E\left[
\frac1G\sum_{i=1}^{G}
\left(
\alpha\mathcal L_{i,0}(\theta)
+
\frac1{T_i}\sum_{t=1}^{T_i}\mathcal L_{i,t}(\theta)
-
\beta D_{\mathrm{KL}}(\pi_\theta\|\pi_{\mathrm{ref}})
\right)
\right]
}
$$
两部分分别对应：
- $\alpha\mathcal L_{i,0}$：Mode Selection，优化推理模式选择。
- $\frac1{T_i}\sum_{t=1}^{T_i}\mathcal L_{i,t}$：Accuracy Improvement，优化回答正确率。
核心改动：
$$
\boxed{
\frac{\mathcal L_{i,0}}{T_i+1}
\quad\longrightarrow\quad
\alpha\mathcal L_{i,0}
}
$$
控制 Token 的权重不再随着响应长度增加而减小。
论文实验使用：
$$
\alpha=0.001
$$
**DeGRPO 并非单纯增大控制 Token 的权重，而是使其权重独立于响应长度，分别平衡模式选择与回答优化。**
<img src="/images/obsidian/bc90aac2686f.png" alt="Thinkless_图2_训练流程.png" width="680" />
Figure 2：Thinkless Training Pipeline。左：用 Reasoning LLM 与 Non-Reasoning LLM 蒸馏 Warm-up，使模型在第 0 个 Token 上学到 $p(c\mid x)$；中：采样 `<think>`/`<short>` 开头的回答；右：按对错与模式给奖励（$1-\gamma$、$-1$、$1$、$-1$），DeGRPO 分别以 $\alpha\mathcal L_{i,0}$ 更新控制 Token、以长度归一化项更新响应 Token。
##### 6. 模式选择的实验表现
<img src="/images/obsidian/98a70ec34f35.png" alt="Thinkless_图1_模式选择与使用比例.png" width="680" />
Figure 1：左为 Thinkless 自动决定 `<think>`/`<short>`，DeGRPO 拆成 Mode Selection 与 Accuracy Improvement 两个目标；右为四个数据集上两种模式的使用比例与各自 P@1。

| 数据集 | Think 使用比例 | Short 使用比例 |
|---|---:|---:|
| AIME 2024 | 100% | 0% |
| Math-500 | 51.6% | 48.4% |
| Minerva Algebra | 25.9% | 74.1% |
| GSM8K | 13.3% | 86.7% |

- **AIME 2024**：模型全部选择长推理。
- **Math-500**：长短模式使用接近均衡。
- **GSM8K**：大部分问题采用短回答。
P@1（Pass@1）表示单次生成答案的正确率。
需要注意：不同模式处理的问题难度可能不同，因此不能直接根据各模式的 P@1 判断哪一种模式本身更准确。
**实验说明：模型能够根据任务特点调整推理模式，而不是对所有问题统一采用长链推理。**
##### 7. 核心总结
Thinkless 将推理效率优化从“压缩推理过程”转向“学习什么时候需要推理”。
技术流程：
$$
\boxed{
\text{Paired Distillation}
\rightarrow
\text{Long/Short Capability}
\rightarrow
\text{DeGRPO}
\rightarrow
\text{Adaptive Mode Selection}
}
$$
核心贡献：
1. **Hybrid Reasoning**：一个统一模型支持 `<think>` 和 `<short>` 两种模式。
2. **Reward Design**：通过正确率与长推理奖励折扣，鼓励不必要时使用短回答。
3. **DeGRPO**：将控制 Token 与响应 Token 的优化解耦，缓解模式坍塌和长短回答长度不平衡。
**核心洞察：推理计算不应该统一分配给所有问题。模型可以通过强化学习，学习何时值得深入思考，并在保证任务表现的同时降低推理成本。**
