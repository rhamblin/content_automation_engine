#!/usr/bin/env bash
set -e

psql \
  --username "$POSTGRES_USER" \
  --dbname   "$POSTGRES_DB" <<-EOSQL
  -- create app user (read/write)
  CREATE USER ${APP_DB_USER} WITH PASSWORD '${APP_DB_PASSWORD}';
  GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${APP_DB_USER};

  -- create analytics user (read-only)
  CREATE USER ${ANALYTICS_DB_USER} WITH PASSWORD '${ANALYTICS_DB_PASSWORD}';
  GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${ANALYTICS_DB_USER};
EOSQL
