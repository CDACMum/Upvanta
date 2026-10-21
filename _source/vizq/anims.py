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





# ============================================================ recipe animations
# Left: the code, one line per step. Right: the chart being built layer by layer.
PX, PY, PW, PH = 420, 52, 320, 230          # right-hand drawing panel


def _r(x, y, w, h, fill, st, op=1, stroke='none'):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{PALETTE.get(fill, fill)}" fill-opacity="{op}" stroke="{stroke}" data-step="{st}"/>'


def _ln(x1, y1, x2, y2, col, st, w=2, dash=''):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{PALETTE.get(col, col)}" stroke-width="{w}"{d} data-step="{st}"/>'


def _pl(pts, col, st, w=2.5, fill='none', op=1):
    d = 'M ' + ' L '.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    f = f' fill="{PALETTE.get(fill, fill)}" fill-opacity="{op}"' if fill != 'none' else ' fill="none"'
    return f'<path d="{d}" stroke="{PALETTE.get(col, col)}" stroke-width="{w}"{f} data-step="{st}"/>'


def _frame(st=1, axes=True):
    out = _r(PX, PY, PW, PH, '#ffffff', st, op=0.04, stroke='#475569')
    if axes:
        out += _ln(PX + 30, PY + PH - 25, PX + PW - 10, PY + PH - 25, '#94a3b8', st, 1.5) + _ln(PX + 30, PY + 15, PX + 30, PY + PH - 25, '#94a3b8', st, 1.5)
    return out


def _recipe(title, code, draw, notes, h=338, code_w=385):
    """code: list of (line, step); draw: list of SVG strings; notes: 5 explanations."""
    elems = [stext(380, 24, title, 'blue', 15, bold=True), _codebox(15, 52, code_w, PH, [], 'gray', step=1)]
    for i, (line, st) in enumerate(code):
        elems.append(_lines(28, 78 + i * 19, [line], '#7dd3fc', 11, step=st))
    elems += draw
    return anim(canvas(760, h, *elems), notes)


def _bottom(text, st, color='cyan', y=302):
    return stext(380, y, text, color, 12, step=st)


# ------------------------------------------------------------ section 1
def anatomy_anim():
    d = [_r(PX, PY, PW, PH, '#0ea5e9', 1, op=0.06, stroke='#0ea5e9'), stext(PX + 8, PY + 16, 'Figure', 'blue', 12, anchor='start', step=1, bold=True),
         _r(PX + 25, PY + 30, PW - 45, PH - 60, '#10b981', 2, op=0.08, stroke='#10b981'), stext(PX + 33, PY + 46, 'Axes', 'green', 12, anchor='start', step=2, bold=True),
         _ln(PX + 45, PY + PH - 45, PX + PW - 30, PY + PH - 45, 'amber', 3, 2), _ln(PX + 45, PY + 55, PX + 45, PY + PH - 45, 'amber', 3, 2),
         stext(PX + PW - 60, PY + PH - 32, 'x Axis', 'amber', 11, step=3), stext(PX + 60, PY + 70, 'y Axis', 'amber', 11, anchor='start', step=3),
         _pl([(PX + 55, PY + 160), (PX + 120, PY + 130), (PX + 180, PY + 120), (PX + 250, PY + 85)], 'blue', 4),
         stext(PX + 230, PY + 115, 'Line2D (artist)', 'blue', 11, step=4),
         _bottom('everything drawn is an Artist · OO style names each object: fig, ax, line', 5)]
    code = [('fig, ax = plt.subplots()', 1), ('# fig holds one Axes', 2), ('ax.xaxis, ax.yaxis', 3), ('line, = ax.plot(x, y)', 4), ('ax.set(title=..., xlabel=...)', 5)]
    return _recipe('Anatomy of a figure', code, d, [
        'The Figure is the whole canvas.', 'An Axes is one plot area inside it; plt.subplots returns both.',
        'Each Axes has an x Axis and a y Axis that own the ticks and labels.', 'Plotting adds Artists (here a Line2D) to the Axes.',
        'Titles and labels are set on the Axes; the OO style keeps every object explicit.'])


def line_anim():
    pts = [(PX + 40 + i * 50, PY + 170 - v) for i, v in enumerate([10, 40, 60, 90, 110, 135])]
    pts2 = [(PX + 40 + i * 50, PY + 170 - v) for i, v in enumerate([25, 30, 40, 40, 55, 60])]
    d = [_frame(), _pl(pts, 'blue', 1), *[_dot(x, y, 'blue', step=1, r=4) for x, y in pts],
         _pl(pts2, 'amber', 2), *[_dot(x, y, 'amber', step=2, r=4) for x, y in pts2],
         _ln(PX + 30, PY + 120, PX + PW - 10, PY + 120, '#94a3b8', 3, 1.5, '5,4'), stext(PX + 40, PY + 134, 'target 60', 'gray', 10, anchor='start', step=3),
         stext(pts[-1][0] + 6, pts[-1][1] + 4, 'PG-DAI', 'blue', 10, anchor='start', step=4), stext(pts2[-1][0] + 6, pts2[-1][1] + 4, 'PG-DAC', 'amber', 10, anchor='start', step=4),
         _bottom('order matters on x · label lines directly · ≤ 5 lines per chart', 5)]
    code = [("ax.plot(months, a, marker='o')", 1), ("ax.plot(months, b, marker='s')", 2), ("ax.axhline(60, linestyle='--')", 3),
            ('ax.annotate(name, (x, y))', 4), ('ax.spines[[...]].set_visible(False)', 5)]
    return _recipe('Building a line chart', code, d, [
        'Plot each series against ordered x values; markers show the actual data points.', 'Add the second series on the same axes.',
        'A reference line gives the trend a meaning: above or below the target.', 'Direct labels at the line ends replace the legend.',
        'Remove clutter; keep the number of lines small.'])


def bar_anim():
    vals = [('Pune', 30), ('Juhu', 31), ('Kharghar', 43)]
    d = [_frame()]
    for i, (n, v) in enumerate(vals):
        y = PY + 30 + i * 60
        d += [_r(PX + 30, y, v * 5.5, 38, 'blue' if n != 'Kharghar' else 'green', 1), stext(PX + 26, y + 24, n, 'gray', 10, anchor='end', step=1),
              stext(PX + 36 + v * 5.5, y + 24, f'{v}%', '#e2e8f0', 10, anchor='start', step=3)]
    d += [stext(PX + 170, PY + 22, 'sorted, horizontal, zero baseline', 'gray', 10, step=2),
          _bottom('grouped: offset x by bar width · stacked: bottom= · bar_label(...) for values', 4),
          _bottom('bars encode length → never truncate the value axis', 5, 'red', y=324)]
    code = [('rate = df.groupby(...).mean()', 1), ('rate = rate.sort_values()', 2), ('bars = ax.barh(rate.index, rate)', 2),
            ("ax.bar_label(bars, fmt='%.1f%%')", 3), ('ax.bar(x + i*w, ..., width=w)', 4), ('ax.set_xlim(0, ...)', 5)]
    return _recipe('Building a bar chart', code, d, [
        'Aggregate to one value per category.', 'Sort and draw horizontal bars from a zero baseline.', 'Label the values on the bars.',
        'Grouped bars offset each series; stacked bars use bottom=.', 'Bar length is the value, so the axis must start at zero.'])


def hist_anim():
    import math
    heights = [2, 6, 14, 24, 30, 26, 17, 9, 4, 1]
    d = [_frame()]
    for i, h in enumerate(heights):
        d.append(_r(PX + 40 + i * 27, PY + PH - 25 - h * 5.5, 25, h * 5.5, 'blue', 1))
    for i in range(5):
        hh = sum(heights[2 * i:2 * i + 2]) / 2
        d.append(_r(PX + 40 + i * 54, PY + PH - 25 - hh * 5.5, 52, hh * 5.5, 'amber', 2, op=0.35, stroke='#f59e0b'))
    d += [stext(PX + 250, PY + 30, '5 wide bins hide shape', 'amber', 10, step=2),
          _pl([(PX + 40 + i * 27 + 12, PY + PH - 25 - h * 5.5) for i, h in enumerate(heights)], 'green', 3),
          stext(PX + 250, PY + 48, 'density=True: area = 1', 'green', 10, step=3),
          _ln(PX + 40 + 4.6 * 27, PY + 20, PX + 40 + 4.6 * 27, PY + PH - 25, 'red', 4, 2, '4,3'), stext(PX + 40 + 4.6 * 27 + 4, PY + 70, 'median', 'red', 10, anchor='start', step=4),
          _bottom("Freedman-Diaconis chose 16 bins of width 3.54 for the final score · ax.ecdf for cumulative shares", 5)]
    code = [("ax.hist(x, bins=20)", 1), ("ax.hist(x, bins=5)  # too coarse", 2), ("ax.hist(x, density=True)", 3),
            ("ax.axvline(x.median())", 4), ("np.histogram(x, bins='fd')", 5)]
    return _recipe('Histograms: the bin width tells the story', code, d, [
        'Counts per bin show the shape of one numeric variable.', 'Too few bins merge the structure away; too many show noise.',
        'density=True scales bars to area 1, so groups of different size compare fairly.', 'Reference lines (median, pass mark) anchor the reading.',
        'Rules such as Freedman-Diaconis pick a sensible bin width automatically.'])


def scatter_anim():
    import random
    rng = random.Random(4)
    pts = []
    for _ in range(45):
        x = rng.uniform(0, 1); y = 0.15 + 0.6 * x + rng.gauss(0, 0.12)
        pts.append((x, y, rng.uniform(0, 1)))
    sx = lambda v: PX + 40 + v * 260
    sy = lambda v: PY + PH - 30 - v * 170
    d = [_frame()] + [_dot(sx(x), sy(y), 'gray', step=1, r=4) for x, y, c in pts]
    import colorsys
    for x, y, c in pts:
        r, g, b = colorsys.hsv_to_rgb(0.75 - 0.5 * c, 0.7, 0.85)
        d.append(_dot(sx(x), sy(y), f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}', step=2, r=4))
    d += [_ln(sx(0), sy(0.15), sx(1), sy(0.75), 'red', 3, 2.5), stext(sx(0.75), sy(0.82), '1.60 marks / hour', 'red', 10, step=3),
          *[_r(PX + PW - 22, PY + 30 + k * 15, 10, 15, c, 4) for k, c in enumerate(['#fde725', '#b5de2b', '#6ece58', '#35b779', '#1f9e89', '#26828e', '#31688e', '#3e4989', '#482878', '#440154'])],
          stext(PX + PW - 30, PY + 26, 'colorbar', 'gray', 9, anchor='end', step=4),
          _bottom('r = 0.664 · alpha / small markers against overplotting · one extra encoding at most', 5)]
    code = [('ax.scatter(hours, score, s=18)', 1), ("sc = ax.scatter(..., c=attendance, cmap='viridis')", 2),
            ('b, a = np.polyfit(x, y, 1); ax.plot(xs, a + b*xs)', 3), ("fig.colorbar(sc, label='attendance %')", 4), ('alpha=0.5, s=8 for many points', 5)]
    return _recipe('Scatter plots: relationships between two numbers', code, d, [
        'One mark per student: study hours against final score.', 'Colour encodes a third variable through a colormap.',
        'A fitted trend line summarises the direction and slope.', 'A colorbar is needed to decode the colours.',
        'Control overplotting and keep extra encodings to a minimum.'])


# ------------------------------------------------------------ section 2
def subplots_anim():
    d = [_r(PX, PY, PW, PH, '#0ea5e9', 1, op=0.05, stroke='#475569')]
    for i in range(3):
        d.append(_r(PX + 10 + i * 103, PY + 20, 95, 90, 'blue', 1, op=0.15, stroke='#0ea5e9'))
        d.append(stext(PX + 57 + i * 103, PY + 70, f'axes[{i}]', 'blue', 10, step=1))
    d += [_ln(PX + 10, PY + 20, PX + 310, PY + 20, 'amber', 2, 2, '4,3'), stext(PX + 160, PY + 15, 'sharey=True → same scale', 'amber', 10, step=2),
          _r(PX + 10, PY + 125, 200, 95, 'green', 3, op=0.15, stroke='#10b981'), stext(PX + 110, PY + 175, 'A (spans 2 cells)', 'green', 10, step=3),
          _r(PX + 215, PY + 125, 95, 95, 'purple', 3, op=0.15, stroke='#8b5cf6'), stext(PX + 262, PY + 175, 'B', 'purple', 10, step=3),
          stext(PX + 160, PY + 120, "subplot_mosaic('AAB')", 'green', 10, step=3),
          _bottom("layout='constrained' prevents overlapping labels · fig.suptitle for the whole figure", 4),
          _bottom('loop: for ax, (name, g) in zip(axes.flat, df.groupby(...))', 5, 'purple', y=324)]
    code = [('fig, axes = plt.subplots(1, 3)', 1), ('..., sharey=True', 2), ("fig, axd = plt.subplot_mosaic('AAB;CCB')", 3),
            ("..., layout='constrained'", 4), ('for ax, g in zip(axes.flat, groups):', 5)]
    return _recipe('Several plots in one figure', code, d, [
        'plt.subplots returns an array of Axes for a grid.', 'Shared axes make panels directly comparable.',
        'subplot_mosaic names panels with letters; repeating a letter makes a panel span cells.', 'A layout engine stops titles and labels colliding.',
        'Fill the panels in a loop over groups.'])


def ticks_anim():
    d = [_frame()]
    import math
    vals = [120, 260, 610, 1300, 2900, 5100, 9400, 15000]
    lin = [(PX + 40 + i * 37, PY + PH - 25 - v / 15000 * 180) for i, v in enumerate(vals)]
    log = [(PX + 40 + i * 37, PY + PH - 25 - (math.log10(v) - 2) / 2.3 * 180) for i, v in enumerate(vals)]
    d += [_pl(lin, 'blue', 1), stext(PX + 90, PY + 40, 'linear: early years flat', 'blue', 10, step=1),
          _pl(log, 'green', 2), stext(PX + 230, PY + 150, 'log: steady growth', 'green', 10, step=2),
          stext(PX + 18, PY + 70, '10k', 'gray', 9, step=3), stext(PX + 18, PY + 150, '1k', 'gray', 9, step=3),
          stext(PX + 160, PY + 22, 'FuncFormatter → "15k"', 'amber', 10, step=3),
          _bottom('PercentFormatter(1) · MultipleLocator(5) · ConciseDateFormatter', 4),
          _bottom('twinx: two arbitrary scales (careful) · secondary_xaxis: same data, other units', 5, 'red', y=324)]
    code = [("ax.plot(years, apps)", 1), ("ax.set_yscale('log')", 2), ('ax.yaxis.set_major_formatter(FuncFormatter(f))', 3),
            ('ax.yaxis.set_major_formatter(PercentFormatter(1))', 4), ('ax2 = ax.twinx()', 5)]
    return _recipe('Axes, scales and tick formats', code, d, [
        'On a linear axis, growth from 120 to 15,000 hides the early years.', 'A log axis turns constant percentage growth into a straight line.',
        'Formatters print ticks the way readers expect.', 'Locators and formatters control where ticks go and how they look.',
        'Secondary axes are safe for unit conversions, risky for unrelated variables.'])


def colour_anim():
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569')]
    cats = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    for i, c in enumerate(cats):
        d.append(_r(PX + 20 + i * 48, PY + 20, 44, 34, c, 1))
    d.append(stext(PX + 160, PY + 70, 'qualitative: categories', 'gray', 10, step=1))
    for i in range(12):
        t = i / 11
        d.append(_r(PX + 20 + i * 24, PY + 85, 23, 34, f'#{int(68 + t * 185):02x}{int(1 + t * 230):02x}{int(84 - t * 50):02x}', 2))
    d.append(stext(PX + 160, PY + 135, 'sequential (viridis-like): magnitudes', 'gray', 10, step=2))
    lo, mid, hi = (33, 102, 172), (247, 247, 247), (178, 24, 43)
    for i in range(12):
        t = i / 11
        a, bb, u = (lo, mid, t * 2) if t <= 0.5 else (mid, hi, (t - 0.5) * 2)
        col = '#' + ''.join(f'{int(a[k] + (bb[k] - a[k]) * u):02x}' for k in range(3))
        d.append(_r(PX + 20 + i * 24, PY + 150, 23, 34, col, 3))
    d += [stext(PX + 160, PY + 200, 'diverging: around a midpoint (0)', 'gray', 10, step=3),
          _bottom('avoid rainbow/jet: false bands, not colour-blind safe · fix vmin/vmax across panels', 4),
          _bottom('grey for context + one accent colour for the message', 5, 'green', y=324)]
    code = [("cmap='tab10'  # groups", 1), ("cmap='viridis'  # low → high", 2), ("cmap='RdBu_r', norm=TwoSlopeNorm(0)", 3),
            ('imshow(..., vmin=-1, vmax=1)', 4), ("color=['#cbd5e1', ..., '#0ea5e9']", 5)]
    return _recipe('Choosing colours by data type', code, d, [
        'Qualitative palettes give unordered groups distinct hues.', 'Sequential maps show low-to-high magnitudes with steadily changing lightness.',
        'Diverging maps show deviations around a meaningful midpoint such as zero.', 'Avoid rainbow maps and fix the colour range when comparing.',
        'Use colour sparingly: grey for context, an accent for the message.'])


def annotate_anim():
    pts = [(PX + 40 + i * 14, PY + 70 + (8 if 9 <= i <= 11 else 0) * 9 + (i % 3) * 4) for i in range(19)]
    d = [_frame(), _pl(pts, 'blue', 1, 2),
         _ln(PX + 30, PY + 110, PX + PW - 10, PY + 110, 'red', 2, 1.5, '5,4'), stext(PX + 40, PY + 104, 'target 80 %', 'red', 10, anchor='start', step=2),
         _r(PX + 40 + 9 * 14, PY + 15, 3 * 14, PH - 40, 'amber', 3, op=0.2), stext(PX + 40 + 10.5 * 14, PY + 30, 'exam week', 'amber', 10, step=3),
         _ln(PX + 250, PY + 170, PX + 40 + 10 * 14 + 4, PY + 70 + 72 + 4, 'gray', 4, 1.5), stext(PX + 252, PY + 185, 'lowest: 67 %', '#e2e8f0', 10, anchor='start', step=4),
         _bottom('title states the message: "Attendance fell ~15 points during exam-prep week"', 5)]
    code = [('ax.plot(dates, rate)', 1), ("ax.axhline(80, ls='--')", 2), ('ax.axvspan(start, end, alpha=0.2)', 3),
            ("ax.annotate(txt, xy=low, xytext=..., arrowprops=dict(arrowstyle='->'))", 4), ('ax.set_title(message)', 5)]
    return _recipe('Annotations tell the reader where to look', code, d, [
        'Start with the plain line.', 'A target line gives context.', 'A shaded span marks the event period.',
        'An arrow and short note point at the key value (13 April, 67 %).', 'A message title states the conclusion.'])


def style_anim():
    d = [_r(PX, PY, 150, 105, '#e5e7eb', 1, op=0.9), stext(PX + 75, PY + 58, "style 'ggplot'", '#111827', 10, step=1),
         _r(PX + 170, PY, 150, 105, '#0f766e', 2, op=0.2, stroke='#0f766e'), stext(PX + 245, PY + 58, 'house rc_context', 'green', 10, step=2),
         _r(PX, PY + 125, 95, 80, 'blue', 3, op=0.25), stext(PX + 47, PY + 170, 'PNG 100 dpi', 'blue', 9, step=3),
         _r(PX + 110, PY + 125, 95, 80, 'blue', 3, op=0.45), stext(PX + 157, PY + 170, 'PNG 300 dpi', 'blue', 9, step=3),
         _r(PX + 220, PY + 125, 95, 80, 'purple', 4, op=0.35), stext(PX + 267, PY + 165, 'SVG / PDF', 'purple', 9, step=4),
         stext(PX + 267, PY + 180, 'vector', 'purple', 9, step=4),
         stext(PX + 47, PY + 220, '11.4 KB', 'gray', 10, step=3), stext(PX + 157, PY + 220, '38.3 KB', 'gray', 10, step=3), stext(PX + 267, PY + 220, '19.5 / 12.2 KB', 'gray', 10, step=4),
         _bottom("bbox_inches='tight' keeps labels · save at the final figsize so fonts stay readable", 5)]
    code = [("plt.style.use('ggplot')", 1), ('with plt.rc_context(house):', 2), ("fig.savefig('c.png', dpi=300)", 3),
            ("fig.savefig('c.svg'); fig.savefig('c.pdf')", 4), ("..., bbox_inches='tight'", 5)]
    return _recipe('Styles and saving', code, d, [
        'Style sheets change many defaults at once.', 'A house style dictionary gives every chart the same look.',
        'Raster PNGs: higher dpi for print, larger files.', 'Vector SVG/PDF stay sharp at any zoom and are editable.',
        'Tight bounding boxes and the right figure size finish the job.'])



# ------------------------------------------------------------ section 3
def box_anim():
    def box(x, q1, med, q3, lo, hi, col, st, outl=()):
        sy = lambda v: PY + PH - 25 - (v - 2) * 11
        out = [_ln(x + 20, sy(lo), x + 20, sy(q1), '#e2e8f0', st, 1.5), _ln(x + 20, sy(q3), x + 20, sy(hi), '#e2e8f0', st, 1.5),
               _r(x, sy(q3), 40, sy(q1) - sy(q3), col, st, op=0.35, stroke=PALETTE.get(col, col)), _ln(x, sy(med), x + 40, sy(med), '#e2e8f0', st, 2.5)]
        out += [f'<circle cx="{x + 20}" cy="{sy(o):.1f}" r="4" fill="none" stroke="#ef4444" stroke-width="1.5" data-step="{st}"/>' for o in outl]
        return out
    d = [_frame()]
    d += box(PX + 50, 4.7, 6.8, 8.0, 2.7, 12.2, 'blue', 1, (13.6, 13.9, 16.6))
    d += box(PX + 120, 4.8, 5.8, 6.9, 3.1, 9.8, 'amber', 1, (10.9, 11.2, 12.6, 14.6))
    d += box(PX + 190, 4.6, 6.0, 7.1, 2.6, 10.4, 'green', 1, (16.4, 19.8))
    d += [stext(PX + 70, PY + PH - 8, 'DBDA', 'gray', 9, step=1), stext(PX + 140, PY + PH - 8, 'DAC', 'gray', 9, step=1), stext(PX + 210, PY + PH - 8, 'DAI', 'gray', 9, step=1),
          stext(PX + 280, PY + 60, 'box = Q1-Q3', 'gray', 9, step=2), stext(PX + 280, PY + 76, 'line = median', 'gray', 9, step=2),
          stext(PX + 280, PY + 92, 'red = outliers', 'red', 9, step=2),
          _pl([(PX + 280, PY + 130), (PX + 265, PY + 150), (PX + 278, PY + 175), (PX + 262, PY + 195), (PX + 280, PY + 215)], 'purple', 3, 1.5),
          _pl([(PX + 280, PY + 130), (PX + 295, PY + 150), (PX + 282, PY + 175), (PX + 298, PY + 195), (PX + 280, PY + 215)], 'purple', 3, 1.5),
          stext(PX + 280, PY + 122, 'violin', 'purple', 9, step=3),
          _bottom('medians 6.8 · 5.8 · 6.0 LPA · outliers 3 · 7 · 2 (real run)', 4),
          _bottom('same box, different shapes: a bimodal group looks like a normal one — add violins or points', 5, 'amber', y=324)]
    code = [('ax.boxplot(data, tick_labels=groups)', 1), ('showmeans=True, patch_artist=True', 2), ('ax.violinplot(data, showmedians=True)', 3),
            ('ax.scatter(i + jitter, d, s=6)', 4), ('# check shape, not just the box', 5)]
    return _recipe('Box and violin plots for comparing groups', code, d, [
        'Each box summarises one group: quartiles, median, whiskers to 1.5 IQR.', 'Points beyond the whiskers are drawn as outliers.',
        'A violin adds the full density shape.', 'Jittered raw points keep small groups honest. Real medians: 6.8, 5.8 and 6.0 LPA.',
        'Different distributions can share the same box; check the shape.'])


def pie_anim():
    import math
    cx, cy, r = PX + 85, PY + 110, 70
    def wedge(a0, a1, col, st, w=0.42):
        ri = r * (1 - w)
        p = lambda a, rr: (cx + rr * math.sin(a), cy - rr * math.cos(a))
        x0, y0 = p(a0, r); x1, y1 = p(a1, r); x2, y2 = p(a1, ri); x3, y3 = p(a0, ri)
        large = 1 if a1 - a0 > math.pi else 0
        return (f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 {large} 1 {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f} A {ri:.1f} {ri:.1f} 0 {large} 0 {x3:.1f} {y3:.1f} Z" '
                f'fill="{PALETTE.get(col, col)}" data-step="{st}"/>')
    a = 0
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569')]
    for share, col in [(0.407, '#0f766e'), (0.378, '#5eead4'), (0.215, '#cbd5e1')]:
        d.append(wedge(a, a + share * 2 * math.pi, col, 1)); a += share * 2 * math.pi
    d += [stext(cx, cy + 4, '600', '#e2e8f0', 12, step=1, bold=True), stext(cx, PY + 205, 'donut: ~half is DBDA', 'gray', 10, step=1)]
    for i, (n, v) in enumerate([('DBDA', 40.7), ('DAC', 37.8), ('DAI', 21.5)]):
        y = PY + 40 + i * 45
        d += [_r(PX + 185, y, v * 2.6, 28, '#0f766e', 2), stext(PX + 180, y + 18, n, 'gray', 9, anchor='end', step=2), stext(PX + 190 + v * 2.6, y + 18, f'{v}%', '#e2e8f0', 9, anchor='start', step=2)]
    d += [stext(PX + 245, PY + 190, 'bars: precise', 'gray', 10, step=2),
          _bottom('5 similar slices (18-25 %): pie unreadable, bars show E > B > C > A > D', 3, 'amber'),
          _bottom('many groups → 100 % stacked bars · never 3-D or exploded pies', 4, 'red', y=324)]
    code = [("ax.pie(v, autopct='%1.0f%%', wedgeprops=dict(width=0.42))", 1), ('ax.barh(s.index, s / s.sum() * 100)', 2), ('# 5 similar slices → bars', 3),
            ("crosstab(..., normalize='index').plot.barh(stacked=True)", 4), ('# pies: 2-4 parts of one whole', 5)]
    return _recipe('Composition: donut vs bars', code, d, [
        'A donut works for a simple part-of-whole message with few parts.', 'Sorted bars allow precise comparison of the same shares.',
        'With many similar slices, angles cannot be compared; bars make the ranking obvious.', 'For composition across groups use 100 % stacked bars.',
        'Keep pies for 2-4 clearly different parts.'])


def heat_anim():
    tab = [[74.8, 78.6, 78.2, 78.1, 77.9], [79.2, 81.7, 82.3, 81.8, 82.3], [77.8, 80.5, 80.6, 80.3, 80.3]]
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569')]
    for i, row in enumerate(tab):
        for j, v in enumerate(row):
            t = (v - 74) / 10
            col = '#' + ''.join(f'{int(a + (b - a) * t):02x}' for a, b in zip((255, 255, 204), (34, 94, 168)))
            d.append(scell(PX + 70 + j * 48, PY + 30 + i * 50, 46, 46, '', col, step=1))
            d.append(stext(PX + 93 + j * 48, PY + 58 + i * 50, f'{v:.1f}', '#111827' if v < 81 else '#ffffff', 10, step=2))
        d.append(stext(PX + 64, PY + 58 + i * 50, ['Juhu', 'Kharghar', 'Pune'][i], 'gray', 9, anchor='end', step=1))
    for j, w in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri']):
        d.append(stext(PX + 93 + j * 48, PY + 195, w, 'gray', 9, step=1))
    d += [_r(PX + 68, PY + 28, 50, 152, '#ef4444', 3, op=0, stroke='#ef4444'), stext(PX + 93, PY + 22, 'Mondays weakest', 'red', 9, step=3),
          _bottom('vmin/vmax fixed (74-84) · text colour flips on dark cells · colorbar with units', 4),
          _bottom('calendar heatmap with pcolormesh: the exam-prep week shows as a dark column', 5, 'purple', y=324)]
    code = [("tab = term.pivot_table(index='centre', columns='weekday', ...)", 1), ("ax.text(j, i, f'{v:.1f}', ha='center')", 2), ('# read the pattern', 3),
            ("ax.imshow(tab, cmap='YlGnBu', vmin=74, vmax=84)", 4), ('ax.pcolormesh(weeks, days, grid)', 5)]
    return _recipe('Heatmaps from a pivot table', code, d, [
        'Pivot to a matrix and colour each cell.', 'Annotate small tables with the values.', 'The pattern jumps out: Monday attendance is lowest at every centre.',
        'Fix the colour range and add a colorbar.', 'pcolormesh draws calendar-style grids with real coordinates.'])


def errbar_anim():
    data = [('Juhu', 58.86, 2.59, 61.83, 2.79), ('Kharghar', 58.23, 2.39, 63.14, 2.28), ('Pune', 58.24, 2.57, 60.34, 2.61)]
    sy = lambda v: PY + PH - 25 - (v - 54) * 14
    d = [_frame()]
    for i, (c, mt, ct, mf, cf) in enumerate(data):
        x = PX + 80 + i * 85
        d += [_ln(x - 10, sy(mt - ct), x - 10, sy(mt + ct), 'gray', 1, 2), _dot(x - 10, sy(mt), 'gray', step=1, r=5),
              _ln(x + 10, sy(mf - cf), x + 10, sy(mf + cf), 'green', 2, 2), _dot(x + 10, sy(mf), 'green', step=2, r=5),
              stext(x, PY + PH - 8, c, 'gray', 9, step=1)]
    d += [stext(PX + 270, PY + 30, 'grey = traditional', 'gray', 9, step=1), stext(PX + 270, PY + 45, 'green = flipped', 'green', 9, step=2),
          _bottom('mean ± 95 % CI (t × SE) — say which interval you draw', 3),
          _bottom('fill_between: narrow CI of the line vs wide prediction band for individuals', 4, 'purple', y=324)]
    code = [('g = df.groupby([...])[...].agg(["mean", "sem"])', 1), ("ax.errorbar(x, mean, yerr=ci, fmt='o', capsize=5)", 2),
            ('ci = sem * t.ppf(0.975, n - 1)', 3), ('ax.fill_between(xs, lo, hi, alpha=0.3)', 4), ('# label: SD, SE or 95 % CI?', 5)]
    return _recipe('Showing uncertainty: error bars and bands', code, d, [
        'Mean post-test per centre for the traditional classroom, with 95 % CIs.', 'The flipped classroom is ahead in every centre (Kharghar 63.1 vs 58.2).',
        'CIs overlap in Juhu and Pune: the per-centre gaps are less certain.', 'Bands around a fitted line: the CI of the mean is narrow, the prediction band wide.',
        'Always state which interval is drawn.'])


def ts_anim():
    import random
    rng = random.Random(3)
    raw, smooth = [], []
    for i in range(60):
        base = 0.84 - i * 0.0008 - (0.15 if 22 <= i <= 25 else 0)
        raw.append(base + rng.gauss(0, 0.02))
    for i in range(60):
        w = raw[max(0, i - 4):i + 5]
        smooth.append(round(sum(w) / len(w), 6))           # rounded: identical on every Python version
    sx = lambda i: PX + 35 + i * 4.6
    sy = lambda v: PY + PH - 25 - (v - 0.6) * 600
    d = [_frame(), _pl([(sx(i), sy(v)) for i, v in enumerate(raw)], '#94a3b8', 1, 1),
         _pl([(sx(i), sy(v)) for i, v in enumerate(smooth)], 'green', 2, 3),
         _r(sx(22), PY + 15, sx(25) - sx(22), PH - 40, 'red', 3, op=0.15), stext(sx(23.5), PY + 30, 'exam-prep', 'red', 9, step=3)]
    for k, m in enumerate(['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']):
        d.append(stext(sx(k * 10 + 2), PY + PH - 10, m, 'gray', 9, step=4))
    d += [_bottom('monthly means (real): Kharghar 84.3 → 83.1 → 79.8 → 81.9 → 80.6 → 79.5', 4),
          _bottom("resample('W-FRI').mean(): 130 days → 26 weekly points", 5, 'purple', y=324)]
    code = [("ax.plot(s.index, s, alpha=0.25)", 1), ('s.rolling(10, center=True).mean()', 2), ('ax.axvspan(start, end, alpha=0.12)', 3),
            ('ConciseDateFormatter(MonthLocator())', 4), ("s.resample('W-FRI').mean()", 5)]
    return _recipe('Time series: raw, smoothed, annotated', code, d, [
        'Daily values are noisy: draw them faintly.', 'A centred rolling mean shows the trend without lag.', 'Shade known events so dips are explained.',
        'Date locators and formatters keep the x-axis readable.', 'Resampling to weeks or months changes the frequency instead of smoothing.'])


# ------------------------------------------------------------ section 4
def sns_anim():
    d = [_r(PX, PY, 140, 110, '#ffffff', 1, op=0.04, stroke='#475569'), stext(PX + 70, PY + 16, 'wide', 'amber', 10, step=1, bold=True),
         stable(PX + 6, PY + 24, ['centre', 'pre', 'post'], [['Juhu', '52.8', '60.2'], ['Khar.', '53.2', '60.8']], [44, 40, 40], h=22, step=1),
         sarrow(PX + 145, PY + 55, PX + 170, PY + 55, 'gray', step=2),
         stable(PX + 175, PY + 6, ['centre', 'test', 'mean'], [['Juhu', 'pre', '52.8'], ['Juhu', 'post', '60.2'], ['Khar.', 'pre', '53.2'], ['Khar.', 'post', '60.8']],
                [48, 40, 52], h=20, step=2, title='tidy (melt)', title_color='green'),
         _r(PX, PY + 130, 150, 100, 'blue', 3, op=0.15, stroke='#0ea5e9'), stext(PX + 75, PY + 172, 'axes-level', 'blue', 11, step=3, bold=True),
         stext(PX + 75, PY + 190, 'sns.barplot(..., ax=ax)', 'blue', 9, step=3),
         _r(PX + 170, PY + 130, 150, 100, 'purple', 4, op=0.15, stroke='#8b5cf6'), stext(PX + 245, PY + 172, 'figure-level', 'purple', 11, step=4, bold=True),
         stext(PX + 245, PY + 190, 'sns.displot(col=...)', 'purple', 9, step=4), stext(PX + 245, PY + 206, '→ FacetGrid, 3 panels', 'purple', 9, step=4),
         _bottom("sns.set_theme(style='whitegrid') · map columns to x, y, hue, col, row", 5)]
    code = [('wide = df.groupby(...)[[...]].mean()', 1), ("long = wide.melt(id_vars='centre')", 2), ("sns.barplot(data=long, x=..., hue='test', ax=ax)", 3),
            ("g = sns.displot(data=df, col='course', kind='kde')", 4), ("sns.set_theme(style='whitegrid')", 5)]
    return _recipe('Seaborn: tidy data in, statistical charts out', code, d, [
        'Wide tables spread one variable across columns.', 'melt turns them into tidy long format: one row per observation.',
        'Axes-level functions draw into an Axes you control.', 'Figure-level functions build their own faceted figure and return a FacetGrid.',
        'A theme and column-to-role mapping do the rest.'])


def dist_anim():
    import math
    f1, f2 = _npdf(58.5, 12.7), _npdf(61.9, 12.7)
    X, Y, W, H = PX + 10, PY + 20, 150, 110
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569'),
         _curve(f1, 20, 100, X, Y, W, H, 0.034, 'gray', step=1, fill=True), _curve(f2, 20, 100, X, Y, W, H, 0.034, 'green', step=1, fill=True),
         stext(X + 75, Y - 6, 'kdeplot(hue=method)', 'gray', 9, step=1)]
    cdf = lambda m: (lambda x: 0.5 * (1 + math.erf((x - m) / (12.7 * math.sqrt(2)))))
    X2 = PX + 165
    d += [_curve(cdf(58.5), 20, 100, X2, Y, W, H, 1, 'gray', step=2), _curve(cdf(61.9), 20, 100, X2, Y, W, H, 1, 'green', step=2),
          _ln(X2, Y + H / 2, X2 + W, Y + H / 2, '#94a3b8', 2, 1, '3,3'), stext(X2 + 75, Y - 6, 'ecdfplot: read quartiles', 'gray', 9, step=2),
          stable(PX + 15, PY + 160, ['method', 'Q1', 'median', 'Q3'], [['flipped', '52', '62', '71'], ['traditional', '51', '58.5', '67']], [85, 50, 60, 50], h=22, step=3,
                 title='real quartiles of post-test', title_color='green'),
          _bottom('bw_adjust=3 spreads density below 0 LPA (impossible) — check bounds', 4, 'red'),
          _bottom("common_norm=False compares shapes of different-sized groups · multiple='stack' for counts", 5, 'purple', y=324)]
    code = [("sns.kdeplot(data=df, x='post_test', hue='method', common_norm=False)", 1), ("sns.ecdfplot(data=df, x='post_test', hue='method')", 2),
            ("df.groupby('method')['post_test'].quantile([...])", 3), ("sns.kdeplot(..., bw_adjust=3)", 4), ("sns.histplot(..., multiple='stack')", 5)]
    return _recipe('Distribution plots in Seaborn', code, d, [
        'KDEs overlay the shape of each group.', 'ECDFs show the share below each value; medians are read at 0.5.',
        'The flipped curve shifts most at the median and upper quartile; the lowest quarter barely moves.', 'KDE bandwidth is a choice: too wide spills into impossible values.',
        'Normalise per group to compare shapes; stack to show counts.'])


def cat_anim():
    d = [_frame()]
    vals = [('Kharghar', 0.429, 0.064), ('Juhu', 0.312, 0.066), ('Pune', 0.299, 0.068)]
    for i, (c, v, ci) in enumerate(vals):
        x = PX + 55 + i * 60
        d += [_r(x, PY + PH - 25 - v * 400, 40, v * 400, 'blue', 1), _ln(x + 20, PY + PH - 25 - (v + ci) * 400, x + 20, PY + PH - 25 - (v - ci) * 400, '#e2e8f0', 2, 2),
              stext(x + 20, PY + PH - 10, c, 'gray', 9, step=1)]
    d += [stext(PX + 115, PY + 20, 'barplot of a 0/1 column = rate', 'blue', 9, step=1),
          stable(PX + 212, PY + 40, ['errorbar', 'width'], [["('ci', 95)", '2.83'], ["'se'", '1.41'], ["'sd'", '21.43']], [62, 44], h=22, step=3,
                 title='final score', title_color='amber'),
          _bottom('box + stripplot: summary and every student · swarmplot for small n', 4),
          _bottom('pointplot(hue=method): interaction centre × method', 5, 'purple', y=324)]
    code = [("sns.countplot(data=df, x='centre', hue='status')", 1), ("sns.barplot(data=df, x='centre', y='placed')", 1),
            ("..., errorbar=('ci', 95)  # bootstrap", 2), ("errorbar='se' / 'sd' / None", 3), ('sns.boxplot(...); sns.stripplot(...)', 4),
            ("sns.pointplot(..., hue='method', dodge=0.3)", 5)]
    return _recipe('Categorical plots: estimates, intervals, data', code, d, [
        'countplot counts rows; barplot shows an estimate (here the mean of 0/1 = placement rate).', 'The default error bar is a bootstrap 95 % CI of that estimate.',
        'Different errorbar choices answer different questions: CI and SE are narrow, SD is the spread of students.', 'Show the data with box + strip or swarm plots.',
        'pointplot compares two categorical factors at once.'])


def rel_anim():
    sy = lambda v: PY + PH - 25 - (v - 0.73) * 1300
    lines = [('Kharghar', [0.792, 0.817, 0.823, 0.818, 0.823], 'blue'), ('Juhu', [0.748, 0.786, 0.782, 0.781, 0.779], 'amber'), ('Pune', [0.778, 0.805, 0.806, 0.803, 0.803], 'green')]
    d = [_frame()]
    for k, (c, vals, col) in enumerate(lines):
        pts = [(PX + 60 + i * 55, sy(v)) for i, v in enumerate(vals)]
        band = [(x, y - 12) for x, y in pts] + [(x, y + 12) for x, y in pts[::-1]]
        d += [_pl(band, col, 2, 0, fill=col, op=0.15), _pl(pts, col, 1), *[_dot(x, y, col, step=1, r=3.5) for x, y in pts],
              stext(pts[-1][0] + 6, pts[-1][1] + 4, c, col, 9, anchor='start', step=1)]
    for i, w in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri']):
        d.append(stext(PX + 60 + i * 55, PY + PH - 10, w, 'gray', 9, step=1))
    d += [stext(PX + 160, PY + 20, '26 days averaged per point', 'gray', 9, step=2),
          _bottom("ordered categorical weekday, else Fri, Mon, Thu… alphabetical", 3, 'red'),
          _bottom("units='week', estimator=None: one thin line per week + bold mean", 4, 'purple', y=324)]
    code = [("sns.lineplot(data=term, x='weekday', y='attendance', hue='centre')", 1), ("errorbar=('ci', 95)  # default band", 2),
            ("pd.Categorical(day, ['Mon', ..., 'Fri'], ordered=True)", 3), ("units='week', estimator=None", 4), ("errorbar='sd' → spread, not uncertainty", 5)]
    return _recipe('lineplot aggregates for you', code, d, [
        'lineplot averages the rows that share each x value.', 'The band is a 95 % CI computed from about 26 days per point.',
        'Categorical x needs an explicit order.', 'With units and estimator=None, it draws every entity instead.',
        'errorbar="sd" shows the spread of days rather than uncertainty of the mean.'])


def reg_anim():
    import random
    rng = random.Random(9)
    sx = lambda v: PX + 40 + v * 10.5
    sy = lambda v: PY + PH - 25 - (v - 30) * 3
    pts = [(h, 44.95 + 1.597 * h + rng.gauss(0, 7)) for h in [min(25, rng.gammavariate(4, 2.2)) for _ in range(40)]]
    d = [_frame()] + [_dot(sx(h), sy(v), 'gray', step=1, r=3) for h, v in pts]
    d += [_pl([(sx(0), sy(44.95 - 1.5)), (sx(25), sy(44.95 + 1.597 * 25 - 2.5)), (sx(25), sy(44.95 + 1.597 * 25 + 2.5)), (sx(0), sy(44.95 + 1.5))], 'blue', 2, 0, fill='blue', op=0.2),
          _ln(sx(0), sy(44.95), sx(25), sy(44.95 + 1.597 * 25), 'blue', 2, 2.5),
          stext(PX + 230, PY + PH - 35, 'regplot: fit + 95 % CI band', 'blue', 9, step=2),
          stext(PX + 45, PY + 32, 'lmplot(hue=course) slopes:', 'green', 9, anchor='start', step=3),
          stext(PX + 45, PY + 47, 'DAC 1.69 · DAI 1.64 · DBDA 1.50', 'green', 9, anchor='start', step=3, bold=True),
          _bottom('logistic=True for 0/1 outcomes · residplot(lowess=True) checks for curvature', 4),
          _bottom('seaborn draws the fit; np.polyfit / statsmodels give the numbers', 5, 'amber', y=324)]
    code = [("sns.regplot(data=df, x='study_hours', y='final_score')", 1), ('# band = CI of the line, not of students', 2),
            ("sns.lmplot(..., hue='course')", 3), ("sns.regplot(..., logistic=True); sns.residplot(..., lowess=True)", 4), ('np.polyfit(x, y, 1)', 5)]
    return _recipe('Regression plots', code, d, [
        'Start from the scatter.', 'regplot adds a least-squares line with a bootstrap confidence band for the line.',
        'lmplot fits one line per group: slopes of 1.50-1.69 marks per hour, nearly parallel.', 'Logistic fits and residual plots cover 0/1 outcomes and model checks.',
        'Compute coefficients with NumPy or statsmodels; Seaborn only draws.'])



# ------------------------------------------------------------ section 5
def facet_anim():
    import random
    rng = random.Random(2)
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569')]
    for r in range(3):
        for c in range(3):
            x, y = PX + 30 + c * 95, PY + 18 + r * 70
            st = 1 if (r, c) == (0, 0) else (2 if r == 0 else 3)
            d.append(_r(x, y, 88, 62, '#0ea5e9', st, op=0.06, stroke='#475569'))
            for _ in range(10):
                h = rng.uniform(0, 1)
                d.append(_dot(x + 6 + h * 76, y + 54 - h * 40 - rng.uniform(0, 12), 'blue', step=st, r=2))
            d.append(_ln(x, y + 46, x + 88, y + 46, 'red', 4, 1, '3,2'))
        d.append(stext(PX + 24, PY + 52 + r * 70, ['DAC', 'DBDA', 'DAI'][r], 'gray', 9, anchor='end', step=3))
    for c, n in enumerate(['Kharghar', 'Juhu', 'Pune']):
        d.append(stext(PX + 74 + c * 95, PY + 12, n, 'gray', 9, step=2))
    d += [_bottom('same axes in every panel → compare by eye · g.refline(y=50) adds the pass mark everywhere', 4),
          _bottom("catplot(kind='box') / displot(col_wrap=3) / g.map_dataframe(sns.stripplot)", 5, 'purple', y=324)]
    code = [("g = sns.relplot(data=df, x=..., y=...,", 1), ("    col='centre',", 2), ("    row='course')", 3), ('g.refline(y=50)', 4),
            ("g.set_titles('{col_name}')", 5)]
    return _recipe('Small multiples with FacetGrid', code, d, [
        'One scatter of study hours vs final score.', 'col= repeats it for each centre.', 'row= adds one row per course: a 3 × 3 grid with shared axes.',
        'Grid-wide helpers add reference lines and labels to every panel.', 'catplot and displot facet the same way; map_dataframe adds custom layers.'])


def pair_anim():
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569')]
    names = ['att', 'hours', 'pre', 'post']
    corr = {(2, 3): 0.81, (0, 1): 0.02}
    for i in range(4):
        for j in range(4):
            if j > i:
                continue
            x, y = PX + 30 + j * 55, PY + 15 + i * 52
            st = 1 if i == j else 2
            d.append(_r(x, y, 50, 47, '#0ea5e9' if i == j else '#10b981', st, op=0.12, stroke='#475569'))
            if i == j:
                d.append(_pl([(x + 5, y + 42), (x + 15, y + 30), (x + 25, y + 12), (x + 35, y + 30), (x + 45, y + 42)], 'blue', st, 1.5))
            else:
                r = corr.get((j, i), 0.3)
                for k in range(8):
                    t = k / 7
                    d.append(_dot(x + 6 + t * 38, y + 40 - (t * 30 * r + (1 - r) * ((k * 37) % 30)), 'green', step=st, r=1.8))
        d.append(stext(PX + 26, PY + 42 + i * 52, names[i], 'gray', 9, anchor='end', step=1))
    d += [stext(PX + 270, PY + 40, 'corner=True', 'green', 10, step=2), stext(PX + 270, PY + 56, 'k² panels', 'gray', 9, step=2),
          stext(PX + 270, PY + 120, 'pre vs post:', 'amber', 10, step=3), stext(PX + 270, PY + 136, 'r = 0.81', 'amber', 10, step=3, bold=True),
          _bottom("jointplot(kind='hex'): one pair in detail with marginal histograms", 4),
          _bottom('select 5-6 columns and sample rows: pairplots get slow and cramped', 5, 'red', y=324)]
    code = [("sns.pairplot(df, vars=cols,", 1), ("    hue='placed', corner=True)", 2), ("df[cols].corr()", 3), ("sns.jointplot(..., kind='hex')", 4),
            ('df.sample(2000)', 5)]
    return _recipe('pairplot and jointplot for EDA', code, d, [
        'The diagonal shows each variable\'s distribution.', 'Off-diagonal panels show every pair; corner=True drops the mirrored half.',
        'Strong pairs stand out (pre- and post-test, r = 0.81); attendance and hours are unrelated (0.02).', 'jointplot zooms into one pair with marginal distributions.',
        'Limit variables and rows to keep it readable and fast.'])


def sheat_anim():
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569')]
    corr = [[1, None, None], [0.02, 1, None], [0.38, 0.66, 1]]
    labels = ['attendance', 'hours', 'final']
    for i in range(3):
        for j in range(3):
            v = corr[i][j]
            if v is None:
                d.append(scell(PX + 70 + j * 46, PY + 20 + i * 46, 44, 44, '', '#1e293b', step=2))
                continue
            t = v
            col = '#' + ''.join(f'{int(a + (b - a) * t):02x}' for a, b in zip((247, 247, 247), (178, 24, 43)))
            d.append(scell(PX + 70 + j * 46, PY + 20 + i * 46, 44, 44, f'{v:.2f}', col, '#111827' if v < 0.6 else '#ffffff', step=1, size=10))
        d.append(stext(PX + 64, PY + 46 + i * 46, labels[i], 'gray', 9, anchor='end', step=1))
    d += [stext(PX + 140, PY + 175, 'mask upper triangle', 'gray', 9, step=2),
          stext(PX + 275, PY + 40, 'clustermap', 'purple', 10, step=3, bold=True)]
    for k, n in enumerate(['Python', 'DSA', 'Spark', 'Java', 'Stats', 'ML', 'Excel', 'R']):
        d.append(stext(PX + 275, PY + 60 + k * 15, n, 'green' if k < 4 else 'amber', 9, step=4))
    d += [_bottom('annot=True, fmt=".2f", center=0, vmin=-1, vmax=1 · mask=np.triu(...)', 3),
          _bottom('clustering regrouped 8 subjects into programming and statistics blocks (real run)', 4, 'purple', y=324)]
    code = [("sns.heatmap(corr, annot=True, fmt='.2f', center=0)", 1), ("mask = np.triu(np.ones_like(corr, bool), k=1)", 2), ("sns.clustermap(marks, z_score=1)", 3),
            ('# column order after clustering', 4), ("cmap='RdBu_r' / 'vlag'", 5)]
    return _recipe('heatmap and clustermap', code, d, [
        'One call draws an annotated, labelled heatmap with a colorbar.', 'A mask hides the redundant upper triangle of a correlation matrix.',
        'clustermap reorders rows and columns by similarity.', 'The shuffled subjects regrouped into two skill blocks: Python, DSA, Spark, Java | Statistics, ML, Excel, R.',
        'Diverging palettes centred at 0 suit correlations.'])


def theme_anim():
    d = []
    for i, (st_, bg, grid) in enumerate([('darkgrid', '#e5e7eb', True), ('whitegrid', '#ffffff', True), ('white', '#ffffff', False), ('ticks', '#ffffff', False)]):
        x = PX + (i % 2) * 165
        y = PY + (i // 2) * 85
        d += [_r(x, y, 155, 75, bg, 1, op=0.95), stext(x + 77, y + 14, st_, '#111827', 10, step=1)]
        if grid:
            d += [_ln(x + 10, y + 40, x + 145, y + 40, '#94a3b8', 1, 1), _ln(x + 10, y + 58, x + 145, y + 58, '#94a3b8', 1, 1)]
        for k, h in enumerate([20, 35, 28, 45]):
            d.append(_r(x + 25 + k * 28, y + 70 - h, 20, h, '#4c72b0', 1))
    pal = ['#0173b2', '#de8f05', '#029e73', '#d55e00', '#cc78bc', '#ca9161']
    d += [*[_r(PX + 10 + k * 50, PY + 180, 46, 22, c, 2) for k, c in enumerate(pal)], stext(PX + 160, PY + 215, "color_palette('colorblind')", 'gray', 9, step=2),
          _bottom("context: paper < notebook < talk < poster (fonts and lines scale)", 3),
          _bottom("palette={'flipped': '#10b981', 'traditional': '#94a3b8'} — same colour in every chart", 4, 'green', y=324)]
    code = [("with sns.axes_style('darkgrid'): ...", 1), ("sns.color_palette('colorblind', 6).as_hex()", 2), ("sns.set_theme(style='ticks', context='talk')", 3),
            ('palette={...}  # fixed per category', 4), ('sns.despine()', 5)]
    return _recipe('Themes, contexts and palettes', code, d, [
        'Four built-in styles change backgrounds and gridlines.', 'Palettes can be listed as hex codes; "colorblind" is a safe default.',
        'Contexts scale everything for paper, notebook, talk or poster.', 'A palette dictionary fixes the colour of each category across all charts.',
        'despine removes the top and right borders.'])


def combine_anim():
    vals = [('DAC', 0.37, 0.28), ('DBDA', 0.37, 0.38), ('DAI', 0.48, 0.26)]
    sy = lambda v: PY + PH - 25 - v * 330
    d = [_frame()]
    for i, (c, f, t) in enumerate(vals):
        x = PX + 50 + i * 85
        d += [_r(x, sy(f), 30, f * 330, 'green', 1), _r(x + 32, sy(t), 30, t * 330, '#94a3b8', 1), stext(x + 31, PY + PH - 10, c, 'gray', 9, step=1),
              stext(x + 15, sy(f) - 4, f'{f:.0%}', '#e2e8f0', 9, step=2), stext(x + 47, sy(t) - 4, f'{t:.0%}', '#e2e8f0', 9, step=2)]
    d += [_ln(PX + 30, sy(0.40), PX + PW - 10, sy(0.40), 'red', 3, 1.5, '5,4'), stext(PX + PW - 15, sy(0.40) + 12, 'target 40 %', 'red', 9, anchor='end', step=3),
          stext(PX + 160, PY + 18, 'Only flipped PG-DAI beats the target', '#e2e8f0', 10, step=4, bold=True),
          _bottom('sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1)) · layer violin + strip + pointplot on one ax', 5)]
    code = [("sns.barplot(..., hue='method', errorbar=None, ax=ax)", 1), ('for c in ax.containers: ax.bar_label(c, ...)', 2), ('ax.axhline(0.40, ls="--")', 3),
            ('ax.set(title=message)', 4), ('sns.move_legend(ax, ...)', 5)]
    return _recipe('Seaborn draws, Matplotlib finishes', code, d, [
        'Seaborn draws the grouped barplot on an Axes you created.', 'Matplotlib bar_label writes the values on every hue container.',
        'Reference lines and formatters come from Matplotlib too.', 'The title states the finding that the data supports.',
        'move_legend relocates Seaborn legends safely; several Seaborn layers can share one Axes.'])


# ------------------------------------------------------------ section 6
def pandas_anim():
    d = [stable(PX, PY + 18, ['date', 'Juhu', 'Khar.', 'Pune'], [['02-02', '.82', '.85', '.84'], ['02-03', '.80', '.86', '.83'], ['…', '…', '…', '…']], [60, 50, 50, 50],
                h=22, step=1, title='wide table: index = x, columns = series', title_color='amber'),
         sarrow(PX + 105, PY + 110, PX + 105, PY + 128, 'gray', step=2),
         _r(PX, PY + 130, 150, 95, 'blue', 2, op=0.12, stroke='#0ea5e9'),
         _pl([(PX + 10, PY + 170), (PX + 50, PY + 175), (PX + 80, PY + 200), (PX + 110, PY + 180), (PX + 140, PY + 190)], 'blue', 2),
         _pl([(PX + 10, PY + 160), (PX + 50, PY + 162), (PX + 80, PY + 190), (PX + 110, PY + 168), (PX + 140, PY + 175)], 'amber', 2),
         stext(PX + 75, PY + 145, ".plot()", 'blue', 10, step=2),
         _r(PX + 170, PY + 130, 150, 95, 'green', 3, op=0.12, stroke='#10b981'),
         *[_r(PX + 185 + k * 22, PY + 215 - h, 16, h, '#10b981', 3) for k, h in enumerate([60, 70, 50, 62, 55, 52])],
         stext(PX + 245, PY + 145, '.plot.bar()', 'green', 10, step=3),
         _bottom('subplots=True, layout=(1, 3), sharey=True → one panel per column', 4),
         _bottom('returns Matplotlib Axes → finish with ax.set(...), annotations, savefig', 5, 'purple', y=324)]
    code = [("wide = term.pivot(index='date', columns='centre', ...)", 1), ("wide.resample('W-FRI').mean().plot()", 2), ('monthly.plot.bar(rot=0)', 3),
            ('wide.plot(subplots=True, layout=(1, 3))', 4), ('ax = ...; ax.set_ylabel(...)', 5)]
    return _recipe('pandas plotting: shape the table, then .plot()', code, d, [
        'pandas plots the index on x and each column as a series.', 'Chain transformations straight into .plot() for quick exploration.',
        'Accessors such as .plot.bar, .plot.box and .plot.hist pick the chart type.', 'subplots=True gives one panel per column.',
        'The result is ordinary Matplotlib, ready for finishing touches.'])


def choose_anim():
    rows = [('Which is biggest?', 'sorted bars', 'blue'), ('How has it changed?', 'line', 'amber'), ('How is it spread?', 'histogram / box', 'green'),
            ('Do two things relate?', 'scatter', 'purple'), ('What are the parts?', '100 % stacked bar', 'cyan')]
    d = []
    for i, (q, c, col) in enumerate(rows):
        y = PY + 8 + i * 44
        d += [sbox(PX, y, 170, 36, q, '', 'gray', step=i + 1, size=11), sarrow(PX + 172, y + 18, PX + 190, y + 18, 'gray', step=i + 1),
              sbox(PX + 192, y, 128, 36, c, '', col, step=i + 1, size=11)]
    d += [_bottom('perception: position > length > angle/area > colour shade', 5)]
    code = [('# comparison', 1), ('# trend over time', 2), ('# distribution', 3), ('# relationship', 4), ('# composition', 5)]
    return _recipe('Choose the chart from the question', code, d, [
        'Comparing categories: sorted bars on a common baseline.', 'Change over time: a line.', 'Shape of one variable: histogram, box or ECDF.',
        'Relationship between two numbers: scatter, ideally with a trend line.', 'Parts of a whole across groups: 100 % stacked bars. Encode the key comparison with position.'])


def mislead_anim():
    d = [_r(PX, PY, 150, 150, '#ffffff', 1, op=0.04, stroke='#475569'), _r(PX + 170, PY, 150, 150, '#ffffff', 2, op=0.04, stroke='#475569')]
    for k, v in enumerate([29.9, 31.2, 42.9]):
        d.append(_r(PX + 15 + k * 45, PY + 140 - (v - 28) * 8.5, 35, (v - 28) * 8.5, 'red', 1))
        d.append(_r(PX + 185 + k * 45, PY + 140 - v * 2.8, 35, v * 2.8, 'green', 2))
    d += [stext(PX + 75, PY + 165, 'axis from 28 %', 'red', 10, step=1), stext(PX + 245, PY + 165, 'axis from 0', 'green', 10, step=2),
          stext(PX + 160, PY + 190, 'data ratio 1.43 · drawn ratio 7.6 → lie factor 5.3', 'amber', 11, step=3, bold=True),
          stext(PX + 160, PY + 212, 'dual axes tuned to make lines cross → index both to 100', 'red', 10, step=4),
          _bottom('area/3-D: doubling width AND height draws a 2× value as 4× · use length', 5, 'red')]
    code = [('ax.set_ylim(28, 44)   # misleading', 1), ('ax.set_ylim(0, 50)    # honest', 2), ('lie = drawn_ratio / data_ratio', 3),
            ('ax.plot(s / s.iloc[0] * 100)', 4), ('# encode with length, not area', 5)]
    return _recipe('How charts mislead — and the honest fix', code, d, [
        'A truncated bar axis makes Kharghar look many times better.', 'From a zero baseline, the 13-point gap is shown in proportion.',
        'The lie factor quantifies the distortion: about 5 here.', 'Dual axes can make unrelated series appear to move together; index them instead.',
        'Areas and 3-D effects exaggerate differences.'])


def makeover_anim():
    d = [_r(PX, PY, 150, 150, '#e5e7eb', 1, op=0.9)]
    for k, (h, c) in enumerate([(66, '#1f77b4'), (73, '#ff7f0e'), (75, '#2ca02c')]):
        d.append(_r(PX + 18 + k * 42, PY + 140 - h * 1.5, 32, h * 1.5, c, 1))
    for k in range(4):
        d.append(_ln(PX, PY + 30 + k * 30, PX + 150, PY + 30 + k * 30, '#111827', 1, 1))
    d += [stext(PX + 75, PY + 165, 'before: "Data"', 'red', 10, step=1)]
    for k, (n, v) in enumerate([('DBDA', 37), ('DAI', 36), ('DAC', 33)]):
        d.append(_r(PX + 210, PY + 20 + k * 40, v * 2.6, 28, '#0f766e' if k == 0 else '#cbd5e1', 2 + (k == 0)))
        d.append(stext(PX + 205, PY + 38 + k * 40, n, 'gray', 9, anchor='end', step=2))
        d.append(stext(PX + 215 + v * 2.6, PY + 38 + k * 40, f'{v}%', '#e2e8f0', 9, anchor='start', step=4))
    d += [stext(PX + 245, PY + 150, 'sorted + horizontal', 'gray', 9, step=2), stext(PX + 245, PY + 165, 'one accent colour', 'green', 9, step=3),
          stext(PX + 160, PY + 200, '"PG-DBDA has the highest placement rate"', '#e2e8f0', 11, step=5, bold=True),
          _bottom('remove: heavy grid, background, legend, axis · add: labels with n, message title', 4)]
    code = [('# before: defaults + legend + grid', 1), ('s = r.sort_values(); ax.barh(...)', 2), ("colors = ['#cbd5e1', ..., '#0f766e']", 3),
            ("ax.bar_label(..., labels=[f'{v:.0f}% (n=...)'])", 4), ("fig.text(..., message, weight='bold')", 5)]
    return _recipe('Makeover: from default output to a message', code, d, [
        'The default: rainbow bars, legend, heavy grid, a title that says nothing.', 'Sort and turn horizontal.', 'Grey for context, one accent for the point.',
        'Label values directly (with n) and remove the axis, grid and legend.', 'A message title tells the reader the conclusion.'])


def bigdata_anim():
    import random
    rng = random.Random(1)
    d = [_r(PX, PY, 100, 110, '#ffffff', 1, op=0.04, stroke='#475569')]
    for _ in range(220):
        x = rng.gauss(0.5, 0.18); y = rng.gauss(0.5, 0.2)
        if 0 < x < 1 and 0 < y < 1:
            d.append(_dot(PX + 5 + x * 90, PY + 105 - y * 100, 'blue', step=1, r=4))
    d.append(stext(PX + 50, PY + 128, 'blob', 'gray', 9, step=1))
    d.append(_r(PX + 110, PY, 100, 110, '#ffffff', 2, op=0.04, stroke='#475569'))
    for _ in range(220):
        x = rng.gauss(0.5, 0.18); y = rng.gauss(0.5, 0.2)
        if 0 < x < 1 and 0 < y < 1:
            d.append(f'<circle cx="{PX + 115 + x * 90:.1f}" cy="{PY + 105 - y * 100:.1f}" r="1.5" fill="#0ea5e9" fill-opacity="0.35" data-step="2"/>')
    d.append(stext(PX + 160, PY + 128, 'alpha + small', 'gray', 9, step=2))
    d.append(_r(PX + 220, PY, 100, 110, '#ffffff', 3, op=0.04, stroke='#475569'))
    import math
    for i in range(8):
        for j in range(8):
            v = math.exp(-((i - 3.5) ** 2 + (j - 3.5) ** 2) / 6)
            col = '#' + ''.join(f'{int(a + (b - a) * v):02x}' for a, b in zip((68, 1, 84), (253, 231, 37)))
            d.append(_r(PX + 225 + i * 11.5, PY + 8 + j * 12, 11, 11.5, col, 3))
    d.append(stext(PX + 270, PY + 128, 'hexbin / hist2d', 'gray', 9, step=3))
    d += [stable(PX + 30, PY + 160, ['200,000 points PDF', 'size', 'save time'], [['vector', '2914 KB', '2.99 s'], ['rasterized=True', '28 KB', '0.11 s']],
                 [120, 70, 70], h=22, step=4, title='real run', title_color='amber', focus_rows={1: '4'}),
          _bottom("hexbin(bins='log') shows dense core and sparse tail · sample for exploration", 5)]
    code = [('ax.scatter(x, y)          # 200k points', 1), ('ax.scatter(x, y, s=1, alpha=0.03)', 2), ("ax.hexbin(x, y, gridsize=40, bins='log')", 3),
            ('ax.scatter(..., rasterized=True)', 4), ('df.sample(5000) / aggregate first', 5)]
    return _recipe('Large data: aggregate instead of overplotting', code, d, [
        'With hundreds of thousands of points, a plain scatter is a solid blob.', 'Tiny, transparent markers reveal some density.',
        'Binning into hexagons or squares shows where points concentrate (log colour scale).', 'Rasterizing the heavy layer shrinks the PDF from 2.9 MB to 28 KB.',
        'Sample or aggregate when the message is a pattern, not every point.'])



# ------------------------------------------------------------ section 7
def area_anim():
    xs = [PX + 40 + i * 28 for i in range(10)]
    a = [5, 10, 30, 40, 48, 70, 80, 90, 98, 105]
    b = [3, 7, 20, 28, 34, 50, 58, 64, 70, 75]
    c = [1, 3, 9, 13, 16, 24, 28, 31, 34, 36]
    base = PY + PH - 25
    sc = 0.7
    l1 = [(x, base - v * sc) for x, v in zip(xs, a)]
    l2 = [(x, base - (v + w) * sc) for x, v, w in zip(xs, a, b)]
    l3 = [(x, base - (v + w + u) * sc) for x, v, w, u in zip(xs, a, b, c)]
    step_pts = []
    for i, (x, y) in enumerate(l3):
        step_pts += [(x, y)] + ([(xs[i + 1], y)] if i + 1 < len(xs) else [])
    d = [_frame(), _pl(step_pts, 'amber', 1, 2.5), stext(PX + 100, PY + 30, 'step: cumulative admissions', 'amber', 9, step=1),
         _pl([(xs[0], base)] + l1 + [(xs[-1], base)], '#0f766e', 2, 0, fill='#0f766e', op=0.9),
         _pl(l1 + l2[::-1], '#5eead4', 3, 0, fill='#5eead4', op=0.9), _pl(l2 + l3[::-1], '#cbd5e1', 3, 0, fill='#cbd5e1', op=0.9),
         stext(PX + 230, PY + 200, 'DBDA', '#e2e8f0', 9, step=2), stext(PX + 230, PY + 120, 'DAC', '#0f172a', 9, step=3), stext(PX + 230, PY + 72, 'DAI', '#0f172a', 9, step=3),
         _bottom('cumulative counts at day 40 (real): DBDA 243 · DAC 181 · DAI 87', 4),
         _bottom('100 % area: divide each day by its total → the mix stays about 48 / 35 / 17', 5, 'purple', y=324)]
    code = [("ax.step(days, total, where='post')", 1), ('ax.stackplot(days, dbda, ...)', 2), ('..., dac, dai, labels=...)', 3),
            ('cum = daily.cumsum()', 4), ('share = cum.div(cum.sum(axis=1), axis=0)', 5)]
    return _recipe('Step and stacked area charts', code, d, [
        'A step chart shows a cumulative count that jumps after each counselling round.', 'stackplot puts the first course at the bottom...',
        '...and stacks the others: the top edge is the total.', 'Middle layers are hard to read precisely; keep layers few.', 'Normalising to 100 % shows composition over time.'])


def radar_anim():
    import math
    cx, cy, R = PX + 130, PY + 118, 95
    skills = ['Python', 'SQL', 'Stats', 'ML', 'Big Data', 'Comm.']
    ang = [math.pi / 2 - 2 * math.pi * k / 6 for k in range(6)]
    pt = lambda k, v: (cx + R * v / 100 * math.cos(ang[k]), cy - R * v / 100 * math.sin(ang[k]))
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569')]
    for rr in [25, 50, 75, 100]:
        d.append(_pl([pt(k, rr) for k in range(6)] + [pt(0, rr)], '#475569', 1, 1))
    for k, n in enumerate(skills):
        x, y = pt(k, 118)
        d += [_ln(cx, cy, *pt(k, 100), '#475569', 1, 1), stext(x, y + 4, n, 'gray', 9, step=1)]
    for vals, col, st in [([68, 72, 61, 58, 55, 66], '#94a3b8', 2), ([88, 80, 75, 82, 70, 60], '#0f766e', 3), ([60, 85, 50, 45, 72, 84], '#f59e0b', 4)]:
        pts = [pt(k, v) for k, v in enumerate(vals)]
        d.append(_pl(pts + [pts[0]], col, st, 2, fill=col, op=0.15))
    d += [stext(PX + 270, PY + 60, 'batch avg', 'gray', 9, step=2), stext(PX + 270, PY + 76, 'Asha', 'green', 9, step=3), stext(PX + 270, PY + 92, 'Rohan', 'amber', 9, step=4),
          _bottom('close the polygon: values + values[:1] · same scale on every spoke · few entities', 5)]
    code = [("fig, ax = plt.subplots(subplot_kw=dict(projection='polar'))", 1), ('angles = np.linspace(0, 2*np.pi, n, endpoint=False)', 2),
            ('ax.plot(a + a[:1], v + v[:1]); ax.fill(...)', 3), ('ax.set_xticks(angles, skills)', 4), ('ax.set_ylim(0, 100)', 5)]
    return _recipe('Radar chart of skill profiles', code, d, [
        'Polar axes: one spoke per skill.', 'The batch average gives a reference shape.', 'Asha: strong in Python and ML.',
        'Rohan: strong in SQL and communication, weaker in ML.', 'Close the polygon and keep spokes on one scale.'])


def mlviz_anim():
    d = [_r(PX, PY, 140, 140, '#ffffff', 1, op=0.04, stroke='#475569')]
    for i, row in enumerate([[0.8, 0.2], [0.35, 0.65]]):
        for j, v in enumerate(row):
            col = '#' + ''.join(f'{int(a + (b - a) * v):02x}' for a, b in zip((239, 246, 255), (8, 69, 148)))
            d.append(scell(PX + 15 + j * 58, PY + 15 + i * 58, 56, 56, f'{v:.2f}', col, '#111827' if v < 0.5 else '#ffffff', step=1))
    d += [stext(PX + 70, PY + 150, 'normalised confusion matrix', 'gray', 9, step=1), _r(PX + 160, PY, 160, 140, '#ffffff', 2, op=0.04, stroke='#475569'),
          _ln(PX + 170, PY + 130, PX + 310, PY + 10, '#94a3b8', 2, 1, '3,3'),
          _pl([(PX + 170, PY + 130), (PX + 180, PY + 70), (PX + 200, PY + 45), (PX + 240, PY + 25), (PX + 310, PY + 10)], 'blue', 2),
          _pl([(PX + 170, PY + 130), (PX + 182, PY + 78), (PX + 205, PY + 50), (PX + 245, PY + 30), (PX + 310, PY + 10)], 'amber', 3),
          stext(PX + 240, PY + 150, 'ROC: logistic vs forest', 'gray', 9, step=3)]
    for k, (n, v) in enumerate([('post_test', 0.091), ('attendance', 0.080), ('study_hours', 0.073), ('pre_test', 0.012)]):
        d += [_r(PX + 90, PY + 165 + k * 17, v * 1500, 13, '#0f766e', 4), stext(PX + 85, PY + 175 + k * 17, n, 'gray', 9, anchor='end', step=4)]
    d += [stext(PX + 260, PY + 190, 'permutation', 'green', 9, step=4), stext(PX + 260, PY + 204, 'importance (AUC)', 'green', 9, step=4),
          _bottom('PR curve for rare positives · CalibrationDisplay · predicted vs actual for regression', 5)]
    code = [("ConfusionMatrixDisplay.from_predictions(y, p, normalize='true')", 1), ('RocCurveDisplay.from_predictions(y, s, ax=ax)', 2),
            ('# second model on the same ax', 3), ('permutation_importance(m, X_te, y_te)', 4), ('PrecisionRecallDisplay...', 5)]
    return _recipe('Charts for model results', code, d, [
        'A row-normalised confusion matrix shows recall per class (illustrative values).', 'ROC curves show the ranking quality across thresholds.',
        'Comparing models on the same axes makes the choice visible.', 'Permutation importance on test data (real run): post_test 0.091, attendance 0.080, study_hours 0.073, pre_test 0.012.',
        'Precision-recall curves suit rare positives; calibration and residual plots complete the picture.'])


def threed_anim():
    import math
    d = [_r(PX, PY, 155, 160, '#ffffff', 1, op=0.04, stroke='#475569')]
    for i in range(8):
        pts = []
        for j in range(8):
            x = PX + 20 + j * 13 + i * 6
            p = 1 / (1 + math.exp(-(-6.11 + 0.054 * (55 + j * 6) + 0.145 * (i * 3.5))))
            pts.append((x, PY + 140 - i * 7 - p * 70))
        d.append(_pl(pts, '#0ea5e9', 1, 1))
    d += [stext(PX + 77, PY + 175, '3-D surface: depth ambiguous', 'gray', 9, step=1), stext(PX + 77, PY + 190, 'view_init changes the story', 'amber', 9, step=2),
          _r(PX + 170, PY, 150, 160, '#ffffff', 3, op=0.04, stroke='#475569')]
    for lv, col in [(0.25, '#94a3b8'), (0.5, '#e2e8f0'), (0.75, '#10b981')]:
        z = math.log(lv / (1 - lv))
        a1, a2 = 55, 100
        h1 = (z + 6.11 - 0.054 * a1) / 0.145; h2 = (z + 6.11 - 0.054 * a2) / 0.145
        sx = lambda a: PX + 175 + (a - 55) / 45 * 140
        sy = lambda h: PY + 150 - h / 25 * 140
        d.append(_ln(sx(a1), sy(min(25, h1)), sx(a2), sy(max(0, h2)), col, 3, 2))
        d.append(stext(sx(a2) - 6, sy(max(0, h2)) - 4, f'{lv:.2f}', col, 9, anchor='end', step=4))
    d += [stext(PX + 245, PY + 175, 'contour: P(placed) lines', 'green', 9, step=3),
          _bottom('model: logit = −6.11 + 0.054·attendance + 0.145·hours (real) · contours are readable, surfaces impress', 5)]
    code = [("ax = fig.add_subplot(projection='3d')", 1), ('ax.view_init(elev=25, azim=-60)', 2), ('cf = ax.contourf(A, H, P, levels=10)', 3),
            ('cs = ax.contour(A, H, P, levels=[.25, .5, .75])', 4), ("ax.clabel(cs, fmt='%.2f')", 5)]
    return _recipe('3-D surface vs contour map', code, d, [
        'A 3-D surface of placement probability over attendance and study hours.', 'Its appearance depends on the viewing angle; values hide behind each other.',
        'A filled contour map shows the same surface flat.', 'Labelled 25 %, 50 % and 75 % lines can be read directly: below the 50 % line, intervene.',
        'Use 3-D for exploration or genuine spatial data; use contours for communication.'])


def animate_anim():
    d = [_frame()]
    import random
    rng = random.Random(5)
    vals = [0.84 - i * 0.0012 - (0.11 if 9 <= i <= 11 else 0) + rng.gauss(0, 0.004) for i in range(30)]
    for k, st in enumerate([1, 2, 3, 4]):
        n = [6, 12, 20, 30][k]
        pts = [(PX + 40 + i * 9, PY + PH - 25 - (v - 0.68) * 900) for i, v in enumerate(vals[:n])]
        d.append(_pl(pts, ['#94a3b8', '#7dd3fc', '#38bdf8', 'blue'][k], st, 2))
        d.append(stext(PX + 250, PY + 25 + k * 15, f'frame {[8, 16, 24, 31][k]}: {["13 Feb", "13 Mar", "17 Apr", "24 Jul"][k]}', 'gray', 9, anchor='start', step=st))
    d += [_bottom('31 frames · writer="pillow" · 167 KB GIF (real run) · fixed axis limits', 5)]
    code = [('lines = {c: ax.plot([], [])[0] for c in cols}', 1), ('def update(i):', 2), ('    line.set_data(x[:i+1], y[:i+1]); return lines', 3),
            ('anim = FuncAnimation(fig, update, frames=..., blit=True)', 4), ("anim.save('term.gif', writer='pillow', fps=8)", 5)]
    return _recipe('FuncAnimation: a flip book of frames', code, d, [
        'Draw the empty scene once with fixed axis limits.', 'update(i) changes only the data of existing lines and the date label.',
        'Each frame extends the lines a little further.', 'FuncAnimation calls update for every frame; blit redraws only what changed.',
        'Saving with the pillow writer produces the GIF shown in the example.'])


# ------------------------------------------------------------ section 8
def dash_anim():
    d = []
    for k, (big, small) in enumerate([('35%', 'placement'), ('6.0', 'median LPA'), ('19.8', 'top LPA'), ('600', 'students')]):
        d += [_r(PX + k * 81, PY, 76, 50, 'green', 1, op=0.15, stroke='#0f766e'), stext(PX + 38 + k * 81, PY + 26, big, 'green', 14, step=1, bold=True),
              stext(PX + 38 + k * 81, PY + 42, small, 'gray', 8, step=1)]
    d += [_r(PX, PY + 60, 158, 80, 'blue', 2, op=0.1, stroke='#475569'), stext(PX + 79, PY + 75, 'Kharghar leads (43 %)', 'blue', 9, step=2),
          *[_r(PX + 10, PY + 85 + k * 17, w, 12, c, 2) for k, (w, c) in enumerate([(130, '#0f766e'), (94, '#cbd5e1'), (90, '#cbd5e1')])],
          _r(PX + 165, PY + 60, 155, 80, 'blue', 2, op=0.1, stroke='#475569'), stext(PX + 242, PY + 75, 'courses close (33-37 %)', 'blue', 9, step=2),
          _r(PX, PY + 150, 158, 80, 'blue', 3, op=0.1, stroke='#475569'), stext(PX + 79, PY + 165, 'most packages 4-8 LPA', 'blue', 9, step=3),
          _r(PX + 165, PY + 150, 155, 80, 'blue', 3, op=0.1, stroke='#475569'), stext(PX + 242, PY + 165, 'attendance ↑ placement ↑', 'blue', 9, step=3),
          _pl([(PX + 180, PY + 215), (PX + 220, PY + 210), (PX + 260, PY + 195), (PX + 300, PY + 180)], 'green', 3),
          _bottom('placement by attendance band (real): 19.9 % → 23.3 % → 38.1 % → 53.8 %', 4),
          _bottom('one script → dashboard.pdf + dashboard.png before every review', 5, 'purple', y=324)]
    code = [("fig, ax = plt.subplot_mosaic('ABCD;EEFF;GGHH')", 1), ("ax['E'].barh(...); ax['F'].barh(...)", 2), ("ax['G'].hist(...); ax['H'].plot(...)", 3),
            ("ax[k].text(..., big, fontsize=26)", 4), ("fig.savefig('dashboard.pdf'); fig.savefig('dashboard.png')", 5)]
    return _recipe('A one-page dashboard', code, d, [
        'KPI tiles on top answer "how are we doing?" at a glance.', 'The next row compares centres and courses, each with a message title.',
        'The bottom row shows packages and the attendance link.', 'Real numbers: placement rises from 20 % to 54 % across attendance bands.',
        'The same script regenerates the PDF and PNG for every review.'])


def report_anim():
    d = []
    for k, (c, pct) in enumerate([('Juhu', None), ('Kharghar', None), ('Pune', '43 %')]):
        x = PX + k * 108
        d += [_r(x, PY, 100, 120, '#ffffff', k + 1, op=0.06, stroke='#475569'), stext(x + 50, PY + 16, c, 'gray', 10, step=k + 1, bold=True),
              _pl([(x + 8, PY + 60), (x + 30, PY + 58), (x + 45, PY + 95), (x + 60, PY + 62), (x + 92, PY + 70)], 'green', k + 1, 2),
              _ln(x + 5, PY + 72, x + 95, PY + 72, 'red', k + 1, 1, '3,2')]
    d += [stext(PX + 266, PY + 110, 'Pune: 43 % < 80 %', 'red', 9, step=3),
          stable(PX + 20, PY + 140, ['file', 'size'], [['attendance_Juhu_2026-W31.png', '63.0 KB'], ['attendance_Kharghar_…png', '63.1 KB'], ['attendance_Pune_…png', '61.7 KB'],
                                                    ['attendance_report.pdf (3 pages)', '20.6 KB']], [210, 70], h=19, step=4, title='real run', title_color='amber'),
          _bottom('plt.close(fig) after saving · Agg backend on servers · schedule with cron / Airflow', 5)]
    code = [('def centre_chart(ax, d, centre): ...', 1), ("for centre, d in term.groupby('centre'):", 2), ("    fig.savefig(f'attendance_{centre}_….png')", 3),
            ("    pdf.savefig(fig)   # with PdfPages(...) as pdf", 4), ('    plt.close(fig)', 5)]
    return _recipe('Automating a chart report', code, d, [
        'One function draws the chart for any centre, so every page looks identical.', 'Loop over the centres.', 'Save one PNG per centre with predictable names...',
        '...and add each figure as a page of one PDF.', 'Close figures to free memory and schedule the script.'])


def forest_anim():
    rows = [('Juhu', 2.97, -0.81, 6.75), ('Kharghar', 4.91, 1.62, 8.20), ('Pune', 2.10, -1.53, 5.74), ('PG-DAC', 1.53, -1.78, 4.85),
            ('PG-DAI', 6.59, 1.93, 11.25), ('PG-DBDA', 3.60, 0.47, 6.74), ('ALL', 3.45, 1.41, 5.49)]
    sx = lambda v: PX + 110 + (v + 4) * 13.5
    d = [_r(sx(2), PY + 5, sx(12) - sx(2), PH - 25, '#10b981', 3, op=0.12), stext(sx(7), PY + PH - 6, '≥ 2 marks worthwhile', 'green', 9, step=3),
         _ln(sx(0), PY + 5, sx(0), PY + PH - 20, '#e2e8f0', 1, 1.5)]
    for k, (n, e, lo, hi) in enumerate(rows):
        y = PY + 22 + k * 28
        col = 'green' if lo > 0 else 'gray'
        st = 4 if n == 'ALL' else 2
        d += [stext(PX + 100, y + 4, n, 'gray', 9, anchor='end', step=st), _ln(sx(lo), y, sx(min(hi, 12)), y, col, st, 3), _dot(sx(e), y, col, step=st, r=5)]
    d += [stext(sx(0), PY + 4, '0', 'gray', 9, step=1), _bottom('green = CI excludes 0 · grey = uncertain · overall +3.45 [1.41, 5.49] (real run)', 5)]
    code = [("for g, d in df.groupby('centre'): ttest_ind(...).confidence_interval()", 1), ('ax.hlines(y, lo, hi); ax.scatter(diff, y)', 2),
            ("ax.axvspan(2, 10, label='worthwhile')", 3), ('# overall row last', 4), ("colours = ['green' if lo > 0 else 'grey' ...]", 5)]
    return _recipe('Forest plot of effects with confidence intervals', code, d, [
        'A zero line marks "no difference".', 'Each subgroup gets a dot (difference) and a whisker (95 % CI).', 'Shading marks the smallest effect worth acting on.',
        'The overall effect is the most precise row.', 'Colour shows which intervals exclude zero: Kharghar, PG-DAI, PG-DBDA and the overall result.'])


def eda_anim():
    d = []
    steps_ = [('1 quality', 'missing · duplicates · ranges', 'red'), ('2 univariate', 'histograms · category counts', 'blue'),
              ('3 vs target', 'correlations · rates · boxes', 'green'), ('4 segments & time', 'groups · trends', 'purple')]
    for k, (t, sub, col) in enumerate(steps_):
        d += [sbox(PX, PY + k * 52, 150, 44, t, sub, col, step=k + 1, size=10)]
    d += [stext(PX + 240, PY + 20, 'found in the extract:', 'gray', 10, step=1, bold=True),
          stext(PX + 240, PY + 40, 'pre_test 80 % missing at Juhu', 'red', 9, step=1), stext(PX + 240, PY + 56, '(form problem)', 'red', 9, step=1),
          stext(PX + 240, PY + 90, '6 attendance values > 100', 'blue', 9, step=2), stext(PX + 240, PY + 106, '(101 ... 120)', 'blue', 9, step=2),
          stext(PX + 240, PY + 140, 'final_score, post_test', 'green', 9, step=3), stext(PX + 240, PY + 156, 'relate most to placed', 'green', 9, step=3),
          stext(PX + 240, PY + 190, 'salary exists only', 'amber', 9, step=4), stext(PX + 240, PY + 206, 'after placement: leakage!', 'amber', 9, step=4),
          _bottom('every finding becomes an action: fix, exclude, transform or ask the data owner', 5)]
    code = [("miss = d.isna().mean(); d.sort_values('centre').isna()", 1), ("for col in num: ax.hist(d[col])", 2), ("num.corrwith(d['placed'])", 3),
            ('# segments, time', 4), ('# write down actions', 5)]
    return _recipe('A repeatable visual EDA', code, d, [
        'Quality first: the missingness matrix shows pre_test missing almost only at Juhu.', 'Histograms per column expose impossible attendance above 100 %.',
        'Correlations with the target show what matters.', 'Some columns only exist after the outcome and must not be used to predict it.',
        'Turn every finding into an action.'])


def explain_anim():
    import math
    f0, f1 = _npdf(0.3, 0.18), _npdf(0.75, 0.15)
    X, Y, W, H = PX + 5, PY + 15, 150, 100
    d = [_r(PX, PY, PW, PH, '#ffffff', 1, op=0.04, stroke='#475569'),
         _curve(f0, 0, 1, X, Y, W, H, 2.8, 'green', step=1, fill=True), _curve(f1, 0, 1, X, Y, W, H, 2.8, 'red', step=1, fill=True),
         stext(X + 75, Y + H + 14, 'risk score: placed vs not', 'gray', 9, step=1),
         _ln(X + W * 0.9, Y, X + W * 0.9, Y + H, 'amber', 2, 2, '4,3'), stext(X + W * 0.9 - 2, Y + 10, 'call list 120', 'amber', 9, anchor='end', step=2),
         stext(PX + 245, PY + 30, 'threshold for 120 calls:', 'amber', 9, step=2), stext(PX + 245, PY + 46, 'recall 30 %, precision 97 %', 'amber', 9, step=2, bold=True)]
    for k, (n, v, col) in enumerate([('attendance = 56', 1.37, 'red'), ('post_test = 47', 1.04, 'red'), ('study_hours = 10', -0.17, 'green')]):
        y = PY + 150 + k * 22
        d += [stext(PX + 100, y + 12, n, 'gray', 9, anchor='end', step=3), _r(PX + 140 + min(0, v) * 80, y, abs(v) * 80, 16, col, 4)]
    d += [_ln(PX + 140, PY + 145, PX + 140, PY + 215, '#e2e8f0', 3, 1), stext(PX + 250, PY + 135, 'student #324: risk 96 %', '#e2e8f0', 9, step=3, bold=True),
          _bottom('contribution = coefficient × (value − batch mean) for linear/logistic models; SHAP for trees', 5)]
    code = [("ax.hist(risk[y == 0]); ax.hist(risk[y == 1])", 1), ('prec, rec, thr = precision_recall_curve(y, risk)', 2), ('i = high-risk student', 3),
            ('contrib = coef * (X.iloc[i] - X.mean())', 4), ('ax.barh(labels, contrib, color=red/green)', 5)]
    return _recipe('Explaining a risk model visually', code, d, [
        'Overlaid score distributions show how well the model separates the groups.', 'At the threshold that fits 120 calls, the list is 97 % correct but catches 30 % of at-risk students.',
        'Pick one student to explain.', 'Low attendance (56 %) and a low post-test (47) push the risk up; slightly above-average study hours pull it down.',
        'Contribution bars work for linear models; SHAP generalises the idea.'])
