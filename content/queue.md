# 队列

## 一、基础知识

### 1.1 Python 中的队列操作

Python 里用 `deque` 当队列。

```python
from collections import deque

q = deque()
q.append(x)       # 队尾进
q.popleft()       # 队头出
q[0]              # 看队头
q[-1]             # 看队尾
q.pop()           # 队尾出（双端队列才用）
```

### 1.2 基础应用

队列常用在 BFS 中，见 [网格图题单](https://leetcode.cn/circle/discuss/YiXPXW/) 和 [图论题单](https://leetcode.cn/circle/discuss/01LUak/)。与此相比，栈常用在 DFS 中，但无需我们手动维护。

[933.最近的请求次数](https://leetcode.cn/problems/number-of-recent-calls/)



## 二、队列设计

[232.用栈实现队列](https://leetcode.cn/problems/implement-queue-using-stacks/)
(面试常考)一个栈作为输入栈，另一个栈作为输出栈,注意move封装,判断不存在不能用[-1],要用not stack,因为如果是0也会返回false

[622. 设计循环队列](https://leetcode.cn/problems/design-circular-queue/)
用长度为(cap+1)的数组实现，用 rear 指向下一个数放置的 index，front 指向**当前队列**第一个元素的 index。用双指针和数组,构造出循环的假象

```python
self.front = (self.front + 1) % self.cap
return self.arr[(self.rear - 1) % self.cap]
```

注意找位置要细心,注意往前还是往后走



## 三、单调双端队列

### 3.1 基本思路与处理顺序

叫**单调双端队列**更准确。必须先掌握滑动窗口和单调栈这两个知识点，再学单调队列。

**灵神对单调队列的两句总结**

- **单调队列 = 滑动窗口 + 单调栈**。队尾的操作就是你已经很熟的单调栈（弹掉没用的），队头负责把**过期的**（离开窗口的）弹掉
- **入队、出队、更新答案的顺序**：出队一般写在前面，每来一个新元素先看队头有没有过期；更新答案时如果要用到当前元素，就**先入队再更新**，否则**先更新再入队**

### 3.2 例题与应用

[239.滑动窗口最大值](https://leetcode.cn/problems/sliding-window-maximum/)

相等也弹,相当于留最新的

<img src="/images/queue/monotonic-queue-1.png" alt="image-20261022201422732" style="zoom:33%;" />

<img src="/images/queue/monotonic-queue-2.png" alt="image-20261022201856704" style="zoom:33%;" />



[1438. 绝对差不超过限制的最长连续子数组](https://leetcode.cn/problems/longest-continuous-subarray-with-absolute-diff-less-than-or-equal-to-limit/)

两个双端队列维护最值,队首分别最大值和最小值,一个滑动窗口负责找最长子序列,都存下标
