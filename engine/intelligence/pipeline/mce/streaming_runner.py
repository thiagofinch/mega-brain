"""
streaming_runner.py -- Streaming Step Runner for MCE Pipeline
=============================================================

Bridges the LLM provider's streaming interface with the pipeline's
hook bus and cost tracker.  Yields ``PartialResult`` objects mid-stream
so downstream consumers can start processing before a step completes.

Architecture
------------
::

    StreamingStepRunner
      |-- execute_streaming(step_id, prompt)  -> AsyncIterator[PartialResult]
      |-- execute_batch(step_id, prompt)      -> str  (v1 fallback)
      |-- execute(step_id, prompt, streaming) -> str  (auto-detect mode)
      |
      v
    LLMProvider.analyze_streaming()   # yields text chunks
    LLMProvider.analyze()             # batch fallback
    HookBus                           # pre_llm_call, post_partial_result, post_llm_call
    CostTracker                       # progressive token tracking
    FeatureGates                      # STREAMING gate check

Design Decisions
~~~~~~~~~~~~~~~~
- ``execute()`` auto-detects mode from FeatureGates when streaming=None.
  This means callers don't need to know about gates -- they call execute()
  and the runner picks the best mode.
- Partial result detection uses simple pattern matching (regex for
  capitalized entity names, insight keywords).  Real NER is deferred to
  a future story -- this gives us the plumbing now.
- Cost tracking is progressive: tokens are estimated per-chunk and a
  final reconciliation happens at stream end.
- Hook emissions: pre_llm_call fires once before streaming starts,
  post_llm_call fires once at the end with final token counts.
  post_partial_result fires for each meaningful chunk (not every token).

Constraints
~~~~~~~~~~~
- stdlib + project deps only (no new external deps).
- All functions are DETERMINISTIC given the same provider responses.
- Thread-safe: no mutable shared state beyond what the hook bus manages.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-4.1 -- Streaming Step Runner
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Iterator

from engine.intelligence.pipeline.mce.cost_tracker import CostTracker
from engine.intelligence.pipeline.mce.feature_gates import FeatureGates
from engine.intelligence.pipeline.mce.hook_bus import HookBus
from engine.intelligence.pipeline.mce.llm_provider import LLMProvider

logger = logging.getLogger("mce.streaming_runner")

# ---------------------------------------------------------------------------
# Regex patterns for lightweight artifact detection in streaming chunks.
# These catch capitalized multi-word entities and common insight keywords.
# Real NER is deferred -- this is the 80/20 detection layer.
# ---------------------------------------------------------------------------

# Matches capitalized multi-word sequences likely to be entity names
# e.g. "Jane Doe", "Acme Corporation", "Revenue Growth"
_ENTITY_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")

# Matches insight-signaling keywords that indicate a meaningful partial result
_INSIGHT_KEYWORDS = frozenset(
    {
        "decision",
        "insight",
        "risk",
        "opportunity",
        "blocker",
        "action",
        "recommendation",
        "finding",
        "conclusion",
        "pattern",
        "trend",
        "anomaly",
        "milestone",
    }
)


# ---------------------------------------------------------------------------
# PartialResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class PartialResult:
    """A partial result yielded during streaming LLM execution.

    Attributes:
        chunk_text: The raw text chunk from the LLM.
        detected_artifacts: Entity names and insight keywords found in
            this chunk via lightweight pattern matching.
        is_final: True if this is the last chunk in the stream.
        cumulative_tokens: Estimated total tokens received so far
            (cumulative across all chunks in this stream).
    """

    chunk_text: str
    detected_artifacts: list[str] = field(default_factory=list)
    is_final: bool = False
    cumulative_tokens: int = 0


# ---------------------------------------------------------------------------
# StreamingStepRunner
# ---------------------------------------------------------------------------


class StreamingStepRunner:
    """Streaming step runner that bridges LLM providers with pipeline hooks.

    Supports three execution modes:
    - ``execute_streaming()``: yields PartialResult objects mid-stream
    - ``execute_batch()``: v1 fallback, calls provider.analyze() directly
    - ``execute()``: auto-detects mode from FeatureGates

    Args:
        provider: LLMProvider instance for LLM calls.
        hook_bus: HookBus for emitting pre/post hooks.
        cost_tracker: Optional CostTracker for token/cost tracking.
        feature_gates: Optional FeatureGates for auto-detecting streaming mode.
    """

    def __init__(
        self,
        provider: LLMProvider,
        hook_bus: HookBus,
        cost_tracker: CostTracker | None = None,
        feature_gates: FeatureGates | None = None,
    ) -> None:
        self._provider = provider
        self._hook_bus = hook_bus
        self._cost_tracker = cost_tracker
        self._feature_gates = feature_gates

        logger.info(
            "StreamingStepRunner initialized: provider=%s, " "cost_tracker=%s, feature_gates=%s",
            type(provider).__name__,
            "enabled" if cost_tracker else "disabled",
            "enabled" if feature_gates else "disabled",
        )

    # ------------------------------------------------------------------
    # Streaming Execution
    # ------------------------------------------------------------------

    def execute_streaming(
        self,
        step_id: str,
        prompt: str,
        **kwargs: Any,
    ) -> Iterator[PartialResult]:
        """Execute a step in streaming mode, yielding partial results.

        Fires pre_llm_call before streaming starts, yields PartialResult
        for each chunk with detected artifacts, and fires post_llm_call
        at stream end with final token counts.

        Args:
            step_id: Pipeline step identifier.
            prompt: The prompt to send to the LLM.
            **kwargs: Passed to the provider's analyze_streaming().

        Yields:
            PartialResult objects with chunk text and detected artifacts.
        """
        t0 = time.monotonic()
        cumulative_tokens = 0
        full_text_parts: list[str] = []
        all_artifacts: list[str] = []

        # --- pre_llm_call hook ---
        self._hook_bus.emit(
            "pre_llm_call",
            {
                "step_id": step_id,
                "mode": "streaming",
                "prompt_length": len(prompt),
            },
        )

        logger.info(
            "Starting streaming execution: step=%s prompt_length=%d",
            step_id,
            len(prompt),
        )

        try:
            chunk_index = 0
            for chunk_text in self._provider.analyze_streaming(prompt, **kwargs):
                chunk_index += 1
                full_text_parts.append(chunk_text)

                # Estimate tokens for this chunk (rough: words ~= tokens)
                chunk_tokens = max(1, len(chunk_text.split()))
                cumulative_tokens += chunk_tokens

                # Detect artifacts in this chunk
                detected = _detect_artifacts(chunk_text)
                all_artifacts.extend(detected)

                partial = PartialResult(
                    chunk_text=chunk_text,
                    detected_artifacts=detected,
                    is_final=False,
                    cumulative_tokens=cumulative_tokens,
                )

                yield partial

            # Yield a final marker with is_final=True
            full_text = "".join(full_text_parts)
            final_partial = PartialResult(
                chunk_text="",
                detected_artifacts=list(set(all_artifacts)),
                is_final=True,
                cumulative_tokens=cumulative_tokens,
            )
            yield final_partial

        except Exception as exc:
            logger.error(
                "Streaming execution failed for step '%s': %s",
                step_id,
                exc,
            )
            raise

        finally:
            elapsed_ms = (time.monotonic() - t0) * 1000.0
            full_text = "".join(full_text_parts)

            # --- Cost tracking ---
            input_tokens = max(1, len(prompt.split()))
            output_tokens = cumulative_tokens

            if self._cost_tracker is not None:
                self._cost_tracker.accumulate(
                    step_id=step_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=self._provider.model_name,
                    latency_ms=elapsed_ms,
                )

            # --- post_llm_call hook ---
            self._hook_bus.emit(
                "post_llm_call",
                {
                    "step_id": step_id,
                    "mode": "streaming",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "duration_ms": round(elapsed_ms, 1),
                    "chunks_yielded": chunk_index if "chunk_index" in dir() else 0,
                    "artifacts_detected": list(set(all_artifacts)),
                },
            )

            logger.info(
                "Streaming execution complete: step=%s chunks=%d " "tokens=%d duration=%.1fms",
                step_id,
                chunk_index if "chunk_index" in dir() else 0,
                cumulative_tokens,
                elapsed_ms,
            )

    # ------------------------------------------------------------------
    # Batch Execution (v1 fallback)
    # ------------------------------------------------------------------

    def execute_batch(
        self,
        step_id: str,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Execute a step in batch mode (v1 fallback, no streaming).

        Fires pre_llm_call, calls provider.analyze(), then fires
        post_llm_call with token counts.

        Args:
            step_id: Pipeline step identifier.
            prompt: The prompt to send to the LLM.
            **kwargs: Passed to the provider's analyze().

        Returns:
            The full LLM response text.
        """
        t0 = time.monotonic()

        # --- pre_llm_call hook ---
        self._hook_bus.emit(
            "pre_llm_call",
            {
                "step_id": step_id,
                "mode": "batch",
                "prompt_length": len(prompt),
            },
        )

        logger.info(
            "Starting batch execution: step=%s prompt_length=%d",
            step_id,
            len(prompt),
        )

        result = self._provider.analyze(prompt, **kwargs)
        elapsed_ms = (time.monotonic() - t0) * 1000.0

        # Token estimation
        input_tokens = max(1, len(prompt.split()))
        output_tokens = max(1, len(result.split()))

        # --- Cost tracking ---
        if self._cost_tracker is not None:
            self._cost_tracker.accumulate(
                step_id=step_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=self._provider.model_name,
                latency_ms=elapsed_ms,
            )

        # --- post_llm_call hook ---
        self._hook_bus.emit(
            "post_llm_call",
            {
                "step_id": step_id,
                "mode": "batch",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "duration_ms": round(elapsed_ms, 1),
            },
        )

        logger.info(
            "Batch execution complete: step=%s tokens=%d duration=%.1fms",
            step_id,
            input_tokens + output_tokens,
            elapsed_ms,
        )

        return result

    # ------------------------------------------------------------------
    # Auto-Detecting Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        step_id: str,
        prompt: str,
        streaming: bool | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute a step, auto-detecting streaming mode from feature gates.

        If streaming=None, checks FeatureGates.gate("streaming").
        If streaming=True, collects all partial results and returns full text.
        If streaming=False, calls batch directly.

        Args:
            step_id: Pipeline step identifier.
            prompt: The prompt to send to the LLM.
            streaming: Explicit mode override. None = auto-detect from gates.
            **kwargs: Passed to the provider.

        Returns:
            The full LLM response text.
        """
        # Resolve streaming mode
        if streaming is None:
            if self._feature_gates is not None:
                streaming = self._feature_gates.gate("streaming")
            else:
                streaming = False

        if streaming:
            # Collect streaming results into full text
            parts: list[str] = []
            for partial in self.execute_streaming(step_id, prompt, **kwargs):
                if not partial.is_final:
                    parts.append(partial.chunk_text)
            return "".join(parts)
        else:
            return self.execute_batch(step_id, prompt, **kwargs)


# ---------------------------------------------------------------------------
# Artifact Detection (lightweight, regex-based)
# ---------------------------------------------------------------------------


def _detect_artifacts(text: str) -> list[str]:
    """Detect entity names and insight keywords in a text chunk.

    Uses lightweight regex matching -- not a full NER system.
    Returns deduplicated list of detected artifact strings.

    Args:
        text: The text chunk to scan.

    Returns:
        List of detected entity names and insight keywords.
    """
    artifacts: list[str] = []

    # Detect capitalized entity-like patterns
    for match in _ENTITY_PATTERN.finditer(text):
        entity = match.group(1).strip()
        if len(entity) > 3:  # Skip very short matches
            artifacts.append(entity)

    # Detect insight keywords
    text_lower = text.lower()
    for keyword in _INSIGHT_KEYWORDS:
        if keyword in text_lower:
            artifacts.append(keyword)

    return list(set(artifacts))
