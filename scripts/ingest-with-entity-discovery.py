#!/usr/bin/env python3
"""Ingest a video/file with Entity Discovery (orchestrator for /ingest slash command).

Orchestrates the corrected ingestion flow:
  1. Run Speaker Visual Gate (extract_local_video_via_gemini) on the file
  2. Parse filename evidence (parse_filename_evidence)
  3. Reconcile via infer_entities -> entity_author + entity_subject
  4. Decide target inbox based on entity routing:
     - External author (e.g. um especialista) -> knowledge/external/inbox/{author}/
     - Business subject (e.g. internal call) -> knowledge/business/inbox/{subject}/
  5. Move/copy file to correct destination with sidecar metadata preserving
     the ORIGINAL filename and entity decision audit trail.
  6. With ``--process``, hand off to ``orchestrate.cmd_full`` so the full
     6-phase pipeline runs without manual python invocation.

Usage:
    python3 scripts/ingest-with-entity-discovery.py /path/to/video.mp4
    python3 scripts/ingest-with-entity-discovery.py /path/to/video.mp4 --dry-run
    python3 scripts/ingest-with-entity-discovery.py /path/to/video.mp4 --skip-gemini
       # skip Gemini, use filename evidence only (fast, deterministic)
    python3 scripts/ingest-with-entity-discovery.py /path/to/video.mp4 --process
       # after move + sidecar, fire orchestrate.cmd_full (ingest+batch+status)

Output: writes a JSON sidecar `{destination}/{original_name}.entity-discovery.json`
that MERGES the N1 normalizer fields (filename_original, tokens_dropped, ...)
with this N5 orchestrator's entity decision (decision, destination, gemini_used,
gemini_bypassed_reason). Last-writer-wins because the two field groups are disjoint.

Created 2026-05-13 as Phase 4 wiring (sua-organizacao contamination fix campaign).
Extended 2026-05-13 for STORY-MCE-ROUND-TRIP N5/G5 (composition-engineer sign-off:
C-N5-1 observability parity, C-N5-2 sidecar merge Option A, C-N5-3 fail-open).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# --- REPO resolution (no hardcoded user path) ---------------------------------
def _resolve_repo_root() -> Path:
    """Resolve the repository root portably.

    Priority:
      1. CLAUDE_PROJECT_DIR env var (set by Claude Code).
      2. Parent of the directory holding this script (scripts/ -> repo).
    """
    env_root = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_root:
        root = Path(env_root).resolve()
        if (root / "engine").is_dir():
            return root
    return Path(__file__).resolve().parent.parent


REPO = _resolve_repo_root()
sys.path.insert(0, str(REPO))


# --- G8 (2026-05-13): load .env so GEMINI_API_KEY is available ---------------
# Previously this orchestrator script only inspected ``os.environ``, so even
# when ``.env`` had a valid GEMINI_API_KEY the Speaker Visual Gate was bypassed
# with reason "GEMINI_API_KEY absent" and downstream got no transcript for
# video inputs. We mirror the pattern already used by
# engine/intelligence/pipeline/video/pipeline.py L304-310 instead of
# pulling in python-dotenv as a new dependency.
def _bootstrap_env_from_dotenv() -> None:
    """Populate ``os.environ`` from ``REPO / .env`` (idempotent, fail-open)."""
    env_path = REPO / ".env"
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


_bootstrap_env_from_dotenv()


# --- Observability parity (C-N5-1) --------------------------------------------
# Slash command invokes us with `python3 -u`. We also force line-buffered prints
# ourselves so the slash UX sees streaming output even if upstream forgot -u.
def _emit(msg: str) -> None:
    """Print + flush so the slash command sees progressive output."""
    print(msg, flush=True)


def _word_count_from_binary_doc(path: Path, ext: str) -> int | None:
    """Word count for a binary document via the REAL text extractor.

    Onda 0 honesty fix (extraction-no-fallbacks). Reading a .pdf/.docx as
    UTF-8 decodes the raw byte stream as garbage and fabricates an enormous
    word count (a Hormozi PDF produced 697,538 fake "words"). Instead we run
    the same extractors the chunk pipeline uses and count words on the
    extracted text.

    Returns:
        int  — real word count from extracted text.
        None — explicit gap: extractor missing, file corrupt, or image-only
               document with no selectable text. NEVER a fabricated number and
               NEVER a zero presented as if it were a measurement.
    """
    try:
        from engine.intelligence.pipeline.extractors import (
            extract_docx_raw,
            extract_pdf,
        )
    except Exception as exc:  # extractor deps unavailable
        _emit(
            f"  [word-count] gap: extractor unavailable for {ext} "
            f"({type(exc).__name__}); word_count=None (not fabricated)"
        )
        return None

    try:
        if ext == ".pdf":
            text = extract_pdf(str(path))
        elif ext in {".docx", ".doc"}:
            text = extract_docx_raw(str(path))
        else:
            # Other binary formats (.pptx/.xlsx/...) have no extractor wired
            # here yet — emit an explicit gap rather than guessing.
            _emit(
                f"  [word-count] gap: no extractor wired for {ext}; "
                f"word_count=None (not fabricated)"
            )
            return None
    except Exception as exc:  # missing native dep / corrupt / image-only
        _emit(
            f"  [word-count] gap: extraction failed for {path.name} "
            f"({type(exc).__name__}: {exc}); word_count=None (not fabricated)"
        )
        return None

    count = len((text or "").split())
    if count == 0:
        # Zero selectable words is itself a signal (image-only PDF needing
        # OCR — Onda 3). Surface it as a gap, not a silent measured zero.
        _emit(
            f"  [word-count] gap: {path.name} yielded 0 selectable words "
            f"(likely image-only {ext}, OCR needed); word_count=None"
        )
        return None
    return count


def slugify(name: str) -> str:
    """Convert a name to kebab-case slug."""
    import re

    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


# --- URL detection (STORY-MCE-INGEST-URL, 2026-05-19) -------------------------
def _is_youtube_url(s: str) -> bool:
    """Return True if ``s`` looks like a YouTube URL.

    Pattern: starts with http:// or https:// AND host contains youtube.com or
    youtu.be. We do NOT validate the video ID — yt-dlp / Gemini will surface
    a 404 if the ID is bogus.
    """
    if not s:
        return False
    if not (s.startswith("http://") or s.startswith("https://")):
        return False
    return "youtube.com" in s or "youtu.be" in s


# --- Shared yt-dlp metadata fetch --------------------------------------------
# Both Tier 1 (captions) and Tier 2 (whisper) need title + uploader + duration
# + availability up-front. Extracted so we never duplicate the call.
def _yt_metadata(url: str) -> dict | None:
    """Fetch YouTube metadata via yt-dlp --skip-download.

    Returns ``None`` on any failure (yt-dlp missing, network error, timeout,
    or private video that even yt-dlp cannot reach). The uploader field
    here is the AUTHORITATIVE source of truth for routing — it comes from
    YouTube's API, not from transcript content. Cascading downstream uses
    this as confidence="high" speaker (overriding any transcript artifact).
    """
    try:
        meta = subprocess.run(
            [
                "yt-dlp",
                "--no-update",
                "--skip-download",
                "--print",
                "%(title)s|%(uploader)s|%(duration)s|%(availability)s",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        _emit("  [warn] yt-dlp not installed -- pip install -U yt-dlp")
        return None
    except subprocess.TimeoutExpired:
        _emit("  [warn] yt-dlp metadata timed out (>60s)")
        return None

    if meta.returncode != 0:
        _emit(f"  [warn] yt-dlp metadata failed: {meta.stderr.strip()[:200]}")
        return None

    parts = (meta.stdout.strip() or "untitled|unknown|0|unknown").split("|", 3)
    return {
        "title": (parts[0].strip() if parts else "untitled") or "untitled",
        "uploader": (parts[1].strip() if len(parts) > 1 else "unknown") or "unknown",
        "duration": (parts[2].strip() if len(parts) > 2 else "0") or "0",
        "availability": (
            parts[3].strip() if len(parts) > 3 else "unknown"
        )
        or "unknown",
    }


# --- YouTube Tier 1: auto-captions (STORY-MCE-YT-CAPTIONS-FIRST) -------------
# Pulls YouTube's own auto-generated captions via yt-dlp --write-auto-subs.
# 165x faster than Whisper (3s vs 8min for a 36min video). Quality is "good
# enough" for 90% of cases — Whisper wins on proper nouns and technical
# terms, but the routing/cascade NEVER depends on transcript content (the
# uploader name is what travels — see infer_entities + speakers contract).
def _youtube_fetch_captions(url: str) -> dict | None:
    """Tier 1 fallback: pull YouTube auto-captions (no audio download).

    Returns a gemini_result-shaped dict on success:
        {title, transcript, speakers=[{name=uploader, confidence=high}],
         _fallback=True, _fallback_source="youtube-captions",
         _uploader, _availability, _duration}

    Returns ``None`` when:
        - yt-dlp metadata call fails (no network, bad URL, video private)
        - video has no English auto-captions (rare for public English videos)
        - caption fetch fails or produces empty content

    On ``None`` the caller MUST try Tier 2 (whisper) before giving up.
    """
    import re
    import tempfile

    _emit("\n[1.5/4] CAPTIONS: yt-dlp auto-subs (Tier 1, fast path)")

    meta = _yt_metadata(url)
    if not meta:
        return None

    title = meta["title"]
    uploader = meta["uploader"]
    duration = meta["duration"]
    availability = meta["availability"]

    _emit(f"  Title:      {title}")
    _emit(f"  Uploader:   {uploader}")
    _emit(f"  Duration:   {duration}s")
    _emit(f"  Available:  {availability}")

    if availability in ("private", "needs_auth", "subscriber_only"):
        _emit(f"  [warn] video is {availability} -- captions inaccessible")
        return None

    with tempfile.TemporaryDirectory(prefix="mce-yt-cap-") as tmpdir:
        sub_template = str(Path(tmpdir) / "subs")
        _emit("  [yt-dlp] fetching auto-captions (en)...")
        try:
            dl = subprocess.run(
                [
                    "yt-dlp",
                    "--no-update",
                    "--write-auto-subs",
                    "--sub-langs",
                    "en",
                    "--skip-download",
                    "--sub-format",
                    "vtt",
                    "-o",
                    sub_template,
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            _emit("  [warn] caption fetch timed out (>2min)")
            return None

        if dl.returncode != 0:
            _emit(
                f"  [warn] caption fetch failed: {dl.stderr.strip()[:200]}"
            )
            return None

        vtt_files = list(Path(tmpdir).glob("subs*.vtt"))
        if not vtt_files:
            _emit("  [warn] no .vtt file produced (no English captions)")
            return None

        vtt_path = vtt_files[0]
        try:
            vtt_raw = vtt_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            _emit(f"  [warn] could not read .vtt file: {exc}")
            return None

        # Dedupe rolling YouTube captions: each line repeats the previous +
        # adds new tokens. We extract unique caption lines after stripping
        # inline timing tags <00:00:00.080><c> ... </c>.
        seen: set[str] = set()
        plain_lines: list[str] = []
        for raw_line in vtt_raw.splitlines():
            s = raw_line.strip()
            if not s:
                continue
            if s.startswith("WEBVTT") or s.startswith("Kind:") or s.startswith(
                "Language:"
            ):
                continue
            if "-->" in s or "align:" in s:
                continue
            # Strip inline timing tags (<00:00:00.080><c>word</c>)
            s = re.sub(r"<[^>]+>", "", s).strip()
            if not s or s in seen:
                continue
            seen.add(s)
            plain_lines.append(s)

        transcript = " ".join(plain_lines).strip()
        if not transcript:
            _emit("  [warn] caption file was empty after parse")
            return None

    word_count = len(transcript.split())
    _emit(
        f"  Captions OK: {len(plain_lines)} segments, "
        f"{word_count} words, {len(transcript)} chars"
    )

    return {
        "title": title,
        "transcript": transcript,
        # AUTHORITATIVE: uploader name is what travels. Confidence=high so
        # infer_entities crowns this as author_candidate (overrides any
        # transcript artifact). Routing locks to the channel, not the words.
        "speakers": (
            [{"name": uploader, "confidence": "high"}]
            if uploader and uploader != "unknown"
            else []
        ),
        "_fallback": True,
        "_fallback_source": "youtube-captions",
        "_uploader": uploader,
        "_availability": availability,
        "_duration": duration,
    }


# --- YouTube Tier 2: yt-dlp + faster-whisper (STORY-MCE-YT-FALLBACK) ---------
# Triggered when Gemini cannot access a YouTube URL AND Tier 1 captions also
# failed. Produces a gemini_result-shaped dict so the rest of
# ``ingest_youtube_url`` proceeds with no branching downstream.
# Author signal comes from the YouTube uploader (yt-dlp metadata) which is
# fed into ``infer_entities`` via the synthetic ``speakers`` field.
def _youtube_fallback_download_transcribe(
    url: str,
    *,
    model_size: str = "base",
) -> dict | None:
    """Fallback path when Gemini cannot extract a YouTube URL.

    Steps:
        1. ``yt-dlp --skip-download --print ...`` -> title + uploader + duration.
        2. ``yt-dlp -x --audio-format m4a -o ...`` -> audio file to a tempdir.
        3. ``faster-whisper`` (base, CPU int8) -> transcript text.
        4. Return a dict mirroring Gemini's shape (``title``, ``transcript``,
           ``speakers=[{name=uploader}]``) plus ``_fallback`` markers.

    Returns ``None`` on any unrecoverable failure (no yt-dlp, no whisper,
    download error, transcription error). The caller treats ``None`` as
    "fallback unavailable" and falls through to URL-only routing.
    """
    import tempfile

    _emit("\n[1.6/4] WHISPER: yt-dlp + faster-whisper LOCAL (Tier 2)")

    # --- Step 1: metadata via shared helper ---------------------------------
    meta = _yt_metadata(url)
    if not meta:
        return None

    title = meta["title"]
    uploader = meta["uploader"]
    duration = meta["duration"]
    availability = meta["availability"]

    _emit(f"  Title:      {title}")
    _emit(f"  Uploader:   {uploader}")
    _emit(f"  Duration:   {duration}s")
    _emit(f"  Available:  {availability}")

    if availability in ("private", "needs_auth", "subscriber_only"):
        _emit(f"  [warn] video is {availability} -- yt-dlp cannot fetch")
        return None

    # --- Step 2: download audio to tempdir ----------------------------------
    with tempfile.TemporaryDirectory(prefix="mce-yt-fb-") as tmpdir:
        audio_template = str(Path(tmpdir) / "audio.%(ext)s")
        _emit("  [yt-dlp] downloading audio (m4a)...")
        try:
            dl = subprocess.run(
                [
                    "yt-dlp",
                    "--no-update",
                    "-x",
                    "--audio-format",
                    "m4a",
                    "-o",
                    audio_template,
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            _emit("  [warn] yt-dlp download timed out (>10min)")
            return None

        if dl.returncode != 0:
            _emit(f"  [warn] yt-dlp download failed: {dl.stderr.strip()[:300]}")
            return None

        audio_files = list(Path(tmpdir).glob("audio.*"))
        if not audio_files:
            _emit("  [warn] yt-dlp produced no audio file")
            return None
        audio_path = audio_files[0]
        size_mb = audio_path.stat().st_size / (1024 * 1024)
        _emit(f"  Downloaded: {audio_path.name} ({size_mb:.1f} MB)")

        # --- Step 3: faster-whisper transcribe ------------------------------
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            _emit(
                "  [warn] faster-whisper not installed "
                "(pip install faster-whisper)"
            )
            return None

        _emit(f"  [whisper] loading model: {model_size} (compute_type=auto)")
        try:
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
        except Exception as exc:
            _emit(f"  [warn] whisper model load failed: {type(exc).__name__}: {exc}")
            return None

        _emit(f"  [whisper] transcribing {audio_path.name} ({size_mb:.1f} MB)...")
        try:
            segments, info = model.transcribe(str(audio_path), language=None)
        except Exception as exc:
            _emit(
                f"  [warn] whisper transcribe failed: "
                f"{type(exc).__name__}: {exc}"
            )
            return None

        lang = getattr(info, "language", "?")
        lang_prob = getattr(info, "language_probability", 0.0)
        _emit(f"  [whisper] detected language: {lang} (probability {lang_prob:.2f})")

        # Iterate lazily; segments is a generator
        chunks: list[str] = []
        for seg in segments:
            chunks.append(seg.text.strip())
        transcript = " ".join(chunks).strip()

        _emit(
            f"  [whisper] DONE -- {len(chunks)} segments, {len(transcript)} chars"
        )

    if not transcript:
        _emit("  [warn] whisper produced empty transcript")
        return None

    # --- Return gemini_result-shaped dict ------------------------------------
    return {
        "title": title,
        "transcript": transcript,
        # AUTHORITATIVE: uploader name is what travels. Confidence=high so
        # infer_entities crowns this as author_candidate (overrides any
        # transcript artifact). Routing locks to the channel, not the words.
        "speakers": (
            [{"name": uploader, "confidence": "high"}]
            if uploader and uploader != "unknown"
            else []
        ),
        "_fallback": True,
        "_fallback_source": "yt-dlp+faster-whisper",
        "_fallback_model": model_size,
        "_fallback_language": lang,
        "_uploader": uploader,
        "_availability": availability,
        "_duration": duration,
    }


def decide_destination(decision: dict) -> tuple[Path, str]:
    """Decide the inbox destination based on entity discovery decision.

    Routing rules:
        - If entity_author is a PERSON (multi-token) and entity_subject is a
          COMPANY -> file is EXTERNAL content (author's content about subject)
          -> route to knowledge/external/inbox/{author-slug}/
        - If only entity_subject (no author) and subject is a known internal
          slug -> route to knowledge/business/inbox/{subject-slug}/
        - Default (low confidence) -> knowledge/external/inbox/_unclassified/

    STORY-MCE-INGEST-ROBUSTNESS AC-3 (2026-05-27): known_business_slugs is
    now sourced DYNAMICALLY from workspace/businesses/* + partners-registry.
    Fail-open: if registry unavailable, fall back to legacy 5 BUs.

    Returns:
        (destination_path, reasoning)
    """
    author = decision.get("entity_author")
    subject = decision.get("entity_subject")
    confidence = decision.get("confidence", "low")  # noqa: F841 — diagnostic only

    try:
        from engine.intelligence.partners import all_business_slugs, list_external_slugs
        known_business_slugs = all_business_slugs()
        known_external_slugs = list_external_slugs()
    except Exception:
        # Fail-open to legacy hardcoded 5 BUs (AC-3 graceful degradation)
        known_business_slugs = {"sua-organizacao", "empresa-b", "empresa-c", "empresa-d", "empresa-e"}
        known_external_slugs = set()

    # =====================================================================
    # STORY-MCE-FOUNDER-ROUTING (2026-06-09) — HIGHEST PRECEDENCE
    # ---------------------------------------------------------------------
    # If the founder (o fundador / @sua-organizacao.com email / a name in a
    # people-registry) is a PARTICIPANT, this is a BUSINESS relationship,
    # NEVER an external expert. This rule OVERRIDES the person->external
    # default AND the external-force alias — a founder genuinely in the call
    # outranks a name-collision guardrail. The counterpart (the non-founder
    # party) becomes the slug; relationship_type is recorded for downstream.
    #
    #   counterpart matches a registry  -> "collaborator"
    #   counterpart is an external party -> "partner" (a.k.a. negotiation)
    # =====================================================================
    if decision.get("internal_party_present"):
        counterpart = decision.get("counterpart_display")
        # Prefer the registry-matched slug (collaborator case) over the raw
        # filename blob, so "Andre Tessmann sua-organizacao" routes to andre-tessmann/.
        counterpart_slug = decision.get("counterpart_slug") or (
            slugify(counterpart) if counterpart else None
        )

        # Classify the counterpart precisely (collaborator vs partner).
        rel_type = "partner"  # external party in a founder call = partner/negotiation
        try:
            from engine.intelligence.pipeline.internal_people import (
                classify as _classify_internal,
            )
        except Exception:
            _classify_internal = None  # type: ignore[assignment]

        if decision.get("counterpart_is_collaborator"):
            rel_type = "collaborator"
        elif counterpart and _classify_internal is not None:
            c = _classify_internal(counterpart)
            if c is not None:
                rel_type = "collaborator"

        # Choose the business slug. Prefer the counterpart (the person the
        # call is WITH). Fall back to the discovered subject, then the
        # founder slug itself, then a safe bucket.
        dest_slug = (
            counterpart_slug
            or subject
            or decision.get("internal_party_slug")
            or "_founder-calls"
        )
        dest = REPO / "knowledge" / "business" / "inbox" / dest_slug
        reason = (
            f"founder-in-call: internal party present "
            f"(signal={decision.get('internal_party_signal')}, "
            f"relationship_type={rel_type}) "
            f"-> business/{dest_slug}/ [counterpart={counterpart or 'n/a'}]"
        )
        # Stamp the resolved relationship_type back onto the decision so the
        # sidecar emitter persists it.
        decision["relationship_type"] = rel_type
        decision["routed_counterpart_slug"] = dest_slug
        return (dest, reason)

    # External-force aliases short-circuit (e.g. hormozi colliding with words)
    if (author and author in known_external_slugs) or (subject and subject in known_external_slugs):
        dest_slug = author if (author and author in known_external_slugs) else subject
        dest = REPO / "knowledge" / "external" / "inbox" / dest_slug
        return (dest, f"external-force alias hit -> external/{dest_slug}/")

    # Business-bucket partner short-circuit (e.g. cauduro recognized as partner)
    for cand in (author, subject):
        if cand and cand in known_business_slugs and cand not in {"sua-organizacao", "empresa-b", "empresa-c", "empresa-d", "empresa-e"}:
            # Partner (not internal BU) — route to business with cand as slug
            dest = REPO / "knowledge" / "business" / "inbox" / cand
            return (dest, f"partner registry hit '{cand}' -> business/{cand}/")

    # STORY-MCE-INGEST-ROBUSTNESS AC-4/AC-7: bucket_hint from local content
    # (Fireflies header parsing + FirefliesSync state consultation) takes
    # precedence over the legacy person-vs-company sintatico heuristic.
    bucket_hint = decision.get("bucket_hint")
    bucket_hint_conf = decision.get("bucket_hint_confidence", "none")
    if bucket_hint == "business" and bucket_hint_conf in ("high", "medium"):
        hint_slug = subject or author
        if hint_slug:
            dest = REPO / "knowledge" / "business" / "inbox" / hint_slug
            return (
                dest,
                f"local-content bucket_hint={bucket_hint} ({bucket_hint_conf}) "
                f"-> business/{hint_slug}/",
            )

    if author and subject:
        if subject in known_business_slugs and author not in known_business_slugs:
            dest = REPO / "knowledge" / "external" / "inbox" / author
            reason = (
                f"External author '{author}' presenting internal subject "
                f"'{subject}' -> external/{author}/"
            )
        else:
            dest = REPO / "knowledge" / "external" / "inbox" / author
            reason = (
                f"External author '{author}' about external subject "
                f"'{subject}' -> external/{author}/"
            )
    elif subject:
        dest = REPO / "knowledge" / "business" / "inbox" / subject
        reason = f"Subject-only routing -> business/{subject}/"
    elif author:
        dest = REPO / "knowledge" / "external" / "inbox" / author
        reason = f"Author-only routing -> external/{author}/"
    else:
        dest = REPO / "knowledge" / "external" / "inbox" / "_unclassified"
        reason = "No entity discovered -- routed to unclassified"

    return (dest, reason)


# --- Sidecar merge (C-N5-2 Option A) ------------------------------------------
def _write_merged_sidecar(
    sidecar_file: Path,
    n5_payload: dict,
) -> None:
    """Write merged sidecar fail-open (C-N5-3).

    If a sidecar already exists at this path (likely emitted by N1 / inbox_organizer
    as schema_version 1.0.0), we MERGE this orchestrator's entity-decision fields
    on top. The two emitters touch disjoint field groups, so last-writer-wins is
    safe -- we bump schema_version to 1.1.0 to signal the merged shape.

    Failure to write is logged but NOT raised, consistent with N4 log_and_continue
    strategy (Art. XII pipeline integrity > observability).
    """
    try:
        merged: dict = {}
        if sidecar_file.exists():
            try:
                existing = json.loads(sidecar_file.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    merged.update(existing)
            except Exception as exc:  # pragma: no cover -- best-effort merge
                _emit(
                    f"  [warn] could not parse existing sidecar "
                    f"({type(exc).__name__}: {exc!s:.100}); overwriting"
                )

        # N5 payload wins over its own keys; N1 keys (filename_original,
        # tokens_dropped, normalizer_rule, ...) survive untouched.
        merged.update(n5_payload)
        # Bump version to flag merged shape if N1 portion present.
        if "filename_original" in merged or "tokens_dropped" in merged:
            merged["schema_version"] = "1.1.0"

        sidecar_file.parent.mkdir(parents=True, exist_ok=True)
        sidecar_file.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        _emit(f"  Sidecar:  {sidecar_file.relative_to(REPO)} (merged)")
    except Exception as exc:
        # C-N5-3: fail-open. Log + continue; do NOT abort the move/downstream pipeline.
        _emit(
            f"  [warn] sidecar write failed ({type(exc).__name__}: {exc!s:.100}); "
            f"continuing fail-open per N4 log_and_continue (Art. XII)"
        )


def _emit_ingest_report(
    *,
    file_path: Path,
    destination_dir: Path,
    decision: dict,
    word_count: int | None,
    gemini_used: bool,
    gemini_bypassed_reason: str | None,
    process_flag: bool,
) -> None:
    """Print the legacy INGEST REPORT block as final stdout tail.

    Preserves the format documented in .claude/commands/ingest.md (founder
    Trade-off #3: downstream consumers may rely on this block).
    """
    ts = datetime.now().isoformat()
    author = decision.get("entity_author") or "(unknown)"
    subject = decision.get("entity_subject") or "(unknown)"
    rel_dest = destination_dir.relative_to(REPO) if destination_dir.is_relative_to(REPO) else destination_dir
    file_kind = "VIDEO" if file_path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv", ".avi"} else "DOCUMENTO"

    border = "=" * 79
    _emit("")
    _emit(border)
    _emit("                              INGEST REPORT")
    _emit(f"                         {ts}")
    _emit(border)
    _emit("")
    _emit("[in] MATERIAL INGERIDO")
    _emit(f"   Fonte: {file_path}")
    _emit(f"   Tipo:  {file_kind}")
    _emit("")
    _emit("[dest] DESTINO")
    _emit(f"   Path: {rel_dest}/{file_path.name}")
    _emit(f"   Author: {author}")
    _emit(f"   Subject: {subject}")
    _emit("")
    _emit("[stats] ESTATISTICAS")
    if word_count is not None:
        _emit(f"   Palavras: {word_count}")
    _emit(f"   Gemini used: {gemini_used}")
    if gemini_bypassed_reason:
        _emit(f"   Bypass reason: {gemini_bypassed_reason}")
    _emit(f"   Verdict: {decision.get('verdict')} ({decision.get('confidence')})")
    _emit("")
    _emit("[next] PROXIMA ETAPA")
    if process_flag:
        _emit("   Pipeline auto-fired via --process flag (see cmd_full output above)")
    else:
        _emit(
            f"   Para processar: python3 -m engine.intelligence.pipeline.mce.orchestrate "
            f"full \"{destination_dir}/{file_path.name}\""
        )
        _emit("   Ou: /inbox para ver pendentes")
    _emit("")
    _emit(border)


def _maybe_run_process(destination_file: Path) -> int:
    """Invoke ``orchestrate.cmd_full`` as a streaming subprocess (legacy monolithic path).

    C-N5-1 observability parity: we stream the child's stdout/stderr directly
    rather than capturing — operator sees live output, not just exit code.

    This is the LEGACY path. Prefer ``_maybe_run_jarvis_chief`` for new runs
    (STORY-MCE-6.0 Phase 8a).
    """
    cmd = [
        sys.executable,
        "-u",
        "-m",
        "engine.intelligence.pipeline.mce.orchestrate",
        "full",
        str(destination_file),
    ]
    _emit(f"\n[--process --legacy-monolithic] running: {' '.join(cmd[2:])}")
    _emit("---- cmd_full stream begin ----")
    try:
        # Inherit stdout/stderr -> live streaming
        rc = subprocess.call(cmd, cwd=str(REPO))
    except FileNotFoundError as exc:
        _emit(f"  [error] cmd_full launcher missing: {exc}")
        return 1
    _emit(f"---- cmd_full stream end (rc={rc}) ----")
    return rc


def _maybe_run_jarvis_chief(destination_file: Path) -> int:
    """Invoke ``jarvis-chief orchestrate <slug>`` as a streaming subprocess.

    STORY-MCE-6.0 Phase 8a — default --process path. Routes through
    jarvis-chief which renders each MCE phase as a chronicler ASCII block,
    giving the operator phase-by-phase visibility in chat.

    Slug is derived from the destination parent directory name (the inbox author
    or subject folder), matching the slug convention used by orchestrate.py and
    jarvis_chief.py.
    """
    slug = destination_file.parent.name
    cmd = [
        sys.executable,
        "-u",
        "-m",
        "engine.intelligence.pipeline.jarvis_chief",
        "orchestrate",
        slug,
    ]
    _emit(f"\n[--process] running jarvis-chief: {' '.join(cmd[2:])}")
    _emit("---- jarvis-chief stream begin ----")
    try:
        # Inherit stdout/stderr -> live chronicler render
        rc = subprocess.call(cmd, cwd=str(REPO))
    except FileNotFoundError as exc:
        _emit(f"  [error] jarvis-chief launcher missing: {exc}")
        return 1
    _emit(f"---- jarvis-chief stream end (rc={rc}) ----")
    return rc


def ingest_with_discovery(
    file_path: Path,
    *,
    dry_run: bool = False,
    skip_gemini: bool = False,
    process: bool = False,
    legacy_monolithic: bool = False,
    forced_author: str | None = None,
    forced_subject: str | None = None,
) -> dict:
    """Main orchestrator."""
    _emit("=" * 72)
    _emit("INGEST WITH ENTITY DISCOVERY -- /ingest slash orchestrator")
    _emit("=" * 72)
    _emit(f"Mode:    {'DRY-RUN' if dry_run else 'EXECUTE'}")
    _emit(f"File:    {file_path.name}")
    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        _emit(f"Size:    {size_mb:.1f} MB")
    except OSError:
        _emit("Size:    (unavailable)")

    # === STORY-MCE-INGEST-ROBUSTNESS AC-1 (FILE mode): early-exit ===
    # Mirror URL-mode MCE-7.0 AC-3 for paths already under knowledge/{bucket}/inbox/{slug}/.
    # When the file is ALREADY classified by an upstream layer (FirefliesSync +
    # MeetingRouter, inbox_organizer, etc), do NOT re-run Gemini/entity-discovery/routing.
    # Fire jarvis-chief orchestrate <slug> directly. Fail-open: any exception
    # falls through to normal flow.
    if not dry_run or dry_run:  # always evaluate (so dry-run can report the decision)
        try:
            rel_parts = file_path.resolve().relative_to(REPO).parts
        except ValueError:
            rel_parts = ()
        early_exit_slug: str | None = None
        early_exit_bucket: str | None = None
        early_exit_reasons: list[str] = []
        if (
            len(rel_parts) >= 5
            and rel_parts[0] == "knowledge"
            and rel_parts[1] in ("business", "external", "personal")
            and rel_parts[2] == "inbox"
        ):
            early_exit_bucket = rel_parts[1]
            early_exit_slug = rel_parts[3]
            early_exit_reasons.append(
                f"path under knowledge/{early_exit_bucket}/inbox/{early_exit_slug}/"
            )

            # Sidecar previously emitted by N1/inbox_organizer/N5?
            sidecar_probe = file_path.with_suffix(file_path.suffix + ".entity-discovery.json")
            if sidecar_probe.exists():
                early_exit_reasons.append(f"sidecar exists ({sidecar_probe.name})")

            # processed-sources registry hit?
            ps_probe = REPO / ".data" / "processed-sources" / f"{early_exit_slug}.json"
            if ps_probe.exists():
                early_exit_reasons.append("processed-sources registry hit")

            # MEET/CALL tag prefix in filename (FirefliesSync convention)?
            import re as _re_tag

            if _re_tag.search(r"\[(MEET|CALL)-\d+\]", file_path.name):
                early_exit_reasons.append("FirefliesSync tag prefix present")

        if early_exit_slug and len(early_exit_reasons) >= 1:
            _emit("\n[MCE-INGEST-ROBUSTNESS AC-1] FILE EARLY-EXIT")
            _emit(
                f"  Slug {early_exit_slug} ja classificado em "
                f"knowledge/{early_exit_bucket}/inbox/"
            )
            for r in early_exit_reasons:
                _emit(f"    - {r}")
            _emit("  Pulando Speaker Visual Gate + entity-discovery + routing.")

            if dry_run:
                _emit("  [DRY-RUN] would fire: jarvis-chief orchestrate "
                      f"{early_exit_slug}")
                return {
                    "status": "already_classified_dryrun",
                    "slug": early_exit_slug,
                    "bucket": early_exit_bucket,
                    "early_exit": True,
                    "reasons": early_exit_reasons,
                }

            if process:
                _emit(
                    f"\n[--process] Firing jarvis-chief on classified slug "
                    f"(idempotent)..."
                )
                _cmd_ee = [
                    sys.executable, "-u", "-m",
                    "engine.intelligence.pipeline.jarvis_chief",
                    "orchestrate", early_exit_slug,
                ]
                import subprocess as _sp_ee
                _rc_ee = _sp_ee.call(_cmd_ee, cwd=str(REPO))
                _emit(f"  jarvis-chief returned rc={_rc_ee}")
            else:
                _emit("  [--process not set] skipping orchestrate. "
                      f"Run: python3 -m engine.intelligence.pipeline.jarvis_chief "
                      f"orchestrate {early_exit_slug}")
                _rc_ee = None

            return {
                "status": "already_classified",
                "slug": early_exit_slug,
                "bucket": early_exit_bucket,
                "early_exit": True,
                "reasons": early_exit_reasons,
                "process_rc": _rc_ee,
            }

    # === STEP 1: extract_local_video_via_gemini (Phase 1) ===
    gemini_result = None
    gemini_bypassed_reason: str | None = None
    is_video = file_path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv", ".avi"}

    if skip_gemini:
        gemini_bypassed_reason = "--skip-gemini flag"
    elif not is_video:
        gemini_bypassed_reason = "non-video file"
    elif not os.environ.get("GEMINI_API_KEY"):
        gemini_bypassed_reason = "GEMINI_API_KEY absent"

    if gemini_bypassed_reason:
        # C-N5-1: explicit BYPASSED line so observability parity with N3 holds.
        _emit("\n[1/4] SPEAKER VISUAL GATE (pre_07)")
        _emit(f"[pre_07] BYPASSED (reason: {gemini_bypassed_reason})")
    else:
        _emit("\n[1/4] SPEAKER VISUAL GATE (pre_07)")
        try:
            from engine.intelligence.pipeline.video.pipeline import (
                assert_speakers_identified,
                extract_local_video_via_gemini,
            )

            _emit(f"  Calling Gemini on {file_path.name}...")
            # G8 (2026-05-13): include transcript when the input is a video,
            # so the downstream batcher has a .txt sidecar to chunk + embed.
            # Non-video files (e.g. .txt/.md/.pdf) don't need transcription.
            gemini_result = extract_local_video_via_gemini(
                file_path, include_transcript=is_video
            )
            if gemini_result:
                gate = assert_speakers_identified(gemini_result)
                _emit(f"  Gate verdict:     {gate['verdict']}")
                _emit(f"  Primary speaker:  {gate['primary_speaker']}")
                _emit(f"  Primary subject:  {gate['primary_subject']}")
                _emit(f"  Reason:           {gate['reason']}")
                if is_video:
                    tx = gemini_result.get("transcript")
                    if tx and isinstance(tx, str):
                        _emit(f"  Transcript chars: {len(tx)}")
                    else:
                        _emit("  Transcript:       (none — Gemini omitted)")
            else:
                _emit("  [warn] Gemini returned None -- proceeding with filename only")
                gemini_bypassed_reason = "gemini returned None"
        except Exception as e:
            _emit(
                f"  [warn] Gemini call failed "
                f"({type(e).__name__}: {str(e)[:100]}) -- filename only"
            )
            gemini_result = None
            gemini_bypassed_reason = f"exception: {type(e).__name__}"

    # === STEP 2: parse_filename_evidence + infer_entities (Phase 2) ===
    _emit("\n[2/4] ENTITY DISCOVERY (pre_08)")
    from engine.intelligence.pipeline.batch_auto_creator import (
        infer_entities,
        parse_filename_evidence,
    )

    fn_ev = parse_filename_evidence(file_path.name)
    _emit(f"  Filename persons:   {fn_ev['persons']}")
    _emit(f"  Filename companies: {fn_ev['companies']}")
    _emit(f"  Filename noise:     {fn_ev['noise']}")

    decision = infer_entities(
        file_path.name,
        gemini_result=gemini_result,
        file_path=file_path,
        forced_author=forced_author,
        forced_subject=forced_subject,
    )
    if forced_author or forced_subject:
        _emit(
            f"  [CLI override] author={forced_author!r} subject={forced_subject!r} "
            f"(HARD — bypasses heuristics)"
        )
    _emit(f"\n  entity_author:    {decision['entity_author']}")
    _emit(f"  entity_subject:   {decision['entity_subject']}")
    _emit(f"  cross_references: {decision['cross_references']}")
    _emit(f"  confidence:       {decision['confidence']}")
    _emit(f"  verdict:          {decision['verdict']}")
    _emit(f"  reasoning:        {decision['reasoning']}")

    # === STEP 3: decide destination ===
    _emit("\n[3/4] ROUTING DECISION")
    if decision["verdict"] == "BLOCK":
        _emit("  BLOCKED -- no entity discovered. Cannot route safely.")
        if not dry_run:
            _emit("  Recommendation: provide --author or --subject manually")
        return {
            "status": "blocked",
            "decision": decision,
            "destination": None,
        }

    destination_dir, reason = decide_destination(decision)
    destination_file = destination_dir / file_path.name
    sidecar_file = destination_dir / f"{file_path.name}.entity-discovery.json"

    try:
        rel_dest = destination_dir.relative_to(REPO)
    except ValueError:
        rel_dest = destination_dir
    _emit(f"  Destination:  {rel_dest}")
    _emit(f"  Reasoning:    {reason}")

    # === STEP 4: move file + write sidecar ===
    _emit("\n[4/4] MOVE FILE + WRITE SIDECAR (merged N1+N5)")
    word_count: int | None = None
    if dry_run:
        _emit(f"  [DRY-RUN] Would move:    {file_path} -> {destination_file}")
        _emit(f"  [DRY-RUN] Would sidecar: {sidecar_file}")
    else:
        destination_dir.mkdir(parents=True, exist_ok=True)
        # Copy (not move) to preserve original
        shutil.copy2(str(file_path), str(destination_file))
        _emit(f"  Copied: {file_path.name} -> {rel_dest}/")

        # G8 (2026-05-13): for video inputs, write a .transcript.txt sidecar
        # containing the Gemini-extracted transcript. batch_auto_creator's
        # BATCHABLE_EXTENSIONS includes .txt, so this sidecar is what enters
        # the chunk+embed pipeline (the .mp4 itself never gets chunked).
        # Filename pattern: ``{original_stem}.transcript.txt`` so it lives
        # next to the source and ``_load_sidecar_decision`` keeps its
        # ``<file>.entity-discovery.json`` contract intact.
        transcript_path: Path | None = None
        if is_video and gemini_result and isinstance(gemini_result.get("transcript"), str):
            tx = gemini_result["transcript"].strip()
            if tx:
                transcript_path = destination_dir / f"{file_path.stem}.transcript.txt"
                # Header mirrors what ingest_with_discovery already emits via
                # the canonical pipeline log so chunks pick up provenance.
                header_lines = [
                    f"# Transcript of {file_path.name}",
                    f"Source: local file ({file_path})",
                    f"Author: {decision.get('entity_author_display') or decision.get('entity_author') or 'unknown'}",
                    f"Subject: {decision.get('entity_subject_display') or decision.get('entity_subject') or 'unknown'}",
                    "Extracted via: gemini-2.5-flash (transcript_only)",
                    f"Extracted at: {datetime.now().isoformat()}",
                    "",
                ]
                transcript_path.write_text(
                    "\n".join(header_lines) + tx + "\n", encoding="utf-8"
                )
                _emit(f"  Transcript sidecar: {transcript_path.name} ({len(tx)} chars)")

        # Word count — honest by format (Onda 0, extraction-no-fallbacks).
        #
        # Binary documents (.pdf/.docx/.pptx...) MUST NOT be read as UTF-8:
        # doing so decodes the raw byte stream as garbage text and inflates the
        # word count by orders of magnitude (a Hormozi PDF produced 697,538
        # fabricated "words"). We instead derive the count from the SAME real
        # extractor the chunk pipeline uses (engine...extractors.extract_pdf /
        # extract_docx_raw). If extraction is unavailable (missing native dep,
        # corrupt file, image-only PDF with no selectable text), word_count
        # stays None — an explicit gap, never a fabricated number or a zero
        # presented as if measured.
        if not is_video:
            ext = destination_file.suffix.lower()
            # Binary formats whose raw bytes are NOT valid UTF-8 text.
            binary_doc_exts = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls"}
            if ext in binary_doc_exts:
                word_count = _word_count_from_binary_doc(destination_file, ext)
            else:
                # Plain-text formats (.txt/.md/.yaml/...) — real UTF-8 content.
                try:
                    txt = destination_file.read_text(encoding="utf-8", errors="ignore")
                    word_count = len(txt.split())
                except Exception:
                    word_count = None
        elif transcript_path is not None:
            # G8: count words on the transcript when the input is a video.
            try:
                word_count = len(transcript_path.read_text(encoding="utf-8").split())
            except Exception:
                word_count = None

        n5_payload = {
            "ingested_at": datetime.now().isoformat(),
            "original_path": str(file_path),
            "original_filename": file_path.name,
            "decision": decision,
            "destination": str(destination_file),
            "routing_reason": reason,
            # STORY-MCE-FOUNDER-ROUTING: top-level relationship_type for cheap
            # downstream access (collaborator | partner | negotiation | None).
            "relationship_type": decision.get("relationship_type"),
            "gemini_used": gemini_result is not None,
            "gemini_bypassed_reason": gemini_bypassed_reason,
            "transcript_sidecar": str(transcript_path) if transcript_path else None,
        }
        _write_merged_sidecar(sidecar_file, n5_payload)

    _emit("")
    _emit("=" * 72)
    _emit("SUMMARY")
    _emit("=" * 72)
    _emit(f"Status:       {'DRY-RUN' if dry_run else 'INGESTED'}")
    _emit(f"Author slug:  {decision['entity_author']}")
    _emit(f"Subject slug: {decision['entity_subject']}")
    _emit(f"Destination:  {rel_dest}")
    _emit(f"Verdict:      {decision['verdict']} ({decision['confidence']})")

    # === STEP 5 (optional): --process -> jarvis-chief (or legacy cmd_full) ===
    process_rc: int | None = None
    if process and not dry_run and decision["verdict"] != "BLOCK":
        if legacy_monolithic:
            # Rollback path — old monolithic behavior (--legacy-monolithic flag)
            process_rc = _maybe_run_process(destination_file)
        else:
            # New default — jarvis-chief orchestrated, chronicler-rendered (STORY-MCE-6.0)
            process_rc = _maybe_run_jarvis_chief(destination_file)

    # === STEP 6: INGEST REPORT tail (founder Trade-off #3) ===
    _emit_ingest_report(
        file_path=file_path,
        destination_dir=destination_dir,
        decision=decision,
        word_count=word_count,
        gemini_used=gemini_result is not None,
        gemini_bypassed_reason=gemini_bypassed_reason,
        process_flag=process,
    )

    return {
        "status": "dry-run" if dry_run else "ingested",
        "decision": decision,
        "destination": str(destination_file),
        "sidecar": str(sidecar_file),
        "gemini_used": gemini_result is not None,
        "gemini_bypassed_reason": gemini_bypassed_reason,
        "process_rc": process_rc,
    }


def ingest_youtube_url(
    url: str,
    *,
    dry_run: bool = False,
    skip_gemini: bool = False,
    process: bool = False,
    legacy_monolithic: bool = False,
    forced_author: str | None = None,
    forced_subject: str | None = None,
) -> dict:
    """Ingest a YouTube URL via Gemini native extraction (with local fallback).

    STORY-MCE-INGEST-URL (2026-05-19): restores URL parity lost in
    STORY-MCE-ROUND-TRIP refactor. The engine has YouTube-native extraction
    at engine/intelligence/pipeline/video/pipeline.py:259 — we call it
    directly so the operator never has to download via yt-dlp.

    STORY-MCE-YT-FALLBACK (2026-05-21): when Gemini cannot access the URL
    (PRIVATE/UNLISTED verdict, quota denied, API blocked, transient error),
    automatically falls back to yt-dlp + faster-whisper local transcription
    so a ``--skip-gemini`` opt-out is the ONLY way Gemini becomes a hard
    blocker. Gemini quota / project denials no longer trap the operator.

    Flow:
        1. Call extract_youtube_via_gemini(url) → gemini_result with title +
           transcript + speakers.
        1.5 (fallback). If gemini_result is None AND --skip-gemini was NOT
           set, call _youtube_fallback_download_transcribe(url) to get the
           same-shaped dict from yt-dlp metadata + faster-whisper local.
        2. Synthesize a filename from gemini_result["title"] slugified +
           ".youtube.mp4" suffix (drives entity discovery + is_video=True).
        3. infer_entities(synthetic_filename, gemini_result) → decision.
           Note: when fallback ran, ``speakers`` contains the uploader name
           so author detection still works.
        4. decide_destination(decision) → destination directory.
        5. Write transcript .txt to destination + sidecar v1.2.0 with
           source_url provenance + ``fallback_used`` flag.
        6. Optional --process → cmd_full on the .transcript.txt path.
    """
    _emit("=" * 72)
    _emit("INGEST WITH ENTITY DISCOVERY -- /ingest slash orchestrator (URL mode)")
    _emit("=" * 72)
    _emit(f"Mode:    {'DRY-RUN' if dry_run else 'EXECUTE'}")
    _emit(f"URL:     {url}")

    # === STORY-MCE-7.0 AC-3 (URL mode): transcript-exists early exit ===
    # Before calling Gemini (expensive), scan all known inbox/ dirs for a
    # sidecar whose source_url matches this URL. If found, the transcript
    # already exists from a prior run — skip Gemini + all downloads, go
    # straight to --process (which will exit in <2s via processed-sources
    # registry check in cmd_ingest).
    # Fail-open: any exception falls through to normal flow.
    if not dry_run:
        try:
            _source_url_hit: Path | None = None
            _sidecar_glob_roots = [
                REPO / "knowledge" / "external" / "inbox",
                REPO / "knowledge" / "business" / "inbox",
                REPO / "knowledge" / "external" / "processed",
                REPO / "knowledge" / "business" / "processed",
            ]
            for _sg_root in _sidecar_glob_roots:
                if not _sg_root.exists():
                    continue
                for _sc in _sg_root.rglob("*.entity-discovery.json"):
                    try:
                        _sc_data = json.loads(_sc.read_text(encoding="utf-8"))
                        _sc_url = _sc_data.get("source_url") or _sc_data.get("n5", {}).get("source_url")
                        if _sc_url == url:
                            # Found matching sidecar — check if transcript exists
                            _tx_hint = _sc_data.get("transcript_sidecar") or _sc_data.get("destination")
                            if _tx_hint and Path(_tx_hint).exists():
                                _source_url_hit = Path(_tx_hint)
                                break
                    except Exception:
                        continue
                if _source_url_hit:
                    break

            if _source_url_hit is not None:
                _emit("\n[MCE-7.0 AC-3] EARLY EXIT — URL already ingested")
                _emit(f"  Transcript: {_source_url_hit}")
                _emit("  Skipping Gemini extraction and transcript download.")
                if process and not dry_run:
                    _emit("\n[--process] Firing jarvis-chief on existing transcript (idempotent)...")
                    _slug_hit = _source_url_hit.parent.name
                    _cmd_hit = [
                        sys.executable, "-u", "-m",
                        "engine.intelligence.pipeline.jarvis_chief",
                        "orchestrate", _slug_hit,
                    ]
                    import subprocess as _sp_hit
                    _rc_hit = _sp_hit.call(_cmd_hit, cwd=str(REPO))
                    _emit(f"  jarvis-chief returned rc={_rc_hit}")
                return {
                    "status": "already_ingested",
                    "source_url": url,
                    "transcript": str(_source_url_hit),
                    "process_rc": _rc_hit if process and not dry_run else None,
                    "mce_7_0_ac3": True,
                }
        except Exception as _ac3_url_exc:
            _emit(f"  [MCE-7.0 AC-3] early-exit check failed (non-fatal): {_ac3_url_exc}")

    # === STEP 1: Gemini native YouTube extraction ===
    gemini_result: dict | None = None
    gemini_bypassed_reason: str | None = None

    if skip_gemini:
        gemini_bypassed_reason = "--skip-gemini incompatible with URL ingest"
        _emit("\n[1/4] YOUTUBE GEMINI EXTRACT")
        _emit(f"[pre_07] BYPASSED (reason: {gemini_bypassed_reason})")
        _emit(
            "  [warn] URL ingest requires Gemini to obtain transcript+title. "
            "Without it routing degrades to BLOCK (no person/company tokens "
            "in raw URL)."
        )
    elif not os.environ.get("GEMINI_API_KEY"):
        gemini_bypassed_reason = "GEMINI_API_KEY absent"
        _emit("\n[1/4] YOUTUBE GEMINI EXTRACT")
        _emit(f"[pre_07] BYPASSED (reason: {gemini_bypassed_reason})")
    elif dry_run:
        # Dry-run still needs at least filename evidence — we skip Gemini and
        # fall through to URL-as-filename heuristic so operator sees the
        # routing math without spending quota.
        gemini_bypassed_reason = "dry-run (Gemini skipped)"
        _emit("\n[1/4] YOUTUBE GEMINI EXTRACT")
        _emit(f"[pre_07] BYPASSED (reason: {gemini_bypassed_reason})")
    else:
        _emit("\n[1/4] YOUTUBE GEMINI EXTRACT")
        try:
            from engine.intelligence.pipeline.video.pipeline import (
                extract_youtube_via_gemini,
            )

            _emit(f"  Calling Gemini on {url}...")
            gemini_result = extract_youtube_via_gemini(url)
            if gemini_result:
                tx = gemini_result.get("transcript")
                title = gemini_result.get("title", "")
                speakers = gemini_result.get("speakers", []) or []
                _emit(f"  Title:            {title}")
                _emit(
                    "  Speakers:         "
                    f"{', '.join(s.get('name', '?') for s in speakers) or '(none)'}"
                )
                if tx and isinstance(tx, str):
                    _emit(f"  Transcript chars: {len(tx)}")
                else:
                    _emit("  Transcript:       (none — Gemini omitted)")
            else:
                _emit("  [warn] Gemini returned None -- proceeding with URL only")
                gemini_bypassed_reason = "gemini returned None"
        except Exception as e:
            _emit(
                f"  [warn] Gemini call failed "
                f"({type(e).__name__}: {str(e)[:100]}) -- URL only"
            )
            gemini_result = None
            gemini_bypassed_reason = f"exception: {type(e).__name__}"

    # === STEP 1.5 (NEW): TIERED YouTube fallback chain ====================
    # Trigger when Gemini did not produce a USEFUL transcript (None OR no
    # title AND no speakers) AND operator did not opt out via --skip-gemini
    # AND we're not in a dry-run.
    #
    # The "useful" check is critical: Gemini sometimes returns raw text (no
    # title, no speakers) when JSON parsing fails. Without title/speakers
    # the routing CANNOT identify the author and falls to BLOCK. So we
    # treat that as "needs fallback" — even though gemini_result exists,
    # it's useless for entity discovery.
    #
    # Tier 1 (default, ~3s): YouTube auto-captions via yt-dlp.
    #   Resolves 90% of cases. Quality "good enough" for the cmd_full pipeline.
    #   Routing is locked by uploader name (channel), not by transcript words —
    #   so transcript artifacts like "Hormozi → Trazosi" do NOT bleed into the
    #   bucket decision (see _youtube_fetch_captions speakers contract).
    #
    # Tier 2 (premium, ~8min): yt-dlp audio + faster-whisper local.
    #   Fires only if captions are unavailable / parse-failed. Higher quality
    #   on proper nouns; same uploader-locked routing.
    gemini_useful_for_routing = bool(
        gemini_result
        and isinstance(gemini_result, dict)
        and (gemini_result.get("title") or gemini_result.get("speakers"))
    )
    if gemini_result is not None and not gemini_useful_for_routing:
        _emit(
            "  [info] Gemini returned content but WITHOUT title/speakers "
            "-- treating as degraded, triggering fallback chain"
        )
        gemini_bypassed_reason = (
            gemini_bypassed_reason or "gemini returned content sans title/speakers"
        )

    if (
        not gemini_useful_for_routing
        and not dry_run
        and not skip_gemini
    ):
        # --- Tier 1: captions -------------------------------------------------
        cap = _youtube_fetch_captions(url)
        if cap is not None:
            gemini_result = cap
            prev_reason = gemini_bypassed_reason or "gemini unavailable"
            gemini_bypassed_reason = (
                f"{prev_reason} -- TIER 1 captions succeeded"
            )
            _emit(
                "  [info] TIER 1 SUCCEEDED -- pipeline will continue with "
                "YouTube auto-captions (uploader-locked routing)"
            )
        else:
            # --- Tier 2: whisper local --------------------------------------
            _emit(
                "  [info] TIER 1 FAILED -- escalating to TIER 2 "
                "(yt-dlp + faster-whisper, ~8min for ~36min video)"
            )
            wh = _youtube_fallback_download_transcribe(url)
            if wh is not None:
                gemini_result = wh
                prev_reason = gemini_bypassed_reason or "gemini unavailable"
                gemini_bypassed_reason = (
                    f"{prev_reason} -- TIER 1 captions failed, "
                    "TIER 2 whisper succeeded"
                )
                _emit(
                    "  [info] TIER 2 SUCCEEDED -- continuing with locally-"
                    "transcribed content (uploader-locked routing)"
                )
            else:
                _emit(
                    "  [info] BOTH TIERS FAILED -- continuing with URL-only "
                    "evidence (routing will likely BLOCK)"
                )

    # === STEP 2: synthesize filename + entity discovery ===
    _emit("\n[2/4] ENTITY DISCOVERY (pre_08)")
    # Build a filename from title (if Gemini gave one) else from URL tail.
    if gemini_result and gemini_result.get("title"):
        title = gemini_result["title"]
        # Keep the human-readable title intact for parse_filename_evidence —
        # it has regex patterns that match "Author Name" style strings.
        synthetic_filename = f"{title}.youtube.mp4"
    else:
        # Fallback: use URL tail (video ID) — yields BLOCK for entity discovery
        # but at least preserves audit trail.
        tail = url.rstrip("/").split("/")[-1].split("?")[0]
        synthetic_filename = f"{tail}.youtube.mp4"

    _emit(f"  Synthetic filename: {synthetic_filename}")

    from engine.intelligence.pipeline.batch_auto_creator import (
        infer_entities,
        parse_filename_evidence,
    )

    fn_ev = parse_filename_evidence(synthetic_filename)
    _emit(f"  Filename persons:   {fn_ev['persons']}")
    _emit(f"  Filename companies: {fn_ev['companies']}")

    decision = infer_entities(
        synthetic_filename,
        gemini_result=gemini_result,
        forced_author=forced_author,
        forced_subject=forced_subject,
    )
    if forced_author or forced_subject:
        _emit(
            f"  [CLI override] author={forced_author!r} subject={forced_subject!r} "
            f"(HARD — bypasses heuristics)"
        )
    _emit(f"\n  entity_author:    {decision['entity_author']}")
    _emit(f"  entity_subject:   {decision['entity_subject']}")
    _emit(f"  cross_references: {decision['cross_references']}")
    _emit(f"  confidence:       {decision['confidence']}")
    _emit(f"  verdict:          {decision['verdict']}")
    _emit(f"  reasoning:        {decision['reasoning']}")

    # === STEP 3: routing ===
    _emit("\n[3/4] ROUTING DECISION")
    if decision["verdict"] == "BLOCK":
        _emit("  BLOCKED -- no entity discovered. Cannot route safely.")
        if skip_gemini or gemini_bypassed_reason:
            _emit(
                "  Hint: URL ingest without Gemini cannot extract speakers. "
                "Remove --skip-gemini and ensure GEMINI_API_KEY is set."
            )
        return {
            "status": "blocked",
            "decision": decision,
            "destination": None,
        }

    destination_dir, reason = decide_destination(decision)
    title_slug = slugify(
        (gemini_result or {}).get("title")
        or synthetic_filename.replace(".youtube.mp4", "")
    )
    transcript_filename = f"{title_slug}.transcript.txt"
    transcript_path = destination_dir / transcript_filename
    sidecar_file = destination_dir / f"{title_slug}.youtube.entity-discovery.json"

    try:
        rel_dest = destination_dir.relative_to(REPO)
    except ValueError:
        rel_dest = destination_dir
    _emit(f"  Destination:  {rel_dest}")
    _emit(f"  Reasoning:    {reason}")

    # === STEP 4: write transcript + sidecar ===
    _emit("\n[4/4] WRITE TRANSCRIPT + SIDECAR (URL mode, schema v1.2.0)")
    word_count: int | None = None
    if dry_run:
        _emit(f"  [DRY-RUN] Would write transcript: {transcript_path}")
        _emit(f"  [DRY-RUN] Would write sidecar:    {sidecar_file}")
    else:
        destination_dir.mkdir(parents=True, exist_ok=True)

        tx = (gemini_result or {}).get("transcript") if gemini_result else None
        used_fallback = bool((gemini_result or {}).get("_fallback"))
        fallback_source = (gemini_result or {}).get("_fallback_source")
        if isinstance(tx, str) and tx.strip():
            tx = tx.strip()
            if fallback_source == "youtube-captions":
                extractor = "yt-dlp --write-auto-subs (YouTube captions)"
            elif fallback_source == "yt-dlp+faster-whisper":
                extractor = (
                    f"yt-dlp + faster-whisper "
                    f"({(gemini_result or {}).get('_fallback_model', 'base')})"
                )
            else:
                extractor = "gemini-2.5-flash (extract_youtube_via_gemini)"
            header_lines = [
                f"# Transcript of {(gemini_result or {}).get('title') or 'untitled'}",
                f"Source: youtube ({url})",
                f"Author: {decision.get('entity_author_display') or decision.get('entity_author') or 'unknown'}",
                f"Subject: {decision.get('entity_subject_display') or decision.get('entity_subject') or 'unknown'}",
                f"Extracted via: {extractor}",
                f"Extracted at: {datetime.now().isoformat()}",
                "",
            ]
            transcript_path.write_text(
                "\n".join(header_lines) + tx + "\n", encoding="utf-8"
            )
            word_count = len(tx.split())
            _emit(
                f"  Transcript: {transcript_path.relative_to(REPO)} "
                f"({len(tx)} chars, {word_count} words)"
            )
        else:
            _emit("  [warn] No transcript available — only sidecar will be written")

        # Channel lock: if the resolved author slug matches an existing
        # external agent dir AND we have an uploader from yt-dlp, mark the
        # routing as "channel-locked" — this is the strongest audit signal
        # that the cascade landed in the right bucket (uploader is API truth).
        author_slug = decision.get("entity_author")
        uploader = (gemini_result or {}).get("_uploader")
        channel_locked = False
        if author_slug and uploader:
            agent_dir = REPO / "agents" / "external" / author_slug
            if agent_dir.is_dir():
                channel_locked = True

        # Honest extractor label for the sidecar (mirrors transcript header).
        if fallback_source == "youtube-captions":
            extractor_label = "yt-dlp+youtube-captions"
        elif fallback_source == "yt-dlp+faster-whisper":
            model = (gemini_result or {}).get("_fallback_model", "base")
            extractor_label = f"yt-dlp+faster-whisper ({model})"
        elif gemini_result is not None:
            extractor_label = "gemini-2.5-flash"
        else:
            extractor_label = None

        n5_payload = {
            "schema_version": "1.2.0",
            "source_kind": "youtube_url",
            "source_url": url,
            "ingested_at": datetime.now().isoformat(),
            "original_filename": synthetic_filename,
            "decision": decision,
            "destination": str(transcript_path),
            "routing_reason": reason,
            "relationship_type": decision.get("relationship_type"),
            # Honest: gemini_used==True only when Gemini actually produced
            # the transcript. Fallback paths set False; the real extractor
            # is surfaced in transcript_extracted_via.
            "gemini_used": bool(gemini_result is not None and not used_fallback),
            "transcript_extracted_via": extractor_label,
            "fallback_used": used_fallback,
            "fallback_source": fallback_source,
            "channel_uploader": uploader,
            "routing_locked_by_channel": channel_locked,
            "gemini_bypassed_reason": gemini_bypassed_reason,
            "transcript_sidecar": str(transcript_path)
            if isinstance(tx, str) and tx.strip()
            else None,
            "gemini_title": (gemini_result or {}).get("title"),
            "gemini_speakers": [
                {
                    "name": s.get("name"),
                    "confidence": s.get("confidence"),
                }
                for s in ((gemini_result or {}).get("speakers") or [])
            ]
            if gemini_result
            else [],
        }
        _write_merged_sidecar(sidecar_file, n5_payload)

    # === SUMMARY ===
    _emit("")
    _emit("=" * 72)
    _emit("SUMMARY")
    _emit("=" * 72)
    _emit(f"Status:       {'DRY-RUN' if dry_run else 'INGESTED'}")
    _emit(f"Author slug:  {decision['entity_author']}")
    _emit(f"Subject slug: {decision['entity_subject']}")
    _emit(f"Destination:  {rel_dest}")
    _emit(f"Verdict:      {decision['verdict']} ({decision['confidence']})")
    # Channel lock audit line (CRITICAL trust signal for cascade routing)
    _uploader_dbg = (gemini_result or {}).get("_uploader") if gemini_result else None
    if not dry_run and decision.get("entity_author") and _uploader_dbg:
        _agent_dir = REPO / "agents" / "external" / decision["entity_author"]
        _channel_locked = _agent_dir.is_dir()
        _emit(
            f"Channel:      {_uploader_dbg} "
            f"{'🔒 LOCKED (agent dir exists)' if _channel_locked else '⚠️ unlocked (no agent dir)'}"
        )
    _src_dbg = (gemini_result or {}).get("_fallback_source") if gemini_result else None
    if _src_dbg:
        _emit(f"Source:       {_src_dbg} (fallback)")
    elif gemini_result is not None:
        _emit("Source:       gemini-2.5-flash")

    # === STEP 5 (optional): --process → jarvis-chief (or legacy cmd_full) on transcript ===
    process_rc: int | None = None
    if process and not dry_run and decision["verdict"] != "BLOCK":
        if transcript_path.exists():
            if legacy_monolithic:
                # Rollback path — old monolithic behavior (--legacy-monolithic flag)
                process_rc = _maybe_run_process(transcript_path)
            else:
                # New default — jarvis-chief orchestrated, chronicler-rendered (STORY-MCE-6.0)
                process_rc = _maybe_run_jarvis_chief(transcript_path)
        else:
            _emit(
                "\n[--process] skipped: transcript file does not exist "
                "(Gemini did not return transcript). Cannot fire pipeline."
            )
            process_rc = 1

    # === STEP 6: INGEST REPORT tail ===
    # Build a synthetic Path so _emit_ingest_report has the right shape.
    synthetic_path = Path(synthetic_filename)
    _emit_ingest_report(
        file_path=synthetic_path,
        destination_dir=destination_dir,
        decision=decision,
        word_count=word_count,
        gemini_used=gemini_result is not None,
        gemini_bypassed_reason=gemini_bypassed_reason,
        process_flag=process,
    )

    return {
        "status": "dry-run" if dry_run else "ingested",
        "decision": decision,
        "destination": str(transcript_path),
        "sidecar": str(sidecar_file),
        "gemini_used": gemini_result is not None,
        "gemini_bypassed_reason": gemini_bypassed_reason,
        "process_rc": process_rc,
        "source_kind": "youtube_url",
        "source_url": url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_path", help="Path to file OR YouTube URL to ingest")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument(
        "--skip-gemini",
        action="store_true",
        help="Filename evidence only (no LLM call)",
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="After move + sidecar, invoke jarvis-chief orchestrate <slug> (phase-by-phase render)",
    )
    parser.add_argument(
        "--legacy-monolithic",
        action="store_true",
        help=(
            "With --process: skip jarvis-chief, use old orchestrate.cmd_full monolithic path "
            "(rollback — STORY-MCE-6.0 Phase 8a)"
        ),
    )
    parser.add_argument(
        "--author",
        default=None,
        help=(
            "HARD override: force the author/expert (e.g. 'Alex Hormozi'). "
            "Highest precedence — bypasses filename/Gemini heuristics and routes "
            "to external/<author-slug>/. STORY-ONDA1-author-routing."
        ),
    )
    parser.add_argument(
        "--subject",
        default=None,
        help=(
            "HARD override: force the subject (e.g. a company/topic). "
            "Highest precedence, same semantics as --author."
        ),
    )
    args = parser.parse_args()

    # STORY-MCE-INGEST-URL (2026-05-19): URL branch BEFORE file existence check
    if _is_youtube_url(args.file_path):
        result = ingest_youtube_url(
            args.file_path,
            dry_run=args.dry_run,
            skip_gemini=args.skip_gemini,
            process=args.process,
            legacy_monolithic=args.legacy_monolithic,
            forced_author=args.author,
            forced_subject=args.subject,
        )
        return 0 if result["status"] in ("ingested", "dry-run") else 1

    file_path = Path(args.file_path).resolve()
    if not file_path.exists():
        _emit(f"[error] File not found: {file_path}")
        return 1

    result = ingest_with_discovery(
        file_path,
        dry_run=args.dry_run,
        skip_gemini=args.skip_gemini,
        process=args.process,
        legacy_monolithic=args.legacy_monolithic,
        forced_author=args.author,
        forced_subject=args.subject,
    )
    return 0 if result["status"] in ("ingested", "dry-run") else 1


if __name__ == "__main__":
    sys.exit(main())
