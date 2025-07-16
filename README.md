# Content Automation Engine

A modular, multi-tenant platform for AI-driven posts. Phase 1 focuses on Post generation; Phases 2 & 3 add Posting/Ads and Analytics/Pruning.

---

## Data Model

### High-Level Relationships


```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```

```mermaid
erDiagram
    identity.tenants ||--o{ identity.tenant_users : has
    identity.users   ||--o{ identity.tenant_users : belongs_to
    identity.tenants ||--o{ identity.projects    : owns
    identity.projects ||--o{ integration_profiles : contains
    niches.niches    ||--o{ niches.keywords      : defines
    niches.niches    ||--o{ integration_profiles : referenced_by
    integration_profiles ||--o{ posts.posts        : generates
    posts.posts      ||--o{ analytics.metrics   : measured_by
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
    identity.tenants {
      UUID tenant_id PK
      TEXT name
      TIMESTAMPTZ created_at
    }
    identity.users {
      UUID user_id PK
      TEXT email
      TEXT provider
      TEXT provider_sub
      TIMESTAMPTZ created_at
    }
    identity.tenant_users {
      UUID tenant_id FK
      UUID user_id FK
      TEXT role
    }
    identity.projects {
      UUID project_id PK
      UUID tenant_id FK
      TEXT name
      TIMESTAMPTZ created_at
    }
    niches.niches {
      UUID niche_id PK
      TEXT name
      TEXT domain
      INTEGER default_budget
      TIMESTAMPTZ created_at
    }
    niches.keywords {
      UUID keyword_id PK
      UUID niche_id FK
      TEXT keyword
    }
    integration_profiles {
      UUID integration_profile_id PK
      UUID project_id FK
      UUID niche_id FK
      TEXT image_provider_key
      TEXT model_provider_key
      TEXT channel_key
      JSONB settings
      TIMESTAMPTZ created_at
    }
    posts.posts {
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
    analytics.metrics {
      SERIAL id PK
      UUID post_id FK
      DATE date
      BIGINT impressions
      BIGINT clicks
      BIGINT saves
    }

    identity.tenants ||--o{ identity.tenant_users : ""
    identity.users   ||--o{ identity.tenant_users : ""
    identity.tenants ||--o{ identity.projects    : ""
    identity.projects ||--o{ integration_profiles : ""
    niches.niches    ||--o{ niches.keywords      : ""
    niches.niches    ||--o{ integration_profiles : ""
    integration_profiles ||--o{ posts.posts        : ""
    posts.posts      ||--o{ analytics.metrics   : ""
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

2. **See db/init/05-seed-db.sql for sample data**  
  
---

## Next Steps

- Phase 2: Poster & AdAutomation workers  
- Phase 3: Analytics Capture & Pruner  
- Drop-in new channel by adding a plugin and an `integration_profile` row  
