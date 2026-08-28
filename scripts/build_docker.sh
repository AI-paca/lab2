#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

image="${DOCKER_IMAGE:-lab2:latest}"

echo "Сборка Docker-образа $image..."
docker build --no-cache -t "$image" .
echo "Docker-образ собран: $image"
