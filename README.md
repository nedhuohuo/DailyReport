# DailyReport

一个低成本的开发者日报/周报/月报生成工具。通过分析多个 Git 仓库的活动，生成兼容 Obsidian 的 Markdown 报告。

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
- AI 工具: Codex 或 Qoder

### 安装步骤

1. 克隆仓库到本地:
```bash
git clone https://github.com/nedhuohuo/DailyReport.git
```

2. 链接到 AI 工具 skill 目录:

**对于 Qoder:**
```bash
ln -s $(pwd)/DailyReport/daily-report ~/.qoder/skills/daily-report
```

**对于 Codex:**
```bash
ln -s $(pwd)/DailyReport/daily-report ~/.codex/skills/daily-report
```

3. 重启 AI 工具以加载 skill

## 使用方法

### 初始化配置

首次使用前需要初始化配置:

```
/dr_init
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
```
/dr_daily
```
或说: "生成今天的日报"

参数:
- `--level=brief|standard|detailed` - 详细程度（默认: standard）
- `--date=YYYY-MM-DD` - 指定日期（默认: 今天）

#### 周报
```
/dr_weekly
```
或说: "生成本周报"

参数:
- `--level=brief|standard|detailed` - 详细程度（默认: brief）
- `--diff` - 包含 diff 分析

#### 月报
```
/dr_monthly
```
或说: "生成本月报"

参数:
- `--level=brief|standard|detailed` - 详细程度（默认: brief）
- `--diff` - 包含 diff 统计

#### 查看状态
```
/dr_status
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
daily-report/
├── SKILL.md              # Skill 定义文件
├── commands/             # 斜杠命令定义
│   ├── dr_init.md
│   ├── dr_daily.md
│   ├── dr_weekly.md
│   ├── dr_monthly.md
│   └── dr_status.md
├── references/           # 参考文档
│   ├── COMMANDS.md
│   ├── CONFIG.md
│   └── TEMPLATES.md
└── scripts/              # Python 脚本
    ├── dr_scan.py        # 仓库扫描
    ├── dr_analyze.py     # Git 分析
    └── dr_common.py      # 公共模块
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
