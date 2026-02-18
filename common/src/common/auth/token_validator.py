import time
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from common.app_logger import AppLogger
from .exceptions import AuthenticationError


class AzureEntraTokenValidator:
    """Validates Azure Entra ID JWTs using the JWKS endpoint.

    Caches the JWKS keys via PyJWKClient's built-in cache.
    """

    def __init__(self, tenant_id: str, client_id: str):
        self._logger = AppLogger(__name__)
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        self._jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)

    def validate(self, token: str) -> dict[str, Any]:
        """Validate a JWT and return decoded claims.

        Raises:
            AuthenticationError: If token is invalid, expired, or has wrong audience/issuer.
        """
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
            return claims
        except jwt.ExpiredSignatureError:
            self._logger.warning("Token expired")
            raise AuthenticationError("Token has expired")
        except jwt.InvalidAudienceError:
            self._logger.warning("Invalid audience in token")
            raise AuthenticationError("Invalid token audience")
        except jwt.InvalidIssuerError:
            self._logger.warning("Invalid issuer in token")
            raise AuthenticationError("Invalid token issuer")
        except jwt.PyJWTError as e:
            self._logger.warning(f"JWT validation failed: {e}")
            raise AuthenticationError("Invalid token")

    def decode_unverified(self, token: str) -> dict[str, Any]:
        """Decode a token without verifying signature (for refresh flow with expired tokens).

        Raises:
            AuthenticationError: If the token cannot be decoded.
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False},
                algorithms=["RS256"],
            )
        except jwt.PyJWTError as e:
            self._logger.warning(f"Failed to decode token: {e}")
            raise AuthenticationError("Cannot decode token")
