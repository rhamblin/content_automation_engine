import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from common.db_core.models import Tenant, User, TenantUser, Project


def test_tenant_auto_generated_fields(db_session):
    """Verify that tenants automatically get an ID and creation timestamp"""
    tenant = Tenant(name="Test Tenant")

    db_session.add(tenant)
    db_session.flush()  # Trigger default value generation

    # After flush (before commit), defaults should be set
    assert tenant.tenant_id is not None
    assert isinstance(tenant.tenant_id, uuid.UUID)
    assert tenant.created_at is not None
    assert isinstance(tenant.created_at, datetime)

    db_session.commit()

    # After commit, values should be maintained
    assert tenant.tenant_id is not None
    assert tenant.created_at is not None


def test_tenant_required_fields_enforcement(db_session):
    """Verify that tenants must have a name (database won't accept empty tenants)"""
    # Missing name
    tenant = Tenant()
    tenant.name = None  # Explicitly set to None
    db_session.add(tenant)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_tenant_cascade_delete_to_projects(db_session):
    """Verify that deleting a tenant also removes all its projects"""
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

    # Delete tenant
    db_session.delete(tenant)
    db_session.commit()

    # Verify cascade delete worked - projects should be deleted
    assert db_session.query(Project).filter_by(tenant_id=tenant.tenant_id).count() == 0


def test_tenant_cascade_delete_to_tenant_users(db_session):
    """Verify that deleting a tenant removes user associations but keeps the users"""
    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)

    # Create users
    user1 = User(email="user1@example.com", provider="google", provider_sub="sub1")
    user2 = User(email="user2@example.com", provider="google", provider_sub="sub2")
    db_session.add_all([user1, user2])
    db_session.commit()

    # Create associations
    tenant_user1 = TenantUser(tenant_id=tenant.tenant_id, user_id=user1.user_id, role="owner")
    tenant_user2 = TenantUser(tenant_id=tenant.tenant_id, user_id=user2.user_id, role="member")
    db_session.add_all([tenant_user1, tenant_user2])
    db_session.commit()

    # Verify associations exist
    assert db_session.query(TenantUser).filter_by(tenant_id=tenant.tenant_id).count() == 2

    # Delete tenant
    db_session.delete(tenant)
    db_session.commit()

    # Verify cascade delete worked - associations deleted
    assert db_session.query(TenantUser).filter_by(tenant_id=tenant.tenant_id).count() == 0

    # Verify users still exist (only associations deleted, not the users themselves)
    assert db_session.query(User).filter_by(user_id=user1.user_id).first() is not None
    assert db_session.query(User).filter_by(user_id=user2.user_id).first() is not None


def test_tenant_relationships_loading(db_session):
    """Verify that a tenant can access its projects and users"""
    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create projects
    project1 = Project(tenant_id=tenant.tenant_id, name="Project 1")
    project2 = Project(tenant_id=tenant.tenant_id, name="Project 2")
    db_session.add_all([project1, project2])

    # Create user and association
    user = User(email="test@example.com", provider="google", provider_sub="sub123")
    db_session.add(user)
    db_session.commit()

    tenant_user = TenantUser(tenant_id=tenant.tenant_id, user_id=user.user_id, role="owner")
    db_session.add(tenant_user)
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve tenant and verify relationships loaded
    retrieved_tenant = db_session.query(Tenant).filter_by(name="Test Tenant").first()

    # Test projects relationship
    assert retrieved_tenant.projects is not None
    assert len(retrieved_tenant.projects) == 2
    project_names = {p.name for p in retrieved_tenant.projects}
    assert project_names == {"Project 1", "Project 2"}

    # Test users relationship
    assert retrieved_tenant.users is not None
    assert len(retrieved_tenant.users) == 1
    assert retrieved_tenant.users[0].user_id == user.user_id
    assert retrieved_tenant.users[0].role == "owner"


def test_tenant_fk_enforcement_in_project(db_session):
    """Verify that projects cannot be created with an invalid tenant ID"""
    # Try to create Project with fake tenant_id
    fake_tenant_id = uuid.uuid4()
    project = Project(tenant_id=fake_tenant_id, name="Orphan Project")
    db_session.add(project)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a FK constraint violation
    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()
