-- 1. Core entities: tenants, users, channels

CREATE TABLE tenants (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        UNIQUE NOT NULL DEFAULT gen_random_uuid(),
  title       TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID
);

CREATE TABLE users (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        UNIQUE NOT NULL DEFAULT gen_random_uuid(),
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  email       TEXT        UNIQUE NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID
);

CREATE TABLE channels (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        UNIQUE NOT NULL DEFAULT gen_random_uuid(),
  identifier  TEXT        UNIQUE NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID
);

-- 2. Junction tables

CREATE TABLE tenants_users (
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role        TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  PRIMARY KEY (tenant_id, user_id),
  CONSTRAINT uq_tenants_users_tenant_user UNIQUE (tenant_id, user_id)
);

CREATE TABLE users_identity_providers (
  user_id                   UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  identity_provider_user_id UUID        NOT NULL,
  identity_provider         TEXT        NOT NULL,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, identity_provider_user_id),
  CONSTRAINT uq_users_identity_providers UNIQUE (identity_provider_user_id, user_id)
);

CREATE TABLE tenants_identity_providers (
  tenant_id                   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  identity_provider_tenant_id UUID        NOT NULL,
  identity_provider           TEXT        NOT NULL,
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, identity_provider_tenant_id),
  CONSTRAINT uq_tenants_identity_providers UNIQUE (identity_provider_tenant_id, tenant_id)
);

CREATE TABLE tenants_channels (
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  channel_id  UUID        NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  PRIMARY KEY (tenant_id, channel_id),
  CONSTRAINT uq_tenants_channels UNIQUE (tenant_id, channel_id)
);

-- 3. Projects and Reports (tenant-scoped)

CREATE TABLE projects (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name        TEXT        NOT NULL,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  CONSTRAINT uq_projects_external_id UNIQUE (external_id),
  CONSTRAINT uq_projects_tenant_name UNIQUE (tenant_id, name)
);

CREATE INDEX idx_projects_tenant_id ON projects(tenant_id);

CREATE TABLE reports (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  content     JSONB,
  recipients  TEXT[]      NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_reports_external_id UNIQUE (external_id)
);

CREATE INDEX idx_reports_tenant_id ON reports(tenant_id);

-- 4. Niches and Keywords

CREATE TABLE niches (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  title       TEXT        NOT NULL,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  CONSTRAINT uq_niches_external_id UNIQUE (external_id),
  CONSTRAINT uq_niches_tenant_title UNIQUE (tenant_id, title)
);

CREATE INDEX idx_niches_tenant_id ON niches(tenant_id);

CREATE TABLE keywords (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  niche_id    UUID        NOT NULL REFERENCES niches(id) ON DELETE CASCADE,
  term        TEXT        NOT NULL,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  CONSTRAINT uq_keywords_external_id UNIQUE (external_id),
  CONSTRAINT uq_keywords_niche_term UNIQUE (niche_id, term)
);

CREATE INDEX idx_keywords_tenant_id ON keywords(tenant_id);
CREATE INDEX idx_keywords_niche_id ON keywords(niche_id);

-- 5. Integration Profiles

CREATE TABLE integration_profiles (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  niche_id    UUID        NOT NULL REFERENCES niches(id) ON DELETE CASCADE,
  project_id  UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  channel_id  UUID        NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  CONSTRAINT uq_integration_profiles_external_id UNIQUE (external_id),
  CONSTRAINT uq_integration_profiles_project_niche_channel UNIQUE (project_id, niche_id, channel_id)
);

CREATE INDEX idx_integration_profiles_tenant_id ON integration_profiles(tenant_id);
CREATE INDEX idx_integration_profiles_project_id ON integration_profiles(project_id);
CREATE INDEX idx_integration_profiles_niche_id ON integration_profiles(niche_id);
CREATE INDEX idx_integration_profiles_channel_id ON integration_profiles(channel_id);

-- 6. Images

CREATE TABLE images (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  niche_id    UUID        NOT NULL REFERENCES niches(id) ON DELETE CASCADE,
  keyword_id  UUID        NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
  kind        TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_images_external_id UNIQUE (external_id)
);

CREATE INDEX idx_images_tenant_id ON images(tenant_id);
CREATE INDEX idx_images_keyword_id ON images(keyword_id);

-- 7. Contents

CREATE TABLE contents (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  niche_id    UUID        NOT NULL REFERENCES niches(id) ON DELETE CASCADE,
  keyword_id  UUID        NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
  title       TEXT        NOT NULL,
  description TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_contents_external_id UNIQUE (external_id)
);

CREATE INDEX idx_contents_tenant_id ON contents(tenant_id);
CREATE INDEX idx_contents_keyword_id ON contents(keyword_id);

-- 8. Renders

CREATE TABLE renders (
  id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id     UUID          NOT NULL DEFAULT gen_random_uuid(),
  tenant_id       UUID          NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  content_id      UUID          NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
  niche_id        UUID          NOT NULL REFERENCES niches(id) ON DELETE CASCADE,
  keyword_id      UUID          NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
  input_image_id  UUID          REFERENCES images(id) ON DELETE SET NULL,
  output_image_id UUID          REFERENCES images(id) ON DELETE SET NULL,
  style_name      TEXT,
  status          TEXT          NOT NULL,
  created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
  CONSTRAINT uq_renders_external_id UNIQUE (external_id)
);

CREATE INDEX idx_renders_tenant_id ON renders(tenant_id);
CREATE INDEX idx_renders_content_id ON renders(content_id);

-- 9. Publications

CREATE TABLE publications (
  id          UUID               PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID               NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID               NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  render_id   UUID               REFERENCES renders(id) ON DELETE SET NULL,
  channel_id  UUID               NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  content_id  UUID               NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
  post_id     TEXT,
  status      TEXT               NOT NULL,
  created_at  TIMESTAMPTZ        NOT NULL DEFAULT now(),
  CONSTRAINT uq_publications_external_id UNIQUE (external_id)
);

CREATE INDEX idx_publications_tenant_id ON publications(tenant_id);
CREATE INDEX idx_publications_channel_id ON publications(channel_id);
CREATE INDEX idx_publications_content_id ON publications(content_id);

-- 10. Promotions

CREATE TABLE promotions (
  id             UUID                   PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id    UUID                   NOT NULL DEFAULT gen_random_uuid(),
  tenant_id      UUID                   NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  publication_id UUID                   NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
  channel_id     UUID                   NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  payload        JSONB,
  action_taken   TEXT                   NOT NULL,
  status         TEXT                   NOT NULL,
  created_at     TIMESTAMPTZ            NOT NULL DEFAULT now(),
  executed_at    TIMESTAMPTZ,
  CONSTRAINT uq_promotions_external_id UNIQUE (external_id)
);

CREATE INDEX idx_promotions_tenant_id ON promotions(tenant_id);
CREATE INDEX idx_promotions_publication_id ON promotions(publication_id);

-- 11. Publication Metrics

CREATE TABLE publication_metrics (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id    UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id      UUID        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  publication_id UUID        NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
  channel_id     UUID        NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  snapshot_date  TIMESTAMPTZ NOT NULL,
  metrics        JSONB,
  fetched_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_publication_metrics_external_id UNIQUE (external_id),
  CONSTRAINT uq_publication_metrics_pub_snapshot UNIQUE (publication_id, snapshot_date)
);

CREATE INDEX idx_publication_metrics_tenant_id ON publication_metrics(tenant_id);
CREATE INDEX idx_publication_metrics_publication_id ON publication_metrics(publication_id);

-- 12. Schedules

CREATE TABLE schedules (
  id              UUID                  PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id     UUID                  NOT NULL DEFAULT gen_random_uuid(),
  tenant_id       UUID                  NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  niche_id        UUID                  NOT NULL REFERENCES niches(id) ON DELETE CASCADE,
  is_active       BOOLEAN               NOT NULL DEFAULT true,
  title           TEXT                  NOT NULL,
  cron_expression TEXT                  NOT NULL,
  message_type    TEXT                  NOT NULL,
  message_payload TEXT,
  last_run_at     TIMESTAMPTZ,
  next_run_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ           NOT NULL DEFAULT now(),
  created_by      UUID,
  updated_at      TIMESTAMPTZ,
  updated_by      UUID,
  CONSTRAINT uq_schedules_external_id UNIQUE (external_id)
);

CREATE INDEX idx_schedules_tenant_id ON schedules(tenant_id);
CREATE INDEX idx_schedules_niche_id ON schedules(niche_id);

-- 13. Schedule Executions

CREATE TABLE schedule_executions (
  id           UUID                      PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id  UUID                      NOT NULL DEFAULT gen_random_uuid(),
  tenant_id    UUID                      NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  schedule_id  UUID                      NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
  niche_id     UUID                      NOT NULL REFERENCES niches(id) ON DELETE CASCADE,
  keyword_id   UUID                      REFERENCES keywords(id) ON DELETE SET NULL,
  status       TEXT                      NOT NULL,
  started_at   TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  CONSTRAINT uq_schedule_executions_external_id UNIQUE (external_id)
);

CREATE INDEX idx_schedule_executions_tenant_id ON schedule_executions(tenant_id);
CREATE INDEX idx_schedule_executions_schedule_id ON schedule_executions(schedule_id);
