#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DE ATUALIZAÇÃO AUTOMATIZADA EM VPS (Ubuntu / Debian)
# Sistema OMR de Correção de Provas & Gabaritos - Prova Canoa
# ==============================================================================

set -e

# Cores para terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo -e "${CYAN}${BOLD}"
echo "=============================================================================="
echo "    🚀 ATUALIZADOR DO SISTEMA PROVA CANOA (CORREÇÃO DE PROVAS & GABARITOS)    "
echo "=============================================================================="
echo -e "${NC}"

# 1. Verificar privilégios de root / sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERRO] Este script precisa ser executado como root ou com sudo.${NC}"
  echo -e "Por favor, execute novamente: ${YELLOW}sudo bash $0${NC}"
  exit 1
fi

# 2. Localizar diretório da aplicação
POSSIBLE_DIRS=(
  "/var/www/correcao-provas"
  "$(pwd)"
  "$(dirname "$(readlink -f "$0")")"
)

INSTALL_DIR=""
for dir in "${POSSIBLE_DIRS[@]}"; do
  if [ -d "$dir/backend" ] && [ -d "$dir/frontend" ] && [ -d "$dir/.git" ]; then
    INSTALL_DIR="$dir"
    break
  fi
done

if [ -z "$INSTALL_DIR" ]; then
  INSTALL_DIR="/var/www/correcao-provas"
fi

if [ ! -d "$INSTALL_DIR" ]; then
  echo -e "${RED}[ERRO] Diretório da aplicação não encontrado em: ${INSTALL_DIR}${NC}"
  echo -e "Certifique-se de que o sistema foi instalado previamente."
  exit 1
fi

echo -e "${BLUE}📁 Diretório detectado:${NC} ${BOLD}${INSTALL_DIR}${NC}"
cd "$INSTALL_DIR"

# 3. Configurar diretório seguro no Git
git config --global --add safe.directory "${INSTALL_DIR}" 2>/dev/null || true

# 4. Baixar atualizações do repositório GitHub
echo -e "\n${BLUE}📥 Buscando versão mais recente no GitHub...${NC}"
git fetch origin main

CURRENT_HASH=$(git rev-parse HEAD 2>/dev/null || echo "antiga")
REMOTE_HASH=$(git rev-parse origin/main 2>/dev/null || echo "nova")

echo -e "Commit local:  ${YELLOW}${CURRENT_HASH:0:7}${NC}"
echo -e "Commit remoto: ${GREEN}${REMOTE_HASH:0:7}${NC}"

echo -e "\n${BLUE}🔄 Sincronizando arquivos do repositório...${NC}"
git reset --hard origin/main

# 5. Atualizar dependências Python no ambiente virtual
VENV_BIN="$INSTALL_DIR/venv/bin"
if [ -d "$VENV_BIN" ]; then
  echo -e "\n${BLUE}🐍 Atualizando dependências Python no venv...${NC}"
  "$VENV_BIN/pip" install --upgrade pip --quiet
  "$VENV_BIN/pip" install -r backend/requirements.txt --quiet
  echo -e "${GREEN}✓ Dependências verificadas e atualizadas com sucesso.${NC}"
else
  echo -e "\n${YELLOW}⚠️ Ambiente virtual 'venv' não encontrado em $INSTALL_DIR/venv. Pulando pip.${NC}"
fi

# 6. Garantir permissões corretas para o servidor web (www-data)
echo -e "\n${BLUE}🔒 Ajustando permissões de arquivos...${NC}"
mkdir -p "$INSTALL_DIR/backend/storage/scans"
mkdir -p "$INSTALL_DIR/backend/storage/sheets"
mkdir -p "$INSTALL_DIR/backend/storage/overlays"
mkdir -p "$INSTALL_DIR/backend/storage/assets"

chown -R www-data:www-data "$INSTALL_DIR" 2>/dev/null || true
chmod -R 755 "$INSTALL_DIR" 2>/dev/null || true
chmod 600 "$INSTALL_DIR/.env" 2>/dev/null || true

# 7. Reiniciar o serviço Systemd e o Nginx
echo -e "\n${BLUE}⚙️ Reiniciando serviço correcao-provas e Nginx...${NC}"
systemctl daemon-reload 2>/dev/null || true

if systemctl list-unit-files | grep -q "correcao-provas.service"; then
  systemctl restart correcao-provas
  sleep 2
  if systemctl is-active --quiet correcao-provas; then
    echo -e "${GREEN}✓ Serviço correcao-provas reiniciado e ATIVO com sucesso!${NC}"
  else
    echo -e "${RED}[AVISO] O serviço correcao-provas não está ativo. Verifique com: journalctl -u correcao-provas -n 50${NC}"
  fi
else
  echo -e "${YELLOW}[AVISO] Serviço systemd 'correcao-provas' não encontrado.${NC}"
fi

if command -v nginx >/dev/null 2>&1; then
  nginx -t 2>/dev/null && systemctl reload nginx || systemctl restart nginx 2>/dev/null || true
  echo -e "${GREEN}✓ Nginx recarregado com sucesso.${NC}"
fi

# 8. Verificação de Saúde (Health Check)
echo -e "\n${BLUE}🩺 Verificando resposta da API local...${NC}"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/api/backup/stats 2>/dev/null || echo "000")

echo -e "\n${GREEN}${BOLD}==============================================================================${NC}"
echo -e "${GREEN}${BOLD}    ✅ SISTEMA ATUALIZADO COM SUCESSO PARA A ÚLTIMA VERSÃO!                   ${NC}"
echo -e "${GREEN}${BOLD}==============================================================================${NC}"
echo -e "Último commit instalado: ${CYAN}$(git log -1 --pretty=format:'%h - %s (%ci)')${NC}"
echo -e "HTTP Local: ${BOLD}http://127.0.0.1:8080${NC} (Status HTTP: ${HEALTH_STATUS})"
echo -e "\nVocê já pode acessar sua plataforma atualizada com o novo Manual, GIFs reais e melhorias!\n"
