from build import *
from numpyq.anims import *
from numpyq.runner import nprun, pyshow

MARKS = """
marks = np.array([[82, 61, 70, 55],
                  [91, 88, 79, 95],
                  [84, 72, 66, 90]])     # 3 students x 4 subjects
"""

SECTION = dict(level='basic', title='Indexing & Selection', questions=[

# ------------------------------------------------------------------ 6
Q('How does indexing and slicing work on multi-dimensional arrays?', 'Indexing & Slicing', minutes=7, cards=[
    definition(
        defbox('NumPy indexes each axis inside one pair of brackets: <code>a[row, col]</code>. Each position can be an integer (picks one, removes that axis), '
               'a slice <code>start:stop:step</code> (keeps the axis), or <code>:</code> (everything). Negative indexes count from the end; '
               '<code>...</code> (Ellipsis) means "all remaining axes".',
               'Basic slicing returns a <strong>view</strong> (no copy).'),
        table(['Expression', 'Result'], [
            ['a[1, 2]', 'single element'],
            ['a[1] or a[1, :]', 'row 1 (1-D)'],
            ['a[:, 2]', 'column 2 (1-D)'],
            ['a[:, 2:3]', 'column 2 as 2-D (n, 1)'],
            ['a[:2, 1:3]', 'block'],
            ['a[::-1]', 'rows reversed'],
            ['a[..., 0]', 'first element of the last axis'],
        ]),
        tags('indexing', 'slicing', 'view', 'Ellipsis'),
    ),
    analogy('A seating chart: "row 2, seat 3" is one person; "everyone in seat 3" is a column; "rows 1–2, seats 3–4" is a block. One instruction, '
            'all axes at once.'),
    slicing_anim(),
    real_world(
        scenario('Marks matrix',
                 p('With students as rows and subjects as columns: <code>marks[:, 2]</code> is one subject for everyone, <code>marks[5]</code> one student\'s '
                   'results, <code>marks[-10:]</code> the last ten students. For images (height, width, channels), <code>img[:, :, 0]</code> is the red channel '
                   'and <code>img[100:200, 50:150]</code> a crop.')),
    ),
    example(
        nprun("""
            print(marks[1, 2])            # student 1, subject 2
            print(marks[1])               # one student
            print(marks[:, 2])            # one subject, 1-D
            print(marks[:, 2:3].shape)    # keep 2-D
            print(marks[:2, 2:])          # block
            print(marks[-1, ::-1])        # last student, subjects reversed
            print(marks[..., 0])          # first column via Ellipsis
        """, setup=MARKS),
        title='Example: Selections on a 3 × 4 Marks Matrix'),
    steps(
        ('Write one index per axis', '<code>a[rows, cols]</code>, separated by commas.'),
        ('Use slices to keep dimensions', '<code>a[:, 2:3]</code> instead of <code>a[:, 2]</code> when you need 2-D.'),
        ('Remember the end is excluded', 'Like Python: <code>a[0:2]</code> is rows 0 and 1.'),
        ('Copy if you will modify', '<code>block = a[:2, :2].copy()</code>.'),
        title='Steps to Select Data'),
    crossq(
        ('a[1][2] vs a[1, 2]?', 'Same value, but a[1][2] first builds a[1] then indexes it; a[1, 2] is one operation, and a[:, 2] cannot be written with chained brackets.'),
        ('Why does a[:, 2] lose a dimension?', 'An integer index removes that axis; a slice (2:3) keeps it with length 1.'),
        ('What does a[[1]] return?', 'A list index is fancy indexing: a 2-D array containing row 1 (a copy), shape (1, n).'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('What is boolean masking? How do you filter and update values with conditions?', 'Boolean Masking', minutes=7, cards=[
    definition(
        defbox('A comparison on an array (<code>marks &gt;= 60</code>) returns a <strong>boolean array</strong> of the same shape. Indexing with it '
               '(<code>marks[mask]</code>) returns the selected elements as a new 1-D array; assigning through it (<code>marks[mask] = 0</code>) modifies the '
               'original in place.',
               'Combine conditions with <code>&amp;</code>, <code>|</code>, <code>~</code> and parentheses. Because True = 1, <code>mask.sum()</code> counts '
               'and <code>mask.mean()</code> gives the fraction; <code>np.any</code>/<code>np.all</code> test conditions, with an <code>axis</code> if needed.'),
        tags('boolean mask', 'filtering', 'np.any', 'np.all', 'count_nonzero'),
    ),
    analogy('A <strong>stencil</strong> laid over the marks sheet with holes only where the condition is true: you read (or paint) only through the holes.'),
    mask_anim(),
    real_world(
        scenario('Result processing',
                 p('Count students failing at least one subject: <code>(marks &lt; 60).any(axis=1).sum()</code>. Apply grace marks only to those between 55 and 59: '
                   '<code>marks[(marks &gt;= 55) &amp; (marks &lt; 60)] = 60</code>. No loops, and the same code works for 50 or 50,000 students.')),
    ),
    example(
        nprun("""
            mask = marks >= 60
            print(mask)
            print(marks[mask])                           # passing marks, 1-D
            print('passes:', mask.sum(), '| pass rate:', mask.mean().round(2))
            print('any fail per student:', (~mask).any(axis=1))
            print('all pass per subject:', mask.all(axis=0))

            m = marks.copy()
            m[(m >= 55) & (m < 60)] = 60                 # grace marks, in place
            print(m)
            print(np.count_nonzero(m >= 90))
        """, setup=MARKS),
        nprun("""
            marks[marks > 60 and marks < 90]
        """, setup=MARKS, title='Python (NumPy) · the classic mistake', expect_error=True),
        title='Example: Masks, Counts, any/all, Conditional Update'),
    steps(
        ('Build the mask', 'One comparison per condition, in parentheses.'),
        ('Combine', '<code>&amp;</code>, <code>|</code>, <code>~</code> (not and/or/not).'),
        ('Inspect', '<code>mask.sum()</code> before acting.'),
        ('Select or assign', '<code>a[mask]</code> to read (copy), <code>a[mask] = v</code> to update in place.'),
        ('Per row/column', '<code>mask.any(axis=1)</code>, <code>mask.all(axis=0)</code>.'),
        title='Steps to Filter with Masks'),
    crossq(
        ('Why does marks[mask] return 1-D even for a 2-D array?', 'Selected elements no longer form a rectangle, so NumPy returns them flattened in row-major order.'),
        ('How do you keep the shape and blank out non-matching values?', '<code>np.where(mask, marks, 0)</code> or a masked array (<code>np.ma.masked_where</code>).'),
        ('Is a mask selection a view?', 'No, boolean indexing always returns a copy; but assignment through a mask writes into the original.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What is fancy indexing? How is it different from slicing?', 'Fancy Indexing', minutes=7, cards=[
    definition(
        defbox('<strong>Fancy (integer-array) indexing</strong> selects elements using arrays or lists of positions: <code>a[[2, 0, 5]]</code>. Positions can '
               'repeat and be in any order. With several index arrays, they are <strong>paired element-wise</strong>: <code>m[[0, 2], [2, 0]]</code> → '
               'elements (0,2) and (2,0). <code>np.ix_</code> builds a cross product to select a sub-matrix.',
               'Unlike slicing, fancy indexing always returns a <strong>copy</strong>, and the result shape follows the shape of the index arrays.'),
        tags('fancy indexing', 'np.ix_', 'argsort', 'take', 'copy'),
    ),
    analogy('Slicing is "seats 3 to 7". Fancy indexing is a <strong>guest list</strong>: "seat 12, then seat 3, then seat 12 again", in exactly that order.'),
    fancy_anim(),
    real_world(
        scenario('Reordering and lookups',
                 p('Sort students by total: <code>order = np.argsort(-totals); marks[order]</code>. Map subject codes to names: <code>names[codes]</code>. '
                   'Pick each student\'s best subject: <code>marks[np.arange(n), marks.argmax(axis=1)]</code>.')),
    ),
    example(
        nprun("""
            a = np.array([82, 61, 91, 55, 88, 47])
            print(a[[2, 0, 5]], a[[1, 1, 1]])

            print(marks[[0, 2], [2, 0]])                 # paired: (0,2), (2,0)
            print(marks[np.ix_([0, 2], [0, 2])])         # 2x2 sub-matrix

            totals = marks.sum(axis=1)
            order = np.argsort(-totals)                  # descending
            print(totals, order, marks[order][:, 0])

            best = marks.argmax(axis=1)
            print('best subject per student:', best, marks[np.arange(len(marks)), best])

            subjects = np.array(['SQL', 'Spark', 'ML', 'Python'])
            print(subjects[best])
        """, setup=MARKS),
        title='Example: Pick, Pair, Sub-matrix, Reorder, Best per Row'),
    steps(
        ('Get positions', 'From <code>argsort</code>, <code>argmax</code>, <code>np.where(cond)</code> or your own list.'),
        ('Index', '<code>a[positions]</code>; for rows and columns together use <code>np.ix_</code>.'),
        ('Per-row picks', '<code>a[np.arange(n_rows), col_positions]</code>.'),
        ('Remember it copies', 'Modifying the result does not change the original (but <code>a[idx] = v</code> does).'),
        title='Steps for Fancy Indexing'),
    crossq(
        ('What happens with a[[0, 0]] = [1, 2]?', 'Both assignments go to position 0; the last wins (value 2). For accumulation use <code>np.add.at</code>.'),
        ('Fancy indexing vs np.take?', 'np.take(a, idx, axis=...) does the same along one axis and can be faster; it also supports mode="wrap"/"clip".'),
        ('Can you mix slices and index arrays?', 'Yes: <code>marks[1:, [0, 3]]</code> → rows 1 onward, columns 0 and 3.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('What is the difference between a view and a copy in NumPy?', 'Views vs Copies', minutes=7, cards=[
    definition(
        defbox('A <strong>view</strong> is a new array object that looks at the <strong>same memory</strong> as the original (with its own shape/strides). '
               'Changing a view changes the original. Basic slicing, <code>reshape</code> (usually), <code>.T</code>, <code>ravel</code> (when possible) and '
               '<code>view()</code> create views.',
               'A <strong>copy</strong> owns new memory. Fancy/boolean indexing, <code>flatten</code>, <code>astype</code>, arithmetic results and '
               '<code>.copy()</code> create copies. Check with <code>np.shares_memory(a, b)</code> or <code>b.base is a</code>.'),
        tags('view', 'copy', 'shares_memory', 'base', 'memory'),
    ),
    analogy('A view is a <strong>second door into the same room</strong>: move the furniture through either door and the room changes. A copy is a '
            '<strong>photograph</strong> of the room: draw on the photo and the room stays as it was.'),
    view_copy_anim(),
    real_world(
        scenario('Bug: the original data changed',
                 p('A function normalised <code>x = data[:, 0]</code> in place (<code>x -= x.mean()</code>) and silently modified the caller\'s dataset. '
                   'Taking <code>.copy()</code> inside the function, or writing <code>x = x - x.mean()</code> (new array), fixed it. Conversely, views avoid '
                   'copying gigabytes when you only read a slice.')),
    ),
    example(
        nprun("""
            a = np.array([10, 20, 30, 40, 50])
            v = a[1:4]
            v[0] = 99
            print(a, '| shares memory:', np.shares_memory(a, v), '| v.base is a:', v.base is a)

            c = a[1:4].copy()
            c[0] = -1
            print(a, '| shares memory:', np.shares_memory(a, c))

            f = a[[1, 2, 3]]                 # fancy -> copy
            f[0] = -5
            print(a, np.shares_memory(a, f))

            col = np.arange(6).reshape(2, 3)[:, 0]
            print(col.flags['C_CONTIGUOUS'], col.strides)  # views can be non-contiguous
        """),
        title='Example: Detecting Views and Copies'),
    steps(
        ('Know which operations view', 'Basic slices, reshape, transpose, ravel.'),
        ('Copy before modifying borrowed data', '<code>x = data[:, 0].copy()</code>.'),
        ('Prefer new arrays in functions', '<code>x = x - mean</code> instead of <code>x -= mean</code> on inputs.'),
        ('Verify when unsure', '<code>np.shares_memory(a, b)</code>.'),
        ('Free big originals', 'A small view keeps the whole parent alive; copy the slice if the parent is huge and no longer needed.'),
        title='Steps to Avoid View/Copy Surprises'),
    crossq(
        ('How is this different from pandas?', 'pandas 3 uses Copy-on-Write, so modifying a subset never changes the parent. Plain NumPy views do write through.'),
        ('Can a view keep memory alive?', 'Yes, the view references the parent buffer (via .base), so a tiny slice of a 2 GB array keeps all 2 GB in memory.'),
        ('Is a[:] a copy?', 'No, it is a view of the whole array. Use a.copy() (or np.array(a)) for a copy.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('How do np.where, np.select, np.clip and np.nonzero work?', 'where, select, clip', minutes=6, cards=[
    definition(
        defbox('<code>np.where(cond, x, y)</code>: element-wise choice: x where cond is True, otherwise y (broadcasting allowed). With only '
               '<code>cond</code>, it returns the <strong>indices</strong> of True elements, same as <code>np.nonzero</code>.',
               '<code>np.select(condlist, choicelist, default)</code>: several conditions checked in order; the first True one decides.',
               '<code>np.clip(a, lo, hi)</code>: limit values to a range. <code>np.argwhere(cond)</code>: indices as an (n, ndim) array.'),
        tags('np.where', 'np.select', 'np.clip', 'np.nonzero', 'argwhere'),
    ),
    analogy('np.where is a <strong>traffic signal</strong> at every element: green → take x, red → take y. np.select is a <strong>sorting conveyor</strong> with '
            'several gates; each item drops through the first gate it matches.'),
    where_anim(),
    real_world(
        scenario('Grades and caps',
                 p('Grades from marks with np.select; PASS/FAIL with np.where; cap bonus-adjusted marks at 100 with np.clip; list the (student, subject) '
                   'positions below 60 with np.argwhere for the re-exam notice.')),
    ),
    example(
        nprun("""
            m = marks.ravel()
            print(np.where(m >= 60, 'P', 'F'))
            print(np.select([m >= 85, m >= 70, m >= 60], ['A', 'B', 'C'], default='F'))
            print(np.clip(m + 8, 0, 100))
            print(np.where(m < 60))                   # indices (tuple of arrays)
            print(np.argwhere(marks < 70))            # (row, col) pairs
            print(np.where(marks >= 90, marks, 0))    # keep shape, zero the rest
        """, setup=MARKS),
        title='Example: Conditional Values and Positions'),
    steps(
        ('Two outcomes', '<code>np.where(cond, a, b)</code>.'),
        ('Several outcomes', '<code>np.select</code>, conditions from most to least specific.'),
        ('Ranges', '<code>np.clip</code>, or <code>np.digitize</code>/<code>np.searchsorted</code> for bins.'),
        ('Positions', '<code>np.nonzero</code>/<code>np.where(cond)</code> (tuple), <code>np.argwhere</code> (rows of coordinates).'),
        title='Steps for Conditional Logic'),
    crossq(
        ('Does np.where evaluate both x and y fully?', 'Yes: both arrays are computed for all elements before choosing, so np.where(x != 0, 1/x, 0) still warns about division by zero; use np.divide(1, x, where=x!=0, out=...) to avoid it.'),
        ('np.where vs boolean indexing?', 'np.where keeps the array shape (replacing values); boolean indexing returns only the selected elements.'),
        ('What does np.digitize do?', 'Returns the bin index of each value for given bin edges, useful for grade bands.'),
    ),
]),
])
