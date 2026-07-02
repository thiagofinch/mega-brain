#!/usr/bin/env python3
"""Chronicler v4.0 — full render driver (real Jeremy Haynes data).

Imports the v4 prototype primitives and renders ALL 44 STEPs + pre-00 + post-44
in the new wide (100-col) format, then writes the full preview log.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "cv4", _HERE / "chronicler_v4_prototype.py"
)
cv4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cv4)

step_box = cv4.step_box
group_banner = cv4.group_banner
mono_header = cv4.mono_header
mono_footer = cv4.mono_footer
row = cv4.row
rule_top = cv4.rule_top
rule_mid = cv4.rule_mid
rule_bot = cv4.rule_bot
pad = cv4.pad
progress_bar = cv4.progress_bar
INNER = cv4.INNER
W = cv4.W


def pre00() -> str:
    out = [rule_top()]
    out.append(cv4.row_split("📦  pre-00 · BUCKET DE SELEÇÃO", "CAPA · ENTRADA"))
    out.append(rule_mid())
    out.append(row("STATUS   ✅ ROUTE → external/jeremy-haynes · roteamento auditado antes dos 44 STEPs"))
    out.append(row())
    out.extend(cv4.kv_table("ENTRADA & ROTEAMENTO", [
        ("Material", "...launch-a-call-funnel-from-scratch.transcript.txt"),
        ("Tipo", "meeting"),
        ("Verdict", "filename-fallback"),
        ("Confiança", "0.55"),
        ("Bucket", "external"),
        ("Slug", "jeremy-haynes"),
        ("Método", "atlas"),
        ("Cross-refs", "knowledge/business/in..."),
    ]))
    out.append(row())
    out.append(row("📖 POR QUE ESTE BLOCO EXISTE?"))
    for wl in cv4.wrap("Resposta antecipada: para qual bucket o material vai parar. Auditoria de "
                       "roteamento — se o slug aparece no bucket errado, o problema é detectado AQUI, "
                       "antes de descer os 44 STEPs.", INNER - 6):
        out.append(row(f"   {wl}"))
    out.append(rule_bot())
    return "\n".join(out)


# ── all 44 steps as data (real JH values) ───────────────────────────────────
STEPS = [
    dict(icon="🔎", nn="00", title="SOURCE DISCOVERY", g=1,
         status="✅ external / jeremy-haynes / txt · proveniência registrada",
         metrics=[("Fonte", "knowledge/external/in..."), ("Tipo", "txt"),
                  ("Bucket", "external"), ("Slug", "jeremy-haynes"),
                  ("Descoberto", "2026-06-01T02:52:16")],
         why="Rastrear a origem e o primeiro elo da cadeia de custódia do conhecimento. "
             "Sem proveniência, não há auditabilidade."),
    dict(icon="🛡", nn="01", title="INGESTION GUARD", g=1,
         status="✅ PROCESS · conteúdo novo, sem duplicata — pipeline liberado",
         metrics=[("Verdito", "✅ PROCESS"), ("Word count", "9.534"),
                  ("Motivo", "new content"), ("Prev count", "0"),
                  ("Identity key", "58a1f977…"), ("Delta", "0")],
         glossary=[("identity key", "impressão digital (hash) do material. Se 2 arquivos têm a "
                    "mesma, são duplicata e o pipeline pula (SKIP).")],
         why="Se fosse duplicata, o pipeline pararia aqui (SKIP) — zero custo de LLM, nenhum "
             "artefato regravado. A auditoria registra o skip."),
    dict(icon="📥", nn="02", title="DOWNLOAD / EXTRACT", g=1,
         status="✅ youtube-captions · 10.343 palavras extraídas",
         metrics=[("Tier", "yt-dlp+captions"), ("Provider", "youtube-captions"),
                  ("Word count", "10.343"), ("Qualidade", "N/A")],
         glossary=[("captions", "legendas automáticas do YouTube — fallback quando o Gemini "
                    "não devolve transcript nativo.")],
         why="Tier1 (Whisper local) = privacidade, custo zero. Tier2 (Deepgram) = rápido, pago. "
             "Tier3 (texto plano) = sem transcrição."),
    dict(icon="👁", nn="03", title="SPEAKER VISUAL GATE", g=1,
         status="⏭️ BYPASSED · Gemini None → captions assumiram · Speaker: Jeremy Haynes",
         metrics=[("Status", "BYPASSED"), ("Speaker", "Jeremy Haynes"),
                  ("Subject", "scale"), ("Modelo", "n/a")],
         why="Sem visual gate, um vídeo de Ryan Deiss ensinando Hormozi seria atribuído ao "
             "arquivo se chamado 'hormozi-leads.mp4'. O gate usa visão computacional pra "
             "confirmar o speaker."),
    dict(icon="🧬", nn="04", title="ENTITY DISCOVERY", g=1,
         status="✅ filename-fallback → jeremy-haynes · external",
         metrics=[("Decision", "filename-fallback"), ("Slug final", "jeremy-haynes"),
                  ("Bucket final", "external"), ("Gemini usado", "Não")],
         why="decision=FILENAME_WINS: nome do arquivo venceu. GEMINI_WINS: visão computacional "
             "venceu. CONSENSUS: ambos concordaram."),
    dict(icon="📋", nn="05", title="FILENAME SIDECAR WRITE", g=1,
         status="⚠️ NÃO ESCRITO · schema v1.1.0 · 0 campos",
         metrics=[("Status", "NÃO ESCRITO"), ("Schema", "v1.1.0"), ("Campos", "0")],
         glossary=[("sidecar", "arquivo-passaporte ao lado do material com metadados de "
                    "roteamento. Sem ele, o Guard não deduplica entre execuções.")],
         why="Sidecar = passport do material. Perde rastreabilidade entre execuções."),
    dict(icon="📌", nn="06", title="CLASSIFICATION (Atlas)", g=1,
         status="⚠️ confiança 0.55 · Atlas com baixa certeza — revisar",
         metrics=[("Bucket", "(n/d)"), ("Confiança", "0.55"),
                  ("Secundário", "(nenhum)"), ("Método", "(n/d)")],
         why="confidence ≥ 0.8: classificação sólida. < 0.5: Atlas sem certeza, revisar manual. "
             "Buckets: external=experts, business=operacional, personal=fundador."),
    dict(icon="📂", nn="07", title="ORGANIZATION + INBOX ROUTING", g=1,
         status="⚠️ ação não disponível neste run",
         metrics=[("Ação", "(n/d)"), ("Destino", "(n/d)"), ("Arquivos", "0"),
                  ("Fonte reg.", "Não")],
         why="action=moved: arquivo realocado pra inbox/{bucket}/. action=registered: só "
             "metadado. Sem isso o pipeline perderia o fio entre runs."),
    dict(icon="📦", nn="08", title="BATCH CREATION", g=1,
         status="✅ BATCH-6663-JH criado · 232 índices",
         metrics=[("Batch ID", "BATCH-6663-JH"), ("Estado", "created"),
                  ("Chunks", "1"), ("Índice", "0/232")],
         glossary=[("batch", "unidade atômica de processamento. Se o LLM falha no chunk 47, só "
                    "esse batch é retentado — não o vídeo inteiro.")],
         why="BATCH-NNNN-XX: NNNN=sequencial, XX=sub-batch index."),
    dict(icon="✂️", nn="09", title="CHUNKING (semantic split)", g=1,
         status="✅ 166 chunks · ~300 palavras cada · estratégia semantic",
         metrics=[("Total chunks", "166"), ("Média palavras", "300"),
                  ("Estratégia", "semantic"), ("Min/Max", "0/0")],
         glossary=[("chunk", "pedaço de ~300 palavras. Janela ideal pra busca semântica: "
                    "grande demais perde precisão, pequeno demais explode custo.")],
         why="Target ~300 palavras/chunk = janela de contexto ideal pro RAG."),
    dict(icon="🧮", nn="10", title="EMBEDDINGS GENERATION", g=1,
         status="✅ 166 chunks vetorizados em 2.9s · $0.006474",
         metrics=[("Chunks emb.", "166"), ("Tokens", "49.800"),
                  ("Modelo", "text-embed-3-L"), ("Custo", "$0.006474"),
                  ("Dimensões", "1536"), ("Duração", "2.94s")],
         glossary=[("embedding", "vetor de 1536 números que descreve o SIGNIFICADO do texto, "
                    "permitindo busca por sentido (não por palavra literal).")],
         why="Sem embeddings o RAG não acha nada por significado — só por texto literal. "
             "text-embedding-3-large é o modelo canônico (ADR-embedding-01)."),
    dict(icon="🧩", nn="11", title="ENTITY RESOLUTION", g=1,
         status="⚠️ 0 entidades resolvidas neste run",
         metrics=[("Total entidades", "0"), ("Pessoas", "0"),
                  ("Aliases fundidos", "0"), ("CANONICAL-MAP", "(n/d)")],
         glossary=[("alias explosion", "quando 'Alex Hormozi', 'Hormozi' e 'Alex H.' viram 3 "
                    "pessoas diferentes — fragmenta o grafo de conhecimento.")],
         why="Sem resolução, 1 pessoa vira N entidades e o RAG retorna resultados contraditórios "
             "pro mesmo especialista."),
    # GRUPO 2 — DNA
    dict(icon="🧠", nn="12", title="DNA L1 · FILOSOFIAS", g=2,
         status="✅ 29 filosofias extraídas",
         metrics=[("Contagem", "29"), ("Camada", "L1")],
         glossary=[("filosofia (L1)", "crença fundamental que guia TODAS as decisões do "
                    "especialista. As premissas que não mudam.")],
         why="L1 é o núcleo do DNA cognitivo — sobre o que tudo o mais se apoia."),
    dict(icon="🧩", nn="13", title="DNA L2 · MODELOS MENTAIS", g=2,
         status="✅ 5 modelos mentais",
         metrics=[("Contagem", "5"), ("Camada", "L2")],
         glossary=[("modelo mental (L2)", "framework cognitivo pra LER situações — a lente pela "
                    "qual o especialista interpreta o mundo.")],
         why="Modelos mentais determinam como o especialista enxerga um problema antes de agir."),
    dict(icon="🎯", nn="14", title="DNA L3 · HEURÍSTICAS", g=2, tag="⭐ TOP",
         status="✅ 61 heurísticas · a camada mais acionável do DNA",
         metrics=[("Heurísticas", "61"), ("Camada", "L3"),
                  ("Valor", "★★★★★ (top)"), ("Acionável", "imediata")],
         glossary=[("heurística (L3)", "regra prática com número: 'Se X então Y'. O insight que "
                    "vira ação direta — por isso o mais valioso.")],
         why="Heurísticas são o conhecimento operacional — o que o especialista faz na prática "
             "quando a situação X aparece. Núcleo do mind-clone."),
    dict(icon="🏗", nn="15", title="DNA L4 · FRAMEWORKS", g=2,
         status="✅ 14 frameworks",
         metrics=[("Contagem", "14"), ("Camada", "L4")],
         glossary=[("framework (L4)", "modelo estruturado com componentes e etapas nomeadas — "
                    "ex.: 'as 4 fases de um funil de VSL'.")],
         why="Frameworks dão estrutura repetível ao conhecimento — viram checklists e processos."),
    dict(icon="🛤", nn="16", title="DNA L5 · METODOLOGIAS", g=2,
         status="✅ 15 metodologias",
         metrics=[("Contagem", "15"), ("Camada", "L5")],
         glossary=[("metodologia (L5)", "processo step-by-step com inputs e outputs — o 'como "
                    "fazer' detalhado, executável.")],
         why="Metodologias são frameworks com instruções de execução — o passo-a-passo."),
    dict(icon="🔄", nn="17", title="DNA L6 · BEHAVIORAL", g=2,
         status="✅ 5 padrões trigger → action",
         metrics=[("Contagem", "5"), ("Camada", "L6")],
         extra=["  [Se key videos] → [Identifying key content that d]",
                "  [Se your key messages] → [Condense your key messages]"],
         glossary=[("padrão comportamental (L6)", "automatismo gatilho→ação: quando ACONTECE X, "
                    "o especialista REAGE com Y, sem pensar.")],
         why="Padrões comportamentais dão ao agente os reflexos da pessoa, não só o pensamento."),
    dict(icon="⭐", nn="18", title="DNA L7 · VALUES HIERARCHY", g=2,
         status="✅ 3 valores ranqueados",
         metrics=[("Contagem", "3"), ("Camada", "L7")],
         extra=["  #1  Mastering paid advertising is crucial for growth",
                "  #2  Maintain relationships for overall happiness",
                "  #3  Adapt marketing strategies based on engagement"],
         glossary=[("hierarquia de valores (L7)", "o que é inegociável e em que ordem. Define "
                    "trade-offs quando 2 coisas boas conflitam.")],
         why="Sem hierarquia de valores, o agente não sabe o que priorizar quando há conflito."),
    dict(icon="💬", nn="19", title="DNA L8 · VOICE DNA", g=2,
         status="✅ 5 frases-assinatura capturadas",
         metrics=[("Tom", "(n/d)"), ("Frases-sig.", "5")],
         extra=['  1. "one thing is really important to master and that\'s cold paid"',
                '  2. "if you\'re one of those people that just makes like weird vir"',
                '  3. "the interest level is a dynamic thing it fluctuates okay it"'],
         glossary=[("Voice DNA (L8)", "tom + frases-assinatura = identidade vocal. Sem ela o "
                    "agente soa genérico, não soa como a pessoa.")],
         why="Voice DNA é o que faz o agente FALAR como o especialista, não como um robô."),
    dict(icon="🔥", nn="20", title="DNA L9 · OBSESSIONS", g=2,
         status="✅ 3 obsessões mapeadas",
         metrics=[("Contagem", "3"), ("Camada", "L9")],
         extra=["  1. People       (freq=5)",
                "  2. Sales        (freq=5)",
                "  3. Advertising  (freq=23)"],
         glossary=[("obsessão (L9)", "tema recorrente que a pessoa não larga — aparece sem "
                    "parar na fala. Revela prioridade cognitiva real.")],
         why="Obsessões mostram pra onde a atenção do especialista gravita naturalmente."),
    dict(icon="⚡", nn="21", title="DNA L10 · PARADOXES", g=2,
         status="✅ 3 paradoxos (tensão A vs B)",
         metrics=[("Contagem", "3"), ("Camada", "L10")],
         extra=["  1. [?] vs [?]    2. [?] vs [?]    3. [?] vs [?]"],
         glossary=[("paradoxo (L10)", "tensão produtiva entre dois valores/ideias que o "
                    "especialista sustenta ao mesmo tempo. Sinal de maturidade cognitiva.")],
         why="Paradoxos revelam maturidade — quem só tem certezas simples é raso."),
    # GRUPO 3 — Identidade
    dict(icon="🔍", nn="22", title="IDENTITY CHECKPOINT", g=3,
         status="✅ APPROVE · DNA coerente entre as 10 camadas · 144 insights",
         metrics=[("Evidence gate", "✅ PASS"), ("Total insights", "144"),
                  ("Coerência L1-L10", "✅ PASS"), ("Recomendação", "→ Consolidar"),
                  ("Obs/paradoxos", "✅ PASS"), ("Verdito", "✅ APPROVE")],
         glossary=[("checkpoint", "o Lens decide APPROVE / REVISE / ABORT comparando as 10 "
                    "camadas entre si. DNA incoerente = agente que se contradiz.")],
         why="Valida coerência cruzada entre L1–L10 antes de gastar tokens consolidando."),
    dict(icon="📜", nn="23", title="CONSOLIDATION (Forge)", g=3,
         status="✅ dossier-jeremy-haynes.md · 9.533 bytes · 9 seções",
         metrics=[("Dossier", "dossier-jeremy-haynes.md"), ("Tamanho", "9.533 bytes"),
                  ("Seções", "9")],
         extra=["  ## 1 Identidade Narrativa   ## 4 Heurísticas (L3+L5)",
                "  ## 2 Filosofias (L1)        ## 5 Voice & Behavioral (L6+L8)",
                "  ## 3 Modelos & Frameworks   ## 6 Obsessions & Paradoxes (+3)"],
         glossary=[("dossiê", "documento narrativo com todo o DNA integrado. É a fonte de "
                    "verdade que o agente lê durante queries do usuário.")],
         why="O dossiê transforma 10 camadas soltas num retrato coerente e legível."),
    dict(icon="🚀", nn="24", title="AGENT PROMOTION (Echo)", g=3,
         status="✅ PROMOVIDO · agent.md · v1.0.0 · status complete",
         metrics=[("Agent file", "agent.md"), ("Status", "complete"),
                  ("Version", "1.0.0"), ("Tamanho", "2.313 bytes"),
                  ("Promovido", "✅ Sim")],
         glossary=[("promoção", "Echo grava frontmatter status=complete e versão ≥1.0.0. Sem "
                    "isso o Lens nega o gate e o pipeline trava no STEP 22.")],
         why="Promoção marca o agente como pronto pra responder — o nascimento do mind-clone."),
    dict(icon="🧠", nn="25", title="MEMORY ENRICHMENT", g=3,
         status="⚠️ 0 insights novos · 576 deduplicados (já conhecidos)",
         metrics=[("Insights add.", "0"), ("Dedup skip", "576"), ("Agentes", "0")],
         glossary=[("MEMORY.md", "experiência acumulada do agente entre ingestões. Sem ela o "
                    "agente responde só com DNA estático, sem aprendizado.")],
         why="Enriquecimento incremental — só insights NOVOS entram; o resto é dedup."),
    # GRUPO 4 — Cascateamento
    dict(icon="📋", nn="26", title="CASCADING A · ROLE-TRACKER", g=4,
         status="✅ 2 domínios · 12 temas mapeados",
         metrics=[("Domínios", "2"), ("Temas", "12"), ("Cargo agents", "0")],
         glossary=[("role-tracker", "mapa 'quem sabe o quê' — registra em quais domínios e temas "
                    "o especialista é referência, pra rotear queries certas pra ele.")],
         why="Cascading A define onde o especialista entra no routing de perguntas do Conclave."),
    dict(icon="📚", nn="27", title="CASCADING B · DOSSIÊS TEMA", g=4,
         status="✅ 12 temas atualizados · 143 insights processados",
         metrics=[("Temas criados", "0"), ("Temas upd.", "12"),
                  ("Insights proc.", "143")],
         glossary=[("dossiê de tema", "visão agregada de MÚLTIPLOS experts num mesmo tema — "
                    "ex.: 'vendas' junta Hormozi + Cole Gordon + Jeremy Haynes.")],
         why="Permite ao Conclave comparar perspectivas de vários experts sobre o mesmo tema."),
    dict(icon="🎵", nn="28", title="CASCADING C · SOLOS P×TEMA", g=4,
         status="✅ 3 solos escritos · 1 pessoa · 3 temas",
         metrics=[("Solos escritos", "3"), ("Pessoas", "1"), ("Temas", "3")],
         glossary=[("solo P×Tema", "a perspectiva individual isolada de UMA pessoa sobre UM "
                    "tema. Facilita 'o que A pensa sobre X vs o que B pensa'.")],
         why="Solos isolam a voz de cada expert pra comparação limpa, sem contaminação."),
    dict(icon="📝", nn="29", title="NARRATIVE SYNTHESIS", g=4,
         status="✅ 6 narrativas · 6 padrões · 5 pontos de consenso",
         metrics=[("Total narrativas", "6"), ("Padrões", "6"), ("Consenso", "5")],
         glossary=[("narrativa", "insights soltos comprimidos em texto fluido. É o que o agente "
                    "'lê' pra responder com a voz da pessoa, não em bullets.")],
         why="Sem narrativa o agente responde em tópicos desconexos. Aqui virou prosa coerente."),
    dict(icon="📚", nn="30", title="SOURCES COMPILATION", g=4,
         status="⏭️ SKIPPED · fontes já compiladas",
         metrics=[("Status", "SKIPPED"), ("Arquivos", "0"), ("Temas", "0")],
         glossary=[("sources.md", "lista as fontes primárias por tema. Permite auditoria: "
                    "'esse insight veio de qual vídeo/livro?'.")],
         why="Rastreabilidade: cada tema aponta pra fonte de origem do insight."),
    dict(icon="🗺", nn="31", title="DOMAIN AGGREGATOR", g=4,
         status="✅ 7 domínios · 0 conflitos detectados",
         metrics=[("Domínios", "7"), ("Conflitos", "0")],
         extra=["  ads experts=2   offers experts=4   content experts=2",
                "  vendas experts=5   marketing experts=3"],
         glossary=[("MAP-CONFLITOS", "identifica onde experts do mesmo domínio DIVERGEM. Essas "
                    "tensões são o material mais rico pro Conclave.")],
         why="Conflitos entre experts = oportunidades de aprendizado e debate."),
    # GRUPO 5 — Gates
    dict(icon="🔍", nn="32", title="RAG INDEXATION (Art. XV)", g=5,
         status="✅ PASS · índice 4968 → 4968 · Δ+0",
         metrics=[("Gate (Art.XV)", "✅ PASS"), ("Chunks pre", "4968"),
                  ("Chunks post", "4968"), ("Delta", "+0"),
                  ("Vetores", "❌ não atualizados")],
         glossary=[("gate de regressão", "garante que o índice nunca DIMINUA além da tolerância "
                    "sem aprovação. Crescimento é normal e sempre permitido (fix 2026-06-08).")],
         why="O RAG é o motor de busca semântica. O gate protege contra perda silenciosa de dados."),
    dict(icon="🏢", nn="33", title="WORKSPACE SYNC", g=5,
         status="⚪ 0 itens · sem escrita de workspace pra este expert",
         metrics=[("Itens sync.", "0"), ("Escritos", "0"), ("Layers", "(nenhum)")],
         glossary=[("L0–L4", "camadas do workspace: L0 identidade (365d), L1 estratégia (90d), "
                    "L2 tático (60d), L3 produto (30d), L4 operacional (7d).")],
         why="Sync garante que knowledge extraído alimenta as camadas estratégicas do negócio."),
    dict(icon="🚦", nn="34", title="PHASE 8 GATE", g=5,
         status="✅ PASS · 10/10 checks · qualidade final aprovada",
         metrics=[("Gate status", "✅ PASS"), ("Score", "10/10")],
         extra=["  7A ✅  7B ✅  7C ✅  7D ✅  7E ✅",
                "  7F ✅  7G ✅  7H ✅  7I ✅  7J ✅      Score ▓▓▓▓▓▓▓▓▓▓ 10/10"],
         why="10 checks em paralelo validam insights, narrativas, fontes, state files, "
             "role-tracking, cobertura de cascateamento e evolution log."),
    dict(icon="📈", nn="35", title="CROSS-BATCH ANALYSIS", g=5,
         status="⚠️ 4 anomalias · extração 77% abaixo da média histórica",
         metrics=[("Batch ID", "BATCH-20260608-001"), ("Anomalias", "4")],
         extra=["  ⚠️ chunks          dev=-46.4%",
                "  ⚠️ insights_total  dev=-76.7%",
                "  ⚠️ insights_high   dev=-76.6%   insights_medium dev=-77.6%"],
         glossary=[("dev (deviation)", "desvio % vs média histórica do MESMO expert. < -50% = "
                    "anomalia crítica (vermelho); < -25% = moderada (amarelo).")],
         why="Detecta quando uma ingestão rende MUITO menos que o normal — sinal de fonte fraca "
             "ou problema de extração."),
    dict(icon="⚡", nn="36", title="CONTRADICTIONS", g=5,
         status="✅ Sem contradições detectadas · DNA coerente",
         metrics=[("Contradições", "0"), ("DNA", "coerente")],
         why="Ausência de contradições = DNA consistente no histórico. Não significa que o "
             "especialista nunca se contradiz — significa que são sutis ou inexistentes."),
    # GRUPO 6 — Finalização
    dict(icon="📤", nn="37", title="LIFECYCLE MOVE", g=6,
         status="✅ 2 arquivos movidos inbox → processed",
         metrics=[("Arquivos mov.", "2"), ("De", "inbox/jeremy-haynes"),
                  ("Para", "processed/jeremy-haynes")],
         glossary=[("lifecycle move", "move o material processado de inbox/ pra processed/. Sem "
                    "isso o inbox cresce infinito e cada run reprocessa tudo.")],
         why="Evita reprocessamento catastrófico de todo o histórico a cada execução."),
    dict(icon="📊", nn="38", title="BATCH HISTORY UPDATE", g=6,
         status="✅ BATCH-20260608-001 · 100 entries · adicionado",
         metrics=[("Batch ID", "BATCH-20260608-001"), ("Total entries", "100"),
                  ("Adicionado", "✅ Sim")],
         glossary=[("batch history", "série temporal de métricas do pipeline. É a base do "
                    "cross-batch analysis (STEP 35) pra detectar anomalias.")],
         why="Histórico de batches = baseline pra detecção de anomalias futuras."),
    dict(icon="💰", nn="39", title="LLM COST + PROVIDER", g=6,
         status="⚪ $0 · contador centralizado pendente (follow-up conhecido)",
         metrics=[("Custo total", "$0.000000"), ("Input tokens", "0"),
                  ("Output tokens", "0"), ("Total tokens", "0")],
         why="Rastreabilidade de custo por fase. (Wiring do cost-tracker é follow-up separado.)"),
    dict(icon="🤖", nn="40", title="SQUAD ACTIVATION + HOOKS", g=6,
         status="✅ 3 squads acionados",
         metrics=[("Squads", "3")],
         extra=["  + memory_enrichment (1x)   + workspace_sync (1x)",
                "  + dossier_consolidation (1x)"],
         glossary=[("squad activation", "audit trail de quais squads/hooks rodaram. Se o "
                    "pipeline falha em silêncio, mostra qual squad não foi acionado.")],
         why="Telemetria essencial pra debugar falhas silenciosas do pipeline."),
    dict(icon="📋", nn="41", title="EXECUTIVE BRIEFING", g=6,
         status="✅ BRIEFING-JH-20260608.md gerado",
         metrics=[("Arquivo", "BRIEFING-JH-20260608.md")],
         extra=["  Em uma frase: 425 chunks → 144 insights (77% abaixo da média).",
                "  1. Insights totais caíram 77% vs média — fonte mais densa.",
                "  2. Insights de alta relevância também caíram."],
         glossary=[("briefing executivo", "resumo de 3-5 parágrafos gerado por LLM. O operador "
                    "lê em 30s o que mudou e a próxima ação.")],
         why="Decisão rápida sem ler o log inteiro — o TL;DR do run."),
    dict(icon="📊", nn="42", title="HEALTH SCORE", g=6,
         status="⚠️ 65/100 · ATENÇÃO · inbox e pipeline puxam pra baixo",
         metrics=[],
         extra=[f"  Score total   {progress_bar(65,100,24)}  65/100   Grade: ATENÇÃO",
                "  State files ▓▓▓▓▓▓▓▓░░ 15/20    Inbox    ▓▓░░░░░░░░  5/20",
                "  Agents      ▓▓▓▓▓▓▓▓▓▓ 20/20    Pipeline ▓▓░░░░░░░░  5/20",
                "  Dossiers    ▓▓▓▓▓▓▓▓▓▓ 20/20"],
         why="A (90-100) saudável · B (70-89) pequenas lacunas · C (<70) atenção já. Aqui: "
             "agentes e dossiês perfeitos; inbox/pipeline acumulados derrubam."),
    dict(icon="⭐", nn="43", title="PRÓXIMA ETAPA", g=6,
         status="🟡 3 ações priorizadas",
         metrics=[],
         extra=["  🟡 P3  Health Score baixo (65/100) — investigar      [~20min]",
                "  🟢 P4  Revisar insights de maior impacto no dossiê    [~10min]",
                "  🟢 P5  Expandir cross-references com outros experts    [~20min]"],
         why="P1-P2 (vermelho) = blockers. P3 (amarelo) = importante. P4-P5 (verde) = enrichment."),
    dict(icon="🔎", nn="44", title="CHRONICLER AUDIT", g=6,
         status="✅ COMPLETO · 44/44 STEPs renderizados · 2/2 blocos canônicos",
         metrics=[("Steps esperados", "44"), ("Renderizados", "44"),
                  ("Status", "✅ COMPLETO"), ("Blocos canônicos", "2/2"),
                  ("Versão", "Chronicler v4.0")],
         glossary=[("chronicler audit", "meta-verificação que o próprio log faz pra garantir "
                    "que os 44 STEPs renderizaram. Se mostra faltando, o renderer tem bug.")],
         why="O log se auto-audita — COMPLETO = integridade garantida."),
]

GROUPS = {
    1: ("INGESTÃO & PREPARAÇÃO", "00–11", 12),
    2: ("EXTRAÇÃO DE DNA (L1–L10)", "12–21", 10),
    3: ("IDENTIDADE & CONSOLIDAÇÃO", "22–25", 4),
    4: ("CASCATEAMENTO", "26–31", 6),
    5: ("GATES & QUALIDADE", "32–36", 5),
    6: ("FINALIZAÇÃO & TELEMETRIA", "37–44", 8),
}


def post44() -> str:
    out = [rule_top()]
    out.append(cv4.row_split("🌳  post-44 · ÁRVORE DE CASCATEAMENTO", "SAÍDA"))
    out.append(rule_mid())
    out.append(row("STATUS   ✅ jeremy-haynes (external) · artefatos tocados em disco"))
    out.append(row())
    tree = [
        " ├── A. ROLE-TRACKER — domínios cobertos:",
        "       ads[2] · offers[3] · content[2] · vendas[4]",
        "       marketing[3] · funnels[3] · pricing[2]",
        " ├── B. DOSSIÊS DE TEMA (cross-pessoa) — 16 dossiers",
        "       02-processo-vendas · 03-contratacao · 05-metricas",
        "       07-pricing · 09-gestao · call-funnels · (+8)",
        " └── C. SOLOS P×TEMA — 3 solos",
        "       jeremy-haynes--paid-media · --scaling · --vendas",
    ]
    for t in tree:
        out.append(row(t))
    out.append(row())
    out.append(row("📖 POR QUE ESTE BLOCO EXISTE?"))
    for wl in cv4.wrap("Os 44 STEPs descrevem o PROCESSO. Este bloco mostra o OUTPUT: quais "
                       "artefatos em disco foram tocados. Fecha o ciclo ENTRADA (pre-00) + "
                       "PROCESSO (00-44) + SAÍDA (post-44).", INNER - 6):
        out.append(row(f"   {wl}"))
    out.append(rule_bot())
    return "\n".join(out)


def main() -> None:
    blocks: list[str] = [mono_header(), "", "", pre00(), "", ""]
    cur_group = None
    for s in STEPS:
        g = s["g"]
        if g != cur_group:
            name, rng, n = GROUPS[g]
            pct = int(round(int(s["nn"]) / 44 * 100))
            blocks.append(group_banner(g, name, rng, n, pct, int(s["nn"])))
            blocks.append("")
            cur_group = g
        blocks.append(step_box(
            icon=s["icon"], nn=s["nn"], title=s["title"],
            group=f"GRUPO {g}", status=s["status"],
            metrics=s.get("metrics") or None,
            glossary=s.get("glossary"),
            why=s.get("why", ""),
            extra=s.get("extra"),
            tag=s.get("tag", ""),
        ))
        blocks.append("")
        blocks.append("")
    blocks.append(post44())
    blocks.append("")
    blocks.append("")
    blocks.append(mono_footer())

    out_path = _HERE.parents[2] / ".data" / "logs" / "mce" / "jeremy-haynes" / "MCE-JH-v4-preview.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(blocks)
    out_path.write_text(content, encoding="utf-8")
    print(f"v4 preview written: {out_path} ({len(content.splitlines())} lines)")


if __name__ == "__main__":
    main()
