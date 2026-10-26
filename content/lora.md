# LoRA

<img src="/images/ai/image-20261021143308123.png" alt="image-20261021143308123" style="zoom:50%;" />

#### 核心5 个公式

$$
W = W_0 + \Delta W
$$

$$
\Delta W = BA
$$

$$
h = W_0x + BAx
$$

$$
\operatorname{rank}(BA) \le r
$$

$$
W' = W_0 + BA
$$

#### 1. Problem

Full Fine-tuning 需要更新整个模型，导致 **trainable parameters、gradient、optimizer states 和 task checkpoint 都很大**。LoRA 只训练少量旁路参数,并冻结大模型参数完成模型适配。

#### 2. Core Idea

Fine-tuning：
$$
W = W_0 + \Delta W
$$
LoRA 假设真正的更新 $\Delta W$ 具有 **low intrinsic rank**，因此：
$$
\Delta W = BA
$$
其中：
$$
B \in \mathbb{R}^{d \times r}, \quad A \in \mathbb{R}^{r \times k}
$$
并且：
$$
r \ll d,k
$$
$W_0$ 被冻结，只训练 $A,B$。

#### 3. Training

$$
h = W_0x + BAx
$$

- $W_0$：Frozen，但仍参与 forward
- $A,B$：Trainable
- 减少 trainable parameters、gradient、optimizer states 和 task checkpoint

#### 4. Rank

$$
\operatorname{rank}(BA) \le r
$$

$r$ 表示 LoRA 最多可以使用多少个独立方向修改模型。论文发现很小的 $r$ 也能取得很好效果，说明真正重要的 adaptation directions 可能很少。

#### 5. Inference

训练完成后可以 merge：
$$
W' = W_0 + BA
$$
推理时：
$$
h = W'x
$$
因此不需要额外的 LoRA 推理层。

#### 6. 结论

LoRA **不是分解 pretrained weight $W_0$**，而是对任务更新量 $\Delta W$ 做低秩表示：
$$
\Delta W = BA
$$
核心思想：$W_0$ 很复杂，不代表新任务需要的 $\Delta W$ 也必须很复杂。