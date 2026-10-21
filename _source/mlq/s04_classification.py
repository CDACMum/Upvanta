from build import *
from mlq.anims import *
from mlq.runner import mlrun, pyshow
from mlq.data import STUDENTS, data_note

S = 'Python (scikit-learn) · uses sample data'
CLF = STUDENTS + """
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
num = ['attendance', 'study_hours', 'mock_test']
cat = ['course', 'centre', 'degree']
X = df[num + cat]
y = df['placed']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
pre = ColumnTransformer([
    ('num', make_pipeline(SimpleImputer(strategy='median'), StandardScaler()), num),
    ('cat', make_pipeline(SimpleImputer(strategy='most_frequent'), OneHotEncoder(handle_unknown='ignore')), cat)])
"""
CLF_NOTE = note('Classification examples predict <code>placed</code> (1/0) from attendance, study hours, mock test, course, centre and degree, with a stratified '
                '75/25 split and the preprocessing ColumnTransformer <code>pre</code> from Q9 (median imputation + scaling for numbers, most-frequent imputation + '
                'one-hot for categories).', 'Data')

SECTION = dict(level='intermediate', title='Classification', questions=[

# ------------------------------------------------------------------ 16
Q('How does logistic regression work for classification? What do predict_proba and coefficients mean?', 'Logistic Regression', minutes=8, cards=[
    definition(
        defbox('<strong>Logistic regression</strong> computes a linear score z = b₀ + Σbᵢxᵢ and converts it to a probability with the <strong>sigmoid</strong> '
               '1/(1+e⁻ᶻ). It is trained by minimising <strong>log loss</strong> (cross-entropy). <code>predict_proba</code> returns class probabilities; '
               '<code>predict</code> applies a 0.5 threshold (for binary problems). Multi-class problems use the multinomial (softmax) form.',
               'Coefficients change the <strong>log-odds</strong>; <code>np.exp(coef)</code> gives <strong>odds ratios</strong> (with standardised features: per one '
               'standard deviation). scikit-learn applies L2 regularisation by default; <code>C</code> is the inverse strength (smaller C = stronger).'),
        tags('LogisticRegression', 'sigmoid', 'predict_proba', 'log-odds', 'odds ratio', 'C'),
    ),
    analogy('Logistic regression is a <strong>points system with a dial</strong>: every feature adds or removes points, and the dial (sigmoid) turns the total into '
            '"probability of placement" between 0 and 100 %, never below or above.'),
    logistic_anim(),
    real_world(
        scenario('Explainable risk scores',
                 p('Mentors trust the at-risk list because each student\'s probability can be explained: "low mock-test score and low study hours pulled the '
                   'probability down". Odds ratios show, for example, that one standard deviation more in mock-test score multiplies the odds of placement by about 3.5 (as in the example).')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.linear_model import LogisticRegression
            model = Pipeline([('pre', pre), ('lr', LogisticRegression(C=1.0, max_iter=1000))]).fit(X_train, y_train)

            proba = model.predict_proba(X_test)[:5]
            print(pd.DataFrame(proba, columns=['P(not placed)', 'P(placed)']).round(3).assign(predicted=model.predict(X_test)[:5]))

            names = model.named_steps['pre'].get_feature_names_out()
            coefs = pd.Series(model.named_steps['lr'].coef_[0], index=names)
            top = coefs.reindex(coefs.abs().sort_values(ascending=False).index).head(5)
            print(pd.DataFrame({'coef': top.round(3), 'odds_ratio': np.exp(top).round(2)}))
            print('test accuracy:', round(model.score(X_test, y_test), 3))
        """, setup=CLF, title=S),
        title='Example: Probabilities, Coefficients and Odds Ratios'),
    steps(
        ('Prepare features', 'Impute, encode, scale (pipeline).'),
        ('Fit', '<code>LogisticRegression(max_iter=1000)</code>; tune C with CV.'),
        ('Use probabilities', '<code>predict_proba</code>, then choose a threshold for the decision.'),
        ('Explain', 'Coefficients / odds ratios on standardised features.'),
        ('Evaluate', 'Confusion matrix, precision/recall, ROC-AUC.'),
        title='Steps for Logistic Regression'),
    crossq(
        ('Why is it called regression if it classifies?', 'It regresses the log-odds of the class linearly on the features; the classification comes from thresholding the resulting probability.'),
        ('What does a ConvergenceWarning mean?', 'The solver hit max_iter before converging; scale features and/or increase max_iter.'),
        ('Are its probabilities well calibrated?', 'Usually reasonably, because it optimises log loss; trees and SVMs often need CalibratedClassifierCV.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is a confusion matrix? Explain accuracy, precision, recall and F1-score.', 'Confusion Matrix & Metrics', minutes=8, cards=[
    definition(
        defbox('A <strong>confusion matrix</strong> counts true negatives (TN), false positives (FP), false negatives (FN) and true positives (TP). '
               '<strong>Accuracy</strong> = (TP+TN)/total. <strong>Precision</strong> = TP/(TP+FP): how many predicted positives are correct. '
               '<strong>Recall</strong> (sensitivity, TPR) = TP/(TP+FN): how many actual positives are found. <strong>F1</strong> = harmonic mean of precision and '
               'recall. <strong>Specificity</strong> = TN/(TN+FP).',
               'Choose by cost: missing a positive (FN) is expensive → recall; false alarms (FP) expensive → precision. <code>classification_report</code> shows '
               'per-class precision/recall/F1 with macro and weighted averages.'),
        tags('confusion matrix', 'precision', 'recall', 'F1', 'accuracy', 'classification_report'),
    ),
    analogy('A metal detector at an exam hall: <strong>precision</strong> is "when it beeps, is it really a phone?"; <strong>recall</strong> is "of all phones '
            'brought in, how many did it catch?". A detector that beeps for everyone has perfect recall and terrible precision.'),
    confusion_anim(),
    real_world(
        scenario('At-risk students',
                 p('Here the "positive" class that matters is "not placed" (at risk). Missing such a student (FN) costs more than an extra mentoring call (FP), so '
                   'the team reports recall for the at-risk class and accepts lower precision.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import confusion_matrix, classification_report, precision_score, recall_score, f1_score, accuracy_score
            model = Pipeline([('pre', pre), ('lr', LogisticRegression(max_iter=1000))]).fit(X_train, y_train)
            pred = model.predict(X_test)

            cm = confusion_matrix(y_test, pred)
            print(pd.DataFrame(cm, index=['actual 0', 'actual 1'], columns=['pred 0', 'pred 1']))
            tn, fp, fn, tp = cm.ravel()
            print(f'accuracy  {(tp + tn) / cm.sum():.3f} = {accuracy_score(y_test, pred):.3f}')
            print(f'precision {tp / (tp + fp):.3f} = {precision_score(y_test, pred):.3f}')
            print(f'recall    {tp / (tp + fn):.3f} = {recall_score(y_test, pred):.3f}')
            print(f'F1        {f1_score(y_test, pred):.3f}')
            print(classification_report(y_test, pred, target_names=['not placed', 'placed'], digits=3))
        """, setup=CLF, title=S),
        title='Example: Confusion Matrix, Metrics by Hand and by Function'),
    steps(
        ('Define the positive class', 'The event you care about finding.'),
        ('Compute the confusion matrix', 'On test data.'),
        ('Pick the metric from costs', 'Recall, precision, F1 or a cost-weighted measure.'),
        ('Report per class', 'classification_report; macro average for imbalanced problems.'),
        ('Adjust the threshold', 'If the precision/recall balance is wrong (next question).'),
        title='Steps to Evaluate a Classifier'),
    crossq(
        ('Why use the harmonic mean in F1?', 'It is low whenever either precision or recall is low; an arithmetic mean could hide a model with 100 % recall and 5 % precision.'),
        ('Macro vs weighted average?', 'Macro averages classes equally (highlights poor minority-class performance); weighted averages by class frequency.'),
        ('Which metric for a cancer screening test?', 'High recall (sensitivity) first, then confirm positives with a second, more precise test.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What are the ROC curve and AUC? How do you choose a classification threshold?', 'ROC-AUC & Thresholds', minutes=8, cards=[
    definition(
        defbox('The <strong>ROC curve</strong> plots true-positive rate (recall) against false-positive rate for all thresholds. <strong>AUC</strong> (area under '
               'it) measures ranking quality: the probability that a random positive gets a higher score than a random negative (0.5 random, 1.0 perfect), '
               'independent of the threshold. The <strong>precision-recall curve</strong> and <strong>average precision</strong> are more informative when positives '
               'are rare.',
               'The default 0.5 threshold is arbitrary; choose it from costs or a target (e.g. recall ≥ 0.9), using validation data, via '
               '<code>precision_recall_curve</code>/<code>roc_curve</code>, or <code>TunedThresholdClassifierCV</code> (scikit-learn 1.5+).'),
        tags('ROC', 'AUC', 'threshold', 'precision-recall curve', 'TunedThresholdClassifierCV'),
    ),
    analogy('A security scanner with a <strong>sensitivity dial</strong>: turn it up and it catches more threats but also beeps at belts and coins. The ROC curve '
            'shows every dial position at once; AUC says how good the scanner is overall, regardless of where you set the dial.'),
    roc_anim(),
    real_world(
        scenario('Mentor capacity decides the threshold',
                 p('Mentors can call about 40 % of students. Instead of 0.5, the team picks the threshold that flags that share of students, or the one reaching '
                   'recall ≥ 0.9 for at-risk students, and documents the choice with the precision it implies.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve, recall_score, precision_score
            model = Pipeline([('pre', pre), ('lr', LogisticRegression(max_iter=1000))]).fit(X_train, y_train)
            proba = model.predict_proba(X_test)[:, 1]
            print('ROC-AUC', round(roc_auc_score(y_test, proba), 3), '| average precision', round(average_precision_score(y_test, proba), 3))

            print('threshold  precision  recall  flagged')
            for t in [0.3, 0.4, 0.5, 0.6, 0.7]:
                pred = (proba >= t).astype(int)
                print(f'   {t:.1f}       {precision_score(y_test, pred):.3f}    {recall_score(y_test, pred):.3f}    {pred.sum():3d}')

            prec, rec, thr = precision_recall_curve(y_test, proba)
            ok = rec[:-1] >= 0.90
            best = thr[ok].max()
            print(f'highest threshold with recall ≥ 0.90: {best:.3f} (precision {prec[:-1][ok][thr[ok].argmax()]:.3f})')
        """, setup=CLF, title=S),
        title='Example: AUC and the Precision/Recall Trade-off Across Thresholds'),
    steps(
        ('Get probabilities', '<code>predict_proba(X)[:, 1]</code>.'),
        ('Measure ranking quality', 'ROC-AUC; PR-AUC for rare positives.'),
        ('Define the operating goal', 'Cost ratio, capacity, or minimum recall/precision.'),
        ('Pick the threshold on validation data', 'Not on the final test set.'),
        ('Apply and monitor', 'Store the threshold with the model.'),
        title='Steps to Set a Threshold'),
    crossq(
        ('Can two models with equal AUC behave differently?', 'Yes; their curves can cross, so one may be better at the threshold you actually use.'),
        ('Why is ROC-AUC optimistic for rare positives?', 'FPR divides by the huge number of negatives, so many false positives look small; precision exposes them.'),
        ('Does changing the threshold retrain the model?', 'No; it only changes how probabilities are converted to decisions.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('How do you handle imbalanced classes?', 'Imbalanced Data', minutes=8, cards=[
    definition(
        defbox('With a rare positive class, models drift towards always predicting the majority and accuracy becomes misleading. Remedies: '
               '<strong>stratified</strong> splits and CV; appropriate <strong>metrics</strong> (recall, precision, F1, PR-AUC, balanced accuracy); '
               '<strong>class_weight="balanced"</strong> (most sklearn classifiers) to weight errors on the rare class; <strong>resampling</strong> '
               '(random over/under-sampling, SMOTE from imbalanced-learn) applied <strong>only to training folds</strong> via an imblearn Pipeline; '
               '<strong>threshold tuning</strong>; and collecting more minority examples.'),
        tags('imbalanced data', 'class_weight', 'SMOTE', 'balanced accuracy', 'stratify'),
    ),
    analogy('Looking for <strong>5 defective bulbs among 100</strong>: an inspector who passes every bulb is 95 % "accurate" and completely useless. Class weights '
            'tell the inspector that missing a defect costs 19 times more than a false reject.'),
    imbalance_anim(),
    real_world(
        scenario('Dropout prediction',
                 p('Only about 5 % of students drop out. The first model had 95 % accuracy and caught no dropouts. With class_weight="balanced", recall on dropouts '
                   'became useful, at the cost of more students flagged for a check-in call, which mentors accepted.')),
    ),
    example(
        mlrun("""
            from sklearn.datasets import make_classification
            from sklearn.model_selection import train_test_split
            from sklearn.linear_model import LogisticRegression
            from sklearn.dummy import DummyClassifier
            from sklearn.metrics import accuracy_score, recall_score, precision_score, balanced_accuracy_score, average_precision_score

            X, y = make_classification(n_samples=4000, n_features=8, n_informative=4, weights=[0.95], flip_y=0.01, random_state=0)
            print('positive rate:', round(y.mean(), 3))
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y, random_state=0)

            models = [('always majority', DummyClassifier()), ('logistic', LogisticRegression(max_iter=1000)),
                      ('logistic balanced', LogisticRegression(max_iter=1000, class_weight='balanced'))]
            print('model               acc    bal_acc  recall  precision  PR-AUC')
            for name, m in models:
                m.fit(X_tr, y_tr); pred = m.predict(X_te); proba = m.predict_proba(X_te)[:, 1]
                print(f'{name:18} {accuracy_score(y_te, pred):.3f}  {balanced_accuracy_score(y_te, pred):.3f}    {recall_score(y_te, pred):.3f}'
                      f'   {precision_score(y_te, pred, zero_division=0):.3f}      {average_precision_score(y_te, proba):.3f}')
        """),
        pyshow("""
            # resampling inside cross-validation (pip install imbalanced-learn)
            from imblearn.pipeline import Pipeline as ImbPipeline
            from imblearn.over_sampling import SMOTE
            pipe = ImbPipeline([('pre', pre), ('smote', SMOTE(random_state=0)), ('model', LogisticRegression(max_iter=1000))])
            cross_val_score(pipe, X, y, cv=StratifiedKFold(5), scoring='average_precision')
        """, title='Python (imbalanced-learn, shown)'),
        title='Example: Accuracy Lies; class_weight Fixes Recall'),
    steps(
        ('Measure imbalance', '<code>y.value_counts(normalize=True)</code>.'),
        ('Stratify', 'Splits and CV folds.'),
        ('Choose metrics', 'Recall/precision/F1/PR-AUC/balanced accuracy, not accuracy.'),
        ('Rebalance training', 'class_weight first; resampling inside the pipeline if needed.'),
        ('Tune the threshold', 'For the desired recall/precision.'),
        title='Steps for Imbalanced Problems'),
    crossq(
        ('Why must SMOTE go inside the CV pipeline?', 'Oversampling before splitting creates synthetic points derived from validation rows, leaking information and inflating scores.'),
        ('Does class_weight change probabilities?', 'Yes, it shifts them towards the rare class (they are no longer calibrated to true frequencies); recalibrate if probabilities themselves matter.'),
        ('Why did PR-AUC go DOWN with class_weight here?', 'class_weight changes the loss being optimised, mainly moving the decision boundary; it does not guarantee better ranking, and here ranking got worse. An alternative is to keep the unweighted model and lower its threshold; compare both on validation data.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('How do K-Nearest Neighbours and Naive Bayes classifiers work? When would you use them?', 'KNN & Naive Bayes', minutes=7, cards=[
    definition(
        defbox('<strong>KNN</strong> stores the training data and predicts by a majority vote (or average, for regression) of the <strong>k nearest</strong> '
               'points under a distance metric. Key choices: k (small k → overfit, large k → underfit), distance, <code>weights="distance"</code>. Requires scaled '
               'features; prediction is slow on large data; suffers in high dimensions.',
               '<strong>Naive Bayes</strong> applies Bayes\' theorem assuming features are independent given the class. <code>GaussianNB</code> for continuous '
               'features, <code>MultinomialNB</code>/<code>ComplementNB</code> for counts (text), <code>BernoulliNB</code> for binary features. Very fast, works with '
               'little data, a strong baseline for text, but probabilities are often poorly calibrated.'),
        tags('KNN', 'KNeighborsClassifier', 'Naive Bayes', 'GaussianNB', 'MultinomialNB'),
    ),
    analogy('KNN is asking <strong>your five closest neighbours</strong> how they voted to guess your vote. Naive Bayes is a <strong>doctor using symptom '
            'checklists</strong>, treating each symptom as separate evidence and multiplying the odds.'),
    knn_nb_anim(),
    real_world(
        scenario('Quick baselines',
                 p('KNN gives an intuitive "students like you" explanation for placement chances; Naive Bayes classifies helpdesk emails (fees, exams, '
                   'hostel) from their words in milliseconds.')),
    ),
    example(
        CLF_NOTE,
        mlrun("""
            from sklearn.neighbors import KNeighborsClassifier
            from sklearn.naive_bayes import GaussianNB
            from sklearn.model_selection import cross_val_score
            print(' k   CV accuracy')
            for k in [1, 5, 15, 31, 61]:
                pipe = Pipeline([('pre', pre), ('knn', KNeighborsClassifier(n_neighbors=k))])
                print(f'{k:2}   {cross_val_score(pipe, X_train, y_train, cv=5).mean():.3f}')

            nb = Pipeline([('pre', ColumnTransformer([('num', make_pipeline(SimpleImputer(strategy='median')), num)])), ('nb', GaussianNB())])
            print('GaussianNB CV accuracy', round(cross_val_score(nb, X_train, y_train, cv=5).mean(), 3))
            nb.fit(X_train, y_train)
            print('class priors:', nb.named_steps['nb'].class_prior_.round(3), '| per-class means:')
            print(pd.DataFrame(nb.named_steps['nb'].theta_, columns=num, index=['not placed', 'placed']).round(1))
        """, setup=CLF, title=S),
        title='Example: Choosing k for KNN, and What GaussianNB Learns'),
    steps(
        ('KNN', 'Scale features, tune k (odd numbers for binary), try weights="distance".'),
        ('Naive Bayes', 'Pick the variant that matches feature types; no scaling needed.'),
        ('Compare with CV', 'Against logistic regression and trees.'),
        ('Use as baselines', 'Or in ensembles; KNN for small, low-dimensional data.'),
        title='Steps to Use KNN and Naive Bayes'),
    crossq(
        ('Why is k = 1 usually a bad choice?', 'The prediction copies the single nearest point, including its noise: very high variance (training accuracy 100 %).'),
        ('What is the curse of dimensionality for KNN?', 'In many dimensions all points become almost equally far apart, so "nearest" loses meaning; reduce dimensions (PCA) or use other models.'),
        ('Why is Naive Bayes good for text despite the wrong independence assumption?', 'Classification only needs the correct class to score highest, not accurate probabilities; word evidence adds up well even if correlated.'),
    ),
]),
])
