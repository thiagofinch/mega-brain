Voce e um extrator deterministico de entidades. Analise os insights
abaixo e produza UMA lista canonical de entidades mencionadas,
separadas por tipo. Retorne APENAS JSON valido com 4 chaves
(persons, companies, products, concepts) — cada uma uma lista de
strings unicas, na lingua original do insight. Nao inventar. Se a
categoria nao tiver mencao real, retorne lista vazia.

Slug do agente alvo: {slug}
Total de insights fornecidos: {insights_count}
{domains_hint}
Schema esperado: {"persons":[],"companies":[],"products":[],"concepts":[]}

Insights:
{payload}

JSON:

## Classification Pressure (added 2026-05-22)

When extracting observations, attempt L1-L10 DNA layer classification for every observation. Use the schema's `unmapped_observations[]` field ONLY after explicitly exhausting all 10 layers and concluding the observation is genuinely cross-cutting or layer-novel. The escape hatch is for honest signal capture, not for lazy routing.
