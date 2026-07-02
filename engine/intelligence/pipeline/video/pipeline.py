"""Video processing pipeline for Mega Brain.

Extracts text from video sources (YouTube, local files) through:
1. PRIMARY: Gemini native YouTube ingestion (audio + visual, no download)
2. FALLBACK 1: youtube-transcript-api (legacy)
3. FALLBACK 2: yt-dlp metadata + Whisper local transcription
4. OCR from key frames (pytesseract)

GEMINI-YT-WIRE (2026-05-12): Added extract_youtube_via_gemini() as primary
path. Google processes from their servers — no local IP block, supports
public videos natively. Private videos return 403 (user must download).

Heavy dependencies are optional -- each component degrades gracefully.
"""

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# GEMINI FILES API — TIMEOUT / RETRY / STRUCTURED LOGGING  (V4 — 2026-05-13)
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY: `extract_local_video_via_gemini` previously hung indefinitely on large
# files (Parte #1, 114MB, stuck 25min, killed manually). The original loop
# polled every 5s for at most 300s but had:
#   - no absolute upload->ACTIVE timeout (could loop forever on a non-ACTIVE
#     state that wasn't PROCESSING, e.g. STILL_UPLOADING)
#   - no retry on transient network errors (502, 504, ECONNRESET, ReadTimeout)
#   - no fail-fast on permanent errors (401, 403, 404)
#   - no structured logging (operator was blind, just an `info()` per poll)
#
# This module exposes:
#   - GeminiTimeoutError / GeminiPermanentError typed exceptions
#   - _upload_with_retry()  — retry-aware upload + poll-to-ACTIVE
#   - _log_gemini_event()  — appends jsonl line to .data/logs/gemini-files-api.jsonl
#
# Env knobs (all optional):
#   MCE_GEMINI_MAX_POLLS         (default 120)
#   MCE_GEMINI_POLL_INTERVAL_S   (default 5)
#   MCE_GEMINI_TIMEOUT_S         (default 600)  absolute upload->ACTIVE budget
#   MCE_GEMINI_MAX_RETRIES       (default 3)
# ─────────────────────────────────────────────────────────────────────────────


class GeminiTimeoutError(RuntimeError):
    """Raised when Gemini Files API upload exceeds MCE_GEMINI_TIMEOUT_S."""


class GeminiPermanentError(RuntimeError):
    """Raised on 401 / 403 / 404 — never retried."""


_TRANSIENT_TOKENS = (
    "502",
    "503",
    "504",
    "econnreset",
    "readtimeout",
    "read timeout",
    "connection aborted",
    "connection reset",
    "timed out",
    "temporarily unavailable",
)
_PERMANENT_TOKENS = ("401", "403", "404", "permission_denied", "not_found")


def _is_transient_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(tok in msg for tok in _TRANSIENT_TOKENS)


def _is_permanent_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(tok in msg for tok in _PERMANENT_TOKENS)


def _gemini_log_path() -> Path:
    """Resolve jsonl log path. Lives at <root>/.data/logs/gemini-files-api.jsonl.

    Resilient to environments where engine.paths is unavailable (we don't want
    to add a hard import dependency at module load — pipeline.py is imported
    by lightweight CLI shims that may not have engine.paths reachable).
    """
    try:
        from engine.paths import LOGS  # type: ignore

        return Path(LOGS) / "gemini-files-api.jsonl"
    except Exception:
        return Path(__file__).resolve().parents[4] / ".data" / "logs" / "gemini-files-api.jsonl"


def _log_gemini_event(payload: dict) -> None:
    """Append a single jsonl line to gemini-files-api.jsonl. Never raises."""
    try:
        path = _gemini_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"ts": datetime.now(UTC).isoformat(), **payload}
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Logging must NEVER break the pipeline.
        pass


def _upload_with_retry(client, fpath: Path, logger):
    """Upload local file to Gemini Files API and wait for ACTIVE state.

    Implements:
      - exponential backoff on transient errors (5s/15s/45s)
      - fail-fast on permanent errors (401/403/404)
      - absolute timeout (default 600s) raises GeminiTimeoutError
      - structured jsonl per poll under .data/logs/gemini-files-api.jsonl

    Returns the ACTIVE uploaded_file. Raises GeminiTimeoutError /
    GeminiPermanentError on failure. Other transient failures bubble up after
    retry budget exhausted.
    """
    max_polls = int(os.environ.get("MCE_GEMINI_MAX_POLLS", "120"))
    poll_interval = float(os.environ.get("MCE_GEMINI_POLL_INTERVAL_S", "5"))
    timeout_s = float(os.environ.get("MCE_GEMINI_TIMEOUT_S", "600"))
    max_retries = int(os.environ.get("MCE_GEMINI_MAX_RETRIES", "3"))

    started_at = time.time()
    delays = [5.0, 15.0, 45.0]

    # --- Upload (with retry) ---
    last_exc: Exception | None = None
    uploaded_file = None
    for attempt in range(1, max_retries + 1):
        try:
            uploaded_file = client.files.upload(file=str(fpath))
            _log_gemini_event(
                {
                    "event": "upload_ok",
                    "file": str(fpath),
                    "attempt": attempt,
                    "state": getattr(uploaded_file.state, "name", "UNKNOWN"),
                }
            )
            break
        except Exception as exc:
            last_exc = exc
            if _is_permanent_error(exc):
                _log_gemini_event(
                    {
                        "event": "upload_permanent_error",
                        "file": str(fpath),
                        "attempt": attempt,
                        "error": str(exc)[:300],
                    }
                )
                raise GeminiPermanentError(
                    f"Gemini upload permanent failure for {fpath.name}: {exc}"
                ) from exc
            if attempt >= max_retries or not _is_transient_error(exc):
                _log_gemini_event(
                    {
                        "event": "upload_failed",
                        "file": str(fpath),
                        "attempt": attempt,
                        "error": str(exc)[:300],
                    }
                )
                raise
            delay = delays[min(attempt - 1, len(delays) - 1)]
            logger.warning(
                f"Gemini upload attempt {attempt}/{max_retries} failed "
                f"({type(exc).__name__}: {str(exc)[:120]}) — retry in {delay}s"
            )
            _log_gemini_event(
                {
                    "event": "upload_retry",
                    "file": str(fpath),
                    "attempt": attempt,
                    "delay_s": delay,
                    "error": str(exc)[:300],
                }
            )
            time.sleep(delay)

    if uploaded_file is None:
        # Defensive — should be unreachable.
        raise GeminiTimeoutError(
            f"Gemini upload returned no file handle for {fpath.name}: {last_exc}"
        )

    # --- Poll to ACTIVE (with absolute timeout) ---
    poll_count = 0
    while True:
        state_name = getattr(uploaded_file.state, "name", "UNKNOWN")
        elapsed = time.time() - started_at
        _log_gemini_event(
            {
                "event": "poll",
                "file": str(fpath),
                "state": state_name,
                "elapsed_s": round(elapsed, 1),
                "poll_count": poll_count,
            }
        )
        if state_name == "ACTIVE":
            return uploaded_file
        if state_name == "FAILED":
            raise GeminiPermanentError(
                f"Gemini reported FAILED state for {fpath.name} after {elapsed:.0f}s"
            )
        if elapsed > timeout_s or poll_count > max_polls:
            _log_gemini_event(
                {
                    "event": "poll_timeout",
                    "file": str(fpath),
                    "state": state_name,
                    "elapsed_s": round(elapsed, 1),
                    "poll_count": poll_count,
                    "timeout_s": timeout_s,
                }
            )
            raise GeminiTimeoutError(
                f"Gemini Files API timeout for {fpath.name}: state={state_name} "
                f"after {elapsed:.0f}s ({poll_count} polls)"
            )
        time.sleep(poll_interval)
        poll_count += 1
        try:
            uploaded_file = client.files.get(name=uploaded_file.name)
        except Exception as exc:
            if _is_permanent_error(exc):
                raise GeminiPermanentError(
                    f"Gemini files.get permanent error for {fpath.name}: {exc}"
                ) from exc
            # transient: log and continue polling within timeout budget
            _log_gemini_event(
                {
                    "event": "poll_transient_error",
                    "file": str(fpath),
                    "error": str(exc)[:300],
                    "poll_count": poll_count,
                }
            )


@dataclass
class VideoResult:
    """Result of video processing."""

    source: str  # URL or file path
    transcript: str  # Full transcript text
    ocr_texts: list[str] = field(default_factory=list)  # Text from frames
    metadata: dict = field(default_factory=dict)  # title, duration, etc.
    output_path: Path | None = None


def extract_youtube_via_gemini(
    url: str,
    model: str = "gemini-2.5-flash",
    include_visual: bool = True,
) -> dict | None:
    """Extract transcript + visual description from YouTube via Gemini native ingestion.

    Google processes the video from THEIR servers — bypasses local IP blocks
    that affect yt-dlp / youtube-transcript-api. Supports public AND unlisted
    videos. Private videos return 403 PERMISSION_DENIED (user must download).

    Args:
        url: YouTube URL (youtu.be or youtube.com/watch).
        model: Gemini model. Default 'gemini-2.5-flash' (~$0.10-0.30/hour).
        include_visual: If True, also extract visual descriptions (slides, UI,
            screen content). Costs slightly more but essential for screen-share
            videos like demos and presentations.

    Returns:
        dict with keys: {transcript, visual_description, summary, raw} OR None
        on failure. Caller should check return value AND log.error output to
        distinguish "video private" vs "API error" vs "no key".
    """
    import logging

    logger = logging.getLogger("pipeline.video.gemini")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # Try loading from .env
        env_path = Path(__file__).resolve().parents[4] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ["GEMINI_API_KEY"] = api_key
                    break
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — cannot use Gemini YouTube path")
            return None

    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        logger.warning(f"google.genai not installed: {e}")
        return None

    client = genai.Client(api_key=api_key)

    # Single multimodal prompt v2 (2026-05-12): SPEAKER VISUAL GATE
    # Reinforced identification of speakers via VISUAL (intro cards, lower-thirds,
    # slides, credits) + TEXTUAL (auto-introductions in transcript). Plus entity
    # discovery (organizations, brands). Same call, more fields, zero extra cost.
    prompt_text = (
        "Extraia o seguinte deste vídeo em formato JSON estrito:\n"
        "{\n"
        '  "title": "<título do vídeo>",\n'
        '  "duration_estimate": "<duração em mm:ss>",\n'
        '  "language": "<idioma detectado, ex: pt-BR>",\n'
        '  "speakers": [\n'
        "    {\n"
        '      "name": "<nome completo OU \\"SPEAKER_UNKNOWN_1\\" se não conseguir identificar>",\n'
        '      "evidence": "visual_intro_card|visual_lower_third|visual_slide|visual_credits|audio_self_introduction|audio_mentioned_by_other|inferred_from_context",\n'
        '      "title": "<cargo/título profissional se visível, ex: Founder, CEO>",\n'
        '      "affiliation": "<empresa/marca a que pertence>",\n'
        '      "time_first_appearance": "<mm:ss quando primeiro identificado>",\n'
        '      "confidence": "high|medium|low"\n'
        "    }\n"
        "  ],\n"
        '  "entities_mentioned": [\n'
        "    {\n"
        '      "name": "<nome da empresa/marca/produto>",\n'
        '      "type": "company|product|methodology|person|other",\n'
        '      "mention_count": <quantas vezes apareceu>,\n'
        '      "is_subject": true,  # Object: é o ASSUNTO PRINCIPAL do vídeo?\n'
        '      "evidence_examples": ["<frase ou texto onde apareceu>"]\n'
        "    }\n"
        "  ],\n"
        '  "transcript": "<transcrição literal completa, com [time-mm:ss] no início de cada parágrafo importante>",\n'
        '  "visual_description": "<o que aparece em tela: slides, UI, demos, dashboards, diagramas — cronológico>",\n'
        '  "key_moments": [\n'
        '    {"time": "mm:ss", "type": "slide|demo|claim|cta", "description": "<o que acontece>"}\n'
        "  ],\n"
        '  "summary": "<resumo executivo em 3-5 frases>"\n'
        "}\n\n"
        "REGRAS DE IDENTIFICAÇÃO (NÃO-NEGOCIÁVEIS):\n"
        "1. SPEAKERS: examine SEMPRE o vídeo VISUAL e o áudio. Procure por:\n"
        "   - Intro card / título de abertura com nome do apresentador\n"
        "   - Lower-third (banner inferior com nome + cargo)\n"
        "   - Slide de apresentação 'About me' / 'Quem sou eu'\n"
        "   - Créditos finais\n"
        "   - Auto-introdução no áudio ('meu nome é X', 'aqui é o X')\n"
        "   - Menção do nome por outro speaker\n"
        "   Se NÃO conseguir identificar nominalmente, retorne 'SPEAKER_UNKNOWN_1' e\n"
        "   descreva o que VIU (descrição física, posição na tela) em 'evidence'.\n"
        "2. ENTITIES: liste TODAS as empresas/produtos/metodologias mencionadas.\n"
        "   Marque is_subject=true para a entidade que é o ASSUNTO PRINCIPAL\n"
        "   (mais menções + claims construídos em torno dela).\n"
        "3. transcript = TUDO falado, literal, sem omissões\n"
        "4. visual_description = TUDO mostrado em tela, mesmo sem áudio\n"
        "5. key_moments = ≥5 momentos chave\n"
        "6. JSON válido, parseável, sem markdown blocks.\n"
    )
    if not include_visual:
        prompt_text = prompt_text.replace(
            '"visual_description": "<o que aparece em tela ao longo do vídeo: slides, UI, demos, dashboards, diagramas — descrição cronológica>",',
            '"visual_description": null,',
        )

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    parts=[
                        types.Part(file_data=types.FileData(file_uri=url)),
                        types.Part(text=prompt_text),
                    ]
                )
            ],
        )
        raw_text = response.text
        # Try to parse JSON (may be wrapped in markdown fence)
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: return raw text under transcript key
            logger.warning(
                f"Gemini response not pure JSON, returning raw text ({len(raw_text)} chars)"
            )
            return {
                "transcript": raw_text,
                "visual_description": None,
                "summary": None,
                "raw": raw_text,
                "parse_error": True,
            }

        return {
            "transcript": parsed.get("transcript", ""),
            "visual_description": parsed.get("visual_description"),
            "summary": parsed.get("summary"),
            "title": parsed.get("title"),
            "duration_estimate": parsed.get("duration_estimate"),
            "language": parsed.get("language"),
            "speakers": parsed.get("speakers", []),
            "key_moments": parsed.get("key_moments", []),
            "raw": raw_text,
        }
    except Exception as e:
        err_str = str(e)
        if "403" in err_str or "PERMISSION_DENIED" in err_str:
            logger.error(f"Video PRIVATE/UNLISTED — Gemini cannot access: {url}")
        elif "404" in err_str or "NOT_FOUND" in err_str:
            logger.error(f"Video NOT FOUND: {url}")
        else:
            logger.error(
                f"Gemini YouTube fetch failed for {url}: {type(e).__name__}: {err_str[:200]}"
            )
        return None


def _identification_response_schema() -> dict:
    """JSON schema for Gemini structured output — Speaker + Entity identification ONLY.

    Speaker Visual Gate (2026-05-12): keep response SMALL (only identification,
    no transcript) to avoid JSON parse failures on 200k+ char responses.
    Transcript is fetched in a SEPARATE call (extract_transcript_only) so
    each call has a bounded response size.
    """
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "duration_estimate": {"type": "string"},
            "language": {"type": "string"},
            "speakers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "evidence": {"type": "string"},
                        "title": {"type": "string"},
                        "affiliation": {"type": "string"},
                        "time_first_appearance": {"type": "string"},
                        "confidence": {"type": "string"},
                    },
                    "required": ["name", "evidence", "confidence"],
                },
            },
            "entities_mentioned": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "mention_count": {"type": "integer"},
                        "is_subject": {"type": "boolean"},
                        "evidence_examples": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["name", "type", "is_subject"],
                },
            },
            "summary": {"type": "string"},
            "key_moments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "type": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
        },
        "required": ["speakers", "entities_mentioned", "summary"],
    }


def extract_local_video_via_gemini(
    file_path: str | Path,
    model: str = "gemini-2.5-flash",
    include_transcript: bool = False,
) -> dict | None:
    """Extract speakers + entities + summary from LOCAL video file via Gemini.

    Speaker Visual Gate (2026-05-12): mirrors extract_youtube_via_gemini but uploads
    the local file via Gemini Files API. Uses response_schema for STRUCTURED output
    that guarantees valid JSON.

    IMPORTANT: by default does NOT extract full transcript (would make response
    too large and break JSON parse). Call extract_transcript_only() separately
    if you need the transcript text.

    Args:
        file_path: Absolute path to local video file (.mp4, .mov, .webm, etc).
        model: Gemini model. Default 'gemini-2.5-flash'.
        include_transcript: If True, include transcript field (NOT recommended
            for videos >10min — use extract_transcript_only instead).

    Returns:
        Dict with: speakers[], entities_mentioned[], summary, title, key_moments[].
        Plus 'transcript' if include_transcript=True. Returns None on failure.
    """
    import logging

    logger = logging.getLogger("pipeline.video.gemini_local")

    fpath = Path(file_path)
    if not fpath.exists():
        logger.error(f"Local video file not found: {fpath}")
        return None

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        env_path = Path(__file__).resolve().parents[4] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ["GEMINI_API_KEY"] = api_key
                    break
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — cannot use Gemini local path")
            return None

    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        logger.warning(f"google.genai not installed: {e}")
        return None

    client = genai.Client(api_key=api_key)

    # Compact identification prompt (no transcript) — bounded response size
    prompt_text = _build_identification_prompt()

    try:
        logger.info(
            f"Uploading {fpath.name} ({fpath.stat().st_size // (1024*1024)}MB) to Gemini Files API..."
        )
        try:
            uploaded_file = _upload_with_retry(client, fpath, logger)
        except GeminiTimeoutError as exc:
            logger.error(str(exc))
            return None
        except GeminiPermanentError as exc:
            logger.error(str(exc))
            return None

        logger.info(f"Calling Gemini {model} with response_schema (identification mode)...")
        response = client.models.generate_content(
            model=model,
            contents=[uploaded_file, prompt_text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_identification_response_schema(),
            ),
        )
        raw_text = response.text

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.warning(
                f"response_schema mode returned non-JSON ({len(raw_text)} chars) "
                f"at pos {e.pos}: {str(e)[:120]}"
            )
            return {
                "speakers": [],
                "entities_mentioned": [],
                "summary": None,
                "raw": raw_text[:2000],
                "parse_error": True,
            }

        result = {
            "title": parsed.get("title"),
            "duration_estimate": parsed.get("duration_estimate"),
            "language": parsed.get("language"),
            "speakers": parsed.get("speakers", []),
            "entities_mentioned": parsed.get("entities_mentioned", []),
            "summary": parsed.get("summary"),
            "key_moments": parsed.get("key_moments", []),
            "raw": raw_text,
        }

        if include_transcript:
            # Separate call for transcript (avoid huge single-response JSON parse)
            logger.info("include_transcript=True — making separate transcript call...")
            tx = extract_transcript_only(uploaded_file, client, model)
            result["transcript"] = tx
        else:
            result["transcript"] = None

        # AUTOMATIC FALLBACK: if main pass returned all UNKNOWN speakers, run
        # keyframe-based Gemini Vision to try to identify nominally.
        gate = assert_speakers_identified(result)
        if gate["verdict"] == "BLOCKED" and "UNKNOWN" in (gate.get("reason") or ""):
            logger.info("Main pass returned UNKNOWN — triggering keyframe fallback...")
            fallback_speakers = fallback_identify_speakers_from_frames(fpath)
            if fallback_speakers:
                logger.info(
                    f"Fallback identified {len(fallback_speakers)} named speakers — merging"
                )
                # Replace UNKNOWN entries with fallback identified ones
                result["speakers"] = fallback_speakers
                result["fallback_used"] = True
            else:
                logger.warning("Fallback also failed — leaving SPEAKER_UNKNOWN as-is")
                result["fallback_used"] = True
                result["fallback_failed"] = True
        else:
            result["fallback_used"] = False

        return result
    except Exception as e:
        logger.error(
            f"Gemini local fetch failed for {fpath.name}: {type(e).__name__}: {str(e)[:200]}"
        )
        return None


def _complete_name_from_filename(partial_name: str, file_path: Path) -> str:
    """Cross-reference partial name from frame OCR against filename for completion.

    Speaker Visual Gate: about_me slides often show only first name
    (e.g. "Jane" but filename has "Jane Doe"). This function looks for
    the partial name as a token in the filename and returns the multi-token
    name fragment containing it.

    Example:
        partial="Jane", filename="Acme-Widget-Jane-Doe-1080p.mp4"
        → returns "Jane Doe"
    """
    if not partial_name or not file_path:
        return partial_name

    # Normalize: split filename into tokens
    import re

    stem = file_path.stem
    # Split on common separators
    tokens = re.split(r"[\s\-_.()]+", stem)
    tokens = [t for t in tokens if t]  # remove empties

    partial_lower = partial_name.lower().strip()

    # Find position of partial in tokens
    for i, tok in enumerate(tokens):
        if tok.lower() == partial_lower:
            # Look forward for capitalized next token (likely surname)
            if i + 1 < len(tokens):
                next_tok = tokens[i + 1]
                # Surname heuristic: starts with uppercase, 3+ chars, not a number/extension
                if (
                    next_tok
                    and next_tok[0].isupper()
                    and len(next_tok) >= 3
                    and not next_tok.isdigit()
                    and next_tok.lower()
                    not in {
                        "mp4",
                        "mov",
                        "webm",
                        "youtube",
                        "youtu",
                        "1080p",
                        "720p",
                        "h264",
                        "h265",
                        "parte",
                    }
                ):
                    return f"{partial_name} {next_tok}"
            return partial_name

    return partial_name


def fallback_identify_speakers_from_frames(
    file_path: str | Path,
    num_frames: int = 6,
    model: str = "gemini-2.5-flash",
) -> list[dict]:
    """Fallback speaker identification via ffmpeg keyframe extraction + Gemini Vision.

    Speaker Visual Gate (2026-05-12): called when the main extract_local_video_via_gemini
    call returns all speakers as SPEAKER_UNKNOWN. Extracts strategic frames (intro,
    early-mid, mid, late, credits) and runs Gemini Vision OCR on each.

    Used ONLY when:
      - Main identification call returned UNKNOWN speakers
      - Subject was discovered (we know it's a real video, not noise)
      - File is locally accessible (for ffmpeg)

    Cost: ~$0.002 per frame x num_frames = ~$0.01 total. Frequency: <5% of videos.

    Args:
        file_path: Absolute path to video file.
        num_frames: Number of keyframes to extract. Default 5 (intro + 4 spread).
        model: Gemini Vision model.

    Returns:
        List of speaker dicts in same shape as main extract. Empty list if fail.
    """
    import logging
    import subprocess
    import tempfile

    logger = logging.getLogger("pipeline.video.fallback_speakers")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        env_path = Path(__file__).resolve().parents[4] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ["GEMINI_API_KEY"] = api_key
                    break
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — cannot run fallback")
            return []

    fpath = Path(file_path)
    if not fpath.exists():
        logger.error(f"Video file not found: {fpath}")
        return []

    # Probe duration
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(fpath),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        duration = float(result.stdout.strip())
    except Exception as e:
        logger.error(f"ffprobe failed: {e}")
        return []

    # Generate keyframe timestamps: focus on EARLY intro window where speakers
    # typically introduce themselves (about_me slide, lower-third, intro card).
    # Empirical finding: the about_me slide appeared at 00:00:15, NOT at
    # 00:00:02 or 00:00:30. So we sample densely in 0-60s.
    timestamps = [
        2,  # immediate intro card
        15,  # about_me slide window (key finding)
        30,  # lower-third typical
        60,  # presenter context after warm-up
        duration * 0.5,  # mid-content (rare credit)
        max(duration - 15, duration * 0.97),  # late credits
    ][:num_frames]

    tmpdir = Path(tempfile.mkdtemp(prefix="speaker-fallback-"))
    frames = []

    for i, ts in enumerate(timestamps):
        out_frame = tmpdir / f"frame-{i:02d}-{int(ts):05d}s.jpg"
        ts_str = f"{int(ts // 3600):02d}:{int((ts % 3600) // 60):02d}:{int(ts % 60):02d}"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    ts_str,
                    "-i",
                    str(fpath),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    str(out_frame),
                ],
                capture_output=True,
                timeout=30,
            )
            if out_frame.exists() and out_frame.stat().st_size > 1000:
                frames.append((ts_str, out_frame))
        except Exception as e:
            logger.warning(f"ffmpeg failed @ {ts_str}: {e}")

    if not frames:
        logger.error("No frames extracted — fallback aborted")
        return []

    logger.info(f"Extracted {len(frames)} keyframes — running Gemini Vision...")

    try:
        from google import genai
        from google.genai import types as genai_types

        client = genai.Client(api_key=api_key)
    except ImportError as e:
        logger.warning(f"google.genai not installed: {e}")
        return []

    VISION_PROMPT = (
        "Analise este frame de vídeo (apresentação corporativa).\n\n"
        "EXTRAIA NOMES PRÓPRIOS de pessoas que aparecem na imagem, mas DISTINGA:\n"
        "  A. NOMES DO APRESENTADOR (pessoa que está fazendo o vídeo)\n"
        "  B. NOMES DE TERCEIROS (clientes citados, equipe de outras empresas)\n\n"
        "INCLUA em 'names' (A — apresentador):\n"
        "  - Nome em intro card ('Apresentador: X', 'Nome | Cargo')\n"
        "  - Nome em lower-third (banner inferior com identificação)\n"
        "  - Nome em slide 'Quem sou eu' / 'About me' onde o apresentador se apresenta\n"
        "  - Nome em webcam name tag (etiqueta com nome no canto)\n"
        "  - Nome em slide de capa/abertura/créditos da própria apresentação\n"
        "  - Nome próximo a foto de pessoa + cargo executivo (CEO, Founder, Diretor)\n\n"
        "EXCLUA de 'names':\n"
        "  - Lista de clientes ou empresas atendidas\n"
        "  - Lista de equipe de OUTRAS empresas (não a do apresentador)\n"
        "  - Audiência ou participantes citados como referência\n\n"
        "Retorne JSON estrito:\n"
        '{"names":["nome do apresentador identificado"],\n'
        ' "titles":["cargo associado"],\n'
        ' "brands":["empresa do apresentador"],\n'
        ' "speaker_identified":"nome completo ou SPEAKER_UNKNOWN",\n'
        ' "context":"intro_card|lower_third|webcam_visible|about_me_slide|credits|content_only|other"}\n\n'
        "Se aparece nome próprio + cargo (CEO/Founder/Diretor) ISOLADO ou junto a foto,\n"
        "MUITO PROVAVELMENTE é o apresentador → INCLUA. Confidence vem do contexto."
    )

    VISION_SCHEMA = {
        "type": "object",
        "properties": {
            "names": {"type": "array", "items": {"type": "string"}},
            "titles": {"type": "array", "items": {"type": "string"}},
            "brands": {"type": "array", "items": {"type": "string"}},
            "speaker_identified": {"type": "string"},
            "context": {"type": "string"},
        },
        "required": ["names", "titles", "brands", "context"],
    }

    aggregated = {"names": set(), "titles": set(), "brands": set(), "frame_results": []}

    for ts_str, frame_path in frames:
        try:
            # New google.genai API: use Part.from_bytes for inline image data
            image_part = genai_types.Part.from_bytes(
                data=frame_path.read_bytes(),
                mime_type="image/jpeg",
            )
            response = client.models.generate_content(
                model=model,
                contents=[VISION_PROMPT, image_part],
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VISION_SCHEMA,
                ),
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip().rstrip("`").strip()
            try:
                parsed = json.loads(text)
                aggregated["names"].update(parsed.get("names", []))
                aggregated["titles"].update(parsed.get("titles", []))
                aggregated["brands"].update(parsed.get("brands", []))
                aggregated["frame_results"].append({"timestamp": ts_str, **parsed})
            except json.JSONDecodeError:
                logger.warning(f"Frame {ts_str} returned non-JSON: {text[:80]}")
        except Exception as e:
            logger.warning(f"Vision call failed @ {ts_str}: {type(e).__name__}")

    # Cleanup temp frames
    try:
        for _, p in frames:
            p.unlink(missing_ok=True)
        tmpdir.rmdir()
    except Exception:
        pass

    # Build speakers list from aggregated names
    # FILTER: prefer "about_me_slide", "intro_card", "lower_third", "credits" contexts
    # over "visual_content" (which often = clients/customer lists, not the presenter).
    PRESENTER_CONTEXTS = {
        "about_me_slide",
        "intro_card",
        "lower_third",
        "webcam_visible",
        "credits",
    }

    # First pass: identify which frames are "presenter context"
    presenter_frames = [
        fr for fr in aggregated["frame_results"] if fr.get("context") in PRESENTER_CONTEXTS
    ]
    # If we have presenter-context frames, prefer their names. Otherwise use all.
    if presenter_frames:
        candidate_names = set()
        for fr in presenter_frames:
            candidate_names.update(fr.get("names", []))
        # Also include explicit speaker_identified values
        for fr in presenter_frames:
            sid = fr.get("speaker_identified")
            if sid and sid.upper() != "SPEAKER_UNKNOWN":
                candidate_names.add(sid)
    else:
        candidate_names = aggregated["names"]

    speakers = []
    for name in sorted(candidate_names):
        # Find which frame first detected this name (for time_first_appearance)
        first_ts = None
        evidence = "visual_unknown_card"
        for fr in aggregated["frame_results"]:
            if name in fr.get("names", []) or fr.get("speaker_identified") == name:
                first_ts = fr.get("timestamp")
                ctx = fr.get("context", "other")
                evidence = (
                    "visual_intro_card"
                    if ctx == "intro_card"
                    else f"visual_{ctx}"
                    if ctx != "other"
                    else "visual_detected"
                )
                break

        # Try to find title + affiliation from same frame
        title = None
        affiliation = None
        for fr in aggregated["frame_results"]:
            if name in fr.get("names", []) or fr.get("speaker_identified") == name:
                titles_in_frame = fr.get("titles", [])
                brands_in_frame = fr.get("brands", [])
                if titles_in_frame and not title:
                    title = titles_in_frame[0]
                if brands_in_frame and not affiliation:
                    affiliation = brands_in_frame[0]

        # Cross-ref with filename to complete partial names (e.g. "Jane" → "Jane Doe")
        completed_name = _complete_name_from_filename(name, fpath)
        if completed_name != name:
            logger.info(f"Filename cross-ref: '{name}' → '{completed_name}'")

        speakers.append(
            {
                "name": completed_name,
                "evidence": evidence,
                "title": title,
                "affiliation": affiliation,
                "time_first_appearance": first_ts,
                "confidence": "high"
                if any(
                    fr.get("context") in ("intro_card", "lower_third", "credits", "about_me_slide")
                    for fr in aggregated["frame_results"]
                    if name in fr.get("names", []) or fr.get("speaker_identified") == name
                )
                else "medium",
            }
        )

    logger.info(f"Fallback identified {len(speakers)} speakers from {len(frames)} frames")
    return speakers


def extract_transcript_only(uploaded_file, client, model: str = "gemini-2.5-flash") -> str | None:
    """Extract full transcript as PLAIN TEXT — no JSON wrapping.

    Speaker Visual Gate (2026-05-12): called separately AFTER identification pass.
    Plain text response avoids JSON parsing failures on 200k+ char outputs.
    """
    import logging

    logger = logging.getLogger("pipeline.video.gemini_transcript")
    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                uploaded_file,
                (
                    "Transcreva TUDO que é falado neste vídeo, literal e completo.\n"
                    "Formato: texto corrido, com [mm:ss] no início de cada parágrafo "
                    "importante (mudança de tópico). Sem marcação JSON, sem markdown — "
                    "apenas o texto da transcrição."
                ),
            ],
        )
        return response.text
    except Exception as e:
        logger.error(f"Transcript extraction failed: {type(e).__name__}: {str(e)[:200]}")
        return None


def _build_identification_prompt() -> str:
    """Compact identification prompt — NO transcript, only speakers + entities + summary.

    Speaker Visual Gate (2026-05-12): paired with response_schema enforces
    structured output. Response size bounded → JSON parse safe. Transcript
    fetched in separate call via extract_transcript_only.

    MCE-13.13: Boosted overlay weight — visual text overlays (lower-thirds,
    intro cards, name banners) are the HIGHEST confidence signal and must be
    prioritised over audio/inference. Subject entity confidence also boosted
    when a text overlay explicitly names the subject.
    """
    return (
        "Analise este vídeo e identifique:\n"
        "\n"
        "1. SPEAKERS — todas as pessoas que aparecem ou falam. Para cada uma:\n"
        "   PRIORIDADE DE IDENTIFICAÇÃO (use sempre a mais alta disponível):\n"
        "   [PRIORITY 1 — confidence: high] Texto visível em overlay: lower-third (banner\n"
        "     inferior com nome+cargo), intro card com nome, slide 'About me', créditos finais.\n"
        "     Se texto em overlay identificar o nome → confidence=high, evidence=visual_lower_third\n"
        "     ou visual_intro_card conforme aplicável.\n"
        "   [PRIORITY 2 — confidence: high] Intro card em tela cheia com nome claramente visível.\n"
        "   [PRIORITY 3 — confidence: medium] Auto-introdução em áudio ('meu nome é X', 'aqui é X').\n"
        "   [PRIORITY 4 — confidence: medium] Outro speaker menciona o nome em áudio.\n"
        "   [PRIORITY 5 — confidence: low] Inferido por contexto sem evidência direta.\n"
        "   - Se QUALQUER texto overlay identificar o speaker: confidence DEVE ser 'high'.\n"
        "   - Se NÃO conseguir identificar: retorne 'SPEAKER_UNKNOWN_1' etc.\n"
        "   - Em 'evidence' indique de ONDE tirou o nome (visual_lower_third preferido).\n"
        "   - Em 'title' o cargo se visível (Founder, CEO, etc).\n"
        "   - Em 'affiliation' a empresa/marca a que pertence.\n"
        "\n"
        "2. ENTITIES_MENTIONED — todas as empresas/produtos/metodologias mencionadas.\n"
        "   - Marque is_subject=true APENAS para a entidade que é o ASSUNTO PRINCIPAL\n"
        "     (mais menções + claims construídos em torno dela).\n"
        "   - Se o nome da entidade aparece em OVERLAY de texto no vídeo (banner, slide, title\n"
        "     card), isso é evidência de ALTA confiança — inclua essa evidência em evidence_examples.\n"
        "   - 'evidence_examples': 2-3 frases curtas onde a entidade apareceu.\n"
        "\n"
        "3. SUMMARY — resumo executivo em 3-5 frases.\n"
        "\n"
        "4. TITLE, DURATION_ESTIMATE, LANGUAGE — metadata básico.\n"
        "\n"
        "5. KEY_MOMENTS — 3-5 momentos chave (não mais).\n"
        "\n"
        "NÃO INCLUA TRANSCRIÇÃO COMPLETA — apenas identificação e resumo.\n"
        "Retorne JSON estruturado conforme schema.\n"
    )


def _build_speaker_aware_prompt() -> str:
    """[LEGACY] Full prompt v2 — kept for YouTube path until migrated to structured."""
    return (
        "Extraia o seguinte deste vídeo em formato JSON estrito:\n"
        "{\n"
        '  "title": "<título do vídeo>",\n'
        '  "duration_estimate": "<duração em mm:ss>",\n'
        '  "language": "<idioma detectado, ex: pt-BR>",\n'
        '  "speakers": [\n'
        "    {\n"
        '      "name": "<nome completo OU \\"SPEAKER_UNKNOWN_1\\" se não conseguir identificar>",\n'
        '      "evidence": "visual_intro_card|visual_lower_third|visual_slide|visual_credits|audio_self_introduction|audio_mentioned_by_other|inferred_from_context",\n'
        '      "title": "<cargo/título profissional se visível>",\n'
        '      "affiliation": "<empresa/marca a que pertence>",\n'
        '      "time_first_appearance": "<mm:ss quando primeiro identificado>",\n'
        '      "confidence": "high|medium|low"\n'
        "    }\n"
        "  ],\n"
        '  "entities_mentioned": [\n'
        "    {\n"
        '      "name": "<nome da empresa/marca/produto>",\n'
        '      "type": "company|product|methodology|person|other",\n'
        '      "mention_count": <quantas vezes apareceu>,\n'
        '      "is_subject": true,\n'
        '      "evidence_examples": ["<frase ou texto onde apareceu>"]\n'
        "    }\n"
        "  ],\n"
        '  "transcript": "<transcrição literal completa>",\n'
        '  "visual_description": "<o que aparece em tela, cronológico>",\n'
        '  "key_moments": [{"time": "mm:ss", "type": "slide|demo|claim|cta", "description": "<o que acontece>"}],\n'
        '  "summary": "<resumo executivo 3-5 frases>"\n'
        "}\n\n"
        "REGRAS DE IDENTIFICAÇÃO (NÃO-NEGOCIÁVEIS):\n"
        "1. SPEAKERS: examine SEMPRE o vídeo VISUAL e o áudio. Procure por:\n"
        "   - Intro card / título de abertura com nome do apresentador\n"
        "   - Lower-third (banner com nome + cargo)\n"
        "   - Slide 'About me' / 'Quem sou eu'\n"
        "   - Créditos finais\n"
        "   - Auto-introdução ('meu nome é X', 'aqui é o X')\n"
        "   - Menção do nome por outro speaker\n"
        "   Se NÃO conseguir, retorne 'SPEAKER_UNKNOWN_1' e descreva o que VIU em 'evidence'.\n"
        "2. ENTITIES: liste TODAS as empresas/produtos/metodologias mencionadas.\n"
        "   is_subject=true para a entidade que é o ASSUNTO PRINCIPAL\n"
        "   (mais menções + claims construídos em torno dela).\n"
        "3. transcript = TUDO falado, literal, sem omissões\n"
        "4. visual_description = TUDO mostrado em tela\n"
        "5. JSON válido, parseável, sem markdown blocks.\n"
    )


def assert_speakers_identified(gemini_result: dict) -> dict:
    """Speaker Visual Gate (2026-05-12) — validate Gemini result has identified speakers.

    This is the GATE that prevents silent speaker-unknown bugs. Called AFTER
    extract_youtube_via_gemini or extract_local_video_via_gemini. Returns a
    verdict dict that the pipeline orchestrator uses to decide:
      - PASS: speakers identified with high/medium confidence — proceed
      - REVIEW: speakers identified but low confidence — flag for human review
      - BLOCKED: no speakers identified — STOP cascade, do not write to agents

    Args:
        gemini_result: Output dict from extract_*_via_gemini functions.

    Returns:
        {
          "verdict": "PASS" | "REVIEW" | "BLOCKED",
          "reason": "<human-readable explanation>",
          "speakers_count": int,
          "speakers_named": int,  # excludes SPEAKER_UNKNOWN_*
          "speakers_high_confidence": int,
          "primary_speaker": str | None,
          "primary_subject": str | None,  # main entity (is_subject=true)
        }
    """
    if not gemini_result or not isinstance(gemini_result, dict):
        return {
            "verdict": "BLOCKED",
            "reason": "gemini_result missing or invalid",
            "speakers_count": 0,
            "speakers_named": 0,
            "speakers_high_confidence": 0,
            "primary_speaker": None,
            "primary_subject": None,
        }

    speakers = gemini_result.get("speakers", []) or []
    # Handle legacy format (list of strings) and v2 format (list of dicts)
    normalized_speakers = []
    for s in speakers:
        if isinstance(s, str):
            normalized_speakers.append({"name": s, "confidence": "low", "evidence": "unknown"})
        elif isinstance(s, dict):
            normalized_speakers.append(s)

    count = len(normalized_speakers)
    named = sum(
        1
        for s in normalized_speakers
        if s.get("name") and not s["name"].upper().startswith("SPEAKER_UNKNOWN")
    )
    high_conf = sum(1 for s in normalized_speakers if s.get("confidence") == "high")

    # Determine primary speaker (first named, prefer high confidence)
    primary_speaker = None
    for s in sorted(normalized_speakers, key=lambda x: 0 if x.get("confidence") == "high" else 1):
        if s.get("name") and not s["name"].upper().startswith("SPEAKER_UNKNOWN"):
            primary_speaker = s["name"]
            break

    # Determine primary subject (entity with is_subject=true and highest mention_count)
    entities = gemini_result.get("entities_mentioned", []) or []
    subjects = [e for e in entities if isinstance(e, dict) and e.get("is_subject")]
    if subjects:
        subjects.sort(key=lambda e: e.get("mention_count", 0), reverse=True)
        primary_subject = subjects[0].get("name")
    else:
        primary_subject = None

    # Verdict logic
    if count == 0:
        verdict = "BLOCKED"
        reason = "Gemini returned ZERO speakers — cannot route to any agent safely"
    elif named == 0:
        verdict = "BLOCKED"
        reason = f"{count} speakers detected but ALL are SPEAKER_UNKNOWN — visual gate failed"
    elif high_conf == 0 and named > 0:
        verdict = "REVIEW"
        reason = f"{named} speakers named but none high-confidence — flag for human review"
    else:
        verdict = "PASS"
        reason = f"{named}/{count} speakers identified ({high_conf} high-confidence)"

    return {
        "verdict": verdict,
        "reason": reason,
        "speakers_count": count,
        "speakers_named": named,
        "speakers_high_confidence": high_conf,
        "primary_speaker": primary_speaker,
        "primary_subject": primary_subject,
    }


def extract_youtube_transcript(url: str) -> str | None:
    """Extract transcript from YouTube using youtube-transcript-api.

    This is the LIGHTWEIGHT approach -- no video download needed.
    Falls back to None if transcript unavailable.

    CR-YT-API fix (2026-05-12):
      - youtube-transcript-api >=1.x dropped classmethod get_transcript().
      - Now uses instance methods .fetch(video_id, languages=[...]).
      - Replaced bare `except Exception: return None` (silent failure) with
        explicit error categories + structured logging so consumers can act
        on the real root cause (ImportError vs RequestBlocked vs NoTranscript).
    """
    import logging

    logger = logging.getLogger("pipeline.video.youtube")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            NoTranscriptFound,
            TranscriptsDisabled,
        )
    except ImportError as e:
        logger.warning(f"youtube_transcript_api not installed: {e}")
        return None

    # Extract video ID from URL
    video_id = None
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]

    if not video_id:
        logger.warning(f"Could not parse video_id from URL: {url}")
        return None

    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=["en", "pt", "pt-BR"])
        snippets = list(fetched) if hasattr(fetched, "__iter__") else fetched.snippets
        return "\n".join(s.text for s in snippets)
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logger.info(f"No transcript available for {video_id}: {type(e).__name__}")
        return None
    except Exception as e:
        # IP block / network / parser change — propagate name so caller knows
        logger.error(
            f"YouTube transcript fetch FAILED for {video_id}: {type(e).__name__}: {str(e)[:200]}"
        )
        return None


def extract_youtube_metadata(url: str) -> dict:
    """Extract video metadata using yt-dlp (no download)."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "title": data.get("title", ""),
                "duration": data.get("duration", 0),
                "uploader": data.get("uploader", ""),
                "upload_date": data.get("upload_date", ""),
                "description": data.get("description", "")[:500],
                "view_count": data.get("view_count", 0),
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def transcribe_assemblyai(file_path: str | Path, language_code: str = "pt") -> str | None:
    """Transcribe audio/video using AssemblyAI (default when ASSEMBLYAI_API_KEY set).

    Returns concatenated transcript text, or None if API unavailable/failed.
    Story: MCE-16.1
    """
    api_key = os.environ.get("ASSEMBLYAI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import assemblyai as aai
    except ImportError:
        logger.warning("[transcribe_assemblyai] assemblyai package not installed; falling back")
        return None

    try:
        aai.settings.api_key = api_key
        config = aai.TranscriptionConfig(
            speaker_labels=True,  # bonus: speaker labels grátis
            language_code=language_code,
        )
        start = time.perf_counter()
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(str(file_path), config=config)

        if transcript.status == aai.TranscriptStatus.error:
            logger.warning(f"[transcribe_assemblyai] error: {transcript.error}")
            return None

        duration = time.perf_counter() - start
        text = transcript.text or ""

        # Sidecar meta (AC4)
        try:
            fp = Path(file_path)
            meta_path = fp.with_suffix(fp.suffix + ".transcription-meta.json")
            meta_path.write_text(
                json.dumps(
                    {
                        "provider": "assemblyai",
                        "duration_seconds": round(duration, 2),
                        "language": language_code,
                        "char_count": len(text),
                        "speaker_count": len({u.speaker for u in (transcript.utterances or [])}),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as meta_exc:
            logger.debug(f"[transcribe_assemblyai] sidecar write failed: {meta_exc}")

        logger.info(f"[transcribe] provider=assemblyai duration={duration:.1f}s chars={len(text)}")
        return text or None

    except Exception as exc:
        logger.warning(f"[transcribe_assemblyai] exception: {exc}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# ASR MODEL RESOLUTION  (STORY-GBA-F4.2 — 2026-06-20)
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY: the local faster-whisper fallback previously hardcoded the `base` model,
# the smallest/least accurate Whisper checkpoint. OpenAI recommends `large-v3`
# for production transcription — `base` loses precision on real audio (accents,
# technical terms, background noise). This story raises the default to
# `large-v3` while keeping it CONFIGURABLE so machines without GPU / enough RAM
# can downgrade.
#
# CONFIG / FALLBACK (machine without GPU or low memory):
#   - Set env var `MCE_ASR_MODEL` to override the default. Examples:
#       export MCE_ASR_MODEL=large-v3   # default (best quality, needs ~3GB)
#       export MCE_ASR_MODEL=medium     # good balance, ~1.5GB, CPU-friendly
#       export MCE_ASR_MODEL=base       # fastest/lowest memory (legacy behavior)
#   - Or pass `model_size="medium"` explicitly to transcribe_local().
#   - faster-whisper runs on CPU here (device="cpu", compute_type="int8"); on a
#     low-RAM CPU box prefer `medium` or `base`. `large-v3` on CPU is slow but
#     correct; downgrade if it OOMs or is too slow for your batch volume.
#
# pyannote 3.1 diarization is NOT touched by this story — only the ASR model.

DEFAULT_ASR_MODEL = "large-v3"


def _resolve_asr_model(model_size: str | None = None) -> str:
    """Resolve which Whisper model the local ASR fallback should load.

    Resolution order (highest precedence first):
      1. Explicit `model_size` argument (caller override).
      2. `MCE_ASR_MODEL` environment variable (deploy-time override).
      3. DEFAULT_ASR_MODEL (`large-v3`, production default).

    Pure function — does no I/O beyond reading os.environ — so it is
    deterministic and characterization-testable without transcribing audio.

    Story: STORY-GBA-F4.2
    """
    if model_size:
        return model_size
    env_model = os.environ.get("MCE_ASR_MODEL", "").strip()
    if env_model:
        return env_model
    return DEFAULT_ASR_MODEL


def transcribe_local(file_path: str | Path, model_size: str | None = None) -> str | None:
    """Dispatcher: AssemblyAI primary, faster-whisper fallback.

    When ASSEMBLYAI_API_KEY is set, uses AssemblyAI (cheaper, accurate, +speaker labels).
    When key absent or AssemblyAI fails, falls back to faster-whisper local.

    Signature preserved for backward compat (model_size used only on Whisper fallback).
    `model_size=None` resolves via env/default policy (large-v3) — see
    _resolve_asr_model(). Story: MCE-16.1, STORY-GBA-F4.2
    """
    # PRIMARY: AssemblyAI when key configured
    if os.environ.get("ASSEMBLYAI_API_KEY", "").strip():
        text = transcribe_assemblyai(file_path)
        if text:
            return text
        logger.info("[transcribe] AssemblyAI returned no text, falling back to Whisper local")

    # FALLBACK: faster-whisper local
    return _transcribe_whisper_local(file_path, model_size=model_size)


def _transcribe_whisper_local(file_path: str | Path, model_size: str | None = None) -> str | None:
    """Transcribe via faster-whisper local (fallback path).

    Default model resolved via _resolve_asr_model() — large-v3 unless overridden
    by `model_size` arg or MCE_ASR_MODEL env. Story: MCE-16.1, STORY-GBA-F4.2

    Requires: pip install faster-whisper
    """
    resolved_model = _resolve_asr_model(model_size)
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Video file not found: {file_path}")

    model = WhisperModel(resolved_model, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(file_path))

    transcript_parts = []
    for segment in segments:
        transcript_parts.append(segment.text)

    text = " ".join(transcript_parts)

    # Sidecar meta (AC4)
    try:
        meta_path = Path(file_path).with_suffix(Path(file_path).suffix + ".transcription-meta.json")
        meta_path.write_text(
            json.dumps(
                {
                    "provider": "faster_whisper",
                    "model_size": resolved_model,
                    "char_count": len(text),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass

    logger.info(f"[transcribe] provider=faster_whisper model={resolved_model} chars={len(text)}")
    return text


def process_video(
    source: str,
    source_tag: str,
    output_dir: str | Path | None = None,
) -> VideoResult:
    """Process a video source (YouTube URL or local file).

    Tries multiple extraction methods in order of preference:
    1. YouTube transcript API (lightest, free)
    2. yt-dlp metadata extraction
    3. Local Whisper transcription (heaviest, most accurate)

    Args:
        source: YouTube URL or local file path.
        source_tag: Source identifier for inbox routing.
        output_dir: Override output directory.

    Returns:
        VideoResult with transcript and metadata.
    """
    from engine.paths import KNOWLEDGE_EXTERNAL

    if output_dir is None:
        output_dir = KNOWLEDGE_EXTERNAL / "inbox" / source_tag
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    is_youtube = "youtube.com" in source or "youtu.be" in source

    transcript = None
    metadata: dict = {}

    if is_youtube:
        # GEMINI-YT-WIRE (2026-05-12): Try Gemini native first
        # (no local IP block, includes visual description for screen videos).
        # Falls back to youtube-transcript-api → yt-dlp metadata chain.
        gemini_result = extract_youtube_via_gemini(source)
        if gemini_result and gemini_result.get("transcript"):
            transcript = gemini_result["transcript"]
            metadata = {
                "title": gemini_result.get("title", ""),
                "duration_estimate": gemini_result.get("duration_estimate", ""),
                "language": gemini_result.get("language", ""),
                "speakers": gemini_result.get("speakers", []),
                "visual_description": gemini_result.get("visual_description"),
                "summary": gemini_result.get("summary"),
                "key_moments": gemini_result.get("key_moments", []),
                "extracted_via": "gemini-2.5-flash",
            }
        else:
            # Legacy fallbacks (most likely also blocked, but try anyway)
            transcript = extract_youtube_transcript(source)
            metadata = extract_youtube_metadata(source)
            if metadata:
                metadata["extracted_via"] = "youtube-transcript-api+yt-dlp"
    else:
        # Local file -- try Whisper
        source_path = Path(source)
        if source_path.exists():
            transcript = transcribe_local(source_path)
            metadata = {"title": source_path.stem, "source": "local", "extracted_via": "whisper"}

    if transcript is None:
        transcript = (
            "[Transcript unavailable -- video may be PRIVATE/UNLISTED, "
            "or all extraction paths failed (Gemini 403 / transcript-api blocked / yt-dlp blocked). "
            "Download manually and re-ingest as local file.]"
        )

    # Generate output filename
    title = metadata.get("title", Path(source).stem if not is_youtube else "video")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:80]
    output_file = output_dir / f"{safe_title}.txt"

    # Write combined output
    output_parts: list[str] = []
    if metadata:
        output_parts.append(f"# {metadata.get('title', 'Video')}")
        output_parts.append(f"Source: {source}")
        if metadata.get("uploader"):
            output_parts.append(f"Author: {metadata['uploader']}")
        if metadata.get("duration"):
            mins = metadata["duration"] // 60
            output_parts.append(f"Duration: {mins} minutes")
        output_parts.append("---\n")

    output_parts.append("## Transcript\n")
    output_parts.append(transcript)

    full_text = "\n".join(output_parts)
    output_file.write_text(full_text, encoding="utf-8")

    return VideoResult(
        source=source,
        transcript=transcript,
        metadata=metadata,
        output_path=output_file,
    )


def check_capabilities() -> dict:
    """Check which video processing capabilities are available."""
    caps = {
        "youtube_transcript": False,
        "yt_dlp": False,
        "whisper": False,
        "pytesseract": False,
        "opencv": False,
    }

    try:
        import youtube_transcript_api  # noqa: F401

        caps["youtube_transcript"] = True
    except ImportError:
        pass

    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, timeout=5)
        caps["yt_dlp"] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        import faster_whisper  # noqa: F401

        caps["whisper"] = True
    except ImportError:
        pass

    try:
        import pytesseract  # noqa: F401

        caps["pytesseract"] = True
    except ImportError:
        pass

    try:
        import cv2  # noqa: F401

        caps["opencv"] = True
    except ImportError:
        pass

    return caps
