from build import *
from statq.anims import *
from statq.runner import strun, pyshow
from statq.data import STUDENTS, data_note

S = 'Python (SciPy · statsmodels) · uses sample data'
P = 'Python (SciPy · statsmodels)'

SECTION = dict(level='advanced', title='Correlation & Regression', questions=[

# ------------------------------------------------------------------ 31
Q('What are covariance and correlation? Compare Pearson, Spearman and Kendall correlation.', 'Correlation', minutes=9, cards=[
    definition(
        defbox('<strong>Covariance</strong> measures whether two variables move together, but its size depends on the units. <strong>Pearson\'s r</strong> = '
               'cov(X, Y) / (s_X·s_Y) rescales it to −1…+1 and measures the strength of a <strong>linear</strong> relationship. r² is the share of variance '
               'in one variable explained by a straight line on the other.',
               '<strong>Spearman\'s ρ</strong> is Pearson on ranks: it measures any <strong>monotonic</strong> relationship and resists outliers. '
               '<strong>Kendall\'s τ</strong> counts concordant vs discordant pairs; it is robust and preferred for small samples with ties. r ≈ 0 does '
               '<strong>not</strong> mean "no relationship": a U-shape can have r = 0. Always plot the data. <code>stats.pearsonr / spearmanr / kendalltau</code> '
               'also give p-values; <code>df.corr(method=...)</code> gives matrices.'),
        tags('covariance', 'Pearson r', 'Spearman ρ', 'Kendall τ', 'correlation matrix', 'r²', 'monotonic'),
    ),
    analogy('Correlation is how tightly a <strong>crowd of points follows an invisible straight road</strong>. Pearson needs the road to be straight; Spearman only '
            'needs it to keep going uphill, however it curves.'),
    corr_anim(),
    real_world(
        scenario('What moves the final score?',
                 p('A correlation matrix of attendance, study hours, pre/post-test and final score is the first look at what drives results. It shows weekly '
                   'study hours are the strongest single correlate (r = 0.66), while centre and method need other tools (they are categorical).')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            cols = ['attendance', 'study_hours', 'pre_test', 'post_test', 'final_score']
            print(df[cols].corr().round(3))
            print(f"covariance attendance-final: {df['attendance'].cov(df['final_score']):.2f} (units: % x marks)")

            for name, fn in [('Pearson', stats.pearsonr), ('Spearman', stats.spearmanr), ('Kendall', stats.kendalltau)]:
                r = fn(df['study_hours'], df['final_score'])
                print(f'{name:8} study_hours vs final: {r.statistic:.3f}  p = {r.pvalue:.1e}')

            x = np.linspace(-3, 3, 101)
            print(f'U-shape y = x^2: Pearson {stats.pearsonr(x, x ** 2).statistic:.3f}, Spearman {stats.spearmanr(x, x ** 2).statistic:.3f}')
            x = np.arange(1, 11); y = np.exp(x)
            print(f'monotonic y = e^x: Pearson {stats.pearsonr(x, y).statistic:.3f}, Spearman {stats.spearmanr(x, y).statistic:.3f}')

            rng = np.random.default_rng(1)
            a = rng.normal(size=30); b = rng.normal(size=30)
            print(f'two unrelated variables: Pearson {stats.pearsonr(a, b).statistic:.3f}', end='')
            a2, b2 = np.append(a, 10), np.append(b, 10)
            print(f' -> add one outlier (10, 10): Pearson {stats.pearsonr(a2, b2).statistic:.3f}, Spearman {stats.spearmanr(a2, b2).statistic:.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: Correlation Matrix, Three Coefficients, U-shapes and Outliers'),
    steps(
        ('Plot first', 'Scatter plot / pairplot to see shape and outliers.'),
        ('Choose the coefficient', 'Linear → Pearson; monotonic, ordinal or outliers → Spearman/Kendall.'),
        ('Compute with a p-value and CI', 'stats.pearsonr(x, y) (.confidence_interval()).'),
        ('Interpret r²', 'Share of variance explained by a linear fit.'),
        ('Do not infer causation', 'Look for confounders (next question).'),
        title='Steps to Analyse Correlation'),
    crossq(
        ('r = 0.3. Strong or weak?', 'Weak to moderate: a line explains 9 % of the variance. Context matters; in social data 0.3 can still be useful.'),
        ('Why can one outlier create a strong correlation?', 'Pearson uses squared deviations, so a single far point dominates. Here it lifted r from −0.16 to 0.78, while Spearman stayed near 0 (0.03).'),
        ('Is correlation symmetric?', 'Yes, r(X, Y) = r(Y, X); regression is not (predicting Y from X differs from X from Y).'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('Correlation does not imply causation: what are confounding variables and how do you control for them?', 'Correlation vs Causation', minutes=9, cards=[
    definition(
        defbox('Two variables can be correlated because X causes Y, Y causes X (<strong>reverse causation</strong>), both are caused by a third variable '
               '(<strong>confounder</strong>), or by chance (especially when many pairs are examined). A confounder Z influences both X and Y and creates a '
               'correlation between them even if X has no effect on Y.',
               'Ways to deal with it: <strong>randomised experiments</strong> (random assignment breaks the link between X and all confounders), or, with '
               'observational data, <strong>adjusting</strong> for measured confounders: stratification, <strong>partial correlation</strong>, multiple '
               'regression, matching. Adjustment only handles confounders you measured; causal claims from observational data need strong domain arguments.'),
        tags('causation', 'confounder', 'reverse causation', 'spurious correlation', 'partial correlation', 'randomised experiment'),
    ),
    analogy('Ice-cream sales and drowning deaths rise together. Ice cream does not cause drowning; <strong>hot weather</strong> (the confounder) causes both. '
            'Compare days with the same temperature and the link disappears.'),
    confound_anim(),
    real_world(
        scenario('Library visits and placement',
                 p('Students who visit the library more get placed more often. Before mandating library hours, the coordinator checks whether library visits still '
                   'matter once study hours are taken into account: motivated students both study more and visit the library, and the effect of the visits '
                   'themselves turns out to be negligible.')),
    ),
    example(
        data_note(),
        strun("""
            from scipy import stats
            import statsmodels.formula.api as smf
            rng = np.random.default_rng(9)
            # library visits per month are driven by study hours, NOT by placement
            df['library_visits'] = np.round(0.8 * df['study_hours'] + rng.normal(0, 2, len(df))).clip(0)

            r = stats.pearsonr(df['library_visits'], df['final_score'])
            print(f'library visits vs final score: r = {r.statistic:.3f}, p = {r.pvalue:.1e}')

            # partial correlation: remove the effect of study hours from both, correlate the residuals
            res_lib = smf.ols('library_visits ~ study_hours', df).fit().resid
            res_fin = smf.ols('final_score ~ study_hours', df).fit().resid
            pr = stats.pearsonr(res_lib, res_fin)
            print(f'partial r (controlling study hours) = {pr.statistic:.3f}, p = {pr.pvalue:.3f}')

            m1 = smf.ols('final_score ~ library_visits', df).fit()
            m2 = smf.ols('final_score ~ library_visits + study_hours', df).fit()
            print(f'coefficient of library_visits alone {m1.params["library_visits"]:.3f} (p {m1.pvalues["library_visits"]:.1e})'
                  f' | with study_hours {m2.params["library_visits"]:.3f} (p {m2.pvalues["library_visits"]:.3f})')

        """, setup=STUDENTS, title=S),
        title='Example: A Spurious Link Explained by a Confounder'),
    steps(
        ('List plausible causal paths', 'X → Y, Y → X, Z → both, chance.'),
        ('Identify measurable confounders', 'From domain knowledge, before analysis.'),
        ('Adjust', 'Stratify, partial correlation, or include them in a regression.'),
        ('Prefer experiments', 'Randomise when the decision is important and feasible.'),
        ('Phrase conclusions carefully', '"associated with" unless the design supports "causes".'),
        title='Steps to Reason About Causation'),
    crossq(
        ('Can adjustment make things worse?', 'Yes: adjusting for a variable caused by both X and Y (a collider) or a mediator on the causal path can create or hide associations.'),
        ('Why do randomised trials solve confounding?', 'Random assignment makes the groups equal on average in every characteristic, measured or not, so differences in outcome come from the treatment.'),
        ('What are the Bradford Hill hints for causation?', 'Strength, consistency, temporality (cause before effect), dose-response, plausibility, experiment, coherence; temporality is the only strict requirement.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('Explain simple linear regression: least squares, slope, intercept, R², and confidence vs prediction intervals.', 'Simple Linear Regression', minutes=10, cards=[
    definition(
        defbox('Simple linear regression models y = β₀ + β₁x + ε. <strong>Ordinary least squares (OLS)</strong> picks the line minimising the sum of squared '
               'residuals: β₁ = cov(x, y) / var(x), β₀ = ȳ − β₁x̄. The <strong>slope</strong> is the expected change in y per unit of x; the '
               '<strong>intercept</strong> is the prediction at x = 0 (often not meaningful). <strong>R²</strong> = 1 − SS_res/SS_tot is the share of variance '
               'explained; with one predictor it equals r².',
               'statsmodels reports each coefficient\'s SE, t, p-value and CI. A <strong>confidence interval</strong> for the mean response (where is the line?) '
               'is narrow; a <strong>prediction interval</strong> for a single new student (where will this student score?) is much wider because it adds '
               'individual noise. <code>smf.ols("y ~ x", df).fit()</code>, <code>.summary()</code>, <code>.get_prediction().summary_frame()</code>.'),
        tags('OLS', 'least squares', 'slope', 'intercept', 'R²', 'residual', 'prediction interval', 'statsmodels'),
    ),
    analogy('Fitting a line is like hanging a <strong>straight rod among nails</strong> with springs attached to each nail: the rod settles where the total spring '
            'tension (squared distances) is smallest.'),
    ols_anim(),
    real_world(
        scenario('"How much does one more study hour help?"',
                 p('Regression of final score on weekly study hours gives a slope in marks per hour, with a confidence interval, that mentors can quote to students. '
                   'For an individual student planning 12 hours a week, the prediction interval shows the realistic range of outcomes, not just the average.')),
    ),
    example(
        data_note(),
        strun("""
            import statsmodels.formula.api as smf
            x, y = df['study_hours'], df['final_score']
            b1 = np.cov(x, y)[0, 1] / x.var()
            b0 = y.mean() - b1 * x.mean()
            print(f'by hand: final = {b0:.3f} + {b1:.3f} x study_hours')

            m = smf.ols('final_score ~ study_hours', df).fit()
            print(m.summary().tables[1])
            print(f'R^2 = {m.rsquared:.4f} = r^2 = {np.corrcoef(x, y)[0, 1] ** 2:.4f} | residual SD {np.sqrt(m.scale):.2f}')

            new = pd.DataFrame({'study_hours': [4, 12]})
            pred = m.get_prediction(new).summary_frame(alpha=0.05)
            print(pred[['mean', 'mean_ci_lower', 'mean_ci_upper', 'obs_ci_lower', 'obs_ci_upper']].round(2))
            print('residuals sum to', round(m.resid.sum(), 8), '| mean of fitted =', round(m.fittedvalues.mean(), 3), '= mean of y', round(y.mean(), 3))
        """, setup=STUDENTS, title=S),
        title='Example: Slope by Hand and with statsmodels, CI vs Prediction Interval'),
    steps(
        ('Plot y against x', 'Check the relationship looks linear.'),
        ('Fit OLS', 'smf.ols("final_score ~ study_hours", df).fit().'),
        ('Read the coefficient table', 'Slope, its CI and p-value; intercept with caution.'),
        ('Check fit and residuals', 'R², residual SD, residual plots.'),
        ('Predict with intervals', 'get_prediction(...).summary_frame(): mean CI vs observation PI.'),
        title='Steps for Simple Linear Regression'),
    crossq(
        ('Why squared residuals?', 'They penalise large errors, give a unique closed-form solution, and correspond to maximum likelihood under normal errors.'),
        ('R² is 0.44. Is that good?', 'Study hours alone explain 44 % of score variation, a lot for one behavioural variable; the slope can be precise and useful even if individual predictions are rough.'),
        ('Can you predict for 40 study hours?', 'That is extrapolation beyond the data (max about 26 hours); the linear relationship may not hold there.'),
        ('Confidence vs prediction interval?', 'CI: uncertainty of the average score at x. PI: range for one new student, adding the residual SD; it never shrinks to zero with more data.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How do you interpret a multiple regression? Explain coefficients, dummy variables, adjusted R² and the F-test.', 'Multiple Regression', minutes=10, cards=[
    definition(
        defbox('Multiple regression y = β₀ + β₁x₁ + … + βₖxₖ + ε estimates each coefficient <strong>holding the other predictors constant</strong>. Categorical '
               'variables enter as <strong>dummy variables</strong> (one per level, minus a reference level): <code>C(centre)</code> in a formula; each dummy '
               'coefficient is the difference from the reference group.',
               '<strong>Adjusted R²</strong> penalises extra predictors (plain R² never decreases when you add one). The <strong>F-test</strong> checks whether the '
               'model as a whole beats an intercept-only model; each coefficient\'s t-test checks that predictor given the others. Compare nested models with an '
               'F-test (<code>anova_lm(m_small, m_big)</code>) or AIC/BIC. Coefficients are only comparable in size after standardising.'),
        tags('multiple regression', 'ceteris paribus', 'dummy variables', 'reference level', 'adjusted R²', 'F-test', 'AIC'),
    ),
    analogy('Asking "what is the effect of study hours?" in a multiple regression is like comparing <strong>two students who are identical in attendance, test '
            'score and centre</strong> and differ only in study hours.'),
    multi_reg_anim(),
    real_world(
        scenario('Which factors matter, and how much?',
                 p('The academic team models the final score on attendance, study hours, post-test score and centre. The coefficients say how many marks each '
                   'factor is worth on its own, and the centre dummies reveal a Pune effect that was invisible in the simple comparison of centre averages.')),
    ),
    example(
        data_note(),
        strun("""
            import statsmodels.formula.api as smf
            from statsmodels.stats.anova import anova_lm
            m1 = smf.ols('final_score ~ study_hours', df).fit()
            m2 = smf.ols('final_score ~ attendance + study_hours + post_test + C(centre)', df).fit()
            print(m2.summary().tables[1])
            print(f'R^2 {m2.rsquared:.4f}  adj R^2 {m2.rsquared_adj:.4f}  F = {m2.fvalue:.1f} (p {m2.f_pvalue:.1e})  AIC {m2.aic:.1f} vs {m1.aic:.1f}')
            print(anova_lm(m1, m2).round(4))

            # true generating effects were 0.30, 1.6, 0.35 and Pune +2; compare the raw centre means
            print('raw centre means:', df.groupby('centre')['final_score'].mean().round(2).to_dict())

            z = df[['attendance', 'study_hours', 'post_test', 'final_score']].apply(lambda s: (s - s.mean()) / s.std())
            print('standardised coefficients:', smf.ols('final_score ~ attendance + study_hours + post_test', z).fit().params.drop('Intercept').round(3).to_dict())

            noise = smf.ols('final_score ~ attendance + study_hours + post_test + C(centre) + np.random.default_rng(0).normal(size=len(df))', df).fit()
            print(f'adding a pure-noise predictor: R^2 {noise.rsquared:.5f} (up) adj R^2 {noise.rsquared_adj:.5f} (down)')
        """, setup=STUDENTS, title=S),
        title='Example: Final Score on Four Predictors, Dummies, Nested F-test, Standardised Coefficients'),
    steps(
        ('Choose predictors from domain knowledge', 'Avoid post-outcome variables (leakage).'),
        ('Fit with a formula', 'C(...) for categorical variables; check the reference level.'),
        ('Read coefficients with CIs', '"Holding the others constant".'),
        ('Compare models', 'Adjusted R², nested F-test, AIC/BIC.'),
        ('Check diagnostics', 'Residuals, multicollinearity, influential points (next question).'),
        title='Steps for Multiple Regression'),
    crossq(
        ('Why did the Pune effect appear only in the multiple regression?', 'Raw centre means mix the centre effect with differences in attendance, hours and test scores; and residual noise is much smaller once those are modelled, so the 2-mark effect becomes detectable.'),
        ('Why is the coefficient of study hours different from the simple regression?', 'In the simple model it also picked up effects of variables correlated with study hours (post-test). Multiple regression separates them.'),
        ('What is the dummy-variable trap?', 'Including a dummy for every level plus an intercept makes the columns perfectly collinear; formulas drop one level automatically.'),
        ('Does a large coefficient mean an important predictor?', 'Not necessarily; it depends on units. Compare standardised coefficients or the change in R² when the variable is dropped.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('What are the assumptions of linear regression and how do you check them? Explain multicollinearity and VIF.', 'Regression Diagnostics', minutes=10, cards=[
    definition(
        defbox('OLS inference relies on (LINE): <strong>Linearity</strong> of the relationship, <strong>Independence</strong> of errors, <strong>Normality</strong> '
               'of errors (mainly for small samples), and <strong>Equal variance</strong> of errors (<strong>homoscedasticity</strong>). Check with residual-vs-'
               'fitted plots, Q-Q plots of residuals, the <strong>Breusch-Pagan</strong> test (heteroscedasticity), Jarque-Bera (normality), Durbin-Watson '
               '(autocorrelation).',
               '<strong>Multicollinearity</strong>: predictors strongly correlated with each other inflate coefficient SEs and make individual coefficients '
               'unstable (even sign-flipping), though predictions stay fine. Measure with the <strong>variance inflation factor</strong> VIF = 1/(1 − R²ⱼ); '
               'VIF above 5–10 is a warning. <strong>Influential points</strong> are found with leverage and <strong>Cook\'s distance</strong>. Remedies: '
               'transformations, robust (HC3) standard errors, dropping or combining collinear predictors, regularisation.'),
        tags('LINE assumptions', 'residual plot', 'heteroscedasticity', 'Breusch-Pagan', 'VIF', 'multicollinearity', 'Cook\'s distance', 'robust SE'),
    ),
    analogy('Multicollinearity is like trying to judge <strong>which of two inseparable twins</strong> broke the vase: together they clearly did it, but you cannot '
            'tell how much each contributed.'),
    diag_anim(),
    real_world(
        scenario('A model with both pre-test and post-test',
                 p('An analyst adds both pre-test and post-test scores to the model. They are strongly correlated (r ≈ 0.81), so their coefficients become uncertain '
                   'and hard to interpret. Their VIFs rise to about 3 and the standard error of the post-test coefficient almost doubles; the fix is to use the post-test (or the gain) rather than both, depending on the question.')),
    ),
    example(
        data_note(),
        strun("""
            import statsmodels.formula.api as smf
            from statsmodels.stats.outliers_influence import variance_inflation_factor
            from statsmodels.stats.diagnostic import het_breuschpagan
            from statsmodels.stats.stattools import jarque_bera, durbin_watson

            m = smf.ols('final_score ~ attendance + study_hours + post_test + pre_test', df).fit()
            X = m.model.exog
            vif = {name: round(float(variance_inflation_factor(X, i)), 2) for i, name in enumerate(m.model.exog_names) if name != 'Intercept'}
            print('VIF:', vif)
            print(m.params.round(3).to_dict())
            print('SE of post_test coefficient: with pre_test', round(m.bse['post_test'], 4),
                  '| without', round(smf.ols('final_score ~ attendance + study_hours + post_test', df).fit().bse['post_test'], 4))

            lm_p = het_breuschpagan(m.resid, X)[1]
            print(f'Breusch-Pagan p = {lm_p:.3f} | Jarque-Bera p = {jarque_bera(m.resid)[1]:.3f} | Durbin-Watson = {durbin_watson(m.resid):.3f}')

            # heteroscedastic example: the spread of y grows with x -> robust standard errors
            rng = np.random.default_rng(4)
            d = pd.DataFrame({'x': rng.uniform(1, 10, 300)})
            d['y'] = 3 + 2 * d['x'] + rng.normal(0, 0.6 * d['x'])
            h = smf.ols('y ~ x', d).fit()
            print(f'funnel-shaped data: Breusch-Pagan p = {het_breuschpagan(h.resid, h.model.exog)[1]:.1e}; '
                  f'SE of slope classic {h.bse["x"]:.4f} vs HC3 robust {h.get_robustcov_results("HC3").bse[1]:.4f}')

            infl = m.get_influence().cooks_distance[0]
            print(f'max Cook distance {infl.max():.4f} (row {infl.argmax()}); rows above 4/n: {(infl > 4 / len(df)).sum()}')
        """, setup=STUDENTS, title=S),
        title='Example: VIF, Breusch-Pagan, Jarque-Bera, Durbin-Watson, Robust SE, Cook\'s Distance'),
    steps(
        ('Plot residuals vs fitted', 'Look for curves (non-linearity) and funnels (heteroscedasticity).'),
        ('Q-Q plot of residuals', 'Heavy tails or skew; matters most for small n.'),
        ('Compute VIFs', 'variance_inflation_factor for each predictor.'),
        ('Check influence', 'Cook\'s distance, leverage; investigate, do not auto-delete.'),
        ('Fix', 'Transform, add terms, robust SE (HC3), drop/merge collinear predictors, regularise.'),
        title='Steps to Diagnose a Regression'),
    crossq(
        ('Does multicollinearity bias predictions?', 'No; predictions and overall R² are fine. It only makes individual coefficients imprecise and unstable.'),
        ('Do the raw variables need to be normal?', 'No; the assumption is about the errors (residuals), and with large samples even that matters little for coefficient tests.'),
        ('What do robust (HC3) standard errors fix?', 'They keep coefficient SEs and p-values valid under heteroscedasticity; the coefficients themselves stay the same.'),
        ('What is the 4/n rule for Cook\'s distance?', 'A common screening threshold; points above it deserve a look, but a few are expected in any large dataset.'),
    ),
]),
])
