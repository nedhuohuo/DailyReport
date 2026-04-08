---
description: "Generate weekly report summarizing Git activity for the current week"
---

Load and use the daily-report skill to generate a weekly report.

This command will:
1. Load config from ~/.config/dailyreport/config.json
2. Determine current ISO week range (Mon-Sun)
3. Check for existing daily reports (token-efficient strategy)
4. Generate summary from dailies or run full analysis
5. Save to <vault>/DailyReport/weekly/<YYYY>-W<WW>.md

Optional parameters:
- `--level=brief|standard|detailed` - Detail level (default: brief)
- `--diff` - Include diff analysis (default: false, uses daily summaries)
