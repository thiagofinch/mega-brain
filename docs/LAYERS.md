# Mega Brain Layer System

> **Version:** 1.0.0
> **Purpose:** Define file classification rules for distribution, packaging, and privacy
> **Audience:** Any contributor, maintainer, or user adding new files to the repository

---

## Quick Reference

| Layer | Name | Git Status | Distribution | Who Uses It |
|-------|------|-----------|-------------|-------------|
| **L1** | Core | Tracked | Shipped in the repo | Everyone — engine foundation |
| **L2** | Knowledge Content | Tracked | Shipped in the repo | Everyone — populated knowledge base |
| **L3** | Personal | Gitignored | Local only / personal backup | Individual user only |
| **NEVER** | Secrets | Gitignored | Never shared anywhere | Nobody |
| **DELETE** | Obsolete | N/A | Remove from repo | N/A |
| **REVIEW** | Unclear | Varies | Needs human decision | Pending classification |

---

## Layer Definitions

### L1 — Core (engine foundation)

**Purpose:** The engine that powers Mega Brain. Distributed as `@thiagofinch/mega-brain`. Anyone with the repo can install and use this to build their own knowledge management system.

**Git status:** Fully tracked
**Distribution:** Shipped in the repo — part of the complete product
**Who uses it:** All users as the foundation layer

**What belongs in L1:**
- Core processing engine (`engine/`)
- CLI binaries (`bin/`)
- Claude Code integration templates (`.claude/`)
- Conclave (collaborative agent templates) (`agents/conclave/`)
- Agent templates (`agents/_templates/`)
- Documentation (`docs/`)
- Empty structure markers (`.gitkeep` files anywhere)

**Real examples from Phase 7 audit:**
```
engine/                          → L1 (Core engine)
engine/tasks/                    → L1 (Core engine)
engine/intelligence/audit_layers.py → L1 (Core engine)
bin/                           → L1 (Core engine)
.claude/                       → L1 (Core engine)
.claude/rules/RULE-GROUP-1.md  → L1 (Core engine)
agents/conclave/               → L1 (Core engine)
docs/                          → L1 (Core engine)
inbox/.gitkeep                 → L1 (Empty structure marker)
knowledge/external/dossiers/persons/.gitkeep → L1 (Empty structure marker)
agents/external/.gitkeep          → L1 (Empty structure marker)
```

**Key rule:** `.gitkeep` files are always L1, regardless of what directory they're in. They mark where populated content will live but contain no personal data.

---

### L2 — Knowledge Content (populated content)

**Purpose:** Content that has been generated through the Mega Brain pipeline — actual knowledge, agent personalities, dossiers, playbooks. The cloned repository already ships with this content as part of the complete product.

**Git status:** Tracked
**Distribution:** Shipped in the repo — part of the complete product
**Who uses it:** All users; populated as the pipeline runs and the knowledge base grows

**What belongs in L2:**
- Populated mind clone agents (`agents/external/` with actual content)
- Populated cargo agents (`agents/cargo/` with actual profiles)
- Knowledge dossiers (`knowledge/external/dossiers/`)
- Knowledge playbooks (`knowledge/external/playbooks/`)
- DNA knowledge base (`knowledge/external/dna/`)
- Knowledge sources (`knowledge/external/sources/`)
- Pipeline artifacts with extracted knowledge (`artifacts/insights/`, `artifacts/chunks/`, `artifacts/extractions/`)

**Real examples from Phase 7 audit:**
```
agents/external/                        → L2 (Knowledge content — when populated)
agents/cargo/                        → L2 (Knowledge content — when populated)
knowledge/external/dossiers/persons/          → L2 (Knowledge content)
knowledge/external/dossiers/themes/           → L2 (Knowledge content)
knowledge/external/playbooks/                 → L2 (Knowledge content)
knowledge/external/dna/                       → L2 (Knowledge content)
knowledge/external/sources/                   → L2 (Knowledge content)
artifacts/insights/                  → L2 (Knowledge content)
artifacts/chunks/                    → L2 (Knowledge content)
```

**Key rule:** L2 is a superset of L1. An L2 distribution includes all L1 content plus the populated knowledge content. If a directory contains only a `.gitkeep`, it is classified as L1 (empty structure).

---

### L3 — Personal (never distributed)

**Purpose:** User-generated content that is specific to one person's workflow — raw source materials, processing logs, session history, company-specific data. Never leaves the local machine except in personal backups.

**Git status:** Gitignored (not committed to any shared repo)
**Distribution:** Local backup only — never shared
**Who uses it:** The individual user only — this is their private data

**What belongs in L3:**
- Raw input materials (`inbox/`)
- Processing and session logs (`logs/`)
- Session history (`.claude/sessions/`)
- Mission control state (`.claude/mission-control/`)
- Company-specific data (`agents/sua-empresa/`)

**Real examples from Phase 7 audit:**
```
inbox/                         → L3 (Personal data)
inbox/alex-hormozi/            → L3 (Personal data)
inbox/my-video-transcript.txt  → L3 (Personal data)
logs/                          → L3 (Personal data)
logs/batches/BATCH-001.md      → L3 (Personal data)
.claude/sessions/              → L3 (Personal data)
.claude/mission-control/       → L3 (Personal data)
agents/sua-empresa/            → L3 (Personal data)
```

**Key rule:** L3 content is the "input" and "runtime state" of your system. It is valuable to you personally but meaningless (or sensitive) to others. Always gitignored — only exists in personal backups.

---

### NEVER — Secrets and Credentials

**Purpose:** Files that must never be committed to any git repository, shared, or distributed under any circumstances. These contain credentials, API keys, or sensitive configuration that could compromise security.

**Git status:** Always gitignored
**Distribution:** Never — not even in personal backups if avoidable
**Who uses it:** Nobody should see these except the owner's local machine

**What belongs in NEVER:**
- Environment files (`.env`, `.env.local`, `.env.production`)
- API keys and credentials (`credentials.json`, `token.json`)
- Certificate files (`*.key`, `*.pem`, `*.secret`)
- MCP configuration with embedded tokens (`.mcp.json`)
- Local settings overrides (`settings.local.json`)

**Real examples from Phase 7 audit:**
```
.env                           → NEVER (Secrets/sensitive config)
.env.local                     → NEVER (Secrets/sensitive config)
.env.example                   → NEVER (Secrets/sensitive config — may contain patterns)
.mcp.json                      → NEVER (Secrets/sensitive config)
credentials.json               → NEVER (Secrets/sensitive config)
token.json                     → NEVER (Secrets/sensitive config)
settings.local.json            → NEVER (Secrets/sensitive config)
*.key                          → NEVER (Certificate/key file)
*.pem                          → NEVER (Certificate file)
```

**Key rule:** If a file contains or could contain API keys, tokens, passwords, or private keys — it is NEVER. When in doubt, classify as NEVER rather than risk exposing credentials.

---

### DELETE — Obsolete Content

**Purpose:** Files and directories that were once useful but are now superseded, abandoned, or replaced by newer implementations. These should be removed from the repository.

**Git status:** Should be removed via `git rm`
**Distribution:** Remove everywhere
**Identified items:** See `docs/audit/AUDIT-REPORT.md` for current delete candidates

**What belongs in DELETE:**
- Old agent implementations replaced by newer versions (e.g., `finance-agent`, `talent-agent`)
- Superseded scripts replaced by better versions
- Empty archived directories with no value
- Duplicate files replaced by canonical versions

**Real examples from Phase 7 audit (10 items identified):**
```
archive/*/finance-agent/       → DELETE (Obsolete — replaced by agents/cargo/)
archive/*/talent-agent/        → DELETE (Obsolete — replaced by agents/cargo/)
```

**Key rule:** DELETE is determined by context, not just file type. Run `python3 engine/intelligence/audit_layers.py` to get current delete candidates. Review before deleting — some archives may have historical value.

---

### REVIEW — Needs Human Classification

**Purpose:** Files that the automated classifier could not confidently assign to a layer. These require a human decision based on context.

**Git status:** Varies — depends on final classification
**Distribution:** Cannot be determined until classified
**Scale:** 12,183 items in Phase 7 audit (58.6% of repo — mostly `.planning/`, IDE config, system files)

**Common REVIEW candidates:**
- IDE configuration (`.vscode/`, `.cursor/`, `.windsurf/`)
- Root-level project files (`README.md`, `package.json`, `requirements.txt`)
- Planning and development artifacts (`.planning/`)
- Unrecognized directory structures
- Files in mixed-use directories

**Real examples from Phase 7 audit:**
```
.cursor/                       → REVIEW (IDE config — probably L1 if committed)
.planning/                     → REVIEW (Planning docs — L1 for the GSD system)
README.md                      → REVIEW (Root readme — L1 if public-facing)
package.json                   → REVIEW (Project config — L1 for npm)
requirements.txt               → REVIEW (Python deps — L1 if needed)
.gitignore                     → REVIEW (Already tracked — probably L1)
```

**Key rule:** REVIEW is not a final classification — it is a signal to stop and decide. Apply the decision flowchart below, or consult the team if still unclear.

---

## Classification Criteria

| Criteria | L1 | L2 | L3 | NEVER | DELETE | REVIEW |
|----------|----|----|----|----|--------|--------|
| Contains API keys or tokens | | | | YES | | |
| Is an obsolete/replaced implementation | | | | | YES | |
| Generated by user's pipeline (personal data) | | | YES | | | |
| Contains user-specific business content | | | YES | | | |
| Populated knowledge (dossiers, playbooks) | | YES | | | | |
| Core engine code | YES | | | | | |
| Empty structure marker (`.gitkeep`) | YES | | | | | |
| Claude Code integration | YES | | | | | |
| Cannot determine without context | | | | | | YES |

---

## Decision Flowchart

```
New file or directory — what layer does it belong in?
│
├── Does it contain secrets, API keys, tokens, or credentials?
│   YES → NEVER
│   NO  ↓
│
├── Is it superseded, abandoned, or explicitly marked obsolete?
│   YES → DELETE
│   NO  ↓
│
├── Is it user-generated content (inbox, logs, sessions, company data)?
│   YES → L3
│   NO  ↓
│
├── Is it populated knowledge (dossiers, playbooks, DNA, artifacts)?
│   YES → L2
│   NO  ↓
│
├── Is it a .gitkeep file?
│   YES → L1 (Empty structure marker — always L1)
│   NO  ↓
│
├── Is it core engine code, CLI, Claude integration, or documentation?
│   YES → L1
│   NO  ↓
│
└── Cannot determine → REVIEW (assign human to make the call)
```

---

## How to Classify a New File

Follow these steps in order — stop at the first match:

**Step 1: Check NEVER patterns**
- Does the filename match: `.env`, `*.key`, `*.pem`, `*.secret`, `credentials.json`, `token.json`, `settings.local.json`, `.mcp.json`?
- Does the content contain API keys, tokens, or passwords?
- If YES → classify as **NEVER** and ensure it's in `.gitignore`

**Step 2: Check DELETE patterns**
- Is this file/directory in `DELETE_PATTERNS` from `audit_layers.py`?
- Is it explicitly superseded by a newer implementation?
- If YES → classify as **DELETE** and schedule for `git rm`

**Step 3: Check L3 patterns**
- Does the path start with: `inbox/`, `logs/`, `.claude/sessions/`, `.claude/mission-control/`, `agents/sua-empresa/`?
- If YES → classify as **L3** (unless it's a `.gitkeep`, which is L1)

**Step 4: Check L2 patterns**
- Does the path start with: `agents/external/`, `agents/cargo/`, `knowledge/external/dossiers/`, `knowledge/external/playbooks/`, `knowledge/external/dna/`, `knowledge/external/sources/`, `artifacts/insights/`, `artifacts/chunks/`, `artifacts/extractions/`?
- If YES → classify as **L2** (unless it's a `.gitkeep` or empty directory, which is L1)

**Step 5: Check L1 patterns**
- Does the path start with: `engine/`, `bin/`, `.claude/`, `agents/conclave/`, `agents/_templates/`, `docs/`?
- Is it a `.gitkeep` file anywhere in the repo?
- If YES → classify as **L1**

**Step 6: Apply REVIEW**
- If none of the above matched, classify as **REVIEW**
- Open a discussion or consult the classification criteria table above
- Document the decision and add it to `audit_layers.py` to prevent future ambiguity

---

## Path Examples Quick Reference

These are real paths from the Phase 7 audit with confirmed classifications:

| Path | Layer | Reason |
|------|-------|--------|
| `engine/` | L1 | Core engine |
| `engine/tasks/HO-TP-001.md` | L1 | Core engine |
| `engine/intelligence/audit_layers.py` | L1 | Core engine |
| `bin/` | L1 | Core engine |
| `.claude/` | L1 | Core engine |
| `.claude/rules/RULE-GROUP-1.md` | L1 | Core engine |
| `agents/conclave/` | L1 | Core engine |
| `docs/` | L1 | Core engine |
| `docs/LAYERS.md` | L1 | Core engine documentation |
| `inbox/.gitkeep` | L1 | Empty structure marker |
| `knowledge/external/dossiers/persons/.gitkeep` | L1 | Empty structure marker |
| `agents/external/.gitkeep` | L1 | Empty structure marker |
| `knowledge/external/dossiers/persons/ALEX-HORMOZI.md` | L2 | Populated content |
| `knowledge/external/playbooks/SALES-PLAYBOOK.md` | L2 | Populated content |
| `knowledge/external/dna/` | L2 | Populated content |
| `agents/external/ALEX-HORMOZI/` | L2 | Knowledge content |
| `artifacts/insights/` | L2 | Knowledge content |
| `inbox/` | L3 | Personal data |
| `inbox/alex-hormozi/video.txt` | L3 | Personal data |
| `logs/` | L3 | Personal data |
| `logs/batches/BATCH-001.md` | L3 | Personal data |
| `.claude/sessions/` | L3 | Personal data |
| `agents/sua-empresa/` | L3 | Personal data |
| `.env` | NEVER | Secrets |
| `.env.local` | NEVER | Secrets |
| `.mcp.json` | NEVER | Secrets/sensitive config |
| `credentials.json` | NEVER | Secrets |
| `token.json` | NEVER | Secrets |
| `settings.local.json` | NEVER | Secrets |
| `archive/*/finance-agent/` | DELETE | Obsolete |
| `archive/*/talent-agent/` | DELETE | Obsolete |
| `.cursor/` | REVIEW | Unclear (IDE config) |
| `.planning/` | REVIEW | Unclear (dev tooling) |
| `README.md` | REVIEW | Unclear (context-dependent) |

---

## Programmatic Classification

For batch classification, use the audit script:

```bash
# Run full audit and get current classification of all files
python3 engine/intelligence/audit_layers.py

# Output files:
#   docs/audit/AUDIT-REPORT.json  — Machine-readable, all 20,797+ items
#   docs/audit/AUDIT-REPORT.md    — Human-readable summary

# View delete candidates
python3 -c "
import json
with open('docs/audit/AUDIT-REPORT.json') as f:
    data = json.load(f)
for item in data['delete_candidates']:
    print(item['path'])
"
```

The classification logic in `audit_layers.py` implements:
- `L1_PATTERNS` — Directory prefixes for core engine
- `L2_PATTERNS` — Directory prefixes for populated content
- `L3_PATTERNS` — Directory prefixes for personal data
- `NEVER_PATTERNS` — File name patterns for secrets
- `DELETE_PATTERNS` — Name fragments for obsolete content

Priority order (highest wins): `DELETE > NEVER > L3 > L2 > L1 > REVIEW`

To add a new classification rule, edit the appropriate `*_PATTERNS` list in `audit_layers.py` and re-run the audit.

---

## Related Files

- `engine/intelligence/audit_layers.py` — Programmatic classifier implementing these rules
- `docs/audit/AUDIT-REPORT.json` — Latest full audit results (20,797 items)
- `docs/audit/AUDIT-REPORT.md` — Human-readable audit summary
- `docs/audit/L1-GITIGNORE-TEMPLATE.txt` — `.gitignore` for L1 (npm) distribution
- `docs/audit/L2-GITIGNORE-TEMPLATE.txt` — `.gitignore` for L2 (knowledge content) distribution
- `docs/audit/L3-GITIGNORE-TEMPLATE.txt` — `.gitignore` for L3 (personal) backup
- `.gitignore` — Active gitignore (reflects L1 distribution rules)

---

## Validation Checklist

This checklist confirms that LAYERS.md meets its stated purpose: "any person can classify a new file by reading this document."

- [x] All 7 sections exist (Quick Reference, Layer Definitions x6, Classification Criteria, Decision Flowchart, How to Classify, Path Examples, Programmatic Classification)
- [x] Each of the 6 categories is documented: L1, L2, L3, NEVER, DELETE, REVIEW
- [x] Real examples from Phase 7 AUDIT-REPORT.json are included for each layer
- [x] Decision flowchart covers all 6 categories in clear YES/NO order
- [x] Flowchart is ASCII-rendered and copy-pasteable
- [x] Step-by-step practical classification guide exists (6 steps)
- [x] REVIEW fallback is documented with examples
- [x] Link to `audit_layers.py` for programmatic classification
- [x] Link to `AUDIT-REPORT.md` for current state
- [x] Classification table with criteria for all layers

**Test cases (a new reader should classify these correctly after reading this document):**
- `engine/tasks/new-task.md` → L1 (Step 5: starts with `engine/`)
- `knowledge/external/playbooks/SALES-PLAYBOOK.md` → L2 (Step 4: starts with `knowledge/external/playbooks/`)
- `inbox/my-video.txt` → L3 (Step 3: starts with `inbox/`)
- `.env.local` → NEVER (Step 1: matches `.env*` pattern)
