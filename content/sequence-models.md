# 序列模型：N 元语法、RNN 与困惑度

## 序列与文本预处理

序列模型,序列有时序结构的数据:音乐、语言、文本、视频
马尔可夫假设,现在的状态和过去一段时间有关
潜变量模型:把过去一段时间建立成一个映射h,h和前面的h和前面的x有关,现在的x和前面的现在的h和前面的x有关,所以相当于建立两个模型
文本预处理:把文本当作时序序列,文本当作很长的时序信息
词表:字符串变成token,映射到从0开始的数字映射成索引index,最小的词记作unknown,主要以后有开始结束的符号<>,生僻词出现后进行统计\<unk>,corpus是一长串的整数

## 语言模型、RNN 与训练

**序列长度为 2：**
$$
p(x, x') = p(x)\,p(x' \mid x) = \frac{n(x)}{n} \cdot \frac{n(x, x')}{n(x)}
$$
**序列长度为 3：**
$$
p(x, x', x'') = p(x)\,p(x' \mid x)\,p(x'' \mid x, x') = \frac{n(x)}{n} \cdot \frac{n(x, x')}{n(x)} \cdot \frac{n(x, x', x'')}{n(x, x')}
$$
**一般形式（链式法则）：**
$$
p(x_1, x_2, \ldots, x_T) = \prod_{t=1}^{T} p(x_t \mid x_1, \ldots, x_{t-1})
$$
N元语法
**一元语法**（每个词独立，不依赖前面的词）：
$$
p(x_1, x_2, x_3, x_4) = p(x_1)\,p(x_2)\,p(x_3)\,p(x_4) = \frac{n(x_1)}{n} \cdot \frac{n(x_2)}{n} \cdot \frac{n(x_3)}{n} \cdot \frac{n(x_4)}{n}
$$
**二元语法**（每个词只依赖前 1 个词）：
$$
p(x_1, x_2, x_3, x_4) = p(x_1)\,p(x_2 \mid x_1)\,p(x_3 \mid x_2)\,p(x_4 \mid x_3) = \frac{n(x_1)}{n} \cdot \frac{n(x_1, x_2)}{n(x_1)} \cdot \frac{n(x_2, x_3)}{n(x_2)} \cdot \frac{n(x_3, x_4)}{n(x_3)}
$$
**三元语法**（每个词只依赖前 2 个词）：
$$
p(x_1, x_2, x_3, x_4) = p(x_1)\,p(x_2 \mid x_1)\,p(x_3 \mid x_1, x_2)\,p(x_4 \mid x_2, x_3)
$$



循环神经网络（RNN）
**更新隐藏状态：**
$$
\mathbf{h}_t = \phi(\mathbf{W}_{hh}\mathbf{h}_{t-1} + \mathbf{W}_{hx}\mathbf{x}_{t-1} + \mathbf{b}_h)
$$
**输出：**

$$
\mathbf{o}_t = \mathbf{W}_{ho}\mathbf{h}_t + \mathbf{b}_o
$$掉 $\mathbf{W}_{hh}\mathbf{h}_{t-1}$ 这一项，就退化成普通的多层感知机（MLP）。
**困惑度（perplexity）**
**平均交叉熵** 衡量一个语言模型的好坏

$$
\pi = \frac{1}{n} \sum_{t=1}^{n} -\log p(x_t \mid x_{t-1}, \ldots)
$$
困惑度：历史原因 NLP 使用困惑度来衡量
$$
\text{PPL} = \exp(\pi)
$$
- 含义：模型平均每一步在多少个选项里犹豫
- 最好情况：$\text{PPL} = 1$，每次都以概率 1 预测对真实词
- 最差情况：$\text{PPL} \to \infty$，给真实词的概率趋近 0


梯度裁剪
$$
\mathbf{g} \leftarrow \min\left(1, \frac{\theta}{\|\mathbf{g}\|}\right)\mathbf{g}
$$
**两种情况：**
- 当 $\|\mathbf{g}\| \le \theta$ 时，$\frac{\theta}{\|\mathbf{g}\|} \ge 1$，取 $\min$ 得 1，梯度不变：$\mathbf{g} \leftarrow \mathbf{g}$
- 当 $\|\mathbf{g}\| > \theta$ 时，$\frac{\theta}{\|\mathbf{g}\|} < 1$，梯度被缩短，裁剪后长度为：
$$
\|\mathbf{g}'\| = \frac{\theta}{\|\mathbf{g}\|} \cdot \|\mathbf{g}\| = \theta
$$
> 结论：裁剪后梯度长度永远不超过 $\theta$，且方向不变。

RNN应用
<img src="/images/obsidian/d3fba8de4515.png" alt="Screenshot 2026-10-30 at 15.47.57.png" />
机器翻译
**编码器：不自回归。** 源句子（比如英文）是完整已知的，直接全部读进去，和文本分类一样，最后把整句信息压缩成隐藏状态 $\mathbf{c}$（上下文）。
**解码器：自回归。** 目标句子（比如中文）是要生成的，长度事先也不知道，所以只能一个词一个词地出：先生成第 1 个词，再把它喂回去生成第 2 个词……直到输出结束符 `<eos>`。
