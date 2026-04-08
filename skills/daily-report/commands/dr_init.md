---
description: "Initialize DailyReport configuration - scan workspace, register repos, and set up output directories"
---

Load and use the daily-report skill to initialize the configuration.

Canonical plugin command: `/daily-report:dr_init`

This command will:
1. Ask for workspace root directory (where Git repos live)
2. Ask for Obsidian vault directory (where reports will be saved)
3. Scan workspace to discover Git repositories
4. Display discovered repos for user confirmation
5. Save configuration to ~/.config/dailyreport/config.json
6. Create output directories (daily, weekly, monthly)

If config already exists, it will run in "detect new repos" mode to add newly discovered repositories.
