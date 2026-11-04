import json
from pathlib import Path
NEW=json.loads((Path(__file__).parent/'content/obsidian-articles.json').read_text())
TITLES={a['slug']:a['title'] for a in NEW}|{'transformer':'Transformer','lora':'LoRA：低秩适配'}
CATEGORY={
 'transformer':('ai','大模型','预训练'), 'gpt-bert':('ai','大模型','预训练'),
 'gpt3-gpt4':('ai','大模型','预训练'),
 'sft':('ai','大模型','微调'),
 'lora':('ai','大模型','微调'),
 'rlhf-ppo':('ai','大模型','对齐'), 'grpo':('ai','大模型','对齐'),
 'sequence-models':('deep-learning','深度学习',''), 'rmsnorm':('deep-learning','深度学习',''),
 'rope-yarn':('deep-learning','深度学习',''), 'padding-mask':('deep-learning','深度学习',''),
 'mdp':('reinforcement-learning','强化学习',''), 'bellman':('reinforcement-learning','强化学习',''),
 'policy-gradient':('reinforcement-learning','强化学习',''), 'ppo':('reinforcement-learning','强化学习',''),
 'actor-critic':('reinforcement-learning','强化学习',''), 'minimind':('projects','项目',''),
}
def destination(slug):
 cat,label,phase=CATEGORY[slug]
 return ('/projects/' if cat=='projects' else '/blogs/#'+cat),label,phase
def rows(cat):
 result='';last_phase=None
 for slug,(category,label,phase) in CATEGORY.items():
  if category!=cat:continue
  if phase and phase!=last_phase:result+=f'<h3 class="topic-stage">{phase}</h3>';last_phase=phase
  date=next((a['date'] for a in NEW if a['slug']==slug),'2026-10-26')
  year,month,day=map(int,date.split('-'));display=f'{year} 年 {month} 月 {day} 日'
  result+=f'<article class="row"><time datetime="{date}">{display}</time><h3><a href="/posts/{slug}/">{TITLES[slug]}</a></h3></article>'
 return result
