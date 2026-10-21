from build import *
from hive.anims import *
from hive.runner import hql, hq, sh, datafile

STUDENTS = '''
CREATE TABLE students (roll_no INT, name STRING, course STRING, marks INT) STORED AS ORC;
INSERT INTO students VALUES
  (2401,'Anuj','PG-DBDA',78), (2402,'Vineeta','PG-DBDA',91), (2403,'Aarshvi','PG-DAC',84),
  (2404,'Rohit','PG-DAC',66), (2405,'Meera','PG-DBDA',78), (2406,'Kabir','PG-DAI',72),
  (2407,'Sana','PG-DAI',88), (2408,'Dev','PG-DAC',59);
'''

SECTION = dict(level='intermediate', title='Querying: Sorting, Joins, Windows & UDFs', questions=[

# ------------------------------------------------------------------ 23
Q('What is the difference between ORDER BY, SORT BY, DISTRIBUTE BY and CLUSTER BY?', 'ORDER / SORT / DISTRIBUTE / CLUSTER BY', minutes=9, cards=[
    definition(
        table(['Clause', 'What it guarantees', 'Reducers'], [
            ['<code>ORDER BY</code>', '<strong>Total order</strong> of the whole result', 'Forces 1 reducer (bottleneck on big data)'],
            ['<code>SORT BY</code>', 'Order <strong>within each reducer</strong> only', 'Many'],
            ['<code>DISTRIBUTE BY col</code>', 'Rows with the same col go to the <strong>same reducer</strong>; no sorting', 'Many'],
            ['<code>CLUSTER BY col</code>', '<code>DISTRIBUTE BY col SORT BY col</code> (ascending only)', 'Many'],
        ]),
        tags('ORDER BY', 'SORT BY', 'DISTRIBUTE BY', 'CLUSTER BY', 'Reducer', 'Total Order'),
    ),
    analogy('Arranging 10,000 answer sheets: <strong>ORDER BY</strong> is one teacher sorting the entire pile alone (perfect order, very slow). '
            '<strong>SORT BY</strong> is four teachers each sorting the pile they happened to get (four sorted piles). <strong>DISTRIBUTE BY course</strong> '
            'is handing each teacher all sheets of one course (grouped, not sorted). <strong>CLUSTER BY course</strong> is both: each teacher gets '
            'whole courses and sorts their pile.'),
    sort_by_anim(),
    real_world(
        scenario('Writing one sorted file per course',
                 p('A downstream system wants one file per course with students sorted by roll number. '
                   '<code>DISTRIBUTE BY course SORT BY course, roll_no</code> sends each course to one reducer and sorts inside it, in '
                   'parallel. Using ORDER BY would push all rows through a single reducer.')),
    ),
    example(
        hql('''
SET spark.sql.shuffle.partitions = 2;      -- like mapreduce.job.reduces = 2 in Hive

-- spark_partition_id() in the outer query shows which "reducer" holds each row
SELECT spark_partition_id() AS reducer, name, marks
FROM (SELECT name, marks FROM students SORT BY marks) t;

SELECT spark_partition_id() AS reducer, course, name
FROM (SELECT course, name FROM students DISTRIBUTE BY course) t;

SELECT spark_partition_id() AS reducer, course, name
FROM (SELECT course, name FROM students CLUSTER BY course) t;

SELECT name, marks FROM students ORDER BY marks DESC LIMIT 3;
''', setup=STUDENTS),
        note('With <code>SORT BY</code> each reducer\'s rows are sorted but the two lists overlap; there is no global order. With '
             '<code>DISTRIBUTE BY</code> / <code>CLUSTER BY</code> every course is entirely on one reducer.', 'Read the output'),
        title='Example: See the Reducers'),
    steps(
        ('Need one globally sorted result?', 'Use <code>ORDER BY ... LIMIT n</code> (strict mode requires LIMIT).'),
        ('Need sorted output per key, at scale?', '<code>DISTRIBUTE BY key SORT BY key, other</code>.'),
        ('Need records grouped per file/reducer only?', '<code>DISTRIBUTE BY key</code> (e.g. before writing dynamic partitions).'),
        ('Set the reducer count if needed', '<code>SET mapreduce.job.reduces=n;</code> (Hive on MR/Tez).'),
        title='Steps to Choose'),
    crossq(
        ('Why does Hive strict mode reject <code>ORDER BY</code> without LIMIT?', 'Sorting billions of rows through one reducer can run for hours or fail; LIMIT lets each mapper keep only its top N.'),
        ('Can CLUSTER BY sort descending?', 'No. Use <code>DISTRIBUTE BY col SORT BY col DESC</code>.'),
        ('Is <code>CLUSTER BY</code> in a SELECT the same as <code>CLUSTERED BY</code> in CREATE TABLE?', 'No. CLUSTERED BY defines table bucketing; CLUSTER BY controls how one query\'s rows are distributed and sorted.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('What types of joins does Hive support? What is a map join?', 'Joins & Map Join', minutes=10, cards=[
    definition(
        table(['Join', 'Returns'], [
            ['<code>[INNER] JOIN</code>', 'Matching rows only'],
            ['<code>LEFT / RIGHT / FULL OUTER JOIN</code>', 'All rows of one/both sides, NULLs where no match'],
            ['<code>LEFT SEMI JOIN</code>', 'Left rows that have a match (like <code>WHERE EXISTS</code>); only left columns'],
            ['<code>LEFT ANTI JOIN</code> (Hive 3.1+ / Spark)', 'Left rows with no match (like <code>NOT EXISTS</code>)'],
            ['<code>CROSS JOIN</code>', 'Cartesian product'],
        ]),
        defbox('Join <strong>strategies</strong>: a <strong>shuffle (common/reduce-side) join</strong> sends both tables through the shuffle by join '
               'key; a <strong>map join</strong> loads the small table into memory on every mapper and joins without a shuffle; bucket map and SMB '
               'joins use bucketing; a <strong>skew join</strong> handles hot keys separately.'),
        tags('INNER JOIN', 'LEFT SEMI JOIN', 'Map Join', 'Broadcast', 'Shuffle Join', 'hive.auto.convert.join'),
    ),
    analogy('A <strong>map join</strong> is giving every exam invigilator a <strong>printed copy of the small seating chart</strong>: each one '
            'checks the students in their own hall without phoning a central office. A shuffle join is every invigilator sending all their '
            'students\' slips to a central office that sorts and matches them.'),
    map_join_anim(),
    real_world(
        scenario('Fact table + dimension table',
                 p('Daily <code>enrolment_events</code> (hundreds of millions of rows) are joined to <code>courses</code> (40 rows) and '
                   '<code>centres</code> (12 rows). Both dimensions are tiny, so Hive converts the joins to map joins automatically and the '
                   'query runs as a single map-only stage.')),
    ),
    example(
        hql('''
CREATE TABLE courses (course STRING, duration_months INT) STORED AS ORC;
INSERT INTO courses VALUES ('PG-DBDA', 6), ('PG-DAC', 6), ('PG-DESD', 6);

-- INNER: students whose course exists in courses
SELECT s.name, s.course, c.duration_months
FROM students s JOIN courses c ON s.course = c.course ORDER BY s.name LIMIT 4;

-- LEFT OUTER: keep all students, NULL if course not found (PG-DAI)
SELECT s.name, s.course, c.duration_months
FROM students s LEFT JOIN courses c ON s.course = c.course WHERE c.course IS NULL;

-- LEFT SEMI: courses that have at least one student
SELECT c.course FROM courses c LEFT SEMI JOIN students s ON c.course = s.course ORDER BY c.course;

-- Map join hint (Hive converts automatically when the table is small)
EXPLAIN SELECT /*+ MAPJOIN(c) */ s.name, c.duration_months
FROM students s JOIN courses c ON s.course = c.course;
''', setup=STUDENTS),
        note('The plan shows <code>BroadcastHashJoin ... BuildRight</code>: the small <code>courses</code> table is broadcast to every task and '
             'no shuffle of <code>students</code> happens. In Hive the plan shows <code>Map Join Operator</code> inside a single map vertex.', 'Read the plan'),
        title='Example: Join Types and a Map Join'),
    steps(
        ('Put the big table where Hive expects it', 'With old Hive versions, the largest table should be last (it is streamed); modern CBO reorders automatically.'),
        ('Keep auto conversion on', '<code>SET hive.auto.convert.join=true;</code> (default).'),
        ('Tune the threshold', '<code>hive.auto.convert.join.noconditionaltask.size</code> (bytes of small tables that may be held in memory).'),
        ('Check EXPLAIN', 'Look for Map Join Operator; if missing, check table statistics (<code>ANALYZE TABLE ... COMPUTE STATISTICS</code>).'),
        title='Steps to Get a Map Join'),
    crossq(
        ('Why can a map join fail with OutOfMemory?', 'The "small" table was larger than estimated (missing or stale stats, or a filter that did not reduce it). Hive builds the hash table in memory; refresh stats or lower the threshold.'),
        ('LEFT SEMI JOIN vs INNER JOIN?', 'SEMI returns each left row at most once and only left columns; INNER can duplicate left rows when there are several matches.'),
        ('Does Hive support non-equi joins?', 'Since Hive 2.2, conditions such as <code>a.x BETWEEN b.lo AND b.hi</code> are allowed in ON, but they are expensive (often a cross product with a filter).'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('Explain window functions in Hive with examples.', 'Window Functions', minutes=10, cards=[
    definition(
        defbox('A <strong>window function</strong> computes a value for each row using a set of related rows (its <strong>window</strong>), '
               'defined with <code>OVER (PARTITION BY ... ORDER BY ... [ROWS/RANGE frame])</code>. Unlike GROUP BY, rows are not collapsed.'),
        table(['Family', 'Functions'], [
            ['Ranking', '<code>ROW_NUMBER()</code>, <code>RANK()</code>, <code>DENSE_RANK()</code>, <code>NTILE(n)</code>, <code>PERCENT_RANK()</code>, <code>CUME_DIST()</code>'],
            ['Offset', '<code>LAG(col, n)</code>, <code>LEAD(col, n)</code>, <code>FIRST_VALUE</code>, <code>LAST_VALUE</code>'],
            ['Aggregate', '<code>SUM</code>, <code>AVG</code>, <code>COUNT</code>, <code>MIN</code>, <code>MAX</code> with OVER (running totals, moving averages)'],
        ]),
        tags('Window Functions', 'OVER', 'PARTITION BY', 'RANK', 'DENSE_RANK', 'ROW_NUMBER', 'LAG', 'LEAD'),
    ),
    analogy('Each student\'s row gets a <strong>rank badge</strong> computed by looking only at classmates in the <strong>same course</strong> '
            '(the window), while everybody stays in the hall. GROUP BY would instead send everyone home and keep just one summary card per course.'),
    window_anim(),
    real_world(
        scenario('Common uses',
                 ul('Top 3 students per course for the merit list (<code>DENSE_RANK</code>).',
                    'Latest record per student from a change log (<code>ROW_NUMBER() ... = 1</code>): deduplication.',
                    'Change in marks since the previous exam (<code>LAG</code>).',
                    'Running total of fee collection by date (<code>SUM ... OVER (ORDER BY dt)</code>).')),
    ),
    example(
        hql('''
SELECT course, name, marks,
       RANK()       OVER (PARTITION BY course ORDER BY marks DESC) AS rnk,
       DENSE_RANK() OVER (PARTITION BY course ORDER BY marks DESC) AS dense_rnk,
       ROW_NUMBER() OVER (PARTITION BY course ORDER BY marks DESC, roll_no) AS row_num,
       ROUND(AVG(marks) OVER (PARTITION BY course), 1)              AS course_avg
FROM students
ORDER BY course, rnk, roll_no;
''', setup=STUDENTS),
        hql('''
-- Top 2 per course (merit list)
SELECT course, name, marks FROM (
  SELECT course, name, marks, DENSE_RANK() OVER (PARTITION BY course ORDER BY marks DESC) AS r
  FROM students) t
WHERE r <= 2 ORDER BY course, marks DESC;

-- Marks change between exams with LAG
CREATE TABLE exam_hist (roll_no INT, exam STRING, marks INT) STORED AS ORC;
INSERT INTO exam_hist VALUES (2401,'2026-08',65),(2401,'2026-09',72),(2401,'2026-10',78),
                             (2402,'2026-08',88),(2402,'2026-09',85),(2402,'2026-10',91);
SELECT roll_no, exam, marks,
       marks - LAG(marks) OVER (PARTITION BY roll_no ORDER BY exam) AS change,
       SUM(marks) OVER (PARTITION BY roll_no ORDER BY exam ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM exam_hist ORDER BY roll_no, exam;
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Decide the window', 'PARTITION BY = the group (course, student); ORDER BY = the sequence (marks, date).'),
        ('Pick the function', 'Ranking, LAG/LEAD or an aggregate.'),
        ('Add a frame if needed', '<code>ROWS BETWEEN 6 PRECEDING AND CURRENT ROW</code> for a 7-row moving window.'),
        ('Filter in an outer query', 'Window results cannot be used in WHERE of the same SELECT: wrap in a subquery (Hive 4 adds <code>QUALIFY</code>).'),
        title='Steps to Write a Window Query'),
    crossq(
        ('RANK vs DENSE_RANK vs ROW_NUMBER for marks 91, 78, 78, 72?', 'RANK: 1, 2, 2, 4. DENSE_RANK: 1, 2, 2, 3. ROW_NUMBER: 1, 2, 3, 4 (ties broken arbitrarily unless you add a tie-breaker).'),
        ('How do you remove duplicates keeping the latest row?', '<code>ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC) = 1</code> in a subquery.'),
        ('What is the default frame with ORDER BY?', '<code>RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW</code>, which is why <code>LAST_VALUE</code> often surprises people: specify <code>ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING</code>.'),
    ),
]),

# ------------------------------------------------------------------ 26
Q('How do you work with arrays and nested data? Explain LATERAL VIEW and explode().', 'LATERAL VIEW & explode()', minutes=8, cards=[
    definition(
        defbox('<code>explode(array)</code> and <code>explode(map)</code> are <strong>UDTFs</strong> (table-generating functions) that turn one '
               'value into several rows. <code>LATERAL VIEW</code> attaches those generated rows to the original row, so other columns can be '
               'selected alongside. <code>posexplode</code> also returns the position; <code>LATERAL VIEW OUTER</code> keeps rows with empty arrays.',
               'The reverse (rows → array) is done with <code>collect_list()</code> (keeps duplicates) or <code>collect_set()</code> (distinct).'),
        tags('LATERAL VIEW', 'explode', 'posexplode', 'UDTF', 'collect_list', 'collect_set'),
    ),
    analogy('A student\'s profile card lists skills in one box: "SQL, Spark". <code>explode</code> is photocopying the card once per skill and '
            'highlighting a different skill on each copy, so you can count how many students know Spark. <code>collect_set</code> is stapling the '
            'copies back into one card.'),
    explode_anim(),
    real_world(
        scenario('Skill demand vs supply',
                 p('Placement drives list required skills as arrays; student profiles list skills as arrays. Exploding both and joining on the '
                   'skill shows which in-demand skills students lack, information that guided which modules to strengthen.')),
    ),
    example(
        hql('''
CREATE TABLE profiles (name STRING, skills ARRAY<STRING>, marks MAP<STRING, INT>) STORED AS ORC;
INSERT INTO profiles SELECT 'Anuj', array('sql','spark'), map('SQL',82,'Spark',77);
INSERT INTO profiles SELECT 'Vineeta', array('python','hive','kafka'), map('SQL',91,'Spark',88);
INSERT INTO profiles SELECT 'Rohit', array(), map('SQL',66);

-- one row per skill
SELECT p.name, s.skill
FROM profiles p LATERAL VIEW explode(p.skills) s AS skill;

-- OUTER keeps Rohit (empty array) with NULL
SELECT p.name, s.skill
FROM profiles p LATERAL VIEW OUTER explode(p.skills) s AS skill WHERE p.name = 'Rohit';

-- explode a MAP into key/value rows
SELECT p.name, m.subject, m.score
FROM profiles p LATERAL VIEW explode(p.marks) m AS subject, score ORDER BY p.name, m.subject;

-- and back again: rows -> array
SELECT s.skill, collect_list(p.name) AS students
FROM profiles p LATERAL VIEW explode(p.skills) s AS skill GROUP BY s.skill ORDER BY s.skill;
'''),
        title='Example'),
    steps(
        ('Identify the array/map column', 'From JSON or a complex-typed table.'),
        ('Add LATERAL VIEW', '<code>FROM t LATERAL VIEW explode(t.arr) alias AS col</code> (two names for a map: key, value).'),
        ('Use OUTER if rows must not disappear', '<code>LATERAL VIEW OUTER explode(...)</code>.'),
        ('Aggregate back if needed', '<code>collect_list</code> / <code>collect_set</code> with GROUP BY.'),
        title='Steps to Flatten Nested Data'),
    crossq(
        ('Why can\'t you write <code>SELECT name, explode(skills) FROM profiles</code>?', 'In Hive a UDTF must be the only expression in the SELECT. LATERAL VIEW is the way to combine it with other columns.'),
        ('How do you parse a JSON string column?', '<code>get_json_object(col, \'$.a.b\')</code> for one field, <code>json_tuple(col, \'a\', \'b\')</code> (a UDTF, often with LATERAL VIEW) for several.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What are UDF, UDAF and UDTF? How do you write a custom function?', 'UDF / UDAF / UDTF', minutes=9, cards=[
    definition(
        table(['Type', 'Rows in → rows out', 'Built-in examples'], [
            ['UDF (User-Defined Function)', '1 → 1', '<code>upper</code>, <code>concat</code>, <code>round</code>, <code>to_date</code>'],
            ['UDAF (User-Defined Aggregate Function)', 'many → 1', '<code>sum</code>, <code>avg</code>, <code>collect_set</code>, <code>percentile</code>'],
            ['UDTF (User-Defined Table-generating Function)', '1 → many', '<code>explode</code>, <code>posexplode</code>, <code>json_tuple</code>, <code>stack</code>'],
        ]),
        defbox('Custom functions are written in Java (extend <code>GenericUDF</code>, <code>AbstractGenericUDAFResolver</code> or '
               '<code>GenericUDTF</code>), packaged as a jar and registered with <code>CREATE FUNCTION</code>. For Python logic, Hive offers '
               '<code>TRANSFORM ... USING \'script\'</code>, which streams rows through the script\'s stdin/stdout.'),
        tags('UDF', 'UDAF', 'UDTF', 'GenericUDF', 'TRANSFORM', 'CREATE FUNCTION'),
    ),
    analogy('A UDF is a <strong>stamp</strong> applied to each sheet (one in, one out). A UDAF is a <strong>calculator</strong> totalling a whole '
            'stack into one number. A UDTF is a <strong>photocopier</strong> that turns one sheet into several.'),
    udf_types_anim(),
    real_world(
        scenario('Masking phone numbers',
                 p('Reports must not show full phone numbers. A small Java UDF <code>mask_phone(phone)</code> returning '
                   '<code>98XXXXXX01</code> is registered once as a permanent function and used in all reporting views.')),
    ),
    example(
        code('''
package in.cdac.hive;

import org.apache.hadoop.hive.ql.exec.UDF;
import org.apache.hadoop.io.Text;

// Simple (legacy-style) UDF: keep first 2 and last 2 digits
public class MaskPhone extends UDF {
    public Text evaluate(Text phone) {
        if (phone == null) return null;
        String p = phone.toString();
        if (p.length() < 5) return phone;
        return new Text(p.substring(0, 2) + "X".repeat(p.length() - 4) + p.substring(p.length() - 2));
    }
}
''', 'MaskPhone.java', 'fa-brands fa-java'),
        hq('''
-- jar copied to HDFS, then:
CREATE FUNCTION cdac.mask_phone AS 'in.cdac.hive.MaskPhone'
USING JAR 'hdfs:///apps/hive/udfs/cdac-udfs-1.0.jar';

SELECT name, cdac.mask_phone(phone) FROM students;
-- TEMPORARY functions (ADD JAR + CREATE TEMPORARY FUNCTION) last only for the session
''', 'Register and use (Hive)'),
        title='Example: Java UDF'),
    example(
        datafile('/data/scripts/grade.py', '''
import sys
# Hive sends each row as tab-separated text on stdin
for line in sys.stdin:
    roll, name, marks = line.rstrip("\\n").split("\\t")
    m = int(marks)
    grade = "A" if m >= 85 else "B" if m >= 70 else "C"
    print(f"{roll}\\t{name}\\t{grade}")
'''),
        hql('''
SELECT TRANSFORM (roll_no, name, marks)
       USING 'python3 /data/scripts/grade.py'
       AS (roll_no INT, name STRING, grade STRING)
FROM students
ORDER BY roll_no;
''', setup=STUDENTS, files={'scripts/grade.py': 'import sys\nfor line in sys.stdin:\n    roll, name, marks = line.rstrip("\\n").split("\\t")\n    m = int(marks)\n    grade = "A" if m >= 85 else "B" if m >= 70 else "C"\n    print(f"{roll}\\t{name}\\t{grade}")\n'}),
        note('In Hive, ship the script to every node first with <code>ADD FILE hdfs:///apps/scripts/grade.py;</code> and use <code>USING \'python3 grade.py\'</code>.', 'On a cluster'),
        title='Example: Python Logic With TRANSFORM'),
    steps(
        ('Check built-ins first', '<code>SHOW FUNCTIONS;</code> and <code>DESCRIBE FUNCTION EXTENDED name;</code>; Hive has hundreds.'),
        ('Write the class', 'Extend <code>GenericUDF</code> (preferred: handles types, NULLs and complex types) and implement <code>initialize</code>, <code>evaluate</code>, <code>getDisplayString</code>.'),
        ('Build the jar', '<code>mvn package</code> with <code>hive-exec</code> as a <em>provided</em> dependency.'),
        ('Upload and register', '<code>hdfs dfs -put</code> the jar; <code>CREATE FUNCTION db.fn AS \'class\' USING JAR \'hdfs:///...\';</code>'),
        ('Test', 'Run on a few rows including NULLs and edge cases.'),
        title='Steps to Create a Permanent UDF'),
    crossq(
        ('Temporary vs permanent function?', 'TEMPORARY exists only in the current session; permanent functions are stored in the metastore with their jar location and are available in every session (and to HiveServer2 users).'),
        ('Why is TRANSFORM slower than a Java UDF?', 'Rows are serialised to text, piped to an external process and parsed back. A Java UDF runs inside the JVM on Hive\'s objects.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What are GROUPING SETS, ROLLUP and CUBE?', 'GROUPING SETS, ROLLUP, CUBE', minutes=7, cards=[
    definition(
        defbox('They compute <strong>several GROUP BY levels in one query</strong> (one scan of the data):'),
        table(['Clause', 'Groups produced for (a, b)'], [
            ['<code>GROUPING SETS ((a,b),(a),())</code>', 'Exactly the sets you list'],
            ['<code>WITH ROLLUP</code>', '(a,b), (a), () : hierarchical subtotals and a grand total'],
            ['<code>WITH CUBE</code>', '(a,b), (a), (b), () : all combinations'],
        ]),
        defbox('Columns not part of a given grouping are NULL in that row; <code>GROUPING__ID</code> / <code>grouping(col)</code> tells subtotal rows apart from real NULLs.'),
        tags('GROUPING SETS', 'ROLLUP', 'CUBE', 'Subtotals', 'GROUPING__ID'),
    ),
    analogy('A fee report with <strong>subtotals per course, per centre, and a grand total</strong> at the bottom. Instead of running three '
            'separate summaries and stitching them together, ROLLUP prints all of them in one pass.'),
    rollup_anim(),
    real_world(
        scenario('One query for a management dashboard',
                 p('Enrolment counts by centre and course, by centre only, and overall feed three dashboard tiles. A single ROLLUP query '
                   'replaces three UNION ALL-ed GROUP BY queries and scans the table once instead of three times.')),
    ),
    example(
        hql('''
CREATE TABLE enrol (centre STRING, course STRING, students INT) STORED AS ORC;
INSERT INTO enrol VALUES ('Kharghar','PG-DBDA',60), ('Kharghar','PG-DAC',120),
                         ('Juhu','PG-DAC',90), ('Juhu','PG-DAI',40);

SELECT centre, course, SUM(students) AS total
FROM enrol
GROUP BY centre, course WITH ROLLUP
ORDER BY centre NULLS LAST, course NULLS LAST;
'''),
        title='Example: Subtotals and Grand Total'),
    steps(
        ('List the levels you need', 'e.g. centre+course, centre, total.'),
        ('Pick the clause', 'Hierarchical → ROLLUP; all combinations → CUBE; specific → GROUPING SETS.'),
        ('Label subtotal rows', '<code>COALESCE(centre, \'ALL CENTRES\')</code> or use <code>grouping(centre)</code>.'),
        title='Steps'),
    crossq(
        ('How many groups does CUBE on 3 columns produce?', '2³ = 8 grouping combinations.'),
    ),
]),
])
