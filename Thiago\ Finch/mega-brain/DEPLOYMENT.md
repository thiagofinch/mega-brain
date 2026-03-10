# Deployment Runbook - Mega Brain

**Production Deployment Guide for Week 4 Launch**

---

## Pre-Deployment Checklist

### Security Requirements
- [ ] All npm vulnerabilities fixed (`npm audit --audit-level=high` shows zero issues)
- [ ] Next.js upgraded to 16.1.6+
- [ ] CSP headers hardened (no unsafe-inline, no unsafe-eval)
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] Authentication guards on protected routes
- [ ] Error messages don't leak sensitive information
- [ ] Environment variables properly configured
- [ ] Secrets rotated (API keys, passwords, etc.)

### Infrastructure Requirements
- [ ] Database backups configured
- [ ] Redis instance running (for rate limiting)
- [ ] SSL/TLS certificates installed (min TLS 1.3)
- [ ] CDN/WAF configured (Cloudflare recommended)
- [ ] Monitoring & alerting enabled
- [ ] Log aggregation configured
- [ ] DDoS protection enabled
- [ ] Database migrations tested

### Configuration Requirements
- [ ] `.env.production` file created with all required variables
- [ ] Secrets Manager integration tested
- [ ] Database connection string verified
- [ ] API keys validated
- [ ] CORS origins whitelisted
- [ ] CSP report URI configured
- [ ] Rate limiting thresholds set

---

## Step-by-Step Deployment

### 1. Pre-Deployment Verification

```bash
# 1.1 Clone and navigate to repository
cd /path/to/mega-brain

# 1.2 Verify git is clean
git status
# Should show no uncommitted changes

# 1.3 Create deployment branch
git checkout -b deploy/week-4-production
```

### 2. Install & Test

```bash
# 2.1 Install dependencies
cd frontend
npm ci --production

# 2.2 Run security audit
npm run security:audit
# Must report ZERO high severity vulnerabilities

# 2.3 Run build
npm run build

# 2.4 Test locally in production mode
npm run start
# Visit http://localhost:3000 and verify
# - No CSP errors in console
# - All pages load correctly
# - API endpoints respond
```

### 3. Configure Production Environment

```bash
# 3.1 Create production environment file
cat > .env.production << 'EOF'
# Application
NODE_ENV=production
NEXT_PUBLIC_BUILD_TIME=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# API Configuration
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WEBSOCKET_URL=wss://api.yourdomain.com/ws

# Security
CSRF_SECRET=$(openssl rand -hex 32)
API_KEY_SECRET=$(openssl rand -hex 32)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis
REDIS_HOST=redis.internal
REDIS_PORT=6379
REDIS_PASSWORD=<secure-password>
REDIS_SSL=true

# CSP Reporting
CSP_REPORT_URI=https://api.yourdomain.com/api/csp-report

# Database
DATABASE_URL=postgresql://user:password@db.internal:5432/mega_brain?sslmode=require

# Monitoring
SENTRY_DSN=<sentry-dsn-if-using>
EOF

# 3.2 Verify environment file
cat .env.production
# Verify all values are set and no secrets are exposed

# 3.3 Ensure .env.production is gitignored
echo ".env.production" >> .gitignore
```

### 4. Database Preparation

```bash
# 4.1 Verify database connection
node scripts/test-db-connection.js

# 4.2 Run database migrations
npm run migrate:prod

# 4.3 Seed initial data (if needed)
npm run seed:prod

# 4.4 Verify database state
npm run verify:db

# 4.5 Create backup before migration
mysqldump mega_brain > backup-pre-deployment-$(date +%s).sql
```

### 5. Build & Package

```bash
# 5.1 Build Next.js application
npm run build

# 5.2 Verify build output
ls -la .next
# Should contain: app, cache, server, static, etc.

# 5.3 Create production-ready bundle
npm run build --profile
# Analyze bundle size

# 5.4 Generate build manifest
node -e "console.log(require('package.json').version)" > VERSION.txt
```

### 6. Docker (if using containers)

```bash
# 6.1 Build Docker image
docker build -t mega-brain:latest -f Dockerfile .

# 6.2 Test Docker image locally
docker run -p 3000:3000 \
  --env-file .env.production \
  mega-brain:latest

# 6.3 Push to registry
docker push mega-brain:latest
docker tag mega-brain:latest mega-brain:v$(cat VERSION.txt)
docker push mega-brain:v$(cat VERSION.txt)
```

### 7. Deploy to Production

#### Option A: Vercel Deployment

```bash
# 7A.1 Install Vercel CLI
npm i -g vercel

# 7A.2 Login to Vercel
vercel login

# 7A.3 Configure environment variables
vercel env add --production REDIS_HOST redis.internal
vercel env add --production REDIS_PASSWORD <secure-password>
# ... repeat for all environment variables

# 7A.4 Deploy
vercel deploy --prod

# 7A.5 Verify deployment
curl https://yourdomain.com/api/health
```

#### Option B: AWS/Docker Deployment

```bash
# 7B.1 SSH into production server
ssh -i deploy-key.pem ubuntu@prod.yourdomain.com

# 7B.2 Clone repository
git clone https://github.com/org/mega-brain.git
cd mega-brain

# 7B.3 Copy environment file
scp -i deploy-key.pem .env.production ubuntu@prod.yourdomain.com:~/mega-brain/

# 7B.4 Pull latest image
docker pull mega-brain:latest

# 7B.5 Stop old container
docker stop mega-brain-app || true
docker rm mega-brain-app || true

# 7B.6 Run new container
docker run -d \
  --name mega-brain-app \
  --restart unless-stopped \
  -p 3000:3000 \
  --env-file .env.production \
  -v /data/logs:/app/logs \
  mega-brain:latest

# 7B.7 Verify running
docker logs mega-brain-app
docker ps | grep mega-brain
```

### 8. Post-Deployment Verification

```bash
# 8.1 Health check
curl https://yourdomain.com/api/health
# Expected: {"status":"healthy","timestamp":"...","version":"..."}

# 8.2 Check for CSP violations
# Visit https://yourdomain.com in browser
# Open DevTools Console (F12)
# Should see NO CSP violations

# 8.3 Verify CSRF protection
curl -X POST https://yourdomain.com/api/protected \
  -H "Content-Type: application/json"
# Expected: 403 Forbidden (missing CSRF token)

# 8.4 Test rate limiting
# Send 100+ requests in quick succession
for i in {1..150}; do
  curl -s https://yourdomain.com/api/sales?hours=24 > /dev/null &
done
wait
# Around request 101, should get 429 Too Many Requests

# 8.5 Check security headers
curl -I https://yourdomain.com
# Verify:
# - Strict-Transport-Security
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - Content-Security-Policy

# 8.6 Verify SSL/TLS
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
# Should show TLS 1.3 or higher

# 8.7 Check database connection
npm run test:db-prod

# 8.8 Monitor logs
docker logs -f mega-brain-app
# Should show no errors
```

### 9. Smoke Tests

```bash
# 9.1 Test API endpoints
curl https://yourdomain.com/api/health
curl https://yourdomain.com/api/sales?hours=24
curl https://yourdomain.com/api/tarifas

# 9.2 Test frontend
# Open https://yourdomain.com in browser
# - Page loads completely
# - No console errors
# - Charts render correctly
# - Dark mode toggle works

# 9.3 Test WebSocket (if applicable)
# Test real-time updates
npm run test:websocket

# 9.4 Performance check
# Run Lighthouse audit
npm run lighthouse:prod

# 9.5 Security check
# Run security scan
npm run security:snyk
```

### 10. Monitoring & Alerting Setup

```bash
# 10.1 Enable performance monitoring
# Create monitoring dashboard in:
# - Datadog / New Relic / CloudWatch
# - Track: response times, error rates, resource usage

# 10.2 Set up alerts
# Alert if:
# - Error rate > 1%
# - Response time p95 > 1000ms
# - CPU usage > 80%
# - Memory usage > 85%
# - Disk space < 10%
# - Database connection pool exhausted

# 10.3 Configure log aggregation
# Logs should go to centralized service:
# - CloudWatch, DataDog, Splunk, etc.
# - Include: access logs, error logs, security logs

# 10.4 Set up error reporting
# If using Sentry:
sentry-cli login
sentry-cli releases create mega-brain@$(cat VERSION.txt)
```

---

## Rollback Procedure

If issues arise after deployment:

```bash
# 1. Immediate rollback
docker stop mega-brain-app
docker run -d \
  --name mega-brain-app \
  --restart unless-stopped \
  -p 3000:3000 \
  --env-file .env.production \
  mega-brain:previous-stable-version

# 2. Restore from backup
mysql mega_brain < backup-pre-deployment-TIMESTAMP.sql

# 3. Verify rollback
curl https://yourdomain.com/api/health

# 4. Notify team
# Send incident notification to team
```

---

## Production Maintenance

### Weekly Tasks
- [ ] Review error logs for anomalies
- [ ] Check security alert emails
- [ ] Monitor disk space (clear old logs if needed)
- [ ] Verify backups completed successfully

### Monthly Tasks
- [ ] Run security audit (npm audit)
- [ ] Update dependencies (minor versions)
- [ ] Review and rotate secrets
- [ ] Test backup restoration
- [ ] Performance review (response times, etc.)

### Quarterly Tasks
- [ ] Major dependency updates (major versions)
- [ ] Security penetration test
- [ ] Capacity planning review
- [ ] Disaster recovery drill

---

## Troubleshooting Common Issues

### Issue: CSP Violations in Production

**Symptoms:** Errors in browser console about blocked resources

**Solution:**
1. Identify which resources are being blocked
2. Add to CSP whitelist in next.config.js
3. Redeploy with `npm run build && npm run start`
4. Verify no violations in console

### Issue: Rate Limiting Too Strict

**Symptoms:** Legitimate users getting 429 errors

**Solution:**
1. Adjust rate limits in middleware.ts
2. Increase RATE_LIMITS.default.points
3. Redeploy and test

### Issue: Database Connection Errors

**Symptoms:** API returns 500, logs show "connection timeout"

**Solution:**
1. Verify Redis is running: `redis-cli ping`
2. Check DATABASE_URL is correct
3. Verify database is accessible from production server
4. Check firewall rules
5. Restart container: `docker restart mega-brain-app`

### Issue: High Memory Usage

**Symptoms:** Container crashes due to OOM

**Solution:**
1. Check for memory leaks in logs
2. Increase Docker memory limit
3. Clear Redis cache: `redis-cli FLUSHALL`
4. Restart application

---

## Security Checklist (Post-Deployment)

- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] CSP headers present and strict
- [ ] CSRF tokens required for state changes
- [ ] Rate limiting working (429 after limit exceeded)
- [ ] Authentication required for protected endpoints
- [ ] Sensitive data not logged
- [ ] Error messages generic (don't leak info)
- [ ] Database backups automated
- [ ] SSL certificates auto-renewed
- [ ] Security headers audit passed
- [ ] OWASP Top 10 vulnerabilities checked

---

## Support & Escalation

**Critical Issues** (service down):
- Contact: @devops team
- Response time: 15 minutes

**Security Issues:**
- Contact: security@yourdomain.com
- Follow: SECURITY.md incident response

**Performance Issues:**
- Contact: @infrastructure team
- Check: Monitoring dashboards first

---

**Last Updated:** 2026-03-06
**Deployment Version:** 1.0.0
**Status:** Ready for Week 4 Production Launch
