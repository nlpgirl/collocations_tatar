import csv
import math
from collections import defaultdict
import os
import subprocess
import re

def process_corpus_with_apertium(csv_path):
    encoding='utf-8'
    text_column='cleaned_text_chunks'
    corpus = []
    original_dir = os.getcwd()  # Сохраняем текущую директорию
    # Переходим в директорию с Apertium
    os.chdir('/home/aigul/apertium-tat')
    with open(csv_path, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row[text_column].lower().strip()
            if not text:
                continue

            # Вызов Apertium из нужной директории
            cmd = f'echo "{text}" | apertium -d . tat-tagger'
            try:
                output = subprocess.check_output(
                    cmd,
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )

                # Парсинг вывода
                lemmas = []
                for token in re.findall(r'\^([^/]+)/([^$]+)\$', output):
                    parts = token[1].split('<')
                    lemma = parts[0]
                    pos = parts[1].split('>')[0] if len(parts) > 1 else 'UNK'
                    lemmas.append((lemma, pos))

                corpus.append(lemmas)

            except subprocess.CalledProcessError:
                continue

    os.chdir(original_dir)

    return corpus

corpus = process_corpus_with_apertium("/home/aigul/Desktop/tatproject/test_little.csv")


from collections import defaultdict
import re

def find_collocations(corpus, target_noun, window_size=1):
    """
    Находит коллокации для заданного существительного по шаблону "прилагательное+существительное"

    Параметры:
    - corpus: список предложений с леммами и частями речи
    - target_noun: целевое существительное (в лемматизированной форме)
    - window_size: размер контекстного окна

    Возвращает:
    - unigrams: словарь частот прилагательных
    - collocations: словарь частот биграмм (прилагательное, существительное)
    """

    unigrams = defaultdict(int)
    collocations = defaultdict(int)

    target_noun = target_noun.lower().strip()

    for sentence in corpus:
        for i, (lemma, pos) in enumerate(sentence):
            unigrams[lemma] += 1
            # Ищем целевое существительное
            if lemma == target_noun and pos == 'n':
                # Проверяем окно слева
                start = max(0, i - window_size)
                for j in range(start, i):
                    colloc_lemma, colloc_pos = sentence[j]

                    # Проверка условий:
                    # 1. Часть речи - прилагательное
                    # 2. Соответствует шаблону "adj + noun"
                    if (colloc_pos == 'adj'):
                        collocations[colloc_lemma] += 1


    return dict(unigrams), dict(collocations)

result = find_collocations(corpus, "ватан")

import math
from collections import defaultdict

def calculate_association_measures(corpus, target_noun, window_size=1):
    """
    Вычисляет меры ассоциации (MI, MI3, Dice) для биграмм с целевым существительным.

    Параметры:
    - corpus: список предложений с леммами и частями речи
    - target_noun: целевое существительное (в лемматизированной форме)
    - window_size: размер контекстного окна

    Возвращает:
    - result_dict: словарь, где ключ - прилагательное, значение - кортеж (MI, MI3, Dice)
    """
    # Получаем частоты слов и коллокаций
    unigrams, collocations = find_collocations(corpus, target_noun, window_size)

    # Общее количество слов в корпусе (N)
    N = sum(unigrams.values())

    # Частота целевого существительного
    f_noun = unigrams.get(target_noun, 0)

    # Словарь для результатов
    result_dict = {}

    # Перебираем все биграммы из коллокаций
    for adj, f_adj_noun in collocations.items():
        # Частота прилагательного в корпусе
        f_adj = unigrams.get(adj, 0)

        # Пропускаем прилагательные с нулевой частотой или отсутствующие в unigrams
        if f_adj == 0 or f_noun == 0:
            continue

        # 1. Вычисление Mutual Information (MI)
        try:
            mi = math.log2((f_adj_noun * N) / (f_adj * f_noun))
        except ValueError:
            mi = float('-inf')  # Обработка нулевого значения в логарифме

        # 2. Вычисление MI3 (кубическая взаимная информация)
        try:
            mi3 = math.log2((f_adj_noun**3 * N) / (f_adj * f_noun))
        except ValueError:
            mi3 = float('-inf')

        # 3. Вычисление коэффициента Dice
        dice = (2 * f_adj_noun) / (f_adj + f_noun)

        # Сохраняем результаты
        result_dict[adj] = (mi, mi3, dice)

    return result_dict

calculate_association_measures(corpus, "ватан")

calculate_association_measures(corpus, "вакыт")
