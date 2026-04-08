#!/usr/bin/env python3
"""
dr_analyze.py - DailyReport Git 分析引擎

对配置中的仓库执行 Git 数据采集：提交记录、代码 diff、分支操作。
支持仓库预筛选（通过文件系统 mtime 快速排除无活动仓库）。

用法:
  python3 dr_analyze.py --config ~/.config/dailyreport/config.json --from 2026-04-07 --to 2026-04-08
  python3 dr_analyze.py --config ~/.config/dailyreport/config.json --from 2026-04-07 --to 2026-04-08 --diff
  python3 dr_analyze.py --config ~/.config/dailyreport/config.json --from 2026-04-01 --to 2026-04-08 --diff --repos my-app,backend

输出: JSON 到 stdout
"""

import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dr_common import (
    eprint,
    git_cmd,
    is_git_repo,
    json_output,
    load_config,
    parse_date,
)

# diff 内容截断限制
DIFF_MAX_LINES_PER_FILE = 80
DIFF_MAX_TOTAL_BYTES = 50 * 1024  # 50KB

# 默认跳过的 diff 文件模式
DEFAULT_SKIP_DIFF_PATTERNS = [
    "*.lock",
    "*-lock.json",
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.svg",
    "dist/*",
    "build/*",
    ".next/*",
    "coverage/*",
    "__snapshots__/*",
    "*.pb.go",
    "*.generated.*",
]


def should_skip_diff_file(filepath, skip_patterns):
    """检查文件是否应跳过 diff 分析"""
    for pattern in skip_patterns:
        if fnmatch.fnmatch(filepath, pattern):
            return True
    return False


def pre_screen_repos(repos, date_from, date_to):
    """
    通过文件系统元数据快速预筛选有活动的仓库。

    检查 .git/logs/HEAD 和 .git/index 的 mtime，
    如果两者都早于目标日期范围的起始时间，判定为无活动。
    """
    from_ts = parse_date(date_from).timestamp()
    active = []
    skipped = []

    for repo in repos:
        repo_path = Path(repo["path"])
        if not repo_path.exists() or not is_git_repo(repo_path):
            skipped.append({"name": repo["name"], "reason": "path_not_found"})
            continue

        # 检查 mtime
        git_dir = repo_path / ".git"
        head_log = git_dir / "logs" / "HEAD"
        index_file = git_dir / "index"

        latest_mtime = 0
        for f in [head_log, index_file]:
            if f.exists():
                mtime = f.stat().st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime

        if latest_mtime > 0 and latest_mtime < from_ts:
            skipped.append({"name": repo["name"], "reason": "no_recent_activity"})
            continue

        active.append(repo)

    return active, skipped


def verify_repo_activity(repo_path, author_email, date_from, date_to):
    """精确验证仓库在指定时段是否有指定用户的提交"""
    result = git_cmd(
        repo_path,
        [
            "log",
            "--oneline",
            f"--after={date_from}",
            f"--before={date_to}",
            f"--author={author_email}",
            "-1",
        ],
    )
    return result is not None and len(result) > 0


def get_commits(repo_path, author_email, date_from, date_to):
    """
    获取指定时段、指定用户的提交记录。
    返回结构化的提交列表。
    """
    # 自定义格式：hash|author_name|date|message
    separator = "---COMMIT_SEP---"
    format_str = f"%H|%an|%ai|%s{separator}"

    raw = git_cmd(
        repo_path,
        [
            "log",
            f"--after={date_from}",
            f"--before={date_to}",
            f"--author={author_email}",
            f"--format={format_str}",
            "--no-merges",
        ],
    )

    if not raw:
        return []

    commits = []
    for entry in raw.split(separator):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("|", 3)
        if len(parts) < 4:
            continue
        commits.append(
            {
                "hash": parts[0][:8],
                "hash_full": parts[0],
                "author": parts[1],
                "date": parts[2],
                "message": parts[3],
            }
        )

    return commits


def get_diff_stats(repo_path, author_email, date_from, date_to):
    """
    获取 diff 统计信息：文件变更数、插入/删除行数、按文件类型分组。
    """
    raw = git_cmd(
        repo_path,
        [
            "log",
            f"--after={date_from}",
            f"--before={date_to}",
            f"--author={author_email}",
            "--shortstat",
            "--no-merges",
            "--format=",
        ],
    )

    if not raw:
        return {"files_changed": 0, "insertions": 0, "deletions": 0, "by_type": {}}

    total_files = 0
    total_insertions = 0
    total_deletions = 0

    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # 匹配: "3 files changed, 10 insertions(+), 5 deletions(-)"
        files_match = re.search(r"(\d+) files? changed", line)
        ins_match = re.search(r"(\d+) insertions?\(\+\)", line)
        del_match = re.search(r"(\d+) deletions?\(-\)", line)

        if files_match:
            total_files += int(files_match.group(1))
        if ins_match:
            total_insertions += int(ins_match.group(1))
        if del_match:
            total_deletions += int(del_match.group(1))

    # 按文件类型分组统计
    numstat_raw = git_cmd(
        repo_path,
        [
            "log",
            f"--after={date_from}",
            f"--before={date_to}",
            f"--author={author_email}",
            "--numstat",
            "--no-merges",
            "--format=",
        ],
    )

    by_type = {}
    if numstat_raw:
        for line in numstat_raw.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            added, deleted, filepath = parts[0], parts[1], parts[2]
            # 二进制文件显示为 -
            if added == "-" or deleted == "-":
                continue
            ext = Path(filepath).suffix or "(no ext)"
            if ext not in by_type:
                by_type[ext] = {"insertions": 0, "deletions": 0, "files": 0}
            by_type[ext]["insertions"] += int(added)
            by_type[ext]["deletions"] += int(deleted)
            by_type[ext]["files"] += 1

    return {
        "files_changed": total_files,
        "insertions": total_insertions,
        "deletions": total_deletions,
        "by_type": by_type,
    }


def get_diff_content(repo_path, author_email, date_from, date_to, skip_patterns):
    """
    获取 diff 内容（实际代码变更）。
    对每个提交获取 diff，按文件截断，跳过不需要的文件。
    返回格式化的 diff 文本。
    """
    # 获取提交哈希列表
    hashes_raw = git_cmd(
        repo_path,
        [
            "log",
            f"--after={date_from}",
            f"--before={date_to}",
            f"--author={author_email}",
            "--format=%H",
            "--no-merges",
        ],
    )

    if not hashes_raw:
        return ""

    hashes = [h.strip() for h in hashes_raw.split("\n") if h.strip()]
    diff_parts = []
    total_bytes = 0

    for commit_hash in hashes:
        if total_bytes >= DIFF_MAX_TOTAL_BYTES:
            diff_parts.append(
                f"\n... (已达到 diff 总量上限 {DIFF_MAX_TOTAL_BYTES // 1024}KB，后续提交省略)"
            )
            break

        # 获取提交信息
        msg = git_cmd(repo_path, ["log", "-1", "--format=%s", commit_hash])
        stat = git_cmd(repo_path, ["diff-tree", "--stat", "--no-commit-id", "-r", commit_hash])

        diff_parts.append(f"\n### commit {commit_hash[:8]}: {msg or '(no message)'}")
        if stat:
            diff_parts.append(f"```\n{stat}\n```")

        # 获取变更文件列表
        files_raw = git_cmd(
            repo_path,
            ["diff-tree", "--no-commit-id", "-r", "--name-only", commit_hash],
        )
        if not files_raw:
            continue

        files = [f.strip() for f in files_raw.split("\n") if f.strip()]

        for filepath in files:
            if should_skip_diff_file(filepath, skip_patterns):
                diff_parts.append(f"  - `{filepath}` (跳过: 匹配过滤规则)")
                continue

            # 获取单文件 diff
            file_diff = git_cmd(
                repo_path,
                ["diff-tree", "-p", "--no-commit-id", commit_hash, "--", filepath],
            )

            if not file_diff:
                continue

            # 检测二进制文件
            if "Binary files" in file_diff[:200]:
                diff_parts.append(f"  - `{filepath}` (二进制文件，跳过)")
                continue

            # 按行截断
            lines = file_diff.split("\n")
            if len(lines) > DIFF_MAX_LINES_PER_FILE:
                truncated = "\n".join(lines[:DIFF_MAX_LINES_PER_FILE])
                truncated += f"\n... (截断, 共 {len(lines)} 行)"
                file_diff = truncated

            diff_parts.append(f"```diff\n{file_diff}\n```")
            total_bytes += len(file_diff.encode("utf-8"))

            if total_bytes >= DIFF_MAX_TOTAL_BYTES:
                break

    return "\n".join(diff_parts)


def get_branch_activity(repo_path, author_email, date_from, date_to):
    """
    获取分支操作信息：当前分支、创建/合并的分支。
    从 reflog 中提取 checkout、merge 操作。
    """
    result = {
        "current": "",
        "created": [],
        "merged": [],
    }

    # 当前分支
    current = git_cmd(repo_path, ["branch", "--show-current"])
    result["current"] = current or "(detached)"

    # 从 reflog 提取分支操作
    reflog_raw = git_cmd(
        repo_path,
        [
            "reflog",
            f"--after={date_from}",
            f"--before={date_to}",
            "--format=%gd|%gs",
        ],
    )

    if not reflog_raw:
        return result

    created_branches = set()
    merged_branches = set()

    for line in reflog_raw.split("\n"):
        line = line.strip()
        if not line:
            continue

        parts = line.split("|", 1)
        if len(parts) < 2:
            continue
        action = parts[1]

        # 检测分支创建（checkout 到新分支）
        if "checkout: moving from" in action:
            match = re.search(r"to (.+)$", action)
            if match:
                branch = match.group(1).strip()
                # 检查是否是新创建的分支（简化检测）
                if branch not in created_branches:
                    created_branches.add(branch)

        # 检测合并操作
        if action.startswith("merge ") or "merge" in action.lower():
            match = re.search(r"merge\s+(\S+)", action, re.IGNORECASE)
            if match:
                merged_branches.add(match.group(1))

    # 精简：创建的分支列表（去除 main/master/develop 等常见分支）
    common_branches = {"main", "master", "develop", "dev", "staging", "release"}
    result["created"] = sorted(created_branches - common_branches)
    result["merged"] = sorted(merged_branches)

    return result


def detect_new_repos_in_workspace(config):
    """检测工作区中的新增仓库"""
    workspace_root = config.get("workspace_root", "")
    if not workspace_root or not Path(workspace_root).is_dir():
        return []

    registered_paths = {r["path"] for r in config.get("repositories", [])}
    skip_dirs = set(config.get("scan_settings", {}).get("skip_dirs", []))
    max_depth = config.get("scan_settings", {}).get("max_depth", 5)

    # 轻量级扫描：仅检测新目录
    workspace = Path(workspace_root).resolve()
    new_repos = []

    for dirpath, dirnames, _ in os.walk(workspace, topdown=True):
        current = Path(dirpath)
        depth = len(current.relative_to(workspace).parts)

        if depth >= max_depth:
            dirnames.clear()
            continue

        if is_git_repo(current):
            if str(current) not in registered_paths:
                new_repos.append(str(current))
            dirnames.clear()
            continue

        dirnames[:] = [
            d for d in dirnames if not d.startswith(".") and d not in skip_dirs
        ]

    return new_repos


def analyze_repo(repo_info, date_from, date_to, include_diff, skip_patterns):
    """分析单个仓库的 Git 活动"""
    repo_path = repo_info["path"]
    author_email = repo_info["git_user"]["email"]

    result = {
        "name": repo_info["name"],
        "path": repo_path,
        "git_user": repo_info["git_user"],
        "commits": get_commits(repo_path, author_email, date_from, date_to),
        "diff_stats": get_diff_stats(repo_path, author_email, date_from, date_to),
        "branch_activity": get_branch_activity(
            repo_path, author_email, date_from, date_to
        ),
    }

    if include_diff:
        result["diff_content"] = get_diff_content(
            repo_path, author_email, date_from, date_to, skip_patterns
        )
    else:
        result["diff_content"] = ""

    return result


def main():
    parser = argparse.ArgumentParser(description="DailyReport Git 分析引擎")
    parser.add_argument(
        "--config",
        default=None,
        help="配置文件路径",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        required=True,
        help="起始日期 (YYYY-MM-DD, 含)",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        required=True,
        help="结束日期 (YYYY-MM-DD, 不含)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="启用 diff 内容分析",
    )
    parser.add_argument(
        "--repos",
        default=None,
        help="指定仓库名称（逗号分隔），不指定则分析所有",
    )
    parser.add_argument(
        "--stat-only",
        action="store_true",
        help="仅获取统计信息，不获取 diff 内容（用于月报）",
    )
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    if config is None:
        eprint("错误: 配置文件不存在，请先执行 /dr_init")
        sys.exit(1)

    repositories = config.get("repositories", [])
    if not repositories:
        eprint("错误: 没有已注册的仓库，请先执行 /dr_init")
        sys.exit(1)

    # 过滤指定仓库
    if args.repos:
        repo_names = set(args.repos.split(","))
        repositories = [r for r in repositories if r["name"] in repo_names]
        if not repositories:
            eprint(f"错误: 未找到匹配的仓库: {args.repos}")
            sys.exit(1)

    # diff 跳过模式
    skip_patterns = config.get("scan_settings", {}).get(
        "skip_diff_patterns", DEFAULT_SKIP_DIFF_PATTERNS
    )

    # 仓库预筛选
    active_repos, skipped_repos = pre_screen_repos(
        repositories, args.date_from, args.date_to
    )

    # 精确验证
    verified_repos = []
    for repo in active_repos:
        if verify_repo_activity(
            repo["path"],
            repo["git_user"]["email"],
            args.date_from,
            args.date_to,
        ):
            verified_repos.append(repo)
        else:
            skipped_repos.append(
                {"name": repo["name"], "reason": "no_user_commits"}
            )

    # 分析每个活跃仓库
    active_results = []
    include_diff = args.diff and not args.stat_only
    for repo in verified_repos:
        repo_result = analyze_repo(
            repo, args.date_from, args.date_to, include_diff, skip_patterns
        )
        active_results.append(repo_result)

    # 检测新仓库
    new_repos = detect_new_repos_in_workspace(config)

    # 输出结果
    output = {
        "date_range": {"from": args.date_from, "to": args.date_to},
        "active_repos": active_results,
        "skipped_repos": skipped_repos,
        "new_repos_detected": new_repos,
    }

    json_output(output)


if __name__ == "__main__":
    main()
