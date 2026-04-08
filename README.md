# DailyReport

一个低成本的开发者日报/周报/月报生成工具。它既可以作为 `skill` 被 Codex 等工具发现，也可以在支持插件命令的 AI 工具中显示为菜单命令。

## 功能特性

- 📊 **自动生成报告** - 基于 Git 提交历史生成日报、周报、月报
- 🔍 **多仓库支持** - 扫描工作区，自动发现和管理多个 Git 仓库
- 🧭 **动态仓库发现兜底** - 当配置中的 `repositories` 为空时，分析脚本会基于 `workspace_root` 自动发现仓库
- 📝 **Obsidian 兼容** - 输出标准 Markdown，支持 YAML frontmatter 和标签
- 🤖 **AI 驱动** - 使用 AI 总结代码变更，生成人类可读的报告
- ⚡ **Token 优化** - 周报/月报优先汇总已有报告，减少 API 调用
- 🔒 **只读安全** - 所有 Git 操作均为只读，不会修改仓库
- 🚀 **分析性能优化** - 多仓库分析使用线程池并发执行，降低日报生成等待时间

## 安装

### 要求

- Python 3.11+
- Git
- AI 工具: Codex、Claude Code、Cursor、Qoder 中的任意一种

## 支持矩阵

| 平台 | 安装方式 | Slash 命令菜单 | 自然语言触发 |
|------|----------|----------------|--------------|
| Claude Code | `claude plugin install` | ✅ | ✅ |
| Cursor | symlink 到 `~/.cursor/skills/` | ✅ | ✅ |
| Qoder | symlink 到 `~/.agents/skills/` | ✅ | ✅ |
| Codex | symlink 到 `~/.agents/skills/` | ❌ | ✅ |

## 安装

### Claude Code

```bash
# 1. 添加 marketplace
claude plugin marketplace add nedhuohuo/DailyReport

# 2. 安装插件
claude plugin install daily-report
```

安装后即可在 `/` 菜单中使用：

```text
/daily-report:dr_init
/daily-report:dr_daily
/daily-report:dr_weekly
/daily-report:dr_monthly
/daily-report:dr_status
```

### Cursor

```bash
git clone https://github.com/nedhuohuo/DailyReport.git ~/.cursor/skills/daily-report
```

重启 Cursor，即可在 `/` 菜单中使用同名命令。

### Qoder

```bash
git clone https://github.com/nedhuohuo/DailyReport.git ~/.agents/daily-report
mkdir -p ~/.agents/skills
ln -s ~/.agents/daily-report/skills/daily-report ~/.agents/skills/daily-report
```

重启 Qoder，即可在 `/` 菜单中使用同名命令。

### Codex

```bash
git clone https://github.com/nedhuohuo/DailyReport.git ~/.codex/daily-report
mkdir -p ~/.agents/skills
ln -s ~/.codex/daily-report/skills/daily-report ~/.agents/skills/daily-report
```

重启 Codex，通过自然语言触发（不支持菜单命令）：

```text
生成今天的日报 / 生成本周周报 / 初始化 DailyReport
```

## 使用方法

### 初始化配置

首次使用前需要初始化配置:

```text
/daily-report:dr_init
```

或说:
> "帮我初始化 daily report"

初始化过程会:
1. 询问工作区根目录（存放 Git 仓库的位置）
2. 询问 Obsidian 仓库目录（报告输出位置）
3. 校验 Obsidian 路径是否存在，不存在时先确认是否创建
4. 扫描并发现 Git 仓库
5. 保存配置到 `~/.config/dailyreport/config.json`

### 生成报告

#### 日报
```text
/daily-report:dr_daily
```
或说: "生成今天的日报"

参数:
- `--level=brief|standard|detailed` - 详细程度（默认: standard）
- `--date=YYYY-MM-DD` - 指定日期（默认: 今天）

#### 周报
```text
/daily-report:dr_weekly
```
或说: "生成本周报"

参数:
- `--level=brief|standard|detailed` - 详细程度（默认: brief）
- `--diff` - 包含 diff 分析

#### 月报
```text
/daily-report:dr_monthly
```
或说: "生成本月报"

参数:
- `--level=brief|standard|detailed` - 详细程度（默认: brief）
- `--diff` - 包含 diff 统计

#### 查看状态
```text
/daily-report:dr_status
```
或说: "查看 daily report 配置"

### 详细程度说明

| 级别 | 日报 | 周报/月报 |
|------|------|-----------|
| **brief** | 每个仓库: 提交数 + 一行总结 | 汇总提交数和主要变更 |
| **standard** | 提交列表 + 关键文件变更 | 汇总 + 重要变更说明 |
| **detailed** | 逐提交分析 + 完整 diff | 详细分析 + 完整时间线 |

## 项目结构

```
DailyReport/
├── .claude-plugin/       # Claude Code 插件清单
├── .cursor-plugin/       # Cursor 插件清单
├── .codex/               # Codex 安装说明
├── commands/             # 插件级菜单命令入口
├── skills/
│   └── daily-report/
│       ├── SKILL.md
│       ├── commands/     # 兼容旧布局的命令说明
│       ├── references/
│       └── scripts/
└── README.md
```

## 配置说明

配置文件位置: `~/.config/dailyreport/config.json`

```json
{
  "version": 1,
  "workspace_root": "/path/to/your/workspace",
  "output": {
    "vault_dir": "/path/to/obsidian/vault",
    "base_folder": "DailyReport",
    "daily_folder": "daily",
    "weekly_folder": "weekly",
    "monthly_folder": "monthly"
  },
  "defaults": {
    "level": "standard",
    "language": "zh-CN"
  },
  "repositories": [],
  "scan_settings": {
    "max_depth": 5,
    "skip_dirs": ["node_modules", "vendor", "__pycache__", ".venv", "venv", "dist", "build", ".build", "Pods", ".gradle"],
    "skip_diff_patterns": ["*.lock", "*-lock.json", "*.min.js", "*.min.css", "*.map", "dist/*", "build/*", ".next/*", "coverage/*", "__snapshots__/*"]
  }
}
```

说明：
- `repositories` 为空时，`dr_analyze.py` 会回退到基于 `workspace_root` 的动态发现模式
- 推荐仍然通过 `/daily-report:dr_init` 注册仓库，这样可以保留每个仓库的绑定用户和注册时间

## 输出示例

报告将保存到 Obsidian 仓库的以下位置:

- 日报: `<vault>/DailyReport/daily/2026-04-08.md`
- 周报: `<vault>/DailyReport/weekly/2026-W14.md`
- 月报: `<vault>/DailyReport/monthly/2026-04.md`

日报/周报/月报的 frontmatter 会包含结构化统计字段，便于在 Obsidian Dataview 中查询：

```yaml
---
title: "日报 2026-04-08"
date: 2026-04-08
type: daily-report
level: standard
repos_scanned: 12
repos_active: 3
commits_total: 9
authors: [nedhuo]
groups: [DailyReport, goodstudy]
tags:
  - daily-report
  - 2026-04
generated: 2026-04-08T08:00:00
---
```

`standard` 和 `detailed` 日报还应将无活动仓库分为三类展示：
- 近 7 天内活跃：显示仓库名和最后提交日期
- 90 天以上沉默：单独列出，方便识别废弃仓库
- 其他无活动仓库：只显示数量

## 版本历史

参见 [CHANGELOG.md](./CHANGELOG.md)

## 许可证

MIT
