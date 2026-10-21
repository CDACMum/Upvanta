from build import *


def _lines(x, y, lines, color='#e2e8f0', size=11, step=None, gap=16):
    return ''.join(stext(x, y + i * gap, ln, color, size, 'start', step=step).replace('<text ', '<text xml:space="preserve" ', 1)
                   for i, ln in enumerate(lines))


def _codebox(x, y, w, h, lines, color='gray', step=None, tcolor='#e2e8f0', size=11, focus=None):
    return sbox(x, y, w, h, '', '', color, step=step, fill_opacity=0.08, focus=focus) + _lines(x + 14, y + 22, lines, tcolor, size, step=step)


def _row(items, y, x0=20, w=130, gap=14, h=56, size=12, arrows=True):
    out = []
    for i, (t, s, c, st) in enumerate(items):
        x = x0 + i * (w + gap)
        out.append(sbox(x, y, w, h, t, s, c, step=st, size=size))
        if arrows and i:
            out.append(sarrow(x - gap, y + h / 2, x - 2, y + h / 2, 'gray', step=st))
    return ''.join(out)


def _dot(x, y, color, step=None, r=5, focus=None):
    c = PALETTE.get(color, color)
    a = f' data-step="{step}"' if step else ''
    f = f' data-focus="{focus}"' if focus else ''
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"{a}{f}/>'


def _axes(x, y, w, h, xl='', yl='', step=None):
    return (sarrow(x, y + h, x + w, y + h, 'gray', step=step) + sarrow(x, y + h, x, y, 'gray', step=step)
            + stext(x + w / 2, y + h + 18, xl, 'gray', 11, step=step) + stext(x - 12, y - 6, yl, 'gray', 11, anchor='start', step=step))


def _path(fn, x0, x1, X, Y, W, H, ymax, n=80):
    """Polyline of fn over [x0, x1] mapped into the box (X, Y, W, H); ymax maps to the top."""
    pts = []
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        pts.append(f'{X + W * k / n:.1f} {Y + H - H * min(fn(x), ymax) / ymax:.1f}')
    return 'M ' + ' L '.join(pts)


def _curve(fn, x0, x1, X, Y, W, H, ymax, color='blue', step=None, width=2.5, fill=False):
    d = _path(fn, x0, x1, X, Y, W, H, ymax)
    c = PALETTE.get(color, color)
    a = f' data-step="{step}"' if step else ''
    if fill:
        return f'<path d="{d} L {X + W} {Y + H} L {X} {Y + H} Z" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="{width}"{a}/>'
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{width}"{a}/>'


def _area(fn, x0, x1, a0, a1, X, Y, W, H, ymax, color='amber', step=None, n=60):
    """Shaded area under fn between a0 and a1 (data units)."""
    sx = lambda x: X + W * (x - x0) / (x1 - x0)
    pts = [f'{sx(a0):.1f} {Y + H}']
    for k in range(n + 1):
        x = a0 + (a1 - a0) * k / n
        pts.append(f'{sx(x):.1f} {Y + H - H * min(fn(x), ymax) / ymax:.1f}')
    pts.append(f'{sx(a1):.1f} {Y + H}')
    c = PALETTE.get(color, color)
    st = f' data-step="{step}"' if step else ''
    return f'<path d="M {" L ".join(pts)} Z" fill="{c}" fill-opacity="0.45" stroke="none"{st}/>'


def _bars(vals, X, Y, W, H, vmax, color='blue', step=None, gap=3, labels=None, lsize=10):
    out = []
    bw = W / len(vals)
    c = PALETTE.get(color, color)
    a = f' data-step="{step}"' if step else ''
    for i, v in enumerate(vals):
        h = H * v / vmax
        out.append(f'<rect x="{X + i * bw + gap / 2:.1f}" y="{Y + H - h:.1f}" width="{bw - gap:.1f}" height="{h:.1f}" fill="{c}"{a}/>')
        if labels:
            out.append(stext(X + i * bw + bw / 2, Y + H + 14, labels[i], 'gray', lsize, step=step))
    return ''.join(out)


def _npdf(m=0, s=1):
    import math
    return lambda x: math.exp(-((x - m) / s) ** 2 / 2) / (s * math.sqrt(2 * math.pi))



# ============================================================ section 1
def types_anim():
    elems = [
        stext(380, 24, 'Types of data and levels of measurement', 'blue', 15, bold=True),
        sbox(300, 44, 160, 40, 'Data', '', 'gray', step=1, size=13),
        sarrow(340, 84, 200, 108, 'gray', step=1), sarrow(420, 84, 560, 108, 'gray', step=1),
        sbox(100, 110, 200, 46, 'Qualitative (categorical)', 'labels', 'purple', step=1, size=12),
        sbox(460, 110, 200, 46, 'Quantitative (numerical)', 'counts & measurements', 'blue', step=1, size=12),
        sbox(40, 180, 150, 50, 'nominal', 'centre, course', 'purple', step=2, size=12),
        sbox(210, 180, 150, 50, 'ordinal', 'grade A–D, rating 1–5', 'purple', step=2, size=12),
        sarrow(160, 156, 115, 178, 'gray', step=2), sarrow(240, 156, 285, 178, 'gray', step=2),
        sbox(400, 180, 150, 50, 'discrete', 'backlogs: 0, 1, 2', 'blue', step=3, size=12),
        sbox(570, 180, 150, 50, 'continuous', 'attendance, package', 'blue', step=3, size=12),
        sarrow(520, 156, 475, 178, 'gray', step=3), sarrow(600, 156, 645, 178, 'gray', step=3),
        stable(40, 262, ['level', 'example', 'meaningful', 'summary'], [['nominal', 'centre', '= ≠', 'mode, counts'], ['ordinal', 'grade', '= ≠ < >', 'median, percentiles'],
                                                                      ['interval', '°C, year', '+ −', 'mean, SD'], ['ratio', 'package, hours', '× ÷ (true zero)', 'all, incl. CV']],
               [110, 150, 160, 180], step=4, title='each level adds operations', title_color='amber'),
        stext(380, 418, 'storage type ≠ statistical type: a roll number stored as int is still nominal', 'red', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 432, *elems), [
        'Data is either qualitative (labels) or quantitative (numbers that measure or count).',
        'Qualitative data is nominal (no order) or ordinal (ordered categories with unequal gaps).',
        'Quantitative data is discrete (countable) or continuous (any value in a range).',
        'Each level of measurement allows more operations and therefore more summary statistics.',
        'Decide the level from meaning, not from the column\'s dtype.',
    ])


def central_anim():
    import math
    ln = lambda x: (math.exp(-(math.log(x) - math.log(6)) ** 2 / (2 * 0.35 ** 2)) / (x * 0.35 * math.sqrt(2 * math.pi))) if x > 0 else 0
    X, Y, W, H = 40, 50, 420, 200
    sx = lambda v: X + W * v / 16
    elems = [stext(380, 24, 'Mean, median and mode in skewed data (placement packages)', 'blue', 15, bold=True),
             _axes(X, Y, W, H, '', '', step=1), stext(X + W / 2, Y + H + 32, 'package (LPA)', 'gray', 11, step=1), _curve(ln, 0.01, 16, X, Y, W, H, 0.2, 'blue', step=1, fill=True)]
    for v in [2, 4, 6, 8, 10, 12, 14]:
        elems.append(stext(sx(v), Y + H + 14, str(v), 'gray', 10, step=1))
    for v, lab, col, st, dy in [(5.3, 'mode ≈ peak', 'green', 2, 0), (6.0, 'median 6.00', 'amber', 2, 16), (6.57, 'mean 6.57', 'red', 2, 32)]:
        elems.append(f'<line x1="{sx(v):.1f}" y1="{Y + 20}" x2="{sx(v):.1f}" y2="{Y + H}" stroke="{PALETTE[col]}" stroke-width="2.5" data-step="{st}"/>')
        elems.append(stext(sx(9), Y + 40 + dy * 1.2, lab, col, 12, anchor='start', step=st, bold=True))
    elems += [
        stext(250, 300, 'right skew: long tail of high packages pulls the mean above the median', 'amber', 12, step=2),
        stable(490, 60, ['measure', '212 placed', '+ one 60 LPA'], [['mean', '6.57', '6.82'], ['median', '6.00', '6.00'], ['10 % trimmed', '—', '6.26']],
               [100, 75, 85], step=3, title='real run', title_color='red', focus_rows={0: '3'}),
        stext(615, 190, 'one offer moves the mean;', 'red', 12, step=3), stext(615, 208, 'the median does not move', 'amber', 12, step=3),
        stext(615, 250, 'mode: most frequent value', 'green', 12, step=4), stext(615, 268, '(Kharghar is the modal centre)', 'green', 11, step=4),
        stext(380, 324, 'combining groups: weighted mean Σ(nᵢ·meanᵢ)/Σnᵢ = 58.723, not the plain mean of centre means 58.710', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 338, *elems), [
        'Placement packages are right-skewed: most offers are 4–8 LPA, a few are much higher.',
        'The mode sits at the peak, the median splits the area in half, and the mean is pulled furthest into the tail.',
        'Adding a single 60 LPA offer lifts the mean by a quarter of a lakh; the median is unchanged. The trimmed mean drops the extremes first.',
        'The mode is the only centre measure that works for categories.',
        'To combine group averages, weight each by its group size.',
    ])


def spread_anim():
    elems = [stext(380, 24, 'Spread: same average, very different batches', 'blue', 15, bold=True),
             stext(90, 62, 'batch A', 'gray', 12, step=1), stext(90, 102, 'batch B', 'gray', 12, step=1),
             f'<line x1="130" y1="60" x2="730" y2="60" stroke="#334155" data-step="1"/><line x1="130" y1="100" x2="730" y2="100" stroke="#334155" data-step="1"/>']
    sx = lambda v: 130 + v * 6
    for v in [55, 57, 58, 60, 60, 61, 62, 63, 64]:
        elems.append(_dot(sx(v), 60, 'blue', step=1, r=6))
    for v in [30, 32, 35, 40, 60, 80, 85, 88, 90]:
        elems.append(_dot(sx(v), 100, 'amber', step=1, r=6))
    elems.append(f'<line x1="{sx(60)}" y1="45" x2="{sx(60)}" y2="115" stroke="#ef4444" stroke-dasharray="4,3" data-step="1"/>')
    elems.append(stext(sx(60), 130, 'both means = 60', 'red', 11, step=1))
    xs = [55, 60, 62, 65, 58]
    for i, v in enumerate(xs):
        x = 60 + i * 70
        d = v - 60
        elems.append(scell(x, 160, 60, 28, str(v), '#1e293b', step=2))
        elems.append(scell(x, 190, 60, 28, f'{d:+d}', '#334155', step=2))
        elems.append(scell(x, 220, 60, 28, str(d * d), '#065f46', step=3, bold=True))
    elems += [stext(30, 179, 'x', 'gray', 11, step=2), stext(30, 209, 'x − x̄', 'gray', 11, step=2), stext(30, 239, '(x−x̄)²', 'gray', 11, step=3),
              stext(380, 292, 'Σ = 58 → ÷ n = 11.6 (ddof=0) · ÷ (n−1) = 14.5 (ddof=1) · SD = √14.5 = 3.81', 'green', 12, step=3, bold=True),
              stable(440, 165, ['column', 'SD', 'IQR', 'CV'], [['attendance', '12.94', '22.47', '0.17'], ['study_hours', '4.33', '5.80', '0.50'], ['final_score', '10.40', '15.23', '0.18']],
                     [100, 60, 60, 50], step=4, title='real run (600 students)', title_color='purple', focus_rows={1: '4'}),
              stext(380, 314, 'CV = SD / mean: study hours vary most relative to their mean', 'purple', 12, step=4),
              stext(380, 336, 'mean ↔ SD · median ↔ IQR (robust) · pandas std uses n−1, NumPy std uses n unless ddof=1', 'cyan', 12, step=5)]
    return anim(canvas(760, 350, *elems), [
        'Two batches with the same mean of 60 can have completely different spreads.',
        'Spread starts with deviations from the mean.',
        'Square and average them for the variance; dividing by n − 1 for a sample gives the unbiased estimate. SD brings it back to marks.',
        'IQR is robust to outliers; CV compares variability across different scales.',
        'Pair each centre measure with its spread measure and watch the ddof default.',
    ])


def boxplot_anim():
    sx = lambda v: 60 + v * 32
    q = dict(mn=2.6, q1=4.7, md=6.0, q3=7.9, hi=12.7, wmax=12.3)
    elems = [stext(380, 24, 'Box plot of placement packages (real quartiles)', 'blue', 15, bold=True),
             f'<line x1="{sx(0)}" y1="200" x2="{sx(20)}" y2="200" stroke="#64748b" data-step="1"/>']
    for v in range(0, 21, 2):
        elems.append(stext(sx(v), 218, str(v), 'gray', 10, step=1))
    elems.append(stext(sx(10), 238, 'package (LPA)', 'gray', 11, step=1))
    for v, lab in [(q['q1'], 'Q1 4.7'), (q['md'], 'median 6.0'), (q['q3'], 'Q3 7.9')]:
        elems.append(stext(sx(v), 72 if lab.startswith('median') else 88, lab, 'amber', 11, step=1))
    elems += [f'<rect x="{sx(q["q1"])}" y="100" width="{sx(q["q3"]) - sx(q["q1"])}" height="60" fill="#0ea5e9" fill-opacity="0.3" stroke="#0ea5e9" stroke-width="2" data-step="2"/>',
              f'<line x1="{sx(q["md"])}" y1="100" x2="{sx(q["md"])}" y2="160" stroke="#f59e0b" stroke-width="3" data-step="2"/>',
              stext((sx(q['q1']) + sx(q['q3'])) / 2, 178, 'IQR = 3.2', 'blue', 11, step=2),
              f'<line x1="{sx(q["hi"])}" y1="90" x2="{sx(q["hi"])}" y2="170" stroke="#ef4444" stroke-dasharray="5,4" data-step="3"/>',
              stext(sx(q['hi']), 82, 'Q3 + 1.5·IQR = 12.7', 'red', 11, step=3),
              f'<line x1="{sx(0)}" y1="90" x2="{sx(0)}" y2="170" stroke="#ef4444" stroke-dasharray="5,4" data-step="3"/>',
              stext(sx(0) + 6, 82, 'lower fence −0.1', 'red', 11, step=3, anchor='start'),
              f'<line x1="{sx(q["mn"])}" y1="130" x2="{sx(q["q1"])}" y2="130" stroke="#e2e8f0" stroke-width="2" data-step="4"/>',
              f'<line x1="{sx(q["q3"])}" y1="130" x2="{sx(q["wmax"])}" y2="130" stroke="#e2e8f0" stroke-width="2" data-step="4"/>',
              f'<line x1="{sx(q["mn"])}" y1="115" x2="{sx(q["mn"])}" y2="145" stroke="#e2e8f0" stroke-width="2" data-step="4"/>',
              f'<line x1="{sx(q["wmax"])}" y1="115" x2="{sx(q["wmax"])}" y2="145" stroke="#e2e8f0" stroke-width="2" data-step="4"/>']
    for v in [13.6, 13.9, 14.6, 16.4, 16.6, 19.8]:
        elems.append(f'<circle cx="{sx(v)}" cy="130" r="6" fill="none" stroke="#ef4444" stroke-width="2.5" data-step="4"/>')
    elems += [stext(sx(16.5), 165, '6 outliers: check, don\'t delete', 'red', 11, step=4),
              stext(380, 268, 'percentiles: 90th percentile of final score = 72.51 → 60 students in the top 10 %', 'green', 12, step=5),
              stext(380, 290, 'percentile rank: a final score of 70 beats 84.7 % of the batch', 'green', 12, step=5)]
    return anim(canvas(760, 305, *elems), [
        'Sort the data and find the quartiles: 25 % of packages are below 4.7 LPA, half below 6.0, 75 % below 7.9.',
        'The box spans Q1 to Q3 (the middle 50 %, IQR = 3.2); the line inside is the median.',
        'Tukey\'s fences sit 1.5 × IQR beyond the box.',
        'Whiskers reach the most extreme points inside the fences; points beyond are drawn individually as outliers.',
        'The same percentile machinery gives thresholds (top 10 %) and percentile ranks for individual students.',
    ])


def shape_anim():
    import math
    rs = lambda x: (x ** 2) * math.exp(-x) / 0.6 if x > 0 else 0
    ls = lambda x: rs(10 - x)
    sym = lambda x: _npdf(5, 1.4)(x) / 0.3
    elems = [stext(380, 24, 'The shape of a distribution: skewness and kurtosis', 'blue', 15, bold=True)]
    for i, (fn, title, col, order, st) in enumerate([(ls, 'left-skewed (skew < 0)', 'purple', 'mean < median < mode', 1),
                                                    (sym, 'symmetric (skew ≈ 0)', 'green', 'mean ≈ median ≈ mode', 1),
                                                    (rs, 'right-skewed (skew > 0)', 'amber', 'mode < median < mean', 2)]):
        X = 20 + i * 250
        elems += [_curve(fn, 0, 10, X, 60, 220, 110, 1.0, col, step=st, fill=True), stext(X + 110, 50, title, col, 12, step=st, bold=True),
                  stext(X + 110, 190, order, 'gray', 11, step=st)]
    elems += [stable(30, 228, ['column', 'skew', 'excess kurt.'], [['attendance', '0.08', '−1.21'], ['study_hours', '0.77', '0.55'], ['salary_lpa', '1.54', '3.71'], ['log(salary)', '0.30', '—']],
                     [110, 60, 90], step=3, title='real run', title_color='amber', focus_rows={2: '3', 3: '4'}),
              stext(340, 250, 'log transform: package skew 1.54 → 0.30', 'green', 12, step=4, anchor='start'),
              stext(340, 278, 'excess kurtosis: normal 0 · uniform −1.2 · t(5) +4.5', 'cyan', 12, step=5, anchor='start'),
              stext(340, 300, '(attendance is uniform-like → −1.21)', 'cyan', 11, step=5, anchor='start'),
              stext(340, 322, 'heavy tails = more extreme values than a normal predicts', 'red', 11, step=5, anchor='start')]
    return anim(canvas(760, 365, *elems), [
        'Symmetric data has mean ≈ median ≈ mode; a left-skewed tail pulls the mean below the median.',
        'A right-skewed tail (incomes, waiting times, study hours) pulls the mean above the median.',
        'Skewness quantifies the asymmetry: packages are strongly right-skewed.',
        'A log transform compresses large values and makes right-skewed data nearly symmetric.',
        'Excess kurtosis measures tail weight relative to the normal distribution.',
    ])


# ============================================================ section 2
def venn_anim():
    elems = [stext(380, 24, 'Probability rules on 600 students (real counts)', 'blue', 15, bold=True),
             '<rect x="20" y="45" width="420" height="250" rx="10" fill="none" stroke="#475569" stroke-width="1.5" data-step="1"/>',
             stext(30, 64, 'all students  P = 1', 'gray', 11, step=1, anchor='start'),
             '<circle cx="180" cy="170" r="95" fill="#0ea5e9" fill-opacity="0.3" stroke="#0ea5e9" stroke-width="2" data-step="1"/>',
             '<circle cx="290" cy="170" r="80" fill="#f59e0b" fill-opacity="0.3" stroke="#f59e0b" stroke-width="2" data-step="2"/>',
             stext(130, 170, 'placed', 'blue', 13, step=1, bold=True), stext(130, 188, '0.353', 'blue', 12, step=1),
             stext(330, 170, 'Pune', 'amber', 13, step=2, bold=True), stext(330, 188, '0.295', 'amber', 12, step=2),
             stext(240, 170, 'both', 'green', 12, step=2, bold=True), stext(240, 188, '0.088', 'green', 12, step=2),
             stext(230, 285, 'not placed = 1 − 0.353 = 0.647', 'gray', 11, step=1)]
    elems += [stable(460, 50, ['rule', 'value'], [['P(placed or Pune)', '0.353 + 0.295 − 0.088'], ['', '= 0.560 ✓ (count 0.560)']], [140, 160], step=3,
                     title='addition rule', title_color='green'),
              stable(460, 150, ['independent?', 'value'], [['P(placed)·P(Pune)', '0.104'], ['observed P(both)', '0.088']], [140, 160], step=4,
                     title='multiplication rule', title_color='purple'),
              stext(610, 250, 'close, but is the gap real? → chi-square test', 'purple', 11, step=4),
              stext(610, 280, 'Pune and Juhu: mutually exclusive,', 'red', 12, step=5),
              stext(610, 298, 'P(both) = 0 ≠ 0.295 × 0.320 → dependent', 'red', 12, step=5)]
    return anim(canvas(760, 310, *elems), [
        'The rectangle is all 600 students. 35.3 % were placed; the complement rule gives 64.7 % not placed.',
        '29.5 % study in Pune; 8.8 % are both placed and from Pune.',
        'Addition rule: add the two probabilities and subtract the overlap so it is not counted twice.',
        'If placement were independent of centre, P(both) would equal the product 0.104. A formal test decides whether 0.088 is different enough.',
        'Mutually exclusive events (one student cannot be in two centres) are the opposite of independent.',
    ])


def bayes_anim():
    elems = [stext(380, 24, 'Bayes with natural frequencies: 10,000 project reports', 'blue', 15, bold=True),
             sbox(300, 45, 160, 46, '10,000 reports', 'prior: 3 % copied', 'gray', step=1, size=12),
             sarrow(340, 91, 180, 120, 'gray', step=1), sarrow(420, 91, 580, 120, 'gray', step=1),
             sbox(90, 122, 180, 46, '300 copied', '3 %', 'red', step=1, size=12),
             sbox(490, 122, 180, 46, '9,700 honest', '97 %', 'green', step=1, size=12),
             sarrow(140, 168, 80, 198, 'gray', step=2), sarrow(220, 168, 270, 198, 'gray', step=2),
             sbox(20, 200, 130, 46, '285 flagged', 'sensitivity 95 %', 'red', step=2, size=12),
             sbox(200, 200, 130, 46, '15 missed', '5 %', 'gray', step=2, size=12),
             sarrow(540, 168, 480, 198, 'gray', step=3), sarrow(620, 168, 670, 198, 'gray', step=3),
             sbox(410, 200, 140, 46, '388 flagged', 'false alarms 4 %', 'amber', step=3, size=12),
             sbox(600, 200, 140, 46, '9,312 clear', '96 %', 'green', step=3, size=12),
             stext(380, 280, 'P(copied | flag) = 285 / (285 + 388) = 0.423', 'amber', 15, step=4, bold=True, focus=4),
             stext(380, 305, 'most flags are false alarms because honest reports vastly outnumber copied ones (base rate)', 'red', 12, step=4),
             stext(380, 330, 'second independent flag: prior 0.423 → posterior 0.946 · simulation of 1,000,000 reports: 0.422', 'cyan', 12, step=5)]
    return anim(canvas(760, 345, *elems), [
        'Start with the base rate: of 10,000 reports, about 300 are copied.',
        'The tool flags 95 % of copied reports: 285.',
        'It also flags 4 % of honest reports: 388 false alarms.',
        'Among all flagged reports only 285 of 673 are copied: Bayes\' theorem gives 0.423.',
        'A second independent check updates the prior again; the simulation confirms the formula.',
    ])


def expect_anim():
    elems = [stext(380, 24, 'Expected value of a guess with negative marking (+3 / −1)', 'blue', 15, bold=True)]
    for i, (opts, pc, ev) in enumerate([(4, 0.25, 0.0), (3, 1 / 3, 1 / 3), (2, 0.5, 1.0)]):
        X = 30 + i * 175
        st = 1 if i == 0 else i + 1
        elems += [stext(X + 70, 56, f'{opts} options left', 'gray', 12, step=st, bold=True),
                  f'<rect x="{X + 10}" y="{200 - pc * 150:.0f}" width="50" height="{pc * 150:.0f}" fill="#10b981" data-step="{st}"/>',
                  f'<rect x="{X + 80}" y="{200 - (1 - pc) * 150:.0f}" width="50" height="{(1 - pc) * 150:.0f}" fill="#ef4444" data-step="{st}"/>',
                  stext(X + 35, 216, '+3', 'green', 11, step=st), stext(X + 105, 216, '−1', 'red', 11, step=st),
                  stext(X + 35, 195 - pc * 150, f'{pc:.2f}', 'green', 10, step=st), stext(X + 105, 195 - (1 - pc) * 150, f'{1 - pc:.2f}', 'red', 10, step=st),
                  stext(X + 70, 240, f'E = {ev:+.3f}', 'amber', 13, step=st, bold=True)]
    elems += [stext(140, 262, '3·0.25 − 1·0.75 = 0', 'gray', 11, step=1),
              stable(560, 60, ['20 blind guesses', 'value'], [['mean (sim.)', '−0.02'], ['SD (sim.)', '7.74'], ['SD theory √60', '7.75'], ['students losing marks', '41.5 %']],
                     [130, 60], step=4, title='100,000 simulated students', title_color='purple'),
              stext(380, 292, 'E[X] = Σ x·p · Var = Σ (x − E)²·p · E[X+Y] = E[X] + E[Y] · variances add if independent', 'cyan', 12, step=5),
              stext(380, 314, 'fair die: E = 3.5, Var = 15.167 − 12.25 = 2.917 · two dice: E = 7, Var = 5.833', 'cyan', 12, step=5)]
    return anim(canvas(760, 330, *elems), [
        'A blind guess among 4 options: 25 % chance of +3, 75 % chance of −1, so E = 0.',
        'Eliminate one option and E becomes +0.333 marks per question.',
        'With two options left, E = +1: guess.',
        'Simulating 100,000 students who guess 20 questions blindly matches the theory: mean ≈ 0, SD ≈ 7.75, and 41.5 % lose marks.',
        'Expectation is linear; variances add for independent variables.',
    ])


def counting_anim():
    elems = [stext(380, 24, 'Counting: order matters (permutations) or not (combinations)', 'blue', 15, bold=True)]
    for i, (role, n) in enumerate([('leader', 10), ('coder', 9), ('tester', 8)]):
        X = 40 + i * 110
        elems += [sbox(X, 50, 90, 50, role, f'{n} choices', 'blue', step=1, size=12)]
        if i:
            elems.append(stext(X - 10, 80, '×', 'gray', 16, step=1))
    elems += [stext(380, 80, '= 720 = 10P3', 'blue', 15, step=1, bold=True, anchor='start'),
              stext(40, 130, 'the same 3 people can fill the roles in 3! = 6 ways →', 'gray', 12, step=2, anchor='start'),
              stext(380, 160, '720 ÷ 6 = 120 = 10C3 teams', 'green', 15, step=2, bold=True, anchor='start'),
              stext(40, 160, 'ABC ACB BAC BCA CAB CBA → one team', 'purple', 12, step=2, anchor='start')]
    X, Y, W, H = 60, 190, 360, 120
    pts = [(10, 0.117), (23, 0.507), (40, 0.891), (60, 0.994)]
    import math
    def pb(n):
        p = 1.0
        for k in range(int(n)):
            p *= (365 - k) / 365
        return 1 - p
    elems += [_axes(X, Y, W, H, 'students in the batch', 'P(shared birthday)', step=3), _curve(pb, 0, 70, X, Y, W, H, 1.0, 'amber', step=3)]
    for n, pv in pts:
        x = X + W * n / 70
        y = Y + H - H * pv
        elems += [_dot(x, y, 'red', step=4, r=5), stext(x + 6, y + 14, f'{n}: {pv:.3f}', 'red', 10, step=4, anchor='start')]
    elems += [stext(600, 220, 'P(all different) = 365/365 · 364/365 · …', 'cyan', 12, step=3),
              stext(600, 242, 'P(shared) = 1 − P(all different)', 'cyan', 12, step=3),
              stext(600, 275, '23 people → just over 50 %', 'amber', 12, step=4),
              stext(600, 297, '60 students: 1,770 pairs → 99.4 % (sim. 0.994)', 'amber', 12, step=4),
              stext(380, 368, 'math.perm · math.comb · itertools.permutations / combinations', 'gray', 12, step=5)]
    return anim(canvas(760, 380, *elems), [
        'Roles are distinct, so order matters: 10 × 9 × 8 = 720 assignments (a permutation).',
        'Each group of three appears 3! = 6 times, so there are 720 ÷ 6 = 120 teams (a combination).',
        'Birthday problem: compute the probability that everyone is different and take the complement.',
        'With 23 people the chance of a shared birthday already exceeds 50 %; with 60 it is near certain.',
        'Python\'s math and itertools modules count or list the outcomes.',
    ])


def lln_anim():
    import math
    X, Y, W, H = 60, 50, 400, 200
    sx = lambda n: X + W * math.log10(n) / 5
    sy = lambda v: Y + H - H * (v - 2.5) / 2
    pts = [(10, 3.1), (100, 3.64), (1000, 3.488), (10000, 3.4752), (100000, 3.4998)]
    elems = [stext(380, 24, 'Law of large numbers and Monte Carlo simulation', 'blue', 15, bold=True),
             _axes(X, Y, W, H, '', 'running average', step=1), stext(X + W / 2, Y + H + 32, 'number of die rolls (log scale)', 'gray', 11, step=1),
             f'<line x1="{X}" y1="{sy(3.5)}" x2="{X + W}" y2="{sy(3.5)}" stroke="#10b981" stroke-dasharray="6,4" data-step="1"/>',
             stext(X + W + 6, sy(3.5) + 4, '3.5', 'green', 11, step=1, anchor='start')]
    for v in [10, 100, 1000, 10000, 100000]:
        elems.append(stext(sx(v), Y + H + 14, f'{v:,}', 'gray', 9, step=1))
    d = 'M ' + ' L '.join(f'{sx(n):.1f} {sy(v):.1f}' for n, v in [(1, 4.0)] + pts)
    elems += [f'<path d="{d}" stroke="#0ea5e9" stroke-width="2.5" fill="none" data-step="2"/>']
    for n, v in pts:
        elems += [_dot(sx(n), sy(v), 'blue', step=2), stext(sx(n), sy(v) - 10, f'{v}', 'blue', 10, step=2)]
    elems += [stext(260, 304, 'not monotonic: 10,000 rolls (error 0.025) was worse than 1,000 (0.012)', 'amber', 11, step=3),
              stable(500, 50, ['simulation', 'result'], [['P(> 55 of 80 attend)', '0.0418'], ['exact binomial', '0.0417'], ['mean attendance', '48.00']],
                     [150, 80], step=4, title='lab capacity, 100,000 days', title_color='purple'),
              stable(500, 170, ['n points', 'π estimate'], [['1,000', '3.12000'], ['100,000', '3.15164'], ['10,000,000', '3.14136']], [150, 80], step=5,
                     title='estimating π', title_color='cyan'),
              stext(610, 300, 'error ∝ 1/√n: 100× points → 10× precision', 'cyan', 12, step=5)]
    return anim(canvas(760, 320, *elems), [
        'Each roll of a fair die has expected value 3.5.',
        'The running average wanders early but settles towards 3.5 as rolls accumulate.',
        'Convergence is a trend, not a promise for every step; the gambler\'s fallacy misreads the law.',
        'Monte Carlo: simulate many days of attendance to estimate a probability; it matches the exact binomial answer.',
        'Precision grows only with the square root of the number of simulations.',
    ])



# ============================================================ section 3
def binom_anim():
    from math import comb, exp, factorial
    bp = [comb(10, k) * 0.35 ** k * 0.65 ** (10 - k) for k in range(11)]
    pp = [exp(-4) * 4 ** k / factorial(k) for k in range(13)]
    elems = [stext(380, 24, 'Binomial (fixed trials) vs Poisson (events per interval)', 'blue', 15, bold=True),
             stext(190, 52, 'Binomial(n=10, p=0.35): offers out of 10 shortlisted', 'blue', 12, step=1, bold=True),
             _axes(30, 60, 330, 160, '', '', step=1)]
    bw = 330 / 11
    for k, v in enumerate(bp):
        col = '#f59e0b' if k >= 5 else '#0ea5e9'
        st = 2 if k >= 5 else 1
        elems.append(f'<rect x="{30 + k * bw + 3:.1f}" y="{220 - v * 560:.1f}" width="{bw - 6:.1f}" height="{v * 560:.1f}" fill="#0ea5e9" data-step="1"/>')
        if k >= 5:
            elems.append(f'<rect x="{30 + k * bw + 3:.1f}" y="{220 - v * 560:.1f}" width="{bw - 6:.1f}" height="{v * 560:.1f}" fill="#f59e0b" data-step="2"/>')
        elems.append(stext(30 + k * bw + bw / 2, 234, str(k), 'gray', 10, step=1))
    elems += [stext(195, 254, 'P(3) = 0.252 · P(≤3) = 0.514 · P(≥5) = sf(4) = 0.249', 'amber', 11, step=2),
              stext(195, 272, 'mean np = 3.5 · variance np(1−p) = 2.275', 'gray', 11, step=2),
              stext(570, 52, 'Poisson(λ=4): doubts per lab hour', 'purple', 12, step=3, bold=True),
              _axes(400, 60, 340, 160, '', '', step=3)]
    bw = 340 / 13
    for k, v in enumerate(pp):
        col = '#ef4444' if k >= 8 else '#8b5cf6'
        elems.append(f'<rect x="{400 + k * bw + 3:.1f}" y="{220 - v * 560:.1f}" width="{bw - 6:.1f}" height="{v * 560:.1f}" fill="{col}" data-step="{4 if k >= 8 else 3}"/>')
        elems.append(stext(400 + k * bw + bw / 2, 234, str(k), 'gray', 10, step=3))
    elems += [stext(570, 254, 'P(8 or more) = sf(7) = 0.051 · mean = variance = 4', 'red', 11, step=4),
              stext(570, 272, '95th percentile: 8 doubts in an hour', 'purple', 11, step=4),
              stext(380, 302, 'Binomial(2000, 0.002) vs Poisson(4): k=2 → 0.1465 vs 0.1465 · k=4 → 0.1956 vs 0.1954', 'cyan', 12, step=5)]
    return anim(canvas(760, 318, *elems), [
        'The binomial counts successes in a fixed number of independent trials: here offers among 10 shortlisted students, each with p = 0.35.',
        '"At least 5 offers" is the orange tail: sf(4), because sf(k) means P(X > k).',
        'The Poisson counts events in an interval at a constant rate, with no fixed number of trials.',
        'The red tail is the chance of a very busy hour, useful for deciding when a second TA is needed.',
        'For many trials with a small p, the binomial is almost identical to a Poisson with λ = np.',
    ])


def normal_anim():
    X, Y, W, H = 40, 50, 440, 200
    f = _npdf(0, 1)
    sx = lambda z: X + W * (z + 4) / 8
    elems = [stext(380, 24, 'The normal distribution, z-scores and the 68-95-99.7 rule', 'blue', 15, bold=True),
             _area(f, -4, 4, -3, 3, X, Y, W, H, 0.42, 'purple', step=3), _area(f, -4, 4, -2, 2, X, Y, W, H, 0.42, 'blue', step=2),
             _area(f, -4, 4, -1, 1, X, Y, W, H, 0.42, 'green', step=1),
             _curve(f, -4, 4, X, Y, W, H, 0.42, '#e2e8f0', step=1, width=2),
             f'<line x1="{X}" y1="{Y + H}" x2="{X + W}" y2="{Y + H}" stroke="#64748b" data-step="1"/>']
    for z in range(-3, 4):
        elems.append(stext(sx(z), Y + H + 15, f'{z:+d}σ' if z else 'μ', 'gray', 10, step=1))
    elems += [stext(sx(0), Y + 120, '68.3 %', '#022c22', 13, step=1, bold=True), stext(sx(0), Y + 160, '95.4 % (±1.96σ → 95 %)', '#082f49', 11, step=2, bold=True),
              stext(sx(0), Y + 190, '99.7 %', '#e9d5ff', 11, step=3),
              f'<line x1="{sx(1.56)}" y1="{Y + 40}" x2="{sx(1.56)}" y2="{Y + H}" stroke="#f59e0b" stroke-width="2.5" data-step="4"/>',
              stext(sx(1.56) + 4, Y + 34, 'score 75 → z = 1.56', 'amber', 11, step=4, anchor='start'),
              stable(500, 55, ['within', 'observed', 'normal'], [['±1 SD', '0.660', '0.683'], ['±2 SD', '0.970', '0.954'], ['±3 SD', '1.000', '0.997']],
                     [70, 80, 80], step=3, title='real final scores (μ 58.72, σ 10.40)', title_color='green'),
              stext(615, 200, '75 is above 94.1 % (model) / 94.2 % (data)', 'amber', 11, step=4),
              stext(615, 230, 'SQL 75 (μ 68, σ 6) → z = +1.17', 'cyan', 11, step=5), stext(615, 250, 'ML 62 (μ 50, σ 8) → z = +1.50 ✓', 'cyan', 11, step=5, bold=True),
              stext(380, 300, 'z = (x − μ) / σ · norm.cdf(z) = area to the left · norm.ppf(0.90) → top-10 % cut-off 72.05 (actual 72.51)', 'gray', 12, step=5)]
    return anim(canvas(760, 315, *elems), [
        'About 68 % of a normal distribution lies within one standard deviation of the mean.',
        'About 95 % lies within two SDs (exactly 95 % within 1.96).',
        'About 99.7 % lies within three SDs. The real final scores follow the rule closely.',
        'A z-score locates a value: 75 marks is 1.56 SDs above the mean, beating about 94 % of students.',
        'z-scores compare marks across papers with different difficulty; cdf and ppf turn them into areas and cut-offs.',
    ])


def pdfcdf_anim():
    import math
    pdf = lambda t: 3 * math.exp(-3 * t)
    cdf = lambda t: 1 - math.exp(-3 * t)
    elems = [stext(380, 24, 'PDF vs CDF: gaps between job submissions (rate 3 per minute)', 'blue', 15, bold=True),
             stext(200, 52, 'PDF: density (area = probability)', 'blue', 12, step=1, bold=True),
             _axes(40, 60, 320, 170, '', '', step=1), _curve(pdf, 0, 2, 40, 60, 320, 170, 3.1, 'blue', step=1),
             _area(pdf, 0, 2, 1, 2, 40, 60, 320, 170, 3.1, 'red', step=2),
             stext(270, 205, 'P(gap > 1 min) = e⁻³ = 0.0498', 'red', 11, step=2),
             stext(48, 70, 'height 3.0 at 0 (a density can exceed 1)', 'gray', 10, step=1, anchor='start'),
             stext(40, 248, '0', 'gray', 10, step=1), stext(200, 248, '1 min', 'gray', 10, step=1), stext(360, 248, '2 min', 'gray', 10, step=1),
             stext(570, 52, 'CDF: P(gap ≤ t)', 'green', 12, step=3, bold=True),
             _axes(400, 60, 320, 170, '', '', step=3), _curve(cdf, 0, 2, 400, 60, 320, 170, 1.0, 'green', step=3),
             f'<line x1="400" y1="{60 + 170 * 0.5:.0f}" x2="{400 + 320 * 0.231 / 2:.0f}" y2="{60 + 170 * 0.5:.0f}" stroke="#f59e0b" stroke-dasharray="4,3" data-step="4"/>',
             f'<line x1="{400 + 320 * 0.231 / 2:.0f}" y1="{60 + 170 * 0.5:.0f}" x2="{400 + 320 * 0.231 / 2:.0f}" y2="230" stroke="#f59e0b" stroke-dasharray="4,3" data-step="4"/>',
             stext(520, 140, 'ppf(0.5) = median 13.9 s', 'amber', 11, step=4, anchor='start'),
             stext(520, 160, 'ppf(0.9) = 46.1 s', 'amber', 11, step=4, anchor='start'),
             stext(380, 270, 'P(a < X < b) = F(b) − F(a) · Uniform(10, 30): P(15 < X < 20) = 0.25', 'cyan', 12, step=4),
             stext(380, 295, 'memoryless: P(T > 1.5 | T > 1) = 0.2231 = P(T > 0.5) · gaps exponential ⇔ counts Poisson (sim: mean 2.999, var 2.998)', 'purple', 12, step=5)]
    return anim(canvas(760, 310, *elems), [
        'The exponential PDF describes waiting times; its height is a density, not a probability.',
        'Probabilities are areas: a gap longer than one minute happens about 5 % of the time.',
        'The CDF accumulates the area from the left and rises from 0 to 1.',
        'Read the CDF backwards (ppf) to get the median or a 90th-percentile timeout; differences of the CDF give interval probabilities.',
        'The exponential forgets how long you have waited, and exponential gaps produce Poisson counts.',
    ])


def tdist_anim():
    import math
    def tpdf(v):
        c = math.gamma((v + 1) / 2) / (math.sqrt(v * math.pi) * math.gamma(v / 2))
        return lambda x: c * (1 + x * x / v) ** (-(v + 1) / 2)
    X, Y, W, H = 30, 55, 400, 190
    elems = [stext(380, 24, 'The t distribution: a normal curve with heavier tails', 'blue', 15, bold=True),
             _curve(_npdf(0, 1), -5, 5, X, Y, W, H, 0.42, 'green', step=1), _curve(tpdf(2), -5, 5, X, Y, W, H, 0.42, 'red', step=2),
             _curve(tpdf(11), -5, 5, X, Y, W, H, 0.42, 'amber', step=3, width=2),
             f'<line x1="{X}" y1="{Y + H}" x2="{X + W}" y2="{Y + H}" stroke="#64748b" data-step="1"/>',
             stext(X + W / 2 + 70, Y + 30, 'normal', 'green', 11, step=1, anchor='start'), stext(X + 50, Y + H - 40, 't(df=2): fat tails', 'red', 11, step=2),
             stext(X + W / 2 + 70, Y + 50, 't(df=11)', 'amber', 11, step=3, anchor='start'),
             stable(460, 55, ['df', '95 % critical'], [['2', '4.303'], ['5', '2.571'], ['11', '2.201'], ['30', '2.042'], ['1000', '1.962'], ['normal', '1.960']],
                    [80, 110], step=3, title='two-sided 95 % critical values', title_color='amber', focus_rows={2: '3'}),
             stext(230, 272, 'simulated n = 6: |t| > 1.96 in 10.6 % of samples (t(5) predicts 10.7 %, not 5 %)', 'red', 11, step=4),
             stext(380, 300, 'chi-square(df): mean = df, 95th pct of χ²(4) = 9.488 · F(2, 597) 95th pct = 3.011 (ANOVA)', 'cyan', 12, step=5)]
    return anim(canvas(760, 315, *elems), [
        'The standard normal curve, used when σ is known.',
        'With σ estimated from very few observations, the statistic follows a t distribution with much fatter tails.',
        'As degrees of freedom grow, t approaches the normal; critical values fall from 4.30 towards 1.96.',
        'Using 1.96 with n = 6 would produce "significant" results twice as often as intended.',
        'Chi-square and F are the sampling distributions behind variance, contingency-table and ANOVA tests.',
    ])


def qq_anim():
    import math
    from statistics import NormalDist
    nd = NormalDist()
    elems = [stext(380, 24, 'Q-Q plots: sample quantiles vs normal quantiles', 'blue', 15, bold=True)]
    for j, (title, col, fn, st) in enumerate([('packages (skew 1.53)', 'red', lambda z: math.exp(0.35 * z), 1), ('log packages (skew 0.29)', 'green', lambda z: z, 2)]):
        X = 40 + j * 250
        elems += [stext(X + 100, 52, title, col, 12, step=st, bold=True), _axes(X, 60, 200, 170, '', '', step=st),
                  f'<line x1="{X}" y1="230" x2="{X + 200}" y2="60" stroke="#64748b" stroke-dasharray="5,4" data-step="{st}"/>']
        zs = [nd.inv_cdf((k + 0.5) / 30) for k in range(30)]
        vals = [fn(z) for z in zs]
        lo, hi = min(vals), max(vals)
        for k, (z, v) in enumerate(zip(zs, vals)):
            x = X + 200 * (z - zs[0]) / (zs[-1] - zs[0])
            y = 230 - 170 * (v - lo) / (hi - lo)
            elems.append(_dot(x, y, col, step=st, r=3.5))
        elems.append(stext(X + 100, 248, 'theoretical normal quantiles', 'gray', 10, step=st))
    elems += [stext(140, 272, 'curve upwards = right skew', 'red', 11, step=1), stext(390, 272, 'straight line = normal', 'green', 11, step=2),
              stable(515, 55, ['column', 'r', 'Shapiro p'], [['final_score', '0.997', '0.014'], ['study_hours', '0.980', '0.000'], ['salary', '0.944', '0.000'], ['log salary', '0.996', '0.325']],
                     [95, 55, 75], step=3, title='real run', title_color='amber', focus_rows={0: '4'}),
              stable(515, 222, ['n', 'rejects'], [['20', '11 %'], ['200', '37 %'], ['5000', '100 %']], [100, 125], step=4, title='nearly-normal t(10) data', title_color='purple'),
              stext(380, 345, 'tests answer "can I detect non-normality?", not "does it matter?" · use plots + purpose', 'cyan', 12, step=5)]
    return anim(canvas(760, 360, *elems), [
        'Plot each sorted value against the quantile a normal distribution would predict. Right-skewed packages bend upwards.',
        'After a log transform, the points lie close to the straight line.',
        'The Q-Q correlation and Shapiro-Wilk test summarise the same idea: log packages pass, raw packages fail.',
        'The same slightly non-normal data is rarely rejected at n = 20 and always rejected at n = 5,000.',
        'Decide with plots and with how sensitive your method is, not with the p-value alone.',
    ])


# ============================================================ section 4
def sampling_anim():
    import random
    rng = random.Random(6)
    cols = ['#0ea5e9', '#10b981', '#f59e0b']
    elems = [stext(380, 24, 'Sampling methods on a population of 60 students (3 centres)', 'blue', 15, bold=True)]
    def grid(X, chosen, st, title, col='white'):
        out = [stext(X + 80, 52, title, 'gray', 12, step=st, bold=True)]
        for i in range(60):
            r, c = divmod(i, 10)
            x, y = X + c * 16 + 8, 66 + r * 16
            fill = cols[r // 2] if i in chosen else '#334155'
            out.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{fill}" data-step="{st}"/>')
        return out
    srs = set(rng.sample(range(60), 9))
    strat = set(rng.sample(range(0, 20), 3) + rng.sample(range(20, 40), 3) + rng.sample(range(40, 60), 3))
    clus = set(range(20, 30))
    for X, chosen, st, t in [(20, srs, 1, 'simple random'), (205, strat, 2, 'stratified (3 per centre)'), (390, clus, 3, 'cluster (1 whole batch)'),
                             (575, set(range(0, 60, 7)), 3, 'systematic (every 7th)')]:
        elems += grid(X, chosen, st, t)
    elems += [stext(100, 178, 'rows = 3 centres (2 rows each)', 'gray', 10, step=1),
              stable(30, 212, ['method (n=60)', 'mean score', 'placed'], [['population', '58.72', '0.353'], ['simple random', '58.64', '0.283'], ['stratified', '59.34', '0.317'],
                                                                         ['convenience', '65.43', '0.600']], [130, 90, 70], step=4, title='real run', title_color='amber', focus_rows={3: '4'}),
              stable(380, 212, ['n', 'random error', 'convenience'], [['30', '1.59', '7.56'], ['60', '1.12', '6.71'], ['120', '0.72', '6.21']],
                     [60, 110, 110], step=5, title='more data shrinks noise, not bias', title_color='red')]
    return anim(canvas(760, 360, *elems), [
        'Simple random sampling: every student has the same chance; centres may be over- or under-represented by luck.',
        'Stratified sampling: a random sample inside each centre guarantees every group is represented.',
        'Cluster sampling takes whole groups (a batch); systematic sampling takes every k-th student from a list.',
        'A convenience sample of the most regular attenders overstates both scores and placement.',
        'Larger random samples get closer to the truth; larger biased samples stay biased.',
    ])


def clt_anim():
    import math
    elems = [stext(380, 24, 'Central limit theorem: means of skewed packages become normal', 'blue', 15, bold=True)]
    ln = lambda x: (math.exp(-(math.log(x) - math.log(6)) ** 2 / (2 * 0.35 ** 2)) / (x * 0.35 * math.sqrt(2 * math.pi))) if x > 0 else 0
    panels = [('population (n = 1)', ln, 0.2, 'red', 'SD 2.68 · skew +1.53', 1),
              ('means of n = 5', _npdf(6.57, 1.197), 0.36, 'amber', 'SD 1.196 · skew +0.70', 2),
              ('means of n = 30', _npdf(6.57, 0.489), 0.85, 'green', 'SD 0.489 · skew +0.29', 3),
              ('means of n = 100', _npdf(6.57, 0.268), 1.55, 'blue', 'SD 0.267 · skew +0.15', 4)]
    for i, (t, fn, ymax, col, lab, st) in enumerate(panels):
        X = 20 + i * 185
        elems += [stext(X + 85, 52, t, col, 12, step=st, bold=True), _curve(fn, 1, 14, X, 60, 170, 150, ymax, col, step=st, fill=True),
                  f'<line x1="{X}" y1="210" x2="{X + 170}" y2="210" stroke="#64748b" data-step="{st}"/>',
                  f'<line x1="{X + 170 * (6.57 - 1) / 13:.0f}" y1="60" x2="{X + 170 * (6.57 - 1) / 13:.0f}" y2="210" stroke="#e2e8f0" stroke-dasharray="3,3" data-step="{st}"/>',
                  stext(X + 85, 228, lab, 'gray', 10, step=st)]
    elems += [stext(380, 258, 'mean of means stays at μ = 6.57 · SD of means = σ/√n (0.489 vs 0.489 at n = 30)', 'green', 12, step=4, bold=True),
              stext(380, 282, '95.1 % of sample means (n = 30) fall within ±1.96·σ/√n → normal-based CIs and t-tests work', 'cyan', 12, step=5),
              stext(380, 304, 'the data stays skewed; only the distribution of the mean becomes normal', 'red', 12, step=5)]
    return anim(canvas(760, 318, *elems), [
        'Individual packages are strongly right-skewed.',
        'Averages of 5 random packages are already less skewed and much narrower.',
        'Averages of 30 look almost normal.',
        'With 100 the bell is narrow and symmetric; its centre stays at μ and its SD matches σ/√n.',
        'This is why intervals and tests for means work even when the raw data is not normal.',
    ])


def se_anim():
    elems = [stext(380, 24, 'Standard deviation vs standard error (study hours)', 'blue', 15, bold=True)]
    sx = lambda v: 60 + v * 26
    elems += [f'<line x1="{sx(0)}" y1="190" x2="{sx(25)}" y2="190" stroke="#64748b" data-step="1"/>']
    for v in range(0, 26, 5):
        elems.append(stext(sx(v), 206, str(v), 'gray', 10, step=1))
    elems += [f'<rect x="{sx(8.63 - 4.33)}" y="60" width="{sx(8.63 + 4.33) - sx(8.63 - 4.33)}" height="22" fill="#8b5cf6" fill-opacity="0.5" data-step="1"/>',
              stext(sx(8.63 + 4.33) + 8, 76, 'mean ± SD: individuals (SD 4.33, does not shrink)', 'purple', 11, step=1, anchor='start')]
    for i, (n, se, st) in enumerate([(25, 0.866, 2), (100, 0.433, 3), (400, 0.216, 4)]):
        y = 100 + i * 28
        elems += [f'<rect x="{sx(8.63 - se)}" y="{y}" width="{sx(8.63 + se) - sx(8.63 - se)}" height="20" fill="#10b981" data-step="{st}"/>',
                  stext(sx(8.63 + 4.33) + 8, y + 15, f'n = {n}: SE = {se}', 'green', 11, step=st, anchor='start')]
    elems += [f'<line x1="{sx(8.63)}" y1="55" x2="{sx(8.63)}" y2="190" stroke="#f59e0b" stroke-dasharray="4,3" data-step="1"/>',
              stext(sx(8.63), 222, 'mean 8.63 h', 'amber', 11, step=1),
              stext(380, 250, 'SE = s / √n · 4× the students → half the SE · simulated SD of 5,000 means at n = 100: 0.427', 'green', 12, step=4),
              stext(380, 274, 'proportion: SE = √(p(1−p)/n) = 0.0195 for 35.3 % of 600 · SE 0.01 needs n ≈ 2,275', 'cyan', 12, step=5),
              stext(380, 298, 'describe data with SD · describe precision of an estimate with SE or a CI', 'amber', 12, step=5)]
    return anim(canvas(760, 312, *elems), [
        'The SD describes how much individual students differ: about ±4.3 hours around the mean.',
        'The SE describes how much the mean of a sample of 25 would move between samples.',
        'With 100 students the SE halves.',
        'With 400 it halves again: SE shrinks with √n while the SD stays put.',
        'The same idea gives the SE of a proportion and tells you the sample size needed for a target precision.',
    ])


def ci_anim():
    import random
    rng = random.Random(12)
    elems = [stext(380, 24, '95 % confidence intervals: the net catches the fish 95 % of the time', 'blue', 15, bold=True)]
    mu_x = 230
    elems.append(f'<line x1="{mu_x}" y1="45" x2="{mu_x}" y2="270" stroke="#f59e0b" stroke-width="2" data-step="1"/>')
    elems.append(stext(mu_x, 284, 'true mean 58.72', 'amber', 11, step=1))
    for i in range(20):
        half = 40 + rng.uniform(-6, 6)
        c = mu_x + max(-0.85 * half, min(0.85 * half, rng.gauss(0, 20)))
        if i == 13:
            c = mu_x + 62
        miss = abs(c - mu_x) > half
        col = '#ef4444' if miss else '#10b981'
        y = 52 + i * 11
        st = 1 if i < 5 else 2
        elems += [f'<line x1="{c - half:.0f}" y1="{y}" x2="{c + half:.0f}" y2="{y}" stroke="{col}" stroke-width="3" data-step="{st}"/>',
                  _dot(c, y, col, step=st, r=3)]
    elems += [stext(330, 200, '1 of 20 misses', 'red', 11, step=2, anchor='start'),
              stable(420, 50, ['level', 'interval for mean score'], [['90 %', '[58.02, 59.42]'], ['95 %', '[57.89, 59.56]'], ['99 %', '[57.63, 59.82]']],
                     [70, 190], step=3, title='real data: 58.72 ± 1.964 × 0.425', title_color='green', focus_rows={1: '3'}),
              stable(420, 180, ['placed', 'Wald', 'Wilson'], [['212 / 600', '[0.315, 0.392]', '[0.316, 0.392]'], ['3 / 12', '[0.005, 0.495]', '[0.089, 0.532]']],
                     [80, 95, 95], step=4, title='proportions', title_color='purple', focus_rows={1: '4'}),
              stext(380, 300, 'simulation: 10,000 intervals from samples of 40 → 94.6 % contain the true mean', 'cyan', 12, step=5)]
    return anim(canvas(760, 315, *elems), [
        'Each sample gives its own interval around its own mean.',
        'Over many samples, about 95 % of the intervals cover the true mean; a few miss.',
        'For the real final scores: estimate ± t × SE. Higher confidence means a wider interval.',
        'For proportions, Wilson behaves well even for small samples where the simple Wald interval breaks down.',
        'Simulation confirms the coverage: the 95 % belongs to the method, not to a single interval.',
    ])


def boot_anim():
    elems = [stext(380, 24, 'Bootstrap: resample with replacement to see the uncertainty', 'blue', 15, bold=True),
             sbox(20, 50, 170, 56, 'original sample', '212 placed packages\nmedian 6.00', 'blue', step=1, size=12)]
    for i in range(3):
        y = 50 + i * 66
        elems += [sarrow(190, 78, 238, y + 25, 'gray', step=2),
                  sbox(240, y, 170, 50, f'resample {i + 1}', 'draw 212 with replacement', 'purple', step=2, size=11),
                  sarrow(410, y + 25, 438, y + 25, 'gray', step=3),
                  stext(470, y + 30, ['5.9', '6.2', '6.0'][i], 'amber', 13, step=3, bold=True)]
    elems += [stext(325, 260, '… 10,000 times (each uses ~135 distinct students)', 'gray', 11, step=2)]
    vals = [2, 6, 18, 40, 62, 70, 55, 30, 14, 5, 2]
    elems.append(_bars(vals, 520, 60, 220, 140, 72, 'amber', step=4))
    elems += [f'<line x1="{520 + 220 * 1.5 / 11:.0f}" y1="55" x2="{520 + 220 * 1.5 / 11:.0f}" y2="205" stroke="#ef4444" stroke-dasharray="4,3" data-step="5"/>',
              f'<line x1="{520 + 220 * 9.5 / 11:.0f}" y1="55" x2="{520 + 220 * 9.5 / 11:.0f}" y2="205" stroke="#ef4444" stroke-dasharray="4,3" data-step="5"/>',
              stext(630, 222, 'bootstrap medians', 'amber', 11, step=4),
              stext(630, 248, '2.5 % and 97.5 % → [5.70, 6.40]', 'red', 12, step=5, bold=True),
              stext(380, 290, 'bootstrap SE 0.175 · Kharghar − others median: +0.70, CI [0.0, 1.5] → touches 0, weak evidence', 'cyan', 12, step=5)]
    return anim(canvas(760, 305, *elems), [
        'Start from the one sample you have.',
        'Draw new samples of the same size with replacement: some students appear twice, others not at all.',
        'Compute the statistic (the median) for every resample.',
        'The pile of bootstrap medians shows how much the median would vary between samples.',
        'Its 2.5th and 97.5th percentiles form a 95 % confidence interval, with no formula needed.',
    ])



# ============================================================ section 5
def pvalue_anim():
    X, Y, W, H = 30, 55, 470, 190
    f = _npdf(0, 1)
    sx = lambda z: X + W * (z + 4) / 8
    elems = [stext(380, 24, 'p-value: how surprising is the data if H₀ is true?', 'blue', 15, bold=True),
             _curve(f, -4, 4, X, Y, W, H, 0.42, 'blue', step=1, fill=True),
             f'<line x1="{X}" y1="{Y + H}" x2="{X + W}" y2="{Y + H}" stroke="#64748b" data-step="1"/>',
             stext(sx(0), Y + 120, 'distribution of t if H₀: μ = 60', '#e2e8f0', 11, step=1)]
    for z in range(-4, 5, 2):
        elems.append(stext(sx(z), Y + H + 14, str(z), 'gray', 10, step=1))
    elems += [f'<line x1="{sx(-3.006):.0f}" y1="{Y + 60}" x2="{sx(-3.006):.0f}" y2="{Y + H}" stroke="#f59e0b" stroke-width="3" data-step="2"/>',
              stext(sx(-3.006), Y + 52, 'observed t = −3.006', 'amber', 11, step=2, bold=True),
              _area(f, -4, 4, -4, -3.006, X, Y, W, H, 0.42, 'red', step=3), _area(f, -4, 4, 3.006, 4, X, Y, W, H, 0.42, 'red', step=3),
              f'<line x1="{sx(3.006):.0f}" y1="{Y + 100}" x2="{sx(3.006):.0f}" y2="{Y + H}" stroke="#ef4444" stroke-dasharray="4,3" data-step="3"/>',
              stext(sx(0), Y + H + 32, 'p = area in both red tails beyond ±3.006 = 0.00276 (tiny slivers)', 'red', 11, step=3),
              f'<line x1="{sx(-1.964):.0f}" y1="{Y + 20}" x2="{sx(-1.964):.0f}" y2="{Y + H}" stroke="#94a3b8" stroke-dasharray="6,4" data-step="4"/>',
              f'<line x1="{sx(1.964):.0f}" y1="{Y + 20}" x2="{sx(1.964):.0f}" y2="{Y + H}" stroke="#94a3b8" stroke-dasharray="6,4" data-step="4"/>',
              stext(sx(0), Y + 14, 'α = 0.05 → critical ±1.964', 'gray', 11, step=4),
              stable(525, 55, ['quantity', 'value'], [['mean / μ₀', '58.72 / 60'], ['SE', '0.425'], ['t', '−3.006'], ['p (two-sided)', '0.00276'], ['simulated null', '0.00310'],
                                                    ['95 % CI', '[57.89, 59.56]']], [110, 110], step=4, title='600 students (real run)', title_color='amber', focus_rows={3: '4'}),
              stext(380, 302, '|t| > 1.964 → reject H₀ · the same drop with 25 students: p = 0.604 → fail to reject (not "accept")', 'green', 12, step=5),
              stext(380, 324, 'p = P(data this extreme | H₀) — not P(H₀ | data), not the size of the effect', 'red', 12, step=5)]
    return anim(canvas(760, 338, *elems), [
        'Assume H₀ is true (mean = 60): t would follow this distribution.',
        'Compute the test statistic from the data: the mean is 3.0 standard errors below 60.',
        'The p-value is the area beyond the observed statistic in both tails: 0.28 %. A simulation of null batches gives the same answer.',
        'With α = 0.05 the cut-offs are ±1.964; the observed t is beyond them, so H₀ is rejected.',
        'A small sample with the same drop is not significant: absence of evidence, not evidence of absence.',
    ])


def power_anim():
    X, Y, W, H = 30, 55, 470, 180
    f0, f1 = _npdf(0, 1), _npdf(2.8, 1)
    sx = lambda z: X + W * (z + 3.5) / 10
    crit = 1.96
    elems = [stext(380, 24, 'Type I error, Type II error and power', 'blue', 15, bold=True),
             _curve(f0, -3.5, 6.5, X, Y, W, H, 0.42, 'gray', step=1), stext(sx(0), Y + 10, 'H₀ true', 'gray', 11, step=1),
             f'<line x1="{sx(crit):.0f}" y1="{Y}" x2="{sx(crit):.0f}" y2="{Y + H}" stroke="#e2e8f0" stroke-width="2" stroke-dasharray="6,4" data-step="1"/>',
             stext(sx(crit), Y + H + 14, 'critical value', 'gray', 10, step=1),
             _area(f0, -3.5, 6.5, crit, 6.5, X, Y, W, H, 0.42, 'red', step=2), stext(sx(2.3), Y + H - 8, 'α', 'red', 13, step=2, bold=True),
             _curve(f1, -3.5, 6.5, X, Y, W, H, 0.42, 'green', step=3), stext(sx(3.6), Y + 10, 'H₁ true (real effect)', 'green', 11, step=3, anchor='start'),
             _area(f1, -3.5, 6.5, -3.5, crit, X, Y, W, H, 0.42, 'gray', step=3), stext(sx(1.3), Y + H - 30, 'β', '#e2e8f0', 13, step=3, bold=True),
             _area(f1, -3.5, 6.5, crit, 6.5, X, Y, W, H, 0.42, 'green', step=4), stext(sx(3.6), Y + 100, 'power = 1 − β', 'green', 12, step=4, bold=True),
             f'<line x1="{X}" y1="{Y + H}" x2="{X + W}" y2="{Y + H}" stroke="#64748b" data-step="1"/>',
             stable(525, 55, ['n per group', 'simulated', 'theory'], [['50', '0.233', '0.236'], ['150', '0.579', '0.579'], ['250', '0.808', '0.797'], ['400', '0.943', '0.942']],
                    [85, 70, 70], step=4, title='power for 3 marks (d = 0.25)', title_color='green', focus_rows={2: '4'}),
             stext(380, 268, 'H₀ true: 5.1 % of 10,000 simulated studies were "significant" = α', 'red', 12, step=2),
             stext(380, 292, 'solve_power(d=0.25, power=0.8, α=0.05) → 253 per group · α = 0.01 → 376 · d = 0.5 → 64 · d = 0.8 → 26', 'cyan', 12, step=5),
             stext(380, 314, 'bigger n or bigger effect separates the curves → fewer Type II errors', 'amber', 12, step=5)]
    return anim(canvas(760, 328, *elems), [
        'If H₀ is true, the test statistic follows the grey curve; we reject beyond the critical value.',
        'The red tail is the Type I error rate α: rejecting although nothing is going on.',
        'If there is a real effect, the statistic follows the green curve. The part left of the critical value is β, a missed effect (Type II error).',
        'The rest is power. For a 3-mark effect, about 250 students per group give 80 % power.',
        'A power analysis solves for the sample size before the study starts.',
    ])


def ttest_anim():
    X, Y, W, H = 30, 55, 470, 170
    a, b = _npdf(61.91, 12.70), _npdf(58.45, 12.74)
    sx = lambda v: X + W * (v - 20) / 80
    elems = [stext(380, 24, 'Two-sample t-test: flipped vs traditional (post-test)', 'blue', 15, bold=True),
             _curve(b, 20, 100, X, Y, W, H, 0.034, 'gray', step=1, fill=True), _curve(a, 20, 100, X, Y, W, H, 0.034, 'green', step=1, fill=True),
             f'<line x1="{X}" y1="{Y + H}" x2="{X + W}" y2="{Y + H}" stroke="#64748b" data-step="1"/>',
             stext(sx(40), Y + 60, 'traditional 58.45 (n 304)', 'gray', 11, step=1), stext(sx(84), Y + 60, 'flipped 61.91 (n 296)', 'green', 11, step=1)]
    for v in range(20, 101, 20):
        elems.append(stext(sx(v), Y + H + 14, str(v), 'gray', 10, step=1))
    elems += [f'<line x1="{sx(58.45):.0f}" y1="{Y}" x2="{sx(58.45):.0f}" y2="{Y + H}" stroke="#94a3b8" stroke-width="2" data-step="2"/>',
              f'<line x1="{sx(61.91):.0f}" y1="{Y}" x2="{sx(61.91):.0f}" y2="{Y + H}" stroke="#10b981" stroke-width="2" data-step="2"/>',
              stext(sx(60.2), Y - 4, 'diff 3.45', 'amber', 11, step=2, bold=True),
              stable(525, 55, ['test', 't', 'p'], [['Levene', '—', '0.473'], ['Student', '3.326', '0.0009'], ['Welch (df 597.7)', '3.326', '0.0009']],
                     [110, 55, 65], step=3, title='real run', title_color='amber', focus_rows={2: '3'}),
              stext(630, 175, 'difference 3.45 marks', 'green', 12, step=4, bold=True), stext(630, 195, '95 % CI [1.41, 5.49]', 'green', 12, step=4),
              stext(630, 215, "Cohen's d = 0.272 (small)", 'green', 12, step=4),
              stext(380, 272, 't = difference / SE(difference): large overlap of the curves, but 600 students make the SE small', 'cyan', 12, step=3),
              stext(380, 296, 'same method effect on the FINAL score: p = 0.600 — diluted by attendance, study hours and noise', 'red', 12, step=5)]
    return anim(canvas(760, 310, *elems), [
        'The two groups\' post-test scores overlap heavily.',
        'Their means differ by 3.45 marks.',
        'The t statistic divides that difference by its standard error. Variances are similar (Levene p = 0.47), so Student and Welch agree; Welch is the safe default.',
        'Report the effect: the difference with a 95 % CI and Cohen\'s d.',
        'An effect on one outcome can be invisible on a noisier downstream outcome.',
    ])


def paired_anim():
    import random
    rng = random.Random(3)
    elems = [stext(380, 24, 'Paired t-test: each student compared with themselves', 'blue', 15, bold=True),
             stext(90, 54, 'pre-test', 'gray', 12, step=1, bold=True), stext(290, 54, 'post-test', 'green', 12, step=1, bold=True)]
    sy = lambda v: 260 - (v - 25) * 2.6
    for i in range(14):
        pre = rng.gauss(52, 11)
        post = pre + rng.gauss(7.7, 7)
        elems += [_dot(90, sy(pre), 'gray', step=1, r=4), _dot(290, sy(post), 'green', step=1, r=4),
                  f'<line x1="90" y1="{sy(pre):.0f}" x2="290" y2="{sy(post):.0f}" stroke="{"#10b981" if post > pre else "#ef4444"}" stroke-width="1.5" data-step="2"/>']
    elems += [stext(190, 280, 'lines = each student\'s change', 'gray', 11, step=2),
              stable(380, 55, ['', 'value'], [['pre mean (SD)', '52.49 (10.68)'], ['post mean (SD)', '60.16 (12.83)'], ['corr(pre, post)', '0.813'], ['mean gain (SD)', '7.67 (7.47)']],
                     [140, 120], step=3, title='600 students (real run)', title_color='green', focus_rows={2: '3'}),
              stable(380, 205, ['test', 'SE', 't'], [['paired ✓', '0.305', '25.14'], ['independent ✗', '0.681', '11.25']], [120, 70, 70], step=4,
                     title='same data, two tests', title_color='amber', focus_rows={0: '4'}),
              stext(570, 300, '20 students: paired p = 4.6e-06 vs independent p = 0.013', 'cyan', 12, step=5),
              stext(570, 320, 'mean gain 7.67, 95 % CI [7.07, 8.27]', 'green', 12, step=5, bold=True)]
    return anim(canvas(760, 335, *elems), [
        'Every student has a pre-test and a post-test score.',
        'The paired test works on each student\'s difference, removing the large differences between students.',
        'Pre and post scores are strongly correlated, so the SD of the differences (7.47) is much smaller than the SD of the scores.',
        'Treating the data as two independent groups doubles the SE and wastes that information.',
        'The advantage is largest for small samples. Report the mean gain with its CI.',
    ])


def tails_anim():
    f = _npdf(0, 1)
    elems = [stext(380, 24, 'Two-tailed vs one-tailed: where does α go?', 'blue', 15, bold=True)]
    for j, (title, areas, crit, st) in enumerate([('two-tailed: α/2 in each tail (±1.96)', [(-4, -1.96), (1.96, 4)], [-1.96, 1.96], 1),
                                                 ('one-tailed "smaller": all α left (−1.645)', [(-4, -1.645)], [-1.645], 2)]):
        X = 20 + j * 370
        W, H, Y = 340, 150, 60
        sx = lambda z, X=X, W=W: X + W * (z + 4) / 8
        elems += [stext(X + W / 2, 50, title, 'amber', 12, step=st, bold=True), _curve(f, -4, 4, X, Y, W, H, 0.42, 'blue', step=st)]
        for a0, a1 in areas:
            elems.append(_area(f, -4, 4, a0, a1, X, Y, W, H, 0.42, 'red', step=st))
        elems.append(f'<line x1="{X}" y1="{Y + H}" x2="{X + W}" y2="{Y + H}" stroke="#64748b" data-step="{st}"/>')
        elems.append(f'<line x1="{sx(-2.333):.0f}" y1="{Y + 40}" x2="{sx(-2.333):.0f}" y2="{Y + H}" stroke="#f59e0b" stroke-width="3" data-step="3"/>')
        elems.append(stext(sx(-2.333), Y + 34, 'z = −2.333', 'amber', 10, step=3))
    elems += [stable(30, 240, ['H₁ (placement rate vs 40 %)', 'p'], [['≠ 40 % (two-sided)', '0.0196'], ['< 40 % (smaller)', '0.0098'], ['exact binomial, less', '0.0106'],
                                                                    ['> 40 % (wrong direction)', '0.9902']], [210, 80], step=3, title='212 of 600 placed (35.3 %)',
                     title_color='amber', focus_rows={3: '4'}),
              stext(560, 260, 'wrong-direction one-tailed test can never', 'red', 12, step=4), stext(560, 278, 'detect the real drop (p = 0.99)', 'red', 12, step=4),
              stext(560, 315, 'Kharghar 42.9 % vs others 30.6 %:', 'cyan', 12, step=5), stext(560, 333, 'z = 3.051, p = 0.0023 (two-proportion z-test)', 'cyan', 12, step=5),
              stext(560, 360, 'choose the tail BEFORE seeing the data', 'green', 12, step=5, bold=True)]
    return anim(canvas(760, 380, *elems), [
        'A two-tailed test splits α between both tails: it can detect a change in either direction.',
        'A one-tailed test puts all of α on one side, so its cut-off is closer to 0 (1.645).',
        'The placement rate is 2.33 standard errors below the 40 % target; the one-sided p is half the two-sided one.',
        'Testing the wrong direction makes the real effect invisible.',
        'Proportion tests compare a rate with a target or two rates with each other.',
    ])


# ============================================================ section 6
def chi_anim():
    obs = [[132, 60], [132, 99], [124, 53]]
    exp_ = [[124.2, 67.8], [149.4, 81.6], [114.5, 62.5]]
    res = [[0.70, -0.95], [-1.42, 1.92], [0.89, -1.21]]
    rows = ['Juhu', 'Kharghar', 'Pune']
    elems = [stext(380, 24, 'Chi-square test of independence: centre × placed', 'blue', 15, bold=True),
             stable(20, 60, ['centre', 'not', 'placed'], [[r] + [str(v) for v in o] for r, o in zip(rows, obs)], [90, 60, 60], step=1, title='observed counts', title_color='blue'),
             stable(270, 60, ['centre', 'not', 'placed'], [[r] + [f'{v}' for v in e] for r, e in zip(rows, exp_)], [90, 60, 60], step=2, title='expected if independent',
                    title_color='purple'),
             stable(520, 60, ['centre', 'not', 'placed'], [[r] + [f'{v:+.2f}' for v in rr] for r, rr in zip(rows, res)], [90, 60, 60], step=4, title='(O − E) / √E',
                    title_color='amber', focus_rows={1: '4'}),
             stext(380, 190, 'E = row total × column total ÷ 600 · e.g. Kharghar placed: 231 × 212 / 600 = 81.6', 'purple', 12, step=2),
             stext(380, 220, 'χ² = Σ (O − E)² / E = 9.374 · df = (3 − 1)(2 − 1) = 2 · p = 0.0092', 'green', 14, step=3, bold=True),
             stext(380, 250, 'Kharghar placed cell: 99 observed vs 81.6 expected (residual +1.92) drives the result', 'amber', 12, step=4),
             stext(380, 280, "Cramér's V = 0.125 (weak association) · goodness of fit, course mix vs plan: χ² = 4.555, p = 0.103", 'cyan', 12, step=5),
             stext(380, 302, 'use counts, not percentages · expected counts ≥ 5, else Fisher\'s exact test', 'gray', 12, step=5)]
    return anim(canvas(760, 318, *elems), [
        'Start from the table of observed counts.',
        'If centre and placement were independent, each centre would get placements in proportion to its size: the expected counts.',
        'The chi-square statistic sums the squared gaps relative to the expected counts; with 2 degrees of freedom p = 0.009.',
        'Standardised residuals show where the gap is: Kharghar has more placements than expected.',
        'Report the strength (Cramér\'s V) too: the association is real but weak.',
    ])


def anova_anim():
    import random
    rng = random.Random(8)
    elems = [stext(380, 24, 'One-way ANOVA: between-group vs within-group variation', 'blue', 15, bold=True)]
    sx = lambda v: 60 + (v - 30) * 7
    centres = [('Juhu', 58.03, 10.50, 'blue'), ('Kharghar', 59.05, 10.72, 'amber'), ('Pune', 59.05, 9.88, 'green')]
    for i, (c, m, sd, col) in enumerate(centres):
        y = 70 + i * 50
        elems.append(stext(30, y + 4, c, col, 11, step=1, anchor='start'))
        for _ in range(28):
            elems.append(_dot(sx(rng.gauss(m, sd)), y + rng.uniform(-8, 8), col, step=1, r=3))
        elems.append(f'<line x1="{sx(m):.0f}" y1="{y - 16}" x2="{sx(m):.0f}" y2="{y + 16}" stroke="#e2e8f0" stroke-width="3" data-step="2"/>')
        elems.append(f'<line x1="{sx(m - sd):.0f}" y1="{y + 20}" x2="{sx(m + sd):.0f}" y2="{y + 20}" stroke="{PALETTE[col]}" stroke-width="2" data-step="3"/>')
    elems += [f'<line x1="{sx(58.72):.0f}" y1="50" x2="{sx(58.72):.0f}" y2="200" stroke="#ef4444" stroke-dasharray="4,3" data-step="2"/>',
              stext(sx(58.72), 215, 'grand mean 58.72', 'red', 10, step=2),
              stable(500, 55, ['source', 'SS', 'df'], [['between centres', '134.0', '2'], ['within centres', '64,685.1', '597']], [120, 80, 40], step=4,
                     title='decomposition (real run)', title_color='amber'),
              stext(620, 160, 'F = (134.0/2) / (64,685.1/597) = 0.618', 'green', 12, step=4, bold=True),
              stext(620, 182, 'p = 0.539 · η² = 0.0021', 'green', 12, step=4),
              stext(380, 250, 'means differ by ~1 mark, students within a centre by ±10 → no evidence of a centre effect', 'amber', 12, step=4),
              stext(380, 278, 'if significant → Tukey HSD for pairs (course: all p > 0.5) · Levene p = 0.535 (equal variances OK)', 'cyan', 12, step=5),
              stext(380, 300, 'ANOVA = regression on group dummies: anova_lm(ols("final_score ~ C(course)")) → F = 0.800, p = 0.450', 'purple', 12, step=5)]
    return anim(canvas(760, 315, *elems), [
        'Final scores of students in three centres.',
        'Between-group variation: how far the centre means are from the grand mean.',
        'Within-group variation: how much students differ inside each centre.',
        'F compares the two. Here the centre means are almost identical relative to the spread inside centres, so F is small and η² tiny.',
        'Only a significant ANOVA is followed by post-hoc comparisons; ANOVA is a special case of regression.',
    ])


def rank_anim():
    elems = [stext(380, 24, 'Rank-based (non-parametric) tests ignore how extreme a value is', 'blue', 15, bold=True)]
    vals = [5, 50, 7, 6]
    ranks = [1, 4, 3, 2]
    for i, (v, r) in enumerate(zip(vals, ranks)):
        x = 60 + i * 80
        elems += [scell(x, 60, 70, 34, f'{v} LPA', '#1e293b', step=1, bold=(v == 50)),
                  sarrow(x + 35, 96, x + 35, 120, 'gray', step=2),
                  scell(x, 122, 70, 34, f'rank {r}', '#065f46' if v != 50 else '#7c2d12', step=2, bold=True)]
    elems += [stext(205, 182, '50 LPA becomes simply rank 4: its size no longer matters', 'amber', 11, step=2),
              stable(400, 55, ['parametric', 'rank-based'], [['independent t-test', 'Mann-Whitney U'], ['paired t-test', 'Wilcoxon signed-rank'], ['one-way ANOVA', 'Kruskal-Wallis'],
                                                           ['Pearson r', 'Spearman ρ']], [160, 170], step=3, title='equivalents', title_color='purple'),
              stable(60, 210, ['packages: Kharghar vs others', 'Welch t p', 'Mann-Whitney p'], [['real data', '0.0140', '0.0381'], ['+ one 60 LPA offer to "others"', '0.4511', '0.0512']],
                     [220, 90, 120], step=4, title='one outlier (real run)', title_color='red', focus_rows={1: '4'}),
              stext(380, 312, 'Wilcoxon post vs pre p = 4.8e-72 · Kruskal packages by centre p = 0.024 (ANOVA 0.019) · report medians & IQR', 'cyan', 12, step=5)]
    return anim(canvas(760, 328, *elems), [
        'Start from the raw values, including an extreme one.',
        'Replace every value by its rank: the extreme value becomes just the largest rank.',
        'Each common parametric test has a rank-based counterpart.',
        'A single 60 LPA offer in the other group wipes out the t-test result (p 0.014 → 0.45); the rank test barely moves.',
        'Rank tests suit skewed data, outliers and ordinal scales; report medians with them.',
    ])


def multi_anim():
    import random
    rng = random.Random(4)
    elems = [stext(380, 24, 'Multiple testing: 20 tests on noise → expect about one "discovery"', 'blue', 15, bold=True)]
    for i in range(20):
        r, c = divmod(i, 10)
        x, y = 40 + c * 38, 60 + r * 40
        hit = i == 13
        elems.append(scell(x, y, 34, 32, 'p<.05' if hit else 'n.s.', '#7c2d12' if hit else '#1e293b', step=1, bold=hit, size=10))
    elems += [stext(230, 160, 'one false positive among 20 noise variables', 'red', 11, step=1)]
    import math
    X, Y, W, H = 470, 55, 260, 120
    elems += [_axes(X, Y, W, H, '', '', step=2), _curve(lambda m: 1 - 0.95 ** m, 0, 60, X, Y, W, H, 1.0, 'red', step=2),
              stext(X + W / 2, Y + H + 16, 'number of tests', 'gray', 10, step=2),
              stext(X + 10, Y - 4, 'P(≥ 1 false positive) = 1 − 0.95^m', 'red', 11, step=2, anchor='start'),
              _dot(X + W * 20 / 60, Y + H - H * 0.642, 'amber', step=2), stext(X + W * 20 / 60 + 8, Y + H - H * 0.642 + 14, '20 tests: 64 %', 'amber', 11, step=2, anchor='start'),
              stext(380, 210, 'simulation: 637 of 1,000 analysts testing 20 noise variables found at least one "effect"', 'amber', 12, step=3),
              stable(60, 248, ['method', 'controls', 'found (3 real effects)'], [['raw p < 0.05', 'nothing', '17, 18, 19'], ['Bonferroni α/m', 'FWER', '17, 19'],
                                                                              ['Holm', 'FWER (more power)', '17, 19'], ['Benjamini-Hochberg', 'FDR', '17, 19']],
                     [170, 150, 160], step=4, title='real run: 17 noise + 3 real attributes', title_color='green'),
              stext(620, 300, 'corrections cost power:', 'cyan', 12, step=5), stext(620, 320, 'the weakest real effect (18) is lost', 'cyan', 12, step=5),
              stext(620, 350, 'count every test you ran', 'green', 12, step=5, bold=True)]
    return anim(canvas(760, 385, *elems), [
        'With α = 0.05, each test on pure noise has a 1-in-20 chance of looking significant.',
        'The chance of at least one false positive grows quickly with the number of tests.',
        'A simulation of 1,000 analysts confirms it: almost two thirds "discover" something in noise.',
        'Corrections raise the bar: Bonferroni and Holm control the family-wise error rate, Benjamini-Hochberg the false discovery rate.',
        'The price is power; pre-registering a primary hypothesis avoids the problem.',
    ])


def effect_anim():
    sx = lambda v: 300 + v * 28
    elems = [stext(380, 24, 'Significant is not the same as important', 'blue', 15, bold=True),
             f'<line x1="{sx(0)}" y1="50" x2="{sx(0)}" y2="230" stroke="#94a3b8" data-step="1"/>', stext(sx(0), 246, '0', 'gray', 10, step=1),
             f'<line x1="{sx(2)}" y1="50" x2="{sx(2)}" y2="230" stroke="#f59e0b" stroke-dasharray="6,4" data-step="1"/>',
             stext(sx(2) + 6, 50, 'smallest important difference: 2 marks', 'amber', 11, step=1, anchor='start')]
    for v in [-2, 4, 6, 8, 10, 12]:
        elems.append(stext(sx(v), 246, str(v), 'gray', 10, step=1))
    rows = [('huge n, tiny effect', 0.41, 0.32, 0.50, 'd 0.04 · p 4e-20', 'red', 2), ('20 per group, big effect', 5.72, -1.55, 13.0, 'd 0.50 · p 0.12', 'amber', 3),
            ('200 per group, big effect', 5.08, 3.16, 7.0, 'd 0.52 · p 3e-07', 'green', 4)]
    for i, (lab, est, lo, hi, txt, col, st) in enumerate(rows):
        y = 80 + i * 55
        elems += [stext(20, y + 4, lab, col, 12, step=st, anchor='start', bold=True),
                  f'<line x1="{sx(lo):.0f}" y1="{y}" x2="{sx(hi):.0f}" y2="{y}" stroke="{PALETTE[col]}" stroke-width="4" data-step="{st}"/>',
                  _dot(sx(est), y, col, step=st, r=6), stext(20, y + 22, txt, 'gray', 11, step=st, anchor='start')]
    ps = ['0.001', '0.155', '0.041', '0.272', '0.027', '0.699', '0.000', '0.179', '0.014', '0.001']
    for i, pv in enumerate(ps):
        elems.append(scell(40 + i * 68, 268, 64, 28, pv, '#065f46' if float(pv) < 0.05 else '#334155', step=5, size=11))
    elems += [stext(380, 316, '10 replications of the same true effect (d = 0.3, n = 100): p jumps from 0.000 to 0.699', 'cyan', 12, step=5)]
    return anim(canvas(760, 330, *elems), [
        'Decide first which difference would matter in practice: here 2 marks.',
        'With 100,000 students per group, a 0.4-mark difference is extremely "significant" but the whole CI lies far below 2 marks: unimportant.',
        'With 20 per group, a large difference is "not significant": the CI is wide and includes both 0 and big effects. Inconclusive, not "no effect".',
        'With 200 per group, the same large effect is estimated precisely and clearly exceeds the important threshold.',
        'p-values bounce around between replications; effect sizes with CIs carry the real information.',
    ])



# ============================================================ section 7
def _scatter(X, Y, W, H, pts, color, step, r=3):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    out = [f'<rect x="{X}" y="{Y}" width="{W}" height="{H}" fill="none" stroke="#475569" data-step="{step}"/>']
    for x, y in pts:
        out.append(_dot(X + 8 + (W - 16) * (x - x0) / ((x1 - x0) or 1), Y + H - 8 - (H - 16) * (y - y0) / ((y1 - y0) or 1), color, step=step, r=r))
    return ''.join(out)


def corr_anim():
    import random, math
    rng = random.Random(7)
    lin = [(x, 0.66 * x + rng.gauss(0, 0.75)) for x in [rng.gauss(0, 1) for _ in range(60)]]
    u = [(x, x * x + rng.gauss(0, 0.3)) for x in [rng.uniform(-3, 3) for _ in range(50)]]
    ex = [(x, math.exp(x)) for x in range(1, 11)]
    out = [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(30)] + [(10, 10)]
    panels = [('study hours vs final', lin, 'blue', 'Pearson 0.664 · Spearman 0.650', 1),
              ('U-shape y = x²', u, 'amber', 'Pearson −0.000 · Spearman −0.007', 2),
              ('monotonic y = eˣ', ex, 'green', 'Pearson 0.717 · Spearman 1.000', 3),
              ('noise + one outlier', out, 'red', 'Pearson −0.16 → 0.78 · Spearman 0.03', 4)]
    elems = [stext(380, 24, 'Correlation measures a straight-line (Pearson) or monotonic (Spearman) relationship', 'blue', 14, bold=True)]
    for i, (t, pts, col, lab, st) in enumerate(panels):
        X = 15 + i * 187
        elems += [stext(X + 85, 52, t, col, 11, step=st, bold=True), _scatter(X, 60, 170, 150, pts, col, st), stext(X + 85, 228, lab, 'gray', 10, step=st)]
    elems += [stext(380, 260, 'r² = share of variance explained by a line: study hours alone explain 0.664² ≈ 44 % of final-score variance', 'cyan', 12, step=5),
              stext(380, 284, 'r ≈ 0 does not mean "no relationship" · one outlier can manufacture r · always plot first', 'red', 12, step=5)]
    return anim(canvas(760, 298, *elems), [
        'A linear relationship: Pearson and Spearman agree.',
        'A strong but U-shaped relationship has Pearson r of zero: correlation only sees straight lines.',
        'A curved but always-increasing relationship: Spearman (ranks) is a perfect 1, Pearson is lower.',
        'Thirty unrelated points plus one extreme point: Pearson jumps to 0.78, Spearman is not fooled.',
        'Interpret r² as variance explained, and always look at the scatter plot.',
    ])


def confound_anim():
    elems = [stext(380, 24, 'A confounder creates a correlation without causation', 'blue', 15, bold=True),
             sbox(290, 50, 180, 50, 'study hours', 'confounder', 'amber', step=2, size=13),
             sbox(60, 170, 180, 50, 'library visits', '', 'blue', step=1, size=13),
             sbox(520, 170, 180, 50, 'final score', '', 'green', step=1, size=13),
             sarrow(240, 195, 518, 195, 'red', step=1, dashed=True), stext(380, 186, 'r = 0.600 (p = 7e-60)', 'red', 12, step=1, bold=True),
             sarrow(330, 100, 170, 168, 'amber', step=2), sarrow(430, 100, 590, 168, 'amber', step=2),
             stext(215, 130, 'drives visits', 'amber', 11, step=2), stext(545, 130, 'drives scores', 'amber', 11, step=2),
             stable(110, 240, ['analysis', 'library effect'], [['correlation', 'r = 0.600'], ['partial r | study hours', '0.080 (p = 0.05)'],
                                                               ['regression slope alone', '1.592 marks/visit'], ['slope + study hours', '0.308']], [200, 160], step=3,
                    title='real run', title_color='green', focus_rows={1: '3', 3: '3'}),
             stext(600, 260, 'adjust: stratify, partial correlation,', 'cyan', 12, step=4), stext(600, 278, 'or include the confounder in a regression', 'cyan', 12, step=4),
             stext(600, 316, 'only randomisation removes', 'green', 12, step=5, bold=True), stext(600, 334, 'unmeasured confounders too', 'green', 12, step=5, bold=True)]
    return anim(canvas(760, 380, *elems), [
        'Library visits and final scores are strongly correlated.',
        'But both are driven by a third variable: students who study more visit the library more and score more.',
        'Holding study hours fixed, the link almost disappears: the partial correlation is 0.08 and the slope falls from 1.59 to 0.31.',
        'Adjustment removes the effect of confounders you measured.',
        'Randomised experiments also balance the confounders you did not measure.',
    ])


def ols_anim():
    import random
    rng = random.Random(10)
    X, Y, W, H = 50, 50, 420, 230
    sx = lambda v: X + W * v / 26
    sy = lambda v: Y + H - H * (v - 25) / 70
    pts = []
    for _ in range(45):
        h = min(25, max(1, rng.gammavariate(4, 2.2)))
        pts.append((h, 44.95 + 1.597 * h + rng.gauss(0, 7.8)))
    elems = [stext(380, 24, 'Least squares: the line that minimises squared residuals', 'blue', 15, bold=True), _axes(X, Y, W, H, '', 'final score', step=1),
             stext(X + W / 2, Y + H + 30, 'weekly study hours', 'gray', 11, step=1)]
    for v in [0, 5, 10, 15, 20, 25]:
        elems.append(stext(sx(v), Y + H + 14, str(v), 'gray', 10, step=1))
    line = lambda h: 44.95 + 1.597 * h
    for h, v in pts:
        elems.append(_dot(sx(h), sy(v), 'blue', step=1, r=3.5))
        elems.append(f'<line x1="{sx(h):.1f}" y1="{sy(v):.1f}" x2="{sx(h):.1f}" y2="{sy(line(h)):.1f}" stroke="#ef4444" stroke-width="1" data-step="3"/>')
    pi = 15.3
    elems += [f'<path d="M {sx(0)} {sy(line(0) + pi):.1f} L {sx(26)} {sy(line(26) + pi):.1f} L {sx(26)} {sy(line(26) - pi):.1f} L {sx(0)} {sy(line(0) - pi):.1f} Z" '
              f'fill="#8b5cf6" fill-opacity="0.15" data-step="5"/>',
              f'<line x1="{sx(0)}" y1="{sy(line(0)):.1f}" x2="{sx(26)}" y2="{sy(line(26)):.1f}" stroke="#f59e0b" stroke-width="3" data-step="2"/>',
              stext(sx(17), sy(line(26)) + 4, 'ŷ = 44.95 + 1.597 · hours', 'amber', 12, step=2, bold=True),
              stable(490, 55, ['', 'estimate', '95 % CI'], [['intercept', '44.95', '[43.55, 46.34]'], ['slope', '1.597', '[1.452, 1.741]']], [80, 65, 110], step=2,
                     title='statsmodels (real run)', title_color='amber'),
              stext(615, 150, 'red = residuals; OLS minimises Σ residual²', 'red', 11, step=3),
              stext(615, 175, 'R² = 0.441 = r² · residual SD 7.78', 'green', 12, step=4, bold=True),
              stable(490, 215, ['hours', 'mean CI', 'prediction PI'], [['4', '[50.42, 52.25]', '[36.02, 66.64]'], ['12', '[63.31, 64.89]', '[48.80, 79.41]']],
                     [50, 100, 105], step=5, title='predictions', title_color='purple', focus_rows={1: '5'})]
    return anim(canvas(760, 318, *elems), [
        'Each point is a student: weekly study hours against final score.',
        'OLS finds the line with slope cov(x, y)/var(x): each extra weekly hour is worth about 1.6 marks.',
        'Residuals are the vertical distances from the points to the line; the line minimises their squared sum.',
        'R² is the share of variance the line explains (44 %); the residual SD is the typical prediction error.',
        'The CI for the mean at 12 hours is narrow; the prediction interval for one student (purple band) is about ±15 marks.',
    ])


def multi_reg_anim():
    sx = lambda v: 330 + v * 120
    coefs = [('attendance (per %)', 0.306, 0.275, 0.336, 'blue'), ('study hours (per h)', 1.563, 1.472, 1.653, 'green'),
             ('post-test (per mark)', 0.368, 0.337, 0.398, 'purple'), ('Kharghar vs Juhu', 0.039, -0.898, 0.975, 'gray'), ('Pune vs Juhu', 2.169, 1.168, 3.169, 'amber')]
    elems = [stext(380, 24, 'Multiple regression: each effect holding the others constant', 'blue', 15, bold=True),
             f'<line x1="{sx(0)}" y1="45" x2="{sx(0)}" y2="235" stroke="#94a3b8" data-step="1"/>', stext(sx(0), 250, '0', 'gray', 10, step=1)]
    for v in [-1, 1, 2, 3]:
        elems.append(stext(sx(v), 250, str(v), 'gray', 10, step=1))
    elems.append(stext(380, 270, 'true values used to generate the data: 0.30 · 1.6 · 0.35 · Pune +2', 'gray', 11, step=3))
    for i, (lab, est, lo, hi, col) in enumerate(coefs):
        y = 60 + i * 38
        st = 1 if i < 3 else 2
        elems += [stext(sx(-1) - 12, y + 4, lab, col, 12, step=st, anchor='end'),
                  f'<line x1="{sx(lo):.0f}" y1="{y}" x2="{sx(hi):.0f}" y2="{y}" stroke="{PALETTE.get(col, col)}" stroke-width="4" data-step="{st}"/>',
                  _dot(sx(est), y, col, step=st, r=6), stext(sx(est), y - 10, f'{est:.3f}', col, 11, step=st)]
    elems += [stable(20, 300, ['model', 'R²', 'adj R²', 'AIC'], [['study_hours only', '0.441', '—', '4167.0'], ['+ attendance, post_test, centre', '0.782', '0.780', '3610.1'],
                                                              ['+ pure noise column', '0.7823 ↑', '0.7801 ↓', '—']], [230, 80, 80, 70], step=4, title='model comparison (real run)',
                     title_color='green', focus_rows={2: '4'}),
              stext(620, 330, 'nested F-test: F = 232.2, p ≈ 0', 'cyan', 12, step=4),
              stext(620, 365, 'raw centre means: Juhu 58.03 ·', 'amber', 12, step=5), stext(620, 383, 'Kharghar 59.05 · Pune 59.05', 'amber', 12, step=5),
              stext(620, 405, '→ Pune effect hidden until adjusted', 'amber', 12, step=5, bold=True)]
    return anim(canvas(760, 420, *elems), [
        'Each numeric coefficient is the change in final score per unit, with the other predictors held fixed; the bars are 95 % CIs.',
        'Categorical centre enters as dummies relative to the reference level (Juhu): Pune is worth +2.2 marks, Kharghar nothing.',
        'The estimates recover the true effects used to generate the data.',
        'R² always rises with extra predictors (even noise); adjusted R² and AIC penalise them. The nested F-test confirms the bigger model is better.',
        'The raw centre averages hide the Pune effect because other factors and noise mask it.',
    ])


def diag_anim():
    import random
    rng = random.Random(2)
    elems = [stext(380, 24, 'Regression diagnostics: check the residuals and the predictors', 'blue', 15, bold=True)]
    for j, (title, col, funnel, st) in enumerate([('residuals vs fitted: OK', 'green', False, 1), ('funnel = heteroscedasticity', 'red', True, 2)]):
        X = 20 + j * 250
        elems += [stext(X + 110, 52, title, col, 12, step=st, bold=True), _axes(X, 60, 220, 140, '', '', step=st),
                  f'<line x1="{X}" y1="130" x2="{X + 220}" y2="130" stroke="#64748b" stroke-dasharray="4,3" data-step="{st}"/>']
        for _ in range(60):
            u = rng.uniform(0, 1)
            sd = (6 + 50 * u) if funnel else 20
            elems.append(_dot(X + 10 + 200 * u, 130 + max(-65, min(65, rng.gauss(0, sd * 0.6))), col, step=st, r=3))
        elems.append(stext(X + 110, 218, 'Breusch-Pagan p = 0.775' if not funnel else 'Breusch-Pagan p = 2.3e-11', col, 11, step=st))
    elems += [stable(530, 55, ['predictor', 'VIF'], [['attendance', '1.00'], ['study_hours', '1.00'], ['post_test', '2.96'], ['pre_test', '2.95']], [120, 70], step=3,
                     title='multicollinearity', title_color='amber', focus_rows={2: '3', 3: '3'}),
              stext(620, 200, 'corr(pre, post) = 0.81', 'amber', 11, step=3),
              stext(620, 218, 'SE(post_test): 0.0158 → 0.0272', 'amber', 11, step=3, bold=True),
              stext(380, 250, 'LINE: Linearity · Independence (Durbin-Watson 2.139) · Normal errors (Jarque-Bera p = 0.582) · Equal variance', 'cyan', 12, step=4),
              stext(380, 274, "Cook's distance: max 0.025, 34 rows above 4/n → look at them, do not auto-delete", 'purple', 12, step=5),
              stext(380, 298, 'fixes: transform · add terms · robust HC3 SE · drop/merge collinear predictors · regularise', 'green', 12, step=5)]
    return anim(canvas(760, 312, *elems), [
        'Residuals should scatter randomly around zero with constant spread.',
        'A funnel means the error variance grows with the fitted value (heteroscedasticity): coefficients are fine, standard errors are not.',
        'Correlated predictors inflate each other\'s variance: adding pre-test makes the post-test coefficient much less precise.',
        'Check each LINE assumption with a plot or test.',
        'Find influential points, investigate them, and apply the matching remedy.',
    ])


# ============================================================ section 8
def ab_anim():
    elems = [stext(380, 24, 'A/B test: SMS reminder vs no reminder (on-time submission)', 'blue', 15, bold=True),
             _row([('plan', 'metric + min lift +5 pts', 'gray', 1), ('power analysis', '1,250 per group', 'purple', 1), ('randomise', 'coin flip per student', 'amber', 2),
                   ('run to n', 'no peeking', 'blue', 2), ('analyse once', 'z-test + lift CI', 'green', 3)], 50, x0=15, w=134, gap=17, h=56, size=12)]
    elems += [stable(30, 140, ['group', 'n', 'submitted', 'rate'], [['A (no SMS)', '1,250', '851', '68.1 %'], ['B (SMS)', '1,250', '946', '75.7 %']], [110, 70, 90, 70], step=3,
                     title='results (simulated run)', title_color='green'),
              stext(190, 240, 'sample ratio check p = 1.000 ✓ · z = 4.23 · p = 2e-05', 'cyan', 11, step=3)]
    sx = lambda v: 420 + v * 25
    elems += [f'<line x1="{sx(0)}" y1="150" x2="{sx(0)}" y2="230" stroke="#94a3b8" data-step="4"/>', stext(sx(0), 246, '0', 'gray', 10, step=4),
              f'<line x1="{sx(5)}" y1="150" x2="{sx(5)}" y2="230" stroke="#f59e0b" stroke-dasharray="5,4" data-step="4"/>', stext(sx(5), 246, '+5 min', 'amber', 10, step=4),
              stext(sx(10), 246, '+10', 'gray', 10, step=4),
              f'<line x1="{sx(4.08):.0f}" y1="190" x2="{sx(11.10):.0f}" y2="190" stroke="#10b981" stroke-width="5" data-step="4"/>',
              _dot(sx(7.6), 190, 'green', step=4, r=7), stext(sx(7.6), 175, 'lift +7.6 pts, CI [+4.1, +11.1]', 'green', 12, step=4, bold=True),
              stext(380, 285, 'whole CI above 0 → ship · lower end below the +5 target → benefit could be smaller than hoped', 'amber', 12, step=5),
              stext(380, 308, 'randomisation balances every other factor · fixed n avoids the peeking problem', 'gray', 12, step=5)]
    return anim(canvas(760, 322, *elems), [
        'Fix the metric and the smallest lift worth acting on; the power analysis gives 1,250 submissions per group for 70 % → 75 %.',
        'Randomise students to A or B and run until the planned sample is reached.',
        'Compare the rates once, after checking that the split came out as planned.',
        'Estimate the lift with a confidence interval and compare it with the minimum worthwhile lift.',
        'Decide with the interval and the cost of the reminder in mind.',
    ])


def simpson_anim():
    elems = [stext(380, 24, "Simpson's paradox: better in every course, worse overall", 'blue', 15, bold=True)]
    def bars(X, title, vals, st):
        out = [stext(X + 90, 52, title, 'gray', 12, step=st, bold=True), f'<line x1="{X}" y1="220" x2="{X + 180}" y2="220" stroke="#64748b" data-step="{st}"/>']
        for i, (lab, v, col) in enumerate(vals):
            h = v * 150
            out += [f'<rect x="{X + 20 + i * 80}" y="{220 - h:.0f}" width="60" height="{h:.0f}" fill="{PALETTE[col]}" data-step="{st}"/>',
                    stext(X + 50 + i * 80, 214 - h, f'{v:.3f}' if v < 0.9 else f'{v:.1f}', col, 11, step=st, bold=True), stext(X + 50 + i * 80, 236, lab, 'gray', 11, step=st)]
        return out
    elems += bars(20, 'overall placement rate', [('North', 0.483, 'blue'), ('South', 0.717, 'amber')], 1)
    elems += bars(270, 'PG-DBDA students', [('North', 0.9, 'blue'), ('South', 0.8, 'amber')], 2)
    elems += bars(520, 'PG-DAC students', [('North', 0.4, 'blue'), ('South', 0.3, 'amber')], 2)
    elems += [stable(30, 262, ['centre', 'PG-DBDA', 'PG-DAC'], [['North', '50', '250'], ['South', '250', '50']], [90, 90, 90], step=3, title='who is enrolled (course mix)',
                     title_color='purple'),
              stext(560, 280, 'standardised to a common mix:', 'green', 12, step=4), stext(560, 300, 'North 0.65 vs South 0.55', 'green', 13, step=4, bold=True),
              stext(560, 335, 'logistic OR South vs North:', 'cyan', 12, step=5), stext(560, 355, '2.704 alone → 0.569 with course', 'cyan', 13, step=5, bold=True)]
    return anim(canvas(760, 375, *elems), [
        'Overall, South places 72 % of students and North only 48 %.',
        'Yet within each course, North places a higher share than South.',
        'The reason is the course mix: North mostly teaches PG-DAC, which places fewer students; South mostly PG-DBDA.',
        'Applying each centre\'s course rates to the same mix gives a fair comparison: North is better.',
        'A regression including course reverses the odds ratio. Which comparison is right depends on the question being asked.',
    ])


def survey_anim():
    X, Y, W, H = 50, 55, 360, 200
    f = lambda e: 1.96 ** 2 * 0.25 / (e / 100) ** 2 if e > 0 else 0
    sx = lambda e: X + W * (e - 1) / 9
    sy = lambda n: Y + H - H * min(n, 2000) / 2000
    elems = [stext(380, 24, 'Survey sample size: precision costs grow fast', 'blue', 15, bold=True), _axes(X, Y, W, H, '', 'n needed', step=1),
             stext(X + W / 2, Y + H + 30, 'margin of error (± percentage points)', 'gray', 11, step=1)]
    d = 'M ' + ' L '.join(f'{sx(e):.1f} {sy(f(e)):.1f}' for e in [2 + k * 0.1 for k in range(81)])
    elems.append(f'<path d="{d}" stroke="#0ea5e9" stroke-width="2.5" fill="none" data-step="1"/>')
    for e in [2, 4, 6, 8, 10]:
        elems.append(stext(sx(e), Y + H + 14, str(e), 'gray', 10, step=1))
    for e, n in [(3, 1068), (5, 385), (10, 97)]:
        elems += [_dot(sx(e), sy(n), 'amber', step=2, r=5), stext(sx(e) + (8 if e < 10 else -8), sy(n) - 10, f'±{e}: {n}', 'amber', 11, step=2, anchor='start' if e < 10 else 'end')]
    elems += [stext(230, 300, 'n = 1.96² · p(1−p) / E², worst case p = 0.5 · ±1 % needs 9,604', 'cyan', 11, step=2),
              stable(450, 55, ['population', 'n for ±5 %'], [['300', '169'], ['600', '235'], ['5,000', '357'], ['1,000,000', '384']], [130, 110], step=3,
                     title='finite population correction', title_color='purple'),
              stable(450, 205, ['centre', 'need', 'invite (60 %)'], [['Kharghar', '145', '242'], ['Juhu', '129', '215'], ['Pune', '122', '204']], [100, 60, 110], step=4,
                     title='±5 % per centre', title_color='green'),
              stext(380, 335, 'simulation: n = 385 lands within ±5 points 94.7 % of the time · response bias is not fixed by a larger n', 'red', 12, step=5)]
    return anim(canvas(760, 350, *elems), [
        'The required sample grows with the square of the precision: halving the margin needs four times the responses.',
        '±5 points at 95 % confidence needs 385 responses from a large population; ±3 points needs 1,068.',
        'For small populations, the finite population correction reduces the requirement sharply.',
        'Reporting each centre separately needs the sample in each centre, then inflating for the response rate.',
        'Simulation confirms the margin; non-response bias needs a different fix (follow-ups, weighting).',
    ])


def rater_anim():
    import random
    rng = random.Random(5)
    sx = lambda v: 60 + (v - 40) * 6
    elems = [stext(380, 24, 'Is evaluator C harsher? Compare, moderate, rescale', 'blue', 15, bold=True)]
    for i, (e, m, sd, col) in enumerate([('A', 67.42, 9.72, 'blue'), ('B', 68.75, 8.12, 'green'), ('C', 64.72, 9.12, 'red')]):
        y = 70 + i * 45
        elems.append(stext(35, y + 4, f'evaluator {e}', col, 11, step=1, anchor='start'))
        for _ in range(25):
            elems.append(_dot(sx(rng.gauss(m, sd)) + 50, y + rng.uniform(-8, 8), col, step=1, r=3))
        elems.append(f'<line x1="{sx(m) + 50:.0f}" y1="{y - 15}" x2="{sx(m) + 50:.0f}" y2="{y + 15}" stroke="#e2e8f0" stroke-width="3" data-step="1"/>')
    elems += [stext(250, 215, 'means 67.4 · 68.8 · 64.7 → ANOVA p = 0.13: cannot separate severity from batch quality', 'amber', 11, step=2),
              stable(490, 55, ['moderation (15 reports of C)', 'value'], [['C − moderator, same reports', '−6.67 marks'], ['paired t-test p', '0.0001']], [170, 85], step=3,
                     title='paired design', title_color='green'),
              stable(500, 160, ['evaluator', 'raw', 'scaled'], [['A', '67.42', '66.97'], ['B', '68.75', '66.97'], ['C', '64.72', '66.97']], [90, 80, 80], step=4,
                     title='z-score scaling', title_color='purple'),
              stext(380, 290, 'correlation with true quality: raw 0.874 → scaled 0.920 · ranks inside each batch unchanged', 'cyan', 12, step=5),
              stext(380, 312, 'valid only with random allocation of reports to evaluators', 'red', 12, step=5)]
    return anim(canvas(760, 326, *elems), [
        'Reports were randomly allocated to three evaluators; C\'s marks look lower.',
        'Comparing different reports, ANOVA cannot separate a 4-mark difference from natural variation in report quality.',
        'A moderator re-marks some of C\'s reports: on the same reports, C is almost 7 marks harsher, highly significant.',
        'Scaling each evaluator\'s marks to a common mean and SD removes the severity.',
        'Scaled marks track the true quality better; the method relies on comparable batches.',
    ])


def control_anim():
    rates = [0.822, 0.861, 0.839, 0.822, 0.839, 0.850, 0.833, 0.833, 0.856, 0.844, 0.833, 0.889, 0.689, 0.872, 0.839, 0.800, 0.867, 0.856, 0.817, 0.844]
    X, Y, W, H = 60, 50, 640, 220
    sx = lambda w: X + W * (w - 0.5) / 20
    sy = lambda v: Y + H - H * (v - 0.65) / 0.3
    elems = [stext(380, 24, 'p-chart: weekly attendance rate (180 enrolled)', 'blue', 15, bold=True),
             _axes(X, Y, W, H, '', 'attendance rate', step=1), stext(X + W / 2, Y + H + 30, 'week', 'gray', 11, step=1)]
    for w in range(1, 21):
        elems.append(stext(sx(w), Y + H + 14, str(w), 'gray', 9, step=1))
    for v, lab, col, st, dash in [(0.840, 'CL 0.840', 'green', 2, ''), (0.922, 'UCL 0.922', 'red', 3, '6,4'), (0.758, 'LCL 0.758', 'red', 3, '6,4'),
                                  (0.895, '2σ 0.895', 'amber', 4, '2,3'), (0.785, '2σ 0.785', 'amber', 4, '2,3')]:
        elems.append(f'<line x1="{X}" y1="{sy(v):.1f}" x2="{X + W}" y2="{sy(v):.1f}" stroke="{PALETTE[col]}" stroke-width="1.5" stroke-dasharray="{dash}" data-step="{st}"/>')
        elems.append(stext(X + W + 4, sy(v) + 4, lab, col, 10, step=st, anchor='start'))
    d = 'M ' + ' L '.join(f'{sx(i + 1):.1f} {sy(v):.1f}' for i, v in enumerate(rates))
    elems.append(f'<path d="{d}" stroke="#0ea5e9" stroke-width="2" fill="none" data-step="1"/>')
    for i, v in enumerate(rates):
        elems.append(_dot(sx(i + 1), sy(v), 'red' if v < 0.758 else 'blue', step=1 if v >= 0.758 else 4, r=5 if v < 0.758 else 4))
    elems += [f'<rect x="{X}" y="{Y}" width="{sx(10.5) - X:.0f}" height="{H}" fill="#10b981" fill-opacity="0.07" data-step="2"/>',
              stext((X + sx(10.5)) / 2, Y + 14, 'baseline weeks 1–10', 'green', 11, step=2),
              stext(sx(13) + 10, sy(0.689) + 4, 'week 13: 0.689 → special cause', 'red', 11, step=4, anchor='start', bold=True),
              stext(sx(16), sy(0.800) + 20, 'week 16: 0.800 → noise', 'gray', 10, step=5),
              stext(380, 322, 'limits = p̄ ± 3·√(p̄(1−p̄)/n) · false alarm per point 0.0027 · investigate signals, not every dip', 'cyan', 12, step=5)]
    return anim(canvas(760, 336, *elems), [
        'Plot the weekly attendance rate in time order.',
        'Compute the centre line from a stable baseline period.',
        'Control limits at ±3 standard errors mark the range of normal week-to-week variation.',
        'Week 13 falls below the lower limit: a special cause (a hackathon elsewhere) explains it.',
        'Week 16\'s dip to 80 % is inside the limits: normal variation that needs no action.',
    ])
