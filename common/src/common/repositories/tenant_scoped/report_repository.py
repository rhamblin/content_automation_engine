from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import Report
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class ReportRepository(BaseTenantScopedRepository[Report]):
    """Repository for Report aggregate."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Report, tenant_id)

    async def add(
        self,
        recipients: List[str],
        content: Optional[dict] = None
    ) -> Report:
        report = Report(
            tenant_id=self._tenant_id,
            recipients=recipients,
            content=content
        )
        self._session.add(report)
        await self._session.flush()
        await self._session.refresh(report)
        return report

    async def get_recent(self, limit: int = 10) -> List[Report]:
        stmt = (
            select(Report)
            .where(Report.tenant_id == self._tenant_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Report]:
        stmt = (
            select(Report)
            .where(
                Report.tenant_id == self._tenant_id,
                Report.created_at >= start_date,
                Report.created_at <= end_date
            )
            .order_by(Report.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_recipient(self, recipient_email: str) -> List[Report]:
        stmt = (
            select(Report)
            .where(
                Report.tenant_id == self._tenant_id,
                Report.recipients.contains([recipient_email])
            )
            .order_by(Report.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
