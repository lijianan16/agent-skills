# 来源说明

这些来源都不需要登录对应网站。某一路失败就跳过，不要编造结果。

| 来源 | 脚本 | 实际拿到的内容 | 容易失败的情况 |
|---|---|---|---|
| Hacker News | `search_web.py` | 近 7 天 story，含时间、分数、评论数 | 很少失败 |
| DuckDuckGo | `search_web.py` | 网页标题和摘要，通常没有发布时间 | 页面结构变化会变 0 条 |
| Bing | `search_web.py` | 网页标题和摘要，通常没有发布时间 | 验证码或页面结构变化会变 0 条 |
| Bilibili | `search_china.py` | 按发布时间排序的公开视频 | 接口返回非 0 code |
| 微博 | `search_china.py` | 热搜榜里和关键词对得上的话题，不是微博正文 | 关键词不在热搜榜就是 0 条 |
| 搜狗 | `search_china.py` | 网页标题和摘要；链接经常是搜狗跳转 | 页面结构变化会变 0 条 |
| Twitter | `search_twitter.py` | 近 3 天原创推文，去掉转推和纯回复 | 没设置 `TWITTER_API_KEY` 就跳过 |
| GitHub 新仓库 | `search_github.py` | 近 30 天创建、star 超过 50、带 `llm` / `ai-agents` / `mcp` / `agent-skills` 主题，并排除 `awesome-list` | 未登录搜索大约每分钟 10 次；超限就停，保留已经拿到的结果 |
| GitHub 仍热仓库 | `search_github.py` | 近 90 天到 31 天之间创建、当前 star 超过 400、最近 14 天有推送、主题是 `llm` 或 `ai-agents` | 未登录搜索大约每分钟 10 次；超限就停，保留已经拿到的结果 |

`TWITTER_API_KEY` 是 [twitterapi.io](https://twitterapi.io) 的 Key，不是 X 的登录密码。

GitHub 不带参数时用上面的 AI 应用主题；传入具体技术名时，改为在仓库名和描述里搜这个词，新仓库 star 门槛降到 30，仍热仓库降到 100。一次报告只调用一次。`likeCount` 是仓库当前 star 数，`viewCount` 是 fork 数。

Bilibili 请求里的 `buvid3` 是访客标识，不是账号 Cookie。`--detect-account` 只在关键词像 UP 主名字时使用：名字一致，或粉丝超过 1000 且名字包含关键词，才拉该账号最新视频。
