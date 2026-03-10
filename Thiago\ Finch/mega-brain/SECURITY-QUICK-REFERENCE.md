# Security Quick Reference Guide

**Mega Brain - Security Implementation Quick Start**

---

## 📋 Pre-Deployment Checklist

```bash
# 1. Audit dependencies
cd frontend
npm run security:audit
# ✅ Must show: 0 vulnerabilities

# 2. Build production bundle
npm run build

# 3. Test CSP in production mode
npm run start
# Open http://localhost:3000
# F12 console → must show ZERO CSP violations

# 4. Configure environment
cp .env.production.example .env.production
# Edit with your production values

# 5. Ready for deployment
# ✅ Follow DEPLOYMENT.md
```

---

## 🔐 Security Features

### Content Security Policy
```javascript
// Location: frontend/middleware.ts + next.config.js
script-src 'self' 'nonce-{random}'      // ✅ No unsafe-inline
style-src 'self'                        // ✅ No unsafe-inline
```

### CSRF Protection
```javascript
// Required for POST/PUT/PATCH/DELETE
headers: {
  'X-CSRF-Token': '<token>'  // ✅ 1 hour expiration
}

// Missing token = 403 Forbidden
```

### Rate Limiting
```
100 requests / minute / IP  // ✅ Returns 429 if exceeded
X-RateLimit-* headers       // ✅ Included in responses
```

### Input Validation
```javascript
// Location: frontend/lib/validation.ts
validateInt(value, min, max)    // ✅ Range validation
validateEmail(email)             // ✅ Email format
sanitizeString(input)            // ✅ XSS prevention
```

---

## 🚀 Quick Deploy

### Option 1: Vercel
```bash
# Install CLI
npm i -g vercel

# Login and deploy
vercel deploy --prod

# Set environment variables
vercel env add --production CSRF_SECRET <value>
vercel env add --production REDIS_HOST <value>
```

### Option 2: Docker
```bash
# Build
docker build -t mega-brain:latest .

# Run
docker run -d \
  --name mega-brain \
  --restart unless-stopped \
  -p 3000:3000 \
  --env-file .env.production \
  mega-brain:latest
```

### Option 3: Node.js Direct
```bash
# Install & build
npm ci --production
npm run build

# Run
npm run start
```

---

## 🔍 Post-Deployment Verification

### Health Check
```bash
curl https://yourdomain.com/api/health
# ✅ { "status": "healthy", ... }
```

### CSP Headers
```bash
curl -I https://yourdomain.com | grep CSP
# ✅ Content-Security-Policy: default-src 'self'; ...
```

### Rate Limiting
```bash
# Send 150 requests
for i in {1..150}; do curl -s https://yourdomain.com/api/sales > /dev/null & done
# ✅ Requests 101+ return 429 Too Many Requests
```

### CSRF Protection
```bash
curl -X POST https://yourdomain.com/api/protected
# ✅ Returns 403 Forbidden (missing CSRF token)
```

---

## 📖 Documentation Reference

| Document | Purpose | When to Use |
|----------|---------|------------|
| **DEPLOYMENT.md** | Step-by-step deployment | Deploying to production |
| **TROUBLESHOOTING.md** | Common issues & solutions | Something breaks |
| **API.md** | API endpoint docs | Building client code |
| **ARCHITECTURE.md** | System design | Understanding system |
| **SECURITY-AUDIT.md** | Security assessment | Security review |

---

## 🛠️ Environment Variables

### Required (Production)
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WEBSOCKET_URL=wss://api.yourdomain.com/ws
ALLOWED_ORIGINS=https://yourdomain.com
CSRF_SECRET=<generate-random-string>
REDIS_HOST=redis.internal
REDIS_PASSWORD=<secure-password>
```

### Optional
```bash
CSP_REPORT_URI=https://api.yourdomain.com/api/csp-report
DATABASE_URL=postgresql://...
SENTRY_DSN=https://...
```

### Generate Random Values
```bash
# CSRF Secret (32 bytes)
openssl rand -hex 32

# Redis Password
openssl rand -base64 32
```

---

## 🐛 Common Issues

### CSP Violations in Console
```
Fix: Check which resource is being blocked
Add to CSP whitelist in next.config.js
Redeploy and verify
```

### Rate Limiting Too Strict
```
Edit: frontend/middleware.ts
Change: RATE_LIMITS.default.points = 200  // was 100
Redeploy
```

### CSRF Token Errors
```
Fix: Ensure X-CSRF-Token header sent
Use: fetch('/api/csrf-token') to get fresh token
Retry request with token
```

### 500 Errors (No Details)
```
Check: Server logs for actual error
Generic error messages are by design (security)
Use request ID to find detailed logs
```

---

## 📊 Monitoring

### Key Alerts to Set Up

```
✅ CSP violations > 0 → Investigate immediately
✅ Auth failures > 50/hour → Check for attacks
✅ Rate limit hits > 100/hour → Check for abuse
✅ Error rate > 1% → Check for bugs
✅ Response time p95 > 1000ms → Performance issue
✅ CPU usage > 80% → Resource issue
✅ Memory usage > 85% → Memory leak possible
```

### Where to Check

```
Application Logs:
  docker logs mega-brain-app
  tail -f /var/log/application.log

Error Tracking:
  Sentry dashboard (if configured)

Performance:
  DataDog / New Relic dashboard

Security:
  CSP reports at CSP_REPORT_URI
```

---

## 🔄 Maintenance

### Daily
- [ ] Check error logs for issues
- [ ] Verify API responding

### Weekly
- [ ] Review security alerts
- [ ] Check rate limiting patterns

### Monthly
- [ ] Update dependencies (minor versions)
- [ ] Review and rotate secrets
- [ ] Check backup status

### Quarterly
- [ ] Major version updates
- [ ] Run security audit
- [ ] Penetration testing

---

## 🚨 Incident Response

### If Attacked / Exploited
```bash
# 1. Immediate actions
docker logs mega-brain-app | grep error

# 2. Block attacker IP (if known)
# Via Cloudflare or WAF rules

# 3. Rotate secrets
openssl rand -hex 32 > new-csrf-secret.txt
update .env with new value

# 4. Investigate
# Review logs for patterns
# Check what was accessed

# 5. Fix and redeploy
# After fix verified, redeploy
```

---

## 📞 Support

| Issue | Contact | Time |
|-------|---------|------|
| Security issue | security@yourdomain.com | 2 hrs |
| Deployment issue | @devops team | 15 mins |
| API question | #dev-help Slack | 1 hr |
| Emergency | +55 XX XXXX-XXXX | ASAP |

---

## ✅ Pre-Flight Checklist

Before going live:

```
SECURITY
[ ] npm audit shows 0 vulnerabilities
[ ] CSP headers present and correct
[ ] CSRF protection enabled
[ ] Rate limiting configured
[ ] Input validation active
[ ] Error messages generic

INFRASTRUCTURE
[ ] Database backups configured
[ ] Redis instance running
[ ] SSL/TLS certificates valid
[ ] CDN/WAF configured
[ ] Monitoring enabled
[ ] Alerting configured

DEPLOYMENT
[ ] .env.production configured
[ ] Build tested locally
[ ] Smoke tests passed
[ ] Team trained
[ ] Documentation reviewed
[ ] Incident response plan ready
```

---

## 🎯 Success Criteria

```
✅ Health check returns 200
✅ No CSP violations in console
✅ Rate limiting blocks at 101 requests/min
✅ CSRF required on POST/PUT/DELETE
✅ Invalid input returns 400
✅ Security headers present
✅ Errors are generic (no leaks)
✅ Response time < 1 second
✅ Zero unhandled exceptions
✅ Monitoring dashboard shows metrics
```

---

## 📚 Full Documentation

For detailed information, see:

- **Full Security Audit:** `SECURITY-AUDIT.md`
- **Deployment Guide:** `DEPLOYMENT.md`
- **Troubleshooting:** `TROUBLESHOOTING.md`
- **API Reference:** `API.md`
- **System Design:** `ARCHITECTURE.md`
- **Implementation Status:** `IMPLEMENTATION-COMPLETE.md`

---

**Last Updated:** 2026-03-06
**Version:** 1.0.0
**Status:** ✅ Production Ready
