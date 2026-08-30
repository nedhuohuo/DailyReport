import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "daily-report" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import dr_render


SAMPLE_ANALYSIS = {
    "date_range": {"from": "2026-04-23", "to": "2026-04-24"},
    "active_repos": [
        {
            "name": "app-api",
            "path": "/workspace/app-api",
            "git_user": {"name": "Ned", "email": "ned@example.com"},
            "commits": [
                {
                    "hash": "abcdef1234567890",
                    "short_hash": "abcdef1",
                    "subject": "feat: add report templates",
                    "author_name": "Ned",
                    "author_email": "ned@example.com",
                    "date": "2026-04-23 10:20:30",
                },
                {
                    "hash": "1234567890abcdef",
                    "subject": "fix: render weekly totals",
                    "author_name": "Ned",
                    "author_email": "ned@example.com",
                    "date": "2026-04-23 11:20:30",
                },
                {
                    "hash": "bbbbbbbb90abcdef",
                    "subject": "fix: render weekly empty state",
                    "author_name": "Ned",
                    "author_email": "ned@example.com",
                    "date": "2026-04-23 11:30:30",
                },
            ],
            "diff_stats": {
                "files_changed": 3,
                "insertions": 42,
                "deletions": 7,
                "files": [
                    {"path": "skills/daily-report/templates/daily.md", "insertions": 20, "deletions": 0},
                    {"path": "skills/daily-report/scripts/dr_render.py", "insertions": 22, "deletions": 7},
                ],
            },
            "branch_activity": {
                "current_branch": "feature/templates",
                "operations": ["checkout: feature/templates"],
            },
        }
    ],
    "skipped_repos": [{"name": "quiet-repo", "reason": "no_recent_commits"}],
    "new_repos_detected": [{"name": "new-tool", "path": "/workspace/new-tool"}],
}


class ReportTemplateRenderingTests(unittest.TestCase):
    def test_daily_report_uses_template_frontmatter_and_repo_sections(self):
        markdown = dr_render.render_report(
            "daily",
            SAMPLE_ANALYSIS,
            {
                "date": "2026-04-23",
                "level": "standard",
                "generated": "2026-04-23T12:00:00",
            },
        )

        self.assertIn('title: "日报 2026-04-23"', markdown)
        self.assertIn("type: daily-report", markdown)
        self.assertIn("repos_active: 1", markdown)
        self.assertIn("commits_total: 3", markdown)
        self.assertIn("# 今日工作进展日报", markdown)
        self.assertIn("汇报日期： 2026年4月23日", markdown)
        self.assertIn("一、 app-api", markdown)
        self.assertIn("当前状态： 已完成", markdown)
        self.assertIn("feat: add report templates", markdown)
        self.assertIn("## 新发现仓库", markdown)
        self.assertIn("new-tool", markdown)

    def test_weekly_report_renders_summary_table_and_source(self):
        markdown = dr_render.render_report(
            "weekly",
            SAMPLE_ANALYSIS,
            {
                "date": "2026-04-23",
                "week": "2026-W17",
                "level": "brief",
                "source": "daily-summary",
                "reporter": "谢鹏",
                "generated": "2026-04-23T12:00:00",
            },
        )

        self.assertIn('title: "周报 2026-W17"', markdown)
        self.assertIn("type: weekly-report", markdown)
        self.assertIn("source: daily-summary", markdown)
        self.assertIn("# 谢鹏汇报周期: 2026年4月23日 — 2026年4月23日", markdown)
        self.assertIn("## 一、本周总结", markdown)
        self.assertIn("## 二、本周任务完成情况", markdown)
        self.assertIn("## 三、下周工作计划", markdown)
        self.assertIn("**任务一：", markdown)
        self.assertIn("| 事项 | 状态 |", markdown)
        self.assertNotIn("| 事项 | 状态 | 备注 |", markdown)
        self.assertIn('✅ 已完成', markdown)
        self.assertIn("add report templates", markdown)
        self.assertIn("render weekly totals", markdown)
        self.assertIn("1. 跟进", markdown)
        self.assertNotIn("核心工作进展：", markdown)
        self.assertNotIn("具体完成任务：", markdown)
        self.assertNotIn("涉及仓库：", markdown)
        self.assertNotIn("本次任务对应提交", markdown)
        self.assertNotIn("代码变更", markdown)
        self.assertNotIn("仓库暂无匹配提交", markdown)

    def test_monthly_report_renders_metrics_and_month_sections(self):
        markdown = dr_render.render_report(
            "monthly",
            SAMPLE_ANALYSIS,
            {
                "date": "2026-04-23",
                "month": "2026-04",
                "level": "brief",
                "source": "weekly-summary",
                "generated": "2026-04-23T12:00:00",
            },
        )

        self.assertIn('title: "月报 2026-04"', markdown)
        self.assertIn("type: monthly-report", markdown)
        self.assertIn("month: 2026-04", markdown)
        self.assertIn("# 月度工作总结月报", markdown)
        self.assertIn("汇报月份： 2026年4月", markdown)
        self.assertIn("月度核心成果：", markdown)
        self.assertIn("一、 app-api", markdown)
        self.assertIn("下月计划", markdown)

    def test_weekly_large_business_items_expand_and_chores_demote(self):
        analysis = {
            "date_range": {"from": "2026-04-20", "to": "2026-04-27"},
            "active_repos": [
                {
                    "name": "interview",
                    "git_user": {"name": "Ned", "email": "ned@example.com"},
                    "commits": [
                        {"hash": "a1", "message": "feat(interviewmeeting): 新增美颜按钮及角色操作切换功能", "author_name": "Ned", "date": "2026-04-21 10:00:00"},
                        {"hash": "a2", "message": "fix(interviewmeeting): 修正麦克风和摄像头图标状态显示", "author_name": "Ned", "date": "2026-04-21 11:00:00"},
                        {"hash": "a3", "message": "refactor(contact): 代码格式化", "author_name": "Ned", "date": "2026-04-21 12:00:00"},
                    ],
                    "diff_stats": {"files_changed": 3, "insertions": 30, "deletions": 5},
                    "diff_content": "",
                }
            ],
            "skipped_repos": [],
            "new_repos_detected": [],
        }

        markdown = dr_render.render_report("weekly", analysis, {"date": "2026-04-20", "week": "2026-W17"})

        self.assertIn("面试会议房间能力完善", markdown)
        self.assertIn("新增美颜按钮及角色操作切换功能", markdown)
        self.assertIn("修正麦克风和摄像头图标状态显示", markdown)
        self.assertIn('✅ 已完成', markdown)
        self.assertIn("其他/支撑性调整", markdown)
        self.assertIn("代码格式化", markdown)
        self.assertNotIn("**任务一：代码格式化**", markdown)
        self.assertNotIn("**任务二：代码格式化**", markdown)

    def test_weekly_uses_diff_paths_to_preserve_product_pages(self):
        analysis = {
            "date_range": {"from": "2026-04-20", "to": "2026-04-27"},
            "active_repos": [
                {
                    "name": "interview",
                    "git_user": {"name": "Ned", "email": "ned@example.com"},
                    "commits": [
                        {"hash": "aaa1111", "message": "style(layout): 优化页面", "author_name": "Ned", "date": "2026-04-21 10:00:00"}
                    ],
                    "diff_stats": {"files_changed": 4, "insertions": 100, "deletions": 10},
                    "diff_content": "\n".join([
                        "diff --git a/ImInterview/src/main/res/layout/iminterview_activity_interview_manage.xml b/ImInterview/src/main/res/layout/iminterview_activity_interview_manage.xml",
                        "+++ b/ImInterview/src/main/res/layout/iminterview_item_interview_manage.xml",
                        "+++ b/ImInterview/src/main/java/com/yilife/android/bu/module/interviewmeeting/ui/activity/InterviewManageActivity.kt",
                        "+++ b/ImInterview/src/main/java/com/yilife/android/bu/module/interviewmeeting/ui/view/OrderContentView.kt",
                    ]),
                }
            ],
            "skipped_repos": [],
            "new_repos_detected": [],
        }

        markdown = dr_render.render_report("weekly", analysis, {"date": "2026-04-20", "week": "2026-W17"})

        body = markdown.split("---", 2)[-1]
        self.assertIn("面试管理页面建设与优化", body)
        self.assertIn("面试管理页面布局", body)
        self.assertIn("订单/客资内容展示", body)
        self.assertIn("| 模块 | 状态 |", body)
        self.assertNotIn("| 模块 | 状态 | 备注 |", body)
        self.assertNotIn("**任务一：优化页面**", body)

    def test_weekly_downgrades_resource_reference_and_expands_grouped_work(self):
        analysis = {
            "date_range": {"from": "2026-04-20", "to": "2026-04-27"},
            "active_repos": [
                {
                    "name": "app-shell",
                    "git_user": {"name": "Ned", "email": "ned@example.com"},
                    "commits": [
                        {"hash": "aaa1111", "message": "[feat] 新增tobB资源引用", "author_name": "Ned", "date": "2026-04-21 10:00:00"}
                    ],
                    "diff_stats": {"files_changed": 1, "insertions": 2, "deletions": 0},
                },
                {
                    "name": "interview",
                    "git_user": {"name": "Ned", "email": "ned@example.com"},
                    "commits": [
                        {"hash": "bbb1111", "message": "feat(interviewmeeting): 添加成员管理和服务人员标记功能", "author_name": "Ned", "date": "2026-04-22 10:00:00"},
                        {"hash": "bbb2222", "message": "feat(interviewmeeting): 新增美颜按钮及角色操作切换功能", "author_name": "Ned", "date": "2026-04-22 11:00:00"},
                        {"hash": "bbb3333", "message": "fix(interviewmeeting): 修正麦克风和摄像头图标状态显示", "author_name": "Ned", "date": "2026-04-22 12:00:00"},
                    ],
                    "diff_stats": {"files_changed": 5, "insertions": 40, "deletions": 8},
                },
            ],
            "skipped_repos": [],
            "new_repos_detected": [],
        }

        markdown = dr_render.render_report("weekly", analysis, {"date": "2026-04-20", "week": "2026-W17"})
        body = markdown.split("---", 2)[-1]

        self.assertNotIn("**任务一：新增tobB资源引用**", body)
        self.assertIn("其他/支撑性调整", body)
        self.assertIn("新增tobB资源引用", body)
        self.assertIn("面试会议房间能力完善", body)
        self.assertIn("成员管理和服务人员标记功能", body)
        self.assertIn("新增美颜按钮及角色操作切换功能", body)
        self.assertIn("修正麦克风和摄像头图标状态显示", body)
        self.assertIn('✅ 已完成', body)

    def test_weekly_status_colors_and_incomplete_remarks(self):
        done_table = dr_render.render_status_table(
            [{"item": "微信支付", "status": "done"}]
        )
        self.assertIn("| 事项 | 状态 |", done_table)
        self.assertNotIn("备注", done_table)
        self.assertIn('✅ 已完成', done_table)

        rows = [
            {"item": "微信支付", "status": "done"},
            {"item": "支付宝", "status": "in_progress", "remark": "等待联调；预计下周三"},
            {"item": "合同列表", "status": "at_risk"},
        ]
        table = dr_render.render_status_table(rows)
        self.assertIn("| 事项 | 状态 | 备注 |", table)
        self.assertIn('✅ 已完成', table)
        self.assertIn('<font color="blue">进行中</font>', table)
        self.assertIn('<font color="red">存在风险</font>', table)
        self.assertIn("等待联调；预计下周三", table)
        self.assertIn("待补充阻碍原因与预计完成时间", table)

    def test_weekly_body_does_not_leak_git_activity_dump(self):
        markdown = dr_render.render_report(
            "weekly",
            SAMPLE_ANALYSIS,
            {
                "date": "2026-04-23",
                "week": "2026-W17",
                "level": "brief",
                "source": "git-analysis",
                "generated": "2026-04-23T12:00:00",
            },
        )
        body = markdown.split("---", 2)[-1]

        forbidden_phrases = [
            "涉及仓库：",
            "本次任务对应提交",
            "相关提交",
            "代码变更 +",
            "文件变更",
            "仓库暂无匹配提交",
            "repos_active",
            "commits_total",
        ]
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, body)

    def test_weekly_uses_canonical_host_app_name_for_zhy(self):
        analysis = {
            "date_range": {"from": "2026-07-27", "to": "2026-08-03"},
            "active_repos": [
                {
                    "name": "zhy-AppShell",
                    "git_user": {"name": "Ned", "email": "ned@example.com"},
                    "commits": [
                        {
                            "hash": "abc1234",
                            "message": "chore(deps): 同步挚护医宿主版本",
                            "author_name": "Ned",
                            "date": "2026-07-29 10:00:00",
                        }
                    ],
                    "diff_stats": {"files_changed": 1, "insertions": 1, "deletions": 1},
                    "diff_content": "",
                }
            ],
            "skipped_repos": [],
            "new_repos_detected": [],
        }

        markdown = dr_render.render_report(
            "weekly",
            analysis,
            {"date": "2026-07-27", "week": "2026-W31"},
        )

        self.assertEqual(dr_render.host_app_display_name("zhb-AppShell"), "挚护办")
        self.assertEqual(dr_render.host_app_display_name("zhy-AppShell"), "挚护易")
        self.assertEqual(dr_render.host_app_display_name("zhy-ModuleMain"), "挚护易")
        self.assertIn("  - zhy-AppShell", markdown)
        self.assertIn("同步挚护易宿主版本", markdown)
        self.assertNotIn("挚护医", markdown)

    def test_cli_writes_rendered_markdown_to_output_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "analysis.json"
            output_path = Path(temp_dir) / "daily.md"
            input_path.write_text(json.dumps(SAMPLE_ANALYSIS), encoding="utf-8")

            exit_code = dr_render.main(
                [
                    "--type",
                    "daily",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--date",
                    "2026-04-23",
                    "--generated",
                    "2026-04-23T12:00:00",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            self.assertIn("# 今日工作进展日报", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
