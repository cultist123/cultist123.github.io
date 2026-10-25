from pathlib import Path
import re,html
from course_notes import MENU,MATH
ARTICLES=[('basics', '堆：基础知识', ''), ('top-k', '堆：第 K 小／大与 Top-K', ''), ('scheduling', '堆：时间模拟与资源调度', ''), ('greedy', '堆：贪心重排', ''), ('merge', '堆：多路归并', '')]
BASE='/posts/heap/'
def url(slug=''):return BASE+(slug+'/' if slug else '')+'?v=sliding-20261009-1'
def build(page):
 def sidebar(current=None,entries=()):
  links=''.join(f'<a href="{url(slug)}"'+(' aria-current="page"' if current==slug else '')+f'>{i+1:02d} · {html.escape(title)}</a>' for i,(slug,title,desc) in enumerate(ARTICLES))
  toc=''.join(f'<a href="#{anchor}">{html.escape(label)}</a>' for anchor,label in entries)
  return '<aside id="course-navigation" class="course-sidebar"><div class="sidebar-heading">文章目录</div><nav aria-label="文章索引"><a class="course-index-link" href="'+url()+'">堆 · 文章索引</a>'+links+'</nav>'+(f'<nav class="local-toc" aria-label="本文目录"><strong>本文目录</strong>{toc}</nav>' if entries else '')+'</aside>'
 rows=''.join(f'<article class="lesson-summary"><h3><a href="{url(slug)}"><span>{i+1:02d}</span> {html.escape(title)}</a></h3></article>' for i,(slug,title,desc) in enumerate(ARTICLES))
 body=f'<a class="back" href="/blogs/#algorithms">返回博客</a><p class="eyebrow">Algorithms · Heap</p><h1>堆</h1><p class="lead">5 篇技术文章 · 更新于 2026 年 10 月 24 日</p><div class="course-layout">{sidebar()}<div class="course-main"><p>整理堆的基础操作、Top-K、时间调度、贪心重排与多路归并。</p>{rows}</div></div>'
 page('堆','blogs',body+MENU, 'posts/heap/index.html')
 for i,(slug,title,desc) in enumerate(ARTICLES):
  content=(Path(__file__).parent/f'content/heap-{slug}.html').read_text();entries=[]
  def heading(m):
   level,text=m.groups();anchor=f'section-{len(entries)+1}';entries.append((anchor,html.unescape(re.sub('<[^>]+>','',text))));return f'<h{level} id="{anchor}">{text}</h{level}>'
  content=re.sub(r'<h([234])>(.*?)</h\1>',heading,content,flags=re.S)
  # Give every article a useful local jump even if the original note has no headings.
  content='<h2 id="template">思路与模板</h2>'+content;entries.insert(0,('template','思路与模板'))
  previous=f'<a rel="prev" href="{url(ARTICLES[i-1][0])}">← 上一篇<br>{ARTICLES[i-1][1]}</a>' if i else '<span></span>'
  following=f'<a rel="next" href="{url(ARTICLES[i+1][0])}">下一篇 →<br>{ARTICLES[i+1][1]}</a>' if i+1<len(ARTICLES) else '<span></span>'
  body=f'<a class="back" href="{url()}">返回文章索引</a><p class="eyebrow">算法 · 堆</p><h1>{title}</h1><p class="lead">更新于 2026 年 10 月 24 日</p><div class="course-layout">{sidebar(slug,entries)}<div class="course-main"><article class="prose course-note">{content}</article><nav class="lesson-pagination" aria-label="相邻文章">{previous}{following}</nav></div></div>'
  page(title,'blogs',body+MENU+MATH,f'posts/heap/{slug}/index.html')
