-- 1. Identity Schema: Tenants, Users, Tenant-Users, Projects

CREATE SCHEMA IF NOT EXISTS identity;

CREATE TABLE identity.tenants (
  tenant_id   UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT       NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE identity.users (
  user_id      UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
  email        TEXT       UNIQUE NOT NULL,
  provider     TEXT       NOT NULL,        -- e.g. 'azure_b2c', 'dev-bypass'
  provider_sub TEXT       NOT NULL,        -- external OIDC sub
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE identity.tenant_users (
  tenant_id UUID REFERENCES identity.tenants(tenant_id) ON DELETE CASCADE,
  user_id   UUID REFERENCES identity.users(user_id) ON DELETE CASCADE,
  role      TEXT NOT NULL,                  -- admin, editor, viewer
  PRIMARY KEY (tenant_id, user_id),
  CONSTRAINT uq_tenant_users_user_id UNIQUE (user_id)
);

CREATE TABLE identity.projects (
  project_id  UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID       NOT NULL REFERENCES identity.tenants(tenant_id) ON DELETE CASCADE,
  name        TEXT       NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index to look up all projects for a given tenant
CREATE INDEX idx_projects_tenant_id
  ON identity.projects(tenant_id);


-- 2. Domain Data Schema: Niches & Keywords

CREATE SCHEMA IF NOT EXISTS niches;

CREATE TABLE niches.niches (
  niche_id       UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT       NOT NULL UNIQUE,
  domain         TEXT       NOT NULL UNIQUE,
  default_budget INTEGER    NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE niches.keywords (
  keyword_id  UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
  niche_id    UUID       NOT NULL REFERENCES niches.niches(niche_id) ON DELETE CASCADE,
  name        TEXT       NOT NULL,
  CONSTRAINT uq_keyword_per_niche UNIQUE(niche_id, name),
  CONSTRAINT ck_keyword_not_empty CHECK (name != '')
);

-- Index to fetch all keywords for a niche quickly
CREATE INDEX idx_keywords_niche_id
  ON niches.keywords(niche_id);


-- 3. Integration Profiles (public schema)

CREATE TABLE integration_profiles (
  integration_profile_id UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id            UUID       NOT NULL REFERENCES identity.projects(project_id) ON DELETE CASCADE,
  niche_id              UUID       NOT NULL REFERENCES niches.niches(niche_id) ON DELETE CASCADE,
  channel_key           TEXT       NOT NULL DEFAULT 'pinterest',    -- e.g. 'pinterest'
  settings              JSONB NOT NULL DEFAULT '{}',                 -- prompt templates, budgets, thresholds, schedule
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_integration_profile_combination UNIQUE (project_id, niche_id, channel_key)
);

-- Indexes for common lookups
CREATE INDEX idx_profiles_project_id
  ON integration_profiles(project_id);
CREATE INDEX idx_profiles_niche_id
  ON integration_profiles(niche_id);
CREATE INDEX idx_profiles_channel_key
  ON integration_profiles(channel_key);


-- 4. Contents Schema: Content and Content Publications

CREATE SCHEMA IF NOT EXISTS contents;

-- Content table (channel-agnostic content pieces)
CREATE TABLE contents.contents (
  content_id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  integration_profile_id UUID         REFERENCES integration_profiles(integration_profile_id) ON DELETE SET NULL,
  asset_url              TEXT         NOT NULL,
  title                  TEXT         NOT NULL,
  description            TEXT         NOT NULL,
  hashtags               TEXT[]       NOT NULL DEFAULT '{}',
  status                 TEXT         NOT NULL DEFAULT 'draft',
  created_at             TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT chk_content_status
    CHECK (status IN ('draft','ready', 'failed'))
);

-- Content Publications table (tracks where content was published)
CREATE TABLE contents.content_publications (
  publication_id   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  content_id       UUID         NOT NULL REFERENCES contents.contents(content_id) ON DELETE CASCADE,
  channel_key      TEXT         NOT NULL,
  status           TEXT         NOT NULL DEFAULT 'pending',
  platform_post_id TEXT,
  published_at     TIMESTAMPTZ,
  platform_metadata JSONB       DEFAULT '{}',
  CONSTRAINT chk_publication_status
    CHECK (status IN ('pending','publishing','published','failed'))
);

-- Indexes for contents
CREATE INDEX idx_contents_by_profile
  ON contents.contents(integration_profile_id);
CREATE INDEX idx_contents_by_status
  ON contents.contents(status);

-- Indexes for content_publications
CREATE INDEX idx_content_publications_content_id
  ON contents.content_publications(content_id);
CREATE INDEX idx_content_publications_channel_key
  ON contents.content_publications(channel_key);
CREATE INDEX idx_content_publications_platform_post_id
  ON contents.content_publications(platform_post_id);


-- 5. Analytics Schema: Metrics

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE analytics.metrics (
  id          SERIAL     PRIMARY KEY,
  content_id  UUID       NOT NULL REFERENCES contents.contents(content_id) ON DELETE CASCADE,
  date        DATE       NOT NULL,
  impressions BIGINT     NOT NULL DEFAULT 0,
  clicks      BIGINT     NOT NULL DEFAULT 0,
  saves       BIGINT     NOT NULL DEFAULT 0,
  CONSTRAINT uq_metrics_content_date UNIQUE (content_id, date)
);

-- Index to query metrics by date
CREATE INDEX idx_metrics_date
  ON analytics.metrics(date);
