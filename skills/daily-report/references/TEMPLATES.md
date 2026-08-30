# DailyReport 报告模板

## 模板文件

实际渲染使用 Skill 目录下的独立模板文件作为输出源：

| 报告类型 | 模板文件 | 渲染脚本 |
|----------|----------|----------|
| 日报 | `templates/daily.md` | `scripts/dr_render.py --type daily` |
| 周报 | `templates/weekly.md` | `scripts/dr_render.py --type weekly` |
| 周报 HTML | `templates/weekly.html` | 复制模板后只替换正文占位符 |
| 月报 | `templates/monthly.md` | `scripts/dr_render.py --type monthly` |

`dr_render.py` 负责稳定填充 YAML frontmatter、统计字段和报告骨架；周报正文必须按任务/功能主题组织，不能按仓库活动组织。

---

## 三级详细度说明

| 等级 | 标识 | 说明 | 默认用于 |
|------|------|------|---------|
| 粗略 | `brief` | 高度概括，按任务/功能主题汇总 | 周报、月报 |
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
repos_scanned: 87
repos_active: 2
commits_total: 7
authors:
  - nedhuo
groups:
  - im
  - zhy
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
# 今日工作进展日报

汇报日期： YYYY年M月D日

核心工作进展： 今日聚焦[核心工作概述]，具体进展如下：

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

### 周报基础规范

1. **汇报周期**：标题明确本周起止日期，格式 `{汇报人}汇报周期: YYYY年M月D日 — YYYY年M月D日`（示例：`张三汇报周期: 2026年7月27日 — 2026年7月31日`）。
2. **三大固定板块**：`一、本周总结` → `二、本周任务完成情况` → `三、下周工作计划`。
3. **任务进展用表格**：清晰罗列事项与完成状态（默认 `事项 | 状态` 两列）；单个任务功能条目不超过 4 条（相近子项合并）；未完成任务须额外备注阻碍原因、预计完成时间（写入状态文案，或仅在有未完成项时才加备注列）。
4. **状态色标**（推荐 `<font color="...">`，Obsidian 可渲染）：
   - 蓝色 = 进行中：`<font color="blue">进行中</font>`
   - 已完成：`✅ 已完成`（带 ✅，文字不用绿色）
   - 红色 = 异常或存在风险：`<font color="red">存在风险</font>`

### 周报正文规则

周报模板用于面向人汇报工作，不展示 Git 流水账。正文固定为上述三节结构：

1. **本周总结**：叙述本周重点工作与推进情况（纯业务语言）。
2. **本周任务完成情况**：按 `任务一/二/三` 组织，子项用状态表格呈现（默认 `事项 | 状态`）。
3. **下周工作计划**：编号列表。

其他规则：

- 一级任务标题优先使用可确认的需求/功能主题（如 `合伙人需求·支付对接·自测·提测`）。
- 无法确认需求名称时，任务标题可留空，只在表格中列出具体事项。
- 大任务可拆成编号子节（`1. 2. 3.`），每个子节配一张状态表；简单任务可直接一张表。
- 状态列示例：`✅ 已完成`、`✅ 完成自测`、`<font color="blue">进行中</font>`、`<font color="red">存在风险</font>`。
- 单个任务下功能/事项行不超过 4 条；超出时合并相近子项后再入表。
- 未完成（进行中/风险）须写明阻碍原因 + 预计完成时间；默认写在状态文案中。仅当确有未完成项需要单独说明时，才增加「备注」列。已完成任务不加空备注列。
- 不在正文展示 commit hash、仓库活跃状态、文件数、代码增删行。
- 格式化、资源引用等支撑性工作归入 `任务N：其他/支撑性调整`。
- 保留产品界面/页面维度，不能把独立页面建设合并进泛泛的“业务流程”或“界面优化”。
- 宿主 App 使用固定名称：`zhb-AppShell` 为“挚护办”，`zhy-AppShell` 和 `zhy-ModuleMain` 为“挚护易”，不得把 `zhy` 宿主写成“挚护医”。
- 标题使用 `{汇报人}汇报周期: YYYY年M月D日 — YYYY年M月D日`；汇报人优先取 `--reporter`，否则回退到作者名。

### 周报质量验收清单

生成后检查：

- 是否明确填写了本周起止日期。
- 是否采用“总结 / 任务完成情况 / 下周计划”三节结构。
- 任务进展是否使用表格，状态是否按蓝/绿/红色标区分，完成项是否带 ✅。
- 单个任务下事项是否不超过 4 条。
- 未完成任务是否备注了阻碍原因与预计完成时间。
- 主任务是否是业务能力/页面/需求，而不是 commit 或仓库。
- 任务是否使用 `任务一/二/三` + 状态表格。
- 是否先从 diff 中提取足够多的事实，再压缩为少量周报事项。
- 大任务是否按子主题拆成编号小节或表格行。
- 面试管理页面、会议房间、邀请分享、音视频录制、基础接口等业务面是否被正确保留。
- 格式化、资源引用、图片优化、代码提交等是否被降级到 `其他/支撑性调整`。
- `zhy-AppShell`、`zhy-ModuleMain` 是否统一使用宿主名称“挚护易”。

### Frontmatter

```yaml
---
title: "周报 YYYY-Www"
date: YYYY-MM-DD
type: weekly-report
level: brief
repos_scanned: 87
repos_active: 6
commits_total: 24
authors:
  - nedhuo
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
# 张三汇报周期: YYYY年M月D日 — YYYY年M月D日

## 一、本周总结

本周重点围绕[核心工作 A]、[核心工作 B]、[核心工作 C]推进。
[补充本周时间线、关键交付与上线/提测情况，使用业务语言描述。]

## 二、本周任务完成情况

**任务一：合伙人需求·支付对接·自测·提测**

1. 支付渠道调试自测

| 事项 | 状态 |
|------|------|
| 微信支付 | ✅ 已完成 |
| 支付宝 | ✅ 已完成 |

2. 关联业务支付功能自测

| 事项 | 状态 |
|------|------|
| 体检预约支付 | <font color="blue">进行中</font>（等待联调环境；预计下周三完成） |

**任务二：推包回归任务支持**

| 事项 | 状态 |
|------|------|
| 合同管理 | ✅ 已完成 |
| 订单池 3.0 | ✅ 已完成 |

**任务三：合同管理·Bug修复**

| 事项 | 状态 |
|------|------|
| 合同列表 UI 优化 | <font color="red">存在风险</font>（依赖设计稿未定稿；预计下周五） |

## 三、下周工作计划

1. 跟进合伙人支付模块测试进度，修复测试中发现的问题。
```

### 周报 HTML 样式锁定

需要 HTML 时，必须以 `templates/weekly.html` 为唯一样式源：

1. 原样复制 `<style>` 块（含 `WEEKLY_HTML_STYLE_LOCKED` 注释），禁止改写、禁止另起皮肤。
2. 结构固定为 `.page` 卡片：`h1` 标题 → `一、本周总结` → `二、本周任务完成情况`（`.task-title` / 可选 `.sub-title` + 表格）→ `三、下周工作计划`（`ol`）→ `.footer`。
3. 状态格使用 `td.status`，文案与 Markdown 一致：`✅ 已完成`、`<font color="blue">进行中</font>`、`<font color="red">存在风险</font>`。
4. 禁止使用深色顶栏、圆形任务序号、状态圆点、自定义编号列表等另一套视觉。

占位符：`{weekly_header}`、`{weekly_summary_html}`、`{weekly_task_sections_html}`、`{weekly_next_plan_items_html}`、`{week_id}`。

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
repos_scanned: 87
repos_active: 14
commits_total: 103
authors:
  - nedhuo
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
# 月度工作总结月报

汇报月份： YYYY年M月

月度核心成果： 本月聚焦[核心成果概述]，具体成果如下：

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
