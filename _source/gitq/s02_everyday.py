from build import *
from gitq.anims import *
from gitq.runner import gitrun, sh
from gitq.s01_foundations import SETUP

SECTION = dict(level='basic', title='Everyday Git', questions=[

# ------------------------------------------------------------------ 6
Q('How do you see what changed? Explain git diff, git diff --staged and comparing commits or branches.', 'git diff', minutes=7, cards=[
    definition(
        defbox('<code>git diff</code> compares the <strong>working directory with the index</strong> (unstaged changes). <code>git diff --staged</code> '
               '(alias <code>--cached</code>) compares the <strong>index with the last commit</strong> — exactly what the next commit will contain. '
               '<code>git diff HEAD</code> shows both together.',
               'Between commits: <code>git diff A B</code>, <code>git diff HEAD~2</code>, <code>git diff main..feature</code> (tips) and '
               '<code>git diff main...feature</code> (changes on feature since it branched). Useful flags: <code>--stat</code>, <code>--name-only</code>, '
               '<code>--word-diff</code>, <code>-- path</code>. Lines starting with <code>-</code> were removed, <code>+</code> added; <code>@@</code> hunks '
               'give line ranges.'),
        tags('git diff', '--staged', '--cached', 'HEAD', 'A..B', 'A...B', '--stat', '--word-diff'),
    ),
    analogy('git diff is a <strong>track-changes view</strong>: red for what you deleted, green for what you added. --staged shows the redlines of the parcel '
            'you are about to post, plain git diff shows what is still on your desk.'),
    diff_anim(),
    real_world(
        scenario('Reviewing before committing',
                 p('Before committing changes to the evaluation script, a faculty member runs <code>git diff --staged</code> and notices a debug '
                   '<code>print</code> she staged by accident — unstaging it takes one command and keeps the commit clean.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q eval && cd eval
            !printf 'def grade(m):\\n    return "P" if m >= 40 else "F"\\n' > grade.py && git add . && git commit -q -m "Add grade function"
            !cd ..
            cd eval
            sed -i 's/40/50/' grade.py
            git diff
            git add grade.py
            git diff
            git diff --staged --stat
            echo '    print("debug")' >> grade.py
            git diff HEAD --word-diff
            git commit -q -m "Raise pass mark to 50"
            git diff HEAD~1 HEAD --name-only
        """),
        title='Example: Unstaged vs Staged Changes, Word Diff, Comparing Commits'),
    steps(
        ('See unstaged changes', '<code>git diff</code>.'),
        ('See what will be committed', '<code>git diff --staged</code>.'),
        ('Summarise', '<code>--stat</code> or <code>--name-only</code>.'),
        ('Compare history', '<code>git diff A B</code>, <code>main...feature</code>.'),
        ('Narrow down', '<code>-- path</code>, <code>--word-diff</code> for prose.'),
        title='Steps to Inspect Changes'),
    crossq(
        ('Why does git diff show nothing after git add?', 'The working directory now matches the index; the change moved to the staged diff (git diff --staged).'),
        ('main..feature vs main...feature in git diff?', 'Two dots compare the two branch tips directly; three dots compare feature with the merge base, i.e. only what feature changed.'),
        ('How do you diff a file between two commits?', 'git diff A B -- path/to/file.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('What is .gitignore? How do patterns work, and how do you stop tracking a file that was already committed?', '.gitignore', minutes=7, cards=[
    definition(
        defbox('A <code>.gitignore</code> file lists patterns of files Git should not track: build output, virtual environments, logs, data dumps, secrets '
               '(<code>.env</code>), IDE folders. Patterns: <code>*.log</code> (any .log), <code>/data/</code> (folder at repository root), <code>build/</code> '
               '(any folder named build), <code>**/tmp</code> (any depth), <code>!keep.log</code> (negation: re-include). Commit the .gitignore so the team '
               'shares it; personal patterns go in <code>.git/info/exclude</code> or a global excludes file.',
               '.gitignore only affects <strong>untracked</strong> files. A file already committed stays tracked: remove it from the index with '
               '<code>git rm --cached file</code> (keeps your local copy) and commit. <code>git check-ignore -v path</code> shows which rule matches.'),
        tags('.gitignore', 'patterns', 'negation', 'git rm --cached', 'check-ignore', 'info/exclude'),
    ),
    analogy('.gitignore is a <strong>"do not pack" list</strong> taped to the parcel box: it stops new items going in, but anything already packed stays until '
            'you take it out.'),
    ignore_anim(),
    real_world(
        scenario('A data science project repository',
                 p('Students push Jupyter notebooks but not the 2 GB raw datasets, the <code>venv/</code> folder, <code>__pycache__</code> or the <code>.env</code> '
                   'file with their database password. One committed .gitignore at the root enforces this for the whole class.')),
    ),
    example(
        SETUP,
        gitrun("""
            git init -q project && cd project
            mkdir -p data venv __pycache__ logs
            touch data/raw.csv venv/pyvenv.cfg __pycache__/x.pyc logs/app.log logs/keep.log .env analysis.ipynb
            printf 'data/\\nvenv/\\n__pycache__/\\n*.log\\n!logs/keep.log\\n.env\\n' > .gitignore
            cat .gitignore
            git status --short --untracked-files=all
            git check-ignore -v logs/app.log .env
            git add . && git commit -q -m "Initial project"
            echo "DB_PASSWORD=secret" > config.ini
            git add config.ini && git commit -q -m "Add config"
            echo "config.ini" >> .gitignore
            git status --short
            git rm --cached config.ini
            git commit -q -am "Stop tracking config.ini"
            git ls-files
            ls
        """),
        title='Example: Ignore Patterns, Negation, check-ignore, Untracking a Committed File'),
    steps(
        ('Create .gitignore at the root', 'Start from a language template (Python, Java, Node).'),
        ('Add project-specific patterns', 'Data, outputs, secrets, IDE folders.'),
        ('Verify', '<code>git status --ignored</code>, <code>git check-ignore -v</code>.'),
        ('Untrack files already committed', '<code>git rm --cached file</code> + commit.'),
        ('Commit .gitignore', 'So the whole team shares the rules.'),
        title='Steps to Set Up .gitignore'),
    crossq(
        ('I added a file to .gitignore but Git still shows changes. Why?', 'It was already tracked; .gitignore only ignores untracked files. Use git rm --cached and commit.'),
        ('Does git rm --cached remove the secret from history?', 'No; earlier commits still contain it. Rotate the secret and, if needed, rewrite history (scenario section).'),
        ('Where do personal ignore rules go?', '.git/info/exclude for one repository, or a global excludes file (core.excludesFile) for all.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('How do you undo changes? Compare git restore, git reset (soft, mixed, hard) and git revert.', 'Undoing Changes', minutes=10, cards=[
    definition(
        defbox('<strong>Working directory</strong>: <code>git restore file</code> discards unstaged edits (irreversible). <strong>Index</strong>: '
               '<code>git restore --staged file</code> unstages but keeps the edit. <strong>Commits</strong>: <code>git reset</code> moves the current branch to '
               'another commit — <code>--soft</code> keeps changes staged, <code>--mixed</code> (default) keeps them unstaged, <code>--hard</code> discards them.',
               '<code>git revert COMMIT</code> creates a <strong>new commit</strong> that undoes an earlier one, leaving history intact — the safe choice for '
               'commits already pushed and shared. Use reset only on local, unpushed commits; rewriting shared history forces everyone else to repair their '
               'clones. Lost something with reset --hard? The reflog usually still has it.'),
        tags('git restore', 'restore --staged', 'reset --soft', 'reset --mixed', 'reset --hard', 'git revert', 'shared history'),
    ),
    analogy('reset is <strong>tearing pages out of your own notebook</strong> — fine before anyone has copied them. revert is <strong>writing a correction '
            'notice</strong> in a published newspaper: the original stays, and the correction cancels it.'),
    undo_anim(),
    real_world(
        scenario('Two different mistakes',
                 p('Locally, a student commits the wrong file twice: <code>git reset --soft HEAD~2</code> lets him redo the commits properly. On the shared main '
                   'branch, a merged commit broke the result-publishing script: the team lead runs <code>git revert</code>, pushes, and nobody\'s history is '
                   'disturbed.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q undo && cd undo
            !for i in 1 2 3; do echo "line $i" >> notes.txt; git add .; git commit -q -m "Add line $i"; done
            !cd ..
            cd undo
            git log --oneline
            echo "oops" >> notes.txt && git restore notes.txt && tail -1 notes.txt
            echo "line 4" >> notes.txt && git add notes.txt && git restore --staged notes.txt && git status --short
            git checkout -q -- notes.txt
            git revert --no-edit HEAD
            git log --oneline
            cat notes.txt
            git reset --soft HEAD~1 && git status --short && git log --oneline -1
            git reset HEAD~1 && git status --short && git log --oneline -1
            git reset --hard HEAD && git status --short
            cat notes.txt
        """),
        title='Example: restore, restore --staged, reset --soft / --mixed / --hard, revert'),
    steps(
        ('Unstaged edit to drop', '<code>git restore file</code>.'),
        ('Staged by mistake', '<code>git restore --staged file</code>.'),
        ('Redo local commits', '<code>git reset --soft HEAD~n</code> (keep staged) or <code>--mixed</code>.'),
        ('Throw away local commits and changes', '<code>git reset --hard REF</code> (careful).'),
        ('Undo a pushed commit', '<code>git revert SHA</code> and push.'),
        title='Steps to Choose the Right Undo'),
    crossq(
        ('Why is revert safer than reset on a shared branch?', 'Revert adds a commit, so others can pull normally; reset rewrites history and makes everyone else\'s copies diverge.'),
        ('Can you recover after reset --hard?', 'Committed work: yes, via git reflog. Uncommitted changes that were never staged: no.'),
        ('In the example, why is git status empty after the mixed reset?', 'After the soft reset the index held "remove line 3"; the mixed reset also undid "Add line 3". The working file (lines 1-2) now equals the new HEAD, so there is nothing left to show.'),
        ('reset --soft vs --mixed?', 'Both move the branch; --soft keeps the undone changes staged, --mixed leaves them in the working directory unstaged.'),
        ('What does git checkout -- file do today?', 'The same as git restore file; restore and switch were added in Git 2.23 to split checkout\'s many jobs.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('How do you fix the last commit with --amend, and what makes a good commit?', 'Amending Commits', minutes=7, cards=[
    definition(
        defbox('<code>git commit --amend</code> replaces the last commit with a new one: it takes the current index (so you can add a forgotten file) and lets '
               'you change the message (<code>-m</code>) or keep it (<code>--no-edit</code>). Because the commit hash changes, amend <strong>rewrites '
               'history</strong>: fine for local commits, but an amended commit that was already pushed needs <code>push --force-with-lease</code> and '
               'coordination.',
               'A good commit is <strong>atomic</strong> (one logical change that builds and passes tests), has a clear message, and does not mix formatting '
               'with behaviour changes. <code>--author</code> fixes authorship; <code>--date</code> or <code>--reset-author</code> update metadata.'),
        tags('commit --amend', '--no-edit', 'rewrite history', 'atomic commits', 'force-with-lease', 'commit message'),
    ),
    analogy('Amend is <strong>reprinting the last page</strong> of a report before you hand it in. Once copies are distributed, you issue an erratum (a new '
            'commit) instead.'),
    amend_anim(),
    real_world(
        scenario('Forgot the test file',
                 p('A faculty member commits a new grading function but forgets its test file and misspells the message. One <code>git add</code> and '
                   '<code>git commit --amend -m ...</code> later, the history shows a single correct commit instead of "fix", "fix again".')),
    ),
    example(
        SETUP,
        gitrun("""
            git init -q amend && cd amend
            echo "def grade(m): ..." > grade.py
            echo "def test_grade(): ..." > test_grade.py
            git add grade.py && git commit -q -m "Add grde fucntion"
            git log --oneline --stat
            git add test_grade.py
            git commit -q --amend -m "Add grade function with tests"
            git log --oneline --stat
            git reflog -3
        """),
        title='Example: Add a Forgotten File and Fix the Message'),
    steps(
        ('Stage what is missing', '<code>git add forgotten_file</code>.'),
        ('Amend', '<code>git commit --amend -m "New message"</code> or <code>--no-edit</code>.'),
        ('Check', '<code>git log --stat -1</code>.'),
        ('If already pushed', 'Coordinate, then <code>git push --force-with-lease</code>.'),
        ('Prefer new commits on shared branches', 'Or fixup commits squashed before merging.'),
        title='Steps to Amend Safely'),
    crossq(
        ('Why does amend change the commit hash?', 'The commit\'s content (tree and/or message, timestamp) changes, and the hash is computed from the content.'),
        ('--force vs --force-with-lease?', '--force overwrites the remote branch blindly; --force-with-lease refuses if someone else pushed in the meantime.'),
        ('Where does the old commit go after amend?', 'It still exists and is listed in the reflog until garbage-collected, so an amend can be undone.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What is git stash and when do you use it?', 'git stash', minutes=7, cards=[
    definition(
        defbox('<code>git stash</code> (<code>push</code>) saves your uncommitted changes (staged and unstaged tracked files) onto a stack and cleans the working '
               'directory, so you can switch branches or pull. <code>git stash list</code> shows saved entries; <code>git stash pop</code> re-applies the latest '
               'and drops it; <code>git stash apply stash@{n}</code> re-applies without dropping; <code>git stash drop/clear</code> deletes.',
               'Options: <code>-m "message"</code> to label, <code>-u</code> to include untracked files, <code>-p</code> to stash parts, '
               '<code>git stash show -p</code> to inspect, <code>git stash branch name</code> to turn a stash into a branch. Stashes are local and easy to forget; '
               'for longer interruptions a work-in-progress commit on a branch is clearer.'),
        tags('git stash', 'stash pop', 'stash apply', 'stash list', '-u untracked', 'stash branch'),
    ),
    analogy('Stash is the <strong>drawer you sweep your desk into</strong> when someone needs the desk urgently. Take it all back out later; just do not leave '
            'too many unlabelled piles in the drawer.'),
    stash_anim(),
    real_world(
        scenario('An urgent fix in the middle of a feature',
                 p('Halfway through adding a new report, the coordinator is asked to fix a typo in the published results page right away. She stashes her work, '
                   'switches to main, fixes and commits the typo, comes back and pops the stash to continue exactly where she left off.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q site && cd site && echo "Results" > results.html && git add . && git commit -q -m "Add results page"
            !git switch -q -c feature/report && echo "<h1>Report</h1>" > report.html && git add . && git commit -q -m "Start report"
            !cd ..
            cd site
            echo "<p>chart</p>" >> report.html
            echo "draft" > notes.txt
            git status --short
            git stash push -u -m "report: chart section"
            git status --short
            git switch -q main
            sed -i 's/Results/Results 2026/' results.html && git commit -q -am "Fix results heading"
            git switch -q feature/report
            git stash list
            git stash show -p --include-untracked | head -12
            git stash pop
            git status --short
        """),
        title='Example: Stash Work (Including Untracked), Fix main, Come Back and Pop'),
    steps(
        ('Save current work', '<code>git stash push -u -m "label"</code>.'),
        ('Do the other task', 'Switch branch, fix, commit.'),
        ('Return', '<code>git switch your-branch</code>.'),
        ('Inspect and restore', '<code>git stash list</code>, <code>show -p</code>, <code>pop</code> or <code>apply</code>.'),
        ('Clean up', '<code>git stash drop</code>; avoid long-lived stashes.'),
        title='Steps to Use git stash'),
    crossq(
        ('pop vs apply?', 'pop applies and removes the entry (unless there is a conflict); apply keeps the entry in the list.'),
        ('Why were my new files not stashed?', 'By default stash ignores untracked files; use -u (or -a for ignored files too).'),
        ('What if stash pop conflicts?', 'Resolve the conflict like a merge; the stash entry is kept, so drop it manually after resolving.'),
    ),
]),
])
