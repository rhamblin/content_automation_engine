"""Tests for ImageRepository custom methods."""
import pytest
from common.contracts.database_models.enums import ImageKind


class TestImageRepository:

    @pytest.mark.asyncio
    async def test_get_by_keyword(self, image_repo, sample_tenant, sample_niche, sample_keyword):
        tenant = sample_tenant
        niche = sample_niche
        keyword = sample_keyword
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id)
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id)

        results = await image_repo.get_by_keyword(keyword.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_keyword_and_kind(self, image_repo, sample_tenant, sample_niche, sample_keyword):
        tenant = sample_tenant
        niche = sample_niche
        keyword = sample_keyword
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, kind=ImageKind.ORIGINAL)
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, kind=ImageKind.RENDERED)
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, kind=ImageKind.ORIGINAL)

        results = await image_repo.get_by_keyword_and_kind(keyword.id, ImageKind.ORIGINAL)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_niche(self, image_repo, sample_tenant, sample_niche, sample_keyword):
        tenant = sample_tenant
        niche = sample_niche
        keyword = sample_keyword
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id)
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id)

        results = await image_repo.get_by_niche(niche.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_kind(self, image_repo, sample_tenant, sample_niche, sample_keyword):
        tenant = sample_tenant
        niche = sample_niche
        keyword = sample_keyword
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, kind=ImageKind.THUMBNAIL)
        await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, kind=ImageKind.ORIGINAL)

        results = await image_repo.get_by_kind(tenant.id, ImageKind.THUMBNAIL)

        assert len(results) == 1
        assert results[0].kind == ImageKind.THUMBNAIL.value
