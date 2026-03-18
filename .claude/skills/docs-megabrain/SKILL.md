# SKILL-DOCS-MEGABRAIN
## Padrões de Documentação do Mega Brain

> **Auto-Trigger:** Criação de qualquer arquivo .md no projeto
> **Keywords:** "documento", "documentar", "criar md", "playbook", "README"
> **Prioridade:** ALTA

---

## PROPÓSITO

Garantir que toda documentação do Mega Brain siga padrões consistentes de:
- Estrutura hierárquica
- Formatação visual
- Linguagem acessível
- Rastreabilidade

---

## QUANDO USAR

### ✅ USAR quando:
- Criar qualquer arquivo .md
- Documentar processos, playbooks, guias
- Atualizar README, CLAUDE.md, SESSION-STATE
- Criar documentação de agentes

### ❌ NÃO USAR quando:
- Arquivos de configuração (.json, .yaml)
- Código fonte (.py, .sh)
- Logs temporários

---

## REGRAS OBRIGATÓRIAS

### Estrutura de Documento

```markdown
# TÍTULO PRINCIPAL
## Subtítulo descritivo

> **Metadata em blockquote**
> **Versão:** X.X.X
> **Atualizado:** Data

---

## SEÇÃO 1

### Subseção 1.1

Conteúdo...

---

## SEÇÃO 2

...
```

### Hierarquia de Títulos

| Nível | Uso | Exemplo |
|-------|-----|---------|
| `#` | Título do documento (1 por arquivo) | `# PLAYBOOK CLOSER` |
| `##` | Seções principais | `## MÉTRICAS` |
| `###` | Subseções | `### Taxa de Conversão` |
| `####` | Detalhes (evitar) | Usar apenas se necessário |

### Regra de Não Abreviar

| ❌ Proibido | ✅ Usar |
|-------------|---------|
| SM | Sales Manager (Gerente de Vendas) |
| BDR | Prospector (Business Development Representative) |
| MRR | Receita Recorrente Mensal |
| LTV | Valor do Tempo de Vida do Cliente |
| CAC | Custo de Aquisição de Cliente |

**Exceção:** Após primeira menção completa, pode usar sigla.

### Formatação de Métricas

```markdown
## Métricas de Sucesso

| Métrica | Target | Crítico |
|---------|--------|---------|
| Taxa de comparecimento | ≥80% | <70% |
| Taxa de fechamento | 25-35% | <20% |

**Na prática:** Se agenda 10 reuniões, 8 devem comparecer.
Dessas 8, fechar 2-3 vendas.
```

### Formatação de Processos

```markdown
## Processo de [Nome]

### Passo 1: [Ação]
**O que:** Descrição clara
**Por que:** Justificativa
**Como:** Instruções específicas

### Passo 2: [Ação]
...
```

### Separadores

- Usar `---` entre seções principais
- Nunca usar `***` ou `___`
- Linha em branco antes e depois do separador

### Blockquotes

```markdown
> ⚠️ **ATENÇÃO:** Para avisos importantes
> 💡 **DICA:** Para sugestões úteis
> 📌 **NOTA:** Para informações adicionais
```

### Tabelas

- Sempre com header
- Alinhamento consistente
- Mínimo 2 colunas

```markdown
| Coluna A | Coluna B | Coluna C |
|----------|----------|----------|
| Valor 1  | Valor 2  | Valor 3  |
```

### Listas

**Bullets para itens sem ordem:**
```markdown
- Item A
- Item B
- Item C
```

**Números para sequências:**
```markdown
1. Primeiro passo
2. Segundo passo
3. Terceiro passo
```

### Links Internos

```markdown
Ver também: [Nome do Documento](/caminho/DOCUMENTO.md)
Fonte: [ID-FONTE](/knowledge/external/dossiers/...)
```

---

## TEMPLATES POR TIPO

### Playbook
```markdown
# PLAYBOOK [FUNÇÃO]

> **Função:** [Nome completo]
> **Versão:** X.X.X
> **Fontes:** [IDs das fontes]

---

## VISÃO GERAL
[Resumo executivo]

## RESPONSABILIDADES
[Lista de responsabilidades]

## MÉTRICAS
[Tabela de métricas]

## PROCESSO DIÁRIO
[Passo a passo]

## scripts/FRAMEWORKS
[Ferramentas práticas]

## ERROS COMUNS
[O que evitar]
```

### Dossier de Pessoa
```markdown
# DOSSIER: [NOME]

> **Empresa:** [Nome]
> **Especialidade:** [Área]
> **Fontes processadas:** [N]

---

## BIOGRAFIA
[Contexto da pessoa]

## FILOSOFIA CORE
[Crenças fundamentais]

## FRAMEWORKS PRINCIPAIS
[Metodologias da pessoa]

## CITAÇÕES MARCANTES
[Quotes importantes]

## FONTES
[Lista de materiais processados]
```

---

## ANTI-PATTERNS (NUNCA FAZER)

1. ❌ Títulos sem hierarquia clara
2. ❌ Parágrafos gigantes sem quebra
3. ❌ Siglas sem explicação na primeira menção
4. ❌ Listas mistas (bullets + números juntos)
5. ❌ Formatação inconsistente entre documentos
6. ❌ Links quebrados ou relativos incorretos
7. ❌ Documentos sem metadata (versão, data)

---

## CHECKLIST PRÉ-ENTREGA

- [ ] Título principal único (#)
- [ ] Metadata em blockquote no topo
- [ ] Separadores entre seções principais
- [ ] Siglas explicadas na primeira menção
- [ ] Tabelas com header
- [ ] Links internos funcionais
- [ ] Sem parágrafos > 5 linhas
- [ ] Versão e data atualizados

---

## META-INFORMAÇÃO

- **Versão:** 1.0.0
- **Domínio:** Documentação
- **Prioridade:** ALTA
- **Dependências:** Nenhuma
