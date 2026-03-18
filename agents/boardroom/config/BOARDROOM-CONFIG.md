# ⚙️ BOARDROOM WARFARE - CONFIGURAÇÃO CENTRAL
## Sistema de Debates Auditivos do Mega Brain

---

## PROPÓSITO

Transformar decisões, análises e playbooks em **episódios de áudio imersivos** onde o ouvinte observa debates reais entre agentes, cada um com sua personalidade, DNA e fontes específicas.

**Princípio fundamental:** ZERO FICÇÃO. Tudo que é dito vem do DNA, das fontes processadas, ou é claramente marcado como síntese do sistema.

---

## CONFIGURAÇÃO GERAL

```yaml
boardroom_config:
  version: "1.0"

  # Identificação
  system_name: "Boardroom Warfare"
  tagline: "Debates Executivos Sem Filtro"

  # Comportamento
  fiction_allowed: false          # NUNCA inventar informação
  source_citation: "always"       # Sempre citar fontes
  personality_expression: "full"  # DNA completo dos personagens
  interruptions_allowed: true     # Interrupções naturais

  # Estrutura de episódio
  episode:
    min_duration: 15              # minutos
    max_duration: 35              # minutos
    default_duration: 25          # minutos

  # Fases obrigatórias
  mandatory_phases:
    - opening                     # Contextualização
    - dna_consultation           # Consulta à constituição
    - agent_debate               # Debate entre experts
    - position_analysis          # Análise dos cargos
    - council_deliberation       # Avaliação do Council
    - resolution                 # Síntese final
    - audience_question          # Pergunta ao ouvinte

  # Pós-produção
  post_episode:
    ask_narration: true          # Perguntar se quer gerar áudio
    auto_save_script: true       # Salvar script automaticamente
    output_path: "agents/boardroom/outputs/"
```

---

## REGRAS DO DEBATE

### Princípios Invioláveis

1. **FIDELIDADE AO DNA**
   - Cada personagem só fala o que seu DNA permite
   - Se não há informação, ele diz "não tenho dados sobre isso"
   - Gírias e padrões de fala são respeitados

2. **CITAÇÃO OBRIGATÓRIA**
   - Toda afirmação factual deve ter fonte
   - Citador anuncia referência após claims importantes
   - Formato: "Referência: [Fonte], [Local específico]"

3. **PROGRESSÃO DE DEBATE**
   ```
   DNA/Constituição → Agents of Person → Agents of Position → Council
   ```
   - Nunca pular etapas
   - Council só entra após debate dos agentes
   - Pode haver ciclos de volta se Council pedir

4. **CONFLITOS SÃO BEM-VINDOS**
   - Discordâncias são expostas, não escondidas
   - Interrupções acontecem naturalmente
   - Tensão é produtiva

5. **PERGUNTA FINAL OBRIGATÓRIA**
   - Todo episódio termina com pergunta ao ouvinte
   - A pergunta deve provocar reflexão/ação
   - Formato: "E você, [pergunta específica]?"

---

## MAPEAMENTO DE PERSONAGENS

### Sempre Presentes
| Personagem | Função | Quando Fala |
|------------|--------|-------------|
| NARRADOR | Conduz e contextualiza | Transições, explicações |
| CITADOR | Referencia fontes | Após claims factuais |

### Convocados por Tema
| Tema | Agents of Person | Agents of Position |
|------|------------------|-------------------|
| Vendas | HORMOZI, COLE | CRO, SALES-MANAGER |
| Marketing | BRUNSON, HORMOZI | CMO, CRO |
| Escala | HORMOZI, COLE | CRO, COO, CFO |

### Council (Sempre os 3)
| Membro | Função |
|--------|--------|
| METHODOLOGICAL-CRITIC | Questiona método e premissas |
| DEVILS-ADVOCATE | Ataca posição dominante |
| SYNTHESIZER | Busca convergência |

---

## TRIGGERS DE CONVOCAÇÃO

```yaml
convocation_triggers:
  # Por palavra-chave no tema
  keywords:
    "comissão|salário|compensação": ["COLE", "HORMOZI", "CRO", "CFO"]
    "funil|conversão|landing": ["BRUNSON", "HORMOZI", "CMO"]
    "oferta|preço|valor": ["HORMOZI", "BRUNSON", "CRO", "CFO"]

  # Mínimo de participantes por fase
  minimums:
    agent_debate: 2               # Mínimo 2 Agents of Person
    position_analysis: 2          # Mínimo 2 Agents of Position
    council: 3                    # Sempre os 3 membros
```

---

## FLUXO DE PRODUÇÃO

```
1. TRIGGER
   └── Tema/decisão identificada (manual ou pós-pipeline)

2. CONVOCAÇÃO
   └── Sistema identifica participantes necessários

3. SCRIPT GENERATION
   └── Gera debate seguindo template e DNA

4. REVIEW (opcional)
   └── Usuário pode revisar/ajustar script

5. NARRATION PROMPT
   └── "Deseja iniciar narração do debate? [SIM/NÃO]"

6. TTS GENERATION (se SIM)
   └── Gera áudio via ElevenLabs

7. SAVE & REFERENCE
   └── Salva em /outputs/AUDIO/ + gera link
```

---

## INTEGRAÇÃO COM PIPELINE JARVIS

```yaml
pipeline_integration:
  # Quando ativar Boardroom automaticamente
  auto_trigger:
    on_playbook_complete: true
    on_dossier_update: false      # Só manual
    on_council_decision: true
    on_synthesis_complete: true

  # Hook pós-processamento
  post_processing_hook:
    enabled: true
    prompt: |
      ════════════════════════════════════════════
      📋 PROCESSAMENTO CONCLUÍDO

      Novo conteúdo disponível para debate:
      • [LISTA DE OUTPUTS]

      🎬 Deseja gerar episódio BOARDROOM WARFARE?

      [1] SIM - Gerar debate sobre este conteúdo
      [2] NÃO - Apenas salvar outputs
      [3] SELECIONAR - Escolher tópicos específicos
      ════════════════════════════════════════════
```
