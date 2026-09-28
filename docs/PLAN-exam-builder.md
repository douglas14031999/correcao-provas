# PLAN-exam-builder.md - Módulo de Elaboração de Provas (Estilo Google Forms)

> **Módulo:** Elaborador de Provas e Avaliações  
> **Modo:** ISOLADO (Zero interferência nas rotas/tabelas existentes do sistema de correção)  
> **Ambiente:** LOCALHOST APENAS (Nenhum commit no Git)  
> **Agente Líder:** `project-planner` → `frontend-specialist` + `backend-specialist`  
> **Status:** Em Planejamento / Aguardando Aprovação  

---

## 1. Visão Geral e Objetivos

Criar um módulo novo e independente para **elaboração de provas no estilo Google Forms**, permitindo que professores criem facilmente avaliações completas, diagramadas e prontas para impressão em PDF.

### Recursos Centrais Solicitados:
1. **Editor de Questões Interativo:**
   - Adicionar questões dinamicamente.
   - Adicionar e remover alternativas (A, B, C, D, E).
   - Indicar com um clique qual é a alternativa correta (gabarito).
   - Inserção de imagens por questão com controle de posicionamento (acima, abaixo, ao lado, centralizada) e escala.
   - Suporte completo a **símbolos e estruturas matemáticas** (LaTeX via KaTeX + teclado/barra rápida de símbolos comuns com 1 clique).
2. **Diagramação e Impressão:**
   - Seletor de **1 coluna por página** OU **2 colunas por página** (estilo vestibular/ENEM para economia de papel).
   - Configuração de **Cabeçalho** (Órgão/SEMED, Escola, Disciplina, Professor, Aluno, Turma, Data, Nota, Logotipo/Brasão).
   - Configuração de **Rodapé** (texto personalizado e numeração de páginas).
   - Quebra inteligente de questões (`break-inside: avoid;`) para evitar cortes feios de questões no meio de colunas ou páginas.
3. **Geração de PDF com 1 Clique:**
   - Visualização prévia idêntica à impressão física.
   - Geração de PDF em alta definição configurado e pronto para envio à impressora.

---

## 2. Garantia de Isolamento e Segurança Local

- **Sem commits no Git:** Nada será commitado ou enviado ao GitHub durante todo o processo de implementação e teste em localhost.
- **Tabelas do Banco Isoladas:** Criadas exclusivamente com prefixo `builder_*` (`builder_exams`, `builder_questions`, `builder_alternatives`) sem alterar ou tocar nas tabelas existentes do sistema.
- **Rotas Backend Isoladas:** Concentradas em um único arquivo `backend/app/api/exam_builder.py` sob o prefixo `/api/exam-builder/`.
- **Frontend Isolado:** Arquivos dedicados `frontend/elaborador.html`, `frontend/elaborador.js`, `frontend/elaborador.css`, sem dependências que afetem o funcionamento do `index.html` e `app.js`.

---

## 3. Estrutura de Arquivos

| Arquivo | Função | Estado |
|---|---|---|
| `backend/app/api/exam_builder.py` | Rotas de CRUD de provas, upload de imagens e geração de PDF | Novo |
| `backend/app/services/exam_builder_pdf.py` | Mecanismo de diagramação de impressão A4 e compilação em PDF | Novo |
| `frontend/elaborador.html` | Interface do editor estilo Google Forms + Live Preview | Novo |
| `frontend/elaborador.js` | Lógica interativa, reordenação de cards, KaTeX e upload | Novo |
| `frontend/elaborador.css` | Design do editor e regras de impressão em 1 ou 2 colunas | Novo |
| `storage/builder_images/` | Diretório para upload das imagens das questões | Novo |

---

## 4. Decomposição de Tarefas (INPUT → OUTPUT → VERIFY)

### [TASK-01] Backend: Estrutura de Banco e Rotas de CRUD
- **Agente:** `backend-specialist` | **Skill:** `clean-code`, `api-patterns`
- **INPUT:** Especificação dos campos de prova (título, disciplina, cabeçalho, rodapé, colunas) e questões (enunciado, imagem, posição, alternativas, correta).
- **OUTPUT:** `backend/app/api/exam_builder.py` com endpoints `GET`, `POST`, `PUT`, `DELETE` e inicialização das tabelas `builder_*`.
- **VERIFY:** Testar requisições de criação e recuperação de uma prova com 3 questões via curl local em `http://localhost:8080/api/exam-builder/exams`.

### [TASK-02] Backend: Upload de Imagens das Questões
- **Agente:** `backend-specialist` | **Skill:** `clean-code`
- **INPUT:** Upload multipart/form-data de imagem (PNG, JPG, WebP).
- **OUTPUT:** Salvamento em `storage/builder_images/` com nome único e retorno de URL pública estática `/storage/builder_images/{filename}`.
- **VERIFY:** Upload de imagem de teste e confirmação de acesso via browser.

### [TASK-03] Frontend: Interface do Editor de Provas (Estilo Google Forms)
- **Agente:** `frontend-specialist` | **Skill:** `frontend-design`, `clean-code`
- **INPUT:** Protótipo de cards de questões expansíveis e interativos.
- **OUTPUT:** `frontend/elaborador.html` com cabeçalho de configurações, barra de ferramentas, lista de cartões de questões, seleção de alternativa correta e botão de adicionar questão.
- **VERIFY:** Renderização fluida, criação de novas questões, seleção visual da resposta correta e exclusão/duplicação de cartões.

### [TASK-04] Frontend: Suporte a Fórmulas Matemáticas (KaTeX) e Teclado de Símbolos
- **Agente:** `frontend-specialist` | **Skill:** `frontend-design`
- **INPUT:** Biblioteca KaTeX (CSS + JS offline/local ou CDN confiável).
- **OUTPUT:** Renderização em tempo real de expressões matemáticas no enunciado e alternativas, acompanhado de barra rápida de símbolos ($\pi, \sqrt{}, \frac{a}{b}, x^2, \pm, \le, \ge, \neq, \alpha, \beta, \Delta, \int$, etc.).
- **VERIFY:** Digitar frações e raízes e verificar renderização nítida imediata no card.

### [TASK-05] Frontend & Backend: Diagramação em 1 ou 2 Colunas e Cabeçalho/Rodapé
- **Agente:** `frontend-specialist` + `backend-specialist` | **Skill:** `frontend-design`
- **INPUT:** Seletor de colunas (1 ou 2), campos de cabeçalho configuráveis (escola, professor, data, aluno, turma, nota, logo) e rodapé.
- **OUTPUT:** Folha de estilos `frontend/elaborador.css` com `@media print` e classes para layout em 1 ou 2 colunas com quebra de página controlada (`break-inside: avoid;`).
- **VERIFY:** Alternar entre 1 e 2 colunas e conferir readequação automática do conteúdo sem sobreposição.

### [TASK-06] Geração e Impressão de PDF de Alta Fidelidade
- **Agente:** `backend-specialist` | **Skill:** `clean-code`
- **INPUT:** Prova finalizada com todas as questões, fórmulas e imagens.
- **OUTPUT:** Botão "Gerar PDF para Impressão" acionando o gerador Chrome Headless do backend ou impressão direta do navegador.
- **VERIFY:** Download do arquivo `.pdf` gerado em A4, verificação da legibilidade das fórmulas matemáticas, alinhamento das imagens e integridade das 2 colunas.

### [TASK-07] Ponto de Entrada Seguro no Sistema e Verificação Geral
- **Agente:** `orchestrator` | **Skill:** `clean-code`
- **INPUT:** Sistema rodando em localhost.
- **OUTPUT:** Link discreto no menu lateral "Elaborador de Provas" abrindo a nova tela isolada.
- **VERIFY:** Confirmar que o sistema original de correção de gabaritos continua 100% inalterado e funcional, sem conflitos de rotas.

---

## 5. Checklist de Verificação (Phase X)

- [ ] Todas as tabelas criadas são independentes e começam com `builder_`
- [ ] O sistema principal de correção de gabaritos e leitura de cartões continua operando normalmente
- [ ] O editor permite adicionar questões, alternativas e definir a correta
- [ ] As fórmulas matemáticas renderizam perfeitamente com KaTeX
- [ ] As imagens podem ser inseridas com alinhamento e tamanho configuráveis
- [ ] A troca entre 1 coluna e 2 colunas funciona instantaneamente
- [ ] O cabeçalho e rodapé são personalizáveis e respeitados na impressão
- [ ] O PDF é gerado limpo, sem cortes incorretos de questões entre páginas
- [ ] Nenhum arquivo foi enviado ou comitado no Git
