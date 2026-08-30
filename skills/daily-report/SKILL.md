---
name: daily-report
description: 'Use when the user asks to generate daily reports, weekly reports, or monthly reports from Git activity, mentions "/daily-report:dr_init", "/daily-report:dr_daily", "/daily-report:dr_weekly", "/daily-report:dr_monthly", or "/daily-report:dr_status", or wants to set up automated development report generation across multiple repositories.'
allowed-tools: Bash, Read, Write, Glob
---

# DailyReport

Low-effort daily/weekly/monthly report generator for developers. Analyzes Git activity across multiple repositories and produces Obsidian-compatible Markdown reports using AI summarization.

## Prerequisites

- Python 3.11+
- Git
- Config file: `~/.config/dailyreport/config.json` (created by `/daily-report:dr_init` or the equivalent natural-language request)

Scripts are located at: `<SKILL_DIR>/scripts/` where SKILL_DIR is the directory containing this SKILL.md.

To resolve SKILL_DIR:
```bash
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)" # if running from skill dir
# Or find via symlink in a home-level skills directory:
SKILL_DIR="$(dirname "$(readlink -f ~/.agents/skills/daily-report/SKILL.md)" 2>/dev/null || dirname "$(readlink ~/.agents/skills/daily-report/SKILL.md)")"
```

## Configuration

Config path: `~/.config/dailyreport/config.json`

Key fields: `workspace_root`, `output` (vault_dir, folder names), `repositories` (path + bound git_user), `scan_settings`, `defaults` (level, language).

See [CONFIG.md](references/CONFIG.md) for full structure and field docs.

## Command Reference

| Command | Purpose | Default | Params |
|---------|---------|---------|--------|
| `/daily-report:dr_init` | Interactive setup | Scan workspace, register repos | — |
| `/daily-report:dr_daily` | Generate daily report | standard + diff | `--level=`, `--date=` |
| `/daily-report:dr_weekly` | Generate weekly report | brief + daily summary | `--level=`, `--diff` |
| `/daily-report:dr_monthly` | Generate monthly report | brief + weekly+daily summary | `--level=`, `--diff` |
| `/daily-report:dr_status` | Show config status | Display all info | — |

On tools without a slash-command menu, the same behaviors should still trigger from natural-language requests such as "generate today's daily report" or "initialize DailyReport".

See [COMMANDS.md](references/COMMANDS.md) for detailed flows and examples.

## Core Workflow: /daily-report:dr_init

This is the entry point. MUST be run before any report generation.

### First-time initialization

1. Ask user for **workspace root directory** (where their Git repos live)
2. Ask user for **Obsidian vault directory** (where reports will be saved)
   Before saving config, verify the path exists. If it does not exist, ask whether to create it:
   ```python
   import os
   if not os.path.isdir(vault_dir):
       # Prompt user: "该路径不存在，是否创建？(y/n)"
       # if yes: mkdir -p vault_dir
       # if no: ask again
   ```
   Do NOT proceed until `vault_dir` is confirmed to exist.
3. Ask user for **default detail level** (optional, defaults to `standard`)
4. Run repo scan:
   ```bash
   python3 "$SKILL_DIR/scripts/dr_scan.py" --workspace "<workspace_root>"
   ```
5. Parse JSON output — it's an array of discovered repos with git user info
6. Display results as a table for user confirmation:
   ```
   | # | Repo Name | Path | Git User | Email | Source |
   ```
   `Source` indicates whether git user is from local repo config or global config.
7. After user confirms, build config object and save:
   ```bash
   # Config is written by the agent using Write tool to ~/.config/dailyreport/config.json
   ```
8. Create output directories:
   ```bash
   mkdir -p "<vault_dir>/DailyReport/daily" "<vault_dir>/DailyReport/weekly" "<vault_dir>/DailyReport/monthly"
   ```

### Adding new repos (re-run /daily-report:dr_init)

When config already exists:
1. Run scan with `--detect-new`:
   ```bash
   python3 "$SKILL_DIR/scripts/dr_scan.py" --workspace "<workspace_root>" --config ~/.config/dailyreport/config.json --detect-new
   ```
2. Show only newly discovered repos
3. Append confirmed repos to existing `repositories` array
4. Do NOT remove existing repos

## Core Workflow: Report Generation

### Shared flow for /daily-report:dr_daily, /daily-report:dr_weekly, /daily-report:dr_monthly

1. **Load config** — Read `~/.config/dailyreport/config.json`. If missing, tell user to run `/daily-report:dr_init` first.

2. **Determine date range and parameters**:
   - `/daily-report:dr_daily`: date from `--date` param (default: today). Range = [date, date+1)
   - `/daily-report:dr_weekly`: current ISO week (Mon-Sun). Range = [monday, sunday+1)
   - `/daily-report:dr_monthly`: current month. Range = [1st, next-month-1st)

3. **Determine detail level**: from `--level` param, fall back to `defaults.level` in config.

4. **Data collection** (varies by report type — see below)

5. **Template rendering**: Render the Markdown report with `scripts/dr_render.py` and the standalone templates in `templates/`. The renderer fills deterministic frontmatter, statistics, repository sections, tables, and footer text. AI may still provide an optional summary via `--summary`.

6. **Write output file** to the appropriate path. Prefer `dr_render.py --output <path>` so the final Markdown follows the selected template.

### /daily-report:dr_daily data collection

Daily reports ALWAYS use diff analysis (this is the foundation of the entire system).

```bash
python3 "$SKILL_DIR/scripts/dr_analyze.py" \
  --config ~/.config/dailyreport/config.json \
  --from <date> --to <date+1> --diff
```

Parse the JSON output. Key fields per active repo: `commits`, `diff_stats`, `diff_content`, `branch_activity`.

Render the daily Markdown with:
```bash
python3 "$SKILL_DIR/scripts/dr_render.py" \
  --type daily \
  --input <analysis.json> \
  --output "<vault>/DailyReport/daily/<YYYY-MM-DD>.md" \
  --date <YYYY-MM-DD> \
  --level <brief|standard|detailed>
```

If `new_repos_detected` is non-empty, the renderer adds a `新发现仓库` section.

### /daily-report:dr_weekly data collection

**Token-efficient strategy**: Weekly reports default to summarizing existing daily reports.

**Decision tree**:
- Check for daily report files in `<vault>/DailyReport/daily/` for dates in the week range
- **Has dailies + no `--diff`** (default): Read daily report files using Read tool. Summarize them. Do NOT call Python scripts. This is the most token-efficient path.
- **Has dailies + `--diff`**: Read dailies AND run analysis:
  ```bash
  python3 "$SKILL_DIR/scripts/dr_analyze.py" \
    --config ~/.config/dailyreport/config.json \
    --from <monday> --to <sunday+1> --diff
  ```
  Use diff data to supplement/verify daily summaries.
- **No dailies**: Run full analysis (with or without `--diff` based on flag).

After collecting either summarized JSON-compatible data or direct analysis JSON, render weekly Markdown with:
```bash
python3 "$SKILL_DIR/scripts/dr_render.py" \
  --type weekly \
  --input <analysis.json> \
  --output "<vault>/DailyReport/weekly/<YYYY>-W<WW>.md" \
  --date <week-monday> \
  --week <YYYY-Www> \
  --level <brief|standard|detailed> \
  --source <daily-summary|daily-summary+diff|diff-analysis> \
  --reporter "<defaults.reporter_name or author>"
```

Weekly Markdown must follow `templates/weekly.md`:
`{汇报人}汇报周期` → `一、本周总结` → `二、本周任务完成情况`（表格罗列事项与状态）→ `三、下周工作计划`。

When also writing HTML, copy `templates/weekly.html` and replace placeholders only. The `<style>` block is locked (`WEEKLY_HTML_STYLE_LOCKED`). Do not invent a new layout, header card, dark theme, or status chips.

### /daily-report:dr_monthly data collection

**Token-efficient strategy**: Monthly reports summarize weekly reports, which summarize dailies.

**Decision tree**:
- Check for weekly reports covering this month in `<vault>/DailyReport/weekly/`
- Check for daily reports in `<vault>/DailyReport/daily/`
- **Has weeklies** (default): Read weekly reports. Supplement gaps with dailies if needed.
- **Has dailies only**: Read all month's dailies and summarize.
- **No reports**: Run analysis. With `--diff`, use `--stat-only` flag (month-scale diff content is too large):
  ```bash
  python3 "$SKILL_DIR/scripts/dr_analyze.py" \
    --config ~/.config/dailyreport/config.json \
    --from <month-1st> --to <next-month-1st> --diff --stat-only
  ```

After collecting either summarized JSON-compatible data or direct analysis JSON, render monthly Markdown with:
```bash
python3 "$SKILL_DIR/scripts/dr_render.py" \
  --type monthly \
  --input <analysis.json> \
  --output "<vault>/DailyReport/monthly/<YYYY-MM>.md" \
  --date <month-first-day> \
  --month <YYYY-MM> \
  --level <brief|standard|detailed> \
  --source <weekly-summary|daily-summary|diff-analysis>
```

## Weekly Report Quality Rules

Weekly reports are human-facing progress reports, not Git activity dumps. Follow these rules strictly:

### 周报基础规范

1. **汇报周期**：标题必须明确本周起止日期。格式：`{汇报人}汇报周期: YYYY年M月D日 — YYYY年M月D日`（示例：`张三汇报周期: 2026年7月27日 — 2026年7月31日`）。
2. **三大固定板块**：正文固定包含且仅按此顺序：`一、本周总结` → `二、本周任务完成情况` → `三、下周工作计划`。
3. **任务进展用表格**：在「本周任务完成情况」中尽量用表格清晰罗列「事项 / 完成状态」（默认两列）；单个任务功能条目不超过 4 条（可合并相近子项）；未完成项须额外备注阻碍原因与预计完成时间（写入状态文案，或仅在有未完成项时才加「备注」列）。
4. **状态色标**（Obsidian/Markdown 可用 `<font color="...">`）：
   - **蓝色** = 进行中：`<font color="blue">进行中</font>`
   - **已完成**：`✅ 已完成`（带 ✅，文字不用绿色）
   - **红色** = 异常或存在风险：`<font color="red">存在风险</font>`

### 内容与质量约束

5. **Task/function first**: The weekly report body must describe completed tasks, features, fixes, verification, and follow-up plans.
6. **Organize as `任务一/二/三：主题`**: Use Markdown status tables under each theme. Large tasks may use numbered subsections (`1. 2. 3.`) each with its own table.
7. **Do not use repository activity as prose**: Do not write sections whose main point is that a repository changed or did not change.
8. **No Git metadata in body prose**: Do not include commit hashes, file counts, insertion/deletion counts, or "repository active/inactive" language in weekly report body sections. Git metadata may stay in JSON/frontmatter/debug output only.
9. **Analyze new repositories**: Newly detected repositories must participate in the target-period analysis before rendering. Keep them in `new_repos_detected` as metadata, but do not omit their commits from the weekly summary.
10. **Do not invent requirement names**: The `任务N` title is a requirement/theme name only. If it cannot be confidently inferred, leave the title empty and list concrete items in the status table. Do not promote low-level chore names to requirement titles.
11. **Aggregate related commits**: Multiple commits for the same feature/fix must be grouped into a small number of work themes. Do not list commit-by-commit unless `--level=detailed` explicitly asks for it.
12. **Write like a weekly report**: Summary and task rows should explain what capability or task moved forward, not how many files changed.
13. **Preserve product surfaces**: If commits or diff paths indicate a user-facing page/screen/management surface, keep it as an independent task instead of merging it into generic buckets like UI optimization or business flow. Example: interview management page work (`InterviewManageActivity`, `iminterview_activity_interview_manage.xml`, `面试列表`, `快速面试入口`, `订单/客资`, `简历操作栏`) should group as `面试管理页面建设与优化`.
14. **Diff-first task inference**: Commit messages are hints only. Weekly task grouping must inspect changed file paths and code/layout/model/API names when `diff_content` is available. Product-surface paths override generic commit scopes such as `ui`, `layout`, or `interview`.
15. **Use canonical host App names**: Render `zhb-AppShell` as `挚护办`; render `zhy-AppShell` and `zhy-ModuleMain` as `挚护易`. Never refer to a `zhy` host as `挚护医`.
16. **Reporter name**: Prefer `--reporter` / `defaults.reporter_name`; otherwise fall back to the first author name.

Bad weekly body examples:
- `涉及仓库：ModuleImInterview；提交 45 次；代码变更 +1200/-300 行。`
- `本次任务对应提交 abc1234，涉及 1 个文件变更。`
- `本周期另有 87 个仓库暂无匹配提交记录。`

Good weekly body example:
- `本周重点围绕支付对接自测、推包回归和合同管理缺陷修复推进。`
- `**任务一：合伙人需求·支付对接·自测·提测**` followed by a status table with green/blue/red colored status cells and remarks for unfinished items.

### Weekly Report Diff-to-Requirement Workflow

For weekly reports, use a two-phase compounding workflow:

1. **Write many facts from diff first**
   - Inspect changed file paths, layouts, Activities/Fragments, ViewModels, repositories, APIs, request/response models, adapters, popups/dialogs, resources, and custom views.
   - Extract concrete facts generously: pages touched, capabilities added, flows changed, UI components created, interfaces/models added, verification/fix areas.
   - Treat commit messages as hints only. Diff paths and code semantics override generic commit scopes like `ui`, `layout`, or `interview`.

2. **Then merge into fewer weekly items**
   - Merge facts into product/business requirements, pages, or capabilities.
   - Preserve independent product surfaces as independent items, such as `面试管理页面建设与优化`.
   - Demote low-value technical chores (`格式化`, `资源引用`, `图片资源`, vague `代码提交`) into `其他/支撑性调整`.
   - Large business blocks must include concrete sub-tasks; do not summarize a large capability in one vague sentence.

Pipeline:
```text
Git diff -> fact extraction -> detailed task list -> requirement/theme merge -> concise weekly report
```

## Three Detail Levels

### brief
- Per-repo: commit count + one-line summary
- No diff details, no branch operations
- Overall: one summary sentence

### standard (daily default)
- Per-repo: commit list + key file changes with descriptions
- Important diff highlights
- Branch operations if any
- Overall: summary paragraph

### detailed
- Per-repo: per-commit analysis with code references
- Full diff coverage for significant changes
- Complete branch operation timeline
- Overall: detailed analysis + next steps

## Report Templates

Reports use Obsidian-compatible Markdown with YAML frontmatter and tags. The standalone files in `templates/` are the output source of truth:
- `templates/daily.md`
- `templates/weekly.md`
- `templates/weekly.html` (locked HTML style; copy `<style>` verbatim)
- `templates/monthly.md`

`references/TEMPLATES.md` documents the rendered structure and frontmatter semantics.

Output paths:
- Daily: `<vault>/<base_folder>/daily/<YYYY-MM-DD>.md`
- Weekly: `<vault>/<base_folder>/weekly/<YYYY>-W<WW>.md`
- Monthly: `<vault>/<base_folder>/monthly/<YYYY>-<MM>.md`

See [TEMPLATES.md](references/TEMPLATES.md) for complete template structures.

Key frontmatter fields: `title`, `date`, `type`, `level`, `tags`, `repos`, `generated`,
`repos_scanned`, `repos_active`, `commits_total`, `authors`.
Reports with grouped activity should also include `groups`.
Weekly/monthly also include: `source` (data source indicator), `date_range`.

Use `> [!summary]` callout for the overview section (Obsidian native support).

## Script Reference

### dr_scan.py

```bash
# Full scan
python3 "$SKILL_DIR/scripts/dr_scan.py" --workspace /path/to/root

# Detect new repos only
python3 "$SKILL_DIR/scripts/dr_scan.py" --workspace /path/to/root \
  --config ~/.config/dailyreport/config.json --detect-new
```

Output: JSON array of `{path, name, git_user: {name, email}, git_user_source}`.

### dr_render.py

```bash
# Render daily Markdown from analysis JSON
python3 "$SKILL_DIR/scripts/dr_render.py" \
  --type daily \
  --input /tmp/daily-analysis.json \
  --output /path/to/vault/DailyReport/daily/2026-04-07.md \
  --date 2026-04-07 --level standard

# Render weekly Markdown with source metadata
python3 "$SKILL_DIR/scripts/dr_render.py" \
  --type weekly \
  --input /tmp/weekly-analysis.json \
  --output /path/to/vault/DailyReport/weekly/2026-W15.md \
  --date 2026-04-06 --week 2026-W15 --source daily-summary
```

Output: Obsidian-compatible Markdown written to `--output`, or stdout when `--output` is omitted.

### dr_analyze.py

```bash
# Daily analysis (with diff)
python3 "$SKILL_DIR/scripts/dr_analyze.py" \
  --config ~/.config/dailyreport/config.json \
  --from 2026-04-07 --to 2026-04-08 --diff

# Weekly analysis (specific repos)
python3 "$SKILL_DIR/scripts/dr_analyze.py" \
  --config ~/.config/dailyreport/config.json \
  --from 2026-03-31 --to 2026-04-07 --diff --repos my-app,backend

# Monthly stat-only
python3 "$SKILL_DIR/scripts/dr_analyze.py" \
  --config ~/.config/dailyreport/config.json \
  --from 2026-04-01 --to 2026-05-01 --diff --stat-only
```

Output: JSON with `date_range`, `active_repos[]`, `skipped_repos[]`, `new_repos_detected[]`.

Each active repo contains: `name`, `path`, `git_user`, `commits[]`, `diff_stats`, `diff_content`, `branch_activity`.

## Important Notes

1. **Git safety**: All operations are READ-ONLY. Never modify any Git repository.
2. **Token control**: Daily reports are the foundation. Weekly/monthly should prefer reading existing reports over running new analysis. The `--diff` flag is opt-in for weekly/monthly.
3. **User binding**: Each repo has its own bound git user. The `--author` filter uses the bound email for each repo independently.
4. **Error handling**: If a script fails (non-zero exit), report the error to user and suggest checking the config. If config is missing, always suggest `/daily-report:dr_init` or the equivalent natural-language request.
5. **Language**: Generate report content in the language specified by `defaults.language` in config (default: `zh-CN`, Chinese).
6. **New repo detection**: When analysis detects new repos in workspace, append a note at the end of the report suggesting the user run `/daily-report:dr_init` to register them.
7. **Inactive repo presentation**: In daily reports under `standard` and `detailed`, split inactive repos into:
   - recently active in the last 7 days: show repo name + last commit date
   - silent for 90+ days: list separately to surface possibly abandoned repos
   - everything else: show count only, do not expand
