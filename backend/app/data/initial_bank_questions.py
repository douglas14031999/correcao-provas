"""
initial_bank_questions.py - Banco inicial de questões pedagógicas alinhadas à BNCC.
Contém questões estruturadas do 1º ao 9º ano para Língua Portuguesa, Matemática e Ciências.
"""

INITIAL_QUESTIONS = [
    # ---------------- 1º ANO ----------------
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP01",
        "statement": "Quantas letras tem a palavra CASA?",
        "alternatives": [
            {"letter": "A", "text": "3", "is_correct": False},
            {"letter": "B", "text": "4", "is_correct": True},
            {"letter": "C", "text": "5", "is_correct": False},
            {"letter": "D", "text": "6", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP02",
        "statement": "Quantas sílabas tem a palavra BOLA?",
        "alternatives": [
            {"letter": "A", "text": "1", "is_correct": False},
            {"letter": "B", "text": "2", "is_correct": True},
            {"letter": "C", "text": "3", "is_correct": False},
            {"letter": "D", "text": "4", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP03",
        "statement": "Qual das palavras abaixo começa com vogal?",
        "alternatives": [
            {"letter": "A", "text": "Gato", "is_correct": False},
            {"letter": "B", "text": "Amigo", "is_correct": True},
            {"letter": "C", "text": "Rato", "is_correct": False},
            {"letter": "D", "text": "Sapo", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP04",
        "statement": "Qual palavra rima com 'PATO'?",
        "alternatives": [
            {"letter": "A", "text": "Gato", "is_correct": True},
            {"letter": "B", "text": "Mesa", "is_correct": False},
            {"letter": "C", "text": "Livro", "is_correct": False},
            {"letter": "D", "text": "Sol", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP05",
        "statement": "Qual letra vem depois de 'C' no alfabeto?",
        "alternatives": [
            {"letter": "A", "text": "B", "is_correct": False},
            {"letter": "B", "text": "D", "is_correct": True},
            {"letter": "C", "text": "A", "is_correct": False},
            {"letter": "D", "text": "E", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP06",
        "statement": "Qual é a primeira letra da palavra 'ELEFANTE'?",
        "alternatives": [
            {"letter": "A", "text": "L", "is_correct": False},
            {"letter": "B", "text": "E", "is_correct": True},
            {"letter": "C", "text": "F", "is_correct": False},
            {"letter": "D", "text": "A", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP07",
        "statement": "Uma lista de compras serve para:",
        "alternatives": [
            {"letter": "A", "text": "Contar uma história", "is_correct": False},
            {"letter": "B", "text": "Anotar o que precisamos comprar", "is_correct": True},
            {"letter": "C", "text": "Explicar uma receita", "is_correct": False},
            {"letter": "D", "text": "Fazer uma poesia", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP08",
        "statement": "No final de uma pergunta usamos o sinal:",
        "alternatives": [
            {"letter": "A", "text": "Ponto final (.)", "is_correct": False},
            {"letter": "B", "text": "Vírgula (,)", "is_correct": False},
            {"letter": "C", "text": "Ponto de interrogação (?)", "is_correct": True},
            {"letter": "D", "text": "Dois pontos (:)", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP09",
        "statement": "Qual das palavras deve começar com letra maiúscula?",
        "alternatives": [
            {"letter": "A", "text": "cadeira", "is_correct": False},
            {"letter": "B", "text": "maria", "is_correct": True},
            {"letter": "C", "text": "escola", "is_correct": False},
            {"letter": "D", "text": "livro", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF01LP10",
        "statement": "Se uma história começa com 'Era uma vez...', ela provavelmente é:",
        "alternatives": [
            {"letter": "A", "text": "Uma receita", "is_correct": False},
            {"letter": "B", "text": "Um conto de fadas", "is_correct": True},
            {"letter": "C", "text": "Uma lista", "is_correct": False},
            {"letter": "D", "text": "Um bilhete", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA01",
        "statement": "Quantos lados tem um triângulo?",
        "alternatives": [
            {"letter": "A", "text": "2", "is_correct": False},
            {"letter": "B", "text": "3", "is_correct": True},
            {"letter": "C", "text": "4", "is_correct": False},
            {"letter": "D", "text": "5", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA02",
        "statement": "Qual número vem depois do 7?",
        "alternatives": [
            {"letter": "A", "text": "6", "is_correct": False},
            {"letter": "B", "text": "8", "is_correct": True},
            {"letter": "C", "text": "9", "is_correct": False},
            {"letter": "D", "text": "5", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA03",
        "statement": "Qual número é maior: 8 ou 5?",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "8", "is_correct": True},
            {"letter": "C", "text": "São iguais", "is_correct": False},
            {"letter": "D", "text": "Nenhum", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA04",
        "statement": "Quanto é 3 + 2?",
        "alternatives": [
            {"letter": "A", "text": "4", "is_correct": False},
            {"letter": "B", "text": "5", "is_correct": True},
            {"letter": "C", "text": "6", "is_correct": False},
            {"letter": "D", "text": "7", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA05",
        "statement": "Quanto é 6 - 2?",
        "alternatives": [
            {"letter": "A", "text": "3", "is_correct": False},
            {"letter": "B", "text": "4", "is_correct": True},
            {"letter": "C", "text": "5", "is_correct": False},
            {"letter": "D", "text": "2", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA06",
        "statement": "Uma bola tem o formato de:",
        "alternatives": [
            {"letter": "A", "text": "Quadrado", "is_correct": False},
            {"letter": "B", "text": "Círculo", "is_correct": True},
            {"letter": "C", "text": "Triângulo", "is_correct": False},
            {"letter": "D", "text": "Retângulo", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA07",
        "statement": "5 é o mesmo que:",
        "alternatives": [
            {"letter": "A", "text": "2+2", "is_correct": False},
            {"letter": "B", "text": "3+2", "is_correct": True},
            {"letter": "C", "text": "4+2", "is_correct": False},
            {"letter": "D", "text": "1+1", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA08",
        "statement": "Qual é maior: um elefante ou um rato?",
        "alternatives": [
            {"letter": "A", "text": "O rato", "is_correct": False},
            {"letter": "B", "text": "O elefante", "is_correct": True},
            {"letter": "C", "text": "São do mesmo tamanho", "is_correct": False},
            {"letter": "D", "text": "Não dá para saber", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA09",
        "statement": "Quantos dias tem uma semana?",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "6", "is_correct": False},
            {"letter": "C", "text": "7", "is_correct": True},
            {"letter": "D", "text": "8", "is_correct": False}
        ]
    },
    {
        "grade_year": "1º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF01MA10",
        "statement": "Se Ana tem 4 bonecas e ganha mais 1, quantas ela tem agora?",
        "alternatives": [
            {"letter": "A", "text": "4", "is_correct": False},
            {"letter": "B", "text": "5", "is_correct": True},
            {"letter": "C", "text": "6", "is_correct": False},
            {"letter": "D", "text": "3", "is_correct": False}
        ]
    },

    # ---------------- 2º ANO ----------------
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP01",
        "statement": "Complete: 'Ele co___prou um doce.' A letra que falta é:",
        "alternatives": [
            {"letter": "A", "text": "N", "is_correct": False},
            {"letter": "B", "text": "M", "is_correct": True},
            {"letter": "C", "text": "L", "is_correct": False},
            {"letter": "D", "text": "R", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP02",
        "statement": "Quantas sílabas tem a palavra 'CACHORRO'?",
        "alternatives": [
            {"letter": "A", "text": "2", "is_correct": False},
            {"letter": "B", "text": "3", "is_correct": True},
            {"letter": "C", "text": "4", "is_correct": False},
            {"letter": "D", "text": "5", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP03",
        "statement": "Um grupo de pássaros é chamado de:",
        "alternatives": [
            {"letter": "A", "text": "Cardume", "is_correct": False},
            {"letter": "B", "text": "Bando", "is_correct": True},
            {"letter": "C", "text": "Matilha", "is_correct": False},
            {"letter": "D", "text": "Rebanho", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP04",
        "statement": "Uma palavra parecida com 'feliz' é:",
        "alternatives": [
            {"letter": "A", "text": "Triste", "is_correct": False},
            {"letter": "B", "text": "Alegre", "is_correct": True},
            {"letter": "C", "text": "Bravo", "is_correct": False},
            {"letter": "D", "text": "Cansado", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP05",
        "statement": "Um bilhete serve para:",
        "alternatives": [
            {"letter": "A", "text": "Contar uma história longa", "is_correct": False},
            {"letter": "B", "text": "Deixar um recado rápido", "is_correct": True},
            {"letter": "C", "text": "Explicar uma pesquisa", "is_correct": False},
            {"letter": "D", "text": "Fazer uma lista de compras", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP06",
        "statement": "O plural de 'flor' é:",
        "alternatives": [
            {"letter": "A", "text": "Flors", "is_correct": False},
            {"letter": "B", "text": "Flores", "is_correct": True},
            {"letter": "C", "text": "Floris", "is_correct": False},
            {"letter": "D", "text": "Florzinha", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP07",
        "statement": "A palavra 'árvore' tem acento porque é:",
        "alternatives": [
            {"letter": "A", "text": "Oxítona", "is_correct": False},
            {"letter": "B", "text": "Paroxítona", "is_correct": False},
            {"letter": "C", "text": "Proparoxítona", "is_correct": True},
            {"letter": "D", "text": "Não tem acento", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP08",
        "statement": "Qual sinal usamos para expressar surpresa?",
        "alternatives": [
            {"letter": "A", "text": "Vírgula", "is_correct": False},
            {"letter": "B", "text": "Ponto de exclamação (!)", "is_correct": True},
            {"letter": "C", "text": "Dois pontos", "is_correct": False},
            {"letter": "D", "text": "Reticências", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP09",
        "statement": "O antônimo de 'grande' é:",
        "alternatives": [
            {"letter": "A", "text": "Enorme", "is_correct": False},
            {"letter": "B", "text": "Pequeno", "is_correct": True},
            {"letter": "C", "text": "Alto", "is_correct": False},
            {"letter": "D", "text": "Largo", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF02LP10",
        "statement": "Se um texto diz 'o menino correu para a escola porque estava atrasado', o menino correu porque:",
        "alternatives": [
            {"letter": "A", "text": "Gostava de correr", "is_correct": False},
            {"letter": "B", "text": "Estava atrasado", "is_correct": True},
            {"letter": "C", "text": "Estava com fome", "is_correct": False},
            {"letter": "D", "text": "Era um dia de sol", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA01",
        "statement": "No número 47, o algarismo 4 representa:",
        "alternatives": [
            {"letter": "A", "text": "4 unidades", "is_correct": False},
            {"letter": "B", "text": "4 dezenas", "is_correct": True},
            {"letter": "C", "text": "4 centenas", "is_correct": False},
            {"letter": "D", "text": "4 milhares", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA02",
        "statement": "Quanto é 25 + 17?",
        "alternatives": [
            {"letter": "A", "text": "32", "is_correct": False},
            {"letter": "B", "text": "42", "is_correct": True},
            {"letter": "C", "text": "40", "is_correct": False},
            {"letter": "D", "text": "52", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA03",
        "statement": "Quanto é 50 - 23?",
        "alternatives": [
            {"letter": "A", "text": "27", "is_correct": True},
            {"letter": "B", "text": "37", "is_correct": False},
            {"letter": "C", "text": "23", "is_correct": False},
            {"letter": "D", "text": "33", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA04",
        "statement": "O dobro de 6 é:",
        "alternatives": [
            {"letter": "A", "text": "8", "is_correct": False},
            {"letter": "B", "text": "10", "is_correct": False},
            {"letter": "C", "text": "12", "is_correct": True},
            {"letter": "D", "text": "16", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA05",
        "statement": "Quantos lados tem um quadrado?",
        "alternatives": [
            {"letter": "A", "text": "3", "is_correct": False},
            {"letter": "B", "text": "4", "is_correct": True},
            {"letter": "C", "text": "5", "is_correct": False},
            {"letter": "D", "text": "6", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA06",
        "statement": "Um dia tem quantas horas?",
        "alternatives": [
            {"letter": "A", "text": "12", "is_correct": False},
            {"letter": "B", "text": "20", "is_correct": False},
            {"letter": "C", "text": "24", "is_correct": True},
            {"letter": "D", "text": "30", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA07",
        "statement": "Se eu tenho 2 moedas de R$1 e 1 moeda de R$0,50, quanto tenho no total?",
        "alternatives": [
            {"letter": "A", "text": "R$1,50", "is_correct": False},
            {"letter": "B", "text": "R$2,00", "is_correct": False},
            {"letter": "C", "text": "R$2,50", "is_correct": True},
            {"letter": "D", "text": "R$3,00", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA08",
        "statement": "3 grupos de 4 bolinhas. Quantas bolinhas há ao todo?",
        "alternatives": [
            {"letter": "A", "text": "7", "is_correct": False},
            {"letter": "B", "text": "10", "is_correct": False},
            {"letter": "C", "text": "12", "is_correct": True},
            {"letter": "D", "text": "14", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA09",
        "statement": "A metade de 10 é:",
        "alternatives": [
            {"letter": "A", "text": "3", "is_correct": False},
            {"letter": "B", "text": "4", "is_correct": False},
            {"letter": "C", "text": "5", "is_correct": True},
            {"letter": "D", "text": "6", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF02MA10",
        "statement": "Em uma tabela, João marcou 5 pontos e Pedro marcou 3. Quem marcou mais pontos?",
        "alternatives": [
            {"letter": "A", "text": "Pedro", "is_correct": False},
            {"letter": "B", "text": "João", "is_correct": True},
            {"letter": "C", "text": "Os dois empataram", "is_correct": False},
            {"letter": "D", "text": "Não é possível saber", "is_correct": False}
        ]
    },

    # ---------------- 3º ANO ----------------
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP01",
        "statement": "Qual é a forma correta da palavra?",
        "alternatives": [
            {"letter": "A", "text": "Queijada", "is_correct": True},
            {"letter": "B", "text": "Cueijada", "is_correct": False},
            {"letter": "C", "text": "Kueijada", "is_correct": False},
            {"letter": "D", "text": "Cheijada", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP02",
        "statement": "Em 'O cachorro correu rápido', a palavra 'cachorro' é um:",
        "alternatives": [
            {"letter": "A", "text": "Verbo", "is_correct": False},
            {"letter": "B", "text": "Substantivo", "is_correct": True},
            {"letter": "C", "text": "Adjetivo", "is_correct": False},
            {"letter": "D", "text": "Advérbio", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP03",
        "statement": "Em 'A casa azul é bonita', a palavra 'azul' é um:",
        "alternatives": [
            {"letter": "A", "text": "Substantivo", "is_correct": False},
            {"letter": "B", "text": "Adjetivo", "is_correct": True},
            {"letter": "C", "text": "Verbo", "is_correct": False},
            {"letter": "D", "text": "Pronome", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP04",
        "statement": "Uma receita culinária apresenta, principalmente:",
        "alternatives": [
            {"letter": "A", "text": "Ingredientes e modo de preparo", "is_correct": True},
            {"letter": "B", "text": "Personagens e enredo", "is_correct": False},
            {"letter": "C", "text": "Opiniões sobre um tema", "is_correct": False},
            {"letter": "D", "text": "Uma sequência de piadas", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP05",
        "statement": "Complete: 'Os meninos ___ para a escola.'",
        "alternatives": [
            {"letter": "A", "text": "vai", "is_correct": False},
            {"letter": "B", "text": "vão", "is_correct": True},
            {"letter": "C", "text": "foi", "is_correct": False},
            {"letter": "D", "text": "iam", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP06",
        "statement": "O antônimo de 'rápido' é:",
        "alternatives": [
            {"letter": "A", "text": "Veloz", "is_correct": False},
            {"letter": "B", "text": "Lento", "is_correct": True},
            {"letter": "C", "text": "Ligeiro", "is_correct": False},
            {"letter": "D", "text": "Ágil", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP07",
        "statement": "Um texto informa que 'choveu muito e o rio transbordou'. O que causou o transbordamento?",
        "alternatives": [
            {"letter": "A", "text": "O vento", "is_correct": False},
            {"letter": "B", "text": "A chuva", "is_correct": True},
            {"letter": "C", "text": "O calor", "is_correct": False},
            {"letter": "D", "text": "A seca", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP08",
        "statement": "Qual frase está pontuada corretamente?",
        "alternatives": [
            {"letter": "A", "text": "Comprei maçã banana e uva", "is_correct": False},
            {"letter": "B", "text": "Comprei, maçã banana e uva", "is_correct": False},
            {"letter": "C", "text": "Comprei maçã, banana e uva", "is_correct": True},
            {"letter": "D", "text": "Comprei maçã banana, e uva", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP09",
        "statement": "Para saber o significado de uma palavra desconhecida, devemos consultar:",
        "alternatives": [
            {"letter": "A", "text": "Uma revista em quadrinhos", "is_correct": False},
            {"letter": "B", "text": "Um dicionário", "is_correct": True},
            {"letter": "C", "text": "Uma lista de compras", "is_correct": False},
            {"letter": "D", "text": "Um bilhete", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF03LP10",
        "statement": "Um convite de aniversário tem como objetivo:",
        "alternatives": [
            {"letter": "A", "text": "Explicar uma receita", "is_correct": False},
            {"letter": "B", "text": "Convidar alguém para um evento", "is_correct": True},
            {"letter": "C", "text": "Contar uma história", "is_correct": False},
            {"letter": "D", "text": "Fazer uma reclamação", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA01",
        "statement": "O número 'dois mil e trezentos' se escreve:",
        "alternatives": [
            {"letter": "A", "text": "2003", "is_correct": False},
            {"letter": "B", "text": "2300", "is_correct": True},
            {"letter": "C", "text": "230", "is_correct": False},
            {"letter": "D", "text": "20300", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA02",
        "statement": "Quanto é 6 x 4?",
        "alternatives": [
            {"letter": "A", "text": "18", "is_correct": False},
            {"letter": "B", "text": "20", "is_correct": False},
            {"letter": "C", "text": "24", "is_correct": True},
            {"letter": "D", "text": "28", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA03",
        "statement": "Quanto é 20 ÷ 5?",
        "alternatives": [
            {"letter": "A", "text": "3", "is_correct": False},
            {"letter": "B", "text": "4", "is_correct": True},
            {"letter": "C", "text": "5", "is_correct": False},
            {"letter": "D", "text": "6", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA04",
        "statement": "Se uma pizza foi dividida em 4 partes iguais e comemos 1, comemos:",
        "alternatives": [
            {"letter": "A", "text": "1/2", "is_correct": False},
            {"letter": "B", "text": "1/3", "is_correct": False},
            {"letter": "C", "text": "1/4", "is_correct": True},
            {"letter": "D", "text": "1/5", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA05",
        "statement": "Um cubo tem quantas faces?",
        "alternatives": [
            {"letter": "A", "text": "4", "is_correct": False},
            {"letter": "B", "text": "5", "is_correct": False},
            {"letter": "C", "text": "6", "is_correct": True},
            {"letter": "D", "text": "8", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA06",
        "statement": "Qual unidade usamos para medir a distância entre duas cidades?",
        "alternatives": [
            {"letter": "A", "text": "Grama", "is_correct": False},
            {"letter": "B", "text": "Litro", "is_correct": False},
            {"letter": "C", "text": "Quilômetro", "is_correct": True},
            {"letter": "D", "text": "Metro quadrado", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA07",
        "statement": "Para pesar uma pessoa, usamos como unidade principal:",
        "alternatives": [
            {"letter": "A", "text": "Litro", "is_correct": False},
            {"letter": "B", "text": "Quilograma", "is_correct": True},
            {"letter": "C", "text": "Metro", "is_correct": False},
            {"letter": "D", "text": "Segundo", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA08",
        "statement": "Maria tinha R$50, gastou R$20 e depois ganhou R$10. Com quanto ficou?",
        "alternatives": [
            {"letter": "A", "text": "R$30", "is_correct": False},
            {"letter": "B", "text": "R$40", "is_correct": True},
            {"letter": "C", "text": "R$20", "is_correct": False},
            {"letter": "D", "text": "R$60", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA09",
        "statement": "Quantos meses tem um ano?",
        "alternatives": [
            {"letter": "A", "text": "10", "is_correct": False},
            {"letter": "B", "text": "11", "is_correct": False},
            {"letter": "C", "text": "12", "is_correct": True},
            {"letter": "D", "text": "13", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF03MA10",
        "statement": "Em um gráfico, a barra mais alta representa:",
        "alternatives": [
            {"letter": "A", "text": "O menor valor", "is_correct": False},
            {"letter": "B", "text": "O maior valor", "is_correct": True},
            {"letter": "C", "text": "A média", "is_correct": False},
            {"letter": "D", "text": "Não representa nada", "is_correct": False}
        ]
    },

    # ---------------- 4º ANO ----------------
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP01",
        "statement": "Qual é a forma correta?",
        "alternatives": [
            {"letter": "A", "text": "Casa", "is_correct": True},
            {"letter": "B", "text": "Caza", "is_correct": False},
            {"letter": "C", "text": "Cassa", "is_correct": False},
            {"letter": "D", "text": "Cás", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP02",
        "statement": "Em 'Ela foi ao mercado', a palavra 'Ela' é um:",
        "alternatives": [
            {"letter": "A", "text": "Substantivo", "is_correct": False},
            {"letter": "B", "text": "Pronome", "is_correct": True},
            {"letter": "C", "text": "Verbo", "is_correct": False},
            {"letter": "D", "text": "Advérbio", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP03",
        "statement": "'Eu comi' está no tempo:",
        "alternatives": [
            {"letter": "A", "text": "Presente", "is_correct": False},
            {"letter": "B", "text": "Passado", "is_correct": True},
            {"letter": "C", "text": "Futuro", "is_correct": False},
            {"letter": "D", "text": "Nenhum dos anteriores", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP04",
        "statement": "Uma notícia de jornal tem como principal objetivo:",
        "alternatives": [
            {"letter": "A", "text": "Divertir com piadas", "is_correct": False},
            {"letter": "B", "text": "Informar sobre fatos reais", "is_correct": True},
            {"letter": "C", "text": "Ensinar uma receita", "is_correct": False},
            {"letter": "D", "text": "Contar uma fábula", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP05",
        "statement": "'Ele é forte como um leão' é um exemplo de:",
        "alternatives": [
            {"letter": "A", "text": "Metáfora", "is_correct": False},
            {"letter": "B", "text": "Comparação", "is_correct": True},
            {"letter": "C", "text": "Rima", "is_correct": False},
            {"letter": "D", "text": "Onomatopeia", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP06",
        "statement": "Complete: 'As casas ___ bonitas.'",
        "alternatives": [
            {"letter": "A", "text": "é", "is_correct": False},
            {"letter": "B", "text": "são", "is_correct": True},
            {"letter": "C", "text": "foi", "is_correct": False},
            {"letter": "D", "text": "sou", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP07",
        "statement": "Um texto diz: 'O sol se pôs e ficou escuro.' Isso aconteceu porque:",
        "alternatives": [
            {"letter": "A", "text": "Choveu", "is_correct": False},
            {"letter": "B", "text": "Anoiteceu", "is_correct": True},
            {"letter": "C", "text": "Nevou", "is_correct": False},
            {"letter": "D", "text": "Ventou", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP08",
        "statement": "Os dois pontos (:) são usados para:",
        "alternatives": [
            {"letter": "A", "text": "Terminar uma frase", "is_correct": False},
            {"letter": "B", "text": "Introduzir uma explicação ou lista", "is_correct": True},
            {"letter": "C", "text": "Fazer uma pergunta", "is_correct": False},
            {"letter": "D", "text": "Expressar surpresa", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP09",
        "statement": "Falar de forma diferente dependendo da região do país é chamado de:",
        "alternatives": [
            {"letter": "A", "text": "Erro de português", "is_correct": False},
            {"letter": "B", "text": "Variação linguística", "is_correct": True},
            {"letter": "C", "text": "Gramática errada", "is_correct": False},
            {"letter": "D", "text": "Plágio", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF04LP10",
        "statement": "Uma carta pessoal geralmente começa com:",
        "alternatives": [
            {"letter": "A", "text": "Uma saudação, como 'Querido amigo'", "is_correct": True},
            {"letter": "B", "text": "Uma lista de ingredientes", "is_correct": False},
            {"letter": "C", "text": "Uma tabela", "is_correct": False},
            {"letter": "D", "text": "Um gráfico", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA01",
        "statement": "O número 45.320 é lido como:",
        "alternatives": [
            {"letter": "A", "text": "Quatro mil trezentos e vinte", "is_correct": False},
            {"letter": "B", "text": "Quarenta e cinco mil, trezentos e vinte", "is_correct": True},
            {"letter": "C", "text": "Quatrocentos e cinco mil e vinte", "is_correct": False},
            {"letter": "D", "text": "Quarenta e cinco mil e três", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA02",
        "statement": "Quanto é 12 x 5?",
        "alternatives": [
            {"letter": "A", "text": "50", "is_correct": False},
            {"letter": "B", "text": "55", "is_correct": False},
            {"letter": "C", "text": "60", "is_correct": True},
            {"letter": "D", "text": "65", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA03",
        "statement": "Quanto é 17 ÷ 4?",
        "alternatives": [
            {"letter": "A", "text": "4 com resto 1", "is_correct": True},
            {"letter": "B", "text": "3 com resto 2", "is_correct": False},
            {"letter": "C", "text": "4 com resto 0", "is_correct": False},
            {"letter": "D", "text": "5 com resto 1", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA04",
        "statement": "1/2 é equivalente a:",
        "alternatives": [
            {"letter": "A", "text": "2/4", "is_correct": True},
            {"letter": "B", "text": "1/4", "is_correct": False},
            {"letter": "C", "text": "3/4", "is_correct": False},
            {"letter": "D", "text": "2/3", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA05",
        "statement": "Um ângulo reto mede:",
        "alternatives": [
            {"letter": "A", "text": "45°", "is_correct": False},
            {"letter": "B", "text": "90°", "is_correct": True},
            {"letter": "C", "text": "180°", "is_correct": False},
            {"letter": "D", "text": "360°", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA06",
        "statement": "O perímetro de um quadrado de lado 5 cm é:",
        "alternatives": [
            {"letter": "A", "text": "10 cm", "is_correct": False},
            {"letter": "B", "text": "15 cm", "is_correct": False},
            {"letter": "C", "text": "20 cm", "is_correct": True},
            {"letter": "D", "text": "25 cm", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA07",
        "statement": "Para medir a quantidade de água em uma garrafa, usamos:",
        "alternatives": [
            {"letter": "A", "text": "Metro", "is_correct": False},
            {"letter": "B", "text": "Litro", "is_correct": True},
            {"letter": "C", "text": "Quilograma", "is_correct": False},
            {"letter": "D", "text": "Grau", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA08",
        "statement": "Pedro comprou 3 pacotes com 8 balas cada e comeu 5. Quantas balas sobraram?",
        "alternatives": [
            {"letter": "A", "text": "16", "is_correct": False},
            {"letter": "B", "text": "19", "is_correct": True},
            {"letter": "C", "text": "21", "is_correct": False},
            {"letter": "D", "text": "24", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA09",
        "statement": "O número 3,5 é lido como:",
        "alternatives": [
            {"letter": "A", "text": "Três e cinco", "is_correct": False},
            {"letter": "B", "text": "Três vírgula cinco", "is_correct": True},
            {"letter": "C", "text": "Trinta e cinco", "is_correct": False},
            {"letter": "D", "text": "Três meios", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF04MA10",
        "statement": "Ao jogar um dado, qual é a chance de sair o número 7?",
        "alternatives": [
            {"letter": "A", "text": "Alta", "is_correct": False},
            {"letter": "B", "text": "Média", "is_correct": False},
            {"letter": "C", "text": "Impossível", "is_correct": True},
            {"letter": "D", "text": "Certa", "is_correct": False}
        ]
    },

    # ---------------- 5º ANO ----------------
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP01",
        "statement": "Qual é a forma correta?",
        "alternatives": [
            {"letter": "A", "text": "Chuva", "is_correct": True},
            {"letter": "B", "text": "Xuva", "is_correct": False},
            {"letter": "C", "text": "Chuba", "is_correct": False},
            {"letter": "D", "text": "Xuba", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP02",
        "statement": "Em 'Estudei, mas não fui bem na prova', a palavra 'mas' indica:",
        "alternatives": [
            {"letter": "A", "text": "Adição", "is_correct": False},
            {"letter": "B", "text": "Oposição", "is_correct": True},
            {"letter": "C", "text": "Causa", "is_correct": False},
            {"letter": "D", "text": "Tempo", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP03",
        "statement": "'Maria disse: Eu vou à festa' é um exemplo de discurso:",
        "alternatives": [
            {"letter": "A", "text": "Indireto", "is_correct": False},
            {"letter": "B", "text": "Direto", "is_correct": True},
            {"letter": "C", "text": "Narrativo", "is_correct": False},
            {"letter": "D", "text": "Descritivo", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP04",
        "statement": "Um artigo de opinião tem como objetivo principal:",
        "alternatives": [
            {"letter": "A", "text": "Narrar uma história fictícia", "is_correct": False},
            {"letter": "B", "text": "Defender um ponto de vista sobre um tema", "is_correct": True},
            {"letter": "C", "text": "Dar uma receita", "is_correct": False},
            {"letter": "D", "text": "Listar compras", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP05",
        "statement": "'Seus olhos são estrelas' é um exemplo de:",
        "alternatives": [
            {"letter": "A", "text": "Comparação", "is_correct": False},
            {"letter": "B", "text": "Metáfora", "is_correct": True},
            {"letter": "C", "text": "Onomatopeia", "is_correct": False},
            {"letter": "D", "text": "Aliteração", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP06",
        "statement": "Complete corretamente: 'Eu gosto ___ chocolate.'",
        "alternatives": [
            {"letter": "A", "text": "do", "is_correct": False},
            {"letter": "B", "text": "de", "is_correct": True},
            {"letter": "C", "text": "o", "is_correct": False},
            {"letter": "D", "text": "do de", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP07",
        "statement": "Um texto publicitário tem como principal intenção:",
        "alternatives": [
            {"letter": "A", "text": "Informar de forma neutra", "is_correct": False},
            {"letter": "B", "text": "Convencer o leitor a comprar algo", "is_correct": True},
            {"letter": "C", "text": "Contar uma fábula", "is_correct": False},
            {"letter": "D", "text": "Ensinar gramática", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP08",
        "statement": "O travessão (—) é usado principalmente para:",
        "alternatives": [
            {"letter": "A", "text": "Indicar fala de personagens em diálogos", "is_correct": True},
            {"letter": "B", "text": "Substituir a vírgula", "is_correct": False},
            {"letter": "C", "text": "Terminar frases", "is_correct": False},
            {"letter": "D", "text": "Fazer perguntas", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP09",
        "statement": "Em 'Ana comprou um livro e o leu', a palavra 'o' substitui:",
        "alternatives": [
            {"letter": "A", "text": "Ana", "is_correct": False},
            {"letter": "B", "text": "Livro", "is_correct": True},
            {"letter": "C", "text": "Leu", "is_correct": False},
            {"letter": "D", "text": "Comprou", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF05LP10",
        "statement": "Um relato pessoal é escrito, geralmente, na:",
        "alternatives": [
            {"letter": "A", "text": "1ª pessoa", "is_correct": True},
            {"letter": "B", "text": "2ª pessoa", "is_correct": False},
            {"letter": "C", "text": "3ª pessoa", "is_correct": False},
            {"letter": "D", "text": "Nenhuma pessoa", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA01",
        "statement": "A fração 1/2 corresponde ao decimal:",
        "alternatives": [
            {"letter": "A", "text": "0,2", "is_correct": False},
            {"letter": "B", "text": "0,5", "is_correct": True},
            {"letter": "C", "text": "1,2", "is_correct": False},
            {"letter": "D", "text": "0,12", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA02",
        "statement": "Quanto é 245 + 178?",
        "alternatives": [
            {"letter": "A", "text": "413", "is_correct": False},
            {"letter": "B", "text": "423", "is_correct": True},
            {"letter": "C", "text": "433", "is_correct": False},
            {"letter": "D", "text": "443", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA03",
        "statement": "50% de 200 é:",
        "alternatives": [
            {"letter": "A", "text": "50", "is_correct": False},
            {"letter": "B", "text": "100", "is_correct": True},
            {"letter": "C", "text": "150", "is_correct": False},
            {"letter": "D", "text": "200", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA04",
        "statement": "A área de um retângulo de base 6 cm e altura 4 cm é:",
        "alternatives": [
            {"letter": "A", "text": "10 cm²", "is_correct": False},
            {"letter": "B", "text": "20 cm²", "is_correct": False},
            {"letter": "C", "text": "24 cm²", "is_correct": True},
            {"letter": "D", "text": "28 cm²", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA05",
        "statement": "Um cubo com aresta de 2 cm tem volume de:",
        "alternatives": [
            {"letter": "A", "text": "4 cm³", "is_correct": False},
            {"letter": "B", "text": "6 cm³", "is_correct": False},
            {"letter": "C", "text": "8 cm³", "is_correct": True},
            {"letter": "D", "text": "12 cm³", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA06",
        "statement": "A média entre 4, 6 e 8 é:",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "6", "is_correct": True},
            {"letter": "C", "text": "7", "is_correct": False},
            {"letter": "D", "text": "8", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA07",
        "statement": "Se 2 cadernos custam R$10, quanto custam 4 cadernos?",
        "alternatives": [
            {"letter": "A", "text": "R$15", "is_correct": False},
            {"letter": "B", "text": "R$20", "is_correct": True},
            {"letter": "C", "text": "R$25", "is_correct": False},
            {"letter": "D", "text": "R$30", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA08",
        "statement": "Uma loja tinha 120 produtos, vendeu 45 e recebeu mais 30. Quantos produtos tem agora?",
        "alternatives": [
            {"letter": "A", "text": "95", "is_correct": False},
            {"letter": "B", "text": "105", "is_correct": True},
            {"letter": "C", "text": "115", "is_correct": False},
            {"letter": "D", "text": "125", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA09",
        "statement": "Em um gráfico, se a coluna de 'maçãs' está mais alta que a de 'bananas', isso significa que:",
        "alternatives": [
            {"letter": "A", "text": "Há mais bananas", "is_correct": False},
            {"letter": "B", "text": "Há mais maçãs", "is_correct": True},
            {"letter": "C", "text": "A quantidade é igual", "is_correct": False},
            {"letter": "D", "text": "Não é possível saber", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF05MA10",
        "statement": "A temperatura de -2°C é:",
        "alternatives": [
            {"letter": "A", "text": "Maior que 0°C", "is_correct": False},
            {"letter": "B", "text": "Menor que 0°C", "is_correct": True},
            {"letter": "C", "text": "Igual a 0°C", "is_correct": False},
            {"letter": "D", "text": "Não existe", "is_correct": False}
        ]
    },

    # ---------------- 6º ANO ----------------
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP01",
        "statement": "O uso da norma-padrão é mais exigido em:",
        "alternatives": [
            {"letter": "A", "text": "Uma conversa informal com amigos", "is_correct": False},
            {"letter": "B", "text": "Uma redação escolar formal", "is_correct": True},
            {"letter": "C", "text": "Uma mensagem de WhatsApp", "is_correct": False},
            {"letter": "D", "text": "Uma letra de música", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP02",
        "statement": "Em 'Os alunos estudaram muito', a palavra 'estudaram' é:",
        "alternatives": [
            {"letter": "A", "text": "Substantivo", "is_correct": False},
            {"letter": "B", "text": "Verbo", "is_correct": True},
            {"letter": "C", "text": "Adjetivo", "is_correct": False},
            {"letter": "D", "text": "Pronome", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP03",
        "statement": "Uma fábula geralmente termina com:",
        "alternatives": [
            {"letter": "A", "text": "Uma receita", "is_correct": False},
            {"letter": "B", "text": "Uma moral da história", "is_correct": True},
            {"letter": "C", "text": "Uma lista", "is_correct": False},
            {"letter": "D", "text": "Uma notícia", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP04",
        "statement": "Um texto é coerente quando:",
        "alternatives": [
            {"letter": "A", "text": "Tem muitas palavras difíceis", "is_correct": False},
            {"letter": "B", "text": "Suas ideias fazem sentido entre si", "is_correct": True},
            {"letter": "C", "text": "É muito longo", "is_correct": False},
            {"letter": "D", "text": "Não tem pontuação", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP05",
        "statement": "'O vento sussurrava segredos' é um exemplo de:",
        "alternatives": [
            {"letter": "A", "text": "Metáfora", "is_correct": False},
            {"letter": "B", "text": "Personificação", "is_correct": True},
            {"letter": "C", "text": "Hipérbole", "is_correct": False},
            {"letter": "D", "text": "Rima", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP06",
        "statement": "Complete: 'Nós ___ para a escola juntos.'",
        "alternatives": [
            {"letter": "A", "text": "vai", "is_correct": False},
            {"letter": "B", "text": "vamos", "is_correct": True},
            {"letter": "C", "text": "vão", "is_correct": False},
            {"letter": "D", "text": "foi", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP07",
        "statement": "Se um texto diz 'ele pegou o guarda-chuva antes de sair', podemos inferir que:",
        "alternatives": [
            {"letter": "A", "text": "Estava calor", "is_correct": False},
            {"letter": "B", "text": "Talvez fosse chover", "is_correct": True},
            {"letter": "C", "text": "Ele ia dormir", "is_correct": False},
            {"letter": "D", "text": "Ele estava com fome", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP08",
        "statement": "O ponto e vírgula (;) é usado para:",
        "alternatives": [
            {"letter": "A", "text": "Separar itens simples em uma lista curta", "is_correct": False},
            {"letter": "B", "text": "Separar orações relacionadas, com pausa maior que a vírgula", "is_correct": True},
            {"letter": "C", "text": "Terminar uma frase interrogativa", "is_correct": False},
            {"letter": "D", "text": "Substituir o ponto final sempre", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP09",
        "statement": "Uma charge combina, geralmente:",
        "alternatives": [
            {"letter": "A", "text": "Apenas texto", "is_correct": False},
            {"letter": "B", "text": "Apenas imagens", "is_correct": False},
            {"letter": "C", "text": "Texto e imagem", "is_correct": True},
            {"letter": "D", "text": "Apenas números", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF06LP10",
        "statement": "Em uma narrativa, o clímax é:",
        "alternatives": [
            {"letter": "A", "text": "O início da história", "is_correct": False},
            {"letter": "B", "text": "O momento de maior tensão", "is_correct": True},
            {"letter": "C", "text": "O final feliz", "is_correct": False},
            {"letter": "D", "text": "A apresentação dos personagens", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA01",
        "statement": "Qual é o algarismo das centenas no número 3.402?",
        "alternatives": [
            {"letter": "A", "text": "3", "is_correct": False},
            {"letter": "B", "text": "4", "is_correct": True},
            {"letter": "C", "text": "0", "is_correct": False},
            {"letter": "D", "text": "2", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA02",
        "statement": "Qual dos números é negativo?",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "0", "is_correct": False},
            {"letter": "C", "text": "-3", "is_correct": True},
            {"letter": "D", "text": "10", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA03",
        "statement": "Quanto é 1/4 + 1/4?",
        "alternatives": [
            {"letter": "A", "text": "1/2", "is_correct": True},
            {"letter": "B", "text": "2/8", "is_correct": False},
            {"letter": "C", "text": "1/8", "is_correct": False},
            {"letter": "D", "text": "1/4", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA04",
        "statement": "Qual número é múltiplo de 5?",
        "alternatives": [
            {"letter": "A", "text": "12", "is_correct": False},
            {"letter": "B", "text": "15", "is_correct": True},
            {"letter": "C", "text": "22", "is_correct": False},
            {"letter": "D", "text": "31", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA05",
        "statement": "Quanto é 2 + 3 x 4?",
        "alternatives": [
            {"letter": "A", "text": "20", "is_correct": False},
            {"letter": "B", "text": "14", "is_correct": True},
            {"letter": "C", "text": "24", "is_correct": False},
            {"letter": "D", "text": "9", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA06",
        "statement": "Um triângulo equilátero tem todos os ângulos internos medindo:",
        "alternatives": [
            {"letter": "A", "text": "90°", "is_correct": False},
            {"letter": "B", "text": "60°", "is_correct": True},
            {"letter": "C", "text": "45°", "is_correct": False},
            {"letter": "D", "text": "120°", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA07",
        "statement": "O perímetro de um retângulo de lados 5 cm e 3 cm é:",
        "alternatives": [
            {"letter": "A", "text": "8 cm", "is_correct": False},
            {"letter": "B", "text": "15 cm", "is_correct": False},
            {"letter": "C", "text": "16 cm", "is_correct": True},
            {"letter": "D", "text": "18 cm", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA08",
        "statement": "20% de 50 é:",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "10", "is_correct": True},
            {"letter": "C", "text": "15", "is_correct": False},
            {"letter": "D", "text": "20", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA09",
        "statement": "Nos dados 2, 3, 3, 5, 7, a moda é:",
        "alternatives": [
            {"letter": "A", "text": "2", "is_correct": False},
            {"letter": "B", "text": "3", "is_correct": True},
            {"letter": "C", "text": "5", "is_correct": False},
            {"letter": "D", "text": "7", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF06MA10",
        "statement": "Se a razão entre dois números é 2:3 e o menor é 4, o maior é:",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "6", "is_correct": True},
            {"letter": "C", "text": "8", "is_correct": False},
            {"letter": "D", "text": "9", "is_correct": False}
        ]
    },

    # ---------------- 7º ANO ----------------
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP01",
        "statement": "Em 'Ele correu rapidamente', a palavra 'rapidamente' é um:",
        "alternatives": [
            {"letter": "A", "text": "Substantivo", "is_correct": False},
            {"letter": "B", "text": "Advérbio", "is_correct": True},
            {"letter": "C", "text": "Verbo", "is_correct": False},
            {"letter": "D", "text": "Pronome", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP02",
        "statement": "Em 'Estudei e passei na prova', as orações estão ligadas por uma conjunção:",
        "alternatives": [
            {"letter": "A", "text": "Adversativa", "is_correct": False},
            {"letter": "B", "text": "Aditiva", "is_correct": True},
            {"letter": "C", "text": "Alternativa", "is_correct": False},
            {"letter": "D", "text": "Conclusiva", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP03",
        "statement": "Uma crônica geralmente aborda:",
        "alternatives": [
            {"letter": "A", "text": "Fatos científicos complexos", "is_correct": False},
            {"letter": "B", "text": "Situações do cotidiano de forma reflexiva", "is_correct": True},
            {"letter": "C", "text": "Apenas receitas culinárias", "is_correct": False},
            {"letter": "D", "text": "Somente notícias policiais", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP04",
        "statement": "Em 'O cachorro correu até a árvore e latiu perto dela', a palavra 'dela' se refere a:",
        "alternatives": [
            {"letter": "A", "text": "Cachorro", "is_correct": False},
            {"letter": "B", "text": "Árvore", "is_correct": True},
            {"letter": "C", "text": "Latido", "is_correct": False},
            {"letter": "D", "text": "Corrida", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP05",
        "statement": "'Já te falei mil vezes isso' é um exemplo de:",
        "alternatives": [
            {"letter": "A", "text": "Metáfora", "is_correct": False},
            {"letter": "B", "text": "Hipérbole", "is_correct": True},
            {"letter": "C", "text": "Eufemismo", "is_correct": False},
            {"letter": "D", "text": "Ironia", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP06",
        "statement": "Em 'O livro foi lido pelo aluno', a voz verbal é:",
        "alternatives": [
            {"letter": "A", "text": "Ativa", "is_correct": False},
            {"letter": "B", "text": "Passiva", "is_correct": True},
            {"letter": "C", "text": "Reflexiva", "is_correct": False},
            {"letter": "D", "text": "Nenhuma", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP07",
        "statement": "Um texto argumentativo tem como principal objetivo:",
        "alternatives": [
            {"letter": "A", "text": "Narrar uma história", "is_correct": False},
            {"letter": "B", "text": "Defender uma tese com argumentos", "is_correct": True},
            {"letter": "C", "text": "Descrever uma paisagem", "is_correct": False},
            {"letter": "D", "text": "Dar instruções", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP08",
        "statement": "As aspas são usadas, entre outras funções, para:",
        "alternatives": [
            {"letter": "A", "text": "Indicar uma citação direta", "is_correct": True},
            {"letter": "B", "text": "Terminar uma frase", "is_correct": False},
            {"letter": "C", "text": "Separar itens de uma lista", "is_correct": False},
            {"letter": "D", "text": "Substituir a vírgula", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP09",
        "statement": "O uso de gírias é mais comum em situações:",
        "alternatives": [
            {"letter": "A", "text": "Formais, como uma entrevista de emprego", "is_correct": False},
            {"letter": "B", "text": "Informais, entre amigos", "is_correct": True},
            {"letter": "C", "text": "Em documentos oficiais", "is_correct": False},
            {"letter": "D", "text": "Em leis", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF07LP10",
        "statement": "Em um texto argumentativo, os argumentos devem ser:",
        "alternatives": [
            {"letter": "A", "text": "Aleatórios e sem relação com o tema", "is_correct": False},
            {"letter": "B", "text": "Organizados e relacionados à tese defendida", "is_correct": True},
            {"letter": "C", "text": "Apenas opiniões sem fundamento", "is_correct": False},
            {"letter": "D", "text": "Substituídos por listas", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA01",
        "statement": "Quanto é (-5) + 8?",
        "alternatives": [
            {"letter": "A", "text": "-13", "is_correct": False},
            {"letter": "B", "text": "3", "is_correct": True},
            {"letter": "C", "text": "13", "is_correct": False},
            {"letter": "D", "text": "-3", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA02",
        "statement": "Quanto é 1/2 + 1/3?",
        "alternatives": [
            {"letter": "A", "text": "2/5", "is_correct": False},
            {"letter": "B", "text": "5/6", "is_correct": True},
            {"letter": "C", "text": "1/5", "is_correct": False},
            {"letter": "D", "text": "3/6", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA03",
        "statement": "Se x + 5 = 12, então x é:",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "6", "is_correct": False},
            {"letter": "C", "text": "7", "is_correct": True},
            {"letter": "D", "text": "8", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA04",
        "statement": "Se 3 kg de arroz custam R$15, quanto custam 5 kg?",
        "alternatives": [
            {"letter": "A", "text": "R$20", "is_correct": False},
            {"letter": "B", "text": "R$25", "is_correct": True},
            {"letter": "C", "text": "R$30", "is_correct": False},
            {"letter": "D", "text": "R$18", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA05",
        "statement": "30% de 90 é:",
        "alternatives": [
            {"letter": "A", "text": "18", "is_correct": False},
            {"letter": "B", "text": "27", "is_correct": True},
            {"letter": "C", "text": "30", "is_correct": False},
            {"letter": "D", "text": "36", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA06",
        "statement": "Dois ângulos que somam 180° são chamados de:",
        "alternatives": [
            {"letter": "A", "text": "Complementares", "is_correct": False},
            {"letter": "B", "text": "Suplementares", "is_correct": True},
            {"letter": "C", "text": "Opostos", "is_correct": False},
            {"letter": "D", "text": "Congruentes", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA07",
        "statement": "A área de um triângulo com base 8 cm e altura 5 cm é:",
        "alternatives": [
            {"letter": "A", "text": "20 cm²", "is_correct": True},
            {"letter": "B", "text": "40 cm²", "is_correct": False},
            {"letter": "C", "text": "13 cm²", "is_correct": False},
            {"letter": "D", "text": "30 cm²", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA08",
        "statement": "A média das notas 6, 7 e 8 é:",
        "alternatives": [
            {"letter": "A", "text": "6", "is_correct": False},
            {"letter": "B", "text": "7", "is_correct": True},
            {"letter": "C", "text": "8", "is_correct": False},
            {"letter": "D", "text": "21", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA09",
        "statement": "Ao lançar uma moeda, a probabilidade de dar 'cara' é:",
        "alternatives": [
            {"letter": "A", "text": "0%", "is_correct": False},
            {"letter": "B", "text": "25%", "is_correct": False},
            {"letter": "C", "text": "50%", "is_correct": True},
            {"letter": "D", "text": "100%", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF07MA10",
        "statement": "Uma figura que tem simetria em relação a uma linha central é chamada de figura:",
        "alternatives": [
            {"letter": "A", "text": "Assimétrica", "is_correct": False},
            {"letter": "B", "text": "Simétrica", "is_correct": True},
            {"letter": "C", "text": "Irregular", "is_correct": False},
            {"letter": "D", "text": "Côncava", "is_correct": False}
        ]
    },

    # ---------------- 8º ANO ----------------
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP01",
        "statement": "Em 'Não fui à festa porque estava doente', a conjunção 'porque' indica:",
        "alternatives": [
            {"letter": "A", "text": "Causa", "is_correct": True},
            {"letter": "B", "text": "Consequência", "is_correct": False},
            {"letter": "C", "text": "Condição", "is_correct": False},
            {"letter": "D", "text": "Tempo", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP02",
        "statement": "Em 'Espero que você venha', a oração 'que você venha' é:",
        "alternatives": [
            {"letter": "A", "text": "Coordenada", "is_correct": False},
            {"letter": "B", "text": "Subordinada", "is_correct": True},
            {"letter": "C", "text": "Independente", "is_correct": False},
            {"letter": "D", "text": "Absoluta", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP03",
        "statement": "Uma resenha crítica tem como objetivo:",
        "alternatives": [
            {"letter": "A", "text": "Apenas narrar uma história", "is_correct": False},
            {"letter": "B", "text": "Analisar e avaliar uma obra", "is_correct": True},
            {"letter": "C", "text": "Dar uma receita", "is_correct": False},
            {"letter": "D", "text": "Fazer uma lista", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP04",
        "statement": "O conectivo 'portanto' indica geralmente:",
        "alternatives": [
            {"letter": "A", "text": "Oposição", "is_correct": False},
            {"letter": "B", "text": "Conclusão", "is_correct": True},
            {"letter": "C", "text": "Adição", "is_correct": False},
            {"letter": "D", "text": "Tempo", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP05",
        "statement": "Dizer 'que dia lindo' durante uma tempestade é um exemplo de:",
        "alternatives": [
            {"letter": "A", "text": "Metáfora", "is_correct": False},
            {"letter": "B", "text": "Ironia", "is_correct": True},
            {"letter": "C", "text": "Comparação", "is_correct": False},
            {"letter": "D", "text": "Onomatopeia", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP06",
        "statement": "Complete: 'Ele assistiu ___ filme.'",
        "alternatives": [
            {"letter": "A", "text": "o", "is_correct": False},
            {"letter": "B", "text": "ao", "is_correct": True},
            {"letter": "C", "text": "no", "is_correct": False},
            {"letter": "D", "text": "do", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP07",
        "statement": "Uma notícia falsa (fake news) se caracteriza por:",
        "alternatives": [
            {"letter": "A", "text": "Ser sempre verdadeira", "is_correct": False},
            {"letter": "B", "text": "Divulgar informações falsas ou distorcidas", "is_correct": True},
            {"letter": "C", "text": "Ser publicada apenas em jornais", "is_correct": False},
            {"letter": "D", "text": "Ter sempre fontes confiáveis", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP08",
        "statement": "Os parênteses são usados para:",
        "alternatives": [
            {"letter": "A", "text": "Substituir o ponto final", "is_correct": False},
            {"letter": "B", "text": "Inserir uma informação adicional no texto", "is_correct": True},
            {"letter": "C", "text": "Terminar uma pergunta", "is_correct": False},
            {"letter": "D", "text": "Indicar diálogo", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP09",
        "statement": "Julgar uma pessoa como 'errada' por falar diferente da norma-padrão é um exemplo de:",
        "alternatives": [
            {"letter": "A", "text": "Respeito linguístico", "is_correct": False},
            {"letter": "B", "text": "Preconceito linguístico", "is_correct": True},
            {"letter": "C", "text": "Norma culta", "is_correct": False},
            {"letter": "D", "text": "Gramática correta", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF08LP10",
        "statement": "Uma carta argumentativa dirigida a uma autoridade tem como principal objetivo:",
        "alternatives": [
            {"letter": "A", "text": "Contar uma história pessoal", "is_correct": False},
            {"letter": "B", "text": "Reivindicar ou defender algo com argumentos", "is_correct": True},
            {"letter": "C", "text": "Fazer uma lista de compras", "is_correct": False},
            {"letter": "D", "text": "Descrever uma paisagem", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA01",
        "statement": "O número √2 é classificado como:",
        "alternatives": [
            {"letter": "A", "text": "Natural", "is_correct": False},
            {"letter": "B", "text": "Inteiro", "is_correct": False},
            {"letter": "C", "text": "Racional", "is_correct": False},
            {"letter": "D", "text": "Irracional", "is_correct": True}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA02",
        "statement": "No sistema x + y = 10 e x - y = 2, o valor de x é:",
        "alternatives": [
            {"letter": "A", "text": "4", "is_correct": False},
            {"letter": "B", "text": "5", "is_correct": False},
            {"letter": "C", "text": "6", "is_correct": True},
            {"letter": "D", "text": "8", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA03",
        "statement": "Quanto é 2³?",
        "alternatives": [
            {"letter": "A", "text": "4", "is_correct": False},
            {"letter": "B", "text": "6", "is_correct": False},
            {"letter": "C", "text": "8", "is_correct": True},
            {"letter": "D", "text": "9", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA04",
        "statement": "Quanto é √16?",
        "alternatives": [
            {"letter": "A", "text": "2", "is_correct": False},
            {"letter": "B", "text": "4", "is_correct": True},
            {"letter": "C", "text": "8", "is_correct": False},
            {"letter": "D", "text": "16", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA05",
        "statement": "Em um triângulo retângulo com catetos 3 e 4, a hipotenusa mede:",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": True},
            {"letter": "B", "text": "6", "is_correct": False},
            {"letter": "C", "text": "7", "is_correct": False},
            {"letter": "D", "text": "9", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA06",
        "statement": "O volume de um cubo com aresta 3 cm é:",
        "alternatives": [
            {"letter": "A", "text": "9 cm³", "is_correct": False},
            {"letter": "B", "text": "18 cm³", "is_correct": False},
            {"letter": "C", "text": "27 cm³", "is_correct": True},
            {"letter": "D", "text": "36 cm³", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA07",
        "statement": "Na sequência 2, 4, 6, 8, 10, a mediana é:",
        "alternatives": [
            {"letter": "A", "text": "4", "is_correct": False},
            {"letter": "B", "text": "5", "is_correct": False},
            {"letter": "C", "text": "6", "is_correct": True},
            {"letter": "D", "text": "8", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA08",
        "statement": "Se 4 pessoas fazem um trabalho em 6 dias, 8 pessoas fariam em:",
        "alternatives": [
            {"letter": "A", "text": "2 dias", "is_correct": False},
            {"letter": "B", "text": "3 dias", "is_correct": True},
            {"letter": "C", "text": "4 dias", "is_correct": False},
            {"letter": "D", "text": "12 dias", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA09",
        "statement": "Na função y = 2x, se x = 3, y é:",
        "alternatives": [
            {"letter": "A", "text": "3", "is_correct": False},
            {"letter": "B", "text": "5", "is_correct": False},
            {"letter": "C", "text": "6", "is_correct": True},
            {"letter": "D", "text": "9", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF08MA10",
        "statement": "Um hexágono regular tem quantos lados?",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "6", "is_correct": True},
            {"letter": "C", "text": "7", "is_correct": False},
            {"letter": "D", "text": "8", "is_correct": False}
        ]
    },

    # ---------------- 9º ANO ----------------
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP01",
        "statement": "O respeito às diferentes variedades linguísticas é importante porque:",
        "alternatives": [
            {"letter": "A", "text": "Todas as formas de falar têm valor comunicativo", "is_correct": True},
            {"letter": "B", "text": "Só a norma-padrão é válida", "is_correct": False},
            {"letter": "C", "text": "Gírias devem ser proibidas", "is_correct": False},
            {"letter": "D", "text": "Sotaques regionais são erros", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP02",
        "statement": "Em 'Se estudar, passarei no exame', a oração 'Se estudar' expressa:",
        "alternatives": [
            {"letter": "A", "text": "Causa", "is_correct": False},
            {"letter": "B", "text": "Condição", "is_correct": True},
            {"letter": "C", "text": "Tempo", "is_correct": False},
            {"letter": "D", "text": "Consequência", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP03",
        "statement": "O texto dissertativo-argumentativo é comumente cobrado em:",
        "alternatives": [
            {"letter": "A", "text": "Bilhetes", "is_correct": False},
            {"letter": "B", "text": "Provas de redação, como o ENEM", "is_correct": True},
            {"letter": "C", "text": "Receitas", "is_correct": False},
            {"letter": "D", "text": "Listas de compras", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP04",
        "statement": "Um texto bem construído evita repetições desnecessárias usando:",
        "alternatives": [
            {"letter": "A", "text": "Sinônimos e pronomes", "is_correct": True},
            {"letter": "B", "text": "Sempre a mesma palavra", "is_correct": False},
            {"letter": "C", "text": "Frases desconexas", "is_correct": False},
            {"letter": "D", "text": "Apenas números", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP05",
        "statement": "'Ele leu Machado de Assis' é um exemplo de:",
        "alternatives": [
            {"letter": "A", "text": "Metáfora", "is_correct": False},
            {"letter": "B", "text": "Metonímia", "is_correct": True},
            {"letter": "C", "text": "Hipérbole", "is_correct": False},
            {"letter": "D", "text": "Comparação", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP06",
        "statement": "Complete: 'Fazem dois anos que ele saiu.' A forma correta é:",
        "alternatives": [
            {"letter": "A", "text": "Fazem", "is_correct": False},
            {"letter": "B", "text": "Faz", "is_correct": True},
            {"letter": "C", "text": "Fazia", "is_correct": False},
            {"letter": "D", "text": "Fizeram", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP07",
        "statement": "Ao ler um texto, identificar a intenção do autor ajuda o leitor a:",
        "alternatives": [
            {"letter": "A", "text": "Memorizar o texto", "is_correct": False},
            {"letter": "B", "text": "Compreender o ponto de vista apresentado", "is_correct": True},
            {"letter": "C", "text": "Ignorar o conteúdo", "is_correct": False},
            {"letter": "D", "text": "Copiar o texto", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP08",
        "statement": "O uso correto da pontuação em um texto contribui para:",
        "alternatives": [
            {"letter": "A", "text": "Deixar o texto mais confuso", "is_correct": False},
            {"letter": "B", "text": "Facilitar a compreensão da leitura", "is_correct": True},
            {"letter": "C", "text": "Aumentar o número de palavras", "is_correct": False},
            {"letter": "D", "text": "Tornar o texto informal", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP09",
        "statement": "Um texto que combina imagem, som e palavra escrita é chamado de:",
        "alternatives": [
            {"letter": "A", "text": "Texto monomodal", "is_correct": False},
            {"letter": "B", "text": "Texto multimodal", "is_correct": True},
            {"letter": "C", "text": "Texto simples", "is_correct": False},
            {"letter": "D", "text": "Texto oral", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Língua Portuguesa",
        "bncc_code": "EF09LP10",
        "statement": "Em uma dissertação argumentativa, a conclusão deve:",
        "alternatives": [
            {"letter": "A", "text": "Apresentar um novo tema", "is_correct": False},
            {"letter": "B", "text": "Retomar a tese e propor um fechamento", "is_correct": True},
            {"letter": "C", "text": "Ser idêntica à introdução", "is_correct": False},
            {"letter": "D", "text": "Não ter relação com o texto", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA01",
        "statement": "O conjunto dos números reais inclui:",
        "alternatives": [
            {"letter": "A", "text": "Apenas números naturais", "is_correct": False},
            {"letter": "B", "text": "Racionais e irracionais", "is_correct": True},
            {"letter": "C", "text": "Apenas números inteiros", "is_correct": False},
            {"letter": "D", "text": "Apenas frações", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA02",
        "statement": "Na equação x² - 9 = 0, os valores de x são:",
        "alternatives": [
            {"letter": "A", "text": "3 e -3", "is_correct": True},
            {"letter": "B", "text": "9 e -9", "is_correct": False},
            {"letter": "C", "text": "3 apenas", "is_correct": False},
            {"letter": "D", "text": "-3 apenas", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA03",
        "statement": "Na função y = 3x + 1, se x = 2, y é:",
        "alternatives": [
            {"letter": "A", "text": "5", "is_correct": False},
            {"letter": "B", "text": "6", "is_correct": False},
            {"letter": "C", "text": "7", "is_correct": True},
            {"letter": "D", "text": "8", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA04",
        "statement": "Um triângulo retângulo tem catetos 6 e 8. A hipotenusa mede:",
        "alternatives": [
            {"letter": "A", "text": "9", "is_correct": False},
            {"letter": "B", "text": "10", "is_correct": True},
            {"letter": "C", "text": "12", "is_correct": False},
            {"letter": "D", "text": "14", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA05",
        "statement": "Dois triângulos semelhantes têm:",
        "alternatives": [
            {"letter": "A", "text": "Lados iguais e ângulos diferentes", "is_correct": False},
            {"letter": "B", "text": "Ângulos correspondentes iguais e lados proporcionais", "is_correct": True},
            {"letter": "C", "text": "Nenhuma relação entre si", "is_correct": False},
            {"letter": "D", "text": "Áreas sempre iguais", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA06",
        "statement": "Em um conjunto de dados, a amplitude é calculada por:",
        "alternatives": [
            {"letter": "A", "text": "Maior valor menos menor valor", "is_correct": True},
            {"letter": "B", "text": "Soma de todos os valores", "is_correct": False},
            {"letter": "C", "text": "Média dos valores", "is_correct": False},
            {"letter": "D", "text": "Valor mais frequente", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA07",
        "statement": "Em um baralho de 52 cartas, a probabilidade de tirar um Ás é:",
        "alternatives": [
            {"letter": "A", "text": "1/52", "is_correct": False},
            {"letter": "B", "text": "4/52", "is_correct": True},
            {"letter": "C", "text": "13/52", "is_correct": False},
            {"letter": "D", "text": "1/13", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA08",
        "statement": "O número 3.000.000 em notação científica é:",
        "alternatives": [
            {"letter": "A", "text": "3 x 10⁴", "is_correct": False},
            {"letter": "B", "text": "3 x 10⁵", "is_correct": False},
            {"letter": "C", "text": "3 x 10⁶", "is_correct": True},
            {"letter": "D", "text": "3 x 10⁷", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA09",
        "statement": "Um cilindro tem quantas bases circulares?",
        "alternatives": [
            {"letter": "A", "text": "1", "is_correct": False},
            {"letter": "B", "text": "2", "is_correct": True},
            {"letter": "C", "text": "3", "is_correct": False},
            {"letter": "D", "text": "0", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Matemática",
        "bncc_code": "EF09MA10",
        "statement": "Em um triângulo retângulo, o seno de um ângulo é a razão entre:",
        "alternatives": [
            {"letter": "A", "text": "Cateto oposto e hipotenusa", "is_correct": True},
            {"letter": "B", "text": "Cateto adjacente e hipotenusa", "is_correct": False},
            {"letter": "C", "text": "Cateto oposto e cateto adjacente", "is_correct": False},
            {"letter": "D", "text": "Hipotenusa e cateto oposto", "is_correct": False}
        ]
    },

    # ---------------- QUESTÕES ADICIONAIS: CIÊNCIAS DA NATUREZA (1º AO 9º ANO) ----------------
    {
        "grade_year": "1º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF01CI01",
        "statement": "Qual órgão dos sentidos usamos para enxergar as cores dos objetos?",
        "alternatives": [
            {"letter": "A", "text": "Orelhas", "is_correct": False},
            {"letter": "B", "text": "Olhos", "is_correct": True},
            {"letter": "C", "text": "Nariz", "is_correct": False},
            {"letter": "D", "text": "Língua", "is_correct": False}
        ]
    },
    {
        "grade_year": "2º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF02CI04",
        "statement": "As plantas precisam de luz do sol, solo fértil e de qual elemento fundamental para crescer?",
        "alternatives": [
            {"letter": "A", "text": "Água", "is_correct": True},
            {"letter": "B", "text": "Fogo", "is_correct": False},
            {"letter": "C", "text": "Plástico", "is_correct": False},
            {"letter": "D", "text": "Sal puro", "is_correct": False}
        ]
    },
    {
        "grade_year": "3º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF03CI04",
        "statement": "Animais que se alimentam exclusivamente de outros animais são classificados como:",
        "alternatives": [
            {"letter": "A", "text": "Herbívoros", "is_correct": False},
            {"letter": "B", "text": "Carnívoros", "is_correct": True},
            {"letter": "C", "text": "Onívoros", "is_correct": False},
            {"letter": "D", "text": "Vegetarianos", "is_correct": False}
        ]
    },
    {
        "grade_year": "4º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF04CI01",
        "statement": "A passagem da água do estado líquido para o estado gasoso pelo calor do Sol chama-se:",
        "alternatives": [
            {"letter": "A", "text": "Solidificação", "is_correct": False},
            {"letter": "B", "text": "Evaporação", "is_correct": True},
            {"letter": "C", "text": "Fusão", "is_correct": False},
            {"letter": "D", "text": "Condensação", "is_correct": False}
        ]
    },
    {
        "grade_year": "5º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF05CI06",
        "statement": "Qual sistema do corpo humano é responsável por bombear o sangue para todos os tecidos?",
        "alternatives": [
            {"letter": "A", "text": "Sistema digestório", "is_correct": False},
            {"letter": "B", "text": "Sistema cardiovascular", "is_correct": True},
            {"letter": "C", "text": "Sistema respiratório", "is_correct": False},
            {"letter": "D", "text": "Sistema esquelético", "is_correct": False}
        ]
    },
    {
        "grade_year": "6º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF06CI02",
        "statement": "As rochas formadas pelo resfriamento e solidificação do magma vulcânico são chamadas de:",
        "alternatives": [
            {"letter": "A", "text": "Sedimentares", "is_correct": False},
            {"letter": "B", "text": "Magmáticas (ou Ígneas)", "is_correct": True},
            {"letter": "C", "text": "Metamórficas", "is_correct": False},
            {"letter": "D", "text": "Orgânicas", "is_correct": False}
        ]
    },
    {
        "grade_year": "7º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF07CI07",
        "statement": "Qual bioma brasileiro possui vegetação adaptada a períodos de seca com folhas reduzidas ou espinhos?",
        "alternatives": [
            {"letter": "A", "text": "Floresta Amazônica", "is_correct": False},
            {"letter": "B", "text": "Caatinga", "is_correct": True},
            {"letter": "C", "text": "Mata Atlântica", "is_correct": False},
            {"letter": "D", "text": "Pantanal", "is_correct": False}
        ]
    },
    {
        "grade_year": "8º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF08CI01",
        "statement": "Qual tipo de usina de geração de energia utiliza a força dos ventos para produzir eletricidade limpa?",
        "alternatives": [
            {"letter": "A", "text": "Termelétrica", "is_correct": False},
            {"letter": "B", "text": "Eólica", "is_correct": True},
            {"letter": "C", "text": "Nuclear", "is_correct": False},
            {"letter": "D", "text": "Carboelétrica", "is_correct": False}
        ]
    },
    {
        "grade_year": "9º Ano",
        "discipline": "Ciências",
        "bncc_code": "EF09CI03",
        "statement": "A unidade fundamental da matéria constituída por prótons, nêutrons e elétrons é denominada:",
        "alternatives": [
            {"letter": "A", "text": "Célula", "is_correct": False},
            {"letter": "B", "text": "Átomo", "is_correct": True},
            {"letter": "C", "text": "Molécula", "is_correct": False},
            {"letter": "D", "text": "Composto", "is_correct": False}
        ]
    }
]
