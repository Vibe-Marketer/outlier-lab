#!/usr/bin/env bash
set -euo pipefail

# AI Simple — Outlier Lab Zero-Friction Local Setup & Launcher
# No cloud accounts, no database, no paid AI API keys required to start.

cd "$(dirname "$0")"

echo ""
echo "  ┌──────────────────────────────────────────────────────┐"
echo "  │  AI SIMPLE · OUTLIER LAB — Quick Setup               │"
echo "  └──────────────────────────────────────────────────────┘"
echo ""

# 1. Pick Python
PY=""
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  echo "  ✗ Python 3.10+ is required. Install it from https://python.org or 'brew install python'."
  exit 1
fi
echo "  ✓ Using Python: $PY"

# 2. Ensure config.json exists (non-destructive)
if [ ! -f "config.json" ]; then
  if [ -f "config.example.json" ]; then
    cp config.example.json config.json
    echo "  ✓ Created starter config.json from config.example.json"
  else
    printf '{\n  "creators": []\n}\n' > config.json
    echo "  ✓ Created blank config.json"
  fi
else
  echo "  ✓ Found existing config.json"
fi

# 3. Build dashboard if missing (or if --rebuild passed)
if [ ! -f "index.html" ] || [ "${1:-}" = "--rebuild" ]; then
  echo "  → Building Outlier Lab dashboard…"
  "$PY" build.py
fi

# 4. Optional status hints (never blocking!)
if [ ! -f ".env" ]; then
  echo "  ℹ Optional: No .env yet — you can paste Apify / TokScript keys in Admin anytime."
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "  ℹ Optional: Install ffmpeg ('brew install ffmpeg') later if you want 3s hook clips."
fi

echo ""
echo "  ✓ Ready! Launching Outlier Lab at http://127.0.0.1:4747/"
echo "    (Admin console: http://127.0.0.1:4747/admin)"
echo "    Go-Live / Vercel / Clerk are 100% optional — see Setup & Go Live tab."
echo ""

exec "$PY" -u serve.py
