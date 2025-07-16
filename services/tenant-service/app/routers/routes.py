from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from db_core.db_async import get_db_session
from db_core.models import Tenant

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("/", response_model=List[dict])
async def list_tenants(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Tenant))
    return [
        {"tenant_id": str(t.tenant_id), "name": t.name} for t in result.scalars().all()
    ]
