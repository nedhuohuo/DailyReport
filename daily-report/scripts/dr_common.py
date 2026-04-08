"""
dr_common.py - DailyReport 共享工具模块

提供配置管理、日期范围计算、Git 命令封装等基础功能。
被 dr_scan.py 和 dr_analyze.py 导入使用。
零第三方依赖，仅使用 Python 标准库。
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 配置文件路径
CONFIG_DIR = Path.home() / ".config" / "dailyreport"
CONFIG_PATH = CONFIG_DIR / "config.json"

# 默认配置结构
DEFAULT_CONFIG = {
    "version": 1,
    "workspace_root": "",
    "output": {
        "vault_dir": "",
        "base_folder": "DailyReport",
        "daily_folder": "daily",
        "weekly_folder": "weekly",
        "monthly_folder": "monthly",
    },
    "defaults": {
        "level": "standard",
        "language": "zh-CN",
    },
    "repositories": [],
    "scan_settings": {
        "max_depth": 5,
        "skip_dirs": [
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
        ],
        "skip_diff_patterns": [
            "*.lock",
            "*-lock.json",
            "*.min.js",
            "*.min.css",
            "*.map",
            "dist/*",
            "build/*",
            ".next/*",
            "coverage/*",
            "__snapshots__/*",
        ],
    },
}


def load_config(config_path=None):
    """读取配置文件，不存在则返回 None"""
    path = Path(config_path) if config_path else CONFIG_PATH
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config, config_path=None):
    """写入配置文件，自动创建目录"""
    path = Path(config_path) if config_path else CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_default_config():
    """返回默认配置的深拷贝"""
    return json.loads(json.dumps(DEFAULT_CONFIG))


# ============================================================
# 日期范围计算
# ============================================================


def parse_date(date_str):
    """解析日期字符串为 datetime 对象，支持 YYYY-MM-DD 格式"""
    return datetime.strptime(date_str, "%Y-%m-%d")


def today_str():
    """返回今天的日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")


def date_range_daily(date_str=None):
    """
    计算日报的日期范围。
    返回 (start, end)，均为 YYYY-MM-DD 格式。
    start 为目标日期，end 为目标日期 +1 天（用于 git log --before）。
    """
    if date_str is None:
        date_str = today_str()
    dt = parse_date(date_str)
    start = dt.strftime("%Y-%m-%d")
    end = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    return start, end


def date_range_weekly(date_str=None):
    """
    计算周报的日期范围（ISO 周：周一 ~ 周日）。
    如果未指定日期，默认为本周。
    返回 (start, end, week_label)。
    week_label 格式为 YYYY-Www（如 2026-W15）。
    """
    if date_str is None:
        dt = datetime.now()
    else:
        dt = parse_date(date_str)
    # ISO 周一
    monday = dt - timedelta(days=dt.weekday())
    sunday = monday + timedelta(days=6)
    start = monday.strftime("%Y-%m-%d")
    end = (sunday + timedelta(days=1)).strftime("%Y-%m-%d")
    iso_year, iso_week, _ = monday.isocalendar()
    week_label = f"{iso_year}-W{iso_week:02d}"
    return start, end, week_label


def date_range_monthly(date_str=None):
    """
    计算月报的日期范围。
    如果未指定日期，默认为本月。
    date_str 支持 YYYY-MM 或 YYYY-MM-DD 格式。
    返回 (start, end, month_label)。
    month_label 格式为 YYYY-MM。
    """
    if date_str is None:
        dt = datetime.now()
    elif len(date_str) == 7:  # YYYY-MM
        dt = datetime.strptime(date_str, "%Y-%m")
    else:
        dt = parse_date(date_str)
    first_day = dt.replace(day=1)
    if first_day.month == 12:
        next_month_first = first_day.replace(year=first_day.year + 1, month=1)
    else:
        next_month_first = first_day.replace(month=first_day.month + 1)
    start = first_day.strftime("%Y-%m-%d")
    end = next_month_first.strftime("%Y-%m-%d")
    month_label = first_day.strftime("%Y-%m")
    return start, end, month_label


def dates_in_range(start_str, end_str):
    """生成日期范围内所有日期的字符串列表（不含 end）"""
    start = parse_date(start_str)
    end = parse_date(end_str)
    dates = []
    current = start
    while current < end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def weeks_in_month(start_str, end_str):
    """返回月份范围内涉及的所有 ISO 周标签列表"""
    start = parse_date(start_str)
    end = parse_date(end_str) - timedelta(days=1)
    weeks = []
    current = start
    while current <= end:
        iso_year, iso_week, _ = current.isocalendar()
        label = f"{iso_year}-W{iso_week:02d}"
        if label not in weeks:
            weeks.append(label)
        current += timedelta(days=7 - current.weekday())  # 跳到下周一
    return weeks


# ============================================================
# Git 命令封装
# ============================================================


def git_cmd(repo_path, args):
    """
    在指定仓库执行 git 命令。
    返回 stdout 字符串（已 strip）。
    失败时返回 None。
    """
    cmd = ["git", "-C", str(repo_path)] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def git_config_user(repo_path):
    """
    读取仓库的 Git 用户信息。
    优先读取仓库级配置，不存在则回退到全局配置。
    返回 {"name": str, "email": str, "source": "local"|"global"}
    """
    # 尝试仓库级配置
    name = git_cmd(repo_path, ["config", "--local", "user.name"])
    email = git_cmd(repo_path, ["config", "--local", "user.email"])

    if name and email:
        return {"name": name, "email": email, "source": "local"}

    # 回退到全局配置
    global_name = git_cmd(repo_path, ["config", "user.name"])
    global_email = git_cmd(repo_path, ["config", "user.email"])

    return {
        "name": name or global_name or "",
        "email": email or global_email or "",
        "source": "global" if not (name and email) else "local",
    }


def is_git_repo(path):
    """检查路径是否为 Git 仓库（包含 .git 目录）"""
    git_dir = Path(path) / ".git"
    return git_dir.exists() and (git_dir.is_dir() or git_dir.is_file())


# ============================================================
# 输出路径计算
# ============================================================


def output_path_daily(config, date_str):
    """计算日报输出路径"""
    base = Path(config["output"]["vault_dir"]) / config["output"]["base_folder"]
    return base / config["output"]["daily_folder"] / f"{date_str}.md"


def output_path_weekly(config, week_label):
    """计算周报输出路径"""
    base = Path(config["output"]["vault_dir"]) / config["output"]["base_folder"]
    return base / config["output"]["weekly_folder"] / f"{week_label}.md"


def output_path_monthly(config, month_label):
    """计算月报输出路径"""
    base = Path(config["output"]["vault_dir"]) / config["output"]["base_folder"]
    return base / config["output"]["monthly_folder"] / f"{month_label}.md"


# ============================================================
# 工具函数
# ============================================================


def eprint(*args, **kwargs):
    """输出到 stderr"""
    print(*args, file=sys.stderr, **kwargs)


def json_output(data):
    """将数据以 JSON 格式输出到 stdout"""
    print(json.dumps(data, ensure_ascii=False, indent=2))
