# Security Layer Test — RAG Isolation

> **Status:** PENDENTE
> **Objetivo:** Confirmar que RAG não expõe conteúdo entre buckets

## Testes Planejados

### Teste 1: Isolamento Personal → Expert
- [ ] Inserir arquivo de teste em knowledge/personal/
- [ ] Executar query RAG em modo expert-only
- [ ] Verificar que arquivo pessoal NÃO aparece nos resultados
- [ ] Resultado: PENDENTE

### Teste 2: Isolamento Business → Expert
- [ ] Inserir arquivo de teste em workspace/
- [ ] Executar query RAG em modo expert-only
- [ ] Verificar que arquivo business NÃO aparece nos resultados
- [ ] Resultado: PENDENTE

### Teste 3: Isolamento Personal → Business
- [ ] Inserir arquivo de teste em knowledge/personal/
- [ ] Executar query RAG em modo business
- [ ] Verificar que arquivo pessoal NÃO aparece nos resultados
- [ ] Resultado: PENDENTE

### Teste 4: Full-3D Access
- [ ] Inserir arquivos em todos os 3 buckets
- [ ] Executar query RAG em modo full-3d
- [ ] Verificar que TODOS os arquivos aparecem nos resultados
- [ ] Resultado: PENDENTE

## Mecanismo de Isolamento

- Cada bucket tem seu próprio RAG index (.data/rag_expert, .data/rag_business, knowledge/personal/index/)
- bucket_router.py controla acesso baseado no modo de consulta
- knowledge/personal/ tem .gitignore próprio que ignora tudo

---
*Testes serão executados após implementação do bucket_router.py (Fase 2 RAG)*
