from build import *
from dbt.anims import *
from dbt.runner import dfile, dbtrun, yml, sqlc, sh
from dbt.common import STG_STUDENTS, STG_MARKS, STG_COURSES, STAGING

SECTION = dict(level='advanced', title='Jinja, Macros, Variables & Packages', questions=[

# ------------------------------------------------------------------ 21
Q('How is Jinja used in dbt? Give examples of loops and conditions.', 'Jinja in dbt', minutes=9, cards=[
    definition(
        defbox('dbt renders every model with <strong>Jinja</strong>, a Python templating language, before sending SQL to the warehouse. '
               '<code>{{ ... }}</code> outputs a value (ref, source, var, macro calls); <code>{% ... %}</code> runs statements '
               '(<code>set</code>, <code>if</code>, <code>for</code>, <code>macro</code>); <code>{# ... #}</code> is a comment. Jinja lets you '
               'generate repetitive SQL, switch logic by environment, and query the database at compile time (<code>run_query</code>).'),
        tags('Jinja', '{{ }}', '{% %}', 'for loop', 'if', 'set', 'run_query'),
    ),
    analogy('Jinja is a <strong>form letter with blanks and instructions</strong>: "for each subject, add a column…", "if this is the practice run, '
            'only use 100 students". dbt fills it in and hands the finished letter (plain SQL) to the warehouse.'),
    jinja_anim(),
    real_world(
        scenario('Pivoting subjects into columns',
                 p('The report card needs one column per subject. Instead of typing a CASE expression for each subject (and editing it every time a '
                   'subject is added), a Jinja loop generates them from a list, or from a query of distinct subjects at compile time.')),
    ),
    example(
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/report_card.sql', """
{% set subjects = ['SQL', 'Spark', 'Java', 'ML'] %}

select
    student_id,
    {% for s in subjects %}
    max(case when subject = '{{ s }}' then marks end) as {{ s | lower }}_marks{{ "," if not loop.last }}
    {% endfor %}
from {{ ref('stg_marks') }}
{% if target.name == 'dev' %}
where student_id < 2405   -- smaller data while developing
{% endif %}
group by student_id
order by student_id
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt --quiet compile --select report_card', 'dbt --quiet show --select report_card'),
        title='Example: A Loop and a Condition'),
    steps(
        ('Write the SQL for one case by hand', 'Make sure it is correct first.'),
        ('Replace repetition with a loop', '<code>{% for x in list %} … {% endfor %}</code>; use <code>loop.last</code> for commas.'),
        ('Add conditions sparingly', 'Environment-specific tweaks with <code>target.name</code>.'),
        ('Compile and read the output', '<code>dbt compile --select model</code>; whitespace control with <code>{%- -%}</code>.'),
        ('Move reusable pieces into macros', 'When the same Jinja appears in several models.'),
        title='Steps to Use Jinja Well'),
    crossq(
        ('When does Jinja run: in the warehouse or before?', 'Before. Jinja is rendered by dbt on your machine/runner at compile time; the warehouse only sees the resulting SQL.'),
        ('What is the risk of too much Jinja?', 'Models become hard to read and debug. Prefer readable SQL; use Jinja for genuine repetition and environment logic.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What are macros in dbt? How do you write and use one?', 'Macros', minutes=8, cards=[
    definition(
        defbox('A <strong>macro</strong> is a reusable Jinja function defined with <code>{% macro name(args) %} … {% endmacro %}</code> in the '
               '<code>macros/</code> folder. Calling <code>{{ name(args) }}</code> in a model inserts the generated SQL. Macros are used for repeated '
               'expressions, cross-database SQL, custom tests and materializations, and admin operations run with '
               '<code>dbt run-operation macro_name --args \'{...}\'</code>.'),
        tags('Macro', '{% macro %}', 'run-operation', 'DRY', 'Reusable SQL'),
    ),
    analogy('A macro is a <strong>rubber stamp</strong>: carve the design once ("grade from marks"), then stamp it on every form that needs it. '
            'Change the stamp and every new form gets the new design.'),
    macro_anim(),
    real_world(
        scenario('One grading rule for all exams',
                 p('Module exams, mock tests and the final exam all assign grades. A <code>grade()</code> macro holds the boundaries; when the academic '
                   'council changed the B boundary from 70 to 65, one line changed and every model followed.')),
    ),
    example(
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('macros/grade.sql', """
{% macro grade(col) -%}
    case when {{ col }} >= 85 then 'A'
         when {{ col }} >= 70 then 'B'
         when {{ col }} >= 60 then 'C'
         else 'F' end
{%- endmacro %}
"""),
        dfile('macros/count_rows.sql', """
{% macro count_rows(model_name) %}
    {% set result = run_query("select count(*) from " ~ ref(model_name)) %}
    {% do log(model_name ~ " has " ~ result.columns[0].values()[0] ~ " rows", info=True) %}
{% endmacro %}
"""),
        dfile('models/marts/fct_grades.sql', """
select student_id, subject, marks, {{ grade('marks') }} as grade
from {{ ref('stg_marks') }}
order by student_id, subject
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt --quiet show --select fct_grades --limit 4',
               """dbt run-operation count_rows --args '{model_name: fct_grades}'"""),
        title='Example'),
    steps(
        ('Spot repeated SQL', 'The same CASE or calculation in several models.'),
        ('Create macros/name.sql', 'With parameters for what varies.'),
        ('Call it in models', '<code>{{ grade(\'marks\') }}</code>.'),
        ('Compile to verify', 'Check the generated SQL.'),
        ('For admin tasks', '<code>dbt run-operation</code> (grants, cleanup of old dev schemas).'),
        title='Steps to Create a Macro'),
    crossq(
        ('Macro vs ephemeral model?', 'A macro generates an SQL expression/fragment with parameters; an ephemeral model is a whole SELECT inlined as a CTE. Use a macro for reusable expressions, an ephemeral model for a reusable dataset.'),
        ('What does adapter.dispatch do?', 'Lets a macro have different implementations per warehouse (e.g. date functions), so packages work across adapters.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How do you use variables (var) and environment variables in dbt?', 'var() & env_var()', minutes=7, cards=[
    definition(
        defbox('<strong>Project variables</strong> are defined under <code>vars:</code> in <code>dbt_project.yml</code> and read with '
               '<code>{{ var(\'name\', default) }}</code>. They can be overridden per run: <code>dbt run --vars \'{name: value}\'</code>. '
               '<strong>Environment variables</strong> are read with <code>{{ env_var(\'NAME\', \'default\') }}</code>, typically for credentials '
               '(in profiles.yml) and environment-specific settings. Names starting with <code>DBT_ENV_SECRET_</code> are masked in logs.'),
        tags('var', 'env_var', '--vars', 'dbt_project.yml', 'Secrets', 'Parameterisation'),
    ),
    analogy('Variables are the <strong>dials on a machine</strong>: the default setting is printed on the panel (dbt_project.yml), and the operator can '
            'turn a dial for one run (--vars) without rebuilding the machine.'),
    vars_anim(),
    real_world(
        scenario('Back-filling a date range',
                 p('An Airflow back-fill task runs <code>dbt run --select fct_attendance --vars \'{start_date: 2026-09-01, end_date: 2026-09-30}\'</code>; the '
                   'model filters on those variables. The nightly run uses the defaults (yesterday).')),
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
  pass_marks: 60
"""),
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/pass_summary.sql', """
select
    {{ var('pass_marks') }}                                         as pass_mark,
    '{{ env_var('CENTRE_NAME', 'all centres') }}'                     as centre_label,
    sum(case when marks >= {{ var('pass_marks') }} then 1 else 0 end) as passed,
    count(*)                                                          as attempts
from {{ ref('stg_marks') }}
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt --quiet show --select pass_summary',
               """dbt --quiet show --select pass_summary --vars '{pass_marks: 80}'""",
               'CENTRE_NAME=Kharghar dbt --quiet show --select pass_summary'),
        title='Example'),
    steps(
        ('Define defaults', 'Under <code>vars:</code> in dbt_project.yml (can be scoped to a package).'),
        ('Read them', '<code>var(\'name\')</code>; provide a default argument for optional vars.'),
        ('Override per run', '<code>--vars \'{key: value}\'</code> (YAML/JSON string).'),
        ('Use env_var for secrets and environment config', 'Set them in the scheduler/CI, never commit them.'),
        title='Steps'),
    crossq(
        ('var vs env_var?', 'var is project configuration, overridable on the command line and visible in code; env_var reads the process environment, used mainly for credentials and deployment-specific values.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('What are hooks and operations in dbt?', 'Hooks & Operations', minutes=7, cards=[
    definition(
        table(['Hook', 'Runs', 'Typical use'], [
            ['<code>pre-hook</code>', 'Before a model is built', 'Session settings, temporary objects'],
            ['<code>post-hook</code>', 'After a model is built', 'GRANT SELECT, analyze, audit insert'],
            ['<code>on-run-start</code>', 'Once at the start of dbt run/build/…', 'Create audit/log tables'],
            ['<code>on-run-end</code>', 'Once at the end (has access to <code>results</code>)', 'Grants on schemas, logging run results, notifications'],
        ]),
        defbox('<strong>Operations</strong> are macros executed on their own with <code>dbt run-operation</code>. The <code>grants</code> config is the '
               'modern, declarative alternative to GRANT hooks.'),
        tags('pre-hook', 'post-hook', 'on-run-start', 'on-run-end', 'run-operation', 'grants'),
    ),
    analogy('Hooks are the <strong>routines around a lecture</strong>: before class (pre-hook) the projector is switched on; after class (post-hook) '
            'the attendance sheet is submitted; at the start and end of the day (on-run-start/end) the building is opened and the day\'s log is filed.'),
    hooks_anim(),
    real_world(
        scenario('Audit trail',
                 p('Every production model writes a row to <code>audit.model_runs</code> through a post-hook (model name, row count, timestamp), and '
                   'on-run-end records the overall run status, giving the team a history of loads independent of the scheduler\'s logs.')),
    ),
    example(
        dfile('dbt_project.yml', """
name: cdac_dw
version: '1.0'
profile: cdac
seeds:
  cdac_dw:
    +schema: raw
on-run-start:
  - "create table if not exists {{ target.schema }}_audit_log (model varchar, row_count integer, logged_at timestamp)"
models:
  cdac_dw:
    marts:
      +materialized: table
      +post-hook:
        - "insert into {{ target.schema }}_audit_log select '{{ this.name }}', count(*), current_timestamp from {{ this }}"
"""),
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/subject_summary.sql', "select subject, count(*) as n from {{ ref('stg_marks') }} group by 1", show=False),
        dfile('models/marts/student_summary.sql', "select student_id, avg(marks) as avg_marks from {{ ref('stg_marks') }} group by 1", show=False),
        dbtrun('!dbt seed', 'dbt run', """dbt --quiet show --inline "select model, row_count from dev_audit_log order by model" """),
        title='Example: Audit Logging With Hooks'),
    steps(
        ('Decide the scope', 'Per model (pre/post-hook) or per run (on-run-start/end).'),
        ('Write the SQL', 'Use <code>{{ this }}</code> for the current model, <code>{{ target }}</code> for environment.'),
        ('Configure', 'In dbt_project.yml for folders or in the model config.'),
        ('Prefer native configs when available', '<code>grants:</code> instead of GRANT hooks.'),
        title='Steps'),
    crossq(
        ('Are hooks part of the model\'s transaction?', 'On transactional warehouses hooks run inside the model\'s transaction by default; <code>before_begin</code>/<code>after_commit</code> helpers run them outside.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What are dbt packages? How do you install and use them?', 'Packages', minutes=7, cards=[
    definition(
        defbox('A <strong>package</strong> is a dbt project you depend on: its macros, tests and models become available in yours. Dependencies are listed '
               'in <code>packages.yml</code> (or <code>dependencies.yml</code>) from the dbt Hub, Git, or a local path; <code>dbt deps</code> installs '
               'them into <code>dbt_packages/</code>. Popular: <strong>dbt_utils</strong> (surrogate keys, date spine, pivot, tests), '
               '<strong>dbt_expectations</strong>, <strong>codegen</strong>, <strong>audit_helper</strong>.'),
        tags('Packages', 'packages.yml', 'dbt deps', 'dbt_utils', 'dbt Hub', 'codegen'),
    ),
    analogy('Packages are like <strong>apps on a phone</strong>: instead of building a calculator yourself, you install a well-tested one (dbt_utils) and '
            'call its functions.'),
    packages_anim(),
    real_world(
        scenario('A shared internal package',
                 p('C-DAC centres run separate dbt projects but share rules (grading, roll-number formats, attendance %). Those macros live in an '
                   'internal package in Git, pinned by version in each centre\'s packages.yml.')),
    ),
    example(
        yml('''
# packages.yml (typical, from the dbt Hub)
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.3.0", "<2.0.0"]
  - git: "https://github.com/cdac-mumbai/dbt-common.git"
    revision: v1.2.0
''', 'packages.yml (Hub and Git)'),
        sqlc('''
select
    {{ dbt_utils.generate_surrogate_key(['student_id', 'subject']) }} as mark_key,
    *
from {{ ref('stg_marks') }}
''', 'Using dbt_utils'),
        p('The page-build environment has no internet access to the dbt Hub, so the runnable example below installs a <strong>local</strong> package, '
          'which uses exactly the same mechanism:'),
        dfile('packages.yml', """
packages:
  - local: ../cdac_common
"""),
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/fct_marks.sql', """
select {{ cdac_common.mark_key('student_id', 'subject') }} as mark_key, student_id, subject, marks
from {{ ref('stg_marks') }}
"""),
        dbtrun("!mkdir -p ../cdac_common/macros && printf \"name: cdac_common\\nversion: '1.0'\\n\" > ../cdac_common/dbt_project.yml && printf \"{%% macro mark_key(a, b) %%} md5(cast({{ a }} as varchar) || '-' || {{ b }}) {%% endmacro %%}\\n\" > ../cdac_common/macros/mark_key.sql",
               'dbt deps', '!dbt seed', '!dbt run', 'dbt --quiet show --select fct_marks --limit 3'),
        title='Example'),
    steps(
        ('Find a package', 'hub.getdbt.com.'),
        ('Add it to packages.yml with a version range', 'Pin versions for reproducible builds.'),
        ('Install', '<code>dbt deps</code> (in CI too, before build).'),
        ('Call its macros/tests', 'With the package prefix: <code>dbt_utils.star()</code>.'),
        ('Upgrade deliberately', 'Read release notes; test in CI.'),
        title='Steps to Use a Package'),
    crossq(
        ('Should dbt_packages/ be committed?', 'No. It is installed by <code>dbt deps</code>; commit packages.yml and the lock file (package-lock.yml) instead.'),
    ),
]),
])
