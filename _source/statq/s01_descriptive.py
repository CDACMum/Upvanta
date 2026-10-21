from build import *
from statq.anims import *
from statq.runner import strun, pyshow
from statq.data import STUDENTS, data_note

S = 'Python (pandas · SciPy) · uses sample data'
P = 'Python (NumPy · SciPy)'

SECTION = dict(level='beginner', title='Descriptive Statistics', questions=[

# ------------------------------------------------------------------ 1
Q('What are the types of data and the levels of measurement (nominal, ordinal, interval, ratio)?', 'Types of Data', minutes=7, cards=[
    definition(
        defbox('Data is <strong>qualitative (categorical)</strong> — labels such as centre or course — or <strong>quantitative (numerical)</strong> — counts '
               'and measurements. Numerical data is <strong>discrete</strong> (countable: number of backlogs) or <strong>continuous</strong> (any value in a '
               'range: attendance %, salary).',
               'The <strong>level of measurement</strong> decides which statistics are meaningful: <strong>nominal</strong> (names only, no order: centre) → '
               'mode, counts; <strong>ordinal</strong> (ordered, unequal gaps: grade A/B/C, feedback 1–5) → median, percentiles; <strong>interval</strong> '
               '(equal gaps, no true zero: temperature in °C, calendar year) → mean, differences; <strong>ratio</strong> (true zero: salary, study hours) → '
               'all of these plus ratios ("twice as much").'),
        tags('qualitative', 'quantitative', 'discrete', 'continuous', 'nominal', 'ordinal', 'interval', 'ratio'),
    ),
    analogy('Think of a race. <strong>Bib numbers</strong> are nominal (just names), <strong>finishing positions</strong> are ordinal (1st beat 2nd, but by '
            'how much?), <strong>clock times of day</strong> are interval, and <strong>race durations</strong> are ratio: a 2-hour run really is twice a '
            '1-hour run.'),
    types_anim(),
    real_world(
        scenario('Choosing the right summary for each column',
                 p('The academic report for a batch shows the most common centre (mode), the median feedback rating (ordinal), and mean attendance and package '
                   '(ratio). Averaging feedback codes or centre IDs would produce numbers that look precise but mean nothing.')),
    ),
    example(
        data_note(),
        strun("""
            print(df.dtypes)
            levels = {'centre': 'nominal', 'course': 'nominal', 'method': 'nominal',
                      'attendance': 'ratio (continuous)', 'study_hours': 'ratio (continuous)',
                      'final_score': 'interval-like score', 'placed': 'nominal (binary)', 'salary_lpa': 'ratio (continuous)'}
            for col, lvl in levels.items():
                print(f'{col:12} {lvl}')

            # ordinal data: grades have an order, so they deserve an ordered categorical
            grade = pd.cut(df['final_score'], [0, 50, 60, 70, 100], labels=['D', 'C', 'B', 'A'])
            print(grade.dtype, '| ordered:', grade.cat.ordered)
            print(grade.value_counts().sort_index())
            print('median grade:', grade.cat.categories[int(np.median(grade.cat.codes))])
            print('most common centre (mode):', df['centre'].mode()[0])
        """, setup=STUDENTS, title=S),
        title='Example: Classify Each Column and Summarise It Appropriately'),
    steps(
        ('List the columns', 'df.dtypes / df.info() show storage types, not statistical types.'),
        ('Decide the level for each', 'Nominal, ordinal, interval or ratio.'),
        ('Encode it correctly', 'category / ordered category for labels; numbers for measurements.'),
        ('Choose summaries', 'Mode for nominal, median for ordinal, mean/std for interval and ratio.'),
        ('Choose charts and tests', 'Bar charts and chi-square for categories; histograms and t-tests for numbers.'),
        title='Steps to Classify Data'),
    crossq(
        ('Is a roll number numeric data?', 'No. It is stored as digits but it is nominal: adding or averaging roll numbers is meaningless.'),
        ('Can you take the mean of a 1–5 Likert rating?', 'Strictly it is ordinal, so median and percentages per level are safest; in practice means of multi-item scales are common but should be reported with care.'),
        ('Why is temperature in °C interval and not ratio?', '0 °C is not "no temperature", so 20 °C is not twice as hot as 10 °C. Kelvin has a true zero and is ratio.'),
        ('Is "placed (1/0)" quantitative?', 'It is a binary nominal variable, but coding it as 0/1 makes its mean equal the proportion placed, which is very useful.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain mean, median and mode. When is the median better than the mean?', 'Central Tendency', minutes=7, cards=[
    definition(
        defbox('<strong>Mean</strong> = sum ÷ count; it uses every value, so a few extreme values pull it. <strong>Median</strong> = the middle value of the '
               'sorted data (average of the two middle values for an even count); it is <strong>robust</strong> to outliers. <strong>Mode</strong> = the most '
               'frequent value; the only one that works for nominal data, and data can be bimodal.',
               'For <strong>symmetric</strong> data mean ≈ median. For <strong>right-skewed</strong> data (salaries, house prices, waiting times) the mean is '
               'pulled above the median, so the median better describes a typical value. A <strong>trimmed mean</strong> (drop the top and bottom x %) is a '
               'compromise. Weighted means account for different group sizes or credits.'),
        tags('mean', 'median', 'mode', 'trimmed mean', 'weighted mean', 'robust'),
    ),
    analogy('Ten friends earn ₹50,000 a month each. A billionaire walks into the café: the <strong>mean</strong> income of the room becomes enormous, but the '
            '<strong>median</strong> person in the room still earns ₹50,000.'),
    central_anim(),
    real_world(
        scenario('Reporting placement packages honestly',
                 p('A brochure that reports only the mean package can be lifted by a single 40 LPA offer. Institutions that want a fair picture report the '
                   'median package, the mean, and the highest package separately, and state how many students were placed.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            sal = df['salary_lpa'].dropna()
            print(f'placed students {len(sal)} | mean {sal.mean():.2f} LPA | median {sal.median():.2f} LPA | mode {sal.mode()[0]} LPA')

            star = pd.concat([sal, pd.Series([60.0])])          # one exceptional offer
            print(f'with one 60 LPA offer: mean {star.mean():.2f} | median {star.median():.2f} | 10 % trimmed mean {stats.trim_mean(star, 0.1):.2f}')

            print('most common centre:', df['centre'].mode()[0], '| course mode:', df['course'].mode()[0])

            # weighted mean: overall average of centre averages must weight by centre size
            g = df.groupby('centre')['final_score'].agg(['mean', 'size'])
            print(g.round(2))
            print(f'simple mean of centre means {g["mean"].mean():.3f} vs weighted {np.average(g["mean"], weights=g["size"]):.3f} '
                  f'= overall mean {df["final_score"].mean():.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: Packages — Mean vs Median vs Trimmed Mean, and a Weighted Mean'),
    steps(
        ('Look at the distribution first', 'Histogram or describe(); is it skewed or are there outliers?'),
        ('Symmetric, no outliers', 'Report the mean (with standard deviation).'),
        ('Skewed or outliers', 'Report the median (with IQR), optionally also the mean.'),
        ('Categories', 'Report the mode and the share of each category.'),
        ('Combining groups', 'Use a weighted mean, never the plain mean of group means.'),
        title='Steps to Choose a Measure of Centre'),
    crossq(
        ('Mean > median. What does that tell you?', 'The distribution is probably right-skewed (a long tail of large values) or has high outliers.'),
        ('Can the median be misleading?', 'Yes: it ignores how far values are from the middle, so two very different distributions can share a median. Report spread too.'),
        ('What is the mode of continuous data?', 'Exact repeated values are rare, so the mode is taken from a histogram bin or a density estimate (the peak).'),
        ('Why does the average of centre averages differ from the overall average?', 'Centres have different sizes; each student should count once, so group means must be weighted by group size.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('How do you measure spread? Explain range, variance, standard deviation, IQR and coefficient of variation.', 'Measures of Dispersion', minutes=8, cards=[
    definition(
        defbox('<strong>Range</strong> = max − min (uses only two values). <strong>Variance</strong> = average squared deviation from the mean; '
               '<strong>standard deviation</strong> (SD) = √variance, in the original units. For a <strong>sample</strong> divide by n − 1 (Bessel\'s '
               'correction, <code>ddof=1</code>), because deviations from the sample mean are slightly too small; pandas uses ddof=1, NumPy defaults to ddof=0.',
               '<strong>IQR</strong> = Q3 − Q1, the spread of the middle 50 %, robust to outliers (pair it with the median). <strong>MAD</strong> (median '
               'absolute deviation) is another robust measure. <strong>Coefficient of variation</strong> CV = SD ÷ mean compares variability between variables '
               'with different units or scales (ratio data only).'),
        tags('range', 'variance', 'standard deviation', 'ddof', 'IQR', 'MAD', 'coefficient of variation'),
    ),
    analogy('Two batches both average 60 marks. In one everyone scored 55–65; in the other half scored 30 and half 90. The <strong>average hides the '
            'difference; the spread reveals it</strong>, like two cricketers with the same average where one is consistent and the other is all-or-nothing.'),
    spread_anim(),
    real_world(
        scenario('Consistency across centres',
                 p('Two centres have similar mean final scores, but one has a much larger standard deviation: some students are being left behind. The '
                   'coordinator compares SD and IQR per centre, not just averages, before deciding where to add remedial sessions.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            x = np.array([55, 60, 62, 65, 58])
            print('values', x, '| mean', x.mean())
            print('squared deviations', (x - x.mean()) ** 2)
            print(f'population variance (ddof=0) {x.var():.2f}   sample variance (ddof=1) {x.var(ddof=1):.2f}')
            print(f'pandas std default {pd.Series(x).std():.3f}  = NumPy std(ddof=1) {x.std(ddof=1):.3f}  (NumPy default {x.std():.3f})')

            for col in ['attendance', 'study_hours', 'final_score']:
                s = df[col]
                q1, q3 = s.quantile([0.25, 0.75])
                print(f'{col:12} range {s.max() - s.min():5.1f}  SD {s.std():5.2f}  IQR {q3 - q1:5.2f}  '
                      f'MAD {stats.median_abs_deviation(s):5.2f}  CV {s.std() / s.mean():.2f}')

            print(df.groupby('centre')['final_score'].agg(['mean', 'std', lambda s: s.quantile(.75) - s.quantile(.25)])
                    .rename(columns={'<lambda_0>': 'IQR'}).round(2))
        """, setup=STUDENTS, title=S),
        title='Example: Variance by Hand, ddof, and Spread Measures for Three Columns'),
    steps(
        ('Pick the centre measure first', 'Mean → report SD; median → report IQR.'),
        ('Use ddof=1 for samples', 'pandas does this by default; NumPy needs ddof=1.'),
        ('Check robustness', 'Compare SD with IQR/MAD; a big difference signals outliers.'),
        ('Compare variables', 'Use CV when units or scales differ.'),
        ('Compare groups', 'groupby + std / IQR per group.'),
        title='Steps to Describe Spread'),
    crossq(
        ('Why square the deviations instead of using absolute values?', 'Squares are mathematically convenient (differentiable, variances of independent variables add) and connect to the normal distribution; absolute deviations give the more robust MAD.'),
        ('Why n − 1?', 'The sample mean is computed from the same data, so deviations around it are systematically smaller than around the true mean; dividing by n − 1 makes the variance estimate unbiased.'),
        ('When is CV meaningless?', 'For interval data or means near zero (e.g. temperature in °C, profit that can be negative): dividing by a mean close to 0 explodes.'),
        ('SD is 0. What does that mean?', 'Every value is identical; the column carries no information.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What are percentiles and quartiles? How does a box plot detect outliers with the 1.5 × IQR rule?', 'Percentiles & Box Plots', minutes=8, cards=[
    definition(
        defbox('The <strong>p-th percentile</strong> is the value below which p % of the data falls. <strong>Quartiles</strong> are the 25th (Q1), 50th '
               '(Q2 = median) and 75th (Q3) percentiles. The <strong>five-number summary</strong> (min, Q1, median, Q3, max) is what a '
               '<strong>box plot</strong> draws: the box spans Q1–Q3, the line is the median, the whiskers reach the furthest points within the fences.',
               '<strong>Tukey\'s fences</strong>: values below Q1 − 1.5·IQR or above Q3 + 1.5·IQR are flagged as outliers (3·IQR for "extreme"). '
               'A <strong>percentile rank</strong> answers the opposite question: "what percentage scored below this student?". Different software uses '
               'slightly different interpolation rules for percentiles on small samples.'),
        tags('percentile', 'quartile', 'five-number summary', 'box plot', 'IQR fences', 'percentile rank'),
    ),
    analogy('Line up the whole batch by height. The <strong>quartiles</strong> are the people standing at the quarter, half and three-quarter marks of the line; '
            'anyone standing far beyond the end of the line (past the fences) is the one you look at twice.'),
    boxplot_anim(),
    real_world(
        scenario('"Top 10 %" and data checks',
                 p('Merit scholarships go to students above the 90th percentile of the final score, and each student\'s report shows their percentile rank. The '
                   'same fences flag suspicious package entries (a 19.8 LPA package might be real, or a typo) for checking before the placement report is published.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            sal = df['salary_lpa'].dropna()
            q1, med, q3 = sal.quantile([0.25, 0.5, 0.75])
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            print(f'five-number summary: min {sal.min()}  Q1 {q1}  median {med}  Q3 {q3}  max {sal.max()}')
            print(f'IQR {iqr:.2f} -> fences [{lo:.2f}, {hi:.2f}]')
            out = sal[(sal < lo) | (sal > hi)]
            print(f'{len(out)} outliers:', sorted(out.tolist()))

            cut = df['final_score'].quantile(0.90)
            print(f'90th percentile of final score {cut:.2f} -> {(df["final_score"] >= cut).sum()} students qualify')
            print(f'a score of 70 beats {stats.percentileofscore(df["final_score"], 70):.1f} % of students')
            print('deciles:', np.percentile(df['final_score'], range(10, 100, 10)).round(1))
            x = [1, 2, 3, 4]
            print('25th percentile of [1,2,3,4] by method:', {m: float(np.percentile(x, 25, method=m)) for m in ['linear', 'lower', 'midpoint', 'nearest']})
        """, setup=STUDENTS, title=S),
        title='Example: Five-Number Summary, Fences, Top 10 % and Percentile Rank'),
    steps(
        ('Compute quartiles', 'Series.quantile([.25, .5, .75]) or np.percentile.'),
        ('Compute IQR and fences', 'Q1 − 1.5·IQR, Q3 + 1.5·IQR.'),
        ('Flag, do not delete', 'Investigate each outlier: error or genuine extreme?'),
        ('Draw the box plot', 'df.boxplot(column, by=group) to compare groups.'),
        ('Report percentiles', 'Thresholds (top 10 %) and percentile ranks for individuals.'),
        title='Steps to Use Percentiles and Box Plots'),
    crossq(
        ('Are all box-plot outliers errors?', 'No. In skewed data (packages, incomes) the long tail naturally exceeds the fences; they must be checked, not removed automatically.'),
        ('Percentile vs percentage?', 'A percentage is a score out of 100; a percentile is a position in the group. 70 % marks can be the 85th percentile in a hard paper.'),
        ('Why 1.5?', 'Tukey\'s convention: for normal data the fences sit at about ±2.7 SD, so only about 0.7 % of points are flagged.'),
        ('Why do Excel and NumPy give different quartiles for small data?', 'They use different interpolation rules (method=linear, inclusive/exclusive). Differences vanish as n grows.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What are skewness and kurtosis? How do you describe the shape of a distribution?', 'Skewness & Kurtosis', minutes=7, cards=[
    definition(
        defbox('<strong>Skewness</strong> measures asymmetry: 0 for symmetric data, <strong>positive</strong> (right-skewed) when a long tail extends to large '
               'values (mean &gt; median: income, study hours), <strong>negative</strong> (left-skewed) when the tail goes to small values (an easy exam: most '
               'score high, a few very low). Rule of thumb: |skew| &lt; 0.5 roughly symmetric, &gt; 1 strongly skewed.',
               '<strong>Kurtosis</strong> measures tail heaviness. pandas and SciPy report <strong>excess kurtosis</strong> (normal = 0): positive = heavier '
               'tails / more outliers than normal (leptokurtic), negative = lighter tails (platykurtic, e.g. uniform = −1.2). Shape matters because many '
               'methods assume roughly normal data; skewed data is often transformed (log, square root).'),
        tags('skewness', 'kurtosis', 'excess kurtosis', 'right-skewed', 'left-skewed', 'log transform'),
    ),
    analogy('Pour sand on a table. A neat <strong>symmetric</strong> heap has skew 0. If a fan blows from the left, the sand drifts into a long tail to the right: '
            '<strong>positive skew</strong>. Kurtosis is about how much sand ends up far away from the heap, in the tails.'),
    shape_anim(),
    real_world(
        scenario('Before you average or model a column',
                 p('Weekly study hours and placement packages are right-skewed. Before using them in a regression or reporting a mean ± SD, the analyst checks skew, '
                   'reports medians, and uses a log transform, which makes the package distribution nearly symmetric.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            cols = ['attendance', 'study_hours', 'final_score', 'salary_lpa']
            print(pd.DataFrame({'skew': df[cols].skew(), 'excess kurtosis': df[cols].kurt(),
                                'mean - median': df[cols].mean() - df[cols].median()}).round(3))

            sal = df['salary_lpa'].dropna()
            print(f'log(package) skew {np.log(sal).skew():.3f} (was {sal.skew():.3f})')

            counts, edges = np.histogram(df['study_hours'], bins=10)
            for c, e in zip(counts, edges):
                print(f'{e:5.1f}+ | ' + '#' * (c // 5))

            rng = np.random.default_rng(1)
            for name, sample in [('normal', rng.normal(size=100_000)), ('uniform', rng.uniform(size=100_000)),
                                 ('t (df=5)', rng.standard_t(5, size=100_000))]:
                print(f'{name:9} skew {stats.skew(sample):+.2f}  excess kurtosis {stats.kurtosis(sample):+.2f}')
        """, setup=STUDENTS, title=S),
        title='Example: Skew and Kurtosis of Real Columns, a Log Transform, Reference Shapes'),
    steps(
        ('Plot a histogram', 'Look before computing.'),
        ('Compute skew and kurtosis', 'df.skew(), df.kurt() (excess kurtosis).'),
        ('Compare mean and median', 'The gap confirms the direction of skew.'),
        ('Transform if needed', 'log / sqrt for right skew; Box-Cox or Yeo-Johnson in general.'),
        ('Choose methods accordingly', 'Medians, non-parametric tests or transformed data for strongly skewed variables.'),
        title='Steps to Describe Shape'),
    crossq(
        ('Which way does the tail point in a right-skewed distribution?', 'To the right (large values). The name follows the tail, not the peak; the peak is on the left.'),
        ('Uniform data has kurtosis −1.2. Why negative?', 'Excess kurtosis compares with the normal (0). A uniform has no tails at all, lighter than normal.'),
        ('Why does a log transform reduce right skew?', 'It compresses large values much more than small ones (log 10 = 1, log 100 = 2), pulling in the long right tail.'),
        ('Is skew 0 proof of normality?', 'No. Symmetric distributions can have heavy tails or two peaks; check plots (histogram, Q-Q) too.'),
    ),
]),
])
