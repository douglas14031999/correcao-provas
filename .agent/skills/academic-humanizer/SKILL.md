---
name: academic-humanizer
description: Diretrizes e padrões para produção de artigos científicos e textos acadêmicos indetectáveis por ferramentas de plágio (CopySpider, Plagius) e detectores estilométricos de inteligência artificial (Turnitin AI, GPTZero, ZeroGPT, Copyleaks).
allowed-tools: Read, Glob, Grep, Write, Edit
---

# Academic Humanizer & Anti-Plagiarism Protocol

> Padrão de engenharia textual e estilometria acadêmica para produção de artigos científicos com alto rigor epistemológico, total originalidade sintática e completa indetectabilidade por ferramentas de plágio (CopySpider) e modelos de classificação probabilística de IA (Turnitin, GPTZero, Copyleaks).

---

## 🎯 1. Modelos de Ameaça e Mecanismos de Detecção

Para garantir a aprovação sem ressalvas, o texto gerado deve neutralizar simultaneamente dois mecanismos de auditoria fundamentalmente distintos:

```
                  ┌──────────────────────────────────────────────────────────┐
                  │              AUDITORIA DO TEXTO ACADÊMICO                │
                  └────────────────────────────┬─────────────────────────────┘
                                               │
             ┌─────────────────────────────────┴─────────────────────────────────┐
             ▼                                                                   ▼
┌──────────────────────────────┐                           ┌──────────────────────────────┐
│  VARREDURA DE PLÁGIO / N-GRAM│                           │ DETECÇÃO PROBABILÍSTICA / IA │
│   (CopySpider, Plagius)      │                           │  (Turnitin AI, GPTZero)      │
├──────────────────────────────┤                           ├──────────────────────────────┤
│ • Busca de cadeias literais  │                           │ • Perplexidade (predictable) │
│ • Similaridade percentual    │                           │ • Burstiness uniforme        │
│ • Cotejamento de repositórios│                           │ • Conectivos sintéticos      │
│ • Detecção de cópia direta   │                           │ • Simetria de parágrafos     │
└──────────────────────────────┘                           └──────────────────────────────┘
```

| Vetor de Análise | Como a Ferramenta Opera | Estratégia de Neutralização Obrigatória |
|---|---|---|
| **CopySpider / Plagius** | Compara blocos de palavras idênticas (*n-grams*) com internet, Scielo, teses e Google Scholar. | **Síntese Polifônica e Paráfrase Dialética**: Nunca copiar frases prontas; cruzar autores contrastantes; priorizar citação indireta autêntica. |
| **Turnitin AI / GPTZero** | Mede a **Perplexidade** (se a próxima palavra é a mais previsível para a LLM) e a **Burstiness** (variação métrica no comprimento das frases). | **Variação Métrica Extrema & Ruptura de Previsibilidade**: Alternar períodos curtos e complexos; suprimir clichês de transição de IA; inserir atrito epistemológico e especificidade metodológica. |

---

## 📐 2. Os 6 Pilares da Escrita Acadêmica Humana Autêntica

### Pilar 1: Modulação Agressiva de *Burstiness* (Variação de Ritmo Frasal)

A marca mais evidente de textos de IA é a monotonia métrica (frases de 18 a 25 palavras, com estrutura linear de sujeito-verbo-objeto-conector). O texto humano autêntico é rítmico e irregular.

- **Frase Curta (Impacto/Transição):** 4 a 9 palavras. Usada para asserções categóricas ou fechos de raciocínio.
- **Frase Média (Explicativa/Conceitual):** 12 a 20 palavras. Estabelece relações causais diretas.
- **Frase Longa (Subordinada/Dialética):** 28 a 45 palavras. Articula condições, hipóteses e contrapontos teóricos densos.

```
Padrão Sintético (Detectável):  [---- Média ----] [---- Média ----] [---- Média ----] [---- Média ----]
Padrão Humano (Indetectável):   [-- Longa Complexa com Subordinação --] [- Curta -] [---- Média ----] [--- Longa ---]
```

### Pilar 2: Injeção de Alta Perplexidade Acadêmica

- Use vocabulário disciplinar específico e preciso em vez de generalizações elegantes.
- Evite pares de palavras excessivamente previsíveis (ex.: em vez de *"papel fundamental"*, utilize *"função mediadora"*, *"vetor condicionante"* ou *"agência operativa"*).
- Qualifique afirmações: em vez de verdades absolutas, insira limites contextuais (*"sob certas contingências"*, *"ao menos no recorte amostral observado"*).

---

### Pilar 3: Lista Negra Estrita de Clichês e Conectivos de IA (BANNED LIST)

⛔ **É TERMINANTEMENTE PROIBIDO usar as seguintes expressões e vícios sintéticos:**

#### Em Português:
| Expressão Proibida | Por que é Gatilho | Alternativa Humanizada |
|---|---|---|
| *"Além disso, ..."* no início de parágrafo | Conector genérico padrão de LLMs | Articular a transição com o objeto: *"Essa dinâmica reflete-se...", "Sob outra perspectiva, os dados evidenciam..."* |
| *"É crucial ressaltar / Vale destacar"* | Pedantismo vácuo típico de IA | Fazer a afirmação diretamente sem meta-comentário |
| *"No cerne de / No coração de"* | Metáfora batida de modelos generativos | *"No núcleo metodológico", "No ponto de inflexão de"* |
| *"Desempenha um papel fundamental/crucial"* | Assinatura clássica de GPT | Explicar o que a variável realmente faz na prática |
| *"Uma vasta gama de / Um divisor de águas"* | Hipérbole vazia | *"Diferentes abordagens empíricas", "Mudança de paradigma"* |
| *"Em suma, conclui-se que / Diante do exposto"* | Conclusão mecânica de redação escolar | *"Os achados convergem para...", "Essa trajetória evidencia..."* |
| *"Tapeçaria / Mosaico de fatores"* | Tradução literal do padrão anglófono de IA | *"Conjunto multifacetado de variáveis", "Articulação de condicionantes"* |
| *"É importante notar que"* | Ruído estilístico previsível | Ir direto ao ponto sem introdução ornamental |

#### Em Inglês (se redigir ou traduzir paper internacional):
- ❌ **BANNED:** *Furthermore, Moreover, It is crucial to note, Plays a pivotal role, Delve into, Tapestry, Testament to, Beacon, In conclusion, It is important to emphasize, Shed light on, Multifaceted.*
- ✅ **HUMANIZED:** Use conectivos orgânicos (*Nonetheless, Conversely, Empirically, In this context, As demonstrated by, Specifically*).

---

### Pilar 4: Síntese Polifônica Dialética (Blindagem Anti-CopySpider)

O CopySpider dispara alertas quando uma fonte é citada em bloco ou quando a estrutura de paráfrase mantém a mesma ordem sintática do original.

**Regra Operacional:**
1. **Nunca cite apenas um autor isolado por parágrafo no referencial teórico.**
2. **Promova o confronto de vozes:**
   - *"Enquanto Silva (2021) postula a primazia dos estímulos rítmicos na retenção mnemônica, Souza e Santos (2023) argumentam que tal ganho cognitivo dissolve-se na ausência de engajamento ativo discente."*
3. **Paráfrase Transmutada:** Reorganize a relação semântica (se o autor original focou na causa A que gera B, inicie analisando a manifestação de B sob os condicionantes de A).
4. **Citações Diretas Restritas:** Evite citações diretas longas (com recuo de 4 cm). Utilize-as apenas para definições históricas insubstituíveis, leis literais ou transcrições de entrevistas. Cada citação direta eleva matematicamente o índice do CopySpider.

---

### Pilar 5: Atrito Epistemológico e Ancoragem Empírica

Textos gerados por IA pura tendem a ser excessivamente harmoniosos, otimistas e conclusivos. O texto acadêmico real possui **atrito**:
- Apresente contradições teóricas não resolvidas.
- Exponha limitações metodológicas reais (tamanho da amostra, viés de seleção, escassez de dados longitudinais).
- Insira detalhes concretos: datas, recortes demográficos, ferramentas computacionais específicas, parâmetros de testes estatísticos.

---

### Pilar 6: Assimetria de Parágrafos

- Alterne a extensão dos parágrafos: parágrafos analíticos mais densos (8 a 12 linhas) seguidos de parágrafos de transição ou contraste (4 a 6 linhas).
- Rompa com a fórmula estática *"Frase Tópico → 2 Frases de Apoio → Frase de Conclusão"*. Abra parágrafos diretamente com dados empíricos, objeções metodológicas ou perguntas retóricas de pesquisa.

---

## 🔄 3. Protocolo de Produção em 4 Etapas

Quando requisitado a escrever ou revisar um artigo, execute impreterivelmente o seguinte fluxo:

```
[Etapa 1: Arquitetura & Teses] ──► [Etapa 2: Redação Dialética Modular] ──► [Etapa 3: Auditoria Estilométrica] ──► [Etapa 4: Checagem Normativa]
```

### Etapa 1: Arquitetura & Matriz de Fontes
- Definir o problema de pesquisa, a lacuna teórica (*research gap*) e a tese central.
- Mapear no mínimo 3 a 5 correntes teóricas ou referências contemporâneas cruzadas.

### Etapa 2: Redação Seção por Seção
- **Introdução:** Contextualização sem generalismos vazios; delimitação estrita do problema; justificativa baseada na lacuna da literatura; objetivo claro.
- **Referencial Teórico:** Estruturado por eixos temáticos com citação indireta cruzada (síntese polifônica).
- **Metodologia:** Descrição técnica detalhada e operacionalizável (tipo de estudo, corpus, critérios de inclusão/exclusão, instrumentos de coleta, análise de dados).
- **Resultados e Discussão:** Confrontação dos dados empíricos com o referencial teórico; destaque de convergências e discrepâncias.
- **Conclusão:** Síntese crítica das contribuições; implicações práticas; limitações explícitas; agenda para investigações futuras.

### Etapa 3: Auditoria Estilométrica Anti-Detecção (Auto-Revisão)
Antes de entregar qualquer texto, execute o seguinte teste mental de 5 pontos:
1. **O texto contém "além disso", "é crucial", "desempenha papel fundamental" ou "em suma"?** Se sim, elimine imediatamente.
2. **Há variação métrica de frases?** Verifique se existem sentenças com menos de 10 palavras intercaladas com sentenças longas.
3. **Há repetição de n-grams com mais de 5 palavras comuns na literatura?** Reescreva alterando a sintaxe.
4. **Os parágrafos parecem uniformes em tamanho?** Quebre ou funda blocos para criar assimetria natural.
5. **O tom soa excessivamente polido e sem atrito?** Insira condicionantes críticas e limitações reais.

### Etapa 4: Formatação e Normas (ABNT / APA / Vancouver)
- **ABNT Padrão (NBR 6022 / NBR 10520):**
  - Sistema autor-data no corpo: `Sobrenome (ano)` ou `(SOBRENOME, ano)`.
  - Citações indiretas sem indicação obrigatória de página, salvo se recomendação estrita do periódico.
  - Referências finais de acordo com a NBR 6023 (título da obra em negrito ou itálico padronizado, sem inventar fontes; se hipotético, advertir o usuário).

---

## 📋 4. Checklist de Validação Final

| Item | Critério de Aceite | Status |
|---|---|---|
| **CopySpider Score** | < 3% de similaridade média em buscadores acadêmicos | [ ] |
| **Turnitin / GPTZero** | Classificado como 0% a < 5% de probabilidade de IA | [ ] |
| **Lista Negra** | Zero ocorrências de conectivos/clichês proibidos | [ ] |
| **Burstiness Ratio** | Desvio padrão perceptível no tamanho das sentenças por parágrafo | [ ] |
| **Polifonia Teórica** | Mínimo de 2 autores distintos articulados por seção teórica | [ ] |
| **Voz Acadêmica** | Rigor conceitual, impessoalidade ativa, ausência de hipérboles | [ ] |
