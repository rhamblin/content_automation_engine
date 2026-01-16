#!/usr/bin/env bash
set -e

psql \
  --username "$POSTGRES_USER" \
  --dbname   "$POSTGRES_DB" <<-EOSQL
  -- Grant usage on public schema
  GRANT USAGE ON SCHEMA public TO ${APP_DB_USER};
  GRANT USAGE ON SCHEMA public TO ${ANALYTICS_DB_USER};

  -- App user: full CRUD on all tables
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ${APP_DB_USER};
  ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${APP_DB_USER};

  -- Analytics user: read-only access
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${ANALYTICS_DB_USER};
  ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO ${ANALYTICS_DB_USER};

  -- Grant usage on sequences (for any auto-increment columns)
  GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${APP_DB_USER};
  ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO ${APP_DB_USER};

  -- Grant usage on enum types
  GRANT USAGE ON TYPE image_kind TO ${APP_DB_USER};
  GRANT USAGE ON TYPE render_status TO ${APP_DB_USER};
  GRANT USAGE ON TYPE publication_status TO ${APP_DB_USER};
  GRANT USAGE ON TYPE promotion_action_taken TO ${APP_DB_USER};
  GRANT USAGE ON TYPE promotion_status TO ${APP_DB_USER};
  GRANT USAGE ON TYPE schedule_message_type TO ${APP_DB_USER};
  GRANT USAGE ON TYPE schedule_execution_status TO ${APP_DB_USER};

  GRANT USAGE ON TYPE image_kind TO ${ANALYTICS_DB_USER};
  GRANT USAGE ON TYPE render_status TO ${ANALYTICS_DB_USER};
  GRANT USAGE ON TYPE publication_status TO ${ANALYTICS_DB_USER};
  GRANT USAGE ON TYPE promotion_action_taken TO ${ANALYTICS_DB_USER};
  GRANT USAGE ON TYPE promotion_status TO ${ANALYTICS_DB_USER};
  GRANT USAGE ON TYPE schedule_message_type TO ${ANALYTICS_DB_USER};
  GRANT USAGE ON TYPE schedule_execution_status TO ${ANALYTICS_DB_USER};
EOSQL
