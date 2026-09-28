# Sincronização do Elaborador de Provas com Gabarito OMR e Capas Oficiais

## Objetivo
Permitir que em cada prova criada no elaborador (tanto em `provas.html` quanto no `elaborador.html`), o usuário possa clicar em um botão para abrir um modal simplificado, configurar a vinculação com uma das capas oficiais de Lagoa da Canoa e gerar/atualizar o gabarito completo no sistema de correção com validação de alternativas corretas.

## Tarefas
- [x] Task 1: Criar endpoint `POST /api/exam-builder/exams/{exam_id}/create-grading-exam` no backend com validação de respostas corretas (Edge Case 1), geração da folha OMR com capa e sincronização com a tabela `exams` → Concluído e verificado.
- [x] Task 2: Implementar o Modal Simplificado de Configuração de Gabarito & Capa e botões de ação em `frontend/provas.html` e `frontend/provas.js` (na tabela e nos cards) → Concluído e verificado.
- [x] Task 3: Integrar o botão e modal na barra superior de `frontend/elaborador.html` e `frontend/elaborador.js` → Concluído e verificado.
- [x] Task 4: Implementar o fluxo de sucesso pós-criação (Edge Case 2) com botões para "Abrir Folha OMR (PDF)" e "Ir para Correção" sem fechar abruptamente → Concluído e verificado.
- [x] Task 5: Validação completa e testes de regressão (provas com questões completas vs provas com questões sem alternativa correta marcada) → Concluído e verificado.

## Concluído Quando
- O botão "Criar Gabarito OMR" estiver visível e funcional na listagem (`provas.html`) e no elaborador (`elaborador.html`).
- O modal simplificado exibir as 4 opções de capas oficiais de Lagoa da Canoa e dados da avaliação.
- Se houver questão sem alternativa correta, o sistema barrar com alerta vermelho indicando quais questões precisam de gabarito.
- Ao confirmar, o gabarito for criado/atualizado no sistema principal de correção e a folha OMR com capa puder ser aberta em PDF imediatamente.
