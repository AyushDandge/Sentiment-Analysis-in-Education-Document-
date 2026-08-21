# Sentiment-Analysis-in-Education-Document-
Educational sentiment analysis platform. Students join online/offline classes, rate them across ten parameters, and leave comments; Naive Bayes turns that into per-parameter probabilities and a Suggested / Your Choice / Not Suggested verdict




---

## Project Description

Students register on the site, join an online or offline class, and then submit
a feedback form for that class. The feedback form asks ten questions, each
scored from 0 to 5, plus a free text comment.

The analysis screen then takes all the feedback for one class and:

1. Groups every answer into **negative** (0 or 1), **neutral** (2 or 3) or
   **positive** (4 or 5).
2. Scores the free text comment by looking for a small list of positive and
   negative words.
3. Applies Bayes' theorem to work out P(Negative), P(Neutral) and P(Positive)
   for each of the eleven review parameters.
4. Averages the positive probability and turns it into a recommendation:
   **Not Suggested**, **Your Choice..** or **Suggested**.

An administrator can see every enrolment and activate or deactivate it.

---

## Features

**Public**

* Home page and About page
* Student registration
* Login (students, plus a built-in administrator account)

**Student**

* Dashboard with image slider and feature cards
* Search online courses by class name or by area/city
* Search offline courses the same way
* Join a class (online or offline), with a duplicate-enrolment check
* Submit feedback for a class you have joined (ten ratings plus a comment)
* View the Naive Bayes analysis for a class, with a results table, a summary
  verdict, a column chart and the list of user comments

**Admin**

* Dashboard
* View every enrolment, with a live search filter
* Activate / deactivate an enrolment

---

## Technologies Used

* **Python 3.10+**
* **Flask** – web framework (replaces ASP.NET Web Forms)
* **Jinja2** – page templates (replaces .aspx pages and master pages)
* **Microsoft SQL Server** – the same database engine the original used
* **pyodbc** – SQL Server driver for Python (replaces `System.Data.SqlClient`)
* **python-dotenv** – reads database settings from a `.env` file
  (replaces `Web.config`)
* **Bootstrap, jQuery, Chart.js, SweetAlert2** – the original project's own
  front-end files, copied across unchanged
* **Visual Studio Code** – the development environment

---

## Project Structure

```
Python_Project/
│
├── main.py                 All the pages (routes). This is the entry point.
├── requirements.txt        The Python packages to install.
├── .env.example            Template for your database settings.
├── .gitignore              Files Git should ignore.
├── README.md               This file.
├── CONVERSION_NOTES.md     How each C# file maps to a Python file.
│
├── database/
│   ├── db_connection.py    Opens the SQL Server connection, runs queries.
│   └── schema.sql          Creates the database, the tables and demo data.
│
├── services/               The logic that used to sit in the .aspx.cs files.
│   ├── auth_service.py     Login and registration.
│   ├── class_service.py    Searching, joining, admin status changes.
│   ├── feedback_service.py The two feedback forms.
│   └── analysis_service.py The Naive Bayes analysis.
│
├── templates/              The pages, one per original .aspx file.
│   ├── master.html         <- MasterPage.master
│   ├── Default.html  AboutUs.html  login.html  registration.html
│   ├── user/               <- the UserNew folder
│   └── admin/              <- the Admin folder
│
└── static/                 The original CSS, JavaScript, images and fonts.
    ├── css/  js/  images/  fonts/     (site root assets)
    ├── user/                          (UserNew assets)
    └── admin/                         (Admin assets)
```

---

## Requirements

Before you start, you need these installed on your Windows laptop:

1. **Python 3.10 or newer** – <https://www.python.org/downloads/>
2. **Visual Studio Code** – <https://code.visualstudio.com/>
3. **Microsoft SQL Server** (Express edition is free) –
   <https://www.microsoft.com/en-us/sql-server/sql-server-downloads>
4. **SQL Server Management Studio (SSMS)** –
   <https://learn.microsoft.com/en-us/ssms/download-sql-server-management-studio-ssms>
5. **Microsoft ODBC Driver 17 or 18 for SQL Server** –
   <https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server>

   This is the piece that lets Python talk to SQL Server. It is a separate
   download from SQL Server itself, and it is the most commonly missed step.

---

## Installation

### Step 1 – Install Python

Download Python from the link above and run the installer.
**Tick "Add python.exe to PATH" on the first screen.** This matters; without it
the `python` command will not work in the terminal.

Check it worked by opening Command Prompt and typing:

```bash
python --version
```

### Step 2 – Install VS Code

Install Visual Studio Code, then open it and install the **Python** extension
by Microsoft (click the Extensions icon on the left, search for "Python").

### Step 3 – Open the project folder in VS Code

`File` → `Open Folder…` → choose the `Python_Project` folder.

### Step 4 – Open the VS Code terminal

Press **Ctrl + `** (the key above Tab), or use `Terminal` → `New Terminal`.
The terminal opens inside the project folder.

---

## MySQL Setup

> **Note:** the original project did **not** use MySQL. Its `Web.config` points
> at Microsoft SQL Server (`Data Source=LAPTOP-151ISPLI\MSSQLSERVER01;
> Integrated Security=True`) and `anliss.sql` is a T-SQL script. This Python
> version therefore stays on SQL Server, so your existing database keeps
> working. The section below is the SQL Server setup.

## SQL Server Setup

### Step 5 – Create the database

1. Open **SQL Server Management Studio** and connect to your SQL Server.
2. `File` → `Open` → `File…` and choose `database/schema.sql` from this project.
3. Click **Execute** (or press F5).

This creates the `Educational_Post_Analysis` database, all eleven tables, the
fixed rows the analysis screens need, and some demo data.

You can run the file again later without harm — every statement checks whether
the object already exists first.

### Step 6 – Find your server name

In SSMS, the server name is shown in the "Connect to Server" box. It usually
looks like one of these:

```
localhost
localhost\SQLEXPRESS
LAPTOP-151ISPLI\MSSQLSERVER01
```

Write it down; you need it in the next step.

---

## Python Environment Setup

### Step 7 – Create a virtual environment

In the VS Code terminal:

```bash
python -m venv venv
```

This makes a `venv` folder that holds this project's packages, so they do not
mix with other projects.

### Step 8 – Activate it

On Windows PowerShell (the VS Code default):

```bash
venv\Scripts\Activate.ps1
```

On Windows Command Prompt:

```bash
venv\Scripts\activate.bat
```

You will know it worked because `(venv)` appears at the start of the prompt.

> If PowerShell refuses with "running scripts is disabled on this system", run
> this once and then try again:
> ```bash
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

---

## Install Dependencies

### Step 9 – Install the packages

```bash
pip install -r requirements.txt
```

---

## Configuration

### Step 10 – Create your .env file

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Then open `.env` in VS Code and change `DB_SERVER` to the server name you noted
in Step 6. For example:

```text
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=Educational_Post_Analysis
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUSTED_CONNECTION=yes
SECRET_KEY=any-random-text-you-like
```

`DB_TRUSTED_CONNECTION=yes` means Windows Authentication, which is what the
original `Web.config` used. If you log in to SQL Server with a username and
password instead, set it to `no` and fill in `DB_USER` and `DB_PASSWORD`.

To check the driver name you actually have: press Start, type
**ODBC Data Sources (64-bit)**, open it and look at the **Drivers** tab.

**Never commit the `.env` file to GitHub.** It is already listed in
`.gitignore`.

---

## Running the Application

### Step 11 – Start it

```bash
python main.py
```

You will see:

```
 * Running on http://127.0.0.1:5000
```

Open **<http://127.0.0.1:5000/>** in your browser.

To stop the application, press **Ctrl + C** in the terminal.

### Logging in

The demo data includes these accounts:

| Role    | Email / username | Password |
| ------- | ---------------- | -------- |
| Admin   | `admin`          | `super`  |
| Student | `r@gmail.com`    | `1122`   |
| Student | `sham@gmail.com` | `7744`   |
| Student | `re@gmail.com`   | `1144`   |

The admin account is hard-coded, exactly as it was in `login.aspx.cs`.

Student `r@gmail.com` is already enrolled in "Python Programming" (online) and
"Java Programming" (offline), so the Rating button works straight away.

### A quick tour

1. Log in as `r@gmail.com` / `1122`.
2. Click **Online Course**, choose **Class Name**, type `Python`, press Search.
3. Press **Rating** to fill in the feedback form, or **View Analysis** to see
   the Naive Bayes results.
4. Use **Join Course** to enrol in something new.
5. Log out and log back in as `admin` / `super` to see the admin screens.


