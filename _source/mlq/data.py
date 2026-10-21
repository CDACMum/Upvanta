"""Synthetic but realistic C-DAC student dataset used across the scikit-learn examples."""
from build import code, note
import textwrap

STUDENTS = '''
rng = np.random.default_rng(2026)
n = 600
course = rng.choice(['PG-DBDA', 'PG-DAC', 'PG-DAI'], n, p=[0.45, 0.35, 0.20])
centre = rng.choice(['Kharghar', 'Juhu', 'Pune'], n)
degree = rng.choice(['BE', 'BSc', 'MCA', 'BCA'], n, p=[0.5, 0.2, 0.15, 0.15])
attendance = rng.uniform(55, 100, n).round(1)
study_hours = rng.gamma(4, 2.2, n).round(1)                  # per week
mock_test = np.clip(rng.normal(55 + 0.25 * attendance + 1.2 * study_hours - 20, 12), 0, 100).round()
final_score = np.clip(0.30 * attendance + 1.6 * study_hours + 0.35 * mock_test
                      + np.where(course == 'PG-DAI', 3, 0) + rng.normal(0, 5, n), 0, 100).round(1)
z = -13 + 0.07 * attendance + 0.18 * study_hours + 0.08 * mock_test + np.where(course == 'PG-DBDA', 0.6, 0)
placed = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)
df = pd.DataFrame({'course': course, 'centre': centre, 'degree': degree, 'attendance': attendance,
                   'study_hours': study_hours, 'mock_test': mock_test, 'final_score': final_score, 'placed': placed})
df.loc[rng.choice(n, 25, replace=False), 'mock_test'] = np.nan     # some missing values
df.loc[rng.choice(n, 15, replace=False), 'degree'] = np.nan
'''


def data_note():
    return note('Examples marked <em>uses sample data</em> start with this block, which builds a reproducible synthetic dataset of 600 C-DAC students '
                '(attendance, weekly study hours, mock-test score, course, centre, degree, final exam score, and whether the student was placed). '
                'Copy it first if you want to run an example yourself: ' +
                code(textwrap.dedent(STUDENTS).strip('\n'), 'Sample data (students)', 'fa-brands fa-python'), 'Sample data')
