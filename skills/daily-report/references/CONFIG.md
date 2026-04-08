# DailyReport 配置文件说明

## 配置文件位置

`~/.config/dailyreport/config.json`

首次执行 `/daily-report:dr_init` 时自动创建。

## 完整结构

```json
{
  "version": 1,
  "workspace_root": "/Users/username/Projects",
  "output": {
    "vault_dir": "/Users/username/ObsidianVault",
    "base_folder": "DailyReport",
    "daily_folder": "daily",
    "weekly_folder": "weekly",
    "monthly_folder": "monthly"
  },
  "defaults": {
    "level": "standard",
    "language": "zh-CN"
  },
  "repositories": [
    {
      "path": "/Users/username/Projects/my-app",
      "name": "my-app",
      "git_user": {
        "name": "Zhang San",
        "email": "zhangsan@company.com"
      },
      "registered_at": "2026-04-07T10:00:00"
    }
  ],
  "scan_settings": {
    "max_depth": 5,
    "skip_dirs": ["node_modules", "vendor", "__pycache__", ".venv", "venv", "dist", "build", ".build", "Pods", ".gradle"],
    "skip_diff_patterns": ["*.lock", "*-lock.json", "*.min.js", "*.min.css", "*.map", "dist/*", "build/*", ".next/*", "coverage/*", "__snapshots__/*"]
  }
}
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | number | Y | 配置格式版本号，当前为 1 |
| `workspace_root` | string | Y | 工作区根目录绝对路径 |
| `output.vault_dir` | string | Y | Obsidian vault 根目录绝对路径 |
| `output.base_folder` | string | Y | 报告根文件夹名（在 vault 内） |
| `output.daily_folder` | string | Y | 日报子文件夹名 |
| `output.weekly_folder` | string | Y | 周报子文件夹名 |
| `output.monthly_folder` | string | Y | 月报子文件夹名 |
| `defaults.level` | string | N | 默认详细度：`brief` / `standard` / `detailed` |
| `defaults.language` | string | N | 报告语言，默认 `zh-CN` |
| `repositories` | array | Y | 已注册仓库列表 |
| `repositories[].path` | string | Y | 仓库绝对路径 |
| `repositories[].name` | string | Y | 仓库显示名称（默认取目录名） |
| `repositories[].git_user.name` | string | Y | 该仓库绑定的 Git 用户名 |
| `repositories[].git_user.email` | string | Y | 该仓库绑定的 Git 邮箱 |
| `repositories[].registered_at` | string | Y | ISO 8601 注册时间 |
| `scan_settings.max_depth` | number | N | 扫描深度上限，默认 5 |
| `scan_settings.skip_dirs` | array | N | 扫描时跳过的目录名列表 |
| `scan_settings.skip_diff_patterns` | array | N | diff 分析时跳过的文件 glob 模式 |

## 用户修改指南

- `repositories[].git_user` 为只读字段，由 `/daily-report:dr_init` 扫描时自动填充
- 如需修改某仓库的 Git 用户信息，请先在对应仓库执行 `git config user.name "新名字"` 和 `git config user.email "新邮箱"`，然后重新执行 `/daily-report:dr_init` 扫描
- `scan_settings` 中的配置可手动编辑，调整扫描和 diff 过滤行为
- `output` 中的文件夹名可自定义，修改后新报告将输出到新路径
