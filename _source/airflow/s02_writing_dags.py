from build import *
from airflow.anims import *
from airflow.runner import dagtest, afcli, afpy

SECTION = dict(level='basic', title='Writing DAGs', questions=[

# ------------------------------------------------------------------ 7
Q('How do you write a DAG with classic operators?', 'First DAG (Classic Operators)', minutes=8, cards=[
    definition(
        defbox('A DAG file is a Python module in the dags folder. The classic style creates a <code>DAG</code> object (usually '
               'with a <code>with</code> block), instantiates operators inside it, and wires them with <code>&gt;&gt;</code>.'),
        tags('DAG', 'BashOperator', 'PythonOperator', 'with DAG', 'dag_id', 'task_id'),
    ),
    example(
        dagtest('''
import pendulum
from datetime import timedelta
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

def compute_grade():
    marks = {"Anuj": 82, "Vineeta": 91, "Aarshvi": 77}
    for name, m in marks.items():
        grade = "A" if m >= 85 else "B" if m >= 75 else "C"
        print(f"{name}: {m} -> {grade}")

with DAG(
    dag_id="grade_report",
    schedule="0 7 * * *",                       # every day at 07:00
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Kolkata"),
    catchup=False,
    default_args={"owner": "vineeta", "retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["reports"],
) as dag:
    download = BashOperator(task_id="download_marks", bash_command="echo downloading marks.csv")
    grade = PythonOperator(task_id="compute_grade", python_callable=compute_grade)
    notify = BashOperator(task_id="notify", bash_command="echo report ready for {{ ds }}")

    download >> grade >> notify
''', 'grade_report', '2026-10-10'),
        title='Example'),
    explanation(
        ul('<strong>dag_id</strong> must be unique across the deployment; <strong>task_id</strong> unique within the DAG.',
           '<strong>start_date</strong> should be a fixed, timezone-aware date (pendulum), never <code>datetime.now()</code>.',
           'Put arguments shared by all tasks in <strong>default_args</strong> (owner, retries, retry_delay, email …).',
           'The file is parsed every few seconds to minutes, so keep top-level code light: no DB queries or API calls outside tasks.'),
        title='Points to Remember'),
    crossq(
        ('Can one file contain several DAGs?', 'Yes. Every DAG object created at module level (or returned by a @dag function call) is picked up.'),
        ('Why did my bash_command ending in .sh fail with a Jinja error?', 'A bash_command ending in <code>.sh</code> is treated as a template <em>file</em> path. Add a trailing space (<code>"bash run.sh "</code>) or set <code>template_searchpath</code>.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What is the TaskFlow API? How is it different from classic operators?', 'TaskFlow API', minutes=8, cards=[
    definition(
        defbox('The <strong>TaskFlow API</strong> (Airflow 2.0+) turns plain Python functions into tasks with the '
               '<code>@task</code> decorator and DAGs with <code>@dag</code>. Return values are passed between tasks automatically '
               'through XCom, and calling one task with another\'s output also creates the dependency.'),
        tags('TaskFlow', '@dag', '@task', 'XCom', 'multiple_outputs', '@task.bash'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Kolkata"),
     catchup=False, default_args={"owner": "aarshvi"})
def sales_summary():

    @task
    def extract():
        return [{"rep": "Anuj", "amount": 52000}, {"rep": "Vineeta", "amount": 61000},
                {"rep": "Aarshvi", "amount": 47000}, {"rep": "Anuj", "amount": 18000}]

    @task(multiple_outputs=True)            # each dict key becomes its own XCom
    def transform(rows):
        totals = {}
        for r in rows:
            totals[r["rep"]] = totals.get(r["rep"], 0) + r["amount"]
        best = max(totals, key=totals.get)
        return {"totals": totals, "best_rep": best}

    @task.bash                              # the function returns a shell command
    def announce(best_rep):
        return f"echo 'Rep of the day: {best_rep}'"

    @task
    def load(totals):
        print(f"writing {len(totals)} rows to warehouse: {totals}")

    result = transform(extract())
    announce(result["best_rep"])
    load(result["totals"])

sales_summary()
''', 'sales_summary', '2026-10-10'),
        title='Example'),
    comparison(
        table(['Aspect', 'Classic operators', 'TaskFlow'], [
            ['Define a task', '<code>PythonOperator(task_id=…, python_callable=f)</code>', '<code>@task</code> on the function'],
            ['Pass data', 'Explicit <code>ti.xcom_pull(task_ids=…)</code>', 'Return value → function argument'],
            ['Dependencies', 'Written with <code>&gt;&gt;</code>', 'Inferred from data flow (can still use &gt;&gt;)'],
            ['Best for', 'Ready-made provider operators (SQL, S3, Spark …)', 'Python logic'],
        ]),
    ),
    interview(p('Real DAGs mix both: provider operators for external systems and @task functions for Python glue. They '
                'interoperate: a classic operator\'s <code>.output</code> can be passed into a @task, and <code>&gt;&gt;</code> works between them.')),
    crossq(
        ('Other TaskFlow decorators?', '<code>@task.bash</code>, <code>@task.branch</code>, <code>@task.short_circuit</code>, <code>@task.sensor</code>, <code>@task.virtualenv</code>, <code>@task.docker</code>, <code>@task.kubernetes</code>, <code>@task_group</code>.'),
        ('What does multiple_outputs=True do?', 'A returned dict is split into one XCom per key, so downstream tasks can take <code>result["totals"]</code> individually.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('How do you set task dependencies? Explain >>, <<, chain and cross_downstream', 'Task Dependencies', minutes=6, cards=[
    definition(
        defbox('Dependencies say which task must finish before another can start. Use <code>a &gt;&gt; b</code> (a before b), '
               '<code>a &lt;&lt; b</code> (b before a), lists for fan-out/fan-in, <code>chain()</code> for sequences and '
               '<code>cross_downstream()</code> to connect every task of one list to every task of another.'),
        tags('>>', '<<', 'set_downstream', 'chain', 'cross_downstream', 'Fan-out', 'Fan-in'),
    ),
    deps_anim(),
    example(
        afpy('''
from airflow.sdk import DAG, chain, cross_downstream
from airflow.providers.standard.operators.empty import EmptyOperator as E

with DAG("deps_demo", schedule=None) as dag:
    start, transform, load = E(task_id="start"), E(task_id="transform"), E(task_id="load")
    ex_o, ex_c = E(task_id="extract_orders"), E(task_id="extract_customers")
    start >> [ex_o, ex_c] >> transform >> load

    a1, a2, b1, b2 = (E(task_id=t) for t in ("a1", "a2", "b1", "b2"))
    cross_downstream([a1, a2], [b1, b2])

    s1, s2, s3 = E(task_id="s1"), E(task_id="s2"), E(task_id="s3")
    chain(s1, s2, s3)                     # same as s1 >> s2 >> s3

for t in dag.tasks:
    if t.upstream_task_ids:
        print(f"{t.task_id:<18} waits for {sorted(t.upstream_task_ids)}")
'''),
        title='Example: Checking the Wiring'),
    crossq(
        ('Is <code>[a, b] &gt;&gt; [c, d]</code> valid?', 'No: Python cannot apply &gt;&gt; between two lists (TypeError). Use cross_downstream, or a loop.'),
        ('How do you make a task depend on a task in another DAG?', 'Not with &gt;&gt;. Use Assets (data-aware scheduling), ExternalTaskSensor, or TriggerDagRunOperator. See the Scenarios section.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What are the commonly used operators and provider packages?', 'Common Operators & Providers', minutes=7, cards=[
    definition(
        defbox('Operators come in <strong>provider packages</strong> installed separately from Airflow core '
               '(<code>apache-airflow-providers-&lt;name&gt;</code>). The <strong>standard</strong> provider has the basics; others add '
               'operators, hooks and sensors for databases, clouds and tools.'),
        tags('Providers', 'EmptyOperator', 'BashOperator', 'PythonOperator', 'SQLExecuteQueryOperator', 'Hooks'),
    ),
    table(['Operator', 'Package', 'Use'], [
        ['EmptyOperator', 'standard', 'Placeholder / start and end markers / join points'],
        ['BashOperator, @task.bash', 'standard', 'Shell commands and scripts'],
        ['PythonOperator, @task', 'standard', 'Python callables'],
        ['TriggerDagRunOperator', 'standard', 'Start another DAG'],
        ['SQLExecuteQueryOperator', 'common-sql', 'Run SQL on any DB with a connection (MySQL, Postgres, Snowflake …)'],
        ['S3CreateObjectOperator, GlueJobOperator, EmrAddStepsOperator', 'amazon', 'AWS services'],
        ['SparkSubmitOperator', 'apache-spark', 'spark-submit a job'],
        ['DatabricksRunNowOperator', 'databricks', 'Run a Databricks job'],
        ['KubernetesPodOperator', 'cncf-kubernetes', 'Run any container as a task'],
        ['EmailOperator', 'smtp', 'Send email'],
    ]),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def sql_demo():
    start = EmptyOperator(task_id="start")
    create = SQLExecuteQueryOperator(
        task_id="create_and_fill", conn_id="school_db",
        sql=["DROP TABLE IF EXISTS marks",
             "CREATE TABLE marks (name TEXT, subject TEXT, score INT)",
             "INSERT INTO marks VALUES ('Anuj','SQL',82), ('Vineeta','SQL',91), ('Aarshvi','SQL',77), "
             "('Anuj','Spark',88), ('Vineeta','Spark',79), ('Aarshvi','Spark',93)"])
    report = SQLExecuteQueryOperator(
        task_id="toppers", conn_id="school_db",
        sql="SELECT subject, name, MAX(score) FROM marks GROUP BY subject ORDER BY subject")

    @task
    def show(rows):                       # query result arrives through XCom
        for subject, name, score in rows:
            print(f"{subject}: {name} ({score})")

    start >> create >> report
    show(report.output)

sql_demo()
''', 'sql_demo', '2026-10-10', env={'AIRFLOW_CONN_SCHOOL_DB': '{"conn_type": "sqlite", "host": "/tmp/school.db"}'}),
        title='Example: SQL Through a Connection'),
    note('The connection <code>school_db</code> was defined with an environment variable '
         '<code>AIRFLOW_CONN_SCHOOL_DB=\'{"conn_type": "sqlite", "host": "/tmp/school.db"}\'</code> (JSON form; a URI also works for most databases). In production you would point the same conn_id at MySQL or Snowflake '
         'without changing the DAG.', 'Connection'),
    crossq(
        ('Operator vs hook?', 'A <strong>hook</strong> is a reusable client for an external system (connect, run query, upload file). Operators use hooks internally; inside @task code you can use hooks directly.'),
    ),
]),

# ------------------------------------------------------------------ 11
Q('What are default_args? How do retries, retry_delay and execution_timeout work?', 'default_args, Retries & Timeouts', minutes=7, cards=[
    definition(
        defbox('<strong>default_args</strong> is a dict of operator arguments applied to every task in the DAG (a task can override '
               'any of them). The most important are <strong>owner</strong>, <strong>retries</strong>, <strong>retry_delay</strong>, '
               '<strong>retry_exponential_backoff</strong>, <strong>execution_timeout</strong> and failure callbacks.'),
        tags('default_args', 'retries', 'retry_delay', 'retry_exponential_backoff', 'execution_timeout', 'up_for_retry'),
    ),
    example(
        dagtest('''
import time, pendulum
from datetime import timedelta
from airflow.sdk import dag, task, get_current_context

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     default_args={"owner": "anuj", "retries": 1, "retry_delay": timedelta(seconds=2)})
def retry_demo():

    @task
    def call_flaky_api():
        ti = get_current_context()["ti"]
        print(f"attempt {ti.try_number}")
        if ti.try_number == 1:
            raise ConnectionError("API timed out")      # transient error on the first try
        return "200 OK"

    @task(retries=0, execution_timeout=timedelta(seconds=2))
    def slow_query():
        time.sleep(5)                                   # takes longer than allowed

    call_flaky_api() >> slow_query()

retry_demo()
''', 'retry_demo', '2026-10-10'),
        title='Example: A Retry That Recovers, and a Timeout'),
    explanation(
        ul('<code>call_flaky_api</code> failed on attempt 1, went to <strong>up_for_retry</strong>, and succeeded on attempt 2.',
           '<code>slow_query</code> was killed after 2 seconds (<code>AirflowTaskTimeout</code>) and, with <code>retries=0</code>, ended <strong>failed</strong>, so the DAG run failed.',
           'Retries help with <em>transient</em> errors (network, locks, rate limits). They do not fix bad code or bad data, so keep them small (1–3).'),
        title='What Happened'),
    crossq(
        ('What is retry_exponential_backoff?', 'Each retry waits longer (roughly doubling retry_delay, capped by max_retry_delay). Good for rate-limited APIs.'),
        ('Why set execution_timeout?', 'A hung task (stuck query, dead connection) would otherwise occupy a worker slot forever and block downstream tasks. A timeout turns it into a visible failure that can be retried or alerted.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How does Jinja templating work in Airflow? What are macros like {{ ds }}?', 'Jinja Templating & Macros', minutes=7, cards=[
    definition(
        defbox('Many operator arguments (<code>bash_command</code>, <code>sql</code>, file paths …) are <strong>templated</strong>: '
               'Airflow renders them with Jinja just before the task runs, filling in run-specific values such as the logical '
               'date. This lets one DAG process "today\'s" data without hard-coding dates.'),
        tags('Jinja', 'Templates', '{{ ds }}', 'logical_date', 'macros', 'params', 'template_fields'),
    ),
    table(['Template variable', 'Example value', 'Meaning'], [
        ['<code>{{ ds }}</code>', '2026-10-10', 'Logical date as YYYY-MM-DD'],
        ['<code>{{ ds_nodash }}</code>', '20261010', 'Same, without dashes (file names, partitions)'],
        ['<code>{{ logical_date }}</code>', 'DateTime object', 'Logical date of the run'],
        ['<code>{{ data_interval_start }}</code> / <code>_end</code>', 'DateTime', 'The data interval of the run'],
        ['<code>{{ macros.ds_add(ds, -1) }}</code>', '2026-10-09', 'Date arithmetic'],
        ['<code>{{ params.x }}</code>', 'any', 'DAG/task params, overridable when triggering'],
        ['<code>{{ var.value.key }}</code>, <code>{{ conn.my_db.host }}</code>', '', 'Variables and connections'],
        ['<code>{{ dag.dag_id }}</code>, <code>{{ task.task_id }}</code>, <code>{{ run_id }}</code>', '', 'Run metadata'],
    ]),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task, get_current_context
from airflow.providers.standard.operators.bash import BashOperator

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     params={"city": "Pune"})
def templating_demo():
    BashOperator(
        task_id="render",
        bash_command=(
            "echo ds={{ ds }} ds_nodash={{ ds_nodash }} yesterday={{ macros.ds_add(ds, -1) }}; "
            "echo path=s3://lake/sales/dt={{ ds }}/ city={{ params.city }} dag={{ dag.dag_id }}"
        ),
    )

    @task
    def from_context():
        ctx = get_current_context()          # same values inside Python tasks
        print("logical_date:", ctx["logical_date"], "| ds:", ctx["ds"])

    from_context()

templating_demo()
''', 'templating_demo', '2026-10-10'),
        title='Example'),
    warn('Templates are rendered only in fields listed in the operator\'s <code>template_fields</code>, and only at run time. '
         '<code>{{ ds }}</code> written in top-level Python code or in a non-templated argument stays a literal string.', 'Gotcha'),
    crossq(
        ('Why use {{ ds }} instead of datetime.today()?', 'Re-running or backfilling a past date must process that date\'s data. {{ ds }} is tied to the run; today() always returns the current day, so reruns would load the wrong partition.'),
        ('How do you see the rendered value?', 'The "Rendered Template" tab of the task instance in the UI, or <code>airflow tasks render &lt;dag&gt; &lt;task&gt; &lt;date&gt;</code>.'),
    ),
]),

])
