# 示例：如何设计一个自主进化的 Agent？

## 用户输入

如何设计一个自主进化的 Agent？

## 推荐分类

technical

## 推荐题目类型

架构设计

## 期望输出重点

- 不要把自主进化讲成让 Agent 自己随便改代码
- 核心观点：自主进化不是全自动，而是可评估、可约束、可回滚
- 设计闭环：执行任务、收集反馈、评估打分、生成候选策略、离线验证、灰度上线、失败回滚
- 核心组件：Evaluator、Memory、Policy Updater、Validator、Rollback Manager、Guardrails
