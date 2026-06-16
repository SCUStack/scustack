# 川流课栈 Windows 启动脚本
# 用法: PowerShell 中执行 .\start.ps1
# 如果提示执行策略限制，先运行: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

function Log   { Write-Host "[$(Get-Date -Format HH:mm:ss)] $args" -ForegroundColor Cyan }
function Ok    { Write-Host "[OK]  $args" -ForegroundColor Green }
function Warn  { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Err   { Write-Host "[ERR]  $args" -ForegroundColor Red }

function Clear-Port {
    param([int]$Port)
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
    if (-not $conns) { return $true }
    $killed = $false
    foreach ($c in $conns) {
        $pid_val = $c.OwningProcess
        if ($pid_val -eq 0) { continue }
        $proc = Get-Process -Id $pid_val -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $pid_val -Force -ErrorAction SilentlyContinue
            Log "已停止 $($proc.ProcessName) (PID $pid_val) 释放端口 $Port"
            $killed = $true
        } else {
            Warn "端口 $Port 被 PID $pid_val 占用，但进程无法访问（可能为 WSL relay），尝试强制释放..."
            taskkill /F /PID $pid_val 2>$null | Out-Null
        }
    }
    if ($killed) { Start-Sleep -Seconds 2 }
    $still = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
    return -not $still
}

# ═══════════════════════════════════════════
# 0. Prerequisites
# ═══════════════════════════════════════════
Write-Host ""
Write-Host "═══════════════════════════════════════════"
Write-Host "  川流课栈 启动脚本 (Windows)"
Write-Host "═══════════════════════════════════════════"
Write-Host ""

$missing = $false
foreach ($cmd in @("docker", "python", "node", "pnpm")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) { Ok "$cmd 已安装" }
    else { Err "$cmd 未安装"; $missing = $true }
}
if ($missing) { Write-Host ""; Err "缺少必要工具，请先安装后再运行"; exit 1 }

# ═══════════════════════════════════════════
# 1. Docker daemon
# ═══════════════════════════════════════════
Log "检查 Docker daemon..."
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Log "Docker Desktop 未运行，正在启动..."
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Start-Process $dockerPath
        Log "等待 Docker daemon 就绪（最多 60s）..."
        $waited = 0
        do {
            Start-Sleep -Seconds 3
            $waited += 3
            docker info 2>&1 | Out-Null
        } while ($LASTEXITCODE -ne 0 -and $waited -lt 60)
        if ($LASTEXITCODE -ne 0) { Err "Docker 启动超时，请手动启动 Docker Desktop 后重试"; exit 1 }
    } else {
        Err "找不到 Docker Desktop，请确认安装路径"; exit 1
    }
}
Ok "Docker daemon 运行中"

# ═══════════════════════════════════════════
# 2. Port conflict check
# ═══════════════════════════════════════════
Log "检查端口占用..."
$ports = @{
    25432 = "PostgreSQL"
    26379 = "Redis"
    9200  = "Elasticsearch"
    8088  = "OnlyOffice"
    8000  = "FastAPI"
    3000  = "Nuxt"
}
$conflict = $false
foreach ($port in $ports.Keys) {
    $name = $ports[$port]
    $pids = (netstat -ano 2>$null | Select-String ":$port " | ForEach-Object { ($_ -split '\s+')[-1] } | Where-Object { $_ -ne "0" } | Sort-Object -Unique)
    if ($pids) {
        foreach ($pid_val in $pids) {
            $proc = Get-Process -Id $pid_val -ErrorAction SilentlyContinue
            if ($proc) { Warn "端口 $port ($name) 被 $($proc.ProcessName) (PID $pid_val) 占用" }
        }
        $conflict = $true
    }
}
if ($conflict) { Warn "存在端口冲突，请手动释放端口或在 docker-compose.yml 中修改映射端口" }

# ═══════════════════════════════════════════
# 3. Docker infrastructure
# ═══════════════════════════════════════════
Log "启动基础设施服务 (Docker)..."
docker compose up -d
if ($LASTEXITCODE -ne 0) { Err "Docker Compose 启动失败"; exit 1 }

Log "等待服务就绪 (最多 120s)..."

function Wait-Container {
    param($Container, $Timeout = 120)
    $elapsed = 0
    while ($elapsed -lt $Timeout) {
        $status = docker inspect -f '{{.State.Health.Status}}' $Container 2>$null
        if ($status -eq "healthy") { return $true }
        Start-Sleep -Seconds 2
        $elapsed += 2
    }
    return $false
}

$services = @(
    "scustack-postgres",
    "scustack-redis",
    "scustack-elasticsearch",
    "scustack-onlyoffice"
)
$allOk = $true
foreach ($svc in $services) {
    Write-Host -NoNewline "  $svc ".PadRight(40)
    if (Wait-Container $svc 120) { Write-Host "ready" -ForegroundColor Green }
    else { Write-Host "timeout" -ForegroundColor Red; $allOk = $false }
    Start-Sleep -Milliseconds 500
}
if (-not $allOk) { Err "部分服务启动超时，运行 docker compose ps 查看状态"; exit 1 }
Ok "基础设施全部就绪"

# ═══════════════════════════════════════════
# 4. Backend .env
# ═══════════════════════════════════════════
Log "配置后端环境..."
$envFile = Join-Path $ROOT "scustack-api\.env"
$envExample = Join-Path $ROOT "scustack-api\.env.example"
if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Ok ".env 已从 .env.example 创建"
} else {
    Ok ".env 已存在"
}

# ═══════════════════════════════════════════
# 5. Backend dependencies
# ═══════════════════════════════════════════
Log "安装后端依赖..."
$apiDir = Join-Path $ROOT "scustack-api"
Set-Location $apiDir

$hasDeps = $false
try { python -c "import fastapi, uvicorn, sqlalchemy, alembic" 2>$null; $hasDeps = $true } catch {}
if ($hasDeps) {
    Ok "Python 核心依赖已安装"
} else {
    Warn "正在安装 Python 依赖..."
    pip install -e ".[dev]" 2>$null
    if ($LASTEXITCODE -ne 0) {
        pip install fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic redis `
            "elasticsearch>=8.17.0,<9.0.0" pydantic pydantic-settings celery httpx `
            "python-jose[cryptography]" "passlib[bcrypt]" python-multipart oss2
    }
    Ok "Python 依赖安装完成"
}

# ═══════════════════════════════════════════
# 6. Database migration
# ═══════════════════════════════════════════
Log "运行数据库迁移..."
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { Err "数据库迁移失败"; exit 1 }
Ok "数据库迁移完成"

Set-Location $ROOT

# ═══════════════════════════════════════════
# 7. Frontend dependencies
# ═══════════════════════════════════════════
Log "检查前端依赖..."
$webModules = Join-Path $ROOT "scustack-web\node_modules"
$rootModules = Join-Path $ROOT "node_modules"
if ((Test-Path $webModules) -or (Test-Path $rootModules)) {
    Ok "node_modules 已存在"
} else {
    Warn "正在安装前端依赖..."
    pnpm install
    Ok "前端依赖安装完成"
}

# ═══════════════════════════════════════════
# 8. Start backend
# ═══════════════════════════════════════════
Log "清理端口 8000 上的残留进程..."
$portOk = Clear-Port 8000
if (-not $portOk) {
    Warn "端口 8000 无法释放（WSL relay 僵尸进程），将尝试端口 8001"
}
$API_PORT = if ($portOk) { 8000 } else { 8001 }

Log "清理 Python 缓存..."
Get-ChildItem -Path $apiDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Ok "Python 缓存已清理"

# Use current shell's python path so venv is inherited
$pythonPath = (Get-Command python).Source
Log "Python: $pythonPath"
Log "启动后端 (uvicorn :${API_PORT})..."
$apiProc = Start-Process -FilePath $pythonPath -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "$API_PORT" -PassThru -WindowStyle Hidden -WorkingDirectory $apiDir
Start-Sleep -Seconds 3

# Verify backend responds (use curl.exe, more reliable than Invoke-WebRequest in PS 5.1)
$backendOk = $false
for ($i = 0; $i -lt 10; $i++) {
    $result = curl.exe -s -o NUL -w "%{http_code}" http://localhost:${API_PORT}/api/v1/health 2>$null
    if ($result -eq "200") {
        $backendOk = $true
        break
    }
    Start-Sleep -Seconds 1
}

if ($backendOk) {
    Ok "后端已启动 -> http://localhost:${API_PORT}"
    Ok "API 文档    -> http://localhost:${API_PORT}/docs"
} else {
    Err "后端启动超时，请手动检查: cd scustack-api && uvicorn app.main:app --reload --port ${API_PORT}"
    Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# ═══════════════════════════════════════════
# 9. Start frontend
# ═══════════════════════════════════════════
Log "清理端口 3000 上的残留进程..."
Clear-Port 3000 | Out-Null

# Pass API port to frontend if we fell back to 8001
if ($API_PORT -ne 8000) {
    $env:NUXT_PUBLIC_API_BASE = "http://localhost:${API_PORT}"
    Warn "前端将连接后端端口 ${API_PORT}"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════"
Write-Host "  全部启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "  前端:  http://localhost:3000"
Write-Host "  后端:  http://localhost:${API_PORT}"
Write-Host "  API:   http://localhost:${API_PORT}/docs"
Write-Host ""
Write-Host "  按 Ctrl+C 停止所有服务"
Write-Host "═══════════════════════════════════════════"
Write-Host ""

# Cleanup on exit
function Stop-Backend {
    Write-Host ""
    Log "正在停止后端 (PID $($apiProc.Id))..."
    Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue
    Ok "后端已停止"
}
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue }

try {
    pnpm dev:web
} finally {
    Stop-Backend
}
