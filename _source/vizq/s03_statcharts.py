from build import *
from vizq.anims import *
from vizq.runner import vizrun, pyshow
from vizq.data import STUDENTS, data_note, TERM, term_note

S = 'Python (Matplotlib) · uses sample data'
P = 'Python (Matplotlib)'

SECTION = dict(level='intermediate', title='Statistical Charts in Matplotlib', questions=[

# ------------------------------------------------------------------ 11
Q('How do you compare distributions across groups with box plots and violin plots?', 'Box & Violin Plots', minutes=8, cards=[
    definition(
        defbox('A <strong>box plot</strong> (<code>ax.boxplot</code>) summarises a distribution with the median, quartiles (box), whiskers (to the furthest '
               'point within 1.5 × IQR) and individual outliers. It compares <strong>many groups compactly</strong> but hides the shape: two very different '
               'distributions (bimodal vs normal) can have identical boxes.',
               'A <strong>violin plot</strong> (<code>ax.violinplot</code>) draws a mirrored density, showing shape and modes, usually with the median marked. '
               'Overlaying the raw points (a strip/jitter plot) is honest for small groups. Useful options: <code>showmeans</code>, <code>notch=True</code> '
               '(rough CI for the median), <code>vert=False</code> for horizontal plots, <code>tick_labels</code> for group names.'),
        tags('ax.boxplot', 'ax.violinplot', 'quartiles', 'whiskers', 'outliers', 'notch', 'jitter'),
    ),
    analogy('A box plot is a <strong>five-number summary card</strong> for each group; a violin is the <strong>silhouette</strong> of the whole crowd. The card '
            'fits in a pocket; the silhouette shows whether the crowd has one hump or two.'),
    box_anim(),
    real_world(
        scenario('Packages by course',
                 p('Side-by-side box plots of placement packages per course show medians, spread and the few very high offers in one view; the violins add the shape: '
                   'most offers sit between 4 and 8 LPA with a long, thin tail of high packages that the boxes reduce to a few outlier circles.')),
    ),
    example(
        data_note(),
        vizrun("""
            groups = ['PG-DBDA', 'PG-DAC', 'PG-DAI']
            data = [df.loc[(df.course == g) & df.salary_lpa.notna(), 'salary_lpa'] for g in groups]
            fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True, layout='constrained')
            axes[0].boxplot(data, tick_labels=groups, showmeans=True, patch_artist=True,
                            boxprops=dict(facecolor='#bae6fd'), medianprops=dict(color='#0f172a', linewidth=2))
            axes[0].set(title='Box plot (triangle = mean)', ylabel='package (LPA)')
            parts = axes[1].violinplot(data, showmedians=True)
            axes[1].set(xticks=[1, 2, 3], xticklabels=groups, title='Violin plot + jittered points')
            rng = np.random.default_rng(0)
            for i, d in enumerate(data, start=1):
                axes[1].scatter(i + rng.uniform(-0.08, 0.08, len(d)), d, s=6, alpha=0.4, color='#0f172a')
            plt.show()
            for g, d in zip(groups, data):
                q1, med, q3 = d.quantile([.25, .5, .75])
                print(f'{g:8} n={len(d):3}  median {med:.1f}  IQR {q3 - q1:.2f}  outliers >{q3 + 1.5 * (q3 - q1):.1f}: {(d > q3 + 1.5 * (q3 - q1)).sum()}')

            # same box, different shapes
            rng = np.random.default_rng(1)
            a = rng.normal(60, 10, 400)
            b = np.r_[rng.normal(48, 4, 200), rng.normal(72, 4, 200)]
            fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), layout='constrained')
            axes[0].boxplot([a, b], tick_labels=['unimodal', 'bimodal']); axes[0].set_title('boxes look alike')
            axes[1].violinplot([a, b], showmedians=True); axes[1].set(xticks=[1, 2], xticklabels=['unimodal', 'bimodal'], title='violins reveal the shape')
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Packages by Course; Two Distributions with Similar Boxes'),
    steps(
        ('Collect one array per group', 'Drop missing values.'),
        ('Box plot for compact comparison', 'ax.boxplot(data, tick_labels=..., showmeans=True).'),
        ('Violin or points for shape', 'ax.violinplot, plus jittered points for small n.'),
        ('Share the value axis', 'sharey=True across panels.'),
        ('Report the numbers', 'Medians, IQRs and n per group.'),
        title='Steps to Compare Distributions'),
    crossq(
        ('What do the whiskers show?', 'By default, the most extreme data points within 1.5 × IQR of the box; points beyond are drawn as outliers.'),
        ('When can a box plot mislead?', 'With multimodal data, very small groups, or when group sizes differ a lot (always show n).'),
        ('What does a notch mean?', 'An approximate 95 % CI for the median; non-overlapping notches suggest the medians differ.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('When is a pie chart acceptable, and what are better alternatives for showing composition?', 'Pie Charts & Composition', minutes=7, cards=[
    definition(
        defbox('A <strong>pie chart</strong> (<code>ax.pie(values, labels=..., autopct=\'%1.0f%%\')</code>) shows parts of one whole. People judge '
               '<strong>angles and areas</strong> much less accurately than lengths or positions, so pies work only with <strong>few categories (2–4) with '
               'clearly different shares</strong>, when the message is "part of the whole" (e.g. about half). A <strong>donut</strong> '
               '(<code>wedgeprops=dict(width=0.4)</code>) is a pie with a hole for a central label.',
               'Better alternatives: a <strong>sorted bar chart</strong> of shares (precise comparisons), a <strong>100 % stacked bar</strong> (composition across '
               'several groups), or a <strong>waffle chart</strong>. Never use 3-D or exploded pies, many slices, or several pies side by side for comparison.'),
        tags('ax.pie', 'autopct', 'donut', 'composition', 'part-to-whole', '100 % stacked bar', 'perception'),
    ),
    analogy('Asking readers to compare pie slices is like asking them to compare <strong>slices of cake by eye</strong>: they can tell half from a quarter, but '
            'not 18 % from 22 %. Lining the slices up as bars is like weighing them.'),
    pie_anim(),
    real_world(
        scenario('Course mix of the batch',
                 p('For the brochure, a donut showing that almost half the batch is PG-DBDA works. For the governing council comparing the course mix across three '
                   'centres, a 100 % stacked bar is clearer than three pies.')),
    ),
    example(
        data_note(),
        vizrun("""
            share = df['course'].value_counts()
            fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout='constrained')
            axes[0].pie(share, labels=share.index, autopct='%1.0f%%', pctdistance=0.79, startangle=90, counterclock=False,
                        wedgeprops=dict(width=0.42, edgecolor='white'), colors=['#0f766e', '#5eead4', '#cbd5e1'])
            axes[0].text(0, 0, f'{len(df)}\\nstudents', ha='center', va='center', fontsize=12)
            axes[0].set_title('Donut: few parts of one whole')
            s = share.sort_values()
            b = axes[1].barh(s.index, s / s.sum() * 100, color='#0f766e')
            axes[1].bar_label(b, fmt='%.1f%%', padding=3)
            axes[1].set(title='Sorted bars: precise comparison', xlim=(0, 55), xlabel='% of students')
            plt.show()

            # many similar slices: pie vs bars
            vals = pd.Series([18, 22, 20, 15, 25], index=list('ABCDE'))
            fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout='constrained')
            axes[0].pie(vals, labels=vals.index); axes[0].set_title('Which slice is largest? Hard to tell')
            axes[1].bar(vals.index, vals, color='#94a3b8'); axes[1].set_title('Same data as bars: E > B > C > A > D')
            plt.show()

            mix = pd.crosstab(df['centre'], df['course'], normalize='index') * 100
            ax = mix.plot.barh(stacked=True, figsize=(8, 2.8), color=['#5eead4', '#cbd5e1', '#0f766e'])
            ax.set(xlabel='% of students', title='100 % stacked bars: course mix per centre')
            ax.legend(ncol=3, bbox_to_anchor=(0.5, -0.28), loc='upper center', frameon=False)
            plt.show()
            print(mix.round(1))
        """, setup=STUDENTS, title=S),
        title='Example: Donut vs Sorted Bars, a Hard-to-Read Pie, 100 % Stacked Bars'),
    steps(
        ('Check the question', 'Part of one whole? Few categories? Otherwise use bars.'),
        ('Limit slices', 'Two to four; merge small ones into "Other".'),
        ('Order and label', 'Start at 12 o\'clock, largest first, percentages on the slices.'),
        ('Prefer bars for comparisons', 'Sorted bars or 100 % stacked bars across groups.'),
        ('Avoid 3-D and exploded pies', 'They distort areas.'),
        title='Steps to Show Composition'),
    crossq(
        ('Why are pie charts criticised?', 'Angle and area are judged less accurately than length or position, so small differences between slices are invisible.'),
        ('When is a pie genuinely fine?', 'For a simple part-to-whole message with 2–3 parts, e.g. "about half of the batch is PG-DBDA".'),
        ('Why not use several pies to compare groups?', 'Readers must compare angles across separate circles; a 100 % stacked bar aligns the segments on a common scale.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('How do you draw heatmaps in Matplotlib with imshow or pcolormesh, including annotations and a colorbar?', 'Heatmaps', minutes=8, cards=[
    definition(
        defbox('A <strong>heatmap</strong> encodes a matrix of values as colours: correlation matrices, pivot tables (centre × month), confusion matrices, '
               'calendar activity. <code>ax.imshow(matrix, cmap=..., aspect=\'auto\')</code> draws equal-sized cells; <code>ax.pcolormesh(x_edges, y_edges, '
               'values)</code> handles unequal cell sizes. Always add a <code>fig.colorbar</code>, tick labels for rows and columns, and choose the colormap by '
               'data type (sequential for magnitudes, diverging around a midpoint).',
               'For small tables, write the values in the cells with <code>ax.text</code> (pick white or black text for contrast). Fix '
               '<code>vmin/vmax</code> to compare several heatmaps. Seaborn\'s <code>heatmap</code> does all this in one call (later section).'),
        tags('imshow', 'pcolormesh', 'colorbar', 'annotated cells', 'pivot table', 'vmin / vmax', 'aspect'),
    ),
    analogy('A heatmap is a <strong>spreadsheet where the cells are painted</strong> instead of filled with numbers: your eye finds the hot corner before you '
            'could read a single figure.'),
    heat_anim(),
    real_world(
        scenario('Attendance by centre and weekday',
                 p('A centre × weekday heatmap of average attendance immediately shows that Mondays are weak everywhere and that one centre is consistently lower; '
                   'the annotated values give the exact figures for the minutes of the meeting.')),
    ),
    example(
        term_note(),
        vizrun("""
            term['weekday'] = term['date'].dt.day_name().str[:3]
            tab = term.pivot_table(index='centre', columns='weekday', values='attendance', aggfunc='mean')[['Mon', 'Tue', 'Wed', 'Thu', 'Fri']] * 100
            print(tab.round(1))
            fig, ax = plt.subplots(figsize=(7, 2.8))
            im = ax.imshow(tab, cmap='YlGnBu', aspect='auto', vmin=74, vmax=84)
            ax.set(xticks=range(tab.shape[1]), xticklabels=tab.columns, yticks=range(tab.shape[0]), yticklabels=tab.index)
            for i in range(tab.shape[0]):
                for j in range(tab.shape[1]):
                    v = tab.iloc[i, j]
                    ax.text(j, i, f'{v:.1f}', ha='center', va='center', color='white' if v > 81 else 'black')
            fig.colorbar(im, ax=ax, label='attendance %')
            ax.set_title('Mondays are weakest at every centre')
            plt.show()

            # calendar-style heatmap: weeks x weekdays for one centre with pcolormesh
            k = term[term.centre == 'Kharghar'].copy()
            k['week'] = k['date'].dt.isocalendar().week.astype(int)
            k['dow'] = k['date'].dt.dayofweek
            grid = k.pivot(index='dow', columns='week', values='attendance') * 100
            fig, ax = plt.subplots(figsize=(10, 2.6))
            mesh = ax.pcolormesh(grid.columns, grid.index, grid.values, cmap='magma', shading='nearest', vmin=60, vmax=95)
            ax.set(yticks=range(5), yticklabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], xlabel='ISO week', title='Kharghar daily attendance: the exam-prep week stands out')
            ax.invert_yaxis()
            fig.colorbar(mesh, ax=ax, label='%')
            plt.show()
        """, setup=TERM, title=S),
        title='Example: Annotated Centre × Weekday Heatmap and a Calendar Heatmap'),
    steps(
        ('Shape the data as a matrix', 'pivot_table with rows, columns and one value.'),
        ('Pick the colormap and range', 'Sequential or diverging; fix vmin/vmax.'),
        ('Draw', 'imshow (equal cells) or pcolormesh (any cell edges).'),
        ('Label', 'Row/column tick labels, colorbar with units, title with the message.'),
        ('Annotate small tables', 'ax.text in each cell with contrasting colour.'),
        title='Steps for a Heatmap'),
    crossq(
        ('imshow vs pcolormesh?', 'imshow treats the data as an image with equal pixels; pcolormesh draws cells at given coordinates, so irregular grids and real axis values work.'),
        ('Why fix vmin and vmax?', 'Otherwise the colour scale stretches to the data range, exaggerating small differences or making separate heatmaps incomparable.'),
        ('Why invert the y-axis in a calendar heatmap?', 'So Monday is at the top, as in a printed calendar; imshow does this by default, pcolormesh does not.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do you show uncertainty: error bars, confidence intervals and shaded bands?', 'Error Bars & Uncertainty', minutes=8, cards=[
    definition(
        defbox('<code>ax.errorbar(x, y, yerr=..., fmt=\'o\', capsize=4)</code> draws a point with an interval; <code>yerr</code> can be symmetric or a '
               '2 × n array for asymmetric intervals (e.g. bootstrap CIs). <code>ax.fill_between(x, lower, upper, alpha=0.2)</code> shades a band around a line '
               '(confidence band, prediction band, min–max range).',
               'Always state <strong>what</strong> the interval is: standard deviation (spread of individuals), standard error (precision of the mean), or a '
               '95 % confidence interval. Bars with error bars ("dynamite plots") hide the data; points with CIs, or the raw points plus a mean and CI, are more '
               'honest.'),
        tags('ax.errorbar', 'yerr', 'capsize', 'fill_between', 'confidence interval', 'standard error', 'uncertainty'),
    ),
    analogy('An estimate without an error bar is a <strong>weather forecast without a chance of rain</strong>: "28 °C" sounds certain, while "28 ± 3 °C" tells you '
            'whether to carry an umbrella.'),
    errbar_anim(),
    real_world(
        scenario('Comparing mean post-test score by teaching method and centre',
                 p('Points with 95 % confidence intervals show that the flipped classroom is ahead in every centre, but the intervals overlap within some centres: '
                   'the per-centre differences are less certain than the overall result, which is exactly the nuance the report needs.')),
    ),
    example(
        data_note(),
        vizrun("""
            from scipy import stats
            g = df.groupby(['centre', 'method'])['post_test'].agg(['mean', 'sem', 'count'])
            g['ci'] = g['sem'] * stats.t.ppf(0.975, g['count'] - 1)
            print(g.round(2))

            fig, ax = plt.subplots(figsize=(7, 3.8))
            centres = ['Juhu', 'Kharghar', 'Pune']
            for k, (method, colour) in enumerate([('traditional', '#94a3b8'), ('flipped', '#10b981')]):
                d = g.xs(method, level='method').loc[centres]
                ax.errorbar(np.arange(3) + (k - 0.5) * 0.2, d['mean'], yerr=d['ci'], fmt='o', capsize=5, color=colour, label=method, markersize=7)
            ax.set(xticks=range(3), xticklabels=centres, ylabel='mean post-test (95 % CI)', title='Flipped ahead everywhere; overlap in some centres')
            ax.legend(frameon=False)
            plt.show()

            # a band around a fitted line
            x = df['study_hours']; y = df['final_score']
            b, a = np.polyfit(x, y, 1)
            xs = np.linspace(x.min(), x.max(), 100)
            resid_sd = np.std(y - (a + b * x), ddof=2)
            se_mean = resid_sd * np.sqrt(1 / len(x) + (xs - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum())
            fig, ax = plt.subplots(figsize=(7, 3.8))
            ax.scatter(x, y, s=6, alpha=0.3, color='#64748b')
            ax.plot(xs, a + b * xs, color='#0ea5e9', linewidth=2, label='fit')
            ax.fill_between(xs, a + b * xs - 1.96 * se_mean, a + b * xs + 1.96 * se_mean, alpha=0.35, color='#0ea5e9', label='95 % CI of the mean')
            ax.fill_between(xs, a + b * xs - 1.96 * resid_sd, a + b * xs + 1.96 * resid_sd, alpha=0.12, color='#0ea5e9', label='~95 % prediction band')
            ax.set(xlabel='weekly study hours', ylabel='final score', title='Confidence band vs prediction band')
            ax.legend(frameon=False, loc='upper left')
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Means with 95 % CIs by Group, and Confidence vs Prediction Bands'),
    steps(
        ('Compute the interval', 'SE, CI (t or bootstrap) or SD — decide which question it answers.'),
        ('Plot points with intervals', 'ax.errorbar(..., fmt="o", capsize=...).'),
        ('Use bands for continuous x', 'ax.fill_between(x, lower, upper, alpha=...).'),
        ('Label the interval type', 'In the axis label, legend or caption.'),
        ('Show the data when possible', 'Faint raw points behind the summary.'),
        title='Steps to Show Uncertainty'),
    crossq(
        ('Error bars overlap. Is the difference non-significant?', 'Not necessarily; overlapping 95 % CIs can still correspond to a significant difference. Plot the CI of the difference for that question.'),
        ('Why is the prediction band so much wider than the confidence band?', 'The confidence band covers the average score at each x; the prediction band covers individual students, including their residual variation.'),
        ('What is wrong with "dynamite plots"?', 'A bar plus a whisker hides the distribution and sample size and wastes ink on the area below the mean.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you plot time series well? Handle dates, resampling, rolling averages and date formatting.', 'Time-Series Plots', minutes=9, cards=[
    definition(
        defbox('Matplotlib plots pandas datetime values directly; use a <code>DatetimeIndex</code> and let <code>matplotlib.dates</code> locators and formatters '
               '(<code>MonthLocator</code>, <code>DateFormatter(\'%b\')</code>, <code>ConciseDateFormatter</code>) produce readable ticks. Noisy daily data '
               'is easier to read when you <strong>resample</strong> (<code>.resample(\'W\').mean()</code>) or add a <strong>rolling mean</strong> '
               '(<code>.rolling(10).mean()</code>) on top of faint raw values.',
               'Good practice: time on the x-axis, consistent intervals (do not join across gaps silently), mark events with <code>axvline/axvspan</code>, '
               'compare series on shared axes (or index them to 100 at the start), and choose the y-range to show meaningful change without exaggerating it.'),
        tags('DatetimeIndex', 'resample', 'rolling mean', 'DateFormatter', 'ConciseDateFormatter', 'seasonality', 'events'),
    ),
    analogy('Raw daily data is <strong>a heartbeat trace</strong>: full of spikes. A rolling average is the doctor\'s summary — "steady, slightly declining" — '
            'and the shaded event is the note saying when the patient ran up the stairs.'),
    ts_anim(),
    real_world(
        scenario('Term attendance trend',
                 p('The term report shows daily attendance faintly, a 10-day rolling mean boldly, and the exam-prep week shaded, for each centre on a shared axis. '
                   'The slow decline across the term, the Monday effect and the April dip are all visible in one figure.')),
    ),
    example(
        term_note(),
        vizrun("""
            import matplotlib.dates as mdates
            s = term.pivot(index='date', columns='centre', values='attendance') * 100
            print(s.resample('ME').mean().round(1))

            fig, ax = plt.subplots(figsize=(10, 4))
            for c, colour in zip(s.columns, ['#0ea5e9', '#f59e0b', '#10b981']):
                ax.plot(s.index, s[c], color=colour, alpha=0.25, linewidth=1)
                ax.plot(s.index, s[c].rolling(10, center=True).mean(), color=colour, linewidth=2.5, label=f'{c} (10-day mean)')
            ax.axvspan(pd.Timestamp('2026-04-13'), pd.Timestamp('2026-04-17'), color='#ef4444', alpha=0.12, label='exam-prep week')
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
            ax.set(ylabel='attendance %', title='Daily attendance (faint) and 10-day rolling mean (bold)', ylim=(60, 95))
            ax.legend(ncol=2, frameon=False, loc='lower left')
            ax.spines[['top', 'right']].set_visible(False)
            plt.show()

            weekly = s.resample('W-FRI').mean()
            fig, ax = plt.subplots(figsize=(10, 3))
            ax.plot(weekly.index, weekly['Kharghar'], 'o-', color='#0ea5e9')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            ax.set(title='Kharghar weekly average (resampled to weeks ending Friday)', ylabel='attendance %')
            plt.show()
            print('weekly points:', len(weekly), '| daily points:', len(s))
        """, setup=TERM, title=S),
        title='Example: Raw vs Rolling Mean with an Event, Month Ticks, Weekly Resampling'),
    steps(
        ('Index by datetime', 'pd.to_datetime, set_index, sort.'),
        ('Reduce noise', 'resample to weeks/months or add a rolling mean over faint raw data.'),
        ('Format date ticks', 'MonthLocator + ConciseDateFormatter or DateFormatter.'),
        ('Mark events', 'axvline / axvspan with a legend entry or label.'),
        ('Compare on one scale', 'Shared axes or values indexed to 100.'),
        title='Steps for a Time-Series Chart'),
    crossq(
        ('resample vs rolling?', 'resample changes the frequency (one value per week); rolling keeps every day but smooths with a moving window.'),
        ('Why center=True in the rolling mean?', 'Without it, each value averages only past days, so the smoothed line lags behind real changes (useful for live dashboards, misleading for history).'),
        ('Why do date labels overlap, and how do you fix it?', 'Too many ticks for the width; use a coarser locator, ConciseDateFormatter, or fig.autofmt_xdate() to rotate them.'),
    ),
]),
])
