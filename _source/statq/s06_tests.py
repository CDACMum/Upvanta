from build import *
from statq.anims import *
from statq.runner import strun, pyshow
from statq.data import STUDENTS, data_note

S = 'Python (SciPy · statsmodels) · uses sample data'
P = 'Python (SciPy · statsmodels)'

SECTION = dict(level='advanced', title='More Statistical Tests', questions=[

# ------------------------------------------------------------------ 26
Q('How do chi-square tests work? Explain goodness of fit and the test of independence.', 'Chi-square Tests', minutes=9, cards=[
    definition(
        defbox('Chi-square tests compare <strong>observed counts</strong> O with <strong>expected counts</strong> E: χ² = Σ (O − E)² / E. Large values mean the '
               'counts are far from what H₀ predicts. <strong>Goodness of fit</strong> (<code>stats.chisquare</code>): does one categorical variable follow a '
               'given distribution (e.g. the planned course mix)? df = categories − 1.',
               '<strong>Test of independence</strong> (<code>stats.chi2_contingency</code>): are two categorical variables related (centre × placed)? Expected '
               'count for a cell = row total × column total ÷ grand total; df = (rows − 1)(cols − 1). Rule of thumb: expected counts ≥ 5 (otherwise Fisher\'s '
               'exact test). Effect size: <strong>Cramér\'s V</strong> (0 = none, 1 = perfect association).'),
        tags('chi-square', 'goodness of fit', 'contingency table', 'chi2_contingency', 'expected counts', 'Cramér\'s V', 'Fisher exact'),
    ),
    analogy('If placement had nothing to do with centre, each centre would get its "fair share" of placements in proportion to its size. The chi-square statistic '
            'adds up <strong>how unfair the actual shares are</strong>, cell by cell.'),
    chi_anim(),
    real_world(
        scenario('Is placement related to centre?',
                 p('Before allocating extra placement-training budget to the Juhu and Pune centres, the coordinator checks whether placement really depends on centre. '
                   'The test of independence on the 3 × 2 table answers that; the residuals show which centre drives the result.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            obs = df['course'].value_counts().reindex(['PG-DBDA', 'PG-DAC', 'PG-DAI'])
            exp = np.array([0.45, 0.35, 0.20]) * len(df)
            gof = stats.chisquare(obs, exp)
            print('course counts', obs.to_dict(), '| expected', exp.round(1))
            print(f'goodness of fit: chi2 = {gof.statistic:.3f}, p = {gof.pvalue:.3f}')

            table = pd.crosstab(df['centre'], df['placed'])
            chi2, p, dof, expected = stats.chi2_contingency(table)
            print(table)
            print('expected if independent:\\n', pd.DataFrame(expected, index=table.index, columns=table.columns).round(1))
            print(f'independence: chi2 = {chi2:.3f}, df = {dof}, p = {p:.4f}')
            print('standardised residuals (O-E)/sqrt(E):\\n', ((table - expected) / np.sqrt(expected)).round(2))
            print(f"Cramér's V = {np.sqrt(chi2 / (table.values.sum() * (min(table.shape) - 1))):.3f}")
            print('method x placed: p =', round(stats.chi2_contingency(pd.crosstab(df['method'], df['placed'])).pvalue, 3))
        """, setup=STUDENTS, title=S),
        title='Example: Course Mix vs Plan, and Centre × Placement'),
    steps(
        ('Build the table of counts', 'value_counts or pd.crosstab (counts, never percentages).'),
        ('Choose the test', 'One variable vs expected shares → chisquare; two variables → chi2_contingency.'),
        ('Check expected counts', 'All ≥ 5; otherwise merge categories or use Fisher\'s exact test.'),
        ('Read the result', 'p-value; then residuals to see which cells differ.'),
        ('Report the strength', 'Cramér\'s V and the percentages per group.'),
        title='Steps for a Chi-square Test'),
    crossq(
        ('Why must you use counts and not percentages?', 'The statistic depends on sample size; percentages hide n and give meaningless χ² values.'),
        ('The test is significant. Which centre is different?', 'Look at the standardised residuals: cells near or beyond ±2 contribute most. Here Kharghar\'s placed cell (+1.92) stands out: more placements than independence predicts.'),
        ('What does chi2_contingency do for 2 × 2 tables by default?', 'It applies Yates\' continuity correction (correction=True), which makes the test slightly more conservative.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What is ANOVA? How do you compare more than two group means and find which groups differ?', 'ANOVA & Post-hoc Tests', minutes=10, cards=[
    definition(
        defbox('<strong>One-way ANOVA</strong> tests H₀: all group means are equal, against "at least one differs". It compares variation <strong>between</strong> '
               'group means with variation <strong>within</strong> groups: F = MS_between / MS_within. A large F means the group means are further apart than '
               'within-group noise would explain. <code>stats.f_oneway(*groups)</code>; statsmodels <code>anova_lm</code> for the full table.',
               'Running many pairwise t-tests instead inflates false positives, so ANOVA comes first and a <strong>post-hoc</strong> test (Tukey HSD: '
               '<code>stats.tukey_hsd</code> or statsmodels <code>pairwise_tukeyhsd</code>) then finds which pairs differ while controlling the family-wise '
               'error rate. Assumptions: independence, roughly normal residuals, similar variances (Welch ANOVA or Kruskal-Wallis otherwise). Effect size: '
               '<strong>η²</strong> = SS_between / SS_total.'),
        tags('ANOVA', 'F statistic', 'f_oneway', 'Tukey HSD', 'post-hoc', 'eta squared', 'between / within variance'),
    ),
    analogy('Three cooks make the same dish. ANOVA asks whether the <strong>differences between cooks</strong> are larger than the <strong>natural variation in '
            'each cook\'s own dishes</strong>. Only if they are does it make sense to ask which cook is different.'),
    anova_anim(),
    real_world(
        scenario('Do centres differ in final scores?',
                 p('The academic head wants to know whether final scores differ across Kharghar, Juhu and Pune. ANOVA gives one overall answer; Tukey\'s test then '
                   'says which pairs differ, and η² says how much of the score variation is explained by centre at all.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            import statsmodels.formula.api as smf
            from statsmodels.stats.anova import anova_lm
            groups = [g['final_score'].to_numpy() for _, g in df.groupby('centre')]
            print(df.groupby('centre')['final_score'].agg(['size', 'mean', 'std']).round(2))
            f = stats.f_oneway(*groups)
            print(f'one-way ANOVA: F = {f.statistic:.3f}, p = {f.pvalue:.4f}')

            # the same decomposition by hand
            grand = df['final_score'].mean()
            ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
            ss_within = sum(((g - g.mean()) ** 2).sum() for g in groups)
            k, n = len(groups), len(df)
            print(f'SS between {ss_between:.1f}, SS within {ss_within:.1f}, F = {(ss_between / (k - 1)) / (ss_within / (n - k)):.3f}, '
                  f'eta^2 = {ss_between / (ss_between + ss_within):.4f}')

            print(anova_lm(smf.ols('final_score ~ C(course)', data=df).fit()).round(4))
            tk = stats.tukey_hsd(*[g['post_test'].to_numpy() for _, g in df.groupby('course')])
            names = sorted(df['course'].unique())
            print('Tukey HSD on post_test by course (p-values):')
            print(pd.DataFrame(tk.pvalue, index=names, columns=names).round(3))
            print(f'Levene (equal variances) by centre: p = {stats.levene(*groups).pvalue:.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: ANOVA by Centre (SciPy and by Hand), ANOVA Table, Tukey HSD'),
    steps(
        ('Check the design', 'One numeric outcome, one categorical factor with 3+ independent groups.'),
        ('Explore', 'Group sizes, means, SDs, box plots.'),
        ('Run ANOVA', 'stats.f_oneway or anova_lm(ols(...)).'),
        ('If significant, run post-hoc tests', 'Tukey HSD for all pairs.'),
        ('Report effect size and assumptions', 'η², Levene test; Welch ANOVA / Kruskal-Wallis if violated.'),
        title='Steps for One-way ANOVA'),
    crossq(
        ('Why not run three t-tests?', 'Three tests at α = 0.05 give about a 14 % chance of at least one false positive; ANOVA plus Tukey keeps the overall rate at 5 %.'),
        ('ANOVA is significant but Tukey finds no significant pair. Possible?', 'Yes, occasionally: the overall test can detect a pattern spread across groups that no single pair shows clearly.'),
        ('What does η² = 0.002 tell you?', 'Centre explains 0.2 % of the variation in final scores: whatever the p-value, it is practically negligible.'),
        ('How is ANOVA related to regression?', 'One-way ANOVA is a linear regression on dummy variables for the groups; anova_lm on an OLS model shows exactly that.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What are non-parametric tests? When would you use Mann-Whitney, Wilcoxon and Kruskal-Wallis?', 'Non-parametric Tests', minutes=8, cards=[
    definition(
        defbox('<strong>Non-parametric</strong> (rank-based) tests make fewer assumptions about the distribution. They replace values by their ranks, so they are '
               'robust to outliers and skew and work for ordinal data. The price: slightly less power when the data really is normal, and they test '
               '"one group tends to have larger values" rather than "means differ".',
               'Equivalents: <strong>Mann-Whitney U</strong> (<code>mannwhitneyu</code>) for two independent groups (vs independent t-test); <strong>Wilcoxon '
               'signed-rank</strong> (<code>wilcoxon</code>) for paired data (vs paired t-test); <strong>Kruskal-Wallis H</strong> (<code>kruskal</code>) for 3+ '
               'groups (vs one-way ANOVA); <strong>Spearman</strong> correlation (vs Pearson).'),
        tags('non-parametric', 'ranks', 'Mann-Whitney U', 'Wilcoxon signed-rank', 'Kruskal-Wallis', 'robust'),
    ),
    analogy('Instead of comparing the <strong>exact finishing times</strong> of two running clubs (one runner with a broken leg could ruin an average), compare their '
            '<strong>finishing positions</strong>. Ranks do not care how far behind the last runner was.'),
    rank_anim(),
    real_world(
        scenario('Comparing packages between centres',
                 p('Packages are skewed with a few very high offers. A t-test on raw packages can be swayed by one 19.8 LPA offer; Mann-Whitney compares the whole '
                   'distributions by rank and is the safer choice, or the t-test can be run on log packages.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            placed = df.dropna(subset=['salary_lpa'])
            kh = placed.loc[placed.centre == 'Kharghar', 'salary_lpa']
            ot = placed.loc[placed.centre != 'Kharghar', 'salary_lpa']
            print(f'median Kharghar {kh.median()} vs others {ot.median()} | mean {kh.mean():.2f} vs {ot.mean():.2f}')
            print(f'Mann-Whitney U p = {stats.mannwhitneyu(kh, ot).pvalue:.4f}   Welch t p = {stats.ttest_ind(kh, ot, equal_var=False).pvalue:.4f}   '
                  f't on log p = {stats.ttest_ind(np.log(kh), np.log(ot), equal_var=False).pvalue:.4f}')

            # one extreme offer in the OTHER group: the t-test changes its verdict, the rank test barely moves
            ot2 = pd.concat([ot, pd.Series([60.0])])
            print(f'one 60 LPA offer added to "others": Mann-Whitney p = {stats.mannwhitneyu(kh, ot2).pvalue:.4f}   '
                  f'Welch t p = {stats.ttest_ind(kh, ot2, equal_var=False).pvalue:.4f}')

            print(f'Wilcoxon signed-rank (post vs pre): p = {stats.wilcoxon(df.post_test, df.pre_test).pvalue:.2e}')
            groups = [g['salary_lpa'].to_numpy() for _, g in placed.groupby('centre')]
            print(f'Kruskal-Wallis packages by centre: p = {stats.kruskal(*groups).pvalue:.4f}   ANOVA p = {stats.f_oneway(*groups).pvalue:.4f}')
            print('ranks of [5, 50, 7, 6]:', stats.rankdata([5, 50, 7, 6]))
        """, setup=STUDENTS, title=S),
        title='Example: Packages by Centre — Rank Tests vs t-test, Effect of One Outlier'),
    steps(
        ('Check the data', 'Strong skew, outliers, ordinal scale or tiny samples → consider rank tests.'),
        ('Pick the matching test', 'Two independent groups, paired data, or 3+ groups.'),
        ('Run it', 'mannwhitneyu, wilcoxon, kruskal (and Dunn post-hoc for Kruskal).'),
        ('Report medians and IQRs', 'They match what the test compares.'),
        ('Consider alternatives', 'A transformation (log) or bootstrap may answer the mean question directly.'),
        title='Steps to Use Non-parametric Tests'),
    crossq(
        ('Does Mann-Whitney test whether medians are equal?', 'Strictly it tests whether a random value from one group tends to exceed one from the other; it equals a median test only when the shapes are the same.'),
        ('Why not always use non-parametric tests?', 'They answer a different question (ranks, not means), give no direct effect estimate in original units, and lose some power for well-behaved data.'),
        ('What about ties in the data?', 'Ties receive the average rank; SciPy corrects the test for them automatically.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('What is the multiple-testing problem? Explain Bonferroni, Holm and false-discovery-rate corrections.', 'Multiple Testing', minutes=8, cards=[
    definition(
        defbox('Each test at α = 0.05 has a 5 % false-positive rate. Running m independent tests on pure noise gives P(at least one false positive) = 1 − 0.95ᵐ '
               '(64 % for 20 tests): the <strong>family-wise error rate (FWER)</strong> explodes. Testing many subgroups, metrics or outcomes and reporting the '
               'significant ones is a form of <strong>p-hacking</strong>.',
               'Corrections: <strong>Bonferroni</strong> (test each at α/m; simple, conservative), <strong>Holm</strong> (step-down, controls FWER, always at '
               'least as powerful as Bonferroni), and <strong>Benjamini-Hochberg</strong> (controls the <strong>false discovery rate</strong>, the expected '
               'share of false positives among discoveries; preferred when screening many hypotheses). statsmodels: <code>multipletests(p, method=...)</code>.'),
        tags('multiple comparisons', 'family-wise error rate', 'Bonferroni', 'Holm', 'Benjamini-Hochberg', 'FDR', 'p-hacking'),
    ),
    analogy('Buy one lottery ticket and winning is a surprise. Buy <strong>twenty tickets</strong> and one small win is expected. Testing twenty hypotheses is '
            'buying twenty tickets: a "significant" result is no longer surprising.'),
    multi_anim(),
    real_world(
        scenario('"Which factors affect placement?"',
                 p('An analyst tests placement against 20 recorded attributes (hostel, bus route, birth month, …) and finds two with p &lt; 0.05. With 20 tests, about '
                   'one false positive is expected anyway; after a Holm or BH correction neither survives, and birth month is quietly dropped from the report.')),
    ),
    example(
        strun("""
            from scipy import stats
            from statsmodels.stats.multitest import multipletests
            rng = np.random.default_rng(5)

            # 1,000 analysts each test 20 noise variables
            hits = 0
            for _ in range(1000):
                p = [stats.ttest_ind(rng.normal(size=60), rng.normal(size=60)).pvalue for _ in range(20)]
                hits += min(p) < 0.05
            print(f'share of analysts finding at least one "significant" noise effect: {hits / 1000:.3f}  (theory {1 - 0.95 ** 20:.3f})')

            # 20 attributes: 17 pure noise + 3 real effects
            effects = [0] * 17 + [0.6, 0.5, 0.45]
            p = np.array([stats.ttest_ind(rng.normal(0, 1, 80), rng.normal(d, 1, 80)).pvalue for d in effects])
            print('raw p < 0.05:', np.where(p < 0.05)[0].tolist(), '(indices 17-19 are the real effects)')
            for m in ['bonferroni', 'holm', 'fdr_bh']:
                reject, p_adj, _, _ = multipletests(p, alpha=0.05, method=m)
                print(f'{m:10} rejects {np.where(reject)[0].tolist()}')
            print('sorted raw p-values:', np.sort(p)[:5].round(4))
        """, title=P),
        title='Example: Simulated p-hacking and Three Corrections'),
    steps(
        ('Count the tests', 'Every subgroup, metric and outcome you looked at, not just the ones reported.'),
        ('Pre-register the main hypothesis', 'One primary test needs no correction.'),
        ('Choose the error rate', 'FWER (Holm) for confirmatory claims; FDR (BH) for screening.'),
        ('Adjust', 'multipletests(pvals, method="holm" / "fdr_bh").'),
        ('Report transparently', 'How many tests were run and which correction was used.'),
        title='Steps to Handle Multiple Tests'),
    crossq(
        ('Why is Bonferroni conservative?', 'It assumes the worst case; with many tests it requires tiny p-values and misses real effects (low power). Holm is uniformly better.'),
        ('FWER vs FDR?', 'FWER: probability of any false positive. FDR: expected proportion of false positives among the rejected hypotheses, which allows a few errors in exchange for more discoveries.'),
        ('Is looking at the data repeatedly during an A/B test also multiple testing?', 'Yes. Peeking and stopping as soon as p < 0.05 inflates false positives; use a fixed sample size or sequential testing methods.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('Statistical significance vs practical significance: why should you report effect sizes and confidence intervals?', 'Effect Size & Practical Significance', minutes=8, cards=[
    definition(
        defbox('A p-value mixes two things: the <strong>size of the effect</strong> and the <strong>sample size</strong>. With a huge sample, trivial differences '
               'become "highly significant"; with a small one, important differences may not reach significance. A p-value alone therefore cannot say whether '
               'an effect matters.',
               'Always report an <strong>effect size</strong> in meaningful units (difference in marks, difference in placement rate, odds ratio) with its '
               '<strong>confidence interval</strong>, plus a standardised effect where helpful: <strong>Cohen\'s d</strong>, <strong>r</strong>, '
               '<strong>η²</strong>, <strong>Cramér\'s V</strong>. Decide beforehand what the <strong>smallest effect of practical interest</strong> is.'),
        tags('effect size', 'practical significance', 'Cohen\'s d', 'confidence interval', 'sample size', 'minimum important difference'),
    ),
    analogy('A bathroom scale so precise that it detects you are <strong>2 grams heavier</strong> after a glass of water gives a "significant" change. Nobody '
            'would call it weight gain. Precision (sample size) is not importance (effect size).'),
    effect_anim(),
    real_world(
        scenario('A national comparison',
                 p('Across 200,000 students nationwide, students who submit assignments online score 0.4 marks higher (p &lt; 0.0001). The effect is real but tiny '
                   '(d ≈ 0.04); it does not justify an expensive policy change. Conversely, a 5-mark improvement in a 20-student pilot may be worth a larger trial '
                   'even with p = 0.12.')),
    ),
    example(
        strun("""
            from scipy import stats
            rng = np.random.default_rng(2)
            def report(a, b, label):
                t = stats.ttest_ind(a, b, equal_var=False)
                d = (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
                lo, hi = t.confidence_interval()
                print(f'{label:34} diff {a.mean() - b.mean():+.2f}  CI [{lo:+.2f}, {hi:+.2f}]  d = {d:+.3f}  p = {t.pvalue:.2g}')

            report(rng.normal(60.4, 10, 100_000), rng.normal(60, 10, 100_000), 'huge sample, tiny effect (0.4)')
            report(rng.normal(65, 10, 20), rng.normal(60, 10, 20), 'small sample, big effect (5)')
            report(rng.normal(65, 10, 200), rng.normal(60, 10, 200), 'same big effect, n = 200')

            # p-values of the SAME true effect (d = 0.3) vary hugely between replications
            ps = [stats.ttest_ind(rng.normal(3, 10, 100), rng.normal(0, 10, 100)).pvalue for _ in range(10)]
            print('10 replications of the same study:', [f'{x:.3f}' for x in ps])
        """, title=P),
        title='Example: Same p-value Story, Very Different Effects'),
    steps(
        ('Define the smallest important effect', 'Before the study, in real units.'),
        ('Estimate the effect', 'Difference, ratio or correlation.'),
        ('Add uncertainty', '95 % confidence interval.'),
        ('Compare the CI with the important threshold', 'Entirely above, entirely below, or straddling it?'),
        ('Report p as supporting information', 'Not as the headline.'),
        title='Steps to Report Results Meaningfully'),
    crossq(
        ('Can a non-significant result be important?', 'Yes. If the CI is wide and includes large effects, the study was inconclusive; it does not show "no effect".'),
        ('Why do p-values vary so much between replications?', 'They are random variables; with moderate power, the same true effect gives p-values from below 0.001 to above 0.3. Effect estimates with CIs are more stable to interpret.'),
        ('What is a standardised effect size good for?', 'Comparing studies with different units and planning sample size; but real units (marks, LPA) are easier for decision makers.'),
    ),
]),
])
