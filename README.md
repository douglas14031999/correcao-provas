# 🎯 Gabarito OMR & Elaborador de Provas

Sistema open-source completo, moderno e autohospedável para **Elaboração de Provas (BNCC)**, **Geração de Folhas de Respostas em PDF** e **Correção Instantânea via Câmera de Smartphone por Visão Computacional**.

---

## ⚡ Deploy Automatizado em VPS (1 Linha)

Para implantar em produção na sua VPS (Ubuntu/Debian) com **PostgreSQL**, **FastAPI**, **Nginx**, **Systemd** e **Certificado SSL**:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/douglas14031999/correcao-provas/main/install.sh)
```

### 🔄 Como Atualizar a VPS com Novas Versões
```bash
cd /var/www/correcao-provas && git fetch origin && git reset --hard origin/main && ./venv/bin/pip install -r backend/requirements.txt && PYTHONPATH=backend ./venv/bin/python backend/scripts/seed_question_bank.py && sudo chown -R www-data:www-data /var/www/correcao-provas && sudo systemctl restart correcao-provas
```

---

## ✨ Principais Funcionalidades

### 📝 1. Elaborador de Provas Integrado (Novo!)
- **Banco de Questões BNCC:** Acervo pré-cadastrado com habilidades do Ensino Fundamental (Língua Portuguesa, Matemática e Ciências).
- **Editor Matemático e Científico:** Suporte completo a fórmulas e equações via **KaTeX** e teclado virtual interativo **MathLive**.
- **Diagramação Profissional em 2 Colunas:** Algoritmo inteligente com paginação automática que evita quebra desnecessária de questões e cabeçalhos.
- **Exportação Multiformato:**
  - 📄 **PDF Diagramado:** Pronto para impressão em alta definição.
  - 📝 **Word (.docx):** Documento formatado e 100% editável.
- **Sincronização com o Corretor OMR:** Criação automática do gabarito oficial no sistema de correção com um clique.

### 🖨️ 2. Geração Avançada de Folhas de Respostas (OMR)
- **Folhas Nominais em Lote:** PDFs gerados com nome do estudante, turma, escola e matrícula pré-preenchidos.
- **Modo Folha Dupla (2 por página):** Permite imprimir 2 provas por folha A4 com linha de corte tracejada, gerando economia de 50% de papel.
- **Ata de Presença Automática:** A primeira página do lote contém a lista oficial de presença para assinatura dos alunos.
- **Etiquetas de Envelopes:** Geração de etiquetas em PDF para identificação e lacre dos pacotes de prova por turma.
- **Capas Oficiais Temáticas:** Modelos de capa estilizados com brasão municipal e cabeçalho institucional.
- **Download em Pacote ZIP:** Download consolidado de todas as turmas de uma escola em um único arquivo compactado.

### 📱 3. Correção Instantânea por Câmera (Mobile PWA)
- **Visão Computacional em Tempo Real:** Detecção matemática dos 4 marcadores ArUco nos cantos da folha.
- **Correção de Perspectiva (Perspective Warp):** Desentorta fotos tiradas em ângulos inclinados.
- **Leitura OMR de Alta Precisão:** Análise por densidade de pixels das bolhas preenchidas a caneta preta ou azul.
- **Raio-X Visual:** Exibe na tela do celular a imagem corrigida com anotações visuais (verde = acerto, vermelho = erro, amarelo = anulada).
- **Funciona como App Nativo (PWA):** Instale diretamente no celular via "Adicionar à Tela de Início", com suporte a offline e feedback tátil/sonoro.

### 📊 4. Gestão Escolar & Relatórios Estatísticos
- Cadastro de Escolas, Turmas e Alunos com **importação em massa via CSV**.
- Relatórios analíticos com percentual de acertos por questão, médias por turma e distribuição de notas.
- Exportação de planilhas consolidadas em **Excel (.xlsx)** e relatórios para impressão em **PDF**.
- Sistema de backup completo do banco de dados e arquivos com restauração facilitada.

---

## 🚀 Como Executar Localmente

### 1. Iniciar o Servidor Backend
No terminal (dentro da pasta do projeto):
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```
Ou diretamente:
```bash
python backend/app/main.py
```

### 2. Acessar a Interface
- **No Computador:** Abra no navegador: [http://localhost:8080](http://localhost:8080)
- **No Celular (mesma rede Wi-Fi):**
  1. Descubra o IP local do computador (ex: `ipconfig` no Windows $\rightarrow$ `192.168.1.X`).
  2. No navegador do smartphone, acesse: `http://192.168.1.X:8080`
  3. Para testar o Elaborador de Provas diretamente, acesse: `http://localhost:8080/elaborador.html`

---

## 🧪 Testes Automatizados

O sistema conta com suíte automatizada cobrindo fluxos de ponta a ponta:

```bash
# Executar toda a suíte de testes (38 testes)
python -m pytest backend/tests
```

**Módulos testados:**
- Leitura e processamento de OMR sintético e folha dupla.
- Geração de PDFs de lotes, etiquetas, capas e atas de presença.
- Autenticação com tokens, backup e integridade de exclusão.
- Motor de relatórios estatísticos e importação CSV de estudantes.

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologias |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn, Pydantic |
| **Visão Computacional & OMR** | OpenCV (`cv2.aruco`, `cv2.warpPerspective`), NumPy |
| **Processamento de Documentos** | ReportLab, PyMuPDF (fitz), python-docx, openpyxl, WeasyPrint |
| **Banco de Dados** | PostgreSQL (Produção VPS) / SQLite (Desenvolvimento local) |
| **Frontend** | HTML5 Semântico, Vanilla CSS, JavaScript ES6+, MathLive, KaTeX |
| **Infraestrutura & Deploy** | Nginx (Proxy Reverso & SSL Let's Encrypt), Systemd, Bash Scripting |

---

## 📄 Licença
Distribuído sob a licença open-source MIT. Desenvolvido para modernizar e agilizar a avaliação escolar na rede pública e privada.
