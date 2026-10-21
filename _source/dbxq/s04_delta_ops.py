from build import *
from dbxq.anims import *
from dbxq.runner import sql, sq, pyrun, py

MARKS_LOG = """
CREATE TABLE marks_log (roll_no INT, subject STRING, marks INT, exam_date DATE)
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
INSERT INTO marks_log VALUES (2401, 'SQL', 72, DATE'2026-03-01'), (2402, 'SQL', 85, DATE'2026-03-01');
INSERT INTO marks_log VALUES (2401, 'Python', 64, DATE'2026-03-02'), (2402, 'Python', 90, DATE'2026-03-02');
"""

SMALL_FILES = """
CREATE TABLE attendance (roll_no INT, att_date DATE, present BOOLEAN);
""" + ''.join(f"INSERT INTO attendance SELECT 2401 + (id % 8), DATE'2026-03-01' + {d}, (id + {d}) % 5 <> 0 FROM range(8);\n"
              for d in range(12))

SECTION = dict(level='intermediate', title='Delta Lake: Time Travel & Optimisation', questions=[

# ------------------------------------------------------------------ 16
Q('What is time travel in Delta Lake? How do you query and restore old versions?', 'Time Travel & RESTORE', minutes=9, cards=[
    definition(
        defbox('Every commit creates a new <strong>version</strong> of a Delta table. Because old data files are kept until VACUUM removes them, '
               'you can read any retained version: this is <strong>time travel</strong>.'),
        table(['Syntax', 'Meaning'], [
            ['<code>DESCRIBE HISTORY t</code>', 'List versions: timestamp, user, operation, parameters, metrics'],
            ['<code>SELECT … FROM t VERSION AS OF 3</code>', 'Read version 3 (also <code>t@v3</code>)'],
            ["<code>SELECT … FROM t TIMESTAMP AS OF '2026-03-01 10:00'</code>", 'Read the latest version committed at or before that time'],
            ['<code>RESTORE TABLE t TO VERSION AS OF 3</code>', 'Make the current table equal to version 3 (a new commit)'],
            ['<code>spark.read.option("versionAsOf", 3).table("t")</code>', 'Python equivalent'],
        ]),
        defbox('How far back you can go depends on two properties: <code>delta.logRetentionDuration</code> (history in the log, default 30 days) '
               'and <code>delta.deletedFileRetentionDuration</code> (how long VACUUM keeps removed data files, default 7 days). In practice, '
               'time travel is reliable for the VACUUM retention period.'),
        tags('Time travel', 'VERSION AS OF', 'TIMESTAMP AS OF', 'DESCRIBE HISTORY', 'RESTORE', 'logRetentionDuration'),
    ),
    analogy('Like the <strong>revision history</strong> of a shared document: you can open yesterday\'s version, copy a paragraph from it, or '
            'restore it, and the restore itself appears as a new entry in the history.'),
    timetravel_anim(),
    real_world(
        scenario('An accidental DELETE',
                 p('A teaching assistant runs <code>DELETE FROM marks_log WHERE subject = \'Python\'</code> instead of a single roll number. '
                   'Within minutes the team checks <code>DESCRIBE HISTORY</code>, confirms the previous version with a time-travel query, and '
                   'runs <code>RESTORE</code>. No backup tapes, no downtime.')),
    ),
    example(
        sql('''
DELETE FROM marks_log WHERE subject = 'Python';

DESCRIBE HISTORY marks_log;

SELECT * FROM marks_log VERSION AS OF 2 ORDER BY roll_no, subject;

RESTORE TABLE marks_log TO VERSION AS OF 2;

SELECT COUNT(*) AS rows_now FROM marks_log;
''', setup=MARKS_LOG, data=False),
        pyrun('''
v1 = spark.read.option("versionAsOf", 1).table("marks_log")
now = spark.table("marks_log")
print(v1.count(), now.count())
now.exceptAll(v1).orderBy("roll_no").show()          # rows added since version 1
''', setup=MARKS_LOG, data=False),
        p('<code>RESTORE</code> reports how many files it removed and restored. It is version 4 in the history, so even the restore can be '
          'undone.', top=True),
        title='Example'),
    steps(
        ('Look at the history', '<code>DESCRIBE HISTORY t LIMIT 10</code>: find the bad operation and the version before it.'),
        ('Verify', 'Query <code>VERSION AS OF n</code> and compare counts or rows with the current table.'),
        ('Restore or repair', 'RESTORE the whole table, or INSERT/MERGE only the missing rows from the old version.'),
        ('Prevent', 'Grant MODIFY only to pipelines; keep enough retention for your recovery window.'),
        title='Steps'),
    crossq(
        ('Is time travel a backup?', 'Only partly. It protects against bad writes for the retention period, but the data lives in the same '
         'storage account. For disaster recovery use deep clones or replication to another region.'),
        ('What is the difference between a shallow clone and a deep clone?', '<code>CREATE TABLE t2 SHALLOW CLONE t</code> copies only the log '
         '(it references the source files; cheap, good for tests). <code>DEEP CLONE</code> copies the data files too, giving an independent '
         'copy; re-running it copies only what changed.'),
        ('Why can time travel fail with "file not found" for a version still listed in the history?', 'The log still has the commit, but VACUUM '
         'already deleted the data files that version needs.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is the small-files problem? How do OPTIMIZE, Z-ORDER and data skipping help?', 'OPTIMIZE & Data Skipping', minutes=9, cards=[
    definition(
        defbox('Many small writes (streaming micro-batches, hourly appends, over-partitioned tables) produce thousands of small files. Every file '
               'costs a cloud-storage request, metadata in the log and task-scheduling overhead, so reads slow down: the '
               '<strong>small-files problem</strong>.',
               '<code>OPTIMIZE t</code> compacts small files into larger ones (bin-packing, target about 1 GB) in a new version; readers are not '
               'blocked. <code>OPTIMIZE t ZORDER BY (col)</code> also sorts rows along one or more columns so that each file covers a narrow range of '
               'values. Delta keeps <strong>min/max statistics</strong> per file, and queries skip files that cannot match a filter '
               '(<strong>data skipping</strong>).'),
        table(['Feature', 'What it does'], [
            ['Optimized writes', 'Shuffle before writing so each partition gets fewer, larger files'],
            ['Auto compaction', 'After a write, compact small files in the touched partitions'],
            ['Predictive optimization', 'Databricks runs OPTIMIZE / VACUUM / ANALYZE on managed tables automatically'],
            ['<code>delta.dataSkippingNumIndexedCols</code>', 'Statistics are collected on the first 32 columns by default'],
        ]),
        tags('Small files', 'OPTIMIZE', 'ZORDER BY', 'Bin-packing', 'Data skipping', 'Min/max statistics', 'Predictive optimization'),
    ),
    analogy('Small files are like an exam cell receiving <strong>one envelope per answer sheet</strong>: opening envelopes takes longer than '
            'reading. OPTIMIZE repacks them into a few bundles, and Z-ORDER sorts each bundle by roll number so you can go straight to the '
            'right one.'),
    optimize_anim(),
    real_world(
        scenario('A streaming table after a month',
                 p('A stream writes attendance every minute: after 30 days the table has about 43,000 files of a few KB each, and a simple count '
                   'takes minutes. A nightly <code>OPTIMIZE … ZORDER BY (roll_no)</code> (or predictive optimization on a managed table) brings '
                   'it down to a few files per day, and lookups for one student read only one or two files.')),
    ),
    example(
        sql('''
DESCRIBE DETAIL attendance;

OPTIMIZE attendance ZORDER BY (roll_no);

DESCRIBE DETAIL attendance;

SELECT COUNT(*) AS days_present FROM attendance WHERE roll_no = 2405 AND present;
''', setup=SMALL_FILES, data=False),
        pyrun('''
import json
loc = spark.sql("DESCRIBE DETAIL attendance").first()["location"] + "/_delta_log/"
last = sorted(f.name for f in dbutils.fs.ls(loc) if f.name.endswith(".json"))[-1]
for line in dbutils.fs.head(loc + last).splitlines():
    if '"add"' in line:
        st = json.loads(json.loads(line)["add"]["stats"])
        print(st["numRecords"], "rows, roll_no", st["minValues"]["roll_no"], "-", st["maxValues"]["roll_no"])
''', setup=SMALL_FILES + 'OPTIMIZE attendance ZORDER BY (roll_no);', data=False),
        p('Twelve daily loads produced 12 files. OPTIMIZE rewrote them into one file (the metrics show 12 removed, 1 added) and the table is '
          'smaller because one file compresses better than twelve. The statistics in the new <code>add</code> action are what data '
          'skipping reads; with a large table Z-ORDER produces many files, each with a narrow roll_no range.', top=True),
        title='Example'),
    steps(
        ('Measure', 'DESCRIBE DETAIL: numFiles and sizeInBytes; average file size = size / files.'),
        ('Prevent', 'Enable optimized writes and auto compaction (default for many Databricks writes).'),
        ('Compact', 'Schedule OPTIMIZE, or rely on predictive optimization for managed tables.'),
        ('Cluster', 'Z-ORDER (or better, liquid clustering) on columns used in selective filters.'),
        title='Steps'),
    crossq(
        ('Does OPTIMIZE change query results?', 'No. It only rewrites files: the commit has <code>dataChange = false</code>, so streaming readers '
         'of the table do not reprocess the rows.'),
        ('How many columns should you Z-order by?', 'One to three columns that appear in selective filters. Each extra column weakens the '
         'clustering of the others, and Z-ordering a column without statistics or with low cardinality does little.'),
        ('Is Z-ORDER incremental?', 'No. Re-running it rewrites the files in scope. Liquid clustering is incremental, which is one reason '
         'Databricks recommends it for new tables.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('Partitioning, Z-ordering or liquid clustering: how should you lay out a Delta table?', 'Partitioning vs Liquid Clustering', minutes=9, cards=[
    definition(
        table(['', 'Partitioning', 'Z-ordering', 'Liquid clustering'], [
            ['Syntax', '<code>PARTITIONED BY (col)</code>', '<code>OPTIMIZE t ZORDER BY (col)</code>', '<code>CLUSTER BY (col)</code> or <code>CLUSTER BY AUTO</code>'],
            ['Layout', 'One folder per value', 'Rows sorted inside files', 'Files clustered by keys, managed by Delta'],
            ['Good for', 'Low-cardinality column always in filters (date, region), very large tables', 'Selective filters on high-cardinality columns', 'Most tables, including changing query patterns'],
            ['Incremental', 'Yes (new data goes to its folder)', 'No, full rewrite of scope', 'Yes'],
            ['Change the keys', 'Rewrite the table', 'Re-run with new columns (rewrite)', '<code>ALTER TABLE t CLUSTER BY (…)</code>, no rewrite needed'],
        ]),
        defbox('Databricks recommends <strong>liquid clustering</strong> for new tables. It cannot be combined with partitioning or Z-order on the '
               'same table. Over-partitioning (a partition column with thousands of values) is one of the most common causes of small files.'),
        tags('PARTITIONED BY', 'Partition pruning', 'ZORDER', 'Liquid clustering', 'CLUSTER BY', 'CLUSTER BY AUTO'),
    ),
    analogy('Partitioning is a <strong>separate cupboard per course</strong>. Z-ordering is <strong>arranging files inside each cupboard by roll '
            'number</strong>, which you must redo when new files arrive. Liquid clustering is a <strong>librarian who keeps things arranged as '
            'they come in</strong> and can switch to arranging by a different key when you ask.'),
    layout_anim(),
    real_world(
        scenario('Re-designing an exam table',
                 p('A table <code>PARTITIONED BY (roll_no)</code> has 30,000 partitions of a few rows each, and every query is slow. It is '
                   're-created with <code>CLUSTER BY (exam_date, roll_no)</code>: one CTAS, after which new data is clustered incrementally and the '
                   'team can later change the keys to <code>(centre, exam_date)</code> without rewriting the history.')),
    ),
    example(
        sql('''
CREATE TABLE marks_by_subject
PARTITIONED BY (subject)
AS SELECT * FROM VALUES
  (2401, 'SQL', 72), (2402, 'SQL', 85), (2403, 'SQL', 91),
  (2401, 'Python', 64), (2402, 'Python', 90)
  AS t(roll_no, subject, marks);

DESCRIBE DETAIL marks_by_subject;

EXPLAIN SELECT roll_no, marks FROM marks_by_subject WHERE subject = 'SQL' AND marks > 80;
''', data=False),
        sq('''
-- liquid clustering (Databricks Runtime 13.3+; recommended)
CREATE TABLE exam_results (roll_no INT, exam_date DATE, centre STRING, marks INT)
CLUSTER BY (exam_date, roll_no);

ALTER TABLE exam_results CLUSTER BY (centre, exam_date);   -- change keys, no rewrite
OPTIMIZE exam_results;                                     -- clusters data incrementally
ALTER TABLE exam_results CLUSTER BY AUTO;                  -- let Databricks choose keys
'''),
        p('The plan shows <code>PartitionFilters: [isnotnull(subject), (subject = SQL)]</code>: the Python folder is never listed or read. '
          '<code>marks &gt; 80</code> is a data filter, pushed to the Parquet reader.', top=True),
        title='Example'),
    steps(
        ('List the filters', 'Which columns appear in WHERE and JOIN clauses of the important queries?'),
        ('Check the size', 'Tables under about 1 TB rarely need partitioning.'),
        ('Prefer liquid clustering', 'CLUSTER BY the 1–4 most selective filter columns, or CLUSTER BY AUTO.'),
        ('Partition only when obvious', 'A date column on a very large table, with ≥ 1 GB per partition.'),
        title='Steps'),
    crossq(
        ('What is partition pruning?', 'Skipping whole partition folders whose values cannot satisfy the filter. It needs a filter on the '
         'partition column itself; <code>WHERE year(exam_date) = 2026</code> on a <code>exam_date</code> partition may still prune through '
         'generated columns.'),
        ('Can you convert a partitioned table to liquid clustering?', 'Not in place: liquid clustering needs an unpartitioned table, so you '
         'create a new table with <code>CLUSTER BY</code> (CTAS or deep clone) and switch readers to it.'),
        ('What are good partition columns?', 'Low cardinality (dozens to a few thousand values), used in almost every query, and large enough '
         'that each partition holds at least about 1 GB.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What does VACUUM do? How do retention periods and deletion vectors affect it?', 'VACUUM & Retention', minutes=8, cards=[
    definition(
        defbox('<code>VACUUM t</code> permanently deletes data files that are <strong>not referenced by the current version</strong> and were '
               'marked removed longer ago than the retention threshold (default <strong>7 days</strong>, table property '
               '<code>delta.deletedFileRetentionDuration</code>). It also deletes files left by failed writes. <code>VACUUM t DRY RUN</code> lists '
               'the files without deleting them; <code>RETAIN n HOURS</code> overrides the threshold.',
               'A retention below 168 hours is refused unless <code>spark.databricks.delta.retentionDurationCheck.enabled = false</code>, because '
               'long-running readers or writers might still need those files. After VACUUM, time travel to versions that need deleted files fails.',
               '<strong>Deletion vectors</strong> mark deleted or updated rows in a small file instead of rewriting the data file. The old rows '
               'physically remain until the file is rewritten (<code>OPTIMIZE</code>, or <code>REORG TABLE … APPLY (PURGE)</code>) and then '
               'vacuumed, which matters for GDPR-style deletion requests.'),
        tags('VACUUM', 'DRY RUN', 'RETAIN HOURS', 'deletedFileRetentionDuration', 'retentionDurationCheck', 'Deletion vectors', 'REORG PURGE'),
    ),
    analogy('VACUUM is <strong>emptying the recycle bin</strong>. Files in it can still be restored, but the bin is only emptied of items older '
            'than a week, and once emptied they are gone for good.'),
    vacuum_anim(),
    real_world(
        scenario('A right-to-erasure request',
                 p('A former student asks for their data to be deleted. <code>DELETE FROM students WHERE roll_no = …</code> removes them from the '
                   'current version, but older files (and, with deletion vectors, the current file) still contain the row. The team runs '
                   '<code>REORG TABLE students APPLY (PURGE)</code> and, after the retention period, <code>VACUUM</code>, so the data is physically '
                   'gone, and documents that time travel beyond that point is no longer possible.')),
    ),
    example(
        sql('''
VACUUM marks_log RETAIN 0 HOURS DRY RUN;

SET spark.databricks.delta.retentionDurationCheck.enabled = false;
VACUUM marks_log RETAIN 0 HOURS DRY RUN;
VACUUM marks_log RETAIN 0 HOURS;

DESCRIBE HISTORY marks_log;
SELECT COUNT(*) AS rows_now FROM marks_log;
''', setup=MARKS_LOG + "UPDATE marks_log SET marks = marks + 3 WHERE subject = 'Python' AND marks < 70;\n"
               "DELETE FROM marks_log WHERE roll_no = 2402 AND subject = 'SQL';", data=False, expect_error=True),
        p('The UPDATE and the DELETE each rewrote one file, leaving two files that the current version no longer uses. With a 0-hour '
          'retention (for this demo only) VACUUM deletes them; the current data is untouched, but versions 1–3, which need those files, '
          'can no longer be read. The VACUUM START / VACUUM END entries '
          'in the history record what happened.', top=True),
        title='Example'),
    steps(
        ('Keep the default 7 days', 'Long enough for running jobs, streams and short-term recovery.'),
        ('Run regularly', 'Weekly VACUUM, or predictive optimization on managed tables.'),
        ('Dry-run first', 'Check what will be deleted on important tables.'),
        ('Plan for erasure', 'DELETE → REORG … PURGE (with deletion vectors) → VACUUM after the retention period.'),
        title='Steps'),
    crossq(
        ('Does VACUUM delete transaction log files?', 'No. Log files are cleaned up automatically after <code>delta.logRetentionDuration</code> '
         '(30 days) when checkpoints are written. VACUUM deletes data files only.'),
        ('Can VACUUM make running queries fail?', 'Yes, if the retention is shorter than the query or stream needs: a reader that started from an '
         'older snapshot can find its files deleted. That is why short retention is blocked by default.'),
        ('Does OPTIMIZE free storage?', 'Not immediately: it adds compacted files and marks the small ones removed. Storage drops after VACUUM '
         'deletes the removed files.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What is Change Data Feed (CDF)? How do you read row-level changes from a Delta table?', 'Change Data Feed', minutes=8, cards=[
    definition(
        defbox('<strong>Change Data Feed</strong> records row-level changes (inserts, updates, deletes) for every commit of a Delta table once '
               '<code>delta.enableChangeDataFeed = true</code>. Readers get the changed rows with three extra columns:'),
        table(['Column', 'Values'], [
            ['<code>_change_type</code>', '<code>insert</code>, <code>delete</code>, <code>update_preimage</code> (row before), <code>update_postimage</code> (row after)'],
            ['<code>_commit_version</code>', 'Table version of the change'],
            ['<code>_commit_timestamp</code>', 'Time of that commit'],
        ]),
        defbox('Read in SQL with <code>table_changes(\'t\', start [, end])</code>, or in Python with '
               '<code>spark.read.option("readChangeFeed", "true").option("startingVersion", n).table("t")</code> (also as a stream). Only changes '
               'made after the property was enabled are available.'),
        tags('Change Data Feed', 'enableChangeDataFeed', 'table_changes', 'readChangeFeed', 'update_preimage', 'update_postimage', 'CDC'),
    ),
    analogy('The table is the <strong>current class register</strong>; CDF is the <strong>register of corrections</strong> beside it: "marks of '
            '2401 changed from 64 to 67 in version 4". Downstream teams copy only the corrections, not the whole register.'),
    cdf_anim(),
    real_world(
        scenario('Keeping a gold table in sync',
                 p('A gold table <code>course_averages</code> is rebuilt every hour from a 50-crore-row silver table, although only a few thousand '
                   'rows change. Reading the CDF since the last processed version gives just those rows; a MERGE updates only the affected '
                   'courses, and the job runs in seconds.')),
    ),
    example(
        sql('''
INSERT INTO marks_log VALUES (2403, 'SQL', 91, DATE'2026-03-01');
UPDATE marks_log SET marks = marks + 3 WHERE subject = 'Python' AND marks < 70;
DELETE FROM marks_log WHERE roll_no = 2402 AND subject = 'SQL';

SELECT roll_no, subject, marks, _change_type, _commit_version
FROM   table_changes('marks_log', 3)
ORDER  BY _commit_version, roll_no, _change_type;

SELECT _change_type, COUNT(*) AS changes FROM table_changes('marks_log', 0) GROUP BY _change_type ORDER BY _change_type;
''', setup=MARKS_LOG, data=False),
        sql('''
SELECT * FROM table_changes('students', 1);
''', setup="UPDATE students SET marks = 70 WHERE roll_no = 2404;", expect_error=True, show='all',
            title='Databricks SQL: CDF not enabled'),
        p('The UPDATE (version 4) produced a pre-image (64) and a post-image (67) for 2401; the DELETE (version 5) produced one '
          '<code>delete</code> row. On a table without the property, <code>table_changes</code> fails.', top=True),
        title='Example'),
    steps(
        ('Enable', "<code>ALTER TABLE t SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')</code> or set it at creation."),
        ('Remember where you stopped', 'Store the last processed version (or use a streaming checkpoint).'),
        ('Read the changes', 'table_changes / readChangeFeed from the next version.'),
        ('Apply downstream', 'MERGE the post-images and deletes into the target; ignore pre-images unless you need them.'),
        title='Steps'),
    crossq(
        ('CDF or Structured Streaming on the table?', 'A plain Delta stream only reads appends and fails (or must ignore) when rows are updated or '
         'deleted. A stream with <code>readChangeFeed</code> receives updates and deletes as rows, so it can propagate them.'),
        ('Does CDF cost extra storage?', 'A little: for UPDATE/DELETE/MERGE Delta may write change files in <code>_change_data/</code>. Inserts '
         'and deletes of whole files are derived from the log. Change files follow the same VACUUM retention.'),
        ('Is CDF the same as CDC from a database?', 'Similar idea, different source: CDC tools (Debezium, Lakeflow Connect) capture changes '
         'from an operational database; CDF exposes changes made to a Delta table. They are often chained: CDC → bronze → MERGE → silver → '
         'CDF → gold.'),
    ),
]),

])
