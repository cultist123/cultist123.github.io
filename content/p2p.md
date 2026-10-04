# P2P System

##### p2p

peer to peer 节点组织方式
每个节点可以请求、提供、转发数据

#### Lesson 1 - Gnutella 找数据

##### 1. Gnutella &flooding&TTL&hop

不知道就问peer,peer不知道就问peer的peer,如果每个patent都有两个child,这是一个二叉树
一个一个领居接着问是泛洪
TTL = time to live 如果system有环就会无限泛洪,所以需要引入hop限制步数
hop 可以理解为一步
Gnutella 本质是个图论问题

##### 2. 数据结构

完全二叉树$ N=2^m-1 $ N为节点数, $m-1$ 为层数量 $[0:m-1]$
$TTL\ge \max_v distance(s,v)$ $  TTL_{\min} = \max_{u,v} distance(u,v)  $
distributed system trade-off:更多的连接=更短的routing path,更多 connection state
child可以沿着parent向上routing

##### 3. 假设 $A \longleftrightarrow B$ 建立connection什么是connection state

ID信息: IP Address/port
连接状态: 正在连接/关闭了, 超时计数器
协议状态: 数据发到百分之多少了, 缓冲区是否有消息等待发送



#### Lesson 2 - BitTorrent 拿数据

##### 1. Peer-to-Peer file sharing&BitTorrent&shard

Parallelism: 不单个服务器作为瓶颈,每个peer都承担download和upload的任务
Load distributionFile切成shard本使得文件分散,进行并行传播和并行下载,利用别的节点的空闲带宽,是一种多对多,one download one upload in swarm,分散上传压力
Better availability: Rarest-First 防止断电找不到数据

##### 2. Rarest-First下载 VS Most- common- first下载

优先下载在系统里副本最少的shard,因为如果出现意外下线,有可能永远拿不到完整的文件
目的是提高rare shard availability,让shard distribution更均匀从而降低某个shard消失的风险
因为备份有传播效应,所以原来已经common的会更common所以要下载rare让所有的均衡



#### Lesson 3 - Chord

Chord Ring 的ID space: $2^m$(并不一定1 ID to 1 Machine 可以没有对应的node)

##### 1. successor 与  consistent hashing ring 与Finger Table

本质上是一种映射,当要找的node找不到时,就像指针一样,顺时针找下一个node, 最基本是一种$O(N)$的链表,然后引出Finger Table
Finger Table: 从认识的 Node 里面，找一个最接近目标、但还没有超过目标的 Node，然后跳过去。$start_i=(n+2^{i-1})\bmod 2^m$
$finger[i]=successor(start_i)$
时间$O(\log N)$ 按照$2^0,\ 2^1,\ 2^2,\ 2^3,\ldots$建立finger table, 所以每次跳跃每次缩小一半的距离

<img src="/images/p2p/chord-ring.png" alt="Distributed caching strategies & sharding techniques for high performance" style="zoom:50%;" />

```
step1
                    0  ← Node 0
                 ↗         ↘
              7               1
            ↗                   ↘
           6                     2  ← Node 2
            ↑                   ↓
              5               3
              ↑               ↓
            Node 5      ←     4

step2
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 0 → ...
↑       ↑           ↑
Node    Node        Node
0       2           5

step3
key = "cat.jpg"
hash("cat.jpg") = 4

step4
0 → 1 → 2 → 3 → [4] → 5 → 6 → 7 → 0
        ↑              ↑
      Node 2          Node 5

step5
位置 4 → 没有 Node！→ key 4 → Node 5
successor(4) = 5
```

#####  2. Chord Routing 的原则与跳法

closest preceding finger: 从 finger table 里选择一个最接近 key、但还没有超过 key 的 node。
算法: 在 Node \(n\)，如果：$ k\in(n, successor(n)] $
	那么 $successor(k)=successor(n) $直接结束。
	否则：$\text{forward to closest preceding finger}$
Node Failure : 凡是 finger table 中指向 failed node 的节点，都需要更新

```
我要找 key k

        ↓

k 是否在 (current, successor]？

     /             \
   YES              NO
    |                |
    ↓                ↓
successor就是答案    finger table里
                     找最接近k但
                     没超过k的node
                          |
                          ↓
                       跳过去
                          |
                          ↺
```

##### 3. Key hash

```
key       = "cat.jpg"     ← 我是谁
value     = 猫图片         ← 我的东西
hash(key) = 4             ← 我的地址编号
Node 5                     ← 最终住的机器
```

Hash 决定的是key在什么位置而不是key的value不要搞混,hash是吧图片变成数字,再用数字去决定放在哪个机器



#### Key-Value Store

#### Lesson 4 - Bloom Filter

hash collision: 数据可能存在但是是别人的
Bloom Filter: 用多个hash操作一个字符串,并相乘如果全为1则maybe present,如果为0就definitely not present,可能假阳性但是一定不会假阴性

##### Bloom Filter — FPR
设：$m=\text{bits},\ k=\text{hash 数},\ n=\text{插入元素数}$  
##### 1. 核心公式
一个 bit 为 1 的概率：  
$$
p=1-\left(1-\frac{1}{m}\right)^{kn}\approx1-e^{-kn/m}
$$
False Positive Rate：  
$$
FPR=p^k
$$
直觉：$n\uparrow \Rightarrow \text{bit 更满} \Rightarrow FPR\uparrow$

##### 2. 多个独立 Filter
若单个 filter 的 False Positive 概率为 $p$：  
**ALL：** $P(FP)=p^k$  
**ANY：** $P(FP)=1-(1-p)^k$  
记忆：**ALL = 全部发生；ANY = 1 - 全部不发生**

##### 3. Q4
**Original Bloom：** $m=1024,\ k=4$  
$$
FPR=\left[1-\left(1-\frac{1}{1024}\right)^{4n}\right]^4
$$
**Leo：** 4 个独立 filter，每个 $m=256,\ k=1$  
单个 filter：
$$
p=1-\left(1-\frac{1}{256}\right)^n
$$
Leo-all：$FPR=p^4$  
Leo-any：$FPR=1-(1-p)^4$  
Original $\approx$ Leo-all，因为 $\frac{4n}{1024}=\frac{n}{256}$。

##### 4. Performance
**ALL：** 遇到 `False` → stop  
**ANY：** 遇到 `True` → stop  
都支持 **short-circuit**；实际性能还取决于 **memory access / separate filters**。



#### Lesson 5 - Quorum Intersection

**Quorum**：完成一次操作所要求参与的一组节点，核心是保证不同操作的节点集合存在 **intersection**。

##### 1. 两个 Quorum

对于 $N$ 个节点，每个 quorum 大小为 $M$：
$$
|Q_1\cap Q_2|\ge 2M-N
$$
若要求至少 $r$ 个共同节点：
$$
2M-N\ge r
$$
所以：
$$
M_{\min}=\left\lceil\frac{N+r}{2}\right\rceil
$$
当 $r=1$ 时：
$$
M_{\min}=\lfloor N/2\rfloor+1
$$
即 **Majority Quorum（超过一半）**。

##### 2. k 个 Quorum

每个 quorum 排除 $N-M$ 个节点，$k$ 个 quorum 最坏排除：
$$
k(N-M)
$$
因此共同交集至少为：
$$
|Q_1\cap\cdots\cap Q_k|\ge N-k(N-M)=kM-(k-1)N
$$
若要求至少 $r$ 个共同节点：
$$
kM-(k-1)N\ge r
$$
所以：
$$
M_{\min}=\left\lceil\frac{(k-1)N+r}{k}\right\rceil
$$
三个 quorum 是特例：
$$
M_{\min}=\left\lceil\frac{2N+r}{3}\right\rceil
$$
核心思想:每个 quorum 能排除 $N-M$ 个节点；$k$ 个 quorum 最坏排除 $k(N-M)$ 个不同节点；**剩下没被任何 quorum 排除的节点，就是共同 intersection。**
注意：
$$
\text{Pairwise Intersection}\neq\text{Common Intersection}
$$
**两两相交不能保证所有集合存在共同节点。**





#### Lesson 6 - Cassandra

核心思想：**顺序写，不原地修改磁盘，之后统一 Compaction。**
$$
\text{Write Fast Now, Compact Later}
$$

##### 1. Write Path

$$
\text{Write}\rightarrow\text{Commit Log}+\text{Memtable}\rightarrow\text{Flush}\rightarrow\text{SSTable}
$$

- **Commit Log (Disk)**：顺序追加，保证 durability。
- **Memtable (RAM)**：快速写入，满后 flush。
- **SSTable (Disk)**：immutable，不原地修改。
  Update 直接写新版本，通过 timestamp/version 选择最新值：

```
Old: B → 20
New: B → 99
```

##### 2. Compaction

合并多个 SSTable，删除过期版本：

```
B→20, B→30, B→50  →  B→50
```

##### 3. Tombstone

DELETE 不物理删除，而是写：

```
B → TOMBSTONE
```

原因：**SSTable immutable + 防止旧 replica 让删除数据复活**。Tombstone 是带 timestamp 的 delete update，最终由 Compaction 清理。

##### 4. Bloom Filter

```
definitely not present → 不读 SSTable
maybe present → 读 SSTable
```

作用：**减少无效 SSTable disk I/O，提高 read performance。**

##### 4. Full Membership vs Finger Table

Chord finger table 需要：
$$
O(\log N)\text{ routing hops}
$$
Cassandra 保存 full membership，可以更直接找到目标 replica：
$$
\text{More Metadata}\Longleftrightarrow\text{Fewer Routing Hops}
$$
即：**用更多 membership metadata 换更低 routing latency。**

##### 5. 一条线记住

```
Write → Commit Log + Memtable → Flush → SSTable
                                  ↓
                     Bloom Filter / Compaction

Delete → Tombstone → Compaction
```



#### Lesson 7 - Lamport Clock

<img src="/images/p2p/lamport-clock.png" alt="Screenshot 2026-10-04 at 15.28.29" style="zoom:30%;" />

##### 1. Happened-Before

$A\rightarrow B$：A 在因果关系上发生于 B 之前。

###### 三种情况

- 同一 Process：前面的事件 $\rightarrow$ 后面的事件
- Message：$send\rightarrow receive$
- 传递性：$A\rightarrow B,\ B\rightarrow C\Rightarrow A\rightarrow C$

###### Concurrent

如果：
$$
A\nrightarrow B,\quad B\nrightarrow A
$$
则 A、B concurrent（没有可证明的因果关系）。

##### 2. Lamport Clock 规则

###### Local / Send

$$
L=L+1
$$
Send 时把当前 $L$ 放进 message。

###### Receive

收到 message timestamp $T_m$：
$$
L=\max(L,T_m)+1
$$

##### 3. 核心性质

$$
A\rightarrow B\Rightarrow L(A)<L(B)
$$
但反过来不成立：
$$
L(A)<L(B)\not\Rightarrow A\rightarrow B
$$
**所以 Lamport Clock 不能判断两个事件是否 concurrent。**

##### 4. 初始值

各 Process 可以从不同值开始，只要仍遵守：
$$
Local/Send:+1
$$
$$
Receive:\max(L,T_m)+1
$$
就仍保证：
$$
A\rightarrow B\Rightarrow L(A)<L(B)
$$






<img src="/images/p2p/vector-clock.png" alt="Screenshot 2026-10-04 at 15.27.04" style="zoom:40%;" />

#### Vector Clock

##### 1. 核心

Lamport Clock：
$$
A\rightarrow B \Rightarrow L(A)<L(B)
$$
但不能反推，所以无法判断 concurrency。Vector Clock 用一个向量记录各 process 的 causal history：
$$
V=[v_1,v_2,\dots,v_N]
$$

##### 2.更新规则

初始：
$$
[0,0,\dots,0]
$$
Local / Send：只增加自己的维度：
$$
V_i[i]++
$$
Send 时携带整个 vector。

Receive：先逐元素取 max：
$$
V_i[j]=\max(V_i[j],V_m[j])
$$
再增加自己的维度：
$$
V_i[i]++
$$
即：**merge knowledge → 记录 receive event**。

##### 3.判断 Causality

若：
$$
V(A)[i]\le V(B)[i],\quad \forall i
$$
且至少一维严格小于，则：
$$
A\rightarrow B
$$
例如：
$$
[1,2,3]<[2,2,5]
$$
如果两个 vector 互有大小：
$$
A\nless B,\quad B\nless A
$$
则：
$$
A\parallel B
$$
表示 concurrent。例如：
$$
[3,1,0]\parallel[2,4,0]
$$

##### 4. Lamport vs Vector

|                 | Lamport  | Vector                      |
| --------------- | -------- | --------------------------- |
| Timestamp       | Integer  | Vector                      |
| Receive         | $\max+1$ | element-wise max，再自己 +1 |
| 判断 causality  | 不能反推 | 可以                        |
| 判断 concurrent | 不可以   | 可以                        |
| Space           | $O(1)$   | $O(N)$                      |

**Lamport 只能给顺序；Vector 能判断因果和并发。**
