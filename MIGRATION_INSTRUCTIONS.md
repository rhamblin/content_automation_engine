# Migration: Post → Content & Service Renaming

## Changes Made

### Schema Updates (Pre-MVP)
Updated `db/init/03-create-tables.sql` and `db/init/05-seed-db.sql` to reflect new architecture:

**Renamed:**
- Schema: `posts` → `contents`
- Table: `posts.posts` → `contents.contents`
- Primary key: `post_id` → `content_id`
- Foreign key in metrics: `post_id` → `content_id`

**Status Enum Changed:**
- `generated` → `draft`
- `ready` → `ready` (unchanged)
- `posted` → `archived`
- `error` → removed (now use `archived`)

**Removed Fields:**
- `last_posted_at` (moved to `content_publications.published_at`)

**New Table:**
```sql
contents.content_publications (
  publication_id,
  content_id,
  channel_key,
  platform_post_id,
  published_at,
  platform_metadata
)
```

### Docker Services Renamed
- `post-worker` → `content-generation-worker`
- `post-dispatcher` → `content-generation-dispatcher`
- `post-generation-scheduler` → `content-generation-scheduler`

### Python Classes Renamed
- `PostWorker` → `ContentGenerationWorker`
- Module: `post_worker` → `content_generation_worker`

## Applying Changes

### Option 1: Fresh Start (Recommended for Pre-MVP)
Recreate the database from scratch:

```bash
# Stop and remove existing containers
docker-compose down -v

# Rebuild services with new names
docker-compose build

# Start fresh (will run init scripts automatically)
docker-compose up -d

# Verify tables created
docker exec -it <db-container-name> psql -U appuser -d contentengine_development -c "\dt contents.*"
```

### Option 2: Manual Migration (If you have data to preserve)

If you have existing data in `posts.posts`, run this migration script first:

```sql
-- Connect to database
psql -U appuser -d contentengine_development

-- Run migration
BEGIN;

-- Rename schema
ALTER SCHEMA posts RENAME TO contents;

ALTER TABLE contents.contents RENAME COLUMN post_id TO content_id;
ALTER TABLE contents.contents DROP COLUMN IF EXISTS last_posted_at;

ALTER TABLE analytics.metrics DROP CONSTRAINT IF EXISTS metrics_post_id_fkey;
ALTER TABLE analytics.metrics RENAME COLUMN post_id TO content_id;
ALTER TABLE analytics.metrics DROP CONSTRAINT IF EXISTS uq_metrics_post_date;
ALTER TABLE analytics.metrics ADD CONSTRAINT uq_metrics_content_date UNIQUE (content_id, date);
ALTER TABLE analytics.metrics ADD CONSTRAINT metrics_content_id_fkey
  FOREIGN KEY (content_id) REFERENCES contents.contents(content_id) ON DELETE CASCADE;

-- Update status values
UPDATE contents.contents SET status = 'draft' WHERE status = 'generated';
UPDATE contents.contents SET status = 'archived' WHERE status IN ('posted', 'error');

-- Update constraint
ALTER TABLE contents.contents DROP CONSTRAINT IF EXISTS chk_post_status;
ALTER TABLE contents.contents ADD CONSTRAINT chk_content_status
  CHECK (status IN ('draft','ready','archived'));

-- Create content_publications table
CREATE TABLE contents.content_publications (
  publication_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_id       UUID NOT NULL REFERENCES contents.contents(content_id) ON DELETE CASCADE,
  channel_key      TEXT NOT NULL,
  platform_post_id TEXT,
  published_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  platform_metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_content_publications_content_id ON contents.content_publications(content_id);
CREATE INDEX idx_content_publications_channel_key ON contents.content_publications(channel_key);
CREATE INDEX idx_content_publications_platform_post_id ON contents.content_publications(platform_post_id);

COMMIT;
```

## Verification

```bash
# Check tables
docker exec -it <db-container-name> psql -U appuser -d contentengine_development

# Verify schema
\dt contents.*
\d contents.contents
\d contents.content_publications
\d analytics.metrics
```

Expected output:
- `contents.contents` with `content_id` column
- `contents.content_publications` table exists
- `analytics.metrics` references `content_id`

## Service Verification

```bash
# Rebuild and start services
docker-compose build
docker-compose up -d

# Check services are running
docker-compose ps

# Expected services:
# - content-generation-worker
# - content-generation-dispatcher
# - content-generation-scheduler
```
