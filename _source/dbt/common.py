STG_STUDENTS = """
select
    roll_no                 as student_id,
    trim(name)              as student_name,
    course                  as course_code,
    centre,
    city,
    cast(joined_on as date) as joined_on
from {{ ref('raw_students') }}
"""

STG_MARKS = """
select
    roll_no                   as student_id,
    subject,
    cast(marks as integer)    as marks,
    cast(exam_date as date)   as exam_date
from {{ ref('raw_marks') }}
"""

STG_COURSES = """
select
    course_code,
    course_name,
    months      as duration_months,
    fee
from {{ ref('raw_courses') }}
"""

STAGING = {
    'models/staging/stg_students.sql': STG_STUDENTS,
    'models/staging/stg_marks.sql': STG_MARKS,
    'models/staging/stg_courses.sql': STG_COURSES,
}
