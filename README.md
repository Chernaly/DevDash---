# DevDash - 开发者智能仪表盘

一个集成多种开发辅助功能的命令行工具，帮助开发者快速了解项目状态。

## 功能特性

- **Git 状态查看**: 显示当前分支、未提交文件、最近提交记录、远程同步状态
- **代码统计**: 统计文件数、代码行数、按类型统计、显示最大文件
- **TODO 管理**: 扫描代码中的 TODO/FIXME 注释，按优先级分类显示
- **开发日志**: 快速记录开发日志，查看今日或最近7天的日志
- **项目健康检查**: 综合检查项目状态，给出健康评分和改进建议

## 安装要求

- Python 3.6 或更高版本
- Windows PowerShell / Linux / macOS 终端

## 安装方法

将 `devdash.py` 复制到项目目录，或者添加到系统 PATH 中。

也可以创建别名（alias）：

**Windows PowerShell:**
```powershell
Set-Alias devdash "C:\path\to\devdash.py"
```

**Linux/macOS:**
```bash
alias devdash='python3 /path/to/devdash.py'
```

## 使用方法

### 显示项目概览
```bash
python devdash.py
```

### Git 状态
```bash
python devdash.py git
```

显示内容：
- 当前分支名称
- 未提交文件统计
- 最近3条提交记录
- 远程同步状态

### 代码统计
```bash
python devdash.py stats
```

显示内容：
- 总文件数
- 总代码行数
- 按文件类型统计
- 最大的5个文件

### TODO 管理
```bash
# 显示所有 TODO
python devdash.py todo

# 按文件过滤
python devdash.py todo --file test.py

# 按优先级过滤
python devdash.py todo --priority high
```

支持的注释格式：
- `# TODO: 任务描述`
- `# TODO:high 高优先级任务`
- `# FIXME: 需要修复的问题`
- `# XXX: 需要注意的代码`
- `# HACK: 临时解决方案`

### 开发日志
```bash
# 记录日志
python devdash.py log "完成用户登录功能"

# 显示今日日志
python devdash.py log --today

# 显示最近7天日志
python devdash.py log --week
```

日志保存在 `.devdash/log.md` 文件中。

### 项目健康检查
```bash
python devdash.py health
```

检查项目：
- 是否有未提交的更改
- 是否有未推送的提交
- 是否有大型文件（>1MB）
- TODO 数量是否正常
- 给出健康评分和改进建议

## 配置文件

DevDash 支持配置文件 `.devdash/config.json`，可以自定义以下选项：

```json
{
  "exclude_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv", ".devdash"],
  "large_file_threshold_mb": 1.0,
  "max_recent_commits": 3,
  "todo_priorities": ["high", "medium", "low"]
}
```

## 示例输出

### 项目概览
```
============================================================
  DevDash - 开发者智能仪表盘 v1.0.0
============================================================

📁 当前目录: C:\Projects\myapp

📍 Git 分支: main
✅ 工作区干净

📊 代码统计:
  • 文件数: 45
  • 代码行: 3,248

📋 TODO 状态:
  • 总计: 8 个 TODO

💚 健康评分: 95/100

------------------------------------------------------------
可用的命令:
  devdash git     - 查看Git状态
  devdash stats   - 查看代码统计
  devdash todo    - 查看TODO列表
  devdash log     - 管理开发日志
  devdash health  - 项目健康检查

使用 devdash --help 查看详细帮助
============================================================
```

## 技术特点

- 使用 Python 标准库开发，无外部依赖
- 支持 UTF-8 编码，正确处理中文
- 支持 Windows PowerShell 环境
- 可配置、可扩展

## 开发计划

- [ ] 支持更多 Git 操作
- [ ] 添加项目模板功能
- [ ] 集成代码质量检查
- [ ] 支持多项目管理

## 许可证

MIT License

## 作者

DevDash Team