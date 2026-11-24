# MeMento：偏好条件化的多模态记忆

#### 1. 研究背景与核心问题
传统具身智能（Embodied AI）主要关注物体识别、环境导航和任务执行，但个性化任务不仅要求机器人理解环境，还需要结合**用户偏好（User Preferences）** 与过去积累的**具身探索经验（Embodied Exploration Experience）** 进行决策。
例如，机器人需要在多个候选房屋中选择最适合用户的一套，不仅要知道每套房屋有什么，还要知道这些特征是否符合用户的习惯和要求。
**核心问题**：机器人探索多个环境后，会积累大量图片、地图、观察和动作记录。直接把全部历史输入 VLM 成本很高，而且容易混淆不同环境的信息。因此，需要把历史压缩成少量与用户偏好相关的记忆。
#### 2. 用户偏好与具身探索
用户偏好分为两种：
- **Explicit Preferences（显式偏好）**：用户明确提出的要求，例如需要 3 间卧室、厨房与客厅相邻。
- **Implicit Preferences（隐式偏好）**：根据用户习惯推断出的需求，例如喜欢做饭意味着可能更关注厨房空间。
**Embodied Exploration（具身探索）**：机器人通过移动、观察和交互收集环境信息，而不是只分析静态图片。
**Multimodal Memory（多模态记忆）**：保存探索过程中获得的图片、地图、观察文本和动作记录。
整个任务流程：**用户偏好 → 探索多个环境 → 积累多模态记忆 → 压缩相关信息 → VLM 决策 → 继续探索或提交结果**。
#### 3. MeMento 整体架构
<img src="/images/obsidian/3f4b16d68e7d.png" alt="Screenshot 2026-11-08 at 16.38.32.png" width="653" />
MeMento 主要由三个部分组成：
- **Multimodal Encoder**：将历史图片、地图、观察和动作编码成特征向量。
- **Preference-Conditioned Memory Compressor**：根据用户偏好，从历史中提取重要信息并压缩成 Memory Tokens。
- **Memory Prefix Injection**：通过 Adapter 将压缩记忆注入冻结 VLM，让模型利用历史信息进行推理和动作预测。
整体流程：**User Preferences + Exploration History → Memory Compressor → Global Memory Tokens → Adapter → Frozen VLM → Action**。
VLM 可以根据当前观察与长期记忆决定继续探索、切换环境、调用工具或提交最终选择。
#### 4. Memory Token 与 Perceiver
**Memory Token（记忆 Token）**：用一个高维向量表示从历史记录中压缩出的信息，不是普通的文字 Token，也不一定对应某一张图片或某一个步骤。
例如机器人探索产生 1000 个历史特征，但只保留 8 个 Memory Tokens，用它们概括重要信息。
**Perceiver 风格模块**：使用固定数量的可学习查询（Learned Queries），通过 Cross-Attention 从大量输入特征中提取信息。
**Learned Queries**：一组通过训练得到的查询向量，用于决定如何从历史特征中提取信息，不是搜索引擎中的查询。
Memory Token 数量由 Learned Queries 的数量控制，因此可以将长度不断增长的历史压缩成固定数量的环境级表示。

<img src="/images/obsidian/656e3a7bf03e.png" alt="Screenshot 2026-11-08 at 16.38.50.png" />
#### 5. 用户偏好与多模态步骤编码
首先将用户偏好编码成多个 Preference Tokens，再通过 Pooling（池化）聚合成单个偏好向量 $\bar{\mathbf z}_r$。这个向量表示用户的整体偏好，用于指导后续记忆选择。
每一步探索包含四类信息：
$$
x_t=\{\text{ego image},\text{map image},\text{observation},\text{action}\}
$$
使用多模态编码器转换成特征向量：
$$
\mathbf e_t=f_{\mathrm{enc}}(x_t)
$$
其中 ego image 是第一视角图片，map image 是地图视图，observation 是观察文本，action 是执行动作。
为了保存时间顺序和环境身份，加入时间与环境嵌入：
$$
\tilde{\mathbf e}_t=\mathbf e_t+\mathbf p_t^{\mathrm{time}}+\mathbf p_k^{\mathrm{env}}
$$
- $\mathbf e_t$：这一步观察到了什么、执行了什么。
- $\mathbf p_t^{\mathrm{time}}$：第几步探索，类似 Transformer 的位置编码。
- $\mathbf p_k^{\mathrm{env}}$：当前步骤属于哪个环境。
**作用**：让模型区分不同时间和不同房屋的探索记录，避免记忆混淆。
#### 6. Preference-Conditioned Memory Compression
##### 6.1 偏好引导的 Learned Queries
首先定义一组可学习查询 $\mathbf Q_0\in\mathbb R^{M\times d}$，其中 $M$ 为查询数量，$d$ 为特征维度。
将用户偏好注入查询：
$$
\mathbf Q_r=\mathbf Q_0+\phi(\bar{\mathbf z}_r)
$$
- $\mathbf Q_0$：通用 Learned Queries。
- $\bar{\mathbf z}_r$：用户偏好向量。
- $\phi$：投影网络，将偏好映射到查询维度。
- $\mathbf Q_r$：融合偏好后的 Queries。
**目的**：不同用户关注不同信息。例如喜欢做饭的用户，模型需要更多关注厨房相关证据。
##### 6.2 Cross-Attention 与 Self-Attention
**Self-Attention**：Q、K、V 都来自同一组输入，使不同 Token 之间交换信息。
$$
Q=XW_Q,\quad K=XW_K,\quad V=XW_V
$$
**Cross-Attention**：Q 来自一组输入，K、V 来自另一组输入。例如：
- **Q**：Preference-Conditioned Learned Queries。
- **K、V**：机器人过去的多模态步骤表示。
两者使用相同的注意力计算：
$$
\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$
**为什么使用 Cross-Attention？** 假设某套房子有 100 个历史步骤，Learned Queries 有 8 个，Cross-Attention 可以把 100 个步骤的信息聚合为 8 个向量。它不是选择其中 8 个步骤，而是对历史特征加权融合。
之后通过 Self-Attention 让这 8 个记忆向量相互交换信息，整合跨步骤关系。
##### 6.3 环境级与全局记忆
每个环境独立压缩：
$$
\mathbf H^{(k)}=\mathrm{SelfAttn}\left(\mathrm{CrossAttn}\left(\mathbf Q_r,\{\tilde{\mathbf e}_t:t\in\mathcal E_k\},\{\tilde{\mathbf e}_t:t\in\mathcal E_k\}\right)\right)
$$
- $\mathcal E_k$：第 $k$ 个环境的探索步骤集合。
- $\mathbf H^{(k)}$：第 $k$ 个环境压缩得到的 Memory Tokens。
**为什么独立压缩？** 防止不同房屋的证据混合，例如错误地把 House A 的厨房和 House B 的卧室当成同一套房子的特征。
最后将各环境的记忆拼接：
$$
\mathbf H_{\mathrm{global}}=\mathrm{Concat}(\mathbf H^{(1)},\ldots,\mathbf H^{(K)})
$$
注意：这里是拼接，不是把所有房屋进一步平均成一个向量。每套环境保留自己的压缩表示。
#### 7. 压缩记忆注入：Adapter 与 Soft Prompt
##### 7.1 Adapter（适配器）
**Adapter** 是一个小型可训练网络，用于将 Memory Compressor 的输出映射到 VLM 能接受的嵌入空间。
$$
\tilde{\mathbf M}=\psi(\mathbf H_{\mathrm{global}})
$$
- $\psi$：可训练的投影适配器。
- $\mathbf H_{\mathrm{global}}$：全局记忆。
- $\tilde{\mathbf M}$：适配后的记忆向量。
例如 Compressor 输出 512 维，VLM 输入需要 4096 维，Adapter 可以负责维度映射，并学习让记忆表示与 VLM 兼容。最简单的 Adapter 可以是线性层 $y=Wx+b$。
##### 7.2 Prefix Injection（前缀注入）
将 Memory Tokens 放在当前输入之前：
$$
[\tilde{\mathbf M};\mathbf X_{\mathrm{current}}]
$$
其中分号表示沿 Token 序列维度拼接，而不是向量相加。
输入结构：`[Memory Token 1, Memory Token 2, ...] + [当前图片、地图、任务指令]`
**Soft Prompt（软提示）**：普通 Prompt 是自然语言，而 Soft Prompt 是直接输入模型嵌入空间的连续向量。这里 Memory Tokens 就充当 Soft Prompt。
**Frozen VLM**：VLM 骨干参数不更新，主要训练 Compressor 和 Adapter，让已有 VLM 能利用长期记忆。
#### 8. 两阶段训练
##### 8.1 Stage 1：偏好引导的压缩训练
**目标**：让 Memory Compressor 学会识别哪些历史步骤与用户偏好相关，并在压缩时重点保留这些信息。
首先为每个探索步骤标注四种相关性标签：
- **Positive**：支持用户偏好的证据，例如发现符合要求的厨房。
- **Negative**：不满足偏好的证据，例如确认卧室数量不足。
- **Unknown**：当前信息不足，无法确定。
- **Irrelevant**：与偏好无关的信息。
注意：Negative 同样重要，因为不满足要求的证据也影响最终决策。
**（1）相关性分类损失**
给定偏好向量和步骤表示，训练分类器预测相关性：
$$
s_t=g(\bar{\mathbf z}_r,\tilde{\mathbf e}_t)
$$
$$
\mathcal L_{\mathrm{rel}}=\mathrm{CE}(s_t,y_t)
$$
其中 CE 为交叉熵损失，用来衡量预测标签与真实标签的差异。
**（2）Attention 对齐损失**
仅识别重要步骤还不够，还要让 Cross-Attention 真正关注这些步骤：
$$
\mathcal L_{\mathrm{attn}}=-\sum_t\tilde y_t\log(\alpha_t+\epsilon)
$$
- $\alpha_t$：Cross-Attention 实际分配给步骤 $t$ 的注意力，跨 Attention Heads 和 Learned Queries 取平均。
- $\tilde y_t$：根据相关性标签构造的目标注意力分布。
- $\epsilon$：避免 $\log(0)$。
例如用户关心卧室，模型应该对发现卧室的步骤分配较高 Attention，对无关装饰分配较低 Attention。
**（3）Stage 1 总损失**
$$
\mathcal L_{\mathrm{stage1}}=\mathcal L_{\mathrm{rel}}+\lambda\mathcal L_{\mathrm{attn}}
$$
$\lambda$ 控制两种损失的相对权重。
**核心区别**：$\mathcal L_{\mathrm{rel}}$ 教模型判断什么重要，$\mathcal L_{\mathrm{attn}}$ 教压缩器真正关注重要信息。
##### 8.2 Stage 2：记忆与 VLM 的对齐训练
**目标**：让压缩后的 Memory Tokens 能够被冻结的 VLM 正确理解。
使用关于历史环境的问答数据训练，例如：
- 问题：House A 的厨房有没有冰箱？
- 答案：Yes / No / Unknown。
流程：**Memory Compressor → Adapter → Frozen VLM → 预测答案 → Loss**。
VLM 输入只有记忆前缀和问题提示，不需要重新输入全部原始历史。
**训练损失**
$$
\mathcal L_{\mathrm{stage2}}=-\sum_{i\in\mathcal T_{\mathrm{ans}}}\log p_\theta(a_i\mid a_{<i},\tilde{\mathbf M},q)
$$
- $\tilde{\mathbf M}$：适配后的记忆。
- $q$：问题。
- $a_i$：目标答案的第 $i$ 个 Token。
- $a_{<i}$：前面已经给定的答案 Token。
- $\mathcal T_{\mathrm{ans}}$：答案 Token 的位置集合。
**Loss Masking**：只计算答案 Token 的 Loss，不计算问题 Prompt 和 Memory Prefix 的 Loss，因为目标是训练模型利用记忆回答问题，而不是预测输入内容。
**为什么 VLM 冻结仍然可以反向传播？** 冻结只表示 VLM 参数不更新，梯度依然可以通过 VLM 的计算图传回 Adapter 和 Compressor，使它们学会生成 VLM 能理解的记忆表示。
#### 9. 两阶段训练的核心区别
- **Stage 1：学会提取什么信息。** 通过相关性分类和 Attention 对齐，让压缩器识别并保留与用户偏好有关的历史证据。
- **Stage 2：学会如何表示这些信息。** 通过问答损失训练 Compressor 和 Adapter，让压缩记忆能被冻结的 VLM 正确使用。
**Stage 1 解决记忆选择问题，Stage 2 解决记忆表示与 VLM 对齐问题。**
#### 10. 总结
**MeMento 的核心思想**：不让 VLM 反复读取完整的多模态探索历史，而是用 Preference-Conditioned Learned Queries 从各环境的探索记录中提取与用户偏好相关的证据，压缩成 Memory Tokens，再通过 Adapter 作为 Soft Prompt 注入冻结 VLM。
关键技术包括：
- **Preference Conditioning**：根据用户偏好决定需要关注的记忆。
- **Cross-Attention + Self-Attention**：从历史中提取并融合信息。
- **Environment-Level Compression**：独立压缩不同环境，避免证据混淆。
- **Adapter + Prefix Injection**：将压缩记忆输入冻结 VLM。
- **Two-Stage Training**：先训练记忆选择能力，再训练记忆与 VLM 的对齐能力。
**一句话：MeMento 让具身智能体把长期探索经历压缩成与用户偏好相关的记忆，并在不微调 VLM 骨干的情况下，利用这些记忆进行个性化决策。**

---
