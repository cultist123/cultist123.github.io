# GPT 与 BERT：预训练、微调与 Prompt

## GPT-1：预训练与微调
nlp每个模型都需要大量标注,模型不能复用
借鉴CV领域预训练模型,下游任务微调的思路
没有像ImageNet那样的标注数据——语言模型自回归训练模型:输入一段文本,让语言模型根据文本生成下一个字,GPT1 decoder- only,因为不需要参考encoder的参数输出,就去掉了cross attention部分了,text prediction进行自回归,task classifier进行微调 
<img src="/images/obsidian/a9bba9984fdc.png" alt="Screenshot 2026-11-01 at 19.27.06.png" width="369" />
预训练：
语言模型似然函数：
$$L_1(u) = \sum_i \log P(u_i \mid u_{i-k}, \ldots, u_{i-1}; \Theta)$$
(最大化整体奖励,最大化似然函数)
如何得到下一个词的概率：
$h_0 = UW_e + W_p$　　：$U$ 为输入Token，$W_e$ 为Embedding矩阵，$W_p$ 为位置编码
$h_l = \text{decoder\_block}(h_{l-1}) \quad \forall l \in [1, n]$
$P(u) = \text{softmax}(h_n W_e^T)$
embedding 矩阵和最后的分类头线性层共享权重,字典长度转化为隐藏层维度,转置后就能把输出的隐藏层转化为字典
微调:
给文本加上一些特殊的token让模型进行具体的任务微调,看见这个token就知道下来不是训练是做任务了,四种具体微调任务
<img src="/images/obsidian/4218c7e4f0c6.png" alt="Screenshot 2026-11-01 at 19.37.09.png" width="587" />
最后加一个双分类,三分类线性层

## BERT：双向表示与下游任务
gpt-1让我们看到了预训练+微调的可能性
bert提出gpt-1的注意力是单向的
**BERT的研究动机：**
• 双向注意力可以看到序列里所有token的信息，这样对于上下文理解会更加全面，应该会取得更好的效果。
**参数**
L：层数
H：Embedding和隐藏层特征维度
A：注意力头的个数
• BERT_base:(L=12,H=768,A=12) 总参数量为110M
• BERT_large(L=24,H=1024,A=16)总参数量为340M
因为数据集大4倍,所以参数大3倍 
**流程:**
• 预训练+微调
• 不同任务的统一结构
下游任务中的标记数据对所以参数进行微调,每个下游任务有微调模型
**BERT的输入和输出:**
可解决两类问题
• 序列级别的问题
• Token级别的问题
<img src="/images/obsidian/374b23dc3a0e.png" alt="Screenshot 2026-11-01 at 20.34.41.png" width="463" />
\<cls>占位符,代表了整个序列的全局信息,利用这个信息加个分类头就可以对序列(单序列或多序列)进行分类
\<sep>序列的分隔符,用来隔开两个序列, 每个token位置最后一层的输出向量就代表了这个token结合上下文后的表示信息,加个分类头进行NER分类头,对所以token都共享一个分类头
NER = 命名实体识别（Named Entity Recognition）

句子分类：[CLS] 这 部 电 影 太 好 看 了
            ↓
         分类头 → 好评
NER：     [CLS] 马  云  在  杭  州 ...
                 ↓   ↓   ↓   ↓   ↓
               分类头（每个字各过一次）
                人名 人名 无  地名 地名

不同任务的区别，只在于**拿哪个输出去分类**：
- **序列级别**（整句一个答案，如情感分析"这句话是好评还是差评"）：BERT 在句子开头放了一个特殊符号 `[CLS]`，它的输出向量代表整句话的意思，拿它接分类头 → 输出"好评/差评"
- **Token 级别**（每个字一个答案，如 NER）：拿**每个字**的输出向量分别接分类头 → 每个字输出一个标签
"**预训练 + 微调**"：BERT 先在海量文本上预训练好，做具体任务时只需要用少量标注数据，把分类头连同 BERT 一起稍微训练一下（微调），效果就很好。

token embedding代表token的原始信息,是可以进行学习参数,没有上下文信息
segment embedding用于区分每个token属于那个序列的embedding,每个序列共享一个embedding,可以进行学习
position embedding 不同于transformer的sin cos 这里的编码也是可以学习的参数

预训练Bert
两种任务
• Token级别任务：遮蔽语言模型
随机将输入token中的一些进行mask替换为\[MASK] token,根据这个输出加个分类头,预测出原始被遮蔽的token id,填空题,能让模型更好的提取token级别的上下文信息,防止他看见mask才提取上下文信息,所以在训练时先随机选15%的token做最终的token id(要预测的位置)预测,15%的token里80%的概率进行masktoken 10%概率随机替换为其他token,10%概率保持原有不变,用id的原因是最后进行多分类问题找出id
• 序列级别任务：下一句预测
问答,推理,是理解两个句子的关系,任务为判断两个任务是否是连续的,采集两个连续的句子作为正样本,两个不连续的句子作为负样本,提取\[cls] token作为最后一层的输出向量加一个分类头,进行二分类判断
对于预训练数据，BERT使用了BooksCorpus（800万个单词）和英文的Wikipedia（25亿个单词）。

Bert微调
两个序列,在序列之间加\[SEP] token,并且设置合适的segment embedding
根据不同的任务,利用输出不同位置的输出,加上分类头来进行下游任务,序列级别提取\[CLS] token输出,token级别就提取每个token的输出
微调时,只有分类头是全新的随机初始化的,其他参数包括encoder和embedding都是预训练好的,但是在微调时候要继续特别小幅的调整(学习率 5e-5、3e-5 或 2e-5，batch size 16 或 32，训练 2～4 轮。学习率很小、轮数很少，所以参数只是在预训练的基础上小幅调整。),进行全参数微调

Bert的意义
• 概念简单，功能强大 11个任务获得成果都取得当时最好
• NLP领域现象级的预训练模型,因为只要很少的标注数据,就能达到很好的效果(几百个)

## GPT-2：Prompt 与多任务学习
动机
• GPT1 和 Bert 将预训练模型引入了NLP，但是下游任务仍然需要收集一部分数据，进行微调。
• GPT2 希望通过预训练模型可以解决所有下游任务。不需要进行微调
怎么解决下游问题？
• 在GPT1，在微调时引入起始符，分割符，结束符来让模型进行下游任务。
  p(output|input)
• GPT2不进行微调，只能用预训练时见过的token，所以自然的引入了Prompt。
  p(output|input,task)
情感分类例子：
GPT1：\<start>今天这家餐厅的服务真的很棒！\<extract>
GPT2：判断下边这个句子的情绪是正面还是负面的：今天这家餐厅的服务真的很棒！
训练修改
1. 上下文长度从512，扩展到1024。
2. BatchSize到512。
3. 用了Reddit里优质的网页，800万文本，40GB文字。
模型效果
<img src="/images/obsidian/a1eeb945f1a7.png" alt="Screenshot 2026-11-01 at 21.23.56.png" width="505" />
发现scaling law
gpt-2之前任务类型要设计成模型结构,现在变成了prompt直接传入模型
