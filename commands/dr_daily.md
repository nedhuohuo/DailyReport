---
description: "Generate a daily report from Git activity across configured repositories"
allowed-tools: Bash, Read, Write, Glob
---

Load and use the `daily-report` skill to generate a daily report.

This command should be exposed by plugin-based tools as `/daily-report:dr_daily`.

This command will:
1. Load config from `~/.config/dailyreport/config.json`.
2. Determine the target date, defaulting to today.
3. Collect Git activity with diff analysis.
4. Generate Obsidian-compatible Markdown output.
5. Save the report to `<vault>/DailyReport/daily/<YYYY-MM-DD>.md`.

Optional parameters:
- `--level=brief|standard|detailed`
- `--date=YYYY-MM-DD`
