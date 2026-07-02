"""state.py -- Persistent state manager for /ingerir-files skill."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STATE_DIR = Path.home() / ".claude" / "para-memory-files"
STATE_FILE = STATE_DIR / "ingerir-files-state.json"
STATE_VERSION = "1.0"


@dataclass
class AccountState:
    api_key_env: str
    last_sync_at: str | None = None
    discovered_meeting_ids: list[str] = field(default_factory=list)


@dataclass
class JarvisState:
    last_run_at: str | None = None
    processed_meeting_ids: list[str] = field(default_factory=list)
    pending_meeting_ids: list[str] = field(default_factory=list)


@dataclass
class DedupEntry:
    primary_id: str | None = None
    secondary_id: str | None = None
    local_meet_id: str | None = None
    primary_account: str | None = None


@dataclass
class IngerirFilesState:
    version: str = STATE_VERSION
    accounts: dict[str, AccountState] = field(default_factory=dict)
    jarvis: JarvisState = field(default_factory=JarvisState)
    dedup_index: dict[str, DedupEntry] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "accounts": {k: asdict(v) for k, v in self.accounts.items()},
            "jarvis": asdict(self.jarvis),
            "dedup_index": {k: asdict(v) for k, v in self.dedup_index.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IngerirFilesState":
        accounts = {k: AccountState(**v) for k, v in data.get("accounts", {}).items()}
        jarvis = JarvisState(**data.get("jarvis", {}))
        dedup = {k: DedupEntry(**v) for k, v in data.get("dedup_index", {}).items()}
        return cls(version=data.get("version", STATE_VERSION), accounts=accounts, jarvis=jarvis, dedup_index=dedup)


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _bootstrap_default_state() -> IngerirFilesState:
    return IngerirFilesState(
        accounts={
            "primary": AccountState(api_key_env="FIREFLIES_API_KEY"),
            "secondary": AccountState(api_key_env="FIREFLIES_API_KEY_SECONDARY"),
        }
    )


def load_state() -> IngerirFilesState:
    ensure_state_dir()
    if not STATE_FILE.exists():
        return _bootstrap_default_state()
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return IngerirFilesState.from_dict(json.load(f))


def save_state(state: IngerirFilesState) -> None:
    ensure_state_dir()
    tmp = STATE_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
    tmp.replace(STATE_FILE)


def _slugify(text: str, max_len: int = 40) -> str:
    if not text:
        return "untitled"
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")
    return cleaned[:max_len] or "untitled"


def make_signature(date_iso: str, title: str, duration_seconds: int) -> str:
    date_only = (date_iso or "")[:10]
    bucket_size = max(30, int(duration_seconds * 0.05))
    duration_bucket = (duration_seconds // bucket_size) * bucket_size if duration_seconds else 0
    return f"{date_only}_{_slugify(title)}_{duration_bucket}"


def upsert_dedup(state: IngerirFilesState, signature: str, account: str, meeting_id: str, local_meet_id: str | None = None) -> DedupEntry:
    entry = state.dedup_index.get(signature) or DedupEntry(primary_account=account, local_meet_id=local_meet_id)
    if account == "primary":
        entry.primary_id = meeting_id
    elif account == "secondary":
        entry.secondary_id = meeting_id
    if local_meet_id and not entry.local_meet_id:
        entry.local_meet_id = local_meet_id
    state.dedup_index[signature] = entry
    return entry


def stamp_account_sync(state: IngerirFilesState, account: str, discovered_ids: list[str]) -> None:
    if account not in state.accounts:
        return
    acc = state.accounts[account]
    acc.last_sync_at = datetime.now(UTC).isoformat()
    existing = set(acc.discovered_meeting_ids)
    acc.discovered_meeting_ids.extend([mid for mid in discovered_ids if mid not in existing])


def stamp_jarvis_run(state: IngerirFilesState, processed_ids: list[str]) -> None:
    state.jarvis.last_run_at = datetime.now(UTC).isoformat()
    existing = set(state.jarvis.processed_meeting_ids)
    new = [mid for mid in processed_ids if mid not in existing]
    state.jarvis.processed_meeting_ids.extend(new)


def diff_pending(state: IngerirFilesState, all_inbox_ids: list[str]) -> list[str]:
    processed = set(state.jarvis.processed_meeting_ids)
    return [mid for mid in all_inbox_ids if mid not in processed]


if __name__ == "__main__":
    import sys
    state = load_state()
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        print(json.dumps(state.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(state.to_dict(), indent=2, ensure_ascii=False))
