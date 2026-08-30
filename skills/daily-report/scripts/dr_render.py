#!/usr/bin/env python3
"""
dr_render.py - DailyReport Markdown template renderer

Renders daily, weekly, and monthly Markdown reports from dr_analyze.py JSON.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPORT_TYPES = {"daily", "weekly", "monthly"}
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "templates"

HOST_APP_DISPLAY_NAMES = {
    "zhb-AppShell": "挚护办",
    "zhy-AppShell": "挚护易",
    "zhy-ModuleMain": "挚护易",
}

HOST_APP_INCORRECT_NAMES = {
    "zhy-AppShell": ("挚护医",),
    "zhy-ModuleMain": ("挚护医",),
}


def host_app_display_name(repo_name):
    return HOST_APP_DISPLAY_NAMES.get(repo_name, repo_name)


def normalize_weekly_host_app_names(markdown, analysis):
    active_repo_names = {
        repo.get("name") for repo in analysis.get("active_repos") or []
    }
    normalized = markdown
    for repo_name in active_repo_names:
        canonical_name = HOST_APP_DISPLAY_NAMES.get(repo_name)
        if not canonical_name:
            continue
        for incorrect_name in HOST_APP_INCORRECT_NAMES.get(repo_name, ()):
            normalized = normalized.replace(incorrect_name, canonical_name)
    return normalized


def load_template(report_type, template_dir=None):
    if report_type not in REPORT_TYPES:
        raise ValueError(f"unsupported report type: {report_type}")
    base_dir = Path(template_dir) if template_dir else TEMPLATE_DIR
    path = base_dir / f"{report_type}.md"
    return path.read_text(encoding="utf-8")


def yaml_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return ""
    text = str(value)
    if not text or any(char in text for char in [":", "#", "\"", "'", "[", "]", "{", "}"]):
        return json.dumps(text, ensure_ascii=False)
    return text


def yaml_list(values, indent=""):
    values = list(dict.fromkeys(value for value in values if value))
    if not values:
        return f"{indent}[]"
    return "\n".join(f"{indent}- {yaml_scalar(value)}" for value in values)


def parse_date(date_text):
    return datetime.strptime(date_text, "%Y-%m-%d")


def safe_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def repo_commits(repo):
    return repo.get("commits") or []


def repo_diff_stats(repo):
    return repo.get("diff_stats") or {}


def repo_files(repo):
    return repo_diff_stats(repo).get("files") or []


def commit_short_hash(commit):
    return commit.get("short_hash") or str(commit.get("hash", ""))[:7] or "unknown"


def collect_metrics(analysis):
    active_repos = analysis.get("active_repos") or []
    skipped_repos = analysis.get("skipped_repos") or []
    commits_total = sum(len(repo_commits(repo)) for repo in active_repos)
    files_changed = sum(safe_int(repo_diff_stats(repo).get("files_changed")) for repo in active_repos)
    insertions = sum(safe_int(repo_diff_stats(repo).get("insertions")) for repo in active_repos)
    deletions = sum(safe_int(repo_diff_stats(repo).get("deletions")) for repo in active_repos)
    authors = []
    dates = set()

    for repo in active_repos:
        user = repo.get("git_user") or {}
        authors.append(user.get("name") or user.get("email"))
        for commit in repo_commits(repo):
            authors.append(commit.get("author_name") or commit.get("author_email"))
            commit_date = str(commit.get("date", ""))[:10]
            if commit_date:
                dates.add(commit_date)

    return {
        "repos_scanned": len(active_repos) + len(skipped_repos),
        "repos_active": len(active_repos),
        "commits_total": commits_total,
        "files_changed": files_changed,
        "insertions": insertions,
        "deletions": deletions,
        "authors": list(dict.fromkeys(author for author in authors if author)),
        "repos": [repo.get("name", "unknown") for repo in active_repos],
        "active_days": len(dates),
    }



def format_cn_date(date_text):
    dt = parse_date(date_text)
    return f"{dt.year}年{dt.month}月{dt.day}日"


def chinese_number(index):
    numbers = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if 1 <= index <= len(numbers):
        return numbers[index - 1]
    return str(index)


def status_for_repo(repo):
    commits = repo_commits(repo)
    if commits:
        return "已完成"
    return "待跟进"


def schedule_for_repo(report_type, repo):
    repo_name = repo.get("name", "该事项")
    if report_type == "daily":
        return f"明日继续跟进 {repo_name} 相关工作"
    if report_type == "monthly":
        return f"下月持续推进 {repo_name} 相关工作"
    return f"下周持续推进 {repo_name} 相关工作"


def detail_for_repo(repo):
    stats = repo_diff_stats(repo)
    files_changed = safe_int(stats.get("files_changed"))
    insertions = safe_int(stats.get("insertions"))
    deletions = safe_int(stats.get("deletions"))
    commit_subjects = [commit.get("subject") or commit.get("message", "无提交说明") for commit in repo_commits(repo)[:3]]
    content = "、".join(commit_subjects) if commit_subjects else "暂无提交明细"
    return (
        f"推进 {repo.get('name', '该仓库')} 相关工作，主要包括{content}。"
        f"本阶段共完成 {len(repo_commits(repo))} 次提交，变更 {files_changed} 个文件，"
        f"代码变更 +{insertions}/-{deletions} 行。"
    )


def render_numbered_work_items(analysis, report_type):
    active_repos = analysis.get("active_repos") or []
    if not active_repos:
        return "暂无活跃工作事项。"
    sections = []
    for index, repo in enumerate(active_repos, start=1):
        sections.append(
            f"{chinese_number(index)}、 {repo.get('name', '未命名事项')}\n\n"
            f"当前状态： {status_for_repo(repo)}\n\n"
            f"时间规划： {schedule_for_repo(report_type, repo)}\n\n"
            f"具体内容： {detail_for_repo(repo)}"
        )
    return "\n\n".join(sections)


def render_next_plan_items(analysis, report_type):
    active_repos = analysis.get("active_repos") or []
    if not active_repos:
        return "- 继续关注各仓库动态，及时补充工作记录。"
    label = {"daily": "明日", "weekly": "下周", "monthly": "下月"}[report_type]
    lines = []
    for repo in active_repos[:5]:
        lines.append(f"- {label}继续跟进 {repo.get('name', '相关项目')} 的后续开发、测试及问题修复工作。")
    return "\n".join(lines)


def render_other_items(analysis):
    skipped_count = len(analysis.get("skipped_repos") or [])
    new_count = len(analysis.get("new_repos_detected") or [])
    lines = []
    if skipped_count:
        lines.append(f"- 本周期另有 {skipped_count} 个仓库暂无匹配提交记录。")
    if new_count:
        lines.append(f"- 本周期检测到 {new_count} 个新仓库，建议确认是否纳入后续日报配置。")
    if not lines:
        lines.append("- 暂无其他补充事项。")
    return "\n".join(lines)

def format_frontmatter(fields):
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.append(yaml_list(value, "  "))
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for child_key, child_value in value.items():
                lines.append(f"  {child_key}: {yaml_scalar(child_value)}")
        else:
            if key == "title":
                lines.append(f"{key}: {json.dumps(str(value), ensure_ascii=False)}")
            else:
                lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def first_commit_subject(repo):
    commits = repo_commits(repo)
    if not commits:
        return "活动记录"
    return commits[0].get("subject") or commits[0].get("message", "活动记录")


def infer_main_focus(analysis):
    active_repos = analysis.get("active_repos") or []
    subjects = [first_commit_subject(repo) for repo in active_repos[:3]]
    if not subjects:
        return "暂无活跃提交"
    return "；".join(subjects)


def render_commit_list(repo):
    commits = repo_commits(repo)
    if not commits:
        return "- 无提交记录"
    lines = []
    for commit in commits:
        subject = commit.get("subject") or commit.get("message", "无提交说明")
        lines.append(f"- `{commit_short_hash(commit)}` {subject}")
    return "\n".join(lines)


def render_file_changes(repo, level):
    if level == "brief":
        return ""
    files = repo_files(repo)
    if not files:
        return "- 无文件级变更统计"
    lines = []
    for file_info in files:
        path = file_info.get("path", "unknown")
        insertions = safe_int(file_info.get("insertions"))
        deletions = safe_int(file_info.get("deletions"))
        lines.append(f"- **{path}** (+{insertions}/-{deletions})")
    return "\n".join(lines)


def render_branch_activity(repo, level):
    if level == "brief":
        return ""
    activity = repo.get("branch_activity") or {}
    operations = activity.get("operations") or []
    if not operations:
        return ""
    return "\n".join(f"- {operation}" for operation in operations)


def render_repo_sections(analysis, level):
    sections = []
    for repo in analysis.get("active_repos") or []:
        stats = repo_diff_stats(repo)
        branch = (repo.get("branch_activity") or {}).get("current_branch", "unknown")
        commits_count = len(repo_commits(repo))
        insertions = safe_int(stats.get("insertions"))
        deletions = safe_int(stats.get("deletions"))
        section = [
            f"### {repo.get('name', 'unknown')}",
            "",
            f"**分支：** `{branch}` | **提交：** {commits_count} 次 | **变更：** +{insertions} / -{deletions} 行",
            "",
            "#### 提交记录",
            render_commit_list(repo),
        ]
        file_changes = render_file_changes(repo, level)
        if file_changes:
            section.extend(["", "#### 关键变更", file_changes])
        branch_activity = render_branch_activity(repo, level)
        if branch_activity:
            section.extend(["", "#### 分支操作", branch_activity])
        sections.append("\n".join(section))
    return "\n\n".join(sections) if sections else "无活跃仓库。"


def render_repo_table(analysis):
    lines = [
        "| 仓库 | 提交数 | 变更文件 | 新增/删除 | 主要工作 |",
        "|------|--------|----------|-----------|----------|",
    ]
    active_repos = analysis.get("active_repos") or []
    if not active_repos:
        lines.append("| 无 | 0 | 0 | +0/-0 | 无活跃提交 |")
        return "\n".join(lines)
    for repo in active_repos:
        stats = repo_diff_stats(repo)
        lines.append(
            f"| {repo.get('name', 'unknown')} | {len(repo_commits(repo))} | "
            f"{safe_int(stats.get('files_changed'))} | +{safe_int(stats.get('insertions'))}/-{safe_int(stats.get('deletions'))} | "
            f"{first_commit_subject(repo)} |"
        )
    return "\n".join(lines)


def render_focus_sections(analysis, report_type):
    active_repos = analysis.get("active_repos") or []
    if not active_repos:
        return "暂无核心成果。"
    title = "工作主题" if report_type == "weekly" else "成果主题"
    sections = []
    for index, repo in enumerate(active_repos[:5], start=1):
        sections.append(
            f"### {index}. {title}：{first_commit_subject(repo)}\n"
            f"- **涉及仓库：** {repo.get('name', 'unknown')}\n"
            f"- **进展：** 完成 {len(repo_commits(repo))} 次提交，涉及 {safe_int(repo_diff_stats(repo).get('files_changed'))} 个文件。\n"
            f"- **关键产出：** +{safe_int(repo_diff_stats(repo).get('insertions'))}/-{safe_int(repo_diff_stats(repo).get('deletions'))} 行变更"
        )
    return "\n\n".join(sections)



def requirement_title(repo):
    return repo.get("requirement") or repo.get("group") or ""


def render_task_points(repo):
    commits = repo_commits(repo)
    if not commits:
        return "- 暂无明确任务点。"
    lines = []
    for commit in commits:
        message = commit.get("subject") or commit.get("message", "无提交说明")
        short_hash = commit_short_hash(commit)
        lines.append(f"- {message}（`{short_hash}`）")
    return "\n".join(lines)


def render_requirement_sections(analysis):
    active_repos = analysis.get("active_repos") or []
    if not active_repos:
        return "一、 \n\n- 本周暂无匹配提交记录。"
    sections = []
    for index, repo in enumerate(active_repos, start=1):
        title = requirement_title(repo)
        heading = f"{chinese_number(index)}、 {title}" if title else f"{chinese_number(index)}、 "
        stats = repo_diff_stats(repo)
        sections.append(
            f"{heading}\n\n"
            f"当前状态： 已完成\n\n"
            f"时间规划： 下周继续跟进\n\n"
            f"具体完成任务点：\n\n"
            f"{render_task_points(repo)}\n\n"
            f"涉及仓库： {repo.get('name', '未知仓库')}；提交 {len(repo_commits(repo))} 次；"
            f"变更 {safe_int(stats.get('files_changed'))} 个文件；代码变更 +{safe_int(stats.get('insertions'))}/-{safe_int(stats.get('deletions'))} 行。"
        )
    return "\n\n".join(sections)


def render_weekly_summary(analysis, metrics):
    tasks = weekly_task_items(analysis)
    if not tasks:
        return "本周暂无明确任务进展，待补充实际完成工作。"
    titles = [task["title"] for task in tasks[:3]]
    focus = "、".join(titles)
    if len(tasks) == 1:
        return (
            f"本周重点推进{focus}。"
            f"相关能力已完成开发与基础验证，后续继续跟进联调、测试与问题修复。"
        )
    return (
        f"本周重点围绕{focus}推进。"
        f"各项任务已完成开发与基础验证，后续继续跟进联调、测试与问题修复。"
    )


def resolve_reporter_name(metadata, metrics):
    reporter = (metadata or {}).get("reporter") or (metadata or {}).get("reporter_name")
    if reporter:
        return str(reporter).strip()
    authors = metrics.get("authors") or []
    if authors:
        return str(authors[0]).strip()
    return ""


STATUS_DONE = "done"
STATUS_IN_PROGRESS = "in_progress"
STATUS_AT_RISK = "at_risk"

STATUS_LABELS = {
    STATUS_DONE: "✅ 已完成",
    STATUS_IN_PROGRESS: "进行中",
    STATUS_AT_RISK: "存在风险",
}

STATUS_COLORS = {
    STATUS_DONE: "green",
    STATUS_IN_PROGRESS: "blue",
    STATUS_AT_RISK: "red",
}


def normalize_status_key(status):
    text = str(status or "").strip().lower()
    if not text:
        return STATUS_DONE
    if text in (STATUS_DONE, STATUS_IN_PROGRESS, STATUS_AT_RISK):
        return text
    if any(token in text for token in ["风险", "异常", "阻塞", "blocked", "risk", "red", "at_risk", "at-risk"]):
        return STATUS_AT_RISK
    if any(
        token in text
        for token in ["进行", "未完成", "待跟进", "in_progress", "in-progress", "in progress", "wip", "blue", "跟进"]
    ):
        return STATUS_IN_PROGRESS
    if any(token in text for token in ["完成", "已上线", "done", "green", "✅"]):
        return STATUS_DONE
    # Already a colored HTML status or free-form label: treat unknown as done only when it looks complete.
    if "<font" in text:
        if "blue" in text:
            return STATUS_IN_PROGRESS
        if "red" in text:
            return STATUS_AT_RISK
        return STATUS_DONE
    return STATUS_DONE


def format_status_cell(status=STATUS_DONE, label=None):
    """Render weekly status cells.

    - Done: plain text with leading ✅ (no green font; ✅ already signals completion)
    - In progress: blue
    - At risk: red
    """
    text = str(status or "").strip()
    if "<font" in text:
        return text
    key = normalize_status_key(status)
    if label:
        display = label
    elif key == STATUS_DONE and text and text.lower() not in (
        STATUS_DONE,
        "已完成",
        "✅",
        "✅ 已完成",
        "done",
        "green",
    ):
        # Keep descriptive done labels like “完成自测” / “已修复”.
        display = text.strip()
    else:
        display = STATUS_LABELS[key]
    if key == STATUS_DONE and not display.startswith("✅"):
        display = f"✅ {display}"
    if key == STATUS_DONE:
        return display
    color = STATUS_COLORS[key]
    return f'<font color="{color}">{display}</font>'


def build_weekly_header(reporter_name, date_from_cn, date_to_cn):
    prefix = f"{reporter_name}汇报周期" if reporter_name else "汇报周期"
    return f"{prefix}: {date_from_cn} — {date_to_cn}"


def render_status_table(rows, column_name="事项", default_status=STATUS_DONE):
    """Render a weekly status table with 事项 / 状态 columns.

    Default is two columns (事项 | 状态), matching the usual weekly template.
    When any row has a non-empty remark (for unfinished / at-risk items), add a 备注 column.
    Incomplete rows without an explicit remark get a placeholder so the blocker/ETA is visible.

    Each row may be:
    - str: item title (status defaults to done)
    - (item, status)
    - (item, status, remark)
    - dict with keys item/status/remark (or 事项/状态/备注)
    """
    normalized = []
    for row in rows:
        item = ""
        status = default_status
        remark = ""
        if isinstance(row, dict):
            item = row.get("item") or row.get("事项") or row.get("title") or ""
            status = row.get("status") or row.get("状态") or default_status
            remark = row.get("remark") or row.get("备注") or ""
            if row.get("label") or row.get("status_label"):
                status_cell = format_status_cell(status, label=row.get("label") or row.get("status_label"))
            else:
                status_cell = format_status_cell(status)
        elif isinstance(row, (tuple, list)):
            if len(row) >= 1:
                item = row[0]
            if len(row) >= 2:
                status = row[1]
            if len(row) >= 3:
                remark = row[2]
            status_cell = format_status_cell(status)
        else:
            item = row
            status_cell = format_status_cell(status)

        key = normalize_status_key(status)
        if key != STATUS_DONE and not str(remark).strip():
            remark = "待补充阻碍原因与预计完成时间"
        normalized.append((item, status_cell, str(remark).strip()))

    include_remark = any(remark for _, _, remark in normalized)
    if include_remark:
        lines = [
            f"| {column_name} | 状态 | 备注 |",
            "|------|------|------|",
        ]
        for item, status_cell, remark in normalized:
            lines.append(f"| {item} | {status_cell} | {remark} |")
    else:
        lines = [
            f"| {column_name} | 状态 |",
            "|------|------|",
        ]
        for item, status_cell, _remark in normalized:
            lines.append(f"| {item} | {status_cell} |")
    return "\n".join(lines)


def task_sub_items(task):
    titles = []
    for message in task.get("messages", []):
        title = (
            message.replace("diff-feature: ", "")
            if str(message).startswith("diff-feature: ")
            else clean_task_title(message)
        )
        if title and title not in titles and not is_supporting_weekly_task(title):
            titles.append(title)
    return titles


def render_new_repo_items(analysis):
    repos = analysis.get("new_repos_detected") or []
    if not repos:
        return "- 暂无新增仓库。"
    lines = []
    for repo in repos:
        if isinstance(repo, str):
            lines.append(f"- `{repo}`")
        else:
            group = repo.get("group")
            suffix = f"（分组：{group}）" if group else ""
            lines.append(f"- {repo.get('name', '未命名仓库')}：`{repo.get('path', '')}`{suffix}")
    return "\n".join(lines)


def clean_task_title(message):
    title = re.sub(r"^\s*\[[^\]]+\]\s*", "", message or "").strip()
    title = re.sub(r"^\s*(feat|fix|docs|chore|refactor|test|style|perf)(\(.+?\))?:\s*", "", title, flags=re.IGNORECASE)
    if title == "移除脏数据":
        return "清理面试模块冗余配置和页面脏数据"
    title = title.lstrip(":：").strip()
    return title or "待补充任务名称"




def is_supporting_weekly_task(title):
    lowered = title.lower()
    return any(keyword in lowered for keyword in ["tobb资源引用", "资源引用", "优化图片资源", "代码提交", "代码格式化", "xml格式化", "硬编码尺寸", "格式化"])


def weekly_supporting_items(analysis):
    items = []
    for repo in analysis.get("active_repos") or []:
        for commit in repo_commits(repo):
            message = commit.get("subject") or commit.get("message", "")
            title = message.replace("diff-feature: ", "") if str(message).startswith("diff-feature: ") else clean_task_title(message)
            if is_supporting_weekly_task(title) and title not in items:
                items.append(title)
    return items

def commit_scope(message):
    match = re.match(r"^\s*(?:\[[^\]]+\]|[a-z]+)\(([^)]+)\)", message or "", flags=re.IGNORECASE)
    return match.group(1).lower() if match else ""



def diff_paths(repo):
    paths = []
    content = repo.get("diff_content") or ""
    for line in content.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                paths.append(parts[3][2:] if parts[3].startswith("b/") else parts[3])
        elif line.startswith("+++ b/") or line.startswith("--- a/"):
            paths.append(line[6:].strip())
    return list(dict.fromkeys(path for path in paths if path and path != "/dev/null"))


def diff_features(repo):
    paths = diff_paths(repo)
    joined = " ".join(paths).lower()
    features = []
    if any(token in joined for token in ["interview_manage", "interviewmanage", "activity_interview_manage", "item_interview_manage"]):
        features.append("面试管理页面布局")
    if any(token in joined for token in ["ordercontent", "customer", "content_order", "content_customer", "order_service"]):
        features.append("订单/客资内容展示")
    if any(token in joined for token in ["resume", "简历"]):
        features.append("面试简历操作栏")
    if any(token in joined for token in ["room_chat", "chatmessage", "interviewroomchat"]):
        features.append("面试房间聊天组件")
    return features


def diff_bucket(repo, message, title):
    features = diff_features(repo)
    if any(feature in features for feature in ["面试管理页面布局", "订单/客资内容展示", "面试简历操作栏"]):
        return "面试管理页面建设与优化"
    if "面试房间聊天组件" in features:
        return "面试房间聊天能力建设"
    return ""

def task_bucket(message, title):
    scope = commit_scope(message)
    content = f"{scope} {title}".lower()
    if any(keyword in content for keyword in ["面试管理", "面试列表", "快速面试", "客资", "订单", "简历操作栏"]):
        return "面试管理页面建设与优化"
    if any(keyword in content for keyword in ["聊天组件", "chatmessage", "room_chat", "聊天输入"]):
        return "面试房间聊天能力建设"
    if any(keyword in content for keyword in ["录制", "补偿上传", "轮询"]):
        return "面试业务流程与管理功能开发"
    if any(keyword in content for keyword in ["interviewmeeting", "美颜", "麦克风", "摄像头", "成员管理", "服务人员", "扬声器", "房间", "邀请", "微信分享", "二次确认"]):
        return "面试会议房间能力完善"
    if any(keyword in content for keyword in ["ui", "layout", "recyclerview", "样式", "浮窗", "屏幕共享", "更多", "底部栏", "音视频状态"]):
        return "面试相关界面与交互体验优化"
    if any(keyword in content for keyword in ["api", "utils", "interviewid", "接口", "请求", "网络", "context"]):
        return "面试基础接口与工具能力建设"
    return title



def task_group_key(title):
    words = title.split()
    if len(words) >= 2:
        return " ".join(words[:2]).lower()
    return title.lower()


def merge_task_title(existing_title, new_title):
    existing_words = existing_title.split()
    new_words = new_title.split()
    common = []
    for existing_word, new_word in zip(existing_words, new_words):
        if existing_word.lower() != new_word.lower():
            break
        common.append(existing_word)
    if len(common) >= 2:
        return " ".join(common)
    return existing_title


def weekly_task_items(analysis):
    grouped = {}
    for repo in analysis.get("active_repos") or []:
        stats = repo_diff_stats(repo)
        for commit in repo_commits(repo):
            message = commit.get("subject") or commit.get("message", "")
            title = clean_task_title(message)
            if is_supporting_weekly_task(title):
                continue
            bucket = diff_bucket(repo, message, title) or task_bucket(message, title)
            key = bucket.lower() if bucket != title else task_group_key(title)
            if key not in grouped:
                grouped[key] = {
                    "title": bucket,
                    "messages": [],
                    "hashes": [],
                    "files_changed": 0,
                    "insertions": 0,
                    "deletions": 0,
                    "commit_count": 0,
                }
            task = grouped[key]
            if task["title"] == title:
                task["title"] = merge_task_title(task["title"], title)
            task["messages"].append(message or "待补充提交说明")
            for feature in diff_features(repo):
                marker = f"diff-feature: {feature}"
                if marker not in task["messages"]:
                    task["messages"].append(marker)
            task["hashes"].append(commit_short_hash(commit))
            task["files_changed"] += safe_int(stats.get("files_changed"))
            task["insertions"] += safe_int(stats.get("insertions"))
            task["deletions"] += safe_int(stats.get("deletions"))
            task["commit_count"] += 1
    return list(grouped.values())

def task_detail_summary(task):
    titles = task_sub_items(task)
    if not titles:
        return "完成相关开发、调整和基础验证工作。"
    if len(titles) == 1:
        return f"完成{titles[0]}相关开发、调整和基础验证工作。"

    bullet_lines = "\n".join(f"  - {title}" for title in titles[:8])
    suffix = "\n  - 其他相关联调和问题修复" if len(titles) > 8 else ""
    return f"完成以下任务：\n{bullet_lines}{suffix}"


def describe_weekly_task(task):
    return task_detail_summary(task)


def infer_status_column_name(items):
    joined = " ".join(items)
    if any(token in joined for token in ["支付", "微信", "支付宝", "转账", "扫码"]):
        return "渠道"
    if any(token in joined for token in ["模块", "页面", "房间", "能力"]):
        return "模块"
    if any(token in joined for token in ["功能", "接口", "联调", "自测"]):
        return "功能"
    return "事项"


def render_weekly_task_block(index, title, items, default_status=STATUS_DONE):
    heading = f"**任务{chinese_number(index)}：{title}**"
    rows = items or [title]
    column_name = infer_status_column_name(
        [r if isinstance(r, str) else (r[0] if isinstance(r, (tuple, list)) else r.get("item") or r.get("事项") or "") for r in rows]
    )
    table = render_status_table(rows[:8], column_name=column_name, default_status=default_status)
    return f"{heading}\n\n{table}"


def render_weekly_task_sections(analysis):
    tasks = weekly_task_items(analysis)
    supporting = weekly_supporting_items(analysis)
    if not tasks and not supporting:
        return render_weekly_task_block(
            1,
            "",
            [{"item": "待补充本周实际完成任务", "status": STATUS_IN_PROGRESS, "remark": "待补充阻碍原因与预计完成时间"}],
            default_status=STATUS_IN_PROGRESS,
        )

    sections = []
    for index, task in enumerate(tasks, start=1):
        items = task_sub_items(task)
        if not items:
            items = [task["title"]]
        sections.append(render_weekly_task_block(index, task["title"], items))

    if supporting:
        sections.append(
            render_weekly_task_block(
                len(sections) + 1,
                "其他/支撑性调整",
                supporting[:8],
                default_status=STATUS_DONE,
            )
        )
    return "\n\n".join(sections)


def render_weekly_next_plan_items(analysis):
    tasks = weekly_task_items(analysis)
    if not tasks:
        return "1. 补充本周任务归档，并明确下周待推进事项。"
    return "\n".join(
        f"{index}. 跟进{task['title']}的验证、联调及潜在问题处理。"
        for index, task in enumerate(tasks[:5], start=1)
    )


def render_weekly_other_items(analysis):
    new_repos = analysis.get("new_repos_detected") or []
    supporting = weekly_supporting_items(analysis)
    lines = []
    if supporting:
        lines.append(f"- 支撑性调整：{'、'.join(supporting[:8])}。")
    if new_repos:
        names = []
        for repo in new_repos[:8]:
            repo_name = repo if isinstance(repo, str) else repo.get("name", "未命名仓库")
            names.append(host_app_display_name(repo_name))
        lines.append(f"- 本周检测到新增代码仓库/模块：{'、'.join(names)}。")
    if not lines:
        lines.append("- 暂无其他补充事项。")
    return "\n".join(lines)


def render_metrics_table(metrics):
    return "\n".join(
        [
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 活跃仓库数 | {metrics['repos_active']} |",
            f"| 总提交数 | {metrics['commits_total']} |",
            f"| 总文件变更 | {metrics['files_changed']} |",
            f"| 代码新增 | +{metrics['insertions']} 行 |",
            f"| 代码删除 | -{metrics['deletions']} 行 |",
            f"| 活跃天数 | {metrics['active_days']} |",
        ]
    )


def render_new_repos_section(analysis):
    repos = analysis.get("new_repos_detected") or []
    if not repos:
        return ""
    lines = ["## 新发现仓库", ""]
    lines.extend(f"- **{repo.get('name', 'unknown')}**：`{repo.get('path', '')}`" for repo in repos)
    return "\n".join(lines)


def default_summary(report_type, metrics):
    labels = {"daily": "今日", "weekly": "本周", "monthly": "本月"}
    label = labels[report_type]
    return (
        f"{label}共记录 {metrics['commits_total']} 次提交，"
        f"覆盖 {metrics['repos_active']} 个活跃仓库，"
        f"累计变更 {metrics['files_changed']} 个文件。"
    )


def build_frontmatter(report_type, analysis, metadata, metrics):
    date_range = analysis.get("date_range") or {}
    generated = metadata.get("generated") or datetime.now().replace(microsecond=0).isoformat()
    level = metadata.get("level", "standard" if report_type == "daily" else "brief")
    date_value = metadata.get("date") or date_range.get("from") or datetime.now().strftime("%Y-%m-%d")

    common = {
        "title": f"日报 {date_value}" if report_type == "daily" else "",
        "date": date_value,
        "type": f"{report_type}-report",
        "level": level,
        "repos_scanned": metrics["repos_scanned"],
        "repos_active": metrics["repos_active"],
        "commits_total": metrics["commits_total"],
        "authors": metrics["authors"],
        "tags": [f"{report_type}-report", date_value[:7] if report_type != "monthly" else date_value[:4]],
    }

    if report_type == "weekly":
        week = metadata.get("week") or iso_week_label(date_range.get("from", date_value))
        common["title"] = f"周报 {week}"
        common["week"] = week
        common["date_range"] = {"from": date_range.get("from", date_value), "to": inclusive_end_date(date_range.get("to", date_value))}
        common["source"] = metadata.get("source", "daily-summary")
    elif report_type == "monthly":
        month = metadata.get("month") or date_value[:7]
        common["title"] = f"月报 {month}"
        common["month"] = month
        common["date_range"] = {"from": date_range.get("from", f"{month}-01"), "to": inclusive_end_date(date_range.get("to", date_value))}
        common["source"] = metadata.get("source", "weekly-summary")
    else:
        groups = metadata.get("groups", [])
        if groups:
            common["groups"] = groups

    common["repos"] = metrics["repos"]
    common["generated"] = generated
    return common


def inclusive_end_date(end_date):
    if not end_date:
        return ""
    return (parse_date(end_date) - timedelta(days=1)).strftime("%Y-%m-%d")


def iso_week_label(date_text):
    dt = parse_date(date_text)
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def template_context(report_type, analysis, metadata, metrics):
    date_range = analysis.get("date_range") or {}
    date_value = metadata.get("date") or date_range.get("from") or datetime.now().strftime("%Y-%m-%d")
    dt = parse_date(date_value)
    week = metadata.get("week") or iso_week_label(date_range.get("from", date_value))
    iso_year, iso_week_text = week.split("-W")
    month = metadata.get("month") or date_value[:7]
    month_year, month_number = month.split("-")
    source = metadata.get("source", "daily-summary" if report_type == "weekly" else "weekly-summary")

    date_from_cn = format_cn_date(date_range.get("from") or date_value)
    date_to_cn = format_cn_date(inclusive_end_date(date_range.get("to") or date_value))
    reporter_name = resolve_reporter_name(metadata, metrics)
    weekly_summary = metadata.get("summary") if report_type == "weekly" and metadata.get("summary") else render_weekly_summary(analysis, metrics)

    context = {
        "frontmatter": format_frontmatter(build_frontmatter(report_type, analysis, metadata, metrics)),
        "date": date_value,
        "date_cn": format_cn_date(date_value),
        "weekday": "一二三四五六日"[dt.weekday()],
        "repos_active": metrics["repos_active"],
        "commits_total": metrics["commits_total"],
        "files_changed": metrics["files_changed"],
        "insertions": metrics["insertions"],
        "deletions": metrics["deletions"],
        "main_focus": infer_main_focus(analysis),
        "reporter_name": reporter_name,
        "weekly_header": build_weekly_header(reporter_name, date_from_cn, date_to_cn),
        "weekly_summary": weekly_summary,
        "requirement_sections": render_requirement_sections(analysis),
        "weekly_task_sections": render_weekly_task_sections(analysis),
        "weekly_next_plan_items": render_weekly_next_plan_items(analysis),
        "weekly_other_items": render_weekly_other_items(analysis),
        "repo_sections": render_repo_sections(analysis, metadata.get("level", "standard")),
        "numbered_work_items": render_numbered_work_items(analysis, report_type),
        "next_plan_items": render_next_plan_items(analysis, report_type),
        "other_items": render_other_items(analysis),
        "repo_table": render_repo_table(analysis),
        "focus_sections": render_focus_sections(analysis, report_type),
        "metrics_table": render_metrics_table(metrics),
        "new_repos_section": render_new_repos_section(analysis),
        "new_repo_items": render_new_repo_items(analysis),
        "summary": metadata.get("summary") or default_summary(report_type, metrics),
        "source": source,
        "iso_year": iso_year,
        "iso_week": str(int(iso_week_text)),
        "date_from_mmdd": (date_range.get("from") or date_value)[5:],
        "date_to_mmdd": inclusive_end_date(date_range.get("to") or date_value)[5:],
        "date_from_cn": date_from_cn,
        "date_to_cn": date_to_cn,
        "month_year": month_year,
        "month_number": str(int(month_number)),
        "active_days": metrics["active_days"],
    }
    return context


def render_report(report_type, analysis, metadata=None, template_dir=None):
    metadata = metadata or {}
    metrics = collect_metrics(analysis)
    template = load_template(report_type, template_dir)
    markdown = template.format(**template_context(report_type, analysis, metadata, metrics))
    if report_type == "weekly":
        markdown = normalize_weekly_host_app_names(markdown, analysis)
    return markdown.rstrip() + "\n"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="DailyReport Markdown 模板渲染器")
    parser.add_argument("--type", choices=sorted(REPORT_TYPES), required=True, help="报告类型")
    parser.add_argument("--input", required=True, help="dr_analyze.py 输出的 JSON 文件")
    parser.add_argument("--output", default=None, help="Markdown 输出路径；未指定时输出到 stdout")
    parser.add_argument("--date", default=None, help="报告日期 YYYY-MM-DD")
    parser.add_argument("--week", default=None, help="周标签 YYYY-Www")
    parser.add_argument("--month", default=None, help="月标签 YYYY-MM")
    parser.add_argument("--level", default=None, help="详细度 brief/standard/detailed")
    parser.add_argument("--source", default=None, help="数据来源标记")
    parser.add_argument("--summary", default=None, help="可选 AI 总结文本")
    parser.add_argument("--reporter", default=None, help="周报汇报人姓名")
    parser.add_argument("--generated", default=None, help="生成时间 ISO 字符串")
    parser.add_argument("--template-dir", default=None, help="自定义模板目录")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    analysis = json.loads(Path(args.input).read_text(encoding="utf-8"))
    metadata = {
        "date": args.date,
        "week": args.week,
        "month": args.month,
        "level": args.level,
        "source": args.source,
        "summary": args.summary,
        "reporter": args.reporter,
        "generated": args.generated,
    }
    metadata = {key: value for key, value in metadata.items() if value is not None}
    markdown = render_report(args.type, analysis, metadata, args.template_dir)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
