import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class IntegrationProfileCreate(BaseModel):
    niche_id: uuid.UUID
    channel_id: uuid.UUID


class IntegrationProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: uuid.UUID
    tenant_id: uuid.UUID
    niche_id: uuid.UUID
    channel_id: uuid.UUID
    is_active: bool
    created_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = None
