#!/usr/bin/env bash
# Doc §19.6: "Staging'de restore test edilmeden canliya gecis tamam sayilmamali"
# (a restore must be test-run in staging before go-live is considered done).
#
# Restores a pg_dump custom-format file (produced by backup_db.sh) into a
# Postgres database. By default this targets a *new* database name, not the
# live one - so running this script never clobbers production data by
# accident. Pass the real target db name explicitly (3rd arg) to actually
# replace it, e.g. once LITZOR runs the staging restore drill the doc asks for.
#
# Usage: ./restore_db.sh <dump_file> [db_container] [target_db_name]
set -euo pipefail

DUMP_FILE="${1:?Usage: restore_db.sh <dump_file> [db_container] [target_db_name]}"
DB_CONTAINER="${2:-bidmont-db}"
DB_USER="${DB_USER:-bidmont}"
TARGET_DB="${3:-bidmont_restore_test}"

if [ ! -f "$DUMP_FILE" ]; then
  echo "[restore_db] Dump file not found: $DUMP_FILE" >&2
  exit 1
fi

echo "[restore_db] (Re)creating target database '$TARGET_DB'..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${TARGET_DB};"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${TARGET_DB};"

echo "[restore_db] Restoring $DUMP_FILE into $TARGET_DB..."
docker exec -i "$DB_CONTAINER" pg_restore -U "$DB_USER" -d "$TARGET_DB" --no-owner < "$DUMP_FILE"

echo "[restore_db] Done. Verify row counts against the source before trusting this restore, e.g.:"
echo "  docker exec $DB_CONTAINER psql -U $DB_USER -d $TARGET_DB -c 'SELECT count(*) FROM auctions;'"
