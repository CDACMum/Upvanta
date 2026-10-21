from build import *
from dbt.anims import *
from dbt.runner import dfile, dbtrun, yml, sqlc, sh
from dbt.common import STG_STUDENTS, STG_MARKS, STG_COURSES, STAGING

MARTS = {
    'models/marts/dim_students.sql': "select s.student_id, s.student_name, c.course_name from {{ ref('stg_students') }} s join {{ ref('stg_courses') }} c using (course_code)",
    'models/marts/fct_marks.sql': "select m.* from {{ ref('stg_marks') }} m join {{ ref('dim_students') }} d using (student_id)",
    'models/reports/rpt_toppers.sql': "{{ config(tags=['daily']) }}\nselect * from {{ ref('fct_marks') }} where marks >= 85",
}

SECTION = dict(level='advanced', title='Running, Selecting & Deploying', questions=[

# ------------------------------------------------------------------ 26
Q('How does node selection work in dbt (--select, +, tags, state)?', 'Node Selection Syntax', minutes=8, cards=[
    definition(
        table(['Selector', 'Selects'], [
            ['<code>--select fct_marks</code>', 'One model by name'],
            ['<code>+fct_marks</code> / <code>fct_marks+</code>', 'With all ancestors / all descendants (<code>2+model</code> limits depth)'],
            ['<code>@fct_marks</code>', 'Descendants and all their ancestors (safe rebuild of everything affected)'],
            ['<code>tag:daily</code>, <code>path:models/marts</code>', 'By tag or folder'],
            ['<code>config.materialized:incremental</code>', 'By any config value'],
            ['<code>test_type:unit</code>, <code>resource_type:snapshot</code>', 'By node type'],
            ['<code>state:modified+</code>', 'Changed since a saved manifest, plus children (needs <code>--state</code>)'],
            ['<code>--exclude</code>', 'Remove nodes from the selection; space = union, comma = intersection'],
        ]),
        tags('--select', '--exclude', 'Graph Operators', 'tag:', 'state:modified', 'Selectors'),
    ),
    analogy('Selecting nodes is like choosing <strong>which trains to run</strong> on a route map: one train, a train with all the trains it waits for '
            '(+model), or a train with all trains that depend on it (model+).'),
    selection_anim(),
    real_world(
        scenario('Different jobs, one project',
                 ul('Hourly job: <code>dbt build --select tag:hourly</code>.',
                    'Nightly job: <code>dbt build --exclude tag:hourly</code>.',
                    'After fixing a staging model: <code>dbt build --select stg_marks+</code> to rebuild and test everything downstream.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        *[dfile(k, v, show=False) for k, v in MARTS.items()],
        dbtrun('dbt --quiet ls --select fct_marks', 'dbt --quiet ls --select +fct_marks --resource-type model', 'dbt --quiet ls --select fct_marks+',
               'dbt --quiet ls --select 1+fct_marks', 'dbt --quiet ls --select tag:daily', 'dbt --quiet ls --select path:models/staging --exclude stg_courses',
               'dbt --quiet ls --select "stg_marks+,path:models/marts"'),
        title='Example'),
    steps(
        ('Start from what changed or what is needed', 'A model, a folder, a tag.'),
        ('Add graph operators', '+ for parents, + after for children, @ for both safely.'),
        ('Preview with dbt ls', 'Always check the selection before running it.'),
        ('Save common selections', 'In <code>selectors.yml</code> and use <code>--selector name</code>.'),
        title='Steps'),
    crossq(
        ('Difference between "a b" and "a,b" in --select?', 'Space is a union (a or b); comma is an intersection (nodes matching both a and b).'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What is the difference between dbt run, dbt test and dbt build?', 'dbt run vs test vs build', minutes=7, cards=[
    definition(
        table(['Command', 'Does'], [
            ['<code>dbt run</code>', 'Builds models only'],
            ['<code>dbt test</code>', 'Runs data and unit tests only'],
            ['<code>dbt seed</code> / <code>dbt snapshot</code>', 'Loads seeds / runs snapshots'],
            ['<code>dbt build</code>', 'All of the above in DAG order: each resource is tested right after it is built; failures skip downstream nodes'],
            ['<code>dbt retry</code>', 'Re-runs only the nodes that failed (or were skipped) in the previous command'],
        ]),
        tags('dbt build', 'dbt run', 'dbt test', 'dbt retry', 'Skip on Failure'),
    ),
    analogy('<code>dbt run</code> is cooking all dishes, <code>dbt test</code> is tasting them afterwards. <code>dbt build</code> tastes each dish '
            '<strong>before</strong> it is used in the next one, so a bad sauce never ends up in ten other dishes.'),
    build_anim(),
    real_world(
        scenario('Stopping bad data at the source',
                 p('Duplicate roll numbers appeared in staging. Because the production job runs <code>dbt build</code>, the unique test on '
                   '<code>stg_students</code> failed and all marts depending on it were skipped; dashboards kept showing yesterday\'s correct data '
                   'instead of double-counted students.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        *[dfile(k, v, show=False) for k, v in MARTS.items()],
        dfile('models/staging/_staging.yml', """
models:
  - name: stg_marks
    columns:
      - name: marks
        data_tests:
          - accepted_values:
              arguments: {values: [61, 72, 75, 82, 84, 88, 91]}   # 58 is missing → fails
"""),
        dbtrun('!dbt seed', 'dbt build --exclude resource_type:seed', allow_fail=True),
        note('The test on <code>stg_marks</code> failed, so <code>fct_marks</code> and <code>rpt_toppers</code> were SKIPPED, while the independent '
             'branch (stg_students, stg_courses, dim_students) still built.', 'Read the output'),
        title='Example: A Failing Test Stops Downstream Models'),
    steps(
        ('Use dbt build in production jobs', 'Tests gate downstream models.'),
        ('Use run / test separately while developing', 'Faster feedback on one model.'),
        ('After a failure', 'Fix, then <code>dbt retry</code> or <code>dbt build --select failed_model+</code>.'),
        title='Steps'),
    crossq(
        ('Can a warning stop downstream models?', 'No. Only tests with severity error (failing their error_if condition) cause downstream skips.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What is in the target folder? What are manifest.json and run_results.json?', 'Artifacts (target/)', minutes=7, cards=[
    definition(
        table(['Artifact', 'Contents', 'Used by'], [
            ['<code>target/compiled/</code>', 'Each model/test SELECT after Jinja rendering', 'Debugging'],
            ['<code>target/run/</code>', 'Exact statements executed (CREATE/MERGE wrappers)', 'Debugging'],
            ['<code>manifest.json</code>', 'Every node, config, dependency, description', 'docs, slim CI (state), orchestrators, catalogues'],
            ['<code>run_results.json</code>', 'Status, timing, rows affected, messages per node', 'Monitoring, dbt retry, alerting'],
            ['<code>catalog.json</code>', 'Warehouse metadata (columns, types, stats)', 'dbt docs'],
            ['<code>sources.json</code>', 'Results of source freshness', 'Freshness dashboards'],
        ]),
        tags('target', 'manifest.json', 'run_results.json', 'catalog.json', 'Compiled SQL'),
    ),
    analogy('The target folder is the <strong>flight recorder</strong> of every dbt command: what was planned (manifest), what exactly was executed '
            '(compiled/run SQL), and how each step went (run_results).'),
    artifacts_anim(),
    real_world(
        scenario('Monitoring model run times',
                 p('After each production run, a small Python task reads <code>run_results.json</code> and pushes model timings to Grafana. A model '
                   'whose time doubled over a week was found and converted to incremental before it became a problem.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        *[dfile(k, v, show=False) for k, v in MARTS.items()],
        dbtrun('!dbt seed', '!dbt run', 'ls target target/compiled/cdac_dw/models/marts',
               """python3 -c "import json; r=json.load(open('target/run_results.json')); [print(f\\"{x['unique_id']:<32} {x['status']:<8} {x['execution_time']:.2f}s\\") for x in r['results']]" """,
               """python3 -c "import json; m=json.load(open('target/manifest.json')); print(m['nodes']['model.cdac_dw.fct_marks']['depends_on']['nodes'])" """),
        note('Execution times vary between runs; the values above are from the build of this page.', 'Note'),
        title='Example'),
    steps(
        ('Debug a model', 'Open target/compiled/…/model.sql and run it in a SQL client.'),
        ('Monitor runs', 'Parse run_results.json after each job.'),
        ('Enable slim CI', 'Save the production manifest.json and pass it with <code>--state</code>.'),
        ('Do not commit target/', 'It is regenerated by every command.'),
        title='Steps'),
    crossq(
        ('Why does dbt retry need run_results.json?', 'It reads the previous command\'s results to know which nodes failed or were skipped and re-runs only those.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('How do you set up CI/CD for dbt? What is slim CI?', 'CI/CD & Slim CI', minutes=9, cards=[
    definition(
        defbox('<strong>CI</strong>: on every pull request, build and test the changed models in an isolated schema before merging. <strong>Slim CI</strong> '
               'builds only what changed: compare the PR\'s project with the production <code>manifest.json</code> using '
               '<code>--select state:modified+ --state path/to/prod-artifacts</code>, and add <code>--defer</code> so unchanged upstream models are '
               'read from production instead of rebuilt. <strong>CD</strong>: after merge, the production job deploys the new code (scheduled '
               '<code>dbt build --target prod</code>).'),
        tags('CI/CD', 'Slim CI', 'state:modified', '--defer', '--state', 'GitHub Actions', 'Pull Request'),
    ),
    analogy('Slim CI is like a teacher re-checking <strong>only the answers a student changed</strong> after review, plus anything that depends on them, '
            'rather than re-marking the whole paper.'),
    ci_anim(),
    real_world(
        scenario('400-model project',
                 p('A full CI build took 35 minutes; with slim CI a typical pull request touching two models builds and tests about 10 nodes in 3 minutes, '
                   'reading the other 390 from production via defer.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        *[dfile(k, v, show=False) for k, v in MARTS.items()],
        dbtrun('!dbt seed', '!dbt run',
               'mkdir -p prod-artifacts && cp target/manifest.json prod-artifacts/',
               "sed -i 's/where marks >= 85/where marks >= 80/' models/reports/rpt_toppers.sql",
               "sed -i 's/trim(name)/upper(trim(name))/' models/staging/stg_students.sql",
               'dbt --quiet ls --select state:modified --state prod-artifacts',
               'dbt --quiet ls --select state:modified+ --state prod-artifacts'),
        yml('''
# .github/workflows/dbt_ci.yml (abridged)
on: pull_request
jobs:
  slim-ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install dbt-core dbt-snowflake
      - run: aws s3 cp s3://cdac-dbt-artifacts/prod/manifest.json prod-artifacts/   # saved by the prod job
      - run: dbt deps
      - run: dbt build --select state:modified+ --defer --state prod-artifacts --target ci
        env:
          DBT_CI_SCHEMA: pr_${{ github.event.number }}
''', 'GitHub Actions workflow'),
        title='Example: Detecting What Changed'),
    steps(
        ('Store production artifacts', 'Upload manifest.json after each prod run (S3, GCS, dbt Cloud does it automatically).'),
        ('Create a CI target', 'Schema per pull request, limited permissions.'),
        ('Run slim CI on every PR', '<code>dbt build --select state:modified+ --defer --state …</code>.'),
        ('Add linting', 'SQLFluff for style; dbt-checkpoint/pre-commit for docs and tests coverage.'),
        ('Deploy on merge', 'The scheduled prod job uses the main branch.'),
        title='Steps to Set Up CI/CD'),
    crossq(
        ('What does --defer do?', 'For any ref() to a model not selected in this run, dbt points to the production relation from the state manifest instead of the (non-existent) CI relation.'),
        ('How do you clean up PR schemas?', 'A run-operation macro that drops schemas matching pr_* after merge or nightly.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('How do you schedule and orchestrate dbt in production (Airflow, dbt Cloud)?', 'Orchestration', minutes=8, cards=[
    definition(
        defbox('dbt does not schedule itself. Options: <strong>dbt Cloud jobs</strong> (cron, API or event triggers); <strong>Airflow</strong> with a '
               '<code>BashOperator</code> running <code>dbt build</code>, or <strong>Astronomer Cosmos</strong>, which renders each dbt model/test '
               'as an Airflow task; <strong>Dagster</strong> (dbt assets); or simple cron/GitHub Actions. The orchestrator handles cross-system '
               'dependencies (load first, then dbt, then BI refresh), retries and alerting.'),
        tags('Airflow', 'Cosmos', 'dbt Cloud Jobs', 'Dagster', 'Scheduling', 'Orchestration'),
    ),
    analogy('dbt is the <strong>chef</strong>; the orchestrator is the <strong>restaurant manager</strong> who makes sure groceries arrive before the chef '
            'starts and the waiters are told when food is ready.'),
    airflow_anim(),
    real_world(
        scenario('Nightly academic pipeline',
                 p('Airflow DAG at 01:00: load exam and attendance data → <code>dbt source freshness</code> → <code>dbt build --target prod</code> → '
                   'refresh Power BI dataset → email summary. On a dbt failure, Airflow alerts the data team on Teams and the dashboards keep the '
                   'last good data.')),
    ),
    example(
        code('''
from datetime import datetime
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

DBT = "cd /opt/dbt/cdac_dw && dbt"

with DAG("cdac_nightly", schedule="0 1 * * *", start_date=datetime(2026, 10, 1), catchup=False) as dag:
    freshness = BashOperator(task_id="source_freshness", bash_command=f"{DBT} source freshness --target prod")
    build     = BashOperator(task_id="dbt_build",        bash_command=f"{DBT} build --target prod")
    docs      = BashOperator(task_id="dbt_docs",         bash_command=f"{DBT} docs generate --target prod")
    freshness >> build >> docs
''', 'Airflow DAG (BashOperator)', 'fa-brands fa-python'),
        code('''
from cosmos import DbtDag, ProjectConfig, ProfileConfig

cdac_dbt = DbtDag(
    dag_id="cdac_dbt_cosmos",
    project_config=ProjectConfig("/opt/dbt/cdac_dw"),
    profile_config=ProfileConfig(profile_name="cdac", target_name="prod",
                                 profiles_yml_filepath="/opt/dbt/profiles.yml"),
    schedule="0 1 * * *", start_date=datetime(2026, 10, 1), catchup=False,
)   # one Airflow task per model, with its tests
''', 'Astronomer Cosmos', 'fa-brands fa-python'),
        title='Example'),
    steps(
        ('Package dbt with its dependencies', 'Docker image or a virtualenv on the workers.'),
        ('Provide credentials via environment', 'Airflow connections/secrets → env vars used by profiles.yml.'),
        ('Order tasks', 'Extract/load → freshness → build → downstream refresh.'),
        ('Handle failures', 'Retries for transient errors, alerts, <code>dbt retry</code> for failed nodes.'),
        ('Keep artifacts', 'Upload target/ artifacts for docs, slim CI and monitoring.'),
        title='Steps to Orchestrate dbt'),
    crossq(
        ('One task for all of dbt, or one task per model?', 'One task is simple and lets dbt handle parallelism; per-model tasks (Cosmos) give per-model retries and visibility but add scheduler overhead on very large projects.'),
    ),
]),
])
