---
week_number: 4
topic_id: "week_04_pandas_data"
title: "Неделя 4: Анализ табличных данных с библиотекой Pandas"
topic_name: "Структуры данных Series и DataFrame, индексация loc/iloc, фильтрация, очистка и инспекция датасетов"
initial_prompt: "Привет! На четвертой лекции мы освоили основы Pandas. В чем заключается принципиальная разница между индексной выборкой loc и позиционной выборкой iloc, и почему векторная фильтрация через булевы маски предпочтительнее поэлементной итерации?"
source_files:
  - "Lecture_4_1_Library Pandas.ipynb"
  - "Lecture_4_2_Library Pandas.ipynb"
glossary:
  - "absolute"
  - "academic"
  - "accessor"
  - "accurate"
  - "across"
  - "additionally"
  - "admission"
  - "admission_date"
  - "admission_score"
  - "after"
  - "algorithms"
  - "allows"
  - "boolean indexing"
  - "data cleaning"
  - "dataframe"
  - "head"
  - "iloc"
  - "loc"
  - "pandas"
  - "series"
---

# Неделя 4: Анализ табличных данных с библиотекой Pandas

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** Структуры данных Series и DataFrame, индексация loc/iloc, фильтрация, очистка и инспекция датасетов

## Материалы ноутбука: Lecture_4_1_Library Pandas.ipynb

# **Lecture_4 Library Pandas.**

# **§1. Basics of Working with Data in Pandas**
# Pandas is a popular library for working with various types of tabular data.

```python
import pandas as pd
```

# ***1. Read a file directly using read_csv()***

# The index=False parameter means that the DataFrame index will not be saved as a separate column in the CSV file.

[Иллюстрация к лекции]

```python
df = pd.read_csv("University Students 2026.csv")

df.head()
```

| Поле / Field        | Описание / Description                                                                                                | Тип данных / Data Type |
| ------------------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| `student_id`        | **RU:** Уникальный идентификатор студента. **EN:** Unique student identifier.                                         | `string`               |
| `gender`            | **RU:** Пол студента (`Male`, `Female`). **EN:** Student's gender (`Male`, `Female`).                                 | `string`               |
| `city`              | **RU:** Город проживания студента. **EN:** Student's city of residence.                                               | `string`               |
| `program`           | **RU:** Образовательная программа студента. **EN:** Student's academic program.                                       | `string`               |
| `year`              | **RU:** Год обучения (1–4). **EN:** Year of study (1–4).                                                              | `integer`              |
| `admission_score`   | **RU:** Балл при поступлении. **EN:** Student's admission score.                                                      | `integer`              |
| `math_score`        | **RU:** Балл по математике. **EN:** Mathematics score.                                                                | `float`*               |
| `programming_score` | **RU:** Балл по программированию. **EN:** Programming score.                                                          | `float`*               |
| `english_score`     | **RU:** Балл по английскому языку. **EN:** English language score.                                                    | `float`*               |
| `attendance`        | **RU:** Посещаемость студента в процентах. **EN:** Student attendance percentage.                                     | `float`*               |
| `assignments`       | **RU:** Итоговый показатель выполнения заданий. **EN:** Student's assignment performance score.                       | `integer`              |
| `final_score`       | **RU:** Итоговый балл студента. **EN:** Student's final academic score.                                               | `integer`              |
| `scholarship`       | **RU:** Получает ли студент стипендию (`Yes`/`No`). **EN:** Whether the student receives a scholarship (`Yes`/`No`).  | `string`               |
| `dormitory`         | **RU:** Проживает ли студент в общежитии (`Yes`/`No`). **EN:** Whether the student lives in a dormitory (`Yes`/`No`). | `string`*              |
| `admission_date`    | **RU:** Дата поступления студента. **EN:** Student's admission date.                                                  | `date/string`          |

# ***2. Initial DataFrame Inspection***

# Before processing and analyzing data, we should examine the structure of the loaded DataFrame. At this stage, no data is modified.

# head() displays the first 5 rows of a DataFrame by default and provides a quick overview of the table structure.

```python
rows, columns = df.shape

print("Number of rows:", rows)
print("Number of columns:", columns)
```

# size returns the total number of elements (cells) in the DataFrame.

# index shows the structure of the DataFrame index. By default, Pandas creates a numerical index from 0 to 199.

# memory_usage() shows the memory used by each column. deep=True provides a more accurate estimate for columns containing string values.

```python
df.memory_usage(deep=True).sum()
```

# ***3.  Data Understanding and Data Quality Inspection/ Исследование содержимого и качества данных***

# The describe() method automatically calculates the main descriptive statistics for numerical columns. Метод describe() автоматически рассчитывает основные статистические характеристики числовых столбцов.

| Показатель | RU                           | EN                        |
| ---------- | ---------------------------- | ------------------------- |
| `count`    | количество непустых значений | number of non-null values |
| `mean`     | среднее арифметическое       | arithmetic mean           |
| `std`      | стандартное отклонение       | standard deviation        |
| `min`      | минимальное значение         | minimum value             |
| `25%`      | первый квартиль              | first quartile            |
| `50%`      | медиана                      | median                    |
| `75%`      | третий квартиль              | third quartile            |
| `max`      | максимальное значение        | maximum value             |

# Для категориальных столбцов Pandas дополнительно показывает:
# unique — количество уникальных значений;
# top — наиболее часто встречающееся значение;
# freq — сколько раз оно встречается.

# For categorical columns, Pandas additionally displays:
# unique — number of unique values;
# top — most frequent value;
# freq — frequency of the most common value.

# nunique() counts the number of distinct values in each column.

```python
df["program"].nunique()
```

# unique() returns an array containing the unique values of the selected column.

```python
df["year"].unique()
```

# value_counts() подсчитывает частоту каждого уникального значения.

# value_counts() counts the frequency of each unique value.

```python
df["city"].value_counts()
```

# normalize=True возвращает не абсолютное количество, а долю каждой категории.

# normalize=True returns the proportion of each category instead of the absolute count.

```python
df["program"].value_counts(normalize=True) * 100
```

```python
df["program"].value_counts(normalize=True).mul(100).round(2)
```

# isna() checks every DataFrame cell:
# True — the value is missing;
# False — the value is present.

```python
df.isna().sum()
```

# The first sum() counts missing values for each column, while the second sum() calculates the total number of missing values in the entire DataFrame.

# Поскольку True = 1, метод mean() вычисляет долю пропущенных значений.

# Since True = 1, the mean() method calculates the proportion of missing values.

```python
df.isna().mean().mul(100).round(2)
```

# notna() identifies non-missing values.

# duplicated() returns True when a row duplicates a previously occurring row.

# keep=False отмечает все строки, участвующие в дублировании.

# keep=False marks all rows involved in duplication.

```python
df[df["year"].duplicated(keep=False)]
```

```python
df[df["student_id"].duplicated(keep=False)]
```

```python
df.shape[0]
```

# Если оба значения равны 200, каждый студент имеет уникальный ID.

# Это позволяет проверить, соответствуют ли значения ожидаемому диапазону.

# This allows us to check whether values fall within the expected range.

# dropna=False заставляет value_counts() учитывать также пропущенные значения.
# dropna=False makes value_counts() include missing values in the frequency table.

# This table combines the main data quality characteristics and allows us to quickly identify potentially problematic columns.

# The dropna() method returns a DataFrame without rows containing at least one missing value.
# Метод dropna() возвращает DataFrame без строк, содержащих хотя бы одно пропущенное значение.

# аналог:

# inplace=True — означает, что результат записывается непосредственно в существующий df_clean, без создания нового DataFrame.

```python
df_clean.isna().sum()
```

```python
df_clean.isna().sum()
```

```python
df_clean.isna().sum()
```

# All missing values in math_score will be replaced with 0.

# Missing scores are replaced with the mean of the available scores.
# Пропущенные оценки заменяются средним значением существующих оценок.

```python
df_clean.isna().sum()
```

# **What is the difference between the mean and the median?**

# **Main Difference**

[Иллюстрация к лекции]

[Иллюстрация к лекции]

[Иллюстрация к лекции]

```python
print("Mean:", df_clean["math_score"].mean())
print("Median:", df_clean["math_score"].median())
```

```python
score_columns = [
    "math_score",
    "programming_score",
    "english_score",
    "attendance"
]

for column in score_columns:
    df_clean[column] = df_clean[column].fillna(
        df_clean[column].median()
    )
```

```python
df_clean.isna().sum()
```

# For each numerical column, missing values are replaced with the median of that column.
# Для каждого числового столбца пропущенные значения заменяются медианой этого столбца.

```python
df_clean[score_columns].isna().sum()
```

```python
df_clean["dormitory"].mode()
```

```python
df_clean["dormitory"] = df_clean["dormitory"].fillna(
    df_clean["dormitory"].mode()[0]
)
```

# For categorical features, missing values can be replaced with the most frequent category.
# Для категориальных признаков пропущенные значения можно заменить наиболее часто встречающейся категорией.

```python
df_clean.isna().sum().sum()
```

```python
df_clean = df_clean.drop_duplicates() # removal
```

```python
df_clean.drop_duplicates(inplace=True)
```

# d.to_datetime() преобразует строковые значения даты в специальный тип Pandas для работы с датой и временем.
# pd.to_datetime() converts date strings into the Pandas datetime data type.

# **Почему datetime важен? / Why Is Datetime Important?**

```python
df_clean["admission_date"].dt.year
```

```python
df_clean["admission_date"].dt.month
```

```python
df_clean["admission_date"].dt.day
```

# Аксессор .dt предоставляет специальные операции для Series, содержащих даты.
# The .dt accessor provides special operations for a Series containing datetime values.

# After filling the NaN values, some score columns may still have the float64 data type.

```python
df_clean["math_score"] = df_clean["math_score"].astype(int)
```

```python
columns = [
    "math_score",
    "programming_score",
    "english_score",
    "attendance"
]

df_clean[columns] = df_clean[columns].astype(int)
```

```python
df_clean.dtypes
```

# astype() is used to explicitly change the data type.

```python
df_clean["gender"] = df_clean["gender"].astype("category")
```

```python
categorical_columns = [
    "gender",
    "city",
    "program",
    "scholarship",
    "dormitory"
]

df_clean[categorical_columns] = (
    df_clean[categorical_columns]
    .astype("category")
)
```

```python
df_clean.dtypes
```

# The category data type is suitable for columns containing a limited set of repeated categorical values.

# Attendance must fall within a specific range.

```python
df_clean["attendance"].between(0, 100).all()
```

# between(0, 100) проверяет каждое значение, а all() определяет, выполняется ли условие для всех строк.
# between(0, 100) checks each value, while all() determines whether the condition is satisfied for every row.

```python
df_clean["math_score"].between(0, 100).all()
```

```python
df_clean["programming_score"].between(0, 100).all()
```

```python
df_clean["final_score"].between(0, 100).all()
```

```python
df_clean["scholarship"].isin(["Yes", "Nan"]).all()
```

# isin() проверяет, принадлежит ли каждое значение заданному набору допустимых значений.
# isin() checks whether each value belongs to a specified set of valid values.

```python
df_clean.isna().sum()
```

```python
df_clean.duplicated().sum()
```

```python
df_clean.dtypes
```

```python
df_clean.shape
```

```python
df_clean.to_csv(
    "University Students 2026 New.csv",
    index=False
)
```

---

## Материалы ноутбука: Lecture_4_2_Library Pandas.ipynb

# ***5. Выбор и фильтрация данных / Data Selection and Filtering***

# After loading, inspecting, and cleaning the data, the next important step is selecting the required rows and columns. Pandas allows us to select data by column names, indexes, positions, and logical conditions.

# После загрузки, исследования и очистки данных следующим важным этапом является выбор нужных строк и столбцов. Pandas позволяет выбирать данные по названиям столбцов, индексам, позициям и логическим условиям.

```python
import pandas as pd
```

```python
df_clean = pd.read_csv("University Students 2026 New.csv")
```

```python
type(df_clean["program"])
```

# A single DataFrame column is typically represented as a Series.

```python
type(df_clean[["program"]])
```

```python
df_clean[["student_id", "program", "final_score"]]
```

```python
df_clean[10:20]
```

```python
df_clean.loc[0:5]
```

# When using loc, the ending label of the range is included.

# We select rows with indexes from 0 to 5 and only the three specified columns.

```python
df_clean.loc[0:5, "student_id":"math_score"]
```

# This selects all columns from student_id through math_score, inclusive.

# iloc is used to select data by integer position, rather than by name or label.
# iloc используется для выбора данных по целочисленной позиции, а не по названию или метке.

```python
df_clean.iloc[1:5]
```

```python
df_clean.iloc[0:5, 0:3]
```

# **Main Difference Between loc and iloc**

[Иллюстрация к лекции]

```python
df_clean.loc[0:5, ["student_id", "program"]]
```

```python
df_clean.iloc[0:5, [0, 3]]
```

# These commands can produce similar results, but they use different selection mechanisms.

# Pandas evaluates the condition for each row and returns True or False.

```python
df_clean[high_score][["student_id", "final_score"]]
```

```python
df_clean.loc[high_score, ["student_id", "final_score"]]
```

# A Boolean mask is a sequence of True and False values that determines which rows should be selected.

```python
df_clean[df_clean["city"] == "Astana"]
```

# ~ инвертирует Boolean mask: True становится False, а False становится True.
# ~ reverses a Boolean mask: True becomes False, and False becomes True.

# isin() checks whether a value belongs to one of the elements in the specified list.
# isin() проверяет, принадлежит ли значение одному из элементов указанного списка.

# The ~ operator reverses the result of isin().

```python
df_clean[
    df_clean["final_score"].between(80, 90)
]
```

```python
df_clean.iloc[0, 11]
```

# The first example uses labels, while the second uses positions.

# First, we select students with a final score of at least 85, and then sort them from the highest to the lowest score.
# Сначала выбираем студентов с итоговым баллом не менее 85, затем сортируем их от максимального балла к минимальному.

```python
df_clean["average_score_1"] = df_clean[
    ["math_score", "programming_score", "english_score"]
].mean(axis=1)

df_clean.head()
```

# axis=1 означает, что среднее вычисляется по строкам, то есть отдельно для каждого студента.
# axis=1 means that the mean is calculated across columns for each row, i.e., separately for each student.

# **Создадим категорию академической успеваемости студента.**
# **Let's create an academic performance category based on the student's final score.**

```python
df_clean[
    ["student_id", "final_score", "performance_level"]
].head(10)
```

```python
df_clean["performance_level"].value_counts()
```

```python
df_clean.columns
```

# ***Масштабирование числовых признаков / Scaling Numerical Features***

# Numerical features may have different value ranges. Scaling transforms them into comparable scales. This is especially important before applying many machine learning algorithms.
# Числовые признаки могут иметь разные диапазоны значений. Масштабирование приводит признаки к сопоставимому масштабу. Это особенно важно перед использованием многих алгоритмов машинного обучения.

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler
```

```python
features = [
    "admission_score",
    "math_score",
    "programming_score",
    "english_score",
    "attendance",
    "assignments"
]
```

```python
standard_scaler = StandardScaler()
```

```python
standardized_data = standard_scaler.fit_transform(
    df_clean[features]
)
```

```python
df_standardized = pd.DataFrame(
    standardized_data,
    columns=features
)

df_standardized.head()
```

# The original df_clean remains unchanged.

# ***MinMaxScaler***

# MinMaxScaler преобразует значения в заданный диапазон. По умолчанию используется диапазон [0, 1].
# MinMaxScaler transforms values into a specified range. By default, the range is [0, 1].

[Иллюстрация к лекции]

```python
minmax_scaler = MinMaxScaler()

normalized_data = minmax_scaler.fit_transform(
    df_clean[features]
)
```

```python
df_normalized = pd.DataFrame(
    normalized_data,
    columns=features
)

df_normalized.head()
```

```python
df_normalized.min()
```

```python
df_normalized.max()
```

```python
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
```

```python
df_clean["scholarship"].value_counts()
```

```python
label_encoder = LabelEncoder()
```

```python
df_clean[
    ["scholarship", "scholarship_encoded"]
].head(10)
```

```python
label_encoder.classes_
```

# LabelEncoder assigns a numerical label to each category.

# sparse_output=False означает: вернуть обычный  NumPy-массив (dense array).В One-Hot Encoding обычно очень много нулей. Поэтому вместо хранения каждого 0 sparse matrix хранит данные более экономно.
# False → обычный массив, удобнее для демонстрации.
# True → разреженная матрица, эффективнее для больших данных.
# sparse_output=False means: return a regular  NumPy array.One-hot encoded data usually contain many zeros. A sparse matrix stores such data more efficiently instead of explicitly storing every zero.

```python
program_encoded_df = pd.DataFrame(
    program_encoded,
    columns=onehot_encoder.get_feature_names_out(["program"]),
    index=df_clean.index
)

program_encoded_df.head()
```

# A separate binary column is created for each category.