#!/usr/bin/env bash
set -euo pipefail

# run as root (or use sudo)
if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo ./install.sh"
  exit 1
fi

# Update & prerequisites
apt-get update -y
apt-get install -y python3 python3-venv python3-pip build-essential git curl

# Optional: install stress-ng if available (used by stress.py)
apt-get install -y stress-ng || true

# Create app dir
APP_DIR=/opt/skillup-final-lab
mkdir -p $APP_DIR
cp -r . $APP_DIR
chown -R $(whoami) $APP_DIR

# Create venv
python3 -m venv $APP_DIR/venv
$APP_DIR/venv/bin/pip install --upgrade pip
$APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Create DB dir
mkdir -p $APP_DIR/db
export DATABASE_FILE=$APP_DIR/db/skillup.db

# Initialize database and seed
$APP_DIR/venv/bin/python3 $APP_DIR/app/db_init.py $DATABASE_FILE

# Copy systemd service
cat > /etc/systemd/system/skillup-lab.service <<'EOS'
[Unit]
Description=SkillUp Final Lab Flask App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/skillup-final-lab
Environment="PATH=/opt/skillup-final-lab/venv/bin"
ExecStart=/opt/skillup-final-lab/venv/bin/gunicorn --bind 0.0.0.0:8080 app.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOS

systemctl daemon-reload
systemctl enable skillup-lab.service

echo "Installation complete."
echo "Start service with: systemctl start skillup-lab.service"
