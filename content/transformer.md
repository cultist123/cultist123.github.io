# Transformer

## 1. 整体结构

<img src="/images/ai/image-20261014230652042.png" alt="image-20261014230652042" style="zoom:50%;" />

#### 1.1 输入表示

- 一个句子 = **$n \times d$ 的矩阵**：$n$ = 序列长度（token 个数，行数），$d$ = 向量长度（$d_{model} = 512$，列数）
- 每个词的向量长度都一样，靠数值不同区分意思；用 512 个数是为了同时描述含义的多个方面
- **位置编码**：attention 本身不知道词的顺序，打乱词序结果不变，所以要把位置编码**加**到词向量上（相加，不是拼接）

## 2. Self-Attention

<img src="/images/ai/image-20261014230800296.png" alt="image-20261014230800296" style="zoom:50%;" />
$$
\text{Attention}(Q,K,V)=\text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$

- $Q = XW_Q,\ K = XW_K,\ V = XW_V$：把词向量投影到"适合比较相似度"的空间
- **维度**：$Q$ 是 $n \times d_k$，$K$ 是 $m \times d_k$，$V$ 是 $m \times d_v$
  - $QK^T$：$(n \times d_k)(d_k \times m) = n \times m$ **打分表**，第 $i$ 行 = 第 $i$ 个 query 对所有 key 的相似度
  - 乘 $V$：$(n \times m)(m \times d_v) = n \times d_v$
  - self-attention 时 $n = m$；cross-attention 时 $n \neq m$
- **除以 $\sqrt{d_k}$**：$d_k$ 越大点积方差越大，softmax 会接近 one-hot，梯度很小；缩放后保持稳定
- **本质**：对 $V$ 做加权平均，负责**词与词之间交流信息**

> **为什么 K 和 V 行数必须相同，Q 和 K 列数必须相同？**
> K、V 是一一配对的（每个 key 对应一个 value），所以行数都是 $m$；Q 和 K 要做点积，所以列数都是 $d_k$。$d_v$ 可以和 $d_k$ 不同。

## 3. Multi-Head Attention

<img src="/images/ai/image-20261014230924284.png" alt="image-20261014230924284" style="zoom:50%;" />

- $d_{model} = 512$，$h = 8$ 个头，每个头 $d_k = d_v = 512 / 8 = 64$
- 三步：**投影到 8 组 Q/K/V → 每个头各自算 attention → 拼接后乘 $W_O$**
- 总计算量和单头差不多（每个头维度变小了）
- 作用：不同的头关注不同类型的关系（比如一个头看指代，一个头看语法）

> $W_O$是一个可以学习的参数,所以attention层总共有$W_Q,W_K, W_V, W_O$四个可以学习的参数

## 4. Mask

- **Causal mask**：点积照常算全部，在 softmax **之前**把未来位置设为 $-\infty$，softmax 后权重为 0
  - 主要为了**训练**：teacher forcing 把整句一次输入、并行计算，mask 保证每个位置看不到后面的答案
  - **推理**时自回归一个个生成，未来本来就不存在，用 KV cache 存之前的 K、V
- **Padding mask**：把补齐用的 pad 位置屏蔽掉

| Attention                     | Causal mask | Padding mask |
| ----------------------------- | ----------- | ------------ |
| Encoder self-attention        | ✗           | ✓            |
| Decoder masked self-attention | ✓           | ✓            |
| Cross-attention               | ✗           | ✓            |

## 5. FFN（MLP）

$$\text{FFN}(x) = \text{ReLU}(xW_1 + b_1)W_2 + b_2 \qquad 512 \to 2048 \to 512$$

- **逐词独立计算，所有位置共用同一套参数**（同一个函数作用在每个词上，可以处理任意长度）
- 作用：attention 只是加权平均（基本线性），FFN 用非线性把收集来的信息**组合成新特征**
  - 例：attention 后 "it" 带有"动物"和"累了"的信息，FFN 的某个神经元组合出"累了的动物"
- 先升到 2048 维：有更多空间组合特征；再降回 512：和残差对得上

|           | 乘法形式                | 混合的是什么                    |
| --------- | ----------------------- | ------------------------------- |
| Attention | $A \cdot V$（乘在左边） | 不同词之间 → 交流               |
| FFN       | $X \cdot W$（乘在右边） | 一个词内部的各个特征 → 自己加工 |

> **追问：只有 attention、去掉 FFN 会怎样？**
> 每层只是在词之间做加权平均，缺少非线性加工，表达能力大幅下降。可以理解为：attention 是开会交流，FFN 是会后各自消化思考。

## 6. 残差 + Normalization

#### 6.1 残差

- 每个子层：$\text{LayerNorm}(x + \text{Sublayer}(x))$
- $\frac{\partial y}{\partial x} = I + \frac{\partial F}{\partial x}$，梯度至少有 $I$ 这条通路，深层也能训练

#### 6.2 Batch Normalization

- BatchNorm 通常对**每个 feature**，在 **batch 维度**上统计 mean/std
- 同样有可学习的 $\gamma$、$\beta$ 做 scale 和 shift
- 依赖 batch：batch 小时统计量不准，**batch = 1 时每个 feature 都被压成 0**
- 训练和推理不一致：推理时要用训练中累计的 running mean / running var

#### 6.3 Layer Normalization

LayerNorm 对**每个 token 自己的 $D$ 个 feature** 做 normalization

* $h_i = [h_{i1}, h_{i2}, \dots, h_{iD}]$，代表某一层输出的第 $i$ 个 hidden vector
* $\mu_i = \text{mean}(h_i)$，$\sigma_i = \text{std}(h_i)$，然后做 normalize：$z_i = \frac{h_i - \mu_i}{\sqrt{\sigma_i^2 + \epsilon}}$（$\epsilon$ 是很小的数，防止除以 0）
* 最后再做 learnable 的 scale 和 shift：$y_i = \gamma \odot z_i + \beta$
  * $\gamma$ 和 $\beta$ 都是 $D$ 维，$\odot$ 表示 element-wise multiplication，意思是**每个维度都有自己的 scale 和 shift**
  * 作用：normalize 后分布被强制成均值 0、方差 1，可能限制表达能力；$\gamma$、$\beta$ 让模型可以自己学回需要的尺度和偏移
* 不依赖 batch，训练和推理计算方式完全一样

|                        | BatchNorm                         | LayerNorm                             |
| ---------------------- | --------------------------------- | ------------------------------------- |
| 统计范围               | 同一个 feature，跨 batch 里的样本 | 同一个 token，跨自己的 $D$ 个 feature |
| 依赖 batch             | 是                                | 否                                    |
| $\gamma$、$\beta$ 维度 | 每个 feature 一个                 | $D$ 维                                |
| 常用于                 | CNN                               | Transformer、RNN                      |

> **追问：为什么 Transformer 用 LN 不用 BN？**
> 句子长度不一（有 padding），batch 也常常很小，BN 的统计量不稳定；LN 每个 token 自己算，不受 batch 和序列长度影响，训练推理一致。

#### 6.4 Post-LN vs Pre-LN

- 原版是 **Post-LN**：先加残差再 LN，$\text{LN}(x + F(x))$
- 现在大模型多用 **Pre-LN**：先 LN 再进子层，$x + F(\text{LN}(x))$，残差通路更干净，训练更稳定

## 7. Dropout

- 原版 $p = 0.1$，用在三处：attention 的 softmax 权重之后、每个子层输出（加残差之前）、embedding + 位置编码之后

## 8. 三种架构

| 架构            | 代表                 | 特点                  | 适合             |
| --------------- | -------------------- | --------------------- | ---------------- |
| Encoder-only    | BERT                 | 双向看全句            | 理解：分类、抽取 |
| Decoder-only    | GPT                  | causal mask，只看前文 | 生成             |
| Encoder-Decoder | T5、原版 Transformer | 输入输出长度/形式不同 | 翻译、摘要       |

## 9. 和 CNN / RNN 对比

- **归纳偏置**：CNN 假设局部性 + 平移等变，RNN 假设顺序性；Transformer 假设很少 → 更灵活、上限高，但需要更多数据
- **并行**：RNN 必须一步步算；Transformer 所有位置可以并行
- **长距离依赖**：任意两个词一步直接相连，不用一层层传递
- **代价**：attention 复杂度 $O(n^2 \cdot d)$，序列长了显存和计算量增长很快

> **追问：为什么 ViT 小数据不如 CNN，大数据反而更好？**
> CNN 自带适合图像的假设，数据少时也能学好；ViT 要从数据里自己学这些规律，数据少学不出来，数据多时不受假设限制，效果反超。

## 一句话总结

Transformer = **attention 负责词之间交流 + FFN 负责每个词自己加工**，用残差和 LayerNorm 保证能堆得很深；完全并行、能直接建模长距离依赖，代价是 $O(n^2)$ 复杂度和对数据量的需求。