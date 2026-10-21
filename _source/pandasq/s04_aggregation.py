from build import *
from pandasq.anims import *
from pandasq.runner import pdrun, pyshow
from pandasq.data import STUDENTS, MARKS, BOTH, data_note

S = 'Python (pandas) · uses sample data'
JOINED = BOTH + "\nm = marks.merge(students[['roll_no', 'name', 'course']], on='roll_no')\n"
JNOTE = note('These examples use <code>m = marks.merge(students[["roll_no", "name", "course"]], on="roll_no")</code>: one row per mark with the '
             'student\'s name and course (sample data shown in section 1).', 'Data')

SECTION = dict(level='intermediate', title='Grouping & Reshaping', questions=[

# ------------------------------------------------------------------ 16
Q('How does groupby work? Explain split-apply-combine.', 'groupby', minutes=8, cards=[
    definition(
        defbox('<code>df.groupby(keys)</code> implements <strong>split-apply-combine</strong>: <strong>split</strong> rows into groups by the key values, '
               '<strong>apply</strong> a function to each group independently, <strong>combine</strong> the results into a new Series/DataFrame. '
               'It is the pandas equivalent of SQL <code>GROUP BY</code>.',
               'The groupby object is lazy: nothing is computed until you call an aggregation (<code>mean</code>, <code>sum</code>, <code>count</code>, '
               '<code>size</code>, <code>agg</code>…), a <code>transform</code>, <code>filter</code> or <code>apply</code>.'),
        tags('groupby', 'split-apply-combine', 'agg', 'GROUP BY', 'size', 'count'),
    ),
    analogy('Sorting answer sheets into <strong>piles by course</strong> (split), each pile\'s examiner <strong>computes its average</strong> (apply), and '
            'the averages are written <strong>on one summary sheet</strong> (combine).'),
    groupby_anim(),
    real_world(
        scenario('Centre-wise performance',
                 p('<code>m.groupby(["centre", "course"]).agg(students=("roll_no", "nunique"), avg=("marks", "mean"), fails=("marks", lambda s: (s &lt; 60).sum()))</code> '
                   'produces the table the coordinator presents in the monthly review, from raw marks rows.')),
    ),
    example(
        data_note('students', 'marks'),
        JNOTE,
        pdrun("""
            print(m.groupby('course')['marks'].mean())
            print()
            print(m.groupby('course').size())                 # rows per group
            print(m.groupby('course')['marks'].count())       # non-missing marks per group
            print()
            print(m.groupby(['course', 'subject'], as_index=False)['marks'].max())
            print()
            for course, grp in m.groupby('course'):           # iterate over groups
                print(course, grp['name'].unique().tolist())
        """, setup=JOINED, title=S),
        title='Example: Mean, size vs count, Two Keys, Iteration'),
    steps(
        ('Choose keys', 'One column, a list of columns, a Series, or <code>pd.Grouper(key="date", freq="ME")</code> for time.'),
        ('Select the value column', "<code>df.groupby('course')['marks']</code>: aggregate only what you need."),
        ('Aggregate', '<code>.mean()</code>, <code>.sum()</code>, <code>.agg(...)</code> for several statistics.'),
        ('Shape the output', '<code>as_index=False</code> or <code>reset_index()</code>; sort the result.'),
        ('Watch missing keys', 'Rows whose key is NaN are dropped unless <code>dropna=False</code>.'),
        title='Steps to Group Data'),
    crossq(
        ('size() vs count()?', 'size counts rows per group including missing values; count counts non-missing values per column.'),
        ('Why does groupby on a category column show empty groups?', 'For categoricals, all categories appear. In pandas 3 <code>observed=True</code> is the default, so only categories present are shown; set observed=False to include all.'),
        ('Can you group by a computed value?', 'Yes: <code>df.groupby(df["marks"] &gt;= 60)</code> or <code>df.groupby(df["date"].dt.month)</code>.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is the difference between agg, transform, apply and filter in groupby?', 'agg vs transform vs apply', minutes=9, cards=[
    definition(
        defbox('<strong>agg</strong>: reduces each group to <strong>one row</strong> (one value per statistic). Supports lists of functions and '
               '<strong>named aggregation</strong>: <code>agg(avg=("marks", "mean"))</code>.',
               '<strong>transform</strong>: returns an object <strong>the same length as the input</strong>, with each row receiving its group\'s value; '
               'used to add group statistics as columns or to normalise within groups.',
               '<strong>filter</strong>: keeps or removes <strong>entire groups</strong> based on a condition returning True/False.',
               '<strong>apply</strong>: runs any function on each group\'s DataFrame; most flexible, slowest, output shape depends on the function.'),
        table(['Method', 'Output rows', 'Typical use'], [
            ['agg', 'one per group', 'summary report'],
            ['transform', 'same as input', "'marks minus course average', group-wise fillna, rank"],
            ['filter', 'subset of input rows', 'courses with at least N students'],
            ['apply', 'depends', 'top-N per group, custom logic'],
        ]),
        tags('agg', 'transform', 'apply', 'filter', 'named aggregation'),
    ),
    analogy('For a class: <strong>agg</strong> is the class average on the notice board (one number per class). <strong>transform</strong> writes the class '
            'average <strong>on every student\'s report card</strong>. <strong>filter</strong> is "only classes with more than 30 students go on the trip". '
            '<strong>apply</strong> is "each class teacher does whatever you ask".'),
    agg_transform_anim(),
    real_world(
        scenario('Relative performance',
                 p('A score of 70 is good in a hard subject and weak in an easy one. <code>m["vs_subject_avg"] = m["marks"] - m.groupby("subject")["marks"].transform("mean")</code> '
                   'shows each student against the subject average; a named agg builds the summary; filter drops subjects with too few attempts.')),
    ),
    example(
        data_note('students', 'marks'),
        JNOTE,
        pdrun("""
            summary = m.groupby('course').agg(
                students=('roll_no', 'nunique'),
                avg_marks=('marks', 'mean'),
                best=('marks', 'max'),
                fails=('marks', lambda s: (s < 60).sum()),
            ).round(1)
            print(summary)
            print()

            m['course_avg'] = m.groupby('course')['marks'].transform('mean').round(1)
            m['diff'] = m['marks'] - m['course_avg']
            print(m[['name', 'course', 'marks', 'course_avg', 'diff']])
            print()

            print(m.groupby('course').filter(lambda g: g['roll_no'].nunique() >= 2)['course'].unique().tolist())
            print()
            top1 = m.groupby('course').apply(lambda g: g.nlargest(1, 'marks'))
            print(top1[['name', 'subject', 'marks']])     # course is in the index, not a column
        """, setup=JOINED, title=S),
        title='Example: Named agg, transform, filter, apply'),
    steps(
        ('One row per group?', 'Use <code>agg</code>, preferably named aggregation for clean column names.'),
        ('Need it on every row?', 'Use <code>transform</code> and assign as a new column.'),
        ('Drop whole groups?', 'Use <code>filter</code>.'),
        ('Something else?', 'Try a built-in first (<code>nlargest</code>, <code>head</code>, <code>rank</code>, <code>cumsum</code>); use <code>apply</code> last.'),
        title='Steps to Choose the Method'),
    crossq(
        ('Why is apply slow?', 'It calls a Python function once per group and must infer how to combine arbitrary results; built-in aggregations run in Cython over all groups at once.'),
        ('Why is the group column missing inside apply in pandas 3?', 'Since pandas 3.0 the grouping columns are excluded from the DataFrame passed to the function (the old include_groups=True behaviour was removed); the key is available as the group name and in the result index.'),
        ('How do you get the top N rows per group without apply?', '<code>df.sort_values("marks", ascending=False).groupby("course").head(N)</code>.'),
        ('How do you flatten MultiIndex columns from agg({"marks": ["mean", "max"]})?', '<code>df.columns = ["_".join(c) for c in df.columns]</code>, or use named aggregation from the start.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What is the difference between pivot, pivot_table and crosstab?', 'pivot vs pivot_table vs crosstab', minutes=7, cards=[
    definition(
        defbox('<strong>pivot(index, columns, values)</strong>: reshapes long data to wide <strong>without aggregating</strong>; raises an error if an '
               'index/column pair appears twice.',
               '<strong>pivot_table(index, columns, values, aggfunc, fill_value, margins)</strong>: like an Excel pivot table, <strong>aggregates</strong> '
               'duplicates (mean by default) and can add totals.',
               '<strong>crosstab(rows, cols)</strong>: a frequency table (counts) of two or more factors; with <code>normalize</code> gives proportions.'),
        tags('pivot', 'pivot_table', 'crosstab', 'margins', 'Excel pivot'),
    ),
    analogy('<strong>pivot</strong> is rearranging chairs into a grid: each seat must have exactly one person. <strong>pivot_table</strong> lets several '
            'people share a seat and writes their <strong>average height</strong> on it. <strong>crosstab</strong> just <strong>counts heads</strong> per seat.'),
    pivot_anim(),
    real_world(
        scenario('Result sheet and centre report',
                 p('A pivot_table of marks (student × subject) is the printed result sheet; crosstab of centre × result (PASS/FAIL) with '
                   '<code>margins=True</code> and <code>normalize="index"</code> gives pass percentages per centre.')),
    ),
    example(
        data_note('students', 'marks'),
        JNOTE,
        pdrun("""
            sheet = m.pivot_table(index='name', columns='subject', values='marks',
                                  aggfunc='mean', margins=True, margins_name='Avg')
            print(sheet.round(1))
            print()

            m['result'] = np.where(m['marks'] >= 60, 'PASS', 'FAIL/ABSENT')
            print(pd.crosstab(m['course'], m['result'], margins=True))
            print()

            dup = pd.DataFrame({'name': ['Anuj', 'Anuj'], 'subject': ['SQL', 'SQL'], 'marks': [82, 85]})
            try:
                dup.pivot(index='name', columns='subject', values='marks')
            except ValueError as e:
                print('pivot:', e)
            print(dup.pivot_table(index='name', columns='subject', values='marks', aggfunc='max'))
        """, setup=JOINED, title=S),
        title='Example: Result Sheet, Pass/Fail Counts, pivot on Duplicates'),
    steps(
        ('Pick rows, columns, values', 'What goes down the side, across the top, and in the cells.'),
        ('Unique pairs?', 'Use <code>pivot</code>; otherwise <code>pivot_table</code> with an explicit <code>aggfunc</code>.'),
        ('Only counting?', 'Use <code>crosstab</code> (or <code>pivot_table(aggfunc="size")</code>).'),
        ('Polish', '<code>fill_value=0</code>, <code>margins=True</code>, <code>round()</code>, then <code>to_excel()</code>.'),
        title='Steps to Build a Pivot'),
    crossq(
        ('What is the default aggfunc of pivot_table?', 'mean.'),
        ('How is pivot_table related to groupby?', 'It is groupby on index+columns keys, an aggregation, then unstack of the column key.'),
        ('How do you undo a pivot?', '<code>melt</code> (or <code>stack</code> if the columns are an index level).'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What are melt, stack and unstack? What is wide vs long (tidy) format?', 'melt, stack, unstack', minutes=7, cards=[
    definition(
        defbox('<strong>Wide</strong> format has one column per variable value (SQL, Spark, ML columns). <strong>Long / tidy</strong> format has one row per '
               'observation (name, subject, marks).',
               '<strong>melt</strong> converts wide → long (columns become rows). <strong>pivot</strong> converts long → wide. <strong>stack</strong> moves '
               'the column level into the row index (wide → long); <strong>unstack</strong> moves an index level into the columns (long → wide).'),
        tags('melt', 'stack', 'unstack', 'tidy data', 'reshape'),
    ),
    analogy('A wide table is a <strong>class photo in rows</strong>: easy to look at. Long format is <strong>one ID card per student per subject</strong>: '
            'boring to read, but you can sort, count and file the cards any way you like.'),
    melt_anim(),
    real_world(
        scenario('Excel marks sheets into a database',
                 p('Faculty send marks as one column per subject. To load them into the marks table (roll_no, subject, marks) or to group by subject, '
                   '<code>melt</code> them into long format first; reports for printing go back to wide with <code>pivot</code>.')),
    ),
    example(
        pdrun("""
            wide = pd.DataFrame({'name': ['Anuj', 'Vineeta'], 'SQL': [82, 91], 'Spark': [61, 88], 'ML': [70, 79]})

            long = wide.melt(id_vars='name', var_name='subject', value_name='marks')
            print(long)
            print()
            print(long.groupby('subject')['marks'].mean())
            print()
            print(long.pivot(index='name', columns='subject', values='marks'))
            print()
            stacked = wide.set_index('name').stack()
            print(stacked.head(4))
            print(stacked.unstack().columns.tolist())
        """),
        title='Example: Wide → Long → Wide'),
    steps(
        ('Identify id columns', 'Columns that identify the row (name, roll_no) stay as <code>id_vars</code>.'),
        ('Melt the rest', '<code>melt(id_vars=..., var_name="subject", value_name="marks")</code>.'),
        ('Clean the new column', 'Variable names may need parsing, e.g. "SQL_marks" → "SQL".'),
        ('Analyse in long format', 'groupby, filters, plots, database loads.'),
        ('Pivot back for presentation', '<code>pivot</code> / <code>pivot_table</code>.'),
        title='Steps to Reshape'),
    crossq(
        ('Why is long format preferred for analysis?', 'Adding a new subject adds rows, not columns; groupby, plotting libraries (seaborn) and databases all expect one observation per row.'),
        ('What does stack do with NaN?', 'In pandas 3 stack keeps missing values (the new implementation); older versions dropped them by default (dropna=True).'),
        ('What is wide_to_long?', 'A helper for columns with stub names and suffixes, e.g. marks_2025, marks_2026 → year column.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What is a MultiIndex? How do you select from and flatten it?', 'MultiIndex', minutes=7, cards=[
    definition(
        defbox('A <strong>MultiIndex</strong> (hierarchical index) has several levels of labels on the rows or columns, e.g. (course, subject). It appears '
               'after grouping by several keys, pivot tables with several index fields, <code>set_index([...])</code>, or agg with several functions.',
               'Select with <code>loc</code> using tuples or the outer level, <code>xs</code> for an inner level, <code>pd.IndexSlice</code> for ranges; '
               'reshape with <code>stack</code>/<code>unstack</code>; remove with <code>reset_index()</code> or <code>droplevel</code>.'),
        tags('MultiIndex', 'xs', 'IndexSlice', 'unstack', 'reset_index'),
    ),
    analogy('A <strong>postal address</strong>: state → city → street. You can ask for everything in Maharashtra (outer level), one exact address '
            '(full tuple), or "every MG Road in any city" (xs on an inner level).'),
    multiindex_anim(),
    real_world(
        scenario('Two-level results',
                 p('<code>groupby(["course", "subject"]).mean()</code> gives a course → subject index. The coordinator wants PG-DBDA only: '
                   '<code>loc["PG-DBDA"]</code>; the SQL faculty wants SQL across courses: <code>xs("SQL", level="subject")</code>; the Excel export '
                   'needs plain columns: <code>reset_index()</code>.')),
    ),
    example(
        data_note('students', 'marks'),
        JNOTE,
        pdrun("""
            s = m.groupby(['course', 'subject'])['marks'].mean()
            print(s)
            print(s.index.nlevels, s.index.names)
            print()
            print(s.loc['PG-DBDA'])
            print(s.loc[('PG-DAI', 'ML')])
            print(s.xs('SQL', level='subject'))
            print()

            stats = m.groupby('course').agg({'marks': ['mean', 'max']})
            print(stats.columns.tolist())
            stats.columns = ['_'.join(c) for c in stats.columns]
            print(stats.reset_index())
        """, setup=JOINED, title=S),
        title='Example: Select by Level, xs, Flatten Columns'),
    steps(
        ('Know your levels', '<code>df.index.names</code>, <code>df.index.nlevels</code>.'),
        ('Select', '<code>loc[outer]</code>, <code>loc[(outer, inner)]</code>, <code>xs(value, level=name)</code>.'),
        ('Reshape', '<code>unstack(level)</code> for a grid, <code>swaplevel</code> + <code>sort_index</code> to reorder.'),
        ('Flatten', '<code>reset_index()</code> for rows; join tuple names for columns.'),
        title='Steps to Work with a MultiIndex'),
    crossq(
        ('Why sort a MultiIndex?', 'Slicing ranges on an unsorted MultiIndex raises a performance warning or error; <code>sort_index()</code> makes lookups fast and slices valid.'),
        ('How do you create one directly?', '<code>df.set_index(["course", "subject"])</code> or <code>pd.MultiIndex.from_product([courses, subjects])</code>.'),
        ('Is a MultiIndex worth it?', 'Useful for hierarchical lookups and reshaping; for everyday work many teams keep flat columns and use groupby/merge.'),
    ),
]),
])
