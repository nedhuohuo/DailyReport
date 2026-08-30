# Report Template Rendering Design

## Goal
Add maintainable daily, weekly, and monthly report templates and a lightweight Python renderer that outputs Markdown using those templates.

## Design
- Add standalone Markdown template files under `skills/daily-report/templates/` for daily, weekly, and monthly reports.
- Add `skills/daily-report/scripts/dr_render.py` to convert `dr_analyze.py` JSON plus metadata into Markdown.
- Keep AI-generated prose optional by exposing placeholders/sections in templates while script-rendering deterministic fields, frontmatter, stats, repo summaries, commits, branch activity, and detected new repos.
- Update `SKILL.md`, command docs, and template reference docs so report generation uses template files as the source of truth.

## Scope
- Implement deterministic template rendering for analysis JSON.
- Support daily, weekly, monthly report types with level/source/date metadata.
- Add unit tests for template loading, frontmatter, report sections, and CLI output.
- Do not call external AI APIs or mutate Git repositories.
