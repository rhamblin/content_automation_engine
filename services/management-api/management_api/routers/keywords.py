from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import Keyword
from common.repositories.tenant_scoped.niche_repository import NicheRepository
from management_api.dependencies import get_db_session
from management_api.schemas.keywords import KeywordCreate, KeywordResponse, KeywordUpdate

router = APIRouter(prefix="/tenants/{tenant_id}/niches/{niche_id}/keywords", tags=["keywords"])


@router.post("", response_model=KeywordResponse, status_code=201)
async def create_keyword(
    tenant_id: UUID, niche_id: UUID, body: KeywordCreate, session: AsyncSession = Depends(get_db_session)
):
    repo = NicheRepository(session, tenant_id)
    # Validate niche exists
    await repo.get_by_id(niche_id)
    keyword = Keyword(tenant_id=tenant_id, niche_id=niche_id, term=body.term)
    keyword = await repo.add_keyword(keyword)
    await session.commit()
    return keyword


@router.get("", response_model=List[KeywordResponse])
async def list_keywords(
    tenant_id: UUID, niche_id: UUID, session: AsyncSession = Depends(get_db_session)
):
    repo = NicheRepository(session, tenant_id)
    return await repo.get_keywords(niche_id, include_only_active=True)


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    tenant_id: UUID, niche_id: UUID, keyword_id: UUID, session: AsyncSession = Depends(get_db_session)
):
    repo = NicheRepository(session, tenant_id)
    return await repo.get_keyword_by_id(keyword_id)


@router.patch("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    tenant_id: UUID, niche_id: UUID, keyword_id: UUID, body: KeywordUpdate, session: AsyncSession = Depends(get_db_session)
):
    repo = NicheRepository(session, tenant_id)
    keyword = await repo.get_keyword_by_id(keyword_id)
    if body.term is not None:
        keyword.term = body.term
    await repo.update(keyword)
    await session.commit()
    return keyword


@router.delete("/{keyword_id}", status_code=204)
async def delete_keyword(
    tenant_id: UUID, niche_id: UUID, keyword_id: UUID, session: AsyncSession = Depends(get_db_session)
):
    repo = NicheRepository(session, tenant_id)
    await repo.deactivate_keyword(keyword_id)
    await session.commit()
