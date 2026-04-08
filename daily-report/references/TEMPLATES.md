# DailyReport 报告模板

## 三级详细度说明

| 等级 | 标识 | 说明 | 默认用于 |
|------|------|------|---------|
| 粗略 | `brief` | 高度概括，每仓库 2-3 行 | 周报、月报 |
| 标准 | `standard` | 适中详细度，关键变更说明 | 日报 |
| 详细 | `detailed` | 完整技术细节，逐 commit 分析 | 按需指定 |

---

## 日报模板

### Frontmatter

```yaml
---
title: "日报 YYYY-MM-DD"
date: YYYY-MM-DD
type: daily-report
level: standard
tags:
  - daily-report
  - YYYY-MM
repos:
  - repo-name-1
  - repo-name-2
generated: YYYY-MM-DDTHH:mm:ss
---
```

### 正文结构

```markdown
# 日报 -- YYYY-MM-DD (星期X)

## 概览

> [!summary]
> 今日在 N 个仓库中共提交 M 次，变更 F 个文件（+A / -D 行）。
> 主要工作集中在 [核心工作概述]。

## 仓库详情

### repo-name-1

**分支：** `feature/xxx` | **提交：** N 次 | **变更：** +A / -D 行

#### 提交记录
- `abc1234` feat: 添加用户认证模块
- `def5678` fix: 修复分页查询问题

#### 关键变更
（standard/detailed 级别包含此部分）
- **src/auth/login.ts** (+45/-3) -- 新增 JWT 验证逻辑
- **src/api/users.ts** (+12/-8) -- 修复 offset 参数计算错误

#### 分支操作
（有分支操作时包含此部分）
- 创建分支 `feature/auth-v2`
- 合并 `hotfix/pagination` -> `main`

### repo-name-2
（同上结构...）

## 今日总结

[AI 生成的总结性段落，概括今日工作重点和进展]

---
> 由 DailyReport Skill 自动生成
```

### 各详细度差异

| 部分 | brief | standard | detailed |
|------|-------|----------|----------|
| 概览 | 一句话 | 2-3 句 | 完整概述 |
| 提交记录 | 仅数量 | 列出所有 | 列出所有+详细说明 |
| 关键变更 | 不包含 | 重要文件概述 | 逐文件分析+代码引用 |
| 分支操作 | 不包含 | 有则列出 | 详细时间线 |
| 总结 | 一句话 | 一段 | 详细分析+下步计划 |

---

## 周报模板

### Frontmatter

```yaml
---
title: "周报 YYYY-Www"
date: YYYY-MM-DD
type: weekly-report
level: brief
tags:
  - weekly-report
  - YYYY-MM
week: YYYY-Www
date_range:
  from: YYYY-MM-DD
  to: YYYY-MM-DD
repos:
  - repo-name-1
  - repo-name-2
source: daily-summary
generated: YYYY-MM-DDTHH:mm:ss
---
```

### 正文结构

```markdown
# 周报 -- YYYY 第 W 周 (MM-DD ~ MM-DD)

## 本周概览

> [!summary]
> 本周在 N 个仓库中共提交 M 次，完成 K 个功能/修复。
> 核心进展：[一句话概括]。

## 重点工作

### 1. [工作主题一：如"用户认证系统重构"]
- **涉及仓库：** repo-name-1
- **进展：** [2-3 句描述]
- **关键产出：** N 个提交，涉及 F 个文件

### 2. [工作主题二]
（同上结构...）

## 各仓库活动汇总

| 仓库 | 提交数 | 变更文件 | 新增/删除 | 主要工作 |
|------|--------|----------|-----------|----------|
| repo-1 | 12 | 25 | +340/-120 | 认证模块重构 |
| repo-2 | 5 | 8 | +60/-20 | Bug 修复 |

## 本周回顾

[AI 生成的回顾段落]

---
> 由 DailyReport Skill 自动生成 | 数据来源：日报汇总
```

### source 字段说明

| 值 | 含义 |
|----|------|
| `daily-summary` | 基于日报内容汇总生成 |
| `daily-summary+diff` | 日报汇总 + diff 分析补全 |
| `diff-analysis` | 直接 Git 分析（无日报可用时） |

---

## 月报模板

### Frontmatter

```yaml
---
title: "月报 YYYY-MM"
date: YYYY-MM-01
type: monthly-report
level: brief
tags:
  - monthly-report
  - YYYY
month: YYYY-MM
date_range:
  from: YYYY-MM-DD
  to: YYYY-MM-DD
repos:
  - repo-name-1
  - repo-name-2
source: weekly-summary
generated: YYYY-MM-DDTHH:mm:ss
---
```

### 正文结构

```markdown
# 月报 -- YYYY年M月

## 月度概览

> [!summary]
> 本月在 N 个仓库中共提交 M 次，变更 F 个文件（+A / -D 行）。
> 活跃天数 D 天，周均提交 X 次。

## 月度统计

| 指标 | 数值 |
|------|------|
| 活跃仓库数 | N |
| 总提交数 | M |
| 总文件变更 | F |
| 代码新增 | +A 行 |
| 代码删除 | -D 行 |
| 活跃天数 | D / 工作日总数 |

## 核心成果

### 1. [成果主题一]
- **时间跨度：** 第 W1-W2 周
- **涉及仓库：** repo-name
- **概述：** [3-5 句描述]

### 2. [成果主题二]
（同上...）

## 各周活动回顾

### 第 W1 周 (MM-DD ~ MM-DD)
- [来自周报的精简概要]

### 第 W2 周
（同上...）

## 仓库活跃度

| 仓库 | 提交 | 变更文件 | +/- | 活跃天数 |
|------|------|----------|-----|----------|
| repo-1 | 45 | 120 | +2000/-800 | 18 |
| repo-2 | 12 | 30 | +300/-100 | 8 |

## 月度总结

[AI 生成的总结段落]

---
> 由 DailyReport Skill 自动生成 | 数据来源：周报+日报汇总
```

---

## Obsidian 兼容性说明

- 所有报告使用标准 YAML frontmatter
- tags 字段供 Obsidian 标签系统使用
- 使用 `> [!summary]` callout 语法（Obsidian 原生支持）
- 文件命名规范确保在 Obsidian 文件列表中按时间排序
- 不使用 wikilink，保持纯 Markdown 兼容性
