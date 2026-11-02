from pathlib import Path
import re,html,json
from course_notes import MENU,MATH
ROOT=Path(__file__).parent
ARTICLES=json.loads((ROOT/'content/obsidian-articles.json').read_text())
def rows():
 return ''.join(f'<article class="row"><time datetime="{a["date"]}">2026 年 11 月 1 日</time><h3><a href="/posts/{a["slug"]}/">{a["title"]}</a></h3></article>' for a in ARTICLES)
def build(page):
 for a in ARTICLES:
  slug,title=a['slug'],a['title'];entries=[]
  content=(ROOT/f'content/{slug}.html').read_text()
  def heading(m):
   level,text=m.groups();anchor=f'section-{len(entries)+1}'
   entries.append((level,anchor,html.unescape(re.sub('<[^>]+>','',text))))
   return f'<h{level} id="{anchor}">{text}</h{level}>'
  content=re.sub(r'<h([23])>(.*?)</h\1>',heading,content,flags=re.S)
  if not entries:
   content='<h2 id="notes">思路与公式</h2>'+content;entries=[('2','notes','思路与公式')]
  toc=''.join(f'<a class="toc-level-{int(level)+1}" href="#{anchor}">{html.escape(label)}</a>' for level,anchor,label in entries)
  sidebar='<aside id="course-navigation" class="course-sidebar"><div class="sidebar-heading">本文目录</div><nav aria-label="本文目录">'+toc+'</nav><nav class="local-toc"><a href="/blogs/#ai">返回 AI 与模型</a></nav></aside>'
  body=f'<a class="back" href="/blogs/#ai">返回博客</a><p class="eyebrow">AI · Models</p><h1>{html.escape(title)}</h1><p class="lead">2026 年 11 月 1 日 · 学习笔记</p><div class="course-layout">{sidebar}<div class="course-main"><article class="prose course-note">{content}</article></div></div>'
  page(title,'blogs',body+MENU+MATH,f'posts/{slug}/index.html')
