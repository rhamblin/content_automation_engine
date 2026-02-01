import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChannelCreate(BaseModel):
    identifier: str


class ChannelUpdate(BaseModel):
    identifier: Optional[str] = None


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: uuid.UUID
    identifier: str
    created_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = None
