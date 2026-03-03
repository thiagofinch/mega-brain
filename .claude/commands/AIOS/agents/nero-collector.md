# nero-collector

Ativa o @nero-collector para descoberta e coleta de sources.

## Uso

```
/AIOS:agents:nero-collector
@nero-collector
```

## Quando Usar

- Iniciar busca de sources para nova persona
- Coletar materiais de múltiplas plataformas
- Inventariar conteúdo disponível
- Preparar sources para pipeline

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*discover {persona}` | Busca sources disponíveis para persona |
| `*collect {url}` | Coleta source específico |
| `*inventory` | Lista sources coletados |
| `*validate` | Valida qualidade dos sources |
| `*handoff` | Entrega para nero-researcher |
| `*exit` | Desativa agente |

## Plataformas Suportadas

| Plataforma | Tipo | Prioridade |
|------------|------|------------|
| YouTube | Vídeo (transcrições) | Alta |
| Podcast | Áudio (transcrições) | Alta |
| Blog/Website | Texto | Média |
| Livros | PDF/EPUB | Alta |
| Social Media | Posts | Baixa |

## Exemplo

```
@nero-collector *discover --persona jeremy-miner --platforms youtube,podcast
```

## Agente Downstream

- `@nero-researcher` - Recebe sources para viability assessment
