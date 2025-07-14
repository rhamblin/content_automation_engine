"""
Implements all database operations for niches and keywords using SQLAlchemy ORM.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID
from app.models.niche import Niche
from app.models.keyword import Keyword
from app.schemas.schema import (
    NicheCreate, NicheUpdate,
    KeywordCreate, KeywordUpdate
)

# --- Niche Services ---

async def get_all_niches(db: AsyncSession):
    result = await db.execute(select(Niche).order_by(Niche.name))
    return result.scalars().all()

async def create_niche(db: AsyncSession, data: NicheCreate):
    new_niche = Niche(**data.model_dump())
    db.add(new_niche)
    await db.commit()
    await db.refresh(new_niche)
    return new_niche

async def get_niche_by_id(db: AsyncSession, niche_id: UUID):
    result = await db.execute(select(Niche).where(Niche.niche_id == niche_id))
    return result.scalar_one_or_none()

async def update_niche(db: AsyncSession, niche_id: UUID, update: NicheUpdate):
    result = await db.execute(select(Niche).where(Niche.niche_id == niche_id))
    niche = result.scalar_one_or_none()
    if not niche:
        return None

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(niche, field, value)

    await db.commit()
    await db.refresh(niche)
    return niche

async def delete_niche(db: AsyncSession, niche_id: UUID):
    result = await db.execute(select(Niche).where(Niche.niche_id == niche_id))
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
