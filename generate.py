from pathlib import Path
import html
import re
import hashlib
from course_notes import topic_rows
root=Path(__file__).parent/'dist'
# One revision controls page links and styles across every generated page.
site_revision=hashlib.sha256((root/'style.css').read_bytes()+(Path(__file__).parent/'content/stack.md').read_bytes()+(Path(__file__).parent/'content/heap.md').read_bytes()+(Path(__file__).parent/'content/queue.md').read_bytes()+(Path(__file__).parent/'course_notes.py').read_bytes()+(Path(__file__).parent/'content/home.html').read_bytes()+(Path(__file__).parent/'content/transformer.md').read_bytes()+(Path(__file__).parent/'content/lora.md').read_bytes()).hexdigest()[:12]
def page(title,active,body,path):
    nav=''.join(f'<a href="{url}"'+(' aria-current="page"' if key==active else '')+f'>{label}</a>' for key,label,url in [('home','首页','/'),('blogs','博客','/blogs/'),('projects','项目','/projects/')])
    text=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="个人主页、项目与学习笔记"><title>{title} · Nathen</title><link rel="stylesheet" href="/style.css?v={site_revision}"><link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%231769aa'/%3E%3Cpath d='M9 8h14v16H9zM12 13h8M12 17h8' fill='none' stroke='white' stroke-width='2'/%3E%3C/svg%3E"></head><body><div class="shell"><header class="header"><a class="name" href="/">Nathen</a><nav class="nav" aria-label="主导航">{nav}</nav></header><main id="main-content">{body}</main><footer class="footer"><span>© 2026 Nathen</span><span>学习、构建与记录。</span></footer></div></body></html>'''
    # Apply the same revision to every internal page link, including existing queries.
    text=re.sub(r'href="(/[^"?#]*?/)(?:\?[^"#]*)?(#[^"]*)?"', lambda m: 'href="'+m.group(1)+'?v='+site_revision+(m.group(2) or '')+'"', text)
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
posts=[('java', 'Java', 'threads', 'Java 并发学习笔记', '理解线程、共享状态和同步机制。', [('共享状态', '多个线程访问同一份可变数据时，需要关注可见性与原子性。一个简单的递增操作也可能包含多个步骤。'), ('同步机制', 'synchronized 和锁可以保护临界区。缩小共享状态和临界区范围，通常比增加复杂同步逻辑更容易维护。')]), ('notes', '随笔', 'first-post', '开始记录，慢慢积累', '给这个个人空间的第一篇笔记。', [('为什么写下来', '把一个问题写清楚，常常意味着重新梳理自己的理解。这里会保留学习过程中的问题、尝试和收获。'), ('接下来', '可以从一个技术问题、一个小项目或一次实验开始。每篇文章只需要讲清楚一个具体问题。')])]
groups='';cats=''
for cat,label in [('systems','分布式系统'),('algorithms','算法'),('ai','AI 与模型'),('java','Java'),('notes','随笔')]:
    cats+=f'<a href="#{cat}">{label}</a>'
    rows=''.join(f'<article class="row"><time datetime="2026-10-03">2026 年 10 月 3 日</time><h3><a href="/posts/{slug}/">{title}</a></h3></article>' for c,l,slug,title,desc,sections in posts if c==cat)
    if cat=='systems':
        rows=topic_rows()+rows
    if cat=='algorithms':
        rows='<article class="row"><time datetime="2026-10-09">2026 年 10 月 9 日</time><h3><a href="/posts/sliding-window/?v=sliding-20261009-1">滑动窗口 · 文章索引</a></h3></article>'+rows
    if cat=='algorithms':
        rows='<article class="row"><time datetime="2026-10-12">2026 年 10 月 12 日</time><h3><a href="/posts/binary-search/">二分算法 · 文章索引</a></h3></article>'+rows
    if cat=='algorithms':
        rows='<article class="row"><time datetime="2026-10-22">2026 年 10 月 22 日</time><h3><a href="/posts/stack/">栈 · 文章索引</a></h3></article>'+rows
    if cat=='algorithms':
        rows='<article class="row"><time datetime="2026-10-24">2026 年 10 月 24 日</time><h3><a href="/posts/heap/">堆 · 文章索引</a></h3></article>'+rows
    if cat=='algorithms':
        rows='<article class="row"><time datetime="2026-10-24">2026 年 10 月 24 日</time><h3><a href="/posts/queue/">队列 · 文章索引</a></h3></article>'+rows
    if cat=='ai':
        rows=''.join(f'<article class="row"><time datetime="2026-10-26">2026 年 10 月 26 日</time><h3><a href="/posts/{slug}/">{title}</a></h3></article>' for slug,title in [('transformer','Transformer'),('lora','LoRA：低秩适配')])
    groups+=f'<section class="group" id="{cat}"><h2>{label}</h2><div class="list">{rows}</div></section>'
page('博客','blogs',f'<p class="eyebrow">Writing & notes</p><h1>博客</h1><p class="lead">记录学习、项目与思考。</p><div class="directory"><nav class="categories" aria-label="文章分类"><span>文章分类</span>{cats}</nav><div>{groups}</div></div>','blogs/index.html')
page('首页','home',(Path(__file__).parent/'content/home.html').read_text(),'index.html')
page('项目','projects','''<p class="eyebrow">Selected work</p><h1>项目</h1><p class="lead">围绕分布式系统、实时数据与 AI 工作流的工程实践。</p><article class="panel"><h2>Distributed Key-Value Store</h2><p class="note">C++ · gRPC · Raft · RocksDB · Docker</p><p>基于 Raft 共识的分布式键值存储，在五节点集群中实现选主和日志复制。通过 gRPC 提供 GET/PUT 接口，使用 RocksDB 持久化数据，并实现日志压缩、快照与故障节点恢复。</p><p>本地基准测试中实现亚毫秒读取延迟；重启与恢复测试中，日志压缩减少约 60% 的持久化日志占用。</p><a class="pill" href="https://github.com/cultist123/distributed-kv-store">查看源码</a></article><article class="panel"><h2>Real-Time IoT Monitoring Platform</h2><p class="note">Node.js · Express · TCP/IP · WebSocket · Spring Boot · MySQL · MongoDB</p><p>通过持久 TCP 连接采集连续传感器数据，使用 WebSocket 实时推送，并提供历史数据查询接口。Spring Boot 管理服务负责用户、设备和访问记录，与实时采集工作负载分离。</p><p>本地负载测试支持 50 多个模拟设备连接，端到端更新延迟低于 50 ms；结合 UWB 定位与 Kalman 滤波，在受控室内测试中将平均定位误差从 15 cm 降至 9 cm。</p><a class="pill" href="https://github.com/cultist123/Real-Time-IoT-Monitoring-Platform">查看源码</a></article><article class="panel"><h2>AgentOps — AI Infrastructure Copilot</h2><p class="note">Python · LangGraph · PostgreSQL · Redis · OpenSearch · Docker</p><p>实现包含规划、检索、持久记忆与工具调用的多步骤 AI Agent 运行时。结合 OpenSearch 与 PostgreSQL 构建混合 RAG 和跨会话记忆层，通过 Redis 缓存减少重复检索，并使用 SSE 展示执行状态。</p><p>缓存命中时，检索延迟从 150–350 ms 降至 2–5 ms；记录检索来源、工具调用和执行延迟，便于调试工作流。</p><a class="pill" href="https://github.com/cultist123/gomini">查看源码</a></article>''','projects/index.html')
for cat,label,slug,title,desc,sections in posts:
    content=''.join(f'<h2>{html.escape(h)}</h2><p>{html.escape(p)}</p>' for h,p in sections)
    page(title,'blogs',f'<a class="back" href="/blogs/#{cat}">返回博客</a><p class="eyebrow">{label}</p><h1>{title}</h1><p class="lead">2026 年 10 月 3 日 · 示例文章</p><article class="panel prose"><p>{desc}</p>{content}</article>',f'posts/{slug}/index.html')

from course_notes import build
build(page)

from sliding_window import build as build_sliding_window
build_sliding_window(page)

from binary_search import build as build_binary_search
build_binary_search(page)

from stack_notes import build as build_stack_notes
build_stack_notes(page)

from heap_notes import build as build_heap_notes
build_heap_notes(page)

from queue_notes import build as build_queue_notes
build_queue_notes(page)

from ai_notes import build as build_ai_notes
build_ai_notes(page)
