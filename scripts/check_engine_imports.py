#!/usr/bin/env python3
"""Gate de integridade dos imports da engine (roda no CI e localmente).

Duas checagens, sem rede e sem gravar no repositório:

1. Estática (AST): todo .py de engine/, .claude/, scripts/ e bin/ precisa
   compilar na versão de Python em uso (o README exige 3.11+), e todo
   ``import engine.<modulo>`` / ``from engine.<modulo> import y`` precisa apontar para um
   módulo que existe no repositório. Imports dentro de um ``try`` que trata
   ImportError são opcionais por desenho e ficam de fora.
2. Smoke: importa cada módulo de engine/ num subprocesso isolado. Arquivos
   com nome que não é identificador Python (ex.: pasta com hífen) são scripts
   e são pulados. Falta de pacote de terceiros (ex.: numpy, que só a voz usa)
   é listada à parte e não reprova: o gate cobre o que a release distribui.

Usage:
    python3 scripts/check_engine_imports.py               # as duas checagens
    python3 scripts/check_engine_imports.py --static-only # só a estática

Saída 0 = tudo importa; 1 = há falhas (listadas no stdout).
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIRS = ("engine", ".claude", "scripts", "bin")
IMPORT_ERRORS = {"ImportError", "ModuleNotFoundError", "Exception", "BaseException"}
MISSING_MODULE_RE = re.compile(r"ModuleNotFoundError: No module named '([^']+)'")
SMOKE_TIMEOUT = 120


def module_exists(name: str) -> bool:
    rel = Path(*name.split("."))
    return (ROOT / rel).with_suffix(".py").is_file() or (ROOT / rel / "__init__.py").is_file()


def _handles_import_error(node: ast.Try) -> bool:
    for handler in node.handlers:
        if handler.type is None:
            return True
        types = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
        if any(isinstance(t, ast.Name) and t.id in IMPORT_ERRORS for t in types):
            return True
    return False


def _engine_imports(tree: ast.AST):
    """Yield (lineno, module) for unguarded engine.* imports."""

    def walk(node: ast.AST, guarded: bool):
        if isinstance(node, ast.Try):
            inner = guarded or _handles_import_error(node)
            for child in node.body:
                yield from walk(child, inner)
            for child in node.handlers + node.orelse + node.finalbody:
                yield from walk(child, guarded)
            return
        if not guarded:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "engine" or alias.name.startswith("engine."):
                        yield node.lineno, alias.name
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                if node.module == "engine" or node.module.startswith("engine."):
                    yield node.lineno, node.module
        for child in ast.iter_child_nodes(node):
            yield from walk(child, guarded)

    yield from walk(tree, False)


def static_check() -> list[str]:
    failures = []
    for base in STATIC_DIRS:
        for path in sorted((ROOT / base).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
            except SyntaxError as exc:
                failures.append(f"{rel}:{exc.lineno}: SyntaxError: {exc.msg}")
                continue
            for lineno, module in _engine_imports(tree):
                if not module_exists(module):
                    failures.append(f"{rel}:{lineno}: módulo inexistente {module}")
    return failures


def _engine_modules() -> tuple[list[str], list[str]]:
    modules, skipped = [], []
    for path in sorted((ROOT / "engine").rglob("*.py")):
        parts = list(path.relative_to(ROOT).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if all(p.isidentifier() for p in parts):
            modules.append(".".join(parts))
        else:
            skipped.append(path.relative_to(ROOT).as_posix())
    return modules, skipped


def _external_package(error_line: str) -> str | None:
    """Nome do pacote de terceiros ausente, ou None se o erro não for esse."""
    match = MISSING_MODULE_RE.match(error_line)
    if not match:
        return None
    top = match.group(1).split(".")[0]
    if (ROOT / top).is_dir() or (ROOT / f"{top}.py").is_file():
        return None  # módulo do próprio repositório: é falha da release
    return top


def _import_one(module: str) -> tuple[str, str] | None:
    """None se importa; ("externo", pacote) ou ("falha", mensagem) se não."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    try:
        proc = subprocess.run(
            [sys.executable, "-B", "-c", "import importlib, sys; importlib.import_module(sys.argv[1])", module],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=SMOKE_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return "falha", f"{module}: timeout ({SMOKE_TIMEOUT}s)"
    if proc.returncode == 0:
        return None
    last = (proc.stderr.strip().splitlines() or ["(sem stderr)"])[-1]
    package = _external_package(last)
    if package:
        return "externo", package
    return "falha", f"{module}: {last}"


def smoke_check() -> tuple[list[str], Counter, int, list[str]]:
    modules, skipped = _engine_modules()
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        results = [r for r in pool.map(_import_one, modules) if r]
    failures = [msg for kind, msg in results if kind == "falha"]
    external = Counter(pkg for kind, pkg in results if kind == "externo")
    return failures, external, len(modules), skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--static-only", action="store_true", help="pula o smoke de import")
    args = parser.parse_args()

    failures = static_check()
    print(f"[estática] {len(failures)} problema(s): sintaxe inválida ou import de módulo inexistente")
    for line in failures:
        print(f"  {line}")

    if not args.static_only:
        smoke, external, total, skipped = smoke_check()
        ok = total - len(smoke) - sum(external.values())
        print(f"[smoke] {ok}/{total} módulos importam ({len(skipped)} scripts pulados)")
        if external:
            deps = ", ".join(f"{pkg} ({n})" for pkg, n in external.most_common())
            print(f"[smoke] {sum(external.values())} dependem de pacote opcional não instalado: {deps}")
        for line in smoke:
            print(f"  {line}")
        failures += smoke

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
