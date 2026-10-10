# P2P System

## p2p

peer to peer 节点组织方式
每个节点可以请求、提供、转发数据

# Gnutella 

## 1. 核心思想

Napster：
> 文件存在 Peer
> 文件索引存在中央 Server
> 问题：Server bottleneck + single point of failure

Gnutella：
> **No central server**
> 每个 Peer 同时是 Client + Server → **Servent**
> Peers 组成 **Overlay Graph**
> 每个 Peer 保存自己的文件和 neighbor 信息

---

## 2. 数据结构

完全二叉树$ N=2^m-1 $ N为节点数, $m-1$ 为层数量 $[0:m-1]$
$TTL\ge \max_v distance(s,v)$ $  TTL_{\min} = \max_{u,v} distance(u,v)  $
distributed system trade-off: 更多的连接=更短的routing path,更多 connection state
child可以沿着parent向上routing

---

## 3. 假设 $A \longleftrightarrow B$ 建立connection什么是connection state

ID信息: IP Address/port
连接状态: 正在连接/关闭了, 超时计数器
协议状态: 数据发到百分之多少了, 缓冲区是否有消息等待发送

---

## 4. 五种 Message

| Message  | 作用            | 路由方式                  |
| -------- | --------------- | ------------------------- |
| Query    | 搜索文件        | Flooding                  |
| QueryHit | 返回搜索结果    | Reverse Path              |
| Ping     | 寻找/维护 Peers | Flooding                  |
| Pong     | 回复 Ping       | Reverse Path              |
| Push     | 处理 Firewall   | Reverse Path 到 responder |

> Query ↔ QueryHit：找文件
> Ping ↔ Pong：维护 Neighbor
> Push：解决 Firewall

---

## 5. Query / Flooding

### Gnutella &flooding&TTL&hop

不知道就问peer,peer不知道就问peer的peer,如果每个patent都有两个child,这是一个二叉树
一个一个领居接着问是泛洪
TTL = time to live 如果system有环就会无限泛洪,所以需要引入hop限制步数
hop 可以理解为一步
Gnutella 本质是个图论问题

![Screenshot 2026-10-07 at 15.22.36](/images/p2p/d3df6a1e967f.png)搜索文件时：A → neighbors → neighbors → ...
规则：

1. Query 发给所有 neighbors，除了发送给自己的那个 Peer
2. 每个 Query 有唯一 **DescriptorID**
3. 相同 DescriptorID 的 Query 第二次收到 → **Drop**
4. 防止重复 Flooding

---

## 6. TTL

TTL = Query 最多还能传播多少个 hop
每经过一个 Peer：TTL = TTL - 1
TTL = 0：不再继续 Forward
所以：**TTL ↑ → 搜索范围 ↑ → 找到文件概率 ↑ → Message Overhead ↑**

---

## 7. 策略

原路返回数据,相同ID后收到的丢弃,以牙还牙给提供好下载速度的节点提供上传速度

### QueryHit

![image-20261007152302132](/images/p2p/8a485050c283.png)

如果某 Peer 找到文件：
Query：A → B → C → D
QueryHit：A ← B ← C ← D
即：**QueryHit 沿 Query 的 Reverse Path 返回**
QueryHit 包含：IP, Port, File information, Servent ID

### 文件下载

QueryHit 回到 Requestor 后：Requestor → Responder
直接建立 **TCP / HTTP** 连接下载。

> **文件不会沿 Query/QueryHit 的 Overlay Path 传输。**
> 搜索走 Gnutella Overlay；
> 真正文件传输是 Peer-to-Peer Direct Connection。

### Firewall + Push

正常：Requestor → Responder
如果 Responder 在 Firewall 后：Requestor 无法主动连接 Responder。

解决：

1. Requestor 发送 **Push**
2. Push 到达 Responder
3. Responder 主动建立 TCP：Responder → Requestor

4. Requestor 再发送 HTTP GET
5. 开始文件传输

记：**谁在墙里，谁主动往外建立tcp连接。**

---

## 8. Ping / Pong

目的：**更新 Neighbor List**
因为 Peer 会不断：Join, Leave, Fail

流程：
Ping → Flooding
Pong → Reverse Path

> Pong 包含：IP, Port, Number of files shared, KB shared

---

## 9. Gnutella 防止流量爆炸

**Duplicate**
相同：DescriptorID + Message Type   再次收到 → **Drop** (QueryHit 和 Pong没有这个机制,只有Query和Ping有)
**TTL**
限制 Flooding 最大距离。

---

## 10. Gnutella Problems

**Flooding**: 搜索产生大量 Message。
**Ping/Pong**:曾占大量网络 Traffic。
**Repeated Query**: 相同关键词反复搜索。
解决：Cache Query / QueryHit
**Freeloader**: 只下载，不上传文件。

---

## 11. Summary

Gnutella：**No Server + Overlay Graph + Flooding**
搜索：

> Query → Flooding  
> QueryHit → Reverse Path

维护 Peer：

> Ping → Flooding  
> Pong → Reverse Path

防火墙：

> Push → 让 Firewall 内的 Responder 主动连接 Requestor

控制 Flooding：

> TTL + DescriptorID 去重

最大问题：

> **Flooding → O(N) Message Overhead**






# BitTorrent 

## 1.  Blocks/shard

Block-based 可以从多个 peer **并行下载**不同 block，从而获得 parallelism、load balancing 和更好的 availability。  
如果整个文件只能从一个 peer 下载，就无法利用其他 peer 的上传带宽，速度受单个 peer 限制，而且该 peer 离开或失败会中断下载。

## 2. Rarest-First

BitTorrent 将文件拆成多个 block/shard，并可以从不同 peer 下载。 **优先下载当前最稀有的 block**。  
$$
availability(x)=\text{拥有 block }x\text{ 的 peer 数}
$$
选择：
$$
\arg\min_x availability(x)
$$
目的：优先复制稀有 block，避免持有它的 peer 离开后该 block 消失，从而导致整个文件无法恢复。

## 3. Most-Common-First 的问题

如果优先下载最常见的 block，稀有 block 会长期得不到复制；一旦持有稀有 block 的 peer 离开：
$$
availability(rare)=0
$$
即使其他 block 有很多副本，完整文件仍无法恢复。  **文件可用性受最稀有 block 限制。**

## 4. 分析方法

统计每个 block 的副本数 → rarest-first 选择最少的 → tie 按题目规则处理。  
新增 peer 时，只更新它所拥有 block 的 $availability$，然后重新比较。

## 5. Peer-to-Peer file sharing&BitTorrent&shard

Parallelism: 不单个服务器作为瓶颈,每个peer都承担download和upload的任务
Load distributionFile切成shard本使得文件分散,进行并行传播和并行下载,利用别的节点的空闲带宽,是一种多对多,one download one upload in swarm,分散上传压力
Better availability: Rarest-First 防止断电找不到数据

## 6. Rarest-First下载 VS Most- common- first下载

文件不完整: 优先下载在系统里副本最少的shard,因为如果出现意外下线,就丢失掉了这个topic,有可能永远拿不到完整的文件
availability:  目的是提高rare shard availability,让shard distribution更均匀从而降低某个shard消失的风险
BitTorrent优势是parallelism: 因为备份有传播效应,所以原来已经common的会更common所以要下载rare让所有的均衡,防止single-peer bottleneck



# Chord 与 Kelips

## 1. Chord

Chord Ring 的ID space: $2^m$(并不一定1 ID to 1 Machine 可以没有对应的node)
Node: 指的是在finger table的点

### 1. successor 与  consistent hashing ring 与Finger Table

本质上是一种映射,当要找的node找不到时,就像指针一样,顺时针找下一个node, 最基本是一种$O(N)$的链表,然后引出Finger Table
Finger Table: 从认识的 Node 里面，找一个最接近目标、但还没有超过目标的 Node，然后跳过去。
$$
start_i=(n+2^{i-1})\bmod 2^m
$$

$$
finger[i]=successor(start_i)
$$


时间$O(\log N)$ 按照$2^0,\ 2^1,\ 2^2,\ 2^3,\ldots$建立finger table, 所以每次跳跃每次缩小一半的距离

<img src="/images/p2p/chord-ring.png" alt="Distributed caching strategies & sharding techniques for high performance" style="zoom:50%;" />

![Screenshot 2026-10-04 at 22.33.06](/images/p2p/6010b0cc994b.png)

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

###  2. Chord Routing 的原则与跳法

closest preceding finger: 从 finger table 里选择一个最大的、但还没有超过 key 的 node。如果所有的node in finger table都超过k,说明要找自己的successor了.
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

### 3. Key hash

```
key       = "cat.jpg"     ← 我是谁
value     = 猫图片         ← 我的东西
hash(key) = 4             ← 我的地址编号
Node 5                    ← 最终住的机器
```

Hash 决定的是key在什么位置而不是key的value不要搞混,hash是吧图片变成数字,再用数字去决定放在哪个机器

### 4.性质

时间复杂度是logN本质是每次接近目标一半,如果中间节点挂了就指向finger table的下一个,如果目标节点挂了就在两个领居node上备份key或者file,新加入的node的successor的key 所有权会发生变化因为new node接管了predecessor部分传过来的key

<img src="/images/p2p/e0b68515376c.png" alt="Screenshot 2026-10-07 at 19.29.14" style="zoom:40%;" />

## 2. Kelips

<img src="/images/p2p/b8edd2750c6b.png" alt="image-20261007192209028" style="zoom:50%;" />

### 1. Affinity Group

- 将 $N$ 个 nodes 分成 $k$ 个 **Affinity Groups**：

$$
k \approx \sqrt{N}
$$

​	Node 通过 `hash mod k` 决定所属 group。

- 每个 node 保存：自己 group 中几乎所有 nodes。其他每个 group 的一个 **contact node**。因此用更多 neighbor 信息换取更快的 lookup。

### 2. File & Metadata

- 文件本身可以存在任意少数 nodes 上，Kelips 主要负责 **file lookup**。
- Filename 通过 hash 映射到一个 Affinity Group。
- 该 group 保存文件的 metadata：`<filename, file location>`
- **文件位置与查询 metadata 分离**，Affinity Group 不一定真正存储文件。

###  3. Lookup

`filename → hash → Affinity Group → contact node → file location`

- 每个 node 都有其他 group 的 contact，因此通常可以直接找到目标 group。
- **Lookup cost：1 hop（失败时可能 few hops）**
- **Memory cost：**

$$
O(\sqrt{N})
$$

### 4. Soft State

- Membership 使用 **Gossip** 在 group 内和 group 间传播：

$$
O(\log N) \text{ dissemination time}
$$

- Soft State 核心：**不断刷新则保留，不刷新则自动过期**。File metadata 需要 source node **周期性 refresh**。长时间没有 refresh → metadata **timeout**。

### 5. Chord vs. Kelips

- **Chord**：

$$
Memory = O(\log N), \quad Lookup = O(\log N)
$$

​	**Kelips**：
$$
Memory = O(\sqrt{N}), \quad Lookup \approx 1\ hop
$$

​	核心 tradeoff：
$$
Memory \leftrightarrow Lookup\ Cost \leftrightarrow Background\ Bandwidth
$$

- **Chord**：保存信息少，但 lookup 多跳。
  **Kelips**：保存更多信息并用 Gossip 维护 freshness，但 lookup 更快。

### 6. P2P 总结

- 实际广泛使用：**Napster / Gnutella / BitTorrent**
- 具有可证明性质的 P2P：**Chord / Kelips**

### 7. 核心要点

$$
k \approx \sqrt{N}
$$

$$
Memory = O(\sqrt{N})
$$

$$
Lookup \approx 1\ hop
$$

Kelips 本质：**用更多 Memory 和 Background Bandwidth 换更低的 Lookup Cost。**


# Key-Value Store

sql:有内键外键
no-sql
CAP Tradeoff
c: Consistency
a: Availability
p: Partition-tolerance

Eventual Consistency最终一致性
可能读到旧数据,因为写入的数据还没异步传播到对应服务器上

<img src="/images/p2p/d9cd2bb05b0b.png" alt="Screenshot 2026-10-05 at 16.44.26" style="zoom:50%;" />

Strong Consistency强一致性
有分布式锁,把并行变成串行,一定有任务顺序

<img src="/images/p2p/d9d6dd861cb5.png" alt="image-20261008102232778" style="zoom:50%;" />

Causal Consistency因果一致性
看见就一定要改,不看见可以不改

<img src="/images/p2p/fb8b6eba764a.png" alt="Screenshot 2026-10-05 at 16.49.33" style="zoom:50%;" />

HBase
<img src="/images/p2p/bebdf0443d47.png" alt="Screenshot 2026-10-05 at 17.20.42" style="zoom:50%;" />







# Bloom Filter

hash collision: 数据可能存在但是是别人的
Bloom Filter: 用多个hash操作一个字符串,并相乘如果全为1则maybe present,如果为0就definitely not present,可能假阳性但是一定不会假阴性

<img src="/images/p2p/df3c618dd8cb.png" alt="image-20261007162957167" style="zoom:50%;" />

## Bloom Filter — FPR
设：$m=\text{bits},\ k=\text{hash 数},\ n=\text{插入元素数}$  
## 1. 核心公式
一个 bit 为 1 的概率：  
$$
p=1-\left(1-\frac{1}{m}\right)^{kn}\approx1-e^{-kn/m}
$$
False Positive Rate：  
$$
FPR=p^k
$$
直觉：$n\uparrow \Rightarrow \text{bit 更满} \Rightarrow FPR\uparrow$

## 2. 多个独立 Filter
若单个 filter 的 False Positive 概率为 $p$：  
**ALL：** $P(FP)=p^k$  
**ANY：** $P(FP)=1-(1-p)^k$  
记忆：**ALL = 全部发生；ANY = 1 - 全部不发生**

## 3. Q4
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

## 4. Performance
**ALL：** 遇到 `False` → stop  
**ANY：** 遇到 `True` → stop  
都支持 **short-circuit**；实际性能还取决于 **memory access / separate filters**。



# Cassandra

## 1. Cassandra 基础

Cassandra 是一个 **Distributed Key-Value Store（分布式键值存储）**。
基本数据形式：Key → Value
基本操作：

> `put(key, value)`：写入
> `get(key)`：读取

Cassandra 最初由 Facebook 设计，受到 Amazon Dynamo 的影响，后来成为 Apache 项目。
核心目标：分布式存储大量数据、支持大量随机读写、高可用、Scale-out：通过增加机器扩展系统，而不是升级单台机器

---

## 2. Key → Server Mapping

Cassandra 使用 **Ring-based DHT** 决定一个 Key 存在哪些服务器。
Key 经过 hash 后得到 Ring 上的位置，然后找到对应的服务器。
与 Chord 的区别：Cassandra 用更多 memory 保存 membership，换取更少的 routing hops。
Chord：

> 使用 Finger Table
> 每个节点只知道部分节点
> 查找通常需要多跳

Cassandra：
> 不使用 Finger Table
> 每个节点保存 **Full Membership List**
> 可以直接找到负责 Key 的节点

---

## 3. Replication

<img src="/images/p2p/2936d2773735.png" alt="Screenshot 2026-10-05 at 15.36.46" style="zoom:40%;" />

一个 Key 不只存储在一台机器，而是保存多个副本（Replica）。例如：
K13 → N16：Primary Replica
K13 → N32：Backup Replica
K13 → N45：Backup Replica
目的：如果一个节点发生故障，其他 Replica 仍然保存数据。

### NetworkTopologyStrategy

Cassandra 可以根据物理网络拓扑放置 Replica。
Topology：Datacenter → Rack → Machine
Cassandra 使用 **Snitch** 判断 IP 属于哪个 Rack 和 Datacenter。
eplica 可以放在不同 Rack，避免一个 Rack 故障导致所有副本同时失效。

---

## 4. Coordinator

Client 不需要自己联系所有 Replica。
Client 首先把请求发送给一个 Cassandra Node，这个节点作为：
**Coordinator**
流程：Client → Coordinator  → 找到负责 Key 的 Replicas  → R1 / R2 / R3
任何 Cassandra Server 都可以成为 Coordinator。
Coordinator 负责组织这一次 Read / Write 请求。

---

## 5. Write

<img src="/images/p2p/7b1fb7806c47.png" alt="Screenshot 2026-10-07 at 19.47.45" style="zoom:50%;" />

基本写入流程：
Client → Coordinator → Responsible Replicas
Coordinator：

> 1 为 Write 分配 Timestamp
> 2 找到负责该 Key 的 Replicas
> 3 将 Write 发送给这些 Replicas
> 4 Replica 将数据写入本地存储

Timestamp 用来判断多个版本中哪个更新。
例如：K13 → (V1, timestamp=10)

---

## 6. Hinted Handoff

如果某个 Replica 暂时 Down：

> R1 ✓
> R2 ✓
> R3 ✗

Coordinator 不需要停止整个 Write。它可以：

> 1 正常写入其他 Replica
> 2 暂时保存 R3 缺失的 Write
> 3 等 R3 恢复
> 4 将缺失的数据发送给 R3

这叫：**Hinted Handoff**
作用：提高 Availability，使 Replica 暂时故障时系统仍然可以继续写入。

---

## 7. Read

<img src="/images/p2p/3d56389b021f.png" alt="Screenshot 2026-10-07 at 19.48.57" style="zoom:50%;" />

Read 与 Write 类似。Coordinator 从多个 Replica 获取数据。例如：
R1: K13 → V1, timestamp=10
R2: K13 → V0, timestamp=9
R3: K13 → V1, timestamp=10
Coordinator 根据 Timestamp 选择最新版本：V1, timestamp=10
因此：**Latest Timestamp → Latest Value**

---

## 8. Read Repair

<img src="/images/p2p/5029e1f31c71.png" alt="Screenshot 2026-10-07 at 19.49.21" style="zoom:50%;" />

读取时如果发现 Replica 数据不一致：
R1 = V1,10
R2 = V0,9
R3 = V1,10
Coordinator 可以发现：R2 保存的是旧数据。
然后在后台将：R2: V0,9 → R2: V1,10
这叫：**Read Repair**
作用：让不同 Replica 最终逐渐恢复一致。

---

## 9. Eventual Consistency

Cassandra 允许不同 Replica 在短时间内保存不同版本。例如：
R1 = V2
R2 = V2
R3 = V1
之后通过：Hinted Handoff、Read Repair
逐渐变成：
R1 = V2
R2 = V2
R3 = V2
这叫：**Eventual Consistency（最终一致性）**
含义：如果停止对一个 Key 继续写入，它的所有 Replica 最终会收敛到相同值。但在收敛之前，Read 可能暂时读到旧数据（Stale Value）。
Cassandra 更偏向：**Availability + Partition Tolerance**, 而不是始终要求 Strong Consistency。

---

## 10. Membership

Cassandra 每个 Server 保存：**Full Membership List** , 也就是知道 Cluster 中其他服务器的信息。
Cassandra 使用：**Gossip Protocol**
传播 Membership 信息，例如：Node Join、Node Leave、Node Failure

---

## 11. Failure Detection

Cassandra 使用 Heartbeat 风格的 Failure Detector：
**Φ Accrual Failure Detector**
根据网络情况判断一个 Node 是否可能发生故障。
Cassandra 使用 **Fail-Recover Model**：
Node Failure → 标记 DOWN → 不直接永久删除 → Node 恢复后重新标记 UP
因为 Cassandra 假设机器可能只是暂时故障，之后还会恢复。

---

## 12. Local Storage

当 Replica 收到 Write：Write → Commit Log → Memtable

### Commit Log

Write 首先记录到磁盘上的 Commit Log。作用：
**Failure Recovery**
如果机器 Crash，可以根据 Commit Log 恢复数据。

### Memtable

然后数据写入：**Memtable**
Memtable 是：**In-Memory Key-Value Data Structure** 也就是存储在 RAM 中。
因此 Cassandra 不需要每次 Write 都先从磁盘查找旧数据。
Write Path：Write → Commit Log → Memtable
Cassandra 的本地存储使用：**LSM Tree（Log-Structured Merge Tree）**核心目标是让 Write 尽量避免昂贵的 Disk Seek。

---

## Cassandra 总流程

Client → Coordinator → Ring 找到负责 Key 的节点 → 多个 Replicas → Read / Write
核心机制：

>**Ring-based DHT**：决定 Key 存在哪里
>**Full Membership List**：直接知道其他节点
>**Replication**：保存多个副本
>**Snitch**：识别 Rack / Datacenter
>**Coordinator**：组织 Read / Write
>**Timestamp**：判断最新数据
>**Hinted Handoff**：处理暂时 Down 的 Replica
>**Read Repair**：修复旧 Replica
>**Eventual Consistency**：Replica 最终收敛
>**Gossip**：传播 Membership
>**Failure Detector**：判断节点 Down / Up
>**Commit Log**：故障恢复
>**Memtable**：内存中的 Key-Value 数据
>**LSM Tree**：优化本地写入





# Cassandra 与 Quorum Intersection

## 1. Cassandra Read / Write

- **CAP**: AP系统, 暂时牺牲强一致性, Eventual Consistency,  BASE 
- **Write**：Client → Coordinator → $N$ replicas；等 $X$ 个响应后 ACK。
- **Hinted Handoff**：Replica down → Coordinator 暂存 write → 恢复后补写。
- **Read**：读取 $X$ replicas → 返回 **latest timestamp** 的 value。
- **Read Repair**：发现旧 replica → 用最新 value 修复 → 最终一致。
- **Membership**：每个节点保存 **full membership list**；用 **Gossip** 传播 join / leave / fail。
- **Failure Detection**：Heartbeat-style $\Phi$ detector，根据网络动态判断 failure；节点只标记 **UP/DOWN**，不直接删除。
- **Quorum**：决定 Read / Write 需要等待多少 replicas。

## 2. CAP & Eventual Consistency

- **CAP**：C = latest data，A = requests keep responding，P = network partition 下继续运行；发生 partition 时通常在 **C / A** 间取舍。
- Cassandra 偏 **AP**，采用 **Eventual Consistency**：replicas 可暂时不一致，停止写后最终收敛；期间可能读到 stale value。
- Cassandra 更偏 **BASE**；传统 RDBMS 更强调 **ACID**。

## 3. Quorum Intersection 原理

**Quorum**：完成一次操作所要求参与的一组节点，核心是保证不同操作的节点集合存在 **intersection**。
**$N$**：系统中**总共有多少个 process / node**。
**$M$**：**每一个 quorum 里面有多少个节点**。
**$r$**：题目要求所有 quorum **至少共同拥有多少个节点**。
**$k$**：一共有**多少个 quorum**。

### k 个 Quorum

共同的人=总人数 - 可能被排除的人

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

## 4. Cassandra Quorum

- **N** = replica 总数，**R** = read 等待数，**W** = write 等待数。
- Read：等 R 个响应 → 返回 **latest timestamp**；Write：等 W 个完成 → **ACK**。
- 一致性条件：
$$
R+W>N
$$
$$
W>N/2
$$
- **Quorum = majority (>50%)**，保证集合相交。
- 大 W / 小 R → read-heavy；小 W / 大 R → write-heavy。
- $R=W=1$ → 高 Availability、可能 stale；Quorum / 大 W → Consistency 更强但 Availability 更低。
- 若 Read / Write 都用 **QUORUM**，则 $R+W>N$，read quorum 必与之前成功的 write quorum 相交，因此 **任何 client** 的后续 read 都能看到该 write 或更新的 value。

## 5. Cassandra Consistency Levels

- **ANY**：任意 server，最快。
- **ONE**：1 个 replica。
- **QUORUM**：多数 replicas。
- **ALL**：全部 replicas，最慢最严格。
- 多 DC：**QUORUM** = 全部 DC 合起来多数；**LOCAL_QUORUM** = 本地 DC 多数；**EACH_QUORUM** = 每个 DC 都达到多数.

## 6. Replica Local Storage

- Write Path

核心思想：**顺序写，不原地修改磁盘，之后统一 Compaction。**
$$
\text{Write Fast Now, Compact Later}
$$

$$
\text{Write}\rightarrow\text{Commit Log}+\text{Memtable}\rightarrow\text{Flush}\rightarrow\text{SSTable}
$$

​	**Commit Log (Disk)**：顺序追加，保证 durability。

​	**Memtable (RAM)**：快速写入，满后 flush。

​	**SSTable (Disk)**：immutable，不原地修改。
Update 直接写新版本，通过 timestamp/version 选择最新值：

```
Old: B → 20
New: B → 99
```

- **Compaction**

合并多个 SSTable，删除过期版本：

```
B→20, B→30, B→50  →  B→50
```

- **Tombstone**

DELETE 不物理删除，而是写：

```
B → TOMBSTONE
```

原因：**SSTable immutable + 防止旧 replica 让删除数据复活**。Tombstone 是带 timestamp 的 delete update，最终由 Compaction 清理。

- **Bloom Filter**

definitely not present → 不读 SSTable
maybe present → 读 SSTable
对于用key比对,bloom filter会更省store,但是会出现false positive,不能determine exactly
作用：**减少无效 SSTable disk I/O，提高 read performance。**

- **Full Membership vs Finger Table**

Chord finger table 需要：
$$
O(\log N)\text{ routing hops}
$$
Cassandra 保存 full membership，可以更直接找到目标 replica：
$$
\text{More Metadata}\Longleftrightarrow\text{Fewer Routing Hops}
$$
即：**用更多 membership metadata 换更低 routing latency。**

- **一条线记住**

```
Write → Commit Log + Memtable → Flush → SSTable
                                  ↓
                     Bloom Filter / Compaction

Delete → Tombstone → Compaction
```

## 7. ring&routing

主副本: 在环上按顺时针方向寻找，第一个大于等于其哈希值的节点
备份副本：在分布式系统（如复制因子为 $r$）中，数据会被同时复制到主副本及其后面的 $r-1$ 个顺时针后继节点上。
Cassandra 基于环 DHT，没有使用Finger Table，每个节点都保存着Full membership list,只要1跳就行

<img src="/images/p2p/2936d2773735.png" alt="Screenshot 2026-10-05 at 15.36.46" style="zoom:40%;" />





# Lamport Clock

<img src="/images/p2p/9b00377381e3.png" alt="Screenshot 2026-10-04 at 15.28.29" style="zoom:30%;" />

## 1. Happened-Before

$A\rightarrow B$：A 在因果关系上发生于 B 之前。

### 三种情况

- 同一 Process：前面的事件 $\rightarrow$ 后面的事件
  Message：$send\rightarrow receive$
  传递性：$A\rightarrow B,\ B\rightarrow C\Rightarrow A\rightarrow C$

### Concurrent

如果：
$$
A\nrightarrow B,\quad B\nrightarrow A
$$
则 A、B concurrent（没有可证明的因果关系）。

## 2. Lamport Clock 规则

### Local / Send

$$
L=L+1
$$
Send 时把当前 $L$ 放进 message。

### Receive

收到 message timestamp $T_m$：
$$
L=\max(L,T_m)+1
$$

## 3. 核心性质

$$
A\rightarrow B\Rightarrow L(A)<L(B)
$$
但反过来不成立：
$$
L(A)<L(B)\not\Rightarrow A\rightarrow B
$$
**所以 Lamport Clock 不能判断两个事件是否 concurrent。**

## 4. 初始值

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








# Vector Clock

<img src="/images/p2p/d0b094213be7.png" alt="Screenshot 2026-10-04 at 15.27.04" style="zoom:40%;" />

## 1. 核心

Lamport Clock：
$$
A\rightarrow B \Rightarrow L(A)<L(B)
$$
但不能反推，所以无法判断 concurrency。Vector Clock 用一个向量记录各 process 的 causal history：
$$
V=[v_1,v_2,\dots,v_N]
$$

## 2.更新规则

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
**merge knowledge → 记录 receive event**。

## 3.判断 Causality

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

## 4. Lamport vs Vector

|                 | Lamport  | Vector                      |
| --------------- | -------- | --------------------------- |
| Timestamp       | Integer  | Vector                      |
| Receive         | $\max+1$ | element-wise max，再自己 +1 |
| 判断 causality  | 不能反推 | 可以                        |
| 判断 concurrent | 不可以   | 可以                        |
| Space           | $O(1)$   | $O(N)$                      |

**Lamport 只能给顺序；Vector 能判断因果和并发。**
