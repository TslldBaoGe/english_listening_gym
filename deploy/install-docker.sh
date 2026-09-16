#!/bin/bash
# install-docker.sh — Install Docker Engine on Ubuntu 24.04
set -e

echo "============================================"
echo "  Docker Installation for Ubuntu 24.04"
echo "============================================"
echo ""

if command -v docker &>/dev/null; then
    echo "[OK] Docker is already installed."
    docker --version
    exit 0
fi

echo "[1/6] Removing old packages..."
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    sudo apt-get remove -y "$pkg" 2>/dev/null || true
done

echo "[2/6] Installing prerequisites..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl

echo "[3/6] Adding Docker's official GPG key..."
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "[4/6] Adding Docker repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "[5/6] Installing Docker..."
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[6/6] Adding current user to docker group..."
sudo usermod -aG docker "$USER"

echo ""
echo "============================================"
echo "  Installation complete!"
echo ""
echo "  Please LOG OUT and LOG BACK IN,"
echo "  or run: newgrp docker"
echo ""
echo "  Then verify: docker run hello-world"
echo "============================================"