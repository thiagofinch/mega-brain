#!/bin/bash
# Install Skill Seekers video processing support.
# This adds PyTorch (~2GB), faster-whisper, and yt-dlp.
#
# Prerequisites:
#   - Run install-skill-seekers.sh first
#
# Usage:
#   ./bin/install-skill-seekers-video.sh

set -e

VENV_PATH="${HOME}/.venvs/skill-seekers"

echo "=== Skill Seekers Video Support ==="
echo ""

# Check base installation exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Skill Seekers not installed"
    echo "Run ./bin/install-skill-seekers.sh first"
    exit 1
fi

# Check if already installed
if "$VENV_PATH/bin/python" -c "import torch; import faster_whisper" 2>/dev/null; then
    echo "Video support already installed"
    exit 0
fi

echo "Installing video dependencies..."
echo "This may take several minutes and download ~2GB..."
echo ""

# Install video extras
"$VENV_PATH/bin/pip" install "skill-seekers[video-full]"

# Verify
echo ""
echo "Verifying installation..."
"$VENV_PATH/bin/python" -c "
import torch
import faster_whisper
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print('faster-whisper: installed')
"

echo ""
echo "=== Video Support Installed ==="
echo ""
echo "You can now use:"
echo "  - /ingest-video skill for YouTube/local video"
echo "  - ss_bridge.ingest_video() from Python"
