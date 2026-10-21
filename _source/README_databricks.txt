Databricks examples (add this section to README.txt; add "dbxq" to the Modules list)
- Build with:  python build.py dbxq   -> writes out/databricks.html
  (folder is called dbxq so it does not hide the "databricks" Python packages)
- Databricks is a cloud service, so the examples run locally in dbxq/dbx_worker.py:
    * Apache Spark 4.2 (PySpark, local mode) for every query, DataFrame, EXPLAIN plan and Structured Streaming example;
    * delta-rs (the "deltalake" package, the Rust implementation of the Delta Lake protocol) for every Delta table
      operation: writes, UPDATE, DELETE, MERGE, OPTIMIZE / ZORDER, VACUUM, RESTORE, time travel, Change Data Feed,
      CHECK / NOT NULL constraints. Each table is a real folder of Parquet files with a real _delta_log;
      Spark reads exactly the Parquet files of the requested version, so plans show real scans and filters;
    * MLflow 3 with a local tracking store.
  Error messages for Delta rules (constraint violations, MERGE duplicates, VACUUM retention check, schema mismatch)
  are printed in Databricks/Delta wording. Table locations are shown as s3://cdac-lakehouse/... and volume paths as /Volumes/...
- Results are cached in _dbxcache/ (one JSON per example), so the build needs no Spark, Java or delta-rs at all.
- To re-run edited examples set DBX_PY to a Python with pyspark 4.2, deltalake, mlflow, pandas<3 and scikit-learn
  (Java 17+ needed). DBX_REFRESH=1 re-executes everything.
- Features that need a workspace (clusters, jobs, Unity Catalog grants, Auto Loader, Lakeflow pipelines, Photon,
  serverless, model serving, SQL warehouses) are shown without output.
- Python UDF examples use spark.sql.execution.pythonUDF.arrow.enabled=false (classic BatchEvalPython path).
