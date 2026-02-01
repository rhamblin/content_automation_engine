from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.repositories.tenant_scoped.niche_repository import NicheRepository
from management_api.dependencies import get_db_session
from management_api.schemas.niches import NicheCreate, NicheResponse, NicheUpdate

router = APIRouter(prefix="/tenants/{tenant_id}/niches", tags=["niches"])


@router.post("", response_model=NicheResponse, status_code=201)
async def create_niche(tenant_id: UUID, body: NicheCreate, session: AsyncSession = Depends(get_db_session)):
    repo = NicheRepository(session, tenant_id)
    niche = await repo.add(title=body.title)
    await session.commit()
    return niche


@router.get("", response_model=List[NicheResponse])
async def list_niches(tenant_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = NicheRepository(session, tenant_id)
    return await repo.get_all(include_only_active=True)


@router.get("/{niche_id}", response_model=NicheResponse)
async def get_niche(tenant_id: UUID, niche_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = NicheRepository(session, tenant_id)
    return await repo.get_by_id(niche_id)


@router.patch("/{niche_id}", response_model=NicheResponse)
async def update_niche(tenant_id: UUID, niche_id: UUID, body: NicheUpdate, session: AsyncSession = Depends(get_db_session)):
    repo = NicheRepository(session, tenant_id)
    niche = await repo.get_by_id(niche_id)
    if body.title is not None:
        niche.title = body.title
    niche = await repo.update(niche)
    await session.commit()
    return niche


@router.delete("/{niche_id}", status_code=204)
async def delete_niche(tenant_id: UUID, niche_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = NicheRepository(session, tenant_id)
    await repo.deactivate(niche_id)
    await session.commit()
