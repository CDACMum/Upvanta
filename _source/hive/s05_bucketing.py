from build import *
from hive.anims import *
from hive.runner import hql, hq, sh, datafile

SECTION = dict(level='intermediate', title='Bucketing & Sampling', questions=[

# ------------------------------------------------------------------ 19
Q('What is bucketing in Hive? How does it work?', 'Bucketing', minutes=9, cards=[
    definition(
        defbox('<strong>Bucketing</strong> (<code>CLUSTERED BY (col) INTO n BUCKETS</code>) divides a table, or each partition, into a '
               '<strong>fixed number of files</strong>. Each row goes to bucket <code>hash(col) mod n</code>, so all rows with the same key are '
               'always in the same bucket file.',
               'It is used for high-cardinality columns where partitioning would create too many folders, and it enables '
               '<strong>bucket map joins, SMB joins and efficient sampling</strong>.'),
        tags('Bucketing', 'CLUSTERED BY', 'INTO n BUCKETS', 'SORTED BY', 'Hash', 'hive.enforce.bucketing'),
    ),
    analogy('Exam answer sheets are sorted into <strong>4 trays by the last digits of the roll number</strong> (roll mod 4). The number of '
            'trays never changes, however many students write the exam, and a given roll number always ends up in the same tray. To find, '
            'or to match, roll 2403 you only look in tray 3.'),
    bucketing_anim(),
    real_world(
        scenario('Joining two large tables on roll_no',
                 p('<code>students</code> (2 million rows) and <code>exam_attempts</code> (500 million rows) are both bucketed by '
                   '<code>roll_no</code> into 64 buckets and sorted. The nightly join runs as a sort-merge-bucket join, bucket 0 with bucket 0, '
                   'etc., without shuffling 500 million rows across the network.')),
    ),
    example(
        hql('''
CREATE TABLE students_b (roll_no INT, name STRING, course STRING)
CLUSTERED BY (roll_no) SORTED BY (roll_no) INTO 4 BUCKETS
STORED AS ORC;

INSERT INTO students_b VALUES
  (2401,'Anuj','PG-DBDA'), (2402,'Vineeta','PG-DBDA'), (2403,'Aarshvi','PG-DAC'),
  (2404,'Rohit','PG-DAC'), (2405,'Meera','PG-DAI'),  (2406,'Kabir','PG-DAI');

dfs -ls -R /user/hive/warehouse/cdac.db/students_b;

-- Which file did each row land in? (bucket id = first 5 digits of the file name)
SELECT roll_no, name, regexp_extract(input_file_name(), '/(\\\\d{5})_', 1) AS bucket_file
FROM students_b ORDER BY roll_no;
'''),
        note('Every row landed in bucket <code>roll_no mod 4</code>, exactly as Hive computes it. Hive writes <strong>one file per bucket</strong> '
             '(<code>000000_0</code> … <code>000003_0</code>); Spark SQL, which ran this example, may write one file per bucket per task, which is '
             'why some bucket numbers appear twice. The bucket number at the start of the file name is what matters.', 'Read the output'),
        title='Example: Create a Bucketed Table and See the Bucket Files'),
    steps(
        ('Choose the bucket column', 'The join or lookup key with high cardinality (roll_no, customer_id).'),
        ('Choose the bucket count', 'Aim for bucket files of roughly 128 MB–1 GB; use a power of 2 so different tables can have multiples of each other.'),
        ('Create the table', '<code>CLUSTERED BY (roll_no) [SORTED BY (roll_no)] INTO 32 BUCKETS</code>.'),
        ('Load with INSERT ... SELECT', 'Hive 2+ always enforces bucketing on insert (older versions needed <code>SET hive.enforce.bucketing=true</code>). Never <code>LOAD DATA</code> into a bucketed table: files would not be bucketed.'),
        ('Use it', 'Joins on the bucket key, <code>TABLESAMPLE(BUCKET x OUT OF n ON roll_no)</code>.'),
        title='Steps to Create a Bucketed Table'),
    crossq(
        ('How is the bucket number computed for a STRING column?', 'Using the Java-style hash of the value: <code>(hashCode &amp; Integer.MAX_VALUE) % numBuckets</code>. For INT the hash is the value itself. Hive 3 bucketing version 2 uses Murmur3.'),
        ('Can you change the number of buckets later?', '<code>ALTER TABLE ... INTO n BUCKETS</code> changes only metadata; existing files are not rebucketed, so you must rewrite (INSERT OVERWRITE) the data.'),
        ('Can a table be both partitioned and bucketed?', 'Yes: each partition folder then contains n bucket files. This is very common: partition by date, bucket by id.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('Partitioning vs bucketing: what is the difference and when do you use each?', 'Partitioning vs Bucketing', minutes=7, cards=[
    comparison(
        table(['Aspect', 'Partitioning', 'Bucketing'], [
            ['Creates', 'Directories, one per value', 'A fixed number of files'],
            ['Number of units', 'Grows with distinct values', 'Fixed at CREATE time'],
            ['Best for column', 'Low/moderate cardinality, used in filters (date, country)', 'High cardinality, used in joins/lookups (id)'],
            ['Main benefit', 'Partition pruning (skip folders)', 'Bucket/SMB joins, sampling, even file sizes'],
            ['Syntax', '<code>PARTITIONED BY (dt STRING)</code>', '<code>CLUSTERED BY (id) INTO 32 BUCKETS</code>'],
            ['Column stored in files?', 'No (folder name)', 'Yes'],
            ['Risk', 'Too many partitions / small files', 'Wrong bucket count; writes that ignore bucketing'],
        ]),
        tags('Partitioning', 'Bucketing', 'Cardinality', 'Design'),
    ),
    analogy('A school file room: <strong>partitioning</strong> is one shelf per academic year (you go straight to 2026). <strong>Bucketing</strong> '
            'is, within each shelf, exactly 10 boxes by the last digit of the roll number: a fixed number of boxes however many students join.'),
    part_vs_bucket_anim(),
    real_world(
        scenario('Combined design',
                 p('<code>exam_attempts</code>: <code>PARTITIONED BY (exam_date)</code> because reports filter by date, and '
                   '<code>CLUSTERED BY (roll_no) INTO 32 BUCKETS</code> because it is joined with <code>students</code> on roll_no. '
                   'Each date folder holds 32 bucket files.')),
    ),
    example(
        hql('''
CREATE TABLE exam_attempts (roll_no INT, subject STRING, marks INT)
PARTITIONED BY (exam_date STRING)
CLUSTERED BY (roll_no) INTO 2 BUCKETS
STORED AS ORC;

INSERT INTO exam_attempts PARTITION (exam_date) VALUES
  (2401,'SQL',78,'2026-10-12'), (2402,'SQL',91,'2026-10-12'),
  (2401,'Spark',80,'2026-10-13'), (2403,'Spark',84,'2026-10-13');

dfs -ls -R /user/hive/warehouse/cdac.db/exam_attempts;
'''),
        note('Each date folder contains bucket files. Buckets that received no rows have no file here; Hive normally creates all bucket files, empty ones included.', 'Read the output'),
        title='Example: Partitioned AND Bucketed'),
    steps(
        ('Partition by the main filter column', 'Usually a date.'),
        ('Bucket by the main join key', 'Same column and compatible bucket counts in tables that are joined.'),
        ('Size check', 'Partitions of hundreds of MB+, bucket files of 128 MB–1 GB.'),
        title='Steps to Decide'),
    crossq(
        ('Why not partition by roll_no?', '100,000 students → 100,000 folders and tiny files; the metastore and NameNode suffer, and queries get slower. Bucketing gives the same "same key together" property with a fixed number of files.'),
    ),
]),

# ------------------------------------------------------------------ 21
Q('What are bucket map join and sort-merge-bucket (SMB) join?', 'Bucket Map & SMB Joins', minutes=8, cards=[
    definition(
        defbox('<strong>Bucket map join</strong>: when both tables are bucketed on the join key and one table\'s bucket count is a multiple of '
               'the other\'s, each mapper loads only the <em>matching bucket</em> of the smaller table into memory instead of the whole table.',
               '<strong>SMB join</strong>: when both tables are bucketed <strong>and sorted</strong> on the join key with the same number of buckets, '
               'each task merges two sorted bucket files, a streaming merge join needing very little memory, with no shuffle.'),
        tags('Bucket Map Join', 'SMB Join', 'Sort-Merge-Bucket', 'hive.optimize.bucketmapjoin', 'Join Optimization'),
    ),
    analogy('Two registers, both organised into 4 sections by roll mod 4 and sorted inside each section. To match every student with their '
            'marks, four clerks work in parallel, each taking section <em>k</em> of both registers and running a finger down both lists at '
            'once. Nobody needs to carry pages between sections.'),
    bucket_join(),
    real_world(
        scenario('Customer 360 in a bank',
                 p('Accounts (300 M rows) and transactions (20 B rows) are both bucketed and sorted by <code>customer_id</code> into 256 buckets. '
                   'The daily join changed from a 2-hour shuffle join to a 25-minute SMB join.')),
    ),
    example(
        hql('''
CREATE TABLE stu (roll_no INT, name STRING) CLUSTERED BY (roll_no) SORTED BY (roll_no) INTO 4 BUCKETS STORED AS ORC;
CREATE TABLE mrk (roll_no INT, marks INT)   CLUSTERED BY (roll_no) SORTED BY (roll_no) INTO 4 BUCKETS STORED AS ORC;
INSERT INTO stu VALUES (2401,'Anuj'),(2402,'Vineeta'),(2403,'Aarshvi'),(2404,'Rohit');
INSERT INTO mrk VALUES (2401,78),(2402,91),(2403,84),(2404,66);

SELECT s.roll_no, s.name, m.marks FROM stu s JOIN mrk m ON s.roll_no = m.roll_no ORDER BY s.roll_no;
'''),
        hq('''
SET hive.auto.convert.sortmerge.join = true;
SET hive.optimize.bucketmapjoin = true;
SET hive.optimize.bucketmapjoin.sortedmerge = true;
SET hive.auto.convert.sortmerge.join.noconditionaltask = true;

EXPLAIN SELECT s.name, m.marks FROM stu s JOIN mrk m ON s.roll_no = m.roll_no;
-- Hive's plan shows "Sorted Merge Bucket Map Join Operator" instead of a shuffle join
''', 'Enabling SMB join in Hive'),
        title='Example'),
    steps(
        ('Bucket both tables on the join key', 'Same column and type.'),
        ('Use the same (or multiple) bucket counts', 'Same count for SMB; one a multiple of the other for bucket map join.'),
        ('Sort the buckets', '<code>SORTED BY (key)</code> for SMB.'),
        ('Load with INSERT ... SELECT', 'So files are really bucketed and sorted.'),
        ('Enable the settings and check EXPLAIN', 'Look for the SMB / bucket map join operator.'),
        title='Steps to Get an SMB Join'),
    crossq(
        ('Map join vs bucket map join?', 'A map join loads the <em>entire</em> small table into every mapper. A bucket map join loads only the matching bucket, so the "small" table can be much larger.'),
        ('Why must keys be the same type?', 'The bucket is computed from the hash of the value; INT 2401 and STRING "2401" hash differently and would be in different buckets.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('How do you sample data in Hive?', 'Sampling (TABLESAMPLE)', minutes=6, cards=[
    definition(
        table(['Method', 'Syntax', 'Notes'], [
            ['Bucket sampling', '<code>TABLESAMPLE(BUCKET 1 OUT OF 4 ON roll_no)</code>', 'On a table bucketed by roll_no into 4, reads only bucket 1 file: fast and repeatable'],
            ['Random bucket sampling', '<code>TABLESAMPLE(BUCKET 1 OUT OF 4 ON rand())</code>', 'Scans everything, random subset'],
            ['Block / percent sampling', '<code>TABLESAMPLE(10 PERCENT)</code>', 'Approximate, by input splits'],
            ['Row count', '<code>TABLESAMPLE(100 ROWS)</code>', 'Per input split'],
            ['Simple', '<code>LIMIT n</code> / <code>ORDER BY rand() LIMIT n</code>', 'LIMIT is not random; rand() ordering is expensive'],
        ]),
        tags('TABLESAMPLE', 'Sampling', 'BUCKET x OUT OF y', 'PERCENT', 'rand()'),
    ),
    analogy('Tasting a pot of biryani: you do not eat it all, you take <strong>one spoonful from one part</strong> (one bucket). If the pot was '
            'mixed evenly (rows hashed into buckets), that spoon is representative.'),
    sampling_anim(),
    real_world(
        scenario('Developing a query on a 10 TB table',
                 p('While writing and testing a new transformation, the developer runs it on <code>TABLESAMPLE(BUCKET 1 OUT OF 64 ON customer_id)</code>, '
                   'about 1.5% of the data, consistently the same customers each time, so results can be compared between runs.')),
    ),
    example(
        hql('''
CREATE TABLE marks (roll_no INT, marks INT) STORED AS ORC;
INSERT INTO marks SELECT 2400 + id, CAST(40 + (id * 37) % 60 AS INT) FROM range(1, 101) AS t(id);

SELECT COUNT(*) AS sampled_rows, ROUND(AVG(marks), 1) AS avg_marks FROM marks TABLESAMPLE (BUCKET 1 OUT OF 4);
SELECT COUNT(*) AS all_rows,     ROUND(AVG(marks), 1) AS avg_marks FROM marks;
SELECT * FROM marks TABLESAMPLE (5 ROWS);
'''),
        hq('''
-- Hive: sample bucket 1 of 4 of a table bucketed by roll_no -> reads one file only
SELECT * FROM students_b TABLESAMPLE(BUCKET 1 OUT OF 4 ON roll_no);
''', 'Bucket sampling on the bucket column (Hive)'),
        title='Example'),
    steps(
        ('For repeatable samples, bucket the table', 'On the column you want to sample by.'),
        ('Use TABLESAMPLE on that column', '<code>TABLESAMPLE(BUCKET 1 OUT OF n ON col)</code> reads 1/n of the files.'),
        ('Compare with the full table', 'Check that averages and distributions are similar before trusting the sample.'),
        title='Steps to Sample'),
    crossq(
        ('Why is <code>LIMIT 100</code> not a good sample?', 'It returns the first rows Hive happens to read, usually from one file, often all from the same date or source: biased.'),
    ),
]),
])
