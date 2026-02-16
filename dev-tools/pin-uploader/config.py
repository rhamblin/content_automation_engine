"""Config loader — reads JSON data file, resolves images + credentials + niche config."""

import base64
import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
MAX_TITLE_LEN = 100
MAX_DESC_LEN = 500


@dataclass(frozen=True)
class RawPinData:
    """Intermediate per-pin data before LLM enrichment."""

    image_b64: str
    content_type: str
    keyword: str
    link: str


@dataclass(frozen=True)
class PinUploadConfig:
    """Validated config from data file + tenant files."""

    tenant: str
    niche: str
    pins: list[RawPinData]
    copy_style_prompt: str
    access_token: str


def _resolve_prompt(value: str | None, base_dir: Path) -> str | None:
    """If value points to a file relative to base_dir, return its contents."""
    if value and (base_dir / value).is_file():
        return (base_dir / value).read_text()
    return value


def _encode_image(path: Path) -> tuple[str, str]:
    """Read image file and return (base64_string, content_type)."""
    ext = path.suffix.lower()
    content_type = "image/png" if ext == ".png" else "image/jpeg"
    return base64.b64encode(path.read_bytes()).decode("utf-8"), content_type


def load_config(data_file: Path) -> PinUploadConfig:
    """Load and validate data file, resolve images, credentials, and niche config."""
    raw = json.loads(data_file.read_text())

    # --- required fields ---
    tenant = raw.get("tenant")
    if not tenant:
        raise ValueError("data file missing required field: tenant")

    niche = raw.get("niche")
    if not niche:
        raise ValueError("data file missing required field: niche")

    pins_raw = raw.get("pins")
    if not pins_raw or not isinstance(pins_raw, list):
        raise ValueError("data file missing required field: pins (non-empty list)")

    input_folder = Path(raw.get("input_folder", ""))
    if not input_folder.is_dir():
        raise ValueError(f"input_folder does not exist: {input_folder}")

    # --- resolve credentials ---
    creds_path = CONFIG_ROOT / tenant / "credentials" / "pinterest.json"
    if not creds_path.exists():
        raise ValueError(f"credentials not found: {creds_path}")

    creds = json.loads(creds_path.read_text())
    access_token = creds.get("access_token", "")
    if not access_token or access_token == "REPLACE_ME":
        raise ValueError("pinterest access_token not configured in credentials")

    # --- resolve niche config + copy_style_prompt ---
    niche_dir = CONFIG_ROOT / tenant / "niches" / niche
    niche_json = niche_dir / f"{niche}.json"
    if not niche_json.exists():
        raise ValueError(f"niche config not found: {niche_json}")

    niche_data = json.loads(niche_json.read_text())
    copy_style_prompt = _resolve_prompt(niche_data.get("copy_style_prompt"), niche_dir) or ""
    if not copy_style_prompt:
        raise ValueError(f"copy_style_prompt not configured for niche: {niche}")

    brand_website = niche_data.get("brand_website", "").rstrip("/")
    if not brand_website:
        raise ValueError(f"brand_website not configured for niche: {niche}")

    # --- resolve pin images ---
    pins: list[RawPinData] = []
    for entry in pins_raw:
        keyword = entry.get("keyword")
        if not keyword:
            raise ValueError("pin missing required field: keyword")

        image_name = entry.get("image")
        if not image_name:
            raise ValueError("pin missing required field: image")

        image_path = input_folder / image_name
        if not image_path.exists():
            raise ValueError(f"image not found: {image_path}")

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"unsupported image format: {image_path.suffix}")

        image_b64, content_type = _encode_image(image_path)

        path = entry.get("path", "")
        link = f"{brand_website}{path}" if path else brand_website

        pins.append(
            RawPinData(
                image_b64=image_b64,
                content_type=content_type,
                keyword=keyword,
                link=link,
            )
        )

    return PinUploadConfig(
        tenant=tenant,
        niche=niche,
        pins=pins,
        copy_style_prompt=copy_style_prompt,
        access_token=access_token,
    )
