#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"

PORT="${SURF_WEB_PORT:-5050}"
URL="http://127.0.0.1:${PORT}"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"

echo "SURF Posture Web Demo"
echo "Project: $PROJECT_DIR"
echo "URL: $URL"
echo

pause_on_error() {
  echo
  echo "Startup failed."
  echo "Press Enter to close this window."
  read -r
}

open_demo_url() {
  if [[ "${SURF_NO_OPEN:-0}" == "1" ]]; then
    echo "Browser open skipped because SURF_NO_OPEN=1."
    return 0
  fi
  if /usr/bin/open "$URL" >/dev/null 2>&1; then
    echo "Opened: $URL"
  else
    echo "Server is running. Open manually: $URL"
  fi
}

health_body() {
  /usr/bin/curl -fsS "$1/health" 2>/dev/null || true
}

is_current_demo_server() {
  [[ "$1" == *'"app":"surf-posture-web"'* ]]
}

pick_available_url() {
  local start_port="$PORT"
  local candidate_port="$start_port"
  local candidate_url
  local body

  while (( candidate_port < start_port + 10 )); do
    candidate_url="http://127.0.0.1:${candidate_port}"
    body="$(health_body "$candidate_url")"

    if [[ -z "$body" ]]; then
      PORT="$candidate_port"
      URL="$candidate_url"
      return 0
    fi

    if is_current_demo_server "$body"; then
      PORT="$candidate_port"
      URL="$candidate_url"
      echo "Web demo is already running."
      open_demo_url
      exit 0
    fi

    echo "Port ${candidate_port} is occupied by another or older local server."
    candidate_port=$((candidate_port + 1))
  done

  echo "Could not find an available port from ${start_port} to $((start_port + 9))."
  exit 1
}

trap pause_on_error ERR

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing project virtual environment: .venv/bin/python"
  echo
  echo "Create it with:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/python -m pip install --upgrade pip"
  echo "  .venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt"
  exit 1
fi

if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import cv2
import flask
import mediapipe as mp

assert hasattr(mp, "solutions")
PY
then
  echo "Required dependencies are missing or incompatible."
  echo
  echo "Install the pinned local stack with:"
  echo "  .venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt"
  exit 1
fi

pick_available_url

echo "Starting server..."
echo "URL: $URL"
echo "Leave this window open while presenting."
echo "Press Ctrl+C to stop the demo."
echo

if [[ "${SURF_NO_OPEN:-0}" != "1" ]]; then
  (sleep 2; /usr/bin/open "$URL" >/dev/null 2>&1 || true) &
fi

exec env SURF_WEB_PORT="$PORT" "$PYTHON_BIN" -m web.app
