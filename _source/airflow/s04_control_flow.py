from build import *
from airflow.anims import *
from airflow.runner import dagtest, afcli, afpy

SECTION = dict(level='intermediate', title='Task Communication & Control Flow', questions=[

# ------------------------------------------------------------------ 19
Q('What are XComs? How do tasks share data?', 'XComs', minutes=8, cards=[
    definition(
        defbox('<strong>XCom</strong> ("cross-communication") lets tasks exchange <strong>small</strong> pieces of data. A value is '
               'stored with a key, the task id and the DAG run; other tasks in the same run pull it. A task\'s return value is pushed '
               'automatically under the key <code>return_value</code>.'),
        tags('XCom', 'xcom_push', 'xcom_pull', 'return_value', 'Custom XCom Backend', 'Object Storage'),
    ),
    xcom_anim(),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task
from airflow.providers.standard.operators.python import PythonOperator

def count_rows(ti):
    ti.xcom_push(key="row_count", value=1240)           # explicit push with a custom key
    return "s3://lake/orders/dt=2026-10-10/part-0.parquet"  # pushed as return_value

def validate(ti):
    path = ti.xcom_pull(task_ids="count_rows")          # return_value by default
    rows = ti.xcom_pull(task_ids="count_rows", key="row_count")
    print(f"validating {rows} rows in {path}")
    return rows > 0

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def xcom_demo():
    c = PythonOperator(task_id="count_rows", python_callable=count_rows)
    v = PythonOperator(task_id="validate", python_callable=validate)

    @task
    def notify(ok, path):                               # TaskFlow: arguments are pulled for you
        print(f"Vineeta, load check passed={ok} for {path}")

    c >> v
    notify(v.output, c.output)

xcom_demo()
''', 'xcom_demo', '2026-10-10'),
        title='Example: Classic Push/Pull and TaskFlow'),
    warn('XComs are stored in the metadata database (in Airflow 3 written through the API server). Pushing DataFrames or files '
         'bloats the database and slows the scheduler. Write the data to storage and pass its <strong>path</strong>; or configure '
         'an object-storage XCom backend that stores large values in S3/GCS automatically.', 'Do Not Pass Big Data'),
    crossq(
        ('Can a task pull an XCom from another DAG?', 'Yes, with <code>xcom_pull(dag_id=…, task_ids=…, run_id=…)</code>, but it couples DAGs tightly. Prefer assets or shared storage.'),
        ('What must an XCom value be?', 'Something Airflow can serialize: JSON types plus types it knows (datetimes, dataclasses, Assets …). XCom pickling was removed in Airflow 3.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('How does branching work in Airflow?', 'Branching', minutes=7, cards=[
    definition(
        defbox('A <strong>branch</strong> task decides at run time which downstream path to follow. With <code>@task.branch</code> '
               '(or <code>BranchPythonOperator</code>) the function returns one task_id or a list of them; all other directly '
               'downstream tasks are <strong>skipped</strong>.'),
        tags('@task.branch', 'BranchPythonOperator', 'Skipped', 'trigger_rule', 'BranchDayOfWeekOperator'),
    ),
    branch_anim(),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task
from airflow.providers.standard.operators.empty import EmptyOperator

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def branch_demo():

    @task.branch
    def check_day(**context):
        day = context["logical_date"].strftime("%A")
        print(f"logical date is a {day}")
        return "weekend_load" if day in ("Saturday", "Sunday") else "weekday_load"

    weekday = EmptyOperator(task_id="weekday_load")
    weekend = EmptyOperator(task_id="weekend_load")
    join_default = EmptyOperator(task_id="join_all_success")
    join_ok = EmptyOperator(task_id="join_fixed", trigger_rule="none_failed_min_one_success")

    check_day() >> [weekday, weekend]
    [weekday, weekend] >> join_default
    [weekday, weekend] >> join_ok

branch_demo()
''', 'branch_demo', '2026-10-10'),
        title='Example: 10 Oct 2026 Is a Saturday'),
    explanation(
        p('Other branching helpers: <code>BranchDayOfWeekOperator</code>, <code>BranchDateTimeOperator</code>, '
          '<code>BranchSQLOperator</code> (branch on a query result), and <code>@task.short_circuit</code> when the choice is '
          'simply "continue or stop".'),
        title='Related Operators'),
    crossq(
        ('Can a branch return several task_ids?', 'Yes, return a list. All listed tasks run; the remaining direct downstream tasks are skipped.'),
        ('Why was my join task skipped?', 'Default trigger rule all_success treats a skipped upstream as "not success", so the skip propagates. Use none_failed_min_one_success.'),
    ),
]),

# ------------------------------------------------------------------ 21
Q('What are trigger rules? Explain all_success, all_done, one_failed, none_failed and others', 'Trigger Rules', minutes=8, cards=[
    definition(
        defbox('A task\'s <strong>trigger_rule</strong> decides, from the states of its upstream tasks, whether it should run. The '
               'default is <code>all_success</code>. Other rules allow tasks to run after failures (cleanup, alerting) or tolerate '
               'skipped branches.'),
        tags('trigger_rule', 'all_success', 'all_done', 'one_failed', 'none_failed', 'none_failed_min_one_success', 'upstream_failed'),
    ),
    trigger_rules_anim(),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task
from airflow.sdk.exceptions import AirflowSkipException
from airflow.providers.standard.operators.empty import EmptyOperator

RULES = ["all_success", "all_failed", "all_done", "one_success", "one_failed",
         "none_failed", "none_skipped", "none_failed_min_one_success", "always"]

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def trigger_rules_demo():
    @task
    def extract_a(): print("ok")

    @task
    def extract_b(): raise ValueError("source down")

    @task
    def extract_c(): raise AirflowSkipException("no file today")

    ups = [extract_a(), extract_b(), extract_c()]
    for rule in RULES:
        ups >> EmptyOperator(task_id=f"t_{rule}", trigger_rule=rule)

trigger_rules_demo()
''', 'trigger_rules_demo', '2026-10-10'),
        title='Example: Every Rule Against the Same Three Upstreams'),
    table(['Use case', 'Rule'], [
        ['Normal step', 'all_success'],
        ['Cleanup / close resources whatever happened', 'all_done'],
        ['Send an alert as soon as anything fails', 'one_failed'],
        ['Join after a branch', 'none_failed_min_one_success'],
        ['Run if no upstream failed (skips are fine)', 'none_failed'],
    ]),
    crossq(
        ('What is the difference between failed and upstream_failed?', '<strong>failed</strong>: the task itself ran and raised an error. <strong>upstream_failed</strong>: it never ran because its trigger rule could not be met due to failed upstream tasks.'),
        ('Setup and teardown tasks?', 'Airflow 2.7+ lets you mark tasks with <code>.as_setup()</code> / <code>.as_teardown()</code>: teardown runs even if work fails (like all_done) but does not make the DAG run succeed by itself, avoiding the leaf-state trap.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What are TaskGroups? Why were SubDAGs removed?', 'TaskGroups', minutes=6, cards=[
    definition(
        defbox('A <strong>TaskGroup</strong> visually groups related tasks in the UI and prefixes their ids '
               '(<code>group_id.task_id</code>). It is only an organisational layer: tasks still belong to the same DAG and are '
               'scheduled normally. Use <code>@task_group</code> or <code>with TaskGroup(...)</code>.'),
        tags('TaskGroup', '@task_group', 'SubDAG', 'group_id', 'UI Grouping'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task, task_group

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def taskgroup_demo():

    @task_group
    def process(source: str):
        @task
        def extract(src):
            print(f"extract {src}")
            return src

        @task
        def clean(src):
            return f"{src}_clean"

        return clean(extract(source))

    @task
    def publish(tables):
        print("publishing", tables)

    publish([process.override(group_id="orders")("orders"),
             process.override(group_id="customers")("customers")])

taskgroup_demo()
''', 'taskgroup_demo', '2026-10-10'),
        title='Example: One Group Definition Used Twice'),
    comparison(
        table(['Aspect', 'SubDAG (removed in Airflow 3)', 'TaskGroup'], [
            ['What it is', 'A separate DAG run inside a SubDagOperator', 'Just a namespace for tasks'],
            ['Scheduling', 'Own scheduler/executor settings, often deadlocked slots', 'Normal, same DAG run'],
            ['Performance', 'Poor', 'No overhead'],
        ]),
    ),
    crossq(
        ('Can dependencies be set on a whole group?', 'Yes: <code>start &gt;&gt; my_group &gt;&gt; end</code> connects start to all root tasks of the group and all leaf tasks to end.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('What is dynamic task mapping? How do expand() and partial() work?', 'Dynamic Task Mapping', minutes=9, cards=[
    definition(
        defbox('<strong>Dynamic task mapping</strong> (Airflow 2.3+) creates a variable number of task instances <strong>at run time</strong>, '
               'one per element of an input list, similar to <code>map</code> in Python. <code>.expand()</code> takes the mapped '
               'arguments; <code>.partial()</code> fixes the arguments that stay the same.'),
        tags('expand', 'partial', 'map_index', 'Mapped Tasks', 'Reduce', 'expand_kwargs', 'max_active_tis_per_dag'),
    ),
    mapping_anim(),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task
from airflow.providers.standard.operators.bash import BashOperator

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def mapping_demo():

    @task
    def list_files():                        # decided at run time (e.g. from S3)
        return ["anuj.csv", "vineeta.csv", "aarshvi.csv"]

    @task
    def process(path: str, min_score: int):
        scores = {"anuj.csv": 82, "vineeta.csv": 91, "aarshvi.csv": 77}
        s = scores[path]
        return {"file": path, "passed": s >= min_score}

    @task
    def summarize(results):                  # receives all mapped results
        passed = [r["file"] for r in results if r["passed"]]
        print(f"{len(passed)} of {len(results)} passed: {passed}")

    results = process.partial(min_score=80).expand(path=list_files())
    summarize(results)

    # Classic operators map too: one bash task per city
    BashOperator.partial(task_id="ping_city").expand(
        bash_command=["echo Mumbai", "echo Pune", "echo Delhi"])

mapping_demo()
''', 'mapping_demo', '2026-10-10'),
        title='Example'),
    explanation(
        ul('Each mapped instance has a <code>map_index</code> (0, 1, 2 …), its own logs, retries and state.',
           'Mapping over two lists with <code>expand(a=[…], b=[…])</code> creates the cross product; <code>expand_kwargs</code> maps over a list of argument dicts.',
           'Limit parallelism with <code>max_active_tis_per_dag</code>; very large lists are capped by <code>[core] max_map_length</code> (1024 by default).',
           'An empty list means zero instances, and the mapped task is marked skipped.'),
        title='Details'),
    crossq(
        ('Dynamic mapping vs a for-loop that creates tasks?', 'A loop runs at parse time, so the number of tasks must be known when the file is parsed (e.g. from a config file). Mapping decides at run time from upstream output.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('Explain ShortCircuit, LatestOnly, depends_on_past and wait_for_downstream', 'ShortCircuit & depends_on_past', minutes=7, cards=[
    definition(
        defbox('<strong>@task.short_circuit</strong> stops the rest of the DAG run (downstream tasks are skipped) when its function '
               'returns a falsy value. <strong>LatestOnlyOperator</strong> skips downstream tasks in all but the most recent scheduled '
               'run (useful during catchup). <strong>depends_on_past=True</strong> makes a task wait until the same task succeeded in '
               'the <em>previous</em> DAG run; <strong>wait_for_downstream</strong> also waits for that task\'s direct downstream tasks.'),
        tags('ShortCircuitOperator', '@task.short_circuit', 'LatestOnlyOperator', 'depends_on_past', 'wait_for_downstream'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def short_circuit_demo():

    @task.short_circuit
    def new_data_arrived():
        new_rows = 0                     # e.g. SELECT COUNT(*) of today's rows
        print(f"new rows: {new_rows}")
        return new_rows > 0              # False → skip everything downstream

    @task
    def transform(): print("transforming")

    @task
    def load(): print("loading")

    new_data_arrived() >> transform() >> load()

short_circuit_demo()
''', 'short_circuit_demo', '2026-10-10'),
        title='Example: Nothing New Today'),
    table(['Feature', 'Use it when'], [
        ['short_circuit', 'A run should stop cleanly (skipped, not failed) when there is nothing to do'],
        ['LatestOnlyOperator', 'Side effects such as emails or cache refreshes should happen only for the latest run, not for every backfilled date'],
        ['depends_on_past', 'Runs must be strictly in order, e.g. each day builds on the previous day\'s table (SCD, running balances)'],
        ['wait_for_downstream', 'Even stricter: the previous run\'s next steps must also be done before today starts'],
    ]),
    warn('With <code>depends_on_past=True</code> one failed day blocks every later day until it is fixed or marked success, so use it only when the order truly matters.'),
]),

# ------------------------------------------------------------------ 25
Q('How do you pass parameters when triggering a DAG? Explain params and TriggerDagRunOperator', 'Params & Triggering DAGs', minutes=7, cards=[
    definition(
        defbox('<strong>params</strong> declare a DAG\'s inputs with defaults (and optional validation via <code>Param</code>). When '
               'a run is triggered manually or through the API, a <strong>conf</strong> JSON can override them. '
               '<strong>TriggerDagRunOperator</strong> lets one DAG start another, optionally passing conf.'),
        tags('params', 'Param', 'dag_run.conf', 'TriggerDagRunOperator', 'REST API', 'Trigger with config'),
    ),
    example(
        dagtest('''
import pendulum
from airflow.sdk import dag, task, Param

@dag(schedule=None, start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     params={
         "student": Param("Anuj", type="string", enum=["Anuj", "Vineeta", "Aarshvi"]),
         "semester": Param(1, type="integer", minimum=1, maximum=4),
     })
def report_card():
    @task
    def generate(**context):
        p = context["params"]
        print(f"report card for {p['student']}, semester {p['semester']}")

    generate()

report_card()
''', 'report_card', '2026-10-10', conf={'student': 'Aarshvi', 'semester': 2}),
        title='Example: airflow dags test report_card -c \'{"student": "Aarshvi", "semester": 2}\''),
    explanation(
        code('''
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

trigger = TriggerDagRunOperator(
    task_id="start_report_card",
    trigger_dag_id="report_card",
    conf={"student": "Vineeta", "semester": 3},
    wait_for_completion=True,        # wait (deferrable=True frees the worker slot)
    poke_interval=60,
)
''', 'Triggering Another DAG', 'fa-brands fa-python'),
        code('''
curl -X POST "https://airflow.example.com/api/v2/dags/report_card/dagRuns" \\
     -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \\
     -d '{"logical_date": null, "conf": {"student": "Anuj", "semester": 1}}'
''', 'Triggering Through the REST API (Airflow 3)', 'fa-terminal'),
        title='Other Ways to Trigger'),
    crossq(
        ('What happens if conf has an invalid value, e.g. semester 7?', 'The run is rejected because the Param schema (minimum 1, maximum 4) validates it, and the UI trigger form shows the error.'),
        ('Params vs Variables?', 'Params are per-run inputs. Variables are global key-value settings shared by all DAGs (next section).'),
    ),
]),

])
