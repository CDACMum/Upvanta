"""Sample files used by the shell examples (written into ~/cdac before each run)."""

STUDENTS = """
roll_no,name,course,centre,city
2401,Anuj,PG-DBDA,Kharghar,Pune
2402,Vineeta,PG-DBDA,Kharghar,Navi Mumbai
2403,Aarshvi,PG-DAI,Juhu,Mumbai
2404,Rohan,PG-DAC,Juhu,Thane
2405,Meera,PG-DBDA,Kharghar,Pune
2406,Kabir,PG-DAI,Juhu,Mumbai
"""

MARKS = """
roll_no,subject,marks
2401,SQL,82
2401,Spark,61
2402,SQL,91
2402,Spark,88
2403,ML,84
2404,Java,58
2405,SQL,75
2406,ML,AB
2406,Python,72
"""

ACCESS_LOG = """
10.0.0.5 - - [13/Oct/2026:09:01:12 +0530] "GET /lms/login HTTP/1.1" 200 512
10.0.0.7 - - [13/Oct/2026:09:01:40 +0530] "GET /lms/course/dbda HTTP/1.1" 200 2048
10.0.0.5 - - [13/Oct/2026:09:02:03 +0530] "POST /lms/quiz/submit HTTP/1.1" 200 128
10.0.0.9 - - [13/Oct/2026:09:15:22 +0530] "GET /lms/notes/hive.pdf HTTP/1.1" 404 0
10.0.0.5 - - [13/Oct/2026:10:05:10 +0530] "GET /lms/notes/spark.pdf HTTP/1.1" 200 90112
10.0.0.7 - - [13/Oct/2026:10:06:45 +0530] "GET /lms/admin HTTP/1.1" 403 64
10.0.0.12 - - [13/Oct/2026:10:30:00 +0530] "GET /lms/login HTTP/1.1" 200 512
10.0.0.9 - - [13/Oct/2026:11:00:01 +0530] "GET /lms/notes/kafka.pdf HTTP/1.1" 404 0
10.0.0.5 - - [13/Oct/2026:11:20:33 +0530] "GET /lms/course/dbda HTTP/1.1" 500 0
10.0.0.7 - - [13/Oct/2026:11:45:09 +0530] "POST /lms/quiz/submit HTTP/1.1" 200 128
"""

APP_LOG = """
2026-10-13 09:00:01 INFO  Starting result-processing job
2026-10-13 09:00:05 INFO  Loaded 120 students
2026-10-13 09:00:07 WARN  Missing marks for roll 2406 (ML)
2026-10-13 09:00:09 ERROR Cannot connect to MySQL at 10.0.0.20:3306
2026-10-13 09:00:19 INFO  Retrying connection
2026-10-13 09:00:21 INFO  Connected
2026-10-13 09:00:40 ERROR Duplicate key 2402-SQL
2026-10-13 09:01:02 INFO  Job finished in 61s
"""

COMMON = {'students.csv': STUDENTS, 'marks.csv': MARKS}
