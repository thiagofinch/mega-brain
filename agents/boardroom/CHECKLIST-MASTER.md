# BOARDROOM WARFARE - Checklist Master
## Checklist completo para implementação e uso do sistema

---

## 1. Setup Inicial

### Dependências

- [ ] Python 3.8+ instalado
- [ ] pip install elevenlabs
- [ ] pip install pydub
- [ ] ffmpeg instalado (para pydub no Windows)

### Configuração de Ambiente

- [ ] ELEVENLABS_API_KEY configurada como variável de ambiente
- [ ] Conta ElevenLabs com créditos disponíveis
- [ ] Acesso aos voice_ids das vozes desejadas

### Estrutura de Pastas

- [ ] agents/boardroom/ criado
- [ ] CONFIG/ com arquivos de configuração
- [ ] TEMPLATES/ com templates de episódio
- [ ] scripts/ com scripts Python
- [ ] OUTPUTS/scripts/ para scripts gerados
- [ ] OUTPUTS/AUDIO/ para áudios gerados
- [ ] OUTPUTS/temp/ para arquivos temporários

---

## 2. Configuração de Vozes

### Mapeamento Obrigatório

Editar `CONFIG/voice_mapping.json`:

- [ ] NARRATOR - voz do narrador
- [ ] CITADOR - voz para citações
- [ ] HORMOZI - voz de Alex Hormozi
- [ ] COLE_GORDON - voz de Cole Gordon
- [ ] BRUNSON - voz de Russell Brunson
- [ ] CRO - voz do Chief Revenue Officer
- [ ] CFO - voz do Chief Financial Officer
- [ ] CMO - voz do Chief Marketing Officer
- [ ] COO - voz do Chief Operating Officer
- [ ] METHODOLOGICAL-CRITIC - voz do Critic
- [ ] DEVILS-ADVOCATE - voz do Advocate
- [ ] SYNTHESIZER - voz do Sintetizador

### Verificação de voice_ids

- [ ] Cada voice_id corresponde a uma voz válida na conta ElevenLabs
- [ ] Vozes testadas individualmente antes de episódio completo
- [ ] Settings (stability, similarity_boost, style) ajustados por personagem

---

## 3. Integração com Pipeline Jarvis

### Arquivos de Integração

- [ ] jarvis_boardroom_hook.py em scripts/
- [ ] Import adicionado no jarvis_pipeline.py
- [ ] Hook chamado ao final da Fase 8

### Código de Integração

```python
# Verificar se está no jarvis_pipeline.py:
from boardroom.jarvis_boardroom_hook import boardroom_hook

# No final da fase 8:
boardroom_hook(pipeline_outputs)
```

### Formato de Output

- [ ] pipeline_outputs é lista de dicts
- [ ] Cada dict tem: type, title, path, content
- [ ] content contém texto para análise de keywords

---

## 4. Pré-Geração de Episódio

### Análise do Tema

- [ ] Tema claramente definido
- [ ] Keywords identificadas para detecção de participantes
- [ ] Relevância verificada (tema polêmico ou com múltiplas perspectivas)

### Participantes Detectados

- [ ] Mínimo 2 Agents of Person
- [ ] Mínimo 2 Agents of Position
- [ ] Council completo (Critic, Advocate, Synthesizer)
- [ ] Participantes fazem sentido para o tema

### DNA Cognitivo

- [ ] DNA dos participantes existe em knowledge/dna/
- [ ] Princípios relevantes identificados para citação
- [ ] Heurísticas disponíveis para posicionamento

---

## 5. Geração do Script

### Estrutura do Episódio

- [ ] ATO 1: Abertura com narrador
- [ ] ATO 2: Citação da Constituição (DNA)
- [ ] ATO 3: Debate entre Agents of Person (mín. 3 rodadas)
- [ ] ATO 4: Perspectiva dos Agents of Position
- [ ] ATO 5: Deliberação do Council
- [ ] ATO 6: Resolução com scoring
- [ ] ATO 7: Pergunta provocativa ao ouvinte

### Formatação do Script

- [ ] Personagens em [CAIXA_ALTA]
- [ ] Instruções em (parênteses)
- [ ] Textos em "aspas"
- [ ] Sons em [SOM: descrição]
- [ ] Pausas em [PAUSA X seg]
- [ ] Citações com [CITADOR]

### Qualidade do Conteúdo

- [ ] Posições são distintas e confrontantes
- [ ] Argumentos baseados em DNA real dos personagens
- [ ] Gírias e tom característicos de cada agente
- [ ] Tensão produtiva (não resolver fácil demais)
- [ ] Council questiona premissas, não só opina
- [ ] Scoring com justificativas claras
- [ ] Pergunta final é pessoal e provocativa

---

## 6. Geração de Áudio

### Pré-Requisitos

- [ ] Script salvo em OUTPUTS/scripts/
- [ ] ELEVENLABS_API_KEY válida
- [ ] Créditos suficientes na conta
- [ ] voice_mapping.json configurado

### Comando de Geração

```bash
python scripts/audio_generator.py OUTPUTS/scripts/script.md
```

### Verificações Durante Geração

- [ ] Parse identifica todos os segmentos
- [ ] Cada speaker tem voice_id válido
- [ ] Áudios individuais gerados em temp/
- [ ] Concatenação sem erros
- [ ] Arquivo final em OUTPUTS/AUDIO/

### Pós-Geração

- [ ] Arquivos temp/ limpos
- [ ] Duração do áudio razoável (5-15 minutos típico)
- [ ] Qualidade de áudio verificada
- [ ] Transições entre vozes naturais

---

## 7. Quality Assurance

### Script Review

- [ ] Todas as posições são autênticas ao DNA
- [ ] Não há "floreios" ou texto inventado
- [ ] Citações são rastreáveis
- [ ] Scoring é justificado
- [ ] Pergunta final é impactante

### Áudio Review

- [ ] Vozes distinguíveis entre si
- [ ] Tom apropriado para cada personagem
- [ ] Pausas em momentos corretos
- [ ] Sem cortes abruptos
- [ ] Duração total adequada

### Conteúdo Review

- [ ] Debate tem tensão real
- [ ] Council adiciona valor (não só concorda)
- [ ] Resolução faz sentido
- [ ] Ouvinte sai com ação clara

---

## 8. Troubleshooting Checklist

### Script Não Gera

- [ ] Verificar formato do script (.md)
- [ ] Verificar encoding (UTF-8)
- [ ] Verificar regex de parse
- [ ] Testar com --dry-run primeiro

### Áudio Não Gera

- [ ] Verificar ELEVENLABS_API_KEY
- [ ] Verificar voice_ids no mapping
- [ ] Verificar créditos na conta
- [ ] Verificar conexão de internet

### Vozes Incorretas

- [ ] Nome do speaker exatamente como no mapping
- [ ] CAIXA_ALTA consistente
- [ ] Fallback para NARRATOR funcionando

### Áudio Com Problemas

- [ ] pydub instalado corretamente
- [ ] ffmpeg instalado (Windows)
- [ ] Arquivos temp não corrompidos
- [ ] Formato de saída correto (.mp3)

---

## 9. Checklist por Episódio

### Antes de Começar

```
[ ] Tema definido: ________________________________
[ ] Keywords: _____________________________________
[ ] Participantes esperados: ______________________
[ ] Princípio para Constituição: __________________
```

### Durante Geração

```
[ ] Script gerado em: _____________________________
[ ] Segmentos identificados: ______________________
[ ] Duração estimada: _____________________________
```

### Após Conclusão

```
[ ] Áudio salvo em: _______________________________
[ ] Duração final: ________________________________
[ ] Review de qualidade: [ ] Script [ ] Áudio [ ] Conteúdo
[ ] Aprovado para distribuição: [ ] Sim [ ] Não
```

---

## 10. Manutenção Contínua

### Semanal

- [ ] Verificar créditos ElevenLabs
- [ ] Limpar pasta temp/ se necessário
- [ ] Backup de scripts aprovados

### Mensal

- [ ] Atualizar voice_mapping se novas vozes
- [ ] Revisar KEYWORD_MAPPING para novos temas
- [ ] Atualizar templates se necessário

### Por Versão

- [ ] Documentar mudanças em CHANGELOG
- [ ] Atualizar README.md se necessário
- [ ] Testar integração com Jarvis
- [ ] Verificar compatibilidade de dependências
