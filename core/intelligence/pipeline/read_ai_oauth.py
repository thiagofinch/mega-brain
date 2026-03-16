"""
Read.ai OAuth 2.1 Helper — handles authorization flow and token management.

Usage:
    # Step 1: Generate authorization URL (open in browser)
    python3 -m core.intelligence.pipeline.read_ai_oauth authorize

    # Step 2: After authorizing, paste the code:
    python3 -m core.intelligence.pipeline.read_ai_oauth exchange <code>

    # Step 3: Check token status
    python3 -m core.intelligence.pipeline.read_ai_oauth status

    # Step 4: Refresh expired token
    python3 -m core.intelligence.pipeline.read_ai_oauth refresh
"""

import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import UTC, datetime, timedelta

from core.intelligence.pipeline.read_ai_config import load_config

# Token storage (gitignored via .data/)
from core.paths import DATA

TOKENS_PATH = DATA / "read_ai_tokens.json"
PKCE_PATH = DATA / "read_ai_pkce.json"

CALLBACK_PORT = 19821


def _load_env() -> dict[str, str]:
    """Load OAuth env vars."""
    load_config()  # triggers .env loading
    return {
        "client_id": os.getenv("READ_AI_CLIENT_ID", ""),
        "client_secret": os.getenv("READ_AI_CLIENT_SECRET", ""),
        "auth_url": os.getenv("READ_AI_AUTH_URL", "https://authn.read.ai/oauth2/auth"),
        "token_url": os.getenv("READ_AI_TOKEN_URL", "https://authn.read.ai/oauth2/token"),
        "redirect_uri": f"http://localhost:{CALLBACK_PORT}/callback",
        "scope": "openid email offline_access profile meeting:read mcp:execute",
    }


def _generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _save_tokens(tokens: dict) -> None:
    """Save tokens to secure location.

    Computes ``expires_at`` (ISO-8601 UTC) from ``expires_in`` so that
    downstream code can check token validity without remembering when the
    save happened.
    """
    TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    # Format as naive-UTC + Z suffix for clean ISO-8601 (no +00:00Z duplication)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    tokens["saved_at"] = now_str

    # Compute absolute expiry timestamp when the server tells us lifetime
    expires_in = tokens.get("expires_in")
    if expires_in is not None:
        expires_at = now + timedelta(seconds=int(expires_in))
        tokens["expires_at"] = expires_at.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    with open(TOKENS_PATH, "w") as f:
        json.dump(tokens, f, indent=2)


def load_tokens() -> dict | None:
    """Load saved tokens. Returns None if no tokens exist."""
    if not TOKENS_PATH.exists():
        return None
    try:
        with open(TOKENS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _parse_iso_utc(value: str) -> datetime | None:
    """Parse an ISO-8601 timestamp that may end with ``Z`` or ``+00:00``.

    Returns a timezone-aware UTC datetime, or ``None`` on parse failure.
    """
    try:
        # Strip trailing Z (if present) and parse; ensure UTC
        cleaned = value.rstrip("Z")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        return None


def _is_token_expired(tokens: dict, buffer_seconds: int = 300) -> bool:
    """Return True if the token is expired or will expire within *buffer_seconds*.

    Uses the ``expires_at`` field written by ``_save_tokens``.  If the field
    is missing we fall back to ``saved_at`` + ``expires_in``.  When neither is
    available we conservatively assume the token is still valid (the server
    will reject it if not).
    """
    expires_at_str = tokens.get("expires_at")
    if expires_at_str:
        expires_at = _parse_iso_utc(expires_at_str)
        if expires_at is None:
            return False
    else:
        # Fallback: reconstruct from saved_at + expires_in
        saved_at_str = tokens.get("saved_at")
        expires_in = tokens.get("expires_in")
        if not saved_at_str or expires_in is None:
            return False
        saved_at = _parse_iso_utc(saved_at_str)
        if saved_at is None:
            return False
        expires_at = saved_at + timedelta(seconds=int(expires_in))

    now = datetime.now(UTC)
    return now >= expires_at - timedelta(seconds=buffer_seconds)


def _refresh_token(tokens: dict) -> dict | None:
    """Attempt to refresh the access token.

    Returns the new token dict on success, or ``None`` on failure.
    """
    env = _load_env()
    refresh_tok = tokens.get("refresh_token")
    if not refresh_tok:
        return None

    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_tok,
    }).encode()

    creds = f"{env['client_id']}:{env['client_secret']}"
    auth = base64.b64encode(creds.encode()).decode()

    req = urllib.request.Request(
        env["token_url"],
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            new_tokens = json.loads(resp.read().decode())

        # Preserve refresh_token if the server did not return a new one
        if not new_tokens.get("refresh_token") and refresh_tok:
            new_tokens["refresh_token"] = refresh_tok

        _save_tokens(new_tokens)
        return new_tokens

    except (urllib.error.HTTPError, urllib.error.URLError, OSError):
        return None


def get_access_token() -> str | None:
    """Get current access token, refreshing automatically if expired.

    Returns ``None`` when no tokens exist or when the refresh attempt fails.
    In the failure case a human-readable message is printed to stderr so
    operators can diagnose the issue.
    """
    tokens = load_tokens()
    if not tokens:
        return None

    if _is_token_expired(tokens):
        refreshed = _refresh_token(tokens)
        if refreshed is None:
            print(
                "ERROR: Read.ai access token is expired and auto-refresh failed. "
                "Run `python3 -m core.intelligence.pipeline.read_ai_oauth refresh` "
                "or `python3 -m core.intelligence.pipeline.read_ai_oauth authorize` "
                "to re-authenticate.",
                file=sys.stderr,
            )
            return None
        tokens = refreshed

    return tokens.get("access_token")


def cmd_authorize() -> None:
    """Open browser for authorization, capture code via localhost, exchange for tokens."""
    env = _load_env()
    if not env["client_id"]:
        print("ERROR: READ_AI_CLIENT_ID not set in .env")
        sys.exit(1)

    verifier, challenge = _generate_pkce()
    state = secrets.token_urlsafe(32)

    # Save PKCE verifier
    PKCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PKCE_PATH, "w") as f:
        json.dump({"code_verifier": verifier, "state": state}, f)

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": env["client_id"],
        "redirect_uri": env["redirect_uri"],
        "scope": env["scope"],
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })

    auth_url = f"{env['auth_url']}?{params}"

    # Capture authorization code via local HTTP server
    captured_code: dict[str, str] = {}

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            code = params.get("code", [None])[0]
            error = params.get("error", [None])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            if code:
                captured_code["code"] = code
                self.wfile.write(b"<html><body><h2>Authorization successful!</h2>"
                                 b"<p>You can close this tab. Mega Brain is processing...</p>"
                                 b"</body></html>")
            elif error:
                captured_code["error"] = error
                self.wfile.write(f"<html><body><h2>Error: {error}</h2></body></html>".encode())
            else:
                self.wfile.write(b"<html><body><h2>No code received</h2></body></html>")

        def log_message(self, format, *args):
            pass  # Suppress HTTP server logs

    print()
    print("=" * 60)
    print("READ.AI AUTHORIZATION")
    print("=" * 60)
    print()
    print("Opening browser for authorization...")
    print(f"(Waiting for callback on localhost:{CALLBACK_PORT})")
    print()

    server = http.server.HTTPServer(("127.0.0.1", CALLBACK_PORT), CallbackHandler)
    server.timeout = 120  # 2 minutes max wait

    # Open browser
    webbrowser.open(auth_url)

    # Wait for single callback request
    while not captured_code:
        server.handle_request()

    server.server_close()

    if "error" in captured_code:
        print(f"Authorization failed: {captured_code['error']}")
        sys.exit(1)

    if "code" not in captured_code:
        print("No authorization code received.")
        sys.exit(1)

    print("Code captured! Exchanging for tokens...")
    print()

    # Auto-exchange
    cmd_exchange(captured_code["code"])


def cmd_exchange(code: str) -> None:
    """Exchange authorization code for tokens."""
    env = _load_env()

    # Load PKCE verifier
    if not PKCE_PATH.exists():
        print("ERROR: No PKCE state found. Run 'authorize' first.")
        sys.exit(1)

    with open(PKCE_PATH) as f:
        pkce = json.load(f)

    verifier = pkce["code_verifier"]

    # Build request
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": env["redirect_uri"],
        "code_verifier": verifier,
    }).encode()

    # Basic auth header (client_id:client_secret)
    creds = f"{env['client_id']}:{env['client_secret']}"
    auth = base64.b64encode(creds.encode()).decode()

    req = urllib.request.Request(
        env["token_url"],
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            tokens = json.loads(resp.read().decode())

        _save_tokens(tokens)

        # Clean up PKCE
        PKCE_PATH.unlink(missing_ok=True)

        print()
        print("=" * 60)
        print("SUCCESS — Tokens saved!")
        print("=" * 60)
        print(f"  Access token:  {tokens.get('access_token', '')[:20]}...")
        print(f"  Refresh token: {'YES' if tokens.get('refresh_token') else 'NO'}")
        print(f"  Expires in:    {tokens.get('expires_in', 'unknown')} seconds")
        print(f"  Scope:         {tokens.get('scope', 'unknown')}")
        print(f"  Saved to:      {TOKENS_PATH}")
        print()
        print("You can now use:")
        print("  /ingest https://app.read.ai/analytics/meetings/<ID>")
        print()

    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"ERROR: Token exchange failed ({e.code})")
        print(f"  Response: {body}")
        sys.exit(1)


def cmd_refresh() -> None:
    """Refresh expired access token (CLI entry point)."""
    tokens = load_tokens()

    if not tokens or not tokens.get("refresh_token"):
        print("ERROR: No refresh token available. Run 'authorize' first.")
        sys.exit(1)

    refreshed = _refresh_token(tokens)
    if refreshed is None:
        print("ERROR: Refresh failed. Run 'authorize' to re-authenticate.")
        sys.exit(1)

    print("Token refreshed successfully.")
    print(f"  Expires in: {refreshed.get('expires_in', 'unknown')} seconds")


def cmd_status() -> None:
    """Show current token status."""
    tokens = load_tokens()
    if not tokens:
        print("No tokens found. Run 'authorize' to set up Read.ai access.")
        return

    print("Read.ai Token Status:")
    print(f"  Access token:  {tokens.get('access_token', '')[:20]}...")
    print(f"  Refresh token: {'YES' if tokens.get('refresh_token') else 'NO'}")
    print(f"  Saved at:      {tokens.get('saved_at', 'unknown')}")
    print(f"  Scope:         {tokens.get('scope', 'unknown')}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "authorize":
        cmd_authorize()
    elif cmd == "exchange":
        if len(sys.argv) < 3:
            print("Usage: ... exchange <authorization_code>")
            sys.exit(1)
        cmd_exchange(sys.argv[2])
    elif cmd == "refresh":
        cmd_refresh()
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
