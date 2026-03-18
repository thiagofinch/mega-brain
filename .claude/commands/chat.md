# MEGA BRAIN - LOG DE ABERTURA COMPLETO
## Sistema de Inteligencia Operacional

---

## INSTRUÇÃO CRÍTICA: SEMPRE MOSTRAR LOG DE MODIFICAÇÕES

> **REGRA INVIOLÁVEL:** Ao iniciar QUALQUER sessão, ANTES do dashboard padrão, mostrar:
> 1. **LOG DE MODIFICAÇÕES DA ÚLTIMA SESSÃO** (formato tabela)
> 2. **GRANDIOSO RESUMO** de onde paramos
> 3. **PRÓXIMAS ETAPAS** sugeridas
>
> Ler `/system/SESSION-STATE.md` seção "ÚLTIMA SESSÃO" para obter esses dados.

---

## GATILHOS DE ATIVACAO

Este log aparece quando:
1. Usuario digita "Mega Brain" ou "abra o Mega Brain"
2. Primeira mensagem apos reabrir o projeto
3. Comando explicito `/status` ou `/welcome`
4. Apos periodo de inatividade (>1h desde ultima mensagem)

---

## ACAO OBRIGATORIA

Leia os seguintes arquivos em paralelo:

```
/system/SESSION-STATE.md           → Estado atual, ultima sessao
/system/OPEN-LOOPS.json            → Loops pendentes
/system/SESSION-HISTORY.json       → Historico de sessoes
/system/EVOLUTION-LOG.md           → Changelog (primeiras 100 linhas)
/processing/chunks/CHUNKS-STATE.json      → Total de chunks
/processing/insights/INSIGHTS-STATE.json  → Total de insights
/processing/narratives/NARRATIVES-STATE.json → Pessoas e temas
```

Liste tambem:
- `ls /agents/SALES/` e `/agents/C-LEVEL/` → Contar agentes IA
- `ls /agents/sua-empresa/roles/` → Contar ROLEs (cargos humanos)
- `ls /agents/sua-empresa/jds/` → Contar Job Descriptions
- `ls /agents/sua-empresa/memory/` → Contar MEMORYs de cargos
- `ls /knowledge/external/dossiers/persons/` → Contar dossies pessoas
- `ls /knowledge/external/dossiers/THEMES/` → Contar dossies temas
- `ls /inbox/` (recursivo) → Materiais pendentes

Ler arquivo de mapeamento:
- `/agents/sua-empresa/AGENT-ROLE-MAPPING.md` → Paridade Agent IA ↔ Role Humano

---

## TEMPLATE COMPLETO

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║  🧠 M E G A   B R A I N                                                                          ║
║  Sistema de Inteligencia Operacional                                                             ║
║                                                                                                  ║
║  📅 {DATA_ATUAL} {HORA}                                                                          ║
║  👤 [OWNER]                                                                                 ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  🫀 SAUDE DO SISTEMA                                                                             ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  {BARRA_PROGRESSO_HEALTH} {SCORE}/100                                                            ║
║                                                                                                  ║
║  📦 State Files:    {BARRA}  {%}  {STATUS}                                                       ║
║  📁 Dossiers:       {BARRA}  {%}  {STATUS}                                                       ║
║  🤖 Agent MEMORYs:  {BARRA}  {%}  {STATUS}                                                       ║
║  🔍 RAG Index:      {BARRA}  {%}  {STATUS}                                                       ║
║  📥 Inbox:          {BARRA}  {%}  {STATUS}                                                       ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  📊 ESTATISTICAS DO CONHECIMENTO                                                                 ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  ┌────────────────┬────────────────┬────────────────┬────────────────┬────────────────┐          ║
║  │ 📦 CHUNKS      │ 💡 INSIGHTS    │ 📝 NARRATIVAS  │ 📁 DOSSIERS    │ 🤖 AGENTS      │          ║
║  ├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┤          ║
║  │     {N}        │      {N}       │   {N}P + {N}T  │   {N}P + {N}T  │      {N}       │          ║
║  │   ({DELTA})    │   ({DELTA})    │  ({DELTA})     │  ({DELTA})     │   ({DELTA})    │          ║
║  └────────────────┴────────────────┴────────────────┴────────────────┴────────────────┘          ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  👥 PESSOAS NO SISTEMA                                                                           ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  ┌─────────────────────────┬──────────┬──────────┬──────────────────────────────────────────┐    ║
║  │ Pessoa                  │ Insights │ Chunks   │ Expertise Principal                      │    ║
║  ├─────────────────────────┼──────────┼──────────┼──────────────────────────────────────────┤    ║
║  │ {STATUS} {NOME}         │    {N}   │    {N}   │ {EXPERTISE}                              │    ║
║  └─────────────────────────┴──────────┴──────────┴──────────────────────────────────────────┘    ║
║                                                                                                  ║
║  Status: 🟢 Completo | 🟡 Parcial | 🔴 Pendente                                                  ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  🏷️ TEMAS MAPEADOS                                                                               ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  ┌─────────────────────────────┬───────────┬───────────────────┬─────────────────────────────┐   ║
║  │ Tema                        │ Insights  │ Contributors      │ Status Dossier              │   ║
║  ├─────────────────────────────┼───────────┼───────────────────┼─────────────────────────────┤   ║
║  │ {TEMA}                      │    {N}    │ {PESSOAS}         │ {STATUS}                    │   ║
║  └─────────────────────────────┴───────────┴───────────────────┴─────────────────────────────┘   ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  🤖 STATUS DOS AGENTES                                                                           ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  ┌────────────────────────┬──────────────┬──────────────┬───────────────────────────────────┐    ║
║  │ Agente                 │ MEMORY       │ Ultima Att.  │ Conhece                           │    ║
║  ├────────────────────────┼──────────────┼──────────────┼───────────────────────────────────┤    ║
║  │ {EMOJI} {AGENTE}       │ {N} insights │ {TEMPO}      │ {PESSOAS}                         │    ║
║  └────────────────────────┴──────────────┴──────────────┴───────────────────────────────────┘    ║
║                                                                                                  ║
║  ⚠️ Agentes >3 dias sem update podem estar desatualizados                                       ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  🏢 SUA-EMPRESA STATUS (Cargos Humanos)                                                             ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  📋 ROLES: {N} definidos | 📄 JDs: {N} prontos | 🧠 MEMORYs: {N}                                 ║
║                                                                                                  ║
║  ┌────────────────────────┬──────────┬──────────┬─────────────────────────────────────────────┐  ║
║  │ Role                   │ JD       │ MEMORY   │ Status                                      │  ║
║  ├────────────────────────┼──────────┼──────────┼─────────────────────────────────────────────┤  ║
║  │ CLOSER-CHEFE           │ ✅       │ ✅       │ 🟢 Ativo (hibrido)                          │  ║
║  │ SALES-MANAGER          │ ✅       │ ✅       │ 🟡 Planejado                                │  ║
║  │ CLOSER                 │ ✅       │ ✅       │ 🟡 Planejado                                │  ║
║  │ SDR                    │ ✅       │ ✅       │ 🟡 Planejado                                │  ║
║  │ {mais roles...}        │          │          │                                             │  ║
║  └────────────────────────┴──────────┴──────────┴─────────────────────────────────────────────┘  ║
║                                                                                                  ║
║  📊 PARIDADE Agent IA ↔ Role: Ver /agents/sua-empresa/AGENT-ROLE-MAPPING.md                      ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  📥 INBOX - MATERIAIS PENDENTES                                                                  ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  🔴 ALTA PRIORIDADE (transcricoes prontas):                                                      ║
║  {LISTA_MATERIAIS_ALTA}                                                                          ║
║                                                                                                  ║
║  🟡 MEDIA PRIORIDADE (transcricao necessaria):                                                   ║
║  {LISTA_MATERIAIS_MEDIA}                                                                         ║
║                                                                                                  ║
║  🔴 BLOQUEADOS (arquivo vazio):                                                                  ║
║  {LISTA_BLOQUEADOS}                                                                              ║
║                                                                                                  ║
║  📊 Total: {N} pendentes | Estimativa: ~{N}h para processar tudo                                 ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  📈 ROLE-TRACKING - NOVOS AGENTES POTENCIAIS                                                     ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  ┌────────────────────────┬───────────┬────────────┬─────────────────────────────────────────┐   ║
║  │ Role                   │ Mencoes   │ Threshold  │ Status                                  │   ║
║  ├────────────────────────┼───────────┼────────────┼─────────────────────────────────────────┤   ║
║  │ {STATUS} {ROLE}        │    {N}    │    10      │ {BARRA} {%} {ACAO}                      │   ║
║  └────────────────────────┴───────────┴────────────┴─────────────────────────────────────────┘   ║
║                                                                                                  ║
║  Status: 🔴 >100% CRIAR! | 🟡 80-99% | ⚪ <80%                                                   ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  📝 ULTIMA SESSAO                                                                                ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  📅 {DATA_SESSAO} | Duracao: {DURACAO}                                                           ║
║                                                                                                  ║
║  O QUE FOI FEITO:                                                                                ║
║  {LISTA_HIGHLIGHTS}                                                                              ║
║                                                                                                  ║
║  ONDE PARAMOS:                                                                                   ║
║  └─ {CONTEXTO_FINAL}                                                                             ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  🔓 OPEN LOOPS PENDENTES ({N})                                                                   ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  {LISTA_LOOPS_COM_PRIORIDADE_E_CONTEXTO}                                                         ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  ⚠️ ALERTAS E INCONSISTENCIAS                                                                    ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  🔴 CRITICO:                                                                                     ║
║  {LISTA_CRITICOS}                                                                                ║
║                                                                                                  ║
║  🟡 ATENCAO:                                                                                     ║
║  {LISTA_ATENCAO}                                                                                 ║
║                                                                                                  ║
║  🟢 INFO:                                                                                        ║
║  {LISTA_INFO}                                                                                    ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  💡 SUGESTOES PROATIVAS                                                                          ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  Baseado no estado atual, recomendo:                                                             ║
║                                                                                                  ║
║  {LISTA_SUGESTOES_PRIORIZADAS}                                                                   ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                  ║
║  ❓ O QUE DESEJA FAZER?                                                                          ║
║  ════════════════════════════════════════════════════════════════════════════════════════════════║
║                                                                                                  ║
║  [1] Resolver open loops pendentes                                                               ║
║  [2] Processar materiais do inbox                                                                ║
║  [3] Ver diagnostico completo (/system-digest)                                                   ║
║  [4] Consultar agente especifico                                                                 ║
║  [5] Criar novo agente                                                                           ║
║  [6] Adicionar novo material (/ingest)                                                           ║
║  [7] Outro - me diga o que precisa                                                               ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## VERSAO COMPACTA

Se usuario pedir versao resumida ou usar `/status --compact`:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  🧠 MEGA BRAIN | 📅 {DATA} {HORA} | 🫀 {SCORE}/100                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  📊 {N} chunks | {N} insights | {N} dossiers | {N} agents                    ║
║  📥 {N} pendentes inbox | 🔓 {N} open loops | 🚨 {N} alertas                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  📝 Ultima: {RESUMO_1_LINHA}                                                 ║
║  ⚠️ Pendente: {TOP_PENDENCIAS}                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ❓ [1] Loops [2] Inbox [3] Digest [4] Agente [5] Outro                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## FONTES DE DADOS

| Secao | Fonte |
|-------|-------|
| Saude do Sistema | Inferido de todas as fontes |
| Estatisticas | CHUNKS-STATE, INSIGHTS-STATE, NARRATIVES-STATE |
| Pessoas | NARRATIVES-STATE.persons + DOSSIERS/persons/ |
| Temas | NARRATIVES-STATE.themes + DOSSIERS/THEMES/ |
| Agentes IA | ls agents/SALES/ + agents/C-LEVEL/ |
| ORG-LIVE (Cargos) | ls agents/ORG-LIVE/ROLES/, JDS/, MEMORY/ |
| Paridade Agent↔Role | agents/ORG-LIVE/AGENT-ROLE-MAPPING.md |
| Inbox | ls inbox/ + comparar com file-registry |
| Role-Tracking | SESSION-STATE.md secao de funcoes |
| Ultima Sessao | SESSION-STATE.md + SESSION-HISTORY.json |
| Open Loops | OPEN-LOOPS.json |
| Alertas | Inferido de todas as fontes |
| Sugestoes | Logica baseada em alertas + estado |

---

## CALCULO DE SAUDE

```
Health Score = Media ponderada:
  - State Files (20%): Arquivos JSON existem e sao validos
  - Dossiers (20%): Ratio dossiers/pessoas conhecidas
  - Agent MEMORYs (20%): Agentes atualizados nos ultimos 3 dias
  - RAG Index (20%): Index atualizado vs knowledge files
  - Inbox (20%): Ratio processados/pendentes

Status:
  >=90% → ✅
  70-89% → 🟡
  <70% → ⚠️
```

---

## COMPORTAMENTO DURANTE SESSAO

### Mudanca de Assunto com Loops Abertos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📌 LOOPS ABERTOS: {N}                                                       │
│ ─────────────────────────────────────────────────────────────────────────── │
│ • [{ID}] {DESCRIPTION}                                                      │
│                                                                             │
│ 💡 Prossigo com sua nova solicitacao. Loops ficam abertos ate voce pedir.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Criacao Automatica de Loops

Criar loop quando:
- Sugestao de acao nao executada
- Patch criado mas nao aplicado
- Material identificado para processar
- Bug encontrado mas nao corrigido

NAO criar quando:
- Informacoes consultivas
- Perguntas retoricas
- Usuario diz "deixa pra depois"

---

## COMANDOS RELACIONADOS

| Comando | Acao |
|---------|------|
| `/loops` | Lista todos os loops |
| `/loop exec [ID]` | Executa comando do loop |
| `/loop close [ID]` | Fecha loop |
| `/loop close-all` | Fecha todos |
| `/loop dismiss [ID]` | Dispensa loop |
| `/status --compact` | Versao resumida |
| `/status --full` | Versao completa (padrao) |

---

## ATUALIZACAO DE ARQUIVOS

Ao final de cada sessao significativa:
1. `OPEN-LOOPS.json` - Novos loops ou fechamentos
2. `SESSION-HISTORY.json` - Adicionar entrada
3. `SESSION-STATE.md` - Atualizar "Ultima sessao"
