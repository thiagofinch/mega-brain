# Pull Request

## Summary
<!-- Breve descrição do que este PR faz -->
-

## Related Issue
<!-- Link para a issue relacionada. Use "Fixes #XX" para fechar automaticamente -->
Fixes #

## Type of Change
- [ ] 🐛 Bug fix (correção que não quebra funcionalidade existente)
- [ ] ✨ New feature (nova funcionalidade que não quebra funcionalidade existente)
- [ ] 💥 Breaking change (correção ou feature que causa mudança em funcionalidade existente)
- [ ] 📚 Documentation (mudanças apenas em documentação)
- [ ] 🔧 Refactor (mudança de código que não corrige bug nem adiciona feature)
- [ ] 🧪 Test (adição ou correção de testes)
- [ ] 🏗️ Infrastructure (mudanças em CI/CD, hooks, scripts)

## Changes Made
<!-- Liste as principais mudanças -->
-
-
-

## JARVIS Context

### Phase Affected
- [ ] Phase 1 - Download
- [ ] Phase 2 - Organization
- [ ] Phase 3 - De-Para
- [ ] Phase 4 - Pipeline
- [ ] Phase 5 - Agents
- [ ] Infrastructure/System

### Rules Affected
<!-- Quais regras do CLAUDE.md são impactadas -->
- Rule #:

### Agents Impacted
<!-- Quais agentes são afetados por esta mudança -->
-

---

## Verification Checklist (6 Levels)

> ⚠️ **IMPORTANT**: All 6 levels must pass before merge. Mark each as you verify.

### Level 1: Hooks/Lint ✅
- [ ] Python files compile without errors (`python -m py_compile`)
- [ ] No syntax errors in YAML/JSON files
- [ ] Pre-commit hooks pass

### Level 2: Tests ✅
- [ ] Existing tests pass (`python -m pytest scripts/tests/`)
- [ ] New tests added for new functionality
- [ ] No regression in test coverage

### Level 3: Build ✅
- [ ] All scripts execute without import errors
- [ ] Dependencies are documented
- [ ] No circular imports

### Level 4: Visual Verification ✅
- [ ] Output format matches expected templates
- [ ] ASCII art renders correctly
- [ ] Progress bars display properly
- [ ] Logs follow dual-location pattern

### Level 5: Staging/Integration ✅
- [ ] Tested with real data (if applicable)
- [ ] Integration with existing workflows verified
- [ ] State files update correctly (JARVIS-STATE.json, MISSION-STATE.json)

### Level 6: Security Audit ✅
- [ ] No hardcoded credentials or secrets
- [ ] No exposed API keys
- [ ] File permissions are appropriate
- [ ] Input validation in place (if applicable)

---

## Screenshots/Logs
<!-- Se aplicável, adicione screenshots ou logs relevantes -->

## Additional Notes
<!-- Qualquer contexto adicional para os reviewers -->

---

## Reviewer Checklist
<!-- Para quem está revisando o PR -->
- [ ] Code follows project conventions
- [ ] Changes match the issue description
- [ ] No unnecessary files included
- [ ] Documentation updated (if needed)
- [ ] All 6 verification levels confirmed

---

**Verification Score**: ___/6 levels passed

> 🤖 This PR follows the Boris Cherny + Continuous Claude workflow.
> Merge only when all 6 verification levels are complete.
