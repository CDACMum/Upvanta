from build import *
from dbt.anims import *
from dbt.runner import dfile, dbtrun, yml, sqlc, sh

RUN_NOTE = note('Every example with an Output box was really executed while this page was built: a fresh dbt project per example, '
                'with <strong>dbt-core 1.12</strong> and the <strong>DuckDB</strong> adapter, seeded with sample C-DAC data '
                '(<code>raw_students</code>, <code>raw_marks</code>, <code>raw_courses</code>). Timestamps are removed from the console '
                'output; everything else is exactly what dbt printed.', 'How the examples were run')

STG_STUDENTS = """
select
    roll_no                as student_id,
    trim(name)             as student_name,
    course                 as course_code,
    centre,
    city,
    cast(joined_on as date) as joined_on
from {{ ref('raw_students') }}
"""

SECTION = dict(level='beginner', title='dbt Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is dbt? Why do data teams use it?', 'What is dbt', minutes=8, cards=[
    definition(
        defbox('<strong>dbt (data build tool)</strong> is an open-source command-line tool that lets analysts and engineers '
               '<strong>transform data inside the warehouse by writing SELECT statements</strong>. dbt turns each SELECT (a <strong>model</strong>) '
               'into a view or table, works out the order to build them from their dependencies, and adds <strong>testing, documentation, version '
               'control and CI/CD</strong> practices to SQL work.',
               'dbt handles only the <strong>T</strong> of ELT: data is extracted and loaded by other tools; dbt uses the warehouse\'s own compute '
               '(Snowflake, BigQuery, Databricks, Redshift, Postgres, DuckDB…).'),
        tags('dbt', 'ELT', 'Transformation', 'Analytics Engineering', 'SQL', 'Data Warehouse'),
    ),
    analogy('Before dbt, transformations were like <strong>handwritten recipes on loose sheets</strong>: each cook kept their own copy, nobody knew '
            'which dish depended on which sauce, and mistakes were found by customers. dbt is a <strong>professional kitchen system</strong>: '
            'recipes in one book (Git), each recipe lists its ingredients (ref), dishes are prepared in the right order automatically, and every '
            'dish is tasted (tests) before it leaves the kitchen.'),
    elt_anim(),
    real_world(
        scenario('C-DAC placement analytics',
                 p('Marks, attendance and placement data land in a warehouse every night. Previously, 40 stored procedures and Excel macros built '
                   'the placement report; nobody knew the order or what broke when a column changed. In dbt, each step is a model in Git, '
                   '<code>dbt build</code> runs them in order, tests check roll numbers and marks ranges, and the generated docs show exactly where '
                   'each report column comes from.')),
        scenario('Industry',
                 p('dbt is used by thousands of companies (JetBlue, HubSpot, Siemens…) and created the "analytics engineer" role: people who '
                   'apply software-engineering practices to SQL transformations.')),
    ),
    example(
        RUN_NOTE,
        dfile('models/staging/stg_students.sql', STG_STUDENTS),
        dfile('models/marts/course_summary.sql', """
select
    course_code,
    count(*)                         as students,
    count(distinct city)             as cities
from {{ ref('stg_students') }}
group by course_code
order by students desc
"""),
        dbtrun('!dbt seed', 'dbt run', 'dbt show --select course_summary'),
        title='Example: Two Models, One Command'),
    steps(
        ('Install dbt with an adapter', '<code>pip install dbt-core dbt-duckdb</code> (or dbt-snowflake, dbt-bigquery…).'),
        ('Create a project', '<code>dbt init cdac_dw</code> and configure the connection in <code>~/.dbt/profiles.yml</code>.'),
        ('Check the connection', '<code>dbt debug</code>.'),
        ('Write a model', 'A .sql file with a SELECT in <code>models/</code>; use <code>ref()</code> for other models.'),
        ('Build and test', '<code>dbt build</code>; then <code>dbt docs generate &amp;&amp; dbt docs serve</code>.'),
        title='Steps to Start a dbt Project'),
    crossq(
        ('Is dbt an ETL tool?', 'Only the T. It does not extract or load data and does not process data on its own servers; it generates SQL that the warehouse executes.'),
        ('What skills does dbt need?', 'SQL first, then a little Jinja (templating), YAML for configuration, and Git. No Python is required (Python models exist for some adapters).'),
        ('Why not just use stored procedures?', 'dbt adds dependency management, modular reusable models, version control, automated tests, documentation, environments (dev/prod) and CI, which stored procedures lack or do ad hoc.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('What is the difference between dbt Core and dbt Cloud? What are adapters?', 'dbt Core vs Cloud & Adapters', minutes=7, cards=[
    comparison(
        table(['Aspect', 'dbt Core', 'dbt Cloud'], [
            ['What', 'Open-source CLI (Apache 2.0)', 'Managed SaaS by dbt Labs, built on the same engine'],
            ['Development', 'Your editor (VS Code) + terminal', 'Browser IDE or Cloud CLI'],
            ['Scheduling', 'You bring Airflow, cron, GitHub Actions…', 'Built-in jobs, triggers, CI on pull requests'],
            ['Docs & lineage', 'Generate and host yourself', 'Hosted docs, dbt Explorer'],
            ['Extras', '—', 'Semantic Layer APIs, cross-project refs (Mesh), alerts, SSO'],
            ['Cost', 'Free', 'Per-seat / usage pricing'],
        ]),
        defbox('An <strong>adapter</strong> is a plugin that teaches dbt how to connect to a particular platform and generate its SQL dialect '
               '(dbt-snowflake, dbt-bigquery, dbt-databricks, dbt-redshift, dbt-postgres, dbt-spark, dbt-duckdb…). The project code stays mostly the same.'),
        tags('dbt Core', 'dbt Cloud', 'Adapter', 'dbt-duckdb', 'dbt-snowflake', 'Open Source'),
    ),
    analogy('dbt Core is a <strong>car engine</strong> you install in your own vehicle and maintain yourself; dbt Cloud is a <strong>taxi service</strong> '
            'using the same engine, with a driver, maintenance and booking app included. Adapters are the <strong>fittings</strong> that let the '
            'engine work with different car models (warehouses).'),
    core_cloud_anim(),
    real_world(
        scenario('Choosing for the institute',
                 p('The training lab uses dbt Core with DuckDB on student laptops (free, works offline). A company running Snowflake with 30 analysts '
                   'chose dbt Cloud for the IDE, managed scheduling and CI; another with an existing Airflow platform runs dbt Core inside Airflow.')),
    ),
    example(
        dbtrun('dbt --version'),
        sh('''
pip install dbt-core dbt-duckdb        # local / training
pip install dbt-core dbt-snowflake     # Snowflake
pip install dbt-core dbt-bigquery      # BigQuery
pip install dbt-core dbt-databricks    # Databricks
''', 'Installing adapters'),
        title='Example'),
    steps(
        ('Pick the adapter for your platform', 'Install it alongside dbt-core in a virtual environment.'),
        ('Decide Core or Cloud', 'Existing orchestration and DevOps skills → Core; want managed IDE/scheduling → Cloud.'),
        ('Pin versions', 'In requirements.txt and <code>require-dbt-version</code> in dbt_project.yml.'),
        title='Steps'),
    crossq(
        ('Can the same project run on Core and Cloud?', 'Yes. The project files are identical; only where it runs and how it is scheduled differ.'),
        ('Is SQL portable across adapters?', 'Mostly, but functions differ by platform. Cross-database macros (<code>dbt.dateadd</code>, <code>dbt.concat</code>…) and dispatch help keep code portable.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('Explain the structure of a dbt project and the dbt_project.yml file.', 'Project Structure', minutes=8, cards=[
    definition(
        table(['Folder / file', 'Contains'], [
            ['<code>dbt_project.yml</code>', 'Project name, profile name, folder paths, default configs for models/seeds/snapshots, vars'],
            ['<code>models/</code>', 'SQL (and Python) models + YAML property files (tests, docs, sources)'],
            ['<code>seeds/</code>', 'CSV files loaded with <code>dbt seed</code>'],
            ['<code>snapshots/</code>', 'Snapshot definitions (history of changing rows)'],
            ['<code>tests/</code>', 'Singular data tests (.sql)'],
            ['<code>macros/</code>', 'Jinja macros, custom generic tests'],
            ['<code>analyses/</code>', 'SQL compiled but not run (ad-hoc analysis kept in Git)'],
            ['<code>target/</code>, <code>logs/</code>, <code>dbt_packages/</code>', 'Generated; excluded from Git'],
        ]),
        tags('dbt_project.yml', 'models', 'seeds', 'snapshots', 'macros', 'tests', 'target'),
    ),
    analogy('A dbt project is like a <strong>school timetable binder</strong>: the cover page (dbt_project.yml) says which school and which rules apply to '
            'each section; tabs separate lessons (models), reference charts (seeds), exam papers (tests) and reusable worksheets (macros).'),
    project_tree_anim(),
    real_world(
        scenario('Organising models by layer',
                 p('In <code>dbt_project.yml</code>, everything under <code>models/staging</code> is a view and everything under <code>models/marts</code> '
                   'is a table in a separate schema, so individual models rarely need their own config.')),
    ),
    example(
        dfile('dbt_project.yml', """
name: cdac_dw
version: '1.0'
profile: cdac

model-paths: ["models"]
seed-paths: ["seeds"]

seeds:
  cdac_dw:
    +schema: raw

models:
  cdac_dw:
    staging:
      +materialized: view
    marts:
      +materialized: table
"""),
        dfile('models/staging/stg_students.sql', STG_STUDENTS, show=False),
        dfile('models/marts/dim_students.sql', "select * from {{ ref('stg_students') }}", show=False),
        dbtrun('!dbt seed', 'dbt run', 'dbt --quiet ls --select config.materialized:table', 'dbt --quiet ls --select config.materialized:view'),
        title='Example: Folder-Level Configuration'),
    steps(
        ('Create the skeleton', '<code>dbt init cdac_dw</code> creates the folders and a sample dbt_project.yml.'),
        ('Set the profile name', 'Must match an entry in profiles.yml.'),
        ('Organise models into folders', 'staging/, intermediate/, marts/ (by business area).'),
        ('Set folder defaults', '<code>+materialized</code>, <code>+schema</code>, <code>+tags</code> under <code>models:</code>.'),
        ('Add .gitignore', 'target/, dbt_packages/, logs/.'),
        title='Steps to Organise a Project'),
    crossq(
        ('What does the + prefix in dbt_project.yml mean?', 'It marks a config (like <code>+materialized</code>) as opposed to a folder name, avoiding ambiguity when a folder is called "schema" or "tags".'),
        ('What goes in analyses/?', 'SQL you want templated and versioned but not materialised, e.g. one-off audit queries; <code>dbt compile</code> renders them.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What is profiles.yml? What are targets and how do dev and prod environments work?', 'Profiles & Targets', minutes=7, cards=[
    definition(
        defbox('<code>profiles.yml</code> (by default in <code>~/.dbt/</code>, outside the project) holds <strong>connection details</strong>. A profile '
               'contains one or more <strong>targets</strong> (e.g. dev, prod), each with its own database, schema, credentials and thread count.',
               'The project\'s <code>profile:</code> setting picks the profile; <code>target:</code> in the profile is the default and '
               '<code>--target prod</code> overrides it. Inside Jinja, <code>target.name</code>, <code>target.schema</code> etc. are available.'),
        tags('profiles.yml', 'Target', 'dev', 'prod', 'Environment', 'env_var', 'threads'),
    ),
    analogy('The project is a <strong>play script</strong>; targets are <strong>stages</strong>. You rehearse on the practice stage (dev schema) and '
            'perform on the main stage (prod). Same script, different venue.'),
    profiles_anim(),
    real_world(
        scenario('Safe development',
                 p('Each analyst\'s dev target writes to <code>dbt_&lt;name&gt;</code>. The production job in Airflow runs '
                   '<code>dbt build --target prod</code> with a service account whose password comes from <code>env_var(\'DBT_PROD_PASSWORD\')</code>.')),
    ),
    example(
        yml('''
# ~/.dbt/profiles.yml
cdac:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: cdac.duckdb
      schema: dev
      threads: 1
    prod:
      type: snowflake
      account: xy12345.ap-south-1
      user: DBT_PROD
      password: "{{ env_var('DBT_PROD_PASSWORD') }}"
      role: TRANSFORMER
      warehouse: TRANSFORM_WH
      database: ANALYTICS
      schema: marts
      threads: 8
''', 'profiles.yml'),
        dfile('models/whoami.sql', """
select '{{ target.name }}' as target_name, '{{ target.schema }}' as target_schema
"""),
        dbtrun('dbt --quiet show --select whoami', 'dbt --quiet show --select whoami --target prod'),
        note('The examples on this page use two DuckDB targets, dev and prod, with schemas <code>dev</code> and <code>prod</code>.', 'Note'),
        title='Example'),
    steps(
        ('Create profiles.yml', '<code>dbt init</code> prompts for it, or write it by hand in <code>~/.dbt/</code>.'),
        ('Add a dev target', 'Personal schema, few threads.'),
        ('Add a prod target', 'Service account; secrets via <code>env_var()</code>, never committed.'),
        ('Verify', '<code>dbt debug --target prod</code>.'),
        ('Use in code sparingly', 'e.g. <code>{% if target.name == \'dev\' %} limit 1000 {% endif %}</code> to keep dev runs cheap.'),
        title='Steps to Configure Environments'),
    crossq(
        ('Why is profiles.yml not inside the project?', 'It contains credentials and differs per person/environment; keeping it outside avoids committing secrets. (DBT_PROFILES_DIR can point elsewhere.)'),
        ('What do threads control?', 'How many models dbt builds in parallel, limited by the DAG and the warehouse\'s capacity.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What happens internally when you run dbt run? What is compilation?', 'How dbt Runs', minutes=8, cards=[
    definition(
        defbox('<code>dbt run</code> <strong>parses</strong> the project, <strong>compiles</strong> each model by rendering Jinja into plain SQL '
               '(<code>ref()</code> → real relation names), builds the <strong>DAG</strong> from the refs, then <strong>executes</strong> models in '
               'dependency order, wrapping each SELECT in the DDL/DML of its materialization. Results go to <code>target/</code>.',
               '<code>dbt compile</code> does everything except execution, which is useful to inspect generated SQL.'),
        tags('dbt run', 'dbt compile', 'Jinja', 'DAG', 'Parsing', 'target folder'),
    ),
    analogy('Like a <strong>mail-merge</strong>: the template letter (model with Jinja) is filled in with real names and addresses (compiled SQL), '
            'letters are sorted by route (DAG), then delivered (executed) one route after another.'),
    run_flow_anim(),
    real_world(
        scenario('Debugging a Jinja-heavy model',
                 p('A model built with loops produced wrong column names. Running <code>dbt compile --select model</code> and reading the rendered SQL '
                   'showed a missing comma from the loop, without touching the warehouse.')),
    ),
    example(
        dfile('models/staging/stg_students.sql', STG_STUDENTS, show=False),
        dfile('models/marts/kharghar_students.sql', """
select student_id, student_name, course_code
from {{ ref('stg_students') }}
where centre = 'Kharghar'
"""),
        dbtrun('!dbt seed', 'dbt compile --select kharghar_students', 'dbt run --select +kharghar_students'),
        title='Example: Compile, Then Run'),
    steps(
        ('Write models with ref()', 'Never hard-code schema names.'),
        ('Compile to check', '<code>dbt compile --select model</code> and read <code>target/compiled/…</code>.'),
        ('Run', '<code>dbt run</code> (all) or <code>--select</code> a subset.'),
        ('Inspect results', 'Console summary, <code>target/run_results.json</code>, <code>logs/dbt.log</code>.'),
        title='Steps'),
    crossq(
        ('Why does dbt run models in parallel only sometimes?', 'Parallelism is limited by dependencies: a model starts only when all its parents finished, and by the <code>threads</code> setting.'),
        ('What is partial parsing?', 'dbt caches the parsed project (<code>target/partial_parse.msgpack</code>) and re-parses only changed files, speeding up commands in large projects.'),
    ),
]),
])
