"""
Login and registration.

Python equivalent of:
    login.aspx.cs        -> Button1_Click
    registration.aspx.cs -> btnsubmit_Click
"""

from database.db_connection import execute, fetch_one

# The hard coded administrator account from login.aspx.cs.
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "super"


def is_admin(email, password):
    """Reproduces:  if (txtemail.Text.Trim()=="admin" && txtpassword.Text.Trim()=="super")"""
    return email.strip() == ADMIN_USERNAME and password.strip() == ADMIN_PASSWORD


def find_student(email, password):
    """
    Reproduces the parameterised query from login.aspx.cs:

        select std_id, Fullname, Email from studentRegistration
        where Email=@u and password=@p

    Returns the row as a dictionary, or None when the credentials are wrong.
    """
    return fetch_one(
        "select std_id, Fullname, Email from studentRegistration "
        "where Email=? and password=?",
        (email.strip(), password.strip()),
    )


def register_student(fullname, email, mobile, password):
    """
    Reproduces the INSERT from registration.aspx.cs.
    Returns the number of rows inserted (the original checked  if (n > 0) ).
    """
    return execute(
        "INSERT INTO studentRegistration (Fullname, Email, mobile, password) "
        "VALUES (?, ?, ?, ?)",
        (fullname, email, mobile, password),
    )
