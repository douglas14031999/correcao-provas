# Plano de Implementação: Painel Analítico SALVEAL no Relatório da Turma

## 1. Contexto e Objetivo
Integrar ao Relatório da Turma (`classroom-report-view`) da plataforma de correção os novos componentes visuais de diagnóstico pedagógico no padrão SALVEAL / SAEB / CAEd, com idêntica estrutura, design e paleta de cores das imagens fornecidas pelo usuário:
1. **Card 1 - Estudantes Avaliados:** Total de alunos avaliados no ciclo/simulado com link "Ver mais".
2. **Card 2 - Estudantes com Aprendizagem Adequada & Distribuição por Níveis:** Percentual de aprendizagem adequada (≥ 70%), barra horizontal segmentada (Defasagem, Intermediário, Adequado) e legenda detalhada com contagem de alunos e percentuais.
3. **Seção - Percentual de Acerto por Habilidade:** Filtro dropdown ("Todos" ou habilidade específica), botões de habilidade no formato `H 01 (Código)` com taxa de acerto colorida conforme faixas (Até 40%, 41-60%, 61-80%, Acima de 80%), legenda oficial e modal "Ver mais" para detalhamento pedagógico.
4. **Posicionamento:** Nova seção dedicada posicionada logo abaixo dos KPIs atuais, mantendo a compatibilidade e riqueza de dados já existentes.

## 2. Estrutura Técnica

### Backend (`backend/app/services/database.py` e rotas de relatório):
- Enriquecer `get_classroom_report`:
  - Calcular `learning_levels`:
    - `adequado`: contagem e percentual de alunos com aproveitamento ≥ 70.0%
    - `intermediario`: contagem e percentual de alunos com aproveitamento entre 50.0% e 69.9%
    - `defasagem`: contagem e percentual de alunos com aproveitamento < 50.0%
    - Listas nominais de alunos em cada nível para o modal "Ver mais"
  - Calcular `skills_performance`:
    - Associar cada questão ao seu código de habilidade BNCC / Matriz (buscando de `builder_questions` ou `exams.weights`/metadados, com fallback limpo para `H 01 (Item 1)`)
    - Calcular percentual de acerto, quantidade de acertos, faixa de corte e cores
- Suportar endpoint ou modal para salvar/editar códigos de habilidade caso o professor/coordenador deseje customizar.

### Frontend (`frontend/index.html`, `frontend/styles.css`, `frontend/app.js`):
- **HTML (`index.html`):**
  - Estrutura da seção `.salveal-analytics-section`:
    - Grid de 2 cards superiores no topo da seção analítica:
      - Card "Estudantes avaliados" com botão "Ver mais"
      - Card "Estudantes com aprendizagem adequada" com barra segmentada e legenda tripla
    - Card expandido "Percentual de acerto por habilidade":
      - Header com título e botão "Ver mais"
      - Seletor de filtro "Acerto por habilidade" (Todos / Habilidades específicas)
      - Grid de badges com classes de cor: `.skill-badge-critical`, `.skill-badge-low`, `.skill-badge-medium`, `.skill-badge-high`
      - Legenda horizontal com marcadores circulares
  - Modal "Ver mais" (`modal-salveal-details`) para exibir:
    - Lista de alunos por nível de aprendizagem com notas e situação
    - Detalhes pedagógicos das habilidades com diagnósticos de intervenção
- **CSS (`styles.css`):**
  - Estilização fiel às imagens:
    - Cores exatas: Coral/Vermelho (`#ea5a47`), Pêssego/Laranja (`#fca374`), Ciano Claro (`#9fe3ea`), Azul Turquesa Vivo (`#00b8d4`), Amarelo (`#eab308`), Roxo/Índigo suave (`#7c82fb`).
    - Tipografia limpa, bordas suaves de card (`border: 1px solid #e2e8f0; border-radius: 10px; background: #ffffff;`), padding e espaçamentos equilibrados.
- **JavaScript (`app.js`):**
  - Função `renderSalvealClassroomAnalytics(data)` chamada em `loadClassroomReportPage(classId, examId)`.
  - Filtro interativo no dropdown de habilidades para destacar/filtrar cards.
  - Funções de abertura e exibição do modal "Ver mais".

## 3. Testes e Validação
- Testar carregamento com turma com provas corrigidas e turma sem provas corrigidas.
- Testar responsividade e filtros.
- Garantir que nenhum relatório existente ou exportação seja quebrado.
