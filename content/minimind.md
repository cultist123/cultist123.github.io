# MiniMind：模型实现与张量数据流

## 架构与模块

今天主要在动手实现大模型,读的论文已经很多了[视频](https://www.bilibili.com/video/BV1T2k6BaEeC/?spm_id_from=333.788.player.switch&vd_source=733134f9510b49487c0246aed03c359a&p=9)
- minimind-dense 架构:使用decoder - only, 与GPT-3对比1.GPT3使用LN,minimid使用rmsnorm归一化,更节约成本,2.用SwiGLU代替ReLU,3.都使用RoPE旋转位置编码
- GQA:与transformetransformer的区别在于,先进行了rmsnorm层归一化,再在自注意力后进行位置编码rope
- FFN:rmsnorm归一化,经过两个linear线性层输入张量升维,其中一个经过SiLU激活(提供非线性),然后逐元素相乘,相乘后经过linear降维,dropout防止过拟合,和原始输入进行残差链接之后输出.
- tokenizer:解码,与词表配合
<img src="/images/obsidian/54c927cb5358.png" alt="Pasted image 20261028163613.png" />

## GQA、残差与 FFN

<img src="/images/obsidian/5556f6e5ea6d.png" alt="Pasted image 20261030210553.png" width="516" />
GQA,因为多头注意力,存很多份QKV很占显存,多个Q共享一组K和V,Linear是进行多头拼接的
ResNet
假设某个完美的 function 是 $H(x) = x$
- **没有残差**：$H(x) = F(x)$，就需要费力拟合 $x$
- **有残差**：$H(x) = F(x) + x$，只需要 $F(x) = 0$
**残差在梯度上的好处：**

$$  
\frac{dL}{dx} = \frac{dL}{dH} \times \frac{dH}{dx} = \frac{dL}{dH} \cdot \left( \frac{dF}{dx} + 1 \right)  
$$
可以有效缓解梯度消失问题。
FFN
升维就是把一个抽象的信息更细化,2个维度转化为6个维度进行表示
SiLU
通用逼近定理,引入非线性,
或者电路的逻辑门控电路,进行了逻辑的嵌套
经过门控电路是对信息进行过滤
**门控**：用一路信号（经激活函数生成 0~1 的"门"）逐元素乘另一路信号，动态决定信息放行多少，即 `y = act(W_g·x) ⊙ (W_v·x)`。


#### 手撕GQA&FFN
```python 
def repeat_kv(x:torch.Tensor,n_rep:int)->torch.Tensor:
    bs,slen,num_key_value_heads,head_dim = x.shape
    if n_rep == 1:
        return x
    return (
        x[:,:,:,None,:]
        .expand(bs, slen, num_key_value_heads, n_rep, head_dim)
        .reshape(bs, slen, n_rep * num_key_value_heads, head_dim)
    )
class Attention(nn.Module):
    def __init__(self, args:MokioMindConfig):
        super().__init__()
        self.num_key_value_heads = args.num_attention_heads if args.num_key_value_heads is None else args.num_key_value_heads
        assert args.num_attention_heads % self.num_key_value_heads == 0 
        # 计算每个key-value头对应的query头数量,必须是整数倍,不然报错
        self.n_local_heads = args.num_attention_heads
        self.n_local_kv_heads = self.num_key_value_heads
        self.n_rep = self.n_local_heads//self.n_local_kv_heads
        self.head_dim = args.hidden_size // args.num_attention_heads
        #投影层
    self.q_proj=nn.Linear(args.hidden_size,args.num_attention_heads*self.head_dim,bias=False)       self.k_proj=nn.Linear(args.hidden_size,self.num_key_value_heads*self.head_dim,bias=False)        self.v_proj=nn.Linear(args.hidden_size,self.num_key_value_heads*self.head_dim,bias=False)        self.o_proj=nn.Linear(args.num_attention_heads*self.head_dim,args.hidden_size,bias=False)
        self.attn_dropout=nn.Dropout(args.dropout)
        self.resid_dropout=nn.Dropout(args.dropout)
        self.dropout=args.dropout
        self.flash=hasattr(torch.nn.functional,'scaled_dot_product_attention') and args.flash_attention
    def forward(
    self,
    x: torch.Tensor,
    position_embdding: Tuple[torch.Tensor, torch.Tensor],
    past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    use_cache=False,
    attention_mask: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    #投影:linear计算q,k,v
        bsz, seq_len, _ = x.shape
        xq,xk,xv=self.q_proj(x),self.k_proj(x),self.v_proj(x)
    #把输入拆分成多个头,用view
    #现在是512维,有8个头,所以每个头拆成64维
        xq = xq.view(bsz, seq_len, self.n_local_heads, self.head_dim)
        xk = xk.view(bsz, seq_len, self.n_local_kv_heads, self.head_dim)
        xv = xv.view(bsz, seq_len, self.n_local_kv_heads, self.head_dim)
    #q和k,使用RoPE
        cos, sin = position_embdding
        xq,xk=apply_rotary_pos_emb(xq,xk,cos[:seq_len],sin[:seq_len])
    #对于k和v,使用repeat(注意kv cashe)
        if past_key_value is not None:
            xk=torch.cat([past_key_value[0],xk],dim=1)
            xv=torch.cat([past_key_value[1],xv],dim=1)
        past_key_value = (xk,xv)if use_cache else None
        xq,xk,xv=(
            xq.transpose(1,2),
            # [bsz, n_local_heads, seq_len, head_dim]
            repeat_kv(xk, self.n_rep).transpose(1,2),
            repeat_kv(xv, self.n_rep).transpose(1,2),
        )
    #进行attention计算,q@k^T/sqrt(d)
        if self.flash and seq_len > 1 and (attention_mask is None or torch.all(attention_mask==1)):
            attn_mask=(
                None
                if attention_mask is None 
                else attention_mask.view(bsz, 1, 1, -1).expand(bsz, self.n_local_heads, seq_len, -1).bool()
            )
            output = F.scaled_dot_product_attention(
                xq, xk, xv, attn_mask=attn_mask, dropout_p=self.dropout if self.training else 0.0, is_causal=True
            )
        else:
            scores = (xq@xk.transpose(-2,-1)) / math.sqrt(self.head_dim)
            scores = scores+torch.triu(
                torch.full((seq_len,seq_len), float('-inf'), device=scores.device), 
                diagonal=1
                ).unsqueeze(0).unsqueeze(0)
    #最后拼接头,输出投影,返回
            if attention_mask is not None:
                extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
                extended_attention_mask = (1.0 - extended_attention_mask) * -1e9
                scores = scores + extended_attention_mask
            scores = F.softmax(scores.float(),dim=-1).type_as(xq)
            scores = self.attn_dropout(scores)
            output = scores @ xv
    #[bsz, seq_len, n_local_heads*head_dim]
        output=output.transpose(1,2).reshape(bsz, seq_len, -1)
        output=self.resid_dropout(self.o_proj(output))
        return output, past_key_value
```

```python
class FeedForward(nn.Module):
    #初始化
    def __init__(self,args:MokioMindConfig):
        super().__init__()
        if args.intermediate_size is None:
            intermediate_size = int(args.hidden_size * 8/3)
            args.intermediate_size = 64*((intermediate_size + 64-1) // 64)
    #升维
        self.up_proj = nn.Linear(args.hidden_size, args.intermediate_size, bias=False)
    #降维
        self.down_proj = nn.Linear(args.intermediate_size, args.hidden_size, bias=False)
    #门控
        self.gate_proj = nn.Linear(args.hidden_size, args.intermediate_size, bias=False)
    #dropout
        self.dropout = nn.Dropout(args.dropout)
    #激活函数
        self.act_fn = ACT2FN[args.hidden_act]
    def forward(self, x):  
        return self.dropout(self.down_proj(self.up_proj(x) * self.act_fn(self.gate_proj(x))))
```
---

## 一次前向传播的数据流

数据流动
<img src="/images/obsidian/54c927cb5358.png" alt="Pasted image 20261028163613.png" width="599" />

4. 在每次的向前传播中
    1. 文本经 tokenizer 得到 [2,10] 的 token id，embedding 为 [2,10,512]，进行一次 dropout 张量不变
    2. position_embedding 是 (cos, sin) 两个 [10,64] 的元组
    3. 然后进入 Block 层
        1. hidden_state 为 [2,10,512]，残差保存和 RMSNorm 不改变形状
        2. 进入 Attention
            1. 进行投影，让 q 投影为 attention_head*head_dim
            2. k 和 v 投影为 kv_head*head_dim
            3. 然后进行重塑，将最后的那一维度拆开成 [nhead,head_dim]
            4. 之后应用旋转位置编码，逐元素相乘相加，q 和 k 仍为 [2,10,8,64] 和 [2,10,2,64]
            5. 将 q 进行 transpose，用于计算 seq_len*seq_len，即转换为 [2,8,10,64]
            6. 然后 repeat k 和 v，复制四次再 transpose 变为 [2,8,10,64]
            7. 注意力分数计算，k 后两位交换，和 q 相乘再除以 √64：`(2, 8, 10, 64) @ (2, 8, 64, 10)` -> `(2, 8, 10, 10)`
            8. 应用因果掩码，把当前 token 之后的都变为 -inf（有 pad 时再加 attention_mask）
                - `causal_mask`: `(10, 10)`
                - `scores = scores + causal_mask.unsqueeze(0).unsqueeze(0)`: `(2, 8, 10, 10)`
            9. softmax 变化，之后再与 v 相乘 `(2, 8, 10, 10) @ (2, 8, 10, 64)` -> `(2, 8, 10, 64)`
            10. transpose，reshape 变回 [2,10,512]，再经 o_proj 输出
        3. 残差处理、RMSNorm 后进入 FFN 层
            1. 输入 [2,10,512]
            2. gate 和 up 并行升维，按 8/3 比例变为 [2,10,1408]
            3. gate 经 SiLU 处理，变为门控
            4. gate*up，维度不变为 [2,10,1408]
            5. down 降维 [2,10,512]
        4. 继续残差处理，然后进入下一个 layer
    4. layer 处理完后，hidden_state 依旧为 [2,10,512]，再经最终 RMSNorm
    5. 向整个词表进行映射 `(2, 10, 512)` -> `(2, 10, 6400)`，输出 logits
    6. 取最后位置的 logits，softmax 后按概率选出下一个 token，拼回序列继续生成

## 训练阶段

pretrain是暴力填鸭,知识填充给了模型
训练阶段=pretrain+SFT+对齐
<img src="/images/obsidian/b93372a05986.png" alt="Screenshot 2026-11-01 at 22.33.53.png" width="404" />
