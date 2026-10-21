from build import *
from statq.anims import *
from statq.runner import strun, pyshow
from statq.data import STUDENTS, data_note

S = 'Python (SciPy) · uses sample data'
P = 'Python (SciPy · NumPy)'

SECTION = dict(level='intermediate', title='Sampling & Estimation', questions=[

# ------------------------------------------------------------------ 16
Q('What is the difference between a population and a sample? Explain sampling methods and sampling bias.', 'Sampling Methods', minutes=8, cards=[
    definition(
        defbox('The <strong>population</strong> is everyone you want to draw conclusions about; a <strong>sample</strong> is the subset you actually measure. '
               'Numbers describing the population are <strong>parameters</strong> (μ, σ, p); numbers computed from a sample are <strong>statistics</strong> '
               '(x̄, s, p̂) that estimate them.',
               'Probability sampling: <strong>simple random</strong> (every unit equally likely), <strong>stratified</strong> (random samples within groups such '
               'as centres, guaranteeing each is represented), <strong>cluster</strong> (randomly pick whole groups, e.g. batches, then survey everyone in them), '
               '<strong>systematic</strong> (every k-th unit). <strong>Convenience</strong> and voluntary-response samples are cheap but biased. '
               '<strong>Sampling bias</strong> (who gets in) cannot be fixed by a larger sample.'),
        tags('population', 'sample', 'parameter', 'statistic', 'stratified', 'cluster', 'sampling bias'),
    ),
    analogy('To check whether a pot of soup is salty you <strong>stir it and taste a spoonful</strong>. A random sample is the stirred spoon; tasting only the top '
            'layer is a biased sample, and a bigger spoon from the top layer does not help.'),
    sampling_anim(),
    real_world(
        scenario('Course feedback survey',
                 p('Asking only students who stay back after class (convenience) over-represents the keen ones. A stratified random sample of 20 students per '
                   'centre gives every centre a voice and smaller error for the same effort, and answers can be weighted back to the real centre sizes.')),
    ),
    example(
        data_note(),
        strun("""
            pop_mean = df['final_score'].mean()
            print(f'population (all 600): mean final score {pop_mean:.2f}, placed {df["placed"].mean():.3f}')

            srs = df.sample(60, random_state=1)
            strat = df.groupby('centre', group_keys=False).sample(frac=0.1, random_state=1)
            k = len(df) // 60
            syst = df.iloc[::k]
            clusters = df.assign(batch=np.arange(len(df)) % 20)              # 20 batches of 30
            chosen = np.random.default_rng(1).choice(20, 2, replace=False)
            clus = clusters[clusters['batch'].isin(chosen)]
            conv = df.nlargest(60, 'attendance')                              # "whoever is in class today"
            for name, s in [('simple random', srs), ('stratified', strat), ('systematic', syst), ('cluster (2 batches)', clus), ('convenience', conv)]:
                print(f'{name:20} n={len(s):3}  mean score {s["final_score"].mean():6.2f}  placed {s["placed"].mean():.3f}')
            print('stratified sample per centre:', strat['centre'].value_counts().to_dict())

            # bias does not shrink with size; random error does
            rng = np.random.default_rng(0)
            for n in [30, 60, 120]:
                srs_err = np.mean([abs(df.sample(n, random_state=int(s))['final_score'].mean() - pop_mean) for s in rng.integers(0, 10**6, 200)])
                print(f'n={n:3}: average error random {srs_err:.2f}   convenience {abs(df.nlargest(n, "attendance")["final_score"].mean() - pop_mean):.2f}')
        """, setup=STUDENTS, title=S),
        title='Example: Five Sampling Methods Compared With the Known Population'),
    steps(
        ('Define the population', 'Who exactly should the conclusion apply to?'),
        ('Get a sampling frame', 'A complete list (all enrolled students).'),
        ('Choose the method', 'Random; stratify on groups you must compare; cluster when travel/cost dominates.'),
        ('Draw with a seed', 'df.sample(n, random_state=…), groupby(...).sample(...).'),
        ('Check representativeness', 'Compare sample and population on known variables; weight if needed.'),
        title='Steps to Draw a Good Sample'),
    crossq(
        ('Why can a sample of 1,000 be worse than a sample of 100?', 'If the 1,000 come from a biased process (online poll, only attendees) their error is systematic; the random 100 is merely noisy.'),
        ('Stratified vs cluster sampling?', 'Stratified samples within every group (precise, guarantees coverage). Cluster samples a few whole groups (cheaper, but less precise if groups differ).'),
        ('What is survivorship bias?', 'Analysing only the units that "survived" a filter, e.g. surveying only students who finished the course about its difficulty.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is the central limit theorem and why is it so important?', 'Central Limit Theorem', minutes=9, cards=[
    definition(
        defbox('The <strong>central limit theorem (CLT)</strong>: for independent samples of size n from any population with mean μ and finite SD σ, the '
               'distribution of the <strong>sample mean</strong> approaches a normal distribution N(μ, σ/√n) as n grows, whatever the shape of the population. '
               'For moderately skewed data n ≈ 30 is often enough; strongly skewed data needs more.',
               'Why it matters: it justifies normal-based <strong>confidence intervals</strong> and <strong>t/z-tests</strong> for means and proportions even when '
               'the raw data is not normal, and it explains why averages are much more stable than individual values (spread shrinks by √n).'),
        tags('central limit theorem', 'sampling distribution', 'sample mean', 'σ/√n', 'normal approximation'),
    ),
    analogy('One student\'s package is unpredictable. The <strong>average package of a random group of 50</strong> is much more predictable, and if you repeat the '
            'experiment many times, those averages pile up into a neat bell curve, even though individual packages are very skewed.'),
    clt_anim(),
    real_world(
        scenario('Why batch averages are trustworthy',
                 p('Individual placement packages are strongly right-skewed, but the mean package of a batch of 50 placed students behaves almost normally. That is '
                   'what lets the placement cell attach a margin of error to "average package this year" and compare it with last year using a t-test.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            pop = df['salary_lpa'].dropna().to_numpy()
            mu, sigma = pop.mean(), pop.std()
            print(f'population of {len(pop)} packages: mean {mu:.3f}, SD {sigma:.3f}, skew {stats.skew(pop):.2f}')

            rng = np.random.default_rng(0)
            for n in [1, 5, 30, 100]:
                means = rng.choice(pop, size=(20_000, n), replace=True).mean(axis=1)
                print(f'n = {n:3}: mean of means {means.mean():.3f}  SD of means {means.std():.3f}  '
                      f'(σ/√n = {sigma / np.sqrt(n):.3f})  skew {stats.skew(means):+.2f}')

            means = rng.choice(pop, size=(20_000, 30)).mean(axis=1)
            counts, edges = np.histogram(means, bins=12)
            for c, e in zip(counts, edges):
                print(f'{e:5.2f} | ' + '#' * (c // 100))
            inside = np.mean(np.abs(means - mu) < 1.96 * sigma / np.sqrt(30))
            print(f'share of sample means within ±1.96·σ/√n: {inside:.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: Means of Skewed Packages Become Normal as n Grows'),
    steps(
        ('Start from any population', 'Here the skewed package distribution.'),
        ('Draw many samples of size n', 'rng.choice(pop, size=(reps, n)).'),
        ('Compute each sample mean', '.mean(axis=1).'),
        ('Compare with theory', 'Mean ≈ μ, SD ≈ σ/√n, skew → 0.'),
        ('Use the result', 'Normal/t-based intervals and tests for means.'),
        title='Steps to See the CLT in Action'),
    crossq(
        ('Does the CLT make the data normal?', 'No. It is about the distribution of the sample mean (or sum); the individual values keep their skew.'),
        ('Is n = 30 always enough?', 'No. It is a rule of thumb for mild skew; very skewed or heavy-tailed data (or rare-event proportions) needs much larger n.'),
        ('When does the CLT fail?', 'With infinite variance (e.g. Cauchy), strongly dependent observations, or when the "average" is dominated by a few huge values.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What is the standard error? How is it different from the standard deviation?', 'Standard Error', minutes=7, cards=[
    definition(
        defbox('The <strong>standard deviation</strong> describes how much <em>individual values</em> vary. The <strong>standard error</strong> (SE) describes how '
               'much a <em>statistic</em> (such as the sample mean) would vary from sample to sample: SE(x̄) = s/√n. For a proportion, SE(p̂) = √(p̂(1 − p̂)/n).',
               'SD does not shrink with more data; SE does, by √n: quadrupling the sample halves the SE. SE is the building block of confidence intervals '
               '(estimate ± critical value × SE) and test statistics (difference ÷ SE). <code>scipy.stats.sem</code> computes s/√n (ddof=1).'),
        tags('standard error', 'standard deviation', 'sem', 's/√n', 'precision', 'sample size'),
    ),
    analogy('SD is how much <strong>individual archers\' arrows</strong> scatter; SE is how much the <strong>average point of a team\'s arrows</strong> moves '
            'from one round to the next. A bigger team does not make each archer steadier, but its average becomes much steadier.'),
    se_anim(),
    real_world(
        scenario('Reporting a survey result',
                 p('"Average weekly study hours: 8.6 ± 0.18 (SE), n = 600" tells the reader the estimate is precise; "SD 4.3" tells them students differ a lot. '
                   'Confusing the two (reporting mean ± SE as if it were the spread of students) makes data look far more consistent than it is.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            h = df['study_hours']
            print(f'study hours: SD {h.std():.3f}   SE {h.std() / np.sqrt(len(h)):.3f}   scipy sem {stats.sem(h):.3f}')

            rng = np.random.default_rng(3)
            print(' n     SD of sample   SE formula   SD of 5000 sample means')
            for n in [25, 100, 400]:
                samples = rng.choice(h, size=(5000, n))
                print(f'{n:4}   {samples[0].std(ddof=1):10.3f}   {h.std() / np.sqrt(n):10.3f}   {samples.mean(axis=1).std():12.3f}')

            p = df['placed'].mean()
            print(f'placement rate {p:.3f}, SE {np.sqrt(p * (1 - p) / len(df)):.4f}')
            print(f'needed n to get SE = 0.01 for a rate near 0.35: {int(np.ceil(0.35 * 0.65 / 0.01 ** 2))}')
        """, setup=STUDENTS, title=S),
        title='Example: SD Stays, SE Shrinks with √n'),
    steps(
        ('Compute the SD', 'Spread of individuals (ddof=1).'),
        ('Divide by √n', 'SE of the mean; √(p(1−p)/n) for a proportion.'),
        ('Report the right one', 'Describing data → SD; precision of an estimate → SE or a CI.'),
        ('Plan sample size', 'n = (SD / target SE)².'),
        ('Use SE in inference', 'CIs and test statistics.'),
        title='Steps to Use the Standard Error'),
    crossq(
        ('Error bars on a chart: SD or SE?', 'Say which. SD bars show variability of individuals; SE (or 95 % CI) bars show uncertainty of the mean. They differ by √n.'),
        ('Why does SE shrink with √n and not n?', 'Variances of independent values add: Var(sum) = nσ², so Var(mean) = σ²/n and SE = σ/√n.'),
        ('Does SE account for bias?', 'No; it only measures random sampling error. A biased sample can have a tiny SE around the wrong value.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What is a confidence interval? How do you compute and interpret one?', 'Confidence Intervals', minutes=9, cards=[
    definition(
        defbox('A <strong>confidence interval</strong> (CI) gives a range of plausible values for a parameter: estimate ± critical value × SE. For a mean with '
               'unknown σ: x̄ ± t(0.975, n − 1)·s/√n. For a proportion, the <strong>Wilson</strong> interval is better than the simple p̂ ± 1.96·SE, especially '
               'for small n or p near 0 or 1.',
               'Interpretation: a 95 % CI comes from a procedure that captures the true value in 95 % of repeated samples. It is <strong>not</strong> "a 95 % '
               'probability that μ is in this particular interval" (μ is fixed). Higher confidence → wider interval; larger n → narrower (∝ 1/√n).'),
        tags('confidence interval', 'margin of error', 't interval', 'Wilson interval', 'coverage', 'confidence level'),
    ),
    analogy('A CI is a <strong>fishing net</strong> thrown at a fish you cannot see. The net is designed so that 95 out of 100 throws catch the fish. For any '
            'single throw, the fish is either in the net or not; the 95 % describes the net, not the fish.'),
    ci_anim(),
    real_world(
        scenario('Publishing the placement rate',
                 p('"35.3 % of students were placed (95 % CI 31.6 % to 39.2 %)" lets readers see the uncertainty. A centre with only 50 students would show a much '
                   'wider interval, which stops anyone over-interpreting a few percentage points of difference.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            from statsmodels.stats.proportion import proportion_confint
            s = df['final_score']
            n, m, se = len(s), s.mean(), stats.sem(s)
            t = stats.t.ppf(0.975, n - 1)
            print(f'mean {m:.2f}, SE {se:.3f}, t {t:.3f} -> 95 % CI [{m - t * se:.2f}, {m + t * se:.2f}]')
            print('same with scipy:', np.round(stats.t.interval(0.95, n - 1, loc=m, scale=se), 2))
            for conf in [0.90, 0.99]:
                print(f'{conf:.0%} CI:', np.round(stats.t.interval(conf, n - 1, loc=m, scale=se), 2))

            k = df['placed'].sum()
            print('placement rate', round(k / n, 3), '| Wald', np.round(proportion_confint(k, n, method='normal'), 3),
                  '| Wilson', np.round(proportion_confint(k, n, method='wilson'), 3))
            print('small centre, 3 of 12 placed | Wald', np.round(proportion_confint(3, 12, method='normal'), 3),
                  '| Wilson', np.round(proportion_confint(3, 12, method='wilson'), 3))

            # coverage: how often does the 95 % CI from a sample of 40 contain the population mean?
            rng = np.random.default_rng(8)
            hits = 0
            for _ in range(10_000):
                x = rng.choice(s, 40)
                lo, hi = stats.t.interval(0.95, 39, loc=x.mean(), scale=stats.sem(x))
                hits += lo <= m <= hi
            print(f'coverage of 10,000 intervals: {hits / 10_000:.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: t Interval for a Mean, Wilson Interval for a Rate, Coverage Simulation'),
    steps(
        ('Pick the parameter', 'Mean, proportion, difference, median…'),
        ('Compute estimate and SE', 'x̄ and s/√n; p̂ and its SE.'),
        ('Choose the confidence level', '95 % is conventional; get the t or z critical value.'),
        ('Build the interval', 'stats.t.interval; proportion_confint(method="wilson").'),
        ('Interpret correctly', 'Range of plausible values from a 95 %-reliable procedure.'),
        title='Steps to Build a Confidence Interval'),
    crossq(
        ('Why is the Wald interval poor for 3 of 12?', 'It is symmetric and relies on a normal approximation that fails for small n; it can even go below 0. Wilson stays inside [0, 1] and has better coverage.'),
        ('Two 95 % CIs overlap. Is the difference non-significant?', 'Not necessarily; overlapping CIs can still correspond to a significant difference. Compute a CI or test for the difference itself.'),
        ('How do you halve the width of a CI?', 'Quadruple the sample size (width ∝ 1/√n), or accept a lower confidence level.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What is bootstrapping? How do you get a confidence interval for a median?', 'Bootstrap', minutes=8, cards=[
    definition(
        defbox('The <strong>bootstrap</strong> estimates the sampling distribution of any statistic by <strong>resampling the data with replacement</strong>: draw '
               'n rows from the n observed rows many times (e.g. 10,000), compute the statistic each time, and look at the spread of those values. The SD of '
               'the bootstrap statistics estimates the SE; the 2.5th and 97.5th percentiles give a <strong>percentile CI</strong>.',
               'It needs no formula and no normality assumption, so it works for medians, percentiles, ratios, correlations and model metrics. '
               '<code>scipy.stats.bootstrap</code> does this for you and also offers the <strong>BCa</strong> interval (more accurate for smooth statistics such as means; it can fail for medians of data with many tied values). Limits: it assumes the sample represents the '
               'population, struggles with very small samples and extreme statistics (max), and must resample whole units (students, not rows) when data is '
               'grouped.'),
        tags('bootstrap', 'resampling', 'with replacement', 'percentile interval', 'BCa', 'scipy.stats.bootstrap'),
    ),
    analogy('You cannot survey the town again, so you <strong>photocopy your sample</strong> and draw new "samples" from the copies. How much the answer changes '
            'between these pretend surveys shows how much it would change between real ones.'),
    boot_anim(),
    real_world(
        scenario('Uncertainty of the median package',
                 p('The median package is the headline number, but there is no simple formula for its standard error. Bootstrapping the 212 placed students gives a '
                   '95 % interval of about 5.7 to 6.4 LPA, which the report can quote next to the median.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            sal = df['salary_lpa'].dropna().to_numpy()
            print(f'median package {np.median(sal):.2f} LPA (n = {len(sal)})')

            rng = np.random.default_rng(11)
            boots = np.array([np.median(rng.choice(sal, size=len(sal), replace=True)) for _ in range(10_000)])
            print(f'bootstrap SE {boots.std():.3f}   percentile 95 % CI [{np.percentile(boots, 2.5):.2f}, {np.percentile(boots, 97.5):.2f}]')
            print('one resample uses', len(np.unique(rng.choice(len(sal), len(sal)))), 'distinct students out of', len(sal))

            res = stats.bootstrap((sal,), np.median, n_resamples=10_000, confidence_level=0.95, method='percentile', random_state=11)
            print('scipy.stats.bootstrap percentile CI:', np.round([res.confidence_interval.low, res.confidence_interval.high], 2))

            # difference in median package between Kharghar and the rest
            placed = df.dropna(subset=['salary_lpa'])
            a = placed.loc[placed.centre == 'Kharghar', 'salary_lpa'].to_numpy()
            b = placed.loc[placed.centre != 'Kharghar', 'salary_lpa'].to_numpy()
            diff = lambda x, y, axis=-1: np.median(x, axis=axis) - np.median(y, axis=axis)
            r = stats.bootstrap((a, b), diff, n_resamples=5000, method='percentile', random_state=1)
            print(f'median difference Kharghar - others {diff(a, b):+.2f}, 95 % CI', np.round([r.confidence_interval.low, r.confidence_interval.high], 2))
        """, setup=STUDENTS, title=S),
        title='Example: Bootstrap CI for the Median Package and for a Difference of Medians'),
    steps(
        ('Choose the statistic', 'Median, percentile, ratio, correlation, model score…'),
        ('Resample with replacement', 'n draws from n rows, thousands of times (resample groups if data is clustered).'),
        ('Compute the statistic each time', 'Collect the bootstrap distribution.'),
        ('Summarise', 'SD = SE; 2.5/97.5 percentiles = 95 % CI (or BCa).'),
        ('Check stability', 'More resamples should not change the answer noticeably.'),
        title='Steps to Bootstrap a Statistic'),
    crossq(
        ('Why sample with replacement?', 'Without replacement, every resample of size n would be the original data. Replacement creates variation that mimics drawing new samples from the population.'),
        ('Does bootstrapping create new information?', 'No. It only estimates the uncertainty already implied by the sample; a small or biased sample stays small or biased.'),
        ('The CI for the median difference is [0.0, 1.5]. Is Kharghar\'s higher median real?', 'The interval touches 0, so the data is compatible with no difference; it is weak evidence at best. A larger sample or a pre-registered test would be needed.'),
        ('When does the bootstrap fail?', 'Very small samples, statistics at the edge (max, min), heavy dependence (time series need block bootstrap), and clustered data resampled at the wrong level.'),
    ),
]),
])
