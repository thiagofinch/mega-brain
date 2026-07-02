---
paths:
  - "squads/design-ops/**"
  - "engine/intelligence/pipeline/**"
  - "engine/intelligence/extract/**"
  - "engine/intelligence/rag/**"
---

# Extraction Pipeline — NO FALLBACKS (NON-NEGOTIABLE)

**Origin:** founder directive 2026-05-02. Promoted from "nada é FIXED" (handoff 2026-05-02-extract-canonical-design-md-handoff.md) → ABSOLUTE RULE.

## Rule

**Extractors and extract-side builders (`squads/design-ops/scripts/extract-from-url/**`) MUST NOT emit fixed/hardcoded fallback values when extraction yields no signal.** They emit `null  # extraction_gap(...)` markers OR derived-from-brand-signals values, never universal defaults.

**Coverage from fallbacks is FALSE COVERAGE — it produces false positives downstream.**

## Why

1. **False positives corrupt data.** A scaffold showing `nav-height: "64px"` when the brand never declared a nav height is a lie. Consumers read it as authoritative and propagate the lie.
2. **Fallbacks belong to the application/render layer, not the extraction layer.** `apps/design`, `apps/mega-brain-squad-design`, render contracts — those are the right places for "if value missing, use shadcn-ui baseline 64px". The extractor's job is to record what was *actually* on the page.
3. **Structured extraction gaps are honest.** `null  # extraction_gap(...)` tells the consumer (human or LLM) "this slot is unfilled — decide". A fixed default tells the consumer "this is the brand's value" and that's wrong.
4. **Coverage % is a quality signal, not a vanity metric.** Inflating coverage with fallbacks makes the metric meaningless. We can no longer distinguish "well-extracted brand" from "brand that just got generic shadcn defaults stamped on it."

## What's allowed (NOT fallbacks)

- **Extracted values from raw inputs** (CSS, HTML, sidecars).
- **Aliased values from extracted brand swatches** (`text` → `foreground` when `text` was extracted).
- **Derivations from EXTRACTED brand signals** (`primary-deep` = `adjustLum(primary, -32)` is OK because `primary` was extracted from THIS brand).
- **Pipeline policy** (`asset_rule`, `accessibility_rule`, `priority_order` — these are ADR-022 v2 contract, not brand-specific).
- **Structured extraction gaps** (`null  # extraction_gap(...)`) when a slot can't be derived from extracted signals.

## What's forbidden

- **Universal hex defaults** ("#2f7613" for success, "#6a9bcc" for info).
- **Universal scale defaults** (Tailwind spacing 0/1/2/3/.../32 stamped on a brand that yielded zero spacing).
- **Universal token defaults** (`btn-height: "40px"`, `nav-height: "64px"`, `container-max: "1280px"`).
- **Generic CTA verbs** ("Get started", "Learn more", "Talk to us").
- **shadcn-ui baseline scales** for shadows/elevation/motion/rounded when brand yielded nothing.
- **Synthesized hex via color-mix** when no hover state was extracted.
- **Padding/spacing from "common DS conventions"** when brand has no spacing scale.

## What's the right pattern

```js
// WRONG — universal fallback
const btnHeight = primary.height || buttonProps["height"]?.most_common || "40px";

// RIGHT — emit only what was extracted, structured gap otherwise
const btnHeight = primary.height || buttonProps["height"]?.most_common;
lines.push(`  btn-height: ${v(btnHeight, "brand_primitives.btn-height — extracted button height unavailable")}`);
```

## Where fallbacks DO belong

- `apps/design/src/lib/design-skin.js` — when consuming a `DESIGN.md`/`preview.json` and a slot is null/missing, the renderer can apply scoped runtime fallback without rewriting source truth.
- `packages/@megabrain/design-tokens-base` — exports a baseline token set that consumers compose with brand overrides.
- Component-level CSS (`globals.css`) — Tailwind/shadcn defaults live in the framework layer.

## Consequence — coverage % must reflect REAL extraction quality

Brand stress test post-removal-of-fallbacks SHOULD show coverage drop for brands without raw inputs (TOKENS_ONLY). That drop is **the truth**. Pursuing 100% coverage by faking values is anti-quality.

## Reference

- Original directive: 2026-05-02 (handoff `docs/sessions/2026-05/2026-05-02-extract-canonical-design-md-handoff.md`)
- Reinforcement: 2026-05-02 lote 6 chat (user message: "na extracao nao devemos ter fallback ... nada de fallback na extracao pq se nao vai gerar falsos positivos ... fallback é hardcoded na aplicacao")
- Anti-pattern example: `.tmp/repair-generated-design-bundles.cjs` — manually edits brand bundles with hardcoded headlines/leads/CTAs. NEVER reproduce this pattern in the extractor.
