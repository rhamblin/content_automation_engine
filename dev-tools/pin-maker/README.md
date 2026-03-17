# Pin Maker

Creates Pinterest-optimized pin images with text overlays from source images. Applies consistent branding and styling.

## Keyword Sourcing

Keywords are read from the **niche config** (`config/tenants/<tenant>/niches/<niche>/<niche>.json`). Keywords with `"status": "disabled"` are skipped automatically.

## Input Structure

The `input_folder` must contain **one subfolder per keyword**, named as the keyword slug (lowercase, spaces → hyphens):

```
input_folder/
├── brown-sugar-boba-tea-recipe/
│   ├── photo1.jpg
│   └── photo2.png
├── matcha-bubble-tea-recipe/
│   └── matcha1.jpg
└── mango-mocktail-recipe/
    └── mango_glass.webp
```

Keywords without a matching subfolder (or with an empty subfolder) are skipped with a warning.

## Data File (`data/input.json`)

```json
{
  "niche": "recipes",
  "locale": "en",
  "styles": "product_review",
  "input_folder": "/absolute/path/to/images"
}
```

| Field          | Required | Description                                      |
|----------------|----------|--------------------------------------------------|
| `niche`        | No       | Niche name (default: `food`)                     |
| `locale`       | No       | `en` / `es` / `sw` (default: `en`)               |
| `styles`       | No       | Style name or list; omit for random from all      |
| `input_folder` | **Yes**  | Path to folder with keyword subfolders            |

## Output

A timestamped output folder is created as a sibling of `input_folder`:

```
images/
├── recipes/            ← input_folder
│   └── brown-sugar.../
└── output-20260317-143022/
    ├── photo1_product_review.jpg
    ├── matcha1_listicle.jpg
    └── manifest.json
```

### `manifest.json`

```json
[
  {
    "keyword": "brown sugar boba tea recipe",
    "style_name": "product_review",
    "output_file": "photo1_product_review.jpg",
    "source_image": "/absolute/path/to/photo1.jpg"
  }
]
```

## Usage

```bash
make pin-maker          # uses default data/input.json
# or
python pin_maker.py data/input.json
python pin_maker.py --list-styles
```
