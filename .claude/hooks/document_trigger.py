#!/usr/bin/env python3
"""
Document Trigger - No-op placeholder.

This file exists solely to prevent a "file not found" error from a cached
hook reference that could not be located in any active settings file.

If you find the source of this hook reference, you may safely delete this file
after removing that reference.

Hook Type: UserPromptSubmit (presumed)
"""

import json
import sys


def main():
    try:
        sys.stdin.read()
    except Exception:
        pass
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
