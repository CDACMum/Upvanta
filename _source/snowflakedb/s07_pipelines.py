from build import *
from snowflakedb.anims import *
from snowflakedb.runner import sql, sq, pyrun, py

# target table + exactly the rows a standard stream on RAW_RESULTS would return after:
#   INSERT 2409, UPDATE 2402 (88 → 90), DELETE 2408
STREAM_ROWS = '''
CREATE OR REPLACE TABLE results_clean (roll_no INT, marks NUMBER(5,2), updated_by VARCHAR);
INSERT INTO results_clean SELECT roll_no, marks, 'initial load' FROM students;

CREATE OR REPLACE TABLE raw_results_s (roll_no INT, marks NUMBER(5,2),
       METADATA$ACTION VARCHAR, METADATA$ISUPDATE BOOLEAN, METADATA$ROW_ID VARCHAR);
INSERT INTO raw_results_s VALUES
  (2409, 81.00, 'INSERT', FALSE, 'r-2409'),
  (2402, 88.00, 'DELETE', TRUE,  'r-2402'),
  (2402, 90.00, 'INSERT', TRUE,  'r-2402'),
  (2408, 59.25, 'DELETE', FALSE, 'r-2408');
'''

SECTION = dict(level='advanced', title='Streams, Tasks, Dynamic Tables & Sharing', questions=[

# ------------------------------------------------------------------ 31
Q('What is a stream in Snowflake? How is it used for change data capture (CDC)?', 'Streams (CDC)', minutes=9, cards=[
    definition(
        defbox('A <strong>stream</strong> is an object that records the <strong>row-level changes</strong> (inserts, updates, deletes) made to a '
               'table, view or external table since the stream was last consumed. It stores only an <strong>offset</strong> into the table\'s version '
               'history, not a copy of the data. Selecting from it returns the changed rows plus metadata columns:'),
        table(['Column', 'Meaning'], [
            ['<code>METADATA$ACTION</code>', "'INSERT' or 'DELETE'"],
            ['<code>METADATA$ISUPDATE</code>', 'TRUE when the row is part of an UPDATE (which appears as a DELETE + INSERT pair)'],
            ['<code>METADATA$ROW_ID</code>', 'A stable unique ID for the row, to track it across changes'],
        ]),
        defbox('Types: <strong>standard</strong> (all DML; returns the net change), <strong>append-only</strong> (inserts only; cheaper; for '
               'insert-only tables), <strong>insert-only</strong> (for external and Iceberg tables). The offset advances only when the stream is read '
               'by a <strong>DML statement that commits</strong> (INSERT, MERGE…); a plain SELECT does not consume it.',
               'If a stream is not consumed within the table\'s data retention period it becomes <strong>stale</strong>. Snowflake extends retention '
               'for tables with streams, up to <code>MAX_DATA_EXTENSION_TIME_IN_DAYS</code> (14 days by default).'),
        tags('CREATE STREAM', 'METADATA$ACTION', 'METADATA$ISUPDATE', 'Offset', 'Append-only', 'Stale stream', 'CDC'),
    ),
    analogy('A stream is a <strong>bookmark with sticky notes</strong> in a ledger: it shows every entry added or crossed out since you last '
            'processed the ledger. When you finish processing and sign off, the bookmark moves forward.'),
    stream_anim(),
    real_world(
        scenario('Keeping the clean results table in sync',
                 p('Centres keep inserting and correcting rows in <code>RAW_RESULTS</code>. A stream on it plus a MERGE every 5 minutes applies only '
                   'the changes to <code>RESULTS_CLEAN</code>, instead of rebuilding the whole table each time.')),
    ),
    example(
        sq('''
CREATE OR REPLACE STREAM raw_results_s ON TABLE raw_results;          -- standard stream
-- CREATE STREAM new_rows_s ON TABLE raw_results APPEND_ONLY = TRUE;

INSERT INTO raw_results VALUES (2409, 81.00);
UPDATE raw_results SET marks = 90.00 WHERE roll_no = 2402;
DELETE FROM raw_results WHERE roll_no = 2408;

SELECT * FROM raw_results_s;              -- does NOT consume the stream
SELECT SYSTEM$STREAM_HAS_DATA('RAW_RESULTS_S');
'''),
        p('A stream cannot be created in the emulator, so the next example puts <strong>exactly the rows the stream returns</strong> for those three '
          'statements into a table with the same columns, and runs the standard MERGE that consumes a stream:', top=True),
        sql('''
-- RAW_RESULTS_S here is a table holding the stream's rows; RESULTS_CLEAN starts as a copy of STUDENTS
SELECT * FROM raw_results_s ORDER BY roll_no, METADATA$ACTION;

MERGE INTO results_clean t
USING (SELECT * FROM raw_results_s
       WHERE NOT (METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE)) s   -- drop the "before" image of updates
ON t.roll_no = s.roll_no
WHEN MATCHED AND s.METADATA$ACTION = 'DELETE' THEN DELETE
WHEN MATCHED AND s.METADATA$ACTION = 'INSERT' THEN UPDATE SET marks = s.marks, updated_by = 'stream merge'
WHEN NOT MATCHED AND s.METADATA$ACTION = 'INSERT' THEN INSERT (roll_no, marks, updated_by)
                                                    VALUES (s.roll_no, s.marks, 'stream merge');

SELECT * FROM results_clean WHERE updated_by = 'stream merge' OR roll_no = 2408 ORDER BY roll_no;
SELECT COUNT(*) AS rows_now FROM results_clean;
''', setup=STREAM_ROWS, show='dml'),
        p('The update of 2402 arrives as a DELETE/INSERT pair with ISUPDATE = TRUE; filtering out its DELETE half turns it into one UPDATE. Result: one '
          'insert (2409), one update (2402), one delete (2408); 8 rows remain. In a real account this MERGE would also advance the stream\'s offset.', top=True),
        title='Example'),
    steps(
        ('Create the stream', 'Standard for full CDC; append-only for insert-only sources.'),
        ('Write the consuming MERGE', 'Handle INSERT, DELETE and the update pair.'),
        ('Run it in a transaction', 'A task does this automatically; the offset moves only on commit.'),
        ('Watch for staleness', 'SHOW STREAMS shows <code>stale_after</code>; consume more often than the retention period.'),
        title='Steps'),
    crossq(
        ('Can two consumers read the same changes?', 'Each stream has one offset. Create one stream per consumer on the same table so each processes '
         'changes independently.'),
        ('What does the stream return if a row is inserted and then deleted before consumption?', 'Nothing for that row: a standard stream returns the '
         'net change between the offset and now.'),
        ('Does a stream add storage cost?', 'The stream itself stores almost nothing, but it can cause the source table\'s changes to be retained longer '
         '(up to the data extension limit), which costs storage.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('What are tasks in Snowflake? How do you schedule and chain them?', 'Tasks & Task Graphs', minutes=8, cards=[
    definition(
        defbox('A <strong>task</strong> runs a single SQL statement, a call to a stored procedure, or procedural logic (Snowflake Scripting) on a '
               'schedule. The schedule is an interval (<code>\'5 MINUTE\'</code>) or a CRON expression with a time zone. Tasks can run on a named '
               '<strong>warehouse</strong> or, if no warehouse is given, on <strong>serverless</strong> compute that Snowflake sizes automatically.',
               'Tasks form <strong>task graphs</strong> (DAGs): child tasks declare <code>AFTER parent1, parent2</code>, and only the root task has a '
               'schedule. A <code>WHEN</code> condition, typically <code>SYSTEM$STREAM_HAS_DATA(\'stream\')</code>, skips a run (without starting '
               'compute) when there is nothing to do. New tasks are created <strong>suspended</strong>; <code>ALTER TASK … RESUME</code> starts them.'),
        tags('CREATE TASK', 'SCHEDULE', 'CRON', 'AFTER', 'Task graph', 'WHEN', 'Serverless task', 'TASK_HISTORY'),
    ),
    analogy('Tasks are <strong>alarm clocks</strong> with to-do notes. The root alarm rings at 2 a.m.; finishing one note rings the next ones; and an '
            'alarm can be set to stay silent if the in-tray is empty.'),
    task_anim(),
    real_world(
        scenario('Nightly result pipeline',
                 p('At 02:00 IST the root task loads new raw files, two child tasks clean results and attendance in parallel, and a final task rebuilds '
                   'the rank list after both finish. Each step uses a stream condition, so on holidays with no new data no credits are spent.')),
    ),
    example(
        sq('''
CREATE OR REPLACE TASK load_raw
  WAREHOUSE = etl_wh
  SCHEDULE  = 'USING CRON 0 2 * * * Asia/Kolkata'
AS
  COPY INTO raw_results FROM @s3_results PATTERN = '.*[.]csv';

CREATE OR REPLACE TASK clean_results
  WAREHOUSE = etl_wh
  AFTER load_raw
  WHEN SYSTEM$STREAM_HAS_DATA('RAW_RESULTS_S')
AS
  MERGE INTO results_clean t USING raw_results_s s ON t.roll_no = s.roll_no
  WHEN MATCHED THEN UPDATE SET marks = s.marks
  WHEN NOT MATCHED THEN INSERT (roll_no, marks) VALUES (s.roll_no, s.marks);

CREATE OR REPLACE TASK build_ranklist      -- serverless: no WAREHOUSE
  AFTER clean_results, clean_attendance
AS
  CALL refresh_ranklist();

-- resume children first, then the root (or use SYSTEM$TASK_DEPENDENTS_ENABLE)
ALTER TASK build_ranklist RESUME;
ALTER TASK clean_results  RESUME;
ALTER TASK load_raw       RESUME;

EXECUTE TASK load_raw;                     -- run once now, for testing

SELECT name, state, scheduled_time, completed_time, error_message
FROM   TABLE(INFORMATION_SCHEMA.TASK_HISTORY()) ORDER BY scheduled_time DESC LIMIT 20;
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Write and test the SQL by hand', 'Including the MERGE that consumes a stream.'),
        ('Create the root task with a schedule', 'CRON with an explicit time zone avoids UTC surprises.'),
        ('Add children with AFTER', 'Add WHEN conditions to skip empty runs.'),
        ('Resume the graph', 'Children first, then root; check privileges (EXECUTE TASK, warehouse USAGE).'),
        ('Monitor', 'TASK_HISTORY and the task graph view in Snowsight; set error notifications.'),
        title='Steps'),
    crossq(
        ('What happens if a run takes longer than the schedule interval?', 'By default the next run is skipped until the current run finishes '
         '(only one instance of a task graph runs at a time).'),
        ('Serverless or warehouse task?', 'Serverless suits short, regular tasks (Snowflake right-sizes and you pay only for use). A user-managed warehouse '
         'is better when tasks are heavy or can share a warehouse already running.'),
        ('Tasks vs Airflow?', 'Tasks are simple and run inside Snowflake. Airflow orchestrates across many systems (APIs, Spark, S3, Snowflake) with '
         'richer retries and monitoring. Many teams use Airflow for cross-system flows and tasks for in-Snowflake steps.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What are dynamic tables? How do they compare with streams + tasks and materialized views?', 'Dynamic Tables', minutes=8, cards=[
    definition(
        defbox('A <strong>dynamic table</strong> is defined by a query and a <strong>target lag</strong>; Snowflake refreshes it automatically so its '
               'contents are never more than that lag behind its sources. Refreshes are <strong>incremental</strong> when the query allows it '
               '(only changed rows processed) and full otherwise. Dynamic tables can read other dynamic tables, forming a declarative pipeline; '
               '<code>TARGET_LAG = DOWNSTREAM</code> means "refresh only when a downstream table needs it".'),
        table(['', 'Streams + tasks', 'Dynamic table', 'Materialized view'], [
            ['Style', 'Imperative (you write MERGE + schedule)', 'Declarative (you write SELECT + lag)', 'Declarative'],
            ['Joins / complex SQL', 'Anything', 'Most SQL incl. joins, aggregates, window functions', 'Single table, limited functions'],
            ['Freshness', 'Task schedule', 'TARGET_LAG (minutes to days)', 'Always current'],
            ['Main use', 'Custom CDC logic, SCD Type 2, side effects', 'Transformation pipelines', 'Speeding up repeated queries'],
        ]),
        tags('CREATE DYNAMIC TABLE', 'TARGET_LAG', 'Incremental refresh', 'DOWNSTREAM', 'Declarative pipeline'),
    ),
    analogy('Streams + tasks is giving a clerk step-by-step <strong>instructions</strong> on how to update the register. A dynamic table is telling '
            'the clerk <strong>what the register must show</strong> and "never more than 10 minutes out of date"; the clerk works out how.'),
    dynamic_anim(),
    real_world(
        scenario('Replacing 300 lines of MERGE code',
                 p('The centre-wise daily summary used a stream, a task and a 120-line MERGE. It became one dynamic table: '
                   '<code>SELECT centre, att_date, COUNT_IF(present) … GROUP BY ALL</code> with a 15-minute target lag. Snowflake handles the '
                   'incremental refresh, and the pipeline graph in Snowsight shows lag and refresh history.')),
    ),
    example(
        sq('''
CREATE OR REPLACE DYNAMIC TABLE exam_marks_dt
  TARGET_LAG = '5 minutes'
  WAREHOUSE  = etl_wh
AS
SELECT s.v:roll::INT AS roll_no, e.value:sub::STRING AS subject, e.value:m::INT AS marks
FROM   raw.submissions s, LATERAL FLATTEN(input => s.v:exams) e;

CREATE OR REPLACE DYNAMIC TABLE subject_stats_dt
  TARGET_LAG = '15 minutes'
  WAREHOUSE  = etl_wh
AS
SELECT subject, COUNT(*) AS candidates, AVG(marks)::NUMBER(5,2) AS avg_marks
FROM   exam_marks_dt
GROUP  BY subject;

ALTER DYNAMIC TABLE exam_marks_dt SET TARGET_LAG = DOWNSTREAM;   -- refresh only as needed by subject_stats_dt
ALTER DYNAMIC TABLE subject_stats_dt REFRESH;                     -- manual refresh
SHOW DYNAMIC TABLES;                                              -- refresh_mode: INCREMENTAL or FULL
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Write the transformation as a SELECT', 'Test it as a normal query.'),
        ('Create the dynamic table', 'Choose a target lag the business needs (shorter lag = more refreshes = more cost).'),
        ('Chain', 'Downstream dynamic tables read upstream ones; use DOWNSTREAM lag for intermediate steps.'),
        ('Check refresh mode', 'Make sure it is INCREMENTAL for large data; rewrite the query if it falls back to FULL.'),
        title='Steps'),
    crossq(
        ('Can you INSERT into a dynamic table?', 'No. Its contents come only from its query. To change data, change the sources or the query.'),
        ('When are streams + tasks still the right tool?', 'When you need procedural logic, calls to external functions, SCD Type 2 history with custom '
         'rules, or very precise control over when and how changes are applied.'),
        ('Does a smaller target lag guarantee fresher data?', 'It sets the goal; Snowflake schedules refreshes to meet it, as long as each refresh '
         'finishes in time on the chosen warehouse.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('Explain Secure Data Sharing. What are shares, reader accounts and the Marketplace?', 'Secure Data Sharing', minutes=8, cards=[
    definition(
        defbox('<strong>Secure Data Sharing</strong> gives another Snowflake account read-only access to selected objects <strong>without copying '
               'or moving data</strong>. The provider creates a <strong>share</strong>, grants it privileges on a database, schemas, tables and '
               '<strong>secure views</strong>, and adds consumer accounts. The consumer creates a database from the share and queries it with '
               '<strong>its own warehouse</strong>. Updates by the provider are visible immediately.',
               'A <strong>reader account</strong> is a Snowflake account created and paid for by the provider, for consumers who do not have '
               'Snowflake. <strong>Listings</strong> package shares with descriptions and terms, privately to chosen accounts or publicly on the '
               '<strong>Snowflake Marketplace</strong>; listings can be auto-fulfilled to other regions and clouds.'),
        tags('Share', 'Provider', 'Consumer', 'Secure view', 'Reader account', 'Listing', 'Marketplace'),
    ),
    analogy('Instead of photocopying the attendance register for the university (copies go out of date and can leak), you give their auditor a '
            '<strong>read-only window</strong> into your register that always shows the current page, and only the columns you allow.'),
    sharing_anim(),
    real_world(
        scenario('Sharing results with the university',
                 p('C-DAC shares a secure view of final results (roll number, course, grade, but no phone numbers) with the university\'s Snowflake account. '
                   'The university joins it with their own records using their warehouse. When a revaluation changes a grade, the university sees it '
                   'immediately, and C-DAC can revoke access at any time.')),
    ),
    example(
        sq('''
-- provider
CREATE SECURE VIEW results_for_university AS
SELECT roll_no, course, centre, grade FROM results_clean WHERE published = TRUE;

CREATE SHARE results_share;
GRANT USAGE  ON DATABASE exam                         TO SHARE results_share;
GRANT USAGE  ON SCHEMA   exam.mart                    TO SHARE results_share;
GRANT SELECT ON VIEW     exam.mart.results_for_university TO SHARE results_share;
ALTER SHARE results_share ADD ACCOUNTS = uniorg.uni_account;

-- consumer (in the university's account)
CREATE DATABASE cdac_results FROM SHARE cdacorg.cdac_account.results_share;
GRANT IMPORTED PRIVILEGES ON DATABASE cdac_results TO ROLE analyst;
SELECT grade, COUNT(*) FROM cdac_results.mart.results_for_university GROUP BY grade;

-- provider: a reader account for a consumer without Snowflake
CREATE MANAGED ACCOUNT pune_univ_reader ADMIN_NAME = 'reader_admin',
  ADMIN_PASSWORD = '********', TYPE = READER;
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Prepare what to share', 'Secure views to hide columns/rows and the underlying logic.'),
        ('Create the share and grant objects', 'USAGE on database and schema, SELECT on views/tables.'),
        ('Add consumers', 'Accounts in the same region; for others, use a listing with auto-fulfilment or replication.'),
        ('Consumer mounts the share', 'CREATE DATABASE … FROM SHARE, then grant IMPORTED PRIVILEGES to roles.'),
        ('Review regularly', 'SHOW SHARES; remove consumers who no longer need access.'),
        title='Steps'),
    crossq(
        ('Why must shared views be secure views?', 'A normal view\'s definition is visible and the optimiser could expose hidden rows through some query '
         'plans. Secure views hide the definition and prevent such leakage.'),
        ('Who pays for what?', 'Provider: storage of the data. Consumer: the compute used to query it. With reader accounts the provider also pays the '
         'compute.'),
        ('Can the consumer modify or re-share the data?', 'No. Shared databases are read-only, and the consumer cannot share them onwards. They can copy '
         'query results into their own tables (CTAS), so share only what they are allowed to keep.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How do you work with Snowflake from Python? Explain the connector, Snowpark, UDFs and stored procedures.', 'Python, Snowpark & UDFs', minutes=9, cards=[
    definition(
        table(['Tool', 'What it is', 'Runs where'], [
            ['<code>snowflake-connector-python</code>', 'DB-API driver: execute SQL, fetch rows, bind parameters, load pandas DataFrames '
             '(<code>write_pandas</code>)', 'Your machine sends SQL; the warehouse executes it'],
            ['Snowpark (Python / Java / Scala)', 'DataFrame API that is translated to SQL lazily', 'Inside a Snowflake warehouse'],
            ['UDF / UDTF', 'User-defined scalar or table function in SQL, Python, Java, Scala or JavaScript', 'Inside the warehouse, called from SQL'],
            ['Stored procedure', 'Multi-statement logic with control flow (Snowflake Scripting, Python, Java, Scala, JavaScript)', 'Inside Snowflake'],
            ['Snowflake Notebooks', 'Notebooks in Snowsight mixing SQL and Python', 'Inside Snowflake'],
        ]),
        defbox('The principle is to <strong>move code to the data</strong>, not data to the code: filter and aggregate inside Snowflake and bring only '
               'small results back.'),
        tags('Python connector', 'Snowpark', 'DataFrame', 'UDF', 'UDTF', 'Stored procedure', 'Snowflake Scripting'),
    ),
    analogy('The connector is <strong>phoning in orders</strong> to the kitchen (SQL) and carrying the plates back. Snowpark is <strong>writing your '
            'recipe in your own language</strong> and the kitchen translates and cooks it there. UDFs are new <strong>house recipes</strong> the kitchen '
            'can use in any order.'),
    snowpark_anim(),
    real_world(
        scenario('Placement-readiness score',
                 p('A Python data scientist computes a readiness score from marks, attendance and mock-interview ratings. With Snowpark the joins and '
                   'aggregations run in the warehouse; the scoring function is registered as a Python UDF and analysts call '
                   '<code>SELECT readiness(roll_no) …</code> from SQL dashboards.')),
    ),
    example(
        pyrun('''
import snowflake.connector

conn = snowflake.connector.connect(
    account="cdac-mumbai", user="vineeta", password="********",   # use key-pair auth or SSO in real code
    warehouse="lab_wh", database="CDAC", schema="BDA",
)
cur = conn.cursor()
cur.execute("CREATE OR REPLACE TABLE mock_interviews (roll_no INT, panel VARCHAR, rating INT)")

rows = [(2401, "A", 7), (2401, "B", 8), (2402, "A", 9), (2405, "B", 10)]
cur.executemany("INSERT INTO mock_interviews VALUES (%s, %s, %s)", rows)   # bound parameters, no string building
print("rows in table:", cur.execute("SELECT COUNT(*) FROM mock_interviews").fetchone()[0])

cur.execute("""
    SELECT roll_no, COUNT(*) AS panels, AVG(rating)::NUMBER(4,2) AS avg_rating
    FROM mock_interviews
    WHERE rating >= %s
    GROUP BY roll_no ORDER BY roll_no
""", (8,))
print([d.name for d in cur.description])
for row in cur.fetchall():
    print(row)
conn.close()
'''),
        p('This ran against the emulator through the real connector API, so the output is genuine. Values come back as Python types '
          '(<code>Decimal</code> for NUMBER). The same code works against a real account once the credentials are real.', top=True),
        sq('''
-- SQL UDF
CREATE OR REPLACE FUNCTION grade(m NUMBER) RETURNS VARCHAR AS
$$ CASE WHEN m >= 80 THEN 'Distinction' WHEN m >= 40 THEN 'Pass' ELSE 'Fail' END $$;

-- Python UDF
CREATE OR REPLACE FUNCTION readiness(marks FLOAT, attendance FLOAT, rating FLOAT)
RETURNS FLOAT LANGUAGE PYTHON RUNTIME_VERSION = '3.11' HANDLER = 'score'
AS $$
def score(marks, attendance, rating):
    return round(0.5 * marks + 0.3 * attendance + 2.0 * rating, 1)
$$;

SELECT name, grade(marks) AS grade FROM students;

-- Snowflake Scripting stored procedure
CREATE OR REPLACE PROCEDURE archive_batch(batch VARCHAR)
RETURNS VARCHAR LANGUAGE SQL AS
$$
DECLARE n INTEGER;
BEGIN
  INSERT INTO results_archive SELECT * FROM results_clean WHERE batch_id = :batch;
  n := SQLROWCOUNT;
  DELETE FROM results_clean WHERE batch_id = :batch;
  RETURN 'archived ' || n || ' rows';
END;
$$;
CALL archive_batch('2026-FEB');
'''),
        py('''
# Snowpark: the same aggregation as a lazy DataFrame (runs in the warehouse on .show()/.collect())
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, avg

session = Session.builder.configs({"account": "cdac-mumbai", "user": "vineeta", "authenticator": "externalbrowser",
                                   "warehouse": "lab_wh", "database": "CDAC", "schema": "BDA"}).create()
df = (session.table("mock_interviews")
             .filter(col("rating") >= 8)
             .group_by("roll_no")
             .agg(avg("rating").alias("avg_rating")))
df.show()
''', 'Snowpark (shown, not executed)'),
        title='Example'),
    steps(
        ('Install', '<code>pip install snowflake-connector-python</code> (and <code>snowflake-snowpark-python</code> for Snowpark).'),
        ('Authenticate safely', 'Key-pair authentication or SSO; never hard-code passwords in notebooks.'),
        ('Push work down', 'Filter and aggregate in SQL/Snowpark; fetch only results.'),
        ('Package reusable logic', 'As UDFs or stored procedures so SQL users can call it.'),
        title='Steps'),
    crossq(
        ('Why use bound parameters instead of f-strings?', 'They prevent SQL injection and quoting errors, and let Snowflake reuse the statement.'),
        ('UDF vs stored procedure?', 'A UDF returns a value (or table) and is called inside a query, row by row. A stored procedure is called with CALL, '
         'can run many statements, DDL and loops, and returns a single value or table.'),
        ('How do you load a pandas DataFrame quickly?', '<code>write_pandas(conn, df, "TABLE_NAME")</code> from <code>snowflake.connector.pandas_tools</code>: '
         'it writes Parquet files to a stage and runs COPY, far faster than row-by-row INSERTs.'),
    ),
]),
])
