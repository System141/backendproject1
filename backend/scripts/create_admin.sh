#!/usr/bin/env bash
# Wraps POST /api/admin/seed - the only way to create an admin account
# (see CLAUDE.md). Does not touch the DB directly, just calls the API so the
# existing checks (SEED_SECRET match, "admin already exists", email taken)
# stay the single source of truth.
#
# Usage: ./create_admin.sh [email] [base_url]
#   - only the password is prompted interactively (never passed as an
#     arg/env var, so it never lands in shell history or the process list)
#   - SEED_SECRET is auto-loaded from the repo root .env (gitignored, never
#     committed) unless already exported - it is NOT hardcoded here on
#     purpose, this file is tracked in git
#   - email defaults to admin@bidmont.me, base_url to http://145.223.90.15:8000/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../.env"
if [ -z "${SEED_SECRET:-}" ] && [ -f "$ENV_FILE" ]; then
  SEED_SECRET="$(grep -m1 '^SEED_SECRET=' "$ENV_FILE" | cut -d= -f2-)"
fi
: "${SEED_SECRET:?SEED_SECRET not set and not found in $ENV_FILE}"
EMAIL="${1:-admin@bidmont.me}"
BASE_URL="${2:-http://localhost:8000/}"

read -rs -p "Admin password: " PASSWORD
echo
if [ -z "$PASSWORD" ]; then
  echo "[create_admin] Password cannot be empty" >&2
  exit 1
fi

RESPONSE=$(curl -sS -G -w '\n%{http_code}' -X POST "${BASE_URL%/}/api/admin/seed" \
  --data-urlencode "email=$EMAIL" \
  --data-urlencode "password=$PASSWORD" \
  --data-urlencode "secret=$SEED_SECRET")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
  echo "[create_admin] Admin created: $EMAIL"
else
  echo "[create_admin] Failed (HTTP $HTTP_CODE): $BODY" >&2
  exit 1
fi
