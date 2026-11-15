---
week_number: 5
topic_id: "week_05_preprocessing_features"
title: "Неделя 5: Агрегация, группировка данных и базовая визуализация в Pandas"
topic_name: "Паттерн Split-Apply-Combine, группировка groupby, агрегатные функции, слияние таблиц и визуализация распределений"
initial_prompt: "Привет! На пятой неделе мы изучили группировку и агрегацию в Pandas. Как работает паттерн Split-Apply-Combine в методе groupby, и в каких случаях заполнение пропусков средним или медианой может сместить общую статистическую оценку выборки?"
source_files:
  - "Lecture_4_3_Library Pandas.ipynb"
  - "Lecture_4_4_Pandas_Visualization.ipynb"
glossary:
  - "about"
  - "academic"
  - "accuracy"
  - "active"
  - "add"
  - "additional"
  - "adds"
  - "admission_score"
  - "after"
  - "agg"
  - "aggregation"
  - "algorithms"
  - "box plot"
  - "fillna"
  - "groupby"
  - "join"
  - "merge"
  - "missing values"
  - "split-apply-combine"
---

# Неделя 5: Агрегация, группировка данных и базовая визуализация в Pandas

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** Паттерн Split-Apply-Combine, группировка groupby, агрегатные функции, слияние таблиц и визуализация распределений

## Материалы ноутбука: Lecture_4_3_Library Pandas.ipynb

# ***Data Grouping and Aggregation / Группировка и агрегирование данных***

# Grouping allows us to split data into groups based on one or more features and perform calculations separately for each group. In Pandas, this is done using the groupby() method.

# Группировка позволяет разделить данные на группы по значениям одного или нескольких признаков и выполнить вычисления отдельно для каждой группы. В Pandas для этого используется метод groupby().

# **Split → Apply → Combine**
# - Split — разделить данные на группы / divide data into groups;
# - Apply — применить функцию к каждой группе / apply a function to each group;
# - Combine — объединить результаты / combine the results.

# **Простая группировка / Basic Grouping**

```python
import pandas as pd
df_clean = pd.read_csv("University Students 2026 New.csv")
```

```python
df_clean.groupby("program")
```

# This command creates a grouping object but does not perform any calculations by itself.
# Эта команда создаёт объект группировки, но сама по себе ещё не выполняет вычислений.

```python
df_clean.groupby("program")["final_score"].mean()
```

# Students are grouped by program, and the mean final_score is calculated for each program.

# count() counts the number of non-null student_id values in each program.

```python
df_clean.groupby("program").size()
```

# count() — считает непропущенные значения / counts non-null values;
# size() — считает все строки группы / counts all rows in the group.

```python
df_clean.groupby("program")["final_score"].min()
```

```python
df_clean.groupby("program")["final_score"].max()
```

```python
df_clean.groupby("program")["final_score"].median()
```

# In the result, each row represents a program, while the columns show the average student performance for that program.

# agg() позволяет применить несколько агрегирующих функций за одну операцию.
# agg() allows multiple aggregation functions to be applied in a single operation.

# This allows us to compare the average final score of students from different years within each academic program.

# First, the data are grouped, then the mean is calculated, and finally the result is sorted.

# Строки показывают образовательные программы, столбцы — курс обучения, а значения — средний итоговый балл.По смыслу это аналог Pivot Table в Excel.
# Rows represent academic programs, columns represent years of study, and values show the average final score.

# ***Корреляционный анализ / Correlation Analysis***

# Корреляционный анализ используется для оценки силы и направления взаимосвязи между числовыми признаками.
# Correlation analysis is used to evaluate the strength and direction of relationships between numerical features.

```python
df_clean["attendance"].corr(df_clean["final_score"])
```

# The correlation coefficient ranges from -1 to 1.

# Положительное значение означает, что более высокая посещаемость имеет тенденцию сопровождаться более высоким итоговым баллом. Корреляция сама по себе не доказывает причинно-следственную связь.
# A positive value means that higher attendance tends to be associated with a higher final score. Correlation itself does not establish causation.

# By default, corr() calculates the Pearson correlation coefficient for each pair of numerical features.
# Метод corr() по умолчанию рассчитывает коэффициент корреляции Пирсона для каждой пары числовых признаков.

# **Combining DataFrames / Объединение таблиц**

# In real-world tasks, data are often stored in multiple tables. For example, student information may be stored in one file, faculty information in another, and additional course results in a third. Pandas provides several methods for combining tables: merge(), join(), and concat().

# В реальных задачах данные часто хранятся не в одной таблице. Например, основная информация о студентах может находиться в одном файле, информация о факультетах — в другом, а результаты дополнительных курсов — в третьем. Pandas предоставляет несколько способов объединения таблиц: merge(), join() и concat().

# **merge()** — объединение по общему ключу / Combining Data Using a Common Key

# Let's create an additional table with information about students. / Создадим дополнительную таблицу с информацией о студентах

```python
student_status = pd.DataFrame({
    "student_id": ["ST001", "ST002", "ST003", "ST004", "ST005","ST201"],
    "status": ["Active", "Active", "Exchange", "Active", "Academic Leave","Exchange"]
})

student_status
```

```python
merged_df = pd.merge(
    df_clean,
    student_status,
    on="student_id",
    how="inner"
)

merged_df.head()
```

# Параметр on="student_id" определяет столбец-ключ, по которому сопоставляются строки двух таблиц.
# The on="student_id" parameter specifies the key column used to match rows from the two tables.

# Types of merge()/Типы объединения merge()
# **inner**
# **left**
# **right**
# **outer**

# Оставляет только студентов, присутствующих в обеих таблицах.
# Keeps only students that are present in both tables.

# Сохраняет всех студентов из левой таблицы df_clean и добавляет найденную информацию из второй таблицы.
# Keeps all students from the left DataFrame df_clean and adds matching information from the second DataFrame.

# Сохраняет все строки правой таблицы.
# Keeps all rows from the right DataFrame.

# Сохраняет все записи из обеих таблиц независимо от наличия соответствия.
# Keeps all records from both DataFrames, regardless of whether a match exists.

# **Different Key Names\Разные названия ключей**

```python
student_status = pd.DataFrame({
    "student_code": ["ST001", "ST002", "ST003"],
    "status": ["Active", "Active", "Exchange"]
})
```

```python
merged_df = pd.merge(
    df_clean,
    student_status,
    left_on="student_id",
    right_on="student_code",
    how="right"
)
```

```python
merged_df.head()
```

# left_on задаёт ключ левой таблицы, right_on — ключ правой.
# left_on specifies the key in the left DataFrame, while right_on specifies the key in the right DataFrame.

# **join()** — объединение по индексу / Joining by Index
# join() особенно удобен, когда таблицы необходимо объединить по индексам.
# join() is particularly convenient when DataFrames need to be combined using their indexes.

```python
status = student_status.set_index("student_code")
students = df_clean.set_index("student_id")
joined_df = students.join(
    status,
    how="left"
)
joined_df.head()
```

# merge() чаще используют для объединения по столбцам, а join() удобно использовать для объединения по индексам.
# merge() is commonly used for column-based matching, while join() is convenient for index-based matching.

# **concat()** — объединение таблиц / Concatenating DataFrames

```python
students_part1.shape
```

```python
students_part2.shape
```

```python
students_all = pd.concat(
    [students_part1, students_part2],
    axis=0
)
students_all.shape
```

# axis=0 означает добавление строк друг под другом.
# axis=0 means combining DataFrames vertically by rows.

```python
students_all = pd.concat(
    [students_part1, students_part2],
    ignore_index=True
)
students_all.shape
```

# ignore_index=True создаёт новый последовательный индекс после объединения.
# ignore_index=True creates a new sequential index after concatenation.

# **concat()** по столбцам / Column-wise concat()

```python
student_info = df_clean[
    ["student_id", "gender", "program"]
]
student_scores = df_clean[
    ["math_score", "programming_score", "final_score"]
]
combined_df = pd.concat(
    [student_info, student_scores],
    axis=1
)
combined_df.head()
```

# axis=1 означает объединение по столбцам.
# axis=1 means combining DataFrames by columns.
# axis=0 → rows
# axis=1 → columns

**merge, join, or concat?**

# | Метод | Когда использовать / When to use |

# | `merge()` | Связать таблицы по ключевому столбцу / Match tables using a key column |
# | `join()` | Связать преимущественно по индексам / Join primarily by index |
# | `concat(axis=0)` | Добавить строки / Add rows |
# | `concat(axis=1)` | Добавить столбцы / Add columns |

# merge() ищет соответствия между записями, а concat() преимущественно складывает существующие структуры вместе.
# merge() matches related records, while concat() primarily combines existing structures.

# **Подготовка структурированных данных для Scikit-learn / Preparing Structured Data for Scikit-learn**

# После очистки и преобразования DataFrame можно подготовить данные для использования алгоритмами машинного обучения. Обычно данные разделяются на матрицу признаков X и целевую переменную y.
# After cleaning and transforming a DataFrame, the data can be prepared for machine learning algorithms. Typically, the dataset is divided into a feature matrix X and a target variable y.
# Допустим, наша задача:
# На основе учебных показателей студента прогнозировать его итоговый балл final_score.
# Predict a student's final_score based on academic characteristics.

```python
print("X shape:", X.shape)
print("y shape:", y.shape)
```

# X содержит входные признаки модели, а y — значение, которое модель должна научиться прогнозировать.
# X contains the model input features, while y contains the value that the model should learn to predict.

# **Разделение на обучающую и тестовую выборки / Train-Test Split**

```python
from sklearn.model_selection import train_test_split
```

```python
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)
```

# test_size=0.2 означает, что 20% данных используются для тестирования, а 80% — для обучения.
# test_size=0.2 means that 20% of the data are used for testing and 80% for training.

```python
print("X_train:", X_train.shape)
print("X_test:", X_test.shape)
print("y_train:", y_train.shape)
print("y_test:", y_test.shape)
```

# **Несбалансированные данные / Imbalanced Data**

# Набор данных называется несбалансированным, если разные классы целевой переменной представлены существенно разным количеством наблюдений.
# A dataset is considered imbalanced when the classes of the target variable contain substantially different numbers of observations.

# Проверка баланса классов / Checking Class Balance

```python
df_clean["scholarship"].value_counts()
```

```python
class_distribution = (
    df_clean["scholarship"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

class_distribution
```

# **Why Is Class Imbalance a Problem?**

# Поэтому высокая accuracy не всегда означает хорошую модель, особенно при сильном дисбалансе классов.
# Therefore, high accuracy does not always indicate a good model, especially when the classes are strongly imbalanced.

# Визуализация распределения классов / Visualizing Class Distribution

```python
import matplotlib.pyplot as plt

df_clean["scholarship"].value_counts().plot(
    kind="bar",
    figsize=(7, 5)
)

plt.title("Scholarship Class Distribution")
plt.xlabel("Scholarship")
plt.ylabel("Number of Students")
plt.xticks(rotation=0)
plt.show()
```

# **Stratified Train-Test Split**

```python
X = df_clean[
    [
        "math_score",
        "programming_score",
        "english_score",
        "attendance",
        "assignments"
    ]
]

y = df_clean["scholarship"]
```

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)
```

```python
print(y.value_counts(normalize=True))
```

```python
print(y_train.value_counts(normalize=True))
```

```python
print(y_test.value_counts(normalize=True))
```

# stratify=y старается сохранить примерно одинаковое соотношение классов в обучающей и тестовой выборках.
# stratify особенно полезен в задачах классификации, когда необходимо сохранить распределение классов при разделении данных.
# stratify=y preserves approximately the same class proportions in the training and test sets.
# stratify is particularly useful in classification tasks when class proportions should be preserved during the train-test split.

# Pandas является не просто библиотекой для просмотра таблиц. Он обеспечивает полный этап подготовки структурированных данных перед статистическим анализом и машинным обучением.
# Pandas is not simply a library for viewing tables. It provides a complete workflow for preparing structured data before statistical analysis and machine learning.

---

## Материалы ноутбука: Lecture_4_4_Pandas_Visualization.ipynb

# ***Визуализация данных / Data Visualization***

```python
import matplotlib.pyplot as plt
```

```python
import seaborn as sns
```

# **Bar Chart — средний итоговый балл по программам / Average Final Score by Program**

```python
import pandas as pd
df_clean = pd.read_csv("University Students 2026 New.csv")
```

```python
average_score = (
    df_clean
    .groupby("program", as_index=False)["final_score"]
    .mean()
)
```

```python
plt.figure(figsize=(10, 6))

sns.barplot(
    data=average_score,
    x="program",
    y="final_score"
)

plt.title("Average Final Score by Program")
plt.xlabel("Program")
plt.ylabel("Average Final Score")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()
```

# **Scatter Plot — посещаемость и итоговая оценка / Attendance vs Final Score**

```python
plt.figure(figsize=(10, 6))

sns.scatterplot(
    data=df_clean,
    x="attendance",
    y="final_score"
)

plt.title("Attendance vs Final Score")
plt.xlabel("Attendance (%)")
plt.ylabel("Final Score")
plt.tight_layout()
plt.show()
```

# **Scatter Plot с линией регрессии / Scatter Plot with Regression Line**

```python
plt.figure(figsize=(10, 6))

sns.regplot(
    data=df_clean,
    x="attendance",
    y="final_score"
)

plt.title("Relationship Between Attendance and Final Score")
plt.xlabel("Attendance (%)")
plt.ylabel("Final Score")
plt.tight_layout()
plt.show()
```

# **Boxplot — распределение итоговых оценок по программам / Final Score Distribution by Program**

```python
plt.figure(figsize=(10, 6))

sns.boxplot(
    data=df_clean,
    x="program",
    y="final_score"
)

plt.title("Final Score Distribution by Program")
plt.xlabel("Program")
plt.ylabel("Final Score")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()
```

# **Histogram — распределение итоговых оценок / Final Score Distribution**

```python
plt.figure(figsize=(10, 6))

sns.histplot(
    data=df_clean,
    x="final_score",
    bins=15
)

plt.title("Distribution of Final Scores")
plt.xlabel("Final Score")
plt.ylabel("Number of Students")
plt.tight_layout()
plt.show()
```

# **Heatmap корреляционной матрицы / Correlation Matrix Heatmap**

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

correlation_matrix = df_clean[numeric_columns].corr()

correlation_matrix
```

```python
plt.figure(figsize=(10, 7))

sns.heatmap(
    correlation_matrix,
    annot=True,
    fmt=".2f"
)

plt.title("Correlation Matrix of Student Performance Features")
plt.tight_layout()
plt.show()
```