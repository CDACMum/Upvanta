from build import *
from mlq.anims import *
from mlq.runner import mlrun, pyshow
from mlq.s04_classification import CLF, CLF_NOTE

S = 'Python (scikit-learn) · uses sample data'

SECTION = dict(level='advanced', title='Model Selection, Tuning & Deployment', questions=[

# ------------------------------------------------------------------ 26
Q('What is cross-validation? Compare KFold, StratifiedKFold, GroupKFold and TimeSeriesSplit.', 'Cross-Validation', minutes=8, cards=[
    definition(
        defbox('<strong>k-fold cross-validation</strong> splits the training data into k folds, trains k models (each leaving one fold out) and averages the k '
               'validation scores. Every row is validated exactly once, so the estimate is less dependent on one lucky or unlucky split, and the '
               '<strong>standard deviation</strong> shows how stable the model is. <code>cross_val_score</code> returns one metric; '
               '<code>cross_validate</code> returns several metrics, fit times and (optionally) training scores.',
               'Choose the splitter to match the data: <strong>StratifiedKFold</strong> keeps class proportions (the default for classifiers when cv is an '
               'integer); <strong>GroupKFold</strong> keeps all rows of one group (student, patient, customer) in the same fold; <strong>TimeSeriesSplit</strong> '
               'always validates on later data than it trains on. Preprocessing must sit inside a Pipeline so it is re-fitted in each fold.'),
        tags('cross_val_score', 'cross_validate', 'KFold', 'StratifiedKFold', 'GroupKFold', 'TimeSeriesSplit'),
    ),
    analogy('One test paper can be easy or hard by chance. Cross-validation is like giving the class <strong>five different papers</strong> and averaging: the '
            'average is fairer, and the spread tells you whether the student is consistently good or just got lucky once.'),
    cv_anim(),
    real_world(
        scenario('Comparing models fairly',
                 p('With only 450 training students, two models can swap places depending on which 25 % lands in a single validation set. The placement team '
                   'compares candidate models by 5-fold CV mean and standard deviation, and only looks at the test set once, for the final choice.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score, cross_validate, KFold, StratifiedKFold, GroupKFold

            pipe = Pipeline([('pre', pre), ('model', LogisticRegression())])

            scores = cross_val_score(pipe, X_train, y_train, cv=StratifiedKFold(5, shuffle=True, random_state=0))
            print('fold accuracies:', scores.round(3))
            print(f'mean {scores.mean():.3f} ± std {scores.std():.3f}')

            res = cross_validate(pipe, X_train, y_train, cv=5, scoring=['accuracy', 'roc_auc', 'f1'], return_train_score=True)
            print(pd.DataFrame(res).drop(columns=['fit_time', 'score_time']).mean().round(3))

            # class balance per validation fold: plain KFold on sorted labels vs StratifiedKFold
            ys = y_train.sort_values()
            for cv in [KFold(5), StratifiedKFold(5)]:
                share = [round(float(ys.iloc[v].mean()), 2) for _, v in cv.split(ys.to_frame(), ys)]
                print(f'{type(cv).__name__:16} placed share per fold {share}')

            # GroupKFold: a centre never appears in both train and validation
            groups = X_train['centre']
            for tr, va in GroupKFold(n_splits=3).split(X_train, y_train, groups):
                print('validate on', sorted(groups.iloc[va].unique()), '| train on', sorted(groups.iloc[tr].unique()))
        """, setup=CLF, title=S),
        title='Example: Fold Scores, Several Metrics, Stratification and Groups'),
    steps(
        ('Wrap preprocessing + model in a Pipeline', 'So scaling/imputation are learned only from each training fold.'),
        ('Pick the splitter', 'Stratified for classes, Group for repeated entities, TimeSeries for time order.'),
        ('Run cross_validate', 'Several metrics, return_train_score=True to see the overfitting gap.'),
        ('Report mean ± std', 'A difference smaller than the std is probably noise.'),
        ('Keep the test set aside', 'Use it once, after model selection.'),
        title='Steps to Cross-Validate Properly'),
    crossq(
        ('What if you scale the data before cross-validation?', 'The scaler has seen the validation folds: leakage, usually a small optimistic bias, and much larger for steps like feature selection or target encoding.'),
        ('How many folds?', '5 or 10 is typical. More folds: less bias, more computation and higher variance per fold; use RepeatedStratifiedKFold for small data.'),
        ('Why not shuffle time-series data?', 'Shuffling lets the model train on the future and validate on the past, which is impossible in production; TimeSeriesSplit avoids it.'),
        ('Is the CV score the final performance estimate?', 'Not after you used it to choose hyperparameters; that choice makes it slightly optimistic. Use the untouched test set or nested CV.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('How do you tune hyperparameters with GridSearchCV and RandomizedSearchCV?', 'Hyperparameter Tuning', minutes=9, cards=[
    definition(
        defbox('<strong>Hyperparameters</strong> are settings chosen before training (max_depth, C, learning_rate), unlike <strong>parameters</strong> learned '
               'from data (coefficients, split thresholds). <strong>GridSearchCV</strong> tries every combination in a grid with cross-validation; '
               '<strong>RandomizedSearchCV</strong> samples <code>n_iter</code> combinations from lists or distributions (e.g. <code>loguniform</code>), which '
               'is far cheaper when there are many parameters.',
               'Parameters of pipeline steps are addressed as <code>step__param</code> (e.g. <code>model__max_depth</code>, '
               '<code>pre__num__simpleimputer__strategy</code>). After fitting, <code>best_params_</code>, <code>best_score_</code>, '
               '<code>cv_results_</code> and the refitted <code>best_estimator_</code> are available. Use <code>n_jobs=-1</code> to parallelise; '
               '<code>HalvingGridSearchCV</code> or Optuna for large spaces.'),
        tags('GridSearchCV', 'RandomizedSearchCV', 'best_params_', 'cv_results_', 'loguniform', 'step__param'),
    ),
    analogy('Tuning is like finding the best <strong>oven temperature and baking time</strong>. Grid search bakes a cake for every pair on a chart; random search '
            'bakes 20 cakes at random settings, which usually finds a great one with far fewer cakes when only one or two settings really matter.'),
    grid_anim(),
    real_world(
        scenario('Tuning without fooling yourself',
                 p('The placement team tunes a tree and a boosting model with 5-fold CV on the training data only. The best configuration is refitted on all '
                   'training students and evaluated once on the 150-student test set; that single number goes into the report.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.tree import DecisionTreeClassifier
            from sklearn.ensemble import HistGradientBoostingClassifier
            from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
            from scipy.stats import loguniform, randint

            pipe = Pipeline([('pre', pre), ('model', DecisionTreeClassifier(random_state=0))])
            grid = {'model__max_depth': [3, 5, 8, None], 'model__min_samples_leaf': [1, 5, 20]}
            gs = GridSearchCV(pipe, grid, cv=5, scoring='roc_auc', n_jobs=-1).fit(X_train, y_train)

            res = pd.DataFrame(gs.cv_results_)
            res['depth'] = [str(p['model__max_depth']) for p in gs.cv_results_['params']]
            table = res.pivot(index='depth', columns='param_model__min_samples_leaf', values='mean_test_score')
            table = table.loc[['3', '5', '8', 'None']]
            print(table.round(3))
            print('fits:', len(res) * 5, '| best:', gs.best_params_, f'CV AUC {gs.best_score_:.3f}')
            print(f'test AUC of refitted best tree {gs.score(X_test, y_test):.3f}')

            hgb = Pipeline([('pre', pre), ('model', HistGradientBoostingClassifier(random_state=0))])
            dist = {'model__learning_rate': loguniform(0.01, 0.3), 'model__max_leaf_nodes': randint(4, 32),
                    'model__l2_regularization': loguniform(1e-3, 10), 'model__max_iter': randint(50, 400)}
            rs = RandomizedSearchCV(hgb, dist, n_iter=20, cv=5, scoring='roc_auc', random_state=0, n_jobs=-1).fit(X_train, y_train)
            print('random search best:', {k.split('__')[1]: round(float(v), 3) for k, v in rs.best_params_.items()})
            print(f'CV AUC {rs.best_score_:.3f} | test AUC {rs.score(X_test, y_test):.3f}')
        """, setup=CLF, title=S),
        title='Example: Grid Search on a Tree, Random Search on Boosting'),
    steps(
        ('Build the full pipeline', 'Preprocessing inside, so each CV fold is clean.'),
        ('Define the space', 'Small grid for 1–2 parameters; distributions (log scale for rates and C) for more.'),
        ('Choose scoring', 'roc_auc, f1, neg_root_mean_squared_error… matching the business goal.'),
        ('Fit the search on training data', 'n_jobs=-1; inspect cv_results_, not only the best row.'),
        ('Evaluate best_estimator_ once on test', 'If the best value is at a grid edge, extend the grid.'),
        title='Steps to Tune a Model'),
    crossq(
        ('Why is random search often better than grid search?', 'Usually only a few parameters matter. A grid wastes fits repeating the same values of the important parameter; random sampling tries many distinct values of each.'),
        ('What is nested cross-validation?', 'An outer CV loop around the whole search, giving an unbiased estimate of "tune + train" performance; used when there is no separate test set.'),
        ('In the example the best tree scored 0.841 in CV but 0.789 on test. Why?', 'Picking the maximum of 12 noisy CV scores favours a lucky configuration (selection bias), and a 150-row test set is itself noisy. The boosting model, with a smoother score, held up (0.843 → 0.845).'),
        ('The best parameter is at the edge of the grid. What now?', 'Extend the grid in that direction; the true optimum may lie outside it.'),
        ('How do you tune the decision threshold?', 'It is not a model hyperparameter: pick it on validation predictions for the business metric, or use TunedThresholdClassifierCV (sklearn ≥ 1.5).'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('How do learning curves and validation curves diagnose underfitting and overfitting?', 'Learning & Validation Curves', minutes=8, cards=[
    definition(
        defbox('A <strong>learning curve</strong> (<code>learning_curve</code>) plots training and validation scores against the number of training rows. '
               'If both are low and close: <strong>underfitting</strong> (high bias) — more data will not help, a more flexible model will. If training is '
               'much higher than validation and validation is still rising: <strong>overfitting</strong> (high variance) — more data or regularisation helps.',
               'A <strong>validation curve</strong> (<code>validation_curve</code>) varies one hyperparameter (e.g. max_depth, C) and shows where validation '
               'score peaks: to the left the model underfits, to the right it overfits. Both functions use cross-validation internally and return arrays you can '
               'plot with matplotlib or <code>LearningCurveDisplay</code> / <code>ValidationCurveDisplay</code>.'),
        tags('learning_curve', 'validation_curve', 'bias', 'variance', 'underfitting', 'overfitting'),
    ),
    analogy('A learning curve is like tracking a student\'s <strong>practice and exam scores as they do more past papers</strong>. If both stay low, they need a '
            'better method, not more papers. If practice is perfect but exams lag, they are memorising answers and need varied practice.'),
    curves_anim(),
    real_world(
        scenario('"Should we collect another year of data?"',
                 p('Before paying for more data collection, the team draws a learning curve. If the validation score has already flattened at 450 students, another '
                   'year of data will add little; effort is better spent on new features such as assignment submission rates.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.tree import DecisionTreeClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import learning_curve, validation_curve

            for name, model in [('logistic', LogisticRegression()), ('deep tree', DecisionTreeClassifier(random_state=0))]:
                pipe = Pipeline([('pre', pre), ('model', model)])
                sizes, tr, va = learning_curve(pipe, X_train, y_train, cv=5, train_sizes=[0.1, 0.25, 0.5, 0.75, 1.0], scoring='accuracy')
                print(name)
                for n, a, b in zip(sizes, tr.mean(1), va.mean(1)):
                    print(f'  {n:4} rows  train {a:.3f}  validation {b:.3f}  gap {a - b:.3f}')

            pipe = Pipeline([('pre', pre), ('model', DecisionTreeClassifier(random_state=0))])
            depths = [1, 2, 3, 4, 6, 8, 12, 20]
            tr, va = validation_curve(pipe, X_train, y_train, param_name='model__max_depth', param_range=depths, cv=5, scoring='accuracy')
            print('max_depth  train  validation')
            for d, a, b in zip(depths, tr.mean(1), va.mean(1)):
                print(f'{d:9}  {a:.3f}  {b:.3f}' + ('   <- best' if d == depths[va.mean(1).argmax()] else ''))
        """, setup=CLF, title=S),
        title='Example: Learning Curves for Two Models and a Depth Validation Curve'),
    steps(
        ('Pick model and metric', 'Same pipeline you plan to deploy.'),
        ('learning_curve', 'train_sizes from 10 % to 100 %, cv=5.'),
        ('Read the gap', 'Large gap = variance; both low = bias.'),
        ('validation_curve', 'Sweep the main complexity parameter on a sensible (often log) scale.'),
        ('Act', 'More data/regularisation for variance; richer model/features for bias.'),
        title='Steps to Diagnose a Model with Curves'),
    crossq(
        ('Training accuracy is 1.000. Is that a problem?', 'Not by itself (forests often score 1.0 on training data); the validation score and the gap decide.'),
        ('How do you fix high bias?', 'Add features or interactions, use a more flexible model, reduce regularisation.'),
        ('How do you fix high variance?', 'More data, stronger regularisation, simpler model, fewer features, ensembles (bagging).'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('How do you measure feature importance? Compare impurity-based importance, permutation importance and feature selection.', 'Feature Importance', minutes=8, cards=[
    definition(
        defbox('Tree ensembles expose <code>feature_importances_</code>: the total impurity decrease from splits on each feature, computed on the '
               '<strong>training data</strong>. It is fast but biased towards features with many unique values (continuous or ID-like columns), even if they are '
               'useless. <strong>Permutation importance</strong> (<code>sklearn.inspection.permutation_importance</code>) shuffles one column at a time on '
               'held-out data and measures how much the score drops; it works for any model.',
               'For linear models, standardised coefficients show direction and size. <strong>Feature selection</strong> tools: <code>SelectKBest</code> '
               '(univariate tests), <code>RFE</code>/<code>RFECV</code> (recursive elimination), <code>SelectFromModel</code> (e.g. L1 or tree importances). '
               '<strong>SHAP</strong> values (separate library) explain individual predictions. Correlated features share (and can hide) importance.'),
        tags('feature_importances_', 'permutation_importance', 'SelectKBest', 'RFE', 'SelectFromModel', 'SHAP'),
    ),
    analogy('Impurity importance is asking players <strong>how much they touched the ball</strong>; permutation importance is <strong>benching one player and '
            'seeing how much the team\'s score drops</strong>. A busy player is not always a useful one.'),
    importance_anim(),
    real_world(
        scenario('Explaining the model to the academic council',
                 p('The council asks why the model flags a student. Permutation importance on the test set shows mock test and study hours drive the predictions; '
                   'a column like student_id, which looked important in the impurity ranking, turns out to have no real effect and is dropped.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.inspection import permutation_importance
            from sklearn.feature_selection import SelectKBest, f_classif, RFE
            from sklearn.linear_model import LogisticRegression

            rng = np.random.default_rng(0)
            feats = num + ['student_id']
            Xa = X_train[num].fillna(X_train[num].median()).assign(student_id=rng.permutation(len(X_train)))
            Xb = X_test[num].fillna(X_train[num].median()).assign(student_id=rng.permutation(len(X_test)))

            rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1).fit(Xa, y_train)
            perm = permutation_importance(rf, Xb, y_test, n_repeats=20, random_state=0, scoring='accuracy')
            out = pd.DataFrame({'impurity (train)': rf.feature_importances_, 'permutation (test)': perm.importances_mean,
                                'perm std': perm.importances_std}, index=feats)
            print(out.round(3).sort_values('permutation (test)', ascending=False))

            kb = SelectKBest(f_classif, k=2).fit(Xa, y_train)
            print('SelectKBest(k=2) keeps', list(Xa.columns[kb.get_support()]), '| F-scores', kb.scores_.round(1))
            rfe = RFE(make_pipeline(StandardScaler(), LogisticRegression()), n_features_to_select=3,
                      importance_getter='named_steps.logisticregression.coef_').fit(Xa, y_train)
            print('RFE ranking:', dict(zip(feats, rfe.ranking_.tolist())))
        """, setup=CLF, title=S),
        title='Example: Impurity vs Permutation Importance with a Useless ID Column'),
    steps(
        ('Fit the final model', 'Ideally the full pipeline.'),
        ('Compute permutation importance on held-out data', 'n_repeats ≥ 10, look at the std as well as the mean.'),
        ('Compare with impurity / coefficients', 'Disagreement points to cardinality bias or correlation.'),
        ('Check correlated groups', 'Permute correlated features together or drop one and re-check.'),
        ('Select and re-validate', 'Drop features only if CV performance does not fall.'),
        title='Steps to Analyse Feature Importance'),
    crossq(
        ('Why can permutation importance be negative?', 'Shuffling a useless feature can by chance slightly improve the score; values around zero (within the std) mean "no effect".'),
        ('Two features are highly correlated. What happens to their importances?', 'They share it: permuting one leaves the other carrying the information, so both can look unimportant though together they matter.'),
        ('Does importance mean causation?', 'No. It measures how much the model relies on a feature, not what happens if you change it in the real world.'),
        ('Should you select features before or inside cross-validation?', 'Inside (in the pipeline). Selecting on all data first leaks information and inflates scores.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('How do you save, load and serve a trained scikit-learn model? What can go wrong in production?', 'Saving & Deploying Models', minutes=8, cards=[
    definition(
        defbox('Persist the <strong>whole fitted Pipeline</strong> (preprocessing + model) with <code>joblib.dump(pipe, "model.joblib")</code> and restore it '
               'with <code>joblib.load</code>; then call <code>predict</code>/<code>predict_proba</code> on raw rows with the same columns. joblib is pickle '
               'with efficient storage of NumPy arrays (optional compression). <strong>skops.io</strong> offers a safer, inspectable format; ONNX allows '
               'serving outside Python.',
               'Pitfalls: pickles must be loaded with the <strong>same scikit-learn (and Python/NumPy) versions</strong>; <strong>never load untrusted '
               'files</strong> (unpickling can run arbitrary code); column names/order and categories must match (use <code>handle_unknown="ignore"</code>); '
               'store metadata (version, training date, metrics, threshold). In production, log predictions and monitor <strong>data drift</strong> and accuracy.'),
        tags('joblib', 'pickle', 'skops', 'ONNX', 'model versioning', 'data drift'),
    ),
    analogy('Saving a model is like <strong>vacuum-packing a cooked meal with its recipe card</strong>: the pipeline includes the sauce (preprocessing), and the card '
            'says which kitchen (library versions) can reheat it safely. And you never eat a sealed meal from a stranger: unpickling an unknown file can run code.'),
    persist_anim(),
    real_world(
        scenario('Nightly batch scoring',
                 p('Each night a scheduled job loads <code>placement_v1.joblib</code>, scores all current students from the database, writes probabilities and the '
                   'risk flag to a table that mentors see in a dashboard, and logs the input distribution. When the mean mock-test score of new batches drifts, the '
                   'team retrains.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            import joblib, json, os, sklearn
            from sklearn.linear_model import LogisticRegression

            pipe = Pipeline([('pre', pre), ('model', LogisticRegression())]).fit(X_train, y_train)
            joblib.dump(pipe, 'placement_v1.joblib', compress=3)
            meta = {'sklearn': sklearn.__version__, 'features': list(X_train.columns), 'threshold': 0.5,
                    'test_accuracy': round(pipe.score(X_test, y_test), 3)}
            with open('placement_v1.json', 'w') as f:
                json.dump(meta, f, indent=1)
            print('saved', os.path.getsize('placement_v1.joblib'), 'bytes ·', meta)

            # --- later, in the scoring job ---
            model = joblib.load('placement_v1.joblib')
            print('same predictions after reload:', (model.predict(X_test) == pipe.predict(X_test)).all())

            new = pd.DataFrame({'attendance': [92, 61], 'study_hours': [11.5, 3.0], 'mock_test': [np.nan, 48],
                                'course': ['PG-DBDA', 'PG-DAI'], 'centre': ['Nagpur', 'Pune'], 'degree': ['BE', 'BSc']})
            new['p_placed'] = model.predict_proba(new)[:, 1].round(3)
            print(new)

            # simple drift check: compare a new batch with the training distribution
            batch = X_test.assign(mock_test=X_test['mock_test'] - 8)
            for c in num:
                shift = (batch[c].mean() - X_train[c].mean()) / X_train[c].std()
                print(f'{c:12} shift {shift:+.2f} sd' + ('  <- drift' if abs(shift) > 0.3 else ''))
        """, setup=CLF, title=S),
        title='Example: Save with Metadata, Reload, Score Raw Rows, Check Drift'),
    steps(
        ('Fit the final pipeline', 'On all training data (or train + validation) with the chosen settings.'),
        ('Save model + metadata', 'joblib.dump plus a JSON with versions, features, metrics, threshold.'),
        ('Pin the environment', 'requirements.txt / Docker image with exact versions.'),
        ('Serve', 'Batch job (cron/Airflow) or API (FastAPI) calling predict_proba.'),
        ('Monitor and retrain', 'Log inputs and outcomes; alert on drift or falling accuracy.'),
        title='Steps to Deploy a Model'),
    crossq(
        ('Why save the pipeline and not just the model?', 'The model expects scaled, encoded columns. Without the fitted preprocessing, the serving code would have to re-implement it exactly, which is a common source of silent bugs.'),
        ('Is pickle safe?', 'Only for files you trust. A malicious pickle can execute code when loaded; use skops.io with trusted types for shared models.'),
        ('What is the difference between data drift and concept drift?', 'Data drift: input distributions change (new batches score lower on mocks). Concept drift: the relationship between inputs and outcome changes (the job market shifts).'),
        ('What does the model do with an unseen centre like "Nagpur"?', 'With OneHotEncoder(handle_unknown="ignore") all centre columns are 0, so it predicts from the other features instead of crashing.'),
    ),
]),
])
