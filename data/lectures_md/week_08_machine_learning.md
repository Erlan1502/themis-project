---
week_number: 8
topic_id: "week_08_machine_learning"
title: "Неделя 8: Введение в классическое машинное обучение (ML)"
topic_name: "Парадигмы Supervised и Unsupervised Learning, разделение выборки train/test split, компромисс Bias-Variance, метрики оценки"
initial_prompt: "Привет! На восьмой лекции мы изучили основы классического машинного обучения. В чем заключается компромисс между смещением (bias) и дисперсией (variance), и почему высокая точность (accuracy) на обучающей выборке часто сигнализирует о переобучении модели?"
source_files:
  - "EN_Lecture_8_Machine_Learning.ipynb"
  - "RU_Lecture_8_Introduction to Machine Learning.ipynb"
glossary:
  - "above"
  - "absent"
  - "absolute"
  - "according"
  - "accuracy"
  - "accuracy_score"
  - "actual"
  - "additive"
  - "adjusted"
  - "advantages"
  - "affects"
  - "after"
  - "bias-variance tradeoff"
  - "decision tree"
  - "machine learning"
  - "overfitting"
  - "supervised learning"
  - "train test split"
  - "unsupervised learning"
---

# Неделя 8: Введение в классическое машинное обучение (ML)

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** Парадигмы Supervised и Unsupervised Learning, разделение выборки train/test split, компромисс Bias-Variance, метрики оценки

## Материалы ноутбука: EN_Lecture_8_Machine_Learning.ipynb

# **Lecture 9. Introduction to Machine Learning**

# **Machine Learning (ML)** is a field of artificial intelligence that enables systems to learn automatically from data and make predictions without explicitly programming every rule.

# Main idea: a model learns from training data and then makes predictions on new data.

# **§ 1. Machine Learning Tasks**

# **Classification**
# Goal: predict an object's category.
# Examples: spam detection, medical diagnosis, image recognition.
# **Regression**
# Goal: predict a numerical value.
# Examples: house price prediction, temperature forecasting, sales estimation.
# **Clustering**
# Goal: group similar objects together (unsupervised learning).
## Examples: customer segmentation, document grouping, image clustering.

# **§ 2. Main Models**

## **2.1 Linear Regression**
# Predicts a numerical variable based on a linear relationship.

[Иллюстрация к лекции]

### Linear regression: model, predictions, and residuals

A linear regression model fits a line to observed data:

$$\hat y_i=\theta_0+\theta_1x_i$$

- **Horizontal axis ($X$):** input feature $x_i$.
- **Vertical axis ($Y$):** observed target $y_i$.
- **Intercept ($\theta_0$):** where the fitted line crosses the vertical axis.
- **Slope ($\theta_1$):** change in the predicted value for a one-unit change in $x$.
- **Predicted value ($\hat y_i$):** point on the regression line.
- **Residual / prediction error:** $\varepsilon_i=y_i-\hat y_i$, the vertical distance from the observation to the line.

**Visual interpretation:** observed points appear above and below the fitted straight line; the residuals measure the vertical deviations from it.

https://habr.com/ru/companies/otus/articles/919258/

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Example data
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([3, 5, 7, 9, 11])

# Model
model = LinearRegression()
model.fit(X, y)

print("Coefficient:", model.coef_)
print("Intercept:", model.intercept_)
print("Prediction:", model.predict([[6]]))
```

We create a dataset: X contains the features (for example, the day number), and y is the target variable (for example, sales).
LinearRegression() fits a straight line describing the relationship between y and X.
model.coef_ is the slope coefficient (it shows how y changes when X increases).
model.intercept_ is the intercept (the value of y when X = 0).
predict([[6]]) predicts y when X = 6.

# **2.2 Logistic Regression**
# Used for binary classification.

[Иллюстрация к лекции]

### Logistic regression: probability curve and classification threshold

Logistic regression maps its linear score to a probability through an S-shaped sigmoid curve.

$$p(y=1\mid x)=\frac{1}{1+e^{-z}},\qquad z=w_0+\sum_{j=1}^{n}w_jx_j$$

| Predicted probability | With threshold 0.5 | Interpretation |
|---:|---|---|
| 0.30 | Class 0 | Below threshold |
| 0.50 | Decision boundary | Exactly at threshold |
| 0.80 | Class 1 | Above threshold |

**Graph description:** the horizontal axis represents the linear score; the vertical axis is probability from 0 to 1. The sigmoid approaches 0 on the left and 1 on the right, crossing 0.5 at $z=0$.

The **classification threshold** can be adjusted to balance different kinds of errors.

### 2. Mathematical model of logistic regression

For binary classification, the model calculates

$$P(y=1\mid\mathbf{x})=\frac{1}{1+e^{-(w_0+w_1x_1+w_2x_2+\cdots+w_nx_n)}}.$$

Here:
- $P(y=1\mid\mathbf{x})$: predicted probability of class 1;
- $x_1,\ldots,x_n$: input features;
- $w_0$: bias / intercept;
- $w_1,\ldots,w_n$: learned model weights;
- $e$: base of the natural logarithm.

With a 0.5 threshold, predict **class 1** when $p\geq0.5$, and **class 0** otherwise.

### 3. Sigmoid function

$$\sigma(z)=\frac{1}{1+e^{-z}},\qquad z=w_0+w_1x_1+\cdots+w_nx_n.$$

The sigmoid maps any real-valued score to a value strictly between **0 and 1**, so it can be interpreted as a predicted probability in logistic regression.

### 4. Training the logistic regression model

Model parameters $w_i$ are estimated using **maximum likelihood estimation (MLE)**, equivalently by minimizing a suitable log-loss (cross-entropy) objective.

Optimization is often performed with **gradient-based methods** such as gradient descent.

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Dataset
data = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)

# Convert to a DataFrame
df = pd.DataFrame(data.data, columns=data.feature_names)
df['target'] = data.target

# Display the first five rows
print(df.head())
print("---------------")

# Model
clf = LogisticRegression(max_iter=3500)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
```

We load the built-in breast cancer dataset. y = 0 indicates a malignant tumor; y = 1 indicates a benign tumor.

We split the data into training (X_train, y_train) and test (X_test, y_test) sets.

We train a logistic regression model: it estimates the probability that an observation belongs to a class.

We calculate classification accuracy.

# Implementing Logistic Regression from Scratch https://habr.com/ru/articles/803397/

# **Gradient Descent**

### Gradient descent: the basic idea

**Gradient descent** is a major optimization method used in machine learning and neural networks to minimize a **loss function**.

It iteratively updates model parameters (weights) in order to reduce prediction error.

**Intuition:** imagine standing on a hillside and trying to reach the lowest point. The negative gradient points in the direction of the steepest local decrease.

### Direction of gradient descent

Imagine starting at the top of a hill and moving toward a minimum.

To decrease the function most rapidly in the local linear approximation, move **opposite to the gradient**, the direction of steepest increase.

The step size is controlled by the **learning rate**.

### 2. Mathematical formulation of gradient descent

Let $J(\boldsymbol\theta)$ be a loss function and $\boldsymbol\theta=[w_1,w_2,\ldots,w_n]$ the model parameters. A gradient descent update is

$$\boxed{\boldsymbol\theta_{t+1}=\boldsymbol\theta_t-\alpha\nabla J(\boldsymbol\theta_t)}$$

where:
- $\alpha$: learning rate (step size);
- $\nabla J(\boldsymbol\theta)$: gradient, the vector of partial derivatives indicating the local direction of greatest increase.

**Worked example:** for $J(x)=x^2$, $J'(x)=2x$. Starting from $x=10$ with $\alpha=0.1$, the next value is $10-0.1\cdot20=8$.

### How the learning rate affects training

- If the learning rate $\alpha$ is **too large**, optimization steps can overshoot the minimum and may diverge.
- If $\alpha$ is **too small**, convergence can be slow and an optimizer may make little progress within a finite number of iterations.

The appropriate learning rate depends on the loss landscape, model, and optimizer.

### 4. Variants of gradient descent

| Variant | How the gradient is computed | Key characteristics |
|---|---|---|
| **Batch Gradient Descent** | Uses the entire training set for each update | Stable gradient estimate; can be computationally costly on large datasets |
| **Stochastic Gradient Descent (SGD)** | Updates after each individual training example | Frequent updates; noisy but often fast in practice |
| **Mini-Batch Gradient Descent** | Uses a small batch of examples per update | Common practical compromise between efficiency and gradient noise |

```python
import numpy as np

# Example: minimizing the function y = x^2
def f(x):
    return x**2

def grad_f(x):
    return 2*x

x = 10.0          # initial value
alpha = 0.1       # learning rate
for i in range(20):
    x = x - alpha * grad_f(x)
    print(f"Step {i+1}: x = {x:.4f}, f(x) = {f(x):.4f}")
```

# **2.3 K-Nearest Neighbors (KNN)**
# Classification using nearest neighbors.
# K-Nearest Neighbors (KNN) is a simple supervised machine learning algorithm for classification and regression. It assumes that similar observations tend to be close to one another. For a new data point, KNN finds the \(K\) closest neighbors in the training set and determines its class by majority vote (or averages their target values for regression).

[Иллюстрация к лекции]

Consider two classes represented by **triangles** and **diamonds** in a two-dimensional feature space. A new point is classified using nearby labeled points.

| Setting | How the prediction is made | Typical behavior |
|---|---|---|
| $k=1$ | Take the class of the **single nearest neighbor** | Very local; sensitive to noise |
| $k=5$ | Take the **majority class among the five nearest neighbors** | More smoothed; less sensitive to isolated mislabeled points |

**Diagram interpretation:** a small neighborhood around the query point contains one neighbor for $k=1$, whereas a larger neighborhood contains five points for $k=5$. The decision can change depending on their labels.

# **How It Works**
# Choose K: Select how many nearest neighbors will contribute to the prediction.
# Calculate distances: Measure the distance from the new observation to the training observations, for example using Euclidean distance.
# Find neighbors: Identify the K closest training observations.
# Classification: Assign the most frequent class among those K neighbors.
# Regression: Calculate the mean target value among the K nearest neighbors and use it as the prediction.

### Distance measures used in KNN

**Euclidean distance:**

$$d(\mathbf x,\mathbf y)=\sqrt{\sum_{i=1}^{n}(x_i-y_i)^2}$$

**Manhattan distance:**

$$d(\mathbf x,\mathbf y)=\sum_{i=1}^{n}|x_i-y_i|$$

**Cosine distance (for nonzero vectors; frequently used for text and embeddings):**

$$d_{\cos}(\mathbf x,\mathbf y)=1-\frac{\mathbf x\cdot\mathbf y}{\|\mathbf x\|\,\|\mathbf y\|}$$

**Note:** scale numeric features appropriately when using distance-based models; otherwise, features with larger numerical scales may dominate the distance.

# **The Hyperparameter K**
# A small K makes the model sensitive to noise (overfitting).
# A large K smooths the decision boundary (potential underfitting).
# An odd K (3, 5, 7) is often used in binary classification to reduce ties.

```python
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier

# Data
iris = load_iris()
X, y = iris.data, iris.target

#Convert to a DataFrame for convenience

df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['species'] = iris.target

# Display the first five rows
print(df.head())
print("---------------")
# Model
knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(X, y)

print("Prediction:", knn.predict([[5.1, 3.5, 1.4, 0.2]]))
```

Load the Iris dataset: measurements of iris flowers (petal and sepal lengths and widths).

Set n_neighbors=3, so the model uses the three closest neighbors.

Predict the species of a new flower with measurements [5.1, 3.5, 1.4, 0.2].

# **2.4 Decision Trees**
# A decision tree is a machine learning algorithm and visualization method used for classification and regression.
# It has a tree-like structure consisting of a root, splitting nodes (conditions), and leaves (predictions). It is easy to interpret, handles various data types, and typically requires little preprocessing.

# In decision analysis, three node types can be distinguished:
# Decision nodes represent choices to be made.
# Chance nodes represent uncertain outcomes and their probabilities.
# End nodes represent the final outcomes of decision paths.

# **Advantages:** easy to use, intuitive, and interpretable.
# **Disadvantages:** a single tree can overfit and may not capture every complex relationship.

# **How the Algorithm Works**
# Select the feature that best splits the observations according to the target.
## Divide the data into subsets.
# Repeat this procedure recursively for each subset.
# Stop growing the tree when:
# the maximum depth is reached;
# too few observations remain in a node;
# further splitting no longer improves the chosen criterion.

# Example: identify whether a fruit is an 🍎 apple, 🍌 banana, or 🍊 orange.

### Decision tree example: classify a fruit

The example uses the **color**, **weight**, and **texture** of a fruit.

```text
Color?
├── Red
│   └── Weight?
│       ├── < 190 g  → Apple
│       └── > 190 g  → Orange
├── Yellow           → Banana
└── Orange
    └── Texture?
        ├── Smooth   → Banana
        └── Rough    → Orange
```

Each internal node checks a feature, each branch corresponds to an outcome of the test, and each leaf gives a predicted class.

*This is the schematic teaching tree shown in the source illustration, not a botanically validated classifier; its splits are illustrative.*

```python
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier, plot_tree
import matplotlib.pyplot as plt

# Load data
iris = load_iris()
X = iris.data
y = iris.target

# Create model
tree = DecisionTreeClassifier(
    criterion="gini",
    max_depth=3,
    random_state=42
)

tree.fit(X, y)

# Visualization
plt.figure(figsize=(14, 7))

plot_tree(
    tree,
    feature_names=iris.feature_names,
    class_names=iris.target_names,
    filled=True,
    rounded=True,
    fontsize=11,
    impurity=False,
    proportion=False
)

plt.title("Decision Tree Classification – Iris Dataset", fontsize=15)
plt.show()
```

Build a decision tree with a maximum depth of 3 levels.

At each internal node, the tree tests a condition (for example, “petal length > 2.5?”).

Leaves contain the predicted classes (iris species).

plot_tree displays the structure of the tree.

# **2.5 Random Forest**

# Instead of building one decision tree (which may overfit),
# we build many trees, each producing its own prediction.
# Their predictions are averaged for regression; for classification, the majority class is selected.

# **How Random Forest Works**
# Bootstrap samples (random samples drawn with replacement) are created from the original dataset.
# A decision tree is trained on each sample and:
# considers randomly selected features at splitting nodes;
# is typically grown deeply without pruning.
# Each tree makes a prediction.
# Final prediction:
# classification — majority vote;
# regression — average prediction.

[Иллюстрация к лекции]

# **Training Three Trees**

### Tree 1 — study hours and attendance

**Features used:** `Study_hours` and `Attendance`.

Simplified rule from the teaching example:

```text
IF Study_hours > 3:
    Predict: Yes (passed)
ELSE:
    Predict: No (failed)
```

This is a deliberately simplified illustrative decision tree.

### Tree 2 — attendance and sleep before the exam

**Features used:** `Attendance` and `Sleep_before_exam`.

```text
IF Attendance > 80 AND Sleep_before_exam == 1:
    Predict: Yes (passed)
ELSE:
    Predict: No (failed)
```

### Tree 3 — study hours and sleep before the exam

**Features used:** `Study_hours` and `Sleep_before_exam`.

```text
IF Sleep_before_exam == 1:
    Predict: Yes (passed)
ELIF Study_hours > 4:
    Predict: Yes (passed)
ELSE:
    Predict: No (failed)
```

# Study hours - 2
# Attendance - 65
# Sleep before the exam - 1

### Majority vote from the three trees

For the sample student:
- `Study_hours = 2`
- `Attendance = 65`
- `Sleep_before_exam = 1`

| Decision tree | Prediction |
|---|---|
| Tree 1 | No |
| Tree 2 | No |
| Tree 3 | Yes |

**Votes:** No = 2, Yes = 1.  
**Final Random Forest prediction: Did not pass (No).**

The ensemble combines several individual model predictions through majority voting.

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load data
iris = load_iris()
X, y = iris.data, iris.target

# Split into training and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# Create the random forest model
rf = RandomForestClassifier(
    n_estimators=11,   # number of trees in the forest
    max_depth=None,     # tree depth (unlimited by default)
    random_state=42
)

# Train the model
rf.fit(X_train, y_train)

# Predictions
y_pred = rf.predict(X_test)

# Metrics
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification report:\n", classification_report(y_test, y_pred, target_names=iris.target_names))

# Feature importance
importances = rf.feature_importances_
for feature, importance in zip(iris.feature_names, importances):
    print(f"{feature}: {importance:.3f}")from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    ConfusionMatrixDisplay
)
from sklearn.tree import plot_tree

import matplotlib.pyplot as plt
import numpy as np

# 1. Load the Iris dataset
iris = load_iris()
X, y = iris.data, iris.target

# 2. Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# 3. Create the Random Forest model
rf = RandomForestClassifier(
    n_estimators=11,
    max_depth=3,
    min_samples_leaf=2,
    random_state=42
)

# 4. Train the model
rf.fit(X_train, y_train)

# 5. Make predictions
y_pred = rf.predict(X_test)

# 6. Evaluate the model
print("=== Random Forest Results ===")
print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=iris.target_names
))

# 7. Visualize one tree from the forest
plt.figure(figsize=(16, 8))

plot_tree(
    rf.estimators_[0],
    feature_names=iris.feature_names,
    class_names=list(iris.target_names),
    filled=True,
    rounded=True,
    fontsize=10,
    impurity=False
)

plt.title("One Decision Tree from Random Forest")
plt.tight_layout()
plt.show()

# 8. Feature Importance
importances = rf.feature_importances_
indices = np.argsort(importances)

plt.figure(figsize=(9, 5))
plt.barh(
    np.array(iris.feature_names)[indices],
    importances[indices]
)

plt.xlabel("Feature Importance")
plt.title("Random Forest - Feature Importance")
plt.tight_layout()
plt.show()

# 9. Confusion Matrix
ConfusionMatrixDisplay.from_predictions(
    y_test,
    y_pred,
    display_labels=iris.target_names,
    cmap="Blues",
    values_format="d"
)

plt.title("Random Forest - Confusion Matrix")
plt.tight_layout()
plt.show()
```

RandomForestClassifier is an ensemble of multiple decision trees.
Each tree is trained using random samples of observations and features.
The final classification uses majority voting among trees.
Parameters:
n_estimators=100 → build 100 trees.
max_depth=None → tree depth is not explicitly limited.
random_state=42 → ensure reproducibility.
feature_importances_ → estimates which features are more important for classification (for example, petal length may be more important than sepal width).

# **2.6 Support Vector Machine (SVM)**
# Support vector machines are used for classification and regression.
# In classification, the goal of a linear SVM is to find a separating hyperplane in an N-dimensional feature space, where N is the number of features. The method attempts to maximize the margin between the separating boundary and the nearest training observations.

# A larger margin generally helps the model generalize, although prediction performance also depends on the data, kernel, and hyperparameters. In a two-dimensional example, the separating boundary can be drawn as a line; observations on different sides may be assigned to different classes. Nonlinear kernels allow more complex decision boundaries.

[Иллюстрация к лекции]

### Support Vector Machine (SVM): margin and support vectors

An SVM classifier seeks a separating **hyperplane** between classes. For linearly separable observations, a maximum-margin SVM chooses the hyperplane that maximizes the margin to the nearest training points.

- **Separating hyperplane:** $\mathbf w^T\mathbf x+b=0$.
- **Margin boundaries (canonical scaling):** $\mathbf w^T\mathbf x+b=+1$ and $\mathbf w^T\mathbf x+b=-1$.
- **Support vectors:** the training points on or within the margin that determine the learned boundary.
- **Geometric margin width:** $2/\|\mathbf w\|$ for the hard-margin formulation.

**Diagram description:** two groups of points appear on opposite sides of a central separating line, with two parallel margin lines touching their nearest points.

# Example: SVM (SVC) for binary classification on the Breast Cancer dataset, with feature scaling and basic evaluation.

# **2.7 Naive Bayes**
# A Naive Bayes classifier is a simple, fast machine learning algorithm based on Bayes' theorem and the assumption of conditional independence between features given the class.
# It is frequently used for text, spam, review, and sentiment classification, as well as medical and risk-related applications.
# **Main Idea**
# The algorithm calculates the probability that an observation belongs to a class based on its feature values.

### Naive Bayes: Bayes' theorem

$$\boxed{P(C\mid X)=\frac{P(X\mid C)P(C)}{P(X)}}$$

where:
- $P(C\mid X)$: **posterior probability** that observation $X$ belongs to class $C$;
- $P(X\mid C)$: **likelihood** of observing $X$ given class $C$;
- $P(C)$: **prior probability** of class $C$;
- $P(X)$: **evidence**, the marginal probability of observing $X$.

For classification, the shared denominator $P(X)$ can be omitted when comparing class scores.

# The algorithm is called “naive” because it assumes conditional independence of features given the class, which rarely holds exactly in real datasets.

# **Example:** Suppose we classify emails as spam or not spam.
# Our features indicate whether these words appear: “buy”, “discount”, and “meeting”.
# *An email contains “buy” and “meeting”. Is it spam?*

### Email classification example: training dataset

Features are binary indicators of whether each word appears in an email.

| Email | "buy" | "discount" | "meeting" | Class |
|---:|---:|---:|---:|---|
| 1 | 1 | 1 | 0 | Spam |
| 2 | 1 | 1 | 1 | Spam |
| 3 | 0 | 0 | 1 | Not spam |
| 4 | 0 | 1 | 1 | Not spam |

Here **1** indicates that a word is present, and **0** indicates that it is absent.

### Worked Naive Bayes calculation

**1. Class prior probabilities:**

$$P(\mathrm{Spam})=\frac24=0.5,\qquad P(\mathrm{NotSpam})=\frac24=0.5.$$

**2. Conditional feature probabilities (estimated from the four training messages):**

- $P(\text{buy}=1\mid\mathrm{Spam})=2/2=1.0$
- $P(\text{meeting}=1\mid\mathrm{Spam})=1/2=0.5$
- $P(\text{buy}=1\mid\mathrm{NotSpam})=0/2=0$
- $P(\text{meeting}=1\mid\mathrm{NotSpam})=2/2=1.0$

**3. Compare unnormalized class scores** for a new message where `buy=1` and `meeting=1` (using these two features):

$$\mathrm{Score(Spam)}=1.0\times0.5\times0.5=0.25$$

$$\mathrm{Score(NotSpam)}=0\times1.0\times0.5=0$$

**Result: predict Spam**, since its score is higher.

*This reproduces the illustration's unsmoothed, two-feature demonstration. In practical text classifiers, Laplace/additive smoothing is normally used to avoid zero feature probabilities.*

# **Example:** Implementing a Naive Bayes classifier on a text dataset. We use MultinomialNB, which is well suited to text analysis (the selected dataset contains two newsgroup topics).

```python
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report

# Load a small text dataset (use only two categories for this example)
categories = ['rec.sport.hockey', 'sci.space']
data = fetch_20newsgroups(subset='all', categories=categories)

# Features and target variable
X, y = data.data, data.target

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

# Text vectorization (Bag of Words)
vectorizer = CountVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Naive Bayes model
nb = MultinomialNB()
nb.fit(X_train_vec, y_train)

# Predictions
y_pred = nb.predict(X_test_vec)

# Metrics
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification report:\n", classification_report(y_test, y_pred, target_names=categories))
```

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report

# Load the Iris dataset
iris = load_iris()
X, y = iris.data, iris.target

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# Create a Gaussian Naive Bayes model
gnb = GaussianNB()
gnb.fit(X_train, y_train)

# Predictions
y_pred = gnb.predict(X_test)

# Metrics
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification report:\n", classification_report(y_test, y_pred, target_names=iris.target_names))
```

# **§ 3. Model Evaluation Metrics**

# **Classification Metrics**

[Иллюстрация к лекции]

[Иллюстрация к лекции]

```python
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

y_true = [1, 0, 1, 1, 0, 1, 0]
y_pred = [1, 0, 1, 0, 0, 1, 1]

print("Accuracy:", accuracy_score(y_true, y_pred))
print("Precision:", precision_score(y_true, y_pred))
print("Recall:", recall_score(y_true, y_pred))
print("F1:", f1_score(y_true, y_pred))
print("ROC-AUC:", roc_auc_score(y_true, y_pred))
```

# **Regression Metrics**

# MAE (Mean Absolute Error)
# Definition:
# MAE measures the average absolute difference between a model's predictions and the actual values.
# It is one of the simplest and most intuitive metrics for regression tasks.

### Mean Absolute Error (MAE)

$$\boxed{MAE=\frac{1}{N}\sum_{i=1}^{N}|y_i-\hat y_i|}$$

where:
- $N$: number of observations;
- $y_i$: actual value;
- $\hat y_i$: predicted value.

MAE measures the average absolute prediction error in the **same units as the target**.

[Иллюстрация к лекции]

```python
from sklearn.metrics import mean_absolute_error

y_true = [3, -0.5, 2, 7]
y_pred = [2.5, 0.0, 2, 8]

mae = mean_absolute_error(y_true, y_pred)
print("MAE =", mae)
```

# **Clustering Metrics**

### Clustering evaluation metrics

| Metric | Typical range | What it evaluates |
|---|---|---|
| **Silhouette Score** | $-1$ to $1$ | Higher values often indicate better-separated, more cohesive clusters |
| **Davies–Bouldin Index** | $\geq0$ | Lower values are generally better, indicating more compact and separated clusters |
| **Calinski–Harabasz Index** | $\geq0$ | Higher values often indicate better-defined clusters under this criterion |

No single metric proves that a clustering is meaningful for the application.

# **How to Choose a Metric**

### How to choose an evaluation metric

| Situation | Suggested metric(s) |
|---|---|
| Balanced classes | Accuracy |
| Imbalanced classes | F1, ROC-AUC (also examine per-class metrics) |
| False positives are especially costly | Precision |
| False negatives are especially costly | Recall |
| Continuous-value predictions | RMSE, MAE, $R^2$ |
| Unsupervised clustering | Silhouette Score, Davies–Bouldin Index |

**Selection principle:** choose metrics that reflect the real cost of errors and the goals of the application.

# **§ 4. Introduction to Scikit-learn**
# Scikit-learn is a widely used Python machine learning library built on NumPy, SciPy, and Matplotlib.
# It provides tools for data preprocessing, model training, evaluation, hyperparameter tuning, and pipelines.

# Features:
# Load standard datasets.
# Preprocess data (scaling, categorical encoding).
# Use classical ML models (regression, classification, clustering).
# Evaluate models and perform cross-validation.
# Build pipelines.

### Scikit-learn: key modules and features (part 1)

| Area | Capabilities and examples |
|---|---|
| **Data preprocessing** (`sklearn.preprocessing`) | Feature scaling, normalization, categorical encoding (`LabelEncoder`, `OneHotEncoder`); use `SimpleImputer` from `sklearn.impute` for missing values and `train_test_split` from `sklearn.model_selection` for train/test separation |
| **Estimators** | Common interface (`fit`, `predict`) for classification, regression, clustering and dimensionality reduction |
| **Classification** | `LogisticRegression`, `SVC`, `DecisionTreeClassifier`, `RandomForestClassifier`, `KNeighborsClassifier`, `GaussianNB`, `GradientBoostingClassifier`, `VotingClassifier` |
| **Regression** | `LinearRegression`, `Ridge`, `Lasso`, `SVR`, `DecisionTreeRegressor`, `RandomForestRegressor` |

### Scikit-learn: key modules and features (part 2)

| Area | Capabilities and examples |
|---|---|
| **Clustering** | `KMeans`, `DBSCAN`, `AgglomerativeClustering`, `MeanShift` |
| **Dimensionality reduction** | `PCA`, `TSNE`, `TruncatedSVD` |
| **Ensemble methods** | Bagging, boosting, stacking, and voting |
| **Metrics and model evaluation** | `accuracy_score`, `precision_score`, `recall_score`, `f1_score`, `roc_auc_score`, `mean_squared_error`, `r2_score` |
| **Cross-validation and hyperparameter search** | `GridSearchCV`, `RandomizedSearchCV`, `cross_val_score`, `StratifiedKFold` |
| **Pipelines** | `Pipeline` combines preprocessing and modeling steps into one reusable workflow, helping prevent data leakage |

---

## Материалы ноутбука: RU_Lecture_8_Introduction to Machine Learning.ipynb

# **Lecture 8. Introduction to Machine Learning**

# **Машинное обучение (Machine Learning, ML)** – это область искусственного интеллекта, которая позволяет системам автоматически учиться на данных и делать предсказания без явного программирования всех правил.

# Основная идея: модель обучается на обучающем наборе данных и затем делает предсказания на новых данных.

# **§ 1. Задачи машинного обучения**

# **Классификация (Classification)**
# Цель: предсказать категорию объекта.
# Примеры: определение спама, диагностика заболеваний, распознавание изображений.
# **Регрессия (Regression)**
# Цель: предсказать числовое значение.
# Примеры: прогноз цен на жильё, предсказание температуры, оценка продаж.
# **Кластеризация (Clustering)**
# Цель: объединить объекты в группы (без учителя).
## Примеры: сегментация клиентов, группировка документов, кластеризация изображений.

# **§ 2. Основные модели**

## **2.1 Линейная регрессия**
# Прогнозирует числовую переменную на основе линейной зависимости.

[Иллюстрация к лекции]

https://habr.com/ru/companies/otus/articles/919258/

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Пример данных
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([3, 5, 7, 9, 11])

# Модель
model = LinearRegression()
model.fit(X, y)

print("Коэффициент:", model.coef_)
print("Свободный член:", model.intercept_)
print("Прогноз:", model.predict([[6]]))
```

Мы создаём набор данных: X — это признаки (например, номер дня), y — это целевая переменная (например, продажи).
LinearRegression() строит прямую, которая описывает зависимость y от X.
model.coef_ — коэффициент наклона линии (показывает, как меняется y, если увеличить X).
model.intercept_ — сдвиг (значение y при X=0).
predict([[6]]) — прогноз значения y при X=6.

# **2.2 Логистическая регрессия**
# Используется для бинарной классификации.

[Иллюстрация к лекции]
https://cloud.vk.com/blog/samye-populyarnye-algoritmy-mashinnogo-obucheniya/

[Иллюстрация к лекции]

[Иллюстрация к лекции]

[Иллюстрация к лекции]

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Датасет
data = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)

# Переводим в DataFrame
df = pd.DataFrame(data.data, columns=data.feature_names)
df['target'] = data.target

# Смотрим первые 5 строк
print(df.head())
print("---------------")

# Модель
clf = LogisticRegression(max_iter=3500)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
```

Загружаем готовый датасет о раке молочной железы. y=0 — злокачественная опухоль, y=1 — доброкачественная.

Делим данные на тренировочные (X_train, y_train) и тестовые (X_test, y_test).

Обучаем логистическую регрессию: она выдаёт вероятность принадлежности объекта к классу.

Считаем точность (accuracy).

# Программирование логистической регрессии с нуля https://habr.com/ru/articles/803397/

# **Градиентный спуск (Gradient Descent)**

[Иллюстрация к лекции]

[Иллюстрация к лекции]

[Иллюстрация к лекции]

[Иллюстрация к лекции]

[Иллюстрация к лекции]

```python
import numpy as np

# Пример: минимизация функции y = x^2
def f(x):
    return x**2

def grad_f(x):
    return 2*x

x = 10.0          # начальное значение
alpha = 0.1       # скорость обучения
for i in range(20):
    x = x - alpha * grad_f(x)
    print(f"Шаг {i+1}: x = {x:.4f}, f(x) = {f(x):.4f}")
```

# **2.3 K-Nearest Neighbors (KNN)**
# Классификация по ближайшим соседям.
# Алгоритм K-ближайших соседей (KNN) — это простой алгоритм машинного обучения с учителем для классификации и регрессии. Он работает по принципу, что похожие объекты находятся близко друг к другу. Для новой точки данных KNN находит \(K\) ближайших соседей из обучающих данных и определяет ее класс по большинству голосов этих соседей (в случае регрессии — усредняет их значения).

[Иллюстрация к лекции]

# **Принцип работы**
# Выбор значения K: Выбирается количество ближайших соседей K, на основе которых будет приниматься решение.
# Вычисление расстояния: Алгоритм рассчитывает расстояние от новой точки данных до всех точек в обучающем наборе с помощью метрики, такой как евклидово расстояние.
# Поиск соседей: Определяются K точек из обучающего набора, которые находятся ближе всего к новой точке.
# Классификация (для задач классификации): Определяется класс, который встречается чаще всего среди этих K соседей. Новая точка получает этот класс.
# Регрессия (для задач регрессии): Вычисляется среднее значение целевой переменной всех K ближайших соседей. Новой точке присваивается это среднее значение.

[Иллюстрация к лекции]

# **Гиперпараметр K**
# Малое значение K → модель чувствительна к шуму (переобучение).
# Большое значение K → сглаживает границы между классами (недообучение).
# Обычно выбирают нечётное K (3, 5, 7), чтобы избежать ничьих.

```python
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier

# Данные
iris = load_iris()
X, y = iris.data, iris.target

#Переводим в DataFrame для удобства

df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['species'] = iris.target

# Показываем первые 5 строк
print(df.head())
print("---------------")
# Модель
knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(X, y)

print("Прогноз:", knn.predict([[5.1, 3.5, 1.4, 0.2]]))
```

Загружаем датасет iris: данные о цветках ириса (длина/ширина лепестков и чашелистиков).

Устанавливаем n_neighbors=3 → модель смотрит на 3 ближайших соседа.

Прогнозируем, к какому виду относится новый цветок с параметрами [5.1, 3.5, 1.4, 0.2].

# **2.4 Decision Trees (Деревья решений)**
# Дерево решений — это алгоритм машинного обучения и метод визуализации, который используется для классификации и регрессии.
# Он представляет собой древовидную структуру с корнем, узлами-ветвлениями (условиями) и листьями (решениями или прогнозами). Этот метод отличается простотой интерпретации, гибкостью в работе с различными типами данных и минимальными требованиями к предварительной обработке.

# В дереве решений могут быть три разных типа узлов:
# Decision nodes — узлы решения, они показывают решение, которое нужно принять.
# Chance nodes — вероятностные узлы, демонстрируют вероятность определенных результатов.
# End nodes — замыкающие узлы, показывают конечный результат пути решения.

# **Плюсы.** Надежность, простота применения, интуитивность.
# **Минусы.** Ограниченная сфера применения. Далеко не все модели можно описывать деревьями.

# **Как работает алгоритм**
# Выбирается признак, который лучше всего делит данные по целевой переменной.
## Данные разбиваются на подмножества.
# Для каждого подмножества повторяется процесс (рекурсивно).
# Строительство дерева прекращается, когда:
# достигается максимальная глубина;
# в узле мало объектов;
# дальнейшее разделение не улучшает качество.

# Пример: определить, какой это фрукт — 🍎 яблоко, 🍌 банан или 🍊 апельсин.

[Иллюстрация к лекции]

```python
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier, plot_tree
import matplotlib.pyplot as plt

# Загрузка данных
iris = load_iris()
X = iris.data
y = iris.target

# Создание модели
tree = DecisionTreeClassifier(
    criterion="gini",
    max_depth=3,
    random_state=42
)

tree.fit(X, y)

# Визуализация
plt.figure(figsize=(14, 7))

plot_tree(
    tree,
    feature_names=iris.feature_names,
    class_names=iris.target_names,
    filled=True,
    rounded=True,
    fontsize=11,
    impurity=False,
    proportion=False
)

plt.title("Decision Tree Classification – Iris Dataset", fontsize=15)
plt.show()
```

Строим дерево решений глубиной до 3 уровней.

На каждом узле дерево задаёт вопрос (например: «длина лепестка > 2.5?»).

В листьях — классы (виды ирисов).

plot_tree рисует графическое представление дерева.

# **2.5 Random Forest (Алгоритм случайного леса)**

# Вместо того чтобы строить одно дерево (которое может переобучиться),
# мы строим множество деревьев, каждое из которых принимает своё решение.
# Затем результаты усредняются (в регрессии) или выбирается класс большинства (в классификации).

# **Как работает Random Forest**
# Из исходного набора данных создаются bootstrap-выборки (случайные подмножества).
# Для каждой выборки строится дерево решений, которое:
# выбирает случайные признаки для каждого узла;
# строится без «обрезки» (deep tree).
# Каждое дерево делает предсказание.
# Итоговое решение:
# при классификации — голосование большинства;
# при регрессии — среднее значение.

[Иллюстрация к лекции]

# Задача: по данным о студентах предсказать, сдал ли студент экзамен (Сдал или Не сдал).
# Признаки:
# Часы_подготовки — количество часов, потраченных на подготовку;
# Посещаемость — процент посещённых занятий;
# Сон_перед_экзаменом — спал ли студент перед экзаменом (1 — да, 0 — нет).

# **Обучение трёх деревьев**

[Иллюстрация к лекции]

[Иллюстрация к лекции]

[Иллюстрация к лекции]

# Часы подготовки - 2
# Посещаемость - 65
# Сон перед экзаменом - 1

[Иллюстрация к лекции]

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    ConfusionMatrixDisplay
)
from sklearn.tree import plot_tree

import matplotlib.pyplot as plt
import numpy as np

# 1. Load the Iris dataset
iris = load_iris()
X, y = iris.data, iris.target

# 2. Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# 3. Create the Random Forest model
rf = RandomForestClassifier(
    n_estimators=11,
    max_depth=3,
    min_samples_leaf=2,
    random_state=42
)

# 4. Train the model
rf.fit(X_train, y_train)

# 5. Make predictions
y_pred = rf.predict(X_test)

# 6. Evaluate the model
print("=== Random Forest Results ===")
print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=iris.target_names
))

# 7. Visualize one tree from the forest
plt.figure(figsize=(16, 8))

plot_tree(
    rf.estimators_[0],
    feature_names=iris.feature_names,
    class_names=list(iris.target_names),
    filled=True,
    rounded=True,
    fontsize=10,
    impurity=False
)

plt.title("One Decision Tree from Random Forest")
plt.tight_layout()
plt.show()

# 8. Feature Importance
importances = rf.feature_importances_
indices = np.argsort(importances)

plt.figure(figsize=(9, 5))
plt.barh(
    np.array(iris.feature_names)[indices],
    importances[indices]
)

plt.xlabel("Feature Importance")
plt.title("Random Forest - Feature Importance")
plt.tight_layout()
plt.show()

# 9. Confusion Matrix
ConfusionMatrixDisplay.from_predictions(
    y_test,
    y_pred,
    display_labels=iris.target_names,
    cmap="Blues",
    values_format="d"
)

plt.title("Random Forest - Confusion Matrix")
plt.tight_layout()
plt.show()
```

# Precision — какая доля объектов, предсказанных как данный класс, действительно относится к нему.

# Recall — какую долю объектов данного класса модель смогла правильно обнаружить.

# F1-score — гармоническое среднее Precision и Recall.

# Support — фактическое количество объектов каждого класса в тестовой выборке.

# Setosa — F1 = 1.00. Все 12 цветков правильно классифицированы. Ошибок нет.
# Versicolor — F1 = 0.89. Из 13 цветков правильно определены 12, один классифицирован неправильно. При этом некоторые цветки другого вида ошибочно отнесены к Versicolor, поэтому Precision ниже Recall.
# Virginica — F1 = 0.88. Из 13 цветков правильно определены 11, два классифицированы неправильно.
# Таким образом, модель допустила всего 3 ошибки.
# - Macro Avg = 0.92 — среднее значение метрики по трём классам без учёта количества объектов.
# - Weighted Avg = 0.92 — среднее значение с учётом количества объектов каждого класса.

# **2.6 SVM (машина опорных векторов)**
# Машины опорных векторов применяют для задач регрессии и классификации.
# Цель SVM — построить в N-мерном пространстве гиперплоскость, которая однозначно разделяет данные на классы. N соответствует количеству признаков, а гиперплоскость ― это прямая, которая разделяет объекты на эти классы. Расстояние от неё до каждого класса должно быть максимальным, так как от этого зависит точность.

# Логика SVM такая: чем больше расстояние между гиперплоскостью и объектами, то есть зазор, тем точнее предсказание. Гиперплоскость графически изображается в виде линии. Точки данных по разным сторонам от линии относятся к разным классам. Сложность заключается в том, чтобы найти правильную линию, которая будет разделять объекты на классы.

[Иллюстрация к лекции]

# Пример SVM (SVC) на бинарном датасете Breast Cancer с масштабированием признаков и базовой оценкой качества.

# Pipeline — инструмент библиотеки Scikit-learn, который объединяет несколько последовательных операций обработки данных и обучения модели.Преимущество Pipeline заключается в том, что масштабирование и обучение выполняются автоматически в правильной последовательности.

# **2.7 Наивный Байес (Naive Bayes)**
# Наивный Байесовский классификатор (Naive Bayes) — это простой и быстрый алгоритм машинного обучения, основанный на теореме Байеса и предположении независимости признаков.
# Он часто используется в задачах классификации текстов, спама, отзывов и эмоций, а также в медицине и прогнозировании рисков.
# **Основная идея.**
# Алгоритм вычисляет вероятность того, что объект принадлежит к определённому классу, исходя из значений его признаков.

[Иллюстрация к лекции]

# Алгоритм называется «наивным», потому что предполагает, что все признаки независимы друг от друга, хотя в реальности это редко так.

# **Пример.** Допустим, мы классифицируем письма как спам или не спам.
# У нас есть признаки — наличие слов: “купить”, “скидка”, “встреча”.
# *Письмо содержит “купить” и “встреча”. Спам или нет?*

[Иллюстрация к лекции]

[Иллюстрация к лекции]

# **Пример** реализации Наивного Байесовского классификатора (Naive Bayes) на датасете с текстами (определение спам / не спам). Мы воспользуемся MultinomialNB, который хорошо подходит для анализа текстов.

```python
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    ConfusionMatrixDisplay
)

import matplotlib.pyplot as plt
import numpy as np

# 1. Load text documents
categories = ["rec.sport.hockey", "sci.space"]

data = fetch_20newsgroups(
    subset="all",
    categories=categories,
    remove=("headers", "footers", "quotes")
)

X, y = data.data, data.target

print("Number of documents:", len(X))
print("Categories:", data.target_names)

# 2. Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# 3. Convert texts to word-frequency vectors
vectorizer = CountVectorizer(
    stop_words="english",
    min_df=2
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

print("Vocabulary size:",
      len(vectorizer.get_feature_names_out()))

# 4. Train Naive Bayes classifier
nb = MultinomialNB(alpha=1.0)
nb.fit(X_train_vec, y_train)

# 5. Predict classes
y_pred = nb.predict(X_test_vec)

# 6. Evaluate the model
print("\nAccuracy:",
      round(accuracy_score(y_test, y_pred), 4))

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=data.target_names
))

# 7. Visualize Confusion Matrix
ConfusionMatrixDisplay.from_predictions(
    y_test,
    y_pred,
    display_labels=data.target_names,
    cmap="Blues",
    values_format="d"
)

plt.title("Naive Bayes - Confusion Matrix")
plt.tight_layout()
plt.show()

# 8. Most characteristic words for each category
feature_names = vectorizer.get_feature_names_out()

# Compare class-conditional log probabilities
log_prob = nb.feature_log_prob_

for class_id, class_name in enumerate(data.target_names):
    other_id = 1 - class_id
    scores = log_prob[class_id] - log_prob[other_id]
    top_indices = np.argsort(scores)[-10:][::-1]

    print(f"\nTop words for {class_name}:")
    print(", ".join(feature_names[top_indices]))

# 9. Classify new texts
new_texts = [
    "The hockey team won the championship game.",
    "NASA launched a spacecraft into orbit."
]

new_vectors = vectorizer.transform(new_texts)
predictions = nb.predict(new_vectors)
probabilities = nb.predict_proba(new_vectors)

for text, label, probs in zip(
    new_texts, predictions, probabilities
):
    print("\nText:", text)
    print("Predicted category:", data.target_names[label])

    for name, probability in zip(
        data.target_names, probs
    ):
        print(f"{name}: {probability:.3f}")
```

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report

# Загружаем датасет Iris
iris = load_iris()
X, y = iris.data, iris.target

# Разделение на train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# Создаём модель Наивного Байеса (с нормальным распределением)
gnb = GaussianNB()
gnb.fit(X_train, y_train)

# Предсказания
y_pred = gnb.predict(X_test)

# Метрики
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification report:\n", classification_report(y_test, y_pred, target_names=iris.target_names))
```

# **§ 3. Метрики качества моделей**

# **Метрики для задач классификации**

[Иллюстрация к лекции]

[Иллюстрация к лекции]

```python
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

y_true = [1, 0, 1, 1, 0, 1, 0]
y_pred = [1, 0, 1, 0, 0, 1, 1]

print("Accuracy:", accuracy_score(y_true, y_pred))
print("Precision:", precision_score(y_true, y_pred))
print("Recall:", recall_score(y_true, y_pred))
print("F1:", f1_score(y_true, y_pred))
print("ROC-AUC:", roc_auc_score(y_true, y_pred))
```

# **Метрики для задач регрессии**

# MAE (Mean Absolute Error) — Средняя абсолютная ошибка
# Определение:
# MAE измеряет среднее абсолютное отклонение предсказаний модели от фактических значений.
# Это одна из самых простых и интуитивных метрик для задач регрессии.

[Иллюстрация к лекции]

[Иллюстрация к лекции]

```python
from sklearn.metrics import mean_absolute_error

y_true = [3, -0.5, 2, 7]
y_pred = [2.5, 0.0, 2, 8]

mae = mean_absolute_error(y_true, y_pred)
print("MAE =", mae)
```

# **Метрики для кластеризации**

[Иллюстрация к лекции]

# **Как выбрать метрику**

[Иллюстрация к лекции]

# **§ 4. Обзор Scikit-learn**
# Scikit-learn — это одна из самых популярных и мощных библиотек Python для машинного обучения, созданная на основе NumPy, SciPy и matplotlib.
# Она предоставляет широкий набор инструментов для предобработки данных, обучения моделей, оценки качества, оптимизации гиперпараметров и работы с пайплайнами.

# Возможности:
# Загрузка стандартных датасетов.
# Предобработка данных (масштабирование, кодирование категорий).
# Классические модели ML (регрессия, классификация, кластеризация).
# Оценка качества и кросс-валидация.
# Построение пайплайнов.

[Иллюстрация к лекции]

[Иллюстрация к лекции]