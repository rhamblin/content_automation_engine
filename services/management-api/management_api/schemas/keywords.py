import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class KeywordCreate(BaseModel):
    term: str


class KeywordUpdate(BaseModel):
    term: Optional[str] = None


class KeywordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: uuid.UUID
    tenant_id: uuid.UUID
    niche_id: uuid.UUID
    term: str
    is_active: bool
    created_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = None
