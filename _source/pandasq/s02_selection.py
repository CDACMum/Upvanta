from build import *
from pandasq.anims import *
from pandasq.runner import pdrun, pyshow
from pandasq.data import STUDENTS, MARKS, BOTH, data_note

S = 'Python (pandas) · uses sample data'

SECTION = dict(level='basic', title='Selecting & Modifying Data', questions=[

# ------------------------------------------------------------------ 6
Q('What is the difference between loc, iloc, at, iat and []?', 'loc vs iloc', minutes=8, cards=[
    definition(
        defbox('<strong>loc</strong> selects rows and columns by <strong>label</strong> (index values, column names, or a boolean mask). Label slices '
               '<strong>include</strong> the end.',
               '<strong>iloc</strong> selects by <strong>integer position</strong> (0, 1, 2…). Slices <strong>exclude</strong> the end, like Python lists.',
               '<strong>at / iat</strong> get or set a <strong>single cell</strong> by label / position, faster than loc/iloc. '
               '<strong>[]</strong> selects columns by name (<code>df["col"]</code>, <code>df[["a", "b"]]</code>), or rows with a slice or boolean mask.'),
        table(['Syntax', 'Selects', 'Example'], [
            ['df.loc[rows, cols]', 'by label', "df.loc[2402, 'name']"],
            ['df.iloc[rows, cols]', 'by position', 'df.iloc[0:3, 1]'],
            ['df.at[label, col]', 'one cell by label', "df.at[2402, 'marks']"],
            ['df.iat[i, j]', 'one cell by position', 'df.iat[0, 2]'],
            ["df['col'] / df[['a','b']]", 'columns', "df['marks']"],
        ]),
        tags('loc', 'iloc', 'at', 'iat', 'Indexing'),
    ),
    analogy('A cinema hall. <strong>loc</strong> is your <strong>ticket</strong>: "seat F-12", a label that stays the same however people sit. '
            '<strong>iloc</strong> is "the <strong>third seat from the left</strong> in the sixth row", a position that changes if the row is rearranged. '
            '<strong>at</strong> is walking straight to one seat without scanning the row.'),
    loc_iloc_anim(),
    real_world(
        scenario('Why it matters after filtering',
                 p('After <code>df = df[df["marks"] > 60]</code> the index is 0, 1, 2, 4, 5 (row 3 was removed). <code>df.loc[3]</code> now raises '
                   'KeyError while <code>df.iloc[3]</code> returns the student originally at label 4. Interviewers love this question because it is a '
                   'common real bug in loops that mix the two.')),
    ),
    example(
        data_note('students'),
        pdrun("""
            df = students.set_index('roll_no')

            print(df.loc[2402])                              # one row by label -> Series
            print()
            print(df.loc[2402:2404, ['name', 'course']])     # label slice: end included
            print()
            print(df.iloc[0:2, 0:2])                         # position slice: end excluded
            print()
            print(df.loc[df['centre'] == 'Juhu', 'name'])    # mask + column
            print()
            print(df.at[2405, 'city'], '|', df.iat[0, 0])    # single cells
        """, setup=STUDENTS, title=S),
        title='Example: Each Selector on the Same Data'),
    steps(
        ('Decide label or position', 'Known key (roll number, date, name) → loc; "first N rows" or "column 3" → iloc.'),
        ('Rows and columns together', '<code>df.loc[row_selector, col_selector]</code>; use <code>:</code> for all.'),
        ('Use a mask for conditions', '<code>df.loc[df["marks"] &lt; 60, "result"] = "FAIL"</code>, which selects and assigns in one step.'),
        ('Single cells in loops', 'Prefer <code>at</code>/<code>iat</code>, but first try to avoid the loop.'),
        title='Steps to Choose the Right Selector'),
    crossq(
        ('Why does df.loc[0:2] return three rows but df.iloc[0:2] two?', 'loc slices by label and includes the end label; iloc slices by position and excludes the end.'),
        ('What does df[0] do?', 'It looks for a column named 0 and raises KeyError if there is none. To get the first row use <code>df.iloc[0]</code>.'),
        ('What happened to .ix?', 'It mixed label and position lookup ambiguously and was removed in pandas 1.0. Use loc or iloc.'),
        ('How do you select the last row?', '<code>df.iloc[-1]</code>; <code>df.tail(1)</code> returns it as a DataFrame.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('How do you filter rows with multiple conditions? What are isin, between and query?', 'Filtering Rows', minutes=7, cards=[
    definition(
        defbox('Filtering uses a <strong>boolean mask</strong>: a Series of True/False of the same length as the DataFrame. '
               '<code>df[mask]</code> or <code>df.loc[mask]</code> keeps rows where the mask is True.',
               'Combine conditions with <code>&amp;</code> (and), <code>|</code> (or), <code>~</code> (not), with each condition in parentheses. Helpers: '
               '<code>isin(list)</code>, <code>between(a, b)</code>, <code>str.contains()</code>, <code>isna()</code>; or write the condition as a string '
               'with <code>df.query()</code>.'),
        tags('Boolean mask', 'query', 'isin', 'between', 'Filtering'),
    ),
    analogy('A <strong>sieve with several meshes</strong>. Each condition is one mesh that marks every row "passes" or "stops". Stack the meshes '
            '(&amp;) and only rows that pass all of them fall through.'),
    filter_anim(),
    real_world(
        scenario('Re-exam list',
                 p('"PG-DBDA students from the Kharghar centre who scored below 60 in any subject, or were absent" is one line of pandas: '
                   '<code>df[(df.course == "PG-DBDA") &amp; (df.centre == "Kharghar") &amp; ((df.marks &lt; 60) | df.marks.isna())]</code>.')),
    ),
    example(
        data_note('students', 'marks'),
        pdrun("""
            m = marks.merge(students[['roll_no', 'name', 'course']], on='roll_no')

            print(m[(m['course'] == 'PG-DBDA') & (m['marks'] > 80)])
            print()
            print(m[m['subject'].isin(['ML', 'Python'])])
            print()
            print(m[m['marks'].between(60, 80)])              # inclusive both ends
            print()
            print(m.query("marks < 60 or marks.isna()"))       # string syntax
            print()
            limit = 85
            print(m.query("marks > @limit")[['name', 'subject', 'marks']])   # @ = Python variable
        """, setup=BOTH, title=S),
        pdrun("""
            m = marks
            m[m['marks'] > 60 and m['subject'] == 'SQL']
        """, setup=MARKS, title='Python (pandas) · the classic mistake', expect_error=True),
        title='Example: Conditions, isin, between, query'),
    steps(
        ('Write each condition', "<code>(df['marks'] &gt; 60)</code>, always in parentheses."),
        ('Combine', '<code>&amp;</code>, <code>|</code>, <code>~</code>; never <code>and</code>/<code>or</code>/<code>not</code>.'),
        ('Use helpers', '<code>isin</code> for lists, <code>between</code> for ranges, <code>str.contains</code> for text, <code>isna</code> for missing.'),
        ('Prefer loc when assigning', '<code>df.loc[mask, "flag"] = True</code>.'),
        ('Check the count', '<code>mask.sum()</code> tells you how many rows match before you act on them.'),
        title='Steps to Filter Safely'),
    crossq(
        ('Why does "and" fail?', 'Python\'s and/or need a single True/False; a Series has many values, so pandas raises "The truth value of a Series is ambiguous". The element-wise operators &amp; | ~ are what you need.'),
        ('Why are parentheses needed?', 'In Python <code>&amp;</code> has higher precedence than <code>&gt;</code> or <code>==</code>, so <code>a &gt; 1 &amp; b &lt; 2</code> is parsed as <code>a &gt; (1 &amp; b) &lt; 2</code>.'),
        ('Is query faster?', 'For large DataFrames, query/eval can use numexpr and avoid temporary arrays; for small ones the difference is negligible. Mainly it is more readable.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('How do you add, modify, rename and drop columns? What is assign?', 'Adding & Changing Columns', minutes=7, cards=[
    definition(
        defbox('<strong>Add/modify</strong>: <code>df["new"] = expression</code> (computed for all rows at once). <strong>Conditional values</strong>: '
               '<code>np.where</code>, <code>np.select</code>, <code>pd.cut</code>, <code>Series.map</code>. <strong>Rename</strong>: '
               '<code>df.rename(columns={...})</code>. <strong>Drop</strong>: <code>df.drop(columns=[...])</code> or <code>df.drop(index=[...])</code>.',
               '<code>df.assign(new=...)</code> returns a <strong>new</strong> DataFrame with the column added, which fits method chains; a lambda receives '
               'the DataFrame as it is at that point in the chain.'),
        tags('assign', 'np.where', 'np.select', 'rename', 'drop', 'pd.cut'),
    ),
    analogy('Adding a column is like adding a <strong>new column in a spreadsheet and dragging the formula down</strong>, except pandas fills the whole '
            'column in one go. <code>assign</code> is "<strong>photocopy the sheet, then add the column on the copy</strong>", leaving the original as it was.'),
    columns_anim(),
    real_world(
        scenario('Grade sheet',
                 p('From raw marks: percentage, grade bands (A ≥ 85, B ≥ 70, C ≥ 60, else F) with <code>np.select</code> or <code>pd.cut</code>, a '
                   'PASS/FAIL flag with <code>np.where</code>, full course names via <code>map</code> on a dictionary, then rename columns for the '
                   'printed report and drop helper columns.')),
    ),
    example(
        data_note('students', 'marks'),
        pdrun("""
            m = marks.dropna(subset=['marks']).copy()

            m['result'] = np.where(m['marks'] >= 60, 'PASS', 'FAIL')
            m['grade'] = np.select([m['marks'] >= 85, m['marks'] >= 70, m['marks'] >= 60],
                                   ['A', 'B', 'C'], default='F')
            m['band'] = pd.cut(m['marks'], bins=[0, 60, 75, 100], labels=['low', 'mid', 'high'], right=False)

            report = (m.assign(subject_upper=lambda d: d['subject'].str.upper())
                       .rename(columns={'roll_no': 'Roll No', 'marks': 'Score'})
                       .drop(columns=['subject']))
            print(report)
            print()
            print(m.columns.tolist())      # m itself unchanged by assign/rename/drop
        """, setup=BOTH, title=S),
        title='Example: Derived Columns, Grades and a Report Chain'),
    steps(
        ('Simple formula', '<code>df["pct"] = df["marks"] / df["max_marks"] * 100</code>.'),
        ('Two outcomes', '<code>np.where(condition, value_if_true, value_if_false)</code>.'),
        ('Several outcomes', '<code>np.select([cond1, cond2], [v1, v2], default=...)</code>, or <code>pd.cut</code> for numeric ranges.'),
        ('Lookup values', '<code>df["course_name"] = df["course"].map({"PG-DBDA": "Big Data Analytics", ...})</code>.'),
        ('Tidy up', '<code>rename(columns=...)</code>, <code>drop(columns=...)</code>; reorder with <code>df[[...]]</code>.'),
        title='Steps to Derive Columns'),
    crossq(
        ('Does drop change the DataFrame?', 'No, it returns a new one. <code>inplace=True</code> exists but is discouraged: it rarely saves memory and prevents chaining.'),
        ('When is pd.cut better than np.select?', 'For numeric ranges: one call with bins and labels, and the result is an ordered categorical.'),
        ('How do you add a column at a specific position?', '<code>df.insert(loc=1, column="pct", value=...)</code> (modifies in place).'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('How do you sort, rank and find the top N rows?', 'Sorting & Ranking', minutes=6, cards=[
    definition(
        defbox('<code>sort_values(by, ascending)</code> sorts rows by one or more columns; <code>sort_index()</code> sorts by the index. '
               '<code>nlargest(n, col)</code> / <code>nsmallest</code> return the top/bottom N efficiently. <code>rank(method=...)</code> assigns a rank '
               'to each value; combined with <code>groupby</code> it ranks inside groups.'),
        table(['rank method', 'Ties 91, 91, 84 get'], [
            ['average (default)', '1.5, 1.5, 3'],
            ['min', '1, 1, 3 (like SQL RANK)'],
            ['dense', '1, 1, 2 (like SQL DENSE_RANK)'],
            ['first', '1, 2, 3 (order of appearance, like ROW_NUMBER)'],
        ]),
        tags('sort_values', 'rank', 'nlargest', 'Top N'),
    ),
    analogy('A results notice board: <strong>sort</strong> pins the sheets in score order; <strong>rank</strong> writes each student\'s position next to '
            'their name; <strong>nlargest</strong> is the "toppers" box that shows just the first three.'),
    sort_anim(),
    real_world(
        scenario('Merit list',
                 p('Course-wise merit list: sort by course ascending and total descending, rank within each course with '
                   '<code>groupby("course")["total"].rank(method="min", ascending=False)</code>, and keep rank ≤ 3 for the toppers\' certificates.')),
    ),
    example(
        data_note('students', 'marks'),
        pdrun("""
            m = marks.merge(students[['roll_no', 'name', 'course']], on='roll_no')

            print(m.sort_values(['course', 'marks'], ascending=[True, False]).head(6))
            print()
            print(m.nlargest(3, 'marks')[['name', 'subject', 'marks']])
            print()
            m['rank_in_course'] = m.groupby('course')['marks'].rank(method='dense', ascending=False)
            print(m.sort_values(['course', 'rank_in_course'])[['course', 'name', 'subject', 'marks', 'rank_in_course']])
        """, setup=BOTH, title=S),
        title='Example: Sort, Top 3 and Rank Within Course'),
    steps(
        ('Sort', '<code>df.sort_values("marks", ascending=False)</code>; several keys with lists.'),
        ('Missing values', '<code>na_position="first"</code>/<code>"last"</code> controls where NaN goes.'),
        ('Top N', '<code>nlargest(n, "marks")</code>; per group: sort then <code>groupby().head(n)</code>.'),
        ('Rank', '<code>rank(method="dense", ascending=False)</code>; per group via <code>groupby(...)[col].rank()</code>.'),
        ('Reset the index if needed', '<code>reset_index(drop=True)</code> to get 0…n-1 after sorting.'),
        title='Steps for a Merit List'),
    crossq(
        ('Is sort_values stable?', 'Only with <code>kind="stable"</code> (or mergesort). With several sort keys pandas uses a stable algorithm, so equal rows keep their order.'),
        ('Why is the index jumbled after sorting?', 'Rows keep their labels. Use <code>ignore_index=True</code> in sort_values or <code>reset_index(drop=True)</code>.'),
        ('How do you get the top 2 per course?', '<code>df.sort_values("marks", ascending=False).groupby("course").head(2)</code>.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What is SettingWithCopyWarning? How does Copy-on-Write in pandas 3 change it?', 'Copy vs View & Copy-on-Write', minutes=9, cards=[
    definition(
        defbox('In pandas 1.x/2.x, some indexing operations returned a <strong>view</strong> (sharing memory with the original) and others a '
               '<strong>copy</strong>, and it was hard to know which. Writing to the result might or might not change the original, so pandas raised '
               '<strong>SettingWithCopyWarning</strong>.',
               '<strong>Copy-on-Write (CoW)</strong>, the default and only mode in <strong>pandas 3.0</strong>: every indexing result <strong>behaves as a '
               'copy</strong>. Data is shared internally until one side is modified, then copied. So modifying a subset never changes the parent, and '
               '<strong>chained assignment</strong> (<code>df[mask]["col"] = x</code>) never works, raising <code>ChainedAssignmentError</code>. '
               'SettingWithCopyWarning no longer exists.'),
        tags('Copy-on-Write', 'SettingWithCopyWarning', 'Chained assignment', 'pandas 3.0', 'view'),
    ),
    analogy('A shared Google Doc versus a photocopy. Old pandas sometimes gave you the <strong>shared doc</strong> (your edits appeared in the original) and '
            'sometimes a <strong>photocopy</strong>, without telling you which. Copy-on-Write always behaves like a photocopy, but cleverly: it only '
            'actually photocopies the moment you start writing on it.'),
    cow_anim(),
    real_world(
        scenario('Bug that disappears in pandas 3',
                 p('A notebook did <code>pending = df[df.status == "pending"]</code> then <code>pending["status"] = "done"</code>, and sometimes the main '
                   'DataFrame changed too. With CoW the behaviour is fixed and predictable: <code>df</code> never changes; to update it, write '
                   '<code>df.loc[df.status == "pending", "status"] = "done"</code>.')),
    ),
    example(
        pdrun("""
            df = pd.DataFrame({'name': ['Anuj', 'Vineeta', 'Rohan'], 'marks': [82, 91, 58]})

            df[df['marks'] < 60]['marks'] = 60        # chained assignment
            print(df)
            print()

            low = df[df['marks'] < 60]
            low['marks'] = 60                         # changes only `low`
            print(low)
            print(df)
            print()

            df.loc[df['marks'] < 60, 'marks'] = 60    # the correct way
            print(df)
            print(pd.__version__)
        """),
        title='Example: Chained Assignment vs .loc in pandas 3'),
    steps(
        ('Update the original', 'Always one step: <code>df.loc[mask, "col"] = value</code>.'),
        ('Work on a subset', '<code>sub = df[mask]</code>, then modify <code>sub</code> freely; add <code>.copy()</code> if you want the intent explicit or are on pandas &lt; 3.'),
        ('Avoid chains of [] on the left of =', 'Anything like <code>df["a"][0] = ...</code> or <code>df[mask]["a"] = ...</code>.'),
        ('Upgrading old code', 'On pandas 2.2 set <code>pd.options.mode.copy_on_write = "warn"</code> to find code that relies on the old behaviour.'),
        title='Steps to Modify Data Safely'),
    crossq(
        ('Does Copy-on-Write make pandas slower because of copying?', 'Usually faster: many operations (reset_index, rename, drop of columns…) no longer copy data at all; a copy happens only when shared data is actually written.'),
        ('What was SettingWithCopyWarning really about?', 'pandas could not tell if you were writing to a view or a copy of a DataFrame, so your change might be lost; it warned about the ambiguity.'),
        ('Is inplace=True still useful?', 'Rarely. It does not save memory in most operations and prevents chaining; pandas recommends assigning the result instead.'),
    ),
]),
])
