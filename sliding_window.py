from pathlib import Path
import re,html
from course_notes import MENU,MATH
ARTICLES=[('fixed','定长窗口：入、更新答案、出','窗口长度固定时的三步套路与元音计数示例。'),('longest','不定长窗口：求最长子数组','扩展右边界，在窗口不合法时收缩，再更新最大长度。'),('shortest','不定长窗口：求最短子数组','窗口满足条件时记录答案，收缩左边界，并比较最长与最短模板。')]
ARTICLES += [('at-most','子数组计数：至多问题','越短越合法时，累加当前合法窗口长度。'),('at-least','子数组计数：至少问题','越长越合法时，累加合法左端点的个数。'),('exactly','子数组计数：恰好问题与例题','用两个至多或两个至少相减，并整理相关例题。')]
BASE='/posts/sliding-window/'
def url(slug=''):return BASE+(slug+'/' if slug else '')+'?v=sliding-20261009-1'
def build(page):
 def sidebar(current=None,entries=()):
  links=''.join(f'<a href="{url(slug)}"'+(' aria-current="page"' if current==slug else '')+f'>{i+1:02d} · {html.escape(title)}</a>' for i,(slug,title,desc) in enumerate(ARTICLES))
  toc=''.join(f'<a href="#{anchor}">{html.escape(label)}</a>' for anchor,label in entries)
  return '<aside id="course-navigation" class="course-sidebar"><div class="sidebar-heading">文章目录</div><nav aria-label="文章索引"><a class="course-index-link" href="'+url()+'">滑动窗口 · 文章索引</a>'+links+'</nav>'+(f'<nav class="local-toc" aria-label="本文目录"><strong>本文目录</strong>{toc}</nav>' if entries else '')+'</aside>'
 rows=''.join(f'<article class="lesson-summary"><h3><a href="{url(slug)}"><span>{i+1:02d}</span> {html.escape(title)}</a></h3><p>{desc}</p></article>' for i,(slug,title,desc) in enumerate(ARTICLES))
 body=f'<a class="back" href="/blogs/#algorithms">返回博客</a><p class="eyebrow">Algorithms · Sliding Window</p><h1>滑动窗口</h1><p class="lead">6 篇技术文章 · 更新于 2026 年 10 月 9 日</p><div class="course-layout">{sidebar()}<div class="course-main"><p>从固定窗口到动态窗口，整理常见模板、代码与例题。</p>{rows}</div></div>'
 page('滑动窗口','blogs',body+MENU, 'posts/sliding-window/index.html')
 for i,(slug,title,desc) in enumerate(ARTICLES):
  content=(Path(__file__).parent/f'content/sliding-window-{slug}.html').read_text();entries=[]
  def heading(m):
   level,text=m.groups();anchor=f'section-{len(entries)+1}';entries.append((anchor,html.unescape(re.sub('<[^>]+>','',text))));return f'<h{level} id="{anchor}">{text}</h{level}>'
  content=re.sub(r'<h([234])>(.*?)</h\1>',heading,content,flags=re.S)
  # Give every article a useful local jump even if the original note has no headings.
  content='<h2 id="template">思路与模板</h2>'+content;entries.insert(0,('template','思路与模板'))
  previous=f'<a rel="prev" href="{url(ARTICLES[i-1][0])}">← 上一篇<br>{ARTICLES[i-1][1]}</a>' if i else '<span></span>'
  following=f'<a rel="next" href="{url(ARTICLES[i+1][0])}">下一篇 →<br>{ARTICLES[i+1][1]}</a>' if i+1<len(ARTICLES) else '<span></span>'
  body=f'<a class="back" href="{url()}">返回文章索引</a><p class="eyebrow">算法 · 滑动窗口</p><h1>{title}</h1><p class="lead">更新于 2026 年 10 月 9 日 · {desc}</p><div class="course-layout">{sidebar(slug,entries)}<div class="course-main"><article class="prose course-note">{content}</article><nav class="lesson-pagination" aria-label="相邻文章">{previous}{following}</nav></div></div>'
  page(title,'blogs',body+MENU+MATH,f'posts/sliding-window/{slug}/index.html')
