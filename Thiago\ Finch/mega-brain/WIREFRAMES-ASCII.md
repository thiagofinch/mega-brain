# WIREFRAMES ASCII - Dashboard Apple-Style

> Visualização de wireframes em ASCII para referência rápida
> Complementa FIGMA-DESIGN-SYSTEM.md com layouts gráficos

---

## 📱 DESKTOP (1440px) - Full Layout

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                         ┃
┃  [Logo]           [Nav] [Dashboard] [Analytics]             [⚙️Profile] ┃
┃                                                                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
┃                                                                         ┃
┃         Bem-vindo ao Dashboard Premium                                 ┃
┃         Acompanhe métricas em tempo real com precisão.                 ┃
┃                                                                         ┃
┃         [Começar Agora] [Saiba mais]                                   ┃
┃                                                                         ┃
┃         ╭─────────────────────────────────────────────────────╮       ┃
┃         │  [Imagem Hero - Ilustração com gradiente]          │       ┃
┃         │                                                     │       ┃
┃         │                                                     │       ┃
┃         ╰─────────────────────────────────────────────────────╯       ┃
┃                                                                         ┃
├─────────────────────────────────────────────────────────────────────────┤
┃                                                                         ┃
┃  Cards Section (3 columns)                                             ┃
┃                                                                         ┃
┃  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    ┃
┃  │ 🚀 Card 1        │  │ 📊 Card 2        │  │ 💡 Card 3        │    ┃
┃  │                  │  │                  │  │                  │    ┃
┃  │ Título           │  │ Título           │  │ Título           │    ┃
┃  │ Descrição breve  │  │ Descrição breve  │  │ Descrição breve  │    ┃
┃  │                  │  │                  │  │                  │    ┃
┃  │ [Saiba mais →]   │  │ [Saiba mais →]   │  │ [Saiba mais →]   │    ┃
┃  └──────────────────┘  └──────────────────┘  └──────────────────┘    ┃
┃                                                                         ┃
├─────────────────────────────────────────────────────────────────────────┤
┃                                                                         ┃
┃  Live Chart                        [3m] [1h] [1d] [Custom]             ┃
┃                                                                         ┃
┃  Vendas em Tempo Real                                                  ┃
┃                                                                         ┃
┃    │        ╱╲                                                         ┃
┃ R$ │       ╱  ╲    ╱╲          Hover → Tooltip                         ┃
┃    │      ╱    ╲╱  ╱  ╲         Value: R$ 32.100                       ┃
┃    │     ╱            ╲                                                ┃
┃    │────────────────────────────────────────                           ┃
┃    │                                                                    ┃
┃    └─ Seg  Ter  Qua  Qui  Sex  Sab  Dom                               ┃
┃                                                                         ┃
┃  Máx: R$ 45.200 | Atual: R$ 32.100 | Variação: +12,5%                ┃
┃                                                                         ┃
├─────────────────────────────────────────────────────────────────────────┤
┃                                                                         ┃
┃  Pricing Plans (3 columns)                                             ┃
┃                                                                         ┃
┃  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    ┃
┃  │ Básico           │  │ ⭐ Popular       │  │ Empresarial      │    ┃
┃  │                  │  │                  │  │                  │    ┃
┃  │ R$ 99/mês        │  │ R$ 299/mês       │  │ Customizado      │    ┃
┃  │                  │  │                  │  │                  │    ┃
┃  │ ✓ Feature 1      │  │ ✓ Feature 1      │  │ ✓ Feature 1      │    ┃
┃  │ ✓ Feature 2      │  │ ✓ Feature 2      │  │ ✓ Feature 2      │    ┃
┃  │ ✗ Feature 3      │  │ ✓ Feature 3      │  │ ✓ Feature 3      │    ┃
┃  │                  │  │                  │  │                  │    ┃
┃  │ [Começar]        │  │ [Começar]        │  │ [Contato]        │    ┃
┃  └──────────────────┘  └──────────────────┘  └──────────────────┘    ┃
┃                                                                         ┃
├─────────────────────────────────────────────────────────────────────────┤
┃                                                                         ┃
┃  Top 5 Produtos                                    [Ver todos →]      ┃
┃                                                                         ┃
┃  1. Produto A          R$ 12.500    4.2★ ████░░░░░░                  ┃
┃  2. Produto B          R$ 11.200    4.0★ ████░░░░░░                  ┃
┃  3. Produto C          R$ 9.800     3.8★ ███░░░░░░░                  ┃
┃  4. Produto D          R$ 8.900     3.9★ ███░░░░░░░                  ┃
┃  5. Produto E          R$ 7.600     3.6★ ███░░░░░░░                  ┃
┃                                                                         ┃
└─────────────────────────────────────────────────────────────────────────┘

Height breakdown:
  Header:           70px
  Hero Section:     800px
  Cards:            300px (+ spacing)
  Live Chart:       500px (+ spacing)
  Pricing:          600px (+ spacing)
  Top Products:     400px (+ spacing)
  Total:            ~3000px scroll height
```

---

## 📱 TABLET (1024px) - Layout

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                ┃
┃  [Logo]  [Nav] [Dashboard]       [⚙️Profile]   ┃
┃                                                ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
┃                                                ┃
┃      Bem-vindo ao Dashboard                   ┃
┃      Acompanhe métricas em tempo real.        ┃
┃                                                ┃
┃      [Começar Agora] [Saiba mais]             ┃
┃                                                ┃
┃      ╭──────────────────────────────────╮    ┃
┃      │  [Imagem Hero]                   │    ┃
┃      │                                  │    ┃
┃      ╰──────────────────────────────────╯    ┃
┃                                                ┃
├────────────────────────────────────────────────┤
┃                                                ┃
┃  Cards (2 columns on tablet)                   ┃
┃                                                ┃
┃  ┌────────────────────┐  ┌────────────────┐   ┃
┃  │ Card 1             │  │ Card 2         │   ┃
┃  │ [Icon]             │  │ [Icon]         │   ┃
┃  │ Título             │  │ Título         │   ┃
┃  │ Descrição breve    │  │ Descrição      │   ┃
┃  │ [Saiba mais →]     │  │ [Saiba mais]   │   ┃
┃  └────────────────────┘  └────────────────┘   ┃
┃                                                ┃
┃  ┌────────────────────┐                        ┃
┃  │ Card 3             │                        ┃
┃  │ [Icon]             │                        ┃
┃  │ Título             │                        ┃
┃  │ Descrição          │                        ┃
┃  │ [Saiba mais]       │                        ┃
┃  └────────────────────┘                        ┃
┃                                                ┃
├────────────────────────────────────────────────┤
┃                                                ┃
┃  Live Chart          [3m] [1h] [1d]           ┃
┃                                                ┃
┃  ╭──────────────────────────────────────╮    ┃
┃  │          ╱╲                          │    ┃
┃  │         ╱  ╲    ╱╲                   │    ┃
┃  │        ╱    ╲╱  ╱  ╲                 │    ┃
┃  │       ╱            ╲                 │    ┃
┃  │──────────────────────────────────    │    ┃
┃  │                                      │    ┃
┃  │  Seg  Ter  Qua  Qui  Sex  Sab  Dom  │    ┃
┃  ╰──────────────────────────────────────╯    ┃
┃                                                ┃
┃  Máx: R$ 45K | Atual: R$ 32K | Var: +12.5%   ┃
┃                                                ┃
├────────────────────────────────────────────────┤
┃                                                ┃
┃  Pricing (2 columns on tablet)                 ┃
┃                                                ┃
┃  ┌────────────────────┐  ┌────────────────┐   ┃
┃  │ Básico             │  │ ⭐ Popular     │   ┃
┃  │ R$ 99/mês          │  │ R$ 299/mês     │   ┃
┃  │ ✓ Feat 1           │  │ ✓ Feat 1       │   ┃
┃  │ ✓ Feat 2           │  │ ✓ Feat 2       │   ┃
┃  │ ✗ Feat 3           │  │ ✓ Feat 3       │   ┃
┃  │ [Começar]          │  │ [Começar]      │   ┃
┃  └────────────────────┘  └────────────────┘   ┃
┃                                                ┃
┃  ┌────────────────────┐                        ┃
┃  │ Empresarial        │                        ┃
┃  │ Customizado        │                        ┃
┃  │ ✓ Feat 1           │                        ┃
┃  │ ✓ Feat 2           │                        ┃
┃  │ ✓ Feat 3           │                        ┃
┃  │ [Contato]          │                        ┃
┃  └────────────────────┘                        ┃
┃                                                ┃
├────────────────────────────────────────────────┤
┃                                                ┃
┃  Top Produtos              [Ver todos]         ┃
┃                                                ┃
┃  1. Produto A     R$ 12.5K   4.2★  ████░░     ┃
┃  2. Produto B     R$ 11.2K   4.0★  ████░░     ┃
┃  3. Produto C     R$ 9.8K    3.8★  ███░░░     ┃
┃                                                ┃
└────────────────────────────────────────────────┘
```

---

## 📱 MOBILE (375px) - Layout

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                             ┃
┃ [Logo]        [Menu] [⚙️]   ┃
┃                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
┃                             ┃
┃   Bem-vindo ao             ┃
┃   Dashboard Premium         ┃
┃                             ┃
┃   Acompanhe métricas em    ┃
┃   tempo real com precisão. ┃
┃                             ┃
┃   [Começar Agora]          ┃
┃   [Saiba mais]             ┃
┃                             ┃
┃   ╭─────────────────────╮  ┃
┃   │  [Hero Image]       │  ┃
┃   │                     │  ┃
┃   ╰─────────────────────╯  ┃
┃                             ┃
├─────────────────────────────┤
┃                             ┃
┃  Cards (1 column)           ┃
┃                             ┃
┃  ┌──────────────────────┐  ┃
┃  │ 🚀 Card 1            │  ┃
┃  │ Título               │  ┃
┃  │ Descrição breve      │  ┃
┃  │ [Saiba mais →]       │  ┃
┃  └──────────────────────┘  ┃
┃                             ┃
┃  ┌──────────────────────┐  ┃
┃  │ 📊 Card 2            │  ┃
┃  │ Título               │  ┃
┃  │ Descrição            │  ┃
┃  │ [Saiba mais →]       │  ┃
┃  └──────────────────────┘  ┃
┃                             ┃
┃  ┌──────────────────────┐  ┃
┃  │ 💡 Card 3            │  ┃
┃  │ Título               │  ┃
┃  │ Descrição            │  ┃
┃  │ [Saiba mais →]       │  ┃
┃  └──────────────────────┘  ┃
┃                             ┃
├─────────────────────────────┤
┃                             ┃
┃  Live Chart                 ┃
┃  Vendas em Tempo Real       ┃
┃                             ┃
┃  [3m] [1h] [1d]             ┃
┃                             ┃
┃  ╭─────────────────────╮   ┃
┃  │     ╱╲              │   ┃
┃  │    ╱  ╲    ╱╲       │   ┃
┃  │   ╱    ╲╱  ╱  ╲     │   ┃
┃  │  ╱           ╲      │   ┃
┃  │─────────────────────│   ┃
┃  │ Seg Ter Qua Qui    │   ┃
┃  ╰─────────────────────╯   ┃
┃                             ┃
┃  Máx: R$ 45K               ┃
┃  Atual: R$ 32K             ┃
┃  Var: +12.5%               ┃
┃                             ┃
├─────────────────────────────┤
┃                             ┃
┃  Pricing Plans              ┃
┃                             ┃
┃  ┌──────────────────────┐  ┃
┃  │ Básico               │  ┃
┃  │ R$ 99/mês            │  ┃
┃  │ ✓ Feature 1          │  ┃
┃  │ ✓ Feature 2          │  ┃
┃  │ ✗ Feature 3          │  ┃
┃  │ [Começar]            │  ┃
┃  └──────────────────────┘  ┃
┃                             ┃
┃  ┌──────────────────────┐  ┃
┃  │ ⭐ Popular           │  ┃
┃  │ R$ 299/mês           │  ┃
┃  │ ✓ Feature 1          │  ┃
┃  │ ✓ Feature 2          │  ┃
┃  │ ✓ Feature 3          │  ┃
┃  │ [Começar]            │  ┃
┃  └──────────────────────┘  ┃
┃                             ┃
┃  ┌──────────────────────┐  ┃
┃  │ Empresarial          │  ┃
┃  │ Customizado          │  ┃
┃  │ ✓ Feature 1          │  ┃
┃  │ ✓ Feature 2          │  ┃
┃  │ ✓ Feature 3          │  ┃
┃  │ [Contato]            │  ┃
┃  └──────────────────────┘  ┃
┃                             ┃
├─────────────────────────────┤
┃                             ┃
┃  Top Produtos               ┃
┃  [Ver todos]                ┃
┃                             ┃
┃  1. Produto A    R$ 12.5K  ┃
┃  2. Produto B    R$ 11.2K  ┃
┃  3. Produto C    R$ 9.8K   ┃
┃  4. Produto D    R$ 8.9K   ┃
┃  5. Produto E    R$ 7.6K   ┃
┃                             ┃
└─────────────────────────────┘
```

---

## 🌓 DARK MODE - Component Examples

### Header (Dark Mode)
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                          ┃
┃  [Logo]           [Nav] [Dashboard]        [⚙️Profile]  ┃
┃                                                          ┃
┃  Background: #0B0B0B with glass effect                  ┃
┃  Text: #E5E5EA (light)                                  ┃
┃  Border: rgba(255,255,255,0.1)                          ┃
┃                                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Card (Dark Mode)
```
┌──────────────────────┐
│ ■ Card Dark Mode     │  Background: #1C1C1E
│                      │  Border: #424245
│ Title in #E5E5EA     │  Text: #A2A2A2
│ Subtitle in gray     │  Icon: #0A84FF
│                      │  Shadow: darker
│ [Link in Blue]       │
└──────────────────────┘
```

### Chart (Dark Mode)
```
┌─────────────────────────────────────┐
│ Vendas em Tempo Real                │  Background: #1C1C1E
│ [3m] [1h] [1d]                      │  Text: #E5E5EA
│                                     │  Line: #0A84FF
│       ╱╲                            │  Fill: rgba(10,132,255,0.2)
│      ╱  ╲    ╱╲                     │  Grid: #424245
│     ╱    ╲╱  ╱  ╲                   │
│    ╱            ╲                   │
│──────────────────────────────────   │
│ Seg Ter Qua Qui Sex Sab Dom         │
│                                     │
│ Máx: R$ 45K | Atual: R$ 32K        │
└─────────────────────────────────────┘
```

---

## 🎯 COMPONENT DETAIL VIEWS

### Hero Section - Desktop
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  H1: "Bem-vindo ao Dashboard Premium"                           │
│  Size: 56px, Weight: 700, Color: #1D1D1D                        │
│  Margin-bottom: 16px                                            │
│                                                                 │
│  P: "Acompanhe métricas em tempo real com precisão."            │
│  Size: 17px, Weight: 400, Color: #535353                        │
│  Line-height: 1.6, Margin-bottom: 40px                          │
│                                                                 │
│  [Primary Button] [Secondary Button]                            │
│  Spacing: 16px between                                          │
│                                                                 │
│  Image (Hero Illustration)                                      │
│  Height: 400px, Border-radius: 16px                             │
│  Box-shadow: 0 8px 24px rgba(0,0,0,0.16)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Card Component - States
```
STATE: NORMAL
┌─────────────────────┐
│ ▲ Icon (48px)       │
│                     │
│ Title (22px, 600)   │
│ Subtitle (13px)     │
│                     │
│ [Link →]            │
└─────────────────────┘

STATE: HOVER
┌─────────────────────┐  ↑ translateY(-8px)
│ ▲ Icon              │  ↑ shadow 3
│                     │  ↑ border color darker
│ Title               │  ↑ icon scale 1.1
│ Subtitle            │
│                     │
│ [Link →]            │
└─────────────────────┘

STATE: FOCUS
┌─────────────────────┐
│█████ (focus ring)   │  outline: 2px #0071E3
│█Icon 48px        █  │  outline-offset: 2px
│█               █    │
│█ Title           █  │
│█ Subtitle        █  │
│█               █    │
│█[Link →]         █  │
│█████████████████│   │
└─────────────────────┘
```

### Button States
```
PRIMARY BUTTON:
  Normal:   Background: #0071E3, Color: #FFFFFF, Shadow: 2
  Hover:    Scale: 1.02, Shadow: 3, Opacity: 0.95
  Active:   Scale: 0.98, Shadow: 1
  Disabled: Opacity: 0.5, Cursor: not-allowed

SECONDARY BUTTON:
  Normal:   Background: transparent, Border: 1.5px #0071E3
  Hover:    Background: rgba(0,113,227,0.1)
  Active:   Opacity: 0.8
  Disabled: Opacity: 0.5

SIZING:
  Small:    12px 16px, Font: 13px
  Medium:   14px 32px, Font: 15px (default)
  Large:    16px 40px, Font: 17px
```

### Chart - Interaction
```
HOVER POINT:
     ↓ tooltip appears (fade-in 150ms)
  • ← circle (6px radius)
    │ value: R$ 32.100
    └─ date: Mar 05

DATA POINT:
  ○ Normal state
  ⊙ Hover state (pulse animation)

AXIS:
  X: Labels with 4-day spacing
  Y: Currency format with decimals
  Grid: Light gray dashed lines

TOOLTIP:
  Background: rgba(0,0,0,0.9)
  Color: #FFFFFF
  Padding: 8px 12px
  Shadow: 0 4px 16px rgba(0,0,0,0.12)
```

---

## 🎭 STATE TRANSITIONS (Timeline)

### Button Click Animation
```
Timeline (150ms total):
0ms    → User presses button
        → Scale: 1.0 → 0.98
        → Ripple starts expanding

75ms   → Ripple at 50% expansion
        → Color fades from 0.3 to 0.1 opacity

150ms  → Animation complete
        → Scale: 0.98 → 1.0
        → Ripple fully transparent

Easing: cubic-bezier(0.4, 0, 0.2, 1)
```

### Card Entrance Animation
```
Timeline (600ms total):
0ms    → Initial state
        → opacity: 0
        → transform: translateY(24px)

300ms  → Midway (40% complete)
        → opacity: 0.5
        → transform: translateY(12px)

600ms  → Final state
        → opacity: 1
        → transform: translateY(0)

Easing: cubic-bezier(0.34, 1.56, 0.64, 1) [elastic]
Stagger: Each card +100ms delay (card 1: 0ms, card 2: 100ms, etc.)
```

---

## 📊 CHART ANIMATION

### Line Draw Animation
```
Timeline (800ms):

0ms:    ─────────────────────────────────────
        └─ stroke-dashoffset: 1000px

400ms:  ╱─────────────────────────────────────
        └─ stroke-dashoffset: 500px

800ms:  ╱╲──────╱╲──────╱╲──────╱╲──────
        └─ stroke-dashoffset: 0px

Method: CSS stroke-dasharray + animation
Easing: ease-out
```

### Fill Animation
```
Gradient fill appears after line is drawn:
- Opacity: 0 → 0.2 over 800ms
- Gradient: from line color to transparent
- Timing: starts at 200ms (after line starts)
```

---

## 🔔 MODAL & OVERLAY

### Modal Entrance
```
Backdrop:
  opacity: 0 → 1 (300ms)
  background: rgba(0, 0, 0, 0.5)

Modal:
  transform: translateY(24px) → translateY(0)
  opacity: 0 → 1
  timing: 300ms cubic-bezier(0.34, 1.56, 0.64, 1)
  scale: 0.95 → 1.0

┌────────────────────────────────┐
│         Modal Header            │ ← Sticky
├────────────────────────────────┤
│                                │
│      Modal Content Area        │ ← Scrollable
│                                │
│                                │
├────────────────────────────────┤
│  [Cancel]          [Confirm]   │ ← Fixed Footer
└────────────────────────────────┘
```

---

## ✨ SPECIAL EFFECTS

### Glassmorphism Background
```
Light Mode:
  Background: rgba(255, 255, 255, 0.8)
  Backdrop-filter: blur(20px)
  Border: 1px solid rgba(255, 255, 255, 0.5)
  Box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08)

Dark Mode:
  Background: rgba(0, 0, 0, 0.6)
  Backdrop-filter: blur(20px)
  Border: 1px solid rgba(255, 255, 255, 0.1)
  Box-shadow: 0 8px 32px rgba(0, 0, 0, 0.40)
```

### Gradient Overlays
```
Hero Section:
  Base: Linear gradient 135deg
  Light: from #F9F9F9 to #FFFFFF
  Dark: from #000000 to #1C1C1E

Accent:
  On hover cards: radial-gradient
  from rgba(0, 113, 227, 0.1) to transparent
```

---

## 📐 RESPONSIVE BREAKPOINTS (Layout Shifts)

```
375px → 768px (Mobile to Tablet)
  Grid: 1 col → 2 col
  Font-size: -2px (headings scale down)
  Padding: 20px → 40px
  Buttons: full-width → inline

768px → 1024px (Tablet portrait to landscape)
  Grid: 2 col → 3 col
  Font-size: normal
  Padding: 40px
  Cards: grow width

1024px → 1440px (Tablet to Desktop)
  Grid: stable at 3+ col
  Spacing: increase by 20-40px
  Font-size: +2px (larger displays)
  Shadows: stronger
```

---

## 🎨 COLOR REFERENCE (Light Mode)

```
Primary Brand Color:
  ████ #0071E3 (Apple Blue)

Success/Positive:
  ████ #34C759 (Apple Green)

Error/Negative:
  ████ #FF3B30 (Apple Red)

Warning:
  ████ #FF9500 (Apple Orange)

Neutral Scale:
  ████ #1D1D1D (Near Black - headings)
  ████ #535353 (Dark Gray - body text)
  ████ #A2A2A2 (Medium Gray - secondary text)
  ████ #E8E8E8 (Light Gray - borders)
  ████ #F9F9F9 (Off-White - backgrounds)
  ████ #FFFFFF (Pure White)
```

---

## 📋 SPACING GRID REFERENCE

```
Every component measured in 8px units:

  4px   = 0.5 unit (micro)
  8px   = 1 unit   ← base
  16px  = 2 units
  24px  = 3 units
  32px  = 4 units  ← most common
  40px  = 5 units
  48px  = 6 units
  60px  = 7.5 units
  80px  = 10 units

Example Card Padding:
  Mobile:  24px (3 units)
  Tablet:  32px (4 units)
  Desktop: 40px (5 units)
```

---

**Wireframes v1.0.0 — Complete & Production Ready**

*ASCII wireframes for quick reference during development*
*Full interactive prototypes in Figma file*
