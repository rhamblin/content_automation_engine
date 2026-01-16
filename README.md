# Content Automation Engine

A modular, multi-tenant platform for AI-driven posts. Phase 1 focuses on Content generation; Phases 2 & 3 add Posting/Ads and Analytics/Pruning.

See system diagram for full context of system design. (Doc)[./doc_assets/system-diagram.png]

## Dev Onboarding

The following applications are requirements
- (VS Code)[https://code.visualstudio.com/download]
- (Docker Desktop)[https://docs.docker.com/desktop/#next-steps]
- (Microsoft Azure Storage Explorer)[https://azure.microsoft.com/en-us/products/storage/storage-explorer#Download-4]
- Git e.g. (GitHub Desktop)[https://github.com/apps/desktop]

## Onboarding a Niche and Keywords
The Niche API can be used to add a net new Niche or to add a keyword to a niche

Once it has been onboarded then a folder with the UUID must be made in the blob storage and images to be used uploaded there.

When making a publication to a channel, this structure is expected to be inplace for a given keyword. If UUID changes then a renaming of folders in blob storage must occur. The keyword_name2.txt file just keeps the human-readable keyword name to aid in cases where UUID changes and a mapping needs to be reestablished.

images/
  keywords/
    keyword_uuid_1/
      keyword_name1.txt
      img1.png
      img2.png
    keyword_uuid_2/
      keyword_name2.txt
      img1.png
      img2.png
      img3.png

## Getting Started For Local Development

1. **Download and install Docker Desktop**
    Visit Docker (website)[https://www.docker.com/products/docker-desktop/]

2. **Ensure the following API keys / secrets are in place under <<APP ROOT>>/secrets**
    azure-blob-storage-connection-string.txt
    azure-foundry-proj-default-api-key.txt
    openai-api-key.txt

3. **Build & run services**
```bash
    # Build & run entire application:
    docker compose --env-file ./config/dev/variables.env up --build -d

    # Spin up a single service:
    docker compose --env-file ./config/dev/variables.env up --build -d service_name

    # Tear down everything including volumes
    docker compose --env-file ./config/dev/variables.env down -v

    # Tear down everything while keeping persisted volumes as the same
    docker compose --env-file ./config/dev/variables.env down
```
1. **See db/init/05-seed-db.sql for sample data**

## Testing

The project uses pytest with containerized dependencies for isolated test execution. Any file that matches *_test.py in repo is considered a test however structurally all tests live under ./test directory

### Running Tests

```bash
# Run all tests
docker compose --env-file ./config/dev/variables.env --profile test run --rm test-runner

# Run specific test file
docker compose --env-file ./config/dev/variables.env --profile test run --rm test-runner pytest test/common/db_core/models/user_test.py -v

# Rebuild test container after dependency changes
docker compose --env-file ./config/dev/variables.env --profile test build test-runner
```

### Test Architecture

- **Test fixtures**: `test/conftest.py` - Uses testcontainers to spin up isolated PostgreSQL instances
- **Test dependencies**: `test/requirements.txt` - Isolated from service dependencies
- **Test container**: `test/Dockerfile` - Self-contained test environment

The test runner has access to:
- All common modules (db_core, providers, etc.)
- Docker socket for testcontainers

## Debugging and Dev Containers
### Steps
1.	Define a devcontainer.json which defines how that container will be spun up. The route our project is going with is by using the service’s Dockerfile directly so that means any special configurations done in the project root docker-compose needs to be replicated e.g. environment variables, networks (a1) . Also ensure any env file is also included and dependent packages are loaded
2.	The service being ran in dev container is ran separate to other so this means the developer at this moment has to manually start up services in the right order as seen in Dependency Order below
```bash
# These are the services in order of dependency. This sequence is important when needing to start a dev container
# This should be kept up to date as new containers/services are added and removed
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps db
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps redis
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps content-generation-worker
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps content-generation-dispatcher
  docker compose --env-file ./config/dev/variables.env up --build -d --no-deps content-generation-scheduler
```
3.	Ensure Dev Containers extension is installed
4.	Startup containers in right order via terminal and “Reopen in container” for the container you want to debug. YOU CAN TYPE ">Dev Containers:Reopen In Container" in VS Code
5.	Start Python Debugger via the following command
```bash
PYTHONPATH=/app/services/content-generation-worker/app:/app/common:/app python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m content_generation_worker.app
```
6.	Run -> Start Debugging : if launch.json file is not already in place then select Python Debugger -> Remote Attach -> localhost -> 5678 (or what ever is configured in devcontainer.json)
7.	Happy Debugging!


*a1 On the note of networks, my early research shows that in its simplest form you can only connect to one network without extra steps so I made a special development network for ease of local development*

### Tracking Logs On Local

Once docker containers are running you can track logs by running
```bash
make logs
```

## Assumptions made
1.  Channel is being passed into common/providers/text/azure_foundry.py generate_text method which is the implementation of the interface but we don't use it as of yet.The system messages was tailored to be Pinterest centric. This can be decoupled at a later time if expansion to other channels is desired. **Currently, Pinterest is the only supported channel**

## Data Model

### Entity Relationship Diagram

```mermaid
erDiagram
  tenants       ||--o{  tenants_users : "has"
  users         ||--|{  tenants_users : belongs_to
  users         ||--o{  users_identity_providers: integrates_with
  tenants       ||--o{  tenants_identity_providers : integrates_with
  tenants       ||--o{  projects : manages
  tenants       ||--o{  reports  : receives
  tenants       ||--o{  schedules: works_based_on
  projects      ||--o{  integration_profiles : configures
  niches        ||--o{  integration_profiles : targeted_by
  niches        ||--|{  keywords : defines
  keywords      ||--|{  images : generates
  keywords      ||--o{  contents : produces
  images        ||--o{  renders: styles_into
  contents      ||--o{  renders: styles_into
  channels      ||--o{  tenants_channels: available_to
  channels      ||--o{  integration_profiles: configured_in
  channels      ||--o{  publications: distributes
  renders       ||--o{  publications: published_in
  contents      ||--o{  publications: published_in
  publications  ||--o{  promotions: promoted_via
  publications  ||--o{  publication_metrics: performs
  schedules     ||--o{  schedule_executions: triggers

  tenants {
    uuid id pk
    uuid external_id
    text title
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% Unique constraint: (external_id)
  }

  users {
    uuid id pk
    uuid external_id
    boolean is_active
    text email
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% Unique constraints: (external_id), (email)
  }

  channels {
    uuid id pk
    uuid external_id
    text  identifier
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% Unique constraints: (external_id), (identifier)
  }

  %% The section below are junction tables
  tenants_users {
    uuid  tenant_id fk
    uuid  user_id fk
    string  role
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% This Juction table needs a unique constraint of (tenant_id, user_id)
  }

  users_identity_providers {
    uuid user_id  fk
    uuid identity_provider_user_id
    text identity_provider
    timestamp created_at
    %% This Juction table needs a unique constraint of (identity_provider_user_id, user_id)
  }

  tenants_identity_providers {
    uuid tenant_id  fk
    uuid identity_provider_tenant_id
    text identity_provider
    timestamp created_at
    %% This Juction table needs a unique constraint of (identity_provider_tenant_id, user_id)
  }

  tenants_channels {
    uuid tenant_id  fk
    uuid  channel_id
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% This Juction table needs a unique constraint of (tenant_id, channel_id)
  }
  %% This is the end of the junction tables sections

  projects {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    text name
    boolean is_active
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% Unique constraints: (external_id), (tenant_id, name)
  }

  reports {
    uuid id  pk
    uuid external_id
    uuid tenant_id fk
    jsonb content
    text[] recipients
    timestamp created_at
    %% Unique constraint: (external_id)
  }

  integration_profiles {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid niche_id fk %% Used to denormalize data and aid in faster queries without joins
    uuid project_id fk
    uuid channel_id fk
    boolean is_active
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% Unique constraints: (external_id), (project_id, niche_id, channel_id)
  }

  niches {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    text title
    boolean is_active
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% Unique constraints: (external_id), (tenant_id, title)
  }

  keywords {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid  niche_id  fk
    text  term
    boolean is_active
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% Unique constraints: (external_id), (niche_id, term)
  }

  images {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid  niche_id  fk %% Used to denormalize data and aid in faster queries without joins
    uuid  keyword_id  fk %% Used to denormalize data and aid in faster queries without joins
    text  kind %% This is an ENUM
    timestamp created_at
    %% Unique constraint: (external_id)
  }

  contents {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid  niche_id  fk %% Used to denormalize data and aid in faster queries without joins
    uuid  keyword_id  fk %% Used to denormalize data and aid in faster queries without joins
    text  title
    text  description
    timestamp created_at
    %% Unique constraint: (external_id)
  }

  renders {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid  content_id fk
    uuid  niche_id  fk %% Used to denormalize data and aid in faster queries without joins
    uuid  keyword_id  fk %% Used to denormalize data and aid in faster queries without joins
    uuid  input_image_id  fk
    uuid  output_image_id fk
    text  style_name
    text  status %% This is an ENUM
    timestamp created_at
    %% Unique constraint: (external_id)
  }

  publications {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid  render_id fk
    uuid  channel_id  fk
    uuid  content_id  fk
    text  post_id %% The ID from channel after posting
    text  status %% This is an ENUM
    timestamp created_at
    %% Unique constraint: (external_id)
  }

  promotions {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid  publication_id  fk
    uuid  channel_id  fk
    jsonb payload %% Channel specific API parameters
    text  action_taken %% This is an ENUM
    text  status %% This is an ENUM
    timestamp created_at
    timestamp executed_at
    %% Unique constraint: (external_id)
  }

  publication_metrics {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid  publication_id  fk
    uuid  channel_id  fk
    timestamp snapshot_date
    jsonb metrics
    timestamp fetched_at
    %% Unique constraints: (external_id), (publication_id, snapshot_date)
  }

  schedules {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid niche_id fk
    boolean is_active
    text  title
    text  cron_expression
    text  message_type %% This is an ENUM
    text  message_payload
    timestamp last_run_at
    timestamp next_run_at
    timestamp created_at
    uuid  created_by
    timestamp updated_at
    uuid  updated_by
    %% Unique constraint: (external_id)
  }

  schedule_executions {
    uuid id pk
    uuid external_id
    uuid tenant_id fk
    uuid schedule_id  fk
    uuid  niche_id  fk %% Used to denormalize data and aid in faster queries without joins
    uuid  keyword_id  fk %% Used to denormalize data and aid in faster queries without joins
    text  status %% This is an ENUM
    timestamp started_at
    timestamp completed_at
    %% Unique constraint: (external_id)
  }

```
