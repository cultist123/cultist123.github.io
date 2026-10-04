"""Build the course index and individual lessons from the preserved note HTML."""
from pathlib import Path
import html
import re

LESSONS = [
 ('gnutella', 'Gnutella：泛洪与 TTL', 'P2P 与数据查找'),
 ('bittorrent', 'BitTorrent：分片与 Rarest-First', 'P2P 与数据查找'),
 ('chord', 'Chord：一致性哈希与路由', 'P2P 与数据查找'),
 ('bloom-filter', 'Bloom Filter：原理与误判率', '键值存储'),
 ('quorum', 'Quorum：交集与多数派', '键值存储'),
 ('cassandra', 'Cassandra：写入、压缩与删除', '键值存储'),
 ('lamport-clock', 'Lamport Clock：事件顺序', '逻辑时钟'),
 ('vector-clock', 'Vector Clock：因果与并发', '逻辑时钟'),
]
MENU = """<button class="course-menu-button" aria-controls="course-navigation" aria-expanded="false">☰ 目录</button><script>const courseMenu=document.querySelector('.course-menu-button');const courseSidebar=document.querySelector('.course-sidebar');courseMenu.addEventListener('click',()=>{const open=courseMenu.getAttribute('aria-expanded')!=='true';courseMenu.setAttribute('aria-expanded',String(open));courseSidebar.classList.toggle('is-open',open);});courseSidebar.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{courseMenu.setAttribute('aria-expanded','false');courseSidebar.classList.remove('is-open');}));document.addEventListener('keydown',e=>{if(e.key==='Escape'){courseMenu.setAttribute('aria-expanded','false');courseSidebar.classList.remove('is-open');}});</script>"""
MATH = r"""<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js"></script>"""

def build(page):
 source=(Path(__file__).parent/'content/p2p.html').read_text()
 source=source.replace('<h2>Key-Value Store</h2>', '')
 # This screenshot introduces vector clocks; keep it with that lesson.
 picture=re.search(r'<p><img src="/images/p2p/vector-clock.png"[^>]* /></p>',source).group(0)
 source=source.replace(picture,'').replace('<h2>Vector Clock</h2>','<h2>Vector Clock</h2>\n'+picture)
 parts=re.split(r'<h2>[^<]+</h2>',source)
 intro=parts.pop(0)
 assert len(parts)==len(LESSONS)
 rendered=[]
 for content in parts:
  entries=[]
  def heading(match):
   level,text=match.groups();anchor=f'section-{len(entries)+1}'
   label=html.unescape(re.sub('<[^>]+>','',text))
   entries.append((level,anchor,label))
   return f'<h{level} id="{anchor}">{text}</h{level}>'
  content=re.sub(r'<h([34])>(.*?)</h\1>',heading,content,flags=re.S)
  rendered.append((content,entries))
 def sidebar(current=None,entries=()):
  links=''.join(f'<a href="/posts/p2p/{slug}/"'+(' aria-current="page"' if slug==current else '')+f'>{i+1:02d} · {html.escape(title)}</a>' for i,(slug,title,group) in enumerate(LESSONS))
  toc=''.join(f'<a class="toc-level-{level}" href="#{anchor}">{html.escape(label)}</a>' for level,anchor,label in entries)
  return '<aside id="course-navigation" class="course-sidebar"><div class="sidebar-heading">笔记目录</div><nav aria-label="课程索引"><a class="course-index-link" href="/posts/p2p/">CS425 · 课程索引</a>'+links+'</nav>'+(f'<nav class="local-toc" aria-label="本文目录"><strong>本文目录</strong>{toc}</nav>' if entries else '')+'</aside>'
 groups=''
 for group in dict.fromkeys(x[2] for x in LESSONS):
  rows=''
  for i,(slug,title,category) in enumerate(LESSONS):
   if category!=group:continue
   _,entries=rendered[i]
   topics=''.join(f'<li><a href="/posts/p2p/{slug}/#{anchor}">{html.escape(label)}</a></li>' for level,anchor,label in entries if level=='3')
   rows+=f'<article class="lesson-summary"><h3><a href="/posts/p2p/{slug}/"><span>{i+1:02d}</span> {html.escape(title)}</a></h3><ul>{topics}</ul></article>'
  groups+=f'<section class="lesson-group"><h2>{group}</h2>{rows}</section>'
 page('分布式系统课程笔记','blogs',f'<a class="back" href="/blogs/#systems">返回博客</a><p class="eyebrow">CS425 · Course notes</p><h1>分布式系统课程笔记</h1><p class="lead">8 篇主题笔记 · 更新于 2026 年 10 月 4 日</p><div class="course-layout">{sidebar()}<div class="course-main"><p>按主题阅读，或从下方索引直接跳到具体知识点。</p>{groups}</div></div>'+MENU,'posts/p2p/index.html')
 for i,((slug,title,group),(content,entries)) in enumerate(zip(LESSONS,rendered)):
  prev=LESSONS[i-1] if i else None;next_=LESSONS[i+1] if i+1<len(LESSONS) else None
  previous=f'<a rel="prev" href="/posts/p2p/{prev[0]}/">← 上一篇<br>{html.escape(prev[1])}</a>' if prev else '<span></span>'
  following=f'<a rel="next" href="/posts/p2p/{next_[0]}/">下一篇 →<br>{html.escape(next_[1])}</a>' if next_ else '<span></span>'
  if i==0:content=intro+content
  body=f'<a class="back" href="/posts/p2p/">返回课程索引</a><p class="eyebrow">CS425 · {group} · {i+1:02d} / 08</p><h1>{html.escape(title)}</h1><p class="lead">2026 年 10 月 4 日 · 课程笔记</p><div class="course-layout">{sidebar(slug,entries)}<div class="course-main"><article class="prose course-note">{content}</article><nav class="lesson-pagination" aria-label="相邻文章">{previous}{following}</nav></div></div>'
  page(title,'blogs',body+MENU+MATH,f'posts/p2p/{slug}/index.html')
