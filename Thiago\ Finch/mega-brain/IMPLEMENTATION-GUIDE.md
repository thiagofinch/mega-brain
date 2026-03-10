# IMPLEMENTATION GUIDE - Dashboard Apple-Style

> **Quick Start for Development Team**
> Complementa FIGMA-DESIGN-SYSTEM.md e WIREFRAMES-ASCII.md
> Instruções passo-a-passo para implementação

---

## 🚀 QUICK START (15 minutes)

### 1. Setup Inicial (5 min)

```bash
# Clone project
git clone <repo-url> mega-brain-dashboard
cd mega-brain-dashboard

# Install dependencies
npm install

# Install design system CLI
npm install figma-tokens @figma/css-config

# Copy design tokens
npm run design:sync

# Start development server
npm run dev
```

### 2. Import Design Tokens (3 min)

```bash
# Generate CSS variables from design tokens
npm run tokens:generate

# Output: src/styles/tokens.css
# Contains all colors, typography, spacing, shadows
```

### 3. Start Building (7 min)

```bash
# Create component structure
mkdir -p src/components/{header,hero,cards,chart,pricing,products}
mkdir -p src/styles/{components,responsive,themes}

# Storybook for component development
npm run storybook

# Opens http://localhost:6006
```

---

## 📁 PROJECT STRUCTURE

```
dashboard-app/
├── public/
│   ├── icons/               ← SVG icons from Figma
│   ├── images/              ← PNG, WebP images
│   └── illustrations/       ← Hero illustrations
│
├── src/
│   ├── components/
│   │   ├── Header.jsx       ← Navigation + profile
│   │   ├── HeroSection.jsx  ← Main hero
│   │   ├── CardGrid.jsx     ← 3-column cards
│   │   ├── LiveChart.jsx    ← Real-time chart
│   │   ├── PricingCards.jsx ← Pricing plans
│   │   └── TopProducts.jsx  ← Product rankings
│   │
│   ├── hooks/
│   │   ├── useMediaQuery.js ← Responsive breakpoints
│   │   ├── useDarkMode.js   ← Dark/light toggle
│   │   └── useChart.js      ← Chart data + animations
│   │
│   ├── styles/
│   │   ├── tokens.css       ← Design tokens (auto-generated)
│   │   ├── global.css       ← Base styles
│   │   ├── components/
│   │   │   ├── button.css
│   │   │   ├── card.css
│   │   │   ├── header.css
│   │   │   └── ...
│   │   ├── responsive/
│   │   │   ├── mobile.css
│   │   │   ├── tablet.css
│   │   │   └── desktop.css
│   │   ├── themes/
│   │   │   ├── light.css
│   │   │   └── dark.css
│   │   └── animations.css   ← Keyframes + transitions
│   │
│   ├── utils/
│   │   ├── formatCurrency.js
│   │   ├── formatDate.js
│   │   └── chartHelpers.js
│   │
│   └── App.jsx
│
├── .figma                   ← Figma token sync config
├── figma.config.js          ← Figma tokens export
├── storybook/               ← Component library
└── package.json
```

---

## 🎨 CSS ARCHITECTURE

### Token Import
```css
/* src/styles/tokens.css (AUTO-GENERATED) */

:root {
  --color-primary: #0071E3;
  --color-primary-dark: #0A84FF;
  --color-success: #34C759;
  --color-error: #FF3B30;
  /* ... ~60 more tokens ... */

  --font-family-display: 'SF Pro Display', -apple-system, sans-serif;
  --font-family-text: 'SF Pro Text', -apple-system, sans-serif;

  --space-xs: 4px;
  --space-s: 8px;
  --space-m: 16px;
  --space-l: 24px;
  --space-xl: 32px;
  --space-2xl: 40px;
  --space-3xl: 48px;
  --space-4xl: 60px;

  --radius-s: 8px;
  --radius-m: 12px;
  --radius-l: 16px;
  --radius-xl: 20px;

  --shadow-1: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-2: 0 4px 16px rgba(0, 0, 0, 0.12);
  --shadow-3: 0 8px 24px rgba(0, 0, 0, 0.16);

  --transition-quick: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-smooth: 500ms cubic-bezier(0.4, 0, 0.2, 1);
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: #0A84FF;
    --color-text-primary: #E5E5EA;
    --color-background: #000000;
    /* ... dark mode tokens ... */
  }
}
```

### Component CSS Pattern
```css
/* src/styles/components/card.css */

.card {
  padding: var(--space-xl);
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

/* Dark mode - no need, tokens already updated */
```

---

## 🧩 COMPONENT IMPLEMENTATION

### 1. Header Component

```jsx
// src/components/Header.jsx

import React, { useState } from 'react';
import '../styles/components/header.css';

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <header className="header" role="banner">
      <div className="header-container">

        {/* Logo */}
        <div className="header-logo">
          <a href="/" aria-label="Dashboard home">
            Mega Brain
          </a>
        </div>

        {/* Navigation (Desktop) */}
        <nav
          className="header-nav"
          aria-label="Main navigation"
          data-visible={!isMobileMenuOpen}
        >
          <a href="#dashboard" className="nav-link active">
            Dashboard
          </a>
          <a href="#analytics" className="nav-link">
            Analytics
          </a>
          <a href="#settings" className="nav-link">
            Settings
          </a>
        </nav>

        {/* Profile Button */}
        <button
          className="header-profile"
          aria-label="User profile menu"
        >
          <span className="icon">⚙️</span>
        </button>

        {/* Mobile Menu Toggle */}
        <button
          className="header-menu-toggle"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle navigation menu"
          aria-expanded={isMobileMenuOpen}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>
    </header>
  );
}
```

#### Header CSS
```css
/* src/styles/components/header.css */

.header {
  position: sticky;
  top: 0;
  z-index: 1000;
  height: 70px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--color-border);
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-m) var(--space-3xl);
  height: 100%;
}

.header-logo {
  font-family: var(--font-family-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.header-nav {
  display: flex;
  gap: var(--space-2xl);
}

.nav-link {
  font-family: var(--font-family-text);
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  padding-bottom: 6px;
  transition: all var(--transition-quick);
  cursor: pointer;
}

.nav-link:hover,
.nav-link.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.header-profile {
  width: 44px;
  height: 44px;
  background: var(--color-background-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-l);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-quick);
}

.header-profile:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-2);
}

.header-menu-toggle {
  display: none;
  flex-direction: column;
  gap: 6px;
  background: none;
  border: none;
  cursor: pointer;
}

.header-menu-toggle span {
  width: 24px;
  height: 2px;
  background: var(--color-text-primary);
  border-radius: 1px;
  transition: all var(--transition-quick);
}

@media (max-width: 768px) {
  .header-container {
    padding: var(--space-m) var(--space-l);
  }

  .header-nav {
    position: fixed;
    left: 0;
    top: 70px;
    width: 100%;
    height: calc(100vh - 70px);
    flex-direction: column;
    gap: var(--space-l);
    background: rgba(0, 0, 0, 0.95);
    padding: var(--space-2xl);
    transform: translateX(-100%);
    transition: transform var(--transition-smooth);
  }

  .header-nav[data-visible="true"] {
    transform: translateX(0);
  }

  .nav-link {
    color: var(--color-text-primary);
    font-size: 17px;
  }

  .header-menu-toggle {
    display: flex;
  }
}

@media (prefers-color-scheme: dark) {
  .header {
    background: rgba(0, 0, 0, 0.6);
  }
}
```

### 2. Hero Section Component

```jsx
// src/components/HeroSection.jsx

import React from 'react';
import '../styles/components/hero.css';

export function HeroSection() {
  return (
    <section className="hero" aria-label="Welcome section">
      <div className="hero-container">

        <h1 className="hero-title">
          Bem-vindo ao Dashboard Premium
        </h1>

        <p className="hero-subtitle">
          Acompanhe métricas em tempo real com precisão.
        </p>

        <div className="hero-actions">
          <button className="button button--primary">
            Começar Agora
          </button>
          <a href="#pricing" className="button button--secondary">
            Saiba mais
          </a>
        </div>

        <figure className="hero-image">
          <img
            src="hero-illustration.webp"
            alt="Dashboard preview showing real-time sales metrics"
            width="600"
            height="400"
            loading="lazy"
          />
        </figure>
      </div>
    </section>
  );
}
```

#### Hero CSS
```css
/* src/styles/components/hero.css */

.hero {
  padding: var(--space-4xl) var(--space-3xl);
  background: linear-gradient(135deg, #F9F9F9 0%, #FFFFFF 100%);
  min-height: 800px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-container {
  max-width: 1200px;
  width: 100%;
}

.hero-title {
  font-family: var(--font-family-display);
  font-size: 56px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
  letter-spacing: -0.5px;
  margin-bottom: var(--space-m);
  animation: slideUp 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hero-subtitle {
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--space-2xl);
  max-width: 600px;
  animation: slideUp 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
  animation-delay: 100ms;
}

.hero-actions {
  display: flex;
  gap: var(--space-m);
  margin-bottom: var(--space-3xl);
  animation: slideUp 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
  animation-delay: 200ms;
}

.hero-image {
  margin: 0;
  animation: slideUp 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
  animation-delay: 300ms;
}

.hero-image img {
  width: 100%;
  height: auto;
  border-radius: var(--radius-l);
  box-shadow: var(--shadow-3);
}

@media (max-width: 1024px) {
  .hero {
    padding: var(--space-3xl) var(--space-2xl);
    min-height: 600px;
  }

  .hero-title {
    font-size: 40px;
  }
}

@media (max-width: 768px) {
  .hero {
    padding: var(--space-2xl) var(--space-l);
    min-height: 500px;
    text-align: center;
  }

  .hero-title {
    font-size: 28px;
  }

  .hero-actions {
    flex-direction: column;
  }
}

@media (prefers-color-scheme: dark) {
  .hero {
    background: linear-gradient(135deg, #000000 0%, #1C1C1E 100%);
  }
}
```

### 3. Card Grid Component

```jsx
// src/components/CardGrid.jsx

import React from 'react';
import '../styles/components/card.css';

const CARDS = [
  {
    id: 1,
    icon: '🚀',
    title: 'Aceleração',
    subtitle: 'Implemente rapidamente com templates prontos.',
    link: '#'
  },
  {
    id: 2,
    icon: '📊',
    title: 'Analytics',
    subtitle: 'Visualize dados em tempo real com precisão.',
    link: '#'
  },
  {
    id: 3,
    icon: '💡',
    title: 'Insights',
    subtitle: 'Decisões baseadas em inteligência de negócio.',
    link: '#'
  }
];

export function CardGrid() {
  return (
    <section className="cards-section">
      <div className="cards-container">
        {CARDS.map((card, index) => (
          <article
            key={card.id}
            className="card"
            style={{ '--delay': `${index * 100}ms` }}
          >
            <div className="card-icon">{card.icon}</div>
            <h3 className="card-title">{card.title}</h3>
            <p className="card-subtitle">{card.subtitle}</p>
            <a href={card.link} className="card-link">
              Saiba mais →
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}
```

#### Card Grid CSS
```css
/* src/styles/components/card.css */

.cards-section {
  padding: var(--space-3xl);
}

.cards-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-2xl);
}

.card {
  padding: var(--space-2xl);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-l);
  box-shadow: var(--shadow-1);
  transition: all var(--transition-quick);
  animation: slideUp 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
  animation-delay: var(--delay, 0ms);
  animation-fill-mode: both;
  min-height: 280px;
  display: flex;
  flex-direction: column;
}

.card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-3);
  border-color: var(--color-primary);
}

.card:focus-within {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.card-icon {
  font-size: 48px;
  margin-bottom: var(--space-m);
  transition: transform var(--transition-quick);
}

.card:hover .card-icon {
  transform: scale(1.1);
}

.card-title {
  font-family: var(--font-family-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-s);
}

.card-subtitle {
  font-family: var(--font-family-text);
  font-size: 13px;
  font-weight: 400;
  color: var(--color-text-secondary);
  line-height: 1.4;
  margin-bottom: var(--space-m);
  flex-grow: 1;
}

.card-link {
  font-family: var(--font-family-text);
  font-size: 15px;
  font-weight: 500;
  color: var(--color-primary);
  text-decoration: none;
  cursor: pointer;
  transition: transform var(--transition-quick);
}

.card-link:hover {
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .cards-section {
    padding: var(--space-2xl);
  }

  .cards-container {
    grid-template-columns: 1fr;
  }

  .card {
    min-height: auto;
  }
}

@media (prefers-color-scheme: dark) {
  .card {
    background: var(--color-background-secondary);
  }
}
```

### 4. Live Chart Component

```jsx
// src/components/LiveChart.jsx

import React, { useState, useEffect } from 'react';
import '../styles/components/chart.css';

export function LiveChart() {
  const [timeframe, setTimeframe] = useState('1h');
  const [data, setData] = useState([]);
  const [hoveredPoint, setHoveredPoint] = useState(null);

  useEffect(() => {
    // Simulate real-time data
    const mockData = Array.from({ length: 7 }, (_, i) => ({
      day: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'][i],
      value: Math.floor(Math.random() * 40000) + 10000
    }));
    setData(mockData);
  }, [timeframe]);

  const maxValue = Math.max(...data.map(d => d.value));
  const points = data.map((d, i) => ({
    ...d,
    x: (i / (data.length - 1)) * 100,
    y: 100 - ((d.value / maxValue) * 100)
  }));

  return (
    <section className="chart-section">
      <div className="chart-container">

        <div className="chart-header">
          <h2 className="chart-title">Vendas em Tempo Real</h2>
          <div className="chart-timeframe">
            {['3m', '1h', '1d'].map(tf => (
              <button
                key={tf}
                className={`timeframe-btn ${timeframe === tf ? 'active' : ''}`}
                onClick={() => setTimeframe(tf)}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Chart SVG */}
        <svg
          className="chart-svg"
          viewBox="0 0 600 300"
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          <g className="grid">
            {[0, 25, 50, 75, 100].map(y => (
              <line
                key={y}
                x1="0"
                y1={`${y}%`}
                x2="100%"
                y2={`${y}%`}
                className="grid-line"
              />
            ))}
          </g>

          {/* Line path */}
          {points.length > 1 && (
            <>
              <path
                className="chart-line"
                d={`M ${points.map(p => `${p.x},${p.y}`).join(' L ')}`}
              />

              {/* Area fill */}
              <path
                className="chart-fill"
                d={`M ${points.map(p => `${p.x},${p.y}`).join(' L ')} L 100,100 L 0,100 Z`}
              />
            </>
          )}

          {/* Data points */}
          {points.map((point, i) => (
            <g key={i}>
              <circle
                className="data-point"
                cx={`${point.x}%`}
                cy={`${point.y}%`}
                r="4"
                onMouseEnter={() => setHoveredPoint(i)}
                onMouseLeave={() => setHoveredPoint(null)}
              />

              {hoveredPoint === i && (
                <g className="tooltip">
                  <text
                    x={`${point.x}%`}
                    y={`${Math.max(point.y - 10, 5)}%`}
                    textAnchor="middle"
                  >
                    R$ {point.value.toLocaleString('pt-BR')}
                  </text>
                </g>
              )}
            </g>
          ))}

          {/* X-axis labels */}
          <g className="axis-x">
            {points.map((point, i) => (
              <text
                key={i}
                x={`${point.x}%`}
                y="100%"
                textAnchor="middle"
                dy="1.2em"
              >
                {point.day}
              </text>
            ))}
          </g>
        </svg>

        {/* Stats */}
        <div className="chart-stats">
          <div className="stat">
            <span className="stat-label">Máximo</span>
            <span className="stat-value">
              R$ {maxValue.toLocaleString('pt-BR')}
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">Atual</span>
            <span className="stat-value">
              R$ {data[data.length - 1]?.value.toLocaleString('pt-BR')}
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">Variação</span>
            <span className="stat-value stat-positive">+12,5%</span>
          </div>
        </div>
      </div>
    </section>
  );
}
```

#### Chart CSS
```css
/* src/styles/components/chart.css */

.chart-section {
  padding: var(--space-3xl);
}

.chart-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-2xl);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-l);
  box-shadow: var(--shadow-1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2xl);
}

.chart-title {
  font-family: var(--font-family-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.chart-timeframe {
  display: flex;
  gap: var(--space-s);
}

.timeframe-btn {
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: var(--radius-s);
  font-family: var(--font-family-text);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-quick);
}

.timeframe-btn.active {
  color: var(--color-primary);
  background: var(--color-background-secondary);
}

.chart-svg {
  width: 100%;
  height: 300px;
  margin-bottom: var(--space-2xl);
  animation: fadeIn 500ms ease-out;
}

.grid-line {
  stroke: var(--color-border);
  stroke-dasharray: 4;
  opacity: 0.5;
}

.chart-line {
  stroke: var(--color-primary);
  stroke-width: 2;
  fill: none;
  animation: drawLine 800ms ease-out forwards;
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
}

.chart-fill {
  fill: url(#gradient);
  opacity: 0.2;
  animation: fadeIn 800ms ease-out forwards;
  animation-delay: 200ms;
}

.data-point {
  fill: var(--color-primary);
  cursor: pointer;
  transition: all var(--transition-quick);
}

.data-point:hover {
  r: 6px;
  filter: drop-shadow(0 0 8px var(--color-primary));
}

.tooltip {
  pointer-events: none;
}

.tooltip text {
  font-family: var(--font-family-mono);
  font-size: 13px;
  fill: var(--color-text-primary);
}

.axis-x text {
  font-family: var(--font-family-text);
  font-size: 12px;
  fill: var(--color-text-secondary);
}

.chart-stats {
  display: flex;
  justify-content: space-around;
  padding: var(--space-l) 0;
  border-top: 1px solid var(--color-border);
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-family: var(--font-family-text);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.stat-value {
  font-family: var(--font-family-display);
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-positive {
  color: var(--color-success);
}

@keyframes drawLine {
  to {
    stroke-dashoffset: 0;
  }
}

@media (max-width: 768px) {
  .chart-section {
    padding: var(--space-2xl);
  }

  .chart-svg {
    height: 200px;
  }

  .chart-stats {
    flex-direction: column;
    gap: var(--space-m);
  }
}

@media (prefers-color-scheme: dark) {
  .chart-container {
    background: var(--color-background-secondary);
  }
}
```

---

## 🔧 HOOKS FOR INTERACTIVITY

### useMediaQuery Hook
```jsx
// src/hooks/useMediaQuery.js

import { useState, useEffect } from 'react';

export function useMediaQuery(query) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }

    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

// Usage:
// const isMobile = useMediaQuery('(max-width: 768px)');
```

### useDarkMode Hook
```jsx
// src/hooks/useDarkMode.js

import { useState, useEffect } from 'react';

export function useDarkMode() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const darkMode = window.matchMedia('(prefers-color-scheme: dark)');
    setIsDark(darkMode.matches);

    const listener = (e) => setIsDark(e.matches);
    darkMode.addEventListener('change', listener);
    return () => darkMode.removeEventListener('change', listener);
  }, []);

  return isDark;
}

// Usage:
// const isDark = useDarkMode();
```

---

## ⚡ PERFORMANCE OPTIMIZATION

### Image Optimization
```jsx
// Use picture element for responsive images
<picture>
  <source srcSet="image.webp" type="image/webp" />
  <source srcSet="image.png" type="image/png" />
  <img src="image.png" alt="..." loading="lazy" />
</picture>

// Responsive images with srcset
<img
  srcSet="image-small.png 375w, image-medium.png 1024w, image-large.png 1440w"
  sizes="(max-width: 768px) 375px, (max-width: 1024px) 1024px, 1440px"
  alt="..."
/>
```

### Code Splitting
```jsx
// src/App.jsx

import React, { Suspense, lazy } from 'react';

const HeroSection = lazy(() => import('./components/HeroSection'));
const CardGrid = lazy(() => import('./components/CardGrid'));
const LiveChart = lazy(() => import('./components/LiveChart'));
const PricingCards = lazy(() => import('./components/PricingCards'));
const TopProducts = lazy(() => import('./components/TopProducts'));

export default function App() {
  return (
    <>
      <Suspense fallback={<div>Loading...</div>}>
        <HeroSection />
        <CardGrid />
        <LiveChart />
        <PricingCards />
        <TopProducts />
      </Suspense>
    </>
  );
}
```

### Critical CSS
```css
/* Inline critical CSS in <head> for above-the-fold content */
/* Keep < 50KB */

@import url('/styles/tokens.css');
@import url('/styles/components/header.css');
@import url('/styles/components/hero.css');
```

---

## 🧪 TESTING

### Visual Regression Testing
```bash
# Install Playwright
npm install @playwright/test

# Run visual tests
npm run test:visual

# Update snapshots
npm run test:visual -- --update
```

### Example Test
```javascript
// tests/header.spec.js

import { test, expect } from '@playwright/test';

test('header renders correctly', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Check header is visible
  const header = await page.locator('header');
  await expect(header).toBeVisible();

  // Check logo
  const logo = await page.locator('[aria-label="Dashboard home"]');
  await expect(logo).toBeVisible();

  // Check dark mode
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page).toHaveScreenshot('header-dark.png');
});
```

---

## 🚢 DEPLOYMENT CHECKLIST

```bash
# Build for production
npm run build

# Run lighthouse audit
npm run audit

# Check performance
npm run test:perf

# Security audit
npm audit

# Deploy
npm run deploy
```

### Performance Targets (Lighthouse)
```
Performance:       95+
Accessibility:     100
Best Practices:    95+
SEO:              100
First Contentful Paint: < 1s
Cumulative Layout Shift: < 0.1
```

---

**Implementation Guide v1.0.0**

*Complete walkthrough from design system to production-ready code*
