from .base import Base
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .project import Project
    from .niche import Niche
    from .post import Post

class IntegrationProfile(Base):
    __tablename__ = "integration_profiles"

    integration_profile_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("identity.projects.project_id"), nullable=False)
    niche_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("niches.niches.niche_id"), nullable=False)
    image_provider_key: Mapped[str] = mapped_column(String, nullable=False)
    model_provider_key: Mapped[str] = mapped_column(String, nullable=False)
    channel_key: Mapped[str] = mapped_column(String, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="integration_profiles")
    niche: Mapped["Niche"] = relationship("Niche", lazy="selectin")
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="integration_profile", lazy="selectin")

    def to_dict(self) -> dict:
        return {
            "integration_profile_id": str(self.integration_profile_id),
            "project_id": str(self.project_id),
            "niche_id": str(self.niche_id),
        }
