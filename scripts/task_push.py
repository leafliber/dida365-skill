#!/usr/bin/env python3
"""
Dida365 任务推送脚本

用于定时任务调用，输出格式化的今日任务和过期任务。

用法:
    python3 task_push.py
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

# 优先级图标
PRIORITY_EMOJI = {5: "🔴", 3: "🟡", 1: "🟢", 0: "⚪"}


def get_tasks():
    """获取未完成任务列表"""
    script_dir = Path(__file__).parent
    result = subprocess.run(
        ["python3", str(script_dir / "dida_api.py"), "filter-tasks", "--status", "0"],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    lines = output.strip().split("\n")

    # 找到 JSON 开始位置
    json_start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("{") or line.strip().startswith("["):
            json_start = i
            break

    if json_start < 0:
        return []

    json_text = "\n".join(lines[json_start:])
    return json.loads(json_text)


def parse_datetime(dt_str):
    """解析 ISO 格式日期时间"""
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.astimezone(BEIJING_TZ)
    except Exception:
        return None


def format_task_time(task):
    """
    格式化任务时间显示

    规则:
    - 全天任务 → "全天"
    - 时间段任务（startDate ≠ dueDate）→ "开始-结束"
    - 单时间点任务 → 只显示时间
    """
    if task.get("isAllDay"):
        return "全天"

    start_dt = parse_datetime(task.get("startDate"))
    due_dt = parse_datetime(task.get("dueDate"))

    if not due_dt:
        return "无截止时间"

    if not start_dt:
        return due_dt.strftime("%H:%M")

    # 判断是否为时间段
    if start_dt != due_dt:
        return f"{start_dt.strftime('%H:%M')}-{due_dt.strftime('%H:%M')}"
    else:
        return due_dt.strftime("%H:%M")


def classify_tasks(tasks):
    """分类任务：今日待办、过期任务"""
    today = datetime.now(BEIJING_TZ).date()

    today_tasks = []
    overdue_tasks = []

    for task in tasks:
        due_dt = parse_datetime(task.get("dueDate"))
        if not due_dt:
            continue

        due_date = due_dt.date()

        task_info = {
            "title": task.get("title", "无标题"),
            "time_str": format_task_time(task),
            "priority": task.get("priority", 0),
            "tags": task.get("tags", []),
            "due_dt": due_dt,
            "due_date": due_date,
        }

        if due_date == today:
            today_tasks.append(task_info)
        elif due_date < today:
            overdue_tasks.append(task_info)

    return today_tasks, overdue_tasks


def print_task_list(tasks, show_overdue_days=False, today=None):
    """打印任务列表"""
    if not tasks:
        return

    # 按优先级排序（高→低）
    sorted_tasks = sorted(tasks, key=lambda t: -t["priority"])

    for i, t in enumerate(sorted_tasks, 1):
        emoji = PRIORITY_EMOJI.get(t["priority"], "⚪")
        tags_str = f" [{', '.join(t['tags'])}]" if t["tags"] else ""

        line = f"{i}. **{emoji} {t['title']}**{tags_str} ⏰ {t['time_str']}"

        if show_overdue_days and today:
            days_overdue = (today - t["due_date"]).days
            if days_overdue == 1:
                line += " *(昨天过期)*"
            else:
                line += f" *(过期{days_overdue}天)*"

        print(line)


def main():
    """主函数"""
    today = datetime.now(BEIJING_TZ).date()

    print("## 📋 任务推送")
    print()
    print(f"### 📅 今天待办任务 ({today.strftime('%Y-%m-%d')})")
    print()

    try:
        tasks = get_tasks()
        today_tasks, overdue_tasks = classify_tasks(tasks)

        if today_tasks:
            print_task_list(today_tasks)
        else:
            print("✅ 今天没有待办任务")

        print()
        print("---")
        print()
        print("### ⚠️ 过期任务")
        print()

        if overdue_tasks:
            print_task_list(overdue_tasks, show_overdue_days=True, today=today)
        else:
            print("✅ 没有过期任务")

        print()
        print("---")
        print()
        print("**汇总：**")
        print(f"- 今日待办：**{len(today_tasks)}** 项")
        print(f"- 过期任务：**{len(overdue_tasks)}** 项")

    except Exception as e:
        print(f"❌ 获取任务失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()