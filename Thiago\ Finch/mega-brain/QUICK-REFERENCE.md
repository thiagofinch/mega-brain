# Quick Reference - Design System Tokens & Patterns

> Copy-paste ready values for implementation

---

## 🎨 COLOR TOKENS

### Light Mode
```css
--color-primary: #0071E3;
--color-success: #34C759;
--color-error: #FF3B30;
--color-warning: #FF9500;
--color-text-primary: #1D1D1D;
--color-text-secondary: #535353;
--color-text-tertiary: #A2A2A2;
--color-background: #FFFFFF;
--color-background-secondary: #F9F9F9;
--color-border: #E8E8E8;
```

### Dark Mode
```css
--color-primary: #0A84FF;
--color-success: #32D74B;
--color-error: #FF453A;
--color-warning: #FF9500;
--color-text-primary: #E5E5EA;
--color-text-secondary: #A2A2A2;
--color-text-tertiary: #8E8E93;
--color-background: #000000;
--color-background-secondary: #1C1C1E;
--color-border: #424245;
```

---

## 📐 TYPOGRAPHY TOKENS

```css
--font-family-display: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-family-text: 'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-family-mono: 'SF Mono', Monaco, 'Courier New', monospace;

/* Sizes */
--font-size-hero: 56px;
--font-size-lg: 40px;
--font-size-h1: 28px;
--font-size-h2: 22px;
--font-size-h3: 17px;
--font-size-body: 15px;
--font-size-small: 13px;
--font-size-xs: 12px;

/* Weights */
--font-weight-regular: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

/* Line Heights (per size) */
--line-height-hero: 1.2;     /* 56px → 67px */
--line-height-lg: 1.3;        /* 40px → 52px */
--line-height-h1: 1.4;        /* 28px → 39px */
--line-height-h2: 1.5;        /* 22px → 33px */
--line-height-body: 1.6;      /* 15px → 27px */
```

---

## 📏 SPACING TOKENS

```css
/* 8px Base Grid */
--space-xs: 4px;       /* 0.5 unit */
--space-s: 8px;        /* 1 unit - base */
--space-m: 16px;       /* 2 units */
--space-l: 24px;       /* 3 units */
--space-xl: 32px;      /* 4 units - most common */
--space-2xl: 40px;     /* 5 units */
--space-3xl: 48px;     /* 6 units */
--space-4xl: 60px;     /* 7.5 units */
--space-5xl: 80px;     /* 10 units */
```

---

## 🎯 RADIUS TOKENS

```css
--radius-xs: 4px;         /* Subtle */
--radius-s: 8px;          /* Buttons, small */
--radius-m: 12px;         /* Cards (most common) */
--radius-l: 16px;         /* Large containers */
--radius-xl: 20px;        /* Hero sections */
--radius-full: 9999px;    /* Pills, avatars */
```

---

## 🌑 SHADOW TOKENS

```css
/* Light Mode */
--shadow-1: 0 2px 8px rgba(0, 0, 0, 0.08);
--shadow-2: 0 4px 16px rgba(0, 0, 0, 0.12);
--shadow-3: 0 8px 24px rgba(0, 0, 0, 0.16);
--shadow-4: 0 12px 32px rgba(0, 0, 0, 0.20);

/* Dark Mode */
--shadow-dark-1: 0 2px 8px rgba(0, 0, 0, 0.40);
--shadow-dark-2: 0 4px 16px rgba(0, 0, 0, 0.50);
--shadow-dark-3: 0 8px 24px rgba(0, 0, 0, 0.60);
--shadow-dark-4: 0 12px 32px rgba(0, 0, 0, 0.70);
```

---

## ⏱️ TRANSITION TOKENS

```css
--transition-quick: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-smooth: 500ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-elastic: 600ms cubic-bezier(0.34, 1.56, 0.64, 1);

/* Usage */
transition: all var(--transition-quick);
transition: transform var(--transition-normal), opacity var(--transition-normal);
```

---

## 🪟 RESPONSIVE BREAKPOINTS

```css
/* Mobile First Approach */
@media (min-width: 768px) {
  /* Tablet and up */
}

@media (min-width: 1024px) {
  /* Desktop and up */
}

@media (min-width: 1440px) {
  /* Large desktop */
}

/* Or Mobile Last */
@media (max-width: 767px) {
  /* Mobile only */
}

@media (max-width: 1023px) {
  /* Mobile and tablet */
}
```

---

## 🎬 ANIMATION KEYFRAMES

### Slide Up
```css
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### Fade In
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

### Scale
```css
@keyframes scaleUp {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### Draw Line (SVG)
```css
@keyframes drawLine {
  to {
    stroke-dashoffset: 0;
  }
}
```

### Pulse
```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
```

---

## 🔘 BUTTON PATTERNS

### Primary Button
```css
.button--primary {
  padding: 14px 32px;
  background: var(--color-primary);
  color: #FFFFFF;
  border: none;
  border-radius: var(--radius-s);
  font-family: var(--font-family-text);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-quick);
  box-shadow: var(--shadow-2);
}

.button--primary:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-3);
  opacity: 0.95;
}

.button--primary:active {
  transform: scale(0.98);
}

.button--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

### Secondary Button
```css
.button--secondary {
  padding: 14px 32px;
  background: transparent;
  color: var(--color-primary);
  border: 1.5px solid var(--color-primary);
  border-radius: var(--radius-s);
  font-family: var(--font-family-text);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-quick);
}

.button--secondary:hover {
  background: rgba(0, 113, 227, 0.1);
}

.button--secondary:active {
  opacity: 0.8;
}
```

---

## 🃏 CARD PATTERN

```css
.card {
  padding: var(--space-2xl);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-l);
  box-shadow: var(--shadow-1);
  transition: all var(--transition-quick);
}

.card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-3);
  border-color: var(--color-primary);
}

.card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

---

## 📝 FORM INPUT PATTERN

```css
input,
textarea,
select {
  padding: 12px 16px;
  background: var(--color-background-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-s);
  font-family: var(--font-family-text);
  font-size: 15px;
  color: var(--color-text-primary);
  transition: all var(--transition-quick);
}

input:focus,
textarea:focus,
select:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-color: var(--color-primary);
}

input:disabled,
textarea:disabled,
select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## 🎯 TYPOGRAPHY HIERARCHY

### H1 (Hero Title)
```css
h1 {
  font-family: var(--font-family-display);
  font-size: 56px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.5px;
  color: var(--color-text-primary);
  margin-bottom: var(--space-m);
}
```

### H2 (Section Title)
```css
h2 {
  font-family: var(--font-family-display);
  font-size: 28px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--color-text-primary);
  margin-bottom: var(--space-l);
}
```

### H3 (Component Title)
```css
h3 {
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--color-text-primary);
  margin-bottom: var(--space-m);
}
```

### Body Text
```css
p {
  font-family: var(--font-family-text);
  font-size: 15px;
  font-weight: 400;
  line-height: 1.6;
  color: var(--color-text-secondary);
}
```

---

## 🌙 DARK MODE SETUP

```css
/* In CSS file root */
:root {
  /* Light mode (default) */
}

@media (prefers-color-scheme: dark) {
  :root {
    /* Dark mode overrides */
    --color-primary: #0A84FF;
    --color-background: #000000;
    --color-text-primary: #E5E5EA;
    /* etc. */
  }
}
```

### JavaScript Toggle
```jsx
function useDarkMode() {
  const [isDark, setIsDark] = useState(
    window.matchMedia('(prefers-color-scheme: dark)').matches
  );

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const listener = (e) => setIsDark(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, []);

  return isDark;
}
```

---

## ♿ ACCESSIBILITY QUICK CHECKS

### Focus Outline (Required)
```css
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### Color Contrast (Check in DevTools)
```
WCAG AA requires:
  Normal text (< 18pt):    4.5:1 contrast ratio
  Large text (≥ 18pt):     3:1 contrast ratio
  UI components:           3:1 contrast ratio
```

### ARIA Labels (Required for icons)
```html
<!-- Icon button needs label -->
<button aria-label="Close menu">×</button>

<!-- Form inputs need labels -->
<label for="email">Email Address</label>
<input id="email" type="email" />

<!-- Images need alt text -->
<img src="..." alt="Dashboard preview" />
```

### Keyboard Navigation
```css
/* Never remove focus outlines, style them instead */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Tab order should be logical */
/* Use tabindex sparingly, prefer HTML order */
```

---

## 📱 RESPONSIVE PATTERNS

### Flexible Grid
```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-2xl);
}
```

### Flexible Container
```css
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-l);
}

@media (min-width: 1024px) {
  .container {
    padding: 0 var(--space-2xl);
  }
}
```

### Stack on Mobile
```css
.flex-row {
  display: flex;
  gap: var(--space-l);
}

@media (max-width: 767px) {
  .flex-row {
    flex-direction: column;
  }
}
```

---

## 🎨 GLASSMORPHISM EFFECT

```css
.glass {
  background: rgba(255, 255, 255, 0.8); /* Light mode */
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

@media (prefers-color-scheme: dark) {
  .glass {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.40);
  }
}
```

---

## 🚀 PERFORMANCE TIPS

### GPU Acceleration
```css
.animated {
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
}
```

### Optimize Animations
```css
/* Good - GPU accelerated */
.element {
  animation: slideUp 600ms ease-out;
}

/* Bad - triggers layout recalculation */
.element {
  animation: changeWidth 600ms ease-out;
}
```

### Respect Motion Preferences
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 📦 COPY-PASTE COMPONENTS

### Complete Button Component
```html
<button class="button button--primary">
  Click Me
</button>

<style>
  .button {
    padding: 14px 32px;
    background: var(--color-primary);
    color: #FFFFFF;
    border: none;
    border-radius: var(--radius-s);
    font-family: var(--font-family-text);
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-quick);
    box-shadow: var(--shadow-2);
  }

  .button:hover {
    transform: scale(1.02);
    box-shadow: var(--shadow-3);
  }

  .button:active {
    transform: scale(0.98);
  }

  .button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
```

### Complete Card Component
```html
<article class="card">
  <h3 class="card-title">Card Title</h3>
  <p class="card-subtitle">Card description</p>
  <a href="#" class="card-link">Learn more →</a>
</article>

<style>
  .card {
    padding: var(--space-2xl);
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-l);
    box-shadow: var(--shadow-1);
    transition: all var(--transition-quick);
  }

  .card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-3);
    border-color: var(--color-primary);
  }

  .card-title {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: var(--space-s);
  }

  .card-subtitle {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin-bottom: var(--space-m);
  }

  .card-link {
    color: var(--color-primary);
    text-decoration: none;
    transition: transform var(--transition-quick);
  }

  .card-link:hover {
    transform: translateX(4px);
  }
</style>
```

---

## 🔗 QUICK LINKS

- **Full Specs:** FIGMA-DESIGN-SYSTEM.md
- **Wireframes:** WIREFRAMES-ASCII.md
- **Code Examples:** IMPLEMENTATION-GUIDE.md
- **Progress:** DESIGN-SYSTEM-STATUS.md

---

**Quick Reference v1.0.0**

*Copy-paste tokens & patterns for rapid implementation*
