# No Secrets in Memory Files

> **Auto-Trigger:** memory, credentials, API key, token, webhook
> **Keywords:** "memory", "credentials", "API key", "secret", "token"
> **Prioridade:** CRITICA

## Rule

NEVER store API keys, tokens, webhook URLs, passwords, or any credentials as plaintext values in:
- MEMORY.md or auto-memory files
- CLAUDE.md files
- Rule files
- Any file that is committed to git or persists across sessions

Use reference-only entries pointing to `.env`:
- CORRECT: "Fireflies API key: stored in `.env` as `FIREFLIES_API_KEY`"
- WRONG: "Fireflies API key: fe9bae31-e325-..."

## Enforcement

If you detect a secret being written to a memory or config file:
1. STOP the write
2. WARN the user
3. Suggest storing in `.env` instead
