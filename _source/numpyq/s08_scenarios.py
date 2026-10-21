from build import *
from numpyq.anims import *
from numpyq.runner import nprun, pyshow

SECTION = dict(level='expert', title='Scenario-Based Questions', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: standardise marks per subject and flag unusual results.', 'z-scores & Outliers', minutes=8, tag='Scenario', cards=[
    definition(
        defbox('A <strong>z-score</strong> expresses a value as standard deviations from its column mean: <code>z = (x − mean) / std</code>, computed for '
               'all subjects at once with broadcasting along axis 0. Values with |z| above a threshold (2 or 3 for large samples) are flagged. A more robust '
               'alternative uses the median and the median absolute deviation (MAD), which outliers barely affect.'),
        tags('z-score', 'standardisation', 'outliers', 'MAD', 'broadcasting'),
    ),
    analogy('A mark of 70 means different things in an easy paper and a hard one. The z-score is <strong>"how far above or below the class"</strong>, a common '
            'currency for comparing subjects, and the far ends of that scale are where you look for mistakes or students who need support.'),
    zscore_anim(),
    real_world(
        scenario('Moderation and data checks',
                 p('Before publishing, z-scores per subject highlight a 20 in a subject where everyone else scored 60–90: either a data-entry error (2O typed as 20) '
                   'or a student to contact. Comparing a student\'s average z across subjects also identifies consistent strengths independent of paper difficulty.')),
    ),
    example(
        nprun("""
            marks = np.array([[82, 61, 70],
                              [91, 88, 79],
                              [84, 72, 66],
                              [20, 66, 74],
                              [78, 59, 81]], dtype=float)
            subjects = np.array(['SQL', 'Spark', 'ML'])

            z = (marks - marks.mean(axis=0)) / marks.std(axis=0)
            print(z.round(2))
            r, c = np.nonzero(np.abs(z) > 1.5)
            print('flag:', [(int(i), str(subjects[j]), float(marks[i, j])) for i, j in zip(r, c)])

            med = np.median(marks, axis=0)
            mad = np.median(np.abs(marks - med), axis=0)
            robust = 0.6745 * (marks - med) / mad
            print(robust.round(2)[:, 0])
            print('student strength (mean z):', z.mean(axis=1).round(2))
        """),
        title='Example: Column z-scores, Flags, Robust MAD Version'),
    steps(
        ('Arrange data', 'Rows = students, columns = subjects (float).'),
        ('Compute per-column statistics', 'mean/std (or median/MAD) with axis=0.'),
        ('Broadcast', '(n, k) − (k,) works directly.'),
        ('Flag', '<code>np.abs(z) &gt; threshold</code>; get positions with np.nonzero.'),
        ('Review, do not auto-correct', 'Flags are for human checking.'),
        title='Steps to Standardise and Flag'),
    crossq(
        ('Why can a big outlier hide itself?', 'It inflates the std (and shifts the mean), shrinking its own z-score; MAD-based scores resist this.'),
        ('What is 0.6745 in the robust formula?', 'It makes MAD comparable to the standard deviation for normally distributed data.'),
        ('What if a subject has std 0?', 'Division by zero → inf/nan; guard with np.where(std == 0, 1, std) or skip that subject.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: find each student\'s two best subjects efficiently.', 'Top-k per Row', minutes=7, tag='Scenario', cards=[
    definition(
        defbox('<code>np.argpartition(a, kth, axis=1)</code> rearranges positions so the k smallest (or, with <code>-a</code>, largest) come first in each row '
               'in O(n), without full sorting. <code>np.take_along_axis(a, idx, axis=1)</code> gathers values at per-row positions. Sort only the k selected '
               'values if their order matters.'),
        tags('argpartition', 'take_along_axis', 'top-k', 'argsort'),
    ),
    analogy('Finding the two tallest students in each class does not require lining up the whole class by height; you just <strong>pull out the two tallest</strong> '
            'and then decide which of the two is taller.'),
    topk_anim(),
    real_world(
        scenario('Elective recommendations',
                 p('For 5,000 students and 40 module scores, the two strongest modules per student drive elective suggestions. argpartition + take_along_axis '
                   'handles the whole matrix in one call, and the same positions index the module names.')),
    ),
    example(
        nprun("""
            marks = np.array([[82, 61, 70, 55],
                              [91, 88, 79, 95],
                              [84, 72, 66, 90]])
            subjects = np.array(['SQL', 'Spark', 'ML', 'Python'])
            k = 2

            idx = np.argpartition(-marks, k - 1, axis=1)[:, :k]          # top-k positions, unordered
            vals = np.take_along_axis(marks, idx, axis=1)
            order = np.argsort(-vals, axis=1)                           # sort only k values
            idx = np.take_along_axis(idx, order, axis=1)
            print(subjects[idx])
            print(np.take_along_axis(marks, idx, axis=1))

            check = np.argsort(-marks, axis=1, kind='stable')[:, :k]    # full sort, for comparison
            print('same as full sort:', (np.sort(idx, 1) == np.sort(check, 1)).all())
        """),
        title='Example: Best Two Subjects per Student'),
    steps(
        ('Negate for largest', 'argpartition finds smallest; use -a for largest.'),
        ('Partition per row', 'axis=1, kth = k − 1.'),
        ('Gather values', 'take_along_axis with the same positions.'),
        ('Order the k results', 'argsort on k columns only.'),
        ('Map to labels', 'Index the names array with the positions.'),
        title='Steps for Top-k'),
    crossq(
        ('Why kth = k − 1?', 'argpartition guarantees the element at position kth is in sorted position, with all smaller ones before it; positions 0..k−1 then hold the k smallest.'),
        ('What about ties?', 'argpartition/argsort pick among ties arbitrarily (or by position with stable sort); define a tie-break rule if it matters.'),
        ('How is this done in pandas?', 'df.apply(lambda r: r.nlargest(2).index.tolist(), axis=1) — readable but row-by-row; NumPy does all rows at once.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: implement linear regression from scratch with NumPy.', 'Linear Regression from Scratch', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('Linear regression finds weights w minimising squared error ‖Xw − y‖². With an intercept column of ones in X: <strong>closed form</strong> '
               '<code>w = solve(XᵀX, Xᵀy)</code> (or <code>lstsq</code>, more stable); <strong>gradient descent</strong> repeats '
               '<code>w -= lr * (2/n) * Xᵀ(Xw − y)</code>, which scales to huge data and is the basis of neural-network training. Evaluate with RMSE and R².'),
        tags('linear regression', 'normal equation', 'gradient descent', 'lstsq', 'R²'),
    ),
    analogy('The normal equation is <strong>solving the puzzle with algebra</strong> in one step. Gradient descent is <strong>walking downhill in fog</strong>: '
            'each step goes in the steepest downward direction until you reach the valley floor (the same answer), and a step size that is too big makes you '
            'overshoot.'),
    regression_anim(),
    real_world(
        scenario('Predicting final marks',
                 p('From attendance percentage and weekly study hours, predict the final exam mark to identify students at risk early. The from-scratch version '
                   'is the classic PG-DBDA interview exercise and shows you understand what <code>LinearRegression().fit()</code> does.')),
    ),
    example(
        nprun("""
            rng = np.random.default_rng(10)
            n = 200
            attendance = rng.uniform(55, 100, n)
            hours = rng.uniform(0, 15, n)
            y = 10 + 0.5 * attendance + 2.0 * hours + rng.normal(0, 4, n)      # true: 10, 0.5, 2.0

            X = np.column_stack([np.ones(n), attendance, hours])
            w_closed = np.linalg.solve(X.T @ X, X.T @ y)
            print('normal equation :', w_closed.round(3))

            mu, sd = X[:, 1:].mean(0), X[:, 1:].std(0)
            Xs = np.column_stack([np.ones(n), (X[:, 1:] - mu) / sd])          # scale for gradient descent
            w = np.zeros(3)
            for _ in range(2000):
                w -= 0.05 * (2 / n) * Xs.T @ (Xs @ w - y)
            w_gd = np.r_[w[0] - (w[1:] * mu / sd).sum(), w[1:] / sd]           # back to original units
            print('gradient descent:', w_gd.round(3))

            pred = X @ w_closed
            rmse = np.sqrt(np.mean((pred - y) ** 2))
            r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
            print(f'RMSE {rmse:.2f} | R² {r2:.3f}')
            print('prediction for 90% attendance, 10 h/week:', (np.array([1, 90, 10]) @ w_closed).round(1))
        """),
        title='Example: Closed Form vs Gradient Descent on Simulated Data'),
    steps(
        ('Build X', 'Column of ones + feature columns; y as a 1-D array.'),
        ('Closed form', '<code>np.linalg.lstsq(X, y)</code> or solve(XᵀX, Xᵀy).'),
        ('Gradient descent', 'Standardise features, choose lr, iterate, monitor loss.'),
        ('Evaluate', 'RMSE, R²; ideally on a held-out split.'),
        ('Interpret', 'Each weight = change in y per unit of that feature, others fixed.'),
        title='Steps to Fit a Linear Model'),
    crossq(
        ('Why scale features for gradient descent?', 'Features on very different scales make the loss surface elongated; one learning rate is too big for one direction and too small for another, so convergence is slow or unstable.'),
        ('When would the normal equation fail?', 'When XᵀX is singular or ill-conditioned (duplicate/collinear features) or when there are very many features; use lstsq/regularisation or gradient methods.'),
        ('What does R² = 0.85 mean?', '85 % of the variance in y around its mean is explained by the model on this data.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: find the most similar students using cosine similarity.', 'Cosine Similarity', minutes=8, tag='Scenario', cards=[
    definition(
        defbox('<strong>Cosine similarity</strong> between vectors a and b is <code>a·b / (‖a‖‖b‖)</code>: 1 for the same direction, 0 for orthogonal. For a '
               'matrix X (rows = items), normalise rows (<code>U = X / norm(X, axis=1, keepdims=True)</code>) and compute <code>S = U @ U.T</code> for all pairs at '
               'once. It compares the <strong>pattern</strong>, not the level; centring each row first gives Pearson correlation, which is often more meaningful '
               'for marks.'),
        tags('cosine similarity', 'normalisation', 'recommendation', 'correlation', 'nearest neighbours'),
    ),
    analogy('Two students pointing in the <strong>same direction</strong> are similar even if one walked further: cosine measures the <strong>angle</strong>, not '
            'the distance. If distance matters too, use Euclidean distance; if you care about ups and downs relative to each student\'s own average, use correlation.'),
    cosine_anim(),
    real_world(
        scenario('Peer-study groups',
                 p('Students are represented by their scores in 12 modules. Correlation-based similarity groups students with similar strengths and weaknesses for '
                   'peer study; the same technique (on ratings or embeddings) drives course and content recommendations.')),
    ),
    example(
        nprun("""
            names = np.array(['Anuj', 'Vineeta', 'Rohan', 'Meera'])
            X = np.array([[82, 61, 70, 55],
                          [91, 88, 79, 95],
                          [41, 30, 35, 28],         # same pattern as Anuj, much lower level
                          [60, 85, 58, 90]], dtype=float)

            U = X / np.linalg.norm(X, axis=1, keepdims=True)
            S = U @ U.T
            print(S.round(3))

            C = X - X.mean(axis=1, keepdims=True)                     # centre each student
            Uc = C / np.linalg.norm(C, axis=1, keepdims=True)
            R = Uc @ Uc.T                                             # = Pearson correlation
            print(R.round(2))
            print(np.allclose(R, np.corrcoef(X)))

            for i, name in enumerate(names):
                best = [j for j in np.argsort(-R[i]) if j != i][0]
                print(f'{name:8} most similar pattern: {names[best]} ({R[i, best]:.2f})')
        """),
        title='Example: Cosine vs Correlation and Nearest Neighbour'),
    steps(
        ('Build the item × feature matrix', 'One row per student.'),
        ('Decide what "similar" means', 'Pattern (cosine), relative pattern (correlation), absolute (Euclidean).'),
        ('Normalise rows', 'Divide by the L2 norm (after centring for correlation).'),
        ('All pairs', 'U @ U.T.'),
        ('Neighbours', 'argsort each row, skip the diagonal.'),
        title='Steps for Similarity Search'),
    crossq(
        ('Why is Anuj–Rohan cosine almost 1?', 'Their mark vectors point in nearly the same direction (Rohan ≈ half of Anuj in every subject); cosine ignores magnitude.'),
        ('How does this scale to millions of items?', 'n × n is too big; use approximate nearest-neighbour libraries (FAISS, Annoy) or block-wise computation with top-k.'),
        ('Cosine distance?', '1 − cosine similarity; used by clustering and nearest-neighbour algorithms.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Scenario: use simulation to answer probability questions (guessing an MCQ exam, confidence interval of a mean).', 'Monte Carlo & Bootstrap', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('<strong>Monte Carlo simulation</strong> estimates probabilities by generating many random trials and counting outcomes; with NumPy, trials are rows of '
               'an array, so millions run in milliseconds. <strong>Bootstrap</strong> estimates the uncertainty of a statistic by resampling the observed data '
               'with replacement many times and looking at the spread (percentiles) of the statistic.'),
        tags('Monte Carlo', 'bootstrap', 'simulation', 'confidence interval', 'random'),
    ),
    analogy('Instead of working out the odds of a card game on paper, you <strong>play it a million times</strong> very quickly and count how often you win. '
            'Bootstrap is <strong>re-drawing your class from itself</strong> many times to see how much the average could wobble.'),
    montecarlo_anim(),
    real_world(
        scenario('Exam design and reporting',
                 p('Is a pass mark of 8/20 in a 4-option MCQ test safe against pure guessing? Simulation (checked against the binomial formula) answers it. When '
                   'reporting a batch average to management, a bootstrap 95 % interval shows how precise that average is for a batch of 40 students.')),
    ),
    example(
        nprun("""
            from math import comb
            rng = np.random.default_rng(99)
            trials, q, p = 200_000, 20, 0.25
            correct = (rng.random((trials, q)) < p).sum(axis=1)          # each row = one guessed exam
            print('simulated P(score >= 8):', (correct >= 8).mean().round(4))
            exact = sum(comb(q, k) * p**k * (1 - p)**(q - k) for k in range(8, q + 1))
            print('exact binomial         :', round(exact, 4))
            print('most likely score      :', np.bincount(correct).argmax())

            marks = rng.normal(68, 12, 40).round()                       # one batch of 40 students
            boots = rng.choice(marks, size=(10_000, marks.size), replace=True).mean(axis=1)
            lo, hi = np.percentile(boots, [2.5, 97.5])
            print(f'batch mean {marks.mean():.1f}, bootstrap 95% CI [{lo:.1f}, {hi:.1f}]')
            se = marks.std(ddof=1) / np.sqrt(marks.size)
            print(f'normal-theory CI      [{marks.mean() - 1.96 * se:.1f}, {marks.mean() + 1.96 * se:.1f}]')
        """),
        title='Example: Guessing Probability (Checked Exactly) and a Bootstrap Interval'),
    steps(
        ('Model one trial', 'What is random and what is counted.'),
        ('Vectorise trials', 'One row per trial: rng.random((trials, steps)).'),
        ('Count outcomes', 'Means of boolean conditions are probabilities.'),
        ('Check convergence', 'Increase trials; compare with exact results when available.'),
        ('Bootstrap', 'Resample with replacement, compute the statistic per row, take percentiles.'),
        title='Steps for Simulation'),
    crossq(
        ('How accurate is a Monte Carlo estimate?', 'Its standard error is about sqrt(p(1−p)/trials): 200,000 trials give roughly ±0.001 for p ≈ 0.1.'),
        ('When is bootstrap useful?', 'For statistics without simple formulas (median, percentiles, ratios) or when distribution assumptions are doubtful.'),
        ('Why fix the seed?', 'So the exact numbers in a report can be reproduced; the conclusions should not depend on the seed.'),
    ),
]),
])
