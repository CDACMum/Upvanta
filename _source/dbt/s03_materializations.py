from build import *
from dbt.anims import *
from dbt.runner import dfile, dbtrun, yml, sqlc, sh
from dbt.common import STG_STUDENTS, STG_MARKS, STG_COURSES, STAGING

OBJECTS = """dbt --quiet show --inline "select table_schema, table_name, table_type from information_schema.tables where table_schema not like '%raw' order by 1, 2" --limit 20"""

SECTION = dict(level='intermediate', title='Materializations, Snapshots & Config', questions=[

# ------------------------------------------------------------------ 11
Q('What are materializations in dbt? Compare view, table, incremental and ephemeral.', 'Materializations', minutes=9, cards=[
    definition(
        defbox('A <strong>materialization</strong> is the strategy dbt uses to persist a model in the warehouse. The SELECT is the same; only the '
               'generated DDL/DML differs.'),
        table(['Materialization', 'What dbt creates', 'Pros', 'Cons', 'Use for'], [
            ['view (default)', '<code>CREATE VIEW</code>', 'No storage, always current, fast to build', 'Query runs on every read', 'Staging, light models'],
            ['table', '<code>CREATE TABLE AS</code> (full rebuild)', 'Fast reads', 'Rebuild time grows with data', 'Marts read by BI'],
            ['incremental', 'Table; later runs insert/merge new rows', 'Fast runs on huge data', 'More logic, needs care with late data', 'Large facts/events'],
            ['ephemeral', 'Nothing: inlined as a CTE', 'No clutter in the warehouse', 'Cannot be queried directly; hard to debug', 'Small helper steps'],
            ['materialized_view', 'Warehouse-managed MV (some adapters)', 'Auto refresh by the warehouse', 'Platform limits', 'Near-real-time aggregates'],
        ]),
        tags('Materialization', 'view', 'table', 'incremental', 'ephemeral', 'materialized_view'),
    ),
    analogy('Four ways to serve tea: a <strong>view</strong> is brewing a fresh cup every time someone asks; a <strong>table</strong> is a full flask '
            'prepared each morning; <strong>incremental</strong> is topping up the flask with only what was drunk; <strong>ephemeral</strong> is '
            'tea concentrate used inside other drinks, never served on its own.'),
    materializations_anim(),
    real_world(
        scenario('Choosing per layer',
                 ul('stg_ models: views (cheap, always reflect raw data).',
                    'int_ helper logic: ephemeral or views.',
                    'dim_students, small facts: tables (BI reads them all day).',
                    'fct_attendance_events (200 million rows): incremental (a full rebuild took 40 minutes; incremental takes 2).')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        dfile('models/intermediate/int_scores.sql', """
{{ config(materialized='ephemeral') }}
select student_id, round(avg(marks), 1) as avg_marks from {{ ref('stg_marks') }} group by 1
"""),
        dfile('models/marts/dim_students.sql', """
{{ config(materialized='table') }}
select s.student_id, s.student_name, sc.avg_marks
from {{ ref('stg_students') }} s left join {{ ref('int_scores') }} sc using (student_id)
"""),
        dbtrun('!dbt seed', 'dbt run', OBJECTS, 'dbt --quiet compile --select dim_students'),
        note('<code>int_scores</code> exists in no schema: being ephemeral, it was inlined as the CTE <code>__dbt__cte__int_scores</code> in the compiled '
             'SQL of <code>dim_students</code>.', 'Read the output'),
        title='Example'),
    steps(
        ('Start with views', 'The default; cheap and simple.'),
        ('Promote to table', 'When a model is read often or is slow as a view.'),
        ('Promote to incremental', 'When a table rebuild becomes too slow or expensive.'),
        ('Set it in config', '<code>{{ config(materialized=\'table\') }}</code> or per folder in dbt_project.yml.'),
        title='Steps to Choose a Materialization'),
    crossq(
        ('A view-based mart is slow in Power BI. What do you change?', 'Materialize it (and possibly heavy upstream models) as a table so BI reads stored results instead of re-running the whole chain of views.'),
        ('When is ephemeral a bad idea?', 'When the logic is reused by many models (it is inlined, so computed repeatedly) or when you need to query it for debugging.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How do incremental models work? Explain is_incremental(), unique_key and incremental strategies.', 'Incremental Models', minutes=11, cards=[
    definition(
        defbox('An <strong>incremental</strong> model builds the full table on the first run, and on later runs processes only new/changed rows. Inside '
               'the model, <code>{% if is_incremental() %}</code> adds a filter (usually against <code>{{ this }}</code>, the existing table). With '
               '<code>unique_key</code>, dbt merges (updates existing keys, inserts new); without it, rows are appended.',
               '<strong>Strategies</strong> (adapter-dependent): <code>append</code>, <code>merge</code>, <code>delete+insert</code>, '
               '<code>insert_overwrite</code> (replace partitions), <code>microbatch</code> (dbt 1.9+, time-batched). '
               '<code>on_schema_change</code> controls what happens when columns change; <code>--full-refresh</code> rebuilds from scratch.'),
        tags('Incremental', 'is_incremental', 'unique_key', 'merge', 'append', 'microbatch', 'full-refresh', 'this'),
    ),
    analogy('Updating the attendance register: on day one you copy the whole class list (full build); every following day you only '
            '<strong>add today\'s entries</strong> (is_incremental filter), and if a correction comes for an existing entry you overwrite that line '
            '(unique_key merge) instead of writing a duplicate.'),
    incremental_anim(),
    real_world(
        scenario('Face-attendance events',
                 p('The attendance fact gets ~2 million events a day. As a table it took 40 minutes nightly; as an incremental model with '
                   '<code>event_time &gt; max(event_time) - 3 days</code> and <code>unique_key=\'event_id\'</code>, it takes 2 minutes and still picks up '
                   'late events from devices that were offline.')),
    ),
    example(
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/fct_marks.sql', """
{{ config(
    materialized='incremental',
    unique_key=['student_id', 'subject']
) }}

select student_id, subject, marks, exam_date, current_timestamp as loaded_at
from {{ ref('stg_marks') }}

{% if is_incremental() %}
  -- only rows newer than what the table already has
  where exam_date >= (select max(exam_date) from {{ this }})
{% endif %}
"""),
        dbtrun('!dbt seed', 'dbt run --select +fct_marks',
               "dbt --quiet show --inline \"select count(*) as rows_in_fct from {{ ref('fct_marks') }}\"",
               "printf '2403,SQL,79,2026-10-12\\n2401,Spark,66,2026-10-12\\n' >> seeds/raw_marks.csv",
               'dbt --quiet seed --select raw_marks',
               'dbt run --select fct_marks',
               "dbt --quiet show --inline \"select student_id, subject, marks, exam_date from {{ ref('fct_marks') }} order by exam_date desc, student_id\" --limit 4",
               "dbt --quiet compile --select fct_marks"),
        note('The second run printed <code>incremental model</code> and only rows with <code>exam_date &gt;= 2026-10-11</code> were processed. '
             'Anuj\'s Spark row (2401, Spark) already existed, so the merge on <code>unique_key</code> <strong>updated</strong> it to 66 instead of '
             'adding a duplicate; Aarshvi\'s SQL row was inserted.', 'Read the output'),
        title='Example: Full Load, New Data, Incremental Merge'),
    steps(
        ('Pick a reliable filter column', 'An event time or updated_at that only increases.'),
        ('Add the is_incremental() block', 'Filter against <code>{{ this }}</code>; add a look-back for late data.'),
        ('Set unique_key if rows can change or repeat', 'Single column or list of columns.'),
        ('Choose the strategy', 'merge (default on most), delete+insert, insert_overwrite for partitions, microbatch for time series.'),
        ('Plan schema changes', '<code>on_schema_change: append_new_columns</code> or full refresh.'),
        ('Full-refresh when logic changes', '<code>dbt run --select model --full-refresh</code>.'),
        title='Steps to Build an Incremental Model'),
    crossq(
        ('What is {{ this }}?', 'The relation of the model being built (its existing table). Used in the incremental filter to compare with already loaded data.'),
        ('Why can incremental models drift from a full rebuild?', 'Late or corrected source rows outside the filter window, deletes in the source (not propagated), or logic changes applied only to new rows. Periodic full refreshes or look-back windows reduce drift.'),
        ('What happens on the very first run?', 'is_incremental() is false (the table does not exist), so the whole SELECT runs and creates the table.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What are snapshots? How do you implement SCD Type 2 with dbt?', 'Snapshots (SCD Type 2)', minutes=10, cards=[
    definition(
        defbox('A <strong>snapshot</strong> records how rows in a mutable source table change over time (Slowly Changing Dimension Type 2). Each run '
               'compares the current source rows with the snapshot table; changed rows get their old version closed (<code>dbt_valid_to</code> set) '
               'and a new version inserted. Meta columns: <code>dbt_scd_id</code>, <code>dbt_updated_at</code>, <code>dbt_valid_from</code>, '
               '<code>dbt_valid_to</code> (null = current).',
               '<strong>Strategies</strong>: <code>timestamp</code> (uses an updated_at column, preferred) or <code>check</code> (compares listed columns). '
               'Run with <code>dbt snapshot</code>. Since dbt 1.9 snapshots can be defined in YAML.'),
        tags('Snapshot', 'SCD Type 2', 'dbt_valid_from', 'dbt_valid_to', 'timestamp strategy', 'check strategy'),
    ),
    analogy('A snapshot is a <strong>diary</strong> next to a whiteboard. The whiteboard (source table) is erased and rewritten; every evening you '
            'copy any changed line into the diary with the date it became true and the date it stopped being true.'),
    snapshot_anim(),
    real_world(
        scenario('Student city history for placement analysis',
                 p('The admission system overwrites a student\'s address when they move. A daily snapshot keeps every version, so the placement '
                   'report can show where a student lived when they were placed, and relocation patterns can be analysed.')),
    ),
    example(
        dfile('snapshots/students_snapshot.yml', """
snapshots:
  - name: students_snapshot
    relation: ref('raw_students')
    config:
      schema: snapshots
      unique_key: roll_no
      strategy: check
      check_cols: ['city', 'course']
"""),
        dbtrun('!dbt seed', 'dbt snapshot',
               "sed -i 's/2402,Vineeta,PG-DBDA,Kharghar,Navi Mumbai/2402,Vineeta,PG-DBDA,Kharghar,Pune/' seeds/raw_students.csv",
               'dbt --quiet seed --select raw_students',
               'dbt snapshot',
               "dbt --quiet show --inline \"select roll_no, city, dbt_valid_from is not null as has_from, dbt_valid_to is null as is_current from {{ ref('students_snapshot') }} where roll_no = 2402 order by dbt_valid_from\""),
        note('After Vineeta\'s city changed in the source, the second snapshot run closed the Navi Mumbai row and added a Pune row: two versions, '
             'one current. (Exact <code>dbt_valid_from/to</code> timestamps are replaced by booleans here because they show the build time.)', 'Read the output'),
        title='Example: Capturing a Change'),
    steps(
        ('Pick the source and key', 'A table that is updated in place; its unique key.'),
        ('Choose the strategy', 'timestamp with a trustworthy updated_at; otherwise check with the tracked columns.'),
        ('Define the snapshot', 'In snapshots/*.yml (1.9+) or a <code>{% snapshot %}</code> block.'),
        ('Run it on a schedule', '<code>dbt snapshot</code> (or <code>dbt build</code>) at least as often as the source changes.'),
        ('Build the dimension from it', 'Filter <code>dbt_valid_to is null</code> for current rows; join facts on dates for history.'),
        title='Steps to Create a Snapshot'),
    crossq(
        ('Why snapshot raw data rather than transformed models?', 'History must be captured from the source as it is; transformations can then be rebuilt any time from the snapshot. You cannot recreate history that was never captured.'),
        ('What does hard_deletes / invalidate_hard_deletes do?', 'Rows that disappear from the source get their current version closed (or, in 1.9+, a deleted record added), instead of staying "current" forever.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('Where can you configure dbt models, and which configuration wins?', 'Configuration Hierarchy', minutes=7, cards=[
    definition(
        defbox('Configs (materialized, schema, tags, unique_key, hooks…) can be set in three places. From least to most specific: '
               '<strong>dbt_project.yml</strong> (project and folder level, with <code>+</code> prefix) → <strong>properties YAML</strong> '
               '(<code>config:</code> under a model) → <strong><code>{{ config() }}</code> in the model file</strong>. The most specific wins; '
               'dictionary-like configs such as tags and meta are merged.'),
        tags('config', 'dbt_project.yml', 'Properties', 'Precedence', 'tags', 'meta'),
    ),
    analogy('School rules, class rules and a teacher\'s instruction for one assignment: the <strong>most specific instruction applies</strong> for that '
            'assignment, while general school rules cover everything else.'),
    config_anim(),
    real_world(
        scenario('Keeping config manageable',
                 p('Teams set 90% of configuration per folder in dbt_project.yml (staging=view, marts=table, schema per area) and use in-file '
                   'config only for exceptions such as an incremental model\'s unique_key.')),
    ),
    example(
        dfile('dbt_project.yml', """
name: cdac_dw
version: '1.0'
profile: cdac
seeds:
  cdac_dw:
    +schema: raw
models:
  cdac_dw:
    +materialized: view
    marts:
      +materialized: table
      +tags: ['nightly']
"""),
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/_marts.yml', """
models:
  - name: fct_marks
    config:
      tags: ['academics']
"""),
        dfile('models/marts/fct_marks.sql', """
{{ config(materialized='incremental', unique_key=['student_id', 'subject']) }}
select * from {{ ref('stg_marks') }}
"""),
        dfile('models/marts/subject_summary.sql', "select subject, avg(marks) as avg_marks from {{ ref('stg_marks') }} group by 1", show=False),
        dbtrun('!dbt seed', 'dbt run',
               'dbt --quiet ls --select tag:academics', 'dbt --quiet ls --select tag:nightly',
               'dbt --quiet ls --select config.materialized:incremental'),
        note('<code>fct_marks</code> is incremental (file config beat the folder\'s table) and has both tags (folder <em>nightly</em> + YAML '
             '<em>academics</em> merged). <code>subject_summary</code>, with no own config, is a nightly table.', 'Read the output'),
        title='Example'),
    steps(
        ('Set defaults per folder', 'In dbt_project.yml with <code>+config</code> keys.'),
        ('Use YAML for model metadata', 'Descriptions, tests, tags, meta.'),
        ('Use in-file config for model-specific SQL behaviour', 'unique_key, incremental strategy, partitioning.'),
        ('Check the result', '<code>dbt ls --select config.materialized:...</code> or the manifest.'),
        title='Steps'),
    crossq(
        ('Is it bad to configure everything in the .sql file?', 'Not wrong, but repetitive; folder-level defaults keep conventions consistent and make the exceptions visible.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do custom schemas and aliases work? What is generate_schema_name?', 'Custom Schemas & Aliases', minutes=8, cards=[
    definition(
        defbox('<code>+schema: marts</code> requests a custom schema. By default dbt\'s <code>generate_schema_name</code> macro returns '
               '<strong>&lt;target schema&gt;_&lt;custom schema&gt;</strong> (e.g. <code>dbt_vineeta_marts</code>, <code>analytics_marts</code>) so '
               'developers and prod never collide. Teams often override this macro, e.g. use the plain custom schema in prod. '
               '<code>alias</code> changes the object name independently of the file name.'),
        tags('Custom Schema', 'generate_schema_name', 'alias', 'Target Schema', 'Environments'),
    ),
    analogy('Your locker number at school is "<strong>class + roll</strong>" (dev_marts) so two classes never share a locker; the school can decide '
            'that the trophy cabinet (prod) is simply called "Trophies" (marts).'),
    schema_anim(),
    real_world(
        scenario('Clean prod schemas',
                 p('BI users wanted <code>marts.dim_students</code>, not <code>analytics_marts.dim_students</code>. A five-line override of '
                   '<code>generate_schema_name</code> uses the custom schema as-is when <code>target.name == \'prod\'</code> and keeps the prefix in dev.')),
    ),
    example(
        dfile('dbt_project.yml', """
name: cdac_dw
version: '1.0'
profile: cdac
seeds:
  cdac_dw:
    +schema: raw
models:
  cdac_dw:
    marts:
      +schema: marts
"""),
        dfile('macros/generate_schema_name.sql', """
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
"""),
        dfile('models/marts/dim_students.sql', """
{{ config(alias='student_dim') }}
select roll_no as student_id, name from {{ ref('raw_students') }}
"""),
        dbtrun('!dbt seed', '!dbt seed --target prod', 'dbt --quiet run', 'dbt --quiet run --target prod',
               """dbt --quiet show --inline "select table_schema, table_name from information_schema.tables where table_name = 'student_dim' order by 1" """),
        title='Example: Same Model, Different Schemas per Target'),
    steps(
        ('Decide the schema layout', 'e.g. staging, marts_academics, marts_placements.'),
        ('Set +schema per folder', 'In dbt_project.yml.'),
        ('Override generate_schema_name if needed', 'Put the macro in macros/; branch on target.name.'),
        ('Use alias for naming exceptions', 'Keep file names unique; alias for the physical name.'),
        title='Steps'),
    crossq(
        ('Why are my models in "dbt_vineeta_marts" instead of "marts"?', 'That is the default generate_schema_name behaviour: custom schemas are appended to the target schema. Override the macro to change it.'),
        ('Can two models have the same alias?', 'Only if they are in different schemas; otherwise they would overwrite each other and dbt raises an error.'),
    ),
]),
])
