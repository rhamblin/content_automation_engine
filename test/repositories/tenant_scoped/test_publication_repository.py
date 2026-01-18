"""Tests for PublicationRepository custom methods."""
import pytest
from datetime import datetime, timezone
from common.contracts.database_models import Promotion, PublicationMetric
from common.contracts.database_models.enums import PublicationStatus, PromotionStatus


class TestPublicationRepository:

    @pytest.mark.asyncio
    async def test_get_by_id_with_promotions(self, publication_repo, sample_publication):
        publication = sample_publication
        promotion = Promotion(
            tenant_id=publication.tenant_id,
            publication_id=publication.id,
            channel_id=publication.channel_id
        )
        await publication_repo.add_promotion(promotion)

        result = await publication_repo.get_by_id_with_promotions(publication.external_id)

        assert result is not None
        assert len(result.promotions) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_with_metrics(self, publication_repo, sample_publication):
        publication = sample_publication
        metric = PublicationMetric(
            publication_id=publication.id,
            snapshot_date=datetime.now(timezone.utc),
            views=100
        )
        await publication_repo.add_metric(metric)

        result = await publication_repo.get_by_id_with_metrics(publication.external_id)

        assert result is not None
        assert len(result.publication_metrics) == 1

    @pytest.mark.asyncio
    async def test_get_by_post_id(self, publication_repo, sample_publication):
        publication = sample_publication
        await publication_repo.update_status(publication.external_id, PublicationStatus.PUBLISHED, post_id="abc123")

        result = await publication_repo.get_by_post_id(publication.channel_id, "abc123")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_status(self, publication_repo, sample_tenant, sample_channel, sample_content):
        tenant = sample_tenant
        channel = sample_channel
        content = sample_content
        p1 = await publication_repo.add(tenant_id=tenant.id, channel_id=channel.id, content_id=content.id)
        p2 = await publication_repo.add(tenant_id=tenant.id, channel_id=channel.id, content_id=content.id)
        await publication_repo.update_status(p2.external_id, PublicationStatus.PUBLISHED)

        results = await publication_repo.get_by_status(tenant.id, PublicationStatus.PENDING)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_by_channel(self, publication_repo, sample_tenant, sample_channel, sample_content):
        tenant = sample_tenant
        channel = sample_channel
        content = sample_content
        await publication_repo.add(tenant_id=tenant.id, channel_id=channel.id, content_id=content.id)
        await publication_repo.add(tenant_id=tenant.id, channel_id=channel.id, content_id=content.id)

        results = await publication_repo.get_by_channel(channel.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_content(self, publication_repo, sample_publication, sample_content, sample_channel, sample_tenant):
        content = sample_content
        channel = sample_channel
        tenant = sample_tenant
        await publication_repo.add(tenant_id=tenant.id, channel_id=channel.id, content_id=content.id)

        results = await publication_repo.get_by_content(content.id)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_update_status(self, publication_repo, sample_publication):
        publication = sample_publication

        result = await publication_repo.update_status(publication.external_id, PublicationStatus.PUBLISHED, post_id="xyz789")

        assert result is True
        fetched = await publication_repo.get_by_id(publication.external_id)
        assert fetched.status == PublicationStatus.PUBLISHED.value
        assert fetched.post_id == "xyz789"

    @pytest.mark.asyncio
    async def test_get_pending_promotions(self, publication_repo, sample_publication):
        publication = sample_publication
        promotion = Promotion(
            tenant_id=publication.tenant_id,
            publication_id=publication.id,
            channel_id=publication.channel_id
        )
        await publication_repo.add_promotion(promotion)

        results = await publication_repo.get_pending_promotions(publication.tenant_id)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_update_promotion_status(self, publication_repo, sample_publication):
        publication = sample_publication
        promotion = Promotion(
            tenant_id=publication.tenant_id,
            publication_id=publication.id,
            channel_id=publication.channel_id
        )
        promo = await publication_repo.add_promotion(promotion)

        result = await publication_repo.update_promotion_status(promo.id, PromotionStatus.EXECUTED)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_latest_metric(self, publication_repo, sample_publication):
        publication = sample_publication
        await publication_repo.add_metric(PublicationMetric(
            publication_id=publication.id,
            snapshot_date=datetime(2024, 1, 1),
            views=50
        ))
        await publication_repo.add_metric(PublicationMetric(
            publication_id=publication.id,
            snapshot_date=datetime(2024, 1, 2),
            views=100
        ))

        result = await publication_repo.get_latest_metric(publication.id)

        assert result is not None
        assert result.views == 100
