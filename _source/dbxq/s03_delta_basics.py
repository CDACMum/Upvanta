from build import *
from dbxq.anims import *
from dbxq.runner import sql, sq, pyrun, py

UPDATES = """
CREATE TABLE marks_updates AS SELECT * FROM VALUES
  (2402, 'Aarshvi', 'PGCP-BDA', 'Juhu',     90.00, DATE'2026-02-02'),
  (2404, 'Kabir',   'PGCP-AC',  'Kharghar', 70.00, DATE'2026-02-03'),
  (2409, 'Zoya',    'PGCP-AI',  'Kharghar', 81.00, DATE'2026-02-06')
  AS u(roll_no, name, course, centre, marks, joined);
"""

SECTION = dict(level='intermediate', title='Delta Lake Fundamentals', questions=[

# ------------------------------------------------------------------ 11
Q('What is Delta Lake? How does the transaction log provide ACID transactions?', 'Delta Lake & the Log', minutes=10, cards=[
    definition(
        defbox('<strong>Delta Lake</strong> is an open-source <strong>table format</strong> (a Linux Foundation project) and the default for '
               'every table on Databricks. A Delta table is a directory of <strong>Parquet</strong> data files plus a '
               '<code>_delta_log</code> directory: the <strong>transaction log</strong>.',
               'Each commit is an ordered JSON file (<code>00000000000000000000.json</code>, <code>…001.json</code>, …) containing '
               '<strong>actions</strong>: <code>add</code> and <code>remove</code> for data files (with per-file statistics), '
               '<code>metaData</code> (schema, partitioning, properties), <code>protocol</code> (required reader/writer features) and '
               '<code>commitInfo</code> (operation, parameters, metrics). Every 10 commits or so a <strong>checkpoint</strong> Parquet file '
               'summarises the state.'),
        table(['ACID property', 'How Delta provides it'], [
            ['Atomicity', 'A commit is one new log file: it is written completely or not at all'],
            ['Consistency', 'Schema enforcement and constraints are checked before the commit'],
            ['Isolation', 'Optimistic concurrency: writers check for conflicts with commits made since they started; '
                          'readers always see a complete snapshot (WriteSerializable by default)'],
            ['Durability', 'Data and log live in durable cloud storage'],
        ]),
        tags('Delta Lake', 'Transaction log', '_delta_log', 'add / remove', 'Checkpoint', 'Optimistic concurrency', 'ACID'),
    ),
    analogy('The transaction log is a <strong>bank passbook</strong>. Money (data files) is never altered; every deposit or withdrawal is a new '
            'line. To know the balance at any date you read the passbook up to that line, and two clerks cannot write the same line number.'),
    delta_log_anim(),
    real_world(
        scenario('A failed nightly job',
                 p('A Spark job writing the day\'s attendance crashes halfway after writing 140 of 300 Parquet files. With plain Parquet, '
                   'dashboards would read the half-written folder. With Delta, the commit JSON was never written, so readers keep seeing the '
                   'previous complete version; the orphaned files are invisible and are cleaned up later by VACUUM.')),
    ),
    example(
        pyrun('''
import json

spark.sql("UPDATE students SET marks = marks + 1 WHERE roll_no = 2408")

log = spark.sql("DESCRIBE DETAIL students").first()["location"] + "/_delta_log/"
for f in dbutils.fs.ls(log):
    print(f.name, f.size)

print("--- actions in commit 2 (the UPDATE) ---")
for line in dbutils.fs.head(log + "00000000000000000002.json").splitlines():
    action, body = next(iter(json.loads(line).items()))
    if action == "commitInfo":
        print(action, body["operation"], body["operationParameters"])
    else:
        print(action, body["path"], {k: body[k] for k in ("dataChange", "size")})
'''),
        p('Commit 0 created the table, commit 1 was the INSERT of 8 rows and commit 2 is the UPDATE: it removed the old file and added a new '
          'one containing all 8 rows with the changed value (copy-on-write). With <strong>deletion vectors</strong> enabled, Databricks can '
          'instead mark the changed rows as deleted in a small side file and write only the new rows, which makes small updates much '
          'cheaper.', top=True),
        sql('DESCRIBE HISTORY students;', setup='UPDATE students SET marks = marks + 1 WHERE roll_no = 2408;'),
        title='Example: Looking Inside the Log'),
    steps(
        ('Write', 'The writer creates new Parquet files.'),
        ('Check', 'It validates schema and constraints, and checks for conflicting commits.'),
        ('Commit', 'It atomically creates the next numbered JSON file listing add/remove actions.'),
        ('Read', 'Readers load the latest checkpoint and later JSON files to get the snapshot.'),
        title='How a Commit Works'),
    crossq(
        ('What happens when two jobs write to the same table at once?', 'Both write their files, then try to commit the same next version. One '
         'wins; the other checks whether the winner touched data it read. If not (e.g. two blind appends) it retries with the next number; if '
         'yes it fails with a <code>ConcurrentModificationException</code> such as <code>ConcurrentAppendException</code>.'),
        ('Why are there statistics in the add actions?', 'Each <code>add</code> stores the row count and min/max/null counts for the first 32 '
         'columns. Readers use them for <strong>data skipping</strong>: files whose ranges cannot match a filter are not read at all.'),
        ('Is Delta Lake only for Databricks?', 'No. It is open source (delta.io) and works with Apache Spark, and there are readers/writers for '
         'Flink, Trino, Rust (delta-rs), Python (Polars, DuckDB) and more. This page\'s outputs were produced locally with delta-rs and Spark.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How do you create Delta tables? Explain managed vs external tables, CTAS and DESCRIBE.', 'Creating Tables', minutes=8, cards=[
    definition(
        defbox('On Databricks every table is a Delta table unless you say otherwise (<code>USING DELTA</code> is the default). Ways to create '
               'one: <code>CREATE TABLE … (columns)</code>, <strong>CTAS</strong> <code>CREATE TABLE … AS SELECT</code>, <code>CREATE OR REPLACE '
               'TABLE</code> (atomic replace that keeps history), <code>df.write.saveAsTable()</code>, or the UI (upload a file).',
               'A <strong>managed table</strong>\'s files live in storage managed by Unity Catalog; dropping the table deletes them. An '
               '<strong>external table</strong> has a <code>LOCATION</code> under an external location you control; dropping it keeps the files. '
               'Use <code>DESCRIBE TABLE</code> (columns), <code>DESCRIBE EXTENDED</code> (plus table information), <code>DESCRIBE DETAIL</code> '
               '(Delta details: files, size, properties) and <code>SHOW CREATE TABLE</code>.'),
        tags('CREATE TABLE', 'CTAS', 'CREATE OR REPLACE', 'Managed table', 'External table', 'DESCRIBE DETAIL', 'Three-level namespace'),
    ),
    analogy('A managed table is a <strong>hostel room</strong>: the institute owns it and clears it when you leave. An external table is '
            '<strong>your own flat</strong> that you merely registered with the institute; leaving the register does not empty the flat.'),
    managed_external_anim(),
    real_world(
        scenario('Choosing managed or external',
                 ul('New tables built by Databricks pipelines: <strong>managed</strong> (they get predictive optimisation and simpler governance).',
                    'Files that another system (an on-premises loader, a partner) also writes to the same path: <strong>external</strong>.',
                    'Never create two external tables on the same path; let one table own each location.')),
    ),
    example(
        sql('''
CREATE TABLE bda_toppers
COMMENT 'PGCP-BDA students with 75+ marks'
AS SELECT roll_no, name, centre, marks
   FROM   students
   WHERE  course = 'PGCP-BDA' AND marks >= 75;

SELECT * FROM bda_toppers ORDER BY marks DESC;
DESCRIBE EXTENDED bda_toppers;
DESCRIBE DETAIL bda_toppers;
''', show='dml'),
        sq('''
-- external table: needs an external location you are allowed to use
CREATE TABLE cdac.bda.legacy_attendance (roll_no INT, att_date DATE, present BOOLEAN)
LOCATION 's3://cdac-legacy/attendance/';

DROP TABLE cdac.bda.legacy_attendance;   -- metadata removed, files remain
DROP TABLE cdac.bda.bda_toppers;         -- managed: data removed
UNDROP TABLE cdac.bda.bda_toppers;       -- managed tables can be recovered for 7 days
'''),
        p('<code>DESCRIBE DETAIL</code> reports one data file, its size in bytes and the protocol versions required to read and write the table. '
          'On Databricks the location of a managed table looks like <code>s3://…/__unitystorage/catalogs/&lt;id&gt;/tables/&lt;id&gt;</code>; '
          'here it is shown as a readable path.', top=True),
        title='Example'),
    steps(
        ('Pick catalog and schema', '<code>USE CATALOG cdac; USE SCHEMA bda;</code> or always use full names.'),
        ('Create', 'With explicit columns for contracts, or CTAS for derived tables.'),
        ('Document', 'Add COMMENT on the table and columns, and tags.'),
        ('Inspect', 'DESCRIBE DETAIL / HISTORY to confirm files, properties and versions.'),
        title='Steps'),
    crossq(
        ('What is the difference between CREATE OR REPLACE and DROP + CREATE?', '<code>CREATE OR REPLACE</code> is one atomic commit: readers '
         'never see a missing table, permissions stay, and the old versions remain in history for time travel. DROP + CREATE leaves a gap and '
         'loses history and grants.'),
        ('Can you convert a Parquet folder to Delta without copying data?', 'Yes: <code>CONVERT TO DELTA parquet.`s3://path`</code> writes a '
         'transaction log that references the existing files.'),
        ('What is a volume, and how is it different from a table?', 'A volume is a Unity Catalog object that governs a folder of '
         '<em>non-tabular</em> files (CSV drops, images, PDFs). A table is structured data with a schema. Raw files land in volumes; pipelines '
         'turn them into tables.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What is schema enforcement and schema evolution in Delta Lake?', 'Schema Enforcement & Evolution', minutes=9, cards=[
    definition(
        defbox('<strong>Schema enforcement</strong> (schema validation) rejects writes whose schema is not compatible with the table: unknown '
               'columns, or types that cannot be safely cast. The write fails as a whole and nothing is committed.',
               '<strong>Schema evolution</strong> changes the table schema deliberately: '
               '<code>.option("mergeSchema", "true")</code> on a DataFrame write, <code>MERGE WITH SCHEMA EVOLUTION</code>, the session setting '
               '<code>spark.databricks.delta.schema.autoMerge.enabled</code>, or DDL such as <code>ALTER TABLE … ADD COLUMNS</code>. To replace the '
               'schema completely (rename or drop columns, change types) overwrite with <code>.option("overwriteSchema", "true")</code>, or use '
               'column mapping for renames and drops without rewriting.'),
        table(['Change', 'How'], [
            ['Add a column', 'mergeSchema, or ALTER TABLE … ADD COLUMNS'],
            ['Widen a type (INT → BIGINT, …)', 'Type widening table feature, or overwriteSchema'],
            ['Rename / drop a column', "ALTER TABLE … RENAME/DROP COLUMN (needs column mapping 'name')"],
            ['Completely new schema', 'Overwrite with overwriteSchema = true'],
        ]),
        tags('Schema enforcement', 'Schema evolution', 'mergeSchema', 'overwriteSchema', 'autoMerge', 'ADD COLUMNS', 'Column mapping'),
    ),
    analogy('Enforcement is the <strong>exam form</strong> that only accepts the fields printed on it. Evolution is the exam cell officially '
            '<strong>printing a new version</strong> of the form with an extra field, after which old forms simply show that field blank.'),
    schema_evolution_anim(),
    real_world(
        scenario('A new column from a centre',
                 p('The Juhu centre starts sending a <code>grade</code> column in the marks file. With enforcement, the pipeline fails loudly the '
                   'first night, which is good: the team checks the column, agrees it is valid, and enables <code>mergeSchema</code> for that '
                   'load. Without enforcement, a typo such as <code>marsk</code> would have silently created a second marks column.')),
    ),
    example(
        pyrun('''
new = spark.createDataFrame(
    [(2410, "Ishan", "PGCP-AI", "Juhu", 80.0, None, "A")],
    "roll_no int, name string, course string, centre string, marks double, joined date, grade string")

try:
    new.write.mode("append").saveAsTable("students")             # enforcement
except Exception as e:
    print(type(e).__name__, ":", str(e).split("Table schema")[0].strip())

new.write.mode("append").option("mergeSchema", "true").saveAsTable("students")   # evolution
spark.table("students").filter("roll_no >= 2407").orderBy("roll_no").show()
'''),
        sql('''
ALTER TABLE students ADD COLUMNS (email STRING COMMENT 'official e-mail');
INSERT INTO students (roll_no, name, course, email) VALUES (2411, 'Neha', 'PGCP-AC', 'neha@cdac.in');
SELECT roll_no, name, marks, email FROM students WHERE roll_no >= 2407 ORDER BY roll_no;
INSERT INTO students VALUES (2412, 'Rohan', 'PGCP-AI', 'Juhu', 70.0, DATE'2026-02-07', 'x', 'y');
''', show='dml', expect_error=True),
        p('The rejected append committed nothing. With <code>mergeSchema</code> the <code>grade</code> column was added and the existing rows '
          'show NULL for it. In SQL, an INSERT with a column list fills the other columns with NULL, while an INSERT with too many values is '
          'rejected by the analyzer.', top=True),
        title='Example'),
    steps(
        ('Keep enforcement on', 'Let unexpected columns fail the job so someone looks at them.'),
        ('Evolve on purpose', 'Use mergeSchema for that write, or ALTER TABLE for planned changes.'),
        ('Rename safely', 'Enable column mapping before renaming or dropping columns.'),
        ('Tell consumers', 'Schema changes can break downstream jobs and dashboards; announce them.'),
        title='Steps'),
    crossq(
        ('Does mergeSchema allow changing a column from STRING to INT?', 'No. mergeSchema adds new columns (and nested fields) and allows some '
         'safe upcasts with type widening; incompatible type changes need an overwrite with <code>overwriteSchema</code>.'),
        ('What does Auto Loader do with new columns?', 'By default (<code>addNewColumns</code>) the stream stops with an error when a new column '
         'appears, records the new schema, and continues with it after a restart; other modes rescue the data or ignore it.'),
        ('Is schema enforcement the same as a CHECK constraint?', 'No. Enforcement checks column names and types; constraints check the '
         '<em>values</em> (NOT NULL, CHECK expressions).'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do UPDATE, DELETE and MERGE work in Delta Lake? Write an upsert.', 'UPDATE, DELETE & MERGE', minutes=10, cards=[
    definition(
        defbox('Delta supports full DML. <code>UPDATE</code> and <code>DELETE</code> find the files that contain matching rows and rewrite them '
               '(or, with <strong>deletion vectors</strong>, mark the rows as deleted without rewriting the file). <code>MERGE INTO</code> '
               'combines a <strong>source</strong> with the <strong>target</strong> on a join condition and applies clauses:'),
        table(['Clause', 'Action'], [
            ['<code>WHEN MATCHED [AND cond] THEN UPDATE SET …</code> / <code>UPDATE SET *</code>', 'Change matched target rows'],
            ['<code>WHEN MATCHED [AND cond] THEN DELETE</code>', 'Remove matched target rows'],
            ['<code>WHEN NOT MATCHED [AND cond] THEN INSERT …</code> / <code>INSERT *</code>', 'Add source rows that have no match'],
            ['<code>WHEN NOT MATCHED BY SOURCE [AND cond] THEN DELETE / UPDATE</code>', 'Handle target rows missing from the source'],
        ]),
        p('Each statement is one atomic commit. If several source rows match the same target row, MERGE fails, because the result would be '
          'ambiguous.'),
        tags('UPDATE', 'DELETE', 'MERGE INTO', 'Upsert', 'WHEN NOT MATCHED BY SOURCE', 'Deletion vectors', 'Copy-on-write'),
    ),
    analogy('MERGE is <strong>updating the class register from a correction list</strong>: names on both lists get their marks corrected, new '
            'names are added, and students no longer in the official list are struck off, all in one signed entry.'),
    merge_anim(),
    real_world(
        scenario('Daily corrections from the exam cell',
                 p('Every evening the exam cell uploads re-evaluation results: some marks change, late registrations add new roll numbers, and '
                   'cancelled admissions must be removed. One MERGE applies all three, and the dashboard never shows a half-updated table.')),
    ),
    example(
        sql('''
SELECT * FROM marks_updates ORDER BY roll_no;

MERGE INTO students AS t
USING marks_updates AS s
ON t.roll_no = s.roll_no
WHEN MATCHED AND s.marks <> t.marks THEN UPDATE SET t.marks = s.marks
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE AND t.centre = 'Juhu' AND t.marks < 60 THEN DELETE;

SELECT * FROM students ORDER BY roll_no;
''', setup=UPDATES),
        sql('''
INSERT INTO marks_updates VALUES (2402, 'Aarshvi', 'PGCP-BDA', 'Juhu', 91.00, DATE'2026-02-02');

MERGE INTO students AS t
USING marks_updates AS s
ON t.roll_no = s.roll_no
WHEN MATCHED THEN UPDATE SET *;
''', setup=UPDATES, show='all', expect_error=True, title='Databricks SQL: duplicate keys in the source'),
        p('In the first MERGE, 2402 and 2404 were updated, 2409 inserted and 2408 (Juhu, 59.25) deleted by the NOT MATCHED BY SOURCE clause. '
          'The second source has two rows for 2402, so the MERGE is rejected; de-duplicate the source first, for example with '
          '<code>QUALIFY ROW_NUMBER() OVER (PARTITION BY roll_no ORDER BY updated_at DESC) = 1</code>.', top=True),
        title='Example'),
    steps(
        ('Prepare the source', 'One row per key; de-duplicate with ROW_NUMBER or QUALIFY.'),
        ('Match on the key', 'Include partition or clustering columns in ON when possible, so fewer files are scanned.'),
        ('Add conditions', 'Update only when values differ, to avoid rewriting unchanged rows.'),
        ('Check the metrics', 'num_updated_rows / num_inserted_rows / num_deleted_rows and DESCRIBE HISTORY.'),
        title='Steps'),
    crossq(
        ('Why can a small MERGE be slow on a big table?', 'Without deletion vectors, every file containing at least one matched row is rewritten '
         'completely. A narrow ON condition, liquid clustering on the key and deletion vectors reduce the files touched.'),
        ('What does UPDATE SET * do?', 'It sets every target column to the source column with the same name. INSERT * does the same for inserts. '
         'The source must have all target columns (or schema evolution must be enabled for extra ones).'),
        ('How is MERGE used for SCD Type 2?', 'Matched current rows whose attributes changed are closed (<code>is_current = false, end_date = '
         '…</code>) and the new version is inserted, usually by unioning the changed rows into the source with a NULL merge key so they fall '
         'into WHEN NOT MATCHED. Question 39 shows a full example.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('What constraints does Delta Lake support? Explain NOT NULL, CHECK, generated and identity columns.', 'Constraints & Special Columns', minutes=8, cards=[
    definition(
        table(['Feature', 'Syntax', 'Enforced?'], [
            ['NOT NULL', '<code>roll_no INT NOT NULL</code>', 'Yes, on every write'],
            ['CHECK', '<code>ALTER TABLE t ADD CONSTRAINT c CHECK (expr)</code>', 'Yes; adding it validates existing rows first'],
            ['Generated column', '<code>exam_year INT GENERATED ALWAYS AS (year(exam_date))</code>', 'Value computed by Delta; supplied values must match'],
            ['Identity column', '<code>id BIGINT GENERATED ALWAYS AS IDENTITY</code>', 'Unique increasing values (not necessarily consecutive)'],
            ['PRIMARY KEY / FOREIGN KEY', '<code>CONSTRAINT pk PRIMARY KEY (roll_no)</code>', 'No: informational only (Unity Catalog)'],
            ['Default value', '<code>status STRING DEFAULT \'active\'</code>', 'Applied when a column is omitted (table feature)'],
        ]),
        defbox('A violated constraint fails the <strong>whole</strong> transaction. CHECK constraints are stored as table properties '
               '(<code>delta.constraints.&lt;name&gt;</code>) and listed by <code>SHOW TBLPROPERTIES</code>.'),
        tags('NOT NULL', 'CHECK', 'Generated column', 'Identity column', 'Informational PK/FK', 'DEFAULT'),
    ),
    analogy('Constraints are the <strong>validation rules on an online admission form</strong>: roll number cannot be blank, marks must be '
            'between 0 and 100. One invalid row and the whole form is sent back, not half of it saved.'),
    constraints_anim(),
    real_world(
        scenario('Catching an upstream bug',
                 p('A grading script starts writing marks out of 200 instead of 100. The <code>valid_marks</code> CHECK constraint on the silver '
                   'table stops the load with the exact row and value in the error message, before any dashboard shows a 150% score.')),
    ),
    example(
        sql('''
CREATE TABLE exam_marks (
  roll_no   INT    NOT NULL,
  subject   STRING NOT NULL,
  marks     INT,
  CONSTRAINT valid_marks CHECK (marks BETWEEN 0 AND 100)
);

INSERT INTO exam_marks VALUES (2401, 'SQL', 72), (2402, 'SQL', 85);
INSERT INTO exam_marks VALUES (2403, 'SQL', 105);
INSERT INTO exam_marks VALUES (NULL, 'SQL', 50);
UPDATE exam_marks SET marks = marks * 2;

ALTER TABLE students ADD CONSTRAINT pass_marks CHECK (marks >= 60);
SHOW TBLPROPERTIES exam_marks;
SELECT * FROM exam_marks ORDER BY roll_no;
''', show='dml', expect_error=True),
        sq('''
CREATE TABLE exam_attempts (
  attempt_id  BIGINT GENERATED ALWAYS AS IDENTITY,
  roll_no     INT NOT NULL,
  exam_ts     TIMESTAMP,
  exam_date   DATE GENERATED ALWAYS AS (CAST(exam_ts AS DATE)),
  CONSTRAINT pk_attempt PRIMARY KEY (attempt_id)      -- informational
);
'''),
        p('Each rejected statement left the table unchanged: the final SELECT still shows the two valid rows. Adding <code>pass_marks</code> to '
          '<code>students</code> failed because one existing row (Tejas, 59.25) already violates it.', top=True),
        title='Example'),
    steps(
        ('Declare NOT NULL', 'For keys and required columns, at creation.'),
        ('Add CHECK constraints', 'For value ranges and allowed codes; fix existing bad rows first.'),
        ('Use generated columns', 'For derived partition or filter columns (date from timestamp).'),
        ('Prefer pipeline expectations for soft rules', 'When bad rows should be dropped or counted, not fail the load.'),
        title='Steps'),
    crossq(
        ('Constraint or Lakeflow expectation?', 'A constraint is a hard rule on the table: any violation fails the write. An expectation in a '
         'declarative pipeline can warn, drop the bad rows, or fail, and it records data-quality metrics.'),
        ('Are identity values gap-free?', 'No. Identity columns guarantee unique, increasing values, but parallel writes reserve ranges, so gaps are '
         'normal. Do not use them as consecutive serial numbers.'),
        ('Why declare a primary key that is not enforced?', 'It documents the model for tools and people, and the optimiser can use '
         '<code>RELY</code> constraints to simplify queries (for example, remove an unnecessary DISTINCT or join).'),
    ),
]),

])
