---
description: "Generate daily report from Git activity across configured repositories"
---

Load and use the daily-report skill to generate a daily report.

This command will:
1. Load config from ~/.config/dailyreport/config.json
2. Determine date range (default: today)
3. Collect Git activity data with diff analysis
4. Generate Obsidian-compatible Markdown report
5. Save to <vault>/DailyReport/daily/<YYYY-MM-DD>.md

Optional parameters:
- `--level=brief|standard|detailed` - Detail level (default: standard)
- `--date=YYYY-MM-DD` - Specific date (default: today)
