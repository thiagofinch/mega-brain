"""
Constitution Gate — PreToolUse guard for constitution.md writes.
Blocks direct writes to mega-brain-core/constitution.md without amendment process.
Exit codes: 0=allow, 1=warn, 2=block
"""

import json
import os
import sys


def main():
    try:
        input_data = json.loads(sys.stdin.read())
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if tool_name not in ("Write", "Edit"):
            sys.exit(0)

        file_path = tool_input.get("file_path", "")
        project_root = os.environ.get("CLAUDE_PROJECT_DIR", "")

        if not file_path:
            sys.exit(0)

        rel_path = file_path.replace(project_root + "/", "") if project_root else file_path

        if "constitution.md" in rel_path.lower() and "mega-brain-core/" in rel_path:
            print(
                json.dumps(
                    {
                        "warning": (
                            "Constitution amendment detected. "
                            "Ensure this follows the amendment process: "
                            "PR + @architect review + @po approval + version bump. "
                            "Constitution Art. I-XIV are foundational law."
                        )
                    }
                )
            )
            sys.exit(1)

        sys.exit(0)

    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
