from build import *
from vizq.anims import *
from vizq.runner import vizrun, pyshow
from vizq.data import STUDENTS, data_note, TERM, term_note

S = 'Python (Seaborn) · uses sample data'

SECTION = dict(level='intermediate', title='Seaborn Essentials', questions=[

# ------------------------------------------------------------------ 16
Q('What is Seaborn and how does it relate to Matplotlib? Explain tidy data, axes-level vs figure-level functions and themes.', 'Seaborn Overview', minutes=8, cards=[
    definition(
        defbox('<strong>Seaborn</strong> is a statistical plotting library built on Matplotlib. It works directly with pandas DataFrames in <strong>tidy (long) '
               'format</strong> — one row per observation, one column per variable — and maps columns to <code>x</code>, <code>y</code>, <code>hue</code>, '
               '<code>size</code>, <code>style</code>, <code>col</code>, <code>row</code>. It aggregates, estimates confidence intervals, fits regressions and '
               'adds legends automatically.',
               '<strong>Axes-level</strong> functions (<code>histplot</code>, <code>scatterplot</code>, <code>boxplot</code>, <code>barplot</code>…) draw on one '
               'Matplotlib Axes (<code>ax=</code>) and return it, so they mix with any Matplotlib code. <strong>Figure-level</strong> functions '
               '(<code>displot</code>, <code>relplot</code>, <code>catplot</code>, <code>lmplot</code>) create their own figure with facets and return a '
               '<code>FacetGrid</code>. <code>sns.set_theme(style=..., context=..., palette=...)</code> sets the look.'),
        tags('seaborn', 'tidy data', 'long format', 'hue', 'axes-level', 'figure-level', 'FacetGrid', 'set_theme'),
    ),
    analogy('Matplotlib is a <strong>set of drawing tools</strong>; Seaborn is a <strong>statistician who uses those tools for you</strong>: hand it a table and '
            'say "scores by centre, coloured by method", and it does the grouping, averaging and legend.'),
    sns_anim(),
    real_world(
        scenario('Exploring a new batch quickly',
                 p('When a new batch\'s data arrives, three lines of Seaborn give distributions by course, scores by centre with confidence intervals and a '
                   'scatter of study hours against results, coloured by method — work that would take dozens of Matplotlib lines.')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            sns.set_theme(style='whitegrid', context='notebook')

            # wide table -> tidy long table
            wide = df.groupby('centre')[['pre_test', 'post_test']].mean().reset_index()
            long = wide.melt(id_vars='centre', var_name='test', value_name='mean_score')
            print(wide.round(2)); print(long.round(2))

            # axes-level: draws into an existing Matplotlib axes
            fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), layout='constrained')
            sns.barplot(data=long, x='centre', y='mean_score', hue='test', ax=axes[0])
            axes[0].set_title('axes-level barplot (ax=axes[0])')
            axes[0].legend(title='test', loc='lower right')
            sns.scatterplot(data=df, x='study_hours', y='final_score', hue='method', s=15, ax=axes[1])
            axes[1].set_title('axes-level scatterplot (ax=axes[1])')
            plt.show()

            # figure-level: creates its own figure with one panel per course
            g = sns.displot(data=df, x='final_score', col='course', hue='method', kind='kde', fill=True, height=2.8, aspect=1.1)
            g.figure.suptitle('figure-level displot(col="course")', y=1.05)
            print(type(g).__name__, '| panels:', len(g.axes.flat))
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Wide vs Tidy Data, Axes-Level and Figure-Level Functions'),
    steps(
        ('Reshape to tidy format', 'df.melt for wide tables; one row per observation.'),
        ('Set a theme', 'sns.set_theme(style="whitegrid", context="notebook").'),
        ('Map columns to roles', 'x, y, hue, size, style, col, row.'),
        ('Choose the function level', 'Axes-level inside your own layout; figure-level for faceting.'),
        ('Finish with Matplotlib', 'Titles, limits and annotations on the returned axes.'),
        title='Steps to Use Seaborn'),
    crossq(
        ('Why does Seaborn need tidy data?', 'Each aesthetic (hue, col…) refers to one column; with wide data, the variable you want to colour by is spread across column names.'),
        ('Can you pass ax= to relplot or catplot?', 'No; figure-level functions manage their own figure. Use the axes-level equivalent (scatterplot, boxplot) inside your subplots.'),
        ('Is Seaborn a replacement for Matplotlib?', 'No; it builds on it. Every Seaborn chart is Matplotlib objects you can customise further.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('How do you visualise distributions in Seaborn with histplot, kdeplot and ecdfplot?', 'Distribution Plots', minutes=8, cards=[
    definition(
        defbox('<code>sns.histplot</code> draws histograms with options for <code>bins</code>/<code>binwidth</code>, <code>stat=\'count\'|\'density\'|'
               '\'percent\'</code>, <code>hue</code> with <code>multiple=\'layer\'|\'stack\'|\'dodge\'|\'fill\'</code>, and <code>kde=True</code> overlay. '
               '<code>common_norm=False</code> normalises each hue group separately so groups of different size can be compared.',
               '<code>sns.kdeplot</code> draws a smoothed density (bandwidth via <code>bw_adjust</code>; can spill outside the possible range, e.g. below 0). '
               '<code>sns.ecdfplot</code> shows the cumulative share, has no smoothing parameter, and makes medians and percentiles easy to read and compare. '
               '<code>sns.displot</code> is the figure-level wrapper (<code>kind=\'hist\'|\'kde\'|\'ecdf\'</code>).'),
        tags('histplot', 'kdeplot', 'ecdfplot', 'displot', 'stat', 'multiple', 'common_norm', 'bw_adjust'),
    ),
    analogy('Histogram, KDE and ECDF are three <strong>photographs of the same crowd</strong>: a headcount per row of seats, a smooth outline of the crowd, and '
            'a running total as you walk from the back to the front.'),
    dist_anim(),
    real_world(
        scenario('Did the flipped classroom shift the whole distribution?',
                 p('The mean post-test went up, but did everyone improve or only the top students? Overlaid KDEs and ECDFs by teaching method answer it: the '
                   'flipped curve is shifted right most at the median and top quartile (62 vs 58.5, 71 vs 67), while the weakest quarter barely moved (52 vs 51).')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            sns.set_theme(style='whitegrid')
            fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), layout='constrained')
            sns.histplot(data=df, x='post_test', hue='method', stat='density', common_norm=False, element='step', ax=axes[0])
            axes[0].set_title('histplot (density per group)')
            sns.kdeplot(data=df, x='post_test', hue='method', fill=True, common_norm=False, ax=axes[1])
            axes[1].set_title('kdeplot')
            sns.ecdfplot(data=df, x='post_test', hue='method', ax=axes[2])
            axes[2].axhline(0.25, color='gray', linestyle=':'); axes[2].axhline(0.5, color='gray', linestyle=':')
            axes[2].set_title('ecdfplot (read quartiles directly)')
            plt.show()
            print(df.groupby('method')['post_test'].quantile([0.25, 0.5, 0.75]).unstack().round(1))

            fig, axes = plt.subplots(1, 3, figsize=(12, 3.2), layout='constrained')
            for ax, bw in zip(axes, [0.3, 1, 3]):
                sns.kdeplot(data=df, x='salary_lpa', bw_adjust=bw, fill=True, ax=ax)
                ax.set_title(f'bw_adjust={bw}')
            axes[2].axvline(0, color='red', linestyle='--')
            plt.show()
            print('smallest package:', df.salary_lpa.min(), '| a wide KDE puts density below 0, which is impossible')

            plt.figure(figsize=(7, 3.4))                    # new figure, otherwise seaborn draws on the last axes
            sns.histplot(data=df, x='final_score', hue='course', multiple='stack', binwidth=4)
            plt.title("histplot(multiple='stack') by course")
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Histogram, KDE and ECDF by Method; Bandwidth; Stacked Histogram'),
    steps(
        ('Start with histplot', 'Choose binwidth; stat="density"/"percent" for comparisons.'),
        ('Compare groups', 'hue with common_norm=False; element="step" or KDE overlays.'),
        ('Use ECDFs for precise comparison', 'Medians and percentiles without smoothing choices.'),
        ('Tune smoothing consciously', 'bw_adjust for KDEs; check bounds (no negative packages).'),
        ('Facet if overlaid curves clutter', 'displot(col=...).'),
        title='Steps to Plot Distributions in Seaborn'),
    crossq(
        ('What does common_norm=False change?', 'Each hue group is normalised to its own total, so group shapes are comparable even when one group is much larger.'),
        ('KDE vs histogram?', 'KDE is smoother and nicer for overlays but depends on bandwidth and can mislead at boundaries; histograms show the raw counts.'),
        ('Why are ECDFs underused?', 'They look less familiar, but they show every data point, need no binning, and make shifts between groups easy to read.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('How do you compare categories in Seaborn? Explain barplot vs countplot, estimators and error bars, box/violin/strip/swarm plots.', 'Categorical Plots', minutes=9, cards=[
    definition(
        defbox('<code>sns.countplot</code> counts rows per category. <code>sns.barplot</code> shows an <strong>estimate</strong> per category — the mean by '
               'default (<code>estimator=\'median\'</code>, <code>sum</code>…) — with an error bar controlled by <code>errorbar=</code>: '
               '<code>(\'ci\', 95)</code> bootstrap confidence interval (default), <code>\'se\'</code>, <code>\'sd\'</code>, <code>(\'pi\', 50)</code> '
               'percentile interval, or <code>None</code>. <code>sns.pointplot</code> shows the same estimate as points, good for interactions.',
               'Distribution views: <code>boxplot</code>, <code>violinplot</code>, <code>boxenplot</code> (large n), and the raw points with '
               '<code>stripplot</code> (jittered) or <code>swarmplot</code> (non-overlapping; small n). Combining a box or violin with a strip plot shows summary '
               'and data together. <code>order=</code> and <code>hue_order=</code> fix category order.'),
        tags('countplot', 'barplot', 'estimator', 'errorbar', 'pointplot', 'boxplot', 'stripplot', 'swarmplot'),
    ),
    analogy('A barplot is the <strong>class average written on the board</strong> with a ± next to it; the strip plot is the <strong>whole class standing in '
            'line</strong>. Showing both tells you the average and whether it describes anybody.'),
    cat_anim(),
    real_world(
        scenario('Placement and scores by centre',
                 p('A countplot of placed vs not placed per centre, a barplot of placement rate with 95 % CIs, and a box-plus-strip plot of final scores by course '
                   'form the "categories" page of the monthly review.')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            sns.set_theme(style='whitegrid')
            order = ['Kharghar', 'Juhu', 'Pune']
            fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), layout='constrained')
            sns.countplot(data=df.assign(status=df.placed.map({0: 'not placed', 1: 'placed'})), x='centre', hue='status', order=order, ax=axes[0])
            axes[0].set_title('countplot: rows per category')
            sns.barplot(data=df, x='centre', y='placed', order=order, errorbar=('ci', 95), ax=axes[1], color='#0ea5e9')
            axes[1].set(title='barplot: mean (= rate) with 95 % CI', ylabel='placement rate')
            sns.pointplot(data=df, x='centre', y='post_test', hue='method', order=order, dodge=0.3, ax=axes[2])
            axes[2].set_title('pointplot: interaction centre x method')
            plt.show()

            fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), layout='constrained')
            sns.boxplot(data=df, x='course', y='final_score', color='#e2e8f0', showfliers=False, ax=axes[0])
            sns.stripplot(data=df, x='course', y='final_score', size=2.5, alpha=0.5, jitter=0.25, ax=axes[0])
            axes[0].set_title('box + strip: summary and every student')
            small = df.sample(90, random_state=1)
            sns.swarmplot(data=small, x='method', y='post_test', hue='method', size=4, ax=axes[1], legend=False)
            axes[1].set_title('swarmplot (90 students)')
            plt.show()

            for eb in [('ci', 95), 'se', 'sd']:
                plt.figure()
                ax = sns.barplot(data=df, x='centre', y='final_score', order=order, errorbar=eb)
                y = ax.lines[0].get_ydata()
                print(f'errorbar={str(eb):10} Kharghar interval width {np.nanmax(y) - np.nanmin(y):5.2f}')
                plt.close()
        """, setup=STUDENTS, title=S),
        title='Example: countplot, barplot with CI, pointplot, box + strip, swarm, and errorbar Options'),
    steps(
        ('Decide: counts, estimates or distributions?', 'countplot, barplot/pointplot, or box/violin/strip.'),
        ('Fix the order', 'order= and hue_order= so charts are consistent.'),
        ('State the error bar', 'errorbar=("ci", 95), "se" or "sd" — mention it in the caption.'),
        ('Show the data for small groups', 'Overlay stripplot or swarmplot.'),
        ('Use pointplot for interactions', 'Two categorical factors with dodge.'),
        title='Steps for Categorical Plots'),
    crossq(
        ('Why is the barplot of a 0/1 column a rate?', 'The mean of a 0/1 variable is the proportion of ones, so barplot(y="placed") shows the placement rate with its CI.'),
        ('Why do the error bars change with errorbar=\'sd\' vs \'ci\'?', 'SD describes how spread out students are (wide); the CI describes uncertainty of the mean (narrow, shrinks with n).'),
        ('swarmplot vs stripplot?', 'Swarm avoids overlap exactly but becomes slow and wide with many points; strip with jitter and alpha scales to hundreds or thousands.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('How do you plot relationships in Seaborn with scatterplot and lineplot? How does lineplot aggregate and show confidence intervals?', 'Relational Plots', minutes=8, cards=[
    definition(
        defbox('<code>sns.scatterplot(data, x, y, hue, size, style)</code> maps up to three extra variables onto colour, marker size and marker shape, with '
               'legends created automatically; numeric hue uses a continuous palette, categorical hue a qualitative one.',
               '<code>sns.lineplot</code> sorts by x and, when several rows share the same x, <strong>aggregates</strong> them (mean by default) and draws a '
               'band for the uncertainty (<code>errorbar=(\'ci\', 95)</code>, or <code>\'sd\'</code>, or <code>None</code>). Use <code>units=</code> with '
               '<code>estimator=None</code> to draw one line per entity instead. <code>sns.relplot</code> is the figure-level version with <code>col</code>/'
               '<code>row</code> facets.'),
        tags('scatterplot', 'lineplot', 'hue', 'size', 'style', 'aggregation', 'errorbar band', 'relplot'),
    ),
    analogy('A lineplot with many rows per x is a <strong>group photo per month</strong>: it shows where the group stood on average and how spread out it was '
            '(the band), instead of every individual\'s path.'),
    rel_anim(),
    real_world(
        scenario('Attendance by weekday and centre',
                 p('Feeding the daily attendance table to lineplot with x = weekday and hue = centre gives the average weekday pattern per centre with a 95 % band, '
                   'computed from about 26 values per point without any manual groupby.')),
    ),
    example(
        term_note(),
        vizrun("""
            import seaborn as sns
            sns.set_theme(style='whitegrid')
            term['weekday'] = pd.Categorical(term['date'].dt.day_name().str[:3], ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], ordered=True)
            term['month'] = term['date'].dt.month

            fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), layout='constrained')
            sns.lineplot(data=term, x='weekday', y='attendance', hue='centre', marker='o', errorbar=('ci', 95), ax=axes[0])
            axes[0].set_title('lineplot: mean per weekday with 95 % CI band')
            sns.lineplot(data=term, x='month', y='attendance', hue='centre', errorbar='sd', ax=axes[1])
            axes[1].set_title("errorbar='sd': spread of days, not uncertainty")
            plt.show()
            print('rows per (centre, weekday):', term.groupby(['centre', 'weekday'], observed=True).size().unique())

            k = term[term.centre == 'Kharghar'].copy()
            k['week'] = k['date'].dt.isocalendar().week.astype(int)
            plt.figure(figsize=(7, 3.4))
            sns.lineplot(data=k, x='weekday', y='attendance', units='week', estimator=None, color='#94a3b8', alpha=0.4, linewidth=1)
            sns.lineplot(data=k, x='weekday', y='attendance', color='#0f766e', linewidth=3, errorbar=None)
            plt.title('Kharghar: one thin line per week, bold mean')
            plt.show()
        """, setup=TERM, title=S),
        title='Example: Aggregating lineplot with CI vs SD Bands, and One Line per Unit'),
    steps(
        ('Use tidy data', 'One row per observation with the grouping columns.'),
        ('Scatter for individual points', 'scatterplot with hue/size/style sparingly.'),
        ('lineplot for trends over ordered x', 'It aggregates repeated x values automatically.'),
        ('Choose the band', 'errorbar=("ci", 95) for uncertainty, "sd" for spread, None to hide.'),
        ('Show units if needed', 'units= with estimator=None for spaghetti plus a bold mean.'),
        title='Steps for Relational Plots'),
    crossq(
        ('Why did lineplot draw a band I did not ask for?', 'Several rows share each x, so it aggregated them and added a 95 % CI by default; pass errorbar=None or pre-aggregate.'),
        ('Why make weekday an ordered categorical?', 'Otherwise strings sort alphabetically (Fri, Mon, Thu…), scrambling the line.'),
        ('hue vs style vs size?', 'Colour is the strongest channel for groups; style (dashes/markers) helps in greyscale; size suits a numeric variable but is read imprecisely.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('How do you show a regression relationship with regplot, lmplot and residplot?', 'Regression Plots', minutes=8, cards=[
    definition(
        defbox('<code>sns.regplot(data, x, y)</code> draws a scatter plus a fitted linear regression line with a 95 % confidence band (bootstrapped). Options: '
               '<code>order=2</code> polynomial fit, <code>lowess=True</code> for a non-parametric smooth curve, <code>logistic=True</code> for a 0/1 outcome, '
               '<code>x_estimator=np.mean</code> to show binned means, <code>scatter_kws</code>/<code>line_kws</code> for styling.',
               '<code>sns.lmplot</code> is the figure-level version with <code>hue</code>, <code>col</code> and <code>row</code> to fit separate lines per group. '
               '<code>sns.residplot</code> plots residuals against x to check whether a straight line is adequate. Seaborn shows the fit but does not report '
               'coefficients: use NumPy, SciPy or statsmodels for the numbers.'),
        tags('regplot', 'lmplot', 'residplot', 'lowess', 'logistic', 'order', 'confidence band'),
    ),
    analogy('regplot is a <strong>ruler laid along the scatter</strong> with a shaded margin of doubt around it; residplot is the <strong>view from the end of '
            'the ruler</strong>, showing how far each point bends away from straight.'),
    reg_anim(),
    real_world(
        scenario('Does the study-hours effect differ by course?',
                 p('lmplot with hue = course draws one regression line per course: parallel lines mean the same marks-per-hour benefit everywhere. A logistic '
                   'regplot of placement against post-test shows how the probability of placement rises with the score.')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            sns.set_theme(style='whitegrid')
            fig, axes = plt.subplots(1, 3, figsize=(13, 3.6), layout='constrained')
            sns.regplot(data=df, x='study_hours', y='final_score', scatter_kws=dict(s=8, alpha=0.3), ax=axes[0])
            axes[0].set_title('regplot: linear fit + 95 % CI')
            sns.regplot(data=df, x='post_test', y='placed', logistic=True, y_jitter=0.03, scatter_kws=dict(s=6, alpha=0.2), ax=axes[1])
            axes[1].set_title('logistic=True: P(placed)')
            sns.residplot(data=df, x='study_hours', y='final_score', lowess=True, scatter_kws=dict(s=8, alpha=0.3), ax=axes[2])
            axes[2].set_title('residplot with lowess: no curve left')
            plt.show()

            g = sns.lmplot(data=df, x='study_hours', y='final_score', hue='course', scatter_kws=dict(s=8, alpha=0.3), height=3.6, aspect=1.6)
            g.ax.set_title('lmplot(hue="course"): nearly parallel lines')
            plt.show()
            for c, d in df.groupby('course'):
                slope, intercept = np.polyfit(d.study_hours, d.final_score, 1)
                print(f'{c:8} slope {slope:.2f} marks per weekly hour, intercept {intercept:.1f}')
        """, setup=STUDENTS, title=S),
        title='Example: Linear, Logistic and Residual Plots; One Line per Course'),
    steps(
        ('Plot the fit', 'regplot (axes-level) or lmplot (with hue/col).'),
        ('Pick the model shape', 'Linear, order=2, lowess, or logistic for 0/1.'),
        ('Check residuals', 'residplot with lowess=True; look for curves or funnels.'),
        ('Get the numbers elsewhere', 'np.polyfit / statsmodels for slopes and p-values.'),
        ('Avoid over-reading the band', 'It is the CI of the line, not where individual students fall.'),
        title='Steps for Regression Plots'),
    crossq(
        ('What does the shaded band around the regplot line show?', 'A bootstrap 95 % confidence interval for the regression line (the mean response), not a prediction interval for individuals.'),
        ('Why use lowess?', 'It fits a flexible local curve without assuming a shape, revealing non-linearity a straight line would hide.'),
        ('How do you get the slope from a seaborn plot?', 'You cannot directly; compute it with np.polyfit, scipy.stats.linregress or statsmodels.'),
    ),
]),
])
