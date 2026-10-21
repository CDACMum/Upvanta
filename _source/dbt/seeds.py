"""Raw data loaded as seeds into every example project (the 'raw' layer of the C-DAC warehouse)."""
SEEDS = {
    'seeds/raw_students.csv': """roll_no,name,course,centre,city,joined_on
2401,Anuj,PG-DBDA,Kharghar,Pune,2026-08-01
2402,Vineeta,PG-DBDA,Kharghar,Navi Mumbai,2026-08-01
2403,Aarshvi,PG-DAC,Juhu,Mumbai,2026-08-02
2404,Rohit,PG-DAC,Juhu,Thane,2026-08-02
2405,Meera,PG-DBDA,Kharghar,Pune,2026-08-03
2406,Kabir,PG-DAI,Juhu,Mumbai,2026-08-03
""",
    'seeds/raw_marks.csv': """roll_no,subject,marks,exam_date
2401,SQL,82,2026-09-20
2401,Spark,61,2026-10-10
2402,SQL,91,2026-09-20
2402,Spark,88,2026-10-10
2403,Java,84,2026-09-21
2404,Java,58,2026-09-21
2405,SQL,75,2026-09-20
2406,ML,72,2026-10-11
""",
    'seeds/raw_courses.csv': """course_code,course_name,months,fee
PG-DBDA,Big Data Analytics,6,95000
PG-DAC,Advanced Computing,6,90000
PG-DAI,Artificial Intelligence,6,98000
""",
}
