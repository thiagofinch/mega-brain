#!/bin/bash

###############################################################################
# JARVIS Installation & Setup Script
#
# Install and activate JARVIS locally
# Status: Production Ready
# Version: 2.1.0
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main installation
main() {
    print_header "🤖 JARVIS Installation & Setup"

    # Step 1: Check Python
    print_info "Step 1: Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.8+ from https://www.python.org/"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_step "Python $PYTHON_VERSION found"

    # Step 2: Check current directory
    print_info "Step 2: Verifying project structure..."
    if [ ! -d ".claude" ]; then
        print_error ".claude directory not found"
        echo "Make sure you're in the AIOX-GPS directory"
        exit 1
    fi
    print_step "Project structure verified"

    # Step 3: Create directories
    print_info "Step 3: Creating artifact directories..."
    mkdir -p .claude/jarvis
    mkdir -p artifacts/chunks
    mkdir -p artifacts/canonical
    mkdir -p artifacts/insights
    mkdir -p artifacts/narratives
    mkdir -p artifacts/dossiers
    print_step "Directories created"

    # Step 4: Install Python dependencies
    print_info "Step 4: Installing Python dependencies..."
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi

    python3 -m pip install -q --upgrade pip
    python3 -m pip install -q -r requirements.txt
    print_step "Dependencies installed"

    # Step 5: Verify imports
    print_info "Step 5: Verifying Python imports..."
    python3 << 'PYEOF'
try:
    import yaml
    import requests
    from dotenv import load_dotenv
    print("✅ All packages imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
PYEOF
    print_step "Imports verified"

    # Step 6: Initialize MISSION-STATE.json
    print_info "Step 6: Initializing JARVIS state..."
    if [ ! -f ".claude/jarvis/MISSION-STATE.json" ]; then
        cat > ".claude/jarvis/MISSION-STATE.json" << 'EOF'
{
  "status": "INITIALIZED",
  "version": "2.1.0",
  "timestamp": "2026-03-08T00:00:00Z",
  "phase": "READY",
  "pipeline": {
    "chunks_processed": 0,
    "entities_resolved": 0,
    "insights_extracted": 0,
    "narratives_created": 0,
    "dossiers_compiled": 0
  },
  "agents_online": []
}
EOF
        print_step "MISSION-STATE.json created"
    else
        print_step "MISSION-STATE.json already exists"
    fi

    # Step 7: Verify JARVIS Memory
    print_info "Step 7: Verifying JARVIS memory..."
    if [ -f ".claude/jarvis/JARVIS-MEMORY.md" ]; then
        print_step "JARVIS-MEMORY.md found"
    else
        print_warning "JARVIS-MEMORY.md not found (not critical)"
    fi

    # Step 8: Set permissions
    print_info "Step 8: Setting permissions..."
    chmod +x .claude/scripts/jarvis_orchestrator.py
    chmod -R 755 .claude/jarvis/
    print_step "Permissions set"

    # Step 9: Verify installation
    print_info "Step 9: Verifying JARVIS installation..."
    python3 << 'PYEOF'
import json
from pathlib import Path

state_file = Path(".claude/jarvis/MISSION-STATE.json")
if state_file.exists():
    with open(state_file) as f:
        state = json.load(f)
    print(f"✅ JARVIS Status: {state['status']}")
    print(f"   Version: {state['version']}")
    print(f"   Phase: {state['phase']}")
else:
    print("❌ State file not found")
    exit(1)
PYEOF

    # Success message
    print_header "🎉 JARVIS Installation Complete!"

    echo -e "${GREEN}✅ JARVIS is now installed and ready to use${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review configuration: .env (optional)"
    echo "2. Check status: python3 -c \"import json; print(json.load(open('.claude/jarvis/MISSION-STATE.json')))\" "
    echo "3. Start processing: python3 .claude/scripts/tag-inbox-files.py"
    echo ""
    echo "Documentation:"
    echo "  - Installation guide: JARVIS-INSTALLATION-GUIDE.md"
    echo "  - Pipeline spec: core/workflows/PIPELINE-JARVIS-DOCS.md"
    echo "  - Memory system: .claude/jarvis/JARVIS-MEMORY.md"
    echo ""
    print_step "Installation successful!"
}

# Run main
main
