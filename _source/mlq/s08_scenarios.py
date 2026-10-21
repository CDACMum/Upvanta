from build import *
from mlq.anims import *
from mlq.runner import mlrun, pyshow
from mlq.data import STUDENTS
from mlq.s04_classification import CLF, CLF_NOTE

S = 'Python (scikit-learn) · uses sample data'

DROPOUT = CLF + """
rng2 = np.random.default_rng(11)
z = -3.2 - 0.09 * (df['attendance'] - 80) - 0.30 * (df['study_hours'] - 7) + rng2.normal(0, 0.6, len(df))
df['dropout'] = (rng2.random(len(df)) < 1 / (1 + np.exp(-z))).astype(int)
y_d = df['dropout']
Xd_train, Xd_test, yd_train, yd_test = train_test_split(X, y_d, test_size=0.25, random_state=1, stratify=y_d)
"""
DROPOUT_NOTE = note('Adds a rare target <code>dropout</code> (1 = left the course), generated from low attendance and low study hours with noise, '
                    'and a stratified 75/25 split <code>Xd_train / Xd_test</code>. Same features and preprocessing <code>pre</code> as the placement examples.', 'Data')

SECTION = dict(level='expert', title='Scenario-Based Questions', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: build a placement-prediction model end to end, from raw data to a saved, evaluated pipeline.', 'End-to-End Project', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('A reliable project follows a fixed order: <strong>define the target and metric</strong> → <strong>split off a test set</strong> → build a '
               '<strong>Pipeline</strong> (imputation, scaling, encoding, model) → compare candidates with <strong>cross-validation</strong> against a '
               '<strong>baseline</strong> → tune the best one → evaluate <strong>once</strong> on the test set (report, confusion matrix, AUC) → refit and '
               '<strong>save</strong> the pipeline with metadata.',
               'Each step guards against a classic mistake: the split prevents grading on training data, the pipeline prevents leakage and train/serve skew, the '
               'baseline shows whether the model adds value, and the single test evaluation keeps the final number honest.'),
        tags('Pipeline', 'ColumnTransformer', 'DummyClassifier', 'cross_validate', 'classification_report', 'joblib'),
    ),
    analogy('Like building a house: <strong>survey (data), foundation (split), frame (pipeline), inspections (CV), final certificate (test set), handover '
            '(saved model)</strong>. Skipping the inspection does not show until the roof leaks.'),
    e2e_anim(),
    real_world(
        scenario('Placement-readiness score for mentors',
                 p('The training team wants a probability of placement for every student two months before the drives start, so that mentors can focus on students '
                   'with a low score. The model must beat simply predicting "not placed" for everyone, be explainable, and run each week on fresh data.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.dummy import DummyClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
            from sklearn.model_selection import cross_validate, GridSearchCV
            from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
            import joblib

            candidates = {'baseline': DummyClassifier(strategy='most_frequent'),
                          'logistic': LogisticRegression(),
                          'forest': RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0),
                          'boosting': HistGradientBoostingClassifier(learning_rate=0.05, max_iter=200, random_state=0)}
            for name, m in candidates.items():
                r = cross_validate(Pipeline([('pre', pre), ('model', m)]), X_train, y_train, cv=5, scoring=['accuracy', 'roc_auc'])
                print(f'{name:9} accuracy {r["test_accuracy"].mean():.3f}   AUC {r["test_roc_auc"].mean():.3f}')

            search = GridSearchCV(Pipeline([('pre', pre), ('model', LogisticRegression())]),
                                  {'model__C': [0.001, 0.01, 0.1, 1, 10]}, cv=5, scoring='neg_log_loss').fit(X_train, y_train)
            print('best C:', search.best_params_['model__C'], f'CV log loss {-search.best_score_:.3f}')

            final = search.best_estimator_
            proba = final.predict_proba(X_test)[:, 1]
            print(f'TEST  AUC {roc_auc_score(y_test, proba):.3f}')
            print(confusion_matrix(y_test, final.predict(X_test)))
            print(classification_report(y_test, final.predict(X_test), target_names=['not placed', 'placed'], digits=3))
            joblib.dump(final, 'placement_model.joblib')
            print('saved pipeline with steps:', list(final.named_steps))
        """, setup=CLF, title=S),
        title='Example: Baseline → Candidates → Tune → Test Once → Save'),
    steps(
        ('Define target and metric', 'placed (1/0); ROC AUC for ranking students, recall for the at-risk group.'),
        ('Split first', 'Stratified train/test; never touch test until the end.'),
        ('Pipeline + baseline', 'ColumnTransformer + model; DummyClassifier as the floor.'),
        ('Compare and tune with CV', 'Prefer the simplest model within noise of the best.'),
        ('Test once, save, document', 'classification_report, confusion matrix, joblib + metadata.'),
        title='Steps for an End-to-End Model'),
    crossq(
        ('Logistic regression and the forest are within 0.01 AUC here. Which do you deploy?', 'The logistic model: the difference is within the CV noise, and it is faster, more stable and explainable through odds ratios. Complexity must earn its place.'),
        ('Why is the baseline AUC exactly 0.5?', 'A constant prediction cannot rank students at all; its accuracy (0.576 here) is the share of the majority class, which is why accuracy alone can flatter a model.'),
        ('Why tune C on log loss instead of ROC AUC?', 'AUC only measures ranking. Tuned on AUC, this search picks C=0.001: the ranking barely changes, but such strong regularisation squashes every probability towards the 42 % base rate, so the 0.5 threshold predicts almost nobody as placed. Log loss also rewards well-calibrated probabilities.'),
        ('After testing, should you retrain on all data?', 'Usually yes, with the same settings, to use every labelled row; the test score remains your estimate of its performance.'),
        ('What would you monitor after deployment?', 'Input distributions (drift), the share of high-risk predictions, and actual placement outcomes as they arrive (AUC/recall over time).'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: only about 1 in 12 students drops out. Build a model that catches most of them with limited mentoring capacity.', 'Imbalanced Risk Model', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('With a rare positive class, <strong>accuracy is misleading</strong> (predicting "no dropout" for everyone scores about 92 %). Use '
               '<strong>stratified</strong> splits, metrics for the rare class (<strong>recall, precision, PR AUC</strong>), and decide the '
               '<strong>decision threshold</strong> from the business constraint rather than using 0.5.',
               'Two common constraints: a <strong>recall target</strong> ("catch at least 80 % of dropouts") → choose the highest threshold that still meets it '
               'on validation data; a <strong>capacity limit</strong> ("mentors can call 40 students") → rank by probability and take the top 40, then report '
               'how many real dropouts that list contains. <code>class_weight="balanced"</code> shifts probabilities but does not replace choosing a threshold.'),
        tags('imbalanced data', 'threshold tuning', 'precision_recall_curve', 'recall', 'capacity', 'class_weight'),
    ),
    analogy('An airport security scanner is set to <strong>catch nearly every dangerous item</strong> and accept that some harmless bags get checked by hand. You '
            'move the sensitivity knob based on what a missed item costs and how many officers are available, not on "50 % sure".'),
    threshold_anim(),
    real_world(
        scenario('Early-warning list for mentors',
                 p('Losing a student costs the centre a seat and the student a career step; a mentoring call costs 20 minutes. The team sets the threshold so that '
                   'about 80 % of likely dropouts are flagged, and when the list is longer than mentors can handle, they work from the top of the ranking.')),
    ),
    example(
        DROPOUT_NOTE,
        mlrun("""
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_predict
            from sklearn.metrics import precision_recall_curve, average_precision_score, recall_score, precision_score

            print(f'dropout rate {y_d.mean():.3f} | always-"no" accuracy {1 - yd_test.mean():.3f}')
            pipe = Pipeline([('pre', pre), ('model', LogisticRegression())])

            # choose the threshold on out-of-fold predictions of the TRAINING data
            oof = cross_val_predict(pipe, Xd_train, yd_train, cv=5, method='predict_proba')[:, 1]
            prec, rec, thr = precision_recall_curve(yd_train, oof)
            ok = np.where(rec[:-1] >= 0.80)[0]
            t = thr[ok[-1]]
            print(f'chosen threshold {t:.3f} (validation recall {rec[ok[-1]]:.2f}, precision {prec[ok[-1]]:.2f})')

            pipe.fit(Xd_train, yd_train)
            p = pipe.predict_proba(Xd_test)[:, 1]
            print(f'test PR AUC {average_precision_score(yd_test, p):.3f}  (random model ≈ {yd_test.mean():.3f})')
            for name, cut in [('default 0.5', 0.5), ('tuned', t)]:
                pred = (p >= cut).astype(int)
                print(f'{name:12} flagged {pred.sum():3}  recall {recall_score(yd_test, pred):.2f}  precision {precision_score(yd_test, pred, zero_division=0):.2f}')

            # capacity: mentors can call only 25 of the 150 test students
            top = np.argsort(p)[::-1][:25]
            print(f'top-25 list contains {yd_test.iloc[top].sum()} of {yd_test.sum()} real dropouts')
        """, setup=DROPOUT, title=S),
        title='Example: Recall-Driven Threshold and a Capacity-Limited List'),
    steps(
        ('Measure the imbalance', 'Positive rate; accuracy of the always-majority baseline.'),
        ('Stratify everything', 'train_test_split(stratify=y), StratifiedKFold.'),
        ('Get honest probabilities', 'Out-of-fold predict_proba on training data.'),
        ('Pick the threshold from the constraint', 'Recall target or capacity (top-N).'),
        ('Report rare-class metrics on test', 'Recall, precision, PR AUC, number flagged.'),
        title='Steps for an Imbalanced Risk Model'),
    crossq(
        ('Why choose the threshold on out-of-fold predictions and not on the test set?', 'The threshold is a tuned parameter; choosing it on the test set makes the reported test recall optimistic.'),
        ('Recall is 0.8 but precision only 0.3. Is that bad?', 'It depends on costs: if a mentoring call is cheap and a dropout expensive, flagging three students to find one real case is a good trade.'),
        ('Validation recall was 0.81 but test recall is 0.67. Did something break?', 'The test set holds only 12 dropouts, so one student moves recall by 8 points. With rare classes, report how many cases the estimate rests on, and prefer cross-validated estimates.'),
        ('Would SMOTE help here?', 'Sometimes slightly; often class_weight plus threshold tuning gives the same benefit with less complexity. If used, oversample only inside the training folds (imblearn Pipeline).'),
        ('Why is PR AUC compared with the dropout rate?', 'A random model\'s PR AUC equals the positive rate, so that is the floor, not 0.5 as for ROC AUC.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: a colleague\'s new model scored better on her split. Is the improvement real?', 'Comparing Models Fairly', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('Scores from one split or one CV run vary by chance. Compare models on <strong>identical folds</strong> (same <code>cv</code> object), ideally '
               '<strong>repeated</strong> (<code>RepeatedStratifiedKFold</code>), and look at the <strong>per-fold differences</strong>: if the mean '
               'difference is small relative to its spread, the "improvement" is noise. Always include a <strong>baseline</strong> '
               '(<code>DummyClassifier</code>/<code>DummyRegressor</code>).',
               'Beyond the score: training and prediction time, stability across folds, explainability and maintenance cost. A model that wins by 0.002 AUC '
               'but is ten times slower and harder to explain usually loses the decision.'),
        tags('RepeatedStratifiedKFold', 'paired comparison', 'DummyClassifier', 'variance of CV', 'model selection'),
    ),
    analogy('Two runners finish 0.1 s apart in a single race with wind gusts. You would not crown a champion; you would <strong>race them several times on the '
            'same track</strong> and see who wins consistently.'),
    compare_anim(),
    real_world(
        scenario('Avoiding a pointless migration',
                 p('A team member proposes replacing the logistic model with a random forest because it scored higher on her own split. Repeated paired CV on '
                   'identical folds shows the forest wins only 9 of 25 folds, averages 0.009 AUC lower and takes about 30 times longer to fit, so the team keeps '
                   'the simpler model and saves the migration effort.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.dummy import DummyClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate, train_test_split
            from sklearn.metrics import roc_auc_score

            lr = Pipeline([('pre', pre), ('model', LogisticRegression())])
            rf = Pipeline([('pre', pre), ('model', RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1))])

            # single random splits: the AUC itself moves by about 0.05 between seeds
            for seed in [0, 1, 2, 3]:
                a, b, ya, yb = train_test_split(X_train, y_train, test_size=0.3, random_state=seed, stratify=y_train)
                s1 = roc_auc_score(yb, lr.fit(a, ya).predict_proba(b)[:, 1]); s2 = roc_auc_score(yb, rf.fit(a, ya).predict_proba(b)[:, 1])
                print(f'split seed {seed}: logistic {s1:.3f}  forest {s2:.3f}  -> {"forest" if s2 > s1 else "logistic"} wins')

            cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=0)
            res = {name: cross_validate(m, X_train, y_train, cv=cv, scoring='roc_auc') for name, m in
                   [('baseline', DummyClassifier()), ('logistic', lr), ('forest', rf)]}
            for name, r in res.items():
                print(f'{name:9} AUC {r["test_score"].mean():.3f} ± {r["test_score"].std():.3f}   fit {r["fit_time"].mean() * 1000:5.0f} ms')
            d = res['forest']['test_score'] - res['logistic']['test_score']
            print(f'forest − logistic per fold: mean {d.mean():+.3f}, std {d.std():.3f}, forest better in {(d > 0).sum()} of {len(d)} folds')
        """, setup=CLF, title=S),
        title='Example: Seed Lottery vs Repeated Paired Cross-Validation'),
    steps(
        ('Fix the folds', 'One cv object (RepeatedStratifiedKFold) shared by all models.'),
        ('Include a baseline', 'DummyClassifier / DummyRegressor.'),
        ('Collect per-fold scores', 'cross_validate returns arrays, plus fit times.'),
        ('Look at paired differences', 'Mean, std and how often each model wins.'),
        ('Decide with costs in mind', 'Speed, explainability, maintenance.'),
        title='Steps to Compare Models Fairly'),
    crossq(
        ('Why "paired"?', 'Both models are scored on the same folds, so fold difficulty cancels out in the difference; comparing two independent means wastes that information.'),
        ('Can you use a t-test on CV folds?', 'With care: folds overlap in training data, so standard t-tests are over-confident. Corrected resampled t-tests (Nadeau–Bengio) adjust for this.'),
        ('What is the risk of comparing many models on the same CV?', 'The best of many noisy scores is optimistic (multiple comparisons). Keep a final test set or use nested CV.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: a model reaches 99 % accuracy on the first try. How do you find out what is wrong?', 'Debugging a Too-Good Model', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('Near-perfect scores on a hard, human problem usually mean <strong>data leakage</strong>: information that would not be available at prediction '
               'time. Typical sources: a <strong>feature recorded after the outcome</strong> (e.g. interview rounds cleared, offer letter date), '
               '<strong>duplicate or related rows</strong> in both train and test, <strong>target-derived features</strong>, preprocessing fitted on all data, '
               'and time travel (training on the future).',
               'Debugging tools: feature importances (one feature dominating), single-feature models (one column alone gives near-perfect AUC), checking for '
               'duplicates across splits, and asking for each feature "<strong>when is this value known?</strong>". Fix the data, then re-evaluate with GroupKFold '
               'or time-based splits if needed.'),
        tags('data leakage', 'target leakage', 'duplicates', 'GroupKFold', 'feature audit'),
    ),
    analogy('A student scoring 100 % on every mock test is wonderful, until you find the <strong>answer key was stapled to the back of the paper</strong>. The '
            'first job is to check what was on the desk, not to celebrate.'),
    leak_anim(),
    real_world(
        scenario('The suspicious placement model',
                 p('A data extract for model training included <code>interview_rounds</code> (rounds cleared during the placement drive), which is only known after '
                   'the outcome, and some students appeared twice after re-enrolment. The model scored 0.99; after removing the leak and grouping by student, the '
                   'honest score was about 0.77, the number that matches what happens in production.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score, GroupKFold, train_test_split
            from sklearn.metrics import roc_auc_score

            rng = np.random.default_rng(3)
            leaky = df.copy()
            leaky['student_id'] = np.arange(len(leaky))
            # interview rounds cleared: known only AFTER the placement outcome
            leaky['interview_rounds'] = np.where(leaky['placed'] == 1, rng.integers(2, 5, len(leaky)), rng.integers(0, 2, len(leaky)))
            # 150 students re-enrolled: duplicated rows with tiny changes
            dup = leaky.sample(150, random_state=0).assign(attendance=lambda d: d['attendance'] + 0.1)
            leaky = pd.concat([leaky, dup], ignore_index=True)

            feats = num + ['interview_rounds']
            Xl = leaky[feats].fillna(leaky[feats].median()); yl = leaky['placed']
            rf = RandomForestClassifier(n_estimators=200, random_state=0)
            print(f'leaky model CV accuracy {cross_val_score(rf, Xl, yl, cv=5).mean():.3f}')

            rf.fit(Xl, yl)
            print('importances:', pd.Series(rf.feature_importances_, index=feats).round(3).to_dict())
            for f in feats:
                auc = roc_auc_score(yl, Xl[f])
                print(f'  single-feature AUC {f:16} {max(auc, 1 - auc):.3f}')

            a, b = train_test_split(leaky, test_size=0.25, random_state=0)
            print('students in both train and test:', len(set(a['student_id']) & set(b['student_id'])))

            clean = num
            g = GroupKFold(n_splits=5)
            honest = cross_val_score(rf, Xl[clean], yl, cv=g, groups=leaky['student_id']).mean()
            naive = cross_val_score(rf, Xl[clean], yl, cv=5).mean()
            print(f'without interview_rounds: plain CV {naive:.3f}   GroupKFold by student {honest:.3f}')
        """, setup=CLF, title=S),
        title='Example: Plant a Leak and Duplicates, Then Detect and Remove Them'),
    steps(
        ('Be suspicious', 'Compare with the baseline and with what domain experts expect.'),
        ('Inspect importances', 'One feature dominating is a red flag.'),
        ('Single-feature AUC', 'Any column that alone predicts nearly perfectly needs an explanation.'),
        ('Ask "when is it known?"', 'Drop anything recorded at or after the outcome.'),
        ('Check duplicates and groups', 'Use GroupKFold / time splits; re-evaluate.'),
        title='Steps to Debug a Too-Good Model'),
    crossq(
        ('Why do duplicates inflate scores even without a leaky feature?', 'A near-copy of a test row sits in training, so a flexible model like a forest can recall its label rather than generalise.'),
        ('What is train/serve skew?', 'Features computed differently in training and in production (e.g. averages over different windows). The model looks good offline and fails live; shared pipelines prevent it.'),
        ('How do you prevent leakage organisationally?', 'Document for each feature the time it becomes available, build training sets "as of" the prediction date, and review features with domain experts.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Scenario: the deployed model scores new batches every month. How do you detect drift and decide when to retrain?', 'Monitoring & Drift', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('<strong>Data drift</strong>: the distribution of inputs changes (new batches have lower mock scores, a new centre opens). '
               '<strong>Concept drift</strong>: the relationship between inputs and outcome changes (the job market shifts, so the same scores lead to fewer '
               'placements). Both degrade a model silently because it still returns confident predictions.',
               'Monitor: input statistics per feature (mean shift in standard deviations, <strong>PSI</strong> — Population Stability Index; PSI &lt; 0.1 stable, '
               '0.1–0.25 moderate, &gt; 0.25 significant), the share of unknown categories, the distribution of predicted probabilities, and, once labels arrive, '
               'real performance. Retrain on recent data when drift is significant or performance falls, then compare the new model with the old one before '
               'switching.'),
        tags('data drift', 'concept drift', 'PSI', 'monitoring', 'retraining', 'batch scoring'),
    ),
    analogy('A model is a <strong>map</strong>. Data drift is driving into a new suburb the map barely covers; concept drift is when the roads themselves have been '
            'rebuilt. Either way, the sat-nav keeps giving confident directions, so you need signs that tell you the map is out of date.'),
    drift_anim(),
    real_world(
        scenario('Monthly placement scoring',
                 p('Each month the scoring job loads the saved pipeline, scores the new batch, writes PSI per feature and the mean predicted probability to a '
                   'monitoring table, and sends an alert when any PSI exceeds 0.25. When the placement results for a batch arrive, real AUC is added to the same '
                   'dashboard.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import roc_auc_score

            model = Pipeline([('pre', pre), ('model', LogisticRegression())]).fit(X_train, y_train)

            def psi(ref, new, bins=10):
                edges = np.unique(np.quantile(ref.dropna(), np.linspace(0, 1, bins + 1)))
                edges[0], edges[-1] = -np.inf, np.inf
                r = np.histogram(ref.dropna(), edges)[0] / ref.notna().sum()
                n = np.histogram(new.dropna(), edges)[0] / new.notna().sum()
                r, n = np.clip(r, 1e-4, None), np.clip(n, 1e-4, None)
                return float(((n - r) * np.log(n / r)).sum())

            rng = np.random.default_rng(5)
            months = {'Jan (like training)': (0, 0.0), 'Mar (weaker mocks)': (-6, 0.0), 'Jun (mocks + market)': (-12, -1.5)}
            for month, (shift, market) in months.items():
                batch = X_test.sample(2000, replace=True, random_state=len(month))
                batch['mock_test'] = (batch['mock_test'] + shift).clip(0, 100)
                # outcome generated with the true rule; "market" lowers placement chances for everyone (concept drift)
                z = (-13 + 0.07 * batch['attendance'] + 0.18 * batch['study_hours'] + 0.08 * batch['mock_test'].fillna(65)
                     + np.where(batch['course'] == 'PG-DBDA', 0.6, 0) + market)
                y_true = (rng.random(len(batch)) < 1 / (1 + np.exp(-z))).astype(int)
                p = model.predict_proba(batch)[:, 1]
                drift = {c: round(psi(X_train[c], batch[c]), 3) for c in num}
                print(f'{month:21} PSI {drift}  mean p {p.mean():.2f}  actual rate {y_true.mean():.2f}  AUC {roc_auc_score(y_true, p):.3f}')
        """, setup=CLF, title=S),
        title='Example: PSI per Feature, Predicted vs Actual Rate, AUC per Month'),
    steps(
        ('Save reference statistics', 'Training distributions (quantile bins) next to the model.'),
        ('Log every batch', 'Inputs, predictions, model version.'),
        ('Compute drift metrics', 'PSI / mean shift per feature; share of unknown categories.'),
        ('Join outcomes when they arrive', 'Real AUC, recall, calibration (predicted vs actual rate).'),
        ('Retrain and compare', 'Champion vs challenger on recent data before switching.'),
        title='Steps to Monitor a Deployed Model'),
    crossq(
        ('In June the AUC is still fine but the predicted placement rate is far above the actual one. What happened?', 'Concept drift: ranking still works (AUC), but the overall level shifted, so probabilities are miscalibrated. Recalibrating or retraining on recent outcomes fixes the level.'),
        ('Why can drift be detected before labels arrive?', 'Input and prediction distributions are available immediately; outcomes (placements) may take months.'),
        ('How often should you retrain?', 'On a schedule matched to how fast the domain changes, plus on alerts; always validate the new model against the current one first.'),
        ('What is PSI\'s weakness?', 'It depends on binning and sample size and looks at one feature at a time; combine it with performance monitoring.'),
    ),
]),
])
