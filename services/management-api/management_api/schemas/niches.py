import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NicheCreate(BaseModel):
    title: str


class NicheUpdate(BaseModel):
    title: Optional[str] = None


class NicheResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    is_active: bool
    created_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = None
