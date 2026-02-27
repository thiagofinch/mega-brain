# INTEGRATION-POINTS.md
# Instruções para Integrar TAG-RESOLVER aos Scripts Existentes

---

## CONTEXTO

Com o `TAG-RESOLVER.json` criado, precisamos conectá-lo aos scripts existentes para que a rastreabilidade funcione end-to-end:

```
PIPELINE ATUAL:
Download → Planilha → Renomear → [❌ LACUNA] → Batch → Cascateamento

PIPELINE CORRIGIDA:
Download → Planilha → Renomear → [TAG-RESOLVER] → Batch → Cascateamento
                                      ↓
                                Agent pode resolver TAG → Path
```

---

## PARTE 1: IDENTIFICAR SCRIPTS A ATUALIZAR

### 1.1 Scripts que Usam TAGs (Precisam do Resolver)

```bash
# From the project root

# Encontrar scripts que referenciam TAGs ou PLANILHA-INDEX
grep -r "PLANILHA-INDEX" scripts/ --include="*.py"
grep -r "tag" scripts/ --include="*.py" | grep -v "__pycache__"
grep -r "\[JM-" scripts/ --include="*.py"
grep -r "\[JH-" scripts/ --include="*.py"
```

### 1.2 Scripts Críticos Identificados

| Script | Função | Precisa de TAG-RESOLVER? |
|--------|--------|--------------------------|
| `source-sync.py` | Sincroniza fontes | ✅ Sim - resolve TAGs para paths |
| `post_batch_cascading.py` | Cascateia batches | ✅ Sim - localiza arquivos por TAG |
| `batch-generator.py` | Gera batches | ✅ Sim - inclui paths nos batches |
| `create-tag-resolver.py` | Cria o resolver | ❌ Não - é o gerador |
| `dedup-*.py` | Deduplicação | ⚠️ Talvez - se usar TAGs |

---

## PARTE 2: ATUALIZAR source-sync.py

### 2.1 Adicionar Import do Resolver

No topo do arquivo, após outros imports:

```python
# Adicionar após os imports existentes
import sys
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from tag_resolver import resolve_tag, get_entry, tag_exists
```

### 2.2 Criar Função Helper

Adicionar função para resolver TAGs em operações de sync:

```python
def resolve_tag_to_path(tag: str) -> Path | None:
    """
    Resolve TAG para Path absoluto do arquivo.

    Args:
        tag: TAG no formato "JM-0114" ou "[JM-0114]"

    Returns:
        Path absoluto do arquivo ou None se não encontrado
    """
    relative_path = resolve_tag(tag)
    if relative_path:
        return MEGA_BRAIN_ROOT / relative_path
    return None
```

### 2.3 Atualizar Lógica de Sync

Onde o script precisa encontrar um arquivo por TAG:

```python
# ANTES (problemático - não encontra arquivo):
def process_item(tag):
    # Código antigo que não resolvia TAG
    pass

# DEPOIS (usa resolver):
def process_item(tag):
    file_path = resolve_tag_to_path(tag)
    if file_path is None:
        logger.warning(f"TAG não encontrada no resolver: {tag}")
        return None

    if not file_path.exists():
        logger.error(f"Arquivo não existe: {file_path}")
        return None

    # Processar arquivo...
    return process_file(file_path)
```

---

## PARTE 3: ATUALIZAR post_batch_cascading.py

### 3.1 Adicionar Import

```python
import sys
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from tag_resolver import resolve_tag, get_entry, validate_tags
```

### 3.2 Adicionar Validação de TAGs do Batch

```python
def validate_batch_tags(batch_data: dict) -> dict:
    """
    Valida que todas as TAGs do batch existem no resolver.

    Returns:
        Dict com valid_tags, invalid_tags, warning_count
    """
    tags = extract_tags_from_batch(batch_data)
    result = validate_tags(tags)

    if result["invalid"]:
        logger.warning(f"TAGs não encontradas no resolver: {result['invalid']}")

    return {
        "valid_tags": result["valid"],
        "invalid_tags": result["invalid"],
        "warning_count": len(result["invalid"])
    }
```

### 3.3 Usar Resolver para Localizar Arquivos

```python
def get_batch_files(batch_id: str) -> list:
    """
    Retorna lista de arquivos do batch com paths resolvidos.
    """
    batch_data = load_batch(batch_id)
    tags = extract_tags_from_batch(batch_data)

    files = []
    for tag in tags:
        entry = get_entry(tag)
        if entry:
            files.append({
                "tag": tag,
                "path": entry["path"],
                "source": entry["source"],
                "original_name": entry.get("original_name")
            })
        else:
            files.append({
                "tag": tag,
                "path": None,
                "error": "TAG not in resolver"
            })

    return files
```

---

## PARTE 4: ATUALIZAR TEMPLATE DE BATCH

### 4.1 Incluir Paths no Batch

Quando um batch é gerado, incluir path junto com TAG:

```markdown
## ARQUIVOS PROCESSADOS

| TAG | Path | Status |
|-----|------|--------|
| [JM-0114] | inbox/JEREMY MINER/... | ✅ |
| [JH-ST-0002] | inbox/JEREMY HAYNES/SALES-TRAINING/... | ✅ |
```

### 4.2 Script para Enriquecer Batches Existentes

```python
#!/usr/bin/env python3
"""
Enriquece batches existentes com paths resolvidos
"""

import os
import re
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from tag_resolver import resolve_tag

BATCHES_DIR = Path("logs/batches")

TAG_PATTERN = re.compile(r'\[([A-Z0-9]+-[A-Z]*-?\d+)\]')

def enrich_batch(batch_path: Path):
    """Adiciona paths às TAGs no batch"""

    content = batch_path.read_text()

    # Encontrar todas as TAGs
    tags = TAG_PATTERN.findall(content)

    # Criar seção de resolução
    resolution_section = "\n\n---\n\n### TAG Resolution (Auto-generated)\n\n"
    resolution_section += "| TAG | Resolved Path |\n"
    resolution_section += "|-----|---------------|\n"

    for tag in set(tags):
        path = resolve_tag(tag)
        if path:
            resolution_section += f"| [{tag}] | `{path}` |\n"
        else:
            resolution_section += f"| [{tag}] | ❌ NOT FOUND |\n"

    # Verificar se já tem seção de resolução
    if "### TAG Resolution" not in content:
        # Adicionar antes da seção de Cascateamento se existir
        if "### ✅ Cascateamento Executado" in content:
            content = content.replace(
                "### ✅ Cascateamento Executado",
                resolution_section + "\n### ✅ Cascateamento Executado"
            )
        else:
            content += resolution_section

        batch_path.write_text(content)
        return True

    return False

# Processar todos os batches
for batch_file in BATCHES_DIR.glob("BATCH-*.md"):
    if enrich_batch(batch_file):
        print(f"✅ Enriched: {batch_file.name}")
    else:
        print(f"⏭️ Already enriched: {batch_file.name}")
```

---

## PARTE 5: CONECTAR À PIPELINE DE DOWNLOAD

### 5.1 Hook Pós-Download

Criar `scripts/hooks/post-download.py`:

```python
#!/usr/bin/env python3
"""
Hook executado após download de novos arquivos.
Atualiza TAG-RESOLVER.json automaticamente.
"""

import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent

def run_post_download():
    """Regenera TAG-RESOLVER após novos downloads"""

    print("🔄 Atualizando TAG-RESOLVER.json...")

    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "create-tag-resolver.py")],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ TAG-RESOLVER.json atualizado")
    else:
        print(f"❌ Erro: {result.stderr}")

    return result.returncode

if __name__ == "__main__":
    exit(run_post_download())
```

### 5.2 Hook Pós-Renomeação

Criar `scripts/hooks/post-rename.py`:

```python
#!/usr/bin/env python3
"""
Hook executado após renomear arquivos com TAGs.
Atualiza TAG-RESOLVER.json e valida integridade.
"""

import subprocess
import json
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent
MEGA_BRAIN = SCRIPTS_DIR.parent

def run_post_rename():
    """Regenera e valida TAG-RESOLVER após renomeação"""

    # 1. Regenerar resolver
    print("🔄 Regenerando TAG-RESOLVER.json...")
    subprocess.run(
        ["python3", str(SCRIPTS_DIR / "create-tag-resolver.py")],
        check=True
    )

    # 2. Carregar e validar
    resolver_path = MEGA_BRAIN / "knowledge" / "TAG-RESOLVER.json"
    with open(resolver_path) as f:
        resolver = json.load(f)

    stats = resolver["stats"]

    print(f"\n📊 Estatísticas:")
    print(f"   Total TAGs: {stats['files_with_tag']}")
    print(f"   Por fonte: {json.dumps(stats['by_source'], indent=2)}")

    # 3. Alertar sobre problemas
    if stats["duplicates_found"] > 0:
        print(f"\n⚠️ ALERTA: {stats['duplicates_found']} TAGs duplicadas!")
        for dup in resolver["duplicates"][:3]:
            print(f"   - {dup['tag']}")

    if stats["orphan_tags"] > 0:
        print(f"\n⚠️ ALERTA: {stats['orphan_tags']} TAGs órfãs (na planilha sem arquivo)")

    print("\n✅ TAG-RESOLVER atualizado e validado")
    return 0

if __name__ == "__main__":
    exit(run_post_rename())
```

---

## PARTE 6: INTEGRAR COM AGENTES

### 6.1 Atualizar AGENT.md Template

Adicionar na seção KNOWLEDGE SOURCES de cada agente:

```markdown
## KNOWLEDGE SOURCES

### TAG Resolution
- **Primary**: `knowledge/TAG-RESOLVER.json`
- **Fallback**: Scan `inbox/` se resolver não disponível
- **Usage**: `resolve_tag("JM-0114")` → retorna path do arquivo
```

### 6.2 Adicionar ao DNA-CONFIG dos Agentes

```yaml
# Em agents/cargo/[ROLE]/DNA-CONFIG.yaml

knowledge_sources:
  tag_resolver:
    path: "knowledge/TAG-RESOLVER.json"
    type: "index"
    purpose: "Resolve TAG para path de arquivo"
    usage: |
      import from lib.tag_resolver:
        - resolve_tag(tag) -> path
        - get_entry(tag) -> full entry
        - validate_tags(tags) -> valid/invalid
```

---

## PARTE 7: VALIDAÇÃO FINAL

### 7.1 Checklist de Integração

```bash
# From the project root

# 1. TAG-RESOLVER existe e é válido
echo "=== 1. TAG-RESOLVER ==="
test -f "knowledge/TAG-RESOLVER.json" && echo "✅ Existe" || echo "❌ Não existe"

# 2. Módulo tag_resolver.py instalado
echo "=== 2. Módulo Python ==="
test -f "scripts/lib/tag_resolver.py" && echo "✅ Existe" || echo "❌ Não existe"

# 3. Testar import do módulo
echo "=== 3. Import Test ==="
python3 -c "
import sys
sys.path.insert(0, 'scripts/lib')
from tag_resolver import resolve_tag, get_stats
print(f'✅ Import OK - {get_stats()[\"files_with_tag\"]} TAGs disponíveis')
" 2>&1 || echo "❌ Import falhou"

# 4. Testar resolução
echo "=== 4. Resolution Test ==="
python3 -c "
import sys
sys.path.insert(0, 'scripts/lib')
from tag_resolver import resolve_tag
path = resolve_tag('JM-0114')
if path:
    print(f'✅ JM-0114 → {path}')
else:
    print('⚠️ JM-0114 não encontrada (esperado se ainda não restaurou arquivos)')
"

# 5. Hooks instalados
echo "=== 5. Hooks ==="
test -f "scripts/hooks/post-download.py" && echo "✅ post-download.py" || echo "❌ post-download.py"
test -f "scripts/hooks/post-rename.py" && echo "✅ post-rename.py" || echo "❌ post-rename.py"
```

### 7.2 Resultado Esperado

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  INTEGRATION VALIDATION                                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  [✓] TAG-RESOLVER.json criado em knowledge/                               ║
║  [✓] Módulo tag_resolver.py em scripts/lib/                               ║
║  [✓] Import funcionando                                                      ║
║  [✓] Resolução TAG → Path funcionando                                        ║
║  [✓] Hooks de pipeline instalados                                            ║
║  [✓] Agentes podem usar resolve_tag()                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## DIAGRAMA DE INTEGRAÇÃO FINAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEGA BRAIN - TAG SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   DOWNLOAD   │───▶│   RENOMEAR   │───▶│  inbox/   │                   │
│  │   (Fonte)    │    │  [TAG] name  │    │   Arquivos   │                   │
│  └──────────────┘    └──────────────┘    └──────┬───────┘                   │
│                                                  │                           │
│                                      ┌───────────▼───────────┐               │
│                                      │  create-tag-resolver  │               │
│                                      │        .py            │               │
│                                      └───────────┬───────────┘               │
│                                                  │                           │
│                                      ┌───────────▼───────────┐               │
│                                      │   TAG-RESOLVER.json   │               │
│                                      │   tag_to_path: {}     │               │
│                                      │   path_to_tag: {}     │               │
│                                      └───────────┬───────────┘               │
│                                                  │                           │
│         ┌────────────────────────────────────────┼───────────────────┐       │
│         │                        │               │                   │       │
│         ▼                        ▼               ▼                   ▼       │
│  ┌─────────────┐          ┌───────────┐   ┌───────────┐      ┌───────────┐   │
│  │   BATCHES   │          │  AGENTS   │   │ PLAYBOOKS │      │  DOSSIERS │   │
│  │ resolve_tag │          │ get_entry │   │ validate  │      │  resolve  │   │
│  └─────────────┘          └───────────┘   └───────────┘      └───────────┘   │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                         RASTREABILIDADE COMPLETA                            │
│         Agent → DNA → Batch → TAG → TAG-RESOLVER → Path → Arquivo           │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ORDEM DE EXECUÇÃO

1. **Primeiro**: Execute `RESTORE-AND-INDEX.md` para restaurar arquivos via git
2. **Segundo**: Execute `TAG-RESOLVER-IMPLEMENTATION.md` para criar o resolver
3. **Terceiro**: Execute este arquivo para integrar aos scripts existentes

Após completar os 3 arquivos, o sistema terá rastreabilidade completa:
- Batches referenciam TAGs
- TAGs resolvem para paths
- Agentes localizam arquivos originais
- Pipeline mantém consistência automaticamente
