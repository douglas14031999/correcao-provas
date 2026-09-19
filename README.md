# 🎯 Gabarito OMR — Sistema de Geração e Correção de Provas via Câmera

Sistema 100% open-source, autohospedável e pronto para uso para criação de folhas de respostas em PDF e correção instantânea por visão computacional através da câmera de smartphones.

---

## ⚡ Deploy Automatizado em VPS (1 Linha)

Para implantar em produção em uma VPS (Ubuntu/Debian) com **PostgreSQL**, **Nginx**, **Systemd** e **Certificado SSL**:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/douglas14031999/correcao-provas/main/install.sh)
```

---

## 🚀 Como Executar Localmente

### 1. Iniciar o Servidor
No terminal, execute:
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
  1. Descubra o IP do seu computador na rede local (ex: `ipconfig` no Windows $\rightarrow$ IPv4 `192.168.1.X`).
  2. No navegador do celular (Chrome ou Safari), acesse: `http://192.168.1.X:8080`
  3. Você pode clicar em "Adicionar à Tela Inicial" para usá-lo em tela cheia como um aplicativo nativo (PWA).

---

## 📋 Como Funciona

### 1. Criar um Simulado ou Prova
1. Acesse a aba **"Criar Simulado"**.
2. Preencha o título (ex: *Simulado ENEM 2026 - Matemática*), o número de questões (ex: 20, 50, 90) e o tipo de alternativas (4 [A-D] ou 5 [A-E]).
3. Defina o gabarito oficial com um clique nas bolinhas de cada questão.
4. Clique em **"Gerar Simulado & Folha PDF"**.

### 2. Imprimir a Folha de Respostas
1. Na aba **"Meus Simulados"**, clique no botão **"PDF A4"**.
2. Uma folha milimétrica de alta definição será gerada contendo:
   - Os **4 Marcadores ArUco** nos cantos.
   - O **QR Code** de identificação da prova.
   - Os campos para nome, turma e data.
   - A grade vetorial de bolhas.
3. Imprima a folha em papel A4 comum.

### 3. Corrigir com a Câmera do Celular
1. Distribua as folhas para os alunos e peça para preencherem com caneta preta ou azul.
2. No celular ou computador, acesse a aba **"Corrigir Prova"**.
3. Aponte a câmera para a folha, enquadrando os 4 marcadores ArUco dentro da moldura da tela.
4. Clique em **"Escanear Folha"** (ou envie uma foto salva pela opção *Galeria / Arquivo*).
5. Em menos de 800ms, o sistema:
   - Desentorta a perspectiva da foto matematicamente (Perspective Warp).
   - Analisa a densidade de preenchimento das bolhas.
   - Calcula a nota e os pontos.
   - Exibe na tela o **Raio-X visual** com círculos verdes nos acertos e vermelhos nos erros!

---

## 🧪 Testes Automatizados

O sistema inclui testes de estresse com geração sintética de folhas inclinadas e upload via API REST:

```bash
# Teste de precisão matemática e visão computacional OMR
python backend/tests/test_omr_synthetic.py

# Teste de upload HTTP multipart de ponta a ponta
python backend/tests/test_api_upload.py
```

---

## 🛠️ Stack Tecnológica

- **Backend:** Python 3.11 + FastAPI + Uvicorn
- **Visão Computacional & OMR:** OpenCV 4.11 (`cv2.aruco`, `warpPerspective`, `adaptiveThreshold`) + NumPy
- **Gerador de Folhas:** ReportLab Community (Renderização vetorial A4 com QR Code)
- **Banco de Dados:** SQLite embutido (`backend/storage/exams.db`)
- **Frontend / PWA:** HTML5 + Vanilla CSS + JavaScript ES6 + WebRTC Camera API + Web Audio API
