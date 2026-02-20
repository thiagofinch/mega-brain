# Quick Start - Mega Brain

> Do zero ao primeiro insight em 5 minutos.

Este guia assume que você já executou a instalação (`npx mega-brain install`) e o setup inicial (`/setup`). Se ainda não fez isso, consulte o [README.md](README.md).

---

## Passo 1: Insira seu primeiro conteúdo

O Mega Brain aceita qualquer material de especialista. Vamos começar com um vídeo do YouTube.

**Comando:**

```
/ingest https://www.youtube.com/watch?v=EXEMPLO_ID
```

**O que acontece:**
- O JARVIS baixa a transcrição automaticamente
- O arquivo é salvo em `inbox/` com metadados (título, autor, data)
- Um registro é criado no sistema de rastreabilidade

**Saída esperada:**

```
JARVIS: Material recebido.

  Fonte:    YouTube
  Título:   "Como Criar Ofertas Irrecusáveis"
  Autor:    Alex Hormozi
  Duração:  42:15
  Palavras: 6.230

  Salvo em: inbox/alex-hormozi/como-criar-ofertas-irrecusaveis.md

  Próximo passo: execute /process-jarvis para processar.
```

**Dica:** Você também pode ingerir arquivos locais (PDFs, transcrições, documentos):

```
/ingest C:\Users\seu-usuario\Downloads\playbook-vendas.pdf
```

---

## Passo 2: Processe com JARVIS

Agora o JARVIS vai processar o material pelo pipeline de 5 fases.

**Comando:**

```
/process-jarvis
```

**O que acontece:**
1. **Chunking** - Quebra o conteúdo em segmentos semânticos
2. **Resolução** - Identifica pessoas, conceitos e entidades
3. **Extração** - Extrai frameworks, insights e regras práticas
4. **Síntese** - Consolida narrativas por tema
5. **Compilação** - Gera dossiê e playbook prontos para uso

**Saída esperada:**

```
JARVIS: Pipeline iniciado.

  Fase 1/5 - Chunking .............. OK (23 chunks)
  Fase 2/5 - Resolução ............ OK (8 entidades)
  Fase 3/5 - Extração ............. OK (12 insights)
  Fase 4/5 - Síntese .............. OK (3 narrativas)
  Fase 5/5 - Compilação ........... OK

  Resultado:
    Dossiê:   knowledge/dossiers/alex-hormozi.md
    Playbook: knowledge/playbooks/ofertas-irrecusaveis.md
    Insights: 12 novos insights indexados

  Tempo total: 2m 34s
```

---

## Passo 3: Veja o resultado

Confira o status geral do sistema e os materiais processados.

**Comando:**

```
/jarvis-briefing
```

**Saída esperada:**

```
JARVIS: Briefing Operacional

  Health Score: 92/100

  Base de Conhecimento:
    Especialistas:  1
    Dossiês:        1
    Playbooks:      1
    Insights:       12

  Último processamento:
    "Como Criar Ofertas Irrecusáveis" (Alex Hormozi)
    Processado em: 2026-02-18 14:30

  Agentes ativos:
    CRO .... Pronto (12 insights carregados)
    CFO .... Pronto (4 insights carregados)
    CMO .... Aguardando material
    COO .... Aguardando material

  Inbox pendente: 0 arquivos
```

---

## Passo 4: Primeira extração de DNA

A extração de DNA cria um clone mental completo de um especialista. Funciona melhor quando você já processou vários materiais do mesmo autor.

**Comando:**

```
/extract-dna alex-hormozi
```

**O que acontece:**
- O JARVIS analisa todos os materiais processados daquele especialista
- Extrai o DNA cognitivo em 5 camadas (Filosofias, Modelos Mentais, Heurísticas, Frameworks, Metodologias)
- Cria um agente dedicado que responde como o especialista

**Saída esperada:**

```
JARVIS: Extração de DNA iniciada.

  Especialista: Alex Hormozi
  Materiais analisados: 1

  Camada L1 - Filosofias .......... OK (5 crenças extraídas)
  Camada L2 - Modelos Mentais ..... OK (3 frameworks)
  Camada L3 - Heurísticas ......... OK (8 regras práticas)
  Camada L4 - Frameworks .......... OK (2 metodologias)
  Camada L5 - Metodologias ........ OK (1 processo completo)

  DNA salvo em: knowledge/dna/alex-hormozi-dna.md
  Agente criado: agents/persons/alex-hormozi.md

  Agora você pode consultar:
    /ask alex-hormozi "Como precificar minha oferta high-ticket?"
```

**Dica:** Quanto mais materiais de um especialista você processar antes da extração de DNA, mais rico e preciso será o clone. Recomendamos pelo menos 3-5 materiais por especialista para resultados de alta fidelidade.

---

## Passo 5: Primeira sessão do Conclave

O Conclave é um conselho de 3 conselheiros que debate qualquer decisão estratégica do seu negócio.

**Comando:**

```
/conclave "Devo lançar um produto de R$2.997 ou R$4.997?"
```

**O que acontece:**
- 3 conselheiros analisam sua pergunta sob perspectivas diferentes
- Cada um fundamenta sua posição com base no conhecimento processado
- O Sintetizador consolida as posições em uma recomendação

**Saída esperada:**

```
CONCLAVE: Sessão iniciada.

  Pergunta: "Devo lançar um produto de R$2.997 ou R$4.997?"

  ── CRÍTICO METODOLÓGICO ──
  "Antes de decidir preço, precisamos validar a Value Equation
  (Hormozi). Qual o dream outcome, time delay, effort e sacrifice
  do seu produto? O preço deve ser consequência do valor percebido,
  não uma decisão arbitrária. Se o valor percebido é 10x o preço,
  ambos funcionam. Se não é, nenhum dos dois funciona."

  Fontes: knowledge/playbooks/ofertas-irrecusaveis.md

  ── ADVOGADO DO DIABO ──
  "R$4.997 parece atraente pela margem, mas considere: qual seu
  volume atual de leads qualificados? Se sua taxa de conversão cair
  de 8% para 4% no preço mais alto, você precisa do dobro de leads.
  Seu funil comporta isso? Qual o CAC atual? Risco: ticket alto
  com funil fraco = receita zero."

  Fontes: Análise de unit economics (CFO)

  ── SINTETIZADOR ──
  "Recomendação: Lance a R$2.997 com upgrade path para R$4.997.
  Isso permite:
  1. Validar conversão no preço menor
  2. Criar case studies com os primeiros alunos
  3. Subir o preço com prova social
  Prazo sugerido: 90 dias no preço menor, avaliar métricas, decidir."

  Consenso: 2/3 recomendam começar por R$2.997
  Confiança: 78% (limitada por base de dados com 1 especialista)
```

---

## Próximos Passos

Agora que você tem o básico funcionando, considere:

1. **Processar mais materiais** - Quanto mais conteúdo, mais inteligente o sistema fica
2. **Diversificar especialistas** - Cada novo especialista adiciona perspectivas ao Conclave
3. **Usar agentes C-Level** - CRO, CFO, CMO e COO ficam mais precisos com mais dados
4. **Configurar JARVIS Voice** - Ative as API keys opcionais para interação por voz

Para configurar API keys adicionais, consulte [API-KEYS-GUIDE.md](API-KEYS-GUIDE.md).

---

*Mega Brain v1.0.0 - MoneyClub Edition*
