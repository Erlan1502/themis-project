---
week_number: 1
topic_id: "week_01_tools_python"
title: "Неделя 1: Инструменты программирования для ИИ и структуры данных"
topic_name: "Основы языка Python, интроспекция, числовые типы, множества (set) и словари (dict)"
initial_prompt: "Привет! На первой лекции мы разобрали фундаментальные структуры данных Python. Почему для быстрого поиска элементов в AI-пайплайнах используют множества (set) и хеш-таблицы словарей (dict), а не стандартные списки (list), и какова временная сложность поиска в них?"
source_files:
  - "Lecture_1_2025.ipynb"
  - "Lecture_1_2_Числовые_данные.ipynb"
  - "Lecture_1_3_Множества и словари.ipynb"
glossary:
  - "a1eni3b5"
  - "abc"
  - "abcde"
  - "ability"
  - "about"
  - "access"
  - "accessed"
  - "ada-26"
  - "add"
  - "additional"
  - "after"
  - "again"
  - "dict"
  - "hash table"
  - "introspection"
  - "o(1)"
  - "python"
  - "set"
  - "time complexity"
  - "tuple"
---

# Неделя 1: Инструменты программирования для ИИ и структуры данных

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** Основы языка Python, интроспекция, числовые типы, множества (set) и словари (dict)

## Материалы ноутбука: Lecture_1_2025.ipynb

# **Python Fundaments and Data Structures in Python**

# **§1. Data Types \ Типы данных**

[Иллюстрация к лекции]

# ***Introspection in Python \ Интроспекция в Python***
# Интроспекция — это способность объекта во время выполнения получить тип, доступные атрибуты и методы, а также другую информацию, необходимую для выполнения дополнительных операций с объектом.

# Часто используемой функцией интроспекции является функция type(). Как видно из названия, эта функция возвращает тип объекта, который может быть примитивным типом данных, объектом, классом или модулем.

#Introspection is the ability of an object at runtime to obtain information about its type, available attributes and methods, as well as other information required to perform additional operations with the object.

#A commonly used introspection function is type(). As its name suggests, this function returns the type of an object, which may be a primitive data type, an object, a class, or a module.

```python
name = "Hello, world!"
print(type(name))  # <--- здесь мы узнаём тип объекта строки
```

```python
type([1, 2, 3])
```

```python
type(1.2) == int
```

# **§2. String. String Operations \ Cтроки. Операции со строками**

# Текстовые строки являются одним из основных объектов. Литерал строки в Python может ограничиваться апострофами, кавычками, а в некоторых случаях даже тремя апострофами или тремя кавычками — и это не меняет тип объекта. Внутри апострофов знак кавычки является просто символом, а внутри кавычек апостроф теряет свой синтаксический смысл. Например, "I'm a student." удобнее написать в кавычках, а 'Я зарегистрировался в системе "Истина"' в апострофах. Если внутри литерала в кавычках нужно записать кавычку или в апострофах апостроф, то его можно экранировать обратной косой чертой (back slash): "Фильм \"Д'Артаньян и три мушкетёра\".".

```python
print("I'm a student.")
print('I registered in "Teams"')
print("The film \"D'Artagnan and the Three Musketeers\"")
```

# Строки можно складывать. Такое сложение строк называется конкатенация, т.к. одна строка приклеивается к другой (кстати, в таком сложении a + b не равно b + a).

# Строки можно также "умножать", но не друг на друга, а на число. "Умножать строки друг на друга" "нельзя"

# Strings can be concatenated. This operation is called concatenation, because one string is joined to another. Note that, in this case, a + b is not equal to b + a.

# Strings can also be "multiplied", but not by each other — only by a number. Strings cannot be multiplied by other strings.

```python
a = 'Student'
b = 'ADA-26'
print(a + b)
print(b + a)
```

```python
"Student ADA-26!" * 3
```

```python
"Strings cannot be multiplied by each other" * "Strings"
```

# **Strings in Python are immutable. \ Строки в Python неизменяемы.**

# Строка является объектом. Это значит, что у неё есть методы. Методы — это функции, которые привязаны к конкретному объекту и вызываются через точку:

#A string is an object. This means that it has methods. Methods are functions associated with a specific object and are called using dot notation:

```python
s = "Hello, student ADA-26!"
s
```

```python
s.lower() #conversion to lowercase
```

```python
s.upper() #conversion to uppercase
```

```python
s.title() #all words in the string start with a capital letter
```

```python
s.replace('e', 'A') #the letter e is replaced with A
```

**текст жирним шрифтом**# **String Slicing \ Срезы строк**
# Для получения отдельных символов строки используется индексация, а для извлечения части строки — срезы.

# Individual characters in a string can be accessed using indexing, while parts of a string can be extracted using slicing.

```python
s = "characterization"
s[1]
```

```python
s = "characterization"
s[1:5]
```

```python
s[4:] + s[:4]
```

```python
s[1:11:2] #Every second character is selected from the 1st to the 10th character of the original string.
```

# **§3. Iterable Objects (Tuple, List) \ Итерируемые объекты (tuple, list)**

# Итерируемый объект (iterable) - это объект, который способен возвращать элементы по одному. Кроме того, это объект, из которого можно получить итератор.

# Примеры итерируемых объектов:

# все последовательности: список, строка, кортеж

# словари

# файлы

# An iterable object is an object that can return its elements one at a time. It is also an object from which an iterator can be obtained.
# Examples of iterable objects:
# sequences: lists, strings, tuples
# dictionaries
# files

# **§3.1 Tuple**

# Кортежи в Python представляют собой простую структуру данных для группировки произвольных объектов. Кортежи являются неизменяемыми — они не могут быть изменены после их создания.

# Tuples in Python are a simple data structure used to group arbitrary objects. Tuples are immutable — they cannot be changed after they are created.

```python
x, y, z = 1, 2, 3
print(x, y, z)
```

```python
A = 1, 2, 4
x, y, z = A
print(x, y, z)
print(A, type(A))
print(z)
```

# В *кортеж имён* можно присваивать не только *кортеж значений*, но и любой другой *итерируемый объект*, например, строку:

# A tuple of variable names can be assigned not only a tuple of values, but also any other iterable object, for example, a string:

```python
a, b, c, d, e = "HELLO"
print(a, b, c, d, e)
```

# Здесь произошло разворачивание или распаковка итерируемого объекта, причём это произошло без цикла for!

# Если длины кортежей не совпадут, будет ошибка:

# If the tuple lengths do not match, an error will occur.

```python
a, b, c = "HELLO"
```

```python
a, b, c, d, *rest = "Goodby, my dear friend!"
print(a, b, c, d)
print(rest)
print(type(rest))
```

```python
*rest, a, b, c = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print(a, b, c)
print(rest)
```

```python
a, b, *rest, c = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print(a, b, c)
print(rest)
```

```python
for a, b, c in "ABC", "KLM", "123":
  print(a, b, c, sep = '\t')
```

# **§3.2 List.**

# Список является динамическим, тогда как кортеж имеет статические характеристики. Это означает, что списки могут быть изменены, тогда как кортежи не могут быть изменены, кортеж быстрее списка из-за статичности по своей природе. Списки обозначаются квадратными скобками, а кортежи обозначаются скобками.

# A list is dynamic, whereas a tuple has static characteristics. This means that lists can be modified, while tuples cannot be changed after creation. Tuples are generally faster than lists due to their immutable nature.

# Lists are enclosed in square brackets [], while tuples are enclosed in parentheses ().

# **Важные различия между List и Tuple в Python**

[Иллюстрация к лекции]

# Создать список можно двумя способами — перечислением объектов в квадратных скобках через запятую или *через конструктор*:

# A list can be created in two ways — by listing objects separated by commas inside square brackets, or using the constructor:

```python
a = ['1', '2', '3', '4', '5'] #listing objects separated by commas inside square brackets
b = list('12345') # using the constructor
print(a, b)
print(a == b)  # checks whether the values are equal (сравнение содержимого).
print(a is b)  # checks whether the variables refer to the same object (same object in memory).
```

```python
s = ' '.join(a) #To combine or join elements back into a single string, the join() method is used.
print(type(s))
s
```

```python
s = '***'.join(a)
s
```

```python
s = "Early to bed, early to rise, makes a man healthy, wealthy, and wise.!"
a = s.split() # splitting a string by spaces
print(a)
print(type(a))
```

```python
print(s.split(', '))
```

# **Срезы списка**

```python
text = """Любовь долготерпит, милосердствует, любовь не завидует,
          любовь не превозносится, не гордится, не бесчинствует, не ищет своего,
          не раздражается, не мыслит зла, не радуется неправде, а сорадуется истине;
          все покрывает, всему верит, всего надеется, все переносит."""
words = text.split()  #  разбиваем строку text по пробелам на отдельные слова
text
```

```python
print(words)  # в итоге получается список из слов строки
```

```python
words[0:9] #в полученный список попадают элементы исходного списка с 0-го по 8-ой (9-ый элемент не попадает)
```

```python
words[7:20:2] #выбираются элементы с 7-го по 19-ый с шагом 2, то есть через один
```

```python
words[6: 19: -2]
```

```python
words[::-1]
```

# Обратите внимание, что списки, как и строки, можно склеивать при помощи +. Операция работает как конкатенация. Результатом операции является новый список.

Note that lists, like strings, can be joined using the + operator. This operation works as concatenation. The result is a new list.

```python
['a', 'b', 'c'] + ['d', 'e']
```

```python
['a', 'b', 'c'] * 3
```

```python
['a', 'b', 'c'] * ['d', 'e']
```

# Строку, если она содержит много строк (т.е. содержит символы "новой строки" "\n") можно разбить на строки.

```python
text = """Любовь долготерпит, милосердствует, любовь завидует,
          любовь не превозносится, не гордится, не бесчинствует, не ищет своего,
          не раздражается, не мыслит зла, не радуется неправде, а сорадуется истине;
          все покрывает, всему верит, всего надеется, все переносит."""
lines = text.splitlines()
lines
```

# Обратите внимание на пробелы в начале строк. Раздражают, не так ли? Конечно, у строки есть метод strip(), но как применить его ко всем строкам в списке?

# s.strip(chars) - удаляет символы chars в начале и конце строки. По умолчанию (s.strip()) удаляются пробелы.

```python
stripped_lines = [line.strip() for line in lines]
stripped_lines
```

# **§3.3 Потоковая обработка списков**

# Генераторы списков используются если  у вас уже есть список или итерируемый объект, и вы хотите создать другой на его основе, применив какую-то операцию.В новый список можно взять не все строки, а отфильтровать их по какому-то признаку. Например, так:

```python
filtered_lines = [line for line in stripped_lines if 'любовь' in line] # в новый список выбираем только те строки, в которых есть слово "любовь"
filtered_lines
```

# Можно одновременно фильтровать элементы списка и применять вычисление к каждому из отобранных.

```python
changed_and_filtered1 = [line.lower() for line in stripped_lines if 'не' in line]
# в новый список выбираем только те строки, в которых есть слово "не",
# и применяем ко всем строкам метод lower, который "превращает" все буквы в строчные
changed_and_filtered1
```

# Для последовательного поэлементного доступа к любому итерируемуму объекту (включая список!) можно использовать обычный цикл for:

For sequential element-by-element access to any iterable object, including a list, you can use a standard for loop:

```python
for line in changed_and_filtered1:
    print(line)
```

# Хотя в данном случае можно добиться того же эффекта — вывести все обработанные строки — развернув их в параметры print:

```python
print(*changed_and_filtered1, sep='\n', end='\n')
```

# **§4. Функция map**

## map() — встроенная функция высшего порядка для преобразования элементов итерируемых объектов (списков, кортежей, генераторов и т.п.) с помощью переданной функции.

# map(function, iterable, *iterables) -> map

# function: вызываемый объект (функция, lambda, метод и т.д.), принимающий столько аргументов, сколько передано итерируемых.
# iterable, *iterables: один или несколько итерируемых источников данных.
# Возвращает ленивый итератор (map-объект). Для получения коллекции оберните в list(), tuple(), set() и т.п.

```python
nums = [1, 2, 3, 4]
squared_iter = map(lambda x: x * x, nums)   # ленивый итератор
squared = list(squared_iter)
print(squared)
```

# lambda — это способ создать анонимную функцию (функцию без имени) «на лету».
# Используется, когда нужно коротко описать простое действие и не хочется писать полноценный def.

lambda is a way to create an anonymous function — a function without a name — on the fly.

It is used when you need to briefly describe a simple operation and do not want to define a full function using def.

```python
double=lambda x: x*2
print (double(10))
```

```python
def double (x):
  return x*2
print (double(10))
```

# **Ключевые свойства (точно и кратко)**

# Ленивость: вычисления выполняются «по требованию». Удобно для больших данных и потоков.

# Одноразовость: пройдя по map-итератору, вы его «исчерпаете».

# Порядок сохраняется: элементы обрабатываются слева направо.

# Несколько итерируемых: чтение идёт до кратчайшего из них.

Когда map() уместен, а когда лучше list comprehension

✅ Уместен:

когда уже есть готовая функция и нужно применить её к потоку данных;

когда важна память (ленивость) или компоновка с другими итераторами;

при множественных итерируемых (аналог «векторизации» по двум+ входам).

✅/🤏 Сравнимо:

простая трансформация: map(f, xs) ≈ [f(x) for x in xs].

🤏 Лучше list/dict/set comprehension, если:

нужна фильтрация и/или сложная логика на месте;

читаемость критична (часто comprehension понятнее для Python-разработчиков).

```python
filtered = filter(lambda s: 'не' in s, stripped_lines)
changed_and_filtered2 = map(lambda s: s.upper(), filtered)

for line in changed_and_filtered2:
    print(line)
```

```python
a = "Astana"
b = map(lambda char: chr(ord(char) + 1), a)
print('once:', *b)
print('again:',*b)
```

```python
a = "Astana"
c = [chr(ord(char) + 1) for char in a]
print('once:', *c)
print('again:', *c)
```

```python
print(type(b), type(c))
```

# Оказывается b — это вообще не список, а какой-то неизведанный итерируемый объект. Увы, эту "карту" мы уже исчерпали, больше она ничего не вернёт, так как обрабатывать ей больше нечего.

# Польза от таких спец.объектов огромная — их можно выстраивать в последовательную обработку очень длинных последовательностей, и они будут работать в режиме конвейера Генри Форда. Или даже системы завода Тойота, где необходимый продукт выполняется только по запросу и никогда не про запас. Это сохраняет ресурсы вашего компьютера.

# **§5. Функция zip**
# zip — молния-застёжка. Работает над итериремыми объектами одинаковой длины, "смыкая" их элементы в кортежи. Её очень удобно применять вместе с распаковкой параметров в заголовке цила for:

```python
a = "Алексей Руслан Тимур".split()
b = "Алёна Рита Тая".split()
for x, y in zip(a, b):
    print(x, '+', y, '= \u2665')
```

```python
for x in zip(a, b):
    print(x)
```

```python
for number, student in enumerate(["Маша", "Вася", "Петя", "Рома", "Макар"]):
    print(number, student)
```

```python
print(*enumerate("Нумерация"))
```

# **§6. Библиотека itertools**
# Для продвинутой работы с итерируемыми объектами есть стандартная библиотека itertools. Чтобы её использовать, необходимо один раз в программе подключить её. Например, так:

```python
import itertools as it
```

# Кобинации, перестановки, декартово произведение.

```python
for x, y, z in it.permutations("ABC"):
    print(x, y, z, sep='', end='\t')
```

```python
for x, y, z in it.permutations("ABCDE", 3):
    print(x, y, z, sep='', end='\t')
```

```python
for x, y in it.combinations("ABCDE", 2):
    print(x, y, sep='', end='\t')
```

```python
for x, y in it.combinations_with_replacement("ABCDE", 2):
    print(x, y, sep='', end='\t')
```

```python
for n, s in it.product([1, 2, 3, 4], "ABC"):
    print(n, s)
```

# Если нужно две или больше последовательностей связать в единую последовательность, как бы "в цепочку", поможет chain:

```python
for a in it.chain("первое", "слово", "дороже", "второго"):
    print(a, end=' ')
```

---

## Материалы ноутбука: Lecture_1_2_Числовые_данные.ipynb

# **Лекция 1.2. Числовые данные.**

```python
from google.colab import drive
drive.mount('/content/drive')
```

# **§1. Представление числовых данных в памяти компьютера**
Компьютеры, которыми мы пользуемся, построены на основе *цифровой логики*.
В этой системе информация представляет из себя простейшие цифровые сигналы `0` и `1`.
Объём информации такой элементарной ячейки называется *битом*.

Любая информация, которую мы хотим хранить или обрабатывать при помощи компьютера, должна быть представлена (*закодирована*) в *двоичном виде*.

Минимальный удобный для хранения в оперативной памяти компьютера квант информации составляет 8 бит. Такое количество информации получило свое название — *байт*.
Если у 1 бита всего 2 состояния, то, исходя из комбинаторики, у байта 256 состояний. Этого мало, чтобы сохранить все возможные числа (тем более, что в математике их бесконечное число), но для начала зададимся хотя бы этим: как назначить коды числам от 0 до 255.

[Иллюстрация к лекции]

# **§2. Системы счисления**
*Двоичная система счисления.*
Самый простой и естественный путь — воспользоваться двоичной системой счисления с лидирующими *незначащими нулями*:
```
00000000 = 0
00000001 = 1
00000010 = 2
00000011 = 3
00000100 = 4
00000101 = 5
00000110 = 6
00000111 = 7
...      = ...
11111111 = 255
```

[Иллюстрация к лекции]

В Python *для целых чисел* реализована **длинная арифметика**, что позволяет создавать очень большие числа. Важно только понимать, что *даже один такой объект числа может занимать очень много оперативной памяти компьютера*. Зато можно не волноваться про переполнения. Этот тип объекта называется `int`.

```python
0b11111111 + 5 #перевод из двоичной системы счисления в десятичную
```

```python
0o76 # перевод из восьмиричной системы счисления в десятичную: 7*8+6
```

```python
0xF3 # перевод из шестнадцатиричной системы счисления в десятичную: 15(F)*16+3
```

Для того, чтобы создать целое число `int` в Python, нужно просто записать цифрами его литерал, либо запустить *конструктор int*, который умеет делать число из строки:

```python
x = 123456789
print(x, type(x))
```

```python
x = int("12345")
print(x, type(x))
```

# **§3. Дробные числа**

Когда нужно хранить дробные числа, возникает много вопросов. Дело в том, что даже натуральных чисел бесконечно много, а дробных чисел много *континуально*. Их так много, что их нельзя пересчитать даже за бесконечное время. Они бесконечно плотно покрывают окрестность любой точки числовой прямой.

Главных вопроса два:
1. как мы вообще сможем записать значение числа;
2. сможем ли мы это закодировать конечным количеством бит.

Но в любом случае бесконечное многообразие сменится хоть и очень большим, но дискретным набором чисел.

Древние греки знали только рациональные числа — *обыкновенные дроби*. Их можно представить как целый числитель и натуральный знаменатель. В Python для работы с ними есть библиотека **fractions** и класс объектов `Fraction`:

```python
from fractions import Fraction
a = Fraction(5, 27)
b = Fraction(91, 11)
print(a, '+', b, '=', a + b)
print(a, '-', b, '=', a - b)
print(a, '*', b, '=', a * b)
print(a, '/', b, '=', a / b, "<--- для математической красоты не хватает скобочек")
print('(', a, ')','/', '(', b,')', '=', a / b)
```

Точность хранения числителя и знаменателя теоретически не ограничена, т.к. они имеют длинный тип `int`, но на практике всё опять упирается в память компьютера.

Из школы мы также знаем *десятичные дроби*. Они представлены библиотекой **decimal** и классом объектов `Decimal`:

```python
from decimal import Decimal
a = Decimal('12.3456786777')
b = Decimal('0.9876')
print(a, '+', b, '=', a + b)
print(a, '-', b, '=', a - b)
print(a, '*', b, '=', a * b)
print(a, '/', b, '=', a / b)
```

Данные объекты активно используются в банковских расчётах, поскольку хорошо воспроизводят вычисления, которые делают люди вручную с десятичными дробями.

Однако для научных вычислений чаще используются *дроби с плавающей точкой* (по-русски — запятой), то есть с мантиссой и экспонентой. По внутреннему хранению они двоичные, но при вводе-выводе для удобства всегда представлены в десятичном виде. Для их использования не нужно подключать библиотек, а представлены они классом объектов `float`.

Числа `float` появляются автоматически, когда целые числа `int` делят друг на друга или возводят в отрицательную степень:

```python
x = 2 ** -1
print(x, type(x))
```

```python
x = 2 / 5
print(x, type(x))
```

Даже если числа делятся друг на друга нацело, результат будет всё равно `float`:

```python
x = 10 / 5
print(x, type(x))
```

Создать такое число можно также из строки при помощи конструктора:

```python
x = float(input("Введите число с плавающей точкой: "))
print(x, type(x))
```

# **§4. Обмен переменных значениями**

Классический обмен переменных значениями через доолнительную переменную:

```python
a = 7
b = 12
print(a, b)
# -------
tmp = a
a = b
b = tmp
# -------
print(a, b)
```

Но в Python это можно сделать так:

```python
a = 7
b = 12
print(a, b)
# -------
a, b = b, a
# -------
print(a, b)
```

# **§5. Подсчёт ситуаций**
Довольно часто значение переменной меняется по своему собственному старому значению.

Для пары подобных изменений есть свои названия. Увеличение на 1 — это *инкрементация*. Уменьшение на 1 — *декрементация*.

```python
x = y = 10
print(x, y)
x = x + 1
y = y - 1
print(x, y)
```

Обратите внимание на выражение `x = x + 1`. Здесь икс в выражении справа ссылается на старый объект, который имеет старое значение. Затем вычисляется выражение, и появляется новый объект числа. Затем иксу присваивается (с именем `x` связывается) ссылка на новый объект.

```python
x += 1  # так красивее, понятнее и удобнее, а смысл тот же — инкрементация
y -= 1  # красивая декрементация
print(x, y, sep="\n")
```

Инкрементацию используют для подсчёта ситуаций. Сколько раз встретится такая строка: `x += 1`, тому и будет равно значение "переменной" `x`.

## Cуммирование чисел
Если нужно просуммировать некоторое количество чисел, то нужно создать переменную-аккумулятор, например, `s`, и в начале положить её равной нулю. После этого накапливаем туда сумму оператором `+=`:

```python
s = 0

x = 4
s += x

x = 6
s += x

x = 15
s += x

print(s)
```

В цикле это делать удобнее:

```python
s = 0
for x in 4, 6, 15:
    s += x
print(s)
```

А ещё можно складывать числа, поступающие с клавиатуры:

1.   Новый пункт
2.   Новый пункт

Отлично! Однако указывать сколько раз вводятся числа с клавиатуры через запятую неудобно. Узнаем как для этого использовать `range` в следующем разделе.

# **§6. Цикл while и арифметические расчёты**
Кроме цикла `for` есть цикл `while`. Он выполняет действия в теле цикла до тех пор, пока условие входа в цикл (оно написано в заголовке после слова while) не окажется ложным.

Типичный цикл while:

```python
x = 0
while x < 100:
    print(x)
    x += 10
print("действие после цикла")
```

[Иллюстрация к лекции]

Иногда он может зациклиться навсегда (подумайте, прежде чем запускать):

```python
x = 1
while x > 0:
    print(x)
    x += 1
print("Никогда...")
```

Или не выполнить ни одной итерации, если условие сразу оказалось ложным:

```python
x = 0
while x > 0:
    print(x)
    x += 1
```

## 6.1 Арифметическая прогрессия
Давайте сделаем арифметическую прогрессию:

```python
(start, stop, step) = (10, 50, 5)

x = start
while x < stop:
    print(x)
    x += step
```

Обратите внимание, что число stop не вошло в прогрессию. Это очень похоже на срезы строк и списков.

Поскольку генерация арифметической прогрессии — типичная задача, в Python есть готовый генератор прогрессий `range(start, stop, step)`, который работает по принципам экономных итерируемых объектов.

```python
for x in range(10, 50, 5):
    print(x)
```

```python
print(*range(0, 10))
```

```python
print(*range(9, -1, -1))  # наоборот
```

## 6.2 Геометрическая прогрессия
Зато мы можем теперь сделать геометрическую прогрессию:

```python
(start, stop, step) = (1, 100, 2)

x = start
while x < stop:
    print(x)
    x *= step
```

Обратите внимание на операцию `x *= step`. Это то же, что `x = x * step`. Так можно поступать и с другими арифметическими операциями.

# **§7. Ветвление хода исполнения программы**
До сих пор наши программы представляли из себя *последовательности действий*, возможно с зацикливаниями.
В таких алгоритмах нет вариативности поведения, не хватает возможности выбора действий, то есть *ветвления*.

Самый простой вариант — это *действие, выполняемое условно*. Оно может произойти, а может и нет:

```python
x = int(input("Какое сегодня число? "))
if x < 1 or x > 32:
    print('Такого не может быть!')
```

Второй вариант — это *ветвление с альтернативой*:

```python
x = int(input("Сколько вам лет? "))
if x < 18:
    print(f'Вам нельзя смотреть этот фильм! Приходите через {18-x} лет.')
    # f-строки делают очень простую вещь — они берут значения переменных,
    # которые есть в текущей области видимости, и подставляют их в строку.
    # В самой строке вам лишь нужно указать имя этой переменной
    # в фигурных скобках
else:
    print('Фильм загружается. Ждите...')
```

[Иллюстрация к лекции]

## 7.1 Вложенные условные конструкции
Как и циклы, условные конструкции можно вкладывать друг в друга. Для этого дополнительно увеличивается отступ.
Рассмотрим пример: Определить четверть, в которую попадает заданная точка.
![5678](data:application/octet-stream;base64,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)

```python
x, y = input("Введите координаты точки — два числа через пробел: ").split()
x, y = int(x), int(y)
if y > 0:
    if x > 0:
        print('Точка в I четверти.')
    else:
        print('Точка во II четверти.')
else:
    if x < 0:
        print('Точка в III четверти.')
    else:
        print('Точка в IV четверти.')
```

Замечательно! Из четырёх `print` будет всегда выбираться и срабатывать только один.

Но кое-что всё-таки не так с этой конструкцией. Мы предполагаем, что точка вообще находится в какой-то четверти, а она может быть и на осях. Поэкспериментируйте с точками (0, 0), (0, 10), (0, -10), (1, 0), (-1, 0). Сделайте вывод о том, нужно ли тестировать программное обеспечение.

## 7.2 Каскадная конструкция if, elif, else
Реализуем тоже самое действие при помощи каскадного ветвления:

```python
x, y = input("Введите координаты точки — два числа через пробел: ").split()
x, y = int(x), int(y)
if y > 0 and x > 0:
    print('Точка в I четверти.')
else:
    if y > 0 and x < 0:
        print('Точка во II четверти.')
    else:
        if y < 0 and x < 0:
            print('Точка в III четверти.')
        else:
            if y < 0 and x > 0:
                print('Точка в IV четверти.')
            else:
                print('Точка не в четвертях: на осях или в центре координат.')
```

**NB!** Обратите внимание на логический оператор И = `and`. Ещё есть логическое ИЛИ = `or` и логическое НЕ = `not`. Их используют для составных условий в циклах while и ветвлениях.

Продолжим. Конструкция напоминает водопад, по которому мы скатываемся до тех пор, пока хотя бы какое-то условие не окажется истинным. Если же всё было ложно, мы "скатываемся" по последней альтернативе — последнему else.

Всё здесь хорошо, но отступы всё время увеличиваются. Чтобы избежать этого, в Python ввели *синтаксический сахар* — `elif`:

```python
x, y = input("Введите координаты точки — два числа через пробел: ").split()
x, y = int(x), int(y)
if y > 0 and x > 0:
    print('Точка в I четверти.')
elif y > 0 and x < 0:
    print('Точка во II четверти.')
elif y < 0 and x < 0:
    print('Точка в III четверти.')
elif y < 0 and x > 0:
    print('Точка в IV четверти.')
else:
    print('Точка не в четвертях: на осях или в центре координат.')
```

[Иллюстрация к лекции]

---

## Материалы ноутбука: Lecture_1_3_Множества и словари.ipynb

# **Лекция 1.3. Множества и словари**

## **§1. Тип set. Множества и работа с ними**
**Множество** --- это контейнер, в котором порядок элементов не сохраняется и даже может изменяться, но многие операции происходят очень быстро и естественно.

Создать множество можно при помощи перечисления значений через запятую в фигурных скобках:

```python
the_set = {2, 3, 5, 7, 11, 13, 17, 19, 7, 5}
print(the_set, type(the_set), len(the_set))
```

Или при помощи конструктора set:

```python
the_set = set(range(10, 100, 10))
print(the_set, type(the_set), len(the_set))
```

Как и в математике, в Python есть пустое множество:

```python
the_set = set()
print(the_set, type(the_set), len(the_set))
```

Элемент не может входить в множество дважды или более. Любое значение либо входит в множество, либо не входит в него. В результате, в отличие от списка, все значения в множестве уникальны:

```python
the_list = [5, 7, 8, 6, 9,1, 2, 3, 4, 8, 7, 6, 5, 4, 3, 2, 1, 5, 2, 20, 10, 5, 15, 50]
the_set = set(the_list)
print(the_set)
```

Множества в Python отражают математический концепт множества, однако применяют их не только математики. Например, биологи всё время работают с *множествами животных и растений*.

### **1.1 Простая задача для биолога**

Итак, у биолога есть файл  `plants.txt` с названиями растений --- каждое в новой строке. Однако, много строк в файле повторяются. Биолог хочет узнать сколько в этой базе уникальных названий растений.

```python
with open('plants.txt', encoding='utf8') as file:
    plants = set(line.strip() for line in file) #line.strip вернет копию строки  с удаленными начальными и конечными символами chars. Другими словами, обрежет строку str с обоих концов.
    print(plants, len(plants))
```

В примере выше можно увидеть, что названия растений идут в каком-то странном порядке --- не по алфавиту (лексикографически) и не в оригинальном порядке их добавления в множество. Увы, это то, чем приходится расплачиваться за *скорость поиска в множестве*.

### **1.2 Множество — итерируемый объект**
Элементы множества можно перебирать циклом for, его можно распаковывать или отдавать в функции конвейерной обработки.

```python
i=1
for plant in plants:
    print("Растение",i,":", plant)
    i+=1
```

```python
print(*plants, sep='; ')
print(type(plants), type(plant))
```

Напечатать с большой буквы растения, у которых последняя буква "а":

```python
print(*map(lambda plant: plant.title(), filter(lambda plant: plant[-1] == 'а', plants)))
```

### **1.3 Принадлежность множеству**
В математике для указания того, что элемент принадлежит множеству есть нотация $x \in A$, что не принадлежит: $y \notin A$

Для проверки, принадлежит элемент множеству или нет, есть две операции: `in` и `not in`.

Результат их логический --- правда или ложь, а значит их можно использовать в циклах `while` и ветвлениях `if`:

```python
plants.add("сосна")
x=input("Введите поиск:")
if x.lower() in plants:
    print(f"{x} есть в этом множестве растений!")
elif x not in plants:
    print("Этого растения в множестве нет...")
else:
    print("Третьего не дано. Этот print никогда не случится.")
```

### **1.4 Сравнение множеств**
В математике множество, все элементы которого содержатся в другом множестве, называется подмножеством, вложенным в это множество.
В Python для проверки отношения вложенности между множествами есть оператор сравнения <=.

[Иллюстрация к лекции]

```python
plants = {"береза", "липа", "дуб", "клен","сосна","ромашка", "роза", "мак", "ландыш"}
tree_plants = {"береза", "липа", "дуб", "клен","сосна"}
flowers = {"ромашка", "роза", "мак", "ландыш", "липа"}

if flowers <= plants:
    print("Все цветы являются растениями.")
if plants >= tree_plants:
    print("Все деревья являются растениями.")
```

Множества, в которых все элементы совпадают, называются эквивалентными множествами. При этом порядок не важен, так как порядка в множестве как бы и нет. Для сравнения на эквивалентность используются операторы "равно" == и "не равно" !=.

```python
if tree_plants == flowers:
    print("'Деревья' и 'цветы' означают один и тот же набор растений.")
if tree_plants != flowers:
    print("'Деревья' и 'цветы' не совпадают по набору растений.")
```

Также есть операторы > и <, которые означают вложенность без эквивалентности:

```python
if plants > tree_plants:
    print("Все деревья являются растениями. При этом растений больше, чем деревьев.")
```

Рассмотрим такой пример:

```python
if flowers > tree_plants:
    print('Цветы - строгое надмножество деревьев.')
elif flowers < tree_plants:
    print('Цветы - строгое подмножество деревьев.')
elif flowers == tree_plants:
    print('Цветы и деревья - эквивалентные множества.')
else:
    print("Казалось бы, такого не может быть...")
```

Разве может быть, что один объект не больше, не меньше и не равен другому?
С числами, строками и многими другими элементами так просто не может быть... А с множествами может!

Для множеств в Python  нет отношения порядка, и *сортировать список множеств бесполезно*.

### **1.5 Опенации над множестами**

**Пересечение множеств**
Множество элементов, которые находятся хотя бы в одном из двух множеств, в математике называется объединением множеств.
Множество элементов, которые одновременно находятся в первом и втором множествах, в математике называется *пересечением множеств*. В Python операция *пересечение множеств* реализована при помощи метода `intersection`, но также можно пользоваться оператором `&`:

[Иллюстрация к лекции]

```python
flowers.intersection(tree_plants)
```

Или:

```python
flowers & tree_plants
```

**Объединение множеств**
Множество элементов, которые находятся хотя бы в одном из двух множеств, в математике называется объединением множеств.
В Python операция объединение множеств реализована при помощи метода union, но также можно пользоваться оператором |:

[Иллюстрация к лекции]

```python
flowers.union(tree_plants)
```

Или:

```python
flowers | tree_plants
```

**Разность множеств**
Также есть возможность вычитать множества, понимая под этим множество элементов первого множества, которые не являются при этом элементами второго множества.
Операции объединения и пересечения симметричны, т.е. не важно какое множество слева, а какое справа. В случае разности множеств это принципиально важно:

[Иллюстрация к лекции]

```python
flowers - tree_plants
```

```python
flowers.difference(tree_plants)
```

```python
tree_plants - flowers
```

```python
tree_plants.difference(flowers)
```

В математике есть ещё одна интересная операция с двумя множествами — **симметрическая разность**. По сути это объединение двух множеств за исключением их пересечения. Ещё раз: из объединения исключаются те элементы, которые принадлежат сразу двум множествам. В Python эта операция вызывается методом множества symmetric_difference или оператором ^:

[Иллюстрация к лекции]

```python
flowers.symmetric_difference(tree_plants)
```

```python
flowers ^ tree_plants
```

### **1.6 Set comprehensions: генерация множеств**
Так же, как и списки, множества можно генерировать на основании итерируемых объектов.

```python
inverted_plants_names = {name[::-1] for name in plants}
print(inverted_plants_names)
```

**Добавление** элементов в множество и удаление их из него

Надо заметить, что все вышеперечисленные операции не изменяют старые, а создают новое множество.

Тем не менее, в Python множество --- это изменяемый объект. В него можно добавлять элементы и удалять их, причём делать это как с одним значением, так и с целым набором

```python
my_garden = {"липа", "береза", "роза", "ромашка", "ландыш"}
print(id(my_garden), my_garden)
my_garden.add('лаванда')
print(id(my_garden), my_garden)
```

```python
my_garden = {"липа", "береза", "роза", "ромашка", "ландыш"}
print(id(my_garden), my_garden)
some_new_plants = ["вишня", "яблоня", "смородина", "роза"]
my_garden.update(some_new_plants)
print(id(my_garden), my_garden)
```

Обратите внимание ещё раз, что "роза" не вошла в множество второй раз. Вообще добавление в множество уже имеющегося там элемента не приводит к ошибке, но и множество при этом не меняется. Учтите это.

**Удаление элементов**
Удаление remove происходит с генерацией ошибки, если удаляемого элемента в множестве нет, и удалять нечего:

```python
my_garden = {"липа", "береза", "роза", "ромашка", "ландыш"}
print(my_garden)
my_garden.remove("береза")
print(my_garden)
my_garden.remove("береза") # <--- тут произойдёт ошибка
print(my_garden)
```

А также молчаливое discard:

```python
my_garden = {"липа", "береза", "роза", "ромашка", "ландыш"}
print(my_garden)
my_garden.discard("береза")
print(my_garden)
my_garden.discard("береза") # <--- тут не произойдёт ошибка
print(my_garden)
```

# **§2. Тип dict. Словарь и операции с ним**
**Словарь** похож на множество тем, что хранение в нём не упорядочено, а поиск происходит насколько возможно быстро. Однако хранятся в нём не элементы, а *пары (ключ, значение)*.

Создаётся словарь как и множество --- перечислением в фигурных скобках `{}`, но не элементов, а пар через знак `:`.

```python
the_dict = {"Казахстан": "Астана","Украина": "Киев","Китай": "Пекин"}
print(type(the_dict))
print(the_dict)
```

Можно использовать конструктор dict, и дать ему итерируемый объект с парами (ключ, значение). Кстати, сформировать такую последовательность пар поможет функция zip.

```python
states =  "Казахстан","Украина", "Китай"
capitals =  "Астана","Киев", "Пекин"

for Cuple in zip(states, capitals):
    print(Cuple)
print(type(Cuple))
print('*'*40)

the_dict = dict(zip(states, capitals))
print(the_dict)
```

Ключи уникальны в рамках словаря, они не могут повторяться. С точки зрения ключей словарь --- это множество. Но при этом каждому ключу сопоставлено значение. Значения не уникальны в рамках словаря, то есть у разных ключей значения могут повторяться. Но у одного ключа всегда только одно значение.

```python
the_dict = {"корова": 2, "коза":2, "собака": 3, "кошка": 3,
            "рыба": 0, "петух": 8}
print("Угадайте, что значат числа в этой задаче-шутке?")
for key in the_dict:
    print(key, the_dict[key], sep=' - ')
```

Обратите внимание, что при итерировании по словарю он отдаёт только ключи!

Чтобы получить значение конкретного ключа, нужно обратиться к словарю с квадратными скобками, то есть буквально как к массиву. Только тип key может быть, например, строкой.

Можно обратиться за поиском значения по одному конкретному ключу:

```python
the_dict["кошка"]
```

*Если* ключа в словаре не будет, то мы получим ошибку KeyError:

```python
the_dict["слон"]
```

Значит, перед тем как обращаться за значением, нужно убедиться, что такой ключ вообще есть в словаре при помощи операций in / not in:

```python
key = input("Введите название животного, и я скажу вам число, если его знаю: ")
while key not in the_dict:
    key = input("Простите, такого животного нет в моей базе знаний. Ещё раз: ")
print("Число для", key, "-", the_dict[key])
```

Чтобы добавить новую пару (ключ, значение) в словарь, нужно просто присвоить этому ключу значение:

```python
the_dict["осёл"] = 2
print("В словаре теперь содержится", len(the_dict), "пар (ключ, значение).")
```

Повторное присваивание ключу значения может привести к изменению значения, но нового ключа не создаёт:

```python
the_dict["осёл"] = 3  # ошибки не будет
print("В словаре содержится", len(the_dict), "пар (ключ, значение).")
```

Чтобы удалить ключ вместе со значением, используется оператор del:

```python
print("Были числа таких животных:", end=' ')
print(*the_dict, sep=", ")  # разворачиваем как итерируемый объект — получаем только ключи
del the_dict["рыба"]
print("Теперь я знаю числа таких животных:", end=' ')
print(*the_dict, sep=", ")  # разворачиваем как итерируемый объект — получаем только ключи
```

Можно безопасно добывать значения из словаря при помощи метода get. В этом случае будет возвращаться значение по умолчанию, которое мы укажем вторым параметром:

```python
key = input()
print("Число для ключа:", the_dict.get(key, "не знаю."))
```

Для словарей есть dict comprehensions, которые позволяют генерировать словари по любым итерируемым объектам:

```python
animals_names = ["корова", "коза", "собака", "кошка", "рыба", "петух", "осёл"]
animals_sounds = ["му", "ме", "гав", "мяу", "", "кукареку", "иа"]
the_dict = {animal: len(sound) for animal, sound in zip(animals_names, animals_sounds)}
print("Разгадка задачи-шутки в исходном тексте:")
print(the_dict)
```

### **2.1 Задача о выборах**
На факультете политологии решили выбрать представителя в студсовет вуза. Голосование
анонимное и открытое: каждый студент мог написать на своём бюллетене фамилию абсолютно любого студента. Для простоты задачи примем, что фамилии студентов на факультете не повторяются.

Данные голосования лежат в файле elections.txt: каждая фамилия в новой строке. При этом среди студентов есть шутники, которые могут вписать несущестующую фамилию , поэтому для отбраковки голосов у вас есть файл students.txt с фамилиями всех студентов курса.

Пришла пора подводить результаты — распечатать рейтинг студентов по убыванию количества голосов, а также определить победителя.

```python
with open("students.txt", encoding='utf8') as file:
    students_set = {line.strip() for line in file}
print(students_set)
```

```python
candidates_votes = {}
with open("elections.txt", encoding='utf8') as file:
    for line in file:
        candidate = line.strip()
        if candidate not in students_set:
            continue
        if candidate not in candidates_votes:
            candidates_votes[candidate] = 1
        else:
            candidates_votes[candidate] += 1
print(candidates_votes)
print(type(candidates_votes), type(students_set))
```

Метод items возвращает ключи и значения словаря в виде набора кортежей. Результат возвращается в виде специального объекта dict_items.

```python
candidates_votes = {}  # пустой словарь для пар (кандидат, количество голосов за него)
with open("students.txt", encoding="utf8") as file:
    students_set = {line.strip() for line in file}
with open("elections.txt", encoding="utf8") as file:
    for line in file:
        candidate = line.strip()
        if candidate not in students_set:
            continue  # пропускаем такую фамилию, прыгаем на следующую итерацию цикла for
        if candidate not in candidates_votes:
            candidates_votes[candidate] = 1  # Это первый голос, поданный за этого студента.
        else:
            candidates_votes[candidate] += 1  # За этого кандидата поступил ещё один голос.

rating = sorted(candidates_votes.items(), key=lambda pair: pair[1], reverse=True)
elected_delegate = rating[0][0]
print("Избранный представитель факультета:", elected_delegate)
print()  # представление результатов табличкой:
print("Фамилия кандидата".ljust(30), "Голосов".ljust(10), sep='| ')
print('-'*30 + '+' + '-'*10)
for candidate, votes in rating:
    print(candidate[:30].ljust(30), str(votes).ljust(10), sep='| ')
```

ljust() вернет новую строку с текстом str , выровненным по левому краю и шириной width.

В случае подсчёта сущностей используем класс Counter из стандартной библиотеки collections.

```python
from collections import Counter

candidates_votes = Counter()
# Счётчик для голосов за кандидатов.
with open("students.txt", encoding="utf8") as file:
    students_set = {line.strip() for line in file}
with open("elections.txt", encoding="utf8") as file:
    for line in file:
        candidate = line.strip()
        if candidate in students_set:
            candidates_votes[candidate] += 1  # +1 голос за кандидата.

rating = candidates_votes.most_common()
elected_delegate = rating[0][0]
print("Избранный представитель факультета:", elected_delegate)
print()  # представление результатов табличкой:
print("Фамилия кандидата".ljust(30), "Голосов".ljust(10), sep='| ')
print('-'*30 + '+' + '-'*10)
for candidate, votes in rating:
    print(candidate[:30].ljust(30), str(votes).ljust(10), sep='| ')
```

most_common() возвращает список из n наиболее распространенных элементов и их количество от наиболее распространенных до наименее. Если n опущено или None , метод cnt. most_common() возвращает все элементы в счетчике.