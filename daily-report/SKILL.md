---
name: daily-report
description: >-
  Use when the user asks to generate daily reports, weekly reports, or monthly reports
  from Git activity, or mentions "/dr_init", "/dr_daily", "/dr_weekly", "/dr_monthly",
  "/dr_status", or wants to set up automated development report generation across
  multiple repositories.
allowed-tools: Bash, Read, Write, Glob
---

# DailyReport

Low-effort daily/weekly/monthly report generator for developers. Analyzes Git activity across multiple repositories and produces Obsidian-compatible Markdown reports using AI summarization.

## Prerequisites

- Python 3.11+
- Git
- Config file: `~/.config/dailyreport/config.json` (created by `/dr_init`)

Scripts are located at: `<SKILL_DIR>/scripts/` where SKILL_DIR is the directory containing this SKILL.md.

To resolve SKILL_DIR:
```bash
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)" # if running from skill dir
# Or find via symlink:
SKILL_DIR="$(dirname "$(readlink -f ~/.qoder/skills/daily-report/SKILL.md)" 2>/dev/null || dirname "$(readlink ~/.qoder/skills/daily-report/SKILL.md)")"
```

## Configuration

Config path: `~/.config/dailyreport/config.json`

Key fields: `workspace_root`, `output` (vault_dir, folder names), `repositories` (path + bound git_user), `scan_settings`, `defaults` (level, language).

See [CONFIG.md](references/CONFIG.md) for full structure and field docs.

## Command Reference

| Command | Purpose | Default | Params |
|---------|---------|---------|--------|
| `/dr_init` | Interactive setup | Scan workspace, register repos | — |
| `/dr_daily` | Generate daily report | standard + diff | `--level=`, `--date=` |
| `/dr_weekly` | Generate weekly report | brief + daily summary | `--level=`, `--diff` |
| `/dr_monthly` | Generate monthly report | brief + weekly+daily summary | `--level=`, `--diff` |
| `/dr_status` | Show config status | Display all info | — |

See [COMMANDS.md](references/COMMANDS.md) for detailed flows and examples.

## Core Workflow: /dr_init

This is the entry point. MUST be run before any report generation.

### First-time initialization

1. Ask user for **workspace root directory** (where their Git repos live)
2. Ask user for **Obsidian vault directory** (where reports will be saved)
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

### Adding new repos (re-run /dr_init)

When config already exists:
1. Run scan with `--detect-new`:
   ```bash
   python3 "$SKILL_DIR/scripts/dr_scan.py" --workspace "<workspace_root>" --config ~/.config/dailyreport/config.json --detect-new
   ```
2. Show only newly discovered repos
3. Append confirmed repos to existing `repositories` array
4. Do NOT remove existing repos

## Core Workflow: Report Generation

### Shared flow for /dr_daily, /dr_weekly, /dr_monthly

1. **Load config** — Read `~/.config/dailyreport/config.json`. If missing, tell user to run `/dr_init` first.

2. **Determine date range and parameters**:
   - `/dr_daily`: date from `--date` param (default: today). Range = [date, date+1)
   - `/dr_weekly`: current ISO week (Mon-Sun). Range = [monday, sunday+1)
   - `/dr_monthly`: current month. Range = [1st, next-month-1st)

3. **Determine detail level**: from `--level` param, fall back to `defaults.level` in config.

4. **Data collection** (varies by report type — see below)

5. **AI report generation**: Using the collected data and report templates from [TEMPLATES.md](references/TEMPLATES.md), generate the Markdown report content.

6. **Write output file** using Write tool to the appropriate path.

### /dr_daily data collection

Daily reports ALWAYS use diff analysis (this is the foundation of the entire system).

```bash
python3 "$SKILL_DIR/scripts/dr_analyze.py" \
  --config ~/.config/dailyreport/config.json \
  --from <date> --to <date+1> --diff
```

Parse the JSON output. Key fields per active repo: `commits`, `diff_stats`, `diff_content`, `branch_activity`.

If `new_repos_detected` is non-empty, mention it at the end of the report.

### /dr_weekly data collection

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

### /dr_monthly data collection

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

Reports use Obsidian-compatible Markdown with YAML frontmatter and tags.

Output paths:
- Daily: `<vault>/<base_folder>/daily/<YYYY-MM-DD>.md`
- Weekly: `<vault>/<base_folder>/weekly/<YYYY>-W<WW>.md`
- Monthly: `<vault>/<base_folder>/monthly/<YYYY>-<MM>.md`

See [TEMPLATES.md](references/TEMPLATES.md) for complete template structures.

Key frontmatter fields: `title`, `date`, `type`, `level`, `tags`, `repos`, `generated`.
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
4. **Error handling**: If a script fails (non-zero exit), report the error to user and suggest checking the config. If config is missing, always suggest `/dr_init`.
5. **Language**: Generate report content in the language specified by `defaults.language` in config (default: `zh-CN`, Chinese).
6. **New repo detection**: When analysis detects new repos in workspace, append a note at the end of the report suggesting the user run `/dr_init` to register them.
