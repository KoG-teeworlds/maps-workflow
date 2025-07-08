  #!/bin/bash

if ! command -v python3 &> /dev/null; then
  echo "Error: Python is required. Please install it and retry."
  exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

REQUIRED_VERSION="3.12"

if [ "$(printf '%s\n' "$PYTHON_VERSION" "$REQUIRED_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher required. Found Python $PYTHON_VERSION."
    exit 1
fi

if [[ "$1" == "--docker" ]]; then
   pip install .
else
  if [ ! -d .venv ]; then
    python3 -m venv .venv
  fi

  ./.venv/bin/pip install -e .
fi
