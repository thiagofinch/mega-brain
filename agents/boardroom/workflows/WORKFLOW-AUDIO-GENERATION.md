# WORKFLOW: Geração de Áudio
## Passo a passo para gerar episódios narrados do Boardroom Warfare

---

## Visão Geral do Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW DE GERAÇÃO DE ÁUDIO                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ETAPA 1: PREPARAÇÃO                                                │
│  └─ Verificar pré-requisitos e configurações                        │
│                                                                     │
│  ETAPA 2: SCRIPT                                                    │
│  └─ Criar ou revisar script do episódio                             │
│                                                                     │
│  ETAPA 3: VALIDAÇÃO                                                 │
│  └─ Dry-run para verificar parse                                    │
│                                                                     │
│  ETAPA 4: GERAÇÃO                                                   │
│  └─ Executar audio_generator.py                                     │
│                                                                     │
│  ETAPA 5: REVIEW                                                    │
│  └─ Verificar qualidade do áudio                                    │
│                                                                     │
│  ETAPA 6: FINALIZAÇÃO                                               │
│  └─ Organizar e documentar                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ETAPA 1: Preparação

### 1.1 Verificar Dependências

```bash
# Verificar Python
python --version  # Deve ser 3.8+

# Verificar pacotes
pip list | grep elevenlabs
pip list | grep pydub

# Se não instalados:
pip install elevenlabs pydub
```

### 1.2 Verificar Variáveis de Ambiente

```bash
# Windows (PowerShell)
echo $env:ELEVENLABS_API_KEY

# Windows (CMD)
echo %ELEVENLABS_API_KEY%

# Linux/Mac
echo $ELEVENLABS_API_KEY

# Se não configurada:
# Windows (PowerShell)
$env:ELEVENLABS_API_KEY = "sua_key_aqui"

# Windows (CMD)
set ELEVENLABS_API_KEY=sua_key_aqui

# Linux/Mac
export ELEVENLABS_API_KEY=sua_key_aqui
```

### 1.3 Verificar Mapeamento de Vozes

```bash
# Verificar se voice_mapping.json existe e está configurado
cat agents/boardroom/config/voice_mapping.json
```

**Checklist de Preparação:**

```
[ ] Python 3.8+ instalado
[ ] elevenlabs instalado
[ ] pydub instalado
[ ] ffmpeg instalado (Windows)
[ ] ELEVENLABS_API_KEY configurada
[ ] voice_mapping.json com voice_ids válidos
[ ] Créditos disponíveis na conta ElevenLabs
```

---

## ETAPA 2: Script

### 2.1 Opção A: Usar Script Existente

Se já existe um script em `OUTPUTS/scripts/`:

```bash
# Listar scripts disponíveis
ls agents/boardroom/outputs/scripts/
```

### 2.2 Opção B: Gerar via Pipeline Jarvis

Se processando novo material:

```python
from boardroom.jarvis_boardroom_hook import boardroom_hook

# Ao final do Pipeline Jarvis:
boardroom_hook(pipeline_outputs)
# Seguir prompts interativos
```

### 2.3 Opção C: Criar Script Manual

Usar template de `TEMPLATES/EPISODE-TEMPLATE.md`:

```markdown
# Estrutura básica do script:

[NARRADOR]
(tom descritivo)
"Texto do narrador aqui."

[PERSONAGEM]
(tom específico)
"Fala do personagem."

[SOM: descrição do som]

[PAUSA 2 seg]
```

### 2.4 Verificar Formatação

**Regras de formatação obrigatórias:**

| Elemento | Formato Correto | Formato Incorreto |
|----------|-----------------|-------------------|
| Personagem | `[HORMOZI]` | `[Hormozi]`, `[Alex]` |
| Instrução | `(tom baixo)` | `[tom baixo]` |
| Texto | `"Texto aqui"` | `Texto aqui` |
| Som | `[SOM: descrição]` | `(SOM: descrição)` |
| Pausa | `[PAUSA 2 seg]` | `[PAUSA 2s]` |

---

## ETAPA 3: Validação (Dry-Run)

### 3.1 Executar Parse Sem Gerar Áudio

```bash
cd agents/boardroom

python scripts/audio_generator.py OUTPUTS/scripts/seu_script.md --dry-run
```

### 3.2 Verificar Output

**Output esperado:**

```
🔍 Modo dry-run: apenas parsing

15 segmentos encontrados:

  [NARRADOR] Sala de reuniões. O tema de hoje: comissão...
  [HORMOZI] Pay for performance, not presence...
  [COLE_GORDON] Eu discordo parcialmente...
  ...
```

### 3.3 Corrigir Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| 0 segmentos | Formatação incorreta | Verificar `[PERSONAGEM]` em CAIXA ALTA |
| Segmentos faltando | Regex não capturou | Verificar aspas e quebras de linha |
| Texto truncado | Caracteres especiais | Remover emojis ou caracteres não-ASCII |

---

## ETAPA 4: Geração

### 4.1 Comando de Geração

```bash
cd agents/boardroom

# Geração padrão
python scripts/audio_generator.py OUTPUTS/scripts/seu_script.md

# Com output customizado
python scripts/audio_generator.py OUTPUTS/scripts/seu_script.md --output meu_episodio.mp3
```

### 4.2 Monitorar Progresso

**Output durante geração:**

```
============================================================
🎬 BOARDROOM WARFARE - GERAÇÃO DE ÁUDIO
============================================================

📄 Parsing do script...
   15 segmentos encontrados

🎭 Carregando mapeamento de vozes...
   ✅ API Key configurada

🔊 Gerando segmentos de áudio...
   [1/15] NARRADOR: Sala de reuniões. O tema de hoje...
       ✅ 4523ms
   [2/15] HORMOZI: Pay for performance, not presence...
       ✅ 3891ms
   ...

🔗 Concatenando segmentos...

💾 Exportando para: OUTPUTS/AUDIO/BWE-20241230_143022.mp3

🧹 Limpando arquivos temporários...

============================================================
✅ ÁUDIO GERADO COM SUCESSO
============================================================
   📁 Arquivo: OUTPUTS/AUDIO/BWE-20241230_143022.mp3
   ⏱️  Duração: 8.3 minutos
   🎭 Vozes: 7
============================================================
```

### 4.3 Tratamento de Erros

| Erro | Causa | Solução |
|------|-------|---------|
| `ELEVENLABS_API_KEY não configurada` | Variável não definida | Configurar variável de ambiente |
| `voice_id não configurado` | Personagem sem voz | Adicionar em voice_mapping.json |
| `Rate limit exceeded` | Muitas requisições | Aguardar ou upgrade de plano |
| `Insufficient credits` | Créditos acabaram | Recarregar conta ElevenLabs |

---

## ETAPA 5: Review

### 5.1 Verificar Arquivo Gerado

```bash
# Verificar se arquivo existe
ls -la agents/boardroom/outputs/AUDIO/

# Verificar tamanho (deve ter alguns MB)
# Arquivos muito pequenos indicam problema
```

### 5.2 Ouvir Áudio

```bash
# Windows
start OUTPUTS/AUDIO/episodio.mp3

# Mac
open OUTPUTS/AUDIO/episodio.mp3

# Linux
xdg-open OUTPUTS/AUDIO/episodio.mp3
```

### 5.3 Checklist de Qualidade

```
QUALIDADE DO ÁUDIO:
[ ] Todas as vozes são audíveis
[ ] Transições entre vozes são suaves
[ ] Não há cortes abruptos
[ ] Pausas estão nos lugares corretos
[ ] Duração total é razoável (5-15 min típico)

QUALIDADE DO CONTEÚDO:
[ ] Vozes são distinguíveis entre si
[ ] Tom de cada personagem está correto
[ ] Citações são claras
[ ] Council adiciona valor
[ ] Pergunta final é impactante

QUALIDADE TÉCNICA:
[ ] Sem ruídos ou artefatos
[ ] Volume consistente
[ ] Formato correto (MP3)
[ ] Metadata presente
```

### 5.4 Problemas Comuns

| Problema | Possível Causa | Solução |
|----------|----------------|---------|
| Vozes todas iguais | voice_id repetido | Verificar voice_mapping.json |
| Cortes abruptos | Segmentos muito curtos | Combinar segmentos pequenos |
| Volume inconsistente | Settings diferentes | Normalizar settings de vozes |
| Pronúncia errada | Modelo não ideal | Testar eleven_turbo_v2 |

---

## ETAPA 6: Finalização

### 6.1 Organizar Arquivos

```
agents/boardroom/outputs/
├── scripts/
│   └── BWE-20241230_143022.md    ← Script usado
└── AUDIO/
    └── BWE-20241230_143022.mp3   ← Áudio gerado
```

### 6.2 Limpar Temporários

```bash
# Verificar se temp está limpo
ls agents/boardroom/outputs/temp/

# Se houver arquivos órfãos
rm agents/boardroom/outputs/temp/segment_*.mp3
```

### 6.3 Documentar Episódio

Criar ou atualizar log de episódios:

```markdown
## Episódio: BWE-2024-20241230_143022

- **Tema:** Estrutura de Comissão
- **Data:** 2024-12-30
- **Duração:** 8.3 minutos
- **Participantes:**
  - Persons: HORMOZI, COLE_GORDON
  - Positions: CRO, CFO
  - Council: SYNTHESIZER, METHODOLOGICAL-CRITIC, DEVILS-ADVOCATE
- **Score Final:** 8.2/10
- **Status:** ✅ Aprovado
```

---

## Fluxo Resumido

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLUXO RÁPIDO                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Verificar ambiente                                              │
│     $ echo $ELEVENLABS_API_KEY                                      │
│                                                                     │
│  2. Dry-run                                                         │
│     $ python scripts/audio_generator.py script.md --dry-run         │
│                                                                     │
│  3. Gerar                                                           │
│     $ python scripts/audio_generator.py script.md                   │
│                                                                     │
│  4. Ouvir                                                           │
│     $ start OUTPUTS/AUDIO/episodio.mp3                              │
│                                                                     │
│  5. Aprovar ou iterar                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting Rápido

### Erro: "ElevenLabs não instalado"

```bash
pip install elevenlabs
```

### Erro: "pydub não instalado"

```bash
pip install pydub
# Windows: também instalar ffmpeg
```

### Erro: "ELEVENLABS_API_KEY não configurada"

```bash
# Windows
$env:ELEVENLABS_API_KEY = "sk_..."

# Linux/Mac
export ELEVENLABS_API_KEY=sk_...
```

### Erro: "voice_id não configurado para: AGENT"

Editar `CONFIG/voice_mapping.json` e adicionar o voice_id.

### Erro: "Rate limit exceeded"

Aguardar 1 minuto e tentar novamente, ou fazer upgrade do plano ElevenLabs.

---

## Referências

| Documento | Propósito |
|-----------|-----------|
| [README.md](../README.md) | Visão geral do sistema |
| [INTEGRATION-GUIDE.md](../INTEGRATION-GUIDE.md) | Integração detalhada |
| [CHECKLIST-MASTER.md](../CHECKLIST-MASTER.md) | Checklist completo |
| [voice_mapping.json](../config/voice_mapping.json) | Configuração de vozes |
| [EPISODE-TEMPLATE.md](../templates/EPISODE-TEMPLATE.md) | Template de script |
