# Guia de Chaves de API — Mega Brain

> Como obter cada chave necessaria e como o sistema usa cada uma.

O Mega Brain usa provedores de IA externos para transcrever, extrair e raciocinar
sobre o seu material. Este guia cobre todas as chaves: o que cada uma faz, se e
obrigatoria ou opcional, onde obter e como configurar.

Todas as chaves ficam no arquivo `.env` na raiz do projeto (copiado de
`.env.example`). O `.env` e a unica fonte de credenciais e ja esta protegido pelo
`.gitignore` — ele nunca vai para o repositorio.

---

## Visao geral

| Chave | Status | Para que serve |
|-------|:------:|----------------|
| `ANTHROPIC_API_KEY` | Obrigatoria | LLM nucleo: processamento, agentes, Conclave, extracao de DNA |
| `OPENAI_API_KEY` | Obrigatoria | Transcricao (Whisper) e embeddings do RAG (busca semantica) |
| `GEMINI_API_KEY` *(ou `GOOGLE_API_KEY`)* | Obrigatoria p/ video | Extracao e analise visual de video na ingestao |
| `VOYAGE_API_KEY` | Recomendada | Provedor de embeddings alternativo para o RAG |
| `ELEVENLABS_API_KEY` | Opcional | Voz do JARVIS (Text-to-Speech) |
| `DEEPGRAM_API_KEY` | Opcional | Speech-to-Text (ouvir comandos por voz) |
| `ASSEMBLYAI_API_KEY` | Opcional | Transcricao na nuvem com diarizacao de falantes |

---

## 1. Anthropic (Claude) — OBRIGATORIA

### Como o sistema usa
Claude e o cerebro do Mega Brain. Toda a inteligencia roda aqui: o processamento
do material, os agentes especializados, o Conclave e a extracao de DNA cognitivo.
Sem essa chave, o sistema nao funciona.

### Onde obter
[https://console.anthropic.com/](https://console.anthropic.com/)

### Passo a passo
1. Acesse [console.anthropic.com](https://console.anthropic.com/) e faca login (ou crie a conta).
2. Confirme o seu email.
3. No menu lateral, va em **API Keys**.
4. Clique em **Create Key** e de um nome descritivo (ex.: `mega-brain`).
5. Copie a chave gerada (comeca com `sk-ant-...`).
6. Em **Billing**, adicione creditos (minimo de US$5).

### Como configurar
```bash
# no arquivo .env
ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui
```

### Como testar
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":50,"messages":[{"role":"user","content":"Diga ok"}]}'
```
Resposta esperada: um JSON contendo `"text": "Ok"` (ou similar).

---

## 2. OpenAI — OBRIGATORIA

### Como o sistema usa
Duas funcoes centrais:
- **Transcricao (Whisper):** converte audio e video em texto durante a ingestao.
- **Embeddings do RAG:** e o provedor canonico da busca semantica
  (`text-embedding-3-large`). Sem essa chave, o RAG nao consegue indexar nem
  consultar o conhecimento por significado.

### Onde obter
[https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Passo a passo
1. Acesse [platform.openai.com](https://platform.openai.com/) e faca login (ou crie a conta).
2. Va em **API keys** (menu do perfil ou [platform.openai.com/api-keys](https://platform.openai.com/api-keys)).
3. Clique em **Create new secret key**, de um nome (ex.: `mega-brain`).
4. Copie a chave imediatamente (comeca com `sk-...`) — ela so e mostrada uma vez.
5. Em **Billing**, garanta que ha saldo/metodo de pagamento ativo.

### Como configurar
```bash
# no arquivo .env
OPENAI_API_KEY=sk-sua-chave-aqui
```

### Como testar
```bash
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":"teste de embedding","model":"text-embedding-3-large"}'
```
Resposta esperada: um JSON com um array `data` contendo o vetor de embedding.

---

## 3. Google Gemini — OBRIGATORIA PARA VIDEO

### Como o sistema usa
O Gemini faz a extracao e a analise **visual** de video durante a ingestao
(Speaker Visual Gate): identifica quem fala e o assunto do conteudo. E necessaria
para ingerir video. Se voce so trabalha com PDFs, transcricoes e textos, na
pratica ela deixa de ser obrigatoria.

> O sistema procura a chave nesta ordem: primeiro `GEMINI_API_KEY`, depois
> `GOOGLE_API_KEY`. Defina apenas **uma** das duas. Quando a chave esta ausente, o
> sistema apenas pula a etapa visual (`[pre_07] BYPASSED`) sem quebrar a ingestao.

### Onde obter
[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### Passo a passo
1. Acesse [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) e faca login com a sua conta Google.
2. Clique em **Create API key** (crie ou selecione um projeto Google Cloud).
3. Copie a chave gerada (comeca com `AIza...`).

### Como configurar
```bash
# no arquivo .env (escolha apenas uma)
GEMINI_API_KEY=AIza-sua-chave-aqui
# GOOGLE_API_KEY=AIza-sua-chave-aqui
```

### Como testar
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY"
```
Resposta esperada: um JSON listando os modelos disponiveis (confirma que a chave e valida).

---

## 4. Voyage AI — RECOMENDADA

### Como o sistema usa
Provedor de embeddings alternativo para o RAG. E **opcional**: a busca semantica
ja funciona usando o `OPENAI_API_KEY` como provedor canonico. Configure a Voyage
se voce preferir um provedor de embeddings dedicado.

### Onde obter
[https://dash.voyageai.com/](https://dash.voyageai.com/)

### Passo a passo
1. Acesse [dash.voyageai.com](https://dash.voyageai.com/) e faca login (aceita Google/GitHub).
2. Va em **API Keys** e clique em **Create new API key**.
3. De um nome (ex.: `mega-brain`) e copie a chave (comeca com `pa-...`).

### Como configurar
```bash
# no arquivo .env
VOYAGE_API_KEY=pa-sua-chave-aqui
```

### Como testar
```bash
curl https://api.voyageai.com/v1/embeddings \
  -H "Authorization: Bearer $VOYAGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":["teste de embedding"],"model":"voyage-3"}'
```
Resposta esperada: um JSON com um array `data` contendo o vetor de embedding.

---

## 5. ElevenLabs — OPCIONAL

### Como o sistema usa
Da voz ao JARVIS (Text-to-Speech): transforma texto em audio com voz natural. So
e necessaria se voce ativar a interacao por voz.

### Onde obter
[https://elevenlabs.io/](https://elevenlabs.io/)

### Passo a passo
1. Acesse [elevenlabs.io](https://elevenlabs.io/) e crie a conta (aceita login com Google).
2. Clique no seu avatar (canto inferior esquerdo) e va em **Profile + API key**.
3. Em **API Key**, clique em **Reveal** ou **Create** e copie a chave (comeca com `sk_...`).

### Como configurar
```bash
# no arquivo .env
ELEVENLABS_API_KEY=sk_sua-chave-aqui
```

---

## 6. Deepgram — OPCIONAL

### Como o sistema usa
Speech-to-Text para o JARVIS: permite dar comandos por voz, convertendo a sua fala
em texto. So e necessaria para a interacao por voz.

### Onde obter
[https://console.deepgram.com/](https://console.deepgram.com/)

### Passo a passo
1. Acesse [console.deepgram.com](https://console.deepgram.com/) e crie a conta (aceita Google/GitHub).
2. Va em **API Keys** no menu lateral e clique em **Create a New API Key**.
3. De um nome (ex.: `mega-brain`), selecione a permissao adequada e clique em **Create Key**.
4. Copie a chave imediatamente — ela nao sera mostrada de novo.

### Como configurar
```bash
# no arquivo .env
DEEPGRAM_API_KEY=sua-chave-aqui
```

### Como testar
```bash
curl -X GET "https://api.deepgram.com/v1/projects" \
  -H "Authorization: Token $DEEPGRAM_API_KEY"
```
Resposta esperada: um JSON listando os seus projetos (confirma que a chave e valida).

---

## 7. AssemblyAI — OPCIONAL

### Como o sistema usa
Transcricao de audio/video na nuvem com **diarizacao de falantes** — identifica
"quem falou o que". E uma alternativa ao Whisper local; util quando voce processa
reunioes ou conteudo com varios participantes. Quando ausente, o sistema usa o
Whisper local como fallback.

### Onde obter
[https://www.assemblyai.com/](https://www.assemblyai.com/)

### Passo a passo
1. Acesse [assemblyai.com](https://www.assemblyai.com/) e crie a conta.
2. No **Dashboard**, localize a secao **API Keys**.
3. Copie a sua chave de API.

### Como configurar
```bash
# no arquivo .env
ASSEMBLYAI_API_KEY=sua-chave-aqui
```

---

## Arquivo .env completo (exemplo)

Apos obter as chaves desejadas, o seu `.env` deve ficar parecido com isto
(use os seus valores reais no lugar dos placeholders):

```bash
# === OBRIGATORIAS ===
ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui
OPENAI_API_KEY=sk-sua-chave-aqui
GEMINI_API_KEY=AIza-sua-chave-aqui     # ou GOOGLE_API_KEY

# === RECOMENDADA ===
# VOYAGE_API_KEY=pa-sua-chave-aqui

# === OPCIONAIS (voz e transcricao avancada) ===
# ELEVENLABS_API_KEY=sk_sua-chave-aqui
# DEEPGRAM_API_KEY=sua-chave-aqui
# ASSEMBLYAI_API_KEY=sua-chave-aqui
```

---

## Duvidas frequentes

**Posso comecar so com as chaves obrigatorias?**
Sim. Com `ANTHROPIC_API_KEY` e `OPENAI_API_KEY` voce ja processa texto/PDF,
indexa no RAG e roda o Conclave. A `GEMINI_API_KEY` so e necessaria para ingerir
video.

**As chaves opcionais cobram se eu nao usar?**
Nao. A maioria dos provedores tem plano gratuito. Voce so e cobrado se ultrapassar
os limites do plano.

**Posso trocar de chave depois?**
Sim. Basta atualizar o valor no `.env` e reiniciar a sessao do Claude Code.

**Minha chave parou de funcionar. O que faco?**
Verifique se: (1) a chave nao expirou, (2) ha saldo/creditos na conta, (3) a chave
foi copiada sem espacos extras. Em caso de duvida, gere uma nova chave.

**Onde fica o `.env`?**
Na raiz do projeto. Copie-o de `.env.example` e nunca o versione — ele ja esta no
`.gitignore`.
