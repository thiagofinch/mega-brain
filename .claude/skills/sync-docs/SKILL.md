# SYNC-DOCS - Sincronizacao de Documentos [SUA EMPRESA]

## Trigger
`/sync-docs` ou `/sync-docs [caminho-do-arquivo]`

## Objetivo
Sincronizar arquivos .md selecionados com:
1. **Shared Drive [SUA EMPRESA]** (Google Drive via Service Account)
2. **Repositorio Mega Brain** (GitHub)

---

## Pre-requisitos

1. Service Account Google configurada com acesso ao Shared Drive
2. Arquivo de credenciais JSON no caminho especificado em `config.json`
3. Git configurado e autenticado no repositorio
4. Python 3.x com dependencias instaladas

---

## Execucao

### 1. Selecao de Arquivos

**Com caminho especificado:**
```
/sync-docs [SUA EMPRESA]-CORE/templates/BILLION-TEMPLATES.md
```

**Sem caminho (selecao interativa):**
```
/sync-docs
```
- Listar .md disponiveis em locais comuns:
  - `[SUA EMPRESA]-CORE/templates/`
  - `[SUA EMPRESA]-CORE/knowledge/playbooks/`
  - `.aios-core/docs/standards/`
- Usuario seleciona arquivo(s) para sincronizar

### 2. Validacao

Antes de sincronizar, validar:
```
[ ] Arquivo existe e e .md valido
[ ] Arquivo tem conteudo (nao vazio)
[ ] Arquivo nao contem dados sensiveis (checar por patterns)
```

### 3. Sync Google Drive

**Processo:**
1. Autenticar via Service Account
2. Conectar ao Shared Drive [SUA EMPRESA]
3. Navegar para pasta destino (conforme config.json)
4. Upload ou update do arquivo
5. Capturar URL do arquivo no Drive

**Script de suporte:** `gdrive_sync.py`

### 4. Sync Repositorio

**Processo:**
1. `git add [caminho-do-arquivo]`
2. `git commit -m "docs: sync [nome-arquivo]"`
3. `git push origin main`
4. Capturar commit hash

### 5. Confirmacao

**Output de sucesso:**
```
SYNC COMPLETO

Google Drive: https://drive.google.com/file/d/[ID]
GitHub: commit [hash] em main
Timestamp: [YYYY-MM-DD HH:MM:SS]

Arquivo: [nome-do-arquivo]
Tamanho: [X] KB
```

**Output de erro:**
```
SYNC FALHOU

Etapa: [Google Drive | GitHub]
Erro: [mensagem de erro]
Acao: [sugestao de correcao]
```

---

## Configuracao

### config.json
Localizado em: `.claude/skills/sync-docs/config.json`

```json
{
  "google": {
    "credentials_path": "CAMINHO_DO_SERVICE_ACCOUNT_JSON",
    "shared_drive_id": "ID_DO_SHARED_DRIVE_[SUA EMPRESA]",
    "default_folder": "DOCUMENTACAO",
    "folder_mapping": {
      "templates": "Templates",
      "playbooks": "Playbooks",
      "standards": "Standards"
    }
  },
  "github": {
    "repo": "Mega Brain",
    "branch": "main",
    "commit_prefix": "docs: sync",
    "auto_push": true
  },
  "validation": {
    "max_file_size_kb": 5000,
    "sensitive_patterns": [
      "API_KEY",
      "SECRET",
      "PASSWORD",
      "CREDENTIALS"
    ]
  }
}
```

---

## Mapeamento de Pastas

| Origem Local | Destino Google Drive |
|--------------|---------------------|
| `[SUA EMPRESA]-CORE/templates/` | Shared Drive > Templates |
| `[SUA EMPRESA]-CORE/knowledge/playbooks/` | Shared Drive > Playbooks |
| `.aios-core/docs/standards/` | Shared Drive > Standards |

---

## Uso Avancado

### Sync Multiplos Arquivos
```
/sync-docs [SUA EMPRESA]-CORE/templates/*.md
```

### Sync Apenas Google Drive
```
/sync-docs --drive-only [SUA EMPRESA]-CORE/templates/BILLION-TEMPLATES.md
```

### Sync Apenas GitHub
```
/sync-docs --git-only [SUA EMPRESA]-CORE/templates/BILLION-TEMPLATES.md
```

### Dry Run (sem executar)
```
/sync-docs --dry-run [SUA EMPRESA]-CORE/templates/BILLION-TEMPLATES.md
```

---

## Troubleshooting

| Problema | Causa | Solucao |
|----------|-------|---------|
| "Credenciais invalidas" | Service Account expirada ou path errado | Verificar config.json credentials_path |
| "Shared Drive nao encontrado" | ID incorreto ou sem permissao | Verificar shared_drive_id e permissoes |
| "Git push falhou" | Branch protegido ou conflito | Verificar permissoes e fazer pull primeiro |
| "Arquivo muito grande" | Excede max_file_size_kb | Aumentar limite ou dividir arquivo |

---

## Dependencias

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## Checklist de Setup

```
[ ] Service Account criada no Google Cloud Console
[ ] Shared Drive [SUA EMPRESA] com permissao para Service Account
[ ] Arquivo JSON de credenciais baixado
[ ] config.json configurado com paths corretos
[ ] Dependencias Python instaladas
[ ] Git autenticado no repositorio
```
