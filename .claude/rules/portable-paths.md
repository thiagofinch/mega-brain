# Portable Paths

Applies to any repo-authored artifact: rules, skills, templates, checklists, squads, scripts, docs and generated outputs committed to the repository.

## Non-Negotiable Rule

**Never commit machine-specific absolute paths.**

Forbidden examples:
- `/Users/<user>/project/...`
- `/home/<user>/project/...`
- `C:\Users\<user>\project\...`
- `file:///Users/<user>/project/...`

These paths are not part of the product. They are local machine state.

## What To Use Instead

### Inside the Repository

Use repo-relative paths:
- `squads/squad-creator/config.yaml`
- `mega-brain-core/product/checklists/pre-push-checklist.md`
- `workspace/businesses/mega-brain/L2-tactical/...`
- `outputs/traceability/...`

### In Scripts

Resolve paths at runtime:
- `$CLAUDE_PROJECT_DIR`
- `$PROJECT_ROOT`
- `$PWD`
- `$(git rev-parse --show-toplevel)`
- `path.resolve(...)`
- `__dirname` / `import.meta.url`

### In Examples and Documentation

Use portable placeholders:
- `/path/to/file.ext`
- `<repo-root>/squads/...`
- `~/Movies/video.mp4`
- `${WHISPER_CPP_CLI}`
- `${WHISPER_CPP_MODEL}`

## Generated Artifact Rule

Generated YAML/Markdown committed to the repo MUST also be portable.

If an artifact references something inside this repository, it must use:
- repo-relative paths, or
- a symbolic placeholder such as `<repo-root>`

It must NOT embed the author machine path.

## Enforcement

Validation command:

```bash
npm run validate:paths
```

CI must block when this validator finds:
- repo-root leaks
- local user home paths
- machine-specific `file://` URLs

## Migration Principle

Historical archives may still contain old absolute paths.
That is not permission to add new ones.

Rule:
1. No new machine-specific absolute paths.
2. Any touched file with such a path should be normalized as part of the edit.
