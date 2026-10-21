from build import *
from pandasq.anims import *
from pandasq.runner import pdrun, pyshow
from pandasq.data import STUDENTS, MARKS, BOTH, data_note

S = 'Python (pandas) · uses sample data'

SECTION = dict(level='intermediate', title='Joins, Windows & Time Series', questions=[

# ------------------------------------------------------------------ 21
Q('How do you join two DataFrames? Explain the merge types.', 'merge (Joins)', minutes=8, cards=[
    definition(
        defbox('<code>pd.merge(left, right, on=..., how=...)</code> (or <code>left.merge(right, ...)</code>) combines rows of two DataFrames whose key '
               'values match, exactly like a SQL JOIN.'),
        table(['how', 'Keeps', 'SQL'], [
            ['inner (default)', 'keys in both', 'INNER JOIN'],
            ['left', 'all left rows; NaN where no match', 'LEFT JOIN'],
            ['right', 'all right rows', 'RIGHT JOIN'],
            ['outer', 'all keys from both', 'FULL OUTER JOIN'],
            ['cross', 'every pair of rows', 'CROSS JOIN'],
            ['left_anti / right_anti (pandas 3)', 'left rows with no match', 'NOT EXISTS'],
        ]),
        p('Key options: <code>on</code> (same name), <code>left_on</code>/<code>right_on</code> (different names), <code>left_index</code>/'
          '<code>right_index</code>, <code>suffixes</code> for overlapping columns, <code>indicator=True</code>, <code>validate</code>.'),
        tags('merge', 'join', 'inner', 'left', 'outer', 'indicator', 'SQL JOIN'),
    ),
    analogy('Matching <strong>admission forms with fee receipts</strong> by roll number. <strong>inner</strong>: only students who have both. '
            '<strong>left</strong>: every admitted student, with a blank where the receipt is missing. <strong>outer</strong>: everything, including '
            'receipts that match no form, which is exactly what the accounts audit wants to see.'),
    merge_anim(),
    real_world(
        scenario('Fee reconciliation',
                 p('Outer merge of the admissions list and the bank statement on roll number with <code>indicator=True</code>: "left_only" are '
                   'students who have not paid, "right_only" are payments with a wrong roll number, "both" are reconciled. Three filters give the '
                   'three follow-up lists.')),
    ),
    example(
        pdrun("""
            students = pd.DataFrame({'roll_no': [2401, 2402, 2407], 'name': ['Anuj', 'Vineeta', 'Isha']})
            fees     = pd.DataFrame({'roll': [2401, 2402, 2499], 'paid': [95000, 90000, 95000]})

            print(students.merge(fees, left_on='roll_no', right_on='roll'))                       # inner
            print()
            print(students.merge(fees, left_on='roll_no', right_on='roll', how='left'))
            print()
            recon = students.merge(fees, left_on='roll_no', right_on='roll', how='outer', indicator=True)
            print(recon)
            print()
            print(recon['_merge'].value_counts())
        """),
        title='Example: inner, left and outer with indicator'),
    steps(
        ('Check keys on both sides', 'Same meaning, same dtype, unique where they should be (<code>is_unique</code>).'),
        ('Choose how', 'Enriching a main table → left; only matches → inner; reconciliation → outer + indicator.'),
        ('Merge', '<code>left.merge(right, on="roll_no", how="left", validate="many_to_one")</code>.'),
        ('Verify', 'Row count before vs after; NaN in right-side columns = unmatched rows.'),
        ('Clean up', 'Drop the duplicate key column when names differed; rename <code>_x</code>/<code>_y</code> suffixes.'),
        title='Steps to Merge Correctly'),
    crossq(
        ('What happens to columns with the same name that are not keys?', 'Both are kept with suffixes _x and _y (configurable with <code>suffixes=("_stu", "_fee")</code>).'),
        ('How do you find rows in A that are not in B?', 'pandas 3: <code>A.merge(B, on=key, how="left_anti")</code>. Any version: <code>A[~A[key].isin(B[key])]</code>, or outer merge with indicator and keep "left_only".'),
        ('Can you merge on several columns?', 'Yes, <code>on=["roll_no", "subject"]</code>.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What is the difference between merge, join and concat?', 'merge vs join vs concat', minutes=6, cards=[
    definition(
        defbox('<strong>concat</strong>: glues objects together along an axis: <strong>stacking rows</strong> (axis=0) or placing side by side (axis=1, '
               'aligned on index). No key matching.',
               '<strong>merge</strong>: database-style join on <strong>column values</strong> (or index), any join type.',
               '<strong>join</strong>: a DataFrame method that merges on the <strong>index</strong> of the right frame (left join by default); convenient when '
               'tables are indexed by the key.'),
        table(['Need', 'Use'], [
            ['Same columns, more rows (monthly files)', 'pd.concat([...])'],
            ['Add columns from another table by key', 'merge'],
            ['Both indexed by the key', 'df.join(other)'],
            ['Add a Series as a column aligned on index', "df['x'] = s or pd.concat([df, s], axis=1)"],
        ]),
        tags('concat', 'merge', 'join', 'append'),
    ),
    analogy('<strong>concat</strong> is stapling <strong>attendance sheets from different weeks</strong> one below the other. <strong>merge</strong> is '
            'looking up each roll number in <strong>another register</strong> and copying its details across. <strong>join</strong> is the same lookup '
            'when both registers are already filed by roll number.'),
    concat_anim(),
    real_world(
        scenario('Monthly marks files',
                 p('Every centre uploads a CSV each month. <code>pd.concat([pd.read_csv(f).assign(source=f) for f in files], ignore_index=True)</code> '
                   'builds one table; a merge with the student master adds names and courses.')),
    ),
    example(
        pdrun("""
            kharghar = pd.DataFrame({'roll_no': [2401, 2402], 'marks': [82, 91]})
            juhu     = pd.DataFrame({'roll_no': [2403, 2404], 'marks': [84, 58]})

            all_marks = pd.concat([kharghar, juhu], keys=['Kharghar', 'Juhu'], names=['centre', None]).reset_index(level=0)
            print(all_marks.reset_index(drop=True))
            print()

            names = pd.DataFrame({'name': ['Anuj', 'Vineeta', 'Aarshvi', 'Rohan']}, index=[2401, 2402, 2403, 2404])
            print(all_marks.set_index('roll_no').join(names))
            print()
            print(pd.concat([kharghar, juhu], axis=1))       # side by side on index 0, 1
        """),
        title='Example: concat with keys, join on index, axis=1'),
    steps(
        ('Many similar files', 'Read each into a list, then <code>pd.concat(list, ignore_index=True)</code>.'),
        ('Remember the source', '<code>keys=</code> or <code>.assign(source=...)</code> before concatenating.'),
        ('Check columns match', 'Missing columns become NaN; misspelt names create extra columns.'),
        ('Enrich', '<code>merge</code> on key columns or <code>join</code> on the index.'),
        title='Steps to Combine Data'),
    crossq(
        ('What happened to DataFrame.append?', 'Deprecated in 1.4 and removed in 2.0. Use pd.concat; appending row by row in a loop is quadratic and slow.'),
        ('What does concat do with different columns?', 'Outer union of columns by default (missing values NaN); <code>join="inner"</code> keeps only common columns.'),
        ('Is join faster than merge?', 'join on an index can be faster because the index is already built and possibly sorted; functionally both use the same machinery.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('What are common mistakes when merging? How do you validate a merge?', 'Merge Pitfalls & validate', minutes=8, cards=[
    definition(
        defbox('The most dangerous merge bug is <strong>row explosion</strong>: duplicate keys on both sides create every combination, inflating sums and '
               'counts without any error. Other issues: <strong>key dtype mismatch</strong> (string "2401" vs integer 2401), <strong>whitespace/case '
               'differences</strong>, <strong>missing keys</strong> producing NaN, and NaN keys matching each other.',
               'Safeguards: <code>validate="one_to_one" / "one_to_many" / "many_to_one"</code> raises <code>MergeError</code> when the relationship is '
               'violated; <code>indicator=True</code> shows unmatched rows; compare row counts before and after.'),
        tags('validate', 'MergeError', 'row explosion', 'indicator', 'data quality'),
    ),
    analogy('Seating a wedding: if the guest list accidentally has <strong>your uncle twice</strong> and the table plan also lists him at two tables, a '
            'naive matching gives him <strong>four seats</strong>. validate is the usher who says "one person, one seat" and stops the process.'),
    merge_pitfall_anim(),
    real_world(
        scenario('Inflated fee collection',
                 p('A report showed fee collection 18% above the bank total. Cause: the student master had duplicate rows for students who changed '
                   'centres, and the merge with payments multiplied their payments. Adding <code>validate="many_to_one"</code> turned the silent error '
                   'into an immediate MergeError that pointed at the duplicates.')),
    ),
    example(
        pdrun("""
            students = pd.DataFrame({'roll_no': [2401, 2401, 2402], 'name': ['Anuj', 'Anuj', 'Vineeta']})
            fees     = pd.DataFrame({'roll_no': [2401, 2401, 2402], 'paid': [50000, 45000, 90000]})

            m = fees.merge(students, on='roll_no')
            print(len(fees), '->', len(m), 'rows | total paid', fees['paid'].sum(), '->', m['paid'].sum())

            try:
                fees.merge(students, on='roll_no', validate='many_to_one')
            except pd.errors.MergeError as e:
                print('MergeError:', str(e).splitlines()[0])

            ok = fees.merge(students.drop_duplicates('roll_no'), on='roll_no', validate='many_to_one')
            print(len(ok), 'rows | total paid', ok['paid'].sum())
            print()

            a = pd.DataFrame({'roll_no': ['2401', '2402'], 'x': [1, 2]})     # strings from a CSV
            b = pd.DataFrame({'roll_no': [2401, 2402], 'y': [3, 4]})         # ints from a database
            try:
                a.merge(b, on='roll_no')
            except ValueError as e:
                print('ValueError:', str(e).split('. ')[0])
            print(a.astype({'roll_no': 'int64'}).merge(b, on='roll_no'))
        """),
        title='Example: Row Explosion, validate, and Key dtypes'),
    steps(
        ('Profile keys first', '<code>df[key].is_unique</code>, <code>df[key].duplicated().sum()</code>, dtype on both sides.'),
        ('Normalise keys', 'Same dtype; <code>str.strip().str.upper()</code> for codes.'),
        ('Declare the relationship', '<code>validate="many_to_one"</code> for fact → dimension lookups.'),
        ('Check unmatched', '<code>indicator=True</code> and count left_only / right_only.'),
        ('Check totals', 'Sum of a measure before and after must be equal for a lookup join.'),
        title='Steps for a Safe Merge'),
    crossq(
        ('What validate values exist?', '"one_to_one" ("1:1"), "one_to_many" ("1:m"), "many_to_one" ("m:1"), "many_to_many" ("m:m", no check).'),
        ('Do NaN keys match in merge?', 'Yes: unlike SQL, pandas matches NaN with NaN in merge keys. Drop or fill missing keys first.'),
        ('How do you detect a many-to-many merge after the fact?', 'Row count larger than both inputs, or the total of a measure from one side increased.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you compute running totals, previous values and moving averages? (shift, cumsum, rolling)', 'shift, cumsum, rolling', minutes=8, cards=[
    definition(
        defbox('pandas has row-relative ("window") operations, the equivalent of SQL window functions:',),
        table(['pandas', 'Meaning', 'SQL equivalent'], [
            ['shift(1) / shift(-1)', 'previous / next row value', 'LAG / LEAD'],
            ['diff(), pct_change()', 'change from previous row', 'value - LAG(value)'],
            ['cumsum(), cummax(), cumcount()', 'running total / max / row number', 'SUM() OVER (ORDER BY …)'],
            ['rolling(n).mean()', 'moving average of last n rows', 'AVG() OVER (ROWS n-1 PRECEDING)'],
            ['expanding().mean()', 'average of all rows so far', 'AVG() OVER (UNBOUNDED PRECEDING)'],
            ['ewm(span=n).mean()', 'exponentially weighted average', '—'],
            ["groupby(key)[col].shift()/cumsum()/rolling()", 'per group', 'PARTITION BY key'],
        ]),
        tags('shift', 'diff', 'cumsum', 'rolling', 'expanding', 'window functions'),
    ),
    analogy('A cricket scoreboard: runs <strong>this over</strong> (value), <strong>last over</strong> (shift), <strong>change</strong> (diff), '
            '<strong>total so far</strong> (cumsum), and <strong>run rate over the last 5 overs</strong> (rolling mean).'),
    window_anim(),
    real_world(
        scenario('Attendance trend and improvement',
                 p('Daily attendance per batch: 7-day rolling average to smooth weekends, cumulative attendance percentage per student '
                   '(<code>groupby("roll_no")["present"].expanding().mean()</code>), and module-to-module change in each student\'s marks with '
                   '<code>groupby("roll_no")["marks"].diff()</code> to spot sudden drops.')),
    ),
    example(
        pdrun("""
            att = pd.DataFrame({'day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], 'present': [52, 55, 49, 58, 60]})
            att['prev']      = att['present'].shift(1)
            att['change']    = att['present'].diff()
            att['running']   = att['present'].cumsum()
            att['avg_3day']  = att['present'].rolling(3).mean().round(1)
            att['avg_sofar'] = att['present'].expanding().mean().round(1)
            print(att)
            print()

            tests = pd.DataFrame({'roll_no': [2401, 2401, 2401, 2402, 2402, 2402],
                                  'module':  [1, 2, 3, 1, 2, 3],
                                  'marks':   [70, 76, 61, 88, 90, 93]})
            tests['vs_prev']   = tests.groupby('roll_no')['marks'].diff()
            tests['best_yet']  = tests.groupby('roll_no')['marks'].cummax()
            tests['attempt_n'] = tests.groupby('roll_no').cumcount() + 1
            print(tests)
        """),
        title='Example: Window Operations, Overall and per Student'),
    steps(
        ('Sort first', 'Window operations follow row order: <code>sort_values(["roll_no", "date"])</code>.'),
        ('Pick the operation', 'Previous value → shift; change → diff/pct_change; running → cum*; moving → rolling.'),
        ('Group if per entity', '<code>df.groupby("roll_no")["marks"].shift()</code> so values never leak between students.'),
        ('Handle the edges', 'First rows give NaN; use <code>min_periods</code> in rolling or fill afterwards.'),
        ('Time-based windows', 'With a DatetimeIndex: <code>rolling("7D")</code> uses a calendar window, robust to missing days.'),
        title='Steps for Window Calculations'),
    crossq(
        ('Why is rolling(3).mean() NaN in the first two rows?', 'The window needs 3 values by default; <code>min_periods=1</code> computes with whatever is available.'),
        ('How do you number rows within each group?', '<code>groupby(key).cumcount() + 1</code> (like ROW_NUMBER).'),
        ('Does rolling with groupby need a reset_index?', 'groupby().rolling() returns a MultiIndex (group, original index); use <code>.reset_index(level=0, drop=True)</code> to assign back, or use transform with a lambda.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('How do you resample and analyse time-series data?', 'Time Series & resample', minutes=8, cards=[
    definition(
        defbox('With a <strong>DatetimeIndex</strong>, pandas offers time-series tools: <code>resample(rule)</code> groups rows into regular calendar '
               'periods (downsampling, like a groupby on time) or creates a finer grid (upsampling, then fill); <code>asfreq</code> conforms to a frequency '
               'without aggregation; <code>date_range</code> builds sequences; string slicing selects periods; <code>shift</code> and '
               '<code>rolling("7D")</code> work in time units.'),
        table(['Rule', 'Meaning'], [
            ["'h' / 'D'", 'hour / calendar day'],
            ["'W' ('W-SUN')", 'week ending Sunday'],
            ["'ME' / 'MS'", 'month end / month start (pandas 2.2+ names)'],
            ["'QE' / 'YE'", 'quarter end / year end'],
            ["'B'", 'business day'],
        ]),
        tags('resample', 'DatetimeIndex', 'asfreq', 'date_range', 'Grouper', 'time series'),
    ),
    analogy('Your phone\'s step counter stores <strong>every walk with a timestamp</strong>; the app shows <strong>daily bars, weekly totals and a monthly '
            'average</strong>. resample is that zoom-out button, including the days you did not walk at all (zero bars).'),
    resample_anim(),
    real_world(
        scenario('LMS login analytics',
                 p('Login events from the learning portal: <code>resample("D").size()</code> for daily activity, <code>resample("W").nunique()</code> '
                   'on roll_no for weekly active students, and days with zero logins show up explicitly, which a plain groupby on the date would hide.')),
    ),
    example(
        pdrun("""
            logins = pd.DataFrame({
                'ts': pd.to_datetime(['2026-10-01 09:05', '2026-10-01 14:30', '2026-10-02 10:10',
                                      '2026-10-04 11:00', '2026-10-08 09:45']),
                'roll_no': [2401, 2402, 2401, 2403, 2402],
                'minutes': [35, 50, 20, 65, 15],
            }).set_index('ts')

            print(logins.resample('D')['minutes'].sum().head(5))
            print()
            print(logins.resample('W').agg({'minutes': 'sum', 'roll_no': 'nunique'}))
            print()
            print(logins.loc['2026-10-01':'2026-10-02', 'minutes'])
            print()
            print(logins['minutes'].rolling('3D').sum())
        """),
        title='Example: Daily, Weekly and Time-Window Aggregations'),
    steps(
        ('Parse and index', '<code>df["ts"] = pd.to_datetime(df["ts"])</code>, <code>df = df.set_index("ts").sort_index()</code>.'),
        ('Pick the period', "<code>resample('D' | 'W' | 'ME')</code> and an aggregation per column."),
        ('Expose gaps', 'Empty periods appear; decide between 0, NaN, ffill or interpolate.'),
        ('Smooth', '<code>rolling("7D").mean()</code> on the resampled series.'),
        ('Without changing the index', '<code>df.groupby(pd.Grouper(key="ts", freq="W"))</code>.'),
        title='Steps for Time-Series Analysis'),
    crossq(
        ('resample vs groupby(df.ts.dt.date)?', 'resample creates every period in the range, including empty ones, and understands frequencies (weeks, month ends); groupby on the date only has dates that occur.'),
        ('Downsampling vs upsampling?', 'Downsampling aggregates to a coarser frequency (minutes → days); upsampling creates a finer grid (days → hours) and needs a fill method (ffill, interpolate).'),
        ('Why "ME" instead of "M"?', 'pandas 2.2 renamed month-end to "ME" (and "Q"→"QE", "Y"→"YE") to separate offsets from periods; "M" now raises an error in pandas 3.'),
    ),
]),
])
