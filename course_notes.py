"""Build the course index and individual lessons from the preserved note HTML."""
from pathlib import Path
import html
import re

LESSONS = [
 ('foundations', '分布式系统：基础概念', '计算模型与架构'),
 ('mapreduce', 'MapReduce 与 Hadoop：数据流、调度与容错', '计算模型与架构'),
 ('grid-computing', 'Grid Computing：资源与跨站点调度', '计算模型与架构'),
 ('gossip', 'Gossip：传播、扩展性与容错', '成员管理与故障检测'),
 ('failure-detection', '故障检测与成员管理：Heartbeat 和 SWIM', '成员管理与故障检测'),
 ('gnutella', 'Gnutella：泛洪、消息与搜索', 'P2P 与数据查找'),
 ('bittorrent', 'BitTorrent：分片与 Rarest-First', 'P2P 与数据查找'),
 ('chord', 'Chord：一致性哈希与路由', 'P2P 与数据查找'),
 ('kelips', 'Kelips：分组、元数据与查找', 'P2P 与数据查找'),
 ('key-value-store', '键值存储：CAP 与一致性模型', '键值存储'),
 ('bloom-filter', 'Bloom Filter：原理与误判率', '键值存储'),
 ('cassandra', 'Cassandra：副本、读写与故障恢复', '键值存储'),
 ('quorum', 'Cassandra 与 Quorum：交集与一致性级别', '键值存储'),
 ('lamport-clock', 'Lamport Clock：事件顺序', '逻辑时钟'),
 ('vector-clock', 'Vector Clock：因果与并发', '逻辑时钟'),
]
MENU = """<button class="course-menu-button" aria-controls="course-navigation" aria-expanded="false">☰ 目录</button><script>const courseMenu=document.querySelector('.course-menu-button');const courseSidebar=document.querySelector('.course-sidebar');courseMenu.addEventListener('click',()=>{const open=courseMenu.getAttribute('aria-expanded')!=='true';courseMenu.setAttribute('aria-expanded',String(open));courseSidebar.classList.toggle('is-open',open);});courseSidebar.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{courseMenu.setAttribute('aria-expanded','false');courseSidebar.classList.remove('is-open');}));document.addEventListener('keydown',e=>{if(e.key==='Escape'){courseMenu.setAttribute('aria-expanded','false');courseSidebar.classList.remove('is-open');}});</script>"""
MATH = r"""<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js"></script>"""

TOPICS = [
 ('architecture','计算模型与架构'),
 ('membership','成员管理与故障检测'),
 ('peer-to-peer','P2P 与数据查找'),
 ('storage','键值存储'),
 ('clocks','逻辑时钟'),
]
def topic_url(name):
 return '/topics/distributed/'+next(slug for slug,label in TOPICS if label==name)+'/'
def topic_rows():
 return ''.join(f'<article class="row"><time datetime="2026-10-24">{sum(c==label for _,_,c in LESSONS)} 篇文章</time><h3><a href="{topic_url(label)}">{label}</a></h3></article>' for _,label in TOPICS)
def build(page):
 rendered={}
 for slug,title,group in LESSONS:
  content=(Path(__file__).parent/f'content/p2p-{slug}.html').read_text();entries=[]
  def heading(m):
   level,text=m.groups();anchor=f'section-{len(entries)+1}'
   entries.append((level,anchor,html.unescape(re.sub('<[^>]+>','',text))))
   return f'<h{level} id="{anchor}">{text}</h{level}>'
  content=re.sub(r'<h([34])>(.*?)</h\1>',heading,content,flags=re.S)
  rendered[slug]=(content,entries)
 def sidebar(group=None,current=None,entries=()):
  members=[x for x in LESSONS if x[2]==group] if group else []
  links=''.join(f'<a href="/posts/p2p/{slug}/"'+(' aria-current="page"' if slug==current else '')+f'>{i+1:02d} · {html.escape(title)}</a>' for i,(slug,title,_) in enumerate(members))
  if group:
   nav=f'<a class="course-index-link" href="{topic_url(group)}">{group} · 文章索引</a>'+links
  else:
   nav=''.join(f'<a href="{topic_url(label)}">{label}</a>' for _,label in TOPICS)
  toc=''.join(f'<a class="toc-level-{level}" href="#{anchor}">{html.escape(label)}</a>' for level,anchor,label in entries)
  return '<aside id="course-navigation" class="course-sidebar"><div class="sidebar-heading">专题目录</div><nav aria-label="文章索引">'+nav+'</nav>'+(f'<nav class="local-toc" aria-label="本文目录"><strong>本文目录</strong>{toc}</nav>' if entries else '')+'<nav class="local-toc" aria-label="专题导航"><a href="/blogs/#systems">全部分布式系统专题</a></nav></aside>'
 overview=''.join(f'<article class="lesson-summary"><h2><a href="{topic_url(label)}">{label}</a></h2><p>{sum(c==label for _,_,c in LESSONS)} 篇文章</p></article>' for _,label in TOPICS)
 page('分布式系统','blogs',f'<a class="back" href="/blogs/#systems">返回博客</a><p class="eyebrow">Distributed Systems</p><h1>分布式系统专题</h1><p class="lead">按主题阅读</p><div class="course-layout">{sidebar()}<div class="course-main">{overview}</div></div>'+MENU,'posts/p2p/index.html')
 for topic_slug,label in TOPICS:
  members=[x for x in LESSONS if x[2]==label];rows=''
  for slug,title,_ in members:
   _,entries=rendered[slug]
   anchors=''.join(f'<li><a href="/posts/p2p/{slug}/#{anchor}">{html.escape(text)}</a></li>' for level,anchor,text in entries if level=='3')
   rows+=f'<article class="lesson-summary"><h2><a href="/posts/p2p/{slug}/">{title}</a></h2><ul>{anchors}</ul></article>'
  page(label,'blogs',f'<a class="back" href="/blogs/#systems">返回博客</a><p class="eyebrow">分布式系统</p><h1>{label}</h1><p class="lead">{len(members)} 篇文章</p><div class="course-layout">{sidebar(label)}<div class="course-main">{rows}</div></div>'+MENU,f'topics/distributed/{topic_slug}/index.html')
  for i,(slug,title,_) in enumerate(members):
   content,entries=rendered[slug]
   prev=members[i-1] if i else None;next_=members[i+1] if i+1<len(members) else None
   previous=f'<a rel="prev" href="/posts/p2p/{prev[0]}/">← 上一篇<br>{prev[1]}</a>' if prev else '<span></span>'
   following=f'<a rel="next" href="/posts/p2p/{next_[0]}/">下一篇 →<br>{next_[1]}</a>' if next_ else '<span></span>'
   body=f'<a class="back" href="{topic_url(label)}">返回{label}</a><p class="eyebrow">分布式系统 · {label} · {i+1:02d} / {len(members):02d}</p><h1>{html.escape(title)}</h1><p class="lead">更新于 2026 年 10 月 9 日</p><div class="course-layout">{sidebar(label,slug,entries)}<div class="course-main"><article class="prose course-note">{content}</article><nav class="lesson-pagination" aria-label="相邻文章">{previous}{following}</nav></div></div>'
   page(title,'blogs',body+MENU+MATH,f'posts/p2p/{slug}/index.html')
