#!/usr/bin/env bash
# setup-ec2.sh — one-shot provisioner for Curie on an EC2 box (Amazon Linux 2023 or Ubuntu).
# Run it ON the instance AFTER you've rsync'd the repo (incl. .env) to it:
#
#     bash ~/Slack4Good/deploy/setup-ec2.sh
#
# Installs Python 3.11 + a venv + dependencies, then installs a systemd service that keeps
# `python app.py` running 24/7 and auto-restarts it on crash or reboot. Idempotent — re-run
# after a code update, or just `sudo systemctl restart curie`.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root (deploy/ is one level down)
RUN_USER="$(whoami)"
SERVICE=/etc/systemd/system/curie.service

echo "==> Curie deploy   dir=$APP_DIR   user=$RUN_USER"

# 1) Python 3.11 (AL2023 -> dnf; Ubuntu -> apt). venv ships pip via ensurepip, so no system pip needed.
if command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y python3.11 rsync
elif command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y && sudo apt-get install -y python3.11 python3.11-venv rsync
fi
PY=python3.11; command -v $PY >/dev/null 2>&1 || PY=python3     # last resort

# 2) venv + dependencies
cd "$APP_DIR"
$PY -m venv .venv || python3 -m venv .venv
./.venv/bin/pip install --upgrade pip >/dev/null
./.venv/bin/pip install -r requirements.txt

# 3) sanity: the app loads .env itself (python-dotenv) from WorkingDirectory
if [ ! -f "$APP_DIR/.env" ]; then
  echo "!! $APP_DIR/.env is MISSING — copy it from your Mac before the service can start:" >&2
  echo "   scp -i <key.pem> ~/Pictures/Slack4Good/.env $RUN_USER@<host>:$APP_DIR/.env" >&2
fi

# 4) systemd unit — absolute paths baked in; Socket Mode needs only outbound network
sudo tee "$SERVICE" >/dev/null <<UNIT
[Unit]
Description=Curie — the lab's memory (Slack agent, Socket Mode)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT

# 5) enable + (re)start, then show status
sudo systemctl daemon-reload
sudo systemctl enable curie.service
sudo systemctl restart curie.service
sleep 2
sudo systemctl --no-pager --full status curie.service | head -20 || true
echo
echo "==> live logs:      sudo journalctl -u curie -f"
echo "==> after an update: rsync again, then  sudo systemctl restart curie"
