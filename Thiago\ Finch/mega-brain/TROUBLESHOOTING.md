# Troubleshooting Guide - Mega Brain

**Common Issues & Solutions for Production Support**

---

## Table of Contents

1. [Application Issues](#application-issues)
2. [Security Issues](#security-issues)
3. [Performance Issues](#performance-issues)
4. [Database Issues](#database-issues)
5. [Deployment Issues](#deployment-issues)
6. [API Issues](#api-issues)
7. [Infrastructure Issues](#infrastructure-issues)

---

## Application Issues

### Issue: Application Won't Start

**Symptoms:**
```
Error: ENOENT: no such file or directory
Error: Cannot find module 'next'
```

**Diagnosis:**
```bash
# Check if node_modules exists
ls -la node_modules/

# Check if npm scripts are readable
cat package.json | grep '"start"'

# Try to start with debugging
npm run build --verbose
npm run start --verbose
```

**Solutions:**

1. **Reinstall dependencies:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Clear Next.js cache:**
   ```bash
   rm -rf .next
   npm run build
   ```

3. **Check Node.js version:**
   ```bash
   node --version
   # Should be >= 18.0.0
   ```

4. **Verify environment variables:**
   ```bash
   # Check if .env file exists
   ls -la .env
   # Should show file exists
   ```

---

### Issue: Pages Load Slowly

**Symptoms:**
- First Contentful Paint (FCP) > 3s
- Time to Interactive (TTI) > 5s
- User reports slow navigation

**Diagnosis:**
```bash
# Run Lighthouse audit
npm run lighthouse:local

# Check bundle size
npm run analyze

# Monitor in real-time
docker logs mega-brain-app | grep "duration"
```

**Solutions:**

1. **Optimize bundle:**
   ```bash
   # Next.js automatically optimizes, but check:
   npm run build --profile
   # Review output for large chunks
   ```

2. **Enable compression:**
   ```javascript
   // next.config.js - already configured
   // Verify: gzip compression is enabled
   ```

3. **Cache optimization:**
   ```javascript
   // Check Cache-Control headers
   // For API: 'no-store, max-age=0' (correct for dynamic data)
   // For static assets: cache indefinitely
   ```

4. **Database query optimization:**
   ```sql
   -- Analyze slow queries
   SELECT * FROM mysql.slow_log;

   -- Add indexes if needed
   CREATE INDEX idx_sales_date ON sales(created_at);
   ```

---

### Issue: White Blank Page on Load

**Symptoms:**
- Browser shows blank white page
- No errors in console
- Network tab shows successful responses

**Diagnosis:**
```bash
# Check browser console (F12)
# Should show no errors

# Check application logs
docker logs mega-brain-app

# Check network requests
# Open DevTools → Network tab
# Look for failed requests or errors
```

**Solutions:**

1. **Clear browser cache:**
   ```
   Ctrl+Shift+Delete (Windows)
   Cmd+Shift+Delete (Mac)
   ```

2. **Hard refresh:**
   ```
   Ctrl+Shift+R (Windows)
   Cmd+Shift+R (Mac)
   ```

3. **Check CSS loading:**
   ```javascript
   // In browser console:
   document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
     console.log(link.href, link.sheet ? 'loaded' : 'failed');
   });
   ```

4. **Verify Tailwind CSS:**
   ```bash
   npm run build
   # Check if CSS is compiled in .next/static/css/
   ```

---

## Security Issues

### Issue: CSP Violations in Console

**Symptoms:**
```
Refused to load the script because it violates the
Content-Security-Policy directive
```

**Diagnosis:**
```bash
# Check CSP headers
curl -I https://yourdomain.com

# Look for Content-Security-Policy header
# Identify which resources are being blocked
# Check browser console (F12) for detailed errors
```

**Solutions:**

1. **For inline scripts:**
   ```javascript
   // next.config.js
   // Verify nonce is being used:
   // script-src 'nonce-{nonce}'
   ```

2. **For external resources:**
   ```javascript
   // Add to CSP in next.config.js
   "connect-src 'self' https: wss: https://external-api.com"
   ```

3. **Report CSP violations:**
   ```javascript
   // CSP violations are reported to:
   // CSP_REPORT_URI in .env
   // Review reports to identify issues
   ```

---

### Issue: CSRF Token Validation Fails

**Symptoms:**
```
Received error: Invalid CSRF token
POST request returns 403 Forbidden
```

**Diagnosis:**
```bash
# Check if CSRF token is being sent
curl -X POST https://yourdomain.com/api/endpoint \
  -H "X-CSRF-Token: $TOKEN" \
  -H "Content-Type: application/json"

# Should return 403 if token is invalid
```

**Solutions:**

1. **Get fresh CSRF token:**
   ```javascript
   // Frontend should request token before POST
   const token = await fetch('/api/csrf-token').then(r => r.json());

   // Include in request headers
   headers: { 'X-CSRF-Token': token }
   ```

2. **Check token expiration:**
   ```bash
   # CSRF tokens expire after 1 hour
   # Refresh if request fails:
   if (error.status === 403) {
     const newToken = await fetch('/api/csrf-token');
     // Retry with new token
   }
   ```

3. **Verify middleware:**
   ```bash
   # Check if middleware.ts is being applied
   grep -r "X-CSRF-Token" .
   # Should see validation in middleware.ts
   ```

---

### Issue: Rate Limiting Too Aggressive

**Symptoms:**
```
Error 429: Too Many Requests
Legitimate users getting rate limited
```

**Diagnosis:**
```bash
# Check rate limit headers
curl -I https://yourdomain.com/api/sales?hours=24

# Look for:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 99
# X-RateLimit-Reset: 1234567890
```

**Solutions:**

1. **Increase rate limit:**
   ```typescript
   // frontend/middleware.ts
   const RATE_LIMITS = {
     default: { points: 200, duration: 60 }, // Increase from 100 to 200
     api: { points: 500, duration: 60 },
   }
   ```

2. **Bypass rate limiting for specific IPs:**
   ```typescript
   // Add to checkRateLimit function
   if (trustedIps.includes(clientIp)) {
     return { allowed: true, remaining: limit.points };
   }
   ```

3. **Disable for development:**
   ```bash
   # In development, bypass rate limiting
   DISABLE_RATE_LIMIT=true npm run dev
   ```

---

## Performance Issues

### Issue: High CPU Usage

**Symptoms:**
- CPU consistently > 80%
- Application slow even with low traffic
- Server is unresponsive

**Diagnosis:**
```bash
# Check process usage
docker stats mega-brain-app

# Check system resources
top
# Look for Node process using high CPU

# Check application logs
docker logs mega-brain-app | tail -50
# Look for error loops or infinite recursion
```

**Solutions:**

1. **Profile application:**
   ```bash
   # Node.js profiling
   node --prof app.js
   node --prof-process isolate-*.log > profile.txt
   ```

2. **Identify hot spots:**
   ```bash
   # Monitor function calls
   npm install --save-dev clinic
   clinic doctor -- npm run start
   ```

3. **Optimize database queries:**
   ```sql
   -- Find slow queries
   SHOW SLOW QUERY LOG;

   -- Analyze query
   EXPLAIN SELECT * FROM sales WHERE created_at > NOW() - INTERVAL 1 DAY;

   -- Add indexes
   CREATE INDEX idx_created_at ON sales(created_at);
   ```

---

### Issue: Memory Leak

**Symptoms:**
- Memory usage increases over time
- Eventually crashes with OOM error
- Process memory never decreases

**Diagnosis:**
```bash
# Monitor memory
watch -n 1 'docker stats mega-brain-app'

# Take heap snapshot
node -e "require('v8').writeHeapSnapshot('heap.heapsnapshot')"

# Analyze with Chrome DevTools
# Open chrome://inspect, connect to process
```

**Solutions:**

1. **Clear connection pools:**
   ```bash
   # Restart Redis
   docker exec redis-container redis-cli FLUSHALL
   ```

2. **Review code for leaks:**
   ```javascript
   // Check for:
   // - Circular references
   // - Event listeners not removed
   // - Timers not cleared
   // - Large objects retained
   ```

3. **Increase memory limit:**
   ```bash
   # In Docker
   docker run -m 2g mega-brain-app

   # In Node.js
   NODE_OPTIONS="--max-old-space-size=2048" npm run start
   ```

---

## Database Issues

### Issue: Database Connection Timeout

**Symptoms:**
```
Error: ECONNREFUSED 127.0.0.1:5432
Error: connection timeout
```

**Diagnosis:**
```bash
# Test database connection
psql -h db.internal -U mega_brain_user -d mega_brain

# Check database logs
tail -f /var/log/postgresql/postgresql.log

# Verify network connectivity
ping db.internal
telnet db.internal 5432
```

**Solutions:**

1. **Check database is running:**
   ```bash
   docker ps | grep postgres

   # If not running, start it
   docker start postgres-container
   ```

2. **Verify connection string:**
   ```bash
   # Check DATABASE_URL format
   # Should be: postgresql://user:pass@host:port/dbname?sslmode=require

   # Verify credentials
   psql -h db.internal -U mega_brain_user -d mega_brain -c "SELECT 1"
   ```

3. **Increase connection pool:**
   ```javascript
   // In application
   const pool = new Pool({
     max: 20, // Increase from 10
     idleTimeoutMillis: 30000,
     connectionTimeoutMillis: 2000,
   });
   ```

---

### Issue: Slow Database Queries

**Symptoms:**
- API response time > 1000ms
- Database CPU usage high
- Timeout errors

**Diagnosis:**
```bash
# Enable slow query log
SET SESSION long_query_time = 2;

# Find slow queries
SELECT * FROM mysql.slow_log;

# Analyze query plan
EXPLAIN SELECT * FROM sales WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY);
```

**Solutions:**

1. **Add indexes:**
   ```sql
   -- Identify columns in WHERE clauses
   CREATE INDEX idx_created_at ON sales(created_at);
   CREATE INDEX idx_user_id ON sales(user_id);
   CREATE INDEX idx_status ON sales(status);
   ```

2. **Denormalize if needed:**
   ```sql
   -- If joins are slow, consider denormalization
   ALTER TABLE sales ADD COLUMN user_name VARCHAR(255);
   -- Maintain with triggers
   ```

3. **Partition large tables:**
   ```sql
   -- For tables > 1GB, partition by date
   ALTER TABLE sales
   PARTITION BY RANGE (YEAR(created_at)) (
     PARTITION p2024 VALUES LESS THAN (2025),
     PARTITION p2025 VALUES LESS THAN (2026)
   );
   ```

---

## Deployment Issues

### Issue: Build Fails

**Symptoms:**
```
npm ERR! code 1
FAIL  .../src/pages/api/index.ts
error: TypeScript compilation failed
```

**Diagnosis:**
```bash
# Run build with details
npm run build --verbose

# Check for TypeScript errors
npx tsc --noEmit

# Verify dependencies
npm list
```

**Solutions:**

1. **Fix TypeScript errors:**
   ```bash
   # Check for missing types
   npm install --save-dev @types/express @types/node

   # Fix compilation
   npx tsc --noEmit
   ```

2. **Clear cache:**
   ```bash
   rm -rf .next
   rm -rf node_modules/.cache
   npm run build
   ```

3. **Check environment variables:**
   ```bash
   # Ensure all required env vars are defined
   env | grep NEXT_
   # Should see NEXT_PUBLIC_API_URL, etc.
   ```

---

### Issue: Deployment Hangs

**Symptoms:**
- Deployment doesn't complete
- No error messages
- Process appears stuck

**Diagnosis:**
```bash
# Check deployment process
ps aux | grep deploy

# Check for hanging connections
lsof -p <PID>

# Monitor system resources
top
free -m
```

**Solutions:**

1. **Kill hung process:**
   ```bash
   kill -9 <deployment-pid>
   ```

2. **Increase timeout:**
   ```bash
   # In Vercel, check:
   # Project Settings → Build & Development
   # Increase function timeout
   ```

3. **Check for large files:**
   ```bash
   # Remove unnecessary files
   find . -name "*.log" -delete
   find . -name ".DS_Store" -delete
   ```

---

## API Issues

### Issue: API Returns 500 Error

**Symptoms:**
```
Error: Internal Server Error
No details provided
```

**Diagnosis:**
```bash
# Check server logs
docker logs mega-brain-app

# Look for:
# - Stack traces
# - Database errors
# - Unhandled exceptions
```

**Solutions:**

1. **Check request format:**
   ```bash
   # Verify headers
   curl -X GET https://yourdomain.com/api/sales?hours=24 \
     -H "X-CSRF-Token: valid-token"

   # Check response headers
   curl -I https://yourdomain.com/api/sales?hours=24
   ```

2. **Enable detailed error logging:**
   ```javascript
   // In app, add detailed logging
   console.error('[API]', {
     endpoint: request.url,
     method: request.method,
     error: error.message,
     stack: error.stack,
   });
   ```

3. **Restart application:**
   ```bash
   docker restart mega-brain-app
   ```

---

### Issue: API Response Slow

**Symptoms:**
- API response time > 2000ms
- Timeout on client side
- User complaints about slow data loading

**Solutions:**

1. **Enable caching:**
   ```javascript
   // Add Cache-Control header
   response.headers.set('Cache-Control', 'public, max-age=60');
   ```

2. **Implement pagination:**
   ```javascript
   // Limit response size
   const data = results.slice(0, 100);
   ```

3. **Add database optimization:**
   ```sql
   -- Analyze query
   EXPLAIN ANALYZE SELECT * FROM sales LIMIT 100;
   ```

---

## Infrastructure Issues

### Issue: Redis Connection Fails

**Symptoms:**
```
Error: ECONNREFUSED 127.0.0.1:6379
Redis not responding
```

**Diagnosis:**
```bash
# Check if Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli ping
# Should return PONG

# Check Redis logs
docker logs redis-container
```

**Solutions:**

1. **Restart Redis:**
   ```bash
   docker restart redis-container
   ```

2. **Check Redis configuration:**
   ```bash
   # Verify bind address
   redis-cli CONFIG GET bind
   # Should include 0.0.0.0 or correct IP
   ```

3. **Clear Redis cache:**
   ```bash
   redis-cli FLUSHALL
   # Warning: Clears ALL keys
   ```

---

### Issue: Disk Space Low

**Symptoms:**
```
No space left on device
Cannot write logs
```

**Diagnosis:**
```bash
# Check disk usage
df -h

# Find large files
du -sh /*
find / -type f -size +100M 2>/dev/null

# Check Docker volumes
docker volume ls
docker volume inspect mega-brain-data
```

**Solutions:**

1. **Clean old logs:**
   ```bash
   # Archive logs
   gzip /var/log/application.log

   # Delete old files
   find /logs -name "*.log" -mtime +30 -delete
   ```

2. **Clean Docker:**
   ```bash
   # Remove unused images
   docker image prune -a

   # Remove unused volumes
   docker volume prune
   ```

3. **Expand disk:**
   ```bash
   # Cloud: Resize EBS volume
   # On-prem: Add storage
   ```

---

## Getting Help

If issues persist:

1. **Gather diagnostics:**
   ```bash
   # Create diagnostics bundle
   ./scripts/gather-diagnostics.sh > diagnostics.tar.gz

   # Include:
   # - System info
   # - Application logs
   # - Config (without secrets)
   # - Error messages
   ```

2. **Contact support:**
   - Email: support@yourdomain.com
   - Slack: #incident-response
   - Phone: +55 XX XXXX-XXXX (emergency only)

3. **Provide information:**
   - When did the issue start?
   - What changed recently?
   - Error messages?
   - System resources used?
   - Recent deployments?

---

**Last Updated:** 2026-03-06
**Status:** Complete
