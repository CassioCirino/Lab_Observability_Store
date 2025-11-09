#!/usr/bin/env bash
set -euo pipefail

# Este script deve ser executado DENTRO de skillup-final-lab/
# Pode ser chamado pelo quick-install.sh ou manualmente.

APP_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${APP_ROOT}/venv"
DB_DIR="${APP_ROOT}/db"
DB_FILE="${DB_DIR}/skillup.db"
SERVICE_NAME="skillup-lab.service"
PORT="${PORT:-80}"

log() { echo -e "\033[1;32m[INFO]\033[0m $*"; }
err(){ echo -e "\033[1;31m[ERRO]\033[0m $*"; exit 1; }

require_cmd() { command -v "$1" >/dev/null 2>&1 || err "Comando obrigatório não encontrado: $1"; }

require_cmd python3
require_cmd pip3
require_cmd systemctl

log "[1/6] Preparando venv e dependências…"
python3 -m venv "${VENV_DIR}"
# pip/setuptools/wheel atualizados
"${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel
# requirements
REQ="${APP_ROOT}/requirements.txt"
[ -f "${REQ}" ] || err "requirements.txt não encontrado em ${REQ}"
"${VENV_DIR}/bin/pip" install -r "${REQ}"

log "[2/6] Banco de dados…"
mkdir -p "${DB_DIR}"
DATABASE_FILE="${DB_FILE}" "${VENV_DIR}/bin/python" "${APP_ROOT}/app/db_init.py" "${DB_FILE}" || true
log "Database em: ${DB_FILE}"

log "[3/6] Unit systemd…"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}"
cat > "${UNIT_PATH}" <<EOF
[Unit]
Description=SkillUp Final Lab Flask App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_ROOT}
Environment=PATH=${VENV_DIR}/bin
Environment=DATABASE_FILE=${DB_FILE}
ExecStartPre=${VENV_DIR}/bin/python ${APP_ROOT}/app/db_init.py ${DB_FILE}
ExecStart=${VENV_DIR}/bin/gunicorn --bind 0.0.0.0:${PORT} app.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

log "[4/6] Habilitando serviço…"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

log "[5/6] Liberando porta ${PORT} local (iptables; opcional se já feito no bootstrap)…"
if ! iptables -C INPUT -p tcp --dport "${PORT}" -j ACCEPT 2>/dev/null; then
  iptables -I INPUT -p tcp --dport "${PORT}" -j ACCEPT || true
fi
# persistência se disponível
if command -v netfilter-persistent >/dev/null 2>&1; then
  netfilter-persistent save || true
fi

log "[6/6] Status:"
systemctl --no-pager --full status "${SERVICE_NAME}" || true

echo
log "Teste local (esperado 302 para /login):"
set +e
curl -sSI "http://127.0.0.1:${PORT}/" | head -n 5 || true
set -e
