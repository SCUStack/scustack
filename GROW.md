# 川大课栈 启动指南

## 环境要求

| 工具 | 最低版本 | 验证命令 |
|------|----------|----------|
| Docker Desktop | 任意 | `docker --version` |
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 9+ | `pnpm --version` |

**Windows 用户**：建议使用 PowerShell 或 Git Bash 终端。以下命令均以项目根目录为工作目录。

---

## 1. Docker 镜像源配置（中国大陆必做）

Docker Hub 在国内无法直连，需要配置镜像加速。执行以下步骤：

1. 打开 Docker Desktop → Settings → Docker Engine
2. 在 `"registry-mirrors"` 数组中添加可用镜像源，例如：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerhub.timeweb.cloud"
  ]
}
```

3. 点击 "Apply & Restart" 等待重启完成
4. 如果上述镜像不可用，可在百度搜索 "Docker 镜像加速器 2025" 找最新可用的

如果仅需单次拉取，也可以手动从镜像站拉取后打标签：

```bash
# 以 daocloud 为例
docker pull docker.m.daocloud.io/library/postgres:16
docker tag docker.m.daocloud.io/library/postgres:16 postgres:16

docker pull docker.m.daocloud.io/library/redis:7-alpine
docker tag docker.m.daocloud.io/library/redis:7-alpine redis:7-alpine

docker pull docker.m.daocloud.io/library/elasticsearch:8.17.0
docker tag docker.m.daocloud.io/library/elasticsearch:8.17.0 elasticsearch:8.17.0

docker pull docker.m.daocloud.io/onlyoffice/documentserver:8.2
docker tag docker.m.daocloud.io/onlyoffice/documentserver:8.2 onlyoffice/documentserver:8.2
```

---

## 2. 端口检查

项目依赖四个基础设施服务，各占用一个端口。启动前请确保以下端口未被其他进程占用：

| 服务 | 默认端口 | 可在哪里修改 |
|------|----------|-------------|
| PostgreSQL | 5432 → **25432** | `docker-compose.yml` + `.env` |
| Redis | 6379 → **26379** | `docker-compose.yml` + `.env` |
| Elasticsearch | 9200 | `docker-compose.yml` + `.env` |
| OnlyOffice | 8088 | `docker-compose.yml` |

> PostgreSQL 和 Redis 的对外端口已改为 25432/26379（原 5432/6379 容易被其他项目占用）。如需改回默认值，请同步修改 `docker-compose.yml` 和 `scustack-api/.env`。

检查端口占用：

```bash
# Windows PowerShell
netstat -ano | findstr "25432 26379 9200 8088"
```

如果端口被占用，可以 stop 掉冲突的容器：

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"  # 查看所有运行中的容器
docker stop <container-name>                         # 停掉冲突的容器
```

---

## 3. 启动基础设施服务

```bash
# 在项目根目录执行
docker compose up -d
```

等待所有容器健康检查通过：

```bash
docker compose ps
# 四个容器的 STATUS 列都显示 (healthy) 即就绪
```

如果 Elasticsearch 启动失败（通常是内存不足），在 `docker-compose.yml` 中将 `ES_JAVA_OPTS` 调整为 `-Xms256m -Xmx256m`。

---

## 4. 配置并启动后端

### 4.1 创建环境变量文件

```bash
cd scustack-api

# 从模板复制
cp .env.example .env
```

**重要**：`.env` 中的 `SCUSTACK_DB_PORT` 和 `SCUSTACK_REDIS_URL` 端口必须与 `docker-compose.yml` 中映射的宿主机端口一致。

当前默认配置（与 docker-compose.yml 匹配）：

```
SCUSTACK_DB_PORT=25432
SCUSTACK_REDIS_URL=redis://localhost:26379/0
```

### 4.2 安装依赖

```bash
# 在 scustack-api/ 目录下
pip install -e ".[dev]"
```

如果可编辑安装失败（setuptools 报 flat-layout 错误），改为直接安装：

```bash
pip install fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic redis \
  "elasticsearch>=8.17.0,<9.0.0" pydantic pydantic-settings celery httpx \
  "python-jose[cryptography]" "passlib[bcrypt]" python-multipart oss2
```

### 4.3 运行数据库迁移

```bash
python -m alembic upgrade head
```

看到 `Running upgrade ...` 系列日志即为成功。如果失败，检查：
- Docker PostgreSQL 容器是否在运行：`docker compose ps postgres`
- `.env` 中数据库连接信息是否正确

### 4.4 启动开发服务器

```bash
# 在 scustack-api/ 目录下
uvicorn app.main:app --reload --port 8000
```

验证：浏览器打开 [http://localhost:8000/docs](http://localhost:8000/docs)，应看到 Swagger API 文档页。

---

## 5. 启动前端

### 5.1 安装依赖

```bash
# 在项目根目录执行
pnpm install
```

### 5.2 启动开发服务器

```bash
# 同时启动后端 + 前端（在项目根目录）
pnpm dev
```

或者分别启动：

```bash
# 终端 1：后端
pnpm dev:api

# 终端 2：前端
pnpm dev:web
```

验证：浏览器打开 [http://localhost:3000](http://localhost:3000)，应看到川大课栈首页。

### 5.3 API 代理

前端 Nuxt 开发服务器的 API 代理指向 `http://localhost:8000`（在 `nuxt.config.ts` 的 `public.apiBase` 中配置）。如果后端在别的地址，修改对应配置即可。

---

## 6. 常用命令速查

```bash
# === Docker 基础设施 ===
docker compose up -d             # 启动所有服务
docker compose down              # 停止并删除容器（数据卷保留）
docker compose down -v           # 停止并删除容器 + 数据卷（重置数据库）
docker compose ps                # 查看容器状态
docker compose logs -f <service> # 查看某服务的日志

# === 后端 ===
cd scustack-api
python -m alembic upgrade head   # 执行迁移
python -m alembic downgrade -1   # 回滚最近一次迁移
python -m alembic revision --autogenerate -m "description"  # 生成新迁移
pytest                           # 运行测试
pytest --cov=app                 # 运行测试并输出覆盖率

# === 前端 ===
pnpm dev                         # 启动全栈开发
pnpm dev:web                     # 仅启动前端
pnpm lint                        # 代码检查
pnpm typecheck                   # TypeScript 类型检查
```

---

## 7. 已知问题

### OnlyOffice 启动慢
OnlyOffice 容器冷启动需要 30-60 秒，health check 有 `start_period: 30s` 等待。如果文档预览功能不可用，先确认该容器已 healthy。

### Docker Desktop 内存不足
四个服务建议分配至少 6GB 内存给 Docker Desktop。在 Settings → Resources 中调整 Memory 限制。

### Elasticsearch 权限错误
如果在 Linux 上遇到 `vm.max_map_count` 过低的问题：
```bash
sudo sysctl -w vm.max_map_count=262144
```

### 端口冲突
5432 和 6379 是常见端口，易与本地安装的 PostgreSQL/Redis 或其他项目容器冲突。本项目已将对外映射改为 25432 和 26379。如果仍然冲突，可自定义端口后同步修改以下两个文件：
- `docker-compose.yml` — 修改 `ports` 映射
- `scustack-api/.env` — 修改 `SCUSTACK_DB_PORT` 和 `SCUSTACK_REDIS_URL`
