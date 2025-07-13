CREATE TABLE IF NOT EXISTS niches.niches (
  id             UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT       NOT NULL UNIQUE,
  default_budget INTEGER    NOT NULL
);

CREATE TABLE IF NOT EXISTS pins.pins (
  pin_id     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  niche_id   UUID         NOT NULL REFERENCES niches.niches(id) ON DELETE CASCADE,
  object_store_key     TEXT         NOT NULL,
  created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
  title      TEXT,
  description TEXT,
  hashtags   TEXT[]
);

CREATE TABLE IF NOT EXISTS analytics.metrics (
  id          SERIAL    PRIMARY KEY,
  pin_id      UUID      NOT NULL REFERENCES pins.pins(pin_id) ON DELETE CASCADE,
  niche_id    UUID      NOT NULL,
  date        DATE      NOT NULL,
  impressions BIGINT    NOT NULL,
  clicks      BIGINT    NOT NULL,
  saves       BIGINT    NOT NULL
);