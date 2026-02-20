# integrations - MCP Hub & Notifications

> **Versao:** 1.0.0
> **Status:** Em construcao (SPEC-004)

## Descricao

Central de integrações do [SUA EMPRESA] OS, incluindo MCPs e sistemas de notificação.

## Estrutura

```
integrations/
├── mcps/                           # MCP Hub
│   ├── MCP-REGISTRY.md             # Registro central (a criar)
│   ├── gdrive/                     # Google Drive + Sheets (ATIVO)
│   ├── excalidraw/                 # Diagramas (ATIVO)
│   ├── playwright/                 # Automacao web (AIOS)
│   ├── desktop-commander/          # Controle desktop (AIOS)
│   └── exa/                        # Search avancado (AIOS)
└── notifications/                  # Sistema de notificacoes
    ├── ntfy/                       # Push notifications (Ralph Inferno)
    └── discord/                    # Webhooks (Ralph Inferno)
```

## MCPs Ativos

| MCP | Status | Descricao |
|-----|--------|-----------|
| gdrive | ✅ ATIVO | Google Drive + Sheets |
| excalidraw | ✅ ATIVO | Diagramas |

## MCPs Pendentes (AIOS)

| MCP | Fonte | Descricao |
|-----|-------|-----------|
| playwright | AIOS | Automacao web, screenshots |
| desktop-commander | AIOS | Controle de desktop |
| exa | AIOS | Search avancado |

## Notifications Pendentes (Ralph Inferno)

| Sistema | Descricao |
|---------|-----------|
| ntfy | Push notifications para celular |
| discord | Webhooks para canal |
