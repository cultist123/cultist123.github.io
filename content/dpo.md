# DPO：偏好对齐的数学推导

> 参考：[知乎 · 猛猿《人人都能看懂的DPO数学原理》](https://zhuanlan.zhihu.com/p/721073733)
---
## 一、DPO 在做一件什么事
### 1.1 偏好对齐在训练流程中的位置
- **预训练**：大量文本/代码/数学数据 → base 模型
- **SFT**：指令微调 → 听懂指令，得到 $\pi_{sft}$
- **偏好对齐**：RLHF（Reward Model + PPO）→ 回答符合人类偏好
### 1.2 RLHF-PPO 的两个疑问
- 训 Reward Model 时已经在判断“什么回答好”，对齐模型又在做同一件事 → 能不能**跳过 Reward Model**，一步到位？
- PPO **显存大、超参多、训练不稳定** → 能不能**绕过强化学习**，用类似 SFT 的方式训？
### 1.3 DPO 的两点改进
-  不训练 Reward Model，直接用人类偏好数据训练对齐模型
-  不用强化学习，把优化目标一步步化简，最后像 SFT 一样训练

|              | RLHF-PPO                          | DPO              |
| ------------ | --------------------------------- | ---------------- |
| Reward Model | 要单独训练                             | 不需要              |
| 训练方式         | 强化学习（PPO）                         | 类似 SFT 的监督 loss  |
| 同时跑的模型       | Actor / Critic / Reward / Ref 4 个 | Policy + Ref 2 个 |
| 数据           | prompt，回答由 Actor 在线生成             | 离线标注好的偏好对        |


---
## 二、偏好对齐的总优化目标
不管 PPO 还是 DPO，总目标不变：
$$\max_{\pi_\theta}\ \mathbb{E}_{x\sim D,\ y\sim\pi_\theta(y|x)}\big[r_\phi(x,y)\big] - \beta\,\mathbb{D}_{KL}\big[\pi_\theta(y|x)\,\|\,\pi_{ref}(y|x)\big]$$
- $\pi_\theta$：正在训练的对齐模型
- $r_\phi$：训练好的奖励模型
- $\pi_{ref}$：参考模型，一般由 SFT 模型初始化
- $\beta$：KL 约束系数
- 和 day 6 的 InstructGPT objective 一样：**Reward − KL Penalty**（不含 PTX）

推导时始终记住两件事：**① 绕过奖励模型；② 尽量简化优化目标**

---
## 三、步骤 1：直接求出最优对齐模型
### 3.1 改写目标
$$
\begin{aligned}
&\max_{\pi}\ \mathbb{E}_{x\sim D,\,y\sim\pi}[r(x,y)] - \beta\,\mathbb{D}_{KL}[\pi(y|x)\,\|\,\pi_{ref}(y|x)] \\
=\ &\max_{\pi}\ \mathbb{E}_{x\sim D}\,\mathbb{E}_{y\sim\pi}\Big[r(x,y) - \beta\log\frac{\pi(y|x)}{\pi_{ref}(y|x)}\Big] \\
=\ &\min_{\pi}\ \mathbb{E}_{x\sim D}\,\mathbb{E}_{y\sim\pi}\Big[\log\frac{\pi(y|x)}{\pi_{ref}(y|x)} - \frac{1}{\beta}r(x,y)\Big] \\
=\ &\min_{\pi}\ \mathbb{E}_{x\sim D}\,\mathbb{E}_{y\sim\pi}\Big[\log\frac{\pi(y|x)}{\frac{1}{Z(x)}\pi_{ref}(y|x)\exp\big(\frac{1}{\beta}r(x,y)\big)} - \log Z(x)\Big]
\end{aligned}
$$
- 第 1→2 行：KL 的定义 $\mathbb{D}_{KL}[\pi\|\pi_{ref}] = \mathbb{E}_{y\sim\pi}\big[\log\frac{\pi}{\pi_{ref}}\big]$
- 第 2→3 行：除以 $\beta$ 并取反（max 变 min）
- 第 3→4 行：$\frac{1}{\beta}r$ 写成 $\log\exp(\frac{1}{\beta}r)$ 合并进 log，分子分母同乘 $\frac{1}{Z(x)}$，多出一项 $-\log Z(x)$
### 3.2 构造配分函数 Z(x)
- 想法：$\pi$ 是概率分布，如果分母也是概率分布，左边那项就是 **KL 散度**
- 把 $Z(x)$ 构造成 partition function（配分函数）：
$$Z(x) = \sum_{y}\pi_{ref}(y|x)\exp\Big(\frac{1}{\beta}r(x,y)\Big)$$
- 作用：对所有 $y$ 求和做**归一化**，让分母取值在 $[0,1]$，成为概率分布
- 关键性质：$Z(x)$ **只和 $x$ 有关，和要优化的 $\pi$ 无关**
- 把分母定义成一个分布：
$$\pi^{*}(y|x) = \frac{1}{Z(x)}\pi_{ref}(y|x)\exp\Big(\frac{1}{\beta}r(x,y)\Big)$$
### 3.3 得到显式解
- 代回后目标变成：
$$\min_{\pi}\ \mathbb{E}_{x\sim D}\Big[\mathbb{D}_{KL}\big(\pi(y|x)\,\|\,\pi^{*}(y|x)\big) - \log Z(x)\Big]$$
- $Z(x)$ 与 $\pi$ 无关，可以忽略；KL 在两个分布相等时最小 → 显式解：
$$\pi_{r}(y|x) = \frac{1}{Z(x)}\pi_{ref}(y|x)\exp\Big(\frac{1}{\beta}r(x,y)\Big)$$
- 下标 $r$：这是**固定某个奖励函数 $r$** 时的最优解
- 实际训练用的是最优奖励模型 $r^{*}$，对应最优对齐模型 $\pi^{*}$，关系不变：
$$\pi^{*}(y|x) = \frac{1}{Z(x)}\pi_{ref}(y|x)\exp\Big(\frac{1}{\beta}r^{*}(x,y)\Big)$$
---
## 四、步骤 2：跳过奖励模型的训练
### 4.1 显式解为什么不能直接用
- $Z(x)$ **很难估计**：每个 prompt 要采样足够多的回答，代价太高
- 显式解里**仍然需要奖励函数 $r$**，没达到省掉 Reward Model 的目标
### 4.2 反解出奖励函数
$$r^{*}(x,y) = \beta\log\frac{\pi^{*}(y|x)}{\pi_{ref}(y|x)} + \beta\log Z(x)$$
- 核心思路：用 $\pi^{*}$ 表示 $r^{*}$ → 代入**奖励模型的训练目标** → 表面上在训奖励模型，实际上**直接训出了对齐模型**
### 4.3 两种偏好标注方式

| 方式 | 数据格式 | 希望奖励模型做到 | 对应统计模型 |
|---|---|---|---|
| 成对（K=2） | `<prompt x, chosen y1, reject y2>` | chosen 得分高于 reject | BT（Bradley-Terry） |
| 多回答（K>2） | `<prompt x, y1, ..., yK>` + 人工排序 $\tau$ | 真值排序 $\tau$ 的总得分高于其他任何排序 | PT（Plackett-Luce） |
- ChatGPT 在 K>2 时把回答拆成两两 pair，和 K=2 统一
- DPO 把**整个排序**当成一条数据，所以 K=2 和 K>2 分开推导
### 4.4 BT 模型：只生成 2 个回答
- BT 模型（1952）：建模成对数据的相对优势，常用于体育比赛、市场研究
$$P(y_1 \succ y_2) = \frac{e^{\lambda_{y_1}}}{e^{\lambda_{y_1}} + e^{\lambda_{y_2}}}$$
- $\lambda$ 是**强度参数**（类比：两支球队过往的胜率）→ 偏好对齐里就是奖励模型的分数：
$$P(y_1 \succ y_2 \mid x) = \frac{\exp[r(x,y_1)]}{\exp[r(x,y_1)] + \exp[r(x,y_2)]}$$
- 数据集 $D = \{x^{i}, y_{w}^{i}, y_{l}^{i}\}_{i=1}^{N}$（$w$ = chosen，$l$ = reject），希望 chosen 打败 reject 的期望概率最大：
$$
\begin{aligned}
L_{R}(r_\phi, D)
&= -\mathbb{E}_{(x,y_w,y_l)\sim D}\big[\log P(y_w \succ y_l \mid x)\big] \\
&= -\mathbb{E}\Big[\log\frac{\exp[r(x,y_w)]}{\exp[r(x,y_w)] + \exp[r(x,y_l)]}\Big] \\
&= -\mathbb{E}\Big[\log\frac{1}{1 + \exp\big(-(r(x,y_w) - r(x,y_l))\big)}\Big] \\
&= -\mathbb{E}_{(x,y_w,y_l)\sim D}\Big[\log\sigma\big(r(x,y_w) - r(x,y_l)\big)\Big]
\end{aligned}
$$
- 最后一行就是 InstructGPT 里**奖励模型的 loss**：InstructGPT 直接给出，这里是从 BT 模型推出来的
- 把 $r^{*} = \beta\log\frac{\pi^{*}}{\pi_{ref}} + \beta\log Z(x)$ 代入：两项相减，**$\beta\log Z(x)$ 正好抵消**
- 把 $\pi^{*}$ 换成待训练的 $\pi_\theta$ → **DPO loss**：
$$L_{DPO}(\pi_\theta;\pi_{ref}) = -\mathbb{E}_{(x,y_w,y_l)\sim D}\Big[\log\sigma\Big(\beta\log\frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \beta\log\frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\Big)\Big]$$
- loss 里只剩 $\pi_\theta$ 和 $\pi_{ref}$ → 不需要 Reward Model，像 SFT 一样直接训
### 4.5 PT 模型：生成 K（K>2）个回答
- $\tau$：人工标注的真值排序（偏好从高到低），$\tau(k)$ 是排第 $k$ 的回答
$$P(\tau \mid y_1,\dots,y_K, x) = \prod_{k=1}^{K}\frac{\exp[r(x, y_{\tau(k)})]}{\sum_{j=k}^{K}\exp[r(x, y_{\tau(j)})]}$$
- 直观理解：
  - 第 1 名 $\tau_1$ 的得分在 $\tau_1 \sim \tau_K$ 中占大头
  - 第 2 名 $\tau_2$ 的得分在 $\tau_2 \sim \tau_K$ 中占大头
  - 依此类推
- 用 $\pi^{*}$ 表示 $r^{*}$（$Z(x)$ 在分子分母中抵消），再换成 $\pi_\theta$：
$$L_{DPO}(\pi_\theta;\pi_{ref}) = -\mathbb{E}_{\tau,\,y_1,\dots,y_K,\,x\sim D}\left[\log\prod_{k=1}^{K}\frac{\exp\Big(\beta\log\frac{\pi_\theta(y_{\tau(k)}|x)}{\pi_{ref}(y_{\tau(k)}|x)}\Big)}{\sum_{j=k}^{K}\exp\Big(\beta\log\frac{\pi_\theta(y_{\tau(j)}|x)}{\pi_{ref}(y_{\tau(j)}|x)}\Big)}\right]$$
---
## 五、推导过程小结
- 总目标：已知 $r$，找使 $\mathbb{E}[r] - \beta\,\mathbb{D}_{KL}[\pi\|\pi_{ref}]$ 最大的 $\pi$
- 求显式解：构造 $Z(x)$，把目标变成 KL → $\pi^{*} = \frac{1}{Z(x)}\pi_{ref}\exp(\frac{1}{\beta}r^{*})$
- 反解奖励：$r^{*} = \beta\log\frac{\pi^{*}}{\pi_{ref}} + \beta\log Z(x)$
- 代入奖励模型 loss：成对用 BT，多回答用 PT；$Z(x)$ 抵消，只剩 $\pi_\theta$ 和 $\pi_{ref}$
> 从 RLHF 总目标求出最优策略的显式解 → 反解成奖励 $r = \beta\log\frac{\pi}{\pi_{ref}} + \beta\log Z$ → 代入 BT / PT 的奖励模型 loss，$Z(x)$ 抵消 → 训“奖励模型”就等于直接训对齐模型，不需要 Reward Model 和 PPO。

## DPO 的 Objective

$$
\mathcal{L}_{DPO}(\pi_\theta;\pi_{ref})=-\mathbb{E}_{(x,y_w,y_l)\sim D}\left[\log\sigma\left(\beta\log\frac{\pi_\theta(y_w\mid x)}{\pi_{ref}(y_w\mid x)}-\beta\log\frac{\pi_\theta(y_l\mid x)}{\pi_{ref}(y_l\mid x)}\right)\right]
$$
可以直接记成：
$$
-\log\sigma\big(\text{chosen 的隐式奖励}-\text{reject 的隐式奖励}\big)
$$
- **Policy → 被训练的模型**：$\pi_\theta$，相当于 PPO 里的 Actor，但不需要在线生成 response。
- **Reference Model → 做约束**：$\pi_{ref}$，冻结的 SFT 模型，作用和 PPO 里的 KL penalty 一样。
- **隐式奖励（implicit reward）**：$\beta\log\frac{\pi_\theta(y|x)}{\pi_{ref}(y|x)}$，论文标题 *Your Language Model is Secretly a Reward Model* 就是这个意思。
- **没有 Reward Model 和 Critic**：和 day 6 的 PPO 四个模型相比，只剩 Policy + Ref 两个。
- **$\beta$**：越大越不允许偏离 $\pi_{ref}$，对应 PPO 里的 `kl_ctl`。
