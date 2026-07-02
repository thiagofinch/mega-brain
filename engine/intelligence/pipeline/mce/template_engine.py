"""
template_engine.py -- Declarative YAML -> prompt compiler for MCE extraction
============================================================================

Why this exists
---------------
The MCE insights extractor ships a single free-form prompt hardcoded in
``orchestrate.py`` (``_INSIGHTS_PROMPT_TEMPLATE`` / ``prompts/insights.prompt.md``).
That prompt bakes one extraction policy into the engine: which entity tags to
use, which fields to emit, how relations are described. Changing *what* to
extract for a new domain (a legal contract vs. a sales-call transcript) meant
editing Python or the canonical prompt file -- a code change, reviewed and
deployed, for what is really a *configuration* concern.

This module adds an OPT-IN config surface: an extraction **template** declared
in YAML. The YAML says WHAT to extract (entity types, relation types, fields);
the compiler turns that declaration into the prompt text the extractor sends to
Gemini. No template -> the engine uses its hardcoded prompt, byte-for-byte
unchanged (the legacy default path is never touched).

ADAPT provenance
----------------
Adapted -- NOT copied -- from Hyper-Extract
``4e333f847f1d:hyperextract/utils/template_engine/parsers/guideline.py``
(``parse_guideline``) and ``factory.py`` (``TemplateFactory.create`` ->
``create_graph``). In Hyper-Extract the YAML schema (``guideline.target`` +
``rules_for_entities`` + ``rules_for_relations``) is compiled into a prompt by
concatenating titled sections and appending a ``{source_text}`` placeholder.
We reproduce that *shape* against the MCE's reality:

  * Hyper-Extract is LangChain + pydantic AutoType machinery. The MCE has no
    such machinery -- it sends a plain string to ``llm_extractor.run_prompt``
    and parses JSON. So the compiler emits a plain ``str`` whose placeholders
    (``{person_name}``, ``{tag_code}``, ``{chunk_count}``, ``{chunks_block}``)
    match exactly what ``cmd_insights`` already feeds ``str.format``. The
    compiled prompt is therefore a drop-in replacement for
    ``_INSIGHTS_PROMPT_TEMPLATE`` with NO change to the call site contract.
  * Hyper-Extract's ``{source_text}`` placeholder becomes the MCE's
    ``{chunks_block}`` (the MCE batches chunks, not a single document).

Provenance of the source lines read (Task 1, contract of absorption) is
recorded in the story Dev Record.

Status
------
Added 2026-06-25 as STORY-HGA-F1.3 (Sprint 1, EPIC-HYPERGRAPH-ABSORPTION).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("mce.template_engine")

# Env var an operator sets to a YAML path to opt IN to template-driven prompts.
# Unset / empty -> the engine keeps its hardcoded insights prompt.
TEMPLATE_ENV = "MCE_INSIGHTS_TEMPLATE"

# Placeholders the compiled prompt MUST preserve so it stays a drop-in for
# ``_INSIGHTS_PROMPT_TEMPLATE`` at the ``cmd_insights`` ``.format(...)`` site.
# Compiled prompts emit these verbatim; chunk text is injected by the caller.
_REQUIRED_PLACEHOLDERS = ("{person_name}", "{tag_code}", "{chunk_count}", "{chunks_block}")


class TemplateError(ValueError):
    """Raised when a template YAML is malformed or cannot be compiled."""


def resolve_template_path(explicit: str | None = None) -> str | None:
    """Resolve the active template path (None = use hardcoded prompt).

    Precedence: explicit arg > ``MCE_INSIGHTS_TEMPLATE`` env > None. An empty or
    whitespace-only value resolves to None so the DEFAULT (hardcoded) path can
    never be broken by an accidentally-set-but-blank env var -- fail-safe to the
    legacy behaviour, exactly like ``resolve_extraction_mode`` (F1.2).
    """
    raw = (explicit if explicit is not None else os.environ.get(TEMPLATE_ENV) or "").strip()
    return raw or None


def _load_yaml(path: str | Path) -> dict[str, Any]:
    """Read + parse the template YAML into a mapping.

    Kept separate from compilation so tests can compile an in-memory dict
    without touching the filesystem (mirrors Hyper-Extract's ``load_template``
    vs. ``TemplateFactory.create(config, ...)`` split).
    """
    p = Path(path)
    if not p.exists():
        raise TemplateError(f"template not found: {p}")
    try:
        import yaml  # PyYAML is a project dependency (stdlib + PyYAML only).
    except ImportError as exc:  # pragma: no cover - environment guarantee
        raise TemplateError("PyYAML is required to load extraction templates") from exc
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TemplateError(f"invalid YAML in template {p}: {exc}") from exc
    if not isinstance(data, dict):
        raise TemplateError(f"template root must be a mapping, got {type(data).__name__}")
    return data


def _as_lines(value: Any) -> list[str]:
    """Normalize a YAML scalar/sequence/mapping into a list of prompt lines.

    Adapts Hyper-Extract's ``str | List | Dict`` guideline fields: a string is
    one line; a list is one line per item; a mapping is ``key: value`` lines.
    Empty / falsy entries are dropped so the compiled prompt never carries a
    blank bullet (and so an absent section is simply omitted, never defaulted --
    honouring the no-fabricated-defaults principle).
    """
    if value is None:
        return []
    if isinstance(value, str):
        v = value.strip()
        return [v] if v else []
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            out.extend(_as_lines(item))
        return out
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            inner = _as_lines(v)
            if inner:
                out.append(f"{k}: {'; '.join(inner)}")
            elif v in (None, "", [], {}):
                out.append(str(k))
        return out
    return [str(value)]


def _bullets(value: Any) -> str:
    """Render normalized lines as a ``- `` bullet block (empty string if none)."""
    lines = _as_lines(value)
    return "\n".join(f"- {ln}" for ln in lines)


def compile_template(config: dict[str, Any]) -> str:
    """Compile a declarative template mapping into an insights prompt string.

    ADAPT of Hyper-Extract ``parse_guideline`` (graph branch): concatenate
    titled sections built from the declaration, then append the source-text
    placeholder. Sections with no content are omitted entirely (same as
    Hyper-Extract's ``if guideline.rules_for_entities:`` guards).

    Recognized keys (all optional except ``task``):

        task            -> "# Role and Task:" section (maps to ``target``)
        entity_types    -> entries under "## Entity Extraction Rules:"
        relation_types  -> entries under "## Relation Extraction Rules:"
        fields          -> "## Fields to Extract:" section (per-insight schema)
        rules           -> extra "## Extraction Rules:" section
        output_hint     -> trailing instruction before the chunks block

    The returned string carries the MCE placeholders verbatim so it is a
    drop-in for ``_INSIGHTS_PROMPT_TEMPLATE``: the caller's existing
    ``.format(person_name=..., tag_code=..., chunk_count=..., chunks_block=...)``
    fills them. Literal ``{`` / ``}`` from the YAML (e.g. a JSON example) are
    escaped to ``{{`` / ``}}`` so ``str.format`` does not choke on them.
    """
    if not isinstance(config, dict):
        raise TemplateError("template config must be a mapping")

    task = config.get("task")
    task_lines = _as_lines(task)
    if not task_lines:
        raise TemplateError("template must declare a non-empty 'task'")

    sections: list[str] = []
    sections.append("# Role and Task:\n" + "\n".join(task_lines))

    entity_block = _bullets(config.get("entity_types"))
    if entity_block:
        sections.append("## Entity Extraction Rules:\n" + entity_block)

    relation_block = _bullets(config.get("relation_types"))
    if relation_block:
        sections.append("## Relation Extraction Rules:\n" + relation_block)

    fields_block = _bullets(config.get("fields"))
    if fields_block:
        sections.append("## Fields to Extract:\n" + fields_block)

    rules_block = _bullets(config.get("rules"))
    if rules_block:
        sections.append("## Extraction Rules:\n" + rules_block)

    output_hint = _as_lines(config.get("output_hint"))
    if output_hint:
        sections.append("## Output:\n" + "\n".join(output_hint))

    sections.append(
        "## Context:\nPerson: {person_name} | tag code: {tag_code}"
    )
    sections.append("## Source Text ({chunk_count} chunks):\n{chunks_block}")

    body = "\n\n".join(sections)

    # Escape any literal braces from the YAML so str.format only sees OUR
    # placeholders. We escape first, then restore the known placeholders.
    body = body.replace("{", "{{").replace("}", "}}")
    for ph in _REQUIRED_PLACEHOLDERS:
        body = body.replace("{{" + ph[1:-1] + "}}", ph)

    _assert_placeholders(body)
    return body


def _assert_placeholders(prompt: str) -> None:
    """Guard: a compiled prompt must keep the MCE placeholders intact."""
    missing = [ph for ph in _REQUIRED_PLACEHOLDERS if ph not in prompt]
    if missing:
        raise TemplateError(
            f"compiled prompt is missing required placeholders: {missing}"
        )


def compile_template_file(path: str | Path) -> str:
    """Load + compile a template YAML file in one step."""
    return compile_template(_load_yaml(path))


def load_insights_prompt(explicit: str | None = None, *, fallback: str) -> str:
    """Resolve the insights prompt: compiled template if opted in, else fallback.

    This is the single integration seam for ``cmd_insights``. It NEVER raises
    into the pipeline: if a template is configured but fails to compile, it logs
    and returns ``fallback`` so a bad template degrades to the legacy prompt
    instead of breaking extraction (fail-safe, same spirit as F1.2's
    ``resolve_extraction_mode``).

    Args:
        explicit: optional explicit template path (overrides env).
        fallback: the hardcoded prompt to use when no template is active.

    Returns:
        The prompt string to ``.format(...)`` at the call site.
    """
    path = resolve_template_path(explicit)
    if path is None:
        return fallback
    try:
        prompt = compile_template_file(path)
        logger.info("template_engine: using compiled insights template from %s", path)
        return prompt
    except TemplateError as exc:
        logger.warning(
            "template_engine: failed to compile %s (%s) -- falling back to hardcoded prompt",
            path,
            exc,
        )
        return fallback
