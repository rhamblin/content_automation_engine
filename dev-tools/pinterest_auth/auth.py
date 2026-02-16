"""Shared Pinterest OAuth — reads credentials from tenant config, caches token centrally."""

import http.server
import json
import ssl
import subprocess
import urllib.parse
import webbrowser
from pathlib import Path

import requests

PINTEREST_AUTH_URL = "https://www.pinterest.com/oauth/"
PINTEREST_API_URL = "https://api.pinterest.com/v5"
REDIRECT_URI = "https://localhost:8765/callback"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read,ads:read,ads:write"

MODULE_DIR = Path(__file__).parent
CERTS_DIR = MODULE_DIR / "certs"
TOKEN_FILE = MODULE_DIR / ".access_token"
CONFIG_ROOT = MODULE_DIR.parent.parent / "config" / "tenants"


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle the OAuth callback from Pinterest."""

    auth_code: str | None = None

    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h1>Authorization successful!</h1><p>You can close this window.</p>"
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error = params.get("error", ["Unknown error"])[0]
            self.wfile.write(f"<h1>Authorization failed</h1><p>{error}</p>".encode())

    def log_message(self, format, *args):
        pass


def _load_credentials(tenant: str) -> tuple[str, str]:
    """Load Pinterest client_id and client_secret from tenant credentials."""
    creds_path = CONFIG_ROOT / tenant / "credentials" / "pinterest.json"
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {creds_path}\n\n"
            "Create pinterest.json with:\n"
            '  {"app_id": "YOUR_APP_ID", "app_secret": "YOUR_APP_SECRET"}\n\n'
            "Get these from: https://developers.pinterest.com/apps/"
        )

    creds = json.loads(creds_path.read_text())
    client_id = creds.get("app_id") or creds.get("client_id", "")
    client_secret = creds.get("app_secret") or creds.get("client_secret", "")

    if not client_id or not client_secret or client_id == "REPLACE_ME":
        raise ValueError(f"Pinterest app_id/app_secret not configured in {creds_path}")

    return client_id, client_secret


def _ensure_ssl_certs() -> tuple[Path, Path]:
    """Generate self-signed SSL certificates if they don't exist."""
    CERTS_DIR.mkdir(exist_ok=True)
    cert_file = CERTS_DIR / "localhost.pem"
    key_file = CERTS_DIR / "localhost-key.pem"

    if cert_file.exists() and key_file.exists():
        return cert_file, key_file

    print("Generating self-signed SSL certificate...")
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:4096",
            "-keyout", str(key_file),
            "-out", str(cert_file),
            "-days", "365",
            "-nodes",
            "-subj", "/CN=localhost",
        ],
        check=True,
        capture_output=True,
    )
    print("SSL certificate generated.")
    return cert_file, key_file


def _get_auth_code(client_id: str) -> str:
    """Open browser for Pinterest OAuth and wait for callback."""
    auth_url = (
        f"{PINTEREST_AUTH_URL}?"
        f"client_id={client_id}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"response_type=code&"
        f"scope={SCOPES}"
    )

    cert_file, key_file = _ensure_ssl_certs()

    OAuthCallbackHandler.auth_code = None
    server = http.server.HTTPServer(("localhost", 8765), OAuthCallbackHandler)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_file, key_file)
    server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
    server.timeout = 120

    print("Opening browser for Pinterest authorization...")
    print("Note: You may need to accept the self-signed certificate in your browser.")
    webbrowser.open(auth_url)

    while OAuthCallbackHandler.auth_code is None:
        server.handle_request()

    server.server_close()

    if not OAuthCallbackHandler.auth_code:
        raise RuntimeError("Failed to get authorization code")

    return OAuthCallbackHandler.auth_code


def _exchange_code_for_token(client_id: str, client_secret: str, code: str) -> str:
    """Exchange authorization code for access token."""
    response = requests.post(
        f"{PINTEREST_API_URL}/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        auth=(client_id, client_secret),
    )

    if not response.ok:
        raise RuntimeError(f"Token exchange failed: {response.status_code} - {response.text}")

    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("No access_token in response")

    return token


def is_token_valid(token: str) -> bool:
    """Check if access token is still valid."""
    response = requests.get(
        f"{PINTEREST_API_URL}/user_account",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.ok


def get_access_token(tenant: str = "dev-tenant") -> str:
    """Get valid access token, running OAuth flow if needed.

    1. Check cached token file
    2. If expired/missing, run browser OAuth flow
    3. Cache token for reuse across tools
    """
    # Check cached token
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
        if token and is_token_valid(token):
            print("Using cached Pinterest token.")
            return token
        print("Cached token expired, re-authenticating...")

    # OAuth flow
    client_id, client_secret = _load_credentials(tenant)
    auth_code = _get_auth_code(client_id)
    token = _exchange_code_for_token(client_id, client_secret, auth_code)

    TOKEN_FILE.write_text(token)
    print("Token cached for future use.")
    return token
