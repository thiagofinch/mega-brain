# TASK: Compose Workflow from Modules
# ID: HO-TP-COMPOSE-001

> **Version:** 1.0.0
> **Category:** ORCHESTRATION
> **Input:** Composition YAML definition
> **Output:** Executable workflow with validated module chain

---

## Purpose

Takes a composition definition (sequential, parallel, or conditional) and resolves it into an executable workflow by:

1. Loading referenced modules from the registry
2. Validating input/output compatibility between chained modules
3. Checking all dependencies are satisfied
4. Producing a resolved execution plan

---

## Steps

### Step 1: Parse Composition

```
INPUT: composition.yaml
OUTPUT: Parsed composition object with module references

ACTIONS:
- Read composition YAML
- Validate against composition schema
- Extract module IDs and their input mappings
```

### Step 2: Resolve Modules

```
INPUT: List of module IDs
OUTPUT: Loaded module definitions

ACTIONS:
- Load MODULE-REGISTRY.yaml
- For each module ID:
  - Verify module exists in registry
  - Verify module status is ACTIVE
  - Load full module definition from path
  - Verify module version compatibility
```

### Step 3: Validate Chain

```
INPUT: Ordered list of module definitions with input mappings
OUTPUT: Validation report

ACTIONS:
- For each module transition (A -> B):
  - Verify A's outputs satisfy B's required inputs
  - Type-check output->input mappings
  - Verify schema compatibility where declared
- Flag any type mismatches or missing inputs
```

### Step 4: Check Dependencies

```
INPUT: All module definitions
OUTPUT: Dependency satisfaction report

ACTIONS:
- Build dependency graph from all modules
- Detect circular dependencies (FAIL if found)
- Verify all external dependencies available
- Order parallel branches by dependency
```

### Step 5: Generate Execution Plan

```
INPUT: Validated composition + resolved modules
OUTPUT: Execution plan with checkpoints

ACTIONS:
- Assign execution order
- Insert quality gates between modules
- Add checkpoint saves at configurable intervals
- Generate rollback points for each module
```

---

## Quality Gate

```
CONDITIONS:
- All modules resolved successfully
- Zero type mismatches in chain
- Zero circular dependencies
- All required inputs satisfied

ON_FAILURE: HALT
```

---

## Error Handling

| Error | Action |
|-------|--------|
| Module not found in registry | HALT with missing module ID |
| Type mismatch between modules | HALT with details of incompatible types |
| Circular dependency | HALT with cycle path |
| Module version conflict | WARN and use latest compatible |

---

*Task: compose-workflow v1.0.0 -- Mega Brain*
