
dbt examples
- Every dbt command was really run with dbt-core 1.12.5 + dbt-duckdb 1.11.0 (DuckDB warehouse) by dbt/runner.py,
  in a fresh temporary project built from dbt/seeds.py plus the files each example shows.
- Results are cached in _dbtcache/ (one JSON per example). While an example is unchanged,
  `python build.py dbt` uses the cache and needs no dbt install.
- To re-run edited examples: pip install dbt-core dbt-duckdb pandas into a virtualenv and set
  DBT_BIN to its bin folder. Set DBT_KEEP_TMP=1 to keep the temporary project for debugging.
- dbt Cloud, Airflow and warehouse-specific features (clustering, grants) are shown without output.
