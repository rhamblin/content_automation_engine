#!/usr/bin/env bash
# init-database.sh — Run SQL init scripts against Azure PostgreSQL Flexible Server.
# Run once after first deployment, then only when schema changes.
#
# Prerequisites: psql client installed, az cli logged in
# Usage: ./init-database.sh <postgres-fqdn> <admin-user> <admin-password> <database-name>

set -euo pipefail

PG_HOST="${1:?Usage: $0 <postgres-fqdn> <admin-user> <admin-password> <database-name>}"
PG_USER="${2:?Usage: $0 <postgres-fqdn> <admin-user> <admin-password> <database-name>}"
PG_PASS="${3:?Usage: $0 <postgres-fqdn> <admin-user> <admin-password> <database-name>}"
PG_DB="${4:?Usage: $0 <postgres-fqdn> <admin-user> <admin-password> <database-name>}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/../../.."
INIT_DIR="${PROJECT_ROOT}/db/init"

export PGPASSWORD="${PG_PASS}"
PG_OPTS="-h ${PG_HOST} -U ${PG_USER} -d ${PG_DB} --set=sslmode=require"

echo "==> Connecting to ${PG_HOST}/${PG_DB} as ${PG_USER}"

# 02 — Enable extensions
echo "==> Running 02-enable-extensions.sql"
psql ${PG_OPTS} -f "${INIT_DIR}/02-enable-extensions.sql"

# 03 — Create tables
echo "==> Running 03-create-tables.sql"
psql ${PG_OPTS} -f "${INIT_DIR}/03-create-tables.sql"

# 01 — Create app users (adapted for Azure — admin is not superuser)
echo "==> Creating application database users"
APP_DB_USER="${APP_DB_USER:-appuser}"
APP_DB_PASSWORD="${APP_DB_PASSWORD:-appsecret}"
ANALYTICS_DB_USER="${ANALYTICS_DB_USER:-analyticsuser}"
ANALYTICS_DB_PASSWORD="${ANALYTICS_DB_PASSWORD:-analyticssecret}"

psql ${PG_OPTS} <<SQL
-- App user (read/write)
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${APP_DB_USER}') THEN
    CREATE ROLE ${APP_DB_USER} LOGIN PASSWORD '${APP_DB_PASSWORD}';
  END IF;
END
\$\$;

GRANT CONNECT ON DATABASE ${PG_DB} TO ${APP_DB_USER};
GRANT USAGE ON SCHEMA public TO ${APP_DB_USER};
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ${APP_DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${APP_DB_USER};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${APP_DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ${APP_DB_USER};

-- Analytics user (read-only)
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${ANALYTICS_DB_USER}') THEN
    CREATE ROLE ${ANALYTICS_DB_USER} LOGIN PASSWORD '${ANALYTICS_DB_PASSWORD}';
  END IF;
END
\$\$;

GRANT CONNECT ON DATABASE ${PG_DB} TO ${ANALYTICS_DB_USER};
GRANT USAGE ON SCHEMA public TO ${ANALYTICS_DB_USER};
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${ANALYTICS_DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ${ANALYTICS_DB_USER};
SQL

echo "==> Database initialization complete."
