NumPy examples (add this section to README.txt; add "numpyq" to the Modules list)
- Build with:  python build.py numpyq   -> writes out/numpy.html
  (folder is called numpyq so it does not hide the real numpy library)
- Every example was really run with NumPy 2.5 (plus pandas 3 in Q31) by numpyq/runner.py.
  Printed output, including warnings, is cached in _npcache/ (one JSON per example).
- While an example is unchanged, the build uses the cache and needs no NumPy install.
- To re-run edited examples, set NP_PY to a Python with NumPy 2 (and pandas for Q31).
- Timing outputs (Q1, Q19, Q20, Q26, Q35) depend on the machine that ran them.
- build.py is included because one shared helper was hardened (text in diagrams is now escaped).
