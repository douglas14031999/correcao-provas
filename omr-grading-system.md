# Task: Sistema Open-Source de Geração e Correção de Gabaritos via Câmera (OMR)

> **Slug:** `omr-grading-system`  
> **Status:** Planning Completed / Awaiting User Confirmation to Execute  
> **Agentes Responsáveis:** `orchestrator`, `backend-specialist`, `frontend-specialist`  
> **Skills Aplicadas:** `clean-code`, `api-patterns`, `frontend-design`, `webapp-testing`  

---

## 1. Visão Geral
Construção do sistema completo de geração de folhas de respostas vetoriais em PDF com marcadores fiduciais ArUco e motor OMR de correção em tempo real via câmera de smartphone (PWA).

## 2. Critérios de Sucesso
- [ ] Geração dinâmica de folhas A4 com ReportLab (de 5 a 100 questões, 4 ou 5 alternativas).
- [ ] Inclusão dos 4 marcadores ArUco nos cantos e QR Code com metadados.
- [ ] Motor OMR em Python com OpenCV que detecta os marcadores, desentorta a perspectiva e lê o preenchimento com acurácia > 99%.
- [ ] Interface Web/Mobile responsiva com câmera integrada para escanear a folha do celular.
- [ ] Visualização imediata do "Raio-X" da correção (verde para acertos, vermelho para erros) e nota calculada.

## 3. Divisão de Tarefas (Task Breakdown)

### Tarefa 1: Motor OMR & Visão Computacional (`backend-specialist`)
- **Input:** Foto bruta da folha com distorção de perspectiva e rotação.
- **Output:** Folha retificada, vetor de respostas assinaladas por questão e imagem com anotações visuais.
- **Verify:** Teste com imagem sintética rotacionada com 100% de precisão de leitura.

### Tarefa 2: Gerador Vetorial de Folhas PDF (`backend-specialist`)
- **Input:** Parâmetros da prova (número de questões, alternativas, título).
- **Output:** Arquivo PDF A4 milimétrico para impressão e mapa de coordenadas de bolhas JSON.
- **Verify:** Validação das coordenadas geradas contra o leitor OMR.

### Tarefa 3: API FastAPI e Persistência de Dados (`backend-specialist`)
- **Input:** Requisições REST para gerenciar provas e upload de imagens para correção.
- **Output:** JSON com nota, erros/acertos e persistência em SQLite.
- **Verify:** Execução de testes de integração com endpoint `/api/grade`.

### Tarefa 4: Frontend Web & Scanner Mobile PWA (`frontend-specialist`)
- **Input:** Design responsivo, acesso ao sensor de câmera traseira com guia visual de enquadramento.
- **Output:** Aplicação web interativa para desktop e celular.
- **Verify:** Carregamento de imagem e captura de câmera com retorno do resultado instantâneo.
