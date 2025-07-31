#!/bin/sh

set -e

case "$1" in
  workflow)
    shift
    python maps_workflow/main.py "$@"
    ;;
  export)
    shift
    twgpu-map-photography "$@"
    ;;
  *)
    echo "Unknown command $1. Allowed commands are: workflow | export [args...]"
    exit 1
    ;;
esac
