from build import *
from numpyq.anims import *
from numpyq.runner import nprun, pyshow

SECTION = dict(level='advanced', title='Performance & Numerics', questions=[

# ------------------------------------------------------------------ 26
Q('Why exactly is NumPy fast? Where does the speed-up come from?', 'Why NumPy is Fast', minutes=8, cards=[
    definition(
        defbox('Four reasons: (1) <strong>no per-element interpreter overhead</strong>: type checks and dispatch happen once per operation, then a compiled loop runs; '
               '(2) <strong>homogeneous, contiguous memory</strong>: raw values, good CPU-cache use and prefetching; (3) <strong>SIMD</strong> instructions '
               'process several values per instruction; (4) <strong>optimised libraries</strong>: linear algebra calls BLAS/LAPACK (OpenBLAS, MKL), often '
               'multi-threaded.',
               'Limits: each operation still makes one pass and usually one temporary array; small arrays are dominated by call overhead; Python-level loops over '
               'arrays (or object dtype) lose all the benefits.'),
        tags('performance', 'SIMD', 'BLAS', 'cache', 'overhead'),
    ),
    analogy('Paying 10,000 cheques at a bank: one clerk verifying each cheque\'s signature, account and amount one by one (Python), versus a <strong>bulk '
            'transfer file</strong> checked once and processed by the bank\'s system in a single batch (NumPy).'),
    speed_anim(),
    real_world(
        scenario('Where it shows',
                 p('Computing z-scores for 10 million readings: a list loop takes seconds, NumPy tens of milliseconds. A 2000 × 2000 matrix product runs in a fraction '
                   'of a second through BLAS. But a loop that calls NumPy on single elements is even slower than plain Python, because of call overhead.')),
    ),
    example(
        nprun("""
            import time
            def bench(fn, n=3):
                t = time.perf_counter()
                for _ in range(n): fn()
                return (time.perf_counter() - t) / n

            x = np.random.default_rng(0).random(2_000_000)
            lst = x.tolist()
            t_list = bench(lambda: [v * 2 + 1 for v in lst])
            t_np   = bench(lambda: x * 2 + 1)
            t_bad  = bench(lambda: [x[i] * 2 + 1 for i in range(200_000)]) * 10   # scaled to 2M
            print(f'list comprehension      : {t_list:.3f} s')
            print(f'numpy vectorised        : {t_np:.4f} s')
            print(f'loop over numpy elements: {t_bad:.3f} s  (worse than the list!)')

            a = np.random.default_rng(1).random((1000, 1000))
            print(f'1000x1000 matrix product: {bench(lambda: a @ a):.3f} s')
            small = np.arange(3)
            print(f'tiny array op           : {bench(lambda: small + 1, 1000) * 1e6:.2f} µs (overhead dominates)')
        """),
        title='Example: Where Time Goes'),
    steps(
        ('Profile first', '<code>%timeit</code>, <code>time.perf_counter</code>, line_profiler.'),
        ('Remove Python loops over elements', 'Express the logic as array operations.'),
        ('Use the right tool for linear algebra', '@, linalg, einsum.'),
        ('Watch temporaries', 'Combine steps, use out=/in-place for big arrays.'),
        ('Still too slow?', 'Numba, numexpr, or a GPU array library (CuPy) with the same API.'),
        title='Steps to Make NumPy Code Fast'),
    crossq(
        ('Why is indexing single elements in a loop slow?', 'Each a[i] creates a NumPy scalar object and goes through the indexing machinery, more overhead than a Python list access.'),
        ('Is NumPy multi-threaded?', 'Element-wise ufuncs run on one core; BLAS-backed operations (matmul, linalg) are often multi-threaded.'),
        ('What does numexpr add?', 'It evaluates whole expressions like 2*x+1 in chunks without temporaries and with threads.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('How do you reduce memory use with NumPy (dtypes, in-place operations, out=)?', 'Memory: dtypes & In-place', minutes=7, cards=[
    definition(
        defbox('Memory = number of elements × itemsize, plus temporaries. Reduce it by: choosing <strong>smaller dtypes</strong> (float32, int32, uint8, bool), '
               'using <strong>views</strong> instead of copies, <strong>in-place operators</strong> (<code>+=</code>, <code>*=</code>) and <strong><code>out=</code></strong> '
               'to avoid temporaries, deleting large intermediates (<code>del</code>), and memory-mapping data that does not fit in RAM.',
               'In-place operations must keep the dtype (an int array cannot hold float results in place) and they change the original data and its views.'),
        tags('memory', 'dtype', 'in-place', 'out=', 'temporary arrays'),
    ),
    analogy('Cooking in one pot versus using a new pot for every step: the result is the same, but with new pots you need a much bigger kitchen (RAM) at the '
            'busiest moment.'),
    inplace_anim(),
    real_world(
        scenario('Image batches',
                 p('10,000 RGB images of 224 × 224 as float64 need 12 GB; as uint8 1.5 GB, converted batch by batch to float32 for the model. Normalising with '
                   '<code>batch /= 255.0</code> on a float32 batch avoids a second copy.')),
    ),
    example(
        nprun("""
            n = 10_000_000
            a64 = np.ones(n);                 a32 = np.ones(n, dtype=np.float32)
            print(a64.nbytes // 2**20, 'MiB vs', a32.nbytes // 2**20, 'MiB')
            print(np.ones(n, dtype=bool).nbytes // 2**20, 'MiB as bool,', np.ones(n, dtype=np.uint8).nbytes // 2**20, 'MiB as uint8')

            x = np.arange(5, dtype=np.float64)
            y = np.empty_like(x)
            np.multiply(x, 2, out=y); np.add(y, 1, out=y)       # one buffer
            print(y)
            x *= 2                                               # x itself changed
            print(x)
            i = np.arange(5)
            try:
                i *= 0.5
            except Exception as e:
                print(type(e).__name__ + ':', str(e).split(' with casting')[0])
            i //= 2
            print(i)
        """),
        title='Example: dtype Sizes, out=, In-place and Its Casting Rule'),
    steps(
        ('Estimate', 'elements × itemsize; multiply by temporaries in your expression.'),
        ('Pick dtypes', 'float32 for ML features, uint8 for images, bool for flags.'),
        ('Avoid temporaries', 'In-place operators or out= for big arrays.'),
        ('Release memory', '<code>del big</code> when no longer needed (and no views reference it).'),
        ('Too big for RAM', 'Process in chunks or memory-map.'),
        title='Steps to Fit Data in Memory'),
    crossq(
        ('Is a += b always the same as a = a + b?', 'No: += modifies the existing array in place (views see the change, dtype is kept); a = a + b creates a new array and rebinds the name.'),
        ('Why can\'t int arrays do *= 0.5 in place?', 'The result is float; in-place operations use "same_kind" casting and refuse to store floats into ints.'),
        ('Does float32 make computations faster too?', 'Often: half the memory traffic and twice as many values per SIMD instruction, at the cost of precision.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('When can broadcasting cause memory problems? What is np.einsum?', 'Broadcasting Pitfalls & einsum', minutes=8, cards=[
    definition(
        defbox('Broadcasting itself does not copy, but the <strong>result</strong> has the full broadcast shape. Expressions like <code>X[:, None, :] - X[None, :, :]</code> '
               'create an (n, n, d) array, which grows quadratically: easy to exhaust memory.',
               '<code>np.einsum(subscripts, *arrays)</code> describes products and sums with index notation (Einstein summation), e.g. <code>"ij,jk->ik"</code> '
               '(matmul), <code>"ij,ij->i"</code> (row-wise dot), <code>"ii->"</code> (trace), <code>"bij,bjk->bik"</code> (batch matmul). It avoids building '
               'large intermediates; <code>optimize=True</code> chooses a good contraction order.'),
        tags('broadcasting', 'einsum', 'memory', 'pairwise distance'),
    ),
    analogy('To find the distance between every pair of 20,000 cities, you do not need to <strong>write out every coordinate difference</strong> on a sheet; '
            'a clever formula from each city\'s own numbers and one multiplication table (X @ X.T) gives the same distances on a much smaller sheet.'),
    einsum_anim(),
    real_world(
        scenario('Student similarity matrix',
                 p('Finding similar students from 50 performance features: naive broadcasting for 20,000 students would need ~160 GB. Using '
                   '‖a−b‖² = ‖a‖² + ‖b‖² − 2a·b with one matrix product needs only the 20,000 × 20,000 result, or process in row blocks.')),
    ),
    example(
        nprun("""
            rng = np.random.default_rng(0)
            X = rng.random((500, 50))

            diff = X[:, None, :] - X[None, :, :]                    # (500, 500, 50)
            d_naive = np.sqrt((diff ** 2).sum(axis=-1))
            print('intermediate:', diff.shape, round(diff.nbytes / 2**20), 'MiB')

            sq = np.einsum('ij,ij->i', X, X)                        # row-wise squared norms
            d_fast = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * X @ X.T, 0))
            print('result only :', d_fast.shape, round(d_fast.nbytes / 2**20, 1), 'MiB')
            print('max difference:', np.abs(d_naive - d_fast).max())    # sqrt amplifies rounding near 0
            print('same result :', np.allclose(d_naive, d_fast, atol=1e-6))

            A = rng.random((3, 4)); B = rng.random((4, 2))
            print(np.allclose(np.einsum('ij,jk->ik', A, B), A @ B), np.einsum('ii->', np.eye(3)))
            print('naive for n=20,000, d=50:', 20_000 * 20_000 * 50 * 8 / 1e9, 'GB')
        """),
        title='Example: Pairwise Distances Two Ways'),
    steps(
        ('Estimate the broadcast result size', 'Product of the result shape × itemsize.'),
        ('Look for an algebraic shortcut', 'Expand squares, use matrix products.'),
        ('Use einsum for sum-of-products', 'Row-wise dots, traces, batch products.'),
        ('Block the computation', 'Process rows in chunks if even the result is too large.'),
        ('Use libraries', 'scipy.spatial.distance.cdist / sklearn pairwise_distances.'),
        title='Steps to Avoid Broadcast Blow-ups'),
    crossq(
        ('Why np.maximum(..., 0) and atol=1e-6?', 'Rounding can make tiny squared distances slightly negative (sqrt → NaN), and the square root magnifies tiny errors near zero, so diagonal values come out around 1e-7 instead of 0.'),
        ('Is einsum always faster than @?', 'No: @ uses BLAS and is usually fastest for plain matrix products; einsum shines for unusual contractions and avoiding temporaries.'),
        ('What does "...->" mean in einsum?', 'Ellipsis stands for remaining (batch) dimensions, e.g. "...ij,...jk->...ik".'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('How do you save and load arrays? What is memory mapping (memmap)?', 'Saving, Loading & memmap', minutes=7, cards=[
    definition(
        defbox('<code>np.save("a.npy", a)</code> / <code>np.load</code>: binary .npy with dtype and shape, fast and exact. <code>np.savez</code> / '
               '<code>savez_compressed</code>: several named arrays in one .npz. <code>np.savetxt</code>/<code>loadtxt</code>/<code>genfromtxt</code>: text/CSV '
               '(readable, slower; genfromtxt handles missing values).',
               '<strong>Memory mapping</strong> (<code>np.load(f, mmap_mode="r")</code> or <code>np.memmap</code>) maps a file into memory: the array object '
               'behaves normally, but data is read from disk only when accessed, so arrays larger than RAM can be processed.'),
        tags('np.save', 'np.load', 'npz', 'savetxt', 'memmap'),
    ),
    analogy('np.save is <strong>vacuum-packing</strong> the array exactly as it is. A memory map is a <strong>library reading room</strong>: the whole collection '
            'is "available", but only the books you open are brought to your desk.'),
    io_anim(),
    real_world(
        scenario('Exam analytics cache',
                 p('Features computed from 3 years of answer logs are saved as .npy so notebooks load them in milliseconds instead of re-parsing CSVs; a 30 GB '
                   'embeddings matrix is opened with mmap_mode="r" and processed in row blocks on a 16 GB laptop.')),
    ),
    example(
        nprun("""
            import os
            marks = np.array([[82, 61, 70], [91, 88, 79]])
            np.save('marks.npy', marks)
            np.savez_compressed('batch.npz', marks=marks, rolls=np.array([2401, 2402]))
            np.savetxt('marks.csv', marks, delimiter=',', fmt='%d', header='sql,spark,ml', comments='')

            print(np.load('marks.npy'))
            with np.load('batch.npz') as z:
                print(z.files, z['rolls'])
            print(open('marks.csv').read().strip())
            print(np.loadtxt('marks.csv', delimiter=',', skiprows=1, dtype=int).sum())

            big = np.lib.format.open_memmap('big.npy', mode='w+', dtype=np.float32, shape=(1_000_000, 10))
            big[:] = 1.0; big.flush(); del big
            m = np.load('big.npy', mmap_mode='r')
            print(type(m).__name__, m.shape, m[500_000:500_002, :3])
            print(os.path.getsize('big.npy') // 2**20, 'MiB on disk')
        """),
        title='Example: .npy, .npz, CSV and a Memory-mapped Array'),
    steps(
        ('Intermediate results', '.npy / .npz.'),
        ('Exchange with people or other tools', 'CSV via savetxt (or pandas), Parquet via pandas/pyarrow.'),
        ('Larger than RAM', 'Create with open_memmap / memmap, read with mmap_mode.'),
        ('Process in blocks', 'Loop over row ranges of the memmap.'),
        ('Security', 'Keep allow_pickle=False for files you did not create.'),
        title='Steps for Array Storage'),
    crossq(
        ('.npy vs pickle?', '.npy is a simple documented format, portable and safe to load; pickle can execute code on load and is Python-specific.'),
        ('loadtxt vs genfromtxt?', 'genfromtxt handles missing values and mixed types (slower); loadtxt is faster for clean numeric data.'),
        ('Does memmap make computation faster?', 'No, it reduces memory; disk access is slower than RAM, so sequential block access works best.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What floating-point and numeric pitfalls should you know in NumPy?', 'Numerical Pitfalls', minutes=8, cards=[
    definition(
        defbox('Floats are <strong>binary approximations</strong>: 0.1 + 0.2 ≠ 0.3 exactly, so compare with <code>np.isclose</code>/<code>np.allclose</code> '
               '(relative and absolute tolerances). float32 has ~7 significant digits, float64 ~15–16. Large + small numbers lose the small one; subtracting '
               'nearly equal numbers loses precision (cancellation). Summation order changes results slightly (NumPy uses pairwise summation).',
               'Integers <strong>overflow and wrap</strong> silently in arrays; <code>//</code> and <code>%</code> floor toward −∞ for negatives; '
               '<code>NaN</code> propagates and never equals itself. For money use integer paise or Python\'s Decimal.'),
        tags('floating point', 'isclose', 'allclose', 'precision', 'overflow'),
    ),
    analogy('Measuring with a <strong>ruler marked in millimetres</strong>: you cannot measure exactly one-third of a centimetre, and if you add a hair\'s width '
            'to the length of a building, the ruler will not notice. Floats are such rulers, in binary.'),
    precision_anim(),
    real_world(
        scenario('Fee totals that did not match',
                 p('Summing fee instalments as floats gave ₹1,23,456.00000001 and an equality check against the bank total failed. Storing amounts in paise as '
                   'int64 made totals exact; for computed averages, comparisons use np.isclose.')),
    ),
    example(
        nprun("""
            print(0.1 + 0.2 == 0.3, np.isclose(0.1 + 0.2, 0.3))
            print(np.float32(16_777_216) + np.float32(1) == np.float32(16_777_216))
            print(np.finfo(np.float64).eps, np.finfo(np.float32).eps)

            x = np.full(10_000_000, 0.1)
            total = 0.0
            for v in x.tolist():                                  # naive left-to-right loop
                total += v
            print(repr(x.sum()), repr(total))                     # pairwise vs naive

            print(np.array([-7, 7]) // 2, np.array([-7, 7]) % 2)
            print(np.array([2**62], dtype=np.int64) * 4)         # silent wrap
            fees = np.array([45000.10, 45000.20, 33456.30])
            print(fees.sum(), (np.round(fees * 100).astype(np.int64)).sum() / 100)
            print(np.allclose([1.0, 2.0], [1.0 + 1e-10, 2.0]))
        """),
        title='Example: Equality, Precision, Summation, Integer Rules'),
    steps(
        ('Never compare floats with ==', 'Use isclose/allclose with tolerances suited to your data.'),
        ('Pick precision consciously', 'float64 for finance/science, float32 for ML features.'),
        ('Check ranges for integer types', 'np.iinfo; upcast before large products.'),
        ('Money', 'Integers in the smallest unit, or Decimal outside NumPy.'),
        ('Test numerics', 'np.testing.assert_allclose in unit tests.'),
        title='Steps to Stay Numerically Safe'),
    crossq(
        ('What do rtol and atol mean in isclose?', '|a − b| ≤ atol + rtol × |b|; defaults rtol=1e-05, atol=1e-08. Near zero, atol matters most.'),
        ('Why do x.sum() and a += loop differ?', 'Different addition order: NumPy\'s pairwise summation accumulates far less rounding error than adding left to right. (Python 3.12+\'s built-in sum() is also compensated; math.fsum is exact.)'),
        ('How do you make NumPy raise on overflow?', 'np.errstate(over="raise") catches float overflow; integer array overflow is not detected, so check ranges or use larger types.'),
    ),
]),
])
