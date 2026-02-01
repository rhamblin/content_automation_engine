import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TenantCreate(BaseModel):
    title: str


class TenantUpdate(BaseModel):
    title: Optional[str] = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: uuid.UUID
    title: str
    created_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = None


class TenantUserCreate(BaseModel):
    user_id: uuid.UUID
    role: str


class TenantUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime


class TenantChannelCreate(BaseModel):
    channel_id: uuid.UUID


class TenantChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: uuid.UUID
    channel_id: uuid.UUID
    created_at: datetime
