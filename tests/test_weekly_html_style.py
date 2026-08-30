import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "skills" / "daily-report" / "templates" / "weekly.html"
CURRENT_WEEK = REPO_ROOT / "weekly" / "2026-W35.html"

LOCKED_STYLE_MARKERS = [
    "WEEKLY_HTML_STYLE_LOCKED",
    ":root{--text:#1f2328;--muted:#57606a;--border:#d0d7de;--bg:#fff;--head-bg:#f6f8fa}",
    '.page{max-width:860px;margin:0 auto;background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:40px 44px}',
    ".task-title{margin:22px 0 10px;font-weight:600}",
    ".sub-title{margin:16px 0 8px;font-weight:600}",
    "td.status{white-space:nowrap;width:8.5em}",
    ".footer{margin-top:36px;padding-top:14px;border-top:1px solid var(--border);color:var(--muted);font-size:.85rem}",
]

FORBIDDEN_STYLE_MARKERS = [
    ".report-header",
    ".plan-list",
    "prefers-color-scheme",
    "--page-bg",
    ".task-number",
]


def extract_style(html: str) -> str:
    match = re.search(r"<style>(.*?)</style>", html, flags=re.S)
    if not match:
        raise AssertionError("missing <style> block")
    return match.group(1)


class WeeklyHtmlStyleLockTests(unittest.TestCase):
    def test_template_keeps_locked_w32_style(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        style = extract_style(html)
        for marker in LOCKED_STYLE_MARKERS:
            self.assertIn(marker, html)
        for marker in FORBIDDEN_STYLE_MARKERS:
            self.assertNotIn(marker, style)
        self.assertIn('class="page"', html)
        self.assertIn("{weekly_header}", html)
        self.assertIn("{weekly_summary_html}", html)
        self.assertIn("{weekly_task_sections_html}", html)

    def test_current_week_html_uses_locked_style(self):
        if not CURRENT_WEEK.exists():
            self.skipTest("local weekly HTML is not published with the skill")
        html = CURRENT_WEEK.read_text(encoding="utf-8")
        style = extract_style(html)
        template_style = extract_style(TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(style, template_style)
        for marker in FORBIDDEN_STYLE_MARKERS:
            self.assertNotIn(marker, html)
        self.assertIn('class="page"', html)
        self.assertIn("nedhuo汇报周期: 2026年8月24日 — 2026年8月30日", html)
        self.assertIn("✅ 已完成", html)
        self.assertNotIn("本周工作周报", html)
