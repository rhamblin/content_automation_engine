from .base import Base
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
import enum
from sqlalchemy import Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .integration_profile import IntegrationProfile
    from .metric import Metric

class PostStatus(enum.Enum):
    generated = "generated"
    ready = "ready"
    posted = "posted"
    error = "error"

class Post(Base):
    __tablename__ = "posts"
    __table_args__ = {"schema": "posts"}

    post_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_profile_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("integration_profiles.integration_profile_id"), nullable=False)
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus, name="post_status", native_enum=False), nullable=False)
    last_posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow)

    integration_profile: Mapped["IntegrationProfile"] = relationship("IntegrationProfile", back_populates="posts")
    metrics: Mapped[List["Metric"]] = relationship("Metric", back_populates="post", lazy="selectin")

    def to_dict(self) -> dict:
        return {
            "post_id": str(self.post_id),
            "integration_profile_id": str(self.integration_profile_id),
            "status": self.status.value,
        }
