"""
Naive Bayes sentiment analysis.

This is a direct port of the Page_Load method and the find() helper in
    UserNew/AnalysisOffline.aspx.cs
    UserNew/AnalysisOnline.aspx.cs

The two C# files are identical apart from the table names, the list of review
parameters and one divisor, so they are handled here by a single function with
a `mode` argument.

The calculations, the rounding and the decision thresholds are reproduced
exactly, including a few quirks in the original code that are called out in the
comments below.  They are kept on purpose: changing them would change the
numbers the application reports.
"""

from database.db_connection import execute, fetch_all, fetch_rows

# ---------------------------------------------------------------------------
# The review parameters, copied character for character from the C# source.
#
# WARNING: three of these strings begin with an invisible U+2060 WORD JOINER
# ("⁠").  That character is present in the original C# array and therefore
# also in database/schema.sql.  The UPDATE statements match on these strings, so
# the character must not be removed from either place.
# ---------------------------------------------------------------------------
OFFLINE_RTYPES = [
    "Content Quality",
    "Instructor Effectiveness",
    "Classroom Audio Quality",
    "Classroom Visibility & Presentation Quality",
    "Learning Experience",
    "Accessibility & Convenience",
    "⁠Engagement & Interactivity",
    "Infrastructure & Facilities",
    "⁠Assessment & Feedback",
    "⁠Career Impact & Skill Development",
    "Comment",
]

ONLINE_RTYPES = [
    "Content Quality",
    "Instructor Effectiveness",
    "Video Quality & Delivery",
    "Audio Quality",
    "Learning Experience",
    "Accessibility & Convenience",
    "⁠Engagement & Interactivity",
    "Technical Issues",
    "⁠Assessment & Feedback",
    "⁠Career Impact & Skill Development",
    "Comment",
]

# Word lists used by find(), taken from the C# source.
STOP_WORDS = ["I", "THIS"]
NEGATIVE_WORDS = ["NOT", "DISLIKE", "BAD"]
POSITIVE_WORDS = ["GOOD", "EXCELLENT", "LIKE"]


def _find(comment, positive, negative, neutral):
    """
    Port of  void find(string comment1).

    Scores a free text comment and increases one of the counters for the
    "Comment" parameter.

    Two details of the original are preserved deliberately:
      * only the FIRST occurrence of each stop word is removed, because the C#
        loop breaks after its first match;
      * on the positive branch the C# increments positive[5] rather than
        positive[10], so a positive comment is credited to "Accessibility &
        Convenience" instead of "Comment".  That is a bug in the original, but
        reproducing it keeps the Python output identical to the C# output.
    """
    comment = (comment or "").upper()
    tokens = comment.split(" ")

    remaining = list(tokens)
    for word in STOP_WORDS:
        for index, token in enumerate(tokens):
            if word == token:
                del remaining[index]
                break
        tokens = list(remaining)

    pos = sum(1 for token in tokens if token in POSITIVE_WORDS)
    neg = sum(1 for token in tokens if token in NEGATIVE_WORDS)

    if neg == pos:
        neutral[10] += 1
    elif neg >= 1:
        negative[10] += 1
    else:
        positive[5] += 1  # original index, see docstring


def _count_answers(feedback_rows, positive, negative, neutral):
    """
    Port of the  while (dr.Read())  loop.

    Columns 3 to 12 of the feedback table hold the ten ratings and column 13
    holds the comment, so the loop walks ordinals 3..13 and maps them onto
    parameters 0..10:
        rating 0 or 1 -> negative
        rating 2 or 3 -> neutral
        rating 4 or 5 -> positive
    """
    for row in feedback_rows:
        j = 0
        for i in range(3, 14):
            if i == 13:
                _find(row[i], positive, negative, neutral)
            else:
                try:
                    value = int(row[i])
                except (TypeError, ValueError):
                    # A question that was left blank. The C# would have thrown
                    # a FormatException here; skipping keeps the page usable.
                    j += 1
                    continue

                if value in (0, 1):
                    negative[j] += 1
                elif value in (2, 3):
                    neutral[j] += 1
                elif value in (4, 5):
                    positive[j] += 1
            j += 1


def run_analysis(mode, class_id):
    """
    Run the whole analysis for one class and return everything the page shows.

    mode is "Offline" or "Online".

    Returns a dictionary with:
        rows            - the AnalysisOffline/AnalysisOnline table, in id order
        chart           - the AnalysisReview... rows for the bar chart
        comments        - the user comments listed under "User Review's"
        total_review    - text for lblTotalReview
        probability     - text for lblProbability
        status          - text for lblStatus
        status_colour   - the colour the original set on lblStatus
    """
    if mode == "Offline":
        feedback_table = "feedbackOffline"
        analysis_table = "AnalysisOffline"
        review_table = "AnalysisReviewOffline"
        rtypes = OFFLINE_RTYPES
        divisor = 11          # AnalysisOffline.aspx.cs:  total_pos_Probability /= 11
    else:
        feedback_table = "feedbackOnline"
        analysis_table = "AnalysisOnline"
        review_table = "AnalysisReviewOnline"
        rtypes = ONLINE_RTYPES
        divisor = 5           # AnalysisOnline.aspx.cs:   total_pos_Probability /= 5

    positive = [0] * 11
    negative = [0] * 11
    neutral = [0] * 11

    # ---- 1. count the raw answers -------------------------------------
    feedback_rows = fetch_rows(
        "select * from %s where classID=?" % feedback_table, (class_id,)
    )
    _count_answers(feedback_rows, positive, negative, neutral)

    # ---- 2. write the counts back to the analysis table ---------------
    for j, rtype in enumerate(rtypes):
        execute(
            "update %s set negative=?, neutral=?, positive=? where rType=?"
            % analysis_table,
            (negative[j], neutral[j], positive[j], rtype),
        )

    # ---- 3. read the analysis table back ------------------------------
    # In the C# this data came from GridView1, which is bound to
    # "SELECT * from AnalysisOffline order by id".  Reading the same rows from
    # the database gives the values the grid displays.
    grid = fetch_all("SELECT * from %s order by id" % analysis_table)

    tnc = sum(int(row["negative"] or 0) for row in grid)   # total negative
    tnec = sum(int(row["neutral"] or 0) for row in grid)   # total neutral
    tpc = sum(int(row["positive"] or 0) for row in grid)   # total positive

    # ---- 4. update the chart totals -----------------------------------
    execute("update %s set count=? where ctype='Positive'" % review_table, (tpc,))
    execute("update %s set count=? where ctype='Negative'" % review_table, (tnc,))
    execute("update %s set count=? where ctype='Neutral'" % review_table, (tnec,))

    # ---- 5. Bayes' theorem --------------------------------------------
    #   P(Yes | Management) = P(Management | Yes) * P(Yes) / P(Management)
    #
    # Note that all three branches divide by tnec (the neutral total) when
    # computing p_nc.  That is what the C# does; it is preserved here.
    total_count = float(tnc + tnec + tpc)

    for j, rtype in enumerate(rtypes):
        row = grid[j]
        row_negative = int(row["negative"] or 0)
        row_neutral = int(row["neutral"] or 0)
        row_positive = int(row["positive"] or 0)
        item_total = float(row_negative + row_neutral + row_positive)

        p_negative = 0.0
        p_neutral = 0.0
        p_positive = 0.0

        if tnc != 0:
            p_item_type1 = row_negative / float(tnc)
            p_item1 = item_total / total_count if total_count else 0.0
            p_nc1 = tnec / total_count if total_count else 0.0
            p_negative = p_item_type1 * p_nc1 / p_item1 if p_item1 else 0.0

        if tnec != 0:
            p_item_type2 = row_neutral / float(tnec)
            p_item2 = item_total / total_count if total_count else 0.0
            p_nc2 = tnec / total_count if total_count else 0.0
            p_neutral = p_item_type2 * p_nc2 / p_item2 if p_item2 else 0.0

        if tpc != 0:
            p_item_type3 = row_positive / float(tpc)
            p_item3 = item_total / total_count if total_count else 0.0
            p_nc3 = tnec / total_count if total_count else 0.0
            p_positive = p_item_type3 * p_nc3 / p_item3 if p_item3 else 0.0

        execute(
            "update %s set p_negative=?, p_neutral=?, p_positive=? where rType=?"
            % analysis_table,
            (round(p_negative, 2), round(p_neutral, 2), round(p_positive, 2), rtype),
        )

    # ---- 6. read back the finished table for display ------------------
    grid = fetch_all("SELECT * from %s order by id" % analysis_table)

    total_pos_probability = sum(float(row["p_positive"] or 0) for row in grid)
    total_pos_probability /= divisor

    first = grid[0] if grid else {"negative": 0, "neutral": 0, "positive": 0}
    total_review = (
        int(first["negative"] or 0)
        + int(first["neutral"] or 0)
        + int(first["positive"] or 0)
    )

    # Thresholds and colours copied from the C#.
    if total_pos_probability <= 0.25:
        status, status_colour = "Not Suggested", "Red"
    elif total_pos_probability <= 0.6:
        status, status_colour = "Your Choice..", "Purple"
    else:
        status, status_colour = "Suggested", "Green"

    chart = fetch_all("SELECT [ctype], [count] FROM [%s]" % review_table)

    comments = fetch_rows(
        "select uname, comment from %s where classID=?" % feedback_table, (class_id,)
    )

    return {
        "rows": grid,
        "chart": chart,
        "comments": [{"uname": c[0], "comment": c[1]} for c in comments],
        "total_review": "Total Review :%d" % total_review,
        "probability": "Average Positive Probability = %.2f" % total_pos_probability,
        "status": status,
        "status_colour": status_colour,
    }
