from build import *
from airflow.anims import *
from airflow.runner import dagtest, afcli, afpy

FS_CONN = {'AIRFLOW_CONN_FS_DEFAULT': '{"conn_type": "fs", "extra": {"path": "/"}}'}
SCHOOL_CONN = {'AIRFLOW_CONN_SCHOOL_DB': '{"conn_type": "sqlite", "host": "/tmp/school.db"}'}

SECTION = dict(level='advanced', title='Sensors, Hooks, Connections & Pools', questions=[

# ------------------------------------------------------------------ 26
Q('What are sensors? Explain poke, reschedule and deferrable modes', 'Sensors & Their Modes', minutes=9, cards=[
    definition(
        defbox('A <strong>sensor</strong> is an operator that <strong>waits until a condition is true</strong>: a file lands, a '
               'partition exists, an API returns "ready", another DAG\'s task finishes. It checks every <code>poke_interval</code> '
               'seconds and fails (or is skipped with <code>soft_fail=True</code>) after <code>timeout</code> seconds.'),
        tags('Sensor', 'FileSensor', 'poke_interval', 'timeout', 'mode=reschedule', 'deferrable', 'soft_fail', '@task.sensor'),
    ),
    sensor_modes_anim(),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task
from airflow.providers.standard.sensors.filesystem import FileSensor

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def sensor_demo():
    @task
    def upstream_system_drops_file():
        open("/tmp/marks_ready.flag", "w").write("ok")

    wait_for_marks = FileSensor(task_id="wait_for_marks", filepath="/tmp/marks_ready.flag",
                                poke_interval=2, timeout=20, mode="poke")

    wait_for_attendance = FileSensor(task_id="wait_for_attendance", filepath="/tmp/attendance.flag",
                                     poke_interval=2, timeout=5, mode="reschedule",
                                     soft_fail=True)          # timeout → skipped, not failed

    upstream_system_drops_file() >> wait_for_marks

sensor_demo()
''', 'sensor_demo', '2026-10-10', env=FS_CONN),
        title='Example: One Sensor Succeeds, One Times Out'),
    explanation(
        code('''
from airflow.sdk import task, PokeReturnValue

@task.sensor(poke_interval=60, timeout=3600, mode="reschedule")
def api_ready() -> PokeReturnValue:
    status = requests.get("https://partner.example.com/report/status").json()["status"]
    return PokeReturnValue(is_done=(status == "READY"), xcom_value=status)
''', '@task.sensor: Any Python Check as a Sensor', 'fa-brands fa-python'),
        title='Custom Sensors'),
    crossq(
        ('What happens when a sensor times out?', 'It raises AirflowSensorTimeout and fails (no retries for that error). With <code>soft_fail=True</code> it is marked skipped instead, and downstream tasks are skipped.'),
        ('Why can many poke-mode sensors deadlock a deployment?', 'Each holds a worker slot. If all slots are filled by sensors waiting for tasks that need a slot to run, nothing progresses. Use reschedule or deferrable mode.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What are deferrable operators and the triggerer?', 'Deferrable Operators & Triggerer', minutes=8, cards=[
    definition(
        defbox('A <strong>deferrable</strong> operator can suspend itself while waiting: it calls <code>self.defer(trigger=…, '
               'method_name=…)</code>, its state becomes <strong>deferred</strong> and its worker slot is freed. The '
               '<strong>trigger</strong> (small async code) runs in the <strong>triggerer</strong> process. When the trigger fires an '
               'event, the task is scheduled again and resumes in the named method.'),
        tags('Deferrable', 'Triggerer', 'Trigger', 'asyncio', 'deferred', 'self.defer'),
    ),
    example(
        dagtest('''
import pendulum
from datetime import timedelta
from airflow.sdk import dag, BaseOperator
from airflow.providers.standard.triggers.temporal import TimeDeltaTrigger

class WaitForReport(BaseOperator):
    """Toy deferrable operator: waits 3 seconds without holding a worker."""

    def execute(self, context):
        print("report not ready, deferring for 3 seconds (worker slot released)")
        self.defer(trigger=TimeDeltaTrigger(timedelta(seconds=3)), method_name="resume")

    def resume(self, context, event=None):          # runs on a worker after the trigger fires
        print("woke up in a worker again, report ready")
        return "done"

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def defer_demo():
    WaitForReport(task_id="wait_for_report")

defer_demo()
''', 'defer_demo', '2026-10-10'),
        title='Example: A Task Defers and Resumes'),
    explanation(
        ul('Many provider operators support <code>deferrable=True</code>: waiting for an EMR step, a Databricks run, a BigQuery job, an S3 key, an external DAG.',
           'A trigger must be <strong>async</strong> and must not block (no time.sleep, no blocking DB drivers).',
           'You need at least one <code>airflow triggerer</code> process running; without it deferred tasks wait forever.',
           '<code>airflow dags test</code> runs triggers in-line, which is why the example above works without a triggerer.'),
        title='Points to Remember'),
    crossq(
        ('Deferrable vs reschedule mode?', 'Reschedule still wakes a worker for every check. Deferrable hands the waiting to the triggerer, which can track thousands of waits in one event loop, so no worker is used at all while waiting.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What are hooks and connections? How do you store credentials?', 'Hooks & Connections', minutes=8, cards=[
    definition(
        defbox('A <strong>connection</strong> stores how to reach an external system: type, host, port, login, password, schema and '
               'extras, under a <code>conn_id</code>. A <strong>hook</strong> is a Python client that reads a connection and gives you '
               'methods such as <code>get_records()</code>, <code>load_file()</code> or <code>run()</code>. Operators use hooks internally.'),
        tags('Connection', 'conn_id', 'Hook', 'MySqlHook', 'S3Hook', 'AIRFLOW_CONN_', 'Secrets Backend'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task
from airflow.providers.sqlite.hooks.sqlite import SqliteHook

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def hook_demo():
    @task
    def load_and_query():
        hook = SqliteHook(sqlite_conn_id="school_db")     # same pattern: MySqlHook(mysql_conn_id=...)
        hook.run("DROP TABLE IF EXISTS fees")
        hook.run("CREATE TABLE fees (student TEXT, paid INT)")
        hook.insert_rows("fees", [("Anuj", 45000), ("Vineeta", 60000), ("Aarshvi", 30000)])
        rows = hook.get_records("SELECT student, paid FROM fees WHERE paid < 50000 ORDER BY paid")
        for r in rows:
            print("fee pending:", r)
        return len(rows)

    load_and_query()

hook_demo()
''', 'hook_demo', '2026-10-10', env=SCHOOL_CONN),
        title='Example: Using a Hook Inside a Task'),
    example(
        afcli(["airflow connections add mysql_src --conn-uri 'mysql://etl_reader:S3cret@db-replica.internal:3306/shop'",
               'airflow connections get mysql_src -o yaml'],
              setup_cmds=['airflow db reset -y']),
        title='Example: Creating a Connection from the CLI'),
    note('The password is stored encrypted (<code>is_encrypted: True</code>), but <code>connections get</code> decrypts it for '
         'whoever can run the CLI on an Airflow machine. Restrict shell access and keep production secrets in a secrets backend.', 'Notice'),
    table(['Where connections can live', 'Notes'], [
        ['Metadata DB (UI / CLI / API)', 'Passwords encrypted with the Fernet key'],
        ['Environment variables <code>AIRFLOW_CONN_&lt;ID&gt;</code>', 'URI or JSON; not visible in the UI; good for containers'],
        ['Secrets backend', 'AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager, Azure Key Vault: checked before the DB'],
    ]),
    warn('Never hard-code passwords in DAG files: they end up in Git and in every parsed copy. Use connections and a secrets backend. '
         'Airflow also masks values of sensitive fields (password, keys) in task logs.'),
    crossq(
        ('What is the Fernet key?', 'A symmetric key Airflow uses to encrypt connection passwords and variables in the metadata DB. Losing it means stored secrets cannot be decrypted.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('What are Variables? What is the problem with Variable.get() at the top level of a DAG file?', 'Variables', minutes=7, cards=[
    definition(
        defbox('<strong>Variables</strong> are global key–value settings (strings or JSON) shared by all DAGs: thresholds, e-mail lists, '
               'bucket names, feature flags. Read them with <code>Variable.get("key")</code> in task code or '
               '<code>{{ var.value.key }}</code> / <code>{{ var.json.key }}</code> in templates.'),
        tags('Variable', 'Variable.get', 'var.value', 'var.json', 'AIRFLOW_VAR_', 'Top-level code'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task, Variable
from airflow.providers.standard.operators.bash import BashOperator

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def variables_demo():
    @task
    def send_report():
        recipients = Variable.get("report_recipients", deserialize_json=True)   # read at RUN time
        threshold = int(Variable.get("min_attendance_pct", default=75))
        print(f"mailing {len(recipients)} people, threshold {threshold}%: {recipients}")

    BashOperator(task_id="templated",
                 bash_command="echo bucket={{ var.value.lake_bucket }} first={{ var.json.report_recipients[0] }}")
    send_report()

variables_demo()
''', 'variables_demo', '2026-10-10', env={
            'AIRFLOW_VAR_REPORT_RECIPIENTS': '["anuj@example.com", "vineeta@example.com", "aarshvi@example.com"]',
            'AIRFLOW_VAR_LAKE_BUCKET': 's3://upvanta-lake'}),
        title='Example (variables set as AIRFLOW_VAR_* environment variables)'),
    warn('Code at the top level of a DAG file runs every time the file is parsed (every 30 seconds by default, in every DAG processor). '
         '<code>Variable.get()</code> there means constant API/DB calls and slower parsing. Read variables inside tasks or through templates, '
         'which are evaluated only when the task runs.', 'Top-level Variable.get()'),
    comparison(
        table(['Use', 'Variables', 'Params', 'Connections'], [
            ['Scope', 'Global, all DAGs', 'One DAG run', 'Global'],
            ['Typical content', 'Settings, flags, lists', 'Run inputs (date, student)', 'Hosts and credentials'],
            ['Changed by', 'Admin/UI/CLI', 'Whoever triggers the run', 'Admin / secrets backend'],
        ]),
    ),
]),

# ------------------------------------------------------------------ 30
Q('How do you control concurrency? Explain pools, priority_weight, max_active_runs and max_active_tasks', 'Pools & Concurrency', minutes=8, cards=[
    definition(
        defbox('Several limits decide how many tasks run at once. <strong>Pools</strong> cap the number of running tasks that use a '
               'shared resource across all DAGs; <strong>priority_weight</strong> orders who gets a free slot first; DAG-level '
               '<strong>max_active_runs</strong> and <strong>max_active_tasks</strong> cap one DAG; <strong>parallelism</strong> caps the whole deployment.'),
        tags('Pool', 'pool_slots', 'priority_weight', 'max_active_runs', 'max_active_tasks', 'parallelism', 'max_active_tis_per_dag'),
    ),
    pools_anim(),
    table(['Setting', 'Level', 'Limits'], [
        ['<code>[core] parallelism</code>', 'Scheduler (each)', 'Running task instances in total'],
        ['<code>max_active_runs</code>', 'DAG', 'Concurrent DAG runs of this DAG (e.g. 1 for strictly sequential loads)'],
        ['<code>max_active_tasks</code>', 'DAG', 'Running tasks across all runs of this DAG'],
        ['<code>max_active_tis_per_dag</code>', 'Task', 'Running instances of one task (incl. mapped) across runs'],
        ['<code>pool</code>, <code>pool_slots</code>', 'Task', 'Slots taken from a named pool (default_pool has 128)'],
        ['<code>priority_weight</code>, <code>weight_rule</code>', 'Task', 'Order in which queued tasks get slots'],
    ]),
    example(
        afcli(['airflow pools set mysql_pool 2 "Max 2 parallel queries on the MySQL replica"', 'airflow pools list'],
              setup_cmds=['airflow db reset -y']),
        title='Example: Creating a Pool'),
    explanation(
        code('''
extract = SQLExecuteQueryOperator(
    task_id="extract_orders", conn_id="mysql_src", sql="sql/orders_delta.sql",
    pool="mysql_pool",            # wait for a free slot in this pool
    pool_slots=1,                 # a heavy query could take 2
    priority_weight=5,            # served before lower weights
)
''', 'Using the Pool', 'fa-brands fa-python'),
        title='Assigning Tasks to a Pool'),
    crossq(
        ('By default, how is priority_weight computed?', 'weight_rule="downstream": a task\'s effective priority is its own weight plus the weights of all its downstream tasks, so tasks that unblock more work start first.'),
    ),
]),

# ------------------------------------------------------------------ 31
Q('How do you write a custom operator?', 'Custom Operators', minutes=8, cards=[
    definition(
        defbox('Subclass <code>BaseOperator</code>, accept your arguments in <code>__init__</code> (passing <code>**kwargs</code> to '
               'super), and put the work in <code>execute(self, context)</code>. Its return value is pushed as an XCom. List the '
               'arguments that should accept Jinja templates in <code>template_fields</code>.'),
        tags('BaseOperator', 'execute', 'template_fields', 'Custom Operator', 'Hook', 'Plugin'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, BaseOperator

class RowCountCheckOperator(BaseOperator):
    """Fail the task if a table partition has fewer rows than expected."""
    template_fields = ("partition",)                 # rendered with Jinja before execute()

    def __init__(self, table: str, partition: str, min_rows: int, **kwargs):
        super().__init__(**kwargs)
        self.table, self.partition, self.min_rows = table, partition, min_rows

    def execute(self, context):
        counts = {"2026-10-10": 1240, "2026-10-09": 3}            # pretend query result
        rows = counts.get(self.partition, 0)
        self.log.info("table=%s partition=%s rows=%s", self.table, self.partition, rows)
        if rows < self.min_rows:
            raise ValueError(f"only {rows} rows in {self.table} for {self.partition}")
        return rows

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     default_args={"owner": "vineeta"})
def custom_operator_demo():
    RowCountCheckOperator(task_id="check_today", table="orders", partition="{{ ds }}", min_rows=100)
    RowCountCheckOperator(task_id="check_yesterday", table="orders",
                          partition="{{ macros.ds_add(ds, -1) }}", min_rows=100)

custom_operator_demo()
''', 'custom_operator_demo', '2026-10-10'),
        title='Example: A Reusable Data-quality Check'),
    explanation(
        ul('Keep <code>__init__</code> cheap: it runs at parse time. Connect to systems only inside <code>execute</code>.',
           'Use a hook for the connection logic so the operator stays thin and testable.',
           'Package shared operators as a Python package (or in <code>plugins/</code>) and install it on all workers.'),
        title='Good Practice'),
    crossq(
        ('Custom operator vs @task?', 'For one-off logic a @task function is simpler. Write an operator when the same configurable step is reused across many DAGs or teams.'),
    ),
]),

])
