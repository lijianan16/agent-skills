---
name: hot-monitor
description: >-
  从 Hacker News、DuckDuckGo、Bing、Bilibili、微博热搜、搜狗、GitHub 公开仓库和可选 Twitter
  聚合公开热点。GitHub 只覆盖 AI 应用开发方向：近 30 天新建且已有 star 的仓库，以及近 90 天出现、最近 14 天仍在更新的热门仓库。
  由当前智能体判断真假、相关性和重要性，并输出中文热点报告。
  Use when the user asks to monitor a keyword, track what is trending, check the latest news,
  find hot or newly released AI GitHub projects,
  or says 热点、盯一下、最近有什么动态、查一下最新消息、热搜、热点报告、monitor、新技术、新仓库.
---

# 热点监控

输出一份中文热点报告，里面有两块：

1. 某个具体词的公开讨论：Hacker News 近 7 天帖子，DuckDuckGo、Bing、搜狗的网页标题和摘要，Bilibili 按发布时间排的公开视频，微博热搜榜里对得上的话题。本机已有 `TWITTER_API_KEY` 时，再加上近 3 天原创推文。
2. AI 应用方向的 GitHub 仓库：近 30 天创建、当前 star 超过 50 的仓库，以及 30 到 90 天前创建、最近 14 天仍有推送、当前 star 超过 400 的仓库。

脚本只负责抓公开页面和公开接口。真假、相关性、重要性由当前智能体判断，不要调用 OpenRouter 或其他外部大模型。

## 配置

不用先配 Key 就能跑。不需要 OpenRouter，也不用登录微博、B 站或搜索引擎。

脚本在本 `SKILL.md` 同级的 `scripts/`。当前工作区里没有这份代码时，不要现写一套爬虫。

依赖是 `requests`、`beautifulsoup4`。只有 `import` 失败时才安装：

```bash
python3 -m pip install -r "<SKILL_ROOT>/scripts/requirements.txt"
```

可选环境变量只有一个：

| 变量 | 不设置时 |
|---|---|
| `TWITTER_API_KEY` | 跳过 Twitter。这是 [twitterapi.io](https://twitterapi.io) 的 Key，不是 X 的登录密码 |

Hacker News、DuckDuckGo、Bing、Bilibili、微博热搜、搜狗、GitHub 都不需要 Key。没有 `TWITTER_API_KEY` 时不要提示用户必须去申请，报告里写明跳过即可。

GitHub 用公开 Search API，未登录大约每分钟 10 次。一次报告只跑一遍 `search_github.py`，不要按每个检索词各跑一次。

## 流程

1. 确认要盯的关键词。用户没给具体词、只说「最近有什么热点」时，先问领域，不要默认搜一个泛词。
2. 把关键词扩成最多 3 个检索词：原词、常见中英文或缩写、必要时一个更具体的说法。不要把「AI」「模型」这种泛词加进去。
3. 每个检索词跑国际源和中文源。检索词之间间隔约 3 秒。
4. 关键词像 B 站 UP 主名字时，中文源加上 `--detect-account`。
5. 只有环境里已有 `TWITTER_API_KEY` 才跑 Twitter。没有就跳过，并在报告里写明。
6. 用户要 AI 应用方向的新技术、新仓库，或要看当前比较火的 GitHub 项目时，跑一遍不带参数的 `search_github.py`。不要把「AI」「模型」拿去搜新闻。
7. 用户给了具体技术或项目名时，新闻源照旧；GitHub 把这个词传给 `search_github.py`，只跑一遍。
8. 合并 JSON，按 [references/analysis-guide.md](references/analysis-guide.md) 筛选。来源差异见 [references/search-sources.md](references/search-sources.md)。
9. 用下面的模板输出中文报告。某路是 0 条或报错时写出来，不要补假结果。

## 命令

把 `<SKILL_ROOT>` 换成本技能目录。

```bash
python3 "<SKILL_ROOT>/scripts/search_web.py" "关键词" --sources hackernews,duckduckgo,bing --limit 8
python3 "<SKILL_ROOT>/scripts/search_china.py" "关键词" --sources bilibili,weibo,sogou --limit 8
python3 "<SKILL_ROOT>/scripts/search_china.py" "UP主名" --sources bilibili --detect-account --limit 5
python3 "<SKILL_ROOT>/scripts/search_twitter.py" "关键词" --limit 8
python3 "<SKILL_ROOT>/scripts/search_github.py"
python3 "<SKILL_ROOT>/scripts/search_github.py" "具体技术名"
```

标准输出是 JSON 数组。失败信息在标准错误里，单路失败不影响其他路。

每条字段：`title`、`content`、`url`、`source`、`publishedAt`、`authorName`、`viewCount`、`likeCount`、`commentCount`。

## 报告

```markdown
## 热点报告 — {关键词}
> 扫描时间: {时间} | 检索词: {词1、词2} | 数据源: {实际用到的源}

### 紧急
- **{标题}** — {一句摘要}
  来源: {source} | 相关性: {relevance} | [原文]({url})

### 重要
...

### 一般
...

### 低优先级
...

### 新发布的仓库
- **{owner/repo}** — {一句说明它做什么，以及能不能直接用来做 AI 应用}
  {stars} stars | 创建 {date} | {language} | [仓库]({url})

### 近期仍热的仓库
- **{owner/repo}** — {一句说明它做什么}
  {stars} stars | 最近推送 {date} | {language} | [仓库]({url})

---
保留 {n} 条。跳过的来源：{名称和原因}
```

报告里的 star 是仓库当前 star 数。仓库写在「新发布的仓库」和「近期仍热的仓库」两节。

没有条目的等级整段省略。相关性不要写模型没判断过的分数。
