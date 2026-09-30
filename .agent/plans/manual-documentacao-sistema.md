# Plano de Implementação: Manual do Usuário e Documentação do Sistema

## 1. Visão Geral
Criar uma página completa de documentação e manual de uso passo a passo da plataforma **Prova Canoa**, projetada com estética moderna, navegação intuitiva, busca rápida, tutoriais detalhados e animações/simuladores visuais interativos demonstrando o fluxo de cada módulo do sistema.

## 2. Requisitos e Escopo (Validados via Socratic Gate)
- **Pontos de Acesso:**
  - Rodapé do card de login (exatamente sob "Acesso restrito", demarcado pelo usuário).
  - Barra de navegação do sistema e menu de Gestão (desktop e mobile).
- **Módulos Abrangidos no Manual:**
  1. **Introdução & Arquitetura**: Visão geral da tecnologia OMR ArUco, matriz BNCC e segurança.
  2. **Controle de Acesso & Autenticação**: Perfis (SEMED/Admin, Coordenador, Professor/Aplicador).
  3. **Dashboard & Indicadores Macros**: Leitura das métricas, cards de rendimento e gráficos.
  4. **Correção de Provas (Scanner OMR)**: Câmera nativa móvel, upload de imagens/PDFs, calibração e auditoria.
  5. **Criação de Provas & Gabaritos (Nova Prova)**: Configuração de cabeçalho, paletas de cores, capas estilizadas e geração de PDF.
  6. **Elaborador de Avaliações (Módulo Pedagógico)**: Banco de itens, seleção de habilidades BNCC, formatação automática e exportação.
  7. **Gestão de Escolas, Turmas e Estudantes**: Cadastro de unidades, enturmação, anos letivos e listagens.
  8. **Relatórios Pedagógicos & Rendimento**: Boletim individual, matriz de proficiência, rendimento por escola e exportação para Excel.
  9. **Backup, Restauração & Governança**: Geração de cópias criptografadas em .ZIP e restauração segura.
  10. **Guia de Boas Práticas OMR**: Como orientar estudantes no preenchimento de bolhas, dicas de iluminação para celular e resolução de problemas comuns.
- **Formato:**
  - Página dedicada `/manual` e `/docs` com layout moderno de documentação (sidebar sticky com índice por seção, busca instantânea por palavras-chave, modo escuro/claro, simuladores animados em SVG/CSS reproduzindo o comportamento das telas).

## 3. Arquivos a Criar e Modificar
- **Backend:**
  - `backend/app/main.py`: Adicionar rotas `/manual` e `/docs` servindo `frontend/manual.html`.
- **Frontend:**
  - `frontend/manual.html`: Estrutura semântica e rica com todos os módulos, guias e simuladores visuais.
  - `frontend/manual.css`: Estilização premium (paleta harmônica, tipografia Inter, cartões interativos, badges coloridos, animações suaves).
  - `frontend/manual.js`: Busca instantânea (filtro de seções e tópicos), links de navegação rápida, controle de abas de tutoriais, toggle dark/light mode e atalho para impressão em PDF.
  - `frontend/index.html`: Inclusão do link de acesso no card de login (sob "Acesso restrito") e no menu de gestão do cabeçalho.
  - `frontend/styles.css`: Estilização do link de manual no card de login.

## 4. Critérios de Aceite e Verificação (Homologado)
- [x] A rota `http://localhost:8080/manual` (e `/static/manual.html`) carrega perfeitamente com todas as 10 seções, simuladores e índice funcional.
- [x] O link no card de login (sob "Acesso restrito") abre o manual em nova aba sem quebrar o layout do login.
- [x] O botão no menu superior (`admin-dropdown-menu` e `mobile-drawer`) permite aos usuários logados abrirem o manual a qualquer momento.
- [x] A busca por termos (ex: "scanner", "BNCC", "gabarito", "backup") destaca e filtra as seções instantaneamente.
- [x] **6 GIFs Animados de Alta Resolução** gerados e incorporados nas seções em cards estilizados de janela:
  - `gif_1_login.gif`: Demonstração do Login Seguro, token JWT e acesso ao manual.
  - `gif_2_scanner.gif`: Leitura OMR pela câmera ao vivo, cantos ArUco, feixe de laser, detecção de bolhas e cálculo da nota 10.0/10.0.
  - `gif_3_nova_prova.gif`: Cadastro de prova, seleção de 5º Ano, cores oficiais, 20 questões e preenchimento da matriz.
  - `gif_4_elaborador.gif`: Filtro por disciplina e série, busca da habilidade `EF05MA08`, visualização e inserção no caderno.
  - `gif_5_turmas.gif`: Cadastro da turma "5º ANO B", colagem em lote da lista de estudantes e salvamento.
  - `gif_6_relatorios.gif`: Visualização da média da turma (8.4), barras de proficiência BNCC e exportação em Excel (.xlsx).
- [x] **Passo a Passo Detalhado** em todas as seções: tabelas de campos com exemplos, botões de ação com tags visuais, checklists de validação, avisos de impressão (escala 100%) e FAQs completas.
- [x] **Visualizador Lightbox**: clique em qualquer GIF para ampliar em tela cheia com alta nitidez.
- [x] Todos os 27 testes unitários do backend continuam passando com 100% de sucesso.

