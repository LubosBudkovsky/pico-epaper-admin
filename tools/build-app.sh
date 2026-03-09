#!/usr/bin/env bash
# Build the React app and copy the output to firmware/www/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$REPO_ROOT/app"
WWW_DIR="$REPO_ROOT/firmware/www"

echo "==> Building app..."
cd "$APP_DIR"
npm run build

echo "==> Clearing firmware/www/..."
rm -rf "$WWW_DIR"
mkdir -p "$WWW_DIR"

echo "==> Copying build output to firmware/www/..."
cp -r "$APP_DIR/dist/." "$WWW_DIR/"

echo "==> Done. Static files copied to firmware/www/"
