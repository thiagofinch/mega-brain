# Story 3.3: Preset Configs

> **Epic:** Evolucao Mega Brain (v1.4.0 -> v2.0.0)
> **Sprint:** 3 -- Quick Wins
> **Effort:** ~2h
> **Risk:** LOW
> **Priority:** P2 (from surgical comparison CAT1 item 14)
> **Dependencies:** None

---

## Objective

Create YAML preset configurations for different pipeline use cases so the system
can optimize chunking, extraction depth, and processing strategy per content type.

Currently, the pipeline uses one-size-fits-all settings. A sales training course
and a weekly team meeting get identical treatment. Presets fix that.

---

## Tasks

| # | Task                                                | Effort |
|---|------------------------------------------------------|--------|
| 1 | Create `core/configs/presets/` directory              | 5 min  |
| 2 | Create `course.yaml` preset                           | 20 min |
|   | Optimized for: educational videos, online courses     |        |
|   | Settings: larger chunks (2000 tokens), framework      |        |
|   | extraction priority, speaker attribution ON           |        |
| 3 | Create `meeting.yaml` preset                          | 20 min |
|   | Optimized for: team meetings, 1:1 calls               |        |
|   | Settings: medium chunks (1000 tokens), action item    |        |
|   | extraction priority, multi-speaker diarization ON     |        |
| 4 | Create `podcast.yaml` preset                          | 20 min |
|   | Optimized for: podcast episodes, interviews           |        |
|   | Settings: large chunks (2500 tokens), key insight     |        |
|   | extraction, guest identification, topic segmentation  |        |
| 5 | Create `book.yaml` preset                             | 20 min |
|   | Optimized for: books, long-form written content       |        |
|   | Settings: chapter-based chunking, concept extraction  |        |
|   | priority, hierarchical structure preservation         |        |
| 6 | Create `_schema.yaml` preset schema definition        | 15 min |
|   | Defines all valid preset fields with types and        |        |
|   | defaults so new presets are self-documenting           |        |
| 7 | Register path in `core/paths.py` ROUTING              | 5 min  |
|   | Key: `"presets"` -> core/configs/presets/              |        |
| 8 | Write test: `tests/python/test_preset_configs.py`     | 15 min |
|   | test_all_presets_valid_yaml (load all, no parse error) |        |
|   | test_all_presets_have_required_fields                  |        |
|   | test_schema_covers_all_preset_fields                   |        |

---

## Preset YAML Structure

```yaml
# Example: course.yaml
preset:
  name: course
  description: "Online courses and educational video content"
  version: "1.0.0"

chunking:
  strategy: "semantic"
  max_tokens: 2000
  overlap_tokens: 200
  respect_headings: true

extraction:
  priority:
    - frameworks
    - methodologies
    - heuristics
    - mental_models
    - philosophies
  speaker_attribution: true
  timestamp_preservation: true

processing:
  batch_size: 10
  parallel_workers: 1
  mce_enabled: true

output:
  format: "markdown"
  include_metadata: true
  source_tagging: true
```

---

## Acceptance Criteria

- [ ] 4 preset YAML files exist in `core/configs/presets/`
- [ ] All presets load without YAML parse errors
- [ ] Schema file documents all valid fields
- [ ] Each preset has: name, description, chunking, extraction, processing, output
- [ ] 3 tests pass in test_preset_configs.py
- [ ] Presets are read-only reference configs (pipeline integration is Sprint 4)

---

## Definition of Done

- All YAML files pass yamllint
- Tests pass in CI
- Schema file is self-documenting (comments explain each field)
- No pipeline code changes (presets are config-only in this story)

---

## File Map

```
CREATES:
  core/configs/presets/_schema.yaml
  core/configs/presets/course.yaml
  core/configs/presets/meeting.yaml
  core/configs/presets/podcast.yaml
  core/configs/presets/book.yaml
  tests/python/test_preset_configs.py

MODIFIES:
  core/paths.py (add ROUTING key)
```
