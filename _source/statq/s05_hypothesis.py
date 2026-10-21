from build import *
from statq.anims import *
from statq.runner import strun, pyshow
from statq.data import STUDENTS, data_note

S = 'Python (SciPy · statsmodels) · uses sample data'
P = 'Python (SciPy · statsmodels)'

SECTION = dict(level='advanced', title='Hypothesis Testing', questions=[

# ------------------------------------------------------------------ 21
Q('Explain hypothesis testing: null and alternative hypotheses, test statistic, p-value and significance level.', 'Hypothesis Testing & p-values', minutes=10, cards=[
    definition(
        defbox('A hypothesis test asks whether the data is surprising if a default claim is true. The <strong>null hypothesis H₀</strong> is the "no effect / no '
               'difference" claim (mean score = 60); the <strong>alternative H₁</strong> is what you want evidence for (mean ≠ 60). A <strong>test '
               'statistic</strong> measures how far the data is from H₀ in standard-error units, e.g. t = (x̄ − μ₀) / (s/√n).',
               'The <strong>p-value</strong> is the probability, <em>assuming H₀ is true</em>, of getting a result at least as extreme as the one observed. If p ≤ '
               'the <strong>significance level α</strong> (chosen beforehand, usually 0.05), reject H₀; otherwise "fail to reject" (not "accept"). The p-value is '
               '<strong>not</strong> the probability that H₀ is true, and a small p-value says nothing about the size or importance of the effect.'),
        tags('null hypothesis', 'alternative hypothesis', 'test statistic', 'p-value', 'significance level α', 'one-sample t-test'),
    ),
    analogy('A court trial: the defendant is presumed innocent (<strong>H₀</strong>). The prosecution must show evidence that would be very unlikely if he were '
            'innocent (<strong>small p-value</strong>). "Not guilty" means the evidence was insufficient, not that innocence was proven.'),
    pvalue_anim(),
    real_world(
        scenario('Has the batch average changed?',
                 p('Last year\'s final-exam average was 60. This year\'s 600 students average 58.72. Is that a real drop or normal year-to-year noise? A one-sample '
                   't-test answers it; the result then goes to the academic committee with the size of the drop and its confidence interval, not just "p &lt; 0.05".')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            s = df['final_score']
            mu0 = 60
            t = (s.mean() - mu0) / (s.std() / np.sqrt(len(s)))
            p = 2 * stats.t.sf(abs(t), len(s) - 1)
            print(f'mean {s.mean():.2f}, SE {stats.sem(s):.3f} -> t = {t:.3f}, two-sided p = {p:.5f}')
            res = stats.ttest_1samp(s, mu0)
            print(f'scipy: t = {res.statistic:.3f}, p = {res.pvalue:.5f}, 95 % CI {np.round(res.confidence_interval(), 2)}')
            print('decision at alpha = 0.05:', 'reject H0' if res.pvalue < 0.05 else 'fail to reject H0')

            # what the p-value means: simulate many batches where H0 is TRUE (mean really 60)
            rng = np.random.default_rng(1)
            sims = rng.normal(mu0, s.std(), size=(20_000, len(s)))
            t_null = (sims.mean(1) - mu0) / (sims.std(1, ddof=1) / np.sqrt(len(s)))
            print(f'share of null batches with |t| >= {abs(t):.2f}: {(np.abs(t_null) >= abs(t)).mean():.5f}')

            small = s.sample(25, random_state=3)
            print(f'same question with only 25 students: mean {small.mean():.2f}, p = {stats.ttest_1samp(small, mu0).pvalue:.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: One-Sample t-test by Hand, with SciPy, and by Simulation'),
    steps(
        ('State H₀ and H₁', 'Before looking at the data; decide one- or two-sided.'),
        ('Choose α', 'Usually 0.05; stricter when false alarms are costly.'),
        ('Pick the test and check assumptions', 'Data type, independence, normality of means.'),
        ('Compute statistic and p-value', 'scipy.stats test functions.'),
        ('Decide and report', 'Effect size, CI and p-value, in plain language.'),
        title='Steps of a Hypothesis Test'),
    crossq(
        ('p = 0.003. Is there a 0.3 % chance that H₀ is true?', 'No. It is the chance of data this extreme if H₀ were true. The probability that H₀ is true needs a prior (Bayes).'),
        ('Why "fail to reject" instead of "accept" H₀?', 'A non-significant result can come from a small sample (low power). With 25 students the same drop is not significant, yet the drop is still there.'),
        ('Why is α fixed in advance?', 'Choosing it after seeing p (or trying several tests until one works) inflates false positives: p-hacking.'),
        ('Is p = 0.049 very different from p = 0.051?', 'No. The 0.05 line is a convention; report the exact p-value and the effect size rather than a yes/no verdict.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What are Type I and Type II errors? What is statistical power and how do you choose a sample size?', 'Errors, Power & Sample Size', minutes=9, cards=[
    definition(
        defbox('<strong>Type I error</strong> (false positive): rejecting a true H₀; its probability is α. <strong>Type II error</strong> (false negative): '
               'failing to reject a false H₀; its probability is β. <strong>Power</strong> = 1 − β = the probability of detecting an effect that really exists.',
               'Power grows with a larger <strong>sample size</strong>, a larger <strong>effect size</strong> (difference ÷ SD, Cohen\'s d), a larger α, and lower '
               'noise. Before a study, a <strong>power analysis</strong> fixes three of (α, power, effect size, n) and solves for the fourth; the usual target is '
               '80 % power at α = 0.05. statsmodels: <code>TTestIndPower().solve_power</code>, <code>NormalIndPower</code> for proportions.'),
        tags('Type I error', 'Type II error', 'α', 'β', 'power', 'effect size', 'sample size', 'Cohen\'s d'),
    ),
    analogy('A fire alarm: a <strong>Type I error</strong> rings with no fire (annoying), a <strong>Type II error</strong> stays silent during a fire (dangerous). '
            'Making the alarm less sensitive reduces false alarms but increases missed fires; only a better detector (more data) reduces both.'),
    power_anim(),
    real_world(
        scenario('Planning the flipped-classroom trial',
                 p('The academic team expects the flipped classroom to raise post-test scores by about 3 marks (SD about 12). A power analysis before the trial shows '
                   'how many students per group are needed for an 80 % chance of detecting that effect, so they do not run an under-powered trial that "finds '
                   'nothing" by design.')),
    ),
    example(
        strun("""
            from scipy import stats
            from statsmodels.stats.power import TTestIndPower
            rng = np.random.default_rng(0)

            # Type I error rate: H0 true (both groups mean 60)
            a = rng.normal(60, 12, size=(10_000, 50)); b = rng.normal(60, 12, size=(10_000, 50))
            p = stats.ttest_ind(a, b, axis=1).pvalue
            print(f'H0 true, alpha 0.05: false-positive rate {(p < 0.05).mean():.3f}')

            # Power: true difference of 3 marks (d = 0.25)
            for n in [50, 150, 250, 400]:
                a = rng.normal(60, 12, size=(5_000, n)); b = rng.normal(63, 12, size=(5_000, n))
                sim = (stats.ttest_ind(a, b, axis=1).pvalue < 0.05).mean()
                theory = TTestIndPower().power(effect_size=3 / 12, nobs1=n, alpha=0.05)
                print(f'n = {n:3} per group: power simulated {sim:.3f}  theory {theory:.3f}')

            n_needed = TTestIndPower().solve_power(effect_size=0.25, power=0.8, alpha=0.05)
            print(f'n per group for 80 % power at d = 0.25: {np.ceil(n_needed):.0f}')
            for d, size in [(0.2, 'small'), (0.5, 'medium'), (0.8, 'large')]:
                print(f'd = {d} ({size}): n per group = {np.ceil(TTestIndPower().solve_power(effect_size=d, power=0.8, alpha=0.05)):.0f}')
            print(f'stricter alpha 0.01 at d = 0.25: n = {np.ceil(TTestIndPower().solve_power(effect_size=0.25, power=0.8, alpha=0.01)):.0f}')
        """, title=P),
        title='Example: Simulated False-Positive Rate and Power, Sample Size from statsmodels'),
    steps(
        ('Decide the smallest effect worth detecting', 'In real units (3 marks), then as d = difference / SD.'),
        ('Choose α and power', 'Typically 0.05 and 0.80 (0.90 for important decisions).'),
        ('Solve for n', 'TTestIndPower().solve_power(effect_size, power, alpha).'),
        ('Adjust for reality', 'Add a margin for dropouts and missing data.'),
        ('Report it', 'State the planned power so a null result can be interpreted.'),
        title='Steps for a Power Analysis'),
    crossq(
        ('Which error is worse?', 'It depends on the cost: wrongly launching an ineffective course (Type I) vs missing a useful one (Type II). Set α and power to match those costs.'),
        ('Why is power analysis done before the study, not after?', '"Observed power" computed from the result is just a re-expression of the p-value; it adds nothing.'),
        ('How does lowering α to 0.01 affect power?', 'Power falls at a fixed n; in the example the required sample rises from 253 to 376 per group.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How does an independent two-sample t-test work? What is Welch\'s t-test and Cohen\'s d?', 'Two-Sample t-test', minutes=9, cards=[
    definition(
        defbox('The <strong>independent two-sample t-test</strong> compares the means of two separate groups: t = (x̄₁ − x̄₂) / SE(difference). Assumptions: '
               'independent observations, roughly normal sample means (fine for moderate n), and for <strong>Student\'s</strong> version equal variances.',
               '<strong>Welch\'s t-test</strong> (<code>equal_var=False</code>) does not assume equal variances and adjusts the degrees of freedom; it loses almost '
               'nothing when variances are equal, so it is the safer default. Report the difference with a confidence interval and an <strong>effect size</strong> '
               'such as <strong>Cohen\'s d</strong> = difference ÷ pooled SD (0.2 small, 0.5 medium, 0.8 large).'),
        tags('ttest_ind', 'Welch', 'equal_var', 'Levene test', 'Cohen\'s d', 'difference in means'),
    ),
    analogy('Comparing two classes by their averages is like comparing two archers by where their arrows centre: the further apart the centres and the tighter '
            'each group of arrows, the more convincing the difference.'),
    ttest_anim(),
    real_world(
        scenario('Did the flipped classroom help?',
                 p('Students were randomly assigned to a traditional or flipped classroom for one module. Comparing their post-test scores with Welch\'s t-test, and '
                   'reporting the mean difference, its 95 % CI and Cohen\'s d, tells the academic committee both whether the method worked and by how much.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            g = df.groupby('method')['post_test']
            print(g.agg(['size', 'mean', 'std']).round(2))
            flipped, trad = df.loc[df.method == 'flipped', 'post_test'], df.loc[df.method == 'traditional', 'post_test']

            print(f'Levene test for equal variances: p = {stats.levene(flipped, trad).pvalue:.3f}')
            st = stats.ttest_ind(flipped, trad)                       # Student
            we = stats.ttest_ind(flipped, trad, equal_var=False)      # Welch
            print(f'Student t = {st.statistic:.3f}, p = {st.pvalue:.4f} | Welch t = {we.statistic:.3f}, p = {we.pvalue:.4f}, df = {we.df:.1f}')
            print('95 % CI of the difference (Welch):', np.round(we.confidence_interval(), 2))

            sp = np.sqrt(((len(flipped) - 1) * flipped.var() + (len(trad) - 1) * trad.var()) / (len(flipped) + len(trad) - 2))
            print(f'difference {flipped.mean() - trad.mean():.2f} marks, Cohen d = {(flipped.mean() - trad.mean()) / sp:.3f}')

            # final score is affected by many other things: the same method effect is diluted
            r = stats.ttest_ind(df.loc[df.method == 'flipped', 'final_score'], df.loc[df.method == 'traditional', 'final_score'], equal_var=False)
            print(f'final score by method: Welch p = {r.pvalue:.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: Flipped vs Traditional Classroom with Student and Welch t-tests'),
    steps(
        ('Check the design', 'Two independent groups (ideally randomised); one numeric outcome.'),
        ('Look at the data', 'Group sizes, means, SDs, box plots.'),
        ('Run Welch\'s t-test', 'stats.ttest_ind(a, b, equal_var=False).'),
        ('Quantify the effect', 'Difference with 95 % CI; Cohen\'s d.'),
        ('Interpret', 'Statistical and practical significance; consider confounders if not randomised.'),
        title='Steps for a Two-Sample t-test'),
    crossq(
        ('Why default to Welch?', 'Student\'s test can be badly wrong when variances and group sizes differ; Welch is nearly as powerful when they are equal.'),
        ('The method changes post-test scores significantly but not final scores. Why?', 'Final scores depend on attendance, study hours and noise too; the same small effect is diluted, so the test has much less power on that outcome.'),
        ('What if the groups were not randomised?', 'A difference could come from who chose each method (motivated students choosing flipped). Randomisation or adjustment (regression) is needed for a causal claim.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('When do you use a paired t-test? Why is it more powerful than an independent test for before/after data?', 'Paired t-test', minutes=8, cards=[
    definition(
        defbox('A <strong>paired t-test</strong> compares two measurements on the <strong>same units</strong>: before/after, left/right, two raters on the same '
               'scripts. It computes each unit\'s difference dᵢ and runs a one-sample t-test on the differences: t = d̄ / (s_d/√n). '
               '<code>stats.ttest_rel(after, before)</code>.',
               'Because each student is compared with themselves, stable differences between students (some are always strong) cancel out, so the SD of the '
               'differences is much smaller than the SD of the scores and the test is far more powerful. Treating paired data as two independent samples is '
               'a classic mistake; it wastes this information (and violates independence).'),
        tags('ttest_rel', 'paired samples', 'before/after', 'differences', 'repeated measures'),
    ),
    analogy('To test whether new running shoes are faster, time the <strong>same runners</strong> in old and new shoes. Comparing a group of runners in old shoes '
            'with a different group in new shoes mixes the shoe effect with who happens to be fast.'),
    paired_anim(),
    real_world(
        scenario('Did the module improve skills?',
                 p('Every student takes a pre-test and a post-test. The paired test on the 600 differences shows a clear gain; the confidence interval of the mean '
                   'gain is what goes in the module review.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            pre, post = df['pre_test'], df['post_test']
            d = post - pre
            print(f'pre mean {pre.mean():.2f} (SD {pre.std():.2f}) | post mean {post.mean():.2f} (SD {post.std():.2f})')
            print(f'differences: mean {d.mean():.2f}, SD {d.std():.2f}, correlation pre/post {np.corrcoef(pre, post)[0, 1]:.3f}')

            pr = stats.ttest_rel(post, pre)
            print(f'paired: t = {pr.statistic:.2f}, p = {pr.pvalue:.2e}, 95 % CI of mean gain {np.round(pr.confidence_interval(), 2)}')
            print(f'same as one-sample t on differences: t = {stats.ttest_1samp(d, 0).statistic:.2f}')
            ind = stats.ttest_ind(post, pre)
            print(f'WRONG independent test: t = {ind.statistic:.2f}  (SE {np.sqrt(pre.var() / 600 + post.var() / 600):.3f} vs paired SE {d.std() / np.sqrt(600):.3f})')

            # the power gain shows most clearly with a small sample
            sub = df.sample(20, random_state=5)
            print(f'n = 20: paired p = {stats.ttest_rel(sub.post_test, sub.pre_test).pvalue:.1e}   independent p = {stats.ttest_ind(sub.post_test, sub.pre_test).pvalue:.4f}')
        """, setup=STUDENTS, title=S),
        title='Example: Pre/Post Scores — Paired vs (Wrong) Independent Test'),
    steps(
        ('Confirm pairing', 'Each "after" value belongs to one "before" value (same student).'),
        ('Compute differences', 'd = after − before; inspect their distribution.'),
        ('Run ttest_rel', 'Or ttest_1samp on d; Wilcoxon signed-rank if d is very non-normal.'),
        ('Report the mean change', 'With its CI and the SD of differences.'),
        ('Watch for alternative explanations', 'Practice effects, regression to the mean; a control group helps.'),
        title='Steps for a Paired t-test'),
    crossq(
        ('Why is the paired SE so much smaller here?', 'Pre and post scores are strongly correlated (r = 0.81), so Var(post − pre) = Var(post) + Var(pre) − 2Cov is small.'),
        ('Does a significant pre/post gain prove the module caused it?', 'Not alone: students might improve anyway (practice, maturity). A randomised comparison group isolates the module\'s effect.'),
        ('What if some students missed the post-test?', 'Only complete pairs can be used; check whether the dropouts differ (e.g. weaker students), which would bias the gain upwards.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('One-tailed vs two-tailed tests: when are they appropriate? How do you test a proportion with a z-test?', 'One- vs Two-Tailed & Proportion Tests', minutes=8, cards=[
    definition(
        defbox('A <strong>two-tailed</strong> test (H₁: μ ≠ μ₀) looks for a difference in either direction and splits α between both tails. A '
               '<strong>one-tailed</strong> test (H₁: μ &gt; μ₀ or μ &lt; μ₀) puts all of α in one tail, so it detects effects in that direction more easily '
               'but can never detect the opposite. It is justified only when the direction is fixed <em>before</em> seeing the data and an effect the other way '
               'would lead to the same action as no effect.',
               'For proportions with large samples, the <strong>z-test</strong> uses z = (p̂ − p₀) / √(p₀(1 − p₀)/n). statsmodels: '
               '<code>proportions_ztest(count, nobs, value, alternative=...)</code> for one or two proportions; <code>binomtest</code> (SciPy) for the exact '
               'one-sample version with small samples.'),
        tags('two-tailed', 'one-tailed', 'alternative=', 'proportions_ztest', 'binomtest', 'z-test'),
    ),
    analogy('A two-tailed test is a <strong>goalkeeper guarding both posts</strong>; a one-tailed test moves to cover one post better and leaves the other one open. '
            'You only do that if you know the shot can only come from one side.'),
    tails_anim(),
    real_world(
        scenario('Meeting the placement target',
                 p('The centre committed to a placement rate of at least 40 %. The question "are we below target?" is one-sided by design. A two-proportion test also '
                   'checks whether Kharghar\'s rate differs from the other centres before any centre is singled out.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            from statsmodels.stats.proportion import proportions_ztest
            k, n = df['placed'].sum(), len(df)
            print(f'placed {k} of {n} = {k / n:.3f}; target 0.40')
            for alt in ['two-sided', 'smaller']:
                z, p = proportions_ztest(k, n, value=0.40, alternative=alt, prop_var=0.40)
                print(f'{alt:9}: z = {z:.3f}, p = {p:.4f}')
            print(f'exact binomial test (smaller): p = {stats.binomtest(k, n, 0.40, alternative="less").pvalue:.4f}')

            # one-tailed on the WRONG side never detects anything
            z, p = proportions_ztest(k, n, value=0.40, alternative='larger', prop_var=0.40)
            print(f'larger   : p = {p:.4f}')

            kh = df['centre'] == 'Kharghar'
            counts = [df.loc[kh, 'placed'].sum(), df.loc[~kh, 'placed'].sum()]
            nobs = [kh.sum(), (~kh).sum()]
            z, p = proportions_ztest(counts, nobs)
            print(f'Kharghar {counts[0] / nobs[0]:.3f} vs others {counts[1] / nobs[1]:.3f}: z = {z:.3f}, p = {p:.4f}')

            res = stats.ttest_1samp(df['final_score'], 60, alternative='less')
            print(f'mean score below 60? one-sided p = {res.pvalue:.5f} (two-sided was {stats.ttest_1samp(df["final_score"], 60).pvalue:.5f})')
        """, setup=STUDENTS, title=S),
        title='Example: Placement Rate vs a 40 % Target, Kharghar vs Others'),
    steps(
        ('Decide the direction before the data', 'Write H₁ with ≠, < or >.'),
        ('Check the decision rule', 'Would an effect in the other direction change what you do? If yes, use two-sided.'),
        ('Choose the test', 'z-test for large-sample proportions, binomtest for small n, t-test for means.'),
        ('Pass alternative=', '"two-sided", "smaller"/"less" or "larger"/"greater".'),
        ('Report', 'Proportions, difference, CI and the p-value with its direction.'),
        title='Steps for Directional and Proportion Tests'),
    crossq(
        ('Why is the one-sided p-value half the two-sided one?', 'All of α sits in one tail, so only the area in that tail is counted (when the effect is in the predicted direction).'),
        ('Can you switch to a one-tailed test after seeing that p = 0.08 two-sided?', 'No. Choosing the tail after looking doubles the real false-positive rate; that is p-hacking.'),
        ('Why does Kharghar\'s higher rate deserve caution even though p is small?', 'It was one of several centres that could have stood out; comparing many groups calls for a correction or a pre-specified hypothesis (see multiple testing).'),
    ),
]),
])
