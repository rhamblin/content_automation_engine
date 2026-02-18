import uuid
from typing import Optional

from fastapi import Request

from common.app_logger import AppLogger
from common.contracts.interfaces.database import IDatabase
from common.repositories.cross_tenant.user_repository import UserRepository
from .auth_context import AuthContext, TenantRole
from .exceptions import AuthenticationError
from .token_validator import AzureEntraTokenValidator

logger = AppLogger(__name__)


def _extract_token(request: Request) -> str:
    """Extract token from cookie or Authorization header."""
    token = request.cookies.get("access_token")
    if token:
        return token

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    raise AuthenticationError("No access token provided")


def _extract_correlation_id(request: Request) -> uuid.UUID:
    """Extract or generate a correlation ID from the request."""
    header_value = request.headers.get("X-Correlation-ID")
    if header_value:
        try:
            return uuid.UUID(header_value)
        except ValueError:
            pass
    return uuid.uuid4()


def create_require_auth(
    validator: AzureEntraTokenValidator,
    database: IDatabase,
):
    """Factory that returns a FastAPI dependency for authentication.

    Usage:
        require_auth = create_require_auth(validator, db_provider)

        @app.get("/protected")
        async def protected(auth: AuthContext = Depends(require_auth)):
            ...
    """

    async def require_auth(request: Request) -> AuthContext:
        token = _extract_token(request)
        claims = validator.validate(token)

        provider_user_id = uuid.UUID(claims["sub"])
        correlation_id = _extract_correlation_id(request)

        async with database.get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_identity_provider(
                provider="azure_entra",
                provider_user_id=provider_user_id,
            )

            if user is None:
                logger.warning(f"No user found for provider sub={provider_user_id}")
                raise AuthenticationError("User not found")

            tenant_user_rows = await user_repo.get_user_tenants(user.external_id)
            tenant_roles = [
                TenantRole(tenant_id=tu.tenant_id, role=tu.role)
                for tu in tenant_user_rows
            ]

        scopes = claims.get("scp", "").split() if claims.get("scp") else []

        return AuthContext(
            user_id=user.external_id,
            email=user.email,
            tenant_roles=tenant_roles,
            scopes=scopes,
            identity_provider="azure_entra",
            correlation_id=correlation_id,
        )

    return require_auth
