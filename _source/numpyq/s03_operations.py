from build import *
from numpyq.anims import *
from numpyq.runner import nprun, pyshow

MARKS = """
marks = np.array([[82, 61, 70],
                  [91, 88, 79]])     # 2 students x 3 subjects
"""

SECTION = dict(level='basic', title='Operations & Broadcasting', questions=[

# ------------------------------------------------------------------ 11
Q('What are ufuncs (universal functions)? What is vectorisation?', 'ufuncs & Vectorisation', minutes=7, cards=[
    definition(
        defbox('A <strong>ufunc</strong> is a function that operates <strong>element by element</strong> on arrays in compiled code: <code>np.add</code>, '
               '<code>np.multiply</code>, <code>np.sqrt</code>, <code>np.exp</code>, <code>np.log</code>, <code>np.maximum</code>, comparisons… Operators '
               '(<code>+ - * / ** &gt;</code>) call ufuncs. Ufuncs support broadcasting, type casting, <code>out=</code>, <code>where=</code>, and methods '
               '<code>reduce</code>, <code>accumulate</code>, <code>outer</code>, <code>at</code>.',
               '<strong>Vectorisation</strong> is writing computations as whole-array ufunc calls instead of Python loops.'),
        tags('ufunc', 'vectorisation', 'np.add', 'reduce', 'outer'),
    ),
    analogy('A ufunc is a <strong>franking machine</strong> in a post office: feed in a stack of 10,000 envelopes and every one gets stamped in one run, '
            'instead of a clerk stamping each by hand.'),
    ufunc_anim(),
    real_world(
        scenario('Weighted final score',
                 p('<code>final = 0.4 * internal + 0.6 * exam</code> computes all students at once; <code>np.maximum(final, re_exam)</code> keeps the better '
                   'of two attempts; <code>np.round(final).astype(int)</code> prepares the result sheet.')),
    ),
    example(
        nprun("""
            internal = np.array([70, 85, 40, 90])
            exam     = np.array([65, 92, 55, 81])
            reexam   = np.array([0, 0, 68, 0])

            final = 0.4 * internal + 0.6 * exam
            print(final)
            print(np.maximum(final, 0.4 * internal + 0.6 * reexam))
            print(np.sqrt(np.array([16, 25])), np.exp(1).round(4), np.log10(1000))

            print(np.add.reduce(exam), np.add.accumulate(exam))
            print(np.multiply.outer([1, 2, 3], [1, 2, 3]))

            out = np.empty(4)
            np.multiply(exam, 0.6, out=out)            # no new allocation
            print(out)
            print(isinstance(np.add, np.ufunc), np.add.nin, np.add.nout)
        """),
        title='Example: Arithmetic, Math, Methods and out='),
    steps(
        ('Think in arrays', 'What would you do to one element? Write it once for the whole array.'),
        ('Use operators and np.* math', 'They are ufuncs.'),
        ('Combine with masks', '<code>np.where</code>, boolean indexing.'),
        ('Large arrays', 'Use <code>out=</code> or in-place operators (<code>a *= 2</code>) to avoid temporary copies.'),
        title='Steps to Vectorise a Calculation'),
    crossq(
        ('Is math.sqrt the same as np.sqrt?', 'No: math.sqrt works on one Python float; np.sqrt works on whole arrays (and scalars) and returns arrays.'),
        ('What does np.add.at do?', 'Unbuffered in-place addition at given indices, so repeated indices accumulate: np.add.at(counts, idx, 1).'),
        ('Can you write your own ufunc?', 'np.frompyfunc / np.vectorize create ufunc-like wrappers (still Python speed); real ufuncs are written in C or with Numba\'s @vectorize.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What is broadcasting? Explain the broadcasting rules with examples.', 'Broadcasting', minutes=9, cards=[
    definition(
        defbox('<strong>Broadcasting</strong> lets NumPy combine arrays of different shapes in element-wise operations by <strong>virtually repeating</strong> '
               'the smaller one, without copying data.',
               '<strong>Rules</strong>: compare shapes from the <strong>rightmost</strong> dimension. Two dimensions are compatible if they are '
               '<strong>equal</strong> or one of them is <strong>1</strong>. Missing leading dimensions count as 1. The result takes the larger size in each '
               'dimension. Otherwise: <code>ValueError: operands could not be broadcast together</code>.'),
        table(['Shapes', 'Result'], [
            ['(2, 3) and scalar', '(2, 3)'],
            ['(2, 3) and (3,)', '(2, 3): row added to every row'],
            ['(2, 3) and (2, 1)', '(2, 3): column added to every column'],
            ['(3, 1) and (1, 4)', '(3, 4): outer combination'],
            ['(2, 3) and (2,)', 'error: 3 vs 2'],
        ]),
        tags('broadcasting', 'shape', 'newaxis', 'keepdims'),
    ),
    analogy('Adding a <strong>5-mark bonus to every student</strong> does not need a sheet full of 5s; you announce "+5" once and everyone applies it. '
            'Broadcasting is that announcement: one small array applied across a big one.'),
    broadcast_anim(),
    real_world(
        scenario('Standardising features',
                 p('<code>(X - X.mean(axis=0)) / X.std(axis=0)</code> standardises every column of a 10,000 × 20 feature matrix in one line: the (20,) '
                   'means broadcast over all rows. Per-row normalisation needs <code>keepdims=True</code> so the (10000, 1) result broadcasts across columns.')),
    ),
    example(
        nprun("""
            print(marks + 5)                                   # scalar
            print(marks - marks.mean(axis=0))                  # (2,3) - (3,)
            print(marks - marks.mean(axis=1, keepdims=True))   # (2,3) - (2,1)

            weights = np.array([0.5, 0.3, 0.2])
            print((marks * weights).sum(axis=1))               # weighted total per student

            col = np.array([[1], [2], [3]]); row = np.array([10, 20, 30, 40])
            print((col + row).shape)                           # (3,1) + (4,) -> (3,4)
            try:
                marks - marks.mean(axis=1)                     # (2,3) - (2,)
            except ValueError as e:
                print('ValueError:', e)
        """, setup=MARKS),
        title='Example: Column and Row Centring, Weights, an Outer Shape, an Error'),
    steps(
        ('Write down both shapes', 'Align them on the right.'),
        ('Check each pair', 'Equal or 1 → fine; otherwise reshape.'),
        ('Fix with newaxis/keepdims', '<code>v[:, np.newaxis]</code> or <code>keepdims=True</code> to turn (n,) into (n, 1).'),
        ('Check the result shape', 'An unexpected (n, n) result means you broadcast a column against a row by mistake.'),
        title='Steps to Debug Broadcasting'),
    crossq(
        ('Does broadcasting copy the smaller array?', 'No: it uses a stride of 0 along the broadcast dimension, so the same values are reread. (np.broadcast_to shows this as a read-only view.)'),
        ('A common silent bug?', 'Subtracting a (n,) vector from an (n,) vs (n,1) array: (n,) - (n,1) gives (n, n) instead of an error. Always check shapes.'),
        ('How do you compute all pairwise differences of x?', '<code>x[:, None] - x[None, :]</code> → an (n, n) matrix.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('How do aggregation functions work with the axis parameter?', 'Aggregations & axis', minutes=7, cards=[
    definition(
        defbox('Aggregations reduce arrays: <code>sum</code>, <code>mean</code>, <code>median</code>, <code>std</code>, <code>var</code>, <code>min</code>, '
               '<code>max</code>, <code>argmin</code>, <code>argmax</code>, <code>prod</code>, <code>ptp</code> (max − min), <code>percentile</code>, '
               '<code>any</code>, <code>all</code>. Cumulative versions (<code>cumsum</code>, <code>cumprod</code>) keep the shape.',
               '<code>axis=None</code> reduces everything; <code>axis=0</code> reduces down the rows (result per column); <code>axis=1</code> across the columns '
               '(result per row); a tuple reduces several axes. <code>keepdims=True</code> keeps reduced axes as length 1.'),
        tags('sum', 'mean', 'axis', 'keepdims', 'argmax'),
    ),
    analogy('A marks register: adding <strong>down each column</strong> gives subject totals (axis 0); adding <strong>along each row</strong> gives each '
            'student\'s total (axis 1). The axis you name is the one that <strong>disappears</strong>.'),
    axis_agg_anim(),
    real_world(
        scenario('Result summary',
                 p('Subject averages (<code>mean(axis=0)</code>), student totals (<code>sum(axis=1)</code>), topper per subject (<code>argmax(axis=0)</code>), '
                   'spread per subject (<code>std(axis=0)</code>). For a (days, students) attendance array, <code>mean(axis=0)</code> is each student\'s '
                   'attendance rate.')),
    ),
    example(
        nprun("""
            print(marks.sum(), marks.sum(axis=0), marks.sum(axis=1))
            print(marks.mean(axis=0), marks.max(axis=1))
            print('topper per subject:', marks.argmax(axis=0))
            print('range per subject :', np.ptp(marks, axis=0))
            print(marks.sum(axis=1, keepdims=True).shape)
            print(marks.cumsum(axis=1))
            cube = np.arange(24).reshape(2, 3, 4)
            print(cube.sum(axis=(1, 2)))       # reduce two axes at once
        """, setup=MARKS),
        title='Example: Reductions Along Different Axes'),
    steps(
        ('Identify what each axis means', 'Rows = students, columns = subjects.'),
        ('Pick the axis to collapse', 'Per subject → collapse students → axis=0.'),
        ('Use arg-functions for positions', '<code>argmax</code>, <code>argmin</code>.'),
        ('Keep dims for follow-up maths', '<code>keepdims=True</code>.'),
        title='Steps for Correct Aggregations'),
    crossq(
        ('np.sum(a) vs a.sum() vs sum(a)?', 'np.sum and a.sum are the same NumPy reduction; Python\'s built-in sum loops in Python over the first axis (slow, and gives a 1-D result for 2-D input).'),
        ('Why is std different from pandas std?', 'NumPy uses ddof=0 (population) by default; pandas uses ddof=1 (sample). Pass ddof=1 to match.'),
        ('What does argmax return on a 2-D array without axis?', 'The index in the flattened array; convert with np.unravel_index.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do you sort and search arrays? Explain sort, argsort, unique and searchsorted.', 'Sorting & Searching', minutes=7, cards=[
    definition(
        defbox('<code>np.sort(a, axis=-1)</code> returns a sorted copy (<code>a.sort()</code> in place); <code>kind="stable"</code> keeps equal elements in order. '
               '<code>np.argsort</code> returns the indices that sort the array. <code>np.argmax/argmin</code> find extreme positions. <code>np.unique</code> '
               'returns sorted distinct values (optionally counts, first indices, inverse). <code>np.searchsorted(sorted, v)</code> gives the insertion position '
               '(binary search). <code>np.partition/argpartition</code> place the k-th element correctly in O(n).'),
        tags('sort', 'argsort', 'unique', 'searchsorted', 'partition'),
    ),
    analogy('<strong>argsort</strong> is the list of <strong>roll numbers in merit order</strong>: it does not move the answer sheets, it tells you in which order '
            'to pick them up. Use the same list to arrange the name list, photo list and certificates consistently.'),
    sort_anim(),
    real_world(
        scenario('Merit list and grade bands',
                 p('<code>order = np.argsort(-totals)</code> reorders names and totals together; <code>np.unique(courses, return_counts=True)</code> counts students '
                   'per course; <code>np.searchsorted([60, 70, 85], marks, side="right")</code> converts marks to band numbers 0–3.')),
    ),
    example(
        nprun("""
            names  = np.array(['Anuj', 'Vineeta', 'Aarshvi', 'Rohan', 'Meera'])
            totals = np.array([213, 258, 222, 160, 222])

            order = np.argsort(-totals, kind='stable')
            print(names[order], totals[order])

            courses = np.array(['DBDA', 'DAC', 'DBDA', 'DAI', 'DBDA'])
            values, counts = np.unique(courses, return_counts=True)
            print(dict(zip(values.tolist(), counts.tolist())))

            marks = np.array([82, 61, 91, 55, 70])
            bands = np.searchsorted([60, 70, 85], marks, side='right')
            print(bands, np.array(['F', 'C', 'B', 'A'])[bands])

            top2 = np.argpartition(-totals, 2)[:2]
            print('top 2 (unordered):', names[top2])
        """),
        title='Example: Merit Order, Counts, Bands, Top-k'),
    steps(
        ('Sort values only', '<code>np.sort</code>.'),
        ('Sort related arrays together', '<code>idx = np.argsort(key)</code> then index each array with idx.'),
        ('Descending', '<code>np.argsort(-a)</code> or <code>[::-1]</code> (note: reversing breaks stability for ties).'),
        ('Counts', '<code>np.unique(..., return_counts=True)</code>.'),
        ('Binning / lookup in sorted data', '<code>np.searchsorted</code>.'),
        title='Steps for Ordering Tasks'),
    crossq(
        ('How do you sort a 2-D array by one column?', '<code>a[a[:, 2].argsort()]</code> sorts rows by column 2.'),
        ('Sort by two keys?', '<code>np.lexsort((secondary, primary))</code>: the last key is the primary one.'),
        ('Why use argpartition for top-k?', 'O(n) instead of O(n log n); sort only the k results afterwards if order matters.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How does NumPy handle missing values (NaN) and infinity?', 'NaN & inf', minutes=7, cards=[
    definition(
        defbox('<code>np.nan</code> (IEEE "not a number") represents missing or undefined float values; <code>np.inf</code> represents infinity. They exist only '
               'in <strong>float</strong> (and complex) arrays.',
               'NaN <strong>propagates</strong>: any arithmetic with NaN yields NaN, so <code>np.mean</code> returns NaN. Use <strong>nan-functions</strong> '
               '(<code>nanmean</code>, <code>nansum</code>, <code>nanmax</code>, <code>nanstd</code>, <code>nanpercentile</code>…), detect with '
               '<code>np.isnan</code>/<code>np.isinf</code>/<code>np.isfinite</code>, replace with <code>np.nan_to_num</code> or <code>np.where</code>. '
               '<code>np.nan == np.nan</code> is False.'),
        tags('NaN', 'inf', 'nanmean', 'isnan', 'nan_to_num', 'errstate'),
    ),
    analogy('NaN is a <strong>blank cell that poisons any formula</strong> it touches: total a column with one blank and the total becomes blank. '
            'nan-functions are formulas that <strong>skip blanks</strong>.'),
    nan_anim(),
    real_world(
        scenario('Absent students and divide-by-zero',
                 p('Absent marks stored as NaN: <code>np.nanmean(marks, axis=0)</code> gives subject averages over students who appeared. Attendance '
                   'percentage = present / total days; a course with 0 days yet gives NaN/inf, handled with <code>np.divide(p, t, out=np.zeros_like(p, float), where=t &gt; 0)</code>.')),
    ),
    example(
        nprun("""
            m = np.array([[82, np.nan, 70],
                          [91, 88, np.nan]])
            print(np.mean(m, axis=0))
            print(np.nanmean(m, axis=0), np.nansum(m), np.nanmax(m, axis=1))
            print(np.isnan(m).sum(), np.nan == np.nan)
            print(np.nan_to_num(m, nan=0))

            present = np.array([18, 0, 21.0]); total = np.array([20, 0, 22.0])
            with np.errstate(divide='ignore', invalid='ignore'):
                print(present / total)
            print(np.divide(present, total, out=np.zeros_like(present), where=total > 0))
            print(np.array([1.0]) / 0)
            try:
                np.array([1, 2]).astype(int)[0] = np.nan
            except ValueError as e:
                print('ValueError:', e)
        """),
        title='Example: Propagation, nan-functions, Safe Division'),
    steps(
        ('Use float for data with gaps', 'NaN needs a float dtype.'),
        ('Count', '<code>np.isnan(a).sum(axis=0)</code>.'),
        ('Aggregate safely', 'nan-functions, or mask: <code>a[~np.isnan(a)]</code>.'),
        ('Replace when needed', '<code>np.nan_to_num</code>, <code>np.where(np.isnan(a), fill, a)</code>.'),
        ('Prevent', '<code>where=</code> in division; check <code>np.isfinite</code> before saving results.'),
        title='Steps to Handle NaN and inf'),
    crossq(
        ('Why can\'t integers be NaN?', 'NaN is a special bit pattern defined only for IEEE floating-point numbers; every int bit pattern is a valid number.'),
        ('What are masked arrays?', 'np.ma arrays carry a separate boolean mask; operations ignore masked elements, and they work for any dtype, including integers.'),
        ('How do you silence divide-by-zero warnings for a block?', 'with np.errstate(divide="ignore", invalid="ignore"): …, or set them to "raise" to turn them into exceptions while debugging.'),
    ),
]),
])
