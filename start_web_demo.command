#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"

PORT="${SURF_WEB_PORT:-5050}"
HOST="${SURF_WEB_HOST:-127.0.0.1}"
HTTPS="${SURF_WEB_HTTPS:-0}"
SCHEME="http"
if [[ "$HTTPS" == "1" ]]; then
  SCHEME="https"
fi
URL="${SCHEME}://127.0.0.1:${PORT}"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
CERT_DIR="$PROJECT_DIR/temp/certs"
CA_CERT="$CERT_DIR/surf-posture-local-ca.crt"
CA_KEY="$CERT_DIR/surf-posture-local-ca.key"
SERVER_CERT=""
SERVER_KEY=""

echo "SURF Posture Web Demo"
echo "Project: $PROJECT_DIR"
echo "Local URL: $URL"
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
  /usr/bin/curl -k --max-time 1 -fsS "$1/health" 2>/dev/null || true
}

is_current_demo_server() {
  if [[ "$1" != *'"app":"surf-posture-web"'* || "$1" != *'"version":"week-02-yolo-pose-labels-v1"'* ]]; then
    return 1
  fi
  if [[ "$HOST" == "0.0.0.0" && "$1" != *'"host":"0.0.0.0"'* ]]; then
    return 1
  fi
  return 0
}

port_is_open() {
  "$PYTHON_BIN" -c 'import socket, sys; sock = socket.socket(); sock.settimeout(0.5); code = sock.connect_ex(("127.0.0.1", int(sys.argv[1]))); sock.close(); sys.exit(0 if code == 0 else 1)' "$1" >/dev/null 2>&1
}

pick_available_url() {
  local start_port="$PORT"
  local candidate_port="$start_port"
  local candidate_url
  local body

  while (( candidate_port < start_port + 10 )); do
    candidate_url="${SCHEME}://127.0.0.1:${candidate_port}"
    body="$(health_body "$candidate_url")"

    if is_current_demo_server "$body"; then
      PORT="$candidate_port"
      URL="$candidate_url"
      echo "Web demo is already running."
      open_demo_url
      exit 0
    fi

    if [[ -n "$body" ]] || port_is_open "$candidate_port"; then
      echo "Port ${candidate_port} is occupied by another or older local server."
      candidate_port=$((candidate_port + 1))
      continue
    fi

    PORT="$candidate_port"
    URL="$candidate_url"
    return 0
  done

  echo "Could not find an available port from ${start_port} to $((start_port + 9))."
  exit 1
}

ensure_https_cert() {
  local lan_ip="$1"
  local cert_ip="${lan_ip:-127.0.0.1}"
  local safe_ip="${cert_ip//./-}"
  local ca_conf="$CERT_DIR/ca.conf"
  local server_conf="$CERT_DIR/server-${safe_ip}.conf"
  local server_csr="$CERT_DIR/server-${safe_ip}.csr"

  mkdir -p "$CERT_DIR"
  chmod 700 "$CERT_DIR"

  if [[ ! -f "$CA_CERT" || ! -f "$CA_KEY" ]]; then
    cat > "$ca_conf" <<'EOF'
[ req ]
prompt = no
distinguished_name = dn
x509_extensions = v3_ca

[ dn ]
CN = SURF Posture Local CA

[ v3_ca ]
basicConstraints = critical,CA:true
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
EOF
    /usr/bin/openssl req -x509 -newkey rsa:2048 -sha256 -days 825 -nodes \
      -keyout "$CA_KEY" \
      -out "$CA_CERT" \
      -config "$ca_conf" >/dev/null 2>&1
    chmod 600 "$CA_KEY"
  fi

  SERVER_CERT="$CERT_DIR/surf-posture-${safe_ip}.crt"
  SERVER_KEY="$CERT_DIR/surf-posture-${safe_ip}.key"

  if [[ ! -f "$SERVER_CERT" || ! -f "$SERVER_KEY" ]]; then
    cat > "$server_conf" <<EOF
[ req ]
prompt = no
distinguished_name = dn
req_extensions = v3_req

[ dn ]
CN = surf-posture.local

[ v3_req ]
basicConstraints = CA:false
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = localhost
IP.1 = 127.0.0.1
IP.2 = ${cert_ip}
EOF
    /usr/bin/openssl req -new -newkey rsa:2048 -nodes \
      -keyout "$SERVER_KEY" \
      -out "$server_csr" \
      -config "$server_conf" >/dev/null 2>&1
    /usr/bin/openssl x509 -req -sha256 -days 825 \
      -in "$server_csr" \
      -CA "$CA_CERT" \
      -CAkey "$CA_KEY" \
      -CAcreateserial \
      -out "$SERVER_CERT" \
      -extensions v3_req \
      -extfile "$server_conf" >/dev/null 2>&1
    chmod 600 "$SERVER_KEY"
  fi
}

lan_ip() {
  "$PYTHON_BIN" - <<'PY'
import ipaddress
import os
import re
import socket
import subprocess

override = os.environ.get("SURF_PHONE_IP", "").strip()
if override:
    print(override)
    raise SystemExit

excluded_interfaces = ("lo", "utun", "awdl", "llw", "bridge", "vmenet")
reserved_benchmark = ipaddress.ip_network("198.18.0.0/15")
candidates = []

try:
    output = subprocess.check_output(["/sbin/ifconfig"], text=True)
except (OSError, subprocess.SubprocessError):
    output = ""

current_interface = ""
for line in output.splitlines():
    if line and not line.startswith((" ", "\t")):
        current_interface = line.split(":", 1)[0]
        continue
    match = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)\b", line)
    if not match:
        continue
    try:
        ip = ipaddress.ip_address(match.group(1))
    except ValueError:
        continue
    if ip.is_loopback or ip.is_link_local or ip in reserved_benchmark:
        continue
    if current_interface.startswith(excluded_interfaces):
        continue
    if not ip.is_private:
        continue
    rank = 0 if current_interface == "en0" else 1
    candidates.append((rank, current_interface, str(ip)))

if candidates:
    print(sorted(candidates)[0][2])
    raise SystemExit

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    sock.connect(("8.8.8.8", 80))
    ip = ipaddress.ip_address(sock.getsockname()[0])
    if not (ip.is_loopback or ip.is_link_local or ip in reserved_benchmark):
        print(str(ip))
except OSError:
    pass
finally:
    sock.close()
PY
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

LAN_IP=""
if [[ "$HOST" == "0.0.0.0" ]]; then
  LAN_IP="$(lan_ip)"
fi

if [[ "$HTTPS" == "1" ]]; then
  ensure_https_cert "$LAN_IP"
fi

echo "Starting server..."
echo "Local URL: $URL"
if [[ "$HOST" == "0.0.0.0" ]]; then
  if [[ -n "$LAN_IP" ]]; then
    echo "Phone URL: ${SCHEME}://${LAN_IP}:${PORT}"
    echo "Use the same Wi-Fi network on the phone and computer."
  else
    echo "Phone URL: use this computer's LAN IP with ${SCHEME} and port ${PORT}."
  fi
else
  echo "Phone collection disabled. Start with SURF_WEB_HOST=0.0.0.0 for LAN access."
fi
if [[ "$HTTPS" == "1" ]]; then
  echo "HTTPS enabled."
  echo "Local CA certificate for phone trust: $CA_CERT"
  echo "On iPhone: AirDrop/open this .crt, install the profile, then enable full trust."
fi
echo "Leave this window open while presenting."
echo "Press Ctrl+C to stop the demo."
echo

if [[ "${SURF_NO_OPEN:-0}" != "1" ]]; then
  (sleep 2; /usr/bin/open "$URL" >/dev/null 2>&1 || true) &
fi

exec env \
  SURF_WEB_PORT="$PORT" \
  SURF_WEB_HOST="$HOST" \
  SURF_WEB_CERT_FILE="$SERVER_CERT" \
  SURF_WEB_KEY_FILE="$SERVER_KEY" \
  "$PYTHON_BIN" -m web.app
