from pathlib import Path
import re,html,json
from course_notes import MENU,MATH
from ai_categories import destination
ROOT=Path(__file__).parent
ARTICLES=json.loads((ROOT/'content/obsidian-articles.json').read_text())
def rows():
 return ''.join(f'<article class="row"><time datetime="{a["date"]}">2026 年 11 月 1 日</time><h3><a href="/posts/{a["slug"]}/">{a["title"]}</a></h3></article>' for a in ARTICLES)
def build(page):
 for a in ARTICLES:
  slug,title=a['slug'],a['title'];entries=[]
  back,label,phase=destination(slug)
  content=(ROOT/f'content/{slug}.html').read_text()
  def heading(m):
   level,text=m.groups();anchor=f'section-{len(entries)+1}'
   entries.append((level,anchor,html.unescape(re.sub('<[^>]+>','',text))))
   return f'<h{level} id="{anchor}">{text}</h{level}>'
  content=re.sub(r'<h([23])>(.*?)</h\1>',heading,content,flags=re.S)
  if not entries:
   content='<h2 id="notes">思路与公式</h2>'+content;entries=[('2','notes','思路与公式')]
  toc=''.join(f'<a class="toc-level-{int(level)+1}" href="#{anchor}">{html.escape(label)}</a>' for level,anchor,label in entries)
  sidebar=f'<aside id="course-navigation" class="course-sidebar"><div class="sidebar-heading">本文目录</div><nav aria-label="本文目录">'+toc+f'</nav><nav class="local-toc"><a href="{back}">返回{label}</a></nav></aside>'
  body=f'<a class="back" href="{back}">返回{label}</a><p class="eyebrow">{label}{' · '+phase if phase else ''}</p><h1>{html.escape(title)}</h1><p class="lead">2026 年 11 月 1 日 · 学习笔记</p><div class="course-layout">{sidebar}<div class="course-main"><article class="prose course-note">{content}</article></div></div>'
  active='projects' if slug=='minimind' else 'blogs'
  page(title,active,body+MENU+MATH,f'posts/{slug}/index.html')
  if slug=='minimind':page(title,active,body+MENU+MATH,'projects/minimind/index.html')
