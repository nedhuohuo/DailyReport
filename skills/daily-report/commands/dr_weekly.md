---
description: "Generate weekly report summarizing Git activity for the current week"
---

Load and use the daily-report skill to generate a weekly report.

Canonical plugin command: `/daily-report:dr_weekly`

This command will:
1. Load config from ~/.config/dailyreport/config.json
2. Determine current ISO week range (Mon-Sun)
3. Check for existing daily reports (token-efficient strategy)
4. Generate summary from dailies or run full analysis, then render with `templates/weekly.md` via `dr_render.py`
5. Save to <vault>/DailyReport/weekly/<YYYY>-W<WW>.md
6. If HTML is requested, copy `templates/weekly.html` and replace placeholders only. Do not change the locked `<style>` block.

Host App names are fixed: `zhb-AppShell` is `挚护办`; `zhy-AppShell` and `zhy-ModuleMain` are `挚护易`. Never call a `zhy` host `挚护医`.

Weekly body format (基础规范):
1. `{reporter}汇报周期: YYYY年M月D日 — YYYY年M月D日`（明确本周起止日期）
2. `一、本周总结`
3. `二、本周任务完成情况`：表格罗列事项与完成状态；蓝色=进行中，绿色=已完成，红色=异常/风险；未完成须备注阻碍原因与预计完成时间
4. `三、下周工作计划`

Optional parameters:
- `--level=brief|standard|detailed` - Detail level (default: brief)
- `--diff` - Include diff analysis (default: false, uses daily summaries)
- `--reporter=` - Reporter name used in the weekly title
