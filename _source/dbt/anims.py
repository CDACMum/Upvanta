from build import *


def _lines(x, y, lines, color='#e2e8f0', size=11, step=None, gap=16):
    return ''.join(stext(x, y + i * gap, ln, color, size, 'start', step=step).replace('<text ', '<text xml:space="preserve" ', 1)
                   for i, ln in enumerate(lines))


def _flow_row(items, y=60, w=130, gap=20, x0=20, h=60):
    """Boxes in a row with arrows; items = (title, sub, color, step)."""
    out = []
    for i, (t, s, c, st) in enumerate(items):
        x = x0 + i * (w + gap)
        out.append(sbox(x, y, w, h, t, s, c, step=st, focus=st, size=12))
        if i:
            out.append(sarrow(x - gap, y + h / 2, x - 2, y + h / 2, 'gray', step=st))
    return ''.join(out)


# ================================================================== foundations
def elt_anim():
    elems = [
        stext(380, 24, 'dbt is the T in ELT', 'blue', 15, bold=True),
        sbox(20, 60, 130, 60, 'Sources', 'MySQL · APIs · CSV', 'gray', step=1, size=12),
        sbox(190, 60, 140, 60, 'Extract + Load', 'Fivetran · Airbyte\nSpark · Python', 'amber', step=2, focus=2, size=12),
        sbox(370, 40, 370, 200, '', '', 'green', step=3, fill_opacity=0.06),
        stext(555, 60, 'Warehouse (Snowflake / BigQuery / Databricks / DuckDB)', 'green', 11, step=3, bold=True),
        sbox(385, 75, 100, 50, 'raw', 'as loaded', 'gray', step=3, size=12),
        sbox(505, 75, 100, 50, 'staging', 'cleaned', 'blue', step=4, focus=4, size=12),
        sbox(625, 75, 100, 50, 'marts', 'facts · dims', 'purple', step=4, focus=4, size=12),
        sarrow(485, 100, 503, 100, 'blue', step=4), sarrow(605, 100, 623, 100, 'purple', step=4),
        sbox(430, 160, 250, 60, 'dbt', 'SELECT statements + Jinja\n→ CREATE VIEW / TABLE', 'cyan', step=4, focus=4, size=12),
        sflow(150, 90, 190, 90, 'amber', step=2, count=2), sflow(330, 90, 385, 100, 'amber', step=2, count=2),
        stext(200, 200, 'dbt does not extract or load:', 'pink', 12, step=5, focus=5),
        stext(200, 218, 'it transforms data already in', 'pink', 12, step=5),
        stext(200, 236, 'the warehouse, using its compute', 'pink', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'Data starts in operational systems: the exam MySQL database, the attendance API, CSV exports.',
        'An <strong>extract-and-load</strong> tool copies it, unchanged, into the warehouse\'s raw schema.',
        'Now the raw data sits in a warehouse whose SQL engine can transform terabytes quickly.',
        '<strong>dbt</strong> runs the <strong>T</strong>: you write SELECT statements (models); dbt wraps them in CREATE VIEW/TABLE, runs them in dependency order and builds staging and mart layers.',
        'dbt itself moves no data in or out: all computation happens inside the warehouse.',
    ])


def core_cloud_anim():
    elems = [
        stext(190, 26, 'dbt Core (open source)', 'blue', 14, bold=True),
        stext(570, 26, 'dbt Cloud (managed SaaS)', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="280" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(60, 50, 260, 50, 'pip install dbt-core dbt-snowflake', 'CLI on your laptop / server', 'blue', step=1, focus=1, size=11),
        sbox(60, 120, 260, 44, 'You schedule it', 'Airflow · cron · GitHub Actions', 'gray', step=2, size=12),
        sbox(60, 180, 260, 44, 'You host docs & logs', '', 'gray', step=2, size=12),
        sbox(440, 50, 260, 50, 'Browser IDE + CLI', 'same dbt projects', 'green', step=3, focus=3, size=12),
        sbox(440, 120, 260, 44, 'Built-in jobs & scheduler', 'CI on pull requests', 'green', step=3, size=12),
        sbox(440, 180, 260, 44, 'Hosted docs, Explorer, Semantic Layer', '', 'green', step=3, size=11),
        stext(380, 260, 'adapters connect dbt to each warehouse: snowflake · bigquery · databricks · postgres · duckdb …', 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 280, *elems), [
        '<strong>dbt Core</strong> is the free, open-source command-line tool: <code>pip install dbt-core</code> plus an adapter for your warehouse.',
        'With Core you provide everything around it: scheduling (Airflow, cron, CI), logs, and hosting of documentation.',
        '<strong>dbt Cloud</strong> is the paid managed platform: a browser IDE, job scheduler, CI for pull requests, hosted docs and lineage, and the Semantic Layer.',
        'Both run the same project files. <strong>Adapters</strong> translate dbt\'s work into each warehouse\'s SQL dialect.',
    ])


def project_tree_anim():
    rows = [('cdac_dw/', 'gray', 1), ('  dbt_project.yml', 'amber', 1), ('  models/', 'blue', 2), ('    staging/stg_students.sql', 'blue', 2),
            ('    marts/fct_marks.sql', 'blue', 2), ('  seeds/raw_students.csv', 'green', 3), ('  tests/', 'red', 3), ('  macros/', 'purple', 4),
            ('  snapshots/', 'pink', 4), ('  target/  (generated)', 'gray', 5)]
    elems = [stext(380, 24, 'A dbt project is just a folder of files', 'blue', 15, bold=True)]
    for i, (t, c, st) in enumerate(rows):
        elems.append(stext(40, 60 + i * 24, t, PALETTE.get(c, c), 13, 'start', step=st, bold=t.endswith('/') and not t.startswith('    ')))
    notes = [(1, 72, 'project name, profile, folder configs'), (2, 132, 'models: one SELECT per file → one table/view'),
             (3, 192, 'seeds: small CSVs · tests: custom SQL tests'), (4, 240, 'macros: reusable Jinja · snapshots: SCD2 history'),
             (5, 276, 'compiled SQL, manifest.json, run_results.json')]
    for st, y, t in notes:
        elems.append(stext(380, y, '← ' + t, 'cyan', 12, 'start', step=st, focus=st))
    return anim(canvas(760, 300, *elems), [
        '<code>dbt_project.yml</code> names the project, points to a connection profile and holds default configs per folder.',
        '<code>models/</code> holds .sql files: each contains one SELECT and becomes one view or table. Sub-folders organise layers.',
        '<code>seeds/</code> holds small CSV reference files; <code>tests/</code> holds custom (singular) data tests.',
        '<code>macros/</code> holds reusable Jinja functions; <code>snapshots/</code> captures history of changing rows.',
        '<code>target/</code> is generated by dbt: compiled SQL and metadata (manifest.json, run_results.json). It is not committed to Git.',
    ])


def profiles_anim():
    elems = [
        stext(380, 24, 'One project, many targets', 'blue', 15, bold=True),
        sbox(20, 70, 180, 70, 'dbt project', 'models (same SQL)', 'gray', step=1, size=12),
        sbox(270, 45, 200, 60, 'target: dev', 'schema dbt_vineeta\n4 threads', 'blue', step=2, focus=2, size=12),
        sbox(270, 125, 200, 60, 'target: prod', 'schema analytics\n16 threads', 'green', step=3, focus=3, size=12),
        sarrow(200, 95, 268, 75, 'blue', step=2), sarrow(200, 115, 268, 155, 'green', step=3),
        sbox(540, 45, 200, 60, 'dbt_vineeta.fct_marks', 'personal sandbox', 'blue', step=2, size=11),
        sbox(540, 125, 200, 60, 'analytics.fct_marks', 'used by dashboards', 'green', step=3, size=11),
        sflow(470, 75, 540, 75, 'blue', step=2, count=2), sflow(470, 155, 540, 155, 'green', step=3, count=2),
        stext(380, 230, '~/.dbt/profiles.yml holds credentials · dbt run --target prod', 'cyan', 12, step=4, focus=4),
        stext(380, 252, "{{ target.name }} and {{ env_var('DBT_PASSWORD') }} available in Jinja", 'pink', 12, step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'The same models are deployed to different places. The project never contains credentials.',
        'Each developer runs against a <strong>dev target</strong> that writes into a personal schema, so experiments never touch production.',
        'The scheduler runs with <code>--target prod</code>, building the real tables dashboards read.',
        'Connection details live in <code>profiles.yml</code> (outside the repo); secrets come from environment variables.',
    ])


def run_flow_anim():
    elems = [stext(380, 24, 'What happens when you type dbt run', 'blue', 15, bold=True)]
    elems.append(_flow_row([('Parse', 'read .sql/.yml', 'gray', 1), ('Compile', 'Jinja → SQL', 'amber', 2), ('Build DAG', 'from ref()', 'purple', 3),
                            ('Execute', 'CREATE … AS', 'green', 4), ('Artifacts', 'run_results', 'cyan', 5)], y=60, w=128, gap=22))
    elems += [
        _lines(40, 165, ["select * from {{ ref('stg_students') }}"], '#fde68a', 12, step=2),
        stext(330, 165, '→', 'amber', 14, 'start', step=2),
        _lines(360, 165, ['select * from "cdac"."dev"."stg_students"'], '#86efac', 12, step=2),
        stext(380, 210, 'stg_students → int_scores → fct_marks: run in dependency order, in parallel where possible', 'purple', 12, step=3),
        stext(380, 235, 'create or replace view/table … as (compiled select)', 'green', 12, step=4),
        stext(380, 260, 'target/run_results.json · manifest.json · logs/dbt.log', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 280, *elems), [
        '<strong>Parse</strong>: dbt reads every model, YAML file and macro in the project.',
        '<strong>Compile</strong>: Jinja is rendered: <code>ref()</code> becomes the real schema.table name for the current target, macros expand to SQL.',
        '<strong>Build the DAG</strong>: the <code>ref()</code> calls define dependencies, so dbt knows the order and what can run in parallel (threads).',
        '<strong>Execute</strong>: each model\'s SELECT is wrapped in DDL for its materialization (view, table, incremental merge) and sent to the warehouse.',
        '<strong>Artifacts</strong>: results, timings and the full project graph are written to <code>target/</code>, used by docs, CI and orchestration.',
    ])


# ================================================================== models
def model_anim():
    elems = [
        stext(380, 24, 'A model = one SELECT in one file', 'blue', 15, bold=True),
        sbox(20, 40, 330, 110, '', '', 'gray', step=1, fill_opacity=0.08),
        _lines(30, 60, ['-- models/marts/course_summary.sql', "select course_code,", '       count(*) as students', "from {{ ref('stg_students') }}", 'group by 1'], '#e2e8f0', 12, step=1),
        sarrow(350, 95, 418, 95, 'amber', step=2),
        stext(385, 85, 'dbt run', 'amber', 11, step=2),
        sbox(420, 40, 320, 110, '', '', 'green', step=2, fill_opacity=0.1),
        _lines(432, 62, ['create view "dev"."course_summary" as (', '  select course_code, count(*) as students', '  from "dev"."stg_students"', '  group by 1', ');'], '#86efac', 11, step=2),
        stext(380, 190, 'file name = object name · folder = layer · no DDL, no INSERT written by you', 'cyan', 12, step=3, focus=3),
        stext(380, 215, 'change the materialization in config → same SELECT becomes a table / incremental', 'purple', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 235, *elems), [
        'You write only a <code>SELECT</code> in a .sql file. No CREATE, no INSERT, no DROP.',
        'dbt wraps it in the right DDL for the warehouse and creates an object named after the file.',
        'The file name becomes the relation name; the folder usually maps to a layer (staging, marts).',
        'Switching from view to table or incremental is a one-line config change; the SELECT stays the same.',
    ])


def dag_anim():
    elems = [
        stext(380, 24, "ref() calls build the lineage graph (DAG)", 'blue', 15, bold=True),
        sbox(20, 50, 140, 40, 'raw_students', 'seed', 'gray', step=1, size=11), sbox(20, 120, 140, 40, 'raw_marks', 'seed', 'gray', step=1, size=11),
        sbox(20, 190, 140, 40, 'raw_courses', 'seed', 'gray', step=1, size=11),
        sbox(210, 50, 150, 40, 'stg_students', '', 'blue', step=2, size=12), sbox(210, 120, 150, 40, 'stg_marks', '', 'blue', step=2, size=12),
        sbox(210, 190, 150, 40, 'stg_courses', '', 'blue', step=2, size=12),
        sarrow(160, 70, 208, 70, 'blue', step=2), sarrow(160, 140, 208, 140, 'blue', step=2), sarrow(160, 210, 208, 210, 'blue', step=2),
        sbox(410, 85, 150, 50, 'dim_students', 'student + course', 'purple', step=3, focus=3, size=11),
        sarrow(360, 70, 408, 100, 'purple', step=3), sarrow(360, 210, 408, 120, 'purple', step=3),
        sbox(600, 120, 140, 50, 'fct_marks', '', 'green', step=4, focus=4, size=12),
        sarrow(360, 140, 598, 145, 'green', step=4), sarrow(560, 110, 598, 135, 'green', step=4),
        stext(380, 265, 'dbt run --select +fct_marks → builds fct_marks and everything upstream', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Raw seeds/sources are the starting nodes.',
        'Each staging model refs one raw table: <code>{{ ref(\'raw_students\') }}</code>.',
        '<code>dim_students</code> refs two staging models, so it must wait for both.',
        '<code>fct_marks</code> refs stg_marks and dim_students. dbt infers all of this from <code>ref()</code>; you never write the order yourself.',
        'The graph powers selection (<code>+model</code>, <code>model+</code>), parallel runs, and the lineage diagram in dbt docs.',
    ])


def source_anim():
    elems = [
        stext(380, 24, "{{ source('exam_db', 'marks') }} vs hard-coded table names", 'blue', 14, bold=True),
        sbox(20, 55, 330, 110, '', '', 'purple', step=1, fill_opacity=0.08),
        _lines(35, 78, ['# models/staging/_sources.yml', 'sources:', '  - name: exam_db', '    schema: raw_exam', '    tables: [ { name: marks,', '      loaded_at_field: loaded_at } ]'], '#e2e8f0', 11, step=1),
        sbox(410, 55, 330, 60, "from {{ source('exam_db','marks') }}", '→ from raw_exam.marks', 'green', step=2, focus=2, size=12),
        stext(575, 140, 'raw tables appear as green source nodes in the DAG', 'green', 11, step=2),
        sbox(410, 165, 330, 60, 'dbt source freshness', 'max(loaded_at) older than 24h → ERROR', 'amber', step=3, focus=3, size=12),
        stext(190, 215, 'one place to change schema names', 'cyan', 12, step=4, focus=4),
        stext(190, 233, 'tests and docs on raw data too', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 255, *elems), [
        'Raw tables loaded by other tools are declared once in YAML as <strong>sources</strong>, with their schema and table names.',
        'Models read them with <code>source()</code> instead of hard-coding names. dbt resolves the real name and shows the source in lineage.',
        'With <code>loaded_at_field</code> and thresholds, <code>dbt source freshness</code> alerts when the loader stopped delivering data.',
        'If the raw schema is renamed, you change one YAML line, not fifty models. Sources can also have tests and descriptions.',
    ])


def seed_anim():
    elems = [
        stext(380, 24, 'Seeds: version-controlled CSV → warehouse table', 'blue', 15, bold=True),
        sbox(20, 55, 260, 110, '', '', 'gray', step=1, fill_opacity=0.08),
        _lines(35, 78, ['seeds/raw_courses.csv', 'course_code,course_name,months,fee', 'PG-DBDA,Big Data Analytics,6,95000', 'PG-DAC,Advanced Computing,6,90000'], '#e2e8f0', 11, step=1),
        sarrow(280, 110, 348, 110, 'green', step=2), stext(315, 100, 'dbt seed', 'green', 11, step=2),
        stable(350, 60, ['course_code', 'course_name', 'months', 'fee'], [['PG-DBDA', 'Big Data Analytics', '6', '95000'], ['PG-DAC', 'Advanced Computing', '6', '90000']],
               [90, 140, 60, 70], step=2, title='dev_raw.raw_courses', title_color='green'),
        stext(380, 200, 'use for small, slow-changing lookup data: course list, state codes, grade bands', 'cyan', 12, step=3, focus=3),
        stext(380, 222, 'not for big or frequently changing data → load it with an EL tool as a source', 'red', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 240, *elems), [
        'A seed is a CSV file committed in the project\'s <code>seeds/</code> folder.',
        '<code>dbt seed</code> creates (or replaces) a table with that data; models <code>ref()</code> it like any model.',
        'Ideal for small reference data that changes rarely and benefits from code review.',
        'Seeds are not a loading tool: large or frequently changing data should come from an EL pipeline as a source.',
    ])


def layers_anim():
    elems = [stext(380, 24, 'Staging → Intermediate → Marts', 'blue', 15, bold=True)]
    elems.append(_flow_row([('sources', 'raw tables', 'gray', 1), ('staging', 'stg_: 1:1, rename,\ncast, clean', 'blue', 2),
                            ('intermediate', 'int_: joins,\nbusiness logic', 'amber', 3), ('marts', 'fct_ / dim_\nfor BI', 'purple', 4)], y=55, w=160, gap=33, h=70))
    elems += [
        stext(380, 170, 'staging: views, one per source table, no joins', 'blue', 12, step=2),
        stext(380, 192, 'intermediate: reusable building blocks, not exposed to users', 'amber', 12, step=3),
        stext(380, 214, 'marts: tables shaped for consumers (star schema), documented and tested', 'purple', 12, step=4),
        stext(380, 245, 'clear layers = easy debugging, reuse and ownership', 'cyan', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 265, *elems), [
        'Raw data arrives in source tables exactly as the loader wrote it.',
        '<strong>Staging</strong> models (<code>stg_</code>) map 1:1 to source tables: rename columns, cast types, standardise values. No joins.',
        '<strong>Intermediate</strong> models (<code>int_</code>) combine staging models and apply business logic, as reusable steps.',
        '<strong>Marts</strong> (<code>fct_</code>, <code>dim_</code>) are the final, consumer-facing tables, usually a star schema per business area.',
        'This convention (from dbt Labs\' style guide) keeps large projects understandable.',
    ])


# ================================================================== materializations
def materializations_anim():
    elems = [stext(380, 24, 'Same SELECT, four materializations', 'blue', 15, bold=True)]
    mats = [('view', 'stored query\nre-runs on read', 'blue'), ('table', 'full rebuild\nevery dbt run', 'green'),
            ('incremental', 'insert/merge only\nnew rows', 'amber'), ('ephemeral', 'inlined as CTE\nno object', 'purple')]
    for i, (t, d, c) in enumerate(mats):
        x = 20 + i * 185
        elems.append(sbox(x, 55, 170, 80, t, d, c, step=i + 1, focus=i + 1, size=13))
    notes = ['cheap to build · slow if read often', 'fast reads · rebuild cost grows with data',
             'fast runs on big data · needs unique key / filter', 'keeps the warehouse tidy · cannot be queried']
    for i, n in enumerate(notes):
        elems.append(stext(105 + i * 185, 160, n.split(' · ')[0], 'cyan', 11, step=i + 1))
        elems.append(stext(105 + i * 185, 177, n.split(' · ')[1], 'pink', 11, step=i + 1))
    elems.append(stext(380, 230, "{{ config(materialized='table') }}  or  +materialized: table in dbt_project.yml", 'cyan', 12, step=5, focus=5))
    return anim(canvas(760, 250, *elems), [
        '<strong>view</strong> (default): only the query is stored; it runs every time someone reads it. Good for staging.',
        '<strong>table</strong>: the result is stored and fully rebuilt on each run. Good for marts read by BI.',
        '<strong>incremental</strong>: the first run builds the table; later runs process only new or changed rows. Good for large event/fact tables.',
        '<strong>ephemeral</strong>: no object is created; the model is inlined as a CTE into the models that ref it.',
        'Choose per model with a config block or per folder in <code>dbt_project.yml</code>.',
    ])


def incremental_anim():
    elems = [
        stext(380, 24, 'Incremental model: process only what is new', 'blue', 15, bold=True),
        sbox(20, 50, 220, 70, 'Run 1 (full)', 'all 1,000,000 rows', 'blue', step=1, focus=1, size=12),
        sbox(280, 50, 200, 70, 'fct_marks', '1,000,000 rows', 'green', step=1, size=12),
        sflow(240, 85, 280, 85, 'blue', step=1, count=3),
        sbox(20, 150, 220, 70, 'Run 2 (incremental)', "where exam_date >\n(select max(exam_date) from {{ this }})", 'amber', step=2, focus=2, size=11),
        stext(130, 245, 'is_incremental() is true', 'amber', 11, step=2),
        sflow(240, 185, 360, 120, 'amber', step=3, count=2),
        stext(390, 175, '+ 5,000 new rows', 'amber', 12, step=3, focus=3),
        sbox(520, 50, 220, 70, 'unique_key: mark_id', 'MERGE: update changed,\ninsert new', 'purple', step=4, focus=4, size=12),
        stext(630, 145, 'no unique_key → append only', 'pink', 11, step=4),
        stext(380, 270, 'dbt run --full-refresh rebuilds from scratch (logic change, late data fix)', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'The first run (or when the table does not exist) builds the whole table like a normal table model.',
        'On later runs <code>is_incremental()</code> is true, so the <code>{% if is_incremental() %}</code> filter limits the SELECT to rows newer than what the table already holds (<code>{{ this }}</code>).',
        'Only those few thousand rows are processed and written, so runs stay fast as the table grows.',
        'With a <code>unique_key</code>, dbt merges: rows with existing keys are updated, new keys inserted. Without one, rows are appended.',
        'When the logic changes, <code>--full-refresh</code> drops and rebuilds the table completely.',
    ])


def snapshot_anim():
    elems = [
        stext(380, 24, 'Snapshots capture history (SCD Type 2)', 'blue', 15, bold=True),
        stable(20, 60, ['roll', 'city'], [['2402', 'Pune']], [60, 110], step=1, title='source, day 1', title_color='gray'),
        stable(20, 160, ['roll', 'city'], [['2402', 'Navi Mumbai']], [60, 110], step=3, title='source, day 2', title_color='amber'),
        stable(250, 60, ['roll', 'city', 'dbt_valid_from', 'dbt_valid_to'], [['2402', 'Pune', '10-12', 'null']], [55, 100, 120, 110], step=2, title='snapshot after day 1', title_color='blue'),
        stable(250, 160, ['roll', 'city', 'dbt_valid_from', 'dbt_valid_to'], [['2402', 'Pune', '10-12', '10-13'], ['2402', 'Navi Mumbai', '10-13', 'null']],
               [55, 100, 120, 110], step=4, title='snapshot after day 2', title_color='green', focus_rows={0: '4', 1: '4'}),
        stext(380, 265, 'strategy: timestamp (updated_at column) or check (compare listed columns)', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'The source table holds only the current value: student 2402 lives in Pune.',
        '<code>dbt snapshot</code> copies the row and adds <code>dbt_valid_from</code> and <code>dbt_valid_to</code> (null = current).',
        'Next day the source row is updated in place: the city is now Navi Mumbai. The old value is gone from the source.',
        'The next snapshot run closes the old version (sets <code>dbt_valid_to</code>) and inserts the new one. History is preserved.',
        'Changes are detected by a <strong>timestamp</strong> column or by <strong>checking</strong> chosen columns for differences.',
    ])


def config_anim():
    elems = [
        stext(380, 24, 'Where configuration comes from (most specific wins)', 'blue', 15, bold=True),
        sbox(60, 55, 640, 50, 'dbt_project.yml', "models: cdac_dw: +materialized: view   (whole project)", 'gray', step=1, size=12),
        sbox(110, 115, 540, 50, 'dbt_project.yml folder', "marts: +materialized: table   (models/marts/*)", 'blue', step=2, size=12),
        sbox(160, 175, 440, 50, 'properties .yml', "models: - name: fct_marks  config: { tags: ['daily'] }", 'amber', step=3, size=11),
        sbox(210, 235, 340, 50, "{{ config(...) }} in the .sql file", "materialized='incremental'", 'green', step=4, focus=4, size=12),
        stext(380, 305, 'result for fct_marks: incremental + tag daily', 'cyan', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 320, *elems), [
        'Project-wide defaults in <code>dbt_project.yml</code> apply to every model.',
        'Folder-level configs (<code>+materialized</code> under <code>marts:</code>) override them for that folder.',
        'Configs in a model\'s YAML properties override folder settings.',
        'A <code>{{ config(...) }}</code> block inside the .sql file is the most specific and wins.',
        'dbt merges all levels: the model ends up incremental (from the file) and tagged daily (from YAML).',
    ])


def schema_anim():
    elems = [
        stext(380, 24, 'Custom schemas: +schema: marts', 'blue', 15, bold=True),
        sbox(40, 60, 200, 60, 'target schema', 'dev: dbt_vineeta\nprod: analytics', 'gray', step=1, size=12),
        sbox(290, 60, 180, 60, '+schema: marts', 'in dbt_project.yml', 'amber', step=2, size=12),
        sbox(520, 45, 220, 40, 'dev: dbt_vineeta_marts', '', 'blue', step=3, focus=3, size=12),
        sbox(520, 95, 220, 40, 'prod: analytics_marts', '', 'green', step=3, focus=3, size=12),
        sarrow(470, 90, 518, 65, 'blue', step=3), sarrow(470, 90, 518, 115, 'green', step=3),
        stext(380, 175, 'default generate_schema_name = <target_schema>_<custom_schema>', 'cyan', 12, step=4, focus=4),
        stext(380, 200, 'override the macro to use plain "marts" in prod only', 'purple', 12, step=5, focus=5),
        stext(380, 225, 'alias config renames the object: alias=\'student_dim\'', 'pink', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Every target has a default schema: a personal one in dev, a shared one in prod.',
        'A folder or model can request a <strong>custom schema</strong>, e.g. all marts in a "marts" schema.',
        'By default dbt <strong>prefixes</strong> it with the target schema, so developers never collide: dbt_vineeta_marts vs analytics_marts.',
        'This behaviour comes from the <code>generate_schema_name</code> macro.',
        'Teams often override that macro so prod uses clean names (marts) while dev keeps prefixes. <code>alias</code> changes the object name.',
    ])


# ================================================================== tests & docs
def tests_anim():
    elems = [
        stext(380, 24, 'Generic tests: one YAML line → one SQL query', 'blue', 15, bold=True),
        sbox(20, 50, 300, 130, '', '', 'gray', step=1, fill_opacity=0.08),
        _lines(35, 72, ['columns:', '  - name: roll_no', '    data_tests: [unique, not_null]', '  - name: course_code', "    data_tests:", "      - accepted_values: {values: [...]}", "      - relationships: {to: ref('dim_courses'), ...}"], '#e2e8f0', 11, step=1),
        sarrow(320, 115, 368, 115, 'amber', step=2), stext(345, 133, 'SQL', 'amber', 10, step=2),
        sbox(370, 50, 370, 60, 'select roll_no from stg_students', 'group by roll_no having count(*) > 1', 'amber', step=2, focus=2, size=11),
        sbox(370, 125, 370, 50, '0 rows returned', 'PASS', 'green', step=3, focus=3, size=12),
        sbox(370, 190, 370, 50, '2 rows returned', 'FAIL 2 (or WARN with severity: warn)', 'red', step=4, focus=4, size=12),
        stext(190, 230, 'a test = a query that finds bad rows', 'cyan', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 255, *elems), [
        'Tests are declared next to columns in YAML. The four built-ins: <code>unique</code>, <code>not_null</code>, <code>accepted_values</code>, <code>relationships</code>.',
        '<code>dbt test</code> compiles each into a SELECT that returns the rows violating the rule.',
        'If the query returns no rows, the test passes.',
        'If it returns rows, the test fails (or warns, depending on <code>severity</code>), and the count tells you how many bad rows exist.',
        'That simple idea, "a test is a query that should return nothing", also explains singular and custom generic tests.',
    ])


def singular_test_anim():
    elems = [
        stext(190, 26, 'Singular test (one-off)', 'blue', 14, bold=True),
        stext(570, 26, 'Custom generic test (reusable)', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="270" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(20, 50, 340, 110, '', '', 'blue', step=1, fill_opacity=0.08),
        _lines(35, 72, ['-- tests/assert_marks_in_range.sql', 'select * from {{ ref(\'fct_marks\') }}', 'where marks < 0 or marks > 100'], '#e2e8f0', 11, step=1),
        stext(190, 190, 'specific business rule, one model', 'blue', 12, step=2, focus=2),
        sbox(400, 50, 340, 110, '', '', 'green', step=3, fill_opacity=0.08),
        _lines(415, 72, ['{% test between(model, column_name, lo, hi) %}', 'select * from {{ model }}', 'where {{ column_name }} not between {{ lo }} and {{ hi }}', '{% endtest %}'], '#e2e8f0', 11, step=3),
        stext(570, 190, '- between: {lo: 0, hi: 100}  on any column', 'green', 12, step=4, focus=4),
        stext(380, 245, 'both: return failing rows; zero rows = pass', 'cyan', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 265, *elems), [
        'A <strong>singular test</strong> is a .sql file in <code>tests/</code> containing a query that returns rows breaking a rule.',
        'Use it for rules that apply to one model, such as "marks must be between 0 and 100 in fct_marks".',
        'A <strong>custom generic test</strong> is a parameterised test macro (<code>{% test %}</code>) you write once.',
        'It can then be attached to any column in YAML, exactly like built-in tests.',
        'Both follow the same contract: a failing test returns the offending rows.',
    ])


def unit_test_anim():
    elems = [
        stext(380, 24, 'Unit tests (dbt 1.8+): test logic with fixed inputs', 'blue', 15, bold=True),
        stable(20, 60, ['roll_no', 'marks'], [['1', '92'], ['2', '74'], ['3', '40']], [80, 70], step=1, title='given: mock input', title_color='gray'),
        sbox(250, 70, 200, 70, 'model logic', "case when marks >= 85 then 'A'\n… end as grade", 'amber', step=2, focus=2, size=11),
        stable(500, 60, ['roll_no', 'grade'], [['1', 'A'], ['2', 'B'], ['3', 'C']], [80, 70], step=3, title='expect', title_color='green'),
        sflow(190, 105, 250, 105, 'amber', step=2, count=2), sflow(450, 105, 500, 105, 'green', step=3, count=2),
        stext(380, 210, 'data tests check real data · unit tests check the SQL logic before it reaches data', 'cyan', 12, step=4, focus=4),
        stext(380, 232, 'run in CI on every pull request: dbt test --select test_type:unit', 'pink', 12, step=4),
    ]
    return anim(canvas(760, 250, *elems), [
        'A unit test supplies small, hand-written <strong>input rows</strong> for the model\'s refs.',
        'dbt runs the model\'s SQL against those mock rows instead of the real tables.',
        'The output must equal the <strong>expected rows</strong>; otherwise the test fails and shows the difference.',
        'Data tests catch bad data; unit tests catch bad logic (edge cases like exactly 85 marks) before deployment.',
    ])


def docs_anim():
    elems = [
        stext(380, 24, 'Documentation generated from the project', 'blue', 15, bold=True),
        sbox(20, 55, 240, 90, 'YAML descriptions', 'models · columns · sources\n+ {% docs %} blocks', 'gray', step=1, size=12),
        sbox(20, 160, 240, 60, 'warehouse catalog', 'column types, row counts', 'gray', step=2, size=12),
        sarrow(260, 100, 318, 130, 'blue', step=3), sarrow(260, 190, 318, 150, 'blue', step=3),
        sbox(320, 105, 160, 70, 'dbt docs generate', 'manifest + catalog', 'blue', step=3, focus=3, size=12),
        sbox(530, 55, 210, 60, 'searchable website', 'every model & column', 'green', step=4, size=12),
        sbox(530, 135, 210, 60, 'lineage graph', 'upstream / downstream', 'purple', step=4, focus=4, size=12),
        sarrow(480, 140, 528, 85, 'green', step=4), sarrow(480, 140, 528, 165, 'purple', step=4),
        stext(380, 250, 'docs live next to the code → reviewed in the same pull request, never out of date', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'You describe models and columns in YAML (and longer text in <code>{% docs %}</code> blocks).',
        'dbt also reads the warehouse catalog: actual column types and statistics.',
        '<code>dbt docs generate</code> combines both into JSON artifacts.',
        '<code>dbt docs serve</code> (or dbt Cloud) shows a searchable site with descriptions, tests and an interactive lineage graph.',
        'Because docs are code, they change in the same pull request as the model.',
    ])


# ================================================================== jinja & macros
def jinja_anim():
    elems = [
        stext(380, 24, 'Jinja: SQL that writes SQL', 'blue', 15, bold=True),
        sbox(20, 50, 340, 170, '', '', 'amber', step=1, fill_opacity=0.08),
        _lines(35, 72, ["{% set subjects = ['SQL', 'Spark', 'Java'] %}", 'select roll_no,', '{% for s in subjects %}', "  sum(case when subject = '{{ s }}'", "      then marks end) as {{ s | lower }}_marks", '  {{ "," if not loop.last }}', '{% endfor %}', "from {{ ref('stg_marks') }} group by 1"], '#fde68a', 11, step=1),
        sarrow(360, 135, 398, 135, 'green', step=2), stext(380, 160, 'dbt', 'green', 10, step=2),
        sbox(400, 50, 340, 170, '', '', 'green', step=2, fill_opacity=0.08),
        _lines(415, 72, ['select roll_no,', "  sum(case when subject = 'SQL'", '      then marks end) as sql_marks,', "  sum(case when subject = 'Spark'", '      then marks end) as spark_marks,', "  sum(case when subject = 'Java'", '      then marks end) as java_marks', 'from "dev"."stg_marks" group by 1'], '#86efac', 11, step=2),
        stext(380, 250, '{{ }} prints a value · {% %} runs logic · {# #} comment', 'cyan', 12, step=3, focus=3),
    ]
    return anim(canvas(760, 270, *elems), [
        'The model mixes SQL with Jinja: a list variable and a for-loop.',
        'At compile time Jinja runs first and produces plain SQL with one column per subject; only that SQL reaches the warehouse.',
        '<code>{{ ... }}</code> outputs an expression, <code>{% ... %}</code> is a statement (set, if, for, macro), <code>{# ... #}</code> is a comment.',
    ])


def macro_anim():
    elems = [
        stext(380, 24, 'Macros: reusable SQL functions', 'blue', 15, bold=True),
        sbox(20, 50, 340, 100, '', '', 'purple', step=1, fill_opacity=0.08),
        _lines(35, 72, ['-- macros/grade.sql', '{% macro grade(col) %}', "  case when {{ col }} >= 85 then 'A'", "       when {{ col }} >= 70 then 'B' else 'C' end", '{% endmacro %}'], '#e2e8f0', 11, step=1),
        sbox(400, 45, 340, 40, "{{ grade('marks') }} in fct_marks", '', 'blue', step=2, size=12),
        sbox(400, 95, 340, 40, "{{ grade('final_score') }} in fct_results", '', 'blue', step=2, size=12),
        sarrow(360, 100, 398, 65, 'purple', step=2), sarrow(360, 100, 398, 115, 'purple', step=2),
        stext(380, 180, 'change the grade bands once → every model updates on the next run', 'green', 12, step=3, focus=3),
        stext(380, 205, 'dbt run-operation macro_name runs a macro on its own (admin tasks)', 'amber', 12, step=4, focus=4),
        stext(380, 228, 'packages such as dbt_utils are collections of macros', 'pink', 12, step=4),
    ]
    return anim(canvas(760, 245, *elems), [
        'A macro is a named, parameterised block of Jinja/SQL in <code>macros/</code>.',
        'Models call it like a function; at compile time the call is replaced by the generated SQL.',
        'Business rules live in one place: change the macro and every model using it follows (DRY).',
        'Macros can also run standalone with <code>dbt run-operation</code> (grants, cleanup), and packages share macros between projects.',
    ])


def vars_anim():
    elems = [
        stext(380, 24, 'Variables: parameterise a run', 'blue', 15, bold=True),
        sbox(20, 55, 300, 60, 'dbt_project.yml', "vars: { min_pass_marks: 40 }", 'gray', step=1, size=12),
        sbox(20, 135, 300, 60, 'command line', "dbt run --vars '{min_pass_marks: 50}'", 'amber', step=2, focus=2, size=11),
        sbox(400, 90, 340, 70, "where marks >= {{ var('min_pass_marks') }}", 'run 1 → 40 · run 2 → 50', 'green', step=3, focus=3, size=12),
        sarrow(320, 85, 398, 115, 'gray', step=3), sarrow(320, 165, 398, 135, 'amber', step=3),
        stext(380, 230, "env_var('DBT_PASSWORD') for secrets · target.name to branch on dev/prod", 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 250, *elems), [
        'Project variables have defaults in <code>dbt_project.yml</code>.',
        'A run can override them with <code>--vars</code>, e.g. a stricter pass mark or a back-fill date range from Airflow.',
        'Models read them with <code>var(\'name\', default)</code>; the value is substituted at compile time.',
        '<code>env_var()</code> reads environment variables (credentials, environment names); <code>target</code> exposes the active target.',
    ])


def hooks_anim():
    elems = [
        stext(380, 24, 'Hooks: SQL that runs around models and runs', 'blue', 15, bold=True),
        sbox(20, 60, 160, 50, 'on-run-start', 'create audit table', 'gray', step=1, size=11),
        sbox(220, 60, 140, 50, 'pre-hook', 'set session', 'amber', step=2, size=12),
        sbox(400, 60, 140, 50, 'model', 'CREATE … AS', 'blue', step=2, focus=2, size=12),
        sbox(580, 60, 160, 50, 'post-hook', 'GRANT SELECT …', 'green', step=3, focus=3, size=11),
        sarrow(180, 85, 218, 85, 'gray', step=2), sarrow(360, 85, 398, 85, 'gray', step=2), sarrow(540, 85, 578, 85, 'gray', step=3),
        sbox(280, 150, 200, 50, 'on-run-end', 'log results, grants', 'purple', step=4, focus=4, size=12),
        stext(380, 235, 'typical: grants, audit logging, analyze/vacuum, session settings', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 255, *elems), [
        '<code>on-run-start</code> runs once before anything else, e.g. creating an audit table.',
        'A model\'s <code>pre-hook</code> runs just before it is built.',
        'A <code>post-hook</code> runs right after, e.g. granting read access to the reporting role.',
        '<code>on-run-end</code> runs once at the end and can use the list of results (log timings, notify).',
        'Hooks keep operational SQL in the project instead of separate scripts.',
    ])


def packages_anim():
    elems = [
        stext(380, 24, 'Packages: reuse other people\'s dbt code', 'blue', 15, bold=True),
        sbox(20, 60, 250, 90, 'packages.yml', '- package: dbt-labs/dbt_utils\n  version: 1.3.0', 'gray', step=1, size=12),
        sbox(320, 75, 140, 60, 'dbt deps', 'downloads', 'amber', step=2, focus=2, size=12),
        sarrow(270, 105, 318, 105, 'amber', step=2),
        sbox(510, 50, 230, 40, 'dbt_utils', 'surrogate keys, date spine…', 'green', step=3, size=11),
        sbox(510, 100, 230, 40, 'dbt_expectations', 'Great-Expectations-style tests', 'green', step=3, size=11),
        sbox(510, 150, 230, 40, 'codegen', 'generate YAML / staging', 'green', step=3, size=11),
        sarrow(460, 105, 508, 70, 'green', step=3), sarrow(460, 105, 508, 120, 'green', step=3), sarrow(460, 105, 508, 170, 'green', step=3),
        stext(380, 235, "{{ dbt_utils.generate_surrogate_key(['roll_no', 'subject']) }}", 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 255, *elems), [
        'Dependencies are listed in <code>packages.yml</code> with pinned versions.',
        '<code>dbt deps</code> downloads them into <code>dbt_packages/</code> (from the dbt Hub or Git).',
        'Popular packages add macros, tests and models: dbt_utils, dbt_expectations, codegen, audit_helper.',
        'Their macros are called with the package prefix, like any macro.',
    ])


# ================================================================== running
def selection_anim():
    nodes = [('stg_students', 40, 70), ('stg_marks', 40, 160), ('dim_students', 280, 70), ('fct_marks', 280, 160), ('rpt_toppers', 520, 115)]
    elems = [stext(380, 24, 'Node selection', 'blue', 15, bold=True)]
    for n, x, y in nodes:
        foc = {'fct_marks': '1,2,3', 'stg_marks': '2', 'stg_students': '2', 'dim_students': '2', 'rpt_toppers': '3'}[n]
        elems.append(sbox(x, y, 180, 44, n, '', 'gray', step=None, focus=foc, size=12))
    elems += [sarrow(220, 92, 278, 92, 'gray'), sarrow(220, 182, 278, 182, 'gray'), sarrow(220, 92, 278, 175, 'gray'),
              sarrow(460, 92, 518, 130, 'gray'), sarrow(460, 182, 518, 145, 'gray')]
    elems += [
        stext(380, 240, '--select fct_marks → just that model', 'blue', 12, step=1),
        stext(380, 260, '--select +fct_marks → it and all parents', 'amber', 12, step=2),
        stext(380, 280, '--select fct_marks+ → it and all children', 'green', 12, step=3),
        stext(380, 305, 'tag:daily · path:models/marts · state:modified+ · --exclude …', 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 320, *elems), [
        '<code>--select fct_marks</code> runs only that model.',
        'A leading <code>+</code> adds every upstream (parent) model: useful to rebuild something with its dependencies.',
        'A trailing <code>+</code> adds every downstream (child) model: useful after changing a model to rebuild what depends on it.',
        'Other selectors: tags, paths, resource types, and <code>state:modified+</code> (only changed models and their children, for CI).',
    ])


def build_anim():
    elems = [
        stext(380, 24, 'dbt build = seed + run + snapshot + test, in DAG order', 'blue', 15, bold=True),
        sbox(20, 60, 140, 50, 'seed', 'raw_courses', 'gray', step=1, size=12),
        sbox(190, 60, 140, 50, 'run stg_marks', '', 'blue', step=1, size=12),
        sbox(360, 60, 140, 50, 'test stg_marks', 'unique · not_null', 'amber', step=2, focus=2, size=11),
        sbox(530, 60, 210, 50, 'run fct_marks', 'only if tests pass', 'green', step=3, focus=3, size=12),
        sarrow(160, 85, 188, 85, 'gray', step=1), sarrow(330, 85, 358, 85, 'gray', step=2), sarrow(500, 85, 528, 85, 'gray', step=3),
        sbox(360, 150, 140, 50, 'test FAILS', '', 'red', step=4, focus=4, size=12),
        sbox(530, 150, 210, 50, 'fct_marks SKIPPED', 'bad data not propagated', 'gray', step=4, size=12),
        sarrow(500, 175, 528, 175, 'red', step=4),
        stext(380, 245, 'dbt run builds models only · dbt test only tests · dbt build does both, node by node', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 265, *elems), [
        '<code>dbt build</code> processes seeds, models, snapshots and tests together, following the DAG.',
        'After building a model, its tests run immediately.',
        'Only if they pass do the downstream models build.',
        'If a test fails, everything downstream is skipped, so bad data never reaches the marts.',
        'That is why production jobs usually run <code>dbt build</code> rather than separate run and test steps.',
    ])


def artifacts_anim():
    elems = [
        stext(380, 24, 'target/: what dbt writes after each command', 'blue', 15, bold=True),
        sbox(20, 60, 230, 60, 'compiled/', 'pure SQL after Jinja', 'amber', step=1, focus=1, size=12),
        sbox(270, 60, 230, 60, 'run/', 'SQL actually executed (DDL)', 'blue', step=2, size=12),
        sbox(520, 60, 220, 60, 'manifest.json', 'full project graph', 'purple', step=3, focus=3, size=12),
        sbox(140, 150, 230, 60, 'run_results.json', 'status, timing per node', 'green', step=4, size=12),
        sbox(390, 150, 230, 60, 'catalog.json', 'from docs generate', 'cyan', step=4, size=12),
        stext(380, 245, 'used for debugging · docs · CI state comparison · orchestration (Cosmos, Dagster)', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 265, *elems), [
        '<code>target/compiled/</code> holds each model\'s SELECT with Jinja resolved: copy it into a SQL client to debug.',
        '<code>target/run/</code> holds the full statements dbt executed, including CREATE/MERGE wrappers.',
        '<code>manifest.json</code> describes every node, its config and dependencies.',
        '<code>run_results.json</code> records each node\'s status and timing; <code>catalog.json</code> comes from docs generation.',
        'Tools build on these files: docs, slim CI (<code>--state</code>), Airflow integrations and observability tools.',
    ])


def ci_anim():
    elems = [stext(380, 24, 'CI/CD for dbt', 'blue', 15, bold=True)]
    elems.append(_flow_row([('Feature branch', 'edit models', 'gray', 1), ('Pull request', 'CI job starts', 'amber', 2), ('Slim CI', 'build state:modified+\nin a PR schema', 'purple', 3),
                            ('Review + merge', 'tests green', 'blue', 4), ('Prod deploy', 'scheduled dbt build', 'green', 5)], y=60, w=128, gap=22, h=70))
    elems += [
        stext(380, 175, "dbt build --select state:modified+ --defer --state prod-artifacts/", 'purple', 12, step=3),
        stext(380, 197, 'unchanged parents are read from production (defer) instead of rebuilt', 'purple', 11, step=3),
        stext(380, 235, 'every change is reviewed and tested before it reaches dashboards', 'cyan', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 255, *elems), [
        'A developer changes models on a Git branch, testing in their dev schema.',
        'Opening a pull request triggers a CI job (dbt Cloud, GitHub Actions, GitLab CI).',
        '<strong>Slim CI</strong> builds and tests only modified models and their children, in a temporary schema, comparing against production\'s manifest; <code>--defer</code> reuses prod tables for unchanged parents.',
        'Reviewers see code, test results and lineage impact; the PR is merged only if everything passes.',
        'The production job then runs the merged code on schedule.',
    ])


def airflow_anim():
    elems = [
        stext(380, 24, 'Orchestrating dbt with Airflow', 'blue', 15, bold=True),
        sbox(20, 60, 160, 50, 'extract_load', 'Airbyte / Spark', 'gray', step=1, size=12),
        sbox(220, 60, 170, 50, 'dbt source freshness', '', 'amber', step=2, size=11),
        sbox(430, 60, 140, 50, 'dbt build', 'staging → marts', 'green', step=2, focus=2, size=12),
        sbox(610, 60, 130, 50, 'refresh BI', 'notify', 'purple', step=3, size=12),
        sarrow(180, 85, 218, 85, 'gray', step=2), sarrow(390, 85, 428, 85, 'gray', step=2), sarrow(570, 85, 608, 85, 'gray', step=3),
        stext(380, 160, 'BashOperator("dbt build --target prod") → simple, one task', 'cyan', 12, step=4),
        stext(380, 185, 'Astronomer Cosmos → one Airflow task per dbt model/test (retries per node)', 'cyan', 12, step=4, focus=4),
        stext(380, 220, 'Airflow decides WHEN and in what order with other systems; dbt decides HOW to transform', 'pink', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 240, *elems), [
        'Loading must finish before transformation starts.',
        'The DAG checks source freshness, then runs <code>dbt build</code> for the prod target.',
        'Downstream steps (BI extract refresh, notifications) follow only on success.',
        'dbt can be called as one shell task, or expanded into one Airflow task per model with Astronomer Cosmos for finer retries and visibility.',
        'Division of labour: the orchestrator handles scheduling and cross-system dependencies; dbt handles SQL transformations and their internal order.',
    ])


# ================================================================== practices
def perf_anim():
    elems = [stext(380, 24, 'Making a slow dbt project fast', 'blue', 15, bold=True)]
    stages = [('Find slow models', 'run_results.json timings', 'red'), ('Right materialization', 'view → table → incremental', 'amber'),
              ('Push filters early', 'select only needed columns/rows', 'green'), ('Parallelism', 'threads, warehouse size', 'purple'),
              ('Warehouse features', 'clustering, partitions', 'cyan')]
    for i, (t, d, c) in enumerate(stages):
        w = 680 - i * 100
        elems.append(sbox(380 - w / 2, 48 + i * 48, w, 40, t, d, c, step=i + 1, focus=i + 1, size=12))
    return anim(canvas(760, 300, *elems), [
        'Measure first: <code>run_results.json</code> (or dbt Cloud\'s model timing) shows which models take longest.',
        'Change materializations: heavy views read often → tables; huge append-only facts → incremental.',
        'Reduce work: filter and project early in staging, avoid SELECT *, avoid repeated heavy CTEs.',
        'Run independent models in parallel (<code>threads</code>) and size the warehouse appropriately.',
        'Use warehouse-specific configs: partitioning/clustering (BigQuery, Snowflake), sort/dist keys (Redshift).',
    ])


def naming_anim():
    elems = [stext(380, 24, 'Conventions that keep 500 models understandable', 'blue', 15, bold=True)]
    rows = [('stg_<source>__<table>', 'stg_exam_db__marks', 'blue'), ('int_<entity>_<verb>', 'int_marks_pivoted', 'amber'),
            ('fct_<process>', 'fct_exam_attempts', 'green'), ('dim_<entity>', 'dim_students', 'purple'),
            ('columns: snake_case, _id, _at, is_', 'student_id, submitted_at, is_passed', 'cyan')]
    for i, (p, ex, c) in enumerate(rows):
        y = 50 + i * 46
        elems.append(sbox(20, y, 330, 38, p, '', c, step=i + 1, size=12))
        elems.append(stext(380, y + 24, '→ ' + ex, c, 12, 'start', step=i + 1, focus=i + 1))
    return anim(canvas(760, 290, *elems), [
        'Staging models name the source and table: one staging model per source table.',
        'Intermediate models describe what they do to which entity.',
        'Fact tables describe a business process or event.',
        'Dimension tables describe an entity.',
        'Consistent column naming (ids, timestamps, booleans) lets anyone guess a column name correctly.',
    ])


def contract_anim():
    elems = [
        stext(380, 24, 'Model contracts: guarantee the output shape', 'blue', 15, bold=True),
        sbox(20, 55, 330, 120, '', '', 'purple', step=1, fill_opacity=0.08),
        _lines(35, 78, ['config: { contract: { enforced: true } }', 'columns:', '  - name: student_id  data_type: integer', '    constraints: [ { type: not_null } ]', '  - name: student_name  data_type: varchar'], '#e2e8f0', 11, step=1),
        sbox(400, 55, 340, 50, 'model SELECT matches', 'names + types → build OK', 'green', step=2, focus=2, size=12),
        sbox(400, 125, 340, 50, 'someone renames a column', 'build FAILS before replacing the table', 'red', step=3, focus=3, size=12),
        stext(380, 220, 'protects dashboards and other teams consuming the model (with versions & access)', 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 240, *elems), [
        'A contract lists the exact column names and data types a model must produce, plus optional constraints.',
        'When the model\'s SELECT matches, dbt builds it (and applies supported constraints in the DDL).',
        'If a change would alter the shape (renamed column, wrong type), dbt fails before replacing the table, so consumers never see a broken shape.',
        'Contracts, model versions and access levels (public/protected/private) support large, multi-team projects (dbt Mesh).',
    ])


def quality_anim():
    elems = [stext(380, 24, 'Layered data-quality strategy', 'blue', 15, bold=True)]
    layers = [('Sources', 'freshness · not_null on keys', 'gray'), ('Staging', 'unique · not_null · accepted_values', 'blue'),
              ('Marts', 'relationships · business rules', 'purple'), ('Logic', 'unit tests in CI', 'amber'), ('Monitoring', 'alerts on\nfailures', 'green')]
    for i, (t, d, c) in enumerate(layers):
        elems.append(sbox(20 + i * 147, 60, 135, 90, t, d.replace(' · ', '\n'), c, step=i + 1, focus=i + 1, size=12))
    elems.append(stext(380, 200, 'catch problems as close to the source as possible', 'cyan', 13, step=5, bold=True))
    return anim(canvas(760, 220, *elems), [
        '<strong>Sources</strong>: is data arriving (freshness)? Are key columns present?',
        '<strong>Staging</strong>: primary keys unique and not null, categorical values valid.',
        '<strong>Marts</strong>: foreign keys match dimensions, business rules (marks 0–100, totals reconcile).',
        '<strong>Logic</strong>: unit tests for complex transformations run in CI.',
        '<strong>Monitoring</strong>: failures alert the owning team; warnings are reviewed regularly.',
    ])


# ================================================================== scenarios
def star_anim():
    elems = [
        stext(380, 24, 'From raw seeds to a star schema with dbt', 'blue', 15, bold=True),
        sbox(20, 60, 130, 36, 'raw_students', '', 'gray', step=1, size=11), sbox(20, 110, 130, 36, 'raw_marks', '', 'gray', step=1, size=11),
        sbox(20, 160, 130, 36, 'raw_courses', '', 'gray', step=1, size=11),
        sbox(190, 60, 130, 36, 'stg_students', '', 'blue', step=2, size=11), sbox(190, 110, 130, 36, 'stg_marks', '', 'blue', step=2, size=11),
        sbox(190, 160, 130, 36, 'stg_courses', '', 'blue', step=2, size=11),
        sarrow(150, 78, 188, 78, 'blue', step=2), sarrow(150, 128, 188, 128, 'blue', step=2), sarrow(150, 178, 188, 178, 'blue', step=2),
        sbox(400, 50, 150, 44, 'dim_students', '', 'purple', step=3, size=12), sbox(400, 170, 150, 44, 'dim_courses', '', 'purple', step=3, size=12),
        sbox(600, 105, 140, 60, 'fct_marks', 'grain: roll × subject', 'green', step=4, focus=4, size=11),
        sarrow(320, 78, 398, 72, 'purple', step=3), sarrow(320, 178, 398, 192, 'purple', step=3),
        sarrow(320, 128, 598, 130, 'green', step=4), sarrow(550, 72, 598, 120, 'green', step=4), sarrow(550, 192, 598, 150, 'green', step=4),
        stext(380, 250, 'dbt build → seeds, 6 models, tests, all in order, one command', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'Three raw tables arrive as seeds (in real life, sources loaded by an EL tool).',
        'Staging models clean and rename each one.',
        'Dimension models describe students and courses.',
        'The fact model has one row per student per subject and references the dimensions.',
        'One <code>dbt build</code> creates and tests everything in dependency order.',
    ])


def late_data_anim():
    elems = [
        stext(380, 24, 'Late-arriving rows and incremental models', 'blue', 15, bold=True),
        '<line x1="40" y1="120" x2="720" y2="120" stroke="#64748b" stroke-width="3"/>',
    ]
    for x, d in [(120, '10-11'), (300, '10-12'), (480, '10-13')]:
        elems.append(f'<circle cx="{x}" cy="120" r="8" fill="#38bdf8"/>'); elems.append(stext(x, 145, d, '#cbd5e1', 11))
    elems += [
        stext(480, 100, 'max(exam_date) in table', 'amber', 11, step=1),
        sbox(200, 165, 200, 40, 'row for 10-12 arrives late', '', 'red', step=2, focus=2, size=12),
        stext(300, 225, 'filter "> max" skips it forever ✘', 'red', 12, step=2),
        '<rect x="290" y="105" width="200" height="30" fill="#10b981" fill-opacity="0.2" stroke="#10b981" stroke-dasharray="5,4" data-step="3"/>',
        stext(600, 180, 'look back 3 days:', 'green', 12, step=3, focus=3),
        stext(600, 198, '>= max - interval 3 day', 'green', 12, step=3),
        stext(600, 225, '+ unique_key → merge, no dupes', 'green', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 245, *elems), [
        'An incremental model normally loads rows newer than the latest date already in the table.',
        'A record for an earlier date that arrives late is older than that maximum, so a strict filter never picks it up.',
        'A <strong>look-back window</strong> reprocesses the last few days on every run.',
        'Combined with a <code>unique_key</code> (merge), re-processed rows update instead of duplicating.',
    ])


def debug_anim():
    elems = [stext(380, 24, 'Debugging a failed dbt run', 'blue', 15, bold=True)]
    steps_ = [('Read the error', 'model + DB message', 'red'), ('Open compiled SQL', 'target/compiled', 'amber'), ('Run it directly', 'SQL client / dbt show', 'blue'),
              ('Fix & re-run', '--select model+', 'green'), ('Add a test', 'prevent repeat', 'cyan')]
    for i, (t, sub, c) in enumerate(steps_):
        x = 15 + i * 150
        elems.append(sbox(x, 80, 135, 80, t, sub, c, step=i + 1, focus=i + 1, size=12))
        if i:
            elems.append(sarrow(x - 15, 120, x - 2, 120, 'gray', step=i + 1))
    elems.append(stext(380, 210, 'dbt debug checks the connection · dbt retry re-runs only failed nodes (1.6+)', 'cyan', 12, step=5))
    return anim(canvas(760, 230, *elems), [
        'The run summary names the failing model and the database error (e.g. column not found, division by zero).',
        'Open the model\'s compiled SQL in <code>target/compiled/</code>: Jinja is resolved, so you see exactly what ran.',
        'Run that SQL (or <code>dbt show</code>) to reproduce and inspect the data causing the problem.',
        'Fix the model and re-run it with its children (<code>dbt build --select model+</code>, or <code>dbt retry</code>).',
        'Add a test so the same data issue is caught earlier next time.',
    ])


def stack_anim():
    elems = [
        stext(380, 24, 'dbt in the modern data stack', 'blue', 15, bold=True),
        sbox(20, 60, 130, 60, 'Ingest', 'Fivetran · Airbyte\nKafka', 'gray', step=1, size=11),
        sbox(180, 60, 160, 60, 'Store + compute', 'Snowflake · BigQuery\nDatabricks', 'blue', step=1, size=11),
        sbox(370, 60, 130, 60, 'Transform', 'dbt', 'green', step=2, focus=2, size=13),
        sbox(530, 60, 210, 60, 'Serve', 'Power BI · Tableau\nSemantic layer · ML', 'purple', step=3, size=11),
        sarrow(150, 90, 178, 90, 'gray', step=1), sarrow(340, 90, 368, 90, 'gray', step=2), sarrow(500, 90, 528, 90, 'gray', step=3),
        sbox(180, 160, 400, 44, 'Orchestration · Observability · Catalog', 'Airflow / Dagster · Monte Carlo · DataHub', 'amber', step=4, size=11),
        stext(380, 240, 'dbt = SQL transformations as software: version control, tests, docs, CI', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 260, *elems), [
        'Ingestion tools load raw data into a cloud warehouse or lakehouse, which provides storage and compute.',
        'dbt transforms the data inside that platform.',
        'BI tools, the dbt Semantic Layer and ML consume the modelled tables.',
        'Orchestrators schedule everything; observability and catalog tools watch quality and lineage.',
        'dbt\'s contribution is engineering discipline for SQL: Git, code review, tests, documentation and CI/CD.',
    ])


def severity_anim():
    elems = [
        stext(380, 24, 'Controlling what a failing test does', 'blue', 15, bold=True),
        sbox(20, 60, 220, 60, 'test finds 3 bad rows', '', 'gray', step=1, size=12),
        sbox(290, 45, 210, 44, "severity: error (default)", 'run fails, downstream skipped', 'red', step=2, focus=2, size=11),
        sbox(290, 100, 210, 44, "severity: warn", 'reported, run continues', 'amber', step=3, focus=3, size=11),
        sarrow(240, 90, 288, 67, 'red', step=2), sarrow(240, 90, 288, 122, 'amber', step=3),
        sbox(540, 45, 200, 99, "warn_if: '>0'", "error_if: '>10'\nthresholds on row count", 'purple', step=4, focus=4, size=11),
        sbox(160, 180, 440, 50, 'store_failures: true', 'failing rows saved to a table for inspection', 'green', step=5, focus=5, size=12),
        stext(380, 260, 'where: "exam_date >= current_date - 7" limits a test to recent data', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'A test returned rows: the question is how serious that is.',
        'With the default <code>severity: error</code> the test fails the run, and <code>dbt build</code> skips everything downstream.',
        'With <code>severity: warn</code> the problem is reported as a warning but the pipeline continues.',
        '<code>warn_if</code> and <code>error_if</code> set thresholds on the number of failing rows (e.g. warn above 0, error above 10).',
        '<code>store_failures</code> saves the failing rows in a table so you can query them; <code>where</code> restricts the test to a subset.',
    ])


def scd_join_anim():
    elems = [
        stext(380, 24, 'Joining facts to an SCD2 dimension "as of" the event date', 'blue', 14, bold=True),
        stable(20, 60, ['roll', 'city', 'valid_from', 'valid_to'], [['2402', 'Navi Mumbai', '08-01', '10-12'], ['2402', 'Pune', '10-13', '9999']], [55, 110, 80, 70],
               step=1, title='dim_student_history', title_color='purple'),
        stable(400, 60, ['roll', 'subject', 'exam_date'], [['2402', 'SQL', '09-20'], ['2402', 'Spark', '10-14']], [55, 80, 90], step=2, title='fct_marks', title_color='blue'),
        stext(380, 162, 'join on roll AND exam_date between valid_from and valid_to', 'amber', 12, step=3, focus=3, bold=True),
        stable(180, 202, ['roll', 'subject', 'city at exam time'], [['2402', 'SQL', 'Navi Mumbai'], ['2402', 'Spark', 'Pune']], [70, 90, 150], step=4, title='result', title_color='green'),
    ]
    return anim(canvas(760, 290, *elems), [
        'The snapshot-based dimension holds two versions of student 2402 with validity ranges.',
        'Facts carry the date on which each exam happened.',
        'The join condition includes the date range, so each fact picks the dimension version valid on that date.',
        'The September exam shows Navi Mumbai; the October exam after the move shows Pune: history-correct reporting.',
    ])


def compare_anim():
    elems = [stext(380, 24, 'dbt vs stored procedures vs Spark', 'blue', 15, bold=True)]
    cols = [('Stored procedures', ['procedural SQL scripts', 'manual order & logging', 'tests/docs ad hoc', 'one database'], 'gray'),
            ('dbt', ['declarative SELECT models', 'DAG from ref()', 'tests, docs, CI built in', 'runs on warehouse compute'], 'green'),
            ('Spark (PySpark)', ['code in Python/Scala', 'any data, any source', 'ML, streaming, files', 'needs a cluster & engineers'], 'blue')]
    for i, (t, items, c) in enumerate(cols):
        x = 20 + i * 245
        elems.append(sbox(x, 50, 230, 40, t, '', c, step=i + 1, focus=i + 1, size=13))
        for j, it in enumerate(items):
            elems.append(stext(x + 115, 115 + j * 24, it, PALETTE.get(c, c) if c != 'gray' else '#cbd5e1', 12, step=i + 1))
    elems.append(stext(380, 240, 'common pattern: Spark for heavy ingestion/ML → warehouse → dbt for SQL modelling', 'cyan', 12, step=4, focus=4, bold=True))
    return anim(canvas(760, 260, *elems), [
        'Stored procedures put transformation logic in procedural scripts inside one database, with ordering, testing and documentation handled by hand.',
        'dbt keeps transformations as declarative SELECT models with dependencies, tests, docs and CI, executed by the warehouse.',
        'Spark is a general distributed engine: transformations in code, any data format, machine learning and streaming, at the cost of cluster operations.',
        'They complement each other: many platforms ingest and process raw files with Spark, then model analytics tables with dbt.',
    ])
