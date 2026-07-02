# Adapter Specifications — extract-knowledge

## Overview

Cada adapter transforma um tipo de input em **markdown unificado** com metadata de origem. O output de qualquer adapter é idêntico em shape:

```typescript
interface AdapterOutput {
  markdown: string;           // Conteúdo convertido para markdown
  source_metadata: {
    source_id: string;        // ID único da fonte (filename sem extensão, URL slug, etc.)
    source_name: string;      // Nome legível da fonte
    source_type: 'pdf' | 'session' | 'markdown' | 'youtube' | 'batch';
  };
}
```

---

## 1. PDF Adapter

**Módulo:** `services/etl/lib/pdf-parser.js` → classe `PdfParser`

**Input:** Caminho para ficheiro `.pdf`

**Processo:**
1. `PdfParser.parseFile(path)` → extrai texto + metadata
2. Verifica `isScanned` (< 100 chars/página) → se true, SKIP com VETO-EK-006
3. `PdfParser.textToMarkdown(text)` → normaliza quebras de linha, remove hifenização

**Metadata extraída do PDF:**
- title, author, subject, creator, producer
- creationDate, modDate, pdfVersion
- pages, charsPerPage

**Limitações:**
- PDFs scanned (imagens) não são processáveis sem OCR
- PDFs com layout complexo (colunas, tabelas) podem perder estrutura
- `services/etl/lib/ocr-handler.js` existe mas é experimental

---

## 2. Session Adapter

**Módulo:** Inline (skill lê contexto da conversa atual)

**Input:** Flag `--session` (sem path)

**Processo:**
1. Extrair mensagens da conversa atual (user messages + assistant responses)
2. Filtrar: ignorar tool calls curtos (< 50 chars), system messages, confirmações simples
3. Concatenar mensagens substantivas em markdown com separadores `---`
4. Cada mensagem mantém: role (user/assistant), timestamp aproximado, conteúdo

**Formato do markdown gerado:**
```markdown
## User Message
{conteúdo}

---

## Assistant Response
{conteúdo}

---
```

**source_metadata:**
```yaml
source_id: "session-{date}-{hash_8chars}"
source_name: "Claude Code session {date}"
source_type: session
```

**Nota:** Este adapter NÃO replica o pipeline completo de `extract-session-heuristics`. Para extração profunda de heurísticas com Pareto ao Cubo, decision cards, e promotion protocol, usar `/extract-session-heuristics`.

---

## 3. Markdown Adapter

**Módulo:** Direto (leitura de ficheiro)

**Input:** Caminho para ficheiro `.md` ou `.txt`

**Processo:**
1. Ler conteúdo do ficheiro
2. SE tem frontmatter YAML (`---\n...\n---`) → extrair metadata e remover do conteúdo
3. Retornar markdown limpo

**source_metadata:**
```yaml
source_id: "{filename_sem_extensão}"
source_name: "{filename}"
source_type: markdown
```

**Suporta:** `.md`, `.txt`, `.mdx`, `.rst` (tratados como texto plano)

---

## 4. YouTube Adapter

**Módulo:** MCP scrapling → `stealthy_fetch`

**Input:** URL de vídeo YouTube

**Processo:**
1. Chamar scrapling MCP com `stealthy_fetch(url)` para obter HTML da página
2. Extrair transcrição do HTML:
   - Procurar por dados de transcrição no HTML (ytInitialPlayerResponse ou timedtext)
   - SE transcrição não disponível → avisar e abortar
3. Converter transcrição para markdown (timestamps opcionais como headings)

**Formato do markdown gerado:**
```markdown
# {título do vídeo}

**Channel:** {nome do canal}
**URL:** {url}

## Transcript

{texto da transcrição}
```

**source_metadata:**
```yaml
source_id: "{video_id}"
source_name: "YouTube: {título}"
source_type: youtube
```

**Limitações:**
- Depende do MCP scrapling estar disponível
- Nem todos os vídeos têm transcrição
- Transcrições auto-geradas podem ter erros de reconhecimento

---

## 5. Batch Adapter

**Módulo:** Composição dos adapters acima

**Input:** Diretório com ficheiros mistos

**Processo:**
1. Listar ficheiros no diretório (não-recursivo por default)
2. Filtrar por extensões suportadas: `.pdf`, `.md`, `.txt`
3. Ordenar alfabeticamente
4. Aplicar `--limit` se especificado
5. Para cada ficheiro: selecionar adapter por extensão e processar
6. Retornar array de `AdapterOutput`

**source_metadata por ficheiro:** delegado ao adapter específico

**Regras de batch:**
- Rate limiting: 3 segundos entre PDFs (protecção de rate limit da API)
- Falha em 1 ficheiro não aborta o batch — log error e continuar
- Report final inclui: processados/total, erros, entidades por ficheiro

---

## Error Handling

| Erro | Adapter | Ação |
|------|---------|------|
| Ficheiro não encontrado | PDF, Markdown | ABORT com mensagem |
| PDF scanned | PDF | SKIP (VETO-EK-006) |
| Transcrição indisponível | YouTube | ABORT com sugestão de alternativa |
| MCP scrapling não disponível | YouTube | ABORT com mensagem |
| Ficheiro vazio ou < 200 chars | Todos | ABORT (VETO-EK-001) |
| Encoding inválido | Markdown | Tentar UTF-8 → Latin-1 → ABORT |
