# /setup - First-Time Configuration Wizard

Guia o usuário na configuração inicial do Mega Brain após instalação.

## Instruções

Execute os seguintes passos em sequência, mostrando progresso ao usuário:

### STEP 1: Verificar Python
```bash
python --version 2>&1 || python3 --version 2>&1
```
- Se Python 3.10+ encontrado: mostrar versão com checkmark
- Se não encontrado: informar "Python 3.10+ necessário. Instale em https://python.org" e parar

### STEP 2: Verificar Node.js
```bash
node --version
```
- Se Node.js 18+ encontrado: mostrar versão com checkmark
- Se não encontrado: informar "Node.js 18+ necessário. Instale em https://nodejs.org" e parar

### STEP 3: Instalar Dependências Python
Verificar se existe `requirements.txt` na raiz. Se existir:
```bash
pip install -r requirements.txt
```
Se falhar, tentar:
```bash
pip install --user -r requirements.txt
```
Se o arquivo não existir, pular este passo informando que será configurado depois.

### STEP 4: Configurar API Keys

Para cada chave abaixo, explicar o serviço e pedir a chave ao usuário.
Usar a ferramenta AskUserQuestion para cada grupo.

**OBRIGATÓRIA:**
1. **OPENAI_API_KEY** - "A API da OpenAI fornece o Whisper para transcrição automática de vídeos do YouTube e áudios. Essencial para o /ingest funcionar com vídeos. Obtenha em: https://platform.openai.com/api-keys"

**RECOMENDADA:**
2. **VOYAGE_API_KEY** - "Voyage AI fornece busca semântica avançada. Permite que o Conclave e agentes encontrem evidências nos materiais inseridos. Obtenha em: https://dash.voyageai.com/api-keys"

**OPCIONAIS (usuário pode pular):**
3. **ANTHROPIC_API_KEY** - "Não necessária se você usa o Claude Code via assinatura Max ou Pro (o acesso ao Claude já está incluído). Apenas necessária se você pretende rodar scripts autônomos fora do Claude Code. Obtenha em: https://console.anthropic.com/settings/keys"
4. **GOOGLE_CLIENT_ID** + **GOOGLE_CLIENT_SECRET** - "Para importar conteúdos diretamente do Google Drive (PDFs, documentos, planilhas). Configure em: https://console.cloud.google.com/apis/credentials"

### STEP 5: Validar Configuração

Para cada chave fornecida, testar a conexão:
- **OpenAI**: Verificar endpoint /models (listar modelos disponíveis)
- **Voyage AI**: Verificar endpoint /embeddings (teste de embedding)
- **Anthropic**: Fazer uma chamada simples de teste (se fornecida)
- **Google Drive**: Verificar OAuth token (se credenciais fornecidas)
- Para chaves opcionais puladas: mostrar "⏭️ Pulado" ao invés de testar

Mostrar resumo:
```
═══════════════════════════════════════════════════════════════
 🔌 VALIDAÇÃO DE CONEXÕES
═══════════════════════════════════════════════════════════════

  OpenAI (Whisper):  [resultado]
  Voyage AI (RAG):   [resultado ou "⏭️ Pulado"]
  Anthropic API:     [resultado ou "⏭️ Pulado"]
  Google Drive:      [resultado ou "⏭️ Pulado"]
```

### STEP 6: Gerar .env

Criar arquivo `.env` na raiz do projeto com todas as chaves configuradas.
Usar o template de `bin/templates/env.example` como base, preenchendo os valores fornecidos.

```bash
# Verificar se .env já existe
test -f .env && echo "EXISTE" || echo "NAO EXISTE"
```

Se já existir, perguntar se deseja sobrescrever.

### STEP 7: Exibir Onboarding

Após completar a configuração, exibir o dashboard de status no formato do JARVIS Operational Briefing:

1. Exibir ASCII JARVIS banner
2. Status do sistema (tabela com progress bars — tudo zerado para instalação nova)
3. Capacidades: Clonagem Mental, Agentes de Cargo, Conclave (com fases completas)
4. Checklists de conteúdo: Especialistas + Negócio
5. Primeiro uso do Conclave
6. Frase de fechamento JARVIS

Usar o conteúdo da função `showOnboarding()` de `bin/lib/ascii-art.js` como referência visual, mas formatar diretamente no output como texto Markdown para melhor visualização no Claude Code.

### Comportamento de Erro

- Se qualquer step OBRIGATÓRIO falhar, parar e informar claramente o que fazer
- Se steps OPCIONAIS falharem, continuar e informar que pode ser configurado depois
- Se o usuário cancelar, salvar progresso parcial no .env com as chaves já configuradas
