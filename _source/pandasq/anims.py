from build import *


def _lines(x, y, lines, color='#e2e8f0', size=11, step=None, gap=16):
    return ''.join(stext(x, y + i * gap, ln, color, size, 'start', step=step).replace('<text ', '<text xml:space="preserve" ', 1)
                   for i, ln in enumerate(lines))


def _codebox(x, y, w, h, lines, color='gray', step=None, tcolor='#e2e8f0', size=11, focus=None):
    return sbox(x, y, w, h, '', '', color, step=step, fill_opacity=0.08, focus=focus) + _lines(x + 14, y + 22, lines, tcolor, size, step=step)


# ============================================================ section 1
def pandas_anim():
    elems = [
        stext(380, 24, 'pandas: load → shape → analyse → deliver', 'blue', 15, bold=True),
        sbox(20, 50, 130, 34, 'CSV / Excel', '', 'gray', step=1, size=12),
        sbox(20, 92, 130, 34, 'SQL database', '', 'gray', step=1, size=12),
        sbox(20, 134, 130, 34, 'JSON / API', '', 'gray', step=1, size=12),
        sbox(20, 176, 130, 34, 'Parquet', '', 'gray', step=1, size=12),
        sarrow(150, 67, 228, 120, 'gray', step=1), sarrow(150, 109, 228, 125, 'gray', step=1),
        sarrow(150, 151, 228, 132, 'gray', step=1), sarrow(150, 193, 228, 138, 'gray', step=1),
        sflow(150, 130, 228, 130, 'cyan', step=1),
        stable(232, 70, ['', 'name', 'course', 'marks'], [['0', 'Anuj', 'PG-DBDA', '82'], ['1', 'Vineeta', 'PG-DBDA', '91'], ['2', 'Aarshvi', 'PG-DAI', '84']],
               [30, 75, 75, 55], step=2, title='DataFrame (in memory)', title_color='blue'),
        sbox(270, 200, 160, 30, 'clean · filter · group · merge', '', 'amber', step=3, size=11),
        sarrow(467, 130, 528, 130, 'gray', step=4),
        sbox(532, 60, 210, 34, 'report (Excel / CSV)', '', 'green', step=4, size=12),
        sbox(532, 104, 210, 34, 'chart (matplotlib)', '', 'green', step=4, size=12),
        sbox(532, 148, 210, 34, 'features for ML (sklearn)', '', 'green', step=4, size=12),
        sbox(532, 192, 210, 34, 'table in a database', '', 'green', step=4, size=12),
        stext(380, 262, 'built on NumPy arrays · labelled rows and columns · one machine, data must fit in RAM', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Data arrives in many formats: CSV and Excel files, SQL tables, JSON from APIs, Parquet files from a data lake.',
        'One function call (<code>pd.read_csv</code>, <code>pd.read_sql</code>…) turns each into a <strong>DataFrame</strong>: a table with labelled rows (index) and named, typed columns.',
        'In memory you clean, filter, group, reshape and join it with short vectorised operations instead of loops.',
        'The result goes out as a report, a chart, a feature table for machine learning, or back into a database.',
        'Underneath, each column is a NumPy (or Arrow) array, which is why it is fast. pandas works on one machine, so data must fit in memory.',
    ])


def series_df_anim():
    elems = [
        stext(380, 24, 'A DataFrame is a set of Series that share one index', 'blue', 15, bold=True),
        stable(20, 60, ['idx', 'name'], [['0', 'Anuj'], ['1', 'Vineeta'], ['2', 'Aarshvi']], [40, 80], step=1, title='Series: name', title_color='purple'),
        stable(170, 60, ['idx', 'course'], [['0', 'PG-DBDA'], ['1', 'PG-DBDA'], ['2', 'PG-DAI']], [40, 80], step=1, title='Series: course', title_color='purple'),
        stable(320, 60, ['idx', 'marks'], [['0', '82'], ['1', '91'], ['2', '84']], [40, 70], step=1, title='Series: marks', title_color='purple'),
        stext(225, 190, '1-D: values + index + dtype + name', 'purple', 12, step=1),
        sarrow(440, 110, 488, 110, 'amber', step=2),
        stable(492, 60, ['index', 'name', 'course', 'marks'], [['0', 'Anuj', 'PG-DBDA', '82'], ['1', 'Vineeta', 'PG-DBDA', '91'], ['2', 'Aarshvi', 'PG-DAI', '84']],
               [48, 70, 72, 55], step=2, title='DataFrame', title_color='green'),
        stext(615, 190, '2-D: rows share the index', 'green', 12, step=2),
        stext(380, 228, "df['marks'] → Series   ·   df[['name', 'marks']] → DataFrame", 'amber', 13, step=3, focus=3, bold=True),
        stext(380, 256, 'each column has ONE dtype (int64, float64, str…); different columns can have different dtypes', 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 275, *elems), [
        'A <strong>Series</strong> is one labelled column: an array of values, an index (labels), a dtype and a name.',
        'A <strong>DataFrame</strong> is several Series glued side by side, all sharing the same row index.',
        'Selecting one column with single brackets gives a Series; a list of columns (double brackets) gives a DataFrame.',
        'Each column has one dtype, but columns can differ: like a SQL table, unlike a NumPy 2-D array.',
    ])


def alignment_anim():
    elems = [
        stext(380, 24, 'Arithmetic aligns on index labels, not positions', 'blue', 15, bold=True),
        stable(30, 70, ['label', 'value'], [['Anuj', '82'], ['Vineeta', '91'], ['Rohan', '58']], [80, 60], step=1, title='sql', title_color='purple'),
        stable(220, 70, ['label', 'value'], [['Vineeta', '88'], ['Anuj', '61'], ['Meera', '70']], [80, 60], step=1, title='spark', title_color='purple'),
        stext(395, 125, '+', 'amber', 26, step=2, bold=True),
        sarrow(372, 125, 468, 125, 'amber', step=2),
        stable(480, 70, ['label', 'sql + spark'], [['Anuj', '143.0'], ['Meera', 'NaN'], ['Rohan', 'NaN'], ['Vineeta', '179.0']], [80, 100], step=3,
               title='result (labels unioned, sorted)', title_color='green', focus_rows={1: '4', 2: '4'}),
        stext(380, 220, 'Anuj: 82 + 61 = 143 even though Anuj is row 0 in one and row 1 in the other', 'cyan', 12, step=3),
        stext(380, 245, "a label missing on one side → NaN.   sql.add(spark, fill_value=0) treats missing as 0", 'amber', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 265, *elems), [
        'Two Series hold marks for different students, in a different order.',
        'Adding them does not pair row 0 with row 0. pandas matches the <strong>index labels</strong>.',
        'Anuj is added to Anuj, Vineeta to Vineeta, whatever their position. The result index is the union of both indexes.',
        'Labels present on only one side give NaN. <code>add(..., fill_value=0)</code> or a reindex controls this. The same alignment happens when assigning a Series to a DataFrame column.',
    ])


def read_csv_anim():
    elems = [
        stext(380, 24, 'pd.read_csv: text file → typed DataFrame', 'blue', 15, bold=True),
        _codebox(20, 45, 250, 150, ['marks.csv', 'roll_no;subject;marks;exam_date', '2401;SQL;82;2026-09-20', '2402;SQL;NA;2026-09-20', '2403;ML;84;2026-09-21',
                                    '...  (2 million rows)'], 'gray', step=1),
        sarrow(270, 120, 300, 120, 'amber', step=2),
        sbox(304, 45, 200, 150, 'parser options', "sep=';'\nusecols=[...]\ndtype={'subject': 'category'}\nparse_dates=['exam_date']\nna_values=['NA']\nnrows / chunksize",
             'amber', step=2, size=12),
        sarrow(504, 120, 532, 120, 'green', step=3),
        stable(536, 70, ['roll_no', 'subject', 'marks'], [['2401', 'SQL', '82.0'], ['2402', 'SQL', 'NaN'], ['2403', 'ML', '84.0']], [65, 70, 65], step=3,
               title='DataFrame', title_color='green'),
        stext(636, 190, 'int64 · category · float64', 'green', 11, step=3),
        stext(380, 228, 'wrong sep → one big column · no dtype → pandas guesses (and uses more memory)', 'red', 12, step=4, focus=4),
        stext(380, 252, 'same idea: read_excel, read_json, read_parquet, read_sql, read_html', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'A CSV is plain text: a header line and delimiter-separated values. pandas has to guess types unless you tell it.',
        'Options control parsing: delimiter, which columns to load, column dtypes, which columns are dates, which strings mean missing, how many rows.',
        'The result is a DataFrame with real types: integers, categories, floats with NaN for missing values, datetimes.',
        'Most read_csv bugs come from a wrong separator, a wrong header row or guessed types. Check with <code>df.info()</code> straight after loading.',
        'Every format has a matching reader, and a matching writer (<code>to_csv</code>, <code>to_parquet</code>…).',
    ])


def inspect_anim():
    elems = [
        stext(380, 24, 'First five minutes with a new DataFrame', 'blue', 15, bold=True),
        sbox(20, 50, 170, 54, 'df.shape', '(9, 3) rows × cols', 'blue', step=1, size=13),
        sbox(20, 112, 170, 54, 'df.head() / tail()', 'look at real rows', 'blue', step=1, size=13),
        sbox(205, 50, 170, 116, 'df.info()', 'columns, dtypes\nnon-null counts\nmemory usage', 'purple', step=2, size=13),
        sbox(390, 50, 170, 116, 'df.describe()', 'count, mean, std\nmin, quartiles, max\n(numeric columns)', 'green', step=3, size=13),
        sbox(575, 50, 170, 54, 'isna().sum()', 'missing per column', 'amber', step=4, size=13),
        sbox(575, 112, 170, 54, 'value_counts()', 'frequency of values', 'amber', step=4, size=13),
        stext(380, 200, 'marks: count 8 of 9 → one missing value · object dtype where you expected numbers → bad rows', 'red', 12, step=5, focus=5),
        stext(380, 226, 'df.nunique() · df.duplicated().sum() · df.dtypes · df.memory_usage(deep=True)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        '<code>shape</code> tells you the size; <code>head()</code>/<code>tail()</code>/<code>sample()</code> show actual rows.',
        '<code>info()</code> lists every column with its dtype and non-null count, plus memory used.',
        '<code>describe()</code> gives summary statistics; <code>describe(include="all")</code> adds text columns.',
        '<code>isna().sum()</code> counts missing values per column; <code>value_counts()</code> shows category frequencies and typos.',
        'What to look for: counts lower than the row count (missing data), text dtypes on numeric columns (bad values such as "AB" for absent), duplicates and outliers.',
    ])


# ============================================================ section 2
_ROWS5 = [['2401', 'Anuj', 'PG-DBDA', '82'], ['2402', 'Vineeta', 'PG-DBDA', '91'], ['2403', 'Aarshvi', 'PG-DAI', '84'],
          ['2404', 'Rohan', 'PG-DAC', '58'], ['2405', 'Meera', 'PG-DBDA', '75']]


def loc_iloc_anim():
    elems = [
        stext(380, 24, 'loc = by label · iloc = by position', 'blue', 15, bold=True),
        stext(30, 62, 'position →', 'gray', 10, anchor='start'),
        stext(118, 62, '0', 'gray', 10), stext(188, 62, '1', 'gray', 10), stext(258, 62, '2', 'gray', 10),
        stable(20, 70, ['index', 'name', 'course', 'marks'], _ROWS5, [60, 70, 70, 70], title=None,
               focus_rows={1: '2', 2: '2', 3: '2'}),
        stext(60, 245, 'index labels: 2401…2405 (roll_no)', 'gray', 11, anchor='start'),
        _codebox(320, 60, 420, 50, ["df.loc[2402:2404, 'name':'marks']", '→ labels 2402, 2403, 2404 (end INCLUDED)'], 'green', step=2, tcolor='#86efac'),
        _codebox(320, 118, 420, 50, ['df.iloc[0:2, 0:2]', '→ positions 0, 1 (end EXCLUDED, like Python)'], 'purple', step=3, tcolor='#c4b5fd'),
        _codebox(320, 176, 420, 50, ["df.loc[df['marks'] > 80, 'name']", '→ boolean mask + column label'], 'amber', step=4, tcolor='#fde68a'),
        stext(380, 268, "df['name'] → column · df[0:2] → rows by position · df.at[2402, 'marks'] → one cell (fast)", 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'The DataFrame has roll numbers as its index. Rows have both a <strong>label</strong> (2401…) and a <strong>position</strong> (0, 1, 2…).',
        '<code>loc</code> selects by <strong>label</strong>. Slices include the end label: 2402:2404 returns three rows.',
        '<code>iloc</code> selects by integer <strong>position</strong>. Slices exclude the end, exactly like Python lists.',
        '<code>loc</code> also accepts a boolean mask for rows, so filtering and choosing columns happen in one step.',
        'Plain <code>[]</code> selects columns by name (or rows when given a slice/mask); <code>at</code>/<code>iat</code> are fast single-cell versions.',
    ])


def filter_anim():
    elems = [
        stext(380, 24, 'Boolean filtering: build a mask, keep the True rows', 'blue', 15, bold=True),
        stable(20, 60, ['name', 'course', 'marks'], [r[1:] for r in _ROWS5], [70, 75, 55], step=1, title='df', title_color='blue'),
        stable(250, 60, ['mask'], [['True'], ['True'], ['False'], ['False'], ['True']], [80], step=2, title='is DBDA?', title_color='purple',
               focus_rows={0: '2', 1: '2', 4: '2'}),
        stable(350, 60, ['mask'], [['True'], ['True'], ['True'], ['False'], ['False']], [80], step=3, title='> 80?', title_color='purple'),
        stext(450, 130, '&', 'amber', 22, step=3, bold=True),
        sarrow(440, 145, 498, 145, 'amber', step=4),
        stable(505, 60, ['name', 'course', 'marks'], [['Anuj', 'PG-DBDA', '82'], ['Vineeta', 'PG-DBDA', '91']], [70, 75, 55], step=4, title='result', title_color='green'),
        stext(380, 245, "df[(df['course'] == 'PG-DBDA') & (df['marks'] > 80)]", 'amber', 13, step=5, bold=True, focus=5),
        stext(380, 270, 'use & | ~ (not and/or/not) and put each condition in brackets · or: df.query("course == \'PG-DBDA\' and marks > 80")', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'Start from the full DataFrame.',
        'A comparison on a column returns a <strong>boolean Series</strong> (a mask) with one True/False per row.',
        'Conditions are combined element-wise with <code>&amp;</code> (and), <code>|</code> (or), <code>~</code> (not).',
        'Indexing the DataFrame with the mask keeps only the rows where it is True. The original index labels are kept.',
        'Brackets are required because <code>&amp;</code> binds tighter than <code>==</code>. Python\'s <code>and</code> raises "truth value of a Series is ambiguous". <code>query()</code> is a readable alternative.',
    ])


def columns_anim():
    elems = [
        stext(380, 24, 'Adding, changing and dropping columns', 'blue', 15, bold=True),
        stable(20, 60, ['name', 'marks'], [['Anuj', '82'], ['Vineeta', '91'], ['Rohan', '58']], [80, 60], step=1, title='df', title_color='blue'),
        stable(200, 60, ['name', 'marks', 'pct'], [['Anuj', '82', '68.3'], ['Vineeta', '91', '75.8'], ['Rohan', '58', '48.3']], [80, 60, 60], step=2,
               title="df['pct'] = df['marks'] / 120 * 100", title_color='green'),
        stable(440, 60, ['name', 'marks', 'pct', 'result'], [['Anuj', '82', '68.3', 'PASS'], ['Vineeta', '91', '75.8', 'PASS'], ['Rohan', '58', '48.3', 'FAIL']],
               [80, 50, 50, 70], step=3, title="np.where(marks >= 60, 'PASS', 'FAIL')", title_color='amber', focus_rows={2: '3'}),
        _codebox(20, 180, 350, 70, ["df.assign(grade=lambda d: ...)   # new copy", "df.rename(columns={'marks': 'score'})", "df.drop(columns=['pct'])"], 'purple', step=4, tcolor='#c4b5fd'),
        stext(560, 200, 'whole-column operations (vectorised)', 'cyan', 12, step=5),
        stext(560, 222, 'no for-loop over rows', 'cyan', 12, step=5),
        stext(560, 244, 'assign/rename/drop return a NEW DataFrame', 'amber', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'Start with a DataFrame of names and marks.',
        'Assigning to a new column name creates it; the expression is computed for all rows at once.',
        'Conditional values come from <code>np.where</code> (two outcomes), <code>np.select</code> (several) or <code>pd.cut</code> (ranges).',
        '<code>assign</code>, <code>rename</code> and <code>drop</code> return a new DataFrame, which makes them easy to chain.',
        'Everything is vectorised: never loop over rows to compute a column.',
    ])


def sort_anim():
    elems = [
        stext(380, 24, 'Sorting, ranking and top-N', 'blue', 15, bold=True),
        stable(20, 60, ['name', 'course', 'marks'], [r[1:] for r in _ROWS5], [70, 75, 55], step=1, title='df', title_color='blue'),
        stable(260, 60, ['name', 'course', 'marks'], [['Vineeta', 'PG-DBDA', '91'], ['Aarshvi', 'PG-DAI', '84'], ['Anuj', 'PG-DBDA', '82'],
                                                     ['Meera', 'PG-DBDA', '75'], ['Rohan', 'PG-DAC', '58']], [70, 75, 55], step=2,
               title="sort_values('marks', ascending=False)", title_color='green'),
        stable(520, 60, ['name', 'marks'], [['Vineeta', '91'], ['Aarshvi', '84']], [80, 60], step=3, title="nlargest(2, 'marks')", title_color='amber'),
        stable(520, 170, ['name', 'rank'], [['Vineeta', '1'], ['Anuj', '2']], [80, 60], step=4, title='rank within course', title_color='purple'),
        stext(380, 270, "sort_values(['course', 'marks'], ascending=[True, False]) · sort_index() · rank(method='dense')", 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'The original order is the order rows were loaded.',
        '<code>sort_values</code> orders by one or more columns and keeps the index labels attached to their rows.',
        '<code>nlargest</code> / <code>nsmallest</code> return the top N without sorting everything.',
        '<code>rank</code> numbers rows by value; with <code>groupby(...).rank()</code> it ranks inside each group (Vineeta first in PG-DBDA).',
        'Multiple keys take a list for <code>ascending</code>; <code>method</code> decides how ties are ranked (average, min, dense, first).',
    ])


def cow_anim():
    elems = [
        stext(380, 24, 'Copy vs view and Copy-on-Write (pandas 3)', 'blue', 15, bold=True),
        sbox(20, 55, 170, 60, 'df', 'original data', 'blue', step=1),
        sbox(250, 55, 220, 60, "sub = df[df['marks'] > 80]", 'shares data until written', 'purple', step=2, size=12),
        sarrow(190, 85, 248, 85, 'gray', step=2),
        sbox(530, 55, 210, 60, "sub['marks'] = 0", 'sub copies itself first', 'amber', step=3, size=12),
        sarrow(470, 85, 528, 85, 'gray', step=3),
        stext(380, 145, 'df is NEVER changed through sub (pandas 3: always; pandas 1/2: "it depends" + SettingWithCopyWarning)', 'green', 12, step=3),
        sbox(20, 170, 330, 56, "df[df['marks'] > 80]['marks'] = 0", 'does nothing → ChainedAssignmentError', 'red', step=4, size=12, focus=4),
        sbox(400, 170, 340, 56, "df.loc[df['marks'] > 80, 'marks'] = 0", 'one step → df updated ✔', 'green', step=5, size=12, focus=5),
        stext(380, 255, 'rule: to change df, index df once with .loc; to get an independent subset, call .copy() explicitly when you need clarity', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'Start with a DataFrame.',
        'Filtering creates <code>sub</code>. Under Copy-on-Write it shares memory with <code>df</code> (cheap) until one of them is modified.',
        'Writing to <code>sub</code> makes it copy its data first, so <code>df</code> stays unchanged. In pandas 1.x/2.x this was unpredictable and raised <code>SettingWithCopyWarning</code>.',
        'Chained indexing like <code>df[mask]["col"] = value</code> writes to a temporary object and never updates <code>df</code>. pandas 3 warns with <code>ChainedAssignmentError</code>.',
        'Correct way: a single <code>.loc[rows, col] = value</code> on the original DataFrame.',
    ])


# ============================================================ section 3
def missing_anim():
    elems = [
        stext(380, 24, 'Missing values: find → decide → fix', 'blue', 15, bold=True),
        stable(20, 60, ['name', 'marks', 'city'], [['Anuj', '82', 'Pune'], ['Vineeta', 'NaN', 'Navi Mumbai'], ['Rohan', '58', '<NA>'], ['Meera', 'NaN', 'Pune']],
               [70, 60, 95], step=1, title='df', title_color='blue', focus_rows={1: '2', 2: '2', 3: '2'}),
        stext(132, 214, 'isna().sum() → marks 2, city 1', 'amber', 12, step=2, bold=True),
        sbox(290, 55, 140, 40, 'dropna()', 'drop rows/cols', 'red', step=3, size=12),
        sbox(290, 103, 140, 40, 'fillna(value)', 'constant / mean', 'green', step=3, size=12),
        sbox(290, 151, 140, 40, 'ffill / bfill', 'carry last value', 'purple', step=3, size=12),
        sbox(290, 199, 140, 40, 'interpolate()', 'estimate between', 'cyan', step=3, size=12),
        sarrow(432, 123, 478, 123, 'green', step=4),
        stable(482, 60, ['name', 'marks', 'city'], [['Anuj', '82', 'Pune'], ['Vineeta', '70', 'Navi Mumbai'], ['Rohan', '58', 'Unknown'], ['Meera', '70', 'Pune']],
               [70, 60, 95], step=4, title="fillna({'marks': mean, 'city': 'Unknown'})", title_color='green'),
        stext(600, 214, 'mean of 82 and 58 = 70', 'green', 11, step=4),
        stext(380, 262, 'NaN, None, NaT, pd.NA all count as missing · aggregations skip them (skipna=True)', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Real data has gaps: absent students, cities not entered.',
        '<code>isna()</code> marks every missing cell; <code>.sum()</code> counts them per column.',
        'Choose a strategy per column: drop the rows, fill with a constant or statistic, carry the previous value forward (time series), or interpolate.',
        'Here marks are filled with the column mean and city with "Unknown". A dict lets each column get its own fill value.',
        'pandas treats NaN, None, NaT (dates) and pd.NA as missing, and functions such as mean() and sum() skip them by default.',
    ])


def duplicates_anim():
    elems = [
        stext(380, 24, 'Duplicates: exact rows vs duplicate keys', 'blue', 15, bold=True),
        stable(20, 60, ['roll_no', 'subject', 'marks', 'loaded_at'], [['2401', 'SQL', '82', '09-20'], ['2401', 'SQL', '82', '09-20'], ['2402', 'SQL', '85', '09-20'],
                                                                      ['2402', 'SQL', '91', '09-25']], [65, 65, 55, 75], step=1, title='raw (4 rows)', title_color='blue',
               focus_rows={1: '2', 3: '3'}),
        stext(150, 210, 'row 1 = row 0 exactly → duplicated() True', 'amber', 11, step=2),
        stext(150, 230, '2402 SQL twice (re-evaluation) → same key', 'purple', 11, step=3),
        sarrow(290, 120, 340, 120, 'gray', step=4),
        _codebox(345, 55, 395, 100, ['df.drop_duplicates()                # exact rows', '', "df.sort_values('loaded_at')", "  .drop_duplicates(['roll_no', 'subject'], keep='last')"],
                 'green', step=4, tcolor='#86efac'),
        stable(400, 175, ['roll_no', 'subject', 'marks'], [['2401', 'SQL', '82'], ['2402', 'SQL', '91']], [70, 70, 60], step=5, title='result: latest per key', title_color='green'),
        stext(380, 270, 'keep="first" (default) · "last" · False (drop all copies) · duplicated() returns the mask', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'A marks file loaded twice and a re-evaluation produce repeated data.',
        'Row 1 is an exact copy of row 0: <code>duplicated()</code> marks it True.',
        'Roll 2402 has two SQL rows with different marks: not exact duplicates, but duplicate <strong>keys</strong>.',
        '<code>drop_duplicates()</code> removes exact copies; with <code>subset=[keys]</code> and <code>keep="last"</code> after sorting by load time, the latest version of each key survives.',
        'Result: one row per student per subject, the re-evaluated 91 kept.',
    ])


def dtypes_anim():
    elems = [
        stext(380, 24, 'Fixing dtypes: text that should be numbers, dates, categories', 'blue', 15, bold=True),
        stable(20, 60, ['column', 'raw dtype', 'sample'], [['marks', 'str', "'82', 'AB'"], ['fee', 'str', "'95,000'"], ['joined', 'str', "'2026-08-01'"],
                                                           ['course', 'str', "'PG-DBDA' ×1M"], ['roll_no', 'float64', '2401.0']], [70, 70, 110], step=1, title='as loaded', title_color='red'),
        sarrow(275, 125, 318, 125, 'amber', step=2),
        _codebox(320, 55, 250, 145, ["pd.to_numeric(s, errors='coerce')", "s.str.replace(',', '').astype(int)", 'pd.to_datetime(s)', "s.astype('category')", "s.astype('Int64')"],
                 'amber', step=2, tcolor='#fde68a'),
        stable(590, 60, ['dtype'], [['float64'], ['int64'], ['datetime64'], ['category'], ['Int64']], [150], step=3, title='after', title_color='green'),
        stext(380, 230, "'AB' → NaN with errors='coerce' (instead of an exception) · category: 1M strings stored once + small codes", 'cyan', 12, step=4),
        stext(380, 255, 'Int64 (capital I) = nullable integer: keeps 2401 as integer even with missing values', 'purple', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'Columns often load with the wrong type: marks with "AB" become text, fees with commas become text, dates stay text, integers with gaps become floats.',
        'Each has a converter: <code>to_numeric</code>, string clean-up then <code>astype</code>, <code>to_datetime</code>, <code>astype("category")</code>.',
        'After conversion the columns have proper numeric, datetime and categorical dtypes, so maths, date filters and grouping work.',
        '<code>errors="coerce"</code> turns unparseable values into NaN instead of failing; category saves memory for repeated text.',
        'The nullable <code>Int64</code> dtype stores integers with missing values (pd.NA) instead of converting them to float.',
    ])


def str_anim():
    elems = [
        stext(380, 24, 'The .str accessor: string functions on a whole column', 'blue', 15, bold=True),
        stable(20, 60, ['city (raw)'], [['  mumbai'], ['MUMBAI '], ['Navi-Mumbai'], ['Pune']], [130], step=1, title='raw', title_color='red'),
        sarrow(152, 120, 198, 120, 'amber', step=2),
        _codebox(200, 55, 290, 120, ['s.str.strip()', "  .str.replace('-', ' ')", '  .str.title()', '', "s.str.contains('mumbai', case=False)"], 'amber', step=2, tcolor='#fde68a'),
        sarrow(490, 120, 538, 120, 'green', step=3),
        stable(540, 60, ['city', 'is_mumbai'], [['Mumbai', 'True'], ['Mumbai', 'True'], ['Navi Mumbai', 'True'], ['Pune', 'False']], [110, 80], step=3, title='clean', title_color='green'),
        stext(380, 210, "split / extract: s.str.split('@').str[1] → email domain · s.str.extract(r'(\\d{4})') → roll number", 'purple', 12, step=4),
        stext(380, 238, 'vectorised: no loop · missing values stay missing instead of raising errors', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 260, *elems), [
        'Text typed by people is inconsistent: spaces, case, separators.',
        'Every Python string method is available on a column through <code>.str</code>, and calls can be chained.',
        'Result: one spelling per city, and a boolean column from <code>str.contains</code> that can be used as a filter.',
        '<code>split</code>, <code>extract</code> (regex groups), <code>startswith</code>, <code>len</code>, <code>pad</code>, <code>slice</code> work the same way.',
        'All operate on the whole column and pass missing values through.',
    ])


def datetime_anim():
    elems = [
        stext(380, 24, 'Dates: parse once, then use .dt and date arithmetic', 'blue', 15, bold=True),
        stable(20, 60, ['joined (text)'], [['01-08-2026'], ['15-08-2026'], ['03-09-2026']], [130], step=1, title='raw', title_color='red'),
        sarrow(152, 105, 198, 105, 'amber', step=2),
        sbox(200, 70, 230, 70, 'pd.to_datetime(s, format=…)', "format='%d-%m-%Y' or dayfirst=True", 'amber', step=2, size=12),
        sarrow(430, 105, 478, 105, 'green', step=3),
        stable(480, 60, ['joined', 'month', 'weekday', 'days_in'], [['2026-08-01', '8', 'Sat', '73'], ['2026-08-15', '8', 'Sat', '59'], ['2026-09-03', '9', 'Thu', '40']],
               [90, 50, 65, 60], step=3, title='.dt parts and date maths', title_color='green'),
        stext(380, 200, "filter: df[df['joined'] >= '2026-08-15']  ·  df['joined'] + pd.Timedelta(days=180)  →  course end", 'purple', 12, step=4),
        stext(380, 228, "resample('W') / ('ME') on a DatetimeIndex → weekly / monthly totals", 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 250, *elems), [
        'Dates arrive as text in many formats; as text they sort wrongly and cannot be subtracted.',
        '<code>pd.to_datetime</code> parses them; giving <code>format</code> is faster and avoids day/month mix-ups (01-08 is 1 August in India).',
        'The <code>.dt</code> accessor extracts parts (year, month, weekday) and subtracting dates gives Timedeltas.',
        'Datetime columns can be compared with date strings and shifted with <code>Timedelta</code> or <code>DateOffset</code>.',
        'With a DatetimeIndex, <code>resample</code> groups by calendar period, the basis of time-series reporting.',
    ])


# ============================================================ section 4
def groupby_anim():
    elems = [
        stext(380, 24, 'groupby = split → apply → combine', 'blue', 15, bold=True),
        stable(20, 60, ['course', 'marks'], [['PG-DBDA', '82'], ['PG-DAI', '84'], ['PG-DBDA', '91'], ['PG-DAC', '58'], ['PG-DBDA', '75'], ['PG-DAI', '72']],
               [80, 60], step=1, title='df', title_color='blue'),
        sarrow(162, 140, 208, 95, 'gray', step=2), sarrow(162, 140, 208, 200, 'gray', step=2), sarrow(162, 140, 208, 275, 'gray', step=2),
        stable(212, 48, ['PG-DBDA'], [['82'], ['91'], ['75']], [90], step=2, title_color='green'),
        stable(212, 162, ['PG-DAI'], [['84'], ['72']], [90], step=2, title_color='purple'),
        stable(212, 250, ['PG-DAC'], [['58']], [90], step=2, title_color='amber'),
        sbox(345, 140, 140, 60, 'apply', 'mean() to each group', 'amber', step=3, size=13),
        sarrow(304, 100, 343, 160, 'gray', step=3), sarrow(304, 200, 343, 170, 'gray', step=3), sarrow(304, 275, 343, 180, 'gray', step=3),
        sarrow(485, 170, 528, 170, 'green', step=4),
        stable(532, 110, ['course', 'mean'], [['PG-DAC', '58.0'], ['PG-DAI', '78.0'], ['PG-DBDA', '82.67']], [90, 70], step=4, title='combine', title_color='green'),
        stext(612, 245, "df.groupby('course')['marks'].mean()", 'cyan', 12, step=4),
        stext(565, 280, 'keys become the index (as_index=False keeps a column)', 'gray', 11, step=5),
    ]
    return anim(canvas(760, 315, *elems), [
        'Rows of several courses are mixed together.',
        '<strong>Split</strong>: groupby partitions the rows by the key value, one group per course.',
        '<strong>Apply</strong>: a function (here mean) runs on each group independently.',
        '<strong>Combine</strong>: results are stitched into one Series/DataFrame indexed by the group key, like SQL GROUP BY.',
        'Group keys become the index; <code>as_index=False</code> or <code>reset_index()</code> turns them back into columns.',
    ])


def agg_transform_anim():
    elems = [
        stext(380, 24, 'agg reduces · transform keeps shape · filter drops groups', 'blue', 15, bold=True),
        stable(20, 60, ['course', 'marks'], [['DBDA', '82'], ['DBDA', '91'], ['DAI', '84'], ['DAI', '72'], ['DAC', '58']], [70, 55], step=1, title='df (5 rows)', title_color='blue'),
        stable(190, 60, ['course', 'mean'], [['DAC', '58.0'], ['DAI', '78.0'], ['DBDA', '86.5']], [65, 55], step=2, title='agg → 3 rows', title_color='green'),
        stable(350, 60, ['marks', 'course_mean'], [['82', '86.5'], ['91', '86.5'], ['84', '78.0'], ['72', '78.0'], ['58', '58.0']], [55, 90], step=3,
               title='transform → 5 rows', title_color='purple'),
        stable(545, 60, ['course', 'marks'], [['DBDA', '82'], ['DBDA', '91'], ['DAI', '84'], ['DAI', '72']], [70, 55], step=4,
               title='filter(len(g) >= 2)', title_color='amber'),
        stext(380, 240, "apply(func): any function per group (flexible, slowest) · agg(['mean', 'max']) / named aggregation for reports", 'cyan', 12, step=5),
        stext(380, 264, "transform → 'marks - course average', 'rank in group', group-wise fillna", 'purple', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 282, *elems), [
        'Five marks rows across three courses.',
        '<code>agg</code> reduces each group to one row: 3 courses, 3 rows.',
        '<code>transform</code> returns a result for every original row (the group value broadcast back), so it can be added as a column.',
        '<code>filter</code> keeps or drops whole groups based on a condition: courses with fewer than two marks vanish.',
        '<code>apply</code> runs any function per group. Prefer built-in agg/transform names: they run in optimised code.',
    ])


def pivot_anim():
    elems = [
        stext(380, 24, 'pivot_table: long rows → a summary grid', 'blue', 15, bold=True),
        stable(20, 60, ['name', 'subject', 'marks'], [['Anuj', 'SQL', '82'], ['Anuj', 'Spark', '61'], ['Vineeta', 'SQL', '91'], ['Vineeta', 'Spark', '88'], ['Meera', 'SQL', '75']],
               [70, 60, 55], step=1, title='long', title_color='blue'),
        sarrow(208, 130, 258, 130, 'amber', step=2),
        sbox(260, 90, 200, 80, "pivot_table(index='name',", "columns='subject',\nvalues='marks', aggfunc='mean')", 'amber', step=2, size=11),
        sarrow(460, 130, 508, 130, 'green', step=3),
        stable(510, 70, ['name', 'SQL', 'Spark'], [['Anuj', '82', '61'], ['Meera', '75', 'NaN'], ['Vineeta', '91', '88']], [70, 60, 60], step=3, title='wide', title_color='green'),
        sbox(510, 190, 190, 46, 'margins=True', "adds 'All': SQL 82.7 · Spark 74.5", 'purple', step=4, size=12),
        stext(380, 260, 'pivot (no aggregation, fails on duplicates) · pivot_table (aggregates) · crosstab (counts)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 278, *elems), [
        'Long format: one row per student per subject.',
        '<code>pivot_table</code> takes the row key (index), the column key (columns), the values and an aggregation.',
        'Each subject becomes a column; missing combinations become NaN (Meera has no Spark mark).',
        '<code>margins=True</code> adds an "All" row/column with totals using the same aggregation.',
        'Choose: <code>pivot</code> just reshapes and needs unique pairs, <code>pivot_table</code> aggregates duplicates, <code>crosstab</code> counts frequencies.',
    ])


def melt_anim():
    elems = [
        stext(380, 24, 'melt (wide → long) and pivot (long → wide)', 'blue', 15, bold=True),
        stable(20, 60, ['name', 'SQL', 'Spark', 'ML'], [['Anuj', '82', '61', '70'], ['Vineeta', '91', '88', '79']], [70, 50, 50, 50], step=1, title='wide (Excel style)', title_color='blue'),
        sarrow(245, 95, 300, 95, 'amber', step=2), stext(272, 85, 'melt', 'amber', 11, step=2),
        stable(305, 60, ['name', 'subject', 'marks'], [['Anuj', 'SQL', '82'], ['Anuj', 'Spark', '61'], ['Anuj', 'ML', '70'], ['Vineeta', 'SQL', '91'],
                                                      ['Vineeta', 'Spark', '88'], ['Vineeta', 'ML', '79']], [70, 60, 55], step=2, title='long (tidy)', title_color='green'),
        sarrow(500, 140, 545, 140, 'purple', step=3), stext(522, 130, 'pivot', 'purple', 11, step=3),
        stable(550, 60, ['name', 'SQL', 'Spark', 'ML'], [['Anuj', '82', '61', '70'], ['Vineeta', '91', '88', '79']], [65, 45, 45, 40], step=3, title='back to wide', title_color='purple'),
        stext(380, 260, 'stack / unstack do the same with index levels · long for groupby/plots/DB, wide for reports', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 278, *elems), [
        'Spreadsheets usually store one column per subject: wide format.',
        '<code>melt(id_vars="name", var_name="subject", value_name="marks")</code> turns subject columns into rows: long, tidy format, one observation per row.',
        '<code>pivot(index="name", columns="subject", values="marks")</code> goes back to wide.',
        '<code>stack()</code>/<code>unstack()</code> do the same between columns and index levels. Long suits analysis and databases; wide suits reading.',
    ])


def multiindex_anim():
    elems = [
        stext(380, 24, 'MultiIndex: hierarchical row labels', 'blue', 15, bold=True),
        stable(20, 60, ['course', 'subject', 'avg'], [['PG-DBDA', 'SQL', '82.7'], ['', 'Spark', '74.5'], ['PG-DAI', 'ML', '84.0'], ['', 'Python', '72.0'], ['PG-DAC', 'Java', '58.0']],
               [80, 70, 55], step=1, title='groupby([course, subject])', title_color='blue'),
        _codebox(240, 55, 260, 120, ["s.loc['PG-DBDA']            # level 0", "s.loc[('PG-DBDA', 'SQL')]   # both", "s.xs('SQL', level='subject')", "s.unstack('subject')"], 'amber', step=2, tcolor='#fde68a'),
        stable(505, 60, ['course', 'Java', 'ML', 'Python', 'SQL', 'Spark'], [['PG-DAC', '58', '', '', '', ''], ['PG-DAI', '', '84', '72', '', ''], ['PG-DBDA', '', '', '', '82.7', '74.5']],
               [62, 36, 32, 46, 38, 40], step=3, title='unstack → grid (blank = NaN)', title_color='green', ),
        stext(380, 230, 'reset_index() flattens it back to ordinary columns: often the simplest option', 'purple', 12, step=4, focus=4),
        stext(380, 255, 'columns can be a MultiIndex too: agg({"marks": ["mean", "max"]}) → ("marks","mean")', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'Grouping by two keys gives a two-level index: course, then subject within course.',
        'Select by the outer level, by a tuple of both levels, or by an inner level with <code>xs</code>.',
        '<code>unstack</code> moves an inner level to the columns: a quick cross-tab.',
        'Many teams flatten with <code>reset_index()</code>; multi-level column names after agg can be joined with "_".',
    ])


# ============================================================ section 5
def merge_anim():
    elems = [
        stext(380, 24, 'merge: SQL-style joins on key columns', 'blue', 15, bold=True),
        stable(20, 55, ['roll_no', 'name'], [['2401', 'Anuj'], ['2402', 'Vineeta'], ['2407', 'Isha']], [65, 75], step=1, title='students (left)', title_color='blue',
               focus_rows={2: '3'}),
        stable(200, 55, ['roll_no', 'marks'], [['2401', '82'], ['2402', '91'], ['2499', '40']], [65, 55], step=1, title='marks (right)', title_color='purple',
               focus_rows={2: '4'}),
        stable(370, 55, ['roll_no', 'name', 'marks'], [['2401', 'Anuj', '82'], ['2402', 'Vineeta', '91']], [60, 65, 50], step=2, title="how='inner'", title_color='green'),
        stable(570, 55, ['roll_no', 'name', 'marks'], [['2401', 'Anuj', '82'], ['2402', 'Vineeta', '91'], ['2407', 'Isha', 'NaN']], [60, 65, 50], step=3,
               title="how='left'", title_color='amber', focus_rows={2: '3'}),
        stable(370, 185, ['roll_no', 'name', 'marks', '_merge'], [['2401', 'Anuj', '82', 'both'], ['2402', 'Vineeta', '91', 'both'], ['2407', 'Isha', 'NaN', 'left_only'],
                                                                 ['2499', 'NaN', '40', 'right_only']], [55, 60, 45, 80], step=4, title="how='outer', indicator=True", title_color='red'),
        stext(185, 215, "right: all marks rows · cross: every pair", 'gray', 11, step=4),
        stext(185, 250, "students.merge(marks, on='roll_no', how='left')", 'cyan', 12, step=5, bold=True, focus=5),
        stext(185, 275, 'left_on/right_on when names differ · suffixes for clashes', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 325, *elems), [
        'Two tables share the key roll_no. Isha (2407) has no marks; 2499 has marks but no student record.',
        '<strong>inner</strong> keeps only keys present in both: Anuj and Vineeta.',
        '<strong>left</strong> keeps every student; Isha gets NaN marks. This is the most common join for enriching a main table.',
        '<strong>outer</strong> keeps everything; <code>indicator=True</code> adds <code>_merge</code> showing where each row came from: perfect for reconciliation.',
        'Syntax mirrors SQL: <code>on</code> for the key, <code>how</code> for the join type, <code>left_on</code>/<code>right_on</code> and <code>suffixes</code> when needed.',
    ])


def concat_anim():
    elems = [
        stext(380, 24, 'concat stacks · merge matches keys · join matches the index', 'blue', 15, bold=True),
        stable(20, 55, ['roll_no', 'marks'], [['2401', '82'], ['2402', '91']], [65, 55], step=1, title='kharghar.csv', title_color='blue'),
        stable(20, 160, ['roll_no', 'marks'], [['2403', '84'], ['2404', '58']], [65, 55], step=1, title='juhu.csv', title_color='purple'),
        sarrow(142, 120, 188, 120, 'amber', step=2),
        stable(190, 55, ['roll_no', 'marks', 'centre'], [['2401', '82', 'Kharghar'], ['2402', '91', 'Kharghar'], ['2403', '84', 'Juhu'], ['2404', '58', 'Juhu']],
               [60, 50, 75], step=2, title='pd.concat([k, j], ignore_index=True)', title_color='green'),
        sbox(420, 55, 320, 60, "concat(axis=1)", 'side by side, aligned on the index', 'purple', step=3, size=12),
        sbox(420, 125, 320, 60, "merge(on='roll_no')", 'columns from another table by key (any join type)', 'amber', step=4, size=12),
        sbox(420, 195, 320, 60, "left.join(right)", 'merge on the index (default how=left)', 'cyan', step=4, size=12),
        stext(283, 210, 'axis=0 (default): add rows', 'green', 11, step=2),
        stext(380, 278, 'append() was removed in pandas 2.0 → collect DataFrames in a list and concat once', 'red', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 295, *elems), [
        'Two centres send files with the same columns.',
        '<code>pd.concat</code> stacks them vertically (axis=0). <code>ignore_index=True</code> renumbers rows; <code>keys=</code> or an added column records the source.',
        'With <code>axis=1</code>, concat places objects side by side, aligning on the index.',
        '<code>merge</code> combines columns by matching key values; <code>join</code> is a shortcut that matches on the index.',
        '<code>DataFrame.append</code> no longer exists. Appending in a loop is slow anyway: build a list of frames and concat once.',
    ])


def merge_pitfall_anim():
    elems = [
        stext(380, 24, 'Merge pitfalls: duplicate keys multiply rows', 'blue', 15, bold=True),
        stable(20, 55, ['roll_no', 'name'], [['2401', 'Anuj'], ['2401', 'Anuj (dup)'], ['2402', 'Vineeta']], [65, 90], step=1, title='students: 3 rows', title_color='blue',
               focus_rows={1: '1'}),
        stable(220, 55, ['roll_no', 'subject'], [['2401', 'SQL'], ['2401', 'Spark'], ['2402', 'SQL']], [65, 65], step=1, title='marks: 3 rows', title_color='purple'),
        sarrow(352, 105, 398, 105, 'red', step=2),
        stable(400, 55, ['roll_no', 'name', 'subject'], [['2401', 'Anuj', 'SQL'], ['2401', 'Anuj', 'Spark'], ['2401', 'Anuj (dup)', 'SQL'], ['2401', 'Anuj (dup)', 'Spark'],
                                                        ['2402', 'Vineeta', 'SQL']], [60, 90, 60], step=2, title='merged: 5 rows (2×2 + 1)', title_color='red'),
        _codebox(20, 210, 350, 68, ["validate='many_to_one'   → MergeError if", "                          right keys repeat", 'indicator=True · check len() before/after'], 'green', step=3, tcolor='#86efac'),
        stext(570, 230, "key dtypes must match: '2401' (str) ≠ 2401 (int)", 'amber', 12, step=4, focus=4),
        stext(570, 255, 'NaN keys match each other in merge (unlike SQL)', 'amber', 12, step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'The student list accidentally contains roll 2401 twice. The marks table legitimately has two rows for 2401.',
        'Every left 2401 matches every right 2401: 2 × 2 = 4 rows. Sums and averages after this join are silently wrong.',
        '<code>validate="many_to_one"</code> (or one_to_one…) makes pandas raise an error instead; also compare row counts before and after.',
        'Other traps: keys with different dtypes do not match (or raise), and missing keys match each other.',
    ])


def window_anim():
    elems = [
        stext(380, 24, 'Row-relative calculations: shift, diff, cumsum, rolling', 'blue', 15, bold=True),
        stable(20, 55, ['day', 'present', 'shift(1)', 'diff()', 'cumsum()', 'rolling(3).mean()'],
               [['Mon', '52', 'NaN', 'NaN', '52', 'NaN'], ['Tue', '55', '52', '3', '107', 'NaN'], ['Wed', '49', '55', '-6', '156', '52.0'],
                ['Thu', '58', '49', '9', '214', '54.0'], ['Fri', '60', '58', '2', '274', '55.7']],
               [60, 70, 80, 70, 90, 130], step=1, title='daily attendance', title_color='blue'),
        sbox(20, 225, 160, 50, 'shift / diff', 'previous row, change', 'purple', step=2, size=12),
        sbox(195, 225, 160, 50, 'cumsum / cummax', 'running totals', 'green', step=3, size=12),
        sbox(370, 225, 170, 50, 'rolling(window)', 'moving average (last 3)', 'amber', step=4, size=12, focus=4),
        sbox(555, 225, 185, 50, 'expanding / ewm', 'all-so-far, weighted recent', 'cyan', step=5, size=12),
        stext(380, 300, "per student: df.groupby('roll_no')['marks'].shift(1) → like SQL LAG() OVER (PARTITION BY roll_no)", 'gray', 11, step=5),
    ]
    return anim(canvas(760, 315, *elems), [
        'Daily attendance counts, in date order. Each derived column looks at neighbouring rows.',
        '<code>shift(1)</code> brings the previous row\'s value (SQL LAG); <code>diff()</code> = value − previous; <code>pct_change()</code> the relative change.',
        '<code>cumsum()</code> keeps a running total; cummax/cummin/cumprod work the same way.',
        '<code>rolling(3).mean()</code> averages the current and two previous rows; the first two are NaN until the window is full (min_periods changes that).',
        '<code>expanding()</code> uses all rows so far; <code>ewm()</code> weights recent rows more. All of them work per group via groupby.',
    ])


def resample_anim():
    elems = [
        stext(380, 24, 'Time series: DatetimeIndex + resample', 'blue', 15, bold=True),
        stable(20, 55, ['timestamp', 'logins'], [['10-01 09:05', '3'], ['10-01 14:30', '5'], ['10-02 10:10', '4'], ['10-04 11:00', '6'], ['10-08 09:45', '2']],
               [100, 55], step=1, title='events (irregular)', title_color='blue'),
        sarrow(178, 120, 228, 120, 'amber', step=2),
        stable(230, 55, ['date', 'logins'], [['10-01', '8'], ['10-02', '4'], ['10-03', '0'], ['10-04', '6'], ['…', '…']], [70, 55], step=2,
               title="resample('D').sum()", title_color='green', focus_rows={2: '2'}),
        sarrow(358, 120, 408, 120, 'amber', step=3),
        stable(410, 55, ['week (ending Sun)', 'logins'], [['2026-10-04', '18'], ['2026-10-11', '2']], [120, 55], step=3, title="resample('W').sum()", title_color='purple'),
        stable(410, 168, ['month', 'logins'], [['2026-10', '20']], [120, 55], step=4, title="resample('ME').sum()", title_color='amber'),
        stext(380, 235, "missing days appear with 0 (sum) or NaN (mean) → gaps become visible · asfreq('D') = pick, no aggregation", 'cyan', 11, step=4),
        stext(380, 260, "df.loc['2026-10'] selects a month · rolling('7D') = time-based window · tz_convert for zones", 'gray', 11, step=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Events happen at irregular times. Setting the timestamp as a <strong>DatetimeIndex</strong> unlocks time-series tools.',
        '<code>resample("D").sum()</code> buckets into calendar days; days without events appear, here with 0.',
        'Change the rule to weeks (<code>"W"</code>, ending Sunday by default) or months (<code>"ME"</code>, month end) to roll up further.',
        'resample is a groupby on time: any aggregation works. <code>asfreq</code> just samples a regular grid without aggregating.',
        'Date-string selection, time-based rolling windows (<code>rolling("7D")</code>) and time zones complete the toolkit.',
    ])


# ============================================================ section 6
def vector_anim():
    elems = [
        stext(380, 24, 'Same result, three speeds (1,000,000 rows)', 'blue', 15, bold=True),
        sbox(20, 55, 230, 70, 'for row in df.iterrows()', 'Python loop, one row object per row', 'red', step=1, size=12),
        sbox(265, 55, 230, 70, 'df.apply(f, axis=1)', 'Python function called per row', 'amber', step=2, size=12),
        sbox(510, 55, 230, 70, "df['a'] * 0.4 + df['b'] * 0.6", 'one call → compiled loop over arrays', 'green', step=3, size=12, focus=3),
        scell(20, 145, 230, 26, 'seconds', '#7f1d1d', step=1),
        scell(265, 145, 230, 26, 'seconds (a bit better)', '#78350f', step=2),
        scell(510, 145, 230, 26, 'milliseconds', '#065f46', step=3),
        sbox(20, 195, 720, 46, 'why: each Python-level call costs microseconds × 1M; NumPy does the loop in C over contiguous memory (SIMD)', '', 'cyan', step=4, size=12),
        stext(380, 268, 'np.where / np.select for conditions · .str / .dt accessors · groupby built-ins · merge instead of row lookups', 'purple', 12, step=5),
    ]
    return anim(canvas(760, 285, *elems), [
        '<code>iterrows</code> builds a Series object for every row and runs Python code each time: the slowest option.',
        '<code>apply(axis=1)</code> hides the loop but still calls your Python function once per row.',
        'A vectorised expression works on whole columns in one call; the loop runs in compiled code.',
        'The difference is the per-element Python overhead, multiplied by a million rows. Typically 100–1000× faster.',
        'Almost every row-wise idea has a vectorised form: np.where/np.select for conditions, accessors for strings and dates, groupby/merge instead of lookups.',
    ])


def memory_anim():
    elems = [
        stext(380, 24, 'Shrinking a DataFrame in memory', 'blue', 15, bold=True),
        stable(20, 55, ['column', 'before', 'after', 'how'], [['roll_no', 'int64 8 B', 'int32 4 B', "downcast='integer'"], ['marks', 'float64 8 B', 'float32 4 B', "downcast='float'"],
                                                             ['course', 'object ~60 B', 'category 1 B', "astype('category')"], ['passed', 'object', 'bool 1 B', 'astype(bool)']],
               [90, 110, 110, 150], step=1, title='per value', title_color='blue', row_steps={0: 2, 1: 2, 2: 3, 3: 4}),
        sbox(510, 55, 230, 60, 'memory_usage(deep=True)', 'measure real bytes, incl. strings', 'purple', step=1, size=12),
        sbox(510, 125, 230, 70, 'category', "3 distinct courses × 1M rows\n→ 3 strings + 1M small codes", 'green', step=3, size=12, focus=3),
        stext(380, 220, 'load only what you need: usecols=[...], dtype={...} in read_csv · Parquet keeps the small types', 'cyan', 12, step=5),
        stext(380, 245, 'pandas 3 + PyArrow strings are already far smaller than Python object strings', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 265, *elems), [
        'Measure first with <code>df.memory_usage(deep=True)</code>; deep counts the actual string contents.',
        'Numbers: smaller integer and float types when the range allows (roll numbers fit in int32; marks in float32).',
        'Repeated text: <strong>category</strong> stores each distinct value once plus a small integer code per row; often a 90%+ saving.',
        'Flags: real booleans instead of "Y"/"N" strings.',
        'Best of all, never load unused columns, and store data as Parquet so the compact types are kept.',
    ])


def chunk_anim():
    elems = [
        stext(380, 24, 'A file bigger than RAM: chunks or a columnar format', 'blue', 15, bold=True),
        sbox(20, 55, 170, 150, 'exam_logs.csv', '20 GB\n200 million rows', 'gray', step=1, size=13),
        sarrow(190, 90, 238, 70, 'amber', step=2), sarrow(190, 130, 238, 130, 'amber', step=2), sarrow(190, 170, 238, 190, 'amber', step=2),
        sbox(240, 50, 150, 40, 'chunk 1 (1M rows)', '', 'amber', step=2, size=11), sbox(240, 110, 150, 40, 'chunk 2', '', 'amber', step=2, size=11),
        sbox(240, 170, 150, 40, 'chunk … n', '', 'amber', step=2, size=11),
        sarrow(390, 70, 438, 120, 'green', step=3), sarrow(390, 130, 438, 130, 'green', step=3), sarrow(390, 190, 438, 140, 'green', step=3),
        sbox(440, 95, 140, 70, 'partial results', 'groupby per chunk', 'green', step=3, size=12),
        sarrow(580, 130, 608, 130, 'green', step=4),
        sbox(610, 95, 130, 70, 'combine', 'sum of sums', 'green', step=4, size=12),
        stext(380, 240, "pd.read_csv(path, chunksize=1_000_000, usecols=[...]) → iterator of DataFrames", 'cyan', 12, step=2),
        stext(380, 265, 'Parquet: read only needed columns/row groups (columns=, filters=) · or use Polars / DuckDB / Dask / PySpark', 'purple', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'The file is larger than the machine\'s memory, so <code>read_csv</code> on it would crash.',
        '<code>chunksize</code> turns read_csv into an iterator: one manageable DataFrame at a time.',
        'Each chunk is filtered/aggregated to a small partial result.',
        'Partial results are combined (sums of sums, counts of counts; averages from sum and count, not average of averages).',
        'Better still: convert once to Parquet and read only the columns and row groups needed, or switch to an out-of-core engine.',
    ])


def map_apply_anim():
    elems = [
        stext(380, 24, 'map vs apply vs replace (and vectorised alternatives)', 'blue', 15, bold=True),
        sbox(20, 55, 235, 80, "Series.map(dict / func)", "element-wise; dict lookup\nunmatched → NaN", 'green', step=1, size=12),
        sbox(265, 55, 235, 80, "Series.replace(dict)", "element-wise; unmatched\nkept as they were", 'purple', step=2, size=12),
        sbox(510, 55, 230, 80, "DataFrame.apply(f, axis)", "f gets a whole column (axis=0)\nor row (axis=1)", 'amber', step=3, size=12),
        sbox(20, 150, 360, 60, "DataFrame.map(f)", "element-wise on every cell (was applymap, renamed in 2.1)", 'cyan', step=4, size=12),
        sbox(395, 150, 345, 60, "prefer: np.where · np.select · pd.cut · .str", 'when the logic is a condition or text rule', 'red', step=5, size=12, focus=5),
        stext(380, 240, "codes.map({'PG-DBDA': 'Big Data'}) → NaN for PG-DAC · codes.replace({...}) → PG-DAC unchanged", 'gray', 11, step=2),
    ]
    return anim(canvas(760, 260, *elems), [
        '<code>Series.map</code> transforms each value with a dict or function; values missing from the dict become NaN.',
        '<code>replace</code> also uses a dict, but leaves values not in the dict unchanged. Useful for fixing a few spellings.',
        '<code>DataFrame.apply</code> passes whole columns (default) or whole rows (<code>axis=1</code>) to the function.',
        '<code>DataFrame.map</code> (formerly <code>applymap</code>) calls a function on every single cell.',
        'All of these run Python per element/row. When the logic is a condition, a range or a string operation, the vectorised tools are much faster.',
    ])


def pandas3_anim():
    elems = [
        stext(380, 24, 'What changed: pandas 1.x → 2.x → 3.0', 'blue', 15, bold=True),
        sbox(20, 55, 230, 175, 'pandas 2.0 (2023)', "PyArrow backend optional\n(dtype_backend='pyarrow')\nnon-nanosecond datetimes\nappend() removed\nnumeric_only defaults", 'purple', step=1, size=13, top=True),
        sbox(265, 55, 230, 175, 'pandas 2.1 / 2.2', "applymap → DataFrame.map\nfillna(method=) deprecated\n'M' → 'ME' frequency names\nCoW opt-in + warn mode\nFutureWarnings for 3.0", 'amber', step=2, size=13, top=True),
        sbox(510, 55, 230, 175, 'pandas 3.0 (2026)', "Copy-on-Write always on\nno SettingWithCopyWarning\ndefault 'str' dtype (Arrow)\nanti joins in merge\nold deprecations removed", 'green', step=3, size=13, top=True, focus=3),
        stext(380, 255, 'upgrade path: run tests on 2.2 with warnings as errors → fix FutureWarnings → move to 3.0', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 275, *elems), [
        'pandas 2.0 introduced optional Apache Arrow-backed columns and removed long-deprecated APIs such as <code>append</code>.',
        'The 2.x releases renamed and deprecated APIs and added Copy-on-Write as an opt-in, preparing for 3.0.',
        'pandas 3.0 makes Copy-on-Write the only mode, stores text in a dedicated string dtype (Arrow-backed when available) and removes the deprecated APIs.',
        'Safe upgrade: fix every FutureWarning/DeprecationWarning on the last 2.x release first, then switch.',
    ])


# ============================================================ section 7
def formats_anim():
    elems = [
        stext(380, 24, 'Choosing a file format', 'blue', 15, bold=True),
        stable(20, 50, ['format', 'types kept', 'size', 'speed', 'best for'],
               [['CSV', 'no', 'large', 'slow', 'exchange, humans'], ['Excel', 'partly', 'large', 'slowest', 'business users'], ['JSON', 'partly', 'large', 'slow', 'APIs, nested data'],
                ['Parquet', 'yes', 'small', 'fast', 'analytics, data lakes'], ['SQL table', 'yes', '—', 'query', 'shared, transactional']],
               [90, 90, 70, 75, 170], step=1, title=None, row_steps={0: 1, 1: 2, 2: 2, 3: 3, 4: 4}, focus_rows={3: '3'}),
        sbox(530, 50, 210, 60, 'read_* / to_*', 'one pair per format', 'purple', step=1, size=13),
        sbox(530, 120, 210, 60, 'to_sql / read_sql', 'SQLAlchemy engine or sqlite3', 'amber', step=4, size=12),
        stext(380, 230, 'rule of thumb: CSV/Excel at the edges (people), Parquet in the middle (pipelines), SQL for shared state', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 250, *elems), [
        'CSV is universal but stores no types: every load re-parses text and guesses dtypes.',
        'Excel and JSON are convenient for people and APIs but large and slow for analytics.',
        'Parquet is columnar, compressed and typed: smaller files, much faster reads, and you can load only some columns.',
        'Databases: <code>to_sql</code> writes a DataFrame as a table, <code>read_sql</code> loads a query result.',
        'Use human-friendly formats at the edges of a pipeline and Parquet inside it.',
    ])


def sql_map_anim():
    rows = [['SELECT a, b', "df[['a', 'b']]"], ['WHERE marks > 60', "df[df['marks'] > 60]"], ['GROUP BY course', "df.groupby('course')"],
            ['HAVING count(*) > 2', 'groupby(...).filter(lambda g: len(g) > 2)'], ['ORDER BY marks DESC', "sort_values('marks', ascending=False)"],
            ['LIMIT 5', 'head(5)'], ['JOIN … ON', 'merge(…, on=…, how=…)'], ['UNION ALL', 'pd.concat([a, b])'],
            ['ROW_NUMBER() OVER (…)', 'groupby(…).cumcount() + 1']]
    return anim(canvas(760, 345,
        stext(380, 24, 'SQL → pandas', 'blue', 15, bold=True),
        stable(60, 45, ['SQL', 'pandas'], rows, [250, 390], title=None, row_steps={i: (1 if i < 3 else 2 if i < 6 else 3) for i in range(9)}),
        stext(380, 330, 'SQL describes WHAT (the engine plans); pandas runs each step eagerly in the order you write it', 'cyan', 12, step=4, focus=4),
    ), [
        'Projection, filtering and grouping map directly: a list of columns, a boolean mask, groupby.',
        'HAVING is a filter on groups; ORDER BY and LIMIT are sort_values and head.',
        'Joins are merge, UNION ALL is concat, window functions are groupby with cumcount/rank/shift/transform.',
        'Difference: SQL is declarative and optimised by the database; pandas executes each method immediately, so the order of steps matters for speed.',
    ])


def ecosystem_anim():
    elems = [
        stext(380, 24, 'pandas vs Polars vs Dask vs PySpark', 'blue', 15, bold=True),
        sbox(20, 55, 170, 150, 'pandas', 'one machine, in memory\neager, single core*\nhuge ecosystem\n≤ a few GB', 'blue', step=1, size=13, top=True),
        sbox(205, 55, 170, 150, 'Polars', 'one machine, Rust\nmulti-core, lazy\nquery optimiser\nstreaming > RAM', 'amber', step=2, size=13, top=True),
        sbox(390, 55, 170, 150, 'Dask', 'pandas API\nsplit into partitions\nlaptop or cluster\nlazy task graph', 'purple', step=3, size=13, top=True),
        sbox(575, 55, 165, 150, 'PySpark', 'cluster, JVM\nlazy, Catalyst\nTB–PB scale\npandas API on Spark', 'green', step=4, size=13, top=True),
        sarrow(100, 230, 660, 230, 'gray', step=5),
        stext(100, 250, 'MB → GB', 'gray', 11, step=5), stext(380, 250, 'GB → 100s of GB', 'gray', 11, step=5), stext(660, 250, 'TB+', 'gray', 11, step=5),
        stext(380, 275, 'start with pandas; switch when data or runtime outgrows one core / RAM, not before', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'pandas: eager, in-memory, mostly single-threaded, with the richest ecosystem (sklearn, plotting, Excel).',
        'Polars: a DataFrame library written in Rust, multi-threaded, with lazy queries optimised before running and streaming for data larger than RAM.',
        'Dask: splits a large dataset into many pandas DataFrames (partitions) and runs them in parallel, on a laptop or a cluster.',
        'PySpark: distributed processing on a cluster for terabytes; the pandas API on Spark offers pandas-like syntax.',
        'Choose by data size and team skills. For most interview and project datasets pandas is enough.',
    ])


def chaining_anim():
    elems = [
        stext(380, 24, 'Method chaining: a readable pipeline', 'blue', 15, bold=True),
        _codebox(20, 50, 330, 200, ['report = (', '    marks', '    .dropna(subset=["marks"])', '    .merge(students, on="roll_no")', '    .query("course == \'PG-DBDA\'")',
                                    '    .assign(pct=lambda d: d.marks / 100)', '    .groupby("name", as_index=False)', '    .agg(avg=("pct", "mean"))', '    .sort_values("avg", ascending=False)',
                                    '    .pipe(add_rank)', ')'], 'blue', step=1, tcolor='#e2e8f0'),
        sbox(380, 50, 360, 40, 'each method returns a new DataFrame', '', 'green', step=2, size=12),
        sbox(380, 100, 360, 40, 'no temporary variables (df1, df2, df_final…)', '', 'green', step=2, size=12),
        sbox(380, 150, 360, 50, '.pipe(func) inserts your own function', 'func(df, ...) → df', 'purple', step=3, size=12),
        sbox(380, 210, 360, 40, 'debug: comment out lines from the bottom', '', 'amber', step=4, size=12),
        stext(380, 278, 'lambda d: … in assign refers to the DataFrame at that point of the chain, not the original', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 295, *elems), [
        'The whole transformation reads top to bottom like a recipe, wrapped in parentheses so each step can be on its own line.',
        'Each method returns a new DataFrame, so no intermediate variables and no accidental reuse of a stale one.',
        '<code>pipe</code> lets custom functions join the chain: <code>df.pipe(add_rank, col="avg")</code> = <code>add_rank(df, col="avg")</code>.',
        'To debug, cut the chain at any line and look at the intermediate result. The lambda inside assign sees the DataFrame as it is at that step.',
    ])


def validate_anim():
    elems = [
        stext(380, 24, 'Testing and validating pandas code', 'blue', 15, bold=True),
        sbox(20, 55, 230, 90, 'unit tests', 'small input → expected output\npd.testing.assert_frame_equal', 'blue', step=1, size=12),
        sbox(265, 55, 230, 90, 'data checks', 'assert df.roll_no.is_unique\nmarks.between(0, 100).all()', 'amber', step=2, size=12),
        sbox(510, 55, 230, 90, 'schema libraries', 'pandera, Great Expectations\ntypes, ranges, uniqueness', 'purple', step=3, size=12),
        sarrow(135, 145, 135, 178, 'gray', step=4), sarrow(380, 145, 380, 178, 'gray', step=4), sarrow(625, 145, 625, 178, 'gray', step=4),
        sbox(20, 180, 720, 50, 'fail fast in the pipeline, before a wrong report reaches students or management', '', 'green', step=4, size=13, focus=4),
        stext(380, 258, 'check: row counts after merges · no unexpected NaN · keys unique · values in allowed sets', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'Transformation functions get pytest tests: build a tiny DataFrame, call the function, compare with <code>assert_frame_equal</code>.',
        'Data checks run on real data in the pipeline: plain asserts on uniqueness, ranges and missing values.',
        'Schema libraries such as pandera or Great Expectations declare those rules once and report every violation.',
        'Either way, the point is to stop the pipeline with a clear error instead of publishing a wrong result.',
        'The most valuable checks are cheap: counts around merges, key uniqueness, NaN counts, allowed values.',
    ])


# ============================================================ section 8
def topn_anim():
    elems = [
        stext(380, 24, 'Top N per group (and the "second highest" question)', 'blue', 15, bold=True),
        stable(20, 55, ['course', 'name', 'avg'], [['DBDA', 'Vineeta', '89.5'], ['DBDA', 'Meera', '75.0'], ['DBDA', 'Anuj', '71.5'], ['DAI', 'Aarshvi', '84.0'], ['DAI', 'Kabir', '72.0'],
                                                  ['DAC', 'Rohan', '58.0']], [55, 75, 50], step=1, title='sorted by avg desc within course', title_color='blue'),
        sbox(220, 55, 250, 70, "sort_values → groupby().head(2)", 'fast, keeps first 2 rows per group', 'green', step=2, size=12),
        sbox(220, 135, 250, 70, "rank(method='dense', ascending=False)", 'ties share a rank → rank == 2', 'purple', step=3, size=12),
        stable(500, 55, ['course', 'name', 'rank'], [['DAC', 'Rohan', '1'], ['DAI', 'Aarshvi', '1'], ['DAI', 'Kabir', '2'], ['DBDA', 'Vineeta', '1'], ['DBDA', 'Meera', '2']],
               [55, 75, 50], step=4, title='top 2 per course', title_color='green', focus_rows={2: '5', 4: '5'}),
        stext(380, 262, 'second highest = rows where dense rank == 2 (handles ties, unlike iloc[1])', 'amber', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Averages per student, sorted descending inside each course.',
        'Simplest top-N: sort, then <code>groupby(...).head(n)</code>. No apply needed.',
        'When ties matter, rank inside each group with <code>method="dense"</code> and filter on the rank.',
        'Result: at most two rows per course (DAC has only one student).',
        'The classic "second highest" question is a dense rank equal to 2, which handles ties correctly.',
    ])


def pipeline_anim():
    steps_ = [('read', 'sep, NA, dtypes', 'gray'), ('normalise', 'strip, case', 'blue'), ('types', 'numbers, dates', 'purple'),
              ('dedupe', 'latest per key', 'amber'), ('validate', 'ranges, keys', 'red'), ('save', 'Parquet + report', 'green')]
    elems = [stext(380, 24, 'Cleaning a messy export: a repeatable pipeline', 'blue', 15, bold=True)]
    for i, (t, s, c) in enumerate(steps_):
        x = 20 + i * 123
        elems.append(sbox(x, 60, 110, 70, t, s, c, step=i + 1, size=13))
        if i:
            elems.append(sarrow(x - 13, 95, x - 2, 95, 'gray', step=i + 1))
    elems += [
        stext(380, 165, "' anuj ', 'AB', '95,000', '01-08-2026', duplicates", 'red', 12, step=1),
        stext(380, 190, "→ 'Anuj', NaN, 95000, 2026-08-01, one row per student", 'green', 12, step=6),
        stext(380, 225, 'one function per step + .pipe() → rerun on next batch in seconds; log row counts at each step', 'cyan', 12, step=6, focus=6),
    ]
    return anim(canvas(760, 245, *elems), [
        'Read with the options the file needs: separator, missing-value markers, dtypes.',
        'Normalise text: trim spaces, fix case, standardise column names.',
        'Convert types: numbers with commas, "AB" to missing, dates with an explicit format.',
        'Remove duplicates, keeping the latest record per key.',
        'Validate: ranges, uniqueness, allowed values. Stop if something is wrong.',
        'Save clean data (Parquet) and the report. Written as small functions in a chain, the whole pipeline reruns on the next batch.',
    ])


def compare_anim():
    elems = [
        stext(380, 24, 'What changed between two versions of a table?', 'blue', 15, bold=True),
        stable(20, 55, ['roll_no', 'city', 'phone'], [['2401', 'Pune', '98…01'], ['2402', 'Navi Mumbai', '98…02'], ['2403', 'Mumbai', '98…03']], [60, 95, 65], step=1,
               title='last month', title_color='blue'),
        stable(260, 55, ['roll_no', 'city', 'phone'], [['2401', 'Pune', '98…01'], ['2402', 'Pune', '98…02'], ['2404', 'Thane', '98…04']], [60, 95, 65], step=1,
               title='this month', title_color='purple', focus_rows={1: '3'}),
        sbox(500, 55, 240, 40, "outer merge + indicator", 'added / removed rows', 'amber', step=2, size=12),
        sbox(500, 105, 240, 40, 'DataFrame.compare()', 'changed cells (self vs other)', 'green', step=3, size=12),
        stable(20, 185, ['change', 'roll_no', 'detail'], [['added', '2404', 'new student'], ['removed', '2403', 'left the course'], ['changed', '2402', 'city: Navi Mumbai → Pune']],
               [75, 65, 220], step=4, title='change log', title_color='green'),
        stext(600, 230, 'same idea as a snapshot /', 'gray', 11, step=4), stext(600, 248, 'SCD2 in a warehouse', 'gray', 11, step=4),
    ]
    return anim(canvas(760, 300, *elems), [
        'Two monthly extracts of the student master.',
        'An outer merge on the key with <code>indicator=True</code> finds rows only in one version: added and removed students.',
        'For keys in both, <code>compare()</code> on the aligned frames shows exactly which cells changed, old and new value side by side.',
        'Together they give a change log, the same idea as snapshots and slowly changing dimensions in a data warehouse.',
    ])


def streak_anim():
    elems = [
        stext(380, 24, 'Consecutive-day streaks ("gaps and islands")', 'blue', 15, bold=True),
        stable(20, 55, ['date', 'present', 'new_streak', 'streak_id'], [['10-01', '1', 'True', '1'], ['10-02', '1', 'False', '1'], ['10-03', '0', 'True', '2'], ['10-04', '1', 'True', '3'],
                                                                         ['10-05', '1', 'False', '3'], ['10-06', '1', 'False', '3']], [70, 70, 90, 80], step=1, title='one student', title_color='blue',
               focus_rows={3: '4', 4: '4', 5: '4'}),
        sbox(360, 55, 380, 52, 'new_streak = present != present.shift()', 'True where a run starts', 'purple', step=2, size=12),
        sbox(360, 115, 380, 52, 'streak_id = new_streak.cumsum()', 'same id for every day of a run', 'amber', step=3, size=12),
        sbox(360, 175, 380, 52, "groupby(streak_id).size() where present", 'run lengths → max = 3 days', 'green', step=4, size=12, focus=4),
        stext(380, 262, 'per student: do the same inside groupby("roll_no") · works for any "runs" problem (absences, failures)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Daily attendance flags for one student, sorted by date.',
        'Compare each day with the previous one: a change marks the start of a new run.',
        'A cumulative sum of those start flags numbers the runs: every day in the same run gets the same id.',
        'Group by run id (only present days) and count: the longest attendance streak is 3 days.',
        'The same shift-cumsum-groupby trick solves every "consecutive" question, also per student.',
    ])


def report_anim():
    elems = [
        stext(380, 24, 'End-to-end: attendance eligibility report', 'blue', 15, bold=True),
        sbox(20, 55, 150, 60, 'attendance log', '1 row per student per day', 'gray', step=1, size=12),
        sbox(20, 125, 150, 60, 'student master', 'name, course, centre', 'gray', step=1, size=12),
        sarrow(170, 85, 208, 110, 'gray', step=2), sarrow(170, 155, 208, 125, 'gray', step=2),
        sbox(210, 80, 150, 70, 'groupby + merge', 'present / total days', 'blue', step=2, size=12),
        sarrow(360, 115, 398, 115, 'gray', step=3),
        sbox(400, 80, 150, 70, 'eligible?', 'pct >= threshold', 'amber', step=3, size=12),
        sarrow(550, 115, 588, 115, 'gray', step=4),
        sbox(590, 55, 150, 60, 'Excel: sheet per course', 'formatted', 'green', step=4, size=12),
        sbox(590, 125, 150, 60, 'shortfall list', 'emailed to mentors', 'red', step=4, size=12),
        stext(380, 220, 'threshold is a parameter · days_needed = ceil(threshold × total) − present tells each student how many more days', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 240, *elems), [
        'Inputs: a daily attendance log and the student master.',
        'Aggregate present and total days per student, then merge names and courses.',
        'Compare the percentage with the course\'s minimum attendance (a parameter, not hard-coded).',
        'Outputs: an Excel workbook with one sheet per course, and the list of students below the threshold.',
        'Adding "days still needed" turns the report into an action list for mentors.',
    ])
