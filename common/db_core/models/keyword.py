from db_core.models.base import Base
from db_core.models.niche import Niche
from typing import List
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

class Keyword(Base):
    __tablename__ = "keywords"
    __table_args__ = {"schema": "niches"}

    keyword_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    niche_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("niches.niches.niche_id"), nullable=False)
    keyword: Mapped[str] = mapped_column(String, nullable=False)

    niche: Mapped[Niche] = relationship(
        back_populates="keywords",
        lazy="selectin"
    )


    def to_dict(self) -> dict:
        """
        Return a JSON-serializable dict representation of this Keyword.
        """
        return {
            "keyword_id": str(self.keyword_id),
            "niche_id": str(self.niche_id),
            "keyword": self.keyword,
        }

    def to_readable(self) -> str:
        """
        Return a human-friendly string representation for logging.
        """
        niche_name = getattr(self.niche, "name", None)
        niche_part = f" (niche='{niche_name}')" if niche_name else ""
        return (
            f"Keyword[{self.keyword_id}]: '{self.keyword}'"
            f"{niche_part} | niche_id={self.niche_id}"
        )