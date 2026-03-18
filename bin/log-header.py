#!/usr/bin/env python3
"""
bin/log-header.py — Colored ASCII log headers for Mega Brain 3D

Prints branded headers with ANSI colors for terminal display.
Works natively in any terminal that supports ANSI escape codes.

Usage:
    python3 bin/log-header.py workspace          # Red business header
    python3 bin/log-header.py personal           # Green personal header
    python3 bin/log-header.py workspace --name ACME
    python3 bin/log-header.py personal --no-color # Without ANSI codes
"""
import os
import sys

# ── ANSI Color Codes ────────────────────────────────────────────
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
WHITE_ON_RED = "\033[1;97;41m"
WHITE_ON_GREEN = "\033[1;97;42m"
RESET = "\033[0m"


def _get_company_short_name(override: str | None = None) -> str:
    """Extract smart abbreviation from company name."""
    if override:
        return override.upper()

    full_name = os.getenv("READ_AI_COMPANY_NAME", "").strip()
    if not full_name:
        return "EMPRESA"

    # Smart abbreviation rules:
    # - 1 word: use as-is → "Acme" → "ACME"
    # - 2+ words: first word → "Mega Brain AI" → "MEGA"
    # - Contains LTDA/SA/ME/LLC: strip suffix, use first word
    parts = full_name.upper().split()
    suffixes = {"LTDA", "SA", "S.A.", "ME", "MEI", "LLC", "INC", "CORP", "LTD", "EIRELI"}
    parts = [p for p in parts if p not in suffixes]

    if len(parts) <= 1:
        return parts[0] if parts else "EMPRESA"
    return parts[0]


def _no_color(text: str) -> str:
    """Strip ANSI codes for --no-color mode."""
    import re
    return re.sub(r"\033\[[0-9;]*m", "", text)


def workspace_header(name: str) -> str:
    R = RED
    E = RESET
    WR = WHITE_ON_RED
    return f"""{R}╔══════════════════════════════════════════════════════════════════════════════╗{E}
{R}║                                                                              ║{E}
{R}║   ██████╗ ██╗   ██╗███████╗██╗███╗   ██╗███████╗███████╗███████╗            ║{E}
{R}║   ██╔══██╗██║   ██║██╔════╝██║████╗  ██║██╔════╝██╔════╝██╔════╝            ║{E}
{R}║   ██████╔╝██║   ██║███████╗██║██╔██╗ ██║█████╗  ███████╗███████╗            ║{E}
{R}║   ██╔══██╗██║   ██║╚════██║██║██║╚██╗██║██╔══╝  ╚════██║╚════██║            ║{E}
{R}║   ██████╔╝╚██████╔╝███████║██║██║ ╚████║███████╗███████║███████║            ║{E}
{R}║   ╚═════╝  ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝            ║{E}
{R}║                                                                              ║{E}
{R}║{E}   {WR} {name} {E} {R}— WORKSPACE LOG{E}                                       {R}║{E}
{R}║{E}   Bucket 2 | Business Intelligence                                    {R}║{E}
{R}║                                                                              ║{E}
{R}╚══════════════════════════════════════════════════════════════════════════════╝{E}"""


def personal_header() -> str:
    G = GREEN
    E = RESET
    WG = WHITE_ON_GREEN
    Y = YELLOW
    return f"""{G}╔══════════════════════════════════════════════════════════════════════════════╗{E}
{G}║                                                                              ║{E}
{G}║   ███████╗███████╗██╗   ██╗                                                  ║{E}
{G}║   ██╔════╝██╔════╝██║   ██║                                                  ║{E}
{G}║   ███████╗█████╗  ██║   ██║                                                  ║{E}
{G}║   ╚════██║██╔══╝  ██║   ██║                                                  ║{E}
{G}║   ███████║███████╗╚██████╔╝                                                  ║{E}
{G}║   ╚══════╝╚══════╝ ╚═════╝                                                   ║{E}
{G}║                                                                              ║{E}
{G}║    ██████╗███████╗██████╗ ███████╗██████╗ ██████╗  ██████╗                   ║{E}
{G}║   ██╔════╝██╔════╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔═══██╗                  ║{E}
{G}║   ██║     █████╗  ██████╔╝█████╗  ██████╔╝██████╔╝██║   ██║                  ║{E}
{G}║   ██║     ██╔══╝  ██╔══██╗██╔══╝  ██╔══██╗██╔══██╗██║   ██║                  ║{E}
{G}║   ╚██████╗███████╗██║  ██║███████╗██████╔╝██║  ██║╚██████╔╝                  ║{E}
{G}║    ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝                   ║{E}
{G}║                                                                              ║{E}
{G}║{E}   {WG} SEU CÉREBRO {E} {G}— PERSONAL LOG{E}                                  {G}║{E}
{G}║{E}   Bucket 3 | Cognitive Layer | {Y}L3 EXCLUSIVO{E}                           {G}║{E}
{G}║                                                                              ║{E}
{G}║{E}   {Y}⚠️  DOCUMENTO CONFIDENCIAL — NUNCA exposto em L1/L2{E}                  {G}║{E}
{G}║                                                                              ║{E}
{G}╚══════════════════════════════════════════════════════════════════════════════╝{E}"""


def main():
    args = sys.argv[1:]
    no_color = "--no-color" in args
    args = [a for a in args if a != "--no-color"]

    name_override = None
    if "--name" in args:
        idx = args.index("--name")
        if idx + 1 < len(args):
            name_override = args[idx + 1]
            args = [a for a in args if a != "--name" and a != name_override]

    if not args or args[0] not in ("workspace", "personal"):
        print("Usage: python3 bin/log-header.py [workspace|personal] [--name NAME] [--no-color]")
        sys.exit(1)

    bucket = args[0]

    if bucket == "workspace":
        name = _get_company_short_name(name_override)
        output = workspace_header(name)
    else:
        output = personal_header()

    if no_color:
        output = _no_color(output)

    print(output)


if __name__ == "__main__":
    main()
