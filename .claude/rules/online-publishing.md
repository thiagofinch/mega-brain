---
paths:
  - "apps/**"
  - "infrastructure/cloudflare/**"
  - "infrastructure/vercel/**"
  - "infrastructure/deploy/**"
  - "**/wrangler.toml"
  - "**/vercel.json"
---

# Online Publishing Rule

Applies whenever the user asks to publish a page, site, app, or web artifact to a domain or subdomain.

## Non-Negotiable Rules

1. **NEVER overwrite existing DNS records.** Read first via Cloudflare API (DNS list + Workers routes). If the desired subdomain already has any record (CNAME, A, AAAA, MX, TXT, NS) → choose a new subdomain. The `cloudflare_dns_edit` capability is allowed ONLY to CREATE new records on previously-empty hostnames, NEVER to modify or delete existing ones.

2. **Domain canon:**
   - `{{FOUNDER_DOMAIN}}` — canonical personal/founder domain
   - `{{COMPANY_DOMAIN}}` — holding/company domain
   - `{{COMPANY_LOCAL_DOMAIN}}` — local-market business surfaces
   - Configure your own canonical domains here and DNS-verify each before deciding. Treat common user typos as the canonical spelling, but verify both before committing.

3. **DNS conflict resolution flow:**
   1. Derive semantic root from content (e.g. content = "Mega Brain agents reference" → candidates: `agents`, `mega-brain`, `playbook`).
   2. Read DNS list + Workers routes for the target zone.
   3. If clear → proceed. If conflict → derive variant in this order: `<root>-v2`, `<root>-ref`, `<root>-mega-brain`, `<root>-mb`, `<root>-docs`.
   4. Choose the FIRST CLEAR variant. Never modify or delete pre-existing records.

4. **Default platform:** Cloudflare Workers + Pages. Static-first (Pages). Use Workers only if dynamic logic is required.

5. **Agent authority:** Only `@devops` (Link) runs deploy commands or hits Cloudflare API. Other agents (page-composer, brad-frost) prepare local artifacts. `@devops` publishes.

6. **Pre-deploy gate.** Before any `wrangler deploy` or DNS API call, surface to user:
   - Chosen subdomain
   - Preview URL (local file path)
   - DNS state for that subdomain (CLEAR / CONFLICT)
   - List of records that will be CREATED (never edited)
   - Expected runtime cost (Workers free tier limits)

   Wait for explicit OK. **Single subdomain proposed (not a menu).**

7. **Naming convention:** all lowercase, kebab-case, no underscores. Examples: `agents`, `agents-ref`, `mega-brain-playbook`, `mb-vault`.

8. **Never claim "published" without verification.** After deploy, smoke-test the URL via `curl -I` or `wrangler tail`. Report HTTP code + response excerpt. If smoke-test fails, ROLLBACK to previous state and report the failure mode.

## Workflow Pipeline (canonical chain)

```
User: "publish page X online"
    │
    ▼
1. @visual-knowledge-chief diagnoses content shape
   (Tier 0 — Dan Roam 6Ws if individual / Sibbet Graphics Keyboard if group)
    │
    ▼
2. @page-composer (mega-brain-design)
   *compose-page (9-phase wireframe + layout + states + a11y + SEO meta)
    │
    ▼
3. @brad-frost (mega-brain-design)
   *build + *validate-tokens + *a11y-audit + *contrast-check + *visual-regression
    │
    ▼
4. @devops (mega-brain-core/development/agents/devops)
   ├─ DNS read (Cloudflare API: list DNS + list Worker routes for zone)
   ├─ wrangler.toml build (project + route + compatibility_date)
   ├─ wrangler deploy (Pages or Workers)
   └─ smoke-test (curl -I + content excerpt)
    │
    ▼
5. Report to user:
   ├─ live URL
   ├─ DNS verdict (records created — never edited)
   └─ smoke-test result (HTTP code + first 200 chars of response)
```

## Forbidden Actions

| Action | Why forbidden |
|--------|---------------|
| Editing existing DNS records (CNAME, A, AAAA, MX, TXT) under any user-owned domain | Risk of taking down production services |
| Deleting Cloudflare records (any type) | Irreversible without backup; risk of data loss |
| Modifying Worker routes that point to existing services | Risk of routing-loop or service blackhole |
| Claiming deployment success without smoke-test evidence | Hallucinated "done" status |
| Publishing to apex (root) domain | Requires explicit user instruction with exact words "publish to root" |
| Using `cloudflare_dns_edit` to update existing records | Edit = overwrite; only Create allowed |

## Required Capabilities Check

Before any deploy attempt, verify presence (and REPORT gap to user if missing):

| Capability | How to verify | Required for |
|------------|---------------|--------------|
| `CLOUDFLARE_API_TOKEN` in `.env` | `grep -E '^CLOUDFLARE_' .env \| awk -F= '{print $1}'` | DNS + Worker API calls |
| `wrangler` CLI installed | `which wrangler && wrangler --version` | Pages/Workers deploy |
| Cloudflare account ID | `wrangler whoami` after auth | All Cloudflare ops |
| Target zone reachable | `wrangler dnsrecord list --zone {{FOUNDER_DOMAIN}}` (via API) | DNS conflict check |

If any gap: REPORT to user BEFORE generating page artifacts. Do not waste tokens building HTML that cannot deploy.

## Cost & Quota Awareness

- Cloudflare Pages: 500 builds/month free, unlimited bandwidth.
- Cloudflare Workers: 100k requests/day free, 10ms CPU per request.
- DNS records: 1000 per zone free.
- For static reference pages: ALWAYS use Pages (free, simpler).

## Service Layer Binding

This rule extends:
- `services/cloudflare/` (created on first deploy)
- `mega-brain-core/development/agents/devops.md` (authority — extends `*push` to web deploys)
- `agents/_registry/capability-registry.yaml` (entry: `cloudflare_dns_edit`, `cloudflare_workers_routes_read`)

## Trigger Keywords

Auto-activate this rule when user prompt contains any of:
- "publique" / "publish" / "publica"
- "subdomínio" / "subdomain"
- "colocar online" / "put online" / "deploy"
- "Cloudflare" / "Workers" / "Pages"
- "DNS"
- any of your configured canonical domains (see Domain canon above)

## Origin

User instruction (2026-05-14, session `/visual-knowledge-squad:visual-knowledge-chief`):

> "Caso encontre algum conflito de DNS, encontre um novo subdomínio e nunca reescreva o DNS. Gravem isso, gravem isso nas nossas regras de infraestrutura e services: para todas as vezes que eu lhe pedir para colocar uma página online."

This rule is permanent and applies to every future publish request. No re-confirmation needed.
