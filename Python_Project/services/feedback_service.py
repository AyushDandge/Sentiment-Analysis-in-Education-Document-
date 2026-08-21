"""
Feedback forms.

Python equivalent of:
    feedbackOffline.aspx.cs -> Page_Load, getCfeedbackID, Button1_Click
    feedbackOnline.aspx.cs  -> Page_Load, getCfeedbackID, Button1_Click
"""

from database.db_connection import execute, fetch_one

# The ten rating questions on each form, in the order they are stored.
# The order matters: the analysis pages read these columns by position.
OFFLINE_FIELDS = [
    ("rblContent", "Content_Quality", "1.Content Quality"),
    ("rblInstructor", "Instructor_Effectiveness", "2.Instructor Effectiveness"),
    ("rblClassroom_Quality", "Classroom_Audio_Quality", "3.Classroom Audio Quality"),
    ("rblClassroom_Vis", "Classroom_Visibility_And_Presentation_Quality",
     "4.Classroom Visibility And Presentation_Quality"),
    ("rblLearning_E", "Learning_Experience", "5.Learning Experience"),
    ("rblAccessibility", "Accessibility_And_Convenience",
     "6.Accessibility and Convenience"),
    ("rblEngagement", "Engagement_And_Interactivity",
     "7.Engagement and Interactivity"),
    ("rblInfrastructure", "Infrastructure_And_Facilities",
     "8.Infrastructure And Facilities"),
    ("rblAssessment", "Assessment_And_Feedback", "9.Assessment and Feedback"),
    ("rblCareer_Impact", "Career_Impact_Skill_Development",
     "10.Career_Impact_and_Skill_Development"),
]

ONLINE_FIELDS = [
    ("rblContent", "Content_Quality", "1.Content Quality"),
    ("rblInstructor", "Instructor_Effectiveness", "2.Instructor Effectiveness"),
    ("rblVideo_Quality", "Video_Quality_Delivery", "3.Video Quality Delivery"),
    ("rblAudio_Q", "Audio_Quality", "4.Audio Quality"),
    ("rblLearning_E", "Learning_Experience", "5.Learning Experience"),
    ("rblAccessibility", "Accessibility_and_Convenience",
     "6.Accessibility and Convenience"),
    ("rblEngagement", "Engagement_and_Interactivity",
     "7.Engagement and Interactivity"),
    ("rblTechnical", "Technical_Issues", "8.Technical Issues"),
    ("rblAssessment", "Assessment_and_Feedback", "9.Assessment and Feedback"),
    ("rblCareer_Impact", "Career_Impact_and_Skill_Development",
     "10.Career_Impact_and_Skill_Development"),
]


def get_enrolment(student_id, class_id):
    """
    Reproduces the Page_Load lookup that fills the read-only class name box:

        select class_Name, class_type, sname, semail FROM Student_Class
        where s_id=@s_id and class_id=@classID and status='Active'

    Returns None when the student is not an active member, which is what makes
    the original show "Not Member of Institution" and redirect back.
    """
    return fetch_one(
        "select class_Name, class_type, sname, semail FROM Student_Class "
        "where s_id=? and class_id=? and status='Active'",
        (student_id, class_id),
    )


def next_feedback_id(table):
    """
    Reproduces getCfeedbackID():

        select fid from feedbackOffline order by fid desc

    ...takes the first row and adds one, or returns 1 when the table is empty.
    The original does not use an identity column here, so this behaviour is
    kept as-is.
    """
    row = fetch_one("select top 1 fid from %s order by fid desc" % table)
    if row and row["fid"] is not None:
        return int(row["fid"]) + 1
    return 1


def save_offline_feedback(class_id, student_id, answers, comment, uname):
    """Reproduces the INSERT in feedbackOffline.aspx.cs Button1_Click."""
    fid = next_feedback_id("feedbackOffline")
    columns = [column for _, column, _ in OFFLINE_FIELDS]
    values = [answers[control] for control, _, _ in OFFLINE_FIELDS]

    sql = (
        "insert into feedbackOffline (fid, sid, classID, {cols}, comment, uname) "
        "values ({marks})".format(
            cols=", ".join(columns),
            marks=", ".join(["?"] * (3 + len(columns) + 2)),
        )
    )
    return execute(sql, tuple([fid, student_id, class_id] + values + [comment, uname]))


def save_online_feedback(class_id, student_id, answers, comment, uname):
    """Reproduces the INSERT in feedbackOnline.aspx.cs Button1_Click."""
    fid = next_feedback_id("feedbackOnline")
    columns = [column for _, column, _ in ONLINE_FIELDS]
    values = [answers[control] for control, _, _ in ONLINE_FIELDS]

    sql = (
        "insert into feedbackOnline (fid, uid, classID, {cols}, comment, uname) "
        "values ({marks})".format(
            cols=", ".join(columns),
            marks=", ".join(["?"] * (3 + len(columns) + 2)),
        )
    )
    return execute(sql, tuple([fid, student_id, class_id] + values + [comment, uname]))
