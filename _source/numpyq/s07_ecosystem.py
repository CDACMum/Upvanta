from build import *
from numpyq.anims import *
from numpyq.runner import nprun, pyshow

SECTION = dict(level='advanced', title='NumPy in Practice', questions=[

# ------------------------------------------------------------------ 31
Q('How do NumPy and pandas relate? How do you convert between them?', 'NumPy and pandas', minutes=7, cards=[
    definition(
        defbox('pandas is built on NumPy (and, since pandas 2/3, optionally Apache Arrow). A Series wraps a 1-D array plus an index; a DataFrame holds columns of '
               'arrays with labels. <code>df.to_numpy()</code> / <code>s.to_numpy()</code> return NumPy arrays (preferred over <code>.values</code>); '
               '<code>pd.DataFrame(arr, columns=...)</code> and <code>pd.Series(arr)</code> go the other way.',
               'NumPy ufuncs work directly on pandas objects and keep labels. Mixed column types convert to a common dtype, often <code>object</code>, which is slow; '
               'select numeric columns before converting.'),
        tags('to_numpy', 'pandas', 'Series', 'DataFrame', 'dtype'),
    ),
    analogy('pandas is NumPy with <strong>name tags</strong>: the same numbers, plus row and column labels. <code>to_numpy()</code> peels off the name tags when '
            'a library only wants the numbers.'),
    pandas_np_anim(),
    real_world(
        scenario('Feature matrix for a model',
                 p('Clean data in pandas (joins, missing values, categories), then <code>X = df[feature_cols].to_numpy(dtype=np.float32)</code> and '
                   '<code>y = df["placed"].to_numpy()</code> for a NumPy-based model or a custom metric. Predictions come back as arrays and are attached with '
                   '<code>df["score"] = preds</code>.')),
    ),
    example(
        nprun("""
            import pandas as pd
            df = pd.DataFrame({'name': ['Anuj', 'Vineeta', 'Rohan'],
                               'marks': [82, 91, np.nan], 'attendance': [0.92, 0.97, 0.71]})
            X = df[['marks', 'attendance']].to_numpy()
            print(X, X.dtype, type(X).__name__)
            print(df.to_numpy().dtype)                         # mixed -> object

            print(np.log(df['marks']))                         # ufunc keeps the index
            print(np.nanmean(X, axis=0))
            df['z'] = (X[:, 0] - np.nanmean(X[:, 0])) / np.nanstd(X[:, 0])
            print(df)
            print(pd.DataFrame(np.eye(2, dtype=int), columns=['a', 'b']))
        """),
        title='Example: DataFrame → Array → back'),
    steps(
        ('Select numeric columns', '<code>df.select_dtypes("number")</code>.'),
        ('Convert', '<code>to_numpy(dtype=..., na_value=...)</code>.'),
        ('Compute in NumPy', 'Vectorised maths, linear algebra.'),
        ('Attach results', 'Assign arrays as new columns (same length and order).'),
        title='Steps to Move Between pandas and NumPy'),
    crossq(
        ('to_numpy vs .values?', 'to_numpy is explicit, supports dtype/na_value/copy, and is the recommended API; .values can return pandas extension arrays.'),
        ('Does to_numpy copy?', 'For a single-dtype numeric DataFrame it may return a view; mixed types or Arrow-backed columns require a copy.'),
        ('Why is the NaN mean computed with nanmean?', 'pandas skips NaN by default, but plain NumPy mean does not; on the raw array you must use nan-functions.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('How is NumPy used to prepare data for machine learning (scaling, encoding, splitting)?', 'NumPy for ML Preprocessing', minutes=8, cards=[
    definition(
        defbox('Core preprocessing steps are short NumPy expressions: <strong>standardisation</strong> <code>(X - mu) / sigma</code> along axis 0; '
               '<strong>min-max scaling</strong>; <strong>one-hot encoding</strong> <code>np.eye(k)[codes]</code> (codes from <code>np.unique(..., return_inverse=True)</code>); '
               '<strong>shuffled train/test split</strong> with <code>rng.permutation</code>; <strong>clipping</strong> outliers.',
               'Rule: compute statistics (mean, std, min, max) on the <strong>training</strong> data only and reuse them for test data, otherwise information leaks.'),
        tags('standardisation', 'one-hot', 'train/test split', 'data leakage', 'scikit-learn'),
    ),
    analogy('Before a race, runners are put on the <strong>same starting line</strong> (scaling) and given <strong>numbered bibs</strong> (encoding). The judge '
            'sets the rules from the practice runs (training data), not from the final race (test data).'),
    ml_prep_anim(),
    real_world(
        scenario('Placement prediction',
                 p('Features: marks, attendance, project score, course. Standardise the numeric columns, one-hot encode course, split 80/20 with a fixed seed, '
                   'and save mu/sigma with the model so new students are scaled identically at prediction time.')),
    ),
    example(
        nprun("""
            rng = np.random.default_rng(42)
            n = 10
            marks = rng.integers(45, 100, n).astype(float)
            attendance = rng.uniform(0.6, 1.0, n).round(2)
            course = np.array(['DBDA', 'DAC', 'DBDA', 'DAI', 'DAC', 'DBDA', 'DAI', 'DBDA', 'DAC', 'DBDA'])
            X = np.column_stack([marks, attendance])

            idx = rng.permutation(n); train, test = idx[:8], idx[8:]
            mu, sigma = X[train].mean(axis=0), X[train].std(axis=0)      # fit on train only
            X_train = (X[train] - mu) / sigma
            X_test = (X[test] - mu) / sigma
            print(X_train.mean(axis=0).round(6) + 0.0, X_train.std(axis=0).round(6))
            print(X_test.round(2))

            cats, codes = np.unique(course, return_inverse=True)
            onehot = np.eye(len(cats), dtype=int)[codes]
            print(cats, onehot[:4], sep='\\n')
            mm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))
            print(mm.min(axis=0), mm.max(axis=0))
        """),
        title='Example: Split, Standardise Without Leakage, One-hot, Min-max'),
    steps(
        ('Fix a seed and split', '<code>idx = rng.permutation(n)</code>.'),
        ('Fit statistics on train', 'mu, sigma (or min, max) from training rows only.'),
        ('Transform both splits', 'With the same statistics.'),
        ('Encode categories', 'np.unique + np.eye, or sklearn OneHotEncoder for unseen categories.'),
        ('Persist', 'Save statistics with the model (np.savez).'),
        title='Steps to Preprocess Safely'),
    crossq(
        ('What is data leakage here?', 'Using test-set statistics (e.g. the overall mean) during training makes evaluation optimistic because the model indirectly saw test data.'),
        ('Why does std of X_train come out exactly 1?', 'Because it was standardised with its own mean and std; the test split will not be exactly 0/1, which is expected.'),
        ('When would you use scikit-learn instead?', 'For pipelines (fit/transform objects), unseen categories, sparse output and cross-validation; the maths is the same.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What changed in NumPy 2.0? What breaks when upgrading old code?', 'NumPy 2.x Changes', minutes=8, cards=[
    definition(
        defbox('NumPy 2.0 (June 2024) was the first major release since 2006. Key changes: <strong>NEP 50 type promotion</strong> (Python scalars are "weak"; '
               '<code>float32_array * 3.0</code> stays float32; out-of-range Python ints raise <code>OverflowError</code>); <strong>scalar repr</strong> shows '
               'the type (<code>np.float64(3.0)</code>); <strong>namespace clean-up</strong> (aliases like <code>np.float_</code>, <code>np.Inf</code>, '
               '<code>np.NaN</code>, <code>np.product</code> removed; later releases also removed <code>np.in1d</code>, <code>np.row_stack</code>, '
               '<code>np.trapz</code>); stricter <code>copy=False</code>; new <code>StringDType</code>; and an <strong>ABI break</strong> requiring compiled '
               'packages to be rebuilt.'),
        tags('NumPy 2.0', 'NEP 50', 'migration', 'NPY201', 'StringDType'),
    ),
    analogy('A city renaming and merging old street names: the city works better afterwards, but <strong>old maps</strong> (old code) send you to streets that '
            'no longer exist until you update them.'),
    np2_anim(),
    real_world(
        scenario('Lab machines upgraded',
                 p('A student project failed with <code>AttributeError: np.float_ was removed in the NumPy 2.0 release. Use np.float64 instead.</code> and an old '
                   'compiled package crashed on import. Running <code>ruff check --select NPY201</code> listed every removed alias; upgrading the package fixed the '
                   'crash.')),
    ),
    example(
        nprun("""
            print(np.__version__)
            print(repr(np.float64(3.0)), repr(np.int64(2) + 1))

            x = np.ones(3, dtype=np.float32)
            print((x * 3.0).dtype, (x * np.float64(3.0)).dtype)    # weak Python float vs strong NumPy float64
            try:
                np.uint8(250) + 300
            except OverflowError as e:
                print('OverflowError:', e)

            for name in ['float_', 'NaN', 'Inf', 'product', 'in1d', 'row_stack', 'trapz']:
                print(f'np.{name:9} exists: {hasattr(np, name)}')
            print('replacements:', ', '.join(f.__name__ for f in [np.float64, np.prod, np.isin, np.vstack, np.trapezoid]), np.nan, np.inf)
            try:
                np.array(np.arange(3), dtype=float, copy=False)
            except ValueError as e:
                print('ValueError:', str(e).splitlines()[0])
        """),
        title='Example: Promotion, repr, Removed Names, copy=False'),
    steps(
        ('Run the linter', '<code>ruff check --select NPY201 .</code> rewrites/flags removed APIs.'),
        ('Replace aliases', 'np.float_ → np.float64, np.NaN → np.nan, np.in1d → np.isin, np.row_stack → np.vstack, np.trapz → np.trapezoid.'),
        ('Review dtype-sensitive maths', 'Float32 pipelines now stay float32; check precision.'),
        ('Fix copy=False', 'Use np.asarray when "copy only if needed" was meant.'),
        ('Upgrade compiled dependencies', 'pandas, SciPy, scikit-learn, etc. built for NumPy 2.'),
        title='Steps to Migrate to NumPy 2'),
    crossq(
        ('Why change type promotion?', 'The old value-based rules made result dtypes depend on the values, not the types, causing surprising upcasts and inconsistent behaviour between scalars and arrays.'),
        ('Does the repr change affect calculations?', 'No, only how scalars print; use float(x) or x.item() when you need plain Python numbers for display.'),
        ('Can NumPy 1.x code run unchanged?', 'Most of it, yes; the common failures are removed aliases, copy=False semantics, and old compiled extensions.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How are images represented as NumPy arrays? Show basic image operations.', 'Images as Arrays', minutes=7, cards=[
    definition(
        defbox('A grayscale image is a 2-D array (height, width) of intensities; a colour image is 3-D (height, width, channels), usually uint8 0–255 '
               '(RGB in Pillow/Matplotlib, BGR in OpenCV). Libraries such as Pillow, OpenCV, imageio and scikit-image read images into NumPy arrays.',
               'Operations are array operations: crop (slicing), flip (negative step), rotate (<code>np.rot90</code>), grayscale (weighted channel sum), '
               'brightness (add + clip), threshold (comparison), normalisation for deep learning (<code>/ 255.0</code>), batching (<code>np.stack</code>).'),
        tags('image', 'uint8', 'channels', 'crop', 'OpenCV', 'Pillow'),
    ),
    analogy('A digital photo is a <strong>huge graph-paper sheet</strong> where each square holds a brightness number (or three numbers for colour). Editing '
            'the photo is doing arithmetic on the sheet.'),
    image_anim(),
    real_world(
        scenario('Face attendance system',
                 p('Camera frames arrive as (480, 640, 3) uint8 arrays; the face region is cropped by slicing, resized, converted to float32 and normalised, and '
                   'a batch of faces is stacked into (n, 112, 112, 3) before going to the recognition model.')),
    ),
    example(
        nprun("""
            h, w = 4, 6
            img = np.zeros((h, w, 3), dtype=np.uint8)
            img[:, :3] = [255, 0, 0]                      # left half red
            img[:, 3:] = [0, 128, 255]                    # right half blue-ish
            print(img.shape, img.dtype, img[0, 0], img[0, -1])

            gray = (img @ np.array([0.299, 0.587, 0.114])).astype(np.uint8)
            print(gray)
            print(img[1:3, 2:5].shape, np.shares_memory(img, img[1:3, 2:5]))   # crop is a view
            print(np.rot90(gray).shape, gray[:, ::-1][0])
            print((gray > 100).astype(np.uint8))         # threshold mask
            bright = np.clip(gray.astype(np.int16) + 120, 0, 255).astype(np.uint8)
            print(gray[0, 0], '->', bright[0, 0], '| without clip:', (gray + 120)[0, -1])
            print((img / 255.0).astype(np.float32).max(), np.stack([img, img]).shape)
        """),
        title='Example: A Tiny Image Through Common Operations'),
    steps(
        ('Load', '<code>np.asarray(PIL.Image.open(path))</code> or <code>cv2.imread</code> (BGR!).'),
        ('Check', 'shape (H, W, C), dtype uint8, value range.'),
        ('Transform', 'Slice, flip, weighted sums, comparisons.'),
        ('Avoid overflow', 'Upcast before arithmetic, clip, cast back.'),
        ('Prepare for models', 'float32, scale to 0–1 or standardise, stack into a batch.'),
        title='Steps for Image Processing with NumPy'),
    crossq(
        ('Why does adding 120 to a bright pixel make it dark?', 'uint8 wraps: 226 + 120 = 346 → 346 − 256 = 90.'),
        ('RGB vs BGR?', 'OpenCV stores channels in BGR order; reverse with img[..., ::-1] when mixing with RGB libraries.'),
        ('How big is a 1080p colour frame?', '1080 × 1920 × 3 bytes ≈ 6.2 MB as uint8; four times that as float32.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How do you convert a nested-loop algorithm into vectorised NumPy code?', 'From Loops to Vectors', minutes=8, cards=[
    definition(
        defbox('A systematic approach: (1) write the clear loop version first and keep it as a test oracle; (2) turn each loop into an <strong>array axis</strong> '
               '(often via broadcasting with <code>[:, None]</code>); (3) turn <code>if</code> into a <strong>mask</strong>; (4) turn counters/totals into '
               '<strong>reductions</strong> (<code>sum</code>, <code>any</code>, <code>max</code>) and running values into <code>cumsum</code>/<code>maximum.accumulate</code>; '
               '(5) check the memory of intermediate arrays; (6) verify the results are identical.'),
        tags('vectorisation', 'broadcasting', 'refactoring', 'algorithm'),
    ),
    analogy('Instead of a teacher walking to each student and comparing them with every classmate one by one, the class lines up on a <strong>grid</strong> and '
            'all comparisons happen at once; then each row of the grid is counted.'),
    loop2vec_anim(),
    real_world(
        scenario('Rank and "students within 5 marks"',
                 p('A merit-list script used a double loop to compute each student\'s rank and how many classmates scored within ±5 marks. For 3,000 students it '
                   'took a few seconds per run; the broadcast version gives the same numbers in milliseconds, and a sort-based rank scales to millions.')),
    ),
    example(
        nprun("""
            import time
            rng = np.random.default_rng(3)
            total = rng.integers(150, 300, 2000)

            def loop_version(t):
                n = len(t); rank = np.empty(n, int); near = np.empty(n, int)
                for i in range(n):
                    higher = close = 0
                    for j in range(n):
                        if t[j] > t[i]: higher += 1
                        if j != i and abs(t[j] - t[i]) <= 5: close += 1
                    rank[i], near[i] = higher + 1, close
                return rank, near

            def vector_version(t):
                diff = t[None, :] - t[:, None]                 # (n, n): t[j] - t[i]
                rank = (diff > 0).sum(axis=1) + 1
                near = (np.abs(diff) <= 5).sum(axis=1) - 1     # minus self
                return rank, near

            s = time.perf_counter(); r1, n1 = loop_version(total[:300]); t_loop = time.perf_counter() - s
            s = time.perf_counter(); r2, n2 = vector_version(total[:300]); t_vec = time.perf_counter() - s
            print('identical:', (r1 == r2).all() and (n1 == n2).all())
            print(f'300 students -> loop {t_loop:.3f} s, vectorised {t_vec * 1000:.2f} ms')

            r, n = vector_version(total)
            sorted_t = np.sort(total)
            rank_sort = len(total) - np.searchsorted(sorted_t, total, side='right') + 1   # O(n log n)
            print('2000 students, ranks agree:', (r == rank_sort).all(), '| top rank count:', (r == 1).sum())
        """),
        title='Example: Double Loop → Broadcasting → Sort-based Rank'),
    steps(
        ('Write the loop first', 'Small, obviously correct; keep it for testing.'),
        ('Map loops to axes', 'i → rows, j → columns via [:, None] and [None, :].'),
        ('Map conditions and counters', 'if → mask; counter → sum along the axis.'),
        ('Check memory', 'n × n is fine for thousands, not for millions; then find an O(n log n) idea (sort/searchsorted).'),
        ('Compare outputs', 'assert (loop == vectorised).all() on random inputs.'),
        title='Steps to Vectorise an Algorithm'),
    crossq(
        ('What if each step depends on the previous result?', 'Look for cumulative functions (cumsum, maximum.accumulate); if none fits, compile the loop with Numba.'),
        ('Is the broadcast version always better?', 'It is O(n²) in memory; the loop is O(1) in memory. For very large n, sort-based or chunked approaches win.'),
        ('How do you test equivalence with floats?', 'np.testing.assert_allclose instead of ==.'),
    ),
]),
])
