"""
Design and Deployment of Sentimental Analysis in Education
Python (Flask) version of the original ASP.NET Web Forms project.

Run with:   python main.py
Then open:  http://127.0.0.1:5000/

Every route below matches the URL of the .aspx page it replaces, so the links
inside the original page templates keep working unchanged.

    ASP.NET page                     ->  route here
    Default.aspx                     ->  /Default.aspx
    login.aspx                       ->  /login.aspx
    UserNew/UserHome.aspx            ->  /UserNew/UserHome.aspx
    Admin/view_user.aspx             ->  /Admin/view_user.aspx
    ...and so on.

Session["std_id"] / Session["Fullname"] / Session["Email"] in the C# become
Flask's session dictionary with the same three keys.
"""

import os

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database.db_connection import DatabaseError
from services import analysis_service, auth_service, class_service, feedback_service

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-in-your-env-file")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def logged_in():
    """True when a student has logged in (Session["std_id"] was set)."""
    return "std_id" in session


def require_login():
    """
    Send the visitor back to the login page if they are not signed in.
    Returns a redirect response, or None when the user may continue.
    """
    if not logged_in():
        return redirect(url_for("login"))
    return None


def alert(message, icon="success", title=None):
    """
    Queue a SweetAlert popup for the next page render.

    The original raised these with either
        Response.Write("<script>alert('...');</script>")
    or
        ScriptManager.RegisterStartupScript(... Swal.fire ...)
    Both are shown here as SweetAlert popups by templates/_alerts.html.
    """
    flash({"title": title or "", "text": message, "icon": icon})


@app.context_processor
def inject_alerts():
    """Make the queued popups and the session available to every template."""
    return {
        "alerts": get_flashed_messages(),
        "current_user": {
            "std_id": session.get("std_id"),
            "Fullname": session.get("Fullname"),
            "Email": session.get("Email"),
        },
    }


@app.errorhandler(DatabaseError)
def handle_database_error(error):
    """Show database problems on a readable page instead of a stack trace."""
    return render_template("error.html", message=str(error)), 500


# ---------------------------------------------------------------------------
# Public pages   (root of the original web site)
# ---------------------------------------------------------------------------

@app.route("/")
@app.route("/Default.aspx")
def default():
    """Default.aspx - the marketing home page built from MasterPage.master."""
    return render_template("Default.html")


@app.route("/AboutUs.aspx")
def about_us():
    """AboutUs.aspx"""
    return render_template("AboutUs.html")


@app.route("/login.aspx", methods=["GET", "POST"])
def login():
    """
    login.aspx  ->  Button1_Click

    The admin shortcut ("admin" / "super") and the student lookup are both
    reproduced exactly as they appear in login.aspx.cs.
    """
    if request.method == "POST":
        email = request.form.get("txtemail", "")
        password = request.form.get("txtpassword", "")

        if auth_service.is_admin(email, password):
            session["admin"] = True
            return redirect(url_for("admin_home"))

        student = auth_service.find_student(email, password)
        if student:
            session["std_id"] = student["std_id"]
            session["Fullname"] = student["Fullname"]
            session["Email"] = student["Email"]
            return redirect(url_for("user_home"))

        # Same message and same "clear both boxes" behaviour as the original.
        alert("Invalid id and password. Please try again.", icon="error")
        return render_template("login.html", txtemail="", txtpassword="")

    return render_template("login.html", txtemail="", txtpassword="")


@app.route("/registration.aspx", methods=["GET", "POST"])
def registration():
    """registration.aspx  ->  btnsubmit_Click"""
    if request.method == "POST":
        fullname = request.form.get("txtfull_name", "")
        email = request.form.get("txtemail", "")
        mobile = request.form.get("txtmobile", "")
        password = request.form.get("txtpassword", "")

        rows = auth_service.register_student(fullname, email, mobile, password)
        if rows > 0:
            alert("Student registered successfully!")
            # The original blanked every box after a successful insert.
            return render_template("registration.html")

        alert("Error in registration. Please try again.", icon="error")

    return render_template("registration.html")


@app.route("/logout")
def logout():
    """
    The original's LogOut link simply navigated back to Default.aspx without
    clearing the session. Clearing it here is the one small change made on
    purpose, because a shared browser would otherwise stay signed in.
    """
    session.clear()
    return redirect(url_for("default"))


# ---------------------------------------------------------------------------
# Student area   (UserNew folder)
# ---------------------------------------------------------------------------

@app.route("/UserNew/UserHome.aspx")
def user_home():
    """UserNew/UserHome.aspx - dashboard with the slider and the three cards."""
    guard = require_login()
    if guard:
        return guard
    return render_template("user/UserHome.html")


@app.route("/UserNew/SearchOnlineCourse.aspx", methods=["GET", "POST"])
def search_online_course():
    """
    UserNew/SearchOnlineCourse.aspx  ->  Button1_Click

    The original read ddlArea.SelectedIndex and redirected to
        viewClassesOnline.aspx?id=<index>&value=<text>
    """
    guard = require_login()
    if guard:
        return guard

    if request.method == "POST":
        return redirect(
            url_for(
                "view_classes_online",
                id=request.form.get("ddlArea", "0"),
                value=request.form.get("txtusername", ""),
            )
        )
    return render_template("user/SearchOnlineCourse.html")


@app.route("/UserNew/SearchOfflineCourse.aspx", methods=["GET", "POST"])
def search_offline_course():
    """UserNew/SearchOfflineCourse.aspx  ->  Button1_Click"""
    guard = require_login()
    if guard:
        return guard

    if request.method == "POST":
        return redirect(
            url_for(
                "view_classes_offline",
                id=request.form.get("ddlArea", "0"),
                value=request.form.get("txtusername", ""),
            )
        )
    return render_template("user/SearchOfflineCourse.html")


@app.route("/UserNew/viewClassesOnline.aspx", methods=["GET", "POST"])
def view_classes_online():
    """
    UserNew/viewClassesOnline.aspx  ->  Page_Load + ToggleStatus_Click

    Page_Load builds the search query; the "Rating" button checks that the
    student has actually joined the class before opening the feedback form.
    """
    guard = require_login()
    if guard:
        return guard
    return _view_classes("Online")


@app.route("/UserNew/viewClassesOffine.aspx", methods=["GET", "POST"])
def view_classes_offline():
    """UserNew/viewClassesOffine.aspx (the original file name is spelled this way)."""
    guard = require_login()
    if guard:
        return guard
    return _view_classes("Offline")


def _view_classes(mode):
    """Shared body for the two viewClasses pages."""
    search_by = request.args.get("id", "")
    value = request.args.get("value", "")

    if request.method == "POST":
        # The Rating button posts back with the classID as its CommandArgument.
        class_id = request.form.get("classID")
        if class_service.is_enrolled(class_id, session["std_id"], mode):
            endpoint = "feedback_online" if mode == "Online" else "feedback_offline"
            return redirect(url_for(endpoint, classID=class_id))
        alert("Please joine the class", icon="error", title="Oops... !")

    classes = class_service.search_classes(mode, search_by, value)
    template = (
        "user/viewClassesOnline.html" if mode == "Online"
        else "user/viewClassesOffine.html"
    )
    return render_template(template, classes=classes)


@app.route("/UserNew/Joined_Class.aspx", methods=["GET", "POST"])
def joined_class():
    """
    UserNew/Joined_Class.aspx  ->  ddltyp_SelectedIndexChanged + Button1_Click

    In ASP.NET the first dropdown posted back to fill the second one. Here the
    class list for the chosen type is fetched by the small script in the
    template, through the /UserNew/classes.json endpoint below.
    """
    guard = require_login()
    if guard:
        return guard

    if request.method == "POST":
        class_type = request.form.get("ddltyp", "")
        class_id = request.form.get("ddlclass", "0")
        class_name = request.form.get("ddlclass_text", "")

        if class_type in ("", "Select") or class_id in ("", "0"):
            alert("Check All Data", icon="error")
            return render_template("user/Joined_Class.html")

        sname = session["Fullname"]
        semail = session["Email"]

        if class_service.already_joined(
            class_id, session["std_id"], class_name, class_type, sname, semail
        ):
            alert(
                "Click ok to continue.",
                icon="warning",
                title="You are already enrolled in this class!",
            )
        else:
            rows = class_service.join_class(
                class_id, session["std_id"], class_name, class_type, sname, semail
            )
            if rows > 0:
                alert(
                    "Click ok to continue!",
                    icon="success",
                    title="Thank You For Joining the Class!",
                )
            else:
                alert("Check All Data", icon="error")

    return render_template("user/Joined_Class.html")


@app.route("/UserNew/classes.json")
def classes_json():
    """
    Supplies the second dropdown on the Join Class page.
    This is the Python stand-in for the ASP.NET AutoPostBack that used to
    repopulate ddlclass when ddltyp changed.
    """
    guard = require_login()
    if guard:
        return guard

    class_type = request.args.get("classType", "")
    rows = class_service.get_classes_by_type(class_type)
    return {
        "classes": [
            {"classID": row["classID"], "className": row["className"]} for row in rows
        ]
    }


@app.route("/UserNew/feedbackOnline.aspx", methods=["GET", "POST"])
def feedback_online():
    """UserNew/feedbackOnline.aspx  ->  Page_Load + Button1_Click"""
    guard = require_login()
    if guard:
        return guard
    return _feedback("Online")


@app.route("/UserNew/feedbackOffline.aspx", methods=["GET", "POST"])
def feedback_offline():
    """UserNew/feedbackOffline.aspx  ->  Page_Load + Button1_Click"""
    guard = require_login()
    if guard:
        return guard
    return _feedback("Offline")


def _feedback(mode):
    """Shared body for the two feedback pages."""
    class_id = request.values.get("classID", "")

    enrolment = feedback_service.get_enrolment(session["std_id"], class_id)
    if not enrolment:
        # Same message and same redirect target as the original.
        alert("Not Member of Institution", icon="error")
        endpoint = (
            "search_online_course" if mode == "Online" else "search_offline_course"
        )
        return redirect(url_for(endpoint))

    fields = (
        feedback_service.ONLINE_FIELDS if mode == "Online"
        else feedback_service.OFFLINE_FIELDS
    )
    template = (
        "user/feedbackOnline.html" if mode == "Online"
        else "user/feedbackOffline.html"
    )

    if request.method == "POST":
        answers = {control: request.form.get(control, "") for control, _, _ in fields}

        missing = [label for control, _, label in fields if not answers[control]]
        if missing:
            alert("Please answer every question before submitting.", icon="error")
        else:
            save = (
                feedback_service.save_online_feedback if mode == "Online"
                else feedback_service.save_offline_feedback
            )
            save(
                class_id,
                session["std_id"],
                answers,
                request.form.get("txtComment", ""),
                session["Fullname"],
            )
            alert("Feedback send successful..! ")

    return render_template(
        template,
        fields=fields,
        class_id=class_id,
        class_name=enrolment["class_Name"],
        customer_name=session["Fullname"],
        email=session["Email"],
    )


@app.route("/UserNew/AnalysisOnline.aspx")
def analysis_online():
    """UserNew/AnalysisOnline.aspx  ->  Page_Load (Naive Bayes)"""
    guard = require_login()
    if guard:
        return guard
    return _analysis("Online")


@app.route("/UserNew/AnalysisOffline.aspx")
def analysis_offline():
    """UserNew/AnalysisOffline.aspx  ->  Page_Load (Naive Bayes)"""
    guard = require_login()
    if guard:
        return guard
    return _analysis("Offline")


def _analysis(mode):
    """Shared body for the two analysis pages."""
    class_id = request.args.get("classID", "")
    if not class_id:
        alert("No class was selected.", icon="error")
        endpoint = (
            "search_online_course" if mode == "Online" else "search_offline_course"
        )
        return redirect(url_for(endpoint))

    class_name = class_service.get_class_name(class_id) or "-"
    result = analysis_service.run_analysis(mode, class_id)

    template = (
        "user/AnalysisOnline.html" if mode == "Online"
        else "user/AnalysisOffline.html"
    )
    return render_template(template, class_name=class_name, **result)


# ---------------------------------------------------------------------------
# Admin area
# ---------------------------------------------------------------------------

def require_admin():
    """Send anyone who is not the admin back to the login page."""
    if not session.get("admin"):
        return redirect(url_for("login"))
    return None


@app.route("/Admin/UserHome.aspx")
def admin_home():
    """Admin/UserHome.aspx"""
    guard = require_admin()
    if guard:
        return guard
    return render_template("admin/UserHome.html")


@app.route("/Admin/view_user.aspx", methods=["GET", "POST"])
def admin_view_user():
    """
    Admin/view_user.aspx  ->  Page_Load + btnvoter_Click

    The Update User button carried "J_id|status" as its CommandArgument and
    flipped the status between Active and Deactive.
    """
    guard = require_admin()
    if guard:
        return guard

    if request.method == "POST":
        argument = request.form.get("commandArgument", "")
        parts = argument.split("|")
        if len(parts) == 2:
            j_id, status = parts
            new_status, rows = class_service.toggle_student_class_status(j_id, status)
            if rows > 0:
                alert("Account  %s  Successfully  ....." % new_status)
            else:
                alert("Error  .....", icon="error")

    return render_template(
        "admin/view_user.html", students=class_service.get_all_joined_students()
    )


if __name__ == "__main__":
    # debug=True gives you automatic reloading while you work in VS Code.
    app.run(host="127.0.0.1", port=5000, debug=True)
