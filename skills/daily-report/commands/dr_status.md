---
description: "Show DailyReport configuration status and registered repositories"
---

Load and use the daily-report skill to display configuration status.

Canonical plugin command: `/daily-report:dr_status`

This command will:
1. Load config from ~/.config/dailyreport/config.json
2. Display workspace root directory
3. Display output directory (Obsidian vault location)
4. List all registered repositories with their Git user bindings
5. Show default settings (detail level, language)
6. Report any configuration issues

Use this to verify your setup is correct before generating reports.
