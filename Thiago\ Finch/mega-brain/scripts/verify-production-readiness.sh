#!/bin/bash

################################################################################
# PRODUCTION READINESS VERIFICATION SCRIPT
#
# Purpose: Verify all components are ready for production deployment
# Usage: ./scripts/verify-production-readiness.sh
# Status: Returns 0 if all checks pass, 1 if any check fails
################################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Utilities
echo_pass() {
  echo -e "${GREEN}✓ $1${NC}"
  ((PASSED++))
}

echo_fail() {
  echo -e "${RED}✗ $1${NC}"
  ((FAILED++))
}

echo_warn() {
  echo -e "${YELLOW}⚠ $1${NC}"
  ((WARNINGS++))
}

echo_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

echo_section() {
  echo ""
  echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
}

################################################################################
# START CHECKS
################################################################################

echo ""
echo_section "MEGA BRAIN PRODUCTION READINESS CHECK"

# ============================================================================
# 1. GIT CHECKS
# ============================================================================

echo_section "1. GIT REPOSITORY STATUS"

# Check working tree clean
if [ -z "$(git status --porcelain)" ]; then
  echo_pass "Working tree is clean"
else
  echo_fail "Working tree has uncommitted changes"
  git status --short
fi

# Check main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" = "main" ]; then
  echo_pass "On main branch"
else
  echo_warn "Not on main branch (currently on: $CURRENT_BRANCH)"
fi

# Check remote configured
if git remote show origin > /dev/null 2>&1; then
  echo_pass "GitHub remote configured"
  git remote -v | head -1
else
  echo_fail "GitHub remote not configured"
fi

# Check commits
COMMIT_COUNT=$(git log --oneline | wc -l)
if [ "$COMMIT_COUNT" -gt 0 ]; then
  echo_pass "Repository has commits (count: $COMMIT_COUNT)"
  echo_info "Latest commit: $(git log -1 --oneline)"
else
  echo_fail "No commits found"
fi

# ============================================================================
# 2. ENVIRONMENT CHECKS
# ============================================================================

echo_section "2. ENVIRONMENT & CONFIGURATION"

# Check .env exists
if [ -f .env ]; then
  echo_pass ".env file exists"
else
  echo_warn ".env file not found (needed for local testing)"
fi

# Check .env is gitignored
if git check-ignore .env > /dev/null 2>&1; then
  echo_pass ".env is gitignored"
else
  echo_warn ".env is NOT gitignored (security risk)"
fi

# Check no secrets in git history
SECRET_COUNT=$(git log -p --all | grep -i -E "sk-proj-|postgresql://|app_usr-" | wc -l)
if [ "$SECRET_COUNT" -eq 0 ]; then
  echo_pass "No hardcoded secrets found in git history"
else
  echo_fail "Found $SECRET_COUNT potential secrets in git history"
fi

# Check Node.js version
if command -v node &> /dev/null; then
  NODE_VERSION=$(node -v)
  echo_pass "Node.js installed: $NODE_VERSION"

  # Extract version number
  MAJOR_VERSION=$(echo $NODE_VERSION | cut -d'.' -f1 | cut -dv -f2)
  if [ "$MAJOR_VERSION" -ge 18 ]; then
    echo_pass "Node.js version is >= 18"
  else
    echo_warn "Node.js version is < 18 (recommended >= 18)"
  fi
else
  echo_fail "Node.js not installed"
fi

# Check npm version
if command -v npm &> /dev/null; then
  NPM_VERSION=$(npm -v)
  echo_pass "npm installed: $NPM_VERSION"
else
  echo_fail "npm not installed"
fi

# ============================================================================
# 3. FRONTEND CHECKS
# ============================================================================

echo_section "3. FRONTEND (Next.js)"

# Check frontend directory
if [ -d "frontend" ]; then
  echo_pass "Frontend directory exists"
else
  echo_fail "Frontend directory not found"
fi

# Check frontend package.json
if [ -f "frontend/package.json" ]; then
  echo_pass "Frontend package.json exists"

  # Check for required scripts
  if grep -q "\"build\"" frontend/package.json; then
    echo_pass "Build script defined"
  else
    echo_fail "Build script not found"
  fi

  if grep -q "\"dev\"" frontend/package.json; then
    echo_pass "Dev script defined"
  else
    echo_warn "Dev script not found"
  fi
else
  echo_fail "Frontend package.json not found"
fi

# Check node_modules
if [ -d "frontend/node_modules" ]; then
  MODULE_COUNT=$(ls frontend/node_modules | wc -l)
  echo_pass "Frontend dependencies installed ($MODULE_COUNT modules)"
else
  echo_warn "Frontend node_modules not found (run: cd frontend && npm ci)"
fi

# Check Next.js config
if [ -f "frontend/next.config.js" ]; then
  echo_pass "next.config.js exists"
else
  echo_warn "next.config.js not found"
fi

# Check Tailwind config
if [ -f "frontend/tailwind.config.js" ]; then
  echo_pass "tailwind.config.js exists"
else
  echo_warn "tailwind.config.js not found (styling may not work)"
fi

# ============================================================================
# 4. BACKEND CHECKS
# ============================================================================

echo_section "4. BACKEND (Express)"

# Check server.js
if [ -f "server.js" ]; then
  echo_pass "server.js exists"

  # Check for required imports
  if grep -q "express" server.js; then
    echo_pass "Express imported"
  else
    echo_fail "Express not imported in server.js"
  fi

  if grep -q "socket.io" server.js || grep -q "Socket.IO" server.js; then
    echo_pass "Socket.IO configured"
  else
    echo_warn "Socket.IO not found in server.js"
  fi

  if grep -q "cors" server.js; then
    echo_pass "CORS configured"
  else
    echo_fail "CORS not configured"
  fi
else
  echo_fail "server.js not found"
fi

# Check root package.json
if [ -f "package.json" ]; then
  echo_pass "Root package.json exists"

  # Check backend dependencies
  if grep -q "express" package.json; then
    echo_pass "Express dependency found"
  else
    echo_fail "Express dependency missing"
  fi
else
  echo_fail "Root package.json not found"
fi

# Check src directory
if [ -d "src" ]; then
  echo_pass "src directory exists"

  # Check database module
  if [ -f "src/db.js" ]; then
    echo_pass "Database module (src/db.js) exists"
  else
    echo_warn "Database module not found"
  fi
else
  echo_warn "src directory not found"
fi

# ============================================================================
# 5. DATABASE CHECKS
# ============================================================================

echo_section "5. DATABASE CONFIGURATION"

# Check database initialization file
if [ -f "scripts/schema-init.sql" ]; then
  echo_pass "Database schema file exists"

  # Check schema contains tables
  if grep -q "CREATE TABLE" scripts/schema-init.sql; then
    TABLE_COUNT=$(grep -c "CREATE TABLE" scripts/schema-init.sql)
    echo_pass "Schema contains $TABLE_COUNT table definitions"
  fi
else
  echo_warn "Database schema file not found (run: npm run setup-db)"
fi

# Check for SQLite files
if [ -f "dev.db" ]; then
  echo_info "SQLite development database found (local)"
fi

# ============================================================================
# 6. BUILD VERIFICATION
# ============================================================================

echo_section "6. BUILD VERIFICATION"

echo_info "Checking if local build succeeds..."

# Frontend build
if [ -d "frontend" ]; then
  cd frontend

  # Check if dependencies installed
  if [ -d "node_modules" ]; then
    echo_info "Frontend dependencies installed, skipping install..."
  else
    echo_info "Installing frontend dependencies..."
    npm ci > /dev/null 2>&1 || echo_warn "npm ci had issues"
  fi

  # Try to build
  if npm run build > /dev/null 2>&1; then
    echo_pass "Frontend builds successfully"

    # Check build output
    if [ -d ".next" ]; then
      NEXT_SIZE=$(du -sh .next | cut -f1)
      echo_info "Build output size: $NEXT_SIZE"
      echo_pass "Next.js build directory created"
    fi
  else
    echo_fail "Frontend build failed"
  fi

  cd ..
fi

# ============================================================================
# 7. DEPLOYMENT FILES
# ============================================================================

echo_section "7. DEPLOYMENT FILES"

# Check deployment docs
if [ -f "PRODUCTION-DEPLOYMENT-STRATEGY.md" ]; then
  echo_pass "PRODUCTION-DEPLOYMENT-STRATEGY.md exists"
else
  echo_warn "PRODUCTION-DEPLOYMENT-STRATEGY.md not found"
fi

if [ -f "PRODUCTION-DEPLOYMENT-CHECKLIST.md" ]; then
  echo_pass "PRODUCTION-DEPLOYMENT-CHECKLIST.md exists"
else
  echo_warn "PRODUCTION-DEPLOYMENT-CHECKLIST.md not found"
fi

# Check docker-compose
if [ -f "docker-compose.dev.yml" ]; then
  echo_pass "docker-compose.dev.yml exists"
else
  echo_warn "docker-compose.dev.yml not found"
fi

# ============================================================================
# 8. SECURITY CHECKS
# ============================================================================

echo_section "8. SECURITY CHECKS"

# Check for common vulnerabilities
if [ -f "package.json" ]; then
  echo_info "Checking npm dependencies..."

  if command -v npm &> /dev/null; then
    AUDIT_RESULT=$(npm audit --production 2>&1 | grep -i "vulnerabilities\|audited" | tail -1)
    echo_info "npm audit: $AUDIT_RESULT"

    if npm audit --production 2>&1 | grep -q "0 vulnerabilities"; then
      echo_pass "No npm vulnerabilities found"
    else
      echo_warn "Review npm audit output"
    fi
  else
    echo_warn "npm not available for audit"
  fi
fi

# Check for .gitignore
if [ -f ".gitignore" ]; then
  echo_pass ".gitignore file exists"

  # Check if common sensitive files are ignored
  for file in ".env" "node_modules" ".next" "dist" "build"; do
    if grep -q "^$file$\|/$file$" .gitignore; then
      echo_pass "$file is gitignored"
    else
      echo_warn "$file is not explicitly gitignored"
    fi
  done
else
  echo_fail ".gitignore not found"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo_section "SUMMARY"

TOTAL=$((PASSED + FAILED + WARNINGS))
echo -e "Total Checks: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"

echo ""

if [ "$FAILED" -eq 0 ]; then
  if [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED - READY FOR PRODUCTION${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Read: PRODUCTION-DEPLOYMENT-STRATEGY.md"
    echo "  2. Follow: PRODUCTION-DEPLOYMENT-CHECKLIST.md"
    echo "  3. Deploy to: Vercel (frontend) + Render (backend) + Supabase (database)"
    exit 0
  else
    echo -e "${YELLOW}⚠ CHECKS PASSED WITH WARNINGS - REVIEW BEFORE DEPLOYING${NC}"
    echo ""
    echo "Address warnings above before production deployment."
    exit 0
  fi
else
  echo -e "${RED}✗ PRODUCTION READINESS CHECK FAILED${NC}"
  echo ""
  echo "Fix the failures above before deploying:"
  echo "  - Ensure git is clean and pushed"
  echo "  - Install all dependencies"
  echo "  - Verify all configuration files exist"
  echo "  - Run security checks"
  exit 1
fi
