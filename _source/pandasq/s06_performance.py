from build import *
from pandasq.anims import *
from pandasq.runner import pdrun, pyshow
from pandasq.data import STUDENTS, MARKS, BOTH, data_note

SECTION = dict(level='advanced', title='Performance & Modern pandas', questions=[

# ------------------------------------------------------------------ 26
Q('Why should you avoid loops and apply in pandas? What is vectorisation?', 'Vectorisation vs Loops', minutes=8, cards=[
    definition(
        defbox('<strong>Vectorisation</strong> means expressing a calculation as operations on <strong>whole columns (arrays)</strong>, so the loop over '
               'elements runs inside NumPy/Arrow compiled code instead of the Python interpreter.',
               '<code>iterrows()</code>, <code>itertuples()</code> and <code>apply(axis=1)</code> call Python code once per row. Each call costs '
               'microseconds; over millions of rows that is seconds or minutes, against milliseconds for the vectorised version.'),
        table(['Approach', 'Relative speed', 'Note'], [
            ['for … in iterrows()', 'slowest', 'creates a Series per row; also loses dtypes'],
            ['apply(func, axis=1)', 'slow', 'still a Python call per row'],
            ['itertuples()', 'faster loop', 'namedtuples, OK when a loop is unavoidable'],
            ['vectorised column maths / np.where', 'fastest', 'compiled loops, SIMD'],
        ]),
        tags('Vectorisation', 'iterrows', 'apply', 'NumPy', 'Performance'),
    ),
    analogy('Paying 1,000 employees: <strong>a loop</strong> is walking to the bank 1,000 times with one cheque each; <strong>vectorisation</strong> is '
            'uploading <strong>one bulk salary file</strong> that the bank processes in one go. Same result, very different effort.'),
    vector_anim(),
    real_world(
        scenario('Weighted score that took 20 minutes',
                 p('A script computed the final score (40% internal + 60% exam, with grace marks rules) using <code>apply(axis=1)</code> over 3 million '
                   'answer-level rows and took about 20 minutes. Rewritten with column arithmetic and <code>np.select</code>, it ran in under a second.')),
    ),
    example(
        pdrun("""
            import time
            n = 200_000
            rng = np.random.default_rng(7)
            df = pd.DataFrame({'internal': rng.integers(0, 101, n), 'exam': rng.integers(0, 101, n)})

            def score(row):
                return row['internal'] * 0.4 + row['exam'] * 0.6

            t = time.perf_counter(); r1 = [r['internal'] * 0.4 + r['exam'] * 0.6 for _, r in df.iterrows()]; t1 = time.perf_counter() - t
            t = time.perf_counter(); r2 = df.apply(score, axis=1);                                        t2 = time.perf_counter() - t
            t = time.perf_counter(); r3 = df['internal'] * 0.4 + df['exam'] * 0.6;                         t3 = time.perf_counter() - t

            print(f'iterrows   : {t1:8.3f} s')
            print(f'apply(row) : {t2:8.3f} s')
            print(f'vectorised : {t3:8.4f} s   (~{t1 / t3:,.0f}x faster than iterrows)')
            print('same result:', np.allclose(r1, r3) and np.allclose(r2, r3))

            df['result'] = np.select([r3 >= 85, r3 >= 60], ['Distinction', 'Pass'], default='Fail')
            print(df['result'].value_counts())
        """),
        title='Example: Timing iterrows vs apply vs Vectorised (200,000 rows)'),
    steps(
        ('Look for row loops', 'iterrows, itertuples, apply(axis=1), list comprehensions over rows.'),
        ('Rewrite as column expressions', 'Arithmetic, comparisons, <code>np.where</code>/<code>np.select</code>, <code>.str</code>/<code>.dt</code>.'),
        ('Lookups → merge or map', 'Instead of searching another DataFrame inside a loop.'),
        ('Per-group logic → groupby built-ins', '<code>transform</code>, <code>cumsum</code>, <code>rank</code>, <code>shift</code>.'),
        ('Measure', '<code>%timeit</code> in Jupyter or <code>time.perf_counter()</code>, and check results are identical.'),
        title='Steps to Vectorise Code'),
    crossq(
        ('Is apply always bad?', 'No: apply on columns (axis=0) with NumPy functions is fine, and for genuinely complex logic on small data clarity matters more. It is the per-row Python call that is slow.'),
        ('When is a loop acceptable?', 'Few rows, calls to external services per row, or logic that depends on the previous result in a way no cumulative function expresses (then consider Numba).'),
        ('Why does iterrows change int columns to float?', 'Each row becomes one Series, which needs a single dtype; mixed int/float rows are upcast to float.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('How do you reduce the memory usage of a DataFrame?', 'Memory Optimisation', minutes=8, cards=[
    definition(
        defbox('Measure with <code>df.memory_usage(deep=True)</code> or <code>df.info(memory_usage="deep")</code>. Then: <strong>downcast numbers</strong> '
               '(<code>pd.to_numeric(downcast=...)</code>, int32/float32), convert repeated text to <strong>category</strong>, use real '
               '<strong>booleans</strong>, use <strong>Arrow-backed</strong> strings, <strong>load fewer columns</strong> (<code>usecols</code>) with the right '
               '<code>dtype</code>, and store as <strong>Parquet</strong> so types persist.'),
        tags('memory_usage', 'category', 'downcast', 'usecols', 'Parquet', 'PyArrow'),
    ),
    analogy('Packing for a trip: you <strong>leave behind what you do not need</strong> (usecols), <strong>roll clothes tightly</strong> (smaller number '
            'types), and instead of carrying ten identical shirts you carry <strong>one with a note "×10"</strong> (category).'),
    memory_anim(),
    real_world(
        scenario('Laptop running out of memory',
                 p('Three years of exam answer logs (40 million rows) did not fit in 16 GB. Loading only 6 of 25 columns, course and subject as '
                   'category, ids as int32 and marks as float32 brought it to a few GB, enough to analyse on the laptop.')),
    ),
    example(
        pdrun("""
            n = 1_000_000
            rng = np.random.default_rng(1)
            df = pd.DataFrame({
                'roll_no': rng.integers(2400, 2900, n),
                'marks':   rng.integers(0, 101, n).astype('float64'),
                'course':  rng.choice(['PG-DBDA', 'PG-DAC', 'PG-DAI'], n),
                'passed':  rng.choice(['Y', 'N'], n),
            })
            def mb(d): return round(d.memory_usage(deep=True).sum() / 1e6, 1)
            print('before:', mb(df), 'MB')
            print(df.dtypes.to_dict())

            small = df.assign(
                roll_no=pd.to_numeric(df['roll_no'], downcast='integer'),
                marks=pd.to_numeric(df['marks'], downcast='float'),
                course=df['course'].astype('category'),
                passed=df['passed'].eq('Y'),
            )
            print('after :', mb(small), 'MB')
            print(small.dtypes.to_dict())
            print((small.memory_usage(deep=True) / 1e6).round(2))
        """),
        title='Example: 1 Million Rows Before and After'),
    steps(
        ('Measure', '<code>df.memory_usage(deep=True).sort_values()</code> shows the worst columns.'),
        ('Drop unused columns', 'Best at load time: <code>usecols</code>.'),
        ('Category for repeated text', 'Rule of thumb: distinct values much fewer than rows.'),
        ('Downcast numbers', '<code>pd.to_numeric(col, downcast="integer"|"float")</code>; check the range first.'),
        ('Persist efficiently', '<code>to_parquet()</code>; next time <code>read_parquet(columns=[...])</code>.'),
        title='Steps to Shrink a DataFrame'),
    crossq(
        ('Why use deep=True?', 'Without it, object/string columns report only the pointer size (8 bytes per value), not the strings themselves.'),
        ('Any risk with float32?', 'About 7 significant digits; fine for marks, not for money or large ids.'),
        ('When does category not help?', 'When almost every value is unique (names, emails): the dictionary is as big as the data.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('How do you process a file that is too large for memory?', 'Large Files & Chunking', minutes=8, cards=[
    definition(
        defbox('Options, from simplest: load <strong>fewer columns and smaller types</strong>; read in <strong>chunks</strong> '
               '(<code>read_csv(chunksize=N)</code> returns an iterator) and combine partial aggregates; convert to <strong>Parquet</strong> and read only '
               'needed columns and row groups (<code>columns=</code>, <code>filters=</code>); or use an engine designed for larger-than-memory data: '
               '<strong>Polars</strong> (lazy/streaming), <strong>DuckDB</strong> (SQL on files), <strong>Dask</strong> (parallel pandas) or '
               '<strong>PySpark</strong> (cluster).'),
        tags('chunksize', 'Parquet', 'Out-of-core', 'Dask', 'Polars', 'DuckDB'),
    ),
    analogy('Eating a whole jackfruit: you cannot swallow it at once, so you <strong>cut it into pieces</strong> (chunks) and keep only what you need from '
            'each. Parquet is buying it <strong>already cut and labelled</strong>, so you pick just the pieces you want.'),
    chunk_anim(),
    real_world(
        scenario('Online exam logs',
                 p('A 20 GB click log from the online exam system: a chunked read computes per-student event counts and suspicious-switch counts, '
                   'keeping only a 50,000-row summary in memory. The team then converted the log to Parquet partitioned by date, so later queries read '
                   'one day in seconds.')),
    ),
    example(
        pdrun("""
            # build a 300,000-row CSV to stand in for a huge file
            rng = np.random.default_rng(3)
            n = 300_000
            pd.DataFrame({'roll_no': rng.integers(2401, 2411, n),
                          'event':   rng.choice(['answer', 'tab_switch', 'idle'], n, p=[0.8, 0.05, 0.15]),
                          'secs':    rng.integers(1, 120, n)}).to_csv('exam_log.csv', index=False)

            parts = []
            for chunk in pd.read_csv('exam_log.csv', chunksize=100_000, usecols=['roll_no', 'event', 'secs']):
                parts.append(chunk.groupby(['roll_no', 'event'])['secs'].agg(['sum', 'count']))
                print('chunk', len(parts), chunk.shape)

            total = pd.concat(parts).groupby(level=[0, 1]).sum()        # combine partial sums and counts
            total['avg_secs'] = (total['sum'] / total['count']).round(1)   # average from sum/count, not avg of avgs
            print(total.xs('tab_switch', level='event').head(4))

            pd.read_csv('exam_log.csv').to_parquet('exam_log.parquet')
            only = pd.read_parquet('exam_log.parquet', columns=['roll_no', 'event'],
                                   filters=[('event', '==', 'tab_switch')])
            print(only.shape, only['event'].unique().tolist())
        """),
        title='Example: Chunked Aggregation, then Parquet with Column and Row Filters'),
    steps(
        ('Estimate', 'File size × 2–5 ≈ pandas memory needed; compare with free RAM.'),
        ('Reduce what you load', '<code>usecols</code>, <code>dtype</code>, <code>nrows</code> for trials.'),
        ('Chunk and aggregate', 'Combine sums/counts/min/max; derive averages at the end.'),
        ('Convert once to Parquet', 'Partition by a commonly filtered column (date, centre).'),
        ('Outgrown one machine?', 'Polars or DuckDB on the laptop; Spark on a cluster.'),
        title='Steps for Big Files'),
    crossq(
        ('Why not average the chunk averages?', 'Chunks have different group sizes; the average of averages is wrong unless every group is the same size. Keep sum and count.'),
        ('Why is Parquet faster than CSV?', 'Columnar, compressed, typed, with statistics per row group: readers skip columns and row groups they do not need and do not parse text.'),
        ('What about operations needing all data, like median or sort?', 'Chunking does not work directly; use an out-of-core engine, or approximate algorithms.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('What is the difference between map, apply, applymap and replace?', 'map vs apply vs replace', minutes=7, cards=[
    definition(
        defbox('<strong>Series.map(arg)</strong>: element-wise transformation using a dict, Series or function; unmatched dict keys become NaN.',
               '<strong>Series.apply(func)</strong>: calls func on each element (or on the Series for NumPy ufuncs). <strong>DataFrame.apply(func, '
               'axis=0|1)</strong>: calls func on each column (default) or each row.',
               '<strong>DataFrame.map(func)</strong>: element-wise on every cell. It was called <code>applymap</code>, renamed in pandas 2.1 '
               '(applymap was removed in 3.0).',
               '<strong>replace(to_replace, value)</strong>: substitutes specific values, leaving others unchanged; supports dicts and regex.'),
        tags('map', 'apply', 'applymap', 'DataFrame.map', 'replace'),
    ),
    analogy('<strong>map</strong> is a translator with a <strong>dictionary</strong>: a word not in the dictionary comes back blank. <strong>replace</strong> is '
            'a <strong>proof-reader</strong> fixing only the listed mistakes and leaving everything else as it was. <strong>apply</strong> hands a whole '
            '<strong>page</strong> (row or column) to someone to do whatever they like with it.'),
    map_apply_anim(),
    real_world(
        scenario('Course names and grade points',
                 p('Course codes → full names with <code>map(course_dict)</code> (NaN highlights unknown codes); fixing a few typos with '
                   '<code>replace({"PG-DBDa": "PG-DBDA"})</code>; per-column min-max scaling with <code>apply(lambda c: (c - c.min()) / (c.max() - c.min()))</code>.')),
    ),
    example(
        pdrun("""
            codes = pd.Series(['PG-DBDA', 'PG-DAC', 'PG-DBDa', 'PG-DAI'])
            names = {'PG-DBDA': 'Big Data Analytics', 'PG-DAI': 'Artificial Intelligence'}

            print(codes.map(names).tolist())                       # unmatched -> NaN
            print(codes.replace({'PG-DBDa': 'PG-DBDA'}).tolist())   # unmatched kept
            print()

            scores = pd.DataFrame({'sql': [82, 61, 91], 'spark': [70, 88, 79]})
            print(scores.apply(lambda col: col.max() - col.min()))          # per column
            print(scores.apply(lambda row: row.mean(), axis=1).tolist())     # per row (slow on big data)
            print(scores.mean(axis=1).tolist())                              # vectorised equivalent
            print(scores.map(lambda v: 'A' if v >= 85 else 'B'))             # every cell
            print(hasattr(pd.DataFrame, 'applymap'))
        """),
        title='Example: map vs replace, apply by column/row, DataFrame.map'),
    steps(
        ('Value lookup', '<code>s.map(dict)</code>; check <code>isna()</code> for unmapped values.'),
        ('Fix a few values', '<code>s.replace({...})</code>.'),
        ('Per column', '<code>df.apply(func)</code>, or a built-in like <code>df.max()</code>.'),
        ('Per cell', '<code>df.map(func)</code>, but try a vectorised version first.'),
        ('Per row', 'Last resort: <code>apply(axis=1)</code>; prefer column expressions.'),
        title='Steps to Pick the Right One'),
    crossq(
        ('map with a function vs apply on a Series?', 'Both are element-wise for plain functions; map also accepts dicts/Series and has na_action="ignore" to skip missing values.'),
        ('How do you map with a default for unknown keys?', '<code>s.map(d).fillna("Other")</code>, or a defaultdict, or <code>s.replace(d)</code> if keeping originals is fine.'),
        ('What replaced applymap?', 'DataFrame.map (pandas 2.1+). applymap was deprecated and is gone in 3.0.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What changed in pandas 2.0 and 3.0? What is the PyArrow backend?', 'pandas 2.x / 3.0 & PyArrow', minutes=8, cards=[
    definition(
        defbox('<strong>pandas 2.0</strong> (April 2023) added optional <strong>Apache Arrow-backed</strong> dtypes (<code>dtype_backend="pyarrow"</code> '
               'in readers, <code>"int64[pyarrow]"</code> etc.), non-nanosecond datetime resolutions, and removed many deprecated APIs '
               '(<code>append</code>, <code>.ix</code> was already gone).',
               '<strong>pandas 3.0</strong> makes <strong>Copy-on-Write</strong> the only behaviour (no SettingWithCopyWarning; chained assignment never '
               'works), uses a <strong>dedicated string dtype</strong> (<code>str</code>, Arrow-backed when PyArrow is installed) by default, infers '
               'microsecond datetime resolution from strings, and removes everything deprecated in 2.x (applymap, fillna(method=), "M" frequency…).',
               '<strong>Why Arrow</strong>: a columnar memory format shared by Spark, Polars, DuckDB and Parquet: compact strings, real missing values for '
               'every type, fast I/O and zero-copy exchange between tools.'),
        tags('pandas 3.0', 'pandas 2.0', 'PyArrow', 'Copy-on-Write', 'string dtype'),
    ),
    analogy('Upgrading from a <strong>handwritten register</strong> to a <strong>standard spreadsheet format</strong> everyone in the office can open: '
            'Arrow is the shared format, so pandas, Spark, Polars and DuckDB pass data around without retyping it.'),
    pandas3_anim(),
    real_world(
        scenario('Upgrading the result-processing scripts',
                 p('Scripts written for pandas 1.3 failed on 3.0: <code>df.append</code> (removed), <code>applymap</code> (removed), '
                   '<code>resample("M")</code> (renamed) and one place that relied on chained assignment silently stopped updating data. Running them on '
                   '2.2 with <code>-W error::FutureWarning</code> listed every place to fix before switching.')),
    ),
    example(
        pdrun("""
            print(pd.__version__)
            s = pd.Series(['PG-DBDA', None, 'PG-DAC'])
            print(s.dtype, '|', s.isna().tolist())                 # str dtype, missing = NaN

            obj = pd.Series(['PG-DBDA', None, 'PG-DAC'], dtype=object)
            big = pd.concat([s] * 100_000)
            big_obj = pd.concat([obj] * 100_000)
            print('str dtype :', round(big.memory_usage(deep=True) / 1e6, 1), 'MB')
            print('object    :', round(big_obj.memory_usage(deep=True) / 1e6, 1), 'MB')

            arrow = pd.Series([82, None, 91], dtype='int64[pyarrow]')
            print(arrow.dtype, arrow.tolist())                     # integer with a real missing value

            print(pd.to_datetime(['2026-10-13 10:00']).dtype)        # microsecond resolution in 3.0
            print([name for name in ['append', 'applymap', 'iteritems'] if hasattr(pd.DataFrame, name)])
        """),
        title='Example: String dtype, Arrow Integers, Removed APIs'),
    steps(
        ('Check your version', '<code>pd.__version__</code>; <code>pd.show_versions()</code> for dependencies.'),
        ('Install PyArrow', 'Needed for the fast string dtype, Parquet and Arrow-backed types.'),
        ('Upgrade via 2.2', 'Run the test suite with warnings as errors; fix each FutureWarning.'),
        ('Fix chained assignment', 'Replace <code>df[a][b] = x</code> patterns with <code>df.loc[...] = x</code>.'),
        ('Then move to 3.0', 'Re-run tests; review string/object dtype assumptions in your code.'),
        title='Steps to Upgrade to pandas 3'),
    crossq(
        ('Can I opt into Arrow for everything?', '<code>pd.read_csv(path, dtype_backend="pyarrow")</code> or <code>df.convert_dtypes(dtype_backend="pyarrow")</code>.'),
        ('Is Copy-on-Write a performance cost?', 'Generally a gain: many operations avoid defensive copies; copies happen only when shared data is written.'),
        ('Does pandas 3 still support object dtype?', 'Yes, explicitly with dtype=object, for mixed Python objects; text just no longer defaults to it.'),
    ),
]),
])
