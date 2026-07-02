# Mega Brain

> Sistema de gestao de conhecimento por IA. Voce ingere o seu proprio material
> (videos, PDFs, transcricoes), o sistema extrai o DNA cognitivo e os insights,
> e tudo fica indexado num RAG de busca hibrida. Em cima dessa base, o
> **Conclave** — um conselho multi-agente — delibera as suas decisoes estrategicas
> fundamentado exclusivamente no conhecimento que voce inseriu.

Funciona dentro do [Claude Code](https://claude.ai/claude-code), com comandos como
`/ingest`, `/process-jarvis`, `/conclave` e `/jarvis-briefing`. Tudo roda
local-first: o seu conhecimento vive no filesystem do projeto, sob o seu controle.

---

## O que e o Mega Brain

O Mega Brain transforma material bruto de especialistas em conhecimento operavel.
Sao tres camadas:

1. **Ingestao (Pipeline MCE).** Voce joga o seu material no sistema com `/ingest`
   (link de video, PDF, transcricao, arquivo local). O pipeline transcreve,
   organiza, fatia em chunks semanticos e extrai o **DNA cognitivo** em 10 camadas
   (filosofias, modelos mentais, heuristicas, frameworks, metodologias, padroes de
   comportamento, hierarquia de valores, voz, obsessoes e paradoxos).

2. **RAG (busca hibrida).** O conhecimento extraido e indexado para busca por
   significado (vetorial) combinada com busca por termos (BM25). Voce consulta a
   base por intencao, nao so por palavra-chave — e cada resposta cita a fonte.

3. **Conclave (a feature hero).** Um conselho multi-agente que delibera decisoes
   estrategicas. Os conselheiros — **Critico Metodologico**, **Advogado do Diabo** e
   **Sintetizador** — debatem a sua pergunta usando *somente* o conhecimento que
   voce ingeriu. Zero achismo: as posicoes sao fundamentadas em evidencias citadas
   da sua propria base.

O resultado e um cerebro externo que pensa com o seu material e te ajuda a decidir
com rigor.

---

## Pre-requisitos

| Requisito | Versao | Para que serve |
|-----------|--------|----------------|
| [Claude Code](https://claude.ai/claude-code) | atual | Interface onde os comandos `/ingest`, `/conclave` etc. rodam |
| [Node.js](https://nodejs.org) | 18 ou superior | CLI e ferramentas do sistema |
| [Python](https://python.org) | 3.10 ou superior | Engine de processamento (pipeline MCE, RAG, transcricao) |
| Git | atual | Clonar e atualizar o repositorio |

Voce tambem vai precisar de pelo menos as **chaves de API obrigatorias** (ver
secao [Chaves de API necessarias](#chaves-de-api-necessarias)).

---

## Instalacao

O Mega Brain e distribuido como um repositorio privado, por convite. Voce clona,
instala as dependencias, configura as chaves e ja pode usar.

```bash
# 1. Clone o repositorio
git clone <url-do-repositorio> mega-brain
cd mega-brain

# 2. Instale as dependencias Node
npm install

# 3. Instale as dependencias Python
pip install -r requirements.txt
#    (recomendado: use um virtualenv)
#    python -m venv .venv && source .venv/bin/activate   # Linux/macOS
#    python -m venv .venv && .venv\Scripts\activate       # Windows

# 4. Configure as chaves de API
cp .env.example .env
#    Abra o .env e preencha as suas chaves (veja a secao abaixo)

# 5. Abra o projeto no Claude Code e comece a usar
#    Ex.: /jarvis-briefing para ver o status do sistema
```

O `.env` e a unica fonte de credenciais e ja esta protegido pelo `.gitignore` —
ele nunca vai para o repositorio.

---

## Comandos principais

Todos rodam dentro do Claude Code, no diretorio do projeto.

| Comando | O que faz |
|---------|-----------|
| `/ingest <fonte>` | Ingere material novo (link de video, PDF, transcricao ou arquivo local). Inicia o Pipeline MCE. |
| `/process-jarvis` | Processa o material da fila pelo pipeline: transcricao, chunking, extracao de DNA e indexacao no RAG. |
| `/conclave "<pergunta>"` | Abre uma sessao do conselho multi-agente para deliberar uma decisao estrategica, citando a sua base. |
| `/jarvis-briefing` | Mostra o status operacional do sistema: o que ja foi processado, agentes ativos e fila pendente. |

Fluxo tipico: `/ingest` o seu material -> `/process-jarvis` para extrair o
conhecimento -> `/conclave` para decidir com base nele. Veja o
[QUICK-START.md](QUICK-START.md) para o passo a passo completo.

---

## Chaves de API necessarias

O Mega Brain usa provedores de IA externos. Configure-os no arquivo `.env`
(copiado de `.env.example`). Guia detalhado de como obter cada uma:
[docs/api-keys-guide.md](docs/api-keys-guide.md).

### Obrigatorias

| Chave | Para que serve | Onde obter |
|-------|----------------|------------|
| `ANTHROPIC_API_KEY` | LLM nucleo. Roda toda a inteligencia: processamento, agentes, Conclave e extracao de DNA. | [console.anthropic.com](https://console.anthropic.com/) |
| `OPENAI_API_KEY` | Transcricao de audio/video (Whisper) e embeddings do RAG (provedor canonico da busca semantica). | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `GEMINI_API_KEY` *(ou `GOOGLE_API_KEY`)* | Extracao e analise visual de video — identifica quem fala e o assunto durante a ingestao. Obrigatoria para ingerir video. | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |

> O sistema le `GEMINI_API_KEY` primeiro e, se ausente, `GOOGLE_API_KEY`. Defina
> apenas uma das duas. Se voce nao for ingerir video, essa chave deixa de ser
> obrigatoria na pratica.

### Recomendada

| Chave | Para que serve | Onde obter |
|-------|----------------|------------|
| `VOYAGE_API_KEY` | Provedor de embeddings alternativo para o RAG. Opcional — a busca semantica ja funciona com `OPENAI_API_KEY` sozinho. | [dash.voyageai.com](https://dash.voyageai.com/) |

### Opcionais (voz e transcricao avancada)

| Chave | Para que serve | Onde obter |
|-------|----------------|------------|
| `ELEVENLABS_API_KEY` | Voz do JARVIS (Text-to-Speech). | [elevenlabs.io](https://elevenlabs.io/) |
| `DEEPGRAM_API_KEY` | Speech-to-Text — ouvir comandos por voz. | [console.deepgram.com](https://console.deepgram.com/) |
| `ASSEMBLYAI_API_KEY` | Transcricao na nuvem com diarizacao de falantes ("quem falou o que"); alternativa ao Whisper local. | [assemblyai.com](https://www.assemblyai.com/) |

A maioria dos provedores tem plano gratuito generoso. Voce pode comecar so com as
obrigatorias e ativar as demais quando precisar.

---

## Arquitetura (visao geral)

```
mega-brain/
├── engine/         → Engine Python: Pipeline MCE, RAG, transcricao, JARVIS
├── agents/         → Agentes de IA (incluindo o sistema Conclave)
├── knowledge/      → Sua base de conhecimento (material extraido, indexado pelo RAG)
├── workspace/      → Dados do seu negocio (contexto para as deliberacoes)
├── .claude/        → Integracao com o Claude Code (comandos, hooks, skills)
├── docs/           → Guias e documentacao
├── .env            → Suas chaves de API (gitignored — nunca versionado)
└── .env.example    → Modelo para criar o seu .env
```

O conhecimento e armazenado em **buckets isolados** (conhecimento externo de
especialistas, dados do seu negocio, notas pessoais), sem contaminacao cruzada.
Cada bucket tem o seu indice RAG.

---

## Stack

- **Node.js 18+** — CLI e tooling.
- **Python 3.10+** — engine de processamento (pipeline, RAG, transcricao).
- **Local-first** — o conhecimento vive no filesystem do projeto. Nenhum banco de
  dados externo e obrigatorio para usar o sistema.

---

## Suporte

- Documentacao completa em [`docs/`](docs/).
- Inicio rapido: [QUICK-START.md](QUICK-START.md).
- Guia de chaves de API: [docs/api-keys-guide.md](docs/api-keys-guide.md).

---

*Mega Brain — `@thiagofinch/mega-brain`*
