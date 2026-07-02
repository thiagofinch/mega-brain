"""
Bucket Isolation Guard — PreToolUse guard for cross-bucket writes.
Warns when writing expert content to business bucket or vice versa.
Constitution Art. XIII enforcement.
Exit codes: 0=allow, 1=warn, 2=block
"""

import json
import os
import sys

BUCKET_PATTERNS = {
    "external": ["knowledge/external/", "agents/external/"],
    "business": ["knowledge/business/", "agents/business/"],
    "personal": ["knowledge/personal/", "agents/personal/"],
}


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

        # Detect which bucket the file belongs to
        target_bucket = None
        for bucket, patterns in BUCKET_PATTERNS.items():
            for pattern in patterns:
                if rel_path.startswith(pattern):
                    target_bucket = bucket
                    break

        if not target_bucket:
            sys.exit(0)

        # Check content for cross-bucket references (heuristic)
        content = tool_input.get("content", "") or tool_input.get("new_string", "")
        if not content:
            sys.exit(0)

        cross_refs = []
        for bucket, patterns in BUCKET_PATTERNS.items():
            if bucket == target_bucket:
                continue
            for pattern in patterns:
                if pattern in content:
                    cross_refs.append(f"{bucket} ({pattern})")

        if cross_refs:
            print(
                json.dumps(
                    {
                        "warning": (
                            f"Cross-bucket reference detected. Writing to '{target_bucket}' bucket "
                            f"but content references: {', '.join(cross_refs)}. "
                            f"Constitution Art. XIII requires bucket isolation. "
                            f"Verify this is intentional (e.g., cross-reference, not data leak)."
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
