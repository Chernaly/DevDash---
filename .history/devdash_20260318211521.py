#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevDash - 开发者智能仪表盘
集成多种开发辅助功能的命令行工具
"""

import sys
import argparse
import io
import subprocess
import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


VERSION = "1.0.0"


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='devdash',
        description='开发者智能仪表盘 - 集成多种开发辅助功能',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  devdash                    显示项目概览
  devdash git               显示Git状态
  devdash stats             显示代码统计
  devdash todo              显示TODO列表
  devdash log "修复了bug"   记录日志
  devdash log --today       显示今日日志
  devdash health            项目健康检查
  devdash --version         显示版本信息
        '''
    )

    parser.add_argument('--version', '-v', action='version', version=f'%(prog)s {VERSION}')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # git 命令
    subparsers.add_parser('git', help='显示Git状态信息')

    # stats 命令
    subparsers.add_parser('stats', help='显示代码统计信息')

    # todo 命令
    todo_parser = subparsers.add_parser('todo', help='显示TODO列表')
    todo_parser.add_argument('--file', '-f', help='按文件过滤')
    todo_parser.add_argument('--priority', '-p', choices=['high', 'medium', 'low'],
                            help='按优先级过滤')

    # log 命令
    log_parser = subparsers.add_parser('log', help='开发日志管理')
    log_parser.add_argument('message', nargs='?', help='日志内容')
    log_parser.add_argument('--today', action='store_true', help='显示今日日志')
    log_parser.add_argument('--week', action='store_true', help='显示最近7天日志')

    # health 命令
    subparsers.add_parser('health', help='项目健康检查')

    return parser


def show_overview():
    """显示项目概览"""
    print("=" * 60)
    print("  DevDash - 开发者智能仪表盘")
    print("=" * 60)
    print(f"\n当前目录: {Path.cwd()}")
    print("\n可用的命令:")
    print("  devdash git     - 查看Git状态")
    print("  devdash stats   - 查看代码统计")
    print("  devdash todo    - 查看TODO列表")
    print("  devdash log     - 管理开发日志")
    print("  devdash health  - 项目健康检查")
    print("\n使用 --help 查看详细帮助信息")


def run_git_command(cmd):
    """执行git命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1


def is_git_repo():
    """检查当前目录是否为Git仓库"""
    _, code = run_git_command('git rev-parse --git-dir')
    return code == 0


def get_current_branch():
    """获取当前分支名"""
    output, code = run_git_command('git branch --show-current')
    if code == 0 and output:
        return output
    return "未知"


def get_uncommitted_count():
    """获取未提交文件数量"""
    # 未暂存的修改
    output1, _ = run_git_command('git diff --name-only')
    unstaged = len([f for f in output1.split('\n') if f])

    # 已暂存的修改
    output2, _ = run_git_command('git diff --cached --name-only')
    staged = len([f for f in output2.split('\n') if f])

    # 未跟踪的文件
    output3, _ = run_git_command('git ls-files --others --exclude-standard')
    untracked = len([f for f in output3.split('\n') if f])

    return unstaged, staged, untracked


def get_recent_commits(count=3):
    """获取最近的提交记录"""
    cmd = f'git log -{count} --pretty=format:"%h|%ad|%s" --date=short'
    output, code = run_git_command(cmd)

    if code != 0 or not output:
        return []

    commits = []
    for line in output.split('\n'):
        if line.strip() and '|' in line:
            parts = line.split('|', 2)
            if len(parts) == 3:
                commits.append({
                    'hash': parts[0],
                    'date': parts[1],
                    'message': parts[2]
                })
    return commits


def get_sync_status():
    """获取与远程分支的同步状态"""
    # 先获取远程信息
    run_git_command('git remote update')

    branch = get_current_branch()
    if branch == "未知":
        return "无法获取分支信息"

    # 获取本地和远程的差异
    ahead_cmd = f'git rev-list --count origin/{branch}..HEAD 2>nul'
    behind_cmd = f'git rev-list --count HEAD..origin/{branch} 2>nul'

    ahead_output, ahead_code = run_git_command(ahead_cmd)
    behind_output, behind_code = run_git_command(behind_cmd)

    if ahead_code != 0 or behind_code != 0:
        return "无法获取同步状态（可能没有远程分支）"

    try:
        ahead = int(ahead_output) if ahead_output else 0
        behind = int(behind_output) if behind_output else 0

        if ahead == 0 and behind == 0:
            return "已同步"
        elif ahead > 0 and behind > 0:
            return f"分歧 (领先 {ahead} 个提交，落后 {behind} 个提交)"
        elif ahead > 0:
            return f"领先 {ahead} 个提交待推送"
        else:
            return f"落后 {behind} 个提交待拉取"
    except ValueError:
        return "无法解析同步状态"


def show_git_status():
    """显示Git状态"""
    if not is_git_repo():
        print("⚠️  当前目录不是Git仓库")
        return

    print("\n" + "=" * 60)
    print("  Git 状态")
    print("=" * 60)

    # 当前分支
    branch = get_current_branch()
    print(f"\n📍 当前分支: {branch}")

    # 未提交文件
    unstaged, staged, untracked = get_uncommitted_count()
    total = unstaged + staged + untracked

    print(f"\n📝 未提交文件:")
    if total == 0:
        print("  ✅ 工作区干净")
    else:
        if unstaged > 0:
            print(f"  📄 未暂存的修改: {unstaged} 个文件")
        if staged > 0:
            print(f"  ✓  已暂存的修改: {staged} 个文件")
        if untracked > 0:
            print(f"  ❓ 未跟踪的文件: {untracked} 个文件")
        print(f"  总计: {total} 个文件")

    # 最近提交
    print(f"\n🕐 最近 {3} 条提交:")
    commits = get_recent_commits(3)
    if commits:
        for i, commit in enumerate(commits, 1):
            print(f"  {i}. [{commit['hash']}] {commit['date']} - {commit['message'][:50]}")
    else:
        print("  无提交记录")

    # 同步状态
    print(f"\n🔄 远程同步状态:")
    sync_status = get_sync_status()
    print(f"  {sync_status}")

    print("\n" + "=" * 60)


def get_file_stats(filepath):
    """获取文件行数"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except:
        return 0


def get_all_files():
    """获取所有文件（排除隐藏文件和特定目录）"""
    exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.devdash'}
    files = []

    for root, dirs, filenames in os.walk('.'):
        # 过滤掉排除的目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in exclude_dirs]

        for filename in filenames:
            if filename.startswith('.'):
                continue
            filepath = os.path.join(root, filename)
            files.append(filepath)

    return files


def get_file_extension(filepath):
    """获取文件扩展名"""
    _, ext = os.path.splitext(filepath)
    return ext.lower() if ext else 'no_extension'


def show_code_stats():
    """显示代码统计"""
    print("\n" + "=" * 60)
    print("  代码统计")
    print("=" * 60)

    files = get_all_files()

    # 总文件数
    print(f"\n📊 总文件数: {len(files)}")

    # 统计各类型文件
    ext_stats = defaultdict(lambda: {'count': 0, 'lines': 0})
    total_lines = 0
    file_sizes = []

    for filepath in files:
        try:
            # 获取文件信息
            ext = get_file_extension(filepath)
            lines = get_file_stats(filepath)
            size = os.path.getsize(filepath)

            ext_stats[ext]['count'] += 1
            ext_stats[ext]['lines'] += lines
            total_lines += lines

            file_sizes.append((filepath, size))
        except Exception:
            continue

    # 总代码行数
    print(f"📏 总代码行数: {total_lines:,}")

    # 按文件类型统计
    print(f"\n📂 按文件类型统计:")
    sorted_stats = sorted(ext_stats.items(), key=lambda x: x[1]['count'], reverse=True)

    # 只显示前10种类型
    for ext, stats in sorted_stats[:10]:
        ext_display = ext if ext else '(无扩展名)'
        print(f"  {ext_display:15} {stats['count']:4} 个文件  {stats['lines']:6,} 行")

    if len(sorted_stats) > 10:
        print(f"  ... 还有 {len(sorted_stats) - 10} 种其他文件类型")

    # 最大的5个文件
    print(f"\n heavyweight 最大的 5 个文件:")
    file_sizes.sort(key=lambda x: x[1], reverse=True)

    for i, (filepath, size) in enumerate(file_sizes[:5], 1):
        size_kb = size / 1024
        lines = get_file_stats(filepath)
        # 简化显示路径
        display_path = filepath.lstrip('./\\')
        if len(display_path) > 45:
            display_path = display_path[:42] + '...'
        print(f"  {i}. {display_path:45} {size_kb:7.1f} KB  ({lines:,} 行)")

    print("\n" + "=" * 60)


def scan_todos(file_filter=None, priority_filter=None):
    """扫描代码中的TODO/FIXME注释"""
    todos = []
    exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.devdash'}

    # TODO模式：匹配注释中的 TODO, FIXME, XXX, HACK
    # Python/Shell: # TODO, # FIXME
    # JavaScript/C: // TODO, /* TODO */
    # 支持优先级标记：TODO:high, TODO:medium, TODO:low
    todo_patterns = [
        r'(?:^|\s)(#|//|/\*|\*)\s*(TODO|FIXME|XXX|HACK)(?:\:(low|medium|high))?\s*:?\s*(.+?)(?:\*/|\s*$)',
    ]

    for root, dirs, filenames in os.walk('.'):
        # 过滤掉排除的目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in exclude_dirs]

        for filename in filenames:
            if filename.startswith('.'):
                continue

            filepath = os.path.join(root, filename)

            # 文件过滤
            if file_filter and file_filter.lower() not in filepath.lower():
                continue

            # 只扫描文本文件
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        original_line = line
                        line = line.strip()

                        for pattern in todo_patterns:
                            match = re.search(pattern, line, re.IGNORECASE)
                            if match:
                                todo_type = match.group(2).upper()
                                priority = match.group(3).lower() if match.group(3) else 'medium'
                                message = match.group(4).strip() if match.group(4) else '无描述'

                                # 优先级过滤
                                if priority_filter and priority != priority_filter:
                                    continue

                                todos.append({
                                    'file': filepath.lstrip('./\\'),
                                    'line': line_num,
                                    'type': todo_type,
                                    'priority': priority,
                                    'message': message
                                })
                                break  # 只匹配第一个模式
            except Exception:
                continue

    return todos


def show_todo_list(file_filter=None, priority_filter=None):
    """显示TODO列表"""
    print("\n" + "=" * 60)
    print("  TODO 列表")
    print("=" * 60)

    todos = scan_todos(file_filter, priority_filter)

    if not todos:
        print("\n✅ 没有找到 TODO/FIXME 注释")
        return

    # 按优先级排序
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    todos.sort(key=lambda x: (priority_order[x['priority']], x['file']))

    # 统计信息
    print(f"\n📋 共找到 {len(todos)} 个 TODO/FIXME:")

    stats = {'high': 0, 'medium': 0, 'low': 0}
    type_stats = {}

    for todo in todos:
        stats[todo['priority']] += 1
        type_stats[todo['type']] = type_stats.get(todo['type'], 0) + 1

    print(f"\n按优先级:")
    if stats['high'] > 0:
        print(f"  🔴 High:   {stats['high']}")
    if stats['medium'] > 0:
        print(f"  🟡 Medium: {stats['medium']}")
    if stats['low'] > 0:
        print(f"  🟢 Low:    {stats['low']}")

    print(f"\n按类型:")
    for todo_type, count in sorted(type_stats.items()):
        print(f"  {todo_type}: {count}")

    # 显示详细列表
    print(f"\n详细列表:")

    current_file = None
    for todo in todos:
        # 分隔不同文件
        if current_file != todo['file']:
            current_file = todo['file']
            print(f"\n📄 {current_file}")

        # 优先级图标
        priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        icon = priority_icons[todo['priority']]

        # 截断长消息
        message = todo['message']
        if len(message) > 60:
            message = message[:57] + '...'

        print(f"  {icon} L{todo['line']:4d} [{todo['type']:4s}] {message}")

    print("\n" + "=" * 60)


def get_log_file_path():
    """获取日志文件路径"""
    log_dir = Path('.devdash')
    log_dir.mkdir(exist_ok=True)
    return log_dir / 'log.md'


def add_log_entry(message):
    """添加日志条目"""
    log_file = get_log_file_path()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')

    entry = f"\n## [{timestamp}]\n{message}\n"

    # 如果文件不存在或不是今天的第一条日志，添加日期标题
    if not log_file.exists():
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"# DevDash 开发日志\n\n# {date_str}\n")
            f.write(entry)
    else:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查今天是否已有日志
        if f"# {date_str}" not in content:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n# {date_str}\n")
                f.write(entry)
        else:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(entry)

    print(f"✅ 日志已记录: {timestamp}")


def show_today_log():
    """显示今日日志"""
    log_file = get_log_file_path()
    date_str = datetime.now().strftime('%Y-%m-%d')

    if not log_file.exists():
        print("\n📭 暂无日志记录")
        return

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取今天的日志
    if f"# {date_str}" not in content:
        print("\n📭 今天还没有记录日志")
        return

    print("\n" + "=" * 60)
    print(f"  今日日志 ({date_str})")
    print("=" * 60)

    # 找到今天的日志部分
    lines = content.split('\n')
    in_today = False
    entry_count = 0

    for line in lines:
        if line.startswith(f"# {date_str}"):
            in_today = True
            continue
        elif in_today and line.startswith('# ') and not line.startswith('# ' + date_str):
            break

        if in_today and line.startswith('## ['):
            entry_count += 1

        if in_today and line.strip():
            print(line)

    if entry_count == 0:
        print("\n  (暂无条目)")

    print(f"\n共 {entry_count} 条记录")
    print("=" * 60)


def show_week_log():
    """显示最近7天的日志"""
    log_file = get_log_file_path()

    if not log_file.exists():
        print("\n📭 暂无日志记录")
        return

    print("\n" + "=" * 60)
    print("  最近7天日志摘要")
    print("=" * 60)

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按日期分割日志
    import re
    date_pattern = r'# (\d{4}-\d{2}-\d{2})'
    dates = re.findall(date_pattern, content)

    # 只显示最近7天
    recent_dates = dates[-7:] if len(dates) > 7 else dates

    if not recent_dates:
        print("\n📭 暂无日志记录")
        return

    for date in recent_dates:
        print(f"\n## {date}")

        # 提取该日期的日志
        pattern = rf'# {date}\n(.*?)(?=# \d{{4}}-\d{{2}}-\d{{2}}|$)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            day_log = match.group(1)
            # 统计条目数
            entries = re.findall(r'## \[', day_log)
            print(f"  {len(entries)} 条记录")

            # 显示前3条日志的摘要
            lines = day_log.strip().split('\n')
            shown = 0
            for line in lines:
                if line.startswith('## ['):
                    if shown < 3:
                        # 提取时间戳
                        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
                        if timestamp_match:
                            print(f"  - {timestamp_match.group(1)}")
                        shown += 1
                elif line.strip() and shown <= 3 and not line.startswith('#'):
                    if shown > 0:
                        summary = line[:70] + '...' if len(line) > 70 else line
                        print(f"    {summary}")

            if len(entries) > 3:
                print(f"  ... 还有 {len(entries) - 3} 条记录")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    # 如果没有指定命令，显示概览
    if not args.command:
        show_overview()
        return 0

    # 根据命令执行对应功能
    try:
        if args.command == 'git':
            show_git_status()

        elif args.command == 'stats':
            show_code_stats()

        elif args.command == 'todo':
            show_todo_list(
                file_filter=args.file if hasattr(args, 'file') else None,
                priority_filter=args.priority if hasattr(args, 'priority') else None
            )

        elif args.command == 'log':
            if args.message:
                add_log_entry(args.message)
            elif args.today:
                show_today_log()
            elif args.week:
                show_week_log()
            else:
                print("请提供日志内容或使用 --today/--week 选项")

        elif args.command == 'health':
            print("项目健康检查 - 开发中...")
            # TODO: 阶段6实现

    except KeyboardInterrupt:
        print("\n操作已取消")
        return 1
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
