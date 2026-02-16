"""Pinterest Pin Uploader — orchestrator (all I/O and wiring lives here)."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.providers.distribution_channel.pinterest import PinterestChannel
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider
from common.workflows.board_manager import BoardItem, BoardManagerService
from common.workflows.pin_uploader import PinItem, PinUploaderService, PinUploadRequest
from common.workflows.title_generator import TitleGeneratorService
from pinterest_auth import get_access_token
from settings import load_dev_settings

from config import load_config

logger = AppLogger(__name__)


def build_draft_board_name(niche: str) -> str:
    """Build secret board name: Draft-Recipes-Feb15-2310."""
    now = datetime.now()
    return f"Draft-{niche.title()}-{now.strftime('%b%d-%H%M')}"


def build_hashtags(niche: str, keyword: str) -> str:
    """Build hashtag string from niche and keyword."""
    tag = keyword.title().replace(" ", "")
    return f"#{niche} #{tag}"


def generate_copy(
    title_svc: TitleGeneratorService,
    niche: str,
    keyword: str,
    copy_style_prompt: str,
) -> dict:
    """Generate title, description, alt_text via LLM.

    Returns:
        dict with keys: title, description, alt_text
    """
    result = title_svc.generate(
        niche=niche,
        keyword=keyword,
        count=1,
        copy_style_prompt=copy_style_prompt,
    )

    if result.error:
        raise RuntimeError(f"LLM error for '{keyword}': {result.error}")

    if not result.options:
        raise RuntimeError(f"LLM returned no options for '{keyword}'")

    option = result.options[0]
    return {
        "title": option.title,
        "description": option.description,
        "alt_text": getattr(option, "alt_text", ""),
    }


def main():
    data_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not data_file:
        print("Usage: python -m pin-uploader data/example.json")
        sys.exit(1)

    # Layer 2: load + validate config
    config = load_config(data_file)
    logger.info(
        f"Loaded {len(config.pins)} pins for niche '{config.niche}' (tenant: {config.tenant})"
    )

    # Wire up providers
    settings = load_dev_settings()
    access_token = get_access_token(config.tenant)
    channel = PinterestChannel(access_token=access_token)

    azure_client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    llm = AzureFoundryLLMProvider(azure_client)
    title_svc = TitleGeneratorService(llm=llm, channel=channel)
    service = PinUploaderService(channel)

    # Create secret draft board via BoardManagerService
    draft_name = build_draft_board_name(config.niche)
    logger.info(f"Creating secret board: {draft_name}")
    board_svc = BoardManagerService(channel)
    board_result = board_svc.create_board(BoardItem(name=draft_name, privacy="SECRET"))
    if not board_result.ok:
        logger.error(f"Failed to create draft board: {board_result.error}")
        sys.exit(1)
    draft_board_id = board_result.board_id
    logger.info(f"Draft board created: {board_result.url}")

    # Build PinItems: generate copy per pin, append hashtags, target draft board
    pin_items: list[PinItem] = []
    for raw_pin in config.pins:
        logger.info(f"Generating copy for keyword: {raw_pin.keyword}")
        try:
            copy = generate_copy(
                title_svc=title_svc,
                niche=config.niche,
                keyword=raw_pin.keyword,
                copy_style_prompt=config.copy_style_prompt,
            )
            hashtags = build_hashtags(config.niche, raw_pin.keyword)
            description = f"{copy['description']} {hashtags}"

            pin_items.append(
                PinItem(
                    board_id=draft_board_id,
                    image_b64=raw_pin.image_b64,
                    content_type=raw_pin.content_type,
                    title=copy["title"],
                    description=description,
                    link=raw_pin.link,
                    alt_text=copy.get("alt_text"),
                )
            )
            logger.info(f"  Title: {copy['title']}")
            logger.info(f"  Desc:  {description[:80]}...")

        except Exception as e:
            logger.error(f"  Skipping '{raw_pin.keyword}': {e}")

    if not pin_items:
        logger.error("No pins to upload")
        sys.exit(1)

    # Upload to draft board
    logger.info(f"Uploading {len(pin_items)} pins to draft board '{draft_name}'...")
    response = service.upload(PinUploadRequest(pins=pin_items))

    # Summary
    print(f"\n{'='*50}")
    print(f"Draft board: {draft_name} ({board_result.url})")
    print(f"Upload complete: {response.succeeded}/{response.total} succeeded")
    for r in response.results:
        status = f"OK {r.url}" if r.ok else f"FAILED: {r.error}"
        print(f"  {r.title} — {status}")
    print(f"{'='*50}")
    print("\nReview pins on the secret board, then move to public boards when ready.")


if __name__ == "__main__":
    main()
