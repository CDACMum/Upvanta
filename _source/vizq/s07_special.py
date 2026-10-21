from build import *
from vizq.anims import *
from vizq.runner import vizrun, pyshow
from vizq.data import STUDENTS, data_note, TERM, term_note

S = 'Python (Matplotlib) · uses sample data'
P = 'Python (Matplotlib)'

SECTION = dict(level='advanced', title='Specialised Charts', questions=[

# ------------------------------------------------------------------ 31
Q('When do you use area, stacked area and step charts? How do you build them?', 'Area, Stacked Area & Step Charts', minutes=7, cards=[
    definition(
        defbox('<code>ax.fill_between(x, y)</code> draws an <strong>area chart</strong>: a line with the area below it filled, emphasising volume. '
               '<code>ax.stackplot(x, y1, y2, ..., labels=...)</code> stacks several series to show how a <strong>total and its composition</strong> change over '
               'time; only the bottom layer and the total are easy to read precisely, so keep layers few and put the most stable one at the bottom. Normalising '
               'each time point to 100 % shows shares instead of amounts.',
               '<strong>Step charts</strong> (<code>ax.step(x, y, where=\'post\')</code> or <code>ax.stairs</code>) show values that change at discrete moments '
               'and stay constant in between — fee slabs, seat counts, cumulative registrations, inventory. <code>where</code> controls whether the step happens '
               'before, at or after each x.'),
        tags('fill_between', 'stackplot', 'stacked area', '100 % area', 'ax.step', 'where=', 'cumulative counts'),
    ),
    analogy('A stacked area chart is a <strong>layered cake seen from the side</strong> as it grows over time: the overall height is clear, the thickness of a '
            'middle layer is not. A step chart is a <strong>staircase</strong>: flat until the next step.'),
    area_anim(),
    real_world(
        scenario('Admissions season',
                 p('A step chart of cumulative confirmed admissions per day shows exactly when seats filled after each counselling round; a stacked area shows how '
                   'the confirmed seats split between PG-DBDA, PG-DAC and PG-DAI, and a 100 % version shows whether the mix shifted over the season.')),
    ),
    example(
        vizrun("""
            rng = np.random.default_rng(5)
            days = pd.date_range('2026-06-01', periods=40)
            rounds = {'2026-06-05': 1, '2026-06-15': 2, '2026-06-25': 3}
            boost = np.zeros(40)
            for d in rounds:
                i = days.get_loc(pd.Timestamp(d)); boost[i:i + 3] += 25
            daily = {c: rng.poisson(lam * (1 + boost / 10)) for c, lam in [('PG-DBDA', 4), ('PG-DAC', 3), ('PG-DAI', 1.6)]}
            cum = pd.DataFrame(daily, index=days).cumsum()
            print(cum.iloc[[9, 19, 29, 39]])

            fig, axes = plt.subplots(1, 3, figsize=(14, 3.6), layout='constrained')
            axes[0].step(cum.index, cum.sum(axis=1), where='post', color='#0f766e', linewidth=2)
            for d in rounds:
                axes[0].axvline(pd.Timestamp(d), color='gray', linestyle=':')
            axes[0].set_title('step: cumulative admissions (dotted = counselling rounds)')
            axes[1].stackplot(cum.index, cum.T.values, labels=cum.columns, colors=['#0f766e', '#5eead4', '#cbd5e1'])
            axes[1].legend(loc='upper left', frameon=False); axes[1].set_title('stackplot: total and composition')
            share = cum.div(cum.sum(axis=1), axis=0) * 100
            axes[2].stackplot(share.index, share.T.values, colors=['#0f766e', '#5eead4', '#cbd5e1'])
            axes[2].set(ylim=(0, 100), title='100 % stacked area: the mix stays stable')
            for ax in axes:
                ax.tick_params(axis='x', rotation=30)
            plt.show()
        """, title=P),
        title='Example: Cumulative Step Chart, Stacked Area and 100 % Area of Admissions'),
    steps(
        ('Decide amount vs share', 'Stacked area for totals; 100 % area for composition.'),
        ('Order the layers', 'Most important or most stable at the bottom.'),
        ('Limit layers', 'Three to five; group the rest.'),
        ('Use steps for discrete changes', 'ax.step(..., where="post") for counts that jump.'),
        ('Mark events', 'axvline for rounds, launches, policy changes.'),
        title='Steps for Area and Step Charts'),
    crossq(
        ('Why are middle layers of a stacked area hard to read?', 'Their baseline moves with the layers below, so readers must judge thickness, not position.'),
        ('Line chart or area chart?', 'Area emphasises magnitude (filled volume) and only makes sense from a zero baseline; lines are better for comparing several series.'),
        ('What does where="post" mean in ax.step?', 'The value at x[i] holds until x[i+1]: the step happens at the next point, which suits "value from this day onward".'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('How do you draw a polar (radar) chart, and when is it appropriate?', 'Polar & Radar Charts', minutes=7, cards=[
    definition(
        defbox('Matplotlib supports polar axes (<code>plt.subplots(subplot_kw=dict(projection=\'polar\'))</code>), where x is an angle and y a radius. A '
               '<strong>radar (spider) chart</strong> plots several variables on spokes and joins them into a polygon — repeat the first point to close the '
               'shape, and set the spoke labels with <code>ax.set_xticks(angles, labels)</code>.',
               'Radar charts suit a <strong>profile of a few entities</strong> on 4–8 variables measured on the <strong>same scale</strong> (e.g. skill scores '
               'out of 100). They distort with different scales or many entities, area exaggerates differences, and variable order changes the shape; a grouped '
               'bar chart or parallel coordinates is often more precise. Polar axes are natural for <strong>cyclic data</strong> (hour of day, direction).'),
        tags('polar axes', 'radar chart', 'spider chart', 'closing the polygon', 'cyclic data', 'profiles'),
    ),
    analogy('A radar chart is a <strong>character sheet in a video game</strong>: one glance shows whether a player is a balanced all-rounder or a specialist. '
            'Compare too many players at once and the sheet becomes a tangle.'),
    radar_anim(),
    real_world(
        scenario('Student skill profiles for mentoring',
                 p('Each student\'s scores in Python, SQL, Statistics, ML, Big Data and Communication are drawn as a radar against the batch average, giving '
                   'mentors an at-a-glance view of strengths and gaps during one-to-one meetings.')),
    ),
    example(
        vizrun("""
            skills = ['Python', 'SQL', 'Statistics', 'ML', 'Big Data', 'Communication']
            profiles = {'batch average': [68, 72, 61, 58, 55, 66],
                        'Asha': [88, 80, 75, 82, 70, 60],
                        'Rohan': [60, 85, 50, 45, 72, 84]}
            angles = np.linspace(0, 2 * np.pi, len(skills), endpoint=False).tolist()
            fig, ax = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(projection='polar'))
            for (name, vals), colour in zip(profiles.items(), ['#94a3b8', '#0f766e', '#f59e0b']):
                v = vals + vals[:1]; a = angles + angles[:1]            # close the polygon
                ax.plot(a, v, color=colour, linewidth=2, label=name)
                ax.fill(a, v, color=colour, alpha=0.12)
            ax.set_xticks(angles, skills)
            ax.set_ylim(0, 100); ax.set_yticks([25, 50, 75], ['25', '50', '75'], color='gray')
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), frameon=False)
            ax.set_title('Skill profiles vs batch average', pad=20)
            plt.show()

            # cyclic data: lab logins by hour of day on a polar bar chart
            rng = np.random.default_rng(2)
            hours = np.r_[rng.normal(11, 1.5, 3000), rng.normal(19, 2, 2500)] % 24
            counts, _ = np.histogram(hours, bins=24, range=(0, 24))
            theta = np.linspace(0, 2 * np.pi, 24, endpoint=False)
            fig, ax = plt.subplots(figsize=(4.8, 4.8), subplot_kw=dict(projection='polar'))
            ax.bar(theta, counts, width=2 * np.pi / 24, color='#0ea5e9', edgecolor='white')
            ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
            ax.set_xticks(theta[::3], [f'{h:02d}:00' for h in range(0, 24, 3)])
            ax.set_title('Lab logins by hour (clock layout)', pad=15)
            plt.show()
            print('peak hours:', np.argsort(counts)[-2:][::-1])
        """, title=P),
        title='Example: Radar Chart of Two Students vs the Batch, and a 24-Hour Polar Bar Chart'),
    steps(
        ('Check suitability', 'Few entities, 4–8 variables on one scale; or cyclic data.'),
        ('Compute angles', 'np.linspace(0, 2π, n, endpoint=False).'),
        ('Close the polygon', 'Append the first value and angle again.'),
        ('Label spokes and radius', 'set_xticks(angles, labels); fixed set_ylim.'),
        ('Compare with a reference', 'Batch average as a grey polygon.'),
        title='Steps for a Radar Chart'),
    crossq(
        ('Why must the radar polygon be closed manually?', 'ax.plot connects points in order; without repeating the first point the last spoke is not joined back to the start.'),
        ('Why do radar charts exaggerate differences?', 'Readers see area, which grows with the square of the radius, and the shape depends on the arbitrary order of the spokes.'),
        ('When is a polar axis the natural choice?', 'For cyclic variables where the end meets the start: hours of a day, days of a week, compass directions.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('How do you visualise machine-learning results: confusion matrix, ROC and precision-recall curves, feature importance?', 'Charts for ML Results', minutes=9, cards=[
    definition(
        defbox('scikit-learn provides display classes that draw on Matplotlib axes: <code>ConfusionMatrixDisplay.from_predictions(y_true, y_pred, ax=...)</code> '
               '(optionally <code>normalize=\'true\'</code> for recall per class), <code>RocCurveDisplay.from_predictions</code> (TPR vs FPR with AUC) and '
               '<code>PrecisionRecallDisplay.from_predictions</code> (better for imbalanced classes). Several models can share one axes for comparison.',
               'Feature importance is a sorted horizontal bar chart (permutation importance with error bars is more trustworthy than impurity importance). '
               'Other useful views: predicted-vs-actual scatter with a 45° line for regression, residual plots, calibration curves '
               '(<code>CalibrationDisplay</code>), and learning curves.'),
        tags('ConfusionMatrixDisplay', 'RocCurveDisplay', 'PrecisionRecallDisplay', 'feature importance', 'calibration', 'predicted vs actual'),
    ),
    analogy('Model charts are the <strong>report card of a model</strong>: the confusion matrix lists which questions it got wrong, the ROC curve shows how its '
            'grade changes with the pass mark, and feature importance shows which subjects carried the score.'),
    mlviz_anim(),
    real_world(
        scenario('Presenting the placement model',
                 p('For the placement committee, the analyst shows a normalised confusion matrix (how many placed students the model misses), ROC and PR curves '
                   'comparing logistic regression with a random forest, and a permutation-importance chart explaining what drives the predictions.')),
    ),
    example(
        data_note(),
        vizrun("""
            from sklearn.model_selection import train_test_split
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.inspection import permutation_importance
            from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay, PrecisionRecallDisplay
            X = df[['attendance', 'study_hours', 'pre_test', 'post_test']]; y = df['placed']
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
            models = {'logistic': LogisticRegression(max_iter=1000).fit(X_tr, y_tr),
                      'forest': RandomForestClassifier(300, min_samples_leaf=5, random_state=0).fit(X_tr, y_tr)}

            fig, axes = plt.subplots(1, 3, figsize=(14, 4), layout='constrained')
            ConfusionMatrixDisplay.from_predictions(y_te, models['logistic'].predict(X_te), normalize='true',
                                                    display_labels=['not placed', 'placed'], cmap='Blues', values_format='.2f', ax=axes[0])
            axes[0].set_title('Logistic: confusion matrix (rows = truth)')
            for name, m in models.items():
                p = m.predict_proba(X_te)[:, 1]
                RocCurveDisplay.from_predictions(y_te, p, name=name, ax=axes[1])
                PrecisionRecallDisplay.from_predictions(y_te, p, name=name, ax=axes[2])
            axes[1].plot([0, 1], [0, 1], 'k:', linewidth=1); axes[1].set_title('ROC curves')
            axes[2].axhline(y_te.mean(), color='gray', linestyle=':', label='baseline'); axes[2].set_title('Precision-recall curves')
            plt.show()

            imp = permutation_importance(models['forest'], X_te, y_te, n_repeats=20, random_state=0, scoring='roc_auc')
            order = np.argsort(imp.importances_mean)
            fig, ax = plt.subplots(figsize=(7, 3))
            ax.barh(X.columns[order], imp.importances_mean[order], xerr=imp.importances_std[order], color='#0f766e', capsize=3)
            ax.set(title='Permutation importance (drop in test AUC)', xlabel='mean decrease in AUC')
            plt.show()
            print({c: round(float(v), 3) for c, v in zip(X.columns, imp.importances_mean)})
        """, setup=STUDENTS, title='Python (scikit-learn · Matplotlib) · uses sample data'),
        title='Example: Confusion Matrix, ROC and PR Curves for Two Models, Permutation Importance'),
    steps(
        ('Hold out a test set', 'Charts of training data flatter the model.'),
        ('Confusion matrix', 'Normalise by true class to read recall per class.'),
        ('Ranking quality', 'ROC for balanced data; precision-recall for rare positives.'),
        ('Explain', 'Sorted permutation importance with error bars.'),
        ('Compare models on the same axes', 'Same test set, same colours across charts.'),
        title='Steps to Visualise Model Results'),
    crossq(
        ('Why normalise the confusion matrix by row?', 'Each row then shows the share of a true class predicted as each label; the diagonal is recall per class, independent of class sizes.'),
        ('ROC or precision-recall curve?', 'With rare positives, ROC can look excellent while precision is poor; the PR curve shows the trade-off that matters.'),
        ('Why prefer permutation importance?', 'Impurity importance from trees is computed on training data and favours high-cardinality features; permutation importance measures the real drop on test data.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('When should you use 3-D plots, and what are better alternatives?', '3-D Plots', minutes=7, cards=[
    definition(
        defbox('Matplotlib\'s <code>mplot3d</code> toolkit (<code>projection=\'3d\'</code>) draws <code>plot_surface</code>, <code>plot_wireframe</code>, 3-D '
               '<code>scatter</code> and <code>contour</code> plots; <code>ax.view_init(elev, azim)</code> sets the viewing angle. They are useful for '
               '<strong>exploring a function of two variables</strong> (a loss surface, a model\'s prediction surface) or physical 3-D data, especially '
               'interactively.',
               'For communication, 3-D plots on a flat page hide values behind others, make depth ambiguous and depend on the viewing angle. Better: '
               '<strong>contour plots</strong> or <strong>heatmaps</strong> (<code>ax.contourf</code>) for surfaces, small multiples or colour/size encoding for '
               'a third variable. Never use 3-D bars or pies for ordinary 2-D data.'),
        tags('mplot3d', "projection='3d'", 'plot_surface', 'view_init', 'contourf', 'occlusion', 'alternatives'),
    ),
    analogy('A 3-D chart on paper is a <strong>photo of a sculpture</strong>: impressive, but you cannot walk around it. A contour plot is the <strong>map with '
            'height lines</strong>: less dramatic, but every value can be read.'),
    threed_anim(),
    real_world(
        scenario('How do attendance and study hours combine?',
                 p('A model predicts placement probability from attendance and study hours. A 3-D surface impresses in a demo, but the contour version with '
                   'labelled 50 % and 75 % probability lines is what mentors can actually use: "below this line, intervene".')),
    ),
    example(
        data_note(),
        vizrun("""
            from sklearn.linear_model import LogisticRegression
            m = LogisticRegression().fit(df[['attendance', 'study_hours']], df['placed'])
            A, H = np.meshgrid(np.linspace(55, 100, 60), np.linspace(0, 25, 60))
            grid = pd.DataFrame({'attendance': A.ravel(), 'study_hours': H.ravel()})
            P = m.predict_proba(grid)[:, 1].reshape(A.shape)
            print('coefficients:', m.coef_.round(3), 'intercept:', m.intercept_.round(2))

            fig = plt.figure(figsize=(13, 4.2))
            ax = fig.add_subplot(1, 3, 1, projection='3d')
            ax.plot_surface(A, H, P, cmap='viridis', linewidth=0, antialiased=True)
            ax.set(xlabel='attendance', ylabel='study hours', zlabel='P(placed)', title='3-D surface (view 1)')
            ax.view_init(elev=25, azim=-60)
            ax = fig.add_subplot(1, 3, 2, projection='3d')
            ax.plot_surface(A, H, P, cmap='viridis', linewidth=0)
            ax.view_init(elev=10, azim=30); ax.set_title('same surface (view 2)')
            ax = fig.add_subplot(1, 3, 3)
            cf = ax.contourf(A, H, P, levels=10, cmap='viridis')
            cs = ax.contour(A, H, P, levels=[0.25, 0.5, 0.75], colors='white', linewidths=1.5)
            ax.clabel(cs, fmt='%.2f')
            ax.scatter(df.attendance, df.study_hours, s=4, c=df.placed, cmap='coolwarm', alpha=0.5)
            fig.colorbar(cf, ax=ax, label='P(placed)')
            ax.set(xlabel='attendance', ylabel='study hours', title='contour: every value readable')
            fig.tight_layout()
            plt.show()
        """, setup=STUDENTS, title='Python (Matplotlib · scikit-learn) · uses sample data'),
        title='Example: A Probability Surface in 3-D from Two Angles vs a Labelled Contour Plot'),
    steps(
        ('Ask whether 3-D is needed', 'Usually a contour, heatmap or colour encoding is clearer.'),
        ('Build a grid', 'np.meshgrid over the two inputs; evaluate the function or model.'),
        ('Draw', 'plot_surface for exploration; contourf + labelled contour lines for reports.'),
        ('Choose the view deliberately', 'view_init(elev, azim); show several angles if 3-D.'),
        ('Add the data', 'Overlay observations on the contour map.'),
        title='Steps for Surfaces and 3-D Data'),
    crossq(
        ('Why do 3-D bar charts mislead?', 'Perspective makes nearer bars look bigger, bars hide each other, and heights cannot be read against an axis.'),
        ('How do you show a third numeric variable without 3-D?', 'Colour (with a colorbar), marker size, small multiples by bins of the variable, or contour lines.'),
        ('When is interactive 3-D worthwhile?', 'For genuine spatial data (molecules, terrain, sensor positions) where the viewer can rotate the plot.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How do you animate a Matplotlib chart with FuncAnimation and save it as a GIF?', 'Animations', minutes=8, cards=[
    definition(
        defbox('<code>matplotlib.animation.FuncAnimation(fig, update, frames=..., interval=ms)</code> calls an <code>update(frame)</code> function for each frame; '
               'the function changes existing artists (<code>line.set_data</code>, <code>bar.set_height</code>, <code>text.set_text</code>) rather than redrawing '
               'the whole figure, and returns them (needed for <code>blit=True</code>).',
               'Save with <code>anim.save(\'file.gif\', writer=\'pillow\', fps=...)</code> (no extra install) or MP4 with ffmpeg. In notebooks, '
               '<code>HTML(anim.to_jshtml())</code> shows a player. Animations suit change over time (racing bars, a growing line, a simulation); keep them short '
               'and also provide a static version for print.'),
        tags('FuncAnimation', 'update function', 'set_data', 'blit', 'PillowWriter', 'GIF', 'to_jshtml'),
    ),
    analogy('FuncAnimation is a <strong>flip book</strong>: you draw the scene once and, page by page, move only what changes. Redrawing every page from scratch '
            'works but is slow.'),
    animate_anim(),
    real_world(
        scenario('Showing the term unfold',
                 p('At the year-end review, a 6-second animation of the 10-day rolling attendance per centre, with a moving date label, makes the exam-week dip and '
                   'the slow decline memorable; the PDF report keeps the static chart.')),
    ),
    example(
        term_note(),
        vizrun("""
            from matplotlib.animation import FuncAnimation
            import os
            s = term.pivot(index='date', columns='centre', values='attendance').rolling(10).mean().dropna() * 100
            frames = range(0, len(s), 4)                      # every 4th day keeps the GIF small

            fig, ax = plt.subplots(figsize=(6.5, 3.4))
            lines = {c: ax.plot([], [], linewidth=2.5, label=c)[0] for c in s.columns}
            label = ax.text(0.02, 0.06, '', transform=ax.transAxes, fontsize=11)
            ax.set(xlim=(s.index[0], s.index[-1]), ylim=(70, 88), ylabel='attendance % (10-day mean)', title='Term attendance, animated')
            ax.legend(loc='upper right', frameon=False, ncol=3)
            fig.autofmt_xdate()

            def update(i):
                for c, line in lines.items():
                    line.set_data(s.index[:i + 1], s[c].iloc[:i + 1])
                label.set_text(f'{s.index[i]:%d %b %Y}')
                return [*lines.values(), label]

            anim = FuncAnimation(fig, update, frames=frames, interval=120, blit=True)
            anim.save('term_attendance.gif', writer='pillow', fps=8, dpi=70)
            print(f'frames: {len(frames)}, GIF size: {os.path.getsize("term_attendance.gif") / 1024:.0f} KB')
            plt.close(fig)                                     # the GIF below is the result
        """, setup=TERM, title=S),
        title='Example: Animate the Rolling Attendance Lines and Save a GIF'),
    steps(
        ('Draw the static scene once', 'Axes limits, empty lines, labels.'),
        ('Write update(frame)', 'Change data of existing artists; return them.'),
        ('Create FuncAnimation', 'frames, interval, blit=True for speed.'),
        ('Save', 'anim.save("x.gif", writer="pillow", fps=...) or MP4 via ffmpeg.'),
        ('Keep it light', 'Fewer frames, lower dpi; provide a static version too.'),
        title='Steps to Animate a Chart'),
    crossq(
        ('Why fix the axis limits before animating?', 'Otherwise autoscaling changes the axes on every frame, making the chart jump and hiding real change.'),
        ('What does blit=True do?', 'Only the changed artists are redrawn each frame, which is much faster; update must return those artists.'),
        ('Why keep a reference to the animation object?', 'If anim is garbage-collected (e.g. created inside a function without being stored), the animation stops.'),
    ),
]),
])
