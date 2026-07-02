#!/usr/bin/env python3
"""
Pipeline Merge Guard -- UserPromptSubmit hook
Warns when pipeline-mce is invoked for a slug that has pre-existing data.
Exit 0 always (warning only, never blocks).
"""

import json
import os
import re
import sys
from pathlib import Path


def main():
    try:
        raw = sys.stdin.read()
        if not raw:
            print(json.dumps({"continue": True}))
            sys.exit(0)

        hook_input = json.loads(raw)
        message = hook_input.get("message", "")

        # Only trigger on pipeline-mce related messages
        triggers = ["pipeline-mce", "/pipeline-mce", "processar fonte", "extrair dna"]
        if not any(t in message.lower() for t in triggers):
            print(json.dumps({"continue": True}))
            sys.exit(0)

        # Extract slug from message
        slug = None
        # Pattern: /pipeline-mce slug or /pipeline-mce --person slug
        m = re.search(r"pipeline-mce\s+(?:--person\s+)?(\S+)", message, re.IGNORECASE)
        if m:
            slug = m.group(1).lower().strip()

        if not slug:
            print(json.dumps({"continue": True}))
            sys.exit(0)

        # Quick scan for prior data
        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
        locations = []

        # Check by-person
        bp = project_dir / "knowledge" / "business" / "insights" / "by-person" / f"{slug}.md"
        if bp.exists() and bp.stat().st_size > 50:
            locations.append(f"by-person ({bp.stat().st_size} bytes)")

        # Check dossiers
        for bucket in ["business", "external"]:
            ddir = project_dir / "knowledge" / bucket / "dossiers" / "persons"
            if ddir.exists():
                for f in ddir.glob("DOSSIER-*.md"):
                    if slug.replace("-", "") in f.stem.lower().replace("-", ""):
                        locations.append(f"{bucket} dossier ({f.name})")

        # Check agents
        agent_dir = project_dir / "agents" / "external" / slug
        if agent_dir.exists() and any(agent_dir.iterdir()):
            locations.append(f"agent ({slug})")

        if locations:
            warning = (
                f"PRIOR DATA for '{slug}': {', '.join(locations)}. "
                f"Pipeline MUST run in brownfield mode (RULE 5)."
            )
            print(json.dumps({"continue": True, "feedback": warning}))
        else:
            print(json.dumps({"continue": True}))

        sys.exit(0)
    except Exception:
        print(json.dumps({"continue": True}))
        sys.exit(0)


if __name__ == "__main__":
    main()
