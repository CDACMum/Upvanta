from build import *
from numpyq.anims import *
from numpyq.runner import nprun, pyshow

SECTION = dict(level='intermediate', title='Linear Algebra, Statistics & Random', questions=[

# ------------------------------------------------------------------ 21
Q('What is the difference between *, np.dot, np.matmul (@) and np.multiply?', 'dot vs matmul vs *', minutes=7, cards=[
    definition(
        defbox('<code>*</code> / <code>np.multiply</code>: <strong>element-wise</strong> product (broadcasting rules).',
               '<code>@</code> / <code>np.matmul</code>: <strong>matrix product</strong>: (m × n) @ (n × p) → (m × p). For 1-D arrays it is the inner product; '
               'for 3-D+ arrays it treats leading axes as a <strong>batch</strong> and broadcasts them. Scalars are not allowed.',
               '<code>np.dot</code>: same as @ for 1-D and 2-D; for higher dimensions it uses a different rule (sum over the last axis of a and second-to-last of b) '
               'and accepts scalars. Prefer <code>@</code> in new code. <code>np.inner</code>, <code>np.outer</code>, <code>np.vdot</code> cover special cases.'),
        tags('matmul', '@', 'dot', 'multiply', 'linear algebra'),
    ),
    analogy('Element-wise <code>*</code> is pairing each student\'s marks with the <strong>same position</strong> on a bonus sheet. Matrix <code>@</code> is a '
            '<strong>weighted total</strong>: each student\'s row is combined with the weight column into one number, like computing a final score from components.'),
    matmul_anim(),
    real_world(
        scenario('Weighted scores and neural networks',
                 p('Final scores for 500 students and 4 components: <code>marks @ weights</code>. A dense neural-network layer is <code>X @ W + b</code>, '
                   'and a batch of inputs (batch, features) times weights (features, units) gives (batch, units).')),
    ),
    example(
        nprun("""
            marks   = np.array([[82, 61, 70], [91, 88, 79]])
            weights = np.array([0.5, 0.3, 0.2])

            print(marks * weights)               # element-wise (broadcast)
            print(marks @ weights)               # weighted total per student
            print(np.dot(marks, weights), (marks * weights).sum(axis=1))

            A = np.arange(6).reshape(2, 3); B = np.arange(6).reshape(3, 2)
            print(A @ B)
            print((np.ones((64, 3, 4)) @ np.ones((4, 2))).shape)     # batched
            print(np.array([1, 2, 3]) @ np.array([4, 5, 6]))
            try:
                A @ A
            except ValueError as e:
                print('ValueError:', e)
        """),
        title='Example: Element-wise vs Matrix Product, Batches, Shape Errors'),
    steps(
        ('Decide the operation', 'Same-position products → *; sums of products (weights, projections) → @.'),
        ('Check inner dimensions', 'Columns of the left = rows of the right.'),
        ('Use @ for clarity', 'np.dot only when you need its n-D semantics.'),
        ('Batch work', 'Stack matrices along a first axis and use @.'),
        title='Steps for Matrix Products'),
    crossq(
        ('Is A @ B equal to B @ A?', 'Generally no: matrix multiplication is not commutative (and the shapes may not even allow the reverse).'),
        ('What does (A * B).sum() compute for equal shapes?', 'The Frobenius inner product, equal to np.trace(A.T @ B) or np.einsum("ij,ij->", A, B).'),
        ('Why is @ so fast?', 'It calls optimised BLAS libraries (OpenBLAS, MKL) with cache blocking, SIMD and multi-threading.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('How do you solve linear equations, invert matrices and find eigenvalues with NumPy?', 'np.linalg', minutes=8, cards=[
    definition(
        defbox('<code>np.linalg</code> provides: <code>solve(A, b)</code> (Ax = b), <code>inv</code>, <code>det</code>, <code>matrix_rank</code>, '
               '<code>norm</code>, <code>eig</code>/<code>eigh</code> (eigenvalues/vectors; eigh for symmetric matrices), <code>svd</code>, <code>lstsq</code> '
               '(least-squares solution), <code>qr</code>, <code>cholesky</code>, <code>pinv</code>.',
               'Prefer <code>solve</code> over <code>inv(A) @ b</code>: it is faster and numerically more stable. A singular matrix raises '
               '<code>LinAlgError</code>.'),
        tags('linalg', 'solve', 'inv', 'eig', 'svd', 'lstsq'),
    ),
    analogy('<code>solve</code> is asking a shopkeeper "2 notebooks and 3 pens cost ₹23; 1 notebook and 4 pens cost ₹24: what does each cost?" and getting the '
            'answer directly, instead of first building a full <strong>price-decoding table</strong> (the inverse) and then reading it.'),
    linalg_anim(),
    real_world(
        scenario('Regression and PCA',
                 p('Linear regression coefficients are a least-squares problem: <code>np.linalg.lstsq(X, y)</code>. PCA uses the eigenvectors of the covariance '
                   'matrix (or the SVD of centred data) to find the directions of greatest variance in student performance data.')),
    ),
    example(
        nprun("""
            A = np.array([[2, 3], [1, 4]]); b = np.array([23, 24])
            x = np.linalg.solve(A, b)
            print(x, np.allclose(A @ x, b))
            print(np.linalg.inv(A) @ b, round(np.linalg.det(A), 6), np.linalg.matrix_rank(A))

            S = np.array([[2.0, 1.0], [1.0, 2.0]])          # symmetric
            vals, vecs = np.linalg.eigh(S)
            print(vals, np.allclose(S @ vecs, vecs * vals))

            X = np.c_[np.ones(4), [1, 2, 3, 4]]             # intercept + feature
            y = np.array([52, 61, 69, 80])
            coef, *_ = np.linalg.lstsq(X, y)
            print('intercept, slope:', coef.round(2))
            try:
                np.linalg.solve([[1, 2], [2, 4]], [1, 2])
            except np.linalg.LinAlgError as e:
                print('LinAlgError:', e)
        """),
        title='Example: solve, inv, eigh, lstsq, a Singular Matrix'),
    steps(
        ('Write the system as A @ x = b', 'Coefficients in A, constants in b.'),
        ('Square and well-conditioned?', 'np.linalg.solve.'),
        ('More equations than unknowns?', 'np.linalg.lstsq (best fit).'),
        ('Symmetric matrix decompositions', 'eigh (faster, real results) instead of eig.'),
        ('Verify', 'np.allclose(A @ x, b); check np.linalg.cond(A) for ill-conditioning.'),
        title='Steps to Solve Linear Problems'),
    crossq(
        ('Why avoid computing the inverse?', 'It costs more operations and amplifies rounding errors; solve uses an LU factorisation directly.'),
        ('What does the determinant tell you?', 'Zero → singular (no unique solution); its magnitude is the volume scaling factor. Near-zero determinants are not a reliable test of near-singularity; use cond().'),
        ('eig vs eigh?', 'eigh assumes a symmetric/Hermitian matrix: guaranteed real eigenvalues in ascending order, faster and more accurate.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How do you compute statistics (mean, median, std, percentile, correlation) in NumPy?', 'Statistics', minutes=7, cards=[
    definition(
        defbox('NumPy offers <code>mean</code>, <code>average</code> (weighted), <code>median</code>, <code>std</code>/<code>var</code> (<code>ddof</code> '
               'controls population vs sample), <code>min</code>/<code>max</code>/<code>ptp</code>, <code>percentile</code>/<code>quantile</code>, '
               '<code>histogram</code>, <code>bincount</code>, <code>cov</code> and <code>corrcoef</code>, all with <code>axis</code> support and nan-versions.',
               'Important default: <code>np.std</code> uses <strong>ddof=0</strong> (divide by n); pandas uses ddof=1 (n − 1).'),
        tags('mean', 'median', 'std', 'ddof', 'percentile', 'corrcoef'),
    ),
    analogy('Mean is the <strong>balance point</strong> of the marks; median is the <strong>middle student</strong> in the queue; standard deviation is how far, on '
            'average, students stand from the balance point; percentile 90 is the mark below which 90 % of the queue stands.'),
    stats_anim(),
    real_world(
        scenario('Batch analysis',
                 p('Report median and interquartile range per subject (robust to a few absent zeros), check whether attendance correlates with marks '
                   '(<code>np.corrcoef</code>), and compute a weighted average across components with <code>np.average(m, weights=w)</code>.')),
    ),
    example(
        nprun("""
            m = np.array([55, 61, 70, 75, 82, 88, 91, 99])
            print(m.mean(), np.median(m), m.std().round(2), m.std(ddof=1).round(2))
            print(np.percentile(m, [25, 50, 75, 90]))
            print(np.average([82, 70, 91], weights=[0.5, 0.3, 0.2]))

            attendance = np.array([60, 70, 75, 80, 85, 88, 92, 98])
            print(np.corrcoef(attendance, m).round(3))
            counts, edges = np.histogram(m, bins=[0, 60, 70, 85, 101])
            print(counts, edges)
            print(np.bincount([0, 2, 2, 3, 3, 3]))
        """),
        title='Example: Centre, Spread, Percentiles, Correlation, Histogram'),
    steps(
        ('Centre', 'mean (sensitive to outliers) and median (robust).'),
        ('Spread', 'std/var with the right ddof; IQR from percentiles 25 and 75.'),
        ('Distribution', 'histogram/bincount.'),
        ('Relationship', 'corrcoef between variables; cov for covariance.'),
        ('Missing data', 'nan-versions (nanmedian, nanpercentile).'),
        title='Steps for Descriptive Statistics'),
    crossq(
        ('Why does ddof matter?', 'Sample std (ddof=1) corrects the bias of estimating population variance from a sample; for small n the difference is noticeable.'),
        ('mean vs average?', 'np.average supports weights; np.mean does not.'),
        ('What does a correlation of 0.99 mean here?', 'A strong linear association in this small sample; it does not prove that attendance causes higher marks.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you compute running totals, differences and moving averages in NumPy?', 'cumsum, diff, Moving Average', minutes=7, cards=[
    definition(
        defbox('<code>np.cumsum</code>/<code>cumprod</code>: running totals/products. <code>np.diff(a, n=1)</code>: differences between consecutive elements '
               '(length n − 1); <code>prepend=</code> keeps the length. <code>np.gradient</code>: central differences.',
               'Moving average: <code>np.convolve(x, np.ones(k)/k, mode="valid")</code>, or <code>sliding_window_view(x, k).mean(axis=1)</code>, or the '
               'cumulative-sum trick <code>(c[k:] - c[:-k]) / k</code> for O(n) on long series.'),
        tags('cumsum', 'diff', 'convolve', 'sliding_window_view', 'moving average'),
    ),
    analogy('A cricket innings: runs per over (data), the <strong>total so far</strong> on the scoreboard (cumsum), <strong>change from the previous over</strong> '
            '(diff), and the <strong>run rate over the last 3 overs</strong> (moving average).'),
    cumsum_anim(),
    real_world(
        scenario('Attendance and LMS activity trends',
                 p('A 7-day moving average smooths daily attendance; <code>np.diff</code> flags sudden drops; the cumulative sum of hours spent on the LMS shows '
                   'progress toward the required total for each student.')),
    ),
    example(
        nprun("""
            from numpy.lib.stride_tricks import sliding_window_view
            x = np.array([52, 55, 49, 58, 60, 57])
            print(np.cumsum(x), np.diff(x), np.diff(x, prepend=x[0]))
            print(np.convolve(x, np.ones(3) / 3, mode='valid').round(1))
            print(sliding_window_view(x, 3))
            print(sliding_window_view(x, 3).mean(axis=1).round(1))
            c = np.cumsum(np.insert(x, 0, 0))
            print(((c[3:] - c[:-3]) / 3).round(1))           # O(n) moving average
            print('drops:', np.where(np.diff(x) < -5)[0] + 1)
        """),
        title='Example: Three Ways to a Moving Average'),
    steps(
        ('Sort by time', 'Window operations assume order.'),
        ('Running totals', 'cumsum.'),
        ('Changes', 'diff (and pct change = diff / previous).'),
        ('Smoothing', 'convolve or sliding_window_view; mode decides edge handling.'),
        ('Per entity', 'Apply per row of a 2-D array with axis=1, or use pandas groupby for ragged data.'),
        title='Steps for Sequence Calculations'),
    crossq(
        ('convolve modes?', '"full" (all overlaps, length n+k−1), "same" (length n, partial windows at edges), "valid" (only full windows, length n−k+1).'),
        ('Is sliding_window_view a copy?', 'No, a read-only view using strides; reductions on it allocate only the result.'),
        ('Weighted moving average?', 'Use non-uniform weights in convolve (remember convolve flips the kernel; use np.correlate or reverse weights).'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('How do you generate random numbers in NumPy? What is a seed and why does it matter?', 'Random Numbers & Seeds', minutes=7, cards=[
    definition(
        defbox('Modern API: <code>rng = np.random.default_rng(seed)</code> creates a <strong>Generator</strong> (PCG64). Methods: <code>integers</code>, '
               '<code>random</code>, <code>normal</code>, <code>uniform</code>, <code>binomial</code>, <code>poisson</code>, <code>choice</code>, '
               '<code>permutation</code>, <code>shuffle</code>.',
               'A <strong>seed</strong> initialises the generator\'s state: the same seed reproduces the same sequence, essential for repeatable experiments and '
               'tests. The legacy API (<code>np.random.seed</code>, <code>np.random.rand</code>) uses one hidden global state and is kept only for compatibility.'),
        tags('default_rng', 'Generator', 'seed', 'choice', 'permutation', 'reproducibility'),
    ),
    analogy('A seed is the <strong>starting page of a huge book of random digits</strong>. Two people who open the book at the same page read the same '
            '"random" numbers, which is exactly what you want when someone has to reproduce your experiment.'),
    random_anim(),
    real_world(
        scenario('Fair allocation and ML splits',
                 p('Randomly assigning 120 students to 4 lab batches: <code>rng.permutation(roll_nos).reshape(4, 30)</code> with a recorded seed, so the '
                   'allocation can be re-created if questioned. Train/test splits and model initialisation use seeds so results are reproducible.')),
    ),
    example(
        nprun("""
            rng = np.random.default_rng(2026)
            print(rng.integers(0, 101, 5), rng.random(3).round(3))
            print(rng.normal(70, 10, 5).round(1))

            rolls = np.arange(2401, 2413)
            batches = np.random.default_rng(7).permutation(rolls).reshape(3, 4)
            print(batches)
            print(np.random.default_rng(7).permutation(rolls).reshape(3, 4)[0])   # same seed, same batch 1

            print(rng.choice(['Anuj', 'Vineeta', 'Aarshvi', 'Rohan'], size=2, replace=False))
            sample = rng.normal(70, 10, 100_000)
            print(sample.mean().round(2), sample.std().round(2))
        """),
        title='Example: Draws, Reproducible Batches, Sampling'),
    steps(
        ('Create one Generator', '<code>rng = np.random.default_rng(seed)</code> at the start; pass it to functions.'),
        ('Record the seed', 'In the notebook/config, so results can be reproduced.'),
        ('Draw what you need', 'integers / random / normal / choice.'),
        ('Splits', '<code>idx = rng.permutation(n)</code>, then slice.'),
        ('Security', 'For tokens or passwords use the <code>secrets</code> module, not NumPy.'),
        title='Steps for Reproducible Randomness'),
    crossq(
        ('Does the same seed give the same numbers on every NumPy version?', 'Generators aim for stream stability, but NumPy does not guarantee identical streams across all versions/methods; record versions for strict reproducibility.'),
        ('shuffle vs permutation?', 'shuffle reorders an array in place; permutation returns a shuffled copy (or a permuted range for an int).'),
        ('How do you get independent streams for parallel workers?', 'rng.spawn(n) or SeedSequence(seed).spawn(n), one child generator per worker.'),
    ),
]),
])
