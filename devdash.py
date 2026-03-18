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
from pathlib import Path
from datetime import datetime

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
            print("代码统计模块 - 开发中...")
            # TODO: 阶段3实现

        elif args.command == 'todo':
            print("TODO管理模块 - 开发中...")
            # TODO: 阶段4实现

        elif args.command == 'log':
            if args.message:
                print(f"记录日志: {args.message}")
                # TODO: 阶段5实现
            elif args.today:
                print("今日日志:")
                # TODO: 阶段5实现
            elif args.week:
                print("最近7天日志:")
                # TODO: 阶段5实现
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
