from build import *
from dbt.anims import *
from dbt.runner import dfile, dbtrun, yml, sqlc, sh
from dbt.common import STG_STUDENTS, STG_MARKS, STG_COURSES, STAGING

SECTION = dict(level='intermediate', title='Testing & Documentation', questions=[

# ------------------------------------------------------------------ 16
Q('How do you test data in dbt? Explain the built-in generic tests.', 'Generic Data Tests', minutes=9, cards=[
    definition(
        defbox('<strong>Data tests</strong> are assertions about the data in a model, source, seed or snapshot. A test is a SELECT that returns the '
               '<strong>failing rows</strong>; zero rows = pass. Four <strong>generic tests</strong> ship with dbt and are declared in YAML under '
               '<code>data_tests:</code> (older projects use <code>tests:</code>):'),
        table(['Test', 'Checks', 'Example'], [
            ['<code>unique</code>', 'No duplicate values', 'student_id in dim_students'],
            ['<code>not_null</code>', 'No NULLs', 'marks in fct_marks'],
            ['<code>accepted_values</code>', 'Only listed values', 'course_code in (PG-DBDA, PG-DAC, PG-DAI)'],
            ['<code>relationships</code>', 'Every value exists in another model (FK)', 'fct_marks.student_id → dim_students.student_id'],
        ]),
        tags('dbt test', 'data_tests', 'unique', 'not_null', 'accepted_values', 'relationships'),
    ),
    analogy('Tests are the <strong>quality-control checkpoint</strong> on a production line: every batch is checked against a list of rules (no '
            'missing labels, no duplicate serial numbers, only approved colours) before it is shipped to customers (dashboards).'),
    tests_anim(),
    real_world(
        scenario('A test that saved a report',
                 p('A new course "PG-DESD" appeared in the source before the courses seed was updated. The <code>relationships</code> test on '
                   '<code>course_code</code> failed in the morning run, so the course-wise dashboard was not refreshed with students silently '
                   'missing from every total.')),
    ),
    example(
        *[dfile(k, v, show=False) for k, v in STAGING.items()],
        dfile('models/staging/_staging.yml', """
models:
  - name: stg_students
    columns:
      - name: student_id
        data_tests: [unique, not_null]
      - name: course_code
        data_tests:
          - accepted_values:
              arguments:
                values: ['PG-DBDA', 'PG-DAC']
          - relationships:
              arguments:
                to: ref('stg_courses')
                field: course_code
  - name: stg_marks
    columns:
      - name: marks
        data_tests: [not_null]
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt test', allow_fail=True),
        note('<code>accepted_values</code> failed with 1 because the list omitted PG-DAI (one distinct bad value); all other tests passed. '
             'In dbt 1.10+ test parameters go under <code>arguments:</code>.', 'Read the output'),
        title='Example: Four Tests, One Failure'),
    steps(
        ('Add a YAML properties file next to the models', 'e.g. models/staging/_staging.yml.'),
        ('Test every primary key', 'unique + not_null on each model\'s grain.'),
        ('Test foreign keys and categories', 'relationships, accepted_values.'),
        ('Run', '<code>dbt test</code> (or <code>dbt build</code>, which tests each model right after building it).'),
        ('Investigate failures', '<code>dbt test --select test_name --store-failures</code> or run the compiled test SQL.'),
        title='Steps to Add Tests'),
    crossq(
        ('What is the minimum testing you would add to every model?', 'unique and not_null on the primary key (the grain), because duplicated or missing keys break almost every downstream join and count.'),
        ('Do tests run against all data every time?', 'By default yes; on very large tables use <code>where</code> configs or limit tests to recent partitions.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What are singular tests and custom generic tests?', 'Singular & Custom Tests', minutes=8, cards=[
    definition(
        defbox('A <strong>singular test</strong> is a .sql file in <code>tests/</code> with a query returning rows that break a rule; it applies to the '
               'models it refs.',
               'A <strong>custom generic test</strong> is a reusable, parameterised test written with <code>{% test name(model, column_name, ...) %}</code> '
               'in <code>macros/</code> (or <code>tests/generic/</code>) and applied in YAML like built-in tests. Packages such as dbt_utils and '
               'dbt_expectations provide many ready-made ones.'),
        tags('Singular Test', 'Generic Test', '{% test %}', 'dbt_utils', 'dbt_expectations'),
    ),
    analogy('A singular test is a <strong>special inspection</strong> for one product; a custom generic test is a <strong>new inspection tool</strong> '
            'that can be used on any product line once it is in the toolbox.'),
    singular_test_anim(),
    real_world(
        scenario('Business rules as tests',
                 ul('Singular: "total fee collected per course must equal the finance system\'s total".',
                    'Generic: <code>between</code> (0–100) used on marks, attendance %, and quiz scores across 15 models.')),
    ),
    example(
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('tests/assert_no_future_exams.sql', """
-- singular test: exams cannot be dated in the future
select * from {{ ref('stg_marks') }}
where exam_date > current_date
"""),
        dfile('macros/test_between.sql', """
{% test between(model, column_name, lo, hi) %}
select {{ column_name }} as bad_value
from {{ model }}
where {{ column_name }} < {{ lo }} or {{ column_name }} > {{ hi }}
{% endtest %}
"""),
        dfile('models/staging/_staging.yml', """
models:
  - name: stg_marks
    columns:
      - name: marks
        data_tests:
          - between:
              arguments: {lo: 0, hi: 100}
          - between:
              name: marks_at_least_60
              arguments: {lo: 60, hi: 100}
              config: {severity: warn}
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt test'),
        title='Example'),
    steps(
        ('One-off rule?', 'Write a singular test in tests/ that selects bad rows.'),
        ('Rule reused on many columns?', 'Write <code>{% test %}</code> with model and column_name parameters.'),
        ('Apply in YAML', 'Same syntax as built-in tests, with arguments.'),
        ('Check packages first', 'dbt_utils (expression_is_true, unique_combination_of_columns), dbt_expectations.'),
        title='Steps'),
    crossq(
        ('How do you test uniqueness of a combination of columns?', 'dbt_utils.unique_combination_of_columns, or a singular test grouping by the columns HAVING count(*) &gt; 1.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('How do you control test severity and inspect failing rows?', 'Severity & store_failures', minutes=7, cards=[
    definition(
        table(['Config', 'Effect'], [
            ['<code>severity: error | warn</code>', 'Fail the run or just report a warning'],
            ['<code>error_if</code> / <code>warn_if</code>', 'Conditions on the failing-row count, e.g. <code>"&gt;10"</code>'],
            ['<code>store_failures: true</code>', 'Save failing rows to a table (schema <code>&lt;target&gt;_dbt_test__audit</code>)'],
            ['<code>where</code>', 'Test only a subset, e.g. recent rows'],
            ['<code>limit</code>', 'Cap the rows returned by the test query'],
        ]),
        tags('severity', 'warn_if', 'error_if', 'store_failures', 'where', 'Test Config'),
    ),
    analogy('Not every quality issue stops the factory line: a <strong>scratch</strong> gets a note (warn), a <strong>missing brake</strong> stops the '
            'line (error), and defective items are put aside in a <strong>reject bin</strong> for inspection (store_failures).'),
    severity_anim(),
    real_world(
        scenario('Tolerating small noise',
                 p('Attendance devices occasionally send a few rows without a roll number. The not_null test uses <code>warn_if: ">0"</code> and '
                   '<code>error_if: ">100"</code>: a handful of bad rows produce a warning; a broken device sending thousands stops the pipeline.')),
    ),
    example(
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/staging/_staging.yml', """
models:
  - name: stg_marks
    columns:
      - name: marks
        data_tests:
          - accepted_values:
              name: marks_pass_check
              arguments:
                values: [60, 61, 72, 75, 82, 84, 88, 91]
              config:
                severity: error
                warn_if: ">0"
                error_if: ">5"
                store_failures: true
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt test',
               """dbt --quiet show --inline "select * from dev_dbt_test__audit.marks_pass_check" """),
        note('One value (58) failed: 1 is above <code>warn_if</code> but not above <code>error_if</code>, so the test WARNs and the run continues; the '
             'failing row was stored in the audit table.', 'Read the output'),
        title='Example'),
    steps(
        ('Decide which rules are blocking', 'Keys and FKs → error; soft expectations → warn.'),
        ('Add thresholds where noise is normal', 'warn_if / error_if.'),
        ('Store failures for debugging', 'Per test or globally (<code>+store_failures: true</code> under tests:).'),
        ('Review warnings regularly', 'Warnings ignored for months become silent errors.'),
        title='Steps'),
    crossq(
        ('Where do stored failures go?', 'A table per test in a schema suffixed <code>_dbt_test__audit</code> (configurable with <code>schema</code>), overwritten on each run.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What are unit tests in dbt? How are they different from data tests?', 'Unit Tests', minutes=8, cards=[
    definition(
        defbox('<strong>Unit tests</strong> (dbt 1.8+) verify a model\'s <strong>SQL logic</strong> with small, hand-written <strong>input rows</strong> '
               '(<code>given</code>) and the exact <strong>output rows</strong> you expect (<code>expect</code>), without depending on production data. '
               'They are defined in YAML under <code>unit_tests:</code> and run with <code>dbt test</code> or <code>dbt build</code>.',
               '<strong>Data tests</strong> check the real data after it is built; unit tests check the transformation code before it touches real data.'),
        tags('Unit Tests', 'given', 'expect', 'dbt 1.8', 'Test-Driven Development', 'CI'),
    ),
    analogy('Before serving a new curry recipe to the whole hostel (data), the cook tries it with <strong>a measured spoon of each ingredient</strong> '
            '(given) and checks the taste against what the recipe promises (expect). That is a unit test.'),
    unit_test_anim(),
    real_world(
        scenario('Grade boundaries',
                 p('The rule "85 and above is A" was implemented as <code>&gt; 85</code> by mistake. A unit test with a student at exactly 85 '
                   'failed in CI, so the bug never reached the published results.')),
    ),
    example(
        dfile('models/staging/stg_marks.sql', STG_MARKS, show=False),
        dfile('models/marts/fct_grades.sql', """
select
    student_id,
    subject,
    marks,
    case when marks > 85 then 'A'      -- bug: should be >= 85
         when marks >= 70 then 'B'
         else 'C' end as grade
from {{ ref('stg_marks') }}
"""),
        dfile('models/marts/_unit_tests.yml', """
unit_tests:
  - name: grade_boundaries
    model: fct_grades
    given:
      - input: ref('stg_marks')
        rows:
          - {student_id: 1, subject: SQL, marks: 85}
          - {student_id: 2, subject: SQL, marks: 70}
          - {student_id: 3, subject: SQL, marks: 69}
    expect:
      rows:
        - {student_id: 1, grade: A}
        - {student_id: 2, grade: B}
        - {student_id: 3, grade: C}
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt test --select test_type:unit', allow_fail=True),
        title='Example: A Unit Test Catches an Off-by-One Bug'),
    steps(
        ('Pick logic worth testing', 'CASE boundaries, date maths, window functions, deduplication.'),
        ('Write given rows', 'Only the columns the model uses, for each ref/source input.'),
        ('Write expected rows', 'Only the columns you want to assert.'),
        ('Run in CI', '<code>dbt test --select test_type:unit</code>; skip them in production runs (<code>--exclude-resource-type unit_test</code>).'),
        title='Steps to Write a Unit Test'),
    crossq(
        ('Do unit tests need the input tables to exist?', 'dbt needs the upstream relations\' schemas (to cast mock rows), so parent models must exist (or be deferred to prod), but their data is not used.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('How do you document a dbt project? What does dbt docs generate?', 'Documentation', minutes=7, cards=[
    definition(
        defbox('Descriptions for models, columns, sources and seeds are written in YAML (<code>description:</code>), optionally using reusable '
               '<code>{% docs %}</code> blocks in .md files. <code>dbt docs generate</code> combines the project manifest with the warehouse '
               'catalog (actual columns and types) into <code>target/manifest.json</code> and <code>catalog.json</code>; <code>dbt docs serve</code> '
               'opens a website with descriptions, tests, SQL and an interactive <strong>lineage graph</strong>. <code>persist_docs</code> can also '
               'write descriptions into the warehouse as table/column comments.'),
        tags('dbt docs', 'description', '{% docs %}', 'Lineage', 'persist_docs', 'catalog.json'),
    ),
    analogy('The docs site is the <strong>library catalogue</strong> of your warehouse: every table has a card saying what it contains, where its data '
            'comes from, who maintains it and which checks it passes.'),
    docs_anim(),
    real_world(
        scenario('Onboarding new analysts',
                 p('New placement-cell analysts used to ask "which table has the final marks?". Now they search the dbt docs site, read the '
                   'description of <code>fct_marks</code>, see its tests and lineage, and know it is the source of truth.')),
    ),
    example(
        dfile('models/staging/stg_students.sql', STG_STUDENTS, show=False),
        dfile('models/staging/_staging.yml', """
models:
  - name: stg_students
    description: One row per enrolled student, cleaned from the admission system.
    columns:
      - name: student_id
        description: '{{ doc("student_id") }}'
        data_tests: [unique, not_null]
      - name: centre
        description: C-DAC centre where the student attends (Kharghar, Juhu).
"""),
        dfile('models/docs.md', """
{% docs student_id %}
Roll number assigned at admission, e.g. 2401. Unique across all courses
and used as the key in every student-level table.
{% enddocs %}
"""),
        dbtrun('!dbt seed', '!dbt run', 'dbt docs generate',
               """python3 -c "import json; m=json.load(open('target/manifest.json')); n=m['nodes']['model.cdac_dw.stg_students']; print(n['description']); print(n['columns']['student_id']['description'])" """),
        title='Example'),
    steps(
        ('Describe every mart and its key columns', 'At minimum; staging later.'),
        ('Use doc blocks for shared definitions', 'Define "student_id" once, reuse everywhere.'),
        ('Generate and publish', '<code>dbt docs generate</code> in CI; host the static site (S3, GitHub Pages) or use dbt Cloud.'),
        ('Optionally persist to the warehouse', '<code>+persist_docs: {relation: true, columns: true}</code> so BI tools show the comments.'),
        title='Steps to Document a Project'),
    crossq(
        ('Why is dbt documentation more reliable than a wiki?', 'It lives in the same repository as the code, is reviewed in the same pull request, and is generated from the actual project and warehouse, including lineage that cannot go out of date.'),
    ),
]),
])
