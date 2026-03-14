"""
Fireflies.ai Integration Configuration.

Loads settings from environment variables (.env file).
All paths come from core.paths -- no hardcoding.

Usage:
    from core.intelligence.pipeline.fireflies_config import load_config
    cfg = load_config()
    print(cfg.api_key, cfg.graphql_url)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from core.paths import LOGS, MISSION_CONTROL, ROUTING

# ============================================================================
# Defaults
# ============================================================================

_DEFAULT_COMPANY_DOMAINS: list[str] = []

_DEFAULT_COMPANY_KEYWORDS: list[str] = []


# ============================================================================
# Config
# ============================================================================


@dataclass
class FirefliesConfig:
    """Configuration for the Fireflies.ai Transcript Sync engine."""

    # Auth
    api_key: str = ""
    graphql_url: str = "https://api.fireflies.ai/graphql"

    # Company classification (shared env vars with Read.ai)
    company_name: str = ""
    company_domains: list[str] = field(default_factory=list)
    company_keywords: list[str] = field(default_factory=list)

    # Tagging -- shared MEET-XXXX sequence with Read.ai
    tag_prefix: str = "MEET"

    # Polling
    poll_interval_minutes: int = 5
    page_size: int = 50

    # Destinations — route to knowledge bucket inboxes (3-bucket arch)
    empresa_dir: Path = field(default_factory=lambda: ROUTING["business_inbox"])
    pessoal_dir: Path = field(default_factory=lambda: ROUTING["personal_inbox"])

    # State & Logs
    state_path: Path = field(default_factory=lambda: MISSION_CONTROL / "FIREFLIES-STATE.json")
    log_dir: Path = field(
        default_factory=lambda: LOGS / "read-ai-harvest"  # shared log dir
    )

    def validate(self) -> list[str]:
        """Return list of missing required fields."""
        errors: list[str] = []
        if not self.api_key:
            errors.append("FIREFLIES_API_KEY is required")
        if not self.company_domains:
            errors.append(
                "Company domains are required (set READ_AI_COMPANY_DOMAINS or COMPANY_DOMAINS)"
            )
        return errors


# ============================================================================
# Helpers
# ============================================================================


def _parse_csv(value: str) -> list[str]:
    """Parse comma-separated env var into list of stripped strings."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_dotenv_stdlib(path: Path) -> None:
    """Minimal .env parser using only stdlib."""
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


# ============================================================================
# Factory
# ============================================================================


def load_config() -> FirefliesConfig:
    """
    Load FirefliesConfig from environment variables.

    Tries to load .env file first if present, otherwise relies on
    shell-exported vars.  Falls back to _DEFAULT_* constants when the
    company classification env vars are absent.
    """
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path.exists():
        _load_dotenv_stdlib(env_path)

    # Company domains: try COMPANY_DOMAINS, then READ_AI_COMPANY_DOMAINS
    raw_domains = os.getenv(
        "COMPANY_DOMAINS",
        os.getenv("READ_AI_COMPANY_DOMAINS", ""),
    )
    domains = _parse_csv(raw_domains) or _DEFAULT_COMPANY_DOMAINS

    # Company keywords: try COMPANY_KEYWORDS, then READ_AI_COMPANY_KEYWORDS
    raw_keywords = os.getenv(
        "COMPANY_KEYWORDS",
        os.getenv("READ_AI_COMPANY_KEYWORDS", ""),
    )
    keywords = _parse_csv(raw_keywords) or _DEFAULT_COMPANY_KEYWORDS

    # Company name: try COMPANY_NAME, then READ_AI_COMPANY_NAME
    company_name = os.getenv(
        "COMPANY_NAME",
        os.getenv("READ_AI_COMPANY_NAME", ""),
    )

    cfg = FirefliesConfig(
        api_key=os.getenv("FIREFLIES_API_KEY", ""),
        graphql_url=os.getenv(
            "FIREFLIES_GRAPHQL_URL",
            "https://api.fireflies.ai/graphql",
        ),
        company_name=company_name,
        company_domains=domains,
        company_keywords=keywords,
        tag_prefix=os.getenv("FIREFLIES_TAG_PREFIX", "MEET"),
        poll_interval_minutes=int(os.getenv("FIREFLIES_POLL_INTERVAL", "5")),
        page_size=int(os.getenv("FIREFLIES_PAGE_SIZE", "50")),
    )
    return cfg


# ============================================================================
# CLI
# ============================================================================


if __name__ == "__main__":
    cfg = load_config()
    errors = cfg.validate()
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    print(f"api_key={'***' + cfg.api_key[-4:] if len(cfg.api_key) > 4 else '(empty)'}")
    print(f"graphql_url={cfg.graphql_url}")
    print(f"company_name={cfg.company_name}")
    print(f"company_domains={cfg.company_domains}")
    print(f"company_keywords={cfg.company_keywords}")
    print(f"tag_prefix={cfg.tag_prefix}")
    print(f"poll_interval_minutes={cfg.poll_interval_minutes}")
    print(f"page_size={cfg.page_size}")
    print(f"empresa_dir={cfg.empresa_dir}")
    print(f"pessoal_dir={cfg.pessoal_dir}")
    print(f"state_path={cfg.state_path}")
    print(f"log_dir={cfg.log_dir}")
    print("OK")
