# COMPONENT INVENTORY & WEEK 2 BUILD MATRIX
## Frontend Architecture Snapshot
**Date:** 2026-03-06
**Status:** Week 1 Complete, Week 2 Ready

---

## 📦 EXISTING COMPONENTS (Week 1)

### ✅ Completed Components

#### 1. Header Component
**File:** `frontend/app/components/Header.tsx`
**Status:** ✅ Complete
**Features:**
- Navigation structure
- Responsive layout
- Accessibility compliant
**Lines:** ~45 LOC
**Tests:** Not yet (Week 2)
**Note:** Will be enhanced in Week 2 with theme toggle

---

#### 2. Button Component
**File:** `frontend/app/components/Button.tsx`
**Status:** ✅ Complete
**Variants:**
- Primary (blue)
- Secondary (gray)
- Danger (red)
**Props:** children, onClick, variant, disabled
**Lines:** ~30 LOC
**Tests:** Not yet
**Reusable:** Yes (used in multiple components)

---

### 🟡 Partially Complete Components

#### 3. Layout
**File:** `frontend/app/layout.tsx`
**Status:** 🟡 Basic Implementation
**Current:**
- Root layout structure
- Font imports (Inter)
- Metadata
**Lines:** ~20 LOC
**Missing:**
- Theme provider
- Global state
**Week 2:** Add Theme Context

---

#### 4. Home Page
**File:** `frontend/app/page.tsx`
**Status:** 🟡 Landing Page
**Current:**
- Welcome screen
- Status indicator
- Feature list
**Lines:** ~40 LOC
**Action in Week 2:** Replace with Dashboard

---

## 🔌 HOOKS (Prepared)

### ✅ Prepared Hooks

#### 1. useApi
**File:** `frontend/app/hooks/useApi.ts`
**Purpose:** Generic SWR data fetching
**Usage:** `const { data, error, isLoading } = useApi('/api/endpoint')`
**Status:** ✅ Ready

---

#### 2. useSales
**File:** `frontend/app/hooks/useSales.ts`
**Purpose:** Fetch sales data from /api/sales
**Status:** ✅ Ready
**Returns:** `{ sales, isLoading, error, mutate }`

---

#### 3. useTariffs
**File:** `frontend/app/hooks/useTariffs.ts`
**Purpose:** Fetch pricing plans from /api/tarifas
**Status:** ✅ Ready
**Returns:** `{ tarifas, isLoading, error, mutate }`

---

#### 4. useTheme
**File:** `frontend/app/hooks/useTheme.ts`
**Purpose:** Dark/light theme toggle
**Status:** ✅ Ready
**Returns:** `{ theme, toggleTheme }`

---

#### 5. useWebSocket
**File:** `frontend/app/hooks/useWebSocket.ts`
**Purpose:** Real-time data via WebSocket
**Status:** ✅ Ready (basic implementation)
**Returns:** `{ data, isConnected, send }`

---

## 📋 COMPONENT BUILD MATRIX (Week 2)

### Week 2 Components (7 New)

| # | Component | Type | Purpose | Status | Est. Time | Test Target |
|---|-----------|------|---------|--------|-----------|-------------|
| 1 | MetricCard | Reusable | Display KPI with trend | 📍 TODO | 90 min | >80% |
| 2 | SalesChart | Chart | Sales over time (Line) | 📍 TODO | 120 min | >80% |
| 3 | PricingTable | Data Table | Plans comparison | 📍 TODO | 60 min | >80% |
| 4 | ActivityFeed | List | Real-time updates | 📍 TODO | 90 min | >80% |
| 5 | StatusMonitor | Health | Service status | 📍 TODO | 60 min | >80% |
| 6 | Header (v2) | Navigation | Enhanced header | 📍 ENHANCE | 30 min | >80% |
| 7 | Dashboard | Container | Main layout | 📍 TODO | 120 min | >80% |

---

## 📊 DETAILED COMPONENT SPECS

### [NEW] MetricCard Component

**Purpose:** Reusable card for displaying KPIs

**Props:**
```typescript
interface MetricCardProps {
  icon: React.ReactNode;      // Icon component
  label: string;              // "Revenue", "Sales", etc.
  value: number | string;     // "R$ 125.4K"
  trend?: number;             // 12 (percentage change)
  trendUp?: boolean;          // true for up trend
  color?: 'green' | 'red' | 'blue';
  onClick?: () => void;
}
```

**Usage Examples:**
```tsx
<MetricCard
  icon={<DollarIcon />}
  label="Today's Revenue"
  value="R$ 45.2K"
  trend={12}
  trendUp={true}
  color="green"
/>
```

**Expected Instances on Dashboard:**
- Revenue (total)
- Sales (count)
- Average Order Value
- Conversion Rate

---

### [NEW] SalesChart Component

**Purpose:** Visualize sales trends over time

**Props:**
```typescript
interface SalesChartProps {
  period?: 'day' | 'week' | 'month';  // default: 'week'
  refreshInterval?: number;            // ms, default: 30000 (30s)
}
```

**Data Source:** `/api/sales` (with timestamp)

**Library:** chart.js + react-chartjs-2

**Expected Chart:**
- X-axis: Dates (rolling last 7/30 days)
- Y-axis: Sales count
- Line chart with gradient fill
- Tooltip on hover

**Performance:**
- Limit to 30 data points max
- Paginate if more data needed

---

### [NEW] PricingTable Component

**Purpose:** Display pricing plans in tabular format

**Props:**
```typescript
interface PricingTableProps {
  highlightPlan?: string;  // e.g., "Professional"
}
```

**Data Source:** `/api/tarifas`

**Features:**
- 3-column table (one per plan)
- Feature comparison rows
- "Most Popular" badge
- CTA button per plan
- Responsive (stacks on mobile)

**Expected Layout:**
```
┌─────────────────────────────────┐
│ Básico | Professional | Enterprise
│ R$299  | R$899        | R$2999
│ Feature 1: ✓ | ✓ | ✓
│ Feature 2: ✗ | ✓ | ✓
│ Feature 3: ✗ | ✗ | ✓
│ [CTA]  | [CTA] (highlight) | [CTA]
└─────────────────────────────────┘
```

---

### [NEW] ActivityFeed Component

**Purpose:** Show real-time sales notifications

**Data Source:** WebSocket (useWebSocket hook)

**Features:**
- Auto-scrolls to new items
- Max 10 visible (scrollable)
- Time-relative formatting ("2 min ago")
- Skeleton loading state
- No data state

**Expected Item Format:**
```
New sale: USD 500
2 min ago

New customer signup
5 min ago
```

---

### [NEW] StatusMonitor Component

**Purpose:** Health check dashboard

**Endpoints:**
- `/api/health` (API status)
- Derived: DB status (from health endpoint)
- Derived: Cache status (from health endpoint)

**Features:**
- 3 service boxes (API, DB, Cache)
- Status indicator (🟢 OK / 🟡 SLOW / 🔴 DOWN)
- Response time displayed
- Last check timestamp
- Auto-refresh every 10s

**Expected Display:**
```
API Status         DB Status      Cache Status
🟢 OK              🟢 OK          🟢 OK
45ms               12ms           8ms
Last: 2 min ago    Last: 2 min ago Last: 2 min ago
```

---

### [ENHANCED] Header Component (v2)

**Current:** Basic navigation
**Add in Week 2:**
- Theme toggle button (light/dark)
- User menu dropdown
- Logo refinement
- Mobile hamburger menu

---

### [NEW] Dashboard Container

**Purpose:** Main layout grid

**Structure:**
```
┌─────────────────────────────────┐
│         Header (full width)     │
├──────────────────┬──────────────┤
│  Metrics (4x)    │ Status       │
│  [Card] [Card]   │ Monitor      │
│  [Card] [Card]   │              │
├──────────────────┼──────────────┤
│    Sales Chart (full width)     │
├──────────────────┬──────────────┤
│  Activity Feed   │ Pricing      │
│  (10 items)      │ Table        │
│                  │              │
└──────────────────┴──────────────┘
```

**Breakpoints:**
- Desktop (1024px+): 2-column
- Tablet (768px-1023px): 1.5-column (sidebar)
- Mobile (320px-767px): 1-column stacked

**Theme:** Dark mode toggle via Context

---

## 🧪 TESTING REQUIREMENTS

### By Component

| Component | Unit Tests | Snapshot | Integration |
|-----------|-----------|----------|-------------|
| MetricCard | 3 | Yes | - |
| SalesChart | 2 | Yes | API mock |
| PricingTable | 2 | Yes | API mock |
| ActivityFeed | 2 | Yes | WebSocket mock |
| StatusMonitor | 2 | Yes | API mock |
| Header (v2) | 2 | Yes | - |
| Dashboard | 1 | Yes | All children |

**Total Tests Target:** 14+ unit tests, 6+ snapshots

---

## 📦 DEPENDENCIES TO ADD

```json
{
  "chart.js": "^4.4.0",
  "react-chartjs-2": "^5.2.0",
  "zustand": "^4.4.0",          // Optional: state management
  "framer-motion": "^10.16.0",  // Optional: animations
  "recharts": "^2.10.0"         // Alternative to chart.js
}
```

**Recommendation:** Start with chart.js (lighter), consider recharts if too slow

---

## 🎨 DESIGN TOKENS

### Colors (Tailwind)
```
Primary:    blue-500   (#3b82f6)
Secondary:  purple-600 (#7c3aed)
Success:    green-500  (#10b981)
Warning:    yellow-500 (#f59e0b)
Danger:     red-500    (#ef4444)
Neutral:    gray-200/gray-700 (light/dark)
```

### Typography
```
H1: 48px, bold
H2: 36px, bold
H3: 24px, semibold
Body: 16px, regular
Small: 14px, regular
```

### Spacing (4px base)
```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
```

---

## 🚀 COMPONENT CREATION TEMPLATE

For Week 2, each component follows this structure:

```
app/components/
├── ComponentName.tsx          (Main component)
├── ComponentName.types.ts     (TypeScript types)
├── ComponentName.stories.tsx  (Storybook - optional)
└── __tests__/
    └── ComponentName.test.tsx (Unit tests)
```

**File: ComponentName.tsx Template:**
```typescript
import React from 'react';
import { ComponentNameProps } from './ComponentName.types';

export const ComponentName: React.FC<ComponentNameProps> = ({
  // props destructured
}) => {
  // Implementation here
  return (
    <div data-testid="component-name">
      {/* JSX */}
    </div>
  );
};

export default ComponentName;
```

**File: ComponentName.types.ts Template:**
```typescript
export interface ComponentNameProps {
  // Props definition
  children?: React.ReactNode;
}
```

---

## 📊 COMPLETION CHECKLIST

### Week 1 Status
- [x] Header component (basic)
- [x] Button component (3 variants)
- [x] Layout structure
- [x] Home page (landing)
- [x] 5 hooks prepared
- [x] API routes (3)
- [x] Package.json configured

### Week 2 Build Checklist
- [ ] MetricCard (T8)
- [ ] SalesChart (T9)
- [ ] PricingTable (T10)
- [ ] ActivityFeed (T11)
- [ ] StatusMonitor (T12)
- [ ] Header v2 (integrated into T13)
- [ ] Dashboard Container (T13)
- [ ] All tests passing
- [ ] Lighthouse score stable
- [ ] Dark mode working
- [ ] Responsive at 3 breakpoints
- [ ] Real-time data flowing

---

## 🔗 DEPENDENCIES BETWEEN COMPONENTS

```
Dashboard (parent)
├── Header (v2)
│   └── useTheme
├── MetricCard (x4 instances)
│   └── No hooks
├── SalesChart
│   └── useSalesData → useApi
├── PricingTable
│   └── useTariffs → useApi
├── ActivityFeed
│   └── useWebSocket
└── StatusMonitor
    └── useApi → /api/health
```

**Dependency Order (build):**
1. Start with no-dependency components: MetricCard, Button enhancements
2. Then data-fetching: PricingTable, SalesChart (useApi)
3. Then real-time: ActivityFeed (useWebSocket)
4. Then composite: StatusMonitor, Dashboard
5. Finally: Header v2 (theme integration)

---

## 📝 NOTES FOR WEEK 2 EXECUTION

1. **Start simple:** MetricCard has no dependencies - good warm-up
2. **API testing:** Mock API responses in tests, use real API in dev
3. **Performance:** Monitor bundle size as dependencies add
4. **Mobile first:** Test responsive at 320px width early
5. **Accessibility:** Add `data-testid` and ARIA labels as you go
6. **Git hygiene:** One component per PR, separate feature branches

---

*Component Inventory prepared by JARVIS on 2026-03-06*
*Week 2 ready-to-build matrix*
