# Governance Rules

Applies to all files in the repository.

## Business Context

This repository serves a single organization as a single-business spoke. There are no cross-business operations, shared products, or multi-founder approval flows within this repository.

## CODEOWNERS Enforcement

- All changes require owner review (the repository owner)
- Framework core paths (`core/`, `agents/development/`, `agents/ecosystem/`, `constitution.md`) require explicit review
- See `.github/CODEOWNERS` for the authoritative path-to-owner mapping

## Workspace Isolation

- Business data lives in `workspace/businesses/{bu}/`
- Domain definitions live in `workspace/domains/`
- System configuration lives in `workspace/_system/`
- Workspace documents are YAML format

## Package Publishing

- Semantic versioning: major for breaking, minor for features, patch for fixes
- Release via git tags (v*)
