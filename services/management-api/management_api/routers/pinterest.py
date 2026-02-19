import hashlib
import hmac
import json
from urllib.parse import urlencode
from uuid import UUID

import httpx
from common.app_logger import AppLogger
from common.auth import AuthContext, AuthenticationError, AuthorizationError
from common.repositories.cross_tenant.channel_repository import ChannelRepository
from common.repositories.tenant_scoped.channel_credential_repository import ChannelCredentialRepository
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

logger = AppLogger(__name__)
router = APIRouter(prefix="/pinterest")

PINTEREST_AUTH_URL = "https://www.pinterest.com/oauth/"
PINTEREST_TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
PINTEREST_SCOPES = "boards:read,pins:read,pins:write"


def _get_deps():
    from management_api.app import db, require_auth, settings
    return db, require_auth, settings


def _sign_state(payload: str, secret: str) -> str:
    """Create HMAC-SHA256 signature for OAuth state."""
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _build_state(tenant_id: UUID, secret: str) -> str:
    """Encode tenant_id into a signed state parameter."""
    payload = json.dumps({"tenant_id": str(tenant_id)})
    sig = _sign_state(payload, secret)
    return f"{payload}|{sig}"


def _verify_state(state: str, secret: str) -> UUID:
    """Verify and extract tenant_id from signed state parameter."""
    parts = state.split("|", 1)
    if len(parts) != 2:
        raise AuthenticationError("Invalid OAuth state")

    payload, sig = parts
    expected_sig = _sign_state(payload, secret)
    if not hmac.compare_digest(sig, expected_sig):
        raise AuthenticationError("Invalid OAuth state signature")

    data = json.loads(payload)
    return UUID(data["tenant_id"])


@router.get("/connect")
async def pinterest_connect(tenant_id: UUID, request: Request):
    _, require_auth, settings = _get_deps()

    if not settings.pinterest_app_id or not settings.pinterest_app_secret:
        raise AuthorizationError("Pinterest OAuth is not configured")

    auth: AuthContext = await require_auth(request)

    # Verify user belongs to the requested tenant
    tenant_ids = {tr.tenant_id for tr in auth.tenant_roles}
    if tenant_id not in tenant_ids:
        raise AuthorizationError("User does not belong to this tenant")

    state = _build_state(tenant_id, settings.pinterest_app_secret)
    redirect_uri = f"{settings.frontend_url.rstrip('/')}/api/pinterest/callback"

    params = urlencode({
        "client_id": settings.pinterest_app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": PINTEREST_SCOPES,
        "state": state,
    })

    return RedirectResponse(f"{PINTEREST_AUTH_URL}?{params}")


@router.get("/callback")
async def pinterest_callback(request: Request):
    db, _, settings = _get_deps()

    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        error = request.query_params.get("error_description", "Pinterest authorization failed")
        params = urlencode({"error": error})
        return RedirectResponse(f"{settings.frontend_url}/channels?{params}")

    # Verify state and extract tenant_id
    try:
        tenant_id = _verify_state(state, settings.pinterest_app_secret)
    except (AuthenticationError, Exception) as exc:
        logger.warning(f"Pinterest OAuth state verification failed: {exc}")
        params = urlencode({"error": "Invalid OAuth state"})
        return RedirectResponse(f"{settings.frontend_url}/channels?{params}")

    # Exchange code for access token
    redirect_uri = f"{settings.frontend_url.rstrip('/')}/api/pinterest/callback"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            PINTEREST_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            auth=(settings.pinterest_app_id, settings.pinterest_app_secret),
        )

    if response.status_code != 200:
        logger.warning(f"Pinterest token exchange failed: {response.status_code} {response.text}")
        params = urlencode({"error": "Failed to exchange Pinterest authorization code"})
        return RedirectResponse(f"{settings.frontend_url}/channels?{params}")

    token_data = response.json()

    # Store credentials
    async with db.get_session() as session:
        channel_repo = ChannelRepository(session)
        channel = await channel_repo.get_or_create_by_identifier("pinterest")

        cred_repo = ChannelCredentialRepository(session, tenant_id)
        await cred_repo.upsert(
            channel_id=channel.external_id,
            credentials={
                "access_token": token_data.get("access_token", ""),
                "refresh_token": token_data.get("refresh_token", ""),
                "token_type": token_data.get("token_type", ""),
                "expires_in": token_data.get("expires_in", 0),
                "scope": token_data.get("scope", ""),
            },
        )

        await session.commit()

    params = urlencode({"pinterest": "connected"})
    return RedirectResponse(f"{settings.frontend_url}/channels?{params}")
