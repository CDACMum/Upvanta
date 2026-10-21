from build import *
from dbt.anims import *
from dbt.runner import dfile, dbtrun, yml, sqlc, sh
from dbt.common import STG_STUDENTS, STG_MARKS, STG_COURSES, STAGING

SECTION = dict(level='advanced', title='Best Practices & Performance', questions=[

# ------------------------------------------------------------------ 31
Q('How do you improve the performance of a dbt project?', 'Performance Tuning', minutes=9, cards=[
    definition(
        table(['Lever', 'What to do'], [
            ['Measure', 'Find slow models in run_results.json / dbt Cloud model timing'],
            ['Materialization', 'Heavy views read often → table; very large facts → incremental (with a sensible lookback)'],
            ['SQL', 'Filter and select columns early; avoid SELECT * in marts; avoid repeated heavy CTEs; pre-aggregate'],
            ['DAG shape', 'Split giant models; remove unnecessary dependencies so more models run in parallel'],
            ['Parallelism', '<code>threads</code> in profiles.yml / <code>--threads</code>; right-sized warehouse'],
            ['Warehouse features', 'Clustering/partitioning configs (Snowflake <code>cluster_by</code>, BigQuery <code>partition_by</code>), incremental <code>insert_overwrite</code>'],
            ['Run less', 'Slim CI, state-based deploys, separate hourly vs nightly selections'],
        ]),
        tags('Performance', 'threads', 'Incremental', 'Materialization', 'run_results', 'Clustering'),
    ),
    analogy('Making the kitchen faster: find the slowest dish first (measure), prepare sauces in advance instead of on every order (tables), only cook new '
            'orders (incremental), use more cooks in parallel (threads), and buy bigger stoves only when needed (warehouse size).'),
    perf_anim(),
    real_world(
        scenario('Nightly run from 2 hours to 25 minutes',
                 ul('Top 5 slowest models accounted for 70% of runtime (from run_results.json).',
                    'Three of them were views on views read by 20 marts → made them tables.',
                    'The 300 M-row attendance fact became incremental with a 3-day lookback.',
                    'Threads raised from 4 to 12; a chain of dependencies split so marts build in parallel.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        dfile('models/marts/fct_a.sql', "{{ config(materialized='table') }} select * from {{ ref('stg_marks') }}", show=False),
        dfile('models/marts/fct_b.sql', "{{ config(materialized='table') }} select * from {{ ref('stg_students') }}", show=False),
        dfile('models/marts/fct_c.sql', "{{ config(materialized='table') }} select * from {{ ref('stg_courses') }}", show=False),
        dbtrun('!dbt seed', 'dbt run --threads 4',
               """python3 -c "import json; r=json.load(open('target/run_results.json'))['results']; [print(f\\"{x['unique_id'].split('.')[-1]:<14}{x['execution_time']:.3f}s\\") for x in sorted(r, key=lambda x: -x['execution_time'])[:3]]" """),
        note('With 4 threads, independent models start in parallel (the "START" lines interleave). The last command lists the slowest models from '
             'run_results.json; timings are from this page\'s build.', 'Read the output'),
        title='Example: Parallel Run and Finding Slow Models'),
    steps(
        ('Profile', 'Rank models by execution time; check warehouse query profiles for the top ones.'),
        ('Fix materializations', 'Tables for heavy shared models, incremental for large facts.'),
        ('Optimise SQL', 'Early filters, fewer columns, avoid cross joins and repeated window functions.'),
        ('Increase parallelism', 'threads + DAG restructuring.'),
        ('Use platform features', 'Partitioning/clustering configs per adapter.'),
        title='Steps'),
    crossq(
        ('More threads always faster?', 'No. Parallelism is limited by DAG dependencies and warehouse capacity; too many concurrent queries can queue or slow each other.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('What naming conventions and style guidelines do you follow in dbt?', 'Conventions & Style', minutes=7, cards=[
    definition(
        table(['Item', 'Convention'], [
            ['Staging', '<code>stg_&lt;source&gt;__&lt;table&gt;</code> (double underscore), one per source table'],
            ['Intermediate', '<code>int_&lt;entity&gt;_&lt;verb&gt;</code>, e.g. int_marks_pivoted'],
            ['Marts', '<code>fct_&lt;process&gt;</code>, <code>dim_&lt;entity&gt;</code>; folder per business area'],
            ['Columns', 'snake_case; <code>&lt;entity&gt;_id</code> keys, <code>_at</code> timestamps, <code>_date</code> dates, <code>is_/has_</code> booleans'],
            ['SQL style', 'CTEs at the top (import CTEs → logic → final select), lowercase keywords, trailing commas, no SELECT * in marts'],
            ['YAML', 'One properties file per folder (_staging.yml) or per model; every model has a description and PK tests'],
            ['Tooling', 'SQLFluff (lint), pre-commit, dbt-project-evaluator (checks best practices)'],
        ]),
        tags('Naming Conventions', 'Style Guide', 'stg_', 'fct_', 'dim_', 'SQLFluff', 'CTEs'),
    ),
    analogy('Conventions are like a <strong>library classification system</strong>: once you know the system, you can find any book in any branch '
            'without asking the librarian.'),
    naming_anim(),
    real_world(
        scenario('Reviewing a pull request',
                 p('A reviewer immediately questions <code>marks_final_v2_new.sql</code>: the conventions say it should be <code>fct_exam_marks</code> in '
                   '<code>marts/academics/</code>, with a description and unique/not_null tests on its key.')),
    ),
    example(
        dfile('models/staging/exam_db/stg_exam_db__marks.sql', """
with source as (

    select * from {{ ref('raw_marks') }}

),

renamed as (

    select
        roll_no                 as student_id,
        lower(subject)          as subject_code,
        cast(marks as integer)  as marks,
        cast(exam_date as date) as exam_date,
        marks >= 60             as is_passed
    from source

)

select * from renamed
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt --quiet show --select stg_exam_db__marks --limit 3'),
        title='Example: A Staging Model in the Recommended Style'),
    steps(
        ('Write the conventions down', 'A short CONTRIBUTING.md; adopt dbt Labs\' style guide as a base.'),
        ('Automate checks', 'SQLFluff with the dbt templater in pre-commit and CI.'),
        ('Check project structure', 'dbt-project-evaluator flags missing tests/docs, direct source joins in marts, etc.'),
        ('Enforce in code review', 'Names, tests, descriptions are part of the definition of done.'),
        title='Steps'),
    crossq(
        ('Why import CTEs at the top?', 'They list all dependencies of the model in one place (like imports in code), making the model easier to read and refactor.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What are model contracts, constraints and versions?', 'Contracts & Versions', minutes=8, cards=[
    definition(
        defbox('A <strong>model contract</strong> (dbt 1.5+) declares the exact columns and data types a model must return '
               '(<code>contract: {enforced: true}</code>). dbt checks the SELECT against it before building and fails on any mismatch. '
               '<strong>Constraints</strong> (not_null, primary_key, unique, foreign_key, check) are added to the DDL where the platform enforces them. '
               '<strong>Model versions</strong> (<code>versions:</code>) let you publish v2 of a model while consumers migrate from v1, and '
               '<strong>access</strong> (private/protected/public) controls who may ref it. Together they support multi-team "dbt Mesh" projects.'),
        tags('Contract', 'Constraints', 'Model Versions', 'access', 'dbt Mesh', 'Breaking Changes'),
    ),
    analogy('A contract is an <strong>API specification</strong> for a table: the consuming team builds on "student_id is an integer, never null". If '
            'someone tries to change that, the build is stopped before the promise is broken.'),
    contract_anim(),
    real_world(
        scenario('Protecting a shared dimension',
                 p('<code>dim_students</code> is used by the placement, finance and academics teams. With an enforced contract, a refactor that '
                   'accidentally changed <code>student_id</code> to text failed in CI instead of breaking three teams\' dashboards.')),
    ),
    example(
        dfile('models/staging/stg_students.sql', STG_STUDENTS, show=False),
        dfile('models/marts/dim_students.sql', """
select
    cast(student_id as varchar) as student_id,   -- someone changed the type
    student_name,
    course_code
from {{ ref('stg_students') }}
"""),
        dfile('models/marts/_marts.yml', """
models:
  - name: dim_students
    config:
      materialized: table
      contract: {enforced: true}
    columns:
      - name: student_id
        data_type: integer
        constraints: [{type: not_null}]
      - name: student_name
        data_type: varchar
      - name: course_code
        data_type: varchar
"""),
        dbtrun('!dbt seed', '!dbt run --select stg_students', 'dbt run --select dim_students', allow_fail=True),
        title='Example: The Contract Stops a Breaking Change'),
    steps(
        ('Identify shared, consumer-facing models', 'Marts used by other teams or tools.'),
        ('Enable the contract', '<code>contract: {enforced: true}</code> with every column\'s name and data_type.'),
        ('Add constraints', 'not_null/primary_key where supported (others still need data tests).'),
        ('Version breaking changes', 'Add v2, keep v1 with a deprecation_date, migrate consumers.'),
        ('Set access', 'public for cross-team models, private for internal helpers.'),
        title='Steps to Add a Contract'),
    crossq(
        ('Contract vs data tests?', 'A contract checks the shape (columns and types) before building; data tests check the values after building. Use both.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How do you design a data-quality strategy with dbt?', 'Data Quality Strategy', minutes=8, cards=[
    definition(
        defbox('Quality checks are layered through the DAG so problems are caught as early as possible: <strong>source freshness and key tests</strong> '
               'on raw data, <strong>PK and accepted-values tests</strong> in staging, <strong>relationship and business-rule tests</strong> on marts, '
               '<strong>unit tests</strong> for complex logic in CI, <strong>contracts</strong> on shared models, and <strong>alerting</strong> on failures '
               'and warnings. <code>dbt build</code> enforces the gates in production.'),
        tags('Data Quality', 'Testing Strategy', 'Freshness', 'Contracts', 'Unit Tests', 'Alerting'),
    ),
    analogy('Like hospital hygiene: hands are washed at the entrance (sources), before each procedure (staging), and after (marts), with audits '
            '(unit tests) and alarms (alerts). One check at the very end would be too late.'),
    quality_anim(),
    real_world(
        scenario('Test coverage targets',
                 ul('100% of models: primary key unique + not_null.',
                    'All foreign keys in marts: relationships tests.',
                    'All sources: freshness thresholds.',
                    'Critical calculations (grades, attendance %, fee totals): unit tests.',
                    'Weekly review of warnings; owners assigned via <code>meta: {owner: …}</code>.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        dfile('models/staging/_quality.yml', """
models:
  - name: stg_students
    columns:
      - name: student_id
        data_tests: [unique, not_null]
      - name: course_code
        data_tests:
          - relationships:
              arguments: {to: ref('stg_courses'), field: course_code}
  - name: stg_marks
    columns:
      - name: student_id
        data_tests:
          - not_null
          - relationships:
              arguments: {to: ref('stg_students'), field: student_id}
      - name: marks
        data_tests:
          - not_null
          - accepted_values:
              name: marks_are_valid_percent
              arguments: {values: [58, 61, 72, 75, 82, 84, 88, 91]}
              config: {severity: warn}
"""),
        dbtrun('!dbt seed', 'dbt build --exclude resource_type:seed'),
        title='Example: Tests Gating Every Layer'),
    steps(
        ('Agree minimum standards', 'PK tests everywhere, FK tests in marts, freshness on sources.'),
        ('Add tests as you build models', 'Part of the definition of done.'),
        ('Run dbt build in production', 'So failures stop propagation.'),
        ('Alert and assign owners', 'Notify on failures; review warnings.'),
        ('Measure coverage', 'dbt-project-evaluator or a script over manifest.json.'),
        title='Steps'),
    crossq(
        ('How many tests are "enough"?', 'Enough that the failures you care about would be caught: keys and relationships everywhere, business rules where errors are costly. Tests with no clear purpose only slow runs and create noise.'),
    ),
]),
])
