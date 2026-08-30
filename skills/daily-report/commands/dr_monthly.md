---
description: "Generate monthly report summarizing Git activity for the current month"
---

Load and use the daily-report skill to generate a monthly report.

Canonical plugin command: `/daily-report:dr_monthly`

This command will:
1. Load config from ~/.config/dailyreport/config.json
2. Determine current month range
3. Check for existing weekly and daily reports (token-efficient strategy)
4. Generate summary from existing reports or run stat-only analysis, then render with `templates/monthly.md` via `dr_render.py`
5. Save to <vault>/DailyReport/monthly/<YYYY>-<MM>.md

Optional parameters:
- `--level=brief|standard|detailed` - Detail level (default: brief)
- `--diff` - Include diff analysis with --stat-only (default: false)
