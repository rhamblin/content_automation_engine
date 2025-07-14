CREATE TABLE IF NOT EXISTS niches.niches (
  niche_id             UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT       NOT NULL UNIQUE,
  domain         TEXT       NOT NULL UNIQUE,
  default_budget INTEGER    NOT NULL
);

CREATE TABLE IF NOT EXISTS niches.keywords (
  keyword_id    UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
  niche_id      UUID      NOT NULL REFERENCES niches.niches(niche_id) ON DELETE CASCADE,
  keyword       TEXT      NOT NULL,
  UNIQUE(niche_id, keyword)
);

CREATE TABLE IF NOT EXISTS pins.pins (
  pin_id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  keyword_id        UUID         NOT NULL REFERENCES niches.keywords(keyword_id) ON DELETE CASCADE,
  asset_url         TEXT         NOT NULL,
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
  title             TEXT         NOT NULL,
  description       TEXT         NOT NULL,
  hashtags          TEXT[]       NOT NULL,
);

CREATE TABLE IF NOT EXISTS analytics.metrics (
  id          SERIAL    PRIMARY KEY,
  pin_id      UUID      NOT NULL REFERENCES pins.pins(pin_id) ON DELETE CASCADE,
  date        DATE      NOT NULL,
  impressions BIGINT    NOT NULL DEFAULT 0,
  clicks      BIGINT    NOT NULL DEFAULT 0,
  saves       BIGINT    NOT NULL DEFAULT 0,
  UNIQUE(pin_id, date)
);