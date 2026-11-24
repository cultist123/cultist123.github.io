# Seq2Seq：编码器、解码器与注意力

### 61 编码器-解码器架构
<img src="/images/obsidian/1d89c2798130.svg" alt="d2l_61_编码器解码器.svg" width="420" />
- **编码器**：把变长输入序列 → 固定形状的**编码状态**（处理输入）
- **解码器**：把编码状态 → 变长输出序列；也可以接收额外输入（如上一步生成的词）
- 本质是一个**接口/抽象**，CNN 也能看成编码器（特征提取）+ 解码器（分类头）
```python
class EncoderDecoder(nn.Module):
    def forward(self, enc_X, dec_X, *args):
        enc_outputs = self.encoder(enc_X, *args)
        dec_state = self.decoder.init_state(enc_outputs, *args)  # 编码输出 → 解码器初始状态
        return self.decoder(dec_X, dec_state)
```
### 62 序列到序列学习（seq2seq）
<img src="/images/obsidian/fa04377d86ea.svg" alt="d2l_62_seq2seq训练.svg" width="520" />
**结构**：两个独立的 RNN（参数不共享，都参与训练）
- **编码器 RNN**：读入整句源语言，不需要输出，只要最后的隐状态（可以是双向、多层）
$$\mathbf{h}_t = f(\mathbf{x}_t, \mathbf{h}_{t-1}),\qquad \mathbf{c} = \mathbf{h}_T$$
- **解码器 RNN**：自回归逐词生成，从 `<bos>` 开始，生成 `<eos>` 停止
$$\mathbf{s}_{t'} = g(y_{t'-1}, \mathbf{c}, \mathbf{s}_{t'-1})$$
- 上下文 $\mathbf{c}$ 怎么传给解码器：
  1. 编码器最后时刻隐状态 → **初始化**解码器隐状态（要求两边层数、隐藏单元数相同）
  2. $\mathbf{c}$ 在**每个时间步**和解码器输入词嵌入 **concat** 一起喂进去
**关键细节**
- **Embedding 层**：词表大小 × embed_size 的矩阵，词索引 $i$ → 取第 $i$ 行作为词向量
- **Teacher forcing（强制教学）**：训练时解码器输入用**真实标签**（`<bos>` + 去掉最后一个词的目标句），不是自己的预测
- **预测**：只能用上一步自己的预测作为下一步输入（贪心取 argmax，更好的方式见束搜索）
<img src="/images/obsidian/041056452c55.svg" alt="d2l_62_seq2seq预测.svg" width="520" />
- **Masked 损失**：句子被 `<pad>` 填充到同长，填充位置的损失要乘 0 过滤掉（`sequence_mask` + `MaskedSoftmaxCELoss`）
**形状速记**（GRU，batch=4，steps=7，hidden=16，layers=2）
- 编码器 `output`: (num_steps, batch, num_hiddens)；`state`: (num_layers, batch, num_hiddens)
- 解码器输出: (batch, num_steps, vocab_size)
**BLEU**：衡量生成序列和标签的 n-gram 匹配度，完全一致为 1
$$\text{BLEU} = \exp\left(\min\left(0, 1 - \frac{\mathrm{len}_{\text{label}}}{\mathrm{len}_{\text{pred}}}\right)\right) \prod_{n=1}^k p_n^{1/2^n}$$
- $p_n$：预测中 n-gram 的精度（匹配数 / 预测中 n-gram 总数）
- 前面的指数项：**惩罚过短**的预测（短句容易精度高）
- $p_n^{1/2^n}$：**长 n-gram 权重更大**（越长越难匹配）
- 例：标签 ABCDEF，预测 ABBCD → $p_1=4/5,\ p_2=3/4,\ p_3=1/3,\ p_4=0$
### 66 使用注意力机制的 seq2seq（Bahdanau 注意力）
**动机**：普通 seq2seq 每一步都用**同一个** $\mathbf{c}$（整句压缩成一个向量），但翻译某个词时只和源句**对应位置**的词最相关 → 让每个解码步自己去"看"源句的不同部分。
<img src="/images/obsidian/21cd48e48a86.svg" alt="d2l_66_注意力seq2seq.svg" width="520" />
$$\mathbf{c}_{t'} = \sum_{t=1}^T \alpha(\mathbf{s}_{t'-1}, \mathbf{h}_t)\, \mathbf{h}_t$$
- **Query**：解码器上一步的隐状态 $\mathbf{s}_{t'-1}$（"我现在要翻译什么"）
- **Key = Value**：编码器**每个时间步**最后一层的输出 $\mathbf{h}_t$
- $\alpha$：加性注意力打分 + softmax（用 `valid_lens` 屏蔽 pad）
- 和 62 的唯一区别：固定 $\mathbf{c}$ → 每步变化的 $\mathbf{c}_{t'}$；只需要**重写解码器**，编码器不变
```python
for x in X:                                          # 解码器逐时间步
    query = hidden_state[-1].unsqueeze(1)             # (batch,1,h) 上一步最后一层隐状态
    context = self.attention(query, enc_outputs, enc_outputs, enc_valid_lens)
    x = torch.cat((context, x.unsqueeze(1)), dim=-1)  # 注意力输出 ⊕ 词嵌入
    out, hidden_state = self.rnn(x.permute(1, 0, 2), hidden_state)
```
- 因为每一步的 query 依赖上一步结果，解码器要写成 for 循环，训练比普通 seq2seq 慢
- 注意力权重热图可视化：每个输出词对应关注源句不同位置（近似"对齐"）
### 67 自注意力（Self-Attention）+ 位置编码
**自注意力**：Query、Key、Value **都来自同一个序列** $\mathbf{X}$，输出长度不变
$$\mathbf{y}_i = f(\mathbf{x}_i, (\mathbf{x}_1, \mathbf{x}_1), \ldots, (\mathbf{x}_n, \mathbf{x}_n))$$
→ 每个词都直接看整句所有词，得到带上下文的新表示。代码就是 `attention(X, X, X, valid_lens)`。
**CNN / RNN / 自注意力对比**（序列长 $n$，维度 $d$，卷积核 $k$）
<img src="/images/obsidian/21213fc6707e.svg" alt="d2l_67_CNN_RNN_自注意力对比.svg" width="520" />
|          | 计算复杂度         | 并行度（顺序操作） | 最大路径长度  |
| -------- | ------------- | --------- | ------- |
| CNN      | $O(knd^2)$    | $O(1)$    | $O(n/k)$ |
| RNN      | $O(nd^2)$     | $O(n)$    | $O(n)$  |
| 自注意力     | $O(n^2d)$     | $O(1)$    | $O(1)$  |
- 自注意力：可并行 + 任意两词一步直达（长距离依赖好学）
- 代价：复杂度是 $n^2$，**序列很长时很慢**
**位置编码**：自注意力本身**不感知顺序**（打乱输入顺序，输出只是跟着打乱）→ 把位置信息直接**加到**输入上：$\mathbf{X} + \mathbf{P}$
$$p_{i,2j} = \sin\left(\frac{i}{10000^{2j/d}}\right),\qquad p_{i,2j+1} = \cos\left(\frac{i}{10000^{2j/d}}\right)$$
- $i$：词在序列中的位置（行）；$2j, 2j+1$：编码维度（列）
- **绝对位置**：类似二进制编码，低维频率高、高维频率低，每个位置得到唯一的编码，且是连续浮点数
- **相对位置**：位置 $i+\delta$ 的编码 = 位置 $i$ 的编码乘一个**只和 $\delta$ 有关**的 2×2 旋转矩阵（$\omega_j = 1/10000^{2j/d}$）
$$\begin{bmatrix} \cos\delta\omega_j & \sin\delta\omega_j \\ -\sin\delta\omega_j & \cos\delta\omega_j \end{bmatrix}\begin{bmatrix} p_{i,2j} \\ p_{i,2j+1} \end{bmatrix} = \begin{bmatrix} p_{i+\delta,2j} \\ p_{i+\delta,2j+1} \end{bmatrix}$$
  → 模型更容易学到"两个词相隔多远"
> **四课串起来**：编码器-解码器（接口）→ seq2seq（用两个 RNN 实现，整句压成一个 $\mathbf{c}$）→ 加注意力（每步动态取 $\mathbf{c}_{t'}$，但仍是 RNN）→ 自注意力（干脆不用 RNN，序列自己对自己做注意力 + 位置编码）→ 下一课 Transformer
