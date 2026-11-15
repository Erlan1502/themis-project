---
week_number: 2
topic_id: "week_02_files_api"
title: "Неделя 2: Работа с файловыми структурами, форматами CSV, JSON, Excel и архивами"
topic_name: "Файловые операции pathlib/os, парсинг CSV, сериализация JSON, интеграция Excel и сжатие zipfile"
initial_prompt: "Привет! На второй лекции мы изучили работу с файлами и форматами данных. В чем ключевое отличие потоковой обработки файла через генераторы от считывания всего файла в память, и почему при работе с внешними REST API критично валидировать JSON-ответы?"
source_files:
  - "Lecture_2_1_Directories and Files.ipynb"
  - "Lecture_2_3_Working with CSV Files.ipynb"
  - "Lecture_2_4_Working with JSON Files.ipynb"
  - "Lecture_2_5_Working with Excel .ipynb"
  - "Lecture_2_6_Pandas and Excel .ipynb"
  - "Lecture_2_7_Archiving Project Files.ipynb"
glossary:
  - "about"
  - "absolute"
  - "access"
  - "accuracy"
  - "active"
  - "add"
  - "added"
  - "additional"
  - "adds"
  - "adjust"
  - "after"
  - "age"
  - "csv"
  - "excel"
  - "json"
  - "openpyxl"
  - "pathlib"
  - "serialization"
  - "streaming"
  - "zipfile"
---

# Неделя 2: Работа с файловыми структурами, форматами CSV, JSON, Excel и архивами

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** Файловые операции pathlib/os, парсинг CSV, сериализация JSON, интеграция Excel и сжатие zipfile

## Материалы ноутбука: Lecture_2_1_Directories and Files.ipynb

# **Lecture 2. Working with Directories and Files in Python**
---

# Part 1. Creating a Project Structure → directories, paths, os, pathlib
# Part 2. Working with Text Files → application log
# Part 3. Working with CSV → student dataset
# Part 4. Working with JSON → AI model configuration
# Part 5. Working with Excel → student performance report
# Part 6. Pandas and Excel → analysis of the generated report
# Part 7. Archiving Project Files → ZIP backup

# **Part 1. Creating a Project Structure**
# **Task: Create a File Structure for an AI Course Project**
# ai_course_project/
# │
# ├── data/
# ├── reports/
# ├── logs/
# └── backup/

# **Step 1. Current working directory**

```python
import os

print(os.getcwd())
```

# os.getcwd() returns the current working directory — the directory where Python is currently running.

# The **os** module provides functions for interacting with the operating system, including working with files and directories.

# The **os** module in Python provides a standard interface for interacting with the operating system. It allows programs to work with the file system, environment variables, processes, and system-level functionality in a platform-independent way (Windows, Linux, macOS).

# **Step 2. View directory contents**

```python
print(os.listdir())
```

```python
print(os.listdir("/content"))
```

# os.listdir() returns the names of files and directories inside a directory.

# **Step 3. Create the project directory**

```python
os.mkdir("ai_course_project")
```

```python
print(os.listdir())
```

# **Step 4. Create several directories**

```python
folders = ["data", "reports", "logs", "backup"]

for folder in folders:
    path = os.path.join("ai_course_project", folder)
    os.mkdir(path)
```

```python
path = os.path.join(
    "ai_course_project",
    "data",
    "students.txt"
)

print(path)
```

# **Step 5. Check whether a directory exists**

```python
project_path = "ai_course_project"

print(os.path.exists(project_path))
```

```python
print(os.path.isdir(project_path))
```

```python
print(os.path.isfile(project_path))
```

# **Step 6. Create nested directories safely**

```python
os.makedirs(
    "ai_course_project/data/raw",
    exist_ok=True
)
```

# makedirs() can create multiple levels of directories at once.

# exist_ok=True means: if the directory already exists, do not raise an error.

# **Working with pathlib**

# **pathlib** is a built-in Python module for working with file and directory paths. It provides a modern, object-oriented, and cross-platform alternative to many functions from os.path.

# **What pathlib is used for:**

# Creating and manipulating file and directory paths

# Navigating the file system

# Checking file and directory properties

# Reading from and writing to files

# Working with absolute and relative paths

# Ensuring cross-platform compatibility (Windows, Linux, macOS)

# **Step 7. Create a path with Path**

```python
from pathlib import Path

project = Path("ai_course_project1")

data_path = project / "data1"
reports_path = project / "reports1"
logs_path = project / "logs1"
backup_path = project / "backup1"

data_path.mkdir(parents=True, exist_ok=True)
reports_path.mkdir(parents=True, exist_ok=True)
logs_path.mkdir(parents=True, exist_ok=True)
backup_path.mkdir(parents=True, exist_ok=True)
```

# parents=True means: if the parent folder ai_course_project1 does not yet exist, create it as well.

# exist_ok=True means: if the folder already exists, do not raise an error.

# **Step 8. Useful Path properties**

```python
file_path = Path(
    "ai_course_project/data/students.txt"
)

print(file_path.name)
print(file_path.stem)
print(file_path.suffix)
print(file_path.parent)
```

```python
print(file_path.resolve())
```

```python
print(file_path.exists())
```

# **Part 2. Working with Text Files**

# Task: Create and Manage an Application Log

# **Step 1. Create and write a text file**

```python
from pathlib import Path

log_file = Path(
    "ai_course_project/logs/application.log"
)

with open(log_file, "w", encoding="utf-8") as file:
    file.write("Application started\n")
    file.write("Student dataset loaded\n")
    file.write("Processing completed\n")
```

# with open(...) automatically closes the file after the block finishes.

# **Step 2. Read the entire file**

```python
with open(log_file, "r", encoding="utf-8") as file:
    content = file.read()

print(content)
```

# read() reads the entire file as one string.

```python
print(type(content))
```

# **Step 3. Read one line**

```python
with open(log_file, "r", encoding="utf-8") as file:
    first_line = file.readline()

print(first_line)
```

readline() reads one line.

# **Step 4. Read all lines into a list**

```python
with open(log_file, "r", encoding="utf-8") as file:
    lines = file.readlines()

print(lines)
```

# **Step 5. Process the file line by line**

```python
with open(log_file, "r", encoding="utf-8") as file:
    for line in file:
        print(line.strip())
```

# **Step 6. Append new information**

```python
with open(log_file, "a", encoding="utf-8") as file:
    file.write("Report generated\n")
```

# **Step 7. Search information in a text file**

```python
with open(log_file, "r", encoding="utf-8") as file:
    for line in file:
        if "completed" in line.lower():
            print(line.strip())
```

# **Step 8. Count lines**

```python
with open(log_file, "r", encoding="utf-8") as file:
    line_count = 0

    for line in file:
        line_count += 1

print("Number of log entries:", line_count)
```

```python
with open(log_file, "r", encoding="utf-8") as file:
    line_count = sum(1 for line in file)
print(line_count)
```

# Working with files in Python is based on the built-in open() function.
# File modes:
# "r" — read mode (default)
# "w" — write mode (creates a new file or overwrites an existing one)
# "a" — append mode (adds data to the end of the file)
# "b" — binary mode

---

## Материалы ноутбука: Lecture_2_3_Working with CSV Files.ipynb

# **§1.Working with CSV Files**

# **Task: Student Dataset**

# We need to create and manage a small dataset containing student results for the Programming for AI course.

# The CSV file should contain:

# **id, name, assignment1, assignment2, assignment3**

# During the task, we will:

# Create a CSV file.
# Write data to the file.
# Open and read the CSV file.
# Read specific columns and records.
# Add a new record.
# Modify existing data.
# Calculate new values.
# Create a processed CSV file.
# Read and analyze the dataset using Pandas.

# **Step 1. Import the CSV module**

# Python provides the built-in csv module for working with CSV files.

# CSV stands for Comma-Separated Values.
# Unlike JSON, CSV does not naturally represent nested structures. It is primarily designed for rows and columns.

# **Step 2. Create and write to a CSV file**

```python
students = [
    [1, "Amina", 85, 90, 88],
    [2, "Arman", 70, 75, 80],
    [3, "Dias", 95, 92, 96],
    [4, "Aigerim", 60, 68, 65]
]
```

# Define the column names:

```python
header = [
    "id",
    "name",
    "assignment1",
    "assignment2",
    "assignment3"
]
```

# Create the CSV file:

```python
with open("students.csv", "w", newline="", encoding="utf-8") as file:

    writer = csv.writer(file)

    # Write column names
    writer.writerow(header)

    # Write all student records
    writer.writerows(students)
```

# Without newline="" extra empty lines may appear between CSV rows in some cases.
# writer.writerow() - writes one line
# writer.writerows() - writes a few lines

# **Step 3. Open and read the CSV file**

```python
with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    for row in reader:
        print(row)
```

# Values read using csv.reader() are returned as strings.

```python
int(row[2])
```

# **Step 4. Skip the header and read student records**

```python
with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    header = next(reader)
    print("Columns:", header)
    for row in reader:
        print(row)
```

# next(reader) получает первую строку и переводит reader на следующую.

# **Step 5. Access specific values**

```python
with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        print(row[1])
```

```python
with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        name = row[1]
        assignment1 = row[2]
        print(name, assignment1)
```

# **Step 6. Read CSV using DictReader**

```python
with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for student in reader:
        print(student)
```

```python
with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for student in reader:
        print(
            student["name"],
            student["assignment1"]
        )
```

# **# Step 7. Calculate values from CSV data**
# Calculate the average assignment score for every student.

```python
with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for student in reader:
        score1 = int(student["assignment1"])
        score2 = int(student["assignment2"])
        score3 = int(student["assignment3"])
        average = (score1 + score2 + score3) / 3

        print(
            student["name"],
            round(average, 2)
        )
```

# **# Step 8. Filter CSV data**
# Display only students whose average score is at least 80.

```python
with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for student in reader:
        scores = [
            int(student["assignment1"]),
            int(student["assignment2"]),
            int(student["assignment3"])
        ]
        average = sum(scores) / len(scores)
        if average >= 80:
            print(student["name"], round(average, 2))
```

# **Step 9. Add a new record**

```python
new_student = [5, "Miras", 78, 85, 80]

with open("students.csv","a",newline="",encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(new_student)
```

# **Step 10. Modify an existing record**
# Change Arman's Assignment 2 score from 75 to 82.

# First, we read the data:

```python
rows = []

with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    fieldnames = reader.fieldnames
    for student in reader:
        if student["name"] == "Arman":
            student["assignment2"] = "82"

        rows.append(student)
```

# then overwrite the file:

```python
with open("students.csv", "w", encoding="utf-8") as file:
    writer = csv.DictWriter(file,fieldnames=fieldnames )
    writer.writeheader()
    writer.writerows(rows)
```

# **Step 11. Add calculated columns**

```python
processed_students = []

with open("students.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for student in reader:
        scores = [
            int(student["assignment1"]),
            int(student["assignment2"]),
            int(student["assignment3"])
        ]
        average = sum(scores) / len(scores)
        student["average"] = round(average, 2)

        if average >= 70:
            student["result"] = "Pass"
        else:
            student["result"] = "Fail"

        processed_students.append(student)
```

# **Step 12. Save processed data to a new CSV file**

```python
fieldnames = [
    "id",
    "name",
    "assignment1",
    "assignment2",
    "assignment3",
    "average",
    "result"
]

with open(
    "students_processed.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(processed_students)
```

# **Step 13. Read CSV with Pandas**

```python
import pandas as pd
df = pd.read_csv("students_processed.csv")
print(df)
```

```python
print(type(df))
```

[Иллюстрация к лекции]

# The csv module teaches us how a CSV file works. Pandas allows us to work with CSV files as datasets.

---

## Материалы ноутбука: Lecture_2_4_Working with JSON Files.ipynb

# **§4. Working with JSON Files**
# **JSON (JavaScript Object Notation) - It is a text format for storing and exchanging data.**

# **Task: Student AI Course Data**

# We need to store information about students and their results in a JSON file.

# The program should:

# Create data in Python.
# Save data to a JSON file.
# Open and read the JSON file.
# Access specific values.
# Modify existing data.
# Add new data.
# Delete data.
# Calculate values using data from JSON.
# Save the updated data back to the file.
# Convert between Python objects and JSON strings.

# **Step 1. Import the JSON module**

# Python has a built-in module for working with JSON.

```python
import json
```

# **Step 2. Create data in Python**

# First, create a Python dictionary.

```python
students = {
    "course": "Programming for AI",
    "semester": 1,
    "students": [
        {
            "id": 1,
            "name": "Amina",
            "scores": [85, 90, 88],
            "active": True
        },
        {
            "id": 2,
            "name": "Arman",
            "scores": [70, 75, 80],
            "active": True
        },
        {
            "id": 3,
            "name": "Dias",
            "scores": [95, 92, 96],
            "active": True
        }
    ]
}

print(students)
print(type(students))
```

# **Step 3. Create and write to a JSON file**

# Теперь создаём файл students.json.

```python
with open("students.json", "w", encoding="utf-8") as file:
    json.dump(students, file, indent=4)
```

# indent=4 — makes the JSON "pretty formatted" with 4-space indents. Removing indent will save everything on a single line.

# **Step 4. Open and read a JSON file**

```python
with open("students.json", "r", encoding="utf-8") as file:
    data = json.load(file)

print(data)
print(type(data))
```

# **Step 5. Access data from JSON**

```python
print(data["course"])
```

```python
print(data["students"])
```

```python
print(data["students"][0])
```

```python
print(data["students"][0]["name"])
```

```python
print(data["students"][0]["scores"])
```

# **Step 6. Read all records**

```python
for student in data["students"]:
    print(student["id"], student["name"], student["scores"])
```

# **Step 7. Calculate values from JSON data**

```python
for student in data["students"]:
    scores = student["scores"]
    average = sum(scores) / len(scores)

    print(student["name"], round(average, 2))
```

# **Step 8. Modify existing data**
# Arman improved his second assignment score from 75 to 82.

```python
for student in data["students"]:

    if student["name"] == "Arman":
        student["scores"][1] = 82

print(data["students"][1])
```

# We have made changes in Python's memory, but the `students.json` file has not yet changed.

# **Step 9. Save changes back to the JSON file**

```python
with open("students.json", "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4)
```

# **Step 10. Add a new value**

```python
for student in data["students"]:
    scores = student["scores"]
    average = sum(scores) / len(scores)
    student["average"] = round(average, 2)
```

```python
for student in data["students"]:

    if student["average"] >= 70:
        student["result"] = "Pass"
    else:
        student["result"] = "Fail"
```

# **Step 11. Add a new record**

```python
new_student = {
    "id": 4,
    "name": "Aigerim",
    "scores": [60, 68, 65],
    "active": True
}

data["students"].append(new_student)
```

```python
for student in data["students"]:
    print(student["name"])
```

# **Step 12. Delete data**

```python
for student in data["students"]:
    student.pop("active", None)
```

```python
data["students"] = [
    student
    for student in data["students"]
    if student["name"] != "Aigerim"
]
```

# **Step 13. Save the final version**

```python
with open("students.json", "w", encoding="utf-8") as file:
    json.dump(
        data,
        file,
        indent=4,
        ensure_ascii=False
    )
```

# **Step 14. json.dumps() — Python object → JSON string**

```python
student = {
    "name": "Amina",
    "age": 22,
    "city": "Astana"
}

json_string = json.dumps(student, indent=4)

print(json_string)
print(type(json_string))
```

# json.dump()  → writes JSON to a FILE
# json.dumps() → creates a JSON STRING

# **Step 15. json.loads() — JSON string → Python object**

# For reading data in the json module, there are two methods:
# json.load — reads a file in JSON format and returns Python objects
# json.loads — reads a JSON-formatted string and returns Python objects

```python
json_string = '''
{
    "model": "RandomForest",
    "accuracy": 0.91,
    "trained": true
}
'''
```

```python
data = json.loads(json_string)

print(data)
print(type(data))
```

```python
print(data["model"])
print(data["accuracy"])
```

[Иллюстрация к лекции]

[Иллюстрация к лекции]

---

## Материалы ноутбука: Lecture_2_5_Working with Excel .ipynb

§5. Working with Excel files

#Working with .xlsx (Microsoft Excel) files in Python is typically done using libraries such as openpyxl, xlrd, pandas, or xlwt, depending on your needs. Here are examples of how to work with .xlsx files using the openpyxl library.

# **Task: Create a Student Performance Report**

# Problem

# The Programming for AI course has the following student results:

[Иллюстрация к лекции]

# **Your task is to create an Excel report student_report.xlsx.**

```python
pip install openpyxl
```

# Step 1. Create the workbook

```python
import openpyxl

# Create a new workbook
workbook = openpyxl.Workbook()

# Get the active worksheet
sheet = workbook.active

# Rename the worksheet
sheet.title = "Students"

# Save the workbook
workbook.save("student_report.xlsx")

print("Excel file created.")
```

# Step 2. Create the table

```python
sheet.append(["No.", "Student", "Assignment 1",
              "Assignment 2", "Assignment 3"])

students = [
    ["Amina", 85, 90, 88],
    ["Arman", 70, 75, 80],
    ["Dias", 95, 92, 96],
    ["Aigerim", 60, 68, 65]
]

for i, student in enumerate(students, start=1):
    sheet.append([i] + student)

# Save the book to a file
workbook.save("student_report.xlsx")

print("Student data saved.")
```

# Step 3. Open and read the Excel file
# Open the existing Excel file and display all student records.

```python
import openpyxl

workbook = openpyxl.load_workbook("student_report.xlsx")

sheet = workbook["Students"]

for row in sheet.iter_rows(values_only=True):
    print(row)
```

# values_only=True - means that we get cell values ​​rather than Cell objects

# Step 4. Read specific cells

# Step 5. Modify existing data
# Arman completed a correction. Change his Assignment 2 score from 75 to 82.

```python
for row in range(2, sheet.max_row + 1):

    name = sheet[f"B{row}"].value

    if name == "Arman":
        sheet[f"D{row}"] = 82

workbook.save("student_report.xlsx")

print("Arman's score updated.")
```

# Step 6. Add calculated columns: Average, Result

# Calculate the average score for each student. A student passes if the average score is at least 70.

```python
sheet["F1"] = "Average"
sheet["G1"] = "Result"

for row in range(2, sheet.max_row + 1):

    scores = [
        sheet[f"C{row}"].value,
        sheet[f"D{row}"].value,
        sheet[f"E{row}"].value
    ]

    average = sum(scores) / len(scores)

    sheet[f"F{row}"] = round(average, 2)

    if average >= 70:
        sheet[f"G{row}"] = "Pass"
    else:
        sheet[f"G{row}"] = "Fail"

workbook.save("student_report.xlsx")

print("Average scores and results calculated.")
```

# Step 7. Add a new student
# A new student joined the course. Add the student to the end of the table.

```python
name = "Miras"
assignment1 = 78
assignment2 = 85
assignment3 = 80

average = (assignment1 + assignment2 + assignment3) / 3

if average >= 70:
    result = "Pass"
else:
    result = "Fail"

number = sheet.max_row

sheet.append([
    number,
    name,
    assignment1,
    assignment2,
    assignment3,
    round(average, 2),
    result
])

workbook.save("student_report.xlsx")

print("New student added.")
```

# Step 8. Create a Summary worksheet
# Create a new worksheet called Summary and calculate general course statistics.

```python
students_sheet = workbook["Students"]

# Remove old Summary sheet if it already exists
if "Summary" in workbook.sheetnames:
    del workbook["Summary"]

# Create a new worksheet
summary_sheet = workbook.create_sheet("Summary")

averages = []
passed = 0
failed = 0

for row in range(2, students_sheet.max_row + 1):
    average = students_sheet[f"F{row}"].value
    result = students_sheet[f"G{row}"].value

    averages.append(average)

    if result == "Pass":
        passed += 1
    else:
        failed += 1

# Write summary
summary_sheet.append(["Metric", "Value"])
summary_sheet.append(["Number of students", len(averages)])
summary_sheet.append(["Course average", round(sum(averages) / len(averages), 2)])
summary_sheet.append(["Highest average", max(averages)])
summary_sheet.append(["Lowest average", min(averages)])
summary_sheet.append(["Passed", passed])
summary_sheet.append(["Failed", failed])

workbook.save("student_report.xlsx")

print("Summary worksheet created.")
```

# Step 9. Format the Excel report

```python
import openpyxl

from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

workbook = openpyxl.load_workbook("student_report.xlsx")

for sheet in workbook.worksheets:

    # Format header
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # Adjust column widths
    for col in range(1, sheet.max_column + 1):

        letter = get_column_letter(col)
        max_len = 0

        for row in range(1, sheet.max_row + 1):

            value = sheet.cell(row, col).value

            if value is not None:
                max_len = max(max_len, len(str(value)))

        sheet.column_dimensions[letter].width = max(
            10,
            min(30, max_len + 2)
        )

workbook.save("student_report.xlsx")

print("Report formatted.")
```

# Create file → Write → Save → Open → Read → Access cells → Modify → Calculate → Add rows → Create worksheet → Format → Save.

---

## Материалы ноутбука: Lecture_2_6_Pandas and Excel .ipynb

# **Pandas and Excel**
# **Task: Analyze Student Performance from an Excel File**

# Suppose we have an Excel file:

Our task is to:

Read the Excel file.
Explore the dataset.
Select rows and columns.
Calculate student averages.
Filter students.
Add new columns.
Calculate statistics.
Sort the data.
Save the results to a new Excel file.

# **Step 1. Import Pandas**

```python
import pandas as pd
```

# **Step 2. Read an Excel file**

```python
df = pd.read_excel("student_report.xlsx")
```

# **Step 3. Explore the dataset**

```python
df.describe()
```

# This is an important difference from openpyxl: Pandas immediately provides tools for data analysis.

# **Step 4. Select a column**

# **Step 5. Select rows**

# **Step 6. Select data using conditions**

# Find students whose Assignment 1 score is at least 80

```python
df[df["Assignment 1"] >= 80]
```

# **Step 7. Calculate the average score**

# Now we want an average for each student.

```python
df["Average"] = df[
    ["Assignment 1", "Assignment 2", "Assignment 3"]
].mean(axis=1)
```

# Add a Result column
# Average >= 70 → Pass
# Average < 70  → Fail

```python
df["Result"] = df["Average"].apply(
    lambda x: "Pass" if x >= 70 else "Fail"
)
```

# **Step 8. Save results to Excel**

```python
df.to_excel(
    "student_results.xlsx",
    index=False
)
```

# The new file contains our processed dataset.

# index=False is important.

# Without it, Pandas may save its DataFrame index.

# **Step 9. Save multiple DataFrames to different Excel sheets**

```python
passed = df[df["Result"] == "Pass"]
failed = df[df["Result"] == "Fail"]
```

```python
with pd.ExcelWriter("student_analysis.xlsx") as writer:

    df.to_excel(
        writer,
        sheet_name="All Students",
        index=False
    )

    passed.to_excel(
        writer,
        sheet_name="Passed",
        index=False
    )

    failed.to_excel(
        writer,
        sheet_name="Failed",
        index=False
    )
```

[Иллюстрация к лекции]

---

## Материалы ноутбука: Lecture_2_7_Archiving Project Files.ipynb

# **Task: Create a Backup of Project Files**

# During the previous tasks, our Python application created several files:

# project/
# │
# ├── students.csv
# ├── students.json
# └── student_report.xlsx

# We need to create a ZIP archive containing the project files.

# During this task, we will:

# Create a ZIP archive.
# Add several files to the archive.
# View the contents of an existing archive.
# Extract one file.
# Extract all files.
# Create a backup of an entire directory.

# **Step 1. Import the zipfile module**

# Python provides the built-in zipfile module:

```python
import zipfile
```

# **Step 2. Create a ZIP archive**

```python
with zipfile.ZipFile("project_backup.zip", "w") as archive:
    archive.write("file3.csv")
    archive.write("file2.jpg")
    archive.write("file1.xlsx")
```

# **Step 3. Use compression**

```python
with zipfile.ZipFile("project_backup1.zip","w",
                     compression=zipfile.ZIP_DEFLATED) as archive:

    archive.write("file3.csv")
    archive.write("file2.jpg")
    archive.write("file1.xlsx")
```

# Available Algorithms:
# ZIP_STORED — no compression
# ZIP_DEFLATED — standard DEFLATE algorithm (need zlib)
# ZIP_BZIP2 — bzip2 compression
# ZIP_LZMA — LZMA compression

# **Step 4. Add a new file to an existing archive**

```python
with zipfile.ZipFile(
    "project_backup1.zip",
    "a",
    compression=zipfile.ZIP_DEFLATED
) as archive:

    archive.write("file4.txt")
```

# **Step 5. Open and read an existing ZIP archive**
# Open project_backup.zip and display all files stored inside.

```python
with zipfile.ZipFile("project_backup1.zip", "r") as archive:
    files = archive.namelist()
    print(files)
```

# **Step 6. Get information about archived files**

```python
with zipfile.ZipFile("project_backup1.zip", "r") as archive:
    for file in archive.infolist():
        print("Name:", file.filename)
        print("Original size:", file.file_size)
        print("Compressed size:", file.compress_size)
        print()
```

# **Why can a compressed file be larger than the original file?**
# Compression does not always make a file smaller. For very small files, the compressed size can be slightly larger because compression requires additional metadata. Compression is more effective for larger files with repetitive data.

# **Step 7. Extract one file**

```python
with zipfile.ZipFile("project_backup1.zip", "r") as archive:

    archive.extract(
        "students.json",
        "extracted"
    )
```

# **Step 8. Extract all files**

```python
with zipfile.ZipFile("project_backup1.zip", "r") as archive:

    archive.extractall("restored_project")
```

# **Step 9. Archive files from a directory**

```python
import os
import zipfile

with zipfile.ZipFile("project_backup1.zip", "w",
    compression=zipfile.ZIP_DEFLATED) as archive:

    for root, directories, files in os.walk("restored_project"):
        for file in files:
            file_path = os.path.join(root, file)
            archive.write(file_path)
            print("Added:", file_path)
```

# **Step 10. Preserve the project directory structure**

# Но предыдущий вариант может сохранить внутри ZIP пути не совсем так, как нам хочется.

# Лучше использовать arcname.

```python
import os
import zipfile

project_folder = "restored_project"

with zipfile.ZipFile("project_backup1.zip",    "w",
    compression=zipfile.ZIP_DEFLATED) as archive:

    for root, directories, files in os.walk(project_folder):
        for file in files:
            file_path = os.path.join(root, file)
            archive_name = os.path.relpath(
                file_path,
                project_folder
            )
            archive.write(
                file_path,
                arcname=archive_name
            )
```

# **Step 11. Check whether a file exists in the archive**
# Check whether students.json exists in the backup.

```python
with zipfile.ZipFile("project_backup1.zip", "r") as archive:

    files = archive.namelist()
    if "file1.xlsx" in files:
        print("file1.xlsx found")
    else:
        print("file1.xlsx not found")
```

# **Module tarfile**

# Python provides the built-in tarfile module for creating, reading, and extracting TAR archives.

# A TAR archive combines multiple files and directories into a single archive.

```python
import tarfile
```

# TAR primarily combines multiple files into a single archive, while compression is usually added separately, for example using GZIP.

# **Step 1. Create a TAR archive**

```python
with tarfile.open("project_backup2.tar", "w") as archive:
    archive.add(
        "restored_project",
        arcname="restored_project"
    )

print("TAR archive created.")
```

# **Step 2. Create a compressed .tar.gz archive**

```python
with tarfile.open("project_backup3.tar.gz", "w:gz") as archive:
    archive.add(
        "restored_project",
        arcname="restored_project"
    )

print("Compressed TAR archive created.")
```

# **Step 3. Open an existing TAR archive**

```python
with tarfile.open("project_backup3.tar.gz", "r:gz") as archive:
    print(archive.getnames())
```

# **Step 4. Get information about archived files**

```python
with tarfile.open("project_backup3.tar.gz", "r:gz") as archive:

    for member in archive.getmembers():

        print("Name:", member.name)
        print("Size:", member.size)
        print("File:", member.isfile())
        print("Directory:", member.isdir())
        print()
```

# **Step 5. Extract one file**

```python
with tarfile.open("project_backup3.tar.gz", "r:gz") as archive:

    member = archive.getmember(
        "restored_project/file1.xlsx"
    )

    archive.extract(
        member,
        path="extracted"
    )
```

# **Step 6. Extract all files**

```python
with tarfile.open("project_backup3.tar.gz", "r:gz") as archive:

    archive.extractall(
        path="restored_project1"
    )
```

[Иллюстрация к лекции]

[Иллюстрация к лекции]

# **В чём отличие TAR от ZIP? **
# ZIP = упаковка + сжатие каждого файла отдельно.
# TAR = упаковка всех файлов в один контейнер → потом общий архив сжимается целиком (gzip, bzip2 и т.д.).
# Поэтому .tar.gz часто компактнее, чем .zip, и быстрее в распаковке на Linux/Unix.