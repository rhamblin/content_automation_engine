"""Fetch all pins and their IDs from a Pinterest account using OAuth."""

import csv
import http.server
import json
import sys
import threading
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

PINTEREST_AUTH_URL = "https://www.pinterest.com/oauth/"
PINTEREST_API_URL = "https://api.pinterest.com/v5"
REDIRECT_URI = "http://localhost:8765/callback"
SCOPES = "boards:read,pins:read"


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
        pass  # Suppress server logs


def get_auth_code(client_id: str) -> str | None:
    """Open browser for Pinterest OAuth and wait for callback."""
    auth_url = (
        f"{PINTEREST_AUTH_URL}?"
        f"client_id={client_id}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"response_type=code&"
        f"scope={SCOPES}"
    )

    server = http.server.HTTPServer(("localhost", 8765), OAuthCallbackHandler)
    server.timeout = 120

    print("Opening browser for Pinterest authorization...")
    webbrowser.open(auth_url)

    # Wait for callback
    while OAuthCallbackHandler.auth_code is None:
        server.handle_request()

    server.server_close()
    return OAuthCallbackHandler.auth_code


def exchange_code_for_token(
    client_id: str, client_secret: str, code: str
) -> str | None:
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


def get_all_pins(access_token: str) -> list[dict]:
    """Fetch all pins from the authenticated Pinterest account."""
    pins = []
    headers = {"Authorization": f"Bearer {access_token}"}
    bookmark = None

    print("Fetching pins...")

    while True:
        params = {"page_size": 100}
        if bookmark:
            params["bookmark"] = bookmark

        response = requests.get(
            f"{PINTEREST_API_URL}/pins", headers=headers, params=params
        )

        if not response.ok:
            print(f"Failed to fetch pins: {response.status_code} - {response.text}")
            break

        data = response.json()
        items = data.get("items", [])
        pins.extend(items)

        print(f"  Fetched {len(items)} pins (total: {len(pins)})")

        bookmark = data.get("bookmark")
        if not bookmark:
            break

    return pins


def save_pins_to_csv(pins: list[dict]) -> Path:
    """Save pins to a timestamped CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = OUTPUT_DIR / f"{timestamp}.csv"

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pin_id", "title", "description", "link", "created_at"])

        for pin in pins:
            writer.writerow(
                [
                    pin.get("id", ""),
                    pin.get("title", ""),
                    pin.get("description", "")[:100] if pin.get("description") else "",
                    pin.get("link", ""),
                    pin.get("created_at", ""),
                ]
            )

    return output_file


def load_credentials() -> tuple[str, str]:
    """Load Pinterest API credentials."""
    creds_file = Path(__file__).parent / "pinterest-credentials.json"

    if not creds_file.exists():
        print(f"Error: Credentials file not found: {creds_file}")
        print("\nCreate pinterest-credentials.json with:")
        print('  {"client_id": "YOUR_APP_ID", "client_secret": "YOUR_APP_SECRET"}')
        print("\nGet these from: https://developers.pinterest.com/apps/")
        sys.exit(1)

    creds = json.loads(creds_file.read_text())
    return creds["client_id"], creds["client_secret"]


def main():
    client_id, client_secret = load_credentials()

    # Check for cached token
    token_file = Path(__file__).parent / ".access_token"
    access_token = None

    if token_file.exists():
        access_token = token_file.read_text().strip()
        # Verify token is still valid
        response = requests.get(
            f"{PINTEREST_API_URL}/user_account",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if not response.ok:
            print("Cached token expired, re-authenticating...")
            access_token = None

    if not access_token:
        auth_code = get_auth_code(client_id)
        if not auth_code:
            print("Failed to get authorization code")
            sys.exit(1)

        access_token = exchange_code_for_token(client_id, client_secret, auth_code)
        if not access_token:
            print("Failed to get access token")
            sys.exit(1)

        # Cache the token
        token_file.write_text(access_token)
        print("Token cached for future use")

    pins = get_all_pins(access_token)

    if not pins:
        print("No pins found")
        return

    output_file = save_pins_to_csv(pins)
    print(f"\nSaved {len(pins)} pins to {output_file}")


if __name__ == "__main__":
    main()
