# Sua Empresa - Company Ingestion Target

Este diretório recebe o output do comando `/ingest-empresa`.

## Como Funciona

1. Coloque material sobre sua empresa no `inbox/` (organograma, JDs, processos, KPIs)
2. Execute `/ingest-empresa` para processar o material
3. O pipeline JARVIS (8 fases) processa e classifica automaticamente
4. O output é roteado para as subpastas abaixo

## Estrutura

```
sua-empresa/
├── org/          # Organograma, estrutura hierárquica
├── roles/        # Definições de cargo (ROLE-*.md)
├── jds/          # Job Descriptions (JD-*.md)
├── operations/   # Processos, rituais, comunicação
├── metrics/      # KPIs, metas, dashboards
├── memory/       # Memória operacional dos agentes
├── sow/          # Scope of Work por cargo
└── _example/     # Exemplo de empresa processada
```

## Routing do Pipeline

| Tipo de Material | Destino |
|------------------|---------|
| Organograma, hierarquia | `org/` |
| Descrição de cargo, perfil | `roles/` |
| Vaga, requisitos, competências | `jds/` |
| Processo, ritual, ferramenta | `operations/` |
| KPI, meta, métrica | `metrics/` |
| Escopo de trabalho | `sow/` |

## Layer Model

- **Layer 1 (público):** Esta estrutura + `_example/`
- **Layer 2 (gated):** Templates avançados de ingestão
- **Layer 3 (local):** Seus dados reais (gitignored)

Todo conteúdo gerado pelo pipeline é automaticamente ignorado pelo git.
Apenas a estrutura vazia e o exemplo são distribuídos no pacote npm.
