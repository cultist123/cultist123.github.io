# ACT / ALOHA：动作分块与双臂模仿学习

##### 1. 研究背景与核心问题
机器人精细操作（Fine-Grained Manipulation）需要高精度位置控制、接触力协调和闭环视觉反馈。例如穿扎带、插入内存条、操作乒乓球等任务，不仅要求机械臂移动准确，还要在接触物体时控制力度，并根据摄像头反馈持续调整动作。
传统高精度遥操作设备价格昂贵，论文提出低成本双臂机器人平台 **ALOHA**，并采用 **ACT（Action Chunking with Transformers）** 学习精细操作策略。
**核心目标**：通过低成本硬件收集人类示范，利用模仿学习训练机器人，使其仅依靠 RGB 图像与关节状态完成复杂的双臂操作。
<img src="/images/obsidian/81325f50fe45.png" alt="ACT_论文图1_ALOHA硬件.png" width="600" />
*论文图 1：ALOHA 主从遥操作（左）与可完成的精细任务（右），整机成本约 2 万美元。*
##### 2. 基础概念：Policy Learning 与 Environment Modeling
**Policy Learning（策略学习）**：学习在当前观察下应该执行什么动作。
$$
a_t=\pi_\theta(o_t)
$$
例如摄像头发现插头偏左，策略预测机械臂应该向右调整。
**Environment Modeling（环境建模）**：学习给定当前状态和动作后，环境将如何变化。
$$
s_{t+1}=f(s_t,a_t)
$$
例如预测机械臂移动后，物体的位置、碰撞和接触力如何变化。
**为什么直接学习策略通常更简单？** 策略只需要学会如何执行有效动作，而精确环境建模可能需要预测复杂的摩擦、接触、碰撞和运动关系。
两者不互斥：
- **Model-Free**：不显式学习环境动态模型，直接学习动作策略。
- **Model-Based**：利用或学习环境模型，预测动作后果并辅助决策。
<img src="/images/obsidian/24ace3751cae.svg" alt="ACT_01_策略学习vs环境建模.svg" width="680" />
##### 3. 机器人模仿学习（Imitation Learning）
**模仿学习**：让机器人通过学习人类示范掌握操作技能，而不是完全依靠试错。
典型流程：人类操作机器人 → 记录图像、关节状态和动作 → 训练策略网络 → 机器人自主执行。
主要方法包括：
- **Behavior Cloning（BC）**：使用监督学习直接模仿专家动作。
- **DAgger**：让当前策略与环境交互，再由专家纠正错误状态对应的动作，减少分布偏移。
- **Inverse Reinforcement Learning（IRL）**：从专家示范中推断奖励函数，再据此学习策略。
- **Action Chunking**：一次预测连续多个动作。
- **Diffusion Policy**：使用扩散模型学习复杂、多模态的动作分布。
注意：Action Chunking 和 Diffusion Policy 是策略建模技术，不是与 BC、DAgger 完全平行的模仿学习类别。
**ACT 本质上属于 Behavior Cloning**，但通过 Transformer、CVAE 和动作分块改进传统 BC。
##### 4. 现有 BC 方法及局限
已有研究主要从以下方向改进 BC：
- **历史信息建模**：利用 Transformer 等网络结合过去的观察和动作，而非只使用当前状态。
- **训练目标优化**：改变动作预测的损失函数，提高策略学习效果。
- **正则化**：减少过拟合，提高泛化能力。
- **多任务与少样本学习**：让一个策略完成多种任务，或利用少量示范掌握新任务。
- **语言引导**：根据自然语言指令生成操作策略，例如 VLM/VLA 相关方法。
- **任务结构建模**：利用机器人任务中的空间关系、抓取约束和运动特性。
这些方法部分借鉴了深度学习和 Transformer 的研究成果，但模仿学习本身并不是从 LLM 发展而来的。
##### 5. 数据分布与分布偏移
**Data Distribution（数据分布）**：训练数据中各种状态、动作和场景出现的频率与比例。
例如训练集中 80% 的物体位于桌子中央，15% 位于左边，5% 位于右边，模型可能更擅长处理中央位置的物体。
**Distribution Shift（分布偏移）**：训练时的数据分布与实际执行时遇到的数据分布不同。
机器人 BC 容易出现分布偏移：某一步动作发生误差 → 机器人进入示范数据中较少出现的状态 → 后续动作更容易出错 → 误差不断累积。
**核心问题**：传统 BC 每一步独立预测动作，长时程任务中的预测误差可能不断传播。
<img src="/images/obsidian/e234571a4e15.svg" alt="ACT_02_分布偏移与误差累积.svg" width="680" />
##### 6. Policy Interaction 与 Teleoperation
**Policy Interaction（策略交互）**：让当前学到的策略真实地与环境交互，执行动作并收集新数据。
**Expert Correction（专家纠正）**：机器人执行错误动作时，由人类提供正确动作示范，用于继续训练。
例如 BC 训练抓杯子 → 机器人实际尝试 → 抓取失败 → 人类纠正 → 将纠正数据加入训练集。
**Teleoperation（遥操作）**：人类通过手柄、VR 控制器或主从机械臂控制机器人，记录操作过程以收集示范数据。
遥操作存在成本高、操作不直观、缺乏自然触觉反馈等问题。ALOHA 通过低成本主从机械臂设计降低双臂示范数据的收集成本。
<img src="/images/obsidian/d0d9244441ac.png" alt="ACT_论文图3_相机与夹爪.png" width="600" />
*论文图 3：前方 / 顶部 / 两个腕部共 4 路相机，以及主端的“手柄+剪刀”结构与定制夹爪。*
##### 7. ACT：Action Chunking with Transformers
ACT 的核心是：**利用模仿学习，让 Transformer 根据当前图像和机器人状态，一次预测未来一段动作，而不是每次只预测一个动作。**
整体流程：
**RGB Images + Joint Positions → CNN → Transformer Encoder → Transformer Decoder → Action Chunk**
输入：
- **RGB Images**：4 路摄像头图像，每路 $480\times640\times3$。
- **Joints**：双臂当前的 14 维关节状态。
- **Latent Variable $z$**：CVAE 学习的潜在动作风格变量。
输出：
$$
\hat A_t=[\hat a_t,\hat a_{t+1},\ldots,\hat a_{t+k-1}]
$$
其中每个 $\hat a_t\in\mathbb R^{14}$，表示双臂关节目标位置，整个 Action Chunk 的形状为 $k\times14$。
**RGB 如何映射为动作？** CNN 提取物体及环境的视觉特征，Transformer 结合关节状态预测未来的关节目标值，再交给机器人底层控制器执行。不是直接把像素值映射成电机电流，也不是输出自然语言动作。
<img src="/images/obsidian/71d251924153.png" alt="ACT_论文图10_四路观测.png" width="560" />
*论文图 10：每行一个任务，四列依次为顶部、前方、左腕、右腕相机。*
##### 8. Action Chunking：动作分块
传统 BC 每次预测一个动作，ACT 一次预测连续 $k$ 个动作。
假设任务需要 100 个动作：
- 传统 BC：连续预测 100 次。
- ACT：如果每次完整执行 10 个动作，则只需要 10 次动作块决策。
有效时域（Effective Horizon）：
$$
H_{\mathrm{effective}}\approx\frac{H}{k}
$$
**Effective Horizon**：完成一个任务需要进行多少次高层策略决策。Action Chunking 将单步动作决策变成动作块决策，因此在非重叠执行情况下，有效决策时域缩短至原来的 $1/k$。
**为什么缓解误差累积？** 一次预测连续动作，可以学习动作之间的关联，减少逐步独立决策导致的误差传播。但并不能完全消除执行误差。
注意：$1/k$ 对应非重叠动作块执行。如果每一步都重新预测并结合 Temporal Ensembling，实际调用策略的次数并不会减少到 $H/k$。
<img src="/images/obsidian/477c71dd4781.svg" alt="ACT_03_动作分块有效时域.svg" width="680" />
##### 9. Temporal Ensembling：时间集成
<img src="/images/obsidian/2e3aa1d3239e.png" alt="Screenshot 2026-11-09 at 21.10.44.png" width="468" />
只有 Action Chunking 时，模型可能执行完整的 $k$ 步后才重新预测：
t=0：预测 [a0, a1, a2, a3]
t=4：预测 [a4, a5, a6, a7]
缺点是动作块内部缺少新的策略反馈，动作块之间也可能出现不连续。
**Temporal Ensembling**：每个时间步重新观察环境并预测动作块，然后对同一个执行时刻的重叠动作预测加权平均。
例如 $k=3$：
t=0：预测 [a0, a1, a2]
t=1：预测 [b1, b2, b3]
t=2：预测 [c2, c3, c4]
在时间 $t=2$，模型存在三个针对当前动作的预测：
$$
a_2,\quad b_2,\quad c_2
$$
最终动作：
$$
\hat a_2=w_1a_2+w_2b_2+w_3c_2,\qquad\sum_iw_i=1
$$
论文通过指数形式的权重融合不同时间生成的预测。
**作用**：减少动作抖动和动作块之间的不连续，同时保留频繁观察并调整动作的能力。
**区别**：Action Chunking 负责一次预测一段动作；Temporal Ensembling 负责融合不同时间对同一动作的预测。
<img src="/images/obsidian/ead95d3d73ca.svg" alt="ACT_04_时间集成k3示例.svg" width="680" />
##### 10. CVAE：Conditional Variational Autoencoder
**CVAE（条件变分自编码器）** 是一种生成模型，用于学习在相同条件下可能存在的多种合理输出。
例如人类拿杯子时，可能从左侧抓取，也可能从右侧抓取。直接使用单一平均动作可能得到不合理的结果。
CVAE 通过潜在变量 $z$ 表示示范动作中的变化性：
$$
A=\operatorname{Decoder}(o_t,q_t,z)
$$
- $o_t$：当前视觉观察。
- $q_t$：当前关节状态。
- $z$：动作方式的潜在表示。
- $A$：预测的动作序列。
**Conditional（条件）**：生成动作时除了 $z$，还需要结合当前图像和机器人关节状态。
CVAE 的两个核心部分：
- **Encoder**：训练时输入人类示范动作与关节状态，预测潜在变量的概率分布。
- **Decoder**：根据视觉、关节状态和 $z$ 生成未来动作块。
这里的 $z$ 是连续特征向量，不一定对应某种能直接解释的动作类别。
##### 11. ACT 的完整网络架构
<img src="/images/obsidian/ff445d9c5459.png" alt="ACT_论文图4_架构.png" width="700" />
*论文图 4：左为 CVAE 编码器（仅训练用），右为策略（CVAE 解码器）。*
###### 11.1 左侧：CVAE Encoder
训练时输入：
**[CLS] + Joints + Human Action Sequence**
- **[CLS]**：用于汇总输入序列的特殊可学习 Token。
- **Joints**：14 维，经过线性层映射为 512 维。
- **Action Sequence**：$k\times14$，每个动作映射为 512 维。
- **Positional Embedding**：表示动作在序列中的先后顺序。
这些数据进入一个 4 层 Transformer Encoder，输出潜在分布参数：
$$
\mu_z,\quad\sigma_z\in\mathbb R^{32}
$$
通过重参数化采样：
$$
z=\mu_z+\sigma_z\odot\epsilon,\qquad \epsilon\sim\mathcal N(0,I)
$$
**重参数化的作用**：将随机性转移到 $\epsilon$，使梯度能够通过采样过程反向传播到 Encoder。
###### 11.2 右侧：动作预测网络
输入：**4 路 RGB 图像 + Joints + z**
视觉部分：
- ResNet18 提取图像特征。
- 将视觉特征展开为 Token，并映射到 Transformer 使用的 512 维空间。
- 添加位置编码，保留图像特征的空间位置信息。
机器人状态：
- Joints：$14\rightarrow512$ 维。
- $z$：$32\rightarrow512$ 维。
模型结构：
- **Transformer Encoder（4 层）**：通过 Self-Attention 融合视觉、关节状态和潜在变量。
- **Transformer Decoder（7 层）**：使用固定位置查询，通过 Cross-Attention 从 Encoder 输出中提取信息，并预测未来 $k$ 个动作。
最终输出：
$$
\hat A\in\mathbb R^{k\times14}
$$
**两个 Encoder 的区别**：
- CVAE Encoder：学习人类示范动作中的潜在变化性，只在训练阶段使用。
- Policy Transformer Encoder：理解当前环境与机器人状态，在训练和实际执行时都使用。
<img src="/images/obsidian/5f49bb9cf26d.png" alt="ACT_论文图11_详细架构.png" width="700" />
*论文图 11：ACT 详细架构（含各模块维度）。*
##### 12. ACT 的训练流程
###### 12.1 Step 1：采样人类示范数据
从 Demo Dataset 中采样：
- 4 张 RGB 图片。
- 当前 14 维 Joints。
- 后续 $k$ 步的动作序列，形状为 $k\times14$。
###### 12.2 Step 2：推断潜在变量 z
将人类示范动作与当前关节状态输入 CVAE Encoder，预测 $\mu_z$ 和 $\sigma_z$，再使用重参数化采样得到 $z$。
###### 12.3 Step 3：预测动作序列
将 RGB 图像、Joints 和 $z$ 输入策略网络：
**ResNet18 → Transformer Encoder → Transformer Decoder → Predicted Action Chunk**
训练时将预测动作与人类示范动作进行比较。
主要训练目标：
$$
\mathcal L_{\mathrm{ACT}}=\mathcal L_{\mathrm{reconstruction}}+\beta\mathcal L_{\mathrm{KL}}
$$
- **Reconstruction Loss**：让预测动作接近人类示范动作，ACT 使用 L1 动作重建损失。
- **KL Loss**：约束 CVAE 学到的潜在分布接近标准正态分布，避免潜在空间过度分散。
- $\beta$：控制 KL 项的权重。
**训练目标**：让策略既能准确模仿人类动作，也能学习示范动作中存在的不同变化模式。
##### 13. ACT 的测试与实际运行
训练完成后，不再需要人类示范动作，也不再运行 CVAE Encoder。
测试输入：
- 当前 4 路 RGB 图片。
- 当前 14 维关节状态。
- 固定潜在变量 $z=0$。
执行流程：
**RGB Images + Joints + z=0 → CNN → Transformer Encoder → Decoder → Future Action Chunk → Robot Controller**
虽然 CVAE 在训练时学习动作分布，但 ACT 实际推理通常使用固定零向量 $z$，使策略产生确定性的动作预测。
如果启用 Temporal Ensembling，机器人每个时间步重新预测一个动作块，并融合重叠预测后执行。
<img src="/images/obsidian/f7fa7bd55372.svg" alt="ACT_05_训练与推理信息流.svg" width="700" />
##### 14. 论文核心贡献与局限
**主要贡献**
- **ALOHA**：低成本双臂遥操作硬件平台，降低高质量操作示范的收集成本。
- **ACT**：通过 Transformer 一次预测未来多个动作，降低长时程任务的决策难度。
- **CVAE**：对人类示范中的动作变化进行建模。
- **Temporal Ensembling**：融合重叠动作预测，提高执行平滑性。
<img src="/images/obsidian/a88f3163a2cd.png" alt="ACT_论文图8_消融.png" width="700" />
*论文图 8：(a) 动作分块对基线也有效；(b) 时间集成的影响；(c) 去掉 CVAE 后从人类数据学习明显变差；(d) 遥操作 5 Hz vs 50 Hz 的完成时间。*
**主要局限**
- 依赖人类示范数据的数量、质量与分布。
- 对训练数据中没有充分覆盖的新环境、新物体或动作可能泛化不足。
- 直接学习动作策略并不意味着模型理解完整物理规律。
- 细粒度接触操作仍可能受到视觉遮挡、感知误差和缺少显式力反馈等因素影响。
##### 15. 总结
**ALOHA 解决如何以较低成本收集双臂精细操作示范，ACT 解决如何从这些示范中学习连续动作策略。**
关键技术关系：
- **Behavior Cloning**：整体学习范式，用人类示范监督训练机器人。
- **ResNet18**：将 RGB 图像转换为视觉特征。
- **Transformer**：融合多模态输入并生成未来动作块。
- **CVAE**：学习人类示范中的动作变化性。
- **Action Chunking**：一次预测多步动作，减小有效决策时域。
- **Temporal Ensembling**：对重叠动作预测加权平均，提高动作连续性。
**一句话：这篇论文通过低成本双臂机器人平台收集人类操作示范，再利用 CVAE + Transformer + Action Chunking 学习从视觉和关节状态到连续双臂动作的映射，使机器人能够模仿人类完成精细操作任务。**
