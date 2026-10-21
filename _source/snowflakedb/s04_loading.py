from build import *
from snowflakedb.anims import *
from snowflakedb.runner import sql, sq, sh

# rows as they arrive from a CSV file, landed as text so nothing is rejected
RAW_CSV = '''
CREATE OR REPLACE TABLE stg_results_raw (file_name VARCHAR, line_no INT, roll_no VARCHAR, subject VARCHAR, marks VARCHAR, exam_date VARCHAR);
INSERT INTO stg_results_raw VALUES
  ('results_juhu.csv',     2, '2402', 'SQL',   '88',    '15-02-2026'),
  ('results_juhu.csv',     3, '2406', 'SQL',   'AB',    '15-02-2026'),
  ('results_juhu.csv',     4, '2407', 'SQL',   '84.5',  '31-02-2026'),
  ('results_kharghar.csv', 2, '2401', 'SQL',   '78.5',  '15-02-2026'),
  ('results_kharghar.csv', 3, '24O5', 'SQL',   '93.75', '15-02-2026'),
  ('results_kharghar.csv', 4, '2403', 'SQL',   '91.25', '15-02-2026');
'''

SECTION = dict(level='intermediate', title='Loading & Unloading Data', questions=[

# ------------------------------------------------------------------ 16
Q('What are stages in Snowflake? Explain internal and external stages and file formats.', 'Stages & File Formats', minutes=8, cards=[
    definition(
        table(['Stage', 'Reference', 'Notes'], [
            ['User stage', '<code>@~</code>', 'One per user, private to that user.'],
            ['Table stage', '<code>@%students</code>', 'One per table; only for loading that table.'],
            ['Named internal stage', '<code>@cdac_stage</code>', 'A schema object; shared by roles you grant; encryption managed by Snowflake.'],
            ['Named external stage', '<code>@s3_results</code>', 'Points to an S3 / Azure / GCS location; access through a STORAGE INTEGRATION.'],
        ]),
        defbox('A <strong>file format</strong> object stores parsing options (type CSV, JSON, PARQUET, AVRO, ORC, XML; delimiter, header lines, '
               'NULL markers, date format, compression) so they can be reused by stages, COPY and queries. <code>PUT</code> uploads local files to '
               'an internal stage (compressing them with gzip by default); <code>GET</code> downloads them. Both run from SnowSQL or a driver, '
               'not from a Snowsight worksheet.'),
        tags('Stage', '@~', '@%table', 'External stage', 'Storage integration', 'FILE FORMAT', 'PUT / GET', 'LIST'),
    ),
    analogy('A stage is the <strong>loading bay</strong> of a warehouse: trucks (files) park there, a supervisor checks the paperwork (file format), '
            'and only then are goods moved onto the shelves (tables). An external stage is a loading bay at <em>your</em> premises that '
            'Snowflake has a key to.'),
    stages_anim(),
    real_world(
        scenario('Exam result files from every centre',
                 p('Each centre\'s coordinator uploads <code>results_&lt;centre&gt;.csv</code> into an S3 bucket. A named external stage '
                   '<code>@s3_results</code> with a reusable <code>csv_results</code> file format lets the data team list, preview and load the files '
                   'with SQL. No AWS keys appear in any script, because the stage uses a storage integration tied to an IAM role.')),
    ),
    example(
        sq('''
CREATE OR REPLACE FILE FORMAT csv_results
  TYPE = CSV  SKIP_HEADER = 1  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NA')  DATE_FORMAT = 'DD-MM-YYYY';

-- internal stage + upload (run in SnowSQL)
CREATE STAGE cdac_stage FILE_FORMAT = csv_results;
PUT file:///home/vineeta/results_juhu.csv @cdac_stage/results/;

-- external stage on S3 through a storage integration (created once by ACCOUNTADMIN)
CREATE STORAGE INTEGRATION s3_int
  TYPE = EXTERNAL_STAGE  STORAGE_PROVIDER = 'S3'  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-results'
  STORAGE_ALLOWED_LOCATIONS = ('s3://cdac-exam-results/');

CREATE STAGE s3_results URL = 's3://cdac-exam-results/2026/'
  STORAGE_INTEGRATION = s3_int  FILE_FORMAT = csv_results;

LIST @s3_results;
SELECT $1 AS roll_no, $2 AS subject, $3 AS marks, METADATA$FILENAME
FROM   @s3_results (FILE_FORMAT => 'csv_results') LIMIT 5;   -- preview before loading
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Create a file format', 'Describe the files once: type, delimiter, header, NULL markers, date format.'),
        ('Create the stage', 'Internal for uploads from laptops or apps; external when files already live in cloud storage.'),
        ('Upload or point to files', 'PUT for internal; the producing system writes to the bucket for external.'),
        ('Preview', '<code>LIST</code> and <code>SELECT $1, $2 … FROM @stage</code> to check parsing before loading.'),
        title='Steps'),
    crossq(
        ('Why use a storage integration instead of credentials on the stage?', 'Keys in SQL can leak and must be rotated by hand. A storage '
         'integration uses an IAM role (or Azure service principal / GCS service account) trusted by your cloud account, and administrators control '
         'which bucket paths are allowed.'),
        ('What are METADATA$FILENAME and METADATA$FILE_ROW_NUMBER?', 'Pseudo-columns available when querying or loading from a stage. Storing them in '
         'the target table tells you which file and line every row came from.'),
        ('Can you query staged files without loading them?', 'Yes, with <code>SELECT … FROM @stage</code>, or permanently with an external table '
         'or an Iceberg table over the files.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('How does COPY INTO work? Explain load metadata, ON_ERROR and VALIDATION_MODE.', 'COPY INTO', minutes=9, cards=[
    definition(
        defbox('<code>COPY INTO &lt;table&gt; FROM @stage</code> bulk-loads staged files using a running warehouse, many files in parallel. You can '
               'select files with <code>FILES = (…)</code> or <code>PATTERN = \'regex\'</code>, and apply simple transformations by selecting '
               '<code>$1, $2 …</code> in a sub-query (reorder, cast, add METADATA$FILENAME).',
               '<strong>Load metadata</strong>: Snowflake remembers, per table, which files were loaded (name, size, checksum) for '
               '<strong>64 days</strong>, and skips them on later COPY runs. This makes COPY idempotent.'),
        table(['Option', 'Values / effect'], [
            ['<code>ON_ERROR</code>', '<code>ABORT_STATEMENT</code> (default for COPY), <code>CONTINUE</code>, <code>SKIP_FILE</code> (default for Snowpipe), '
             '<code>SKIP_FILE_n</code> / <code>SKIP_FILE_n%</code>'],
            ['<code>VALIDATION_MODE</code>', '<code>RETURN_ERRORS</code>, <code>RETURN_ALL_ERRORS</code>, <code>RETURN_n_ROWS</code>: check files without loading'],
            ['<code>FORCE</code>', 'TRUE reloads files even if already loaded (creates duplicates)'],
            ['<code>PURGE</code>', 'TRUE deletes files from the stage after a successful load'],
            ['<code>MATCH_BY_COLUMN_NAME</code>', 'Load Parquet/Avro/ORC/CSV-with-header columns into same-named table columns'],
        ]),
        tags('COPY INTO', 'Load metadata', '64 days', 'ON_ERROR', 'VALIDATION_MODE', 'FORCE', 'PATTERN'),
    ),
    analogy('A <strong>gatekeeper with a register</strong>: every delivery is noted by its challan number. If the same challan arrives again, it is '
            'turned away. ON_ERROR is the rule for a box with damaged goods: reject the whole truck, the one box, or accept the rest.'),
    copy_anim(),
    real_world(
        scenario('Safe re-runs',
                 p('The nightly job crashed halfway through 40 result files. Re-running the same COPY statement loads only the files that were not '
                   'loaded, because the first 23 are already in the table\'s load metadata. Nobody has to work out which files to skip.')),
    ),
    example(
        sq('''
-- 1. dry run: show errors without loading
COPY INTO results FROM @s3_results PATTERN = '.*results_.*[.]csv'
  VALIDATION_MODE = RETURN_ERRORS;

-- 2. load with a transformation and the source file name
COPY INTO results (roll_no, subject, marks, exam_date, src_file)
FROM (SELECT $1::INT, $2, $3::NUMBER(5,2), TO_DATE($4, 'DD-MM-YYYY'), METADATA$FILENAME
      FROM @s3_results)
PATTERN = '.*results_.*[.]csv'
ON_ERROR = CONTINUE;

-- 3. what happened? (per file: status, rows loaded, first error)
SELECT file_name, status, row_count, first_error_message
FROM   TABLE(INFORMATION_SCHEMA.COPY_HISTORY(TABLE_NAME => 'RESULTS',
                                             START_TIME => DATEADD(hour, -1, CURRENT_TIMESTAMP())));
'''),
        p('A robust alternative many teams use is to land files as text into a staging table, then validate with <code>TRY_</code> functions in SQL. '
          'This keeps every bad row, with its file and line number, for the coordinator to correct:', top=True),
        sql(RAW_CSV + '''
-- rows that convert cleanly
SELECT TRY_TO_NUMBER(roll_no)                 AS roll_no,
       subject,
       TRY_TO_NUMBER(marks, 5, 2)             AS marks,
       TRY_TO_DATE(exam_date, 'DD-MM-YYYY')   AS exam_date
FROM   stg_results_raw
WHERE  TRY_TO_NUMBER(roll_no) IS NOT NULL
  AND  TRY_TO_NUMBER(marks, 5, 2) IS NOT NULL
  AND  TRY_TO_DATE(exam_date, 'DD-MM-YYYY') IS NOT NULL
ORDER  BY roll_no;

-- rows to send back to the centre
SELECT file_name, line_no, roll_no, marks, exam_date
FROM   stg_results_raw
WHERE  TRY_TO_NUMBER(roll_no) IS NULL
   OR  TRY_TO_NUMBER(marks, 5, 2) IS NULL
   OR  TRY_TO_DATE(exam_date, 'DD-MM-YYYY') IS NULL
ORDER  BY file_name, line_no;
''', data=False, show='queries'),
        p('Three rows are rejected: <code>AB</code> (absent) is not a number, 31 February is not a date, and <code>24O5</code> contains the letter O '
          'instead of zero. <code>TRY_TO_*</code> returns NULL instead of failing.', top=True),
        title='Example'),
    steps(
        ('Validate first', 'VALIDATION_MODE = RETURN_ERRORS on a new file source.'),
        ('Choose the error policy', 'ABORT_STATEMENT for critical data; CONTINUE or SKIP_FILE plus an error report for bulk feeds.'),
        ('Record lineage', 'Load METADATA$FILENAME and a load timestamp into each row.'),
        ('Check COPY_HISTORY', 'Status, rows loaded and first error per file.'),
        ('Never use FORCE casually', 'It bypasses load metadata and duplicates data.'),
        title='Steps'),
    crossq(
        ('What happens if a file is loaded, then modified and re-uploaded with the same name?', 'Its checksum changes, so COPY treats it as a new file '
         'and loads it again, which can duplicate rows. Use new file names for corrections, or dedupe with MERGE.'),
        ('What if load metadata has expired (file older than 64 days)?', 'COPY cannot tell whether it was loaded. By default it skips files whose load '
         'status is uncertain; <code>LOAD_UNCERTAIN_FILES = TRUE</code> loads them.'),
        ('COPY INTO vs INSERT … SELECT?', 'COPY reads files from a stage in parallel with load metadata and error handling. INSERT … SELECT moves data '
         'between tables already in Snowflake.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What is Snowpipe? How is it different from COPY INTO and from Snowpipe Streaming?', 'Snowpipe', minutes=8, cards=[
    definition(
        defbox('<strong>Snowpipe</strong> loads files <strong>continuously</strong>, soon after they arrive in a stage. A <strong>pipe</strong> object '
               'wraps one COPY INTO statement. With <code>AUTO_INGEST = TRUE</code> it is triggered by cloud event notifications (S3 via SQS, '
               'Azure Event Grid, Google Pub/Sub); otherwise applications call the Snowpipe REST API. It runs on <strong>serverless compute</strong>, '
               'not on your warehouses, and keeps its own load history for 14 days.',
               '<strong>Snowpipe Streaming</strong> skips files altogether: applications (or the Kafka connector) write rows through an SDK/API '
               'directly into tables, with lower latency and no staging files.'),
        table(['', 'COPY INTO', 'Snowpipe', 'Snowpipe Streaming'], [
            ['Trigger', 'You / a scheduler', 'File-arrival event or REST call', 'Client sends rows'],
            ['Compute', 'Your warehouse', 'Serverless', 'Serverless'],
            ['Unit', 'Batches of files', 'Individual files as they land', 'Rows'],
            ['Latency', 'Schedule-dependent', 'Typically a minute or so', 'Seconds'],
            ['Default ON_ERROR', 'ABORT_STATEMENT', 'SKIP_FILE', 'n/a (client handles errors)'],
        ]),
        tags('Snowpipe', 'AUTO_INGEST', 'PIPE', 'Serverless', 'Event notification', 'Snowpipe Streaming', 'Kafka connector'),
    ),
    analogy('COPY INTO is a <strong>courier van that comes once a night</strong>. Snowpipe is a <strong>doorbell</strong>: each parcel is taken in '
            'shortly after it arrives. Snowpipe Streaming is a <strong>conveyor belt</strong> straight from the sender\'s door.'),
    snowpipe_anim(),
    real_world(
        scenario('Live biometric attendance',
                 p('Every centre\'s biometric system drops a small JSON file into S3 every five minutes. A pipe with <code>AUTO_INGEST</code> loads '
                   'each file within about a minute, so the attendance dashboard is near real time without any warehouse running all day.')),
    ),
    example(
        sq('''
CREATE OR REPLACE PIPE att_pipe AUTO_INGEST = TRUE AS
COPY INTO attendance_raw (v, src_file, loaded_at)
FROM (SELECT $1, METADATA$FILENAME, CURRENT_TIMESTAMP() FROM @s3_attendance)
FILE_FORMAT = (TYPE = JSON);

SHOW PIPES;                                  -- notification_channel = SQS ARN to configure on the bucket
SELECT SYSTEM$PIPE_STATUS('att_pipe');       -- executionState, pendingFileCount …
ALTER PIPE att_pipe REFRESH;                 -- queue files already in the stage (last 7 days)

SELECT * FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'ATTENDANCE_RAW', START_TIME => DATEADD(hour, -2, CURRENT_TIMESTAMP())));
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Create stage, file format and target table', 'Usually a raw table with VARIANT plus file name and load time.'),
        ('Create the pipe with AUTO_INGEST = TRUE', 'Its COPY statement defines the load.'),
        ('Connect the bucket events', 'Point the S3 event notification to the pipe\'s SQS ARN from SHOW PIPES.'),
        ('Backfill existing files', '<code>ALTER PIPE … REFRESH</code>.'),
        ('Monitor', 'SYSTEM$PIPE_STATUS, COPY_HISTORY, PIPE_USAGE_HISTORY for cost.'),
        title='Steps'),
    crossq(
        ('Does Snowpipe guarantee load order?', 'No. Files are loaded in parallel and not necessarily in arrival order. Use a timestamp column, not '
         'load order, when order matters.'),
        ('Can Snowpipe load the same file twice?', 'Its own 14-day load history prevents duplicates of the same file name and content. Re-uploading a '
         'modified file with the same name can be loaded again.'),
        ('How do you change a pipe\'s COPY statement?', 'Pause it (<code>ALTER PIPE … SET PIPE_EXECUTION_PAUSED = TRUE</code>), recreate it with '
         'CREATE OR REPLACE, then refresh for any files that arrived in between.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('How do you unload data from Snowflake to files?', 'Unloading Data', minutes=6, cards=[
    definition(
        defbox('<code>COPY INTO @stage/path FROM table_or_query</code> writes query results to files in an internal or external stage, in CSV, JSON '
               'or Parquet. By default Snowflake writes several files in parallel (names like <code>data_0_0_0.csv.gz</code>), compressed with gzip '
               'for CSV/JSON, up to <code>MAX_FILE_SIZE</code> (16 MB by default) each.',
               'Useful options: <code>SINGLE = TRUE</code> (one file), <code>HEADER = TRUE</code>, <code>OVERWRITE = TRUE</code>, '
               '<code>PARTITION BY</code> an expression (writes folder-like prefixes), <code>FILE_FORMAT</code>. Download from internal stages with '
               '<code>GET</code>.'),
        tags('COPY INTO @stage', 'Unload', 'SINGLE', 'MAX_FILE_SIZE', 'PARTITION BY', 'GET', 'Parquet'),
    ),
    analogy('Unloading is <strong>printing a report</strong>: you choose the format, whether to print one long document or one booklet per centre, '
            'and where to drop the printouts.'),
    unload_anim(),
    real_world(
        scenario('Sending results to the university portal',
                 p('The university\'s system reads Parquet files from an S3 prefix per centre. One COPY with '
                   '<code>PARTITION BY (\'centre=\' || centre)</code> writes <code>centre=Juhu/…parquet</code> and <code>centre=Kharghar/…parquet</code> '
                   'in a single statement.')),
    ),
    example(
        sq('''
-- one gzip CSV per thread, with header
COPY INTO @cdac_stage/exports/results_
FROM (SELECT roll_no, name, course, marks FROM students ORDER BY roll_no)
FILE_FORMAT = (TYPE = CSV COMPRESSION = GZIP)
HEADER = TRUE  OVERWRITE = TRUE;

-- Parquet, one folder per centre, on an external stage
COPY INTO @s3_exports/results/
FROM students
PARTITION BY ('centre=' || centre)
FILE_FORMAT = (TYPE = PARQUET)
HEADER = TRUE;

-- exactly one file (up to 5 GB with MAX_FILE_SIZE)
COPY INTO @cdac_stage/exports/students.csv FROM students
FILE_FORMAT = (TYPE = CSV COMPRESSION = NONE) SINGLE = TRUE HEADER = TRUE MAX_FILE_SIZE = 104857600;

LIST @cdac_stage/exports/;
GET  @cdac_stage/exports/students.csv file:///home/vineeta/downloads/;   -- SnowSQL
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Pick the format', 'Parquet for other data tools, CSV for spreadsheets, JSON for APIs.'),
        ('Decide the file layout', 'Parallel files (default), SINGLE, or PARTITION BY a column.'),
        ('Run COPY INTO @stage', 'Optionally from a query to filter and order the data.'),
        ('Deliver', 'GET from an internal stage, or let consumers read the external bucket.'),
        title='Steps'),
    crossq(
        ('Why not just SELECT in a client and save the result?', 'For large data COPY INTO is much faster: the warehouse writes files in parallel '
         'straight to cloud storage, instead of streaming every row through one client connection.'),
        ('Is unloading the best way to share data with another Snowflake customer?', 'No: Secure Data Sharing gives them live, read-only access without '
         'any files or copies.'),
        ('Does unloading cost money?', 'It uses warehouse credits, and data transfer charges apply if the stage is in another region or cloud.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What are the best practices for loading data efficiently into Snowflake?', 'Loading Best Practices', minutes=7, cards=[
    definition(
        ul('<strong>File size</strong>: aim for roughly <strong>100–250 MB compressed</strong> per file. Split very large files; combine tiny ones.',
           '<strong>Parallelism</strong>: COPY loads files in parallel, so more well-sized files keep a bigger warehouse busy. One huge file uses one thread.',
           '<strong>Dedicated loading warehouse</strong>: keep loading separate from BI so neither slows the other; size it by file volume.',
           '<strong>Organise stage paths</strong> by date/source (<code>/2026/02/15/</code>) and load with a path or PATTERN rather than scanning everything.',
           '<strong>ELT</strong>: load raw data first (even as text or VARIANT), then clean it with SQL inside Snowflake.',
           '<strong>Lineage</strong>: store file name, row number and load timestamp with each row.',
           '<strong>Continuous data</strong>: Snowpipe or Snowpipe Streaming instead of frequent small COPY jobs on a warehouse.'),
        tags('100–250 MB', 'Parallel load', 'Loading warehouse', 'ELT', 'PATTERN', 'Lineage'),
    ),
    analogy('Moving house: one giant crate needs a crane and one person waits; a thousand envelopes take forever to carry one by one. '
            '<strong>Medium boxes</strong> let the whole team carry at once.'),
    filesize_anim(),
    real_world(
        scenario('Fixing a slow nightly load',
                 p('A single 18 GB CSV export took 50 minutes on a Large warehouse, with most nodes idle. Splitting the export at source into about 90 '
                   'compressed files of ~200 MB let the same warehouse load in parallel; the load finished in minutes and could move to a smaller '
                   'warehouse.')),
    ),
    example(
        sh('''
# split a large CSV into 1,000,000-line chunks, keep the header in each, then gzip (Linux)
tail -n +2 attendance_2025.csv | split -l 1000000 -d --additional-suffix=.csv - att_part_
for f in att_part_*.csv; do (head -1 attendance_2025.csv; cat "$f") > "tmp_$f" && mv "tmp_$f" "$f"; done
gzip att_part_*.csv
'''),
        sq('''
-- load only today's folder, in parallel, into a raw table with lineage
COPY INTO attendance_raw (roll_no, att_date, status, src_file, src_line, loaded_at)
FROM (SELECT $1, $2, $3, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER, CURRENT_TIMESTAMP()
      FROM @s3_attendance/2026/02/15/)
FILE_FORMAT = (FORMAT_NAME = 'csv_results');
'''),
        title='Example'),
    steps(
        ('Measure file sizes', 'LIST @stage shows the size of each file.'),
        ('Fix at the source', 'Ask the producing system to write files of the right size, or split/combine in a pre-step.'),
        ('Load into raw tables', 'With lineage columns; transform afterwards.'),
        ('Tune warehouse size', 'Increase only while load time keeps dropping.'),
        title='Steps'),
    crossq(
        ('Does compression matter?', 'Yes. Compressed files (gzip, bzip2, zstd, brotli…) upload faster; COPY detects the compression automatically '
         '(COMPRESSION = AUTO). Parquet and ORC are already compressed internally.'),
        ('Is Parquet faster to load than CSV?', 'Often similar for raw loading; Parquet\'s benefits are typed columns, embedded schema and smaller files. '
         'Use MATCH_BY_COLUMN_NAME to load it into typed columns.'),
        ('How do you load data from a database such as MySQL?', 'Export to files and COPY, or use a replication/ELT tool (for example Fivetran, '
         'Airbyte, AWS DMS, or Snowflake\'s own connectors) that does CDC into Snowflake.'),
    ),
]),
])
