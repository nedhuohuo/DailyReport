# Report Template Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add standalone report templates and a Python renderer for daily, weekly, and monthly Markdown output.

**Architecture:** Template files live beside the skill and contain named placeholders. `dr_render.py` loads a template, derives deterministic metrics from analysis JSON, renders frontmatter and body sections, and writes Markdown to stdout or a file.

**Tech Stack:** Python 3.11 standard library, `unittest`, Markdown templates.

---

### Task 1: Renderer Tests

**Files:**
- Create: `tests/test_dr_render.py`

- [ ] Write tests that import `dr_render`, render sample daily/weekly/monthly analysis data, and assert required frontmatter and sections exist.
- [ ] Run `python3 -m unittest tests/test_dr_render.py` and confirm it fails because `dr_render.py` is missing.

### Task 2: Renderer Implementation

**Files:**
- Create: `skills/daily-report/scripts/dr_render.py`

- [ ] Implement template loading, metric aggregation, YAML-safe frontmatter formatting, body section rendering, and CLI arguments.
- [ ] Run `python3 -m unittest tests/test_dr_render.py` and confirm tests pass.

### Task 3: Template Files

**Files:**
- Create: `skills/daily-report/templates/daily.md`
- Create: `skills/daily-report/templates/weekly.md`
- Create: `skills/daily-report/templates/monthly.md`

- [ ] Add templates with placeholders for frontmatter, headings, summaries, tables, repo sections, and footer.
- [ ] Ensure renderer can load all templates by report type.

### Task 4: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `skills/daily-report/SKILL.md`
- Modify: `skills/daily-report/references/COMMANDS.md`
- Modify: `skills/daily-report/references/TEMPLATES.md`

- [ ] Document `dr_render.py` usage and state that `templates/*.md` are the output source of truth.
- [ ] Run targeted tests and `python3 -m py_compile skills/daily-report/scripts/*.py`.
