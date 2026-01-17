"""Tests for ReportRepository custom methods."""
import pytest
from datetime import datetime, timedelta


class TestReportRepository:

    @pytest.mark.asyncio
    async def test_get_recent(self, report_repo, sample_tenant):
        tenant = sample_tenant
        await report_repo.add(tenant_id=tenant.id, recipients=["a@test.com"])
        await report_repo.add(tenant_id=tenant.id, recipients=["b@test.com"])
        await report_repo.add(tenant_id=tenant.id, recipients=["c@test.com"])

        results = await report_repo.get_recent(tenant.id, limit=2)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_date_range(self, report_repo, sample_tenant, async_db_session):
        tenant = sample_tenant
        r1 = await report_repo.add(tenant_id=tenant.id, recipients=["a@test.com"])
        r2 = await report_repo.add(tenant_id=tenant.id, recipients=["b@test.com"])

        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)
        results = await report_repo.get_by_date_range(tenant.id, start_date, end_date)

        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_get_by_recipient(self, report_repo, sample_tenant):
        tenant = sample_tenant
        await report_repo.add(tenant_id=tenant.id, recipients=["target@test.com", "other@test.com"])
        await report_repo.add(tenant_id=tenant.id, recipients=["different@test.com"])

        results = await report_repo.get_by_recipient(tenant.id, "target@test.com")

        assert len(results) == 1
