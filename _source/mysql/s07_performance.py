from build import *
from mysql.anims import *
from mysql.data import EMP, SALES, ALL, sample

# 2,00,000 generated orders so the optimizer behaves as it would on a real table
BIG = """
SET SESSION cte_max_recursion_depth = 300000;
CREATE TABLE orders (
  order_id    INT PRIMARY KEY,
  customer_id INT NOT NULL,
  order_date  DATE NOT NULL,
  amount      DECIMAL(10,2) NOT NULL,
  status      VARCHAR(12) NOT NULL,
  phone       VARCHAR(15) NOT NULL
);
INSERT INTO orders
WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < 200000)
SELECT n, 1 + n % 5000, DATE '2025-01-01' + INTERVAL (n % 600) DAY, (n * 37) % 10000,
       ELT(1 + (n DIV 7) % 4, 'DELIVERED', 'SHIPPED', 'CANCELLED', 'PENDING'),
       CONCAT('98', LPAD(n, 8, '0'))
FROM s;
CREATE INDEX idx_customer ON orders(customer_id);
CREATE INDEX idx_order_date ON orders(order_date);
CREATE INDEX idx_phone ON orders(phone);
ANALYZE TABLE orders;
"""

BIG_NOTE = note('These examples run on a generated <code>orders</code> table with <strong>2,00,000 rows</strong> '
                '(columns order_id, customer_id, order_date, amount, status, phone) so that the optimizer behaves as it would on a real table. '
                'Timings in EXPLAIN ANALYZE are from the build server and will differ on yours.', 'Test data')

SECTION = dict(level='expert', title='Performance & Query Tuning', questions=[

# ------------------------------------------------------------------ 44
Q('How do you use EXPLAIN and EXPLAIN ANALYZE? How do you read the output?', 'EXPLAIN & EXPLAIN ANALYZE', minutes=9, cards=[
    definition(
        defbox('<strong>EXPLAIN</strong> shows the plan the optimizer <em>intends</em> to use: access method per table, chosen '
               'index, estimated rows and extra operations such as sorting. <strong>EXPLAIN ANALYZE</strong> (MySQL 8.0.18+) actually '
               '<em>runs</em> the query and adds real row counts and timings to each step.'),
        tags('EXPLAIN', 'EXPLAIN ANALYZE', 'type', 'key', 'rows', 'Extra', 'Using filesort', 'Using index'),
    ),
    explanation(
        table(['type (best → worst)', 'Meaning'], [
            ['system / const', 'At most one row, found by primary key or unique index with a constant'],
            ['eq_ref', 'One row per row of the previous table, via a unique key (ideal join)'],
            ['ref', 'Several rows via a non-unique index lookup'],
            ['range', 'Index range scan (BETWEEN, &gt;, &lt;, IN, LIKE \'abc%\')'],
            ['index', 'Full scan of an index (all entries, but not the table)'],
            ['ALL', 'Full table scan: usually what you are trying to remove'],
        ]),
        table(['Extra', 'Meaning'], [
            ['Using index', 'Covering index: answered from the index alone (good)'],
            ['Using where', 'Rows filtered after being read'],
            ['Using filesort', 'Extra sort step for ORDER BY / GROUP BY (no index provides the order)'],
            ['Using temporary', 'An internal temporary table was needed (GROUP BY, DISTINCT, UNION)'],
        ]),
        title='Reading the Columns'),
    BIG_NOTE,
    example(
        sqlrun("""
-- Indexed equality on customer_id: type ref, ~40 rows
EXPLAIN SELECT order_id, amount FROM orders WHERE customer_id = 42\\G

-- No index on status, and ORDER BY amount: full scan + filesort
EXPLAIN SELECT order_id, amount FROM orders
WHERE status = 'PENDING' ORDER BY amount DESC LIMIT 5\\G
""", setup=BIG),
        title='Example: EXPLAIN'),
    example(
        sqlrun("""
EXPLAIN ANALYZE
SELECT customer_id, SUM(amount) AS spend
FROM orders
WHERE order_date >= '2026-08-01'
GROUP BY customer_id
ORDER BY spend DESC
LIMIT 3\\G
""", setup=BIG),
        title='Example: EXPLAIN ANALYZE (read bottom-up, innermost first)'),
    interview(p('Compare <strong>estimated rows</strong> with <strong>actual rows</strong> in EXPLAIN ANALYZE. A large difference '
                'means the optimizer had poor statistics (run <code>ANALYZE TABLE</code>) and may have chosen a bad plan.')),
    crossq(
        ('Does EXPLAIN run the query?', 'Plain EXPLAIN does not (except for some derived tables). EXPLAIN ANALYZE does run it fully, so be careful with very slow queries on production.'),
        ('Which formats exist?', 'Traditional (table), <code>FORMAT=TREE</code> (indented plan tree), <code>FORMAT=JSON</code> (with cost details).'),
    ),
]),

# ------------------------------------------------------------------ 45
Q('Why is my index not being used? (Sargable predicates)', 'Why Is My Index Not Used?', minutes=9, cards=[
    definition(
        defbox('An index can only be used when the condition lets MySQL <strong>search the sorted index</strong> for a value or '
               'range. Such conditions are called <strong>sargable</strong>. Wrapping the column in a function, comparing it to '
               'a different type, or using a leading wildcard makes the predicate non-sargable and forces a full scan.'),
        tags('Sargable', 'Function on Column', 'Implicit Conversion', 'Leading Wildcard', 'Functional Index'),
    ),
    sargable_anim(),
    table(['Non-sargable', 'Sargable rewrite'], [
        ["<code>WHERE YEAR(order_date) = 2026</code>", "<code>WHERE order_date &gt;= '2026-01-01' AND order_date &lt; '2027-01-01'</code>"],
        ["<code>WHERE DATE(created_at) = '2026-10-11'</code>", "<code>WHERE created_at &gt;= '2026-10-11' AND created_at &lt; '2026-10-12'</code>"],
        ['<code>WHERE amount * 1.18 &gt; 1000</code>', '<code>WHERE amount &gt; 1000 / 1.18</code>'],
        ['<code>WHERE phone = 9800000042</code> (VARCHAR vs number)', "<code>WHERE phone = '9800000042'</code>"],
        ["<code>WHERE name LIKE '%kumar'</code>", "<code>LIKE 'kumar%'</code>, or a FULLTEXT index / reversed column"],
        ['<code>WHERE a = 1 OR b = 2</code> (separate indexes)', 'Often fine (index merge); otherwise UNION of two indexed queries'],
    ]),
    BIG_NOTE,
    example(
        sqlrun("""
EXPLAIN FORMAT=TREE SELECT SUM(amount) FROM orders
WHERE order_date >= '2026-02-01' AND order_date < '2026-03-01'\\G

EXPLAIN FORMAT=TREE SELECT SUM(amount) FROM orders
WHERE MONTH(order_date) = 2 AND YEAR(order_date) = 2026\\G

-- phone is VARCHAR: a numeric literal forces a cast on every row
EXPLAIN FORMAT=TREE SELECT order_id, amount FROM orders WHERE phone = 9800000042\\G
EXPLAIN FORMAT=TREE SELECT order_id, amount FROM orders WHERE phone = '9800000042'\\G
""", setup=BIG),
        title='Example: Same Question, Different Plans'),
    example(
        sqlrun("""
-- MySQL 8.0.13+: index an expression when the function cannot be avoided
CREATE INDEX idx_order_month ON orders ((MONTH(order_date)));
EXPLAIN FORMAT=TREE SELECT SUM(amount) FROM orders WHERE MONTH(order_date) = 2\\G
""", setup=BIG),
        title='Example: Functional Index'),
    crossq(
        ('Other reasons an index is skipped?', 'Low selectivity (the condition matches a large share of rows, so a scan is cheaper); the leftmost-prefix rule for composite indexes; stale statistics; a different collation or character set on a join column.'),
        ('How do you force an index for testing?', '<code>SELECT … FROM orders FORCE INDEX (idx_order_date) WHERE …</code>. Use it to test, not as a permanent fix: data changes and the hint stays.'),
    ),
]),

# ------------------------------------------------------------------ 46
Q('A query is slow. How do you approach optimising it?', 'Query Optimisation Approach', minutes=9, cards=[
    definition(
        defbox('Tuning is a loop: <strong>measure</strong> (find the real slow query), <strong>explain</strong> (see the plan), '
               '<strong>fix the biggest cost</strong> (usually a missing or unusable index, or too much data read), and '
               '<strong>measure again</strong>.'),
        tags('Query Tuning', 'Composite Index', 'Covering Index', 'Filesort', 'SELECT *'),
    ),
    explanation(
        ul('<strong>Find it</strong>: slow query log or <code>performance_schema</code> digests (next questions). Fix the query that costs the most in total, not the one that looks worst once.',
           '<strong>EXPLAIN / EXPLAIN ANALYZE</strong>: look for <code>type: ALL</code> on big tables, high row estimates, <em>Using filesort</em> and <em>Using temporary</em>.',
           '<strong>Index for the query</strong>: equality columns first, then the range or ORDER BY column. A <strong>composite index</strong> can filter <em>and</em> deliver rows already sorted.',
           '<strong>Make predicates sargable</strong>: no functions or casts on indexed columns.',
           '<strong>Read less</strong>: select only needed columns (enables covering indexes), filter early, avoid fan-out joins, use keyset pagination.',
           '<strong>Rewrite</strong>: correlated subqueries → joins or window functions; <code>OR</code> → UNION ALL; huge IN lists → join to a temp table.',
           '<strong>Check the environment</strong>: statistics (<code>ANALYZE TABLE</code>), buffer pool size vs data size, lock waits.'),
        title='Checklist'),
    BIG_NOTE,
    example(
        sqlrun("""
-- The customer's 5 most recent delivered orders
-- Before: only idx_customer exists, so all of the customer's rows are read, filtered and sorted
EXPLAIN ANALYZE
SELECT order_id, order_date, amount FROM orders
WHERE customer_id = 42 AND status = 'DELIVERED'
ORDER BY order_date DESC LIMIT 5\\G

-- After: composite index (equality columns, then the sort column)
CREATE INDEX idx_cust_status_date ON orders (customer_id, status, order_date);

EXPLAIN ANALYZE
SELECT order_id, order_date, amount FROM orders
WHERE customer_id = 42 AND status = 'DELIVERED'
ORDER BY order_date DESC LIMIT 5\\G
""", setup=BIG),
        title='Example: Removing a Filesort with a Composite Index'),
    explanation(
        p('Before: <em>Index lookup on idx_customer</em> reads all 40 rows of the customer, the <em>Filter</em> keeps the 12 '
          'delivered ones, and a <em>Sort</em> step orders them to pick 5. After: <em>Index lookup … (reverse)</em> on the new '
          'index goes straight to this customer\'s delivered orders, already in date order, so the filter and the sort '
          'disappear and MySQL stops after reading 5 rows.'),
        title='What Changed'),
    interview(p('Interviewers like a structured answer: "First I confirm which query is slow and how often it runs, then I '
                'read EXPLAIN ANALYZE, then I fix indexes or rewrite, and I verify the improvement with the same measurement." '
                'Also mention that every new index slows down writes, so add indexes for real query patterns only.')),
    crossq(
        ('Why avoid SELECT *?', 'It reads and sends columns you do not need, prevents covering-index plans, and breaks code when columns are added.'),
        ('Is adding more indexes always good?', 'No. Each index costs disk, memory and time on every INSERT/UPDATE/DELETE, and too many similar indexes confuse the optimizer. Remove unused ones (<code>sys.schema_unused_indexes</code>).'),
    ),
]),

# ------------------------------------------------------------------ 47
Q('Why is LIMIT with a large OFFSET slow? What is keyset pagination?', 'OFFSET vs Keyset Pagination', minutes=7, cards=[
    definition(
        defbox('<code>LIMIT 10 OFFSET 100000</code> must read and discard the first 1,00,000 rows before returning 10, so each '
               'deeper page is slower. <strong>Keyset (seek) pagination</strong> remembers the last key of the previous page and '
               'asks for <code>WHERE key &gt; last_key ORDER BY key LIMIT 10</code>, which is an index seek costing the same for every page.'),
        tags('Pagination', 'LIMIT', 'OFFSET', 'Keyset Pagination', 'Seek Method'),
    ),
    keyset_anim(),
    BIG_NOTE,
    example(
        sqlrun("""
EXPLAIN ANALYZE
SELECT order_id, amount FROM orders ORDER BY order_id LIMIT 10 OFFSET 100000\\G

EXPLAIN ANALYZE
SELECT order_id, amount FROM orders WHERE order_id > 100000 ORDER BY order_id LIMIT 10\\G
""", setup=BIG),
        title='Example: Rows Actually Read'),
    explanation(
        code("""
-- Page by a non-unique column: use (column, id) as the key
SELECT order_id, order_date, amount
FROM orders
WHERE (order_date, order_id) < ('2026-03-01', 51234)   -- last row of the previous page
ORDER BY order_date DESC, order_id DESC
LIMIT 20;
""", 'Keyset on (date, id)'),
        title='Sorting by Something Other than the Primary Key'),
    real_world(p('Extracting a big table in chunks for a pipeline: loop with <code>WHERE id &gt; :last_id ORDER BY id LIMIT 50000</code> '
                 'instead of increasing OFFSETs. The last chunk is as fast as the first, and the job can resume from the last id after a failure.')),
    crossq(
        ('What if the user needs to jump to page 500?', 'Keyset cannot jump. Options: limit how deep users can go, use a "deferred join" (<code>SELECT … JOIN (SELECT id … LIMIT 10 OFFSET n) USING (id)</code>, scanning only the narrow index), or precompute page boundaries.'),
    ),
]),

# ------------------------------------------------------------------ 48
Q('How do you find slow queries? Explain the slow query log, performance_schema and sys schema', 'Slow Query Log & performance_schema', minutes=7, cards=[
    definition(
        defbox('The <strong>slow query log</strong> records statements that take longer than <code>long_query_time</code>. '
               '<strong>performance_schema</strong> collects in-memory statistics on everything the server does, including totals per '
               'normalised statement (<em>digest</em>). The <strong>sys schema</strong> wraps performance_schema in readable views.'),
        tags('Slow Query Log', 'long_query_time', 'performance_schema', 'Statement Digest', 'sys schema', 'pt-query-digest'),
    ),
    explanation(
        code("""
-- Enable the slow query log at runtime (persist it in my.cnf for restarts)
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;                     -- seconds
SET GLOBAL log_queries_not_using_indexes = ON;      -- optional, can be noisy
SHOW VARIABLES LIKE 'slow_query_log_file';
""", 'Slow Query Log'),
        p('Summarise the log with <code>mysqldumpslow</code> or Percona\'s <code>pt-query-digest</code>, which groups similar '
          'queries and ranks them by total time.', True),
    ),
    example(
        sqlrun("""
-- Some workload
SELECT COUNT(*) FROM orders WHERE status = 'PENDING';
SELECT COUNT(*) FROM orders WHERE status = 'SHIPPED';
SELECT SUM(amount) FROM orders WHERE customer_id = 7;

-- Top statements in this schema by total time (literals are normalised to ?)
SELECT DIGEST_TEXT                          AS query,
       COUNT_STAR                           AS runs,
       SUM_ROWS_EXAMINED                    AS rows_examined,
       SUM_NO_INDEX_USED                    AS no_index_runs
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME = DATABASE() AND DIGEST_TEXT LIKE 'SELECT%FROM `orders`%'
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 3;
""", setup=BIG + "TRUNCATE TABLE performance_schema.events_statements_summary_by_digest;"),
        title='Example: Statement Digests'),
    note('The two status queries differ only in the literal, so they are grouped into one digest that ran 2 times and '
         'examined 4,00,000 rows without an index. That is exactly the kind of query to tune first.', 'Reading the result'),
    explanation(
        table(['sys view', 'Shows'], [
            ['sys.statement_analysis', 'Statements ranked by total latency'],
            ['sys.statements_with_full_table_scans', 'Queries doing full scans'],
            ['sys.schema_unused_indexes', 'Indexes never used since startup (candidates to drop)'],
            ['sys.schema_redundant_indexes', 'Indexes duplicated by another index\'s prefix'],
            ['sys.innodb_lock_waits', 'Who is blocking whom right now'],
        ]),
        title='Useful sys Views'),
    crossq(
        ('How do you see what is running right now?', '<code>SHOW FULL PROCESSLIST;</code> (or <code>sys.processlist</code>). A runaway query can be stopped with <code>KILL QUERY &lt;id&gt;</code>.'),
    ),
]),

# ------------------------------------------------------------------ 49
Q('What is table partitioning in MySQL? What is partition pruning?', 'Partitioning & Pruning', minutes=8, cards=[
    definition(
        defbox('<strong>Partitioning</strong> splits one logical table into several physical pieces by a <em>partition key</em>, '
               'inside the same server. MySQL supports RANGE, LIST, HASH and KEY partitioning. <strong>Partition pruning</strong> means '
               'the optimizer reads only the partitions that can contain matching rows.'),
        tags('RANGE Partitioning', 'LIST', 'HASH', 'Partition Pruning', 'DROP PARTITION', 'Data Retention'),
    ),
    example(
        sqlrun("""
CREATE TABLE events (
  event_id   BIGINT NOT NULL,
  event_date DATE   NOT NULL,
  user_id    INT,
  PRIMARY KEY (event_id, event_date)          -- must include the partition key
)
PARTITION BY RANGE (YEAR(event_date)) (
  PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION p2025 VALUES LESS THAN (2026),
  PARTITION p2026 VALUES LESS THAN (2027),
  PARTITION pmax  VALUES LESS THAN MAXVALUE
);
INSERT INTO events VALUES
 (1, '2024-03-01', 10), (2, '2024-11-20', 11), (3, '2025-06-15', 12),
 (4, '2026-01-10', 13), (5, '2026-09-30', 14), (6, '2026-10-01', 15);

-- Pruning: only p2026 is read (see the partitions column)
EXPLAIN SELECT * FROM events WHERE event_date >= '2026-01-01' AND event_date < '2027-01-01'\\G

SELECT PARTITION_NAME, TABLE_ROWS
FROM information_schema.PARTITIONS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'events';

-- Retention: removing a year is instant, no row-by-row DELETE
ALTER TABLE events DROP PARTITION p2024;
SELECT COUNT(*) AS rows_left FROM events;
"""),
        title='Example: Yearly RANGE Partitions'),
    comparison(
        table(['Benefit', 'Limitation'], [
            ['Queries on the partition key read fewer rows (pruning)', 'Queries <em>without</em> the partition key must check every partition'],
            ['Dropping / truncating old partitions is instant', 'Every PRIMARY/UNIQUE key must include the partition key'],
            ['Smaller per-partition indexes', 'Foreign keys are not supported on partitioned InnoDB tables'],
            ['Easy archival (EXCHANGE PARTITION)', 'Max 8192 partitions; too many small partitions hurt'],
        ]),
    ),
    crossq(
        ('Partitioning vs sharding?', 'Partitioning splits a table <em>within one server</em> and is transparent to the application. Sharding spreads data across <em>several servers</em> and needs routing logic. (See the RDBMS module.)'),
        ('Does the pruning work with YEAR(event_date) in the WHERE?', 'Write the condition on the raw column (<code>event_date &gt;= …</code>). MySQL maps the range onto the partitions itself; RANGE pruning on YEAR() expressions is supported for DATE columns.'),
    ),
]),

])
