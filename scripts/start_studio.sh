#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"
echo "============================================================"
echo "  🌸 Starting Anima Agent Studio..."
echo "============================================================"
python3 -u web_gui.py
