from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from db_core.db_async import get_db_session
from db_core.models.integration_profile import IntegrationProfile

router = APIRouter(prefix="/integration_profiles", tags=["IntegrationProfiles"])

@router.get("/", response_model=List[dict])
async def list_profiles(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(IntegrationProfile))
    return [p.to_dict() for p in result.scalars().all()]
