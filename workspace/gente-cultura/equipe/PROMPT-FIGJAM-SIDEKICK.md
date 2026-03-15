# PROMPT PARA FIGJAM SIDEKICK - ORGANOGRAMA BILHON 3.0 (OTIMIZADO)

Cole este prompt no Sidekick do FigJam (clique no icone de IA no canto inferior direito do FigJam).

---

## PROMPT PRINCIPAL (COPIE TUDO ABAIXO):

```
Crie um organograma corporativo profissional para a empresa BILHON com estrutura HIBRIDA: Business Units autonomas + Funcoes Corporativas compartilhadas.

═══════════════════════════════════════════════════════════════
INSTRUCOES DE DESIGN DETALHADAS
═══════════════════════════════════════════════════════════════

LAYOUT GERAL:
- Orientacao: Top-Down (hierarquia de cima para baixo)
- Largura total: ~3000px para acomodar todas as BUs lado a lado
- Espacamento vertical entre niveis: 150px
- Espacamento horizontal entre cards do mesmo nivel: 50px

CARDS (SHAPES):
- Formato: Retangulo com bordas arredondadas (border-radius: 12px)
- CEO: 400x120px, fonte 24px bold
- Diretores/BU Labels: 320x100px, fonte 18px bold
- Heads: 280x80px, fonte 16px bold
- Coordenadores: 240x70px, fonte 14px
- Analistas: 200x60px, fonte 12px

TIPOGRAFIA:
- Nome: MAIUSCULAS, Bold
- Cargo: Capitalizado, Regular

CONECTORES:
- Estilo: Linha solida, 2px
- Cor: Cinza (#666666)
- Tipo: Orthogonal (angulos retos)
- Setas: Apenas na ponta inferior (indicando reporte)

AGRUPAMENTO:
- Cada BU em um Frame/Section separado
- Label da BU no topo do frame
- Background do frame: cor da BU com 10% opacidade

═══════════════════════════════════════════════════════════════
PALETA DE CORES POR AREA
═══════════════════════════════════════════════════════════════

| AREA                    | COR HEX    | NOME            |
|-------------------------|------------|-----------------|
| CEO/Founder             | #CDF4D3    | Verde Claro     |
| BILHON HOLDING          | #E6E6E6    | Cinza           |
| - Pessoas/RH            | #FFE0C2    | Laranja Claro   |
| - Financeiro            | #FFEA79    | Amarelo         |
| - Operacoes             | #E6E6E6    | Cinza           |
| - Produtora             | #E6E6E6    | Cinza           |
| BU CLICKMAX             | #DCCCFF    | Roxo            |
| - Tech                  | #DCCCFF    | Roxo            |
| - Produto               | #DCCCFF    | Roxo            |
| - Marketing Clickmax    | #FFCCE5    | Rosa            |
| - CX/COPS               | #FFE0C2    | Laranja         |
| BU COMERCIAL            | #C2E5FF    | Azul Claro      |
| BRANDING                | #C2FFE5    | Cyan/Verde Agua |
| PRODUTOS EDUCACIONAIS   | #C2E5FF    | Azul Claro      |
| [VAGAS]                 | Borda tracejada, fundo branco    |

═══════════════════════════════════════════════════════════════
NIVEL 0 - FOUNDER & CEO
═══════════════════════════════════════════════════════════════

Posicao: Centro, Topo
Cor: Verde (#CDF4D3)
Tamanho: 400x120px

THIAGO FINCH
Founder & CEO

═══════════════════════════════════════════════════════════════
NIVEL 1 - LABELS DAS BUs (5 blocos lado a lado)
═══════════════════════════════════════════════════════════════

Posicao: Linha horizontal abaixo do CEO
Tamanho: 300x80px cada

Da esquerda para direita:
1. BILHON HOLDING - Funcoes Corporativas (Cinza #E6E6E6)
2. BU CLICKMAX - Produto SaaS (Roxo #DCCCFF)
3. BU COMERCIAL - High-Ticket (Azul #C2E5FF)
4. BRANDING - Marca Pessoal (Cyan #C2FFE5)
5. PRODUTOS EDU (Azul #C2E5FF)

═══════════════════════════════════════════════════════════════
NIVEL 2 - DIRETORES/LIDERES DE BU
═══════════════════════════════════════════════════════════════

--- BILHON HOLDING ---

NATHALIA GOMES | Diretora de Pessoas (Laranja #FFE0C2)
Reporta: CEO

PALOMA FONSECA | Diretora Financeira (Amarelo #FFEA79)
Reporta: CEO

ROMULO SALDANHA | Diretor de Operacoes (Cinza #E6E6E6)
Reporta: CEO

HOMER HENRICCO | Head de Produtora (Cinza #E6E6E6)
Reporta: CEO

--- BU CLICKMAX ---

LEANDRO RESENDE | CEO Clickmax (Roxo #DCCCFF)
Reporta: Founder
Autoridade: P&L completo da BU

--- BU COMERCIAL ---

GUSTAVO PECANHA | Head Comercial (Azul #C2E5FF)
Reporta: CEO
Autoridade: Pipeline, Vendas, Comissoes

--- BRANDING ---

EDUARDO HELUANY | Head de Branding (Cyan #C2FFE5)
Reporta: CEO
Autoridade: Marca pessoal Thiago

--- PRODUTOS EDU ---

TIAGO BRENDON | Head de Educacao (Azul #C2E5FF)
Reporta: CEO
Autoridade: Produtos educacionais

═══════════════════════════════════════════════════════════════
NIVEL 3 - HEADS/COORDENADORES
═══════════════════════════════════════════════════════════════

--- Sob NATHALIA GOMES (Pessoas) ---
WELINGTON SILVA | Coordenador de DP (Laranja #FFE0C2)

--- Sob PALOMA FONSECA (Financeiro) ---
NOEMI BARBOSA | Coordenadora Administrativa (Amarelo #FFEA79)
MARCEL ROSA | FP&A (Amarelo #FFEA79)

--- Sob ROMULO SALDANHA (Operacoes) ---
AQUILA TRINDADE | Head de Infraestrutura (Cinza #E6E6E6)
ISAQUE CARDOSO | Gestor de Projetos (Cinza #E6E6E6)

--- Sob LEANDRO RESENDE (CLICKMAX) ---
ANDRE TESSMANN | CTO (Roxo #DCCCFF)
Autoridade: Tech team, arquitetura, roadmap tecnico

MARLOS HENRI | Head de Produto (Roxo #DCCCFF)
Autoridade: Roadmap produto, priorizacao

RODRIGO GODOY | Head Marketing Clickmax (Rosa #FFCCE5)
Autoridade: Growth, aquisicao Clickmax

AMANDA AUDINO | Diretora Customer Excellence (Laranja #FFE0C2)
Autoridade: NPS, Churn, Retencao

--- Sob AMANDA AUDINO (CX/COPS) ---
COR JESUM | Head de CX (Laranja #FFE0C2)
CAROLINA PEDRINI | Coordenadora de Comunidade (Laranja #FFE0C2)
TAISE ARAUJO | Coordenadora de Atendimento (Laranja #FFE0C2)

--- Sob MARLOS HENRI (Produto) ---
RAFAEL TORALES | Product Designer (Roxo #DCCCFF)

═══════════════════════════════════════════════════════════════
NIVEL 4 - ESPECIALISTAS/ANALISTAS
═══════════════════════════════════════════════════════════════

--- FINANCEIRO (Sob Noemi/Marcel) ---
LAURA HELOISA | Analista Financeiro (Amarelo #FFEA79)
JESSICA DIAS | Assistente Executiva (Amarelo #FFEA79)

--- OPERACOES (Sob Aquila) ---
ROMULO ROCHA | Analista de TI/Infra (Cinza #E6E6E6)

--- TECH (Sob Andre CTO) ---
Desenvolvedores (Roxo #DCCCFF):
- ANDRE VON | Dev Backend
- ARTHUR FIORETTI | Dev Fullstack
- JOAO CABRAL | Dev Fullstack
- PAULO SANTA RITA | Dev Backend
- THIAGO MARQUES | Dev Fullstack
- FILIPE FERNANDES | Dev Frontend
- SAULO SANTANA | Dev Frontend
- LUIGI JORDANIO | Dev Fullstack

Designers (Roxo #DCCCFF):
- AMANDA MERIEN | Designer LP
- ANDRE WALLACE | Designer
- RENATO CARVALHO | Designer

--- MARKETING CLICKMAX (Sob Rodrigo) ---
GUSTAVO TEIXEIRA | Analista Back Office (Rosa #FFCCE5)
JOAO CRUZ | Copywriter (Rosa #FFCCE5)
ALESSANDRO WEDING | Gestor de Trafego (Rosa #FFCCE5)

--- COPS/CX (Sob Cor Jesum/Taise) ---
BRUNA TEIXEIRA | Analista Back Office (Laranja #FFE0C2)
SELMA DUARTE | Analista Atendimento (Laranja #FFE0C2)
ANA CRISTINA | Analista Atendimento (Laranja #FFE0C2)
JORDAN LEAL | Analista Atendimento (Laranja #FFE0C2)
BRUNO MARTINS | Analista Atendimento (Laranja #FFE0C2)
JEAN OLIVEIRA | Analista Atendimento (Laranja #FFE0C2)
DANILO LUIZ | Customer Success (Laranja #FFE0C2)

--- BU COMERCIAL (Sob Gustavo Pecanha) ---
Closers (Azul #C2E5FF):
- TAYNARA TEODOSIO | Closer
- ANNA PAULA MARTINS | Closer
- NATHALIA NOGUEIRA | Closer

Vagas (Borda tracejada, fundo branco):
- [VAGA] SDRs (5-10 posicoes)
- [VAGA] Customer Success (2)
- [VAGA] +Closers (2-3)

--- BRANDING (Sob Eduardo) ---
MARIA LUIZA BUSS | Social Media (Cyan #C2FFE5)
CAUA AZEVEDO | Designer (Cyan #C2FFE5)
JOAO PEDRO PEREIRA | Editor Conteudo (Cyan #C2FFE5)
ANA FLAVIA DAMIAO | Analista (Cyan #C2FFE5)

--- PRODUTOS EDU (Sob Tiago Brendon) ---
PAULO LUCAS | Designer (Azul #C2E5FF)
WILL BERNARDO | Design Instrucional (Azul #C2E5FF)

═══════════════════════════════════════════════════════════════
LEGENDA E ESTATISTICAS
═══════════════════════════════════════════════════════════════

Posicao: Canto inferior direito

ORGANOGRAMA BILHON 3.0
Atualizado: Janeiro 2026

TOTAL: 56 Colaboradores + 14-18 Vagas

DISTRIBUICAO:
- BILHON HOLDING: 12 pessoas
  - Pessoas: 2
  - Financeiro: 5
  - Operacoes: 4
  - Produtora: 1
- BU CLICKMAX: 32 pessoas
  - Lideranca: 2
  - Tech: 12
  - Produto: 2
  - Marketing: 4
  - CX/COPS: 12
- BU COMERCIAL: 4 pessoas + VAGAS
- BRANDING: 5 pessoas
- PRODUTOS EDU: 3 pessoas

═══════════════════════════════════════════════════════════════
INSTRUCOES FINAIS
═══════════════════════════════════════════════════════════════

1. CRIE FRAMES/SECTIONS para cada BU:
   - Frame "BILHON HOLDING" com background cinza 10%
   - Frame "BU CLICKMAX" com background roxo 10%
   - Frame "BU COMERCIAL" com background azul 10%
   - Frame "BRANDING" com background cyan 10%
   - Frame "PRODUTOS EDU" com background azul 10%

2. CONECTORES HIERARQUICOS:
   - CEO → Todos os lideres de BU
   - Cada lider de BU → Seus diretos
   - Use linha solida cinza 2px
   - Conectores ortogonais (angulos de 90 graus)

3. CARDS DE VAGAS:
   - Borda tracejada (dashed)
   - Fundo branco
   - Texto em italico
   - Indicar quantidade

4. VALIDACAO FINAL:
   - Todos os 56 colaboradores presentes?
   - Hierarquia clara de cima para baixo?
   - Cores consistentes por area?
   - Nenhum colaborador orfao (sem conexao)?
   - Vagas indicadas claramente?
```

---

## INSTRUCOES DE USO:

1. Abra seu arquivo FigJam
2. Clique no icone de IA (Sidekick) no canto inferior direito
3. Cole TODO o prompt acima
4. Aguarde a criacao
5. Ajuste posicoes se necessario

---

## PROMPT ALTERNATIVO CURTO (se o longo nao funcionar):

```
Crie um org chart HIBRIDO para BILHON com 56 pessoas + vagas:

CEO: THIAGO FINCH (Founder)

5 BLOCOS PRINCIPAIS:

1. BILHON HOLDING (Corporativo - Cinza/Amarelo/Laranja):
   - Nathalia Gomes (Dir. Pessoas) → Welington
   - Paloma Fonseca (Dir. Financeira) → Noemi, Marcel, Laura, Jessica
   - Romulo Saldanha (Dir. Operacoes) → Aquila, Isaque, Romulo Rocha
   - Homer Henricco (Head Produtora)

2. BU CLICKMAX (Produto SaaS - Roxo):
   - Leandro Resende (CEO Clickmax)
     - Andre Tessmann (CTO) → 8 Devs + 3 Designers
     - Marlos Henri (Head Produto) → Rafael Torales
     - Rodrigo Godoy (Head Marketing) → Gustavo, Joao, Alessandro
     - Amanda Audino (Dir. CX) → Cor Jesum, Carolina, Taise → 7 Analistas

3. BU COMERCIAL HIGH-TICKET (Azul):
   - Gustavo Pecanha (Head Comercial)
     - 3 Closers: Taynara, Anna Paula, Nathalia
     - [VAGAS]: SDRs (5-10), CS (2), +Closers

4. BRANDING (Cyan):
   - Eduardo Heluany (Head Branding)
     - Maria Luiza, Caua, Joao Pedro, Ana Flavia

5. PRODUTOS EDU (Azul Claro):
   - Tiago Brendon (Head Educacao)
     - Paulo Lucas, Will Bernardo

Cores: Tech=roxo, CX/COPS=laranja, Comercial=azul, Financeiro=amarelo, Branding=cyan
Vagas com borda tracejada.
```

---

## MUDANCAS DE TITULOS (Referencia):

| Nome | Titulo Anterior | Titulo Atual |
|------|-----------------|--------------|
| Nathalia Gomes | CHRO | Diretora de Pessoas |
| Paloma Fonseca | Head Adm-Financeiro | Diretora Financeira |
| Eduardo Heluany | CBO | Head de Branding |
| Cor Jesum Duarte | CXO | Head de CX |
| Amanda Audino | Customer Excellence | Diretora de Customer Excellence |
| Gustavo Pecanha | Gerente Comercial | Head Comercial |

*Nota: C-Level mantido apenas para CEO (Thiago) e CEO Clickmax (Leandro)*

---

Criado em: 2026-01-13
Versao: 3.0 (Otimizado com estrutura hibrida)
