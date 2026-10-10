# 滑动窗口

## 1.定长窗口

**理论**: [定长滑窗套路](https://leetcode.cn/problems/maximum-number-of-vowels-in-a-substring-of-given-length/solutions/2809359/tao-lu-jiao-ni-jie-jue-ding-chang-hua-ch-fzfo/)
**定长滑窗套路**
窗口右端点在$ i $时，由于窗口长度为 $k$，所以窗口左端点为$ i−k+1$
总结成三步：**入-更新答案-出**
**1.入**：下标为 $i $的元素进入窗口，更新相关统计量。如果窗口左端点$ i−k+1<0$，说明尚未形成第一个窗口，重复第一步。
**2.更新答案**：此时窗口长度为 $k$，符合题目要求，用相关统计量更新答案。
**3.出**：下标为 $i−k+1 $的元素离开窗口，更新相关统计量，为下一个循环做准备。注：元素离开窗口后，窗口长度为 k−1。下一轮循环元素进入窗口后，窗口长度为 k。

```
class Solution(object):
    def maxVowels(self, s, k):
        ans = vowel = 0
        #i是索引c是内容
        for i,c in enumerate(s):
            if c in "aeiou":
                vowel += 1
            left = i-k+1#根据索引写出left坐标,因为k是固定的,所以知道right就知道left
            if left<0 :#如果不满足就重复第一步说明尚未形成第一个窗口
                continue
            ans = max(ans,vowel)#此时窗口长度为k符合题目要求统计相关量
            if s[left] in "aeiou":
                vowel-=1
        return ans
```

**例题**: [固定长度的滑动窗口](https://leetcode.cn/problems/number-of-sub-arrays-of-size-k-and-average-greater-than-or-equal-to-threshold/)

## 2.不定长滑动窗口

看到 A **subarray** is a **contiguous** part of an array.要想到滑动窗口.
不定长滑动窗口主要分为三类：求最长子数组，求最短子数组，求子数组个数。

### **不定长滑窗套路**

滑动窗口相当于在维护一个队列。右指针的移动可以视作入队，左指针的移动可以视作出队。

### 2.1求最长子数组

窗口大小随条件动态伸缩：

1. **扩展右界（`right` 进窗口）**：逐个将字符加入 `count` 计数器中。
2. **校验并收缩（`while` 条件不满足）**：如果新加入的字符导致 `count[ch] > 2`，说明当前窗口合法性破坏。通过 `while` 循环将 `s[left]` 弹出窗口，并递增 `left`，直至窗口恢复合法状态。   
3. **计算与更新（全局最大值）**：进入第 3 步时窗口必然合法，当前合法窗口长度为 `right - left + 1`，用 `max` 维护全局最大值。
4. **返回值**：遍历结束后，`ans` 即为答案。   

```
class Solution:
    def maxWindowTemplate(self, nums: List[int]) -> int:
        left = 0
        ans = 0  # 1. 初始值设为 0（或 -1 / float('-inf')，取决于具体逻辑）
        cur_state = 0  # 窗口状态（如字符频次表、滑动和等）
        for right, val in enumerate(nums):
            # 1. 进窗口：扩展右边界并更新状态
            # 例如：freq[val] = freq.get(val, 0) + 1 或 cur_sum += val
            # 2. 校验与收缩：当窗口处于非法状态时，强制收缩左边界，直到重新合法
            while is_invalid(cur_state):  # 检查窗口是否违规（如 freq[val] > k 或 cur_sum > target）
                # 出窗口：扣除 left 指针对应的状态
                # 例如：freq[nums[left]] -= 1 或 cur_sum -= nums[left]
                left += 1  # 左指针右移
            # 3. 结果维护：此时 while 循环结束，窗口必然合法！
            # 用当前合法的实时长度 (right - left + 1) 去刷新全局最大值
            ans = max(ans, right - left + 1)
        # 4. 返回最大长度
        return ans
```



**例题**:[每个字符最多出现两次的最长子字符串](https://leetcode.cn/problems/maximum-length-substring-with-two-occurrences/)
[无重复最长子串](https://leetcode.cn/problems/longest-substring-without-repeating-characters/)

### 2.2求最短子数组

**1.进窗口**（扩展 `right`）

将当前右指针元素 `nums[right]` 加入窗口统计数据中（如求和 `cur_sum += nums[right]` 或维护频次表）。

**2.校验、记录并收缩**（`while` 窗口合法）

**触发条件**：`while` 检查窗口**是否已经满足条件**（例如 `cur_sum >= target`）。

**动作 1（记录答案）**：因为当前窗口已经合法，**立刻用 `min` 记录/更新最小值** `ans = min(ans, right - left + 1)`。

**动作 2（出窗口试探）**：将左指针元素 `nums[left]` 移出窗口，并让 `left += 1`，试图“挤掉”左边的元素，探查在保持合法的前提下窗口能否更短。

**3.兜底与返回**（边缘处理）

遍历结束后，检查 `ans` 是否仍为初始设定的极大值 `float('inf')`。如果是，说明全程没有满足条件的子数组，按题意返回 `0`；否则返回 `ans`。

```
class Solution:
    def minWindowTemplate(self, nums: List[int], target: int) -> int:
        left = 0
        ans = float("inf")  # 1. 初始值设为正无穷
        cur_state = 0  # 窗口状态（如区间和、字符频次等）
        for right, val in enumerate(nums):
            # 1. 进窗口：扩展右边界
            cur_state += val
            # 2. 只要满足条件，就不断尝试“收缩”以寻找更短的合法窗口
            while is_valid(cur_state):  # 判断条件（如 cur_state >= target）
                ans = min(ans, right - left + 1)  # 2a. 先记录当前最小值
                cur_state -= nums[left]  # 2b. 出窗口
                left += 1  # 2c. 左指针右移
        # 3. 兜底返回
        return ans if ans != float("inf") else 0
```

**例题：**[长度最小的子数组](https://leetcode.cn/problems/minimum-size-subarray-sum/)
[ 不同元素和至少为 K 的最短子数组长度](https://leetcode.cn/problems/minimum-subarray-length-with-distinct-sum-at-least-k/) 

**最大最小的区别**

| **维度 / 差异**      | **求最长 / 最大（如 LeetCode 3, 3090）** | **求最短 / 最小（如 LeetCode 209, 76）**       |
| -------------------- | ---------------------------------------- | ---------------------------------------------- |
| **`while` 触发条件** | `while (窗口不合法)`                     | `while (窗口合法)`                             |
| **`while` 内部动作** | 强行踢出 `left`，直到窗口**重新合法**    | **先更新 `min`**，然后踢出 `left` 试探更短可能 |
| **答案更新位置**     | **`while` 循环外部**（此时刚恢复合法）   | **`while` 循环内部**（每次合法时立刻更新）     |
| **答案初始值**       | `ans = 0`                                | `ans = float('inf')`                           |

### 2.3求子数组个数

#### 2.3.1 越短越合法—至多问题

一般要写`ans += right - left +1`

内层循环结束后,$[left,right]$满足要求,$[left+1,right]$也满足要求,数组越短越满足要求,$[left+1,right],[left+2,right],...,[right,right]$都满足要求,当固定right时,一共有$right - left +1$个满足要求

数组越短越满足要求,right变大更有可能不满足要求,所以while放不合法内容,违规要剔除左边界值,然后再记录合法值

**例题**:[乘积小于 K 的子数组](https://leetcode.cn/problems/subarray-product-less-than-k/)

#### 2.3.2 越长越合法—至少问题

一般要写`ans += left`

内层循环结束后,$[left,right]$是不满足要求的,在退出循环的最后一轮$[left-1,right]$,是满足要求的,数组越长越满足要求,$[left-1,right],[left-2,right],...,[0,right]$都满足要求,当固定right时,一共有$left$个满足要求

数组越长越满足要求,right变大更有可能满足要求,所以while放合法内容,测试最短合法区间,left-1为最后一个合法的索引,然后再记录合法值

**例题**:[包含所有三种字符的子字符串数目](https://leetcode.cn/problems/number-of-substrings-containing-all-three-characters/)

| **问题类型**                             | **特征性质**                 | **while 条件**                  | **循环结束后 ans 增加量**                          |
| ---------------------------------------- | ---------------------------- | ------------------------------- | -------------------------------------------------- |
| **越短越合法** (如 LC 713 乘积 $< k$)    | 窗口**变长**可能导致**违规** | `while (不合法)` 收缩到重新合法 | **`ans += right - left + 1`** (当前合法窗口的长度) |
| **越长越合法** (如 LC 1358 包含所有字符) | 窗口**变短**可能导致**违规** | `while (合法)` 挤压到刚好不合法 | **`ans += left`** (合法左端点的个数)               |

#### 2.3.3 恰好型滑动窗口

要计算有多少个元素和恰好等于 k 的子数组，可以把问题变成：

1. 计算有多少个元素和 ≥k 的子数组。
2. 计算有多少个元素和 >k，也就是 ≥k+1 的子数组。
3. 答案就是元素和 ≥k 的子数组个数，减去元素和 ≥k+1 的子数组个数。这里把 > 转换成 ≥，从而可以把滑窗逻辑封装成一个函数 solve，然后用 solve(k)−solve(k+1) 计算，无需编写两份滑窗代码。

总结：「恰好」可以拆分成两个「至少」，也就是两个「越长越合法」的滑窗问题。

> 注：也可以把问题变成 ≤k 减去 ≤k−1，即两个「至多」。可根据题目选择合适的变形方式。
>
> 注：也可以把两个滑动窗口合并起来，维护同一个右端点 right 和两个左端点 left 1和 left 2，我把这种写法叫做三指针滑动窗口。



**例题**: [和相同的二元子数组](https://leetcode.cn/problems/binary-subarrays-with-sum/)
转变为两个至多相剪或者两个至少相减,拆成两个越长越合法或两个越短越合法的问题
[K个不同整数的子数组](https://leetcode.cn/problems/subarrays-with-k-different-integers/)
转变为atMostK(k)-atMostK(k-1),因为要知道的数字是不确定的,但是频率确定,所以要维护一个频率计数器,同时我们注意到`1 <= nums[i], k <= nums.length`,所以要构造的数字储存空间是固定的len(nums)+1
[424. 替换后的最长重复字符（高频）](https://leetcode.cn/problems/longest-repeating-character-replacement/)
先想最长还是最短问题, **需要被替换的次数 = 当前窗口长度 - 字母最大频次**, 给窗口内每个字符计数，`max(freq)`用作（动态扫描)功能,每次获取到次数最多的字符出现的次数，如果需要替换的次数 > 实际有的次数则要收缩窗口
[找出最长等值子数组](https://leetcode.cn/problems/find-the-longest-equal-subarray/)
将滑动数字变为了滑动索引, 滑动索引list从而找到个数,窗口长度,删除次数.最短问题.用map存储每个数值key的索引list 记录index，将非连续搜索转化为对一维下标列表的单向滑动。**需要被删除的次数 = 当前窗口长度 - 字母最大频次**
>1. 原数组上滑窗没有意义
>   在原数组上直接开双指针滑动窗口时，窗口里混杂着各种不同的数值。一旦杂质超标，你根本不知道该为了保留哪个数字去右移 `left`—为了照顾数字 A 去剔除数字 B，可能会破坏数字 B 凑成答案的可能。不同数值相互干扰，导致窗口缺乏明确的收缩方向。
>
>2. 进行数组变化，只抓数值坐标
>   仔细观察可以发现：想要凑出全为 A 的子数组，其他数字具体是什么根本不重要，它们只是占了位置的“无名杂质”。既然不同数值之间完全独立，最自然的做法就是**按数值分组**，把每个数值出现的位置（下标）单独提取出来，存进一个列表 `vec` 里，将杂乱的原数组拆分成多个纯净的坐标轴。
>
>3. 用“下标差值”得出其余变量
>
>   将问题转化为在坐标轴 `vec` 上滑窗后，杂质数量的计算变得极其简单。从 `vec[left]` 到 `vec[right]` 的原数组跨度，减去当前保留的目标元素个数，就是需要删除的杂质数 `(vec[right] - vec[left]) - (right - left)`。我们不需要关心杂质究竟是几，只用坐标相减就能瞬间精准推演窗口的合法性。

