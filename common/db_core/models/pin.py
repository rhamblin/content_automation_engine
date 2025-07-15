from db_core.models.base import Base
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    # avoid circular import at runtime, but allow type checkers to see Keyword
    from db_core.models.keywords import Keyword

class Pin(Base):
    __tablename__ = "pins"
    __table_args__ = {"schema": "pins"}

    pin_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("niches.keywords.keyword_id", ondelete="CASCADE"),
        nullable=False
    )
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),        # DB will default to now()
        default=datetime.utcnow,          # Python side default if you create in-Python
        nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    # ORM relationship back to Keyword
    keyword: Mapped["Keyword"] = relationship(
        "Keyword",
        back_populates="pins",
        lazy="joined"
    )

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict representation of this Pin."""
        return {
            "pin_id": str(self.pin_id),
            "keyword_id": str(self.keyword_id),
            "asset_url": self.asset_url,
            # "created_at": self.created_at.strftime("%B %d, %Y at %I:%M %p"),
            "title": self.title,
            "description": self.description,
            "hashtags": self.hashtags,
        }

    def to_readable(self) -> str:
        """Return a human-friendly string representation for logging."""
        tags = ", ".join(self.hashtags) if self.hashtags else ""
        return (
            f"Pin[{self.pin_id}] for keyword of {self.keyword}: \n\n\n{self.title}\n\n"
            f"\n{self.description}\n"
            f"\n\n{self.asset_url}\n\n"
        )