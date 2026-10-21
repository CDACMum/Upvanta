"""Shared sample data (C-DAC style) used by the pandas examples."""
from build import code, note
import textwrap

STUDENTS = """
students = pd.DataFrame({
    'roll_no': [2401, 2402, 2403, 2404, 2405, 2406],
    'name':    ['Anuj', 'Vineeta', 'Aarshvi', 'Rohan', 'Meera', 'Kabir'],
    'course':  ['PG-DBDA', 'PG-DBDA', 'PG-DAI', 'PG-DAC', 'PG-DBDA', 'PG-DAI'],
    'centre':  ['Kharghar', 'Kharghar', 'Juhu', 'Juhu', 'Kharghar', 'Juhu'],
    'city':    ['Pune', 'Navi Mumbai', 'Mumbai', 'Thane', 'Pune', 'Mumbai'],
})
"""

MARKS = """
marks = pd.DataFrame({
    'roll_no': [2401, 2401, 2402, 2402, 2403, 2404, 2405, 2406, 2406],
    'subject': ['SQL', 'Spark', 'SQL', 'Spark', 'ML', 'Java', 'SQL', 'ML', 'Python'],
    'marks':   [82, 61, 91, 88, 84, 58, 75, None, 72],
})
"""

BOTH = STUDENTS + MARKS


def data_note(*names):
    src = ''.join({'students': STUDENTS, 'marks': MARKS}[n] for n in names)
    return note('Examples marked <em>uses sample data</em> start from these DataFrames (copy this block first): ' +
                code(textwrap.dedent(src).strip('\n'), 'Sample data', 'fa-brands fa-python'),
                'Sample data')
