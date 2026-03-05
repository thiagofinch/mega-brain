# TAG-RESOLVER-IMPLEMENTATION.md
# Instruções para Criar o Sistema de Resolução TAG ↔ Path

---

## CONTEXTO

O sistema atual tem uma lacuna crítica:
- `PLANILHA-INDEX.json` tem 915 entries com `tag`, `original_name`, `sheet`
- **NÃO TEM** campo `path` - não sabe onde o arquivo está fisicamente
- Batches referenciam TAGs (ex: `JH-ST-0002`)
- Agentes não conseguem resolver TAG → arquivo real

---

## PARTE 1: CRIAR TAG-RESOLVER.json

### 1.1 Script Python para Gerar o Resolver

Criar arquivo `scripts/create-tag-resolver.py`:

```python
#!/usr/bin/env python3
"""
TAG-RESOLVER Generator
Cria índice bidirecional TAG ↔ Path para o sistema Mega Brain

Uso:
    python create-tag-resolver.py

Output:
    knowledge/TAG-RESOLVER.json
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configuração
MEGA_BRAIN_ROOT = Path(__file__).parent.parent  # Sobe de scripts para raiz
INBOX_PATH = MEGA_BRAIN_ROOT / "inbox"
OUTPUT_PATH = MEGA_BRAIN_ROOT / "knowledge" / "TAG-RESOLVER.json"
PLANILHA_INDEX_PATH = MEGA_BRAIN_ROOT / "PLANILHA-INDEX.json"

# Regex para extrair TAGs do nome do arquivo
# Formatos suportados:
# - [JM-0114] filename.txt
# - [JH-ST-0002] filename.txt
TAG_PATTERN = re.compile(r'\[([A-Z0-9]+-[A-Z]*-?\d+)\]')

def extract_tag_from_filename(filename: str) -> str | None:
    """Extrai TAG do nome do arquivo"""
    match = TAG_PATTERN.search(filename)
    return match.group(1) if match else None

def get_source_code(path: str) -> str:
    """Determina o código fonte baseado no path"""
    path_lower = path.lower()

    if "jeremy miner" in path_lower or "7th level" in path_lower:
        return "JM"
    elif "jeremy haynes" in path_lower:
        if "sales-training" in path_lower:
            return "JH-ST"
        elif "inbound-closer" in path_lower:
            return "JH-IC"
        else:
            return "JH"
    elif "alex hormozi" in path_lower or "alex-hormozi" in path_lower:
        return "AH"
    elif "cole gordon" in path_lower or "cole-gordon" in path_lower:
        return "CG"
    else:
        return "UNK"

def scan_inbox(inbox_path: Path) -> dict:
    """Varre o INBOX e cria mapeamento TAG → Path"""

    tag_to_path = {}
    path_to_tag = {}
    stats = {
        "total_files": 0,
        "files_with_tag": 0,
        "files_without_tag": 0,
        "by_source": defaultdict(int),
        "duplicates": [],
        "errors": []
    }

    print(f"Scanning: {inbox_path}")

    for root, dirs, files in os.walk(inbox_path):
        # Ignorar pastas de backup
        dirs[:] = [d for d in dirs if not d.startswith('_')]

        for filename in files:
            # Ignorar arquivos ocultos e de sistema
            if filename.startswith('.') or filename.startswith('_'):
                continue

            stats["total_files"] += 1

            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, MEGA_BRAIN_ROOT)

            tag = extract_tag_from_filename(filename)

            if tag:
                stats["files_with_tag"] += 1
                source = get_source_code(relative_path)
                stats["by_source"][source] += 1

                # Verificar duplicata
                if tag in tag_to_path:
                    stats["duplicates"].append({
                        "tag": tag,
                        "path1": tag_to_path[tag],
                        "path2": relative_path
                    })
                    print(f"  ⚠️ TAG duplicada: {tag}")
                else:
                    tag_to_path[tag] = relative_path
                    path_to_tag[relative_path] = tag
            else:
                stats["files_without_tag"] += 1

    return {
        "tag_to_path": tag_to_path,
        "path_to_tag": path_to_tag,
        "stats": stats
    }

def load_planilha_index(path: Path) -> dict:
    """Carrega PLANILHA-INDEX.json existente"""
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"entries": []}

def merge_with_planilha(resolver_data: dict, planilha_data: dict) -> dict:
    """Merge resolver com dados da planilha"""

    tag_to_path = resolver_data["tag_to_path"]

    # Criar índice por tag da planilha
    planilha_by_tag = {}
    for entry in planilha_data.get("entries", []):
        if "tag" in entry:
            planilha_by_tag[entry["tag"]] = entry

    # Criar entries enriquecidas
    enriched_entries = []

    for tag, path in tag_to_path.items():
        entry = {
            "tag": tag,
            "path": path,
            "source": get_source_code(path),
            "filename": os.path.basename(path)
        }

        # Enriquecer com dados da planilha se existir
        if tag in planilha_by_tag:
            planilha_entry = planilha_by_tag[tag]
            entry["original_name"] = planilha_entry.get("original_name")
            entry["sheet"] = planilha_entry.get("sheet")
            entry["in_planilha"] = True
        else:
            entry["in_planilha"] = False

        enriched_entries.append(entry)

    # Identificar TAGs na planilha sem arquivo
    orphan_tags = []
    for tag in planilha_by_tag:
        if tag not in tag_to_path:
            orphan_tags.append({
                "tag": tag,
                "original_name": planilha_by_tag[tag].get("original_name"),
                "sheet": planilha_by_tag[tag].get("sheet")
            })

    return {
        "entries": enriched_entries,
        "orphan_tags": orphan_tags
    }

def create_tag_resolver():
    """Função principal - cria TAG-RESOLVER.json"""

    print("=" * 60)
    print("TAG-RESOLVER Generator")
    print("=" * 60)
    print()

    # 1. Scan do INBOX
    print("📁 Fase 1: Scanning INBOX...")
    resolver_data = scan_inbox(INBOX_PATH)

    print(f"   Total arquivos: {resolver_data['stats']['total_files']}")
    print(f"   Com TAG: {resolver_data['stats']['files_with_tag']}")
    print(f"   Sem TAG: {resolver_data['stats']['files_without_tag']}")
    print()

    # 2. Carregar planilha existente
    print("📊 Fase 2: Loading PLANILHA-INDEX.json...")
    planilha_data = load_planilha_index(PLANILHA_INDEX_PATH)
    print(f"   Entries na planilha: {len(planilha_data.get('entries', []))}")
    print()

    # 3. Merge dados
    print("🔗 Fase 3: Merging data...")
    merged_data = merge_with_planilha(resolver_data, planilha_data)
    print(f"   Entries enriquecidas: {len(merged_data['entries'])}")
    print(f"   TAGs órfãs (na planilha sem arquivo): {len(merged_data['orphan_tags'])}")
    print()

    # 4. Criar output final
    output = {
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generator": "create-tag-resolver.py",
        "stats": {
            "total_files_scanned": resolver_data["stats"]["total_files"],
            "files_with_tag": resolver_data["stats"]["files_with_tag"],
            "files_without_tag": resolver_data["stats"]["files_without_tag"],
            "by_source": dict(resolver_data["stats"]["by_source"]),
            "duplicates_found": len(resolver_data["stats"]["duplicates"]),
            "orphan_tags": len(merged_data["orphan_tags"])
        },
        "tag_to_path": resolver_data["tag_to_path"],
        "path_to_tag": resolver_data["path_to_tag"],
        "entries": merged_data["entries"],
        "orphan_tags": merged_data["orphan_tags"],
        "duplicates": resolver_data["stats"]["duplicates"]
    }

    # 5. Salvar
    print(f"💾 Fase 4: Saving to {OUTPUT_PATH}...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Salvo: {OUTPUT_PATH}")
    print()

    # 6. Sumário
    print("=" * 60)
    print("SUMÁRIO")
    print("=" * 60)
    print(f"Total TAGs mapeadas: {len(output['tag_to_path'])}")
    print(f"Por fonte:")
    for source, count in sorted(output["stats"]["by_source"].items()):
        print(f"  - {source}: {count}")

    if output["duplicates"]:
        print(f"\n⚠️ ATENÇÃO: {len(output['duplicates'])} TAGs duplicadas encontradas!")
        for dup in output["duplicates"][:5]:
            print(f"  - {dup['tag']}: {dup['path1']} vs {dup['path2']}")

    if output["orphan_tags"]:
        print(f"\n⚠️ ATENÇÃO: {len(output['orphan_tags'])} TAGs na planilha sem arquivo!")
        for orphan in output["orphan_tags"][:5]:
            print(f"  - {orphan['tag']}: {orphan['original_name']}")

    print()
    print("✅ TAG-RESOLVER.json criado com sucesso!")
    return output

if __name__ == "__main__":
    create_tag_resolver()
```

### 1.2 Executar o Script

```bash
python3 scripts/create-tag-resolver.py
```

**Resultado esperado:**
- Arquivo `knowledge/TAG-RESOLVER.json` criado
- ~727 TAGs mapeadas para seus paths
- Relatório de TAGs duplicadas ou órfãs

---

## PARTE 2: VALIDAR TAG-RESOLVER

### 2.1 Verificar Estrutura

```bash
# Verificar que arquivo foi criado
ls -la "knowledge/TAG-RESOLVER.json"

# Ver estatísticas
cat "knowledge/TAG-RESOLVER.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('=== TAG-RESOLVER Stats ===')
print(f'Version: {data[\"version\"]}')
print(f'Generated: {data[\"generated_at\"]}')
print(f'Total TAGs: {len(data[\"tag_to_path\"])}')
print()
print('Por fonte:')
for src, count in sorted(data['stats']['by_source'].items()):
    print(f'  {src}: {count}')
print()
print(f'Duplicatas: {data[\"stats\"][\"duplicates_found\"]}')
print(f'Órfãs: {data[\"stats\"][\"orphan_tags\"]}')
"
```

### 2.2 Testar Resolução de TAGs

```bash
# Script de teste rápido
python3 << 'EOF'
import json

with open("knowledge/TAG-RESOLVER.json") as f:
    resolver = json.load(f)

# Testar algumas TAGs conhecidas

print("=== Teste de Resolução TAG → Path ===")
for tag in test_tags:
    path = resolver["tag_to_path"].get(tag)
    if path:
        print(f"✅ {tag} → {path}")
    else:
        print(f"❌ {tag} → NOT FOUND")

print()
print("=== Teste de Resolução Path → TAG ===")
# Pegar 3 paths aleatórios
for path in list(resolver["path_to_tag"].keys())[:3]:
    tag = resolver["path_to_tag"][path]
    print(f"✅ {path[:50]}... → {tag}")
EOF
```

### 2.3 Resultado Esperado

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  TAG-RESOLVER VALIDAÇÃO                                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  [✓] Arquivo criado em knowledge/TAG-RESOLVER.json                        ║
║  [✓] ~727 TAGs mapeadas                                                      ║
║  [✓] Resolução bidirecional funcionando                                      ║
║  [✓] Stats por fonte calculados                                              ║
║  [✓] Duplicatas identificadas (se houver)                                    ║
║  [✓] Órfãs identificadas (TAGs na planilha sem arquivo)                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## PARTE 3: FUNÇÃO HELPER PARA USO EM SCRIPTS

### 3.1 Criar Módulo tag_resolver.py

Adicionar em `scripts/lib/tag_resolver.py`:

```python
#!/usr/bin/env python3
"""
TAG Resolver Library
Funções helper para resolver TAG ↔ Path em scripts do Mega Brain
"""

import json
import os
from pathlib import Path
from functools import lru_cache

# Cache do resolver
_resolver_cache = None
_resolver_path = None

def get_resolver_path() -> Path:
    """Retorna path do TAG-RESOLVER.json"""
    global _resolver_path
    if _resolver_path is None:
        # Tenta encontrar o arquivo subindo diretórios
        current = Path(__file__).resolve()
        for _ in range(5):
            current = current.parent
            candidate = current / "knowledge" / "TAG-RESOLVER.json"
            if candidate.exists():
                _resolver_path = candidate
                break
    return _resolver_path

@lru_cache(maxsize=1)
def load_resolver() -> dict:
    """Carrega e cacheia o TAG-RESOLVER.json"""
    global _resolver_cache
    if _resolver_cache is None:
        path = get_resolver_path()
        if path and path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                _resolver_cache = json.load(f)
        else:
            raise FileNotFoundError("TAG-RESOLVER.json não encontrado. Execute create-tag-resolver.py primeiro.")
    return _resolver_cache

def resolve_tag(tag: str) -> str | None:
    """
    Resolve TAG para path do arquivo

    Args:
        tag: TAG no formato "JM-0114" ou "[JM-0114]"

    Returns:
        Path relativo do arquivo ou None se não encontrado
    """
    # Remove colchetes se presentes
    tag = tag.strip("[]")

    resolver = load_resolver()
    return resolver["tag_to_path"].get(tag)

def resolve_path(path: str) -> str | None:
    """
    Resolve path para TAG

    Args:
        path: Path relativo do arquivo

    Returns:
        TAG ou None se não encontrado
    """
    resolver = load_resolver()
    return resolver["path_to_tag"].get(path)

def get_entry(tag: str) -> dict | None:
    """
    Retorna entry completa para uma TAG

    Args:
        tag: TAG no formato "JM-0114"

    Returns:
        Dict com tag, path, source, filename, original_name, sheet, in_planilha
    """
    tag = tag.strip("[]")
    resolver = load_resolver()

    for entry in resolver["entries"]:
        if entry["tag"] == tag:
            return entry
    return None

def get_tags_by_source(source_code: str) -> list:
    """
    Retorna todas as TAGs de uma fonte específica

    Args:

    Returns:
        Lista de dicts com tag e path
    """
    resolver = load_resolver()
    return [
        {"tag": e["tag"], "path": e["path"]}
        for e in resolver["entries"]
        if e.get("source") == source_code
    ]

def validate_tags(tags: list) -> dict:
    """
    Valida lista de TAGs

    Args:
        tags: Lista de TAGs

    Returns:
        Dict com valid (lista de TAGs encontradas) e invalid (não encontradas)
    """
    resolver = load_resolver()
    tag_set = set(resolver["tag_to_path"].keys())

    valid = []
    invalid = []

    for tag in tags:
        tag = tag.strip("[]")
        if tag in tag_set:
            valid.append(tag)
        else:
            invalid.append(tag)

    return {"valid": valid, "invalid": invalid}

# Funções de conveniência
def tag_exists(tag: str) -> bool:
    """Verifica se TAG existe no resolver"""
    return resolve_tag(tag) is not None

def get_absolute_path(tag: str, mega_brain_root: str = None) -> str | None:
    """Retorna path absoluto para uma TAG"""
    relative = resolve_tag(tag)
    if relative is None:
        return None

    if mega_brain_root is None:
        mega_brain_root = get_resolver_path().parent.parent

    return os.path.join(mega_brain_root, relative)

# Stats helpers
def get_stats() -> dict:
    """Retorna estatísticas do resolver"""
    return load_resolver()["stats"]

def get_orphan_tags() -> list:
    """Retorna TAGs que estão na planilha mas não têm arquivo"""
    return load_resolver()["orphan_tags"]

def get_duplicates() -> list:
    """Retorna TAGs duplicadas encontradas"""
    return load_resolver()["duplicates"]
```

### 3.2 Criar __init__.py

```bash
mkdir -p scripts/lib
touch scripts/lib/__init__.py
```

---

## PARTE 4: ATUALIZAR PLANILHA-INDEX.json

### 4.1 Script para Adicionar Campo Path

```python
#!/usr/bin/env python3
"""
Atualiza PLANILHA-INDEX.json com campo 'path' do TAG-RESOLVER
"""

import json
from pathlib import Path

MEGA_BRAIN = Path(".")
PLANILHA_PATH = MEGA_BRAIN / "PLANILHA-INDEX.json"
RESOLVER_PATH = MEGA_BRAIN / "knowledge" / "TAG-RESOLVER.json"

# Carregar arquivos
with open(RESOLVER_PATH) as f:
    resolver = json.load(f)

with open(PLANILHA_PATH) as f:
    planilha = json.load(f)

# Criar índice tag → path
tag_to_path = resolver["tag_to_path"]

# Atualizar entries
updated = 0
not_found = 0

for entry in planilha.get("entries", []):
    tag = entry.get("tag")
    if tag and tag in tag_to_path:
        entry["path"] = tag_to_path[tag]
        updated += 1
    else:
        entry["path"] = None
        not_found += 1

# Salvar
with open(PLANILHA_PATH, 'w', encoding='utf-8') as f:
    json.dump(planilha, f, indent=2, ensure_ascii=False)

print(f"PLANILHA-INDEX.json atualizada!")
print(f"  Entries com path: {updated}")
print(f"  Entries sem path: {not_found}")
```

---

## PRÓXIMO PASSO

Após completar esta parte, execute as instruções em:
**`INTEGRATION-POINTS.md`**

Isso conectará o TAG-RESOLVER aos scripts existentes da pipeline.
