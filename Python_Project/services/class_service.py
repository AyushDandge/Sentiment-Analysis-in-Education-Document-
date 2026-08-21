"""
Class searching, joining and membership checks.

Python equivalent of:
    SearchOnlineCourse.aspx.cs / SearchOfflineCourse.aspx.cs -> Button1_Click
    viewClassesOnline.aspx.cs  / viewClassesOffine.aspx.cs    -> Page_Load,
                                                                 ToggleStatus_Click
    Joined_Class.aspx.cs -> ddltyp_SelectedIndexChanged, Button1_Click
    Admin/view_user.aspx.cs -> Page_Load, btnvoter_Click
"""

from database.db_connection import execute, fetch_all, fetch_one, fetch_scalar


def search_classes(class_type, search_by, value):
    """
    Reproduces the two SelectCommand variants built in viewClasses*.aspx.cs.

    search_by is the dropdown index the original passed in the query string:
        "1" -> Class Name,  "2" -> Area/City
    Anything else returns no rows, exactly as the original did (neither branch
    ran, so the SqlDataSource had an empty SelectCommand).

    The original concatenated the search text straight into the SQL. Here the
    same LIKE search is done with a bound parameter, which produces identical
    results but cannot be broken by a quote in the search box.
    """
    value = value or ""

    if search_by == "1":
        column = "className"
    elif search_by == "2":
        column = "Area"
    else:
        return []

    return fetch_all(
        "SELECT rating, classID, className, city, Area FROM [ClassesRegistration] "
        "WHERE status='Active' AND classType=? AND {col} LIKE ?".format(col=column),
        (class_type, "%" + value + "%"),
    )


def get_class_name(class_id):
    """
    Reproduces:
        select className from ClassesRegistration where classID=<id>
    used at the top of the analysis pages to fill lblClassName.
    """
    row = fetch_one(
        "select className from ClassesRegistration where classID=?", (class_id,)
    )
    return row["className"] if row else None


def is_enrolled(class_id, student_id, class_type):
    """
    Reproduces the membership check in ToggleStatus_Click:

        select class_id, s_id from Student_Class
        where class_id=@class_id and s_id=@s_id
          and status='Active' and class_type='Online'|'Offline'
    """
    row = fetch_one(
        "select class_id, s_id from Student_Class "
        "where class_id=? and s_id=? and status='Active' and class_type=?",
        (class_id, student_id, class_type),
    )
    return row is not None


def get_classes_by_type(class_type):
    """
    Reproduces ddltyp_SelectedIndexChanged, which fills the second dropdown:

        SELECT DISTINCT [className], classID FROM ClassesRegistration
        WHERE classType = @classType
    """
    return fetch_all(
        "SELECT DISTINCT [className], classID FROM ClassesRegistration "
        "WHERE classType = ?",
        (class_type,),
    )


def already_joined(class_id, student_id, class_name, class_type, sname, semail):
    """
    Reproduces the duplicate check in UserNew/Joined_Class.aspx.cs, which counts
    rows matching every field before inserting.
    """
    count = fetch_scalar(
        "SELECT COUNT(*) FROM Student_Class "
        "WHERE class_id = ? AND s_id = ? AND class_Name = ? "
        "AND class_type = ? AND sname = ? AND semail = ?",
        (class_id, student_id, class_name, class_type, sname, semail),
    )
    return (count or 0) > 0


def join_class(class_id, student_id, class_name, class_type, sname, semail):
    """
    Reproduces the INSERT in Joined_Class.aspx.cs. New rows are always 'Active'.
    """
    return execute(
        "Insert Into Student_Class "
        "(class_id, s_id, class_Name, class_type, sname, semail, status) "
        "Values (?, ?, ?, ?, ?, ?, ?)",
        (class_id, student_id, class_name, class_type, sname, semail, "Active"),
    )


# --------------------------------------------------------------------------
# Admin
# --------------------------------------------------------------------------

def get_all_joined_students():
    """Reproduces  SELECT * FROM [Student_Class]  from Admin/view_user.aspx.cs."""
    return fetch_all("SELECT * FROM [Student_Class]")


def toggle_student_class_status(j_id, current_status):
    """
    Reproduces btnvoter_Click + UpdateAccount in Admin/view_user.aspx.cs:
    'Deactive' becomes 'Active', anything else becomes 'Deactive'.

    Returns (new_status, rows_affected).
    """
    new_status = "Active" if current_status == "Deactive" else "Deactive"
    rows = execute(
        "UPDATE Student_Class SET status = ? WHERE J_id = ?", (new_status, j_id)
    )
    return new_status, rows
