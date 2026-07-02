# Me Guia -- Usage Examples

## Example 1: ALTA Confidence (0 questions)

**User:** "Quero criar um carrossel de Instagram sobre retencao de alunos para donos de academia"

**Phase 0 extraction:**
- domain: conteudo (ALTA -- "carrossel", "Instagram")
- action: criar (ALTA -- "criar")
- target: carrossel (ALTA -- explicit)
- business: not specified (skip)
- state: not mentioned (default: nothing)

**Overall confidence:** ALTA

**Response:**
```
Entendi: voce quer criar um carrossel no squad conteudo.
Agent: carousel-creator
Task: squads/conteudo/tasks/create-carousel.md

Executar agora?
```

---

## Example 2: MEDIA Confidence (1 question)

**User:** "Preciso de copy para uma campanha de lancamento"

**Phase 0 extraction:**
- domain: copy OR traffic (MEDIA -- "copy" matches both)
- action: criar (ALTA -- "preciso de")
- target: campanha de lancamento (MEDIA)
- state: not mentioned

**Overall confidence:** MEDIA

**Response:**
```
Encontrei 2 caminhos para sua necessidade:
A) Squad mega-brain-copy -- criar pecas de copy (sales page, VSL, emails)
B) Squad mega-brain-traffic -- criar campanha de ads com criativos

Qual deles?
```

---

## Example 3: BAIXA Confidence (up to 3 questions)

**User:** "Me ajuda"

**Phase 0 extraction:**
- domain: unknown (BAIXA)
- action: unknown (BAIXA)
- target: unknown (BAIXA)

**Overall confidence:** BAIXA

**Response:**
```
Como posso te ajudar?

A) "Sei o que quero"
   Diga: Quero [resultado final], a partir de [o que ja tenho], para [quem vai usar].

B) "Tenho um problema"
   Diga: Hoje [situacao atual] e o problema e [o que esta errado].

C) "Quero explorar"
   Diga: Area: [assunto]. Ja sei [X]. Nao sei [Y].

D) Fale livremente
   Descreva sua necessidade e eu faco as perguntas certas.
```

---

## Example 4: Pipeline with Task Gap

**User:** "Quero criar um curso online a partir de uma transcricao de palestra de 2h"

**Phase 0 extraction:**
- domain: course-creator (ALTA -- "curso online")
- action: criar (ALTA)
- target: curso online (ALTA)
- state: transcricao existente (ALTA)

**Phase 2 resolution:**
```
Step 1: Extrair modulos da transcricao
  BUSCA: squads/course-creator/tasks/...
  MATCH: course-architect (aceita input textual)

Step 2: Organizar modulos em grade curricular
  BUSCA: squads/course-creator/tasks/...
  SEM MATCH

Step 3: Gerar conteudo das aulas
  BUSCA: squads/course-creator/tasks/...
  MATCH: blog-writer (adapta para conteudo de aula)
```

**Response for Step 2 gap:**
```
Nao encontrei uma task existente para: organizar modulos em grade curricular

Tasks mais proximas encontradas:
- course-architect (squads/course-creator/) -- extrai modulos mas nao organiza em grade
- blog-writer (squads/course-creator/) -- gera conteudo mas nao estrutura curriculo

Sugestao: Criar task 'structure-curriculum' no squad course-creator.
- Responsavel: @squad-chief (squad: course-creator)
- A task sera criada ANTES de executar o pipeline

Quer que eu crie essa task?
```

**If accepted, pipeline becomes:**
```markdown
# Pipeline: Curso online a partir de transcricao

## Steps

### [CRIAR] Step 0: Criar task "structure-curriculum"
- Handoff: @squad-chief
- Input: { task_purpose: "Organizar modulos em grade curricular",
           squad_name: "course-creator", agent: "course-architect",
           io_signature: { inputs: ["modules.yaml"], outputs: ["curriculum.yaml"] } }
- Status: [ ] Pendente

### [EXISTENTE] Step 1: course-architect -- Extrair modulos
- Squad: course-creator
- Input: transcricao.md
- Output: modules.yaml
- Status: [ ] Pendente

### [CRIADA] Step 2: structure-curriculum -- Organizar grade
- Squad: course-creator
- Input: modules.yaml
- Output: curriculum.yaml
- Status: [ ] Pendente

### [EXISTENTE] Step 3: blog-writer -- Gerar conteudo
- Squad: course-creator
- Input: curriculum.yaml
- Output: aulas/*.md
- Status: [ ] Pendente
```

---

## Example 5: Mode Inference

| User Says | Extracted | Inferred Mode |
|-----------|-----------|---------------|
| "Quero um brandbook completo" | action=criar, target=brandbook, state=nada | CRIAR |
| "O deploy ta quebrando no CI" | action=resolver, target=CI, state=deploy quebrado | RESOLVER |
| "Como funciona o sistema de squads?" | action=entender, target=squads | ENTENDER |
| "Auditar a seguranca do codigo" | action=validar, target=seguranca | VALIDAR |
| "Configurar o Supabase pra esse projeto" | action=configurar, target=supabase | CONFIGURAR |
| "Qual o status do epic 3?" | action=gerenciar, target=epic | GERENCIAR |
| "Ideias para conteudo de Instagram" | action=explorar, target=conteudo | EXPLORAR |
| "Quero planejar o Q2 do produto" | action=planejar, target=Q2 | PLANEJAR |
