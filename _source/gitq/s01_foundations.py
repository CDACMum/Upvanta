from build import *
from gitq.anims import *
from gitq.runner import gitrun, sh

SETUP = note('Every example runs for real in an empty folder <code>~/cdac</code> on Ubuntu 24.04 with git 2.43, as user <em>student</em> with '
             '<code>user.name = Asha Patil</code>, <code>user.email = asha@cdac.example</code> and <code>init.defaultBranch = main</code> configured. '
             'Commit times are simulated (each git command is one minute later, from 14 Oct 2026 09:00), which is why the hashes you see are reproducible; '
             'on your machine the hashes will differ but everything else will match.', 'How these examples ran')

SECTION = dict(level='beginner', title='Git Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is version control, and why is Git called a distributed version control system?', 'What Git Is', minutes=7, cards=[
    definition(
        defbox('A <strong>version control system</strong> records changes to files over time so you can see who changed what and why, go back to any earlier '
               'state, and let many people work on the same project in parallel. <strong>Git</strong> stores the project as a series of <strong>snapshots</strong> '
               '(commits) of the whole tree, each identified by a SHA hash of its content, so history cannot be altered silently.',
               'Git is <strong>distributed</strong>: every clone is a full repository with the complete history. Committing, branching, viewing history and '
               'diffing work offline; collaboration happens by exchanging commits with <strong>remotes</strong> (GitHub, GitLab, a server). Centralised '
               'systems (SVN) keep history only on the server. GitHub/GitLab are hosting services built around Git, not Git itself.'),
        tags('version control', 'snapshot', 'commit', 'SHA hash', 'distributed', 'clone', 'remote', 'GitHub vs Git'),
    ),
    analogy('Git is a <strong>save-game system for your project</strong>: every commit is a save point you can return to, with a note saying what changed. '
            'And every player has the full set of save files on their own console, not just the server.'),
    vc_anim(),
    real_world(
        scenario('Course material for three centres',
                 p('The PG-DBDA lab manuals are edited by faculty at Kharghar, Juhu and Pune. With Git each faculty member has the full history locally, works '
                   'offline, and pushes changes to a shared repository; any page can be traced to the commit and person that changed it, and a bad edit can be '
                   'reverted in seconds.')),
    ),
    example(
        SETUP,
        gitrun("""
            git --version
            git init lab-manual
            cd lab-manual
            ls -a
            ls .git
            echo "# PG-DBDA Lab Manual" > README.md
            git add README.md
            git commit -m "Start the lab manual"
            git log --oneline
            du -sh .git
        """),
        title='Example: Create a Repository and Look Inside .git'),
    steps(
        ('Install and check', '<code>git --version</code>.'),
        ('Set your identity once', '<code>git config --global user.name / user.email</code>.'),
        ('Create or copy a repository', '<code>git init</code> for a new project, <code>git clone URL</code> for an existing one.'),
        ('Work and commit', 'Edit, <code>git add</code>, <code>git commit -m "..."</code>.'),
        ('Share', 'Connect a remote and <code>git push</code> / <code>git pull</code>.'),
        title='Steps to Start with Git'),
    crossq(
        ('Git vs GitHub?', 'Git is the version control tool that runs on your machine; GitHub is a hosting service that stores Git repositories and adds pull requests, issues and CI.'),
        ('What does the .git folder contain?', 'The whole repository: objects (snapshots), refs (branches and tags), HEAD, config and the index. Deleting it turns the folder back into plain files.'),
        ('Why snapshots rather than diffs?', 'Each commit points to a full tree; unchanged files are shared by reference, so snapshots stay small while making checkout, branching and comparison fast.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain the working directory, staging area (index) and repository. How do git status, git add and git commit move changes between them?', 'The Three Areas', minutes=8, cards=[
    definition(
        defbox('Git has three places for your changes: the <strong>working directory</strong> (the files you edit), the <strong>staging area / index</strong> '
               '(the exact content of the next commit, built with <code>git add</code>) and the <strong>repository</strong> (<code>.git</code>, the committed '
               'history, written by <code>git commit</code>).',
               '<code>git status</code> reports files as <strong>untracked</strong> (new, never added), <strong>modified</strong> (changed but not staged) or '
               '<strong>staged</strong> ("Changes to be committed"). Staging lets you commit only part of your work (<code>git add file</code>, '
               '<code>git add -p</code>). <code>git commit -a</code> stages tracked modified files automatically but never adds untracked ones.'),
        tags('working directory', 'staging area', 'index', 'git status', 'git add', 'git commit', 'untracked'),
    ),
    analogy('The working directory is your <strong>desk</strong>, the staging area is the <strong>parcel box</strong> you are packing, and a commit '
            '<strong>seals and posts the box</strong> with a label. You can put only some things from the desk into the box.'),
    areas_anim(),
    real_world(
        scenario('Two unrelated changes in one sitting',
                 p('While fixing a typo in the Hive lab, a faculty member also starts rewriting the Spark lab. Staging only the Hive file lets her commit the '
                   'typo fix on its own with a clear message, and keep the half-finished Spark work out of the commit.')),
    ),
    example(
        SETUP,
        gitrun("""
            git init -q labs && cd labs
            echo "SELECT * FROM students;" > hive_lab.sql
            echo "df = spark.read.csv('marks.csv')" > spark_lab.py
            git status --short
            git add hive_lab.sql
            git status
            git commit -q -m "Add Hive lab query"
            echo "-- fixed typo" >> hive_lab.sql
            git status --short
            git add hive_lab.sql spark_lab.py
            git status --short
            git commit -m "Fix Hive comment and add Spark lab"
            git status
        """),
        title='Example: Untracked → Staged → Committed, Partial Commits'),
    steps(
        ('Check the state', '<code>git status</code> (or <code>-s</code> for short).'),
        ('Stage what belongs together', '<code>git add file</code>, <code>git add -p</code> for parts of a file.'),
        ('Review the staged content', '<code>git diff --staged</code>.'),
        ('Commit with a clear message', '<code>git commit -m "Verb what and why"</code>.'),
        ('Repeat for the next logical change', 'Small, focused commits.'),
        title='Steps for the Basic Workflow'),
    crossq(
        ('What do ?? , A and M mean in git status -s?', '?? = untracked, A = new file staged, M in the first column = modified and staged, M in the second column = modified but not staged.'),
        ('Why have a staging area at all?', 'It lets you build a commit deliberately: commit related changes together and leave unrelated or unfinished work out.'),
        ('Does git commit -a add new files?', 'No. It stages modifications and deletions of tracked files only; new files still need git add.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('How do you configure Git? Explain system, global and local config, and how clone and init differ.', 'Configuration, init & clone', minutes=7, cards=[
    definition(
        defbox('<code>git config</code> reads and writes settings at three levels: <strong>system</strong> (<code>/etc/gitconfig</code>, all users), '
               '<strong>global</strong> (<code>~/.gitconfig</code>, your user) and <strong>local</strong> (<code>.git/config</code>, one repository). The more '
               'specific level wins, so a repository can use your work email while others use your personal one. <code>git config --list --show-origin</code> '
               'shows every setting and where it comes from.',
               'Essential settings: <code>user.name</code>, <code>user.email</code>, <code>init.defaultBranch</code>, <code>core.editor</code>, '
               '<code>pull.rebase</code>, aliases (<code>alias.lg</code>). <code>git init</code> creates a new empty repository; <code>git clone URL</code> copies '
               'an existing one with all history, sets up the remote <code>origin</code> and checks out the default branch.'),
        tags('git config', '--global', '--local', '--show-origin', 'user.email', 'alias', 'git init', 'git clone'),
    ),
    analogy('Config levels are like <strong>rules at a hostel</strong>: the university rules (system), your own habits (global) and the special rules of one '
            'room (local). The room rule wins inside that room.'),
    config_anim(),
    real_world(
        scenario('Personal and institutional accounts',
                 p('A faculty member uses her personal email globally but must commit to the C-DAC course repository with her institutional address. A local '
                   '<code>user.email</code> in that one repository does it, and <code>--show-origin</code> proves which setting is in effect.')),
    ),
    example(
        SETUP,
        gitrun("""
            git config --global user.name
            git config --global alias.lg "log --oneline --graph --all"
            git init -q course && cd course
            git config user.email "asha.patil@cdac.in"
            git config user.email
            git config --list --show-origin | grep -E "user|alias|defaultBranch"
            echo "notes" > n.txt && git add n.txt && git commit -q -m "Notes"
            git log -1 --format='%an <%ae>'
            cd ..
            git clone -q course course-copy
            cd course-copy
            git remote -v
            git lg
        """),
        title='Example: Global vs Local Email, an Alias, and Cloning'),
    steps(
        ('Set identity globally', '<code>git config --global user.name "…"</code> and <code>user.email</code>.'),
        ('Override per repository', '<code>git config user.email "…"</code> inside the repo.'),
        ('Check effective values', '<code>git config --list --show-origin</code>.'),
        ('Add helpful aliases', '<code>git config --global alias.lg "log --oneline --graph --all"</code>.'),
        ('Start a project', '<code>git init</code> (new) or <code>git clone URL</code> (existing).'),
        title='Steps to Configure Git'),
    crossq(
        ('Which wins: local or global?', 'Local (repository) settings override global, which override system.'),
        ('What does clone set up besides copying files?', 'The full history, remote-tracking branches (origin/main), the remote named origin and a local branch tracking the default branch.'),
        ('Why do commits show the wrong email?', 'The email is taken at commit time from the effective config; fix the config, then amend or rewrite the affected commits if needed.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('How do you explore history? Explain git log options, git show and good commit messages.', 'Viewing History', minutes=8, cards=[
    definition(
        defbox('<code>git log</code> lists commits from newest to oldest. Useful options: <code>--oneline</code>, <code>--graph --all</code> (branch structure), '
               '<code>-n 5</code>, <code>--stat</code> (files changed), <code>-p</code> (patches), <code>--author</code>, <code>--since/--until</code>, '
               '<code>--grep</code> (message text), <code>-- path</code> (history of one file), <code>--format</code> for custom output. <code>git show '
               'COMMIT</code> displays one commit\'s metadata and diff; <code>git show COMMIT:path</code> prints a file as it was.',
               'Good commit messages make history useful: a short imperative summary line (≤ 50–72 chars, "Add marks validation", not "changes"), a blank line, '
               'then the <em>why</em> in the body. Commit one logical change at a time.'),
        tags('git log', '--oneline', '--graph', '--stat', '--grep', 'git show', 'commit message'),
    ),
    analogy('git log is the <strong>project diary</strong>; good commit messages are diary entries that say "why", not just "worked on stuff today". Six '
            'months later, they are the only explanation anyone has.'),
    log_anim(),
    real_world(
        scenario('"When did the pass mark change?"',
                 p('An auditor asks when and why the pass mark in the grading script changed from 40 to 50. <code>git log -S "PASS_MARK = 50" -p -- grade.py</code> '
                   'finds the exact commit, its author, date and the message explaining the academic council decision.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q grading && cd grading
            !printf 'PASS_MARK = 40\\n' > grade.py && git add . && git commit -q -m "Add grading script with pass mark 40"
            !printf '# Grading rules\\n' > RULES.md && git add . && git commit -q -m "Document grading rules"
            !sed -i 's/40/50/' grade.py && git commit -q -am "Raise pass mark to 50" -m "Academic council decision of Oct 2026 for PG-DBDA."
            !echo "def grade(m): return 'P' if m >= PASS_MARK else 'F'" >> grade.py && git commit -q -am "Add grade function"
            !cd ..
            cd grading
            git log --oneline
            git log --stat -n 1
            git log --format='%h | %an | %ad | %s' --date=format:'%d %b %H:%M'
            git log -S "PASS_MARK = 50" --oneline -- grade.py
            git show --no-patch --format=%B HEAD~1
            git show HEAD~2:grade.py
        """),
        title='Example: Several Views of the Same History'),
    steps(
        ('Get an overview', '<code>git log --oneline --graph --all</code>.'),
        ('Filter', '<code>--author</code>, <code>--since</code>, <code>--grep</code>, <code>-- path</code>.'),
        ('Search code changes', '<code>git log -S "text"</code> (pickaxe) or <code>-G regex</code>.'),
        ('Inspect one commit', '<code>git show SHA</code>, <code>git show SHA:file</code>.'),
        ('Write messages for the reader', 'Imperative summary + why in the body.'),
        title='Steps to Explore History'),
    crossq(
        ('What does HEAD~2 mean?', 'Two commits before HEAD following first parents; HEAD^2 instead means the second parent of a merge commit.'),
        ('git log -S vs --grep?', '-S searches the code changes (commits that add or remove the string); --grep searches commit messages.'),
        ('Why imperative mood?', 'It reads as what the commit does when applied ("Add validation"), matching Git\'s own messages like "Merge branch".'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('How does Git store data internally? Explain blobs, trees, commits and SHA hashes.', 'Git Objects', minutes=9, cards=[
    definition(
        defbox('Git is a <strong>content-addressable store</strong>. Every object is named by the SHA-1 hash of its content: a <strong>blob</strong> stores file '
               'content (no name), a <strong>tree</strong> stores a directory listing (names, modes, and the hashes of blobs and sub-trees), and a '
               '<strong>commit</strong> stores a tree hash, parent commit hash(es), author, committer and message. Tags are objects too.',
               'Consequences: identical content is stored once; changing one byte changes the blob hash, which changes the tree hash and the commit hash, so '
               'history is tamper-evident; a branch is just a file containing a commit hash. Inspect with <code>git cat-file -t / -p</code> and '
               '<code>git hash-object</code>.'),
        tags('blob', 'tree', 'commit object', 'SHA-1', 'content-addressable', 'cat-file', 'hash-object'),
    ),
    analogy('Git objects are <strong>sealed envelopes labelled with a fingerprint of their contents</strong>. A commit envelope holds the fingerprint of the '
            'folder envelope, which holds the fingerprints of the file envelopes. Alter any page and every fingerprint above it changes.'),
    objects_anim(),
    real_world(
        scenario('Why the same file is not stored twice',
                 p('Thirty lab folders contain the same 2 MB sample dataset. Git stores one blob for it and thirty tree entries pointing to that blob, so the '
                   'repository stays small; and anyone can verify that the dataset in a given commit is byte-for-byte the one originally committed.')),
    ),
    example(
        SETUP,
        gitrun("""
            git init -q store && cd store
            echo "student_id,score" > marks.csv
            git hash-object marks.csv
            mkdir lab1 lab2 && cp marks.csv lab1/ && cp marks.csv lab2/
            git add . && git commit -q -m "Add marks in three places"
            git cat-file -t HEAD
            git cat-file -p HEAD
            git cat-file -p HEAD^{tree}
            git cat-file -p HEAD:lab1
            git count-objects
            echo "student_id,score,grade" > lab2/marks.csv
            git commit -q -am "Change lab2 only"
            git cat-file -p HEAD^{tree}
        """),
        title='Example: Hash a File, Read a Commit, a Tree and a Sub-tree'),
    steps(
        ('Hash content', '<code>git hash-object file</code>.'),
        ('Read a commit', '<code>git cat-file -p HEAD</code>: tree, parent, author, message.'),
        ('Walk the tree', '<code>git cat-file -p HEAD^{tree}</code>, then sub-trees.'),
        ('See deduplication', 'Same content → same blob hash.'),
        ('Count objects', '<code>git count-objects -v</code>.'),
        title='Steps to Inspect Git Objects'),
    crossq(
        ('Why do three copies of the file produce one blob?', 'The blob hash depends only on content; identical content gives the identical hash, so it is stored once and referenced three times.'),
        ('Why does count-objects report only 4 objects for three files in three folders?', 'One blob (the shared content), one tree shared by lab1 and lab2 (identical listings hash the same), the root tree and the commit.'),
        ('Where are file names stored?', 'In tree objects, next to the blob hash and file mode; blobs contain only content.'),
        ('Why does changing one file change the commit hash?', 'The blob changes, so its tree changes, so the root tree changes, so the commit (which records the root tree hash) changes.'),
    ),
]),
])
