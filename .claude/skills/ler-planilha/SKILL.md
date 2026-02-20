# SKILL: Leitura Inteligente de Planilhas

## Objetivo
Ler e interpretar corretamente planilhas de controle do Mega Brain, identificando estrutura, conteúdo, transcrições e materiais complementares.

---

## PRINCÍPIO ABSOLUTO #1: MAPEAR ANTES DE AGIR

```
NUNCA ESCREVER SEM ANTES LER E MAPEAR A ESTRUTURA COMPLETA DA ABA.
```

## PRINCÍPIO ABSOLUTO #2: UMA LINHA = UM ITEM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1 LINHA NA PLANILHA = 1 VÍDEO/AULA = 1 TAG                                 │
│                                                                             │
│  Cada linha pode conter:                                                    │
│  ├── 1 Transcrição (escolher a MELHOR disponível, NÃO ambas)               │
│  │   └── Visual+Verbal > Simples (hierarquia de qualidade)                 │
│  │                                                                          │
│  └── N Materiais complementares (PDFs, playbooks) ← ESTES são extras       │
│      └── Compartilham a mesma TAG do vídeo                                 │
│                                                                             │
│  ⚠️  TRANSCRIÇÕES DUPLICADAS NÃO SÃO MATERIAIS COMPLEMENTARES              │
│  ⚠️  São VERSÕES do mesmo conteúdo - escolher a melhor, descartar a outra  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## REGRA CRÍTICA: HIERARQUIA DE TRANSCRIÇÕES

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  QUANDO HÁ DUAS COLUNAS DE TRANSCRIÇÃO:                                     │
│                                                                             │
│  Coluna G: TRANSCRIÇÃO VISUAL + VERBAL  ← PREFERENCIAL (mais completa)     │
│  Coluna H: TRANSCRIÇÃO                  ← FALLBACK (só se G vazia)         │
│                                                                             │
│  REGRA: Baixar APENAS UMA por linha:                                       │
│  - Se G tem arquivo → usar G, ignorar H                                    │
│  - Se G vazia e H tem arquivo → usar H                                     │
│  - NUNCA baixar ambas para o mesmo vídeo                                   │
│                                                                             │
│  POR QUÊ Visual+Verbal é melhor:                                           │
│  - Captura texto falado + texto na tela (slides, exemplos)                 │
│  - Muito do conteúdo só pode ser entendido VISTO                           │
│  - Alimenta os agentes de forma mais rica                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### O que SÃO materiais complementares (BAIXAR):
- PDFs de playbooks, frameworks, checklists
- Planilhas de apoio (.xlsx)
- Apresentações (.pptx)
- Resumos em .docx (diferente da transcrição)
- Qualquer arquivo que ESTENDE o conteúdo do vídeo

### O que NÃO SÃO materiais complementares (NÃO DUPLICAR):
- Transcrição simples quando já existe Visual+Verbal
- Mesmo arquivo em pastas diferentes
- Versões duplicadas do mesmo conteúdo

Antes de adicionar QUALQUER TAG:
1. Ler row 3 (headers) - mapear TODAS as colunas
2. Ler amostra de dados (rows 4-20) - verificar onde ha conteudo
3. Identificar coluna de transcricao
4. Identificar coluna(s) de materiais complementares
5. SO ENTAO determinar coluna de TAG

**NAO ASSUMIR. VERIFICAR.**

---

## CONCEITO: UMA TAG = UM PACOTE

```
┌─────────────────────────────────────────────────────────────────┐
│  1 TAG = 1 Video + N Materiais Complementares                  │
│                                                                 │
│  Exemplo:                                                       │
│  TAG JH-WK-0065 representa:                                    │
│    - 1 video (aula)                                            │
│    - 5 PDFs associados (Ad_Ideas.pdf, Hammer_Them.pdf, etc)    │
│    - 1 transcricao .docx                                       │
│                                                                 │
│  Tudo isso e UMA entrada, UMA TAG.                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## REGRAS FUNDAMENTAIS

### 1. ESTRUTURA PADRAO
```
Row 1: Links de acesso (Drive, credenciais) - IGNORAR
Row 2: Titulo da aba (nome do curso/fonte) - IDENTIFICACAO
Row 3: Headers das colunas - MAPEAR ESTRUTURA
Row 4+: Dados - PROCESSAR
```

### 2. ORDEM DE LEITURA OBRIGATORIA

**PASSO 1: Carregar Schema**
```
Ler: .claude/mission-control/SPREADSHEET-SCHEMA.json
```
- Se aba existe no schema, usar configuracao existente
- Se aba NAO existe, mapear nova estrutura

**PASSO 2: Identificar Colunas**
Ler row 3 (headers) para mapear:
- Qual coluna tem TRANSCRICAO
- Qual coluna tem MATERIAL COMPLEMENTAR (PDFs, PPTX, etc)
- Qual coluna deve ter TAG

**PASSO 3: Determinar Coluna de TAGs**
```
REGRA DE OURO: TAG vai na PRIMEIRA coluna completamente vazia apos a transcricao

SE coluna I tem arquivos (PDFs, materiais) → TAG vai em J
SE coluna I esta vazia → TAG vai em I
SE coluna J tem arquivos → TAG vai em K
```

### 3. IDENTIFICACAO DE CONTEUDO

**Linha com Video (PRECISA TAG):**
- Coluna B tem nome do arquivo/video
- Coluna de transcricao tem .docx
- Outras colunas tem dados

**Linha Separadora (NAO TEM TAG):**
- Maioria das colunas vazias
- Pode ter apenas texto em A ou B indicando modulo
- NUNCA colocar TAG em separadores

**Material Complementar (NAO SOBRESCREVER):**
- Celula tem .pdf, .pptx, .xlsx, .docx (fora da coluna de transcricao)
- Preservar conteudo - NAO substituir por TAG

### 4. VALIDACAO ANTES DE ESCREVER

Antes de adicionar QUALQUER TAG, verificar:
```
[ ] A row tem conteudo real (video/aula)?
[ ] A row NAO e separador vazio?
[ ] A celula destino esta VAZIA?
[ ] A celula destino NAO tem arquivo/material?
[ ] A TAG segue o formato [PREFIX]-[NNNN]?
```

### 5. PADRAO DE TAGs

```
Formato: [PREFIX]-[NNNN]
- NNNN: Numero sequencial com 4 digitos (0001, 0002, etc)

Exemplos:
- TSC-0001 (The Scalable Company, item 1)
- UHTC-0011 (Ultra High Ticket Closer, item 11)
```

---

## FLUXO DE TRABALHO

### Para Nova Aba (sem schema):
1. Ler row 2 → Identificar fonte/empresa
2. Ler row 3 → Mapear headers
3. Ler amostra de dados (rows 4-20) → Entender estrutura
4. Identificar onde estao materiais (PDFs)
5. Determinar coluna de TAG
6. Criar prefixo baseado no nome
7. Adicionar ao schema

### Para Aba Existente (com schema):
1. Carregar configuracao do schema
2. Verificar se estrutura mudou
3. Identificar rows sem TAG
4. Adicionar TAGs faltantes
5. Atualizar schema se necessario

---

## ERROS COMUNS A EVITAR

| Erro | Consequencia | Prevencao |
|------|--------------|-----------|
| TAG em linha vazia | Polui dados | Verificar se row tem conteudo |
| TAG sobre PDF | Perde material | Verificar se celula esta vazia |
| TAG em coluna errada | Inconsistencia | Usar schema ou mapear estrutura |
| Pular numeracao | Gaps nas TAGs | Contar sequencialmente |
| Nao atualizar schema | Proxima sessao erra | Sempre gravar mudancas |
| Assumir estrutura | TAGs em lugar errado | SEMPRE ler antes de escrever |
| Ignorar materiais | Sobrescreve PDFs | Verificar conteudo existente |

---

## LICOES APRENDIDAS (2026-01-07)

### Caso Inner Circle Weekly
- **Erro**: TAGs colocadas em coluna I que tinha materiais em algumas rows
- **Correcao**: Mover TAGs para coluna K, preservar materiais em I
- **Licao**: Verificar TODAS as rows da coluna antes de assumir que esta vazia

### Caso Scale The Agency / 30 Days Challenge
- **Erro**: TAGs em coluna I quando havia PDFs em rows especificas
- **Correcao**: Mover TAGs para coluna J
- **Licao**: Uma coluna pode ter conteudo esparso (algumas rows vazias, outras com PDF)

### Padrao Identificado
```
TRANSCRIÇÃO → MATERIAIS (se houver) → TAG (primeira COMPLETAMENTE vazia)

Verificar "completamente vazia" significa:
- Ler TODA a coluna
- Se QUALQUER row tem conteudo que nao e TAG, essa coluna tem materiais
- TAG vai na proxima coluna
```

---

## ATUALIZACAO AUTOMATICA

Quando esta skill e executada e algum aprendizado novo ocorre:
1. Atualizar esta skill AUTOMATICAMENTE
2. Atualizar o schema AUTOMATICAMENTE
3. NAO perguntar ao usuario se deve atualizar
4. Apenas informar que atualizou

**Se aprendeu algo novo, grava. Sem perguntar.**

---

## COMANDOS RAPIDOS

```
/scan-planilha    → Verificar status de todas as abas
/ler-planilha     → Esta skill
```

---

## ARQUIVOS RELACIONADOS

- `.claude/mission-control/SPREADSHEET-SCHEMA.json` - Schema central
- `.claude/mission-control/SMART-SCAN.md` - Protocolo de scan
- `.claude/mission-control/AUDIT-REPORT-V2.json` - Ultimo audit

---

## EXEMPLO PRATICO

**Cenario:** Nova aba "Curso XYZ" sem TAGs

**Passo 1 - Ler headers (row 3):**
```
A: MODULO | B: AULA | C: TEMA | D: DURACAO | E: DRIVE | F: YOUTUBE | G: TRANSCRICAO | H: MATERIAL | I: (vazio)
```

**Passo 2 - Identificar estrutura:**
- Transcricao: G
- Material: H
- TAG deve ir em: I (primeira vazia)

**Passo 3 - Criar TAGs:**
- Prefix sugerido: XYZ
- Formato: XYZ-0001, XYZ-0002, etc

**Passo 4 - Aplicar:**
- Adicionar header I3 = "TAG"
- Adicionar TAGs em I4+ para rows com video
- Pular rows vazias/separadores
- Pular rows onde I ja tem arquivo

**Passo 5 - Atualizar schema**
