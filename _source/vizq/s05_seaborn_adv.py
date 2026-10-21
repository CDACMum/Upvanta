from build import *
from vizq.anims import *
from vizq.runner import vizrun, pyshow
from vizq.data import STUDENTS, data_note, TERM, term_note

S = 'Python (Seaborn) · uses sample data'

SECTION = dict(level='advanced', title='Advanced Seaborn', questions=[

# ------------------------------------------------------------------ 21
Q('What are small multiples? How do you build faceted plots with relplot, catplot, displot and FacetGrid?', 'Faceting & Small Multiples', minutes=9, cards=[
    definition(
        defbox('<strong>Small multiples</strong> repeat the same chart for each subset of the data (one panel per centre, course or month) on <strong>shared '
               'axes</strong>, so readers compare panels at a glance instead of untangling many overlapping series.',
               'Seaborn\'s figure-level functions facet with <code>col=</code>, <code>row=</code> and <code>col_wrap=</code>: <code>relplot</code> (scatter/line), '
               '<code>catplot</code> (strip, box, violin, bar, point, count via <code>kind=</code>), <code>displot</code> (hist, kde, ecdf). They return a '
               '<strong>FacetGrid</strong>; customise with <code>g.set_titles("{col_name}")</code>, <code>g.set_axis_labels</code>, <code>g.refline</code>, and '
               'loop over <code>g.axes_dict</code>. <code>sns.FacetGrid(df, col=...).map_dataframe(func, ...)</code> facets any plotting function.'),
        tags('small multiples', 'FacetGrid', 'relplot', 'catplot', 'displot', 'col_wrap', 'set_titles', 'map_dataframe'),
    ),
    analogy('Small multiples are a <strong>comic strip</strong>: the same frame drawn several times with one thing changing, so the change jumps out. One '
            'crowded frame with everything layered is a riddle.'),
    facet_anim(),
    real_world(
        scenario('Course × centre review',
                 p('Nine overlapping lines are unreadable. A 3 × 3 grid (rows = course, columns = centre) of study hours vs final score, with the same axes and a '
                   'reference line at the pass mark, lets the academic committee spot the one combination that behaves differently.')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            sns.set_theme(style='whitegrid')
            g = sns.relplot(data=df, x='study_hours', y='final_score', col='centre', row='course', hue='method',
                            s=12, alpha=0.6, height=2.3, aspect=1.15, facet_kws=dict(margin_titles=True))
            g.refline(y=50, color='red', linestyle=':')
            g.set_axis_labels('study hours', 'final score')
            g.figure.suptitle('relplot: rows = course, columns = centre', y=1.02)
            plt.show()
            print('grid shape:', g.axes.shape)

            g = sns.catplot(data=df, x='method', y='post_test', col='centre', kind='box', height=3, aspect=0.9, color='#e2e8f0')
            g.map_dataframe(sns.stripplot, x='method', y='post_test', size=2, alpha=0.4, color='#0f766e')
            g.set_titles('{col_name}')
            g.figure.suptitle('catplot(kind="box") + stripped points per centre', y=1.04)
            plt.show()

            term['month'] = term['date'].dt.strftime('%m %b')
            g = sns.displot(data=term, x='attendance', col='month', col_wrap=3, hue='centre', kind='kde', height=2.2, aspect=1.4)
            g.figure.suptitle('displot with col_wrap=3', y=1.03)
            plt.show()
        """, setup=STUDENTS + TERM, title=S),
        title='Example: 3 × 3 relplot Grid, Faceted Box + Strip, Wrapped KDEs'),
    steps(
        ('Choose the faceting variables', 'col / row for categories you want to compare.'),
        ('Keep axes shared', 'Default in figure-level functions; do not unshare without reason.'),
        ('Limit panels', 'col_wrap for many levels; aggregate rare levels.'),
        ('Add common references', 'g.refline, consistent hue colours.'),
        ('Tidy labels', 'g.set_titles, g.set_axis_labels, suptitle.'),
        title='Steps to Build Small Multiples'),
    crossq(
        ('Why small multiples instead of one chart with many colours?', 'Beyond 4–5 overlapping series, colours become hard to separate; separate panels with shared axes keep each series readable and comparable.'),
        ('How do you add a custom plot to every facet?', 'g.map_dataframe(function, x=..., y=...) or loop over g.axes_dict.items().'),
        ('Why can catplot\'s figure not be placed into my subplots?', 'Figure-level functions create their own figure; for embedding use the axes-level function with ax=.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('How do pairplot and jointplot help in exploratory data analysis?', 'pairplot & jointplot', minutes=8, cards=[
    definition(
        defbox('<code>sns.pairplot(df, vars=[...], hue=...)</code> draws a <strong>scatter-plot matrix</strong>: every numeric variable against every other, with '
               'distributions on the diagonal (<code>diag_kind=\'kde\'|\'hist\'</code>). It is a fast first look at relationships, clusters and outliers; '
               '<code>corner=True</code> removes the redundant upper triangle. <code>sns.PairGrid</code> gives full control of upper/lower/diagonal plots.',
               '<code>sns.jointplot(x, y, kind=\'scatter\'|\'hex\'|\'kde\'|\'reg\')</code> shows one relationship in detail with the two marginal '
               'distributions on the sides; <code>JointGrid</code> customises it. Both scale badly with many variables (k² panels) or many rows — select '
               'variables and sample rows.'),
        tags('pairplot', 'PairGrid', 'corner', 'diag_kind', 'jointplot', 'JointGrid', 'hexbin', 'EDA'),
    ),
    analogy('A pairplot is a <strong>speed-dating round</strong> where every variable meets every other variable once; a jointplot is the <strong>long dinner '
            'date</strong> with the one pair that looked interesting.'),
    pair_anim(),
    real_world(
        scenario('First look at a new dataset',
                 p('Before any modelling, the analyst runs a corner pairplot of attendance, study hours, pre/post-test and final score coloured by placement. In '
                   'one image she sees that pre- and post-test are strongly related, that attendance and study hours are unrelated, and that placed students sit '
                   'in the upper-right of most panels.')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            sns.set_theme(style='ticks')
            cols = ['attendance', 'study_hours', 'pre_test', 'post_test', 'final_score']
            g = sns.pairplot(df.assign(placed=df.placed.map({0: 'no', 1: 'yes'})), vars=cols, hue='placed', corner=True,
                             diag_kind='kde', plot_kws=dict(s=6, alpha=0.4), height=1.7)
            g.figure.suptitle('pairplot(corner=True, hue="placed")', y=1.01)
            plt.show()
            print(df[cols].corr().round(2).loc[['post_test', 'final_score']])

            j = sns.jointplot(data=df, x='pre_test', y='post_test', kind='hex', height=4.5, gridsize=25, cmap='mako_r')
            j.figure.suptitle('jointplot(kind="hex") with marginal histograms', y=1.02)
            plt.show()

            j = sns.jointplot(data=df, x='study_hours', y='final_score', hue='method', height=4.5, s=12, alpha=0.6)
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Corner pairplot by Placement, Hexbin and Hue jointplots'),
    steps(
        ('Select a handful of numeric variables', 'Five or six; more becomes unreadable.'),
        ('Sample rows if large', 'df.sample(2000) keeps it fast.'),
        ('Run pairplot', 'corner=True, hue for the target or a key group.'),
        ('Zoom into interesting pairs', 'jointplot with kind="hex" or "kde" for dense data.'),
        ('Confirm with numbers', 'Correlations or models; plots suggest, statistics confirm.'),
        title='Steps for Pairwise EDA'),
    crossq(
        ('Why corner=True?', 'The upper triangle repeats the lower one mirrored; removing it halves the clutter.'),
        ('Why use kind="hex" in a jointplot?', 'With many points, a scatter saturates; hexagonal bins show where points are dense.'),
        ('What is the cost of a pairplot?', 'k² panels for k variables and every row drawn in each: slow and cramped for many columns or rows.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How do you build annotated heatmaps and clustermaps in Seaborn, e.g. for a correlation matrix or pivot table?', 'Seaborn heatmap & clustermap', minutes=8, cards=[
    definition(
        defbox('<code>sns.heatmap(matrix, annot=True, fmt=\'.2f\', cmap=..., center=0, vmin=..., vmax=..., linewidths=0.5, mask=...)</code> draws a labelled '
               'heatmap from a DataFrame (index and columns become tick labels) with a colorbar, all in one call. <code>mask=np.triu(...)</code> hides the '
               'redundant upper triangle of a correlation matrix; <code>center=0</code> centres a diverging palette.',
               '<code>sns.clustermap</code> reorders rows and columns by <strong>hierarchical clustering</strong> and draws dendrograms, so similar rows (e.g. '
               'students with similar profiles, or centres with similar monthly patterns) sit together. Use <code>standard_scale</code> or '
               '<code>z_score</code> to compare variables on different scales.'),
        tags('sns.heatmap', 'annot', 'fmt', 'center', 'mask', 'clustermap', 'dendrogram', 'z_score'),
    ),
    analogy('A clustermap is a <strong>seating plan that moves friends next to each other</strong>: after reordering, groups of similar rows form visible '
            'blocks of colour.'),
    sheat_anim(),
    real_world(
        scenario('Which subjects go together?',
                 p('Module scores of 60 students in eight subjects, shown as a clustermap, group the subjects into "programming" and "statistics" blocks and the '
                   'students into profiles — useful for planning electives and remedial classes.')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            cols = ['attendance', 'study_hours', 'pre_test', 'post_test', 'final_score']
            corr = df[cols].corr()
            mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
            fig, ax = plt.subplots(figsize=(6, 4.5))
            sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0, vmin=-1, vmax=1, linewidths=0.5, square=True, ax=ax)
            ax.set_title('Correlation matrix (lower triangle)')
            plt.show()

            pv = df.pivot_table(index='course', columns='centre', values='placed', aggfunc='mean') * 100
            fig, ax = plt.subplots(figsize=(5.5, 2.8))
            sns.heatmap(pv, annot=True, fmt='.0f', cmap='Greens', cbar_kws=dict(label='% placed'), ax=ax)
            ax.set_title('Placement % by course and centre')
            plt.show()

            # simulated module scores: two latent skills -> two blocks of subjects
            rng = np.random.default_rng(4)
            prog, stat = rng.normal(0, 1, (2, 60))
            subj = {'Python': prog, 'Java': prog, 'Spark': prog, 'DSA': prog,
                    'Statistics': stat, 'ML': stat, 'R': stat, 'Excel': stat}
            marks = pd.DataFrame({k: 60 + 10 * v + rng.normal(0, 6, 60) for k, v in subj.items()})
            g = sns.clustermap(marks.sample(frac=1, axis=1, random_state=1), z_score=1, cmap='vlag', center=0,
                               figsize=(6, 6), dendrogram_ratio=0.15, yticklabels=False)
            g.figure.suptitle('clustermap: subjects regroup into two skill blocks', y=1.02)
            plt.show()
            print('column order after clustering:', [t.get_text() for t in g.ax_heatmap.get_xticklabels()])
        """, setup=STUDENTS, title=S),
        title='Example: Masked Correlation Heatmap, Annotated Pivot Table, Clustermap'),
    steps(
        ('Prepare a matrix', 'corr(), pivot_table or a wide DataFrame.'),
        ('Choose palette and centre', 'Diverging with center=0 for correlations; sequential otherwise.'),
        ('Annotate if small', 'annot=True, fmt to control decimals.'),
        ('Mask redundancy', 'Upper triangle of symmetric matrices.'),
        ('Cluster to find structure', 'clustermap with z_score/standard_scale.'),
        title='Steps for Seaborn Heatmaps'),
    crossq(
        ('Why use z_score=1 in the clustermap?', 'It standardises each column so subjects with higher averages do not dominate the colours and the clustering.'),
        ('Why centre the colormap at 0 for correlations?', 'So "no correlation" is the neutral colour and positive/negative values get opposite hues of equal intensity.'),
        ('When is annot=True a bad idea?', 'For large matrices: dozens of tiny numbers become unreadable noise; rely on colour and provide the table separately.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you control Seaborn\'s look: themes, contexts, palettes and custom colour mappings?', 'Seaborn Themes & Palettes', minutes=7, cards=[
    definition(
        defbox('<code>sns.set_theme(style=..., context=..., palette=..., font_scale=...)</code> sets global defaults. <strong>Styles</strong>: darkgrid, whitegrid, '
               'dark, white, ticks. <strong>Contexts</strong> scale fonts and lines for the destination: paper &lt; notebook &lt; talk &lt; poster. '
               '<code>sns.despine()</code> removes the top/right spines; <code>sns.axes_style()</code> / <code>plotting_context()</code> work as '
               'temporary <code>with</code> blocks.',
               '<strong>Palettes</strong>: <code>sns.color_palette(\'deep\'|\'colorblind\'|\'Set2\'|\'rocket\'|\'mako\'|\'vlag\', n)</code>, '
               '<code>light_palette</code>, <code>blend_palette</code>, or a dict <code>palette={\'flipped\': \'#10b981\', \'traditional\': \'#94a3b8\'}</code> to '
               'fix colours per category across every chart. \'colorblind\' is a safe default for categorical data.'),
        tags('set_theme', 'style', 'context', 'font_scale', 'despine', 'color_palette', 'colorblind', 'palette dict'),
    ),
    analogy('Themes are <strong>dress codes</strong> (formal for the paper, bold for the poster); palettes are <strong>team jerseys</strong> — once flipped is '
            'green, it must be green on every chart in the report.'),
    theme_anim(),
    real_world(
        scenario('One look across a 20-chart report',
                 p('The analyst sets the theme once, uses context="talk" for the slides and "paper" for the PDF, and passes the same palette dictionary to every '
                   'plot so "flipped" is always green and "traditional" always grey.')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            for style in ['darkgrid', 'whitegrid', 'white', 'ticks']:
                with sns.axes_style(style):                       # temporary style for this figure only
                    fig, ax = plt.subplots(figsize=(3.4, 2.3))
                    sns.histplot(df['final_score'], bins=15, ax=ax)
                    ax.set_title(f'style="{style}"')
            plt.show()

            for name in ['deep', 'colorblind', 'Set2', 'rocket', 'mako', 'vlag']:
                pal = sns.color_palette(name, 6)
                print(f'{name:10}', pal.as_hex())
            sns.palplot(sns.color_palette('colorblind', 8))
            plt.title('colorblind palette')
            plt.show()

            sns.set_theme(style='ticks', context='talk', font_scale=0.8)
            colours = {'flipped': '#10b981', 'traditional': '#94a3b8'}
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.kdeplot(data=df, x='post_test', hue='method', palette=colours, fill=True, common_norm=False, ax=ax)
            sns.despine()
            ax.set_title('context="talk" + fixed palette dict')
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Four Styles, Palette Hex Codes, Talk Context with a Fixed Palette'),
    steps(
        ('Set the theme once', 'sns.set_theme at the top of the notebook or script.'),
        ('Match the context to the medium', 'paper / notebook / talk / poster.'),
        ('Fix category colours', 'palette={...} dictionary reused everywhere.'),
        ('Prefer accessible palettes', '"colorblind", viridis family; avoid red-green pairs.'),
        ('Clean up', 'sns.despine(); temporary styles with with-blocks.'),
        title='Steps to Style Seaborn Charts'),
    crossq(
        ('Why use a palette dictionary instead of a palette name?', 'With a name, colours follow the order categories appear in each chart; a dict guarantees the same colour for the same category everywhere.'),
        ('What does context="talk" change?', 'It scales fonts, line widths and markers up so charts stay legible on a projector.'),
        ('Does set_theme affect plain Matplotlib plots?', 'Yes; it changes Matplotlib rcParams, so all subsequent figures use the theme.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('How do you customise Seaborn charts with Matplotlib: titles, legends, annotations and combining layers?', 'Seaborn + Matplotlib Together', minutes=8, cards=[
    definition(
        defbox('Every axes-level Seaborn function returns a Matplotlib <code>Axes</code>, and figure-level functions return a grid with <code>.figure</code> and '
               '<code>.axes</code>. So all Matplotlib tools apply: <code>ax.set(...)</code>, <code>ax.annotate</code>, <code>ax.axhline</code>, tick formatters, '
               'and layering several Seaborn calls on the same <code>ax</code> (e.g. violin + strip + point estimate).',
               'Legends: <code>sns.move_legend(ax, \'upper left\', bbox_to_anchor=(1, 1), title=...)</code> relocates a Seaborn legend reliably; '
               '<code>legend=False</code> suppresses one. Bar values: <code>ax.bar_label(ax.containers[0], fmt=...)</code>. The figure is saved with '
               '<code>fig.savefig</code> or <code>g.savefig</code>.'),
        tags('returned Axes', 'layering', 'move_legend', 'bar_label', 'ax.containers', 'annotate', 'g.figure'),
    ),
    analogy('Seaborn builds the <strong>house</strong>; Matplotlib is the <strong>interior decorator</strong> who adds the signs, moves the furniture (legend) '
            'and hangs the labels. Both work in the same rooms.'),
    combine_anim(),
    real_world(
        scenario('A presentation-ready chart',
                 p('A Seaborn barplot of placement rate by course becomes slide-ready with Matplotlib finishing: percentage tick labels, value labels on bars, a '
                   'target line with its label, a message title, and the legend moved outside the plot.')),
    ),
    example(
        data_note(),
        vizrun("""
            import seaborn as sns
            from matplotlib.ticker import PercentFormatter
            sns.set_theme(style='whitegrid')
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(data=df, x='course', y='placed', hue='method', errorbar=None,
                        palette={'flipped': '#10b981', 'traditional': '#94a3b8'}, ax=ax)
            for c in ax.containers:
                ax.bar_label(c, labels=[f'{v:.0%}' for v in c.datavalues], padding=2)
            ax.yaxis.set_major_formatter(PercentFormatter(1))
            ax.axhline(0.40, color='#ef4444', linestyle='--', linewidth=1)
            ax.text(2.45, 0.385, 'target 40 %', color='#ef4444', ha='right', va='top')
            ax.set(title='Only flipped PG-DAI students beat the 40 % placement target', xlabel='', ylabel='placed', ylim=(0, 0.55))
            sns.move_legend(ax, 'upper left', bbox_to_anchor=(1, 1), title='method', frameon=False)
            sns.despine(left=True)
            plt.show()

            fig, ax = plt.subplots(figsize=(8, 4))
            order = ['Kharghar', 'Juhu', 'Pune']
            sns.violinplot(data=df, x='centre', y='final_score', order=order, color='#e0f2fe', inner=None, ax=ax)
            sns.stripplot(data=df, x='centre', y='final_score', order=order, size=2, alpha=0.35, color='#0369a1', ax=ax)
            sns.pointplot(data=df, x='centre', y='final_score', order=order, estimator='median', errorbar=None,
                          color='#ef4444', markers='D', linestyles='', ax=ax)
            top = df.loc[df.final_score.idxmax()]
            ax.annotate(f'top score {top.final_score}', xy=(order.index(top.centre), top.final_score),
                        xytext=(25, -8), textcoords='offset points', arrowprops=dict(arrowstyle='->'))
            ax.set(title='Three seaborn layers on one axes: violin + points + median (red)')
            plt.show()
            print(df.groupby('centre')['final_score'].median())
        """, setup=STUDENTS, title=S),
        title='Example: Finishing a Seaborn Barplot with Matplotlib, and Layering Three Seaborn Plots'),
    steps(
        ('Draw with Seaborn on an ax you created', 'fig, ax = plt.subplots(); sns.xxx(..., ax=ax).'),
        ('Layer more plots on the same ax', 'Strip over violin, point estimates on top.'),
        ('Finish with Matplotlib', 'Formatters, bar_label, reference lines, annotations.'),
        ('Fix the legend', 'sns.move_legend(ax, ...) or legend=False.'),
        ('Save', 'fig.savefig(..., bbox_inches="tight").'),
        title='Steps to Customise Seaborn with Matplotlib'),
    crossq(
        ('How do you add value labels to a seaborn barplot?', 'Loop over ax.containers and call ax.bar_label(container, ...); each hue level is one container.'),
        ('Why use sns.move_legend instead of ax.legend(loc=...)?', 'Calling ax.legend recreates the legend and can lose Seaborn\'s handles and title; move_legend keeps them.'),
        ('How do you change titles of a FacetGrid?', 'g.set_titles("{col_name}") for panels and g.figure.suptitle(...) for the whole figure.'),
    ),
]),
])
