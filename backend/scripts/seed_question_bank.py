#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_question_bank.py - Popula o Banco de Questões do Sistema (PostgreSQL / SQLite)
com o acervo pedagógico oficial da BNCC (1º ao 9º Ano) para Língua Portuguesa e Matemática.

Compatível com:
- PostgreSQL em produção (lendo DATABASE_URL do .env)
- SQLite em desenvolvimento local

Regra de Idempotência:
- Não duplica questões se o mesmo enunciado já existir no banco.
"""

import os
import sys
import uuid
import logging
from datetime import datetime

# Garantir path raiz do backend
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    env_file = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(env_file):
        env_file = os.path.join(BACKEND_DIR, ".env")
    load_dotenv(env_file)
except Exception:
    pass

from app.services.database import get_connection, is_postgres
from app.services.exam_builder_db import init_builder_db

logger = logging.getLogger("seed_questions")

# ---------------------------------------------------------------------------
# Catálogo de Questões BNCC (1º ao 9º Ano)
# Cada item: (ano, disciplina, codigo_habilidade, enunciado, alt_a, alt_b, alt_c, alt_d, resposta_correta)
# ---------------------------------------------------------------------------
RAW_QUESTIONS = []

def q(ano, disc, cod, enun, a, b, c, d, resp):
    RAW_QUESTIONS.append({
        "grade_year": ano,
        "discipline": disc,
        "bncc_code": cod,
        "statement": enun,
        "alt_a": a,
        "alt_b": b,
        "alt_c": c,
        "alt_d": d,
        "correct": resp.strip().upper()
    })

# ---------------- 1º ANO ----------------
q("1º Ano","Língua Portuguesa","EF01LP01","Quantas letras tem a palavra CASA?","3","4","5","6","B")
q("1º Ano","Língua Portuguesa","EF01LP02","Quantas sílabas tem a palavra BOLA?","1","2","3","4","B")
q("1º Ano","Língua Portuguesa","EF01LP03","Qual das palavras abaixo começa com vogal?","Gato","Amigo","Rato","Sapo","B")
q("1º Ano","Língua Portuguesa","EF01LP04","Qual palavra rima com 'PATO'?","Gato","Mesa","Livro","Sol","A")
q("1º Ano","Língua Portuguesa","EF01LP05","Qual letra vem depois de 'C' no alfabeto?","B","D","A","E","B")
q("1º Ano","Língua Portuguesa","EF01LP06","Qual é a primeira letra da palavra 'ELEFANTE'?","L","E","F","A","B")
q("1º Ano","Língua Portuguesa","EF01LP07","Uma lista de compras serve para:","Contar uma história","Anotar o que precisamos comprar","Explicar uma receita","Fazer uma poesia","B")
q("1º Ano","Língua Portuguesa","EF01LP08","No final de uma pergunta usamos o sinal:","Ponto final (.)","Vírgula (,)","Ponto de interrogação (?)","Dois pontos (:)","C")
q("1º Ano","Língua Portuguesa","EF01LP09","Qual das palavras deve começar com letra maiúscula?","cadeira","maria","escola","livro","B")
q("1º Ano","Língua Portuguesa","EF01LP10","Se uma história começa com 'Era uma vez...', ela provavelmente é:","Uma receita","Um conto de fadas","Uma lista","Um bilhete","B")

q("1º Ano","Matemática","EF01MA01","Quantos lados tem um triângulo?","2","3","4","5","B")
q("1º Ano","Matemática","EF01MA02","Qual número vem depois do 7?","6","8","9","5","B")
q("1º Ano","Matemática","EF01MA03","Qual número é maior: 8 ou 5?","5","8","São iguais","Nenhum","B")
q("1º Ano","Matemática","EF01MA04","Quanto é 3 + 2?","4","5","6","7","B")
q("1º Ano","Matemática","EF01MA05","Quanto é 6 - 2?","3","4","5","2","B")
q("1º Ano","Matemática","EF01MA06","Uma bola tem o formato de:","Quadrado","Círculo","Triângulo","Retângulo","B")
q("1º Ano","Matemática","EF01MA07","5 é o mesmo que:","2+2","3+2","4+2","1+1","B")
q("1º Ano","Matemática","EF01MA08","Qual é maior: um elefante ou um rato?","O rato","O elefante","São do mesmo tamanho","Não dá para saber","B")
q("1º Ano","Matemática","EF01MA09","Quantos dias tem uma semana?","5","6","7","8","C")
q("1º Ano","Matemática","EF01MA10","Se Ana tem 4 bonecas e ganha mais 1, quantas ela tem agora?","4","5","6","3","B")

# ---------------- 2º ANO ----------------
q("2º Ano","Língua Portuguesa","EF02LP01","Complete: 'Ele co___prou um doce.' A letra que falta é:","N","M","L","R","B")
q("2º Ano","Língua Portuguesa","EF02LP02","Quantas sílabas tem a palavra 'CACHORRO'?","2","3","4","5","B")
q("2º Ano","Língua Portuguesa","EF02LP03","Um grupo de pássaros é chamado de:","Cardume","Bando","Matilha","Rebanho","B")
q("2º Ano","Língua Portuguesa","EF02LP04","Uma palavra parecida com 'feliz' é:","Triste","Alegre","Bravo","Cansado","B")
q("2º Ano","Língua Portuguesa","EF02LP05","Um bilhete serve para:","Contar uma história longa","Deixar um recado rápido","Explicar uma pesquisa","Fazer uma lista de compras","B")
q("2º Ano","Língua Portuguesa","EF02LP06","O plural de 'flor' é:","Flors","Flores","Floris","Florzinha","B")
q("2º Ano","Língua Portuguesa","EF02LP07","A palavra 'árvore' tem acento porque é:","Oxítona","Paroxítona","Proparoxítona","Não tem acento","C")
q("2º Ano","Língua Portuguesa","EF02LP08","Qual sinal usamos para expressar surpresa?","Vírgula","Ponto de exclamação (!)","Dois pontos","Reticências","B")
q("2º Ano","Língua Portuguesa","EF02LP09","O antônimo de 'grande' é:","Enorme","Pequeno","Alto","Largo","B")
q("2º Ano","Língua Portuguesa","EF02LP10","Se um texto diz 'o menino correu para a escola porque estava atrasado', o menino correu porque:","Gostava de correr","Estava atrasado","Estava com fome","Era um dia de sol","B")

q("2º Ano","Matemática","EF02MA01","No número 47, o algarismo 4 representa:","4 unidades","4 dezenas","4 centenas","4 milhares","B")
q("2º Ano","Matemática","EF02MA02","Quanto é 25 + 17?","32","42","40","52","B")
q("2º Ano","Matemática","EF02MA03","Quanto é 50 - 23?","27","37","23","33","A")
q("2º Ano","Matemática","EF02MA04","O dobro de 6 é:","8","10","12","16","C")
q("2º Ano","Matemática","EF02MA05","Quantos lados tem um quadrado?","3","4","5","6","B")
q("2º Ano","Matemática","EF02MA06","Um dia tem quantas horas?","12","20","24","30","C")
q("2º Ano","Matemática","EF02MA07","Se eu tenho 2 moedas de R$1 e 1 moeda de R$0,50, quanto tenho no total?","R$1,50","R$2,00","R$2,50","R$3,00","C")
q("2º Ano","Matemática","EF02MA08","3 grupos de 4 bolinhas. Quantas bolinhas há ao todo?","7","10","12","14","C")
q("2º Ano","Matemática","EF02MA09","A metade de 10 é:","3","4","5","6","C")
q("2º Ano","Matemática","EF02MA10","Em uma tabela, João marcou 5 pontos e Pedro marcou 3. Quem marcou mais pontos?","Pedro","João","Os dois empataram","Não é possível saber","B")

# ---------------- 3º ANO ----------------
q("3º Ano","Língua Portuguesa","EF03LP01","Qual é a forma correta da palavra?","Queijada","Cueijada","Kueijada","Cheijada","A")
q("3º Ano","Língua Portuguesa","EF03LP02","Em 'O cachorro correu rápido', a palavra 'cachorro' é um:","Verbo","Substantivo","Adjetivo","Advérbio","B")
q("3º Ano","Língua Portuguesa","EF03LP03","Em 'A casa azul é bonita', a palavra 'azul' é um:","Substantivo","Adjetivo","Verbo","Pronome","B")
q("3º Ano","Língua Portuguesa","EF03LP04","Uma receita culinária apresenta, principalmente:","Ingredientes e modo de preparo","Personagens e enredo","Opiniões sobre um tema","Uma sequência de piadas","A")
q("3º Ano","Língua Portuguesa","EF03LP05","Complete: 'Os meninos ___ para a escola.'","vai","vão","foi","iam","B")
q("3º Ano","Língua Portuguesa","EF03LP06","O antônimo de 'rápido' é:","Veloz","Lento","Ligeiro","Ágil","B")
q("3º Ano","Língua Portuguesa","EF03LP07","Um texto informa que 'choveu muito e o rio transbordou'. O que causou o transbordamento?","O vento","A chuva","O calor","A seca","B")
q("3º Ano","Língua Portuguesa","EF03LP08","Qual frase está pontuada corretamente?","Comprei maçã banana e uva","Comprei, maçã banana e uva","Comprei maçã, banana e uva","Comprei maçã banana, e uva","C")
q("3º Ano","Língua Portuguesa","EF03LP09","Para saber o significado de uma palavra desconhecida, devemos consultar:","Uma revista em quadrinhos","Um dicionário","Uma lista de compras","Um bilhete","B")
q("3º Ano","Língua Portuguesa","EF03LP10","Um convite de aniversário tem como objetivo:","Explicar uma receita","Convidar alguém para um evento","Contar uma história","Fazer uma reclamação","B")

q("3º Ano","Matemática","EF03MA01","O número 'dois mil e trezentos' se escreve:","2003","2300","230","20300","B")
q("3º Ano","Matemática","EF03MA02","Quanto é 6 x 4?","18","20","24","28","C")
q("3º Ano","Matemática","EF03MA03","Quanto é 20 ÷ 5?","3","4","5","6","B")
q("3º Ano","Matemática","EF03MA04","Se uma pizza foi dividida em 4 partes iguais e comemos 1, comemos:","1/2","1/3","1/4","1/5","C")
q("3º Ano","Matemática","EF03MA05","Um cubo tem quantas faces?","4","5","6","8","C")
q("3º Ano","Matemática","EF03MA06","Qual unidade usamos para medir a distância entre duas cidades?","Grama","Litro","Quilômetro","Metro quadrado","C")
q("3º Ano","Matemática","EF03MA07","Para pesar uma pessoa, usamos como unidade principal:","Litro","Quilograma","Metro","Segundo","B")
q("3º Ano","Matemática","EF03MA08","Maria tinha R$50, gastou R$20 e depois ganhou R$10. Com quanto ficou?","R$30","R$40","R$20","R$60","B")
q("3º Ano","Matemática","EF03MA09","Quantos meses tem um ano?","10","11","12","13","C")
q("3º Ano","Matemática","EF03MA10","Em um gráfico, a barra mais alta representa:","O menor valor","O maior valor","A média","Não representa nada","B")

# ---------------- 4º ANO ----------------
q("4º Ano","Língua Portuguesa","EF04LP01","Qual é a forma correta?","Casa","Caza","Cassa","Cás","A")
q("4º Ano","Língua Portuguesa","EF04LP02","Em 'Ela foi ao mercado', a palavra 'Ela' é um:","Substantivo","Pronome","Verbo","Advérbio","B")
q("4º Ano","Língua Portuguesa","EF04LP03","'Eu comi' está no tempo:","Presente","Passado","Futuro","Nenhum dos anteriores","B")
q("4º Ano","Língua Portuguesa","EF04LP04","Uma notícia de jornal tem como principal objetivo:","Divertir com piadas","Informar sobre fatos reais","Ensinar uma receita","Contar uma fábula","B")
q("4º Ano","Língua Portuguesa","EF04LP05","'Ele é forte como um leão' é um exemplo de:","Metáfora","Comparação","Rima","Onomatopeia","B")
q("4º Ano","Língua Portuguesa","EF04LP06","Complete: 'As casas ___ bonitas.'","é","são","foi","sou","B")
q("4º Ano","Língua Portuguesa","EF04LP07","Um texto diz: 'O sol se pôs e ficou escuro.' Isso aconteceu porque:","Choveu","Anoiteceu","Nevou","Ventou","B")
q("4º Ano","Língua Portuguesa","EF04LP08","Os dois pontos (:) são usados para:","Terminar uma frase","Introduzir uma explicação ou lista","Fazer uma pergunta","Expressar surpresa","B")
q("4º Ano","Língua Portuguesa","EF04LP09","Falar de forma diferente dependendo da região do país é chamado de:","Erro de português","Variação linguística","Gramática errada","Plágio","B")
q("4º Ano","Língua Portuguesa","EF04LP10","Uma carta pessoal geralmente começa com:","Uma saudação, como 'Querido amigo'","Uma lista de ingredientes","Uma tabela","Um gráfico","A")

q("4º Ano","Matemática","EF04MA01","O número 45.320 é lido como:","Quatro mil trezentos e vinte","Quarenta e cinco mil, trezentos e vinte","Quatrocentos e cinco mil e vinte","Quarenta e cinco mil e três","B")
q("4º Ano","Matemática","EF04MA02","Quanto é 12 x 5?","50","55","60","65","C")
q("4º Ano","Matemática","EF04MA03","Quanto é 17 ÷ 4?","4 com resto 1","3 com resto 2","4 com resto 0","5 com resto 1","A")
q("4º Ano","Matemática","EF04MA04","1/2 é equivalente a:","2/4","1/4","3/4","2/3","A")
q("4º Ano","Matemática","EF04MA05","Um ângulo reto mede:","45°","90°","180°","360°","B")
q("4º Ano","Matemática","EF04MA06","O perímetro de um quadrado de lado 5 cm é:","10 cm","15 cm","20 cm","25 cm","C")
q("4º Ano","Matemática","EF04MA07","Para medir a quantidade de água em uma garrafa, usamos:","Metro","Litro","Quilograma","Grau","B")
q("4º Ano","Matemática","EF04MA08","Pedro comprou 3 pacotes com 8 balas cada e comeu 5. Quantas balas sobraram?","16","19","21","24","B")
q("4º Ano","Matemática","EF04MA09","O número 3,5 é lido como:","Três e cinco","Três vírgula cinco","Trinta e cinco","Três meios","B")
q("4º Ano","Matemática","EF04MA10","Ao jogar um dado, qual é a chance de sair o número 7?","Alta","Média","Impossível","Certa","C")

# ---------------- 5º ANO ----------------
q("5º Ano","Língua Portuguesa","EF05LP01","Qual é a forma correta?","Chuva","Xuva","Chuba","Xuba","A")
q("5º Ano","Língua Portuguesa","EF05LP02","Em 'Estudei, mas não fui bem na prova', a palavra 'mas' indica:","Adição","Oposição","Causa","Tempo","B")
q("5º Ano","Língua Portuguesa","EF05LP03","'Maria disse: Eu vou à festa' é um exemplo de discurso:","Indireto","Direto","Narrativo","Descritivo","B")
q("5º Ano","Língua Portuguesa","EF05LP04","Um artigo de opinião tem como objetivo principal:","Narrar uma história fictícia","Defender um ponto de vista sobre um tema","Dar uma receita","Listar compras","B")
q("5º Ano","Língua Portuguesa","EF05LP05","'Seus olhos são estrelas' é um exemplo de:","Comparação","Metáfora","Onomatopeia","Aliteração","B")
q("5º Ano","Língua Portuguesa","EF05LP06","Complete corretamente: 'Eu gosto ___ chocolate.'","do","de","o","do de","B")
q("5º Ano","Língua Portuguesa","EF05LP07","Um texto publicitário tem como principal intenção:","Informar de forma neutra","Convencer o leitor a comprar algo","Contar uma fábula","Ensinar gramática","B")
q("5º Ano","Língua Portuguesa","EF05LP08","O travessão (—) é usado principalmente para:","Indicar fala de personagens em diálogos","Substituir a vírgula","Terminar frases","Fazer perguntas","A")
q("5º Ano","Língua Portuguesa","EF05LP09","Em 'Ana comprou um livro e o leu', a palavra 'o' substitui:","Ana","Livro","Leu","Comprou","B")
q("5º Ano","Língua Portuguesa","EF05LP10","Um relato pessoal é escrito, geralmente, na:","1ª pessoa","2ª pessoa","3ª pessoa","Nenhuma pessoa","A")

q("5º Ano","Matemática","EF05MA01","A fração 1/2 corresponde ao decimal:","0,2","0,5","1,2","0,12","B")
q("5º Ano","Matemática","EF05MA02","Quanto é 245 + 178?","413","423","433","443","B")
q("5º Ano","Matemática","EF05MA03","50% de 200 é:","50","100","150","200","B")
q("5º Ano","Matemática","EF05MA04","A área de um retângulo de base 6 cm e altura 4 cm é:","10 cm²","20 cm²","24 cm²","28 cm²","C")
q("5º Ano","Matemática","EF05MA05","Um cubo com aresta de 2 cm tem volume de:","4 cm³","6 cm³","8 cm³","12 cm³","C")
q("5º Ano","Matemática","EF05MA06","A média entre 4, 6 e 8 é:","5","6","7","8","B")
q("5º Ano","Matemática","EF05MA07","Se 2 cadernos custam R$10, quanto custam 4 cadernos?","R$15","R$20","R$25","R$30","B")
q("5º Ano","Matemática","EF05MA08","Uma loja tinha 120 produtos, vendeu 45 e recebeu mais 30. Quantos produtos tem agora?","95","105","115","125","B")
q("5º Ano","Matemática","EF05MA09","Em um gráfico, se a coluna de 'maçãs' está mais alta que a de 'bananas', isso significa que:","Há mais bananas","Há mais maçãs","A quantidade é igual","Não é possível saber","B")
q("5º Ano","Matemática","EF05MA10","A temperatura de -2°C é:","Maior que 0°C","Menor que 0°C","Igual a 0°C","Não existe","B")

# ---------------- 6º ANO ----------------
q("6º Ano","Língua Portuguesa","EF06LP01","O uso da norma-padrão é mais exigido em:","Uma conversa informal com amigos","Uma redação escolar formal","Uma mensagem de WhatsApp","Uma letra de música","B")
q("6º Ano","Língua Portuguesa","EF06LP02","Em 'Os alunos estudaram muito', a palavra 'estudaram' é:","Substantivo","Verbo","Adjetivo","Pronome","B")
q("6º Ano","Língua Portuguesa","EF06LP03","Uma fábula geralmente termina com:","Uma receita","Uma moral da história","Uma lista","Uma notícia","B")
q("6º Ano","Língua Portuguesa","EF06LP04","Um texto é coerente quando:","Tem muitas palavras difíceis","Suas ideias fazem sentido entre si","É muito longo","Não tem pontuação","B")
q("6º Ano","Língua Portuguesa","EF06LP05","'O vento sussurrava segredos' é um exemplo de:","Metáfora","Personificação","Hipérbole","Rima","B")
q("6º Ano","Língua Portuguesa","EF06LP06","Complete: 'Nós ___ para a escola juntos.'","vai","vamos","vão","foi","B")
q("6º Ano","Língua Portuguesa","EF06LP07","Se um texto diz 'ele pegou o guarda-chuva antes de sair', podemos inferir que:","Estava calor","Talvez fosse chover","Ele ia dormir","Ele estava com fome","B")
q("6º Ano","Língua Portuguesa","EF06LP08","O ponto e vírgula (;) é usado para:","Separar itens simples em uma lista curta","Separar orações relacionadas, com pausa maior que a vírgula","Terminar uma frase interrogativa","Substituir o ponto final sempre","B")
q("6º Ano","Língua Portuguesa","EF06LP09","Uma charge combina, geralmente:","Apenas texto","Apenas imagens","Texto e imagem","Apenas números","C")
q("6º Ano","Língua Portuguesa","EF06LP10","Em uma narrativa, o clímax é:","O início da história","O momento de maior tensão","O final feliz","A apresentação dos personagens","B")

q("6º Ano","Matemática","EF06MA01","Qual é o algarismo das centenas no número 3.402?","3","4","0","2","B")
q("6º Ano","Matemática","EF06MA02","Qual dos números é negativo?","5","0","-3","10","C")
q("6º Ano","Matemática","EF06MA03","Quanto é 1/4 + 1/4?","1/2","2/8","1/8","1/4","A")
q("6º Ano","Matemática","EF06MA04","Qual número é múltiplo de 5?","12","15","22","31","B")
q("6º Ano","Matemática","EF06MA05","Quanto é 2 + 3 x 4?","20","14","24","9","B")
q("6º Ano","Matemática","EF06MA06","Um triângulo equilátero tem todos os ângulos internos medindo:","90°","60°","45°","120°","B")
q("6º Ano","Matemática","EF06MA07","O perímetro de um retângulo de lados 5 cm e 3 cm é:","8 cm","15 cm","16 cm","18 cm","C")
q("6º Ano","Matemática","EF06MA08","20% de 50 é:","5","10","15","20","B")
q("6º Ano","Matemática","EF06MA09","Nos dados 2, 3, 3, 5, 7, a moda é:","2","3","5","7","B")
q("6º Ano","Matemática","EF06MA10","Se a razão entre dois números é 2:3 e o menor é 4, o maior é:","5","6","8","9","B")

# ---------------- 7º ANO ----------------
q("7º Ano","Língua Portuguesa","EF07LP01","Em 'Ele correu rapidamente', a palavra 'rapidamente' é um:","Substantivo","Advérbio","Verbo","Pronome","B")
q("7º Ano","Língua Portuguesa","EF07LP02","Em 'Estudei e passei na prova', as orações estão ligadas por uma conjunção:","Adversativa","Aditiva","Alternativa","Conclusiva","B")
q("7º Ano","Língua Portuguesa","EF07LP03","Uma crônica geralmente aborda:","Fatos científicos complexos","Situações do cotidiano de forma reflexiva","Apenas receitas culinárias","Somente notícias policiais","B")
q("7º Ano","Língua Portuguesa","EF07LP04","Em 'O cachorro correu até a árvore e latiu perto dela', a palavra 'dela' se refere a:","Cachorro","Árvore","Latido","Corrida","B")
q("7º Ano","Língua Portuguesa","EF07LP05","'Já te falei mil vezes isso' é um exemplo de:","Metáfora","Hipérbole","Eufemismo","Ironia","B")
q("7º Ano","Língua Portuguesa","EF07LP06","Em 'O livro foi lido pelo aluno', a voz verbal é:","Ativa","Passiva","Reflexiva","Nenhuma","B")
q("7º Ano","Língua Portuguesa","EF07LP07","Um texto argumentativo tem como principal objetivo:","Narrar uma história","Defender uma tese com argumentos","Descrever uma paisagem","Dar instruções","B")
q("7º Ano","Língua Portuguesa","EF07LP08","As aspas são usadas, entre outras funções, para:","Indicar uma citação direta","Terminar uma frase","Separar itens de uma lista","Substituir a vírgula","A")
q("7º Ano","Língua Portuguesa","EF07LP09","O uso de gírias é mais comum em situações:","Formais, como uma entrevista de emprego","Informais, entre amigos","Em documentos oficiais","Em leis","B")
q("7º Ano","Língua Portuguesa","EF07LP10","Em um texto argumentativo, os argumentos devem ser:","Aleatórios e sem relação com o tema","Organizados e relacionados à tese defendida","Apenas opiniões sem fundamento","Substituídos por listas","B")

q("7º Ano","Matemática","EF07MA01","Quanto é (-5) + 8?","-13","3","13","-3","B")
q("7º Ano","Matemática","EF07MA02","Quanto é 1/2 + 1/3?","2/5","5/6","1/5","3/6","B")
q("7º Ano","Matemática","EF07MA03","Se x + 5 = 12, então x é:","5","6","7","8","C")
q("7º Ano","Matemática","EF07MA04","Se 3 kg de arroz custam R$15, quanto custam 5 kg?","R$20","R$25","R$30","R$18","B")
q("7º Ano","Matemática","EF07MA05","30% de 90 é:","18","27","30","36","B")
q("7º Ano","Matemática","EF07MA06","Dois ângulos que somam 180° são chamados de:","Complementares","Suplementares","Opostos","Congruentes","B")
q("7º Ano","Matemática","EF07MA07","A área de um triângulo com base 8 cm e altura 5 cm é:","20 cm²","40 cm²","13 cm²","30 cm²","A")
q("7º Ano","Matemática","EF07MA08","A média das notas 6, 7 e 8 é:","6","7","8","21","B")
q("7º Ano","Matemática","EF07MA09","Ao lançar uma moeda, a probabilidade de dar 'cara' é:","0%","25%","50%","100%","C")
q("7º Ano","Matemática","EF07MA10","Uma figura que tem simetria em relação a uma linha central é chamada de figura:","Assimétrica","Simétrica","Irregular","Côncava","B")

# ---------------- 8º ANO ----------------
q("8º Ano","Língua Portuguesa","EF08LP01","Em 'Não fui à festa porque estava doente', a conjunção 'porque' indica:","Causa","Consequência","Condição","Tempo","A")
q("8º Ano","Língua Portuguesa","EF08LP02","Em 'Espero que você venha', a oração 'que você venha' é:","Coordenada","Subordinada","Independente","Absoluta","B")
q("8º Ano","Língua Portuguesa","EF08LP03","Uma resenha crítica tem como objetivo:","Apenas narrar uma história","Analisar e avaliar uma obra","Dar uma receita","Fazer uma lista","B")
q("8º Ano","Língua Portuguesa","EF08LP04","O conectivo 'portanto' indica geralmente:","Oposição","Conclusão","Adição","Tempo","B")
q("8º Ano","Língua Portuguesa","EF08LP05","Dizer 'que dia lindo' durante uma tempestade é um exemplo de:","Metáfora","Ironia","Comparação","Onomatopeia","B")
q("8º Ano","Língua Portuguesa","EF08LP06","Complete: 'Ele assistiu ___ filme.'","o","ao","no","do","B")
q("8º Ano","Língua Portuguesa","EF08LP07","Uma notícia falsa (fake news) se caracteriza por:","Ser sempre verdadeira","Divulgar informações falsas ou distorcidas","Ser publicada apenas em jornais","Ter sempre fontes confiáveis","B")
q("8º Ano","Língua Portuguesa","EF08LP08","Os parênteses são usados para:","Substituir o ponto final","Inserir uma informação adicional no texto","Terminar uma pergunta","Indicar diálogo","B")
q("8º Ano","Língua Portuguesa","EF08LP09","Julgar uma pessoa como 'errada' por falar diferente da norma-padrão é um exemplo de:","Respeito linguístico","Preconceito linguístico","Norma culta","Gramática correta","B")
q("8º Ano","Língua Portuguesa","EF08LP10","Uma carta argumentativa dirigida a uma autoridade tem como principal objetivo:","Contar uma história pessoal","Reivindicar ou defender algo com argumentos","Fazer uma lista de compras","Descrever uma paisagem","B")

q("8º Ano","Matemática","EF08MA01","O número √2 é classificado como:","Natural","Inteiro","Racional","Irracional","D")
q("8º Ano","Matemática","EF08MA02","No sistema x + y = 10 e x - y = 2, o valor de x é:","4","5","6","8","C")
q("8º Ano","Matemática","EF08MA03","Quanto é 2³?","4","6","8","9","C")
q("8º Ano","Matemática","EF08MA04","Quanto é √16?","2","4","8","16","B")
q("8º Ano","Matemática","EF08MA05","Em um triângulo retângulo com catetos 3 e 4, a hipotenusa mede:","5","6","7","9","A")
q("8º Ano","Matemática","EF08MA06","O volume de um cubo com aresta 3 cm é:","9 cm³","18 cm³","27 cm³","36 cm³","C")
q("8º Ano","Matemática","EF08MA07","Na sequência 2, 4, 6, 8, 10, a mediana é:","4","5","6","8","C")
q("8º Ano","Matemática","EF08MA08","Se 4 pessoas fazem um trabalho em 6 dias, 8 pessoas fariam em:","2 dias","3 dias","4 dias","12 dias","B")
q("8º Ano","Matemática","EF08MA09","Na função y = 2x, se x = 3, y é:","3","5","6","9","C")
q("8º Ano","Matemática","EF08MA10","Um hexágono regular tem quantos lados?","5","6","7","8","B")

# ---------------- 9º ANO ----------------
q("9º Ano","Língua Portuguesa","EF09LP01","O respeito às diferentes variedades linguísticas é importante porque:","Todas as formas de falar têm valor comunicativo","Só a norma-padrão é válida","Gírias devem ser proibidas","Sotaques regionais são erros","A")
q("9º Ano","Língua Portuguesa","EF09LP02","Em 'Se estudar, passarei no exame', a oração 'Se estudar' expressa:","Causa","Condição","Tempo","Consequência","B")
q("9º Ano","Língua Portuguesa","EF09LP03","O texto dissertativo-argumentativo é comumente cobrado em:","Bilhetes","Provas de redação, como o ENEM","Receitas","Listas de compras","B")
q("9º Ano","Língua Portuguesa","EF09LP04","Um texto bem construído evita repetições desnecessárias usando:","Sinônimos e pronomes","Sempre a mesma palavra","Frases desconexas","Apenas números","A")
q("9º Ano","Língua Portuguesa","EF09LP05","'Ele leu Machado de Assis' é um exemplo de:","Metáfora","Metonímia","Hipérbole","Comparação","B")
q("9º Ano","Língua Portuguesa","EF09LP06","Complete: 'Fazem dois anos que ele saiu.' A forma correta é:","Fazem","Faz","Fazia","Fizeram","B")
q("9º Ano","Língua Portuguesa","EF09LP07","Ao ler um texto, identificar a intenção do autor ajuda o leitor a:","Memorizar o texto","Compreender o ponto de vista apresentado","Ignorar o conteúdo","Copiar o texto","B")
q("9º Ano","Língua Portuguesa","EF09LP08","O uso correto da pontuação em um texto contribui para:","Deixar o texto mais confuso","Facilitar a compreensão da leitura","Aumentar o número de palavras","Tornar o texto informal","B")
q("9º Ano","Língua Portuguesa","EF09LP09","Um texto que combina imagem, som e palavra escrita é chamado de:","Texto monomodal","Texto multimodal","Texto simples","Texto oral","B")
q("9º Ano","Língua Portuguesa","EF09LP10","Em uma dissertação argumentativa, a conclusão deve:","Apresentar um novo tema","Retomar a tese e propor um fechamento","Ser idêntica à introdução","Não ter relação com o texto","B")

q("9º Ano","Matemática","EF09MA01","O conjunto dos números reais inclui:","Apenas números naturais","Racionais e irracionais","Apenas números inteiros","Apenas frações","B")
q("9º Ano","Matemática","EF09MA02","Na equação x² - 9 = 0, os valores de x são:","3 e -3","9 e -9","3 apenas","-3 apenas","A")
q("9º Ano","Matemática","EF09MA03","Na função y = 3x + 1, se x = 2, y é:","5","6","7","8","C")
q("9º Ano","Matemática","EF09MA04","Um triângulo retângulo tem catetos 6 e 8. A hipotenusa mede:","9","10","12","14","B")
q("9º Ano","Matemática","EF09MA05","Dois triângulos semelhantes têm:","Lados iguais e ângulos diferentes","Ângulos correspondentes iguais e lados proporcionais","Nenhuma relação entre si","Áreas sempre iguais","B")
q("9º Ano","Matemática","EF09MA06","Em um conjunto de dados, a amplitude é calculada por:","Maior valor menos menor valor","Soma de todos os valores","Média dos valores","Valor mais frequente","A")
q("9º Ano","Matemática","EF09MA07","Em um baralho de 52 cartas, a probabilidade de tirar um Ás é:","1/52","4/52","13/52","1/13","B")
q("9º Ano","Matemática","EF09MA08","O número 3.000.000 em notação científica é:","3 x 10⁴","3 x 10⁵","3 x 10⁶","3 x 10⁷","C")
q("9º Ano","Matemática","EF09MA09","Um cilindro tem quantas bases circulares?","1","2","3","0","B")
q("9º Ano","Matemática","EF09MA10","Em um triângulo retângulo, o seno de um ângulo é a razão entre:","Cateto oposto e hipotenusa","Cateto adjacente e hipotenusa","Cateto oposto e cateto adjacente","Hipotenusa e cateto oposto","A")

# ---------------- QUESTÕES ADICIONAIS: CIÊNCIAS DA NATUREZA (1º AO 9º ANO) ----------------
q("1º Ano","Ciências","EF01CI01","Qual órgão dos sentidos usamos para enxergar as cores dos objetos?","Orelhas","Olhos","Nariz","Língua","B")
q("2º Ano","Ciências","EF02CI04","As plantas precisam de luz solar, solo fértil e de qual elemento fundamental para crescer?","Água","Fogo","Plástico","Sal puro","A")
q("3º Ano","Ciências","EF03CI04","Animais que se alimentam exclusivamente de outros animais são chamados de:","Herbívoros","Carnívoros","Onívoros","Vegetarianos","B")
q("4º Ano","Ciências","EF04CI01","A passagem da água do estado líquido para o estado gasoso pelo calor solar chama-se:","Solidificação","Evaporação","Fusão","Condensação","B")
q("5º Ano","Ciências","EF05CI06","Qual sistema do corpo humano é responsável por bombear o sangue para todos os órgãos?","Sistema digestório","Sistema cardiovascular","Sistema respiratório","Sistema esquelético","B")
q("6º Ano","Ciências","EF06CI02","As rochas formadas pelo resfriamento e solidificação do magma vulcânico são chamadas de:","Sedimentares","Magmáticas (ou Ígneas)","Metamórficas","Orgânicas","B")
q("7º Ano","Ciências","EF07CI07","Qual bioma brasileiro possui vegetação adaptada à seca com folhas reduzidas ou espinhos?","Floresta Amazônica","Caatinga","Mata Atlântica","Pantanal","B")
q("8º Ano","Ciências","EF08CI01","Qual tipo de usina utiliza a força dos ventos para produzir energia elétrica limpa?","Termelétrica","Eólica","Nuclear","Carboelétrica","B")
q("9º Ano","Ciências","EF09CI03","A unidade fundamental da matéria constituída por prótons, nêutrons e elétrons é denominada:","Célula","Átomo","Molécula","Composto","B")


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def seed_questions():
    """Popula as questões no banco de dados ativo (PostgreSQL ou SQLite)."""
    db_type = "PostgreSQL" if is_postgres() else "SQLite"
    print(f"[*] Iniciando populacao do Banco de Questoes no {db_type}...")
    
    # 1. Garantir tabelas criadas
    init_builder_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 2. Obter enunciados já existentes para evitar duplicação
    cursor.execute("SELECT LOWER(TRIM(statement)) FROM builder_questions")
    existing_statements = set()
    for row in cursor.fetchall():
        if row and row[0]:
            existing_statements.add(row[0].strip().lower())
            
    print(f"    - Enunciados ja existentes no banco: {len(existing_statements)}")
    
    inserted_count = 0
    skipped_count = 0
    now = datetime.now().isoformat()
    
    for item in RAW_QUESTIONS:
        stmt = item["statement"].strip()
        stmt_key = stmt.lower()
        
        # Idempotência: se já existe com o mesmo enunciado, pula
        if stmt_key in existing_statements:
            skipped_count += 1
            continue
            
        qid = str(uuid.uuid4())
        
        # Inserir na tabela builder_questions vinculada ao banco geral
        cursor.execute("""
            INSERT INTO builder_questions (
                id, exam_id, question_number, statement, points,
                image_url, image_position, image_width, image_caption,
                created_at, bncc_code, discipline, grade_year, source_exam_title
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            qid,
            "banco_questoes_geral",
            inserted_count + 1,
            stmt,
            1.0,
            "",
            "after_statement",
            "50%",
            "",
            now,
            item["bncc_code"],
            item["discipline"],
            item["grade_year"],
            "Acervo BNCC Oficial"
        ))
        
        # Inserir as 4 alternativas
        alternatives = [
            ("A", item["alt_a"], item["correct"] == "A", 0),
            ("B", item["alt_b"], item["correct"] == "B", 1),
            ("C", item["alt_c"], item["correct"] == "C", 2),
            ("D", item["alt_d"], item["correct"] == "D", 3),
        ]
        
        for letter, text, is_corr, idx in alternatives:
            alt_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO builder_alternatives (
                    id, question_id, letter, text, is_correct, order_index, image_url, image_width, image_align
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alt_id,
                qid,
                letter,
                text,
                1 if is_corr else 0,
                idx,
                "",
                "180px",
                "center"
            ))
            
        existing_statements.add(stmt_key)
        inserted_count += 1
        
    conn.commit()
    conn.close()
    
    print(f"[OK] Concluido com sucesso:")
    print(f"     - Questoes novas inseridas: {inserted_count}")
    print(f"     - Questoes ja existentes ignoradas: {skipped_count}")
    print(f"     - Total no acervo de questoes: {len(RAW_QUESTIONS)}")
    return inserted_count, skipped_count

if __name__ == "__main__":
    seed_questions()
