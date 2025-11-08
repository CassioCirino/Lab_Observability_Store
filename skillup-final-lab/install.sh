#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Execute como root: sudo ./install.sh"; exit 1
fi

apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl build-essential stress-ng || true

APP_DIR=/opt/skillup-final-lab
mkdir -p "$APP_DIR"
cp -r . "$APP_DIR"

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip setuptools wheel
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Garante DB inicializado
mkdir -p "$APP_DIR/db"
DATABASE_FILE="$APP_DIR/db/skillup.db"
"$APP_DIR/venv/bin/python3" "$APP_DIR/app/db_init.py" "$DATABASE_FILE"

# Unit systemd com ExecStartPre para garantir DB
cat > /etc/systemd/system/skillup-lab.service <<'EOS'
[Unit]
Description=SkillUp Final Lab Flask App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/skillup-final-lab
Environment="PATH=/opt/skillup-final-lab/venv/bin"
ExecStartPre=/opt/skillup-final-lab/venv/bin/python3 /opt/skillup-final-lab/app/db_init.py /opt/skillup-final-lab/db/skillup.db
ExecStart=/opt/skillup-final-lab/venv/bin/gunicorn --bind 0.0.0.0:8080 app.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOS

systemctl daemon-reload
systemctl enable skillup-lab.service
systemctl restart skillup-lab.service

echo "OK. Verifique em: systemctl status skillup-lab.service"
