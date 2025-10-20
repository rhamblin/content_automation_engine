# Content Automation Engine

A modular, multi-tenant platform for AI-driven posts. Phase 1 focuses on Post generation; Phases 2 & 3 add Posting/Ads and Analytics/Pruning.

---

## Data Model

### High-Level Relationships

```mermaid
erDiagram
    tenants ||--o{ tenant_users : has
    users   ||--o{ tenant_users : belongs_to
    tenants ||--o{ projects    : owns
    projects ||--o{ integration_profiles : contains
    niches    ||--o{ keywords      : defines
    niches    ||--o{ integration_profiles : referenced_by
    integration_profiles ||--o{ posts        : generates
    posts      ||--o{ analytics_metrics   : measured_by
```

## Data Objects

- **Tenant** (`identity.tenants`)  
  Represents an isolated customer or organization.

- **User** (`identity.users`)  
  External identity (email + provider) mapped to internal `user_id`.

- **TenantUser** (`identity.tenant_users`)  
  Links a user to a tenant with a specific role (`admin`, `editor`, `viewer`).

- **Project** (`identity.projects`)  
  A workspace under a tenant, grouping integration profiles and posts.

- **Niche** (`niches.niches`)  
  A topical domain (name + domain) with a default budget for content.

- **Keyword** (`niches.keywords`)  
  Individual search terms associated with a niche.

- **IntegrationProfile** (`integration_profiles`)  
  Bundles one niche + one image/model provider + one channel + settings.

- **Post** (`posts.posts`)  
  A generated asset/text item tied to an integration profile and channel.

- **Metric** (`analytics.metrics`)  
  Daily performance data (impressions, clicks, saves) for each post.

### Data Object Tables & Columns

```mermaid
erDiagram
    tenants {
      UUID tenant_id PK
      TEXT name
      TIMESTAMPTZ created_at
    }
    users {
      UUID user_id PK
      TEXT email
      TEXT provider
      TEXT provider_sub
      TIMESTAMPTZ created_at
    }
    tenant_users {
      UUID tenant_id FK
      UUID user_id FK
      TEXT role
    }
    projects {
      UUID project_id PK
      UUID tenant_id FK
      TEXT name
      TIMESTAMPTZ created_at
    }
    niches {
      UUID niche_id PK
      TEXT name
      TEXT domain
      INTEGER default_budget
      TIMESTAMPTZ created_at
    }
    keywords {
      UUID keyword_id PK
      UUID niche_id FK
      TEXT keyword
    }
    integration_profiles {
      UUID integration_profile_id PK
      UUID project_id FK
      UUID niche_id FK
      TEXT image_provider_key
      TEXT text_provider_key
      TEXT channel_key
      JSONB settings
      TIMESTAMPTZ created_at
    }
    posts {
      UUID post_id PK
      UUID integration_profile_id FK
      TEXT asset_url
      TEXT title
      TEXT description
      TEXT[] hashtags
      TEXT status
      TIMESTAMPTZ last_posted_at
      TIMESTAMPTZ created_at
    }
    analytics_metrics {
      SERIAL id PK
      UUID post_id FK
      DATE date
      BIGINT impressions
      BIGINT clicks
      BIGINT saves
    }

    tenants ||--o{ tenant_users : ""
    users   ||--o{ tenant_users : ""
    tenants ||--o{ projects    : ""
    projects ||--o{ integration_profiles : ""
    niches    ||--o{ keywords      : ""
    niches    ||--o{ integration_profiles : ""
    integration_profiles ||--o{ posts        : ""
    posts      ||--o{ analytics_metrics   : ""
```

---

## Getting Started

1. **Download and install Docker Desktop**
    Visit Docker (website)[https://www.docker.com/products/docker-desktop/]
    
2. **Build & run services**  
    Build & run entire application: 
    docker compose --env-file ./config/dev/variables.env up --build -d

    Spin up a single service:
    docker compose --env-file ./config/dev/variables.env up --build -d service_name

    Tear down including volumes
    docker compose --env-file ./config/dev/variables.env down -v

    Tear down while keeping persisted volumes as the same
    docker compose --env-file ./config/dev/variables.env down

3. **See db/init/05-seed-db.sql for sample data**  
  
---

## Important Notes
These are the services in order of dependency. This sequence is important when needing to start a dev container
This should be kept up to date as new containers/services are added and removed
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps db
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps redis
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps post-worker
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps post-dispatcher
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps post-generation-scheduler

---

## Next Steps

- Phase 2: Poster & AdAutomation workers  
- Phase 3: Analytics Capture & Pruner  
- Drop-in new channel by adding a plugin and an `integration_profile` row  
