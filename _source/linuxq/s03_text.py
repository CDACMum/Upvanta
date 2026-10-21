from build import *
from linuxq.anims import *
from linuxq.runner import shrun, sh, script_file
from linuxq.data import COMMON, APP_LOG, ACCESS_LOG

FILES = {**COMMON, 'app.log': APP_LOG}

SECTION = dict(level='basic', title='Text Processing', questions=[

# ------------------------------------------------------------------ 11
Q('How do you search text with grep? Explain the important options and regular expressions.', 'grep', minutes=8, cards=[
    definition(
        defbox('<code>grep PATTERN files</code> prints lines matching a pattern. Key options: <code>-i</code> ignore case, <code>-v</code> invert, <code>-c</code> '
               'count, <code>-n</code> line numbers, <code>-w</code> whole words, <code>-r</code>/<code>-R</code> recursive, <code>-l</code> file names only, '
               '<code>-o</code> only the matched part, <code>-E</code> extended regex (<code>|</code>, <code>+</code>, <code>{n}</code>), <code>-F</code> fixed '
               'string, <code>-A/-B/-C n</code> context lines.',
               'Regex basics: <code>^</code> start, <code>$</code> end, <code>.</code> any character, <code>*</code> zero or more, <code>[0-9]</code> class, '
               '<code>\\b</code> word boundary. grep returns exit status 0 if something matched, 1 if not.'),
        tags('grep', 'regex', 'grep -E', 'log analysis'),
    ),
    analogy('grep is a <strong>highlighter pen that cuts out lines</strong>: you tell it what to look for, and it hands you only the lines that contain it.'),
    grep_anim(),
    real_world(
        scenario('Debugging a failed job',
                 p('<code>grep -n ERROR job.log</code> finds failure lines; <code>grep -C 3 "Exception" spark.log</code> shows context around a stack trace; '
                   '<code>grep -rl "jdbc:mysql" /opt/etl</code> lists every script that connects to MySQL before a password change.')),
    ),
    example(
        shrun("""
            grep ERROR app.log
            grep -c ERROR app.log
            grep -inE 'warn|error' app.log
            grep -v INFO app.log | wc -l
            grep -oE '[0-9]{4}-[A-Z]+' app.log
            grep -w ML marks.csv
            grep -A1 'Cannot connect' app.log
            grep -q FATAL app.log; echo "exit status: $?"
        """, files=FILES),
        title='Example: Searching a Job Log'),
    steps(
        ('Start simple', '<code>grep word file</code>.'),
        ('Refine', 'Add <code>-i</code>, <code>-w</code>, anchors <code>^</code>/<code>$</code>.'),
        ('Several alternatives', '<code>grep -E "a|b"</code>.'),
        ('Across files', '<code>grep -rn pattern dir/</code> (add <code>--include="*.py"</code>).'),
        ('In scripts', 'Use <code>grep -q</code> and the exit status.'),
        title='Steps to Search Effectively'),
    crossq(
        ('grep vs egrep vs fgrep?', 'egrep = grep -E (extended regex), fgrep = grep -F (fixed strings, fastest); the separate names are deprecated.'),
        ('How do you search compressed logs?', 'zgrep pattern file.gz.'),
        ('Why quote the pattern?', 'So the shell does not expand *, ?, [ ] or split on spaces before grep sees the pattern.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What is sed? How do you substitute, delete and edit files in place?', 'sed', minutes=7, cards=[
    definition(
        defbox('<strong>sed</strong> (stream editor) applies editing commands to each input line: <code>s/regex/replacement/flags</code> substitute '
               '(<code>g</code> all matches, <code>I</code> ignore case), <code>d</code> delete, <code>p</code> print (with <code>-n</code>), <code>i</code>/<code>a</code> '
               'insert/append text. Addresses select lines: numbers (<code>1</code>, <code>$</code>), ranges (<code>2,5</code>), patterns (<code>/ERROR/</code>).',
               '<code>-i</code> edits the file in place (<code>-i.bak</code> keeps a backup); <code>-E</code> enables extended regex with groups referenced as '
               '<code>\\1</code>, <code>\\2</code>.'),
        tags('sed', 'substitute', 'in-place edit', 'regex'),
    ),
    analogy('sed is <strong>Find &amp; Replace that works on a conveyor belt</strong>: each line passes under the tool, gets corrected, and moves on, so the '
            'file can be any size.'),
    sed_anim(),
    real_world(
        scenario('Fixing configs and data',
                 p('Change the NameNode host in 40 config files: <code>sed -i \'s/old-nn:8020/new-nn:8020/g\' *.xml</code>. Clean an export: remove the header, '
                   'replace "AB" with empty values, convert semicolons to commas, before loading into Hive.')),
    ),
    example(
        shrun("""
            sed 's/AB/0/' marks.csv | tail -n 2
            sed '1d' marks.csv | head -n 2
            sed -n '/ERROR/p' app.log
            sed -n '2,3p' students.csv
            sed -E 's/^([0-9]+),([^,]+),.*/\\2 (\\1)/' students.csv | tail -n +2 | head -n 3
            cp students.csv s2.csv
            sed -i.bak 's/PG-DBDA/DBDA/g' s2.csv
            grep -c PG-DBDA s2.csv s2.csv.bak
            diff s2.csv.bak s2.csv | head -n 4
        """, files=FILES),
        title='Example: Substitute, Delete, Print Ranges, In-place with Backup'),
    steps(
        ('Preview first', 'Run without <code>-i</code> and check the output.'),
        ('Substitute', '<code>sed \'s/old/new/g\'</code>; use another delimiter for paths: <code>s#/a#/b#</code>.'),
        ('Select lines', 'By number, range or <code>/pattern/</code>.'),
        ('Edit in place with backup', '<code>sed -i.bak</code>.'),
        ('Verify', '<code>diff file.bak file</code>.'),
        title='Steps to Edit with sed'),
    crossq(
        ('Why does sed -i behave differently on macOS?', 'BSD sed requires a suffix argument after -i (use -i \'\' for none); GNU sed (Linux) makes it optional.'),
        ('How do you replace only on lines matching a pattern?', '<code>sed \'/ERROR/s/MySQL/database/\'</code>.'),
        ('sed vs awk?', 'sed is best for line-oriented substitutions and deletions; awk for field-based logic, calculations and reports.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What is awk? How do you work with fields, conditions and aggregations?', 'awk', minutes=9, cards=[
    definition(
        defbox('<strong>awk</strong> is a small language for processing <strong>column-structured text</strong>. Each line is split into fields '
               '<code>$1</code>, <code>$2</code>… (<code>$0</code> is the whole line) using whitespace or <code>-F</code> separator. A program is a list of '
               '<code>pattern { action }</code> rules plus optional <code>BEGIN{}</code> and <code>END{}</code> blocks.',
               'Built-ins: <code>NR</code> line number, <code>NF</code> number of fields, <code>FS</code>/<code>OFS</code> input/output separators. Associative '
               'arrays (<code>sum[$2] += $3</code>) make group-by aggregations easy; <code>printf</code> formats output.'),
        tags('awk', 'fields', 'NR', 'NF', 'aggregation', 'BEGIN END'),
    ),
    analogy('awk is a <strong>clerk with a calculator</strong> reading a register row by row: for each row that matches a rule, note certain columns or add '
            'them to a running total, and at the end print the summary.'),
    awk_anim(),
    real_world(
        scenario('Quick reports without Python',
                 p('On a server without pandas, awk computes subject averages from <code>marks.csv</code>, total bytes per IP from a web log, or the slowest '
                   'requests from an access log, in one line, streaming files of any size.')),
    ),
    example(
        shrun("""
            awk -F, 'NR > 1 {print $2, $3}' marks.csv | head -n 3
            awk -F, '$3 ~ /^[0-9]+$/ && $3 < 60 {print $1, $2, $3}' marks.csv
            awk -F, 'NR > 1 && $3 ~ /^[0-9]+$/ {sum[$2] += $3; n[$2]++}
                     END {for (s in sum) printf "%-7s %5.1f\\n", s, sum[s] / n[s]}' marks.csv | sort
            awk -F, 'NR > 1 {c[$3]++} END {for (k in c) print k, c[k]}' students.csv | sort
            awk -F, 'BEGIN {OFS="|"} NR <= 3 {print $2, $5, NF}' students.csv
            awk '{print $3}' app.log | sort | uniq -c
        """, files=FILES),
        title='Example: Fields, Filters, Group-by Averages, Counts, OFS'),
    steps(
        ('Set the separator', '<code>-F,</code> for CSV (simple CSV without quoted commas).'),
        ('Skip the header', '<code>NR &gt; 1</code>.'),
        ('Filter', 'Conditions on fields: <code>$3 &gt;= 60</code>, <code>$2 == "SQL"</code>, regex <code>~</code>.'),
        ('Aggregate', 'Arrays keyed by a field; print in END.'),
        ('Format', '<code>printf</code>, <code>OFS</code>; sort the result with sort.'),
        title='Steps to Write an awk One-liner'),
    crossq(
        ('Why check $3 ~ /^[0-9]+$/?', 'To skip non-numeric values such as "AB" for absent, which awk would otherwise treat as 0 and pull the average down.'),
        ('Why is the output of for (k in arr) unordered?', 'awk arrays are hash tables; pipe to sort (or use gawk\'s PROCINFO["sorted_in"]).'),
        ('Can awk handle quoted CSV fields with commas?', 'Not with -F, alone; gawk\'s FPAT or --csv (gawk 5.3+) handle it, or use a proper CSV tool (csvkit, Python, Miller).'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do you combine cut, sort, uniq, tr and wc in pipelines? Find the most frequent values.', 'cut, sort, uniq Pipelines', minutes=8, cards=[
    definition(
        defbox('<code>cut -d, -f2,5</code> extracts fields (or <code>-c</code> character positions); <code>sort</code> sorts (<code>-n</code> numeric, <code>-r</code> '
               'reverse, <code>-t, -k3</code> by field, <code>-u</code> unique); <code>uniq</code> collapses <strong>adjacent</strong> duplicates (<code>-c</code> count, '
               '<code>-d</code> only duplicated); <code>tr</code> translates or deletes characters; <code>wc</code> counts; <code>head</code>/<code>tail</code> trim; '
               '<code>paste</code>, <code>join</code>, <code>comm</code> combine files.',
               'The standard "top-N" idiom: <code>… | sort | uniq -c | sort -rn | head</code>.'),
        tags('cut', 'sort', 'uniq', 'tr', 'pipeline', 'top-N'),
    ),
    analogy('An assembly line of specialists: one <strong>cuts out</strong> the column, one <strong>sorts</strong> the pieces, one <strong>counts</strong> '
            'identical ones, one <strong>ranks</strong> them. Each does one small job well.'),
    pipe_text_anim(),
    real_world(
        scenario('Questions answered in seconds',
                 p('"Which cities do most students come from?", "Which IPs hit the LMS most?", "How many distinct subjects?", "Which roll numbers appear twice in '
                   'the upload?" are all one pipeline, no spreadsheet needed.')),
    ),
    example(
        shrun("""
            tail -n +2 students.csv | cut -d, -f5 | sort | uniq -c | sort -rn | head -n 3
            cut -d, -f2 marks.csv | tail -n +2 | sort -u | wc -l
            tail -n +2 marks.csv | sort -t, -k3,3nr | head -n 3
            cut -d, -f1 marks.csv | tail -n +2 | sort | uniq -d
            echo 'PG-DBDA Kharghar' | tr 'a-z' 'A-Z'
            tr -d '\\r' < students.csv | head -n 1 | tr ',' '\\n'
        """, files=FILES),
        title='Example: Top Cities, Distinct Subjects, Top Marks, Duplicate Rolls, tr'),
    steps(
        ('Extract', '<code>cut</code> (or awk for complex parsing).'),
        ('Sort', 'Always before uniq.'),
        ('Count', '<code>uniq -c</code>.'),
        ('Rank', '<code>sort -rn</code>, <code>head</code>.'),
        ('Clean characters', '<code>tr -d \'\\r\'</code> for Windows line endings, <code>tr \'A-Z\' \'a-z\'</code> for case.'),
        title='Steps to Build a Counting Pipeline'),
    crossq(
        ('Why does uniq miss duplicates?', 'It only compares neighbouring lines; unsorted input leaves duplicates apart.'),
        ('sort -n vs sort?', 'Default is text order ("100" before "9"); -n compares numbers. -k3,3n sorts by the 3rd field only.'),
        ('What are \\r characters?', 'Windows files end lines with \\r\\n; the \\r breaks comparisons and shows as ^M. Remove with tr -d \'\\r\' or dos2unix.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you find files with find? How do -exec and xargs work?', 'find & xargs', minutes=8, cards=[
    definition(
        defbox('<code>find PATH tests actions</code> walks a directory tree. Tests: <code>-name/-iname \'*.log\'</code>, <code>-type f/d/l</code>, <code>-size +100M</code>, '
               '<code>-mtime +7</code> (modified more than 7 days ago), <code>-mmin -30</code>, <code>-user</code>, <code>-perm</code>, <code>-empty</code>, '
               '<code>-maxdepth n</code>; combine with <code>!</code>, <code>-o</code>. Actions: <code>-print</code> (default), <code>-delete</code>, '
               '<code>-exec cmd {} \\;</code> (one per file), <code>-exec cmd {} +</code> (batched).',
               '<code>xargs</code> turns input lines into command arguments; with <code>find -print0 | xargs -0</code> names with spaces are safe; '
               '<code>xargs -P 4</code> runs in parallel.'),
        tags('find', 'xargs', '-exec', '-mtime', 'cleanup'),
    ),
    analogy('find is a <strong>librarian walking every shelf</strong> with a checklist ("older than a week, bigger than 50 MB, ends in .log"); -exec/xargs '
            'is <strong>handing each book found to someone</strong> who stamps, moves or discards it.'),
    find_anim(),
    real_world(
        scenario('Log housekeeping',
                 p('A nightly cron job compresses logs older than 1 day and deletes those older than 30: '
                   '<code>find /var/log/etl -name "*.log" -mtime +1 -exec gzip {} +</code> and <code>find /var/log/etl -name "*.gz" -mtime +30 -delete</code>.')),
    ),
    example(
        shrun("""
            !mkdir -p logs data; for d in 01 05 12 13; do echo "log $d" > logs/app-2026-10-$d.log; touch -d "2026-10-$d 10:00" logs/app-2026-10-$d.log; done
            !head -c 3000000 /dev/zero > data/backup.bin; touch "data/my notes.txt"
            find . -name '*.log' | sort
            find logs -type f -mtime +7 | sort
            find . -size +1M -exec ls -lh {} +
            find logs -name '*.log' -mtime +7 -exec gzip {} +
            ls logs
            find . -name '*.txt' -print0 | xargs -0 ls -l
            find . -type f | wc -l
        """, files=COMMON),
        title='Example: By Name, Age and Size; Compress Old Logs; Safe xargs'),
    steps(
        ('Write the tests', 'Name, type, age, size.'),
        ('Run with -print first', 'Check the list.'),
        ('Add the action', '<code>-exec … {} +</code>, <code>-delete</code>, or pipe to <code>xargs</code>.'),
        ('Handle odd names', '<code>-print0 | xargs -0</code>.'),
        ('Schedule', 'Put housekeeping in cron with absolute paths.'),
        title='Steps for Safe Bulk Operations'),
    crossq(
        ('-exec {} \\; vs {} +?', '\\; runs the command once per file (slow for thousands); + passes many files to one command.'),
        ('What does -mtime +7 mean exactly?', 'Modified more than 7×24 hours ago (fractions are truncated to whole days); -mtime -1 = within the last day.'),
        ('find vs locate?', 'locate searches a prebuilt database (fast, possibly stale); find searches the live filesystem with rich conditions.'),
    ),
]),
])
