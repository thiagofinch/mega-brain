# Verification Levels

> **6 Níveis de Verificação do JARVIS**
> Todo código deve passar por 6 níveis de verificação antes do merge.

---

## Overview

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    JARVIS 6-LEVEL VERIFICATION SYSTEM                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║    Level 1         Level 2         Level 3         Level 4                  ║
║    ┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐                    ║
║    │LINT │───────▶│TEST │───────▶│BUILD│───────▶│VISUAL│                   ║
║    └─────┘        └─────┘        └─────┘        └─────┘                    ║
║       │              │              │              │                        ║
║       │              │              │              │                        ║
║       ▼              ▼              ▼              ▼                        ║
║    Syntax         Unit          Import        Output                       ║
║    YAML/JSON      Integration   No cycles     Format                       ║
║    Hooks          Regression    Dependencies  ASCII art                    ║
║                                                                              ║
║                                                                              ║
║                   Level 5         Level 6                                   ║
║                   ┌─────┐        ┌─────┐                                   ║
║              ────▶│STAGE│───────▶│SECUR│───────▶ MERGE                     ║
║                   └─────┘        └─────┘                                   ║
║                      │              │                                       ║
║                      ▼              ▼                                       ║
║                   Real data     No secrets                                 ║
║                   State files   Permissions                                ║
║                   Integration   Validation                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Level 1: Hooks/Lint

### O Que Verifica

| Check | Ferramenta | Comando |
|-------|-----------|---------|
| Python syntax | py_compile | `python -m py_compile file.py` |
| YAML syntax | PyYAML | `yaml.safe_load()` |
| JSON syntax | json | `json.load()` |
| Pre-commit | hooks | `pre-commit run --all-files` |

### Critérios de Aprovação

```
✅ PASSA quando:
- Todos os arquivos .py compilam sem erro
- Todos os arquivos .yaml/.yml são válidos
- Todos os arquivos .json são válidos
- Pre-commit hooks passam

❌ FALHA quando:
- SyntaxError em qualquer arquivo Python
- YAML mal formatado
- JSON inválido
- Hook rejeita mudança
```

### Automação

GitHub Actions executa automaticamente no job `level-1-lint`.

---

## Level 2: Tests

### O Que Verifica

| Check | Descrição |
|-------|-----------|
| Unit tests | Testes unitários em `scripts/tests/` |
| Integration tests | Testes de integração entre componentes |
| Regression | Nenhum teste que passava agora falha |
| Coverage | Cobertura de código (meta: >70%) |

### Critérios de Aprovação

```
✅ PASSA quando:
- pytest retorna exit code 0
- Nenhum teste falha
- Testes novos adicionados para código novo
- Coverage não diminui

❌ FALHA quando:
- Qualquer teste falha
- Testes existentes quebram
- Código novo sem testes (para features críticas)
```

### Comandos

```bash
# Rodar todos os testes
python -m pytest scripts/tests/ -v

# Com coverage
python -m pytest scripts/tests/ --cov=scripts --cov-report=html

# Teste específico
python -m pytest scripts/tests/test_validation.py -v
```

---

## Level 3: Build/Integrity

### O Que Verifica

| Check | Descrição |
|-------|-----------|
| Imports | Todos os imports resolvem corretamente |
| Circular imports | Não há dependências circulares |
| Dependencies | Todas as dependências documentadas |
| Critical files | Arquivos essenciais existem |

### Critérios de Aprovação

```
✅ PASSA quando:
- Todos os scripts podem ser importados
- Nenhum ImportError
- requirements.txt atualizado (se aplicável)
- CLAUDE.md, settings.json existem

❌ FALHA quando:
- ImportError em qualquer script
- Circular import detectado
- Dependência não documentada
- Arquivo crítico faltando
```

### Arquivos Críticos

```
/CLAUDE.md                          # Regras invioláveis
/.claude/settings.json              # Configurações Claude
/.claude/jarvis/STATE.json         # Estado JARVIS
/.claude/mission-control/           # Mission control
```

---

## Level 4: Visual Verification

### O Que Verifica

| Check | Descrição |
|-------|-----------|
| Output format | Formato de saída segue templates |
| ASCII art | Boxes e headers renderizam corretamente |
| Progress bars | Barras de progresso funcionam |
| Dual-location | Logs aparecem em ambos locais |

### Critérios de Aprovação

```
✅ PASSA quando:
- Outputs seguem template oficial
- ASCII art com ╔═══╗ e ┌───┐ renderiza
- Progress bars [████████░░░░] funcionam
- Log em /logs/ E /.claude/mission-control/

❌ FALHA quando:
- Formato não padrão
- ASCII quebrado
- Log em apenas um local
- Template V3 não seguido (para agentes)
```

### Exemplos de Verificação

```
Output correto:
╔══════════════════════════════════════════════════════════════╗
║                    BATCH 042 - JEREMY HAYNES                 ║
╠══════════════════════════════════════════════════════════════╣
║  Arquivos: 8/8    Progresso: [████████████████] 100%        ║
╚══════════════════════════════════════════════════════════════╝

Output incorreto:
BATCH 042
Arquivos: 8/8
Progresso: 100%
```

---

## Level 5: Staging/Integration

### O Que Verifica

| Check | Descrição |
|-------|-----------|
| Real data | Testado com dados reais (não mock) |
| State files | JARVIS-STATE.json atualiza corretamente |
| Workflows | Integração com workflows existentes |
| Cascading | Cascateamento funciona (Regra #22) |

### Critérios de Aprovação

```
✅ PASSA quando:
- Funciona com dados de produção
- Estado salva/carrega corretamente
- Não quebra workflows existentes
- Cascateamento multi-destino funciona

❌ FALHA quando:
- Funciona só com mock
- Estado inconsistente
- Quebra integração existente
- Destinos não recebem cascateamento
```

### Testes de Integração

```bash
# Validar Phase 5
python3 scripts/validate_phase5.py

# Validar cascateamento
python3 scripts/validate_cascading_integrity.py

# Verificar estado
python3 scripts/verify_state.py
```

---

## Level 6: Security Audit

### O Que Verifica

| Check | Descrição |
|-------|-----------|
| Secrets | Nenhuma credencial hardcoded |
| API keys | Keys não expostas no código |
| Permissions | Permissões de arquivo apropriadas |
| Input validation | Inputs validados (se aplicável) |

### Critérios de Aprovação

```
✅ PASSA quando:
- Nenhum password/token no código
- .env usado para secrets
- Arquivos sem permissão excessiva
- Inputs sanitizados

❌ FALHA quando:
- Secret encontrado no código
- API key exposta
- Arquivo com permissão 777
- SQL injection possível
```

### Padrões a Verificar

```python
# ❌ ERRADO
api_key = "sk-abc123def456"
password = "minhasenha123"

# ✅ CORRETO
api_key = os.environ.get("API_KEY")
password = os.environ.get("DB_PASSWORD")
```

### .gitignore Obrigatório

```
.env
*.key
*.pem
credentials.json
secrets/
```

---

## Checklist Visual

Use este checklist no PR:

```markdown
## Verification Checklist (6 Levels)

### Level 1: Hooks/Lint ✅
- [ ] Python files compile without errors
- [ ] No syntax errors in YAML/JSON files
- [ ] Pre-commit hooks pass

### Level 2: Tests ✅
- [ ] Existing tests pass
- [ ] New tests added for new functionality
- [ ] No regression in test coverage

### Level 3: Build ✅
- [ ] All scripts execute without import errors
- [ ] Dependencies are documented
- [ ] No circular imports

### Level 4: Visual Verification ✅
- [ ] Output format matches expected templates
- [ ] ASCII art renders correctly
- [ ] Logs follow dual-location pattern

### Level 5: Staging/Integration ✅
- [ ] Tested with real data
- [ ] Integration with existing workflows verified
- [ ] State files update correctly

### Level 6: Security Audit ✅
- [ ] No hardcoded credentials or secrets
- [ ] No exposed API keys
- [ ] File permissions are appropriate

**Verification Score**: ___/6 levels passed
```

---

## Automation

### GitHub Actions

O workflow `verification.yml` executa:

| Level | Automação |
|-------|-----------|
| 1 | ✅ Totalmente automático |
| 2 | ✅ Automático (se tests existem) |
| 3 | ✅ Automático |
| 4 | ⚠️ Parcialmente automático |
| 5 | ⚠️ Requer verificação manual |
| 6 | ⚠️ Scan automático + review manual |

### Scores

```
6/6 = READY TO MERGE
5/6 = Review needed for failing level
4/6 = Significant issues
<4  = Major rework required
```

---

## Quick Commands

```bash
# Level 1: Lint
python -m py_compile scripts/*.py

# Level 2: Tests
python -m pytest scripts/tests/ -v

# Level 3: Import check
python -c "import scripts.my_script"

# Level 5: Integration
python3 scripts/validate_phase5.py

# Level 6: Secret scan
grep -rn "password\|api_key\|secret" --include="*.py"
```

---

> 🤖 Todos os 6 níveis devem passar antes do merge.
> Não há exceções. Não há atalhos.
