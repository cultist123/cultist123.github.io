# RLHF-PPO：四个模型、GAE 与训练代码

RLHF - PPO
最早是强化学习中的 **Actor-Critic / Policy Gradient** 思路  
↓  
**Schulman et al., 2017 — Proximal Policy Optimization Algorithms (PPO)**  
提出 PPO，使用 **Policy + Value Function** 进行更稳定的策略优化  
↓  
**Ziegler et al., 2019 — Fine-Tuning Language Models from Human Preferences**  
把 **PPO + Reward Model + KL to Reference Policy** 用到语言模型的人类偏好优化中  
↓  
**Ouyang et al., 2022 — InstructGPT**  
将这套方法发展成现代 LLM RLHF 的典型形式：

**SFT Actor + Frozen Reference Model + Reward Model + Critic/Value Model + PPO**
可以简化记成：
**Actor-Critic → PPO → PPO + Reward Model + Reference/KL → InstructGPT-style RLHF**
其中：
- **Actor + Critic**：来自 Actor-Critic / PPO
- **Reward Model**：来自基于人类偏好的 Reward Learning
- **Reference Model + KL**：Ziegler et al., 2019 中已经明确使用
- **SFT Model 初始化 Actor 和 Reference、Reward Model 初始化 Critic**：InstructGPT 中采用

## RLHF-PPO 原理与源码
<img src="/images/obsidian/21848cc64d66.png" alt="Pasted image 20261102220708.png" />

> 参考：[知乎 · 猛猿《图解大模型RLHF系列之：人人都能看懂的PPO原理与源码解读》](https://zhuanlan.zhihu.com/p/677607581)
---
## 一、强化学习基础
<img src="/images/obsidian/1fe1c3d05efe.png" alt="Pasted image 20261102204811.png" width="511" />
### 1.1 基本要素
- **智能体 Agent** 与 **环境 Environment** 交互
- **状态空间 S**：环境所有可能状态
- **动作空间 A**：智能体所有可能动作
- **奖励 R**：智能体在某状态下获得的奖励
- 交互循环：观测 $S_t, R_t$ → 采取 $A_t$ → 环境变为 $S_{t+1}$，得到 $R_{t+1}$
- **目标**：学到一个策略，根据当前状态和奖励选出最佳动作
### 1.2 价值函数（简化版）
$$V_t = R_t + \gamma V_{t+1}$$
- $V_t$：t 时刻总收益（即时 + 未来）
- $R_t$：t 时刻即时收益
- $\gamma$：折扣因子，控制未来收益计入当下的比重
---
## 二、强化学习在 NLP 中的对应关系
<img src="/images/obsidian/ad2cf29e6e9c.png" alt="Pasted image 20261102204825.png" />

| RL 概念 | NLP / LLM 中的含义 |
|---|---|
| 智能体 | 语言模型本身 |
| 动作 $A_t$ | t 时刻生成的 token |
| 动作空间 | 词表 |
| 状态 $S_t \to S_{t+1}$ | 上文 → 上文 + 新 token |
| 收益 $R_t, V_t$ | 对“人类喜好”的衡量 |

**常见疑问**
- 下标问题：严格说 $A_t$ 对应 $R_{t+1}$，这里为了贴合代码统一写成同一下标，不必纠结
- $A_t$ 由语言模型产生；$R_t$、$V_t$ 由**另外两个模型**产生
- 参数更新时机：**不是**每看到一个收益就更新，而是等完整 response 生成、积累足够数据后再更新
- $R_t$：生成当前 token 的即时收益
- $V_t$：从当前 token 到 response 结束的**期望**总收益（未来的 token 还没生成，只能预估）
---

## 三、RLHF-PPO 的四个模型
<img src="/images/obsidian/3aff734d29e8.png" alt="Pasted image 20261102204835.png" width="576" />

| 模型 | 作用 | 是否训练 | 初始化 |
|---|---|---|---|
| **Actor**（演员） | 目标语言模型，生成 response | ✅ 训练 | SFT 模型 |
| **Critic**（评论家） | 预估总收益 $V_t$ | ✅ 训练 | Reward Model（deepspeed-chat 做法） |
| **Reward**（奖励） | 计算即时收益 $R_t$ | ❄️ 冻结 | RW 阶段训好的奖励模型 |
| **Reference**（参考） | 约束 Actor，防止“训歪” | ❄️ 冻结 | SFT 模型 |

- Critic + Reward + Ref 共同构成“奖励-loss 计算体系”，算出 loss 用来更新 Actor 和 Critic
- 4 个模型同时在硬件上跑 → 显存压力大
### 3.1 Actor：负责生成并更新策略
- 输入 prompt → 生成 response → “prompt + response”送入奖励-loss 体系 → 算 loss 更新 Actor
<img src="/images/obsidian/26321fc481ea.png" alt="Pasted image 20261102204851.png" width="499" />
### 3.2 Reference：用 KL 约束防止训歪
- 目标：Actor 既符合人类喜好，又不要离 SFT 模型太远（输出分布相似）
- 做法：
  - Actor 生成 response，得到每个 token 的 `log_probs`
  - 把同一份“prompt + response”喂给 Ref，得到 `ref_log_probs`
  - 用 `ref_log_probs - log_probs` 衡量相似度
- 直觉：该值越大，说明 Ref 也认可 Actor 的输出，没训歪
- KL 视角：$KL[Actor \| Ref] \approx$ `log_probs - ref_log_probs`，越小越相似
- 写成 `ref - actor` 的形式，是因为后面奖励里是“$R_t$ 减去 KL”，带负号更直观
<img src="/images/obsidian/f18638e56fc9.png" alt="Pasted image 20261102204903.png" width="514" />
### 3.3 Critic：为什么要单独训练
<img src="/images/obsidian/1a7b28bac642.png" alt="Pasted image 20261102204914.png" width="395" />
- 真实总收益 $V_t$ 是“上帝视角”的，训练时拿不到，只能训一个模型去预测
- RLHF 既要提升**生成**符合人类喜好内容的能力（Actor），也要提升**判断**人类喜好的能力（Critic）
- 结构：与 Actor 相似的主干 + 最后一层 **Value Head**（线性层，输出单个标量 $V_t$）
### 3.4 Reward：为什么可以冻结
<img src="/images/obsidian/07491ac8f433.png" alt="Pasted image 20261102204933.png" width="420" />
- 它已在 RW 阶段专门训练过，可当作给出“客观值”的模型
- 即时收益在 token 生成后就能直接算出
- **为什么有了 $V_t$ 还要 $R_t$？**
  - t 时刻总收益有两种估计：
    1. Critic 直接预测的 $V_t$（全靠预测）
    2. $R_t + \gamma V_{t+1}$（含一项真实数据 $R_t$）→ **更接近真值**
  - 所以用 $R_t + \gamma V_{t+1}$ 作为 Critic 的学习目标（近似真实收益）
---
## 四、Loss 设计
两个 loss：
- **Actor loss**：Actor 是否生成了符合人类喜好的结果
- **Critic loss**：Critic 是否准确预测了人类喜好
### 4.1 Actor loss 的演进
#### (1) 直观版
$$actor\_loss = -V_t \log P(A_t|S_t)$$
- $V_t > 0$：正反馈 → 提高该 token 的概率
- $V_t < 0$：负反馈 → 降低该 token 的概率
- （实际是对 response 所有 token 求和/平均，公式中省略）
#### (2) 引入优势 Advantage
- 例子：王者中路走大龙路支援，Critic 预计拿 1 个人头，实际拿了 2 个 → 多出来的“甜头”就是优势
$$Adv_t = R_t + \gamma V_{t+1} - V_t$$
$$actor\_loss = -Adv_t \log P(A_t|S_t)$$
- 含义：实际收益 − 预期收益
#### (3) 重新设计 $R_t$（加入 KL 约束）
deepspeed-chat 的做法：
$$
R_t =
\begin{cases}
-kl\_ctl \cdot \log\dfrac{P(A_t|S_t)}{P_{ref}(A_t|S_t)}, & t \ne T \\[2mm]
-kl\_ctl \cdot \log\dfrac{P(A_t|S_t)}{P_{ref}(A_t|S_t)} + R_T, & t = T
\end{cases}
$$
- `kl_ctl`：缩放系数，默认 0.1
- 非最后位置：只看 Actor 是否遵守 Ref 约束
- 最后位置：KL 约束 + Reward Model 给出的分数
- 只在最后一位加奖励分的原因：RW 阶段就是用最后一个 token 位置的分数代表整条 prompt+response 的奖励
- 其他设计也可行，例如用所有 token 奖励的平均值替代最后一位
- reward_score 会被裁剪到 `[-clip_reward_value, clip_reward_value]`，默认 5
<img src="/images/obsidian/3072265fb33d.png" alt="Pasted image 20261102205103.png" width="373" />
#### (4) 重新设计优势：GAE
$$Adv_t = (R_t + \gamma V_{t+1} - V_t) + \gamma \lambda \, Adv_{t+1}$$
- $\lambda$：权衡当下与未来优势（RL 角度：平衡偏差与方差）
- 计算方法：最后时刻 $Adv_T = R_T - V_T$（未来项为 0），**从后往前动态规划**依次求出
- 同时得到实际收益：$returns_t = Adv_t + V_t$（用于 Critic loss）
#### (5) PPO-epoch：经验复用 + 新约束
**训练流程**
1. 准备一个 batch 的 prompts
2. Actor 生成 responses
3. prompt+response 送入 Critic / Reward / Ref，得到**经验（experiences）**
4. 用经验计算 loss，更新 Actor 和 Critic —— **同一批经验重复用 ppo_epochs 次**
**为什么复用**：收集经验要 4 个模型都推理一遍，很贵，只用一次太浪费
**问题**：复用期间 Actor 不和环境交互，只能“模拟”交互 → 要让更新中的 $Actor_{new}$ 不偏离产出经验的 $Actor_{old}$
**加入新旧策略比值**（去掉 log 涉及重要性采样）：
$$actor\_loss = -Adv_t \cdot \frac{P(A_t|S_t)}{P_{old}(A_t|S_t)}$$
**再加裁剪 clip**（如范围 0.8~1.2）：
$$actor\_loss = -\min\left(Adv_t \cdot r_t,\; Adv_t \cdot clip(r_t, 0.8, 1.2)\right), \quad r_t = \frac{P(A_t|S_t)}{P_{old}(A_t|S_t)}$$
- 超出范围时比值变为常数，loss 与 Actor 无关 → 相当于**停止更新**，保证稳定
<img src="/images/obsidian/30576e375fc9.png" alt="Pasted image 20261102205129.png" width="412" />
#### (6) Actor loss 小结
- ✅ 改造 $R_t$：引入 Ref 的 KL 约束
- ✅ 改造 $Adv_t$：GAE，兼顾当下和未来优势
- ✅ 经验复用 ppo_epochs 次：用 $Actor_{old}$ 约束 $Actor_{new}$
- ✅ clip：更新幅度超限就不更新
### 4.2 Critic loss
- 初始想法：
$$critic\_loss = (R_t + \gamma V_{t+1} - V_t)^2$$
- **实际收益优化**：用 $Adv_t + V_t$（即 returns）代替 $R_t + \gamma V_{t+1}$，信息更丰富
- **预估收益优化**：Critic 也在 ppo_epochs 中更新，用旧 Critic 的 `old_values` 给新 `values` 设定范围 `[old - cliprange_value, old + cliprange_value]`（默认 0.2）
- 最终：取未裁剪和裁剪后 MSE 的较大值，按 token 平均，再乘 0.5
- 注意：returns 中的 $Adv_t, V_t$ 来自**旧 Critic**（固定）；预估值随 ppo_epochs **变动**
---
## 五、核心代码速记（deepspeed-chat）
### compute_rewards：计算每个 token 的奖励
```python
kl = -kl_ctl * (log_probs - ref_log_probs)   # 每个位置的 KL 奖励
rewards = kl
start = prompts.shape[1] - 1                  # response 起点（prompt 已 padding，统一）
ends = start + action_mask[:, start:].sum(1) + 1  # 每条 response 终点不同
reward_clip = torch.clamp(reward_score, -clip_reward_value, clip_reward_value)
for j in range(batch_size):
    rewards[j, start:ends[j]][-1] += reward_clip[j]  # 只在最后一位加 RM 分数
```
### get_advantages_and_returns：GAE 倒推
```python
lastgaelam = 0
for t in reversed(range(start, length)):
    nextvalues = values[:, t+1] if t < length - 1 else 0.0
    delta = rewards[:, t] + gamma * nextvalues - values[:, t]
    lastgaelam = delta + gamma * lam * lastgaelam
    # 收集后反转得到 advantages
returns = advantages + values[:, start:]      # 实际收益
```
### actor_loss_fn：PPO-clip
```python
ratio = torch.exp((logprobs - old_logprobs) * mask)
pg_loss1 = -advantages * ratio
pg_loss2 = -advantages * torch.clamp(ratio, 1 - cliprange, 1 + cliprange)  # cliprange=0.2
pg_loss = torch.sum(torch.max(pg_loss1, pg_loss2) * mask) / mask.sum()
```
- 只有 `logprobs` 随 Actor 更新变化；`old_logprobs`、`advantages`、`mask` 固定
- 注意：loss 带负号，所以取 `max` 等价于公式里的 `-min`
### critic_loss_fn：value clip
```python
values_clipped = torch.clamp(values, old_values - cliprange_value, old_values + cliprange_value)
vf_loss1 = (values - returns) ** 2
vf_loss2 = (values_clipped - returns) ** 2
vf_loss = 0.5 * torch.sum(torch.max(vf_loss1, vf_loss2) * mask) / mask.sum()
```
### 整体训练伪代码
```python
actor, critic, reward, ref = initialize_models()
for batch in steps:
    exps = generate_experience(prompts, actor, critic, reward, ref)
    for _ in range(ppo_epochs):          # 同一批经验复用多次
        actor_loss  = cal_actor_loss(exps, actor)
        critic_loss = cal_critic_loss(exps, critic)
        actor.backward(actor_loss);  actor.step()
        critic.backward(critic_loss); critic.step()
```
---
## 六、默认超参速查

| 参数                  | 默认值 | 含义                 |
| ------------------- | --- | ------------------ |
| `kl_ctl`            | 0.1 | KL 奖励缩放系数          |
| `clip_reward_value` | 5   | RM 分数裁剪范围          |
| `cliprange`         | 0.2 | Actor 新旧策略比值裁剪     |
| `cliprange_value`   | 0.2 | Critic 新旧 value 裁剪 |
| `gamma`             | —   | 折扣因子               |
| `lam`               | —   | GAE 权衡因子           |
## 七、一句话总结
> Actor 生成 → Reward 打分 + Ref 算 KL 得到每个 token 的奖励 → Critic 估值 → GAE 倒推优势与 returns → 同一批经验复用 ppo_epochs 次，用 clip 约束 Actor 和 Critic 的更新幅度。

## 论文
### InstructGPT 的 PPO Objective
$$  
\operatorname{objective}(\phi)=\mathbb{E}_{(x,y)\sim D_{\pi_{\phi}^{RL}}}\left[r_{\theta}(x,y)-\beta\log\frac{\pi_{\phi}^{RL}(y\mid x)}{\pi^{SFT}(y\mid x)}\right]+\gamma\mathbb{E}_{x\sim D_{\mathrm{pretrain}}}\left[\log\pi_{\phi}^{RL}(x)\right]  
$$
可以直接记成：  
$$  
\text{Reward}-\text{KL Penalty}+\text{PTX}  
$$
- **Actor → 最终被 PPO 更新**：$\pi_{\phi}^{RL}$，真正通过 PPO 被更新的模型，负责生成 response。
- **Reward Model → 给 reward**： $r_{\theta}(x,y)$，给完整的 prompt + response 打分，告诉 Actor 这个回答好不好。
- **Reference Model → 做 KL 约束**：$\pi^{SFT}$，冻结的 SFT 模型，用在 KL penalty 里限制 Actor 不要偏离太远。
- **Critic → 算 $V_t$ 和 advantage**：这个总 objective 里**没有直接写出来**。Critic 负责预测 $V_t$，再和 reward 一起计算 advantage $A_t$，最终用于 PPO 的 Actor loss。
- **PTX：** $\gamma\mathbb{E}[\log\pi_{\phi}^{RL}(x)]$，继续用一部分预训练数据训练 Actor，防止 RLHF 后遗忘原来的能力。(加的原来的reward)