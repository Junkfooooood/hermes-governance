#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=9200

# 1. Port check
if lsof -i :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Error: Port $PORT already in use"; exit 1
fi

# 2. Dependency check
command -v node >/dev/null || { echo "Error: node not found"; exit 1; }
command -v python3 >/dev/null || { echo "Error: python3 not found"; exit 1; }

# 3. Backend virtual environment
VENV="$DIR/backend/.venv"
if [ ! -d "$VENV" ]; then
  echo "Creating Python venv..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r "$DIR/backend/requirements.txt"
fi

# 4. Frontend build (if needed)
STAMP="$DIR/frontend/dist/.build.stamp"
NEED_BUILD=false
if [ ! -d "$DIR/frontend/dist" ] || [ ! -f "$STAMP" ]; then
  NEED_BUILD=true
elif find "$DIR/frontend/src" -name "*.tsx" -newer "$STAMP" -print -quit 2>/dev/null | grep -q .; then
  NEED_BUILD=true
fi
if [ "$NEED_BUILD" = true ]; then
  echo "Building frontend..."
  cd "$DIR/frontend" && npm install --silent && npm run build
  touch "$DIR/frontend/dist/.build.stamp"
fi

# 5. Start
echo "Dashboard → http://localhost:$PORT"
cd "$DIR/backend"
"$VENV/bin/python" -m uvicorn main:app --host 0.0.0.0 --port $PORT
