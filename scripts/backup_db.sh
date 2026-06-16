#!/bin/bash
# PostgreSQL backup script — pg_dump → gzip → OSS upload
# Usage: ./backup_db.sh
# Requires: pg_dump, gzip, ossutil (Alibaba Cloud CLI) or environment variables
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Source .env if exists
if [ -f "$PROJECT_DIR/scustack-api/.env" ]; then
    set -a; source "$PROJECT_DIR/scustack-api/.env"; set +a
fi

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="/tmp/backup-${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting database backup..."

# pg_dump
PGPASSWORD="${SCUSTACK_DB_PASSWORD:-scustack}" pg_dump \
    -h "${SCUSTACK_DB_HOST:-localhost}" \
    -p "${SCUSTACK_DB_PORT:-5432}" \
    -U "${SCUSTACK_DB_USER:-scustack}" \
    -d "${SCUSTACK_DB_NAME:-scustack}" \
    --no-owner --no-acl | gzip > "$BACKUP_FILE"

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup created: $BACKUP_FILE ($SIZE)"

# Upload to OSS if configured
if [ -n "${SCUSTACK_OSS_ACCESS_KEY_ID:-}" ] && [ -n "${SCUSTACK_OSS_BUCKET:-}" ]; then
    OSS_KEY="backups/database/backup-${TIMESTAMP}.sql.gz"
    echo "[$(date)] Uploading to OSS: $OSS_KEY..."

    python3 -c "
import oss2
auth = oss2.Auth('${SCUSTACK_OSS_ACCESS_KEY_ID}', '${SCUSTACK_OSS_ACCESS_KEY_SECRET}')
bucket = oss2.Bucket(auth, '${SCUSTACK_OSS_ENDPOINT}', '${SCUSTACK_OSS_BUCKET}')
bucket.put_object_from_file('${OSS_KEY}', '${BACKUP_FILE}')
print('Upload complete')
"
    echo "[$(date)] Uploaded to OSS: $OSS_KEY"
fi

# Cleanup old local backups (keep 7 days)
find /tmp -name 'backup-*.sql.gz' -mtime +7 -delete 2>/dev/null || true

echo "[$(date)] Backup complete."

# Retention reminder — OSS lifecycle policy should handle remote cleanup:
# Daily backups: retain 7 days
# Weekly backups (Monday): retain 4 weeks
# Monthly backups (1st of month): retain 12 months
