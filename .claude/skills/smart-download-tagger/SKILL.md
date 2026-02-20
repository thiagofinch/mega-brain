# SKILL: Smart Download & Tagger

## Descrição
Sistema inteligente de download, tagueamento e organização de materiais do Mega Brain.
Lê a planilha de controle, identifica materiais pendentes, baixa do Drive, gera TAGs e atualiza a planilha.

---

## ESTRUTURA DA PLANILHA (PADRÃO ATUAL)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  COLUNA  │  CONTEÚDO                                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│  A       │  Módulo (número ou categoria)                                     │
│  B       │  Número da Aula                                                   │
│  C       │  Aula/Assunto/Tema (título descritivo)                           │
│  D       │  Duração (mm:ss)                                                  │
│  E       │  Link - Drive (URL ou nome do arquivo no Drive)                  │
│  F       │  Link - YouTube (URL do vídeo no YouTube)                        │
│  G       │  Transcrição (nome do arquivo .docx no Drive)                    │
│  H       │  TAG (gerada por JARVIS - VAZIA = pendente)                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Regras da Planilha:
1. **Cada linha = um conteúdo** (vídeo OU material complementar)
2. **Materiais complementares** (PDFs, etc.) têm sua própria linha dedicada
3. **Coluna H vazia** = material novo, não processado, precisa de download/TAG
4. **Coluna H preenchida** = já processado e tagueado

---

## PREFIXOS DE TAG POR ABA

| Aba | Prefixo TAG | Descrição |
|-----|-------------|-----------|
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

---

## ALGORITMO DE PROCESSAMENTO

```python
def process_pending_materials():
    """
    1. Para cada aba da planilha:
       a. Ler todas as linhas
       b. Identificar linhas onde coluna H está VAZIA
       c. Para cada linha pendente:
          - Extrair nome do arquivo da coluna G (ou E para materiais)
          - Buscar arquivo no Google Drive por nome
          - Baixar conteúdo do arquivo
          - Gerar TAG no formato: PREFIXO-XXXX
          - Atualizar coluna H na planilha com a TAG
          - Salvar arquivo no INBOX como: [TAG] nome_original.ext
    """
```

---

## FORMATO DE SAÍDA

### Arquivo no INBOX
```
[TAG] Nome Original do Arquivo.ext

Exemplos:
[JM-0152] How to Handle Objections.txt
[UHTC-0012] Module_5.m4a
[CA-0032] 9 Figure Ad Scripts.pdf
```

### Atualização na Planilha
- Coluna H recebe a TAG gerada
- Formato: `PREFIXO-XXXX` (4 dígitos com zero à esquerda)

---

## TIPOS DE ARQUIVO SUPORTADOS

| Tipo | Extensão | Ação |
|------|----------|------|
| Transcrição | .docx | Extrair texto, salvar como .txt |
| PDF | .pdf | Baixar binário, manter formato |
| Áudio | .mp3, .m4a | Baixar binário, manter formato |
| Planilha | .xlsx | Baixar binário, manter formato |
| Apresentação | .pptx | Baixar binário, manter formato |
| Imagem | .jpeg, .jpg, .png | Baixar binário, manter formato |

---

## FERRAMENTAS MCP UTILIZADAS

| Ferramenta | Uso |
|------------|-----|
| `mcp__gdrive__gsheets_read` | Ler planilha para identificar pendentes |
| `mcp__gdrive__gdrive_search` | Buscar arquivos no Drive por nome |
| `mcp__gdrive__gdrive_read_file` | Baixar conteúdo do arquivo |
| `mcp__gdrive__gsheets_update_cell` | Atualizar TAG na coluna H |

---

## MAPEAMENTO DE DESTINO NO INBOX

| Prefixo | Pasta Destino |
|---------|---------------|
| JM | JEREMY MINER/COURSES |
| JH-ST, JH-IC, JH-WK, AOBA, PCVP, LYFC, MMM, 30DC, STA, UHTC | JEREMY HAYNES/COURSES |
| TSC | THE SCALABLE COMPANY/COURSES |
| EDC | COLE GORDON/COURSES |
| AH | ALEX HORMOZI/COURSES |
| CA | JEREMY HAYNES PROGRAM/COURSES |

---

## SCRIPT PRINCIPAL

Localização: `scripts/smart-download-tagger.py`

---

## REGRAS IMPORTANTES

1. **NUNCA duplicar** - verificar se arquivo já existe no INBOX antes de baixar
2. **SEMPRE atualizar planilha** - TAG na coluna H após download bem-sucedido
3. **MANTER consistência** - mesmo formato de TAG em todo o sistema
4. **LOGS detalhados** - registrar cada ação para auditoria

---

**Skill criada em:** 2026-01-08
**Autor:** JARVIS
**Versão:** 1.0
