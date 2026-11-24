# CLIP：图文对比预训练与零样本迁移

> Radford et al., 2021（OpenAI）｜整理自 Zotero 阅读批注｜[在 Zotero 中打开 PDF](zotero://open-pdf/library/items/EBRF6KBS)

**一句话**：用 4 亿对网络（图像, 文本）做对比学习，让图像编码器和文本编码器在同一语义空间对齐；推理时把类别名写成句子，就能直接做 **zero-shot** 分类，摆脱"固定类别 + 分类头"的范式。

##### 1. 动机：为什么要从文本中学习
- **传统做法的局限**：视觉模型在 *a fixed set of predetermined object categories* 上训练（如 ImageNet 固定 1000 类）。输出只能"1000 选 1"（*static softmax classifiers*），遇到新类别就要重新标注、重新训练，难以扩大规模。
- **CLIP 的思路**：*Learning directly from raw text about images*。互联网上的文本是取之不尽的弱监督信号——文本里见过的概念，就有可能在图片里认出来。
- **NLP 的启发**：GPT 等用 *autoregressive / masked language modeling* 自监督预训练 + *"text-to-text"* 接口，做到了与任务无关的迁移，几乎不需要特定数据集的训练数据（*little to no dataset specific training data*）。CLIP 想把这种范式搬到视觉上。
- **为什么以前没做成**：之前的弱监督 / 文本监督工作并非方法不行，而是**规模不够**——只在一二十万张图上训练几个加速器天（*accelerator days on one to two hundred thousand images*），而同期弱监督工作用的是加速器"年"级别的计算。CLIP 把数据扩大到 **4 亿（image, text）对**。
- 文本监督介于两端之间（*pragmatic middle ground*）：比固定标签更灵活，比纯无监督更容易利用。

##### 2. 方法总览：对比预训练 + 零样本分类器
<img src="/images/obsidian/67d89c32e3bd.png" alt="CLIP_图1_CLIP方法总览.png" width="720" />
*论文图 1：(1) 对比预训练；(2) 用标签文本构造分类器；(3) 零样本预测。*

**(1) 对比预训练**
- 一个 batch 有 N 对（图像, 文本），分别过 Image Encoder 和 Text Encoder，得到 $I_1..I_N$ 与 $T_1..T_N$。
- 计算 N×N 相似度矩阵 $I_i\cdot T_j$：**对角线是正样本**（真实配对），其余 $N^2-N$ 个都是负样本。
- 不需要人工标注类别、筛选清洗标签，只需要"配对"本身：模型学的是**语言和图片的配对关系**，而不是单纯的图片特征。
- 无监督/弱监督需要大量、质量过得去的数据。

**(2)(3) 零样本推理**
- 训练好后得到两个编码器。文本端输入你关心的标签，例如 plane / car / dog / bird。
- 用 prompt template 把单词变成句子："A photo of a {object}."，4 个类别 → 4 个句子 → 4 个文本特征。
- 图像特征与这些文本特征算余弦相似度，经 softmax 得到概率分布，最相似的句子就是预测类别；多个类别可并行计算。
- **没有分类头、没在下游数据集上微调**：文本编码器即时"合成"了一个零样本线性分类器。

##### 3. 为什么选对比学习而不是预测文本
<img src="/images/obsidian/d65397fb62be.png" alt="CLIP_图2_对比学习效率.png" width="480" />
*论文图 2：同样看过的图片数下，对比目标（绿）的零样本 ImageNet 准确率远高于词袋预测（橙）和 Transformer 语言模型（蓝）。*

- 一张图可以有无数种描述，**逐字预测**图片对应的文本（类似 image captioning）可能性太多，训练很慢。
- 论文改为一个更容易的代理任务：*predicting only which text as a whole is paired with which image*，即**只判断图文是否配对**（*predictive objective → contrastive objective*）。
- 效果：词袋预测比 Transformer 语言模型快 3 倍，对比目标再快 4 倍。

##### 4. 数据集：WIT（WebImageText）
- 从互联网收集 **4 亿**（图像, 文本）对。
- 构造方式：用 50 万个查询词（Wikipedia 高频词等）检索图文对，每个查询最多保留 2 万对，以平衡类别。
- 目标是学习**开放集合的视觉概念**（*open set of visual concepts*），而不是固定类别。
- 数据集足够大，因此作者认为过拟合（*over-fitting*）不是主要问题。

##### 5. 训练实现：核心伪代码
<img src="/images/obsidian/4f7436db13f1.png" alt="CLIP_图3_伪代码.png" width="480" />
*论文图 3：CLIP 核心实现的 Numpy 风格伪代码。*

流程与单模态对比学习一模一样，只是把两路特征换成**图像特征 + 文本特征**：
1. 两个编码器分别提特征 $I_f$、$T_f$。
2. 线性投影到同一嵌入空间并 L2 归一化（CLIP 只用**线性**投影，没有采用 SimCLR 等工作里的 *non-linear projections* 非线性投影头）。
3. 相似度矩阵 × $\exp(t)$，温度 $t$ 是**可学习**参数。
4. 标签就是 `arange(n)`（对角线）；对图像方向、文本方向各做一次交叉熵，取平均（对称损失）。

训练细节：
- Batch size 达 **32,768**。
- **混合精度**（*Mixed-precision*）加速训练、节省显存，且基本不掉点。
- 最大的 RN50x64 用 592 张 V100 训练 18 天；最大的 ViT 用 256 张 V100 训练 12 天。
- ViT-L/14 额外在 **336 像素**更高分辨率上多训练 1 个 epoch（类似 FixRes），提升效果，即 ViT-L/14@336px。

##### 6. Zero-shot 迁移与 Prompt Engineering
**目标**：表征学习通常学到好特征后仍要微调；CLIP 借助文本实现灵活的 zero-shot 迁移。

**和 Visual N-Grams 对比**：ImageNet 零样本准确率从 11.5% 提升到 **76.2%**，与原始有监督 ResNet-50 持平，而且**一张 ImageNet 训练图都没用**（*none of the 1.28 million crowd-labeled training examples*）。

**为什么需要 prompt**：
- **多义性**（*polysemy*）：只给一个单词有歧义，如 *construction cranes*（起重机）与 *cranes*（鹤）。
- **分布差距**（*distribution gap*）：预训练文本大多是完整句子，推理时只给单词会不匹配。
- 默认模板 **"A photo of a {label}."**；针对数据集加上下文可以**缩小解空间**，如 Oxford-IIIT Pets 用 "A photo of a {label}, a type of pet."。
- **Prompt ensembling**：用多个模板分别推理再集成。ImageNet 上集成 80 个模板，比单一模板再提升 3.5%；prompt engineering 与 ensembling 合计提升近 5%。

##### 7. 零样本 vs 有监督 vs 少样本
<img src="/images/obsidian/bb251046c55c.png" alt="CLIP_图5_零样本vs线性探针.png" width="480" />
*论文图 5：零样本 CLIP 与在 ResNet-50 特征上训练的全监督线性分类器对比，27 个数据集中 16 个更好（含 ImageNet）。*

- 对比对象是**线性探针**（*linear probe*）基线：冻住 ResNet-50 特征，只在每个数据集上训练一个线性分类头；而 CLIP 这边完全零样本。
- 结论：零样本迁移不只在个别数据集上有效。普通物体分类（StanfordCars、Food101 等）表现好；**物体计数（CLEVRCounts）、纹理（DTD）、卫星图（EuroSAT）、医学图像（PatchCamelyon）**等专业或抽象任务明显更弱。

<img src="/images/obsidian/6d98fd5154ac.png" alt="CLIP_图6_零样本vs少样本.png" width="440" />
*论文图 6：零样本 CLIP ≈ 同一特征空间上 4-shot 线性分类器的平均水平。*

- zero-shot 与 few-shot 的用法对比：零样本 CLIP 和在**它自己特征上**训练的 4-shot 线性探针相当。
- 对很难的任务，还是要给一点样本（*few-shot transfer*），而不是完全 zero-shot。

##### 8. 表征学习：线性探针
<img src="/images/obsidian/62497a1fc675.png" alt="CLIP_图10_线性探针对比.png" width="720" />
*论文图 10：线性探针平均分 vs 计算量，CLIP-ViT（红星）在 12 个与 27 个数据集上均最优。*

- 3.1 节测 zero-shot 迁移，3.2 节改为测**表征学习**（*Representation Learning*）质量。
- 两种评估方式：
  - **线性探针**：冻住模型，在提取的特征上训练线性分类器。
  - **端到端微调**：更灵活，但效果分不清是预训练还是微调的功劳，还需要大量调参。论文选择线性探针，因为它更能反映**与数据集无关的预训练**（*dataset-agnostic pre-training*）本身学到了什么。
- 结论：CLIP 的线性探针效果最好，且随算力扩展更高效。

##### 9. 鲁棒性：分布偏移
<img src="/images/obsidian/e8e1f4f49b8c.png" alt="CLIP_图13_分布偏移鲁棒性.png" width="720" />
*论文图 13：在 ImageNet 上准确率相同（76.2）时，零样本 CLIP 在 ImageNetV2 / R / ObjectNet / Sketch / A 等分布偏移数据集上远好于 ResNet-101。*

- 泛化性在这里体现为**稳健性**（robustness）：标准 ImageNet 模型在原分布上高、换分布就掉；零样本 CLIP 曲线更接近理想的 $y=x$。
- 例：ImageNet-R（艺术/卡通香蕉）37.7 → 88.9，ImageNet-A（对抗难样本）2.7 → 77.1。

##### 10. 与人类对比
<img src="/images/obsidian/42bf38ddbcb6.png" alt="CLIP_表2_人类对比.png" width="480" />
*论文表 2：Oxford-IIIT Pets 上人类与 CLIP 的对比。*

- 零样本人类 53.7%，零样本 CLIP 93.5%。
- 人类只看**一张**样例就升到 75.7%，再多看一张（two-shot）几乎不再提升——人类能高效利用**先验知识**，知道自己哪里不确定；CLIP 的 few-shot 方式还做不到这一点（*one-shot / two-shot*）。

##### 11. 局限
- 零样本平均水平只是与简单基线（ResNet-50 线性探针）*competitive*，距离各数据集的 **state of the art** 仍有明显差距。
- 处理不了**抽象和系统性任务**（*abstract and systematic tasks*），如计数。
- 只能从给定的类别里**选**，不能像 image captioning 那样**生成**新输出。后续工作（如 BLIP）尝试把理解和生成统一起来。
- 评测用了 27 个数据集，但测的主要还是分类；复杂任务和视觉概念仍难以评估。

##### 12. 总结
- 把 NLP 中"大规模预训练 + 自然语言接口"的思路**迁移到视觉领域**。
- 通过对比预训练，CLIP 在预训练中学会了大量任务，再借助 **prompt** 零样本迁移到下游数据集，**解放了固定类别的分类范式**。
- 关键要素：**数据规模（4 亿对）+ 对比目标（高效）+ 自然语言接口（prompt）**。

> [!tip] 和机器人 / VLA 的联系
> CLIP 式的图文对齐表征是后续 VLM 的视觉骨干来源之一（如 SigLIP 也采用图文对比训练），VLA 再在 VLM 之上接动作输出。读 RT-2、OpenVLA、π0 时可以回看这里。
