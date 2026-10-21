from build import *


def _lines(x, y, lines, color='#e2e8f0', size=11, step=None, gap=16):
    return ''.join(stext(x, y + i * gap, ln, color, size, 'start', step=step).replace('<text ', '<text xml:space="preserve" ', 1)
                   for i, ln in enumerate(lines))


def _codebox(x, y, w, h, lines, color='gray', step=None, tcolor='#e2e8f0', size=11, focus=None):
    return sbox(x, y, w, h, '', '', color, step=step, fill_opacity=0.08, focus=focus) + _lines(x + 14, y + 22, lines, tcolor, size, step=step)


def _row(items, y, x0=20, w=130, gap=14, h=56, size=12, arrows=True):
    out = []
    for i, (t, s, c, st) in enumerate(items):
        x = x0 + i * (w + gap)
        out.append(sbox(x, y, w, h, t, s, c, step=st, size=size))
        if arrows and i:
            out.append(sarrow(x - gap, y + h / 2, x - 2, y + h / 2, 'gray', step=st))
    return ''.join(out)


def _dot(x, y, color, step=None, r=5, focus=None):
    c = PALETTE.get(color, color)
    a = f' data-step="{step}"' if step else ''
    f = f' data-focus="{focus}"' if focus else ''
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"{a}{f}/>'


def _axes(x, y, w, h, xl='', yl='', step=None):
    return (sarrow(x, y + h, x + w, y + h, 'gray', step=step) + sarrow(x, y + h, x, y, 'gray', step=step)
            + stext(x + w / 2, y + h + 18, xl, 'gray', 11, step=step) + stext(x - 12, y - 6, yl, 'gray', 11, anchor='start', step=step))


# ============================================================ section 1
def ml_types_anim():
    elems = [
        stext(380, 24, 'Three kinds of machine learning', 'blue', 15, bold=True),
        sbox(20, 55, 230, 120, 'Supervised', 'learn X → y from labelled examples\n\nregression: final_score (number)\nclassification: placed? (yes/no)', 'green', step=1, size=12, top=True),
        sbox(265, 55, 230, 120, 'Unsupervised', 'no labels: find structure\n\nclustering: student segments\nPCA: compress features', 'purple', step=2, size=12, top=True),
        sbox(510, 55, 230, 120, 'Reinforcement', 'agent learns from rewards\n\ngames, robotics, recommendations\n(not in scikit-learn)', 'amber', step=3, size=12, top=True),
        stext(380, 205, 'traditional program: rules + data → answers   ·   ML: data + answers → rules (a model)', 'cyan', 13, step=4, bold=True, focus=4),
        stext(380, 235, 'scikit-learn: classic ML on tabular data (not deep learning) · one consistent API for 100+ algorithms', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        '<strong>Supervised</strong> learning uses examples with known answers (labels): predict a number (regression) or a category (classification).',
        '<strong>Unsupervised</strong> learning has no labels: it finds groups (clustering) or simpler representations (dimensionality reduction).',
        '<strong>Reinforcement</strong> learning trains an agent by trial, error and reward; scikit-learn does not cover it.',
        'The key shift: instead of writing rules, you give data plus answers and the algorithm learns the rules.',
        'scikit-learn is the standard Python library for classical machine learning on tables of data.',
    ])


def estimator_anim():
    elems = [
        stext(380, 24, 'The estimator API: the same three verbs everywhere', 'blue', 15, bold=True),
        stable(20, 55, ['attendance', 'hours', 'mock'], [['92.0', '11.5', '81'], ['61.4', '4.2', '52'], ['78.3', '8.0', '66']], [80, 60, 55], step=1, title='X (n_samples × n_features)', title_color='blue'),
        stable(230, 55, ['placed'], [['1'], ['0'], ['?']], [70], step=1, title='y', title_color='purple'),
        sbox(330, 55, 190, 50, 'model.fit(X, y)', 'learn parameters', 'green', step=2, size=13),
        sbox(330, 115, 190, 50, 'model.predict(X_new)', 'labels / numbers', 'amber', step=3, size=13),
        sbox(540, 55, 200, 50, 'scaler.fit_transform(X)', 'transformers change X', 'purple', step=4, size=12),
        sbox(540, 115, 200, 50, 'model.score(X, y)', 'default metric', 'cyan', step=5, size=12),
        stext(380, 200, 'learned values end with _ : model.coef_, scaler.mean_, tree.feature_importances_', 'gray', 12, step=2),
        stext(380, 225, 'swap LogisticRegression() for RandomForestClassifier(): the rest of the code stays the same', 'amber', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Data is a 2-D feature matrix X (rows = samples, columns = features) and a target vector y.',
        '<code>fit</code> learns the parameters from training data; learned attributes get a trailing underscore.',
        '<code>predict</code> applies the learned model to new rows.',
        'Transformers (scalers, encoders, imputers) use <code>fit</code> + <code>transform</code> to change the data instead of predicting.',
        '<code>score</code> gives a default metric. Because every estimator shares this API, algorithms are interchangeable.',
    ])


def split_anim():
    elems = [stext(380, 24, 'Train/test split: never grade a model on what it studied', 'blue', 15, bold=True)]
    for i in range(20):
        test = i in (2, 7, 11, 15, 18)
        col = '#f59e0b' if test else '#10b981'
        elems.append(scell(20 + i * 36, 60, 34, 34, '', '#334155', step=1))
        elems.append(scell(20 + i * 36, 60, 34, 34, 'T' if test else '', col, '#fff', step=2, bold=True))
    elems += [
        stext(200, 120, 'train 80 % → fit', 'green', 13, step=2, bold=True),
        stext(560, 120, 'test 20 % → evaluate once', 'amber', 13, step=2, bold=True),
        _codebox(20, 140, 720, 58, ['X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,',
                                     '                                                    random_state=42, stratify=y)'], 'gray', step=3),
        stext(380, 225, 'random_state → same split every run · stratify=y → same class ratio in both parts', 'purple', 12, step=4),
        stext(380, 250, 'time series: split by time (train on past, test on future), never shuffle', 'red', 12, step=5),
    ]
    return anim(canvas(760, 268, *elems), [
        'The full labelled dataset.',
        'A random 20 % is held back as the test set; the model only ever learns from the other 80 %.',
        '<code>train_test_split</code> does this in one call.',
        'Fix <code>random_state</code> for reproducible results and use <code>stratify=y</code> so rare classes appear in both parts.',
        'For time-ordered data the test set must come after the training period.',
    ])


def fit_anim():
    import math
    pts = [(40, 160), (80, 140), (120, 150), (160, 115), (200, 120), (240, 95), (280, 100), (320, 70)]
    def poly(x0, color, kind, step):
        d = ''
        for k in range(41):
            x = k * 8
            if kind == 'under':
                y = 130
            elif kind == 'good':
                y = 162 - 0.27 * x
            else:
                y = 162 - 0.27 * x + 18 * math.sin(x / 13)
            d += ('M' if k == 0 else 'L') + f' {x0 + 30 + x * 0.6:.1f} {y + 30:.1f} '
        return f'<path d="{d}" stroke="{PALETTE[color]}" stroke-width="2.5" fill="none" data-step="{step}"/>'
    elems = [stext(380, 24, 'Underfitting · good fit · overfitting', 'blue', 15, bold=True)]
    for j, (title, kind, color, step) in enumerate([('underfit (too simple)', 'under', 'red', 2), ('good fit', 'good', 'green', 3), ('overfit (memorises noise)', 'over', 'amber', 4)]):
        x0 = 10 + j * 250
        elems.append(stext(x0 + 120, 52, title, color, 12, step=step, bold=True))
        for (x, y) in pts:
            elems.append(_dot(x0 + 30 + x * 0.6, y + 30, 'blue', step=1))
        elems.append(poly(x0, color, kind, step))
    elems += [
        stext(380, 245, 'train error high, test error high → add features / more complex model', 'red', 11, step=2),
        stext(380, 265, 'train error tiny, test error high → simplify, regularise, more data, cross-validate', 'amber', 11, step=4),
        stext(380, 285, 'bias-variance trade-off: too simple = high bias · too flexible = high variance', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 300, *elems), [
        'Data points with a roughly linear trend plus noise.',
        '<strong>Underfitting</strong>: the model is too simple to capture the trend; it is wrong on training and test data alike.',
        'A <strong>good fit</strong> captures the trend and ignores the noise, so it generalises to new data.',
        '<strong>Overfitting</strong>: the model follows the noise of the training points; training error is tiny but new data is predicted badly.',
        'This is the bias-variance trade-off; model complexity, regularisation and data size move you along it.',
    ])


def workflow_anim():
    elems = [stext(380, 24, 'A complete supervised-learning workflow', 'blue', 15, bold=True),
             _row([('1 define', 'target, metric', 'gray', 1), ('2 data', 'load, explore', 'blue', 2), ('3 split', 'train / test', 'purple', 3),
                   ('4 prepare', 'impute, encode,\nscale (fit on train)', 'amber', 4), ('5 train', 'fit, tune with CV', 'green', 5)], 60, w=130, gap=17, h=64, size=12),
             _row([('6 evaluate', 'test set, once', 'red', 6), ('7 interpret', 'errors, importance', 'cyan', 7), ('8 deploy', 'save pipeline,\npredict, monitor', 'pink', 8)], 160, x0=110, w=165, gap=20, h=64, size=12),
             stext(380, 260, 'most of the effort goes into steps 1–4; the algorithm is often the easiest part', 'amber', 12, step=8, focus=8)]
    return anim(canvas(760, 280, *elems), [
        'Define what to predict and how success is measured (e.g. recall of at-risk students).',
        'Collect and explore the data: types, missing values, distributions, target balance.',
        'Hold out a test set before doing anything that learns from data.',
        'Prepare features (imputation, encoding, scaling), fitting these steps on training data only.',
        'Train candidate models and tune them with cross-validation on the training data.',
        'Evaluate the chosen model once on the untouched test set.',
        'Look at errors and important features: does the model make sense?',
        'Save the whole pipeline, use it for predictions, and monitor it over time.',
    ])


# ============================================================ section 2
def scaling_anim():
    elems = [
        stext(380, 24, 'Feature scaling: put features on comparable ranges', 'blue', 15, bold=True),
        stable(20, 55, ['attendance', 'study_hours'], [['92', '11.5'], ['61', '4.2'], ['78', '8.0'], ['100', '25.7']], [90, 90], step=1, title='raw: 55–100 vs 1–26', title_color='red'),
        stable(250, 55, ['attendance', 'study_hours'], [['1.17', '0.67'], ['-1.23', '-1.03'], ['0.09', '-0.15'], ['1.79', '3.97']], [90, 90], step=2,
               title='StandardScaler: mean 0, std 1', title_color='green'),
        stable(480, 55, ['attendance', 'study_hours'], [['0.82', '0.43'], ['0.13', '0.13'], ['0.52', '0.29'], ['1.00', '1.00']], [90, 90], step=3,
               title='MinMaxScaler: 0 to 1', title_color='purple'),
        stext(380, 210, 'needed for distance/gradient models: KNN, SVM, logistic/linear with regularisation, K-Means, PCA, neural nets', 'amber', 12, step=4),
        stext(380, 235, 'not needed for trees and forests · RobustScaler uses median/IQR when there are outliers', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'Raw features have very different ranges; distance- and gradient-based models would be dominated by the larger one.',
        'StandardScaler subtracts the training mean and divides by the training standard deviation.',
        'MinMaxScaler maps each feature to 0–1 using the training minimum and maximum (sensitive to outliers).',
        'Scaling matters for models that use distances or gradients.',
        'Tree models split on thresholds and ignore scale; RobustScaler resists outliers.',
    ])


def encoding_anim():
    elems = [
        stext(380, 24, 'Encoding categories as numbers', 'blue', 15, bold=True),
        stable(20, 55, ['course'], [['PG-DBDA'], ['PG-DAC'], ['PG-DAI'], ['PG-DBDA']], [100], step=1, title='raw text', title_color='gray'),
        stable(150, 55, ['DAC', 'DAI', 'DBDA'], [['0', '0', '1'], ['1', '0', '0'], ['0', '1', '0'], ['0', '0', '1']], [55, 55, 55], step=2, title='OneHotEncoder', title_color='green'),
        stable(350, 55, ['course_code'], [['2'], ['0'], ['1'], ['2']], [100], step=3, title='OrdinalEncoder', title_color='amber'),
        _codebox(480, 55, 260, 110, ["OneHotEncoder(handle_unknown='ignore')", '  → nominal categories', "OrdinalEncoder(categories=[['C','B','A']])",
                                     '  → ordered grades'], 'gray', step=4, tcolor='#e2e8f0'),
        stext(380, 220, 'ordinal codes on nominal data invent an order (DAC < DAI < DBDA) that linear models will believe', 'red', 12, step=3),
        stext(380, 245, 'many categories (e.g. 500 colleges) → min_frequency / max_categories, target encoding, or tree models', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 262, *elems), [
        'Models need numbers, but course is text.',
        'One-hot encoding creates one 0/1 column per category: no fake order.',
        'Ordinal encoding maps categories to integers: right for ordered data, misleading for unordered data.',
        'Set handle_unknown so a new category at prediction time does not crash the model; give explicit order for ordinal features.',
        'High-cardinality features need grouping of rare values or other encodings.',
    ])


def impute_anim():
    elems = [
        stext(380, 24, 'Imputing missing values', 'blue', 15, bold=True),
        stable(20, 55, ['mock_test', 'degree'], [['81', 'BE'], ['NaN', 'BSc'], ['66', 'NaN'], ['52', 'BE']], [90, 80], step=1, title='raw', title_color='red',
               focus_rows={1: '1', 2: '1'}),
        stable(230, 55, ['mock_test', 'degree'], [['81', 'BE'], ['65.0', 'BSc'], ['66', 'BE'], ['52', 'BE']], [90, 80], step=2, title="SimpleImputer(median / most_frequent)", title_color='green'),
        sbox(440, 55, 300, 50, 'KNNImputer', 'fill from the 5 most similar students', 'purple', step=3, size=12),
        sbox(440, 115, 300, 50, 'add_indicator=True', 'extra 0/1 column "was missing"', 'amber', step=4, size=12),
        stext(380, 210, 'imputation statistics are LEARNED from the training data (fit) and reused for test data (transform)', 'cyan', 12, step=5, focus=5),
        stext(380, 235, 'HistGradientBoosting handles NaN natively; most other estimators raise an error on NaN', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'Some mock-test scores and degrees are missing.',
        'SimpleImputer fills numbers with the training median (or mean) and categories with the most frequent value.',
        'KNNImputer estimates a missing value from similar rows.',
        'An indicator column lets the model learn whether "missing" itself is informative.',
        'Like every transformer, imputers learn from training data only.',
    ])


def pipeline_anim():
    elems = [
        stext(380, 24, 'ColumnTransformer + Pipeline: one object from raw rows to predictions', 'blue', 15, bold=True),
        sbox(20, 60, 140, 120, 'raw DataFrame', 'course, centre,\ndegree,\nattendance,\nhours, mock', 'gray', step=1, size=12),
        sarrow(160, 95, 208, 80, 'gray', step=2), sarrow(160, 145, 208, 160, 'gray', step=2),
        sbox(210, 55, 220, 55, 'numeric', 'SimpleImputer → StandardScaler', 'blue', step=2, size=12),
        sbox(210, 135, 220, 55, 'categorical', 'SimpleImputer → OneHotEncoder', 'purple', step=2, size=12),
        sarrow(430, 82, 478, 115, 'gray', step=3), sarrow(430, 162, 478, 125, 'gray', step=3),
        sbox(480, 95, 120, 50, 'model', 'LogisticRegression', 'green', step=3, size=11),
        sarrow(600, 120, 638, 120, 'gray', step=3),
        sbox(640, 95, 100, 50, 'predict', 'placed?', 'amber', step=3, size=12),
        stext(380, 225, 'pipe.fit(X_train, y_train): every step fitted on training data only → no leakage', 'green', 12, step=4, bold=True),
        stext(380, 250, 'pipe.predict(raw_new_rows) · GridSearchCV(pipe, …) tunes preprocessing and model together · joblib.dump(pipe)', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 268, *elems), [
        'Real data mixes numeric and categorical columns, with missing values.',
        'A ColumnTransformer sends each group of columns through its own preprocessing pipeline.',
        'The transformed features feed the model; the whole chain is one Pipeline object.',
        'Fitting the pipeline fits each step on the training data in order, which prevents data leakage automatically.',
        'The same object predicts on raw new rows, can be tuned as a unit and saved to disk.',
    ])


def leakage_anim():
    elems = [
        stext(380, 24, 'Data leakage: information from the answer sneaks into training', 'blue', 15, bold=True),
        sbox(20, 55, 350, 70, 'leaky preprocessing', 'scaler.fit(ALL data) → then split\ntest statistics influenced training', 'red', step=1, size=12),
        sbox(390, 55, 350, 70, 'leaky feature', "'final_score' used to predict 'placed'\nknown only AFTER the event", 'red', step=2, size=12),
        sbox(20, 140, 350, 70, 'duplicates across split', 'same student in train and test\n(or time leakage: future → past)', 'red', step=3, size=12),
        sbox(390, 140, 350, 70, 'symptom', 'suspiciously high test score\n(99 %) that collapses in production', 'amber', step=4, size=12, focus=4),
        stext(380, 240, 'cure: split first · Pipeline for all preprocessing · ask "would I know this at prediction time?" · group/time splits', 'green', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 258, *elems), [
        'Fitting a scaler, imputer or feature selector on all data before splitting leaks test-set statistics into training.',
        'Features that are only known after the outcome (final exam score when predicting placement at mid-course) leak the answer.',
        'The same entity in both train and test, or future information in training, inflates scores.',
        'The tell-tale sign is a model that looks too good to be true and fails on real new data.',
        'Prevention: split before any fitting, keep preprocessing inside a Pipeline, check every feature\'s availability at prediction time, and use group- or time-aware splits.',
    ])


# ============================================================ section 3
def linreg_anim():
    pts = [(60, 52), (90, 60), (120, 57), (150, 70), (180, 66), (210, 78), (240, 74), (270, 86), (300, 84)]
    elems = [stext(380, 24, 'Linear regression: the best straight line (least squares)', 'blue', 15, bold=True),
             _axes(40, 50, 330, 190, 'study hours', 'final score', step=1)]
    for (x, y) in pts:
        elems.append(_dot(40 + x, 240 - (y - 40) * 2.2, 'blue', step=1))
    elems.append(f'<path d="M 70 {240 - (49 - 40) * 2.2} L 360 {240 - (91 - 40) * 2.2}" stroke="#10b981" stroke-width="2.5" data-step="2"/>')
    for (x, y) in pts[::2]:
        yl = 49 + (x - 30) * (91 - 49) / 290
        elems.append(f'<path d="M {40 + x} {240 - (y - 40) * 2.2} L {40 + x} {240 - (yl - 40) * 2.2}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="3,3" data-step="3"/>')
    elems += [
        _codebox(400, 50, 340, 120, ['ŷ = b₀ + b₁·hours + b₂·attendance + …', '', 'model.intercept_  → b₀', 'model.coef_       → [b₁, b₂, …]',
                                     'fit = minimise Σ (y − ŷ)²'], 'green', step=2, tcolor='#86efac'),
        stext(570, 200, 'red dashes = residuals (errors)', 'red', 12, step=3),
        stext(570, 225, 'b₁ = 1.6 → each extra weekly hour adds', 'amber', 12, step=4),
        stext(570, 245, '≈1.6 marks, other features held fixed', 'amber', 12, step=4),
        stext(380, 275, 'fast, interpretable, a strong baseline · assumes a roughly linear, additive relationship', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'Each point is a student: study hours vs final score.',
        'Linear regression fits ŷ = intercept + coefficients × features.',
        'It chooses the coefficients that minimise the sum of squared residuals (vertical distances).',
        'Each coefficient is the expected change in the target per unit change in that feature, holding the others fixed.',
        'Simple and interpretable, a good baseline, but limited to linear additive relationships unless you engineer features.',
    ])


def reg_metrics_anim():
    elems = [
        stext(380, 24, 'Regression metrics', 'blue', 15, bold=True),
        stable(20, 55, ['actual', 'predicted', 'error'], [['72', '70', '+2'], ['58', '63', '-5'], ['85', '84', '+1'], ['64', '56', '+8']], [80, 90, 70], step=1, title='errors', title_color='blue'),
        sbox(290, 55, 220, 52, 'MAE = mean |error|', '(2+5+1+8)/4 = 4.0 marks', 'green', step=2, size=12),
        sbox(290, 117, 220, 52, 'RMSE = √mean(error²)', '√(94/4) = 4.85 · punishes big misses', 'amber', step=3, size=12),
        sbox(520, 55, 220, 52, 'R² = 1 − SSres/SStot', 'share of variance explained', 'purple', step=4, size=12),
        sbox(520, 117, 220, 52, 'MAPE', 'mean % error (avoid near 0)', 'gray', step=4, size=12),
        stext(380, 210, 'MAE/RMSE are in the target\'s units (marks) → easy to explain; R² ≤ 1, can be negative on test data', 'cyan', 12, step=5),
        stext(380, 235, 'compare with a baseline that always predicts the mean (R² = 0)', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'Each prediction has an error (actual − predicted).',
        'MAE averages absolute errors: "on average we are 4 marks off".',
        'RMSE squares errors first, so large misses count more; always ≥ MAE.',
        'R² compares the model with always predicting the mean: 1 is perfect, 0 is no better than the mean.',
        'Report errors in the target\'s units for stakeholders, and compare against a baseline.',
    ])


def regularization_anim():
    feats = ['hours', 'mock', 'attend', 'noise1', 'noise2']
    ols = [5.0, 4.6, 3.8, 1.4, -1.2]
    ridge = [4.2, 3.9, 3.2, 0.6, -0.5]
    lasso = [4.4, 4.0, 3.1, 0.0, 0.0]
    elems = [stext(380, 24, 'Regularisation shrinks coefficients', 'blue', 15, bold=True)]
    for j, (name, vals, color, step) in enumerate([('LinearRegression', ols, 'gray', 1), ('Ridge (L2)', ridge, 'blue', 2), ('Lasso (L1)', lasso, 'green', 3)]):
        x0 = 20 + j * 245
        elems.append(stext(x0 + 110, 55, name, color, 13, step=step, bold=True))
        elems.append(f'<line x1="{x0}" y1="150" x2="{x0 + 220}" y2="150" stroke="#475569" data-step="{step}"/>')
        for i, v in enumerate(vals):
            h = abs(v) * 15
            y = 150 - h if v > 0 else 150
            if v != 0:
                elems.append(f'<rect x="{x0 + 10 + i * 42}" y="{y}" width="30" height="{h}" fill="{PALETTE[color]}" data-step="{step}"/>')
            else:
                elems.append(stext(x0 + 25 + i * 42, 146, '0', 'green', 12, step=step, bold=True))
            elems.append(stext(x0 + 25 + i * 42, 190, feats[i], 'gray', 9, step=step))
    elems += [
        stext(380, 220, 'loss = errors² + α·Σβ² (Ridge) or + α·Σ|β| (Lasso) · bigger α → stronger shrinkage', 'amber', 12, step=4),
        stext(380, 245, 'Lasso sets weak coefficients exactly to 0 (feature selection) · ElasticNet mixes both · scale features first', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 262, *elems), [
        'Ordinary least squares gives every feature a coefficient, including noise features, which hurts generalisation.',
        'Ridge (L2) adds a penalty on squared coefficients: all shrink towards zero, none reach exactly zero.',
        'Lasso (L1) penalises absolute values: weak features are set exactly to zero, giving automatic feature selection.',
        'The strength α is a hyperparameter chosen by cross-validation (RidgeCV, LassoCV).',
        'ElasticNet combines both penalties; because penalties compare coefficient sizes, features must be scaled.',
    ])


def poly_anim():
    import math
    elems = [stext(380, 24, 'Capturing curves: polynomial features in a linear model', 'blue', 15, bold=True),
             _axes(40, 50, 300, 180, 'x', 'y', step=1)]
    pts = [(i * 28 + 20, 150 - 0.012 * (i * 28 - 130) ** 2 + (7 if i % 2 else -6)) for i in range(10)]
    for (x, y) in pts:
        elems.append(_dot(40 + x, 230 - y, 'blue', step=1))
    elems.append('<path d="M 60 120 L 330 120" stroke="#ef4444" stroke-width="2.5" data-step="2"/>')
    d = ' '.join(('M' if k == 0 else 'L') + f' {40 + 20 + k * 6.3:.1f} {230 - (150 - 0.012 * ((k * 6.3) - 110) ** 2):.1f}' for k in range(43))
    elems.append(f'<path d="{d}" stroke="#10b981" stroke-width="2.5" fill="none" data-step="3"/>')
    elems += [
        stext(200, 260, 'straight line: underfits the curve', 'red', 12, step=2),
        _codebox(380, 50, 360, 110, ['make_pipeline(PolynomialFeatures(degree=2),', '              StandardScaler(),', '              Ridge(alpha=1))', '',
                                     'x → [x, x²]: still LINEAR in the coefficients'], 'green', step=3, tcolor='#86efac'),
        stext(560, 190, 'degree 15 → wiggly overfit', 'amber', 12, step=4),
        stext(560, 212, 'pick degree with cross-validation', 'amber', 12, step=4),
        stext(560, 245, 'interaction terms: attendance × hours', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'The data follows a curve (rise then fall).',
        'A straight line cannot follow it: underfitting.',
        'Adding x² as an extra feature lets a linear model fit a parabola; the model is still linear in its coefficients.',
        'High degrees overfit; choose the degree with cross-validation and use regularisation.',
        'PolynomialFeatures also creates interaction terms (products of features).',
    ])


def residual_anim():
    elems = [
        stext(380, 24, 'Checking a regression model through its residuals', 'blue', 15, bold=True),
        stext(130, 55, 'good: random scatter', 'green', 12, step=1, bold=True), _axes(20, 65, 220, 120, 'predicted', 'residual', step=1),
        stext(380, 55, 'curve: missing non-linearity', 'amber', 12, step=2, bold=True), _axes(270, 65, 220, 120, 'predicted', '', step=2),
        stext(630, 55, 'funnel: unequal variance', 'red', 12, step=3, bold=True), _axes(520, 65, 220, 120, 'predicted', '', step=3),
    ]
    import math
    for i in range(14):
        x = 30 + i * 14
        elems.append(_dot(20 + x, 125 + (13 if i % 3 == 0 else -9 if i % 3 == 1 else 3), 'green', step=1, r=4))
        elems.append(_dot(270 + x, 125 - 40 * math.sin(i / 4.3) + 20, 'amber', step=2, r=4))
        elems.append(_dot(520 + x, 125 + (i * 3.2) * (1 if i % 2 else -1) * 0.7, 'red', step=3, r=4))
    elems += [
        stext(380, 225, 'also check: big outliers/leverage points · correlated features (multicollinearity) · errors over time', 'purple', 12, step=4),
        stext(380, 250, 'fixes: transform target (log), add features/interactions, robust models, tree ensembles', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 268, *elems), [
        'If the model is adequate, residuals scatter randomly around zero.',
        'A curved pattern means the model is missing a non-linear relationship.',
        'A funnel shape means errors grow with the prediction (heteroscedasticity); intervals and coefficients become unreliable.',
        'Outliers, multicollinearity and time patterns are other things residual analysis reveals.',
        'Typical remedies: transform the target, engineer features, or switch to models that capture non-linearity.',
    ])


# ============================================================ section 4
def logistic_anim():
    import math
    elems = [stext(380, 24, 'Logistic regression: a linear score squashed into a probability', 'blue', 15, bold=True),
             _axes(40, 50, 330, 190, 'z = b₀ + b·x (linear score)', 'P(placed)', step=1)]
    d = ' '.join(('M' if k == 0 else 'L') + f' {40 + k * 8:.1f} {240 - 180 / (1 + math.exp(-(k - 20) / 3.5)):.1f}' for k in range(41))
    elems.append(f'<path d="{d}" stroke="#10b981" stroke-width="3" fill="none" data-step="2"/>')
    elems += [
        f'<line x1="40" y1="150" x2="370" y2="150" stroke="#f59e0b" stroke-dasharray="5,4" data-step="3"/>',
        stext(330, 143, 'threshold 0.5', 'amber', 11, step=3),
        _codebox(400, 50, 340, 110, ['p = 1 / (1 + e^(−z))', '', 'predict_proba → [P(0), P(1)]', 'predict → 1 if P(1) ≥ 0.5'], 'green', step=2, tcolor='#86efac'),
        stext(570, 190, 'coefficient → change in log-odds', 'purple', 12, step=4),
        stext(570, 210, 'np.exp(coef) → odds ratio', 'purple', 12, step=4),
        stext(380, 270, 'despite the name it is a CLASSIFIER · C = inverse regularisation strength (smaller C = stronger)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 288, *elems), [
        'Logistic regression first computes a linear score z from the features.',
        'The sigmoid function turns z into a probability between 0 and 1.',
        'A threshold (0.5 by default) turns probabilities into class labels; it can be moved.',
        'Coefficients act on the log-odds; exponentiated, they are odds ratios, which makes the model explainable.',
        'It is a classification model with L2 regularisation by default, controlled by C.',
    ])


def confusion_anim():
    elems = [
        stext(380, 24, 'Confusion matrix and the metrics built from it', 'blue', 15, bold=True),
        stext(170, 58, 'predicted not placed', 'gray', 11, step=1), stext(290, 58, 'predicted placed', 'gray', 11, step=1),
        stext(50, 95, 'actual 0', 'gray', 11, step=1), stext(50, 155, 'actual 1', 'gray', 11, step=1),
        scell(110, 65, 120, 56, 'TN 74', '#065f46', '#fff', step=1, bold=True, size=14), scell(230, 65, 120, 56, 'FP 12', '#7f1d1d', '#fff', step=1, bold=True, size=14),
        scell(110, 121, 120, 56, 'FN 18', '#7f1d1d', '#fff', step=1, bold=True, size=14), scell(230, 121, 120, 56, 'TP 46', '#065f46', '#fff', step=1, bold=True, size=14),
        sbox(390, 55, 350, 40, 'accuracy = (TP+TN)/all = 120/150 = 0.80', '', 'gray', step=2, size=12),
        sbox(390, 102, 350, 40, 'precision = TP/(TP+FP) = 46/58 = 0.79', 'of those flagged, how many right?', 'blue', step=3, size=11),
        sbox(390, 149, 350, 40, 'recall = TP/(TP+FN) = 46/64 = 0.72', 'of the real positives, how many found?', 'green', step=4, size=11),
        sbox(390, 196, 350, 40, 'F1 = 2·P·R/(P+R) = 0.75', 'balance of precision and recall', 'purple', step=5, size=11),
        stext(230, 215, 'FP = false alarm · FN = missed case', 'red', 12, step=4),
        stext(380, 262, 'which error is worse? missing an at-risk student (FN) → optimise recall · spam filter (FP) → precision', 'amber', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'The confusion matrix counts correct and incorrect predictions per class.',
        'Accuracy is the share of all correct predictions, misleading when classes are imbalanced.',
        'Precision: among predicted positives, how many are real.',
        'Recall (sensitivity): among real positives, how many we found.',
        'F1 balances the two. Choose the metric from the cost of each error type.',
    ])


def roc_anim():
    import math
    elems = [stext(380, 24, 'ROC curve, AUC and choosing a threshold', 'blue', 15, bold=True),
             _axes(40, 50, 250, 200, 'false positive rate', 'true positive rate', step=1),
             '<path d="M 40 250 L 290 50" stroke="#64748b" stroke-dasharray="5,4" data-step="1"/>',
             stext(200, 175, 'random (AUC 0.5)', 'gray', 10, step=1)]
    d = ' '.join(('M' if k == 0 else 'L') + f' {40 + k * 6.25:.1f} {250 - 200 * (1 - (1 - k / 40) ** 3.2):.1f}' for k in range(41))
    elems.append(f'<path d="{d}" stroke="#10b981" stroke-width="3" fill="none" data-step="2"/>')
    elems += [
        _dot(40 + 0.22 * 250, 250 - 200 * (1 - (1 - 0.22) ** 3.2), 'amber', step=3, r=7, focus=3),
        stext(130, 95, 'threshold 0.35', 'amber', 11, step=3),
        _codebox(330, 50, 410, 120, ['proba = model.predict_proba(X_test)[:, 1]', 'roc_auc_score(y_test, proba)', 'fpr, tpr, thr = roc_curve(y_test, proba)',
                                     'pred = (proba >= 0.35).astype(int)   # custom threshold'], 'gray', step=2),
        stext(535, 200, 'AUC = probability a random positive', 'green', 12, step=2),
        stext(535, 220, 'scores higher than a random negative', 'green', 12, step=2),
        stext(380, 275, 'imbalanced data: precision-recall curve / average precision is more informative', 'cyan', 12, step=5),
        stext(535, 245, 'lower threshold → more recall, more false alarms', 'amber', 12, step=4),
    ]
    return anim(canvas(760, 292, *elems), [
        'The ROC curve plots true-positive rate against false-positive rate for every possible threshold; the diagonal is random guessing.',
        'A better model bows towards the top-left; the area under the curve (AUC) summarises ranking quality independent of the threshold.',
        'Each point is a threshold. The default 0.5 is rarely optimal for business costs.',
        'Lowering the threshold catches more positives (recall up) at the price of more false alarms.',
        'For rare positive classes, the precision-recall curve shows performance more honestly.',
    ])


def imbalance_anim():
    elems = [stext(380, 24, 'Imbalanced classes: 95 % "no", 5 % "yes"', 'blue', 15, bold=True)]
    for i in range(40):
        rare = i in (7, 26)
        elems.append(scell(20 + (i % 20) * 34, 50 + (i // 20) * 34, 32, 32, '', '#ef4444' if rare else '#334155', step=1))
    elems += [
        sbox(20, 130, 230, 60, 'always predict "no"', 'accuracy 95 %, recall 0 %', 'red', step=2, size=12, focus=2),
        sbox(265, 130, 230, 60, "class_weight='balanced'", 'errors on rare class cost more', 'green', step=3, size=12),
        sbox(510, 130, 230, 60, 'resampling (in the pipeline)', 'oversample rare / undersample common', 'purple', step=4, size=12),
        stext(380, 220, 'stratified splits · metrics: recall, precision, F1, PR-AUC · tune the decision threshold', 'amber', 12, step=5),
        stext(380, 245, 'collect more positive examples if possible: often the best fix', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 262, *elems), [
        'When one class is rare (dropouts, fraud, defaults), the data is imbalanced.',
        'A useless model that always predicts the majority gets high accuracy, so accuracy is the wrong metric.',
        'Class weights make mistakes on the rare class more expensive during training.',
        'Resampling changes the training data balance (e.g. imbalanced-learn), but only inside training folds.',
        'Use stratified splits, recall/precision/PR-AUC and threshold tuning.',
    ])


def knn_nb_anim():
    import math
    elems = [stext(380, 24, 'K-Nearest Neighbours and Naive Bayes', 'blue', 15, bold=True),
             _axes(20, 50, 300, 190, 'attendance', 'hours', step=1)]
    pts = [(60, 80, 'red'), (90, 120, 'red'), (70, 160, 'red'), (120, 100, 'red'), (200, 60, 'green'), (230, 90, 'green'), (260, 70, 'green'),
           (190, 120, 'green'), (150, 140, 'red'), (220, 150, 'green')]
    for (x, y, c) in pts:
        elems.append(_dot(20 + x, 50 + y, c, step=1))
    elems += [
        _dot(20 + 180, 50 + 100, 'amber', step=2, r=8, focus=2),
        f'<circle cx="200" cy="150" r="48" fill="none" stroke="#f59e0b" stroke-dasharray="4,3" data-step="3"/>',
        stext(170, 268, 'k = 5 nearest: 4 green, 1 red → "placed"', 'amber', 12, step=3),
        sbox(360, 50, 380, 80, 'KNN: no training, store data', 'predict by majority of k closest points\nscale features · slow for big data · choose k by CV', 'blue', step=4, size=12),
        sbox(360, 145, 380, 80, 'Naive Bayes: P(class | features)', 'assumes features independent given the class\nvery fast · great for text (MultinomialNB)', 'purple', step=5, size=12),
    ]
    return anim(canvas(760, 280, *elems), [
        'Students plotted by two features; colour shows the known outcome.',
        'A new student (orange) needs a prediction.',
        'KNN looks at the k nearest training points and takes a majority vote.',
        'KNN does no real training; prediction cost grows with the data, and scaling is essential.',
        'Naive Bayes applies Bayes\' theorem with an independence assumption: simple, fast, a strong baseline for text classification.',
    ])


# ============================================================ section 5
def tree_anim():
    elems = [
        stext(380, 24, 'A decision tree: a sequence of yes/no questions', 'blue', 15, bold=True),
        sbox(280, 50, 200, 46, 'mock_test ≤ 68.5?', 'gini 0.489 · 450 students', 'blue', step=1, size=12),
        sarrow(330, 96, 190, 128, 'gray', step=2), sarrow(430, 96, 570, 128, 'gray', step=2),
        stext(240, 110, 'yes', 'green', 11, step=2), stext(520, 110, 'no', 'red', 11, step=2),
        sbox(90, 130, 200, 46, 'mock_test ≤ 61.5?', '273 students', 'purple', step=2, size=12),
        sbox(470, 130, 200, 46, 'study_hours ≤ 7.15?', '177 students', 'purple', step=2, size=12),
        sbox(20, 215, 140, 44, 'not placed', '153 vs 19', 'red', step=3, size=12), sbox(180, 215, 140, 44, 'not placed', '59 vs 42', 'amber', step=3, size=12),
        sbox(440, 215, 140, 44, 'not placed', '25 vs 22', 'amber', step=3, size=12), sbox(600, 215, 140, 44, 'placed', '108 vs 22', 'green', step=3, size=12),
        sarrow(150, 176, 90, 213, 'gray', step=3), sarrow(230, 176, 250, 213, 'gray', step=3),
        sarrow(530, 176, 510, 213, 'gray', step=3), sarrow(610, 176, 670, 213, 'gray', step=3),
        stext(380, 285, 'split chosen to make child nodes purest (Gini or entropy) · max_depth / min_samples_leaf stop overfitting', 'cyan', 12, step=4),
        stext(380, 308, 'no scaling needed · handles interactions · readable rules · unstable: small data changes → different tree', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 322, *elems), [
        'The root question splits all training students on the most informative feature and threshold.',
        'Each branch asks a further question about its subset.',
        'Leaves give the predicted class (and a probability from the class mix in the leaf).',
        'Splits are chosen greedily to reduce impurity; limits on depth and leaf size control overfitting.',
        'Trees are interpretable and need no scaling, but a single tree has high variance, which ensembles fix.',
    ])


def forest_anim():
    elems = [stext(380, 24, 'Random forest: many decorrelated trees vote', 'blue', 15, bold=True),
             sbox(20, 55, 140, 60, 'training data', '450 students', 'gray', step=1, size=12)]
    for i in range(4):
        x = 200 + i * 135
        elems += [sarrow(x + 60, 42, x + 60, 53, 'gray', step=1),
                  sbox(x, 55, 120, 60, f'bootstrap {i + 1}', 'random rows\n+ random features', 'blue', step=1, size=11),
                  sarrow(x + 60, 115, x + 60, 143, 'gray', step=2),
                  sbox(x, 145, 120, 50, f'tree {i + 1}', 'placed' if i != 2 else 'not placed', 'green' if i != 2 else 'red', step=2, size=12)]
    elems += [
        '<path d="M 90 55 L 90 42 L 665 42" stroke="#94a3b8" stroke-width="2" fill="none" data-step="1"/>',
        sbox(330, 225, 200, 46, 'vote: placed (3 of 4)', 'probability = 0.75', 'amber', step=3, size=12),
        sarrow(430, 195, 430, 223, 'gray', step=3),
        stext(380, 295, 'bagging lowers variance · max_features adds diversity · out-of-bag (OOB) rows give a free validation score', 'cyan', 12, step=4),
        stext(380, 318, 'n_estimators ↑ = more stable (never overfits by adding trees) · feature_importances_ · n_jobs=-1 parallel', 'purple', 12, step=5),
    ]
    return anim(canvas(760, 332, *elems), [
        'Each tree is trained on a bootstrap sample (rows drawn with replacement) and considers a random subset of features at each split.',
        'The trees differ, so their individual errors are partly independent.',
        'Predictions are combined by majority vote (classification) or averaging (regression).',
        'Averaging many high-variance trees reduces variance; rows left out of a bootstrap provide an out-of-bag score.',
        'More trees only make results more stable; the forest also reports feature importances and trains in parallel.',
    ])


def boosting_anim():
    elems = [stext(380, 24, 'Gradient boosting: each tree fixes the previous errors', 'blue', 15, bold=True)]
    for i, (t, s, c) in enumerate([('tree 1', 'rough prediction', 'blue'), ('tree 2', 'fits residuals of 1', 'purple'), ('tree 3', 'fits residuals of 1+2', 'amber'),
                                   ('…tree 200', 'tiny corrections', 'green')]):
        x = 20 + i * 185
        elems.append(sbox(x, 60, 165, 60, t, s, c, step=i + 1, size=12))
        if i:
            elems.append(sarrow(x - 20, 90, x - 2, 90, 'gray', step=i + 1))
    elems += [
        stext(380, 155, 'prediction = tree1 + η·tree2 + η·tree3 + …   (η = learning_rate)', 'amber', 13, step=2, bold=True),
        stext(380, 190, 'shallow trees, added sequentially · small learning_rate + more trees = better but slower', 'purple', 12, step=3),
        stext(380, 215, 'early stopping on a validation split prevents overfitting', 'purple', 12, step=4),
        _codebox(20, 230, 720, 50, ["HistGradientBoostingClassifier(learning_rate=0.1, max_iter=300, early_stopping=True)  · XGBoost · LightGBM · CatBoost"],
                 'green', step=5, tcolor='#86efac'),
    ]
    return anim(canvas(760, 295, *elems), [
        'The first shallow tree makes a rough prediction.',
        'The next tree is trained on what is still wrong (the residuals / gradient of the loss), and its contribution is scaled by the learning rate.',
        'Each new tree corrects the remaining errors of the ensemble so far.',
        'Hundreds of small corrections add up; early stopping halts when validation error stops improving.',
        'Histogram-based boosting in scikit-learn (and XGBoost/LightGBM/CatBoost) is usually the strongest choice for tabular data.',
    ])


def svm_anim():
    elems = [stext(380, 24, 'Support Vector Machine: the widest possible margin', 'blue', 15, bold=True),
             _axes(20, 50, 320, 210, 'feature 1', 'feature 2', step=1)]
    for (x, y) in [(60, 60), (90, 90), (70, 130), (120, 70), (110, 110)]:
        elems.append(_dot(20 + x, 50 + y, 'red', step=1))
    for (x, y) in [(220, 150), (250, 120), (260, 180), (200, 190), (290, 150)]:
        elems.append(_dot(20 + x, 50 + y, 'green', step=1))
    elems += [
        '<path d="M 110 250 L 300 60" stroke="#e2e8f0" stroke-width="2.5" data-step="2"/>',
        '<path d="M 70 230 L 260 40" stroke="#94a3b8" stroke-dasharray="5,4" data-step="2"/>',
        '<path d="M 150 270 L 340 80" stroke="#94a3b8" stroke-dasharray="5,4" data-step="2"/>',
        f'<circle cx="{20 + 110}" cy="{50 + 110}" r="9" fill="none" stroke="#f59e0b" stroke-width="2" data-step="3"/>',
        f'<circle cx="{20 + 220}" cy="{50 + 150}" r="9" fill="none" stroke="#f59e0b" stroke-width="2" data-step="3"/>',
        sbox(380, 55, 360, 50, 'support vectors (circled)', 'the only points that define the boundary', 'amber', step=3, size=12),
        sbox(380, 115, 360, 50, 'C: margin vs mistakes', 'small C = wider margin, more errors allowed', 'purple', step=4, size=12),
        sbox(380, 175, 360, 60, "kernel='rbf' (default) · 'linear' · 'poly'", 'kernel trick: curved boundaries without\nbuilding new features · gamma = reach of each point', 'green', step=5, size=12),
        stext(380, 302, 'needs scaled features · slow beyond ~50k rows · probability=True adds costly calibration', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 318, *elems), [
        'Two classes in feature space.',
        'SVM finds the separating line (hyperplane) with the widest margin to the nearest points of each class.',
        'Those nearest points are the support vectors; the other points do not affect the boundary.',
        'C trades margin width against training errors (soft margin).',
        'Kernels let SVM draw curved boundaries; RBF is the default. Scale features, and prefer other models for very large datasets.',
    ])


def ensemble_anim():
    elems = [
        stext(380, 24, 'Bagging · Boosting · Voting · Stacking', 'blue', 15, bold=True),
        sbox(20, 55, 350, 80, 'Bagging (RandomForest, BaggingClassifier)', 'same model on bootstrap samples, in parallel\naverages away VARIANCE', 'blue', step=1, size=12),
        sbox(390, 55, 350, 80, 'Boosting (GradientBoosting, AdaBoost)', 'models in sequence, each fixing earlier errors\nreduces BIAS (and variance with care)', 'green', step=2, size=12),
        sbox(20, 150, 350, 80, 'Voting (VotingClassifier)', 'different models vote (hard) or average\nprobabilities (soft)', 'purple', step=3, size=12),
        sbox(390, 150, 350, 80, 'Stacking (StackingClassifier)', 'a meta-model learns how to combine\nout-of-fold predictions of base models', 'amber', step=4, size=12),
        stext(380, 260, 'ensembles help most when members are accurate AND make different errors · cost: complexity, speed, explainability', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 278, *elems), [
        'Bagging trains copies of one model on different bootstrap samples and averages them, reducing variance.',
        'Boosting trains models sequentially, each focusing on what earlier ones got wrong, reducing bias.',
        'Voting combines different model types by majority or averaged probabilities.',
        'Stacking trains a second-level model on the base models\' out-of-fold predictions.',
        'Diversity of errors is what makes ensembles work; weigh the gain against complexity.',
    ])


# ============================================================ section 6
def cv_anim():
    elems = [stext(380, 24, '5-fold cross-validation', 'blue', 15, bold=True)]
    for r in range(5):
        for c in range(5):
            val = (r == c)
            elems.append(scell(120 + c * 100, 55 + r * 36, 98, 32, 'validate' if val else 'train', '#f59e0b' if val else '#10b981', '#fff', step=r + 1, bold=val))
        elems.append(stext(70, 76 + r * 36, f'round {r + 1}', 'gray', 11, step=r + 1))
        elems.append(stext(660, 76 + r * 36, ['0.778', '0.767', '0.822', '0.833', '0.700'][r], 'amber', 12, step=r + 1, bold=True))
    elems += [
        stext(380, 260, 'score = mean 0.780 ± std 0.047 · every row validated exactly once', 'green', 13, step=5, bold=True),
        stext(380, 285, 'StratifiedKFold (classification) · GroupKFold (repeated entities) · TimeSeriesSplit (time) · test set still kept aside', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 300, *elems), [
        'The training data is cut into 5 folds. Round 1: train on folds 2–5, validate on fold 1.',
        'Round 2: a different fold is held out.',
        'Each round trains a fresh model.',
        'Every row is used for validation exactly once and for training four times.',
        'The mean (and spread) of the 5 scores is a more reliable estimate than one split. Choose the splitter that matches the data structure.',
    ])


def grid_anim():
    elems = [stext(380, 24, 'Hyperparameter search with cross-validation', 'blue', 15, bold=True)]
    vals = [[0.811, 0.816, 0.841], [0.752, 0.798, 0.834], [0.698, 0.795, 0.834], [0.696, 0.795, 0.834]]
    elems.append(stext(110, 70, 'max_depth ↓ / min_samples_leaf →', 'gray', 11, step=1))
    for j, leaf in enumerate([1, 5, 20]):
        elems.append(stext(250 + j * 80, 70, str(leaf), 'gray', 11, step=1))
    for i, depth in enumerate([3, 5, 8, 'None']):
        elems.append(stext(190, 100 + i * 36, str(depth), 'gray', 11, step=1))
        for j in range(3):
            best = (i == 0 and j == 2)
            elems.append(scell(210 + j * 80, 80 + i * 36, 78, 32, f'{vals[i][j]:.3f}', '#065f46' if best else '#1e293b', '#fff', step=2, bold=best))
    elems += [
        _codebox(470, 60, 270, 115, ["GridSearchCV(pipe, {", "  'model__max_depth': [3, 5, 8, None],", "  'model__min_samples_leaf': [1, 5, 20]},",
                                     "  cv=5, scoring='roc_auc')"], 'blue', step=1, tcolor='#7dd3fc'),
        stext(605, 200, '12 combinations × 5 folds = 60 fits', 'amber', 12, step=2),
        stext(330, 240, 'best_params_ → refit on all training data → best_estimator_', 'green', 13, step=3, bold=True),
        stext(380, 268, 'RandomizedSearchCV: sample n_iter combinations from distributions (faster for many parameters)', 'purple', 12, step=4),
        stext(380, 292, 'HalvingGridSearchCV / Optuna for big spaces · report the test score of the refit model only once', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 308, *elems), [
        'Define candidate values for each hyperparameter (step names reach inside the pipeline).',
        'Every combination is evaluated with cross-validation; the cell colour marks the best mean score.',
        'The best combination is refitted on all training data and exposed as best_estimator_.',
        'Random search samples combinations, usually finding good settings with far fewer fits.',
        'Successive halving and Bayesian tools scale further; the test set stays untouched until the end.',
    ])


def curves_anim():
    import math
    elems = [stext(380, 24, 'Learning curves and validation curves', 'blue', 15, bold=True),
             stext(190, 52, 'learning curve (more data →)', 'blue', 12, step=1, bold=True), _axes(30, 60, 300, 170, 'training set size', 'score', step=1)]
    d1 = ' '.join(('M' if k == 0 else 'L') + f' {30 + k * 7.5:.1f} {80 + 40 * (1 - math.exp(-k / 15)):.1f}' for k in range(41))
    d2 = ' '.join(('M' if k == 0 else 'L') + f' {30 + k * 7.5:.1f} {220 - 100 * (1 - math.exp(-k / 12)):.1f}' for k in range(41))
    elems += [f'<path d="{d1}" stroke="#0ea5e9" stroke-width="2.5" fill="none" data-step="1"/>',
              f'<path d="{d2}" stroke="#10b981" stroke-width="2.5" fill="none" data-step="2"/>',
              stext(280, 100, 'train', 'blue', 11, step=1), stext(280, 145, 'validation', 'green', 11, step=2),
              stext(190, 272, 'gap closing & flattening → more data helps little', 'amber', 11, step=2),
              stext(570, 52, 'validation curve (complexity →)', 'purple', 12, step=3, bold=True), _axes(410, 60, 320, 170, 'max_depth', '', step=3)]
    d3 = ' '.join(('M' if k == 0 else 'L') + f' {410 + k * 8:.1f} {200 - 120 * (1 - math.exp(-k / 8)):.1f}' for k in range(41))
    d4 = ' '.join(('M' if k == 0 else 'L') + f' {410 + k * 8:.1f} {200 - 90 * math.exp(-((k - 12) / 10) ** 2):.1f}' for k in range(41))
    elems += [f'<path d="{d3}" stroke="#0ea5e9" stroke-width="2.5" fill="none" data-step="3"/>',
              f'<path d="{d4}" stroke="#10b981" stroke-width="2.5" fill="none" data-step="4"/>',
              f'<line x1="{410 + 12 * 8}" y1="74" x2="{410 + 12 * 8}" y2="230" stroke="#f59e0b" stroke-dasharray="4,3" data-step="4"/>',
              stext(410 + 12 * 8, 66, 'sweet spot', 'amber', 11, step=4),
              stext(380, 300, 'left of the peak: underfitting (both low) · right of it: overfitting (train high, validation falls)', 'cyan', 12, step=5)]
    return anim(canvas(760, 315, *elems), [
        'A learning curve plots scores against training-set size; training score starts high.',
        'Validation score rises with more data. When the curves converge and flatten, more data will not help much; a persistent gap suggests overfitting.',
        'A validation curve varies one hyperparameter: training score keeps rising with complexity.',
        'Validation score peaks and then falls: the peak is the best complexity.',
        'Both curves turn the bias-variance trade-off into something you can see and act on.',
    ])


def importance_anim():
    elems = [stext(380, 24, 'Which features matter? Two ways to ask', 'blue', 15, bold=True)]
    feats = [('mock_test', 0.36, 0.10), ('study_hours', 0.26, 0.04), ('attendance', 0.22, 0.03), ('student_id', 0.15, -0.02)]
    for i, (f, imp, perm) in enumerate(feats):
        y = 60 + i * 34
        elems.append(stext(110, y + 18, f, 'gray', 12, anchor='end', step=1))
        elems.append(f'<rect x="120" y="{y}" width="{imp * 500}" height="24" fill="#0ea5e9" data-step="1"/>')
        elems.append(stext(130 + imp * 500, y + 17, f'{imp:.2f}', 'blue', 11, anchor='start', step=1))
        elems.append(f'<rect x="460" y="{y}" width="{max(perm, 0) * 2000}" height="24" fill="#10b981" data-step="2"/>')
        elems.append(stext(470 + max(perm, 0) * 2000, y + 17, f'{perm:+.2f}', 'green', 11, anchor='start', step=2))
    elems += [
        stext(240, 48, 'impurity importance (feature_importances_)', 'blue', 12, step=1, bold=True),
        stext(600, 48, 'permutation importance (test data)', 'green', 12, step=2, bold=True),
        stext(380, 250, 'impurity importance favours high-cardinality features (an ID can look useful) and is computed on training data', 'red', 12, step=3, focus=3),
        stext(380, 275, 'permutation: shuffle one column, measure the score drop → model-agnostic, on held-out data', 'green', 12, step=4),
        stext(380, 300, 'SelectKBest, RFE, L1 models select features · SHAP explains individual predictions', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 318, *elems), [
        'Tree models report impurity-based importances: how much each feature reduced impurity during training.',
        'Permutation importance shuffles one feature at a time on validation/test data and measures how much the score drops.',
        'Impurity importance is biased towards features with many unique values, such as IDs, and reflects training data only.',
        'Permutation importance works for any model and reflects real predictive value on unseen data.',
        'Feature selection methods and SHAP values build on these ideas.',
    ])


def persist_anim():
    elems = [
        stext(380, 24, 'From notebook to production: saving and serving a model', 'blue', 15, bold=True),
        _row([('fit pipeline', 'preprocessing + model', 'blue', 1), ('joblib.dump', 'placement_v3.joblib', 'green', 2), ('record', 'versions, metrics,\nfeatures, threshold', 'purple', 3),
              ('joblib.load', 'in the scoring job / API', 'amber', 4), ('predict_proba', 'raw rows in', 'cyan', 5)], 60, w=130, gap=17, h=66, size=12),
        stext(380, 170, 'load with the SAME scikit-learn version (pickles are not portable across versions) · pin requirements', 'red', 12, step=3, focus=3),
        stext(380, 195, 'only load model files you trust: unpickling can execute code · skops.io offers a safer format', 'amber', 12, step=4),
        stext(380, 225, 'batch scoring (cron/Airflow) or a REST API (FastAPI) · log inputs and predictions · monitor drift and accuracy', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Train the whole pipeline so preprocessing travels with the model.',
        'Save it with joblib (efficient for NumPy arrays inside the model).',
        'Store metadata next to it: library versions, training data date, metrics, feature list, chosen threshold.',
        'Load it in the scoring environment with the same library versions; never load untrusted pickle files.',
        'Serve predictions in batches or through an API, and monitor inputs and accuracy over time.',
    ])


# ============================================================ section 7
def _blob(rng, n, cx, cy, sx, sy):
    return [(cx + rng.gauss(0, sx), cy + rng.gauss(0, sy)) for _ in range(n)]


def kmeans_anim():
    import random
    rng = random.Random(3)
    groups = [_blob(rng, 14, 110, 200, 28, 18), _blob(rng, 12, 210, 120, 22, 20), _blob(rng, 10, 320, 170, 24, 22)]
    cols = ['red', 'blue', 'green']
    elems = [stext(380, 24, 'K-Means: assign to nearest centroid, move centroid, repeat', 'blue', 15, bold=True),
             _axes(40, 60, 380, 200, 'study hours (scaled)', 'mock test (scaled)', step=1)]
    for g in groups:
        elems += [_dot(x, y, 'gray', step=1) for x, y in g]
    start = [(150, 110), (180, 230), (380, 230)]
    for (x, y), c in zip(start, cols):
        elems.append(f'<path d="M {x-8} {y-8} L {x+8} {y+8} M {x-8} {y+8} L {x+8} {y-8}" stroke="{PALETTE[c]}" stroke-width="4" data-step="1"/>')
    for g, c in zip(groups, cols):
        elems += [_dot(x, y, c, step=2) for x, y in g]
    for g, c, (sx, sy) in zip(groups, cols, start):
        mx = round(sum(p[0] for p in g) / len(g), 1); my = round(sum(p[1] for p in g) / len(g), 1)   # rounded: identical on every Python version
        elems.append(sarrow(sx, sy, mx, my, c, step=3, dashed=True))
        elems.append(f'<circle cx="{mx:.0f}" cy="{my:.0f}" r="10" fill="none" stroke="{PALETTE[c]}" stroke-width="4" data-step="3"/>')
    elems += [
        stext(240, 300, 'repeat until no point changes cluster (converged)', 'amber', 12, step=4),
        stable(460, 60, ['k', 'inertia', 'silhouette'], [['2', '1191.9', '0.307'], ['3', '904.3', '0.303'], ['4', '752.3', '0.275'], ['5', '649.2', '0.266']],
               [40, 90, 90], step=4, title='choosing k (real run)', title_color='amber', focus_rows={1: '4'}),
        stable(460, 250, ['segment', 'n', 'placed'], [['low effort', '257', '14 %'], ['high attendance', '201', '58 %'], ['high study hours', '142', '71 %']],
               [130, 50, 60], step=5, title='profile the segments', title_color='green'),
    ]
    return anim(canvas(760, 380, *elems), [
        'Start with k centroids (✕). k-means++ spreads them out; here k = 3.',
        'Assign every student to the nearest centroid (Euclidean distance on scaled features).',
        'Move each centroid to the mean of the points assigned to it.',
        'Repeat assign + move until nothing changes. Compare inertia and silhouette across k: k = 2 and 3 are almost tied; the elbow and usefulness favour 3.',
        'Profile the clusters in original units. The placement rate (not used for clustering) confirms the segments are meaningful.',
    ])


def density_anim():
    import math, random
    rng = random.Random(1)
    pts = []
    for i in range(26):
        t = math.pi * i / 25
        pts.append((math.cos(t) + rng.gauss(0, .06), math.sin(t) + rng.gauss(0, .06), 0))
        pts.append((1 - math.cos(t) + rng.gauss(0, .06), .5 - math.sin(t) + rng.gauss(0, .06), 1))
    def xy(px, py, ox, oy):
        return ox + (px + 1.1) * 58, oy + (1.25 - py) * 60
    elems = [stext(380, 24, 'Shapes K-Means cannot see: density and hierarchy', 'blue', 15, bold=True),
             stext(130, 52, 'K-Means k=2 (ARI 0.23)', 'red', 12, step=1, bold=True),
             stext(390, 52, 'DBSCAN eps=0.2 (ARI 1.00)', 'green', 12, step=2, bold=True)]
    for px, py, lab in pts:
        x, y = xy(px, py, 12, 62)
        elems.append(_dot(x, y, 'blue' if px < 0.5 else 'amber', step=1, r=4))
    elems.append(f'<line x1="{xy(.5, 0, 12, 62)[0]}" y1="60" x2="{xy(.5, 0, 12, 62)[0]}" y2="250" stroke="#ef4444" stroke-dasharray="5,4" data-step="1"/>')
    for px, py, lab in pts:
        x, y = xy(px, py, 262, 62)
        elems.append(_dot(x, y, 'gray', step=2, r=4))
    cx, cy = xy(pts[21][0], pts[21][1], 262, 62)
    elems.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="22" fill="#10b981" fill-opacity="0.15" stroke="#10b981" stroke-width="2" data-step="2"/>')
    elems.append(stext(cx, cy + 38, 'core point: ≥ min_samples within eps', 'green', 10, step=2))
    for px, py, lab in pts:
        x, y = xy(px, py, 262, 62)
        elems.append(_dot(x, y, 'green' if lab == 0 else 'purple', step=3, r=4))
    for nx, ny in [(2.2, 0.75), (-0.9, -0.4)]:
        x, y = xy(nx, ny, 262, 62)
        elems.append(f'<path d="M {x-5:.0f} {y-5:.0f} L {x+5:.0f} {y+5:.0f} M {x-5:.0f} {y+5:.0f} L {x+5:.0f} {y-5:.0f}" stroke="#ef4444" stroke-width="2.5" data-step="3"/>')
    elems.append(stext(390, 268, 'red ✕ = noise (label −1)', 'red', 11, step=3))
    # dendrogram
    elems.append(stext(650, 52, 'dendrogram (agglomerative)', 'purple', 12, step=4, bold=True))
    xs = [560, 585, 610, 635, 670, 695, 720, 745]
    for x in xs:
        elems.append(f'<line x1="{x}" y1="250" x2="{x}" y2="225" stroke="#a78bfa" stroke-width="2" data-step="4"/>')
    def merge(x1, x2, y0, y, st=4):
        return (f'<path d="M {x1} {y0[0]} L {x1} {y} L {x2} {y} L {x2} {y0[1]}" stroke="#a78bfa" stroke-width="2" fill="none" data-step="{st}"/>')
    elems += [merge(560, 585, (225, 225), 210), merge(610, 635, (225, 225), 205), merge(670, 695, (225, 225), 212), merge(720, 745, (225, 225), 200),
              merge(572, 622, (210, 205), 170), merge(682, 732, (212, 200), 160), merge(597, 707, (170, 160), 90)]
    elems.append(f'<line x1="550" y1="130" x2="755" y2="130" stroke="#f59e0b" stroke-dasharray="5,4" data-step="4"/>')
    elems.append(stext(655, 122, 'cut here → 2 clusters', 'amber', 10, step=4))
    elems += [stext(380, 295, 'two moons: KMeans 0.23 · ward 0.30 · single linkage 1.00 · DBSCAN 1.00 (adjusted Rand index)', 'cyan', 12, step=5),
              stext(380, 315, 'eps 0.05 → 243 noise points · 0.1 → 11 clusters · 0.2 → 2 clusters · 0.5 → everything in 1', 'amber', 12, step=5)]
    return anim(canvas(760, 330, *elems), [
        'K-Means splits the plane with a straight boundary between centroids, so it cuts each moon in half.',
        'DBSCAN looks at the neighbourhood of each point: a point with at least min_samples neighbours within eps is a core point.',
        'Clusters grow through connected core points, following any shape; isolated points become noise (−1).',
        'Agglomerative clustering merges the closest clusters step by step; cutting the dendrogram at a height gives the clusters.',
        'Real results on 300 moon points: single linkage and DBSCAN recover the moons perfectly, but DBSCAN is very sensitive to eps.',
    ])


def pca_anim():
    import math, random
    rng = random.Random(5)
    elems = [stext(380, 24, 'PCA: rotate to the directions of greatest variance', 'blue', 15, bold=True),
             _axes(40, 60, 300, 210, 'feature 1 (scaled)', 'feature 2 (scaled)', step=1)]
    ang = math.radians(-32)
    cx, cy = 190, 165
    pts = []
    for _ in range(40):
        a, b = rng.gauss(0, 55), rng.gauss(0, 14)
        pts.append((cx + a * math.cos(ang) - b * math.sin(ang), cy + a * math.sin(ang) + b * math.cos(ang), a))
    elems += [_dot(x, y, 'blue', step=1, r=4) for x, y, a in pts]
    ux, uy = math.cos(ang), math.sin(ang)
    elems += [sarrow(cx - 130 * ux, cy - 130 * uy, cx + 130 * ux, cy + 130 * uy, 'amber', step=2),
              stext(cx + 135 * ux + 10, cy + 135 * uy - 4, 'PC1', 'amber', 12, step=2, bold=True),
              sarrow(cx + 40 * uy, cy - 40 * ux, cx - 40 * uy, cy + 40 * ux, 'green', step=2),
              stext(cx - 46 * uy, cy + 46 * ux + 14, 'PC2', 'green', 12, step=2, bold=True)]
    for x, y, a in pts[::3]:
        px, py = cx + a * ux, cy + a * uy
        elems.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{px:.0f}" y2="{py:.0f}" stroke="#f59e0b" stroke-width="1" stroke-dasharray="2,2" data-step="3"/>')
        elems.append(_dot(px, py, 'amber', step=3, r=3))
    shares = [0.362, 0.192, 0.111, 0.071, 0.066]
    cum = 0
    elems.append(stext(560, 60, 'wine data (13 features): variance per component', 'purple', 12, step=4, bold=True))
    for i, v in enumerate(shares):
        cum += v
        x = 410 + i * 62
        h = v * 400
        elems.append(f'<rect x="{x}" y="{230 - h:.0f}" width="44" height="{h:.0f}" fill="#8b5cf6" data-step="4"/>')
        elems.append(stext(x + 22, 246, f'PC{i + 1}', 'gray', 11, step=4))
        elems.append(stext(x + 22, 224 - h, f'{v:.0%}', 'purple', 11, step=4))
        elems.append(stext(x + 22, 262, f'Σ {cum:.0%}', 'amber', 10, step=4))
    elems += [stext(380, 304, '8 components keep 90 % of variance · logistic CV accuracy: 2 PCs 0.955 vs all 13 features 0.983', 'cyan', 12, step=5),
              stext(380, 326, 'standardise first · PCA is unsupervised: low-variance directions can still matter for y', 'red', 12, step=5)]
    return anim(canvas(760, 340, *elems), [
        'Correlated, standardised features form an elongated cloud.',
        'PC1 points along the direction of greatest spread; PC2 is perpendicular to it and captures the next-largest spread.',
        'Projecting each point onto PC1 keeps most of the information in one number instead of two.',
        'On the 13-feature wine data the first two components hold 55 % of the variance; the cumulative share tells you how many to keep.',
        'Two components already give 0.955 CV accuracy versus 0.983 with all features: much simpler, slightly less accurate.',
    ])


def isolation_anim():
    import random
    rng = random.Random(9)
    elems = [stext(380, 24, 'Isolation Forest: anomalies are isolated in fewer random cuts', 'blue', 15, bold=True),
             sbox(40, 60, 300, 200, '', '', 'gray', step=1, fill_opacity=0.04)]
    normal = _blob(rng, 30, 150, 175, 30, 25)
    elems += [_dot(x, y, 'blue', step=1, r=4) for x, y in normal]
    ox, oy = 305, 85
    elems.append(_dot(ox, oy, 'red', step=1, r=6))
    elems.append(stext(340, 54, 'outlier: 31 % att · 0 h · mock 98', 'red', 10, anchor='end', step=1))
    elems += [f'<line x1="270" y1="60" x2="270" y2="260" stroke="#f59e0b" stroke-width="2" data-step="2"/>',
              f'<line x1="270" y1="120" x2="340" y2="120" stroke="#f59e0b" stroke-width="2" data-step="2"/>',
              stext(305, 140, '2 cuts', 'amber', 11, step=2, bold=True)]
    nx, ny = normal[0]
    for k, (x1, y1, x2, y2) in enumerate([(200, 60, 200, 260), (40, 200, 200, 200), (120, 60, 120, 200), (120, 150, 200, 150), (160, 150, 160, 200), (120, 175, 160, 175)]):
        elems.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#10b981" stroke-width="1.5" data-step="3"/>')
    elems.append(stext(140, 276, 'a typical student needs many cuts', 'green', 11, step=3))
    elems.append(stable(400, 60, ['att', 'hours', 'mock', 'score'], [['31', '0.0', '98', '−0.123'], ['28', '13.0', '25', '−0.119'], ['72', '23.4', '100', '−0.064'],
                                                                     ['45', '14.5', '99', '−0.062'], ['100', '0.0', '97', '−0.054'], ['99', '0.5', '30', '−0.041']],
                        [55, 65, 55, 80], step=4, title='lowest scores (real run)', title_color='red', focus_rows={0: '4', 1: '4', 3: '4', 4: '4', 5: '4'}))
    elems += [stext(380, 296, 'all 5 planted records caught (IF and LOF) · 7 real extreme students also flagged for review', 'amber', 11, step=5),
              stext(380, 318, 'average path length over 300 random trees → score · contamination sets the flag threshold · humans review the list', 'cyan', 12, step=5)]
    return anim(canvas(760, 332, *elems), [
        'Most students form a dense cloud; one record is far from it.',
        'Random splits on random features isolate the odd record after only two cuts.',
        'A typical student sits among many others, so many cuts are needed to isolate it.',
        'Averaging the path length over many random trees gives an anomaly score: lower is more abnormal. The five planted records rank near the top.',
        'contamination=0.02 flags the 12 lowest-scoring rows; the list goes to a person for review, not to automatic action.',
    ])


def text_anim():
    elems = [
        stext(380, 24, 'Text classification: words → TF-IDF numbers → Naive Bayes', 'blue', 15, bold=True),
        _codebox(20, 50, 330, 76, ['"again lectures are too fast and', ' placement cell replies late"', '→ label: faculty'], 'gray', step=1, tcolor='#e2e8f0'),
        sbox(370, 50, 370, 76, 'tokenise · lowercase · drop stop words', 'again, lectures, fast, placement, cell, replies, late', 'purple', step=2, size=12),
        stable(20, 160, ['fast', 'lectures', 'cell', 'late', 'replies', 'placement', '…85'], [['0.54', '0.39', '0.39', '0.39', '0.39', '0.31', '0']],
               [60, 70, 50, 50, 65, 80, 45], step=3, title='TF-IDF row for this comment (real weights)', title_color='amber'),
        stext(380, 252, 'rare, topic-specific words weigh more; "placement" appears in many comments → lower IDF', 'amber', 11, step=3),
        sbox(470, 160, 270, 70, 'MultinomialNB', 'P(topic) × Π P(word | topic)\n→ most probable topic', 'green', step=4, size=12),
        sarrow(440, 195, 468, 195, 'gray', step=4),
        stext(380, 280, 'CV accuracy: Naive Bayes 0.850 · Logistic Regression 0.867 · mixed comments are the hard ones', 'cyan', 12, step=5),
        stext(380, 303, 'unseen words ("teacher") are ignored → "teacher was late to the lab" → lab, only 0.43 confident', 'red', 12, step=5),
    ]
    return anim(canvas(760, 318, *elems), [
        'Each training comment is raw text with a topic label. This one mixes a faculty phrase with a placement phrase.',
        'The vectoriser splits text into tokens, lowercases them and removes stop words ("are", "too", "and").',
        'TF-IDF turns the comment into a sparse row: one column per vocabulary word, weighted by frequency × rarity.',
        'Naive Bayes combines per-topic word probabilities and picks the most probable topic.',
        'Both models reach about 85–87 % on mixed comments; words never seen in training contribute nothing.',
    ])


# ============================================================ section 8
def e2e_anim():
    elems = [
        stext(380, 24, 'End-to-end: every step guards against a classic mistake', 'blue', 15, bold=True),
        _row([('raw data', '600 students', 'gray', 1), ('split', '450 train / 150 test', 'amber', 1), ('Pipeline', 'impute · scale ·\none-hot · model', 'purple', 2),
              ('CV compare', 'vs baseline', 'blue', 3), ('tune C', 'log loss', 'cyan', 4)], 50, x0=20, w=132, gap=16, h=60, size=12),
        stable(30, 140, ['model', 'CV accuracy', 'CV AUC'], [['baseline', '0.576', '0.500'], ['logistic', '0.787', '0.862'], ['forest', '0.802', '0.851'], ['boosting', '0.753', '0.800']],
               [100, 100, 80], step=3, title='5-fold CV on training data (real run)', title_color='blue', focus_rows={1: '3'}),
        sbox(370, 150, 170, 56, 'best C = 0.1', 'CV log loss 0.453', 'cyan', step=4, size=12),
        sbox(560, 150, 180, 56, 'TEST once', 'AUC 0.877 · accuracy 0.773', 'green', step=5, size=12),
        sbox(560, 220, 180, 50, 'joblib.dump', 'pipeline + metadata', 'green', step=5, size=12),
        sarrow(540, 178, 558, 178, 'gray', step=5), sarrow(650, 206, 650, 218, 'gray', step=5),
        stext(380, 300, 'simplest model within noise of the best wins: logistic ≈ forest, faster and explainable', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 315, *elems), [
        'Split off a stratified test set before looking at anything else.',
        'Put every preprocessing step and the model into one Pipeline, so CV folds and production use the same code.',
        'Compare candidates with cross-validation against a baseline. The baseline\'s AUC of 0.5 is the floor; logistic and forest are close.',
        'Tune the chosen model on the training data only (log loss rewards calibrated probabilities).',
        'Evaluate once on the untouched test set, then save the fitted pipeline with its metadata.',
    ])


def threshold_anim():
    import random
    rng = random.Random(4)
    elems = [stext(380, 24, 'Rare dropouts: move the threshold to match the goal', 'blue', 15, bold=True),
             sarrow(40, 150, 470, 150, 'gray', step=1), stext(40, 172, '0', 'gray', 11, step=1), stext(460, 172, '1', 'gray', 11, step=1),
             stext(255, 190, 'predicted dropout probability', 'gray', 11, step=1)]
    for _ in range(46):
        p = min(abs(rng.gauss(0, 0.09)), 0.45)
        elems.append(_dot(40 + p * 420, 140 - rng.random() * 70, 'blue', step=1, r=4))
    for p in [0.03, 0.06, 0.1, 0.13, 0.17, 0.24, 0.33, 0.46]:
        elems.append(_dot(40 + p * 420, 140 - rng.random() * 70, 'red', step=1, r=5))
    elems += [f'<line x1="250" y1="55" x2="250" y2="150" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5,4" data-step="2"/>',
              stext(250, 50, 'default 0.5', 'gray', 11, step=2),
              f'<line x1="74" y1="55" x2="74" y2="150" stroke="#f59e0b" stroke-width="3" data-step="3"/>',
              stext(80, 50, 'tuned 0.081', 'amber', 11, step=3, anchor='start'),
              stable(495, 55, ['threshold', 'flagged', 'recall', 'precision'], [['0.5', '2', '0.00', '0.00'], ['0.081', '47', '0.67', '0.17']],
                     [66, 56, 52, 66], step=2, title='test set: 12 real dropouts', title_color='red', focus_rows={1: '3'}),
              sbox(495, 160, 245, 50, 'capacity: top 25 by probability', 'contains 5 of the 12 dropouts', 'purple', step=4, size=12),
              stext(380, 235, 'dropout rate 8 % → "nobody drops out" scores 92 % accuracy and is useless', 'red', 12, step=1),
              stext(380, 260, 'threshold chosen on out-of-fold training predictions (recall ≥ 0.80 there), never on the test set', 'cyan', 12, step=5),
              stext(380, 283, 'PR AUC 0.209 vs 0.080 for a random ranking · report how many positives each estimate rests on', 'amber', 12, step=5)]
    return anim(canvas(760, 298, *elems), [
        'Most students (blue) get low dropout probabilities; real dropouts (red) are scattered and mostly below 0.5.',
        'With the default 0.5 threshold the model flags 2 students and catches none of the 12 dropouts.',
        'Lowering the threshold to 0.081 (chosen for 80 % recall on training folds) flags 47 and catches 8 of 12 on the test set.',
        'If mentors can only call 25 students, rank by probability and take the top of the list.',
        'The threshold is a tuned parameter: choose it on validation data and report rare-class metrics.',
    ])


def compare_anim():
    import random
    rng = random.Random(2)
    elems = [stext(380, 24, 'Is the difference real? Paired, repeated cross-validation', 'blue', 15, bold=True),
             stable(20, 55, ['split seed', 'logistic', 'forest'], [['0', '0.839', '0.836'], ['1', '0.877', '0.869'], ['2', '0.873', '0.860'], ['3', '0.890', '0.867']],
                    [80, 70, 70], step=1, title='single splits: AUC moves ±0.05', title_color='amber')]
    diffs = [-0.040 + i * 0.038 / 15 for i in range(16)] + [0.003 + i * 0.022 / 8 for i in range(9)]   # illustrative: 16 losses, 9 wins
    elems += [stext(560, 52, 'forest − logistic, 25 paired folds', 'purple', 12, step=2, bold=True),
              f'<line x1="300" y1="150" x2="740" y2="150" stroke="#94a3b8" stroke-width="1.5" data-step="2"/>',
              stext(745, 154, '0', 'gray', 11, step=2, anchor='start')]
    for i, d in enumerate(diffs):
        elems.append(_dot(312 + i * 17, 150 - d * 1500, 'green' if d > 0 else 'red', step=2, r=5))
    elems += [f'<line x1="300" y1="{150 + 0.009 * 1500:.0f}" x2="740" y2="{150 + 0.009 * 1500:.0f}" stroke="#f59e0b" stroke-dasharray="5,4" data-step="3"/>',
              stext(520, 240, 'mean −0.009 ± 0.017 · forest better in 9 of 25', 'amber', 12, step=3),
              stable(20, 230, ['model', 'AUC', 'fit time'], [['baseline', '0.500', '1 ms'], ['logistic', '0.862 ± 0.036', '14 ms'], ['forest', '0.853 ± 0.039', '479 ms']],
                     [80, 110, 70], step=4, title='5 × 5 repeated stratified CV', title_color='blue'),
              stext(560, 280, 'difference smaller than its spread → noise', 'cyan', 12, step=5),
              stext(560, 305, 'keep the simpler, 30× faster logistic model', 'green', 12, step=5, bold=True)]
    return anim(canvas(760, 345, *elems), [
        'On single random splits, AUC jumps by about 0.05 between seeds, more than the gap between the models.',
        'Score both models on the same 25 folds and plot the per-fold difference.',
        'The mean difference is −0.009 with a spread of 0.017: the forest wins 9 times, loses 16.',
        'Add a baseline and fit times to the comparison.',
        'A difference inside the noise is not an improvement; simplicity and speed decide.',
    ])


def leak_anim():
    elems = [
        stext(380, 24, 'A 100 % model: find the answer key on the desk', 'blue', 15, bold=True),
        sbox(20, 62, 220, 56, 'leaky model', 'CV accuracy 1.000', 'red', step=1, size=13),
        stable(270, 62, ['feature', 'importance', 'AUC alone'], [['attendance', '0.019', '0.693'], ['study_hours', '0.053', '0.755'], ['mock_test', '0.093', '0.805'],
                                                                 ['interview_rounds', '0.836', '1.000']], [140, 90, 90], step=2, title='feature audit', title_color='amber',
               focus_rows={3: '2'}),
        stext(380, 218, 'interview_rounds is recorded during the drive → known only AFTER the outcome → drop it', 'red', 12, step=3, focus=3),
        sbox(20, 236, 220, 50, '150 duplicated students', '66 land in both train and test', 'amber', step=4, size=12),
        _row([('leaky', '1.000', 'red', 5), ('no leak, plain CV', '0.861', 'amber', 5), ('GroupKFold by student', '0.767', 'green', 5)], 236, x0=260, w=150, gap=18, h=50, size=12),
        stext(380, 312, 'ask of every feature: "when is this value known?" · group related rows · build training data as of prediction time', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 328, *elems), [
        'A random forest reaches 100 % accuracy on a problem experts find hard: suspicious.',
        'Importances and single-feature AUCs point at one column that predicts the label perfectly on its own.',
        'That column is only known after the outcome: target leakage. Remove it.',
        'Re-enrolled students appear twice, so near-copies end up on both sides of the split.',
        'Removing the leak gives 0.861; grouping by student removes the duplicate effect and gives the honest 0.767.',
    ])


def drift_anim():
    months = [('Jan', 0.098, 0.46, 0.44, 0.867), ('Mar', 0.216, 0.37, 0.38, 0.866), ('Jun', 0.759, 0.31, 0.15, 0.878)]
    elems = [stext(380, 24, 'Monitoring: watch inputs now, outcomes when they arrive', 'blue', 15, bold=True),
             stext(170, 52, 'PSI of mock_test per month', 'purple', 12, step=1, bold=True),
             sarrow(40, 240, 310, 240, 'gray', step=1)]
    for y, lab, col in [(240 - 0.1 * 220, '0.10', 'green'), (240 - 0.25 * 220, '0.25', 'red')]:
        elems.append(f'<line x1="40" y1="{y:.0f}" x2="310" y2="{y:.0f}" stroke="{PALETTE[col]}" stroke-dasharray="5,4" data-step="1"/>')
        elems.append(stext(318, y + 4, lab, col, 10, step=1, anchor='start'))
    for i, (m, psi, p, act, auc) in enumerate(months):
        x = 70 + i * 85
        h = min(psi, 0.8) * 220
        col = '#10b981' if psi < 0.1 else '#f59e0b' if psi < 0.25 else '#ef4444'
        elems.append(f'<rect x="{x}" y="{240 - h:.0f}" width="50" height="{h:.0f}" fill="{col}" data-step="{i + 1}"/>')
        elems.append(stext(x + 25, 256, m, 'gray', 11, step=i + 1))
        elems.append(stext(x + 54, 252 - h, f'{psi:.3f}', 'gray', 11, step=i + 1, anchor='start'))
    elems.append(stable(380, 55, ['month', 'mean p', 'actual', 'AUC'], [[m, f'{p:.2f}', f'{a:.2f}', f'{u:.3f}'] for m, _, p, a, u in months],
                        [70, 80, 80, 80], step=4, title='predictions vs outcomes', title_color='blue', focus_rows={2: '4'}))
    elems += [stext(560, 200, 'June: ranking still good (AUC), but predicted 31 % vs actual 15 %', 'red', 12, step=4),
              stext(560, 220, '→ concept drift: the market changed, recalibrate / retrain', 'red', 12, step=4),
              stext(380, 290, 'save training quantiles with the model · log every batch · alert on PSI > 0.25 · champion vs challenger before switching', 'cyan', 12, step=5)]
    return anim(canvas(760, 305, *elems), [
        'January looks like the training data: PSI below 0.1 (stable).',
        'March batches score lower in mock tests: PSI 0.216, moderate drift; predictions fall with them.',
        'June: mock scores drop further, PSI 0.759, a significant shift that should trigger an alert.',
        'When outcomes arrive, compare predicted and actual rates. AUC is still high, but the level is badly off: the job market changed (concept drift).',
        'Monitoring inputs gives early warning; outcome monitoring confirms whether to retrain.',
    ])
