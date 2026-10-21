from build import *
from cassandra.anims import *
from cassandra.runner import cql, cq, sh, conf

SECTION = dict(level='basic', title='Keyspaces, Tables & Keys', questions=[

# ------------------------------------------------------------------ 6
Q('What is a keyspace? Explain SimpleStrategy and NetworkTopologyStrategy.', 'Keyspace & Replication Strategy', minutes=7, cards=[
    definition(
        defbox('A <strong>keyspace</strong> is the outermost container for tables, similar to a database or schema in SQL. Its most important '
               'property is <strong>replication</strong>: the strategy and the <strong>replication factor (RF)</strong>, i.e. how many copies of '
               'every row are kept. It also has <code>durable_writes</code> (use the commit log; always keep it true).'),
        table(['Strategy', 'How replicas are placed', 'Use'], [
            ['<code>SimpleStrategy</code>', 'First replica on the token owner, the next RF-1 copies on the following nodes clockwise. Ignores racks and DCs.', 'Single-node labs, tests'],
            ['<code>NetworkTopologyStrategy</code>', 'RF given per data centre; within each DC, replicas placed on different racks where possible.', 'All production clusters (even with one DC)'],
        ]),
        tags('Keyspace', 'Replication factor', 'SimpleStrategy', 'NetworkTopologyStrategy', 'durable_writes'),
    ),
    analogy('A keyspace is a <strong>filing policy</strong> for a department: "keep 3 photocopies of every file in the Mumbai office, in three '
            'different cupboards, and 2 copies in the Pune office". Every table in that department follows the policy.'),
    keyspace_anim(),
    real_world(
        scenario('Different keyspaces, different policies',
                 ul('<code>exam_live</code>: <code>{\'dc_mumbai\': 3, \'dc_pune\': 2}</code>, critical data in both regions.',
                    '<code>proctor_events</code>: <code>{\'dc_mumbai\': 2}</code>, high volume, one region, cheaper.',
                    '<code>lab_sandbox</code>: <code>SimpleStrategy</code> with RF 1 on a student\'s laptop.')),
    ),
    example(
        cql('''
CREATE KEYSPACE exam_live
  WITH replication = {'class': 'NetworkTopologyStrategy', 'dc_mumbai': 3, 'dc_pune': 2}
  AND durable_writes = true;

CREATE KEYSPACE lab_sandbox
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- creating it again fails; IF NOT EXISTS makes the script re-runnable
CREATE KEYSPACE lab_sandbox WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
CREATE KEYSPACE IF NOT EXISTS lab_sandbox WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE exam_live;
''', expect_error=True, keyspace=False),
        cq('''
-- change RF later, then stream the new copies with repair
ALTER KEYSPACE exam_live
  WITH replication = {'class': 'NetworkTopologyStrategy', 'dc_mumbai': 3, 'dc_pune': 3};
-- on each node in dc_pune:   nodetool repair -full exam_live
''', 'Changing replication (real cluster)'),
        title='Example'),
    steps(
        ('Name the data centres', 'The DC names must match what the snitch reports (<code>nodetool status</code>).'),
        ('Choose RF per DC', '3 is the usual production value: QUORUM still works with one replica down.'),
        ('Create the keyspace', 'Use NetworkTopologyStrategy.'),
        ('After changing RF', 'Run a full repair so existing data is copied to the new replicas.'),
        title='Steps'),
    crossq(
        ('Why is RF 3 so common?', 'QUORUM of 3 is 2, so reads and writes at QUORUM keep working with one replica down while still giving strong '
         'consistency. With RF 2, QUORUM is 2, so any single failure blocks QUORUM requests.'),
        ('Can RF be larger than the number of nodes?', 'You can create such a keyspace, but writes at levels needing more replicas than exist will fail. '
         'Keep RF ≤ number of nodes in each DC.'),
        ('Is the system keyspace replicated?', '<code>system</code> is local to each node. <code>system_auth</code>, <code>system_distributed</code> and '
         '<code>system_traces</code> are replicated; increase <code>system_auth</code> RF in production so logins survive node failures.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('Explain primary key, partition key and clustering columns.', 'Partition & Clustering Keys', minutes=10, cards=[
    definition(
        defbox('The <strong>primary key</strong> of a Cassandra table has two parts: <code>PRIMARY KEY ((partition key columns), clustering columns…)</code>.',
               'The <strong>partition key</strong> (first element) is hashed to a token that decides <strong>which nodes</strong> store the data. All rows '
               'with the same partition key form one <strong>partition</strong>, stored together on the same replicas. The <strong>clustering '
               'columns</strong> decide the <strong>sort order of rows inside the partition</strong> and make each row unique within it.',
               'With <code>PRIMARY KEY (a)</code> each partition has one row. With <code>PRIMARY KEY (a, b)</code> partition key is a, clustering '
               'column b. With <code>PRIMARY KEY ((a, b), c)</code> the partition key is the pair (a, b).'),
        tags('Primary key', 'Partition key', 'Clustering column', 'Partition', 'Token', 'Wide row'),
    ),
    analogy('A <strong>filing cabinet per student</strong>: the roll number (partition key) decides which cabinet and in which building it sits; inside '
            'the cabinet, the papers are kept sorted by exam date (clustering column). Fetching "all of Anuj\'s papers since October" means opening one '
            'cabinet and taking one contiguous bundle.'),
    primary_key_anim(),
    real_world(
        scenario('Result history screen',
                 p('The student portal shows "my results, newest first". The table <code>marks_by_student</code> uses <code>roll_no</code> as the '
                   'partition key and <code>exam_date DESC, module</code> as clustering columns, so the screen is one single-partition read already sorted.')),
    ),
    example(
        cql('''
CREATE TABLE marks_by_student (
  roll_no   int,
  exam_date date,
  module    text,
  marks     int,
  PRIMARY KEY ((roll_no), exam_date, module)
) WITH CLUSTERING ORDER BY (exam_date DESC, module ASC);

INSERT INTO marks_by_student (roll_no, exam_date, module, marks) VALUES (2401, '2026-09-10', 'SQL', 78);
INSERT INTO marks_by_student (roll_no, exam_date, module, marks) VALUES (2401, '2026-10-05', 'Spark', 84);
INSERT INTO marks_by_student (roll_no, exam_date, module, marks) VALUES (2401, '2026-10-05', 'Kafka', 72);
INSERT INTO marks_by_student (roll_no, exam_date, module, marks) VALUES (2402, '2026-09-10', 'SQL', 91);

SELECT roll_no, token(roll_no), exam_date, module, marks FROM marks_by_student;

SELECT * FROM marks_by_student WHERE roll_no = 2401 AND exam_date >= '2026-10-01';

-- the full primary key is required to write a row
INSERT INTO marks_by_student (roll_no, module, marks) VALUES (2402, 'Spark', 88);
''', expect_error=True),
        p('All rows of 2401 share one token: they are one partition on the same replicas. Inside it, rows are sorted by '
          '<code>exam_date DESC</code>, then <code>module ASC</code>, which is why Kafka comes before Spark on the same date.', top=True),
        title='Example'),
    steps(
        ('Write down the query', '"Marks of a student, newest first, optionally from a date".'),
        ('Equality inputs → partition key', '<code>roll_no</code>.'),
        ('Range / ordering inputs → clustering columns', '<code>exam_date DESC</code>.'),
        ('Add columns to make rows unique', '<code>module</code> (two modules can share a date).'),
        ('Check partition size', 'Rows per student stay small, so the partition is bounded.'),
        title='Steps to Choose a Primary Key'),
    crossq(
        ('What is the difference between primary key and partition key?', 'The partition key is only the first part; it decides data placement. The '
         'primary key is partition key + clustering columns and uniquely identifies a row.'),
        ('What happens if two rows have the same full primary key?', 'They are the same row: the later write overwrites the earlier one (upsert).'),
        ('Can a table have no clustering columns?', 'Yes, e.g. <code>PRIMARY KEY (roll_no)</code>: each partition holds exactly one row, a pure key-value lookup.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What is a composite partition key? Why would you use one?', 'Composite Partition Key', minutes=8, cards=[
    definition(
        defbox('A <strong>composite partition key</strong> is made of two or more columns, written in an inner pair of parentheses: '
               '<code>PRIMARY KEY ((sensor, day), ts)</code>. The token is computed from <strong>all</strong> of them together.',
               'Reasons to use one: (1) <strong>bound partition size</strong> by adding a time bucket (day, month) or a bucket number; (2) '
               '<strong>spread load</strong> so that one busy entity does not hit the same nodes all the time; (3) the query naturally always provides '
               'both values. The consequence: <strong>every query must supply every partition key column</strong> (with = or IN).'),
        tags('Composite partition key', 'Bucketing', 'Time bucket', 'Partition size', 'Hot spot'),
    ),
    analogy('Instead of one ever-growing diary per sensor, you start a <strong>new notebook every day</strong> labelled "lab-1 / 14 Oct". To read a page '
            'you must know both the sensor and the date written on the cover.'),
    composite_pk_anim(),
    real_world(
        scenario('Lab temperature sensors',
                 p('Each of 200 lab sensors reports every second (86,400 rows a day). With <code>(sensor, day)</code> as the partition key, each partition '
                   'holds one day (about 3 MB), and the dashboard query "lab-1 today" reads exactly one partition.')),
    ),
    example(
        cql('''
CREATE TABLE readings (
  sensor text, day date, ts timestamp, temp double,
  PRIMARY KEY ((sensor, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

INSERT INTO readings (sensor, day, ts, temp) VALUES ('lab-1', '2026-10-13', '2026-10-13 23:59:00+0530', 23.1);
INSERT INTO readings (sensor, day, ts, temp) VALUES ('lab-1', '2026-10-14', '2026-10-14 10:00:00+0530', 24.5);
INSERT INTO readings (sensor, day, ts, temp) VALUES ('lab-1', '2026-10-14', '2026-10-14 10:05:00+0530', 25.3);

SELECT sensor, day, token(sensor, day), ts, temp FROM readings;

SELECT * FROM readings WHERE sensor = 'lab-1' AND day = '2026-10-14';

-- only part of the partition key: Cassandra cannot compute the token
SELECT * FROM readings WHERE sensor = 'lab-1';

-- several days: list them with IN
SELECT * FROM readings WHERE sensor = 'lab-1' AND day IN ('2026-10-13', '2026-10-14');
''', expect_error=True),
        title='Example'),
    steps(
        ('Estimate rows per natural key', 'e.g. readings per sensor per day.'),
        ('Pick a bucket that keeps partitions small', 'Hour, day or month, so partitions stay well under ~100 MB.'),
        ('Add the bucket to the partition key', '<code>((sensor, day), ts)</code>.'),
        ('Make the application compute the bucket', 'Reads for a range of days query each bucket (IN or parallel queries).'),
        title='Steps to Bucket a Partition'),
    crossq(
        ('Is ((a, b), c) the same as (a, b, c)?', 'No. ((a, b), c) has partition key (a, b) and clustering column c. (a, b, c) has partition key a and '
         'clustering columns b, c: all rows with the same a share one partition.'),
        ('Is a large IN on the partition key a good idea?', 'Keep it small (a few values). Each value is a separate partition, possibly on different '
         'nodes, and one coordinator must gather them all. For many buckets, run parallel asynchronous queries instead.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('How does clustering order work? What are the rules for ORDER BY?', 'Clustering Order & ORDER BY', minutes=8, cards=[
    definition(
        defbox('Rows inside a partition are stored on disk <strong>sorted by the clustering columns</strong>, in the direction set by '
               '<code>WITH CLUSTERING ORDER BY (col ASC|DESC, …)</code> (ASC by default). Reads return rows in this order.',
               '<code>ORDER BY</code> in a SELECT can only (1) be used when the partition key is restricted with <code>=</code> or <code>IN</code>, '
               '(2) name <strong>clustering columns</strong>, (3) in their <strong>declared order</strong>, and (4) request either the stored order '
               'or its exact reverse. Cassandra never sorts by arbitrary columns.'),
        tags('Clustering order', 'ORDER BY', 'ASC / DESC', 'Reverse read', 'Sorted storage'),
    ),
    analogy('Pages in a register are bound in date order. You can read the register <strong>front to back or back to front</strong>, but you cannot '
            'ask the register to rearrange itself by the amount written on each page.'),
    clustering_order_anim(),
    real_world(
        scenario('Choose the order you read most',
                 p('Dashboards almost always need the <strong>latest</strong> readings, so time-series tables use <code>ts DESC</code>: "last 10 readings" '
                   'reads the first 10 rows of the partition. Reverse reads are supported but slightly less efficient.')),
    ),
    example(
        cql('''
SELECT ts, temp FROM readings WHERE sensor = 'lab-1' AND day = '2026-10-14' LIMIT 2;

SELECT ts, temp FROM readings WHERE sensor = 'lab-1' AND day = '2026-10-14' ORDER BY ts ASC;

SELECT ts, temp FROM readings WHERE sensor = 'lab-1' AND day = '2026-10-14' ORDER BY temp DESC;

SELECT ts, temp FROM readings ORDER BY ts ASC;
''', setup='''
CREATE TABLE readings (sensor text, day date, ts timestamp, temp double, PRIMARY KEY ((sensor, day), ts)) WITH CLUSTERING ORDER BY (ts DESC);
INSERT INTO readings (sensor, day, ts, temp) VALUES ('lab-1', '2026-10-14', '2026-10-14 10:00:00+0530', 24.5);
INSERT INTO readings (sensor, day, ts, temp) VALUES ('lab-1', '2026-10-14', '2026-10-14 10:05:00+0530', 25.3);
INSERT INTO readings (sensor, day, ts, temp) VALUES ('lab-1', '2026-10-14', '2026-10-14 10:10:00+0530', 25.9);
''', expect_error=True),
        title='Example'),
    steps(
        ('Decide the dominant read order', 'Latest first → DESC; chronological replay → ASC.'),
        ('Declare it on the table', '<code>WITH CLUSTERING ORDER BY (ts DESC)</code>; it cannot be changed later without a new table.'),
        ('For multiple clustering columns', 'Declare each direction: <code>(exam_date DESC, module ASC)</code>; ORDER BY must flip all or none.'),
        ('Need another sort key?', 'Create another table with that column as a clustering column.'),
        title='Steps'),
    crossq(
        ('Can you ORDER BY exam_date DESC, module DESC if the table is (exam_date DESC, module ASC)?', 'No: you may only use the stored order (DESC, ASC) '
         'or its exact reverse (ASC, DESC). Mixing gives "Unsupported order by relation".'),
        ('How do you get the top 10 marks of an exam?', 'Model a table partitioned by exam with <code>marks DESC</code> as a clustering column (plus roll '
         'number for uniqueness), then <code>LIMIT 10</code>.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What are static columns? When would you use them?', 'Static Columns', minutes=7, cards=[
    definition(
        defbox('A <strong>static column</strong> (declared with <code>STATIC</code>) has <strong>one value per partition</strong>, shared by all rows of '
               'that partition, instead of one value per row. It is stored once in the partition header.',
               'Rules: allowed only in tables with clustering columns; cannot be part of the primary key; can be updated with only the partition key '
               'in the WHERE clause; <code>SELECT DISTINCT partition_key, static_col</code> reads one row per partition cheaply.'),
        tags('STATIC', 'Partition-level value', 'One-to-many', 'SELECT DISTINCT'),
    ),
    analogy('A <strong>class register</strong>: the class teacher\'s name is written once on the cover (static), while each page lists a student '
            '(rows). Changing the class teacher means correcting only the cover, and every page now belongs to the new teacher.'),
    static_anim(),
    real_world(
        scenario('Batch details with its students',
                 p('The coordinator portal shows a batch: batch-level fields (coordinator, start date, lab room) plus the student list. Storing batch fields as '
                   'static columns in <code>students_by_batch</code> gives the whole screen in one partition read, and the batch info is not repeated in every row.')),
    ),
    example(
        cql('''
CREATE TABLE students_by_batch (
  batch       text,
  roll_no     int,
  name        text,
  coordinator text STATIC,
  lab_room    text STATIC,
  PRIMARY KEY (batch, roll_no)
);

INSERT INTO students_by_batch (batch, coordinator, lab_room) VALUES ('DBDA-2026', 'Vineeta', 'Lab-3');
INSERT INTO students_by_batch (batch, roll_no, name) VALUES ('DBDA-2026', 2401, 'Anuj');
INSERT INTO students_by_batch (batch, roll_no, name) VALUES ('DBDA-2026', 2402, 'Aarshvi');
SELECT * FROM students_by_batch WHERE batch = 'DBDA-2026';

UPDATE students_by_batch SET coordinator = 'Manoj' WHERE batch = 'DBDA-2026';
SELECT batch, roll_no, coordinator FROM students_by_batch WHERE batch = 'DBDA-2026';

SELECT DISTINCT batch, coordinator, lab_room FROM students_by_batch;
'''),
        title='Example'),
    steps(
        ('Find values shared by all rows of a partition', 'Batch coordinator, account owner, sensor location.'),
        ('Declare them STATIC', '<code>coordinator text STATIC</code>.'),
        ('Write them with only the partition key', 'INSERT or UPDATE without clustering columns.'),
        ('Read them cheaply', '<code>SELECT DISTINCT pk, static_cols</code> returns one row per partition.'),
        title='Steps'),
    crossq(
        ('What if a partition has only the static value and no rows?', 'SELECT returns one row with the static values and <code>null</code> clustering '
         'columns, so the partition is still visible.'),
        ('Why not just use a separate batches table?', 'You can, but then the screen needs two queries. Static columns put the "one" side into the same '
         'partition as the "many" side, which works well when they are always read together.'),
    ),
]),
])
