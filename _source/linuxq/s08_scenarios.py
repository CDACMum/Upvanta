from build import *
from linuxq.anims import *
from linuxq.runner import shrun, sh, script_file
from linuxq.data import COMMON, APP_LOG, ACCESS_LOG

BACKUP = r"""
#!/usr/bin/env bash
# backup.sh <source_dir> <backup_dir> [keep_days]
set -euo pipefail
src="${1:?usage: backup.sh <source> <dest> [keep_days]}"
dest="${2:?usage: backup.sh <source> <dest> [keep_days]}"
keep="${3:-7}"
log() { echo "$(date '+%F %T') [$1] ${*:2}"; }

[[ -d "$src" ]] || { log ERROR "source $src not found"; exit 2; }
mkdir -p "$dest"
free_kb=$(df -Pk "$dest" | awk 'NR == 2 {print $4}')
need_kb=$(du -sk "$src" | cut -f1)
(( free_kb > need_kb * 2 )) || { log ERROR "not enough space"; exit 3; }

archive="$dest/$(basename "$src")_$(date +%F_%H%M%S).tar.gz"
tar -czf "$archive" -C "$(dirname "$src")" "$(basename "$src")"
tar -tzf "$archive" > /dev/null || { log ERROR "archive unreadable"; exit 4; }
log INFO "created $archive ($(du -h "$archive" | cut -f1))"

deleted=$(find "$dest" -name '*.tar.gz' -mtime +"$keep" -print -delete | wc -l)
log INFO "removed $deleted archive(s) older than $keep days"
"""

HEALTH = r"""
#!/usr/bin/env bash
# health.sh - quiet when healthy; prints problems and exits 1 otherwise
set -uo pipefail
DISK_LIMIT=${DISK_LIMIT:-80}
problems=()

usage=$(df -P "$HOME" | awk 'NR == 2 {gsub("%", "", $5); print $5}')
(( usage < DISK_LIMIT )) || problems+=("disk ${usage}% used (limit ${DISK_LIMIT}%)")

services=("http.server 8000")          # e.g. add "kafka.Kafka" on a broker
for svc in "${services[@]}"; do
    pgrep -f "$svc" > /dev/null || problems+=("process missing: $svc")
done

curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/ | grep -q 200 \
    || problems+=("web check failed on :8000")

state="$HOME/.health_lines"
last=$(cat "$state" 2>/dev/null || echo 0)
total=$(wc -l < app.log)
new_errors=$(tail -n +"$((last + 1))" app.log | grep -c ERROR)
echo "$total" > "$state"
(( new_errors == 0 )) || problems+=("$new_errors new ERROR line(s) in app.log")

if (( ${#problems[@]} )); then
    printf 'ALERT %s\n' "${problems[@]}"
    exit 1
fi
"""

SECTION = dict(level='expert', title='Scenario-Based Questions', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: analyse a web server access log. Find top clients, errors and traffic per hour.', 'Log Analysis', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('Access logs (Apache/Nginx "combined" format) are space-separated: client IP (<code>$1</code>), timestamp (<code>$4</code>), request '
               '(<code>$6–$8</code>), status (<code>$9</code>), bytes (<code>$10</code>). Combining <code>awk</code> field extraction with '
               '<code>sort | uniq -c | sort -rn</code>, filters on status codes and associative arrays answers most operational questions without a database, '
               'streaming files of any size.'),
        tags('access log', 'awk', 'uniq -c', 'HTTP status', 'log analysis'),
    ),
    analogy('A log file is a <strong>visitor register at a gate</strong>. Counting who came most often, who was turned away, and how busy each hour was is just '
            'reading the right columns and tallying.'),
    logscen_anim(),
    real_world(
        scenario('LMS slow on exam morning',
                 p('Within minutes: one IP made a quarter of all requests (a misbehaving script), 404s are for notes PDFs that were renamed, a 500 on the course '
                   'page points to a backend bug, and traffic peaks at 10:00. Each finding came from one pipeline over the raw access log.')),
    ),
    example(
        shrun("""
            head -n 2 access.log
            awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -n 3
            awk '{print $9}' access.log | sort | uniq -c | sort -rn
            awk '$9 >= 400 {print $9, $7}' access.log
            awk '{h = substr($4, 14, 2); n[h]++} END {for (k in n) print k ":00", n[k]}' access.log | sort
            awk '{b[$7] += $10} END {for (p in b) printf "%8d %s\\n", b[p], p}' access.log | sort -rn | head -n 3
            awk '$9 >= 500' access.log | wc -l
        """, files={'access.log': ACCESS_LOG}),
        title='Example: Six Questions, Six One-liners'),
    steps(
        ('Identify the fields', 'Print one line with field numbers: <code>awk \'{for (i=1;i&lt;=NF;i++) print i, $i}\'</code>.'),
        ('Count by a field', '<code>awk \'{print $N}\' | sort | uniq -c | sort -rn</code>.'),
        ('Filter', 'Conditions on status, path or time.'),
        ('Aggregate', 'Associative arrays in awk; print in END.'),
        ('Automate', 'Wrap in a script that runs daily and mails the summary.'),
        title='Steps to Analyse Any Log'),
    crossq(
        ('How would you only look at the last hour of a huge log?', 'tail -n with an estimate, or awk on the timestamp field; for rotated logs zcat older files as needed.'),
        ('What do 4xx and 5xx mean?', '4xx client errors (404 not found, 403 forbidden), 5xx server errors (500 internal error, 503 unavailable).'),
        ('When do you stop using awk?', 'When you need joins across many sources, history over months or dashboards: load logs into Elasticsearch, Hive/Spark or a log platform.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: write a backup script with verification, rotation and logging.', 'Backup Script', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('A dependable backup script: validates arguments and the source, checks free space, creates a <strong>dated compressed archive</strong>, '
               '<strong>verifies</strong> it can be read, <strong>deletes archives older than the retention period</strong>, <strong>logs</strong> each step with '
               'timestamps and returns meaningful <strong>exit codes</strong>; it runs from cron with output appended to a log.'),
        tags('backup', 'tar', 'retention', 'find -mtime', 'cron', 'exit codes'),
    ),
    analogy('Like a careful librarian archiving registers every night: check the shelf space first, box and label the registers with the date, open the '
            'box once to be sure it is not empty, throw out boxes older than a week, and note everything in the logbook.'),
    backup_anim(),
    real_world(
        scenario('Protecting coursework and results',
                 p('Every night at 01:00 the results folder and project submissions are archived to a backup disk, with 14 days retained; a weekly job copies the '
                   'latest archive to another server with rsync. A monthly restore test proves the archives are usable.')),
    ),
    example(
        script_file('backup.sh', BACKUP),
        shrun("""
            !mkdir -p results backups; cp *.csv results/
            !for d in 01 03 05 09; do touch -d "2026-10-$d 01:00" "backups/results_2026-10-${d}_010000.tar.gz"; done
            ls backups
            bash backup.sh results backups 7; echo "exit $?"
            ls backups
            bash backup.sh nofolder backups; echo "exit $?"
            bash backup.sh; echo "exit $?"
            latest=$(ls -t backups/*.tar.gz | head -n 1); mkdir restore && tar -xzf "$latest" -C restore && ls restore/results
        """, files={**COMMON, 'backup.sh': BACKUP}),
        sh("""
            # crontab -e
            0 1 * * * /opt/backup/backup.sh /data/results /backup/results 14 >> /var/log/backup.log 2>&1
        """, title='crontab entry'),
        title='Example: Run, Rotate, Fail Cleanly, Restore'),
    steps(
        ('Validate inputs', '<code>${1:?usage}</code> stops with a message if an argument is missing.'),
        ('Pre-checks', 'Source exists, enough free space.'),
        ('Archive and verify', 'Dated name; tar -tzf after creating.'),
        ('Rotate', '<code>find … -mtime +N -delete</code>.'),
        ('Schedule and test restores', 'cron + log; regular restore drills.'),
        title='Steps to a Trustworthy Backup'),
    crossq(
        ('Why were the 01, 03 and 05 archives deleted but not 09?', 'They were older than 7 days relative to the run date (13 October); the 9 October archive is within the retention window.'),
        ('What if two backups run at the same time?', 'Use flock in the crontab (flock -n /tmp/backup.lock backup.sh …) so a second run exits immediately.'),
        ('Is a local archive a real backup?', 'Only partly; copy it off the machine (another server, cloud storage) following the 3-2-1 rule: 3 copies, 2 media, 1 off-site.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: a server reports "No space left on device". How do you troubleshoot?', 'Disk Full Troubleshooting', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('Systematic approach: <code>df -h</code> (which filesystem), <code>df -i</code> (inodes), <code>du -xh --max-depth=1 / | sort -rh</code> drilling down '
               '(<code>-x</code> stays on one filesystem), <code>find -size +100M</code> (large files), <code>lsof +L1</code> (deleted files still open). Relief: '
               'compress or delete old logs, truncate open logs, clean package caches and temp files, move data. Prevention: log rotation, retention jobs, '
               'separate disks for data/logs, alerts before 100 %.'),
        tags('disk full', 'df', 'du', 'lsof', 'inodes', 'troubleshooting'),
    ),
    analogy('A full warehouse: first see which building is full (df), then which room (du), then which boxes (find), and check for boxes marked "discarded" '
            'that someone is still holding on to (lsof) before ordering a bigger warehouse.'),
    diskfull_anim(),
    real_world(
        scenario('HDFS DataNode stopped writing',
                 p('A DataNode\'s root disk filled because application logs were written to /var/log without rotation. du found 38 GB of logs; old ones were gzipped '
                   'and removed, the active one truncated, and a logrotate rule added. The DataNode resumed without restart.')),
    ),
    example(
        shrun("""
            !mkdir -p app/logs app/data app/tmp
            !head -c 6000000 /dev/zero > app/logs/app.log; head -c 2500000 /dev/zero > app/logs/app.log.1; head -c 1500000 /dev/zero > app/data/part-0001
            !for i in $(seq 1 300); do : > "app/tmp/t$i"; done
            du -h --max-depth=1 app | sort -rh
            du -ah app/logs | sort -rh | head -n 3
            find app -type f -size +2M -exec ls -lh {} + | awk '{print $5, $9}'
            find app/tmp -type f | wc -l
            gzip app/logs/app.log.1 && ls -lh app/logs | awk 'NR > 1 {print $5, $9}'
            sleep 300 >> app/logs/app.log &
            : > app/logs/app.log; ls -lh app/logs/app.log | awk '{print $5, $9}'
            du -sh app
            kill $!
        """),
        title='Example: Find What Filled the Disk, Then Free Space Safely'),
    steps(
        ('Confirm', '<code>df -h</code> and <code>df -i</code>.'),
        ('Locate', '<code>du -xh --max-depth=1 /path | sort -rh</code>, repeat deeper.'),
        ('Inspect big files', '<code>find /path -xdev -size +500M -exec ls -lh {} +</code>.'),
        ('Free space safely', 'Compress/remove old rotated logs; truncate active logs with <code>: &gt; file</code>; check <code>lsof +L1</code>.'),
        ('Fix the cause', 'logrotate, retention cron, monitoring alert at 80 %.'),
        title='Steps to Recover a Full Disk'),
    crossq(
        ('Why truncate instead of rm on an active log?', 'rm removes the name but the process keeps writing to the open (deleted) file, so space is not freed; truncation empties the same file.'),
        ('What uses inodes but little space?', 'Huge numbers of tiny files (session files, temp files, mail queues); df -i reaches 100 % while df -h shows free space.'),
        ('Why du -x?', 'It stays on one filesystem, so mounted disks (e.g. /data, /proc) do not distort the numbers for /.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: join two CSV files and compute per-group averages using only shell tools.', 'CSV Join & Aggregate', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('Two shell approaches: <strong>awk two-file idiom</strong>: <code>awk -F, \'NR==FNR {lookup[$1]=$3; next} {…lookup[$1]…}\' a.csv b.csv</code> '
               '(NR==FNR is true only while reading the first file, which builds a lookup table; the second file is processed against it); or <strong>join</strong> '
               'on files sorted by the key (<code>join -t, -1 1 -2 1</code>). Aggregation then uses awk arrays. Handle headers (<code>FNR &gt; 1</code>) and invalid '
               'values (e.g. "AB").'),
        tags('awk NR==FNR', 'join', 'CSV', 'group by', 'shell analytics'),
    ),
    analogy('awk first <strong>memorises the class list</strong> (roll → course), then walks through the marks sheet, <strong>looking up each roll\'s course</strong> '
            'and adding the mark to that course\'s running total, a VLOOKUP and pivot in one pass.'),
    csvjoin_anim(),
    real_world(
        scenario('Server without Python or a database',
                 p('On a locked-down exam server, a coordinator needs course-wise averages from two exported CSVs before the files leave the machine. A three-line '
                   'awk program produces the same numbers the SQL query gives later in the warehouse.')),
    ),
    example(
        shrun("""
            awk -F, 'FNR == 1 {next}
                     NR == FNR {course[$1] = $3; next}
                     $3 ~ /^[0-9]+$/ {sum[course[$1]] += $3; n[course[$1]]++}
                     END {for (c in sum) printf "%-8s %5.1f %d\\n", c, sum[c] / n[c], n[c]}' students.csv marks.csv | sort
            join -t, <(tail -n +2 students.csv | sort -t, -k1,1) <(tail -n +2 marks.csv | sort -t, -k1,1) | head -n 3
            join -t, -v 1 <(tail -n +2 students.csv | cut -d, -f1,2 | sort) <(tail -n +2 marks.csv | cut -d, -f1 | sort -u)
            awk -F, 'FNR > 1 && $3 !~ /^[0-9]+$/ {print "invalid mark:", $0}' marks.csv
        """, files=COMMON),
        title='Example: Course Averages, an Inner Join, Students Without Marks, Bad Values'),
    steps(
        ('Know the keys', 'Same key format in both files (trim spaces, same case).'),
        ('Small lookup + big file', 'awk NR==FNR idiom (lookup file first).'),
        ('Two big sorted files', '<code>join</code> on sorted input.'),
        ('Clean', 'Skip headers; detect non-numeric values.'),
        ('Cross-check', 'Compare a few results with a spreadsheet or SQL.'),
        title='Steps for Shell Joins'),
    crossq(
        ('Why did join -v 1 print nothing?', 'Every student in students.csv has at least one mark row; -v 1 prints only unpaired lines from file 1 (like a LEFT ANTI JOIN).'),
        ('Why is NR == FNR true only for the first file?', 'NR counts lines across all input; FNR restarts at 1 for each file, so they are equal only while reading the first one.'),
        ('Limits of this approach?', 'Simple CSV only (no quoted commas), the lookup table must fit in memory, and complex logic becomes hard to maintain; switch to Python/SQL then.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Scenario: write a monitoring script that checks disk, processes, a port and new log errors, suitable for cron.', 'Health-Check Script', minutes=10, tag='Scenario', cards=[
    definition(
        defbox('A cron-friendly health check: <strong>quiet when healthy</strong>, prints a clear alert and exits non-zero when not; checks <strong>disk usage</strong> '
               '(df), <strong>processes</strong> (pgrep), <strong>endpoints</strong> (curl status codes), and <strong>new errors</strong> in logs since the last run '
               '(remembering the last position in a state file); thresholds come from variables; output goes to mail or a chat webhook.'),
        tags('monitoring', 'health check', 'cron', 'pgrep', 'curl', 'alerting'),
    ),
    analogy('A night watchman\'s round: check the water tank level (disk), that the generator is running (process), that the phone line works (port), and '
            'read only the new entries in the incident book since the last round (log), then call the manager only if something is wrong.'),
    monitor_anim(),
    real_world(
        scenario('Lab server watchdog',
                 p('Every 5 minutes cron runs the check with <code>DISK_LIMIT=85</code>; any alert is piped to a Slack webhook via curl. Because it only reports new log '
                   'errors, the same error does not alert every 5 minutes, and a healthy server produces no messages at all.')),
    ),
    example(
        script_file('health.sh', HEALTH),
        shrun("""
            python3 -m http.server 8000 --bind 127.0.0.1 > web.log 2>&1 &
            sleep 1
            bash health.sh; echo "exit $?"
            bash health.sh; echo "exit $? (second run: old errors not repeated)"
            echo '2026-10-13 09:05:00 ERROR Disk quota exceeded for /data/results' >> app.log
            DISK_LIMIT=1 bash health.sh; echo "exit $?"
            kill %1; sleep 0.5
            bash health.sh; echo "exit $?"
        """, files={'health.sh': HEALTH, 'app.log': APP_LOG}),
        sh("""
            # crontab: every 5 minutes, alert to Slack only when the check fails
            */5 * * * * out=$(/opt/ops/health.sh 2>&1) || curl -s -X POST -H 'Content-type: application/json' \\
                --data "{\\"text\\": \\"$(hostname): $out\\"}" "$SLACK_WEBHOOK_URL"
        """, title='crontab entry'),
        title='Example: Four Runs of the Health Check'),
    steps(
        ('List what "healthy" means', 'Disk, processes, ports/URLs, logs, maybe HDFS/YARN status commands.'),
        ('Make thresholds configurable', 'Environment variables with defaults.'),
        ('Report only new problems', 'State file for log positions; avoid alert storms.'),
        ('Exit codes and messages', '0 healthy, 1 with a readable list of issues.'),
        ('Schedule and route alerts', 'cron + mail/Slack; consider Prometheus/Grafana as the setup grows.'),
        title='Steps to Build a Health Check'),
    crossq(
        ('Why did the first run report 2 errors but the second none?', 'The script stores how many log lines it has seen; only lines added after that position are counted.'),
        ('Why not set -e in this script?', 'Failed checks are expected outcomes to collect, not reasons to abort; the script handles each status explicitly.'),
        ('What would you add for a Hadoop cluster?', 'hdfs dfsadmin -report (dead DataNodes, remaining space), yarn node -list (unhealthy nodes), and checks on NameNode/ResourceManager web ports.'),
    ),
]),
])
