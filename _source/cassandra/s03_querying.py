from build import *
from cassandra.anims import *
from cassandra.runner import cql, cq, sh

MARKS = '''
CREATE TABLE marks_by_student (
  roll_no int, exam_date date, module text, marks int, centre text,
  PRIMARY KEY ((roll_no), exam_date, module)
) WITH CLUSTERING ORDER BY (exam_date DESC, module ASC);
INSERT INTO marks_by_student (roll_no, exam_date, module, marks, centre) VALUES (2401, '2026-09-10', 'SQL', 78, 'Kharghar');
INSERT INTO marks_by_student (roll_no, exam_date, module, marks, centre) VALUES (2401, '2026-10-05', 'Spark', 84, 'Kharghar');
INSERT INTO marks_by_student (roll_no, exam_date, module, marks, centre) VALUES (2401, '2026-10-12', 'Python', 79, 'Kharghar');
INSERT INTO marks_by_student (roll_no, exam_date, module, marks, centre) VALUES (2402, '2026-09-10', 'SQL', 91, 'Juhu');
INSERT INTO marks_by_student (roll_no, exam_date, module, marks, centre) VALUES (2402, '2026-10-05', 'Spark', 88, 'Juhu');
INSERT INTO marks_by_student (roll_no, exam_date, module, marks, centre) VALUES (2403, '2026-09-10', 'SQL', 66, 'Kharghar');
'''

SECTION = dict(level='intermediate', title='Querying with CQL', questions=[

# ------------------------------------------------------------------ 11
Q('Why can\'t you put any column in the WHERE clause in Cassandra? Explain the restriction rules.', 'WHERE Clause Rules', minutes=10, cards=[
    definition(
        defbox('A Cassandra query must be answerable by reading <strong>one contiguous slice of known partitions</strong>. Therefore:'),
        ul('<strong>Partition key</strong>: restrict <strong>all</strong> its columns with <code>=</code> or <code>IN</code> (or use '
           '<code>token()</code> ranges for full scans). Ranges like <code>roll_no &gt; 2400</code> are not allowed on the partition key.',
           '<strong>Clustering columns</strong>: restrict them <strong>left to right</strong> without gaps. All but the last restricted one must use '
           '<code>=</code> (or IN); the last may be a range (<code>&gt;</code>, <code>&lt;=</code>…).',
           '<strong>Regular columns</strong>: cannot be restricted unless they have an index (SAI / secondary index) or you add '
           '<code>ALLOW FILTERING</code>.',
           'Cassandra rejects queries that break these rules with a clear error instead of silently running a slow scan.'),
        tags('WHERE restrictions', 'Partition key = / IN', 'Clustering prefix', 'Range on last column', 'token()'),
    ),
    analogy('A <strong>phone directory sorted by city, then surname, then first name</strong>. "Pune, Sharma, all first names from A to M" is one '
            'contiguous block of pages. "Everyone called Rahul in any city" would mean reading the whole book.'),
    where_rules_anim(),
    real_world(
        scenario('A rejected query is a design signal',
                 p('A developer needs "all students of the Kharghar centre". <code>WHERE centre = \'Kharghar\'</code> is rejected on '
                   '<code>marks_by_student</code>. The right fix is not ALLOW FILTERING but a new table <code>students_by_centre</code> partitioned by '
                   'centre, written at the same time as the other tables.')),
    ),
    example(
        cql('''
-- ✓ full partition key + clustering prefix with a range on the last column
SELECT * FROM marks_by_student WHERE roll_no = 2401 AND exam_date >= '2026-10-01';

-- ✓ IN on the partition key
SELECT roll_no, module, marks FROM marks_by_student WHERE roll_no IN (2402, 2403);

-- ✗ skips the first clustering column
SELECT * FROM marks_by_student WHERE roll_no = 2401 AND module = 'SQL';

-- ✗ range on the partition key
SELECT * FROM marks_by_student WHERE roll_no > 2401;

-- ✗ regular column without index
SELECT * FROM marks_by_student WHERE centre = 'Kharghar';

-- ✗ a range on exam_date followed by a restriction on module
SELECT * FROM marks_by_student WHERE roll_no = 2401 AND exam_date > '2026-10-01' AND module = 'Spark';
''', setup=MARKS, expect_error=True),
        title='Example: Allowed and Rejected Queries'),
    steps(
        ('Write the query you need', 'List its equality inputs, ranges and required order.'),
        ('Check against the table key', 'Equality inputs must cover the partition key; ranges must fall on the next clustering column.'),
        ('If it does not fit', 'Create a table whose key matches the query (preferred), or add an SAI index for occasional queries.'),
        ('Use ALLOW FILTERING only knowingly', 'Inside a known partition, or on small tables.'),
        title='Steps When a Query Is Rejected'),
    crossq(
        ('How do you read an entire table, e.g. for an export?', 'Page through it with token ranges: <code>WHERE token(pk) &gt; ? AND token(pk) &lt;= ?</code>, '
         'split into many ranges and read them in parallel. Tools such as the Spark Cassandra Connector and DSBulk do exactly this.'),
        ('Is IN on the partition key always fine?', 'With a few values, yes. With hundreds, one coordinator must contact many replica sets and hold all '
         'results; issue separate asynchronous queries instead.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What does ALLOW FILTERING do? Why is it considered dangerous?', 'ALLOW FILTERING', minutes=8, cards=[
    definition(
        defbox('<code>ALLOW FILTERING</code> tells Cassandra to execute a query that needs to <strong>read rows and discard those that do not match</strong>, '
               'instead of jumping straight to the requested data. Without it, Cassandra refuses with "Cannot execute this query as it might involve '
               'data filtering and thus may have unpredictable performance…".',
               'Danger: without the partition key, the query scans <strong>every partition on every node</strong>. Its cost depends on table size, not '
               'on how many rows are returned. On production tables it causes read timeouts and loads the whole cluster. It is reasonable when the '
               '<strong>partition key is given</strong> (filtering inside one partition) or the table is known to be small.'),
        tags('ALLOW FILTERING', 'Full scan', 'Unpredictable performance', 'Read timeout'),
    ),
    analogy('Asking the post office for "all letters with a red stamp". They can do it, but only by <strong>opening every sack in every sorting '
            'centre</strong>. For 12 letters you pay for a national search.'),
    allow_filtering_anim(),
    real_world(
        scenario('Fine vs dangerous',
                 ul('<strong>Fine</strong>: <code>WHERE roll_no = 2401 AND marks &gt; 80 ALLOW FILTERING</code>: reads one student\'s few rows.',
                    '<strong>Dangerous</strong>: <code>WHERE marks &gt; 80 ALLOW FILTERING</code> on 50 million rows: scans the whole table on every node.',
                    'Rule used by many teams: ALLOW FILTERING is blocked in code review unless the partition key is restricted.')),
    ),
    example(
        cql('''
SELECT * FROM marks_by_student WHERE marks > 85;

SELECT * FROM marks_by_student WHERE marks > 85 ALLOW FILTERING;

-- filtering inside one known partition: cheap
SELECT module, marks FROM marks_by_student WHERE roll_no = 2401 AND marks > 80 ALLOW FILTERING;
''', setup=MARKS, expect_error=True),
        title='Example'),
    steps(
        ('Ask: is the partition key restricted?', 'If yes, filtering is bounded by one partition: usually acceptable.'),
        ('If not, estimate table size', 'Thousands of rows: acceptable for admin tasks. Millions: no.'),
        ('Prefer a query table', 'e.g. <code>toppers_by_exam</code> with marks as a clustering column.'),
        ('Or index the column', 'SAI turns the filter into an index lookup.'),
        title='Steps'),
    crossq(
        ('Does ALLOW FILTERING read data from disk on all nodes?', 'Yes: to cover the whole token range, the coordinator must query enough replicas to '
         'read every partition, and each replica scans its data and filters it. LIMIT does not help much when matches are rare.'),
        ('Can guardrails block it?', 'Yes. Cassandra 4.1+ guardrails include <code>allow_filtering_enabled: false</code> in cassandra.yaml to reject '
         'such queries cluster-wide (superusers excepted).'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What are secondary indexes and SAI? When should you use them?', 'Secondary Indexes & SAI', minutes=10, cards=[
    definition(
        defbox('An index lets you query a <strong>non-key column</strong> without ALLOW FILTERING. Cassandra indexes are <strong>local</strong>: each '
               'node indexes only the data it stores, so a query on an indexed column without the partition key fans out to many nodes.'),
        table(['Index', 'Created with', 'Supports', 'Notes'], [
            ['Legacy secondary index (2i)', '<code>CREATE INDEX ON t (col)</code>', '= on a column; CONTAINS / CONTAINS KEY on collections', 'Stored as a hidden table per node; poor for high/low cardinality'],
            ['SASI', '<code>CREATE CUSTOM INDEX … USING \'…SASIIndex\'</code>', 'LIKE, ranges', 'Experimental, deprecated'],
            ['<strong>SAI</strong> (Storage-Attached Index, 5.0)', '<code>CREATE INDEX … USING \'sai\'</code>', '=, ranges, CONTAINS, AND of several indexed columns, vector ANN', 'Recommended; attached to SSTables/memtables, small and fast'],
        ]),
        tags('Secondary index', 'Local index', 'SAI', 'StorageAttachedIndex', 'Cardinality', 'Fan-out'),
    ),
    analogy('Each library branch keeps its <strong>own card index</strong> of the books on its shelves. To find a subject without knowing the branch, '
            'you must phone every branch and ask them to check their own index. That is fine for occasional questions, but too slow for every visitor.'),
    index_anim(),
    real_world(
        scenario('Admin search screen',
                 p('Coordinators occasionally search students by centre and marks range. Instead of maintaining another denormalised table for a '
                   'low-traffic admin screen, the team adds SAI indexes on <code>centre</code> and <code>marks</code>. Student-facing, high-traffic queries '
                   'still use purpose-built tables.')),
    ),
    example(
        cql('''
SELECT roll_no, module, marks FROM marks_by_student WHERE centre = 'Juhu';

CREATE INDEX marks_centre_sai ON marks_by_student (centre) USING 'sai';
CREATE INDEX marks_marks_sai  ON marks_by_student (marks)  USING 'sai';

SELECT roll_no, module, marks FROM marks_by_student WHERE centre = 'Juhu';

-- SAI supports ranges and AND across indexed columns
SELECT roll_no, module, marks, centre FROM marks_by_student WHERE centre = 'Kharghar' AND marks >= 79;

-- best of both: partition key + indexed column
SELECT module, marks FROM marks_by_student WHERE roll_no = 2401 AND marks > 80;
''', setup=MARKS, expect_error=True),
        title='Example'),
    steps(
        ('Confirm the query is occasional or partition-scoped', 'Index queries without a partition key contact many nodes.'),
        ('Prefer SAI on Cassandra 5.0', "<code>CREATE INDEX name ON table (col) USING 'sai';</code>"),
        ('Avoid unsuitable columns', 'Very high cardinality (email, unique IDs: use a lookup table) and frequently updated or deleted values.'),
        ('Test under load', 'Check latency with tracing and table metrics before production.'),
        title='Steps'),
    crossq(
        ('Why is a 2i on a unique column like email a bad idea?', 'Each node holds only a few matching rows, but the coordinator still has to ask nodes '
         'across the ring to find the one row. A <code>students_by_email</code> table finds it in one partition read.'),
        ('Why is a 2i on a boolean column bad?', 'Very low cardinality: each index value points to huge numbers of rows, so the query reads a large '
         'fraction of the table anyway.'),
        ('What is vector search in Cassandra 5.0?', 'A <code>vector&lt;float, n&gt;</code> column with an SAI index supports '
         '<code>ORDER BY embedding ANN OF [ … ] LIMIT k</code>, returning approximate nearest neighbours for AI/RAG applications.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do collections (set, list, map) and user-defined types work in Cassandra?', 'Collections & UDTs', minutes=9, cards=[
    definition(
        table(['Type', 'Behaviour', 'Update syntax'], [
            ['<code>set&lt;T&gt;</code>', 'Unique values, returned sorted', "<code>skills = skills + {'kafka'}</code>, <code>- {…}</code>"],
            ['<code>list&lt;T&gt;</code>', 'Ordered, allows duplicates', "<code>phones = phones + ['…']</code> (append), <code>['…'] + phones</code> (prepend)"],
            ['<code>map&lt;K,V&gt;</code>', 'Key → value pairs, sorted by key', "<code>scores['Spark'] = 84</code>, <code>DELETE scores['SQL'] FROM …</code>"],
            ['UDT (<code>CREATE TYPE</code>)', 'Named fields grouped as one value', "<code>addr = {city: 'Pune', pin: 411001}</code>"],
            ['<code>frozen&lt;…&gt;</code>', 'Stored as one immutable blob; rewritten as a whole; can be used in a primary key', '—'],
        ]),
        p('Collections are for <strong>small, bounded</strong> data that is read with its row (a few tags, phone numbers). They are always read in full; '
          'anything that can grow without limit belongs in clustering rows. Querying inside a collection needs an index with '
          '<code>CONTAINS</code> / <code>CONTAINS KEY</code>.', top=True),
        tags('set', 'list', 'map', 'UDT', 'frozen', 'CONTAINS', 'CONTAINS KEY'),
    ),
    analogy('A student\'s ID card with a <strong>small pocket</strong> for a few skill badges (set), a short list of emergency numbers (list) and a '
            'mini mark sheet (map). Handy, but you would not keep the student\'s entire exam history in that pocket.'),
    collections_anim(),
    real_world(
        scenario('Student profile',
                 p('Skills (set), phone numbers (list), latest score per module (map) and a postal address (frozen UDT) fit naturally in one profile row. '
                   'The full exam history, which keeps growing, lives in <code>marks_by_student</code> as clustering rows.')),
    ),
    example(
        cql('''
CREATE TYPE address (city text, pin int);

CREATE TABLE profiles (
  roll_no int PRIMARY KEY,
  name    text,
  skills  set<text>,
  phones  list<text>,
  scores  map<text, int>,
  addr    frozen<address>
);

INSERT INTO profiles (roll_no, name, skills, phones, scores, addr)
VALUES (2401, 'Anuj', {'sql', 'spark'}, ['9820011111'], {'SQL': 78}, {city: 'Pune', pin: 411001});

UPDATE profiles SET skills = skills + {'kafka', 'sql'},
                    phones = phones + ['9930022222'],
                    scores['Spark'] = 84
WHERE roll_no = 2401;

SELECT * FROM profiles WHERE roll_no = 2401;

UPDATE profiles SET skills = skills - {'sql'} WHERE roll_no = 2401;
DELETE scores['SQL'] FROM profiles WHERE roll_no = 2401;
SELECT skills, scores FROM profiles WHERE roll_no = 2401;

CREATE INDEX ON profiles (skills);
SELECT roll_no, name FROM profiles WHERE skills CONTAINS 'kafka';
'''),
        title='Example'),
    steps(
        ('Use a collection only for small, bounded data', 'Rough guide: well under 100 elements; Cassandra warns about large collections.'),
        ('Prefer set over list', 'Lists need read-before-write for index-based updates and are not idempotent on retry (an append may be applied twice).'),
        ('Use frozen UDTs for structured values', 'Addresses, coordinates; they can also be primary-key components.'),
        ('Index if you must query inside', '<code>CREATE INDEX ON t (col)</code> / <code>(KEYS(map))</code> / <code>(ENTRIES(map))</code>.'),
        title='Steps'),
    crossq(
        ('Why can overwriting a whole collection create tombstones?', 'Setting <code>skills = {…}</code> first writes a range tombstone deleting the old '
         'collection, then the new elements. Frequent full overwrites therefore create many tombstones; use + / - updates instead.'),
        ('frozen vs non-frozen collections?', 'Non-frozen: elements stored as separate cells, can be updated individually. Frozen: one serialized value, '
         'replaced as a whole, but usable in primary keys and cheaper to store.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do aggregates, GROUP BY, LIMIT, PER PARTITION LIMIT and DISTINCT work in CQL?', 'Aggregates & Limits', minutes=9, cards=[
    definition(
        table(['Feature', 'What it does', 'Restriction'], [
            ['<code>count(*)</code>, <code>min</code>, <code>max</code>, <code>sum</code>, <code>avg</code>', 'Aggregate on the coordinator', 'Without the partition key it scans the table and warns'],
            ['<code>GROUP BY</code>', 'One result per group', 'Only primary-key columns, in key order'],
            ['<code>LIMIT n</code>', 'At most n rows overall', '—'],
            ['<code>PER PARTITION LIMIT n</code>', 'At most n rows from each partition', 'Great for "latest N per sensor"'],
            ['<code>SELECT DISTINCT</code>', 'One row per partition', 'Only partition key and static columns'],
        ]),
        p('Aggregate results keep the column\'s type: <code>avg()</code> of an <code>int</code> column is an <strong>integer</strong> (the decimal part is '
          'dropped), and <code>sum()</code> of ints can overflow.', top=True),
        tags('count', 'avg', 'GROUP BY', 'LIMIT', 'PER PARTITION LIMIT', 'DISTINCT'),
    ),
    analogy('Counting the papers in <strong>one cabinet</strong> is quick. Counting the papers in <strong>every cabinet in every building</strong> '
            'is the same command, but takes all day, so Cassandra warns you.'),
    aggregate_anim(),
    real_world(
        scenario('Per-student statistics',
                 p('The student dashboard shows "exams taken, best mark, average". With <code>WHERE roll_no = ?</code> this is one partition and fast. '
                   'Centre-wide statistics are pre-computed by a Spark job and stored in a small summary table instead of being computed live.')),
    ),
    example(
        cql('''
SELECT count(*) AS exams, max(marks) AS best, avg(marks) AS average
FROM marks_by_student WHERE roll_no = 2401;

SELECT roll_no, count(*) AS exams, max(marks) AS best
FROM marks_by_student GROUP BY roll_no;

-- latest exam of every student
SELECT roll_no, exam_date, module, marks FROM marks_by_student PER PARTITION LIMIT 1;

SELECT DISTINCT roll_no FROM marks_by_student;

SELECT roll_no, count(*) FROM marks_by_student GROUP BY centre;
''', setup=MARKS, expect_error=True),
        p('Student 2401\'s marks are 78, 84 and 79: the true average is 80.33, but <code>avg()</code> on an <code>int</code> column returns '
          '<strong>80</strong>. Store marks as <code>double</code> or <code>decimal</code> if fractions matter.', top=True),
        title='Example'),
    steps(
        ('Aggregate within a partition when possible', 'Add the partition key to WHERE.'),
        ('Pre-compute table-wide statistics', 'Spark job or counters into a summary table.'),
        ('Use PER PARTITION LIMIT for "top N per key"', 'Rows come in clustering order, so choose the clustering order accordingly.'),
        ('Mind the data type', 'Cast or use double/decimal for averages.'),
        title='Steps'),
    crossq(
        ('Is count(*) on a big table a good idea?', 'No: it reads every partition and often times out. Keep counts with counters or compute them offline '
         'with Spark; <code>nodetool tablestats</code> gives an estimated partition count.'),
        ('Can you GROUP BY a clustering column?', 'Yes, if all preceding key columns are also grouped: <code>GROUP BY roll_no, exam_date</code> is allowed, '
         '<code>GROUP BY exam_date</code> alone is not.'),
    ),
]),
])
