from build import *
from mlq.anims import *
from mlq.runner import mlrun, pyshow
from mlq.data import STUDENTS, data_note

S = 'Python (scikit-learn) · uses sample data'
RUN_NOTE = note('Every example with an Output box was really executed while this page was built, with <strong>scikit-learn 1.9</strong>, pandas 3 and '
                'NumPy 2. Hidden lines: <code>import numpy as np</code>, <code>import pandas as pd</code> and display settings. The student data is '
                'synthetic (generated with a fixed seed, shown below) so results are reproducible; the iris, breast-cancer and diabetes datasets ship with scikit-learn.',
                'How the examples were run')

SECTION = dict(level='beginner', title='Machine Learning Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is machine learning? What are supervised, unsupervised and reinforcement learning? What is scikit-learn?', 'What is ML & scikit-learn', minutes=8, cards=[
    definition(
        defbox('<strong>Machine learning</strong> builds models that learn patterns from data instead of following hand-written rules. '
               '<strong>Supervised learning</strong> learns a mapping from features X to a known target y: <strong>regression</strong> for numbers, '
               '<strong>classification</strong> for categories. <strong>Unsupervised learning</strong> finds structure without labels: clustering, dimensionality '
               'reduction, anomaly detection. <strong>Reinforcement learning</strong> trains an agent through rewards.',
               '<strong>scikit-learn</strong> is the standard open-source Python library for classical ML on tabular data: preprocessing, regression, '
               'classification, clustering, model selection and pipelines, all with one consistent API, built on NumPy and SciPy.'),
        tags('machine learning', 'supervised', 'unsupervised', 'regression', 'classification', 'scikit-learn'),
    ),
    analogy('Teaching a child to recognise fruit: <strong>supervised</strong> is showing pictures with names ("this is a mango"); <strong>unsupervised</strong> is '
            'giving a basket and letting them sort similar fruit into piles; <strong>reinforcement</strong> is a game where they get a sweet for every right pick.'),
    ml_types_anim(),
    real_world(
        scenario('ML at C-DAC',
                 p('Regression: predict a student\'s final exam score from attendance, study hours and mock tests. Classification: flag students at risk of not '
                   'being placed early enough to help. Clustering: group students by learning pattern to plan remedial batches.')),
        scenario('Industry',
                 p('Credit scoring, churn prediction, demand forecasting, fraud detection and recommendation shortlists are mostly classical supervised models on '
                   'tables of data, which is exactly scikit-learn\'s territory; images, audio and text generation use deep learning (TensorFlow/PyTorch).')),
    ),
    example(
        RUN_NOTE,
        mlrun("""
            import sklearn
            from sklearn.datasets import load_iris
            from sklearn.model_selection import train_test_split
            from sklearn.tree import DecisionTreeClassifier

            X, y = load_iris(return_X_y=True)
            print(sklearn.__version__, X.shape, y.shape, np.unique(y))

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=0)
            model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
            print('predictions:', model.predict(X_test[:5]), 'actual:', y_test[:5])
            print('test accuracy:', round(model.score(X_test, y_test), 3))
        """),
        title='Example: A Complete Model in Eight Lines'),
    steps(
        ('Install', '<code>pip install scikit-learn pandas</code> (in a virtual environment).'),
        ('Get X and y', 'Features as a 2-D table, target as a 1-D array.'),
        ('Split', '<code>train_test_split</code>.'),
        ('Fit and predict', '<code>model.fit(X_train, y_train)</code>, <code>model.predict(X_test)</code>.'),
        ('Evaluate', 'A metric suited to the problem.'),
        title='Steps to Your First Model'),
    crossq(
        ('Is scikit-learn used for deep learning?', 'No; it has only a basic MLPClassifier. Deep learning uses PyTorch or TensorFlow/Keras, often with scikit-learn for preprocessing and evaluation.'),
        ('Regression or classification: predicting a grade A/B/C?', 'Classification (categories), though the grades are ordered; predicting the numeric mark would be regression.'),
        ('What is semi-supervised learning?', 'Learning from a few labelled and many unlabelled examples (e.g. sklearn\'s SelfTrainingClassifier, LabelSpreading).'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain the scikit-learn estimator API: fit, predict, transform, fit_transform and score.', 'Estimator API', minutes=7, cards=[
    definition(
        defbox('Every scikit-learn object is an <strong>estimator</strong> created with hyperparameters in its constructor and trained with '
               '<code>fit(X, y)</code>. <strong>Predictors</strong> (models) add <code>predict</code> (and often <code>predict_proba</code>, '
               '<code>decision_function</code>, <code>score</code>). <strong>Transformers</strong> (scalers, encoders, imputers, PCA) add '
               '<code>transform</code> and <code>fit_transform</code>.',
               'X is a 2-D array/DataFrame of shape (n_samples, n_features); y is 1-D (n_samples,). Attributes learned during fit end with an underscore '
               '(<code>coef_</code>, <code>mean_</code>, <code>classes_</code>); hyperparameters are read with <code>get_params()</code> and changed with '
               '<code>set_params()</code>.'),
        tags('fit', 'predict', 'transform', 'fit_transform', 'estimator', 'hyperparameters'),
    ),
    analogy('Every appliance in a kitchen has the same buttons: <strong>fit</strong> (learn the recipe), <strong>predict</strong> (cook a dish), '
            '<strong>transform</strong> (chop or blend ingredients). Once you know the buttons, you can use any appliance.'),
    estimator_anim(),
    real_world(
        scenario('Swapping algorithms painlessly',
                 p('A team compared logistic regression, random forest and gradient boosting for placement prediction by changing one line each; preprocessing, '
                   'evaluation and reporting code stayed identical because every model has fit/predict/score.')),
    ),
    example(
        data_note(),
        mlrun("""
            from sklearn.preprocessing import StandardScaler
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier

            X = df[['attendance', 'study_hours']].to_numpy()
            y = df['placed'].to_numpy()
            print(X.shape, y.shape)

            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)                       # fit + transform
            print('learned means:', scaler.mean_.round(2), '| scaled mean:', Xs.mean(axis=0).round(6) + 0)

            for model in [LogisticRegression(), RandomForestClassifier(n_estimators=50, random_state=0)]:
                model.fit(Xs, y)
                print(type(model).__name__, model.predict(Xs[:5]), 'train accuracy:', round(model.score(Xs, y), 3))

            lr = LogisticRegression(C=0.5)
            print(lr.get_params()['C'], lr.set_params(C=2.0).C, hasattr(lr, 'coef_'))
        """, setup=STUDENTS, title=S),
        title='Example: Transformer and Two Models with the Same Interface'),
    steps(
        ('Create', '<code>est = Algorithm(hyperparameters)</code>.'),
        ('Fit', '<code>est.fit(X_train, y_train)</code> (transformers may ignore y).'),
        ('Use', '<code>predict</code> for models, <code>transform</code> for transformers.'),
        ('Inspect', 'Learned attributes ending in <code>_</code>.'),
        ('Never fit on test data', 'Only <code>transform</code>/<code>predict</code> on it.'),
        title='Steps to Use Any Estimator'),
    crossq(
        ('fit_transform vs fit then transform?', 'Same result on the same data; fit_transform can be more efficient. On test data call only transform, never fit_transform.'),
        ('Why is the training accuracy of the random forest so high?', 'It is evaluated on the data it learned from; forests can nearly memorise training data. Only test/CV scores tell you about generalisation.'),
        ('Why must X be 2-D even for one feature?', 'The API always expects (n_samples, n_features); use X.reshape(-1, 1) or df[["col"]].'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('Why do we split data into training and test sets? What do random_state and stratify do?', 'Train/Test Split', minutes=7, cards=[
    definition(
        defbox('A model must be judged on data it has <strong>not</strong> seen during training; otherwise we measure memorisation, not generalisation. '
               '<code>train_test_split(X, y, test_size=0.2)</code> randomly holds back a <strong>test set</strong>, used once at the end. During development, '
               'compare and tune models on a <strong>validation set</strong> or with <strong>cross-validation</strong> on the training data.',
               '<code>random_state</code> fixes the shuffle so the split is reproducible. <code>stratify=y</code> keeps the class proportions identical in train '
               'and test, essential for imbalanced classes. Time-ordered data must be split by time; grouped data (several rows per student) by group.'),
        tags('train_test_split', 'test set', 'validation set', 'stratify', 'random_state'),
    ),
    analogy('A teacher who sets the exam using the <strong>exact questions from the practice sheet</strong> learns nothing about understanding. The test set is '
            'the <strong>unseen exam paper</strong>, locked in a cupboard until the end.'),
    split_anim(),
    real_world(
        scenario('Placement model review',
                 p('A model reported 96 % accuracy, measured on the training data. On a proper held-out set it scored 78 %. Since then every report shows the '
                   'stratified test-set score and the split\'s random_state, so anyone can reproduce it.')),
    ),
    example(
        data_note(),
        mlrun("""
            from sklearn.model_selection import train_test_split
            X = df.drop(columns=['placed', 'final_score'])
            y = df['placed']

            a = train_test_split(X, y, test_size=0.2, random_state=42)
            b = train_test_split(X, y, test_size=0.2, random_state=42)
            print('reproducible:', a[0].index.equals(b[0].index), '| sizes:', len(a[0]), len(a[1]))

            for strat in [None, y]:
                X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=7, stratify=strat)
                print('stratify' if strat is not None else 'random  ', 'train placed rate', round(y_tr.mean(), 3), '| test placed rate', round(y_te.mean(), 3))

            X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.3, random_state=1, stratify=y)
            X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.5, random_state=1, stratify=y_tmp)
            print('train/val/test:', len(X_tr), len(X_val), len(X_te))
        """, setup=STUDENTS, title=S),
        title='Example: Reproducible, Stratified and Three-way Splits'),
    steps(
        ('Split first', 'Before any fitting, scaling or feature selection.'),
        ('Choose the size', '20–30 % test for small data; less for very large data.'),
        ('Stratify classification targets', '<code>stratify=y</code>.'),
        ('Fix the seed', '<code>random_state</code>, and record it.'),
        ('Special structure', 'TimeSeriesSplit for time, GroupShuffleSplit/GroupKFold for repeated entities.'),
        title='Steps to Split Correctly'),
    crossq(
        ('Why not use the test set for tuning?', 'Every decision based on it leaks information; after enough tuning the test score becomes optimistic. Tune with validation/CV, test once.'),
        ('What if the dataset is small?', 'Use cross-validation for model selection and a test set (or nested CV) for the final estimate; a single small split is noisy.'),
        ('Does stratify work for regression?', 'Not directly; bin the target (e.g. pd.qcut) and stratify on the bins if needed.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What are overfitting and underfitting? Explain the bias-variance trade-off.', 'Overfitting & Bias-Variance', minutes=8, cards=[
    definition(
        defbox('<strong>Underfitting</strong>: the model is too simple to capture the real pattern: high error on both training and test data (high '
               '<strong>bias</strong>). <strong>Overfitting</strong>: the model fits noise in the training data: very low training error, much higher test error '
               '(high <strong>variance</strong>, i.e. it changes a lot with different training samples).',
               'Remedies for overfitting: simpler model, regularisation (C, alpha, max_depth, min_samples_leaf), more data, feature selection, ensembling, early '
               'stopping. For underfitting: more expressive model, better features, less regularisation. Diagnose with train vs validation scores and learning curves.'),
        tags('overfitting', 'underfitting', 'bias', 'variance', 'regularisation', 'generalisation'),
    ),
    analogy('An <strong>underfitting</strong> student learns only "the answer is usually C" and fails every exam. An <strong>overfitting</strong> student memorises '
            'last year\'s paper word for word and fails when the questions change. A good student learns the <strong>concepts</strong>.'),
    fit_anim(),
    real_world(
        scenario('Decision tree depth',
                 p('An unlimited-depth tree reached 100 % training accuracy on placement data and much lower test accuracy; limiting depth to 3–5 traded a little '
                   'training accuracy for better test accuracy. The example shows the same pattern with real numbers.')),
    ),
    example(
        data_note(),
        mlrun("""
            from sklearn.model_selection import train_test_split
            from sklearn.tree import DecisionTreeClassifier
            X = df[['attendance', 'study_hours']]
            y = df['placed']
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)

            print('depth   train   test   gap')
            for depth in [1, 2, 3, 5, 8, 12, None]:
                m = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_tr, y_tr)
                tr, te = m.score(X_tr, y_tr), m.score(X_te, y_te)
                print(f'{str(depth):>5}   {tr:.3f}   {te:.3f}   {tr - te:+.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: Train vs Test Accuracy as Tree Depth Grows'),
    steps(
        ('Compare train and validation scores', 'Both low → underfit; big gap → overfit.'),
        ('Adjust complexity', 'Depth, number of features, polynomial degree, regularisation strength.'),
        ('Add data or augment', 'More examples reduce variance.'),
        ('Use cross-validation', 'To compare settings reliably.'),
        ('Plot learning curves', 'To see whether more data would help.'),
        title='Steps to Diagnose Fit'),
    crossq(
        ('Can a model have high bias and high variance?', 'Yes, e.g. a poorly chosen model on tiny noisy data; but typically increasing complexity lowers bias and raises variance.'),
        ('How does regularisation reduce overfitting?', 'It penalises large or many parameters, forcing simpler functions that generalise better.'),
        ('Why is 100 % training accuracy a warning sign?', 'Real data contains noise; fitting it perfectly usually means memorising it.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('Walk through a complete machine-learning workflow, from problem definition to a deployed model.', 'End-to-End ML Workflow', minutes=9, cards=[
    definition(
        defbox('A typical supervised workflow: (1) <strong>define</strong> the target, the decision it supports and the success metric; (2) <strong>collect and '
               'explore</strong> data; (3) <strong>split</strong> off a test set; (4) <strong>prepare</strong> features (cleaning, imputation, encoding, scaling, '
               'feature engineering) inside a pipeline; (5) <strong>train</strong> baseline and candidate models and tune them with cross-validation; '
               '(6) <strong>evaluate</strong> once on the test set; (7) <strong>interpret</strong> errors and feature effects; (8) <strong>deploy</strong> the '
               'saved pipeline and <strong>monitor</strong> performance and data drift.',
               'Always compare with a <strong>baseline</strong> (e.g. DummyClassifier predicting the majority class) to know whether the model adds value.'),
        tags('ML workflow', 'baseline', 'DummyClassifier', 'pipeline', 'evaluation'),
    ),
    analogy('Building a model is like <strong>cooking for an event</strong>: decide the menu and who is coming (problem, metric), buy and clean ingredients (data), '
            'cook and taste in the kitchen (train, validate), serve to guests once (test), then watch whether people enjoy it (monitoring).'),
    workflow_anim(),
    real_world(
        scenario('At-risk student alerts',
                 p('Goal: by week 6, flag students unlikely to be placed so mentors can intervene. Metric: recall of at-risk students at acceptable precision. '
                   'Features available at week 6 only (attendance, hours, mock test, course). Baseline vs logistic regression vs boosting; the chosen pipeline is '
                   'saved and runs weekly, with accuracy checked against actual placements at batch end.')),
    ),
    example(
        data_note(),
        mlrun("""
            from sklearn.model_selection import train_test_split
            from sklearn.dummy import DummyClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import accuracy_score, recall_score

            features = ['attendance', 'study_hours', 'mock_test']
            data = df.dropna(subset=features)                                 # (imputation comes in section 2)
            X, y = data[features], data['placed']
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

            baseline = DummyClassifier(strategy='most_frequent').fit(X_tr, y_tr)
            model = make_pipeline(StandardScaler(), LogisticRegression()).fit(X_tr, y_tr)

            for name, m in [('baseline', baseline), ('logistic', model)]:
                pred = m.predict(X_te)
                print(f'{name:9} accuracy {accuracy_score(y_te, pred):.3f}   recall(placed) {recall_score(y_te, pred):.3f}')

            new = pd.DataFrame({'attendance': [95, 62], 'study_hours': [12, 3], 'mock_test': [82, 48]})
            print(model.predict_proba(new)[:, 1].round(2))
        """, setup=STUDENTS, title=S),
        title='Example: Baseline vs Model, Then Scoring New Students'),
    steps(
        ('Frame the problem', 'Target, prediction time, decision, metric.'),
        ('Explore the data', 'Types, missing values, target balance, leakage risks.'),
        ('Split, then build a pipeline', 'Preprocessing + model in one object.'),
        ('Baseline, then improve', 'DummyClassifier → simple model → complex models, tuned with CV.'),
        ('Test once, deploy, monitor', 'Save with joblib, re-evaluate as new outcomes arrive.'),
        title='Steps of a Real Project'),
    crossq(
        ('Why does the baseline have 0 recall?', 'It always predicts the majority class (not placed), so it never identifies a placed student: accuracy alone hides this.'),
        ('What is model drift?', 'Performance drops because the data or the relationship changes over time (new syllabus, different student intake); monitoring detects it.'),
        ('Where do most projects fail?', 'Unclear problem definitions, leakage, poor data quality and no monitoring, more often than algorithm choice.'),
    ),
]),
])
