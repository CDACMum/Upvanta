Upvanta module page generator
-----------------------------
Each module's questions live in <module>/sNN_*.py (one file per sidebar section).
Build a page:   python build.py rdbms     -> writes out/rdbms.html
Copy the generated file next to index.html.

build.py  - page template, shared JS (navigation, search, progress) and content helpers
base.css  - styles shared with apache-pyspark.html

Modules: rdbms, python, etl, mysql, airflow, hadoop, hive, mongodb, dbt, pandasq, numpyq, linuxq, mlq, statq, vizq, gitq, cassandra, snowflakedb, dbxq

SQL examples (rdbms, etl, mysql) run on a MySQL server reachable as `mysql -uroot`.

Airflow examples
- Every DAG in the airflow module was really run with `airflow dags test` on Airflow 3.3.2.
- The runs are cached in _afcache/ (one JSON file per example). While the example code is
  unchanged, `python build.py airflow` uses the cache and needs no Airflow install.
- If you edit an example, the build re-runs it. That needs:
    AF_BIN  = bin folder of a virtualenv with apache-airflow==3.3.2,
              apache-airflow-providers-sqlite and pytest installed
    AF_HOME = an AIRFLOW_HOME where `airflow db migrate` has been run
  (defaults: /home/claude/af/bin and /home/claude/afhome; set the environment variables
  to your own paths).

Hadoop examples
- Python examples run with python3 at build time (the file-formats question needs `pip install pyarrow`).
- Streaming word-count / combiner / counter examples are really run as local pipes
  (cat input | mapper | sort | reducer) by hadoop/runner.py; HDFS/YARN commands are shown, not run.

Hive examples
- HiveQL examples were executed on Spark SQL with Hive support (PySpark 4.2, Hive 2.3 metastore/SerDes)
  by hive/hive_worker.py; results are cached in _hivecache/ (one JSON per example).
- While an example is unchanged, `python build.py hive` uses the cache and needs no Spark.
- If you edit an example, set HIVE_PY to a Python with pyspark installed and Java available.
- build.py gained two card helpers used by the Hive module: analogy() and steps().

MongoDB examples
- mongodb/mongo_shell.js is a mongosh-like shell: queries, updates and aggregation pipelines are evaluated
  by mingo (a JavaScript implementation of the MongoDB Query Language). Results are cached in _mongocache/.
- While an example is unchanged, `python build.py mongodb` uses the cache and needs no Node.js.
- To re-run edited examples: install Node.js, run `npm install mingo@6 acorn@8` inside _source/mongodb
  (or set MINGO_DIR to a node_modules folder that has them).
- Server-only features (explain, replica sets, sharding, transactions) are shown without output.

dbt examples
- Every dbt command was really run with dbt-core 1.12.5 + dbt-duckdb 1.11.0 (DuckDB warehouse) by dbt/runner.py,
  in a fresh temporary project built from dbt/seeds.py plus the files each example shows.
- Results are cached in _dbtcache/ (one JSON per example). While an example is unchanged,
  `python build.py dbt` uses the cache and needs no dbt install.
- To re-run edited examples: pip install dbt-core dbt-duckdb pandas into a virtualenv and set
  DBT_BIN to its bin folder. Set DBT_KEEP_TMP=1 to keep the temporary project for debugging.
- dbt Cloud, Airflow and warehouse-specific features (clustering, grants) are shown without output.

pandas examples (add this section to README.txt; add "pandasq" to the Modules list)
- Build with:  python build.py pandasq   -> writes out/pandas.html
  (the folder is called pandasq because a folder named "pandas" would hide the real pandas library)
- Every example was really run with pandas 3.0.5, NumPy 2.5, PyArrow 26 and Polars 2.0 (Q33) by pandasq/runner.py.
  Printed output (including warnings such as ChainedAssignmentError) is cached in _pdcache/ (one JSON per example).
- While an example is unchanged, the build uses the cache and needs no pandas install.
- To re-run edited examples, set PD_PY to a Python with pandas 3, pyarrow, openpyxl and polars installed.
- Shared sample data (students, marks) is in pandasq/data.py; timing outputs (Q26) depend on the machine.

NumPy examples (add this section to README.txt; add "numpyq" to the Modules list)
- Build with:  python build.py numpyq   -> writes out/numpy.html
  (folder is called numpyq so it does not hide the real numpy library)
- Every example was really run with NumPy 2.5 (plus pandas 3 in Q31) by numpyq/runner.py.
  Printed output, including warnings, is cached in _npcache/ (one JSON per example).
- While an example is unchanged, the build uses the cache and needs no NumPy install.
- To re-run edited examples, set NP_PY to a Python with NumPy 2 (and pandas for Q31).
- Timing outputs (Q1, Q19, Q20, Q26, Q35) depend on the machine that ran them.
- build.py is included because one shared helper was hardened (text in diagrams is now escaped).

Linux & shell examples (add this section to README.txt; add "linuxq" to the Modules list)
- Build with:  python build.py linuxq   -> writes out/linux.html
- Every Terminal box is a real transcript: commands ran on Ubuntu 24.04 / bash 5.2 as a normal user
  "student" in ~/cdac (a few user/group examples ran as root), via linuxq/runner.py.
  Transcripts are cached in _linuxcache/ (one JSON per example).
- While an example is unchanged, the build uses the cache and needs no Linux at all (works on Windows).
- To re-run edited examples you need Linux, run the build as root, and have a user called "student"
  plus gawk, acl, tree, rsync, cron, openssh-client, iproute2 installed.
- systemd/journalctl and real ssh/scp to a server are shown but not run (no systemd or remote host on the build machine).
- Q34 uses a two-line stub for the `hadoop` command to demonstrate PATH/symlinks without downloading Hadoop (stated on the page).


scikit-learn examples (add this section to README.txt; add "mlq" to the Modules list)
- Build with:  python build.py mlq   -> writes out/sklearn.html
- Every Output box is real: each example ran in a fresh Python 3.13 process with scikit-learn 1.9.1, NumPy 2.5.3,
  pandas 3.0.5 and SciPy 1.18.1, via mlq/runner.py. Outputs are cached in _mlcache/ (one JSON per example).
- While an example is unchanged, the build uses the cache and needs no scikit-learn at all.
- To re-run edited examples set ML_PY to a Python that has scikit-learn, pandas, NumPy and SciPy installed.
- Sample data: mlq/data.py builds a reproducible 600-student dataset (seed 2026) with features attendance, study_hours,
  mock_test, course, centre, degree and targets final_score / placed. Q6 (feature scaling with KNN) and Q33 (PCA) use the built-in
  wine dataset; Q32 uses make_moons; Q35 uses 120 synthetic feedback comments; Q37 adds a synthetic dropout target.
- Animation numbers that say "real run" match the cached outputs; the others are illustrative.


Statistics examples (add this section to README.txt; add "statq" to the Modules list)
- Build with:  python build.py statq   -> writes out/statistics.html
- Every Output box is real: each example ran in a fresh Python 3.13 process with NumPy 2.5.3, pandas 3.0.5,
  SciPy 1.18.1 and statsmodels 0.15.0, via statq/runner.py. Outputs are cached in _statcache/ (one JSON per example).
- While an example is unchanged, the build uses the cache and needs no SciPy/statsmodels at all.
- To re-run edited examples set STAT_PY to a Python that has NumPy, pandas, SciPy and statsmodels installed.
- Sample data: statq/data.py builds a reproducible 600-student dataset (seed 2026): centre, course, teaching method
  (traditional/flipped), attendance, study hours, pre/post-test, final score, placed and package (LPA).
  Some examples simulate their own data (A/B test, evaluators, control chart, Simpson's paradox table); this is stated on the page.
- Animation numbers marked "real run" match the cached outputs; scatter clouds and illustrative curves are drawn for explanation.


Data visualization examples (add this section to README.txt; add "vizq" to the Modules list)
- Build with:  python build.py vizq   -> writes out/matplotlib.html
- Every Output box is real: each example ran in a fresh Python 3.13 process with Matplotlib 3.11.2, Seaborn 0.13.2,
  pandas 3.0.5, NumPy 2.5.3 (plus SciPy / scikit-learn where used), via vizq/runner.py. The runner saves every open
  figure after the script ends (and any .gif the example writes) and embeds the real images in the page.
  Text output and images are cached in _vizcache/ (one JSON per example), so the build needs no Matplotlib at all.
- To re-run edited examples set VIZ_PY to a Python that has Matplotlib, Seaborn, pandas, NumPy, SciPy and scikit-learn.
- Sample data: vizq/data.py (600-student dataset, seed 2026, and a daily attendance table for one term, seed 7).
- Images are stored as optimised PNGs (256-colour where that is lossless to the eye, full colour for gradients), so the page is about 3 MB.

Git & GitHub examples (add this section to README.txt; add "gitq" to the Modules list)
- Build with:  python build.py gitq   -> writes out/git.html
- Every Terminal box is real: each example ran with git 2.43 and bash on Ubuntu 24.04 as the user 'student', in a fresh
  /home/student (work folder ~/cdac) with a fixed ~/.gitconfig (Asha Patil, default branch main), via gitq/runner.py.
- Simulated clock: every git command runs one minute after the previous one, starting 14 Oct 2026 09:00 IST, so commit
  hashes are reproducible and the hashes drawn in the animations match the transcripts.
- Output is cached in _gitcache/ (one JSON per example), so the build needs no Git at all.
- To re-run an edited example, build as root on Linux with git installed and a user called 'student'; the CI example
  (Q32) also needs pytest, and the notebook example (Q35) needs python3. The SSH-key example prints part of a random key,
  so only that line changes when it is re-run.
- Lines starting with '!' in an example are hidden setup commands (run, not shown).

Cassandra examples
- Every CQL example with an Output box is executed at build time by cassandra/cqlsim.py, a deterministic CQL engine
  written for this site that follows Apache Cassandra 5.0's rules: Murmur3Partitioner tokens (bit-identical to
  Cassandra), token order across partitions, clustering order, WHERE-clause restrictions and their exact error
  messages (ALLOW FILTERING, clustering prefix, ORDER BY, GROUP BY), secondary indexes and SAI, upserts with
  last-write-wins timestamps, TTL on a simulated clock (`!sleep N` in an example), tombstones, static columns,
  collections, frozen UDTs, counters, lightweight transactions, batches, materialized views and JSON.
- Output is printed in cqlsh format. Pure Python: `python build.py cassandra` needs no Cassandra and no extra packages.
- Multi-node behaviour (replication, consistency levels, repair) and nodetool commands are shown without output.

Snowflake examples
- Build with:  python build.py snowflakedb   -> writes out/snowflake.html
  (folder is called snowflakedb so it does not hide the snowflake connector package)
- SQL examples ran on fakesnow (a Snowflake emulator on DuckDB) through the real snowflake-connector-python API,
  in a fresh database CDAC.BDA per example, via snowflakedb/runner.py. Output is shown in SnowSQL table format.
- Results are cached in _snowflakecache/ (one JSON per example), so the build needs no Snowflake or fakesnow.
  Set SNOWFLAKE_REFRESH=1 (with fakesnow installed) to re-execute everything.
- Cloud-only features (warehouses, Time Travel, streams, tasks, Snowpipe, shares, RBAC, masking) are shown without output.

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

Light theme (all pages)
- theme_light.css is the Upvanta light theme (teal/indigo, Unbounded + Manrope), matching index.html.
- build.py adds it to every page it builds (inject_theme in apply_theme.py), so new builds are themed automatically.
- To re-apply to the pages next to index.html after editing the CSS:  python apply_theme.py ../*.html
- redis.html has its own layout and uses theme_redis.css instead.
- index.html is generated by:  python build_index.py index_template.html ../index.html
