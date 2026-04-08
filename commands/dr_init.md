---
description: "Initialize DailyReport configuration - scan workspace, register repos, and set up output directories"
allowed-tools: Bash, Read, Write, Glob
---

Load and use the `daily-report` skill to initialize the configuration.

This command should be exposed by plugin-based tools as `/daily-report:dr_init`.

This command will:
1. Ask for the workspace root directory where Git repositories live.
2. Ask for the Obsidian vault directory where reports will be written.
3. Scan the workspace to discover Git repositories.
4. Display discovered repositories for confirmation.
5. Save configuration to `~/.config/dailyreport/config.json`.
6. Create the `daily`, `weekly`, and `monthly` output directories.

If configuration already exists, run in detect-new mode and append only newly discovered repositories.
