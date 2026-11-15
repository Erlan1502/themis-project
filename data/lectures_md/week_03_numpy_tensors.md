---
week_number: 3
topic_id: "week_03_numpy_tensors"
title: "Неделя 3: Библиотека NumPy и тензорные вычисления"
topic_name: "Архитектура ndarray, непрерывные блоки памяти C-order, векторизация, broadcasting и обработка изображений"
initial_prompt: "Привет! На третьей лекции мы перешли к библиотеке NumPy. За счет каких низкоуровневых механизмов памяти и архитектуры ndarray векторизованные операции работают быстрее стандартных циклов for, и как работает механизм broadcasting при выравнивании размерностей?"
source_files:
  - "Lecture_3_1_NumPy Library.ipynb"
  - "Lecture_3_2_NumPy Arrays for Image Processing.ipynb"
  - "Lecture_3_3_Numpy_Example_2026.ipynb"
glossary:
  - "about"
  - "above"
  - "absolute"
  - "across"
  - "add"
  - "added"
  - "adds"
  - "after"
  - "against"
  - "aggregations"
  - "allows"
  - "alternatively"
  - "broadcasting"
  - "dtype"
  - "matrix multiplication"
  - "ndarray"
  - "numpy"
  - "shape"
  - "strides"
  - "vectorization"
---

# Неделя 3: Библиотека NumPy и тензорные вычисления

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** Архитектура ndarray, непрерывные блоки памяти C-order, векторизация, broadcasting и обработка изображений

## Материалы ноутбука: Lecture_3_1_NumPy Library.ipynb

# **Lecture 3. NumPy Library and Fundamentals of Tensor Computations for Artificial Intelligence**

# Why do we need NumPy?

# A Python list can store data, but AI works with thousands and millions of numbers.

# Image        → millions of pixel values

# Audio        → thousands of samples

# Text         → embedding vectors

# Dataset      → matrices

# Neural Net   → tensors

# NumPy is a Python library for efficient numerical computing with multidimensional arrays.

# **1. Python List → NumPy Array**

```python
import numpy as np

A = np.array([85, 90, 88, 92])
print(A)
```

```python
print(type(A))
```

# ndarray = N-dimensional array

```python
A.itemsize # shows how many bytes of memory a single element of a NumPy array occupies.
```

```python
B = np.array([
    [1,  2,  3,  4],
    [5,  6,  7,  8],
    [9, 10, 11, 12],
    [13, 14, 15, 16]
])

print(B)
```

```python
B.flatten() # convert into a one-dimensional array
```

# flatten() creates a new array with its own data in memory, independent of the original array.

# **2. Dimensions**

#`ndim` stands for "number of dimensions"—that is, the number of dimensions (axes) of a NumPy array.

For example, grayscale image:

shape = (28, 28)

RGB image:

shape = (224, 224, 3)

Batch:

shape = (32, 224, 224, 3)

32   → number of images
224  → height
224  → width
3    → RGB channels

# **3. Creating arrays**
# np.zeros, np.ones, np.eye, np.arange, np.linspace.

```python
print(np.zeros((2,3)))
```

```python
print(np.ones((3,3)))
```

```python
print(np.eye(3))
```

```python
print(np.arange(0, 10, 2)) # step 2
```

```python
print(np.linspace(0, 2, 5)) # uniform division
```

```python
A[2:5, 2:7]
```

```python
row, col = 3, 5
A[:row, :col]
```

```python
row, col = 3, 5
A[row:, :col]
```

```python
A = np.arange(60).reshape(6, 10)
A[:, 4] = range(111, 700, 111)
A
```

```python
A = np.arange(60).reshape(6, 10)
A[1::2, :] = np.zeros((3, 10))
A
```

# **4. Arithmetic**

```python
x = np.array([1, 2, 3])
y = np.array([10, 20, 30])
```

```python
print(x + y)
```

```python
print(x * y) # element-wise multiplication
```

```python
print(x @ y) # matrix multiplication
```

```python
print(np.sqrt(x))
```

# Vectorization means applying operations to entire arrays without explicitly writing Python loops.

```python
np.random.seed(42)
print(np.random.rand(3,3))
```

# Creates a 3×3 two-dimensional array filled with random floating-point numbers from the range:[0, 1)

# **5.Statistical functions**

```python
data = np.array([5, 10, 15, 20, 25])
```

```python
print("Average:", data.mean())
```

```python
print("Standard deviation:", data.std())
```

```python
print("Maximum:", data.max(), "in position", data.argmax())
```

# **6.Vectorization**

# Vectorization in NumPy means performing an operation on an entire array at once, without writing an explicit for loop for each element.

# **Broadcasting**
# Broadcasting is a NumPy mechanism that allows us to perform operations on arrays with different but compatible shapes without manually copying the data.

```python
X = np.array([
    [10, 20, 30],
    [40, 50, 60]
])

bias = np.array([1, 2, 3])
print(X + bias)
```

# Y = X @ W + b represents a linear transformation: input data X is multiplied by model weights W, and bias b is added to produce output Y. The @ operator in NumPy performs matrix multiplication.

```python
X = np.array([
    [1.0, 2.0],
    [3.0, 4.0],
    [5.0, 6.0]
])
# model weight matrix
W = np.array([
    [0.5, 0.2],
    [0.1, 0.8]
])
# bias
b = np.array([ 1,  2])

Y = X @ W + b # @ - matrix multiplication

print(X @ W)
print()
print(Y)
print(type(Y))
```

# For example, if we have 32 samples, each with 100 features, and the layer should produce 64 output features:
# X = (32, 100)
# W = (100, 64)
# b = (64,)

[Иллюстрация к лекции]

---

## Материалы ноутбука: Lecture_3_2_NumPy Arrays for Image Processing.ipynb

# **NumPy Arrays for Image Processing**

# **Task: Represent and Process an Image as a NumPy Array**
# A digital image can be represented as a multidimensional NumPy array. Each pixel contains numerical values describing its intensity or color.

[Иллюстрация к лекции]

# **Step 1. Load an image**

```python
import numpy as np
import matplotlib.pyplot as plt

image = plt.imread("street.jpg")

plt.imshow(image)
plt.axis("off")
plt.show()

print(image[1, 2])
```

# **Step 2. Examine the image as a NumPy array**

```python
print("Type:", type(image))
print("Shape:", image.shape)
print("Dimensions:", image.ndim)
print("Number of elements:", image.size)
print("Data type:", image.dtype)
```

# **Step 3. Understand a pixel**

```python
pixel = image[100, 200]

print(pixel) # R, G, B
```

```python
red = image[100, 200, 0] # image[row, column, channel]
green = image[100, 200, 1]
blue = image[100, 200, 2]

print(red, green, blue)
```

# subplot() divides a figure into rows and columns and selects the position where the current plot will be displayed.

```python
gray = image.mean(axis=2) # mean value of the voltage axis — the RGB channel axes

plt.figure(figsize=(10, 8)) #creates a new figure (a canvas for plots or images).

plt.subplot(1, 2, 1)
plt.imshow(gray)
plt.title("Default colormap")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(gray, cmap="gray") # cmap = color map
plt.title("Gray colormap")
plt.axis("off")

plt.show()
```

# gray contains one numerical value for each pixel. Since it is not an RGB value ([R, G, B]), Matplotlib needs to decide which color should be used to display each numerical value. If cmap is not specified, Matplotlib uses the default colormap.

```python
bright = np.clip(image + 40, 0, 255)
plt.imshow(bright)
plt.axis("off")
plt.show()
```

# np.clip() limits array values to a specified minimum and maximum range. Values below the minimum are replaced by the minimum, and values above the maximum are replaced by the maximum.

# **Step 4. Crop an image using NumPy slicing**

```python
plt.imshow(image[500:2000, 1200:3500])
```

```python
plt.imshow(image[1000:2000])
```

```python
plt.imshow(image[:, 100:1200])
```

```python
plt.imshow(image[:1500, :2000])

plt.axis("off")
plt.show()
```

# **Step 5. Resize by NumPy slicing**

```python
small_image = image[::10, ::10]

plt.figure(figsize=(20, 8))

plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title("Original")
plt.axis("off")
print(image.shape)

plt.subplot(1, 2, 2)
plt.imshow(small_image)
plt.title("Reduced")
plt.axis("off")
print(small_image.shape)

plt.show()
```

# **Step 6. Flip an image**

```python
flipped = image[::-1, :]

plt.imshow(flipped)
plt.axis("off")
plt.show()
```

# **Step 7. Separate RGB channels**

```python
red = image[:, :, 0]
green = image[:, :, 1]
blue = image[:, :, 2]

print(red.shape)
```

# **Step 8. Visualize RGB channels**

```python
fig, axes = plt.subplots(1, 3, figsize=(12, 4))

axes[0].imshow(red, cmap="Reds")
axes[0].set_title("Red")

axes[1].imshow(green, cmap="Greens")
axes[1].set_title("Green")

axes[2].imshow(blue, cmap="Blues")
axes[2].set_title("Blue")

plt.show()
```

# **Step 9. Modify pixel values**

# We create a copy so that we do not change the original image array.

```python
modified = image.copy()

modified[500:1000, 1000:2000] = 255 # white pixels

plt.imshow(modified)
plt.axis("off")
plt.show()
```

# **Step 10. Normalize pixel values**

```python
normalized_image = image.astype(np.float32) / 255.0

print(normalized_image.dtype)
print(normalized_image.min())
print(normalized_image.max())
print(normalized_image[1,2])
```

# Original pixels

# 0 ─────────────── 255
#           ↓ /255
# 0.0 ───────────── 1.0

# **Step 11. Image as a Tensor**

# image.shape (H, W, C)
# 3D tensor:
# Dimension 0 → Height
# Dimension 1 → Width
# Dimension 2 → Channels

# **Step 12. Add a Batch Dimension**

# AI models usually process not just one image, but a batch of images

```python
batch = np.expand_dims(normalized_image, axis=0)

print("Image:", normalized_image.shape)
print("Batch:", batch.shape)
```

# 1   → number of images
#3000 → height
# 4000 → width
# 3   → channels

# If we have 32 images:
# 32   → number of images
#3000 → height
# 4000 → width
# 3   → channels

# np.expand_dims() adds a new dimension to an array. axis=0 adds the new dimension at the beginning, which can be used to create a batch of images.

```python
from PIL import Image
import numpy as np

images = []

for i in range(32):
    img = Image.open(f"images/image_{i}.jpg")
    img = img.resize((224, 224))
    img = np.array(img)
    images.append(img)

batch = np.stack(images)

print(batch.shape)
```

# In real machine learning, you usually do not load 32 images manually. A Dataset/DataLoader automatically takes, for example, 32 images from a large dataset and creates a batch. The next 32 images form the next batch, and so on. For example, if a dataset contains 3,200 images and batch_size = 32, one training epoch will contain 100 batches of 32 images.

---

## Материалы ноутбука: Lecture_3_3_Numpy_Example_2026.ipynb

# **Example “Online Courses and Ratings”**

# **Context**
# There are 20 users and 12 courses. Ratings are stored in a matrix R of size 20×12:
# 0 — the course is counted as “not taken”
# 1..5 — course rating

# **Goal:** to learn how to create arrays, fill them, modify data, select elements, and perform aggregations and transformations.

# **Пример «Онлайн-курсы и оценки»**
# **Контекст**
# Есть 20 пользователей и 12 курсов. Мы храним оценки в матрице R размера 20×12:
# 0 — курс counting как “не проходил”
# 1..5 — рейтинг

# **§2.Creation and Initialization of Arrays / Создание и заполнение массивов**

```python
import numpy as np
import matplotlib.pyplot as plt
```

# Create a ratings matrix:
# R = np.zeros((20, 12), dtype=np.int8)

# Create an array of course names (strings) and a user_id array:
# courses = np.array([...12 course names...])
# users = np.arange(1, 21)

```python
users = np.arange(1, n_users + 1)
courses = np.array([
    "Python Basics", "Data Analysis", "SQL", "ML Intro", "Deep Learning", "NLP",
    "Computer Vision", "Cloud", "Cybersecurity", "Project Mgmt", "DevOps", "GIS"
], dtype=object)

print("R shape:", R.shape, "dtype:", R.dtype)
print(users)
print(courses)
```

# Fill the data using different methods:
# randomly select 200 (user, course) pairs and assign a random rating from 1 to 5
# hint: np.random.default_rng(seed) + integers + indexing

# alternatively: manually fill the first 5 users using slicing

```python
print(R[:5, :3])

# Also manual fill via slicing for first 5 users (just to show)
R[:5, :3] = rng.integers(1, 6, size=(5, 3))
print(R[:5, :3])
```

# Save and load the array:
# np.save("ratings.npy", R)
# R2 = np.load("ratings.npy")
# Check:np.array_equal(R, R2)

# **§2. Indexing and Data Modification**

**Индексация и изменение данных**
5.	Выведите:
•	рейтинг пользователя u=10 по курсу c=3
•	все оценки пользователя u=10 (строка)
•	все оценки курса c=3 (столбец)
6.	Изменения:
•	пользователь 10 прошёл курс 3 и поставил 5 → обновите элемент
•	пользователь 7 удалил оценку курса 2 → верните в 0
•	всем пользователям в курсе 1 поднять оценку на 1, но не выше 5
o	подсказка: np.clip
7.	Поиск индексов:
•	найдите индексы всех ненулевых оценок пользователя 10
o	np.nonzero, np.where

# *Display*:
# • the rating of user u=10 for course c=3
# • all ratings of user u=10 (row)
# • all ratings of course c=3 (column)

# *Modifications:*
# • user 10 completed course 3 and gave a rating of 5 → update the element
# • user 7 removed the rating for course 2 → set it back to 0
# • increase the rating in course 1 by 1 for all users, but not above 5
# (hint: np.clip)

# *Index search:*
# • find the indices of all non-zero ratings of user 10
# (np.nonzero, np.where)

# np.nonzero() is designed to work with multidimensional arrays and returns the indices for each axis separately.

# **§3. Masks, Filtering, Selection**

[Иллюстрация к лекции]

[Иллюстрация к лекции]

```python
x = np.array([1, 5, 8, 2, 0])
mask = x > 2
print(mask)
print(x[mask])
A = np.array([
    [5, 0, 3],
    [0, 0, 4],
    [2, 1, 0]
])

mask1 = A != 0
print(mask1)

A[mask1]
```

**Маски, фильтрация, выборки**
Создайте булевы маски:
•	taken = R > 0
•	high = R >= 4
Посчитайте:
•	сколько курсов прошёл каждый пользователь → taken.sum(axis=1)
•	сколько пользователей прошли каждый курс → taken.sum(axis=0)
•	долю “высоких” оценок (>=4) по каждому курсу среди тех, кто проходил
o	аккуратно делить на количество прошедших (защита от деления на 0)
Фильтрация:
•	вывести список курсов, где средняя оценка (среди прошедших) >= 3
•	найти пользователей, которые прошли ≥ 8 курсов

# *Create boolean masks*:
# • taken = R > 0
# • high = R >= 4

# *Calculate:*
# • how many courses each user has completed → taken.sum(axis=1)
# • how many users completed each course → taken.sum(axis=0)
# • the share of “high” ratings (>=4) for each course among those who completed it
# o carefully divide by the number of completed entries (protection from division by zero)

[Иллюстрация к лекции]

# *Filtering*:
# • output the list of courses where the average rating (among completed users) is >= 3
# • find users who have completed ≥ 8 courses

# NaN нужен здесь, чтобы не учитывать отсутствующие оценки при вычислении среднего рейтинга курса.

# **§4. Aggregations and “Missing Values”  / Агрегации и “пропуски”**
Средние рейтинги:
•	средний рейтинг по пользователю (только по ненулевым)

•	средний рейтинг по курсу (только по ненулевым)

Подсказки:
•	вариант A: заменить 0 на np.nan, считать через np.nanmean

•	вариант B: считать сумму и делить на taken.sum, где taken.sum>0

Найдите:
•	топ-3 курса по средней оценке
•	курс с максимальным количеством прохождений

# **Average ratings:**
# • average rating per user (only non-zero values)
# • average rating per course (only non-zero values)

# **Hints:**
# • option A: replace 0 with np.nan and compute using np.nanmean
# • option B: compute the sum and divide by taken.sum, where taken.sum > 0

# **Find:**
# • the top-3 courses by average rating
# • the course with the highest number of completions

# **§5. Normalization and Transformations (Important for ML)/ Нормализация и преобразования (важно для ML)**

# **Нормализация** — это преобразование данных к стандартизированной шкале, чтобы убрать систематические смещения, сделать значения сопоставимыми и улучшить качество анализа, обучения моделей и сравнения объектов.

# *Что это означает по сути*

# Каждый пользователь имеет свою шкалу оценивания:
# один всегда ставит высокие оценки (4–5),
# другой — более строгий (2–3),
# третий — использует весь диапазон.
# 👉 Модель начинает путать вкусы с личным стилем оценивания.
# Нормализация устраняет этот эффект.

[Иллюстрация к лекции]

# *После нормализации:*

# 0 → нейтральное отношение
# > 0 → нравится больше среднего
# < 0 → нравится меньше среднего
# То есть оценки становятся относительными, а не абсолютными.

# **ПРИМЕР**
# User A: [5, 4, 5]
# mean = 4.67
# → centered = [0.33, -0.67, 0.33]

Задание: Нормализация оценок по пользователям (centered ratings):

•	R_centered[u, i] = R[u, i] - mean_u, но только там, где R>0

Стандартизация по курсам (z-score) для ненулевых:

•	использовать среднее и стандартное отклонение курса

•	защититься от std=0

Проверка:
•	среднее по пользователю после центрирования должно быть около 0 (по ненулевым)

# Task: User-Based Rating Normalization (Centered Ratings):

# R_centered[u, i] = R[u, i] - mean_u, but only where R > 0.

# Course-Based Standardization (Z-score) for Non-Zero Ratings:

# Use the mean and standard deviation for each course.
# Handle cases where std = 0 to avoid division by zero.

# Check:

# The mean rating for each user after centering should be approximately 0 (considering only non-zero ratings).

# **Стандартизация** по курсам (z-score normalization) — это метод приведения оценок/признаков к нулевому среднему и единичному стандартному отклонению для каждого курса (item / feature), чтобы сделать данные сопоставимыми по шкале и убрать масштабные и дисперсионные искажения.

# **Standardization** by courses (z-score normalization) is a method of transforming ratings/features to have a zero mean and unit standard deviation for each course (item/feature). This makes the data comparable across scales and reduces the effects of differences in scale and variance.

[Иллюстрация к лекции]

# Стандартизация по курсам (z-score) =
# преобразование оценок каждого курса в относительные значения (σ-единицы),
# устраняет масштаб и дисперсию,
# делает курсы статистически сопоставимыми,
# критически важна для similarity-based моделей.

# Course-based standardization (z-score) =
# transforming the ratings of each course into relative values (σ units),
# eliminates differences in scale and variance,
# makes courses statistically comparable,
# critically important for similarity-based models.

[Иллюстрация к лекции]

Example of Course-Based Standardization (Z-score)

Course A: ratings [5, 5, 4, 5]

1. Calculate the mean value μ:

μₐ = (5 + 5 + 4 + 5) / 4 = 19 / 4 = 4.75

2. Calculate the standard deviation σ:

σₐ = √[((5 − 4.75)² + (5 − 4.75)² + (4 − 4.75)² + (5 − 4.75)²) / 4]

σₐ = √[(0.0625 + 0.0625 + 0.5625 + 0.0625) / 4]

σₐ = √0.1875 ≈ 0.43

Result: μₐ = 4.75, σₐ ≈ 0.43

3. Z-score for a rating of 5 in Course A:

zₐ = (5 − 4.75) / 0.43 ≈ 0.58

Course B: ratings [3, 2, 3, 2]

1. Calculate the mean value μ:

μᵦ = (3 + 2 + 3 + 2) / 4 = 10 / 4 = 2.5

2. Calculate the standard deviation σ:

σᵦ = √[((3 − 2.5)² + (2 − 2.5)² + (3 − 2.5)² + (2 − 2.5)²) / 4]

σᵦ = √[(0.25 + 0.25 + 0.25 + 0.25) / 4]

σᵦ = √0.25 = 0.5

Result: μᵦ = 2.5, σᵦ = 0.5

3. Z-score for a rating of 3 in Course B:

zᵦ = (3 − 2.5) / 0.5 = 1.0

Interpretation

Although in absolute terms: 5 > 3

After standardization: zₐ = 0.58, zᵦ = 1.0

In relative terms, a rating of 3 in Course B is stronger than a rating of 5 in Course A, because it is 1 standard deviation above the mean for Course B, whereas a rating of 5 in Course A is only about 0.58 standard deviations above the mean.

# Course-based standardization (z-score) for non-zero values:
# • use the course mean and standard deviation
# • protect against std = 0

# Validation:
# • the mean per user after centering should be approximately 0 (for non-zero values only)

```python
print("Z-score (first 5 courses):")
print(np.round(R_z[:5, :], 3))
```