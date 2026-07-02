# 🚨 INSTRUÇÃO OBRIGATÓRIA - LEIA ANTES DE QUALQUER AÇÃO

## CONTEXTO

Estou te enviando junto com esta mensagem dois arquivos críticos:

1. **MOGA-BRAIN-PHASE5-TEMPLATES.md** - Templates visuais ASCII para output da Fase 5
2. **INSTRUCAO-IMPLEMENTACAO-TEMPLATES-FASE5.md** - Documentação de como usar

Estes arquivos são **PARTE OFICIAL DO SISTEMA JARVIS** e devem ser tratados com a mesma importância que os templates das Fases 1, 2, 3 e 4 que já existem no projeto.

---

## 🎯 O QUE VOCÊ DEVE FAZER AGORA

### PASSO 1: Localizar onde estão os templates das outras fases

Procure no projeto por:
- `/system/templates/` 
- Ou qualquer pasta que contenha templates de fases anteriores (PHASE1, PHASE2, etc.)
- Ou arquivos como `PHASE4-TEMPLATES.md`, `JARVIS-TEMPLATES.md`, etc.

**Me diga onde encontrou antes de prosseguir.**

### PASSO 2: Criar estrutura para Fase 5

Na mesma localização dos outros templates, criar:
```
PHASE5/
├── MOGA-BRAIN-PHASE5-TEMPLATES.md    ← Arquivo principal de templates
└── IMPLEMENTATION-GUIDE.md            ← Guia de implementação
```

### PASSO 3: Salvar os arquivos anexados

Copiar o conteúdo dos arquivos que enviei para os locais corretos.

### PASSO 4: Atualizar índices

Se existir um `_INDEX.md` ou arquivo similar que liste os templates, adicionar referência aos novos arquivos da Fase 5.

---

## 🔴 POR QUE ISSO É CRÍTICO

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║   REGRA ABSOLUTA DO SISTEMA JARVIS:                                            ║
║                                                                                ║
║   Toda execução de fase DEVE produzir output visual padronizado.               ║
║                                                                                ║
║   - Fase 1 tem seus templates → ✅                                             ║
║   - Fase 2 tem seus templates → ✅                                             ║
║   - Fase 3 tem seus templates → ✅                                             ║
║   - Fase 4 tem seus templates → ✅                                             ║
║   - Fase 5 PRECISA ter seus templates → ⚠️ É ISSO QUE ESTAMOS FAZENDO         ║
║                                                                                ║
║   Sem esses templates, a Fase 5 está INCOMPLETA e o sistema está QUEBRADO.    ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

---

## 📋 O QUE OS TEMPLATES DA FASE 5 CONTÊM

O arquivo `MOGA-BRAIN-PHASE5-TEMPLATES.md` contém **7 templates visuais**:

| Template | Quando Usar |
|----------|-------------|
| **5.1 - FOUNDATION** | Após extrair DNA de uma fonte |
| **5.2 - PERSON AGENTS** | Após criar/atualizar agente de pessoa |
| **5.3 - CARGO AGENTS** | Após criar/atualizar agentes de cargo |
| **5.4 - THEME DOSSIERS** | Após consolidar dossiers temáticos |
| **5.5 - ORG-LIVE** | Após sincronizar estrutura organizacional |
| **5.6 - VALIDATION** | Validação final por fonte |
| **5.FINAL - CONSOLIDADO** | Relatório cross-source após todas as fontes |

Cada template inclui:
- Header ASCII visual
- Seções de delta (antes → depois)
- Gatilhos e alertas
- Top insights com IDs
- Menu de próximas ações

---

## ⚠️ COMPORTAMENTO ESPERADO APÓS IMPLEMENTAÇÃO

### A partir de agora, sempre que a Fase 5 for executada:

1. **Você DEVE carregar** o template apropriado de `/system/templates/PHASE5/`
2. **Você DEVE preencher** as variáveis `{NOME}` com dados reais
3. **Você DEVE exibir** o template completo no chat
4. **Você DEVE incluir** o menu de ações no final

### Exemplo de trigger:

```
USUÁRIO: "Execute a Fase 5 para Cole Gordon"

VOCÊ DEVE:
1. Carregar MOGA-BRAIN-PHASE5-TEMPLATES.md
2. Executar subfase 5.1
3. Exibir Template 5.1 preenchido com dados de Cole Gordon
4. Continuar para 5.2, 5.3, 5.4, 5.5, 5.6
5. Exibir cada template correspondente
```

---

## 🚫 O QUE NUNCA FAZER

```
❌ PROIBIDO: Executar Fase 5 e dar apenas texto corrido como output
❌ PROIBIDO: Resumir ou abreviar os templates
❌ PROIBIDO: Omitir seções dos templates
❌ PROIBIDO: Esquecer de exibir os headers ASCII
❌ PROIBIDO: Pular o menu de ações numeradas no final
❌ PROIBIDO: Ignorar os gatilhos e alertas
❌ PROIBIDO: Não mostrar deltas (antes → depois)
```

---

## ✅ CONFIRMAÇÃO NECESSÁRIA

Após implementar, me confirme:

1. [ ] Onde você salvou os arquivos (path completo)
2. [ ] Se a estrutura de pastas está igual às outras fases
3. [ ] Se atualizou algum índice ou arquivo de referência
4. [ ] Se entendeu que DEVE usar esses templates automaticamente na Fase 5

---

## 💡 ANALOGIA PARA FIXAR

Pense assim:

> Os templates são como o **painel de um carro**. Quando você dirige (executa a fase), o painel (template) mostra velocidade, combustível, alertas. 
>
> **Dirigir sem painel = Executar fase sem template = PROIBIDO**
>
> O motorista (usuário) PRECISA ver o que está acontecendo. Sem o painel visual, ele está cego.

---

## 🔧 COMANDO RESUMIDO

Se precisar de um comando único:

```
"Salve os dois arquivos anexados na pasta de templates do sistema JARVIS, 
junto com os templates das outras fases. A partir de agora, sempre que 
executar a Fase 5, use esses templates para gerar output visual. 
Nunca execute a Fase 5 sem exibir os templates correspondentes."
```

---

## AGORA: EXECUTE OS PASSOS 1-4

Comece me dizendo onde estão os templates das outras fases no projeto.
