import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ScheduleCreate(BaseModel):
    cron_expression: str
    message_type: str
    integration_profile_id: Optional[uuid.UUID] = None


class ScheduleUpdate(BaseModel):
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: uuid.UUID
    tenant_id: uuid.UUID
    integration_profile_id: Optional[uuid.UUID] = None
    is_active: bool
    cron_expression: str
    message_type: str
    created_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = None
