from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import httpx
import jwt
from common.app_logger import AppLogger
from common.auth import AuthContext, AuthenticationError
from common.contracts.database_models import UsersIdentityProviders
from common.repositories.cross_tenant.user_repository import UserRepository
from common.repositories.cross_tenant.user_session_repository import UserSessionRepository
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

logger = AppLogger(__name__)
router = APIRouter()


def _get_deps():
    """Late import to avoid circular dependency with app wiring."""
    from management_api.app import db, require_auth, settings, token_encryptor, token_validator
    return db, require_auth, settings, token_encryptor, token_validator


@router.get("/entra/callback")
async def entra_callback(request: Request):
    db, _, settings, token_encryptor, _ = _get_deps()

    code = request.query_params.get("code")
    if not code:
        error = request.query_params.get("error_description", "No auth code received")
        params = urlencode({"error": error})
        return RedirectResponse(f"{settings.frontend_url}/login?{params}")

    token_url = (
        f"https://login.microsoftonline.com/"
        f"{settings.azure_entra_tenant_id}/oauth2/v2.0/token"
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "client_id": settings.azure_entra_client_id,
                "client_secret": settings.azure_entra_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{request.base_url}entra/callback",
                "scope": "openid profile email User.Read offline_access",
            },
        )

    if response.status_code != 200:
        logger.warning(f"Token exchange failed: {response.status_code}")
        params = urlencode({"error": "Authentication failed"})
        return RedirectResponse(f"{settings.frontend_url}/login?{params}")

    token_data = response.json()
    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")
    id_token = token_data.get("id_token", "")

    try:
        id_claims = jwt.decode(id_token, options={"verify_signature": False})
    except jwt.PyJWTError:
        params = urlencode({"error": "Failed to decode identity token"})
        return RedirectResponse(f"{settings.frontend_url}/login?{params}")

    oid = id_claims.get("oid") or id_claims.get("sub")
    email = id_claims.get("preferred_username") or id_claims.get("email", "")

    if not oid or not email:
        params = urlencode({"error": "Missing identity claims"})
        return RedirectResponse(f"{settings.frontend_url}/login?{params}")

    provider_user_id = UUID(oid)

    async with db.get_session() as session:
        user_repo = UserRepository(session)
        session_repo = UserSessionRepository(session)

        user = await user_repo.get_by_identity_provider(
            provider="azure_entra",
            provider_user_id=provider_user_id,
        )

        if user is None:
            user = await user_repo.get_by_email(email)
            if user is None:
                user = await user_repo.add(email=email)

            await user_repo.add_identity_provider(
                UsersIdentityProviders(
                    user_id=user.external_id,
                    identity_provider_user_id=provider_user_id,
                    identity_provider="azure_entra",
                )
            )

        await session_repo.delete_by_user(user.external_id)
        if refresh_token:
            stored_token = token_encryptor.encrypt(refresh_token) if token_encryptor else refresh_token
            expires_at = datetime.now(timezone.utc) + timedelta(days=90)
            await session_repo.add(
                user_id=user.external_id,
                refresh_token=stored_token,
                identity_provider="azure_entra",
                expires_at=expires_at,
            )

        await session.commit()

    redirect = RedirectResponse(f"{settings.frontend_url}/welcome")
    redirect.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.app_environment != "development",
        samesite="lax",
        max_age=3600,
    )
    return redirect


@router.get("/me")
async def me(request: Request):
    _, require_auth, _, _, _ = _get_deps()
    auth: AuthContext = await require_auth(request)
    return {
        "user_id": str(auth.user_id),
        "email": auth.email,
        "tenants": [
            {"tenant_id": str(tr.tenant_id), "role": tr.role}
            for tr in auth.tenant_roles
        ],
        "scopes": auth.scopes,
    }


@router.post("/auth/refresh")
async def auth_refresh(request: Request):
    db, _, settings, token_encryptor, token_validator = _get_deps()

    token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationError("No access token cookie")

    claims = token_validator.decode_unverified(token)
    oid = claims.get("oid") or claims.get("sub")
    if not oid:
        raise AuthenticationError("Cannot identify user from token")

    provider_user_id = UUID(oid)

    async with db.get_session() as session:
        user_repo = UserRepository(session)
        session_repo = UserSessionRepository(session)

        user = await user_repo.get_by_identity_provider(
            provider="azure_entra",
            provider_user_id=provider_user_id,
        )
        if user is None:
            raise AuthenticationError("User not found")

        user_session = await session_repo.get_active_by_user(user.external_id)
        if user_session is None:
            raise AuthenticationError("No active session — please log in again")

        stored_refresh_token = (
            token_encryptor.decrypt(user_session.refresh_token)
            if token_encryptor
            else user_session.refresh_token
        )

        token_url = (
            f"https://login.microsoftonline.com/"
            f"{settings.azure_entra_tenant_id}/oauth2/v2.0/token"
        )

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                token_url,
                data={
                    "client_id": settings.azure_entra_client_id,
                    "client_secret": settings.azure_entra_client_secret,
                    "refresh_token": stored_refresh_token,
                    "grant_type": "refresh_token",
                    "scope": "openid profile email User.Read offline_access",
                },
            )

        if resp.status_code != 200:
            logger.warning(f"Refresh token exchange failed: {resp.status_code}")
            await session_repo.delete_by_user(user.external_id)
            await session.commit()
            raise AuthenticationError("Refresh failed — please log in again")

        new_tokens = resp.json()
        new_access_token = new_tokens.get("access_token", "")
        new_refresh_token = new_tokens.get("refresh_token", "")

        if new_refresh_token and new_refresh_token != stored_refresh_token:
            encrypted_token = token_encryptor.encrypt(new_refresh_token) if token_encryptor else new_refresh_token
            await session_repo.delete_by_user(user.external_id)
            await session_repo.add(
                user_id=user.external_id,
                refresh_token=encrypted_token,
                identity_provider="azure_entra",
                expires_at=datetime.now(timezone.utc) + timedelta(days=90),
            )

        await session.commit()

    response = JSONResponse(content={"status": "refreshed"})
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.app_environment != "development",
        samesite="lax",
        max_age=3600,
    )
    return response


@router.post("/auth/logout")
async def auth_logout(request: Request):
    db, _, settings, _, token_validator = _get_deps()

    token = request.cookies.get("access_token")

    if token:
        try:
            claims = token_validator.decode_unverified(token)
            oid = claims.get("oid") or claims.get("sub")
            if oid:
                provider_user_id = UUID(oid)
                async with db.get_session() as session:
                    user_repo = UserRepository(session)
                    session_repo = UserSessionRepository(session)
                    user = await user_repo.get_by_identity_provider(
                        provider="azure_entra",
                        provider_user_id=provider_user_id,
                    )
                    if user:
                        await session_repo.delete_by_user(user.external_id)
                        await session.commit()
        except Exception:
            logger.warning("Failed to clean up session during logout", exc_info=True)

    response = JSONResponse(content={"status": "logged_out"})
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.app_environment != "development",
        samesite="lax",
    )
    return response
