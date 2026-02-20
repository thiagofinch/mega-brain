# Guia de API Keys - Mega Brain

> Como obter e configurar cada API key do sistema.

Este guia cobre todas as API keys utilizadas pelo Mega Brain. Apenas a **Anthropic (Claude)** é obrigatória. Todas as demais são opcionais e adicionam funcionalidades extras.

---

## Visão Geral

| API Key | Obrigatória | Funcionalidade | Custo Estimado |
|---------|:-----------:|----------------|----------------|
| **Anthropic (Claude)** | Sim | LLM principal - processamento, agentes, Conclave | ~$5-20/mês |
| **ElevenLabs** | Não | JARVIS falando (Text-to-Speech) | Gratuito até 10k chars/mês |
| **Deepgram** | Não | JARVIS ouvindo (Speech-to-Text) | Gratuito até 45h/mês (Nova-2) |
| **Google Drive** | Não | Importar documentos do Google Drive | Gratuito |
| **Voyage AI** | Não | Busca semântica (RAG) via embeddings | Gratuito até 50M tokens |

---

## 1. Anthropic (Claude) - OBRIGATORIA

### O que faz

Claude é o cérebro do Mega Brain. Toda a inteligência do sistema -- processamento de materiais, agentes especializados, Conclave, extração de DNA -- roda via Claude.

### Onde obter

**URL:** [https://console.anthropic.com/](https://console.anthropic.com/)

### Passo a passo

1. Acesse [console.anthropic.com](https://console.anthropic.com/)
2. Clique em **Sign Up** (ou faça login se já tiver conta)
3. Confirme seu email
4. No painel, vá em **API Keys** no menu lateral
5. Clique em **Create Key**
6. Dê um nome descritivo: `mega-brain-prod`
7. Copie a chave gerada (começa com `sk-ant-...`)
8. Adicione créditos em **Billing** > **Add Credits** (mínimo $5)

### Como configurar

```bash
# No arquivo .env do Mega Brain
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

### Como testar

```bash
# No terminal, execute:
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":50,"messages":[{"role":"user","content":"Diga ok"}]}'
```

**Resposta esperada:** Um JSON contendo `"text": "Ok"` (ou similar).

### Custos típicos

| Uso | Custo Aproximado |
|-----|------------------|
| Processar 1 vídeo de 40 min | ~$0.10-0.30 |
| Sessão do Conclave | ~$0.05-0.15 |
| Extração de DNA (5 materiais) | ~$0.50-1.00 |
| Uso diário moderado | ~$1-3/dia |

---

## 2. ElevenLabs - OPCIONAL

### O que faz

Permite que o JARVIS fale em voz alta. Transforma texto em áudio com voz natural e realista. Usado no dashboard de voz do JARVIS (`/jarvis-painel`).

### Onde obter

**URL:** [https://elevenlabs.io/](https://elevenlabs.io/)

### Passo a passo

1. Acesse [elevenlabs.io](https://elevenlabs.io/)
2. Clique em **Sign Up** (aceita login com Google)
3. Confirme seu email
4. No painel, clique no seu avatar (canto inferior esquerdo)
5. Vá em **Profile + API key**
6. Na seção **API Key**, clique em **Reveal** ou **Create**
7. Copie a chave (começa com `sk_...`)

### Como configurar

```bash
# No arquivo .env do Mega Brain
ELEVENLABS_API_KEY=sk_sua-chave-aqui
```

### Como testar

```bash
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/[VOICE_ID_RACHEL]" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"Teste do JARVIS","model_id":"eleven_multilingual_v2"}' \
  --output teste-jarvis.mp3
```

**Resultado esperado:** Um arquivo `teste-jarvis.mp3` com a frase "Teste do JARVIS" em áudio.

### Planos

| Plano | Caracteres/mês | Custo |
|-------|----------------|-------|
| Free | 10.000 | Gratuito |
| Starter | 30.000 | $5/mês |
| Creator | 100.000 | $22/mês |

Para uso normal do JARVIS, o plano Free ou Starter é suficiente.

---

## 3. Deepgram - OPCIONAL

### O que faz

Permite que o JARVIS ouça você. Transforma áudio/voz em texto (Speech-to-Text). Usado para interação por voz com o JARVIS no dashboard.

### Onde obter

**URL:** [https://console.deepgram.com/](https://console.deepgram.com/)

### Passo a passo

1. Acesse [console.deepgram.com](https://console.deepgram.com/)
2. Clique em **Sign Up** (aceita login com Google/GitHub)
3. Confirme seu email
4. No painel, vá em **API Keys** no menu lateral
5. Clique em **Create a New API Key**
6. Dê um nome: `mega-brain`
7. Em permissões, selecione **Member** (acesso completo)
8. Clique em **Create Key**
9. Copie a chave gerada imediatamente (ela não será mostrada novamente)

### Como configurar

```bash
# No arquivo .env do Mega Brain
DEEPGRAM_API_KEY=sua-chave-aqui
```

### Como testar

```bash
curl -X POST "https://api.deepgram.com/v1/listen?model=nova-2&language=pt-BR" \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: audio/wav" \
  --data-binary @teste-audio.wav
```

**Resultado esperado:** Um JSON com o campo `transcript` contendo o texto do áudio.

**Sem arquivo de áudio para testar?** Basta verificar a autenticação:

```bash
curl -X GET "https://api.deepgram.com/v1/projects" \
  -H "Authorization: Token $DEEPGRAM_API_KEY"
```

**Resultado esperado:** Um JSON listando seus projetos (confirma que a key é válida).

### Planos

| Plano | Horas/mês | Custo |
|-------|-----------|-------|
| Pay as you go | 45h grátis | $200 em créditos iniciais |
| Growth | Ilimitado | $4.25/1000 min (Nova-2) |

Os créditos iniciais são mais do que suficientes para uso pessoal.

---

## 4. Google Drive - OPCIONAL

### O que faz

Permite importar documentos diretamente do Google Drive para o inbox do Mega Brain. Útil se você armazena PDFs, transcrições ou documentos de curso no Drive.

### Onde obter

**URL:** [https://console.cloud.google.com/](https://console.cloud.google.com/)

### Passo a passo

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/)
2. Crie um novo projeto (ou selecione existente):
   - Clique em **Select a project** > **New Project**
   - Nome: `mega-brain`
   - Clique em **Create**
3. Ative a API do Google Drive:
   - No menu lateral, vá em **APIs & Services** > **Library**
   - Busque por **Google Drive API**
   - Clique em **Enable**
4. Crie credenciais:
   - Vá em **APIs & Services** > **Credentials**
   - Clique em **Create Credentials** > **OAuth client ID**
   - Em tipo, selecione **Desktop app**
   - Nome: `mega-brain-drive`
   - Clique em **Create**
5. Baixe o arquivo JSON de credenciais:
   - Clique no ícone de download ao lado da credencial criada
   - Salve como `credentials.json`
6. Configure a tela de consentimento (se solicitado):
   - Vá em **OAuth consent screen**
   - Tipo: **External**
   - Preencha nome do app: `Mega Brain`
   - Adicione seu email como usuário de teste
   - Salve

### Como configurar

```bash
# Copie o arquivo de credenciais para o Mega Brain
cp credentials.json /caminho/para/mega-brain/system/credentials.json

# No arquivo .env do Mega Brain
GOOGLE_DRIVE_CREDENTIALS=system/credentials.json
```

### Como testar

```bash
# No Mega Brain, execute:
/ingest gdrive://pasta-id/nome-do-arquivo.pdf
```

**Resultado esperado:** O arquivo é baixado do Drive e salvo no inbox para processamento.

### Observações

- O Google Drive API é **gratuito** para uso pessoal
- Na primeira execução, será solicitado que você autorize o acesso no navegador
- O token de acesso é salvo localmente e renovado automaticamente

---

## 5. Voyage AI - OPCIONAL

### O que faz

Fornece embeddings de alta qualidade para busca semântica (RAG). Quando ativado, você pode buscar informações na base de conhecimento por significado, não apenas por palavras-chave.

### Onde obter

**URL:** [https://dash.voyageai.com/](https://dash.voyageai.com/)

### Passo a passo

1. Acesse [dash.voyageai.com](https://dash.voyageai.com/)
2. Clique em **Sign Up** (aceita login com Google/GitHub)
3. Confirme seu email
4. No painel, vá em **API Keys**
5. Clique em **Create new API key**
6. Nome: `mega-brain`
7. Copie a chave gerada (começa com `pa-...`)

### Como configurar

```bash
# No arquivo .env do Mega Brain
VOYAGE_API_KEY=pa-sua-chave-aqui
```

### Como testar

```bash
curl -X POST "https://api.voyageai.com/v1/embeddings" \
  -H "Authorization: Bearer $VOYAGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":["teste de embedding"],"model":"voyage-2"}'
```

**Resultado esperado:** Um JSON contendo um array `data` com o vetor de embedding (lista de números decimais).

### Planos

| Plano | Tokens/mês | Custo |
|-------|------------|-------|
| Free | 50M tokens | Gratuito |
| Pro | 300M tokens | $0.10/1M tokens |

O plano gratuito cobre amplamente o uso normal do Mega Brain.

---

## Arquivo .env Completo

Após obter todas as chaves desejadas, seu arquivo `.env` deve ficar assim:

```bash
# === OBRIGATORIA ===
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# === OPCIONAIS ===
# JARVIS Voice (Text-to-Speech)
ELEVENLABS_API_KEY=sk_sua-chave-aqui

# JARVIS Voice (Speech-to-Text)
DEEPGRAM_API_KEY=sua-chave-aqui

# Google Drive (importação de documentos)
GOOGLE_DRIVE_CREDENTIALS=system/credentials.json

# Busca Semântica (RAG)
VOYAGE_API_KEY=pa-sua-chave-aqui
```

**Localização:** O arquivo `.env` fica na raiz do projeto Mega Brain.

**Segurança:** Nunca compartilhe suas API keys. O arquivo `.env` já está incluído no `.gitignore` por padrão.

---

## Verificação Geral

Após configurar suas chaves, execute o comando de diagnóstico:

```
/setup --check
```

**Saída esperada:**

```
JARVIS: Verificação de API Keys

  Anthropic (Claude) ......... OK
  ElevenLabs ................. OK (ou "Não configurada")
  Deepgram ................... OK (ou "Não configurada")
  Google Drive ............... OK (ou "Não configurada")
  Voyage AI .................. OK (ou "Não configurada")

  Funcionalidades ativas:
    Processamento ............ OK
    Agentes .................. OK
    Conclave ................. OK
    JARVIS Voice (TTS) ....... OK (ou "Desativado")
    JARVIS Voice (STT) ....... OK (ou "Desativado")
    Importação Drive ......... OK (ou "Desativado")
    Busca Semântica (RAG) .... OK (ou "Desativado")
```

---

## Dúvidas Frequentes

**P: Posso usar o sistema apenas com a Anthropic API key?**
R: Sim. Todas as funcionalidades principais (processamento, agentes, Conclave, DNA extraction) funcionam apenas com a chave da Anthropic.

**P: As chaves opcionais cobram se eu não usar?**
R: Não. Todas as APIs opcionais listadas possuem planos gratuitos generosos. Você só é cobrado se ultrapassar os limites do plano free.

**P: Posso trocar de chave depois?**
R: Sim. Basta atualizar o valor no arquivo `.env` e reiniciar a sessão do Claude Code.

**P: Minha chave parou de funcionar. O que faço?**
R: Verifique se: (1) a chave não expirou, (2) há créditos/saldo na conta, (3) a chave foi copiada corretamente sem espaços extras. Em caso de dúvida, gere uma nova chave.

---

*Mega Brain v1.0.0 - MoneyClub Edition*
