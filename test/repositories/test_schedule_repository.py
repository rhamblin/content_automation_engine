"""Tests for ScheduleRepository custom methods."""
import pytest
from datetime import datetime, timedelta
from common.contracts.database_models import ScheduleExecution
from common.contracts.database_models.enums import ScheduleExecutionStatus


class TestScheduleRepository:

    @pytest.mark.asyncio
    async def test_get_by_id_with_executions(self, schedule_repo, sample_schedule):
        schedule = sample_schedule
        execution = ScheduleExecution(
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            started_at=datetime.utcnow()
        )
        await schedule_repo.add_execution(execution)

        result = await schedule_repo.get_by_id_with_executions(schedule.external_id)

        assert result is not None
        assert len(result.schedule_executions) == 1

    @pytest.mark.asyncio
    async def test_get_active_schedules(self, schedule_repo, sample_tenant, sample_niche):
        tenant = sample_tenant
        niche = sample_niche
        s1 = await schedule_repo.add(tenant_id=tenant.id, niche_id=niche.id, title="Active", cron_expression="0 9 * * *")
        s2 = await schedule_repo.add(tenant_id=tenant.id, niche_id=niche.id, title="Inactive", cron_expression="0 9 * * *")
        await schedule_repo.deactivate(s2.external_id)

        results = await schedule_repo.get_active_schedules(tenant.id)

        titles = [s.title for s in results]
        assert "Active" in titles
        assert "Inactive" not in titles

    @pytest.mark.asyncio
    async def test_get_due_schedules(self, schedule_repo, sample_tenant, sample_niche, async_db_session):
        tenant = sample_tenant
        niche = sample_niche
        schedule = await schedule_repo.add(
            tenant_id=tenant.id,
            niche_id=niche.id,
            title="Due Schedule",
            cron_expression="0 9 * * *"
        )
        schedule.next_run_at = datetime.utcnow() - timedelta(hours=1)
        await async_db_session.flush()

        results = await schedule_repo.get_due_schedules(datetime.utcnow())

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_by_niche(self, schedule_repo, sample_tenant, sample_niche):
        tenant = sample_tenant
        niche = sample_niche
        await schedule_repo.add(tenant_id=tenant.id, niche_id=niche.id, title="Schedule 1", cron_expression="0 9 * * *")
        await schedule_repo.add(tenant_id=tenant.id, niche_id=niche.id, title="Schedule 2", cron_expression="0 10 * * *")

        results = await schedule_repo.get_by_niche(niche.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_update_last_run(self, schedule_repo, sample_schedule):
        schedule = sample_schedule
        last_run = datetime.utcnow()
        next_run = datetime.utcnow() + timedelta(days=1)

        result = await schedule_repo.update_last_run(schedule.external_id, last_run, next_run)

        assert result is True
        fetched = await schedule_repo.get_by_id(schedule.external_id)
        assert fetched.last_run_at is not None
        assert fetched.next_run_at is not None

    @pytest.mark.asyncio
    async def test_deactivate(self, schedule_repo, sample_schedule):
        schedule = sample_schedule

        result = await schedule_repo.deactivate(schedule.external_id)

        assert result is True
        fetched = await schedule_repo.get_by_id(schedule.external_id)
        assert fetched.is_active is False

    @pytest.mark.asyncio
    async def test_add_execution(self, schedule_repo, sample_schedule):
        schedule = sample_schedule
        execution = ScheduleExecution(
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            started_at=datetime.utcnow()
        )

        result = await schedule_repo.add_execution(execution)

        assert result.id is not None

    @pytest.mark.asyncio
    async def test_get_executions(self, schedule_repo, sample_schedule):
        schedule = sample_schedule
        await schedule_repo.add_execution(ScheduleExecution(
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            started_at=datetime.utcnow()
        ))
        await schedule_repo.add_execution(ScheduleExecution(
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            started_at=datetime.utcnow()
        ))

        results = await schedule_repo.get_executions(schedule.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_running_executions(self, schedule_repo, sample_schedule):
        schedule = sample_schedule
        execution = ScheduleExecution(
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            started_at=datetime.utcnow(),
            status=ScheduleExecutionStatus.RUNNING.value
        )
        await schedule_repo.add_execution(execution)

        results = await schedule_repo.get_running_executions(schedule.tenant_id)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_update_execution_status(self, schedule_repo, sample_schedule):
        schedule = sample_schedule
        execution = ScheduleExecution(
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            started_at=datetime.utcnow()
        )
        exec_result = await schedule_repo.add_execution(execution)

        result = await schedule_repo.update_execution_status(exec_result.id, ScheduleExecutionStatus.COMPLETED)

        assert result is True
        fetched = await schedule_repo.get_execution_by_id(exec_result.id)
        assert fetched.status == ScheduleExecutionStatus.COMPLETED.value
