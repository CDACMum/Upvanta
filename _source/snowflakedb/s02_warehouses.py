from build import *
from snowflakedb.anims import *
from snowflakedb.runner import sql, sq

SECTION = dict(level='beginner', title='Virtual Warehouses & Caching', questions=[

# ------------------------------------------------------------------ 6
Q('What is a virtual warehouse? How do you create, size and resize one?', 'Virtual Warehouses', minutes=7, cards=[
    definition(
        defbox('A <strong>virtual warehouse</strong> is a named cluster of compute resources (CPU, memory, local SSD) that executes SQL '
               'queries, DML and data loading. It holds no data. Sizes are <strong>X-Small, Small, Medium, Large, X-Large, 2X-Large … 6X-Large</strong>; '
               'each size up roughly doubles the compute and the credits per hour (1, 2, 4, 8, 16, 32 …).',
               'Warehouse types: <strong>Standard</strong> for most work and <strong>Snowpark-optimized</strong>, which has much more memory per '
               'node for memory-heavy Python and ML workloads. A warehouse is either <em>started</em> (billing) or <em>suspended</em> (not billing).'),
        tags('WAREHOUSE_SIZE', 'Credits per hour', 'Started / Suspended', 'Resize online', 'Snowpark-optimized', 'USE WAREHOUSE'),
    ),
    analogy('A warehouse is a <strong>team of cooks</strong> hired by the hour. The pantry (storage) is shared. A bigger team cooks a big order faster; '
            'when the kitchen is quiet you send them home and stop paying.'),
    warehouse_anim(),
    real_world(
        scenario('Choosing sizes',
                 ul('Ad hoc analyst queries on a few GB: X-Small or Small.',
                    'Nightly transformation of the full exam dataset (hundreds of GB): Medium or Large, sized by testing.',
                    'A one-off backfill of five years of attendance: temporarily resize to X-Large, then back to Small.')),
    ),
    example(
        sq('''
CREATE WAREHOUSE lab_wh
  WAREHOUSE_SIZE      = 'XSMALL'
  AUTO_SUSPEND        = 60          -- seconds of idle time before suspending
  AUTO_RESUME         = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT             = 'PGCP-BDA lab sessions';

USE WAREHOUSE lab_wh;

ALTER WAREHOUSE lab_wh SET WAREHOUSE_SIZE = 'LARGE';   -- resize, even while running
ALTER WAREHOUSE lab_wh SUSPEND;
ALTER WAREHOUSE lab_wh RESUME;

SHOW WAREHOUSES LIKE 'LAB%';
'''),
        title='Example'),
    steps(
        ('Create', 'Give a name, size, auto-suspend and auto-resume; start suspended.'),
        ('Grant access', '<code>GRANT USAGE ON WAREHOUSE lab_wh TO ROLE bda_student;</code>'),
        ('Use it', '<code>USE WAREHOUSE lab_wh;</code> or set it as the user\'s default warehouse.'),
        ('Measure', 'Check execution time, spilling and queuing in the Query Profile and QUERY_HISTORY.'),
        ('Resize if needed', 'Scale up for slow queries, scale out (multi-cluster) for concurrency.'),
        title='Steps'),
    crossq(
        ('Does resizing affect queries that are already running?', 'No. Running queries finish on the resources they started with; queued and new '
         'queries use the new size. Resizing a suspended warehouse only takes effect when it next starts.'),
        ('Is bigger always faster?', 'Not always. Small queries finish in seconds on X-Small and gain nothing. Bigger sizes help large scans, '
         'big joins and sorts, and queries that spill to disk.'),
        ('Does a warehouse cost money while suspended?', 'No compute cost while suspended. You only pay storage for the data, which is separate.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('What is the difference between scaling up and scaling out? Explain multi-cluster warehouses.', 'Scale Up vs Scale Out', minutes=8, cards=[
    definition(
        table(['', 'Scale up', 'Scale out'], [
            ['How', 'Bigger warehouse size', 'More clusters of the same size (multi-cluster warehouse)'],
            ['Solves', 'Slow, complex individual queries', 'Many concurrent queries waiting in the queue'],
            ['Command', "<code>ALTER WAREHOUSE … SET WAREHOUSE_SIZE = 'LARGE'</code>", '<code>MIN_CLUSTER_COUNT / MAX_CLUSTER_COUNT</code>'],
            ['Edition', 'All', 'Enterprise and above'],
        ]),
        defbox('A <strong>multi-cluster warehouse</strong> has a minimum and maximum number of clusters. In <strong>auto-scale</strong> mode '
               '(min &lt; max) Snowflake starts and stops clusters according to load and the <strong>scaling policy</strong>: '
               '<code>STANDARD</code> (default) starts a cluster as soon as queries queue; <code>ECONOMY</code> starts one only when there is '
               'enough load to keep it busy for about 6 minutes. In <strong>maximized</strong> mode (min = max) all clusters always run.'),
        tags('Scale up', 'Scale out', 'Multi-cluster', 'STANDARD policy', 'ECONOMY policy', 'Concurrency'),
    ),
    analogy('Scaling up is giving a single <strong>cashier a faster machine</strong>. Scaling out is <strong>opening more checkout counters</strong> '
            'when the queue gets long, and closing them when it clears.'),
    scale_up_out_anim(),
    real_world(
        scenario('Result day',
                 p('When CCEE results are published, hundreds of coordinators open the same dashboards within minutes. A '
                   '<code>BI_WH</code> of size Small with <code>MIN_CLUSTER_COUNT = 1, MAX_CLUSTER_COUNT = 4</code> grows to four clusters '
                   'during the rush and shrinks back to one by evening. Each query is still small, so making the warehouse Large would not help.')),
    ),
    example(
        sq('''
CREATE OR REPLACE WAREHOUSE bi_wh
  WAREHOUSE_SIZE    = 'SMALL'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 4
  SCALING_POLICY    = 'STANDARD'
  AUTO_SUSPEND      = 120
  AUTO_RESUME       = TRUE;

-- was there queuing?  (real account)
SELECT warehouse_name,
       COUNT(*)                                 AS queries,
       AVG(queued_overload_time) / 1000         AS avg_queued_s,
       AVG(execution_time) / 1000               AS avg_exec_s
FROM   SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE  start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP  BY warehouse_name;
'''),
        p('High <code>avg_queued_s</code> with low <code>avg_exec_s</code> means "too many queries at once": scale out. High '
          '<code>avg_exec_s</code> with spilling means "queries too heavy": scale up.', top=True),
        title='Example'),
    steps(
        ('Diagnose', 'Queued time → concurrency problem; long execution or spilling → size problem.'),
        ('For concurrency', 'Set MIN/MAX_CLUSTER_COUNT and a scaling policy (Enterprise edition).'),
        ('For heavy queries', 'Try the next size and compare elapsed time and credits.'),
        ('Re-check after a week', 'Look at QUERY_HISTORY and WAREHOUSE_METERING_HISTORY.'),
        title='Steps'),
    crossq(
        ('Does a multi-cluster warehouse make one query faster?', 'No. A single query runs on one cluster. Multi-cluster only adds capacity for more '
         'queries at the same time.'),
        ('How is a multi-cluster warehouse billed?', 'Each running cluster is billed like a separate warehouse of that size, per second. Four Small '
         'clusters cost 4 × 2 = 8 credits per hour while all four run.'),
        ('What is MAX_CONCURRENCY_LEVEL?', 'A warehouse parameter (default 8) that limits how many queries run at once on a cluster before new ones '
         'queue. Lowering it gives each query more resources; it does not add capacity.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('How do auto-suspend and auto-resume work, and how are warehouses billed?', 'Auto-Suspend & Billing', minutes=6, cards=[
    definition(
        defbox('<code>AUTO_SUSPEND</code> is the number of seconds of inactivity after which a warehouse suspends itself. '
               '<code>AUTO_RESUME = TRUE</code> starts it automatically when a query arrives. Warehouses are billed '
               '<strong>per second</strong> while started, with a <strong>minimum of 60 seconds</strong> each time a warehouse starts or resumes '
               '(also when it is resized up, for the added resources).'),
        tags('AUTO_SUSPEND', 'AUTO_RESUME', 'Per-second billing', '60-second minimum', 'Warehouse cache'),
    ),
    analogy('Lights with a <strong>motion sensor</strong>: they switch off when nobody is in the room and switch on when someone walks in. '
            'But every switch-on has a minimum charge, so a sensor that flickers on and off every few seconds costs more.'),
    suspend_anim(),
    real_world(
        scenario('A forgotten warehouse',
                 p('A faculty member creates a Medium warehouse with <code>AUTO_SUSPEND = NULL</code> (never) for a demo and forgets it. It runs for '
                   'a 30-day month: 4 × 24 × 30 = 2,880 credits for nothing. With <code>AUTO_SUSPEND = 60</code> it would have cost only the '
                   'minutes of actual use.')),
    ),
    example(
        sql('''
-- 10 short queries (5 s each) spread over an hour, at two AUTO_SUSPEND settings
-- each gap is longer than the setting, so every query causes a resume
SELECT setting,
       resumes,
       resumes * GREATEST(5 + idle_before_suspend, 60)      AS billed_seconds,
       (billed_seconds * 1 / 3600)::NUMBER(6,4)              AS xs_credits
FROM VALUES ('AUTO_SUSPEND = 60',  10, 60),
            ('AUTO_SUSPEND = 600', 10, 600)
     AS t(setting, resumes, idle_before_suspend);
''', data=False),
        p('Each resume runs for 5 seconds of work plus the idle time until suspension, with 60 seconds as the minimum. With a 60-second setting '
          'each episode is billed 65 seconds; with 600 seconds it is 605 seconds, almost ten times more for the same work.', top=True),
        sq('''
ALTER WAREHOUSE bi_wh SET AUTO_SUSPEND = 60;
ALTER WAREHOUSE etl_wh SET AUTO_SUSPEND = 300;   -- keeps the local cache warm between ETL steps
'''),
        title='Example: Effect of AUTO_SUSPEND'),
    steps(
        ('Always set AUTO_RESUME = TRUE', 'Users never have to start a warehouse manually.'),
        ('Start with AUTO_SUSPEND = 60', 'Good for BI and ad hoc warehouses.'),
        ('Lengthen only with a reason', 'If consecutive queries reuse the same data, a few minutes keeps the cache warm.'),
        ('Audit', 'Find warehouses with AUTO_SUSPEND = 0/NULL using <code>SHOW WAREHOUSES</code>.'),
        title='Steps'),
    crossq(
        ('Can AUTO_SUSPEND be shorter than 60 seconds?', 'It can be set lower, but the 60-second minimum is charged on every resume, so very '
         'low values rarely save money and can cost more when queries arrive every minute or two.'),
        ('What is lost when a warehouse suspends?', 'The local SSD cache. The next query must read data from remote storage again. The result '
         'cache, which belongs to the cloud services layer, is not affected.'),
        ('Do serverless features use your warehouses?', 'No. Snowpipe, automatic clustering, serverless tasks and similar features run on '
         'Snowflake-managed compute and are billed separately.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('Explain caching in Snowflake: result cache, warehouse cache and metadata.', 'Caching', minutes=8, cards=[
    definition(
        table(['Cache', 'Where', 'Lifetime', 'Reused when…'], [
            ['Result cache', 'Cloud services layer', '24 h, extended on each reuse up to 31 days', 'Exactly the same query text, data unchanged, '
             'role has privileges, no non-deterministic functions such as CURRENT_TIMESTAMP()'],
            ['Warehouse (local disk) cache', 'SSD of a running warehouse', 'Until the warehouse suspends', 'Any query on that warehouse that needs the '
             'same micro-partitions and columns'],
            ['Metadata', 'Cloud services layer', 'Always kept current', 'COUNT(*), MIN/MAX on a column, and similar questions answered from '
             'micro-partition statistics'],
        ]),
        tags('Result cache', 'Local disk cache', 'Metadata', 'USE_CACHED_RESULT', '24 hours', 'RESULT_SCAN'),
    ),
    analogy('A teacher answering questions: if someone asks the <strong>same question again</strong>, she repeats the answer (result cache). If she '
            'needs a book, she checks the <strong>books already on her desk</strong> first (warehouse cache) before walking to the library. '
            'For "how many books are on shelf 3?" she just reads the <strong>label on the shelf</strong> (metadata).'),
    cache_anim(),
    real_world(
        scenario('Dashboards that refresh every 5 minutes',
                 p('Twenty coordinators open the same "centre-wise pass percentage" dashboard. The first run uses the warehouse; the next nineteen '
                   'identical queries come back from the result cache in milliseconds without starting the warehouse, until new results are '
                   'loaded and the cache entry becomes invalid.')),
    ),
    example(
        sql('''
-- answered from micro-partition metadata in a real account (no warehouse scan)
SELECT COUNT(*)    AS total_students,
       MIN(marks)  AS lowest,
       MAX(marks)  AS highest,
       MIN(joined) AS first_join,
       MAX(joined) AS last_join
FROM   students;
''', show='queries'),
        sq('''
-- result cache: run twice, the second run shows "QUERY RESULT REUSE" in the Query Profile
SELECT centre, COUNT(*) FROM students GROUP BY centre;

-- turn it off for honest performance tests (session level)
ALTER SESSION SET USE_CACHED_RESULT = FALSE;

-- reuse the result of the previous query as a table
SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())) WHERE "COUNT(*)" > 3;
'''),
        title='Example'),
    steps(
        ('Write identical query text for repeated reports', 'BI tools generating the same SQL get result-cache hits.'),
        ('Avoid CURRENT_TIMESTAMP() in repeated queries', 'Non-deterministic functions disable result reuse.'),
        ('Group similar workloads on one warehouse', 'They share the warm local cache.'),
        ('Disable the result cache when benchmarking', '<code>USE_CACHED_RESULT = FALSE</code>.'),
        title='Steps'),
    crossq(
        ('Is the result cache shared between users?', 'Yes, across users and warehouses, as long as the role running the query has the required '
         'privileges on all tables in it and the other conditions hold.'),
        ('Does the result cache cost anything?', 'No warehouse credits. Results are stored by Snowflake and you are not billed storage for them.'),
        ('Why can resizing a warehouse slow the next queries slightly?', 'When a warehouse is resized or suspended, its local cache may be partly or '
         'fully lost, so the next queries read from remote storage until the cache warms up again.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('A query is slow. How do you use the Query Profile and QUERY_HISTORY to tune it?', 'Query Profile & Tuning', minutes=9, cards=[
    definition(
        defbox('The <strong>Query Profile</strong> (Snowsight → Query History → a query) shows the execution plan as a tree of operators '
               '(TableScan, Filter, Join, Aggregate, Sort…) with the percentage of time spent in each, plus statistics. '
               '<code>SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY</code> holds the same metrics for every query for a year.'),
        table(['Symptom in the profile', 'Likely cause', 'Typical fix'], [
            ['Bytes spilled to local / remote storage', 'Warehouse memory too small for the join / sort / aggregate', 'Larger warehouse; reduce data earlier'],
            ['Partitions scanned ≈ partitions total', 'No pruning on the filter column', 'Filter on the raw column; clustering key; search optimisation'],
            ['Join outputs far more rows than inputs', '"Exploding" join: missing or wrong join condition, duplicate keys', 'Fix the join keys; deduplicate'],
            ['Long queued time', 'Too many concurrent queries', 'Multi-cluster warehouse or separate warehouses'],
            ['Most time in a remote disk read', 'Cold cache', 'Keep related workloads on one warehouse'],
        ]),
        tags('Query Profile', 'QUERY_HISTORY', 'Spilling', 'Pruning', 'Exploding join', 'Queuing'),
    ),
    analogy('A <strong>doctor\'s report</strong>: do not guess the medicine. Look at which test is abnormal (spilling, pruning, queuing) and treat '
            'that cause.'),
    profile_anim(),
    real_world(
        scenario('A report that took 40 minutes',
                 p('The profile showed 92% of time in a Join that produced 1.2 billion rows from two inputs of 3 million and 40,000 rows. The '
                   '<code>exam_attempts</code> table had several attempts per student, and the join on <code>roll_no</code> alone multiplied them. '
                   'Joining on <code>(roll_no, attempt_no)</code> brought the query down to under a minute on the same warehouse.')),
    ),
    example(
        sql('''
CREATE TABLE attempts (roll_no INT, attempt_no INT, score INT);
INSERT INTO attempts VALUES (2401,1,55),(2401,2,78),(2402,1,88),(2405,1,90),(2405,2,94);

CREATE TABLE feedback (roll_no INT, attempt_no INT, rating INT);
INSERT INTO feedback VALUES (2401,1,3),(2401,2,4),(2402,1,5),(2405,1,4),(2405,2,5);

-- wrong: joined on roll_no only → rows multiply
SELECT COUNT(*) AS rows_out FROM attempts a JOIN feedback f ON a.roll_no = f.roll_no;

-- right: join on the full key
SELECT COUNT(*) AS rows_out FROM attempts a JOIN feedback f
  ON a.roll_no = f.roll_no AND a.attempt_no = f.attempt_no;
''', data=False, show='queries'),
        p('Five rows on each side produce 9 rows with the wrong key (2×2 for 2401, 1×1 for 2402, 2×2 for 2405) and 5 rows with the right key. '
          'On real data this is the difference between thousands and billions of rows.', top=True),
        sq('''
-- slowest queries of the last day with their key statistics (real account)
SELECT query_id, warehouse_name, total_elapsed_time/1000 AS secs,
       partitions_scanned, partitions_total,
       bytes_spilled_to_local_storage, bytes_spilled_to_remote_storage,
       queued_overload_time/1000 AS queued_s
FROM   SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE  start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP())
ORDER  BY total_elapsed_time DESC
LIMIT  10;
'''),
        title='Example: Spotting an Exploding Join'),
    steps(
        ('Find the query', 'Query History in Snowsight or QUERY_HISTORY ordered by elapsed time.'),
        ('Open the profile', 'Start at the most expensive operator.'),
        ('Read the statistics', 'Spilling, pruning ratio, rows in/out of joins, queued time.'),
        ('Apply the matching fix', 'Rewrite, recluster, resize or scale out; change one thing at a time.'),
        ('Compare', 'Re-run with USE_CACHED_RESULT = FALSE and compare elapsed time and credits.'),
        title='Steps'),
    crossq(
        ('What is the difference between local and remote spilling?', 'Data that does not fit in memory spills first to the warehouse\'s local SSD, '
         'then to remote cloud storage, which is much slower. Remote spilling is a strong signal to use a bigger warehouse or process less data.'),
        ('Does Snowflake have indexes to tune?', 'Not in the traditional sense. You influence performance through pruning (filters, clustering), '
         'warehouse size, query design and optional services such as search optimisation.'),
        ('What does EXPLAIN do in Snowflake?', 'It shows the logical plan (operators, estimated partitions) without running the query, useful to check '
         'pruning before running something expensive.'),
    ),
]),
])
