"""
structured_output.py -- Structured Output Parsers for Conclave Agents
=====================================================================

Provides typed dataclasses and parse/validate functions for the structured
output formats used by critico and advogado-diabo agents in the Conclave
deliberation protocol.

Architecture
------------
Before this module, critico and advogado-diabo produced free-form markdown.
Now each agent MUST produce output matching a specific structured template.
This module parses that output into typed objects for downstream consumption
by sintetizador-conclave and the coordinator.

Data Flow::

    critico produces raw text
         |
         v
    parse_critico_output(raw) -> CriticoOutput
         |
         v
    validate_critico_output(output) -> ValidationResult
         |
         v
    sintetizador-conclave consumes typed object

    advogado-diabo produces raw text
         |
         v
    parse_advogado_output(raw) -> AdvogadoOutput
         |
         v
    validate_advogado_output(output) -> ValidationResult
         |
         v
    sintetizador-conclave consumes typed object

Public API
----------
- ``CriterionScore``           -- single criterion score for critico
- ``CriticoOutput``            -- full critico structured output
- ``AdvogadoSection``          -- single section from advogado
- ``AdvogadoOutput``           -- full advogado structured output
- ``OutputValidationResult``   -- validation outcome
- ``parse_critico_output()``   -- parse raw text into CriticoOutput
- ``parse_advogado_output()``  -- parse raw text into AdvogadoOutput
- ``validate_critico_output()``  -- validate completeness
- ``validate_advogado_output()`` -- validate completeness

Constraints
~~~~~~~~~~~
- stdlib only (no external deps).
- All fields validated at construction via ``__post_init__``.
- Every criterion/section produces ACTIONABLE feedback, not just scores.

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-3.2
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("mce.structured_output")


# ---------------------------------------------------------------------------
# Shared validation result
# ---------------------------------------------------------------------------


@dataclass
class OutputValidationResult:
    """Outcome of structured output validation.

    Attributes:
        valid:    Whether the output passes all checks.
        errors:   List of error messages (blocking).
        warnings: List of warning messages (non-blocking).
    """

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# CRITICO OUTPUT
# ═══════════════════════════════════════════════════════════════════════════

# The 5 canonical criteria IDs
CRITICO_CRITERIA: tuple[str, ...] = (
    "premissas_declaradas",
    "evidencias_rastreaveis",
    "logica_consistente",
    "cenarios_alternativos",
    "conflitos_resolvidos",
)

# Human-readable names
CRITICO_CRITERIA_NAMES: dict[str, str] = {
    "premissas_declaradas": "Premissas Declaradas",
    "evidencias_rastreaveis": "Evidencias Rastreaveis",
    "logica_consistente": "Logica Consistente",
    "cenarios_alternativos": "Cenarios Alternativos",
    "conflitos_resolvidos": "Conflitos Resolvidos",
}


@dataclass(frozen=True)
class CriterionScore:
    """Score and actionable feedback for a single critico criterion.

    Attributes:
        criterion_id:      Canonical criterion identifier.
        criterion_name:    Human-readable name.
        score:             Points awarded (0-20).
        max_score:         Maximum points possible (always 20).
        justification:     Why this score was given.
        actionable_feedback: Concrete action to improve this score.
        evidence_refs:     Source/chunk references supporting the score.
    """

    criterion_id: str
    criterion_name: str
    score: int
    max_score: int = 20
    justification: str = ""
    actionable_feedback: str = ""
    evidence_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.criterion_id:
            raise ValueError("criterion_id must be non-empty")
        if not (0 <= self.score <= self.max_score):
            raise ValueError(f"score must be 0-{self.max_score}, got {self.score}")


@dataclass
class CriticoOutput:
    """Full structured output from the critico agent.

    Template:
    [PREMISE AUDIT] -> [EVIDENCE CHAIN] -> [LOGIC GAPS] ->
    [ALTERNATIVE SCENARIOS] -> [VERDICT + SCORE]

    Attributes:
        input_evaluated: Description of what was evaluated.
        premise_audit:       Findings for premissas_declaradas criterion.
        evidence_chain:      Findings for evidencias_rastreaveis criterion.
        logic_gaps:          Findings for logica_consistente criterion.
        alternative_scenarios: Findings for cenarios_alternativos criterion.
        verdict_score:       Findings for conflitos_resolvidos criterion.
        total_score:         Sum of all criterion scores (0-100).
        verdict:             APROVAR | REVISAR | REJEITAR.
        gaps_for_sintetizador: Specific gaps for sintetizador to address.
    """

    input_evaluated: str
    premise_audit: CriterionScore
    evidence_chain: CriterionScore
    logic_gaps: CriterionScore
    alternative_scenarios: CriterionScore
    verdict_score: CriterionScore
    total_score: int
    verdict: str
    gaps_for_sintetizador: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.verdict not in ("APROVAR", "REVISAR", "REJEITAR"):
            raise ValueError(f"verdict must be APROVAR|REVISAR|REJEITAR, " f"got {self.verdict!r}")
        if not (0 <= self.total_score <= 100):
            raise ValueError(f"total_score must be 0-100, got {self.total_score}")

    @property
    def criteria(self) -> list[CriterionScore]:
        """All 5 criterion scores in canonical order."""
        return [
            self.premise_audit,
            self.evidence_chain,
            self.logic_gaps,
            self.alternative_scenarios,
            self.verdict_score,
        ]

    @property
    def calculated_total(self) -> int:
        """Sum of individual scores (for validation against total_score)."""
        return sum(c.score for c in self.criteria)


# ---------------------------------------------------------------------------
# validate_critico_output()
# ---------------------------------------------------------------------------


def validate_critico_output(output: CriticoOutput) -> OutputValidationResult:
    """Validate a CriticoOutput for completeness and consistency.

    Checks:
    1. All 5 criteria present with scores 0-20.
    2. Total score matches sum of criteria.
    3. Verdict matches score threshold.
    4. Each criterion has actionable_feedback.
    5. No criterion has empty justification.

    Args:
        output: The CriticoOutput to validate.

    Returns:
        OutputValidationResult with errors and warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Score ranges
    for criterion in output.criteria:
        if not (0 <= criterion.score <= criterion.max_score):
            errors.append(
                f"{criterion.criterion_name}: score {criterion.score} "
                f"outside 0-{criterion.max_score}"
            )

    # 2. Total consistency
    calculated = output.calculated_total
    if output.total_score != calculated:
        errors.append(f"total_score ({output.total_score}) != sum of criteria " f"({calculated})")

    # 3. Verdict-score consistency
    expected_verdict = _score_to_verdict(output.total_score)
    if output.verdict != expected_verdict:
        warnings.append(
            f"verdict '{output.verdict}' may not match score "
            f"{output.total_score} (expected '{expected_verdict}')"
        )

    # 4. Actionable feedback required
    for criterion in output.criteria:
        if not criterion.actionable_feedback:
            warnings.append(f"{criterion.criterion_name}: missing actionable_feedback")

    # 5. Justification required
    for criterion in output.criteria:
        if not criterion.justification:
            errors.append(
                f"{criterion.criterion_name}: missing justification "
                "(never give partial scores without justifying deductions)"
            )

    return OutputValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _score_to_verdict(score: int) -> str:
    """Map total score to expected verdict."""
    if score >= 70:
        return "APROVAR"
    if score >= 50:
        return "REVISAR"
    return "REJEITAR"


# ---------------------------------------------------------------------------
# parse_critico_output()
# ---------------------------------------------------------------------------


def parse_critico_output(raw: str) -> CriticoOutput:
    """Parse raw text from critico agent into a CriticoOutput.

    Expected sections:
    [PREMISE AUDIT], [EVIDENCE CHAIN], [LOGIC GAPS],
    [ALTERNATIVE SCENARIOS], [VERDICT + SCORE]

    Args:
        raw: Raw text output from critico agent.

    Returns:
        CriticoOutput populated from parsed text.

    Raises:
        ValueError: If required sections are missing.
    """
    # Extract input evaluated
    input_match = re.search(r"(?:Input Avaliado|Input Evaluated):\s*(.+)", raw)
    input_evaluated = input_match.group(1).strip() if input_match else ""

    # Parse each section
    section_map = {
        "[PREMISE AUDIT]": ("premissas_declaradas", "Premissas Declaradas"),
        "[EVIDENCE CHAIN]": ("evidencias_rastreaveis", "Evidencias Rastreaveis"),
        "[LOGIC GAPS]": ("logica_consistente", "Logica Consistente"),
        "[ALTERNATIVE SCENARIOS]": ("cenarios_alternativos", "Cenarios Alternativos"),
        "[VERDICT + SCORE]": ("conflitos_resolvidos", "Conflitos Resolvidos"),
    }

    criteria: dict[str, CriterionScore] = {}
    for header, (crit_id, crit_name) in section_map.items():
        section_text = _extract_critico_section(raw, header)
        score = _parse_section_score(section_text)
        justification = _parse_section_justification(section_text)
        feedback = _parse_section_feedback(section_text)
        refs = _parse_section_refs(section_text)

        criteria[crit_id] = CriterionScore(
            criterion_id=crit_id,
            criterion_name=crit_name,
            score=score,
            justification=justification,
            actionable_feedback=feedback,
            evidence_refs=refs,
        )

    # Parse total and verdict
    total_match = re.search(r"Total:\s*(\d+)/100", raw)
    total_score = (
        int(total_match.group(1)) if total_match else sum(c.score for c in criteria.values())
    )

    verdict_match = re.search(r"(?:Verdict|Veredicto):\s*(APROVAR|REVISAR|REJEITAR)", raw)
    verdict = verdict_match.group(1) if verdict_match else _score_to_verdict(total_score)

    # Parse gaps for sintetizador
    gaps: list[str] = []
    gaps_match = re.search(
        r"(?:Gaps|Gaps Identificados|Gaps for Sintetizador).*?\n((?:\s*\d+\..+\n?)+)",
        raw,
    )
    if gaps_match:
        for line in gaps_match.group(1).strip().splitlines():
            line = line.strip()
            numbered = re.match(r"^\d+\.\s+(.+)$", line)
            if numbered:
                gaps.append(numbered.group(1).strip())

    return CriticoOutput(
        input_evaluated=input_evaluated,
        premise_audit=criteria.get(
            "premissas_declaradas",
            _empty_criterion("premissas_declaradas", "Premissas Declaradas"),
        ),
        evidence_chain=criteria.get(
            "evidencias_rastreaveis",
            _empty_criterion("evidencias_rastreaveis", "Evidencias Rastreaveis"),
        ),
        logic_gaps=criteria.get(
            "logica_consistente",
            _empty_criterion("logica_consistente", "Logica Consistente"),
        ),
        alternative_scenarios=criteria.get(
            "cenarios_alternativos",
            _empty_criterion("cenarios_alternativos", "Cenarios Alternativos"),
        ),
        verdict_score=criteria.get(
            "conflitos_resolvidos",
            _empty_criterion("conflitos_resolvidos", "Conflitos Resolvidos"),
        ),
        total_score=total_score,
        verdict=verdict,
        gaps_for_sintetizador=gaps,
    )


def _empty_criterion(crit_id: str, crit_name: str) -> CriterionScore:
    """Create an empty criterion score (for missing sections)."""
    return CriterionScore(
        criterion_id=crit_id,
        criterion_name=crit_name,
        score=0,
        justification="Section missing from output",
        actionable_feedback="Provide this section in output",
    )


def _extract_critico_section(text: str, header: str) -> str:
    """Extract content between a critico section header and the next."""
    all_headers = [
        "[PREMISE AUDIT]",
        "[EVIDENCE CHAIN]",
        "[LOGIC GAPS]",
        "[ALTERNATIVE SCENARIOS]",
        "[VERDICT + SCORE]",
    ]

    escaped_header = re.escape(header)
    start_match = re.search(escaped_header, text)
    if not start_match:
        return ""

    start_pos = start_match.end()
    remaining = text[start_pos:]

    # Find next section header
    next_pos = len(remaining)
    for h in all_headers:
        if h == header:
            continue
        h_match = re.search(re.escape(h), remaining)
        if h_match and h_match.start() < next_pos:
            next_pos = h_match.start()

    # Also check for "Total:" or "Verdict:" as boundaries
    for boundary in (r"^Total:", r"^Verdict:", r"^Veredicto:", r"^Gaps"):
        b_match = re.search(boundary, remaining, re.MULTILINE)
        if b_match and b_match.start() < next_pos:
            next_pos = b_match.start()

    return remaining[:next_pos].strip()


def _parse_section_score(text: str) -> int:
    """Extract score from a section (e.g., '15/20' or 'Score: 15')."""
    match = re.search(r"(\d+)/20", text)
    if match:
        return int(match.group(1))
    match = re.search(r"Score:\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return 0


def _parse_section_justification(text: str) -> str:
    """Extract justification from a section."""
    match = re.search(r"(?:Justificativa|Justification):\s*(.+)", text)
    if match:
        return match.group(1).strip()
    # Fallback: first non-empty line after score
    lines = text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if line and not re.match(r"^\d+/20", line) and not line.startswith("Score:"):
            return line
    return ""


def _parse_section_feedback(text: str) -> str:
    """Extract actionable feedback from a section."""
    match = re.search(r"(?:Actionable Feedback|Acao|Action|Feedback):\s*(.+)", text)
    if match:
        return match.group(1).strip()
    return ""


def _parse_section_refs(text: str) -> list[str]:
    """Extract evidence references (chunk_ids) from a section."""
    refs: list[str] = []
    # Match patterns like [IM-001-015], [MEET-0050], etc.
    refs = re.findall(r"\[([A-Z]+-\d+(?:-\d+)?)\]", text)
    return refs


# ═══════════════════════════════════════════════════════════════════════════
# ADVOGADO-DIABO OUTPUT
# ═══════════════════════════════════════════════════════════════════════════

# The 4 canonical section IDs
ADVOGADO_SECTIONS: tuple[str, ...] = (
    "weakest_premise",
    "undiscussed_risk",
    "regret_scenario",
    "ignored_alternative",
)


@dataclass(frozen=True)
class AdvogadoSection:
    """A single section from advogado-diabo's structured output.

    Each section has: claim, evidence_against, confidence, action_if_right.

    Attributes:
        section_id:       Canonical section identifier.
        section_name:     Human-readable name.
        claim:            The claim or assertion being made.
        evidence_against: Evidence that supports this attack.
        confidence:       How confident the advogado is in this attack (0-100).
        action_if_right:  What should happen if this attack is correct.
    """

    section_id: str
    section_name: str
    claim: str
    evidence_against: str = ""
    confidence: float = 0.0
    action_if_right: str = ""

    def __post_init__(self) -> None:
        if not self.section_id:
            raise ValueError("section_id must be non-empty")
        if not self.claim:
            raise ValueError("claim must be non-empty")
        if not (0 <= self.confidence <= 100):
            raise ValueError(f"confidence must be 0-100, got {self.confidence}")


@dataclass
class AdvogadoOutput:
    """Full structured output from advogado-diabo.

    Template:
    [WEAKEST PREMISE] -> [UNDISCUSSED RISK] -> [REGRET SCENARIO] ->
    [IGNORED ALTERNATIVE] -> [ATTACK VERDICT]

    Attributes:
        input_evaluated:     What decision/position is being attacked.
        weakest_premise:     The single weakest assumption.
        undiscussed_risk:    Risk nobody mentioned.
        regret_scenario:     12-month worst-case narrative.
        ignored_alternative: Unconsidered option.
        attack_verdict:      Overall assessment of vulnerability.
        overall_vulnerability: Score 0-100 (how vulnerable is the position).
    """

    input_evaluated: str
    weakest_premise: AdvogadoSection
    undiscussed_risk: AdvogadoSection
    regret_scenario: AdvogadoSection
    ignored_alternative: AdvogadoSection
    attack_verdict: str = ""
    overall_vulnerability: float = 0.0

    def __post_init__(self) -> None:
        if not (0 <= self.overall_vulnerability <= 100):
            raise ValueError(
                f"overall_vulnerability must be 0-100, " f"got {self.overall_vulnerability}"
            )

    @property
    def sections(self) -> list[AdvogadoSection]:
        """All 4 sections in canonical order."""
        return [
            self.weakest_premise,
            self.undiscussed_risk,
            self.regret_scenario,
            self.ignored_alternative,
        ]


# ---------------------------------------------------------------------------
# validate_advogado_output()
# ---------------------------------------------------------------------------


def validate_advogado_output(output: AdvogadoOutput) -> OutputValidationResult:
    """Validate an AdvogadoOutput for completeness.

    Checks:
    1. All 4 mandatory sections present with non-empty claims.
    2. Each section has evidence_against.
    3. Each section has action_if_right.
    4. Overall vulnerability is within range.
    5. Attack verdict is non-empty.

    Args:
        output: The AdvogadoOutput to validate.

    Returns:
        OutputValidationResult with errors and warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. All sections have claims
    for section in output.sections:
        if not section.claim:
            errors.append(
                f"{section.section_name}: claim is empty -- " "every section MUST have a claim"
            )

    # 2. Evidence against
    for section in output.sections:
        if not section.evidence_against:
            warnings.append(f"{section.section_name}: evidence_against is empty")

    # 3. Action if right
    for section in output.sections:
        if not section.action_if_right:
            warnings.append(f"{section.section_name}: action_if_right is empty")

    # 4. Vulnerability range
    if not (0 <= output.overall_vulnerability <= 100):
        errors.append(
            f"overall_vulnerability must be 0-100, " f"got {output.overall_vulnerability}"
        )

    # 5. Attack verdict
    if not output.attack_verdict:
        warnings.append("attack_verdict is empty")

    return OutputValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# parse_advogado_output()
# ---------------------------------------------------------------------------


def parse_advogado_output(raw: str) -> AdvogadoOutput:
    """Parse raw text from advogado-diabo into an AdvogadoOutput.

    Expected sections:
    [WEAKEST PREMISE], [UNDISCUSSED RISK], [REGRET SCENARIO],
    [IGNORED ALTERNATIVE], [ATTACK VERDICT]

    Args:
        raw: Raw text output from advogado-diabo.

    Returns:
        AdvogadoOutput populated from parsed text.
    """
    # Extract input evaluated
    input_match = re.search(r"(?:Input|Decision|Position):\s*(.+)", raw)
    input_evaluated = input_match.group(1).strip() if input_match else ""

    # Parse each section
    section_headers = {
        "[WEAKEST PREMISE]": ("weakest_premise", "Premissa Mais Fragil"),
        "[UNDISCUSSED RISK]": ("undiscussed_risk", "Risco Nao Discutido"),
        "[REGRET SCENARIO]": ("regret_scenario", "Cenario de Arrependimento"),
        "[IGNORED ALTERNATIVE]": ("ignored_alternative", "Alternativa Ignorada"),
    }

    sections: dict[str, AdvogadoSection] = {}
    for header, (sec_id, sec_name) in section_headers.items():
        section_text = _extract_advogado_section(raw, header)
        claim = _parse_advogado_claim(section_text)
        evidence = _parse_advogado_evidence(section_text)
        confidence = _parse_advogado_confidence(section_text)
        action = _parse_advogado_action(section_text)

        sections[sec_id] = AdvogadoSection(
            section_id=sec_id,
            section_name=sec_name,
            claim=claim or f"[Missing {sec_name}]",
            evidence_against=evidence,
            confidence=confidence,
            action_if_right=action,
        )

    # Parse attack verdict
    verdict_text = _extract_advogado_section(raw, "[ATTACK VERDICT]")
    attack_verdict = verdict_text.strip() if verdict_text else ""

    # Parse overall vulnerability
    vuln_match = re.search(r"(?:Vulnerability|Vulnerabilidade):\s*([\d.]+)%?", raw)
    vulnerability = float(vuln_match.group(1)) if vuln_match else 0.0

    return AdvogadoOutput(
        input_evaluated=input_evaluated,
        weakest_premise=sections.get(
            "weakest_premise",
            _empty_advogado_section("weakest_premise", "Premissa Mais Fragil"),
        ),
        undiscussed_risk=sections.get(
            "undiscussed_risk",
            _empty_advogado_section("undiscussed_risk", "Risco Nao Discutido"),
        ),
        regret_scenario=sections.get(
            "regret_scenario",
            _empty_advogado_section("regret_scenario", "Cenario de Arrependimento"),
        ),
        ignored_alternative=sections.get(
            "ignored_alternative",
            _empty_advogado_section("ignored_alternative", "Alternativa Ignorada"),
        ),
        attack_verdict=attack_verdict,
        overall_vulnerability=vulnerability,
    )


def _empty_advogado_section(sec_id: str, sec_name: str) -> AdvogadoSection:
    """Create a placeholder section for missing output."""
    return AdvogadoSection(
        section_id=sec_id,
        section_name=sec_name,
        claim=f"[Missing {sec_name}]",
    )


def _extract_advogado_section(text: str, header: str) -> str:
    """Extract content between an advogado section header and the next."""
    all_headers = [
        "[WEAKEST PREMISE]",
        "[UNDISCUSSED RISK]",
        "[REGRET SCENARIO]",
        "[IGNORED ALTERNATIVE]",
        "[ATTACK VERDICT]",
    ]

    escaped = re.escape(header)
    start_match = re.search(escaped, text)
    if not start_match:
        return ""

    start_pos = start_match.end()
    remaining = text[start_pos:]

    next_pos = len(remaining)
    for h in all_headers:
        if h == header:
            continue
        h_match = re.search(re.escape(h), remaining)
        if h_match and h_match.start() < next_pos:
            next_pos = h_match.start()

    return remaining[:next_pos].strip()


def _parse_advogado_claim(text: str) -> str:
    """Extract the main claim from an advogado section."""
    match = re.search(r"(?:Claim|Se\s)(.+?)(?:\n|$)", text)
    if match:
        return match.group(0).strip()
    # Fallback: first substantial line
    for line in text.strip().splitlines():
        line = line.strip()
        if line and len(line) > 20:
            return line
    return text.strip()[:200] if text.strip() else ""


def _parse_advogado_evidence(text: str) -> str:
    """Extract evidence_against from an advogado section."""
    match = re.search(
        r"(?:Evidence Against|Evidencia|Evidence):\s*(.+?)(?:\n\n|\n(?=[A-Z])|\Z)",
        text,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    return ""


def _parse_advogado_confidence(text: str) -> float:
    """Extract confidence from an advogado section."""
    match = re.search(r"Confid(?:ence|encia):\s*([\d.]+)%?", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    # Check probability field (legacy format)
    match = re.search(r"Probabilidade:\s*(Alta|Media|Baixa)", text)
    if match:
        mapping = {"Alta": 80.0, "Media": 50.0, "Baixa": 20.0}
        return mapping.get(match.group(1), 50.0)
    return 50.0  # default to medium confidence


def _parse_advogado_action(text: str) -> str:
    """Extract action_if_right from an advogado section."""
    match = re.search(
        r"(?:Action if Right|Acao se Correto|Action):\s*(.+?)(?:\n\n|\Z)",
        text,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    return ""
