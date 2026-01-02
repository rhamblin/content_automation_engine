import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from common.db_core.models import Project, Tenant, IntegrationProfile, Niche


def test_project_auto_generated_fields(db_session):
    """Test that project_id and created_at are auto-generated"""
    # Create a tenant first (required FK)
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create project
    project = Project(tenant_id=tenant.tenant_id, name="Test Project")

    db_session.add(project)
    db_session.flush()  # Trigger default value generation

    # After flush (before commit), defaults should be set
    assert project.project_id is not None
    assert isinstance(project.project_id, uuid.UUID)
    assert project.created_at is not None
    assert isinstance(project.created_at, datetime)

    db_session.commit()

    # After commit, values should be maintained
    assert project.project_id is not None
    assert project.created_at is not None


def test_project_required_fields_enforcement(db_session):
    """Test that nullable=False constraints are enforced at DB level"""
    # Create a tenant first
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Missing name
    project = Project(tenant_id=tenant.tenant_id)
    project.name = None  # Explicitly set to None
    db_session.add(project)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Missing tenant_id
    project = Project(name="Test Project")
    project.tenant_id = None  # Explicitly set to None
    db_session.add(project)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_project_requires_valid_tenant_fk(db_session):
    """Test that project must reference an existing tenant (FK constraint)"""
    # Try to create Project with fake tenant_id
    fake_tenant_id = uuid.uuid4()
    project = Project(tenant_id=fake_tenant_id, name="Orphan Project")
    db_session.add(project)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a FK constraint violation
    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_project_tenant_relationship_loading(db_session):
    """Test that project.tenant relationship works bidirectionally"""
    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create project
    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve project and verify tenant relationship loaded
    retrieved_project = db_session.query(Project).filter_by(name="Test Project").first()

    assert retrieved_project.tenant is not None
    assert retrieved_project.tenant.tenant_id == tenant.tenant_id
    assert retrieved_project.tenant.name == "Test Tenant"


def test_multiple_projects_per_tenant(db_session):
    """Test that one tenant can own multiple projects"""
    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create multiple projects for same tenant
    project1 = Project(tenant_id=tenant.tenant_id, name="Project 1")
    project2 = Project(tenant_id=tenant.tenant_id, name="Project 2")
    project3 = Project(tenant_id=tenant.tenant_id, name="Project 3")
    db_session.add_all([project1, project2, project3])
    db_session.commit()

    # Verify all projects belong to same tenant
    projects = db_session.query(Project).filter_by(tenant_id=tenant.tenant_id).all()
    assert len(projects) == 3
    project_names = {p.name for p in projects}
    assert project_names == {"Project 1", "Project 2", "Project 3"}

    # Verify tenant can access all projects via relationship
    db_session.expire_all()
    retrieved_tenant = db_session.query(Tenant).filter_by(name="Test Tenant").first()
    assert len(retrieved_tenant.projects) == 3


def test_project_cascade_delete_from_tenant(db_session):
    """Test that deleting tenant cascades to delete projects (ON DELETE CASCADE)"""
    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create projects for the tenant
    project1 = Project(tenant_id=tenant.tenant_id, name="Project 1")
    project2 = Project(tenant_id=tenant.tenant_id, name="Project 2")
    db_session.add_all([project1, project2])
    db_session.commit()

    # Verify projects exist
    assert db_session.query(Project).filter_by(tenant_id=tenant.tenant_id).count() == 2

    # Store project IDs for verification
    project_ids = [project1.project_id, project2.project_id]

    # Delete tenant
    db_session.delete(tenant)
    db_session.commit()

    # Verify cascade delete worked - projects should be deleted
    assert db_session.query(Project).filter_by(tenant_id=tenant.tenant_id).count() == 0
    for project_id in project_ids:
        assert db_session.query(Project).filter_by(project_id=project_id).first() is None


def test_project_cascade_delete_to_integration_profiles(db_session):
    """Test that deleting project cascades to delete integration profiles"""
    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create project
    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    # Create niche (required for integration profile)
    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create integration profiles for the project
    profile1 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        text_provider_key="openai",
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        text_provider_key="claude",
        channel_key="instagram"
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Verify integration profiles exist
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


def test_project_integration_profiles_relationship(db_session):
    """Test that project can access its integration_profiles via relationship"""
    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create project
    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    # Create niche
    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create integration profiles
    profile1 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        text_provider_key="openai",
        channel_key="pinterest"
    )
    profile2 = IntegrationProfile(
        project_id=project.project_id,
        niche_id=niche.niche_id,
        text_provider_key="claude",
        channel_key="instagram"
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve project and verify integration_profiles relationship loaded
    retrieved_project = db_session.query(Project).filter_by(name="Test Project").first()

    assert retrieved_project.integration_profiles is not None
    assert len(retrieved_project.integration_profiles) == 2

    # Verify the profiles are correctly associated
    channel_keys = {p.channel_key for p in retrieved_project.integration_profiles}
    assert channel_keys == {"pinterest", "instagram"}
