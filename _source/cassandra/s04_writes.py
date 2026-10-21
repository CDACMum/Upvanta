from build import *
from cassandra.anims import *
from cassandra.runner import cql, cq, sh, conf

SECTION = dict(level='intermediate', title='Writes, TTL, Deletes & Counters', questions=[

# ------------------------------------------------------------------ 16
Q('What is an upsert in Cassandra? How does "last write wins" work with write timestamps?', 'Upserts & Last-Write-Wins', minutes=9, cards=[
    definition(
        defbox('In Cassandra, <code>INSERT</code> and <code>UPDATE</code> are both <strong>upserts</strong>: they write the given cells whether or not the '
               'row exists, without reading first. There is no "duplicate key" error and an UPDATE of a missing row creates it.',
               'Every cell is stored with a <strong>write timestamp</strong> in microseconds (assigned by the coordinator or client, or set with '
               '<code>USING TIMESTAMP</code>). When two versions of a cell meet (on different replicas, or in different SSTables), the one with the '
               '<strong>higher timestamp wins</strong>: <strong>last write wins (LWW)</strong>. <code>WRITETIME(col)</code> shows a cell\'s timestamp.'),
        tags('Upsert', 'Last write wins', 'WRITETIME', 'USING TIMESTAMP', 'Cell-level resolution', 'Idempotent writes'),
    ),
    analogy('Every note pinned to a notice board is <strong>stamped with the exact time</strong> it was written. When two notes say different things, '
            'readers always believe the one with the later stamp, no matter which one was pinned last.'),
    lww_anim(),
    real_world(
        scenario('Retries are safe',
                 p('A mobile app on a weak network re-sends "set profile city = Pune" three times. Because the write is an idempotent upsert, the '
                   'result is the same. A delayed old retry carrying an older client timestamp cannot overwrite a newer change.')),
    ),
    example(
        cql('''
CREATE TABLE profiles (roll_no int PRIMARY KEY, city text, phone text);

INSERT INTO profiles (roll_no, city, phone) VALUES (2401, 'Pune', '9820011111');
-- UPDATE of a row that does not exist simply creates it
UPDATE profiles SET city = 'Thane' WHERE roll_no = 2402;
-- INSERT on an existing key overwrites only the columns given
INSERT INTO profiles (roll_no, city) VALUES (2401, 'Mumbai');
SELECT roll_no, city, phone, WRITETIME(city), WRITETIME(phone) FROM profiles;

-- a write with an OLDER timestamp loses, even though it arrives later
UPDATE profiles USING TIMESTAMP 1791952200000000 SET city = 'Nashik' WHERE roll_no = 2401;
SELECT roll_no, city, WRITETIME(city) FROM profiles WHERE roll_no = 2401;
'''),
        p('Timestamps resolve conflicts <strong>per cell</strong>: the phone keeps its first write time while the city got a newer one. The '
          'Nashik update had a timestamp earlier than the Mumbai write, so it was ignored.', top=True),
        title='Example'),
    steps(
        ('Design writes to be idempotent', 'Same statement applied twice = same result (avoid list appends and counters for critical data).'),
        ('Let one clock source assign timestamps', 'Driver-side timestamps (default in modern drivers) keep a client\'s writes ordered.'),
        ('Keep clocks synchronised', 'Run NTP/chrony on all servers and clients.'),
        ('Use LWT when the outcome depends on the current value', '"Insert only if absent" cannot be done with plain upserts.'),
        title='Steps'),
    crossq(
        ('What if two writes have exactly the same timestamp?', 'Cassandra breaks ties deterministically (deletes win over writes; otherwise the greater '
         'value wins), so all replicas still converge on the same result.'),
        ('Why is clock skew dangerous?', 'If a node\'s clock runs ahead, its writes get "future" timestamps and later correct writes lose to them, '
         'so updates appear to be ignored.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is TTL in Cassandra? How do you make data expire automatically?', 'TTL (Time To Live)', minutes=8, cards=[
    definition(
        defbox('<strong>TTL</strong> is a lifetime in seconds attached to written cells: <code>INSERT … USING TTL 300</code> or '
               '<code>UPDATE … USING TTL 300 SET …</code>. When it runs out the data is no longer returned by reads; later, compaction removes it. '
               '<code>TTL(col)</code> shows the remaining seconds.',
               'A table can define <code>default_time_to_live</code> so every write expires after that period unless the write sets its own TTL. TTL is '
               'tracked <strong>per cell</strong>, and an expired cell becomes a tombstone until compaction purges it.'),
        tags('TTL', 'USING TTL', 'default_time_to_live', 'Expiry', 'Tombstone'),
    ),
    analogy('A <strong>self-destructing OTP SMS</strong>: valid for 5 minutes. Nobody has to delete it; after 5 minutes it simply stops working.'),
    ttl_anim(),
    real_world(
        scenario('Typical TTL uses',
                 ul('OTP codes and password-reset tokens (minutes).',
                    'Login sessions and rate-limit windows (hours).',
                    'Raw proctoring events and IoT readings kept for 30–90 days, combined with TimeWindowCompactionStrategy.')),
    ),
    example(
        cql('''
CREATE TABLE otp (mobile text PRIMARY KEY, code int, purpose text);

INSERT INTO otp (mobile, code, purpose) VALUES ('9820012345', 482913, 'exam-login') USING TTL 300;
SELECT mobile, code, TTL(code) FROM otp;
!sleep 120
SELECT mobile, code, TTL(code) FROM otp;
!sleep 181
SELECT * FROM otp;

-- table-level default: every row expires 30 days after it is written
CREATE TABLE login_events (roll_no int, ts timestamp, ip text, PRIMARY KEY (roll_no, ts))
  WITH default_time_to_live = 2592000;
INSERT INTO login_events (roll_no, ts, ip) VALUES (2401, '2026-10-14 10:00:00+0530', '10.0.4.17');
SELECT ip, TTL(ip) FROM login_events WHERE roll_no = 2401;
'''),
        title='Example'),
    steps(
        ('Decide the retention period', 'From business or legal rules.'),
        ('Prefer a table default', '<code>WITH default_time_to_live = …</code> so no write is forgotten.'),
        ('Use TWCS for time-series with TTL', 'Expired SSTables are dropped whole, avoiding tombstone scans.'),
        ('Remember TTL is per cell', 'Updating a column resets only that column\'s TTL; re-insert the whole row to refresh all.'),
        title='Steps'),
    crossq(
        ('Can you remove a TTL from existing data?', 'Re-write the value with <code>USING TTL 0</code> (no expiry) or without a TTL when the table has '
         'no default.'),
        ('Does expired data free disk space immediately?', 'No. It becomes a tombstone and disappears at compaction after gc_grace_seconds. With TWCS '
         'and uniform TTLs, whole SSTables are dropped once fully expired.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('How do deletes work in Cassandra? What are tombstones and gc_grace_seconds?', 'Deletes & Tombstones', minutes=10, cards=[
    definition(
        defbox('Because SSTables are immutable, a <code>DELETE</code> does not remove data. It <strong>writes a tombstone</strong>, a marker with a '
               'timestamp that hides older data during reads. Tombstones can cover a cell, a row, a <strong>range of rows</strong> (clustering range) '
               'or a whole <strong>partition</strong>; TTL expiry also produces them.',
               'Tombstones are kept for <code>gc_grace_seconds</code> (default 864000 = 10 days) so that every replica receives them, including replicas '
               'that were down. After that, compaction may purge them together with the data they shadow. If a replica missed the delete and is not '
               'repaired within gc_grace, the old data can come back ("<strong>zombie</strong>" or resurrected data).'),
        tags('Tombstone', 'gc_grace_seconds', 'Range tombstone', 'Partition tombstone', 'Zombie data', 'TombstoneOverwhelmingException'),
    ),
    analogy('Crossing out a line in a <strong>register written in ink</strong>: you cannot erase it, so you add "cancelled on 14 Oct". The '
            'register only gets rewritten cleanly at the yearly clean-up (compaction), and until then every reader has to read past the crossed-out lines.'),
    tombstone_anim(),
    real_world(
        scenario('The queue anti-pattern',
                 p('A team used a Cassandra table as a job queue: insert a job, process it, delete it. After a few weeks every "fetch next job" query had to '
                   'skip hundreds of thousands of tombstones, logged tombstone warnings and finally failed. The fix was a time-bucketed design that never '
                   'reads deleted ranges (or Kafka for queueing).')),
    ),
    example(
        cql('''
CREATE TABLE attempts (exam text, roll_no int, status text, PRIMARY KEY (exam, roll_no));
INSERT INTO attempts (exam, roll_no, status) VALUES ('SQL-2026-10', 2401, 'submitted');
INSERT INTO attempts (exam, roll_no, status) VALUES ('SQL-2026-10', 2402, 'submitted');
INSERT INTO attempts (exam, roll_no, status) VALUES ('SQL-2026-10', 2403, 'absent');
INSERT INTO attempts (exam, roll_no, status) VALUES ('SQL-2026-10', 2404, 'absent');

DELETE status FROM attempts WHERE exam = 'SQL-2026-10' AND roll_no = 2401;      -- cell tombstone
DELETE FROM attempts WHERE exam = 'SQL-2026-10' AND roll_no >= 2403;            -- range tombstone
SELECT * FROM attempts WHERE exam = 'SQL-2026-10';

-- a write with an older timestamp than the delete stays hidden
INSERT INTO attempts (exam, roll_no, status) VALUES ('SQL-2026-10', 2404, 'late') USING TIMESTAMP 1791952200000000;
SELECT * FROM attempts WHERE exam = 'SQL-2026-10';

DELETE FROM attempts WHERE exam = 'SQL-2026-10';                                -- partition tombstone
SELECT * FROM attempts WHERE exam = 'SQL-2026-10';
'''),
        p('Deleting only the <code>status</code> column of 2401 leaves the row itself alive (it was created by an INSERT), so it still appears with '
          '<code>null</code>.', top=True),
        conf('''
# cassandra.yaml thresholds (per query)
tombstone_warn_threshold: 1000         # log a warning
tombstone_failure_threshold: 100000    # abort the read

-- per table
ALTER TABLE cdac.attempts WITH gc_grace_seconds = 864000;
''', 'Related settings'),
        title='Example'),
    steps(
        ('Prefer TTL or partition-level deletes', 'One partition tombstone is far cheaper than many row tombstones.'),
        ('Avoid delete-and-read-again patterns', 'Queues, "latest status" rows that are deleted and recreated.'),
        ('Never write nulls you do not mean', 'Inserting <code>null</code> explicitly creates a tombstone; omit the column instead.'),
        ('Repair within gc_grace_seconds', 'Otherwise deleted data can be resurrected.'),
        ('Monitor', 'Tombstone warnings in system.log, <code>nodetool tablestats</code> (tombstones per slice).'),
        title='Steps to Keep Tombstones Under Control'),
    crossq(
        ('Why does inserting null create a tombstone?', 'A null means "this cell has no value as of now", which must override older values on other '
         'replicas, so it is stored as a tombstone. Drivers can leave unset values (unset) to avoid this.'),
        ('Can you lower gc_grace_seconds to 0?', 'Only for tables never deleted from, or with RF 1 / no repair needs. Otherwise a down replica that missed '
         'the delete brings data back. Common values: 1–10 days, matched to the repair schedule.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What are counter columns? What are their limitations?', 'Counters', minutes=7, cards=[
    definition(
        defbox('A <code>counter</code> is a 64-bit integer column that supports only <strong>increment and decrement</strong>: '
               '<code>UPDATE t SET views = views + 1 WHERE …</code>. Each replica keeps its own contribution (shard), and reads merge them, so '
               'concurrent increments from many clients are not lost to last-write-wins.'),
        ul('A counter table contains <strong>only</strong> primary-key columns and counter columns.',
           'No <code>INSERT</code>, no setting to a value, no TTL; a counter starts at 0 when first incremented.',
           'Increments are <strong>not idempotent</strong>: a retried increment after a timeout can be counted twice.',
           'Deleting and re-creating a counter is unreliable; treat deletions as permanent.'),
        tags('counter', 'Increment', 'Not idempotent', 'Counter table'),
    ),
    analogy('A <strong>tally sheet at each gate</strong> of the exam centre. Each gatekeeper adds strokes on their own sheet, and the total is the '
            'sum of all sheets. Nobody overwrites anybody else\'s count.'),
    counter_anim(),
    real_world(
        scenario('Approximate metrics',
                 p('Counters track how many times each study module page was viewed and how many questions each student attempted. Small inaccuracies '
                   'from retries are acceptable. Fee balances, by contrast, are stored as normal values written with LWT, never as counters.')),
    ),
    example(
        cql('''
CREATE TABLE module_views (module text, day date, views counter, PRIMARY KEY (module, day));

UPDATE module_views SET views = views + 1 WHERE module = 'cassandra' AND day = '2026-10-14';
UPDATE module_views SET views = views + 1 WHERE module = 'cassandra' AND day = '2026-10-14';
UPDATE module_views SET views = views + 5 WHERE module = 'cassandra' AND day = '2026-10-14';
UPDATE module_views SET views = views - 1 WHERE module = 'cassandra' AND day = '2026-10-14';
SELECT * FROM module_views WHERE module = 'cassandra';

INSERT INTO module_views (module, day, views) VALUES ('hive', '2026-10-14', 10);
UPDATE module_views SET views = 10 WHERE module = 'hive' AND day = '2026-10-14';
''', expect_error=True),
        title='Example'),
    steps(
        ('Create a dedicated counter table', 'Primary key + counter columns only.'),
        ('Increment with UPDATE', '<code>SET c = c + n</code>; the row appears on the first increment.'),
        ('Accept approximate results', 'Do not use counters for money or exact inventory.'),
        ('Read normally', '<code>SELECT</code> returns the merged total.'),
        title='Steps'),
    crossq(
        ('Why can\'t a counter table have normal columns?', 'Counter updates use a different write path (read the local shard, then replicate) and cannot '
         'be mixed with regular last-write-wins cells in one table.'),
        ('How else can you count exactly?', 'Write individual events (idempotent, with unique IDs) and count them in a batch job (Spark), or use LWT '
         'compare-and-set on a regular bigint column.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What are batches in Cassandra? Logged vs unlogged, and when should you use them?', 'Batches', minutes=9, cards=[
    definition(
        defbox('A <code>BEGIN BATCH … APPLY BATCH</code> groups INSERT/UPDATE/DELETE statements, all with the same timestamp.',
               '<strong>Logged batch</strong> (default): the coordinator first writes the batch to the <strong>batchlog</strong> on other nodes. If the '
               'coordinator fails midway, the batch is replayed, so <strong>all statements are eventually applied</strong> (atomicity). It is '
               '<strong>not isolated</strong>: readers may see some statements applied before others. Use it to keep <strong>denormalised tables in sync</strong>.',
               '<strong>Unlogged batch</strong>: no batchlog. Efficient only when all statements target the <strong>same partition</strong> (sent as one '
               'mutation). <strong>Counter batch</strong>: for counter updates only.'),
        tags('Logged batch', 'Unlogged batch', 'Batchlog', 'Atomic', 'Not isolated', 'Anti-pattern: bulk load'),
    ),
    analogy('A <strong>registered parcel</strong> containing letters for two offices. The post office logs it, so if the van breaks down the parcel is '
            're-sent and both letters are delivered eventually. It is a delivery guarantee, not a speed-up, and you would never send a whole '
            'warehouse as one registered parcel.'),
    batch_anim(),
    real_world(
        scenario('Registration writes two tables',
                 p('Registering a student writes <code>students_by_roll</code> and <code>students_by_email</code> in one logged batch, so the login table '
                   'and the profile table never permanently disagree. Loading 2 lakh historical records, on the other hand, uses many asynchronous single '
                   'inserts (or DSBulk), not batches.')),
    ),
    example(
        cql('''
CREATE TABLE students_by_roll  (roll_no int PRIMARY KEY, email text, name text);
CREATE TABLE students_by_email (email text PRIMARY KEY, roll_no int, name text);

BEGIN BATCH
  INSERT INTO students_by_roll  (roll_no, email, name) VALUES (2405, 'riya@cdac.in', 'Riya');
  INSERT INTO students_by_email (email, roll_no, name) VALUES ('riya@cdac.in', 2405, 'Riya');
APPLY BATCH;

SELECT * FROM students_by_roll WHERE roll_no = 2405;
SELECT * FROM students_by_email WHERE email = 'riya@cdac.in';

-- statements in a batch share one write timestamp
SELECT WRITETIME(name) FROM students_by_roll WHERE roll_no = 2405;
SELECT WRITETIME(name) FROM students_by_email WHERE email = 'riya@cdac.in';
'''),
        conf('''
batch_size_warn_threshold: 5KiB     # warn when a batch is larger
batch_size_fail_threshold: 50KiB    # reject larger batches
unlogged_batch_across_partitions_warn_threshold: 10
''', 'cassandra.yaml guardrails'),
        title='Example'),
    steps(
        ('Use logged batches for multi-table consistency', 'Same fact written to several query tables.'),
        ('Use unlogged batches only within one partition', 'e.g. several rows of one sensor-day.'),
        ('Keep batches small', 'A few statements, well under the 5 KiB warning.'),
        ('Bulk load with async single writes', 'Limit in-flight requests; or use DSBulk / Spark.'),
        title='Steps'),
    crossq(
        ('Does a logged batch give ACID transactions?', 'Atomicity (eventually all or nothing) only. There is no isolation and no rollback; partially '
         'applied state can be read while the batch is in progress or being replayed.'),
        ('Can a batch contain lightweight transactions?', 'Yes, but then every statement must target the same partition, and the whole batch is applied '
         'only if the conditions hold.'),
    ),
]),
])
