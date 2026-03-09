# QUICK START - Mega Brain

**Para começar AGORA em 4 passos:**

---

## 📦 PASSO 1: Adicionar Materiais

```bash
# Navegar para o projeto
# Navigate to the Mega Brain project root
cd "<your-AIOX-GPS-path>"

# Copiar materiais para pastas corretas
cp ~/Downloads/hormozi-curso/*.mp4 00-raw-materials/HORMOZI/videos/
cp ~/Downloads/hormozi-ebooks/*.pdf 00-raw-materials/HORMOZI/pdfs/


cp ~/Downloads/call-funnel/*.pdf 00-raw-materials/CALL-FUNNEL/pdfs/

cp ~/Documents/processos-internos/*.pdf 00-raw-materials/INTERNO-OWNER/pdfs/
cp ~/gravacoes/*.mp4 00-raw-materials/INTERNO-OWNER/videos/
```

---

## 🎤 PASSO 2: Transcrever Vídeos

```bash
# Transcrever cada fonte (roda automático, pode demorar horas)
./00-raw-materials/TRANSCRIBE-AND-CATALOG.sh HORMOZI
./00-raw-materials/TRANSCRIBE-AND-CATALOG.sh INTERNO-OWNER
./00-raw-materials/TRANSCRIBE-AND-CATALOG.sh CALL-FUNNEL
```

**Deixa rodar.** Whisper vai transcrever tudo automaticamente.

**Resultado:**
```
HORMOZI/transcripts/aula-01.txt ✅
HORMOZI/transcripts/aula-02.txt ✅
...
```

---

## 📊 PASSO 3: Verificar Catálogo

Abrir e atualizar:
```
00-raw-materials/MASTER-CATALOG.md
```

Adicionar materiais na tabela de cada fonte:

```markdown
### HORMOZI
| # | Arquivo | Tipo | Descrição | Processado? |
|---|---------|------|-----------|-------------|
| 1 | aula-01.txt | Transcrição | Offers Framework | ❌ Pendente |
| 2 | aula-02.txt | Transcrição | Scripts vendas | ❌ Pendente |
```

---

## 🤖 PASSO 4: Processar com MASTER AGENT

No Claude Code:

```
"MASTER AGENT, inicie processamento completo.

Prioridade:
1. INTERNO-OWNER (contexto primário)
2. HORMOZI
3. CALL-FUNNEL

Rastreie a fonte de cada insight.
Identifique diferenças entre modelos de negócio.
Documente conflitos e resolva com justificativa."
```

**Ou processar fonte por fonte:**

```
"MASTER AGENT, processe todos os materiais de INTERNO-OWNER"
```

Aguardar conclusão (2-3h por fonte, automático).

Depois:
```
"MASTER AGENT, processe todos os materiais de HORMOZI"
"MASTER AGENT, processe todos os materiais de CALL-FUNNEL"
```

---

## ✅ PASSO 5: Gerar Playbook

Após processar todas as fontes:

```
"MASTER AGENT, gere checkpoint de validação"
```

Aguardar relatório de conflitos resolvidos.

Depois:
```
"MASTER AGENT, gere o Master Playbook v1.0"
```

**RESULTADO:**
```
02-master-playbook/MASTER-PLAYBOOK-v1.0-COMPLETE.md
```

**200-300 páginas de estratégia completa para 10M+/mês.**

---

## 🔥 COMANDOS DE EMERGÊNCIA

### Verificar materiais:
```bash
# Listar vídeos
ls -la 00-raw-materials/HORMOZI/videos/

# Contar transcrições
ls 00-raw-materials/HORMOZI/transcripts/ | wc -l

# Ver estrutura completa
tree 00-raw-materials/ -L 2
```

### Transcrever em massa:
```bash
# Todas as fontes de uma vez
  echo "Transcrevendo $SOURCE..."
  ./00-raw-materials/TRANSCRIBE-AND-CATALOG.sh $SOURCE
done
```

### Verificar Whisper:
```bash
# Testar instalação
which whisper

# Se não tiver, instalar
pip install openai-whisper
```

---

## 📚 DOCUMENTAÇÃO COMPLETA

- **Guia detalhado:** `00-raw-materials/GUIA-COMPLETO-DE-USO.md`
- **Estrutura de fontes:** `00-raw-materials/SOURCE-REGISTRY.md`
- **Protocolo de iteração:** `04-iteration-versions/ITERATION-PROTOCOL.md`

---

## ⏱️ TIMELINE ESPERADA

**50 materiais total:**

| Etapa | Tempo | Automático? |
|-------|-------|-------------|
| Organizar materiais | 2h | ❌ Manual |
| Transcrever vídeos | 8h | ✅ Sim (Whisper) |
| Processar INTERNO-OWNER | 2-3h | ✅ Sim (MASTER AGENT) |
| Processar HORMOZI | 3-4h | ✅ Sim |
| Processar CALL-FUNNEL | 1-2h | ✅ Sim |
| Checkpoint + Síntese | 2-3h | ✅ Sim |
| **TOTAL** | **~7 dias** | **80% automático** |

**Seu tempo ativo:** 10-15h apenas
**Tempo do sistema trabalhando:** 15-20h

---

## 🎯 RESULTADO FINAL

Ao completar, você terá:

✅ **4 Knowledge Bases completas** (CFO, CRO, CMO, COO)
✅ **500+ insights extraídos e rastreados**
✅ **Conflitos entre fontes resolvidos**
✅ **Decisões justificadas com fontes citadas**
✅ **Master Playbook v1.0 completo** (200-300 páginas)
✅ **Roadmap de 90 dias acionável**
✅ **Playbook worth R$1M+**

---

**Comece agora:** Organize seus materiais nas pastas e rode o primeiro comando de transcrição!
