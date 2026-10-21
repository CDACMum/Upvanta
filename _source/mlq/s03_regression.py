from build import *
from mlq.anims import *
from mlq.runner import mlrun, pyshow
from mlq.data import STUDENTS, data_note

S = 'Python (scikit-learn) · uses sample data'
REG = STUDENTS + """
from sklearn.model_selection import train_test_split
reg = df.dropna(subset=['mock_test'])
Xr = reg[['attendance', 'study_hours', 'mock_test']]
yr = reg['final_score']
Xr_train, Xr_test, yr_train, yr_test = train_test_split(Xr, yr, test_size=0.25, random_state=42)
"""
REG_NOTE = note('Regression examples predict <code>final_score</code> from <code>attendance</code>, <code>study_hours</code> and <code>mock_test</code> '
                '(rows with a missing mock test dropped for simplicity), split 75/25 with <code>random_state=42</code>.', 'Data')

SECTION = dict(level='basic', title='Regression', questions=[

# ------------------------------------------------------------------ 11
Q('How does linear regression work? How do you interpret its coefficients?', 'Linear Regression', minutes=8, cards=[
    definition(
        defbox('<strong>Linear regression</strong> models the target as a weighted sum of features: ŷ = b₀ + b₁x₁ + … + bₙxₙ. <strong>Ordinary least squares</strong> '
               'chooses the coefficients that minimise the sum of squared residuals. In scikit-learn: <code>LinearRegression().fit(X, y)</code>, then '
               '<code>intercept_</code> and <code>coef_</code>.',
               '<strong>Interpretation</strong>: a coefficient is the expected change in y for a one-unit increase in that feature, <strong>holding the other features '
               'constant</strong>. Coefficients are comparable in size only if features are on the same scale (standardise first), and they are unreliable when '
               'features are strongly correlated (multicollinearity).'),
        tags('linear regression', 'OLS', 'coefficients', 'intercept', 'multicollinearity'),
    ),
    analogy('A coefficient is a <strong>price list</strong>: "each extra weekly study hour is worth about 1.6 marks, each extra attendance point about 0.3", '
            'and the intercept is the starting price before anything is added.'),
    linreg_anim(),
    real_world(
        scenario('Planning interventions',
                 p('Coefficients show coordinators which levers matter most in the data: if an extra study hour is associated with more marks than an extra '
                   'attendance point, a supervised study hall may help more than stricter attendance rules (keeping in mind that correlation is not causation).')),
    ),
    example(
        REG_NOTE,
        mlrun("""
            from sklearn.linear_model import LinearRegression
            lr = LinearRegression().fit(Xr_train, yr_train)
            print('intercept:', round(lr.intercept_, 2))
            print(pd.Series(lr.coef_, index=Xr.columns).round(3))
            print('test R²:', round(lr.score(Xr_test, yr_test), 3))

            student = pd.DataFrame({'attendance': [85], 'study_hours': [10], 'mock_test': [70]})
            pred = lr.predict(student)[0]
            manual = lr.intercept_ + (lr.coef_ * student.iloc[0].to_numpy()).sum()
            print(f'prediction {pred:.2f} = intercept + Σ coef·x = {manual:.2f}')
            more = student.assign(study_hours=11)
            print('one more study hour adds', round(lr.predict(more)[0] - pred, 3), 'marks')
        """, setup=REG, title=S),
        title='Example: Fit, Read Coefficients, Reproduce a Prediction by Hand'),
    steps(
        ('Check relationships', 'Scatter plots / correlations with the target.'),
        ('Fit', '<code>LinearRegression().fit(X_train, y_train)</code>.'),
        ('Interpret', '<code>intercept_</code>, <code>coef_</code> with feature names; standardise for comparable sizes.'),
        ('Evaluate', 'R², MAE/RMSE on test data; inspect residuals.'),
        ('Improve', 'Interactions/polynomial terms, regularisation, or non-linear models.'),
        title='Steps for Linear Regression'),
    crossq(
        ('Why do the learned coefficients differ slightly from the true ones used to generate the data?', 'Noise and the finite sample; also the target was clipped to 0–100 and features are correlated (mock test depends on hours).'),
        ('What is multicollinearity and why does it matter?', 'Highly correlated features make individual coefficients unstable and hard to interpret, though predictions can stay fine; check correlations or VIF, or use Ridge.'),
        ('Does scikit-learn give p-values?', 'No; it focuses on prediction. Use statsmodels (OLS summary) for statistical inference.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How do you evaluate a regression model? Explain MAE, MSE, RMSE and R².', 'Regression Metrics', minutes=7, cards=[
    definition(
        defbox('<strong>MAE</strong> (mean absolute error): average size of errors, in target units, robust to outliers. <strong>MSE</strong>: mean squared error, '
               'penalises large errors more; <strong>RMSE</strong> = √MSE, back in target units. <strong>R²</strong> (coefficient of determination): '
               '1 − SS_res/SS_tot, the share of variance explained relative to always predicting the mean; 1 is perfect, 0 equals the mean baseline, and it can be '
               'negative on test data. <strong>MAPE</strong>: mean absolute percentage error (unstable near zero).',
               'Always compare with a baseline (<code>DummyRegressor</code>) and choose the metric that matches the cost of errors.'),
        tags('MAE', 'MSE', 'RMSE', 'R²', 'DummyRegressor', 'metrics'),
    ),
    analogy('MAE is "on average the weather forecast is 2 °C off". RMSE is a stricter teacher who <strong>punishes the big misses</strong> heavily. R² asks '
            '"how much better is the forecast than just saying \'same as the yearly average\' every day?"'),
    reg_metrics_anim(),
    real_world(
        scenario('Explaining accuracy to coordinators',
                 p('"The model predicts final marks within about 4.6 marks on average (MAE), with occasional larger misses (RMSE ≈ 5.8); it explains about 80 % of '
                   'the variation in marks (R² ≈ 0.8), while always guessing the average would be off by about 10 marks": numbers from the example, each with a clear meaning.')),
    ),
    example(
        REG_NOTE,
        mlrun("""
            from sklearn.linear_model import LinearRegression
            from sklearn.dummy import DummyRegressor
            from sklearn.metrics import mean_absolute_error, mean_squared_error, root_mean_squared_error, r2_score

            for name, m in [('mean baseline', DummyRegressor()), ('linear', LinearRegression())]:
                pred = m.fit(Xr_train, yr_train).predict(Xr_test)
                print(f'{name:14} MAE {mean_absolute_error(yr_test, pred):5.2f}  MSE {mean_squared_error(yr_test, pred):6.2f}  '
                      f'RMSE {root_mean_squared_error(yr_test, pred):5.2f}  R² {r2_score(yr_test, pred):6.3f}')

            y_true = np.array([72, 58, 85, 64]); y_pred = np.array([70, 63, 84, 56])
            print('worked example:', mean_absolute_error(y_true, y_pred), round(root_mean_squared_error(y_true, y_pred), 2))
        """, setup=REG, title=S),
        title='Example: Metrics for a Baseline and a Linear Model'),
    steps(
        ('Pick the primary metric', 'MAE for interpretability, RMSE when large errors are costly.'),
        ('Compute on test data', 'Never on training data.'),
        ('Compare to a baseline', 'DummyRegressor (mean or median).'),
        ('Look beyond averages', 'Residual plots and errors per group (course, centre).'),
        title='Steps to Evaluate a Regressor'),
    crossq(
        ('Why is RMSE always ≥ MAE?', 'Squaring weights large errors more; they are equal only if all errors have the same size.'),
        ('Can R² be negative?', 'Yes, on test data when the model is worse than predicting the training mean; the baseline here is slightly negative for that reason.'),
        ('Which metric for scoring in GridSearchCV?', 'Use the negated versions, e.g. scoring="neg_mean_absolute_error", because scikit-learn always maximises scores.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What is regularisation? Compare Ridge, Lasso and ElasticNet.', 'Ridge, Lasso & ElasticNet', minutes=8, cards=[
    definition(
        defbox('<strong>Regularisation</strong> adds a penalty on coefficient size to the loss, trading a little bias for lower variance. <strong>Ridge</strong> '
               '(L2): penalty α·Σβ²; shrinks all coefficients, handles correlated features well. <strong>Lasso</strong> (L1): penalty α·Σ|β|; can set '
               'coefficients exactly to zero, performing feature selection. <strong>ElasticNet</strong>: a mix controlled by <code>l1_ratio</code>.',
               'Larger α means stronger shrinkage. Choose α with cross-validation (<code>RidgeCV</code>, <code>LassoCV</code>, <code>ElasticNetCV</code>). Standardise '
               'features first, because the penalty treats all coefficients equally. (In LogisticRegression the equivalent knob is <code>C</code> = 1/strength.)'),
        tags('Ridge', 'Lasso', 'ElasticNet', 'L1', 'L2', 'alpha'),
    ),
    analogy('Regularisation is a <strong>budget limit on explanations</strong>: Ridge makes every feature take a smaller share; Lasso is a strict manager who '
            '<strong>removes</strong> features that do not earn their keep.'),
    regularization_anim(),
    real_world(
        scenario('Many candidate features',
                 p('With dozens of engineered features (weekly quiz scores, login counts, assignment delays) and a few hundred students, plain regression overfits. '
                   'LassoCV kept the handful that matter and set the rest to zero; Ridge was more stable when several features were strongly correlated.')),
    ),
    example(
        REG_NOTE,
        mlrun("""
            from sklearn.linear_model import LinearRegression, Ridge, Lasso, LassoCV
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import make_pipeline

            rng = np.random.default_rng(1)
            noise = pd.DataFrame(rng.normal(size=(len(Xr), 8)), index=Xr.index, columns=[f'noise{i}' for i in range(8)])
            X_big = pd.concat([Xr, noise], axis=1)                      # 3 real + 8 useless features
            tr, te = Xr_train.index, Xr_test.index

            rows = {}
            for name, model in [('OLS', LinearRegression()), ('Ridge a=10', Ridge(alpha=10)), ('Lasso a=0.3', Lasso(alpha=0.3))]:
                pipe = make_pipeline(StandardScaler(), model).fit(X_big.loc[tr], yr.loc[tr])
                rows[name] = pipe[-1].coef_
                print(f'{name:12} test R² {pipe.score(X_big.loc[te], yr.loc[te]):.3f}')
            print(pd.DataFrame(rows, index=X_big.columns).round(2).head(6))
            print('Lasso zeroed', int((rows['Lasso a=0.3'] == 0).sum()), 'of 8 noise features')

            cv = make_pipeline(StandardScaler(), LassoCV(cv=5, random_state=0)).fit(X_big.loc[tr], yr.loc[tr])
            print('LassoCV chose alpha =', round(cv[-1].alpha_, 4))
        """, setup=REG, title=S),
        title='Example: Coefficients of OLS, Ridge and Lasso with Noise Features'),
    steps(
        ('Scale features', 'StandardScaler in a pipeline.'),
        ('Start with Ridge', 'Robust default for many correlated features.'),
        ('Need feature selection?', 'Lasso or ElasticNet.'),
        ('Tune α', 'RidgeCV/LassoCV or GridSearchCV over a log range.'),
        ('Inspect coefficients', 'Zeros (Lasso) and shrinkage paths.'),
        title='Steps to Regularise'),
    crossq(
        ('Why can Lasso produce exact zeros but Ridge cannot?', 'The L1 penalty has corners at zero, so the optimum often lies exactly on an axis; the smooth L2 penalty only shrinks towards zero.'),
        ('What happens with α = 0?', 'Ridge/Lasso become ordinary least squares (use LinearRegression instead for numerical reasons).'),
        ('Lasso with highly correlated features?', 'It tends to pick one arbitrarily and drop the others; ElasticNet keeps groups of correlated features together.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How can a linear model capture non-linear relationships? Explain PolynomialFeatures.', 'Polynomial Features', minutes=7, cards=[
    definition(
        defbox('<strong>PolynomialFeatures(degree=d)</strong> adds powers and interaction terms (x², x₁·x₂, …) as new features. A linear model on these features '
               'fits curves while remaining linear in its coefficients ("linear regression with polynomial basis").',
               'Number of features grows quickly with degree and inputs, which increases overfitting risk: combine with scaling and Ridge, and choose the degree '
               'with cross-validation. Alternatives: <code>SplineTransformer</code>, log/sqrt transforms, binning, or non-linear models (trees, boosting).'),
        tags('PolynomialFeatures', 'interactions', 'non-linearity', 'SplineTransformer', 'degree'),
    ),
    analogy('A ruler can only draw straight lines; give it a few <strong>bendable joints</strong> (x², x³) and it can trace a curve. Too many joints and it '
            'wiggles through every point, including the noise.'),
    poly_anim(),
    real_world(
        scenario('Diminishing returns of study hours',
                 p('Marks rise quickly with the first few weekly study hours and then flatten. A quadratic term captures this curve; an interaction '
                   'attendance × hours captures "hours help more when attendance is good".')),
    ),
    example(
        mlrun("""
            from sklearn.preprocessing import PolynomialFeatures, StandardScaler
            from sklearn.linear_model import LinearRegression, Ridge
            from sklearn.pipeline import make_pipeline
            from sklearn.model_selection import cross_val_score

            rng = np.random.default_rng(3)
            hours = rng.uniform(0, 20, 200).reshape(-1, 1)
            score = 40 + 6 * hours[:, 0] - 0.22 * hours[:, 0] ** 2 + rng.normal(0, 4, 200)   # rise then flatten

            print(PolynomialFeatures(2).fit(hours).get_feature_names_out(['hours']))
            print(PolynomialFeatures(2, include_bias=False).fit_transform([[2, 3]]), '← x1, x2, x1², x1·x2, x2²')
            for d in [1, 2, 3, 8, 15]:
                model = make_pipeline(PolynomialFeatures(d), StandardScaler(), LinearRegression())
                cv = cross_val_score(model, hours, score, cv=5, scoring='r2').mean()
                fit = model.fit(hours, score).score(hours, score)
                print(f'degree {d:2}: train R² {fit:.3f}   CV R² {cv:.3f}')
        """),
        title='Example: Choosing the Polynomial Degree by Cross-validation'),
    steps(
        ('Plot the relationship', 'Look for curvature in scatter/residual plots.'),
        ('Add features', 'PolynomialFeatures (or SplineTransformer) in a pipeline.'),
        ('Scale and regularise', 'StandardScaler + Ridge.'),
        ('Pick degree with CV', 'Stop when CV score stops improving.'),
        title='Steps to Model Curves'),
    crossq(
        ('How many features does degree 3 on 10 inputs create?', 'C(10+3, 3) = 286 including the bias; this explosion is why high degrees overfit and get slow.'),
        ('Why does train R² keep rising with degree while CV R² does not?', 'Higher degrees always fit training data at least as well (more flexibility), but start fitting noise, which does not generalise.'),
        ('Splines vs polynomials?', 'Splines are piecewise low-degree polynomials: flexible but well-behaved at the edges, often better than high-degree polynomials.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you check whether a regression model is adequate? Residual analysis and assumptions.', 'Residual Analysis', minutes=7, cards=[
    definition(
        defbox('Classical linear regression assumes: a <strong>linear</strong> relationship, <strong>independent</strong> errors, <strong>constant variance</strong> '
               'of errors (homoscedasticity), approximately <strong>normal</strong> errors (for inference), and no extreme <strong>multicollinearity</strong>.',
               'Check them with <strong>residuals</strong> (actual − predicted): plot residuals against predictions (patterns → missing non-linearity; funnel → '
               'unequal variance), histogram/Q-Q plot for normality, residuals by group or over time, and correlations/VIF among features. For pure prediction, '
               'good cross-validated error matters most, but residuals explain where the model fails.'),
        tags('residuals', 'assumptions', 'homoscedasticity', 'multicollinearity', 'diagnostics'),
    ),
    analogy('Residuals are the <strong>model\'s mistakes laid out on a table</strong>. Random crumbs mean the recipe is fine; crumbs that form a pattern mean '
            'something systematic is wrong with the recipe.'),
    residual_anim(),
    real_world(
        scenario('Under-predicting one course',
                 p('Residuals grouped by course showed PG-DAI students systematically scoring about 2.5 marks higher than predicted. Adding course as a feature '
                   '(one-hot) removed the bias. The example uses out-of-fold predictions (cross_val_predict) so every student gets an honest residual and the group '
                   'means are not distorted by a small test slice.')),
    ),
    example(
        data_note(),
        mlrun("""
            from sklearn.model_selection import cross_val_predict
            from sklearn.linear_model import LinearRegression
            from sklearn.compose import make_column_transformer
            from sklearn.preprocessing import OneHotEncoder
            from sklearn.pipeline import make_pipeline

            data = df.dropna(subset=['mock_test'])
            num = ['attendance', 'study_hours', 'mock_test']
            y = data['final_score']

            pred = cross_val_predict(LinearRegression(), data[num], y, cv=5)       # out-of-fold predictions for every student
            resid = y - pred
            print('mean residual by course, numeric features only:')
            print(resid.groupby(data['course']).agg(['mean', 'count']).round(2))

            ct = make_column_transformer((OneHotEncoder(), ['course']), remainder='passthrough')
            pred2 = cross_val_predict(make_pipeline(ct, LinearRegression()), data[num + ['course']], y, cv=5)
            resid2 = y - pred2
            print('after adding course:')
            print(resid2.groupby(data['course']).mean().round(2))
            print('overall residual std:', round(resid.std(), 2), '→', round(resid2.std(), 2))
            print('feature correlations:'); print(data[num].corr().round(2))
        """, setup=STUDENTS, title=S),
        title='Example: Residuals by Group Reveal a Missing Feature'),
    steps(
        ('Compute residuals', 'On validation/test data, or out-of-fold with cross_val_predict.'),
        ('Plot', 'Residuals vs predicted, vs each feature, histogram.'),
        ('Group', 'Mean residual by category/time.'),
        ('Check collinearity', 'Correlation matrix, VIF (statsmodels).'),
        ('Fix', 'Add features/terms, transform target, robust or non-linear models.'),
        title='Steps for Residual Analysis'),
    crossq(
        ('Why does a funnel-shaped residual plot matter?', 'Errors are not constant: predictions are less reliable for some ranges, and standard errors/intervals from OLS are wrong. A log transform of the target often helps.'),
        ('Do tree models need these assumptions?', 'No linearity or normality assumptions, but residual analysis is still useful to find where they fail.'),
        ('What is VIF?', 'Variance Inflation Factor: how much a coefficient\'s variance is inflated by correlation with other features; values above ~5–10 signal multicollinearity.'),
    ),
]),
])
