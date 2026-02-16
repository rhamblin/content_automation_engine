"""Seed worker — loads tenant config from config/tenants/ into the database.

Reads JSON files from the tenant folder structure and upserts via
async SQLAlchemy repositories so the same data-access code is reusable
by HTTP API handlers.

Usage:
    python seed.py                          # default: config/tenants/
    python seed.py /path/to/tenants/dir     # custom tenants root
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

# Ensure common package is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common" / "src"))

from azure.storage.blob import BlobServiceClient

from common.app_logger import AppLogger
from common.providers.database.sqlalchemy import SQLAlchemyDatabaseProvider
from common.repositories.cross_tenant import TenantRepository, ChannelRepository
from common.repositories.tenant_scoped import (
    NicheRepository,
    IntegrationProfileRepository,
    ScheduleRepository,
    StyleRepository,
    ChannelCredentialRepository,
)
from common.contracts.database_models import Keyword, Schedule
from common.workflows.seed_images import SeedImageService

logger = AppLogger("seed-worker")


def _resolve_prompt(value: str | None, base_dir: Path) -> str | None:
    """If value points to a file relative to base_dir, return its contents."""
    if value and (base_dir / value).is_file():
        return (base_dir / value).read_text()
    return value


# ── Loaders ──────────────────────────────────────────────────────────────────


async def load_tenant(session: AsyncSession, tenant_dir: Path) -> UUID:
    """Load tenant.json → upsert tenant row. Returns tenant external_id."""
    data = json.loads((tenant_dir / "tenant.json").read_text())
    repo = TenantRepository(session)
    existing = await repo.get_by_title(data["title"])
    if existing:
        logger.info(f"Tenant '{data['title']}' exists: {existing.external_id}")
        return existing.external_id
    tenant = await repo.add(data["title"])
    logger.info(f"Created tenant '{data['title']}': {tenant.external_id}")
    return tenant.external_id


async def ensure_channels(session: AsyncSession, tenant_dir: Path) -> dict[str, UUID]:
    """Scan styles/ and credentials/ dirs to discover channels, upsert them.
    Returns mapping of channel identifier → external_id."""
    channel_ids: set[str] = set()

    styles_dir = tenant_dir / "styles"
    if styles_dir.exists():
        for d in styles_dir.iterdir():
            if d.is_dir():
                channel_ids.add(d.name)

    creds_dir = tenant_dir / "credentials"
    if creds_dir.exists():
        for f in creds_dir.glob("*.json"):
            channel_ids.add(f.stem)

    repo = ChannelRepository(session)
    result = {}
    for identifier in channel_ids:
        channel = await repo.get_or_create_by_identifier(identifier)
        result[identifier] = channel.external_id
        logger.info(f"Channel '{identifier}': {channel.external_id}")
    return result


async def link_tenant_channels(
    session: AsyncSession, tenant_id: UUID, channel_map: dict[str, UUID]
) -> None:
    """Ensure tenants_channels rows exist."""
    repo = TenantRepository(session)
    existing = await repo.get_tenant_channels(tenant_id)
    existing_channel_ids = {tc.channel_id for tc in existing}

    from common.contracts.database_models import TenantsChannels

    for identifier, channel_id in channel_map.items():
        if channel_id not in existing_channel_ids:
            tc = TenantsChannels(tenant_id=tenant_id, channel_id=channel_id)
            await repo.add_channel_to_tenant(tc)
            logger.info(f"Linked tenant to channel '{identifier}'")


async def load_niches(
    session: AsyncSession,
    tenant_id: UUID,
    tenant_dir: Path,
    channel_map: dict[str, UUID],
) -> dict[str, UUID]:
    """Load niches/<name>/<name>.json → upsert niches + keywords + integration profiles.
    Returns mapping of niche title → external_id."""
    niches_dir = tenant_dir / "niches"
    if not niches_dir.exists():
        return {}

    niche_repo = NicheRepository(session, tenant_id)
    profile_repo = IntegrationProfileRepository(session, tenant_id)
    niche_map: dict[str, UUID] = {}

    for niche_dir in sorted(niches_dir.iterdir()):
        if not niche_dir.is_dir():
            continue
        json_file = niche_dir / f"{niche_dir.name}.json"
        if not json_file.exists():
            logger.warning(f"No {niche_dir.name}.json in {niche_dir}, skipping")
            continue

        data = json.loads(json_file.read_text())
        title = data["title"]
        base_dir = niche_dir

        # Resolve file-ref prompts to full text
        persona_prompt = _resolve_prompt(data.get("persona_prompt"), base_dir)
        copy_style_prompt = _resolve_prompt(data.get("copy_style_prompt"), base_dir)

        channel_prompts_raw = data.get("channel_prompts") or {}
        channel_prompts: dict[str, str] = {}
        for ch, ref in channel_prompts_raw.items():
            resolved = _resolve_prompt(ref, base_dir)
            if resolved:
                channel_prompts[ch] = resolved

        niche = await niche_repo.upsert(
            title=title,
            brand_name=data.get("brand_name"),
            brand_website=data.get("brand_website"),
            brand_watermark=data.get("brand_watermark"),
            persona_name=data.get("persona_name"),
            persona_prompt=persona_prompt,
            copy_style_prompt=copy_style_prompt,
            channel_prompts=channel_prompts or None,
        )
        niche_map[title] = niche.external_id
        logger.info(f"Niche '{title}': {niche.external_id}")

        # Upsert keywords
        for term in data.get("keywords", []):
            existing_kw = await niche_repo.get_keyword_by_term(niche.external_id, term)
            if not existing_kw:
                kw = Keyword(
                    tenant_id=tenant_id,
                    niche_id=niche.external_id,
                    term=term,
                )
                await niche_repo.add_keyword(kw)
                logger.info(f"  Keyword '{term}'")

        # Create integration profiles for each channel
        for identifier, channel_id in channel_map.items():
            existing_profile = await profile_repo.get_by_niche_and_channel(
                niche.external_id, channel_id
            )
            if not existing_profile:
                await profile_repo.add(niche.external_id, channel_id)
                logger.info(f"  Integration profile: {title} × {identifier}")

    return niche_map


async def load_styles(
    session: AsyncSession, tenant_id: UUID, tenant_dir: Path, channel_map: dict[str, UUID]
) -> None:
    """Load styles/<channel>/*.json → upsert style rows."""
    styles_dir = tenant_dir / "styles"
    if not styles_dir.exists():
        return

    repo = StyleRepository(session, tenant_id)
    for channel_dir in sorted(styles_dir.iterdir()):
        if not channel_dir.is_dir():
            continue
        channel_id = channel_map.get(channel_dir.name)
        if not channel_id:
            logger.warning(f"Unknown channel '{channel_dir.name}' in styles/, skipping")
            continue

        for f in sorted(channel_dir.glob("*.json")):
            data = json.loads(f.read_text())
            await repo.upsert(
                channel_id=channel_id,
                name=data["name"],
                description=data.get("description"),
                spec=data["spec"],
            )
            logger.info(f"Style '{data['name']}' for {channel_dir.name}")


async def load_credentials(
    session: AsyncSession, tenant_id: UUID, tenant_dir: Path, channel_map: dict[str, UUID]
) -> None:
    """Load credentials/*.json → upsert channel_credentials rows."""
    creds_dir = tenant_dir / "credentials"
    if not creds_dir.exists():
        return

    repo = ChannelCredentialRepository(session, tenant_id)
    for f in sorted(creds_dir.glob("*.json")):
        data = json.loads(f.read_text())
        channel_identifier = data.get("channel", f.stem)
        channel_id = channel_map.get(channel_identifier)
        if not channel_id:
            logger.warning(f"Unknown channel '{channel_identifier}' in credentials/, skipping")
            continue

        # Strip the "channel" key from credentials payload before storing
        cred_payload = {k: v for k, v in data.items() if k != "channel"}
        await repo.upsert(channel_id=channel_id, credentials=cred_payload)
        logger.info(f"Credentials for '{channel_identifier}'")


async def load_schedules(
    session: AsyncSession, tenant_id: UUID, tenant_dir: Path, channel_map: dict[str, UUID]
) -> None:
    """Load schedules.json → upsert schedule rows."""
    schedules_file = tenant_dir / "schedules.json"
    if not schedules_file.exists():
        return

    data = json.loads(schedules_file.read_text())
    repo = ScheduleRepository(session, tenant_id)

    for entry in data:
        message_type = entry["message_type"]
        # Check if schedule already exists for this message type
        existing = await repo.get_by_message_type(message_type)
        if existing:
            logger.info(f"Schedule '{message_type}' already exists, skipping")
            continue

        schedule = Schedule(
            tenant_id=tenant_id,
            cron_expression=entry["cron_expression"],
            message_type=message_type,
        )
        session.add(schedule)
        await session.flush()
        logger.info(f"Schedule '{message_type}': {entry['cron_expression']}")


def _load_niche_title(niche_dir: Path) -> str | None:
    """Read niche title from its JSON config."""
    json_file = niche_dir / f"{niche_dir.name}.json"
    if not json_file.exists():
        return None
    return json.loads(json_file.read_text()).get("title")


# ── Main ─────────────────────────────────────────────────────────────────────


async def seed(tenants_root: Path) -> None:
    """Process all tenant folders under tenants_root."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    blob_conn = os.environ.get("AZURE_BLOB_STORAGE_CONNECTION_STRING")
    blob_client = BlobServiceClient.from_connection_string(blob_conn) if blob_conn else None

    database = SQLAlchemyDatabaseProvider(db_url)

    for tenant_dir in sorted(tenants_root.iterdir()):
        if not tenant_dir.is_dir() or not (tenant_dir / "tenant.json").exists():
            continue

        logger.info(f"Seeding tenant: {tenant_dir.name}")

        async with database.get_session() as session:
            # Dependency-ordered processing
            tenant_id = await load_tenant(session, tenant_dir)
            channel_map = await ensure_channels(session, tenant_dir)
            await link_tenant_channels(session, tenant_id, channel_map)
            niche_map = await load_niches(session, tenant_id, tenant_dir, channel_map)
            await load_styles(session, tenant_id, tenant_dir, channel_map)
            await load_credentials(session, tenant_id, tenant_dir, channel_map)
            await load_schedules(session, tenant_id, tenant_dir, channel_map)

            await session.commit()
            logger.info(f"Tenant '{tenant_dir.name}' seeded successfully")

            # Upload seed images (after commit so keywords exist)
            if blob_client and niche_map:
                image_service = SeedImageService(blob_client, session)
                niches_dir = tenant_dir / "niches"
                for niche_dir in sorted(niches_dir.iterdir()):
                    if not niche_dir.is_dir():
                        continue
                    niche_title = _load_niche_title(niche_dir)
                    niche_id = niche_map.get(niche_title) if niche_title else None
                    if niche_id:
                        count = await image_service.upload_niche_seed_images(
                            tenant_id, niche_id, niche_dir
                        )
                        if count:
                            logger.info(f"Uploaded {count} seed images for '{niche_title}'")
            elif not blob_conn:
                logger.warning("AZURE_BLOB_STORAGE_CONNECTION_STRING not set, skipping seed images")

    await database.close_connection()


def main():
    if len(sys.argv) > 1:
        tenants_root = Path(sys.argv[1])
    else:
        tenants_root = Path(__file__).parent.parent.parent / "config" / "tenants"

    if not tenants_root.exists():
        logger.error(f"Tenants directory not found: {tenants_root}")
        sys.exit(1)

    logger.info(f"Tenants root: {tenants_root}")
    asyncio.run(seed(tenants_root))
    logger.info("Seed complete")


if __name__ == "__main__":
    main()
