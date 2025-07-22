"""
Defines all v1 endpoints for managing niches and keywords.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from db_core.db_async import get_db_session
import app.services.service as service
from app.schemas.schema import (
    NicheCreate, NicheUpdate, NicheRead,
    KeywordCreate, KeywordUpdate, KeywordRead
)

router = APIRouter(prefix="/v1/niches", tags=["Niches"])

# --- Healthcheck ----
@router.head("/healthcheck")
async def healthcheck():
    return "Alive!"

# --- Niche Routes ---

@router.get("/", response_model=List[NicheRead])
async def list_niches(db: AsyncSession = Depends(get_db_session)):
    return await service.get_all_niches(db)

@router.post("/", response_model=NicheRead)
async def create_niche(niche: NicheCreate, db: AsyncSession = Depends(get_db_session)):
    return await service.create_niche(db, niche)

@router.get("/{niche_id}", response_model=NicheRead)
async def get_niche(niche_id: UUID, db: AsyncSession = Depends(get_db_session)):
    result = await service.get_niche_by_id(db, niche_id)
    if not result:
        raise HTTPException(status_code=404, detail="Niche not found")
    return result

@router.put("/{niche_id}", response_model=NicheRead)
async def update_niche(niche_id: UUID, update: NicheUpdate, db: AsyncSession = Depends(get_db_session)):
    result = await service.update_niche(db, niche_id, update)
    if not result:
        raise HTTPException(status_code=404, detail="Niche not found")
    return result

@router.delete("/{niche_id}", status_code=204)
async def delete_niche(niche_id: UUID, db: AsyncSession = Depends(get_db_session)):
    success = await service.delete_niche(db, niche_id)
    if not success:
        raise HTTPException(status_code=404, detail="Niche not found")

# --- Keyword Routes ---

@router.get("/{niche_id}/keywords", response_model=List[KeywordRead])
async def list_keywords(niche_id: UUID, db: AsyncSession = Depends(get_db_session)):
    return await service.get_keywords_for_niche(db, niche_id)

@router.post("/{niche_id}/keywords", response_model=KeywordRead)
async def add_keyword(niche_id: UUID, keyword: KeywordCreate, db: AsyncSession = Depends(get_db_session)):
    return await service.add_keyword_to_niche(db, niche_id, keyword)

@router.put("/keywords/{keyword_id}", response_model=KeywordRead)
async def update_keyword(keyword_id: UUID, update: KeywordUpdate, db: AsyncSession = Depends(get_db_session)):
    result = await service.update_keyword(db, keyword_id, update)
    if not result:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return result

@router.delete("/keywords/{keyword_id}", status_code=204)
async def delete_keyword(keyword_id: UUID, db: AsyncSession = Depends(get_db_session)):
    success = await service.delete_keyword(db, keyword_id)
    if not success:
        raise HTTPException(status_code=404, detail="Keyword not found")
