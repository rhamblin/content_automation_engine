import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from common.db_core.models import IntegrationProfile, Project, Tenant, Niche, Post


def test_integration_profile_auto_generated_fields(db_session):
    """Test that integration_profile_id and created_at are auto-generated"""
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

    # Create integration profile
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )

    db_session.add(profile)
    db_session.flush()  # Trigger default value generation

    # After flush (before commit), defaults should be set
    assert profile.integration_profile_id is not None
    assert isinstance(profile.integration_profile_id, uuid.UUID)
    assert profile.created_at is not None
    assert isinstance(profile.created_at, datetime)

    db_session.commit()

    # After commit, values should be maintained
    assert profile.integration_profile_id is not None
    assert profile.created_at is not None


def test_integration_profile_requires_project_id(db_session):
    """Test that project_id is required (nullable=False constraint)"""
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

    # Try to create IntegrationProfile with project_id = None
    profile = IntegrationProfile(
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    profile.project_id = None  # Explicitly set to None
    db_session.add(profile)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_integration_profile_requires_niche_id(db_session):
    """Test that niche_id is required (nullable=False constraint)"""
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

    # Try to create IntegrationProfile with niche_id = None
    profile = IntegrationProfile(
        project_id=project.project_id,
        channel_key="pinterest"
    )
    profile.niche_id = None  # Explicitly set to None
    db_session.add(profile)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_integration_profile_requires_channel_key(db_session):
    """Test that channel_key is required (nullable=False constraint)"""
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

    # Try to create IntegrationProfile with channel_key = None
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id
    )
    profile.channel_key = None  # Explicitly set to None
    db_session.add(profile)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_integration_profile_requires_valid_project_fk(db_session):
    """Test that integration profile must reference an existing project (FK constraint)"""
    # Create niche dependency
    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Try to create IntegrationProfile with fake project_id
    fake_project_id = uuid.uuid4()
    profile = IntegrationProfile(
        project_id=fake_project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a FK constraint violation
    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_integration_profile_requires_valid_niche_fk(db_session):
    """Test that integration profile must reference an existing niche (FK constraint)"""
    # Create project dependencies
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    # Try to create IntegrationProfile with fake niche_id
    fake_niche_id = uuid.uuid4()
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=fake_niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a FK constraint violation
    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_integration_profile_settings_defaults_to_empty_dict(db_session):
    """Test that settings field defaults to empty dict when not provided"""
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

    # Create profile without settings
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Verify settings defaults to empty dict
    assert profile.settings == {}
    assert isinstance(profile.settings, dict)


def test_integration_profile_settings_stores_complex_json(db_session):
    """Test that settings can store and retrieve complex JSON structures"""
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

    # Create complex settings
    complex_settings = {
        "posting_schedule": {
            "frequency": "daily",
            "times": ["09:00", "15:00", "21:00"]
        },
        "hashtags": ["#tech", "#ai", "#automation"],
        "content_preferences": {
            "tone": "professional",
            "max_length": 280,
            "include_emojis": False
        },
        "budget_allocation": {
            "ads": 500,
            "content": 300
        }
    }

    # Create profile with complex settings
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest",
        settings=complex_settings
    )
    db_session.add(profile)
    db_session.commit()

    # Clear session to test persistence
    db_session.expire_all()

    # Retrieve and verify
    retrieved_profile = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).first()

    assert retrieved_profile.settings == complex_settings
    assert retrieved_profile.settings["posting_schedule"]["frequency"] == "daily"
    assert len(retrieved_profile.settings["hashtags"]) == 3
    assert retrieved_profile.settings["budget_allocation"]["ads"] == 500


def test_integration_profile_project_relationship(db_session):
    """Test that integration_profile.project relationship works correctly"""
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

    # Create integration profile
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve profile and verify project relationship loaded
    retrieved_profile = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).first()

    assert retrieved_profile.project is not None
    assert retrieved_profile.project.project_id == project.project_id
    assert retrieved_profile.project.name == "Test Project"


def test_integration_profile_niche_relationship(db_session):
    """Test that integration_profile.niche relationship works correctly"""
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

    # Create integration profile
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve profile and verify niche relationship loaded
    retrieved_profile = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).first()

    assert retrieved_profile.niche is not None
    assert retrieved_profile.niche.niche_id == niche.niche_id
    assert retrieved_profile.niche.name == "Test Niche"


def test_delete_project_cascades_to_integration_profiles(db_session):
    """Test that deleting project cascades to delete integration profiles (ON DELETE CASCADE)"""
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

    # Create integration profiles for the project
    profile1 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="instagram"
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Verify profiles exist
    assert db_session.query(IntegrationProfile).filter_by(project_id=project.project_id).count() == 2

    # Store profile IDs for verification
    profile_ids = [profile1.integration_profile_id, profile2.integration_profile_id]

    # Delete project
    db_session.delete(project)
    db_session.commit()

    # Verify cascade delete worked - integration profiles should be deleted
    assert db_session.query(IntegrationProfile).filter_by(project_id=project.project_id).count() == 0
    for profile_id in profile_ids:
        assert db_session.query(IntegrationProfile).filter_by(integration_profile_id=profile_id).first() is None


def test_delete_niche_cascades_to_integration_profiles(db_session):
    """Test that deleting niche cascades to delete integration profiles (ON DELETE CASCADE)"""
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

    # Create integration profiles for the niche
    profile1 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="instagram"
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Verify profiles exist
    assert db_session.query(IntegrationProfile).filter_by(niche_id=niche.niche_id).count() == 2

    # Store profile IDs for verification
    profile_ids = [profile1.integration_profile_id, profile2.integration_profile_id]

    # Delete niche
    db_session.delete(niche)
    db_session.commit()

    # Verify cascade delete worked - integration profiles should be deleted
    assert db_session.query(IntegrationProfile).filter_by(niche_id=niche.niche_id).count() == 0
    for profile_id in profile_ids:
        assert db_session.query(IntegrationProfile).filter_by(integration_profile_id=profile_id).first() is None


def test_multiple_integration_profiles_per_project(db_session):
    """Test that one project can have multiple integration profiles"""
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

    # Create multiple profiles for same project
    profile1 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="instagram"
    )
    profile3 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="twitter"
    )
    db_session.add_all([profile1, profile2, profile3])
    db_session.commit()

    # Verify all profiles belong to same project
    profiles = db_session.query(IntegrationProfile).filter_by(project_id=project.project_id).all()
    assert len(profiles) == 3
    channel_keys = {p.channel_key for p in profiles}
    assert channel_keys == {"pinterest", "instagram", "twitter"}

    # Verify project can access all profiles via relationship
    db_session.expire_all()
    retrieved_project = db_session.query(Project).filter_by(name="Test Project").first()
    assert len(retrieved_project.integration_profiles) == 3


def test_multiple_integration_profiles_per_niche(db_session):
    """Test that one niche can be used by multiple integration profiles"""
    # Create dependencies
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    project1 = Project(tenant_id=tenant.tenant_id, name="Project 1")
    project2 = Project(tenant_id=tenant.tenant_id, name="Project 2")
    db_session.add_all([project1, project2])
    db_session.commit()

    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create multiple profiles using same niche
    profile1 = IntegrationProfile(
        project_id=project1.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project2.project_id,
        niche_id=niche.niche_id,
        channel_key="instagram"
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Verify all profiles use same niche
    profiles = db_session.query(IntegrationProfile).filter_by(niche_id=niche.niche_id).all()
    assert len(profiles) == 2

    # Verify niche can access all profiles via relationship
    db_session.expire_all()
    retrieved_niche = db_session.query(Niche).filter_by(name="Test Niche").first()
    assert len(retrieved_niche.integration_profiles) == 2


def test_integration_profile_different_channel_combinations(db_session):
    """Test various valid channel combinations"""
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

    # Test different channels
    channels = ["pinterest", "instagram", "twitter", "facebook"]

    profiles = []
    for channel in channels:
        profile = IntegrationProfile(
            project_id=project.project_id,
            niche_id=niche.niche_id,
            channel_key=channel
        )
        profiles.append(profile)

    db_session.add_all(profiles)
    db_session.commit()

    # Verify all channels were stored correctly
    retrieved_profiles = db_session.query(IntegrationProfile).filter_by(project_id=project.project_id).all()
    assert len(retrieved_profiles) == 4

    for profile in retrieved_profiles:
        assert profile.channel_key is not None
        assert profile.channel_key in channels


def test_integration_profile_with_identical_combinations(db_session):
    """Test that creating duplicate profiles with identical (project, niche, channel) raises IntegrityError"""
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

    # Create first profile
    profile1 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest",
        settings={"theme": "dark"}
    )
    db_session.add(profile1)
    db_session.commit()

    # Try to create second profile with identical combination
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest",
        settings={"theme": "light"}
    )
    db_session.add(profile2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a unique constraint violation
    assert "unique constraint" in str(exc_info.value).lower() or "uq_integration_profile_combination" in str(exc_info.value).lower()
    db_session.rollback()


def test_delete_integration_profile_sets_null_on_posts(db_session):
    """Test that deleting integration profile sets integration_profile_id to NULL on posts (ON DELETE SET NULL)"""
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

    # Create integration profile
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Create posts associated with this profile
    post1 = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image1.jpg",
        title="Test Post 1",
        description="Description 1",
        hashtags=["#test"]
    )
    post2 = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image2.jpg",
        title="Test Post 2",
        description="Description 2",
        hashtags=["#test"]
    )
    db_session.add_all([post1, post2])
    db_session.commit()

    # Store post IDs for later verification
    post_ids = [post1.post_id, post2.post_id]

    # Verify posts are linked to profile
    assert db_session.query(Post).filter_by(integration_profile_id=profile.integration_profile_id).count() == 2

    # Delete integration profile
    db_session.delete(profile)
    db_session.commit()

    # Verify posts still exist but integration_profile_id is NULL
    for post_id in post_ids:
        post = db_session.query(Post).filter_by(post_id=post_id).first()
        assert post is not None  # Post should still exist
        assert post.integration_profile_id is None  # FK should be NULL

    # Verify posts count remains the same
    assert db_session.query(Post).filter(Post.post_id.in_(post_ids)).count() == 2


def test_integration_profile_posts_relationship_empty(db_session):
    """Test that integration_profile.posts returns empty list when no posts exist"""
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

    # Create integration profile without posts
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve profile and verify posts collection is empty
    retrieved_profile = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).first()

    assert retrieved_profile.posts == []
    assert len(retrieved_profile.posts) == 0


def test_integration_profile_posts_relationship_loaded(db_session):
    """Test that integration_profile.posts relationship loads all associated posts"""
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

    # Create integration profile
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Create multiple posts for this profile
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

    # Store post IDs for verification
    expected_post_ids = {post1.post_id, post2.post_id, post3.post_id}

    # Clear session to test lazy loading (with selectin)
    db_session.expire_all()

    # Retrieve profile and verify posts relationship loaded
    retrieved_profile = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).first()

    assert len(retrieved_profile.posts) == 3
    loaded_post_ids = {post.post_id for post in retrieved_profile.posts}
    assert loaded_post_ids == expected_post_ids

    # Verify post data is accessible
    for post in retrieved_profile.posts:
        assert post.asset_url.startswith("https://example.com/")
        assert post.title.startswith("Test Post")
        assert post.description.startswith("Description")


def test_integration_profile_posts_relationship_selectin_loading(db_session):
    """Test that integration_profile.posts uses selectin loading (lazy='selectin')"""
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

    # Create integration profile
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Create posts for this profile
    for i in range(5):
        post = Post(
            integration_profile_id=profile.integration_profile_id,
            asset_url=f"https://example.com/image{i}.jpg",
            title=f"Test Post {i}",
            description=f"Description {i}"
        )
        db_session.add(post)
    db_session.commit()

    # Clear session
    db_session.expire_all()

    # Retrieve profile - posts should be loaded via selectin
    retrieved_profile = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).first()

    # Accessing posts should not trigger additional queries (already loaded)
    # This is a behavioral test - with selectin, posts are preloaded
    assert len(retrieved_profile.posts) == 5


def test_integration_profile_posts_count(db_session):
    """Test counting posts associated with an integration profile"""
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
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="instagram"
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Create different numbers of posts for each profile
    for i in range(7):
        post = Post(
            integration_profile_id=profile1.integration_profile_id,
            asset_url=f"https://example.com/profile1_image{i}.jpg",
            title=f"Profile 1 Post {i}",
            description=f"Description {i}"
        )
        db_session.add(post)

    for i in range(3):
        post = Post(
            integration_profile_id=profile2.integration_profile_id,
            asset_url=f"https://example.com/profile2_image{i}.jpg",
            title=f"Profile 2 Post {i}",
            description=f"Description {i}"
        )
        db_session.add(post)

    db_session.commit()

    # Clear session
    db_session.expire_all()

    # Retrieve profiles and verify post counts
    retrieved_profile1 = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile1.integration_profile_id
    ).first()
    retrieved_profile2 = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile2.integration_profile_id
    ).first()

    assert len(retrieved_profile1.posts) == 7
    assert len(retrieved_profile2.posts) == 3


def test_integration_profile_posts_with_different_statuses(db_session):
    """Test accessing posts through integration_profile with different post statuses"""
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

    # Create integration profile
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        channel_key="pinterest"
    )
    db_session.add(profile)
    db_session.commit()

    # Create posts with different statuses
    from common.db_core.models import PostStatus

    post1 = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image1.jpg",
        title="Generated Post",
        description="Description",
        status=PostStatus.generated.value
    )
    post2 = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image2.jpg",
        title="Ready Post",
        description="Description",
        status=PostStatus.ready.value
    )
    post3 = Post(
        integration_profile_id=profile.integration_profile_id,
        asset_url="https://example.com/image3.jpg",
        title="Posted Post",
        description="Description",
        status=PostStatus.posted.value
    )
    db_session.add_all([post1, post2, post3])
    db_session.commit()

    # Clear session
    db_session.expire_all()

    # Retrieve profile and verify all posts are accessible regardless of status
    retrieved_profile = db_session.query(IntegrationProfile).filter_by(
        integration_profile_id=profile.integration_profile_id
    ).first()

    assert len(retrieved_profile.posts) == 3

    # Verify we can filter posts by status
    statuses = {post.status for post in retrieved_profile.posts}
    assert PostStatus.generated.value in statuses
    assert PostStatus.ready.value in statuses
    assert PostStatus.posted.value in statuses
