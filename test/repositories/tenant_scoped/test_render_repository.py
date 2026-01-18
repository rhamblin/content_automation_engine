"""Tests for RenderRepository custom methods."""
import pytest
from common.contracts.database_models.enums import RenderStatus


class TestRenderRepository:

    @pytest.mark.asyncio
    async def test_get_by_id_with_images(self, render_repo, image_repo, sample_tenant, sample_content, sample_niche, sample_keyword):
        tenant = sample_tenant
        content = sample_content
        niche = sample_niche
        keyword = sample_keyword
        input_image = await image_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id)
        render = await render_repo.add(
            tenant_id=tenant.id,
            content_id=content.id,
            niche_id=niche.id,
            keyword_id=keyword.id,
            input_image_id=input_image.id
        )

        result = await render_repo.get_by_id_with_images(render.external_id)

        assert result is not None
        assert result.input_image is not None

    @pytest.mark.asyncio
    async def test_get_by_content(self, render_repo, sample_content, sample_niche, sample_keyword):
        content = sample_content
        niche = sample_niche
        keyword = sample_keyword
        await render_repo.add(tenant_id=content.tenant_id, content_id=content.id, niche_id=niche.id, keyword_id=keyword.id)
        await render_repo.add(tenant_id=content.tenant_id, content_id=content.id, niche_id=niche.id, keyword_id=keyword.id)

        results = await render_repo.get_by_content(content.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_status(self, render_repo, sample_tenant, sample_content, sample_niche, sample_keyword):
        tenant = sample_tenant
        content = sample_content
        niche = sample_niche
        keyword = sample_keyword
        r1 = await render_repo.add(tenant_id=tenant.id, content_id=content.id, niche_id=niche.id, keyword_id=keyword.id)
        r2 = await render_repo.add(tenant_id=tenant.id, content_id=content.id, niche_id=niche.id, keyword_id=keyword.id)
        await render_repo.update_status(r2.external_id, RenderStatus.COMPLETED)

        results = await render_repo.get_by_status(tenant.id, RenderStatus.PENDING)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_pending(self, render_repo, sample_tenant, sample_content, sample_niche, sample_keyword):
        tenant = sample_tenant
        content = sample_content
        niche = sample_niche
        keyword = sample_keyword
        await render_repo.add(tenant_id=tenant.id, content_id=content.id, niche_id=niche.id, keyword_id=keyword.id)

        results = await render_repo.get_pending(tenant.id)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_by_keyword(self, render_repo, sample_tenant, sample_content, sample_niche, sample_keyword):
        tenant = sample_tenant
        content = sample_content
        niche = sample_niche
        keyword = sample_keyword
        await render_repo.add(tenant_id=tenant.id, content_id=content.id, niche_id=niche.id, keyword_id=keyword.id)
        await render_repo.add(tenant_id=tenant.id, content_id=content.id, niche_id=niche.id, keyword_id=keyword.id)

        results = await render_repo.get_by_keyword(keyword.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_update_status(self, render_repo, sample_tenant, sample_content, sample_niche, sample_keyword):
        tenant = sample_tenant
        content = sample_content
        niche = sample_niche
        keyword = sample_keyword
        render = await render_repo.add(tenant_id=tenant.id, content_id=content.id, niche_id=niche.id, keyword_id=keyword.id)

        result = await render_repo.update_status(render.external_id, RenderStatus.COMPLETED)

        assert result is True
        fetched = await render_repo.get_by_id(render.external_id)
        assert fetched.status == RenderStatus.COMPLETED.value
