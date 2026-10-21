from build import *
from dbxq.anims import *
from dbxq.runner import sql, sq, pyrun, py, sh, conf

SECTION = dict(level='advanced', title='Pipelines, Jobs & Performance', questions=[

# ------------------------------------------------------------------ 26
Q('What are Lakeflow Declarative Pipelines (formerly Delta Live Tables)? Explain streaming tables, materialized views and expectations.', 'Declarative Pipelines (DLT)', minutes=10, cards=[
    definition(
        defbox('<strong>Lakeflow Declarative Pipelines</strong> (the product formerly called <strong>Delta Live Tables</strong>, DLT) is a '
               'framework where you <em>declare</em> the tables you want in SQL or Python, and the pipeline engine works out the dependency graph, '
               'runs the steps in order, handles incremental processing, checkpoints, retries and compute. The engine is based on Apache Spark '
               'Declarative Pipelines, which is open source in Spark 4.1.'),
        table(['Object', 'What it is', 'Typical layer'], [
            ['<strong>Streaming table</strong>', 'Delta table fed by one or more streaming flows; each input row is processed once', 'Bronze, silver'],
            ['<strong>Materialized view</strong>', 'Stored result of a query, refreshed (incrementally when possible) on each update', 'Silver, gold'],
            ['<strong>View</strong>', 'Not stored; used inside the pipeline', 'Intermediate steps'],
            ['<strong>Expectation</strong>', '<code>CONSTRAINT name EXPECT (cond) [ON VIOLATION DROP ROW | FAIL UPDATE]</code>', 'Data quality on any table'],
            ['<strong>AUTO CDC</strong>', 'Apply CDC changes as SCD Type 1 or 2 (formerly APPLY CHANGES INTO)', 'Silver'],
        ]),
        tags('Lakeflow Declarative Pipelines', 'Delta Live Tables', 'Streaming table', 'Materialized view', 'Expectations', 'AUTO CDC', 'Event log'),
    ),
    analogy('With a normal job you write a <strong>recipe</strong>: step 1, step 2, step 3. With a declarative pipeline you write the '
            '<strong>menu</strong>: "this dish is made from these ingredients"; the kitchen decides the order, re-cooks only what changed, and '
            'throws away ingredients that fail the quality check.'),
    ldp_anim(),
    real_world(
        scenario('Results pipeline with quality rules',
                 p('The bronze streaming table ingests every centre\'s JSON with Auto Loader. Silver has two expectations that drop rows without a '
                   'roll number or with impossible marks; gold is a materialized view of centre averages. The pipeline UI shows, for each update, '
                   'how many rows each expectation dropped, so the exam cell can chase the centre that sent "105".')),
    ),
    example(
        sq('''
CREATE OR REFRESH STREAMING TABLE bronze_results
COMMENT 'Raw CCEE result files, as received'
AS SELECT *, _metadata.file_path AS source_file
FROM STREAM read_files('/Volumes/cdac/bda/landing/results/', format => 'json');

CREATE OR REFRESH STREAMING TABLE silver_results (
  CONSTRAINT valid_roll  EXPECT (roll_no IS NOT NULL)     ON VIOLATION DROP ROW,
  CONSTRAINT valid_marks EXPECT (marks BETWEEN 0 AND 100) ON VIOLATION DROP ROW,
  CONSTRAINT known_centre EXPECT (centre IN ('Kharghar', 'Juhu'))       -- keep, but count violations
)
AS SELECT CAST(roll_no AS INT) AS roll_no, subject, CAST(marks AS INT) AS marks, centre, source_file
FROM STREAM(bronze_results);

CREATE OR REFRESH MATERIALIZED VIEW gold_centre_summary
AS SELECT centre, subject, COUNT(*) AS students, ROUND(AVG(marks), 2) AS avg_marks
FROM silver_results
GROUP BY centre, subject;
''', title='Pipeline source file, SQL (shown, not executed)'),
        py('''
from pyspark import pipelines as dp          # older pipelines: import dlt  (@dlt.table, @dlt.expect_or_drop …)
from pyspark.sql import functions as F

@dp.table(comment="Raw CCEE result files, as received")
def bronze_results():
    return (spark.readStream.format("cloudFiles")
                 .option("cloudFiles.format", "json")
                 .load("/Volumes/cdac/bda/landing/results/"))

@dp.table()
@dp.expect_or_drop("valid_roll", "roll_no IS NOT NULL")
@dp.expect_or_drop("valid_marks", "marks BETWEEN 0 AND 100")
def silver_results():
    return (spark.readStream.table("bronze_results")
                 .select(F.col("roll_no").cast("int").alias("roll_no"), "subject",
                         F.col("marks").cast("int").alias("marks"), "centre"))

@dp.materialized_view()
def gold_centre_summary():
    return (spark.read.table("silver_results")
                 .groupBy("centre", "subject").agg(F.round(F.avg("marks"), 2).alias("avg_marks")))
''', title='Pipeline source file, Python (shown, not executed)'),
        p('Pipelines run only inside the Lakeflow pipeline engine, so this code is shown without output. Question 21 builds the same three '
          'tables step by step with ordinary Spark code; compare how much bookkeeping the declarative version removes.', top=True),
        title='Example'),
    steps(
        ('Create a pipeline', 'Jobs & Pipelines → Create → ETL pipeline; choose a catalog and target schema.'),
        ('Add source files', 'SQL or Python files that declare streaming tables, materialized views and expectations.'),
        ('Choose compute', 'Serverless (recommended) or classic; triggered or continuous mode.'),
        ('Run and inspect', 'Watch the graph, row counts and expectation metrics; query the event log.'),
        ('Schedule', 'Add the pipeline as a task in a job.'),
        title='Steps'),
    crossq(
        ('Streaming table or materialized view?', 'Streaming table for append-style sources where each row is processed once (files, Kafka). '
         'Materialized view for results that depend on all of the data (joins, aggregates) and must reflect updates and deletes upstream.'),
        ('What happens to rows dropped by an expectation?', 'They are not written, and the count appears in the pipeline\'s data-quality metrics '
         'and event log. To keep them for review, write a separate quarantine table with the inverted condition.'),
        ('What does a full refresh do?', 'It clears the pipeline\'s tables and checkpoints and reprocesses all source data, for example after a '
         'logic change. It can be expensive and, for sources with limited retention (Kafka), lose data, so use it with care.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('How do you orchestrate work with Lakeflow Jobs (Databricks Workflows)?', 'Lakeflow Jobs', minutes=8, cards=[
    definition(
        defbox('A <strong>job</strong> (Lakeflow Jobs, formerly Databricks Workflows) runs one or more <strong>tasks</strong> on a schedule or '
               'trigger. Tasks form a directed acyclic graph through <code>depends_on</code>. Task types include notebooks, Python scripts and '
               'wheels, SQL queries and files, pipelines, dbt, JARs, "run job" (another job), and control flow: <strong>If/else</strong> conditions '
               'and <strong>For each</strong> loops.'),
        table(['Feature', 'Use'], [
            ['Triggers', 'Cron schedule, file arrival, table update, continuous, manual / API'],
            ['Job parameters &amp; widgets', 'Pass values such as the exam name or date into tasks'],
            ['Task values', '<code>dbutils.jobs.taskValues.set()</code> in one task, <code>get()</code> in a later one'],
            ['Retries, timeouts', 'Per task; plus "run if" rules (all succeeded, at least one failed, …)'],
            ['Compute', 'Job clusters (shared by tasks of a run) or serverless'],
            ['Notifications', 'E-mail, Slack, webhooks on start, success, failure, duration'],
            ['Repair run', 'Re-run only the failed tasks and those after them'],
        ]),
        tags('Lakeflow Jobs', 'Workflows', 'Task', 'depends_on', 'Triggers', 'Task values', 'Repair run', 'For each'),
    ),
    analogy('A job is the <strong>exam-day timetable</strong>: question papers are printed first, then distributed to centres in parallel, and '
            'only when every centre has finished are answer sheets collected; if one centre fails, only that part is re-done (repair run).'),
    jobs_anim(),
    real_world(
        scenario('The nightly results job',
                 ul('<strong>Trigger</strong>: file arrival in <code>/Volumes/cdac/bda/landing/results/</code>, or 23:00 daily.',
                    '<strong>Tasks</strong>: ingest (notebook) → clean marks + clean attendance (parallel) → publish gold (wheel) → refresh dashboard.',
                    '<strong>Compute</strong>: serverless, or one job cluster shared by all tasks of the run.',
                    '<strong>On failure</strong>: retry twice, then notify the data team; fix and use <em>Repair run</em>.')),
    ),
    example(
        conf('''
resources:
  jobs:
    nightly_results:
      name: nightly-results
      trigger:
        file_arrival:
          url: /Volumes/cdac/bda/landing/results/
      parameters:
        - name: exam
          default: CCEE
      tasks:
        - task_key: ingest
          notebook_task:
            notebook_path: ../notebooks/ingest_results.py
        - task_key: clean_marks
          depends_on: [{ task_key: ingest }]
          pipeline_task:
            pipeline_id: ${resources.pipelines.results_pipeline.id}
        - task_key: clean_attendance
          depends_on: [{ task_key: ingest }]
          sql_task:
            file: { path: ../sql/clean_attendance.sql }
            warehouse_id: ${var.warehouse_id}
        - task_key: publish_gold
          depends_on: [{ task_key: clean_marks }, { task_key: clean_attendance }]
          python_wheel_task:
            package_name: cdac_results
            entry_point: publish
          max_retries: 2
      email_notifications:
        on_failure: [data-team@cdac.in]
''', title='Job definition in a bundle (resources/nightly_results.yml)'),
        py('''
# in the "ingest" notebook
exam = dbutils.widgets.get("exam")                     # job parameter
rows = spark.table("cdac.bda.bronze_results").filter(f"exam = '{exam}'").count()
dbutils.jobs.taskValues.set(key="rows_loaded", value=rows)

# in a later notebook task
loaded = dbutils.jobs.taskValues.get(taskKey="ingest", key="rows_loaded", default=0)
if loaded == 0:
    dbutils.notebook.exit("nothing to publish")
'''),
        title='Example'),
    steps(
        ('Split the work into tasks', 'One responsibility per task; keep notebooks small.'),
        ('Wire dependencies', 'Parallel where independent; conditions for branching.'),
        ('Choose compute', 'Serverless or job clusters, never an always-on all-purpose cluster.'),
        ('Add retries and alerts', 'Retries for transient errors; notifications for the on-call person.'),
        ('Deploy as code', 'Define the job in an Asset Bundle so it is versioned and promoted with the code.'),
        title='Steps'),
    crossq(
        ('Why is running production jobs on an all-purpose cluster a bad idea?', 'All-purpose compute has a higher DBU rate, is shared with '
         'interactive users (noisy neighbours, library conflicts), and may be restarted by someone else. Job compute is isolated and created '
         'per run.'),
        ('Lakeflow Jobs or Apache Airflow?', 'Jobs is built in, needs no extra infrastructure and understands Databricks tasks natively. Airflow '
         'fits when one orchestrator must also manage many non-Databricks systems; it can trigger Databricks jobs with the Databricks '
         'provider.'),
        ('What is a repair run?', 'After a failure you fix the cause and repair the run: only the failed tasks and their downstream tasks run '
         'again, reusing the successful results.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('How do you do CI/CD on Databricks? Explain Git folders and Databricks Asset Bundles.', 'CI/CD & Asset Bundles', minutes=8, cards=[
    definition(
        defbox('<strong>Git folders</strong> (formerly Repos) connect a workspace folder to a Git repository (GitHub, GitLab, Azure DevOps, '
               'Bitbucket): users clone, branch, commit, pull and push from the workspace.',
               '<strong>Databricks Asset Bundles</strong> (DABs) describe a project as code: source files plus the resources it needs (jobs, '
               'pipelines, clusters, dashboards, ML experiments, permissions) in <code>databricks.yml</code>, with <strong>targets</strong> such as '
               'dev, staging and prod. The Databricks CLI validates, deploys and runs them: <code>databricks bundle validate | deploy | run | '
               'destroy</code>. In <code>development</code> mode resources are prefixed with your user name so developers do not clash.'),
        tags('Git folders', 'Repos', 'Asset Bundles', 'databricks.yml', 'Targets', 'Databricks CLI', 'Service principal'),
    ),
    analogy('A bundle is a <strong>shipping container with a packing list</strong>: the code and a list of everything it needs. The same '
            'container is shipped to the test lab and then to production, only the delivery address (target) changes.'),
    cicd_anim(),
    real_world(
        scenario('From laptop to production',
                 ul('A developer edits code in a Git folder or in VS Code with the Databricks extension and runs '
                    '<code>databricks bundle deploy -t dev</code> to test the job under their own name.',
                    'A pull request triggers GitHub Actions: unit tests with pytest, then <code>bundle validate</code>.',
                    'On merge to main, the pipeline deploys to staging, runs an integration test job, and after approval deploys to prod with a '
                    'service principal.')),
    ),
    example(
        conf('''
bundle:
  name: cdac_results

include:
  - resources/*.yml          # job and pipeline definitions

variables:
  warehouse_id:
    description: SQL warehouse for SQL tasks

targets:
  dev:
    mode: development        # resources prefixed with [dev user], schedules paused
    default: true
    workspace:
      host: https://adb-1111111111111111.1.azuredatabricks.net
  prod:
    mode: production
    workspace:
      host: https://adb-2222222222222222.2.azuredatabricks.net
    run_as:
      service_principal_name: 5c1f0e2a-0000-0000-0000-000000000000
''', title='databricks.yml'),
        sh('''
databricks bundle init                      # start from a template
databricks bundle validate -t dev
databricks bundle deploy   -t dev           # upload code, create/update jobs and pipelines
databricks bundle run      -t dev nightly_results
databricks bundle deploy   -t prod          # from CI, authenticated as the service principal
'''),
        title='Example'),
    steps(
        ('Put everything in Git', 'Notebooks as source files, SQL, Python packages, bundle YAML.'),
        ('Develop on a branch', 'Deploy to the dev target with development mode.'),
        ('Test in CI', 'Unit tests for transformation functions; bundle validate.'),
        ('Promote', 'Deploy the same bundle to staging and prod targets with a service principal.'),
        title='Steps'),
    crossq(
        ('How do you unit-test PySpark code?', 'Put transformations in functions that take and return DataFrames, then test them with pytest on a '
         'local SparkSession or with Databricks Connect against a cluster; compare results with small expected DataFrames.'),
        ('Why deploy to production with a service principal?', 'Jobs keep running when people leave or change roles, permissions are explicit '
         'and auditable, and no personal token sits in CI secrets.'),
        ('Git folder or bundle?', 'They work together: Git folders are for interactive development in the workspace; bundles are for deploying a '
         'versioned project and its resources to each environment.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('Python UDFs, pandas UDFs or built-in functions: which should you use and why?', 'UDFs vs Built-ins', minutes=8, cards=[
    definition(
        table(['', 'Built-in functions', 'Python UDF (<code>@udf</code>)', 'pandas UDF (<code>@pandas_udf</code>)'], [
            ['Runs in', 'JVM / Photon', 'Python worker, one row at a time', 'Python worker, Arrow batches as pandas Series'],
            ['Optimiser can see inside', 'Yes', 'No (black box)', 'No (black box)'],
            ['Speed', 'Fastest', 'Slowest (serialisation per row)', 'Much faster than @udf'],
            ['Plan node', 'Normal expressions', '<code>BatchEvalPython</code>', '<code>ArrowEvalPython</code>'],
            ['Use for', 'Almost everything', 'Simple logic with no built-in equivalent', 'Vectorised logic, ML inference, NumPy/pandas code'],
        ]),
        defbox('Also available: <strong>Arrow-optimised Python UDFs</strong> (<code>@udf(useArrow=True)</code>), <strong>SQL UDFs</strong> '
               '(<code>CREATE FUNCTION … RETURN expr</code>, inlined by the optimiser) and Unity Catalog <strong>Python UDFs</strong> registered '
               'as governed functions. <code>mapInPandas</code> and <code>applyInPandas</code> work on whole partitions or groups.'),
        tags('Built-in functions', '@udf', '@pandas_udf', 'Apache Arrow', 'BatchEvalPython', 'ArrowEvalPython', 'SQL UDF'),
    ),
    analogy('A built-in function is a <strong>machine on the factory line</strong>. A Python UDF is <strong>sending each item by courier</strong> '
            'to an outside workshop and back. A pandas UDF sends <strong>a whole crate at a time</strong>: still outside, but far fewer trips.'),
    udf_anim(),
    real_world(
        scenario('A grading UDF that was 20× slower',
                 p('A notebook converted marks to grades with a Python UDF over 3 crore rows and took 40 minutes. Rewriting it as '
                   '<code>F.when(...).otherwise(...)</code> made it a normal expression that Photon could run, and the step took under two '
                   'minutes. A pandas UDF stayed for the one step that called a scikit-learn model.')),
    ),
    example(
        pyrun('''
import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql.functions import udf, pandas_udf

df = spark.table("students")

@udf("string")                                   # 1. Python UDF: called once per row
def grade_udf(m):
    m = float(m)
    return "A" if m >= 85 else "B" if m >= 70 else "C"

@pandas_udf("string")                            # 2. pandas UDF: called once per Arrow batch
def grade_pandas(m: pd.Series) -> pd.Series:
    m = m.astype(float)
    return pd.Series(["A" if x >= 85 else "B" if x >= 70 else "C" for x in m])

grade_builtin = (F.when(F.col("marks") >= 85, "A")      # 3. built-in expression: no Python at all
                  .when(F.col("marks") >= 70, "B").otherwise("C"))

r1 = df.select("roll_no", grade_udf("marks").alias("g")).collect()
r2 = df.select("roll_no", grade_pandas("marks").alias("g")).collect()
r3 = df.select("roll_no", grade_builtin.alias("g")).collect()
print("same result:", sorted(r1) == sorted(r2) == sorted(r3))
df.select("name", "marks", grade_builtin.alias("grade")).orderBy("roll_no").show()

df.select(grade_udf("marks")).explain()
df.select(grade_pandas("marks")).explain()
df.select(grade_builtin).explain()
'''),
        sq('''
-- a SQL UDF: inlined by the optimiser, governed in Unity Catalog
CREATE OR REPLACE FUNCTION cdac.bda.grade(m DECIMAL(5,2))
RETURNS STRING
RETURN CASE WHEN m >= 85 THEN 'A' WHEN m >= 70 THEN 'B' ELSE 'C' END;

SELECT name, cdac.bda.grade(marks) AS grade FROM cdac.bda.students;
'''),
        p('All three give the same grades, but the plans differ: <code>BatchEvalPython</code> and <code>ArrowEvalPython</code> mean rows leave '
          'the JVM for a Python process; the built-in version is a plain <code>CASE WHEN</code> inside the scan stage.', top=True),
        title='Example'),
    steps(
        ('Search the function list first', '<code>pyspark.sql.functions</code> has hundreds of functions, plus higher-order functions.'),
        ('If you need Python, vectorise', 'pandas UDF, or an Arrow-optimised UDF.'),
        ('For reusable SQL logic', 'A SQL UDF in Unity Catalog.'),
        ('Check the plan', 'Look for BatchEvalPython / ArrowEvalPython and measure.'),
        title='Steps'),
    crossq(
        ('Why can a UDF stop predicate pushdown?', 'Spark cannot reason about the code inside a UDF, so a filter such as '
         '<code>WHERE my_udf(col) = \'A\'</code> cannot be pushed into the Parquet scan or used for data skipping.'),
        ('What does useArrow=True change?', 'The UDF still runs per row in your code, but data moves between the JVM and Python as Arrow '
         'batches, which cuts serialisation cost.'),
        ('When is a pandas UDF the right choice?', 'Applying a trained model, NumPy/SciPy maths, or string logic that pandas does vectorised: '
         'anything where per-row Python calls would dominate.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('A Spark job on Databricks is slow. How do you find and fix the problem?', 'Performance Tuning', minutes=10, cards=[
    definition(
        defbox('Tuning starts with <strong>measurement</strong>: the <strong>Spark UI</strong> (jobs, stages, tasks, SQL/DataFrame tab with the '
               'plan and metrics), the <strong>query profile</strong> in Databricks SQL and serverless, and cluster metrics. Look for the stage '
               'that takes the most time and ask why.'),
        table(['Problem', 'How you see it', 'Fixes'], [
            ['Data skew', 'One task much slower; uneven shuffle read sizes', 'AQE skew join (on by default), salting, handle the hot key separately'],
            ['Spill', '"Spill (memory/disk)" in stage metrics', 'More / smaller partitions, larger memory per core, avoid huge collect_list'],
            ['Small files / too many tasks', 'Thousands of tasks of a few KB', 'OPTIMIZE, auto compaction, liquid clustering'],
            ['Large shuffles', 'Big shuffle read/write', 'Filter and project early, broadcast small tables, cluster on join keys'],
            ['Scanning too much', 'Files read ≫ files needed', 'Data skipping, clustering, partition filters, select fewer columns'],
            ['Python bottleneck', 'BatchEvalPython / long Python time', 'Built-ins, pandas UDFs'],
            ['Driver overload', 'Driver OOM, long collect', 'Avoid collect()/toPandas() on big data'],
        ]),
        tags('Spark UI', 'Query profile', 'Skew', 'Spill', 'AQE', 'Photon', 'Salting', 'Broadcast'),
    ),
    analogy('Tuning is <strong>like finding the bottleneck in an exam evaluation centre</strong>: if one evaluator has 90% of the papers (skew), '
            'hiring more evaluators does not help; you have to split that pile.'),
    tuning_anim(),
    real_world(
        scenario('The default centre id',
                 p('An attendance join ran for 3 hours, but 199 of 200 tasks finished in seconds. The slow task held all swipes with '
                   '<code>centre_id = 1</code>, the default value the gate software used when the centre was unknown. With AQE skew handling '
                   'the partition was split automatically; the long-term fix was to clean the default value in silver.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F

spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)    # force a shuffle join for the demo
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256KB")
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "256KB")

# 90% of 4 lakh swipes come from centre 1 (a "hot" key)
swipes = spark.range(0, 400_000).select(
    F.when(F.col("id") % 10 < 9, F.lit(1)).otherwise(F.col("id") % 50).alias("centre_id"),
    F.col("id").alias("swipe_id"))
centres = spark.range(0, 50).select(F.col("id").alias("centre_id"), (F.col("id") * 7).alias("staff"))

swipes.groupBy("centre_id").count().orderBy(F.desc("count")).show(3)

j = swipes.join(centres, "centre_id")
rows = j.collect()                  # run the join
print(len(rows))
j.explain()
''', data=False),
        p('The thresholds were lowered only because the demo data is small (defaults: 256 MB, and 5× the median partition). In the '
          '<strong>Final Plan</strong>, AQE marked the join <code>SortMergeJoin(skew=true)</code> and the left side is read with '
          '<code>AQEShuffleRead coalesced and skewed</code>: the hot partition was split into several tasks, while the many tiny partitions '
          'were coalesced.', top=True),
        conf('''
# common settings worth knowing (defaults in brackets)
spark.sql.adaptive.enabled                      true
spark.sql.adaptive.skewJoin.enabled             true
spark.sql.shuffle.partitions                    auto   (Databricks; open-source Spark: 200)
spark.sql.autoBroadcastJoinThreshold            10MB
spark.sql.files.maxPartitionBytes               128MB
spark.databricks.delta.optimizeWrite.enabled    true   (for many write paths)
''', title='Spark configuration'),
        title='Example'),
    steps(
        ('Reproduce', 'Run the slow query once and keep the run.'),
        ('Find the slowest stage', 'Spark UI → SQL/DataFrame tab or query profile.'),
        ('Read task metrics', 'Duration and input distribution (skew), spill, shuffle sizes, files read.'),
        ('Fix the cause', 'Data layout, join strategy, partitions, UDFs, or code that collects to the driver.'),
        ('Re-measure', 'Compare time and DBUs; keep changes that help.'),
        title='Steps'),
    crossq(
        ('Will a bigger cluster fix skew?', 'No. The skewed partition is still processed by one task on one core. More workers only help when work '
         'is spread evenly.'),
        ('What is salting?', 'Adding a random number (0–N) to the hot key on the big side and replicating the small side N times, so the hot '
         'key\'s rows spread over N partitions. AQE skew join makes it unnecessary in many cases.'),
        ('When should you enable Photon?', 'For SQL and DataFrame workloads with joins, aggregations and scans on Delta/Parquet, which Photon '
         'accelerates. Jobs dominated by Python UDFs or RDD code gain little.'),
    ),
]),

])
