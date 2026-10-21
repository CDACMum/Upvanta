from build import *
from pandasq.anims import *
from pandasq.runner import pdrun, pyshow
from pandasq.data import STUDENTS, MARKS, BOTH, data_note

S = 'Python (pandas) · uses sample data'

SECTION = dict(level='basic', title='Data Cleaning', questions=[

# ------------------------------------------------------------------ 11
Q('How do you handle missing values in pandas?', 'Missing Values', minutes=8, cards=[
    definition(
        defbox('pandas represents missing data as <code>NaN</code> (floats), <code>None</code>/<code>NaN</code>/<code>pd.NA</code> (strings and '
               'nullable types) and <code>NaT</code> (datetimes). <code>isna()</code>/<code>notna()</code> detect all of them.',
               'Handling options: <strong>drop</strong> (<code>dropna</code>), <strong>fill</strong> with a constant, statistic or group statistic '
               '(<code>fillna</code>), <strong>carry forward/backward</strong> (<code>ffill</code>/<code>bfill</code>), or <strong>interpolate</strong>. '
               'The right choice depends on why the value is missing.'),
        table(['Method', 'Effect'], [
            ['df.isna().sum()', 'count missing per column'],
            ["df.dropna(subset=['marks'])", 'drop rows missing marks'],
            ["df.dropna(thresh=3)", 'keep rows with at least 3 non-missing values'],
            ["df.fillna({'marks': 0, 'city': 'Unknown'})", 'per-column fill values'],
            ["df['marks'].fillna(df['marks'].mean())", 'mean imputation'],
            ["df.groupby('course')['marks'].transform('mean')", 'group mean, for filling within each course'],
            ['df.ffill() / df.bfill()', 'previous / next valid value (time series)'],
            ['df.interpolate()', 'linear estimate between neighbours'],
        ]),
        tags('NaN', 'isna', 'fillna', 'dropna', 'ffill', 'interpolate', 'Imputation'),
    ),
    analogy('An attendance register with blank cells. You can <strong>tear out</strong> the incomplete pages (dropna), write <strong>"absent"</strong> in '
            'every blank (fillna constant), write the <strong>class average</strong> (mean imputation), or assume the student <strong>did what they did '
            'yesterday</strong> (ffill). Which is right depends on why the cell is blank.'),
    missing_anim(),
    real_world(
        scenario('Absent vs not yet evaluated',
                 p('In a marks sheet, NaN can mean "absent" (should count as 0 or a re-exam) or "paper not yet evaluated" (must stay missing). '
                   'Filling both with the mean would hide the difference. Typical fix: add a status column first, then fill absent with 0 and leave '
                   'pending ones missing.')),
        scenario('Sensor/attendance time series',
                 p('Biometric attendance logs miss a few readings: forward fill or interpolate per device, because neighbouring readings are informative.')),
    ),
    example(
        data_note('students', 'marks'),
        pdrun("""
            print(marks.isna().sum())
            print()
            print(marks.dropna(subset=['marks']).shape)

            m = marks.merge(students[['roll_no', 'course']], on='roll_no')
            m['marks_filled'] = m['marks'].fillna(m.groupby('course')['marks'].transform('mean'))
            print(m[['roll_no', 'subject', 'course', 'marks', 'marks_filled']])
            print()

            temps = pd.Series([31.0, None, None, 34.0, None], index=pd.date_range('2026-10-01', periods=5))
            print(pd.DataFrame({'raw': temps, 'ffill': temps.ffill(), 'interpolate': temps.interpolate()}))
        """, setup=BOTH, title=S),
        title='Example: Count, Drop, Group-Mean Fill, ffill vs interpolate'),
    steps(
        ('Measure', '<code>df.isna().sum()</code> and <code>df.isna().mean()</code> (fraction missing).'),
        ('Understand why', 'Missing at random, absent, not applicable, data-entry error? Ask the data owner.'),
        ('Drop what is useless', 'Columns mostly empty, rows missing the key or target.'),
        ('Fill the rest deliberately', 'Constant, median (robust to outliers), group statistic, ffill/interpolate for time series.'),
        ('Flag it', 'Optionally keep <code>df["marks_was_missing"] = df["marks"].isna()</code> before filling, so later analysis knows.'),
        title='Steps to Handle Missing Data'),
    crossq(
        ('Does mean() include NaN?', 'No, aggregations skip missing values by default (<code>skipna=True</code>); <code>count()</code> counts only non-missing values while <code>size</code> counts all rows.'),
        ('Why is NaN == NaN False?', 'IEEE floating-point rule: NaN is not equal to anything, including itself. Always use <code>isna()</code>, never <code>== np.nan</code>.'),
        ('What replaced fillna(method="ffill")?', 'The method argument was deprecated in pandas 2.1 and removed in 3.0; use <code>df.ffill()</code> / <code>df.bfill()</code>.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How do you find and remove duplicate rows?', 'Duplicates', minutes=6, cards=[
    definition(
        defbox('<code>df.duplicated(subset=None, keep="first")</code> returns a boolean mask marking repeated rows; <code>df.drop_duplicates()</code> '
               'removes them. <code>subset</code> restricts the comparison to key columns; <code>keep</code> chooses which copy survives: '
               '<code>"first"</code>, <code>"last"</code>, or <code>False</code> to drop every copy.',
               'Distinguish <strong>exact duplicates</strong> (the same load happened twice) from <strong>duplicate keys</strong> (two versions of the same '
               'record, where you must decide which is correct).'),
        tags('duplicated', 'drop_duplicates', 'subset', 'keep', 'Deduplication'),
    ),
    analogy('Admission forms: two <strong>identical photocopies</strong> of one form (exact duplicate, throw one away) versus a student who filled the form '
            '<strong>twice with a new phone number</strong> (duplicate key, keep the latest).'),
    duplicates_anim(),
    real_world(
        scenario('Re-evaluation results',
                 p('After re-evaluation the portal export contains both the original and the revised marks. Sort by the update timestamp and '
                   '<code>drop_duplicates(["roll_no", "subject"], keep="last")</code> keeps the final marks; <code>duplicated(keep=False)</code> lists '
                   'every affected student for the audit file.')),
    ),
    example(
        pdrun("""
            raw = pd.DataFrame({
                'roll_no':   [2401, 2401, 2402, 2402, 2403],
                'subject':   ['SQL', 'SQL', 'SQL', 'SQL', 'ML'],
                'marks':     [82, 82, 85, 91, 84],
                'loaded_at': pd.to_datetime(['2026-09-20', '2026-09-20', '2026-09-20', '2026-09-25', '2026-09-21']),
            })
            print(raw.duplicated().sum(), 'exact duplicate row(s)')
            print(raw.duplicated(['roll_no', 'subject'], keep=False).sum(), 'rows share a key with another row')
            print()
            print(raw.drop_duplicates())
            print()
            latest = (raw.sort_values('loaded_at')
                         .drop_duplicates(['roll_no', 'subject'], keep='last')
                         .sort_values('roll_no'))
            print(latest)
        """),
        title='Example: Exact Duplicates and Latest Version per Key'),
    steps(
        ('Count', '<code>df.duplicated().sum()</code> and <code>df.duplicated(keys).sum()</code>.'),
        ('Inspect', '<code>df[df.duplicated(keys, keep=False)].sort_values(keys)</code> shows every copy side by side.'),
        ('Decide the rule', 'Latest timestamp wins? Highest marks? Non-missing values?'),
        ('Apply', 'Sort by the rule, then <code>drop_duplicates(keys, keep="last")</code>.'),
        ('Assert', '<code>assert not df.duplicated(keys).any()</code> so a future load cannot break it silently.'),
        title='Steps to Deduplicate'),
    crossq(
        ('How do you find duplicate index labels?', '<code>df.index.duplicated()</code>; remove with <code>df[~df.index.duplicated(keep="first")]</code>.'),
        ('Are NaN values considered equal by duplicated()?', 'Yes, for duplicate detection two NaN in the same column count as equal (unlike ==).'),
        ('How do you count how many times each key appears?', '<code>df.value_counts(["roll_no", "subject"])</code> or <code>groupby(keys).size()</code>.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('How do you check and convert data types? What are nullable and category dtypes?', 'Data Types & Conversion', minutes=8, cards=[
    definition(
        defbox('Every column has a <strong>dtype</strong>: <code>int64</code>, <code>float64</code>, <code>bool</code>, <code>datetime64</code>, '
               '<code>timedelta64</code>, <code>category</code>, <code>str</code> (pandas 3 strings; <code>object</code> in older versions), plus '
               '<strong>nullable</strong> extension types <code>Int64</code>, <code>Float64</code>, <code>boolean</code> that hold <code>pd.NA</code>.',
               'Convert with <code>astype()</code>, <code>pd.to_numeric(errors="coerce")</code>, <code>pd.to_datetime()</code>, or at load time with '
               '<code>dtype=</code> in read_csv. <code>convert_dtypes()</code> picks the best nullable types automatically.'),
        table(['dtype', 'Use', 'Note'], [
            ['int64 / float64', 'numbers', 'int64 cannot hold NaN (becomes float)'],
            ['Int64 (nullable)', 'integers with gaps', 'missing shown as &lt;NA&gt;'],
            ['category', 'few distinct repeated values', 'big memory saving, ordered option'],
            ['str / object', 'text', 'pandas 3 uses a real string dtype'],
            ['datetime64', 'dates and times', '.dt accessor, resample'],
            ['bool / boolean', 'flags', 'boolean = nullable'],
        ]),
        tags('dtype', 'astype', 'to_numeric', 'category', 'Int64', 'convert_dtypes'),
    ),
    analogy('Data types are the <strong>labels on storage boxes</strong>. If "marks" is labelled "text", you cannot add them up; if "course" is stored as '
            'a full word a million times instead of a <strong>short code</strong> (category), the store room overflows.'),
    dtypes_anim(),
    real_world(
        scenario('Fee report that would not sum',
                 p('Fees exported from accounts as "95,000" load as text, so <code>sum()</code> concatenates strings or fails. '
                   '<code>str.replace(",", "")</code> then <code>astype(int)</code> fixes it. Roll numbers with gaps had become 2401.0: '
                   '<code>astype("Int64")</code> keeps them integers.')),
    ),
    example(
        pdrun("""
            df = pd.DataFrame({'roll_no': [2401, None, 2403],
                               'marks':   ['82', 'AB', '84'],
                               'fee':     ['95,000', '90,000', '85,000'],
                               'course':  ['PG-DBDA', 'PG-DAC', 'PG-DBDA']})
            print(df.dtypes)
            print()

            df['roll_no'] = df['roll_no'].astype('Int64')
            df['marks']   = pd.to_numeric(df['marks'], errors='coerce')
            df['fee']     = df['fee'].str.replace(',', '').astype('int64')
            df['course']  = df['course'].astype('category')
            print(df)
            print(df.dtypes)
            print()
            print(df['fee'].sum(), df['marks'].mean())
            print(df['course'].cat.categories.tolist(), df['course'].cat.codes.tolist())
        """),
        pdrun("""
            pd.Series(['82', 'AB']).astype(int)
        """, title='Python (pandas) · without errors="coerce"', expect_error=True),
        title='Example: Converting Each Problem Column'),
    steps(
        ('Inspect', '<code>df.dtypes</code> or <code>df.info()</code> right after loading.'),
        ('Find bad values', "<code>df.loc[pd.to_numeric(df['marks'], errors='coerce').isna() &amp; df['marks'].notna(), 'marks']</code> lists what failed to parse."),
        ('Convert', '<code>to_numeric</code>, <code>to_datetime</code>, <code>astype</code>; clean strings first if needed.'),
        ('Save memory', '<code>category</code> for repeated text, smaller ints (<code>int32</code>) via <code>pd.to_numeric(downcast="integer")</code>.'),
        ('Fix at the source', 'Pass <code>dtype=</code> and <code>na_values=</code> to read_csv next time.'),
        title='Steps to Fix Types'),
    crossq(
        ('Why does an int column become float after a merge or reindex?', 'Missing values are introduced and NumPy int64 cannot store NaN, so pandas upcasts to float64. Nullable Int64 avoids this.'),
        ('What is an ordered category?', '<code>pd.Categorical(values, categories=["C", "B", "A"], ordered=True)</code>: comparisons and sorting follow that order, e.g. grade &gt; "B".'),
        ('astype vs to_numeric?', 'astype fails on any bad value; to_numeric can coerce bad values to NaN and downcast.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do you clean text columns? Explain the .str accessor.', 'String Methods (.str)', minutes=7, cards=[
    definition(
        defbox('The <strong>.str accessor</strong> applies string operations to every element of a text Series at once: <code>lower</code>, '
               '<code>upper</code>, <code>title</code>, <code>strip</code>, <code>replace</code>, <code>contains</code>, <code>startswith</code>, '
               '<code>split</code>, <code>extract</code> (regex groups), <code>len</code>, <code>slice</code>, <code>pad</code>, <code>cat</code>…',
               'Missing values pass through as missing. Results are Series, so calls chain and combine with filters.'),
        tags('.str', 'regex', 'extract', 'split', 'contains', 'Text Cleaning'),
    ),
    analogy('<code>.str</code> is <strong>"Find and Replace" plus "Format Cells" applied to an entire column in one click</strong>, instead of editing '
            'each cell by hand.'),
    str_anim(),
    real_world(
        scenario('Admission form data',
                 p('Cities typed as " mumbai", "MUMBAI", "Navi-Mumbai"; names with double spaces; emails from which you need the domain; course codes '
                   'buried in text like "Batch Aug-2026 / PG-DBDA". <code>strip</code>, <code>title</code>, <code>replace</code>, <code>split</code> '
                   'and <code>extract</code> normalise all of it in a few lines before grouping by city or course.')),
    ),
    example(
        pdrun("""
            df = pd.DataFrame({
                'name':  ['  anuj  sharma', 'VINEETA RAO', 'aarshvi  k'],
                'email': ['anuj@cdac.in', 'vineeta@gmail.com', None],
                'batch': ['Aug-2026 / PG-DBDA', 'Aug-2026 / PG-DAC', 'Feb-2026 / PG-DBDA'],
            })
            df['name']   = df['name'].str.strip().str.replace(r'\\s+', ' ', regex=True).str.title()
            df['domain'] = df['email'].str.split('@').str[1]
            df[['month', 'year', 'course']] = df['batch'].str.extract(r'(\\w{3})-(\\d{4}) / (\\S+)')
            print(df.drop(columns='batch'))
            print()
            print(df[df['email'].str.endswith('cdac.in', na=False)]['name'].tolist())
        """),
        title='Example: Normalise Names, Split Emails, Extract with Regex'),
    steps(
        ('Normalise', '<code>str.strip()</code>, <code>str.lower()</code>/<code>title()</code>, collapse spaces with a regex replace.'),
        ('Standardise variants', '<code>replace</code> or a mapping dict for known spellings.'),
        ('Split structured text', '<code>str.split(sep, expand=True)</code> or <code>str.extract(regex)</code> into new columns.'),
        ('Filter', "<code>str.contains(pattern, case=False, na=False)</code>."),
        ('Then convert', 'Low-cardinality cleaned text → <code>category</code>.'),
        title='Steps to Clean Text'),
    crossq(
        ('Why na=False in contains?', 'Missing values would give missing in the mask; na=False treats them as "no match" so the mask can filter rows.'),
        ('Is .str vectorised?', 'It runs in a loop internally for object strings, but with PyArrow-backed strings (pandas 3 default when pyarrow is installed) many methods run in compiled code and are much faster.'),
        ('How do you replace using a regex?', '<code>s.str.replace(pattern, repl, regex=True)</code>; since pandas 2.0 the default is regex=False.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you work with dates and times in pandas?', 'Dates & Times', minutes=8, cards=[
    definition(
        defbox('<code>pd.to_datetime()</code> converts text or numbers to <code>datetime64</code>. The <strong>.dt accessor</strong> extracts parts '
               '(<code>year</code>, <code>month</code>, <code>day_name()</code>, <code>quarter</code>…) and does rounding and time-zone conversion. '
               'Subtracting dates gives <strong>Timedelta</strong>s; <code>pd.Timedelta</code> and <code>pd.DateOffset</code> shift dates.',
               '<code>pd.date_range()</code> generates sequences of dates; with a <strong>DatetimeIndex</strong>, <code>resample()</code> aggregates by '
               'calendar period and string slicing (<code>df.loc["2026-09"]</code>) selects a month.'),
        tags('to_datetime', '.dt', 'Timedelta', 'date_range', 'DatetimeIndex', 'resample'),
    ),
    analogy('Text dates are <strong>pictures of a calendar</strong>; you can look at them but not count days on them. <code>to_datetime</code> turns them '
            'into a <strong>real calendar</strong> where you can count, jump 180 days ahead, and group by week or month.'),
    datetime_anim(),
    real_world(
        scenario('Course timelines',
                 p('Joining dates arrive as "01-08-2026" (day first). After parsing: days since joining for the attendance percentage, course end '
                   'date = joining + 6 months (<code>DateOffset(months=6)</code>), weekday of each exam, and weekly counts of new admissions with '
                   '<code>resample("W")</code>.')),
    ),
    example(
        pdrun("""
            df = pd.DataFrame({'name':   ['Anuj', 'Vineeta', 'Aarshvi'],
                               'joined': ['01-08-2026', '15-08-2026', '03-09-2026']})
            df['joined'] = pd.to_datetime(df['joined'], format='%d-%m-%Y')

            today = pd.Timestamp('2026-10-13')
            df['weekday']    = df['joined'].dt.day_name()
            df['days_in']    = (today - df['joined']).dt.days
            df['course_end'] = df['joined'] + pd.DateOffset(months=6)
            print(df)
            print(df.dtypes)
            print()

            print(df[df['joined'] >= '2026-08-15']['name'].tolist())
            print(pd.date_range('2026-10-01', periods=4, freq='W-MON').strftime('%d %b').tolist())
        """),
        title='Example: Parse, Extract Parts, Date Arithmetic'),
    steps(
        ('Parse', '<code>pd.to_datetime(col, format="%d-%m-%Y")</code> or <code>parse_dates=</code> in read_csv; use <code>errors="coerce"</code> for dirty data.'),
        ('Check', 'dtype should be datetime64; look at min/max for impossible years.'),
        ('Extract', '<code>.dt.year</code>, <code>.dt.month</code>, <code>.dt.day_name()</code>, <code>.dt.to_period("M")</code>.'),
        ('Calculate', 'Subtract for durations; add <code>Timedelta</code>/<code>DateOffset</code>.'),
        ('Aggregate by time', '<code>set_index("date").resample("ME").sum()</code> or <code>groupby(pd.Grouper(key="date", freq="W"))</code>.'),
        title='Steps for Date Handling'),
    crossq(
        ('Timedelta vs DateOffset?', 'Timedelta is an exact duration (180 days); DateOffset follows calendar rules (6 months later, end of month, business days).'),
        ('How do you handle time zones?', '<code>dt.tz_localize("Asia/Kolkata")</code> to attach a zone to naive times, <code>dt.tz_convert("UTC")</code> to convert.'),
        ('Why give format= explicitly?', 'It is faster and removes ambiguity: "01-08-2026" is 1 August in India but 8 January to a US parser.'),
    ),
]),
])
