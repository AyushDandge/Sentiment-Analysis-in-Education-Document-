"""
Database connection helpers.

This is the Python equivalent of the C# pattern that appeared at the top of
almost every code-behind file:

    SqlConnection con = new SqlConnection(ConfigurationManager.AppSettings["LIS"]);
    con.Open();
    SqlCommand cmd = new SqlCommand();
    ...

In C# the connection string lived in Web.config.  Here it is built from a .env
file so that no credentials are ever written into the source code.
"""

import os

from dotenv import load_dotenv

# Load the .env file that sits next to main.py (one folder above this file).
load_dotenv()

# pyodbc is imported lazily inside get_connection() so that the application can
# still start and show a readable message if the package is missing.
try:
    import pyodbc
except ImportError:  # pragma: no cover - only hit when pyodbc is not installed
    pyodbc = None


class DatabaseError(Exception):
    """Raised with a message that is safe to show to the user."""


def _env(name, default=""):
    return (os.getenv(name) or default).strip()


def build_connection_string():
    """Assemble the ODBC connection string from the .env settings."""
    driver = _env("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    server = _env("DB_SERVER", "localhost")
    database = _env("DB_NAME", "Educational_Post_Analysis")
    trusted = _env("DB_TRUSTED_CONNECTION", "yes").lower() in ("yes", "true", "1")

    parts = [
        "DRIVER={%s}" % driver,
        "SERVER=%s" % server,
        "DATABASE=%s" % database,
    ]

    if trusted:
        # Windows Authentication - this is what the original Web.config used
        # ("Integrated Security=True").
        parts.append("Trusted_Connection=yes")
    else:
        # SQL Server Authentication
        parts.append("UID=%s" % _env("DB_USER"))
        parts.append("PWD=%s" % _env("DB_PASSWORD"))

    # Newer ODBC drivers (18+) encrypt by default and then reject the self
    # signed certificate a local SQL Server uses, so trust it explicitly.
    parts.append("TrustServerCertificate=yes")

    return ";".join(parts) + ";"


def get_connection():
    """
    Open a new connection to SQL Server.

    Raises DatabaseError with a plain English message when something is wrong,
    instead of letting a raw driver error reach the browser.
    """
    if pyodbc is None:
        raise DatabaseError(
            "The 'pyodbc' package is not installed. "
            "Run:  pip install -r requirements.txt"
        )

    try:
        connection = pyodbc.connect(build_connection_string(), timeout=5)
        connection.autocommit = True
        return connection
    except pyodbc.Error as exc:
        raise DatabaseError(_friendly_error(exc)) from exc


def _friendly_error(exc):
    """Turn a pyodbc error into something a beginner can act on."""
    text = str(exc)

    if "IM002" in text or "Data source name not found" in text:
        return (
            "The ODBC driver named in your .env file was not found. "
            "Install 'ODBC Driver 17 for SQL Server' from Microsoft, or change "
            "DB_DRIVER in .env to a driver you already have."
        )
    if "Cannot open database" in text:
        return (
            "SQL Server was reached but the database does not exist. "
            "Run database/schema.sql in SQL Server Management Studio first."
        )
    if "Login failed" in text:
        return (
            "SQL Server refused the login. Check DB_USER and DB_PASSWORD in "
            ".env, or set DB_TRUSTED_CONNECTION=yes to use Windows "
            "Authentication."
        )
    if "server was not found" in text.lower() or "08001" in text:
        return (
            "Could not reach SQL Server. Check that the service is running and "
            "that DB_SERVER in .env matches your instance name "
            "(for example  LAPTOP-151ISPLI\\MSSQLSERVER01)."
        )
    if "Invalid object name" in text:
        return (
            "A table is missing from the database. "
            "Run database/schema.sql to create all the tables."
        )
    return "Database error: %s" % text


# ---------------------------------------------------------------------------
# Small query helpers.
#
# These replace the repeated  ExecuteReader / ExecuteNonQuery / ExecuteScalar
# blocks in the C# code.  Every one of them opens a connection, runs the
# statement and closes the connection again, which is exactly what the original
# code-behind did.
# ---------------------------------------------------------------------------

def fetch_all(sql, params=()):
    """Run a SELECT and return a list of dictionaries (one per row)."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_rows(sql, params=()):
    """
    Run a SELECT and return a list of plain tuples.

    Used by the analysis code, which reads the feedback columns by POSITION,
    the same way the C# did with  dr.GetString(i).
    """
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        return [tuple(row) for row in cursor.fetchall()]


def fetch_one(sql, params=()):
    """Run a SELECT and return the first row as a dictionary, or None."""
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def fetch_scalar(sql, params=()):
    """Run a SELECT and return the first column of the first row, or None."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return row[0] if row else None


def execute(sql, params=()):
    """Run an INSERT / UPDATE / DELETE and return the number of rows affected."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        return cursor.rowcount
