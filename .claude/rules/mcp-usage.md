---
paths:
  - ".mcp.json"
  - ".claude/settings*.json"
  - "services/**"
  - "infrastructure/mcp/**"
---
# MCP Usage Rules

Applies when MCP tools are referenced or needed.

## Tool Selection Priority (NON-NEGOTIABLE)

ALWAYS prefer native Claude Code tools over MCP servers:

| Task | USE THIS | NOT THIS |
|------|----------|----------|
| Read files | `Read` tool | docker-gateway / mcp read |
| Write files | `Write` / `Edit` tools | docker-gateway |
| Run commands | `Bash` tool | docker-gateway |
| Search files | `Glob` tool | docker-gateway |
| Search content | `Grep` tool | docker-gateway |
| List directories | `Bash(ls)` or `Glob` | docker-gateway |

## MCP Governance

**ONLY `@devops`** can:
- `claude mcp add/remove/configure`
- Modify `.mcp.json`
- Setup Docker MCP Gateway
- Manage MCP secrets

Other agents are MCP **consumers**, not administrators.

### Management Commands

| Operation | Agent | Command |
|-----------|-------|---------|
| Search MCP catalog | @devops | `*search-mcp` |
| Add MCP server | @devops | `*add-mcp` |
| List enabled MCPs | @devops | `*list-mcps` |
| Remove MCP server | @devops | `*remove-mcp` |
| Setup Docker MCP | @devops | `*setup-mcp-docker` |

## MCP Servers Available

### Direct (Global)
| MCP | Use When |
|-----|----------|
| **playwright** | Browser automation, screenshots, web testing, UI interaction |
| **scrapling** | Adaptive web scraping, anti-bot bypass (Cloudflare), bulk URL extraction |
| **figma-remote-mcp** | Design-to-code, Figma component/style/token extraction |
| **desktop-commander** | Docker container operations |

### Inside Docker (via docker-gateway)
| MCP | Use When |
|-----|----------|
| **EXA** | Web search, research, competitor analysis |
| **Context7** | Library/framework documentation lookup |
| **Apify** | Web scraping, social media data extraction |

## Decision Tree — Scrapling vs Playwright vs Apify

| Scenario | Use |
|----------|-----|
| Site has Cloudflare/anti-bot protection | **scrapling** (`stealthy_fetch`) |
| Bulk scraping 5+ URLs | **scrapling** (`bulk_get` / `bulk_fetch`) |
| Simple HTML content extraction | **scrapling** (`get`) — fastest, no browser overhead |
| Need to interact with site (clicks, forms) | **playwright** |
| Need visual screenshot | **playwright** (`browser_take_screenshot`) |
| Social media at scale (Instagram, TikTok) | **apify** (specialized actors) |
| Official API available (Meta, YouTube) | **Use API directly** — never scrape |
| General keyword search | **WebSearch** (Tier 1) or **EXA** (Tier 3) |
| Library documentation | **Context7** |
| Design tokens from Figma | **Figma Remote MCP** |

## When to Use docker-gateway

ONLY when:
1. User explicitly says "use docker" or "use container"
2. Accessing MCPs running inside Docker (EXA, Context7, Apify)
3. Task specifically requires Docker container operations

NEVER for local file operations — use native tools.

## Known Issues

### Docker MCP Secrets Bug (Dec 2025)

**Issue:** Docker MCP Toolkit's secrets store and template interpolation do not work properly.

**Workaround:** Edit `~/.docker/mcp/catalogs/docker-mcp.yaml` directly with hardcoded env values.

For detailed instructions, ask @devops for assistance.
