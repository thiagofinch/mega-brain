# Workflow: Auto-Discovery
## Descoberta Automática e Sincronização de Squads

---

## Visao Geral

### Proposito
Garantir que o SQUAD-REGISTRY esteja sempre sincronizado com os squads existentes em disco, detectando automaticamente novos squads, remoções e modificações sem depender exclusivamente de notificações.

### Problema que Resolve
**GAP CRITICO:** O sistema depende de notificações do squad-creator para indexar novos squads, mas se a notificação falhar ou squads forem criados manualmente, o orquestrador não terá conhecimento deles, resultando em:
- Squads "invisíveis" ao roteador
- Capacidades não utilizadas
- Inconsistências no registry

### Estrategia
Implementar um mecanismo de descoberta proativa que:
1. Executa periodicamente (diario)
2. Responde a eventos de startup
3. Pode ser invocado manualmente
4. Compara estado em disco vs registry

---

## Triggers

```yaml
triggers:
  - tipo: "startup"
    descricao: "Quando o sistema inicializa"
    modo: "scan_completo"
    prioridade: "P0"

  - tipo: "periodico"
    descricao: "Execucao diaria de manutencao"
    cron: "0 0 * * *"  # Meia-noite todos os dias
    modo: "scan_completo"
    prioridade: "P2"

  - tipo: "callback"
    descricao: "Notificacao do squad-creator"
    evento: "squad_criado"
    modo: "adicionar"
    prioridade: "P0"

  - tipo: "callback"
    descricao: "Notificacao de modificacao"
    evento: "squad_modificado"
    modo: "atualizar"
    prioridade: "P1"

  - tipo: "manual"
    descricao: "Solicitacao explicita de re-scan"
    comando: "*sync-squads"
    modo: "scan_completo"
    prioridade: "P0"
```

---

## Diagrama de Fluxo

```
[Trigger]
    |
    v
[Fase 1: Comparar Estado]
    |-- Ler SQUAD-REGISTRY atual
    |-- Escanear squads/
    |-- Calcular diff
    |
    v
[Fase 2: Classificar Mudancas]
    |-- Squads novos (em disco, nao no registry)
    |-- Squads removidos (no registry, nao em disco)
    |-- Squads modificados (hash diferente)
    |
    v
[Fase 3: Processar Mudancas]
    |-- Para novos: indexar completamente
    |-- Para removidos: arquivar entrada
    |-- Para modificados: atualizar entrada
    |
    v
[Fase 4: Validar e Salvar]
    |-- Validar consistencia
    |-- Atualizar SQUAD-REGISTRY
    |-- Gerar relatorio
    |
    v
[Fase 5: Notificar]
    |-- Alertar sobre gaps encontrados
    |-- Reportar estatisticas
    |
    v
[FIM]
```

---

## Fases Detalhadas

### Fase 1: Comparar Estado (5-10s)

**Agente:** indexador-squads
**Objetivo:** Identificar discrepancias entre registry e disco

```yaml
fase_1:
  acoes:
    - nome: "Carregar registry atual"
      input: "knowledge/SQUAD-REGISTRY.md"
      output: "lista_registry: [{id, hash, updated_at}]"

    - nome: "Escanear diretorio de squads"
      input: "squads/"
      output: "lista_disco: [{id, path, mtime}]"

    - nome: "Calcular diff"
      input: "lista_registry + lista_disco"
      output:
        novos: "IDs em disco mas nao no registry"
        removidos: "IDs no registry mas nao em disco"
        potencialmente_modificados: "IDs em ambos"

  validacoes:
    - "Diretorio de squads acessivel"
    - "SQUAD-REGISTRY existe ou inicializar vazio"
```

**Algoritmo de Deteccao:**
```
PARA cada squad_id em disco:
    SE squad_id NAO EXISTE em registry:
        ADICIONAR a lista_novos
    SENAO:
        ADICIONAR a lista_verificar

PARA cada squad_id em registry:
    SE squad_id NAO EXISTE em disco:
        ADICIONAR a lista_removidos

PARA cada squad_id em lista_verificar:
    hash_atual = calcular_hash(squad_path)
    hash_registry = registry[squad_id].hash
    SE hash_atual != hash_registry:
        ADICIONAR a lista_modificados
```

---

### Fase 2: Classificar Mudancas (2-5s)

**Agente:** indexador-squads
**Objetivo:** Determinar acao necessaria para cada squad

```yaml
fase_2:
  classificacao:
    novo:
      condicao: "Squad existe em disco mas nao no registry"
      acao: "Indexar completamente"
      prioridade: "Alta"
      exemplo: "Squad criado manualmente ou notificacao falhou"

    removido:
      condicao: "Squad existe no registry mas nao em disco"
      acao: "Arquivar entrada com flag 'removido'"
      prioridade: "Media"
      exemplo: "Squad deletado do sistema"

    modificado:
      condicao: "Hash diferente ou mtime mais recente"
      acao: "Re-extrair metadados e atualizar"
      prioridade: "Media"
      exemplo: "Agentes adicionados/removidos"

    inalterado:
      condicao: "Hash identico e mtime igual ou anterior"
      acao: "Nenhuma"
      prioridade: "Baixa"

  output:
    sumario:
      novos: 2
      removidos: 0
      modificados: 1
      inalterados: 15
```

---

### Fase 3: Processar Mudancas (10-30s)

**Agente:** indexador-squads
**Objetivo:** Executar acoes de sincronizacao

#### 3.1 Processar Novos Squads

```yaml
processar_novo:
  para_cada_novo_squad:
    - nome: "Ler SQUAD.md"
      arquivo: "{squad_path}/SQUAD.md"
      obrigatorio: true

    - nome: "Extrair metadados"
      campos:
        - id
        - nome
        - dominio
        - proposito
        - problemas_que_resolve
        - prioridade

    - nome: "Listar agentes"
      diretorio: "{squad_path}/agents/"
      para_cada_agente:
        - extrair: "nome, papel, capacidades, tipos_tarefa"

    - nome: "Listar workflows"
      diretorio: "{squad_path}/workflows/"
      para_cada_workflow:
        - extrair: "id, trigger, output"

    - nome: "Gerar keywords"
      fontes:
        - dominio (peso: 3)
        - problemas (peso: 3)
        - nomes_agentes (peso: 2)
        - capacidades (peso: 2)
        - tags (peso: 1)
      max_keywords: 50

    - nome: "Identificar capacidades especiais"
      verificar:
        - "CRIAR_NOVOS_SQUADS": "tem workflow create-squad ou create-agent"
        - "ORQUESTRACAO_CENTRAL": "tem agente roteador ou orquestrador"
        - "AUTO_DISCOVERY": "tem workflow auto-discovery"

    - nome: "Calcular hash"
      inclui: "SQUAD.md + lista de agentes + lista de workflows"

    - nome: "Criar entrada no registry"
```

#### 3.2 Processar Squads Removidos

```yaml
processar_removido:
  para_cada_removido:
    - nome: "Marcar como removido"
      acao: "Adicionar flag 'status: removido'"

    - nome: "Manter historico"
      acao: "Mover para secao 'Squads Arquivados'"

    - nome: "Atualizar indices"
      acao: "Remover de indices por dominio e tipo de tarefa"

    - nome: "Alertar"
      acao: "Gerar alerta de squad removido"
```

#### 3.3 Processar Squads Modificados

```yaml
processar_modificado:
  para_cada_modificado:
    - nome: "Re-extrair metadados"
      igual_a: "processar_novo"

    - nome: "Calcular diff de mudancas"
      comparar:
        - agentes_adicionados
        - agentes_removidos
        - problemas_alterados
        - workflows_alterados

    - nome: "Atualizar entrada"
      acao: "Substituir entrada no registry"

    - nome: "Atualizar hash e timestamp"
```

---

### Fase 4: Validar e Salvar (5s)

**Agente:** indexador-squads
**Objetivo:** Garantir consistencia e persistir

```yaml
fase_4:
  validacoes_pre_save:
    - nome: "IDs unicos"
      verificar: "Nenhum ID duplicado no registry"

    - nome: "Squads validos"
      verificar: "Todos squads tem pelo menos 1 agente"

    - nome: "Keywords nao vazias"
      verificar: "Todos squads tem pelo menos 3 keywords"

    - nome: "Indices consistentes"
      verificar: "Indices por dominio e tipo refletem squads ativos"

  backup:
    - nome: "Backup do registry atual"
      destino: "knowledge/SQUAD-REGISTRY.backup.md"
      quando: "Antes de qualquer alteracao"

  persistencia:
    - nome: "Escrever SQUAD-REGISTRY.md"
      conteudo: "Registry completo atualizado"
      incluir:
        - cabecalho com estatisticas
        - secao de squads ativos
        - indices de capacidades
        - squads arquivados (se houver)
        - timestamp de atualizacao
```

---

### Fase 5: Notificar (2s)

**Agente:** supervisor-sistema
**Objetivo:** Reportar resultados

```yaml
fase_5:
  gerar_relatorio:
    formato: "yaml"
    campos:
      - timestamp
      - trigger
      - duracao
      - mudancas_detectadas
      - squads_novos (lista)
      - squads_removidos (lista)
      - squads_modificados (lista)
      - alertas

  notificacoes:
    - condicao: "squads_novos.length > 0"
      mensagem: "Descobertos {N} novos squads: {lista}"
      prioridade: "Alta"

    - condicao: "squads_removidos.length > 0"
      mensagem: "Detectada remocao de {N} squads: {lista}"
      prioridade: "Alta"

    - condicao: "alertas.length > 0"
      mensagem: "Encontrados {N} alertas durante sync"
      prioridade: "Media"

  metricas:
    registrar:
      - "sync_duration_ms"
      - "squads_processados"
      - "mudancas_detectadas"
      - "erros_encontrados"
```

---

## Protocolo de Callback

### Para squad-creator Notificar Indexador

O squad-creator DEVE notificar o indexador quando criar ou modificar um squad:

```yaml
callback_protocol:
  evento: "squad_criado"
  payload:
    squad_id: "nome-do-novo-squad"
    squad_path: "squads/{squad_id}/"
    timestamp: "ISO-8601"
    origem: "squad-creator"

  como_executar:
    metodo_1: "Chamar task indexar-squad.md com evento='criado'"
    metodo_2: "Executar workflow auto-discovery com modo='adicionar'"

  exemplo_chamada:
    ```yaml
    trigger:
      tipo: "callback"
      evento: "squad_criado"
    input:
      squad_path: "squads/novo-squad"
      evento: "criado"
    executor: "@capability-cartographer"
    task: "indexar-squad"
    ```
```

### Integracao com create-squad.md

Adicionar como PHASE 5.5 no workflow de criacao:

```yaml
phase_5_5_notificar_indexador:
  nome: "Notificar Orquestrador"
  apos: "PHASE 5: VALIDATION"
  antes: "PHASE 6: HANDOFF"
  obrigatorio: true

  acoes:
    - nome: "Preparar payload"
      dados:
        squad_id: "{pack_name}"
        squad_path: "squads/{pack_name}/"
        evento: "criado"
        timestamp: "{now}"
        agentes_criados: "{lista_agentes}"
        dominio: "{domain}"

    - nome: "Executar callback"
      target: "@orquestrador-global/indexador-squads"
      task: "indexar-squad"
      modo: "sincrono"
      timeout: "30s"

    - nome: "Verificar indexacao"
      validar:
        - "Squad aparece no SQUAD-REGISTRY"
        - "Keywords geradas corretamente"
        - "Indices atualizados"

  fallback:
    on_failure:
      - "Log de erro"
      - "Agendar re-tentativa em 5min"
      - "Marcar squad para indexacao pendente"
    max_retries: 3
```

---

## Garantias de Consistencia

### Mecanismos de Seguranca

```yaml
garantias:
  backup_automatico:
    descricao: "Backup antes de qualquer modificacao"
    retencao: "Ultimos 5 backups"

  idempotencia:
    descricao: "Re-executar nao causa duplicatas"
    implementacao: "Usar hash para detectar mudancas reais"

  atomic_writes:
    descricao: "Registry atualizado atomicamente"
    implementacao: "Escrever em temp, depois renomear"

  recovery:
    descricao: "Recuperacao de falhas"
    acoes:
      - "Restaurar backup se escrita falhar"
      - "Re-scan se registry corrompido"
      - "Alertar humano se falha persistente"
```

### Resolucao de Conflitos

```yaml
conflitos:
  squad_duplicado:
    cenario: "Dois squads com mesmo ID"
    resolucao: "Manter primeiro, alertar sobre segundo"

  registry_corrompido:
    cenario: "Arquivo SQUAD-REGISTRY invalido"
    resolucao: "Restaurar backup ou re-scan completo"

  notificacao_fora_de_ordem:
    cenario: "Callback chega antes de squad estar pronto"
    resolucao: "Retry com backoff exponencial"
```

---

## Comandos Disponiveis

| Comando | Descricao | Modo |
|---------|-----------|------|
| `*sync-squads` | Executar sincronizacao completa | scan_completo |
| `*index-squad {id}` | Indexar squad especifico | adicionar |
| `*refresh-registry` | Reconstruir registry do zero | scan_completo + force |
| `*validate-registry` | Validar consistencia sem modificar | validacao |

---

## Metricas de Sucesso

| Metrica | Alvo | Descricao |
|---------|------|-----------|
| Cobertura | 100% | Todos squads em disco indexados |
| Latencia de descoberta | < 5min | Tempo para detectar novo squad |
| Tempo de sync | < 60s | Duracao do scan completo |
| Taxa de erro | < 1% | Syncs sem falhas |
| Consistencia | 100% | Registry = disco |

---

## Exemplo de Execucao

### Cenario: Startup do Sistema

**Trigger:**
```yaml
trigger:
  tipo: "startup"
  timestamp: "2026-02-04T08:00:00Z"
```

**Execucao:**

1. **Fase 1 - Comparar:**
   - Registry: 15 squads
   - Disco: 18 squads
   - Diff: 3 novos

2. **Fase 2 - Classificar:**
   ```yaml
   novos: ["youtube-content", "design-system", "media-buy"]
   removidos: []
   modificados: []
   ```

3. **Fase 3 - Processar:**
   - Indexar youtube-content (7 agentes, 32 keywords)
   - Indexar design-system (4 agentes, 28 keywords)
   - Indexar media-buy (5 agentes, 35 keywords)

4. **Fase 4 - Salvar:**
   - Backup criado
   - Registry atualizado (18 squads, 145 agentes)

5. **Fase 5 - Notificar:**
   ```
   [AUTO-DISCOVERY] Sync completo
   - 3 novos squads descobertos
   - 0 squads removidos
   - Registry atualizado
   - Duracao: 23s
   ```

---

## Metadados

| Campo | Valor |
|-------|-------|
| Versao | 1.0.0 |
| Criado em | 2026-02-04 |
| Autor | Mega Brain-Core |
| Squad | orquestrador-global |
| Tipo | Workflow de Manutencao |
| Prioridade | P0 |
| Tags | discovery, sync, registry, squads, indexacao |

## MEGABRAIN Deep Validation

- Last run: `20260514-validate-deep`
- Validator: `mega-brain/megabrain-chief`
- Mode: `deep`
- Workflow ID: `auto-discovery`
- Status: `pass`
- External execution: not performed during structural validation.
