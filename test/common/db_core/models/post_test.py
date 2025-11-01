import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from common.db_core.models import Post, IntegrationProfile, Project, Tenant, Niche, PostStatus


def test_post_auto_generated_fields(db_session):
    """Test that post_id and created_at are auto-generated"""
    # Create post with minimal required fields
    post = Post(
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )

    db_session.add(post)
    db_session.flush()  # Trigger default value generation

    # After flush (before commit), defaults should be set
    assert post.post_id is not None
    assert isinstance(post.post_id, uuid.UUID)
    assert post.created_at is not None
    assert isinstance(post.created_at, datetime)

    db_session.commit()

    # After commit, values should be maintained
    assert post.post_id is not None
    assert post.created_at is not None


def test_post_requires_asset_url(db_session):
    """Test that asset_url is required (nullable=False constraint)"""
    # Try to create Post without asset_url
    post = Post(
        title="Test Post",
        description="Test description"
    )
    post.asset_url = None  # Explicitly set to None
    db_session.add(post)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_post_requires_title(db_session):
    """Test that title is required (nullable=False constraint)"""
    # Try to create Post without title
    post = Post(
        asset_url="https://example.com/image.jpg",
        description="Test description"
    )
    post.title = None  # Explicitly set to None
    db_session.add(post)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_post_requires_description(db_session):
    """Test that description is required (nullable=False constraint)"""
    # Try to create Post without description
    post = Post(
        asset_url="https://example.com/image.jpg",
        title="Test Post"
    )
    post.description = None  # Explicitly set to None
    db_session.add(post)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_post_status_defaults_to_generated(db_session):
    """Test that status defaults to 'generated' when not provided"""
    post = Post(
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )
    db_session.add(post)
    db_session.commit()

    # Verify status defaults to generated
    assert post.status == PostStatus.generated


def test_post_hashtags_defaults_to_empty_list(db_session):
    """Test that hashtags defaults to empty list when not provided"""
    post = Post(
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )
    db_session.add(post)
    db_session.commit()

    # Verify hashtags defaults to empty list
    assert post.hashtags == []
    assert isinstance(post.hashtags, list)


def test_post_hashtags_stores_array(db_session):
    """Test that hashtags can store and retrieve string arrays"""
    hashtags = ["#tech", "#ai", "#automation", "#python"]

    post = Post(
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description",
        hashtags=hashtags
    )
    db_session.add(post)
    db_session.commit()

    # Clear session to test persistence
    db_session.expire_all()

    # Retrieve and verify
    retrieved_post = db_session.query(Post).filter_by(post_id=post.post_id).first()
    assert retrieved_post.hashtags == hashtags
    assert len(retrieved_post.hashtags) == 4


def test_post_status_enum_values(db_session):
    """Test that all PostStatus enum values work correctly"""
    statuses = [
        PostStatus.generated,
        PostStatus.ready,
        PostStatus.posted,
        PostStatus.error
    ]

    for status in statuses:
        post = Post(
            asset_url=f"https://example.com/image_{status.value}.jpg",
            title=f"Test Post {status.value}",
            description=f"Test description for {status.value}",
            status=status
        )
        db_session.add(post)

    db_session.commit()

    # Verify all statuses were stored correctly
    for status in statuses:
        retrieved_post = db_session.query(Post).filter_by(
            title=f"Test Post {status.value}"
        ).first()
        assert retrieved_post is not None
        assert retrieved_post.status == status


def test_post_last_posted_at_nullable(db_session):
    """Test that last_posted_at is nullable and defaults to None"""
    post = Post(
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )
    db_session.add(post)
    db_session.commit()

    # Verify last_posted_at is None by default
    assert post.last_posted_at is None


def test_post_without_integration_profile(db_session):
    """Test that posts can be created without an integration_profile_id (nullable FK)"""
    post = Post(
        integration_profile_id=None,
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )
    db_session.add(post)
    db_session.commit()

    # Verify post was created with NULL integration_profile_id
    assert post.integration_profile_id is None
    assert post.integration_profile is None


def test_post_with_valid_integration_profile(db_session):
    """Test that posts can be created with a valid integration_profile_id"""
    # Create dependencies
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
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Create post with valid integration_profile_id
    post = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )
    db_session.add(post)
    db_session.commit()

    # Verify post was created with the integration_profile_id
    assert post.integration_profile_id == profile.integration_profile_id


def test_post_with_invalid_integration_profile_id(db_session):
    """Test that creating post with invalid integration_profile_id raises IntegrityError"""
    # Try to create post with non-existent integration_profile_id
    fake_profile_id = uuid.uuid4()

    post = Post(
        integration_profile_id=fake_profile_id,
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )
    db_session.add(post)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a FK constraint violation
    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_post_integration_profile_relationship(db_session):
    """Test that post.integration_profile relationship works correctly"""
    # Create dependencies
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
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Create post linked to profile
    post = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )
    db_session.add(post)
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve post and verify integration_profile relationship loaded
    retrieved_post = db_session.query(Post).filter_by(post_id=post.post_id).first()

    assert retrieved_post.integration_profile is not None
    assert retrieved_post.integration_profile.integration_profile_id == profile.integration_profile_id
    assert retrieved_post.integration_profile.channel_key == "pinterest"


def test_post_integration_profile_relationship_null(db_session):
    """Test that post.integration_profile is None when integration_profile_id is NULL"""
    post = Post(
        integration_profile_id=None,
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description"
    )
    db_session.add(post)
    db_session.commit()

    # Clear session
    db_session.expire_all()

    # Retrieve post and verify integration_profile is None
    retrieved_post = db_session.query(Post).filter_by(post_id=post.post_id).first()
    assert retrieved_post.integration_profile is None


def test_post_status_transition_workflow(db_session):
    """Test a typical post status transition workflow"""
    post = Post(
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description",
        status=PostStatus.generated
    )
    db_session.add(post)
    db_session.commit()

    # Transition to ready
    post.status = PostStatus.ready
    db_session.commit()
    assert post.status == PostStatus.ready

    # Transition to posted and set last_posted_at
    post.status = PostStatus.posted
    post.last_posted_at = datetime.utcnow()
    db_session.commit()
    assert post.status == PostStatus.posted
    assert post.last_posted_at is not None


def test_post_status_error_state(db_session):
    """Test that posts can be marked with error status"""
    post = Post(
        asset_url="https://example.com/image.jpg",
        title="Test Post",
        description="Test description",
        status=PostStatus.error
    )
    db_session.add(post)
    db_session.commit()

    assert post.status == PostStatus.error


def test_multiple_posts_for_same_integration_profile(db_session):
    """Test that multiple posts can reference the same integration_profile"""
    # Create dependencies
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
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Create multiple posts for same profile
    post1 = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image1.jpg",
        title="Test Post 1",
        description="Description 1"
    )
    post2 = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image2.jpg",
        title="Test Post 2",
        description="Description 2"
    )
    post3 = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image3.jpg",
        title="Test Post 3",
        description="Description 3"
    )
    db_session.add_all([post1, post2, post3])
    db_session.commit()

    # Verify all posts reference the same profile
    posts = db_session.query(Post).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).all()
    assert len(posts) == 3

    for post in posts:
        assert post.integration_profile_id == profile.integration_profile_id


def test_query_posts_by_integration_profile_id(db_session):
    """Test querying posts filtered by integration_profile_id"""
    # Create dependencies
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create two different profiles
    profile1 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        image_provider_key="dalle",
        text_provider_key="claude",
        channel_key="instagram"
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Create posts for each profile
    for i in range(3):
        post = Post(
            integration_profile_id=profile1.integration_profile_id,
            asset_url=f"https://example.com/profile1_image{i}.jpg",
            title=f"Profile 1 Post {i}",
            description=f"Description {i}"
        )
        db_session.add(post)

    for i in range(2):
        post = Post(
            integration_profile_id=profile2.integration_profile_id,
            asset_url=f"https://example.com/profile2_image{i}.jpg",
            title=f"Profile 2 Post {i}",
            description=f"Description {i}"
        )
        db_session.add(post)

    db_session.commit()

    # Query posts for profile1
    profile1_posts = db_session.query(Post).filter_by(
        integration_profile_id=profile1.integration_profile_id
    ).all()
    assert len(profile1_posts) == 3

    # Query posts for profile2
    profile2_posts = db_session.query(Post).filter_by(
        integration_profile_id=profile2.integration_profile_id
    ).all()
    assert len(profile2_posts) == 2


def test_query_posts_with_null_integration_profile_id(db_session):
    """Test querying posts that have no associated integration_profile"""
    # Create posts with and without integration_profile
    post_with_profile = Post(
        integration_profile_id=None,  # This would normally be a valid UUID
        asset_url="https://example.com/image1.jpg",
        title="Post without profile",
        description="Description"
    )

    post_without_profile = Post(
        integration_profile_id=None,
        asset_url="https://example.com/image2.jpg",
        title="Another post without profile",
        description="Description"
    )

    db_session.add_all([post_with_profile, post_without_profile])
    db_session.commit()

    # Query posts with NULL integration_profile_id
    orphan_posts = db_session.query(Post).filter(
        Post.integration_profile_id.is_(None)
    ).all()

    assert len(orphan_posts) == 2
    for post in orphan_posts:
        assert post.integration_profile_id is None
