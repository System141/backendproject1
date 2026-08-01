#!/usr/bin/env bash
# Doc §19.6: DB backup schedule + media backup policy.
#
# Dumps the bidmont-db Postgres container (custom format, via pg_dump inside
# the container itself - no Postgres client tools needed on the host, only
# docker) plus a tarball of the bidmont-uploads named volume, into a
# timestamped pair of files under BACKUP_DIR.
#
# Usage: ./backup_db.sh [backup_dir]
# Cron (daily at 03:00, keeping the last 14 days - adjust retention/schedule
# to whatever LITZOR's actual ops policy ends up being, this is a starting
# point not a mandated schedule):
#   0 3 * * * /path/to/backend/scripts/backup_db.sh /var/backups/bidmont >> /var/log/bidmont-backup.log 2>&1
#   find /var/backups/bidmont -name '*.sql.dump' -mtime +14 -delete
#   find /var/backups/bidmont -name '*.tar.gz' -mtime +14 -delete
set -euo pipefail

DB_CONTAINER="${DB_CONTAINER:-bidmont-db}"
DB_USER="${DB_USER:-bidmont}"
DB_NAME="${DB_NAME:-bidmont}"
UPLOADS_VOLUME="${UPLOADS_VOLUME:-backendproject1_bidmont-uploads}"
BACKUP_DIR="${1:-./backups}"
STAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "[backup_db] Dumping $DB_NAME from $DB_CONTAINER..."
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -Fc -d "$DB_NAME" > "$BACKUP_DIR/bidmont_${STAMP}.sql.dump"
echo "[backup_db] DB dump written to $BACKUP_DIR/bidmont_${STAMP}.sql.dump"

echo "[backup_db] Archiving uploads volume ($UPLOADS_VOLUME)..."
# docker cp (not a -v bind mount) so this works identically on Linux/macOS
# hosts and on Windows+Git-Bash, where MSYS path translation on -v host
# paths containing a drive letter + colon is unreliable.
CID=$(docker create -v "${UPLOADS_VOLUME}:/data:ro" alpine sh -c "tar czf /uploads.tar.gz -C /data .")
docker start -a "$CID" > /dev/null
docker cp "$CID:/uploads.tar.gz" "$BACKUP_DIR/uploads_${STAMP}.tar.gz"
docker rm "$CID" > /dev/null
echo "[backup_db] Uploads archive written to $BACKUP_DIR/uploads_${STAMP}.tar.gz"

echo "[backup_db] Done."
