# Diffusion Policy：用扩散模型生成动作

论文：https://arxiv.org/abs/2303.04137
##### 1. 研究背景与核心问题
**Diffusion Policy（扩散策略）** 是一种基于扩散模型的机器人模仿学习方法，主要应用于 Low-Level Policy（底层动作策略），根据视觉观察与机器人状态生成连续的动作序列。
传统 Behavior Cloning（BC）使用神经网络直接预测专家动作，但机器人操作存在多个合理动作模式，单一回归模型容易将不同动作平均，产生不合理动作。
例如抓杯子时，从左侧和右侧抓取都合理，直接平均可能得到一个不合理的中间动作。
**核心问题**：如何学习复杂的多模态动作分布，同时实现连续、稳定的机器人动作控制？
Diffusion Policy 将动作预测转化为条件扩散生成问题，通过迭代去噪生成动作序列，并结合滚动时域控制实现闭环执行。
##### 2. Diffusion Policy 与 ACT 的关系
两者都属于机器人模仿学习中的动作策略，目标是从观察预测未来的动作序列。
- **ACT**：使用 Transformer + CVAE，直接预测 Action Chunk，并通过 Temporal Ensembling 融合重叠动作预测。
- **Diffusion Policy**：使用扩散模型，从随机动作噪声开始，经过多次去噪生成 Action Chunk，并通过 Receding Horizon Control 执行动作。
两者都工作在机器人底层策略层，不负责高层任务规划，也不是直接驱动电机的底层控制器。
**核心区别**：ACT 主要通过一次网络前向传播生成动作块，Diffusion Policy 通过迭代去噪生成动作块。
##### 3. 为什么 Diffusion Policy 属于模仿学习？
**Imitation Learning（模仿学习）** 是训练范式，**Diffusion Model（扩散模型）** 是用于表示和生成动作的方法。
训练过程：
1. 人类示范机器人操作，记录 RGB 图像、机器人状态和专家动作。
2. 对专家动作序列添加随机高斯噪声。
3. 训练神经网络根据观察和噪声等级预测添加的噪声。
4. 推理时从随机噪声开始，逐渐生成符合专家示范分布的动作。
模型学习的是专家动作分布，不需要通过环境 Reward 进行训练，因此属于模仿学习。
##### 4. 显式策略、隐式策略与扩散策略
<img src="/images/obsidian/1612f704846a.png" alt="DP_论文图1_三种策略表示.png" width="720" />
*论文图 1（Policy Representations）：(a) 显式策略直接输出动作或动作分布；(b) 隐式策略通过能量函数寻找低能量动作；(c) 扩散策略通过学习梯度场，从噪声中迭代生成动作。*
###### 4.1 Explicit Policy（显式策略）
显式策略直接根据观察输出动作或动作分布参数：
$$
\hat a=F_\theta(o)
$$
常见输出表示（对应图 (a) 右侧虚线框）：
- **Scalar Regression**：直接预测连续动作数值。
- **Mixture of Gaussians（高斯混合）**：预测多个高斯分布的混合，表示不同动作模式。
- **Categorical**：将动作离散化后预测类别概率。
简单回归通常计算 MSE 或 L1 Loss，面对多种合理动作时可能预测出动作平均值。
###### 4.2 Implicit Policy（隐式策略）
隐式策略不直接输出动作，而是学习能量函数：
$$
E_\theta(o,a)
$$
根据观察 $o$ 和候选动作 $a$，计算动作对应的能量。通常认为低能量动作更符合专家数据。
通过优化寻找动作：
$$
a^*=\arg\min_a E_\theta(o,a)
$$
**缺点**：高维连续动作空间中，直接优化能量函数寻找合理动作可能比较耗时。
###### 4.3 Diffusion Policy（扩散策略）
Diffusion Policy 利用噪声预测网络学习动作分布的得分信息：
$$
\nabla_a\log p(a\mid o)
$$
它不需要直接枚举所有候选动作，也不需要显式计算每个动作的概率密度，而是通过多次去噪从随机动作生成合理动作。
**核心区别**：
- 显式策略：直接预测动作。
- 隐式策略：通过优化能量函数选择动作。
- 扩散策略：学习去噪方向，通过迭代采样生成动作。
##### 5. 多模态动作分布（Multimodal Action Distribution）
**Mode（模态）**：概率分布中的一个局部峰值区域，即数据较集中的地方。
**Multimodal Distribution（多模态分布）**：同一个条件下存在多个高概率区域，对应多种合理的动作方式。
例如机器人抓杯子：
- Mode A：从左侧抓取。
- Mode B：从右侧抓取。
- 中间区域：可能并不是合理动作。
普通 MSE 回归模型可能把两个动作平均，而扩散模型可以表示多个高概率区域，并从中生成一种合理的动作。
<img src="/images/obsidian/c7e4f5671bc8.png" alt="DP_论文图3_多模态行为.png" width="640" />
*论文图 3：Push-T 任务中的多模态行为，T 块可以从左侧或右侧绕过去推。Diffusion Policy 每次 rollout 只选一边并坚持到底；LSTM-GMM、IBC 偏向一侧，BET 在两种模式间来回跳，轨迹抖动。*
注意：这里的多模态是指概率分布存在多个峰值，不是指图像、语言等多种数据模态。
##### 6. 概率密度、能量函数与梯度场
###### 6.1 Probability Density（概率密度）
机器人动作通常是连续向量：
$$
a=[x,y,z,\theta,\text{gripper}]
$$
每个维度可以取连续数值，因此无法像三个离散动作那样枚举所有可能结果。
**概率密度 $p(a\mid o)$** 描述在观察 $o$ 下，专家动作集中在哪些区域。
例如人类示范大多选择向左移动 10mm，则 10mm 附近的概率密度较高，远离该位置的概率密度较低。
概率密度不等于某个精确连续动作发生的概率，连续变量落入某个区间的概率需要对密度积分。
###### 6.2 Energy Function（能量函数）
能量和概率密度可以建立关系：
$$
p(a\mid o)=\frac{1}{Z(o)}\exp(-E(o,a))
$$
其中 $Z(o)$ 是归一化常数。
- **低能量**：对应较高概率密度，通常是合理动作区域。
- **高能量**：对应较低概率密度，通常偏离专家示范。
可以把能量函数想象为地形：合理动作位于山谷，不合理动作位于较高区域。
<img src="/images/obsidian/96fb3cc20e0e.png" alt="DP_论文图1b_隐式策略能量图.png" width="460" />
*论文图 1(b)：颜色越浅能量越低。黑色曲线是二维示意中的低能量区域（专家动作所在处），不是机器人真实运动轨迹；横轴为观察 $o$，纵轴为动作 $a$。注意 $o\approx-0.5\sim0.5$ 时同一个 $o$ 对应上下两个 $a$，这就是多模态。*
###### 6.3 Score Gradient（得分梯度）
得分梯度定义为：
$$
s(a,o)=\nabla_a\log p(a\mid o)
$$
它不是给出动作概率密度的数值，而是告诉模型：**从当前动作出发，沿哪个方向调整，能够使动作进入概率密度更高的区域。**
由于：
$$
\log p(a\mid o)=-E(o,a)-\log Z(o)
$$
所以：
$$
\boxed{\nabla_a\log p(a\mid o)=-\nabla_aE(o,a)}
$$
**对 Energy 做梯度下降，与对 Log Probability 做梯度上升，在该关系下具有相同的方向。** 而且 $Z(o)$ 与 $a$ 无关，求梯度时直接消掉——这正是扩散策略绕开隐式策略中难以估计的归一化常数的关键。
<img src="/images/obsidian/2d53dfb2cdc4.png" alt="DP_论文图1c_扩散策略梯度场.png" width="480" />
*论文图 1(c)：蓝色箭头就是梯度场，每个箭头指向“离黑色曲线（高密度区域）更近”的方向；左侧框中 $\varepsilon_\theta(o,a)$ 被反复调用 $K$ 次，每次沿箭头更新一次 $a$。*
###### 6.4 数值例子：梯度如何调整动作
假设专家动作集中在 10mm 附近：
$$
p(a)\propto\exp\left(-\frac{(a-10)^2}{2}\right)
$$
其得分梯度：
$$
\nabla_a\log p(a)=-(a-10)
$$
当 $a=13$ 时：
$$
\nabla_a\log p(13)=-3
$$
负号表示应该减少当前动作数值。
使用简化的梯度上升：
$$
a_{\mathrm{new}}=a+\eta\nabla_a\log p(a)
$$
若 $\eta=0.5$，则更新过程为：
$$
13\rightarrow11.5\rightarrow10.75\rightarrow\cdots\rightarrow10
$$
**核心区别**：概率密度描述哪里存在合理动作，得分梯度描述应该朝哪个方向调整动作。
##### 7. 扩散模型如何学会去噪？
###### 7.1 训练阶段：人为加噪
给专家动作序列 $A^0$ 添加随机噪声，形成不同噪声等级的动作：
$$
A^k=\sqrt{\bar\alpha_k}A^0+\sqrt{1-\bar\alpha_k}\epsilon
$$
其中：
- $A^0$：原始专家动作序列。
- $A^k$：第 $k$ 个噪声等级下的动作。
- $\epsilon\sim\mathcal N(0,I)$：人为添加的高斯噪声。
- $\bar\alpha_k$：控制原始动作与噪声的比例。
由于噪声是人为添加的，所以训练时知道真实噪声 $\epsilon$。
网络接收观察、带噪动作和噪声等级：
$$
\epsilon_\theta(O,A^k,k)
$$
通过噪声预测损失训练：
$$
\mathcal L=\mathbb E\left[\|\epsilon-\epsilon_\theta(O,A^k,k)\|^2\right]
$$
**训练目标**：让网络学会在不同噪声等级和环境观察条件下，判断动作中包含哪些噪声。
###### 7.2 推理阶段：从噪声生成动作
实际运行时不存在需要还原的真实动作，模型从随机高斯噪声开始：
$$
A^K\sim\mathcal N(0,I)
$$
然后反复调用同一个去噪网络：
$$
A^K\rightarrow A^{K-1}\rightarrow\cdots\rightarrow A^1\rightarrow A^0
$$
- 高噪声阶段：形成大致合理的动作结构。
- 中间阶段：调整动作序列。
- 低噪声阶段：进一步修正细节。
**关键点**：模型并不是恢复某条已经存在的真实动作，而是从学到的专家动作分布中生成新的动作样本。
> [!example] 对照图
> Figure 2 左下角三张图 $A_t^K\rightarrow A_t^3\rightarrow A_t^0$ 就是这个过程：一开始彩色点（未来动作）散满画面，逐步收拢成一条推 T 块的平滑轨迹。见第 11 节的 Figure 2(a)。
##### 8. 扩散与普通梯度下降的区别
普通梯度下降使用固定能量函数：
$$
a_{n+1}=a_n-\eta\nabla_aE(a_n)
$$
每一步都沿同一个能量函数的下降方向优化。
Diffusion Policy 则学习不同噪声等级下的得分场：
$$
s_\theta(A^k,k,O)\approx\nabla_{A^k}\log p_k(A^k\mid O)
$$
其中 $p_k$ 是第 $k$ 个噪声等级下的动作分布。
**为什么不同？**
- 普通梯度下降：针对固定目标函数寻找低能量点。
- Diffusion Policy：从高度加噪的分布出发，逐步转换到专家动作分布。
- 不同 $k$ 对应不同噪声等级和不同的得分场，因此去噪方向会随阶段变化。
扩散去噪不是简单地对一个固定能量函数不断做梯度下降，而是使用噪声调度、去噪网络及可能的随机项完成采样。
##### 9. Langevin Dynamics（朗之万动力学）
**朗之万动力学**是一种结合梯度和随机噪声的采样方法，可用于从概率分布中采样，而不只是寻找一个最优点。
其典型离散形式：
$$
a_{n+1}=a_n-\eta\nabla_aE(a_n)+\sqrt{2\eta T}\epsilon_n
$$
其中：
- $-\eta\nabla_aE(a_n)$：沿能量下降方向更新。
- $\epsilon_n\sim\mathcal N(0,I)$：随机噪声。
- $T$：控制噪声强度。
- $\eta$：更新步长。
与普通梯度下降相比，朗之万动力学增加随机扰动，使采样过程能够探索不同的低能量区域。
**核心区别**：梯度下降主要寻找低能量解，朗之万动力学可以在一定条件下从目标分布中采样。
Diffusion Policy 的反向扩散过程与得分驱动的随机采样密切相关，但具体更新形式不完全等同于上述简单公式。
##### 10. Diffusion Policy 的整体架构
<img src="/images/obsidian/b341a27be1df.png" alt="DP_论文图2_整体架构.png" width="760" />
*论文图 2（Diffusion Policy Overview）：(a) 输入观察序列和输出动作序列；(b) CNN + FiLM 去噪网络；(c) Transformer + Cross-Attention 去噪网络。*
整体流程：
**Observation → Noisy Action Sequence → Denoising Network × K → Predicted Action Sequence → Robot Execution**
模型并不是对 RGB 图像去噪，而是根据图像和机器人状态，对随机动作序列进行去噪。
##### 11. Figure 2(a)：Observation 与 Action Horizon
<img src="/images/obsidian/14a51e3fe158.png" alt="DP_论文图2a_通用形式.png" width="640" />
*论文图 2(a)（General Formulation）：上方是最近几步的观察，中间是扩散策略 $\varepsilon_\theta(O,A,k)$，下方是预测的动作序列；机器人执行部分动作后，在新时刻 $t+4$ 重新观察并预测。*
###### 11.1 输入 Observation
$$
O_t=[o_{t-T_o+1},\ldots,o_t]
$$
- $T_o$：Observation Horizon，即输入多少步历史观察。
- $o_t$：某个时间步的视觉图像和机器人状态。
例如图中使用 $o_{t-2},o_{t-1},o_t$ 三步观察。
###### 11.2 输出 Action Sequence
$$
A_t=[a_t,a_{t+1},\ldots,a_{t+T_p-1}]
$$
- $T_p$：Prediction Horizon，一次预测未来多少步动作。
- $T_a$：Action Horizon，实际连续执行多少步动作。
通常满足：
$$
T_a\leq T_p
$$
###### 11.3 Receding Horizon Control（滚动时域控制）
例如一次预测未来 8 步，但只执行前 4 步：
1. 在 $t$ 时刻，根据最近观察生成 $A_t$。
2. 执行 $a_t,a_{t+1},a_{t+2},a_{t+3}$（图中深蓝色的四格）。
3. 到 $t+4$ 时，重新获取观察 $O_{t+4}$。
4. 生成新动作序列 $A_{t+4}$。
**为什么只执行部分动作？** 环境会发生变化，预测越远可能越不准确。只执行前面一段再重新规划，能够结合新的视觉反馈修正动作。
##### 12. Figure 2(b)：CNN-based Diffusion Policy
<img src="/images/obsidian/d480e49bde00.png" alt="DP_论文图2b_CNN_FiLM.png" width="340" />
*论文图 2(b)：带噪动作序列 $A_t$ 进入 Conv1D 网络；Observation 经过 Linear 层生成调节参数 $a,b$，通过 FiLM 影响动作特征。*
CNN-based Diffusion Policy 使用 **1D CNN + FiLM Conditioning** 实现动作序列去噪。
- **Action Embedding**：将带噪动作序列转换成特征。
- **Conv1D**：沿动作时间维度提取序列特征。
- **Observation Embedding**：将图像和机器人状态编码成条件特征。
- **FiLM（Feature-wise Linear Modulation）**：使用观察条件调节 CNN 中间层。
FiLM 的计算：
$$
y=a\odot x+b
$$
- $x$：CNN 当前的动作特征。
- $a,b$：由观察条件生成的缩放和偏移参数。
- $\odot$：逐元素乘法。
例如机器人看到杯子在左侧，Observation 会改变 $a,b$，从而影响去噪网络如何生成动作。
**核心作用**：CNN 负责建模动作序列，FiLM 负责将环境观察信息注入动作去噪过程。
##### 13. Figure 2(c)：Transformer-based Diffusion Policy
<img src="/images/obsidian/f550d909ece4.png" alt="DP_论文图2c_Transformer.png" width="340" />
*论文图 2(c)：带噪动作转换成 Action Embedding，观察转换成 Observation Embedding；Transformer 使用 Cross-Attention 结合环境信息，并通过 Causal Mask（中间的下三角蓝色格子）限制动作 Token 的注意力范围。*
核心组成：
- **Action Embedding**：将带噪动作转换为 Token。
- **Observation Embedding**：将图像和机器人状态转换为 Token。
- **Self-Attention**：建模动作序列内部的依赖关系。
- **Cross-Attention**：让动作 Token 关注 Observation 特征。
- **Causal Mask**：限制动作 Token 只能关注自身和前面的动作位置。
在 Cross-Attention 中：
- **Q**：Action Embedding。
- **K、V**：Observation Embedding。
Transformer 输出动作噪声预测，用于下一轮去噪。
**与 CNN 版本的区别**：CNN 使用 FiLM 注入 Observation，Transformer 使用 Cross-Attention 融合 Observation 与 Action。
##### 14. 噪声等级 k 与去噪次数 K
> [!tip] 看图位置
> 在上面 Figure 2(b)(c) 两张图里：左下/中间的**蓝色小方块 $k$** 是输入去噪网络的噪声等级标识，右边蓝色回环上的 **×K** 表示整个去噪过程重复 K 次（输出 $\nabla E(A_t)$ 后更新 $A_t$ 再送回底部）。
- **$A^k$**：当前噪声等级下的动作序列。
- **$O$**：当前观察条件。
- **$k$**：当前处于哪个噪声等级。
- **$K$**：去噪总步数。
例如：
$$
A^4\xrightarrow{k=4}A^3\xrightarrow{k=3}A^2\xrightarrow{k=2}A^1\xrightarrow{k=1}A^0
$$
**每次使用同一个去噪网络和参数，但输入的动作序列、噪声等级不同。**
网络需要知道 $k$，才能根据当前噪声强度预测适当的去噪方向。
##### 15. Diffusion Policy 的训练与执行
###### 15.1 训练
使用专家示范数据：
$$
\mathcal D=\{(O_t,A_t)\}
$$
训练流程：采样专家动作 → 添加不同等级的高斯噪声 → 输入 Observation、Noisy Actions 和 $k$ → 预测噪声 → 计算 Loss → 更新网络。
模型通过监督式去噪训练，间接学习专家的条件动作分布。
###### 15.2 推理
推理时：
1. 获取最近 $T_o$ 步观察。
2. 随机初始化长度为 $T_p$ 的动作序列。
3. 经过 $K$ 次去噪，得到 $A_t^0$。
4. 执行其中前 $T_a$ 步。
5. 获取新的观察，继续预测。
**执行特点**：每次生成一段连续动作，但只执行其中一部分，再利用新的视觉反馈重新规划。
##### 16. 与 ACT 的核心对比
- **相同点**：两者都利用专家示范进行模仿学习，均可根据 RGB 图像和机器人状态生成未来动作序列。
- **ACT**：使用 CVAE + Transformer 预测 Action Chunk，训练时学习潜在变量，部署时通常令 $z=0$，并使用 Temporal Ensembling 平滑重叠动作。
- **Diffusion Policy**：通过去噪网络生成动作序列，能够建模复杂的多模态动作分布，并通过 Receding Horizon Control 实现闭环执行。
- **ACT 的主要特点**：动作块预测和重叠预测融合。
- **Diffusion Policy 的主要特点**：基于得分的迭代生成和多模态动作分布建模。
##### 17. 总结
**Diffusion Policy 的核心思想**：将机器人动作预测转化为条件扩散生成任务，让模型从专家示范中学习动作分布的去噪方向，从随机动作噪声中逐步生成合理的连续动作序列。
关键技术关系：
- **Imitation Learning**：训练范式，使用专家示范学习动作策略。
- **Score Gradient**：表示动作概率密度增长的局部方向。
- **Diffusion Model**：通过多噪声等级的去噪学习复杂动作分布。
- **CNN + FiLM / Transformer + Cross-Attention**：两种条件去噪网络架构。
- **Action Prediction Horizon**：一次预测未来较长的动作序列。
- **Receding Horizon Control**：只执行部分动作，并根据新观察重新规划。
**一句话：Diffusion Policy 通过学习专家动作分布的梯度信息，从随机噪声中迭代生成合理动作，再结合滚动时域控制完成机器人闭环操作。**
