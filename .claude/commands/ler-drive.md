---
description: Lê e cria recursos do Google Drive (planilhas, pastas, documentos) via MCP
tags: [mcp, gdrive, sheets, docs, automation]
---

# /ler-drive

Explora, lê e **cria** recursos do Google Drive conectado via MCP.

## MODOS DE USO

### 1. Listar recursos disponíveis
```
/ler-drive
```
→ Mostra todos os recursos do Google Drive conectados

### 2. Ler planilha específica
```
/ler-drive [nome ou parte do nome]
```
→ Busca e lê a planilha correspondente

**Exemplos:**
- `/ler-drive BENCH` → Lê "[BENCH] ESTRUTURA COMERCIAL"
- `/ler-drive [Sua Empresa]` → Lê "Ferramentas [Sua Empresa] 2025 [MATRIZ]"
- `/ler-drive Fixos` → Lê "Fixos 2025 | [Sua Empresa] V.2"

### 3. Explorar pasta
```
/ler-drive pasta:[nome]
```
→ Lista conteúdo da pasta

**Exemplos:**
- `/ler-drive pasta:Acervo`
- `/ler-drive pasta:Estratégia`

### 4. Criar documento Google Docs (NOVO!)
```
/ler-drive criar:[titulo] --arquivo [path]
/ler-drive criar:[titulo] --conteudo "texto direto"
```
→ Cria um novo Google Doc com o conteúdo especificado

**Exemplos:**
- `/ler-drive criar:Relatório Mensal --arquivo logs/relatorio.md`
- `/ler-drive criar:Notas Rápidas --conteudo "Texto do documento"`
- `/ler-drive criar:Backup DOSSIER --arquivo knowledge/external/dossiers/persons/DOSSIER-COLE-GORDON.md`

## COMPORTAMENTO

**Ao executar, Claude deve:**

1. **Listar recursos** (se sem argumentos)
   - Mostrar tabela com: Nome | Tipo | ID
   - Separar por: Planilhas, Pastas, Documentos

2. **Ler planilha** (se argumento fornecido)
   - Buscar por nome parcial (case-insensitive)
   - Ler primeiras 50 linhas de todas as abas
   - Identificar estrutura: colunas, tipos de dados
   - **DESTACAR URLs** encontradas (YouTube, Google Docs, etc.)
   - Mostrar resumo executivo

3. **Explorar pasta** (se prefixo `pasta:`)
   - Listar arquivos dentro da pasta
   - Mostrar tipos e tamanhos
   - Identificar arquivos processáveis (planilhas, docs)

4. **Auto-detectar links**
   - Escanear células em busca de URLs
   - Categorizar: YouTube, Google Docs, PDFs, externos
   - Sugerir `/jarvis-full` para URLs de vídeo

## OUTPUT ESPERADO

### Para Planilhas:
```markdown
## 📊 [NOME DA PLANILHA]

**ID:** [spreadsheet_id]
**Abas:** [lista de abas]

### 📋 Estrutura Detectada

| Coluna | Tipo | Exemplo |
|--------|------|---------|
| A | Texto | "Nome do curso" |
| B | URL | https://youtube.com/... |
| C | Status | "Pendente" |

### 🔗 URLs Encontradas (12)

**YouTube (8):**
- [Linha 5] https://youtube.com/watch?v=...
- [Linha 7] https://youtube.com/watch?v=...

**Google Docs (4):**
- [Linha 3] https://docs.google.com/...

### 💡 Sugestões
- [ ] Processar 8 vídeos do YouTube via `/jarvis-full`
- [ ] Ingerir 4 Google Docs via MCP
- [ ] Atualizar Status após processamento
```

### Para Pastas:
```markdown
## 📁 [NOME DA PASTA]

**Conteúdo (15 itens):**

| Nome | Tipo | Processável |
|------|------|-------------|
| Curso 1.pdf | PDF | ✅ SIM |
| Planilha.xlsx | Spreadsheet | ✅ SIM |
| Video.mp4 | Video | ⚠️ Precisa link |
```

## INTEGRAÇÕES

**Após ler planilha com URLs, sugerir automaticamente:**

1. **Comando de lote:**
   ```bash
   # Processar todos os vídeos encontrados
   /jarvis-batch --from-gdrive [spreadsheet_id] --col [coluna_url]
   ```

2. **Atualização de status:**
   ```bash
   # Atualizar coluna Status após processar
   /update-gdrive [spreadsheet_id] --row [N] --col "Status" --value "Processado"
   ```

## CASOS DE USO

### Caso 1: Acervo de Aprendizado
```
/ler-drive Acervo
→ Lista cursos/vídeos pendentes
→ Identifica URLs do YouTube
→ Sugere processamento em lote
```

### Caso 2: Estrutura Comercial
```
/ler-drive BENCH
→ Lê benchmarks e estrutura
→ Extrai KPIs e métricas
→ Sugere atualização de agentes (CRO, CFO)
```

### Caso 3: Ferramentas [Sua Empresa]
```
/ler-drive [Sua Empresa]
→ Lê matriz de ferramentas
→ Identifica stack tecnológico
→ Atualiza AGENT-COO.md
```

## REGRAS DE EXECUÇÃO

1. **SEMPRE** usar `mcp__gdrive__gdrive_search` para buscar
2. **SEMPRE** usar `mcp__gdrive__gsheets_read` para planilhas
3. **SEMPRE** usar `mcp__gdrive__gdocs_create` para criar documentos
4. **SEMPRE** destacar URLs em formato de lista
5. **SEMPRE** sugerir próximos passos (comandos)
6. **NUNCA** processar automaticamente sem confirmar com usuário

## ARGUMENTOS AVANÇADOS

```
/ler-drive [nome] --extract-urls    # Apenas extrair URLs
/ler-drive [nome] --format json     # Output JSON
/ler-drive [nome] --col [letra]     # Ler apenas coluna específica
```

## FERRAMENTAS MCP DISPONÍVEIS

| Ferramenta | Uso |
|------------|-----|
| `mcp__gdrive__gdrive_search` | Buscar arquivos e pastas |
| `mcp__gdrive__gdrive_read_file` | Ler conteúdo de arquivo |
| `mcp__gdrive__gsheets_read` | Ler planilhas |
| `mcp__gdrive__gsheets_update_cell` | Atualizar célula em planilha |
| `mcp__gdrive__gdocs_create` | **NOVO** - Criar Google Docs |

## SCRIPT DE CRIAÇÃO DE DOCUMENTOS

Para criar documentos diretamente via linha de comando:

```bash
# Sintaxe
python scripts/gdocs_full_auth.py "Título do Documento" "caminho/arquivo.md" [folder_id]

# Exemplos
python scripts/gdocs_full_auth.py "Meu Relatório" "arquivo.md"
python scripts/gdocs_full_auth.py "Backup DOSSIER" "knowledge/external/dossiers/persons/DOSSIER-COLE-GORDON.md"
```

---

**Criado em:** 2025-12-21
**Atualizado em:** 2025-12-28
**Versão:** 2.0.0

## CHANGELOG

- **v2.0.0** (2025-12-28): Adicionado suporte a criação de Google Docs
- **v1.0.0** (2025-12-21): Versão inicial com leitura de planilhas e pastas
