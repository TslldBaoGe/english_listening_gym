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
echo "[1/3] Checking prerequisites..."

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

# ── Note about LLM config ────────────────────────
echo "[2/3] Note: LLM API Key is configured via the web Settings page."
echo "  No .env file needed. Just deploy and configure in the browser."
echo ""

# ── Build & Start ────────────────────────────────
echo "[3/3] Building Docker images..."
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose build

echo ""
echo "  Starting services..."
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