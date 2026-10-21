from build import *
from dbxq.anims import *
from dbxq.runner import sql, sq, pyrun, py, sh, conf

CCEE = {
    '/Volumes/cdac/bda/landing/ccee/kharghar.json':
        '{"roll_no": 2401, "name": "Anuj",  "course": "PGCP-BDA", "centre": "Kharghar", "subject": "SQL",    "marks": 72}\n'
        '{"roll_no": 2401, "name": "Anuj",  "course": "PGCP-BDA", "centre": "Kharghar", "subject": "Python", "marks": 64}\n'
        '{"roll_no": 2405, "name": "Sana",  "course": "PGCP-BDA", "centre": "Kharghar", "subject": "SQL",    "marks": 95}\n'
        '{"roll_no": 2405, "name": "Sana",  "course": "PGCP-BDA", "centre": "Kharghar", "subject": "Python", "marks": 89}\n'
        '{"roll_no": 2403, "name": "Riya",  "course": "PGCP-AI",  "centre": "Kharghar", "subject": "ML",     "marks": 91}\n'
        '{"roll_no": 2403, "name": "Riya",  "course": "PGCP-AI",  "centre": "Kharghar", "subject": "Python", "marks": 120}\n',
    '/Volumes/cdac/bda/landing/ccee/juhu.json':
        '{"roll_no": 2402, "name": "Aarshvi", "course": "PGCP-BDA", "centre": "Juhu", "subject": "SQL",    "marks": 88}\n'
        '{"roll_no": 2402, "name": "Aarshvi", "course": "PGCP-BDA", "centre": "Juhu", "subject": "Python", "marks": 90}\n'
        '{"roll_no": 2408, "name": "Tejas",   "course": "PGCP-BDA", "centre": "Juhu", "subject": "SQL",    "marks": 38}\n'
        '{"roll_no": 2408, "name": "Tejas",   "course": "PGCP-BDA", "centre": "Juhu", "subject": "Python", "marks": 61}\n'
        '{"roll_no": 2406, "name": "Omkar",   "course": "PGCP-AI",  "centre": "Juhu", "subject": "ML",     "marks": 77}\n'
        '{"roll_no": 2406, "name": "Omkar",   "course": "PGCP-AI",  "centre": "Juhu", "subject": "Python", "marks": 81}\n',
}

SCD = """
CREATE TABLE dim_student (roll_no INT, name STRING, centre STRING, start_date DATE, end_date DATE, is_current BOOLEAN);
INSERT INTO dim_student VALUES
  (2401, 'Anuj',  'Kharghar', DATE'2026-02-02', NULL, true),
  (2404, 'Kabir', 'Kharghar', DATE'2026-02-03', NULL, true),
  (2407, 'Meera', 'Juhu',     DATE'2026-02-05', NULL, true);
CREATE TABLE student_updates AS SELECT * FROM VALUES
  (2404, 'Kabir', 'Juhu',     DATE'2026-03-10'),
  (2407, 'Meera', 'Juhu',     DATE'2026-03-10'),
  (2409, 'Zoya',  'Kharghar', DATE'2026-03-10')
  AS u(roll_no, name, centre, effective_date);
"""

SECTION = dict(level='expert', title='Databricks SQL, Cost & Real-World Scenarios', questions=[

# ------------------------------------------------------------------ 36
Q('What is Databricks SQL? Explain SQL warehouses, dashboards and connecting BI tools.', 'Databricks SQL & Warehouses', minutes=8, cards=[
    definition(
        defbox('<strong>Databricks SQL</strong> (DBSQL) is the data-warehousing part of the platform: a SQL editor, query history and profiles, '
               'alerts, <strong>AI/BI dashboards</strong>, <strong>Genie</strong> spaces (ask questions in natural language over curated tables), and '
               'connectivity for BI tools (Power BI, Tableau, Looker, Excel) through JDBC/ODBC and partner connectors.',
               'Queries run on <strong>SQL warehouses</strong>: compute dedicated to SQL with Photon, result and disk caching, and '
               '<strong>intelligent workload management</strong> that scales out across clusters when many users query at once. Types: '
               '<strong>serverless</strong> (starts in seconds, recommended), <strong>pro</strong> and <strong>classic</strong> (both run in your '
               'cloud account). A warehouse has a size (2X-Small … 4X-Large), min/max clusters for concurrency and an auto-stop time.'),
        tags('Databricks SQL', 'SQL warehouse', 'Serverless', 'Photon', 'AI/BI dashboards', 'Genie', 'JDBC/ODBC', 'Query profile'),
    ),
    analogy('A SQL warehouse is like a <strong>reading room with extra desks that open automatically</strong> when many students arrive before '
            'an exam, and close when the room empties; you pay only while desks are in use.'),
    sqlwh_anim(),
    real_world(
        scenario('Result-day dashboards',
                 p('On result day, 300 coordinators open the CCEE dashboard within an hour. A serverless SQL warehouse of size Small with '
                   '<code>min 1, max 6</code> clusters scales out for the rush and auto-stops after 10 idle minutes. Popular tiles are answered '
                   'from the result cache; Power BI reports connect to the same warehouse in DirectQuery mode with the coordinator\'s own '
                   'permissions.')),
    ),
    example(
        sq('''
-- a query behind a dashboard tile (parameter :course from a dashboard filter)
SELECT centre,
       COUNT(DISTINCT roll_no)                AS students,
       ROUND(AVG(total), 1)                   AS avg_total,
       COUNT_IF(result = 'PASS') / COUNT(*)   AS pass_rate
FROM   cdac.gold.rank_list
WHERE  course = :course
GROUP  BY centre
ORDER  BY pass_rate DESC;

-- slow dashboards? check the query history system table
SELECT statement_text, total_duration_ms, read_bytes, executed_by
FROM   system.query.history
WHERE  compute.warehouse_id = '1234abcd5678ef90'
ORDER  BY total_duration_ms DESC
LIMIT  10;
'''),
        conf('''
Server hostname : adb-1234567890123456.7.azuredatabricks.net
Port            : 443
HTTP path       : /sql/1.0/warehouses/1234abcd5678ef90
Authentication  : OAuth (Microsoft Entra ID) or personal access token
Catalog/schema  : cdac.gold
''', title='Power BI / Tableau connection details'),
        title='Example'),
    steps(
        ('Create a warehouse', 'Serverless, size Small to start, auto-stop 10 minutes, max clusters for peak users.'),
        ('Model gold tables', 'Pre-aggregated, clustered on the filter columns used by dashboards.'),
        ('Build dashboards', 'AI/BI dashboard with parameters; or connect Power BI with the warehouse\'s HTTP path.'),
        ('Govern', 'Users query with their own identity, so Unity Catalog grants, row filters and masks apply.'),
        ('Tune', 'Use query profiles and system.query.history; resize or add clusters only after looking.'),
        title='Steps'),
    crossq(
        ('Scale up or scale out a SQL warehouse?', 'Increase the size when single queries are slow (spill, large joins). Increase max clusters when '
         'queries wait in the queue because many users run them at once.'),
        ('Can a SQL warehouse run Python?', 'It runs SQL (including SQL and Python UDFs registered in Unity Catalog). Notebooks with arbitrary '
         'Python run on clusters or serverless notebook compute.'),
        ('What is Genie?', 'A natural-language interface: domain experts curate tables, instructions and example queries in a Genie space, and '
         'business users ask questions in plain language; Genie writes and runs the SQL on a warehouse, with the user\'s permissions.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('How do you monitor and reduce Databricks costs?', 'Cost Optimisation', minutes=8, cards=[
    definition(
        defbox('Databricks charges for <strong>DBUs</strong> consumed by compute (rate depends on product: jobs, all-purpose, SQL, serverless, '
               'model serving; and on tier and cloud). With classic compute you also pay the cloud provider for VMs, disks and networking. '
               'Storage is billed by the cloud provider (or included for some serverless/default storage).'),
        table(['Lever', 'Why it saves money'], [
            ['Job compute or serverless for production', 'Lower DBU rates than all-purpose; no idle time'],
            ['Auto-termination / auto-stop', 'No clusters or warehouses running overnight for nothing'],
            ['Cluster policies', 'Cap sizes and node types; force tags and auto-termination'],
            ['Spot / preemptible workers', 'Much cheaper VMs for fault-tolerant batch workloads (keep the driver on-demand)'],
            ['Right-size, then autoscale', 'Measure with the Spark UI; avoid oversized fixed clusters'],
            ['Photon where it helps', 'Higher DBU rate but often far shorter runtime for SQL-heavy jobs'],
            ['Good table layout', 'Clustering, OPTIMIZE and VACUUM mean less data scanned and stored'],
            ['availableNow streaming', 'Incremental processing without an always-on cluster'],
            ['Tags + budgets + system.billing', 'Know which team, job or warehouse spends what; alert on budgets'],
        ]),
        tags('DBU', 'system.billing.usage', 'list_prices', 'Tags', 'Budgets', 'Spot instances', 'Auto-termination', 'Serverless'),
    ),
    analogy('Cloud cost is an <strong>electricity bill</strong>: the biggest savings come from switching off lights in empty rooms '
            '(auto-termination), using the right appliance (compute type), and knowing which room uses what (tags), long before buying a '
            'more efficient bulb.'),
    cost_anim(),
    real_world(
        scenario('A 40% reduction in one month',
                 ul('The billing system table showed 55% of DBUs on all-purpose clusters running scheduled notebooks: moved to job compute and '
                    'serverless jobs.',
                    'Two SQL warehouses had auto-stop disabled: set to 10 minutes.',
                    'A nightly job scanned a 2 TB table fully: liquid clustering on <code>exam_date</code> cut the scan to 3%.',
                    'Every cluster now needs <code>team</code> and <code>project</code> tags (cluster policy), and a budget alert goes to each '
                    'team lead.')),
    ),
    example(
        sq('''
-- DBUs and approximate list cost by SKU for the last 30 days
SELECT u.sku_name,
       SUM(u.usage_quantity)                          AS dbus,
       SUM(u.usage_quantity * p.pricing.default)      AS list_cost
FROM   system.billing.usage u
JOIN   system.billing.list_prices p
  ON   u.sku_name = p.sku_name
 AND   u.usage_start_time >= p.price_start_time
 AND  (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
WHERE  u.usage_date >= current_date() - INTERVAL 30 DAYS
GROUP  BY u.sku_name
ORDER  BY list_cost DESC;

-- which jobs cost the most?
SELECT usage_metadata.job_id, SUM(usage_quantity) AS dbus
FROM   system.billing.usage
WHERE  usage_metadata.job_id IS NOT NULL
  AND  usage_date >= current_date() - INTERVAL 30 DAYS
GROUP  BY usage_metadata.job_id
ORDER  BY dbus DESC
LIMIT  10;

-- spend by team tag
SELECT custom_tags['team'] AS team, SUM(usage_quantity) AS dbus
FROM   system.billing.usage
WHERE  usage_date >= current_date() - INTERVAL 30 DAYS
GROUP  BY ALL
ORDER  BY dbus DESC;
'''),
        title='Example'),
    steps(
        ('Make spend visible', 'Enable system tables; tag all compute; build a cost dashboard; set budgets.'),
        ('Remove waste', 'Idle clusters, always-on warehouses, all-purpose compute for jobs.'),
        ('Right-size', 'Use metrics to pick node types and autoscaling ranges; spot workers for batch.'),
        ('Reduce work', 'Incremental processing, good layout, fewer full rewrites.'),
        ('Review monthly', 'Top jobs, warehouses and teams; track trends.'),
        title='Steps'),
    crossq(
        ('Is serverless always cheaper?', 'Not per hour, but often in total: no idle time, no start-up minutes, no over-provisioning, and no '
         'separate VM bill. For long, steady, well-tuned workloads classic job compute can be cheaper; measure both.'),
        ('Why keep the driver on an on-demand instance when using spot?', 'If a spot worker is reclaimed Spark re-runs its tasks; if the driver '
         'is reclaimed, the whole job fails.'),
        ('What is predictive optimization?', 'For Unity Catalog managed tables, Databricks automatically runs OPTIMIZE, VACUUM and ANALYZE '
         'when it predicts they pay off, saving both engineering time and compute on scans.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: design a Databricks pipeline for C-DAC CCEE results, from JSON files to a published rank list.', 'Scenario: Results Pipeline', minutes=12, tag='Scenario', cards=[
    definition(
        defbox('<strong>Requirements</strong>: every centre uploads a JSON file of subject-wise marks after the CCEE exam. The exam cell needs a '
               'clean per-subject table, a list of rejected rows to send back to centres, and a <strong>rank list</strong> per course with total '
               'marks and PASS/FAIL (every subject ≥ 40). Re-uploads and corrections must not create duplicates, and the whole run must be '
               'repeatable.'),
        table(['Layer', 'Table', 'Design choice'], [
            ['Landing', '<code>/Volumes/cdac/bda/landing/ccee/</code>', 'One volume folder per feed; files never edited'],
            ['Bronze', '<code>bronze_ccee</code>', 'Auto Loader (here: batch read) + source file + ingest time'],
            ['Silver', '<code>silver_ccee</code>', 'Typed; MERGE on (roll_no, subject) so re-runs are idempotent; CHECK constraint on marks'],
            ['Quarantine', '<code>quarantine_ccee</code>', 'Rows that failed validation, with the reason'],
            ['Gold', '<code>gold_rank_list</code>', 'Totals, RANK() per course, PASS/FAIL; read by dashboard and PDF job'],
            ['Orchestration', 'Lakeflow job', 'File-arrival trigger; tasks bronze → silver → gold → dashboard refresh'],
        ]),
        tags('Medallion', 'Quarantine', 'MERGE', 'Idempotent', 'Window functions', 'RANK', 'File-arrival trigger'),
    ),
    analogy('Think of the real exam cell: <strong>sealed envelopes</strong> arrive (bronze), clerks <strong>check every mark sheet</strong> and '
            'return faulty ones to the centre (silver and quarantine), and finally the <strong>merit list</strong> is printed (gold).'),
    exam_pipeline_anim(),
    real_world(
        scenario('What could go wrong, and how the design handles it',
                 ul('<strong>A centre uploads twice</strong>: the silver MERGE on (roll_no, subject) updates instead of duplicating.',
                    '<strong>A mark of 120</strong>: goes to quarantine with the reason; the CHECK constraint on silver is a second safety net.',
                    '<strong>A late correction</strong>: re-running the job MERGEs the new value and the gold table is rebuilt from silver.',
                    '<strong>A bug in the rank logic</strong>: fix the code and rebuild gold from silver; bronze still holds every original row.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F

# ---------------- bronze: raw rows + where they came from
(spark.read.json("/Volumes/cdac/bda/landing/ccee/")
      .withColumn("source_file", F.element_at(F.split(F.col("_metadata.file_path"), "/"), -1))
      .withColumn("ingested_at", F.current_timestamp())
      .write.mode("append").saveAsTable("bronze_ccee"))

# ---------------- silver + quarantine
spark.sql("""CREATE TABLE IF NOT EXISTS silver_ccee (
               roll_no INT NOT NULL, name STRING, course STRING, centre STRING,
               subject STRING NOT NULL, marks INT,
               CONSTRAINT valid_marks CHECK (marks BETWEEN 0 AND 100))""")

checked = (spark.table("bronze_ccee")
                .withColumn("reason", F.when(F.col("roll_no").isNull(), "missing roll_no")
                                       .when(~F.col("marks").between(0, 100), "marks out of range")))
checked.filter("reason IS NOT NULL").select("roll_no", "subject", "marks", "source_file", "reason") \\
       .write.mode("overwrite").saveAsTable("quarantine_ccee")
checked.filter("reason IS NULL").createOrReplaceTempView("valid_rows")

spark.sql("""
  MERGE INTO silver_ccee AS t
  USING (SELECT CAST(roll_no AS INT) AS roll_no, name, course, centre, subject,
                CAST(marks AS INT) AS marks FROM valid_rows) AS s
  ON t.roll_no = s.roll_no AND t.subject = s.subject
  WHEN MATCHED THEN UPDATE SET *
  WHEN NOT MATCHED THEN INSERT *""").show()

# ---------------- gold: rank list per course
spark.sql("""
  CREATE OR REPLACE TABLE gold_rank_list AS
  SELECT course, roll_no, name, centre,
         SUM(marks) AS total,
         CASE WHEN MIN(marks) >= 40 THEN 'PASS' ELSE 'FAIL' END AS result,
         RANK() OVER (PARTITION BY course ORDER BY SUM(marks) DESC) AS course_rank
  FROM   silver_ccee
  GROUP  BY course, roll_no, name, centre""")

spark.table("quarantine_ccee").show()
spark.table("gold_rank_list").orderBy("course", "course_rank").show()
''', files=CCEE, data=False),
        sql('''
-- the job runs again after a corrected file arrives: idempotent MERGE, nothing duplicated
MERGE INTO silver_ccee AS t
USING (SELECT * FROM VALUES (2403, 'Riya', 'PGCP-AI', 'Kharghar', 'Python', 92)
       AS s(roll_no, name, course, centre, subject, marks)) AS s
ON t.roll_no = s.roll_no AND t.subject = s.subject
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

SELECT course, COUNT(*) AS rows, COUNT(DISTINCT roll_no) AS students FROM silver_ccee GROUP BY course ORDER BY course;
''', setup="""
CREATE TABLE silver_ccee (roll_no INT NOT NULL, name STRING, course STRING, centre STRING, subject STRING NOT NULL, marks INT,
  CONSTRAINT valid_marks CHECK (marks BETWEEN 0 AND 100));
INSERT INTO silver_ccee VALUES
  (2401, 'Anuj', 'PGCP-BDA', 'Kharghar', 'SQL', 72), (2401, 'Anuj', 'PGCP-BDA', 'Kharghar', 'Python', 64),
  (2405, 'Sana', 'PGCP-BDA', 'Kharghar', 'SQL', 95), (2405, 'Sana', 'PGCP-BDA', 'Kharghar', 'Python', 89),
  (2403, 'Riya', 'PGCP-AI', 'Kharghar', 'ML', 91),
  (2402, 'Aarshvi', 'PGCP-BDA', 'Juhu', 'SQL', 88), (2402, 'Aarshvi', 'PGCP-BDA', 'Juhu', 'Python', 90),
  (2408, 'Tejas', 'PGCP-BDA', 'Juhu', 'SQL', 38), (2408, 'Tejas', 'PGCP-BDA', 'Juhu', 'Python', 61),
  (2406, 'Omkar', 'PGCP-AI', 'Juhu', 'ML', 77), (2406, 'Omkar', 'PGCP-AI', 'Juhu', 'Python', 81);
""", data=False, title='Databricks SQL: a corrected file for Riya'),
        p('Riya\'s Python mark (120) went to quarantine, so her total in the first gold run counts only ML; Tejas fails because SQL is below 40. '
          'When the corrected file arrives, the MERGE inserts her Python row (it was never in silver) and a rebuild of gold would rank her '
          'correctly. Running the corrected MERGE twice would leave the counts unchanged.', top=True),
        title='Example: The Pipeline, End to End'),
    steps(
        ('Agree the contract', 'File format, columns, keys, valid ranges, who fixes rejected rows.'),
        ('Bronze', 'Auto Loader with availableNow, source file and ingest time.'),
        ('Silver', 'Validate → quarantine; MERGE on the business key; constraints as a safety net.'),
        ('Gold', 'Window functions for ranks; one table per consumer.'),
        ('Operate', 'Job with file-arrival trigger, retries, alerts; dashboard on a SQL warehouse; lineage in Unity Catalog.'),
        title='Steps'),
    crossq(
        ('Why RANK and not ROW_NUMBER for a merit list?', 'Students with the same total should share a rank (1, 2, 2, 4). ROW_NUMBER would give '
         'them different ranks arbitrarily; DENSE_RANK would give 1, 2, 2, 3.'),
        ('How would you make this incremental for 10 lakh students?', 'Auto Loader with availableNow for bronze; MERGE only the new rows into '
         'silver (read bronze incrementally with a stream or CDF); recompute gold only for affected courses, or make it a materialized view in '
         'a declarative pipeline.'),
        ('Where would you write this in production: a job with notebooks or a declarative pipeline?', 'A declarative pipeline expresses bronze, '
         'silver (with expectations and AUTO CDC) and gold (materialized view) with far less code and handles retries and incremental refresh; '
         'a job with notebooks gives more control. Both are valid answers if you can justify them.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: implement a Slowly Changing Dimension Type 2 table with MERGE in Delta Lake.', 'Scenario: SCD Type 2', minutes=10, tag='Scenario', cards=[
    definition(
        table(['SCD type', 'What happens on a change', 'History kept?'], [
            ['Type 0', 'Never change the attribute', 'n/a'],
            ['Type 1', 'Overwrite the old value', 'No'],
            ['Type 2', 'Close the current row (end date, flag) and insert a new current row', 'Yes, full history'],
            ['Type 3', 'Keep the previous value in an extra column', 'Only one previous value'],
        ]),
        defbox('A Type 2 dimension has validity columns such as <code>start_date</code>, <code>end_date</code> and <code>is_current</code>. In '
               'Delta Lake one atomic <code>MERGE</code> can close the old row and insert the new one, using a common trick: the source contains '
               'every changed row twice, once with the real key (it <em>matches</em> the current row, which is closed) and once with a '
               '<code>NULL</code> merge key (it never matches, so it is inserted). In a declarative pipeline, '
               '<code>AUTO CDC … STORED AS SCD TYPE 2</code> does all of this for you.'),
        tags('SCD Type 2', 'Slowly changing dimension', 'MERGE', 'merge_key', 'is_current', 'AUTO CDC', 'Point-in-time query'),
    ),
    analogy('A Type 2 dimension is a <strong>passport\'s address history</strong>: when you move, the old address is not erased; it gets an '
            '"until" date, and the new address is added below with a "from" date.'),
    scd2_anim(),
    real_world(
        scenario('Centre transfers and old reports',
                 p('Kabir moves from Kharghar to Juhu on 10 March. February attendance reports must still count him at Kharghar, while March '
                   'reports count him at Juhu. With a Type 2 <code>dim_student</code>, facts are joined to the dimension row that was valid on the '
                   'fact\'s date, so old reports never change.')),
    ),
    example(
        sql('''
SELECT * FROM student_updates ORDER BY roll_no;

MERGE INTO dim_student AS d
USING (
  SELECT u.roll_no AS merge_key, u.* FROM student_updates u          -- matches: closes the old row
  UNION ALL
  SELECT NULL AS merge_key, u.*                                      -- never matches: inserts the new version
  FROM   student_updates u
  JOIN   dim_student d ON d.roll_no = u.roll_no AND d.is_current AND d.centre <> u.centre
) AS s
ON d.roll_no = s.merge_key AND d.is_current
WHEN MATCHED AND d.centre <> s.centre THEN
  UPDATE SET d.is_current = false, d.end_date = s.effective_date
WHEN NOT MATCHED THEN
  INSERT (roll_no, name, centre, start_date, end_date, is_current)
  VALUES (s.roll_no, s.name, s.centre, s.effective_date, NULL, true);

SELECT * FROM dim_student ORDER BY roll_no, start_date;

-- point-in-time lookup: where was 2404 on 1 March?
SELECT name, centre FROM dim_student
WHERE  roll_no = 2404
  AND  DATE'2026-03-01' >= start_date
  AND  (end_date IS NULL OR DATE'2026-03-01' < end_date);
''', setup=SCD, data=False),
        sq('''
-- the declarative equivalent in a Lakeflow pipeline
CREATE OR REFRESH STREAMING TABLE dim_student_scd2;

CREATE FLOW student_scd2 AS AUTO CDC INTO dim_student_scd2
FROM STREAM(student_updates_feed)
KEYS (roll_no)
SEQUENCE BY effective_date
COLUMNS * EXCEPT (effective_date)
STORED AS SCD TYPE 2
TRACK HISTORY ON (centre);
'''),
        p('One MERGE produced 1 update (Kabir\'s Kharghar row closed on 2026-03-10) and 2 inserts (Kabir at Juhu, and the new student Zoya). '
          'Meera\'s row matched but her centre had not changed, so nothing happened to it. The point-in-time query still finds Kabir at '
          'Kharghar on 1 March.', top=True),
        title='Example'),
    steps(
        ('Design the dimension', 'Business key, tracked attributes, start/end dates, current flag (and a surrogate key if needed).'),
        ('Prepare the source', 'One row per key per load; detect changed attributes.'),
        ('MERGE with the NULL-key union', 'Close changed current rows and insert new versions in one commit.'),
        ('Query by date', 'Join facts on key and date range, or filter is_current for the latest view.'),
        title='Steps'),
    crossq(
        ('Why not run an UPDATE and then an INSERT?', 'Two commits mean a reader can see the old row closed before the new one exists, and a '
         'failure between them leaves the dimension inconsistent. MERGE does both atomically.'),
        ('How do you add a surrogate key?', 'Use an identity column (<code>student_sk BIGINT GENERATED ALWAYS AS IDENTITY</code>) so each '
         'version gets its own key, and store that key in fact tables.'),
        ('What does SEQUENCE BY do in AUTO CDC?', 'It orders changes for the same key, so out-of-order events are applied correctly: a late, older '
         'change does not overwrite a newer one.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('How does Databricks compare with Snowflake, AWS EMR/Glue and Microsoft Fabric? And how do you troubleshoot common errors?', 'Comparison & Troubleshooting', minutes=10, cards=[
    definition(
        table(['', 'Databricks', 'Snowflake', 'AWS EMR / Glue', 'Microsoft Fabric'], [
            ['Core idea', 'Data + AI lakehouse on open files', 'Managed cloud data platform, SQL first', 'Managed open-source (Spark, Hive, …) / serverless ETL', 'All-in-one SaaS analytics on OneLake'],
            ['Storage', 'Your object storage, Delta (and Iceberg)', 'Snowflake-managed; Iceberg tables too', 'Your S3 (Parquet, Iceberg, Hudi, Delta)', 'OneLake, Delta format'],
            ['Strengths', 'Spark, streaming, ML/GenAI, open formats, governance', 'Ease of SQL use, near-zero tuning, data sharing', 'Full control, AWS integration', 'Power BI and Microsoft 365 integration'],
            ['Trade-offs', 'More concepts to learn', 'Less control over compute and formats', 'You operate and tune clusters', 'Newer; capacity-based pricing'],
            ['Clouds', 'AWS, Azure, GCP', 'AWS, Azure, GCP', 'AWS only', 'Azure only'],
        ]),
        tags('Databricks', 'Snowflake', 'EMR', 'Glue', 'Microsoft Fabric', 'Lakehouse', 'Open formats'),
    ),
    analogy('Choosing a platform is like choosing <strong>transport for a college trip</strong>: a hired bus with a driver (Snowflake, Fabric), '
            'your own bus that you maintain (EMR), or a fleet service that also carries cargo and lab equipment (Databricks). The right answer '
            'depends on the trip, not on the brand.'),
    compare_anim(),
    real_world(
        scenario('Common errors and what they mean',
                 table(['Error', 'Usual cause', 'Fix'], [
                     ['<code>[TABLE_OR_VIEW_NOT_FOUND]</code>', 'Wrong catalog/schema, or no USE CATALOG / USE SCHEMA', 'Use full names; check grants and current_schema()'],
                     ['<code>PERMISSION_DENIED</code>', 'Missing privilege, or compute without Unity Catalog access mode', 'Grant to the group; use standard/dedicated access mode'],
                     ['Schema mismatch on write', 'New or renamed column in the data', 'Fix the data, or mergeSchema / ALTER TABLE on purpose'],
                     ['<code>DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE</code>', 'Duplicate keys in the MERGE source', 'De-duplicate the source (ROW_NUMBER / QUALIFY)'],
                     ['<code>ConcurrentAppendException</code>', 'Two writers changed the same files', 'Partition/cluster so writers touch different data; retry; row-level concurrency'],
                     ['Executor lost / OOM', 'Skew, huge partitions, collect() to driver', 'AQE, more partitions, avoid collect; check the Spark UI'],
                     ['Stream fails after a schema change', 'Auto Loader detected a new column', 'Restart (the job retry does it); review schema evolution mode'],
                     ['<code>FileNotFound</code> on time travel', 'Files removed by VACUUM', 'Keep retention ≥ the recovery window you need'],
                 ])),
        title='Troubleshooting Guide'),
    example(
        sql('''
SELECT * FROM cdac.bda.student;
SELECT roll_no, course FROM students WHERE roll_no = 2401;
''', show='all', expect_error=True),
        p('A misspelt table name (<code>student</code> instead of <code>students</code>) gives <code>TABLE_OR_VIEW_NOT_FOUND</code>; reading '
          'the error class first usually tells you which category of problem you have.', top=True),
        title='Example'),
    steps(
        ('Read the error class', 'The text in square brackets names the problem category.'),
        ('Check identity and grants', 'current_user(), SHOW GRANTS, the compute\'s access mode.'),
        ('Check the data', 'DESCRIBE DETAIL / HISTORY: what changed recently?'),
        ('Check the run', 'Spark UI or query profile for skew, spill, and failed tasks.'),
        ('Fix the cause, then re-run', 'Use repair run for jobs; restart streams from their checkpoint.'),
        title='Steps'),
    crossq(
        ('Databricks or Snowflake for a team that only writes SQL reports?', 'Both work. Snowflake is very simple for pure SQL warehousing; '
         'Databricks SQL is comparable and wins when the same data also feeds streaming, Python data engineering or ML. Existing skills, '
         'cloud and cost usually decide.'),
        ('Is Microsoft Fabric a replacement for Azure Databricks?', 'They overlap. Fabric is an integrated SaaS suite centred on Power BI and '
         'OneLake; Azure Databricks offers deeper Spark, ML and governance capabilities. Many companies use both, sharing Delta tables between '
         'them.'),
        ('What would you say in an interview when asked "which is best"?', 'That it depends on workloads, data formats, skills, governance needs '
         'and cost, and then give a concrete recommendation for the scenario in the question, with its trade-offs.'),
    ),
]),

])
