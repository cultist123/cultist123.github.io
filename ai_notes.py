from pathlib import Path
import re,html
from course_notes import MENU,MATH
ARTICLES=[('transformer','Transformer'),('lora','LoRA：低秩适配')]
def build(page):
 for slug,title in ARTICLES:
  content=(Path(__file__).parent/f'content/{slug}.html').read_text();entries=[]
  def heading(m):
   level,text=m.groups();anchor=f'section-{len(entries)+1}'
   entries.append((level,anchor,html.unescape(re.sub('<[^>]+>','',text))))
   return f'<h{level} id="{anchor}">{text}</h{level}>'
  content=re.sub(r'<h([23])>(.*?)</h\1>',heading,content,flags=re.S)
  toc=''.join(f'<a class="toc-level-{int(level)+1}" href="#{anchor}">{html.escape(label)}</a>' for level,anchor,label in entries)
  links=''.join(f'<a href="/posts/{s}/"'+(' aria-current="page"' if s==slug else '')+f'>{t}</a>' for s,t in ARTICLES)
  sidebar='<aside id="course-navigation" class="course-sidebar"><div class="sidebar-heading">本文目录</div><nav aria-label="本文目录">'+toc+'</nav><nav class="local-toc" aria-label="相关文章"><strong>AI 与模型</strong>'+links+'<a href="/blogs/#ai">返回博客</a></nav></aside>'
  body=f'<a class="back" href="/blogs/#ai">返回博客</a><p class="eyebrow">AI · Models</p><h1>{title}</h1><p class="lead">2026 年 10 月 26 日</p><div class="course-layout">{sidebar}<div class="course-main"><article class="prose course-note">{content}</article></div></div>'
  page(title,'blogs',body+MENU+MATH,f'posts/{slug}/index.html')
