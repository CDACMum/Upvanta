from build import *


def _lines(x, y, lines, color='#e2e8f0', size=11, step=None, gap=16):
    return ''.join(stext(x, y + i * gap, ln, color, size, 'start', step=step).replace('<text ', '<text xml:space="preserve" ', 1)
                   for i, ln in enumerate(lines))


def _codebox(x, y, w, h, lines, color='gray', step=None, tcolor='#e2e8f0', size=11, focus=None):
    return sbox(x, y, w, h, '', '', color, step=step, fill_opacity=0.08, focus=focus) + _lines(x + 14, y + 22, lines, tcolor, size, step=step)


def grid(x, y, vals, cw=40, ch=28, step=None, title=None, tc='blue', hi=None, hstep=None, hcolor='#0ea5e9', rlabels=False, clabels=False):
    """Array drawn as a grid of cells. hi: set of (r, c) highlighted at hstep."""
    rows = [vals] if vals and not isinstance(vals[0], (list, tuple)) else vals
    out = []
    if title:
        out.append(stext(x + len(rows[0]) * cw / 2, y - 8 - (14 if clabels else 0), title, PALETTE.get(tc, tc), 13, bold=True))
    if clabels:
        for c in range(len(rows[0])):
            out.append(stext(x + c * cw + cw / 2, y - 6, str(c), 'gray', 10))
    for r, row in enumerate(rows):
        if rlabels:
            out.append(stext(x - 10, y + r * ch + ch / 2 + 4, str(r), 'gray', 10))
        for c, v in enumerate(row):
            out.append(scell(x + c * cw, y + r * ch, cw, ch, str(v), '#162033' if (r + c) % 2 else '#1b2940'))
    if hi:
        cells = ''.join(scell(x + c * cw, y + r * ch, cw, ch, str(rows[r][c]), hcolor, '#fff', bold=True) for r, c in hi)
        out.append(f'<g{" data-step=%s" % chr(34) + str(hstep) + chr(34) if hstep else ""}>{cells}</g>')
    return f'<g{" data-step=%s" % chr(34) + str(step) + chr(34) if step else ""}>' + ''.join(out) + '</g>'


# ============================================================ section 1
def numpy_anim():
    elems = [
        stext(380, 24, 'Python list vs NumPy array in memory', 'blue', 15, bold=True),
        stext(190, 52, 'list: array of pointers', 'red', 13, step=1, bold=True),
        sbox(20, 62, 340, 34, '', '', 'red', step=1, fill_opacity=0.08),
    ]
    for i in range(5):
        elems.append(scell(30 + i * 64, 67, 56, 24, '→', '#3f1d1d', step=1))
        elems.append(sbox(30 + i * 64, 120 + (i % 2) * 28, 56, 26, f'int {80 + i}', '', 'red', step=1, size=10, fill_opacity=0.15))
        elems.append(sarrow(58 + i * 64, 91, 58 + i * 64, 118 + (i % 2) * 28, 'red', step=1))
    elems += [
        stext(190, 195, 'each item: a full Python object (28 bytes) somewhere in memory', 'red', 11, step=1),
        stext(570, 52, 'ndarray: one contiguous block', 'green', 13, step=2, bold=True),
        grid(410, 67, [80, 81, 82, 83, 84], cw=64, ch=30, step=2),
        stext(570, 115, 'int64 → 8 bytes each, same type, side by side', 'green', 11, step=2),
        sbox(410, 135, 320, 50, 'a * 2  →  one C loop', 'no type checks, CPU cache + SIMD friendly', 'green', step=3, size=13, focus=3),
        stext(380, 228, 'typically 10–100× faster and several times smaller than lists for numeric work', 'amber', 12, step=4, focus=4),
        stext(380, 252, 'foundation of pandas, scikit-learn, SciPy, TensorFlow, PyTorch, OpenCV', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'A Python list stores <strong>pointers</strong> to separate Python objects. Every number carries its own type information and reference count.',
        'A NumPy <strong>ndarray</strong> stores raw values of one dtype in one contiguous block of memory.',
        'Operations such as <code>a * 2</code> run one compiled loop over that block: no per-element type checks, good use of CPU cache and vector (SIMD) instructions.',
        'Result: much faster arithmetic and much less memory than the equivalent list code.',
        'Almost the whole Python data stack is built on top of ndarrays.',
    ])


def ndarray_anim():
    elems = [
        stext(380, 24, 'Anatomy of an ndarray', 'blue', 15, bold=True),
        grid(40, 60, [[82, 61, 70], [91, 88, 79]], cw=56, ch=34, step=1, title='marks (2 students × 3 subjects)', rlabels=True, clabels=True),
        _codebox(260, 45, 230, 130, ['a.shape    (2, 3)', 'a.ndim     2', 'a.size     6', 'a.dtype    int64', 'a.itemsize 8  (bytes)', 'a.nbytes   48'], 'purple', step=2, tcolor='#c4b5fd'),
        stext(625, 52, 'memory (row-major, C order)', 'amber', 12, step=3, bold=True),
        grid(510, 62, [82, 61, 70, 91, 88, 79], cw=38, ch=28, step=3),
        stext(625, 112, 'a.strides = (24, 8)', 'amber', 13, step=4, bold=True, focus=4),
        stext(625, 132, 'next row: jump 24 bytes · next column: 8 bytes', 'amber', 11, step=4),
        stext(380, 200, 'shape + dtype + strides describe how to read the same bytes → reshape/transpose are often free (views)', 'cyan', 12, step=5),
        stext(380, 224, 'axis 0 = rows (down), axis 1 = columns (across)', 'green', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'A 2-D array of marks: 2 rows (students) and 3 columns (subjects).',
        'Attributes describe it: shape, number of dimensions, element count, dtype and bytes per element.',
        'In memory it is a flat block of 6 values stored row after row (C order).',
        '<strong>Strides</strong> say how many bytes to jump to move one step along each axis: 24 bytes to the next row, 8 to the next column.',
        'Because an array is "buffer + shape + strides", many operations just create a new description of the same buffer. Axis 0 runs down the rows, axis 1 across the columns.',
    ])


def create_anim():
    elems = [
        stext(380, 24, 'Ways to create arrays', 'blue', 15, bold=True),
        stext(30, 62, 'np.array([1, 2, 3])', 'gray', 12, anchor='start', step=1), grid(260, 46, [1, 2, 3], step=1),
        stext(30, 100, 'np.zeros(4) / np.ones(4)', 'gray', 12, anchor='start', step=2), grid(260, 84, ['0.', '0.', '0.', '0.'], step=2),
        stext(30, 138, 'np.arange(0, 10, 3)', 'purple', 12, anchor='start', step=3), grid(260, 122, [0, 3, 6, 9], step=3),
        stext(450, 138, 'start, stop (excluded), STEP', 'purple', 11, anchor='start', step=3),
        stext(30, 176, 'np.linspace(0, 1, 5)', 'green', 12, anchor='start', step=4), grid(260, 160, ['0.', '.25', '.5', '.75', '1.'], step=4),
        stext(470, 176, 'start, stop (included), COUNT', 'green', 11, anchor='start', step=4),
        stext(30, 214, 'np.full((2,2), 7) · np.eye(3) · np.empty(n)', 'amber', 12, anchor='start', step=5),
        stext(30, 238, 'rng = np.random.default_rng(42); rng.integers(0, 100, 5)', 'cyan', 12, anchor='start', step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'From existing data: <code>np.array</code> on a list (or nested lists for 2-D).',
        'Pre-filled: <code>zeros</code>, <code>ones</code> (float64 by default), useful as starting buffers.',
        '<code>arange</code> is like Python range: you give the <strong>step</strong>, and the stop value is excluded.',
        '<code>linspace</code> gives a <strong>number of points</strong>, evenly spaced, and includes the stop value. Safer than arange with float steps.',
        'Others: <code>full</code>, <code>eye</code> (identity), <code>empty</code> (uninitialised, fast) and random arrays from a Generator.',
    ])


def dtype_anim():
    elems = [
        stext(380, 24, 'dtypes: fixed size, fixed range', 'blue', 15, bold=True),
        stable(20, 55, ['dtype', 'bytes', 'range / precision'], [['int8', '1', '-128 … 127'], ['int32', '4', '±2.1 billion'], ['int64', '8', '±9.2 × 10¹⁸'],
                                                               ['float32', '4', '~7 digits'], ['float64', '8', '~15–16 digits'], ['bool', '1', 'True / False']],
               [80, 55, 140], step=1, title=None),
        sbox(330, 55, 410, 56, 'np.int8(100) + np.int8(100) → -56', 'overflow wraps around silently (RuntimeWarning for scalars only)', 'red', step=2, size=12, focus=2),
        sbox(330, 121, 410, 56, "np.array([1, 2.5, 'x']) → all strings ('<U32')", 'one dtype per array: the most general type wins', 'amber', step=3, size=12),
        sbox(330, 187, 410, 56, "a.astype(np.int32) · np.array(.., dtype='float32')", 'astype always makes a copy · float → int truncates', 'green', step=4, size=12),
        stext(380, 268, 'NumPy 2 (NEP 50): np.int8(100) + 200 → OverflowError instead of silently upcasting', 'purple', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'Every array has one dtype with a fixed size, which fixes its range or precision.',
        'Integer arithmetic that exceeds the range <strong>wraps around</strong>: 100 + 100 in int8 gives -56. Arrays do this without any warning.',
        'Mixed input is converted to one common dtype: here everything becomes a string.',
        '<code>astype</code> converts (and copies); converting floats to ints truncates toward zero.',
        'NumPy 2 changed promotion rules (NEP 50): the array/scalar dtype wins, and a Python int that does not fit raises an error.',
    ])


def reshape_anim():
    elems = [
        stext(380, 24, 'reshape, transpose, ravel: same data, new shape', 'blue', 15, bold=True),
        grid(20, 60, [0, 1, 2, 3, 4, 5], cw=40, step=1, title='a = np.arange(6)  shape (6,)'),
        grid(300, 60, [[0, 1, 2], [3, 4, 5]], cw=40, step=2, title='a.reshape(2, 3)'),
        grid(470, 60, [[0, 1], [2, 3], [4, 5]], cw=40, step=3, title='a.reshape(3, -1)'),
        grid(600, 60, [[0, 3], [1, 4], [2, 5]], cw=40, step=4, title='a.reshape(2,3).T'),
        stext(380, 170, '-1 = "work this dimension out": 6 elements / 3 rows = 2 columns', 'purple', 12, step=3),
        stext(380, 195, 'transpose swaps axes by changing strides (no data moved)', 'green', 12, step=4),
        sbox(20, 215, 360, 50, 'ravel() → view when possible', 'flatten() → always a copy', 'amber', step=5, size=12),
        sbox(400, 215, 340, 50, 'reshape needs the same number of elements', 'a.reshape(4, 2) → ValueError', 'red', step=5, size=12),
    ]
    return anim(canvas(760, 280, *elems), [
        'Six values in a 1-D array.',
        '<code>reshape(2, 3)</code> reads the same values row by row into 2 rows of 3.',
        'One dimension can be <code>-1</code>: NumPy computes it from the total size.',
        '<code>.T</code> transposes: rows become columns. It only swaps the strides.',
        '<code>ravel</code> flattens (a view if possible), <code>flatten</code> always copies; the total size must match or reshape fails.',
    ])


# ============================================================ section 2
_M = [[82, 61, 70, 55], [91, 88, 79, 95], [84, 72, 66, 90]]


def slicing_anim():
    elems = [
        stext(380, 24, 'Indexing and slicing 2-D arrays: a[rows, cols]', 'blue', 15, bold=True),
        grid(40, 70, _M, cw=50, ch=32, title='a (3 × 4)', rlabels=True, clabels=True, hi={(1, 2)}, hstep=1),
        stext(150, 190, 'a[1, 2] → 79', 'blue', 13, step=1, bold=True),
        grid(290, 70, _M, cw=50, ch=32, hi={(0, 1), (1, 1), (2, 1)}, hstep=2, hcolor='#10b981', title='a[:, 1] → column 1'),
        grid(530, 70, _M, cw=50, ch=32, hi={(0, 2), (0, 3), (1, 2), (1, 3)}, hstep=3, hcolor='#8b5cf6', title='a[:2, 2:] → block'),
        stext(390, 190, '[61 88 72]  (1-D)', 'green', 12, step=2),
        stext(630, 190, '[[70 55] [79 95]]', 'purple', 12, step=3),
        stext(380, 222, 'a[-1] → last row · a[::2] → every second row · a[:, ::-1] → columns reversed', 'cyan', 12, step=4),
        stext(380, 248, 'a[1][2] works too, but a[1, 2] is one step (and needed for slices on both axes)', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 265, *elems), [
        'One comma-separated index per axis: row 1, column 2 gives one element.',
        'A colon means "all" on that axis: every row of column 1 → a 1-D array.',
        'Slices on both axes cut out a block: first two rows, columns 2 to the end.',
        'Negative indexes count from the end; steps skip or reverse.',
        'Chained <code>a[1][2]</code> creates an intermediate array first; <code>a[1, 2]</code> is the NumPy way.',
    ])


def mask_anim():
    elems = [
        stext(380, 24, 'Boolean masking: condition → True/False array → selection', 'blue', 15, bold=True),
        grid(30, 60, [82, 61, 91, 55, 88, 47], cw=50, step=1, title='marks'),
        grid(30, 130, ['T', 'T', 'T', 'F', 'T', 'F'], cw=50, step=2, title='marks >= 60', tc='purple', hi={(0, 0), (0, 1), (0, 2), (0, 4)}, hstep=2, hcolor='#8b5cf6'),
        sarrow(335, 140, 385, 140, 'green', step=3),
        grid(390, 130, [82, 61, 91, 88], cw=50, step=3, title='marks[marks >= 60]', tc='green'),
        grid(390, 60, [82, 61, 91, 0, 88, 0], cw=50, step=4, title='marks[marks < 60] = 0', tc='amber', hi={(0, 3), (0, 5)}, hstep=4, hcolor='#f59e0b'),
        stext(380, 205, '(marks >= 60) & (marks < 90)  ·  | or  ·  ~ not  ·  brackets required', 'cyan', 12, step=5),
        stext(380, 230, 'mask.sum() → how many pass · mask.mean() → fraction · np.any / np.all', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 250, *elems), [
        'An array of marks.',
        'A comparison is applied element-wise and returns a boolean array of the same shape.',
        'Indexing with the boolean array keeps only the True positions: a new 1-D array (a copy).',
        'Assigning through a mask changes the original elements in place: every fail mark set to 0.',
        'Combine conditions with &amp;, | and ~; True counts as 1, so sum and mean give counts and fractions.',
    ])


def fancy_anim():
    elems = [
        stext(380, 24, 'Fancy indexing: select with arrays of positions', 'blue', 15, bold=True),
        grid(30, 60, [82, 61, 91, 55, 88, 47], cw=50, step=1, title='a', clabels=True),
        grid(380, 60, [91, 82, 47], cw=50, step=2, title='a[[2, 0, 5]]', tc='green'),
        stext(560, 80, 'any order, repeats allowed', 'green', 11, step=2, anchor='start'),
        grid(30, 150, [[82, 61, 70], [91, 88, 79], [84, 72, 66]], cw=50, step=3, title='m', rlabels=True, hi={(0, 2), (2, 0)}, hstep=3, hcolor='#8b5cf6'),
        stext(330, 175, 'm[[0, 2], [2, 0]] → [70, 84]', 'purple', 13, step=3, anchor='start', bold=True),
        stext(330, 200, 'pairs: (0,2) and (2,0), not a block', 'purple', 11, step=3, anchor='start'),
        stext(330, 225, 'm[np.ix_([0, 2], [0, 2])] → 2×2 block', 'amber', 12, step=4, anchor='start'),
        stext(380, 262, 'fancy indexing always returns a COPY · np.argsort / np.argmax give positions to use with it', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'A 1-D array with positions 0–5.',
        'Indexing with a list of positions picks those elements in that order.',
        'On 2-D arrays, two index arrays are paired element by element: (0, 2) and (2, 0).',
        'To take a rectangular sub-matrix from chosen rows and columns, use <code>np.ix_</code>.',
        'Unlike basic slices, fancy indexing copies data. It combines well with argsort/argmax, which return positions.',
    ])


def view_copy_anim():
    elems = [
        stext(380, 24, 'Views share memory, copies do not', 'blue', 15, bold=True),
        grid(30, 60, [10, 20, 30, 40, 50], cw=50, step=1, title='a'),
        grid(30, 150, [20, 30, 40], cw=50, step=2, title='v = a[1:4]  (view)', tc='purple'),
        sarrow(105, 122, 105, 90, 'purple', step=2), sarrow(155, 122, 155, 90, 'purple', step=2),
        stext(330, 75, 'v[0] = 99  →  a = [10 99 30 40 50]', 'red', 13, step=3, anchor='start', bold=True, focus=3),
        stext(330, 100, 'the slice is a window onto a\'s buffer', 'red', 11, step=3, anchor='start'),
        grid(30, 232, [20, 30, 40], cw=50, step=4, title='c = a[1:4].copy()', tc='green'),
        stext(330, 175, 'views: basic slices, reshape*, .T, ravel*', 'purple', 12, step=4, anchor='start'),
        stext(330, 200, 'copies: fancy/boolean indexing, flatten, astype, .copy()', 'green', 12, step=4, anchor='start'),
        stext(330, 238, 'check: np.shares_memory(a, v) → True · v.base is a', 'cyan', 12, step=5, anchor='start'),
    ]
    return anim(canvas(760, 275, *elems), [
        'An original array.',
        'A basic slice does not copy: <code>v</code> is a view describing part of the same memory.',
        'Writing to the view changes the original. Surprising if you expected a copy, but it is what makes slicing fast.',
        'Call <code>.copy()</code> when you need independence. Fancy and boolean indexing always copy.',
        '<code>np.shares_memory</code> or the <code>.base</code> attribute tell you which one you have.',
    ])


def where_anim():
    elems = [
        stext(380, 24, 'Conditional values without loops', 'blue', 15, bold=True),
        grid(30, 60, [82, 61, 91, 55, 47], cw=56, step=1, title='marks'),
        grid(30, 130, ['P', 'P', 'P', 'F', 'F'], cw=56, step=2, title="np.where(marks >= 60, 'P', 'F')", tc='green'),
        grid(400, 60, ['B', 'C', 'A', 'F', 'F'], cw=56, step=3, title='np.select([≥85, ≥70, ≥60], [A, B, C], F)', tc='purple'),
        grid(400, 130, [82, 61, 91, 55, 50], cw=56, step=4, title='np.clip(marks, 50, 100)', tc='amber', hi={(0, 4)}, hstep=4, hcolor='#f59e0b'),
        stext(380, 205, 'np.where(cond) with ONE argument → indices where True (like np.nonzero) → (array([0, 1, 2]),)', 'cyan', 12, step=5),
        stext(380, 230, 'all vectorised: the condition is computed for the whole array at once', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 250, *elems), [
        'Marks of five students.',
        '<code>np.where(cond, x, y)</code> picks x where the condition is True, y elsewhere.',
        '<code>np.select</code> handles several conditions in order, with a default.',
        '<code>np.clip</code> limits values to a range, here a minimum of 50 (e.g. grace marks floor).',
        'With a single argument, <code>np.where</code> returns the indices of True elements.',
    ])


# ============================================================ section 3
def ufunc_anim():
    elems = [
        stext(380, 24, 'Universal functions (ufuncs): element-wise, in C', 'blue', 15, bold=True),
        grid(30, 60, [82, 61, 91, 55], cw=50, step=1, title='a'),
        grid(30, 125, [10, 20, 5, 15], cw=50, step=1, title='b'),
        stext(255, 105, 'a + b', 'amber', 14, step=2, bold=True), sarrow(240, 112, 290, 112, 'amber', step=2),
        grid(300, 92, [92, 81, 96, 70], cw=50, step=2, title='np.add(a, b)', tc='green'),
        stext(560, 70, 'arithmetic: + - * / // % **', 'purple', 12, step=3, anchor='start'),
        stext(560, 92, 'math: np.sqrt, exp, log, sin', 'purple', 12, step=3, anchor='start'),
        stext(560, 114, 'compare: > == !=  → bool', 'purple', 12, step=3, anchor='start'),
        stext(560, 136, 'np.maximum(a, b), np.abs', 'purple', 12, step=3, anchor='start'),
        stext(380, 200, 'ufunc methods: np.add.reduce (= sum) · np.add.accumulate (= cumsum) · np.multiply.outer (table)', 'cyan', 12, step=4),
        stext(380, 226, 'out= and where= parameters: write into an existing array, skip some elements', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Two arrays of the same shape.',
        'An operator such as <code>+</code> calls the ufunc <code>np.add</code>, which processes all pairs in one compiled loop.',
        'Ufuncs cover arithmetic, math functions, comparisons and element-wise max/min.',
        'Every binary ufunc also has <code>reduce</code>, <code>accumulate</code> and <code>outer</code> methods.',
        '<code>out=</code> avoids allocating a new array; <code>where=</code> computes only where a condition holds.',
    ])


def broadcast_anim():
    elems = [
        stext(380, 24, 'Broadcasting: shapes are stretched (virtually) to match', 'blue', 15, bold=True),
        grid(30, 60, [[82, 61, 70], [91, 88, 79]], cw=50, step=1, title='marks (2, 3)'),
        stext(200, 90, '−', 'amber', 22, step=2, bold=True),
        grid(225, 60, [86.5, 74.5, 74.5], cw=50, step=2, title='mean (3,)', tc='purple'),
        grid(225, 88, [86.5, 74.5, 74.5], cw=50, step=3, tc='purple'),
        stext(300, 140, 'row repeated, no copy', 'purple', 11, step=3),
        sarrow(385, 88, 425, 88, 'green', step=4),
        grid(430, 60, [[-4.5, -13.5, -4.5], [4.5, 13.5, 4.5]], cw=56, step=4, title='centred (2, 3)', tc='green'),
        _codebox(20, 165, 360, 90, ['rule: compare shapes from the RIGHT', '(2, 3) and (3,)   → OK, result (2, 3)', '(2, 3) and (2, 1) → OK, result (2, 3)',
                                    '(2, 3) and (2,)   → ValueError'], 'amber', step=5, tcolor='#fde68a'),
        stext(570, 190, 'dimensions are compatible when', 'cyan', 12, step=5),
        stext(570, 212, 'equal, or one of them is 1', 'cyan', 12, step=5, bold=True),
        stext(570, 240, 'per-student: x - x.mean(axis=1, keepdims=True)', 'gray', 11, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'A 2 × 3 marks matrix (2 students, 3 subjects).',
        'We subtract the subject means: a 1-D array of 3 values.',
        'NumPy treats the 1-D array as if it were repeated for every row, without copying memory.',
        'The result is the element-wise difference: every mark centred on its subject mean.',
        'The rule: align shapes from the right; each pair of dimensions must be equal or 1. Otherwise: "operands could not be broadcast together".',
    ])


def axis_agg_anim():
    elems = [
        stext(380, 24, 'Aggregations and the axis parameter', 'blue', 15, bold=True),
        grid(40, 70, [[82, 61, 70], [91, 88, 79]], cw=56, ch=32, step=1, title='marks', rlabels=True),
        sarrow(124, 140, 124, 165, 'green', step=2),
        grid(40, 170, [173, 149, 149], cw=56, step=2, title=None),
        stext(124, 222, 'sum(axis=0) → per column', 'green', 12, step=2),
        sarrow(215, 102, 260, 102, 'purple', step=3),
        grid(265, 72, [[213], [258]], cw=56, ch=32, step=3),
        stext(380, 155, 'sum(axis=1) → per row', 'purple', 12, step=3),
        stext(560, 80, 'sum() → 471 (all)', 'amber', 13, step=4, bold=True),
        stext(560, 105, 'mean · std · min · max', 'amber', 12, step=4),
        stext(560, 125, 'argmin · argmax · prod', 'amber', 12, step=4),
        stext(560, 145, 'cumsum · any · all · ptp', 'amber', 12, step=4),
        stext(560, 200, 'keepdims=True → (2, 1)', 'cyan', 12, step=5, bold=True),
        stext(560, 222, 'ready to broadcast back', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'A 2 × 3 array.',
        '<code>axis=0</code> collapses the rows (moves down): one result per column.',
        '<code>axis=1</code> collapses the columns (moves across): one result per row.',
        'Without axis, the whole array is reduced to one value. Most statistics follow the same rule.',
        '<code>keepdims=True</code> keeps the reduced axis with length 1, so the result broadcasts against the original.',
    ])


def sort_anim():
    elems = [
        stext(380, 24, 'Sorting and searching', 'blue', 15, bold=True),
        grid(30, 60, [82, 61, 91, 55, 88], cw=50, step=1, title='a', clabels=True),
        grid(330, 60, [55, 61, 82, 88, 91], cw=50, step=2, title='np.sort(a)', tc='green'),
        grid(30, 140, [3, 1, 0, 4, 2], cw=50, step=3, title='np.argsort(a) → positions', tc='purple'),
        stext(330, 155, 'a[np.argsort(a)] == np.sort(a)', 'purple', 12, step=3, anchor='start'),
        stext(330, 178, 'sort another array by a: names[np.argsort(a)]', 'purple', 12, step=3, anchor='start'),
        stext(30, 222, 'np.argmax(a) → 2 · np.unique(x, return_counts=True) · np.searchsorted(sorted, 75) → 2', 'amber', 12, step=4, anchor='start'),
        stext(30, 248, 'np.partition(a, 2) / argpartition: top-k without a full sort (O(n))', 'cyan', 12, step=5, anchor='start'),
    ]
    return anim(canvas(760, 265, *elems), [
        'Unsorted marks with their positions.',
        '<code>np.sort</code> returns a sorted copy (<code>a.sort()</code> sorts in place).',
        '<code>argsort</code> returns the positions that would sort the array: use them to reorder other arrays the same way.',
        '<code>argmax</code>, <code>unique</code> and <code>searchsorted</code> (insertion position in a sorted array) cover most search needs.',
        '<code>partition</code>/<code>argpartition</code> find the k smallest/largest without sorting everything.',
    ])


def nan_anim():
    elems = [
        stext(380, 24, 'NaN and inf: special floating-point values', 'blue', 15, bold=True),
        grid(30, 60, [82, 'nan', 91, 'nan', 75], cw=56, step=1, title='a (float64)', hi={(0, 1), (0, 3)}, hstep=1, hcolor='#ef4444'),
        sbox(360, 50, 380, 40, 'np.mean(a) → nan', 'NaN propagates through arithmetic', 'red', step=2, size=12),
        sbox(360, 98, 380, 40, 'np.nanmean(a) → 82.67', 'nan-functions ignore NaN', 'green', step=3, size=12),
        stext(30, 160, 'np.isnan(a) → [F T F T F]  ·  a[~np.isnan(a)]  ·  np.nan_to_num(a, nan=0)', 'purple', 12, step=4, anchor='start'),
        stext(30, 186, 'np.nan == np.nan → False  (always use np.isnan)', 'red', 12, step=4, anchor='start', bold=True),
        stext(30, 214, '1 / 0.0 → inf (RuntimeWarning) · 0 / 0.0 → nan · np.isfinite, np.isinf', 'amber', 12, step=5, anchor='start'),
        stext(30, 240, 'integers cannot hold NaN → arrays with missing data must be float (or masked arrays)', 'cyan', 12, step=5, anchor='start'),
    ]
    return anim(canvas(760, 258, *elems), [
        'NaN ("not a number") marks missing or undefined values in float arrays.',
        'Any arithmetic with NaN gives NaN, so a plain mean becomes NaN.',
        'NaN-aware functions (nanmean, nansum, nanmax, nanstd…) skip NaN values.',
        'Detect with <code>np.isnan</code>; NaN is never equal to anything, not even itself.',
        'Division by zero gives inf or nan with a warning; integers have no NaN, so missing data forces float dtype.',
    ])


# ============================================================ section 4
def stack_anim():
    elems = [
        stext(380, 24, 'Joining and splitting arrays', 'blue', 15, bold=True),
        grid(30, 60, [[1, 2], [3, 4]], cw=40, step=1, title='a', tc='blue'),
        grid(130, 60, [[5, 6], [7, 8]], cw=40, step=1, title='b', tc='purple'),
        grid(250, 60, [[1, 2], [3, 4], [5, 6], [7, 8]], cw=40, step=2, title='vstack / axis=0', tc='green'),
        grid(380, 60, [[1, 2, 5, 6], [3, 4, 7, 8]], cw=40, step=3, title='hstack / axis=1', tc='amber'),
        stext(640, 70, 'np.stack([a, b])', 'purple', 12, step=4, bold=True),
        stext(640, 92, '→ NEW axis: (2, 2, 2)', 'purple', 12, step=4),
        stext(640, 120, 'np.column_stack', 'gray', 11, step=4), stext(640, 138, '1-D arrays → columns', 'gray', 11, step=4),
        _codebox(30, 195, 700, 60, ['np.split(x, 3) → 3 equal parts · np.array_split(x, 3) → uneven allowed · np.hsplit / np.vsplit',
                                    'concatenate once from a list: appending in a loop copies every time (O(n²))'], 'cyan', step=5, tcolor='#a5f3fc'),
    ]
    return anim(canvas(760, 270, *elems), [
        'Two 2 × 2 arrays.',
        '<code>np.concatenate([a, b], axis=0)</code> (= <code>vstack</code>) stacks rows: shape (4, 2).',
        '<code>axis=1</code> (= <code>hstack</code> for 2-D) joins side by side: shape (2, 4).',
        '<code>np.stack</code> adds a new dimension instead of extending an existing one.',
        'Splitting is the reverse. Collect pieces in a list and concatenate once: <code>np.append</code> in a loop copies the whole array every time.',
    ])


def newaxis_anim():
    elems = [
        stext(380, 24, 'Adding and repeating axes', 'blue', 15, bold=True),
        grid(30, 60, [1, 2, 3], cw=40, step=1, title='x (3,)'),
        grid(200, 60, [[1], [2], [3]], cw=40, step=2, title='x[:, np.newaxis] (3,1)', tc='purple'),
        grid(380, 60, [1, 2, 3], cw=40, step=2, title='x[np.newaxis, :] (1,3)', tc='purple'),
        stext(560, 74, 'np.expand_dims(x, 1)', 'purple', 11, step=2, anchor='start'),
        stext(560, 94, 'np.squeeze removes 1-axes', 'purple', 11, step=2, anchor='start'),
        grid(30, 175, [[1, 2, 3], [2, 4, 6], [3, 6, 9]], cw=40, step=3, title='x[:, None] * x → table', tc='green'),
        grid(250, 175, [1, 1, 2, 2, 3, 3], cw=40, step=4, title='np.repeat(x, 2)', tc='amber'),
        grid(250, 230, [1, 2, 3, 1, 2, 3], cw=40, step=4, title=None, tc='amber'),
        stext(600, 245, '← np.tile(x, 2)', 'amber', 12, step=4),
        stext(600, 190, 'broadcasting usually', 'cyan', 11, step=5), stext(600, 208, 'avoids real repeats', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'A 1-D array with shape (3,).',
        '<code>np.newaxis</code> (or <code>None</code>) inserts an axis of length 1: a column (3, 1) or a row (1, 3).',
        'A column times a row broadcasts into a 3 × 3 multiplication table: the basis of pairwise calculations.',
        '<code>repeat</code> repeats each element; <code>tile</code> repeats the whole array. Both really copy data.',
        'Prefer broadcasting with newaxis over repeat/tile when the goal is arithmetic: it uses no extra memory.',
    ])


def setops_anim():
    elems = [
        stext(380, 24, 'Set operations on arrays', 'blue', 15, bold=True),
        grid(30, 60, [2401, 2402, 2403, 2405], cw=60, step=1, title='enrolled', tc='blue'),
        grid(30, 130, [2402, 2403, 2404], cw=60, step=1, title='attended exam', tc='purple'),
        grid(360, 50, [2402, 2403], cw=60, step=2, title='np.intersect1d → both', tc='green'),
        grid(360, 110, [2401, 2405], cw=60, step=3, title='np.setdiff1d(enrolled, attended) → absent', tc='red'),
        grid(360, 170, [2404], cw=60, step=3, title='np.setdiff1d(attended, enrolled) → not enrolled!', tc='amber'),
        grid(30, 215, ['F', 'T', 'T', 'F'], cw=60, step=4, title='np.isin(enrolled, attended)', tc='cyan'),
        stext(560, 245, 'np.union1d · np.unique · np.setxor1d', 'gray', 11, step=5),
        stext(560, 228, 'all return sorted unique values', 'gray', 11, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'Two arrays of roll numbers: enrolled students and those who attended the exam.',
        '<code>intersect1d</code>: present in both.',
        '<code>setdiff1d</code>: in the first but not the second: absentees one way, and attendees who were never enrolled the other way.',
        '<code>isin</code> keeps the original order and shape and gives a mask for filtering.',
        'Set functions return sorted unique values; <code>union1d</code> and <code>setxor1d</code> complete the set.',
    ])


def layout_anim():
    elems = [
        stext(380, 24, 'Memory layout: C order vs Fortran order', 'blue', 15, bold=True),
        grid(30, 60, [['a', 'b', 'c'], ['d', 'e', 'f']], cw=50, step=1, title='logical 2 × 3'),
        stext(470, 52, "C order (row-major, NumPy default)", 'green', 12, step=2, bold=True),
        grid(330, 60, ['a', 'b', 'c', 'd', 'e', 'f'], cw=50, step=2),
        stext(470, 120, "F order (column-major, Fortran/MATLAB)", 'purple', 12, step=3, bold=True),
        grid(330, 128, ['a', 'd', 'b', 'e', 'c', 'f'], cw=50, step=3),
        stext(380, 200, 'summing along the contiguous direction reads memory sequentially → faster (cache)', 'amber', 12, step=4),
        stext(380, 226, 'a.flags["C_CONTIGUOUS"] · np.ascontiguousarray(a) · a.T of a C array is F-contiguous', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'The same 2 × 3 array can be laid out in memory in two ways.',
        'C order stores row after row: the last index changes fastest.',
        'Fortran order stores column after column: the first index changes fastest.',
        'Operations that walk memory sequentially use the CPU cache well, so layout can affect speed for big arrays.',
        'Flags tell you the layout; some libraries require contiguous input, which <code>ascontiguousarray</code> provides.',
    ])


def vectorize_anim():
    elems = [
        stext(380, 24, 'Applying a custom function: from slow to fast', 'blue', 15, bold=True),
        sbox(20, 55, 230, 66, 'Python loop', 'for x in arr: f(x)', 'red', step=1, size=13),
        sbox(265, 55, 230, 66, 'np.vectorize(f)', 'convenient, still a Python loop', 'amber', step=2, size=13),
        sbox(510, 55, 230, 66, 'rewrite with ufuncs', 'np.where / arithmetic / np.select', 'green', step=3, size=13, focus=3),
        sbox(20, 140, 350, 56, 'np.apply_along_axis(f, 1, a)', 'f gets each row; Python call per row', 'purple', step=4, size=12),
        sbox(390, 140, 350, 56, 'Numba @njit / Cython', 'compile a real loop when no ufunc form exists', 'cyan', step=5, size=12),
        stext(380, 230, 'np.vectorize is for convenience, not performance (documented as such)', 'amber', 12, step=2),
    ]
    return anim(canvas(760, 250, *elems), [
        'A Python loop calls your function once per element: slow for big arrays.',
        '<code>np.vectorize</code> makes the function accept arrays and broadcast, but internally it is still a loop.',
        'The fast path is expressing the logic with ufuncs and array operations.',
        '<code>apply_along_axis</code> passes rows/columns to a Python function: convenient, not fast.',
        'For genuinely loop-shaped algorithms, compile with Numba or Cython.',
    ])


# ============================================================ section 5
def matmul_anim():
    elems = [
        stext(380, 24, '* is element-wise · @ is matrix multiplication', 'blue', 15, bold=True),
        grid(30, 60, [[82, 61, 70], [91, 88, 79]], cw=46, step=1, title='marks (2×3)', hi={(0, 0), (0, 1), (0, 2)}, hstep=3, hcolor='#8b5cf6'),
        stext(195, 92, '@', 'amber', 20, step=2, bold=True),
        grid(215, 60, [[0.5], [0.3], [0.2]], cw=50, step=2, title='weights (3×1)', hi={(0, 0), (1, 0), (2, 0)}, hstep=3, hcolor='#8b5cf6'),
        stext(285, 92, '=', 'amber', 20, step=2, bold=True),
        grid(305, 60, [[73.3], [87.7]], cw=60, step=2, title='(2×1)', hi={(0, 0)}, hstep=3, hcolor='#10b981'),
        stext(380, 185, 'row · column: 82×0.5 + 61×0.3 + 70×0.2 = 73.3', 'purple', 13, step=3, bold=True),
        _codebox(420, 50, 320, 105, ['(m × n) @ (n × p) → (m × p)', 'inner sizes must match', '', 'a * b   → same shape, element-wise', 'np.dot(a, b) = a @ b for 2-D'], 'cyan', step=4, tcolor='#a5f3fc'),
        stext(380, 215, 'np.matmul broadcasts over leading "batch" dimensions: (64, 3, 4) @ (4, 2) → (64, 3, 2)', 'amber', 12, step=5),
        stext(380, 240, 'for 1-D vectors: a @ b = dot product (a scalar)', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 258, *elems), [
        'Marks of 2 students in 3 subjects.',
        'Matrix-multiplying by a 3 × 1 weight vector gives a 2 × 1 result: one weighted score per student.',
        'Each result is a row of the left matrix "dotted" with the column of the right one.',
        'Shapes: (m × n) @ (n × p) → (m × p). <code>*</code> instead multiplies element by element and needs broadcastable shapes.',
        '<code>@</code>/<code>matmul</code> treats extra leading dimensions as a batch; for 1-D arrays it is the dot product.',
    ])


def linalg_anim():
    elems = [
        stext(380, 24, 'Solving linear equations with np.linalg', 'blue', 15, bold=True),
        _codebox(20, 50, 300, 90, ['2x + 3y = 23   (fee in thousands)', ' x + 4y = 24', '', 'A = [[2, 3], [1, 4]],  b = [23, 24]'], 'gray', step=1),
        sbox(345, 50, 190, 50, 'np.linalg.solve(A, b)', '→ [4. 5.]', 'green', step=2, size=13, focus=2),
        sbox(550, 50, 190, 50, 'np.linalg.inv(A) @ b', 'same answer, slower, less accurate', 'amber', step=3, size=11),
        stext(380, 170, 'det(A) = 5 → invertible (det = 0 → singular: no unique solution)', 'purple', 12, step=4),
        stext(380, 195, 'eig / eigh → eigenvalues (PCA) · svd · norm · lstsq (best fit when no exact solution)', 'cyan', 12, step=5),
        stext(380, 220, 'np.linalg.LinAlgError: Singular matrix', 'red', 12, step=4),
    ]
    return anim(canvas(760, 240, *elems), [
        'Two equations with two unknowns written as a matrix A and a vector b.',
        '<code>solve</code> finds x with A @ x = b directly: x = 4, y = 5.',
        'Computing the inverse first works but is slower and numerically less stable: prefer solve.',
        'The determinant shows whether a unique solution exists; a singular matrix raises LinAlgError.',
        'The same module offers eigen-decomposition, SVD, norms and least squares, the building blocks of PCA and regression.',
    ])


def stats_anim():
    elems = [
        stext(380, 24, 'Descriptive statistics in NumPy', 'blue', 15, bold=True),
        grid(30, 60, [55, 61, 70, 75, 82, 88, 91, 99], cw=46, step=1, title='marks (sorted for display)'),
        sbox(30, 115, 160, 50, 'mean 77.6', 'median 78.5', 'blue', step=2, size=13),
        sbox(205, 115, 180, 50, 'std (ddof=0) 14.2', 'ddof=1 (sample) 15.2', 'purple', step=3, size=13),
        sbox(400, 115, 160, 50, 'percentile 90', '→ 93.4', 'amber', step=4, size=13),
        sbox(575, 115, 165, 50, 'corrcoef', 'attendance vs marks', 'green', step=5, size=13),
        stext(380, 200, 'np.std defaults to population (ddof=0) · pandas .std() defaults to sample (ddof=1)', 'red', 12, step=3, focus=3),
        stext(380, 225, 'np.cov / np.corrcoef: rows are variables by default (rowvar=True)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Eight students\' marks.',
        'Centre: mean and median (robust to outliers).',
        'Spread: standard deviation. <code>ddof</code> chooses population (n) or sample (n − 1) in the denominator.',
        'Percentiles/quantiles: 90 % of students scored at or below this value.',
        'Relationships: correlation coefficient between two variables, e.g. attendance and marks.',
    ])


def cumsum_anim():
    elems = [
        stext(380, 24, 'Running totals, differences and moving averages', 'blue', 15, bold=True),
        grid(30, 60, [52, 55, 49, 58, 60, 57], cw=50, step=1, title='daily attendance'),
        grid(30, 125, [52, 107, 156, 214, 274, 331], cw=50, step=2, title='np.cumsum', tc='green'),
        grid(400, 60, [3, -6, 9, 2, -3], cw=50, step=3, title='np.diff (n-1 values)', tc='purple'),
        grid(400, 125, [52.0, 54.0, 55.7, 58.3], cw=56, step=4, title="np.convolve(x, np.ones(3)/3, 'valid')", tc='amber'),
        stext(380, 200, 'moving average of 3 days: (52+55+49)/3 = 52.0, (55+49+58)/3 = 54.0 …', 'amber', 12, step=4),
        stext(380, 226, 'sliding_window_view(x, 3).mean(axis=1) gives the same, as a view of windows', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Daily attendance counts.',
        '<code>cumsum</code> gives the running total.',
        '<code>diff</code> gives day-to-day change (one value shorter).',
        'A moving average is a convolution with equal weights; "valid" mode keeps only full windows.',
        '<code>sliding_window_view</code> builds the windows without copying, then any reduction works.',
    ])


def random_anim():
    elems = [
        stext(380, 24, 'Random numbers: Generator, seed, reproducibility', 'blue', 15, bold=True),
        sbox(20, 55, 220, 60, 'rng = np.random.default_rng(42)', 'own state, PCG64', 'green', step=1, size=12),
        sbox(270, 55, 220, 60, 'same seed → same numbers', 'reproducible experiments', 'purple', step=2, size=12, focus=2),
        sbox(520, 55, 220, 60, 'np.random.seed / rand', 'legacy global state', 'gray', step=5, size=12),
        stext(30, 150, "rng.integers(0, 101, 5) · rng.random(3) · rng.normal(70, 10, 100)", 'amber', 12, step=3, anchor='start'),
        stext(30, 175, "rng.choice(names, 3, replace=False) · rng.permutation(n) · rng.shuffle(x)", 'amber', 12, step=4, anchor='start'),
        stext(30, 210, 'train/test split: idx = rng.permutation(n); train, test = idx[:800], idx[800:]', 'cyan', 12, step=4, anchor='start'),
        stext(30, 236, 'pseudo-random: deterministic algorithm, not for passwords/tokens (use the secrets module)', 'red', 12, step=5, anchor='start'),
    ]
    return anim(canvas(760, 255, *elems), [
        'Create a Generator with <code>default_rng(seed)</code>; it keeps its own state.',
        'The same seed always produces the same sequence, so results can be reproduced and checked.',
        'Draw integers, uniform floats or samples from distributions (normal, binomial, poisson…).',
        'Sample with or without replacement, permute indices, or shuffle in place, e.g. for train/test splits.',
        'The old <code>np.random.seed</code> API uses one global state; prefer Generators. Never use NumPy random for security.',
    ])


# ============================================================ section 6
def speed_anim():
    elems = [
        stext(380, 24, 'Where the time goes: Python loop vs NumPy', 'blue', 15, bold=True),
        stext(30, 62, 'Python, per element:', 'red', 13, step=1, anchor='start', bold=True),
        sbox(30, 72, 120, 34, 'fetch object', '', 'red', step=1, size=11), sbox(155, 72, 120, 34, 'check type', '', 'red', step=1, size=11),
        sbox(280, 72, 120, 34, 'dispatch +', '', 'red', step=1, size=11), sbox(405, 72, 120, 34, 'new int object', '', 'red', step=1, size=11),
        sbox(530, 72, 120, 34, 'refcounts', '', 'red', step=1, size=11),
        stext(30, 140, 'NumPy, once per array:', 'green', 13, step=2, anchor='start', bold=True),
        sbox(30, 150, 200, 34, 'check dtypes & shapes', '', 'green', step=2, size=11),
        sbox(240, 150, 410, 34, 'tight C loop: load · add · store (SIMD: 4–8 values at a time)', '', 'green', step=3, size=11),
        stext(380, 220, 'the per-element overhead is what you remove; the arithmetic itself is the same', 'amber', 12, step=4, focus=4),
        stext(380, 246, 'contiguous memory → CPU cache prefetching · many BLAS routines multi-threaded (matmul)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 262, *elems), [
        'A Python loop pays interpreter overhead for every element: fetching objects, checking types, dispatching, allocating results.',
        'NumPy does the checks once for the whole array.',
        'Then a compiled loop processes raw values, often several per CPU instruction (SIMD).',
        'The speed-up comes from removing per-element overhead, not from faster arithmetic.',
        'Contiguous memory helps caching; linear algebra calls optimised BLAS libraries that can use several cores.',
    ])


def inplace_anim():
    elems = [
        stext(380, 24, 'Temporary arrays and in-place operations', 'blue', 15, bold=True),
        stext(30, 62, 'y = 2 * x + 1   (x: 800 MB)', 'red', 13, step=1, anchor='start', bold=True),
        sbox(30, 72, 160, 40, 'x', '800 MB', 'gray', step=1, size=12),
        sbox(205, 72, 160, 40, 'tmp = 2 * x', '+800 MB', 'red', step=1, size=12),
        sbox(380, 72, 160, 40, 'y = tmp + 1', '+800 MB', 'red', step=1, size=12),
        stext(620, 92, 'peak ≈ 2.4 GB', 'red', 13, step=1, bold=True),
        stext(30, 150, 'y = x * 2;  y += 1   or   np.multiply(x, 2, out=y); np.add(y, 1, out=y)', 'green', 13, step=2, anchor='start', bold=True),
        stext(30, 175, 'peak ≈ 1.6 GB (one result array, reused)', 'green', 12, step=2, anchor='start'),
        stext(30, 205, 'x *= 2 modifies x itself: no new memory, but the original values are gone (and views see it)', 'amber', 12, step=3, anchor='start'),
        stext(30, 230, 'int array: x *= 0.5 → error (cannot cast float result into int in place)', 'red', 12, step=4, anchor='start'),
        stext(30, 255, 'choose smaller dtypes (float32) when precision allows: half the memory', 'cyan', 12, step=5, anchor='start'),
    ]
    return anim(canvas(760, 272, *elems), [
        'Each operator in an expression creates a full temporary array: for big data the peak memory is a multiple of the input.',
        'Augmented assignment (<code>+=</code>) and <code>out=</code> reuse an existing buffer instead of allocating new ones.',
        'In-place on the input saves the most memory but destroys the original data (and changes any views of it).',
        'In-place operations must keep the dtype: multiplying an int array by 0.5 in place raises a casting error.',
        'Smaller dtypes halve memory and bandwidth when the precision is sufficient.',
    ])


def einsum_anim():
    elems = [
        stext(380, 24, 'Broadcasting can explode memory · einsum and matmul avoid it', 'blue', 15, bold=True),
        sbox(20, 55, 350, 70, 'pairwise diff: X[:, None, :] - X[None, :, :]', 'n = 20,000 points, d = 50 → 20k × 20k × 50 × 8 B = 160 GB', 'red', step=1, size=12),
        sbox(390, 55, 350, 70, '‖a−b‖² = ‖a‖² + ‖b‖² − 2·a·b', 'uses X @ X.T → only n × n = 3.2 GB', 'green', step=2, size=12, focus=2),
        _codebox(20, 145, 720, 80, ["np.einsum('ij,ij->i', A, B)      # row-wise dot products, no temporary A*B",
                                     "np.einsum('ij,jk->ik', A, B)     # = A @ B",
                                     "np.einsum('ii->', M)              # trace"], 'purple', step=3, tcolor='#c4b5fd'),
        stext(380, 250, 'rule: estimate result size = product of broadcast shape × itemsize before running', 'amber', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 268, *elems), [
        'A naive pairwise-difference broadcast creates an n × n × d array: impossible for large n.',
        'Rewriting the maths with a matrix product needs only the n × n result.',
        '<code>einsum</code> expresses sums over indices (dot products, traces, batch matmul) without building big intermediates.',
        'Before broadcasting, multiply out the result shape and itemsize to estimate memory.',
    ])


def io_anim():
    elems = [
        stext(380, 24, 'Saving, loading and memory-mapping arrays', 'blue', 15, bold=True),
        sbox(20, 55, 230, 70, 'np.save / np.load', '.npy: one array, binary\nexact dtype & shape', 'green', step=1, size=12),
        sbox(265, 55, 230, 70, 'np.savez(_compressed)', '.npz: several named arrays', 'purple', step=2, size=12),
        sbox(510, 55, 230, 70, 'np.savetxt / loadtxt', 'CSV/text: readable,\nslow, loses precision', 'amber', step=3, size=12),
        sbox(20, 145, 720, 60, "np.load('big.npy', mmap_mode='r')  ·  np.memmap('data.bin', dtype='float32', shape=(n, d))",
             'data stays on disk; slices are read into memory only when accessed', 'cyan', step=4, size=12, focus=4),
        stext(380, 235, "np.load(..., allow_pickle=False) is the default: never unpickle files from untrusted sources", 'red', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        '<code>.npy</code> stores one array with its dtype and shape: fast and exact.',
        '<code>.npz</code> bundles several arrays under names (optionally compressed).',
        'Text formats are human-readable but slower, larger, and may round floats.',
        'Memory-mapping lets you work with arrays larger than RAM: the OS loads pages only when they are touched.',
        'Object arrays require pickle; loading pickles from untrusted files can execute code, so it is disabled by default.',
    ])


def precision_anim():
    elems = [
        stext(380, 24, 'Floating-point pitfalls', 'blue', 15, bold=True),
        sbox(20, 55, 350, 54, '0.1 + 0.2 == 0.3  →  False', '0.30000000000000004 (binary cannot store 0.1 exactly)', 'red', step=1, size=12),
        sbox(390, 55, 350, 54, 'np.isclose / np.allclose', 'compare with tolerance (rtol, atol)', 'green', step=2, size=12, focus=2),
        sbox(20, 125, 350, 54, 'float32: 16777216 + 1 = 16777216', 'only ~7 significant digits', 'amber', step=3, size=12),
        sbox(390, 125, 350, 54, 'sum of many floats', 'np.sum uses pairwise summation (more accurate than a loop)', 'purple', step=4, size=12),
        sbox(20, 195, 720, 46, 'integers: overflow wraps · // and % follow floor rules for negatives (-7 // 2 = -4) · money → integer paise or Decimal', '', 'cyan', step=5, size=12),
    ]
    return anim(canvas(760, 258, *elems), [
        'Decimal fractions such as 0.1 have no exact binary representation, so equality checks on floats fail.',
        'Compare with a tolerance: <code>np.isclose</code> element-wise, <code>np.allclose</code> for whole arrays.',
        'float32 keeps about 7 significant digits; adding a small number to a large one can do nothing.',
        'Summation order matters; NumPy uses pairwise summation to reduce error, so results can differ slightly from a Python loop.',
        'Integer overflow and floor division rules are other sources of surprise; use integers (paise) or Decimal for money.',
    ])


# ============================================================ section 7
def pandas_np_anim():
    elems = [
        stext(380, 24, 'pandas sits on NumPy (and Arrow)', 'blue', 15, bold=True),
        stable(20, 55, ['name', 'marks', 'attendance'], [['Anuj', '82', '0.92'], ['Vineeta', '91', '0.97'], ['Rohan', 'NaN', '0.71']], [80, 70, 90], step=1, title='DataFrame', title_color='blue'),
        sarrow(262, 100, 312, 100, 'green', step=2),
        grid(320, 68, [[82.0, 0.92], [91.0, 0.97], ['nan', 0.71]], cw=60, step=2, title='.to_numpy()', tc='green'),
        stext(600, 80, 'float64 (2-D)', 'green', 12, step=2, anchor='start'),
        stext(600, 100, 'labels dropped', 'green', 12, step=2, anchor='start'),
        sarrow(312, 160, 262, 160, 'purple', step=3),
        stext(380, 190, 'pd.DataFrame(arr, columns=[...]) · np functions work on Series: np.log(df["marks"]) keeps the index', 'purple', 12, step=3),
        stext(380, 215, 'mixed dtypes → to_numpy() gives object dtype (slow) · select numeric columns first', 'amber', 12, step=4),
        stext(380, 240, 'scikit-learn takes DataFrames but works on the underlying NumPy array', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 258, *elems), [
        'A DataFrame adds labels (index, column names) and per-column dtypes on top of arrays.',
        '<code>to_numpy()</code> returns the raw 2-D NumPy array (labels gone); NaN stays as np.nan in float columns.',
        'Arrays convert back with pd.DataFrame; NumPy ufuncs applied to a Series return a Series with the same index.',
        'If columns have different types, the common dtype is object, which loses NumPy\'s speed. Select numeric columns first.',
        'Machine-learning libraries accept DataFrames but compute on NumPy arrays internally.',
    ])


def ml_prep_anim():
    elems = [
        stext(380, 24, 'NumPy for ML preprocessing', 'blue', 15, bold=True),
        grid(20, 60, [[82, 0.92], [91, 0.97], [58, 0.71], [75, 0.85]], cw=55, step=1, title='X (4 × 2)'),
        sbox(160, 55, 180, 50, 'standardise', '(X − mean) / std, axis=0', 'green', step=2, size=12),
        sbox(160, 115, 180, 50, 'min-max scale', '(X − min) / (max − min)', 'purple', step=3, size=12),
        sbox(360, 55, 180, 50, 'one-hot encode', 'np.eye(k)[codes]', 'amber', step=4, size=12),
        grid(560, 70, [[1, 0, 0], [0, 1, 0], [1, 0, 0], [0, 0, 1]], cw=40, step=4, title='DBDA DAC DAI', tc='amber'),
        sbox(360, 115, 180, 50, 'shuffle & split', 'rng.permutation(n)', 'cyan', step=5, size=12),
        stext(380, 215, 'fit statistics on the TRAINING split only, then apply them to test data (no data leakage)', 'red', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 235, *elems), [
        'A feature matrix: rows are students, columns are features (marks, attendance).',
        'Standardisation: subtract each column\'s mean and divide by its std, so features are comparable.',
        'Min-max scaling maps each column to 0–1.',
        'One-hot encoding: index rows of an identity matrix with category codes.',
        'Shuffle indices and split. Compute means/stds on the training part only to avoid leaking test information.',
    ])


def np2_anim():
    elems = [
        stext(380, 24, 'NumPy 2.x: what changed', 'blue', 15, bold=True),
        sbox(20, 55, 350, 52, 'type promotion (NEP 50)', 'float32 array * 3.0 → float32; int8 + 300 → OverflowError', 'blue', step=1, size=12),
        sbox(390, 55, 350, 52, 'scalar repr', 'np.float64(0.5) instead of 0.5', 'purple', step=2, size=12),
        sbox(20, 117, 350, 52, 'cleaned-up namespace', 'np.float_, np.Inf, np.NaN, np.in1d, row_stack… removed', 'red', step=3, size=12),
        sbox(390, 117, 350, 52, 'copy keyword', 'np.array(x, copy=False) raises if a copy is needed', 'amber', step=4, size=12),
        sbox(20, 179, 350, 52, 'StringDType', 'variable-length strings in arrays', 'green', step=5, size=12),
        sbox(390, 179, 350, 52, 'ABI break (2.0)', 'compiled extensions rebuilt for NumPy 2', 'gray', step=5, size=12),
        stext(380, 258, 'upgrade aid: ruff check --select NPY201 flags removed APIs automatically', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'NumPy 2.0 (June 2024) changed promotion rules: Python scalars no longer upcast arrays, and out-of-range values raise.',
        'Scalars print with their type, e.g. <code>np.float64(0.5)</code>, which makes types visible in notebooks.',
        'Many duplicate aliases were removed from the main namespace; old code using them fails with AttributeError.',
        'The meaning of <code>copy=False</code> became strict; use <code>np.asarray</code> for "copy only if needed".',
        'New StringDType for text; compiled packages had to be rebuilt. The ruff rule NPY201 finds most migration issues.',
    ])


def image_anim():
    elems = [
        stext(380, 24, 'An image is just an array', 'blue', 15, bold=True),
        grid(30, 60, [[0, 50, 100, 150], [50, 100, 150, 200], [100, 150, 200, 250], [150, 200, 250, 255]], cw=46, step=1, title='grayscale (H, W) uint8'),
        sbox(250, 55, 230, 52, 'colour: (H, W, 3)', 'img[:, :, 0] = red channel', 'red', step=2, size=12),
        sbox(250, 117, 230, 52, 'crop: img[100:300, 50:250]', 'a view, no copy', 'green', step=3, size=12),
        sbox(500, 55, 240, 52, 'flip: img[:, ::-1]', 'rotate: np.rot90(img)', 'purple', step=3, size=12),
        sbox(500, 117, 240, 52, 'grayscale: img @ [.299, .587, .114]', 'weighted sum of channels', 'amber', step=4, size=12),
        stext(380, 200, '255 - img → negative · img > 128 → binary mask · (img / 255.0).astype(np.float32) → model input', 'cyan', 12, step=5),
        stext(380, 225, 'beware uint8 overflow: convert to a wider type before arithmetic, clip, convert back', 'red', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'A grayscale image is a 2-D array of pixel intensities 0–255 (uint8).',
        'A colour image adds a channel axis: (height, width, 3).',
        'Cropping is slicing (a view); flipping and rotating are slicing or stride tricks.',
        'Converting to grayscale is a weighted sum over the channel axis, a matrix-vector product.',
        'Point operations (negative, threshold, scaling to 0–1) are single vectorised expressions; watch uint8 overflow.',
    ])


def loop2vec_anim():
    elems = [
        stext(380, 24, 'Turning nested loops into array operations', 'blue', 15, bold=True),
        _codebox(20, 50, 340, 130, ['# rank: how many classmates scored higher?', 'for i in range(n):', '    count = 0', '    for j in range(n):',
                                    '        if total[j] > total[i]:', '            count += 1', '    rank[i] = count + 1'], 'red', step=1, tcolor='#fca5a5'),
        sarrow(362, 115, 398, 115, 'amber', step=2),
        _codebox(400, 50, 340, 130, ['# compare every pair at once', 'higher = total[None, :] > total[:, None]', 'rank = higher.sum(axis=1) + 1', '',
                                     '# or O(n log n): ranks from a sort'], 'green', step=2, tcolor='#86efac'),
        stext(380, 205, 'recipe: inner loop → an axis · if → mask · counter → sum · accumulation → cumsum', 'purple', 12, step=3, bold=True),
        stext(380, 230, 'check memory (n × n here) and verify both versions give the same answer', 'amber', 12, step=4),
    ]
    return anim(canvas(760, 250, *elems), [
        'A typical O(n²) Python double loop: for each student, count classmates with a higher total.',
        'Broadcasting a row against a column builds the full comparison matrix; summing each row gives the counts.',
        'General recipe: each loop becomes an axis, each if becomes a mask, each counter or total becomes a reduction.',
        'Broadcast solutions trade memory for speed (n × n booleans here); always compare against the loop on small data.',
    ])


# ============================================================ section 8
def zscore_anim():
    elems = [
        stext(380, 24, 'Standardise per subject, then flag outliers', 'blue', 15, bold=True),
        grid(30, 60, [[82, 61], [91, 88], [84, 72], [20, 66]], cw=50, step=1, title='marks', hi={(3, 0)}, hstep=4, hcolor='#ef4444'),
        stext(270, 80, 'mean per column (axis=0)', 'purple', 12, step=2, anchor='start'),
        stext(270, 100, 'std per column (axis=0)', 'purple', 12, step=2, anchor='start'),
        stext(270, 130, 'z = (marks − mean) / std', 'green', 14, step=3, anchor='start', bold=True),
        stext(270, 150, 'broadcast (4,2) with (2,)', 'green', 11, step=3, anchor='start'),
        stext(270, 185, '|z| > 1.5 → unusual mark', 'red', 13, step=4, anchor='start', bold=True),
        stext(380, 235, 'z-scores make subjects comparable: +1 in a hard subject = +1 in an easy one', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'Raw marks per student and subject. Subjects differ in difficulty.',
        'Compute each subject\'s mean and standard deviation along axis 0.',
        'Broadcasting subtracts and divides column-wise in one expression.',
        'Large absolute z-scores mark unusual values for review (data error or a student who needs help).',
        'Standardised scores compare performance across subjects of different difficulty.',
    ])


def topk_anim():
    elems = [
        stext(380, 24, 'Top-k per row with argpartition', 'blue', 15, bold=True),
        grid(30, 70, [[82, 61, 70, 55], [91, 88, 79, 95], [84, 72, 66, 90]], cw=50, step=1, title='marks', clabels=True,
             hi={(0, 0), (0, 2), (1, 3), (1, 0), (2, 3), (2, 0)}, hstep=3, hcolor='#10b981'),
        sbox(280, 60, 250, 56, 'np.argpartition(-marks, 2, axis=1)[:, :2]', 'positions of the 2 largest (unordered)', 'purple', step=2, size=11),
        sbox(280, 126, 250, 56, 'np.take_along_axis(marks, idx, axis=1)', 'values at those positions', 'green', step=3, size=11),
        sbox(550, 60, 190, 122, 'then sort only k', 'argsort of the k values\n→ ordered top-k\n\nO(n) + O(k log k)', 'amber', step=4, size=12),
        stext(380, 222, 'subject names: subjects[idx] · full sort would be O(n log n) per row', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 240, *elems), [
        'Marks of 3 students in 4 subjects.',
        '<code>argpartition</code> moves the k largest positions to the front of each row without fully sorting.',
        '<code>take_along_axis</code> gathers the values at those per-row positions.',
        'Only the k selected items are then sorted, which is much cheaper than sorting every row for large data.',
        'The same positions index the subject names to give "best two subjects" per student.',
    ])


def regression_anim():
    elems = [
        stext(380, 24, 'Linear regression from scratch with NumPy', 'blue', 15, bold=True),
        sbox(20, 55, 230, 60, 'X = [1, attendance, hours]', 'add a column of ones (intercept)', 'blue', step=1, size=12),
        sbox(265, 55, 230, 60, 'normal equation', 'w = solve(XᵀX, Xᵀy)', 'green', step=2, size=12),
        sbox(510, 55, 230, 60, 'gradient descent', 'w −= lr · 2/n · Xᵀ(Xw − y)', 'purple', step=3, size=12),
        sbox(20, 135, 350, 54, 'predict: ŷ = X @ w', 'R² = 1 − SS_res / SS_tot', 'amber', step=4, size=12),
        sbox(390, 135, 350, 54, 'scale features for gradient descent', 'otherwise it converges very slowly', 'red', step=5, size=12),
        stext(380, 222, 'both methods reach the same weights; sklearn LinearRegression does the first via lstsq', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 240, *elems), [
        'Build the design matrix with a column of ones for the intercept.',
        'Closed form: solve the normal equations (or use lstsq) to get the weights in one step.',
        'Iterative: gradient descent repeatedly moves the weights against the gradient of the squared error.',
        'Predictions are one matrix product; R² measures the fit.',
        'Gradient descent needs standardised features and a suitable learning rate.',
    ])


def cosine_anim():
    elems = [
        stext(380, 24, 'Similarity between students: cosine similarity', 'blue', 15, bold=True),
        grid(30, 60, [[82, 61, 70], [91, 88, 79], [40, 30, 35]], cw=50, step=1, title='profiles (marks)'),
        sbox(220, 55, 240, 56, 'normalise rows', 'U = X / ‖X‖ (row-wise)', 'purple', step=2, size=12),
        sbox(220, 121, 240, 56, 'S = U @ U.T', 'all pairwise cosines at once', 'green', step=3, size=12, focus=3),
        grid(500, 60, [['1.00', '0.99', '1.00'], ['0.99', '1.00', '0.99'], ['1.00', '0.99', '1.00']], cw=60, step=3, title='S (n × n)', tc='green', hi={(0, 2), (2, 0)}, hstep=4, hcolor='#f59e0b'),
        stext(380, 210, 'cosine ignores scale (pattern only): centre the data first if level matters (→ correlation)', 'amber', 12, step=4, focus=4),
        stext(380, 235, 'most similar: np.argsort(-S[i])[1:k+1] (skip self)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'Each student is a vector of marks.',
        'Divide each row by its length so every vector has length 1.',
        'One matrix product gives every pairwise cosine similarity.',
        'Students 0 and 2 score 1.00 although their marks are very different: cosine compares the pattern, not the level. Centring first measures correlation instead.',
        'Sorting a row of S gives the most similar students (excluding the student itself).',
    ])


def montecarlo_anim():
    elems = [
        stext(380, 24, 'Simulation: answer probability questions by sampling', 'blue', 15, bold=True),
        sbox(20, 55, 230, 64, 'simulate 100,000 exams', 'rng.random((100_000, 20)) < 0.25', 'blue', step=1, size=12),
        sbox(265, 55, 230, 64, 'score each attempt', '.sum(axis=1) → correct answers', 'purple', step=2, size=12),
        sbox(510, 55, 230, 64, 'P(pass by guessing)', '(scores >= 8).mean()', 'green', step=3, size=12, focus=3),
        sbox(20, 140, 350, 56, 'bootstrap', 'resample marks with replacement 10,000×', 'amber', step=4, size=12),
        sbox(390, 140, 350, 56, '95% interval', 'np.percentile(means, [2.5, 97.5])', 'amber', step=4, size=12),
        stext(380, 228, 'vectorised simulation: millions of trials in milliseconds · compare with the exact formula when one exists', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Each row is one simulated exam of 20 four-option questions answered by pure guessing.',
        'Summing each row gives the number of correct answers per attempt.',
        'The fraction of attempts reaching the pass mark estimates the probability.',
        'Bootstrap: resample observed data many times to estimate the uncertainty of a statistic such as the mean.',
        'Because everything is vectorised, many trials run quickly; check against an exact result where possible.',
    ])
