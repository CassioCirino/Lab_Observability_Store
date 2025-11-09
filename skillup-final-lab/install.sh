#!/usr/bin/env bash
set -euo pipefail

# Diretórios da APP (note o subdiretório skillup-final-lab)
REPO_DIR="/opt/skillup-final-lab"
APP_DIR="/opt/skillup-final-lab/skillup-final-lab"
UNIT_FILE="/etc/systemd/system/skillup-lab.service"
DB_DIR="$APP_DIR/db"
DB_FILE="$DB_DIR/skillup.db"
VENV_DIR="$APP_DIR/venv"
REQUIREMENTS="$APP_DIR/requirements.txt"

echo "[1/6] Preparando pacotes do sistema..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip build-essential curl git

echo "[2/6] Criando venv e instalando dependências..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
# Corrigido: requirements no subdiretório da app
"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS"

echo "[3/6] Garantindo diretório e banco de dados..."
mkdir -p "$DB_DIR"
"$VENV_DIR/bin/python3" "$APP_DIR/app/db_init.py" "$DB_FILE"

echo "[4/6] Gravando unit do systemd..."
cat > "$UNIT_FILE" << 'EOS'
[Unit]
Description=SkillUp Final Lab Flask App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/skillup-final-lab/skillup-final-lab
Environment="PATH=/opt/skillup-final-lab/skillup-final-lab/venv/bin"
Environment="DATABASE_FILE=/opt/skillup-final-lab/skillup-final-lab/db/skillup.db"
ExecStartPre=/opt/skillup-final-lab/skillup-final-lab/venv/bin/python3 /opt/skillup-final-lab/skillup-final-lab/app/db_init.py /opt/skillup-final-lab/skillup-final-lab/db/skillup.db
ExecStart=/opt/skillup-final-lab/skillup-final-lab/venv/bin/gunicorn --bind 0.0.0.0:80 app.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOS

echo "[5/6] Ativando serviço..."
systemctl daemon-reload
systemctl enable skillup-lab.service
systemctl restart skillup-lab.service

echo "[6/6] Liberando porta 80 no firewall (se existir)..."
ufw allow 80 || true

echo "OK. Verifique o status:"
systemctl status skillup-lab.service --no-pager -l || true
echo
echo "Teste local:"
curl -I http://127.0.0.1/ || true
