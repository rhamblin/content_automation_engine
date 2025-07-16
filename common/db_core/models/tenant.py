from .base import Base
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .project import Project
    from .tenant_user import TenantUser

class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "identity"}

    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow)

    projects: Mapped[List["Project"]] = relationship("Project", back_populates="tenant", lazy="selectin")
    users: Mapped[List["TenantUser"]] = relationship("TenantUser", back_populates="tenant", lazy="selectin")

    def to_dict(self) -> dict:
        return {
            "tenant_id": str(self.tenant_id),
            "name": self.name,
        }
