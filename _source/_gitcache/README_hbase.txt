
HBase examples
- Every HBase shell example with an Output box is executed at build time by hbase/hbasesim.py, a deterministic HBase
  shell written for this site that follows Apache HBase 2.x behaviour: row keys sorted as bytes, column families,
  multi-version cells and timestamps, delete markers (RAW scans), TTL and MIN_VERSIONS on a simulated clock
  (`!sleep N` in an example), KEEP_DELETED_CELLS, counters (8-byte longs), the Filter Language and comparators,
  namespaces and table DDL (create/alter/describe/disable/drop).
- Output follows the hbase shell format; "Took N seconds" timing lines are left out and timestamps are shown in IST.
- Pure Python: `python build.py hbase` needs no HBase and no extra packages.
- Cluster-level commands (regions, compaction, replication, status) are shown without output.
