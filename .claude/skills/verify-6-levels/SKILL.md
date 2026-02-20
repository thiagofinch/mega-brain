> **Auto-Trigger:** Quando usuário pede verificação, validação, ou checagem de qualidade
> **Keywords:** "verificar", "verify", "verificação", "validar", "validation", "checar", "check", "qualidade", "quality", "6 níveis", "6 levels"
> **Prioridade:** ALTA
> **Tools:** Bash, Read, Grep

---

# /verify-6-levels - Verificação Completa em 6 Níveis

## Propósito

Este skill executa verificação completa do código/sistema seguindo os 6 níveis
definidos no workflow Boris Cherny + Continuous Claude.

---

## Os 6 Níveis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE VERIFICAÇÃO                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NÍVEL 1: LINT/HOOKS                                                        │
│  ├── O que: Formatação, style guides, pre-commit hooks                     │
│  ├── Como: pre-commit run --all-files                                      │
│  └── Falha: Código mal formatado, violações de style                       │
│                                                                             │
│  NÍVEL 2: TESTS                                                             │
│  ├── O que: Testes unitários e de integração                               │
│  ├── Como: pytest / npm test / go test                                     │
│  └── Falha: Testes quebrando, cobertura baixa                              │
│                                                                             │
│  NÍVEL 3: BUILD/INTEGRITY                                                   │
│  ├── O que: Compilação, integridade de arquivos                            │
│  ├── Como: python -m py_compile / npm run build / validate_phase5.py      │
│  └── Falha: Erros de sintaxe, imports quebrados                            │
│                                                                             │
│  NÍVEL 4: VISUAL                                                            │
│  ├── O que: Revisão visual do output                                       │
│  ├── Como: Inspeção manual dos resultados                                  │
│  └── Falha: Output incorreto, formatação errada                            │
│                                                                             │
│  NÍVEL 5: STAGING                                                           │
│  ├── O que: Teste em ambiente staging/preview                              │
│  ├── Como: Deploy para ambiente de teste                                   │
│  └── Falha: Funciona local mas quebra em produção                          │
│                                                                             │
│  NÍVEL 6: SECURITY                                                          │
│  ├── O que: Auditoria de segurança                                         │
│  ├── Como: bandit / npm audit / revisão manual                             │
│  └── Falha: Vulnerabilidades, secrets expostos                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Comandos por Nível

### Nível 1: Lint/Hooks
```bash
# Python
python3 -m py_compile **/*.py
ruff check .
black --check .

# JavaScript/TypeScript
npm run lint
eslint .

# Pre-commit (universal)
pre-commit run --all-files
```

### Nível 2: Tests
```bash
# Python
pytest -v
pytest --cov=. --cov-report=term-missing

# JavaScript
npm test
jest --coverage

# Go
go test ./...
```

### Nível 3: Build/Integrity
```bash
# Python - Validar sintaxe de todos os arquivos
find . -name "*.py" -exec python3 -m py_compile {} \;

# JARVIS específico - Validar Fase 5
python3 scripts/validate_phase5.py

# Validar cascateamento
python3 scripts/validate_cascading_integrity.py

# JavaScript
npm run build
```

### Nível 4: Visual
```markdown
Verificação Manual:
- [ ] Output está formatado corretamente?
- [ ] ASCII art renderiza corretamente?
- [ ] Logs estão completos?
- [ ] Métricas fazem sentido?
```

### Nível 5: Staging
```bash
# Depende do projeto
# Exemplos:
vercel --prod
railway up
heroku push staging
```

### Nível 6: Security
```bash
# Python
bandit -r . -ll
pip-audit
safety check

# JavaScript
npm audit
snyk test

# Secrets
git secrets --scan
trufflehog .

# Manual
# - Revisar .env não commitado
# - Verificar permissions em APIs
# - Checar tokens não expirados
```

---

## Verificação Rápida (JARVIS)

Para verificação rápida do Mega Brain:

```bash
# Executar todos os níveis aplicáveis
cd "."

# Nível 1: Sintaxe Python
echo "=== NÍVEL 1: LINT ===" && \
find . -name "*.py" -path "./.claude/*" -exec python3 -m py_compile {} \; && \
echo "PASSED"

# Nível 3: Integridade
echo "=== NÍVEL 3: INTEGRITY ===" && \
python3 scripts/validate_phase5.py --fix && \
echo "PASSED"

# Nível 6: Security Check
echo "=== NÍVEL 6: SECURITY ===" && \
grep -r "sk-" .claude/ --include="*.json" && echo "WARNING: API keys found" || echo "PASSED"
```

---

## Checklist de PR

Use este checklist em Pull Requests:

```markdown
## Verification Checklist
- [ ] 1. Hooks/Lint passed
- [ ] 2. Tests passed
- [ ] 3. Build successful
- [ ] 4. Visual verification done
- [ ] 5. Staging tested (if applicable)
- [ ] 6. Security audit completed
```

---

## Quando NÃO Ativar

- Quando usuário só quer ver status rápido (usar `/status`)
- Perguntas sobre o que verificação significa (conceitual)
- Quando já está em processo de verificação e só quer um nível específico

---

## Regras Relacionadas

- **REGRA #30**: GitHub Workflow (exige 6 níveis antes de merge)
- **REGRA #23**: Validação automática da Fase 5
- **REGRA #26**: Validação de integridade do cascateamento

---

## Integração com GitHub Actions

O arquivo `.github/workflows/verification.yml` implementa os níveis 1-3 automaticamente:

```yaml
jobs:
  level-1-lint:
    # Verifica formatação
  level-2-tests:
    # Executa testes
  level-3-integrity:
    # Valida integridade
```

Níveis 4-6 requerem verificação manual ou ferramentas adicionais.

---

## Exemplos de Uso

**Usuário:** "Verifica se está tudo ok antes de fazer merge"
**JARVIS:** [Executa verificação dos 6 níveis, reporta status]

**Usuário:** "Roda os testes de integridade"
**JARVIS:** [Executa Nível 3 especificamente]

**Usuário:** "O que é verificação de 6 níveis?"
**JARVIS:** [Mostra explicação do pipeline]

---

*Para workflow completo do GitHub, use `/github-workflow`*
