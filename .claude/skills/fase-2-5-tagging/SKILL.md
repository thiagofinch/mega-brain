# SKILL: Fase 2.5 - Tagueamento de Arquivos INBOX

## Objetivo
Renomear arquivos do INBOX com prefixo [TAG] baseado na planilha de controle, permitindo DE-PARA instantâneo entre arquivo e entrada na planilha.

---

## CONCEITO FUNDAMENTAL

```
ARQUIVO INBOX → NOME SIMILAR NA PLANILHA → TAG DA PLANILHA → PREFIXO NO ARQUIVO

Exemplo:
  Arquivo: "112 - How To Get Prospects.txt"
  Planilha: "112 - How To Get Prospects To Open Up To You" → JM-0114
  Resultado: "[JM-0114] 112 - How To Get Prospects.txt"
```

**IMPORTANTE:** TAG ≠ Número do arquivo. TAG é posição sequencial na planilha.

---

## ARQUIVOS DO SISTEMA

| Arquivo | Propósito |
|---------|-----------|
| `.claude/scripts/build-complete-index.py` | Constrói índice nome→TAG da planilha |
| `.claude/scripts/tag-inbox-v2.py` | Faz matching e renomeia arquivos |
| `.claude/scripts/revert-tags.py` | Remove TAGs incorretas (rollback) |
| `.claude/mission-control/PLANILHA-INDEX.json` | Índice com 915+ entradas |
| `.claude/mission-control/TAG-MAPPING-V2.json` | Relatório do último matching |
| `.claude/mission-control/SPREADSHEET-SCHEMA.json` | Schema das abas da planilha |

---

## FLUXO DE TRABALHO

### Passo 1: Atualizar Índice (se necessário)
```bash
# From the project root
python3 .claude/scripts/build-complete-index.py
```

### Passo 2: Executar Matching (preview)
```bash
python3 .claude/scripts/tag-inbox-v2.py --threshold=0.65
```

### Passo 3: Verificar Relatório
- Revisar `TAG-MAPPING-V2.json`
- Verificar amostras de matches
- Ajustar threshold se necessário (0.6 = mais flexível, 0.8 = mais estrito)

### Passo 4: Executar Renomeação
```bash
python3 .claude/scripts/tag-inbox-v2.py --threshold=0.65 --execute
```

### Rollback (se necessário)
```bash
python3 .claude/scripts/revert-tags.py
```

---

## ALGORITMO DE MATCHING

```python
def match_file_to_index(file_info, index, threshold=0.7):
    # 1. Normaliza nome do arquivo (remove extensão, número, caracteres especiais)
    # 2. Compara com cada entrada do índice usando difflib.SequenceMatcher
    # 3. Retorna melhor match acima do threshold
```

**Normalização:**
- Remove extensão (.txt, .docx, .pdf)
- Remove número inicial ("123 - ", "123. ")
- Remove timestamps (_20260107)
- Remove datas (12-25-24)
- Remove [youtube.com...]
- Lowercase

---

## ESTATÍSTICAS ATUAIS (2026-01-07)

```
ÍNDICE:
  - 915 entradas
  - 19 sheets/abas

MATCHING:
  - 932 arquivos no INBOX
  - 727 matches encontrados (78%)
  - 205 órfãos (22%)

RESULTADO:
  - 727 arquivos renomeados com [TAG]
  - 0 erros
```

---

## ÓRFÃOS (205 arquivos)

Arquivos sem match são tipicamente:
- PDFs/materiais complementares não catalogados
- Transcrições com nome diferente
- Conteúdo de masterminds/podcasts não na planilha
- Arquivos com formato de nome muito diferente

**Tratamento:**
1. Revisar manualmente se são relevantes
2. Adicionar à planilha se necessário
3. Mover para pasta de materiais complementares

---

## QUANDO USAR

1. **Novos arquivos no INBOX** - Após download de novos conteúdos
2. **Sincronização** - Quando planilha foi atualizada com novas TAGs
3. **Reorganização** - Após mover arquivos entre pastas

---

## COMANDOS RÁPIDOS

```bash
# Preview matching
/tag-inbox preview

# Executar tagueamento
/tag-inbox execute

# Reverter tags
/tag-inbox revert

# Atualizar índice
/tag-inbox update-index
```

---

## REGRAS IMPORTANTES

1. **SEMPRE fazer preview antes de execute**
2. **NUNCA executar sem verificar amostras do relatório**
3. **Threshold recomendado: 0.65** (bom equilíbrio entre precisão e cobertura)
4. **Guardar backup antes de operações em massa**
5. **Índice deve estar atualizado com planilha**

---

## ESTRUTURA DE TAG

```
Formato: [PREFIX]-[NNNN]

Prefixes:
  JM    = Jeremy Miner
  JH-ST = Jeremy Haynes - Sales Training
  JH-IC = Jeremy Haynes - Inner Circle Mastermind
  JH-WK = Jeremy Haynes - Weekly Calls
  AOBA  = Agency Blueprint
  PCVP  = Cold Video Pitch
  LYFC  = Land Your First Agency Client
  MMM   = Marketer Mindset Masterclass
  30DC  = 30 Days Challenge
  STA   = Scale The Agency
  UHTC  = Ultra High Ticket Closer
  TSC   = The Scalable Company
  EDC   = Sales Training BR
  AH    = Alex Hormozi
  CA    = Jeremy Haynes Program
```

---

## HISTÓRICO

- **2026-01-07**: Criação inicial. 727 arquivos tagueados com sucesso.
