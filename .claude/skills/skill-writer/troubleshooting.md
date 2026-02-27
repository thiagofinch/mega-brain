# Troubleshooting Skills

Common issues and solutions when creating or debugging Skills.

## Skill doesn't activate

**Symptoms**: Claude doesn't use your Skill when you expect it to.

**Solutions**:

1. **Make description more specific**
   ```yaml
   # Before (too vague)
   description: Helps with documents

   # After (specific triggers)
   description: Extract text from PDF files. Use when working with PDFs or document extraction.
   ```

2. **Include trigger words users would say**
   - Add file extensions: `.pdf`, `.xlsx`, `.json`
   - Add action verbs: "analyze", "extract", "generate", "create"
   - Add context: "Use when...", "For..."

3. **Check the "Use when" clause**
   ```yaml
   description: [What it does]. Use when [specific scenario].
   ```

## Skill not found

**Symptoms**: Skill doesn't appear in available skills list.

**Check**:

1. **File location**
   ```bash
   # Personal skills
   ls ~/.claude/skills/skill-name/SKILL.md

   # Project skills
   ls .claude/skills/skill-name/SKILL.md
   ```

2. **Directory name matches frontmatter**
   ```
   Folder: skill-name/
   Frontmatter: name: skill-name  # Must match exactly
   ```

3. **SKILL.md filename** (case-sensitive)
   - Correct: `SKILL.md`
   - Wrong: `skill.md`, `Skill.md`

## YAML parsing errors

**Symptoms**: Skill fails to load or behaves unexpectedly.

**Check**:

1. **No tabs in YAML** (spaces only)
   ```yaml
   # Wrong (tabs)
   name:	skill-name

   # Correct (spaces)
   name: skill-name
   ```

2. **Frontmatter delimiters**
   ```yaml
   ---              # Line 1 (no blank lines before)
   name: skill-name
   description: ...
   ---              # Closing delimiter

   # Content starts here
   ```

3. **Validate YAML**
   ```bash
   head -n 10 SKILL.md
   ```

## Multiple Skills conflict

**Symptoms**: Wrong Skill activates, or Skills interfere.

**Solutions**:

1. **Make descriptions more distinct**
   ```yaml
   # Skill A
   description: Extract text from PDFs...

   # Skill B
   description: Create PDF reports from data...
   ```

2. **Use different trigger words**

3. **Narrow scope of each Skill**
   - One Skill = one capability
   - Split broad Skills into focused ones

## Skill has runtime errors

**Symptoms**: Skill loads but fails during execution.

**Check**:

1. **Script permissions**
   ```bash
   chmod +x scripts/*.py
   ```

2. **Dependencies installed**
   ```bash
   pip install -r requirements.txt
   ```

3. **File paths use forward slashes**
   ```yaml
   # Correct
   python scripts/helper.py

   # Wrong (Windows backslashes)
   python scripts\helper.py
   ```

4. **Relative paths from skill directory**
   ```yaml
   # From SKILL.md, reference sibling files
   See [examples.md](examples.md)
   Run: python scripts/validate.py
   ```

## Debug mode

Run Claude Code with debug output:

```bash
claude --debug
```

This shows:
- Which Skills are loaded
- Why Skills activate or don't
- Any parsing errors

## Common mistakes

### 1. Name mismatch

```
Folder: my-skill/
Frontmatter: name: myskill  # Wrong - doesn't match
```

### 2. Description too vague

```yaml
description: Utility for files  # Won't trigger
```

### 3. Missing "Use when" context

```yaml
# Missing context
description: Extracts data from spreadsheets

# Better
description: Extracts data from spreadsheets. Use when working with Excel or CSV files.
```

### 4. Nested file references

```markdown
# Avoid deep nesting
SKILL.md → advanced.md → details.md → more.md

# Keep it flat
SKILL.md → reference.md
SKILL.md → examples.md
```

### 5. Tabs in YAML

YAML requires spaces. Tabs cause silent failures.

## Validation commands

```bash
# Check file exists
ls .claude/skills/skill-name/SKILL.md

# View frontmatter
head -n 10 .claude/skills/skill-name/SKILL.md

# Check for tabs (should return nothing)
grep -P '\t' .claude/skills/skill-name/SKILL.md

# Restart Claude to reload skills
# (Exit and relaunch Claude Code)
```
