pandas examples (add this section to README.txt; add "pandasq" to the Modules list)
- Build with:  python build.py pandasq   -> writes out/pandas.html
  (the folder is called pandasq because a folder named "pandas" would hide the real pandas library)
- Every example was really run with pandas 3.0.5, NumPy 2.5, PyArrow 26 and Polars 2.0 (Q33) by pandasq/runner.py.
  Printed output (including warnings such as ChainedAssignmentError) is cached in _pdcache/ (one JSON per example).
- While an example is unchanged, the build uses the cache and needs no pandas install.
- To re-run edited examples, set PD_PY to a Python with pandas 3, pyarrow, openpyxl and polars installed.
- Shared sample data (students, marks) is in pandasq/data.py; timing outputs (Q26) depend on the machine.
