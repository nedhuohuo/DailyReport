---
description: "Generate a weekly report summarizing Git activity for the current ISO week"
allowed-tools: Bash, Read, Write, Glob
---

Load and use the `daily-report` skill to generate a weekly report.

This command should be exposed by plugin-based tools as `/daily-report:dr_weekly`.

This command will:
1. Load config from `~/.config/dailyreport/config.json`.
2. Determine the current ISO week range.
3. Prefer existing daily reports when available.
4. Fall back to Git analysis when summaries are missing or `--diff` is requested.
5. Save the report to `<vault>/DailyReport/weekly/<YYYY>-W<WW>.md`.

Optional parameters:
- `--level=brief|standard|detailed`
- `--diff`
