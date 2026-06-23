#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
exec env SURF_WEB_HOST=0.0.0.0 "$PROJECT_DIR/start_web_demo.command"
