"""
Skill Seekers Bridge — Subprocess integration with SS CLI.
===========================================================

This module enables Mega Brain to call Skill Seekers commands via subprocess,
keeping dependencies isolated in separate virtual environments.

SS is installed in ~/.venvs/skill-seekers/ and called via its CLI entrypoints.
If SS is not available, this module falls back to lightweight extractors.

Usage:
    from core.intelligence.pipeline.ss_bridge import ingest_pdf, is_ss_available

    if is_ss_available():
        output_path = ingest_pdf(Path("document.pdf"), "alex-hormozi")
    else:
        # Use fallback extractors
        from core.intelligence.pipeline.extractors import extract_pdf
        text = extract_pdf(Path("document.pdf"))
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from core.paths import ROUTING, KNOWLEDGE_EXTERNAL, KNOWLEDGE_BUSINESS, KNOWLEDGE_PERSONAL

logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────

_CONFIG_PATH = ROUTING.get("ss_bridge_config")
_LOG_PATH = ROUTING.get("ss_bridge_log")

_DEFAULT_CONFIG = {
    "skill_seekers": {
        "venv_path": "~/.venvs/skill-seekers",
        "timeout_seconds": 300,
        "output_format": "markdown",
        "fallback_enabled": True,
        "log_level": "INFO",
    },
    "commands": {
        "pdf": "skill-seekers-pdf",
        "docx": "skill-seekers-word",
        "video": "skill-seekers-video",
        "web": "skill-seekers-doc-scrape",
    },
    "output_templates": {
        "external": "external/inbox/{source_tag}",
        "business": "business/inbox/{source_tag}",
        "personal": "personal/inbox/{source_tag}",
    },
}


def _load_config() -> dict[str, Any]:
    """Load SS bridge configuration from YAML file."""
    if _CONFIG_PATH and _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config:
                    return config
        except (yaml.YAMLError, OSError) as e:
            logger.warning("Failed to load SS bridge config: %s. Using defaults.", e)
    return _DEFAULT_CONFIG


def _get_config() -> dict[str, Any]:
    """Get cached configuration."""
    if not hasattr(_get_config, "_cache"):
        _get_config._cache = _load_config()
    return _get_config._cache


def _get_venv_path() -> Path:
    """Get the SS virtual environment path."""
    config = _get_config()
    venv_str = config.get("skill_seekers", {}).get("venv_path", "~/.venvs/skill-seekers")
    return Path(os.path.expanduser(venv_str))


def _get_timeout() -> int:
    """Get command timeout in seconds."""
    config = _get_config()
    return config.get("skill_seekers", {}).get("timeout_seconds", 300)


def _get_command(cmd_type: str) -> str:
    """Get the CLI command for a given type."""
    config = _get_config()
    return config.get("commands", {}).get(cmd_type, f"skill-seekers-{cmd_type}")


def _is_fallback_enabled() -> bool:
    """Check if fallback to lightweight extractors is enabled."""
    config = _get_config()
    return config.get("skill_seekers", {}).get("fallback_enabled", True)


# ── Logging ─────────────────────────────────────────────────────────────────

def _log_operation(
    operation: str,
    success: bool,
    input_path: str | None = None,
    output_path: str | None = None,
    error: str | None = None,
    duration_ms: int | None = None,
) -> None:
    """Append operation to SS bridge log (JSONL format)."""
    if not _LOG_PATH:
        return

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "success": success,
        "input": input_path,
        "output": output_path,
        "error": error,
        "duration_ms": duration_ms,
    }

    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        logger.warning("Failed to write SS bridge log: %s", e)


# ── Availability Check ──────────────────────────────────────────────────────

def is_ss_available() -> bool:
    """Check if Skill Seekers is installed and available.

    Returns:
        True if SS venv exists and skill_seekers module is importable.
    """
    venv_path = _get_venv_path()

    # Check venv directory exists
    if not venv_path.exists():
        logger.debug("SS venv not found at %s", venv_path)
        return False

    # Check Python executable exists
    python_path = venv_path / "bin" / "python"
    if not python_path.exists():
        logger.debug("SS Python not found at %s", python_path)
        return False

    # Try to import skill_seekers
    try:
        result = subprocess.run(
            [str(python_path), "-c", "import skill_seekers; print('ok')"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "ok" in result.stdout:
            return True
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.debug("SS availability check failed: %s", e)

    return False


def is_ss_video_available() -> bool:
    """Check if Skill Seekers video support is installed.

    Returns:
        True if torch and faster_whisper are available in SS venv.
    """
    if not is_ss_available():
        return False

    venv_path = _get_venv_path()
    python_path = venv_path / "bin" / "python"

    try:
        result = subprocess.run(
            [str(python_path), "-c", "import torch; import faster_whisper; print('ok')"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0 and "ok" in result.stdout
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False


# ── Core Subprocess Interface ───────────────────────────────────────────────

def call_ss(
    command: list[str],
    timeout: int | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Execute a Skill Seekers CLI command.

    Args:
        command: Command and arguments to execute (e.g., ["skill-seekers-pdf", "file.pdf"])
        timeout: Command timeout in seconds (defaults to config value)
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess with return code, stdout, stderr

    Raises:
        subprocess.TimeoutExpired: If command exceeds timeout
        subprocess.SubprocessError: If command fails to execute
        RuntimeError: If SS is not available
    """
    if not is_ss_available():
        raise RuntimeError("Skill Seekers is not installed. Run bin/install-skill-seekers.sh")

    venv_path = _get_venv_path()
    timeout = timeout or _get_timeout()

    # Build environment with SS venv activated
    env = os.environ.copy()
    env["PATH"] = f"{venv_path}/bin:{env.get('PATH', '')}"
    env["VIRTUAL_ENV"] = str(venv_path)

    # Remove any existing Python path that might interfere
    env.pop("PYTHONHOME", None)

    logger.debug("Executing SS command: %s", " ".join(command))

    return subprocess.run(
        command,
        env=env,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
    )


# ── Output Path Resolution ──────────────────────────────────────────────────

def _resolve_output_path(
    source_tag: str,
    filename: str,
    bucket: str = "external",
) -> Path:
    """Resolve output path for ingested content.

    Args:
        source_tag: Source identifier (e.g., "alex-hormozi")
        filename: Output filename
        bucket: Knowledge bucket ("external", "business", "personal")

    Returns:
        Full path to output file
    """
    bucket_roots = {
        "external": KNOWLEDGE_EXTERNAL,
        "business": KNOWLEDGE_BUSINESS,
        "personal": KNOWLEDGE_PERSONAL,
    }

    root = bucket_roots.get(bucket, KNOWLEDGE_EXTERNAL)
    output_dir = root / "inbox" / source_tag
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir / filename


# ── Ingest Functions ────────────────────────────────────────────────────────

def ingest_pdf(
    pdf_path: Path,
    source_tag: str,
    bucket: str = "external",
    use_fallback: bool = True,
) -> Path:
    """Ingest a PDF file using Skill Seekers.

    Args:
        pdf_path: Path to PDF file
        source_tag: Source identifier for organization
        bucket: Knowledge bucket for output
        use_fallback: Whether to use lightweight extractor if SS unavailable

    Returns:
        Path to generated markdown file

    Raises:
        RuntimeError: If SS not available and fallback disabled
        FileNotFoundError: If PDF file doesn't exist
    """
    import time
    start_time = time.time()

    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_filename = f"{pdf_path.stem}.md"
    output_path = _resolve_output_path(source_tag, output_filename, bucket)

    # Try SS first
    if is_ss_available():
        try:
            cmd = _get_command("pdf")
            result = call_ss([cmd, str(pdf_path), "-o", str(output_path)])

            if result.returncode == 0:
                duration_ms = int((time.time() - start_time) * 1000)
                _log_operation(
                    "ingest_pdf",
                    success=True,
                    input_path=str(pdf_path),
                    output_path=str(output_path),
                    duration_ms=duration_ms,
                )
                return output_path
            else:
                logger.warning("SS PDF extraction failed: %s", result.stderr)
        except subprocess.SubprocessError as e:
            logger.warning("SS PDF command failed: %s", e)

    # Fallback to lightweight extractor
    if use_fallback and _is_fallback_enabled():
        logger.info("Using fallback PDF extractor for %s", pdf_path.name)
        try:
            from core.intelligence.pipeline.extractors import extract_pdf

            text = extract_pdf(pdf_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text, encoding="utf-8")

            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "ingest_pdf_fallback",
                success=True,
                input_path=str(pdf_path),
                output_path=str(output_path),
                duration_ms=duration_ms,
            )
            return output_path
        except ImportError as e:
            _log_operation(
                "ingest_pdf",
                success=False,
                input_path=str(pdf_path),
                error=f"Fallback not available: {e}",
            )
            raise RuntimeError(f"PDF extraction failed and fallback not available: {e}")

    _log_operation(
        "ingest_pdf",
        success=False,
        input_path=str(pdf_path),
        error="SS not available and fallback disabled",
    )
    raise RuntimeError("SS not available and fallback disabled")


def ingest_docx(
    docx_path: Path,
    source_tag: str,
    bucket: str = "external",
    use_fallback: bool = True,
) -> Path:
    """Ingest a DOCX file using Skill Seekers.

    Args:
        docx_path: Path to DOCX file
        source_tag: Source identifier for organization
        bucket: Knowledge bucket for output
        use_fallback: Whether to use lightweight extractor if SS unavailable

    Returns:
        Path to generated markdown file

    Raises:
        RuntimeError: If SS not available and fallback disabled
        FileNotFoundError: If DOCX file doesn't exist
    """
    import time
    start_time = time.time()

    docx_path = Path(docx_path).resolve()
    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX not found: {docx_path}")

    output_filename = f"{docx_path.stem}.md"
    output_path = _resolve_output_path(source_tag, output_filename, bucket)

    # Try SS first
    if is_ss_available():
        try:
            cmd = _get_command("docx")
            result = call_ss([cmd, str(docx_path), "-o", str(output_path)])

            if result.returncode == 0:
                duration_ms = int((time.time() - start_time) * 1000)
                _log_operation(
                    "ingest_docx",
                    success=True,
                    input_path=str(docx_path),
                    output_path=str(output_path),
                    duration_ms=duration_ms,
                )
                return output_path
            else:
                logger.warning("SS DOCX extraction failed: %s", result.stderr)
        except subprocess.SubprocessError as e:
            logger.warning("SS DOCX command failed: %s", e)

    # Fallback to lightweight extractor
    if use_fallback and _is_fallback_enabled():
        logger.info("Using fallback DOCX extractor for %s", docx_path.name)
        try:
            from core.intelligence.pipeline.extractors import extract_docx

            text = extract_docx(docx_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text, encoding="utf-8")

            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "ingest_docx_fallback",
                success=True,
                input_path=str(docx_path),
                output_path=str(output_path),
                duration_ms=duration_ms,
            )
            return output_path
        except ImportError as e:
            _log_operation(
                "ingest_docx",
                success=False,
                input_path=str(docx_path),
                error=f"Fallback not available: {e}",
            )
            raise RuntimeError(f"DOCX extraction failed and fallback not available: {e}")

    _log_operation(
        "ingest_docx",
        success=False,
        input_path=str(docx_path),
        error="SS not available and fallback disabled",
    )
    raise RuntimeError("SS not available and fallback disabled")


def ingest_video(
    url_or_path: str,
    source_tag: str,
    bucket: str = "external",
) -> Path:
    """Ingest a video (YouTube URL or local file) using Skill Seekers.

    Args:
        url_or_path: YouTube URL or path to local video file
        source_tag: Source identifier for organization
        bucket: Knowledge bucket for output

    Returns:
        Path to generated transcript markdown file

    Raises:
        RuntimeError: If SS video support not available
    """
    import time
    start_time = time.time()

    if not is_ss_video_available():
        _log_operation(
            "ingest_video",
            success=False,
            input_path=url_or_path,
            error="SS video support not installed",
        )
        raise RuntimeError(
            "SS video support not installed. Run bin/install-skill-seekers-video.sh"
        )

    # Determine output filename
    if url_or_path.startswith(("http://", "https://")):
        # Extract video ID from URL for filename
        import re
        video_id_match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", url_or_path)
        video_id = video_id_match.group(1) if video_id_match else "video"
        output_filename = f"{video_id}_transcript.md"
    else:
        # Local file
        path = Path(url_or_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {url_or_path}")
        output_filename = f"{path.stem}_transcript.md"

    output_path = _resolve_output_path(source_tag, output_filename, bucket)

    try:
        cmd = _get_command("video")
        result = call_ss([cmd, url_or_path, "-o", str(output_path)])

        if result.returncode == 0:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "ingest_video",
                success=True,
                input_path=url_or_path,
                output_path=str(output_path),
                duration_ms=duration_ms,
            )
            return output_path
        else:
            _log_operation(
                "ingest_video",
                success=False,
                input_path=url_or_path,
                error=result.stderr,
            )
            raise RuntimeError(f"Video ingestion failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        _log_operation(
            "ingest_video",
            success=False,
            input_path=url_or_path,
            error="Command timed out",
        )
        raise RuntimeError("Video ingestion timed out")


def ingest_website(
    url: str,
    source_tag: str,
    bucket: str = "external",
) -> Path:
    """Scrape and ingest a website using Skill Seekers.

    Args:
        url: Website URL to scrape
        source_tag: Source identifier for organization
        bucket: Knowledge bucket for output

    Returns:
        Path to generated markdown file

    Raises:
        RuntimeError: If SS not available
    """
    import time
    import hashlib
    start_time = time.time()

    if not is_ss_available():
        _log_operation(
            "ingest_website",
            success=False,
            input_path=url,
            error="SS not available",
        )
        raise RuntimeError("Skill Seekers is not installed")

    # Generate filename from URL hash
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    output_filename = f"web_{url_hash}.md"
    output_path = _resolve_output_path(source_tag, output_filename, bucket)

    try:
        cmd = _get_command("web")
        result = call_ss([cmd, url, "-o", str(output_path)])

        if result.returncode == 0:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "ingest_website",
                success=True,
                input_path=url,
                output_path=str(output_path),
                duration_ms=duration_ms,
            )
            return output_path
        else:
            _log_operation(
                "ingest_website",
                success=False,
                input_path=url,
                error=result.stderr,
            )
            raise RuntimeError(f"Website scraping failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        _log_operation(
            "ingest_website",
            success=False,
            input_path=url,
            error="Command timed out",
        )
        raise RuntimeError("Website scraping timed out")


# ── Utility Functions ───────────────────────────────────────────────────────

def get_ss_version() -> str | None:
    """Get the installed Skill Seekers version.

    Returns:
        Version string or None if not installed.
    """
    if not is_ss_available():
        return None

    venv_path = _get_venv_path()
    python_path = venv_path / "bin" / "python"

    try:
        result = subprocess.run(
            [str(python_path), "-c", "import skill_seekers; print(skill_seekers.__version__)"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    return None


def get_bridge_status() -> dict[str, Any]:
    """Get current bridge status and configuration.

    Returns:
        Dict with availability, version, config, and capability info.
    """
    return {
        "ss_available": is_ss_available(),
        "ss_video_available": is_ss_video_available(),
        "ss_version": get_ss_version(),
        "venv_path": str(_get_venv_path()),
        "fallback_enabled": _is_fallback_enabled(),
        "timeout_seconds": _get_timeout(),
        "config_path": str(_CONFIG_PATH) if _CONFIG_PATH else None,
        "log_path": str(_LOG_PATH) if _LOG_PATH else None,
    }
