"""
credential_manager.py -- Credential Lifecycle Manager for MCE Pipeline
======================================================================

Manages credential loading, validation, hot-reload, and injection for
LLM providers. Supports three credential types:

- API key (static): simple string, never expires.
- OAuth token (refresh): access_token + refresh_token + expires_at.
- Environment variable: reads from os.environ at load time.

Hot-reload: watches config file mtime and reloads when changed,
without requiring a pipeline restart.

Integration: LLMProvider calls ``get_credential(provider)`` before
API calls to get the current valid credential.

Usage::

    from engine.intelligence.pipeline.mce.credential_manager import (
        CredentialManager, CredentialType,
    )

    manager = CredentialManager(config_path="path/to/credentials.yaml")
    manager.load("openai")
    cred = manager.get_credential("openai")
    print(cred.api_key)  # or cred.token for OAuth

Constraints:
    - stdlib + PyYAML only (no external OAuth libraries).
    - Thread-safe for reads (credentials are replaced atomically).
    - Never raises on hot-reload failure -- logs and keeps old credential.

Version: 1.0.0
Date: 2026-04-01
Story: MCE21-3.3
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import yaml

logger = logging.getLogger("mce.credential_manager")


# ---------------------------------------------------------------------------
# Credential Types
# ---------------------------------------------------------------------------


class CredentialType(str, Enum):
    """Classification of credential storage and lifecycle.

    - API_KEY: Static key string. No expiration.
    - OAUTH: Access token + refresh token. Has expiration.
    - ENV_VAR: Read from environment variable at load time.
    """

    API_KEY = "api_key"
    OAUTH = "oauth"
    ENV_VAR = "env_var"


# ---------------------------------------------------------------------------
# Credential dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Credential:
    """Immutable credential record.

    Attributes:
        provider: Provider name (e.g., "openai", "gemini").
        credential_type: One of CredentialType values.
        api_key: Static API key (for API_KEY and ENV_VAR types).
        token: OAuth access token (for OAUTH type).
        refresh_token: OAuth refresh token (for OAUTH type).
        expires_at: Unix timestamp when token expires (0 = never).
        extra: Additional provider-specific metadata.
    """

    provider: str
    credential_type: CredentialType
    api_key: str = ""
    token: str = ""
    refresh_token: str = ""
    expires_at: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Return True if this credential has expired.

        API keys and env vars never expire (expires_at == 0).
        OAuth tokens expire when current time exceeds expires_at.
        """
        if self.expires_at == 0.0:
            return False
        return time.time() > self.expires_at

    @property
    def effective_key(self) -> str:
        """Return the usable credential string regardless of type.

        - API_KEY/ENV_VAR: returns api_key
        - OAUTH: returns token
        """
        if self.credential_type == CredentialType.OAUTH:
            return self.token
        return self.api_key

    def __repr__(self) -> str:
        masked_key = self.effective_key[:4] + "****" if self.effective_key else "<empty>"
        return (
            f"Credential(provider={self.provider!r}, "
            f"type={self.credential_type.value}, "
            f"key={masked_key}, "
            f"expired={self.is_expired})"
        )


# ---------------------------------------------------------------------------
# YAML config loader
# ---------------------------------------------------------------------------


def _load_credentials_yaml(path: Path) -> dict[str, Any]:
    """Load credentials config YAML. Returns empty dict on failure."""
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning("Failed to load credentials config %s: %s", path, exc)
        return {}


def _parse_credential(provider: str, entry: dict[str, Any]) -> Credential | None:
    """Parse a single provider entry from credentials config into a Credential.

    Expected YAML structure per provider::

        openai:
          type: api_key
          api_key: "sk-..."

        anthropic:
          type: env_var
          env_var: "ANTHROPIC_API_KEY"

        google:
          type: oauth
          token: "ya29...."
          refresh_token: "1//0e..."
          expires_at: 1712000000

    Returns None if the entry is invalid.
    """
    if not isinstance(entry, dict):
        logger.warning("Invalid credential entry for %s: not a dict", provider)
        return None

    raw_type = entry.get("type", "api_key")
    try:
        cred_type = CredentialType(raw_type)
    except ValueError:
        logger.warning(
            "Unknown credential type %r for provider %s, defaulting to api_key",
            raw_type,
            provider,
        )
        cred_type = CredentialType.API_KEY

    if cred_type == CredentialType.API_KEY:
        api_key = str(entry.get("api_key", ""))
        return Credential(
            provider=provider,
            credential_type=cred_type,
            api_key=api_key,
            extra=entry.get("extra", {}),
        )

    if cred_type == CredentialType.ENV_VAR:
        env_var_name = str(entry.get("env_var", ""))
        resolved = os.environ.get(env_var_name, "")
        if not resolved:
            logger.warning(
                "Environment variable %s not found for provider %s",
                env_var_name,
                provider,
            )
        return Credential(
            provider=provider,
            credential_type=cred_type,
            api_key=resolved,
            extra={"env_var_name": env_var_name, **entry.get("extra", {})},
        )

    if cred_type == CredentialType.OAUTH:
        return Credential(
            provider=provider,
            credential_type=cred_type,
            token=str(entry.get("token", "")),
            refresh_token=str(entry.get("refresh_token", "")),
            expires_at=float(entry.get("expires_at", 0.0)),
            extra=entry.get("extra", {}),
        )

    return None


# ---------------------------------------------------------------------------
# CredentialManager
# ---------------------------------------------------------------------------


class CredentialManager:
    """Manages credential lifecycle for MCE pipeline LLM providers.

    Responsibilities:
    - load(provider): parse credential from config
    - validate(): check all loaded credentials are valid
    - refresh_if_expired(): refresh OAuth tokens when expired
    - get_credential(provider): return current valid credential
    - Hot-reload: watch config file mtime, reload on change

    Parameters:
        config_path: Path to credentials YAML file.
        refresh_callback: Optional async refresh function for OAuth.
                         Signature: (provider, refresh_token) -> dict with
                         {token, expires_at}.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        refresh_callback: Callable[[str, str], dict[str, Any]] | None = None,
    ) -> None:
        self._config_path: Path | None = Path(config_path) if config_path else None
        self._credentials: dict[str, Credential] = {}
        self._config_mtime: float = 0.0
        self._raw_config: dict[str, Any] = {}
        self._refresh_callback = refresh_callback

        # Initial load if config path provided
        if self._config_path:
            self._load_config()

    # -- Config loading & hot-reload ----------------------------------------

    def _load_config(self) -> None:
        """Load the credentials config from disk and parse all providers."""
        if self._config_path is None:
            return

        self._raw_config = _load_credentials_yaml(self._config_path)

        try:
            self._config_mtime = self._config_path.stat().st_mtime
        except OSError:
            self._config_mtime = 0.0

        providers = self._raw_config.get("providers", self._raw_config)
        if isinstance(providers, dict):
            for provider_name, entry in providers.items():
                if provider_name.startswith("_"):
                    continue
                cred = _parse_credential(provider_name, entry)
                if cred is not None:
                    self._credentials[provider_name] = cred
                    logger.debug("Loaded credential for %s", provider_name)

    def _check_hot_reload(self) -> None:
        """Check if config file has changed and reload if so."""
        if self._config_path is None:
            return
        if not self._config_path.is_file():
            return

        try:
            current_mtime = self._config_path.stat().st_mtime
        except OSError:
            return

        if current_mtime > self._config_mtime:
            logger.info(
                "Credential config changed (mtime %s > %s), reloading",
                current_mtime,
                self._config_mtime,
            )
            old_credentials = dict(self._credentials)
            try:
                self._load_config()
                logger.info(
                    "Hot-reload complete: %d credentials loaded",
                    len(self._credentials),
                )
            except Exception as exc:
                logger.error("Hot-reload failed, keeping old credentials: %s", exc)
                self._credentials = old_credentials

    # -- Public API ---------------------------------------------------------

    def load(self, provider: str) -> Credential | None:
        """Load (or reload) a single provider credential from config.

        Checks for hot-reload first, then returns the credential
        for the given provider.

        Args:
            provider: Provider name (e.g., "openai", "gemini").

        Returns:
            Credential object, or None if provider not found in config.
        """
        self._check_hot_reload()

        if provider in self._credentials:
            return self._credentials[provider]

        # Try to parse from raw config
        providers = self._raw_config.get("providers", self._raw_config)
        if isinstance(providers, dict) and provider in providers:
            cred = _parse_credential(provider, providers[provider])
            if cred is not None:
                self._credentials[provider] = cred
                return cred

        logger.warning("Provider %s not found in credential config", provider)
        return None

    def validate(self) -> dict[str, bool]:
        """Validate all loaded credentials.

        Returns:
            Dict mapping provider name to validity (True = valid,
            False = expired or empty).
        """
        results: dict[str, bool] = {}
        for name, cred in self._credentials.items():
            if not cred.effective_key or cred.is_expired:
                results[name] = False
            else:
                results[name] = True
        return results

    def refresh_if_expired(self, provider: str | None = None) -> bool:
        """Refresh expired OAuth tokens.

        If provider is None, refreshes all expired OAuth credentials.
        Uses the refresh_callback provided at construction.

        Args:
            provider: Optional specific provider to refresh.

        Returns:
            True if at least one credential was refreshed.
        """
        if self._refresh_callback is None:
            logger.debug("No refresh callback configured")
            return False

        refreshed = False
        targets = (
            {provider: self._credentials[provider]}
            if provider and provider in self._credentials
            else dict(self._credentials)
        )

        for name, cred in targets.items():
            if cred.credential_type != CredentialType.OAUTH:
                continue
            if not cred.is_expired:
                continue
            if not cred.refresh_token:
                logger.warning("Cannot refresh %s: no refresh_token available", name)
                continue

            try:
                new_data = self._refresh_callback(name, cred.refresh_token)
                new_cred = Credential(
                    provider=name,
                    credential_type=CredentialType.OAUTH,
                    token=str(new_data.get("token", "")),
                    refresh_token=cred.refresh_token,
                    expires_at=float(new_data.get("expires_at", 0.0)),
                    extra=cred.extra,
                )
                self._credentials[name] = new_cred
                refreshed = True
                logger.info("Refreshed OAuth token for %s", name)
            except Exception as exc:
                logger.error("Failed to refresh credential for %s: %s", name, exc)

        return refreshed

    def get_credential(self, provider: str) -> Credential | None:
        """Get the current credential for a provider.

        Performs hot-reload check and auto-refresh before returning.

        Args:
            provider: Provider name (e.g., "openai").

        Returns:
            Credential object, or None if not found.
        """
        self._check_hot_reload()

        cred = self._credentials.get(provider)
        if cred is None:
            return None

        # Auto-refresh expired OAuth tokens
        if cred.is_expired and cred.credential_type == CredentialType.OAUTH:
            self.refresh_if_expired(provider)
            cred = self._credentials.get(provider)

        return cred

    def load_from_dict(self, provider: str, entry: dict[str, Any]) -> Credential | None:
        """Load a credential from an explicit dict (no file needed).

        Useful for programmatic credential injection.

        Args:
            provider: Provider name.
            entry: Dict with type, api_key/token/env_var fields.

        Returns:
            Credential object, or None on parse failure.
        """
        cred = _parse_credential(provider, entry)
        if cred is not None:
            self._credentials[provider] = cred
        return cred

    @property
    def providers(self) -> list[str]:
        """Return list of loaded provider names."""
        return sorted(self._credentials.keys())

    @property
    def count(self) -> int:
        """Return number of loaded credentials."""
        return len(self._credentials)

    def __repr__(self) -> str:
        return (
            f"CredentialManager(providers={self.providers}, "
            f"config={'set' if self._config_path else 'none'})"
        )
