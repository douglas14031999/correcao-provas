# Plano de Implementação: Gerador de Questões Inéditas com IA (Groq - Llama 3.1 8B + BNCC)

## 1. Visão Geral
Integrar a API gratuita da **Groq Cloud** utilizando o modelo open-source **Llama 3.1 8B Instant** (`llama-3.1-8b-instant`) para gerar questões pedagógicas inéditas, rigorosamente alinhadas à BNCC e aos padrões SAEB, com suporte a contextualização local (Alagoas/Lagoa da Canoa) e controle fino pelo professor/coordenador.

## 2. Requisitos Confirmados
1. **Gestão da Chave de API:** Campo nas Configurações do Sistema (`system_settings`) com suporte a chave no `.env` (`GROQ_API_KEY`) e botão para testar a conexão.
2. **Destino da Questão:** Opção de salvar diretamente no Banco de Questões e/ou adicionar diretamente à Prova Atual.
3. **Controle Pedagógico:** Geração 1 por vez com card de pré-visualização e edição completa antes de salvar.
4. **Parâmetros:**
   - Componente Curricular (Disciplina);
   - Ano/Série (1º ao 9º Ano);
   - Código e descrição da BNCC (com atalho para o catálogo oficial da BNCC do sistema);
   - Nível de Dificuldade (Fácil, Médio, Difícil);
   - Quantidade de alternativas (4 alternativas A-D ou 5 alternativas A-E);
   - Tema / Contexto Local (ex: Alagoas, Lagoa da Canoa, cotidiano do estudante, texto-base).
5. **Casos de Borda:**
   - Mensagem clara e link amigável caso a chave não esteja configurada ou cota excedida.
   - Edição livre do enunciado, alternativas e seleção do gabarito correto antes da gravação.

## 3. Arquitetura e Componentes

### 3.1 Backend
- **`backend/app/services/groq_service.py`**:
  - Obtenção da chave `GROQ_API_KEY` (banco de dados `system_settings` ou variável de ambiente).
  - Chamada à API da Groq (`https://api.groq.com/openai/v1/chat/completions`) com `response_format: {"type": "json_object"}`.
  - Prompt pedagógico especialista na BNCC, taxonomia de Bloom e distratores plausíveis SAEB.
  - Função para testar a validade da chave Groq.
- **`backend/app/api/settings.py`**:
  - Exposição de `groq_api_key` (mascarada para leitura, configurável por Admin/Coordenador).
  - Endpoint `POST /api/settings/test-groq-key`.
- **`backend/app/api/exam_builder.py`**:
  - Endpoint `POST /api/exam-builder/ai/generate-question`.
  - Endpoint `POST /api/exam-builder/ai/save-to-bank` para inserção atômica na tabela `builder_questions` e `builder_alternatives`.

### 3.2 Frontend
- **Configurações (`frontend/index.html` + `frontend/app.js`)**:
  - Novo card/campo: "Inteligência Artificial (Groq Cloud API)" com input de chave, status de conexão e botão "Testar Chave".
- **Banco de Questões (`frontend/provas.html` + `frontend/provas.js`)**:
  - Botão de destaque: `+ Gerar Questão com IA`.
  - Modal interativo `#modal-ai-question-generator`:
    - Formulário com Disciplina, Ano, BNCC (com botão de busca), Dificuldade, Alternativas e Contexto Local.
    - Área de loading animada com feedback pedagógico.
    - Card de prévia interativa com campos de input para edição do enunciado e alternativas.
    - Botão "Salvar no Banco de Questões".
- **Elaborador de Provas (`frontend/elaborador.html` + `frontend/elaborador.js`)**:
  - Botão "Gerar com IA" na barra lateral e toolbar rápida.
  - Inserção imediata na prova em edição.

## 4. Plano de Testes e Validação
- Teste unitário do serviço Groq com mock e teste de formato JSON.
- Teste do endpoint de geração e salvamento no banco de questões.
- Teste de fluxo no navegador (UI responsiva, sem violações do design system Prova Canoa).
