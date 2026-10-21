from build import *
from linuxq.anims import *
from linuxq.runner import shrun, sh, script_file
from linuxq.data import COMMON

REPORT = r"""
#!/usr/bin/env bash
# report.sh <course> [min_marks]  - list students of a course
course="$1"
min="${2:-60}"
echo "script: $0 | args: $# | all: $@"
echo "course=$course, min=$min"
grep -c ",$course," students.csv
exit 3
"""

CHECK = r"""
#!/usr/bin/env bash
file="$1"
if [[ ! -e "$file" ]]; then
    echo "$file: missing"; exit 1
elif [[ ! -s "$file" ]]; then
    echo "$file: empty"; exit 2
fi
lines=$(wc -l < "$file")
if (( lines > 5 )); then size="large"; else size="small"; fi
case "$file" in
    *.csv) kind="CSV" ;;
    *.log) kind="log" ;;
    *)     kind="other" ;;
esac
echo "$file: $kind, $lines lines, $size"
[[ "$file" =~ ^marks ]] && echo "  -> marks file detected"
exit 0
"""

LOOPS = r"""
#!/usr/bin/env bash
for f in *.csv; do
    printf '%-14s %3d lines\n' "$f" "$(wc -l < "$f")"
done
for ((i = 1; i <= 3; i++)); do echo -n "round $i "; done; echo
count=0
while IFS=, read -r roll name course centre city; do
    [[ "$course" == "PG-DBDA" ]] || continue
    count=$((count + 1))
    echo "$count. $name ($roll) from $city"
done < <(tail -n +2 students.csv)
tries=0
until [[ -f ready.flag ]] || (( ++tries > 3 )); do
    echo "waiting for ready.flag (try $tries)"
    (( tries == 2 )) && touch ready.flag
done
echo "done after $tries tries"
"""

STRICT = r"""
#!/usr/bin/env bash
set -euo pipefail
log() { echo "$(date +%T) [$1] ${*:2}" >&2; }
is_number() { [[ $1 =~ ^[0-9]+$ ]]; }
avg_marks() {
    local subject="$1" sum=0 n=0 roll subj m
    while IFS=, read -r roll subj m; do
        [[ "$subj" == "$subject" ]] || continue
        if is_number "$m"; then sum=$((sum + m)); n=$((n + 1)); else log WARN "skipping $roll: '$m'"; fi
    done < <(tail -n +2 marks.csv)
    (( n > 0 )) || return 1
    echo $((sum / n))
}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"; log INFO "cleaned up"' EXIT
trap 'log ERROR "failed at line $LINENO"' ERR
log INFO "SQL average: $(avg_marks SQL)"
log INFO "ML average: $(avg_marks ML)"
avg_marks Hadoop > "$tmp/out" || log WARN "no marks for Hadoop"
echo "next line uses an unset variable"
echo "$undefined_var"
echo "never printed"
"""

ARRAYS = r"""
#!/usr/bin/env bash
course="PG-DBDA"; min=60; verbose=0
while getopts "c:m:v" opt; do
    case $opt in
        c) course=$OPTARG ;;
        m) min=$OPTARG ;;
        v) verbose=1 ;;
        *) echo "usage: $0 [-c course] [-m min] [-v]"; exit 1 ;;
    esac
done
subjects=(SQL Spark ML)
subjects+=(Python)
echo "subjects: ${subjects[*]} (count ${#subjects[@]}, second ${subjects[1]})"
declare -A fee=([PG-DBDA]=95000 [PG-DAC]=90000)
echo "fee for $course: ${fee[$course]:-unknown}"
f="marks_2026.csv"
echo "${f%.csv} | ${f#marks_} | ${#f} | ${f^^} | ${f/2026/2027}"
total=$(( 82 + 61 + 91 ))
echo "total=$total integer avg=$(( total / 3 )) bc avg=$(echo "scale=2; $total / 3" | bc)"
(( verbose )) && echo "course=$course min=$min"
"""

SECTION = dict(level='intermediate', title='Shell Scripting', questions=[

# ------------------------------------------------------------------ 21
Q('How do you write and run a shell script? Explain the shebang, arguments ($1, $@, $#) and exit codes.', 'Your First Script', minutes=8, cards=[
    definition(
        defbox('A <strong>shell script</strong> is a text file of commands. The first line, the <strong>shebang</strong> (<code>#!/usr/bin/env bash</code> or '
               '<code>#!/bin/bash</code>), names the interpreter. Run it with <code>bash script.sh</code>, or make it executable (<code>chmod +x</code>) and run '
               '<code>./script.sh</code>.',
               'Special parameters: <code>$0</code> script name, <code>$1…$9</code>, <code>${10}</code> arguments, <code>$#</code> count, <code>"$@"</code> all '
               'arguments as separate words, <code>$?</code> last exit status, <code>$$</code> PID. <code>${var:-default}</code> provides defaults. '
               '<code>exit N</code> sets the script\'s exit status (0 = success).'),
        tags('shebang', 'shell script', '$1', '$@', '$#', 'exit code'),
    ),
    analogy('A script is a <strong>recipe card</strong>: the first line says which chef can read it (bash), the blanks (<code>$1</code>, <code>$2</code>) are '
            'filled with the ingredients you pass when you use it, and the final "success/failure" stamp is the exit code.'),
    script_anim(),
    real_world(
        scenario('Re-usable lab scripts',
                 p('<code>./ingest.sh 2026-10-13 kharghar</code> downloads one day\'s attendance for one centre, puts it into HDFS and exits non-zero on any failure, '
                   'so cron, Airflow or a CI job can detect and alert on it.')),
    ),
    example(
        script_file('report.sh', REPORT),
        shrun("""
            ./report.sh PG-DBDA
            chmod +x report.sh
            ./report.sh PG-DBDA 50; echo "exit code: $?"
            bash report.sh PG-DAI
            ./report.sh "PG DBDA" extra args
        """, files={**COMMON, 'report.sh': REPORT}),
        title='Example: Arguments, Defaults and the Exit Code'),
    steps(
        ('Create the file', 'Shebang on line 1, comments describing usage.'),
        ('Read arguments', '<code>course="$1"</code>; validate <code>$#</code>; defaults with <code>${2:-60}</code>.'),
        ('Make executable', '<code>chmod +x script.sh</code>.'),
        ('Run and test', '<code>./script.sh args</code>; check <code>echo $?</code>.'),
        ('Return meaningful codes', '<code>exit 0</code> on success, non-zero for specific failures.'),
        title='Steps to Write a Script'),
    crossq(
        ('Why "Permission denied" on ./report.sh?', 'The file has no execute bit; chmod +x it or run bash report.sh.'),
        ('"$@" vs "$*"?', '"$@" expands to each argument as a separate word (preserving spaces inside arguments); "$*" joins them into one string.'),
        ('#!/bin/bash vs #!/usr/bin/env bash?', 'env finds bash on PATH (portable across systems where bash lives elsewhere); /bin/bash is fixed and immune to PATH changes.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('How do conditions work in bash? Explain if, [ ], [[ ]], file tests and case.', 'if, test & case', minutes=8, cards=[
    definition(
        defbox('<code>if COMMAND; then … elif …; else …; fi</code> branches on a command\'s exit status. <code>[ … ]</code> (test) and bash\'s safer '
               '<code>[[ … ]]</code> evaluate expressions; <code>(( … ))</code> evaluates arithmetic.',
               'File tests: <code>-e</code> exists, <code>-f</code> regular file, <code>-d</code> directory, <code>-s</code> non-empty, <code>-r/-w/-x</code>, '
               '<code>-nt</code> newer than. Strings: <code>==</code>, <code>!=</code>, <code>-z</code> empty, <code>-n</code> non-empty, <code>=~</code> regex. '
               'Integers: <code>-eq -ne -lt -le -gt -ge</code> (or symbols inside <code>(( ))</code>). <code>case</code> matches a value against glob patterns.'),
        tags('if', '[[ ]]', 'test', 'file tests', 'case', 'arithmetic'),
    ),
    analogy('An if statement is a <strong>gatekeeper asking a yes/no question</strong> (does the file exist? is it empty?) and sending you through a different '
            'door for each answer; case is a <strong>sorting desk</strong> that routes items by label.'),
    if_anim(),
    real_world(
        scenario('Defensive ingest',
                 p('Before loading a daily file into Hive, the script checks that it exists, is not empty, is newer than the last load, and has the expected '
                   'extension; otherwise it exits with a specific code that the scheduler turns into an alert.')),
    ),
    example(
        script_file('check.sh', CHECK),
        shrun("""
            touch empty.csv
            for f in marks.csv students.csv empty.csv nofile.txt app.log; do bash check.sh "$f"; echo "  exit $?"; done
            [ 10 -gt 9 ] && echo 'numeric: 10 > 9'
            [[ 10 > 9 ]] || echo 'string compare: "10" sorts before "9"'
            x=''; [ -z "$x" ] && echo 'x is empty'
        """, files={**COMMON, 'check.sh': CHECK, 'app.log': 'one line'}),
        title='Example: File Checks, Arithmetic, case, Regex and a Classic Trap'),
    steps(
        ('Validate inputs first', 'Exit early with clear messages.'),
        ('Use [[ ]] in bash', 'Quote variables anyway for clarity.'),
        ('Numbers', '<code>(( a &gt; b ))</code> or <code>-gt</code>; never <code>&gt;</code> inside [[ ]] for numbers.'),
        ('Many alternatives', '<code>case</code> with patterns.'),
        ('Distinct exit codes', 'So callers know what went wrong.'),
        title='Steps to Write Conditions'),
    crossq(
        ('Why is [[ 10 > 9 ]] false?', 'Inside [[ ]], > compares strings lexically ("1" sorts before "9"); use -gt or (( 10 > 9 )) for numbers.'),
        ('[ vs [[?', '[ is a command (POSIX, portable to sh); [[ is bash syntax: no word splitting inside, supports &&, ||, pattern and regex matching.'),
        ('Why end check.sh with exit 0?', 'A script returns the status of its last command. Without it, a final [[ … ]] &amp;&amp; echo returns 1 whenever the test is false, so callers would see a valid file as a failure.'),
        ('What does if grep -q x file; then do?', 'Uses grep\'s exit status directly: no need for $? or [ ].'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How do you write loops in bash? How do you read a file line by line?', 'Loops & Reading Files', minutes=8, cards=[
    definition(
        defbox('<code>for x in list; do …; done</code> iterates over words, globs (<code>*.csv</code>) or ranges (<code>{1..10}</code>); C-style '
               '<code>for ((i=0; i&lt;n; i++))</code>; <code>while COND; do …; done</code> and <code>until COND</code> loop on a command\'s status; '
               '<code>break</code> and <code>continue</code> control flow.',
               'Read a file line by line with <code>while IFS=, read -r a b c; do …; done &lt; file</code>: <code>IFS</code> sets the field separator, '
               '<code>-r</code> keeps backslashes. Feeding via <code>&lt; &lt;(command)</code> (process substitution) keeps variables set inside the loop, '
               'unlike a pipe into while, which runs in a subshell.'),
        tags('for', 'while', 'until', 'read', 'IFS', 'process substitution'),
    ),
    analogy('A for loop is a <strong>teacher calling the roll</strong> from a list; a while-read loop is <strong>reading the register line by line</strong> '
            'and acting on each row; until is <strong>knocking until the door opens</strong> (with a limit on tries).'),
    loop_anim(),
    real_world(
        scenario('Batch processing',
                 p('Loop over every centre\'s CSV in a folder, validate and upload each; read a list of roll numbers to create accounts; retry a database '
                   'connection up to 5 times with a sleep in between before giving up.')),
    ),
    example(
        script_file('loops.sh', LOOPS),
        shrun("""
            bash loops.sh
            n=0; tail -n +2 students.csv | while read -r line; do n=$((n + 1)); done; echo "after pipe-while: n=$n"
        """, files={**COMMON, 'loops.sh': LOOPS}),
        title='Example: for, C-style, while read (CSV), until with Retries'),
    steps(
        ('Files', '<code>for f in dir/*.csv; do … "$f" …; done</code>.'),
        ('Lines', '<code>while IFS= read -r line; do …; done &lt; file</code>.'),
        ('Fields', 'Set IFS to the delimiter and name the fields in read.'),
        ('Keep variables', 'Use <code>&lt; file</code> or <code>&lt; &lt;(cmd)</code> instead of <code>cmd | while</code>.'),
        ('Retries', 'until/while with a counter and sleep; fail after N tries.'),
        title='Steps for Loops'),
    crossq(
        ('Why was n still 0 after the pipe-while?', 'Each part of a pipeline runs in a subshell; the loop incremented its own copy of n, which vanished when the pipeline ended.'),
        ('Why not for line in $(cat file)?', 'It splits on all whitespace and expands globs, so lines with spaces break into several items.'),
        ('Why read -r?', 'Without -r, backslashes in the input are treated as escape characters and removed.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you write functions and make scripts robust (set -euo pipefail, trap)?', 'Functions & Strict Mode', minutes=9, cards=[
    definition(
        defbox('<strong>Functions</strong>: <code>name() { …; }</code>, called like commands with arguments <code>$1…</code>; <code>local</code> limits variable scope; '
               '<code>return N</code> sets the status; data is "returned" by printing and capturing with <code>$(…)</code>.',
               '<strong>Strict mode</strong> <code>set -euo pipefail</code>: <code>-e</code> exit when a command fails (outside conditions), <code>-u</code> treat '
               'unset variables as errors, <code>-o pipefail</code> fail a pipeline if any stage fails. <strong>trap</strong> runs code on signals or events: '
               '<code>trap cleanup EXIT</code> (always), <code>trap … ERR</code> (on failure), <code>trap … INT TERM</code>.'),
        tags('functions', 'set -e', 'set -u', 'pipefail', 'trap', 'local'),
    ),
    analogy('Strict mode is a <strong>safety switch on a machine</strong>: at the first sign of trouble it stops, instead of continuing to produce defective '
            'parts. trap is the <strong>clean-up crew</strong> that always comes in at the end, however the shift ended.'),
    func_anim(),
    real_world(
        scenario('The script that deleted the wrong folder',
                 p('A clean-up script ran <code>rm -rf "$DATA_DIR/old"</code> with DATA_DIR misspelt; it expanded to <code>/old</code>. With <code>set -u</code> it would '
                   'have stopped with "unbound variable". Strict mode plus a trap for clean-up is now the team template for every script.')),
    ),
    example(
        script_file('strict.sh', STRICT),
        shrun("""
            bash strict.sh; echo "exit code: $?"
        """, files={**COMMON, 'strict.sh': STRICT}),
        title='Example: Functions, Warnings, Cleanup Trap, and set -u Stopping the Script'),
    steps(
        ('Start every script with', '<code>#!/usr/bin/env bash</code> and <code>set -euo pipefail</code>.'),
        ('Wrap steps in functions', 'With <code>local</code> variables.'),
        ('Log to stderr', 'So stdout stays clean for data.'),
        ('Clean up with trap EXIT', 'Temporary files and lock files.'),
        ('Lint', '<code>shellcheck script.sh</code>.'),
        title='Steps to a Robust Script'),
    crossq(
        ('Where does set -e not stop the script?', 'In commands tested by if/while/&&/||, inside $(…) in some contexts, and for non-final pipeline stages without pipefail; it is a safety net, not a replacement for explicit checks.'),
        ('Why did "avg_marks Hadoop > file || log WARN" not stop the script?', 'The failure was handled by ||, so set -e does not trigger.'),
        ('How do you return a string from a function?', 'Print it (echo/printf) and capture: result=$(func args).'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('How do you use arrays, string operations, arithmetic and command-line options (getopts) in bash?', 'Arrays, Strings & getopts', minutes=8, cards=[
    definition(
        defbox('<strong>Indexed arrays</strong>: <code>a=(x y z)</code>, <code>${a[1]}</code>, <code>"${a[@]}"</code>, <code>${#a[@]}</code>, <code>a+=(w)</code>. '
               '<strong>Associative arrays</strong>: <code>declare -A m=([k]=v)</code>, <code>${m[k]}</code>.',
               '<strong>Parameter expansion</strong>: <code>${f%.csv}</code> remove suffix, <code>${f#prefix}</code> remove prefix, <code>${#f}</code> length, '
               '<code>${f^^}</code>/<code>${f,,}</code> case, <code>${f/a/b}</code> replace, <code>${v:-default}</code>. <strong>Arithmetic</strong> '
               '<code>$(( ))</code> is integer-only (use <code>bc</code>/<code>awk</code> for decimals). <strong>getopts</strong> parses short options like '
               '<code>-c PG-DBDA -v</code>.'),
        tags('arrays', 'parameter expansion', 'arithmetic', 'getopts', 'bc'),
    ),
    analogy('Parameter expansion is a <strong>pair of scissors built into the shell</strong>: trim the extension, cut a prefix, change case, without calling '
            'another program. getopts is the <strong>form reader</strong> that knows which box (-c, -m) each answer belongs to.'),
    arrays_anim(),
    real_world(
        scenario('A friendly CLI for coordinators',
                 p('<code>./result.sh -c PG-DBDA -m 50 -v</code> instead of remembering argument positions; file names like <code>marks_2026-10.csv</code> become '
                   'output names with <code>${f%.csv}_report.txt</code>; fees come from an associative array.')),
    ),
    example(
        script_file('arrays.sh', ARRAYS),
        shrun("""
            bash arrays.sh
            bash arrays.sh -c PG-DAC -m 50 -v
            bash arrays.sh -x
        """, files={'arrays.sh': ARRAYS}),
        title='Example: Arrays, Associative Arrays, String Tricks, Arithmetic, getopts'),
    steps(
        ('Lists', 'Arrays and "${arr[@]}" (always quoted).'),
        ('Lookups', '<code>declare -A</code>.'),
        ('File-name manipulation', '<code>${f%.*}</code>, <code>${f##*/}</code> (basename), <code>${f%/*}</code> (dirname).'),
        ('Maths', '<code>$(( ))</code> for integers; bc/awk for decimals.'),
        ('Options', 'getopts with a usage message on unknown options.'),
        title='Steps to Use bash Features'),
    crossq(
        ('Why does bash say 234/3 = 78?', 'Integer division; 234/3 is exactly 78 here, but 143/2 would give 71. Use bc or awk for fractional results.'),
        ('${f#*_} vs ${f##*_}?', '# removes the shortest matching prefix, ## the longest (similarly % and %% for suffixes).'),
        ('getopts vs getopt?', 'getopts is a bash builtin for short options; the external getopt also supports long options (--course) but varies across systems.'),
    ),
]),
])
