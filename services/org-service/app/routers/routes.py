from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from db_core.db_async import get_db_session
from db_core.models.tenant import Tenant

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.get("/", response_model=List[dict])
async def list_tenants(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Tenant))
    return [t.to_dict() for t in result.scalars().all()]

@router.post("/", response_model=dict)
async def create_tenant(data: dict, db: AsyncSession = Depends(get_db_session)):
    tenant = Tenant(name=data.get("name"))
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant.to_dict()

@router.post("/{tenant_id}/invite")
async def invite_user(tenant_id: UUID):
    return {"status": "invited"}
