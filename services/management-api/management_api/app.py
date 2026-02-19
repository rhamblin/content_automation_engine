from common.app_logger import AppLogger
from common.auth import (
    AuthenticationError,
    AuthorizationError,
    AzureEntraTokenValidator,
    TokenEncryptor,
    create_require_auth,
)
from common.providers.database.sqlalchemy import SQLAlchemyDatabaseProvider
from common.settings import load_settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from management_api.routers import auth, health, niches, pinterest

logger = AppLogger(__name__)
settings = load_settings()

# --- Infrastructure wiring ---

db = SQLAlchemyDatabaseProvider(settings.database_url)
token_validator = AzureEntraTokenValidator(
    tenant_id=settings.azure_entra_tenant_id,
    client_id=settings.azure_entra_client_id,
)
require_auth = create_require_auth(token_validator, db)
token_encryptor = TokenEncryptor(settings.refresh_token_encryption_key) if settings.refresh_token_encryption_key else None

# --- App ---

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Exception handlers ---

@app.exception_handler(AuthenticationError)
async def authentication_error_handler(_request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"error": exc.detail})


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(_request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"error": exc.detail})


# --- Lifecycle ---

@app.on_event("shutdown")
async def shutdown():
    await db.close_connection()


# --- Routers ---

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(niches.router)
app.include_router(pinterest.router)
