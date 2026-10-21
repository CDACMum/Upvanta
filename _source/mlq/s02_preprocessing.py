from build import *
from mlq.anims import *
from mlq.runner import mlrun, pyshow
from mlq.data import STUDENTS, data_note

S = 'Python (scikit-learn) · uses sample data'
SPLIT = STUDENTS + """
from sklearn.model_selection import train_test_split
X = df.drop(columns=['placed', 'final_score'])
y = df['placed']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
"""
SPLIT_NOTE = note('These examples continue from the sample data with <code>X = df.drop(columns=["placed", "final_score"])</code>, <code>y = df["placed"]</code> '
                  'and <code>X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)</code>.', 'Data')

SECTION = dict(level='basic', title='Data Preprocessing & Pipelines', questions=[

# ------------------------------------------------------------------ 6
Q('Why and how do you scale features? Compare StandardScaler, MinMaxScaler and RobustScaler.', 'Feature Scaling', minutes=7, cards=[
    definition(
        defbox('Many algorithms are sensitive to feature ranges: <strong>distance-based</strong> (KNN, K-Means, SVM with RBF kernel), <strong>gradient-based and '
               'regularised</strong> models (logistic/linear regression with penalties, neural networks) and <strong>PCA</strong>. Scaling puts features on '
               'comparable scales. Tree-based models do not need it.'),
        table(['Scaler', 'Formula', 'Use when'], [
            ['StandardScaler', '(x − mean) / std', 'default choice; roughly symmetric features'],
            ['MinMaxScaler', '(x − min) / (max − min) → [0, 1]', 'bounded inputs (images, neural nets); sensitive to outliers'],
            ['RobustScaler', '(x − median) / IQR', 'features with outliers'],
            ['MaxAbsScaler', 'x / max|x|', 'sparse data (keeps zeros)'],
        ]),
        tags('StandardScaler', 'MinMaxScaler', 'RobustScaler', 'scaling', 'normalisation'),
    ),
    analogy('Comparing students by <strong>height in centimetres and weight in tonnes</strong> makes height dominate every distance. Scaling converts both to '
            '"how unusual is this value", so neither wins just because of its unit.'),
    scaling_anim(),
    real_world(
        scenario('KNN recommending study groups',
                 p('How much scaling matters depends on the data. In the example, attendance and study hours have spreads of the same order, so KNN accuracy barely '
                   'changes; on the wine dataset, where one feature reaches 1680 and another stays near 1, the large feature dominates every distance until the data '
                   'is standardised, and accuracy jumps. Scaling is cheap insurance, so it is the default for distance-based models.')),
    ),
    example(
        SPLIT_NOTE,
        mlrun("""
            from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
            from sklearn.neighbors import KNeighborsClassifier
            num = ['attendance', 'study_hours']
            Xtr, Xte = X_train[num], X_test[num]

            for scaler in [StandardScaler(), MinMaxScaler(), RobustScaler()]:
                t = scaler.fit(Xtr).transform(Xte)                 # fit on TRAIN, apply to test
                print(f'{type(scaler).__name__:15} test min {t.min(axis=0).round(2)} max {t.max(axis=0).round(2)}')

            knn = KNeighborsClassifier(n_neighbors=15)
            raw = knn.fit(Xtr, y_train).score(Xte, y_test)
            sc = StandardScaler().fit(Xtr)
            scaled = knn.fit(sc.transform(Xtr), y_train).score(sc.transform(Xte), y_test)
            print(f'students KNN accuracy raw {raw:.3f} vs scaled {scaled:.3f}   (std of features: {Xtr.std().round(1).tolist()})')

            from sklearn.datasets import load_wine
            from sklearn.model_selection import train_test_split
            from sklearn.pipeline import make_pipeline
            Xw, yw = load_wine(return_X_y=True, as_frame=True)
            print('wine feature ranges:', Xw.max().round(1).sort_values().iloc[[0, -1]].to_dict())
            a, b, c, d = train_test_split(Xw, yw, random_state=0, stratify=yw)
            print(f'wine KNN accuracy raw {KNeighborsClassifier().fit(a, c).score(b, d):.3f} vs scaled '
                  f'{make_pipeline(StandardScaler(), KNeighborsClassifier()).fit(a, c).score(b, d):.3f}')
        """, setup=SPLIT, title=S),
        title='Example: Three Scalers; KNN With and Without Scaling on Two Datasets'),
    steps(
        ('Decide if needed', 'Distance/gradient/PCA models: yes; trees: no.'),
        ('Pick a scaler', 'Standard by default, Robust with outliers, MinMax for bounded ranges.'),
        ('Fit on training data only', 'Then transform validation/test/new data.'),
        ('Put it in a Pipeline', 'So cross-validation and deployment apply it correctly.'),
        title='Steps to Scale Features'),
    crossq(
        ('Why can scaled test values fall outside 0–1 with MinMaxScaler?', 'The min/max were learned from training data; test values beyond that range map outside [0, 1]. That is expected (clip=True can bound them).'),
        ('Normalisation vs standardisation?', 'Usually "normalisation" means min-max scaling to a range, "standardisation" means zero mean and unit variance; sklearn\'s Normalizer instead scales each ROW to unit length.'),
        ('Do you scale the target?', 'Rarely needed for linear models; sometimes helpful for neural nets (TransformedTargetRegressor handles it cleanly).'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('How do you encode categorical variables? OneHotEncoder vs OrdinalEncoder vs LabelEncoder.', 'Encoding Categories', minutes=7, cards=[
    definition(
        defbox('<strong>OneHotEncoder</strong> creates one binary column per category: right for nominal features (course, centre). Options: '
               '<code>handle_unknown="ignore"</code> (or <code>"infrequent_if_exist"</code>), <code>drop="first"</code> for linear models without '
               'regularisation, <code>min_frequency</code>/<code>max_categories</code> to group rare values, <code>sparse_output</code>.',
               '<strong>OrdinalEncoder</strong> maps categories to integers in a given order: for ordered features (grade C &lt; B &lt; A) or for tree models. '
               '<strong>LabelEncoder</strong> is meant for the <strong>target</strong> y, not for features. <code>pd.get_dummies</code> works for quick analysis '
               'but does not remember categories for new data.'),
        tags('OneHotEncoder', 'OrdinalEncoder', 'LabelEncoder', 'categorical', 'get_dummies'),
    ),
    analogy('One-hot encoding is a <strong>row of separate light switches</strong>, one per course, with exactly one on. Ordinal encoding is a <strong>dimmer '
            'knob</strong>: fine for levels that really are ordered, misleading for things that are not.'),
    encoding_anim(),
    real_world(
        scenario('New centre added',
                 p('A pipeline trained when only Kharghar, Juhu and Pune existed crashed when the first student from a new centre arrived. With '
                   '<code>handle_unknown="ignore"</code> the unknown centre becomes all zeros and prediction continues.')),
    ),
    example(
        SPLIT_NOTE,
        mlrun("""
            from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, LabelEncoder
            ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False).fit(X_train[['course', 'centre']])
            print(ohe.get_feature_names_out())
            print(ohe.transform(pd.DataFrame({'course': ['PG-DAI'], 'centre': ['Bengaluru']})))     # unknown centre

            grades = pd.DataFrame({'grade': ['B', 'A', 'C', 'A']})
            ordinal = OrdinalEncoder(categories=[['C', 'B', 'A']])
            print(ordinal.fit_transform(grades).ravel())

            le = LabelEncoder().fit(['not placed', 'placed', 'placed'])
            print(le.classes_, le.transform(['placed', 'not placed']))

            strict = OneHotEncoder().fit(X_train[['centre']])
            try:
                strict.transform(pd.DataFrame({'centre': ['Bengaluru']}))
            except ValueError as e:
                print('ValueError:', str(e)[:70])
        """, setup=SPLIT, title=S),
        title='Example: One-hot with Unknown Categories, Ordinal Order, LabelEncoder for y'),
    steps(
        ('Classify each categorical column', 'Nominal → one-hot; ordered → ordinal with explicit categories.'),
        ('Plan for unseen values', '<code>handle_unknown="ignore"</code> or an "Other" bucket.'),
        ('Limit width', '<code>min_frequency</code>/<code>max_categories</code> for many levels.'),
        ('Use inside a ColumnTransformer', 'Encoders learn categories from training data.'),
        title='Steps to Encode Categories'),
    crossq(
        ('Why drop="first" sometimes?', 'For plain linear regression, k one-hot columns plus an intercept are perfectly collinear (dummy variable trap); regularised models and trees do not need it.'),
        ('Why not use pd.get_dummies in production?', 'It encodes whatever categories appear in the data passed in, so train and new data can end up with different columns.'),
        ('What is target encoding?', 'Replacing a category with a smoothed mean of the target for that category (sklearn TargetEncoder, using internal cross-fitting to avoid leakage); useful for many categories.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('How do you handle missing values in scikit-learn? SimpleImputer, KNNImputer and missing indicators.', 'Imputation', minutes=7, cards=[
    definition(
        defbox('Most estimators reject NaN. <strong>SimpleImputer</strong> fills with the mean, median, most frequent value or a constant, learned on training '
               'data. <strong>KNNImputer</strong> uses the k most similar rows; <strong>IterativeImputer</strong> (experimental) models each feature from the others. '
               '<code>add_indicator=True</code> (or MissingIndicator) adds "was missing" flags, useful when missingness itself is informative.',
               'Some models accept NaN directly: HistGradientBoosting, and decision trees/random forests in recent versions. Dropping rows is acceptable only '
               'when few rows are affected and missingness is random.'),
        tags('SimpleImputer', 'KNNImputer', 'missing values', 'add_indicator', 'NaN'),
    ),
    analogy('Filling a missing mock-test mark with the <strong>class median</strong> is like a teacher estimating an absent student\'s mark from the class; '
            'KNN imputation estimates it from the <strong>five most similar students</strong>; the indicator writes "absent" in the margin so nobody forgets.'),
    impute_anim(),
    real_world(
        scenario('Mock test not taken',
                 p('Students who skipped the mock test were less likely to be placed. Median imputation alone hid that signal; adding a missing indicator let the '
                   'model use it.')),
    ),
    example(
        SPLIT_NOTE,
        mlrun("""
            from sklearn.impute import SimpleImputer, KNNImputer
            print(X_train.isna().sum()[lambda s: s > 0])

            num = ['attendance', 'study_hours', 'mock_test']
            imp = SimpleImputer(strategy='median', add_indicator=True).fit(X_train[num])
            print('learned medians:', imp.statistics_, '| output columns:', imp.get_feature_names_out())
            print(imp.transform(X_test[num])[X_test['mock_test'].isna().to_numpy()][:2])

            cat = SimpleImputer(strategy='most_frequent').fit(X_train[['degree']])
            print('degree fill value:', cat.statistics_)

            knn = KNNImputer(n_neighbors=5).fit(X_train[num])
            row = X_test[num][X_test['mock_test'].isna()].head(1)
            print('KNN estimate for', row.to_dict('records'), '→', knn.transform(row).round(1))
        """, setup=SPLIT, title=S),
        title='Example: Median + Indicator, Most Frequent, KNN Estimate'),
    steps(
        ('Measure', '<code>X.isna().mean()</code> per column; ask why values are missing.'),
        ('Choose a strategy', 'Median for skewed numbers, most_frequent/constant for categories, KNN when similar rows exist.'),
        ('Keep the signal', '<code>add_indicator=True</code>.'),
        ('Fit on training data only', 'Inside a Pipeline.'),
        ('Or use NaN-aware models', 'HistGradientBoosting handles missing values natively.'),
        title='Steps to Impute'),
    crossq(
        ('Why median instead of mean?', 'Median is robust to skew and outliers; one extreme value does not move it.'),
        ('Can imputing before the split leak information?', 'Yes, the fill values would be computed using test rows; impute inside the pipeline after splitting.'),
        ('When should a column with missing values be dropped?', 'When most values are missing and they carry no signal, or when it cannot be known at prediction time.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('What are Pipeline and ColumnTransformer? Why should preprocessing live inside a pipeline?', 'Pipeline & ColumnTransformer', minutes=9, cards=[
    definition(
        defbox('A <strong>Pipeline</strong> chains transformers and a final estimator into one estimator: <code>fit</code> fits each step in order on the training '
               'data, <code>predict</code> pushes new data through the same steps. A <strong>ColumnTransformer</strong> applies different transformations to '
               'different columns (numeric vs categorical) and concatenates the results.',
               'Benefits: no leakage in cross-validation, one object to tune (<code>step__param</code> names in GridSearchCV), one object to save and deploy, '
               'raw DataFrames in, predictions out. <code>make_pipeline</code>/<code>make_column_transformer</code> name steps automatically; '
               '<code>set_output(transform="pandas")</code> keeps DataFrame outputs.'),
        tags('Pipeline', 'ColumnTransformer', 'make_pipeline', 'leakage', 'deployment'),
    ),
    analogy('A pipeline is a <strong>factory assembly line</strong> sealed in one box: raw material goes in one end, a finished product comes out the other, and '
            'the line is set up from the training batch, then reused unchanged for every new batch.'),
    pipeline_anim(),
    real_world(
        scenario('One artefact for production',
                 p('The placement model is saved as a single pipeline file. The weekly scoring job loads it and calls <code>predict_proba</code> on the raw export: '
                   'no copy of preprocessing code that could drift from training.')),
    ),
    example(
        SPLIT_NOTE,
        mlrun("""
            from sklearn.pipeline import Pipeline
            from sklearn.compose import ColumnTransformer
            from sklearn.impute import SimpleImputer
            from sklearn.preprocessing import StandardScaler, OneHotEncoder
            from sklearn.linear_model import LogisticRegression

            num = ['attendance', 'study_hours', 'mock_test']
            cat = ['course', 'centre', 'degree']
            pre = ColumnTransformer([
                ('num', Pipeline([('impute', SimpleImputer(strategy='median')), ('scale', StandardScaler())]), num),
                ('cat', Pipeline([('impute', SimpleImputer(strategy='most_frequent')),
                                  ('onehot', OneHotEncoder(handle_unknown='ignore'))]), cat),
            ])
            pipe = Pipeline([('pre', pre), ('model', LogisticRegression(max_iter=1000))])
            pipe.fit(X_train, y_train)

            print('test accuracy:', round(pipe.score(X_test, y_test), 3))
            print(len(pipe.named_steps['pre'].get_feature_names_out()), 'features after preprocessing')
            print(list(pipe.named_steps['pre'].get_feature_names_out()[:5]))
            raw = pd.DataFrame([{'course': 'PG-DBDA', 'centre': 'Juhu', 'degree': None,
                                 'attendance': 91, 'study_hours': 10, 'mock_test': None}])
            print('P(placed) for a raw new row:', pipe.predict_proba(raw)[0, 1].round(3))
            print([k for k in pipe.get_params() if k.startswith('model__C') or k.startswith('pre__num__impute__strategy')])
        """, setup=SPLIT, title=S),
        title='Example: Raw Mixed Data → One Pipeline → Predictions'),
    steps(
        ('Group columns', 'Numeric, categorical, (text, dates…).'),
        ('Build per-group pipelines', 'Impute → scale; impute → encode.'),
        ('Combine with ColumnTransformer', 'Then add the model as the last step.'),
        ('Fit and evaluate the whole pipeline', 'Use it in cross_val_score / GridSearchCV.'),
        ('Save the pipeline', 'Not just the model.'),
        title='Steps to Build a Pipeline'),
    crossq(
        ('How do you tune a parameter inside a pipeline?', 'Use step names with double underscores: {"model__C": [0.1, 1, 10], "pre__num__impute__strategy": ["mean", "median"]}.'),
        ('What does remainder="passthrough" do?', 'Columns not listed in any transformer are passed through unchanged (default "drop" removes them).'),
        ('Why did the new row with missing values still work?', 'The pipeline\'s imputers filled them with values learned from the training data before scaling, encoding and predicting.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What is data leakage? Give examples and show how to prevent it.', 'Data Leakage', minutes=8, cards=[
    definition(
        defbox('<strong>Data leakage</strong> is when information that would not be available at prediction time (or that comes from the evaluation data) is used '
               'during training, producing over-optimistic scores that do not hold in production.',
               'Common forms: <strong>preprocessing leakage</strong> (scaling, imputation or feature selection fitted on all data before splitting/CV); '
               '<strong>target leakage</strong> (features derived from or recorded after the outcome); <strong>train-test contamination</strong> (duplicates or the '
               'same entity in both); <strong>temporal leakage</strong> (future data predicting the past). Prevention: split first, keep all fitting inside a '
               'Pipeline, audit each feature\'s timing, and use group/time-aware splits.'),
        tags('data leakage', 'target leakage', 'Pipeline', 'cross-validation', 'feature selection'),
    ),
    analogy('Leakage is a student who has <strong>seen the answer key</strong>: the practice scores are brilliant, and the real exam goes badly.'),
    leakage_anim(),
    real_world(
        scenario('Feature selection on all data',
                 p('With many random features, selecting the "best" ones using all rows and then cross-validating gives impressive scores even when the target is '
                   'pure noise. Doing the selection inside the pipeline reveals the truth: about 50 %, a coin toss. The example reproduces this classic trap.')),
    ),
    example(
        mlrun("""
            from sklearn.feature_selection import SelectKBest, f_classif
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score
            from sklearn.pipeline import make_pipeline

            rng = np.random.default_rng(0)
            X = rng.normal(size=(200, 5000))          # 5000 random features
            y = rng.integers(0, 2, 200)               # random target: nothing to learn

            X_selected = SelectKBest(f_classif, k=20).fit_transform(X, y)      # WRONG: uses all rows
            leaky = cross_val_score(LogisticRegression(max_iter=1000), X_selected, y, cv=5).mean()

            pipe = make_pipeline(SelectKBest(f_classif, k=20), LogisticRegression(max_iter=1000))
            honest = cross_val_score(pipe, X, y, cv=5).mean()                  # RIGHT: inside each fold
            print(f'leaky CV accuracy : {leaky:.3f}')
            print(f'honest CV accuracy: {honest:.3f}  (random target → ~0.5 expected)')
        """),
        data_note(),
        mlrun("""
            from sklearn.model_selection import train_test_split
            from sklearn.ensemble import RandomForestClassifier
            cols_ok = ['attendance', 'study_hours']
            cols_leak = cols_ok + ['final_score']          # final exam is AFTER the mid-course prediction
            for cols in [cols_ok, cols_leak]:
                X_tr, X_te, y_tr, y_te = train_test_split(df[cols], df['placed'], test_size=0.25, random_state=0, stratify=df['placed'])
                acc = RandomForestClassifier(random_state=0).fit(X_tr, y_tr).score(X_te, y_te)
                print(f'{len(cols)} features {cols[-1]:12} test accuracy {acc:.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: Feature-selection Leakage on Noise, and a Target-leakage Feature'),
    steps(
        ('Split before anything learns', 'Test set aside first.'),
        ('Put every fitted step in a Pipeline', 'Imputers, scalers, encoders, selectors, resamplers.'),
        ('Audit features', 'Would this value exist at the moment of prediction?'),
        ('Match the split to the data', 'GroupKFold for repeated entities, TimeSeriesSplit for time.'),
        ('Be suspicious of great scores', 'Check feature importances for "too good" features.'),
        title='Steps to Prevent Leakage'),
    crossq(
        ('Why did final_score raise accuracy?', 'It is strongly related to placement but is only known at the end of the course; at mid-course prediction time it does not exist, so the higher score is not achievable in practice.'),
        ('Is fitting a scaler on all data really harmful?', 'The effect is often small for scaling but large for feature selection, target encoding, oversampling and imputation; the rule is the same for all: fit inside the training folds.'),
        ('How do you detect leakage after deployment?', 'A large gap between offline evaluation and live performance; investigate the most important features first.'),
    ),
]),
])
