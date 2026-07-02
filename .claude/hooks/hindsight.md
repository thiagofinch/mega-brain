# Hindsight — Layer 4: Behavioral Pattern Extraction

> Padrões comportamentais extraídos de sessões anteriores.
> Claude lê isso e AJUSTA comportamento, não apenas lembra fatos.
> Atualizado ao final de cada sessão significativa.

## Last Updated: 2026-04-05

---

## Padrões de Execução (O QUE FUNCIONA)

### P1: Briefing → Consolidar .md → Roundtable → PM → SM/PO → Dev YOLO
Fluxo validado na sessão 2026-04-04/05. Investigação livre → consolida em .md → roundtable valida → PM cria epic → SM cria stories → PO valida → Dev executa em YOLO. NÃO pular etapas.

### P2: Progress log ASCII após cada story
Mostrar barra de progresso com TODAS as stories do epic após completar cada uma. Nunca parecer que o trabalho está completo quando faltam stories.

### P3: Agentes @dev precisam de path EXPLÍCITO
Agentes spawned não conhecem o contexto da sessão. Se o path não for explícito no prompt, escrevem em diretórios errados (ex: "services 2/" ao invés de "services/"). SEMPRE incluir paths absolutos nos prompts de agentes.

### P4: git add seletivo, NUNCA git add .
Usar `git add {arquivos específicos}` sempre. `git add services/` pode capturar deletions inesperadas se o working tree divergiu do index.

### P5: Verificar diff --cached antes de commit
Após git add, SEMPRE rodar `git diff --cached --name-status | grep "^D"` para confirmar que não há deletions inesperadas.

---

## Anti-Padrões (O QUE NÃO FUNCIONA)

### A1: Oferecer opções A/B/C
o fundador quer uma ação — a mais óbvia, ordenada, que fecha o trabalho atual. Não perguntar "prefere X ou Y?".

### A2: Perguntar "quer pausar?" após 1 story de 5
Implica que o trabalho está feito. Declarar o que falta ANTES de qualquer sugestão de pausa.

### A3: Delegar a agentes sem path absoluto
Agentes criam em paths errados. Incluir CRITICAL PATH WARNING no prompt.

### A4: git add amplo após trabalho de agentes
Agentes podem ter deletado/movido arquivos. Verificar working tree antes de staging.

### A5: Apresentar status parcial como progresso completo
20% feito não é "done". Sempre mostrar X de Y com o que resta.

---

## Preferências de Interação (extraídas de correções)

- **Comunicação:** Direto, sem opções, sem enrolação. 1 ação por vez.
- **Formato:** Tabelas para status, ASCII box para progress, prosa curta para decisões.
- **Erros:** Reconhecer objetivo, corrigir, seguir. Sem auto-flagelação.
- **Agents:** Sempre com paths absolutos, CRITICAL PATH WARNING, verificação pós-execução.
- **Git:** Seletivo, verificado, sem surpresas.
- **Sessões:** PRIMER.md + memory.sh garantem continuidade. Nunca começar do zero.
