# 论文智能分析系统 - 一键启动脚本
# Paper Auto Summarize - Quick Start Script

$ErrorActionPreference = "Stop"

# 切换到脚本所在目录（支持双击运行）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  论文智能分析系统 - 启动中..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在项目根目录
if (-not (Test-Path "run.py")) {
    Write-Host "[ERROR] 请将脚本放在项目根目录" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 检查 uv 是否可用
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    Write-Host "[ERROR] 未找到 uv 命令。请先安装: https://docs.astral.sh/uv/" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 检查 npm 是否可用
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCmd) {
    Write-Host "[ERROR] 未找到 npm 命令。请先安装 Node.js: https://nodejs.org/" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 检查 .env 文件
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] 未找到 .env 文件，正在从模板创建..." -ForegroundColor Yellow
    if (Test-Path "deploy/.env.example") {
        Copy-Item "deploy/.env.example" ".env"
        Write-Host "  已创建 .env，请编辑并填入 DEEPSEEK_API_KEY" -ForegroundColor Yellow
    }
}

# 安装 Python 依赖（uv 会自动处理虚拟环境）
Write-Host "[1/5] 检查 Python 依赖..." -ForegroundColor Gray
uv sync --quiet 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  uv sync 失败，尝试 pip install..." -ForegroundColor Yellow
    uv pip install -r requirements.txt --quiet
}

# 检查前端依赖
if (-not (Test-Path "frontend/node_modules")) {
    Write-Host "[2/5] 安装前端依赖..." -ForegroundColor Gray
    Push-Location frontend
    npm install --silent
    Pop-Location
    Write-Host "  前端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "[2/5] 前端依赖已就绪" -ForegroundColor Gray
}

# 首次运行初始化数据库
if (-not (Test-Path "paper_analysis.db")) {
    Write-Host "[3/5] 首次运行，初始化数据库..." -ForegroundColor Yellow
    uv run python scripts/init_default_themes.py 2>$null
    uv run python scripts/create_test_user.py 2>$null
    Write-Host "  数据库初始化完成" -ForegroundColor Green
} else {
    Write-Host "[3/5] 数据库已存在" -ForegroundColor Gray
}

Write-Host ""
Write-Host "正在启动服务..." -ForegroundColor Cyan
Write-Host ""

# 启动后端 API — 用 cmd /k 在新窗口中运行（确保 PATH 正确继承）
Write-Host "[4/5] 启动后端 API (端口 8000)..." -ForegroundColor Green
$backendProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/k", "title Paper-Backend && cd /d `"$ScriptDir`" && uv run python run.py api" `
    -PassThru

# 等待后端就绪
Start-Sleep -Seconds 3

# 启动前端
Write-Host "[5/5] 启动前端服务 (端口 4321)..." -ForegroundColor Green
$frontendProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/k", "title Paper-Frontend && cd /d `"$ScriptDir\frontend`" && npm run dev" `
    -PassThru

# 等待前端就绪
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  前端界面: " -NoNewline; Write-Host "http://localhost:4321" -ForegroundColor Cyan
Write-Host "  API 文档: " -NoNewline; Write-Host "http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  测试账号: test@huginn.com / test123" -ForegroundColor Yellow
Write-Host ""

# 打开浏览器
Start-Process "http://localhost:4321"

Write-Host "按回车键停止所有服务..." -ForegroundColor Gray
Read-Host

# 停止服务
Write-Host "正在停止服务..." -ForegroundColor Yellow
if ($backendProc -and -not $backendProc.HasExited) {
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    # 同时清理 uvicorn 子进程
    Get-Process -Name "python" -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -eq "" } |
        Stop-Process -Force -ErrorAction SilentlyContinue
}
if ($frontendProc -and -not $frontendProc.HasExited) {
    Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue
    # 清理 node 子进程
    Get-Process -Name "node" -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -eq "" } |
        Stop-Process -Force -ErrorAction SilentlyContinue
}
Write-Host "服务已停止" -ForegroundColor Green
