from common.auth import AuthContext, AuthorizationError
from common.repositories.tenant_scoped.niche_repository import NicheRepository
from fastapi import APIRouter, Request

router = APIRouter()


def _get_deps():
    from management_api.app import db, require_auth
    return db, require_auth


@router.get("/niches")
async def get_niches(request: Request):
    db, require_auth = _get_deps()
    auth: AuthContext = await require_auth(request)

    if not auth.tenant_roles:
        raise AuthorizationError("User has no tenant")

    tenant_id = auth.tenant_roles[0].tenant_id

    async with db.get_session() as session:
        niche_repo = NicheRepository(session, tenant_id)
        niches = await niche_repo.get_all(include_only_active=True)

    return [
        {
            "id": str(n.external_id),
            "title": n.title,
            "brand_name": n.brand_name,
            "is_active": n.is_active,
        }
        for n in niches
    ]
