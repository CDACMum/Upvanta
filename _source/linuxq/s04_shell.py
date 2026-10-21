from build import *
from linuxq.anims import *
from linuxq.runner import shrun, sh, script_file
from linuxq.data import COMMON, APP_LOG

FILES = {**COMMON, 'app.log': APP_LOG}

SECTION = dict(level='intermediate', title='Redirection, Pipes & the Shell', questions=[

# ------------------------------------------------------------------ 16
Q('What are stdin, stdout and stderr? Explain >, >>, 2>, 2>&1, /dev/null and tee.', 'Redirection', minutes=8, cards=[
    definition(
        defbox('Every process starts with three file descriptors: <strong>0 stdin</strong> (input), <strong>1 stdout</strong> (normal output), <strong>2 stderr</strong> '
               '(errors). Redirection connects them to files: <code>&gt;</code> overwrite stdout, <code>&gt;&gt;</code> append, <code>2&gt;</code> stderr, '
               '<code>2&gt;&amp;1</code> stderr to wherever stdout goes, <code>&amp;&gt;</code> both, <code>&lt;</code> stdin from a file, <code>&lt;&lt;EOF</code> '
               'here-document. <code>/dev/null</code> discards output; <code>tee</code> writes to a file and the screen at the same time.'),
        tags('stdout', 'stderr', 'redirection', '2>&1', '/dev/null', 'tee'),
    ),
    analogy('A program has <strong>one mouth and two exits</strong>: the main door for results (stdout) and the emergency exit for problems (stderr). '
            'Redirection decides where each door leads: a file, the bin (/dev/null), or both a file and your screen (tee).'),
    redirect_anim(),
    real_world(
        scenario('Cron job logging',
                 p('<code>/opt/etl/run.sh &gt;&gt; /var/log/etl/run.log 2&gt;&amp;1</code> keeps both output and errors from every night in one log; without '
                   '<code>2&gt;&amp;1</code> the error messages would be lost (or emailed by cron) and the log would look clean while the job failed.')),
    ),
    example(
        shrun("""
            ls students.csv missing.csv
            ls students.csv missing.csv > out.txt
            cat out.txt
            ls students.csv missing.csv > all.txt 2>&1; cat all.txt
            ls students.csv missing.csv 2>/dev/null
            echo 'run 1' > run.log; echo 'run 2' >> run.log; cat run.log
            grep -c ERROR app.log | tee count.txt; cat count.txt
            wc -l < marks.csv
            cat > notes.txt <<EOF
            batch: Aug-2026
            centre: Kharghar
            EOF
            cat notes.txt
        """, files=FILES),
        title='Example: Where Output and Errors Go'),
    steps(
        ('Separate or combine', 'Logs usually want <code>&gt;&gt; file 2&gt;&amp;1</code>.'),
        ('Order matters', '<code>&gt; file 2&gt;&amp;1</code>, not <code>2&gt;&amp;1 &gt; file</code>.'),
        ('Discard noise', '<code>2&gt;/dev/null</code>, carefully: you also hide real errors.'),
        ('See and save', '<code>| tee -a run.log</code>.'),
        ('Protect files', '<code>set -o noclobber</code> makes <code>&gt;</code> refuse to overwrite.'),
        title='Steps to Redirect Correctly'),
    crossq(
        ('Why did the error still appear with > out.txt?', 'Only stdout (fd 1) went to the file; the error was written to stderr (fd 2), still the terminal.'),
        ('What does 2>&1 > file do?', 'Duplicates stderr to the current stdout (the terminal) first, then moves stdout to the file, so errors still go to the screen.'),
        ('Does a pipe carry stderr?', 'No, only stdout; use 2>&1 | or |&amp; to include errors.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('How do pipes and command chaining (;, &&, ||) work? What is an exit status?', 'Pipes & Chaining', minutes=7, cards=[
    definition(
        defbox('A <strong>pipe</strong> <code>a | b</code> connects a\'s stdout to b\'s stdin; both run at the same time, streaming data. '
               '<strong>Exit status</strong>: every command returns a number in <code>$?</code>, 0 for success and 1–255 for failure.',
               'Chaining: <code>a ; b</code> always runs b; <code>a &amp;&amp; b</code> runs b only if a succeeded; <code>a || b</code> only if a failed. '
               '<code>( … )</code> runs a subshell (changes to directory/variables do not persist); <code>{ …; }</code> groups in the current shell. '
               'A pipeline\'s status is the last command\'s, unless <code>set -o pipefail</code>.'),
        tags('pipe', 'exit status', '&&', '||', 'pipefail', 'subshell'),
    ),
    analogy('&amp;&amp; is "<strong>if the exam is passed, then issue the certificate</strong>"; || is "<strong>if it failed, schedule a re-exam</strong>". '
            'A pipe is a <strong>bucket brigade</strong>: each person passes water to the next as soon as they get it.'),
    chain_anim(),
    real_world(
        scenario('Safe deployment steps',
                 p('<code>cd /opt/etl &amp;&amp; git pull &amp;&amp; ./tests.sh &amp;&amp; ./deploy.sh || echo "deploy failed" | mail -s alert team</code>: each step runs only '
                   'if the previous one succeeded, and any failure triggers the alert.')),
    ),
    example(
        shrun("""
            ls students.csv; echo "status: $?"
            ls nothing.csv; echo "status: $?"
            mkdir -p reports && echo 'created' && ls -d reports
            grep -q FATAL app.log || echo 'no FATAL errors'
            cat nothing.csv | wc -l; echo "pipeline status: $?"
            set -o pipefail; cat nothing.csv | wc -l; echo "with pipefail: $?"; set +o pipefail
            (cd /tmp && pwd); pwd
            { echo header; tail -n +2 marks.csv | head -n 2; } > top.csv; cat top.csv
        """, files=FILES),
        title='Example: Exit Statuses, Conditional Chains, pipefail, Subshells'),
    steps(
        ('Check $?', 'Right after a command (any command overwrites it).'),
        ('Chain dependent steps', 'With &amp;&amp;.'),
        ('Provide fallbacks', 'With ||.'),
        ('Pipelines in scripts', '<code>set -o pipefail</code> so a failing early stage is not hidden.'),
        ('Isolate', 'Use ( … ) when a step changes directory or environment temporarily.'),
        title='Steps for Reliable Command Sequences'),
    crossq(
        ('Why was the pipeline status 0 although cat failed?', 'By default a pipeline returns the status of its last command (wc succeeded); pipefail returns the last non-zero status.'),
        ('What does a && b || c do if b fails?', 'c runs too: it is not a true if/else. Use if a; then b; else c; fi when that matters.'),
        ('What is PIPESTATUS?', 'A bash array with the exit status of every command in the last pipeline, e.g. ${PIPESTATUS[0]}.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What are environment variables? How do PATH, export and .bashrc work?', 'Variables, export & PATH', minutes=8, cards=[
    definition(
        defbox('A <strong>shell variable</strong> (<code>NAME=value</code>, no spaces) exists only in the current shell. <code>export NAME</code> makes it an '
               '<strong>environment variable</strong>, copied into every child process (programs, scripts). Read with <code>$NAME</code> or <code>${NAME}</code>; list '
               'with <code>env</code>/<code>printenv</code>; remove with <code>unset</code>; set for one command with <code>NAME=value command</code>.',
               '<strong>PATH</strong> is a colon-separated list of directories searched, left to right, for commands. Start-up files: <code>~/.bashrc</code> '
               '(interactive non-login shells, usually sourced by login too), <code>~/.profile</code>/<code>~/.bash_profile</code> (login), <code>/etc/profile</code>, '
               '<code>/etc/environment</code> (system-wide).'),
        tags('environment variables', 'export', 'PATH', '.bashrc', 'JAVA_HOME', 'source'),
    ),
    analogy('Shell variables are <strong>notes on your own desk</strong>; exported variables are notes <strong>photocopied into the folder of every task you hand '
            'out</strong>. PATH is the <strong>list of cupboards</strong> checked, in order, when someone asks for a tool by name.'),
    env_anim(),
    real_world(
        scenario('Hadoop/Spark environment',
                 p('<code>export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64</code>, <code>export HADOOP_HOME=/opt/hadoop</code>, '
                   '<code>export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin</code> in <code>~/.bashrc</code>; "hdfs: command not found" almost always means PATH '
                   'was not updated or the file was not sourced.')),
    ),
    example(
        shrun("""
            BATCH=aug26
            bash -c 'echo "child sees: [$BATCH]"'
            export BATCH
            bash -c 'echo "child sees: [$BATCH]"'
            CENTRE=Juhu bash -c 'echo "one command: $CENTRE"'; echo "after: [$CENTRE]"
            echo "$PATH" | tr ':' '\\n'
            mkdir -p ~/bin; printf '#!/bin/bash\\necho "hello from my tool"\\n' > ~/bin/mytool; chmod +x ~/bin/mytool
            mytool
            export PATH="$HOME/bin:$PATH"; mytool; type mytool
            printenv HOME USER | head -n 2
            echo 'export DATA_DIR=$HOME/cdac/data' >> ~/.bashrc
            source ~/.bashrc; echo "script sees: [$DATA_DIR]"
            head -n 9 ~/.bashrc | tail -n 4
            bash -ic 'echo "interactive shell sees: [$DATA_DIR]"' 2>/dev/null
        """, files=FILES),
        title='Example: Shell vs Environment Variables, PATH, .bashrc'),
    steps(
        ('Set', '<code>export NAME=value</code> (quote values with spaces).'),
        ('Extend PATH', '<code>export PATH="$HOME/bin:$PATH"</code>; never overwrite it completely.'),
        ('Make permanent', 'Append to <code>~/.bashrc</code>.'),
        ('Apply now', '<code>source ~/.bashrc</code> (or open a new terminal).'),
        ('Check', '<code>echo $NAME</code>, <code>which tool</code>, <code>env | grep NAME</code>.'),
        title='Steps to Configure Your Environment'),
    crossq(
        ('Why does a script not change my shell\'s directory or variables?', 'A script runs in a child process; changes die with it. Use source script.sh (or . script.sh) to run it in the current shell.'),
        ('Why did source ~/.bashrc set nothing inside the script?', 'Ubuntu\'s default ~/.bashrc starts with "If not running interactively, don\'t do anything" and returns immediately. Put variables needed by scripts and cron in the script itself, ~/.profile or /etc/environment.'),
        ('Why are spaces around = an error?', 'NAME = value is parsed as running a command called NAME with arguments "=" and "value".'),
        ('What happens if PATH is set to only $HOME/bin?', 'ls, grep etc. become "command not found"; restore with export PATH=/usr/local/bin:/usr/bin:/bin.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What is the difference between single and double quotes? Explain command substitution, globbing and brace expansion.', 'Quoting & Expansions', minutes=8, cards=[
    definition(
        defbox('<strong>Single quotes</strong> keep everything literal. <strong>Double quotes</strong> allow <code>$var</code>, <code>$(command)</code> and '
               '<code>$((arithmetic))</code> but prevent word splitting and globbing. <strong>Unquoted</strong> text undergoes all expansions.',
               'Expansions (in order): brace <code>{a,b}</code>, <code>{1..5}</code> → tilde <code>~</code> → parameter <code>$var</code>, command '
               '<code>$(cmd)</code>, arithmetic <code>$((…))</code> → <strong>word splitting</strong> on spaces → <strong>globbing</strong> '
               '(<code>*</code>, <code>?</code>, <code>[abc]</code>) by the shell, before the command runs. Always write <code>"$var"</code> unless you want splitting.'),
        tags('quoting', 'command substitution', 'globbing', 'brace expansion', 'word splitting'),
    ),
    analogy('Single quotes are a <strong>sealed envelope</strong>: delivered exactly as written. Double quotes are an <strong>open envelope</strong>: the '
            'postman fills in names ($var) but keeps the letter in one piece. No quotes: the postman may also <strong>cut the letter into pieces</strong> at every space.'),
    quote_anim(),
    real_world(
        scenario('The space-in-filename bug',
                 p('A cleanup script did <code>rm $f</code> for each uploaded file; a file called "final marks.csv" made it try to delete "final" and "marks.csv" '
                   '(a different file!). Quoting <code>"$f"</code> fixed it; ShellCheck flags exactly this mistake.')),
    ),
    example(
        shrun("""
            name=Vineeta
            echo 'Hello $name' "Hello $name"
            echo "Today is $(date +%A), 7 x 6 = $((7 * 6))"
            echo report_{sql,spark,ml}.csv
            echo {2401..2405}
            ls *.csv
            echo '*.csv' "*.csv"
            touch 'my marks.csv' marks_2026.csv
            f='my marks.csv'
            ls -l $f
            ls -l "$f"
            ls marks_20[0-9][0-9].csv
            printf '[%s]\\n' $f
            printf '[%s]\\n' "$f"
        """, files=COMMON),
        title='Example: Quotes, Substitution, Braces, Globs and Word Splitting'),
    steps(
        ('Default to double quotes', 'Around every variable and command substitution.'),
        ('Literal text', 'Single quotes (regexes, awk/sed programs).'),
        ('Generate names', 'Brace expansion <code>{a,b}</code>, <code>{1..10}</code>.'),
        ('Match files', 'Globs, but check there is a match (nullglob in scripts).'),
        ('Lint', 'Run <code>shellcheck script.sh</code>.'),
        title='Steps to Avoid Quoting Bugs'),
    crossq(
        ('$(cmd) vs backticks?', 'Same result; $(…) nests cleanly and is easier to read, so it is preferred.'),
        ('Who expands *.csv: the shell or ls?', 'The shell; ls receives the list of matching names. If nothing matches, bash passes the literal *.csv (unless nullglob/failglob).'),
        ('How do you print a literal $ inside double quotes?', 'Escape it: "\\$HOME", or use single quotes.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What is the difference between a hard link and a soft (symbolic) link? What is an inode?', 'Hard vs Soft Links', minutes=7, cards=[
    definition(
        defbox('An <strong>inode</strong> stores a file\'s metadata (type, permissions, owner, size, timestamps, data block pointers), everything except its name. '
               'A directory entry maps a <strong>name to an inode</strong>.',
               'A <strong>hard link</strong> (<code>ln target name</code>) is another name for the same inode; data is freed only when the last name is removed. '
               'Hard links cannot cross filesystems or point to directories. A <strong>symbolic (soft) link</strong> (<code>ln -s target name</code>) is a separate '
               'small file containing a path; it can point anywhere (directories, other filesystems) and breaks ("dangling") if the target is removed.'),
        tags('inode', 'hard link', 'symbolic link', 'ln -s', 'ls -i'),
    ),
    analogy('A hard link is a <strong>second name plate on the same house</strong>: remove one plate, the house is still there. A symlink is a <strong>signboard '
            'pointing to the house\'s address</strong>: if the house is demolished, the sign points to nothing.'),
    links_anim(),
    real_world(
        scenario('Switching software versions',
                 p('<code>/opt/spark → /opt/spark-3.5.1</code> is a symlink; SPARK_HOME=/opt/spark never changes. Upgrading means unpacking 3.5.2 and repointing the '
                   'link (<code>ln -sfn /opt/spark-3.5.2 /opt/spark</code>), with instant rollback by pointing it back.')),
    ),
    example(
        shrun("""
            echo 'roll,marks' > marks_v1.csv
            ln marks_v1.csv hard.csv
            ln -s marks_v1.csv soft.csv
            ls -li marks_v1.csv hard.csv soft.csv
            rm marks_v1.csv
            cat hard.csv
            cat soft.csv
            ls -l soft.csv
            mkdir spark-3.5.1 spark-3.5.2; ln -s spark-3.5.1 spark; readlink spark
            ln -sfn spark-3.5.2 spark; readlink spark
            ln spark-3.5.1 dirlink
        """),
        title='Example: Inodes, Link Counts and a Dangling Symlink'),
    steps(
        ('Inspect', '<code>ls -li</code> shows inode numbers and link counts.'),
        ('Alias a file within one filesystem', '<code>ln</code> (rarely needed).'),
        ('Point to files/dirs anywhere', '<code>ln -s target linkname</code>.'),
        ('Repoint safely', '<code>ln -sfn new linkname</code>.'),
        ('Find broken links', '<code>find . -xtype l</code>.'),
        title='Steps to Use Links'),
    crossq(
        ('Why is the link count of a new directory 2?', 'Its name in the parent plus its own "." entry; each subdirectory adds one more through its "..".'),
        ('Does deleting a symlink delete the target?', 'No, rm on the link removes only the link file.'),
        ('Can you run out of inodes with free disk space?', 'Yes, millions of tiny files can exhaust inodes; df -i shows inode usage.'),
    ),
]),
])
