from build import *
from airflow.anims import *
from airflow.runner import dagtest, afcli, afpy

STUDENT_DAG = '''
import pendulum
from airflow.sdk import dag, task

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Kolkata"),
     catchup=False, tags=["upvanta"], default_args={"owner": "vineeta"})
def student_results():
    @task
    def extract():
        return [{"name": "Anuj", "marks": 82}, {"name": "Vineeta", "marks": 91}, {"name": "Aarshvi", "marks": 77}]

    @task
    def top_scorer(rows):
        best = max(rows, key=lambda r: r["marks"])
        print(f"Top scorer: {best['name']} ({best['marks']})")
        return best["name"]

    top_scorer(extract())

student_results()
'''

SECTION = dict(level='beginner', title='Airflow Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is Apache Airflow? Why use it instead of cron?', 'What is Airflow?', minutes=7, cards=[
    definition(
        defbox('<strong>Apache Airflow</strong> is an open-source platform to <strong>author, schedule and monitor workflows</strong> '
               'as code. A workflow is a Python-defined <strong>DAG</strong> of tasks with dependencies; Airflow decides when each '
               'task should run, runs it on workers, retries failures and records everything in a database and UI.',
               'It was created at Airbnb in 2014 and is an Apache top-level project. Airflow 3.0 was released in April 2025; '
               'this module uses <strong>Airflow 3.3</strong> and notes where Airflow 2 differs.'),
        hl('Airflow is an <strong>orchestrator</strong>, not a processing engine. It tells Spark, SQL, dbt or a Python script '
           '<em>when</em> to run and in which order; the heavy data work happens in those systems.', 'Key idea'),
        tags('Orchestration', 'Workflow as Code', 'DAG', 'Scheduler', 'Open Source', 'Airflow 3'),
    ),
    comparison(
        table(['Need', 'cron', 'Airflow'], [
            ['Dependencies between jobs', 'None: guess times ("load at 2 AM, report at 3 AM")', 'Explicit: report runs after load succeeds'],
            ['Retries', 'Write it yourself', 'retries=3, retry_delay=5 min per task'],
            ['Monitoring', 'Grep log files', 'UI with run history, task states, logs, durations'],
            ['Re-running past dates', 'Manual', 'Backfill / clear a date range'],
            ['Alerts', 'Manual', 'Callbacks, email/Slack on failure'],
            ['Scaling', 'One machine', 'Distributed workers (Celery, Kubernetes)'],
            ['Integrations', 'Shell scripts', '80+ provider packages: AWS, GCP, Databricks, Snowflake, MySQL …'],
        ]),
        title='cron vs Airflow'),
    explanation(
        p('Airflow is a good fit for <strong>batch</strong> pipelines that run on a schedule or when data arrives: ETL/ELT, '
          'ML training, reports, data-quality checks. It is <strong>not</strong> a streaming engine (use Kafka/Flink/Spark '
          'Streaming), and it is not meant to move large volumes of data between its own tasks.'),
        title='When to Use It'),
    crossq(
        ('Is Airflow an ETL tool?', 'No. It orchestrates ETL. The extract/transform/load work is done by the systems the tasks call (SQL engines, Spark, Python, dbt).'),
        ('Name some alternatives.', 'Prefect, Dagster, Luigi (older), Apache Oozie (Hadoop), Azure Data Factory, AWS Step Functions, Argo Workflows. Managed Airflow: AWS MWAA, Google Cloud Composer, Astronomer.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain the Airflow architecture and its components', 'Airflow Architecture', minutes=9, cards=[
    definition(
        defbox('An Airflow deployment is a set of cooperating services around a <strong>metadata database</strong>: the '
               '<strong>DAG processor</strong> parses DAG files, the <strong>scheduler</strong> decides what should run, the '
               '<strong>executor</strong> and <strong>workers</strong> run tasks, the <strong>API server</strong> serves the UI and '
               'APIs, and the <strong>triggerer</strong> handles deferred (async) waits.'),
        tags('Scheduler', 'DAG Processor', 'Executor', 'Worker', 'API Server', 'Triggerer', 'Metadata DB'),
    ),
    arch_anim(),
    explanation(
        table(['Component', 'Job', 'Notes'], [
            ['Metadata DB', 'Stores serialized DAGs, DAG runs, task instances, XComs, connections, variables', 'PostgreSQL or MySQL in production; SQLite only for local testing'],
            ['DAG processor', 'Parses DAG files and serializes them', 'A separate process in Airflow 3 (was inside the scheduler in Airflow 2)'],
            ['Scheduler', 'Creates DAG runs, checks dependencies, queues tasks', 'Several can run at once for high availability'],
            ['Executor', 'Decides where/how queued tasks run', 'Configured setting, runs inside the scheduler'],
            ['Workers', 'Execute the task code', 'Use the Task SDK; talk to the API server, not the DB'],
            ['API server', 'Web UI, REST API, Task Execution API', 'Replaces the Airflow 2 "webserver"'],
            ['Triggerer', 'Runs async triggers for deferrable tasks', 'Needed for deferrable sensors/operators'],
        ]),
    ),
    crossq(
        ('Why did Airflow 3 stop workers from accessing the DB directly?', 'Security and isolation: task code (which can be anything) no longer holds database credentials, and it enables remote/edge workers and task SDKs in other languages.'),
        ('What happens if the scheduler stops?', 'Running tasks finish, but nothing new is scheduled. That is why production setups run 2+ schedulers (active-active, coordinated through DB row locks).'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What is a DAG? Why must it be acyclic?', 'What is a DAG?', minutes=6, cards=[
    definition(
        defbox('A <strong>DAG (Directed Acyclic Graph)</strong> is a collection of tasks with directed dependencies and no cycles. '
               'In Airflow a DAG also carries scheduling settings: <code>dag_id</code>, <code>schedule</code>, <code>start_date</code>, '
               '<code>catchup</code>, default arguments and tags.'),
        tags('DAG', 'Directed', 'Acyclic', 'dag_id', 'Graph'),
    ),
    dag_anim(),
    example(
        afpy('''
from airflow.sdk import DAG
from airflow.providers.standard.operators.empty import EmptyOperator

with DAG("cycle_demo", schedule=None) as dag:
    a = EmptyOperator(task_id="A")
    b = EmptyOperator(task_id="B")
    c = EmptyOperator(task_id="C")
    a >> b >> c >> a            # cycle!

print("Python accepted the definition")
dag.check_cycle()              # the DAG processor runs this check when it parses the file
''', expect_error=True),
        title='Example: Airflow Detects the Cycle'),
    crossq(
        ('Can a DAG have just one task?', 'Yes. A DAG is simply the unit Airflow schedules; one task is valid.'),
        ('How do you repeat something "until done" without a cycle?', 'Use a sensor (wait until a condition is true), dynamic task mapping (N parallel copies), or trigger a new DAG run at the end.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What is the difference between an Operator, a Task, a Task Instance and a DAG Run?', 'Operator vs Task vs Task Instance', minutes=6, cards=[
    definition(
        defbox('An <strong>operator</strong> is a template class for a kind of work (BashOperator, PythonOperator). A '
               '<strong>task</strong> is an operator placed in a DAG with a <code>task_id</code>. A <strong>DAG run</strong> is one '
               'execution of the DAG for a logical date, and a <strong>task instance</strong> is one execution of a task within a DAG run.'),
        tags('Operator', 'Task', 'Task Instance', 'DAG Run', 'try_number'),
    ),
    table(['Concept', 'Analogy (class → object → execution)', 'Identified by'], [
        ['Operator', 'A class', 'Python class name'],
        ['Task', 'An object of that class inside a DAG', 'dag_id + task_id'],
        ['DAG run', 'One "day" of the whole workflow', 'dag_id + run_id (logical date)'],
        ['Task instance', 'That task in that run, with a state', 'dag_id + task_id + run_id (+ map_index), tries counted by try_number'],
    ]),
    explanation(
        p('Three kinds of operators: <strong>action operators</strong> do something (BashOperator, SQLExecuteQueryOperator), '
          '<strong>transfer operators</strong> move data between systems (S3ToRedshiftOperator), and <strong>sensors</strong> '
          'wait for a condition (FileSensor, ExternalTaskSensor).'),
        title='Types of Operators'),
    example(
        afpy('''
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator

with DAG("attendance", schedule="@daily") as dag:
    start = EmptyOperator(task_id="start")
    greet = BashOperator(task_id="greet", bash_command="echo Hello Anuj, Vineeta and Aarshvi")
    start >> greet

for t in dag.tasks:                       # tasks = operator objects bound to this DAG
    print(f"task_id={t.task_id:<6} operator={type(t).__name__:<14} downstream={sorted(t.downstream_task_ids)}")
'''),
        title='Example: Tasks Are Operator Objects in a DAG'),
    crossq(
        ('What is a task\'s try_number?', 'How many times this task instance has been attempted. With retries=2 a failing task runs with try_number 1, 2, 3 before ending as failed.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What changed in Airflow 3 compared with Airflow 2?', 'Airflow 3 vs Airflow 2', minutes=8, cards=[
    definition(
        defbox('Airflow 3 (April 2025) is the first major release since 2.0 (2020). It changes the architecture (task execution '
               'through an API), introduces DAG versioning and a new React UI, renames Datasets to <strong>Assets</strong>, and '
               'removes several long-deprecated features.'),
        tags('Airflow 3', 'Task SDK', 'Assets', 'DAG Versioning', 'API Server', 'Breaking Changes'),
    ),
    table(['Area', 'Airflow 2', 'Airflow 3'], [
        ['DAG authoring imports', '<code>from airflow import DAG</code>, <code>airflow.decorators</code>', '<code>from airflow.sdk import DAG, dag, task, Asset …</code>'],
        ['Core operators', '<code>airflow.operators.bash</code>', '<code>airflow.providers.standard.operators.bash</code>'],
        ['Task execution', 'Workers connect to the metadata DB', 'Workers use the Task Execution API (API server)'],
        ['Web server', '<code>airflow webserver</code> (Flask)', '<code>airflow api-server</code> (FastAPI), new React UI'],
        ['DAG parsing', 'Inside the scheduler', 'Separate <code>airflow dag-processor</code>'],
        ['Data-aware scheduling', 'Datasets', 'Assets (+ asset watchers for external events)'],
        ['Schedule argument', '<code>schedule_interval</code> (deprecated)', 'Only <code>schedule</code>'],
        ['@daily cron meaning', 'Data interval (runs at end of the day)', 'Trigger timetable by default (runs at the time, no interval)'],
        ['catchup default', 'True', 'False'],
        ['Context keys', '<code>execution_date</code>, <code>next_ds</code>, …', 'Removed: use <code>logical_date</code>, <code>data_interval_start/end</code>'],
        ['Removed', 'SubDAGs, SLA miss callbacks, SequentialExecutor, direct DB access from tasks', '—'],
        ['Backfill', 'CLI process', 'Run by the scheduler, started from UI / API / CLI'],
        ['DAG versions', 'Only the latest code is known', 'Each run is tied to the DAG version it ran with'],
    ]),
    interview(p('If an interviewer asks about "execution_date", answer with the Airflow 3 term <strong>logical_date</strong> and '
                'mention that it was renamed in 2.2 and removed in 3.0. It shows you know current Airflow, not just old tutorials.')),
    crossq(
        ('How do you upgrade DAGs to Airflow 3?', 'Run the <code>ruff</code> Airflow rules (<code>ruff check --select AIR3</code>) which flag removed imports and arguments, fix them, test with <code>airflow dags test</code>, and upgrade providers.'),
    ),
]),

# ------------------------------------------------------------------ 6
Q('Which Airflow CLI commands should you know?', 'Airflow CLI', minutes=6, cards=[
    definition(
        defbox('The <code>airflow</code> command line starts the services and lets you inspect and test DAGs without the UI. '
               'In interviews, the commands for <strong>testing</strong> and <strong>debugging</strong> matter most.'),
        tags('airflow dags test', 'airflow tasks test', 'list-import-errors', 'db migrate', 'standalone'),
    ),
    table(['Command', 'Purpose'], [
        ['<code>airflow standalone</code>', 'Start everything locally (dev only) with an admin user'],
        ['<code>airflow db migrate</code>', 'Create / upgrade the metadata DB schema'],
        ['<code>airflow scheduler</code>, <code>api-server</code>, <code>dag-processor</code>, <code>triggerer</code>', 'Start individual services'],
        ['<code>airflow dags list</code> / <code>list-import-errors</code>', 'See loaded DAGs / files that failed to parse'],
        ['<code>airflow dags test &lt;dag&gt; [date]</code>', 'Run a whole DAG once in one process (no scheduler needed)'],
        ['<code>airflow tasks test &lt;dag&gt; &lt;task&gt; [date]</code>', 'Run one task without recording state or checking dependencies'],
        ['<code>airflow dags trigger &lt;dag&gt; -c \'{...}\'</code>', 'Trigger a run with config'],
        ['<code>airflow tasks clear &lt;dag&gt; -t &lt;regex&gt; -s … -e …</code>', 'Re-run tasks for a date range'],
        ['<code>airflow backfill create --dag-id … --from-date … --to-date …</code>', 'Backfill past dates (Airflow 3)'],
    ]),
    example(
        afcli(['airflow dags list -o plain', 'airflow tasks list student_results', 'airflow dags list-import-errors'],
              src=STUDENT_DAG, name='student_results', setup_cmds=['airflow db reset -y', 'airflow dags reserialize']),
        title='Example: Inspecting a DAG'),
    example(
        dagtest(STUDENT_DAG, 'student_results', '2026-10-10'),
        title='Example: airflow dags test student_results 2026-10-10'),
    crossq(
        ('dags test vs tasks test?', '<code>dags test</code> runs every task in dependency order and creates a real DAG run. <code>tasks test</code> runs a single task in isolation, ignoring upstream state, which is handy while developing one task.'),
    ),
]),

])
