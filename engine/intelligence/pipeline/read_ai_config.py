"""
Read.ai Harvester Configuration.

Loads settings from environment variables (.env file).
All paths come from engine.paths — no hardcoding.

Usage:
    from engine.intelligence.pipeline.read_ai_config import load_config
    cfg = load_config()
    print(cfg.email, cfg.api_url)
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

from engine.config import get_config
from engine.paths import INBOX, MISSION_CONTROL, ROUTING, WORKSPACE


@dataclass
class ReadAIConfig:
    """Configuration for the Read.ai Transcript Harvester."""

    # Auth
    email: str = ""
    password: str = ""
    api_url: str = "https://api.read.ai/v1"

    # Company classification
    company_name: str = ""
    company_domains: list[str] = field(default_factory=list)
    company_keywords: list[str] = field(default_factory=list)

    # Tagging
    tag_prefix: str = "MEET"

    # Triggers
    ingestion_batch: int = 10
    gardener_trigger: int = 5

    # Pagination
    page_size: int = 50

    # Derived paths (from engine.paths)
    log_dir: Path = field(default_factory=lambda: ROUTING["read_ai_log"])
    state_path: Path = field(default_factory=lambda: ROUTING["read_ai_state"])
    staging_dir: Path = field(default_factory=lambda: ROUTING["read_ai_staging"])
    stop_signal: Path = field(default_factory=lambda: MISSION_CONTROL / "STOP-READ-AI-HARVEST")

    # Inbox destinations
    # empresa meetings go to workspace/inbox/meetings/ (matches existing harvest output)
    empresa_dir: Path = field(default_factory=lambda: WORKSPACE / "inbox" / "meetings")
    pessoal_dir: Path = field(default_factory=lambda: INBOX / "PESSOAL" / "MEETINGS")

    def validate(self) -> list[str]:
        """Return list of missing required fields."""
        errors = []
        if not self.email:
            errors.append("READ_AI_EMAIL is required")
        if not self.password:
            errors.append("READ_AI_PASSWORD is required")
        if not self.company_name:
            errors.append("READ_AI_COMPANY_NAME is required")
        return errors


def _parse_csv(value: str) -> list[str]:
    """Parse comma-separated env var into list of stripped strings."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config() -> ReadAIConfig:
    """
    Load ReadAIConfig from the canonical config module.

    Hierarchy is handled by ``get_config()``:
    env system > .env file > config file > default.
    """
    cfg = ReadAIConfig(
        email=get_config("READ_AI_EMAIL", ""),
        password=get_config("READ_AI_PASSWORD", ""),
        api_url=get_config("READ_AI_API_URL", "https://api.read.ai/mcp"),
        company_name=get_config("READ_AI_COMPANY_NAME", ""),
        company_domains=_parse_csv(get_config("READ_AI_COMPANY_DOMAINS", "")),
        company_keywords=_parse_csv(get_config("READ_AI_COMPANY_KEYWORDS", "")),
        tag_prefix=get_config("READ_AI_TAG_PREFIX", "MEET"),
        ingestion_batch=int(get_config("READ_AI_INGESTION_BATCH", "10")),
        gardener_trigger=int(get_config("READ_AI_GARDENER_TRIGGER", "5")),
        page_size=int(get_config("READ_AI_PAGE_SIZE", "50")),
    )
    return cfg


if __name__ == "__main__":
    cfg = load_config()
    errors = cfg.validate()
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    print(f"email={cfg.email}")
    print(f"api_url={cfg.api_url}")
    print(f"company_name={cfg.company_name}")
    print(f"company_domains={cfg.company_domains}")
    print(f"company_keywords={cfg.company_keywords}")
    print(f"tag_prefix={cfg.tag_prefix}")
    print(f"ingestion_batch={cfg.ingestion_batch}")
    print(f"gardener_trigger={cfg.gardener_trigger}")
    print(f"page_size={cfg.page_size}")
    print(f"log_dir={cfg.log_dir}")
    print(f"state_path={cfg.state_path}")
    print(f"staging_dir={cfg.staging_dir}")
    print("OK")
