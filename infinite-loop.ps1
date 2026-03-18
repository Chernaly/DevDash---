.# Claude Code 无限询问脚本 (Windows PowerShell)
# 使用方法: .\infinite-loop.ps1 -Task "你的任务描述" -MaxIterations 50

param(
    [Parameter(Mandatory=$true)]
    [string]$Task,
    
    [int]$MaxIterations = 50,
    [string]$CompletionMarker = "[TASK_COMPLETE]",
    [switch]$Verbose
)

$iteration = 0
$completed = $false
$historyFile = ".claude_infinite_history"

Write-Host "=== Claude Code 无限询问模式 ===" -ForegroundColor Cyan
Write-Host "任务: $Task" -ForegroundColor Yellow
Write-Host "最大迭代次数: $MaxIterations" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 初始化历史记录
if (Test-Path $historyFile) {
    Remove-Item $historyFile -Force
}

while ($iteration -lt $MaxIterations -and -not $completed) {
    $iteration++
    Write-Host "[$iteration/$MaxIterations] 正在执行任务..." -ForegroundColor Green
    
    # 构建提示词
    $prompt = $Task
    if ($iteration -gt 1) {
        $prompt = "继续执行以下任务（第 $iteration 轮）。检查上一轮结果，如未完成则继续：$Task`n`n如已完成所有目标，请回复 '$CompletionMarker'"
    }
    
    # 检查是否需要停止（通过文件标记）
    if (Test-Path ".stop_claude") {
        Write-Host "检测到停止标记，正在退出..." -ForegroundColor Red
        Remove-Item ".stop_claude" -Force
        break
    }
    
    # 显示提示（verbose模式）
    if ($Verbose) {
        Write-Host "提示词: $prompt" -ForegroundColor Gray
    }
    
    # 这里需要用户手动复制提示到Claude Code
    Write-Host "请复制以下提示词到Claude Code:" -ForegroundColor Cyan
    Write-Host "---" -ForegroundColor DarkGray
    Write-Host $prompt -ForegroundColor White
    Write-Host "---" -ForegroundColor DarkGray
    Write-Host ""
    
    # 等待用户确认
    $response = Read-Host "任务是否完成? (y=完成, n=继续, s=停止)"
    
    switch ($response.ToLower()) {
        "y" { 
            $completed = $true
            Write-Host "任务已完成！" -ForegroundColor Green
        }
        "s" {
            Write-Host "用户停止执行" -ForegroundColor Red
            exit 0
        }
        default {
            Write-Host "继续下一轮..." -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
}

if ($iteration -ge $MaxIterations) {
    Write-Host "达到最大迭代次数 ($MaxIterations)，自动停止" -ForegroundColor Yellow
}

Write-Host "总共执行了 $iteration 轮" -ForegroundColor Cyan
