# SKILL: Leitura de Fontes Híbridas

## Descrição
Skill para leitura inteligente de conteúdo proveniente de múltiplas fontes de dados (Google Sheets, Google Docs, arquivos locais).

---

## FONTES DA MISSÃO ATUAL

### 1. Planilha Google Sheets (Conteúdo Principal)
```
ID: [YOUR_SHEET_ID_HERE]
URL: https://docs.google.com/spreadsheets/d/[YOUR_SHEET_ID_HERE]
```

**19 Abas Disponíveis:**
| Aba | Prefixo | Descrição |
|-----|---------|-----------|
| Jeremy Miner | JM | Jeremy Miner Sales |
| Jeremy Haynes Sales Training | JH-ST | Cursos JH |
| Jeremy Haynes Inner Circle | JH-IC | Masterminds JH |
| Inner Circle Weekly Group Call Recordings | JH-WK | Calls Semanais JH |
| Agency Blueprint | AOBA | Cursos Agência |
| Cold Video Pitch | PCVP | Cold Pitch |
| Land Your First Agency Client | LYFC | Primeiro Cliente |
| Marketer Mindset Masterclass | MMM | Mindset |
| 30 Days Challenge | 30DC | Desafio 30 dias |
| Scale The Agency | STA | Escala |
| Ultra High Ticket Closer | UHTC | High Ticket |
| The Scalable Company | TSC | Ryan Deiss |
| Sales Training BR | EDC | Closer BR |
| Alex Hormozi | AH | Hormozi |
| Jeremy Haynes Program | CA | Sam Ovens |

### 2. Documento Google Docs (SOPs)
```
ID: [YOUR_DOC_ID_HERE]
URL: https://docs.google.com/document/d/[YOUR_DOC_ID_HERE]
Nome: [2.0 OWNER] Master SOP Index
```

**32 SOPs do Jeremy Haynes:**
| SOP # | Nome | TAG Sugerida |
|-------|------|--------------|
| 1 | THE HYDRA Ad Strategy | JH-SOP-0001 |
| 2 | Hammer Them Ad Strategy | JH-SOP-0002 |
| 3 | Mastering VSLs | JH-SOP-0003 |
| 4 | Mastering Webinars | JH-SOP-0004 |
| 5 | Client Reporting | JH-SOP-0005 |
| 6 | If This, Then That Rules for Advertising | JH-SOP-0006 |
| 7 | Client Onboarding | JH-SOP-0007 |
| 8 | Hiring & Team Onboarding | JH-SOP-0008 |
| 9 | A2P 10DLC Compliance | JH-SOP-0009 |
| 10 | 5-Point Client Retention Star | JH-SOP-0010 |
| 11 | The Tornado Ad Strategy | JH-SOP-0011 |
| 12 | Venus Fly Trap 2.0 Ad Strategy | JH-SOP-0012 |
| 13 | The Email Matrix | JH-SOP-0013 |
| 14 | Venus Fly Trap Ad Strategy | JH-SOP-0014 |
| 15 | The Forester Ad Strategy | JH-SOP-0015 |
| 16 | DSL Deck Sales Letter Funnel Strategy | JH-SOP-0016 |
| 17 | The Harvester Ad Strategy | JH-SOP-0017 |
| 18 | Ultimate Sales Guide | JH-SOP-0018 |
| 19 | What I Wish I Knew | JH-SOP-0019 |
| 20 | Top Hooks & Headlines for Copywriting | JH-SOP-0020 |
| 21 | Cold Video Pitch | JH-SOP-0021 |
| 22 | Friends and Family Insurance Policy | JH-SOP-0022 |
| 23 | The Perfect Client Traits | JH-SOP-0023 |
| 24 | Thinking Time | JH-SOP-0024 |
| 25 | What is Ad Fatigue? | JH-SOP-0025 |
| 26 | Direct Response Ad Creation Framework (Expanded) | JH-SOP-0026 |
| 27 | Direct Response Ad Creation Framework (TLDR) | JH-SOP-0027 |
| 28 | Confirmation Page Best Practices | JH-SOP-0028 |
| 29 | Advanced Book Funnel Creative | JH-SOP-0029 |
| 30 | Challenge Funnel Mastery | JH-SOP-0030 |
| 31 | Ad Diversification Mastery | JH-SOP-0031 |
| 32 | Setter Pre Call Best Practices | JH-SOP-0032 |

---

## ESTRUTURA DAS TRANSCRIÇÕES NA PLANILHA

**AS TRANSCRIÇÕES ESTÃO NA PLANILHA, NÃO EM ARQUIVOS EXTERNOS.**

### Colunas Típicas (variam por aba):
```
┌────────────────────────────────────────────────────────────────────────────┐
│  COLUNA  │  CONTEÚDO                                                       │
├────────────────────────────────────────────────────────────────────────────┤
│  A       │  MÓDULO (número ou categoria)                                   │
│  B       │  AULA (número + título)                                         │
│  C       │  ASSUNTO/TEMA (descrição/resumo)                                │
│  D       │  DURAÇÃO (mm:ss)                                                │
│  E       │  LINK - DRIVE (nome do arquivo de vídeo .mp4)                   │
│  F       │  LINK - YOUTUBE (título ou URL)                                 │
│  G       │  TRANSCRIÇÃO VISUAL + VERBAL ← PREFERENCIAL (nome .docx)       │
│  H       │  TRANSCRIÇÃO ← FALLBACK (nome .docx)                           │
│  I       │  TAG (JM-0001, JH-ST-0015, etc.)                               │
└────────────────────────────────────────────────────────────────────────────┘
```

### Hierarquia de Extração:
```
1. TRANSCRIÇÃO VISUAL + VERBAL (coluna G) → Melhor qualidade, usa primeiro
2. TRANSCRIÇÃO (coluna H) → Fallback se G não disponível
```

### Como Extrair Transcrições:
```
1. Ler planilha → identificar linhas faltantes no INBOX
2. Para cada linha faltante:
   a. Pegar valor da coluna G (nome do arquivo .docx)
   b. Se G vazio → usar coluna H
   c. Buscar arquivo .docx no Google Drive por nome
   d. Ler conteúdo do .docx
   e. Salvar como [TAG] Nome.txt no INBOX
```

### Detecção Inteligente de Padrão por Aba:
```python
def detect_columns(sheet_data):
    """
    Analisa primeira linha para detectar estrutura da aba.
    Retorna mapeamento de colunas.
    """
    headers = sheet_data['columnHeaders']
    mapping = {}

    for i, header in enumerate(headers):
        value = header.get('value', '').upper()
        col_letter = chr(65 + i)  # A, B, C...

        if 'TRANSCRIÇÃO VISUAL' in value or 'VISUAL + VERBAL' in value:
            mapping['transcription_primary'] = col_letter
        elif 'TRANSCRIÇÃO' in value:
            mapping['transcription_fallback'] = col_letter
        elif 'TAG' in value:
            mapping['tag'] = col_letter
        elif 'AULA' in value or 'NOME' in value:
            mapping['name'] = col_letter

    return mapping
```

---

## COMO LER CADA FONTE

### Google Sheets
```
1. Usar mcp__gdrive__gsheets_read com spreadsheetId
2. Especificar ranges por aba: ["NomeAba!A:Z"]
3. Analisar headers para detectar estrutura
4. Coluna de TRANSCRIÇÃO: G ou H (verificar header)
5. Coluna de TAG: geralmente I ou J
6. Se resultado muito grande, será salvo em tool-results/
```

### Google Docs
```
1. Usar mcp__gdrive__gdrive_read_file com fileId
2. Se muito grande, será salvo em tool-results/
3. Usar grep para buscar padrões específicos
4. Formato markdown com headers e links
```

### Arquivos Locais
```
1. Usar Read tool para arquivos .txt
2. Usar Glob para encontrar padrões
3. Usar Grep para buscar conteúdo
```

---

## MATCHING DE ARQUIVOS

### Formato de TAG no Nome do Arquivo
```
[PREFIX-XXXX] Nome Original.txt

Exemplos:
[JM-0114] 112 - How To Sell A Pen.txt
[JH-SOP-0001] SOP 01. THE HYDRA AD STRATEGY.txt
```

### Algoritmo de Matching
```python
from difflib import SequenceMatcher

def match_file_to_entry(filename, entries, threshold=0.7):
    """
    Compara nome do arquivo com entradas da planilha
    Retorna melhor match se score >= threshold
    """
    normalized = normalize_name(filename)
    best_match = None
    best_score = 0

    for entry_name, tag in entries.items():
        score = SequenceMatcher(None, normalized, normalize_name(entry_name)).ratio()
        if score > best_score:
            best_score = score
            best_match = (entry_name, tag)

    return best_match if best_score >= threshold else None
```

---

## HIERARQUIA DE DECISÃO

```
1. Arquivo já tem TAG [PREFIX-XXXX]?
   → SIM: Verificar se corresponde à planilha
   → NÃO: Buscar match na planilha

2. Match encontrado com score >= 0.7?
   → SIM: Renomear com TAG
   → NÃO: Marcar como órfão

3. Órfão identificado?
   → Verificar se existe em outra fonte (Docs, etc)
   → Se não existe, é conteúdo não catalogado
```

---

## FERRAMENTAS MCP DISPONÍVEIS

| Ferramenta | Uso |
|------------|-----|
| `mcp__gdrive__gsheets_read` | Ler planilhas Google Sheets |
| `mcp__gdrive__gdrive_read_file` | Ler documentos Google Docs |
| `mcp__gdrive__gdrive_search` | Buscar arquivos no Drive |
| `mcp__gdrive__gsheets_update_cell` | Atualizar célula na planilha |

---

## CACHE DE RESULTADOS

Resultados grandes são salvos automaticamente em:
```
~/.claude/projects/<project-path>/[SESSION-ID]/tool-results/
```

Formato dos arquivos:
```json
[{"type": "text", "text": "...conteúdo JSON..."}]
```

**Para ler:** Fazer double-parse do JSON (outer array → inner text)

---

## REGRAS IMPORTANTES

1. **SEMPRE verificar ambas as fontes** (Sheets + Docs) antes de declarar órfão
2. **NUNCA assumir** que arquivo não existe sem verificar
3. **GRAVAR** mapeamento DE-PARA após cada operação
4. **LOGAR** todas as ações em CURRENT-SESSION.md

---

**Skill criada em:** 2026-01-07
**Autor:** JARVIS
