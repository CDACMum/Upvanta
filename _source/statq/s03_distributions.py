from build import *
from statq.anims import *
from statq.runner import strun, pyshow
from statq.data import STUDENTS, data_note

S = 'Python (SciPy) · uses sample data'
P = 'Python (SciPy · NumPy)'

SECTION = dict(level='intermediate', title='Probability Distributions', questions=[

# ------------------------------------------------------------------ 11
Q('Explain the binomial and Poisson distributions. When do you use each?', 'Binomial & Poisson', minutes=8, cards=[
    definition(
        defbox('<strong>Binomial(n, p)</strong>: the number of successes in n independent trials, each with success probability p (placed / not placed, '
               'defective / fine). P(X = k) = C(n, k)·pᵏ·(1 − p)ⁿ⁻ᵏ; mean np, variance np(1 − p).',
               '<strong>Poisson(λ)</strong>: the number of events in a fixed interval when events occur independently at a constant average rate λ (doubts '
               'raised per hour, server errors per day, typos per page). P(X = k) = e^(−λ)·λᵏ / k!; mean = variance = λ. For large n and small p, '
               'Binomial(n, p) ≈ Poisson(np). In SciPy: <code>stats.binom</code>, <code>stats.poisson</code> with <code>pmf</code>, <code>cdf</code>, '
               '<code>sf</code> (= 1 − cdf), <code>ppf</code>, <code>rvs</code>.'),
        tags('binomial', 'Poisson', 'pmf', 'cdf', 'sf', 'Bernoulli trial', 'rate λ'),
    ),
    analogy('Binomial is <strong>counting heads in a fixed number of coin tosses</strong>. Poisson is <strong>counting raindrops landing on a tile in one '
            'minute</strong>: there is no fixed number of "tries", just an average rate.'),
    binom_anim(),
    real_world(
        scenario('Planning interview slots and doubt sessions',
                 p('If a company shortlists 10 students and each clears the interview with probability 0.35, the binomial tells the placement cell how likely it '
                   'is that at least 5 get offers. If students raise on average 4 doubts per hour in a lab, the Poisson tells the TA how often an hour will bring '
                   '8 or more, and whether a second TA is needed.')),
    ),
    example(
        strun("""
            from scipy import stats
            b = stats.binom(n=10, p=0.35)
            print('P(X = k) for k = 0..10:', b.pmf(range(11)).round(3))
            print(f'P(exactly 3) = {b.pmf(3):.4f}   P(at most 3) = {b.cdf(3):.4f}   P(at least 5) = {b.sf(4):.4f}')
            print(f'mean = np = {b.mean():.2f}   variance = np(1-p) = {b.var():.3f}')

            po = stats.poisson(mu=4)
            print(f'doubts per hour ~ Poisson(4): P(0) = {po.pmf(0):.4f}  P(8 or more) = {po.sf(7):.4f}  mean {po.mean()} var {po.var()}')
            print('95th percentile of hourly doubts:', po.ppf(0.95))

            # Poisson approximation to a binomial with large n, small p
            n, p = 2000, 0.002            # 2000 exam scripts, 0.2 % have a totalling error
            for k in [0, 2, 4, 6]:
                print(f'k={k}: binomial {stats.binom.pmf(k, n, p):.4f}   Poisson(np=4) {stats.poisson.pmf(k, n * p):.4f}')

            sims = np.random.default_rng(1).poisson(4, size=100_000)
            print(f'simulated mean {sims.mean():.3f}, variance {sims.var():.3f}')
        """, title=P),
        title='Example: Interview Offers (Binomial), Doubts per Hour (Poisson), the Approximation'),
    steps(
        ('Identify the count', 'Successes in n trials → binomial; events in an interval → Poisson.'),
        ('Check assumptions', 'Independence; constant p or constant rate λ.'),
        ('Create the distribution', 'stats.binom(n, p) or stats.poisson(λ).'),
        ('Ask the question', 'pmf for "exactly", cdf for "at most", sf for "more than".'),
        ('Validate', 'Compare mean and variance of real counts; overdispersion → negative binomial.'),
        title='Steps to Use Binomial and Poisson Models'),
    crossq(
        ('Why is P(at least 5) = sf(4) and not sf(5)?', 'sf(k) = P(X > k). "At least 5" is X > 4. This off-by-one is the most common SciPy mistake with discrete distributions.'),
        ('Real counts have variance much larger than the mean. Is Poisson still right?', 'No; that is overdispersion (events cluster). A negative binomial or a model with covariates fits better.'),
        ('Is a Bernoulli distribution different from a binomial?', 'Bernoulli is the single-trial case, Binomial(1, p); a binomial is the sum of n independent Bernoulli trials.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What is the normal distribution? Explain z-scores and the 68-95-99.7 rule.', 'Normal Distribution & z-scores', minutes=9, cards=[
    definition(
        defbox('The <strong>normal (Gaussian) distribution</strong> N(μ, σ) is the symmetric bell curve fully described by its mean μ and standard deviation σ. '
               'Many measurements are approximately normal because they add up many small independent effects, and sample means are approximately normal '
               'thanks to the central limit theorem.',
               'A <strong>z-score</strong> z = (x − μ) / σ says how many SDs a value is from the mean, putting different scales on one footing. The '
               '<strong>empirical rule</strong>: about 68 % of values lie within ±1σ, 95 % within ±2σ (exactly ±1.96σ), 99.7 % within ±3σ. '
               '<code>stats.norm.cdf(z)</code> gives the area to the left; <code>stats.norm.ppf(q)</code> the cut-off for a given area.'),
        tags('normal distribution', 'Gaussian', 'z-score', 'standardisation', 'empirical rule', 'cdf / ppf'),
    ),
    analogy('A z-score is a <strong>common currency</strong>: 75 marks in an easy paper and 62 in a hard one can only be compared after converting both to '
            '"how far above the class average, in SDs".'),
    normal_anim(),
    real_world(
        scenario('Comparing students across papers and setting cut-offs',
                 p('Different modules have different averages and spreads. Converting each student\'s marks to z-scores identifies who is genuinely strong relative '
                   'to peers, and <code>norm.ppf(0.90)</code> gives the cut-off for the top 10 % when scores are roughly normal.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            s = df['final_score']
            mu, sd = s.mean(), s.std()
            print(f'final score: mean {mu:.2f}, SD {sd:.2f}')
            for k in [1, 2, 3]:
                inside = s.between(mu - k * sd, mu + k * sd).mean()
                print(f'within ±{k} SD: observed {inside:.3f}   normal theory {stats.norm.cdf(k) - stats.norm.cdf(-k):.3f}')

            z = (75 - mu) / sd
            print(f'a score of 75 -> z = {z:.2f} -> above {stats.norm.cdf(z):.1%} (normal) / {(s < 75).mean():.1%} (actual)')
            print(f'top-10 % cut-off: normal model {stats.norm.ppf(0.90, mu, sd):.2f}  vs actual 90th percentile {s.quantile(0.90):.2f}')

            # comparing two papers with z-scores
            sql = dict(score=75, mean=68, sd=6)
            ml = dict(score=62, mean=50, sd=8)
            for name, d in [('SQL', sql), ('ML', ml)]:
                print(f'{name}: {d["score"]} marks -> z = {(d["score"] - d["mean"]) / d["sd"]:+.2f}')
            print('critical values: z for 90 %, 95 %, 99 % two-sided =', stats.norm.ppf([0.95, 0.975, 0.995]).round(3))
        """, setup=STUDENTS, title=S),
        title='Example: Empirical Rule on Real Scores, z-scores, Cut-offs, Critical Values'),
    steps(
        ('Check the shape', 'Histogram / Q-Q plot: roughly symmetric and bell-shaped?'),
        ('Estimate μ and σ', 'Sample mean and SD.'),
        ('Standardise', 'z = (x − μ)/σ to compare across scales.'),
        ('Probabilities', 'norm.cdf / norm.sf for areas; norm.ppf for cut-offs.'),
        ('Verify against data', 'Compare model predictions with actual shares.'),
        title='Steps to Use the Normal Model'),
    crossq(
        ('Which is better, 75 in SQL or 62 in ML?', '62 in ML: z = +1.50 versus +1.17 for SQL. Relative to their classes, the ML score is more exceptional.'),
        ('Why 1.96 and not 2?', '±1.96σ contains exactly 95 % of a normal distribution; 2σ contains 95.45 %.'),
        ('Is all real data normal?', 'No. Incomes, waiting times and counts are skewed; bounded scores have no long tails. Check before relying on normal-based cut-offs.'),
        ('Does standardising make data normal?', 'No. z-scores change location and scale, not shape; a skewed variable stays skewed.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What is the difference between a PDF and a CDF? Explain the uniform and exponential distributions.', 'Continuous Distributions', minutes=8, cards=[
    definition(
        defbox('For a continuous variable, the <strong>PDF</strong> (density) f(x) is the height of the curve; probabilities are <strong>areas</strong>: '
               'P(a &lt; X &lt; b) = ∫ f(x) dx. Density values can exceed 1. The <strong>CDF</strong> F(x) = P(X ≤ x) rises from 0 to 1; '
               'P(a &lt; X &lt; b) = F(b) − F(a). The inverse CDF (<code>ppf</code>) gives quantiles.',
               '<strong>Uniform(a, b)</strong>: every value in [a, b] equally likely; mean (a + b)/2. <strong>Exponential(λ)</strong>: waiting time until the '
               'next event in a Poisson process; mean 1/λ, P(T &gt; t) = e^(−λt), and it is <strong>memoryless</strong>: having waited 5 minutes does not '
               'change the distribution of the remaining wait. SciPy uses <code>scale = 1/λ</code>.'),
        tags('PDF', 'CDF', 'ppf', 'uniform', 'exponential', 'memoryless', 'scale parameter'),
    ),
    analogy('The PDF is a <strong>map of crowd density</strong> along a street; the CDF is the <strong>running count</strong> of people you have passed so far. '
            'You find how many people are between two shops by subtracting two running counts.'),
    pdfcdf_anim(),
    real_world(
        scenario('Lab server requests',
                 p('Job submissions to the lab Spark cluster arrive at about 3 per minute. The gap between submissions is roughly exponential with mean 20 seconds, '
                   'so the admin can estimate how often the cluster sits idle for over a minute, and how long a monitoring script should wait before alerting.')),
    ),
    example(
        strun("""
            from scipy import stats
            u = stats.uniform(loc=10, scale=20)            # Uniform(10, 30): arrival minute of a guest speaker
            print(f'Uniform(10,30): pdf {u.pdf(15):.3f}  P(X <= 15) = {u.cdf(15):.2f}  P(15 < X < 20) = {u.cdf(20) - u.cdf(15):.2f}  mean {u.mean()}')

            rate = 3                                         # jobs per minute
            e = stats.expon(scale=1 / rate)                  # SciPy uses scale = 1/λ
            print(f'mean gap {e.mean() * 60:.0f} s   P(gap > 1 min) = {e.sf(1):.4f} = exp(-3) = {np.exp(-3):.4f}')
            print(f'median gap {e.median() * 60:.1f} s   90th percentile {e.ppf(0.9) * 60:.1f} s')
            print(f'density at 0 is {e.pdf(0):.1f} (> 1 is fine: it is a density, not a probability)')

            # memoryless: P(T > 1.5 | T > 1) == P(T > 0.5)
            print(f'P(T > 1.5 | T > 1) = {e.sf(1.5) / e.sf(1):.4f}   P(T > 0.5) = {e.sf(0.5):.4f}')

            rng = np.random.default_rng(2)
            gaps = rng.exponential(1 / rate, 200_000)
            counts = np.histogram(gaps.cumsum(), bins=np.arange(0, gaps.sum(), 1))[0]
            print(f'simulated jobs per minute: mean {counts.mean():.3f}, variance {counts.var():.3f}  (Poisson: both = 3)')
        """, title=P),
        title='Example: Uniform Arrival Time, Exponential Gaps, Memorylessness, Link to Poisson'),
    steps(
        ('Choose the distribution', 'Equal chance in a range → uniform; waiting time at a constant rate → exponential.'),
        ('Parameterise correctly', 'SciPy: loc and scale (scale = 1/λ for exponential).'),
        ('Use the CDF for probabilities', 'cdf / sf and differences of cdf values.'),
        ('Use ppf for thresholds', 'Medians, percentiles, timeouts.'),
        ('Check with data or simulation', 'Histogram of observed gaps vs the fitted pdf.'),
        title='Steps to Work With Continuous Distributions'),
    crossq(
        ('Can a PDF value be greater than 1?', 'Yes. Only the total area must be 1; a narrow, tall density (exponential with rate 3 starts at 3) is valid.'),
        ('How are Poisson and exponential related?', 'If events follow a Poisson process with rate λ, the counts per interval are Poisson(λ) and the gaps between events are exponential with mean 1/λ.'),
        ('Is human waiting time memoryless?', 'Rarely: a process that wears out or gets fixed has an increasing or decreasing hazard; Weibull or gamma distributions model that.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('What are the t, chi-square and F distributions, and where are they used?', 't, Chi-square & F', minutes=8, cards=[
    definition(
        defbox('These <strong>sampling distributions</strong> describe test statistics computed from normal samples. The <strong>t distribution</strong> '
               '(degrees of freedom df = n − 1 for one mean) looks like a normal with heavier tails, because σ is estimated from the sample; as df grows it '
               'approaches N(0, 1). Used in t-tests and confidence intervals for means and regression coefficients.',
               'The <strong>chi-square</strong> distribution (sum of squared standard normals; right-skewed, mean = df) is used for variance tests, '
               'goodness-of-fit and contingency-table tests. The <strong>F distribution</strong> (ratio of two scaled chi-squares) compares variances: '
               'ANOVA and the overall F-test in regression.'),
        tags('t distribution', 'degrees of freedom', 'chi-square', 'F distribution', 'critical value', 'sampling distribution'),
    ),
    analogy('The t distribution is the normal curve <strong>wearing a safety margin</strong>: with only a few observations you are less sure of σ, so the tails '
            'are fatter and the critical values wider. With many observations the margin is no longer needed.'),
    tdist_anim(),
    real_world(
        scenario('Small pilot studies',
                 p('A pilot of a new lab format runs with only 12 students. A 95 % confidence interval for their mean improvement must use t with 11 degrees of '
                   'freedom (critical value 2.20, not 1.96), otherwise the uncertainty is understated by about 12 %.')),
    ),
    example(
        strun("""
            from scipy import stats
            print('two-sided 95 % critical values:')
            for df_ in [2, 5, 11, 30, 100, 1000]:
                print(f'  t(df={df_:4}) {stats.t.ppf(0.975, df_):.3f}')
            print(f'  normal       {stats.norm.ppf(0.975):.3f}')
            print(f'P(|T| > 3) with df=5: {2 * stats.t.sf(3, 5):.4f}   normal: {2 * stats.norm.sf(3):.4f}')

            c = stats.chi2(df=4)
            print(f'chi-square(4): mean {c.mean()}, 95th percentile {c.ppf(0.95):.3f}')
            rng = np.random.default_rng(0)
            z = rng.standard_normal((100_000, 4))
            print(f'sum of 4 squared normals: simulated 95th pct {np.percentile((z ** 2).sum(axis=1), 95):.3f}')

            print(f'F(2, 597) 95th percentile (one-way ANOVA, 3 groups, 600 students): {stats.f.ppf(0.95, 2, 597):.3f}')

            # where t comes from: standardising a sample mean with the SAMPLE sd
            samples = rng.normal(50, 10, size=(100_000, 6))
            tstat = (samples.mean(1) - 50) / (samples.std(1, ddof=1) / np.sqrt(6))
            print(f'share of |t| > 1.96 with n=6: {(np.abs(tstat) > 1.96).mean():.3f}  (t(5) predicts {2 * stats.t.sf(1.96, 5):.3f}, normal 0.050)')
        """, title=P),
        title='Example: Critical Values, Tail Probabilities, and Where t Comes From'),
    steps(
        ('Identify the statistic', 'Mean with unknown σ → t; variances / counts → chi-square; ratio of variances → F.'),
        ('Find the degrees of freedom', 'n − 1, (r − 1)(c − 1), (k − 1, N − k), …'),
        ('Get critical values or p-values', 'stats.t.ppf / stats.t.sf, stats.chi2, stats.f.'),
        ('Prefer software tests', 'ttest_ind, chi2_contingency, f_oneway compute these for you.'),
        ('Remember the assumptions', 'Normality matters most for small samples.'),
        title='Steps to Use These Distributions'),
    crossq(
        ('Why does t have heavier tails than the normal?', 'The denominator uses the sample SD, which itself varies; occasionally it is small, inflating the statistic.'),
        ('When can you use z instead of t?', 'When σ is truly known, or n is large (df above ~100 the difference is negligible).'),
        ('What are degrees of freedom intuitively?', 'The number of independent pieces of information left after estimating parameters; computing the mean uses one, so n − 1 remain for the variance.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you check whether data is normally distributed? Explain Q-Q plots and the Shapiro-Wilk test.', 'Testing Normality', minutes=8, cards=[
    definition(
        defbox('Visual checks come first: a <strong>histogram</strong> and a <strong>Q-Q plot</strong>, which plots sample quantiles against theoretical normal '
               'quantiles; normal data falls on a straight line, an S-shape means heavy or light tails, a curve means skew. '
               '<code>stats.probplot</code> computes the points and the correlation of the line.',
               'Formal tests: <strong>Shapiro-Wilk</strong> (<code>stats.shapiro</code>, powerful for small and medium n), <strong>D\'Agostino-Pearson</strong> '
               '(<code>stats.normaltest</code>, based on skew and kurtosis), Anderson-Darling, Kolmogorov-Smirnov. H₀ = "the data is normal"; a small '
               'p-value rejects normality. With large samples, tests reject even trivial deviations; with small samples, they miss real ones — so combine '
               'tests with plots and the question "does the deviation matter for my method?".'),
        tags('Q-Q plot', 'probplot', 'Shapiro-Wilk', 'normaltest', 'Anderson-Darling', 'normality assumption'),
    ),
    analogy('A Q-Q plot is a <strong>height chart against the "ideal" class</strong>: line up your students and an imaginary perfectly normal class by rank. '
            'If each of your students is about as tall as the matching ideal student, the points form a straight line.'),
    qq_anim(),
    real_world(
        scenario('Choosing between a t-test and a non-parametric test',
                 p('Before comparing packages between two centres, the analyst checks normality: packages are strongly skewed (Shapiro p ≈ 0), so she compares '
                   'log-packages with a t-test or uses the Mann-Whitney test instead.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            sal = df['salary_lpa'].dropna()
            cols = {'final_score': df['final_score'], 'study_hours': df['study_hours'], 'salary_lpa': sal, 'log salary': np.log(sal)}
            print('column        skew  Q-Q r   Shapiro p   normaltest p')
            for name, x in cols.items():
                (_, _), (slope, inter, r) = stats.probplot(x, dist='norm')
                print(f'{name:12} {x.skew():5.2f}  {r:.4f}  {stats.shapiro(x).pvalue:10.4f}  {stats.normaltest(x).pvalue:12.4f}')

            # sample size changes what the tests can see
            rng = np.random.default_rng(4)
            for n in [20, 200, 5000]:            # t(10): nearly normal, slightly heavy tails
                rejected = np.mean([stats.shapiro(rng.standard_t(10, size=n)).pvalue < 0.05 for _ in range(300)])
                print(f'n = {n:5}: Shapiro rejects normality in {rejected:.0%} of 300 samples')

            (osm, osr), _ = stats.probplot(sal, dist='norm')
            print('Q-Q points (theoretical, sample) at the top end:', [(round(float(a), 2), float(b)) for a, b in zip(osm[-3:], osr[-3:])])
        """, setup=STUDENTS, title=S),
        title='Example: Q-Q Correlation, Shapiro-Wilk and normaltest on Four Columns'),
    steps(
        ('Plot', 'Histogram and Q-Q plot (stats.probplot / statsmodels qqplot).'),
        ('Read the pattern', 'Straight = normal; curve = skew; S = tail problems.'),
        ('Test if needed', 'stats.shapiro (n up to a few thousand) or stats.normaltest.'),
        ('Judge practical impact', 'Large n: t-tests are robust to mild non-normality (CLT).'),
        ('Act', 'Transform (log), use non-parametric tests, or bootstrap.'),
        title='Steps to Check Normality'),
    crossq(
        ('The final score has Shapiro p &lt; 0.05 but looks normal. Which do you trust?', 'With 600 rows the test detects tiny deviations (light tails here). For a t-test on means of this size the deviation is irrelevant; the plot and the purpose decide.'),
        ('Does a t-test need the raw data to be normal?', 'It needs the sampling distribution of the mean to be about normal; with moderate n and no extreme skew, the CLT provides this.'),
        ('Why can\'t a normality test prove normality?', 'A large p-value only means no evidence against normality, which is common with small samples simply because the test has little power.'),
    ),
]),
])
