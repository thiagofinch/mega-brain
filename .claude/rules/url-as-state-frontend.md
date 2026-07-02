---
paths:
  - "apps/**/*.tsx"
  - "apps/**/*.jsx"
  - "apps/**/src/**"
  - "apps/**/app/**"
  - "apps/**/pages/**"
  - "apps/**/components/**"
---

# URL as State (Frontend Navigation)

> Stub for auto-load. Full content: `minds/knowledge_architect/heuristics/_archived/AN_KE_044-archived-v3.13.0-frontend-specific.md`

## Principle

For frontend navigation state (filters, tabs, pagination, sort, search query) that **must survive refresh, share-link, or back/forward navigation** — store it in the URL (search params or path), NOT in component state.

## When to Apply

| State | URL or component? |
|-------|-------------------|
| Active tab on a dashboard | URL (`?tab=overview`) |
| Filter selections (price, category) | URL (`?category=clothes&price_max=100`) |
| Pagination page number | URL (`?page=3`) |
| Sort order | URL (`?sort=date_desc`) |
| Search query | URL (`?q=react+hooks`) |
| Open/closed modal state | Component (transient, doesn't survive refresh by design) |
| Form draft (before submit) | Component or local storage (don't pollute URL) |
| Dropdown open/closed | Component |

## Why

Sharing a filtered view = sharing the URL. Refresh preserves the user's place. Back/forward works as intended. Without URL-as-state, every refresh resets, every share-link arrives at default, every browser-back loses position.

## Right Pattern

```tsx
// Next.js App Router example
const searchParams = useSearchParams()
const router = useRouter()
const tab = searchParams.get('tab') ?? 'overview'

const setTab = (newTab: string) => {
  const params = new URLSearchParams(searchParams)
  params.set('tab', newTab)
  router.push(`?${params.toString()}`)
}
```

## Anti-Pattern

```tsx
// WRONG — state lost on refresh, no shareable URL, broken back-button UX
const [tab, setTab] = useState<'overview' | 'analytics'>('overview')
```

## Source

AN_KE_044 — promoted to frontend-specific governance, archived 2026-04-27 v3.13.0.
