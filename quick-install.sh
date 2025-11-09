#!/usr/bin/env bash
set -euo pipefail

### ========= CONFIG =========
REPO_URL="${REPO_URL:-https://github.com/CassioCirino/Lab_Observability_Store.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
APP_DIR="${APP_DIR:-/opt/skillup-final-lab}"   # onde o repo será clonado
SUBDIR="${SUBDIR:-skillup-final-lab}"          # subpasta com o app/requirements/install.sh
PORT="${PORT:-80}"
### ==========================

need_root() { [ "$(id -u)" -eq 0 ] || { echo "Por favor, execute como root (use sudo)." >&2; exit 1; }; }
log() { echo -e "\033[1;32m[INFO]\033[0m $*"; }
warn(){ echo -e "\033[1;33m[WARN]\033[0m $*"; }
err() { echo -e "\033[1;31m[ERRO]\033[0m $*"; exit 1; }

pkg_install() {
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y git curl python3 python3-venv python3-pip build-essential
    # iptables-persistent para salvar regras
    apt-get install -y iptables-persistent || true
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y git curl python3 python3-pip python3-virtualenv gcc gcc-c++ make
    # preferir firewalld em distros RHEL-like
    dnf install -y firewalld iptables iptables-services || true
    systemctl enable --now firewalld || true
  elif command -v yum >/dev/null 2>&1; then
    yum install -y git curl python3 python3-pip gcc gcc-c++ make
    yum install -y firewalld iptables iptables-services || true
    systemctl enable --now firewalld || true
  else
    err "Gerenciador de pacotes não suportado (precisa de apt, dnf ou yum)."
  fi
}

open_firewall() {
  # Tenta primeiro pelo firewalld (RHEL/Oracle Linux), senão usa iptables puro e salva.
  if systemctl is-active --quiet firewalld 2>/dev/null; then
    log "Liberando porta ${PORT} no firewalld…"
    firewall-cmd --add-service=http --permanent >/dev/null 2>&1 || firewall-cmd --add-port=${PORT}/tcp --permanent
    firewall-cmd --add-service=https --permanent >/dev/null 2>&1 || true
    firewall-cmd --reload || true
  else
    log "Liberando porta ${PORT} via iptables…"
    # adiciona apenas se não existir
    if ! iptables -C INPUT -p tcp --dport "${PORT}" -j ACCEPT 2>/dev/null; then
      iptables -I INPUT -p tcp --dport "${PORT}" -j ACCEPT
    fi
    # HTTPS opcional
    if ! iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null; then
      iptables -I INPUT -p tcp --dport 443 -j ACCEPT || true
    fi
    # salvar (Debian/Ubuntu com iptables-persistent; em RHEL-like, iptables-save > /etc/sysconfig/iptables)
    if command -v netfilter-persistent >/dev/null 2>&1; then
      netfilter-persistent save || true
      netfilter-persistent reload || true
    elif [ -d /etc/sysconfig ]; then
      iptables-save > /etc/sysconfig/iptables || true
      systemctl enable iptables 2>/dev/null || true
      systemctl restart iptables 2>/dev/null || true
    fi
  fi
}

clone_repo() {
  rm -rf "${APP_DIR}"
  mkdir -p "${APP_DIR}"
  log "Clonando ${REPO_URL} (${REPO_BRANCH}) para ${APP_DIR}…"
  git clone --branch "${REPO_BRANCH}" --depth=1 "${REPO_URL}" "${APP_DIR}"
}

run_inner_installer() {
  local inner="${APP_DIR}/${SUBDIR}/install.sh"
  [ -f "${inner}" ] || err "install.sh não encontrado em ${inner}"
  chmod +x "${inner}"
  log "Executando instalador interno…"
  "${inner}"
}

healthcheck() {
  log "Healthcheck local…"
  if command -v curl >/dev/null 2>&1; then
    set +e
    curl -sS -I "http://127.0.0.1:${PORT}/" | head -n1 || true
    set -e
  fi
}

### MAIN
need_root
log "Instalando dependências do sistema…"
pkg_install
log "Abrindo firewall/iptables…"
open_firewall
clone_repo
run_inner_installer
healthcheck
log "Concluído. Verifique o serviço com:  systemctl status skillup-lab.service"
log "Acesse: http://SEU-IP-PUBLICO:${PORT}/  (na OCI já está liberado no NSG e Internet GW)"
