"""
Tests for core.intelligence.pipeline.read_ai_oauth
===================================================
All tests are OFFLINE -- no real API calls, no real filesystem outside tmp_path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_token_file(path: Path, tokens: dict) -> None:
    """Write a token dict to the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(tokens, f)


def _utc_iso(dt: datetime) -> str:
    """Format a UTC datetime as ISO-8601 with Z suffix (no +00:00)."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _make_tokens(
    *,
    access_token: str = "test-access-token-abc123",
    refresh_token: str = "test-refresh-token-xyz789",
    expires_in: int = 3600,
    expires_at: str | None = None,
    saved_at: str | None = None,
) -> dict:
    """Build a realistic token dict."""
    now = datetime.now(UTC)
    tok = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "scope": "openid email offline_access profile meeting:read mcp:execute",
    }
    if saved_at is not None:
        tok["saved_at"] = saved_at
    else:
        tok["saved_at"] = _utc_iso(now)
    if expires_at is not None:
        tok["expires_at"] = expires_at
    else:
        tok["expires_at"] = _utc_iso(now + timedelta(seconds=expires_in))
    return tok


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_oauth(tmp_path, monkeypatch):
    """Redirect TOKENS_PATH and PKCE_PATH to tmp, stub _load_env."""
    tokens_path = tmp_path / "read_ai_tokens.json"
    pkce_path = tmp_path / "read_ai_pkce.json"

    import core.intelligence.pipeline.read_ai_oauth as oauth_mod

    monkeypatch.setattr(oauth_mod, "TOKENS_PATH", tokens_path)
    monkeypatch.setattr(oauth_mod, "PKCE_PATH", pkce_path)

    # Stub _load_env so tests never touch real environment
    monkeypatch.setattr(oauth_mod, "_load_env", lambda: {
        "client_id": "fake-client-id",
        "client_secret": "fake-client-secret",
        "auth_url": "https://authn.read.ai/oauth2/auth",
        "token_url": "https://authn.read.ai/oauth2/token",
        "redirect_uri": "http://localhost:19821/callback",
        "scope": "openid email offline_access profile meeting:read mcp:execute",
    })


@pytest.fixture()
def oauth_mod():
    """Return the oauth module (already patched by _isolate_oauth)."""
    import core.intelligence.pipeline.read_ai_oauth as mod
    return mod


# ---------------------------------------------------------------------------
# _save_tokens: expires_at computation
# ---------------------------------------------------------------------------

class TestSaveTokens:
    """Verify that _save_tokens computes expires_at from expires_in."""

    def test_saves_expires_at_when_expires_in_present(self, oauth_mod, tmp_path):
        tokens = {"access_token": "tok", "expires_in": 7200}
        oauth_mod._save_tokens(tokens)
        saved = json.loads(oauth_mod.TOKENS_PATH.read_text())
        assert "expires_at" in saved
        assert "saved_at" in saved

    def test_skips_expires_at_when_expires_in_absent(self, oauth_mod, tmp_path):
        tokens = {"access_token": "tok"}
        oauth_mod._save_tokens(tokens)
        saved = json.loads(oauth_mod.TOKENS_PATH.read_text())
        assert "expires_at" not in saved
        assert "saved_at" in saved

    def test_expires_at_is_in_future(self, oauth_mod, tmp_path):
        tokens = {"access_token": "tok", "expires_in": 3600}
        oauth_mod._save_tokens(tokens)
        saved = json.loads(oauth_mod.TOKENS_PATH.read_text())
        expires_at = datetime.fromisoformat(saved["expires_at"].replace("Z", "+00:00"))
        now = datetime.now(UTC)
        # expires_at should be roughly 1 hour from now (within 5s tolerance)
        assert expires_at > now + timedelta(seconds=3590)


# ---------------------------------------------------------------------------
# _is_token_expired
# ---------------------------------------------------------------------------

class TestIsTokenExpired:
    """Verify expiry detection with the 5-minute buffer."""

    def test_not_expired_when_plenty_of_time(self, oauth_mod):
        future = _utc_iso(datetime.now(UTC) + timedelta(hours=1))
        tokens = _make_tokens(expires_at=future)
        assert oauth_mod._is_token_expired(tokens) is False

    def test_expired_when_past(self, oauth_mod):
        past = _utc_iso(datetime.now(UTC) - timedelta(hours=1))
        tokens = _make_tokens(expires_at=past)
        assert oauth_mod._is_token_expired(tokens) is True

    def test_expired_within_buffer(self, oauth_mod):
        # Token expires in 4 minutes (< 5 min buffer) => should be considered expired
        soon = _utc_iso(datetime.now(UTC) + timedelta(minutes=4))
        tokens = _make_tokens(expires_at=soon)
        assert oauth_mod._is_token_expired(tokens) is True

    def test_not_expired_just_outside_buffer(self, oauth_mod):
        # Token expires in 6 minutes (> 5 min buffer) => still valid
        later = _utc_iso(datetime.now(UTC) + timedelta(minutes=6))
        tokens = _make_tokens(expires_at=later)
        assert oauth_mod._is_token_expired(tokens) is False

    def test_fallback_to_saved_at_plus_expires_in(self, oauth_mod):
        # No expires_at field, but saved_at + expires_in indicate it expired
        saved_at = _utc_iso(datetime.now(UTC) - timedelta(hours=2))
        tokens = {"access_token": "tok", "saved_at": saved_at, "expires_in": 3600}
        assert oauth_mod._is_token_expired(tokens) is True

    def test_no_expiry_fields_returns_false(self, oauth_mod):
        # Conservative: no expiry info => assume valid
        tokens = {"access_token": "tok"}
        assert oauth_mod._is_token_expired(tokens) is False

    def test_custom_buffer(self, oauth_mod):
        # Token expires in 30 seconds, buffer is 60 => expired
        soon = _utc_iso(datetime.now(UTC) + timedelta(seconds=30))
        tokens = _make_tokens(expires_at=soon)
        assert oauth_mod._is_token_expired(tokens, buffer_seconds=60) is True


# ---------------------------------------------------------------------------
# get_access_token: the main public API
# ---------------------------------------------------------------------------

class TestGetAccessToken:
    """Verify auto-refresh behavior in get_access_token."""

    def test_returns_token_when_not_expired(self, oauth_mod, tmp_path):
        tokens = _make_tokens()
        _write_token_file(oauth_mod.TOKENS_PATH, tokens)
        result = oauth_mod.get_access_token()
        assert result == tokens["access_token"]

    def test_returns_none_when_no_tokens(self, oauth_mod):
        result = oauth_mod.get_access_token()
        assert result is None

    def test_auto_refreshes_when_expired(self, oauth_mod, tmp_path):
        # Write expired tokens
        expired = _make_tokens(
            expires_at=_utc_iso(datetime.now(UTC) - timedelta(hours=1)),
        )
        _write_token_file(oauth_mod.TOKENS_PATH, expired)

        # Mock _refresh_token to return new tokens
        new_tokens = _make_tokens(access_token="new-fresh-token")
        with patch.object(oauth_mod, "_refresh_token", return_value=new_tokens):
            result = oauth_mod.get_access_token()

        assert result == "new-fresh-token"

    def test_returns_none_and_prints_error_when_refresh_fails(self, oauth_mod, tmp_path, capsys):
        # Write expired tokens
        expired = _make_tokens(
            expires_at=_utc_iso(datetime.now(UTC) - timedelta(hours=1)),
        )
        _write_token_file(oauth_mod.TOKENS_PATH, expired)

        # Mock _refresh_token to fail
        with patch.object(oauth_mod, "_refresh_token", return_value=None):
            result = oauth_mod.get_access_token()

        assert result is None
        captured = capsys.readouterr()
        assert "expired and auto-refresh failed" in captured.err

    def test_does_not_refresh_when_token_valid(self, oauth_mod, tmp_path):
        tokens = _make_tokens()
        _write_token_file(oauth_mod.TOKENS_PATH, tokens)

        with patch.object(oauth_mod, "_refresh_token") as mock_refresh:
            result = oauth_mod.get_access_token()

        mock_refresh.assert_not_called()
        assert result == tokens["access_token"]


# ---------------------------------------------------------------------------
# _refresh_token
# ---------------------------------------------------------------------------

class TestRefreshToken:
    """Verify the internal refresh helper."""

    def test_returns_none_when_no_refresh_token(self, oauth_mod):
        tokens = {"access_token": "tok"}
        result = oauth_mod._refresh_token(tokens)
        assert result is None

    def test_preserves_refresh_token_if_server_omits(self, oauth_mod, tmp_path):
        tokens = _make_tokens()
        server_response = json.dumps({
            "access_token": "brand-new-access",
            "expires_in": 7200,
        }).encode()

        # Mock the HTTP call
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = mock_urlopen.return_value.__enter__.return_value
            mock_resp.read.return_value = server_response
            result = oauth_mod._refresh_token(tokens)

        assert result is not None
        assert result["access_token"] == "brand-new-access"
        # Original refresh token should be preserved
        assert result["refresh_token"] == tokens["refresh_token"]
