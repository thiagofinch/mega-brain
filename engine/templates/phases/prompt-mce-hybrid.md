# Prompt MCE: Cross-Expert Hybrid Dossier Generation

> **version:** 1.0.0
> **type:** extraction-prompt
> **input:** 2+ expert DNA files + dossiers on the same theme
> **output:** HYBRID-{THEME}-{PERSONS}.md in knowledge/external/dossiers/hybrid/
> **template:** core/templates/knowledge/dossier-hybrid.md

---

## SYSTEM CONTEXT

You are a knowledge synthesis specialist. Your task is to create a HYBRID DOSSIER that cross-references perspectives from multiple experts on a single theme.

You will receive:
1. DNA entries (filosofias, heuristicas, frameworks, metodologias, modelos-mentais) from 2+ experts
2. Existing person dossiers or source compilations on the same theme
3. The theme name and scope

---

## EXTRACTION RULES

### Source Attribution
- Every factual claim MUST cite the expert and chunk/entry ID: `[chunk_{SOURCE_ID}_{CHUNK}]`
- Never paraphrase without attribution
- Preserve original quotes in "Citacoes Originais" section

### Convergence Detection
- Identify principles where 2+ experts agree
- Each convergence point must cite evidence from multiple experts
- Rank convergence by strength (all agree > most agree > two agree)

### Divergence Detection
- Identify where experts disagree or take different approaches
- Present both sides without choosing
- Note contextual factors that explain the divergence (ticket size, market, stage)

### Synthesis
- Create meta-insights that emerge from cross-pollination
- These must be DERIVED from documented positions, not invented
- Mark synthesis statements clearly as interpretive

---

## INPUT FORMAT

```
THEME: {theme_name}
EXPERTS: {expert_1}, {expert_2}, ...

--- EXPERT 1: {name} ---
DNA Entries:
{yaml entries from relevant layers}

Dossier/Source excerpts:
{relevant sections from existing dossiers}

--- EXPERT 2: {name} ---
DNA Entries:
{yaml entries from relevant layers}

Dossier/Source excerpts:
{relevant sections from existing dossiers}

[repeat for each expert]
```

---

## OUTPUT FORMAT

Follow the template structure from `core/templates/knowledge/dossier-hybrid.md`:

1. **TL;DR** — One paragraph synthesis
2. **Filosofia Central** — Collective "why" with expert quotes
3. **Perspectivas por Especialista** — Per-expert narrative with frameworks and heuristics
4. **Pontos de Convergencia** — Table of shared principles with evidence
5. **Pontos de Divergencia** — Table of disagreements with context
6. **Sintese Consolidada** — Meta-insight narrative
7. **Insights Acionaveis** — Ranked actionable takeaways
8. **Citacoes Originais** — Preserved original quotes
9. **Metadados** — Sources processed, version history

---

## QUALITY CRITERIA

| Criterion | Minimum |
|-----------|---------|
| Experts cited | 2+ |
| Convergence points with multi-expert evidence | 3+ |
| Divergence points documented | 1+ (if they exist) |
| Actionable insights | 3+ |
| Original quotes preserved | 2+ per expert |
| Every claim has chunk reference | 100% |
| Synthesis is DERIVED not invented | 100% |

---

## CONFIDENCE SCORING

- **ALTA (80-100%):** Specific methodology or framework applied, multiple experts converge
- **MEDIA (50-79%):** Heuristics applied with inference, partial framework coverage
- **BAIXA (20-49%):** Based on mental models or philosophy only, significant inference
- **N/A:** Topic not covered by available sources

---

## ANTI-HALLUCINATION RULES

1. If an expert has NO entries on the theme, say so explicitly — do not invent
2. If convergence is weak (only surface-level), downgrade confidence
3. If sources are insufficient for meaningful synthesis, produce a SPARSE dossier (density: 1) rather than hallucinating depth
4. Never attribute a position to an expert without a chunk reference

---

## FILENAME CONVENTION

```
HYBRID-{THEME}-{EXPERT1_CODE}-{EXPERT2_CODE}[-{EXPERT3_CODE}].md

Examples:
- HYBRID-VENDAS-AH-CG-JM.md
- HYBRID-HIRING-AH-RL-TSC.md
- HYBRID-OFFERS-AH-SO.md
```

Expert codes:
- AH = Alex Hormozi
- CG = Cole Gordon
- JM = Jeremy Miner
- JH = Jeremy Haynes
- JL = Jordan Lee
- LO = Liam Ottley
- SO = Sam Oven
- RL = Richard Linder
- TSC = The Scalable Company
- SVS = um sistema de vendas
