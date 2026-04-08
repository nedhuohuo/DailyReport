---
description: "Generate a monthly report summarizing Git activity for the current month"
allowed-tools: Bash, Read, Write, Glob
---

Load and use the `daily-report` skill to generate a monthly report.

This command should be exposed by plugin-based tools as `/daily-report:dr_monthly`.

This command will:
1. Load config from `~/.config/dailyreport/config.json`.
2. Determine the current month range.
3. Prefer existing weekly and daily reports when available.
4. Fall back to stat-oriented Git analysis when summaries are missing.
5. Save the report to `<vault>/DailyReport/monthly/<YYYY>-<MM>.md`.

Optional parameters:
- `--level=brief|standard|detailed`
- `--diff`
