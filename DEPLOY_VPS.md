# Guia Completo de Deploy na VPS (Ubuntu / Debian)

Este documento descreve o processo completo para colocar o **Sistema OMR de Correção de Provas & Gabaritos** em produção na sua VPS com **PostgreSQL**, **FastAPI** e **Nginx (com HTTPS/SSL)**.

---

## 📋 Pré-requisitos na VPS

- Sistema Operacional: Ubuntu 22.04 LTS / 24.04 LTS ou Debian 11/12
- Acesso SSH com privilégios `sudo`
- Domínio ou subdomínio apontando para o IP da VPS (ex: `provas.semed.seudominio.gov.br`)

---

## 🚀 Passo 1: Atualizar o Sistema e Instalar Pacotes Essenciais

Execute no terminal da VPS:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx postgresql postgresql-contrib libgl1 libglib2.0-0
```

---

## 🐘 Passo 2: Configurar o Banco de Dados PostgreSQL

1. Acesse o terminal do PostgreSQL:
```bash
sudo -u postgres psql
```

2. Crie o banco de dados e o usuário com senha segura:
```sql
CREATE DATABASE correcao_provas;
CREATE USER correcao_user WITH PASSWORD 'SUA_SENHA_SEGURA_AQUI';
GRANT ALL PRIVILEGES ON DATABASE correcao_provas TO correcao_user;
ALTER DATABASE correcao_provas OWNER TO correcao_user;
\q
```

---

## 📥 Passo 3: Clonar o Repositório e Configurar o Ambiente

1. Clone o projeto para o diretório `/var/www/correcao-provas`:
```bash
sudo git clone https://github.com/SEU_USUARIO/correcao-provas.git /var/www/correcao-provas
sudo chown -R $USER:$USER /var/www/correcao-provas
cd /var/www/correcao-provas
```

2. Crie e ative o ambiente virtual Python:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

3. Configure o arquivo `.env`:
```bash
cp .env.example .env
nano .env
```
Edite preenchendo sua `DATABASE_URL` do PostgreSQL e gere uma `SECRET_KEY`:
```env
PORT=8080
HOST=127.0.0.1
DATABASE_URL=postgresql://correcao_user:SUA_SENHA_SEGURA_AQUI@localhost:5432/correcao_provas
SECRET_KEY=gere_uma_chave_longa_e_aleatoria_aqui
```

4. *(Opcional)* Se desejar migrar os usuários e dados base do seu SQLite de desenvolvimento:
```bash
python3 backend/scripts/migrate_sqlite_to_postgres.py
# Ou para trazer também escolas já cadastradas:
# python3 backend/scripts/migrate_sqlite_to_postgres.py --with-schools
```

---

## ⚙️ Passo 4: Configurar Serviço Systemd (Inicialização Automática)

Crie o arquivo de serviço do sistema para manter a API sempre ativa:

```bash
sudo nano /etc/systemd/system/correcao-provas.service
```

Cole a configuração abaixo:

```ini
[Unit]
Description=Servidor OMR Correcao de Provas FastAPI
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/correcao-provas
Environment="PATH=/var/www/correcao-provas/venv/bin"
ExecStart=/var/www/correcao-provas/venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8080 --workers 2

Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Ajuste as permissões das pastas de armazenamento:
```bash
sudo chown -R www-data:www-data /var/www/correcao-provas
sudo chmod -R 755 /var/www/correcao-provas
```

Inicie e habilite o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable correcao-provas
sudo systemctl start correcao-provas
sudo systemctl status correcao-provas
```

---

## 🌐 Passo 5: Configurar o Nginx e Certificado SSL (HTTPS)

> [!IMPORTANT]
> O acesso via **HTTPS** é obrigatório para que os navegadores em celulares permitam abrir a **câmera fotográfica** para escaneamento dos gabaritos.

1. Crie o arquivo de configuração do Nginx:
```bash
sudo nano /etc/nginx/sites-available/correcao-provas
```

2. Cole o conteúdo (substitua `seu-dominio.com.br` pelo seu domínio real):
```nginx
server {
    listen 80;
    server_name seu-dominio.com.br;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Ative o site e reinicie o Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/correcao-provas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. Emita o certificado SSL gratuito Let's Encrypt:
```bash
sudo certbot --nginx -d seu-dominio.com.br
```

---

## 🔒 Passo 6: Verificação Final

- Acesse no navegador: `https://seu-dominio.com.br`
- Faça login com o usuário mestre padrão:
  - **Usuário:** `admin`
  - **Senha:** `semed2026`
- **Recomendação de Segurança**: Altere a senha do usuário `admin` na tela de Gestão de Usuários assim que acessar a produção!
