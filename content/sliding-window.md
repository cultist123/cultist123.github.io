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

不定长滑动窗口主要分为三类：求最长子数组，求最短子数组，求子数组个数。

#### **不定长滑窗套路**

滑动窗口相当于在维护一个队列。右指针的移动可以视作入队，左指针的移动可以视作出队。

#### 2.1求最长子数组

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

#### 2.2求最短子数组

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

#### 2.3求子数组个数
