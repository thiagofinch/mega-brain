---
wave: 1
depends_on: []
files_modified:
  - artifacts/insights/INSIGHTS-STATE.json
requirements:
  - DATA-01
---

# Plan: Repair INSIGHTS-STATE.json

## Problem

INSIGHTS-STATE.json has a trailing comma on line 2181 causing JSON parse failure:
```
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 2181 column 9
```

The issue: `"priority": "MEDIUM",` followed by `},` - trailing comma after last property.

## Solution

1. Read the file content
2. Use regex to find and fix trailing commas before `}`
3. Validate the repaired JSON with `json.loads()`
4. Write back the corrected file

## Implementation

```python
import json
import re
from pathlib import Path

file_path = Path("artifacts/insights/INSIGHTS-STATE.json")
content = file_path.read_text()

# Fix trailing commas: ",\s*}" → "}"
fixed = re.sub(r',(\s*[}\]])', r'\1', content)

# Validate
json.loads(fixed)

# Write back
file_path.write_text(fixed)
```

## Verification

```bash
python3 -c "import json; json.load(open('artifacts/insights/INSIGHTS-STATE.json')); print('OK')"
```

## Rollback

Backup created before modification: `INSIGHTS-STATE.json.bak`
