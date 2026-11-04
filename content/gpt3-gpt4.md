# GPT-3 与 GPT-4：Few-shot 与模型演进

GPT3
动机： 
- 延续GPT2的思想，继续做大做强。
- 人类在做一个语言任务时，只要给几个例子就可以。但是传统Bert，GPT1，还需要成千上万的下游任务的例子。
- 能否通过在Prompt里给模型提供几个例子，提升模型性能。（Few-shot）
<img src="/images/obsidian/a220e5dbc2b1.png" alt="Screenshot 2026-11-02 at 13.55.51.png" width="425" />
微调就是给例子

gpt3模型修改
稀疏注意力机制,每个token不和他前面所有的token计算注意力,只选择部分的
<img src="/images/obsidian/4b188b5cd738.png" alt="Screenshot 2026-11-02 at 13.57.38.png" />
gpt3训练数据
<img src="/images/obsidian/d275d19248d6.png" alt="Screenshot 2026-11-02 at 13.58.20.png" />
 
 gpt3模型效果
<img src="/images/obsidian/64ebc930575b.png" alt="Screenshot 2026-11-02 at 13.59.51.png" width="700" />few-shot好于别的

gpt4
多模态,输入是文本和图片,输出是文字
GPT4透漏出来的见解
模型的能力是在预训练的时候获得的，RLHF只是和人类意识对齐。并不能提高模型表现。如果RLHF做的不好，还可能破坏模型原有的能力。

