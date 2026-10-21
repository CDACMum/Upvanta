from build import *
from airflow.anims import *
from airflow.runner import dagtest, afcli, afpy

PIPE_CONN = {'AIRFLOW_CONN_SHOP_REPLICA': '{"conn_type": "sqlite", "host": "/tmp/shop.db"}',
             'AIRFLOW_CONN_WAREHOUSE': '{"conn_type": "sqlite", "host": "/tmp/warehouse.db"}'}

SECTION = dict(level='expert', title='Real-world Scenarios', questions=[

# ------------------------------------------------------------------ 43
Q('Design a daily DAG that loads new and changed orders from MySQL into a data lake and a warehouse', 'Incremental ETL DAG (End to End)', minutes=12, cards=[
    definition(
        defbox('A classic interview design question. A good answer is <strong>incremental</strong> (only the run\'s data interval), '
               '<strong>idempotent</strong> (safe to retry and backfill), <strong>validated</strong> before publishing, and '
               '<strong>observable</strong> (alerts, clear task boundaries).'),
        tags('Incremental Load', 'Data Interval', 'Idempotent', 'Partition', 'Data Quality', 'Backfill'),
    ),
    pipeline_anim(),
    example(
        dagtest('''
import csv, os, pendulum
from datetime import timedelta
from airflow.sdk import dag, task
from airflow.timetables.interval import CronDataIntervalTimetable
from airflow.providers.sqlite.hooks.sqlite import SqliteHook   # MySqlHook in production

LAKE = "/tmp/lake/orders"

@dag(schedule=CronDataIntervalTimetable("@daily", timezone="UTC"),   # one run per day of data
     start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False, max_active_runs=3,
     default_args={"owner": "vineeta", "retries": 2, "retry_delay": timedelta(minutes=5)},
     tags=["sales", "incremental"])
def orders_incremental():

    @task
    def seed_source():                       # demo only: a tiny "MySQL" source
        h = SqliteHook(sqlite_conn_id="shop_replica")
        h.run("DROP TABLE IF EXISTS orders")
        h.run("CREATE TABLE orders (order_id INT, customer TEXT, amount INT, updated_at TEXT)")
        h.insert_rows("orders", [
            (101, "Anuj", 4500, "2026-10-09 23:10:00"),     # belongs to the previous run
            (102, "Vineeta", 61000, "2026-10-10 09:30:00"),
            (103, "Aarshvi", 2500, "2026-10-10 18:45:00"),
            (101, "Anuj", 5200, "2026-10-10 20:05:00"),     # order 101 was updated today
            (104, "Ravi", 800, "2026-10-11 00:02:00"),      # next run's data
        ])

    @task
    def extract_delta(data_interval_start=None, data_interval_end=None):
        h = SqliteHook(sqlite_conn_id="shop_replica")
        rows = h.get_records(
            "SELECT order_id, customer, amount, updated_at FROM orders "
            "WHERE updated_at >= ? AND updated_at < ? ORDER BY updated_at",
            parameters=(data_interval_start.strftime("%Y-%m-%d %H:%M:%S"),
                        data_interval_end.strftime("%Y-%m-%d %H:%M:%S")))
        path = f"{LAKE}/dt={data_interval_start.to_date_string()}/orders.csv"   # partition = the day of data
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="") as f:              # overwrite: same path for the same run
            csv.writer(f).writerows(rows)
        print(f"interval {data_interval_start} → {data_interval_end}: {len(rows)} rows → {path}")
        return path

    @task
    def quality_check(path):
        rows = list(csv.reader(open(path)))
        assert rows, "no rows extracted"
        assert all(r[0] for r in rows), "null order_id"
        latest = {r[0]: r for r in rows}                  # keep the latest version of each order
        print(f"{len(rows)} change rows, {len(latest)} distinct orders")
        return path

    @task
    def load_warehouse(path, data_interval_start=None):
        rows = list(csv.reader(open(path)))
        latest = {r[0]: r for r in rows}.values()
        h = SqliteHook(sqlite_conn_id="warehouse")
        conn = h.get_conn()
        with conn:
            conn.execute("CREATE TABLE IF NOT EXISTS fact_orders (order_id INT PRIMARY KEY, customer TEXT, amount INT, load_dt TEXT)")
            conn.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?) "
                             "ON CONFLICT(order_id) DO UPDATE SET amount = excluded.amount, load_dt = excluded.load_dt",
                             [(int(r[0]), r[1], int(r[2]), data_interval_start.to_date_string()) for r in latest])
        print("fact_orders now:", conn.execute("SELECT * FROM fact_orders ORDER BY order_id").fetchall())

    seed_source() >> load_warehouse(quality_check(extract_delta()))

orders_incremental()
''', 'orders_incremental', '2026-10-11', env=PIPE_CONN),
        title='Example: airflow dags test orders_incremental 2026-10-11 (processes 10 Oct)'),
    note('<code>dags test</code> creates a <em>manual</em> run. For manual runs Airflow assigns the data interval that <strong>ended</strong> '
         'at the given date, so passing 2026-10-11 processes the 10 Oct → 11 Oct interval. That is also why the lake partition is named '
         'from <code>data_interval_start</code> rather than <code>ds</code>: it is always "the day of data", however the run was created.', 'Why 2026-10-11?'),
    explanation(
        ul('Only 3 of the 5 source rows fall inside the interval; the 9 Oct and 11 Oct rows belong to other runs.',
           'Order 101 changed during the day, so the extract has its newer version; the MERGE (upsert) updates it in the warehouse.',
           'Re-running 10 Oct overwrites the same lake file and upserts the same keys, giving identical results.',
           'In production: MySqlHook on a <strong>read replica</strong>, an index on <code>updated_at</code>, Parquet instead of CSV, '
           'a pool to limit load on the source, and a failure callback to the team channel.'),
        title='What to Point Out'),
    crossq(
        ('How would you capture deletes?', 'Timestamp extraction cannot see hard deletes. Use soft-delete flags, a periodic full key comparison, or log-based CDC (Debezium) instead of query-based extraction.'),
        ('How do you load 2 years of history the first time?', 'Backfill the date range with max_active_runs limiting parallelism, or run a separate one-off full load and then switch on the incremental DAG.'),
    ),
]),

# ------------------------------------------------------------------ 44
Q('How do you orchestrate Spark jobs (Databricks, EMR, spark-submit) from Airflow?', 'Orchestrating Spark Jobs', minutes=8, cards=[
    definition(
        defbox('Airflow should <strong>submit</strong> Spark jobs to a cluster and <strong>wait</strong> for them, never process big data '
               'on its own workers. Provider operators exist for each platform; most support <code>deferrable=True</code> so the wait '
               'costs no worker slot.'),
        tags('SparkSubmitOperator', 'DatabricksSubmitRunOperator', 'EmrAddStepsOperator', 'EMR Serverless', 'Dataproc', 'Deferrable'),
    ),
    explanation(
        code('''
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

aggregate = SparkSubmitOperator(
    task_id="aggregate_sales",
    conn_id="spark_yarn",                         # master=yarn, deploy-mode=cluster
    application="/jobs/aggregate_sales.py",
    application_args=["--date", "{{ ds }}", "--input", "s3a://lake/orders/dt={{ ds }}/"],
    conf={"spark.executor.memory": "8g", "spark.sql.shuffle.partitions": "200"},
    executor_cores=4, num_executors=10,
)
''', 'spark-submit to YARN / Kubernetes', 'fa-brands fa-python')
        + code('''
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

run_job = DatabricksRunNowOperator(
    task_id="run_sales_job",
    databricks_conn_id="databricks_default",
    job_id=12345,
    job_parameters={"run_date": "{{ ds }}"},
    deferrable=True,
)
''', 'Databricks job', 'fa-brands fa-python')
        + code('''
from airflow.providers.amazon.aws.operators.emr import EmrServerlessStartJobOperator

spark_on_emr = EmrServerlessStartJobOperator(
    task_id="spark_on_emr",
    application_id="00fabc123",
    execution_role_arn="arn:aws:iam::123456789012:role/emr-job-role",
    job_driver={"sparkSubmit": {"entryPoint": "s3://code/aggregate_sales.py",
                                "entryPointArguments": ["--date", "{{ ds }}"]}},
    deferrable=True,
)
''', 'EMR Serverless', 'fa-brands fa-python'),
        title='Examples'),
    table(['Concern', 'Practice'], [
        ['Parameters', 'Pass {{ ds }} / interval bounds as job arguments so the job processes exactly the run\'s data'],
        ['Idempotency', 'Spark job overwrites its output partition (dynamic partition overwrite / Delta MERGE)'],
        ['Cost', 'Ephemeral clusters (job clusters, EMR Serverless) created per run and terminated after'],
        ['Waiting', 'Deferrable operators or sensors in reschedule mode'],
        ['Logs', 'Operators pull the driver log or a link to the Spark UI into the Airflow task log'],
    ]),
    crossq(
        ('Should pandas/PySpark transformations run inside a @task?', 'Small data, yes. Large data, no: the Airflow worker is not a compute cluster. Push the work to Spark, the warehouse (SQL/dbt) or a container with the right resources.'),
    ),
]),

# ------------------------------------------------------------------ 45
Q('Tasks are stuck in "scheduled" or "queued" and nothing runs. How do you troubleshoot?', 'Stuck Tasks Troubleshooting', minutes=7, cards=[
    definition(
        defbox('A task that never starts is waiting on a <strong>limit</strong> or on a <strong>component</strong>. "Scheduled" means the '
               'scheduler has not queued it yet (limits); "queued" means the executor has it but no worker started it (workers).'),
        tags('scheduled', 'queued', 'parallelism', 'Pools', 'Workers', 'Scheduler Health', 'Celery'),
    ),
    table(['Check', 'Where', 'Typical finding'], [
        ['Scheduler alive?', 'UI health banner, <code>/api/v2/monitor/health</code>, scheduler logs', 'Scheduler crashed or cannot reach the DB'],
        ['Pool full?', 'Admin → Pools (running / queued / scheduled slots)', 'All slots of a small pool held by long tasks'],
        ['DAG limits?', 'max_active_tasks, max_active_runs, depends_on_past', 'Yesterday\'s run is still running or failed'],
        ['Global limit?', '[core] parallelism × number of schedulers', 'Too low for the number of tasks'],
        ['Workers alive?', 'Celery Flower, worker logs, Kubernetes pod events', 'Workers down, wrong queue name, pods Pending (no CPU/memory)'],
        ['Sensors hogging slots?', 'Count running sensors in poke mode', 'All slots taken by waiting sensors → switch to reschedule/deferrable'],
        ['Deferred forever?', 'Triggerer logs', 'No triggerer running'],
    ]),
    interview(p('Walk through it in the order the task travels: DAG run created → scheduler → limits/pools → executor → worker. '
                'Saying where each state is set shows you understand the architecture, not just the UI.')),
]),

# ------------------------------------------------------------------ 46
Q('How do you pass large data between tasks?', 'Passing Large Data Between Tasks', minutes=7, cards=[
    definition(
        defbox('Do not push large data through XCom. Write it to <strong>shared storage</strong> (S3, GCS, ADLS, HDFS, a staging table) '
               'and pass only the <strong>reference</strong> (path or table name). Airflow\'s <code>ObjectStoragePath</code> gives one '
               'API for local files and cloud storage.'),
        tags('ObjectStoragePath', 'XCom', 'S3', 'Staging Table', 'Object Storage XCom Backend'),
    ),
    example(
        dagtest('''
import csv, io, pendulum
from airflow.sdk import dag, task, ObjectStoragePath

BASE = ObjectStoragePath("file:///tmp/lake/")       # "s3://bucket/lake/" with conn_id in production

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def large_data_demo():

    @task
    def extract(ds=None) -> str:
        path = BASE / "attendance" / f"dt={ds}" / "part-0.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [("Anuj", d, d % 7 != 0) for d in range(1, 31)] + \\
               [("Vineeta", d, True) for d in range(1, 31)] + \\
               [("Aarshvi", d, d % 5 != 0) for d in range(1, 31)]
        with path.open("w") as f:
            csv.writer(f).writerows(rows)
        print(f"wrote {len(rows)} rows, passing only the path through XCom")
        return str(path)                              # small XCom: a string

    @task
    def summarize(path: str):
        present = {}
        with ObjectStoragePath(path).open("r") as f:
            for name, day, here in csv.reader(f):
                present[name] = present.get(name, 0) + (here == "True")
        for name, n in present.items():
            print(f"{name}: {n}/30 days present")

    summarize(extract())

large_data_demo()
''', 'large_data_demo', '2026-10-10'),
        title='Example: Hand Over a Path, Not the Data'),
    comparison(
        table(['Option', 'Good for'], [
            ['Path in XCom + files in object storage', 'Most batch pipelines'],
            ['Staging table name in XCom', 'SQL-centric pipelines (ELT)'],
            ['Object-storage XCom backend', 'When you want to keep "return the DataFrame" code but store it in S3 automatically'],
            ['Do it all in one task / one Spark job', 'When splitting adds I/O without adding retry value'],
        ]),
    ),
]),

# ------------------------------------------------------------------ 47
Q('How do you make one DAG depend on another DAG?', 'Cross-DAG Dependencies', minutes=8, cards=[
    definition(
        defbox('Dependencies between DAGs are expressed with <strong>Assets</strong> (data-aware scheduling), '
               '<strong>ExternalTaskSensor</strong> (wait for a task in another DAG), or <strong>TriggerDagRunOperator</strong> '
               '(start another DAG). Prefer Assets for producer → consumer data dependencies.'),
        tags('ExternalTaskSensor', 'TriggerDagRunOperator', 'Assets', 'execution_delta', 'Cross-DAG'),
    ),
    cross_dag_anim(),
    explanation(
        code('''
from datetime import timedelta
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor

wait_for_orders = ExternalTaskSensor(
    task_id="wait_for_orders",
    external_dag_id="load_orders",
    external_task_id="write_orders",          # None = wait for the whole DAG run
    execution_delta=timedelta(hours=1),       # A runs at 02:00, B at 03:00 → look 1 h back
    allowed_states=["success"],
    failed_states=["failed", "skipped"],
    mode="reschedule", timeout=4 * 3600,      # or deferrable=True
)
''', 'ExternalTaskSensor', 'fa-brands fa-python'),
        title='Example'),
    comparison(
        table(['Aspect', 'ExternalTaskSensor', 'TriggerDagRunOperator', 'Assets'], [
            ['Direction', 'Consumer pulls', 'Producer pushes', 'Event-driven'],
            ['Coupling', 'B knows A\'s ids and timing', 'A knows B', 'Both know only the asset'],
            ['Schedules', 'Must line up (execution_delta)', 'B usually schedule=None', 'B runs when data is ready'],
            ['Waiting cost', 'Sensor slot (unless deferrable)', 'None (or wait_for_completion)', 'None'],
        ]),
    ),
    crossq(
        ('The sensor waits forever although A succeeded. Why?', 'Its logical date does not match A\'s run (different schedules or time zones). Fix with <code>execution_delta</code> / <code>execution_date_fn</code>, or switch to Assets.'),
    ),
]),

# ------------------------------------------------------------------ 48
Q('You need to load 100 similar tables. Do you write 100 DAGs?', 'Generating DAGs from Config', minutes=8, cards=[
    definition(
        defbox('No. Use a <strong>DAG factory</strong>: one Python file reads a <em>local</em> config (YAML/JSON in the repo) and '
               'creates one DAG (or one task group) per entry at parse time. If the list is only known at run time, use '
               '<strong>dynamic task mapping</strong> inside a single DAG instead.'),
        tags('DAG Factory', 'Dynamic DAG Generation', 'YAML Config', 'Dynamic Task Mapping', 'Parse Time vs Run Time'),
    ),
    example(
        afcli(['airflow dags list -o plain'],
              src={'table_loaders': '''
import pendulum
from airflow.sdk import dag, task

TABLES = {                      # in practice: yaml.safe_load(open("tables.yaml")) from the repo
    "students":   {"schedule": "@daily",  "owner": "vineeta", "key": "student_id"},
    "attendance": {"schedule": "@hourly", "owner": "anuj",    "key": "att_id"},
    "fees":       {"schedule": "@daily",  "owner": "aarshvi", "key": "receipt_no"},
}

def make_dag(table, cfg):
    @dag(dag_id=f"load_{table}", schedule=cfg["schedule"],
         start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
         default_args={"owner": cfg["owner"], "retries": 2}, tags=["generated", table])
    def loader():
        @task
        def extract():
            print(f"SELECT * FROM {table} WHERE updated_at in the data interval")
        @task
        def merge():
            print(f"MERGE INTO dw.{table} USING stage ON key {cfg['key']}")
        extract() >> merge()
    return loader()

for table, cfg in TABLES.items():
    make_dag(table, cfg)        # each call registers one DAG at module level
'''}, setup_cmds=['airflow db reset -y', 'airflow dags reserialize']),
        title='Example: One File, Three DAGs'),
    comparison(
        table(['Approach', 'Decided at', 'Use when'], [
            ['DAG factory (one DAG per table)', 'Parse time, from repo config', 'Tables have different schedules/owners and should fail and retry independently'],
            ['One DAG, task group per table', 'Parse time', 'Same schedule, one place to monitor'],
            ['One DAG, dynamic task mapping', 'Run time', 'The list of tables/files changes from day to day'],
        ]),
    ),
    warn('Do not build the list by calling a database or API at parse time. If the source is unreachable, the file fails to import and all generated DAGs disappear from Airflow.'),
]),

# ------------------------------------------------------------------ 49
Q('Data for past days keeps arriving late. How do you design the DAG to handle it?', 'Late-arriving Data', minutes=8, cards=[
    definition(
        defbox('If records can arrive up to N days late, each run should <strong>reprocess a lookback window</strong> (e.g. its own day '
               'plus the previous 2 days) idempotently, or a separate correction DAG should re-run affected dates. Either way the '
               'load must overwrite or merge, never append.'),
        tags('Late-arriving Data', 'Lookback Window', 'Reprocessing', 'Idempotent Overwrite', 'Watermark'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task
from airflow.timetables.interval import CronDataIntervalTimetable

LOOKBACK_DAYS = 2

@dag(schedule=CronDataIntervalTimetable("@daily", timezone="UTC"),
     start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def late_data_demo():

    @task
    def plan_window(data_interval_start=None, data_interval_end=None):
        start = data_interval_start.subtract(days=LOOKBACK_DAYS)
        days = [start.add(days=i).to_date_string() for i in range((data_interval_end - start).days)]
        print(f"run interval {data_interval_start.to_date_string()} → {data_interval_end.to_date_string()}, "
              f"reprocessing {days}")
        return days

    @task
    def reload_day(day: str):
        print(f"DELETE FROM attendance WHERE dt = '{day}'; INSERT … SELECT … WHERE dt = '{day}'")

    reload_day.expand(day=plan_window())            # one idempotent reload per day, in parallel

late_data_demo()
''', 'late_data_demo', '2026-10-11'),
        title='Example: Each Run Rebuilds Its Day Plus the 2 Days Before'),
    table(['Approach', 'Trade-off'], [
        ['Lookback window in every run', 'Simple and automatic; costs N× the processing'],
        ['Partition by arrival date, not event date', 'Never misses data; consumers must handle event-date queries'],
        ['Correction DAG triggered with the affected dates', 'Efficient; needs a way to detect late data (counts, CDC)'],
        ['Clear / backfill specific dates on request', 'Manual, fine for rare cases'],
    ]),
    crossq(
        ('Why not just re-run yesterday by changing the start of the WHERE clause to now() - 3 days?', 'Then the result depends on when the run executes, so reruns and backfills give different answers. Anchor the window to the data interval.'),
    ),
]),

])
