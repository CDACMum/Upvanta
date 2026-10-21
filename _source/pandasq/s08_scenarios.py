from build import *
from pandasq.anims import *
from pandasq.runner import pdrun, pyshow
from pandasq.data import STUDENTS, MARKS, BOTH, data_note

S = 'Python (pandas) · uses sample data'

SECTION = dict(level='expert', title='Scenario-Based Questions', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: find the top 2 students per course, and the student with the second-highest average.', 'Top N per Group', minutes=8, tag='Scenario', cards=[
    definition(
        defbox('Two standard patterns: <strong>sort then groupby().head(n)</strong> for top-N rows per group, and <strong>groupby().rank(method="dense")</strong> '
               'when ties must be handled (the "second highest" family of questions). <code>nlargest</code> inside <code>apply</code> also works but is slower.',
               'This is the pandas version of SQL\'s <code>ROW_NUMBER()/DENSE_RANK() OVER (PARTITION BY course ORDER BY avg DESC)</code>.'),
        tags('Top N', 'rank', 'dense rank', 'groupby head', 'second highest'),
    ),
    analogy('Picking <strong>house captains</strong>: line each house up by score and take the first two (head). If two students tie for second place, '
            'a fair teacher gives <strong>both the same position</strong> (dense rank) instead of picking whoever stood first in line.'),
    topn_anim(),
    real_world(
        scenario('Toppers\' certificates',
                 p('Certificates go to the top 2 per course per centre. With ties, both students receive one, so the rule is "dense rank ≤ 2", not "first two '
                   'rows". The same code, with n as a parameter, produces the top 10 list for the placement cell.')),
    ),
    example(
        data_note('students', 'marks'),
        pdrun("""
            avg = (marks.merge(students, on='roll_no')
                        .groupby(['course', 'name'], as_index=False)['marks'].mean()
                        .rename(columns={'marks': 'avg'}))

            top2 = avg.sort_values(['course', 'avg'], ascending=[True, False]).groupby('course').head(2)
            print(top2)
            print()

            avg['rank'] = avg.groupby('course')['avg'].rank(method='dense', ascending=False).astype(int)
            print(avg.sort_values(['course', 'rank']))
            print()

            overall = avg['avg'].rank(method='dense', ascending=False)
            print('second highest overall:', avg.loc[overall == 2, ['name', 'avg']].to_dict('records'))
        """, setup=BOTH, title=S),
        title='Example: Top 2 per Course and Second Highest Overall'),
    steps(
        ('Aggregate to one row per entity', 'Student averages first, if the data is per subject.'),
        ('No ties concern', '<code>sort_values([group, value], ascending=[True, False]).groupby(group).head(n)</code>.'),
        ('Ties matter', '<code>groupby(group)[value].rank(method="dense", ascending=False)</code>, then filter <code>rank &lt;= n</code>.'),
        ('Nth highest', 'Filter <code>rank == n</code>; handle "no such row" (fewer than n distinct values).'),
        title='Steps to Solve Top-N Questions'),
    crossq(
        ('Why not avg.sort_values("avg").iloc[-2]?', 'It ignores ties: if two students share the highest average, iloc[-2] returns the highest again.'),
        ('Fastest top N for one column overall?', '<code>nlargest(n, col)</code>, which uses a partial sort (O(n log k)).'),
        ('How do you keep all tied rows at the cut-off in nlargest?', '<code>nlargest(n, col, keep="all")</code>.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: you receive a messy CSV export. Walk through cleaning it end to end.', 'Cleaning a Messy File', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('A cleaning pipeline has repeatable stages: <strong>read</strong> with the right options → <strong>normalise</strong> column names and text → '
               '<strong>convert types</strong> (numbers, dates, categories, missing markers) → <strong>deduplicate</strong> → <strong>validate</strong> → '
               '<strong>save</strong>. Each stage is a small function so the pipeline can be rerun on every new file, with row counts logged between stages.'),
        tags('Data cleaning', 'pipeline', 'pipe', 'validation', 'ETL'),
    ),
    analogy('Washing vegetables from the market: <strong>unpack</strong>, <strong>rinse</strong> the dirt (spaces, case), <strong>sort</strong> them into the '
            'right baskets (types), throw out <strong>duplicates and spoiled ones</strong>, <strong>inspect</strong>, then put them in the fridge, every week, '
            'the same way.'),
    pipeline_anim(),
    real_world(
        scenario('Admission portal export',
                 p('The export has trailing spaces in names, "AB" for absent in the entrance score, fees with commas, day-first dates, and students who '
                   'submitted twice. A five-function pipeline produces a clean Parquet file and a log line per stage; the next batch runs unchanged.')),
    ),
    example(
        pdrun("""
            def load(path):
                return pd.read_csv(path, na_values=['AB', '-', ''], skipinitialspace=True)

            def normalise(df):
                df = df.rename(columns=lambda c: c.strip().lower().replace(' ', '_'))
                return df.assign(name=df['name'].str.strip().str.title(),
                                 course=df['course'].str.strip().str.upper())

            def convert(df):
                return df.assign(fee=pd.to_numeric(df['fee'].str.replace(',', '')),
                                 entrance=pd.to_numeric(df['entrance'], errors='coerce'),
                                 submitted=pd.to_datetime(df['submitted'], format='%d-%m-%Y %H:%M'),
                                 course=lambda d: d['course'].astype('category'))

            def dedupe(df):
                return df.sort_values('submitted').drop_duplicates('roll_no', keep='last')

            def validate(df):
                assert df['roll_no'].is_unique, 'duplicate roll numbers'
                bad = df[~df['entrance'].between(0, 100) & df['entrance'].notna()]
                assert bad.empty, f'entrance out of range: {bad.roll_no.tolist()}'
                return df

            def log(df, step):
                print(f'{step:<10} rows={len(df)}')
                return df

            clean = (load('admissions.csv').pipe(log, 'load')
                     .pipe(normalise).pipe(convert).pipe(log, 'convert')
                     .pipe(dedupe).pipe(log, 'dedupe')
                     .pipe(validate)
                     .sort_values('roll_no').reset_index(drop=True))
            print(clean)
            print(clean.dtypes)
            clean.to_parquet('admissions_clean.parquet')
        """, files={'admissions.csv': '''
            Roll No, Name ,Course, Fee ,Entrance,Submitted
            2401,  anuj sharma ,pg-dbda,"95,000",78,01-08-2026 10:15
            2402,VINEETA RAO,PG-DBDA ,"95,000",AB,01-08-2026 11:00
            2403,aarshvi k,pg-dai,"90,000",84,02-08-2026 09:30
            2402,Vineeta Rao,PG-DBDA,"95,000",81,03-08-2026 16:45
        '''}),
        title='Example: Five Small Functions, One Chain, Logged Row Counts'),
    steps(
        ('Look at the raw file', 'Delimiter, quoting, encoding, header, missing markers.'),
        ('Load with options', 'na_values, skipinitialspace, dtype for ids (keep leading zeros as text).'),
        ('Normalise', 'Column names to snake_case; strip/case text.'),
        ('Convert and dedupe', 'Explicit formats; keep the latest record per key.'),
        ('Validate and save', 'Asserts with useful messages; Parquet output; keep the raw file untouched.'),
        title='Steps to Clean Any Export'),
    crossq(
        ('Why keep the raw file?', 'Cleaning rules change; you must be able to rerun from the original, and auditors may ask for it.'),
        ('How do you keep leading zeros in ids like 00123?', 'Read them as strings: <code>dtype={"id": "str"}</code>.'),
        ('What do you report to the data owner?', 'Counts per issue (missing, duplicates, out of range) with examples, so the source system can be fixed.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: compare this month\'s student master with last month\'s. What was added, removed or changed?', 'Comparing Two Datasets', minutes=8, tag='Scenario', cards=[
    definition(
        defbox('Comparing two versions of a table has two parts: <strong>row-level differences</strong> (keys only in one version) via an <strong>outer merge '
               'with indicator</strong>, and <strong>cell-level differences</strong> for keys in both via <code>DataFrame.compare()</code> on frames aligned by '
               'the key (same index and columns).'),
        tags('compare', 'indicator', 'change data capture', 'diff', 'SCD'),
    ),
    analogy('Comparing two class photos taken a month apart: who is <strong>new</strong>, who has <strong>left</strong>, and among those in both, who '
            '<strong>changed their hairstyle</strong>.'),
    compare_anim(),
    real_world(
        scenario('Change log for the student database',
                 p('The office keeps a monthly extract. A short script produces "added", "removed" and "changed (field, old → new)" lists, emailed to the '
                   'coordinator, and the same output feeds a history table, which is how data warehouses track changes (snapshots / SCD Type 2).')),
    ),
    example(
        pdrun("""
            old = pd.DataFrame({'roll_no': [2401, 2402, 2403], 'city': ['Pune', 'Navi Mumbai', 'Mumbai'],
                                'phone': ['9800000001', '9800000002', '9800000003']})
            new = pd.DataFrame({'roll_no': [2401, 2402, 2404], 'city': ['Pune', 'Pune', 'Thane'],
                                'phone': ['9800000001', '9800000002', '9800000004']})

            both = old.merge(new, on='roll_no', how='outer', indicator=True)
            print('added  :', both.loc[both['_merge'] == 'right_only', 'roll_no'].tolist())
            print('removed:', both.loc[both['_merge'] == 'left_only', 'roll_no'].tolist())
            print()

            keys = sorted(set(old.roll_no) & set(new.roll_no))
            a = old.set_index('roll_no').loc[keys]
            b = new.set_index('roll_no').loc[keys]
            diff = a.compare(b, result_names=('old', 'new'))
            print(diff)
            print()

            log = (diff.stack(level=0)
                       .reset_index()
                       .rename(columns={'level_1': 'field'}))
            print(log)
        """),
        title='Example: Added, Removed and Changed Cells'),
    steps(
        ('Pick the key', 'roll_no; check it is unique in both versions.'),
        ('Rows', 'Outer merge on the key with <code>indicator=True</code>: left_only = removed, right_only = added.'),
        ('Cells', 'Align both on the common keys (same index order and columns), then <code>compare()</code>.'),
        ('Tidy the output', 'Stack to one row per changed field with old and new values.'),
        ('Store', 'Append to a change-history table with the run date.'),
        title='Steps to Diff Two Tables'),
    crossq(
        ('Why must frames be aligned for compare()?', 'compare() requires identically labelled frames (same index and columns); it compares cell by cell at the same labels.'),
        ('How do you treat NaN vs NaN?', 'compare() treats two missing values as equal (not a change).'),
        ('How would you do this for millions of rows?', 'Hash each row (<code>pd.util.hash_pandas_object</code>) and compare hashes per key first, then compare only the keys whose hashes differ.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: find each student\'s longest streak of consecutive present days.', 'Consecutive Streaks', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('"Consecutive" questions (streaks, runs, sessions) are <strong>gaps-and-islands</strong> problems. The pandas pattern: sort by entity and time, '
               'mark where a run starts with <code>value != value.shift()</code> (or a time gap &gt; threshold for sessions), number the runs with '
               '<code>cumsum()</code>, then <code>groupby</code> the run id to get each run\'s length, start and end.'),
        tags('gaps and islands', 'shift', 'cumsum', 'streak', 'sessionisation'),
    ),
    analogy('Beads on a string, white for present and black for absent. Every time the colour changes you <strong>tie a knot</strong> (shift comparison); '
            'counting knots numbers each run of beads (cumsum); then you <strong>measure the longest white stretch</strong> (groupby).'),
    streak_anim(),
    real_world(
        scenario('Attendance awards and early warnings',
                 p('The longest present streak per student for a "perfect fortnight" award, and the current absence streak: three or more consecutive '
                   'absences triggers a mentor call. The same code with a 30-minute gap rule turns LMS clicks into study sessions.')),
    ),
    example(
        pdrun("""
            days = pd.date_range('2026-10-01', periods=8)
            att = pd.DataFrame({
                'roll_no': [2401] * 8 + [2402] * 8,
                'date':    list(days) * 2,
                'present': [1, 1, 0, 1, 1, 1, 0, 1,
                            1, 1, 1, 1, 0, 0, 0, 1],
            }).sort_values(['roll_no', 'date'])

            g = att.groupby('roll_no')['present']
            att['run_id'] = (att['present'] != g.shift()).groupby(att['roll_no']).cumsum()

            runs = (att.groupby(['roll_no', 'run_id'])
                       .agg(present=('present', 'first'), days=('date', 'size'),
                            start=('date', 'min'), end=('date', 'max'))
                       .reset_index())
            print(runs)
            print()

            longest = runs[runs['present'] == 1].sort_values('days', ascending=False).groupby('roll_no').head(1)
            print(longest[['roll_no', 'days', 'start', 'end']])
            print()
            absent3 = runs[(runs['present'] == 0) & (runs['days'] >= 3)]
            print('3+ consecutive absences:')
            print(absent3[['roll_no', 'days', 'start', 'end']])
        """),
        title='Example: Runs per Student, Longest Streak, Absence Alert'),
    steps(
        ('Sort', 'By entity and date; make sure every date is present (reindex missing days as absent if needed).'),
        ('Mark run starts', '<code>value != groupby(entity).shift()</code>.'),
        ('Number runs', '<code>groupby(entity).cumsum()</code> of the start flags.'),
        ('Summarise runs', 'groupby (entity, run_id): size, first value, min/max date.'),
        ('Answer', 'Filter the run type and take the max length per entity.'),
        title='Steps for Streak Problems'),
    crossq(
        ('What if the log skips days with no record?', 'Reindex each student to the full date range (<code>pd.date_range</code>) first, filling missing days as absent; otherwise runs join across gaps.'),
        ('How is sessionisation different?', 'A new session starts when the time since the previous event exceeds a threshold: <code>ts.diff() &gt; pd.Timedelta("30min")</code>, then cumsum.'),
        ('Why groupby in the shift?', 'So the first row of a student is compared with nothing (NaN), not with the previous student\'s last day.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Scenario: build the monthly attendance eligibility report as an Excel file.', 'End-to-End Report', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('A typical end-to-end pandas task: <strong>aggregate</strong> a daily log per student, <strong>merge</strong> the master data, <strong>derive</strong> '
               'percentages and flags with vectorised logic, <strong>reshape</strong> for presentation (pivot), and <strong>export</strong> a multi-sheet Excel '
               'file with <code>pd.ExcelWriter</code>, with parameters (month, threshold) instead of hard-coded values.'),
        tags('report', 'ExcelWriter', 'pivot_table', 'groupby', 'automation'),
    ),
    analogy('Making the monthly <strong>attendance notice for the board</strong>: count each student\'s days, compare with the rule, list the defaulters, '
            'and pin one neat sheet per course. The script is the clerk who does it in seconds every month, without mistakes.'),
    report_anim(),
    real_world(
        scenario('C-DAC coordinator\'s monthly task',
                 p('Biometric attendance exports are combined into one log. The script computes attendance percentage per student, flags those below the '
                   'course minimum, calculates how many more days each needs, and writes one sheet per course plus a "Shortfall" sheet that mentors '
                   'use to call students. The minimum attendance is a parameter, so a policy change is a one-line edit.')),
    ),
    example(
        data_note('students'),
        pdrun("""
            MIN_ATTENDANCE = 0.80          # parameter: set to the course rule
            rng = np.random.default_rng(42)
            days = pd.bdate_range('2026-09-01', '2026-09-30')
            prob = {2401: .95, 2402: .97, 2403: .70, 2404: .85, 2405: .78, 2406: .90}
            log = pd.DataFrame([(r, d, int(rng.random() < p)) for r, p in prob.items() for d in days],
                               columns=['roll_no', 'date', 'present'])

            summary = (log.groupby('roll_no')
                          .agg(present=('present', 'sum'), total=('present', 'size'))
                          .reset_index()
                          .merge(students, on='roll_no', validate='one_to_one')
                          .assign(pct=lambda d: (d['present'] / d['total'] * 100).round(1),
                                  eligible=lambda d: d['pct'] >= MIN_ATTENDANCE * 100))
            summary['days_needed'] = (np.ceil(MIN_ATTENDANCE * summary['total']) - summary['present']).clip(lower=0).astype(int)

            cols = ['roll_no', 'name', 'centre', 'present', 'total', 'pct', 'eligible', 'days_needed']
            print(summary[['course'] + cols].sort_values(['course', 'pct']).to_string(index=False))

            with pd.ExcelWriter('attendance_sep_2026.xlsx') as xw:
                for course, grp in summary.groupby('course'):
                    grp[cols].sort_values('pct').to_excel(xw, sheet_name=course, index=False)
                summary.loc[~summary['eligible'], ['course'] + cols].to_excel(xw, sheet_name='Shortfall', index=False)
                summary.pivot_table(index='centre', columns='course', values='pct', aggfunc='mean').round(1).to_excel(xw, sheet_name='Centre x Course')

            print()
            print(pd.ExcelFile('attendance_sep_2026.xlsx').sheet_names)
        """, setup=STUDENTS, title=S),
        title='Example: From Daily Log to a Four-Sheet Excel Report'),
    steps(
        ('Parameterise', 'Month, threshold and file paths at the top (or command-line arguments).'),
        ('Aggregate the log', 'present and total days per student with named agg.'),
        ('Enrich and derive', 'merge master data (validate), percentage, eligible flag, days needed.'),
        ('Shape for readers', 'One sheet per course, a shortfall sheet, a centre × course pivot.'),
        ('Automate', 'Schedule the script (cron/Airflow) and email the file; keep a copy per month.'),
        title='Steps to Automate the Report'),
    crossq(
        ('How would you format the Excel (colours, column widths)?', 'Use the ExcelWriter engine: openpyxl styles or xlsxwriter formats and conditional formatting; or <code>df.style</code> with background colours, then <code>to_excel</code>.'),
        ('Why validate="one_to_one" in the merge?', 'Each student summary must match exactly one master row; a duplicate in the master would duplicate students in the report.'),
        ('How do you test this script?', 'Feed a tiny hand-made log where the expected percentages are obvious and compare with assert_frame_equal.'),
    ),
]),
])
