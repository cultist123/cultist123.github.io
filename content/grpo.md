# GRPO：目标函数与组内优势估计

<img src="/images/obsidian/6988f0fed6f3.png" alt="Pasted image 20261030233240.png" width="520" />
简单过了一遍《DeepSeekMath》,主要就是在PPO的基础上改进GRPO,主要在于数学式子,先有个印象,学完强化学习再回来自己推一遍公式
$$
\mathcal{J}_{GRPO}(\theta)=\mathbb{E}_{q\sim P(Q),\,\{o_i\}_{i=1}^{G}\sim\pi_{\theta_{old}}(O|q)}\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}\sum_{t=1}^{|o_i|}\left\{\min\left[\frac{\pi_\theta(o_{i,t}|q,o_{i,<t})}{\pi_{\theta_{old}}(o_{i,t}|q,o_{i,<t})}\hat{A}_{i,t},\ \mathrm{clip}\left(\frac{\pi_\theta(o_{i,t}|q,o_{i,<t})}{\pi_{\theta_{old}}(o_{i,t}|q,o_{i,<t})},1-\varepsilon,1+\varepsilon\right)\hat{A}_{i,t}\right]-\beta\,\mathbb{D}_{KL}\left[\pi_\theta\,\|\,\pi_{ref}\right]\right\}
$$

$$
\mathbb{D}_{KL}\left[\pi_\theta\,\|\,\pi_{ref}\right]=\frac{\pi_{ref}(o_{i,t}|q,o_{i,<t})}{\pi_\theta(o_{i,t}|q,o_{i,<t})}-\log\frac{\pi_{ref}(o_{i,t}|q,o_{i,<t})}{\pi_\theta(o_{i,t}|q,o_{i,<t})}-1
$$

$$
\hat{A}_{i,t}=\tilde{r}_i=\frac{r_i-\mathrm{mean}(\mathbf{r})}{\mathrm{std}(\mathbf{r})}
$$
