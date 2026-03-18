# Frontend Design Skill

> **Auto-Trigger:** Quando usuário pedir UI, interface, design, frontend, componente visual, layout, CSS, styling
> **Keywords:** "frontend", "UI", "interface", "design", "componente", "visual", "CSS", "layout", "styling", "theme", "aesthetics"
> **Prioridade:** ALTA
> **Namespace:** [OFFICIAL]
> **Tools:** Read, Write, Edit, Glob, Grep, Bash

## Quando NÃO Ativar

- Tarefas puramente de backend/API sem componente visual
- Discussões sobre arquitetura de dados
- Debugging de lógica de negócio sem UI envolvida
- Quando usuário explicitamente pedir skill diferente

---

## Core Purpose

Creating distinctive, production-grade frontend interfaces with high design quality.
Guides developers in building **creative, polished code that avoids generic AI aesthetics.**

---

## Design Thinking Framework

Before implementation, establish context across these four areas:

### 1. Purpose & Audience
Identify what problem the interface solves and who uses it. Understanding the user context shapes every design decision.

### 2. Aesthetic Tone
Commit to a clear direction:
- Minimalist
- Maximalist
- Retro
- Brutalist
- Art Deco
- Glassmorphism
- Neomorphism
- Custom/Hybrid

### 3. Technical Constraints
Consider framework requirements, performance targets, and accessibility standards before diving into implementation.

### 4. Differentiation
What makes this design memorable? Identify the unique elements that will set this interface apart.

---

## Frontend Aesthetics Priorities

### Typography
Distinctive choices that elevate aesthetics.

**AVOID:** Inter, Roboto, Arial, system fonts (overused, generic)

**PREFER:** Purposeful font selections that match the aesthetic tone. Consider:
- Display fonts for headers
- Readable body fonts with character
- Variable fonts for flexibility

### Color & Theme
Cohesive palettes with dominant colors and sharp accents.

- Establish a clear primary color
- Use accent colors intentionally
- Consider dark/light mode from the start
- Avoid the "safe blue" default palette

### Motion
CSS animations with high-impact moments over scattered micro-interactions.

- Purposeful entrance animations
- Meaningful state transitions
- Avoid animation for animation's sake
- Consider reduced-motion preferences

### Spatial Composition
Embrace asymmetry, overlap, and grid-breaking elements.

- Break out of standard 12-column monotony
- Use negative space intentionally
- Layer elements for depth
- Consider viewport-relative sizing

### Visual Details
Atmosphere through gradients, textures, and contextual effects.

- Subtle gradients over flat colors
- Texture overlays for depth
- Contextual shadows and glows
- Micro-details that reward attention

---

## Key Warnings

### What to AVOID

- Overused font families (Inter, Roboto, Arial)
- Clichéd color schemes (corporate blue, startup teal)
- Predictable layouts (centered hero, 3-column features)
- Cookie-cutter design patterns
- Generic component libraries without customization
- "Safe" design choices that blend in

### Complexity Matching

Match code complexity to aesthetic vision:
- **Minimalist designs:** Clean, efficient code with elegant simplicity
- **Maximalist designs:** Elaborate implementations with rich detail layers

---

## Implementation Guidelines

### Before Writing Code

1. **Sketch the vision** - Even mentally, know what you're building
2. **Identify hero elements** - What draws the eye first?
3. **Plan the hierarchy** - Visual importance should be clear
4. **Consider states** - Hover, active, loading, error, empty

### During Implementation

1. **Start with structure** - HTML semantics matter
2. **Build mobile-first** - Responsive by default
3. **Layer styles progressively** - Base → Theme → Variations
4. **Test in context** - Components rarely exist alone

### Code Quality

- Use CSS custom properties for theming
- Implement proper accessibility (ARIA, focus states)
- Optimize for performance (lazy loading, efficient animations)
- Document design decisions in code comments

---

## Key Principle

> **"Bold maximalism and refined minimalism both work—the key is intentionality, not intensity."**

Every design choice should be deliberate. Whether you choose elaborate or simple, own that choice fully.

---

## Example Prompts This Skill Handles

- "Crie uma interface de dashboard moderna"
- "Design a landing page for a SaaS product"
- "Preciso de um componente de card com visual premium"
- "Build a dark theme for this application"
- "Create an animated hero section"
- "Redesign this form to be more visually appealing"

---

## Integration Notes

This skill is part of the **Claude Code Official Skills** collection.
Namespace: `[OFFICIAL]` - Distinguishes from Mega Brain custom skills.

For custom Mega Brain skills, see: `/.claude/skills/`
