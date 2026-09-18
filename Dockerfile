FROM python:3.11-slim

# Evitar prompts interativos no apt
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Instalar dependências de sistema para OpenCV headless e PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependências Python
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copiar código do projeto
COPY backend /app/backend
COPY frontend /app/frontend

# Criar pastas de armazenamento
RUN mkdir -p /app/backend/storage/scans \
             /app/backend/storage/overlays \
             /app/backend/storage/sheets

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8080"]
