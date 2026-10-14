# 示例：LangChain Agent 为什么重复调用工具？

## 用户输入

LangChain Agent 为什么会重复调用工具？

## 推荐分类

technical

## 推荐题目类型

故障排查

## 期望输出重点

- 不要简单归因于 LangChain bug
- 解释工具返回不明确、缺少终止信号、observation 不清晰等原因
- 区分：
  - 调试手段：trace、callback、LangSmith
  - 兜底手段：max_iterations、timeout
  - 根治方案：结构化工具返回、status、summary、result、next_action
