# Title Generator

Generates AI-powered titles and descriptions for content given a channel, niche, and keyword. Outputs multiple variations with different styles (clickbait, professional, SEO-focused).

## Keyword Sourcing

Keywords are read from the **niche config** (`config/tenants/<tenant>/niches/<niche>/<niche>.json`), not from the data file.

- Keywords with `active: false` are filtered out.
- Keywords **without a `blog_url`** are skipped (with a warning log).
- If a keyword has `reference_images`, a random image from that folder is picked and sent to the LLM for grounding.

## Data File (`data/input.json`)

```json
{
  "tenant": "dev-tenant",
  "channel": "pinterest",
  "niche": "kitchen_appliances"
}
```

| Field     | Required | Description                        |
|-----------|----------|------------------------------------|
| `tenant`  | yes      | Tenant identifier                  |
| `channel` | yes      | Target channel (pinterest, etc.)   |
| `niche`   | yes      | Niche name matching config folder  |

## Niche Config Keyword Schema

```json
{
  "term": "Gourmet french door air fryer review",
  "intent": "buyer",
  "amazon_monetization_angle": "Gourmet french door air fryer",
  "active": true,
  "blog_url": "https://chefexotic.com/shop/",
  "reference_images": "/absolute/path/to/images/keyword-slug"
}
```

- `active` — boolean. Keywords with `false` are skipped by all dev tools.
- `blog_url` — optional. Keywords without it are skipped by title-generator.
- `reference_images` — optional. Absolute path to a folder of source images for LLM grounding.

## Usage

```bash
make title-generator
```
