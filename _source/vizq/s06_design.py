from build import *
from vizq.anims import *
from vizq.runner import vizrun, pyshow
from vizq.data import STUDENTS, data_note, TERM, term_note

S = 'Python (pandas · Matplotlib) · uses sample data'
P = 'Python (Matplotlib)'

SECTION = dict(level='advanced', title='pandas Plotting & Chart Design', questions=[

# ------------------------------------------------------------------ 26
Q('How does pandas plotting (df.plot) work, and when is it enough?', 'pandas .plot', minutes=7, cards=[
    definition(
        defbox('<code>DataFrame.plot</code> / <code>Series.plot</code> is a thin wrapper around Matplotlib: the index becomes x, each column a series. '
               '<code>kind=</code> (or accessors <code>df.plot.line / bar / barh / hist / box / kde / area / scatter / hexbin / pie</code>) picks the chart; '
               'options include <code>subplots=True</code>, <code>layout=</code>, <code>stacked=True</code>, <code>secondary_y=</code>, <code>logy=</code>, '
               '<code>title</code>, <code>figsize</code>, <code>ax=</code>.',
               'It returns Matplotlib Axes, so you finish with normal Matplotlib calls. It is ideal for quick exploration right after a groupby/pivot/resample; '
               'for statistical summaries with CIs or faceting by a column, Seaborn is more convenient; for publication layouts, Matplotlib directly.'),
        tags('df.plot', 'kind', 'plot accessor', 'subplots=True', 'stacked', 'secondary_y', 'pivot then plot'),
    ),
    analogy('pandas plotting is the <strong>"quick photo" button on the data</strong>: shape the table (groupby, pivot), press plot, and you see it. For a '
            'framed portrait you still go to the studio (Matplotlib).'),
    pandas_anim(),
    real_world(
        scenario('Analysing in a notebook',
                 p('While exploring attendance, the analyst chains <code>.pivot(...).resample(\'W\').mean().plot()</code> to check a trend in one line, then switches '
                   'to Matplotlib only for the final, annotated version that goes to the director.')),
    ),
    example(
        term_note(),
        vizrun("""
            wide = term.pivot(index='date', columns='centre', values='attendance')
            ax = wide.resample('W-FRI').mean().plot(figsize=(8, 3.5), marker='o', title='wide.resample("W").mean().plot()')
            ax.set_ylabel('attendance')
            plt.show()

            axes = wide.plot(subplots=True, layout=(1, 3), figsize=(12, 3), sharey=True, legend=False, title=list(wide.columns), alpha=0.8)
            plt.show()

            monthly = wide.resample('ME').mean()
            monthly.index = monthly.index.strftime('%b')
            monthly.plot.bar(figsize=(8, 3.5), rot=0, title='monthly.plot.bar()', ylim=(0.7, 0.9))
            plt.show()

            ax = wide.plot.box(figsize=(6, 3.5), title='wide.plot.box()')
            plt.show()
            print(type(ax).__name__, '| shape of wide table:', wide.shape)
        """, setup=TERM, title=S),
        title='Example: Resampled Lines, Subplots, Grouped Bars and Box Plots in One Line Each'),
    steps(
        ('Shape the table first', 'Index = x; one column per series (pivot / unstack).'),
        ('Pick the kind', 'df.plot.line / bar / hist / box / scatter …'),
        ('Use options', 'subplots, stacked, logy, secondary_y, figsize, title.'),
        ('Finish with Matplotlib', 'The return value is an Axes (or array of Axes).'),
        ('Switch tools when needed', 'Seaborn for CIs/facets by column, Matplotlib for custom layouts.'),
        title='Steps for pandas Plotting'),
    crossq(
        ('Why does a bar chart from pandas start at ylim 0.7 here, and is that OK?', 'I set ylim to show small differences; for bars this exaggerates differences — acceptable for exploration, not for a report (see misleading charts).'),
        ('How do you plot a long-format table with pandas?', 'Pivot it to wide first (one column per series), or use Seaborn with hue.'),
        ('What does secondary_y do?', 'Plots the named column(s) on a right-hand y-axis; the same caveats as twinx apply.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('How do you choose the right chart for a question? Comparison, distribution, composition, relationship and trend.', 'Choosing the Right Chart', minutes=9, cards=[
    definition(
        defbox('Start from the <strong>question</strong>, not the data type: <strong>comparison</strong> across categories → sorted bar / dot plot; '
               '<strong>trend over time</strong> → line; <strong>distribution</strong> → histogram, box/violin, ECDF; <strong>relationship</strong> between two '
               'numbers → scatter (+ trend line); <strong>composition</strong> (parts of a whole) → stacked or 100 % bars (pie only for 2–3 parts); '
               '<strong>matrix of values</strong> → heatmap; <strong>ranking</strong> → sorted horizontal bars.',
               'Then apply perception: position on a common scale is read most accurately, then length, then angle/area, then colour intensity. Encode the most '
               'important comparison with position, put the things to compare next to each other, and use one chart per message.'),
        tags('chart selection', 'comparison', 'trend', 'distribution', 'relationship', 'composition', 'perceptual ranking'),
    ),
    analogy('Charts are <strong>tools in a toolbox</strong>: a line is a tape measure for change over time, a scatter is a magnifying glass for relationships, a '
            'histogram is a sieve for distributions. Using the wrong tool still produces a picture, just not an answer.'),
    choose_anim(),
    real_world(
        scenario('Five questions, five charts',
                 p('"Which centre places best?" (sorted bars), "is attendance falling?" (line), "how are scores spread?" (histogram), "do study hours help?" '
                   '(scatter), "what is the course mix?" (100 % bar). One dataset, five different charts, because there are five different questions.')),
    ),
    example(
        data_note(),
        vizrun("""
            fig, axes = plt.subplots(2, 3, figsize=(13, 7), layout='constrained')
            ax = axes[0, 0]
            r = df.groupby('centre')['placed'].mean().sort_values() * 100
            ax.barh(r.index, r, color='#0ea5e9'); ax.set_title('Comparison: which centre places best?\\n(sorted bars)')
            ax = axes[0, 1]
            m = df.groupby(pd.cut(df.attendance, [55, 65, 75, 85, 100]), observed=True)['final_score'].mean()
            ax.plot([str(i) for i in m.index], m, 'o-', color='#f59e0b'); ax.set_title('Trend: score vs attendance band\\n(line over ordered bins)')
            ax = axes[0, 2]
            ax.hist(df.final_score, bins=20, color='#10b981'); ax.set_title('Distribution: how are scores spread?\\n(histogram)')
            ax = axes[1, 0]
            ax.scatter(df.study_hours, df.final_score, s=6, alpha=0.4); ax.set_title('Relationship: do study hours help?\\n(scatter)')
            ax = axes[1, 1]
            mix = pd.crosstab(df.centre, df.course, normalize='index')
            left = np.zeros(len(mix))
            for c, col in zip(mix.columns, ['#5eead4', '#cbd5e1', '#0f766e']):
                ax.barh(mix.index, mix[c], left=left, label=c, color=col); left += mix[c].values
            ax.legend(fontsize=8, ncol=3, loc='lower center', bbox_to_anchor=(0.5, -0.3)); ax.set_title('Composition: course mix per centre\\n(100 % stacked bars)')
            ax = axes[1, 2]
            pv = df.pivot_table(index='course', columns='centre', values='final_score')
            im = ax.imshow(pv, cmap='Blues'); ax.set(xticks=range(3), xticklabels=pv.columns, yticks=range(3), yticklabels=pv.index)
            fig.colorbar(im, ax=ax); ax.set_title('Matrix: mean score by course x centre\\n(heatmap)')
            fig.suptitle('One dataset, six questions, six chart types', fontsize=14)
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Six Questions Answered by Six Chart Types'),
    steps(
        ('Write the question in one sentence', '"Which…", "How has…", "Is there a relationship…".'),
        ('Identify the task', 'Compare, trend, distribution, relationship, composition, matrix.'),
        ('Pick the chart family', 'Bars, lines, histograms/boxes, scatter, stacked bars, heatmap.'),
        ('Encode the key comparison with position', 'Common baseline, aligned panels.'),
        ('Title with the answer', 'Then remove anything that does not support it.'),
        title='Steps to Choose a Chart'),
    crossq(
        ('Why is position more accurate than colour?', 'People compare positions along a common scale precisely, but judge colour shades and areas poorly (Cleveland & McGill).'),
        ('Bar chart or dot plot?', 'Dot plots work when the axis should not start at zero or there are many categories; bars must start at zero.'),
        ('When is a table better than a chart?', 'When readers need exact values or few numbers; charts are for patterns and comparisons.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What makes a chart misleading? Show truncated axes, manipulated dual axes and area distortion, and how to fix them.', 'Misleading Charts', minutes=9, cards=[
    definition(
        defbox('Common distortions: <strong>truncated bar axes</strong> (bars not starting at 0 exaggerate differences); <strong>dual y-axes</strong> whose '
               'ranges are chosen to create or hide a correlation; <strong>area/3-D effects</strong> where icons or 3-D pies scale in two dimensions so a 2× '
               'value looks 4×; <strong>inconsistent scales</strong> across panels; <strong>cherry-picked time windows</strong>; cumulative plots that always '
               'go up; and <strong>unlabelled or inverted axes</strong>.',
               'The <strong>lie factor</strong> = (size of effect shown) ÷ (size of effect in data); honest charts have a lie factor near 1. Fixes: zero '
               'baselines for bars (dot plots or lines if zero is irrelevant), shared scales, two panels instead of two axes, honest time windows, and '
               'labelled units.'),
        tags('truncated axis', 'dual axis', 'lie factor', '3-D charts', 'area distortion', 'cherry-picking', 'honest scales'),
    ),
    analogy('A misleading chart is a <strong>funhouse mirror</strong>: everything in it is real, but the shape is bent so you see what the maker wanted. The '
            'fix is a flat mirror — consistent scales and baselines.'),
    mislead_anim(),
    real_world(
        scenario('"Placement up dramatically!"',
                 p('A brochure draft shows Kharghar\'s placement rate towering over Pune\'s by using a y-axis starting at 28 %. The actual difference is 13 '
                   'percentage points (43 % vs 30 %), important but not the 7.6× gap the bars suggest. The coordinator replaces it with a zero-based bar chart.')),
    ),
    example(
        data_note(),
        vizrun("""
            r = df.groupby('centre')['placed'].mean().sort_values() * 100
            fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout='constrained')
            axes[0].bar(r.index, r, color='#ef4444'); axes[0].set_ylim(28, 44); axes[0].set_title('MISLEADING: y-axis starts at 28 %')
            axes[1].bar(r.index, r, color='#10b981'); axes[1].set_ylim(0, 50); axes[1].set_title('HONEST: zero baseline')
            for ax in axes: ax.set_ylabel('% placed')
            plt.show()
            shown = (r.max() - 28) / (r.min() - 28)
            print(f'data ratio Kharghar/Pune = {r.max() / r.min():.2f}; truncated bars ratio = {shown:.1f}; lie factor = {shown / (r.max() / r.min()):.1f}')

            months = pd.date_range('2026-02-01', periods=6, freq='MS').strftime('%b')
            att = np.array([84, 83, 79, 81, 80, 79]); pkg = np.array([6.1, 6.2, 6.3, 6.3, 6.4, 6.5])
            fig, axes = plt.subplots(1, 2, figsize=(11, 3.5), layout='constrained')
            ax = axes[0]; ax.plot(months, att, 'o-', color='#0ea5e9'); ax.set_ylim(78.5, 84.5)
            ax2 = ax.twinx(); ax2.plot(months, pkg, 's-', color='#ef4444'); ax2.set_ylim(6.0, 6.6)
            ax.set_title('MISLEADING: axes tuned to make the lines cross')
            ax = axes[1]
            ax.plot(months, att / att[0] * 100, 'o-', label='attendance'); ax.plot(months, pkg / pkg[0] * 100, 's-', label='mean package')
            ax.axhline(100, color='gray', linewidth=0.8); ax.legend(frameon=False)
            ax.set_title('HONEST: both indexed to Feb = 100')
            plt.show()

            fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), layout='constrained')
            for ax, mode in zip(axes, ['area', 'length']):
                for i, v in enumerate([1, 2]):                      # values 1 and 2
                    w = v if mode == 'area' else 1                   # area mode scales width AND height
                    ax.add_patch(plt.Rectangle((i * 2.6, 0), w, v, color='#f59e0b' if mode == 'area' else '#10b981'))
                ax.set(xlim=(-0.3, 5), ylim=(0, 2.3), aspect='equal'); ax.set_axis_off()
            axes[0].set_title('MISLEADING: value 2 drawn 2x wider AND taller\\n(4x area)')
            axes[1].set_title('HONEST: value 2 drawn 2x as long')
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Truncated Bars, Rigged Dual Axes, Area Distortion — and Honest Versions'),
    steps(
        ('Check baselines', 'Bars and areas start at zero.'),
        ('Check scales', 'Same scale across compared panels; label units.'),
        ('Avoid dual axes', 'Use two panels or index both series.'),
        ('Encode with one dimension', 'Length or position, not area or 3-D volume.'),
        ('Check the window', 'Show enough history; disclose what was filtered.'),
        title='Steps to Keep Charts Honest'),
    crossq(
        ('Is it ever OK not to start at zero?', 'For line charts and dot plots, yes, when the meaningful variation is far from zero (e.g. body temperature); never for bars or areas.'),
        ('What is the lie factor of the truncated chart here?', 'The bars show a ratio of 7.6 while the data ratio is 1.43: a lie factor of about 5.3.'),
        ('How can a chart mislead without changing axes?', 'Through selection (cherry-picked periods or groups), cumulative totals, missing denominators (counts instead of rates) or omitted uncertainty.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('What are good design practices for clear charts? Show a before/after makeover.', 'Chart Makeover & Best Practices', minutes=8, cards=[
    definition(
        defbox('Clear charts maximise the <strong>data-ink ratio</strong> (Tufte): remove heavy gridlines, borders, background fills, 3-D effects and redundant '
               'legends; keep only what carries information. Order categories meaningfully (by value), use horizontal bars for long labels, label lines and bars '
               'directly, and round numbers sensibly.',
               'Guide attention: grey for context and one <strong>accent colour</strong> for the point; a <strong>message title</strong> ("Kharghar leads '
               'placements") with a subtitle for details; annotations for the key fact; consistent fonts sized for the medium; accessible colours. Check: can '
               'someone state the message within five seconds?'),
        tags('data-ink ratio', 'declutter', 'accent colour', 'direct labels', 'message title', 'sorting', 'accessibility'),
    ),
    analogy('A chart makeover is <strong>editing a paragraph</strong>: cut words that do not add meaning, put the main point first, and highlight the one phrase '
            'the reader must remember.'),
    makeover_anim(),
    real_world(
        scenario('From default output to slide',
                 p('The default grouped bar chart with a legend, grid and unsorted categories becomes a sorted horizontal bar chart with direct labels, one accent '
                   'bar and a title stating the conclusion. The committee understands it before the presenter speaks.')),
    ),
    example(
        data_note(),
        vizrun("""
            r = (df.groupby('course')['placed'].mean() * 100)
            n = df.groupby('course').size()

            # BEFORE: defaults, unsorted, legend, heavy grid, vague title
            fig, ax = plt.subplots(figsize=(7, 4))
            for i, (c, v) in enumerate(r.items()):
                ax.bar(i, v, label=c)
            ax.set_xticks(range(3)); ax.set_xticklabels(r.index)
            ax.grid(True, color='black', linewidth=0.8); ax.legend(); ax.set_title('Data')
            ax.set_facecolor('#e5e7eb')
            plt.show()

            # AFTER: sorted, horizontal, grey + accent, direct labels, message title
            s = r.sort_values()
            colours = ['#cbd5e1'] * (len(s) - 1) + ['#0f766e']
            fig, ax = plt.subplots(figsize=(7, 3))
            bars = ax.barh(s.index, s, color=colours, height=0.6)
            ax.bar_label(bars, labels=[f'{v:.0f}%  (n={n[c]})' for c, v in s.items()], padding=4)
            ax.set_xlim(0, 50)
            ax.xaxis.set_visible(False)
            for side in ['top', 'right', 'bottom']:
                ax.spines[side].set_visible(False)
            ax.tick_params(left=False)
            fig.text(0.02, 1.02, f'{s.index[-1]} has the highest placement rate', fontsize=14, weight='bold')
            fig.text(0.02, 0.93, '% of students placed, by course, 2026 batch', fontsize=10, color='#475569')
            plt.show()
            print(s.round(1).to_dict())
        """, setup=STUDENTS, title=S),
        title='Example: The Same Data Before and After a Makeover'),
    steps(
        ('State the message', 'One sentence; make it the title.'),
        ('Remove non-data ink', 'Heavy grids, borders, backgrounds, 3-D, redundant legends.'),
        ('Order and orient', 'Sort by value; horizontal bars for labels.'),
        ('Highlight', 'Grey for context, one accent colour; direct labels.'),
        ('Check', 'Five-second test, greyscale test, readable at the final size.'),
        title='Steps for a Chart Makeover'),
    crossq(
        ('Why grey plus one accent colour instead of a colour per bar?', 'Different colours imply different meanings and compete for attention; one accent tells the eye exactly where to look.'),
        ('Is removing the x-axis acceptable?', 'Yes, when every bar is labelled with its value; the axis would only repeat that information.'),
        ('Why show n next to the rate?', 'Rates from small groups are less reliable; showing n lets readers judge that without a separate table.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('How do you plot large datasets without overplotting or slow, huge files? Explain alpha, hexbin, 2-D histograms and rasterization.', 'Large Data & Overplotting', minutes=8, cards=[
    definition(
        defbox('With tens of thousands of points, a scatter plot becomes a solid blob (<strong>overplotting</strong>): density and structure disappear. Remedies: '
               'tiny markers with low <code>alpha</code>; <strong>aggregation</strong> with <code>ax.hexbin(x, y, gridsize=..., bins=\'log\')</code> or '
               '<code>ax.hist2d</code>; 2-D KDE contours; or random <strong>sampling</strong> for exploration.',
               'Performance and file size: vector output (SVG/PDF) stores every point, so 200,000 markers make huge, slow files; '
               '<code>rasterized=True</code> on the heavy artist embeds it as an image while keeping text and axes as vectors. Plot aggregates (resampled, '
               'binned) instead of raw rows when the message is about patterns, and use Datashader or similar tools for millions of points.'),
        tags('overplotting', 'alpha', 'hexbin', 'hist2d', 'sampling', 'rasterized', 'file size', 'aggregation'),
    ),
    analogy('Overplotting is a <strong>crowded stadium photographed from above</strong>: you see a solid mass of heads. Counting people per section (hexbin) '
            'tells you where the crowd is densest.'),
    bigdata_anim(),
    real_world(
        scenario('Five years of lab-login events',
                 p('200,000 login records (session length vs hour of day) are a black rectangle as a plain scatter. A log-scaled hexbin shows the evening peak and '
                   'the cluster of very long sessions; the PDF version stays small because the hexbin layer is rasterized.')),
    ),
    example(
        vizrun("""
            import os, time
            rng = np.random.default_rng(0)
            n = 200_000
            hour = np.r_[rng.normal(11, 1.5, n // 2), rng.normal(18.5, 2, n // 2)] % 24
            minutes = rng.lognormal(3.5, 0.6, n) + (hour > 20) * rng.exponential(40, n)

            fig, axes = plt.subplots(1, 4, figsize=(15, 3.4), layout='constrained')
            t = time.perf_counter(); axes[0].scatter(hour, minutes, s=4); t0 = time.perf_counter() - t
            axes[0].set_title('plain scatter: a blob')
            axes[1].scatter(hour, minutes, s=1, alpha=0.03); axes[1].set_title('s=1, alpha=0.03')
            hb = axes[2].hexbin(hour, minutes, gridsize=40, bins='log', cmap='viridis'); axes[2].set_title("hexbin(bins='log')")
            fig.colorbar(hb, ax=axes[2], label='log10(count)')
            axes[3].hist2d(hour, minutes, bins=[48, 60], cmap='magma', cmin=1); axes[3].set_title('hist2d')
            for ax in axes:
                ax.set(xlabel='hour of day', ylim=(0, 250))
            axes[0].set_ylabel('session minutes')
            plt.show()

            for raster in [False, True]:
                f, ax = plt.subplots(figsize=(5, 3.5))
                ax.scatter(hour, minutes, s=1, alpha=0.05, rasterized=raster)
                name = f'scatter_raster_{raster}.pdf'
                t = time.perf_counter(); f.savefig(name); dt = time.perf_counter() - t
                print(f'rasterized={raster!s:5}: PDF {os.path.getsize(name) / 1024:8.0f} KB, saved in {dt:.2f} s')
                plt.close(f)
            print(f'points: {n:,}')
        """, title=P),
        title='Example: 200,000 Points — Blob, Alpha, Hexbin, hist2d; Rasterized vs Vector PDF'),
    steps(
        ('Count the points', 'Thousands → alpha/small markers; 100k+ → aggregate.'),
        ('Aggregate', 'hexbin / hist2d (log counts), or resample/bin before plotting.'),
        ('Sample for exploration', 'df.sample(n) when the full set is not needed.'),
        ('Rasterize heavy layers', 'rasterized=True for vector outputs.'),
        ('Scale up the tools', 'Datashader / database aggregation for millions of rows.'),
        title='Steps to Plot Large Data'),
    crossq(
        ('Why use bins="log" in hexbin?', 'Counts are often very skewed; a log colour scale shows both the dense core and the sparse outskirts.'),
        ('What does rasterized=True keep as vectors?', 'Only the marked artist becomes pixels; axes, ticks and text stay sharp vector graphics.'),
        ('Is sampling honest?', 'For showing overall patterns, a random sample is fine; rare events and extremes may disappear, so check them separately.'),
    ),
]),
])
