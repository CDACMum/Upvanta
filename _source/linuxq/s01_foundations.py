from build import *
from linuxq.anims import *
from linuxq.runner import shrun, sh, script_file
from linuxq.data import COMMON, STUDENTS, MARKS, APP_LOG, ACCESS_LOG

RUN_NOTE = note('Every Terminal box on this page is a real transcript: the commands were executed while the page was built, on '
                '<strong>Ubuntu 24.04 with bash 5.2</strong>, as an ordinary user called <code>student</code> in the folder '
                '<code>~/cdac</code>, which holds small sample files (<code>students.csv</code>, <code>marks.csv</code>, logs). '
                'Lines starting with <code>$</code> are what was typed; <code>&gt;</code> marks continuation lines. Dates and sizes are what the system printed.',
                'How the examples were run')

SECTION = dict(level='beginner', title='Linux Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is Linux? What are the kernel, shell and distribution? Why is Linux used for big data?', 'What is Linux', minutes=7, cards=[
    definition(
        defbox('<strong>Linux</strong> is an open-source, Unix-like operating system. Strictly, Linux is the <strong>kernel</strong>: the core that manages '
               'processes, memory, files, devices and networking. A <strong>shell</strong> (bash, zsh) is the command interpreter users type into; together with '
               'GNU tools it forms the user environment. A <strong>distribution</strong> (Ubuntu, RHEL, Rocky, Debian, Amazon Linux) packages the kernel, tools, '
               'a package manager and defaults.',
               'Big data runs on Linux because servers and clusters run Linux: it is free, stable, scriptable, multi-user, secure, and Hadoop, Spark, Kafka, '
               'Hive and cloud VMs are built and tested on it.'),
        tags('Linux', 'kernel', 'shell', 'bash', 'distribution', 'Ubuntu'),
    ),
    analogy('The kernel is a building\'s <strong>electricity, plumbing and lifts</strong>; the shell is the <strong>reception desk</strong> where you ask for '
            'things; a distribution is a <strong>furnished building</strong> from a particular builder: same foundations, different fittings.'),
    layers_anim(),
    real_world(
        scenario('A PG-DBDA lab day',
                 p('You SSH into a lab server, start HDFS and YARN with shell scripts, submit Spark jobs from the terminal, read logs with <code>tail</code> and '
                   '<code>grep</code>, and schedule a nightly ingest with cron. Interviews for data-engineering roles always include Linux questions for this reason.')),
    ),
    example(
        RUN_NOTE,
        shrun("""
            uname -s -r
            grep PRETTY_NAME /etc/os-release
            echo $SHELL; bash --version | head -1
            whoami; id
            nproc; free -h | head -2
        """),
        title='Example: What Am I Running On?'),
    steps(
        ('Get a Linux environment', 'A VM (VirtualBox), WSL on Windows, a cloud VM, or the lab server.'),
        ('Open a terminal', 'Or connect with <code>ssh user@host</code>.'),
        ('Identify the system', '<code>uname -a</code>, <code>cat /etc/os-release</code>.'),
        ('Learn the basics', 'Navigation, files, permissions, text tools, processes.'),
        ('Automate', 'Turn repeated command sequences into shell scripts.'),
        title='Steps to Get Started'),
    crossq(
        ('Linux vs Unix?', 'Unix is the original OS family (AT&amp;T, 1970s) and a trademark/specification; Linux is an independent Unix-like kernel that follows similar design and POSIX standards.'),
        ('What is a shell vs a terminal?', 'The terminal is the window/program that shows text; the shell (bash) is the program inside it that reads and runs commands.'),
        ('Ubuntu vs RHEL family?', 'Ubuntu/Debian use .deb packages and apt; RHEL/Rocky/CentOS use .rpm packages and dnf/yum. Commands and concepts are otherwise mostly the same.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain the Linux filesystem hierarchy. What is the difference between absolute and relative paths?', 'Filesystem Hierarchy & Paths', minutes=7, cards=[
    definition(
        defbox('Linux has a <strong>single directory tree</strong> starting at <code>/</code> (root). Standard locations (FHS): <code>/home</code> users\' files, '
               '<code>/root</code> root\'s home, <code>/etc</code> configuration, <code>/var</code> variable data (<code>/var/log</code> logs), <code>/tmp</code> '
               'temporary files, <code>/usr/bin</code> programs, <code>/opt</code> optional software, <code>/dev</code> devices, <code>/proc</code> kernel/process '
               'information, <code>/mnt</code> and <code>/media</code> mount points.',
               'An <strong>absolute path</strong> starts with <code>/</code> and is the same from anywhere. A <strong>relative path</strong> is interpreted from the '
               'current directory. Shortcuts: <code>~</code> home, <code>.</code> current, <code>..</code> parent, <code>-</code> (in cd) previous directory.'),
        tags('FHS', '/etc', '/var/log', 'absolute path', 'relative path', 'pwd'),
    ),
    analogy('An absolute path is a <strong>full postal address</strong> ("India, Maharashtra, Navi Mumbai, Kharghar, C-DAC"); a relative path is directions '
            '<strong>from where you stand</strong> ("next building on the left").'),
    fhs_anim(),
    real_world(
        scenario('Where things live on a Hadoop node',
                 p('Hadoop unpacked in <code>/opt/hadoop</code>, its configuration in <code>/opt/hadoop/etc/hadoop</code> (or <code>/etc/hadoop/conf</code>), logs in '
                   '<code>/var/log/hadoop</code> or <code>$HADOOP_HOME/logs</code>, data directories on mounted disks like <code>/data1</code>, and your scripts in '
                   '<code>/home/student</code>. Knowing the layout tells you where to look when something breaks.')),
    ),
    example(
        shrun("""
            pwd
            ls -d /home /etc /var/log /tmp /usr/bin /opt /proc /root /dev
            cd ..; pwd
            cd cdac; pwd
            cd /etc && pwd && cd - >/dev/null && pwd
            ls ~/cdac/students.csv ./students.csv ../cdac/students.csv
            realpath ../cdac/./students.csv
        """, files=COMMON),
        title='Example: Moving Around the Tree'),
    steps(
        ('Know where you are', '<code>pwd</code>.'),
        ('Go home', '<code>cd</code> or <code>cd ~</code>.'),
        ('Move', '<code>cd /absolute/path</code> or <code>cd relative/path</code>; <code>cd ..</code> up; <code>cd -</code> back.'),
        ('In scripts', 'Prefer absolute paths (or paths built from a known base), because the current directory may differ when cron runs the script.'),
        title='Steps to Navigate'),
    crossq(
        ('What is in /proc?', 'A virtual filesystem generated by the kernel: /proc/cpuinfo, /proc/meminfo, and a directory per running process (/proc/&lt;pid&gt;).'),
        ('Why does a script work from the terminal but fail in cron?', 'Often relative paths or a different PATH/working directory; use absolute paths and set PATH in the script.'),
        ('What is a mount point?', 'A directory where another filesystem (disk partition, NFS share, USB drive) is attached to the tree.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What are the basic commands to create, copy, move, rename and delete files and directories?', 'File & Directory Commands', minutes=7, cards=[
    definition(
        defbox('<code>ls</code> list (<code>-l</code> long, <code>-a</code> hidden, <code>-h</code> human sizes, <code>-t</code> by time, <code>-R</code> recursive); '
               '<code>mkdir</code> (<code>-p</code> parents); <code>touch</code> create empty file / update timestamp; <code>cp</code> copy (<code>-r</code> '
               'directories, <code>-p</code> keep attributes, <code>-i</code> confirm); <code>mv</code> move or rename; <code>rm</code> delete (<code>-r</code> '
               'recursive, <code>-f</code> force, <code>-i</code> confirm); <code>rmdir</code> remove an empty directory; <code>tree</code> show a directory tree.',
               'There is no recycle bin: <code>rm</code> is permanent.'),
        tags('ls', 'mkdir', 'cp', 'mv', 'rm', 'touch'),
    ),
    analogy('Working with folders in a filing cabinet: make a new folder (mkdir), photocopy a document (cp), move it to another drawer or relabel it (mv), and '
            'shred it (rm), and a shredder has no undo.'),
    fileops_anim(),
    real_world(
        scenario('Setting up a project workspace',
                 p('Every new batch project starts with <code>mkdir -p project/{data/raw,data/clean,scripts,logs}</code>, raw files copied in with <code>cp</code>, '
                   'processed outputs moved with <code>mv</code> into dated folders, and old logs removed. Doing it from the shell is repeatable and scriptable.')),
    ),
    example(
        shrun("""
            mkdir -p project/{data/raw,data/clean,scripts,logs}
            cp marks.csv project/data/raw/
            cp project/data/raw/marks.csv project/data/raw/marks_backup.csv
            mv project/data/raw/marks_backup.csv project/data/clean/marks_v1.csv
            touch project/logs/run.log
            tree project
            ls -lh project/data/raw
            rm project/logs/run.log
            rmdir project/logs
            rmdir project/data
            rm -r project/data
            ls project
        """, files=COMMON),
        title='Example: Build, Copy, Rename and Clean a Project Tree'),
    steps(
        ('Create the structure', '<code>mkdir -p</code> with brace expansion.'),
        ('Copy safely', '<code>cp -i</code> (or <code>-n</code> no-clobber) to avoid overwriting.'),
        ('Rename/move', '<code>mv old new</code>.'),
        ('Delete carefully', '<code>ls</code> the pattern first, then <code>rm</code>; use <code>-i</code> interactively.'),
        ('Check', '<code>ls -la</code> / <code>tree</code>.'),
        title='Steps for Safe File Management'),
    crossq(
        ('Why did rmdir project/data fail?', 'rmdir only removes empty directories; data still contained raw/ and clean/. rm -r removes recursively.'),
        ('How do you recover a file deleted with rm?', 'Normally you cannot (no recycle bin); restore from a backup or snapshot. That is why backups and version control matter.'),
        ('cp vs mv within the same filesystem?', 'mv just renames the directory entry (instant, same inode); cp duplicates the data.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('How do you view file contents? Explain cat, less, head, tail, tail -f and wc.', 'Viewing Files', minutes=6, cards=[
    definition(
        defbox('<code>cat</code> prints whole files (or concatenates several); <code>less</code> pages through large files (search with <code>/</code>, quit with '
               '<code>q</code>); <code>head -n N</code> / <code>tail -n N</code> show the first/last N lines; <code>tail -n +2</code> starts from line 2 (skip a header); '
               '<code>tail -f</code> follows a growing file; <code>wc -l</code> counts lines; <code>nl</code> numbers lines; <code>file</code> identifies the type; '
               '<code>stat</code> shows metadata.'),
        tags('cat', 'less', 'head', 'tail', 'tail -f', 'wc'),
    ),
    analogy('<code>head</code> reads the <strong>first page</strong> of a register, <code>tail</code> the <strong>last page</strong>, <code>less</code> lets you '
            '<strong>flip through</strong> it, and <code>tail -f</code> is <strong>standing next to the clerk</strong> as new entries are written.'),
    viewing_anim(),
    real_world(
        scenario('Watching a job',
                 p('While a nightly result-processing job runs, <code>tail -f /var/log/results/job.log</code> shows progress live; afterwards <code>grep ERROR</code> '
                   'finds failures and <code>wc -l marks.csv</code> confirms the expected number of records (header + students).')),
    ),
    example(
        shrun("""
            head -n 3 students.csv
            tail -n 2 marks.csv
            tail -n +2 marks.csv | head -n 3
            wc -l students.csv marks.csv
            nl -b a app.log | tail -n 3
            file students.csv
            stat -c '%n: %s bytes, owner %U' app.log
        """, files={**COMMON, 'app.log': APP_LOG}),
        title='Example: Headers, Tails, Counts and Metadata'),
    steps(
        ('Small file', '<code>cat</code>.'),
        ('Large file', '<code>less</code>, or <code>head</code>/<code>tail</code>.'),
        ('Skip a CSV header', '<code>tail -n +2</code>.'),
        ('Live logs', '<code>tail -f</code> (or <code>tail -F</code> if the log is rotated).'),
        ('Counting', '<code>wc -l</code>; remember the header line.'),
        title='Steps to Inspect a File'),
    crossq(
        ('tail -f vs tail -F?', '-F follows the file name, reopening it if the log is rotated or recreated; -f keeps following the original file descriptor.'),
        ('How do you view a gzip-compressed log?', '<code>zcat</code>, <code>zless</code>, <code>zgrep</code> without decompressing to disk.'),
        ('Why can wc -l be one less than you expect?', 'It counts newline characters; a last line without a trailing newline is not counted.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('How do you get help in Linux? What are man pages, aliases and command history?', 'Help, History & Aliases', minutes=6, cards=[
    definition(
        defbox('<code>man command</code> opens the manual; <code>command --help</code> prints a summary; <code>apropos keyword</code> searches manuals; '
               '<code>type</code> and <code>which</code> show whether a name is an alias, shell builtin, function or program (and where). <code>history</code> lists '
               'previous commands; <code>!!</code> repeats the last, <code>!n</code> runs number n, <strong>Ctrl+R</strong> searches. <code>alias name=\'command\'</code> '
               'creates shortcuts, made permanent in <code>~/.bashrc</code>.'),
        tags('man', '--help', 'type', 'which', 'history', 'alias'),
    ),
    analogy('man pages are the <strong>instruction manual</strong> in the box; history is your <strong>diary</strong> of what you did; an alias is a '
            '<strong>speed-dial</strong> button for a long number you call every day.'),
    help_anim(),
    real_world(
        scenario('Team shortcuts',
                 p('A data team keeps aliases like <code>alias hls=\'hdfs dfs -ls\'</code> and <code>alias sparklog=\'tail -f $SPARK_HOME/logs/*.out\'</code> in a shared '
                   '<code>.bashrc</code> snippet; new members find options in <code>man</code> rather than guessing.')),
    ),
    example(
        shrun("""
            ls --help | head -n 3
            type cd echo grep
            which grep awk
            alias ll='ls -la'
            type ll
            unalias ll
            help cd | head -n 2
        """),
        sh("""
            man ls            # full manual (q quits, /word searches)
            man 5 crontab     # section 5 = file formats
            apropos 'disk usage'
            man -k compress   # same as apropos
        """, title='Shell (man pages: not installed on this minimal server image)'),
        title='Example: Help, type/which and Aliases'),
    steps(
        ('Quick look', '<code>cmd --help | less</code>.'),
        ('Details', '<code>man cmd</code>; search inside with <code>/word</code>.'),
        ('Do not know the command?', '<code>apropos keyword</code>.'),
        ('Reuse', 'Ctrl+R to search history, <code>!!</code>, <code>sudo !!</code>.'),
        ('Make it permanent', 'Add aliases to <code>~/.bashrc</code>, then <code>source ~/.bashrc</code>.'),
        title='Steps to Help Yourself'),
    crossq(
        ('Why does "which cd" print nothing?', 'cd is a shell builtin, not a program on PATH; use type cd.'),
        ('Where is history stored?', 'In memory during the session and in ~/.bash_history when the shell exits (size set by HISTSIZE/HISTFILESIZE).'),
        ('Alias vs shell function?', 'An alias is a simple text substitution; a function can take arguments, use logic and is preferred for anything non-trivial.'),
    ),
]),
])
