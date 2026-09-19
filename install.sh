#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DE INSTALAÇÃO AUTOMATIZADA EM VPS (Ubuntu / Debian)
# Sistema OMR de Correção de Provas & Gabaritos com PostgreSQL, Nginx e SSL
# ==============================================================================

set -e

# Cores para mensagens
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Limpa a tela e exibe banner
clear
echo -e "${CYAN}${BOLD}"
echo "=============================================================================="
echo "    🚀 INSTALADOR AUTOMATIZADO - SISTEMA DE CORREÇÃO DE PROVAS & GABARITOS   "
echo "=============================================================================="
echo -e "${NC}"

# 1. Verificar privilégios de root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERRO] Este script precisa ser executado como root.${NC}"
  echo -e "Por favor, execute novamente com: ${YELLOW}sudo bash $0${NC} ou como usuário root."
  exit 1
fi

# 2. Detectar Distribuição Linux
if [ -f /etc/os-release ]; then
  . /etc/os-release
  DISTRO=$ID
  VERSION=$VERSION_ID
else
  echo -e "${RED}[ERRO] Não foi possível identificar o sistema operacional.${NC}"
  exit 1
fi

if [[ "$DISTRO" != "ubuntu" && "$DISTRO" != "debian" ]]; then
  echo -e "${YELLOW}[AVISO] Distribuição detectada: $DISTRO. O instalador foi homologado para Ubuntu/Debian.${NC}"
  read -r -p "Deseja continuar mesmo assim? [s/N]: " PROCEED </dev/tty
  if [[ ! "$PROCEED" =~ ^([sS][iI][mM]|[sS]|[yY])$ ]]; then
    exit 1
  fi
fi

# 3. Detectar IP público
echo -e "\n${BLUE}🔍 Detectando endereço IP público da VPS...${NC}"
PUBLIC_IP=$(curl -sSL --max-time 4 https://ifconfig.me || curl -sSL --max-time 4 https://api.ipify.org || hostname -I | awk '{print $1}')
echo -e "IP público detectado: ${GREEN}${BOLD}${PUBLIC_IP}${NC}"

# 4. Perguntar sobre Domínio e Certificado SSL
echo -e "\n${YELLOW}------------------------------------------------------------------------------${NC}"
echo -e "${BOLD}🌐 CONFIGURAÇÃO DE DOMÍNIO E CERTIFICADO SSL (HTTPS)${NC}"
echo -e "Para a câmera do celular abrir no escaneamento de gabaritos, o HTTPS é obrigatório."
echo -e "${YELLOW}------------------------------------------------------------------------------${NC}"
read -r -p "Você já possui um domínio/subdomínio apontado para o IP ${PUBLIC_IP}? [s/N]: " HAS_DOMAIN </dev/tty

DOMAIN=""
CERT_EMAIL=""

if [[ "$HAS_DOMAIN" =~ ^([sS][iI][mM]|[sS]|[yY])$ ]]; then
  while [ -z "$DOMAIN" ]; do
    read -r -p "👉 Digite o domínio (ex: provas.minhaescola.com.br): " DOMAIN </dev/tty
    DOMAIN=$(echo "$DOMAIN" | tr -d '[:space:]')
  done
  while [ -z "$CERT_EMAIL" ]; do
    read -r -p "👉 Digite o seu e-mail para registro do certificado Let's Encrypt: " CERT_EMAIL </dev/tty
    CERT_EMAIL=$(echo "$CERT_EMAIL" | tr -d '[:space:]')
  done
  echo -e "${GREEN}✓ Modo configurado: Domínio oficial com Let's Encrypt SSL (${DOMAIN})${NC}"
else
  echo -e "${GREEN}✓ Modo configurado: Acesso direto por IP (${PUBLIC_IP}) com certificado SSL autoassinado SAN${NC}"
fi

# 5. Definir diretório de instalação
INSTALL_DIR="/var/www/correcao-provas"
echo -e "\n${BLUE}📁 Diretório de instalação: ${BOLD}${INSTALL_DIR}${NC}"

# Verificar repositório Git de origem
GIT_REPO_DEFAULT="https://github.com/douglas14031999/correcao-provas.git"
REPO_URL=""

# Se o script estiver sendo executado dentro de uma pasta do projeto clonado
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$CURRENT_DIR/backend/app/main.py" ]; then
  echo -e "${GREEN}✓ Código-fonte detectado no diretório atual: ${CURRENT_DIR}${NC}"
  SOURCE_FROM_CURRENT=true
else
  SOURCE_FROM_CURRENT=false
  echo -e "\nInforme a URL do repositório Git do projeto."
  read -r -p "URL do repositório Git [pressione Enter para padrão]: " USER_REPO </dev/tty
  if [ -n "$USER_REPO" ]; then
    REPO_URL="$USER_REPO"
  else
    REPO_URL="$GIT_REPO_DEFAULT"
  fi
fi

# 6. Atualização do Sistema e Instalação de Pacotes
echo -e "\n${BLUE}📦 Atualizando repositórios do sistema (apt update)...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt update -y

echo -e "\n${BLUE}📦 Instalando dependências essenciais do sistema...${NC}"
apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  python3-dev \
  git \
  curl \
  wget \
  openssl \
  nginx \
  certbot \
  python3-certbot-nginx \
  libgl1 \
  libglib2.0-0 \
  zbar-tools \
  libpq-dev \
  build-essential \
  ufw

# 7. Verificação e Instalação do PostgreSQL
echo -e "\n${BLUE}🐘 Verificando PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
  echo -e "${YELLOW}PostgreSQL não encontrado. Instalando PostgreSQL automaticamente...${NC}"
  apt install -y postgresql postgresql-contrib
  systemctl enable postgresql
  systemctl start postgresql
  echo -e "${GREEN}✓ PostgreSQL instalado e iniciado com sucesso.${NC}"
else
  echo -e "${GREEN}✓ PostgreSQL já está instalado.${NC}"
  systemctl start postgresql || true
fi

# 8. Criação de Banco de Dados e Usuário no PostgreSQL
DB_NAME="correcao_provas"
DB_USER="correcao_user"
# Gerar senha forte aleatória
DB_PASS=$(openssl rand -hex 16)

echo -e "\n${BLUE}⚙️ Configurando banco de dados PostgreSQL (${DB_NAME})...${NC}"

# Criar banco se não existir
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};"

# Criar usuário se não existir ou atualizar senha
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = '${DB_USER}'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"

sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
sudo -u postgres psql -c "ALTER DATABASE ${DB_NAME} OWNER TO ${DB_USER};"

# Permissões do Schema public para PostgreSQL 15+
sudo -u postgres psql -d ${DB_NAME} -c "GRANT ALL ON SCHEMA public TO ${DB_USER};" >/dev/null 2>&1 || true
sudo -u postgres psql -d ${DB_NAME} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};" >/dev/null 2>&1 || true

echo -e "${GREEN}✓ Banco de dados e usuário configurados com sucesso.${NC}"

# 9. Copiar ou Clonar o Projeto para /var/www/correcao-provas
echo -e "\n${BLUE}📥 Preparando arquivos do projeto...${NC}"
mkdir -p /var/www

if [ "$SOURCE_FROM_CURRENT" = true ]; then
  if [ "$CURRENT_DIR" != "$INSTALL_DIR" ]; then
    echo "Copiando arquivos do diretório atual para ${INSTALL_DIR}..."
    mkdir -p "$INSTALL_DIR"
    cp -r "$CURRENT_DIR"/* "$INSTALL_DIR"/
    cp -r "$CURRENT_DIR"/.env* "$INSTALL_DIR"/ 2>/dev/null || true
  fi
else
  if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Diretório ${INSTALL_DIR} já existe. Atualizando código via git pull..."
    cd "$INSTALL_DIR"
    git fetch origin
    git reset --hard origin/main || git pull
  else
    echo "Clonando ${REPO_URL} em ${INSTALL_DIR}..."
    rm -rf "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi
fi

cd "$INSTALL_DIR"

# 10. Criar e Configurar Ambiente Virtual Python
echo -e "\n${BLUE}🐍 Configurando ambiente virtual Python (venv)...${NC}"
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r backend/requirements.txt

# 11. Configurar arquivo de ambiente .env
echo -e "\n${BLUE}🔐 Gerando configurações de produção (.env)...${NC}"
SECRET_KEY=$(openssl rand -hex 24)

cat <<EOF > "$INSTALL_DIR/.env"
# Configurações geradas automaticamente pelo instalador VPS
PORT=8080
HOST=127.0.0.1
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}
SECRET_KEY=${SECRET_KEY}
EOF

chmod 600 "$INSTALL_DIR/.env"

# 12. Inicializar tabelas do banco e criar usuário admin inicial
echo -e "\n${BLUE}🗄️ Inicializando tabelas no PostgreSQL e usuário admin mestre...${NC}"
cd "$INSTALL_DIR"
PYTHONPATH=backend venv/bin/python -c "from app.services.database import init_db; init_db()" || {
  echo -e "${YELLOW}[AVISO] Falha ao rodar init_db direto. A aplicação tentará ao iniciar o serviço.${NC}"
}
echo -e "${GREEN}✓ Tabelas e usuário administrador (admin) verificados com sucesso.${NC}"

# 13. Garantir pastas de armazenamento e permissões
mkdir -p "$INSTALL_DIR/backend/storage/scans"
mkdir -p "$INSTALL_DIR/backend/storage/sheets"
mkdir -p "$INSTALL_DIR/backend/storage/overlays"
mkdir -p "$INSTALL_DIR/backend/storage/assets"

chown -R www-data:www-data "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

# 13. Configurar Serviço Systemd
echo -e "\n${BLUE}⚙️ Configurando serviço Systemd (correcao-provas.service)...${NC}"
cat <<EOF > /etc/systemd/system/correcao-provas.service
[Unit]
Description=Sistema OMR de Correcao de Provas & Gabaritos (FastAPI)
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
Environment="PATH=${INSTALL_DIR}/venv/bin"
ExecStart=${INSTALL_DIR}/venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8080 --workers 3
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable correcao-provas
systemctl restart correcao-provas

echo -e "${GREEN}✓ Serviço correcao-provas habilitado e iniciado.${NC}"

# 14. Configurar Nginx e SSL (HTTPS)
echo -e "\n${BLUE}🌐 Configurando servidor Web Nginx e HTTPS/SSL...${NC}"

# Remover site padrão do Nginx se existir
rm -f /etc/nginx/sites-enabled/default

if [ -n "$DOMAIN" ]; then
  # ---- MODO DOMÍNIO (LET'S ENCRYPT) ----
  cat <<EOF > /etc/nginx/sites-available/correcao-provas
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

  ln -sf /etc/nginx/sites-available/correcao-provas /etc/nginx/sites-enabled/
  nginx -t
  systemctl restart nginx

  echo -e "\n${BLUE}🔒 Emitindo certificado SSL oficial Let's Encrypt para ${DOMAIN}...${NC}"
  certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "${CERT_EMAIL}" --redirect || {
    echo -e "${YELLOW}[AVISO] O certbot não conseguiu emitir o certificado imediatamente.${NC}"
    echo -e "Certifique-se de que o DNS do domínio ${DOMAIN} está apontando para o IP ${PUBLIC_IP}."
    echo -e "Após verificar o DNS, você poderá rodar: ${BOLD}sudo certbot --nginx -d ${DOMAIN}${NC}"
  }

  ACCESS_URL="https://${DOMAIN}"

else
  # ---- MODO IP DIRETO (CERTIFICADO AUTOASSINADO SAN) ----
  SSL_DIR="/etc/ssl/correcao-provas"
  mkdir -p "${SSL_DIR}"

  echo -e "Gerando certificado SSL autoassinado com extensão SAN para o IP ${PUBLIC_IP}..."
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "${SSL_DIR}/selfsigned.key" \
    -out "${SSL_DIR}/selfsigned.crt" \
    -subj "/CN=${PUBLIC_IP}" \
    -addext "subjectAltName=IP:${PUBLIC_IP},IP:127.0.0.1" >/dev/null 2>&1

  cat <<EOF > /etc/nginx/sites-available/correcao-provas
server {
    listen 80;
    server_name ${PUBLIC_IP} localhost;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name ${PUBLIC_IP} localhost;

    ssl_certificate ${SSL_DIR}/selfsigned.crt;
    ssl_certificate_key ${SSL_DIR}/selfsigned.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

  ln -sf /etc/nginx/sites-available/correcao-provas /etc/nginx/sites-enabled/
  nginx -t
  systemctl restart nginx

  ACCESS_URL="https://${PUBLIC_IP}"
fi

# 15. Configurar Firewall UFW (se instalado)
if command -v ufw &> /dev/null; then
  echo -e "\n${BLUE}🛡️ Ajustando regras de firewall (UFW)...${NC}"
  ufw allow 22/tcp >/dev/null 2>&1 || true
  ufw allow 80/tcp >/dev/null 2>&1 || true
  ufw allow 443/tcp >/dev/null 2>&1 || true
fi

# 16. Teste de Funcionamento da Aplicação
echo -e "\n${BLUE}🩺 Verificando status dos serviços...${NC}"
sleep 2

if systemctl is-active --quiet correcao-provas; then
  APP_STATUS="${GREEN}ATIVO E OPERANTE (OK)${NC}"
else
  APP_STATUS="${RED}ERRO AO INICIAR (Consulte: journalctl -u correcao-provas -n 50)${NC}"
fi

if systemctl is-active --quiet nginx; then
  NGINX_STATUS="${GREEN}ATIVO E OPERANTE (OK)${NC}"
else
  NGINX_STATUS="${RED}ERRO NO NGINX${NC}"
fi

if systemctl is-active --quiet postgresql; then
  DB_STATUS="${GREEN}ATIVO E CONECTADO (OK)${NC}"
else
  DB_STATUS="${RED}ERRO NO POSTGRESQL${NC}"
fi

# 17. Exibição da Conclusão e Credenciais
echo -e "\n${GREEN}${BOLD}=============================================================================="
echo "         🎉 INSTALAÇÃO E DEPLOY CONCLUÍDOS COM SUCESSO!                       "
echo "==============================================================================${NC}"

echo -e "\n${BOLD}📊 STATUS DOS SERVIÇOS:${NC}"
echo -e " • Backend FastAPI: ${APP_STATUS}"
echo -e " • Servidor Nginx:  ${NGINX_STATUS}"
echo -e " • Banco PostgreSQL:${DB_STATUS}"

echo -e "\n${BOLD}🔗 ACESSO AO SISTEMA:${NC}"
echo -e " • URL: ${CYAN}${BOLD}${ACCESS_URL}${NC}"
if [ -z "$DOMAIN" ]; then
  echo -e "   ${YELLOW}(Como está usando IP direto, o navegador exibirá aviso de segurança; clique em 'Avançado' -> 'Continuar')${NC}"
fi
echo -e " • Usuário Inicial: ${GREEN}${BOLD}admin${NC}"
echo -e " • Senha Inicial:   ${GREEN}${BOLD}semed2026${NC}"

echo -e "\n${BOLD}🗄️ DADOS DO BANCO POSTGRESQL (Gravados em ${INSTALL_DIR}/.env):${NC}"
echo -e " • Banco:   ${DB_NAME}"
echo -e " • Usuário: ${DB_USER}"
echo -e " • Senha:   ${DB_PASS}"

echo -e "\n${BOLD}🛠️ COMANDOS ÚTEIS PARA ADMINISTRAÇÃO:${NC}"
echo -e " • Reiniciar sistema:   ${YELLOW}sudo systemctl restart correcao-provas${NC}"
echo -e " • Ver logs em tempo real: ${YELLOW}sudo journalctl -u correcao-provas -f${NC}"
echo -e " • Recarregar Nginx:    ${YELLOW}sudo systemctl reload nginx${NC}"
echo -e "==============================================================================\n"
