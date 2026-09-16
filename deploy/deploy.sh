#!/bin/bash
# deploy.sh — One-click deploy and start English Listening Gym
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "============================================"
echo "  English Listening Gym - Docker Deploy"
echo "============================================"
echo ""

# ── Check prerequisites ──────────────────────────
echo "[1/4] Checking prerequisites..."

if ! command -v docker &>/dev/null; then
    echo "[ERROR] Docker not found. Run: bash deploy/install-docker.sh"
    exit 1
fi
echo "  [OK] docker $(docker --version | cut -d' ' -f3 | tr -d ',' )"

if ! docker compose version &>/dev/null; then
    echo "[ERROR] Docker Compose plugin not found."
    exit 1
fi
echo "  [OK] $(docker compose version)"

# ── Check .env ───────────────────────────────────
echo "[2/4] Checking .env configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        cat > .env << 'EOF'
ZHIPU_API_KEY=your_api_key_here
LLM_MODEL=glm-4-flash
EOF
    fi
    echo ""
    echo "  ┌─────────────────────────────────────────────────────┐"
    echo "  │  .env file created.                                 │"
    echo "  │  Please edit it and set your ZHIPU_API_KEY:         │"
    echo "  │    nano .env                                        │"
    echo "  │  Then run this script again.                         │"
    echo "  └─────────────────────────────────────────────────────┘"
    echo ""
    exit 0
fi

# Validate .env has a real key (not the placeholder)
if grep -q "your_api_key_here" .env 2>/dev/null; then
    echo "  [WARN] ZHIPU_API_KEY is still the placeholder."
    echo "  Please set your actual API key in .env and re-run."
    echo ""
fi
echo "  [OK] .env found"

# ── Build & Start ────────────────────────────────
echo "[3/4] Building Docker images..."
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose build

echo ""
echo "[4/4] Starting services..."
docker compose up -d

# ── Verify ───────────────────────────────────────
echo ""
echo "Waiting for services to be ready..."
sleep 5
if docker compose ps --status running | grep -q "backend"; then
    echo "  [OK] Backend is running"
else
    echo "  [WARN] Backend may not be ready yet. Check: docker compose logs backend"
fi
if docker compose ps --status running | grep -q "frontend"; then
    echo "  [OK] Frontend is running"
else
    echo "  [WARN] Frontend may not be ready yet. Check: docker compose logs frontend"
fi

# ── Summary ──────────────────────────────────────
echo ""
echo "============================================"
echo "  Deployment Complete!"
echo ""
echo "  Access the app at:"
echo "    http://$(hostname -I | awk '{print $1}')"
echo "    http://localhost"
echo ""
echo "  Management commands:"
echo "    Logs:   docker compose logs -f"
echo "    Stop:   docker compose down"
echo "    Rebuild: docker compose build && docker compose up -d"
echo "============================================"