---
description: "Show DailyReport configuration status and registered repositories"
allowed-tools: Bash, Read, Write, Glob
---

Load and use the `daily-report` skill to display configuration status.

This command should be exposed by plugin-based tools as `/daily-report:dr_status`.

This command will:
1. Load config from `~/.config/dailyreport/config.json`.
2. Display the workspace root directory.
3. Display the Obsidian vault output directory.
4. List registered repositories and their bound Git identities.
5. Show default reporting settings and report configuration issues.
