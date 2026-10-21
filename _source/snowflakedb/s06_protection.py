from build import *
from snowflakedb.anims import *
from snowflakedb.runner import sql, sq

SECTION = dict(level='intermediate', title='Time Travel, Fail-safe & Cloning', questions=[

# ------------------------------------------------------------------ 26
Q('What is Time Travel? How do you query or restore historical data?', 'Time Travel', minutes=9, cards=[
    definition(
        defbox('<strong>Time Travel</strong> lets you access data as it was at any point within a retention period: query it, clone it, or restore '
               'dropped tables, schemas and databases. It works because micro-partitions are immutable: changes write new ones, and the old ones '
               'are kept for the retention period.',
               'Retention is set by <code>DATA_RETENTION_TIME_IN_DAYS</code> on the account, database, schema or table: default <strong>1 day</strong>; '
               'up to <strong>90 days</strong> for permanent objects on Enterprise edition and above; 0 or 1 day for transient and temporary tables. '
               'Setting it to 0 disables Time Travel for that object.'),
        table(['Syntax', 'Meaning'], [
            ["<code>AT(TIMESTAMP => '2026-02-15 10:00'::TIMESTAMP_LTZ)</code>", 'Data as of that moment'],
            ['<code>AT(OFFSET => -60*30)</code>', 'Data as of 30 minutes ago (seconds, negative)'],
            ["<code>AT(STATEMENT => '&lt;query_id&gt;')</code>", 'Data including the changes of that statement'],
            ["<code>BEFORE(STATEMENT => '&lt;query_id&gt;')</code>", 'Data just before that statement ran'],
            ['<code>UNDROP TABLE | SCHEMA | DATABASE</code>', 'Restore the most recently dropped object with that name'],
        ]),
        tags('Time Travel', 'AT', 'BEFORE', 'OFFSET', 'UNDROP', 'DATA_RETENTION_TIME_IN_DAYS'),
    ),
    analogy('Version history in Google Docs: you can open the document as it looked yesterday at 10 a.m., copy from it, or restore it, but only for as '
            'long as the history is kept.'),
    timetravel_anim(),
    real_world(
        scenario('The marks that changed overnight',
                 p('A coordinator reports that some SQL marks changed after a moderation script ran at 22:00. Comparing the table '
                   '<code>AT(TIMESTAMP => \'… 21:55\')</code> with the current table using <code>MINUS</code> shows exactly which rows the script '
                   'changed, before anyone decides whether to roll back.')),
    ),
    example(
        sq('''
ALTER TABLE results SET DATA_RETENTION_TIME_IN_DAYS = 30;     -- Enterprise: up to 90

-- the table as it was 30 minutes ago
SELECT * FROM results AT(OFFSET => -60*30) WHERE roll_no = 2402;

-- which rows did last night's script change?
SELECT * FROM results AT(TIMESTAMP => '2026-02-15 21:55:00'::TIMESTAMP_LTZ)
MINUS
SELECT * FROM results;

-- the state just before one statement
SELECT COUNT(*) FROM results BEFORE(STATEMENT => '01b2c3d4-0000-1a2b-0000-00012345abcd');

-- restore a dropped table
DROP TABLE results;
UNDROP TABLE results;

SHOW TABLES HISTORY LIKE 'RESULTS';     -- includes dropped versions and when they were dropped
'''),
        title='Example (shown, not executed: needs a real account)'),
    steps(
        ('Set retention per table', 'Longer for critical tables, 0–1 day for scratch and staging.'),
        ('Find the moment or statement', 'Query history gives timestamps and query IDs.'),
        ('Look before restoring', 'Query with AT/BEFORE and compare with the current data.'),
        ('Restore', 'UNDROP, clone the old version, or INSERT the missing rows back.'),
        title='Steps'),
    crossq(
        ('What if you UNDROP a table but a new table with the same name exists?', 'UNDROP fails. Rename the existing table first, then UNDROP.'),
        ('Does Time Travel cost money?', 'Yes, storage for the changed and deleted micro-partitions kept during the retention period. Tables that are '
         'rewritten often can have a large Time Travel footprint.'),
        ('Can you query a point before the table was created or beyond retention?', 'No. Snowflake returns an error saying the requested time is out of '
         'the Time Travel range.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What is Fail-safe and how is it different from Time Travel?', 'Fail-safe', minutes=6, cards=[
    definition(
        defbox('<strong>Fail-safe</strong> is a non-configurable <strong>7-day</strong> period that begins when Time Travel retention ends, for '
               '<strong>permanent</strong> tables only. During Fail-safe you cannot query or restore the data yourself; only Snowflake Support can '
               'recover it, on a best-effort basis, after a disaster. Transient and temporary tables have no Fail-safe.'),
        table(['', 'Time Travel', 'Fail-safe'], [
            ['Duration', '0–90 days (configurable)', '7 days (fixed)'],
            ['Who can use it', 'You, with SQL', 'Only Snowflake Support'],
            ['Purpose', 'Everyday mistakes: bad DELETE, dropped table, audits', 'Last-resort disaster recovery'],
            ['Applies to', 'All table types (transient/temporary max 1 day)', 'Permanent tables only'],
            ['Cost', 'Storage for retained data', 'Storage for retained data'],
        ]),
        tags('Fail-safe', '7 days', 'Continuous Data Protection', 'Snowflake Support', 'Permanent tables'),
    ),
    analogy('Time Travel is your own <strong>recycle bin</strong>: you can open it and take things back. Fail-safe is the city\'s '
            '<strong>landfill</strong> for the next week: the municipality might dig something out for you in an emergency, but you cannot go in yourself.'),
    failsafe_anim(),
    real_world(
        scenario('Explaining a storage bill',
                 p('An hourly job does <code>CREATE OR REPLACE TABLE stg_attendance AS …</code> on a permanent table. Every replaced version goes '
                   'through 1 day of Time Travel and then 7 days of Fail-safe, so storage shows many times the live size. Converting it to a '
                   'transient table removes the Fail-safe part entirely.')),
    ),
    example(
        sq('''
-- live, Time Travel and Fail-safe bytes per table (real account)
SELECT table_catalog, table_schema, table_name, is_transient,
       active_bytes      / POWER(1024, 3) AS active_gb,
       time_travel_bytes / POWER(1024, 3) AS time_travel_gb,
       failsafe_bytes    / POWER(1024, 3) AS failsafe_gb
FROM   SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
WHERE  deleted = FALSE
ORDER  BY failsafe_bytes DESC
LIMIT  10;
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Find tables with large Fail-safe bytes', 'TABLE_STORAGE_METRICS.'),
        ('Check whether they can be rebuilt', 'Staging and intermediate tables usually can.'),
        ('Recreate them as transient', 'Or put them in a transient schema.'),
        ('Rely on Time Travel and backups for recovery', 'Do not plan on Fail-safe for normal operations.'),
        title='Steps'),
    crossq(
        ('Can you shorten or disable Fail-safe?', 'Not for permanent tables. Use transient or temporary tables when Fail-safe is not wanted.'),
        ('How long does a Fail-safe recovery take?', 'It is a support process and can take hours or days; it is not meant for quick fixes.'),
        ('Is Fail-safe a backup?', 'It is part of Snowflake\'s data protection, but it is not under your control. For guaranteed recovery points use '
         'longer Time Travel, clones, replication, or Snowflake\'s backup features where available.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What is zero-copy cloning? How does it work and what is it used for?', 'Zero-Copy Cloning', minutes=8, cards=[
    definition(
        defbox('<code>CREATE TABLE | SCHEMA | DATABASE new_name CLONE source</code> creates a copy that <strong>shares the source\'s micro-partitions</strong>. '
               'Only metadata is written, so a clone of terabytes is created in seconds and initially uses <strong>no additional storage</strong>. '
               'After that the two objects are fully independent: changes to either write new micro-partitions belonging only to that object, and '
               'you pay storage only for those changes.',
               'Clones can be combined with Time Travel: <code>CLONE results AT(OFFSET => -3600)</code>. Cloning a database or schema clones the '
               'objects inside it (tables, views, sequences, file formats, streams, tasks…); cloned tasks start suspended, and internal named stages '
               'are not cloned.'),
        tags('CLONE', 'Zero-copy', 'Metadata only', 'Dev/Test environments', 'AT / BEFORE', 'Copy-on-write'),
    ),
    analogy('Two shortcuts on your desktop pointing to the <strong>same photo album</strong>. The moment someone edits a page through one shortcut, '
            'that page is copied for them and the other person still sees the original.'),
    clone_anim(),
    real_world(
        scenario('A safe test environment in seconds',
                 p('Before trying a new grading formula, the data team runs <code>CREATE DATABASE exam_dev CLONE exam;</code>. They get a full-size, '
                   'production-identical copy instantly, test on real volumes, and drop it afterwards. Production is never touched, and storage cost is '
                   'only for the rows they changed.')),
    ),
    example(
        sql('''
CREATE TABLE students_dev CLONE students;

-- experiment on the clone: apply 5 grace marks to everyone below 70
UPDATE students_dev SET marks = marks + 5 WHERE marks < 70;

-- the original is unchanged
SELECT s.roll_no, s.name, s.marks AS prod_marks, d.marks AS dev_marks
FROM   students s JOIN students_dev d ON d.roll_no = s.roll_no
WHERE  s.marks <> d.marks
ORDER  BY s.roll_no;

SELECT (SELECT COUNT(*) FROM students)     AS prod_rows,
       (SELECT COUNT(*) FROM students_dev) AS dev_rows;
''', show='dml'),
        sq('''
CREATE DATABASE exam_dev CLONE exam;                                -- whole database
CREATE TABLE results_0900 CLONE results AT(TIMESTAMP => '2026-02-15 09:00'::TIMESTAMP_LTZ);
CREATE TABLE students_copy CLONE students COPY GRANTS;              -- keep the source table's grants
'''),
        title='Example'),
    steps(
        ('Clone the object', 'Table for a quick experiment, database for a full environment.'),
        ('Optionally clone a past state', 'Add AT/BEFORE.'),
        ('Work on the clone', 'It behaves exactly like any other object.'),
        ('Drop when done', 'Storage is released for changed data that is no longer needed.'),
        title='Steps'),
    crossq(
        ('Does a clone copy the grants?', 'A cloned database or schema keeps the grants on the objects inside it, but not grants on the cloned container '
         'itself. For a single table, add <code>COPY GRANTS</code>.'),
        ('What happens to a stream that is cloned?', 'The clone starts its own offset; any changes that were unconsumed in the source stream are not '
         'available through the cloned stream.'),
        ('Is a clone a backup?', 'It protects against logical mistakes for as long as you keep it, and costs only for changes. But it lives in the same '
         'account and region, so it does not protect against a regional outage; use replication for that.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('Someone ran DELETE without a WHERE clause on a production table. How do you recover?', 'Recovering from Mistakes', minutes=8, cards=[
    definition(
        ul('<strong>Stop further writes</strong> to the table if possible (pause tasks or pipes that write to it).',
           '<strong>Find the bad statement</strong>: its query ID in Snowsight Query History or <code>QUERY_HISTORY</code>.',
           '<strong>Inspect</strong> the old state with <code>BEFORE(STATEMENT => \'id\')</code>.',
           '<strong>Restore</strong>: clone the old state and <code>ALTER TABLE … SWAP WITH …</code>, or re-insert only the missing rows if other '
           'valid changes happened after the mistake.',
           '<strong>Verify</strong> row counts and key totals, then resume pipelines.',
           '<strong>Prevent</strong>: least-privilege roles, pre-change clones before risky scripts, and enough retention on critical tables.'),
        tags('BEFORE(STATEMENT)', 'Query ID', 'SWAP WITH', 'Clone', 'Retention', 'Least privilege'),
    ),
    analogy('Like recovering a deleted email: find when it was deleted, open the trash from <strong>just before</strong> that moment, and move it '
            'back, before the trash is emptied.'),
    recovery_anim(),
    real_world(
        scenario('Partial damage',
                 p('A script deleted 3 of 8 students\' results by mistake at 10:42, but at 10:50 new correct results were inserted. Swapping in the '
                   '10:41 version would lose the 10:50 rows, so the team inserts only the rows that exist in the old version and are missing now.')),
    ),
    example(
        sq('''
-- full restore when nothing else changed after the mistake
CREATE TABLE results_restored CLONE results BEFORE(STATEMENT => '01b2c3d4-0000-1a2b-0000-00012345abcd');
ALTER TABLE results SWAP WITH results_restored;      -- atomic name exchange
DROP TABLE results_restored;                         -- now holds the damaged version
'''),
        p('When other good changes happened afterwards, put back only what was lost. Here a pre-change clone (a good habit before running risky '
          'scripts) plays the role of the Time Travel version:', top=True),
        sql('''
CREATE TABLE students_before_fix CLONE students;     -- safety copy before the script

DELETE FROM students WHERE course = 'PGCP-AC';       -- the mistake (should have been one roll_no)
INSERT INTO students VALUES (2409, 'Ishaan', 'PGCP-BDA', 'Kharghar', 81.00, '2026-02-06');   -- a valid new row

-- restore only the rows that were lost
INSERT INTO students
SELECT b.* FROM students_before_fix b
WHERE  NOT EXISTS (SELECT 1 FROM students s WHERE s.roll_no = b.roll_no);

SELECT course, COUNT(*) AS students FROM students GROUP BY course ORDER BY course;
''', show='dml'),
        p('The two PGCP-AC students come back and the new student 2409 is kept: 9 students in total.', top=True),
        title='Example'),
    steps(
        ('Contain', 'Pause writers; note the time of discovery.'),
        ('Locate', 'Query ID and time of the bad statement.'),
        ('Choose the method', 'Swap for a clean full restore; insert-missing for partial damage.'),
        ('Verify and document', 'Counts, totals, and a short incident note.'),
        ('Harden', 'Roles without DELETE on production for ad hoc users; longer retention on key tables.'),
        title='Steps'),
    crossq(
        ('What if the mistake was a DROP TABLE?', '<code>UNDROP TABLE results;</code> restores it, with its data and history, as long as it is within '
         'retention.'),
        ('What if it was discovered after the retention period?', 'Time Travel can no longer help. Only Fail-safe (via Snowflake Support, for permanent '
         'tables within 7 more days), a clone or a replica can.'),
        ('Why is SWAP better than DROP + RENAME?', 'SWAP exchanges the two names in one atomic metadata operation, so there is no moment when the table '
         'does not exist for users and pipelines.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('How does Snowflake support business continuity: replication, failover and cross-region sharing?', 'Replication & Failover', minutes=7, cards=[
    definition(
        defbox('<strong>Replication</strong> copies objects from a primary account to secondary accounts in other regions or even other clouds. A '
               '<strong>replication group</strong> replicates a set of objects (databases, shares, and with account replication also users, roles, '
               'warehouses, integrations, network policies) together, consistently, on a schedule. Only changed micro-partitions are transferred.',
               'A <strong>failover group</strong> (Business Critical edition and above) can be <strong>promoted</strong> in the secondary account, making '
               'it the new primary during an outage. <strong>Client Redirect</strong> provides a connection URL that can be switched to whichever '
               'account is primary, so applications reconnect without configuration changes.'),
        tags('Replication group', 'Failover group', 'Secondary database', 'Client Redirect', 'Cross-region', 'Cross-cloud', 'RPO / RTO'),
    ),
    analogy('Keeping a <strong>second, continually updated copy of the exam cell\'s records</strong> in another city. If the main office floods, the '
            'other office is declared the main office and everyone is told to call its number instead.'),
    replication_anim(),
    real_world(
        scenario('Results must be published on time',
                 p('C-DAC runs its primary account in AWS Mumbai and replicates the <code>EXAM</code> and <code>RESULTS</code> databases plus roles and '
                   'users every 10 minutes to an Azure Pune account. If the primary region is unavailable on result day, the failover group is promoted '
                   'and the results portal, using the Client Redirect URL, keeps working with at most about 10 minutes of data lag.')),
    ),
    example(
        sq('''
-- in the primary account (Business Critical for failover groups)
CREATE FAILOVER GROUP exam_fg
  OBJECT_TYPES = DATABASES, ROLES, USERS, WAREHOUSES
  ALLOWED_DATABASES = exam, results
  ALLOWED_ACCOUNTS  = cdac.mumbai_dr
  REPLICATION_SCHEDULE = '10 MINUTE';

-- in the secondary account
CREATE FAILOVER GROUP exam_fg AS REPLICA OF cdac.mumbai_prod.exam_fg;
ALTER FAILOVER GROUP exam_fg REFRESH;            -- manual refresh, besides the schedule

-- during an outage, run in the secondary account
ALTER FAILOVER GROUP exam_fg PRIMARY;

-- monitor replication cost and progress
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.REPLICATION_GROUP_USAGE_HISTORY;
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Define RPO and RTO', 'How much data loss and downtime are acceptable.'),
        ('Create a secondary account', 'In another region (or cloud) within the same organization.'),
        ('Create replication or failover groups', 'Choose objects and a schedule that meets the RPO.'),
        ('Set up Client Redirect', 'Applications use the connection URL, not the account URL.'),
        ('Test failover', 'Regularly, including failing back.'),
        title='Steps'),
    crossq(
        ('Can you write to a secondary database?', 'No, secondary databases are read-only until the group is promoted to primary. They are useful for '
         'read-only reporting in another region meanwhile.'),
        ('What does replication cost?', 'Data transfer between regions/clouds, compute for the refresh (serverless), and storage in the secondary account.'),
        ('How do you share data with a consumer in another region?', 'Shares only work within a region directly. Replicate the database to an account in '
         'the consumer\'s region and share from there, or use a listing with Cross-Cloud Auto-Fulfilment.'),
    ),
]),
])
