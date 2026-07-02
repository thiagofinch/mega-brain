#!/usr/bin/env python3
"""
CONTRACT RESOLVER - Domain-File Contract Resolution
=====================================================
Resolves queries to pre-defined file sets based on domain contracts.

When a query matches a domain contract's keywords, the resolver reads
ALL files listed in that contract's ``always_read`` list and returns
the assembled context. If no contract matches, returns None so the
caller can fall through to RAG pipelines.

Domain classification reuses scope_classifier's expert/entity signals
where possible (no duplication).

Performance target: <500ms for contract-resolved queries.

Version: 1.0.0
Date: 2026-03-25
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CONTRACTS_PATH = Path(__file__).resolve().parent / "domain_contracts.yaml"


# ---------------------------------------------------------------------------
# CONTRACT DATA MODEL
# ---------------------------------------------------------------------------
class DomainContract:
    """A single domain-to-files contract."""

    __slots__ = ("always_read", "description", "fallback", "keywords", "name")

    def __init__(
        self,
        name: str,
        description: str,
        keywords: list[str],
        always_read: list[str],
        fallback: str = "hybrid_search",
    ) -> None:
        self.name = name
        self.description = description
        # Normalize keywords to lowercase for matching
        self.keywords = [kw.lower() for kw in keywords]
        self.always_read = always_read
        self.fallback = fallback

    def match_score(self, query: str) -> int:
        """Count how many keywords appear in the query.

        The query is lowercased internally for case-insensitive matching.

        Returns: number of keyword hits (0 = no match).
        """
        query_lower = query.lower()
        hits = 0
        for kw in self.keywords:
            if kw in query_lower:
                hits += 1
        return hits


# ---------------------------------------------------------------------------
# CONTRACT REGISTRY
# ---------------------------------------------------------------------------
class ContractRegistry:
    """Loads and holds all domain contracts from YAML."""

    def __init__(self) -> None:
        self._contracts: list[DomainContract] = []
        self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def contracts(self) -> list[DomainContract]:
        return self._contracts

    def load(self, contracts_path: Path | None = None) -> None:
        """Load contracts from YAML file."""
        path = contracts_path or _CONTRACTS_PATH
        t0 = time.time()

        if not path.exists():
            logger.warning("Domain contracts file not found: %s", path)
            self._loaded = True
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict) or "contracts" not in data:
                logger.warning("Invalid domain contracts format in %s", path)
                self._loaded = True
                return

            for name, spec in data["contracts"].items():
                if not isinstance(spec, dict):
                    continue
                contract = DomainContract(
                    name=name,
                    description=spec.get("description", ""),
                    keywords=spec.get("keywords", []),
                    always_read=spec.get("always_read", []),
                    fallback=spec.get("fallback", "hybrid_search"),
                )
                self._contracts.append(contract)

            self._loaded = True
            elapsed = (time.time() - t0) * 1000
            logger.debug(
                "ContractRegistry loaded: %d contracts, %.1fms",
                len(self._contracts),
                elapsed,
            )

        except (yaml.YAMLError, OSError) as e:
            logger.warning("Failed to load domain contracts: %s", e)
            self._loaded = True

    def classify_domain(self, query: str) -> tuple[DomainContract | None, int]:
        """Classify a query into a domain contract.

        Uses keyword matching. The contract with the most keyword hits wins.
        Ties go to the first contract (order in YAML matters).

        Returns:
            (matched_contract, hit_count) or (None, 0) if no match.
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return None, 0

        best_contract: DomainContract | None = None
        best_hits = 0

        for contract in self._contracts:
            hits = contract.match_score(query_lower)
            if hits > best_hits:
                best_hits = hits
                best_contract = contract

        return best_contract, best_hits


# ---------------------------------------------------------------------------
# RESOLVER
# ---------------------------------------------------------------------------
class ContractResolver:
    """Resolves queries to file content via domain contracts.

    Usage:
        resolver = ContractResolver()
        resolver.load()
        result = resolver.resolve("como melhorar close rate de vendas?")
        if result:
            print(result["domain"], result["files_read"])
        else:
            # Fall through to RAG
            pass
    """

    def __init__(self) -> None:
        self._registry = ContractRegistry()

    @property
    def loaded(self) -> bool:
        return self._registry.loaded

    def load(self, contracts_path: Path | None = None) -> None:
        """Load the contract registry."""
        self._registry.load(contracts_path)

    def resolve(
        self,
        query: str,
        min_hits: int = 1,
        root: Path | None = None,
    ) -> dict[str, Any] | None:
        """Attempt to resolve a query via domain contracts.

        Args:
            query: The search query.
            min_hits: Minimum keyword hits required to activate a contract.
            root: Project root override (for testing).

        Returns:
            dict with keys:
                - query: original query
                - domain: matched domain name
                - description: domain description
                - keyword_hits: number of matching keywords
                - files: list of Path objects that were read
                - files_read: number of files successfully read
                - files_missing: list of paths that didn't exist
                - content: concatenated file content
                - resolution_path: "contract:{domain}"
                - fallback: configured fallback for this domain
                - latency_ms: float
            None if no contract matches.
        """
        if not self._registry.loaded:
            self.load()

        t0 = time.time()
        project_root = root or _ROOT

        contract, hits = self._registry.classify_domain(query)

        if contract is None or hits < min_hits:
            logger.debug(
                "Contract resolver: no domain match for query (hits=%d): %s",
                hits,
                query[:80],
            )
            return None

        # Read all always_read files
        content_parts: list[str] = []
        resolved_files: list[Path] = []
        missing_files: list[str] = []
        max_chars = 48000  # ~12K tokens — contracts can be generous
        total_chars = 0

        for rel_path in contract.always_read:
            abs_path = project_root / rel_path
            if not abs_path.exists():
                missing_files.append(rel_path)
                logger.debug("Contract file missing: %s", abs_path)
                continue

            try:
                text = abs_path.read_text(encoding="utf-8")
                if total_chars + len(text) > max_chars:
                    remaining = max_chars - total_chars
                    if remaining > 200:
                        text = text[:remaining]
                    else:
                        break
                content_parts.append(f"[CONTRACT:{contract.name}:{abs_path.name}]\n{text}")
                resolved_files.append(abs_path)
                total_chars += len(text)
            except (OSError, UnicodeDecodeError) as e:
                missing_files.append(rel_path)
                logger.warning("Failed to read contract file %s: %s", abs_path, e)

        if not content_parts:
            logger.debug(
                "Contract resolver: domain '%s' matched but no files readable",
                contract.name,
            )
            return None

        latency = (time.time() - t0) * 1000
        resolution_path = f"contract:{contract.name}"

        logger.info(
            "Contract resolved: domain=%s, hits=%d, files=%d, latency=%.1fms",
            contract.name,
            hits,
            len(resolved_files),
            latency,
        )

        return {
            "query": query,
            "domain": contract.name,
            "description": contract.description,
            "keyword_hits": hits,
            "files": resolved_files,
            "file_paths": [str(f) for f in resolved_files],
            "files_read": len(resolved_files),
            "files_missing": missing_files,
            "content": "\n\n".join(content_parts),
            "resolution_path": resolution_path,
            "fallback": contract.fallback,
            "latency_ms": round(latency, 1),
        }

    def list_contracts(self) -> list[dict[str, Any]]:
        """List all loaded contracts with metadata."""
        if not self._registry.loaded:
            self.load()
        return [
            {
                "name": c.name,
                "description": c.description,
                "keywords_count": len(c.keywords),
                "files_count": len(c.always_read),
                "fallback": c.fallback,
            }
            for c in self._registry.contracts
        ]


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------
_resolver: ContractResolver | None = None


def get_contract_resolver() -> ContractResolver:
    """Get or create the singleton ContractResolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = ContractResolver()
        _resolver.load()
    return _resolver


def contract_resolve(query: str) -> dict[str, Any] | None:
    """Convenience function: resolve a query using the singleton resolver."""
    return get_contract_resolver().resolve(query)
