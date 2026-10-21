from build import *
from airflow.anims import *
from airflow.runner import dagtest, afcli, afpy

WH_CONN = {'AIRFLOW_CONN_WAREHOUSE': '{"conn_type": "sqlite", "host": "/tmp/warehouse.db"}'}

SECTION = dict(level='expert', title='Best Practices & Operations', questions=[

# ------------------------------------------------------------------ 36
Q('What does it mean for a task to be idempotent? Why does it matter in Airflow?', 'Idempotent Tasks', minutes=9, cards=[
    definition(
        defbox('A task is <strong>idempotent</strong> if running it several times for the same DAG run gives the same final '
               'result as running it once. Airflow re-runs tasks all the time (retries, clears, backfills), so non-idempotent tasks '
               'silently create duplicates or wrong totals.',
               'Tasks should also be <strong>atomic</strong>: either the whole result is written or nothing is, so a crash halfway '
               'never leaves a half-loaded table.'),
        tags('Idempotency', 'Atomicity', 'Retries', 'Backfill', 'DELETE + INSERT', 'MERGE', 'Partition Overwrite'),
    ),
    idempotency_anim(),
    example(
        dagtest('''
import pendulum
from datetime import timedelta
from airflow.sdk import dag, task, get_current_context
from airflow.providers.sqlite.hooks.sqlite import SqliteHook

ROWS = [("2026-10-10", "Anuj", 52000), ("2026-10-10", "Vineeta", 61000), ("2026-10-10", "Aarshvi", 47000)]

def crash_on_first_try():
    if get_current_context()["ti"].try_number == 1:
        raise RuntimeError("worker lost after writing")      # simulate a failure AFTER the insert

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     default_args={"retries": 1, "retry_delay": timedelta(seconds=1)})
def idempotency_demo():
    @task(retries=0)
    def setup():
        h = SqliteHook(sqlite_conn_id="warehouse")
        for t in ("sales_naive", "sales_idempotent"):
            h.run(f"DROP TABLE IF EXISTS {t}")
            h.run(f"CREATE TABLE {t} (dt TEXT, rep TEXT, amount INT)")

    @task
    def load_naive(ds=None):
        h = SqliteHook(sqlite_conn_id="warehouse")
        h.insert_rows("sales_naive", ROWS)                       # plain append
        crash_on_first_try()

    @task
    def load_idempotent(ds=None):
        h = SqliteHook(sqlite_conn_id="warehouse")
        conn = h.get_conn()
        with conn:                                              # one transaction
            conn.execute("DELETE FROM sales_idempotent WHERE dt = ?", (ds,))
            conn.executemany("INSERT INTO sales_idempotent VALUES (?, ?, ?)", ROWS)
        crash_on_first_try()

    @task(retries=0)
    def compare():
        h = SqliteHook(sqlite_conn_id="warehouse")
        for t in ("sales_naive", "sales_idempotent"):
            print(f"{t:<17}: {h.get_first(f'SELECT COUNT(*) FROM {t}')[0]} rows (expected 3)")

    setup() >> [load_naive(), load_idempotent()] >> compare()

idempotency_demo()
''', 'idempotency_demo', '2026-10-10', env=WH_CONN),
        title='Example: Same Crash, Two Loading Styles'),
    table(['Pattern', 'Idempotent?', 'Better'], [
        ['INSERT INTO target SELECT … (append)', 'No', 'DELETE the run\'s partition + INSERT, in one transaction'],
        ['Write file <code>out_{now}.csv</code>', 'No (new file each run)', 'Write <code>dt={{ ds }}/part.parquet</code> and overwrite'],
        ['Process "rows since last run" stored in a variable', 'No (state changes)', 'Process the run\'s data interval'],
        ['Send an e-mail / call a payment API', 'No by nature', 'Make it the last step; use dedup keys on the receiving side'],
        ['MERGE / upsert on a business key', 'Yes', '—'],
    ]),
    crossq(
        ('Is a task that reads datetime.now() idempotent?', 'No. A retry tomorrow processes a different period. Use logical_date / data_interval from the context.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Why should you avoid top-level code in DAG files? How do you keep parsing fast?', 'Top-level Code & DAG Parsing', minutes=8, cards=[
    definition(
        defbox('<strong>Top-level code</strong> is anything in a DAG file outside task callables and templates. It runs every time '
               'the file is <strong>parsed</strong>, which happens continuously, not when the DAG runs. Slow or side-effecting top-level '
               'code delays every DAG in the deployment and can cause parse timeouts.'),
        tags('Top-level Code', 'DAG Parsing', 'dagbag_import_timeout', 'min_file_process_interval', 'airflow dags report'),
    ),
    parsing_anim(),
    example(
        afcli(['airflow dags report -o plain'],
              src={
                  'fast_dag': '''
import pendulum
from airflow.sdk import dag, task

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def fast_dag():
    @task
    def get_students():
        import json, urllib.request            # heavy work and imports INSIDE the task
        return ["Anuj", "Vineeta", "Aarshvi"]
    get_students()

fast_dag()
''',
                  'slow_dag': '''
import time, pendulum
from airflow.sdk import dag, task

time.sleep(2)                                   # stands in for an API call / DB query at top level
STUDENTS = ["Anuj", "Vineeta", "Aarshvi"]

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def slow_dag():
    @task
    def get_students():
        return STUDENTS
    get_students()

slow_dag()
'''}),
        title='Example: Parse Time per File'),
    explanation(
        ul('No API calls, DB queries, <code>Variable.get()</code> or file reads at module level; do them in tasks or templates.',
           'Import heavy libraries (pandas, sklearn, boto3 clients) <strong>inside</strong> the task function.',
           'Generate many DAGs from a <em>local</em> config file (YAML/JSON in the repo), not from a remote API.',
           'Use <code>.airflowignore</code> for helper modules and SQL files in the dags folder.',
           'Check with <code>airflow dags report</code> and the DAG processor metrics.'),
        title='Rules'),
]),

# ------------------------------------------------------------------ 38
Q('How do you test Airflow DAGs?', 'Testing DAGs', minutes=8, cards=[
    definition(
        defbox('Test at three levels: (1) <strong>DAG integrity</strong>: every file imports without errors and follows team rules '
               '(tags, owners, retries, no cycles); (2) <strong>unit tests</strong> of task logic as plain Python; (3) '
               '<strong>end-to-end</strong> runs with <code>airflow dags test</code> or <code>dag.test()</code> against test data. Run them in CI.'),
        tags('pytest', 'DagBag', 'DAG Integrity Test', 'Unit Test', 'airflow dags test', 'CI'),
    ),
    example(
        afcli(['pytest -q test_dags.py'],
              src={'student_results': '''
import pendulum
from airflow.sdk import dag, task

def grade(marks: int) -> str:
    return "A" if marks >= 85 else "B" if marks >= 75 else "C"

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     tags=["upvanta"], default_args={"owner": "vineeta", "retries": 2})
def student_results():
    @task
    def grade_all():
        return {n: grade(m) for n, m in {"Anuj": 82, "Vineeta": 91, "Aarshvi": 77}.items()}
    grade_all()

student_results()
''',
                   'untagged': '''
import pendulum
from airflow.sdk import dag, task

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"))
def untagged():
    @task
    def hello():
        print("hi")
    hello()

untagged()
'''},
              files={'/tmp/aftests/test_dags.py': '''
import os, sys, pytest
from airflow.models import DagBag

DAGS_DIR = os.path.join(os.environ["AIRFLOW_HOME"], "dags")
dagbag = DagBag(dag_folder=DAGS_DIR)

def test_no_import_errors():
    assert dagbag.import_errors == {}, dagbag.import_errors

@pytest.mark.parametrize("dag_id", sorted(dagbag.dag_ids))
def test_team_rules(dag_id):
    dag = dagbag.get_dag(dag_id)
    assert dag.tags, f"{dag_id} has no tags"
    assert all(t.retries >= 1 for t in dag.tasks), f"{dag_id}: every task needs retries"

def test_grade_function():                        # unit test of plain Python logic
    sys.path.insert(0, DAGS_DIR)
    from student_results import grade
    assert [grade(91), grade(82), grade(60)] == ["A", "B", "C"]
'''}),
        title='Example: pytest Finds a DAG That Breaks Team Rules'),
    explanation(
        ul('Keep business logic in plain functions (or a package) so it can be unit-tested without Airflow.',
           'Integrity tests catch most production incidents: broken imports, missing providers, cycles, wrong arguments.',
           'For end-to-end tests use a separate Airflow home/DB and test connections pointing to test databases.',
           'In CI: lint (ruff, including the Airflow AIR rules) → pytest → deploy DAGs.'),
        title='Good Practice'),
]),

# ------------------------------------------------------------------ 39
Q('How do you get alerted when a task fails? Explain callbacks and what replaced SLAs', 'Callbacks & Alerting', minutes=7, cards=[
    definition(
        defbox('Tasks and DAGs accept <strong>callbacks</strong>: <code>on_failure_callback</code>, <code>on_success_callback</code>, '
               '<code>on_retry_callback</code>, <code>on_execute_callback</code> and <code>on_skipped_callback</code>. Each receives the '
               'context and typically posts to Slack/Teams/e-mail or PagerDuty. Airflow 3 removed SLA-miss callbacks; '
               '<strong>Deadline Alerts</strong> (3.1+) replace them.'),
        tags('on_failure_callback', 'on_retry_callback', 'Notifier', 'Slack', 'email_on_failure', 'Deadline Alerts', 'SLA'),
    ),
    example(
        dagtest('''
import pendulum
from datetime import timedelta
from airflow.sdk import dag, task

def alert_on_failure(context):
    ti = context["ti"]
    print(f"ALERT to #data-alerts: {ti.dag_id}.{ti.task_id} failed on try {ti.try_number} "
          f"for {context['ds']}: {context.get('exception')!r} (owner: aarshvi)")

def note_retry(context):
    print(f"retrying {context['ti'].task_id} ...")

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     default_args={"retries": 1, "retry_delay": timedelta(seconds=1),
                   "on_failure_callback": alert_on_failure, "on_retry_callback": note_retry})
def alerting_demo():
    @task
    def load_marks():
        raise PermissionError("access denied to s3://lake/marks/")

    load_marks()

alerting_demo()
''', 'alerting_demo', '2026-10-10'),
        title='Example: Retry Callback, Then Failure Alert'),
    explanation(
        code('''
from airflow.providers.slack.notifications.slack import SlackNotifier

@dag(..., on_failure_callback=SlackNotifier(slack_conn_id="slack_alerts",
                                            text="{{ dag.dag_id }} failed for {{ ds }}",
                                            channel="#data-alerts"))
''', 'Notifiers: Ready-made Callbacks', 'fa-brands fa-python'),
        title='Production Alerting'),
    crossq(
        ('Task-level vs DAG-level on_failure_callback?', 'Task-level (often via default_args) fires for each failed task. DAG-level fires once when the whole DAG run fails, which avoids alert storms.'),
        ('How do you alert when a job is late rather than failed?', 'Airflow 3.1+ Deadline Alerts (e.g. "alert if the run has not finished 2 hours after its scheduled time"). In Airflow 2 this was the SLA feature, now removed.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('A task failed in production. How do you debug and recover?', 'Debugging Failures', minutes=8, cards=[
    definition(
        defbox('Read the task log first (UI → task instance → Logs), reproduce locally with <code>airflow tasks test</code> or '
               '<code>dags test</code>, fix the cause, then <strong>clear</strong> the failed task (and its downstream) so the scheduler '
               're-runs it for the same logical date. Never edit data by hand without re-running the pipeline.'),
        tags('Logs', 'Clear', 'Mark Success', 'airflow tasks test', 'Rendered Template', 'Root Cause'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def debug_demo():
    @task
    def extract():
        return [{"name": "Anuj", "marks": 82}, {"name": "Vineeta", "marks": 91}, {"student": "Aarshvi", "marks": 77}]

    @task
    def transform(rows):
        return {r["name"]: r["marks"] for r in rows}      # third row uses "student", not "name"

    @task
    def load(d):
        print("loaded", d)

    load(transform(extract()))

debug_demo()
''', 'debug_demo', '2026-10-10'),
        title='Example: Schema Drift Breaks a Task'),
    table(['Step', 'How'], [
        ['1. Read the log and the exception', 'UI Logs tab; the traceback shows <code>KeyError: \'name\'</code> in transform'],
        ['2. Check inputs', 'XCom tab of extract; Rendered Template tab for templated SQL/commands'],
        ['3. Reproduce', '<code>airflow tasks test debug_demo transform 2026-10-10</code> with a breakpoint or extra logging'],
        ['4. Fix', 'Handle the new field / fix the source contract; add a data check upstream'],
        ['5. Re-run', 'Clear <code>transform</code> with "Downstream" checked; or <code>airflow tasks clear debug_demo -t transform -d -s 2026-10-10 -e 2026-10-10</code>'],
        ['6. Prevent', 'Test with this case; alert earlier; contract/schema checks'],
    ]),
    warn('"Mark success" makes Airflow <em>believe</em> a task ran. Use it only when the work was really done outside Airflow, '
         'otherwise downstream tasks run on missing data.'),
]),

# ------------------------------------------------------------------ 41
Q('How do you deploy Airflow and ship DAG changes (CI/CD)?', 'Deployment & CI/CD', minutes=7, cards=[
    definition(
        defbox('Airflow itself is deployed as containers (official image) with the <strong>Helm chart</strong> on Kubernetes or '
               '<strong>docker-compose</strong> for small setups, or bought as a managed service (AWS MWAA, Google Cloud Composer, '
               'Astronomer). DAG code is shipped separately through CI/CD: tests in CI, then sync to the DAG location.'),
        tags('Docker', 'Helm Chart', 'MWAA', 'Cloud Composer', 'Astronomer', 'git-sync', 'DAG Bundles', 'CI/CD'),
    ),
    table(['How DAGs reach Airflow', 'Notes'], [
        ['Baked into the image', 'Immutable and reproducible; every DAG change needs an image build and rollout'],
        ['git-sync sidecar', 'Containers pull the DAG repo every few seconds'],
        ['Shared volume / object storage sync', 'CI copies files to S3/GCS (MWAA, Composer)'],
        ['DAG bundles (Airflow 3)', 'Airflow reads DAGs from a versioned source such as a Git repo, and each run records the bundle version it used'],
    ]),
    explanation(
        code('''
# .github/workflows/dags.yml (sketch)
on: { push: { branches: [main] } }
jobs:
  test-and-deploy:
    steps:
      - run: pip install "apache-airflow==3.3.2" -r requirements.txt --constraint constraints.txt
      - run: ruff check dags/ --select AIR          # Airflow-specific lint rules
      - run: pytest tests/                          # DAG integrity + unit tests
      - run: aws s3 sync dags/ s3://mwaa-bucket/dags/ --delete
''', 'CI Pipeline', 'fa-file-code'),
        title='Example'),
    crossq(
        ('Why pin providers and use the constraints file?', 'Airflow has hundreds of dependencies. The official constraints file pins a tested set so installs are reproducible and do not break when a library releases a new version.'),
    ),
]),

# ------------------------------------------------------------------ 42
Q('How does Airflow compare with cron, Prefect, Dagster and cloud orchestrators?', 'Airflow vs Alternatives', minutes=6, cards=[
    definition(
        defbox('All of these schedule and orchestrate work, but they differ in model (task-centric vs asset-centric), hosting and '
               'ecosystem. Airflow\'s strengths are maturity, a huge provider ecosystem and a large community; its weak spots have been '
               'local development and data passing, which Airflow 2 and 3 have improved.'),
        tags('Prefect', 'Dagster', 'Azure Data Factory', 'AWS Step Functions', 'Argo Workflows', 'Oozie'),
    ),
    table(['Tool', 'Model', 'Typical choice when'], [
        ['cron', 'Time-based commands', 'A couple of independent scripts on one server'],
        ['Apache Airflow', 'Python DAGs of tasks; Assets for data-aware scheduling', 'Many pipelines, many systems, need for history, retries, backfills'],
        ['Prefect', 'Python flows, dynamic, hybrid cloud execution', 'Python-first teams wanting very dynamic workflows'],
        ['Dagster', 'Software-defined assets, strong typing and testing', 'Teams modelling pipelines as data assets with lineage'],
        ['Azure Data Factory / AWS Step Functions / Glue Workflows', 'Managed, low-code / JSON state machines', 'All-in on one cloud, little custom code'],
        ['Argo Workflows', 'Kubernetes-native YAML workflows', 'Container-first platform teams'],
        ['Apache Oozie', 'XML workflows for Hadoop', 'Legacy Hadoop clusters (being retired)'],
    ]),
    interview(p('Avoid "X is better". Explain the trade-off and tie it to the team: existing skills, cloud, number of pipelines, '
                'need for backfills and observability.')),
]),

])
