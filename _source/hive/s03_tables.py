from build import *
from hive.anims import *
from hive.runner import hql, hq, sh, datafile

STUD = '2401,Anuj,PG-DBDA,78\n2402,Vineeta,PG-DBDA,91\n2403,Aarshvi,PG-DAC,84\n'

SECTION = dict(level='basic', title='Tables, SerDes & Schema-on-Read', questions=[

# ------------------------------------------------------------------ 10
Q('What is the difference between managed (internal) and external tables?', 'Managed vs External Tables', minutes=9, cards=[
    definition(
        defbox('A <strong>managed (internal) table</strong> is fully owned by Hive: its data lives in the warehouse directory and '
               '<code>DROP TABLE</code> deletes <strong>both metadata and data</strong>.',
               'An <strong>external table</strong> (<code>CREATE EXTERNAL TABLE ... LOCATION \'...\'</code>) only registers metadata over files '
               'that someone else owns. <code>DROP TABLE</code> removes <strong>only the metadata</strong>; the files stay.'),
        tags('Managed Table', 'Internal Table', 'External Table', 'LOCATION', 'DROP TABLE', 'external.table.purge'),
    ),
    analogy('A managed table is a <strong>book you bought</strong>: when you throw it away, it is gone. An external table is a '
            '<strong>library card for a book in the public library</strong>: tearing up your card (DROP TABLE) does not destroy the book, and '
            'other people can still read it.'),
    managed_external(),
    comparison(
        table(['Aspect', 'Managed', 'External'], [
            ['Who owns the files', 'Hive', 'You / another tool'],
            ['Default location', 'Warehouse dir (<code>/user/hive/warehouse/db.db/t</code>)', 'Wherever <code>LOCATION</code> points'],
            ['DROP TABLE', 'Deletes metadata + data', 'Deletes metadata only'],
            ['TRUNCATE TABLE', 'Allowed', 'Not allowed'],
            ['ACID (UPDATE/DELETE)', 'Possible (Hive 3: managed ORC tables are transactional by default)', 'Not possible'],
            ['Typical use', 'Curated, Hive-controlled tables', 'Raw/landing data, data shared with Spark or other tools'],
        ]),
    ),
    real_world(
        scenario('Raw layer as external, curated layer as managed',
                 p('Log files written by Flume/Spark into <code>/data/raw/weblogs/</code> are exposed through an <strong>external</strong> table, '
                   'so an accidental <code>DROP TABLE</code> cannot delete the only copy of the logs. Cleaned, aggregated tables built by Hive '
                   'are <strong>managed</strong>, since Hive created them and can rebuild them.')),
    ),
    example(
        hql('''
CREATE TABLE students_m (roll_no INT, name STRING, course STRING, marks INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',';

CREATE EXTERNAL TABLE students_x (roll_no INT, name STRING, course STRING, marks INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION '/data/raw/students';

INSERT INTO students_m SELECT * FROM students_x;

DESCRIBE FORMATTED students_x;
''', files={'raw/students/part1.csv': STUD}),
        hql('''
DROP TABLE students_m;
DROP TABLE students_x;
SHOW TABLES;
dfs -ls -R /user/hive/warehouse/cdac.db;
dfs -ls -R /data/raw/students;
''', setup='''
CREATE TABLE students_m (roll_no INT, name STRING, course STRING, marks INT) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',';
CREATE EXTERNAL TABLE students_x (roll_no INT, name STRING, course STRING, marks INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LOCATION '/data/raw/students';
INSERT INTO students_m SELECT * FROM students_x;
''', files={'raw/students/part1.csv': STUD}),
        note('After both DROPs the managed table\'s folder is gone, but the external table\'s file is still in <code>/data/raw/students</code>. '
             'Re-running the <code>CREATE EXTERNAL TABLE</code> brings the table back instantly.', 'Result'),
        title='Example: Same Data, Different DROP Behaviour'),
    steps(
        ('Decide ownership', 'Will anything other than Hive write or need these files? If yes → external.'),
        ('Put the files in place', '<code>hdfs dfs -mkdir -p /data/raw/students; hdfs dfs -put *.csv /data/raw/students/</code>'),
        ('Create the external table', '<code>CREATE EXTERNAL TABLE ... ROW FORMAT ... LOCATION \'/data/raw/students\';</code> (point to the <strong>folder</strong>, not a file).'),
        ('Verify', '<code>DESCRIBE FORMATTED</code> shows <code>Table Type: EXTERNAL_TABLE</code>; run a <code>SELECT ... LIMIT 10</code>.'),
        ('Convert later if needed', '<code>ALTER TABLE t SET TBLPROPERTIES (\'EXTERNAL\'=\'TRUE\')</code> (or FALSE) switches the type.'),
        title='Steps to Create an External Table'),
    crossq(
        ('How do you tell whether a table is managed or external?', '<code>DESCRIBE FORMATTED t</code> → <code>Table Type: MANAGED_TABLE</code> or <code>EXTERNAL_TABLE</code>.'),
        ('Can an external table be in the warehouse directory?', 'Yes. LOCATION can be anywhere, including under the warehouse. What matters is the EXTERNAL flag, not the path.'),
        ('What does <code>external.table.purge</code> do?', 'Setting <code>TBLPROPERTIES (\'external.table.purge\'=\'true\')</code> makes DROP delete the external table\'s files too. Hive 3 uses it for tables created by some tools.'),
        ('In Hive 3, why does a plain CREATE TABLE sometimes become external?', 'With strict managed tables, non-ORC managed tables are converted: managed tables must be transactional ORC, so other formats are created as external tables with purge enabled.'),
    ),
]),

# ------------------------------------------------------------------ 11
Q('What is a SerDe? Which SerDes and row formats have you used?', 'SerDe & Row Format', minutes=9, cards=[
    definition(
        defbox('A <strong>SerDe</strong> (<strong>Ser</strong>ializer/<strong>De</strong>serializer) tells Hive how to convert between the bytes in a '
               'file and the columns of a row. The <strong>InputFormat/OutputFormat</strong> decide how records are split; the SerDe decides how '
               'each record is parsed into columns (and written back).'),
        table(['SerDe', 'For', 'Declared with'], [
            ['LazySimpleSerDe', 'Delimited text (the default)', '<code>ROW FORMAT DELIMITED FIELDS TERMINATED BY \',\'</code>'],
            ['OpenCSVSerde', 'CSV with quoted fields containing commas (all columns read as STRING)', '<code>ROW FORMAT SERDE \'org.apache.hadoop.hive.serde2.OpenCSVSerde\'</code>'],
            ['JsonSerDe', 'One JSON object per line', '<code>ROW FORMAT SERDE \'org.apache.hive.hcatalog.data.JsonSerDe\'</code>'],
            ['RegexSerDe', 'Logs: each capture group becomes a column', '<code>WITH SERDEPROPERTIES (\'input.regex\'=\'...\')</code>'],
            ['OrcSerde / ParquetHiveSerDe / AvroSerDe', 'Binary columnar/row formats', '<code>STORED AS ORC | PARQUET | AVRO</code>'],
        ]),
        tags('SerDe', 'LazySimpleSerDe', 'OpenCSVSerde', 'JsonSerDe', 'RegexSerDe', 'ROW FORMAT'),
    ),
    analogy('A SerDe is a <strong>translator</strong> standing at the store-room door. Files arrive written in different languages (CSV, JSON, '
            'log lines). For each table you hire the right translator, who reads each line and tells Hive "this is the name, this is the '
            'marks". The InputFormat is the <strong>porter</strong> who carries the pages one by one to the translator.'),
    serde_anim(),
    real_world(
        scenario('Three sources, three SerDes',
                 ul('Student master from the admission portal: CSV with addresses like <code>"Kharghar, Navi Mumbai"</code> → OpenCSVSerde.',
                    'Mobile app events: JSON lines → JsonSerDe, later converted to ORC.',
                    'Apache web server access logs → RegexSerDe extracting IP, time, URL and status.')),
    ),
    example(
        datafile('/data/raw/addresses/a.csv', '2401,"Anuj","Kharghar, Navi Mumbai"\n2402,"Vineeta","Vashi, Navi Mumbai"'),
        hql('''
-- Plain delimited table: the comma INSIDE quotes breaks the columns
CREATE EXTERNAL TABLE addr_simple (roll_no INT, name STRING, address STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION '/data/raw/addresses';

-- OpenCSVSerde understands quotes
CREATE EXTERNAL TABLE addr_csv (roll_no STRING, name STRING, address STRING)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"')
LOCATION '/data/raw/addresses';

SELECT * FROM addr_simple;
SELECT * FROM addr_csv;
''', files={'raw/addresses/a.csv': '2401,"Anuj","Kharghar, Navi Mumbai"\n2402,"Vineeta","Vashi, Navi Mumbai"\n'}),
        title='Example: Quoted CSV Needs the Right SerDe'),
    example(
        datafile('/data/raw/weblogs/access.log',
                 '10.0.0.5 - - [13/Oct/2026:10:15:01 +0530] "GET /course/dbda HTTP/1.1" 200 5120\n'
                 '10.0.0.9 - - [13/Oct/2026:10:15:07 +0530] "GET /admission HTTP/1.1" 404 312'),
        hql(r'''
CREATE EXTERNAL TABLE weblogs (ip STRING, ts STRING, method STRING, url STRING, status STRING, bytes STRING)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES (
  'input.regex' = '(\\S+) \\S+ \\S+ \\[([^\\]]+)\\] "(\\S+) (\\S+) \\S+" (\\d{3}) (\\d+)'
)
LOCATION '/data/raw/weblogs';

SELECT ip, url, status, bytes FROM weblogs;
''', files={'raw/weblogs/access.log': '10.0.0.5 - - [13/Oct/2026:10:15:01 +0530] "GET /course/dbda HTTP/1.1" 200 5120\n'
                                       '10.0.0.9 - - [13/Oct/2026:10:15:07 +0530] "GET /admission HTTP/1.1" 404 312\n'}),
        title='Example: Parsing Web Logs With RegexSerDe'),
    steps(
        ('Inspect a sample of the file', '<code>hdfs dfs -cat /path/file | head</code>: delimiter? quotes? header line? JSON?'),
        ('Pick the SerDe', 'Delimited → default; quoted CSV → OpenCSVSerde; JSON → JsonSerDe; logs → RegexSerDe.'),
        ('Create the table with ROW FORMAT', 'Add <code>SERDEPROPERTIES</code> and <code>TBLPROPERTIES (\'skip.header.line.count\'=\'1\')</code> if there is a header.'),
        ('Check for NULL columns', 'All-NULL columns usually mean a wrong delimiter or regex.'),
        ('Convert to ORC/Parquet', '<code>CREATE TABLE t_orc STORED AS ORC AS SELECT ...</code> so later queries skip the slow text parsing.'),
        title='Steps to Read a New File Format'),
    crossq(
        ('Why does OpenCSVSerde return every column as STRING?', 'It ignores declared types and treats all fields as strings. Cast in a view or when inserting into a typed ORC table.'),
        ('How do you skip a header line?', '<code>TBLPROPERTIES (\'skip.header.line.count\'=\'1\')</code> (and <code>skip.footer.line.count</code> for footers).'),
        ('How do you handle a custom NULL marker such as "NA"?', '<code>TBLPROPERTIES (\'serialization.null.format\'=\'NA\')</code>; by default text tables treat <code>\\N</code> as NULL.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What is schema-on-read? What happens when data does not match the table schema?', 'Schema-on-Read', minutes=7, cards=[
    definition(
        defbox('<strong>Schema-on-read</strong> means the schema is applied <strong>when data is read</strong>, not when it is written. Loading '
               'just places files; the SerDe parses and casts values at query time.',
               'Values that do not fit the declared type become <strong>NULL</strong>, missing trailing fields become NULL, and extra fields are '
               'ignored. Hive does not raise an error.'),
        tags('Schema-on-read', 'Schema-on-write', 'NULL', 'Data Quality', 'Late Binding'),
    ),
    analogy('Schema-on-write is a <strong>school admission office</strong> that refuses incomplete forms at the counter. Schema-on-read is a '
            '<strong>drop box</strong>: every form is accepted, and problems are noticed only when someone later reads the forms. Faster intake, '
            'but you must check quality yourself.'),
    schema_on_read(),
    real_world(
        scenario('A silent data-quality bug',
                 p('A source system started sending marks as <code>"78.5"</code> instead of <code>78</code>. The Hive column was INT, so every '
                   'value became NULL and the average-marks dashboard silently dropped to "no data". The fix was a data-quality check '
                   'that counts NULLs per load and fails the pipeline above a threshold.')),
    ),
    example(
        hql('''
CREATE EXTERNAL TABLE marks_raw (roll_no INT, name STRING, marks INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION '/data/raw/marks';

SELECT * FROM marks_raw;

-- Find the problem rows: read the same files as plain strings
CREATE EXTERNAL TABLE marks_str (roll_no STRING, name STRING, marks STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION '/data/raw/marks';

SELECT s.* FROM marks_str s JOIN marks_raw r ON s.roll_no = CAST(r.roll_no AS STRING)
WHERE r.marks IS NULL;
''', files={'raw/marks/m.csv': '2401,Anuj,78\n2402,Vineeta,91\n2403,Aarshvi,abc\n2404,Rohit\n2405,Meera,88,extra\n'}),
        title='Example: Bad Values Become NULL, Silently'),
    steps(
        ('Land data in a raw external table', 'Ideally with all columns as STRING, so nothing is lost.'),
        ('Validate', 'Count rows where <code>CAST(col AS INT) IS NULL AND col IS NOT NULL</code>, check field counts.'),
        ('Route bad rows', 'Write them to a quarantine table with the reason.'),
        ('Insert good rows into the typed table', 'ORC/Parquet, correct types.'),
        title='Steps for Safe Schema-on-Read Ingestion'),
    crossq(
        ('Advantages of schema-on-read?', 'Very fast ingestion, the raw data is preserved, and the same files can be read with different schemas as needs change.'),
        ('Disadvantages?', 'Errors surface late (at query time, as NULLs), and every query pays the parsing cost for text files.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What are views in Hive? How are they different from tables and materialized views?', 'Views & Materialized Views', minutes=7, cards=[
    definition(
        defbox('A <strong>view</strong> is a saved query with a name. It stores <strong>no data</strong>; each time you query the view, Hive '
               'substitutes its query. A <strong>materialized view</strong> (Hive 3) stores the query\'s result and the optimizer can '
               '<strong>automatically rewrite</strong> matching queries to read it.'),
        tags('View', 'Materialized View', 'Query Rewrite', 'Security', 'Abstraction'),
    ),
    comparison(
        table(['Aspect', 'Table', 'View', 'Materialized view'], [
            ['Stores data', 'Yes', 'No', 'Yes (pre-computed result)'],
            ['Always up to date', '—', 'Yes', 'Only after <code>REBUILD</code> (incremental rebuild for ACID sources)'],
            ['Speed', 'Normal', 'Same as running the query', 'Fast for matching queries'],
            ['Use', 'Data', 'Simplify, hide columns, security', 'Speed up repeated aggregations'],
        ]),
    ),
    analogy('A view is a <strong>saved search</strong> in a shopping app: tapping it runs the search again and shows today\'s results. A '
            'materialized view is a <strong>printed catalogue</strong> of that search: instant to read, but it shows yesterday\'s prices until you reprint it.'),
    view_anim(),
    real_world(
        scenario('Hiding sensitive columns',
                 p('The <code>students</code> table has phone numbers and Aadhaar-like IDs. Faculty get access to a view '
                   '<code>v_student_marks</code> exposing only roll number, name, course and marks; the base table is restricted.')),
    ),
    example(
        hql('''
CREATE TABLE students (roll_no INT, name STRING, phone STRING, course STRING, marks INT) STORED AS ORC;
INSERT INTO students VALUES (2401,'Anuj','98xxxxxx01','PG-DBDA',78), (2402,'Vineeta','98xxxxxx02','PG-DBDA',91),
                            (2403,'Aarshvi','98xxxxxx03','PG-DAC',84);

CREATE VIEW v_student_marks AS
SELECT roll_no, name, course, marks FROM students;

CREATE VIEW v_course_summary AS
SELECT course, COUNT(*) AS n, AVG(marks) AS avg_marks FROM students GROUP BY course;

SELECT * FROM v_course_summary;

-- A view always reflects the latest data
INSERT INTO students VALUES (2404, 'Rohit', '98xxxxxx04', 'PG-DAC', 66);
SELECT * FROM v_course_summary;
'''),
        hq('''
-- Hive 3 materialized view (source tables must be transactional for incremental rebuild)
CREATE MATERIALIZED VIEW mv_course_summary
STORED AS ORC AS
SELECT course, COUNT(*) AS n, SUM(marks) AS total FROM students GROUP BY course;

ALTER MATERIALIZED VIEW mv_course_summary REBUILD;   -- refresh after new data
-- Queries like "SELECT course, SUM(marks) FROM students GROUP BY course"
-- can now be answered from the materialized view automatically.
''', 'Materialized view (Hive 3)'),
        title='Example'),
    steps(
        ('Write and test the SELECT', 'Make sure it returns exactly what consumers need.'),
        ('Create the view', '<code>CREATE VIEW IF NOT EXISTS v_name AS SELECT ...;</code>'),
        ('Grant access to the view only', 'With Ranger/SQL authorization, grant SELECT on the view, not the base table.'),
        ('Change it later', '<code>ALTER VIEW v_name AS SELECT ...;</code> or <code>CREATE OR REPLACE VIEW</code>.'),
        title='Steps to Create a View'),
    crossq(
        ('Can you insert into a view?', 'No. Hive views are read-only.'),
        ('Does a view make a query faster?', 'No, it is the same query. Only a materialized view (or a real table) stores results.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do you modify a table with ALTER TABLE?', 'ALTER TABLE', minutes=7, cards=[
    definition(
        table(['Operation', 'Syntax', 'Changes data files?'], [
            ['Rename table', '<code>ALTER TABLE a RENAME TO b</code>', 'Managed: folder renamed; external: no'],
            ['Add columns (at the end)', '<code>ALTER TABLE t ADD COLUMNS (email STRING)</code>', 'No: old rows read NULL'],
            ['Rename/retype a column', '<code>ALTER TABLE t CHANGE old new TYPE</code>', 'No: metadata only'],
            ['Replace all columns', '<code>ALTER TABLE t REPLACE COLUMNS (...)</code>', 'No (dangerous: positional)'],
            ['Table properties', '<code>ALTER TABLE t SET TBLPROPERTIES (...)</code>', 'No'],
            ['Location', '<code>ALTER TABLE t SET LOCATION \'...\'</code>', 'No: just points elsewhere'],
            ['Partitions', '<code>ADD / DROP / RENAME PARTITION</code>', 'Drop on managed tables deletes the folder'],
        ]),
        tags('ALTER TABLE', 'ADD COLUMNS', 'CHANGE', 'RENAME', 'TBLPROPERTIES', 'Schema Evolution'),
    ),
    analogy('ALTER TABLE changes the <strong>label on the box</strong>, not the contents. Adding a column is like adding a new heading to a '
            'register: old pages simply have that column blank (NULL). Renaming a heading does not rewrite what is written under it.'),
    add_column_anim(),
    real_world(
        scenario('Source adds a new field',
                 p('The admission system starts sending <code>email</code>. <code>ADD COLUMNS (email STRING)</code> makes the new field '
                   'queryable; old partitions return NULL for it. No data is rewritten, so the change is instant even on terabytes.')),
    ),
    example(
        hql('''
CREATE TABLE students (roll_no INT, name STRING) STORED AS ORC;
INSERT INTO students VALUES (2401, 'Anuj');

ALTER TABLE students ADD COLUMNS (email STRING COMMENT 'added Oct 2026');
INSERT INTO students VALUES (2402, 'Vineeta', 'vineeta@cdac.in');
SELECT * FROM students;

ALTER TABLE students RENAME TO learners;
ALTER TABLE learners SET TBLPROPERTIES ('comment' = 'all enrolled learners', 'owner_team' = 'dbda');
SHOW TBLPROPERTIES learners;
SHOW TABLES;
'''),
        title='Example'),
    steps(
        ('Check current definition', '<code>SHOW CREATE TABLE t;</code> / <code>DESCRIBE FORMATTED t;</code>'),
        ('Prefer additive changes', 'Add new columns at the end; avoid changing types incompatibly.'),
        ('Apply', '<code>ALTER TABLE t ADD COLUMNS (...)</code> (for partitioned tables add <code>CASCADE</code> so existing partitions get the column too).'),
        ('Verify old and new data', 'Query an old partition and a new one.'),
        title='Steps for a Safe Schema Change'),
    crossq(
        ('What does <code>CASCADE</code> mean in <code>ADD COLUMNS ... CASCADE</code>?', 'Each partition has its own copy of the schema in the metastore. CASCADE updates the table and all existing partitions; RESTRICT (default) changes only the table, so old partitions do not see the new column.'),
        ('Can you drop a column?', 'Not directly; use <code>REPLACE COLUMNS</code> with the list minus that column (metadata only; for text/positional formats the remaining columns must still line up with the data).'),
    ),
]),
])
