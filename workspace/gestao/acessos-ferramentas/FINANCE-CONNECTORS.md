# Finance Connectors — Specification

> **Path:** `workspace/tools/FINANCE-CONNECTORS.md`
> **PRD Reference:** Section 4.5
> **Status:** PLANNED

---

## Purpose

Connect financial data sources (Google Sheets, CSVs, DRE exports) to `workspace/finance/` so the council can cite real numbers in decisions.

## Data Sources

| Source | Type | Connector | Frequency |
|--------|------|-----------|-----------|
| Google Sheets (KPIs) | Spreadsheet | Google Sheets MCP | On-demand or weekly |
| DRE/P&L exports | CSV/XLSX | Manual upload to inbox | Monthly |
| Bank statements | CSV | Manual upload to inbox | Monthly |
| CRM revenue data | API | ClickUp MCP or n8n | Weekly |

## Schema

The council reads financial data as structured markdown tables. Each financial file in `workspace/finance/` should contain:

```markdown
## KPIs — {Month} {Year}

| Metric | Value | Previous | Delta |
|--------|-------|----------|-------|
| MRR | R$ X | R$ Y | +Z% |
| CAC | R$ X | R$ Y | -Z% |
| LTV | R$ X | R$ Y | +Z% |
| Churn | X% | Y% | -Z% |
| Team Size | X | Y | +Z |
| Monthly Burn | R$ X | R$ Y | +Z% |
```

## Implementation Plan

1. Add `GOOGLE_SHEETS_ID_KPIS` to `.env`
2. Create n8n workflow or use Google Sheets MCP to sync monthly
3. Output: `workspace/finance/KPI-{YYYY-MM}.md`
4. Council reads via `workspace/finance/` path in `full-3d` or `business` mode

## Data Flow

```
Google Sheets / CSV → workspace/inbox/financial/ → bucket_processor → workspace/finance/
```
