# Short Video Script Skill

一个用于把主题、文章、技术问题、产品说明、论文摘要等内容转成短视频脚本、分镜和发布文案的 AI Skill。

## 适合场景

- 技术科普：AI、编程、工程实践、架构设计、踩坑复盘
- 泛知识科普：商业、心理、历史、社会、常识解释
- 产品/项目介绍：工具、SaaS、开源项目、功能发布
- 职场经验：方法论、成长复盘、求职经验、沟通协作
- 论文/技术文章转短视频：摘要解读、论文亮点、研究方法科普

## 推荐用法

把本仓库作为 Skill 加入 OpenClaw、Claude Code、其他 Agent 框架或你自己的智能体系统中。

第一版是**纯提示词 Skill**，不在 Skill 内部请求大模型，所以不需要配置 API Key。

宿主 Agent 读取 `SKILL.md` 后，会根据用户输入自动选择分类，并按多步流程生成结果。

## 目录结构

```text
short-video-script-skill/
├── SKILL.md
├── README.md
├── prompts/
│   ├── 00_common/
│   ├── technical/
│   ├── general_knowledge/
│   ├── product_marketing/
│   ├── career_experience/
│   └── paper_to_video/
├── examples/
├── feedback/
└── .github/ISSUE_TEMPLATE/
```

## 输出结果

最终只输出给用户看的 Markdown 版本，不额外输出 JSON 或 XML 结构化块

详见 `prompts/00_common/03_output_contract.md`。

## 示例效果

### 输入

> 请把“BGE-M3 稀疏向量是什么”改写成一个 60 秒小红书短视频脚本

### 输出片段

**推荐标题：**

为什么你的 RAG 召回总漏关键信息？试试 BGE-M3 稀疏向量

**开头 3 秒钩子：**

你的 RAG 搜不到「Transformer」这个词？问题可能出在向量上。

**口播片段：**

大部分人做向量检索，只知道稠密向量。把文本变成一串浮点数，语义相近就聚在一起。  
但它有个问题：对罕见词、专有名词和精确匹配不一定稳定。

这就是稀疏向量出场的地方。你可以把它理解成「关键词加权向量」：它会判断哪些词对当前文本更重要，然后给这些词更高的权重。

BGE-M3 的特点是可以同时输出稠密向量和稀疏向量。稠密向量更适合语义理解，稀疏向量更适合精确匹配。两者结合，通常更适合 RAG 和 AI 搜索场景。

完整示例见：[`examples/tech-ai-bge-m3-sparse-vector.md`](examples/tech-ai-bge-m3-sparse-vector.md)

示例效果图：

![`images/1783231156829.jpg`](images/1783231156829.jpg)

## 反馈

可以通过 GitHub Issue 或 `feedback/feedback_template.md` 反馈生成质量。


## v0.1.2 优化点

- 默认输出更接近“可拍成稿”，减少冗长中间过程。
- 加强 30 秒、60 秒、3 分钟脚本的字数和节奏约束。
- 修复 Markdown 表格列数一致性要求。
- 技术架构类内容增加“最小实现方式”和“能力边界”要求。
- 分镜输出拆成“轻量版拍摄建议”和“完整分镜表”，降低执行成本。
- 收敛“变聪明”“自主进化”等容易夸张的表达，正文必须解释边界。
