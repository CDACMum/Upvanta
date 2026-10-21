from build import *
from snowflakedb.anims import *
from snowflakedb.runner import sql, sq, sh, conf

RUN_NOTE = note('Snowflake is a cloud-only service, so every example with an Output box was executed while this page was built on '
                '<strong>fakesnow</strong>, an open-source Snowflake emulator, through the real <code>snowflake-connector-python</code> '
                'driver. The output is shown in SnowSQL table format (the "Time Elapsed" part of the footer is left out). Features '
                'that need a real account (warehouses, Time Travel, streams, tasks, Snowpipe, sharing, access policies) are marked '
                '"shown, not executed". Every example uses the same small table, <code>CDAC.BDA.STUDENTS</code> (8 rows).',
                'How the examples were run')

SECTION = dict(level='beginner', title='Snowflake Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is Snowflake? What are its key features and when should you use it?', 'What is Snowflake', minutes=8, cards=[
    definition(
        defbox('<strong>Snowflake</strong> is a fully managed <strong>cloud data platform</strong> offered as software-as-a-service. It began as '
               'a cloud <strong>data warehouse</strong> and now also covers data lakes (Apache Iceberg tables), data engineering, data '
               'sharing and machine learning. It runs on <strong>AWS, Microsoft Azure and Google Cloud</strong>; you choose the cloud and '
               'region when the account is created.',
               'Key features: <strong>separate storage and compute</strong> that scale independently, <strong>near-zero administration</strong> '
               '(no indexes, vacuuming, distribution keys or hardware), per-second billing, automatic <strong>micro-partitioning</strong>, native '
               'semi-structured data (<code>VARIANT</code>), <strong>Time Travel</strong>, <strong>zero-copy cloning</strong> and '
               '<strong>secure data sharing</strong> across accounts.'),
        tags('Cloud data warehouse', 'SaaS', 'Separation of storage & compute', 'ANSI SQL', 'AWS / Azure / GCP', 'VARIANT', 'Time Travel'),
    ),
    analogy('A traditional warehouse is a <strong>company-owned delivery fleet</strong>: you buy trucks, hire mechanics and pay for them even when '
            'idle. Snowflake is a <strong>ride-hailing app</strong> for queries: cars appear when you need them, you pay per minute of the ride, '
            'and someone else looks after the vehicles.'),
    what_is_snowflake_anim(),
    comparison(
        table(['Use Snowflake when…', 'Think twice when…'], [
            ['Many teams run SQL analytics on the same data', 'You need a transactional (OLTP) database with millisecond single-row updates'],
            ['Workloads are spiky: heavy at month-end, quiet otherwise', 'Data is tiny and one PostgreSQL server is enough'],
            ['You load JSON / Parquet and want to query it with SQL', 'You must run fully on-premises with no cloud'],
            ['You need to share live data with partners', 'Cost must be fixed and predictable without any monitoring'],
        ]),
        title='When to Use It'),
    real_world(
        scenario('Who uses it',
                 ul('Thousands of companies across retail, finance, healthcare and media use Snowflake for reporting and data sharing.',
                    'Typical users are data engineers loading data with SQL and dbt, analysts on Power BI or Tableau, and data scientists using Python.',
                    'At C-DAC scale: exam, attendance and placement data from every centre can land in one account. Each team gets its own warehouse, '
                    'so the placement cell\'s dashboards never slow down the exam cell\'s result processing.')),
    ),
    example(
        RUN_NOTE,
        sql('''
SELECT * FROM students ORDER BY roll_no;

SELECT course,
       COUNT(*)                AS students,
       AVG(marks)::NUMBER(6,2) AS avg_marks
FROM   students
GROUP  BY course
ORDER  BY avg_marks DESC;
'''),
        p('The SQL is ordinary ANSI SQL. Notice that the column headers come back in UPPER case: Snowflake stores unquoted identifiers in '
          'upper case.', top=True),
        title='Example: Your First Queries'),
    steps(
        ('Sign up for a trial', 'Go to signup.snowflake.com, choose an edition, a cloud and a region close to you (for example AWS Mumbai).'),
        ('Open Snowsight', 'The web UI: worksheets for SQL, data browser, query history and cost views.'),
        ('Create a warehouse and database', '<code>CREATE WAREHOUSE lab_wh WAREHOUSE_SIZE = \'XSMALL\' AUTO_SUSPEND = 60;</code> then '
         '<code>CREATE DATABASE cdac;</code>'),
        ('Create and load a table', 'Create a table, then INSERT rows or load a CSV with the Snowsight "Load data" wizard.'),
        ('Query', 'Run SELECT statements in a worksheet. Suspend the warehouse when done.'),
        title='Steps to Try It'),
    crossq(
        ('Is Snowflake built on Hadoop or an open-source database?', 'No. It is a new SQL engine designed for the cloud, with its own storage '
         'format on top of the cloud provider\'s object storage (S3, Azure Blob, Google Cloud Storage).'),
        ('Is Snowflake OLTP or OLAP?', 'Mainly OLAP: large scans and aggregations. Hybrid tables (part of "Unistore") add row-level lookups '
         'and enforced primary keys for light transactional use, but it is not a replacement for MySQL or PostgreSQL in an application.'),
        ('Can you install Snowflake on your own servers?', 'No. It is only available as a cloud service. You can choose the cloud provider and '
         'region, not the hardware.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain Snowflake\'s architecture: storage, compute and cloud services layers.', 'Three-Layer Architecture', minutes=9, cards=[
    definition(
        table(['Layer', 'What it does', 'Billed as'], [
            ['Database Storage', 'Keeps all table data as compressed, columnar <strong>micro-partitions</strong> in cloud object storage. '
             'Snowflake manages organisation, compression and statistics.', 'TB per month'],
            ['Query Processing (compute)', '<strong>Virtual warehouses</strong>: MPP clusters that execute queries. Each warehouse is '
             'independent and can be started, stopped and resized at any time.', 'credits per second'],
            ['Cloud Services', 'The "brain": authentication, access control, metadata, query parsing and optimisation, transactions, '
             'result cache.', 'free up to 10% of daily compute'],
        ]),
        defbox('Snowflake calls this a <strong>multi-cluster, shared-data</strong> architecture. Like <em>shared-disk</em> systems, all '
               'compute sees one copy of the data; like <em>shared-nothing</em> MPP systems, each warehouse processes its share of the '
               'data in parallel on local CPU, memory and SSD cache.'),
        tags('Storage layer', 'Compute layer', 'Cloud services', 'Micro-partitions', 'Virtual warehouse', 'Shared data'),
    ),
    analogy('A <strong>public library</strong>: the book stacks are the storage layer (one copy for everyone), the reading rooms are warehouses '
            '(open as many as you like, each with its own seats), and the front desk with the catalogue is the cloud services layer that '
            'checks your card and tells you where everything is.'),
    architecture_anim(),
    real_world(
        scenario('Workload isolation at a training centre',
                 p('The nightly ETL that loads exam submissions runs on <code>ETL_WH</code> (Medium). Faculty dashboards use <code>BI_WH</code> '
                   '(Small). A data-science intern experimenting with heavy joins uses <code>DS_WH</code>. All three read the same tables, '
                   'but none slows down the others, and each is billed only while it runs.')),
    ),
    example(
        sq('''
-- each workload gets its own compute
CREATE WAREHOUSE etl_wh WAREHOUSE_SIZE = 'MEDIUM' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
CREATE WAREHOUSE bi_wh  WAREHOUSE_SIZE = 'SMALL'  AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;

USE WAREHOUSE bi_wh;      -- the session now runs queries on BI_WH
SELECT CURRENT_WAREHOUSE(), CURRENT_ROLE();
'''),
        sql('''
-- the same data is visible no matter which warehouse runs the query
SELECT CURRENT_DATABASE() AS db,
       CURRENT_SCHEMA()   AS sch,
       COUNT(*)           AS rows_in_students
FROM   students;
''', show='queries'),
        title='Example'),
    steps(
        ('Identify workloads', 'Loading, transformation, BI, data science, ad hoc.'),
        ('Create one warehouse per workload', 'Size each for its queries; set AUTO_SUSPEND and AUTO_RESUME.'),
        ('Grant USAGE on each warehouse to the right role', 'So analysts cannot run on the ETL warehouse.'),
        ('Keep all data in shared databases', 'No copies per team; access is controlled by roles.'),
        title='Steps to Apply It'),
    crossq(
        ('Where is the data physically stored?', 'In the cloud provider\'s object storage in your account\'s region (S3, Azure Blob or GCS), '
         'but in Snowflake\'s internal format. You cannot read those files directly; you access them only through Snowflake.'),
        ('What happens to data when all warehouses are suspended?', 'Nothing: data lives in the storage layer. Suspending compute only stops '
         'billing for compute. Some queries (metadata, result cache) still answer without a warehouse.'),
        ('Is Snowflake shared-nothing or shared-disk?', 'A hybrid: shared data (one central copy) plus shared-nothing MPP compute clusters '
         'with local caches.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('How is Snowflake priced? Explain credits, editions and how warehouse size affects cost.', 'Pricing & Credits', minutes=8, cards=[
    definition(
        defbox('You pay for three things: <strong>compute</strong> (credits used by warehouses and serverless features), <strong>storage</strong> '
               '(average compressed TB per month) and <strong>data transfer</strong> out of the region or cloud. A <strong>credit</strong> is the '
               'unit of compute; its price in money depends on the <strong>edition</strong>, cloud, region and contract.'),
        table(['Edition', 'Adds (main points)'], [
            ['Standard', 'Core SQL warehouse, Time Travel up to 1 day, secure data sharing.'],
            ['Enterprise', 'Multi-cluster warehouses, Time Travel up to 90 days, materialized views, search optimisation, masking and row '
             'access policies.'],
            ['Business Critical', 'Higher security and compliance (e.g. HIPAA, PCI), private connectivity, Tri-Secret Secure keys, '
             'database failover.'],
            ['Virtual Private Snowflake (VPS)', 'A completely separate Snowflake environment for the most sensitive customers.'],
        ]),
        tags('Credits', 'Per-second billing', '60-second minimum', 'Editions', 'Serverless', 'Storage per TB'),
    ),
    analogy('Warehouse sizes are like <strong>taxis by the minute</strong>: a 4-seater costs 1 unit per minute, an 8-seater 2 units. If the bigger car '
            'finishes the trip in half the time, you pay exactly the same and arrive earlier.'),
    pricing_anim(),
    real_world(
        scenario('Month-end result processing',
                 p('Result processing takes 40 minutes on a Medium warehouse (4 credits/hour = 2.67 credits). On a Large warehouse it finishes '
                   'in about 20 minutes (8 credits/hour = 2.67 credits): same cost, results published 20 minutes earlier. Scaling up is only '
                   'wasteful when the query does not get faster, for example when it is already small or limited by a single-threaded step.')),
    ),
    example(
        sql('''
-- credits = credits_per_hour × billed seconds / 3600, minimum 60 s per resume
SELECT size,
       credits_per_hour,
       run_seconds,
       (GREATEST(run_seconds, 60) * credits_per_hour / 3600)::NUMBER(8,4) AS credits_billed
FROM VALUES ('X-Small', 1,   45),
            ('X-Small', 1,  600),
            ('Medium',  4, 2400),
            ('Large',   8, 1200)
     AS t(size, credits_per_hour, run_seconds);
''', data=False),
        p('The 45-second X-Small run is billed as 60 seconds (0.0167 credits). The Medium and Large rows show the same job at two sizes: '
          '2.6667 credits either way.', top=True),
        sq('''
-- real account: credits actually used per warehouse in the last 30 days
SELECT warehouse_name, SUM(credits_used) AS credits
FROM   SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE  start_time >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP  BY warehouse_name
ORDER  BY credits DESC;
'''),
        title='Example: Estimating Credits'),
    steps(
        ('Pick an edition', 'Enterprise if you need multi-cluster warehouses, long Time Travel or masking policies.'),
        ('Choose the region', 'Close to your users and data sources; prices differ by region.'),
        ('Start small', 'X-Small or Small; scale up only when the Query Profile shows the need.'),
        ('Set auto-suspend and resource monitors', 'Stop idle spending and cap the monthly credits.'),
        ('Review usage weekly', 'ACCOUNT_USAGE views or the Snowsight cost management pages.'),
        title='Steps to Control Cost from Day One'),
    crossq(
        ('Is storage or compute usually the bigger bill?', 'For most customers compute (credits) is the larger part. Storage is billed on compressed '
         'size, which is typically several times smaller than the raw data.'),
        ('What are on-demand and capacity pricing?', 'On-demand: pay monthly for what you use at list price. Capacity: commit to an amount in advance '
         'for a lower price per credit.'),
        ('Do you pay when a query is answered from the result cache?', 'No warehouse credits are used. Only cloud services work is done, which is '
         'free unless it exceeds 10% of that day\'s warehouse usage.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('Describe the Snowflake object hierarchy. How do databases, schemas and identifiers work?', 'Objects & Identifiers', minutes=7, cards=[
    definition(
        table(['Level', 'Objects'], [
            ['Organization', 'Accounts (one per region/cloud/edition), billing across accounts.'],
            ['Account', 'Users, roles, warehouses, resource monitors, databases, integrations, shares.'],
            ['Database', 'Schemas. Holds no compute.'],
            ['Schema', 'Tables, views, stages, file formats, sequences, streams, tasks, pipes, UDFs, stored procedures, dynamic tables.'],
        ]),
        defbox('Objects are named <code>database.schema.object</code>. <strong>Unquoted identifiers are stored and resolved in UPPER case</strong>, '
               'so <code>students</code>, <code>Students</code> and <code>STUDENTS</code> are the same table. A <strong>double-quoted</strong> '
               'identifier (<code>"Students"</code>) is case-sensitive and must be quoted every time it is used.',
               'Every database also contains an <code>INFORMATION_SCHEMA</code> with views describing its objects. Account-wide history is in '
               'the shared <code>SNOWFLAKE.ACCOUNT_USAGE</code> schema.'),
        tags('Organization', 'Account', 'Database', 'Schema', 'Fully qualified name', 'INFORMATION_SCHEMA'),
    ),
    analogy('An <strong>address</strong>: country (organization), city (account), building (database), floor (schema), room (table). '
            '"Room 12" is ambiguous; "C-DAC Kharghar, 3rd floor, room 12" is not.'),
    hierarchy_anim(),
    real_world(
        scenario('Database per domain, schema per layer',
                 p('C-DAC Mumbai keeps one database per domain (<code>EXAM</code>, <code>ATTENDANCE</code>, <code>PLACEMENT</code>) and '
                   'inside each a schema per layer (<code>RAW</code>, <code>CLEAN</code>, <code>MART</code>). Grants can then be given '
                   'per schema: analysts read <code>MART</code> only.')),
    ),
    example(
        sql('''
CREATE SCHEMA exam;                       -- also becomes the current schema
CREATE TABLE cdac.exam.papers (paper_id INT, subject VARCHAR);
USE SCHEMA cdac.bda;

SELECT table_schema, table_name, table_type
FROM   cdac.information_schema.tables
WHERE  table_schema IN ('BDA', 'EXAM')
ORDER  BY table_schema, table_name;

-- unquoted names are case-insensitive: all three are the same table
SELECT COUNT(*) AS n1 FROM students;
SELECT COUNT(*) AS n2 FROM STUDENTS;
SELECT COUNT(*) AS n3 FROM cdac.bda.Students;
''', show='queries'),
        title='Example'),
    steps(
        ('Plan names', 'Database per domain or environment (DEV/PROD), schema per layer or team.'),
        ('Avoid quoted identifiers', 'Keep names unquoted and use snake_case so case never matters.'),
        ('Set the context', '<code>USE ROLE</code>, <code>USE WAREHOUSE</code>, <code>USE DATABASE</code>, <code>USE SCHEMA</code>, or '
         'always use fully qualified names in scripts.'),
        ('Explore', 'Query <code>INFORMATION_SCHEMA</code> views or use SHOW commands such as <code>SHOW TABLES IN SCHEMA cdac.bda;</code>'),
        title='Steps'),
    crossq(
        ('What is the difference between INFORMATION_SCHEMA and ACCOUNT_USAGE?', 'INFORMATION_SCHEMA is per database, real-time, and keeps limited '
         'history (e.g. 7 to 14 days of query history depending on the function). ACCOUNT_USAGE is account-wide, has 45 minutes to 3 hours of '
         'latency, keeps 1 year of history and includes dropped objects.'),
        ('Why would someone use double-quoted identifiers?', 'Usually by accident: tools that create tables from mixed-case DataFrame columns. '
         'Then every query must write <code>"rollNo"</code> exactly. Upper-casing column names before loading avoids this.'),
        ('Can a query join tables from two databases?', 'Yes, if the role has access: <code>SELECT … FROM exam.raw.papers p JOIN placement.mart.offers o …</code>. '
         'Databases are only namespaces.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What are permanent, transient and temporary tables? When would you use each?', 'Table Types', minutes=7, cards=[
    definition(
        defbox('<strong>Permanent</strong> tables (the default) get full Continuous Data Protection: Time Travel (1 day by default, up to 90 on '
               'Enterprise) plus 7 days of <strong>Fail-safe</strong>. <strong>Transient</strong> tables persist until dropped and are visible '
               'to all sessions, but have at most 1 day of Time Travel and <strong>no Fail-safe</strong>. <strong>Temporary</strong> tables '
               'exist only for the current session and are dropped automatically when it ends.',
               'Databases and schemas can also be created as <code>TRANSIENT</code>; every table inside them is then transient. Snowflake '
               'additionally offers <strong>external</strong>, <strong>Iceberg</strong>, <strong>dynamic</strong> and <strong>hybrid</strong> tables '
               'for special purposes.'),
        tags('Permanent', 'Transient', 'Temporary', 'Fail-safe', 'Time Travel', 'Storage cost'),
    ),
    analogy('<strong>Permanent</strong> is a document in a bank locker with a backup copy. <strong>Transient</strong> is a document in your office '
            'drawer: it stays until you throw it out, but there is no backup. <strong>Temporary</strong> is a sticky note on your desk that the '
            'cleaner throws away when you leave.'),
    table_types_anim(),
    real_world(
        scenario('Cutting storage on staging data',
                 p('A pipeline truncates and reloads <code>STG_ATTENDANCE</code> every hour. As a permanent table, every reload keeps the old '
                   'data in Time Travel and then 7 more days in Fail-safe, so storage is billed many times over. Making it transient, with '
                   '<code>DATA_RETENTION_TIME_IN_DAYS = 0</code>, removes that cost; the data can always be reloaded from source files.')),
    ),
    example(
        sql('''
CREATE TRANSIENT TABLE stg_attendance (roll_no INT, att_date DATE, present BOOLEAN);
CREATE TEMPORARY TABLE scratch_toppers AS
  SELECT roll_no, name, marks FROM students WHERE marks >= 85;

SELECT * FROM scratch_toppers ORDER BY marks DESC;
''', show='all'),
        p('<code>SCRATCH_TOPPERS</code> vanishes when this session ends. In a real account, <code>SHOW TABLES</code> also shows the '
          '<code>kind</code> column (TABLE, TRANSIENT, TEMPORARY) and <code>retention_time</code>.', top=True),
        sq('''
ALTER TABLE stg_attendance SET DATA_RETENTION_TIME_IN_DAYS = 0;   -- no Time Travel either
CREATE TRANSIENT SCHEMA staging;                                 -- all tables inside are transient
'''),
        title='Example'),
    steps(
        ('Classify each table', 'Can it be rebuilt from source? If yes, it is a candidate for transient.'),
        ('Use temporary tables inside scripts', 'For intermediate results needed only during one session or stored procedure.'),
        ('Keep business data permanent', 'Fact and dimension tables, anything that cannot be regenerated.'),
        ('Tune retention', 'Longer Time Travel on critical tables, 0–1 day on scratch tables.'),
        title='Steps'),
    crossq(
        ('Can you convert a permanent table to transient?', 'Not with ALTER TABLE. Create a new transient table with '
         '<code>CREATE TRANSIENT TABLE t_new AS SELECT * FROM t</code>, then swap the names with <code>ALTER TABLE t SWAP WITH t_new</code>.'),
        ('What if a temporary table has the same name as a permanent table?', 'The temporary table takes precedence in that session and hides the '
         'permanent one, which can cause confusing results. Use distinct names.'),
        ('Do temporary tables cost money?', 'Yes, storage is billed while they exist (and up to 1 day of Time Travel if set), but they are dropped '
         'when the session ends.'),
    ),
]),
])
