from build import *
from numpyq.anims import *
from numpyq.runner import nprun, pyshow

SECTION = dict(level='intermediate', title='Array Manipulation', questions=[

# ------------------------------------------------------------------ 16
Q('How do you join and split arrays? concatenate vs stack vs vstack/hstack.', 'Joining & Splitting', minutes=7, cards=[
    definition(
        defbox('<code>np.concatenate(seq, axis)</code> joins arrays along an <strong>existing</strong> axis. <code>vstack</code> (rows, axis 0) and '
               '<code>hstack</code> (columns, axis 1 for 2-D) are shortcuts; <code>column_stack</code> turns 1-D arrays into columns.',
               '<code>np.stack(seq, axis)</code> joins along a <strong>new</strong> axis: n arrays of shape (a, b) → (n, a, b).',
               'Splitting: <code>np.split(a, sections_or_indices, axis)</code> (equal parts required), <code>np.array_split</code> (uneven allowed), '
               '<code>hsplit</code>/<code>vsplit</code>.'),
        tags('concatenate', 'stack', 'vstack', 'hstack', 'split'),
    ),
    analogy('<strong>concatenate</strong> is taping two attendance sheets together to make one longer sheet. <strong>stack</strong> is putting them in a '
            '<strong>folder</strong>, one on top of the other: you get a new dimension (sheet number).'),
    stack_anim(),
    real_world(
        scenario('Combining batches',
                 p('Marks from three centres (each students × subjects) → <code>np.vstack</code> for one big matrix; the same subjects in three exams → '
                   '<code>np.stack</code> gives (exam, student, subject) so <code>mean(axis=0)</code> averages across exams. Train/validation/test splits use '
                   '<code>np.split(shuffled, [int(.7*n), int(.85*n)])</code>.')),
    ),
    example(
        nprun("""
            a = np.array([[1, 2], [3, 4]]); b = np.array([[5, 6], [7, 8]])
            print(np.concatenate([a, b], axis=0).shape, np.vstack([a, b]).shape)
            print(np.hstack([a, b]))
            print(np.stack([a, b]).shape, np.stack([a, b], axis=-1).shape)
            print(np.column_stack([[1, 2, 3], [70, 80, 90]]))

            x = np.arange(10)
            train, val, test = np.split(x, [7, 9])
            print(train, val, test)
            print([p.tolist() for p in np.array_split(x, 3)])
            try:
                np.split(x, 3)
            except ValueError as e:
                print('ValueError:', e)
        """),
        title='Example: Joining Along Old and New Axes, Splitting'),
    steps(
        ('Same number of dimensions?', 'concatenate/vstack/hstack along an existing axis.'),
        ('Need a batch dimension?', 'np.stack.'),
        ('Collect first, join once', 'Append pieces to a Python list, then one concatenate.'),
        ('Split by positions', '<code>np.split(a, [i, j])</code>; uneven parts → array_split.'),
        title='Steps to Combine Arrays'),
    crossq(
        ('Why is np.append in a loop slow?', 'Arrays have a fixed size; np.append allocates a new array and copies everything each time, giving O(n²) total work.'),
        ('What shapes does concatenate need?', 'All dimensions equal except the one being joined.'),
        ('hstack on 1-D arrays?', 'It joins them end to end (axis 0), because 1-D arrays have only one axis; use column_stack to make columns.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What are np.newaxis, expand_dims, squeeze, repeat and tile used for?', 'newaxis, repeat, tile', minutes=7, cards=[
    definition(
        defbox('<code>np.newaxis</code> (alias <code>None</code>) inside an index inserts an axis of length 1: <code>x[:, np.newaxis]</code> turns (n,) into '
               '(n, 1). <code>np.expand_dims(x, axis)</code> does the same as a function; <code>np.squeeze</code> removes axes of length 1.',
               '<code>np.repeat(a, k)</code> repeats each element k times; <code>np.tile(a, reps)</code> repeats the whole array. Both copy data; broadcasting '
               'usually gives the same result without copying.'),
        tags('newaxis', 'expand_dims', 'squeeze', 'repeat', 'tile'),
    ),
    analogy('newaxis is <strong>turning a list on its side</strong>, from a row of names across the page into a column down the page, so it can be combined '
            'with another list to fill a table. repeat is <strong>photocopying each page twice</strong>; tile is <strong>photocopying the whole booklet twice</strong>.'),
    newaxis_anim(),
    real_world(
        scenario('Pairwise distances and model inputs',
                 p('<code>diff = points[:, None, :] - points[None, :, :]</code> builds all pairwise differences for a distance matrix. A single grayscale '
                   'image (28, 28) becomes a batch of one with a channel, (1, 28, 28, 1), using expand_dims before passing it to a CNN.')),
    ),
    example(
        nprun("""
            x = np.array([1, 2, 3])
            print(x[:, np.newaxis].shape, x[None, :].shape, np.expand_dims(x, 0).shape)
            print(x[:, None] * x)                     # multiplication table via broadcasting
            print(np.squeeze(np.zeros((1, 3, 1))).shape)
            print(np.repeat(x, 2), np.tile(x, 2))
            print(np.repeat([[1, 2]], 3, axis=0))
            img = np.zeros((28, 28))
            print(img[np.newaxis, :, :, np.newaxis].shape)
        """),
        title='Example: Adding, Removing and Repeating Axes'),
    steps(
        ('Need a column vector?', '<code>x[:, None]</code>.'),
        ('Pairwise operation?', 'Column vs row: <code>a[:, None] op b[None, :]</code>.'),
        ('Remove extra length-1 axes', '<code>squeeze</code> (specify axis to be safe).'),
        ('Really need copies?', 'repeat/tile; otherwise rely on broadcasting.'),
        title='Steps to Shape Data for Operations'),
    crossq(
        ('Is np.newaxis different from None?', 'No, np.newaxis is None; the name makes code more readable.'),
        ('repeat vs tile on [1, 2]?', 'repeat → [1, 1, 2, 2]; tile → [1, 2, 1, 2].'),
        ('What is np.broadcast_to?', 'Returns a read-only view of an array broadcast to a shape: repetition without copying.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('How do you find common, missing and unique values between arrays?', 'Set Operations', minutes=6, cards=[
    definition(
        defbox('NumPy set routines work on 1-D arrays and return <strong>sorted unique</strong> results: <code>np.unique</code>, <code>np.intersect1d</code> '
               '(in both), <code>np.union1d</code> (in either), <code>np.setdiff1d(a, b)</code> (in a, not b), <code>np.setxor1d</code> (in exactly one).',
               '<code>np.isin(a, b)</code> returns a boolean mask of a\'s shape telling whether each element is in b (it replaced <code>np.in1d</code>, which '
               'has been removed in recent NumPy versions).'),
        tags('unique', 'intersect1d', 'setdiff1d', 'union1d', 'isin'),
    ),
    analogy('Two guest lists for a function: who is on <strong>both</strong> (intersect), who was <strong>invited but did not come</strong> (setdiff), who '
            '<strong>came without an invitation</strong> (setdiff the other way), and a tick mark against each name on the invitation list (isin).'),
    setops_anim(),
    real_world(
        scenario('Exam attendance check',
                 p('Enrolled roll numbers vs those in the answer-sheet scan: <code>setdiff1d</code> lists absentees, the reverse lists scans with a wrong '
                   'roll number, and <code>isin</code> builds a present/absent column in the original order of the enrolment list.')),
    ),
    example(
        nprun("""
            enrolled = np.array([2401, 2402, 2403, 2405])
            attended = np.array([2403, 2402, 2404, 2402])     # scanned, with a duplicate

            print('both          :', np.intersect1d(enrolled, attended))
            print('absent        :', np.setdiff1d(enrolled, attended))
            print('not enrolled  :', np.setdiff1d(attended, enrolled))
            print('either        :', np.union1d(enrolled, attended))
            print('present mask  :', np.isin(enrolled, attended))
            vals, counts = np.unique(attended, return_counts=True)
            print('scanned twice :', vals[counts > 1])
            print(hasattr(np, 'in1d'))
        """),
        title='Example: Attendance Reconciliation'),
    steps(
        ('Make keys comparable', 'Same dtype (ints vs strings do not match).'),
        ('Find differences', 'setdiff1d both ways.'),
        ('Keep the original order', 'isin + boolean indexing instead of setdiff1d (which sorts).'),
        ('Find duplicates', 'unique with return_counts.'),
        title='Steps to Compare Lists of Keys'),
    crossq(
        ('Why use isin instead of a Python loop with "in"?', 'isin is vectorised (sorting/hashing based), O(n log n) instead of O(n × m).'),
        ('How do you get the positions of common elements?', '<code>np.intersect1d(a, b, return_indices=True)</code>.'),
        ('Do set functions work on 2-D arrays?', 'They flatten the input; for unique rows use np.unique(a, axis=0).'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What is C order vs Fortran order? What are contiguous arrays and why do they matter?', 'Memory Layout & Strides', minutes=8, cards=[
    definition(
        defbox('A multi-dimensional array is stored as a flat buffer. <strong>C order</strong> (row-major, NumPy default) stores rows one after another: the last '
               'index varies fastest. <strong>Fortran order</strong> (column-major) stores columns one after another.',
               'An array is <strong>contiguous</strong> when its elements fill the buffer without gaps in that order. Slices with steps and transposes produce '
               'non-contiguous views. Operations that read memory sequentially are faster (CPU cache); some C/Fortran libraries require a specific layout, which '
               '<code>np.ascontiguousarray</code>/<code>np.asfortranarray</code> provide.'),
        tags('C order', 'Fortran order', 'strides', 'contiguous', 'cache'),
    ),
    analogy('Reading a book <strong>line by line</strong> (C order) versus <strong>column by column</strong> like a newspaper (F order). Both contain the same '
            'text, but reading in the order it was printed is much quicker than jumping around.'),
    layout_anim(),
    real_world(
        scenario('Speed and interop',
                 p('Summing a large C-ordered matrix along rows vs along columns can differ noticeably in speed because of cache access. Passing a transposed '
                   'array to a C extension or an image library may require <code>np.ascontiguousarray</code> first, or the library raises an error about '
                   'non-contiguous input.')),
    ),
    example(
        nprun("""
            import time
            c = np.ones((3000, 3000))
            f = np.asfortranarray(c)
            print(c.flags['C_CONTIGUOUS'], f.flags['F_CONTIGUOUS'], c.strides, f.strides)
            print(c.T.flags['C_CONTIGUOUS'], c.T.flags['F_CONTIGUOUS'])   # transpose flips layout
            print(c[:, ::2].flags['C_CONTIGUOUS'])                         # stepped slice: gaps

            def timed(fn):
                t = time.perf_counter()
                for _ in range(5): fn()
                return (time.perf_counter() - t) / 5 * 1000
            print(f'copy C-array     : {timed(lambda: c.copy()):6.1f} ms')
            print(f'copy as F-order  : {timed(lambda: np.asfortranarray(c)):6.1f} ms  (must reorder memory)')
            print(np.arange(6).reshape(2, 3, order='F'))
        """),
        title='Example: Flags, Strides, and the Cost of Changing Layout'),
    steps(
        ('Check', '<code>a.flags</code>, <code>a.strides</code>.'),
        ('Match the access pattern', 'Iterate/reduce along the contiguous axis in hot loops.'),
        ('Fix for libraries', '<code>np.ascontiguousarray(a)</code> before passing to C/C++ code.'),
        ('Avoid unnecessary layout changes', 'They copy the whole array.'),
        title='Steps When Layout Matters'),
    crossq(
        ('Does pandas care about layout?', 'Yes: DataFrame columns are stored column-wise, so df.to_numpy() of mixed blocks may copy, and column access is cheap.'),
        ('Can strides be negative?', 'Yes: a[::-1] is a view with a negative stride, reading backwards.'),
        ('What does np.lib.stride_tricks.sliding_window_view do?', 'Creates overlapping windows as a view by manipulating strides, e.g. for moving averages without copies.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('How do you apply a custom function to an array? Is np.vectorize fast?', 'vectorize & apply_along_axis', minutes=7, cards=[
    definition(
        defbox('<code>np.vectorize(func)</code> wraps a scalar Python function so it accepts arrays and broadcasts, but it still <strong>calls func once per '
               'element</strong> in Python: the documentation states it is for convenience, not performance. <code>np.apply_along_axis(func, axis, a)</code> calls '
               'func on each 1-D slice. <code>np.frompyfunc</code> creates an object-dtype ufunc.',
               'For speed, rewrite the logic with ufuncs, <code>np.where</code>/<code>np.select</code>, or compile with <strong>Numba</strong> '
               '(<code>@njit</code>, <code>@vectorize</code>) or Cython.'),
        tags('np.vectorize', 'apply_along_axis', 'Numba', 'performance'),
    ),
    analogy('np.vectorize is a <strong>receptionist</strong> who accepts the whole stack of forms at once, but still walks each form to the same slow officer. '
            'Real vectorisation replaces the officer with a <strong>machine</strong> that processes the whole stack.'),
    vectorize_anim(),
    real_world(
        scenario('Grade function',
                 p('A colleague wrapped an if/elif <code>grade(m)</code> function in np.vectorize. On a million marks the np.select version was several '
                   'times faster (measured below) and gives identical answers; the gap grows with more complex per-element logic and more data.')),
    ),
    example(
        nprun("""
            import time
            rng = np.random.default_rng(0)
            m = rng.integers(0, 101, 1_000_000)

            def grade(x):
                if x >= 85: return 'A'
                elif x >= 70: return 'B'
                elif x >= 60: return 'C'
                return 'F'

            t = time.perf_counter(); g1 = np.vectorize(grade)(m); t1 = time.perf_counter() - t
            t = time.perf_counter(); g2 = np.select([m >= 85, m >= 70, m >= 60], ['A', 'B', 'C'], 'F'); t2 = time.perf_counter() - t
            print(f'np.vectorize: {t1:.3f} s | np.select: {t2:.3f} s | same: {(g1 == g2).all()}')

            rows = np.array([[3, 9, 1], [7, 2, 8]])
            print(np.apply_along_axis(lambda r: r.max() - r.min(), 1, rows), np.ptp(rows, axis=1))
        """),
        title='Example: np.vectorize vs np.select on 1 Million Marks'),
    steps(
        ('Try built-ins first', 'Most logic maps to ufuncs, comparisons, where/select, cumulative functions.'),
        ('Convenience only?', 'np.vectorize is fine for small arrays or prototypes.'),
        ('Per-row functions', 'Check for an axis argument first (ptp, sort, percentile…) before apply_along_axis.'),
        ('Truly sequential logic', 'Numba @njit on a plain loop.'),
        title='Steps to Apply Custom Logic Efficiently'),
    crossq(
        ('Why is np.vectorize slow?', 'It loops in Python and calls the function per element, with extra overhead for broadcasting and output handling.'),
        ('What does Numba do?', 'JIT-compiles Python functions using NumPy arrays to machine code, so explicit loops run at C speed.'),
        ('When is apply_along_axis acceptable?', 'For few, long rows where the per-call overhead is small relative to the work per row.'),
    ),
]),
])
