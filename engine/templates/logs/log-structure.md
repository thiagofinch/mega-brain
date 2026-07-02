# LOG-STRUCTURE-PROTOCOL.md

> **⚠️ DEPRECATED - NÃO USAR**
> **Versão:** 2.0.0
> **Data:** 2026-01-05
> **Status:** DEPRECATED - Substituído por BATCH-VISUAL-PROTOCOL.md

---

## ⛔ ESTE PROTOCOLO FOI DEPRECADO

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                       ║
║   ❌ NÃO USAR ESTE DOCUMENTO PARA GERAR LOGS                                          ║
║                                                                                       ║
║   ✅ USAR: core/templates/logs/batch-visual-template.md                              ║
║                                                                                       ║
║   Este documento foi substituído por BATCH-VISUAL-PROTOCOL.md que contém:            ║
║   • Template COMPLETO para logs de BATCH (10 seções)                                  ║
║   • Template COMPLETO para logs de SOURCE (12 seções com visual)                      ║
║   • Template COMPLETO para logs de MISSION (cross-source)                             ║
║                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Por Que Foi Deprecado?

1. **Formato errado**: Este documento usava formato de 11 seções + 5 camadas texto
2. **Sem visual**: Não tinha ASCII art, grids, ou boxes visuais
3. **Conflito**: Criava confusão sobre qual template usar

---

## Documento Correto

**FONTE DE VERDADE ÚNICA:** `core/templates/logs/batch-visual-template.md`

### Hierarquia de Templates

| Template | Seções | Quando Usar | Localização Output |
|----------|--------|-------------|-------------------|
| BATCH | 10 | Cada batch | `/logs/batches/BATCH-NNN.md` |
| SOURCE | 12 | Fonte completa | `/logs/SOURCES/SOURCE-{FONTE}.md` |
| MISSION | Cross | Missão completa | `/logs/MISSIONS/MISSION-{ID}-FINAL.md` |

### Referência Implementada


---

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 2.0.0 | 2026-01-05 | DEPRECATED - Substituído por BATCH-VISUAL-PROTOCOL.md |
| 1.0.0 | 2026-01-04 | Versão inicial (formato errado - não usar) |

---

**⚠️ Este arquivo existe apenas para histórico. NÃO seguir os templates originais.**

**SEMPRE usar:** `BATCH-VISUAL-PROTOCOL.md`
