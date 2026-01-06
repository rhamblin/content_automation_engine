import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from common.db_core.models import Content, IntegrationProfile, Project, Tenant, Niche, ContentGenerationStatus


def test_content_auto_generated_fields(db_session):
    """Test that content_id and created_at are auto-generated"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )

    db_session.add(content)
    db_session.flush()

    assert content.content_id is not None
    assert isinstance(content.content_id, uuid.UUID)
    assert content.created_at is not None
    assert isinstance(content.created_at, datetime)

    db_session.commit()

    assert content.content_id is not None
    assert content.created_at is not None


def test_content_requires_asset_url(db_session):
    """Test that asset_url is required (nullable=False constraint)"""
    content = Content(
        title="Test Content",
        description="Test description"
    )
    content.asset_url = None
    db_session.add(content)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_content_requires_title(db_session):
    """Test that title is required (nullable=False constraint)"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        description="Test description"
    )
    content.title = None
    db_session.add(content)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_content_requires_description(db_session):
    """Test that description is required (nullable=False constraint)"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content"
    )
    content.description = None
    db_session.add(content)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_content_status_defaults_to_draft(db_session):
    """Test that status defaults to 'draft' when not provided"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    assert content.status == "draft"


def test_content_hashtags_defaults_to_empty_list(db_session):
    """Test that hashtags defaults to empty list when not provided"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    assert content.hashtags == []
    assert isinstance(content.hashtags, list)


def test_content_hashtags_stores_array(db_session):
    """Test that hashtags can store and retrieve string arrays"""
    hashtags = ["#tech", "#ai", "#automation", "#python"]

    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description",
        hashtags=hashtags
    )
    db_session.add(content)
    db_session.commit()

    db_session.expire_all()

    retrieved_content = db_session.query(Content).filter_by(content_id=content.content_id).first()
    assert retrieved_content.hashtags == hashtags
    assert len(retrieved_content.hashtags) == 4


def test_content_status_enum_values(db_session):
    """Test that all ContentGenerationStatus enum values work correctly"""
    statuses = [
        ContentGenerationStatus.DRAFT,
        ContentGenerationStatus.READY,
        ContentGenerationStatus.FAILED,
    ]

    for status in statuses:
        content = Content(
            asset_url=f"https://example.com/image_{status.value}.jpg",
            title=f"Test Content {status.value}",
            description=f"Test description for {status.value}",
            status=status.value
        )
        db_session.add(content)

    db_session.commit()

    for status in statuses:
        retrieved_content = db_session.query(Content).filter_by(
            title=f"Test Content {status.value}"
        ).first()
        assert retrieved_content is not None
        assert retrieved_content.status == status.value


def test_content_without_integration_profile(db_session):
    """Test that contents can be created without an integration_profile_id (nullable FK)"""
    content = Content(
        integration_profile_id=None,
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    assert content.integration_profile_id is None
    assert content.integration_profile is None


def test_content_with_valid_integration_profile(db_session):
    """Test that contents can be created with a valid integration_profile_id"""
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    content = Content(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    assert content.integration_profile_id == profile.integration_profile_id


def test_content_with_invalid_integration_profile_id(db_session):
    """Test that creating content with invalid integration_profile_id raises IntegrityError"""
    fake_profile_id = uuid.uuid4()

    content = Content(
        integration_profile_id=fake_profile_id,
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_content_integration_profile_relationship(db_session):
    """Test that content.integration_profile relationship works correctly"""
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    content = Content(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    db_session.expire_all()

    retrieved_content = db_session.query(Content).filter_by(content_id=content.content_id).first()

    assert retrieved_content.integration_profile is not None
    assert retrieved_content.integration_profile.integration_profile_id == profile.integration_profile_id
    assert retrieved_content.integration_profile.channel_key == "pinterest"


def test_content_status_transition_workflow(db_session):
    """Test a typical content generation status transition workflow"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description",
        status=ContentGenerationStatus.DRAFT.value
    )
    db_session.add(content)
    db_session.commit()

    # Transition to ready when generation completes
    content.status = ContentGenerationStatus.READY.value
    db_session.commit()
    assert content.status == ContentGenerationStatus.READY.value


def test_multiple_contents_for_same_integration_profile(db_session):
    """Test that multiple contents can reference the same integration_profile"""
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    content1 = Content(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image1.jpg",
        title="Test Content 1",
        description="Description 1"
    )
    content2 = Content(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image2.jpg",
        title="Test Content 2",
        description="Description 2"
    )
    content3 = Content(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image3.jpg",
        title="Test Content 3",
        description="Description 3"
    )
    db_session.add_all([content1, content2, content3])
    db_session.commit()

    contents = db_session.query(Content).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).all()
    assert len(contents) == 3

    for content in contents:
        assert content.integration_profile_id == profile.integration_profile_id
