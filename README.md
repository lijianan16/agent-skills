# Agent Skills

个人智能体技能仓库，用于持续收集、维护和复用技能。

## 技能目录

| 技能 | 用途 | 入口 |
| --- | --- | --- |
| hot-monitor | 聚合公开热点，发现 AI 应用方向的新仓库和近期热门仓库 | [SKILL.md](skills/hot-monitor/SKILL.md) |
| short-video-script-skill | 把文章或主题整理成短视频口播稿和镜头安排 | [SKILL.md](skills/short-video-script-skill/SKILL.md) |
| jianying-editor | 把素材导入剪映，拼接画面并加入配音、字幕和背景音乐 | [SKILL.md](skills/jianying-editor/SKILL.md) |

## 仓库结构

```text
skills/
  hot-monitor/
    SKILL.md
    scripts/
    references/
  short-video-script-skill/
    SKILL.md
    prompts/
    examples/
  jianying-editor/
    SKILL.md
    scripts/
    rules/
```

每个技能使用独立目录，技能说明、脚本和参考资料放在一起。

## 使用 hot-monitor

将 `skills/hot-monitor/` 完整放入智能体支持的技能目录，然后让智能体读取 `SKILL.md`。

需要 Python 3.9 或更新版本，以及 `requests` 和 `beautifulsoup4`：

```bash
python3 -m pip install -r skills/hot-monitor/scripts/requirements.txt
```

可以向智能体说：

- 帮我查一下最近 Claude Code 有什么热点。
- 给我一份 OpenAI 热点报告。
- 看看近期 AI 应用方向的新 GitHub 仓库。

也可以直接运行脚本获取 JSON：

```bash
python3 skills/hot-monitor/scripts/search_github.py
python3 skills/hot-monitor/scripts/search_web.py "OpenAI" --sources hackernews,duckduckgo,bing --limit 8
```

公开来源无需登录。Twitter 为可选来源，需要通过环境变量设置 twitterapi.io 的 `TWITTER_API_KEY`。不要将 Key 提交到仓库。抓取结果由智能体判断相关性和重要性；部分来源可能受限、报错或没有结果。

## 添加或更新技能

1. 在 `skills/` 下创建以技能名命名的目录。
2. 放入 `SKILL.md`，以及技能所需的 `scripts/`、`references/`、`assets/` 等文件。
3. 在上面的技能目录表中添加一行。
4. 检查并排除密钥、账号配置、运行输出和缓存，再提交修改。

更新技能时直接修改对应目录，保留 Git 提交历史。第三方技能请保留其原始许可证和来源说明。
