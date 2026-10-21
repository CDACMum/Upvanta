from build import *
from vizq.anims import *
from vizq.runner import vizrun, pyshow
from vizq.data import STUDENTS, data_note

S = 'Python (Matplotlib) · uses sample data'
P = 'Python (Matplotlib)'

SECTION = dict(level='beginner', title='Matplotlib Fundamentals', questions=[

# ------------------------------------------------------------------ 1
Q('What is the anatomy of a Matplotlib figure? Explain Figure, Axes, Axis and the pyplot vs object-oriented interfaces.', 'Figure, Axes & the Two APIs', minutes=8, cards=[
    definition(
        defbox('A <strong>Figure</strong> is the whole canvas (the image or window). It contains one or more <strong>Axes</strong>: each Axes is one plot with its '
               'own data area, title and two <strong>Axis</strong> objects (x and y) that manage ticks and labels. Everything drawn — lines, bars, text, legends — '
               'is an <strong>Artist</strong>.',
               'Two interfaces: <strong>pyplot</strong> (<code>plt.plot(...)</code>, <code>plt.title(...)</code>) acts on the "current" Axes, convenient for quick '
               'plots; the <strong>object-oriented (OO)</strong> interface (<code>fig, ax = plt.subplots()</code>, <code>ax.plot(...)</code>, '
               '<code>ax.set_title(...)</code>) names every object explicitly and is the recommended style for anything with more than one plot, functions '
               'that draw on a given Axes, and reusable code.'),
        tags('Figure', 'Axes', 'Axis', 'Artist', 'pyplot', 'object-oriented API', 'plt.subplots'),
    ),
    analogy('A Figure is a <strong>sheet of chart paper</strong>; each Axes is a <strong>graph box drawn on it</strong>; the Axis objects are the rulers along '
            'the edges. pyplot is "draw on whichever box I touched last"; the OO style is "draw in box number 2".'),
    anatomy_anim(),
    real_world(
        scenario('Weekly report figures',
                 p('A coordinator\'s script draws the same three panels every week. Written in the OO style, each panel is a function that receives an Axes, so the '
                   'panels can be rearranged, reused in other reports and tested independently, without plots accidentally drawing on the wrong panel.')),
    ),
    example(
        data_note(),
        vizrun("""
            # pyplot style: quick, acts on the "current" axes
            plt.figure(figsize=(6, 3.5))
            plt.plot(['Feb', 'Mar', 'Apr', 'May'], [52, 58, 61, 66], marker='o')
            plt.title('pyplot style: mock-test average by month')
            plt.xlabel('month'); plt.ylabel('average score')
            plt.show()

            # object-oriented style: explicit figure and axes objects
            fig, ax = plt.subplots(figsize=(6, 3.5))
            line, = ax.plot(['Feb', 'Mar', 'Apr', 'May'], [52, 58, 61, 66], marker='o', label='mock test')
            ax.set(title='OO style: same chart', xlabel='month', ylabel='average score')
            ax.legend()
            print(type(fig).__name__, type(ax).__name__, type(line).__name__)
            print('axes in figure:', len(fig.axes), '| x-axis object:', type(ax.xaxis).__name__)
            print('artists on the axes:', len(ax.get_children()))
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: The Same Chart in pyplot and OO Style'),
    steps(
        ('Import', '<code>import matplotlib.pyplot as plt</code>.'),
        ('Create figure and axes', '<code>fig, ax = plt.subplots(figsize=(w, h))</code>.'),
        ('Draw on the axes', 'ax.plot / ax.bar / ax.scatter / ax.hist.'),
        ('Label', 'ax.set(title=..., xlabel=..., ylabel=...), ax.legend().'),
        ('Show or save', 'plt.show() in notebooks/scripts; fig.savefig("chart.png", dpi=150).'),
        title='Steps to Create a Figure'),
    crossq(
        ('Why prefer the OO interface?', 'With several subplots or helper functions, "current axes" state causes plots to land in the wrong place; explicit ax objects avoid that and make code reusable.'),
        ('What does plt.subplots() return?', 'A Figure and an Axes (or a NumPy array of Axes for a grid).'),
        ('What is the difference between Axes and Axis?', 'Axes is a whole plot area; Axis is one of its x/y rulers with ticks and tick labels.'),
        ('Why does a script sometimes show nothing?', 'In a non-interactive script you must call plt.show() (or savefig); notebooks display figures automatically.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('How do you create and customise line plots? Explain markers, line styles, labels and legends.', 'Line Plots', minutes=7, cards=[
    definition(
        defbox('<code>ax.plot(x, y)</code> draws a line connecting points in order; use it for <strong>ordered</strong> x values such as time, so the slope '
               'means change. Style with <code>color</code>, <code>linestyle</code> (\'-\', \'--\', \':\', \'-.\'), <code>linewidth</code>, <code>marker</code> '
               '(\'o\', \'s\', \'^\') and <code>alpha</code>; the shorthand format string <code>\'o--\'</code> combines marker and style.',
               'Give every line a <code>label=</code> and call <code>ax.legend()</code> (or label lines directly at their ends). Set axis labels with units, '
               'a title that states the message, and grid lines lightly (<code>ax.grid(alpha=0.3)</code>). Several lines on one Axes compare trends; more than '
               'about five lines become spaghetti — use small multiples instead.'),
        tags('ax.plot', 'linestyle', 'marker', 'label', 'legend', 'grid', 'format string'),
    ),
    analogy('A line chart is a <strong>route on a map</strong>: the order of the points matters and the line between them suggests continuity. Joining '
            'unordered categories with a line invents a journey that never happened.'),
    line_anim(),
    real_world(
        scenario('Mock-test trends per course',
                 p('Monthly average mock-test scores for PG-DBDA, PG-DAC and PG-DAI on one chart show which course is improving fastest. A dashed target line at '
                   '60 marks makes the gap to the goal obvious at a glance.')),
    ),
    example(
        vizrun("""
            months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
            scores = {'PG-DBDA': [54, 57, 60, 63, 65, 68],
                      'PG-DAC':  [56, 57, 58, 58, 60, 61],
                      'PG-DAI':  [50, 55, 59, 61, 66, 70]}
            fig, ax = plt.subplots(figsize=(7, 4))
            for (course, ys), m in zip(scores.items(), ['o', 's', '^']):
                ax.plot(months, ys, marker=m, linewidth=2, label=course)
            ax.axhline(60, color='gray', linestyle='--', linewidth=1, label='target 60')
            ax.set(title='Average mock-test score by month', xlabel='month (2026)', ylabel='average score', ylim=(45, 75))
            ax.grid(alpha=0.3)
            ax.legend(loc='upper left', frameon=False)
            plt.show()

            # format-string shorthand and direct labels instead of a legend
            fig, ax = plt.subplots(figsize=(7, 4))
            for course, ys in scores.items():
                ax.plot(months, ys, 'o-', linewidth=2)
                ax.annotate(course, (months[-1], ys[-1]), xytext=(6, 0), textcoords='offset points', va='center')
            ax.set(title='Direct labels: no legend lookup needed', ylabel='average score')
            ax.spines[['top', 'right']].set_visible(False)
            plt.show()
        """, title=P),
        title='Example: Three Courses, a Target Line, Legend vs Direct Labels'),
    steps(
        ('Order the x values', 'Time or another ordered variable.'),
        ('Plot each series', 'ax.plot(x, y, marker=..., label=...).'),
        ('Add references', 'ax.axhline for targets or averages.'),
        ('Label everything', 'Title with the message, axis labels with units, legend or direct labels.'),
        ('Reduce clutter', 'Light grid, remove top/right spines, limit to about five lines.'),
        title='Steps for a Clear Line Chart'),
    crossq(
        ('When should you not use a line chart?', 'For unordered categories (centres, courses): the connecting line implies a progression. Use bars or dots.'),
        ('Legend or direct labels?', 'Direct labels at line ends save eye movement and work in greyscale; legends are fine for many short series in a consistent position.'),
        ('How do you plot two lines with very different scales?', 'Prefer two panels or indexing both to 100; a secondary axis (ax.twinx()) is possible but easily misread.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('How do you build bar charts: horizontal, grouped and stacked? How do you add value labels?', 'Bar Charts', minutes=8, cards=[
    definition(
        defbox('<code>ax.bar(x, height)</code> and <code>ax.barh(y, width)</code> compare <strong>quantities across categories</strong>. Bars must start at '
               'zero, because their length encodes the value. Use horizontal bars for long category names or many categories, and sort bars by value unless '
               'the categories have a natural order.',
               '<strong>Grouped</strong> bars place series side by side (offset x positions by a bar width); <strong>stacked</strong> bars place them on top '
               'of each other with <code>bottom=</code> to show parts of a total (only the bottom segment is easy to compare). <code>ax.bar_label(container, '
               'fmt=...)</code> writes values on bars. pandas: <code>df.plot.bar(stacked=True)</code>.'),
        tags('ax.bar', 'ax.barh', 'grouped bars', 'stacked bars', 'bar_label', 'zero baseline', 'sorting'),
    ),
    analogy('Bars are <strong>stacks of coins</strong>: you compare heights, so every stack must start on the same table. Stacked bars are coins of different '
            'colours in one stack — easy to see the total, harder to compare the middle colours.'),
    bar_anim(),
    real_world(
        scenario('Placement rate per centre and course',
                 p('A sorted horizontal bar chart of placement rate by centre answers "who is ahead?"; grouped bars by course inside each centre answer "is the '
                   'ranking the same in every course?"; a stacked bar of placed / not placed counts shows batch sizes too.')),
    ),
    example(
        data_note(),
        vizrun("""
            rate = df.groupby('centre')['placed'].mean().sort_values()
            fig, ax = plt.subplots(figsize=(6, 3))
            bars = ax.barh(rate.index, rate.values * 100, color='#0ea5e9')
            ax.bar_label(bars, fmt='%.1f%%', padding=3)
            ax.set(title='Placement rate by centre', xlabel='% placed', xlim=(0, 50))
            plt.show()
            print(rate.round(3).to_dict())

            tab = df.pivot_table(index='centre', columns='course', values='placed', aggfunc='mean') * 100
            x = np.arange(len(tab.index)); w = 0.27
            fig, ax = plt.subplots(figsize=(7, 4))
            for i, course in enumerate(tab.columns):
                b = ax.bar(x + (i - 1) * w, tab[course], width=w, label=course)
                ax.bar_label(b, fmt='%.0f', fontsize=8)
            ax.set(xticks=x, xticklabels=tab.index, ylabel='% placed', title='Grouped: placement rate by centre and course')
            ax.legend(frameon=False)
            plt.show()

            counts = pd.crosstab(df['centre'], df['placed']).rename(columns={0: 'not placed', 1: 'placed'})
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.bar(counts.index, counts['placed'], label='placed', color='#10b981')
            ax.bar(counts.index, counts['not placed'], bottom=counts['placed'], label='not placed', color='#cbd5e1')
            ax.set(ylabel='students', title='Stacked: placed and not placed per centre')
            ax.legend(frameon=False)
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Sorted Horizontal, Grouped and Stacked Bars with Labels'),
    steps(
        ('Aggregate first', 'groupby / pivot_table to one value per bar.'),
        ('Choose orientation and order', 'barh for long names; sort by value.'),
        ('Draw', 'ax.bar / ax.barh; offsets for grouped, bottom= for stacked.'),
        ('Label values', 'ax.bar_label(bars, fmt=...).'),
        ('Keep the zero baseline', 'Never truncate the value axis of a bar chart.'),
        title='Steps for a Bar Chart'),
    crossq(
        ('Why must bars start at zero?', 'The eye reads bar length; a truncated axis makes a 3 % difference look like 300 %.'),
        ('Grouped or stacked?', 'Grouped to compare the series against each other; stacked to show totals and composition (only the bottom segment and the total are easy to compare).'),
        ('How do you show percentages that sum to 100 % per group?', 'A 100 % stacked bar (normalise each row), or better, side-by-side bars of the share of interest.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('How do you plot a distribution with a histogram? How do bins, density and cumulative options change it?', 'Histograms', minutes=8, cards=[
    definition(
        defbox('A <strong>histogram</strong> (<code>ax.hist(x, bins=...)</code>) divides the range into bins and draws the count in each bin; it shows '
               'centre, spread, skew, gaps and outliers of <strong>one numeric variable</strong>. The <strong>bin width</strong> changes the story: too few '
               'bins hide structure, too many show noise. <code>bins</code> can be a number, explicit edges, or a rule (\'auto\', \'fd\', \'sturges\').',
               '<code>density=True</code> scales bars so their total area is 1 (compare groups of different size, overlay a density curve); '
               '<code>cumulative=True</code> (or the step-free <code>ax.ecdf</code>) shows the share below each value; <code>histtype=\'step\'</code> and <code>alpha</code> let you overlay several '
               'groups. <code>ax.hist</code> returns counts and edges so you can print them.'),
        tags('ax.hist', 'bins', 'bin width', 'density', 'cumulative', 'histtype', 'distribution'),
    ),
    analogy('A histogram is <strong>sorting marbles into cups by size</strong> and lining the cups up. Use too few cups and every marble lands in one or two; '
            'too many and most cups hold zero or one marble.'),
    hist_anim(),
    real_world(
        scenario('Is the final exam well calibrated?',
                 p('Before declaring results, the exam cell looks at the histogram of final scores: a pile-up at 100 suggests the paper was too easy, a gap around '
                   'the pass mark can reveal moderation effects, and a long right tail in packages warns against reporting only the mean.')),
    ),
    example(
        data_note(),
        vizrun("""
            fig, axes = plt.subplots(1, 3, figsize=(11, 3.2), sharey=False)
            for ax, b in zip(axes, [5, 20, 120]):
                counts, edges, _ = ax.hist(df['final_score'], bins=b, color='#0ea5e9', edgecolor='white')
                ax.set_title(f'{b} bins (width {edges[1] - edges[0]:.1f})')
            fig.suptitle('Same data, three bin choices')
            fig.tight_layout()
            plt.show()

            counts, edges = np.histogram(df['final_score'], bins='fd')
            print(f"Freedman-Diaconis rule chose {len(counts)} bins of width {edges[1] - edges[0]:.2f}")

            fig, ax = plt.subplots(figsize=(7, 3.8))
            for method, colour in [('traditional', '#94a3b8'), ('flipped', '#10b981')]:
                ax.hist(df.loc[df.method == method, 'post_test'], bins=20, density=True, alpha=0.55, label=method, color=colour)
            ax.set(title='Post-test by teaching method (density, overlaid)', xlabel='post-test score', ylabel='density')
            ax.legend(frameon=False)
            plt.show()

            fig, ax = plt.subplots(figsize=(7, 3.5))
            ax.ecdf(df['salary_lpa'].dropna(), linewidth=2)            # empirical cumulative distribution (Matplotlib >= 3.8)
            ax.axhline(0.5, color='gray', linestyle=':')
            ax.set(title='Cumulative share of packages (half are at or below the median)', xlabel='package (LPA)', ylabel='share at or below')
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Bin Choice, Overlaid Densities and a Cumulative Distribution'),
    steps(
        ('Pick one numeric variable', 'Drop or report missing values.'),
        ('Choose bins deliberately', 'Try a rule (\'fd\', \'auto\') and a couple of alternatives.'),
        ('Compare groups fairly', 'density=True, shared bins, alpha or step outlines.'),
        ('Add references', 'Mean/median or a pass mark with ax.axvline.'),
        ('Describe the shape', 'Centre, spread, skew, modes, outliers.'),
        title='Steps for a Histogram'),
    crossq(
        ('Histogram vs bar chart?', 'A histogram shows a continuous variable split into adjacent bins (no gaps, x is numeric); a bar chart compares separate categories.'),
        ('Why use density=True when comparing groups?', 'Groups of different size would otherwise differ in bar height just because one has more students.'),
        ('What is a KDE?', 'A smoothed estimate of the density (seaborn kdeplot); it removes bin choice but adds a bandwidth choice and can show values outside the possible range.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('How do scatter plots show relationships? How do you encode extra variables with colour and size?', 'Scatter Plots', minutes=8, cards=[
    definition(
        defbox('<code>ax.scatter(x, y)</code> places one mark per observation and shows the <strong>relationship between two numeric variables</strong>: '
               'direction, strength, shape (linear or curved), clusters and outliers. A third variable can be encoded with colour (<code>c=</code> plus '
               '<code>cmap</code> and <code>fig.colorbar</code> for numbers; one call per group with <code>label=</code> for categories) and a fourth with '
               'size (<code>s=</code>).',
               'With many points, <strong>overplotting</strong> hides density: use small markers, <code>alpha</code>, or hexbin / 2-D histograms. Add a '
               'trend line (<code>np.polyfit</code>) to guide the eye, and keep extra encodings to a minimum — two or three variables per chart are readable, '
               'five are not.'),
        tags('ax.scatter', 'colour encoding', 'colormap', 'colorbar', 'marker size', 'alpha', 'trend line', 'overplotting'),
    ),
    analogy('A scatter plot is a <strong>night sky</strong>: each star is a student. You look for constellations (clusters), the Milky Way (a trend) and the '
            'odd lone star far from the rest (an outlier).'),
    scatter_anim(),
    real_world(
        scenario('Study hours versus results',
                 p('A scatter of study hours against final score, coloured by attendance, shows that the best results need both: students who study a lot but '
                   'rarely attend sit below the trend line, which is exactly the group mentors should talk to.')),
    ),
    example(
        data_note(),
        vizrun("""
            fig, ax = plt.subplots(figsize=(7, 4.5))
            sc = ax.scatter(df['study_hours'], df['final_score'], c=df['attendance'], cmap='viridis', s=18, alpha=0.8)
            fig.colorbar(sc, ax=ax, label='attendance %')
            slope, intercept = np.polyfit(df['study_hours'], df['final_score'], 1)
            xs = np.linspace(0, df['study_hours'].max(), 50)
            ax.plot(xs, intercept + slope * xs, color='#ef4444', linewidth=2, label=f'trend: {slope:.2f} marks / hour')
            ax.set(title='Study hours vs final score (colour = attendance)', xlabel='weekly study hours', ylabel='final score')
            ax.legend(frameon=False)
            plt.show()
            print(f'correlation {np.corrcoef(df.study_hours, df.final_score)[0, 1]:.3f}')

            fig, ax = plt.subplots(figsize=(7, 4.5))
            for centre, colour in zip(['Kharghar', 'Juhu', 'Pune'], ['#0ea5e9', '#f59e0b', '#10b981']):
                d = df[df.centre == centre]
                ax.scatter(d['post_test'], d['final_score'], s=d['study_hours'] * 4, alpha=0.5, color=colour, label=centre)
            ax.set(title='Post-test vs final score (colour = centre, size = study hours)', xlabel='post-test', ylabel='final score')
            ax.legend(frameon=False, markerscale=0.6)
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Colour by a Number with a Colorbar, Colour by Category, Size by a Third Variable'),
    steps(
        ('Put the explanatory variable on x', 'And the outcome on y.'),
        ('Handle overplotting', 'Smaller markers, alpha, hexbin for thousands of points.'),
        ('Encode one extra variable at most', 'Colour (category or colormap) or size.'),
        ('Add a guide', 'Trend line, reference lines, or annotations for outliers.'),
        ('State the relationship in the title', 'And report the correlation or slope.'),
        title='Steps for a Scatter Plot'),
    crossq(
        ('Why add a colorbar?', 'Without it, colours from a colormap cannot be decoded into values.'),
        ('Is size a good encoding?', 'Only for rough comparisons: people judge area poorly, so use it for a secondary variable and show a size legend.'),
        ('Scatter plot vs line plot?', 'Scatter for independent observations (students); line for ordered measurements of one thing over time.'),
    ),
]),
])
