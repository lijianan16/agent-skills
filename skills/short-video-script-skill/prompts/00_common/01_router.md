# 分类路由规则

根据用户输入选择一个主分类。

## technical

适用于：AI、Agent、RAG、MCP、LangChain、Qdrant、vLLM、编程语言、框架、部署、数据库、工程问题、架构设计、系统设计、技术踩坑、故障排查。

示例：

- LangChain Agent 为什么重复调用工具？
- 如何设计一个自主进化的 Agent？
- RAG 为什么召回不准？

## general_knowledge

适用于：商业、心理、历史、社会、生活常识、科学常识，用户想把一个知识点讲给普通人听。

## product_marketing

适用于：产品介绍、项目介绍、开源工具介绍、功能发布，用户想做宣传、转化、展示卖点。

## career_experience

适用于：工作方法、成长经验、求职、面试、职场沟通、个人复盘、项目经验、学习路线。

## paper_to_video

适用于：用户提供论文标题、摘要、技术文章、研究成果，目标是把长文或论文改成科普短视频。

## 多分类冲突处理

- 有论文/文章正文：优先 `paper_to_video`
- 明确介绍产品/项目：优先 `product_marketing`
- 技术故障、架构、工具原理：优先 `technical`
- 工作经验、成长复盘：优先 `career_experience`
- 其他知识解释：使用 `general_knowledge`
