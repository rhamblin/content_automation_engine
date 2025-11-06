import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from common.db_core.models import Niche, Keyword, IntegrationProfile, Project, Tenant


# ============================================================================
# 1. UNIQUE CONSTRAINT TESTS
# ============================================================================

def test_niche_name_must_be_unique(db_session):
    """Test that two niches cannot have the same name (uq_niches_name)"""
    # Create first niche
    niche1 = Niche(name="Technology", domain="tech.com", default_budget=1000)
    db_session.add(niche1)
    db_session.commit()

    # Try to create second niche with same name
    niche2 = Niche(name="Technology", domain="different.com", default_budget=2000)
    db_session.add(niche2)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's the name unique constraint
    assert "uq_niches_name" in str(exc_info.value).lower() or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_niche_domain_must_be_unique(db_session):
    """Test that two niches cannot have the same domain (uq_niches_domain)"""
    # Create first niche
    niche1 = Niche(name="Technology", domain="tech.com", default_budget=1000)
    db_session.add(niche1)
    db_session.commit()

    # Try to create second niche with same domain
    niche2 = Niche(name="Different Name", domain="tech.com", default_budget=2000)
    db_session.add(niche2)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's the domain unique constraint
    assert "uq_niches_domain" in str(exc_info.value).lower() or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_update_niche_to_duplicate_name_fails(db_session):
    """Test that updating a niche to an existing name fails"""
    # Create two niches with different names
    niche1 = Niche(name="Technology", domain="tech.com", default_budget=1000)
    niche2 = Niche(name="Health", domain="health.com", default_budget=2000)
    db_session.add_all([niche1, niche2])
    db_session.commit()

    # Try to update niche2's name to match niche1
    niche2.name = "Technology"

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's the name unique constraint
    assert "uq_niches_name" in str(exc_info.value).lower() or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_update_niche_to_duplicate_domain_fails(db_session):
    """Test that updating a niche to an existing domain fails"""
    # Create two niches with different domains
    niche1 = Niche(name="Technology", domain="tech.com", default_budget=1000)
    niche2 = Niche(name="Health", domain="health.com", default_budget=2000)
    db_session.add_all([niche1, niche2])
    db_session.commit()

    # Try to update niche2's domain to match niche1
    niche2.domain = "tech.com"

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's the domain unique constraint
    assert "uq_niches_domain" in str(exc_info.value).lower() or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()


# ============================================================================
# 2. CASCADE DELETE TESTS
# ============================================================================

def test_delete_niche_cascades_to_keywords(db_session):
    """Test that deleting a niche cascades to delete all associated keywords"""
    # Create niche
    niche = Niche(name="Technology", domain="tech.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create keywords for this niche
    keyword1 = Keyword(niche_id=niche.niche_id, keyword="AI")
    keyword2 = Keyword(niche_id=niche.niche_id, keyword="Machine Learning")
    keyword3 = Keyword(niche_id=niche.niche_id, keyword="Data Science")
    db_session.add_all([keyword1, keyword2, keyword3])
    db_session.commit()

    # Verify keywords exist
    assert db_session.query(Keyword).filter_by(niche_id=niche.niche_id).count() == 3

    # Store keyword IDs for verification
    keyword_ids = [keyword1.keyword_id, keyword2.keyword_id, keyword3.keyword_id]

    # Delete niche
    db_session.delete(niche)
    db_session.commit()

    # Verify cascade delete - all keywords should be deleted
    assert db_session.query(Keyword).filter_by(niche_id=niche.niche_id).count() == 0
    for keyword_id in keyword_ids:
        assert db_session.query(Keyword).filter_by(keyword_id=keyword_id).first() is None


def test_delete_niche_cascades_to_integration_profiles(db_session):
    """Test that deleting a niche cascades to delete all associated integration profiles"""
    # Create dependencies
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    project = Project(tenant_id=tenant.tenant_id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    niche = Niche(name="Technology", domain="tech.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create integration profiles for this niche
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

    # Verify cascade delete - all integration profiles should be deleted
    assert db_session.query(IntegrationProfile).filter_by(niche_id=niche.niche_id).count() == 0
    for profile_id in profile_ids:
        assert db_session.query(IntegrationProfile).filter_by(integration_profile_id=profile_id).first() is None


# ============================================================================
# 3. MULTI-TENANT SCENARIOS
# ============================================================================

def test_niche_shared_across_multiple_projects(db_session):
    """Test that one niche can be used by multiple projects (multi-tenant scenario)"""
    # Create tenant and multiple projects
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    project1 = Project(tenant_id=tenant.tenant_id, name="Project 1")
    project2 = Project(tenant_id=tenant.tenant_id, name="Project 2")
    project3 = Project(tenant_id=tenant.tenant_id, name="Project 3")
    db_session.add_all([project1, project2, project3])
    db_session.commit()

    # Create single niche
    niche = Niche(name="Technology", domain="tech.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create integration profiles linking different projects to the same niche
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
    profile3 = IntegrationProfile(
        project_id=project3.project_id,
        niche_id=niche.niche_id,
        image_provider_key="midjourney",
        text_provider_key="gemini",
        channel_key="twitter"
    )
    db_session.add_all([profile1, profile2, profile3])
    db_session.commit()

    # Verify all three projects are using the same niche
    profiles = db_session.query(IntegrationProfile).filter_by(niche_id=niche.niche_id).all()
    assert len(profiles) == 3

    project_ids = {p.project_id for p in profiles}
    assert project_ids == {project1.project_id, project2.project_id, project3.project_id}

    # Verify niche can access all profiles via relationship
    db_session.expire_all()
    retrieved_niche = db_session.query(Niche).filter_by(niche_id=niche.niche_id).first()
    assert len(retrieved_niche.integration_profiles) == 3


def test_keyword_same_text_different_niches_allowed(db_session):
    """Test that the same keyword text can exist in different niches"""
    # Create two niches
    niche1 = Niche(name="Technology", domain="tech.com", default_budget=1000)
    niche2 = Niche(name="Health", domain="health.com", default_budget=2000)
    db_session.add_all([niche1, niche2])
    db_session.commit()

    # Create same keyword text in both niches - should succeed
    keyword1 = Keyword(niche_id=niche1.niche_id, keyword="innovation")
    keyword2 = Keyword(niche_id=niche2.niche_id, keyword="innovation")
    db_session.add_all([keyword1, keyword2])
    db_session.commit()

    # Verify both keywords exist with same text but different niches
    keywords = db_session.query(Keyword).filter_by(keyword="innovation").all()
    assert len(keywords) == 2
    assert keywords[0].keyword == keywords[1].keyword == "innovation"
    assert keywords[0].niche_id != keywords[1].niche_id


def test_keyword_duplicate_within_same_niche_fails(db_session):
    """Test that duplicate keyword within the same niche fails (uq_keyword_per_niche)"""
    # Create niche
    niche = Niche(name="Technology", domain="tech.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create first keyword
    keyword1 = Keyword(niche_id=niche.niche_id, keyword="AI")
    db_session.add(keyword1)
    db_session.commit()

    # Try to create duplicate keyword in same niche
    keyword2 = Keyword(niche_id=niche.niche_id, keyword="AI")
    db_session.add(keyword2)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's the unique constraint per niche
    assert "uq_keyword_per_niche" in str(exc_info.value).lower() or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()
