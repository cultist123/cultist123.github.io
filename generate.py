from pathlib import Path
import html
root=Path(__file__).parent/'dist'
def page(title,active,body,path):
    nav=''.join(f'<a href="{url}"'+(' aria-current="page"' if key==active else '')+f'>{label}</a>' for key,label,url in [('home','首页','/'),('blogs','博客','/blogs/'),('projects','项目','/projects/')])
    text=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="个人主页、项目与学习笔记"><title>{title} · Nathen</title><link rel="stylesheet" href="/style.css"><link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%231769aa'/%3E%3Cpath d='M9 8h14v16H9zM12 13h8M12 17h8' fill='none' stroke='white' stroke-width='2'/%3E%3C/svg%3E"></head><body><div class="shell"><header class="header"><a class="name" href="/">Nathen</a><nav class="nav" aria-label="主导航">{nav}</nav></header><main id="main-content">{body}</main><footer class="footer"><span>© 2026 Nathen</span><span>学习、构建与记录。</span></footer></div></body></html>'''
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
posts=[('systems','分布式系统','membership','成员管理与故障检测','从心跳到 Gossip，理解分布式系统如何判断节点是否存活。',[('为什么需要成员管理','一个节点需要知道哪些同伴可以通信。成员管理维护这一视图，并处理节点加入、离开与故障。'),('故障检测的取舍','超时并不能证明节点已经故障。网络延迟和丢包也会造成误判。调整检测周期、超时与确认方式，需要平衡检测速度和误报率。'),('实验记录','记录实验环境、节点数量、注入的故障以及测量方式，才能比较不同配置的表现。')]),('systems','分布式系统','consistency','一致性与可用性的取舍','整理副本、一致性与网络分区之间的关系。',[('副本与读写','副本提高容错能力，也让不同节点可能在同一时刻看到不同数据。讨论一致性之前，需要明确读写如何传播。'),('网络分区','通信中断时，系统无法同时保证每个请求都成功响应和所有读写都符合线性一致性。设计需要针对具体业务选择行为。')]),('java','Java','threads','Java 并发学习笔记','理解线程、共享状态和同步机制。',[('共享状态','多个线程访问同一份可变数据时，需要关注可见性与原子性。一个简单的递增操作也可能包含多个步骤。'),('同步机制','synchronized 和锁可以保护临界区。缩小共享状态和临界区范围，通常比增加复杂同步逻辑更容易维护。')]),('notes','随笔','first-post','开始记录，慢慢积累','给这个个人空间的第一篇笔记。',[('为什么写下来','把一个问题写清楚，常常意味着重新梳理自己的理解。这里会保留学习过程中的问题、尝试和收获。'),('接下来','可以从一门课程、一个小项目或一次实验开始。每篇文章只需要讲清楚一个具体问题。')])]
groups='';cats=''
for cat,label in [('systems','分布式系统'),('java','Java'),('notes','随笔')]:
    cats+=f'<a href="#{cat}">{label}</a>'
    rows=''.join(f'<article class="row"><time datetime="2026-10-03">2026 年 10 月 3 日</time><h3><a href="/posts/{slug}/">{title}</a></h3></article>' for c,l,slug,title,desc,sections in posts if c==cat)
    groups+=f'<section class="group" id="{cat}"><h2>{label}</h2><div class="list">{rows}</div></section>'
page('博客','blogs',f'<p class="eyebrow">Writing & notes</p><h1>博客</h1><p class="lead">记录学习、项目与思考。</p><div class="directory"><nav class="categories" aria-label="文章分类"><span>文章分类</span>{cats}</nav><div>{groups}</div></div>','blogs/index.html')
page('首页','home','''<section class="intro"><p class="eyebrow">Learning & building</p><h1>你好，我是Nathen。</h1><p class="lead">在这里分享我的学习经历、项目实践，以及对技术和生活的思考。</p><a class="pill" href="/blogs/">阅读博客</a></section><section class="prose"><h2>关于我</h2><p>这里将放置你的个人简介、研究方向与兴趣。</p><h2>正在关注</h2><p>分布式系统、软件开发，以及把想法变成实际项目的过程。</p><h2>最新记录</h2><p><a href="/posts/first-post/">开始记录，慢慢积累</a></p></section>''','index.html')
page('项目','projects','''<p class="eyebrow">Selected work</p><h1>项目</h1><p class="lead">从想法到实现，记录构建的过程。</p><article class="panel"><h2>你的第一个项目</h2><p>这里将介绍项目解决的问题、你的贡献以及实现方法。</p><p class="note">待补充项目介绍与链接</p></article>''','projects/index.html')
for cat,label,slug,title,desc,sections in posts:
    content=''.join(f'<h2>{html.escape(h)}</h2><p>{html.escape(p)}</p>' for h,p in sections)
    page(title,'blogs',f'<a class="back" href="/blogs/#{cat}">返回博客</a><p class="eyebrow">{label}</p><h1>{title}</h1><p class="lead">2026 年 10 月 3 日 · 示例文章</p><article class="panel prose"><p>{desc}</p>{content}</article>',f'posts/{slug}/index.html')
