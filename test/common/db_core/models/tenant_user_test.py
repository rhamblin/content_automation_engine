import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from common.db_core.models import User, TenantUser, Tenant

def test_user_cascade_delete_to_tenant_users(db_session):
    """Test that deleting a user cascades to TenantUser (via cascade='all, delete')"""
    # Create user
    user = User(
        email="test@example.com",
        provider="google",
        provider_sub="google123"
    )
    db_session.add(user)

    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create association
    tenant_user = TenantUser(
        tenant_id=tenant.tenant_id,
        user_id=user.user_id,
        role="owner"
    )
    db_session.add(tenant_user)
    db_session.commit()

    # Verify association exists
    assert db_session.query(TenantUser).filter_by(user_id=user.user_id).first() is not None

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify cascade delete worked
    assert db_session.query(TenantUser).filter_by(user_id=user.user_id).first() is None
    # Tenant should still exist (only association deleted)
    assert db_session.query(Tenant).filter_by(tenant_id=tenant.tenant_id).first() is not None


def test_tenant_user_fk_enforcement_invalid_user(db_session):
    """Test that FK constraint prevents TenantUser with non-existent user_id"""
    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Try to create TenantUser with fake user_id
    fake_user_id = uuid.uuid4()
    tenant_user = TenantUser(
        tenant_id=tenant.tenant_id,
        user_id=fake_user_id,
        role="owner"
    )
    db_session.add(tenant_user)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a FK constraint violation
    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_user_relationship_loading(db_session):
    """Test that the tenant relationship works correctly (lazy='selectin')"""
    # Create user
    user = User(
        email="test@example.com",
        provider="google",
        provider_sub="google123"
    )
    db_session.add(user)

    # Create tenant
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    # Create association
    tenant_user = TenantUser(tenant_id=tenant.tenant_id, user_id=user.user_id, role="owner")
    db_session.add(tenant_user)
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve user and verify relationship loaded
    retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert retrieved_user.tenant is not None
    assert retrieved_user.tenant.role == "owner"
    assert retrieved_user.tenant.tenant_id == tenant.tenant_id


def test_user_can_only_belong_to_one_tenant(db_session):
    """Test that the unique constraint prevents a user from belonging to multiple tenants"""
    # Create user
    user = User(
        email="test@example.com",
        provider="google",
        provider_sub="google123"
    )
    db_session.add(user)

    # Create two tenants
    tenant1 = Tenant(name="Tenant 1")
    tenant2 = Tenant(name="Tenant 2")
    db_session.add_all([tenant1, tenant2])
    db_session.commit()

    # Create first association
    tenant_user1 = TenantUser(tenant_id=tenant1.tenant_id, user_id=user.user_id, role="owner")
    db_session.add(tenant_user1)
    db_session.commit()

    # Try to create second association with same user - should fail
    tenant_user2 = TenantUser(tenant_id=tenant2.tenant_id, user_id=user.user_id, role="member")
    db_session.add(tenant_user2)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a unique constraint violation
    assert "uq_tenant_users_user_id" in str(exc_info.value).lower() or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()