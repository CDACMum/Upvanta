from build import *
from dbt.anims import *
from dbt.runner import dfile, dbtrun, yml, sqlc, sh
from dbt.common import STG_STUDENTS, STG_MARKS, STG_COURSES, STAGING

SECTION = dict(level='expert', title='Real-World Scenarios', questions=[

# ------------------------------------------------------------------ 35
Q('Scenario: Build a star schema for student results from raw data using dbt.', 'End-to-End Star Schema', minutes=12, cards=[
    definition(
        defbox('A typical interview task: given raw tables, design staging models, dimensions and a fact table at a clear <strong>grain</strong>, add '
               'tests on keys and relationships, and build everything with one command. The fact table holds measures (marks) and foreign keys to '
               'dimensions (student, course); dimensions hold descriptive attributes.'),
        tags('Star Schema', 'Fact Table', 'Dimension', 'Grain', 'dbt build', 'Data Modeling'),
    ),
    analogy('Like organising an exam result board: a central <strong>score sheet</strong> (fact) with one line per student per subject, and '
            '<strong>reference cards</strong> (dimensions) describing each student and course, linked by roll number and course code.'),
    star_anim(),
    real_world(
        scenario('Requirements',
                 ul('Reports: average marks by course and centre, pass rate by subject, topper list.',
                    'Grain of the fact: one row per student per subject per exam.',
                    'Every fact row must link to an existing student and course (relationships tests).')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
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
      +materialized: table
""", show=False),
        dfile('models/marts/dim_students.sql', """
select
    s.student_id,
    s.student_name,
    s.centre,
    s.city,
    s.course_code
from {{ ref('stg_students') }} s
"""),
        dfile('models/marts/dim_courses.sql', """
select course_code, course_name, duration_months, fee
from {{ ref('stg_courses') }}
"""),
        dfile('models/marts/fct_marks.sql', """
select
    m.student_id,
    s.course_code,
    m.subject,
    m.exam_date,
    m.marks,
    m.marks >= 60 as is_passed
from {{ ref('stg_marks') }} m
join {{ ref('dim_students') }} s using (student_id)
"""),
        dfile('models/marts/_marts.yml', """
models:
  - name: dim_students
    columns:
      - name: student_id
        data_tests: [unique, not_null]
  - name: dim_courses
    columns:
      - name: course_code
        data_tests: [unique, not_null]
  - name: fct_marks
    data_tests:
      - unique_combination:
          arguments: {cols: "student_id || subject || exam_date"}
    columns:
      - name: student_id
        data_tests:
          - relationships: {arguments: {to: ref('dim_students'), field: student_id}}
      - name: course_code
        data_tests:
          - relationships: {arguments: {to: ref('dim_courses'), field: course_code}}
""", show=True),
        dfile('macros/test_unique_combination.sql', """
{% test unique_combination(model, cols) %}
select {{ cols }} as k, count(*) from {{ model }} group by 1 having count(*) > 1
{% endtest %}
""", show=False),
        dbtrun('dbt build', """dbt --quiet show --inline "select c.course_name, s.centre, count(*) as results, round(avg(f.marks),1) as avg_marks, sum(case when f.is_passed then 1 else 0 end) as passed from {{ ref('fct_marks') }} f join {{ ref('dim_students') }} s using (student_id) join {{ ref('dim_courses') }} c on c.course_code = f.course_code group by 1, 2 order by 1, 2" """),
        title='Example: Build, Test and Query the Star Schema'),
    steps(
        ('State the grain of the fact', 'One row per student per subject per exam.'),
        ('Stage every source', 'Rename, cast, standardise.'),
        ('Build dimensions', 'One row per entity; unique + not_null on the key.'),
        ('Build the fact', 'Measures + foreign keys; test the grain and relationships.'),
        ('Run dbt build and verify with a report query', 'Compare totals with the source.'),
        ('Document', 'Descriptions for the fact\'s grain and every measure.'),
        title='Steps'),
    crossq(
        ('Why define the grain first?', 'Every other decision (joins, measures, tests, aggregation) depends on it; an unclear grain causes double counting.'),
        ('Surrogate keys or natural keys?', 'Natural keys are fine when stable and unique (roll number). Surrogate keys (dbt_utils.generate_surrogate_key) help with multi-column keys and SCD2 versions.'),
    ),
]),

# ------------------------------------------------------------------ 36
Q('Scenario: Report results by the city the student lived in at exam time (SCD2 with snapshots).', 'SCD2 Dimension & As-of Join', minutes=12, cards=[
    definition(
        defbox('Use a <strong>snapshot</strong> with the <strong>timestamp strategy</strong> on the source\'s <code>updated_at</code>, so '
               '<code>dbt_valid_from</code>/<code>dbt_valid_to</code> come from real change times. Build a history dimension from the snapshot '
               '(replacing the open <code>dbt_valid_to</code> with a far-future date) and join facts on the key <strong>and</strong> '
               '<code>event_date between valid_from and valid_to</code>.'),
        tags('SCD Type 2', 'Snapshot', 'timestamp strategy', 'As-of Join', 'History Dimension'),
    ),
    analogy('Like reading an old <strong>class photograph</strong>: to know who sat where on a given date, you use the seating chart that was valid '
            'on that date, not today\'s.'),
    scd_join_anim(),
    real_world(
        scenario('Why it matters',
                 p('Placement reports by city were changing month to month because students\' current city was used. Joining on the city valid at '
                   'exam time made historical reports stable and correct.')),
    ),
    example(
        dfile('seeds/student_addresses.csv', """
roll_no,city,updated_at
2401,Pune,2026-08-01 10:00:00
2402,Navi Mumbai,2026-08-01 10:00:00
"""),
        dfile('snapshots/addresses_snapshot.yml', """
snapshots:
  - name: addresses_snapshot
    relation: ref('student_addresses')
    config:
      unique_key: roll_no
      strategy: timestamp
      updated_at: updated_at
"""),
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/dim_student_history.sql', """
select
    roll_no                                     as student_id,
    city,
    cast(dbt_valid_from as date)                as valid_from,
    coalesce(cast(dbt_valid_to as date), date '9999-12-31') as valid_to
from {{ ref('addresses_snapshot') }}
"""),
        dfile('models/marts/fct_marks_by_city.sql', """
select m.student_id, m.subject, m.exam_date, h.city as city_at_exam
from {{ ref('stg_marks') }} m
join {{ ref('dim_student_history') }} h
  on m.student_id = h.student_id
 and m.exam_date >= h.valid_from and m.exam_date < h.valid_to
order by m.student_id, m.exam_date
"""),
        dbtrun('dbt --quiet seed', 'dbt --quiet snapshot',
               "printf '2402,Pune,2026-10-01 09:00:00\\n' > /tmp/upd.csv && sed -i '/^2402,/d' seeds/student_addresses.csv && cat /tmp/upd.csv >> seeds/student_addresses.csv",
               'dbt --quiet seed --select student_addresses', 'dbt --quiet snapshot', 'dbt --quiet run',
               'dbt --quiet show --select dim_student_history', 'dbt --quiet show --select fct_marks_by_city'),
        note('Vineeta (2402) moved to Pune on 1 October. Her SQL exam (20 Sept) is attributed to Navi Mumbai and her Spark exam (10 Oct) to Pune.', 'Read the output'),
        title='Example'),
    steps(
        ('Snapshot the source with the timestamp strategy', 'Using the system\'s updated_at.'),
        ('Run snapshots regularly', 'Before dbt run, at least as often as the source changes.'),
        ('Build a history dimension', 'Clean names; replace null valid_to with a far-future date.'),
        ('Join facts as-of the event date', 'Key + date range condition.'),
        ('Test', 'Exactly one current row per key; no overlapping ranges.'),
        title='Steps'),
    crossq(
        ('What if two changes happen between two snapshot runs?', 'Only the latest state at snapshot time is captured; intermediate versions are lost. Snapshot frequency must match how often history matters, or use CDC.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: Late-arriving records are missing from an incremental model. How do you fix it?', 'Late-Arriving Data', minutes=9, cards=[
    definition(
        defbox('An incremental filter like <code>event_date &gt; (select max(event_date) from {{ this }})</code> skips rows that arrive after newer rows '
               'were already loaded. Fixes: a <strong>look-back window</strong> (reprocess the last N days every run) with a <strong>unique_key</strong> '
               'so reprocessed rows merge instead of duplicating; filter on <strong>load time</strong> (<code>_loaded_at</code>) instead of event time; '
               'or the <strong>microbatch</strong> strategy with <code>lookback</code>. Periodic full refreshes reconcile any remaining drift.'),
        tags('Late-Arriving Data', 'Incremental', 'Lookback', 'unique_key', 'microbatch', 'Full Refresh'),
    ),
    analogy('Closing the attendance register each evening and refusing late slips means students who submitted late are marked absent forever. '
            'Keeping the last three days\' pages open for corrections (look-back) fixes it.'),
    late_data_anim(),
    real_world(
        scenario('Offline attendance devices',
                 p('Devices at a remote centre upload two days late after network outages. With a strict filter those students appeared absent; '
                   'switching to a 3-day lookback and <code>unique_key=\'event_id\'</code> fixed the reports without duplicates.')),
    ),
    example(
        dfile('dbt_project.yml', """
name: cdac_dw
version: '1.0'
profile: cdac
seeds:
  cdac_dw:
    +schema: raw
vars:
  lookback_days: 3
""", show=False),
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/fct_marks.sql', """
{{ config(materialized='incremental', unique_key=['student_id', 'subject', 'exam_date']) }}

select student_id, subject, exam_date, marks
from {{ ref('stg_marks') }}
{% if is_incremental() %}
where exam_date >= (
    select max(exam_date) - interval {{ var('lookback_days') }} day from {{ this }}
)
{% endif %}
"""),
        dbtrun('!dbt seed', 'dbt --quiet run',
               "printf '2405,Spark,70,2026-10-09\\n' >> seeds/raw_marks.csv",
               'dbt --quiet seed --select raw_marks', 'dbt --quiet run',
               "dbt --quiet show --inline \"select count(*) as rows, max(case when student_id = 2405 and subject = 'Spark' then marks end) as late_row_marks from {{ ref('fct_marks') }}\""),
        note('A Spark result for 2405 dated 9 Oct arrived after rows up to 11 Oct were loaded. A strict "&gt; max" filter would have skipped it; the '
             '3-day lookback picked it up, and re-processed rows merged on the key instead of duplicating (9 rows, not more).', 'Read the output'),
        title='Example'),
    steps(
        ('Measure lateness', 'How late can records arrive? Choose the lookback accordingly.'),
        ('Add the lookback and a unique_key', 'So reprocessing is idempotent.'),
        ('Consider load-time filtering', 'Filter on when rows arrived, not when events happened.'),
        ('Schedule full refreshes', 'e.g. weekly, to reconcile edge cases.'),
        ('Test', 'Compare counts per day between source and model.'),
        title='Steps'),
    crossq(
        ('Why not always full-refresh?', 'On very large tables it is slow and expensive; a lookback keeps runs cheap while still correcting recent data.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: The nightly dbt run failed. How do you debug and recover?', 'Debugging & dbt retry', minutes=9, cards=[
    definition(
        defbox('Read the run summary (failing node + database error) → open the <strong>compiled SQL</strong> in <code>target/compiled</code> and run it '
               'directly or with <code>dbt show</code> → fix the model or data → re-run only what is needed: <code>dbt retry</code> (re-executes the failed '
               'and skipped nodes of the last command) or <code>dbt build --select model+</code>. <code>dbt debug</code> checks connection problems; '
               '<code>logs/dbt.log</code> has full details.'),
        tags('Debugging', 'dbt retry', 'Compiled SQL', 'dbt debug', 'logs', 'Recovery'),
    ),
    analogy('Like a failed train journey: find which station had the problem (failing node), inspect the track (compiled SQL), repair it, and restart '
            'the journey from that station (retry), not from the first station.'),
    debug_anim(),
    real_world(
        scenario('A division by zero at 2 a.m.',
                 p('A new course with zero enrolled students made the pass-percentage model divide by zero. The on-call engineer read the error, '
                   'wrapped the division in <code>nullif(total, 0)</code>, ran <code>dbt retry</code> to finish the remaining models, and added a test '
                   'to catch courses with no students.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        dfile('models/marts/course_pass_rate.sql', """
select
    s.course_code,
    count(*) filter (where m.marks >= 60) * 100.0 / count(*) as pass_pct
from {{ ref('stg_marks') }} m
join {{ ref('stg_students') }} s using (student_id)
group by s.course_code
"""),
        dfile('models/marts/course_report.sql', """
select c.course_name, r.pass_pct
from {{ ref('course_pass_rate') }} r
join {{ ref('stg_courses') }} c using (course_code)
"""),
        dbtrun('!dbt seed',
               "sed -i 's/count(\\*) filter (where m.marks >= 60)/count(*) filter (where m.mark >= 60)/' models/marts/course_pass_rate.sql",
               'dbt run', allow_fail=True),
        dbtrun('!dbt seed',
               "!sed -i 's/count(\\*) filter (where m.marks >= 60)/count(*) filter (where m.mark >= 60)/' models/marts/course_pass_rate.sql",
               '!dbt run || true',
               "sed -i 's/m.mark >= 60/m.marks >= 60/' models/marts/course_pass_rate.sql",
               'dbt retry', 'dbt --quiet show --select course_report',
               extra={k: v for k, v in list(STAGING.items())} | {
                   'models/marts/course_pass_rate.sql': "select\n    s.course_code,\n    count(*) filter (where m.marks >= 60) * 100.0 / count(*) as pass_pct\nfrom {{ ref('stg_marks') }} m\njoin {{ ref('stg_students') }} s using (student_id)\ngroup by s.course_code\n",
                   'models/marts/course_report.sql': "select c.course_name, r.pass_pct\nfrom {{ ref('course_pass_rate') }} r\njoin {{ ref('stg_courses') }} c using (course_code)\n"},
               title='After fixing the typo'),
        title='Example: A Typo Breaks the Run, dbt retry Finishes It'),
    steps(
        ('Read the summary and the error', 'Which node? Compilation error (Jinja/YAML) or database error (SQL/data)?'),
        ('Inspect compiled SQL', '<code>target/compiled/…</code>; reproduce in a SQL client.'),
        ('Check recent changes', 'Git log for the model; source data changes; schema changes upstream.'),
        ('Fix and re-run', '<code>dbt retry</code> or <code>dbt build --select model+</code>.'),
        ('Prevent', 'Add a test or contract; add the case to unit tests.'),
        title='Steps to Recover'),
    crossq(
        ('Compilation error vs database error?', 'Compilation errors happen before anything runs (bad Jinja, missing ref, YAML mistakes); database errors come from the warehouse executing the compiled SQL (unknown column, type error, permissions).'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('dbt vs stored procedures vs Spark: when do you use which? Can dbt run Python?', 'dbt vs Stored Procedures vs Spark', minutes=9, cards=[
    comparison(
        table(['Aspect', 'Stored procedures', 'dbt', 'Spark'], [
            ['Style', 'Procedural SQL (loops, variables, DML)', 'Declarative SELECT models + Jinja', 'Python/Scala/SQL code on DataFrames'],
            ['Dependencies', 'Hand-coded call order', 'Automatic DAG from ref()', 'Code or orchestrator'],
            ['Testing & docs', 'Ad hoc', 'Built in (tests, unit tests, docs, lineage)', 'Unit tests in code; docs separate'],
            ['Version control & CI', 'Possible but uncommon', 'Native (files in Git, slim CI)', 'Native'],
            ['Compute', 'One database', 'The warehouse/lakehouse', 'Spark cluster'],
            ['Best for', 'Legacy OLTP logic', 'Analytics modelling in SQL', 'Large-scale processing, files, ML, streaming'],
        ]),
        defbox('dbt supports <strong>Python models</strong> on some adapters (Snowflake Snowpark, BigQuery/Databricks via Spark, DuckDB locally): a '
               '<code>model(dbt, session)</code> function that returns a DataFrame, still part of the DAG.'),
        tags('Stored Procedures', 'Spark', 'Python Models', 'Comparison', 'Architecture'),
    ),
    analogy('Stored procedures are a <strong>handwritten cookbook</strong> only one chef understands; dbt is a <strong>shared, tested recipe system</strong> '
            'for the restaurant; Spark is the <strong>industrial food factory</strong> for huge volumes and unusual ingredients.'),
    compare_anim(),
    real_world(
        scenario('Migration from stored procedures',
                 p('A legacy MIS ran 60 stored procedures in a fixed order from a SQL Agent job. Rewriting them as dbt models gave a lineage graph, '
                   'tests on every key, and parallel runs; heavy log parsing stayed in Spark, which writes Parquet tables that dbt then models.')),
    ),
    example(
        sqlc('''
-- Stored procedure style (procedural, order and DDL handled by hand)
CREATE PROCEDURE refresh_course_summary()
BEGIN
  TRUNCATE TABLE course_summary;
  INSERT INTO course_summary
  SELECT course, COUNT(*) FROM students GROUP BY course;
END;
''', 'Stored procedure (MySQL)'),
        dfile('models/marts/student_stats.py', """
import pandas as pd

def model(dbt, session):
    dbt.config(materialized="table")
    marks = dbt.ref("raw_marks").df()            # DuckDB relation -> pandas
    stats = (marks.groupby("roll_no")["marks"]
                  .agg(["count", "mean", "max"])
                  .reset_index()
                  .rename(columns={"count": "subjects", "mean": "avg_marks", "max": "best"}))
    stats["avg_marks"] = stats["avg_marks"].round(1)
    return stats
"""),
        dbtrun('!dbt seed', 'dbt run', 'dbt --quiet show --inline "select * from {{ ref(\'student_stats\') }} order by roll_no" --limit 10', allow_fail=False),
        title='Example: A Python Model in the Same DAG'),
    steps(
        ('Transformations in SQL on warehouse data?', 'dbt.'),
        ('Heavy processing of files, complex code, ML, streaming?', 'Spark (or Python), writing results to the lakehouse/warehouse.'),
        ('Small Python step inside the analytics DAG?', 'dbt Python model, if the adapter supports it.'),
        ('Legacy procedures', 'Migrate gradually: one procedure → a few dbt models, compare outputs.'),
        title='Steps to Choose'),
    crossq(
        ('Can dbt replace Spark?', 'For SQL-shaped analytics on data already in a warehouse, often yes. For raw file processing, ML training and streaming, no; they work together.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Where does dbt fit in the modern data stack? What are exposures and the semantic layer?', 'dbt in the Modern Data Stack', minutes=8, cards=[
    definition(
        defbox('In the modern data stack, EL tools (Fivetran, Airbyte) load raw data into a cloud warehouse/lakehouse; <strong>dbt</strong> transforms it; '
               'BI and ML tools consume it; orchestrators, observability and catalogue tools operate around it.',
               '<strong>Exposures</strong> declare downstream consumers (dashboards, ML models, apps) in YAML so lineage shows what each model feeds '
               'and <code>dbt build --select +exposure:name</code> refreshes exactly what a dashboard needs. The <strong>dbt Semantic Layer</strong> '
               '(MetricFlow) defines metrics once (e.g. pass rate) so every BI tool computes them identically.'),
        tags('Modern Data Stack', 'Exposures', 'Semantic Layer', 'MetricFlow', 'Lineage', 'Analytics Engineering'),
    ),
    analogy('dbt is the <strong>central kitchen</strong> of a food chain: suppliers deliver raw ingredients (EL), the kitchen prepares standard dishes '
            '(models), outlets serve them (BI), and the menu card (semantic layer) guarantees "pass rate" tastes the same in every outlet.'),
    stack_anim(),
    real_world(
        scenario('Knowing what a change affects',
                 p('The "Placement Dashboard" in Power BI is declared as an exposure depending on <code>fct_placements</code> and <code>dim_students</code>. '
                   'When someone changes <code>stg_students</code>, the lineage graph and CI show that the dashboard is downstream, and its owner is notified.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        dfile('models/marts/fct_marks.sql', "select * from {{ ref('stg_marks') }}", show=False),
        dfile('models/marts/dim_students.sql', "select * from {{ ref('stg_students') }}", show=False),
        dfile('models/exposures.yml', """
exposures:
  - name: placement_dashboard
    label: Placement Dashboard (Power BI)
    type: dashboard
    maturity: high
    url: https://app.powerbi.com/groups/cdac/reports/placements
    owner:
      name: Placement Cell
      email: placements@cdac.example
    depends_on:
      - ref('fct_marks')
      - ref('dim_students')
"""),
        dbtrun('!dbt seed', 'dbt --quiet ls --resource-type exposure', 'dbt --quiet ls --select +exposure:placement_dashboard --resource-type model',
               'dbt build --select +exposure:placement_dashboard --exclude resource_type:seed'),
        title='Example: Building Exactly What a Dashboard Needs'),
    steps(
        ('Declare important consumers as exposures', 'Dashboards, ML models, reverse-ETL syncs, with owners.'),
        ('Use them in jobs', '<code>dbt build --select +exposure:name</code> for dashboard-specific refreshes.'),
        ('Define shared metrics', 'In the semantic layer (semantic models + metrics) for consistent KPIs.'),
        ('Connect the stack', 'Orchestrator for scheduling, catalogue for discovery, observability for alerts.'),
        title='Steps'),
    crossq(
        ('Why do analytics engineers exist as a role?', 'dbt made it practical for SQL-strong analysts to own production transformations with engineering practices (Git, tests, CI), between data engineers (pipelines/platform) and analysts (insights).'),
        ('What are the limits of dbt?', 'It only transforms data already in a supported platform; it is batch-oriented (not streaming); it depends on the warehouse\'s performance and cost; and very complex non-SQL logic is better done in Spark/Python.'),
    ),
]),
])
