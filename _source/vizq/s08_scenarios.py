from build import *
from vizq.anims import *
from vizq.runner import vizrun, pyshow
from vizq.data import STUDENTS, data_note, TERM, term_note

S = 'Python (Matplotlib) · uses sample data'

SECTION = dict(level='expert', title='Scenario-Based Questions', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: build a one-page placement dashboard figure for the director.', 'One-Page Dashboard', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('A static dashboard is one figure that answers the few questions a decision-maker asks every month. Layout: <strong>KPI tiles</strong> at the top '
               '(big numbers with context: placement rate, median package, students), then 3–4 charts ordered by importance, each with a message title, all '
               'sharing colours and scales.',
               'In Matplotlib, <code>fig.subplot_mosaic</code> places tiles and charts on a grid; KPI tiles are axes with <code>ax.axis(\'off\')</code> and large '
               '<code>ax.text</code>. Save once as PDF (print) and PNG (email/web) with <code>bbox_inches=\'tight\'</code>. For interactive, auto-refreshing '
               'dashboards, tools such as Power BI, Tableau, Streamlit or Dash take over, but the design rules are the same.'),
        tags('dashboard', 'KPI tiles', 'subplot_mosaic', 'layout', 'message titles', 'consistent colours', 'savefig'),
    ),
    analogy('A dashboard is a <strong>car\'s instrument panel</strong>: the few gauges the driver needs, in fixed places, readable at a glance — not every '
            'sensor the engine has.'),
    dash_anim(),
    real_world(
        scenario('Monthly placement review',
                 p('The director wants one page: how many students were placed, at what packages, which centre and course lag, and whether attendance relates to '
                   'placement. The figure is regenerated from the latest data with one script before every review.')),
    ),
    example(
        data_note(),
        vizrun("""
            accent, grey = '#0f766e', '#cbd5e1'
            fig, ax = plt.subplot_mosaic('ABCD;EEFF;GGHH', figsize=(12, 8.5), layout='constrained',
                                         height_ratios=[0.55, 1, 1])
            kpis = [('A', f"{df.placed.mean():.0%}", 'placement rate'), ('B', f"{df.salary_lpa.median():.1f} LPA", 'median package'),
                    ('C', f"{df.salary_lpa.max():.1f} LPA", 'highest package'), ('D', f"{len(df)}", 'students in batch')]
            for k, big, small in kpis:
                ax[k].axis('off')
                ax[k].text(0.5, 0.58, big, ha='center', va='center', fontsize=26, weight='bold', color=accent, transform=ax[k].transAxes)
                ax[k].text(0.5, 0.18, small, ha='center', fontsize=11, color='#475569', transform=ax[k].transAxes)

            r = df.groupby('centre')['placed'].mean().sort_values() * 100
            b = ax['E'].barh(r.index, r, color=[grey, grey, accent]); ax['E'].bar_label(b, fmt='%.0f%%', padding=3)
            ax['E'].set(title='Kharghar leads placements', xlim=(0, 55)); ax['E'].xaxis.set_visible(False)

            c = df.groupby('course')['placed'].mean().sort_values() * 100
            b = ax['F'].barh(c.index, c, color=grey); ax['F'].bar_label(b, fmt='%.0f%%', padding=3)
            ax['F'].set(title='Courses are close (33-37 %)', xlim=(0, 55)); ax['F'].xaxis.set_visible(False)

            ax['G'].hist(df.salary_lpa.dropna(), bins=25, color=accent)
            ax['G'].axvline(df.salary_lpa.median(), color='black', linestyle=':')
            ax['G'].set(title='Most packages are 4-8 LPA', xlabel='package (LPA)')

            band = pd.cut(df.attendance, [55, 65, 75, 85, 100])
            a = df.groupby(band, observed=True)['placed'].mean() * 100
            ax['H'].plot([str(i) for i in a.index], a, 'o-', color=accent, linewidth=2.5)
            ax['H'].set(title='Higher attendance, higher placement', xlabel='attendance band (%)', ylabel='% placed', ylim=(0, 60))
            for k in 'EFGH':
                ax[k].spines[['top', 'right']].set_visible(False)
            fig.suptitle('Placement dashboard — 2026 batch', fontsize=16, weight='bold', x=0.02, ha='left')
            fig.savefig('dashboard.pdf', bbox_inches='tight'); fig.savefig('dashboard.png', dpi=150, bbox_inches='tight')
            plt.show()
            print({str(k): round(v, 1) for k, v in a.items()})
        """, setup=STUDENTS, title=S),
        title='Example: KPI Tiles and Four Message Charts in One Mosaic Figure'),
    steps(
        ('List the decision questions', 'Three to five, agreed with the user.'),
        ('Choose KPIs and charts', 'One chart per question; message titles.'),
        ('Lay out by importance', 'KPIs on top, then left-to-right, top-to-bottom.'),
        ('Unify the style', 'One accent colour, shared scales, removed clutter.'),
        ('Automate', 'A script that reloads data and saves PDF and PNG.'),
        title='Steps to Build a Static Dashboard'),
    crossq(
        ('Why give a KPI context?', 'A bare "35 %" means little; compare with target or last year ("35 %, target 40 %") so the reader knows whether it is good.'),
        ('How many charts belong on one page?', 'Usually four to six; beyond that, the page becomes a data dump and the message is lost.'),
        ('When should you move to a BI tool?', 'When users need filters, drill-down, frequent refresh or many viewers; Matplotlib suits fixed, reproducible reports.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: automate a weekly report — one chart per centre saved as PNGs and a multi-page PDF.', 'Automated Chart Reports', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('Report automation loops over groups, draws the same chart for each with a <strong>function</strong> that takes the data and an Axes, and saves '
               'the result. <code>matplotlib.backends.backend_pdf.PdfPages</code> collects several figures into one multi-page PDF (<code>pdf.savefig(fig)</code>), '
               'and its <code>infodict()</code> stores title and author metadata.',
               'Good practice: use the non-interactive \'Agg\' backend on servers, <strong>close each figure</strong> after saving (<code>plt.close(fig)</code>) '
               'to avoid memory growth, fix axis limits across groups so pages are comparable, name files predictably (<code>attendance_Pune_2026-W30.png</code>), '
               'and schedule the script (cron, Airflow, Task Scheduler).'),
        tags('automation', 'PdfPages', 'plt.close', 'Agg backend', 'consistent limits', 'file naming', 'scheduling'),
    ),
    analogy('An automated report is a <strong>printing press</strong>: set the template once, feed in each centre\'s data, and identical, comparable pages come '
            'out every week without anyone redrawing a chart by hand.'),
    report_anim(),
    real_world(
        scenario('Friday attendance mail',
                 p('Every Friday evening a scheduled job reads the week\'s attendance, writes one PNG per centre for the centre heads and a three-page PDF for the '
                   'director, and attaches them to an email — the same layout, axes and colours every week.')),
    ),
    example(
        term_note(),
        vizrun("""
            import os
            from matplotlib.backends.backend_pdf import PdfPages

            def centre_chart(ax, d, centre):
                d = d.set_index('date')['attendance'] * 100
                ax.plot(d.index, d, color='#94a3b8', linewidth=1)
                ax.plot(d.index, d.rolling(10, center=True).mean(), color='#0f766e', linewidth=2.5)
                ax.axhline(80, color='#ef4444', linestyle='--', linewidth=1)
                ax.set(title=f'{centre}: {(d < 80).mean():.0%} of days below the 80 % target', ylim=(60, 95), ylabel='attendance %')
                ax.spines[['top', 'right']].set_visible(False)

            files = []
            with PdfPages('attendance_report.pdf') as pdf:
                for centre, d in term.groupby('centre'):
                    fig, ax = plt.subplots(figsize=(8, 3))
                    centre_chart(ax, d, centre)
                    name = f'attendance_{centre}_2026-W31.png'
                    fig.savefig(name, dpi=120, bbox_inches='tight')
                    pdf.savefig(fig, bbox_inches='tight')
                    files.append(name)
                    if centre != 'Pune':
                        plt.close(fig)                      # keep only the last one open to show it here
                pdf.infodict().update(Title='Weekly attendance report', Author='C-DAC Kharghar')
            for f in files + ['attendance_report.pdf']:
                print(f'{f:36} {os.path.getsize(f) / 1024:6.1f} KB')
            from pypdf import PdfReader
            print('PDF pages:', len(PdfReader('attendance_report.pdf').pages))
            plt.show()
        """, setup=TERM, title=S),
        title='Example: A Chart Function, One PNG per Centre and a Three-Page PDF'),
    steps(
        ('Write a chart function', 'def chart(ax, data, label): … so every page is identical.'),
        ('Loop over groups', 'groupby, one figure per group (or panels in one figure).'),
        ('Save consistently', 'Predictable names; PdfPages for a combined PDF.'),
        ('Close figures', 'plt.close(fig) after saving to free memory.'),
        ('Schedule and deliver', 'cron / Airflow / Task Scheduler; email or shared drive.'),
        title='Steps to Automate Chart Reports'),
    crossq(
        ('Why does a long-running report script slowly use more memory?', 'Figures stay open in pyplot\'s registry until closed; call plt.close(fig) (Matplotlib warns after 20 open figures).'),
        ('Why fix ylim across centres?', 'So a reader flipping pages compares like with like; autoscaling would make a small dip look as dramatic as a large one.'),
        ('Which backend should a server use?', '"Agg" (non-interactive); interactive backends need a display and fail on headless machines.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: present A/B or multi-group comparison results visually so non-statisticians understand the uncertainty.', 'Visualising Comparisons with Uncertainty', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('Decision-makers need three things: the <strong>size</strong> of each effect, its <strong>uncertainty</strong>, and the <strong>threshold</strong> '
               'that matters. A <strong>forest plot</strong> (dot-and-whisker chart) shows each difference with its 95 % confidence interval on one axis, with a '
               'line at zero ("no effect") and a band for the minimum worthwhile effect. Sorting rows by effect and labelling values makes it readable.',
               'Avoid showing only p-values or bars of means. Complement with the raw distributions (small multiples of histograms or strip plots) so viewers see '
               'how much the groups overlap: a significant 3-mark difference can still mean that most individual students score similarly.'),
        tags('forest plot', 'confidence interval', 'effect size', 'minimum important effect', 'dot-and-whisker', 'overlap'),
    ),
    analogy('A forest plot is a <strong>row of fishing nets</strong>: each net (interval) shows where the true effect could be. Nets entirely right of the zero '
            'line say "real gain"; nets crossing it say "not sure yet".'),
    forest_anim(),
    real_world(
        scenario('Did the flipped classroom work everywhere?',
                 p('For the academic council, the analyst shows the flipped-minus-traditional difference in post-test score for each centre and course with 95 % '
                   'CIs, a zero line and a shaded "at least 2 marks" zone, plus a pair of overlaid distributions to show what a 3.5-mark gain looks like for '
                   'individual students.')),
    ),
    example(
        data_note(),
        vizrun("""
            from scipy import stats
            rows = []
            for kind in ['centre', 'course']:
                for g, d in df.groupby(kind):
                    a = d.loc[d.method == 'flipped', 'post_test']; b = d.loc[d.method == 'traditional', 'post_test']
                    t = stats.ttest_ind(a, b, equal_var=False)
                    lo, hi = t.confidence_interval()
                    rows.append((f'{kind}: {g}', a.mean() - b.mean(), lo, hi, len(a) + len(b)))
            a = df.loc[df.method == 'flipped', 'post_test']; b = df.loc[df.method == 'traditional', 'post_test']
            t = stats.ttest_ind(a, b, equal_var=False); lo, hi = t.confidence_interval()
            rows.append(('ALL STUDENTS', a.mean() - b.mean(), lo, hi, len(df)))
            res = pd.DataFrame(rows, columns=['group', 'diff', 'lo', 'hi', 'n'])
            print(res.round(2).to_string(index=False))

            fig, ax = plt.subplots(figsize=(8, 4))
            y = np.arange(len(res))[::-1]
            colours = ['#0f766e' if lo_ > 0 else '#94a3b8' for lo_ in res['lo']]
            ax.axvspan(2, 10, color='#ccfbf1', alpha=0.6, label='worthwhile (>= 2 marks)')
            ax.axvline(0, color='black', linewidth=1)
            ax.hlines(y, res['lo'], res['hi'], color=colours, linewidth=3)
            ax.scatter(res['diff'], y, color=colours, s=60, zorder=3)
            for yi, (_, r) in zip(y, res.iterrows()):
                ax.text(10.2, yi, f"{r['diff']:+.1f}  [{r['lo']:+.1f}, {r['hi']:+.1f}]  n={r['n']}", va='center', fontsize=9)
            ax.set(yticks=y, yticklabels=res['group'], xlim=(-4, 10), xlabel='flipped minus traditional (post-test marks, 95 % CI)',
                   title='Flipped classroom gain: clear overall, uncertain in some subgroups')
            ax.legend(loc='upper left', bbox_to_anchor=(0, -0.18), frameon=False)
            ax.spines[['top', 'right']].set_visible(False)
            plt.show()

            fig, ax = plt.subplots(figsize=(8, 3))
            ax.hist(b, bins=25, alpha=0.6, color='#94a3b8', label=f'traditional (mean {b.mean():.1f})', density=True)
            ax.hist(a, bins=25, alpha=0.6, color='#0f766e', label=f'flipped (mean {a.mean():.1f})', density=True)
            ax.set(title='A 3.5-mark gain shifts the distribution, but individual scores overlap heavily', xlabel='post-test')
            ax.legend(frameon=False)
            plt.show()
        """, setup=STUDENTS, title=S),
        title='Example: Forest Plot of Subgroup Effects with a Worthwhile Zone, and Overlapping Distributions'),
    steps(
        ('Compute effects and CIs', 'Differences per group with 95 % CIs (t or bootstrap).'),
        ('Draw a forest plot', 'Dots and whiskers, zero line, sorted or grouped rows.'),
        ('Mark what matters', 'Shade the minimum worthwhile effect.'),
        ('Label numbers and n', 'Readers should not need a separate table.'),
        ('Show the raw overlap', 'Overlaid distributions or strip plots.'),
        title='Steps to Visualise Effects with Uncertainty'),
    crossq(
        ('Why colour intervals that exclude zero differently?', 'It guides the eye to groups where the evidence is clear, while still showing the others honestly.'),
        ('Why are subgroup intervals wider than the overall one?', 'Each subgroup has fewer students, so its estimate is less precise; subgroup differences need caution (multiple comparisons).'),
        ('Why show the overlapping distributions as well?', 'An average gain can be real yet small relative to individual variation; the overlap prevents over-promising.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: you receive a new dataset. Which charts make up a fast visual EDA, and in what order?', 'Visual EDA Workflow', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('A repeatable visual <strong>exploratory data analysis</strong> answers, in order: (1) <strong>quality</strong> — missing values per column and '
               'pattern (a missingness matrix or bar chart), duplicates, impossible values; (2) <strong>univariate</strong> — histograms for numbers, bar charts '
               'of counts for categories; (3) <strong>bivariate</strong> — correlation heatmap, scatter or box plots against the target; (4) '
               '<strong>segments and time</strong> — group comparisons and trends.',
               'Automate the first pass with loops over columns (<code>df.select_dtypes</code>) so every new dataset gets the same views in minutes, then '
               'investigate what looks odd. Each chart should lead to an action: fix, exclude, transform, or ask the data owner.'),
        tags('EDA', 'missing values', 'data quality', 'univariate', 'bivariate', 'correlation heatmap', 'automation'),
    ),
    analogy('Visual EDA is a <strong>doctor\'s routine check-up</strong>: temperature, blood pressure and reflexes first, in the same order every time, before any '
            'specialist tests. Most problems are caught by the routine.'),
    eda_anim(),
    real_world(
        scenario('A new feedback-and-results extract',
                 p('The exam cell sends a fresh extract with a few hundred rows. In ten minutes the EDA script shows that one column is a quarter missing (almost all from one '
                   'centre — a form problem), that attendance has impossible values above 100, and that the target relates strongly to two columns.')),
    ),
    example(
        data_note(),
        vizrun("""
            rng = np.random.default_rng(8)
            d = df.copy()
            d.loc[(d.centre == 'Juhu') & (rng.random(len(d)) < 0.75), 'pre_test'] = np.nan      # a form problem at one centre
            d.loc[rng.choice(len(d), 6, replace=False), 'attendance'] = [104, 110, 101, 120, 103, 108]   # impossible values

            num = d.select_dtypes('number').drop(columns=['placed', 'salary_lpa'])     # salary exists only after placement
            fig, axes = plt.subplot_mosaic('AB;CC', figsize=(12, 7), layout='constrained')
            miss = d.isna().mean().sort_values() * 100
            axes['A'].barh(miss.index, miss, color=['#ef4444' if v > 20 else '#94a3b8' for v in miss])
            axes['A'].set(title='1. Missing values per column (%)', xlim=(0, 100))
            axes['B'].imshow(d.sort_values('centre').isna().values, aspect='auto', cmap='Greys', interpolation='nearest')   # rows sorted by centre
            axes['B'].set(title='   missingness matrix, rows sorted by centre (black = missing)', xticks=range(d.shape[1]))
            axes['B'].set_xticklabels(d.columns, rotation=60, ha='right', fontsize=8); axes['B'].set_yticks([])
            corr = num.corrwith(d['placed']).sort_values()
            axes['C'].barh(corr.index, corr, color=['#0f766e' if v > 0 else '#f59e0b' for v in corr])
            axes['C'].set(title='3. Correlation of each numeric column with placed', xlim=(-0.1, 0.5))
            plt.show()
            print(d.groupby('centre')['pre_test'].apply(lambda s: s.isna().mean()).round(2).to_dict())

            fig, axes = plt.subplots(2, 3, figsize=(12, 5.5), layout='constrained')
            for ax, col in zip(axes.flat, num.columns):
                ax.hist(d[col].dropna(), bins=25, color='#0ea5e9')
                ax.set_title(f'2. {col}', fontsize=10)
            axes.flat[0].axvline(100, color='red', linestyle='--')        # attendance cannot exceed 100
            for ax in axes.flat[len(num.columns):]:
                ax.set_axis_off()
            plt.show()
            print('attendance above 100:', sorted(d.loc[d.attendance > 100, 'attendance'].tolist()))
        """, setup=STUDENTS, title=S),
        title='Example: Missingness Bar and Matrix, Correlation with the Target, a Histogram per Column'),
    steps(
        ('Quality first', 'Missing values (by column and pattern), duplicates, impossible ranges.'),
        ('Univariate', 'Histogram per numeric column; counts per category.'),
        ('Against the target', 'Correlations, box plots or rates by category.'),
        ('Segments and time', 'Group comparisons, trends.'),
        ('Turn findings into actions', 'Fix, exclude, transform, or ask the data owner.'),
        title='Steps for a Visual EDA'),
    crossq(
        ('Why sort the missingness matrix?', 'Sorting rows by a column groups missing entries together, revealing whether missingness is random or tied to a group (here, one centre).'),
        ('Why check impossible values before modelling?', 'They distort means, scales and model fits; a histogram with a reference line at the valid limit finds them instantly.'),
        ('Why automate EDA charts?', 'The same checks run on every new extract in minutes, so nothing is forgotten and time goes into interpreting, not drawing.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Scenario: explain a risk model to mentors — show score distributions, the threshold trade-off and one student\'s explanation.', 'Explaining a Model Visually', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('Non-technical users need to see <strong>how scores separate the groups</strong> (overlaid score distributions for placed vs not placed), '
               '<strong>what a threshold means in people</strong> (precision and recall, or "students flagged" vs "real cases caught", as the threshold moves), '
               'and <strong>why one student got their score</strong> (a contribution chart: how each feature pushed the score up or down from the average).',
               'For a logistic model, contributions on the log-odds scale are coefficient × (value − mean); a horizontal bar chart sorted by size, green for '
               'positive and red for negative, is a simple "waterfall-style" explanation. Use plain-language labels ("+0.8 because attendance is 95 %") and the '
               'same colours across all charts.'),
        tags('score distribution', 'threshold trade-off', 'precision / recall', 'local explanation', 'contributions', 'waterfall chart'),
    ),
    analogy('Explaining a model is like a <strong>doctor showing an X-ray</strong>: the overall picture (score distributions), where the line between "fine" and '
            '"needs care" is drawn (threshold), and an arrow pointing at the exact spot for this patient (contributions).'),
    explain_anim(),
    real_world(
        scenario('Mentoring list for students at risk of not being placed',
                 p('Mentors can call about 120 students. The threshold chart shows how many truly unplaced students that list catches; each mentor also receives a '
                   'one-student explanation chart so the conversation starts from concrete reasons ("study hours are well below the batch").')),
    ),
    example(
        data_note(),
        vizrun("""
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import precision_recall_curve
            feats = ['attendance', 'study_hours', 'post_test']
            X = df[feats]; y = 1 - df['placed']                       # target: NOT placed (at risk)
            m = LogisticRegression(max_iter=1000).fit(X, y)
            risk = m.predict_proba(X)[:, 1]

            fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), layout='constrained')
            axes[0].hist(risk[y == 0], bins=25, alpha=0.6, color='#0f766e', label='placed', density=True)
            axes[0].hist(risk[y == 1], bins=25, alpha=0.6, color='#ef4444', label='not placed', density=True)
            axes[0].set(title='Risk scores separate the groups (with overlap)', xlabel='predicted risk of not being placed'); axes[0].legend(frameon=False)
            prec, rec, thr = precision_recall_curve(y, risk)
            flagged = np.array([(risk >= t).sum() for t in thr])
            axes[1].plot(thr, rec[:-1], label='share of at-risk students caught (recall)', color='#ef4444', linewidth=2)
            axes[1].plot(thr, prec[:-1], label='share of flagged who are at risk (precision)', color='#0f766e', linewidth=2)
            k = np.argmin(np.abs(flagged - 120))
            axes[1].axvline(thr[k], color='gray', linestyle=':')
            axes[1].text(thr[k] - 0.01, 0.3, f'call list of {flagged[k]}\\nrecall {rec[k]:.0%}, precision {prec[k]:.0%}', fontsize=9, ha='right')
            axes[1].set(title='Where to draw the line', xlabel='threshold'); axes[1].legend(frameon=False, loc='lower left', fontsize=8)
            plt.show()

            i = int(np.argsort(risk)[-40])                             # one high-risk student
            contrib = m.coef_[0] * (X.iloc[i] - X.mean())
            contrib = contrib.sort_values()
            fig, ax = plt.subplots(figsize=(7, 2.6))
            ax.barh([f'{f} = {X.iloc[i][f]:.0f}' for f in contrib.index], contrib, color=['#ef4444' if v > 0 else '#0f766e' for v in contrib])
            ax.axvline(0, color='black', linewidth=0.8)
            ax.set(title=f'Why student #{i} has risk {risk[i]:.0%} (red = pushes risk up)', xlabel='contribution to log-odds vs batch average')
            plt.show()
            print(X.iloc[i].round(1).to_dict(), '| batch mean:', X.mean().round(1).to_dict())
        """, setup=STUDENTS, title='Python (scikit-learn · Matplotlib) · uses sample data'),
        title='Example: Score Distributions, Threshold Trade-off for a 120-Student Call List, One Student\'s Explanation'),
    steps(
        ('Show separation', 'Overlaid score distributions by true outcome.'),
        ('Translate the threshold into people', 'Recall and precision vs threshold; mark the capacity.'),
        ('Explain individuals', 'Contribution bars sorted, coloured by direction.'),
        ('Use plain labels', 'Feature names with the student\'s actual values.'),
        ('Keep colours consistent', 'Risk-raising red, protective green, everywhere.'),
        title='Steps to Explain a Model Visually'),
    crossq(
        ('Why show distributions instead of just accuracy?', 'They show how much the scores overlap, which tells users how many students near the threshold could go either way.'),
        ('How do you choose the threshold with users?', 'Mark the operational constraint (a 120-student call list) on the trade-off chart and read off recall and precision there.'),
        ('Are coefficient × deviation contributions valid for any model?', 'Only for linear (log-odds) models; for trees and ensembles use SHAP values, which generalise the same idea.'),
    ),
]),
])
