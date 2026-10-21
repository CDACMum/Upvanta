"""Synthetic but realistic C-DAC student dataset used across the statistics examples."""
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
