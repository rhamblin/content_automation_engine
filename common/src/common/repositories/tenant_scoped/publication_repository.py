from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Publication, Promotion, PublicationMetric
from common.contracts.database_models.enums import PublicationStatus, PromotionStatus
from common.repositories.base_tenant_scoped_repository import BaseTenantScopedRepository


class PublicationRepository(BaseTenantScopedRepository[Publication]):
    """Repository for Publication aggregate (includes promotions & metrics)."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Publication, tenant_id)

    async def add(
        self,
        channel_id: UUID,
        content_id: UUID,
        render_id: Optional[UUID] = None
    ) -> Publication:
        publication = Publication(
            tenant_id=self._tenant_id,
            channel_id=channel_id,
            content_id=content_id,
            render_id=render_id
        )
        self._session.add(publication)
        await self._session.flush()
        await self._session.refresh(publication)
        return publication

    async def get_by_id_with_promotions(self, id: UUID) -> Optional[Publication]:
        stmt = (
            select(Publication)
            .options(selectinload(Publication.promotions))
            .where(Publication.tenant_id == self._tenant_id, Publication.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_metrics(self, id: UUID) -> Optional[Publication]:
        stmt = (
            select(Publication)
            .options(selectinload(Publication.publication_metrics))
            .where(Publication.tenant_id == self._tenant_id, Publication.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_post_id(self, channel_id: UUID, post_id: str) -> Optional[Publication]:
        stmt = select(Publication).where(
            Publication.tenant_id == self._tenant_id,
            Publication.channel_id == channel_id,
            Publication.post_id == post_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_status(self, status: PublicationStatus, limit: int = 100) -> List[Publication]:
        stmt = (
            select(Publication)
            .where(Publication.tenant_id == self._tenant_id, Publication.status == status)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending(self, limit: int = 100) -> List[Publication]:
        return await self.get_by_status(PublicationStatus.PENDING, limit)

    async def get_by_channel(self, channel_id: UUID, limit: int = 100, offset: int = 0) -> List[Publication]:
        stmt = select(Publication).where(
            Publication.tenant_id == self._tenant_id,
            Publication.channel_id == channel_id
        ).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_content(self, content_id: UUID) -> List[Publication]:
        stmt = select(Publication).where(
            Publication.tenant_id == self._tenant_id,
            Publication.content_id == content_id
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, id: UUID, status: PublicationStatus, post_id: Optional[str] = None) -> bool:
        publication = await self.get_by_id(id)
        if publication:
            publication.status = status
            if post_id:
                publication.post_id = post_id
            await self._session.flush()
            return True
        return False

    # Promotion methods
    async def add_promotion(self, promotion: Promotion) -> Promotion:
        self._session.add(promotion)
        await self._session.flush()
        await self._session.refresh(promotion)
        return promotion

    async def get_promotions(self, publication_id: UUID) -> List[Promotion]:
        stmt = select(Promotion).where(
            Promotion.tenant_id == self._tenant_id,
            Promotion.publication_id == publication_id
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_promotions(self, limit: int = 100) -> List[Promotion]:
        stmt = (
            select(Promotion)
            .where(Promotion.tenant_id == self._tenant_id, Promotion.status == PromotionStatus.PENDING)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_promotion_status(self, promotion_id: UUID, status: PromotionStatus) -> bool:
        promotion = await self._session.get(Promotion, promotion_id)
        if promotion and promotion.tenant_id == self._tenant_id:
            promotion.status = status
            if status == PromotionStatus.EXECUTED:
                promotion.executed_at = datetime.now(timezone.utc)
            await self._session.flush()
            return True
        return False

    # Metrics methods
    async def add_metric(self, metric: PublicationMetric) -> PublicationMetric:
        self._session.add(metric)
        await self._session.flush()
        await self._session.refresh(metric)
        return metric

    async def get_metrics(self, publication_id: UUID) -> List[PublicationMetric]:
        stmt = (
            select(PublicationMetric)
            .where(
                PublicationMetric.tenant_id == self._tenant_id,
                PublicationMetric.publication_id == publication_id
            )
            .order_by(PublicationMetric.snapshot_date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_metric(self, publication_id: UUID) -> Optional[PublicationMetric]:
        stmt = (
            select(PublicationMetric)
            .where(
                PublicationMetric.tenant_id == self._tenant_id,
                PublicationMetric.publication_id == publication_id
            )
            .order_by(PublicationMetric.snapshot_date.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_metric_by_date(self, publication_id: UUID, snapshot_date: datetime) -> Optional[PublicationMetric]:
        stmt = select(PublicationMetric).where(
            PublicationMetric.tenant_id == self._tenant_id,
            PublicationMetric.publication_id == publication_id,
            PublicationMetric.snapshot_date == snapshot_date
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
