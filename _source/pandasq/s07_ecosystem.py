from build import *
from pandasq.anims import *
from pandasq.runner import pdrun, pyshow
from pandasq.data import STUDENTS, MARKS, BOTH, data_note

S = 'Python (pandas) · uses sample data'

SECTION = dict(level='advanced', title='I/O, SQL & Ecosystem', questions=[

# ------------------------------------------------------------------ 31
Q('How do you read and write CSV, Excel, Parquet, JSON and SQL tables? Which format should you use?', 'File Formats & Databases', minutes=8, cards=[
    definition(
        defbox('Each format has a reader and a writer: <code>read_csv</code>/<code>to_csv</code>, <code>read_excel</code>/<code>to_excel</code> '
               '(openpyxl), <code>read_json</code>/<code>to_json</code>, <code>read_parquet</code>/<code>to_parquet</code> (pyarrow), '
               '<code>read_sql</code>/<code>to_sql</code> (SQLAlchemy engine or a sqlite3 connection).',
               '<strong>CSV</strong>: universal, untyped, slow. <strong>Excel</strong>: for business users, multiple sheets. <strong>JSON</strong>: APIs, '
               'nested records (<code>pd.json_normalize</code> flattens). <strong>Parquet</strong>: columnar, compressed, typed, fastest for analytics. '
               '<strong>SQL</strong>: shared, queryable storage.'),
        tags('to_parquet', 'to_excel', 'to_sql', 'read_sql', 'json_normalize', 'I/O'),
    ),
    analogy('CSV is a <strong>photocopy</strong>: anyone can read it, but it loses the formatting. Parquet is a <strong>sealed, labelled, vacuum-packed '
            'box</strong>: smaller, keeps everything intact, and you can open just one compartment. A database is the <strong>shared cupboard</strong> '
            'everyone in the office uses.'),
    formats_anim(),
    real_world(
        scenario('Weekly result pipeline',
                 p('Faculty upload Excel sheets → pandas reads every sheet (<code>sheet_name=None</code>) → cleaned data saved as Parquet for analysis → '
                   'final results written to the MySQL results table with <code>to_sql(if_exists="append")</code> → a formatted Excel summary goes '
                   'to the coordinator.')),
    ),
    example(
        data_note('marks'),
        pdrun("""
            import os, sqlite3
            df = marks.copy()
            df.to_csv('marks.csv', index=False)
            df.to_parquet('marks.parquet', index=False)
            df.to_json('marks.json', orient='records')
            with pd.ExcelWriter('marks.xlsx') as xw:
                df.to_excel(xw, sheet_name='Marks', index=False)
                df.groupby('subject', as_index=False)['marks'].mean().to_excel(xw, sheet_name='Summary', index=False)

            for f in ['marks.csv', 'marks.parquet', 'marks.json', 'marks.xlsx']:
                print(f'{f:14}', os.path.getsize(f), 'bytes')
            print(pd.read_excel('marks.xlsx', sheet_name=None).keys())
            print(pd.read_json('marks.json').head(2))

            con = sqlite3.connect('cdac.db')
            df.to_sql('marks', con, index=False, if_exists='replace')
            print(pd.read_sql('SELECT subject, ROUND(AVG(marks), 1) AS avg FROM marks GROUP BY subject ORDER BY avg DESC', con))

            nested = [{'roll_no': 2401, 'contact': {'city': 'Pune', 'email': 'anuj@cdac.in'}}]
            print(pd.json_normalize(nested))
        """, setup=MARKS, title=S),
        title='Example: Every Format, a Two-Sheet Excel File, SQLite, Nested JSON'),
    steps(
        ('Install the engines', '<code>pip install pyarrow openpyxl sqlalchemy</code> (plus a DB driver such as pymysql).'),
        ('Write without the index', '<code>index=False</code> unless the index carries meaning.'),
        ('Excel with several sheets', '<code>pd.ExcelWriter</code> as a context manager.'),
        ('Databases', '<code>engine = sqlalchemy.create_engine("mysql+pymysql://user:pw@host/db")</code>, then <code>to_sql</code>/<code>read_sql</code>; <code>chunksize</code> for big tables.'),
        ('Pipelines', 'Store intermediate data as Parquet.'),
        title='Steps for Reading and Writing'),
    crossq(
        ('Why is the Parquet file not smaller here?', 'For a 9-row table the fixed metadata dominates; on real data (thousands+ rows) Parquet is typically several times smaller than CSV.'),
        ('What does if_exists do in to_sql?', '"fail" (default), "replace" (drop and recreate), "append".'),
        ('How do you avoid SQL injection with read_sql?', 'Pass parameters with <code>params=</code> instead of formatting values into the query string.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('How do common SQL queries translate to pandas?', 'SQL vs pandas', minutes=8, cards=[
    definition(
        defbox('Most SQL clauses have a direct pandas equivalent: SELECT → column list, WHERE → boolean mask / query, GROUP BY → groupby, HAVING → filter on '
               'groups, ORDER BY → sort_values, LIMIT → head, JOIN → merge, UNION ALL → concat, DISTINCT → drop_duplicates, window functions → groupby '
               'with transform/rank/shift/cumcount.',
               'Key difference: SQL is <strong>declarative</strong> (the database optimises the whole query); pandas is <strong>eager</strong> (each step runs '
               'immediately, in the order written) and works in memory.'),
        tags('SQL', 'GROUP BY', 'HAVING', 'window functions', 'pandasql', 'DuckDB'),
    ),
    analogy('SQL is <strong>ordering in a restaurant</strong>: you say what dish you want and the kitchen decides how. pandas is <strong>cooking at home</strong>: '
            'you do every step yourself, in order, so the order you choose (filter before join) changes how long it takes.'),
    sql_map_anim(),
    real_world(
        scenario('Same question both ways',
                 p('"For each course, students with an average above 75, highest first": a GROUP BY … HAVING … ORDER BY query in MySQL, or a groupby-agg-'
                   'filter-sort chain in pandas. Interviewers often give the SQL and ask for the pandas (or the reverse).')),
    ),
    example(
        data_note('students', 'marks'),
        pdrun("""
            import sqlite3
            con = sqlite3.connect(':memory:')
            students.to_sql('students', con, index=False)
            marks.to_sql('marks', con, index=False)

            sql = '''
            SELECT s.course, s.name, ROUND(AVG(m.marks), 1) AS avg_marks
            FROM marks m JOIN students s ON s.roll_no = m.roll_no
            GROUP BY s.course, s.name
            HAVING AVG(m.marks) > 70
            ORDER BY avg_marks DESC
            '''
            print(pd.read_sql(sql, con))
            print()

            pandas_way = (marks.merge(students, on='roll_no')
                               .groupby(['course', 'name'], as_index=False)
                               .agg(avg_marks=('marks', 'mean'))
                               .query('avg_marks > 70')
                               .sort_values('avg_marks', ascending=False)
                               .round({'avg_marks': 1})
                               .reset_index(drop=True))
            print(pandas_way)
        """, setup=BOTH, title=S),
        title='Example: One Question in SQL and in pandas (Same Answer)'),
    steps(
        ('Start with FROM/JOIN', 'merge the tables.'),
        ('WHERE', 'filter rows before grouping (cheaper).'),
        ('GROUP BY + aggregates', 'groupby + named agg.'),
        ('HAVING', 'filter the aggregated result (query on the new column).'),
        ('ORDER BY / LIMIT', 'sort_values / head.'),
        title='Steps to Translate a Query'),
    crossq(
        ('How do you do COUNT(DISTINCT x)?', '<code>groupby(key)["x"].nunique()</code>.'),
        ('How do you do a CASE WHEN?', '<code>np.select</code> or <code>np.where</code> (or pd.cut for ranges).'),
        ('Can I run SQL directly on DataFrames?', 'Yes, with DuckDB: <code>duckdb.sql("SELECT ... FROM df").df()</code> queries a DataFrame in memory; or load into sqlite as shown.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('How does pandas compare with Polars, Dask and PySpark? When would you switch?', 'pandas vs Polars vs Dask vs Spark', minutes=8, cards=[
    definition(
        defbox('<strong>pandas</strong>: eager, in-memory, single machine, mostly single-threaded; the richest ecosystem.',
               '<strong>Polars</strong>: DataFrame library in Rust with an expression API, multi-threaded, <strong>lazy</strong> mode with a query optimiser, '
               'streaming for larger-than-memory data, built on Arrow.',
               '<strong>Dask</strong>: parallel pandas: a big DataFrame split into many pandas partitions, scheduled on all cores or a cluster.',
               '<strong>PySpark</strong>: distributed engine on a cluster (JVM), lazy with the Catalyst optimiser, terabyte scale; includes a pandas API on Spark.'),
        table(['', 'pandas', 'Polars', 'Dask', 'PySpark'], [
            ['Scale', 'GB (RAM)', 'GB–100s GB', '100s GB+', 'TB–PB'],
            ['Execution', 'eager', 'eager or lazy', 'lazy', 'lazy'],
            ['Parallelism', 'mostly 1 core', 'all cores', 'cores/cluster', 'cluster'],
            ['API', 'pandas', 'expressions', 'pandas-like', 'DataFrame/SQL'],
            ['Best for', 'analysis, ML prep', 'fast single-node ETL', 'scaling pandas code', 'big data pipelines'],
        ]),
        tags('Polars', 'Dask', 'PySpark', 'Scalability', 'Lazy evaluation'),
    ),
    analogy('Moving house: <strong>pandas</strong> is your own car, perfect for most trips. <strong>Polars</strong> is a faster car with a smarter route '
            'planner. <strong>Dask</strong> is several cars driving in convoy. <strong>Spark</strong> is hiring a fleet of trucks: worth it only when the '
            'load is really that big.'),
    ecosystem_anim(),
    real_world(
        scenario('PG-DBDA project choice',
                 p('A 2 GB placement dataset: pandas is fine. A 60 GB clickstream on a laptop: Polars lazy/streaming or DuckDB. The 5 TB log data of a '
                   'telecom partner on their Hadoop cluster: PySpark. The pandas skills transfer: concepts (groupby, joins, window functions) are the same.')),
    ),
    example(
        data_note('students', 'marks'),
        pdrun("""
            import polars as pl

            # pandas
            p = (marks.merge(students, on='roll_no')
                      .groupby('course', as_index=False)['marks'].mean()
                      .sort_values('course'))
            print(p)
            print()

            # Polars: the same question, lazy, optimised before it runs
            q = (pl.from_pandas(marks).lazy()
                   .join(pl.from_pandas(students).lazy(), on='roll_no')
                   .group_by('course')
                   .agg(pl.col('marks').mean())
                   .sort('course'))
            print(q.collect())
            print(pl.__version__)
        """, setup=BOTH, title=S),
        pyshow("""
            # PySpark: the same aggregation on a cluster (shown, not run here)
            from pyspark.sql import functions as F
            (spark.read.parquet('s3://cdac/marks').join(spark.read.parquet('s3://cdac/students'), 'roll_no')
                  .groupBy('course').agg(F.avg('marks').alias('marks')).orderBy('course').show())

            # Dask: pandas syntax over many partitions
            import dask.dataframe as dd
            dd.read_parquet('marks/*.parquet').groupby('course')['marks'].mean().compute()
        """, title='Python (PySpark / Dask)'),
        title='Example: pandas and Polars Side by Side'),
    steps(
        ('Measure the problem', 'Data size vs RAM, run time, need for parallelism.'),
        ('Optimise pandas first', 'Fewer columns, better dtypes, vectorisation, Parquet.'),
        ('Single machine, bigger data', 'Polars or DuckDB.'),
        ('Existing pandas code to scale out', 'Dask (or pandas API on Spark).'),
        ('Cluster-scale data', 'PySpark; convert small results to pandas with <code>toPandas()</code> for plotting.'),
        title='Steps to Decide When to Switch'),
    crossq(
        ('Why is Polars often faster than pandas?', 'Multi-threaded Rust engine, Arrow memory, lazy query optimisation (predicate/projection pushdown) and no Python per-row overhead.'),
        ('What is lazy evaluation?', 'Operations build a plan; nothing runs until collect()/compute()/an action, so the engine can optimise the whole plan.'),
        ('Can pandas use multiple cores?', 'Mostly no for core operations; some readers (pyarrow engine) and NumPy internals use threads. Tools like Dask or modin parallelise it.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('What is method chaining? How and why do you use pipe?', 'Method Chaining & pipe', minutes=6, cards=[
    definition(
        defbox('<strong>Method chaining</strong> writes a transformation as one expression of successive method calls, each returning a new DataFrame: '
               '<code>(df.dropna().merge(...).assign(...).groupby(...).agg(...))</code>.',
               '<strong>pipe(func, *args)</strong> calls <code>func(df, *args)</code> inside the chain, so your own functions fit in the same readable flow. '
               '<code>assign</code> with lambdas and <code>query</code> are the other chain-friendly tools.'),
        tags('method chaining', 'pipe', 'assign', 'readability', 'functional style'),
    ),
    analogy('An <strong>assembly line</strong>: each station does one job and passes the item on. You can read the line from start to end, and adding a '
            'station (pipe) does not require rebuilding the factory.'),
    chaining_anim(),
    real_world(
        scenario('Reusable cleaning steps',
                 p('The team keeps small functions (<code>clean_names</code>, <code>add_grade</code>, <code>flag_low_attendance</code>) in a module; each '
                   'batch\'s notebook is one chain of <code>.pipe(...)</code> calls, which is easy to review and to reuse for the next batch.')),
    ),
    example(
        data_note('students', 'marks'),
        pdrun("""
            def add_grade(df, col='avg'):
                return df.assign(grade=np.select([df[col] >= 85, df[col] >= 70], ['A', 'B'], default='C'))

            def top_n(df, n):
                return df.nlargest(n, 'avg')

            report = (
                marks
                .dropna(subset=['marks'])
                .merge(students, on='roll_no')
                .query("centre == 'Kharghar'")
                .groupby('name', as_index=False)
                .agg(avg=('marks', 'mean'), subjects=('subject', 'count'))
                .pipe(add_grade)
                .pipe(top_n, n=3)
                .reset_index(drop=True)
            )
            print(report)
        """, setup=BOTH, title=S),
        title='Example: A Readable Report Pipeline with pipe'),
    steps(
        ('Wrap in parentheses', 'Lets each method sit on its own line without backslashes.'),
        ('One step per line', 'Easy to read, comment out and reorder.'),
        ('Use assign/query', 'Instead of separate assignment statements.'),
        ('Extract custom steps into functions', 'Each takes and returns a DataFrame; use <code>.pipe()</code>.'),
        ('Debug', 'Cut the chain at a line, or add <code>.pipe(lambda d: print(d.shape) or d)</code> temporarily.'),
        title='Steps to Write a Chain'),
    crossq(
        ('Is chaining slower?', 'No: it calls the same methods; it just avoids naming intermediate results.'),
        ('Why does assign need a lambda sometimes?', 'To refer to columns created earlier in the same chain: the lambda receives the current DataFrame, not the original variable.'),
        ('What are the downsides?', 'Very long chains can be hard to debug; split them into named stages or functions.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How do you test pandas code and validate data quality?', 'Testing & Validation', minutes=7, cards=[
    definition(
        defbox('<strong>Testing code</strong>: put transformations in functions and test them with pytest on tiny hand-made DataFrames, comparing with '
               '<code>pd.testing.assert_frame_equal</code> / <code>assert_series_equal</code> (which check values, dtypes, index and column names).',
               '<strong>Validating data</strong>: checks on real data inside the pipeline: key uniqueness, ranges, allowed values, missing values, row counts '
               'around merges. Plain <code>assert</code>s work; libraries such as <strong>pandera</strong> and <strong>Great Expectations</strong> declare '
               'schemas and report all failures.'),
        tags('assert_frame_equal', 'pytest', 'pandera', 'Great Expectations', 'data quality'),
    ),
    analogy('Testing code is checking the <strong>recipe</strong> with a small trial batch; validating data is <strong>checking the ingredients</strong> '
            'that arrive each morning. A perfect recipe with spoiled milk still gives a bad cake.'),
    validate_anim(),
    real_world(
        scenario('Result publication gate',
                 p('Before results are published, the pipeline asserts: every enrolled student has a row, marks are 0–100 or absent, no duplicate '
                   '(roll_no, subject), totals match the sum of components. One failed check blocks publishing and lists the offending rows.')),
    ),
    example(
        pdrun("""
            def add_result(df, pass_mark=60):
                return df.assign(result=np.where(df['marks'] >= pass_mark, 'PASS', 'FAIL'))

            # unit test: tiny input, exact expected output
            given    = pd.DataFrame({'roll_no': [1, 2], 'marks': [60, 59]})
            expected = pd.DataFrame({'roll_no': [1, 2], 'marks': [60, 59], 'result': ['PASS', 'FAIL']})
            pd.testing.assert_frame_equal(add_result(given), expected)
            print('unit test passed')

            # data validation on a real batch
            batch = pd.DataFrame({'roll_no': [2401, 2402, 2402, 2403], 'subject': ['SQL', 'SQL', 'SQL', 'ML'],
                                  'marks': [82, 91, 91, 140]})
            problems = {
                'duplicate keys': batch[batch.duplicated(['roll_no', 'subject'], keep=False)],
                'marks out of range': batch[~batch['marks'].between(0, 100)],
                'missing marks': batch[batch['marks'].isna()],
            }
            for name, rows in problems.items():
                print(f'{name:20}: {len(rows)} row(s)', rows['roll_no'].tolist() if len(rows) else '')

            try:
                pd.testing.assert_series_equal(pd.Series([1, 2]), pd.Series([1.0, 2.0]))
            except AssertionError as e:
                print('AssertionError:', str(e).splitlines()[0], '- dtypes differ')
        """),
        title='Example: Unit Test with assert_frame_equal, then Data Checks'),
    steps(
        ('Make logic testable', 'Functions that take and return DataFrames; no hidden file reads inside.'),
        ('Write small tests', 'Edge cases: boundary values, missing values, empty input, duplicates.'),
        ('Compare properly', '<code>assert_frame_equal</code> (use <code>check_dtype=False</code> or <code>check_exact=False</code> only on purpose).'),
        ('Validate inputs in the pipeline', 'Keys, ranges, allowed sets, counts; fail with the offending rows.'),
        ('Automate', 'Run tests in CI; schedule data checks with the pipeline (e.g. in Airflow).'),
        title='Steps to Make pandas Code Trustworthy'),
    crossq(
        ('Why not compare with df1 == df2?', 'It returns an element-wise DataFrame, fails on different shapes, and NaN != NaN; <code>df1.equals(df2)</code> gives one bool, and assert_frame_equal explains the difference.'),
        ('What does pandera add?', 'A declarative schema (column types, checks, nullability, uniqueness) that validates a DataFrame and reports all failures, usable as function decorators.'),
        ('How do you test float results?', 'assert_frame_equal compares floats with a tolerance by default (check_exact=False, rtol=1e-5).'),
    ),
]),
])
