# 二分算法

参考:[灵神题单](https://leetcode.cn/discuss/post/3579164/ti-dan-er-fen-suan-fa-er-fen-da-an-zui-x-3rqn/)



## 1.闭区间写法

<img src="/images/binary-search/boundary.png" alt="二分题单 二分查找 二分算法 二分入门 二分题目 力扣二分 leetcode 二分 灵茶山艾府 灵神 灵神题单" style="zoom:50%;" />

> 图：闭区间二分循环结束时的左右指针位置（查找第一个 8）,左右指针位置互换

找该数

```
class Solution:
    # 标准的二分搜索框架，搜索目标元素的索引，若不存在则返回 -1
    def search(self, nums: List[int], target: int) -> int:
        left = 0
        right = len(nums) - 1

        while left <= right:
            mid = left + (right - left) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                left = mid + 1
            elif nums[mid] > target:
                right = mid - 1
        return -1
```

找左边界

```
def search(self, nums: List[int], target: int) -> int:
    left = 0
    right = len(nums) - 1

    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            right=mid-1
        elif nums[mid] < target:
            left = mid + 1
        elif nums[mid] > target:
            right = mid - 1
    return left
```



例题:[34. 在排序数组中查找元素的第一个和最后一个位置](https://leetcode.cn/problems/find-first-and-last-position-of-element-in-sorted-array/)



## 2.二分查找

讲解：[二分查找 红蓝染色法【基础算法精讲 04】](https://leetcode.cn/link/?target=https%3A%2F%2Fwww.bilibili.com%2Fvideo%2FBV1AP41137w7%2F)

设 *nums* 为递增（非递减）数组，长为 *n*。

**二分查找常用转化表**：

| 需求                         | 写法                          | 如果不存在  |
| ---------------------------- | ----------------------------- | ----------- |
| $\ge x$ 的第一个整数的下标   | `lowerBound(nums, x)`         | 结果为 $n$  |
| $> x$ 的第一个整数的下标     | `lowerBound(nums, x + 1)`     | 结果为 $n$  |
| $< x$ 的最后一个整数的下标   | `lowerBound(nums, x) - 1`     | 结果为 $-1$ |
| $\le x$ 的最后一个整数的下标 | `lowerBound(nums, x + 1) - 1` | 结果为 $-1$ |

**数量统计**:

| 需求               | 写法                          |
| ------------------ | ----------------------------- |
| $< x$ 的整数个数   | `lowerBound(nums, x)`         |
| $\le x$ 的整数个数 | `lowerBound(nums, x + 1)`     |
| $\ge x$ 的整数个数 | `n - lowerBound(nums, x)`     |
| $> x$ 的整数个数   | `n - lowerBound(nums, x + 1)` |

注意 <*x* 和 ≥*x* 互为补集，元素个数之和为 *n*。≤*x* 和 >*x* 同理。



## 2.非单调数组

利用一个条件，把数组里所有的元素切分成“红色:不满足条件”和“蓝色:满足条件”两大部分，并给它们涂上颜色。

- **红色**：代表 **不满足条件** 的元素（位于目标的左边）。
- **蓝色**：代表 **满足条件** 的元素（位于目标及其右边）。

在闭区间 `while left <= right` 的二分过程中 ,`left` 和 `right` 维系着如下的不变性：

1. **`left - 1` 及其左边**：已经被**确认染成红色**（非目标区域）。
2. **`right + 1` 及其右边**：已经被**确认染成蓝色**（目标及右侧区域）。
3. **`[left, right]` 区间**：是**尚未染色的未知区域**（等待二分去检验）。

而我们做二分查找的最终目的，**就是寻找“第一个蓝色元素”所在的位置**（即红蓝交界处的蓝色起点）。二分查找的过程，本质上就是**用红/蓝两种颜色的油漆，去吞噬中间灰色未知区域的过程**：

随着循环不断进行，灰色的未知区域 `[left, right]` 被两侧的红蓝油漆不断挤压。

当 `left > right` 时（即 `left = right + 1`），**灰色未知区域彻底消失（变成 0）**！

此时数组被完美分割为两半：

- **`right`**：死死停在**最后一个红色**（最后一个不满足条件的位置）。
- **`left`**：死死停在**第一个蓝色**（第一个满足条件的位置，即我们要找的目标）。

nums[n-1]初始为蓝色



> 部分题目需要先排序，然后在有序数组上二分查找。

例题
[162. 寻找峰值](https://leetcode.cn/problems/find-peak-element/)
每次拿nums[mid]和 nums[mid+1]比较,是一个爬峰的过程。
[153. 寻找旋转排序数组中的最小值](https://leetcode.cn/problems/find-minimum-in-rotated-sorted-array/)
将nums[mid]与固定值nums[n-1]进行比较。



## 2.二分答案

> “花费一个 log 的时间，增加了一个条件。” —— 二分答案



### 2.1 求最小—越大越合法(往小逼近)

题目求什么，就二分什么。

例题: 
[1283. 使结果不超过阈值的最小除数](https://leetcode.cn/problems/find-the-smallest-divisor-given-a-threshold/)
对余数进行二分,观察数组发现,令余数为数组最大的数可以满足条件,所以范围是[1,max(nums)],对这个数组进行二分查找最小的值,满足要求
[2187. 完成旅途的最少时间](https://leetcode.cn/problems/minimum-time-to-complete-trips/)
对时间进行二分,发现time最小的值✖️trips就是最长需要的时间,对这个数组进行二分求最小值

闭区间二分模版(求最小):

```
class Solution:
    # 计算满足 check(x) == True 的最小整数 x（二分答案/寻找第一个 True 的位置）
    def binarySearchMin(self, nums: List[int]) -> int:
        # 二分猜答案：判断 mid 是否满足题目要求
        def check(mid: int) -> bool:
            # TODO: 实现具体问题的判定逻辑
            pass

        left =   # 答案的最小可能取值（循环不变量：left - 1 及其左边 check 恒为 False，即红色区域）
        right =  # 答案的最大可能取值（循环不变量：right + 1 及其右边 check 恒为 True，即蓝色区域）

        while left <= right:  # 闭区间 [left, right] 不为空
            mid = left + (right - left) // 2
            if check(mid):  # mid 满足条件（蓝色），说明 check(>= mid 的数) 均为 True
                right = mid - 1  # 尝试寻找更小的合法解，向左逼近，把 mid 及其右边刷成蓝色
            else:  # mid 不满足条件（红色），说明 check(<= mid 的数) 均为 False
                left = mid + 1   # 答案必定在右边，向右放大，把 mid 及其左边刷成红色

        # 循环结束后 left > right（具体为 left = right + 1），未知闭区间彻底被完全抹除
        # 此时 right 停在最后一个 False（红色），left 精准停在第一个 True（蓝色）
        # 所以 left 就是满足 check 的最小整数解
        return left
```



### 2.2 求最大—越小越合法(往大逼近)

请注意「求最小」和「求最大」在二分写法上的区别。

「求最小」和二分查找求「排序数组中某元素的第一个位置」是类似的，按照红蓝染色法，左边是不满足要求的（红色），右边则是满足要求的（蓝色）。

「求最大」的题目则相反，左边是满足要求的（蓝色），右边是不满足要求的（红色）。这会导致二分写法和上面的「求最小」有一些区别。

以闭区间二分为例：

- 求最小：check(mid) == true 时更新 right = mid - 1，反之更新 left = mid + 1，最后返回 left。
- 求最大：check(mid) == true 时更新 left = mid + 1，反之更新 right = mid - 1，最后返回 right。

对于闭区间写法，出循环check(mid) == true 时左右指针发生交叉（left = right + 1）：求最小（寻找第一个蓝色位置）最终返回 left，求最大（寻找最后一个蓝色位置）最终返回 right。

```
class Solution:
    # 计算满足 check(x) == True 的最大整数 x
    def binarySearchMax(self, nums: List[int]) -> int:
        # 二分猜答案：判断 mid 是否满足题目要求
        def check(mid: int) -> bool:
            # TODO

        left =   # 循环不变量：left - 1 及其左边 check 恒为 True
        right =   # 循环不变量：right + 1 及其右边 check 恒为 False
        while left <= right:
            mid = (left + right) // 2
            if check(mid):
                left = mid + 1  # 注意这里更新的是 left = mid + 1，和求最小模板反过来
            else:
                right = mid - 1
        # 循环结束后 left > right（此时 left = right + 1）
        # 此时 check(right) == True 而 check(right+1) == check(left) == False
        # 所以 right 就是最大的满足 check 的值
        return right
```

例题
[275. H 指数 II](https://leetcode.cn/problems/h-index-ii/)
找最大值左边开始染成蓝的,右边是红的,不断推高left使得变为红
[2226.每个小孩最多能分到多少糖果](https://leetcode.cn/problems/maximum-candies-allocated-to-k-children/)
分的糖果数为二分数组,已有的//要分的,即为人数,人数可以与给定的进行比较



### 2.3 二分间接值

二分的不是答案，而是一个和答案有关的值（间接值）。

[3143. 正方形中的最多点数](https://leetcode.cn/problems/maximum-points-inside-the-square/)
二分得到正方形的最大值,求最大最小值规定的是left和right的染色方向,辅助函数本质是把判断逻辑解耦,check遵循找点-找字母-加字母,最后输入的是距离输出的是是否重复,

>`list`：我要保存一串东西
>`set`：我要快速判断“这个东西有没有出现过”
>`dict`：我要保存“key 对应什么 value”



### 2.4 最小化最大值

本质是二分答案求最小。二分的 *mid* 表示上界。

好比用一个盖子（上界）去压住最大值，看看能否压住（check 函数）。

例题
[410. 分割数组的最大值](https://leetcode.cn/problems/split-array-largest-sum/)
遍历数组，当前累加和大于mid时，创建一个新的分割，cnt+=1.注意left的设置,因为箱子本身不能比数字小不然会出现逻辑错误导致,在一个数上重复加2次,所以left = maxval



### 2.5 最大化最小值

本质是二分答案求最大。二分的 *mid* 表示下界。

例题:
[3281.范围内整数的最大得分](https://leetcode.cn/problems/maximize-score-of-numbers-in-ranges/)
(较难没想出来)绝对值理解为距离;要进行排序减少不确定性;画图解决,运用贪心从开始值开始选,为后面留出足够的空间;要mid定为两个点最小能达到的距离



### 2.6 第 K 小/大

例如数组 [1,1,1,2,2]，其中第 1 小、第 2 小和第 3 小的数都是 1，第 4 小和第 5 小的数都是 2。

对于第 k 小/大问题，有如下转化套路：

- 第 k 小等价于：求最小的 x，满足 ≤x 的数至少有 k 个。
- 第 k 大等价于：求最大的 x，满足 ≥x 的数至少有 k 个。

通常需要构造辅助函数check(mid),进行cnt计数,并与k比较.

> 注 1：一般规定 k 从 1 开始，而不是像数组下标那样从 0 开始。
> 注 2：部分题目也可以用堆解决。

例题
[719. 找出第 K 小的数对距离](https://leetcode.cn/problems/find-k-th-smallest-pair-distance/)
(hard题:二分查找+滑动窗口)要构造辅助函数, 数一下所有距离中, 小于等于X的距离个数,因为不是直接要距离而是对距离进行计数,所以需要复制函数输入距离输出的是计数。对应滑动窗口的“越短越合法”。然后再用二分查找,第k小问题,找x满足小于x的有k个,转化为求最小的问题
[378. 有序矩阵中第 K 小的元素](https://leetcode.cn/problems/kth-smallest-element-in-a-sorted-matrix/)
本质是数组的第k小在有序矩阵的应用,第 K 小的元素=**最小**的x,使得**矩阵中最少有K个元素小于等于它**,check(mid)在矩阵中搜索，返回小于等于x的元素的个数。性质：在矩阵中，任意取一个元素，小于等于它的元素正好在**矩阵的左上方**,因此从左下角开始搜索，若当前元素num小于等于x，则往右移动，同时可知num即其上方所有元素皆小于x，故cnt+=row+1,如果num大于x则往row-1进行移动,因为右边的数不可能满足要求

> 二分答案的一个难点是 `check` 函数怎么写，这会涉及到**贪心**等技巧，可以练练下面的贪心题单（主要是第一章节）。