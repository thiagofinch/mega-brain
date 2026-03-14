#!/bin/bash
# Install Skill Seekers in isolated virtual environment.
# This keeps SS dependencies (langchain, llama-index) separate from Mega Brain.
#
# Usage:
#   ./bin/install-skill-seekers.sh
#
# Requirements:
#   - Python 3.10+
#   - pip

set -e

VENV_PATH="${HOME}/.venvs/skill-seekers"
SS_PACKAGE="skill-seekers"

echo "=== Skill Seekers Installation ==="
echo ""

# Check if already installed
if [ -d "$VENV_PATH" ]; then
    echo "Skill Seekers venv already exists at $VENV_PATH"
    echo "To reinstall, first remove: rm -rf $VENV_PATH"

    # Verify it works
    if "$VENV_PATH/bin/python" -c "import skill_seekers" 2>/dev/null; then
        echo "Installation verified - skill_seekers importable"
        exit 0
    else
        echo "Warning: venv exists but skill_seekers not importable"
        echo "Consider removing and reinstalling"
        exit 1
    fi
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

# Create venv
echo ""
echo "Creating virtual environment at $VENV_PATH..."
python3 -m venv "$VENV_PATH"

# Upgrade pip
echo "Upgrading pip..."
"$VENV_PATH/bin/pip" install --upgrade pip --quiet

# Install Skill Seekers (base package - no video deps)
echo "Installing $SS_PACKAGE..."
"$VENV_PATH/bin/pip" install "$SS_PACKAGE" --quiet

# Verify installation
echo ""
echo "Verifying installation..."
if "$VENV_PATH/bin/python" -c "import skill_seekers; print(f'skill_seekers {skill_seekers.__version__}')" 2>/dev/null; then
    echo "Success!"
else
    echo "Warning: skill_seekers package installed but import failed"
    echo "This might be a version compatibility issue"
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Skill Seekers is installed at: $VENV_PATH"
echo ""
echo "To install video support (adds ~2GB for PyTorch):"
echo "  ./bin/install-skill-seekers-video.sh"
echo ""
echo "Mega Brain will automatically detect and use this installation."
