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
  tenant_id   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  user_id     UUID        NOT NULL REFERENCES users(external_id) ON DELETE CASCADE,
  role        TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  PRIMARY KEY (tenant_id, user_id),
  CONSTRAINT uq_tenants_users_tenant_user UNIQUE (tenant_id, user_id)
);

CREATE TABLE users_identity_providers (
  user_id                   UUID        NOT NULL REFERENCES users(external_id) ON DELETE CASCADE,
  identity_provider_user_id UUID        NOT NULL,
  identity_provider         TEXT        NOT NULL,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, identity_provider_user_id),
  CONSTRAINT uq_users_identity_providers UNIQUE (identity_provider_user_id, user_id)
);

CREATE TABLE tenants_identity_providers (
  tenant_id                   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  identity_provider_tenant_id UUID        NOT NULL,
  identity_provider           TEXT        NOT NULL,
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, identity_provider_tenant_id),
  CONSTRAINT uq_tenants_identity_providers UNIQUE (identity_provider_tenant_id, tenant_id)
);

CREATE TABLE tenants_channels (
  tenant_id   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  channel_id  UUID        NOT NULL REFERENCES channels(external_id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  PRIMARY KEY (tenant_id, channel_id),
  CONSTRAINT uq_tenants_channels UNIQUE (tenant_id, channel_id)
);

-- 3. Reports (tenant-scoped)

CREATE TABLE reports (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  content     JSONB,
  recipients  TEXT[]      NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_reports_external_id UNIQUE (external_id)
);

CREATE INDEX idx_reports_tenant_id ON reports(tenant_id);

-- 4. Niches and Keywords

CREATE TABLE niches (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id     UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id       UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  title           TEXT        NOT NULL,
  brand_name      TEXT,
  brand_website   TEXT,
  brand_watermark TEXT,
  persona_name    TEXT,
  persona_prompt    TEXT,
  copy_style_prompt TEXT,
  channel_prompts   JSONB,
  is_active       BOOLEAN     NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by      UUID,
  updated_at      TIMESTAMPTZ,
  updated_by      UUID,
  CONSTRAINT uq_niches_external_id UNIQUE (external_id),
  CONSTRAINT uq_niches_tenant_title UNIQUE (tenant_id, title)
);

CREATE INDEX idx_niches_tenant_id ON niches(tenant_id);

CREATE TABLE keywords (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  niche_id    UUID        NOT NULL REFERENCES niches(external_id) ON DELETE CASCADE,
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
  tenant_id   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  niche_id    UUID        NOT NULL REFERENCES niches(external_id) ON DELETE CASCADE,
  channel_id  UUID        NOT NULL REFERENCES channels(external_id) ON DELETE CASCADE,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  CONSTRAINT uq_integration_profiles_external_id UNIQUE (external_id),
  CONSTRAINT uq_integration_profiles_tenant_niche_channel UNIQUE (tenant_id, niche_id, channel_id)
);

CREATE INDEX idx_integration_profiles_tenant_id ON integration_profiles(tenant_id);
CREATE INDEX idx_integration_profiles_niche_id ON integration_profiles(niche_id);
CREATE INDEX idx_integration_profiles_channel_id ON integration_profiles(channel_id);

-- 6. Contents

CREATE TABLE contents (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  niche_id    UUID        NOT NULL REFERENCES niches(external_id) ON DELETE CASCADE,
  keyword_id  UUID        NOT NULL REFERENCES keywords(external_id) ON DELETE CASCADE,
  title       TEXT        NOT NULL DEFAULT '[Untitled]',
  description TEXT        NOT NULL DEFAULT '[No description]',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_contents_external_id UNIQUE (external_id)
);

CREATE INDEX idx_contents_tenant_id ON contents(tenant_id);
CREATE INDEX idx_contents_keyword_id ON contents(keyword_id);

-- 7. Renders

CREATE TABLE renders (
  id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id      UUID          NOT NULL DEFAULT gen_random_uuid(),
  tenant_id        UUID          NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  content_id       UUID          NOT NULL REFERENCES contents(external_id) ON DELETE CASCADE,
  niche_id         UUID          NOT NULL REFERENCES niches(external_id) ON DELETE CASCADE,
  keyword_id       UUID          NOT NULL REFERENCES keywords(external_id) ON DELETE CASCADE,
  input_image_uri  TEXT          NOT NULL,
  output_image_uri TEXT,
  style_name       TEXT,
  status           TEXT          NOT NULL DEFAULT 'pending',
  created_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
  CONSTRAINT uq_renders_external_id UNIQUE (external_id)
);

CREATE INDEX idx_renders_tenant_id ON renders(tenant_id);
CREATE INDEX idx_renders_content_id ON renders(content_id);

-- 8. Publications

CREATE TABLE publications (
  id          UUID               PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID               NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID               NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  render_id   UUID               REFERENCES renders(external_id) ON DELETE SET NULL,
  channel_id  UUID               NOT NULL REFERENCES channels(external_id) ON DELETE CASCADE,
  content_id  UUID               NOT NULL REFERENCES contents(external_id) ON DELETE CASCADE,
  post_id     TEXT,
  status      TEXT               NOT NULL DEFAULT 'pending',
  created_at  TIMESTAMPTZ        NOT NULL DEFAULT now(),
  CONSTRAINT uq_publications_external_id UNIQUE (external_id)
);

CREATE INDEX idx_publications_tenant_id ON publications(tenant_id);
CREATE INDEX idx_publications_channel_id ON publications(channel_id);
CREATE INDEX idx_publications_content_id ON publications(content_id);

-- 9. Promotions

CREATE TABLE promotions (
  id             UUID                   PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id    UUID                   NOT NULL DEFAULT gen_random_uuid(),
  tenant_id      UUID                   NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  publication_id UUID                   NOT NULL REFERENCES publications(external_id) ON DELETE CASCADE,
  channel_id     UUID                   NOT NULL REFERENCES channels(external_id) ON DELETE CASCADE,
  payload        JSONB,
  action_taken   TEXT                   NOT NULL DEFAULT 'none',
  status         TEXT                   NOT NULL DEFAULT 'pending',
  created_at     TIMESTAMPTZ            NOT NULL DEFAULT now(),
  executed_at    TIMESTAMPTZ,
  CONSTRAINT uq_promotions_external_id UNIQUE (external_id)
);

CREATE INDEX idx_promotions_tenant_id ON promotions(tenant_id);
CREATE INDEX idx_promotions_publication_id ON promotions(publication_id);

-- 10. Publication Metrics

CREATE TABLE publication_metrics (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id    UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id      UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  publication_id UUID        NOT NULL REFERENCES publications(external_id) ON DELETE CASCADE,
  channel_id     UUID        NOT NULL REFERENCES channels(external_id) ON DELETE CASCADE,
  snapshot_date  TIMESTAMPTZ NOT NULL,
  metrics        JSONB,
  fetched_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_publication_metrics_external_id UNIQUE (external_id),
  CONSTRAINT uq_publication_metrics_pub_snapshot UNIQUE (publication_id, snapshot_date)
);

CREATE INDEX idx_publication_metrics_tenant_id ON publication_metrics(tenant_id);
CREATE INDEX idx_publication_metrics_publication_id ON publication_metrics(publication_id);

-- 11. Schedules

CREATE TABLE schedules (
  id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id            UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id              UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  integration_profile_id UUID        REFERENCES integration_profiles(external_id) ON DELETE CASCADE,
  is_active              BOOLEAN     NOT NULL DEFAULT true,
  cron_expression        TEXT        NOT NULL,
  message_type           TEXT        NOT NULL DEFAULT 'content_generation_requested',
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by             UUID,
  updated_at             TIMESTAMPTZ,
  updated_by             UUID,
  CONSTRAINT uq_schedules_external_id UNIQUE (external_id)
);

CREATE INDEX idx_schedules_tenant_id ON schedules(tenant_id);
CREATE INDEX idx_schedules_integration_profile_id ON schedules(integration_profile_id);

-- Tenant-level schedules: one per tenant per message_type
CREATE UNIQUE INDEX uq_schedules_tenant_message_type
  ON schedules(tenant_id, message_type)
  WHERE integration_profile_id IS NULL;

-- Content generation: one per integration_profile
CREATE UNIQUE INDEX uq_schedules_integration_profile
  ON schedules(integration_profile_id)
  WHERE integration_profile_id IS NOT NULL;

-- 12. Styles (tenant-scoped, per channel)

CREATE TABLE styles (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  channel_id  UUID        NOT NULL REFERENCES channels(external_id) ON DELETE CASCADE,
  name        TEXT        NOT NULL,
  description TEXT,
  spec        JSONB       NOT NULL,
  is_active   BOOLEAN     NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  CONSTRAINT uq_styles_external_id UNIQUE (external_id),
  CONSTRAINT uq_styles_tenant_channel_name UNIQUE (tenant_id, channel_id, name)
);

CREATE INDEX idx_styles_tenant_id ON styles(tenant_id);
CREATE INDEX idx_styles_channel_id ON styles(channel_id);

-- 13. Channel Credentials (tenant-scoped)

CREATE TABLE channel_credentials (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id UUID        NOT NULL DEFAULT gen_random_uuid(),
  tenant_id   UUID        NOT NULL REFERENCES tenants(external_id) ON DELETE CASCADE,
  channel_id  UUID        NOT NULL REFERENCES channels(external_id) ON DELETE CASCADE,
  credentials JSONB       NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  UUID,
  updated_at  TIMESTAMPTZ,
  updated_by  UUID,
  CONSTRAINT uq_channel_credentials_external_id UNIQUE (external_id),
  CONSTRAINT uq_channel_credentials_tenant_channel UNIQUE (tenant_id, channel_id)
);

CREATE INDEX idx_channel_credentials_tenant_id ON channel_credentials(tenant_id);
CREATE INDEX idx_channel_credentials_channel_id ON channel_credentials(channel_id);
