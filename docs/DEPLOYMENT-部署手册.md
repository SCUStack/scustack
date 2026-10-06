# Production Deployment Runbook

| 字段 | 内容 |
|---|---|
| Type | `deployment` |
| Status | `active` |
| Owner | `team` |
| Last Updated | `2026-06-19` |
| Source of Truth | `yes` |
| Scope | 低预算单机 MVP 的生产部署、环境变量、验证与回滚说明。 |

> 本文是当前可执行的部署主文档，默认面向 `¥400` 预算的单机上线方案，不覆盖多机高可用生产集群。

## 1. Infrastructure

Recommended MVP baseline for the current codebase and a first-year budget around `¥400`:

- `1 x lightweight cloud server` with `2C2G`, `40-50GB SSD`, `3-4Mbps`
- `1 x PostgreSQL 16` running on the same host via Docker
- `1 x Redis 7` running on the same host via Docker
- `1 x external LFS service` for uploads and downloads
- `1 x Elasticsearch 8` running via the production Compose stack (required by the API and worker)
- OnlyOffice is not started in the MVP; the production Compose service remains development-profile only and publishes no port
- `0 x RDS / CDN / SLB` in MVP

Recommended purchase path:

- Primary: Alibaba Cloud Lightweight Application Server, if an annual promo in the `¥99-199` range is available
- Backup: Tencent Cloud Lighthouse, if you have a student/campus offer or a short-term promo
- File storage: the verified LFS service configured through `SCUSTACK_LFS_*`

Official links:

- Alibaba Cloud Lightweight Application Server: https://www.aliyun.com/product/swas
- Alibaba Cloud ECS promo page: https://cn.aliyun.com/daily-act/ecs/activity_selection%20?from_alibabacloud=&userCode=mvsk1hl5
- Tencent Cloud Lighthouse: https://cloud.tencent.com/product/lighthouse
- Tencent Cloud Campus promo: https://cloud.tencent.com/act/campus

Clone the repo on each app host:

```bash
git clone https://github.com/SCUStack/scustack.git
cd scustack
```

The `¥400` MVP profile must deploy Elasticsearch: `docker-compose.production.yml` includes it as a production service, and the `api` and `worker` services depend on its healthy status. OnlyOffice remains deferred and is not exposed by the production Compose stack. This conclusion is based on `docker-compose.production.yml`.

## 2. DNS And SSL

Create DNS records:

```text
scustack.cn              A      <server public IP>
www.scustack.cn          CNAME  scustack.cn
api.scustack.cn          CNAME  scustack.cn   # requires external LB/reverse proxy routing
download.scustack.cn     CNAME  <LFS download gateway domain>
```

`docker/nginx/scustack.conf` currently contains one default `server` (`server_name _`) and routes `/api/` to the internal API. It does not define an `api.scustack.cn` virtual host. Therefore `api.scustack.cn` in `NUXT_PUBLIC_API_BASE` must be provided by a load balancer or reverse proxy outside this repository, or replaced with the externally published hostname that routes to this ingress.

If using Let's Encrypt on Nginx:

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d scustack.cn -d www.scustack.cn -d api.scustack.cn
```

Verify certificate renewal:

```bash
sudo certbot renew --dry-run
```

## 3. Environment

Backend production `.env`:

```bash
cat > scustack-api/.env <<'EOF'
SCUSTACK_APP_ENV=prod
SCUSTACK_DEBUG=false
SCUSTACK_PUBLIC_API_BASE=https://scustack.top
SCUSTACK_CORS_ORIGINS=["https://scustack.top","https://www.scustack.top"]
SCUSTACK_TRUSTED_HOSTS=["scustack.top","www.scustack.top"]
SCUSTACK_COOKIE_SECURE=true
SCUSTACK_CSRF_COOKIE_DOMAIN=.scustack.top
SCUSTACK_DB_HOST=<postgres-host>
SCUSTACK_DB_PORT=5432
SCUSTACK_DB_USER=<db-user>
SCUSTACK_DB_PASSWORD=<db-password>
SCUSTACK_DB_NAME=scustack
SCUSTACK_DB_POOL_SIZE=20
SCUSTACK_REDIS_URL=redis://<redis-host>:6379/0
SCUSTACK_ES_HOST=
SCUSTACK_STORAGE_DEFAULT_PROVIDER=lfs
SCUSTACK_STORAGE_DOWNLOAD_GATEWAY=https://download.cacodex.app
SCUSTACK_THUMBNAIL_DIR=/app/data/thumbnails
SCUSTACK_PREVIEW_CACHE_DIR=/app/data/previews
SCUSTACK_PREVIEW_CACHE_TTL_SECONDS=900
SCUSTACK_PREVIEW_CACHE_MAX_BYTES=1073741824
SCUSTACK_LFS_UPLOAD_URL=https://lfs.cacodex.app/upload
SCUSTACK_LFS_PUBLIC_BASE=https://lfs.cacodex.app
SCUSTACK_LFS_API_TOKEN=<lfs-api-token>
SCUSTACK_LFS_AUTH_HEADER=Authorization
SCUSTACK_LFS_AUTH_PREFIX=Bearer
SCUSTACK_LFS_UPLOAD_FIELD=file
SCUSTACK_JWT_SECRET_KEY=<at-least-32-random-characters>
SCUSTACK_ENCRYPTION_KEY=<at-least-32-random-characters>
SCUSTACK_SENTRY_DSN=<sentry-dsn>
SCUSTACK_UNIVERSITY_AUTH_PROVIDER=scu_cli
SCUSTACK_SCU_CLI_PATH=/usr/local/bin/scu
SCUSTACK_SCU_CLI_TIMEOUT_SECONDS=30
SCUSTACK_SCU_CLI_RUNTIME_DIR=/dev/shm
EOF
```

The database password must contain at least 16 characters. Keep the LFS token, JWT secret,
encryption key, and database password in deployment secrets and never commit their values.

The API image installs the checksum-verified SCU-CLI `v0.4.1` release. Registration runs it in
an isolated pseudo-terminal so the university password never appears in process arguments. Each
request gets a private directory under `/dev/shm`; the directory and the CLI-created credentials
file are deleted before the request returns. Keep the API service `tmpfs` mount enabled. SCU-CLI is
licensed under AGPL-3.0 and its corresponding source is available at
`https://github.com/The-Brotherhood-of-SCU/SCU-CLI/tree/v0.4.1`.

Variables required by `docker-compose.production.yml`:

```bash
export SCUSTACK_RELEASE_SHA=<immutable-release-tag>
export SCUSTACK_INGRESS_PORT=80
export SCUSTACK_DB_PASSWORD=<at-least-16-random-characters>
export SCUSTACK_ENV_FILE=/srv/apps/scustack/shared/.env
```

Frontend production `.env`:

```bash
cat > scustack-web/.env <<'EOF'
NUXT_PUBLIC_API_BASE=https://api.scustack.cn
NUXT_PUBLIC_OFFICE_PREVIEW_BASE=https://office.scustack.cn
NUXT_PUBLIC_APP_ENV=prod
NUXT_PUBLIC_SENTRY_DSN=<frontend-sentry-dsn>
EOF
```

`NUXT_PUBLIC_OFFICE_PREVIEW_BASE` must point to a browser-reachable and securely configured
OnlyOffice-compatible preview gateway. The production Compose file keeps OnlyOffice in the
`development` profile and publishes no port for it. The current repository does not provide this
gateway; deploy it separately outside this repository before setting this variable.

Store secrets in your cloud secret store or GitHub Actions secrets. Do not commit `.env`.

生产自动部署当前未启用。`.github/workflows/docker-build.yml` 仅在 pull request、`main` 推送或手动触发时执行 Docker 镜像构建静态检查，不登录 GHCR、不推送镜像，也不连接生产服务器。生产部署需由经过授权的运维流程按本手册手动执行；后续若恢复自动部署，必须单独评审并显式修改工作流。

Suggested production compose override for a single-node app host:

```yaml
services:
  api:
    build: ./scustack-api
    env_file:
      - ./scustack-api/.env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8403
    ports:
      - "8403:8403"

  web:
    build: ./scustack-web
    env_file:
      - ./scustack-web/.env
    ports:
      - "3000:3000"

  celery-worker:
    build: ./scustack-api
    env_file:
      - ./scustack-api/.env
    command: celery -A app.core.celery_app worker -l info -Q default,scan,thumbnail

  celery-beat:
    build: ./scustack-api
    env_file:
      - ./scustack-api/.env
    command: celery -A app.core.celery_app beat -l info
```

## 4. Database And Search Initialization

Install backend dependencies and run migrations:

```bash
cd scustack-api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
```

Seed colleges:

```bash
python scripts/seed_colleges.py
```

If using mock data in staging only:

```bash
python -m scripts.seed_mock_data
```

Initialize the database and seed baseline data:

```bash
python scripts/seed_colleges.py
```

The production Compose stack starts Elasticsearch as a required service. Initialize its index manually:

```bash
python - <<'PY'
import asyncio
from app.core.elasticsearch import ensure_materials_index
asyncio.run(ensure_materials_index())
PY
```

Health check after initialization:

```bash
curl -fsS https://api.scustack.cn/api/v1/health | jq
curl -fsS https://api.scustack.cn/api/v1/health/ready | jq
curl -fsS http://<es-host>:9200/_cluster/health | jq
```

## 5. Monitoring

Backend Sentry is enabled when `SCUSTACK_SENTRY_DSN` is set.

Check Celery worker and beat:

```bash
celery -A app.core.celery_app inspect active
celery -A app.core.celery_app inspect scheduled
```

Check application health:

```bash
curl -fsS https://api.scustack.cn/api/v1/health
curl -fsS https://api.scustack.cn/api/v1/health/live
curl -fsS https://api.scustack.cn/api/v1/health/ready
```

Check Redis and PostgreSQL connectivity from the app host:

```bash
redis-cli -h <redis-host> ping
psql "postgresql://<db-user>:<db-password>@<rds-host>:5432/scustack" -c "select 1;"
```

For the MVP profile, verify Elasticsearch as well as the app and storage. OnlyOffice is optional; verify it only when a separately deployed preview gateway is configured:

```bash
curl -fsS https://scustack.cn
curl -fsS https://api.scustack.cn/api/v1/health
```

If using containerized services:

```bash
docker ps
docker logs scustack-elasticsearch --tail 100
docker logs scustack-onlyoffice --tail 100
```

## 6. Pre-Launch Verification

Smoke-test API:

```bash
curl -fsS https://api.scustack.cn/api/v1/health
curl -fsS https://api.scustack.cn/api/v1/search?q=%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84
curl -fsS https://api.scustack.cn/api/v1/colleges
```

Smoke-test frontend:

```bash
curl -I https://scustack.cn
curl -I https://scustack.cn/search
curl -I https://api.scustack.cn/docs
```

Manual critical-path checklist:

- Home page renders and search works
- Login sets cookies and authenticated write requests succeed
- Upload token flow succeeds and created hosted material stays `pending`
- Admin review can approve a pending material
- Office files load via `NUXT_PUBLIC_OFFICE_PREVIEW_BASE` when enabled; otherwise the MVP shows the download fallback
- `/api/v1/health`, `/api/v1/health/live`, and `/api/v1/health/ready` all return 200

## 7. 文档与配置对照

| 文档路径 | 对应配置路径 | 对齐结论 |
|---|---|---|
| `docs/DEPLOYMENT-部署手册.md` | `docker-compose.production.yml` | 生产 MVP 启动 Elasticsearch；`api` 和 `worker` 等待其 healthy；OnlyOffice 仅保留 `development` profile 且不发布端口 |
| `docs/DEPLOYMENT-部署手册.md` | `docker/nginx/scustack.conf` | 仓库只有默认 `server`，`/api/` 代理到内部 API；`api.scustack.cn` 需由仓库外部负载均衡或反向代理提供 |
| `README.md`、`CONTRIBUTING.md` | `.github/workflows/pr-checks.yml`、`pnpm-lock.yaml`、`scustack-web/package-lock.json` | 本地支持根目录 pnpm workspace；前端 CI 使用 `npm ci` 和前端 package-lock，二者不混用 |
| `README.md` | `LICENSE`、SCUSTACK-3 | 当前无 `LICENSE` 文件，SCUSTACK-3 尚未落地，README 保留未加入仓库的说明并交叉引用工单 |

## 8. Rollback

Application rollback to previous image:

```bash
docker ps
docker images | head
docker stop scustack-api
docker rm scustack-api
docker run -d --name scustack-api --env-file scustack-api/.env -p 8403:8403 <previous-api-image>
```

Frontend rollback:

```bash
docker stop scustack-web
docker rm scustack-web
docker run -d --name scustack-web --env-file scustack-web/.env -p 3000:3000 <previous-web-image>
```

Database migration rollback:

```bash
cd scustack-api
alembic history
alembic downgrade -1
```

Backup restore helper:

```bash
bash scripts/backup_db.sh
psql "postgresql://<db-user>:<db-password>@<rds-host>:5432/scustack" < backup.sql
```

Staging rollback verification status:

- Not verified in this repository-only pass.
- A staging rollback rehearsal is still required before declaring the runbook fully complete.
| 字段 | 内容 |
|---|---|
| Type | `deployment` |
| Status | `active` |
| Owner | `team` |
| Last Updated | `2026-06-19` |
| Source of Truth | `yes` |
| Scope | 低预算单机 MVP 的生产部署、环境变量、验证与回滚说明。 |

> 本文是当前可执行的部署主文档，默认面向 `¥400` 预算的单机上线方案，不覆盖多机高可用生产集群。
