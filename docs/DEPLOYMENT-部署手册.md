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
- `0 x Elasticsearch` in MVP
- `0 x OnlyOffice` in MVP
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
git clone https://github.com/yeyixiang2007/scustack.git
cd scustack
```

Do not deploy Elasticsearch or OnlyOffice in the `¥400` MVP profile. They are deferred upgrade items.

## 2. DNS And SSL

Create DNS records:

```text
scustack.cn              A      <server public IP>
www.scustack.cn          CNAME  scustack.cn
api.scustack.cn          CNAME  scustack.cn
download.scustack.cn     CNAME  <LFS download gateway domain>
```

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
SCUSTACK_PUBLIC_API_BASE=https://api.scustack.cn
SCUSTACK_CORS_ORIGINS=["https://scustack.cn","https://www.scustack.cn"]
SCUSTACK_TRUSTED_HOSTS=["api.scustack.cn"]
SCUSTACK_COOKIE_SECURE=true
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

`NUXT_PUBLIC_OFFICE_PREVIEW_BASE` must point to a browser-reachable OnlyOffice-compatible
preview gateway. The production Compose file does not publish the development OnlyOffice
container, so configure a separately secured service or an ingress route before launch.

Store secrets in your cloud secret store or GitHub Actions secrets. Do not commit `.env`.

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

If you later enable Elasticsearch as an upgrade item, initialize the index manually:

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

For the MVP profile, skip Elasticsearch and OnlyOffice checks. Verify app + storage instead:

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

## 7. Rollback

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
