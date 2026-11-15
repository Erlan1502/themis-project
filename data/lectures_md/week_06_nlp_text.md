---
week_number: 6
topic_id: "week_06_nlp_text"
title: "Неделя 6: Обработка естественного языка (NLP) и анализ текстов"
topic_name: "Библиотеки NLTK/Spacy, токенизация, лемматизация, стемминг, TF-IDF, анализ тональности и суммаризация статей"
initial_prompt: "Привет! На шестой лекции мы погрузились в обработку естественного языка (NLP). Чем лемматизация отличается от стемминга при подготовке текста к обучению моделей, и почему модель мешка слов (Bag-of-Words / TF-IDF) теряет контекст по сравнению с семантическими эмбеддингами?"
source_files:
  - "Lecture 6.1 Libraries and toolkits for NLP (1).ipynb_"
  - "Lecture_6_2_Automatic Summarization of Articles (1).ipynb"
  - "Lecture_6_3_Text_sentiment_1.ipynb"
  - "Лекция 6_NLP (1).pptx"
glossary:
  - "above"
  - "absolutely"
  - "abstract"
  - "accepts"
  - "accessing"
  - "account"
  - "accuracy"
  - "accuracy_score"
  - "actual"
  - "add_pipe"
  - "addition"
  - "adj"
  - "lemmatization"
  - "nlp"
  - "nltk"
  - "sentiment analysis"
  - "stemming"
  - "tf-idf"
  - "tokenization"
  - "wordnet"
---

# Неделя 6: Обработка естественного языка (NLP) и анализ текстов

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** Библиотеки NLTK/Spacy, токенизация, лемматизация, стемминг, TF-IDF, анализ тональности и суммаризация статей

## Материалы ноутбука: Lecture 6.1 Libraries and toolkits for NLP (1).ipynb_

# **Lecture 6.1 Libraries and toolkits for NLP.**

## **1.1 NLP в Python**

Python offers several libraries that can be used for text analysis. Some of the most popular libraries include:

NLTK (Natural Language Toolkit)
TextBlob
spaCy
Gensim
TfidfVectorizer (from scikit-learn library)

```python
import nltk
```

```python
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
```

# **nltk.download('wordnet')**
# Purpose: Downloads the WordNet lexical database.
# What it is: WordNet is a large ontology of the English language where words are grouped into synsets (sets of synonyms). Each synset is connected to others through semantic relationships (hypernymy, hyponymy, antonymy, etc.).
# Applications:

# Word lemmatization (reducing words to their base form, e.g., cars → car, running → run).

# Synonym/antonym lookup.

# Semantic text analysis.

# **nltk.download('wordnet')**

# Назначение: Загружает лексическую базу данных WordNet.
# Что это: WordNet – это большая онтология английского языка, где слова объединены в синсеты (synsets) – группы синонимов. Каждый синсет связан с другими через семантические отношения (гиперонимия, гипонимия, антонимия и др.).
# Применение:
# Лемматизация слов (приведение к нормальной форме, например: cars → car, running → run).
# Поиск синонимов/антонимов.
# Семантический анализ текста.

```python
from nltk.corpus import wordnet

syns = wordnet.synsets("car")

for syn in syns:
    if syn.examples():
        print("Definition:", syn.definition())
        print("Examples:", syn.examples())
```

# **nltk.download('averaged_perceptron_tagger_eng')**
# Purpose: Downloads a pre-trained model for POS tagging (Part-of-Speech tagging).
# What it is: The Averaged Perceptron Tagger is a perceptron-based algorithm that automatically determines the part of speech of a word in a sentence (noun, verb, adjective, etc.).
# Applications:

# Morphological analysis of text.

# Data preparation for syntactic or semantic analysis.

# Improving lemmatization accuracy (e.g., “running” as a verb → run, but as a noun → running).

# **nltk.download('averaged_perceptron_tagger_eng')**

# Назначение: Загружает предобученную модель для POS-tagging (Part-of-Speech tagging – разметка частей речи).
# Что это: Модель Averaged Perceptron Tagger – алгоритм на основе перцептрона, который автоматически определяет часть речи слова в предложении (существительное, глагол, прилагательное и т.д.).
# Применение:
# Морфологический разбор текста.
# Подготовка данных для синтаксического или семантического анализа.
# Улучшение точности лемматизации (например, “running” как глагол → run, а как существительное → running).

```python
import nltk

text = nltk.word_tokenize("NLTK is a great library for text processing.")
pos_tags = nltk.pos_tag(text)
print(pos_tags)
# [('NLTK', 'NNP'), ('is', 'VBZ'), ('a', 'DT'), ('great', 'JJ'), ('library', 'NN'), ('for', 'IN'), ('text', 'NN'), ('processing', 'NN'), ('.', '.')]
```

# **nltk.download('stopwords')**
# Purpose: Downloads a list of stop words for various languages (including English, German, French, Russian, etc.).
# What it is: Stop words are frequently used words that do not carry significant semantic meaning (e.g., the, is, a, и, но, как).
# Applications:

# Text cleaning before analysis.

# Removing “noise” in word frequency analysis.

# Data preparation for training NLP and ML models.

# **nltk.download('stopwords')**

# Назначение: Загружает список стоп-слов для разных языков (в том числе английского, немецкого, французского, русского и др.).
# Что это: Стоп-слова – это частотные слова, не несущие существенной смысловой нагрузки (the, is, a, и, но, как).
# Применение:
# Очистка текста перед анализом.
# Удаление "шума" при анализе частотности слов.
# Подготовка данных для обучения моделей (NLP, ML).

```python
from nltk.corpus import stopwords

stop_words = set(stopwords.words('english'))
words = ["this", "is", "a", "sample", "sentence"]
filtered = [w for w in words if w.lower() not in stop_words]
print(filtered)  # ['sample', 'sentence']
```

```python
stop_words = set(stopwords.words('english'))
filtered = [w for w in text if w.lower() in stop_words]
print(filtered)
```

# **nltk.download('punkt')**
# Purpose: Downloads the pre-trained Punkt Tokenizer models.
# What it is: An algorithm used to split text into:

# sentences (sentence tokenization),

# words (word tokenization).
# Applications:

# Splitting text into tokens before analysis.

# Data preparation for POS tagging, lemmatization, frequency analysis, etc.

# **nltk.download('punkt')**
# Назначение: Загружает предобученные модели токенизации Punkt Tokenizer.
# Что это: Алгоритм для разбиения текста на:
#предложения (sentence tokenization),
# слова (word tokenization).
# Применение:
# Разделение текста на токены перед анализом.
# Подготовка данных для POS-tagging, лемматизации, частотного анализа и т.д.

```python
from nltk.tokenize import sent_tokenize, word_tokenize

text = "Hello world. NLTK makes text processing easy!"
print(sent_tokenize(text))  # ['Hello world.', 'NLTK makes text processing easy!']
print(word_tokenize(text))  # ['Hello', 'world', '.', 'NLTK', 'makes', 'text', 'processing', 'easy', '!']
```

# We need to prepare our textual data for analysis. This may include:

# 1. removing whitespace, punctuation, and numbers

# 2. converting the text to lowercase

# 3. removing stop words (e.g., “a”, “an”, “the”) — these are the most common words in any language. There is no strict definition of ignored words; you can think of them as words used to form meaningful sentences

# 4. tokenization — splitting a piece of text into tokens or words

# 5. lemmatization or stemming (reducing words to their base form)

Первым делом нам нужно подготовить наши текстовые данные для анализа. Это может включать в себя:

1. удаление пробелов, знаков препинания и чисел
2. приведение текста к нижнему регистру
3. удаление стоп-слов (например, «a», «an», «the») - это самые распространенные слова в любом языке. Нет правильного определения игнорируемых слов, вы можете думать об этих словах как о словах, которые используются для создания значимого предложения.
4. токенизация - разделение фрагмента текста на токены или слова.
5. лемматизация или стемминг (приведение слов к их основной форме)

## **1.2 Removing punctuation, whitespace, and numbers. / Удаление знаков препинания, пробелов и чисел.**
# Using the re (regular expressions) library. Regular expressions (Regex) are strings that define a search pattern for specific fragments in text. In addition to searching, special Regex patterns can be used to manipulate text fragments — to partially or completely remove or modify substrings.Regular expressions consist of a set of literals (letters and digits) and metacharacters.
# С помощью библиотеки регулярных выражений re. Регулярные выражения (Regex) – это строки, задающие шаблон для поиска определенных фрагментов в тексте. Помимо поиска, с помощью специальных Regex-шаблонов можно манипулировать текстовыми фрагментами – удалять и изменять подстроки частично или полностью.
# Регулярные выражения состоят из набора литералов (букв и цифр) и метасимволов.

```python
text = "Life, believe, is not a dream.\n So dark as sages say;\n Oft a little morning rain \n Foretells a pleasant day!"
print(text, end="\n\n")
text1=re.sub(r'[^\w\s]','',text)
# замена знаков, которые ^(не в диапазоне) \w(букв)+ \s(пробел), "" (пробелом)
# replace characters that are not in the allowed set: ^ (not in range), \w (letters), \s (whitespace), with "" (empty string) or a space
print('-'*40)
print(text1)
```

# Here, the re module (regular expressions) is used to replace characters in the string text that are not letters, digits, or whitespace.
# re.sub(): A function from the re module that replaces all matches found by a regular expression in a string with a specified character or string (in this case — an empty string '').
# r'[^\w\s]':
# r'': Raw strings are used in regular expressions so that characters such as the backslash are not interpreted as escape sequences.
# \w: Represents an alphanumeric character (letters and digits, as well as the underscore _).
# \s: Represents any whitespace character (spaces, tabs, line breaks).
# [^\w\s]: Square brackets [ ] define a set of characters, and the caret ^ inside the brackets means “not”, so this expression matches any characters that are not letters, digits, or whitespace.

# Здесь модуль re (регулярные выражения) используется для замены символов в строке text, которые не являются буквами, цифрами или пробелами.
# re.sub(): Функция из модуля re, которая заменяет все найденные регулярным выражением совпадения в строке на указанный символ или строку (в данном случае — пустая строка '').
# r'[^\w\s]':
# r'': Сырые строки (raw strings) используются для регулярных выражений, чтобы символы, такие как обратная косая черта \, не интерпретировались как специальные символы.
#\w: Обозначает буквенно-цифровой символ (буквы и цифры, а также знак подчеркивания _).
# \s: Обозначает любой пробельный символ (пробелы, табуляции, переводы строки).
# [^\w\s]: Квадратные скобки [ ] обозначают набор символов, а каретка ^ внутри скобок означает "не", то есть выражение ищет любые символы, которые не являются буквами, цифрами или пробелами.

```python
match = re.findall(r'sa', text, re.I) # находит все вхождения 'sa' в text
print(match)
```

```python
text2 = re.sub(r'sa', '*'*2, text, flags=re.I)
print(text2)
```

# **Использование цикла Python для удаления знаков препинания.**

# Сохраните все знаки препинания в строке.
# Создайте цикл for и создайте оператор if для каждой итерации так, чтобы при обнаружении символа пунктуации он заменялся пробелом.

```python
inp_str = "Hello? Folks, we are here to learn & improve!@!"

print("Original string:\n\n" + inp_str)
print()
marks = "!()-[]{};?@#$%:'\,./^&;*_"
opt_str = inp_str
for x in inp_str:
  for i in marks:
    if x == i:
        opt_str = opt_str.replace(x,"")
print('-'*40)
print("String after deletion of punctuation marks:\n\n", opt_str)
print(type(opt_str))


print('-'*40)
text2 = re.sub(r"[!()\[\]{};?@#$%:'\\,./^&;*_]", '', inp_str)
print(text2)
```

## **1.3 Stop word removal + tokenization./ Удаление стоп-слов + токенизация**

```python
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
```

```python
nltk.download('stopwords')  # Download stop words (if not previously loaded).

# Get the list of English stop words.
stop_words = set(stopwords.words('english')) #загружает список стоп-слов для английского языка.
print(stop_words)
```

```python
text = "Life, believe, is not a dream.\n So dark as sages say;\n Oft a little morning rain \n Foretells a pleasant day!"
print(text, end="\n\n")

print('-'*40)
sentences=sent_tokenize(text) # Sentence segmentation.
print(sentences)

print('-'*40)
tokens = word_tokenize(text) # Word tokenization.
tokenization = [word for word in tokens if not word in stopwords.words('english')] # удаление english стоп-слов
print(tokens, sep="\n")

print('-'*40)
print(tokenization, type(tokenization), sep="\n")
```

# \xa0 — this is a non-breaking space. It is used to prevent an automatic line break at the position where it appears. In this output, this character indicates the place where a non-breaking space was present in the original text.

# \n — this is a newline character. It is used to move to a new line. In text, this character typically separates lines and indicates the end of one line and the beginning of the next.

# \xa0 — это неразрывный пробел (non-breaking space). Он используется для предотвращения автоматического разрыва строки в том месте, где он находится. В данном выводе этот символ обозначает место, где в исходном тексте был неразрывный пробел.

# \n — это символ новой строки (newline). Он используется для перехода на новую строку. В тексте этот символ обычно разделяет строки и обозначает конец одной строки и начало следующей.

# Еще один вариант с переводом в нижний регистр, удалением все, что не является буквами и удалением стоп-слов.

```python
import nltk
from nltk.corpus import stopwords

text = "Life, believe, is not a dream.\n So dark as sages say;\n Oft a little morning rain \n Foretells a pleasant day!"
print(text, end="\n\n")
text = text.lower()
words = word_tokenize(text)
words = [word for word in words if word.isalpha()]
stop_words = set(stopwords.words('english')) # множество english стоп-слов
words = [word for word in words if word not in stop_words]
print(words, type(words), sep="\n")
```

```python
nltk.download('stopwords')

kazakh_stopwords = stopwords.words('kazakh')

print(kazakh_stopwords[:30])
print("Количество стоп-слов:", len(kazakh_stopwords))
```

## **1.4 Lemmatization./ Лемматизация**

```python
import nltk
from nltk.stem import WordNetLemmatizer

print(words)
lemmatizer = WordNetLemmatizer()
lemmatized_output = ' '.join([lemmatizer.lemmatize(w) for w in words]) # Лемматизировать список слов и соединить
print('-'*40)
print(lemmatized_output)
```

for w in words — последовательно перебираем каждое слово из списка words.

lemmatizer.lemmatize(w) — применяем лемматизацию к каждому слову.

[ ... ] — создаём новый список из лемматизированных слов (list comprehension).

' '.join(...) — объединяем полученные слова в одну строку, разделяя пробелами.

lemmatized_output = — сохраняем полученную строку в переменную.

# Note that there are errors. For example, “foretells” was not converted to “foretell” as expected. This can be fixed by providing the correct part-of-speech (POS) tag as the second argument to lemmatize().
# In NLTK, you can use the nltk.pos_tag() method for this. It accepts only a list (a list of words), even if you need to tag just a single word.
# Sometimes, the same word can have different lemmas depending on its meaning or context.

# Обратите внимание, что есть ошибки. Потому  что «foretells» не преобразовалось в «foretell», как ожидалось. Это можно исправить, если в качестве второго аргумента lemmatize() указать правильный тег «part-of-speech» (POS-тег).

# В nltk для этого есть метод nltk.pos_tag(). Он принимает только список (список слов), даже если нужно передать только одно слово.

# Иногда одно и то же слово может иметь несколько лемм в зависимости от значения / контекста.

```python
from nltk.tag import pos_tag

print(nltk.pos_tag(words))
```

# nltk.pos_tag() returns a tuple with the POS tag. The key point here is mapping
# the NLTK POS tags to the format required by the WordNet lemmatizer.
# WordNet is divided into four subsets, such as:

# *   Noun
# *   Verb
# *   Adjective
# *   Adverb

# nltk.pos_tag() возвращает кортеж с тегом POS. Ключевым моментом здесь является сопоставление POS-тегов NLTK с форматом, принятым лемматизатором wordnet.
# Wordnet, он разделен на четыре подсети, такие как

# *   Существительное
# *   Глагол
# *   Имя прилагательное
# *   Наречие

Объяснение POS-тегов:
В результате каждого слова присваивается POS-тег. Вот несколько наиболее распространённых тегов:

NN — существительное в единственном числе (noun, singular).

NNS — существительное во множественном числе (noun, plural).

NNP — собственное имя (proper noun, singular).

VB — глагол в начальной форме (verb, base form).

VBZ — глагол в форме третьего лица единственного числа (verb, 3rd person singular present).

VBG — причастие настоящего времени (verb, gerund/present participle).

JJ — прилагательное (adjective).

DT — определённый или неопределённый артикль (determiner).

IN — предлог или союз (preposition/subordinating conjunction).

TO — частица "to" перед инфинитивом (to).

```python
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import word_tokenize, pos_tag
from collections import defaultdict

tag_map = defaultdict(lambda : wn.NOUN)
tag_map['J'] = wn.ADJ
tag_map['V'] = wn.VERB
tag_map['R'] = wn.ADV

text="Yesterday he was in the most beautiful buildings on our streets."
text5=word_tokenize(text)
lemma_function = WordNetLemmatizer()

for w,tag in pos_tag(text5):

    lemmaWord = lemma_function.lemmatize(w,tag_map[tag[0]])
    #if w not in set(stopwords.words('english')):
    print(w, "=>", lemmaWord,"=>", tag)
```

Функция pos_tag() возвращает теги, например:
- JJ — adjective
- VBG — verb
- RB — adverb
- NNS — noun

А WordNetLemmatizer ожидает обозначения a, v, r, n.

# если POS-тег не начинается с J, V или R, используется категория существительного. Это удобное упрощение, но оно не обеспечивает корректную обработку всех грамматических категорий.

# **defaultdict** is a special type of dictionary in Python that automatically creates a default value for a missing key.
# In a regular dictionary, accessing a key that does not exist raises a KeyError. In a defaultdict, the value is automatically created using the specified function.

# **defaultdict** — это специальный тип словаря Python, который автоматически создаёт значение для отсутствующего ключа.
# В обычном словаре обращение к несуществующему ключу вызывает ошибку KeyError. В defaultdict значение создаётся автоматически с помощью указанной функции.Переведи на английский язык.

```python
from nltk.stem import PorterStemmer

ps = PorterStemmer()
words = ["program", "programs", "programmer", "programming", "programmers"]
for w in words:
  print(w, " : ", ps.stem(w))
```

# The **stemming** algorithm works by cutting off suffixes from a word. More broadly, it trims the beginning or the end of a word.

# **Lemmatization**, on the other hand, is a more powerful operation that takes into account the morphological analysis of words. It returns the lemma, which is the base form of all its inflected variants.

# Stemming is a general operation, whereas lemmatization is a more intelligent process in which the correct form appears as it would in a dictionary. Therefore, lemmatization helps in building better machine learning features.

# Алгоритм Stemming работает, вырезая суффикс из слова. В более широком смысле отсекает начало или конец слова.
#	Лемматизация, наоборот,  является более мощной операцией и учитывает морфологический анализ слов. Она возвращает лемму, которая является базовой формой всех ее флективных форм.
#	Стемминг – это общая операция, а лемматизация – интеллектуальная операция, в которой правильная форма будет выглядеть в словаре. Следовательно, лемматизация помогает в формировании лучших возможностей машинного обучения.

---

## Материалы ноутбука: Lecture_6_2_Automatic Summarization of Articles (1).ipynb

# **Lecture 6.2 Automatic Summarization of Articles**
# **Автоматическое реферирование или Суммаризация статей**

```python
import nltk
```

```python
import string
```

```python
import collections
```

```python
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('brown')
```

# Brown Corpus (Брауновский корпус) — один из наиболее известных текстовых корпусов английского языка, используемых в обработке естественного языка (NLP). Brown Corpus — это коллекция текстов американского английского языка, созданная в Брауновском университете (Brown University) в 1960-х годах.
Корпус содержит:
- Около 1 миллиона слов.
- 500 текстовых образцов.
- Тексты из 15 жанров, включая новости, художественную литературу, научные и другие тексты.
- Разметку частей речи (POS tagging).Переведи на английский.

# Brown Corpus is one of the most well-known English text corpora used in Natural Language Processing (NLP).
# The Brown Corpus is a collection of American English texts compiled at Brown University in the 1960s.

The corpus contains:
- Approximately 1 million words.
- 500 text samples.
- Texts from 15 different genres, including news, fiction, scientific writing, and other types of texts.
- Part-of-speech (POS) tagging, which identifies the grammatical categories of words.

```python
from nltk.tokenize.sonority_sequencing import punctuation
from nltk.lm import Vocabulary
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import word_tokenize, pos_tag, sent_tokenize
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.util import ngrams, bigrams
```

```python
from nltk.stem import WordNetLemmatizer

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

text_list=word_tokenize(text) # Split the text into words.

#Remove stop words.
stop_words=stopwords.words('english')
text_list=[word for word in text_list if word not in stop_words]

# Find the lemmas of the words and combine them into a text.
lemma_function = WordNetLemmatizer()
text1 = ' '.join([lemma_function.lemmatize(w, get_wordnet_pos(w)) for w in text_list])

text1=text1.lower() # Convert all words to lowercase.

text_sent=sent_tokenize(text1) # Split the text into sentences.

for p in string.punctuation: # Remove punctuation from the sentences.
    for i in range(len(text_sent)):
      if p in text_sent[i]:
        text_sent[i] = text_sent[i].replace(p, '') # Replace a character in a string.

preprocessed_text=' '.join(text_sent) # Preprocessed text.

print(text_sent)
print(preprocessed_text)
```

## **Lemmatization using different NLP packages.**
https://webdevblog.ru/podhody-lemmatizacii-s-primerami-v-python/

# print(fdist)	Выводит представление объекта FreqDist

# print(*fdist)	Выводит все уникальные слова, разделённые пробелами

# print(fdist.items())	Выводит пары «слово — частота»

# print(fdist.most_common())	Выводит слова и их частоты в порядке убывания

```python
from nltk import bigrams, word_tokenize
from nltk.lm.preprocessing import flatten, pad_both_ends

bigrams = __import__('nltk').bigrams
#Эта строка восстанавливает функцию bigrams из библиотеки NLTK,
#если ранее её имя было случайно переопределено, например списком.


padded_bigrams=[]
unigram =[]

for i in range(len(text_sent)):
    padded_bigrams.append(list(bigrams(pad_both_ends(word_tokenize(text_sent[i]), n=2))))
    text_word.append(word_tokenize(text_sent[i]))

unigram=list(flatten(pad_both_ends(sent, n=2) for sent in text_word))

print("Биграммы: \n", padded_bigrams)
print("Униграммы: \n", unigram)
```

```python
the_dict = {text: probability for text, probability in zip(sent_tokenize(text), sentences_probability)}
the_dict = sorted(the_dict.items(), key=lambda pair: pair[1], reverse=True)
for i in the_dict:
  print(i)
```

```python
for i in range(5):
  print(the_dict[i])
```

```python
for i,j in the_dict[:5]:
  print(i)
```

# **A short summary using the sumy library and the TextRank algorithm.**

## **Краткий реферат используя библиотеку sumy и алгоритм TextRank**

```python
import nltk
nltk.download('punkt_tab')
```

```python
with open('article2.txt', encoding='utf8') as file:
       text = file.read()

# Load Packages
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer


# For Strings
parser = PlaintextParser.from_string(text,Tokenizer("english"))

# Summarize using sumy TextRank
summarizer = TextRankSummarizer()
summary =summarizer(parser.document,2)
text_summary=""
for sentence in summary:
    text_summary+=str(sentence)
```

```python
text_summary
```

# **A short summary using the sumy library and the Luhn algorithm.**

## **Краткий реферат используя библиотеку sumy и алгоритм Луна**

```python
from sumy.summarizers.luhn import LuhnSummarizer

summarizer = LuhnSummarizer()
summary =summarizer(parser.document,2)

for sentence in summary:
  print(sentence)
```

# **A short summary using the sumy library and the LSA algorithm.**

## **Краткий реферат используя библиотеку sumy и алгоритм LSA**

---

## Материалы ноутбука: Lecture_6_3_Text_sentiment_1.ipynb

# Лекция 6.3. Анализ тональности текста

**Text sentiment analysis**

Цель: освоить словарные методы TextBlob и VADER, понять роль spaCy и построить обучаемый классификатор TF–IDF + SVM без утечки данных.

После занятия вы сможете объяснить полярность и субъективность, интерпретировать оценки VADER, сравнивать методы и оценивать классификатор на отложенных текстах.

**План:** 1. TextBlob. 2. VADER и spaCy. 3. VADER в NLTK. 4. TF–IDF + SVM. 5. Визуализация и анализ ошибок. 6. Русский и казахский языки. 7. Практические задания.

Пояснения, комментарии и интерфейс — на русском. Английские тексты сохранены как входные данные: стандартные словари TextBlob и VADER ориентированы на английский язык.

## Подготовка среды

Запускайте ячейки сверху вниз в Jupyter Notebook или Google Colab. Установка требует подключения к интернету. `%pip` устанавливает пакеты в среду текущего ядра; после первой установки иногда требуется перезапуск ядра.

Для показанного анализа `TextBlob.sentiment` не требуется загружать все корпуса TextBlob. Для VADER в NLTK нужен отдельный ресурс `vader_lexicon`; для spaCy используем `spacy.blank("en")` без загрузки языковой модели.

```python
import sys
from importlib.metadata import version
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

print("Python:", sys.version.split()[0])
for package in ["textblob", "vaderSentiment", "nltk", "spacy", "scikit-learn", "pandas", "matplotlib"]:
    print(f"{package}: {version(package)}")
```

## Что такое анализ тональности?

Это определение выраженной в тексте оценки: положительной, отрицательной или нейтральной. Он применяется к отзывам, сообщениям и обращениям пользователей.

- **Полярность** — направление оценки и её интенсивность.
- **Субъективность** — оценка того, насколько текст выражает мнение; это не вероятность ошибки или ложности.
- **Класс** — дискретная метка, полученная моделью или пороговым правилом.

Нейтральный итоговый балл может возникнуть и при смешении положительной и отрицательной оценок. Сарказм, предметная область и контекст затрудняют анализ. Тональность не равна конкретной эмоции, например страху или радости.

## §1. Анализ с помощью TextBlob

TextBlob предоставляет интерфейс к инструментам NLP. В этой лекции используем стандартный анализатор тональности английского текста.

`TextBlob(text).sentiment` возвращает:

| Поле | Диапазон | Значение |
|---|---|---|
| `polarity` | от −1 до 1 | Отрицательная или положительная оценка |
| `subjectivity` | от 0 до 1 | От более объективного к более субъективному высказыванию |

Баллы не являются калиброванными вероятностями классов. Для учебного преобразования полярности в три класса используем порог 0,01. Это наше правило, а не обязательный порог TextBlob.

```python
from textblob import TextBlob


def textblob_sentiment(text, threshold=0.01):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Передайте непустую строку.")
    if not 0 <= threshold <= 1:
        raise ValueError("Порог должен находиться в диапазоне [0, 1].")
    scores = TextBlob(text).sentiment
    label = ("Положительная" if scores.polarity > threshold else
             "Отрицательная" if scores.polarity < -threshold else "Нейтральная")
    return {"polarity": scores.polarity, "subjectivity": scores.subjectivity,
            "label": label}


example_text = "The service was excellent and the staff were friendly."
print("Текст:", example_text)
print(textblob_sentiment(example_text))
```

```python
examples = [
    "The service was excellent!",
    "The service was terrible.",
    "The meeting starts at ten.",
    "The food was good, but the service was terrible.",
    "Great, another three-hour delay.",
]
textblob_table = pd.DataFrame([
    {"text": text, **textblob_sentiment(text)} for text in examples
])
display(textblob_table.round(3))
```

## §2. VADER и роль spaCy

**VADER — Valence Aware Dictionary and sEntiment Reasoner**: словарь и правила для оценки тональности, разработанные прежде всего для англоязычных социальных сообщений. Метод учитывает отрицания, усилители, регистр и пунктуацию. Пакет `vaderSentiment` также обрабатывает ряд эмодзи; покрытие не универсально.

`polarity_scores(text)` возвращает:

| Поле | Интерпретация |
|---|---|
| `neg`, `neu`, `pos` | Нормированные доли отрицательного, нейтрального и положительного содержания по правилам VADER; сумма близка к 1 |
| `compound` | Сводный нормированный балл от −1 до 1 |

Это не вероятности принадлежности текста к классам. Стандартное пороговое правило VADER:
- `compound >= 0.05` — положительная тональность;
- `compound <= -0.05` — отрицательная;
- иначе — нейтральная.

**spaCy** выполняет NLP-обработку: токенизацию, сегментацию и, при наличии обученных компонентов, другие задачи. Загрузка `en_core_web_sm` сама по себе не добавляет классификатор тональности. Здесь тональность рассчитывает VADER, а spaCy выделяет предложения.

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as VaderAnalyzer

vader_analyzer = VaderAnalyzer()


def vader_label(compound):
    if compound >= 0.05:
        return "Положительная"
    if compound <= -0.05:
        return "Отрицательная"
    return "Нейтральная"


def vader_sentiment(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Передайте непустую строку.")
    scores = vader_analyzer.polarity_scores(text)
    return {**scores, "label": vader_label(scores["compound"])}


display(pd.DataFrame([
    {"text": text, **vader_sentiment(text)} for text in examples
]).round(3))
```

```python
intensity_examples = [
    "The service is good.",
    "The service is very good.",
    "The service is GOOD!!!",
    "The service is not good.",
    "The service is bad.",
    "The service is not bad.",
]
display(pd.DataFrame([
    {"text": text, **vader_sentiment(text)} for text in intensity_examples
]).round(3))
```

```python
import spacy

nlp_sentences = spacy.blank("en")
nlp_sentences.add_pipe("sentencizer")

review = "The food was excellent! The delivery was late. The package arrived today."
doc = nlp_sentences(review)
sentence_results = pd.DataFrame([
    {"sentence": sentence.text, **vader_sentiment(sentence.text)}
    for sentence in doc.sents
])
display(sentence_results.round(3))
print("Тональность всего отзыва:", vader_sentiment(review))
```

**Почему анализировать предложения отдельно?** Общий балл может скрывать различие между положительной оценкой еды и отрицательной оценкой доставки. Но анализ предложений ещё не является полноценным аспектным анализом: для него требуется связать оценку с конкретным объектом или свойством.

Не удаляйте отрицания, регистр, эмодзи и пунктуацию автоматически перед VADER: они могут нести информацию. Предобработка должна соответствовать выбранному методу.

## §3. VADER в NLTK

NLTK предоставляет ещё одну реализацию VADER. Это не принципиально другой метод: сравниваем реализации, а не независимые семейства алгоритмов. Версии словарей и обработка отдельных символов могут различаться.

Загрузка ресурса требует интернета при первом запуске. Если ресурс уже установлен, повторное скачивание не нужно.

```python
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer as NltkVaderAnalyzer

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    if not nltk.download("vader_lexicon", quiet=True):
        raise RuntimeError("Не удалось загрузить vader_lexicon. Проверьте интернет.")

nltk_vader_analyzer = NltkVaderAnalyzer()
implementation_comparison = pd.DataFrame([
    {
        "text": text,
        "vaderSentiment": vader_analyzer.polarity_scores(text)["compound"],
        "NLTK VADER": nltk_vader_analyzer.polarity_scores(text)["compound"],
    }
    for text in examples
])
display(implementation_comparison.round(3))
```

## §4. Обучаемый подход: TF–IDF + SVM

`TfidfVectorizer` преобразует тексты в числовые признаки, но самостоятельно не определяет тональность.

- **TF** описывает частоту термина в документе.
- **IDF** уменьшает относительный вклад терминов, встречающихся во многих документах.
- **SVM** обучается отделять классы по полученным векторам.
- **Биграммы** позволяют представить сочетания вроде `not good`, однако не гарантируют понимания отрицания.

Используем исходные **30 учебных предложений**: 15 положительных и 15 отрицательных. Нейтрального класса в этом наборе нет. Классификатор будет выбирать только между двумя классами.

Это маленький искусственный набор для демонстрации кода. По его метрикам нельзя делать выводы о качестве на реальных отзывах.

```python
data = [("I love this product, it's amazing!", 1), ("This is the best experience I've ever had!", 1), ("I'm very satisfied with the service.", 1), ('Everything was perfect, highly recommend.', 1), ('The food was delicious and the staff was friendly.', 1), ('Great atmosphere and excellent service.', 1), ('This was a fantastic movie!', 1), ('The book is absolutely incredible!', 1), ('I really enjoyed the vacation, it was relaxing and fun.', 1), ('The presentation was excellent and very informative.', 1), ('I had an awful experience.', 0), ("This is the worst product I've ever bought.", 0), ('I am extremely disappointed.', 0), ('The service was terrible and the staff was rude.', 0), ('The quality of the product is really poor.', 0), ('I will never come back to this place again.', 0), ('The food was cold and tasteless.', 0), ('I hated the experience, it was a waste of money.', 0), ('It was a boring and pointless movie.', 0), ('The product broke after one day of use.', 0), ('The website is too slow and difficult to navigate.', 0), ('The room was dirty and uncomfortable.', 0), ('The customer service was unresponsive and unhelpful.', 0), ("The packaging was damaged and the product didn't work.", 0), ('I am very unhappy with this purchase.', 0), ('The app is very user-friendly and intuitive.', 1), ('I am absolutely thrilled with the results!', 1), ('The staff went above and beyond to help.', 1), ('The product exceeded all my expectations.', 1), ('The design is elegant and the functionality is great.', 1)]

dataset = pd.DataFrame(data, columns=["text", "label"])
label_names = {0: "Отрицательная", 1: "Положительная"}
display(dataset.head())
print("Число текстов:", len(dataset))
print("Распределение классов:")
print(dataset["label"].map(label_names).value_counts())
print("Повторяющихся текстов:", dataset["text"].duplicated().sum())
```

### Разделение данных без утечки

Сначала делим **исходные тексты**: 80% на обучение и 20% на тест — 24 и 6 предложений.

`stratify` сохраняет доли классов. `random_state=42` фиксирует случайное разбиение, но не гарантирует репрезентативности.

**Ошибка:** обучать TF–IDF на всех текстах до разбиения. Тогда словарь и IDF зависят от тестовых данных.

**Решение:** `Pipeline` объединяет TF–IDF и SVM. При `fit` преобразование обучается только на обучающей части; при `predict` тестовые тексты преобразуются уже обученным векторизатором.

```python
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

X_train, X_test, y_train, y_test = train_test_split(
    dataset["text"], dataset["label"],
    test_size=0.2, random_state=42, stratify=dataset["label"]
)

sentiment_model = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
    ("svm", LinearSVC(random_state=42)),
])
sentiment_model.fit(X_train, y_train)
y_pred = sentiment_model.predict(X_test)
print("Обучающих примеров:", len(X_train))
print("Тестовых примеров:", len(X_test))
print("Признаков:", len(sentiment_model.named_steps["tfidf"].vocabulary_))
```

### Оценка качества

- **Accuracy** — доля правильных ответов среди всех примеров.
- **Precision** класса — доля верных ответов среди объектов, отнесённых к этому классу.
- **Recall** класса — доля найденных объектов класса среди всех его реальных объектов.
- **F1** — гармоническое среднее Precision и Recall.
- **Macro-F1** — среднее F1 по классам с одинаковым весом каждого класса.

На тесте из шести текстов одна ошибка меняет Accuracy примерно на 16,7 процентного пункта. Метрики нестабильны. `zero_division=0` задаёт вывод для неопределённой метрики, но не устраняет проблему отсутствия предсказаний класса.

```python
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.dummy import DummyClassifier

print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
print(f"Macro-F1: {f1_score(y_test, y_pred, average='macro', zero_division=0):.3f}")
print(classification_report(
    y_test, y_pred, labels=[0, 1],
    target_names=[label_names[0], label_names[1]], zero_division=0
))

# Простой ориентир: всегда предсказывать самый частый класс обучения.
dummy = DummyClassifier(strategy="most_frequent")
dummy.fit([[0]] * len(y_train), y_train)
dummy_predictions = dummy.predict([[0]] * len(y_test))
print(f"Accuracy простого ориентира: {accuracy_score(y_test, dummy_predictions):.3f}")
```

## §5. Визуализация и анализ ошибок

Матрица ошибок показывает, какие классы путает классификатор. Строки — реальные классы, столбцы — предсказанные. Диагональ содержит правильные ответы.

```python
from sklearn.metrics import ConfusionMatrixDisplay

fig, ax = plt.subplots(figsize=(6, 4))
ConfusionMatrixDisplay.from_predictions(
    y_test, y_pred, labels=[0, 1],
    display_labels=[label_names[0], label_names[1]],
    cmap="Blues", colorbar=False, ax=ax
)
ax.set_title("TF–IDF + SVM: матрица ошибок")
ax.set_xlabel("Предсказанный класс")
ax.set_ylabel("Реальный класс")
plt.tight_layout()
plt.show()

test_results = pd.DataFrame({
    "text": X_test.to_numpy(),
    "actual": y_test.to_numpy(),
    "predicted": y_pred,
})
test_results["correct"] = test_results["actual"] == test_results["predicted"]
display(test_results)
print("Ошибки:")
display(test_results.loc[~test_results["correct"]])
```

```python
new_texts = [
    "I enjoyed the friendly service and the delicious dinner.",
    "The delivery was late and the box was broken.",
    "The parcel arrived on Tuesday.",
]
new_predictions = sentiment_model.predict(new_texts)
display(pd.DataFrame({
    "text": new_texts,
    "prediction": [label_names[int(value)] for value in new_predictions],
}))
```

**Почему фактическое сообщение тоже получает положительную или отрицательную метку?** Модель обучалась только на двух классах. Добавление нейтрального класса требует соответствующих размеченных примеров и повторного обучения. Значение `decision_function` у SVM — не вероятность; для вероятностной интерпретации нужна отдельная процедура калибровки на достаточных данных.

Новые тексты выше не дублируют обучающие предложения. Проверка на фразе, уже присутствующей в обучении, не является независимой оценкой.

```python
comparison_rows = []
for text in examples:
    tb = textblob_sentiment(text)
    vd = vader_sentiment(text)
    svm_label = int(sentiment_model.predict([text])[0])
    comparison_rows.append({
        "text": text,
        "TextBlob": tb["label"],
        "TextBlob polarity": tb["polarity"],
        "VADER": vd["label"],
        "VADER compound": vd["compound"],
        "SVM (2 класса)": label_names[svm_label],
    })
comparison = pd.DataFrame(comparison_rows)
display(comparison.round(3))

fig, ax = plt.subplots(figsize=(9, 4))
comparison.set_index(pd.Index(range(1, len(comparison) + 1)))[
    ["TextBlob polarity", "VADER compound"]
].plot.bar(ax=ax)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_ylim(-1.05, 1.05)
ax.set_xlabel("Номер текста в таблице")
ax.set_ylabel("Баллы методов")
ax.set_title("Оценки тональности: различие шкал и правил")
ax.tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.show()
```

Баллы TextBlob и VADER рассчитаны по разным правилам: одинаковое значение не означает одинаковую уверенность. Таблица иллюстрирует расхождения, но не доказывает превосходство метода: для этого нужны эталонные метки и единый протокол.

### Дополнительно: кросс-валидация на обучающей части

`Pipeline` заново обучает TF–IDF внутри каждого разбиения. Тестовая часть остаётся отложенной. На 24 учебных текстах даже кросс-валидация не обеспечивает надёжной оценки для реальных данных.

```python
from sklearn.model_selection import StratifiedKFold, cross_val_score

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
cv_scores = cross_val_score(
    sentiment_model, X_train, y_train,
    cv=cv, scoring="f1_macro"
)
print("Macro-F1 по разбиениям:", cv_scores.round(3))
print(f"Среднее: {cv_scores.mean():.3f}; стандартное отклонение: {cv_scores.std():.3f}")
```

## §6. Русский и казахский языки

Стандартные англоязычные анализаторы TextBlob и VADER нельзя автоматически считать пригодными для русского или казахского текста. Нулевой балл может означать, что слова отсутствуют в словаре, а не нейтральность текста.

| Инструмент | Возможная роль | Что важно проверить |
|---|---|---|
| spaCy с русской моделью | Токенизация, морфология, синтаксический анализ | Наличие NLP-модели не означает наличие классификатора тональности |
| Stanza с ресурсами для казахского языка | Лингвистическая обработка в рамках доступных процессоров | Набор процессоров и ресурсов; тональность требует отдельной модели |
| TF–IDF + обучаемый классификатор | Базовая модель для размеченных текстов соответствующего языка | Разметка, размер корпуса, дисбаланс, отрицания и морфология |
| Многоязычный трансформер | Основа для дообучения на тональности | Поддержка языка, предметной области и проверка на независимом тесте |

Для казахского языка существенны словоизменение, аффиксация, варианты написания и смешение языков. Нужны данные именно на языке и из области применения.

Перевод текста на английский — отдельный экспериментальный вариант: он может менять оттенки, отрицания и иронию. Его качество необходимо проверять.

### Корректный план эксперимента
1. Собрать тексты и определить классы.
2. Подготовить инструкции разметчикам и проверить согласованность разметки.
3. Удалить дубликаты; исключить попадание близких текстов или одного автора в разные части, если это создаёт утечку.
4. Разделить данные до обучения преобразований; для временных данных рассмотреть временное разбиение.
5. Обучить базовую модель и сравниваемые методы на одинаковых частях.
6. Оценить Macro-F1, показатели по классам и матрицу ошибок.
7. Проверить отрицания, смешанные отзывы, сарказм и перенос в другую область.

---

## Слайды презентации: Лекция 6_NLP (1).pptx

### Lecture 6.  Introduction to NLP

### Слайд 2
- Lecture outline

### Слайд 3
- Обработка естественного языка NLP (natural language processing) – изучает проблемы взаимодействия компьютеров и естественных языков.
- Цель: повышение качества машинного анализа и синтеза сообщений на естественном языке.
- При этом под машинным анализом понимается способность компьютера получать смысл из входящих естественно-речевых сообщений, а под машинным синтезом – способность компьютера грамотно генерировать исходящие сообщения на естественном языке.

### Слайд 4

### Слайд 5
- Наиболее известные прикладные задачи машинного анализа текстов на естественном языке:

### Слайд 6
- Lecture 1: Introduction to NLP and Deep Learning (Video, Slides + Review)
- Lecture 2: Word Vector Representations - word2vec (Video, Slides + Readings)
- Lecture 3: GloVe - Global Vectors for Word Representation (Video, Slides + Readings)
- Lecture 4: Word Window Classification and Neural Networks (Video, Slides + Readings)
- Lecture 5: Backpropagation and Project Advice (Video, Slides + Readings)
- Lecture 6: Dependency Parsing (Video, Slides + Readings)


Таблица:
https://github.com/khanhnamle1994/natural-language-processing | Cерия лекций зимнего курса Стэнфордского университета 2019 года по обработке естественного языка с глубоким обучением | Английский | Бесплатно

### Слайд 7
- Lecture 7: Introduction to TensorFlow (Video, Slides + Readings)
- Lecture 8: Recurrent Neural Networks and Language Models (Video, Slides + Readings)
- Lecture 9: Machine translation and advanced recurrent LSTMs and GRUs (Video, Slides + Readings)
- Lecture 10: Neural Machine Translation and Models with Attention (Video, Slides + Readings)
- Lecture 11: Gated recurrent units and further topics in NMT (Video, Slides + Readings)
- Lecture 12: End-to-end models for Speech Processing (Video, Slides)
- Lecture 13: Convolutional Neural Networks (Video, Slides + Readings)
- Lecture 14: Tree Recursive Neural Networks and Constituency Parsing (Video, Slides + Readings)

### Слайд 8
- Lecture 15: Coreference Resolution (Video, Slides + Readings)
- Lecture 16: Dynamic Neural Networks for Question Answering (Video, Slides + Readings)
- Lecture 17: Issues in NLP and Possible Architectures for NLP (Video, Slides + Readings)
- Lecture 18: Tackling the Limits of Deep Learning for NLP (Video, Slides + Readings)
- Assignments
- Assignment 1 (Problem, Solutions, Folder)
- Assignment 2 (Problem, Solutions, Folder)
- Assignment 3 (Problem, Solutions, Folder)

### Слайд 9
- ТОП-10 книг по обработке естественного языка: от новичка до профессионала
- https://proglib.io/p/top-10-knig-po-obrabotke-estestvennogo-yazyka-ot-novichka-do-professionala-2021-03-24

### Слайд 10
- Программы разных курсов
- https://www.roschinsm.ru/courses/
- Методы векторизации текстов
- https://medium.com/@bigdataschool/4-%D0%BC%D0%B5%D1%82%D0%BE%D0%B4%D0%B0-%D0%B2%D0%B5%D0%BA%D1%82%D0%BE%D1%80%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D0%B8-%D1%82%D0%B5%D0%BA%D1%81%D1%82%D0%BE%D0%B2-f8ac90e4175a

### Морфологический анализMorphological analysis
- Морфологический анализ изучает формы и свойства слова

### Задачи морфологического анализа


Таблица:
ЛЕММАТИЗАЦИЯ | ГРАММАТИЧЕСКИЕ ХАРАКТЕРИСТИКИ | ГЕНЕРАЦИЯ
Процесс приведения словоформы к лемме — её нормальной (словарной) форме | Показывает от какого «родственника» и с помощью каких морфем образовалось слово | Постановка слов в заданную форму (падеж, время …)

### Задачи морфологического анализа


Таблица:
ЛЕММАТИЗАЦИЯ
В последнее время в городе происходит много интересных и захватывающих событий.


В последний время в город происходить много интересный и захватывать событие

### Задачи морфологического анализа


Таблица:
ГРАММАТИЧЕСКИЕ ХАРАКТЕРИСТИКИ
План, что и говорить, был превосходный: простой и ясный, лучше не придумать.

превосходный (какой?) — прилагательное;
начальная форма — превосходный;
постоянные признаки: качественное;
непостоянные: ед.ч., им.п., муж.р., полная форма;
часть составного сказуемого (был превосходный).

### Задачи морфологического анализа


Таблица:
ГРАММАТИЧЕСКИЕ ХАРАКТЕРИСТИКИ
В последнее время в городе происходит много интересных и захватывающих событий.

В|PR последний|A время|S в|PR город|S происходить|V много|ADV интересный|A и|CONJ захватывать|V событие|S

### Задачи морфологического анализа


Таблица:
ГЕНЕРАЦИЯ

### Стемминг. Алгоритм Портера
- Стеммер Портера — алгоритм стемминга (нахождения основы слова для заданного исходного слова), опубликованный Мартином Портером. Алгоритм не использует баз основ слов, а работает, последовательно применяя ряд правил отсечения окончаний и суффиксов.
- Стемминг — это выделение основы слова (не всегда совпадает с корнем).

### Слайд 18
- Токенизация
- Токенизация – это процесс разбиения фразы, предложения, абзаца или всего текстового документа на более мелкие единицы, например, отдельные слова или термины. Каждое из этих меньших подразделений называется токенами.

### Слайд 19
- Токенизация слов
- Метод word_tokenize ()

### Слайд 20
- Токенизация предложений
- Метод sent_tokenize()

### ЯЗЫКОВЫЕ МОДЕЛИ

### Языковые модели

### Языковые модели
- Учитывая, что языки могут использоваться для выражения огромного множества верных предложений (так называемая цифровая бесконечность), языковое моделирование сталкивается с проблемой задания ненулевых вероятностей лингвистически верным последовательностям, которые могут никогда не встретиться в обучающих данных. Для преодоления этой проблемы было разработано несколько подходов к моделированию, таких как применение марковских цепей или использование нейронных архитектур, таких как рекуррентные нейронные сети или трансформеры.

### N-грамма
- N-грамма — это просто последовательность из n элементов (звуков, слогов, слов или символов), идущих в каком-то тексте подряд. На практике чаще имеют в виду ряд слов (реже — символов). Последовательность из двух элементов называют биграмма, из трёх элементов — триграмма.
- Биграммы I want, want to, to go, go to, to the…
- Триграммы I want to, want to go, to go to...

### N-грамма

### N-грамма
- Целью построения N-граммных моделей является определение вероятности употребления заданной фразы. Эту вероятность можно задать формально как вероятность возникновения последовательности слов в некоем корпусе (наборе текстов).

### N-грамма
- В общем виде правило выглядит следующим образом:

### N-грамма
- Счастье вдохновляет людей изменять их жизнь к лучшему.
- P = P(счастье) * P(вдохновляет | счастье) * P(людей |счастье вдохновляет) * P(изменять | счастье вдохновляет людей) * P(их | счастье вдохновляет людей изменять) * P(жизнь | счастье вдохновляет людей изменять их) * P(к | счастье вдохновляет людей изменять их жизнь) * P(лучшему| счастье вдохновляет людей изменять их жизнь к)
- Чтобы определить P(счастье), нужно посчитать, сколько раз это слово встретилось в тексте, и поделить это значение на общее число слов.

### Слайд 29
- Рассчитать условную вероятность P(вдохновляет | счастье) несложно. Для этого считаем количество пар 'счастье вдохновляет', и делим на количество в тексте слова 'счастье’.
- Рассчитать вероятность P(лучшему| счастье вдохновляет людей изменять их жизнь к) сложнее.

### Слайд 30
- Чтобы упростить эту задачу, примем, что вероятность слова в тексте зависит только от предыдущего слова. Используем цепи Маркова, с помощью которых мы можем предсказать вероятность элемента последовательности, не учитывая слишком широкий контекст.
- Марковская модель первого порядка:
- Марковская модель второго порядка:

### Слайд 31
- В результате, если мы посчитаем все пары слов в некотором тексте, мы сможем вычислить вероятность произвольной фразы. Этот набор рассчитанных вероятностей и будет биграммной моделью.
- Тогда наша формула для расчета фразы примет следующий вид:

### Слайд 32
- P = P(вдохновляет | счастье) *
- *P(людей | вдохновляет) * P(изменять | людей) *
- *P(их | изменять) * P(жизнь | их) * P(к | жизнь) * *P(лучшему| к)
- Счастье вдохновляет людей изменять их жизнь к лучшему.

### Слайд 33
- Поэтому на практике используются логарифмы, при этом логарифм произведения равен сумме логарифмов, т.е.
- заменим на:

### Пример
- В саду были дети.
- Дети сорвали все ромашки.
- Сергей купил Кате ромашки.
- Ромашки завяли в саду.
- Катя не любит садовые ромашки.
- У Кати растут розы.
- Ромашки завяли у Кати.
- Постройте биграммную языковую модель на основе корпуса и вычислите вероятность предложения:
- Р(завяли | ромашки) =1/4
- Р(у | завяли) =1/1
- Р(Кати | у) =1/1
- Р =1/4

### Слайд 35
- Вероятности многих биграмм равны 0, что превращает в 0 вероятность любого предложения, содержащего эти биграммы.

### Сглаживание Лапласаоценка «+1»
- Добавляем к частотам всех биграмм +1. Тогда вероятности будем считать по формуле:
- где V ‒ это размер словаря.

### Слайд 37
- Частоты увеличены на 1,  вероятности  биграмм уже не будут 0, следовательно можно посчитать вероятность любого предложения, содержащего эти биграммы.

### Пример
- Ромашки завяли у Кати.
- Р=0,087*0,05*0,1=0,000435
- или
- ln(Р)=ln(0,087*0,05*0,1)= ‒7,74

### Информационный поиск

### Слайд 40
- Информационный поиск – поиск в большой коллекции документов, удовлетворяющей потребности пользователя, сформулированный в виде короткого запроса на естественном языке.

### Слайд 41
- Под релевантностью понимается соответствие смыслового содержания выданных документов информационному запросу.
- Документы, содержания которых отвечает запросу пользователя называются релевантными, а не отвечающие – нерелевантными.
- Соответствие содержания выданных документов к информационной потребности пользователя называется пертинентностью, а документы, содержания которых отвечают информационным потребностям пользователя называются пертинентными.

### Процесс индексирования
- Анализ структуры – выделение заголовков, абзацев и т.п.; удаление html-разметки и т.д;
- Токенизация – разбиение текста на слова, удаление знаков препинания;
- Удаление стоп-слов - высокочастотных служебных слов (предлогов, союзов и т.п.);
- Лемматизация – приведение слов к нормальной (например, словарной) форме;
- Взвешивание

### Взвешивание
- В индексе хочется учитывать не только сам факт вхождения слова в документ, но и «вес», т.е. информацию о частоте данного слова в документе.
- Однако саму по себе частоту использовать плохо, поскольку слова распределены в языке неравномерно: некоторые встречаются гораздо чаще других

### Слайд 44
- Классический метод взвешивания: tf-idf
- Показатель tf-idf оценивает значимость слова в документе, на основе данных о всей коллекции документов. Данная мера определяет вес слова за величину пропорциональную частоте его вхождения в документ и обратно пропорциональную частоте его вхождения во всех документах коллекции.
- tf - term frequency (частота слова),
- idf - inverse document frequency (обратная частота документа).

### Слайд 45
- Классический метод взвешивания: tf-idf
- tf – относительная частота слова в документе
- Показатель tf рассчитывается как отношение количества вхождений слова документ к количеству слов в документе.

### Слайд 46
- Классический метод взвешивания: tf-idf
- idf – обратная документальная частота (чем меньше в коллекции документов, в которые входит это слово, тем idf больше)
- Показатель idf равен логарифму отношения количества документов в коллекции к количеству документов в коллекции, в которых встречается заданное слово.
- Учет idf позволяет снизить вес слов, употребляемых часто (например, предлогов).

### Слайд 47
- Классический метод взвешивания: tf-idf
- Общий же показатель tf-idf является произведением tf и idf.
- Вес слова в документе:
- В современных поисковых системах используются более сложные варианты взвешивания.

### Слайд 48
- tf = 25 ÷ 10000 = 0,0025
- idf = lg(2000000 ÷ 2000) = lg(1000 ÷ 1) = 3
- (lg - логарифм с основанием 10)
- tf-idf = 0,0025 × 3 = 0,0075
- Расчет для тематического слова
- Документ состоит из 10000 слов в котором слово “садовник” встречается 25 раз, а коллекция состоит из 2 миллионов документов, в 2000 из которых также встречается данное слово.

### Слайд 49
- Расчет для союза
- Для второго примера расчета tf-idf возьмём тот же документ из 10000 слов в котором союз “но” встречается 30 раз, а коллекция по-прежнему состоит из 2 миллионов документов, в 200000 из которых также встречается данное слово.
- tf = 30 ÷ 10000 = 0,003
- idf = lg(2000000 ÷ 200000) = lg(10 ÷ 1) = 1
- (lg - логарифм с основанием 10)
- tf-idf = 0,003 × 1 = 0,003

### Слайд 50
- Сравнение расчетов
- Так как мы использовали идентичные документ и коллекцию, можем сравнить семантический вес слов:
- 0,0075 > 0,003,
- следовательно слово "садовник" имеет больше веса, чем союз "но", что справедливо.

### Слайд 51
- Стоит ли вообще работать с такой старой методикой оценки текстов?
- Алгоритм tf-idf является основой информационного поиска.
- Он уже давно интегрирован в формулу ранжирования Яндекс и Google, а теперь и лёг в основу более продвинутых алгоритмов вроде векторного анализа текста.

### Векторная модель

### Векторная модель
- Близость запроса к документу: косинусная мера близости

### Вероятностные модели
- Вероятность вычисляется на основе теоремы Байеса:
- P(R) – вероятность того, что случайно выбранный из коллекции документ D является релевантным
- P(d|R) – вероятность случайного выбора документа d из множества релевантных документов
- P(d) – вероятность случайного выбора документа d из коллекции D

### Оценка информационного поиска
- Оценка требует большой коллекции размеченных документов, т.е. огромного труда асессоров.


Таблица:
Релевантные | Нерелевантные
Найденные | TP | FP
Ненайденные | FN | TN

### Слайд 56
- Полнота поиска (recall) характеризует долю выданных ИПС релевантных документов по сравнению с количеством всех имеющихся релевантных документов в информационном (поисковом) массиве.
- Точность поиска (presicion) характеризует долю релевантных документов, действительно соответствующих запросу пользователя среди всех выданных ИПС документов.
- Другими словами можно сказать, что полнота – это способность ИПС найти и выдавать все релевантные документы, а точность – это способность ИПС задерживать, т.е. не выдавать нерелевантные документы.

### Слайд 57

### Слайд 58
- F-мера
- Понятно что чем выше точность и полнота, тем лучше. Но в реальной жизни максимальная точность и полнота не достижимы одновременно и приходится искать некий баланс. Поэтому, хотелось бы иметь некую метрику которая объединяла бы в себе информацию о точности и полноте нашего алгоритма.
- В этом случае нам будет проще принимать решение о том какую реализацию запускать в production (у кого больше тот и круче). Именно такой метрикой является F-мера.
- F-мера представляет собой гармоническое среднее между точностью и полнотой. Она стремится к нулю, если точность или полнота стремится к нулю.

### Слайд 59
- Данная формула придает одинаковый вес Precision-точности и Recall-полноте, поэтому F-мера будет падать одинаково при уменьшении и точности и полноты. Возможно рассчитать F-меру придав различный вес точности и полноте, если вы осознанно отдаете приоритет одной из этих метрик при разработке алгоритма.

### Слайд 60
- где α принимает значения в диапазоне 0< α <1, если вы хотите отдать приоритет точности,
- а при  α >1 приоритет отдается полноте.
- При  α =1 формула сводится к предыдущей и вы получаете сбалансированную F-меру (также ее называют F1).

### Пример
- Для примера расчёта F-score, предположим, что у нас есть модель классификации, и она классифицирует объекты как "положительные" или "отрицательные". Мы рассчитываем F-score на основе таких метрик, как Precision (точность) и Recall (полнота).

### Слайд 62
- Предположим, модель классификации дала следующие результаты:
- TP=40 (истинно положительные),
- FP=10 (ложно положительные),
- FN=5 (ложно отрицательные).


Таблица:
Релевантные | Нерелевантные
Найденные | TP | FP
Ненайденные | FN | TN

### Слайд 63
- Значение F-score в данном примере составляет 0.842, что указывает на хороший баланс между точностью и полнотой.

### Литература: К. Д. Маннинг, П. Рагхаван, Х. Шютце Введение в информационный поиск – Вильямс, 2011

### Автоматическое реферирование

### Слайд 66
- Один документ  текст, который необходимо сжать.
- Несколько документов − получение реферата на основе сразу нескольких текстов, объединённых одной темой или посвящённых одному событию, например, ряд новостных сообщений об одном и том же событии.
- На входе

### Слайд 67
- Например, на входе
- Написанная автором аннотация (abstract), выступающая как исходный текст, подлежащий дальнейшему сокращению, или полный текст.
- Литература, касающаяся биомедицинских исследований vs. EHR (electronic health record) – электронные записи медиков; критерий специфичный именно для сферы обработки медицинских текстов.

### Слайд 68
- На выходе
- Extract («квазиреферат») содержит предложения из исходного текста/текстов, отобранные по определённым критериям и расположенные по порядку, возможно с минимальными изменениями.
- В Extract варианте реферат собирается исключительно из предложений первичного документа.

### Слайд 69
- На выходе
- Аbstract (реферат) представляет собой новый текст, порождённый программой.
- В abstract варианте компьютерная программа может по своему усмотрению добавлять в реферат новые слова, заменять существующие, создавая текст, которого не было в первичном документе.

### Слайд 70
- На выходе
- Индикативный реферат (Indicative) доносит до пользователя только ключевые идеи исходного документа/документов (пользователь вынужден ознакомиться с содержанием источника, чтобы понять, о чём конкретно идёт в них речь).
- Информативный реферат (informative), в свою очередь, содержит всю необходимую информацию из источника в сжатом виде, поэтому пользователь может ограничиться прочтением реферата и не читать текст в оригинале.

### Слайд 71
- Методы  автоматического реферирования

### Слайд 72
- Статистические методы, в которых предложения ранжируются согласно формуле, присваивающей каждому предложению значение (score) на основании различных факторов, например, ключевых словосочетаний, ключевых слов, положения предложения в документе.
- Например, наличие определённых слов или фраз в предложении может говорить в пользу его включения в реферат, и тогда это повышает вес, другие же, напротив, могут уменьшать вес. В отличие от машинного обучения, подразумевается ручная работа с математическими формулами.

### Слайд 73
- Автоматическая обработка языка (NLP):
- компьютерные методы понимания естественного языка – от подсчёта слов до глубокого парсинга (разрешение омонимии, частеречная разметка).

### Слайд 74
- Подходы, основанные на графах. Эти подходы основаны на идее представления текста в виде графа. Предложения представляются вершинами графа, а связи между ними — взвешенными ребрами. С помощью различных алгоритмов каждой вершине графа, обозначающей определенное предложение текста, можно присвоить вес на основе весов ребер. Реферат формируется аналогично формированию реферата при статистическом подходе. Данные подходы широко используются на практике.
- Один из таких методов реализован в библиотеке gensim для Python.

### Слайд 75
- Машинное обучение: порождение рефератов моделью, обученной на большом корпусе размеченных данных.
- Гибридные подходы сочетают два или более метода, описанных выше.

### Слайд 76
- Оценка качества
- Специальный программный пакет для оценки качества работы системы под названием ROUGE (Recall-Oriented Understudy for Gisting Evaluation), разработанный в Южно-Калифорнийском университете.

### Слайд 77

### Слайд 78

### Слайд 79

### Слайд 80

### Слайд 81

### Слайд 82

### Слайд 83

### Слайд 84

### Слайд 85

### Слайд 86

### Автоматический анализ тональности

### Слайд 88
- Анализ тональности (сентимент-анализ) − это область компьютерной лингвистики, которая занимается изучением мнений и эмоций в текстовых документах.

### Зачем нужны системы автоматического анализа тональности?
- Социология: данные о религиозных взглядах населения;
- Политология: мониторинг политических взглядов населения;
- Маркетинг: анализ сообщений на предмет того, какая модель ноутбуков пользуется наибольшим спросом;
- Медицина  и  психология:  сентимент-анализ  может использоваться  для  определения депрессии у пользователей социальных сетей;
- Сфера финансов: анализ тональности финансовых отчётов и финансовых новостей для определения трендов на фондовом и валютных рынках;
- Поиск спама в отзывах;
- А также в журналистике, бизнесе, и т.д.

### Слайд 90
- Анализ тональности
- Мнение – это общая эмоция, суждение или оценка по поводу некоторого объекта описанного автором
- Классификация мнений – это задача определения общей оценки текста (документа, предложения и т.п.)
- Двоичная
- Троичная
- По некоторой шкале
- Большое количество приложений

### Задача анализа тональности
- Анализ тональности - выявление мнения автора текста по поводу предмета, обсуждаемого в тексте

### Слайд 92
- Классификация отзывов о фильмах
- Это какой-то ужас‾. В рецензии все описано так, что от фильма ждешь минимум продолжения фильма "Адреналина" с Стэтхэмом, но нет. 80 минут бесмысленных‾ бегов, туда-сюда. Единтсвенный вопрос - Зачем?!?!
- Я в диком восторге+!!!!
- Эта парочка неподражаема+!
- Так всё красиво+, аккуратно+, технично+, с долей юмора, и ТАК ЗАХВАТЫВАЮЩЩЩЩЩЩЕ динамично+!!!!
- В экстазе+)
- Хороший+, трешовый+ фильм, с отличным+ чувством юмора. Для любителей гая ритчи самое то, вот только картинка нищенская‾, но ничего страшного+. Это даже колорит+ какой-то придает.

### Жанры текстов относительно анализа тональности
- Отзывы: один автор – один объект (указанный в метаданных!!)
- Но могут быть сравнения: «книга была лучше», «в прошлый раз в ресторане было лучше»
- Множество работ по обработке отзывов
- Авторский текст (блоги): один автор – много объектов (еда, ресторан,  официант, интерьер)
- Новостные или аналитические тексты:
- Много упоминаемых субъектов (ситуация, политики, ответственные лица), которые могут иметь свои мнения по отношению к обсуждаемой теме
- Отношения упоминаемых субъектов между собой
- Мнения в разное время
- И плюс еще мнения автора
- Короткие или Длинные тексты

### Эксплицитные и имлицитные оценки
- Явные оценочные слова
- Хороший, гадкий, неприятный
- Оценочные факты, т.е. фактическая информация, которая подразумевает оценку
- В супе плавает муха
- Долго ждали
- И слова с коннотациями (=оценочными ассоциациями)
- Очереди
- Безработица  (в экономике)
- Муха (В ресторане)
- В отзыве о фильме: фамилии хороших актеров
- Проблема: оценочные факты – разнообразие выражения, высокая зависимость от предметной области

### Слайд 95
- Отзывы: разные типы лексики
- Друзья, давайте перестанем покорно принимать курицу с сухарями залитую майонезом за салат цезарь. Я заказала цезарь во "временах года" и опять как и во многих других ресторанах, мне принесли залитую майонезом кислятину под названием "салат цезарь с куриным филе" за 280 руб.
- Уважаемые повара, вам не стыдно??? Цезарь - это салат с особым соусом с  анчоусами ,очень вкусный. В вашем заведении - столовская кухня по ценам хорошего ресторана.

### Многозначность оценочной лексики
- Разная тональность многозначного слова в разных значениях
- Пресный (невкусный, неинтересный) или Пресная вода
- Тональность в зависимость от предметной области
- Смешной часто позитивно в области фильмов, и скорее негативно в политике
- Подлость, вероломство обычно не относятся к оценке фильмов, а к их содержанию
- Зависимость от контекста в одной предметной области
- Долго заряжается  или Долго не разряжается

### Модификаторы тональности
- Изменение тональности на противоположную: отрицания (не, нет), слишком, без
- Усиление тональности: очень
- Проблема: сфера действия
- Теперь я не знаю как буду без потрясающей еды в своём городе
- Жаль, что не спросили имя официантки, она была просто супер-мила

### Факторы нереального контекста (ирреалис)
- Ирреалис (ирреальное наклонение) – группа грамматических средств, которые показывают, что сообщаемое в предложении не относится к тому, что реально происходит (plungyan, 2005).
- - Я надеялась, что мне понравится
- - Если бы фильм был хорошим
- - Разве это хорошо кормить холодным?
- Эксперименты показывают, что оценочным словам, попавшим в такие контексты, нужно учитывать априорную оценку с понижением

### Сравнения
- Семантические сравнение, а не синтаксически выделяемый сравнительный оборот
- - Фильм замечательный, он получил множество наград. Но я бы не сказала, что он лучше более ранних работ на подобную тему. Мне, например, гораздо больше понравился фильм 2004 года «именины» - режиссера валерия наумова. А в восторг привел фильм еще более раннего выпуска 2001 года с очень плохим названием «механическая сюита» режиссера дмитрия месхиева.
- - Зимой довольно часто посещала это место и была в восторге, все было на высоте — атмосфера дружеская, обслуживание супер... Была на выходных, и разочаровалась.

### Ирония и сарказм
- Ирония – это высказывание, буквальное содержание которого не соответствует реальному содержанию.
- Сарказм – более резкая, агрессивная форма высказывания, чем ирония.
- Обычно по словам выглядит положительным, а на самом деле отрицательно
- В сбербанке живая очередь опять победила электронную
- Сбербанк - самая крупная сеть неработающих банкоматов
- My car window just asked me if I want to upgrade to windows 10.
- When you get back from vacation fired up for new music releases but your computer is still on vacation. Thanks windows 10!        Us so much!

### Подзадачи анализа тональности
- Классификация целого документа
- Классификация отдельного предложения
- Автоматическая генерация аннотаций
- Вопросно-ответные системы
- Тональность по конкретным объектам
- Тональность по конкретным атрибутам (аспектам)
- Выделение конкретных атрибутов
- Выделение мнений по атрибутам
- Классификация мнений по конкретному атрибуту
- Позиция по вопросу (stance detection)

### Оценка качества
- Сравнение с оценками людей (золотой стандарт)
- Точность-полнота-f-мера
- Если у нас три класс: позитивный, негативный и нейтральный, то может считаться средняя мера по позитивному и негативному классам
- Accuracy (аккуратность – правильность классификации)
- Отношение правильно классифицированных текстов ко всем текстам

### Слайд 103
- ‹#›

### Точность, полнота, F-мера
- Значение F-score в данном примере составляет 0. 27, что указывает на слабый баланс между точностью и полнотой.

### Анализ тональности целого текста (текстового фрагмента)

### Слайд 106
- Подходы к анализу тональности
- ЛИНГВИСТИКО-ИНЖЕНЕРНЫЕ ПОДХОДЫ
- Словари (жалко, скучный, мало повидавший)
- Правила (не очень скучный)
- Проблемы: трудно все зафиксировать
- ПОДХОДЫ, ОСНОВАННЫЕ НА МАШИННОМ ОБУЧЕНИИ
- Ручная разметка сообщений (+, -, 0)
- Выделение признаков сообщений
- Слова, знаки препинания, смайлики, и др.
- Математические методы нахождения закономерностей
- Нейронные сети, деревья решений, метод опорных векторов
- Проблемы: нужна ручная разметка,
- Размеченная выборка недостаточной величины

### Предварительная обработка
- Эти программы могут также осуществлять следующую обработку текстов:
- Лемматизацию - процесс приведения слов к нормальным (словарным) формам
- "Такой интересной книги я давно не читала" =>
- =>"такой интересный книга я давно не читать"
- Стемминг - избавление от суффиксов и окончаний:
- «малюсенький экран»));
- Удаление стоп-слов - тех, которые часто встречаются, но практически не несут никакой эмоциональной нагрузки:
- - Предлоги (в, на, под);
- - некоторые местоимения (притяжательные: его,    мой);
- - Некоторые наречия (туда);   И др.

### Предварительная обработка
- Приведение к нижнему регистру (в некоторых случаях также теряется эмоциональный акцент):
- «Приобретение данного товара было ОШИБКОЙ» =>
- => «приобретение данного товара было ошибкой»
- Морфологическая разметка (в текстовый корпус вставляются метаданные для обозначения частей речи и др.);
- и т.д.

### Выделение сущностей
- При сентимент-анализе необходимо выделять следующие составляющие:
- 1) субъект тональности ‒ источник мнения, тот, кто является, автором     сообщения;
- 2) объект тональности ‒ то, о чём идёт речь в тексте (фильм, модель ноутбука);
- 3) аспект тональности ‒ характеристика объекта (например, для фильма это может быть: игра актёров, спецэффекты, сюжет, музыкальный ряд и т.д.);
- 4) тональная оценка ‒ тип мнения, отношение автора к отдельному аспекту или к объекту в целом.

### Классификация при сентимент-анализе
- Текст: позитивный / негативный
- Комментарий:
- Грустный
- Радостный
- Злой
- Отзыв:
- Положительный
- Нейтральный
- Отрицательный

### Подходы к автоматическому анализу тональности
- Основные подходы к автоматическому определению тональности текста можно разделить на 2 большие группы:
- Лингвистические алгоритмы, основанные на правилах, шаблонах и словарях;
- Алгоритмы, использующие методы машинного обучения.
- Многие коммерческие системы используют первый подход как наиболее точный.

### Словари оценочной лексики
- Словарь оценочной лексики – база данных, где хранятся слова и n‑компонентные цепочки – n-граммы (например, фразеологизмы и различные устойчивые словосочетания («задеть за живое», «с гулькин нос»), при этом каждой такой единице присвоен уровень эмоциональной оценки.
- Словари:
- - Используют различные шкалы оценок;
- - С автоматическим пополнением списков и без.

### Виды словарей
- Словам может быть приписана лишь одна тональная оценка – числовое значение полярности (число большее нуля – позитивный сентимент, число меньшее нуля – негативный сентимент).
- ‹#›
- Пример для английского языка: AFINN
- В некоторых других системах (к примеру, SentiStrength) группы слов получают не одну, а две тональные оценки (положительную и отрицательную).


Таблица:
Слово/
словосочетание | Уровень эмоциональной оценки
отвратительный | -5
с гулькин нос | -2
модный | +3
усталый | -2

### Виды словарей
- Существуют лексиконы, в которых словам приписываются разные эмоциональные категории, к ним относится NRC word-emotion association lexicon. Каждому слову здесь сопоставляются 2 тональные оценки и 8 эмоций: «гнев», «страх», «предчувствие», «вера», «удивление», «грусть», «отвращение», «радость». Списки данного словаря были переведены на несколько десятков языков, среди которых есть и русский.


Таблица:
Слово | Эмоциональная или тональная оценка | Значение
(1 – присутствие;
 0 – отсутствие)
откровенный | гнев | 0
страх | 0
предчувствие | 0
вера | 1
удивление | 0
грусть | 0
отвращение | 0
радость | 0
положительная | 1
отрицательная | 0

### Виды словарей
- В тезаурусе wordnet-affect наряду с метками, указывающими эмоциональную категорию («гнев», «страх», «удивление», «печаль», «отвращение», «радость»), и валентностями (позитивная, негативная, неоднозначная, нейтральная) словарным единицам – синсетам, синонимическим рядам – были сопоставлены метки, описывающие эмоции: «физическое состояние», «настроение», «поведение», «отношение», «чувство» и др. Данный тезаурус был переведен с английского языка на русский и румынский.

### Лексический подход
- Шаблоны: <им. Прил.  Им. Сущ.>, <Им. Прил.  Им. Прил.>
- По шаблонам из текста извлекаются n-граммы. Их тональность определяется как при помощи словаря, так и посредством правил.
- Тональность всего текста складывается из тональности предложений, а тональность предложений — из тональности слов. Для получения итоговой окраски общую сумму весов нужно подсчитать по формуле, которую составляют разработчики конкретного решения, универсальной формулы не существует. Можно, к примеру, просто просуммировать полярности цепочек документа.

### Примеры правил при лингвистическом подходе
- 1. Правила, построенные по модели «если… то…».
- Если цепочка содержит глагол из списка («любить», «нравиться», 	«обожать» и др.) И не содержит глагола из другого списка 	(«ужасать», «отвращать» и др.) Или отрицания, то её 	тональность положительная.
- 2. Правила, обрабатывающие слова с их модификаторами.
- Модификаторы:
- - Усиливающие («очень», «более») исходную тональность;
- - Снижающие («слишком», «менее») исходную тональность;
- - Преобразующие в обратную («не», «нет») исходную тональность.
- Модификаторам тональности приписываются некоторые коэффициенты, которые рассматриваются как множители относительно априорной полярности соответствующего оценочного слова.

### Примеры правил при лингвистическом подходе
- 3. Правила обработки слов с коннотациями.
- Коннотации — это оценочные ассоциации, связанные со словами. Появление в тексте слов с положительными или отрицательными коннотациями коррелирует с соответствующими оценками, выражаемыми в тексте. Так, в отзывах о фильмах словами с положительными коннотациями обычно являются имена известных актеров. В отзывах о ресторанах на русском языке отрицательными коннотациями обладают такие слова, как «майонез» и «клеенка». Если эти слова появляются в отзыве, обычно в этом месте выражается негативная оценка.
- «Вместо нормальных скатертей какие-то клеёнки…»
- «В салатах, которые на принесли, было столько майонеза!»

### Особенности UGC (user-generated content) текстов
- Особенности языка социальных медиа:
- Эмотиконы и смайлики;
- Опечатки;
- Неологизмы («пичалька» - опечатка или нет?);
- Окказионализмы – индивидуально-авторские неологизмы;
- Эмоционально окрашенные аббревиатуры («omg!..» );
- И много другое.

### Лингвистический подход
- ‹#›

### Общие проблемы сентимент-анализа
- У любой системы автоматического анализа тональности на данный момент остаются такие проблемы, как:
- Обработка саркастических и ироничных отрывков;
- «Было скучно. Давно не смотрела фильмов с настолько интригующим сюжетом»
- Обработка метафор пользователя;
- «Школа как второй дом»
- Сложности, возникающие, когда в отзыве содержится оценка сразу нескольких объектов, иногда конкурирующих;
- «Huawei впервые обогнала apple по продажам смартфонов в Казахстане»
- и др.

### Спасибо за внимание!
- ‹#›