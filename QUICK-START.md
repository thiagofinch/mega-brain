# Quick Start — Mega Brain

> Do zero ao seu primeiro Conclave em cerca de 5 minutos.

Este guia assume que voce ja seguiu a instalacao do [README.md](README.md)
(clone, `npm install`, `pip install -r requirements.txt`) e ja preencheu o `.env`
com pelo menos as chaves obrigatorias. Os comandos abaixo rodam dentro do
[Claude Code](https://claude.ai/claude-code), no diretorio do projeto.

A ideia e simples: voce ingere o **seu proprio material**, o sistema extrai o
conhecimento e, em seguida, o Conclave delibera uma decisao sua com base nele.

---

## Passo 1 — Ingira o seu primeiro material

Use `/ingest` com qualquer conteudo seu: um link de video, um PDF, uma
transcricao ou um arquivo local. Aqui usamos um arquivo local como exemplo.

```
/ingest C:\Users\seu-usuario\Documentos\treinamento-vendas.pdf
```

Outros formatos aceitos:

```
/ingest https://www.youtube.com/watch?v=SEU_VIDEO_ID
/ingest C:\Users\seu-usuario\Downloads\reuniao-estrategia.mp4
/ingest C:\Users\seu-usuario\Documentos\transcricao-mentoria.txt
```

**O que acontece:**
- O material e recebido e registrado na fila de ingestao.
- Videos e audios sao transcritos automaticamente.
- O arquivo e classificado por fonte e tipo, com metadados (titulo, autor, data).

**Saida esperada (exemplo):**

```
JARVIS: Material recebido.

  Fonte:    Arquivo local (PDF)
  Titulo:   "Treinamento de Vendas"
  Paginas:  18
  Palavras: 7.420

  Salvo na fila de ingestao.
  Proximo passo: execute /process-jarvis para processar.
```

---

## Passo 2 — Processe com o JARVIS

```
/process-jarvis
```

O JARVIS roda o Pipeline MCE sobre o material da fila:

1. **Transcricao** — converte audio/video em texto (quando aplicavel).
2. **Chunking** — quebra o conteudo em segmentos semanticos.
3. **Resolucao** — identifica pessoas, conceitos e entidades.
4. **Extracao de DNA** — extrai filosofias, modelos mentais, heuristicas,
   frameworks e metodologias.
5. **Indexacao no RAG** — tudo vira busca hibrida (vetorial + BM25), com fontes.

**Saida esperada (exemplo):**

```
JARVIS: Pipeline iniciado.

  Transcricao ......... OK
  Chunking ............ OK (31 chunks)
  Resolucao ........... OK (9 entidades)
  Extracao de DNA ..... OK (14 insights)
  Indexacao no RAG .... OK

  Resultado:
    Conhecimento extraido e indexado.
    14 novos insights disponiveis para consulta e deliberacao.

  Tempo total: ~3 min
```

---

## Passo 3 — Confira o status

```
/jarvis-briefing
```

Mostra o panorama do sistema: o que ja foi processado, agentes ativos e fila.

**Saida esperada (exemplo):**

```
JARVIS: Briefing Operacional

  Base de Conhecimento:
    Materiais processados:  1
    Insights indexados:     14

  Ultimo processamento:
    "Treinamento de Vendas"

  Conclave: pronto para deliberar.
  Fila pendente: 0 arquivos
```

---

## Passo 4 — Sua primeira sessao do Conclave

O Conclave e um conselho multi-agente que delibera uma decisao sua usando
**exclusivamente** o conhecimento que voce ingeriu. Faca uma pergunta estrategica:

```
/conclave "Devo focar o proximo trimestre em aquisicao de novos clientes ou em retencao da base atual?"
```

**O que acontece:**
- Os conselheiros analisam a pergunta sob perspectivas diferentes.
- Cada posicao e fundamentada em evidencias citadas da sua base.
- O Sintetizador consolida tudo em uma recomendacao.

**Saida esperada (exemplo):**

```
CONCLAVE: Sessao iniciada.

  Pergunta: "Aquisicao de novos clientes ou retencao da base atual?"

  ── CRITICO METODOLOGICO ──
  "Antes de escolher, precisamos dos numeros que sustentam a decisao.
  Qual o custo de aquisicao versus o valor de uma base retida? A decisao
  deve seguir a evidencia, nao a preferencia."
  Fonte: knowledge/... (material processado)

  ── ADVOGADO DO DIABO ──
  "Focar em aquisicao parece crescimento, mas se a retencao esta fraca
  voce enche um balde furado. Qual a taxa de churn atual? Sem isso
  resolvido, cada novo cliente custa caro e vaza rapido."
  Fonte: knowledge/... (material processado)

  ── SINTETIZADOR ──
  "Recomendacao: priorizar retencao por 90 dias, estancar o churn e so
  entao escalar aquisicao sobre uma base estavel. Reavaliar com metricas."

  Confianca: limitada pela base atual (1 material processado).
```

> A confianca do Conclave cresce conforme voce alimenta a base. Com poucos
> materiais, as respostas sao mais cautelosas; com varios, ficam mais ricas e
> fundamentadas.

---

## Proximos passos

1. **Ingira mais material.** Quanto mais conhecimento seu na base, mais
   inteligente e fundamentado o sistema fica.
2. **Diversifique as fontes.** Cada novo material adiciona perspectivas ao
   Conclave e enriquece a busca no RAG.
3. **Faca perguntas reais.** Use o `/conclave` nas decisoes que realmente
   importam para o seu negocio.

Para configurar chaves de API adicionais (voz, transcricao avancada), consulte o
[guia de chaves de API](docs/api-keys-guide.md).

---

*Mega Brain — `@thiagofinch/mega-brain`*
