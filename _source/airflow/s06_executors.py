from build import *
from airflow.anims import *
from airflow.runner import dagtest, afcli, afpy

SECTION = dict(level='advanced', title='Executors, States & Scaling', questions=[

# ------------------------------------------------------------------ 32
Q('What are executors? Compare LocalExecutor, CeleryExecutor and KubernetesExecutor', 'Executors', minutes=9, cards=[
    definition(
        defbox('The <strong>executor</strong> is the part of the scheduler that takes queued task instances and gets them '
               'executed somewhere. It is set with <code>[core] executor</code>; Airflow 3 can run <strong>several executors</strong> '
               'side by side and let each task choose one with <code>executor="…"</code>.'),
        tags('Executor', 'LocalExecutor', 'CeleryExecutor', 'KubernetesExecutor', 'Multiple Executors', 'EdgeExecutor'),
    ),
    executors_anim(),
    comparison(
        table(['Aspect', 'LocalExecutor', 'CeleryExecutor', 'KubernetesExecutor'], [
            ['Where tasks run', 'Processes on the scheduler host', 'Long-running Celery workers', 'One new pod per task'],
            ['Extra infrastructure', 'None', 'Broker (Redis/RabbitMQ) + workers', 'Kubernetes cluster'],
            ['Scaling', 'One machine', 'Add workers (autoscale with KEDA)', 'Cluster autoscaling, scale to zero'],
            ['Task start-up', 'Fast', 'Fast (workers are warm)', 'Slower (pod creation, image pull)'],
            ['Isolation / dependencies', 'Shared environment', 'Shared per worker; queues for special workers', 'Per-task image, CPU and memory'],
            ['Good for', 'Dev, small deployments', 'Many short tasks, steady load', 'Spiky load, heavy or varied tasks'],
        ]),
    ),
    example(
        afcli(['airflow config get-value core executor', 'airflow config get-value core parallelism']),
        title='Example: Checking the Configured Executor'),
    explanation(
        code('''
# airflow.cfg (Airflow 3): several executors, the first is the default
[core]
executor = CeleryExecutor,KubernetesExecutor
''', 'Config', 'fa-file-code')
        + code('''
@task(executor="KubernetesExecutor")      # this heavy task gets its own pod
def train_model(): ...
''', 'Per-task Choice', 'fa-brands fa-python'),
        title='Multiple Executors (Airflow 2.10+)'),
    crossq(
        ('What happened to SequentialExecutor?', 'It ran one task at a time and was the SQLite default. Airflow 3 removed it; LocalExecutor works with SQLite for local development.'),
        ('What are Celery queues used for?', 'Routing: tasks with <code>queue="gpu"</code> go only to workers started with <code>airflow celery worker -q gpu</code>, e.g. machines with GPUs or special network access.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What is the difference between KubernetesPodOperator and KubernetesExecutor?', 'KubernetesPodOperator vs KubernetesExecutor', minutes=7, cards=[
    definition(
        defbox('<strong>KubernetesExecutor</strong> is an <em>executor</em>: it runs <strong>every</strong> Airflow task (your Python code) '
               'inside a pod built from the Airflow image. <strong>KubernetesPodOperator</strong> is an <em>operator</em>: one task that '
               'launches <strong>any container image you choose</strong> (a Spark job, an R script, a dbt project) and waits for it. '
               'It works with any executor.'),
        tags('KubernetesPodOperator', 'KubernetesExecutor', 'Pod', 'Container Image', 'Dependency Isolation'),
    ),
    comparison(
        table(['Aspect', 'KubernetesExecutor', 'KubernetesPodOperator'], [
            ['What it is', 'How all tasks are run', 'A single task type'],
            ['Image', 'Airflow image (+ your DAG code)', 'Any image, any language'],
            ['Code runs', 'Your operator/@task code', 'The container\'s entrypoint/command'],
            ['Works with', 'Is the executor', 'Local, Celery or Kubernetes executor'],
            ['Typical use', 'Resource isolation for all tasks', 'Dependency isolation: conflicting libraries, other languages'],
        ]),
    ),
    explanation(
        code('''
from kubernetes.client import models as k8s
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

score_students = KubernetesPodOperator(
    task_id="score_students",
    name="score-students",
    namespace="data-jobs",
    image="registry.example.com/ml/scoring:1.4.2",
    cmds=["python", "score.py"],
    arguments=["--date", "{{ ds }}", "--batch", "pgcp-bda"],
    container_resources=k8s.V1ResourceRequirements(requests={"cpu": "2", "memory": "4Gi"}),
    get_logs=True,
    on_finish_action="delete_pod",
    deferrable=True,
)
''', 'KubernetesPodOperator', 'fa-brands fa-python'),
        title='Example'),
    interview(p('A popular pattern is "Airflow as a pure orchestrator": every heavy step is a container run through '
                'KubernetesPodOperator, so Airflow workers need no data libraries and teams ship their own images.')),
]),

# ------------------------------------------------------------------ 34
Q('Explain the task instance lifecycle and its states', 'Task Instance States', minutes=7, cards=[
    definition(
        defbox('A task instance moves through states as the scheduler, executor and worker act on it: '
               '<code>none → scheduled → queued → running → success / failed</code>, with side paths for retries, sensors, '
               'deferral, skipping and upstream failure.'),
        tags('scheduled', 'queued', 'running', 'up_for_retry', 'up_for_reschedule', 'deferred', 'skipped', 'upstream_failed'),
    ),
    states_anim(),
    example(
        afpy('''
from airflow.utils.state import TaskInstanceState, DagRunState

print("Task instance states:", ", ".join(s.value for s in TaskInstanceState))
print("DAG run states:     ", ", ".join(s.value for s in DagRunState))
'''),
        title='Example: All States Defined in Airflow 3.3'),
    table(['Stuck in…', 'Usually means'], [
        ['scheduled', 'No free slot: parallelism, pool, max_active_tasks, or the executor is not picking tasks up'],
        ['queued', 'Executor accepted it but no worker started it: workers down, wrong Celery queue, pod cannot be scheduled'],
        ['running (for hours)', 'Long or hung job: add execution_timeout; check the external system'],
        ['deferred', 'No triggerer running, or the trigger is waiting for a condition that never happens'],
    ]),
    crossq(
        ('What does "zombie task" mean?', 'A task the DB says is running but whose process died (e.g. the worker was killed). The scheduler detects missing heartbeats and fails it (and retries if allowed).'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How do you scale Airflow and make it highly available?', 'Scaling & High Availability', minutes=8, cards=[
    definition(
        defbox('Scale each component separately: more <strong>workers</strong> (or Kubernetes capacity) for task throughput, more '
               '<strong>DAG processors</strong> for many DAG files, <strong>multiple schedulers</strong> (active-active) for scheduling '
               'throughput and availability, and a production-grade <strong>metadata database</strong> (PostgreSQL/MySQL) with connection pooling.'),
        tags('HA Scheduler', 'parallelism', 'Workers', 'PgBouncer', 'DAG Processor', 'Helm Chart'),
    ),
    example(
        afcli(['airflow config get-value core parallelism',
               'airflow config get-value core max_active_tasks_per_dag',
               'airflow config get-value core max_active_runs_per_dag',
               'airflow config get-value dag_processor min_file_process_interval',
               'airflow config get-value dag_processor refresh_interval',
               'airflow config get-value core dagbag_import_timeout']),
        title='Example: Default Limits in Airflow 3.3'),
    table(['Bottleneck', 'Symptom', 'Fix'], [
        ['Workers', 'Many tasks in "queued"', 'More workers / pods; raise worker concurrency'],
        ['Limits', 'Tasks "scheduled" while workers are idle', 'Raise parallelism, pool slots, max_active_tasks'],
        ['Scheduler', 'Slow to create runs/queue tasks', 'Run 2+ schedulers; tune scheduler loop settings'],
        ['DAG parsing', 'Changes appear late, parse timeouts', 'Lighter top-level code; more DAG processors; fewer, bigger files'],
        ['Metadata DB', 'Connection errors, slow UI', 'PgBouncer, bigger instance, clean old rows (<code>airflow db clean</code>)'],
    ]),
    explanation(
        ul('Every service runs as several replicas except the database. Schedulers coordinate through row-level locks in the DB, so no leader election is needed.',
           'Deploy with the official Helm chart (Kubernetes) or docker-compose for small setups; managed options are AWS MWAA, Google Cloud Composer and Astronomer.',
           'Keep the database lean: XComs and task history grow fast. Schedule <code>airflow db clean --clean-before-timestamp …</code>.'),
        title='Production Notes'),
]),

])
