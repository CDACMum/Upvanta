"""Synthetic but realistic C-DAC student dataset used across the visualization examples."""
from build import code, note
import textwrap

STUDENTS = '''
rng = np.random.default_rng(2026)
n = 600
centre = rng.choice(['Kharghar', 'Juhu', 'Pune'], n, p=[0.4, 0.3, 0.3])
course = rng.choice(['PG-DBDA', 'PG-DAC', 'PG-DAI'], n, p=[0.45, 0.35, 0.20])
method = rng.choice(['traditional', 'flipped'], n)                  # teaching method (A/B)
attendance = rng.uniform(55, 100, n).round(1)
study_hours = rng.gamma(4, 2.2, n).round(1)                         # per week, right-skewed
pre_test = np.clip(rng.normal(52, 11, n), 0, 100).round()           # before the module
post_test = np.clip(pre_test + rng.normal(6, 7, n) + np.where(method == 'flipped', 3, 0), 0, 100).round()
final_score = np.clip(0.30 * attendance + 1.6 * study_hours + 0.35 * post_test
                      + np.where(centre == 'Pune', 2, 0) + rng.normal(0, 5, n), 0, 100).round(1)
z = -12 + 0.07 * attendance + 0.15 * study_hours + 0.08 * post_test
placed = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)
salary_lpa = np.where(placed == 1, np.round(rng.lognormal(np.log(6), 0.35, n), 1), np.nan)   # package, lakh per annum
df = pd.DataFrame({'centre': centre, 'course': course, 'method': method, 'attendance': attendance,
                   'study_hours': study_hours, 'pre_test': pre_test, 'post_test': post_test,
                   'final_score': final_score, 'placed': placed, 'salary_lpa': salary_lpa})
'''


def data_note():
    return note('Examples marked <em>uses sample data</em> start with this block, which builds a reproducible synthetic dataset of 600 C-DAC students: '
                'centre, course, teaching method (traditional / flipped classroom), attendance %, weekly study hours, pre- and post-module test scores, '
                'final exam score, placement (1/0) and package in lakh per annum (placed students only). Copy it first to run an example yourself: ' +
                code(textwrap.dedent(STUDENTS).strip('\n'), 'Sample data (students)', 'fa-brands fa-python'), 'Sample data')


TERM = '''
rng = np.random.default_rng(7)
days = pd.bdate_range('2026-02-02', '2026-07-31')                          # weekdays of one term
centres = ['Kharghar', 'Juhu', 'Pune']
base = {'Kharghar': 0.86, 'Juhu': 0.82, 'Pune': 0.84}
rows = []
for c in centres:
    trend = np.linspace(0, -0.06, len(days))                               # slow decline over the term
    monday = np.where(days.dayofweek == 0, -0.03, 0)                       # Mondays are weaker
    dip = np.where((days >= '2026-04-13') & (days <= '2026-04-17'), -0.15, 0)   # exam-prep week
    rate = np.clip(base[c] + trend + monday + dip + rng.normal(0, 0.02, len(days)), 0, 1)
    rows.append(pd.DataFrame({'date': days, 'centre': c, 'attendance': rate.round(3)}))
term = pd.concat(rows, ignore_index=True)
'''


def term_note():
    return note('Time-series examples use this block: daily attendance rate for three centres over one term (weekdays, Feb–Jul 2026) with a slow '
                'decline, weaker Mondays and an exam-preparation dip in mid-April: ' +
                code(textwrap.dedent(TERM).strip('\n'), 'Sample data (term attendance)', 'fa-brands fa-python'), 'Sample data')
