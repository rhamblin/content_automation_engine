from urllib.parse import urlencode

import httpx
from common.settings import load_settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

settings = load_settings()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/entra/callback")
async def entra_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        error = request.query_params.get("error_description", "No auth code received")
        params = urlencode({"error": error})
        return RedirectResponse(f"{settings.frontend_url}/auth/complete?{params}")

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
                "scope": "openid profile email User.Read",
            },
        )

    if response.status_code != 200:
        params = urlencode({"error": response.text})
        return RedirectResponse(f"{settings.frontend_url}/auth/complete?{params}")

    token_data = response.json()
    params = urlencode({
        "access_token": token_data.get("access_token", ""),
        "id_token": token_data.get("id_token", ""),
    })
    return RedirectResponse(f"{settings.frontend_url}/auth/complete?{params}")
