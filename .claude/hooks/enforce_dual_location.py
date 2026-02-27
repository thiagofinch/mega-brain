#!/usr/bin/env python3
"""
DUAL-LOCATION ENFORCEMENT HOOK - REGRA #8
==========================================
Garante que todo batch log existe em AMBOS os locais:
- /logs/batches/BATCH-XXX.md
- /.claude/mission-control/batch-logs/BATCH-XXX.json

Autor: JARVIS
Data: 2026-01-11
"""

import os
import re
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple

# Caminhos
BASE_PATH = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LOGS_MD = BASE_PATH / "logs" / "batches"
LOGS_JSON = BASE_PATH / ".claude" / "mission-control" / "batch-logs"
ENFORCEMENT_LOG = BASE_PATH / "logs" / "enforcement.jsonl"


def ensure_directories():
    """Garante que os diretórios existem."""
    LOGS_MD.mkdir(parents=True, exist_ok=True)
    LOGS_JSON.mkdir(parents=True, exist_ok=True)


def log_enforcement(action: str, batch_id: str, details: dict):
    """Registra ação de enforcement no log."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "batch_id": batch_id,
        "details": details
    }
    with open(ENFORCEMENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def extract_batch_id_from_filename(filename: str) -> Optional[str]:
    """
    Extrai o ID do batch do nome do arquivo.
    Suporta múltiplos formatos:
    - BATCH-050.md
    - BATCH-033-CG.json
    - BATCH-001-JEREMY-HAYNES-SOPS-20260104.md
    """
    # Tenta extrair número do batch
    match = re.search(r'BATCH[_-]?(\d+)', filename, re.IGNORECASE)
    if match:
        return match.group(1).zfill(3)  # Padroniza para 3 dígitos
    return None


def extract_metadata_from_md(md_path: Path) -> dict:
    """
    Extrai metadados do arquivo .md para criar .json.
    Faz parsing do formato visual do batch log.
    """
    content = md_path.read_text(encoding="utf-8")

    metadata = {
        "batch_id": "",
        "source": "",
        "timestamp": datetime.now().isoformat(),
        "status": "COMPLETE",
        "files_processed": 0,
        "files": [],
        "extraction_summary": {
            "filosofias": 0,
            "frameworks": 0,
            "heuristicas": 0,
            "metodologias": 0,
            "modelos_mentais": 0
        },
        "key_frameworks": [],
        "key_heuristicas": [],
        "key_filosofias": [],
        "key_metodologias": [],
        "auto_generated": True,
        "generated_from": str(md_path.name),
        "generated_at": datetime.now().isoformat()
    }

    # Extrai batch_id do nome do arquivo
    batch_match = re.search(r'BATCH[_-]?(\d+)', md_path.name, re.IGNORECASE)
    if batch_match:
        metadata["batch_id"] = f"BATCH-{batch_match.group(1).zfill(3)}"

    # Extrai SOURCE
    source_patterns = [
        r'SOURCE\s+([A-Z][A-Z\s\(\)\.]+)',
        r'FONTE\s+([A-Z][A-Z\s\(\)\.]+)',
        r'Source:\s*([^\n]+)',
        r'\|\s*SOURCE\s*\|\s*([^\|]+)',
    ]
    for pattern in source_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            metadata["source"] = match.group(1).strip()
            break

    # Se nao encontrou, tenta extrair do nome do arquivo dinamicamente
    if not metadata["source"]:
        # Extract source hint from filename by removing BATCH-XXX prefix and extension
        name_upper = md_path.stem.upper()
        # Remove BATCH-NNN- prefix
        source_hint = re.sub(r'^BATCH[_-]?\d+[_-]?', '', name_upper).strip('-_ ')
        if source_hint:
            # Convert dash/underscore separated name to readable form
            metadata["source"] = source_hint.replace('-', ' ').replace('_', ' ').strip()

    # Extrai metricas
    metrics_patterns = {
        "filosofias": r'Filosofias\s*[:\|]?\s*(\d+)',
        "frameworks": r'Frameworks?\s*[:\|]?\s*(\d+)',
        "heuristicas": r'Heur[ií]sticas?\s*[:\|]?\s*(\d+)',
        "metodologias": r'Metodologias?\s*[:\|]?\s*(\d+)',
        "modelos_mentais": r'Modelos?\s*Mentais?\s*[:\|]?\s*(\d+)'
    }

    for key, pattern in metrics_patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            metadata["extraction_summary"][key] = int(match.group(1))

    # Extrai arquivos processados da tabela
    table_pattern = r'\|\s*\d+\s*\|\s*([^\|]+)\s*\|'
    files = re.findall(table_pattern, content)
    metadata["files"] = [f.strip() for f in files if f.strip() and "Arquivo" not in f]
    metadata["files_processed"] = len(metadata["files"])

    # Extrai filosofias destaque
    filosofias_section = re.search(r'PHILOSOPHIES.*?```(.*?)```', content, re.DOTALL | re.IGNORECASE)
    if filosofias_section:
        filosofias = re.findall(r'"([^"]+)"', filosofias_section.group(1))
        metadata["key_filosofias"] = filosofias[:12]  # Limita a 12

    # Extrai frameworks
    frameworks_section = re.search(r'KEY FRAMEWORKS(.*?)(?:##|FILOSOFIAS|HEURISTICAS|```\s*\n\s*##)', content, re.DOTALL | re.IGNORECASE)
    if frameworks_section:
        # Busca nomes de frameworks entre boxes ASCII
        framework_names = re.findall(r'[\u2500-\u257F]\s*([A-Z][A-Za-z0-9\s\(\)\-]+?)\s*[\u2500-\u257F]', frameworks_section.group(1))
        if not framework_names:
            framework_names = re.findall(r'([A-Z][A-Z\s\-]+(?:Framework|Method|System|Model|Process))', frameworks_section.group(1), re.IGNORECASE)
        metadata["key_frameworks"] = list(set(framework_names))[:12]

    # Extrai heuristicas
    heuristicas_section = re.search(r'HEURISTICS.*?```(.*?)```', content, re.DOTALL | re.IGNORECASE)
    if heuristicas_section:
        heuristicas = re.findall(r'"([^"]+)"', heuristicas_section.group(1))
        metadata["key_heuristicas"] = [{"heuristica": h, "rating": 4} for h in heuristicas[:17]]

    return metadata


def create_json_from_md(batch_id: str, md_path: Path) -> bool:
    """Cria arquivo .json a partir do .md existente."""
    try:
        metadata = extract_metadata_from_md(md_path)

        # Determina o nome do arquivo JSON dynamically from source name
        source_code = ""
        source_upper = metadata["source"].upper().strip()
        if source_upper:
            # Generate short code from initials of source name words
            words = source_upper.replace('(', '').replace(')', '').replace('.', '').split()
            if len(words) == 1:
                source_code = f"-{words[0][:3]}"
            else:
                source_code = f"-{''.join(w[0] for w in words if w)}"

        json_filename = f"BATCH-{batch_id}{source_code}.json"
        json_path = LOGS_JSON / json_filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        log_enforcement("CREATE_JSON", batch_id, {
            "source_md": str(md_path.name),
            "created_json": json_filename,
            "files_processed": metadata["files_processed"]
        })

        return True

    except Exception as e:
        log_enforcement("ERROR_CREATE_JSON", batch_id, {
            "source_md": str(md_path.name),
            "error": str(e)
        })
        return False


def create_md_from_json(batch_id: str, json_path: Path) -> bool:
    """Cria arquivo .md minimo a partir do .json existente."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Gera markdown minimo
        source = data.get("source", "UNKNOWN")
        files_processed = data.get("files_processed", 0)
        timestamp = data.get("timestamp", datetime.now().isoformat())

        extraction = data.get("extraction_summary", {})
        filosofias = extraction.get("filosofias", 0)
        frameworks = extraction.get("frameworks", 0)
        heuristicas = extraction.get("heuristicas", 0)
        metodologias = extraction.get("metodologias", 0)
        modelos = extraction.get("modelos_mentais", 0)
        total = filosofias + frameworks + heuristicas + metodologias + modelos

        md_content = f"""# BATCH-{batch_id}

> **AUTO-GENERATED from JSON** - {datetime.now().strftime('%Y-%m-%d %H:%M')}
> Original JSON: {json_path.name}

## BATCH SUMMARY

| Campo | Valor |
|-------|-------|
| SOURCE | {source} |
| ARQUIVOS | {files_processed} |
| TIMESTAMP | {timestamp} |
| STATUS | {data.get('status', 'COMPLETE')} |

## METRICAS

| Camada | Quantidade |
|--------|------------|
| Filosofias | {filosofias} |
| Frameworks | {frameworks} |
| Heuristicas | {heuristicas} |
| Metodologias | {metodologias} |
| Modelos Mentais | {modelos} |
| **TOTAL** | **{total}** |

## ARQUIVOS PROCESSADOS

"""
        files = data.get("files", [])
        for i, f in enumerate(files, 1):
            md_content += f"| {i} | {f} |\n"

        if data.get("key_frameworks"):
            md_content += "\n## KEY FRAMEWORKS\n\n"
            for fw in data["key_frameworks"]:
                md_content += f"- {fw}\n"

        if data.get("key_filosofias"):
            md_content += "\n## FILOSOFIAS DESTAQUE\n\n"
            for fil in data["key_filosofias"]:
                md_content += f"- \"{fil}\"\n"

        md_content += f"""
---

```
AUTO-GENERATED BY DUAL-LOCATION ENFORCEMENT HOOK
JARVIS v3.33 | {datetime.now().strftime('%Y-%m-%d %H:%M')}
```
"""

        md_filename = f"BATCH-{batch_id}.md"
        md_path = LOGS_MD / md_filename

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        log_enforcement("CREATE_MD", batch_id, {
            "source_json": str(json_path.name),
            "created_md": md_filename
        })

        return True

    except Exception as e:
        log_enforcement("ERROR_CREATE_MD", batch_id, {
            "source_json": str(json_path.name),
            "error": str(e)
        })
        return False


def get_all_batches() -> Dict[str, Dict[str, Optional[Path]]]:
    """
    Coleta todos os batches de ambos os locais.
    Retorna dict: batch_id -> {"md": Path or None, "json": Path or None}
    """
    batches = {}

    # Coleta .md files
    if LOGS_MD.exists():
        for md_file in LOGS_MD.glob("BATCH-*.md"):
            batch_id = extract_batch_id_from_filename(md_file.name)
            if batch_id:
                if batch_id not in batches:
                    batches[batch_id] = {"md": None, "json": None}
                batches[batch_id]["md"] = md_file

    # Coleta .json files
    if LOGS_JSON.exists():
        for json_file in LOGS_JSON.glob("BATCH-*.json"):
            batch_id = extract_batch_id_from_filename(json_file.name)
            if batch_id:
                if batch_id not in batches:
                    batches[batch_id] = {"md": None, "json": None}
                batches[batch_id]["json"] = json_file

    return batches


def enforce_dual_location(batch_id: str) -> Tuple[bool, str]:
    """
    Garante que batch existe em ambos locais.
    Retorna (success, message)
    """
    # Busca arquivos existentes para este batch
    md_files = list(LOGS_MD.glob(f"BATCH-{batch_id}*.md")) + list(LOGS_MD.glob(f"BATCH-{batch_id.lstrip('0')}*.md"))
    json_files = list(LOGS_JSON.glob(f"BATCH-{batch_id}*.json")) + list(LOGS_JSON.glob(f"BATCH-{batch_id.lstrip('0')}*.json"))

    md_exists = len(md_files) > 0
    json_exists = len(json_files) > 0

    if md_exists and json_exists:
        return True, f"BATCH-{batch_id}: Dual-location OK"

    if md_exists and not json_exists:
        success = create_json_from_md(batch_id, md_files[0])
        if success:
            return True, f"BATCH-{batch_id}: JSON criado a partir de MD"
        return False, f"BATCH-{batch_id}: ERRO ao criar JSON"

    if json_exists and not md_exists:
        success = create_md_from_json(batch_id, json_files[0])
        if success:
            return True, f"BATCH-{batch_id}: MD criado a partir de JSON"
        return False, f"BATCH-{batch_id}: ERRO ao criar MD"

    return False, f"BATCH-{batch_id}: Nao encontrado em nenhum local"


def enforce_single_batch(batch_id: str) -> dict:
    """
    Enforça dual-location para um batch especifico.
    Usado como hook apos criar batch.
    """
    ensure_directories()
    success, message = enforce_dual_location(batch_id)

    result = {
        "batch_id": batch_id,
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

    return result


def main():
    """
    Verifica TODOS os batches e enforça dual-location.
    Gera relatorio completo.
    """
    ensure_directories()

    print("=" * 70)
    print(" DUAL-LOCATION ENFORCEMENT HOOK - REGRA #8")
    print(" Verificando todos os batches...")
    print("=" * 70)
    print()

    batches = get_all_batches()

    stats = {
        "total": len(batches),
        "complete": 0,
        "md_only": 0,
        "json_only": 0,
        "created_json": 0,
        "created_md": 0,
        "errors": 0
    }

    # Ordena por numero do batch
    sorted_batches = sorted(batches.items(), key=lambda x: int(x[0]))

    for batch_id, paths in sorted_batches:
        md_exists = paths["md"] is not None
        json_exists = paths["json"] is not None

        if md_exists and json_exists:
            stats["complete"] += 1
            status = "OK"
        elif md_exists and not json_exists:
            stats["md_only"] += 1
            # Tenta criar JSON
            success = create_json_from_md(batch_id, paths["md"])
            if success:
                stats["created_json"] += 1
                status = "CREATED JSON"
            else:
                stats["errors"] += 1
                status = "ERROR"
        elif json_exists and not md_exists:
            stats["json_only"] += 1
            # Tenta criar MD
            success = create_md_from_json(batch_id, paths["json"])
            if success:
                stats["created_md"] += 1
                status = "CREATED MD"
            else:
                stats["errors"] += 1
                status = "ERROR"
        else:
            status = "MISSING"
            stats["errors"] += 1

        # Output visual
        md_icon = "+" if md_exists or status == "CREATED MD" else "X"
        json_icon = "+" if json_exists or status == "CREATED JSON" else "X"
        print(f"  BATCH-{batch_id}: [MD:{md_icon}] [JSON:{json_icon}] -> {status}")

    # Sumario
    print()
    print("=" * 70)
    print(" SUMARIO")
    print("=" * 70)
    print(f"  Total de batches:        {stats['total']}")
    print(f"  Ja completos:            {stats['complete']}")
    print(f"  Apenas MD:               {stats['md_only']}")
    print(f"  Apenas JSON:             {stats['json_only']}")
    print(f"  JSONs criados:           {stats['created_json']}")
    print(f"  MDs criados:             {stats['created_md']}")
    print(f"  Erros:                   {stats['errors']}")
    print()

    final_complete = stats['complete'] + stats['created_json'] + stats['created_md']
    compliance = (final_complete / stats['total'] * 100) if stats['total'] > 0 else 0

    print(f"  COMPLIANCE FINAL:        {final_complete}/{stats['total']} ({compliance:.1f}%)")
    print()
    print(f"  Log salvo em: {ENFORCEMENT_LOG}")
    print("=" * 70)

    # Log final
    log_enforcement("FULL_SCAN", "ALL", {
        "stats": stats,
        "compliance": compliance
    })

    return stats


def hook_main():
    """
    Hook entry point for Claude Code PostToolUse event.
    Reads JSON from stdin, outputs JSON to stdout.
    Triggers dual-location enforcement when a batch file is written.
    """
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}

        tool_input = hook_input.get('tool_input', {})
        file_path = tool_input.get('file_path', '')

        # Only trigger for batch files
        if 'BATCH' not in file_path.upper():
            print(json.dumps({'continue': True}))
            return

        # Extract batch ID from path
        batch_id = extract_batch_id_from_filename(Path(file_path).name)
        if not batch_id:
            print(json.dumps({'continue': True}))
            return

        ensure_directories()
        success, message = enforce_dual_location(batch_id)

        feedback = f"[REGRA #8] {message}" if success else None
        print(json.dumps({'continue': True, 'feedback': feedback}))

    except Exception:
        print(json.dumps({'continue': True}))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        main()
    else:
        hook_main()
