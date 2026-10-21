from build import *
from numpyq.anims import *
from numpyq.runner import nprun, pyshow

RUN_NOTE = note('Every example with an Output box was really executed while this page was built, with <strong>NumPy 2</strong> '
                '(the only hidden lines are <code>import numpy as np</code> and a print-width setting). NumPy 2 prints scalars as '
                '<code>np.float64(0.5)</code> instead of <code>0.5</code>, and changed some type rules; answers point out where NumPy 1.x behaved differently.',
                'How the examples were run')

SECTION = dict(level='beginner', title='NumPy Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is NumPy? Why is it faster than Python lists?', 'What is NumPy', minutes=7, cards=[
    definition(
        defbox('<strong>NumPy</strong> (Numerical Python) is the core library for numerical computing in Python. Its central object is the '
               '<strong>ndarray</strong>: an n-dimensional array of elements of <strong>one data type</strong>, stored in a <strong>contiguous block of '
               'memory</strong>.',
               'It is fast because operations are <strong>vectorised</strong>: one call runs a compiled C loop over the whole array, with no per-element '
               'Python type checks, using CPU caches and SIMD instructions. A list instead holds pointers to separate Python objects.'),
        table(['Aspect', 'Python list', 'NumPy array'], [
            ['Element types', 'any, mixed', 'one dtype'],
            ['Memory', 'pointers to objects (~28+ bytes per int)', 'raw values (8 bytes per int64)'],
            ['a * 2', 'repeats the list', 'multiplies every element'],
            ['Loops', 'Python bytecode', 'compiled C'],
            ['Dimensions', 'nested lists', 'true n-D with shape'],
        ]),
        tags('NumPy', 'ndarray', 'vectorisation', 'contiguous memory', 'SIMD'),
    ),
    analogy('A list is a <strong>notice board with sticky notes</strong> pointing to files kept in different cupboards; to add marks you visit every '
            'cupboard. A NumPy array is <strong>one printed sheet</strong> with all marks in a row; the calculator runs down the sheet in one sweep.'),
    numpy_anim(),
    real_world(
        scenario('Under every data tool',
                 p('pandas columns, scikit-learn feature matrices, images in OpenCV, tensors converted from PyTorch: all are (or convert to) NumPy arrays. '
                   'Scoring 1 million answer sheets, normalising features or computing distances between student profiles are one-line NumPy expressions.')),
    ),
    example(
        RUN_NOTE,
        nprun("""
            import time, sys
            marks_list = list(range(1_000_000))
            marks_arr  = np.arange(1_000_000)

            t = time.perf_counter(); doubled_list = [m * 2 for m in marks_list]; t_list = time.perf_counter() - t
            t = time.perf_counter(); doubled_arr  = marks_arr * 2;               t_arr  = time.perf_counter() - t
            print(f'list comprehension: {t_list * 1000:7.1f} ms')
            print(f'numpy vectorised  : {t_arr * 1000:7.1f} ms  ({t_list / t_arr:.0f}x faster)')

            list_bytes = sys.getsizeof(marks_list) + sum(sys.getsizeof(m) for m in marks_list)
            print(f'memory: list ~{list_bytes / 1e6:.0f} MB, array {marks_arr.nbytes / 1e6:.0f} MB')
            print([1, 2, 3] * 2, np.array([1, 2, 3]) * 2)
        """),
        title='Example: Speed, Memory, and What * Means'),
    steps(
        ('Install', '<code>pip install numpy</code> (included in Anaconda).'),
        ('Import', '<code>import numpy as np</code>, the universal alias.'),
        ('Create an array', '<code>np.array([82, 91, 75])</code> or <code>np.arange</code>, <code>np.zeros</code>…'),
        ('Operate on whole arrays', '<code>(marks - marks.mean()) / marks.std()</code>, with no loop.'),
        ('Inspect', '<code>shape</code>, <code>dtype</code>, <code>ndim</code>.'),
        title='Steps to Start with NumPy'),
    crossq(
        ('Is NumPy always faster than a list?', 'For numeric work on many elements, yes. For a handful of elements, or for appending items one by one, lists are fine or faster (arrays have a fixed size; appending copies).'),
        ('Why must all elements have the same type?', 'So each element has a fixed size and position: element i is at start + i × itemsize, enabling direct addressing and compiled loops.'),
        ('What is SIMD?', 'Single Instruction, Multiple Data: CPU instructions that process several numbers at once; NumPy\'s inner loops use them where available.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('What are the main attributes of an ndarray (shape, ndim, dtype, strides)? What is an axis?', 'ndarray Attributes & Axes', minutes=7, cards=[
    definition(
        defbox('An <strong>ndarray</strong> is a memory buffer plus metadata: <code>shape</code> (size along each dimension), <code>ndim</code> (number of '
               'dimensions), <code>size</code> (total elements), <code>dtype</code> (element type), <code>itemsize</code> (bytes per element), '
               '<code>nbytes</code>, and <code>strides</code> (bytes to step along each dimension).',
               'An <strong>axis</strong> is a dimension. In a 2-D array, <strong>axis 0</strong> runs down the rows and <strong>axis 1</strong> across the '
               'columns. <code>sum(axis=0)</code> collapses the rows, giving one value per column.'),
        tags('shape', 'ndim', 'dtype', 'strides', 'axis'),
    ),
    analogy('A theatre: <strong>shape</strong> is "20 rows × 30 seats", <strong>dtype</strong> is "every seat is the same size", and '
            '<strong>strides</strong> are the instructions "to reach the next seat walk 1 step, to reach the next row walk 30 steps".'),
    ndarray_anim(),
    real_world(
        scenario('Thinking in axes',
                 p('A marks matrix of 120 students × 6 subjects has shape (120, 6). <code>marks.mean(axis=0)</code> gives the 6 subject averages; '
                   '<code>marks.mean(axis=1)</code> gives the 120 student averages. A batch of 64 colour images for a CNN has shape (64, 224, 224, 3).')),
    ),
    example(
        nprun("""
            marks = np.array([[82, 61, 70],
                              [91, 88, 79]])
            print('shape   ', marks.shape)
            print('ndim    ', marks.ndim)
            print('size    ', marks.size)
            print('dtype   ', marks.dtype)
            print('itemsize', marks.itemsize, 'bytes')
            print('nbytes  ', marks.nbytes, 'bytes')
            print('strides ', marks.strides)
            print()
            print('per subject (axis=0):', marks.mean(axis=0))
            print('per student (axis=1):', marks.mean(axis=1))
            print('transposed strides  :', marks.T.strides, marks.T.shape)
        """),
        title='Example: Attributes and Aggregating Along Axes'),
    steps(
        ('Check shape first', 'Most NumPy errors are shape mismatches; print <code>a.shape</code>.'),
        ('Know your axes', 'Decide what each axis means (samples, features, time, channels).'),
        ('Aggregate along an axis', '<code>axis=0</code> → result per column; <code>axis=1</code> → per row.'),
        ('Keep dimensions when needed', '<code>keepdims=True</code> keeps a (n, 1) shape for broadcasting back.'),
        title='Steps to Work with Shapes and Axes'),
    crossq(
        ('What is the shape of a 1-D array of 5 elements?', '(5,): a one-element tuple. (5, 1) is a 2-D column and (1, 5) a 2-D row.'),
        ('Why are strides useful to know?', 'They explain why transpose, slicing with steps and reshape are free (views), and why non-contiguous arrays can be slower.'),
        ('What does axis=None mean?', 'Operate on the flattened array: one result for all elements.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('How do you create arrays? What is the difference between arange and linspace?', 'Creating Arrays', minutes=7, cards=[
    definition(
        defbox('From data: <code>np.array(list)</code>, <code>np.asarray</code> (no copy if already an array). Filled: <code>zeros</code>, <code>ones</code>, '
               '<code>full</code>, <code>empty</code>, <code>eye</code>/<code>identity</code>, <code>zeros_like</code>. Ranges: <code>arange(start, stop, '
               'step)</code> and <code>linspace(start, stop, num)</code>. Random: <code>np.random.default_rng(seed)</code> then <code>integers</code>, '
               '<code>random</code>, <code>normal</code>, <code>choice</code>.',
               '<strong>arange</strong> takes a <strong>step</strong> and excludes the stop value; with float steps the count can be surprising due to rounding. '
               '<strong>linspace</strong> takes the <strong>number of points</strong> and includes the stop value by default.'),
        tags('np.array', 'arange', 'linspace', 'zeros', 'default_rng'),
    ),
    analogy('<strong>arange</strong> is "walk from the gate in 3-metre steps and stop before the wall". <strong>linspace</strong> is "place exactly 5 poles '
            'from the gate to the wall, evenly spaced": you always get 5 poles and one stands at the wall.'),
    create_anim(),
    real_world(
        scenario('Typical uses',
                 p('<code>np.zeros((n_students, n_subjects))</code> to fill marks in a loop over files; <code>linspace</code> for x-values of a plot or '
                   'thresholds to test (0.1 to 0.9 in 9 steps); <code>default_rng(42)</code> for reproducible sample data and train/test splits.')),
    ),
    example(
        nprun("""
            print(np.array([[1, 2], [3, 4]]))
            print(np.zeros((2, 3)), np.zeros(3).dtype)
            print(np.full((2, 2), 7), np.eye(3, dtype=int), sep='\\n')
            print(np.arange(0, 10, 3))
            print(np.linspace(0, 1, 5))
            print(len(np.arange(0, 1, 0.1)), len(np.arange(1, 1.3, 0.1)))   # float step surprise
            rng = np.random.default_rng(42)
            print(rng.integers(40, 101, size=5))
            print(rng.normal(70, 10, size=3).round(1))
        """),
        title='Example: Constructors, arange vs linspace, Random'),
    steps(
        ('Have the data?', '<code>np.array(data, dtype=...)</code>.'),
        ('Need a buffer?', '<code>np.zeros(shape)</code> (or <code>empty</code> if you will overwrite every value).'),
        ('Integer sequence?', '<code>np.arange(start, stop, step)</code>.'),
        ('Evenly spaced floats?', '<code>np.linspace(start, stop, num)</code>.'),
        ('Random?', '<code>rng = np.random.default_rng(seed)</code>; use rng methods, not the legacy <code>np.random.rand</code>.'),
        title='Steps to Pick a Constructor'),
    crossq(
        ('Why can np.arange(1, 1.3, 0.1) have 4 elements?', 'Floating-point rounding: 0.1 cannot be stored exactly, so 1 + 3×0.1 can be slightly below 1.3 and is included. Use linspace for floats.'),
        ('np.array vs np.asarray?', 'np.array copies by default; asarray returns the input unchanged if it is already an array of the right dtype.'),
        ('Why prefer default_rng over np.random.seed?', 'Generators are independent objects (no global state), use a better algorithm (PCG64) and are the recommended API since NumPy 1.17.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What are NumPy dtypes? What happens on overflow and type conversion?', 'dtypes & Casting', minutes=8, cards=[
    definition(
        defbox('A <strong>dtype</strong> fixes the type and size of every element: <code>int8/16/32/64</code>, <code>uint8…</code>, <code>float16/32/64</code>, '
               '<code>complex</code>, <code>bool</code>, <code>datetime64</code>, fixed-width strings <code>&lt;U10</code>, <code>object</code>, and in '
               'NumPy 2 the variable-length <code>StringDType</code>.',
               'Consequences: integer overflow <strong>wraps around</strong> silently in arrays; mixed inputs are <strong>upcast</strong> to a common type; '
               '<code>astype</code> converts (copying) and float → int <strong>truncates</strong>. NumPy 2 (NEP 50) changed scalar promotion: the array\'s '
               'dtype wins over Python numbers, and out-of-range Python ints raise <code>OverflowError</code>.'),
        tags('dtype', 'astype', 'overflow', 'type promotion', 'NEP 50'),
    ),
    analogy('Dtypes are <strong>box sizes</strong>. A small box (int8) is cheap but holds only up to 127; force 200 in and the counter rolls over like an old '
            '<strong>car odometer</strong> going from 99999 to 00000.'),
    dtype_anim(),
    real_world(
        scenario('Image brightness bug',
                 p('Images are uint8 (0–255). Adding 50 to brighten a photo made white areas dark: 230 + 50 wrapped to 24. The fix: convert to a larger '
                   'type, add, clip to 0–255, convert back. The same applies to counters stored in small integer types.')),
    ),
    example(
        nprun("""
            a = np.array([100, 120], dtype=np.int8)
            print(a + a)                                    # wraps around, no warning for arrays

            img = np.array([230, 100, 10], dtype=np.uint8)
            print(img + 50)                                 # 230 + 50 -> 24
            print(np.clip(img.astype(np.int16) + 50, 0, 255).astype(np.uint8))

            print(np.array([1, 2.5]).dtype, np.array([1, 'x']).dtype, np.array([1, None]).dtype)
            print(np.array([2.9, -2.9]).astype(int))        # truncates toward zero
            print(np.iinfo(np.int32).max, np.finfo(np.float32).eps)

            x = np.array([1, 2], dtype=np.float32)
            print((x * 3.0).dtype)                          # NumPy 2: stays float32
            try:
                np.int8(100) + 200
            except OverflowError as e:
                print('OverflowError:', e)
        """),
        title='Example: Overflow, Upcasting, Truncation, NumPy 2 Promotion'),
    steps(
        ('Choose deliberately', 'float64/int64 by default; smaller types to save memory when the range allows.'),
        ('Check limits', '<code>np.iinfo(dtype)</code> and <code>np.finfo(dtype)</code>.'),
        ('Upcast before risky maths', 'Convert uint8 images or int16 counters to a bigger type first.'),
        ('Round before converting floats', '<code>np.round(x).astype(int)</code> if you do not want truncation.'),
        ('Avoid object dtype', 'It stores Python objects and loses the speed advantage.'),
        title='Steps to Avoid dtype Bugs'),
    crossq(
        ('Why does an int array with None become object dtype?', 'Integers have no missing-value representation; NumPy falls back to object. Use float with np.nan, or pandas nullable types.'),
        ('What changed in NumPy 2 promotion?', 'NEP 50: Python scalars are "weak": float32 array * 3.0 stays float32, and np.int8(100) + 200 raises OverflowError instead of quietly becoming int16/int64.'),
        ('What is the difference between &lt;U5 and StringDType?', '&lt;U5 is fixed-width (5 characters, longer strings are cut off); StringDType (NumPy 2) stores variable-length strings.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('How do reshape, ravel, flatten and transpose work? What does -1 mean in reshape?', 'Reshaping Arrays', minutes=7, cards=[
    definition(
        defbox('<code>reshape(new_shape)</code> gives the same elements in a new shape; the total size must match. One dimension may be <code>-1</code>, which '
               'NumPy computes. It returns a <strong>view</strong> when possible.',
               '<code>ravel()</code> flattens to 1-D, a view when possible; <code>flatten()</code> always returns a copy. <code>.T</code> / <code>transpose()</code> '
               'reverses (or permutes) axes by changing strides. <code>np.newaxis</code>/<code>expand_dims</code> add an axis of length 1; <code>squeeze</code> removes them.'),
        tags('reshape', 'ravel', 'flatten', 'transpose', '-1'),
    ),
    analogy('An <strong>egg tray of 12</strong> can be arranged as 2×6 or 3×4 or one line of 12: the eggs are the same, only the arrangement changes. '
            '"-1" means "you figure out the other side": 3 rows → 4 per row.'),
    reshape_anim(),
    real_world(
        scenario('Machine-learning shapes',
                 p('scikit-learn expects a 2-D feature matrix: a single feature column <code>x</code> of shape (100,) must become (100, 1) with '
                   '<code>x.reshape(-1, 1)</code>. A 28×28 image is flattened to 784 values for a dense layer with <code>img.reshape(-1)</code>.')),
    ),
    example(
        nprun("""
            a = np.arange(6)
            m = a.reshape(2, 3)
            print(m)
            print(a.reshape(3, -1).shape, a.reshape(-1, 1).shape)
            print(m.T)
            print(m.ravel(), m.flatten())

            r = m.ravel(); r[0] = 100          # view: changes m
            f = m.flatten(); f[1] = 200        # copy: m unchanged
            print(m)
            print(np.shares_memory(m, r), np.shares_memory(m, f))
            try:
                a.reshape(4, 2)
            except ValueError as e:
                print('ValueError:', e)
        """),
        title='Example: reshape, -1, Transpose, ravel vs flatten'),
    steps(
        ('Count elements', 'The product of the new shape must equal <code>a.size</code>.'),
        ('Use -1 once', 'For the dimension you do not want to compute yourself.'),
        ('Single feature for ML', '<code>x.reshape(-1, 1)</code>.'),
        ('Flatten', '<code>ravel()</code> for speed, <code>flatten()</code> when you need an independent copy.'),
        ('Swap axes', '<code>.T</code> for 2-D, <code>np.transpose(a, (0, 2, 1))</code> or <code>np.moveaxis</code> for n-D.'),
        title='Steps to Reshape Safely'),
    crossq(
        ('Does reshape copy data?', 'Not if the data can be described with new strides (usually for C-contiguous arrays); otherwise (e.g. reshaping a transposed array) it copies.'),
        ('What is the difference between reshape and resize?', 'reshape returns a new view/array and requires the same size; resize changes the array in place and can pad or truncate.'),
        ('What is order="F"?', 'Read/write elements column by column (Fortran order) instead of row by row (C order).'),
    ),
]),
])
