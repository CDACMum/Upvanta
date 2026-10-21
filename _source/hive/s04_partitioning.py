from build import *
from hive.anims import *
from hive.runner import hql, hq, sh, datafile

ATT_SETUP = '''
CREATE TABLE attendance (roll_no INT, name STRING, status STRING)
PARTITIONED BY (dt STRING)
STORED AS ORC;
INSERT INTO attendance PARTITION (dt='2026-10-11') VALUES (2401,'Anuj','P'),(2402,'Vineeta','P'),(2403,'Aarshvi','A');
INSERT INTO attendance PARTITION (dt='2026-10-12') VALUES (2401,'Anuj','A'),(2402,'Vineeta','P'),(2403,'Aarshvi','P');
INSERT INTO attendance PARTITION (dt='2026-10-13') VALUES (2401,'Anuj','P'),(2402,'Vineeta','P'),(2403,'Aarshvi','P');
'''

SECTION = dict(level='intermediate', title='Partitioning', questions=[

# ------------------------------------------------------------------ 15
Q('What is partitioning in Hive? How does it improve performance?', 'Partitioning & Pruning', minutes=9, cards=[
    definition(
        defbox('<strong>Partitioning</strong> divides a table into sub-directories based on the values of one or more <strong>partition '
               'columns</strong>, e.g. <code>PARTITIONED BY (dt STRING)</code> → <code>.../attendance/dt=2026-10-13/</code>.',
               'When a query filters on a partition column, Hive reads only the matching directories: <strong>partition pruning</strong>. '
               'Partition columns are not stored inside the data files; their values come from the directory names.'),
        tags('Partitioning', 'PARTITIONED BY', 'Partition Pruning', 'Sub-directory', 'Predicate'),
    ),
    analogy('An <strong>almirah with one drawer per month</strong> for fee receipts. To find October receipts you open only the October '
            'drawer instead of searching every receipt. The drawer label (the month) is not written on each receipt; it is known from the '
            'drawer you took it out of.'),
    partition_pruning(),
    real_world(
        scenario('Daily attendance at all C-DAC centres',
                 p('Face-recognition attendance produces ~2 GB per day. Partitioning by <code>dt</code> means "attendance for 13 October" reads '
                   '2 GB instead of the entire 1.5 TB history, and the daily load can overwrite just one partition if it is re-run.')),
    ),
    example(
        hql('''
CREATE TABLE attendance (roll_no INT, name STRING, status STRING)
PARTITIONED BY (dt STRING)          -- NOT repeated in the column list
STORED AS ORC;

INSERT INTO attendance PARTITION (dt='2026-10-11') VALUES (2401,'Anuj','P'),(2402,'Vineeta','P'),(2403,'Aarshvi','A');
INSERT INTO attendance PARTITION (dt='2026-10-12') VALUES (2401,'Anuj','A'),(2402,'Vineeta','P'),(2403,'Aarshvi','P');
INSERT INTO attendance PARTITION (dt='2026-10-13') VALUES (2401,'Anuj','P'),(2402,'Vineeta','P'),(2403,'Aarshvi','P');

SHOW PARTITIONS attendance;
dfs -ls -R /user/hive/warehouse/cdac.db/attendance;
SELECT dt, COUNT(*) AS present FROM attendance WHERE status = 'P' GROUP BY dt ORDER BY dt;
'''),
        hql('''
EXPLAIN SELECT * FROM attendance WHERE dt = '2026-10-13';
''', setup=ATT_SETUP),
        note('In the plan, <code>PartitionFilters: [... (dt = 2026-10-13)]</code> and <code>Location: ...(1 paths)[.../dt=2026-10-13]</code> show '
             'that only one of the three folders is read. In Hive, <code>EXPLAIN DEPENDENCY</code> lists the partitions a query will read.', 'Read the plan'),
        title='Example: Create, Load and Prune'),
    steps(
        ('Pick the partition column', 'A column used in most WHERE clauses with moderate cardinality: date, month, country, course.'),
        ('Create the table', '<code>CREATE TABLE t (...) PARTITIONED BY (dt STRING) STORED AS ORC;</code> (the partition column is not in the column list).'),
        ('Load each partition', '<code>INSERT OVERWRITE TABLE t PARTITION (dt=\'2026-10-13\') SELECT ...</code>'),
        ('Query with a partition filter', '<code>WHERE dt = \'2026-10-13\'</code> or <code>dt BETWEEN ...</code>; avoid functions on the column, e.g. <code>WHERE substr(dt,1,7)=...</code>, which can prevent pruning.'),
        ('Enforce it', '<code>SET hive.strict.checks.no.partition.filter=true</code> (Hive 3) rejects queries on partitioned tables without a partition filter.'),
        title='Steps to Create a Partitioned Table'),
    crossq(
        ('Can the partition column also be a normal column?', 'No. Declaring it in both places fails with "Column repeated in partitioning columns". It still appears in SELECT * as the last column.'),
        ('Where are partition values stored?', 'In the directory names and the metastore (<code>PARTITIONS</code>, <code>PARTITION_KEY_VALS</code>), not in the data files.'),
        ('Can a table have multiple partition columns?', 'Yes, nested in order: <code>PARTITIONED BY (year INT, month INT)</code> → <code>year=2026/month=10/</code>. Filter on the first level to prune most.'),
    ),
]),

# ------------------------------------------------------------------ 16
Q('What is the difference between static and dynamic partitioning?', 'Static vs Dynamic Partitioning', minutes=9, cards=[
    definition(
        defbox('<strong>Static partitioning</strong>: the partition value is given in the statement, '
               '<code>INSERT INTO t PARTITION (course=\'PG-DBDA\') SELECT ...</code>. All rows go to that partition.',
               '<strong>Dynamic partitioning</strong>: only the column is named, <code>PARTITION (course)</code>, and Hive takes each row\'s value '
               'from the <strong>last column(s) of the SELECT</strong>, creating partitions as needed.'),
        tags('Static Partition', 'Dynamic Partition', 'nonstrict', 'hive.exec.dynamic.partition', 'max.dynamic.partitions'),
    ),
    analogy('Static: a teacher carries a stack of papers to <strong>one labelled tray</strong> ("DBDA"). Dynamic: papers go on a '
            '<strong>sorting machine</strong> that reads the course written on each paper and drops it into the right tray, creating a new tray '
            'if it sees a new course.'),
    static_dynamic(),
    comparison(
        table(['Aspect', 'Static', 'Dynamic'], [
            ['Partition value', 'Written in the query', 'From data (last SELECT columns)'],
            ['Partitions per statement', 'One', 'Many'],
            ['Speed', 'Faster (no redistribution by key)', 'Slower; can create many files'],
            ['Risk', 'Wrong value hard-coded', 'Thousands of partitions by mistake (e.g. using a timestamp)'],
            ['Typical use', 'Daily load of "today"', 'Initial/back-fill load of history'],
        ]),
    ),
    real_world(
        scenario('Back-fill then daily',
                 p('Moving 3 years of exam results into a partitioned table: one <strong>dynamic</strong> INSERT creates ~1,000 daily partitions. '
                   'After that, the nightly job uses <strong>static</strong> partitioning with the run date from Airflow: '
                   '<code>PARTITION (dt=\'{{ ds }}\')</code>.')),
    ),
    example(
        hql('''
CREATE TABLE students_raw (roll_no INT, name STRING, course STRING, marks INT) STORED AS ORC;
INSERT INTO students_raw VALUES (2401,'Anuj','PG-DBDA',78), (2402,'Vineeta','PG-DBDA',91),
  (2403,'Aarshvi','PG-DAC',84), (2404,'Rohit','PG-DAI',66);

CREATE TABLE students_p (roll_no INT, name STRING, marks INT)
PARTITIONED BY (course STRING) STORED AS ORC;

-- STATIC: value fixed in the statement
INSERT INTO students_p PARTITION (course = 'PG-DBDA')
SELECT roll_no, name, marks FROM students_raw WHERE course = 'PG-DBDA';

-- DYNAMIC: value taken from the LAST select column
SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;
INSERT INTO students_p PARTITION (course)
SELECT roll_no, name, marks, course FROM students_raw WHERE course <> 'PG-DBDA';

SHOW PARTITIONS students_p;
SELECT * FROM students_p ORDER BY roll_no;
'''),
        hq('''
-- Mixed: static first level, dynamic second level (allowed even in strict mode)
INSERT INTO results PARTITION (year = 2026, course)
SELECT roll_no, marks, course FROM staging;

-- Safety limits (defaults shown)
SET hive.exec.max.dynamic.partitions = 1000;          -- per statement
SET hive.exec.max.dynamic.partitions.pernode = 100;   -- per mapper/reducer
SET hive.exec.max.created.files = 100000;
''', 'Strict mode and limits'),
        title='Example: Both Styles'),
    steps(
        ('Enable dynamic partitioning', '<code>SET hive.exec.dynamic.partition=true;</code> (default true in recent versions)'),
        ('Allow all-dynamic partitions', '<code>SET hive.exec.dynamic.partition.mode=nonstrict;</code> (strict needs at least one static column)'),
        ('Put partition columns last', 'In the SELECT, in the same order as <code>PARTITIONED BY</code>.'),
        ('Check cardinality first', '<code>SELECT COUNT(DISTINCT course) FROM src</code> to avoid exceeding the limits.'),
        ('Run and verify', '<code>SHOW PARTITIONS t;</code>'),
        title='Steps for a Dynamic Partition Load'),
    crossq(
        ('Why is "strict" the default dynamic partition mode?', 'To prevent a mistake (e.g. partitioning by a timestamp) from creating millions of partitions and files. Strict mode requires at least one static partition column.'),
        ('Does the name of the SELECT column matter for dynamic partitions?', 'No, only the <strong>position</strong>: the last column(s) feed the partition columns.'),
        ('How do you avoid too many small files with dynamic partitions?', 'Add <code>DISTRIBUTE BY course</code> so each partition is written by one reducer, or enable <code>hive.optimize.sort.dynamic.partition</code>.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('Files were added directly to HDFS but Hive does not show them. Why? How do you fix it?', 'MSCK REPAIR & ADD PARTITION', minutes=8, cards=[
    definition(
        defbox('Hive reads only partitions <strong>registered in the metastore</strong>. Folders created directly in HDFS (by Spark, Flume, '
               '<code>hdfs dfs -put</code>) are invisible until registered with <code>ALTER TABLE ... ADD PARTITION</code> or discovered with '
               '<code>MSCK REPAIR TABLE</code>.'),
        tags('MSCK REPAIR TABLE', 'ADD PARTITION', 'DROP PARTITION', 'Metastore Sync', 'partition.discovery'),
    ),
    analogy('The metastore is the <strong>attendance register</strong>. A new student who walks into class without being added to the '
            'register is physically present but never counted. <code>MSCK REPAIR</code> is the teacher doing a head-count and adding the missing names.'),
    msck_anim(),
    real_world(
        scenario('Spark writes, Hive reads',
                 p('A Spark job writes each day\'s results to <code>/data/results/dt=YYYY-MM-DD/</code>. The Hive external table over '
                   '<code>/data/results</code> showed no data for new days until the Airflow DAG got a final task: '
                   '<code>ALTER TABLE results ADD IF NOT EXISTS PARTITION (dt=\'{{ ds }}\')</code>.')),
    ),
    example(
        hql('''
CREATE EXTERNAL TABLE results (roll_no INT, marks INT)
PARTITIONED BY (dt STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION '/data/results';

-- Folders already exist in HDFS, but the metastore knows nothing yet
SHOW PARTITIONS results;
SELECT COUNT(*) AS rows_visible FROM results;

-- Option 1: register one known partition (fast)
ALTER TABLE results ADD IF NOT EXISTS PARTITION (dt = '2026-10-11');
SELECT dt, COUNT(*) AS n FROM results GROUP BY dt;

-- Option 2: scan the location and add every missing partition
MSCK REPAIR TABLE results;
SHOW PARTITIONS results;
SELECT dt, COUNT(*) AS n FROM results GROUP BY dt ORDER BY dt;
''', files={'results/dt=2026-10-11/p.csv': '2401,78\n2402,91\n',
            'results/dt=2026-10-12/p.csv': '2401,80\n2402,89\n2403,84\n',
            'results/dt=2026-10-13/p.csv': '2401,82\n'}),
        hq('''
ALTER TABLE results DROP IF EXISTS PARTITION (dt < '2025-01-01');   -- retention
ALTER TABLE results PARTITION (dt='2026-10-13') SET LOCATION '/archive/results/2026-10-13';
MSCK REPAIR TABLE results SYNC PARTITIONS;   -- Hive 3: also drops partitions whose folders were deleted
-- Hive 4 / Hive 3.x: automatic discovery for external tables
ALTER TABLE results SET TBLPROPERTIES ('discover.partitions' = 'true');
''', 'More partition management'),
        title='Example: Making New Folders Visible'),
    steps(
        ('Write data in Hive layout', 'Folder names must be <code>col=value</code>, e.g. <code>dt=2026-10-13</code>.'),
        ('Register the partition', '<code>ALTER TABLE t ADD IF NOT EXISTS PARTITION (dt=\'2026-10-13\');</code> after each load.'),
        ('Or repair in bulk', '<code>MSCK REPAIR TABLE t;</code> after a back-fill or migration.'),
        ('Verify', '<code>SHOW PARTITIONS t;</code> and a count for the new date.'),
        title='Steps to Register New Partitions'),
    crossq(
        ('Why not run MSCK REPAIR after every load?', 'It lists the whole table location and compares it with the metastore; on tables with tens of thousands of partitions (or on S3) that is slow. ADD PARTITION for the known folder is instant.'),
        ('What if a folder name is not in <code>col=value</code> form?', 'MSCK ignores it (or fails, depending on <code>hive.msck.path.validation</code>). Register it explicitly with <code>ADD PARTITION ... LOCATION \'/odd/path\'</code>.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('How do you choose a partition column? What is over-partitioning?', 'Choosing Partitions', minutes=7, cards=[
    definition(
        defbox('A good partition column is <strong>used in most filters</strong>, has <strong>low to moderate cardinality</strong> (tens to a '
               'few thousand values over the table\'s life) and gives partitions of a healthy size (hundreds of MB to a few GB).',
               '<strong>Over-partitioning</strong> means too many, too small partitions (e.g. by <code>roll_no</code> or by minute). It creates '
               'millions of small files and metastore entries and makes queries <em>slower</em>.'),
        tags('Partition Design', 'Cardinality', 'Over-partitioning', 'Small Files', 'Multi-level Partitions'),
    ),
    analogy('Drawers per <strong>month</strong> help. A drawer per <strong>student</strong> means 10,000 drawers holding one sheet each: '
            'the cupboard is mostly drawer handles, and finding anything means opening thousands of drawers.'),
    over_partition_anim(),
    real_world(
        scenario('Good and bad choices',
                 table(['Column', 'Verdict', 'Why'], [
                     ['<code>dt</code> (event date)', 'Good', 'In almost every filter; ~365 partitions/year'],
                     ['<code>course</code>', 'Good as second level', 'Few values; used in reports'],
                     ['<code>roll_no</code>', 'Bad', 'Very high cardinality: use bucketing instead'],
                     ['<code>event_time</code> (timestamp)', 'Bad', 'Unique values → one partition per row'],
                     ['<code>status</code> (P/A)', 'Usually bad', 'Only 2 values: partitions too big, little pruning benefit'],
                 ])),
    ),
    example(
        hql('''
-- Two-level partitioning: year, then month
CREATE TABLE fees (receipt_no INT, roll_no INT, amount DECIMAL(10,2))
PARTITIONED BY (yr INT, mon INT) STORED AS ORC;

INSERT INTO fees PARTITION (yr, mon) VALUES
  (1, 2401, 45000.00, 2026, 7), (2, 2402, 45000.00, 2026, 7), (3, 2401, 30000.00, 2026, 10);

SHOW PARTITIONS fees;
SELECT yr, mon, SUM(amount) AS collected FROM fees WHERE yr = 2026 GROUP BY yr, mon ORDER BY mon;
'''),
        title='Example: Multi-level Partitions'),
    steps(
        ('List the common filters', 'From real queries/dashboards: which columns appear in WHERE?'),
        ('Estimate partition count and size', '<code>SELECT col, COUNT(*) FROM src GROUP BY col</code>; aim for ≥ ~256 MB per partition.'),
        ('Choose 1–2 levels', 'Coarse first (year/month or date), optional low-cardinality second level.'),
        ('Use bucketing for high-cardinality keys', 'Joins/lookups on roll_no or customer_id → CLUSTERED BY.'),
        title='Steps to Design Partitions'),
    crossq(
        ('A table has 200,000 partitions and queries are slow even with filters. Why?', 'Query planning fetches partition metadata from the metastore and lists folders; with that many partitions this dominates. Coarser partitioning (month instead of hour) usually fixes it.'),
        ('Should you partition a 2 GB table?', 'Usually no: it fits in a few files and a full scan is cheap. Partition when tables are large and queries filter on a column.'),
    ),
]),
])
