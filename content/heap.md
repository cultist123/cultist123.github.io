# 堆

## 一、基础知识

### 1.1 什么时候用堆

- 要在一堆会变化的东西里，反复拿最小（最大）的那个 → 堆
- 东西不变，只要排一次 → 排序
- 要找的是“左右第一个更大 / 更小” → 单调栈
- 要找的是“窗口里的最大 / 最小” → 单调队列

### 1.2 Python 的堆操作

```python
import heapq

heap = []
heapq.heappush(heap, x)      # 放进去，O(log n)
heapq.heappop(heap)          # 弹出最小的，O(log n)
heap[0]                      # 看最小的，不弹出
heapq.heapify(nums)          # 把一个列表原地变成堆，O(n)
```

- **最大堆**：存 `-x`，取出来再取反
- **放元组**：先比第一个，相同再比第二个（23 题讲过：第一个相同时会去比第二个，所以第二个要能比较）
- 不要用 `nlargest` / `nsmallest` 这种一行写法，要自己写堆

### 1.3 两个常用套路

- **Top-K**：要第 K 大，就维护一个**大小为 K 的最小堆**。超过 K 个就弹掉最小的，最后堆里是最大的 K 个，**堆顶就是第 K 大**。和 347 一样
- **按时间模拟**：先按开始时间排序，堆里放“正在进行的”或“当前可用的”，每到一个时刻，先把已经结束的从堆里弹掉，再处理新的

**建堆的复杂度**：`heapify` 把整个列表变成堆是 **O(n)**，比一个个 push 进去（O(n log n)）快。

### 1.4 基础例题

[2558. 从数量最多的堆取走礼物](https://leetcode.cn/problems/take-gifts-from-the-richest-pile/)
```python
import math
x = math.isqrt(x)  # 开平方，向下取整
```

[1046. 最后一块石头的重量](https://leetcode.cn/problems/last-stone-weight/)



## 二、第 K 小／大与 Top-K

[215. 数组中的第K个最大元素](https://leetcode.cn/problems/kth-largest-element-in-an-array/)

[703. 数据流中的第 K 大元素](https://leetcode.cn/problems/kth-largest-element-in-a-stream/)
**Top-K 模板题**：大小为 K 的最小堆，堆顶就是第 K 大

[205. 数组中的第K个最大元素](https://leetcode.cn/problems/kth-largest-element-in-an-array/)

[347. 前k个高频元素](https://leetcode.cn/problems/top-k-frequent-elements/)

[692. 前K个高频单词](https://leetcode.cn/problems/top-k-frequent-words/)
Top-K + counter计数器 + 元组比较 注意存进去的是[(2,word)]元组,数组转换的时候不要忘了加(),最后结果for pair,取pair[1]

[973. 最接近原点的 K 个点](https://leetcode.cn/problems/k-closest-points-to-origin/)

Problem: 面试题 17.14. 最小K个数



## 三、时间模拟与资源调度

[2406.将区间分为最少组数](https://leetcode.cn/problems/divide-intervals-into-minimum-number-of-groups/)
**区间经典题**（同会议室 II）：按开始排序，堆里放结束时间

[1942. 最小未被占据椅子的编号](https://leetcode.cn/problems/the-number-of-the-smallest-unoccupied-chair/)
较难,需要两个堆配合,一个维护区间,见2406,另一个维护椅子,为了每次找到最小的椅子编号要在放入下一个之前先把所有释放的椅子加入,相当于两个组互吸,一个吐出椅子放入人,一个吐出人放入椅子



[1834. 单线程 CPU](https://leetcode.cn/problems/single-threaded-cpu/)
好题,注意各种变量都在控制什么东西,arr,i,times,ans 是一种播快时间和缓存,还有对cpu串行的理解,可以仔细看注释,进heap队列的条件是: 只要时间times到了，不管候诊室里有没有人，都应该进去排队，正确的条件只看两件事：**门外还有人（`j < n`）**，并且**这个人已经到了（`arr[j][0] <= times`）**

[1353. 最多可以参加的会议数目](https://leetcode.cn/problems/maximum-number-of-events-that-can-be-attended/)
和单线程cpu逻辑基本上一样,但是day不能跳过且要按天遍历,时间计算不一样,弹掉过期的会议,每天贪心参加结束时间最短的会议,因为结束时间的晚越有概率放到后面参加,先弹掉很重要,不然就会发生这天没参加会议,浪费了一天

[1882. 使用服务器处理任务](https://leetcode.cn/problems/process-tasks-using-servers/)
注意这个问题前提是每秒来一个任务,而不是前面,每秒来好多任务,所以只有任务阻塞时,之后释放了才会出现并行的情况,结合了前面的1834单线程播快时间的操作,和1353的区别是能进行时间跳跃,不是i按照顺序指下去, 注意没有空闲服务器要进行时间跳跃操作

两个堆：`arr` 放空闲服务器 `(权重, 下标)`，`heap` 放忙碌服务器 `(空出来的时间, 权重, 下标)`。

每个任务一轮：先 `cur = max(cur, i)`，把 `heap` 里空出来时间 `<= cur` 的放回 `arr`；如果没有空闲的，`cur` 跳到 `heap[0][0]` 再释放一次；然后从 `arr` 弹出一台，`time = cur + tasks[i]` 放进 `heap`。

⚠️ 时间要单独用 `cur` 记“现在实际几点”，不能直接用 i，因为任务可能要排队。外层循环只跑任务个数，不能写 `or heap`，否则死循环。



## 四、贪心重排

[621. 任务调度器🌟](https://leetcode.cn/problems/task-scheduler/)

重排元素,队列和堆配合,堆贪心维护次数最多的任务,以减少气泡,队列作为先进先出的冷却,到了冷却时间再放回堆里第 K 小/大

注意元素为0就不要放进去,不然会多判断

[1405. 最长快乐字符串](https://leetcode.cn/problems/longest-happy-string/)
用贪心,在满足不联系3个的基础上,尽量用数字最多的,注意元组不能修改,所以要先拿出来再放进去,以及堆只能找到最大但是不能找到第二大的,所以要把最大拿出来,然后才能再把第二大拿出来,还有就是判断字母是否=0,如果=0就不要放入堆,以免下面还要再检测一下是否超出范围



## 五、多路归并

[373. 查找和最小的 K 对数字](https://leetcode.cn/problems/find-k-pairs-with-smallest-sums/)

[23. 合并 K 个升序链表] 联动一下,本质上就是用堆维护了合并k个升序序列,先把num1[i]+num2[0]放入堆,这个就是链表头,然后就有i被取出来的,就往后再移一格



## 参考资料

- [常用数据结构题单 - 灵茶山艾府](https://leetcode.cn/discuss/post/3583665/fen-xiang-gun-ti-dan-chang-yong-shu-ju-j-bvmv/)
- [Stack&Queue&Heap · Ruoke Zhang](https://ruokezhang.github.io/zh-cn/post/leetcode/stackqueue/)
