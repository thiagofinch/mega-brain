"""
Speaker Gate — QG-SPEAKER-001
Validates presence of speaker labels in a text transcript.
Part of phase_0: PRE_VALIDATION in wf-ingest.yaml.
"""

import re
from pathlib import Path

LABEL_PATTERNS = [
    re.compile(r"^[A-ZÀ-Ú][a-zà-ú\s\-]{2,40}:\s", re.MULTILINE),  # "Nome Sobrenome: texto"
    re.compile(
        r"^\[?\d{1,2}:\d{2}\]?\s+[A-ZÀ-Ú][a-zà-ú\s]{2,30}:", re.MULTILINE
    ),  # "[00:00] Nome:"
    re.compile(r"^(Speaker\s+\d+|SPEAKER_\d+):", re.MULTILINE | re.IGNORECASE),  # "Speaker 1:"
]


def detect_speaker_labels(text: str) -> bool:
    """Returns True if text contains speaker labels."""
    for pattern in LABEL_PATTERNS:
        if pattern.search(text):
            return True
    return False


def validate_file(file_path: str) -> dict:
    """
    Validate a transcript file for speaker labels.
    Returns: {has_labels: bool, file: str, lines: int, sample: str}
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}", "has_labels": False}

    text = path.read_text(encoding="utf-8", errors="replace")
    has_labels = detect_speaker_labels(text)
    lines = text.count("\n")
    sample = text[:300].replace("\n", " ")

    return {
        "file": str(path.name),
        "has_labels": has_labels,
        "lines": lines,
        "sample": sample,
    }


def prompt_options(file_path: str) -> str:
    """
    Interactive prompt when no speaker labels found.
    Returns chosen action: 'monologue' | 'manual' | 'cancel'
    """
    name = Path(file_path).name
    print(f"\n[QG-SPEAKER-001] Nenhum label de speaker detectado em '{name}'")
    print("Este arquivo parece ter multiplas vozes sem identificacao.\n")
    print("Opcoes:")
    print("  1. Monologo — prosseguir sem labels (atribui tudo a fonte)")
    print("  2. Identificar participantes manualmente (informe os nomes)")
    print("  3. Cancelar ingestao")

    choice = input("\nEscolha [1/2/3]: ").strip()
    if choice == "1":
        return "monologue"
    elif choice == "2":
        return "manual"
    else:
        return "cancel"


def run_gate(file_path: str, auto_mode: bool = False) -> dict:
    """
    Run the speaker gate on a file.
    If auto_mode=True, returns result without prompting (for pipeline use).
    """
    result = validate_file(file_path)
    if result.get("error"):
        return result

    if result["has_labels"]:
        result["action"] = "pass"
        result["message"] = "Speaker labels detected — OK to ingest"
    else:
        if auto_mode:
            result["action"] = "block"
            result["message"] = "No speaker labels — blocked (auto_mode)"
        else:
            action = prompt_options(file_path)
            result["action"] = action
            result["message"] = f"User chose: {action}"

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python speaker_gate.py <transcript_file>")
        sys.exit(1)
    r = run_gate(sys.argv[1])
    print(r)
    sys.exit(0 if r.get("action") in ("pass", "monologue", "manual") else 1)
