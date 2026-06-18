# Production Deployment Runbook

## 1. Infrastructure

Recommended Alibaba Cloud baseline:

- `2 x ECS 4C8G` for app traffic behind a load balancer
- `1 x ECS 4C8G` for `OnlyOffice`
- `1 x RDS PostgreSQL 16`
- `1 x Redis 7`
- `1 x Elasticsearch 8.x` with IK plugin
- `1 x OSS bucket` for hosted files and thumbnails
- `1 x CDN` in front of OSS file delivery

Clone the repo on each app host:

```bash
git clone https://github.com/yeyixiang2007/scustack.git
cd scustack
```

Build the custom Elasticsearch image with IK:

```bash
docker build -t scustack-elasticsearch:8.17.0 docker/elasticsearch
```

Run Elasticsearch:

```bash
docker run -d --name scustack-elasticsearch \
  -p 9200:9200 -p 9300:9300 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  --ulimit memlock=-1:-1 \
  -v es_data:/usr/share/elasticsearch/data \
  scustack-elasticsearch:8.17.0
```

Run OnlyOffice:

```bash
docker run -d --name scustack-onlyoffice \
  -p 8088:80 \
  -e JWT_ENABLED=false \
  -v oo_data:/var/www/onlyoffice/Data \
  onlyoffice/documentserver:8.2
```

## 2. DNS And SSL

Create DNS records:

```text
scustack.cn              A      <SLB or ECS public IP>
www.scustack.cn          CNAME  scustack.cn
api.scustack.cn          CNAME  scustack.cn
files.scustack.cn        CNAME  <OSS CDN domain>
office.scustack.cn       A      <OnlyOffice ECS public IP>
```

If using Alibaba Cloud ACM certificates, bind the certificate to SLB / CDN and terminate HTTPS there.

If using Let's Encrypt on Nginx:

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d scustack.cn -d www.scustack.cn -d api.scustack.cn -d office.scustack.cn
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
SCUSTACK_DB_HOST=<rds-host>
SCUSTACK_DB_PORT=5432
SCUSTACK_DB_USER=<db-user>
SCUSTACK_DB_PASSWORD=<db-password>
SCUSTACK_DB_NAME=scustack
SCUSTACK_DB_POOL_SIZE=20
SCUSTACK_REDIS_URL=redis://<redis-host>:6379/0
SCUSTACK_ES_HOST=http://<es-host>:9200
SCUSTACK_OSS_ACCESS_KEY_ID=<oss-ak>
SCUSTACK_OSS_ACCESS_KEY_SECRET=<oss-sk>
SCUSTACK_OSS_ENDPOINT=https://oss-cn-chengdu.aliyuncs.com
SCUSTACK_OSS_BUCKET=<oss-bucket>
SCUSTACK_JWT_SECRET_KEY=<strong-random-secret>
SCUSTACK_ENCRYPTION_KEY=<strong-random-secret>
SCUSTACK_SENTRY_DSN=<sentry-dsn>
EOF
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

Store secrets in Alibaba Cloud KMS, GitHub Actions secrets, or your deployment platform secret store. Do not commit `.env`.

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

Initialize Elasticsearch index:

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

Check Elasticsearch and OnlyOffice:

```bash
curl -fsS http://<es-host>:9200/_cluster/health
curl -fsS https://office.scustack.cn/welcome/
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
- Office preview loads via `NUXT_PUBLIC_OFFICE_PREVIEW_BASE`
- `/api/v1/health` reports healthy `database`, `redis`, and `elasticsearch`

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
