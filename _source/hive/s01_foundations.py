from build import *
from hive.anims import *
from hive.runner import hql, hq, sh, datafile

RUN_NOTE = note('Every HiveQL example with an Output box was really executed while building this page, on Spark SQL with Hive '
                'support (Hive 2.3 metastore and SerDes). Output is shown in Beeline\'s table style, and file paths are shown as they would '
                'appear on HDFS. Hive-only features (ACID, Tez settings) are shown without output.', 'How the examples were run')

SECTION = dict(level='beginner', title='Hive Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is Apache Hive? Why is it used?', 'What is Hive', minutes=7, cards=[
    definition(
        defbox('<strong>Apache Hive</strong> is a <strong>data warehouse system built on top of Hadoop</strong> that lets you query and '
               'manage large datasets stored in HDFS (or cloud storage) using a SQL-like language called <strong>HiveQL</strong>.',
               'Hive converts each query into distributed jobs (Tez, MapReduce or Spark) that run on the cluster. It was created at '
               '<strong>Facebook</strong> (2007–08) so analysts could use SQL on Hadoop instead of writing Java MapReduce programs, and '
               'became a top-level Apache project in 2010.'),
        tags('Hive', 'HiveQL', 'Data Warehouse', 'SQL on Hadoop', 'Batch Analytics', 'Metastore'),
    ),
    analogy('Think of HDFS as a <strong>huge library store-room</strong> full of boxes of loose papers (files). Finding anything means '
            'opening boxes by hand. Hive is the <strong>librarian with a catalogue</strong>: you ask a question in plain language '
            '(SQL), the librarian looks up in the catalogue (metastore) which boxes hold the answer, sends a team of assistants '
            '(parallel tasks) to read only those boxes, and hands you a neat summary. The papers never leave the store-room; '
            'the catalogue just describes them.'),
    hive_intro(),
    real_world(
        scenario('C-DAC: five years of exam data',
                 p('Every exam produces CSV exports of answers, marks and proctoring logs: billions of rows over the years, far too '
                   'much for a single MySQL server to scan. The files are copied to HDFS and exposed as Hive tables. Coordinators then '
                   'answer questions like "average marks per centre per module over 5 years" with one SQL query, which Hive runs in '
                   'parallel across the cluster.')),
        scenario('Industry',
                 p('Facebook built Hive for petabyte-scale log analysis; banks and telecoms run nightly regulatory and billing reports '
                   'in Hive; and the <strong>Hive Metastore</strong> is still the standard table catalogue used by Spark, Trino and '
                   'Impala even where Hive\'s query engine is not used.')),
    ),
    example(
        RUN_NOTE,
        hql('''
CREATE TABLE students (roll_no INT, name STRING, course STRING, marks INT)
STORED AS ORC;

INSERT INTO students VALUES
  (2401, 'Anuj', 'PG-DBDA', 78), (2402, 'Vineeta', 'PG-DBDA', 91),
  (2403, 'Aarshvi', 'PG-DAC', 84), (2404, 'Rohit', 'PG-DAC', 66);

SELECT course, COUNT(*) AS students, ROUND(AVG(marks), 1) AS avg_marks
FROM students
GROUP BY course;
'''),
        title='Example: Your First Hive Query'),
    steps(
        ('Open Beeline and connect to HiveServer2', '<code>beeline -u jdbc:hive2://localhost:10000 -n vineeta</code>'),
        ('Create (or choose) a database', '<code>CREATE DATABASE IF NOT EXISTS cdac; USE cdac;</code>'),
        ('Create a table', 'Define columns, types and storage format: <code>CREATE TABLE students (...) STORED AS ORC;</code>'),
        ('Load or insert data', '<code>INSERT INTO ...</code> for a few rows, <code>LOAD DATA INPATH</code> or an external table for files.'),
        ('Query it', 'Run a <code>SELECT</code>; watch the Tez job progress in Beeline and in the YARN UI (port 8088).'),
        title='Steps to Try It'),
    crossq(
        ('Is Hive a database?', 'Not in the OLTP sense. Hive stores no data itself; tables are files in HDFS/S3 plus metadata. It is a '
         'SQL engine and catalogue for <strong>batch analytics</strong>, with high latency (seconds to minutes) and no indexes.'),
        ('When should you not use Hive?', 'For low-latency lookups or row-by-row transactions (use an RDBMS or HBase), for sub-second '
         'interactive dashboards (Impala, Trino, Druid, or Hive LLAP), or for small data that fits in one database.'),
        ('Who uses HiveQL in a project?', 'Data engineers (building ETL and tables), analysts (reporting), and other engines: Spark SQL '
         'understands most HiveQL and reads Hive tables through the same metastore.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain the architecture of Hive.', 'Hive Architecture', minutes=9, cards=[
    definition(
        defbox('Hive has four layers: <strong>clients</strong> (Beeline, JDBC/ODBC), <strong>HiveServer2</strong> (the service clients connect to), '
               'the <strong>Driver</strong> (compiler, optimizer, executor) and the <strong>Metastore</strong> (table metadata in an RDBMS). '
               'Queries run on an <strong>execution engine</strong> (Tez, MapReduce or Spark) over <strong>HDFS/S3</strong>.'),
        table(['Component', 'Role'], [
            ['Beeline / JDBC / ODBC', 'Clients that submit HiveQL. The old <code>hive</code> CLI talked to the metastore directly and is deprecated.'],
            ['HiveServer2 (HS2)', 'Thrift service (port 10000) accepting concurrent sessions, with Kerberos/LDAP authentication'],
            ['Driver', 'Manages the query lifecycle: session, compile, optimise, execute, fetch'],
            ['Compiler', 'Parses HiveQL into an AST, checks semantics against metastore metadata, builds a logical plan'],
            ['Optimizer', 'Rule- and cost-based (Apache Calcite) rewriting: predicate pushdown, partition pruning, join reordering, map joins'],
            ['Executor', 'Submits the physical plan (DAG of stages) to the execution engine and tracks it'],
            ['Metastore (HMS)', 'Schemas, table locations, partitions, statistics; stored in MySQL/PostgreSQL/Oracle; Thrift service on port 9083'],
            ['Execution engine', 'Tez (default), MapReduce (deprecated) or Spark, on YARN'],
            ['Storage', 'HDFS, S3, ADLS… Hive tables are directories of files'],
        ]),
        tags('HiveServer2', 'Beeline', 'Driver', 'Compiler', 'Optimizer', 'Metastore', 'Tez', 'YARN'),
    ),
    analogy('A <strong>restaurant</strong>: customers (Beeline, BI tools) give orders to the <strong>waiter</strong> (HiveServer2). The '
            '<strong>head chef</strong> (Driver) reads the order, checks the <strong>recipe book and pantry list</strong> (Metastore: what '
            'ingredients exist and where they are), plans the cooking steps (compiler and optimizer), and the <strong>kitchen staff</strong> '
            '(Tez tasks on YARN) cook in parallel using ingredients from the <strong>cold store</strong> (HDFS). The recipe book contains no food; '
            'the cold store has no recipes.'),
    hive_arch(),
    real_world(
        scenario('A typical cluster layout',
                 ul('2 HiveServer2 instances behind ZooKeeper service discovery (high availability), on edge/master nodes.',
                    '2 Metastore services sharing one MySQL database, also used by Spark and Trino.',
                    'Queries run as Tez applications in a dedicated YARN queue (e.g. <code>analytics</code>).',
                    'Analysts connect from DBeaver/Power BI via JDBC/ODBC; Airflow submits ETL through Beeline.')),
    ),
    example(
        sh('''
# Connect with Beeline (JDBC URL to HiveServer2)
beeline -u "jdbc:hive2://hs2.cdac.local:10000/cdac" -n vineeta

# With ZooKeeper service discovery (HA HiveServer2)
beeline -u "jdbc:hive2://zk1:2181,zk2:2181,zk3:2181/;serviceDiscoveryMode=zooKeeper;zooKeeperNamespace=hiveserver2"

# Start services (on the server)
hive --service metastore &        # port 9083
hive --service hiveserver2 &      # port 10000, web UI 10002
''', 'Connecting and starting services'),
        title='Example'),
    steps(
        ('Set up the metastore database', 'Create a MySQL/PostgreSQL database and user for Hive.'),
        ('Configure hive-site.xml', '<code>javax.jdo.option.ConnectionURL</code>, driver, user/password; <code>hive.metastore.uris=thrift://host:9083</code>; <code>hive.execution.engine=tez</code>.'),
        ('Initialise the schema', '<code>schematool -dbType mysql -initSchema</code> creates the metastore tables.'),
        ('Start the Metastore, then HiveServer2', '<code>hive --service metastore</code>, <code>hive --service hiveserver2</code>.'),
        ('Connect and test', '<code>beeline -u jdbc:hive2://host:10000</code> then <code>SHOW DATABASES;</code>'),
        title='Steps to Set Up Hive'),
    crossq(
        ('Hive CLI vs Beeline?', 'The old Hive CLI ran the driver inside the client and accessed the metastore directly, bypassing '
         'HiveServer2 security. Beeline is a thin JDBC client to HiveServer2, supporting authentication, authorisation and concurrency. Beeline is the standard.'),
        ('HiveServer1 vs HiveServer2?', 'HS1 could not handle concurrent clients safely and had no proper authentication. HS2 (Hive 0.11+) '
         'supports multi-client concurrency, Kerberos/LDAP, and a JDBC/ODBC API. HS1 has been removed.'),
        ('What is Hive LLAP?', 'Live Long And Process: long-running daemons that cache data in memory and execute query fragments, giving '
         'interactive (sub-second to seconds) performance while still using Tez.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What happens internally when you run a Hive query?', 'Query Execution Flow', minutes=8, cards=[
    definition(
        defbox('A Hive query goes through <strong>parse → semantic analysis (with metastore lookups) → logical plan → optimisation → '
               'physical plan (DAG of stages) → execution on Tez/YARN → fetch results</strong>.'),
        tags('Query Lifecycle', 'AST', 'Logical Plan', 'Physical Plan', 'EXPLAIN', 'Stages'),
    ),
    analogy('Like an <strong>online food order</strong>: the app (Beeline) sends your order to the restaurant (HiveServer2); the manager '
            '(compiler) checks the menu and stock list (metastore), writes a ticket that splits the order into stations (plan with stages), '
            'the kitchen stations cook in parallel (Tez tasks), and the delivery partner brings the packed food back (fetch).'),
    query_flow(),
    real_world(
        scenario('Why understanding the flow matters',
                 p('A query that "hangs before starting" is usually stuck in compilation or metastore calls (e.g. a table with 100,000 '
                   'partitions). A query slow "at 99%" is an execution problem (skew). Knowing the phases tells you where to look.')),
    ),
    example(
        hql('''
CREATE TABLE marks (roll_no INT, subject STRING, marks INT) STORED AS ORC;
EXPLAIN
SELECT subject, AVG(marks) FROM marks WHERE marks >= 40 GROUP BY subject;
'''),
        p('Hive\'s own <code>EXPLAIN</code> lists <strong>STAGE DEPENDENCIES</strong> and <strong>STAGE PLANS</strong> (Tez vertices: Map 1 → Reducer 2) '
          'with operators such as TableScan, Filter Operator, Group By Operator and File Output Operator. The plan above is Spark SQL\'s '
          'equivalent; the idea is the same: scan → filter → partial aggregate → shuffle → final aggregate.'),
        hq('''
EXPLAIN EXTENDED   SELECT ...;   -- more detail (paths, serde)
EXPLAIN DEPENDENCY SELECT ...;   -- tables and partitions the query will read
EXPLAIN VECTORIZATION SELECT ...;
''', 'Other EXPLAIN forms in Hive'),
        title='Example: Look at the Plan'),
    steps(
        ('Write the query', 'Start with the business question and the filter columns.'),
        ('Run <code>EXPLAIN</code>', 'Check that partition filters appear (pruning) and which join strategy was chosen.'),
        ('Run the query', 'Watch the Tez progress bars per vertex in Beeline.'),
        ('Check the Tez/YARN UI', 'Look at the slowest vertex and tasks if it is slow.'),
        title='Steps to Analyse a Query'),
    crossq(
        ('Does every Hive query launch a job?', 'No. Simple queries such as <code>SELECT * FROM t LIMIT 10</code> or filters on partition '
         'columns can be answered by a <strong>fetch task</strong> that reads files directly (<code>hive.fetch.task.conversion=more</code>). '
         'Metadata commands (SHOW, DESCRIBE) never launch jobs.'),
        ('What is a stage in Hive?', 'A unit of the plan: a Tez DAG, a MapReduce job, a move of files into the table, a stats task, etc. '
         'EXPLAIN shows them and their dependencies.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('How is Hive different from an RDBMS like MySQL?', 'Hive vs RDBMS', minutes=7, cards=[
    comparison(
        table(['Aspect', 'RDBMS (MySQL, Oracle)', 'Hive'], [
            ['Purpose', 'OLTP: many small transactions', 'OLAP: analytics over huge data'],
            ['Schema', '<strong>Schema-on-write</strong>: data validated on insert', '<strong>Schema-on-read</strong>: applied when reading'],
            ['Data size', 'GBs – few TBs', 'TBs – PBs'],
            ['Latency', 'Milliseconds', 'Seconds to minutes'],
            ['Updates / deletes', 'Row-level, everywhere', 'Only on ACID (transactional ORC) tables; normally INSERT OVERWRITE'],
            ['Indexes', 'B-tree indexes', 'None (removed in Hive 3); uses partitioning, bucketing, ORC indexes'],
            ['Constraints', 'Enforced PK/FK/NOT NULL', 'PK/FK declarable but <strong>not enforced</strong> (hints for the optimizer)'],
            ['Storage', 'Own storage engine', 'Files in HDFS/S3 in open formats'],
            ['Scaling', 'Mostly vertical', 'Horizontal (add nodes)'],
        ]),
        tags('Schema-on-read', 'OLAP', 'OLTP', 'Latency', 'ACID'),
    ),
    analogy('An RDBMS is a <strong>bank teller</strong>: fast, precise, one customer and one account at a time, and every form is checked '
            'before it is accepted. Hive is the bank\'s <strong>auditor</strong>: slow to start, but able to read every transaction of the last '
            'ten years in one go and summarise it. You would not ask the auditor to withdraw ₹500 for you.'),
    write_vs_read(),
    real_world(
        scenario('Both in one system',
                 p('The C-DAC admission portal stores applications in <strong>MySQL</strong> (each form submission is a transaction). Each '
                   'night the day\'s rows are exported to HDFS into a Hive table partitioned by date, where years of applications are '
                   'analysed (applications per state per year, conversion to admission).')),
    ),
    example(
        hql('''
-- Hive accepts constraints, but does NOT enforce them
CREATE TABLE centres (centre_id INT, name STRING,
  PRIMARY KEY (centre_id) DISABLE NOVALIDATE)
STORED AS ORC;
''', expect_error=True),
        p('On Hive 3 this statement succeeds and duplicate <code>centre_id</code> values can still be inserted: the constraint is metadata only '
          '(<code>DISABLE NOVALIDATE</code> is mandatory). Spark SQL, used to run these examples, rejects Hive\'s <code>DISABLE NOVALIDATE</code> '
          'syntax (error above), another reminder that such constraints are engine-specific optimizer hints, not guarantees.'),
        title='Example: Constraints Are Not Enforced'),
    steps(
        ('Keep transactions in the RDBMS', 'Applications write to MySQL/PostgreSQL.'),
        ('Extract daily', 'Spark JDBC, Sqoop (legacy) or CDC with Debezium/Kafka.'),
        ('Land in HDFS', 'Write Parquet/ORC into a date-partitioned folder.'),
        ('Expose in Hive', 'External or managed partitioned table; <code>MSCK REPAIR</code> or <code>ADD PARTITION</code>.'),
        ('Analyse', 'Reports and dashboards query Hive/Trino, never the live database.'),
        title='Steps: Moving Data From an RDBMS to Hive'),
    crossq(
        ('Why doesn\'t Hive have indexes?', 'Hive scans large files in parallel; partition pruning, bucketing and the min/max/bloom-filter '
         'indexes inside ORC/Parquet files skip data more effectively. The old Hive indexes were rarely useful and were removed in Hive 3.'),
        ('Can Hive do UPDATE and DELETE?', 'Yes, since Hive 0.14, but only on <strong>transactional</strong> (ACID) ORC tables. It writes delta files rather than changing rows in place. See the ACID question.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('Hive vs Spark SQL vs Impala/Trino: when do you use which?', 'Hive vs Spark SQL vs Trino', minutes=7, cards=[
    comparison(
        table(['Aspect', 'Hive (on Tez)', 'Spark SQL', 'Impala / Trino (Presto)'], [
            ['Main strength', 'Large, reliable batch ETL; the metastore catalogue', 'ETL + ML + streaming in one engine; Python API', 'Interactive, low-latency SQL'],
            ['Latency', 'Seconds–minutes (LLAP: seconds)', 'Seconds–minutes', 'Sub-second–seconds'],
            ['Execution', 'Tez DAG on YARN, writes to disk between stages when needed', 'In-memory DAG, spills to disk', 'MPP daemons, pipelined in memory'],
            ['Fault tolerance mid-query', 'Yes (task retry)', 'Yes (lineage)', 'Limited (query restarts; Trino has optional fault-tolerant mode)'],
            ['Uses Hive Metastore?', 'Yes (it is the owner)', 'Yes', 'Yes'],
            ['Typical use', 'Nightly warehouse loads, long heavy queries', 'Data pipelines, feature engineering', 'BI dashboards, ad-hoc exploration'],
        ]),
        tags('Spark SQL', 'Trino', 'Presto', 'Impala', 'LLAP', 'Hive Metastore'),
    ),
    analogy('Three vehicles on the same roads (the same tables in the metastore): Hive is a <strong>goods train</strong>, slow to start but '
            'carries enormous loads reliably; Spark is a <strong>truck</strong>, flexible and fast for most deliveries; Trino/Impala is a '
            '<strong>motorbike courier</strong>, very quick for small urgent trips but not for moving a warehouse.'),
    shared_catalog_anim(),
    real_world(
        scenario('One catalogue, three engines',
                 p('A bank defines all its tables once in the Hive Metastore. Overnight ETL runs in Hive/Spark; analysts explore with Trino '
                   'from DBeaver; Power BI dashboards hit Impala. Everyone sees the same table names and data files.')),
    ),
    example(
        hql('''
CREATE TABLE placements (roll_no INT, company STRING, ctc_lpa DOUBLE) STORED AS PARQUET;
INSERT INTO placements VALUES (2401, 'TCS', 7.5), (2402, 'Infosys', 9.0), (2403, 'TCS', 8.2);
-- The same table, readable by Hive, Spark and Trino through the metastore
SELECT company, COUNT(*) AS hires, MAX(ctc_lpa) AS best_ctc FROM placements GROUP BY company ORDER BY hires DESC;
'''),
        sh('''
# Spark reading the Hive table
spark.sql("SELECT company, COUNT(*) FROM cdac.placements GROUP BY company").show()

# Trino reading the same table (hive connector -> same metastore)
trino> SELECT company, count(*) FROM hive.cdac.placements GROUP BY company;
''', 'Same table from other engines'),
        title='Example'),
    steps(
        ('Point every engine at one metastore', '<code>hive.metastore.uris=thrift://hms:9083</code> in Spark/Trino config.'),
        ('Store tables in open formats', 'ORC or Parquet, so all engines read them efficiently.'),
        ('Choose the engine per workload', 'Heavy batch → Hive/Spark; interactive → Trino/Impala/LLAP.'),
        title='Steps to Share Tables Across Engines'),
    crossq(
        ('Is Hive being replaced by Spark?', 'For new ETL code, Spark (or dbt on a warehouse) is more common. But the <strong>Hive Metastore</strong> '
         'remains the de-facto catalogue, Hive is still heavily used in on-prem Cloudera estates, and HiveQL knowledge transfers directly to Spark SQL.'),
    ),
]),
])
