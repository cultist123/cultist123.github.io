# LayerNorm 与 RMSNorm：原理与实现

- Norm的作用：因为梯度的值与X相关，X过大或者过小会导致梯度爆炸或梯度消失。所以需要将标准差变为1的归一化。
- RMSNorm：与传统Norm相比少了均值的相关计算，能节省计算开销同时效果不错。是Meta在llama中使用到的。
### 1. LayerNorm 回顾
对每个 token 自己的 $D$ 个特征做两件事：

$$y = \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} \odot \gamma + \beta$$

1. **减均值**（re-centering）：把中心移到 0
2. **除以标准差**（re-scaling）：把尺度变成 1
最后用可学习的 $\gamma$、$\beta$（都是 $D$ 维）调回模型需要的尺度和偏移。
### 2. RMSNorm
**只做第 2 步，去掉减均值，也去掉 $\beta$：**

$$y = \frac{x}{\text{RMS}(x)} \odot \gamma, \qquad \text{RMS}(x) = \sqrt{\frac{1}{D}\sum_i x_i^2 + \epsilon}$$

- RMS 是均方根，衡量这个向量的数值整体有多大

|         | LayerNorm        | RMSNorm       |
| ------- | ---------------- | ------------- |
| 操作      | 先平移到以 0 为中心，再缩放  | **不平移**，只整体缩放 |
| 各数之间的比例 | 改变               | 完全不变          |
| 可学习参数   | $\gamma$、$\beta$ | 只有 $\gamma$   |
### 3.手撕RMS Norm
``` python
import torch
import torch.nn as nn

class RMSNorm(nn.Module):
def __init__(self,dim:int,eps:float=1E-5):
super().__init__()
self.dim=dim
self.eps=eps
self.weight=nn.Parameter(torch.ones(dim))

def _norm(self,x):
return x * torch.rsqrt(x.pow(2).mean(-1,keepdim=True)+self.eps)
def forward(self,x):
return self.weight*self._norm(x.float()).type_as(x)
```
