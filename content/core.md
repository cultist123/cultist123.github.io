# Core Theories & Architectures

#### distributed system

A distributed system is a collection of entities, each of which is autonomous, programmable, *asynchronous* *and* failure-prone, and which communicate through an unreliable communication medium.
Entity=a process on a device (PC, PDA/mobile device)
Communication Medium=Wired or wireless network
Our interest in distributed systems involves design and implementation, maintenance, algorithmics 



# MapReduce and Hadoop

MapReduce 是一种用于大规模数据处理的分布式计算模型：
$$Input → Map → Shuffle → Reduce → Output$$
**Map 负责并行处理，Shuffle 负责按 Key 重新组织数据，Reduce 负责聚合结果。**

## 1. MapReduce

### Map

Map 将输入转换成 `<key, value>`。
例如 WordCount：`hello world hello`
Map 输出：`<hello,1> <world,1> <hello,1>`
不同 Map Task 相互独立，因此可以并行执行。

### Shuffle & Reduce

Shuffle 的规则：**Same Key → Same Reducer** 相同 key 的数据会被送给同一个 Reducer
例如：`<cat,1> <dog,1> <cat,1>`
经过 Shuffle：`cat → [1,1]`    `dog → [1]`
然后 Reduce：`<cat,2>`    `<dog,1>`
因此 `reduce()` 的调用次数取决于 **distinct keys 的数量**，而不是 Map 输出记录数量。每一个不同的 key，调用一次 reduce()。

### Partition

系统通过 Partition Function 决定数据进入哪个 Reducer：
`hash(key) % number_of_reducers`
Map Output 会按照 Key 排序，Reducer 再 Merge 来自不同 Mapper 的数据。
Map 和 Reduce 之间存在 **Barrier**，保证 Reduce 获得完整的 Map 输出。

---

## 2. MapReduce 的典型应用

**WordCount**
`Map: word → <word,1>`
`Reduce: <word,[1,1,...]> → <word,count>`

**Reverse Web-Link**
如果 `<a,b>` 表示 `a → b`：`Map: <a,b> → <b,a>`
这样 Shuffle 后即可得到：`b → [所有指向 b 的网页]`

**Global Maximum / Percentage**
多个 Reducer 相互独立，不能直接共享全局状态。
因此全局统计通常需要第二个 MapReduce Job：`MR1 → 局部统计 → MR2 → 全局统计`
例如寻找最大 Word Count，可以让第二轮 Map 输出：`<1,(word,count)>`
所有记录 Key 都是 `1`，因此会进入同一个 Reducer。 
Chain another MapReduce job after above one: 本质上是前一个mapreducer先聚合并行统计,之后再令key=1发到一个服务器进行global变量.

**Global Sort**

普通任务通常使用 Hash Partitioning；需要全局排序时使用 **Range Partitioning**，保证不同 Reducer 负责连续的数据范围。

---

## 3. Hadoop

MapReduce 描述计算模型，而 Hadoop 负责真正执行这些分布式任务。

<img src="/images/core/1a4bc512434d.png" alt="Screenshot 2026-10-06 at 20.29.23" style="zoom:40%;" />

整体数据流：$$ 原始输入 → DFS → Map → Local Disk → Shuffle → Reduce → DFS $$

- Map Input：Distributed File System
  Map Output：Local Disk
- Reduce Input：从多个 Mapper的Local Disk 获取
  Reduce Output：Distributed File System

常见 DFS 包括 **GFS** 和 **HDFS**。
用户主要编写 Map、Reduce 和 Partition Function；任务调度、数据传输和故障恢复由系统处理。

---

## 4. YARN

YARN（Yet Another Resource Negotiator）负责 Hadoop 的资源管理与任务调度。
Container 可以简单理解为：$$Container = CPU + Memory$$

- 三个核心组件：
  **Resource Manager（RM）**：Cluster, 负责整个集群的**资源管理和调度（scheduling）**
  **Node Manager（NM）**：Server, 每台机器上的管理者，负责启动/监控 container
  **Application Manager（AM）**：Job, 负责**某一个 application/job** 的执行和协调，会向 RM 申请资源
- 资源申请过程：$$AM → RM 请求资源 → RM 分配 Node → AM 请求 NM 启动 Task$$

---

## 5. Fault Tolerance

Node Manager 会持续向 Resource Manager 发送 **Heartbeat**。
如果服务器停止 Heartbeat：$Timeout → RM 检测故障 → 通知 AM → 在其他机器 Restart Task$
Task 本身失败也可以重新执行。
Reduce 输出通常采用：$Temporary File → 完成 → Rename$
避免重复执行的 Task 同时破坏最终输出。
AM Failure 可以由 RM 重启；RM Failure 可以通过 Checkpoint 和备用 RM 恢复。

---

## 6. Straggler

没有失败但运行异常慢的 Task 称为 **Straggler**。
一个 Straggler 可能因为 Barrier 拖慢整个 Job，因此可以使用 **Speculative Execution**：
$$ 原 Task 很慢 → 另一台机器运行副本 → 谁先完成用谁$$
本质是：**用额外计算资源减少慢节点造成的延迟。**

---

## 7. Data Locality

分布式计算中，移动大量数据的成本很高，因此 MapReduce 尽量：**Move computation to data.**
调度优先级：$$ Same Machine > Same Rack > Anywhere$$
HDFS/GFS 会保存多个数据 Replica，这既提高 Fault Tolerance，也增加了 Data Locality 的机会。

---

## 8.  Summary

设计 MapReduce 时最重要的问题是：**哪些数据需要放在一起处理？**
因为：$$Same Key → Same Reducer$$
所以通常按照：$$确定需要聚合的数据 → 设计 Key → Map → Shuffle → Reduce$$
例如 `(a,b)` 表示 `a follows b`，如果统计 b 的 followers：`Map: (a,b) → <b,a>`
Shuffle：`b → [a,c,d,...]`    Reduce：`<b, follower_count>`
因此 MapReduce 概括为：**Map 决定数据形式，Key 决定数据去哪里，Shuffle 完成分组，Reduce 完成聚合。**



# Gossip / Epidemic Multicast
Gossip（Epidemic Protocol）模仿信息传播：节点收到消息后，周期性随机选择其他节点继续传播。主要用于解决大规模分布式系统中的 **Multicast、Scalability 和 Fault Tolerance**。

## 1. Multicast
**Multicast**：将一条消息发送给一组节点。主要目标是 **Reliability、Speed、Scalability、Fault Tolerance**。
**Centralized Multicast** Sender 直接发送给所有节点，实现简单，但需要发送 $$O(N)$$ 条消息，Sender 容易成为瓶颈和单点故障。
**Tree-Based Multicast**: 节点组成 **Spanning Tree**，消息沿树传播。平衡树、固定 fanout 下传播时间约为：
$$
O(\log N)
$$
为了保证可靠性可以使用 **ACK / NAK**：
- **ACK**：确认收到
  **NAK**：通知未收到，请求重传
  SRM 使用 NAK，RMTP 使用 ACK，但仍可能产生 $$O(N)$$ 的 ACK/NAK 开销，而且需要维护树结构。

## 2. Gossip
Gossip 不维护固定传播路径。一个节点收到 multicast 消息,从uninfected变成infected , 一个拥有消息**infected node** 每轮随机选择 $$b$$ 个节点发送消息，新收到消息的节点继续周期性 Gossip传播。Gossip 消息使用 UDP 发送。节点分为：

- **Infected**：已经收到消息
  **Uninfected**：还没有收到消息
> **Random communication + repeated propagation → global dissemination**
> 主要特点：**Fast、Scalable、Fault-tolerant、Lightweight**。

<img src="/images/core/4d8fe1551986.png" alt="image-20261007114011154" style="zoom:50%;" />

## 3. Push / Pull Gossip

##### Push
拥有消息的节点主动发送给随机节点：$$Infected → Random Node$$
前期 infected 节点较少时效果很好；后期容易把消息重复发送给已经 infected 的节点。

##### Pull
节点主动询问随机节点是否拥有自己缺少的消息。后期 infected 节点很多时，uninfected 节点很容易 Pull 到消息。因此：
> **Push 前期更有效，Pull 后期更有效。**可以结合形成 **Push-Pull Gossip**。

## 4. Gossip 传播速度
假设每个 infected 节点每轮联系固定数量 `b` 个节点，感染节点数量近似：
$$ 1 → 2 → 4 → 8 → 16 → ...$$
因此传播到大量节点需要：
$$
O(\log N)
$$
定义 contact rate：
$$
\beta=\frac{b}{n}
$$
其中 $n$ 为系统规模，$b$为每轮随机选择的目标数。运行约：
$$
t=c\log N
$$
轮后，绝大多数节点已经收到消息。$log N$ 增长很慢，例如：$$log₂(1000)≈10，log₂(1M)≈20，log₂(1B)≈30。$$

<img src="/images/core/768b189dc847.png" alt="image-20261007114044820" style="zoom:50%;" />

## 5. Push vs. Pull
所有 Gossip 在前半段都至少需要：
$$
O(\log N)
$$
因为固定 fanout 的传播树也需要 $O(log N)$ 层才能覆盖约一半节点。
达到约 `N/2` 个 infected 节点后，**Pull 比 Push 更快**。设第 `i` 轮未感染比例为 $p_i$，每轮 Pull `k` 次：
$$
p_{i+1}=(p_i)^{k+1}
$$
未感染比例会 super-exponential 下降，因此 Pull 后半段约为：
$$
O(\log\log N)
$$
所以如果已经有约一半节点拥有消息：**选择 Pull。**
## 6. Fault Tolerance
Gossip 没有固定传播路径，因此丢包或部分节点故障不会直接切断传播。
##### Packet Loss
50% packet loss 可以近似看成：
$$
b\rightarrow\frac{b}{2}
$$
为了达到相同可靠性，大约需要 **2 倍 rounds**。
##### Node Failure
50% nodes fail 时：
$$
n\rightarrow\frac n2,\qquad b\rightarrow\frac b2
$$
传播仍可继续。传播刚开始时可能因少数 infected 节点全部失败而停止，但一旦已有多个 infected 节点，Gossip 完全消失的概率会迅速降低。

## 7. Topology-Aware Gossip
真实网络通常有 Rack / Subnet 等层级结构。完全随机选择 Gossip target 会产生大量跨 subnet 通信，使核心 Router 承担约 $O(N)$ load。对于包含 $n_i$ 个节点的 subnet：
$$
P(\text{选择本 subnet})=1-\frac1{n_i}
$$
即 **大部分消息在本地传播，少量消息跨 subnet**，从而：
$$
\text{Router Load}=O(1)
$$
同时保持：
$$
\text{Dissemination Time}=O(\log N)
$$
> **Local communication 为主，Global communication 为辅。**

## 8. Gossip 的实际应用
Gossip 不只是理论协议，它被用于很多实际分布式系统。典型例子是 **Cassandra**：使用 Gossip 维护集群中的 **membership list**，让节点逐渐知道哪些节点存在以及相关状态。
Gossip 的核心可以记成：
$$
\text{Random + Repeated + Decentralized}
$$
它牺牲了严格、固定的传播路径，换来了：
$$
\text{Scalability} + \text{Fault Tolerance} + \text{Low Latency}
$$
> **Push 前期快，Pull 后期快** ;Gossip 整体传播约为 **$O(\log N)$** ;Pull 后半段可达到 **$O(\log\log N)$**
> 随机冗余传播带来较强 **Fault Tolerance**; **Topology-Aware Gossip** 降低核心网络负载





# Failure Detection and Membership
在大规模分布式系统中，Failure 不是例外，而是常态。节点数量越多，系统中某台机器发生故障的频率越高，因此很多分布式系统都需要 **Failure Detector** 和 **Membership Service**。

## 1. Group Membership
Membership Service 维护当前系统中的成员列表，并处理：
> Join
> Leave
> Failure

它通常由两个部分组成：
- **Failure Detector**：发现哪些节点可能已经失败
  **Dissemination**：把 join / leave / failure 信息传播给其他节点

Membership List 可以是：
- Strongly Consistent：始终维护完整一致列表
  Weakly Consistent：允许短暂不一致，如 Gossip / SWIM
  Partial Membership：每个节点只知道部分成员

大规模系统通常更偏向后两者，因为可扩展性更好。

## 2. Failure Detector 的目标
Failure Detector 主要考虑四个指标：
**Completeness**：真正失败的节点最终会被检测出来。(完全保证)
**Accuracy**：正常节点不会被错误判断为失败。(概率保证)
**Speed**：故障发生后多久第一次被检测到。
**Scale**：每个节点负载是否均衡、网络消息数量是否可接受、是否存在单点瓶颈

在异步、可能丢包的网络里，**Completeness 和 Accuracy 无法同时做到绝对保证**。因为一个节点长时间没有响应，无法区分它到底是：真正 Crash、网络消息延迟、消息丢失、节点运行很慢。因此实际系统通常更重视 **Completeness**，而 Accuracy 常采用概率性保证。

## 3. Heartbeating
Heartbeat 的基本思想： Node → periodic heartbeat → Detector
如果超过 Timeout 没有收到新的 heartbeat，就怀疑该节点失败。

##### Centralized Heartbeating
<img src="/images/core/960ba8bdc762.png" alt="Screenshot 2026-10-07 at 21.55.26" style="zoom:50%;" />所有节点向一个中心节点发送 Heartbeat。
优点：

- 实现简单

问题：
- 中心节点是 Hotspot
  中心节点本身是 Single Point of Failure
  网络延迟或丢包可能造成 False Positive

##### Ring Heartbeating
<img src="/images/core/df1c63c88a53.png" alt="Screenshot 2026-10-07 at 21.55.41" style="zoom:50%;" />

每个节点只监控 Ring 上的某个邻居。

优点：
- 每个节点负载小

问题：
- 多个节点同时失败时行为不稳定
  Ring 中断后可能漏掉 Failure

##### All-to-All Heartbeating
<img src="/images/core/bd696011087c.png" alt="Screenshot 2026-10-07 at 21.55.59" style="zoom:50%;" />每个节点向所有其他节点发送 Heartbeat。
优点：

- 负载比较均匀
  Detection 快

问题：
- 每个节点需要维护 $O(N)$ 通信
  单次 Heartbeat 丢失就可能导致误判

  <img src="/images/core/c83bef038e7b.png" alt="Screenshot 2026-10-07 at 22.03.09" style="zoom:25%;" />

## 4. Gossip-Style Failure Detection
<img src="/images/core/2ee33eff9103.png" alt="Screenshot 2026-10-07 at 21.56.47" style="zoom:50%;" />为了提高 Heartbeat 的鲁棒性，可以使用 Gossip。每个节点维护类似：$$ <Address, Heartbeat Counter, Local Time>$$
节点周期性随机选择其他节点发送自己的 Membership List；收到后与本地列表 Merge。
如果某个节点的 Heartbeat Counter 很久没有增加：
$$
\text{No heartbeat update for }T_{fail}
\Rightarrow \text{mark as failed}
$$

再经过一段：

$$
T_{cleanup}
$$

才真正从 Membership List 中删除。

##### 为什么不能立即删除？
因为其他节点可能还保存旧状态，并通过 Gossip 再次传播回来，造成已经失败的节点“复活”。
所以状态通常经历：$$ Alive → Failed → Cleanup/Delete$$
而不是：$$ Alive → Delete$$
Gossip 本身传播一条更新大约需要：
$$
O(\log N)
$$

如果每个节点带宽足够大，可以同时传播大量 heartbeat；如果每个节点带宽受限，则整体传播时间会增加。

## 5. Failure Detection 的 Tradeoff
几个参数之间存在明显 tradeoff。

##### Gossip Period
$$ T_{gossip} $$ 越小，Gossip 越频繁：

$$
T_{gossip}\downarrow
\Rightarrow
\text{Detection Faster}
$$

但同时：
- Detection Time ↓或unchanged
  False Positive Rate  ↓
  Bandwidth ↑

因为检测更激进，heartbeat 信息传播得更频繁、更及时。

##### Failure Timeout
$$ T_{fail} $$ 越大, 可以检测的时间越长：
- Detection Time ↑
  False Positive Rate ↓
  Bandwidth 基本不变

所以核心权衡是：

$$
\boxed{\text{Detection Time}\leftrightarrow\text{False Positive Rate}\leftrightarrow\text{Bandwidth}}
$$

## 6. 为什么传统 Heartbeating 不是最优
All-to-All 和 Gossip Heartbeating 都尝试让很多节点同时检测 Failure，因此会产生较高消息负载。传统方法没有很好地区分：

- **Failure Detection**：先让某个节点快速发现 Failure
  **Dissemination**：再把 Failure 信息传播给其他节点

更好的设计应该把这两个过程分开。

## 7. SWIM Failure Detector
SWIM 的目标是让 Failure Detection 的负载与系统规模基本无关。

<img src="/images/core/05fb200483e5.png" alt="Screenshot 2026-10-07 at 22.07.15" style="zoom:50%;" />

每个 Protocol Period：

>1. `pi` 随机选择 `pj`
>2. 发送 `ping`
>3. 如果收到 `ack`，说明正常
>4. 如果没收到，选择 `K` 个随机节点
>5. 请求它们执行 `ping-req`
>6. 这些节点间接 ping `pj`
>7. 如果仍然没有 ack，则怀疑 `pj`

流程：$pi → ping → pj$
如果失败：$pi → K helpers → ping pj$
这种 **Indirect Ping** 能减少因为单条网络路径异常导致的误判。
SWIM 的特点：

- First Detection Time：期望为常数级
  Process Load：每周期常数级
  False Positive Rate：可通过 `K` 调节
  Completeness：可做到有界检测

相比传统 Heartbeating：
$$SWIM: Constant Load + Constant Expected First Detection$$
$$Heartbeating: Load 随 N 增长$$

## 8. Time-Bounded Completeness
为了保证每个节点最终一定被检查，可以让 Ping Target 不完全随机，而是：

- Round-robin 遍历 Membership List
  每次遍历后重新随机排列

这样每个成员都会在有限时间内成为 Ping Target。最坏情况下：
$$
O(N)
$$

个 Protocol Period 内会检测到 Failure。

## 9. Dissemination
Failure Detector 只解决“谁先发现”，还需要把信息传播给全系统。
常见方法：

- Multicast
- Point-to-Point
- Piggyback

SWIM 更偏向第三种：**把 Membership Update Piggyback 在原本的 ping / ack 消息上。**
这样可以做到：$$Zeroextra messages也叫$$  **Infection-style Dissemination**。节点维护最近发生的更新 Buffer，例如：

- Joined
- Suspected
- Failed
- Left

发送 ping / ack 时顺便携带这些信息。
Update 经过约：
$$
O(\log N)
$$

个周期后通常已经传播到整个系统，因此之后可以 Garbage Collect。

## 10. Suspicion Mechanism
直接从 Alive 变 Failed 容易误判，所以可以增加中间状态：$Alive → Suspected → Failed$
当某个节点收到关于自己的 $Suspect$ 消息时，如果自己其实还活着，可以主动发送 **Alive** 消息进行反驳。

##### Incarnation Number
为了区分旧状态和新状态，每个节点维护 **Incarnation Number**。
规则：

>只有节点自己可以增加自己的 incarnation number
>更高 incarnation number 覆盖更低版本
>同一个 incarnation 内：`Suspect > Alive`
>`Failed` 状态优先级最高

这样可以防止旧消息覆盖新状态。

## 11. Summary
Membership Protocol 可以概括成：$$ Failure Detection + Dissemination$$
传统 Heartbeat 简单，但在 Scale、Load、Accuracy 上存在问题。
SWIM 的核心改进是：**Random Ping + Indirect Ping + Separate Detection/Dissemination + Piggyback Membership Updates + Suspicion**
因此能够实现：

- 较低 Process Load
- 较快 Failure Detection
- 可调 False Positive Rate
- 良好的 Scalability

SWIM 后来被应用在 Serf、Consul、Uber Ringpop 等系统中。





# Grid Computing
Grid Computing 的目标是把分布在不同地点、不同组织中的计算资源组合起来，为计算密集型任务提供大规模计算能力。它主要面向 **HPC（High Performance Computing）** 场景。

## 1. Grid 的基本思想
传统 HPC 通常依赖昂贵的 Supercomputer，而 Grid 尝试把不同地点已有的计算资源组合起来：
$$ MIT + Wisconsin + NCSA + ... → Shared Computing Resources$$
这些资源属于不同组织，因此 Grid 通常具有 **Federated** 特征，即没有单一实体完全控制整个系统。
Grid 的核心问题包括：Resource Allocation、Job Scheduling、Data Transfer、Monitoring、Security

## 2. Job Dependency
一个大型科学计算任务通常由多个 Job 组成。
例如：`Job 0 → Job 1` `Job 0 → Job 2` `Job 1 + Job 2 → Job 3`其中 Job 1 和 Job 2 可以并行运行。

<img src="/images/core/afb94d5a8a0c.png" alt="Screenshot 2026-10-07 at 11.57.37" style="zoom:33%;" />

Job 通常包含几个阶段：
$$ Stage In → Execute → Stage Out → Publish $$

> Stage In：把输入数据传到执行节点
> Execute：进行计算
> Stage Out：把结果传出
> Publish：发布结果供其他 Job 使用

因为输入/输出文件可能达到 GB 级，因此 **Compute Scheduling 和 Data Transfer 同样重要**。

## 3. Two-Level Scheduling
Grid 通常采用两级调度：

### Intra-Site 站点内部
站点内部自己负责资源调度。例如：
	Wisconsin：**HTCondor**协议
	其他站点：PBS 或其他本地 Scheduler

负责：
	Internal Allocation & Scheduling: 内部资源分配与调度
	Monitoring: job和machine监控
	Distribution and Publishing of Files: 文件的监控与发布

### Inter-Site 站点之间
跨站点使用类似 **Globus** 的协议。
负责：
	External Allocation & Scheduling
	Stage In / Stage Out
	跨站点资源协调
Globus 不需要知道每个站点内部细节，只和站点暴露出来的 Scheduler 交互。
因此：
	$Inter-Site Scheduler → 选择哪个 Site$
	$$ Intra-Site Scheduler → 决定该 Site 内具体哪台机器运行 Job$$

## 4. HTCondor
HTCondor 是 Wisconsin 开发的 High-Throughput Computing 系统。它属于 **Cycle-Scavenging** 系统：利用普通工作站空闲时的 CPU 资源执行任务。
基本模式：$$ Workstation Idle → Request Job → Execute $$
如果用户开始使用机器：$$ Keyboard / Mouse Activity → Stop Task $$ 就：Kill Task或重新调度到其他机器
类似系统还有：ETI@Home、Folding@Home. HTCondor 也可以运行在 Dedicated Machines 上。

## 5. Globus
Globus 是 Grid Computing 中的重要基础设施和标准化工具集合。核心组件包括：
**GridFTP**: 用于 **Wide-Area Bulk Data Transfer**。适合跨站点传输大量数据。
**GRAM**: Grid Resource Allocation Manager。负责：Submit Job、Locate Job、Cancel Job、Manage Job
但：**GRAM 本身不是 Scheduler。**它会和 HTCondor、PBS 等站点内部 Scheduler 交互。
**RLS**:Replica Location Service。作用类似 Naming Service：$$ File Name → Physical Location$$
**GSI**: Grid Security Infrastructure。负责 Grid 环境中的安全与认证。

## 6. Security
Grid 的 Security 很重要，因为它通常跨多个组织和管理域。Grid 中 Security 比普通单一数据中心更复杂，因为 Grid 是 Federated，而 Cloud 通常由单一 Provider 控制。主要问题包括：

>**Single Sign-On**: 用户只认证一次，就能运行整个 Job Chain。
**Local Security Mapping**: 不同 Site 使用不同安全机制，例如：Kerberos、Unix AccountGrid 需要把统一身份映射到本地权限系统。
**Delegation**: 父 Job 可以把 Credentials 传给子 Job，使子任务能够继续访问资源。
**Community Authorization**: 允许第三方或组织级授权。

## 7. Summary
Grid Computing 的核心可以概括成：
$$ Distributed Resources + HPC + Two-Level Scheduling + Data Movement + Security$$
典型结构：$$Application DAG → Inter-Site Scheduling → Choose Site$$
$$ → Intra-Site Scheduling → Choose Machine → Execute Job $$

> HTCondor：站点内部调度
> Globus：跨站点协调
> GridFTP：大文件传输
> GRAM：Job 管理
> RLS：Replica Location
> GSI：Security

Grid 的很多设计思想后来也影响了 Cloud 和 Datacenter Systems。
