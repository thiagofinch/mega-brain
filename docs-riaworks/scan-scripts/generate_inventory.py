"""
File Inventory Generator for Security Audit
Generates SHA256 hashes for all files in the repository.
Authorized by repository owner for security audit purposes.
"""
import hashlib, json, os
from datetime import datetime

inventory = []
base = r'C:\__thiago\mega-brain'

for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d != '.git' and d != 'node_modules']
    for f in files:
        path = os.path.join(root, f)
        rel_path = os.path.relpath(path, base).replace('\\', '/')
        try:
            size = os.path.getsize(path)
            with open(path, 'rb') as fh:
                sha256 = hashlib.sha256(fh.read()).hexdigest()
            inventory.append({"file": rel_path, "sha256": sha256, "size": size})
        except Exception as e:
            inventory.append({"file": rel_path, "sha256": "ERROR", "size": -1, "error": str(e)})

output = {
    "total_files": len(inventory),
    "generated_at": datetime.now().isoformat(),
    "purpose": "Security audit file inventory",
    "inventory": sorted(inventory, key=lambda x: x["file"])
}

out_path = os.path.join(base, 'docs-riaworks', 'file-inventory.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Inventory complete: {len(inventory)} files written to {out_path}")
