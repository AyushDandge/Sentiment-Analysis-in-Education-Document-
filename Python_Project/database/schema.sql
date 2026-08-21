/* ============================================================================
   Educational_Post_Analysis  --  Microsoft SQL Server schema
   ----------------------------------------------------------------------------
   Python version of "Design and Deployment of Sentimental Analysis in Education"

   The two tables that existed in the original dump (anliss.sql) are reproduced
   exactly.  The remaining tables were reconstructed from the SQL statements
   found in the original C# code-behind files, because anliss.sql only contained
   studentRegistration and User_review.

   IMPORTANT -- do not "tidy up" the rType text values inserted below.
   Three of them begin with an invisible U+2060 WORD JOINER character, exactly
   as they appear in the original C# source (AnalysisOffline.aspx.cs line 77).
   The analysis pages match on these strings with
       UPDATE AnalysisOffline SET ... WHERE rType = '<value>'
   so if the character is removed here the update silently matches no rows and
   the analysis table stays at zero.  This file is saved as UTF-8.

   Run this whole file once in SQL Server Management Studio (or with sqlcmd)
   BEFORE starting the Python application.
   ========================================================================== */

USE [master]
GO

/* ---------------------------------------------------------------- database */
IF DB_ID('Educational_Post_Analysis') IS NULL
    CREATE DATABASE [Educational_Post_Analysis]
GO

USE [Educational_Post_Analysis]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO


/* ==========================================================================
   1. studentRegistration      (original -- preserved from anliss.sql)
      Used by: login.aspx.cs, registration.aspx.cs
   ========================================================================== */
IF OBJECT_ID('dbo.studentRegistration', 'U') IS NULL
CREATE TABLE [dbo].[studentRegistration](
    [std_id]    [int] IDENTITY(1,1) NOT NULL,
    [Fullname]  [nvarchar](max) NULL,
    [Email]     [nvarchar](max) NULL,
    [mobile]    [nvarchar](50)  NULL,
    [password]  [nvarchar](max) NULL,
    CONSTRAINT [PK_studentRegistration] PRIMARY KEY CLUSTERED ([std_id] ASC)
)
GO


/* ==========================================================================
   2. User_review              (original -- preserved from anliss.sql)
      Kept for fidelity with the original database.
   ========================================================================== */
IF OBJECT_ID('dbo.User_review', 'U') IS NULL
CREATE TABLE [dbo].[User_review](
    [rv_id]    [int] IDENTITY(1,1) NOT NULL,
    [std_id]   [int] NULL,
    [mode]     [nvarchar](50)  NULL,
    [subject]  [nvarchar](max) NULL,
    [contain]  [nvarchar](max) NULL,
    [review]   [nvarchar](max) NULL,
    CONSTRAINT [PK_User_review] PRIMARY KEY CLUSTERED ([rv_id] ASC)
)
GO


/* ==========================================================================
   3. ClassesRegistration      (reconstructed)
      Referenced by: viewClassesOffine/Online.aspx.cs, Joined_Class.aspx.cs,
                     AnalysisOffline/Online.aspx.cs
      classID is read with dr.GetInt32(1)  -> int
      className is read with dr.GetString(0) -> nvarchar
   ========================================================================== */
IF OBJECT_ID('dbo.ClassesRegistration', 'U') IS NULL
CREATE TABLE [dbo].[ClassesRegistration](
    [classID]   [int] IDENTITY(1,1) NOT NULL,
    [className] [nvarchar](200) NOT NULL,
    [city]      [nvarchar](100) NULL,
    [Area]      [nvarchar](100) NULL,
    [rating]    [nvarchar](50)  NULL,
    [classType] [nvarchar](50)  NULL,   -- 'Online' / 'Offline'
    [status]    [nvarchar](50)  NULL,   -- 'Active' / 'Deactive'
    CONSTRAINT [PK_ClassesRegistration] PRIMARY KEY CLUSTERED ([classID] ASC)
)
GO


/* ==========================================================================
   4. Student_Class            (reconstructed)
      Referenced by: Joined_Class.aspx.cs (insert + duplicate check),
                     viewClasses*.aspx.cs (membership check),
                     Admin/view_user.aspx.cs (J_id, status toggle)
   ========================================================================== */
IF OBJECT_ID('dbo.Student_Class', 'U') IS NULL
CREATE TABLE [dbo].[Student_Class](
    [J_id]       [int] IDENTITY(1,1) NOT NULL,
    [class_id]   [int] NULL,
    [s_id]       [int] NULL,
    [class_Name] [nvarchar](200) NULL,
    [class_type] [nvarchar](50)  NULL,   -- 'Online' / 'Offline'
    [sname]      [nvarchar](200) NULL,
    [semail]     [nvarchar](200) NULL,
    [status]     [nvarchar](50)  NULL,   -- 'Active' / 'Deactive'
    CONSTRAINT [PK_Student_Class] PRIMARY KEY CLUSTERED ([J_id] ASC)
)
GO


/* ==========================================================================
   5. feedbackOffline          (reconstructed)

      COLUMN ORDER IS SIGNIFICANT.  AnalysisOffline.aspx.cs runs
          select * from feedbackOffline where classID=...
      and then reads the reader by ORDINAL:
          index 3 .. 12  -> the ten rating answers   (dr.GetString(i))
          index 13       -> comment                  (passed to find())
      Because the values are read with GetString they are stored as nvarchar,
      exactly as the original code inserts them (rbl...SelectedValue.ToString()).

      fid is NOT an identity column -- feedbackOffline.aspx.cs computes the next
      id itself in getCfeedbackID() and supplies it explicitly.
   ========================================================================== */
IF OBJECT_ID('dbo.feedbackOffline', 'U') IS NULL
CREATE TABLE [dbo].[feedbackOffline](
    [fid]                                          [int] NOT NULL,   -- 0
    [sid]                                          [int] NULL,       -- 1
    [classID]                                      [int] NULL,       -- 2
    [Content_Quality]                              [nvarchar](50) NULL,  -- 3
    [Instructor_Effectiveness]                     [nvarchar](50) NULL,  -- 4
    [Classroom_Audio_Quality]                      [nvarchar](50) NULL,  -- 5
    [Classroom_Visibility_And_Presentation_Quality][nvarchar](50) NULL,  -- 6
    [Learning_Experience]                          [nvarchar](50) NULL,  -- 7
    [Accessibility_And_Convenience]                [nvarchar](50) NULL,  -- 8
    [Engagement_And_Interactivity]                 [nvarchar](50) NULL,  -- 9
    [Infrastructure_And_Facilities]                [nvarchar](50) NULL,  -- 10
    [Assessment_And_Feedback]                      [nvarchar](50) NULL,  -- 11
    [Career_Impact_Skill_Development]              [nvarchar](50) NULL,  -- 12
    [comment]                                      [nvarchar](max) NULL, -- 13
    [uname]                                        [nvarchar](200) NULL, -- 14
    CONSTRAINT [PK_feedbackOffline] PRIMARY KEY CLUSTERED ([fid] ASC)
)
GO


/* ==========================================================================
   6. feedbackOnline           (reconstructed)
      Same ordinal contract as feedbackOffline.  Note the online questionnaire
      replaces the two classroom questions with video / audio quality and
      "Infrastructure And Facilities" with "Technical Issues".
      Note also that the online table calls the student column "uid", not "sid"
      -- that difference is in the original code and is preserved here.
   ========================================================================== */
IF OBJECT_ID('dbo.feedbackOnline', 'U') IS NULL
CREATE TABLE [dbo].[feedbackOnline](
    [fid]                                 [int] NOT NULL,        -- 0
    [uid]                                 [int] NULL,            -- 1
    [classID]                             [int] NULL,            -- 2
    [Content_Quality]                     [nvarchar](50) NULL,   -- 3
    [Instructor_Effectiveness]            [nvarchar](50) NULL,   -- 4
    [Video_Quality_Delivery]              [nvarchar](50) NULL,   -- 5
    [Audio_Quality]                       [nvarchar](50) NULL,   -- 6
    [Learning_Experience]                 [nvarchar](50) NULL,   -- 7
    [Accessibility_and_Convenience]       [nvarchar](50) NULL,   -- 8
    [Engagement_and_Interactivity]        [nvarchar](50) NULL,   -- 9
    [Technical_Issues]                    [nvarchar](50) NULL,   -- 10
    [Assessment_and_Feedback]             [nvarchar](50) NULL,   -- 11
    [Career_Impact_and_Skill_Development] [nvarchar](50) NULL,   -- 12
    [comment]                             [nvarchar](max) NULL,  -- 13
    [uname]                               [nvarchar](200) NULL,  -- 14
    CONSTRAINT [PK_feedbackOnline] PRIMARY KEY CLUSTERED ([fid] ASC)
)
GO


/* ==========================================================================
   7. AnalysisOffline / AnalysisOnline    (reconstructed)
      One fixed row per review parameter.  The analysis page UPDATEs these rows
      (it never inserts), so the 11 rows below must exist.
      Displayed by the GridView:  rType | negative | neutral | positive |
                                  p_negative | p_neutral | p_positive
      ordered by id.
   ========================================================================== */
IF OBJECT_ID('dbo.AnalysisOffline', 'U') IS NULL
CREATE TABLE [dbo].[AnalysisOffline](
    [id]         [int] IDENTITY(1,1) NOT NULL,
    [rType]      [nvarchar](200) NOT NULL,
    [negative]   [int] NULL DEFAULT 0,
    [neutral]    [int] NULL DEFAULT 0,
    [positive]   [int] NULL DEFAULT 0,
    [p_negative] [float] NULL DEFAULT 0,
    [p_neutral]  [float] NULL DEFAULT 0,
    [p_positive] [float] NULL DEFAULT 0,
    CONSTRAINT [PK_AnalysisOffline] PRIMARY KEY CLUSTERED ([id] ASC)
)
GO

IF OBJECT_ID('dbo.AnalysisOnline', 'U') IS NULL
CREATE TABLE [dbo].[AnalysisOnline](
    [id]         [int] IDENTITY(1,1) NOT NULL,
    [rType]      [nvarchar](200) NOT NULL,
    [negative]   [int] NULL DEFAULT 0,
    [neutral]    [int] NULL DEFAULT 0,
    [positive]   [int] NULL DEFAULT 0,
    [p_negative] [float] NULL DEFAULT 0,
    [p_neutral]  [float] NULL DEFAULT 0,
    [p_positive] [float] NULL DEFAULT 0,
    CONSTRAINT [PK_AnalysisOnline] PRIMARY KEY CLUSTERED ([id] ASC)
)
GO


/* ==========================================================================
   8. AnalysisReviewOffline / AnalysisReviewOnline   (reconstructed)
      Three fixed rows feeding the "Total Review Analysis" chart.
   ========================================================================== */
IF OBJECT_ID('dbo.AnalysisReviewOffline', 'U') IS NULL
CREATE TABLE [dbo].[AnalysisReviewOffline](
    [id]    [int] IDENTITY(1,1) NOT NULL,
    [ctype] [nvarchar](50) NOT NULL,
    [count] [int] NULL DEFAULT 0,
    CONSTRAINT [PK_AnalysisReviewOffline] PRIMARY KEY CLUSTERED ([id] ASC)
)
GO

IF OBJECT_ID('dbo.AnalysisReviewOnline', 'U') IS NULL
CREATE TABLE [dbo].[AnalysisReviewOnline](
    [id]    [int] IDENTITY(1,1) NOT NULL,
    [ctype] [nvarchar](50) NOT NULL,
    [count] [int] NULL DEFAULT 0,
    CONSTRAINT [PK_AnalysisReviewOnline] PRIMARY KEY CLUSTERED ([id] ASC)
)
GO


/* ==========================================================================
   9. tabular                  (reconstructed, legacy)
      Only written by viewClassesOnline.aspx.cs btntabu_Click, which is
      commented out in the original markup.  Recreated so the database matches
      the original object list.
   ========================================================================== */
IF OBJECT_ID('dbo.tabular', 'U') IS NULL
CREATE TABLE [dbo].[tabular](
    [id]           [int] IDENTITY(1,1) NOT NULL,
    [StationID]    [nvarchar](50)  NULL,
    [StationName]  [nvarchar](200) NULL,
    [City]         [nvarchar](100) NULL,
    [VehicleTypes] [nvarchar](100) NULL,
    [no_of_review] [nvarchar](50)  NULL,
    [yes_review]   [nvarchar](50)  NULL,
    [no_review]    [nvarchar](50)  NULL,
    [percentage]   [nvarchar](50)  NULL,
    CONSTRAINT [PK_tabular] PRIMARY KEY CLUSTERED ([id] ASC)
)
GO


/* ==========================================================================
   FIXED ROWS -- required for the analysis screens to work at all
   ========================================================================== */

/* -- AnalysisOffline: the 11 offline parameters, in the exact order and with
      the exact text used by AnalysisOffline.aspx.cs                        */
IF NOT EXISTS (SELECT 1 FROM [dbo].[AnalysisOffline])
INSERT INTO [dbo].[AnalysisOffline] ([rType],[negative],[neutral],[positive],[p_negative],[p_neutral],[p_positive]) VALUES
 (N'Content Quality',                             0,0,0,0,0,0),
 (N'Instructor Effectiveness',                    0,0,0,0,0,0),
 (N'Classroom Audio Quality',                     0,0,0,0,0,0),
 (N'Classroom Visibility & Presentation Quality', 0,0,0,0,0,0),
 (N'Learning Experience',                         0,0,0,0,0,0),
 (N'Accessibility & Convenience',                 0,0,0,0,0,0),
 (N'⁠Engagement & Interactivity',                  0,0,0,0,0,0),
 (N'Infrastructure & Facilities',                 0,0,0,0,0,0),
 (N'⁠Assessment & Feedback',                       0,0,0,0,0,0),
 (N'⁠Career Impact & Skill Development',           0,0,0,0,0,0),
 (N'Comment',                                     0,0,0,0,0,0)
GO

/* -- AnalysisOnline: the 11 online parameters                              */
IF NOT EXISTS (SELECT 1 FROM [dbo].[AnalysisOnline])
INSERT INTO [dbo].[AnalysisOnline] ([rType],[negative],[neutral],[positive],[p_negative],[p_neutral],[p_positive]) VALUES
 (N'Content Quality',                    0,0,0,0,0,0),
 (N'Instructor Effectiveness',           0,0,0,0,0,0),
 (N'Video Quality & Delivery',           0,0,0,0,0,0),
 (N'Audio Quality',                      0,0,0,0,0,0),
 (N'Learning Experience',                0,0,0,0,0,0),
 (N'Accessibility & Convenience',        0,0,0,0,0,0),
 (N'⁠Engagement & Interactivity',         0,0,0,0,0,0),
 (N'Technical Issues',                   0,0,0,0,0,0),
 (N'⁠Assessment & Feedback',              0,0,0,0,0,0),
 (N'⁠Career Impact & Skill Development',  0,0,0,0,0,0),
 (N'Comment',                            0,0,0,0,0,0)
GO

/* -- chart rows                                                            */
IF NOT EXISTS (SELECT 1 FROM [dbo].[AnalysisReviewOffline])
INSERT INTO [dbo].[AnalysisReviewOffline] ([ctype],[count]) VALUES
 (N'Positive',0), (N'Negative',0), (N'Neutral',0)
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[AnalysisReviewOnline])
INSERT INTO [dbo].[AnalysisReviewOnline] ([ctype],[count]) VALUES
 (N'Positive',0), (N'Negative',0), (N'Neutral',0)
GO


/* ==========================================================================
   DEMO DATA
   The three students below are the original rows from anliss.sql.
   Everything after them is sample data so that you can log in and see the
   screens working immediately.  Delete this whole section if you want to
   start from an empty system.
   ========================================================================== */

IF NOT EXISTS (SELECT 1 FROM [dbo].[studentRegistration])
BEGIN
    SET IDENTITY_INSERT [dbo].[studentRegistration] ON
    INSERT INTO [dbo].[studentRegistration] ([std_id],[Fullname],[Email],[mobile],[password]) VALUES
     (1, N'rudra Koli', N'r@gmail.com',    N'7412589658', N'1122'),
     (2, N'sham sha',   N'sham@gmail.com', N'7458896587', N'7744'),
     (3, N'rames ',     N're@gmail.com',   N'7485698745', N'1144')
    SET IDENTITY_INSERT [dbo].[studentRegistration] OFF
END
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[User_review])
BEGIN
    SET IDENTITY_INSERT [dbo].[User_review] ON
    INSERT INTO [dbo].[User_review] ([rv_id],[std_id],[mode],[subject],[contain],[review]) VALUES
     (1, 1, N'Online Education', N'just demo',
      N'we will definitely give to you don''t warry', N' write now it just review  go through ')
    SET IDENTITY_INSERT [dbo].[User_review] OFF
END
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[ClassesRegistration])
INSERT INTO [dbo].[ClassesRegistration] ([className],[city],[Area],[rating],[classType],[status]) VALUES
 (N'Python Programming',   N'Pune',   N'Kothrud',      N'4', N'Online',  N'Active'),
 (N'Data Structures',      N'Pune',   N'Shivaji Nagar',N'4', N'Online',  N'Active'),
 (N'Machine Learning',     N'Mumbai', N'Andheri',      N'5', N'Online',  N'Active'),
 (N'Java Programming',     N'Pune',   N'Hadapsar',     N'4', N'Offline', N'Active'),
 (N'Database Management',  N'Nashik', N'College Road', N'3', N'Offline', N'Active'),
 (N'Web Development',      N'Mumbai', N'Dadar',        N'5', N'Offline', N'Active')
GO

/* student 1 (r@gmail.com / 1122) is enrolled in one online and one offline
   class, so the Rating buttons on the search screens work straight away.   */
IF NOT EXISTS (SELECT 1 FROM [dbo].[Student_Class])
INSERT INTO [dbo].[Student_Class] ([class_id],[s_id],[class_Name],[class_type],[sname],[semail],[status]) VALUES
 (1, 1, N'Python Programming', N'Online',  N'rudra Koli', N'r@gmail.com',    N'Active'),
 (4, 1, N'Java Programming',   N'Offline', N'rudra Koli', N'r@gmail.com',    N'Active'),
 (1, 2, N'Python Programming', N'Online',  N'sham sha',   N'sham@gmail.com', N'Active'),
 (4, 3, N'Java Programming',   N'Offline', N'rames ',     N're@gmail.com',   N'Active')
GO

/* Sample feedback so the Naive Bayes screens have something to analyse.
   Ratings are stored as text, exactly as the application inserts them.     */
IF NOT EXISTS (SELECT 1 FROM [dbo].[feedbackOnline])
INSERT INTO [dbo].[feedbackOnline]
 ([fid],[uid],[classID],[Content_Quality],[Instructor_Effectiveness],[Video_Quality_Delivery],
  [Audio_Quality],[Learning_Experience],[Accessibility_and_Convenience],[Engagement_and_Interactivity],
  [Technical_Issues],[Assessment_and_Feedback],[Career_Impact_and_Skill_Development],[comment],[uname])
VALUES
 (1, 1, 1, N'5',N'4',N'4',N'5',N'5',N'4',N'3',N'2',N'4',N'5', N'I LIKE THIS CLASS',        N'rudra Koli'),
 (2, 2, 1, N'4',N'5',N'3',N'4',N'4',N'3',N'4',N'1',N'5',N'4', N'GOOD TEACHING',            N'sham sha'),
 (3, 1, 2, N'2',N'1',N'3',N'2',N'3',N'2',N'1',N'0',N'2',N'3', N'NOT GOOD',                 N'rudra Koli')
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[feedbackOffline])
INSERT INTO [dbo].[feedbackOffline]
 ([fid],[sid],[classID],[Content_Quality],[Instructor_Effectiveness],[Classroom_Audio_Quality],
  [Classroom_Visibility_And_Presentation_Quality],[Learning_Experience],[Accessibility_And_Convenience],
  [Engagement_And_Interactivity],[Infrastructure_And_Facilities],[Assessment_And_Feedback],
  [Career_Impact_Skill_Development],[comment],[uname])
VALUES
 (1, 1, 4, N'5',N'5',N'4',N'4',N'5',N'4',N'4',N'5',N'4',N'5', N'EXCELLENT CLASS',   N'rudra Koli'),
 (2, 3, 4, N'4',N'4',N'3',N'3',N'4',N'5',N'3',N'4',N'4',N'4', N'GOOD',              N'rames '),
 (3, 1, 5, N'1',N'2',N'0',N'1',N'2',N'1',N'2',N'0',N'1',N'2', N'BAD CLASS',         N'rudra Koli')
GO

PRINT 'Educational_Post_Analysis schema created successfully.'
GO
