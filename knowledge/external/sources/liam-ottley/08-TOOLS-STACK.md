# LIAM OTTLEY — Tools e Stack

[[HOME|← Home]] | [[MOC-SOURCES|📚 Sources]] | [[MOC-PESSOAS|👤 Pessoas]] | [[MOC-TEMAS|📦 Temas]]

> **Em resumo:** O stack técnico do AIOS é surpreendentemente acessível. Claude Code como base (não requer saber programar), skills como documentos que ensinam workflows ao AI, e o comando /explore que permite pesquisa autônoma. A tese implícita: AIOS não é para desenvolvedores — é para founders. As ferramentas refletem isso: non-technical access by design.
>
> **Versao:** 1.0 | **Atualizado:** 2026-03-16
> **Densidade:** ◐◐◐◯◯ (3)

---

## Filosofia Central

Liam faz uma distinção que define todo o posicionamento do AIOS:

> "AIOS ≠ ChatGPT. AIOS = sistema com contexto." — [chunk_574, chunk_575]

ChatGPT é genérico — responde qualquer coisa sem conhecer nada sobre o negócio. AIOS é específico — tem contexto profundo sobre o negócio, os processos, as pessoas, as métricas. É a diferença entre um consultor que acabou de chegar e um COO que está na empresa há 5 anos. [chunk_574, chunk_575]

O stack todo é construído para ser acessível a non-technical founders. Claude Code não exige saber programar. Skills são documentos em markdown, não código. O /explore pesquisa e propõe soluções sem input técnico. [chunk_595, chunk_596]

---

## Modus Operandi

### Claude Code como Base

Claude Code é o workspace principal do AIOS. Não é um chatbot — é um ambiente de trabalho onde o AI tem acesso a arquivos, contexto, histórico, e ferramentas. [chunk_574, chunk_575]

```
┌────────────────────────────────────────────────────────────┐
│              CLAUDE CODE vs CHATGPT                         │
├────────────────────────────────────────────────────────────┤
│                                                             │
│   CHATGPT                    CLAUDE CODE (AIOS)             │
│   ┌──────────────┐          ┌──────────────────────┐        │
│   │  Conversa     │          │  Workspace            │       │
│   │  isolada      │          │  ├─ Arquivos do biz   │       │
│   │  sem contexto │          │  ├─ Skills/workflows  │       │
│   │  genérico     │          │  ├─ Histórico         │       │
│   │               │          │  ├─ Integrações       │       │
│   │  "O que você  │          │  └─ Contexto total    │       │
│   │   precisa?"   │          │                       │       │
│   └──────────────┘          │  "Já sei o que você   │       │
│                              │   precisa."           │       │
│                              └──────────────────────┘       │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Skills System

Skills são o conceito mais poderoso para non-technical founders. São **documentos** (markdown) que ensinam ao Claude workflows específicos do negócio. [chunk_576, chunk_577]

```
┌──────────────────────────────────────────────────────┐
│                   SKILLS SYSTEM                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│   SKILL = Documento Markdown                         │
│                                                      │
│   ┌─────────────────────────────────┐                │
│   │  # Gerar Proposta Comercial     │                │
│   │                                 │                │
│   │  ## Contexto                    │                │
│   │  - Empresa: Morningside AI      │                │
│   │  - Serviço: AI Workforce        │                │
│   │                                 │                │
│   │  ## Steps                       │                │
│   │  1. Ler transcript da call      │                │
│   │  2. Identificar pain points     │                │
│   │  3. Mapear para agents          │                │
│   │  4. Calcular ROI                │                │
│   │  5. Gerar PDF da proposta       │                │
│   └─────────────────────────────────┘                │
│                                                      │
│   Resultado: Claude executa o workflow               │
│   inteiro automaticamente                            │
│                                                      │
└──────────────────────────────────────────────────────┘
```

> "Skills = docs que ensinam Claude workflows." — [chunk_576, chunk_577]

O poder das skills é que **não precisa saber programar**. O founder escreve o processo em linguagem natural, e o Claude executa. É como escrever um SOP para um funcionário — exceto que o "funcionário" é uma IA que executa perfeitamente toda vez. [chunk_576, chunk_577]

### /explore Command

O comando /explore é o "botão mágico" do AIOS para non-technical founders: [chunk_595, chunk_596]

1. Founder descreve o problema em linguagem natural
2. Claude pesquisa a codebase e contexto
3. Claude propõe solução com implementação
4. Founder aprova ou ajusta
5. Claude implementa

> "/explore Command: Claude pesquisa e propõe solução." — [chunk_595, chunk_596]

Isso elimina a barreira técnica mais comum: "eu sei o que preciso, mas não sei como pedir para a máquina fazer." O /explore faz a tradução. [chunk_595, chunk_596]

---

## Arsenal Técnico

### Stack Completo do AIOS

| Ferramenta | Papel | Camada AIOS | Chunk |
|------------|-------|-------------|-------|
| **Claude Code** | Base do workspace | L1-L5 (todas) | [chunk_574, chunk_575] |
| **Skills (markdown)** | Workflows automatizados | L4-AUTOMATE | [chunk_576, chunk_577] |
| **/explore** | Pesquisa + proposta | L5-BUILD | [chunk_595, chunk_596] |
| **Telegram** | Interface mobile | L3-INTELLIGENCE | [chunk_549] |
| **Fireflies** | Transcrição de reuniões | L2-DATA | — |
| **Slack** | Comunicação queryable | L2-DATA | — |
| **n8n / Make** | Automação de workflows | L4-AUTOMATE | — |

### Acessibilidade para Non-Technical

| Barreira Tradicional | Solução AIOS |
|---------------------|--------------|
| "Preciso saber programar" | Claude Code + linguagem natural |
| "Preciso entender APIs" | Skills em markdown |
| "Preciso de equipe de dev" | /explore propõe e implementa |
| "Preciso de meses de setup" | 7-Day Sprint com tudo pronto |
| **Chunk** | [chunk_576, chunk_577, chunk_595, chunk_596] |

---

## Armadilhas

### Confundir Claude Code com ChatGPT

O erro mais comum: tratar Claude Code como um chatbot de perguntas e respostas. Claude Code é um workspace — tem acesso a arquivos, pode executar comandos, persiste contexto entre sessões. Usar como chatbot é desperdiçar 95% da capacidade. [chunk_574, chunk_575]

### Skills Genéricas

Skills precisam ser específicas para o negócio. Uma skill genérica de "gerar email" é inútil — o ChatGPT faz isso. Uma skill de "gerar proposta comercial para AI Workforce com pricing baseado em custo humano do cliente" é poderosa. [chunk_576, chunk_577]

### Depender de AI Tricks Isolados

Usar AI para uma coisa aqui, outra ali, sem sistema unificador é o anti-pattern que Liam mais critica. Cada trick é uma ilha. O AIOS é o continente que conecta tudo. [chunk_643]

> "AI tricks fail without unifying system to compound." — [chunk_643]

---

## Citações-Chave

> "AIOS ≠ ChatGPT. AIOS = sistema com contexto." — [chunk_574, chunk_575] contexto: distinção fundamental

> "/explore Command: Claude pesquisa e propõe solução." — [chunk_595, chunk_596] contexto: acesso non-technical

> "Skills = docs que ensinam Claude workflows." — [chunk_576, chunk_577] contexto: skills system

> "AI tricks fail without unifying system to compound." — [chunk_643] contexto: anti-pattern

---

## Metadados

| Campo | Valor |
|-------|-------|
| **Fonte** | Liam Ottley |
| **Tema** | 08-TOOLS-STACK |
| **Chunks** | chunk_574, chunk_575, chunk_576, chunk_577, chunk_595, chunk_596, chunk_643 |
| **Insights** | INS-LO-010, INS-LO-021, INS-LO-023, INS-LO-031 |
| **Protocolo** | Narrative Metabolism v2.0 |
| **Pipeline** | MCE v1.0 |

---

## Fontes Relacionadas

- [Perfil completo Liam Ottley](../../dossiers/persons/DOSSIER-LIAM-OTTLEY.md)
- [DNA: Liam Ottley](../../dna/persons/liam-ottley/)

---

*Compilado via Narrative Metabolism Protocol v1.0*
*Mega Brain System v3.21.0*
