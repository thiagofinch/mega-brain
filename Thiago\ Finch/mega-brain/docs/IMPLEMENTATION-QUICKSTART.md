# IMPLEMENTATION QUICKSTART - Dashboard Real-Time

> **Para:** Data Engineer
> **Duração:** 4-5 semanas
> **Baseline:** ARCHITECTURE.md (leia primeiro)

---

## Day 1: Infrastructure Setup (AWS)

### Step 1: PostgreSQL RDS

```bash
# Via Terraform
terraform init
terraform apply -var="env=production"

# Or via AWS CLI
aws rds create-db-instance \
  --db-instance-identifier dashboard-live \
  --db-instance-class db.t4g.large \
  --engine postgres \
  --engine-version 15.2 \
  --allocated-storage 100 \
  --storage-type gp3 \
  --master-username postgres \
  --master-user-password $(openssl rand -base64 32) \
  --backup-retention-period 7 \
  --multi-az \
  --enable-cloudwatch-logs-exports postgresql

# Wait for status: "available" (5-10 min)
aws rds describe-db-instances \
  --db-instance-identifier dashboard-live \
  --query 'DBInstances[0].DBInstanceStatus'

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier dashboard-live \
  --query 'DBInstances[0].Endpoint.Address'
# Output: dashboard-live.xxxxxxx.rds.amazonaws.com
```

### Step 2: Redis ElastiCache

```bash
# Via AWS CLI
aws elasticache create-cache-cluster \
  --cache-cluster-id dashboard-cache \
  --cache-node-type cache.t4g.medium \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --port 6379 \
  --cache-parameter-group-name default.redis7 \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled

# Wait for status: "available"
aws elasticache describe-cache-clusters \
  --cache-cluster-id dashboard-cache \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint'
# Output: dashboard-cache.xxxxxxx.ng.0001.use1.cache.amazonaws.com:6379
```

### Step 3: Security Groups & VPC

```bash
# Create security group for RDS
aws ec2 create-security-group \
  --group-name dashboard-rds-sg \
  --description "Dashboard PostgreSQL" \
  --vpc-id vpc-xxxxx

# Allow N8N (or your IP) to connect
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 5432 \
  --cidr 10.0.0.0/8  # N8N security group IP

# Same for Redis
aws ec2 create-security-group \
  --group-name dashboard-redis-sg \
  --description "Dashboard Redis"

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 6379 \
  --cidr 10.0.0.0/8
```

---

## Day 2-3: Database Schema

### Step 1: Connect to RDS

```bash
# Install psql (macOS)
brew install postgresql

# Connect (use password from Step 1)
psql -h dashboard-live.xxxxxxx.rds.amazonaws.com \
     -U postgres \
     -d postgres

# Create database
CREATE DATABASE dashboard_live;
\c dashboard_live
```

### Step 2: Create Schemas

```bash
# Create public schema (default)
CREATE SCHEMA public;

# Run the SQL from ARCHITECTURE.md § 3.1
-- Copy all CREATE TABLE statements from ARCHITECTURE.md
-- Copy all CREATE INDEX statements
-- Copy all CREATE TRIGGER + FUNCTION statements

# Verify tables
\dt

# Verify indices
\di
```

### Step 3: Test Inserts

```sql
-- Test sales_live insert
INSERT INTO sales_live (
  order_id, seller_id, item_id, sku, quantity,
  unit_price_brl, final_price_brl,
  status, payment_status, shipment_status
) VALUES (
  999999999, 123456, 987654, 'SKU-001', 1,
  299.90, 299.90,
  'pending', 'pending', 'unshipped'
);

-- Verify
SELECT * FROM sales_live WHERE order_id = 999999999;
-- Should return 1 row

-- Check trigger (should log to PostgreSQL)
SELECT * FROM pg_stat_user_functions WHERE funcname = 'notify_sales_live_change';
```

### Step 4: Create Views

```sql
-- Copy all CREATE OR REPLACE VIEW statements from ARCHITECTURE.md § 3.2
-- Then test:

SELECT * FROM v_sales_daily_summary LIMIT 5;
SELECT * FROM v_sales_status_breakdown LIMIT 5;
SELECT * FROM v_top_products_24h LIMIT 5;
```

### Step 5: Verify Connection String

```bash
# Format: postgresql://user:password@host:5432/database
export DATABASE_URL="postgresql://postgres:PASSWORD@dashboard-live.xxxxxxx.rds.amazonaws.com:5432/dashboard_live"

# Test with psql
psql $DATABASE_URL -c "SELECT 1;"
# Output: ?column?
#    1

# Save to .env
echo "DATABASE_URL=$DATABASE_URL" > .env.production
```

---

## Day 3-4: Redis Setup & Testing

### Step 1: Connect to Redis

```bash
# Install redis-cli (macOS)
brew install redis

# Test connection
redis-cli -h dashboard-cache.xxxxxxx.ng.0001.use1.cache.amazonaws.com \
          -p 6379 \
          ping
# Output: PONG
```

### Step 2: Test Pub/Sub

```bash
# Terminal 1: Subscribe to channel
redis-cli SUBSCRIBE sales_live_changed

# Terminal 2: Publish message
redis-cli PUBLISH sales_live_changed '{"event":"INSERT","order_id":123}'

# Terminal 1 should receive: [message] sales_live_changed {"event":"INSERT"...}
```

### Step 3: Test Cache Operations

```bash
# Set cache keys (simulating tariffs snapshot)
redis-cli SET tariffs:2026-03-06 '{"ml_commission_pct":12.00}'
redis-cli EXPIRE tariffs:2026-03-06 300  # 5 min TTL

# Retrieve
redis-cli GET tariffs:2026-03-06

# Dedup set
redis-cli SETEX redis_meli:order:123456789 3600 1
redis-cli EXISTS redis_meli:order:123456789
```

### Step 4: Save Redis URL

```bash
# Format: redis://:password@host:6379
export REDIS_URL="redis://default:PASSWORD@dashboard-cache.xxxxxxx.ng.0001.use1.cache.amazonaws.com:6379"

echo "REDIS_URL=$REDIS_URL" >> .env.production
```

---

## Day 5-7: N8N Setup

### Step 1: Deploy N8N

```bash
# Via Docker on ECS
cat > n8n-docker-compose.yml << 'EOF'
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n-dashboard
    ports:
      - "5678:5678"
    environment:
      - DATABASE_URL=postgresql://user:pass@rds.amazonaws.com:5432/n8n
      - N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
      - WEBHOOK_TUNNEL_URL=https://n8n.yourserver.com/
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - dashboard-net

volumes:
  n8n_data:

networks:
  dashboard-net:
    driver: bridge
EOF

docker-compose up -d
```

### Step 2: Create Webhook Workflow

In N8N UI (localhost:5678):

1. **Create new workflow**
   - Name: "MercadoLivre Order Webhook"
   - Description: "Handle real-time order events"

2. **Add Webhook trigger node**
   - HTTP Method: POST
   - URL: /webhook/meli-order
   - Authentication: None (for testing; add JWT later)
   - Response: {"status":"received"}

3. **Add Dedupe node (Function)**
   ```javascript
   // Check if order already processed
   const orderId = $input.first().json.order_id;
   const redisKey = `redis_meli:order:${orderId}`;

   // In production, query Redis here
   // For now, assume dedupe passed
   return [{ json: $input.first().json, dedupe_passed: true }];
   ```

4. **Add Transform node**
   - Transform: Map data
   - Fields:
     ```
     order_id: .order_id
     seller_id: .seller.id
     item_id: .item.id
     sku: .item.sku
     quantity: .quantity
     unit_price_brl: .price
     final_price_brl: .price  // Handle discounts in step 5
     status: "pending"
     payment_status: .payment.status
     shipment_status: "unshipped"
     created_at: .timestamp
     ```

5. **Add PostgreSQL Insert node**
   - Connection: [Configure with RDS endpoint + credentials]
   - Operation: "Insert"
   - Table: sales_live
   - Columns: [map from Transform node]

6. **Add Redis Publish node**
   - Host: [ElastiCache endpoint]
   - Channel: "sales_live_changed"
   - Message: JSON stringify of order data

7. **Add Error Handler**
   - On error: Log to DataDog + alert Slack

8. **Test**
   - Click "Test Webhook"
   - Send sample JSON:
   ```json
   {
     "order_id": 123456789,
     "seller": {"id": 987654},
     "item": {"id": 111111, "sku": "SKU-001"},
     "quantity": 1,
     "price": 299.90,
     "payment": {"status": "pending"},
     "timestamp": "2026-03-06T14:30:00Z"
   }
   ```

### Step 3: Create Polling Workflow (Fallback)

1. **Create new workflow**
   - Name: "MercadoLivre Polling (5 min)"
   - Trigger: Cron (every 5 minutes)

2. **Add MercadoLivre API node**
   - Method: GET
   - URL: https://api.mercadolivre.com/orders/seller/{seller_id}
   - Params:
     - modified_after: [T-5min in ISO format]
     - status: all
   - Auth: Bearer token [MercadoLivre API key]

3. **Add Loop node**
   - For each order in response array

4. **Add Dedupe + Insert** (same as webhook flow)

---

## Day 8-10: Backend API (Next.js)

### Step 1: Setup Next.js 14

```bash
# Create project
npx create-next-app@latest dashboard \
  --typescript \
  --app \
  --no-eslint \
  --no-git

cd dashboard
```

### Step 2: Install Dependencies

```bash
npm install \
  swr \
  recharts \
  pg \
  redis \
  ws \
  tailwindcss \
  darktheme-tailwindcss

# Or use package.json
cat > package.json << 'EOF'
{
  "dependencies": {
    "next": "14.0.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "swr": "^2.2.4",
    "recharts": "^2.10.3",
    "pg": "^8.11.3",
    "redis": "^4.6.13",
    "ws": "^8.15.0"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "@types/node": "^20.10.6"
  }
}
EOF

npm install
```

### Step 3: Create Database Connection Pool

```typescript
// lib/db.ts
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,  // Max connections
  idleTimeoutMillis: 30000,
});

export async function query(text: string, params?: any[]) {
  const start = Date.now();
  const result = await pool.query(text, params);
  const duration = Date.now() - start;
  console.log(`Query executed in ${duration}ms`);
  return result;
}

export default pool;
```

### Step 4: Create Redis Connection

```typescript
// lib/redis.ts
import { createClient } from 'redis';

const redis = createClient({
  url: process.env.REDIS_URL,
});

redis.on('error', (err) => console.error('Redis error', err));

export async function getCache(key: string) {
  const value = await redis.get(key);
  return value ? JSON.parse(value) : null;
}

export async function setCache(key: string, value: any, ttl: number = 300) {
  await redis.setEx(key, ttl, JSON.stringify(value));
}

export async function publishEvent(channel: string, data: any) {
  await redis.publish(channel, JSON.stringify(data));
}

export default redis;
```

### Step 5: Create API Routes

```typescript
// app/api/sales/live/route.ts
import { query } from '@/lib/db';

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const limit = parseInt(searchParams.get('limit') ?? '50');
    const offset = parseInt(searchParams.get('offset') ?? '0');

    const result = await query(
      `SELECT id, order_id, sku, quantity, final_price_brl, status, created_at
       FROM sales_live
       WHERE created_at > NOW() - INTERVAL '24h'
       ORDER BY created_at DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    return Response.json({
      data: result.rows,
      count: result.rowCount,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('API error:', error);
    return Response.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

```typescript
// app/api/sales/daily/route.ts
import { getCache, setCache } from '@/lib/redis';
import { query } from '@/lib/db';

export async function GET() {
  try {
    // Try cache first
    const cached = await getCache('sales:daily:summary');
    if (cached) {
      return Response.json({ data: cached, cached: true });
    }

    // Query database
    const result = await query(
      `SELECT * FROM v_sales_daily_summary LIMIT 30`
    );

    // Cache for 5 minutes
    await setCache('sales:daily:summary', result.rows, 300);

    return Response.json({ data: result.rows, cached: false });
  } catch (error) {
    console.error('API error:', error);
    return Response.json(
      { error: 'Failed to fetch daily summary' },
      { status: 500 }
    );
  }
}
```

```typescript
// app/api/sales/top-products/route.ts
import { getCache, setCache } from '@/lib/redis';
import { query } from '@/lib/db';

export async function GET() {
  try {
    const cached = await getCache('sales:top:products');
    if (cached) {
      return Response.json({ data: cached, cached: true });
    }

    const result = await query(
      `SELECT * FROM v_top_products_24h LIMIT 20`
    );

    await setCache('sales:top:products', result.rows, 300);

    return Response.json({ data: result.rows, cached: false });
  } catch (error) {
    console.error('API error:', error);
    return Response.json(
      { error: 'Failed to fetch top products' },
      { status: 500 }
    );
  }
}
```

### Step 6: Create WebSocket Server

```typescript
// app/ws/route.ts
import { WebSocketServer } from 'ws';
import redis from '@/lib/redis';

const wss = new WebSocketServer({ noServer: true });

// Subscribe to Redis channel
async function subscribeToRedis(ws: any) {
  const subscriber = redis.duplicate();
  await subscriber.subscribe('sales_live_changed', (message: string) => {
    if (ws.readyState === 1) {  // OPEN
      ws.send(JSON.stringify({
        type: 'sales:new',
        data: JSON.parse(message),
        timestamp: new Date().toISOString(),
      }));
    }
  });

  ws.on('close', () => {
    subscriber.disconnect();
  });
}

export function GET(req: Request) {
  // Upgrade HTTP to WebSocket
  const head = req.headers.get('upgrade') === 'websocket' ? '' : undefined;
  if (head === undefined) {
    return new Response('Upgrade required', { status: 400 });
  }

  const ws = new WebSocket(req.url);
  subscribeToRedis(ws);

  return new Response(null, { status: 101 });
}
```

---

## Day 11-13: Frontend Dashboard

### Step 1: Create Layout with TailwindCSS

```typescript
// app/layout.tsx
import './globals.css';  // TailwindCSS

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-white dark:bg-slate-900">
        {children}
      </body>
    </html>
  );
}
```

### Step 2: Create Dashboard Main Page

```typescript
// app/page.tsx
'use client';

import { useEffect, useState } from 'react';
import useSWR from 'swr';
import SalesChart from '@/components/SalesChart';
import SalesTable from '@/components/SalesTable';
import TopProducts from '@/components/TopProducts';

const fetcher = (url: string) => fetch(url).then(r => r.json());

export default function Dashboard() {
  const { data: liveData, isLoading: liveLoading } = useSWR(
    '/api/sales/live?limit=50',
    fetcher,
    { refreshInterval: 5000 }  // Fallback poll if WS fails
  );

  const { data: dailyData, isLoading: dailyLoading } = useSWR(
    '/api/sales/daily',
    fetcher,
    { refreshInterval: 300000 }  // 5 min refresh
  );

  const { data: topProducts, isLoading: topLoading } = useSWR(
    '/api/sales/top-products',
    fetcher,
    { refreshInterval: 300000 }
  );

  return (
    <main className="p-8 bg-white dark:bg-slate-900">
      <h1 className="text-4xl font-bold mb-8">Dashboard de Vendas</h1>

      {/* Status Bar */}
      <div className="mb-8 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 rounded">
        <p className="text-green-800 dark:text-green-200">
          ✅ Sincronização em tempo real ativa
        </p>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-8 mb-8">
        <SalesChart data={dailyData?.data} loading={dailyLoading} />
        <TopProducts data={topProducts?.data} loading={topLoading} />
      </div>

      {/* Live Table */}
      <SalesTable data={liveData?.data} loading={liveLoading} />
    </main>
  );
}
```

### Step 3: Create Chart Component

```typescript
// components/SalesChart.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function SalesChart({ data, loading }: { data: any[], loading: boolean }) {
  if (loading) return <div>Loading chart...</div>;
  if (!data) return <div>No data</div>;

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">Vendas Diárias (últimos 30 dias)</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="sale_date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="total_revenue_brl" stroke="#3b82f6" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Step 4: Create WebSocket Hook

```typescript
// hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

export function useWebSocket(url: string) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData(message);

      // Also update IndexedDB for offline support
      if ('indexedDB' in window) {
        const dbRequest = indexedDB.open('dashboard', 1);
        dbRequest.onsuccess = (e) => {
          const db = (e.target as any).result;
          const tx = db.transaction('sales', 'readwrite');
          tx.objectStore('sales').add(message.data);
        };
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    return () => ws.close();
  }, [url]);

  return { data, connected };
}
```

---

## Day 14-15: Testing & Optimization

### Load Testing

```bash
# Install artillery
npm install -g artillery

# Create test config
cat > load-test.yml << 'EOF'
config:
  target: "https://yourserver.com"
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 120
      arrivalRate: 50
      name: "Ramp up"
    - duration: 60
      arrivalRate: 100
      name: "Stress test"

scenarios:
  - name: "Dashboard flow"
    flow:
      - get:
          url: "/api/sales/live"
      - get:
          url: "/api/sales/daily"
      - get:
          url: "/api/sales/top-products"

  - name: "WebSocket"
    flow:
      - ws:
          url: "wss://yourserver.com/ws"
          message: "subscribe"
EOF

# Run test
artillery run load-test.yml
```

### Latency Audit

```bash
# Measure each stage
echo "=== LATENCY AUDIT ==="

# 1. API Response Time
time curl -s https://yourserver.com/api/sales/live | jq . > /dev/null

# 2. Database Query (from N8N logs)
# Check N8N execution history

# 3. WebSocket Latency
# Browser DevTools → Network → WS tab → check message sizes/times

# 4. React Render
# Browser DevTools → Performance → Record → measure frame rates
```

### Core Web Vitals Check

```bash
# Use PageSpeed Insights API
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://yourserver.com&key=YOUR_API_KEY"

# Or use Lighthouse CLI
npm install -g lighthouse
lighthouse https://yourserver.com --output=json
```

---

## Day 16-20: Deployment

### Deploy to Vercel (Frontend)

```bash
# Install Vercel CLI
npm install -g vercel

# Link project
vercel link

# Set environment variables
vercel env add DATABASE_URL
vercel env add REDIS_URL
vercel env add NEXT_PUBLIC_WS_URL

# Deploy
vercel deploy --prod
```

### Deploy N8N on ECS

```bash
# Push Docker image to ECR
aws ecr create-repository --repository-name n8n-dashboard

docker tag n8n-meli n8n-dashboard:latest
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/n8n-dashboard:latest

# Create ECS task definition
# Update launch-type to FARGATE
# Configure CloudWatch logs
```

### Configure Monitoring

```bash
# Install DataDog agent
npm install --save datadog-browser-rum
npm install --save @datadog/browser-logs

# In Next.js _app.tsx or layout.tsx:
import { datadogRum } from '@datadog/browser-rum';

datadogRum.init({
  applicationId: 'YOUR_APP_ID',
  clientToken: 'YOUR_CLIENT_TOKEN',
  site: 'datadoghq.com',
  service: 'dashboard',
  env: 'production',
  sessionSampleRate: 100,
  sessionReplaySampleRate: 20,
  trackUserInteractions: true,
  trackResources: true,
  trackLongTasks: true,
});

datadogRum.startSessionReplayRecording();
```

---

## Post-Deployment Checklist

```
[ ] Database replication lag < 100ms
[ ] Redis memory usage < 512MB
[ ] N8N error rate < 0.1%
[ ] E2E latency P99 < 500ms
[ ] Sync success rate > 99%
[ ] Core Web Vitals all green
[ ] WebSocket connections stable
[ ] Error alerts working (PagerDuty)
[ ] Logs flowing (DataDog)
[ ] Monitoring dashboards created
[ ] Team trained on dashboard
[ ] Runbook documented
[ ] Rollback procedure tested
```

---

## Support & Monitoring

After deployment, monitor:

1. **E2E Latency** (DataDog APM)
   - Alert if P99 > 500ms

2. **Sync Success** (PostgreSQL logs)
   - Alert if < 99% in last hour

3. **WebSocket Health** (DataDog)
   - Count active connections
   - Monitor disconnects

4. **Infrastructure** (AWS CloudWatch)
   - RDS CPU/memory
   - Redis memory/CPU
   - Network throughput

5. **Application** (Next.js)
   - Core Web Vitals
   - Error rates
   - User interactions

---

**Ready to implement? Start with Day 1 and follow the checklist above. Reference ARCHITECTURE.md for detailed specs.**
