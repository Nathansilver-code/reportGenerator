# PrimaryTrack — Uganda Primary School Marksheet System

A full-stack web application built with **Flask + PostgreSQL + Python** for
managing student marks, generating class marksheets, and printing individual
report cards for Uganda primary schools (P1–P7).

---

## Features

| Feature | Description |
|---|---|
| Teacher Auth | Register / login with hashed passwords |
| Mark Entry | Enter English, Maths, Science, SST marks (0–100) per learner |
| Uganda Grading |
| Marksheet | Full class table with position, aggregate sum, division |
| Report Card | Printable individual report with comment |
| Print Support | Browser print button produces clean A4 output |

---

## Project Structure

```
marksheet_app/
│
├── app.py               ← Flask application factory & entry point
├── config.py            ← Database URL, secret key
├── extensions.py        ← Shared db & login_manager objects
├── models.py            ← Teacher, Student, Mark database models
├── requirements.txt     ← Python dependencies
├── .env.example         ← Environment variable template
│
├── routes/
│   ├── auth.py          ← /login  /register  /logout
│   ├── marks.py         ← /select-class  /register-student  /students
│   └── reports.py       ← /marksheet  /report/<id>  /reports
│
├── utils/
│   └── grading.py       ← Uganda grading logic (grades, divisions, comments)
│
└── templates/
    ├── base.html             ← Master layout (navbar, alerts, styles)
    ├── login.html            ← Login + sign-up landing page
    ├── register.html         ← New teacher registration form
    ├── select_class.html     ← Choose P1–P7 class and term
    ← register_student.html  ← Enter learner name & marks
    ├── students_list.html    ← View/filter/delete all students
    ├── reports_home.html     ← Choose class before viewing marksheet
    ├── marksheet.html        ← Full class marksheet (printable)
    └── report_card.html      ← Individual learner report (printable)
```

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- PostgreSQL installed and running

### 2. Create the Database

Open **psql** and run:

```sql
CREATE DATABASE marksheet_db;
```

### 3. Clone / Download and Install

```bash
cd marksheet_app
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```
SECRET_KEY=any-long-random-string
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/marksheet_db
```

### 5. Run the App

```bash
python app.py
```

Flask will print:

```
 * Running on http://127.0.0.1:5000
```

Open that URL in your browser.

On first run, `db.create_all()` automatically creates all tables.

---


