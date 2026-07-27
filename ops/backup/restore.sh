#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: restore.sh /backups/crm_fuel_YYYYMMDDTHHMMSSZ.dump" >&2
  exit 2
fi

backup_file="$1"
case "$backup_file" in
  /backups/crm_fuel_*.dump) ;;
  *) echo "Backup must be an explicit /backups/crm_fuel_*.dump file" >&2; exit 2 ;;
esac

test -f "$backup_file"
pg_restore --list "$backup_file" >/dev/null
pg_restore \
  --host="$POSTGRES_HOST" \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  --clean \
  --if-exists \
  --no-owner \
  "$backup_file"
