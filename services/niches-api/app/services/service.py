"""
Implements all database operations for niches and keywords using SQLAlchemy ORM.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from uuid import UUID
from db_core.models.niche import Niche
from db_core.models.keyword import Keyword
from app.schemas.schema import (
    NicheCreate, NicheUpdate,
    KeywordCreate, KeywordUpdate
)

# --- Niche Services ---

async def get_all_niches(db: AsyncSession):
    result = await db.execute(select(Niche).order_by(Niche.name).options(selectinload(Niche.keywords)))
    return result.scalars().all()

async def create_niche(db: AsyncSession, data: NicheCreate):
    new_niche = Niche(
        name=data.name,
        domain=data.domain,
        default_budget=data.default_budget,
        keywords=[Keyword(keyword=kw.keyword) for kw in data.keywords or []]
    )
    db.add(new_niche)
    await db.commit()

    # Re-fetch with keywords loaded (optional if you want to guarantee selectinload)
    result = await db.execute(
        select(Niche)
        .options(selectinload(Niche.keywords))
        .where(Niche.niche_id == new_niche.niche_id)
    )
    return result.scalars().first()

async def get_niche_by_id(db: AsyncSession, niche_id: UUID):
    result = await db.execute(select(Niche).where(Niche.niche_id == niche_id).options(selectinload(Niche.keywords)))
    return result.scalar_one_or_none()

async def update_niche(db: AsyncSession, niche_id: UUID, update: NicheUpdate):
    result = await db.execute(select(Niche).where(Niche.niche_id == niche_id).options(selectinload(Niche.keywords)))
    niche = result.scalar_one_or_none()
    if not niche:
        return None

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(niche, field, value)

    await db.commit()
    await db.refresh(niche)
    return niche

async def delete_niche(db: AsyncSession, niche_id: UUID):
    result = await db.execute(select(Niche).where(Niche.niche_id == niche_id).options(selectinload(Niche.keywords)))
    niche = result.scalar_one_or_none()
    if not niche:
        return False

    await db.delete(niche)
    await db.commit()
    return True

# --- Keyword Services ---

async def get_keywords_for_niche(db: AsyncSession, niche_id: UUID):
    result = await db.execute(select(Keyword).where(Keyword.niche_id == niche_id).order_by(Keyword.keyword))
    return result.scalars().all()

async def add_keyword_to_niche(db: AsyncSession, niche_id: UUID, data: KeywordCreate):
    new_keyword = Keyword(niche_id=niche_id, keyword=data.keyword)
    db.add(new_keyword)
    await db.commit()
    await db.refresh(new_keyword)
    return new_keyword

async def update_keyword(db: AsyncSession, keyword_id: UUID, update: KeywordUpdate):
    result = await db.execute(select(Keyword).where(Keyword.keyword_id == keyword_id))
    keyword = result.scalar_one_or_none()
    if not keyword:
        return None

    keyword.keyword = update.keyword
    await db.commit()
    await db.refresh(keyword)
    return keyword

async def delete_keyword(db: AsyncSession, keyword_id: UUID):
    result = await db.execute(select(Keyword).where(Keyword.keyword_id == keyword_id))
    keyword = result.scalar_one_or_none()
    if not keyword:
        return False

    await db.delete(keyword)
    await db.commit()
    return True
