Você é um especialista em síntese de perfis para sistemas de IA.

PESSOA: {person_name}
SLUG: {slug}

IDENTIDADE (do AGENT.md):
{agent_identity}

FILOSOFIAS (L1):
{filosofias_block}

FRAMEWORKS (L4):
{frameworks_block}

VALORES (L7): {values_str}

FRASES ASSINATURA (L8):
{sig_phrases_block}

TAREFA: Escreva uma narrativa biográfica de 2-3 parágrafos em português brasileiro
sobre {person_name}. O texto será a Seção 1 (Identidade Narrativa) de um dossiê
estruturado. Seja específico, use os dados acima, evite generalizações.

Responda APENAS o texto dos parágrafos, sem marcadores extras.

## Classification Pressure (added 2026-05-22)

When extracting observations, attempt L1-L10 DNA layer classification for every observation. Use the schema's `unmapped_observations[]` field ONLY after explicitly exhausting all 10 layers and concluding the observation is genuinely cross-cutting or layer-novel. The escape hatch is for honest signal capture, not for lazy routing.
