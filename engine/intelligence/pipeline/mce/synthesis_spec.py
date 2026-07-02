"""
synthesis_spec.py -- Synthesis Spec Pattern for Conclave Outputs
================================================================

Provides typed dataclasses and parse/validate/format functions for the
Synthesis Spec pattern.  This is the structured output format that
sintetizador-conclave MUST produce after integrating findings from the
pipeline debate + critico score + advogado-diabo attacks.

Architecture
------------
The Synthesis Spec replaces narrative summaries ("baseado nos achados...")
with concrete, actionable output.  Every spec item contains a file path,
an imperative action, a measurable metric, and acceptance criteria.

Data Flow::

    Agent Outputs (critico, advogado, pipeline)
                    |
                    v
    sintetizador-conclave produces raw text
                    |
                    v
    parse_spec(raw_text) -> SynthesisSpec
                    |
                    v
    validate_spec(spec) -> ValidationResult
                    |
                    v
    format_spec(spec) -> str (for coordinator consumption)

Public API
----------
- ``SynthesisSpec``       -- top-level synthesis dataclass
- ``SpecItem``            -- individual spec action item
- ``Finding``             -- agent finding with confidence
- ``ValidationResult``    -- validation outcome
- ``parse_spec()``        -- parse raw text into SynthesisSpec
- ``validate_spec()``     -- check all required fields present
- ``format_spec()``       -- format for coordinator consumption

Constraints
~~~~~~~~~~~
- stdlib only (no external deps).
- All fields validated at construction via ``__post_init__``.
- Anti-pattern: "baseado nos achados..." is explicitly rejected by validation.

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-3.2
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("mce.synthesis_spec")

# ---------------------------------------------------------------------------
# Anti-pattern phrases that trigger validation rejection
# ---------------------------------------------------------------------------

ANTI_PATTERN_PHRASES: tuple[str, ...] = (
    "baseado nos achados",
    "based on the findings",
    "conforme reportado",
    "as reported by",
    "de acordo com o que foi apresentado",
    "segundo os agentes",
    "os agentes indicaram que",
    "podemos concluir que",
    "a analise mostra que",
    "em resumo",
)


# ---------------------------------------------------------------------------
# Finding -- individual agent finding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """A single finding from an agent in the pipeline.

    Attributes:
        agent_id:   The agent that produced this finding.
        step:       MCE step number/name.
        outputs:    Concrete outputs produced (bullet list).
        confidence: Agent-reported confidence (0-100).
        gaps:       What is missing or uncertain.
    """

    agent_id: str
    step: str
    outputs: list[str]
    confidence: float
    gaps: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.agent_id:
            raise ValueError("Finding.agent_id must be non-empty")
        if not (0 <= self.confidence <= 100):
            raise ValueError(f"Finding.confidence must be 0-100, got {self.confidence}")


# ---------------------------------------------------------------------------
# SpecItem -- actionable spec entry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpecItem:
    """A single actionable specification item.

    Every spec item answers: WHAT file, WHAT action, HOW to measure,
    and WHAT constitutes acceptance.

    Attributes:
        file_path:           Target file or resource path.
        action:              Imperative action (CREATE, EDIT, DELETE, etc.).
        metric:              How to measure success.
        acceptance_criteria: Concrete criteria for acceptance.
    """

    file_path: str
    action: str
    metric: str
    acceptance_criteria: str

    def __post_init__(self) -> None:
        if not self.file_path:
            raise ValueError("SpecItem.file_path must be non-empty")
        if not self.action:
            raise ValueError("SpecItem.action must be non-empty")
        if not self.metric:
            raise ValueError("SpecItem.metric must be non-empty")
        if not self.acceptance_criteria:
            raise ValueError("SpecItem.acceptance_criteria must be non-empty")


# ---------------------------------------------------------------------------
# SynthesisSpec -- top-level synthesis output
# ---------------------------------------------------------------------------


@dataclass
class SynthesisSpec:
    """The complete Synthesis Spec output from sintetizador-conclave.

    Follows the mandatory template:
    [FINDINGS] -> [CROSS-AGENT ANALYSIS] -> [SPEC] -> [ACTIONS] -> [CONFIDENCE]

    Attributes:
        findings:             List of agent findings.
        cross_agent_analysis: Coordinator's cross-agent insight (convergence,
                              divergence, gaps, confidence delta).
        specs:                List of actionable SpecItems.
        actions:              Ordered list of imperative actions.
        confidence:           Final calibrated confidence (0-100).
        confidence_breakdown: Dict with calibration math.
        decision_status:      EMIT or ESCALATE.
        reversal_criteria:    IF/THEN triggers for reconsideration.
        topic:                The deliberation topic.
    """

    findings: list[Finding]
    cross_agent_analysis: str
    specs: list[SpecItem]
    actions: list[str]
    confidence: float
    confidence_breakdown: dict[str, float] = field(default_factory=dict)
    decision_status: str = "EMIT"
    reversal_criteria: list[str] = field(default_factory=list)
    topic: str = ""

    def __post_init__(self) -> None:
        if not (0 <= self.confidence <= 100):
            raise ValueError(f"SynthesisSpec.confidence must be 0-100, got {self.confidence}")
        if self.decision_status not in ("EMIT", "ESCALATE"):
            raise ValueError(
                f"decision_status must be EMIT or ESCALATE, " f"got {self.decision_status!r}"
            )


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Outcome of spec validation.

    Attributes:
        valid:    Whether the spec passes all checks.
        errors:   List of error messages (blocking).
        warnings: List of warning messages (non-blocking).
    """

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# validate_spec() -- check all required fields and anti-patterns
# ---------------------------------------------------------------------------


def validate_spec(spec: SynthesisSpec) -> ValidationResult:
    """Validate a SynthesisSpec for completeness and anti-pattern compliance.

    Checks:
    1. At least 1 finding present.
    2. cross_agent_analysis is non-empty.
    3. At least 1 spec item present.
    4. At least 1 action present.
    5. Confidence is within 0-100.
    6. No anti-pattern phrases in cross_agent_analysis.
    7. Confidence < 60% requires ESCALATE status.
    8. Each SpecItem has all 4 required fields.

    Args:
        spec: The SynthesisSpec to validate.

    Returns:
        ValidationResult with errors and warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Findings
    if not spec.findings:
        errors.append("[FINDINGS] section is empty -- at least 1 finding required")

    # 2. Cross-agent analysis
    if not spec.cross_agent_analysis or not spec.cross_agent_analysis.strip():
        errors.append(
            "[CROSS-AGENT ANALYSIS] is empty -- " "coordinator must add cross-agent insight"
        )

    # 3. Spec items
    if not spec.specs:
        errors.append("[SPEC] section is empty -- at least 1 spec item required")

    # 4. Actions
    if not spec.actions:
        errors.append("[ACTIONS] section is empty -- at least 1 action required")

    # 5. Confidence range
    if not (0 <= spec.confidence <= 100):
        errors.append(f"Confidence must be 0-100, got {spec.confidence}")

    # 6. Anti-pattern check on cross_agent_analysis
    analysis_lower = spec.cross_agent_analysis.lower() if spec.cross_agent_analysis else ""
    for phrase in ANTI_PATTERN_PHRASES:
        if phrase.lower() in analysis_lower:
            errors.append(
                f"Anti-pattern detected: '{phrase}' -- "
                "narrative summaries are PROHIBITED. "
                "Use concrete cross-agent analysis instead."
            )

    # Also check actions for anti-patterns
    for i, action in enumerate(spec.actions):
        action_lower = action.lower()
        for phrase in ANTI_PATTERN_PHRASES:
            if phrase.lower() in action_lower:
                errors.append(
                    f"Anti-pattern in action[{i}]: '{phrase}' -- "
                    "actions must be imperative, not narrative."
                )

    # 7. Escalation rule: confidence < 60 must ESCALATE
    if spec.confidence < 60 and spec.decision_status != "ESCALATE":
        errors.append(
            f"Confidence {spec.confidence}% < 60% requires "
            f"decision_status='ESCALATE', got '{spec.decision_status}'"
        )

    # 8. SpecItem completeness (validated at construction, but double-check)
    for i, item in enumerate(spec.specs):
        if not item.file_path:
            errors.append(f"spec[{i}].file_path is empty")
        if not item.action:
            errors.append(f"spec[{i}].action is empty")
        if not item.metric:
            errors.append(f"spec[{i}].metric is empty")
        if not item.acceptance_criteria:
            errors.append(f"spec[{i}].acceptance_criteria is empty")

    # Warnings
    if not spec.confidence_breakdown:
        warnings.append("confidence_breakdown is empty -- " "calibration math should be shown")

    if not spec.reversal_criteria:
        warnings.append("reversal_criteria is empty -- " "IF/THEN triggers are recommended")

    if spec.confidence >= 80 and len(spec.findings) < 2:
        warnings.append(
            f"Confidence {spec.confidence}% >= 80% with only "
            f"{len(spec.findings)} finding(s) -- "
            "high confidence requires multiple corroborating agents"
        )

    result = ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )

    logger.debug(
        "Validation result: valid=%s, errors=%d, warnings=%d",
        result.valid,
        len(errors),
        len(warnings),
    )
    return result


# ---------------------------------------------------------------------------
# format_spec() -- format for coordinator consumption
# ---------------------------------------------------------------------------


def format_spec(spec: SynthesisSpec) -> str:
    """Format a SynthesisSpec into the canonical text template.

    Produces the [FINDINGS] -> [CROSS-AGENT ANALYSIS] -> [SPEC] ->
    [ACTIONS] -> [CONFIDENCE] template that the coordinator consumes.

    Args:
        spec: The SynthesisSpec to format.

    Returns:
        Formatted string ready for coordinator consumption.
    """
    lines: list[str] = []

    # Topic header
    if spec.topic:
        lines.append(f"# Conclave Synthesis -- {spec.topic}")
    else:
        lines.append("# Conclave Synthesis")
    lines.append("")

    # [FINDINGS]
    lines.append("[FINDINGS]")
    for finding in spec.findings:
        lines.append(f"- Agent: {finding.agent_id}")
        lines.append(f"  Step: {finding.step}")
        lines.append("  Key outputs:")
        for output in finding.outputs:
            lines.append(f"    - {output}")
        lines.append(f"  Confidence: {finding.confidence}%")
        if finding.gaps:
            lines.append("  Gaps:")
            for gap in finding.gaps:
                lines.append(f"    - {gap}")
        lines.append("")

    # [CROSS-AGENT ANALYSIS]
    lines.append("[CROSS-AGENT ANALYSIS]")
    lines.append(spec.cross_agent_analysis)
    lines.append("")

    # [SPEC]
    lines.append("[SPEC]")
    for i, item in enumerate(spec.specs, 1):
        lines.append(f"{i}. File: {item.file_path}")
        lines.append(f"   Action: {item.action}")
        lines.append(f"   Metric: {item.metric}")
        lines.append(f"   Acceptance: {item.acceptance_criteria}")
    lines.append("")

    # [ACTIONS]
    lines.append("[ACTIONS]")
    for i, action in enumerate(spec.actions, 1):
        lines.append(f"{i}. {action}")
    lines.append("")

    # [CONFIDENCE]
    lines.append(f"[CONFIDENCE] {spec.confidence}%")
    if spec.confidence_breakdown:
        lines.append("Calibration Breakdown:")
        for key, value in spec.confidence_breakdown.items():
            sign = "+" if value >= 0 else ""
            lines.append(f"  - {key}: {sign}{value}%")
    lines.append("")

    # Decision status
    lines.append(f"Decision Status: {spec.decision_status}")

    # Reversal criteria
    if spec.reversal_criteria:
        lines.append("")
        lines.append("Reversal Criteria:")
        for criterion in spec.reversal_criteria:
            lines.append(f"- {criterion}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# parse_spec() -- parse raw text into SynthesisSpec
# ---------------------------------------------------------------------------

# Section header regex patterns
_SECTION_RE = re.compile(
    r"^\[(?:FINDINGS|CROSS-AGENT ANALYSIS|SPEC|ACTIONS|CONFIDENCE)\b",
    re.MULTILINE,
)


def _extract_section(text: str, header: str) -> str:
    """Extract content between a section header and the next section.

    Args:
        text:   The full spec text.
        header: Section header (e.g., "[FINDINGS]").

    Returns:
        Content between this header and the next, stripped.
    """
    start_pattern = re.escape(header)
    start_match = re.search(start_pattern, text)
    if not start_match:
        return ""

    start_pos = start_match.end()

    # Find the next section header after this one
    remaining = text[start_pos:]
    next_match = _SECTION_RE.search(remaining)
    if next_match:
        content = remaining[: next_match.start()]
    else:
        content = remaining

    return content.strip()


def _parse_findings(text: str) -> list[Finding]:
    """Parse the [FINDINGS] section into Finding objects.

    Expects format:
    - Agent: {agent_id}
      Step: {step}
      Key outputs:
        - {output}
      Confidence: {N}%
      Gaps:
        - {gap}

    Args:
        text: The [FINDINGS] section content.

    Returns:
        List of Finding objects.
    """
    findings: list[Finding] = []

    # Split on "- Agent:" boundaries
    blocks = re.split(r"(?=^- Agent:)", text, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        agent_match = re.search(r"Agent:\s*(.+)", block)
        step_match = re.search(r"Step:\s*(.+)", block)
        confidence_match = re.search(r"Confidence:\s*([\d.]+)%?", block)

        if not agent_match:
            continue

        agent_id = agent_match.group(1).strip()
        step = step_match.group(1).strip() if step_match else ""
        confidence = float(confidence_match.group(1)) if confidence_match else 0.0

        # Extract outputs (lines after "Key outputs:" indented with "- ")
        outputs: list[str] = []
        outputs_match = re.search(r"Key outputs:\s*\n((?:\s+- .+\n?)+)", block)
        if outputs_match:
            for line in outputs_match.group(1).strip().splitlines():
                line = line.strip()
                if line.startswith("- "):
                    outputs.append(line[2:].strip())

        # Extract gaps
        gaps: list[str] = []
        gaps_match = re.search(r"Gaps:\s*\n((?:\s+- .+\n?)+)", block)
        if gaps_match:
            for line in gaps_match.group(1).strip().splitlines():
                line = line.strip()
                if line.startswith("- "):
                    gaps.append(line[2:].strip())

        findings.append(
            Finding(
                agent_id=agent_id,
                step=step,
                outputs=outputs,
                confidence=confidence,
                gaps=gaps,
            )
        )

    return findings


def _parse_spec_items(text: str) -> list[SpecItem]:
    """Parse the [SPEC] section into SpecItem objects.

    Expects numbered format:
    1. File: {path}
       Action: {action}
       Metric: {metric}
       Acceptance: {criteria}

    Args:
        text: The [SPEC] section content.

    Returns:
        List of SpecItem objects.
    """
    items: list[SpecItem] = []

    # Split on numbered entries
    blocks = re.split(r"(?=^\d+\.\s)", text, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        file_match = re.search(r"File:\s*(.+)", block)
        action_match = re.search(r"Action:\s*(.+)", block)
        metric_match = re.search(r"Metric:\s*(.+)", block)
        accept_match = re.search(r"Acceptance:\s*(.+)", block)

        if not all([file_match, action_match, metric_match, accept_match]):
            continue

        items.append(
            SpecItem(
                file_path=file_match.group(1).strip(),
                action=action_match.group(1).strip(),
                metric=metric_match.group(1).strip(),
                acceptance_criteria=accept_match.group(1).strip(),
            )
        )

    return items


def _parse_actions(text: str) -> list[str]:
    """Parse the [ACTIONS] section into a list of action strings.

    Expects numbered format:
    1. {action}
    2. {action}

    Args:
        text: The [ACTIONS] section content.

    Returns:
        List of action strings.
    """
    actions: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        # Match numbered items: "1. action text"
        match = re.match(r"^\d+\.\s+(.+)$", line)
        if match:
            actions.append(match.group(1).strip())
    return actions


def _parse_confidence(text: str) -> tuple[float, dict[str, float]]:
    """Parse the [CONFIDENCE] section.

    Expects:
    [CONFIDENCE] 75%
    Calibration Breakdown:
      - Base (synthesis): 80%
      - Critico adjustment: -5%

    Args:
        text: The [CONFIDENCE] section content (or the line itself).

    Returns:
        Tuple of (confidence_float, breakdown_dict).
    """
    # The confidence value may be on the header line itself
    conf_match = re.search(r"([\d.]+)%", text)
    confidence = float(conf_match.group(1)) if conf_match else 0.0

    breakdown: dict[str, float] = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            # Parse "- Key: +10%" or "- Key: -5%"
            bd_match = re.match(r"^-\s+(.+?):\s*([+-]?[\d.]+)%", line)
            if bd_match:
                key = bd_match.group(1).strip()
                value = float(bd_match.group(2))
                breakdown[key] = value

    return confidence, breakdown


def parse_spec(raw_text: str) -> SynthesisSpec:
    """Parse raw text output from sintetizador-conclave into a SynthesisSpec.

    The raw text must contain the 5 mandatory sections:
    [FINDINGS], [CROSS-AGENT ANALYSIS], [SPEC], [ACTIONS], [CONFIDENCE]

    Args:
        raw_text: The raw text output from sintetizador-conclave.

    Returns:
        A SynthesisSpec populated from the parsed text.

    Raises:
        ValueError: If required sections are missing.
    """
    # Parse topic from header if present
    topic = ""
    topic_match = re.search(r"^#\s+Conclave Synthesis\s*--\s*(.+)$", raw_text, re.MULTILINE)
    if topic_match:
        topic = topic_match.group(1).strip()

    # Extract each section
    findings_text = _extract_section(raw_text, "[FINDINGS]")
    analysis_text = _extract_section(raw_text, "[CROSS-AGENT ANALYSIS]")
    spec_text = _extract_section(raw_text, "[SPEC]")
    actions_text = _extract_section(raw_text, "[ACTIONS]")

    # Confidence is special -- the value may be on the header line
    confidence_header_match = re.search(r"\[CONFIDENCE\]\s*([\d.]+)%", raw_text)
    confidence_section = _extract_section(raw_text, "[CONFIDENCE]")
    if confidence_header_match:
        confidence_section = confidence_header_match.group(0) + "\n" + confidence_section

    # Parse subsections
    findings = _parse_findings(findings_text)
    specs = _parse_spec_items(spec_text)
    actions = _parse_actions(actions_text)
    confidence, breakdown = _parse_confidence(confidence_section)

    # Parse decision status
    decision_status = "EMIT"
    status_match = re.search(r"Decision Status:\s*(EMIT|ESCALATE)", raw_text)
    if status_match:
        decision_status = status_match.group(1)

    # Parse reversal criteria
    reversal: list[str] = []
    reversal_match = re.search(r"Reversal Criteria:\s*\n((?:- .+\n?)+)", raw_text)
    if reversal_match:
        for line in reversal_match.group(1).strip().splitlines():
            line = line.strip()
            if line.startswith("- "):
                reversal.append(line[2:].strip())

    return SynthesisSpec(
        findings=findings,
        cross_agent_analysis=analysis_text,
        specs=specs,
        actions=actions,
        confidence=confidence,
        confidence_breakdown=breakdown,
        decision_status=decision_status,
        reversal_criteria=reversal,
        topic=topic,
    )
