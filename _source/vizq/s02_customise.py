from build import *
from vizq.anims import *
from vizq.runner import vizrun, pyshow
from vizq.data import STUDENTS, data_note

S = 'Python (Matplotlib) · uses sample data'
P = 'Python (Matplotlib)'

SECTION = dict(level='basic', title='Layout & Customisation', questions=[

# ------------------------------------------------------------------ 6
Q('How do you arrange several plots in one figure? Explain subplots, sharex/sharey, layout engines and subplot_mosaic.', 'Subplots & Layouts', minutes=8, cards=[
    definition(
        defbox('<code>fig, axes = plt.subplots(nrows, ncols, figsize=...)</code> returns a grid of Axes as a NumPy array; index it (<code>axes[0, 1]</code>) or '
               'loop over <code>axes.flat</code>. <code>sharex=True / sharey=True</code> give panels a common scale, which is essential for fair visual '
               'comparison. <code>fig.suptitle</code> adds an overall title.',
               'Layout engines stop labels overlapping: <code>layout=\'constrained\'</code> (recommended) or <code>fig.tight_layout()</code>. For irregular '
               'layouts, <code>fig.subplot_mosaic("AAB;CCB")</code> names panels with letters (a panel can span cells), and <code>GridSpec</code> gives full '
               'control of width/height ratios. Remove unused panels with <code>ax.remove()</code> or <code>ax.axis(\'off\')</code>.'),
        tags('plt.subplots', 'axes.flat', 'sharex / sharey', 'constrained layout', 'tight_layout', 'subplot_mosaic', 'GridSpec'),
    ),
    analogy('A figure with subplots is a <strong>newspaper page</strong>: panels share one sheet, related panels line up on the same columns, and the layout '
            'engine is the editor who makes sure headlines never overlap the photos.'),
    subplots_anim(),
    real_world(
        scenario('One page per centre',
                 p('The monthly review shows, for each centre, the score distribution, attendance trend and placement rate. A 3 × 3 grid with shared y-axes per '
                   'column makes the centres directly comparable; a mosaic layout gives the most important chart a double-width panel.')),
    ),
    example(
        data_note(),
        vizrun("""
            fig, axes = plt.subplots(1, 3, figsize=(10, 3.2), sharey=True, layout='constrained')
            for ax, (centre, d) in zip(axes, df.groupby('centre')):
                ax.hist(d['final_score'], bins=15, color='#0ea5e9', edgecolor='white')
                ax.axvline(d['final_score'].median(), color='#ef4444', linewidth=2)
                ax.set_title(f'{centre} (median {d.final_score.median():.1f})')
                ax.set_xlabel('final score')
            axes[0].set_ylabel('students')
            fig.suptitle('Final scores by centre — shared y-axis')
            plt.show()
            print('axes array shape:', axes.shape)

            fig, axd = plt.subplot_mosaic('AAB;CCB', figsize=(10, 5), layout='constrained')
            axd['A'].scatter(df.study_hours, df.final_score, s=8, alpha=0.5)
            axd['A'].set(title='A: study hours vs final score', xlabel='hours', ylabel='score')
            rate = df.groupby('course')['placed'].mean().sort_values()
            axd['B'].barh(rate.index, rate * 100, color='#10b981')
            axd['B'].set(title='B: placement % by course')
            axd['C'].hist(df.attendance, bins=20, color='#f59e0b')
            axd['C'].set(title='C: attendance distribution', xlabel='attendance %')
            fig.suptitle("subplot_mosaic('AAB;CCB')")
            plt.show()
            print('mosaic panels:', sorted(axd))
        """, setup=STUDENTS, title=S),
        title='Example: A Shared-Axis Grid and a Mosaic Layout'),
    steps(
        ('Plan the grid', 'Rows × columns, or a mosaic string for spanning panels.'),
        ('Create with a layout engine', 'plt.subplots(..., layout="constrained").'),
        ('Share scales where comparing', 'sharex / sharey.'),
        ('Fill panels in a loop', 'for ax, group in zip(axes.flat, groups).'),
        ('Title the figure', 'fig.suptitle; remove empty panels.'),
        title='Steps to Build a Multi-Panel Figure'),
    crossq(
        ('Why share the y-axis?', 'Without it, each panel autoscales; a panel with smaller counts looks just as tall, and readers compare heights wrongly.'),
        ('constrained layout vs tight_layout?', 'Both prevent overlaps; constrained layout is applied automatically at draw time and handles colorbars and suptitles better.'),
        ('How do you make one panel twice as wide?', 'subplot_mosaic with a repeated letter ("AAB"), or GridSpec with width_ratios=[2, 1].'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('How do you control axes: limits, log scales, tick locations, tick formatting and secondary axes?', 'Axes, Ticks & Scales', minutes=8, cards=[
    definition(
        defbox('<strong>Limits</strong>: <code>ax.set_xlim / set_ylim</code> (or <code>ax.set(ylim=...)</code>). <strong>Scales</strong>: '
               '<code>ax.set_yscale(\'log\')</code> for data spanning orders of magnitude or for multiplicative change (equal steps = equal ratios); '
               '\'symlog\' handles zero and negatives.',
               '<strong>Ticks</strong> are controlled by locators and formatters from <code>matplotlib.ticker</code>: <code>MultipleLocator(5)</code>, '
               '<code>MaxNLocator</code>, <code>PercentFormatter</code>, <code>FuncFormatter</code> or a format string such as <code>\'{x:,.0f}\'</code>; '
               '<code>ax.tick_params</code> styles them. A <strong>secondary axis</strong> (<code>ax.twinx()</code>) plots a second variable with its own '
               'y-scale; <code>ax.secondary_xaxis</code> shows the same data in other units (e.g. LPA and ₹ per month).'),
        tags('set_xlim', 'log scale', 'ticker', 'MultipleLocator', 'PercentFormatter', 'twinx', 'secondary_xaxis'),
    ),
    analogy('Axes settings are the <strong>rulers of the chart</strong>: you choose where they start, whether each mark is "+10" or "×10", and how numbers are '
            'printed. A badly chosen ruler can make a small change look dramatic or a huge one look flat.'),
    ticks_anim(),
    real_world(
        scenario('Showing growth in applications',
                 p('Online applications grew from 120 to 15,000 over eight years. On a linear axis the early years are a flat line; a log axis shows the growth '
                   'rate each year, and formatted ticks ("15k") keep the chart readable.')),
    ),
    example(
        data_note(),
        vizrun("""
            from matplotlib.ticker import PercentFormatter, MultipleLocator, FuncFormatter
            years = np.arange(2019, 2027)
            apps = np.array([120, 260, 610, 1300, 2900, 5100, 9400, 15000])
            fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout='constrained')
            for ax, scale in zip(axes, ['linear', 'log']):
                ax.plot(years, apps, 'o-')
                ax.set_yscale(scale)
                ax.set_title(f'{scale} scale')
                ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v / 1000:.0f}k' if v >= 1000 else f'{v:.0f}'))
            fig.suptitle('Online applications per year')
            plt.show()
            print('year-on-year growth:', (apps[1:] / apps[:-1]).round(2))

            rate = df.groupby('course')['placed'].mean()
            mean_score = df.groupby('course')['final_score'].mean()
            fig, ax = plt.subplots(figsize=(7, 3.8))
            ax.bar(rate.index, rate, color='#0ea5e9', label='placement rate')
            ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
            ax.set(ylim=(0, 0.6), ylabel='placement rate')
            ax2 = ax.twinx()
            ax2.plot(mean_score.index, mean_score, 'o-', color='#ef4444', label='mean final score')
            ax2.set(ylim=(50, 65), ylabel='mean final score')
            ax2.yaxis.set_major_locator(MultipleLocator(5))
            ax.set_title('twinx: two y-axes (read carefully: both scales are arbitrary)')
            fig.legend(loc='upper right', bbox_to_anchor=(0.88, 0.88), frameon=False)
            plt.show()

            fig, ax = plt.subplots(figsize=(7, 2.8))
            ax.hist(df.salary_lpa.dropna(), bins=30, color='#10b981')
            ax.set(xlabel='package (LPA)', title='secondary_xaxis: the same values in Rs per month')
            sec = ax.secondary_xaxis('top', functions=(lambda l: l * 1e5 / 12 / 1000, lambda k: k * 1000 * 12 / 1e5))
            sec.set_xlabel('approx. Rs thousand per month')
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Linear vs Log Axis, Percent Formatting, twinx and a Unit-Conversion Axis'),
    steps(
        ('Decide the scale', 'Linear for differences; log for ratios or wide ranges.'),
        ('Set limits deliberately', 'Zero baseline for bars; sensible padding for lines.'),
        ('Format ticks', 'PercentFormatter, thousands separators, units.'),
        ('Use secondary axes sparingly', 'Unit conversions are safe; two unrelated variables invite misreading.'),
        ('Label units clearly', 'Especially on log or secondary axes.'),
        title='Steps to Control Axes'),
    crossq(
        ('When is a log scale appropriate?', 'When values span orders of magnitude, or when you care about relative change (growth rates): a straight line on a log axis means constant percentage growth.'),
        ('Why are dual y-axes risky?', 'Each axis range is arbitrary; by changing them you can make two series appear to cross or move together. Prefer two panels or indexed values.'),
        ('How do you put a percent sign on tick labels?', 'ax.yaxis.set_major_formatter(PercentFormatter(xmax=1)) for 0–1 data (xmax=100 for 0–100).'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('How do you choose colours and colormaps? Explain sequential, diverging and qualitative palettes and colour-blind safety.', 'Colours & Colormaps', minutes=8, cards=[
    definition(
        defbox('Match the palette to the data: <strong>qualitative</strong> (categorical: tab10, Set2) for unordered groups — distinct hues, no implied order; '
               '<strong>sequential</strong> (viridis, Blues) for ordered magnitudes from low to high; <strong>diverging</strong> (RdBu, coolwarm) for values around a '
               'meaningful midpoint such as 0, a target or a correlation of 0 — set <code>vmin/vmax</code> symmetric or use <code>TwoSlopeNorm</code>.',
               'Prefer <strong>perceptually uniform</strong> maps (viridis, cividis, magma) over rainbow ("jet"), which creates false boundaries and fails in '
               'greyscale and for colour-blind readers (about 8 % of men). Use colour purposefully: grey for context, one accent colour for the message. '
               'Colours can be names, hex (<code>\'#0ea5e9\'</code>) or palette lookups (<code>plt.get_cmap(\'viridis\')(0.3)</code>).'),
        tags('qualitative', 'sequential', 'diverging', 'viridis', 'colormap', 'TwoSlopeNorm', 'colour-blind safe', 'highlight colour'),
    ),
    analogy('Colour is a <strong>volume knob</strong>, not decoration. Turn it up (a bright accent) only for what you want the reader to notice; keep everything '
            'else at background volume (grey).'),
    colour_anim(),
    real_world(
        scenario('A correlation heatmap that reads correctly',
                 p('In a correlation matrix, 0 means "no relationship" and ±1 means strong. A diverging RdBu map centred at 0 (vmin −1, vmax 1) shows positive and '
                   'negative correlations as opposite hues; a rainbow map would make 0.4 and 0.6 look like different categories.')),
    ),
    example(
        data_note(),
        vizrun("""
            from matplotlib.colors import TwoSlopeNorm
            grad = np.linspace(0, 1, 256)[None, :]
            maps = ['tab10', 'viridis', 'Blues', 'RdBu', 'jet']
            fig, axes = plt.subplots(len(maps), 1, figsize=(7, 3.2), layout='constrained')
            for ax, m in zip(axes, maps):
                ax.imshow(grad, aspect='auto', cmap=m)
                ax.set_axis_off()
                ax.text(-0.01, 0.5, m, transform=ax.transAxes, ha='right', va='center')
            fig.suptitle('qualitative · sequential · sequential · diverging · rainbow (avoid)')
            plt.show()

            cols = ['attendance', 'study_hours', 'pre_test', 'post_test', 'final_score']
            corr = df[cols].corr()
            fig, ax = plt.subplots(figsize=(6, 4.6))
            im = ax.imshow(corr, cmap='RdBu_r', norm=TwoSlopeNorm(vcenter=0, vmin=-1, vmax=1))
            ax.set(xticks=range(len(cols)), yticks=range(len(cols)))
            ax.set_xticklabels(cols, rotation=40, ha='right'); ax.set_yticklabels(cols)
            for i in range(len(cols)):
                for j in range(len(cols)):
                    ax.text(j, i, f'{corr.iloc[i, j]:.2f}', ha='center', va='center', fontsize=8,
                            color='white' if abs(corr.iloc[i, j]) > 0.6 else 'black')
            fig.colorbar(im, ax=ax, label='correlation')
            ax.set_title('Diverging map centred at 0')
            plt.show()

            rate = df.groupby('course')['placed'].mean().sort_values()
            colours = ['#cbd5e1' if c != 'PG-DBDA' else '#0ea5e9' for c in rate.index]
            fig, ax = plt.subplots(figsize=(6, 2.6))
            ax.barh(rate.index, rate * 100, color=colours)
            ax.set(title='One accent colour, everything else grey', xlabel='% placed')
            plt.show()
            print('viridis RGB at 0.0, 0.5, 1.0:', [tuple(round(float(c), 2) for c in plt.get_cmap('viridis')(v)[:3]) for v in (0.0, 0.5, 1.0)])
        """, setup=STUDENTS, title=S),
        title='Example: Palette Types, a Centred Diverging Heatmap, and an Accent Colour'),
    steps(
        ('Identify the data type', 'Categories, ordered magnitudes, or deviations from a midpoint.'),
        ('Pick the palette family', 'Qualitative, sequential or diverging.'),
        ('Prefer perceptually uniform maps', 'viridis / cividis; never jet for magnitudes.'),
        ('Fix the colour scale', 'vmin/vmax shared across panels; centre diverging maps.'),
        ('Check accessibility', 'Greyscale print and colour-blind simulators; add labels, not colour alone.'),
        title='Steps to Choose Colours'),
    crossq(
        ('Why is the rainbow (jet) colormap discouraged?', 'Its lightness is not monotonic, so it creates false bands, hides real ones, distorts magnitudes and fails for colour-blind readers and in greyscale.'),
        ('Why must several heatmaps share vmin and vmax?', 'Otherwise the same colour means different values in each panel and comparisons are wrong.'),
        ('How many qualitative colours can readers distinguish?', 'Roughly 6–8; beyond that, group categories into "Other" or use small multiples.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('How do you annotate a chart? Explain text, arrows, reference lines and shaded regions.', 'Annotations', minutes=7, cards=[
    definition(
        defbox('Annotations turn a chart into an explanation. <code>ax.annotate(text, xy=point, xytext=label_position, arrowprops=dict(...))</code> points at a '
               'data value; <code>ax.text(x, y, s)</code> writes text in data coordinates, or in axes coordinates with <code>transform=ax.transAxes</code> '
               '(0–1, independent of the data).',
               'Reference elements: <code>ax.axhline / axvline</code> for targets, averages or events; <code>ax.axhspan / axvspan</code> to shade a range (an exam '
               'week, a "pass" zone); <code>ax.fill_between</code> for bands. Keep annotations few and close to what they explain; the title can state the '
               'conclusion ("Attendance fell 15 points during exam-prep week").'),
        tags('ax.annotate', 'arrowprops', 'ax.text', 'transAxes', 'axhline', 'axvspan', 'storytelling'),
    ),
    analogy('Annotations are a <strong>teacher\'s chalk marks on the board</strong>: the diagram is the same, but the circled point, the arrow and the note '
            'beside it tell the class exactly where to look.'),
    annotate_anim(),
    real_world(
        scenario('Explaining an attendance dip',
                 p('The weekly attendance chart for the governing council shades the exam-preparation week, marks the 80 % target, and points an arrow at the '
                   'lowest day with a short note. Nobody has to ask "what happened there?".')),
    ),
    example(
        vizrun("""
            rng = np.random.default_rng(3)
            days = pd.bdate_range('2026-03-02', '2026-05-29')
            rate = 0.86 - np.linspace(0, 0.04, len(days)) + rng.normal(0, 0.02, len(days))
            rate[(days >= '2026-04-13') & (days <= '2026-04-17')] -= 0.15
            s = pd.Series(rate, index=days)

            fig, ax = plt.subplots(figsize=(9, 4))
            ax.plot(s.index, s * 100, color='#0ea5e9')
            ax.axhline(80, color='#ef4444', linestyle='--', linewidth=1)
            ax.text(s.index[1], 80.6, 'target 80 %', color='#ef4444')
            ax.axvspan(pd.Timestamp('2026-04-13'), pd.Timestamp('2026-04-17'), color='#f59e0b', alpha=0.2)
            low = s.idxmin()
            ax.annotate(f'lowest: {s.min() * 100:.0f} % on {low:%d %b}', xy=(low, s.min() * 100), xytext=(low + pd.Timedelta(days=12), 66),
                        arrowprops=dict(arrowstyle='->', color='black'), fontsize=10)
            ax.text(0.01, 0.04, 'shaded: exam-prep week', transform=ax.transAxes, color='#b45309')
            ax.set(title='Attendance fell about 15 points during exam-prep week', ylabel='attendance %', ylim=(60, 95))
            ax.spines[['top', 'right']].set_visible(False)
            plt.show()
            print(f'lowest day {low.date()} at {s.min():.3f}')
        """, title=P),
        title='Example: Target Line, Shaded Week, Arrow to the Minimum, Axes-Coordinate Note'),
    steps(
        ('Decide the message', 'Put it in the title.'),
        ('Add references', 'Targets and averages with axhline; events with axvline / axvspan.'),
        ('Point at the key data', 'ax.annotate with an arrow and short text.'),
        ('Place notes in axes coordinates', 'transform=ax.transAxes for fixed positions.'),
        ('Remove what distracts', 'Extra gridlines, spines, unused legends.'),
        title='Steps to Annotate a Chart'),
    crossq(
        ('Data coordinates vs axes coordinates?', 'Data coordinates move with the data (x = a date, y = 80 %); axes coordinates are fractions of the plot box (0.01, 0.04 = bottom-left) and stay put.'),
        ('How many annotations are too many?', 'When they compete with the data. Two or three that support one message usually work best.'),
        ('Why state the conclusion in the title?', 'Readers read titles first; a descriptive title ("Attendance") makes them work out the point, a message title tells them.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('How do you apply styles and save figures for reports? Explain style sheets, rcParams, DPI and file formats.', 'Styles & Saving Figures', minutes=8, cards=[
    definition(
        defbox('<strong>Style sheets</strong> (<code>plt.style.use(\'ggplot\')</code>, \'seaborn-v0_8-whitegrid\', \'fivethirtyeight\'…) set many defaults at once; '
               '<code>with plt.style.context(...)</code> applies one temporarily. <strong>rcParams</strong> (<code>plt.rcParams[\'font.size\'] = 11</code>) '
               'change individual defaults; a <code>matplotlibrc</code> file or a helper function gives a whole team the same house style.',
               '<code>fig.savefig(path, dpi=..., bbox_inches=\'tight\', transparent=...)</code>: <strong>PNG</strong> (raster; dpi 150–300 for print, 100 for '
               'screens) for slides and web; <strong>SVG/PDF</strong> (vector: sharp at any zoom, editable) for reports and papers; JPEG is poor for line art. '
               'Set <code>figsize</code> in inches to the final size so fonts are not shrunk later.'),
        tags('plt.style.use', 'style.context', 'rcParams', 'savefig', 'dpi', 'bbox_inches', 'PNG vs SVG vs PDF'),
    ),
    analogy('A style sheet is the <strong>institution\'s letterhead template</strong>: everyone writes their own content, but fonts, colours and margins match. '
            'Saving as SVG/PDF is sending the editable original; PNG is sending a photograph of it.'),
    style_anim(),
    real_world(
        scenario('Charts for the annual report',
                 p('The design team asks for all charts in the institute style (teal accent, no top/right borders, 11-point font) as PDF for print and PNG for the '
                   'website. A small style helper plus one savefig call per format produces both consistently.')),
    ),
    example(
        data_note(),
        vizrun("""
            import os
            rate = df.groupby('centre')['placed'].mean().sort_values() * 100
            for style in ['default', 'ggplot', 'seaborn-v0_8-whitegrid', 'fivethirtyeight']:
                with plt.style.context(style):
                    fig, ax = plt.subplots(figsize=(4.5, 2.6))
                    ax.barh(rate.index, rate)
                    ax.set_title(f'style: {style}', fontsize=10)

            house = {'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.prop_cycle': plt.cycler(color=['#0f766e', '#94a3b8', '#f59e0b']), 'axes.titleweight': 'bold'}
            with plt.rc_context(house):
                fig, ax = plt.subplots(figsize=(4.5, 2.6))
                ax.barh(rate.index, rate)
                ax.set_title('house style via rc_context')
                for fmt, dpi in [('png', 100), ('png', 300), ('svg', None), ('pdf', None)]:
                    name = f'placement_{dpi or "vec"}.{fmt}'
                    fig.savefig(name, dpi=dpi or 'figure', bbox_inches='tight')
                    print(f'{name:22} {os.path.getsize(name) / 1024:6.1f} KB')
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Four Built-in Styles, a House Style, and File Sizes per Format'),
    steps(
        ('Pick or define a style', 'Built-in style sheet or a house rc dictionary.'),
        ('Apply consistently', 'plt.style.use at the top, or rc_context / style.context per figure.'),
        ('Size for the destination', 'figsize in inches matching the slide or page.'),
        ('Save in the right format', 'PNG (dpi 150–300) for slides/web; SVG/PDF for print and editing.'),
        ('Use bbox_inches="tight"', 'So labels are not cut off.'),
        title='Steps to Style and Save Figures'),
    crossq(
        ('Why does a chart look blurry in a printed report?', 'A low-dpi PNG was enlarged. Save at 300 dpi or, better, as PDF/SVG vector graphics.'),
        ('Why save at the final size instead of scaling later?', 'Scaling an image also scales fonts and line widths; a 12-inch figure shrunk to 4 inches has unreadable labels.'),
        ('When is PNG better than SVG?', 'For plots with tens of thousands of points: vector files store every marker and become huge and slow; raster files stay small.'),
    ),
]),
])
