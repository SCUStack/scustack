#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; }

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ── 0. Prerequisites check ──────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "  川大课栈 启动脚本"
echo "═══════════════════════════════════════════"
echo ""

missing=0
for cmd in docker python node pnpm; do
    if command -v "$cmd" &>/dev/null; then
        ok "$cmd 已安装"
    else
        err "$cmd 未安装"
        missing=1
    fi
done
if [ "$missing" -ne 0 ]; then
    echo ""
    err "缺少必要工具，请先安装后再运行"
    exit 1
fi

# ── 1. Docker daemon ────────────────────────────────────────────────────────
log "检查 Docker daemon..."
if ! docker info &>/dev/null; then
    err "Docker daemon 未运行。请启动 Docker Desktop 后重试"
    exit 1
fi
ok "Docker daemon 运行中"

# ── 2. Port conflict check ──────────────────────────────────────────────────
log "检查端口占用..."

check_port() {
    local port=$1 name=$2
    # Windows: use netstat; Linux/Mac: use lsof or ss
    if command -v netstat &>/dev/null; then
        if netstat -ano 2>/dev/null | grep -q ":$port "; then
            warn "端口 $port ($name) 已被占用"
            return 1
        fi
    elif command -v ss &>/dev/null; then
        if ss -tlnp 2>/dev/null | grep -q ":$port "; then
            warn "端口 $port ($name) 已被占用"
            return 1
        fi
    fi
    return 0
}

CONFLICT=0
for pair in "25432:PostgreSQL" "26379:Redis" "9200:Elasticsearch" "8088:OnlyOffice" "8000:FastAPI" "3000:Nuxt"; do
    port="${pair%%:*}"
    name="${pair##*:}"
    if ! check_port "$port" "$name"; then
        CONFLICT=1
    fi
done
if [ "$CONFLICT" -ne 0 ]; then
    warn "存在端口冲突，请手动释放端口或在 docker-compose.yml 中修改映射端口"
fi

# ── 3. Docker infrastructure ────────────────────────────────────────────────
log "启动基础设施服务 (Docker)..."
docker compose up -d

log "等待服务就绪 (最多 120s)..."

wait_container() {
    local container=$1 timeout=${2:-120}
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        local status
        status=$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "missing")
        case "$status" in
            healthy) return 0 ;;
            missing)
                # May still be creating
                sleep 2
                elapsed=$((elapsed + 2))
                ;;
            *)
                sleep 2
                elapsed=$((elapsed + 2))
                ;;
        esac
    done
    return 1
}

ALL_OK=true
for svc in scustack-postgres scustack-redis scustack-elasticsearch scustack-onlyoffice; do
    printf "  %-30s " "$svc"
    if wait_container "$svc" 120; then
        echo -e "${GREEN}ready${NC}"
    else
        echo -e "${RED}timeout${NC}"
        ALL_OK=false
    fi
    sleep 1
done

if [ "$ALL_OK" = false ]; then
    err "部分服务启动超时，运行 docker compose ps 查看状态"
    exit 1
fi
ok "基础设施全部就绪"

# ── 4. Backend .env ─────────────────────────────────────────────────────────
log "配置后端环境..."
ENV_FILE="$ROOT/scustack-api/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$ROOT/scustack-api/.env.example" "$ENV_FILE"
    ok ".env 已从 .env.example 创建"
else
    ok ".env 已存在"
fi

# ── 5. Backend dependencies ─────────────────────────────────────────────────
log "安装后端依赖..."
cd "$ROOT/scustack-api"

# Check if key deps are present
if python -c "import fastapi, uvicorn, sqlalchemy, alembic" 2>/dev/null; then
    ok "Python 核心依赖已安装"
else
    warn "正在安装 Python 依赖..."
    pip install -e ".[dev]" 2>/dev/null || pip install fastapi "uvicorn[standard]" \
        "sqlalchemy[asyncio]" asyncpg alembic redis "elasticsearch>=8.17.0,<9.0.0" \
        pydantic pydantic-settings celery httpx "python-jose[cryptography]" \
        "passlib[bcrypt]" python-multipart oss2
    ok "Python 依赖安装完成"
fi

# ── 6. Database migration ───────────────────────────────────────────────────
log "运行数据库迁移..."
python -m alembic upgrade head
ok "数据库迁移完成"

# ── 7. Start backend ────────────────────────────────────────────────────────
log "启动后端 (uvicorn :8000)..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 2

if kill -0 "$BACKEND_PID" 2>/dev/null; then
    ok "后端已启动 → http://localhost:8000"
    ok "API 文档 → http://localhost:8000/docs"
else
    err "后端启动失败，检查上方错误信息"
    exit 1
fi

cd "$ROOT"

# ── 8. Frontend dependencies ────────────────────────────────────────────────
log "检查前端依赖..."
if [ -d "$ROOT/scustack-web/node_modules" ] || [ -d "$ROOT/node_modules" ]; then
    ok "node_modules 已存在"
else
    warn "正在安装前端依赖..."
    pnpm install
    ok "前端依赖安装完成"
fi

# ── 9. Start frontend ───────────────────────────────────────────────────────
log "启动前端 (Nuxt :3000)..."
echo ""
echo "═══════════════════════════════════════════"
echo -e "  ${GREEN}全部启动完成！${NC}"
echo ""
echo "  前端:  http://localhost:3000"
echo "  后端:  http://localhost:8000"
echo "  API:   http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "═══════════════════════════════════════════"
echo ""

# Trap Ctrl+C to clean up background uvicorn
cleanup() {
    echo ""
    log "正在停止服务..."
    kill "$BACKEND_PID" 2>/dev/null || true
    ok "后端已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM

pnpm dev:web
