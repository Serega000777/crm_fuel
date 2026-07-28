#!/bin/sh
set -eu

backup_dir="${BACKUP_DIR:-/backups}"
restore_database="${RESTORE_DATABASE:-crm_fuel_restore}"
backup_file="$(find "$backup_dir" -type f -name 'crm_fuel_*.dump' | sort | tail -n 1)"
test -n "$backup_file"

pg_restore --list "$backup_file" >/dev/null
PGDATABASE="$restore_database" pg_restore \
  --host="$POSTGRES_HOST" \
  --username="$POSTGRES_USER" \
  --no-owner \
  "$backup_file"

marker="$(
  PGDATABASE="$restore_database" psql \
    --host="$POSTGRES_HOST" \
    --username="$POSTGRES_USER" \
    --tuples-only \
    --no-align \
    --command='SELECT marker FROM backup_rehearsal LIMIT 1'
)"
test "$marker" = "crm-fuel-backup-ok"
echo "Restore rehearsal passed using: $backup_file"
