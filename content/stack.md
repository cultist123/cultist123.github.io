# 栈

## 一、普通栈

> 四类用法: 配对 / 嵌套 / 消除 / 撤销
> 题目要求求什么就往栈里面存什么

### 1.1 基本思路与处理流程

**栈里存什么？**

原则：**弹出时需要什么，就存什么。**

1. **要算距离 / 长度 / 位置 → 存下标**（32、739、84）
   不确定就存下标：值可以用下标查，下标不能用值查。

2. **嵌套结构 → 存外层被打断时的进度**（856、394、224）
   `(` 压栈保存外层，`)` 弹出接着算。

**栈的基本处理流程**

1. **初始化**：`stack = []`。
2. **遇到普通元素**：入栈，暂存后续需要的数据。
3. **遇到处理信号**：出栈取出需要的数据，完成处理；如果结果后续还要用，就重新入栈。

[150.逆波兰表达式求值](https://leetcode.cn/problems/evaluate-reverse-polish-notation/)

[636. 函数的独占时间](https://leetcode.cn/problems/exclusive-time-of-functions/)
后进先出,栈顶表示当前正在运行的操作,递归构造时间,需要prev切上一个时间段



### 1.2 合法括号字符串

[32.最长有效括号](https://leetcode.cn/problems/longest-valid-parentheses/)——配对
第一遍循环, 用一个**掩码表mark**记录匹配成功的index,成功标为True。遇到(时，把它的 index 加入栈。遇到）如果stack有东西时，从栈里pop出一个(，它们两个匹配成功，把mark中它们两个的index上都标记为True,同时如果stack没东西,说明不符合先左再右的规则,就直接跳过.
第二遍循环,统计最长的连续True子数组长度即可。

[856.括号的分数](https://leetcode.cn/problems/score-of-parentheses/)——嵌套

规则：`()` 得 1 分；`AB` 得 A + B 分；`(A)` 得 2 × A 分。

思路：把每对括号看成一个盒子，用栈保存“外层被打断时的进度”。栈里存的不是括号，而是**进入里层之前，外层已经算好的分数**。

- 初始化 `stack = []`，`cur = 0`。`cur` 表示**当前这一层已经并排攒了多少分**
- 见到 `(`：要进入里层了。把 `cur` push 进栈，**保存外层到目前为止的分数**；然后 `cur` 清零，开始计算这对括号里面的值
- 见到 `)`：这对括号结束，`res` 是括号**里面**的总分
  - 先算这对括号本身的值：里面是空的（cur == 0）就是 1 ，否则是 2 × cur
  - 再 `stack.pop()` 取回**外层在这对括号之前攒的分数**，两者相加，作为新的 `cur`（这一步就是 AB = A + B）
  - 如果后面还有 `(`，这个 `cur` 会被 push 进栈继续保存,相当于暂存结果,等下个`(`算完了再并行加上；如果到结尾了，`cur` 就是答案

三条规则对应的代码：
- `()` = 1 → `if cur == 0: inner = 1`
- `(A)` = 2 × A → `else: inner = 2 * cur`
- `AB` = A + B → `res = stack.pop() + inner`

[1111. 有效括号的嵌套深度](https://leetcode.cn/problems/maximum-nesting-depth-of-two-valid-parentheses-strings/)
(没用到栈,本身是对嵌套的处理)把嵌套深度为奇数的括号和为偶数的括号，分别分到两个组。



### 1.3 邻项消除

[1717. 删除子字符串的最大得分](https://leetcode.cn/problems/maximum-score-from-removing-substrings/)——相邻消除
贪心，先尽量删分值大的 ab, 再删分值小的 ba. 不用while,算两遍,先算s再算剩下的rest

[735. 小行星碰撞](https://leetcode.cn/problems/asteroid-collision/)——相邻消除
用 while， 碰撞过后，要继续和栈里的行星碰撞。条件分支负责的话加个alive作为flag

[1209. 删除字符串中的所有相邻重复项 II](https://leetcode.cn/problems/remove-all-adjacent-duplicates-in-string-ii/)——相邻消除
栈里面放字母和它目前出现的次数，遇到新的字符，首先**比较它是否与栈顶相同**。如果相同，则栈顶次数+1,重复的只存一次,频率只修改一个就行,不需要出现一次往上加一个



### 1.4 表达式解析

[394. decode string](https://leetcode.cn/problems/decode-string/)——嵌套
Input: s = "2[abc]3[cd]ef" Output: "abcabccdcdcdef"
遇到[, 入栈(ans,num)，清空ans和num
遇到]，出栈ans = prev + ans*k
ans和num用来记录当前字符串的前缀，以及之后字符串需要重复的倍数。 num有可能是多位数所以要处理。
c.isdigit()数字是多位数

> 栈里存的就是**两样“进入里层后会被覆盖、但出来时还要用”的东西**。正好之前的字符串和要乘的数字在进行处理之后都会没有

[224. 基本计算器](https://leetcode.cn/problems/basic-calculator/)——嵌套
**用栈处理括号**
存下出来之后要使用的量,所以一次存两个。变量：`res`、`num`、`sign`（初始为 1）、`stack`

- 数字：`num = num * 10 + int(c)`
  `+` / `-`：`res += sign * num`，更新 sign，num 置 0
  `(`：把外层的答案 res 和括号前的符号 sign 一起入栈（出括号时要用这两个算），然后 res 置 0、sign 置 1
  `)`：先 `res += sign * num`，再弹出 `prev_res, prev_sign`，`res = prev_res + prev_sign * res`
  结束：返回 `res + sign * num`

[772. 基本计算器 III](https://leetcode.cn/problems/basic-calculator-iii/)——嵌套,递归
**用递归来处理括号**
变量：`it = iter(s)`（所有层共享读取位置），每层 `dfs` 各有 `stack`、`num`、`op`（初始为 +）

- 数字：`num = num * 10 + int(c)`
  `(`：递归 `num = dfs()`，括号整体当成一个数（递归自动保存外层的 stack、num、op）
  `+-*/)`：前一个数读完了，用前一个 op 处理它，再记下新 op、num 置 0
  `+` 压 num，`-` 压 -num，`*` / `/` 和栈顶马上算（除法用 `int(a / b)` 向 0 取整）
  `)`：处理完最后一个数，返回 `sum(stack)`
  for 结束：字符串读完，再处理一次最后一个数，返回 `sum(stack)`

```python
class Solution(object):
    def calculate(self, s):
        it = iter(s) # 所有递归层共享，读走的字符就没了
        def apply(stack,op,num):
            if op=="+":
                stack.append(num)
            elif op=="-":
                stack.append(-num)  
            elif op=="*":
                stack.append(stack.pop()*num)   
            else:
                stack.append(int(float(stack.pop())/num))
        def dfs():
            stack=[]
            op="+"
            num=0
            for c in it:
                if c.isdigit():
                    num=num*10+int(c)
                elif c=="(":
                    num=dfs()
                #当读到第一个字符才知道数字已经读完,所以开始处理上一个op的运算
                elif c in "+-*/)":
                    apply(stack,op,num)
                    if c ==")":
                        return sum(stack)
                    #处理完上一个再进行改变
                    op=c
                    num=0
            apply(stack,op,num)
            return sum(stack)
        return dfs() 
```



### 1.5 最小栈设计

[155.最小栈](https://leetcode.cn/problems/min-stack/)
用一个栈,存元组同时维护当前值和最小值,或者用两个栈，一个存所有元素，另一个存可能的最小值，从底到顶为从大到小。

## 二、单调栈

### 2.1 基本原则与遍历方向

<img src="/images/stack/monotonic-stack.png" alt="image-20261020201531318" style="zoom:50%;" />

- 找左/右边第一个更大的数：降序栈
  找左/右边第一个更小的数：升序栈

- 遍历方向：双向都可以，一种是去除无用，一种是去除已经有答案的数。

去除已经有答案的数：在循环里，一边把它弹出来，一边给它答案.
去除无用：在新遍历到某个数的时候，给它答案。

找右边第一个更大/小的数：**从左到右**遍历是**去除已经有答案的数**，**从右到左**是**去除无用**

想要留下那些最大的数：降序栈

> 即时去掉无用数据,保证栈中数据有序



### 2.2 单调栈基础例题

[739.每日温度](https://leetcode.cn/problems/daily-temperatures/)
包括单调增和单调减栈,从右往左遍历，此时发现5比2，3大，因此可以去除2和3。降序栈。**已经不会是别人答案的数，不需要放在栈里。**从左往右遍历，降序栈。**已经拥有答案的数，不需要放在栈里。**

<img src="/images/stack/daily-temperatures.png" alt="Alt text" style="zoom:50%;" />

[84. Largest Rectangle in Histogram](https://leetcode.cn/problems/largest-rectangle-in-histogram/)
前后两个哨兵节点[0]。找左右第一个**更小**的元素用**升序栈**。当栈顶从栈里 pop 出来的时候，更新的答案高为heigh[栈顶],width（这个矩形的左右边界）为此时的宽度,计算面积.

[85.最大矩形](https://leetcode.cn/problems/maximal-rectangle/)
84题升级版,二维问题拆解成m次的一维问题,看成一种生长的柱子,关键规则:一旦遇到0,不管之前柱子多高都归零.84写的不熟练

[1944. 队列中可以看到的人数](https://leetcode.cn/problems/number-of-visible-people-in-a-queue/)
因为是从左往右看,所以从右往左遍历，用降序栈。一旦有更大的元素入栈，则**循环把比它小的元素移出栈**，这几个人被他挡住了，以后不会再被别人看到，且当前人能看到他们。待循环结束后，如果此时栈中还有元素，则他看到的人数再+=1。



### 2.3 字典序与数字大小

[316. 去除重复字母](https://leetcode.cn/problems/remove-duplicate-letters/)
单调递增栈,需要一个counter计数和一个set记类,注意弹出的条件

[402. 移掉 K 位数字](https://leetcode.cn/problems/remove-k-digits/)
lstrip("0")去掉前导0,和316一样,单调递增栈,但是限额弹出k次.注意细节处理,遍历完了但是k没用完,贪心弹出最后的,



### 2.4 单调栈变形

[962. 最大宽度坡](https://leetcode.cn/problems/maximum-width-ramp/) 
起点从左往右递减栈,如果j>i,nums[j]>nums[i],在贪心下j不会回比i更有机会更远,所以不入栈 
终点从右往左比较,j>i,j>stacke[-1],i>stack[-1],所以i才是离stack[-1]最远的距离,所以一完成出栈条件就弹出,当碰到无法出栈就移动到下一个

[1124. 表现良好的最长时间段](https://leetcode.cn/problems/longest-well-performing-interval/)
前缀和+降序栈,较难,思路是找起点和终点,相减是长度,起点从左往右找,终点从右往左找,需要两次遍历,先找起点,再找长度,注意从0开始,前缀和从0,以及栈本身里面就有0



### 2.5 把数组变为零

todo

