#!/bin/sh

API_URL="https://api.github.com/repos/ddnet/ddnet/contents/data/mapres?ref=master"
MAPRES_DIR="/usr/share/games/ddnet/data/mapres"

set -e

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Attempting to install."

  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to install uv. Please install it and try again."
    exit 1
  fi

  echo "Installing uv using curl..."
  curl -LsSf https://astral.sh/uv/install.sh | sh

  . $HOME/.local/bin/env
fi

if [ "$1" = "--docker" ]; then
  uv pip install --system .
else
  if [ ! -d ".venv" ]; then
    uv venv
  fi

  . .venv/bin/activate
  uv pip install -e .
fi

if [ -d /usr/share/games/ddnet/data/mapres ]; then
  echo "mapres directory already exists. Skipping download of external mapres."
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq not found. Skipping download of external mapres."
  exit 0
fi

if ! mkdir -p "$MAPRES_DIR" 2>/dev/null; then
  echo "Failed to create directory $MAPRES_DIR. Try again with elevated privileges."
  echo "Skipping download of external mapres."
  exit 0
fi

json=$(curl -s "$API_URL")

echo "$json" | jq -r '.[].download_url' | while read -r url; do
  filename=$(basename "$url")
  echo "Downloading $filename to $MAPRES_DIR."
  if ! curl -Lf -o "$MAPRES_DIR/$filename" "$url"; then
    echo "Failed to download $filename."
  fi
done
