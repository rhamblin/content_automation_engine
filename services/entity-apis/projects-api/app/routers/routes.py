from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from common.db_core.db_async import get_db_session
from common.db_core.models import Project

router = APIRouter(prefix="/tenants/{tenant_id}/projects", tags=["Projects"])


@router.get("/", response_model=List[dict])
async def list_projects(tenant_id: UUID, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Project).where(Project.tenant_id == tenant_id))
    return [
        {"project_id": str(p.project_id), "name": p.name} for p in result.scalars().all()
    ]
