from build import *
from pandasq.anims import *
from pandasq.runner import pdrun, pyshow
from pandasq.data import STUDENTS, MARKS, BOTH, data_note

RUN_NOTE = note('Every example with an Output box was really executed while this page was built, with '
                '<strong>pandas 3.0</strong>, NumPy 2 and PyArrow. The only hidden lines are <code>import pandas as pd</code>, '
                '<code>import numpy as np</code> and display-width settings. Where pandas 3 behaves differently from pandas 1.x/2.x, '
                'the answer says so, because interviewers still ask about both.', 'How the examples were run')

SECTION = dict(level='beginner', title='Pandas Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is pandas? Why is it used in data analysis?', 'What is pandas', minutes=7, cards=[
    definition(
        defbox('<strong>pandas</strong> is an open-source Python library for working with <strong>tabular and time-series data</strong>. '
               'Its two core structures are the <strong>Series</strong> (one labelled column) and the <strong>DataFrame</strong> (a table of labelled '
               'rows and named, typed columns).',
               'It provides fast, vectorised tools to <strong>read</strong> data from files and databases, <strong>clean</strong> it, <strong>filter, '
               'group, reshape and join</strong> it, and <strong>write</strong> it out again. It is built on NumPy arrays (and optionally Apache Arrow), '
               'and runs on a single machine, in memory.'),
        tags('pandas', 'DataFrame', 'Series', 'Data Wrangling', 'Python', 'EDA'),
    ),
    analogy('pandas is <strong>Excel inside Python, with a programmable memory</strong>. Everything you would do with filters, VLOOKUP, pivot tables '
            'and formulas, you write as one line of code. The difference: the steps are saved, repeatable on next month\'s file in a second, '
            'and work on millions of rows where Excel gives up at about one million.'),
    pandas_anim(),
    real_world(
        scenario('C-DAC result processing',
                 p('Every module test produces a CSV of marks per centre. A 20-line pandas script reads all files, joins them to the student list, '
                   'flags students below the pass mark, computes course-wise averages and writes the Excel sheet for the coordinator. '
                   'The same script runs for every batch.')),
        scenario('Industry',
                 p('Data scientists use pandas for exploratory analysis and feature preparation before scikit-learn; data engineers use it for '
                   'small and medium ETL jobs, data quality checks and prototypes before scaling up with PySpark.')),
    ),
    example(
        RUN_NOTE,
        pdrun("""
            marks = pd.DataFrame({
                'name':    ['Anuj', 'Vineeta', 'Aarshvi', 'Rohan', 'Meera'],
                'course':  ['PG-DBDA', 'PG-DBDA', 'PG-DAI', 'PG-DAC', 'PG-DBDA'],
                'marks':   [82, 91, 84, 58, 75],
            })

            print(marks)
            print()
            print(marks[marks['marks'] >= 60])          # filter
            print()
            print(marks.groupby('course')['marks'].mean())  # aggregate
        """),
        title='Example: Your First DataFrame'),
    steps(
        ('Install', '<code>pip install pandas</code> (comes with Anaconda). Optional: <code>pyarrow</code> for Parquet and faster strings, <code>openpyxl</code> for Excel.'),
        ('Import', '<code>import pandas as pd</code>, the universal convention.'),
        ('Load data', '<code>df = pd.read_csv("marks.csv")</code> or build one from a dict with <code>pd.DataFrame({...})</code>.'),
        ('Inspect', '<code>df.head()</code>, <code>df.info()</code>, <code>df.describe()</code>.'),
        ('Transform and save', 'Filter, group, join; then <code>df.to_csv()</code> / <code>to_excel()</code> / <code>to_parquet()</code>.'),
        title='Steps to Start with pandas'),
    crossq(
        ('Why is pandas fast if Python is slow?', 'Column operations run in compiled C code over NumPy/Arrow arrays (vectorisation). Only Python-level loops such as iterrows or apply with a Python function are slow.'),
        ('What is the main limitation?', 'Single machine and in memory: a DataFrame usually needs several times the file size in RAM. For larger data use chunking, Polars, Dask or PySpark.'),
        ('Where does the name come from?', 'From "panel data" (an econometrics term for multi-dimensional data), and a play on "Python data analysis".'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('What is the difference between a Series and a DataFrame?', 'Series vs DataFrame', minutes=6, cards=[
    definition(
        defbox('A <strong>Series</strong> is a one-dimensional labelled array: values, an <strong>index</strong> (row labels), one dtype and an optional name.',
               'A <strong>DataFrame</strong> is a two-dimensional labelled table: a collection of Series (columns) that share the same index. Each column '
               'has its own dtype.'),
        table(['Aspect', 'Series', 'DataFrame'], [
            ['Dimensions', '1-D', '2-D (rows × columns)'],
            ['dtype', 'one', 'one per column'],
            ['Created from', 'list, dict, NumPy array, scalar', 'dict of lists, list of dicts, 2-D array, CSV…'],
            ['df[...] returns', '—', "df['col'] → Series, df[['col']] → DataFrame"],
            ['Typical use', 'one variable, a result of an aggregation', 'a whole dataset'],
        ]),
        tags('Series', 'DataFrame', 'Index', 'dtype'),
    ),
    analogy('A Series is <strong>one column of an attendance register</strong> with the roll numbers printed down the side. A DataFrame is the '
            '<strong>whole register</strong>: the same roll numbers down the side, and one column per date. Tear out one column and you have a Series again.'),
    series_df_anim(),
    real_world(
        scenario('Where each appears',
                 p('<code>df["marks"]</code> gives a Series you can call <code>.mean()</code> on; <code>df.groupby("course")["marks"].mean()</code> '
                   'returns a Series indexed by course; <code>df.groupby("course").agg(...)</code> with several outputs returns a DataFrame. '
                   'Knowing which one you have explains most "AttributeError: Series has no attribute..." mistakes.')),
    ),
    example(
        pdrun("""
            s = pd.Series([82, 91, 84], index=['Anuj', 'Vineeta', 'Aarshvi'], name='marks')
            print(s)
            print('type:', type(s).__name__, '| dtype:', s.dtype, '| ndim:', s.ndim)
            print()

            df = pd.DataFrame({'course': ['PG-DBDA', 'PG-DBDA', 'PG-DAI'],
                               'marks':  [82, 91, 84]},
                              index=['Anuj', 'Vineeta', 'Aarshvi'])
            print(df)
            print(df.dtypes)
            print()
            print(type(df['marks']).__name__, '<- df["marks"]')
            print(type(df[['marks']]).__name__, '<- df[["marks"]]')
            print(df.loc['Vineeta'])     # one row is also a Series (index = column names)
        """),
        title='Example: Series, DataFrame, and What Brackets Return'),
    steps(
        ('Series from a list', '<code>pd.Series([82, 91], index=["Anuj", "Vineeta"], name="marks")</code>.'),
        ('Series from a dict', 'Keys become the index: <code>pd.Series({"Anuj": 82, "Vineeta": 91})</code>.'),
        ('DataFrame from a dict of lists', 'Keys become column names: <code>pd.DataFrame({"name": [...], "marks": [...]})</code>.'),
        ('DataFrame from a list of dicts', 'Each dict is a row: handy for JSON records.'),
        ('Convert', '<code>s.to_frame()</code> turns a Series into a one-column DataFrame; <code>df.squeeze()</code> the reverse.'),
        title='Steps to Create Them'),
    crossq(
        ('Is a row of a DataFrame a Series?', 'Yes. <code>df.loc[label]</code> returns a Series whose index is the column names. If columns have mixed types, that Series has a common type such as object.'),
        ('How is a Series different from a NumPy array?', 'It has an index (labels) that operations align on, a name, missing-value handling, and many data-analysis methods (value_counts, str, dt…).'),
        ('Why does the course column show dtype str?', 'pandas 3.0 stores text in a dedicated string dtype (shown as <code>str</code>, backed by PyArrow when installed). pandas 1.x/2.x stored text as generic Python objects, shown as <code>object</code>.'),
        ('How is a DataFrame different from a 2-D NumPy array?', 'Columns are named and can each have a different dtype; rows have labels; alignment and missing data are handled automatically.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What is the index in pandas? What is data alignment?', 'Index & Alignment', minutes=7, cards=[
    definition(
        defbox('The <strong>index</strong> is the set of row labels of a Series or DataFrame (the columns are also an Index object). By default it is a '
               'RangeIndex 0, 1, 2…, but it can be any labels: roll numbers, dates, names, or several levels (MultiIndex).',
               '<strong>Data alignment</strong>: when two objects are combined (arithmetic, assignment of a Series to a column, concat), pandas '
               '<strong>matches rows by index label, not by position</strong>. Labels missing on one side produce NaN.'),
        tags('Index', 'Alignment', 'set_index', 'reset_index', 'NaN'),
    ),
    analogy('Two teachers hand in marks lists in different orders. A careless clerk adds line 1 to line 1 and gives Anuj Vineeta\'s marks. pandas is the '
            'careful clerk: it <strong>looks up each name</strong> on the second list before adding, and writes "missing" when a name appears on only one list.'),
    alignment_anim(),
    real_world(
        scenario('Silent bug it prevents (and causes)',
                 p('Adding SQL and Spark marks from two exports sorted differently works correctly because of alignment. But after filtering or '
                   'sorting a DataFrame, assigning a NumPy array or list to a column is positional, while assigning a Series is aligned; mixing '
                   'them up gives wrong rows or unexpected NaN. <code>reset_index(drop=True)</code> is often the fix.')),
    ),
    example(
        pdrun("""
            sql   = pd.Series({'Anuj': 82, 'Vineeta': 91, 'Rohan': 58})
            spark = pd.Series({'Vineeta': 88, 'Anuj': 61, 'Meera': 70})

            print(sql + spark)                       # aligned by label
            print()
            print(sql.add(spark, fill_value=0))      # treat missing as 0
            print()

            df = pd.DataFrame({'roll_no': [2401, 2402, 2403], 'name': ['Anuj', 'Vineeta', 'Aarshvi']})
            df = df.set_index('roll_no')             # column -> index
            print(df.loc[2402])                      # lookup by label
            print(df.index)
            print(df.reset_index().columns.tolist()) # index -> column again
        """),
        title='Example: Alignment, set_index and reset_index'),
    steps(
        ('Pick a unique key', 'Use a natural key such as roll_no as the index when you will look rows up by it.'),
        ('Set it', '<code>df = df.set_index("roll_no")</code> (or <code>index_col="roll_no"</code> in read_csv).'),
        ('Check it', '<code>df.index.is_unique</code>; duplicate labels make <code>loc</code> return several rows.'),
        ('Use it', '<code>df.loc[2402]</code>, joins with <code>join</code>, time-series resampling on a DatetimeIndex.'),
        ('Undo it', '<code>reset_index()</code> moves it back to a column; <code>reset_index(drop=True)</code> discards it.'),
        title='Steps to Work with the Index'),
    crossq(
        ('Can the index have duplicates?', 'Yes, pandas allows it, but label lookups then return multiple rows and some operations (reindex) fail. Check with <code>index.is_unique</code>.'),
        ('How do you avoid alignment when you want positional behaviour?', 'Use <code>.to_numpy()</code> (or <code>.values</code>) on the right-hand side, or reset both indexes first.'),
        ('Why is the index useful at all?', 'Fast label lookups, automatic alignment, natural joins (<code>df.join</code>), and time-series features (resample, rolling with time windows) on a DatetimeIndex.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('How do you read data into pandas? What are the important read_csv parameters?', 'Reading Data (read_csv)', minutes=8, cards=[
    definition(
        defbox('pandas has a reader for each format: <code>read_csv</code>, <code>read_excel</code>, <code>read_json</code>, <code>read_parquet</code>, '
               '<code>read_sql</code>, <code>read_html</code>, <code>read_xml</code>… Each returns a DataFrame. The matching writers are '
               '<code>to_csv</code>, <code>to_excel</code>, <code>to_parquet</code> and so on.',
               '<code>read_csv</code> is the most used and has the most options, because a CSV carries no type information.'),
        table(['Parameter', 'Use'], [
            ['sep', "delimiter: ',' (default), ';', '\\t', '|'"],
            ['header / names', 'which line holds the column names; or give names yourself'],
            ['usecols', 'load only some columns (saves memory)'],
            ['dtype', "force types, e.g. {'roll_no': 'int32', 'subject': 'category'}"],
            ['parse_dates', 'convert columns to datetime while reading'],
            ['na_values', "extra strings to treat as missing, e.g. ['NA', 'AB', '-']"],
            ['index_col', 'use a column as the index'],
            ['nrows / skiprows', 'read part of the file'],
            ['chunksize', 'read a big file in pieces (iterator of DataFrames)'],
            ['encoding', "e.g. 'utf-8', 'latin-1' for files from old systems"],
        ]),
        tags('read_csv', 'read_excel', 'read_parquet', 'read_sql', 'I/O'),
    ),
    analogy('<code>read_csv</code> is a <strong>data-entry operator typing a printed sheet into the system</strong>. Without instructions they guess: '
            '"AB" for absent becomes text, dates stay as words, the semicolon-separated sheet goes into one box. The parameters are your '
            'instructions: "columns are separated by semicolons, AB means absent, this column is a date".'),
    read_csv_anim(),
    real_world(
        scenario('Exam export from the online test system',
                 p('The export uses semicolons, writes "AB" for absent students and dates as text. Read naively, <code>marks</code> becomes a text '
                   'column and averages fail. With <code>sep=";"</code>, <code>na_values=["AB"]</code> and <code>parse_dates</code>, the DataFrame is '
                   'ready to analyse.')),
    ),
    example(
        pdrun("""
            # marks.csv was written by the example; the file is shown in the first print
            print(open('marks.csv').read())

            naive = pd.read_csv('marks.csv')
            print(naive.shape, naive.columns.tolist())      # wrong separator -> 1 column

            df = pd.read_csv('marks.csv',
                             sep=';',
                             na_values=['AB'],
                             parse_dates=['exam_date'],
                             dtype={'subject': 'category'})
            print(df)
            print(df.dtypes)
        """, files={'marks.csv': """
            roll_no;subject;marks;exam_date
            2401;SQL;82;2026-09-20
            2402;SQL;AB;2026-09-20
            2403;ML;84;2026-09-21
            2404;Java;58;2026-09-22
        """}),
        title='Example: read_csv with the Right Options'),
    steps(
        ('Open the file in a text editor first', 'Check the delimiter, header row, encoding and how missing values are written.'),
        ('Read a sample', '<code>pd.read_csv(path, nrows=1000)</code> to try options quickly.'),
        ('Set the options', '<code>sep</code>, <code>usecols</code>, <code>dtype</code>, <code>parse_dates</code>, <code>na_values</code>.'),
        ('Verify', '<code>df.info()</code>: check dtypes and non-null counts.'),
        ('For repeat loads', 'Save as Parquet (<code>df.to_parquet()</code>): types are stored and reading is much faster.'),
        title='Steps to Load a File Reliably'),
    crossq(
        ('How do you read a CSV that does not fit in memory?', '<code>chunksize=100_000</code> returns an iterator of DataFrames; process each chunk and combine the small results. Or load only needed columns with <code>usecols</code> and smaller dtypes.'),
        ('How do you read all sheets of an Excel file?', '<code>pd.read_excel(path, sheet_name=None)</code> returns a dict {sheet name: DataFrame}.'),
        ('How do you read from a database?', '<code>pd.read_sql(query, connection)</code> with a SQLAlchemy engine or a DB-API connection (e.g. sqlite3).'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('How do you explore a new dataset quickly? Explain head, info, describe, value_counts.', 'Inspecting Data (EDA)', minutes=7, cards=[
    definition(
        defbox('Exploratory data analysis starts with a few inspection methods that show the <strong>size, structure, types, missing values and '
               'distributions</strong> of a DataFrame before any transformation.'),
        table(['Method', 'Shows'], [
            ['shape', '(rows, columns)'],
            ['head(n) / tail(n) / sample(n)', 'actual rows'],
            ['info()', 'columns, dtypes, non-null counts, memory'],
            ['describe()', 'count, mean, std, min, quartiles, max for numeric columns'],
            ['dtypes', 'type of each column'],
            ['isna().sum()', 'missing values per column'],
            ['value_counts()', 'frequency of each value in a column'],
            ['nunique()', 'number of distinct values per column'],
            ['duplicated().sum()', 'number of duplicate rows'],
        ]),
        tags('EDA', 'info', 'describe', 'value_counts', 'isna'),
    ),
    analogy('A doctor\'s first check-up: <strong>height and weight</strong> (shape), <strong>looking at the patient</strong> (head), the '
            '<strong>blood report</strong> (info and describe), and asking <strong>what is missing</strong> (isna). Only then the treatment (cleaning).'),
    inspect_anim(),
    real_world(
        scenario('New placement dataset from a partner company',
                 p('<code>info()</code> shows <code>package_lpa</code> as text: a few rows contain "4.5 LPA". <code>describe()</code> shows a maximum '
                   'CGPA of 85, so some colleges sent percentages. <code>value_counts()</code> on city shows "Mumbai", "mumbai" and "Mumbai ". '
                   'Three cleaning tasks found in two minutes.')),
    ),
    example(
        data_note('marks'),
        pdrun("""
            print(marks.shape)
            print(marks.head(3))
            print()
            marks.info()
            print()
            print(marks.describe())
            print()
            print(marks['subject'].value_counts())
            print()
            print(marks.isna().sum())
        """, setup=MARKS, title='Python (pandas) · uses sample data'),
        title='Example: Inspecting the Marks Data'),
    steps(
        ('Size and sample', '<code>df.shape</code>, <code>df.head()</code>, <code>df.sample(5)</code>.'),
        ('Structure', '<code>df.info()</code>: are the dtypes what you expect?'),
        ('Numbers', '<code>df.describe()</code>: impossible minimums/maximums, outliers.'),
        ('Categories', '<code>df["col"].value_counts(dropna=False)</code>: typos, spelling variants, missing.'),
        ('Problems', '<code>df.isna().sum()</code>, <code>df.duplicated().sum()</code>; write down what to clean.'),
        title='Steps for a First Look'),
    crossq(
        ('What does describe() show for text columns?', 'With <code>include="object"</code> or <code>include="all"</code>: count, unique, top (most frequent) and freq.'),
        ('Why is marks float64 in the sample?', 'It contains a missing value (None → NaN). The classic NumPy int64 cannot hold NaN, so pandas upcasts to float64. Use the nullable <code>Int64</code> dtype to keep integers.'),
        ('How do you get percentages instead of counts?', '<code>value_counts(normalize=True)</code>.'),
    ),
]),
])
