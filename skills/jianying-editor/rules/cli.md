---
name: cli-tools
description: CLI tools for diagnostics, draft inspection, search, and export.
metadata:
  tags: cli, diagnostics, drafts, export
---

# CLI Tools

Prefer these scripts for command-line workflows.

## 1) Draft Inspector (Recommended)

Use `draft_inspector.py` to inspect local drafts quickly.

```bash
# list drafts
python <SKILL_ROOT>/scripts/draft_inspector.py list --limit 20

# summary by draft name
python <SKILL_ROOT>/scripts/draft_inspector.py summary --name "DraftName"

# show full draft JSON
python <SKILL_ROOT>/scripts/draft_inspector.py show --name "DraftName" --kind content --json
python <SKILL_ROOT>/scripts/draft_inspector.py show --name "DraftName" --kind meta --json
```

Notes:

- `--root` can override drafts root.
- `--path` can inspect by absolute draft path.
- `--json` returns machine-readable payload.

## 2) Diagnostics

```bash
python <SKILL_ROOT>/scripts/api_validator.py --json
```

## 3) Asset Search

```bash
python <SKILL_ROOT>/scripts/asset_search.py "复古" -c filters
python <SKILL_ROOT>/scripts/asset_search.py "雾化" -c transitions
```

## 4) Export

```bash
python <SKILL_ROOT>/scripts/auto_exporter.py "DraftName"
python <SKILL_ROOT>/scripts/auto_exporter.py "DraftName" "output.mp4" --res 1080 --fps 60
```

不写输出路径时，macOS 写到 `~/Movies/DraftName.mp4`，Windows 和 Linux 写到 `~/Videos/DraftName.mp4`。`--mode auto` 在 Windows 点剪映导出，在 macOS 用 ffmpeg 拼预览片。`--mode preview` 强制走 ffmpeg，`--mode jianying` 只走 Windows 剪映窗口。缺 ffmpeg 时把报错里的安装命令原样告诉用户，命令见 [rules/setup.md](setup.md)。

## 5) CLI Output Contract

For scripts supporting `--json`, prefer:

```json
{
  "ok": true,
  "code": "ok",
  "reason": "",
  "data": {}
}
```
