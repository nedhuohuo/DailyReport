#!/usr/bin/env python3
"""
dr_scan.py - DailyReport 仓库发现与扫描引擎

扫描工作区目录，发现所有 Git 仓库，读取每个仓库的 Git 用户配置。
支持全量扫描和增量检测（仅发现新增仓库）。

用法:
  python3 dr_scan.py --workspace /path/to/root
  python3 dr_scan.py --workspace /path/to/root --config ~/.config/dailyreport/config.json --detect-new

输出: JSON 数组到 stdout
"""

import argparse
import os
import sys
from pathlib import Path

# 确保可以导入同目录的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dr_common import (
    eprint,
    git_config_user,
    is_git_repo,
    json_output,
    load_config,
)


def scan_workspace(workspace_root, skip_dirs=None, max_depth=5):
    """
    扫描工作区目录，发现所有 Git 仓库。

    策略:
    - 递归遍历目录树，查找包含 .git 的目录
    - 找到 .git 后不再深入该仓库的子目录
    - 跳过隐藏目录（以 . 开头）和 skip_dirs 中列出的目录
    - 深度上限 max_depth 层

    返回仓库信息列表。
    """
    if skip_dirs is None:
        skip_dirs = {
            "node_modules",
            "vendor",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".build",
            "Pods",
            ".gradle",
        }
    else:
        skip_dirs = set(skip_dirs)

    workspace_root = Path(workspace_root).resolve()
    repos = []

    for dirpath, dirnames, _ in os.walk(workspace_root, topdown=True):
        current = Path(dirpath)
        depth = len(current.relative_to(workspace_root).parts)

        # 深度检查
        if depth >= max_depth:
            dirnames.clear()
            continue

        # 检查当前目录是否是 Git 仓库
        if is_git_repo(current):
            user_info = git_config_user(current)
            repos.append(
                {
                    "path": str(current),
                    "name": current.name,
                    "git_user": {
                        "name": user_info["name"],
                        "email": user_info["email"],
                    },
                    "git_user_source": user_info["source"],
                }
            )
            # 不再深入仓库子目录
            dirnames.clear()
            continue

        # 过滤掉不需要遍历的子目录
        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".") and d not in skip_dirs
        ]
        # 按名称排序，确保输出一致性
        dirnames.sort()

    return repos


def detect_new_repos(workspace_root, config, skip_dirs=None, max_depth=5):
    """
    增量检测：扫描工作区并对比已注册仓库列表，只返回新发现的仓库。
    """
    all_repos = scan_workspace(workspace_root, skip_dirs, max_depth)
    registered_paths = {r["path"] for r in config.get("repositories", [])}
    new_repos = [r for r in all_repos if r["path"] not in registered_paths]
    return new_repos


def main():
    parser = argparse.ArgumentParser(description="DailyReport 仓库扫描引擎")
    parser.add_argument(
        "--workspace",
        required=True,
        help="工作区根目录路径",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="配置文件路径（用于增量检测模式）",
    )
    parser.add_argument(
        "--detect-new",
        action="store_true",
        help="增量检测模式：仅输出新发现的仓库",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="扫描深度上限（默认 5）",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.is_dir():
        eprint(f"错误: 工作区目录不存在: {workspace}")
        sys.exit(1)

    # 读取配置中的扫描设置
    config = None
    skip_dirs = None
    max_depth = args.max_depth

    if args.config:
        config = load_config(args.config)
    elif args.detect_new:
        config = load_config()

    if config and "scan_settings" in config:
        skip_dirs = config["scan_settings"].get("skip_dirs")
        max_depth = config["scan_settings"].get("max_depth", max_depth)

    if args.detect_new:
        if config is None:
            eprint("错误: 增量检测模式需要配置文件，请先执行 /dr_init")
            sys.exit(1)
        repos = detect_new_repos(workspace, config, skip_dirs, max_depth)
    else:
        repos = scan_workspace(workspace, skip_dirs, max_depth)

    json_output(repos)


if __name__ == "__main__":
    main()
