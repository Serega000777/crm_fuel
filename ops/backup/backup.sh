#!/bin/sh
set -eu

backup_dir="${BACKUP_DIR:-/backups}"
retention_days="${BACKUP_RETENTION_DAYS:-14}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${backup_dir}/crm_fuel_${timestamp}.dump"

mkdir -p "$backup_dir"
pg_dump \
  --host="$POSTGRES_HOST" \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  --format=custom \
  --compress=9 \
  --file="$target"

pg_restore --list "$target" >/dev/null
find "$backup_dir" -type f -name 'crm_fuel_*.dump' -mtime "+$retention_days" -delete
echo "Verified backup created: $target"
