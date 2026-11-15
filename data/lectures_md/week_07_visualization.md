---
week_number: 7
topic_id: "week_07_visualization"
title: "Неделя 7: Визуализация данных (Matplotlib, Seaborn, Plotly)"
topic_name: "Построение статических и интерактивных графиков, статистическая визуализация Seaborn, тепловые карты и 3D-графики"
initial_prompt: "Привет! На седьмой лекции мы разобрали инструменты визуализации. Каковы преимущества статистических графиков Seaborn (например, pairplot или heatmap корреляций) перед базовым Matplotlib при первичном разведочном анализе данных (EDA)?"
source_files:
  - "Lecture_7_1_Visualization_Matplotlib.ipynb"
  - "Lecture_7_2_Visualization_Seaborn.ipynb"
  - "Lecture_7_3_Plotly_Visualization.ipynb"
glossary:
  - "ability"
  - "academic"
  - "add_trace"
  - "additional"
  - "admission"
  - "admission_date"
  - "admission_score"
  - "admission_year"
  - "advantage"
  - "agg"
  - "allow"
  - "alpha"
  - "eda"
  - "heatmap"
  - "histogram"
  - "interactive charts"
  - "matplotlib"
  - "plotly"
  - "scatter plot"
  - "seaborn"
---

# Неделя 7: Визуализация данных (Matplotlib, Seaborn, Plotly)

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** Построение статических и интерактивных графиков, статистическая визуализация Seaborn, тепловые карты и 3D-графики

## Материалы ноутбука: Lecture_7_1_Visualization_Matplotlib.ipynb

# **Лекция 7_1. Библиотека Matplotlib**

## **§1 Построение графиков и основы библиотеки Matplotlib**
Библиотека Matplotlib предназначена для построения диграмм и графиков, в том числе трёхмерных.
Документация на английском языке по ней доступна онлайн на https://matplotlib.org/

### **1.1 Простой график на декартовой плоскости**

График функции одной переменной обычно строится на картезианской плоскости. Картезианская плоскость — это система координат, в которой положение точки на плоскости определяется двумя координатами (x,y).

```python
import matplotlib.pyplot as plt
```

[Иллюстрация к лекции]

[Иллюстрация к лекции]

***Некоторые функции отрисовки***

plt.scatter(x, y, params) — нарисовать точки с координатами из  x
  по горизонтальной оси и из  y
  по вертикальной оси;

plt.plot(x, y, params) — нарисовать график по точкам с координатами из  x
  по горизонтальной оси и из  y
  по вертикальной оси. Точки будут соединятся в том порядке, в котором они указаны в этих массивах;

plt.fill_between(x, y1, y2, params) — закрасить пространство между  y1
  и  y2
  по координатам из  x
 ;

plt.pcolormesh(x1, x1, y, params) — закрасить пространство в соответствии с интенсивностью  y
 ;

plt.contour(x1, x1, y, lines) — нарисовать линии уровня. Затем нужно применить plt.clabel.

***Вспомогательные функции***

plt.figure(figsize=(x, y)) — создать график размера  (x,y)
 ;

plt.show() — показать график;

plt.subplot(...) — добавить подграфик;

plt.xlim(x_min, x_max) — установить пределы графика по горизонтальной оси;

plt.ylim(y_min, y_max) — установить пределы графика по вертикальной оси;

plt.title(name) — установить имя графика;

plt.xlabel(name) — установить название горизонтальной оси;

plt.ylabel(name) — установить название вертикальной оси;

plt.legend(loc=...) — сделать легенду в позиции loc;

plt.grid() — добавить сетку на график;

plt.savefig(filename) — сохранить график в файл.

http://matplotlib.org/gallery.html — тысячи примеров

У функций в matplotlib много параметров. Для того, чтобы посмотреть все параметры, можно воспользоваться справкой, например,

plt.plot?

***Примеры***
https://mipt-stats.gitlab.io/courses/python/06_matplotlib.html

```python
x = [-3, -2, -1, 0, 1, 2, 3]
y = [9, 4, 1, 0, 1, 4, 9]
plt.plot(x, y)
plt.show()
```

```python
plt.plot(x, y,'r--')
plt.show()
```

### **1.2 Графики математических функций**
В математкие функция рассматривается как *отображение*, в котором каждому прообразу из области определения функции соответствует *только один* образ из множества значений функции.

[Иллюстрация к лекции]

## Стандартные математические функции
Библиотека **math** содержит немного полезных и известных вам из школы математических функций.

### Тригонометрические функции
Базовые тригонометрические функции — синус `math.sin(x)` и косинус `math.cos(x)`.

```python
import math
x = [-7.0, -6.8, -6.6, -6.3, -6.1, -5.9, -5.7, -5.5, -5.3, -5.1, -4.9, -4.7, -4.5, -4.3, -4.1, -3.9,
     -3.7, -3.5, -3.3, -3.1, -2.9, -2.7, -2.5, -2.3, -2.1, -1.9, -1.7, -1.5, -1.3, -1.1, -0.9, -0.7,
     -0.5, -0.3, -0.1, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0,
     3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.6, 5.8, 6.0, 6.2, 6.4, 6.6, 6.8]
sin_y = [math.sin(t) for t in x]
cos_y = [math.cos(t) for t in x]
plt.title("harmonic functions: sin and cos")
plt.plot(x, sin_y, x, cos_y)
plt.show()
```

```python
y=x
plt.plot(x, y, '--', x, [1]*len(x), '--', x, [-1]*len(x), '--',
         x, sin_y, x, cos_y)
plt.show()
```

Функция tangent имеет национальную особенность: в русской и немецкой математической традиции она пишется как *tg*, но в других европейских странах её сокращают как *tan*.

Значит и в Python пишем `math.tan(x)`:

```python
x = [-1.482, -1.44, -1.404, -1.326, -1.248, -1.17, -1.092, -1.014, -0.936, -0.86, -0.78, -0.7, -0.6, -0.5, -0.3,
     -0.15, 0.0, 0.15, 0.3, 0.5, 0.6, 0.7, 0.78, 0.86, 0.936, 1.014, 1.092, 1.17, 1.248, 1.326, 1.404, 1.44, 1.482]
tan_y = [math.tan(t) for t in x]
plt.title("tangent function")
plt.axvline(x=0)
plt.plot(x, tan_y,'r', x, x, '--')
plt.show()
```

### Экспонента
Экспонента — это одна из показательных функций, как $2^{x}$, только основанием служит число $e$.

При этом $e = 2.718281828459045..$.

Для функции $e^{x}$ даже придумали специальное обозначение: $\exp(x)$

```python
x = [-3.1, -2.9, -2.7, -2.5, -2.3, -2.1, -1.9, -1.7, -1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3,
     -0.1, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]
exp_y = [math.exp(t) for t in x]
plt.title("exponent function")
plt.plot(x, [0]*len(x), '--', x, exp_y)
plt.show()
```

### Логарифм
$log_{A}{B}$

Логарифм — функция, обратная показательной, отвечает на вопрос "в какую степень нужно возвести A, чтобы получить B".

Эта функция не определена для отрицательных чисел и нуля, поэтому для неё возьмём диапазон от 0.1 до 5.

```python
x = [0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4,
     2.6, 2.8, 3.0,3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0]
log_y = [math.log(t, 2) for t in x]
plt.title("logarithm function")
plt.plot(x, log_y, x, [0]*len(x), '--')
plt.show()
```

Если мы вызываем функцию `math.log(t)` с одним параметром, то возвращаемое значение - это натуральный логарифм (то есть основание равно `e`).

### **1.3. Практика создания пользовательских функций**
Дано математическое выражение, переписать его как функцию на Python:

$ e^{\frac{x}{2}+1} + e^{2 x + 1} \cdot \sin^2(5x + 3)$

```python
from math import *
import matplotlib.pyplot as plt

def p_function(x: float) -> float:
    return e**(x/2 + 1) + e ** (2*x + 1) * sin(5*x + 3)**2

x = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05,
     1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0, 2.05,
     2.1, 2.15, 2.2, 2.25, 2.3, 2.35, 2.4, 2.45, 2.5, 2.55, 2.6, 2.65, 2.7, 2.75, 2.8, 2.85, 2.9, 2.95, 3.0, 3.05,
     3.1, 3.15, 3.2, 3.25, 3.3, 3.35, 3.4, 3.45, 3.5, 3.55, 3.6, 3.65, 3.7, 3.75, 3.8, 3.85, 3.9, 3.95, 4.0, 4.05,
     4.1, 4.15, 4.2, 4.25, 4.3, 4.35, 4.4, 4.45, 4.5, 4.55, 4.6, 4.65, 4.7, 4.75, 4.8, 4.85, 4.9, 4.95, 5.0, 5.05,
     5.1, 5.15, 5.2, 5.25, 5.3, 5.35, 5.4, 5.45, 5.5, 5.55, 5.6, 5.65, 5.7, 5.75, 5.8, 5.85, 5.9, 5.95, 6.0, 6.05,
     6.1, 6.15, 6.2, 6.25, 6.3, 6.35, 6.4, 6.45, 6.5, 6.55, 6.6, 6.65, 6.7, 6.75, 6.8, 6.85, 6.9, 6.95, 7.0, 7.05,
     7.1, 7.15, 7.2, 7.25, 7.3, 7.35, 7.4, 7.45, 7.5, 7.55, 7.6, 7.65, 7.7, 7.75, 7.8, 7.85, 7.9, 7.95, 8.0, 8.05,
     8.1, 8.15, 8.2, 8.25, 8.3, 8.35, 8.4, 8.45, 8.5, 8.55, 8.6, 8.65, 8.7, 8.75, 8.8, 8.85, 8.9, 8.95, 9.0, 9.05,
     9.1, 9.15, 9.2, 9.25, 9.3, 9.35, 9.4, 9.45, 9.5, 9.55, 9.6, 9.65, 9.7, 9.75, 9.8, 9.85, 9.9, 9.95, 10.0]
y = [p_function(t) for t in x]
plt.plot(x, y)
```

```python
import numpy as np
import matplotlib.pyplot as plt
```

Векторные операции дают возможность оперативно подготавливать данные для отображения на графиках.

Визуализируем некоторые математические функции:

```python
x = np.linspace(-3*np.pi, +3*np.pi, 60)
sin_x = np.sin(x)
cos_x = np.cos(x)
plt.plot(x, cos_x, 'g--')
plt.plot(x, sin_x, 'r')
plt.show()
```

```python
import math
import matplotlib.pyplot as plt

my_range = [-2.01, -1.99, -1.51, -1.5, -1.49, -1.01, -0.99, -0.51, -0.5, -0.49, -0.01,
            0.01, 0.49, 0.5, 0.51,  0.99, 1.01, 1.49, 1.5, 1.51, 1.99, 2.01]
floor_values = [math.floor(x) for x in my_range]
round_values = [round(x) for x in my_range]
ceil_values = [math.ceil(x) for x in my_range]

plt.plot(my_range, my_range, 'r-',
         my_range, floor_values, 'g.-.',
         my_range, ceil_values, 'b.-.',
         my_range, round_values, 'y--')
plt.show()
trunc_values = [math.trunc(x) for x in my_range]
print("number", "", "trunc", "floor", "ceil", "round", sep='\t')
for x, *values in zip(my_range, trunc_values, floor_values, ceil_values, round_values):
    print(str(x).ljust(4), '-->', *(str(x).ljust(7) for x in values), sep='\t')
```

### **2.7 Гистограммы и диаграммы**
Иногда нам нужно визуализировать данные не в форме графика, а при помощи других *диаграмм*. Одна из самых важных для статистики и анализа данных диаграмм — это **гистограмма**:

> Филолог хочет вывести гистограмму количества слов в зависимости от количества букв в слове.

```python
from collections import Counter

with open('plants1.txt', encoding='utf8') as text:
    words_lengths_counter = Counter(len(word) for word in text.read().split())

longest_word_length = max(words_lengths_counter)

histogram = [words_lengths_counter[word_length] for word_length in range(0, longest_word_length + 1)]
for k in range(longest_word_length, 0, -1):
    bin_width = histogram[k]
    print(str(k).ljust(4), "* " * bin_width)
```

```python
plt.hist(list(range(0, longest_word_length + 1)), weights=histogram, bins=longest_word_length+1, orientation='horizontal')
plt.xlabel("количество слов данной длины")
plt.ylabel("длина слова")
plt.show()
plt.savefig("1.png")
```

```python
plt.hist(list(range(0, longest_word_length + 1)), weights=histogram, bins=longest_word_length+1, orientation='vertical')
plt.ylabel("количество слов данной длины")
plt.xlabel("длина слова")
plt.plot()
plt.savefig('1.png')
```

```python
import matplotlib.pyplot as plt

with open('plants1.txt', encoding='utf8') as text:
    words_lengths = [len(word) for word in text.read().split()]
longest_word_length = max(words_lengths)
plt.hist(words_lengths, bins=longest_word_length)
plt.title("Распределение слов по длинам")
plt.ylabel("количество слов данной длины")
plt.xlabel("длина слова")
plt.show()
```

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
data = pd.read_csv("apartments.csv")
```

```python
rooms_col = "Количество комнат"
area_col  = "Площадь (кв. м)"

# Лёгкий джиттер по X, чтобы точки не слипались (регулируйте scale при желании)
rng = np.random.default_rng(42)             # фиксируем «случайность» для воспроизводимости
x = apartments[rooms_col].to_numpy(dtype=float)
x_jittered = x + rng.normal(0, 0.08, size=len(x))  # sd=0.08 ~ 8% от шага между категориями
y = apartments[area_col].to_numpy(dtype=float)

plt.figure(figsize=(10, 6))
plt.scatter(x_jittered, y, s=18, alpha=0.6)  # точки чуть прозрачные

# Оси, подписи и сетка
rooms_sorted = np.sort(apartments[rooms_col].unique())
plt.xticks(rooms_sorted, [str(int(r)) if float(r).is_integer() else str(r) for r in rooms_sorted])
plt.xlabel("Количество комнат")
plt.ylabel("Площадь (кв. м)")
plt.title("Scatter: площадь по количеству комнат")
plt.grid(True, axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()
```

---

## Материалы ноутбука: Lecture_7_2_Visualization_Seaborn.ipynb

# **Что такое Seaborn и когда его использовать**

# **Seaborn** — высокоуровневая библиотека визуализации на базе Matplotlib, тесно интегрированная с pandas.
# Ключевая идея: “statistical plotting” — многие графики сразу умеют агрегировать данные (estimator), вычислять доверительные интервалы и строить «семейства» графиков через faceting (row/col/hue).

# **Преимущества**
# Высокоуровневый API: меньше кода для сложных графиков (facets, legend, palettes).
# Умные стили по умолчанию: сетки, палитры, шрифты.
# Статистические функции: агрегирование (median/mean), доверительные интервалы, сглаживание, регрессия.
# Плотная интеграция с pandas DataFrame (аргументы data=..., x=..., y=..., hue=...).
# Богатый набор: relplot, displot, catplot, jointplot, pairplot, heatmap, clustermap, lmplot и др.

```python
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Рекомендуемая современная настройка темы:
sns.set_theme(context="notebook", style="whitegrid")  # стиль сетки и читаемый контекст
```

# **Базовые паттерны Seaborn**
# *Axes-level vs Figure-level*

# Axes-level функции рисуют внутри переданной оси (например, sns.scatterplot, sns.histplot, sns.boxplot).
# Figure-level функции создают целую фигуру с FacetGrid (например, sns.relplot, sns.displot, sns.catplot, sns.lmplot), удобно для faceting.

[Иллюстрация к лекции]

# **Диаграммы распределений и плотности**

# *Гистограммы и KDE*

# **KDE (Kernel Density Estimation)**

# KDE — это оценка плотности вероятности (гладкая кривая распределения).
# Использует ядровую аппроксимацию, чтобы показать, как распределены данные.
# Визуально: плавная линия, «напоминающая горы».
# В Seaborn можно построить через sns.kdeplot() или включить kde=True в sns.histplot().

# *ECDF (эмпирическая функция распределения)*

```python
plt.figure(figsize=(6,4))
sns.ecdfplot(data=penguins, x="bill_length_mm", hue="species")  # сравнение распределений по видам
plt.title("ECDF по видам пингвинов")
plt.show()
```

# *distplot / displot (современный способ — displot)*

# **Точечные/линейные графики и регрессия**

# *Scatter/Line (relplot, scatterplot, lineplot)*

[Иллюстрация к лекции]

[Иллюстрация к лекции]

# *Регрессия (regplot, lmplot)*

# **Категориальные графики**

# *Bar/Point/Count*

# *Box/Violin/Boxen/Swarm/Strip*

# **boxenplot** (или letter-value plot) — это расширенный вариант boxplot в библиотеке Seaborn, который используется для визуализации распределений данных.

# 📌 Он показывает:
# медиану, квартили (как boxplot);
# выбросы;
# но главное — детализированные "хвосты" распределения: чем дальше от медианы, тем глубже строятся дополнительные уровни (letter-values).

# Таким образом, boxenplot полезен для:
# больших выборок;
# асимметричных распределений;
# анализа длинных хвостов данных.

# 📌 **violinplot** показывает:

# распределение данных по признаку;
# плотность вероятности (kernel density estimation, KDE);
# медиану и квартили (как boxplot).
# То есть это комбинация boxplot + сглаженная кривая распределения (напоминает форму скрипки 🎻, отсюда название).

# *Figure-level «catplot»*

# В Seaborn функция **catplot** — это универсальный «фасетный» (обобщённый) график для категориальных данных.

# 📌 Что делает **catplot**:позволяет строить разные виды категориальных графиков: strip, swarm, box, violin, boxen, point, bar, count;
# имеет встроенную возможность «фасетирования» (разделения графика на подгруппы по категориям с помощью аргументов row и col);
# удобен, когда нужно сравнивать распределения или частоты по категориям.

# **Парные и совместные распределения**

# *Pairplot*

# *Jointplot*

# **Корреляции и тепловые карты**

# **Faceting и «мелтиние» (tidy-format)**

# **Тепловая карта для временных рядов**

# **Комбинирование с Matplotlib**

```python
fig, ax = plt.subplots(figsize=(6,4))
sns.violinplot(data=penguins, x="species", y="bill_depth_mm", hue="sex", split=True, ax=ax)
ax.set_title("Violinplot + кастомные подписи через Matplotlib")
ax.set_xlabel("Вид")
ax.set_ylabel("Толщина клюва, мм")
ax.legend_.set_title("Пол")  # доступ к легенде
plt.show()
```

# **Сохранение рисунков**

# **Пример: Корреляция. Посчитайте корреляции по числовым полям в diamonds и нарисуйте тепловую карту с маской верхнего треугольника; выделите сильнейшие связи.**

```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Загружаем встроенный датасет
diamonds = sns.load_dataset("diamonds")
```

# Таблица содержит ~54 000 строк и такие поля:

# carat — масса (в каратах),
# cut — качество огранки,
# color — цвет,
# clarity — чистота,
# depth — глубина огранки,
# table — размер верхней грани,
# price — цена в долларах,
# x, y, z — размеры камня (мм).

[Иллюстрация к лекции]

# Тепловая карта с маской верхнего треугольника (цвета от -1 до +1).
# Таблица топ-5 связей — например:
#carat ~ x (≈ 0.97)
# carat ~ y (≈ 0.95)
# price ~ carat (≈ 0.92)
# x ~ y (≈ 0.97)
# y ~ z (≈ 0.95)

# Это ожидаемая структура: размеры бриллианта (x, y, z) и масса (carat) очень сильно связаны между собой и с ценой (price).

---

## Материалы ноутбука: Lecture_7_3_Plotly_Visualization.ipynb

# **Интерактивная визуализация данных с Plotly / Interactive Data Visualization with Plotly**

# **Plotly** is a Python library for creating interactive visualizations. Unlike static Matplotlib charts, Plotly supports zooming, panning, hover tooltips, and interactive control over displayed data series.
# **Plotly** — библиотека Python для создания интерактивных графиков. В отличие от статических графиков Matplotlib, Plotly позволяет масштабировать изображения, перемещаться по графику, просматривать значения при наведении курсора и включать или отключать отдельные категории данных.

```python
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
```

```python
df_clean = pd.read_csv("University Students 2026 New.csv")
```

# **Круговая диаграмма / Pie Chart**

```python
program_counts = (
    df_clean["program"]
    .value_counts()
    .reset_index()
)
program_counts.columns = ["program", "students"]
fig = px.pie(
    program_counts,
    names="program",
    values="students",
    title="Distribution of Students by Program",
    hole=0.3
)

fig.update_traces(
    textinfo="percent+label"
)

fig.show()
```

# hole=0.3 создаёт отверстие в центре диаграммы, превращая её в кольцевую (donut chart). textinfo="percent+label" выводит название категории и её процент.
# hole=0.3 creates a donut chart. textinfo="percent+label" displays category names and percentages.

# **Корреляционная тепловая карта / Correlation Heatmap**

# Тепловая карта корреляций показывает силу и направление линейной связи между числовыми признаками. Значения коэффициента Пирсона находятся в диапазоне от −1 до +1.
# A correlation heatmap visualizes the strength and direction of linear relationships between numerical features. Pearson correlation coefficients range from −1 to +1.

```python
numeric_columns = [
    "admission_score",
    "math_score",
    "programming_score",
    "english_score",
    "attendance",
    "assignments",
    "final_score"
]

corr_matrix = df_clean[numeric_columns].corr()

fig = px.imshow(
    corr_matrix,
    text_auto=".2f",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    aspect="auto",
    title="Correlation Matrix of Student Performance"
)

fig.update_layout(
    width=950,
    height=650
)

fig.show()
```

# text_auto=".2f" отображает коэффициенты с двумя знаками после запятой, а color_continuous_scale задаёт цветовую шкалу.
# text_auto=".2f" displays coefficients with two decimal places, while color_continuous_scale defines the color scale.

# **Диаграмма рассеивания / Scatter Plot**

```python
fig = px.scatter(
    df_clean,
    x="attendance",
    y="final_score",
    color="program",
    hover_data=["student_id", "year"],
    title="Attendance vs Final Score",
    labels={
        "attendance": "Attendance (%)",
        "final_score": "Final Score",
        "program": "Academic Program"
    }
)

fig.update_layout(
    width=950,
    height=550
)

fig.show()
```

# hover_data добавляет информацию, отображаемую при наведении курсора на точку.
# hover_data specifies additional information displayed when hovering over a point.

# **Трёхмерная диаграмма рассеивания / 3D Scatter Plot**

```python
fig = px.scatter_3d(
    df_clean,
    x="math_score",
    y="programming_score",
    z="final_score",
    color="program",
    hover_name="student_id",
    title="3D Student Performance Analysis",
    labels={
        "math_score": "Math Score",
        "programming_score": "Programming Score",
        "final_score": "Final Score"
    }
)

fig.update_layout(
    width=950,
    height=650
)

fig.show()
```

# **Временные ряды / Time Series**

```python
df_clean["admission_date"] = pd.to_datetime(
    df_clean["admission_date"]
)
df_clean["admission_year"] = (
    df_clean["admission_date"].dt.year
)
```

```python
yearly_scores = (
    df_clean
    .groupby(["admission_year", "program"], as_index=False)
    .agg(avg_score=("final_score", "mean"))
)
```

```python
fig = px.line(
    yearly_scores,
    x="admission_year",
    y="avg_score",
    color="program",
    markers=True,
    title="Average Final Score by Admission Year",
    labels={
        "admission_year": "Admission Year",
        "avg_score": "Average Final Score",
        "program": "Academic Program"
    }
)

fig.update_xaxes(dtick=1)

fig.show()
```

# **Гистограмма / Histogram**

```python
fig = px.histogram(
    df_clean,
    x="final_score",
    nbins=15,
    color="program",
    barmode="overlay",
    opacity=0.65,
    title="Distribution of Final Scores",
    labels={
        "final_score": "Final Score",
        "count": "Number of Students"
    }
)

fig.update_layout(
    xaxis_title="Final Score",
    yaxis_title="Number of Students",
    width=950,
    height=550
)

fig.show()
```

# nbins=15 задаёт желаемое количество интервалов, barmode="overlay" накладывает распределения друг на друга, а opacity=0.65 делает столбцы полупрозрачными.
# nbins=15 specifies the desired number of bins, barmode="overlay" overlays the distributions, and opacity=0.65 makes the bars partially transparent.

# **Ящик с усами / Boxplot**

```python
fig = px.box(
    df_clean,
    x="program",
    y="final_score",
    color="program",
    #points="all",
    title="Final Score Distribution by Program",
    labels={
        "program": "Academic Program",
        "final_score": "Final Score"
    }
)

fig.update_layout(
    width=950,
    height=550,
    showlegend=False
)

fig.show()
```

# **Анимация графиков / Animations in Python**

```python
animation_data = (
    df_clean
    .groupby(["year", "program"], as_index=False)
    .agg(students=("student_id", "count"))
)

programs = sorted(df_clean["program"].unique())
years = sorted(df_clean["year"].unique())

complete_index = pd.MultiIndex.from_product(
    [years, programs],
    names=["year", "program"]
)

animation_data = (
    animation_data
    .set_index(["year", "program"])
    .reindex(complete_index, fill_value=0)
    .reset_index()
)
```

```python
fig = px.bar(
    animation_data,
    x="program",
    y="students",
    color="program",
    animation_frame="year",
    range_y=[0, animation_data["students"].max() * 1.15],
    title="Student Distribution by Year of Study",
    labels={
        "program": "Academic Program",
        "students": "Number of Students",
        "year": "Year of Study"
    }
)

fig.update_layout(
    width=950,
    height=600,
    showlegend=False
)

fig.update_xaxes(categoryorder="array", categoryarray=programs)

fig.show()
```

# Параметр animation_frame="year" создаёт отдельный кадр для каждого курса обучения. Пользователь может запускать анимацию и переключаться между кадрами с помощью ползунка.
# animation_frame="year" creates a separate frame for each year of study. Users can play the animation or switch between frames using the slider.

# **Сохранение интерактивного графика / Saving an Interactive Chart**

# Важное преимущество Plotly — возможность сохранять графики в HTML с сохранением интерактивности.
# An important advantage of Plotly is the ability to save charts as HTML files while preserving their interactivity.

```python
fig.write_html("Student_Visualization.html")
```

# TML-файл можно открыть в браузере без запуска Python. В нём сохраняются масштабирование, наведение курсора и другие интерактивные элементы.
# The HTML file can be opened in a browser without running Python. Zooming, hover information, and other interactive features are preserved.

# **Sunburst Chart** — иерархическая круговая диаграмма

# Sunburst позволяет отображать иерархические данные с несколькими уровнями вложенности. Например: образовательная программа → курс → получение стипендии.
# A Sunburst chart visualizes hierarchical data with multiple levels, such as academic program → year of study → scholarship status.

```python
fig = px.sunburst(
    df_clean,
    path=["program", "year", "scholarship"],
    title="Student Distribution by Program, Year and Scholarship"
)

fig.show()
```

# **Treemap — древовидная карта**

# Treemap отображает иерархические категории в виде вложенных прямоугольников. Размер каждого прямоугольника отражает количество наблюдений.
# A Treemap displays hierarchical categories as nested rectangles, where rectangle size represents the number of observations.

```python
fig = px.treemap(
    df_clean,
    path=["program", "year", "gender"],
    title="Student Distribution by Program, Year and Gender"
)

fig.show()
```

# **Violin Plot — скрипичная диаграмма**

# Violin plot объединяет характеристики boxplot с оценкой плотности распределения. Он позволяет увидеть, в каких диапазонах сосредоточено больше наблюдений.
# A violin plot combines boxplot statistics with an estimated probability density, showing where observations are concentrated.

```python
fig = px.violin(
    df_clean,
    x="program",
    y="final_score",
    color="program",
    box=True,
    #points="all",
    title="Final Score Distribution by Program"
)

fig.show()
```

# **Parallel Coordinates — параллельные координаты**

# Один из наиболее интересных инструментов Plotly для многомерного анализа. Каждая линия представляет одного студента, а вертикальные оси — различные числовые признаки.
# Parallel Coordinates is a powerful visualization for multivariate analysis. Each line represents a student, while vertical axes represent numerical features.

```python
fig = px.parallel_coordinates(
    df_clean,
    dimensions=[
        "math_score",
        "programming_score",
        "english_score",
        "attendance",
        "final_score"
    ],
    color="final_score",
    color_continuous_scale="Viridis",
    title="Multidimensional Student Performance Analysis"
)

fig.show()
```

# **Scatter Matrix — матрица диаграмм рассеивания**

# Scatter Matrix автоматически создаёт набор диаграмм рассеивания для всех пар выбранных признаков. Это удобно для предварительного исследования взаимосвязей.
# A Scatter Matrix automatically creates scatter plots for all pairs of selected features, making it useful for exploratory relationship analysis.

```python
fig = px.scatter_matrix(
    df_clean,
    dimensions=[
        "math_score",
        "programming_score",
        "attendance",
        "final_score"
    ],
    color="program",
    title="Scatter Matrix of Student Performance"
)

fig.update_traces(diagonal_visible=False)
fig.show()
```

# **Interactive Dropdown — переключение данных на одном графике**

# Plotly позволяет создавать выпадающие списки, с помощью которых пользователь может менять отображаемый показатель без повторного запуска кода.
# Plotly supports dropdown menus that allow users to change the displayed metric without rerunning the code.

```python
metrics = [
    "math_score",
    "programming_score",
    "english_score",
    "final_score"
]

fig = go.Figure()

for i, metric in enumerate(metrics):
    avg = df_clean.groupby("program")[metric].mean()

    fig.add_trace(
        go.Bar(
            x=avg.index,
            y=avg.values,
            name=metric,
            visible=(i == 0)
        )
    )

fig.update_layout(
    title="Average Student Scores by Program",
    xaxis_title="Program",
    yaxis_title="Average Score",
    updatemenus=[
        dict(
            buttons=[
                dict(
                    label=metric,
                    method="update",
                    args=[{"visible": [
                        j == i for j in range(len(metrics))
                    ]}]
                )
                for i, metric in enumerate(metrics)
            ],
            direction="down"
        )
    ]
)

fig.show()
```