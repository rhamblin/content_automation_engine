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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest"
    )
    profile.niche_id = None  # Explicitly set to None
    db_session.add(profile)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_integration_profile_requires_image_provider_key(db_session):
    """Test that image_provider_key is required (nullable=False constraint)"""
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

    # Try to create IntegrationProfile with image_provider_key = None
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        text_provider_key="openai",
        channel_key="pinterest"
    )
    profile.image_provider_key = None  # Explicitly set to None
    db_session.add(profile)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_integration_profile_requires_text_provider_key(db_session):
    """Test that text_provider_key is required (nullable=False constraint)"""
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

    # Try to create IntegrationProfile with text_provider_key = None
    profile = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        image_provider_key="unsplash",
        channel_key="pinterest"
    )
    profile.text_provider_key = None  # Explicitly set to None
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
        niche_id=niche.niche_id,
        image_provider_key="unsplash",
        text_provider_key="openai"
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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
    profile3 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        image_provider_key="midjourney",
        text_provider_key="gemini",
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
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project2.project_id,
        niche_id=niche.niche_id,
        image_provider_key="dalle",
        text_provider_key="claude",
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


def test_integration_profile_different_provider_combinations(db_session):
    """Test various valid combinations of image/text/channel providers"""
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

    # Test different provider combinations
    combinations = [
        ("unsplash", "openai", "pinterest"),
        ("dalle", "claude", "instagram"),
        ("midjourney", "gemini", "twitter"),
        ("pexels", "openai", "facebook"),
    ]

    profiles = []
    for img_provider, text_provider, channel in combinations:
        profile = IntegrationProfile(
            project_id=project.project_id,
            niche_id=niche.niche_id,
            image_provider_key=img_provider,
            text_provider_key=text_provider,
            channel_key=channel
        )
        profiles.append(profile)

    db_session.add_all(profiles)
    db_session.commit()

    # Verify all combinations were stored correctly
    retrieved_profiles = db_session.query(IntegrationProfile).filter_by(project_id=project.project_id).all()
    assert len(retrieved_profiles) == 4

    for profile in retrieved_profiles:
        assert profile.image_provider_key is not None
        assert profile.text_provider_key is not None
        assert profile.channel_key is not None

        # Verify the combination exists in our original set
        combo = (profile.image_provider_key, profile.text_provider_key, profile.channel_key)
        assert combo in combinations


def test_integration_profile_with_identical_provider_combinations(db_session):
    """Test creating multiple profiles with identical provider combinations (should be allowed)"""
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

    # Create two profiles with identical provider combinations but different settings
    profile1 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest",
        settings={"theme": "dark"}
    )
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest",
        settings={"theme": "light"}
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Verify both profiles exist with same provider combination
    profiles = db_session.query(IntegrationProfile).filter_by(
        project_id=project.project_id,
        image_provider_key="unsplash",
        text_provider_key="openai",
        channel_key="pinterest"
    ).all()

    assert len(profiles) == 2
    assert profiles[0].settings != profiles[1].settings


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
        image_provider_key="unsplash",
        text_provider_key="openai",
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
