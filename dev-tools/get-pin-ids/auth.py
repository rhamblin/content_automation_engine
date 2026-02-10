"""Shared Pinterest OAuth authentication."""

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
SCOPES = "boards:read,pins:read,user_accounts:read,ads:read,ads:write"

CERTS_DIR = Path(__file__).parent / "certs"
TOKEN_FILE = Path(__file__).parent / ".access_token"
CREDS_FILE = Path(__file__).parent / "pinterest-credentials.json"


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


def load_credentials() -> tuple[str, str]:
    """Load Pinterest API credentials."""
    if not CREDS_FILE.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {CREDS_FILE}\n\n"
            "Create pinterest-credentials.json with:\n"
            '  {"client_id": "YOUR_APP_ID", "client_secret": "YOUR_APP_SECRET"}\n\n'
            "Get these from: https://developers.pinterest.com/apps/"
        )

    creds = json.loads(CREDS_FILE.read_text())
    return creds["client_id"], creds["client_secret"]


def ensure_ssl_certs() -> tuple[Path, Path]:
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


def get_auth_code(client_id: str) -> str | None:
    """Open browser for Pinterest OAuth and wait for callback."""
    auth_url = (
        f"{PINTEREST_AUTH_URL}?"
        f"client_id={client_id}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"response_type=code&"
        f"scope={SCOPES}"
    )

    cert_file, key_file = ensure_ssl_certs()

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
    return OAuthCallbackHandler.auth_code


def exchange_code_for_token(client_id: str, client_secret: str, code: str) -> str | None:
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
        print(f"Token exchange failed: {response.status_code} - {response.text}")
        return None

    return response.json().get("access_token")


def is_token_valid(token: str) -> bool:
    """Check if access token is still valid."""
    response = requests.get(
        f"{PINTEREST_API_URL}/user_account",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.ok


def get_access_token() -> str:
    """Get valid access token, refreshing via OAuth if needed."""
    # Check cached token
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
        if is_token_valid(token):
            return token
        print("Cached token expired, re-authenticating...")

    # Do OAuth flow
    client_id, client_secret = load_credentials()

    auth_code = get_auth_code(client_id)
    if not auth_code:
        raise RuntimeError("Failed to get authorization code")

    token = exchange_code_for_token(client_id, client_secret, auth_code)
    if not token:
        raise RuntimeError("Failed to get access token")

    TOKEN_FILE.write_text(token)
    print("Token cached for future use")
    return token
