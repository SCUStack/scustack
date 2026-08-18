#!/usr/bin/env bash
set -Eeuo pipefail

release_sha="${1:?usage: deploy-production.sh <release-sha>}"
app_dir="${SCUSTACK_APP_DIR:-/srv/apps/scustack}"
repo_dir="$app_dir/repository"
env_file="$app_dir/shared/.env"
lock_file="$app_dir/shared/deploy.lock"
compose_files=(-f docker-compose.yml -f docker-compose.production.yml)

exec 9>"$lock_file"
flock -n 9 || { echo "Another deployment is in progress" >&2; exit 1; }

cd "$repo_dir"
test -f "$env_file"
export SCUSTACK_DB_PASSWORD="$(sed -n 's/^SCUSTACK_DB_PASSWORD=//p' "$env_file" | tail -n 1)"
export SCUSTACK_INGRESS_PORT="$(sed -n 's/^SCUSTACK_INGRESS_PORT=//p' "$env_file" | tail -n 1)"
test -n "$SCUSTACK_DB_PASSWORD"

previous_sha="$(git rev-parse HEAD 2>/dev/null || true)"
rollback() {
  exit_code=$?
  if [[ $exit_code -ne 0 && -n "$previous_sha" && "$previous_sha" != "$release_sha" ]]; then
    echo "Deployment failed; restoring $previous_sha" >&2
    git checkout --detach "$previous_sha"
    SCUSTACK_RELEASE_SHA="$previous_sha" SCUSTACK_ENV_FILE="$env_file" \
      docker compose "${compose_files[@]}" up -d --remove-orphans || true
  fi
  exit "$exit_code"
}
trap rollback EXIT

git fetch --prune origin main
git cat-file -e "$release_sha^{commit}"
git checkout --detach "$release_sha"

export SCUSTACK_RELEASE_SHA="$release_sha"
export SCUSTACK_ENV_FILE="$env_file"

docker compose "${compose_files[@]}" config --quiet
docker compose "${compose_files[@]}" pull
docker compose "${compose_files[@]}" up -d postgres redis elasticsearch
docker compose "${compose_files[@]}" run --rm api alembic upgrade head
docker compose "${compose_files[@]}" up -d --remove-orphans

for attempt in $(seq 1 30); do
  if curl --fail --silent --show-error http://127.0.0.1:8080/api/v1/health/ready >/dev/null; then
    trap - EXIT
    printf '%s\n' "$release_sha" > "$app_dir/shared/current-release"
    docker image prune -f --filter 'until=168h' >/dev/null
    echo "Deployment $release_sha is healthy"
    exit 0
  fi
  sleep 5
done

docker compose "${compose_files[@]}" ps
docker compose "${compose_files[@]}" logs --tail=100 api web ingress
echo "Deployment health check timed out" >&2
exit 1
