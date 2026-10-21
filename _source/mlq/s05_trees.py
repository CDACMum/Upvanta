from build import *
from mlq.anims import *
from mlq.runner import mlrun, pyshow
from mlq.s04_classification import CLF, CLF_NOTE

S = 'Python (scikit-learn) · uses sample data'

SECTION = dict(level='intermediate', title='Trees, Ensembles & SVM', questions=[

# ------------------------------------------------------------------ 21
Q('How does a decision tree work? What are Gini impurity and entropy? How do you control overfitting?', 'Decision Trees', minutes=8, cards=[
    definition(
        defbox('A <strong>decision tree</strong> recursively splits the data with yes/no questions on single features (e.g. mock_test ≤ 68.5), choosing at each node '
               'the split that makes the child nodes as <strong>pure</strong> as possible. Impurity measures: <strong>Gini</strong> = 1 − Σpᵢ² (default) and '
               '<strong>entropy</strong> = −Σpᵢ log₂ pᵢ (information gain). Regression trees minimise squared error. Leaves predict the majority class (or mean).',
               'Unrestricted trees memorise the training data. Control complexity with <code>max_depth</code>, <code>min_samples_leaf</code>, '
               '<code>min_samples_split</code>, <code>max_leaf_nodes</code>, or cost-complexity pruning (<code>ccp_alpha</code>). Trees need no scaling and capture '
               'interactions, but a single tree is unstable.'),
        tags('DecisionTreeClassifier', 'Gini', 'entropy', 'max_depth', 'pruning', 'export_text'),
    ),
    analogy('A tree is the <strong>"20 questions" game</strong>: each question is chosen to rule out as much as possible, until the answer is clear. Asking too '
            'many very specific questions just memorises the examples you practised on.'),
    tree_anim(),
    real_world(
        scenario('Rules a coordinator can read',
                 p('A depth-2 or depth-3 tree turns placement data into rules such as "mock test above 68.5 and more than 7 study hours per week → '
                   'likely placed", easy to explain in a faculty meeting and to act on.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.tree import DecisionTreeClassifier, export_text
            Xn = X_train[num].fillna(X_train[num].median())
            tree = DecisionTreeClassifier(max_depth=2, random_state=0).fit(Xn, y_train)
            print(export_text(tree, feature_names=num, show_weights=True))

            p = y_train.mean()
            print('root Gini = 1 - p² - (1-p)² =', round(1 - p**2 - (1 - p)**2, 3), '| tree says', round(tree.tree_.impurity[0], 3))

            Xt = X_test[num].fillna(X_train[num].median())
            for kw in [dict(), dict(max_depth=3), dict(min_samples_leaf=20), dict(ccp_alpha=0.005)]:
                t = DecisionTreeClassifier(random_state=0, **kw).fit(Xn, y_train)
                print(f'{str(kw):24} leaves {t.get_n_leaves():3}  train {t.score(Xn, y_train):.3f}  test {t.score(Xt, y_test):.3f}')
        """, setup=CLF, title=S),
        title='Example: Readable Rules, Gini at the Root, and Four Ways to Limit a Tree'),
    steps(
        ('Start shallow', '<code>max_depth=3</code> to read the rules with export_text/plot_tree.'),
        ('Limit complexity', 'Tune max_depth, min_samples_leaf or ccp_alpha with CV.'),
        ('Check stability', 'Refit on different samples; if rules change a lot, use an ensemble.'),
        ('Inspect importances', 'Prefer permutation importance on test data.'),
        title='Steps to Build a Useful Tree'),
    crossq(
        ('Gini vs entropy?', 'Both measure impurity and usually give very similar trees; Gini is slightly faster (no logarithm).'),
        ('Why do trees not need feature scaling?', 'Splits compare one feature to a threshold; any monotonic rescaling gives the same splits.'),
        ('Can a tree extrapolate?', 'No: predictions are constants per leaf, so a regression tree cannot predict beyond the range of training targets.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What is a random forest? How do bagging, max_features and out-of-bag scores work?', 'Random Forest', minutes=8, cards=[
    definition(
        defbox('A <strong>random forest</strong> is an ensemble of decision trees, each trained on a <strong>bootstrap sample</strong> of the rows (bagging) and '
               'considering only a random subset of features at each split (<code>max_features</code>, default √n for classification). Predictions are majority '
               'votes (or averaged probabilities); for regression, averages.',
               'Averaging many decorrelated, high-variance trees reduces variance, so forests are accurate and robust with little tuning. Rows not drawn for a tree '
               '("out-of-bag") give a free validation estimate (<code>oob_score=True</code>). Key parameters: <code>n_estimators</code> (more = more stable), '
               '<code>max_depth</code>/<code>min_samples_leaf</code>, <code>max_features</code>, <code>class_weight</code>, <code>n_jobs=-1</code>.'),
        tags('RandomForestClassifier', 'bagging', 'bootstrap', 'max_features', 'OOB score'),
    ),
    analogy('Instead of trusting one expert, ask <strong>200 experts who each studied a different random sample</strong> of past cases and looked at different '
            'clues, then take a vote. Individual experts make odd mistakes; the crowd is reliably good.'),
    forest_anim(),
    real_world(
        scenario('A dependable default',
                 p('For the placement data, a random forest with default settings beat a single tree without careful tuning, and its OOB score agreed with the '
                   'test score, giving confidence without spending data on an extra validation set.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.tree import DecisionTreeClassifier
            Xn = X_train[num].fillna(X_train[num].median()); Xt = X_test[num].fillna(X_train[num].median())

            tree = DecisionTreeClassifier(random_state=0).fit(Xn, y_train)
            print(f'single tree      test {tree.score(Xt, y_test):.3f}')
            for n in [10, 100, 300]:
                rf = RandomForestClassifier(n_estimators=n, min_samples_leaf=5, oob_score=True, n_jobs=-1, random_state=0).fit(Xn, y_train)
                print(f'forest {n:3} trees test {rf.score(Xt, y_test):.3f}   OOB {rf.oob_score_:.3f}')
            print(pd.Series(rf.feature_importances_, index=num).round(3).sort_values(ascending=False))
            print('trees disagree on', int(((np.array([t.predict(Xt.to_numpy()) for t in rf.estimators_]).mean(0)) % 1 != 0).sum()), 'of', len(Xt), 'test students')
        """, setup=CLF, title=S),
        title='Example: Tree vs Forests of Growing Size, OOB Score, Importances'),
    steps(
        ('Start with defaults', '<code>RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=0)</code>.'),
        ('Check OOB vs CV', 'oob_score=True for a quick estimate.'),
        ('Tune lightly', 'min_samples_leaf, max_features, max_depth.'),
        ('Imbalance', 'class_weight="balanced" or "balanced_subsample".'),
        ('Explain', 'Permutation importance, partial dependence plots.'),
        title='Steps to Use a Random Forest'),
    crossq(
        ('Can adding more trees overfit?', 'No; more trees only reduce the variance of the average. Overfitting comes from each tree being too deep, controlled by depth/leaf size.'),
        ('Why random feature subsets?', 'Without them, strong features would dominate every tree, making trees similar; averaging similar trees reduces variance much less.'),
        ('Forest vs gradient boosting?', 'Forests are robust and easy; boosting usually reaches higher accuracy on tabular data but needs more tuning (learning rate, iterations).'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How does gradient boosting work? When would you use HistGradientBoosting, XGBoost or LightGBM?', 'Gradient Boosting', minutes=9, cards=[
    definition(
        defbox('<strong>Gradient boosting</strong> builds an additive model of shallow trees <strong>sequentially</strong>: each new tree is fitted to the negative '
               'gradient of the loss (for squared error, simply the residuals) of the current ensemble, and added with a shrinkage factor '
               '(<code>learning_rate</code>). Many small corrections produce a strong model.',
               'scikit-learn\'s <strong>HistGradientBoostingClassifier/Regressor</strong> bins features into histograms: fast on large data, native missing-value and '
               'categorical support, early stopping. <strong>XGBoost</strong>, <strong>LightGBM</strong> and <strong>CatBoost</strong> are popular libraries with '
               'the same idea and sklearn-compatible APIs. Key knobs: learning_rate × number of iterations, tree size (max_depth / max_leaf_nodes), regularisation, '
               'early stopping.'),
        tags('gradient boosting', 'HistGradientBoosting', 'XGBoost', 'LightGBM', 'learning_rate', 'early stopping'),
    ),
    analogy('Boosting is a <strong>team of proof-readers in a row</strong>: the first fixes the obvious mistakes, each next one looks only at what is still wrong, '
            'and each is allowed to change only a little (learning rate) so nobody over-corrects.'),
    boosting_anim(),
    real_world(
        scenario('Tabular competitions and industry',
                 p('Gradient-boosted trees dominate tabular prediction: credit risk, churn, demand forecasting. For the placement data, HistGradientBoosting handles '
                   'missing mock-test scores and categorical courses natively, with no imputation or one-hot encoding needed.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.ensemble import HistGradientBoostingClassifier
            from sklearn.metrics import roc_auc_score
            Xc_train = X_train.astype({c: 'category' for c in cat}); Xc_test = X_test.astype({c: 'category' for c in cat})
            print('missing values passed straight in:', int(Xc_train.isna().sum().sum()))

            for lr, it in [(1.0, 20), (0.1, 100), (0.05, 300)]:
                m = HistGradientBoostingClassifier(learning_rate=lr, max_iter=it, max_depth=3, categorical_features='from_dtype',
                                                   random_state=0).fit(Xc_train, y_train)
                print(f'learning_rate {lr:<5} iterations {it:3}  test acc {m.score(Xc_test, y_test):.3f}  AUC {roc_auc_score(y_test, m.predict_proba(Xc_test)[:, 1]):.3f}')

            es = HistGradientBoostingClassifier(learning_rate=0.1, max_iter=1000, early_stopping=True, validation_fraction=0.2,
                                                n_iter_no_change=20, categorical_features='from_dtype', random_state=0).fit(Xc_train, y_train)
            print('early stopping used', es.n_iter_, 'of 1000 iterations; test acc', round(es.score(Xc_test, y_test), 3))
        """, setup=CLF, title=S),
        title='Example: Native NaN and Categories, Learning Rate vs Iterations, Early Stopping'),
    steps(
        ('Start with HistGradientBoosting', 'Defaults are strong; pass categoricals as category dtype.'),
        ('Use early stopping', 'Let max_iter be large; stop on validation loss.'),
        ('Tune', 'learning_rate (0.03–0.2), max_depth/max_leaf_nodes, l2_regularization, min_samples_leaf.'),
        ('Compare with CV', 'Against logistic regression and random forest baselines.'),
        ('Explain', 'Permutation importance, SHAP.'),
        title='Steps to Use Gradient Boosting'),
    crossq(
        ('Why a small learning rate?', 'Small steps generalise better (each tree corrects only part of the error) but need more trees; early stopping finds the right number.'),
        ('Bagging vs boosting in one line?', 'Bagging trains independent models in parallel to reduce variance; boosting trains dependent models sequentially to reduce bias.'),
        ('Is boosting sensitive to noisy labels?', 'More than forests: later trees can chase noise, which is why shrinkage, subsampling and early stopping matter.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How does a Support Vector Machine work? What do C, kernel and gamma control?', 'Support Vector Machines', minutes=8, cards=[
    definition(
        defbox('A <strong>Support Vector Machine</strong> finds the boundary (hyperplane) that separates classes with the <strong>maximum margin</strong>; only the '
               'closest points, the <strong>support vectors</strong>, define it. A <strong>soft margin</strong> allows some violations, controlled by <code>C</code> '
               '(large C: fewer violations, narrower margin, risk of overfitting; small C: wider margin, more regularisation).',
               'The <strong>kernel trick</strong> computes similarities in a higher-dimensional space without building it: <code>"linear"</code>, <code>"rbf"</code> '
               '(default, <code>gamma</code> sets how far each point\'s influence reaches; large gamma → wiggly boundary), <code>"poly"</code>. SVMs need scaled '
               'features and scale poorly beyond tens of thousands of rows (use LinearSVC or SGDClassifier for big linear problems).'),
        tags('SVC', 'kernel', 'C', 'gamma', 'support vectors', 'margin'),
    ),
    analogy('Drawing the <strong>widest road</strong> between two villages: the houses closest to the road (support vectors) decide where it goes; houses far away '
            'do not matter. A kernel lets the road curve around hills.'),
    svm_anim(),
    real_world(
        scenario('Medium-sized, high-dimensional data',
                 p('SVMs shine on clean, medium-sized datasets with many features, such as classifying short texts or sensor signatures; for large tabular data, '
                   'boosting is usually faster and more accurate.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.svm import SVC
            from sklearn.model_selection import cross_val_score
            print('C       gamma   CV acc   support vectors')
            for C, gamma in [(0.1, 'scale'), (1, 'scale'), (10, 'scale'), (1, 0.01), (1, 1.0), (100, 1.0)]:
                pipe = Pipeline([('pre', pre), ('svm', SVC(C=C, gamma=gamma))])
                acc = cross_val_score(pipe, X_train, y_train, cv=5).mean()
                n_sv = pipe.fit(X_train, y_train).named_steps['svm'].n_support_.sum()
                print(f'{C:<6} {str(gamma):<7} {acc:.3f}    {n_sv}')
            lin = Pipeline([('pre', pre), ('svm', SVC(kernel='linear', C=1))])
            print('linear kernel CV acc', round(cross_val_score(lin, X_train, y_train, cv=5).mean(), 3))
        """, setup=CLF, title=S),
        title='Example: Effect of C and gamma, Number of Support Vectors'),
    steps(
        ('Scale features', 'StandardScaler in a pipeline (essential).'),
        ('Start with RBF', 'Default C=1, gamma="scale".'),
        ('Tune C and gamma together', 'Log-scale grid, e.g. C in [0.1, 1, 10, 100], gamma in [0.001 … 1].'),
        ('Large data?', 'LinearSVC / SGDClassifier, or switch model family.'),
        ('Need probabilities?', 'probability=True (slower) or CalibratedClassifierCV.'),
        title='Steps to Use an SVM'),
    crossq(
        ('Why does a larger C often mean fewer support vectors?', 'Violations become expensive, so the margin narrows and fewer points lie on or inside it.'),
        ('What does very large gamma do?', 'Each point influences only its immediate neighbourhood, so the boundary wraps tightly around training points: overfitting.'),
        ('SVM vs logistic regression?', 'Both are linear classifiers in their basic form; SVM optimises the margin (hinge loss) and does not output probabilities natively; logistic regression is probabilistic and easier to explain.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What are ensemble methods? Compare bagging, boosting, voting and stacking.', 'Ensembles: Voting & Stacking', minutes=8, cards=[
    definition(
        defbox('<strong>Ensembles</strong> combine several models to get better accuracy or stability than any single one. <strong>Bagging</strong> trains the same '
               'model on bootstrap samples in parallel and averages (reduces variance; random forest). <strong>Boosting</strong> trains models sequentially, each '
               'correcting earlier errors (reduces bias; gradient boosting, AdaBoost). <strong>Voting</strong> combines different models by majority (hard) or by '
               'averaging probabilities (soft). <strong>Stacking</strong> trains a meta-model on out-of-fold predictions of the base models.',
               'They work best when members are individually good and make <strong>different</strong> errors.'),
        tags('ensemble', 'bagging', 'boosting', 'VotingClassifier', 'StackingClassifier'),
    ),
    analogy('A selection panel for admissions: one interviewer can be biased; a <strong>panel vote</strong> is fairer (voting), and a <strong>chairperson who '
            'knows which interviewer is reliable for which kind of candidate</strong> is stacking.'),
    ensemble_anim(),
    real_world(
        scenario('Squeezing the last few points',
                 p('Final production models are often a soft-voting or stacking blend of a linear model and a boosted model: the linear model is smooth and '
                   'robust, the trees capture interactions. Gains are usually modest, so the extra complexity must be worth it.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, VotingClassifier, StackingClassifier
            from sklearn.neighbors import KNeighborsClassifier
            from sklearn.model_selection import cross_val_score

            base = [('lr', LogisticRegression(max_iter=1000)),
                    ('rf', RandomForestClassifier(n_estimators=200, min_samples_leaf=5, random_state=0)),
                    ('knn', KNeighborsClassifier(n_neighbors=31))]
            models = dict(base)
            models['soft voting'] = VotingClassifier(base, voting='soft')
            models['stacking'] = StackingClassifier(base, final_estimator=LogisticRegression(), cv=5)

            for name, m in models.items():
                pipe = Pipeline([('pre', pre), ('m', m)])
                s = cross_val_score(pipe, X_train, y_train, cv=5, scoring='roc_auc')
                print(f'{name:12} CV AUC {s.mean():.3f} ± {s.std():.3f}')
        """, setup=CLF, title=S),
        title='Example: Three Base Models vs Soft Voting vs Stacking'),
    steps(
        ('Build diverse strong models', 'Different families (linear, trees, neighbours).'),
        ('Check their error correlation', 'Similar models add little.'),
        ('Try soft voting first', 'Simple, no extra training.'),
        ('Stacking for more', 'Meta-model on out-of-fold predictions (StackingClassifier does this).'),
        ('Compare with CV', 'Keep the ensemble only if the gain justifies the complexity.'),
        title='Steps to Build an Ensemble'),
    crossq(
        ('Why use out-of-fold predictions in stacking?', 'If the meta-model learned from predictions made on the base models\' own training data, it would trust overfitted outputs; out-of-fold predictions mimic unseen data.'),
        ('Hard vs soft voting?', 'Hard counts predicted labels; soft averages probabilities, which uses confidence and usually works better if models are calibrated.'),
        ('When is an ensemble a bad idea?', 'When explainability, latency or maintenance cost matter more than a small accuracy gain.'),
    ),
]),
])
