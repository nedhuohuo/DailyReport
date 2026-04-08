# DailyReport

一个低成本的开发者日报/周报/月报生成工具。它既可以作为 `skill` 被 Codex 等工具发现，也可以在支持插件命令的 AI 工具中显示为菜单命令。

## 功能特性

- 📊 **自动生成报告** - 基于 Git 提交历史生成日报、周报、月报
- 🔍 **多仓库支持** - 扫描工作区，自动发现和管理多个 Git 仓库
- 📝 **Obsidian 兼容** - 输出标准 Markdown，支持 YAML frontmatter 和标签
- 🤖 **AI 驱动** - 使用 AI 总结代码变更，生成人类可读的报告
- ⚡ **Token 优化** - 周报/月报优先汇总已有报告，减少 API 调用
- 🔒 **只读安全** - 所有 Git 操作均为只读，不会修改仓库

## 安装

### 要求

- Python 3.11+
- Git
- AI 工具: Codex、Claude Code、Cursor、Qoder 中的任意一种

## 支持矩阵

| 平台 | 安装方式 | Skill 自动触发 | 菜单命令 |
|------|----------|----------------|----------|
| Codex | `~/.agents/skills` | 支持 | 不保证 |
| Claude Code | 插件 | 支持 | 支持 |
| Cursor | 插件 | 支持 | 支持 |
| Qoder | skill/命令目录 | 支持 | 待验证 |

## 安装

### Codex

Codex 当前按原生 skill 发现工作，不承诺 `/` 菜单命令。

1. 克隆仓库：
```bash
git clone https://github.com/nedhuohuo/DailyReport.git ~/.codex/daily-report
```

2. 链接 skill：
```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/daily-report/skills/daily-report ~/.agents/skills/daily-report
```

3. 重启 Codex。

4. 使用方式：
```text
生成今天的日报
初始化 DailyReport
查看 DailyReport 配置
```

详细安装说明见 [`.codex/INSTALL.md`](./.codex/INSTALL.md)。

### Claude Code / Cursor

这两个工具走插件布局，命令位于仓库根目录的 `commands/`，skill 位于 `skills/`。

标准命令名：

```text
/daily-report:dr_init
/daily-report:dr_daily
/daily-report:dr_weekly
/daily-report:dr_monthly
/daily-report:dr_status
```

仓库中对应的插件清单文件：

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.cursor-plugin/plugin.json`

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
3. 扫描并发现 Git 仓库
4. 保存配置到 `~/.config/dailyreport/config.json`

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
  "workspace_root": "/path/to/your/workspace",
  "output": {
    "vault_dir": "/path/to/obsidian/vault",
    "base_folder": "DailyReport"
  },
  "repositories": [
    {
      "path": "/path/to/repo1",
      "name": "repo1",
      "git_user": {
        "name": "Your Name",
        "email": "your@email.com"
      }
    }
  ],
  "defaults": {
    "level": "standard",
    "language": "zh-CN"
  }
}
```

## 输出示例

报告将保存到 Obsidian 仓库的以下位置:

- 日报: `<vault>/DailyReport/daily/2026-04-08.md`
- 周报: `<vault>/DailyReport/weekly/2026-W14.md`
- 月报: `<vault>/DailyReport/monthly/2026-04.md`

## 版本历史

参见 [CHANGELOG.md](./CHANGELOG.md)

## 许可证

MIT
