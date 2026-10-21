from build import *
from statq.anims import *
from statq.runner import strun, pyshow
from statq.data import STUDENTS, data_note

S = 'Python (SciPy · statsmodels) · uses sample data'
P = 'Python (SciPy · statsmodels)'

SECTION = dict(level='expert', title='Scenario-Based Questions', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: design and analyse an A/B test — do SMS reminders increase assignment submission?', 'A/B Test End to End', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('An A/B test is a randomised experiment: units are <strong>randomly assigned</strong> to control (A) or treatment (B), one <strong>primary '
               'metric</strong> is defined in advance, and the <strong>sample size</strong> is fixed by a power analysis for the smallest lift worth detecting. '
               'Randomisation makes the groups comparable, so a difference in outcome can be attributed to the treatment.',
               'Analysis of a rate: two-proportion z-test (or chi-square), the absolute and relative <strong>lift</strong> with a confidence interval, and checks: '
               '<strong>sample ratio mismatch</strong> (did the split come out as planned?), no peeking/early stopping, and novelty effects. The decision uses the '
               'CI against the minimum worthwhile lift, not just p &lt; 0.05.'),
        tags('A/B test', 'randomisation', 'primary metric', 'power analysis', 'two-proportion z-test', 'lift', 'sample ratio mismatch'),
    ),
    analogy('An A/B test is a <strong>fair coin toss deciding who gets the new medicine</strong>: because chance alone decides, any systematic difference between '
            'the groups afterwards must come from the medicine.'),
    ab_anim(),
    real_world(
        scenario('Assignment reminders',
                 p('About 70 % of students submit lab assignments on time. The coordinator wants to know whether an automated SMS reminder the evening before the '
                   'deadline raises that to at least 75 %. Students are randomly split; after the required sample is collected, the submission rates are compared '
                   'once, with a confidence interval for the lift.')),
    ),
    example(
        strun("""
            from scipy import stats
            from statsmodels.stats.power import NormalIndPower
            from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest, confint_proportions_2indep

            # 1. sample size for 70 % -> 75 % with 80 % power
            es = proportion_effectsize(0.75, 0.70)
            n = int(np.ceil(NormalIndPower().solve_power(effect_size=es, power=0.8, alpha=0.05)))
            print(f"effect size h = {es:.4f} -> {n} assignment submissions per group")

            # 2. run the experiment (simulated: the reminder really adds 6 points)
            rng = np.random.default_rng(21)
            group = rng.permutation(np.repeat(['A', 'B'], n))
            submitted = np.where(group == 'A', rng.random(2 * n) < 0.70, rng.random(2 * n) < 0.76)
            res = pd.DataFrame({'group': group, 'submitted': submitted})
            print(res.groupby('group')['submitted'].agg(['size', 'sum', 'mean']).round(4))

            # 3. sanity check: sample ratio mismatch
            print(f"sample ratio check: p = {stats.binomtest((group == 'A').sum(), 2 * n, 0.5).pvalue:.3f}")

            # 4. test and estimate
            cnt = res.groupby('group')['submitted'].sum()[['B', 'A']].to_numpy()
            nob = res.groupby('group')['submitted'].size()[['B', 'A']].to_numpy()
            z, p = proportions_ztest(cnt, nob)
            lo, hi = confint_proportions_2indep(cnt[0], nob[0], cnt[1], nob[1])
            lift = cnt[0] / nob[0] - cnt[1] / nob[1]
            print(f'lift {lift:+.4f} ({lift / (cnt[1] / nob[1]):+.1%} relative), 95 % CI [{lo:+.4f}, {hi:+.4f}], z = {z:.2f}, p = {p:.1e}')
            print('decision:', 'ship the reminder' if lo > 0 else 'no clear benefit yet')
        """, title=P),
        title='Example: Power Analysis, Randomisation, SRM Check, z-test and Lift CI'),
    steps(
        ('Define metric and minimum lift', 'On-time submission rate; +5 points is worth it.'),
        ('Compute the sample size', 'NormalIndPower with proportion_effectsize.'),
        ('Randomise and run to the planned size', 'No peeking and stopping early.'),
        ('Check data quality', 'Sample ratio mismatch, logging gaps, novelty effects.'),
        ('Test, estimate, decide', 'z-test, lift with CI, compare with the minimum worthwhile lift.'),
        title='Steps for an A/B Test'),
    crossq(
        ('Why randomise rather than compare students who opted in to SMS?', 'Opt-in students are probably more organised already; the difference would mix their habits with the reminder\'s effect.'),
        ('The CI is [+0.2 %, +8 %]. Ship it?', 'It is positive, but the lower end is far below the 5-point target. If reminders are cheap, yes; if costly, run a larger test to narrow the CI.'),
        ('What is a sample ratio mismatch and why does it matter?', 'A split that deviates from the planned 50/50 more than chance allows signals a bug in assignment or logging, which can bias the result.'),
        ('Why not stop as soon as p &lt; 0.05?', 'Repeatedly checking inflates the false-positive rate far above 5 %; use the planned sample size or a sequential design.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: one centre looks worse overall but better in every course. Explain Simpson\'s paradox.', 'Simpson\'s Paradox', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('<strong>Simpson\'s paradox</strong>: a trend that appears in every subgroup reverses (or disappears) when the groups are combined. It happens when '
               'a third variable (here, course mix) is associated with both the grouping and the outcome, and the groups have very different compositions.',
               'The aggregated comparison answers "which centre has more placed students overall?"; the stratified comparison answers "for a student in a given '
               'course, which centre does better?". Which one is right depends on the causal question. A fair overall comparison <strong>standardises</strong> '
               'rates to a common mix (direct standardisation) or uses a regression with the confounder.'),
        tags('Simpson\'s paradox', 'confounding', 'stratification', 'aggregation', 'standardised rate', 'weighted average'),
    ),
    analogy('A hospital that takes the most severe cases can have a higher overall death rate yet treat <strong>every type of patient</strong> better than a '
            'hospital that only sees mild cases. The overall number reflects <strong>who walks in</strong>, not only how well they are treated.'),
    simpson_anim(),
    real_world(
        scenario('Ranking centres by placement rate',
                 p('Centre North admits mostly PG-DAC students, whose placement market was tougher this year; Centre South admits mostly PG-DBDA students. A '
                   'league table of overall placement rates would penalise North for its course mix, even though it places a higher share in each course.')),
    ),
    example(
        strun("""
            import statsmodels.formula.api as smf
            counts = pd.DataFrame({
                'centre': ['North', 'North', 'South', 'South'],
                'course': ['PG-DBDA', 'PG-DAC', 'PG-DBDA', 'PG-DAC'],
                'students': [50, 250, 250, 50],
                'placed':   [45, 100, 200, 15]})
            counts['rate'] = (counts['placed'] / counts['students']).round(3)
            print(counts)

            overall = counts.groupby('centre')[['placed', 'students']].sum()
            print('overall rate:', (overall['placed'] / overall['students']).round(3).to_dict())
            print('by course   :', counts.pivot(index='course', columns='centre', values='rate').to_dict())

            # direct standardisation: apply each centre's course rates to the SAME course mix (total of both centres)
            mix = counts.groupby('course')['students'].sum() / counts['students'].sum()
            std = counts.pivot(index='course', columns='centre', values='rate').mul(mix, axis=0).sum()
            print('standardised to a common mix:', std.round(3).to_dict())

            # logistic regression on individual rows: centre effect with and without course
            rows = counts.loc[counts.index.repeat(counts['students'])].copy()
            rows['y'] = np.concatenate([[1] * p + [0] * (n - p) for p, n in zip(counts['placed'], counts['students'])])
            for f in ['y ~ C(centre)', 'y ~ C(centre) + C(course)']:
                m = smf.logit(f, rows).fit(disp=0)
                print(f'{f:28} odds ratio South vs North = {np.exp(m.params["C(centre)[T.South]"]):.3f}')
        """, title=P),
        title='Example: Overall vs Per-Course Rates, Standardisation, Logistic Regression'),
    steps(
        ('Compare overall rates', 'groupby on the grouping variable alone.'),
        ('Stratify by plausible confounders', 'Course, batch, background.'),
        ('Compare the group compositions', 'Very different mixes signal a possible paradox.'),
        ('Adjust', 'Standardised rates or regression including the confounder.'),
        ('Answer the right question', 'Decide whether the overall or the within-stratum comparison matches the decision.'),
        title='Steps to Detect Simpson\'s Paradox'),
    crossq(
        ('Which number should a student choosing a centre look at?', 'The per-course rate for their own course: North is better for both PG-DBDA and PG-DAC students.'),
        ('Is the overall rate "wrong"?', 'No, it is a correct description of each centre\'s total outcome; it just answers a different question and should not be read as centre quality.'),
        ('Can adding a control variable always fix Simpson\'s paradox?', 'Only if it is a confounder. Adjusting for a variable on the causal path (a mediator) can create misleading results.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: how many students must you survey to estimate satisfaction within ±5 percentage points?', 'Survey Sample Size', minutes=8, tag='Scenario', cards=[
    definition(
        defbox('For a proportion, the <strong>margin of error</strong> at 95 % confidence is E = 1.96·√(p(1 − p)/n), so the required sample is n = 1.96²·p(1 − p)/E². '
               'If p is unknown, use p = 0.5, the worst case (largest variance): n = 385 for ±5 %, about 1,068 for ±3 %.',
               'For a <strong>finite population</strong> N, apply the correction n_adj = n / (1 + (n − 1)/N): surveying 300 batch-mates needs far fewer than 385 '
               'responses. Then inflate for the expected <strong>response rate</strong>. With stratified sampling, allocate proportionally (or more to small '
               'strata that must be reported separately). Precision needs are per subgroup: ±5 % for each centre needs that n in each centre.'),
        tags('margin of error', 'sample size', 'worst case p = 0.5', 'finite population correction', 'response rate', 'allocation'),
    ),
    analogy('Like deciding how many spoonfuls to taste: the required number depends on how sure you want to be and how precise, <strong>not on the size of the '
            'pot</strong>, unless the pot is small enough that you are tasting a large part of it.'),
    survey_anim(),
    real_world(
        scenario('End-of-module feedback across three centres',
                 p('The quality team wants overall satisfaction within ±5 points and also a separate figure per centre. Response rates average 60 %, so they must '
                   'invite more students than the formula says, and the per-centre requirement dominates the total.')),
    ),
    example(
        strun("""
            from scipy import stats
            z = stats.norm.ppf(0.975)
            def n_needed(E, p=0.5, N=None):
                n0 = z ** 2 * p * (1 - p) / E ** 2
                return int(np.ceil(n0 if N is None else n0 / (1 + (n0 - 1) / N)))

            for E in [0.10, 0.05, 0.03, 0.01]:
                print(f'margin ±{E:.0%}: n = {n_needed(E):5}  (if p is about 0.8: {n_needed(E, 0.8):5})')

            for N in [300, 600, 5000, 1_000_000]:
                print(f'population {N:>9,}: n = {n_needed(0.05, N=N)}')

            centres = {'Kharghar': 231, 'Juhu': 192, 'Pune': 177}
            per = {c: n_needed(0.05, N=N) for c, N in centres.items()}
            print('±5 % per centre:', per, '-> total', sum(per.values()), '| invitations at 60 % response:',
                  {c: int(np.ceil(v / 0.6)) for c, v in per.items()})

            # check by simulation: with n = 385 from a large population, how often is the estimate within ±5 %?
            rng = np.random.default_rng(3)
            est = rng.binomial(385, 0.5, 100_000) / 385
            print(f'simulated share within ±5 points: {(np.abs(est - 0.5) <= 0.05).mean():.3f}')
        """, title=P),
        title='Example: Margin of Error, Finite Population Correction, Per-Centre Allocation'),
    steps(
        ('Set the precision and confidence', 'E.g. ±5 points at 95 %.'),
        ('Guess p or use 0.5', 'Worst case gives a safe n.'),
        ('Compute n', 'z²·p(1−p)/E², then the finite population correction.'),
        ('Repeat for each subgroup to be reported', 'Subgroup precision usually dominates.'),
        ('Adjust for non-response and check bias', 'Invite n / response rate; compare responders with non-responders.'),
        title='Steps to Size a Survey'),
    crossq(
        ('Why is the sample size almost the same for a city of 1 million and a country of 1 billion?', 'Precision depends on n, not on the population size, unless the sample is a sizeable fraction of the population.'),
        ('Why does p = 0.5 give the largest n?', 'p(1 − p) is maximal at 0.5; for p = 0.8 the variance is 0.16 instead of 0.25.'),
        ('Does a larger sample fix low response rates?', 'It fixes precision, not non-response bias: if dissatisfied students do not reply, the estimate stays too rosy.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: three evaluators marked different batches of project reports. Is one of them harsher, and how do you make marks fair?', 'Fair Marking Across Evaluators', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('If reports are <strong>randomly allocated</strong> to evaluators, the batches should be of similar quality, so systematic differences in average '
               'marks indicate evaluator severity. One-way ANOVA (or Kruskal-Wallis) tests whether evaluator means differ; Tukey HSD identifies which.',
               'Common fixes: <strong>moderation</strong> (a second marker re-marks a sample; compare with a paired test), or <strong>statistical '
               'scaling</strong>: convert each evaluator\'s marks to z-scores and map back to a common mean and SD, which preserves each student\'s rank within '
               'the batch. Scaling assumes the batches really are comparable; if allocation was not random, adjust for prior performance (e.g. regression on '
               'pre-test) instead.'),
        tags('rater bias', 'moderation', 'ANOVA', 'Tukey HSD', 'z-score scaling', 'random allocation', 'inter-rater agreement'),
    ),
    analogy('Three judges scoring a talent show: if one consistently gives two points less than the others for <strong>the same kinds of acts</strong>, '
            'contestants in that judge\'s group are disadvantaged. Rescaling each judge\'s scores puts all contestants on the same ruler.'),
    rater_anim(),
    real_world(
        scenario('Project marks for 120 students',
                 p('Reports were randomly split among three faculty. Evaluator C\'s average is 3–4 marks lower, but with only 40 reports each, ANOVA cannot separate '
                   'severity from chance differences between batches. A moderator re-marks 15 of C\'s reports: the paired comparison shows C marks almost 7 marks '
                   'lower on the same reports, and the committee approves z-score scaling for C\'s batch.')),
    ),
    example(
        strun("""
            from scipy import stats
            rng = np.random.default_rng(12)
            quality = rng.normal(68, 9, 120)                                   # true quality of each report
            evaluator = rng.permutation(np.repeat(['A', 'B', 'C'], 40))        # random allocation
            bias = pd.Series({'A': 0, 'B': 1, 'C': -6})[evaluator].to_numpy()
            marks = np.clip(np.round(quality + bias + rng.normal(0, 3, 120)), 0, 100)
            d = pd.DataFrame({'evaluator': evaluator, 'mark': marks, 'quality': quality})
            print(d.groupby('evaluator')['mark'].agg(['size', 'mean', 'std']).round(2))

            groups = [g['mark'].to_numpy() for _, g in d.groupby('evaluator')]
            print(f'ANOVA p = {stats.f_oneway(*groups).pvalue:.2e}')
            tk = stats.tukey_hsd(*groups)
            print('Tukey p-values (A, B, C):\\n', pd.DataFrame(tk.pvalue, index=list('ABC'), columns=list('ABC')).round(4))

            # moderation: a second marker (unbiased) re-marks 15 of C's reports
            idx = d.index[d.evaluator == 'C'][:15]
            second = np.round(d.loc[idx, 'quality'] + rng.normal(0, 3, 15))
            pr = stats.ttest_rel(d.loc[idx, 'mark'], second)
            print(f'moderation sample: C minus moderator = {(d.loc[idx, "mark"] - second).mean():+.2f}, paired p = {pr.pvalue:.4f}')

            # scaling to the overall mean and SD
            m_all, s_all = d['mark'].mean(), d['mark'].std()
            d['scaled'] = d.groupby('evaluator')['mark'].transform(lambda x: (x - x.mean()) / x.std()) * s_all + m_all
            print(d.groupby('evaluator')[['mark', 'scaled']].mean().round(2))
            print(f'correlation with true quality: raw {np.corrcoef(d.mark, d.quality)[0, 1]:.3f}  scaled {np.corrcoef(d.scaled, d.quality)[0, 1]:.3f}')
        """, title=P),
        title='Example: Detect a Harsh Evaluator, Confirm by Moderation, Rescale'),
    steps(
        ('Allocate scripts randomly', 'Otherwise batch quality and evaluator severity are confounded.'),
        ('Compare evaluator distributions', 'Means, SDs, box plots; ANOVA and Tukey.'),
        ('Moderate a sample', 'Second marking; paired t-test or Wilcoxon on the differences.'),
        ('Scale if justified', 'z-score per evaluator mapped to the common mean/SD.'),
        ('Document and review', 'Report the adjustment and check that rankings within batches are unchanged.'),
        title='Steps for Fair Marking'),
    crossq(
        ('Why does random allocation matter so much?', 'Without it, a lower average could mean weaker reports rather than a harsher evaluator; the test cannot tell the two apart.'),
        ('Why did the ANOVA miss what 15 moderated reports found?', 'ANOVA compares different reports, so the large variation in report quality (SD ≈ 9) hides a 6-mark bias. Moderation compares two markers on the same reports, removing quality differences: a paired design is far more powerful.'),
        ('Does scaling change who is best within C\'s batch?', 'No. z-scaling is a monotonic transformation within a batch, so ranks are preserved; only the level and spread change.'),
        ('What if evaluators differ in spread, not mean?', 'Scaling by SD fixes that too: a lenient-but-flat marker compresses differences between students, which scaling stretches back.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Scenario: weekly attendance dropped this week. Is it a real signal or normal variation? Use a control chart.', 'Control Charts', minutes=8, tag='Scenario', cards=[
    definition(
        defbox('A <strong>control chart</strong> (statistical process control) plots a statistic over time with a centre line and <strong>control limits</strong> '
               'at about ±3 standard errors, computed from a stable baseline period. Points inside the limits are treated as <strong>common-cause</strong> '
               '(normal) variation; a point outside, or a run of points on one side (e.g. 8 in a row below the centre), signals a <strong>special cause</strong> '
               'worth investigating.',
               'For a proportion (share of students attending) use a <strong>p-chart</strong>: limits p̄ ± 3·√(p̄(1 − p̄)/n), which widen when fewer students are '
               'enrolled. Reacting to every dip inside the limits ("tampering") wastes effort and can make the process worse.'),
        tags('control chart', 'p-chart', 'control limits', 'common cause', 'special cause', 'SPC', 'Western Electric rules'),
    ),
    analogy('Your commute takes 30 to 40 minutes on normal days. A 37-minute trip needs no explanation; a <strong>75-minute trip</strong> does. Control limits '
            'formalise "normal days" so that you only investigate the real anomalies.'),
    control_anim(),
    real_world(
        scenario('Attendance monitoring',
                 p('The coordinator tracks the share of enrolled students attending each week. A dip to 80 % after weeks of 82–89 % triggers a panic email, but '
                   'the p-chart shows it is inside the limits. Week 13, at 69 %, is outside: it coincided with a hackathon in another city, a special cause that '
                   'explains it.')),
    ),
    example(
        strun("""
            from scipy import stats
            rng = np.random.default_rng(14)
            enrolled = 180
            p_true = np.r_[np.full(12, 0.85), 0.71, np.full(7, 0.85)]            # week 13 has a special cause
            attended = rng.binomial(enrolled, p_true)
            weeks = pd.DataFrame({'week': np.arange(1, 21), 'attended': attended, 'rate': (attended / enrolled).round(3)})

            base = weeks.iloc[:10]                                                  # baseline period
            p_bar = base['attended'].sum() / (10 * enrolled)
            se = np.sqrt(p_bar * (1 - p_bar) / enrolled)
            lcl, ucl = p_bar - 3 * se, p_bar + 3 * se
            print(f'centre line {p_bar:.3f}, control limits [{lcl:.3f}, {ucl:.3f}]  (2-sigma warning [{p_bar - 2 * se:.3f}, {p_bar + 2 * se:.3f}])')

            weeks['signal'] = np.where(weeks['rate'] < lcl, 'BELOW LCL', np.where(weeks['rate'] > ucl, 'ABOVE UCL', ''))
            print(weeks.to_string(index=False))

            low = weeks.loc[weeks['signal'] == '', 'rate'].min()
            print(f'lowest in-control week: {low:.3f} -> normal variation; investigate only flagged weeks')
            print(f'false-alarm rate per point with 3-sigma limits: {2 * stats.norm.sf(3):.4f}')
        """, title=P),
        title='Example: p-chart for Weekly Attendance with a Baseline and Signals'),
    steps(
        ('Choose the statistic and chart', 'Proportion → p-chart; mean → X̄ chart; counts → c-chart.'),
        ('Compute limits from a stable baseline', 'Centre line ± 3 standard errors.'),
        ('Plot new points as they arrive', 'Keep the limits fixed unless the process changes.'),
        ('Apply signal rules', 'Point outside limits; runs of 8 on one side; trends.'),
        ('Investigate signals only', 'Find the special cause; do not react to noise.'),
        title='Steps to Build a Control Chart'),
    crossq(
        ('Why ±3σ and not ±2σ?', 'With many weekly points, ±2σ would raise a false alarm about once every 20 weeks; ±3σ about once every 370 points.'),
        ('Should the limits be recomputed every week including new data?', 'No; including special-cause points widens the limits and hides problems. Recompute only after a deliberate, verified process change.'),
        ('How is a control chart related to hypothesis testing?', 'Each point is effectively a test of "the process is unchanged"; the chart adds time order and run rules that catch gradual shifts.'),
    ),
]),
])
