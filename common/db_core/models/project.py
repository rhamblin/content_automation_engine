from .base import Base
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .tenant import Tenant
    from .integration_profile import IntegrationProfile

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "identity"}

    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("identity.tenants.tenant_id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="projects")
    integration_profiles: Mapped[List["IntegrationProfile"]] = relationship("IntegrationProfile", back_populates="project", lazy="selectin")

    def to_dict(self) -> dict:
        return {
            "project_id": str(self.project_id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
        }
