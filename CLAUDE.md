# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This is a modular, multi-tenant content automation platform built with microservices architecture. The system generates AI-driven posts for social media platforms using a provider-based approach.

### Core Components

- **Services Directory (`services/`)**: Contains microservices written in Python using FastAPI
  - `post-worker`: Handles post generation using AI providers (OpenAI, Unsplash)
  - `post-dispatcher`: FastAPI service that dispatches jobs to workers via Redis
  - `post-generation-scheduler`: Schedules post generation tasks
  - `entity-apis`: RESTful APIs for managing entities (niches, projects, etc.)

- **Common Directory (`common/`)**: Shared code across services
  - `db_core/`: Database models and connection utilities using SQLAlchemy
  - `providers/`: Plugin-based provider system for AI services (text, image, channels)
  - `constants/`: Shared constants including Redis queue names

- **Database**: PostgreSQL with multi-schema design:
  - `identity` schema: tenants, users, projects
  - `niches` schema: content domains and keywords
  - `posts` schema: generated content
  - `analytics` schema: performance metrics

### Provider System

The platform uses a registry-based provider system (`common/providers/registry.py`):
- **Image Providers**: Currently supports Unsplash
- **Text Providers**: Currently supports OpenAI
- **Channels**: Currently supports Pinterest

Add new providers by implementing base interfaces and registering in `registry.py`.

## Development Commands

### Docker Operations
```bash
# Build and run entire application
docker compose --env-file ./config/dev/variables.env up --build -d

# Run single service
docker compose --env-file ./config/dev/variables.env up --build -d service_name

# Tear down with volumes
docker compose --env-file ./config/dev/variables.env down -v

# Tear down keeping volumes
docker compose --env-file ./config/dev/variables.env down
```

### Database
- Database initialization scripts: `db/init/`
- Sample data: `db/init/05-seed-db.sql`
- Direct PostgreSQL access: `localhost:5432`

### Service Architecture
- All services use Redis for inter-service communication
- Post generation workflow: scheduler → dispatcher → worker → Redis queue
- Services depend on shared `db_core` package for database operations

## Key File Locations

- Service requirements: `services/*/requirements.txt`
- Docker configurations: `services/*/Dockerfile`
- Database models: `common/db_core/models.py`
- Provider interfaces: `common/providers/base.py`
- Environment variables: `config/dev/variables.env`
- API secrets: `secrets/` directory

## Current Development Status

- Phase 1: Post generation (active services: post-worker, post-dispatcher, post-generation-scheduler)
- Phase 2: Posting/Ads automation (commented out in docker-compose.yaml)
- Phase 3: Analytics/Pruning (commented out in docker-compose.yaml)