from build import *
from snowflakedb.anims import *
from snowflakedb.runner import sql, sq

# 3,650 exam rows with dates spread over a year in a scrambled (deterministic) load order
EXAMS = '''
CREATE OR REPLACE TABLE exam_log AS
SELECT n,
       DATEADD(day, MOD(n * 7919, 365), '2026-01-01'::DATE) AS exam_date,
       FLOOR(n / 365)                                      AS mp_load_order
FROM (SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1 AS n
      FROM TABLE(GENERATOR(ROWCOUNT => 3650)));
'''

SECTION = dict(level='intermediate', title='Micro-partitions, Pruning & Performance', questions=[

# ------------------------------------------------------------------ 11
Q('What are micro-partitions? How does Snowflake store table data?', 'Micro-partitions', minutes=8, cards=[
    definition(
        defbox('Snowflake automatically divides every table into <strong>micro-partitions</strong>: contiguous units of storage holding '
               '<strong>50 to 500 MB of uncompressed data</strong> (much less once compressed). Rows are grouped in the order they are loaded, '
               'and inside each micro-partition the data is stored <strong>column by column</strong>, each column compressed with the best '
               'algorithm for its values.',
               'Micro-partitions are <strong>immutable</strong>. An UPDATE or DELETE writes new micro-partitions and marks the old ones as '
               'replaced; this is what makes Time Travel and zero-copy cloning possible. For every micro-partition Snowflake stores '
               '<strong>metadata</strong>: the range of values (min/max) of each column, the number of distinct values and other statistics.'),
        tags('Micro-partition', 'Columnar', 'Immutable', 'Min/max metadata', 'Automatic', 'No manual partitioning'),
    ),
    analogy('An exam answer-sheet store room where bundles of about 500 sheets are tied up in the order they arrive, and each bundle has a '
            '<strong>label</strong> saying "roll numbers 2401–2460, dates 2–5 Feb". You never open a bundle whose label cannot match what you want.'),
    micropartition_anim(),
    comparison(
        table(['', 'Hive / Spark partitions', 'Snowflake micro-partitions'], [
            ['Created by', 'You (PARTITIONED BY column)', 'Snowflake, automatically'],
            ['Size', 'Whatever the data gives: can be tiny or huge', '50–500 MB uncompressed, uniform'],
            ['Granularity', 'Folder per value; too many values = too many folders', 'Millions of small units; no skew from cardinality'],
            ['Overlap', 'None: one value per folder', 'Value ranges can overlap; clustering reduces overlap'],
        ]),
        title='Compared with Traditional Partitioning'),
    real_world(
        scenario('Why nobody writes PARTITION BY in Snowflake',
                 p('A 2-TB attendance table loaded daily ends up naturally ordered by date, because each day\'s file is loaded after the previous '
                   'one. Queries for "last 7 days" read only the newest micro-partitions without anyone having designed a partitioning scheme.')),
    ),
    example(
        sql(EXAMS + '''
SELECT COUNT(*)                 AS exam_rows,
       MIN(exam_date)           AS first_date,
       MAX(exam_date)           AS last_date,
       COUNT(DISTINCT exam_date) AS distinct_days
FROM   exam_log;
''', data=False, show='queries'),
        p('<code>GENERATOR</code> with <code>ROW_NUMBER()</code> is the usual way to create test data inside Snowflake. This table is reused in the '
          'next questions to simulate pruning.', top=True),
        sq('''
-- real account: how many micro-partitions and how well clustered on exam_date
SELECT SYSTEM$CLUSTERING_INFORMATION('exam_log', '(exam_date)');
-- returns JSON with total_partition_count, average_overlaps, average_depth, partition_depth_histogram …
'''),
        title='Example'),
    steps(
        ('Load data in a sensible order', 'For example by date; micro-partitions follow load order.'),
        ('Do not try to "partition" manually', 'No PARTITION BY, no many small tables per month.'),
        ('Check pruning', 'In the Query Profile compare partitions scanned with partitions total.'),
        ('Consider a clustering key', 'Only for very large tables whose natural order does not match the main filters.'),
        title='Steps'),
    crossq(
        ('Can you see or control individual micro-partitions?', 'No. You see only their effect: statistics in the Query Profile and clustering '
         'information. Snowflake manages them completely.'),
        ('What happens on UPDATE of one row?', 'The micro-partition containing it is rewritten as a new micro-partition with the change; the old one '
         'is kept for Time Travel and Fail-safe. Frequent single-row updates on huge tables are therefore expensive.'),
        ('Why is Snowflake storage cheap even for large tables?', 'Columnar compression is very effective (often 3–10×), and billing is on the '
         'compressed size.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What is partition pruning? How do you write queries that prune well?', 'Pruning', minutes=8, cards=[
    definition(
        defbox('<strong>Pruning</strong> means skipping micro-partitions that cannot contain matching rows, using only their min/max metadata. It '
               'happens in the cloud services layer before any data is read. The Query Profile shows it as <strong>Partitions scanned</strong> '
               'vs <strong>Partitions total</strong>.',
               'Pruning works for filters (and join filters) that compare a column with constants: <code>=</code>, <code>&lt;</code>, '
               '<code>&gt;</code>, <code>BETWEEN</code>, <code>IN</code>, <code>LIKE \'abc%\'</code>. It may not work when the column is hidden '
               'inside an expression or function, or compared with the result of a sub-query evaluated per row.'),
        tags('Pruning', 'Partitions scanned', 'Min/max', 'Sargable predicate', 'Query Profile'),
    ),
    analogy('Looking for a word in a <strong>dictionary</strong>: you use the guide words at the top of each page and skip to the right page. If you '
            'asked "find words whose <em>last</em> letter is e", the guide words are useless and you must read every page.'),
    pruning_anim(),
    real_world(
        scenario('Same answer, different cost',
                 p('A report filtered on <code>YEAR(exam_date) = 2026 AND MONTH(exam_date) = 2</code>. Rewriting it as a date range '
                   '(<code>exam_date &gt;= \'2026-02-01\' AND exam_date &lt; \'2026-03-01\'</code>) gives exactly the same rows and lets the optimiser '
                   'compare the raw column with the min/max ranges directly. Snowflake can sometimes prune through simple functions, but a plain '
                   'range on the column is the form that always works.')),
    ),
    example(
        sql('''
-- function-wrapped column: harder to prune
SELECT COUNT(*) AS feb_joiners
FROM   students
WHERE  YEAR(joined) = 2026 AND MONTH(joined) = 2;

-- plain range on the column: prunes on min/max
SELECT COUNT(*) AS feb_joiners
FROM   students
WHERE  joined >= '2026-02-01' AND joined < '2026-03-01';
''', show='queries'),
        p('Both return the same count. On an 8-row table both are instant; on billions of rows the second form is the one to write.', top=True),
        sq('''
-- check before running: EXPLAIN shows partitionsTotal and partitionsAssigned
EXPLAIN SELECT COUNT(*) FROM attendance WHERE att_date = '2026-02-15';
'''),
        title='Example'),
    steps(
        ('Filter on the stored column', 'Move functions to the constant side: <code>col &gt;= DATEADD(day, -7, CURRENT_DATE())</code>.'),
        ('Match data types', 'Compare a DATE column with a DATE, not with a string that needs conversion per row.'),
        ('Use EXPLAIN', 'Look at partitionsAssigned vs partitionsTotal before running a heavy query.'),
        ('Check the profile after running', 'Partitions scanned should be a small fraction of the total for selective filters.'),
        title='Steps'),
    crossq(
        ('Does pruning work on joins?', 'Yes, partly. Snowflake can use the values from the smaller side of a join to prune the larger side at run '
         'time (dynamic or join pruning), for example a filtered date dimension joined to a fact table.'),
        ('Does LIMIT reduce the data scanned?', 'Sometimes: for a simple <code>SELECT … LIMIT n</code> Snowflake stops early. With ORDER BY or '
         'aggregation it must still read every relevant micro-partition.'),
        ('Can pruning work on VARIANT columns?', 'Yes for paths Snowflake has extracted into hidden sub-columns, for example '
         '<code>WHERE v:centre::STRING = \'Juhu\'</code>.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What is a clustering key? When should you define one, and what does clustering depth mean?', 'Clustering Keys', minutes=9, cards=[
    definition(
        defbox('A <strong>clustering key</strong> is one or more columns (or expressions) that Snowflake should use to co-locate rows in the same '
               'micro-partitions. Once defined, <strong>Automatic Clustering</strong> re-organises data in the background using serverless '
               'compute, billed in credits.',
               '<strong>Clustering depth</strong> is the average number of micro-partitions whose value ranges overlap for a given value. A '
               'perfectly clustered table has a depth close to 1; a high depth means filters must read many micro-partitions. Use '
               '<code>SYSTEM$CLUSTERING_INFORMATION</code> and <code>SYSTEM$CLUSTERING_DEPTH</code> to measure it.'),
        tags('CLUSTER BY', 'Automatic Clustering', 'Clustering depth', 'Overlap', 'Serverless credits'),
    ),
    analogy('A <strong>library returns trolley</strong>: books come back in random order and are shelved wherever there is space, so every '
            'shelf has a bit of everything. Clustering is the librarian re-shelving by subject so that one shelf holds one subject.'),
    clustering_anim(),
    real_world(
        scenario('When it is worth it',
                 ul('Table is multi-terabyte (many thousands of micro-partitions) and queries filter on the same column most of the time.',
                    'The natural load order does not match the filter, for example data loaded by centre but queried by date.',
                    'The table is queried far more often than it changes, so the re-clustering credits pay for themselves.',
                    'It is not worth it for small tables or tables rewritten completely every day.')),
    ),
    example(
        sql(EXAMS + '''
-- simulate micro-partitions of 365 rows and ask: which could hold 15 May 2026?
-- 1) in load order (scrambled dates)
SELECT COUNT(*) AS partitions_total,
       COUNT_IF('2026-05-15'::DATE BETWEEN min_d AND max_d) AS partitions_to_scan
FROM (SELECT mp_load_order, MIN(exam_date) AS min_d, MAX(exam_date) AS max_d
      FROM exam_log GROUP BY mp_load_order);

-- 2) after clustering by exam_date (rows re-grouped in date order)
SELECT COUNT(*) AS partitions_total,
       COUNT_IF('2026-05-15'::DATE BETWEEN min_d AND max_d) AS partitions_to_scan
FROM (SELECT mp, MIN(exam_date) AS min_d, MAX(exam_date) AS max_d
      FROM (SELECT exam_date,
                   FLOOR((ROW_NUMBER() OVER (ORDER BY exam_date, n) - 1) / 365) AS mp
            FROM exam_log)
      GROUP BY mp);
''', data=False, show='queries'),
        p('This is a SQL simulation of what Automatic Clustering achieves: the same 3,650 rows in 10 groups. In load order every group spans almost '
          'the whole year, so all 10 must be scanned; after sorting by date only 1 group can contain 15 May.', top=True),
        sq('''
ALTER TABLE exam_log CLUSTER BY (exam_date);
ALTER TABLE events   CLUSTER BY (TO_DATE(event_ts), centre);   -- expressions and multiple columns
SELECT SYSTEM$CLUSTERING_DEPTH('exam_log', '(exam_date)');
ALTER TABLE exam_log SUSPEND RECLUSTER;                          -- pause the background service
ALTER TABLE exam_log DROP CLUSTERING KEY;
'''),
        title='Example: Simulating Pruning Before and After Clustering'),
    steps(
        ('Confirm the problem', 'Partitions scanned close to total for the important queries.'),
        ('Pick the key', 'The column used most in selective filters; low-to-medium cardinality first, at most 3–4 columns; truncate high-cardinality '
         'timestamps with an expression such as <code>TO_DATE(ts)</code>.'),
        ('Define it', '<code>ALTER TABLE … CLUSTER BY (…)</code>.'),
        ('Monitor cost and effect', 'AUTOMATIC_CLUSTERING_HISTORY for credits; clustering depth and query times for benefit.'),
        title='Steps'),
    crossq(
        ('Is a clustering key the same as a primary key or index?', 'No. It only guides physical placement of rows. Snowflake does not enforce primary '
         'keys on standard tables, and there are no B-tree indexes.'),
        ('Why not cluster on a unique ID column?', 'Very high cardinality makes clustering expensive to maintain and gives little pruning benefit for '
         'range filters. Search optimisation is better for point lookups on IDs.'),
        ('Can you get good clustering without a clustering key?', 'Yes, by loading or inserting data sorted by the filter column, for example '
         '<code>INSERT … SELECT … ORDER BY exam_date</code> when rebuilding a table.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('Explain Search Optimization, Materialized Views and the Query Acceleration Service.', 'Performance Services', minutes=8, cards=[
    definition(
        table(['Feature', 'Speeds up', 'How', 'Notes'], [
            ['Search Optimization Service', 'Selective point lookups: <code>WHERE email = …</code>, IN lists, substring and regex, VARIANT fields, geo',
             'Builds a persistent search access path per micro-partition', 'Enable for a table or specific columns; storage + serverless cost'],
            ['Materialized View', 'Repeated aggregations or filters on one large table', 'Stores the query result; background refresh keeps it current',
             'Single table only (no joins); limited functions; serverless refresh cost'],
            ['Query Acceleration Service (QAS)', 'Outlier queries with large scans and selective filters', 'Offloads part of the scan to shared serverless compute',
             'Warehouse setting; QUERY_ACCELERATION_MAX_SCALE_FACTOR caps it'],
        ]),
        defbox('All three require <strong>Enterprise edition or higher</strong> and are billed through serverless credits (and storage for search '
               'access paths and materialized views).'),
        tags('Search Optimization', 'Materialized View', 'Query Acceleration', 'Enterprise', 'Serverless'),
    ),
    analogy('Search optimisation is a <strong>book index</strong> at the back; a materialized view is a <strong>summary sheet</strong> someone keeps '
            'updated; query acceleration is <strong>calling in extra helpers</strong> only on the day a huge job arrives.'),
    accel_anim(),
    real_world(
        scenario('Matching each problem to a feature',
                 ul('Support staff look up one candidate by email in a 2-billion-row login table: <strong>search optimisation</strong>.',
                    'Every dashboard computes daily attendance per centre from the same 500 GB table: <strong>materialized view</strong> '
                    '(or a dynamic table if joins are needed).',
                    'A monthly audit query scans a year of data while the warehouse is sized for small queries: <strong>query acceleration</strong>.')),
    ),
    example(
        sq('''
-- 1. Search optimisation for lookups on specific columns
ALTER TABLE logins ADD SEARCH OPTIMIZATION ON EQUALITY(email), SUBSTRING(device_name);
SELECT * FROM logins WHERE email = 'riya.k@example.in';

-- 2. Materialized view on one table
CREATE MATERIALIZED VIEW daily_attendance_mv AS
SELECT att_date, centre, COUNT(*) AS present
FROM   attendance
WHERE  present
GROUP  BY att_date, centre;

-- 3. Query acceleration on a warehouse
ALTER WAREHOUSE bi_wh SET ENABLE_QUERY_ACCELERATION = TRUE
                          QUERY_ACCELERATION_MAX_SCALE_FACTOR = 8;
SELECT SYSTEM$ESTIMATE_QUERY_ACCELERATION('<query_id>');   -- would this query benefit?
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Identify the slow pattern', 'Lookup, repeated aggregation, or occasional huge scan.'),
        ('Estimate', '<code>SYSTEM$ESTIMATE_SEARCH_OPTIMIZATION_COSTS</code> and <code>SYSTEM$ESTIMATE_QUERY_ACCELERATION</code>.'),
        ('Enable on the smallest scope', 'Specific columns or one warehouse.'),
        ('Measure benefit vs cost', 'Compare query times and the serverless credit history views.'),
        title='Steps'),
    crossq(
        ('Does a query have to mention the materialized view?', 'No. The optimiser can rewrite queries on the base table to use the MV automatically '
         'when it can answer them, though querying the MV directly is clearer.'),
        ('Is a materialized view ever stale?', 'Results are always current: if background maintenance is behind, Snowflake combines the MV with the '
         'base table\'s newer data at query time.'),
        ('What is the difference between a materialized view and a dynamic table?', 'A materialized view is for accelerating queries on one table and '
         'is always current. A dynamic table can contain joins and complex SQL, is refreshed to a target lag, and is used to build pipelines.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('Which Snowflake-specific SQL features help you write shorter, faster queries?', 'Snowflake SQL Extras', minutes=8, cards=[
    definition(
        table(['Feature', 'What it does'], [
            ['<code>QUALIFY</code>', 'Filter on window-function results without a sub-query'],
            ['<code>GROUP BY ALL</code>', 'Group by every non-aggregate column in the SELECT list'],
            ['<code>SELECT * EXCLUDE (…)</code> / <code>RENAME (…)</code>', 'All columns except some, or with some renamed'],
            ['<code>ILIKE</code>, <code>LIKE ANY (…)</code>', 'Case-insensitive match; match any of several patterns'],
            ['<code>IFF</code>, <code>DECODE</code>, <code>NVL</code>, <code>ZEROIFNULL</code>', 'Short conditional and NULL handling'],
            ['<code>MAX_BY</code> / <code>MIN_BY</code>', 'Value of one column at the max/min of another'],
            ['<code>COUNT_IF</code>, <code>LISTAGG</code>, <code>ARRAY_AGG</code>', 'Conditional counts and string/array aggregation'],
            ['Lateral column alias', 'Use an alias defined earlier in the same SELECT list'],
        ]),
        tags('QUALIFY', 'GROUP BY ALL', 'EXCLUDE', 'ILIKE', 'MAX_BY', 'COUNT_IF', 'LISTAGG'),
    ),
    analogy('Snowflake SQL is standard SQL with <strong>keyboard shortcuts</strong>: you could type everything the long way, but the shortcuts save '
            'time and mistakes.'),
    qualify_anim(),
    real_world(
        scenario('Course toppers in one query',
                 p('The academic cell wants the topper of each course with their marks and the course average. QUALIFY with RANK() gives the toppers '
                   'without a sub-query, and a window AVG gives the average on the same row.')),
    ),
    example(
        sql('''
-- topper of each course
SELECT course, name, marks,
       AVG(marks) OVER (PARTITION BY course)::NUMBER(6,2) AS course_avg
FROM   students
QUALIFY RANK() OVER (PARTITION BY course ORDER BY marks DESC) = 1
ORDER  BY course;

-- GROUP BY ALL, COUNT_IF, MAX_BY, LISTAGG
SELECT centre,
       COUNT(*)                                        AS students,
       COUNT_IF(marks >= 80)                           AS distinctions,
       MAX_BY(name, marks)                             AS topper,
       LISTAGG(name, ', ') WITHIN GROUP (ORDER BY name) AS names
FROM   students
GROUP  BY ALL
ORDER  BY centre;

-- EXCLUDE, ILIKE, IFF
SELECT * EXCLUDE (joined, centre),
       IFF(marks >= 80, 'Distinction', 'Pass') AS grade
FROM   students
WHERE  name ILIKE 'a%'
ORDER  BY roll_no;
''', show='queries'),
        title='Example'),
    steps(
        ('Replace sub-query filters on window functions', 'Use QUALIFY.'),
        ('Use GROUP BY ALL in exploratory queries', 'Fewer mistakes when columns change.'),
        ('Avoid SELECT * in production', 'Use explicit columns or EXCLUDE so fewer columns are read (columnar storage).'),
        ('Prefer COUNT_IF / IFF over long CASE expressions', 'Shorter and easier to read.'),
        title='Steps'),
    crossq(
        ('Is QUALIFY standard SQL?', 'No, it is an extension (also found in Teradata, BigQuery and Databricks). The standard way is a sub-query or CTE '
         'with a WHERE on the window column.'),
        ('Why does SELECT * hurt more in Snowflake than in a row store?', 'Storage is columnar: every extra column is extra data read from storage. '
         'Selecting 5 of 60 columns can cut the data scanned by more than 90%.'),
        ('RANK vs ROW_NUMBER in QUALIFY?', 'RANK returns all tied toppers; ROW_NUMBER returns exactly one row per group (tie broken arbitrarily unless '
         'you add more ORDER BY columns).'),
    ),
]),
])
