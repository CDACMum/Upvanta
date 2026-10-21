from build import *
from gitq.anims import *
from gitq.runner import gitrun, sh
from gitq.s04_remotes import REMOTE_NOTE, team

T = 'Terminal (git 2.43)'

SECTION = dict(level='expert', title='Scenario-Based Questions', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: you made three commits on main that should have been on a feature branch. How do you move them?', 'Commits on the Wrong Branch', minutes=7, tag='Scenario', cards=[
    definition(
        defbox('If the commits are <strong>not pushed</strong>, the fix is two pointer moves: create a branch at the current commit (<code>git branch '
               'feature/x</code>) so the work is safe, then move main back to where it should be (<code>git reset --hard origin/main</code> or '
               '<code>HEAD~3</code>). Nothing is copied; the commits simply end up "on" the new branch.',
               'If they were <strong>already pushed</strong> to a shared main, do not rewrite it: revert them on main (or leave them) and continue on a branch. '
               'For commits that belong on a <em>different existing</em> branch, <code>git cherry-pick</code> them there and then reset or revert main.'),
        tags('wrong branch', 'git branch', 'git reset --hard', 'origin/main', 'cherry-pick', 'unpushed commits'),
    ),
    analogy('You wrote three pages in the wrong notebook. Because pages in Git are never torn out by a branch move, you just <strong>put a new bookmark</strong> '
            'on the last page (the feature branch) and <strong>move the main bookmark back</strong> three pages.'),
    wrongbranch_anim(),
    real_world(
        scenario('Monday morning on the project repo',
                 p('Ravi forgot to create a branch and made three commits for the attendance export directly on main. Before pushing, he creates '
                   'feature/attendance-export at HEAD, resets main to origin/main, pushes the feature branch and opens a pull request as the team requires.')),
    ),
    example(
        REMOTE_NOTE,
        gitrun(team("""
            cd asha
            for i in 1 2 3; do echo "step $i" >> export.py; git add export.py; git commit -q -m "Export: step $i"; done
            git status -sb
            git log --oneline --graph --all --decorate
            git branch feature/attendance-export
            git reset --hard -q origin/main
            git status -sb
            git log --oneline --graph --all --decorate
            git switch -q feature/attendance-export && ls
            git push -q -u origin feature/attendance-export && git branch -vv
        """), title=T),
        title='Example: Rescue Three Unpushed Commits onto a Feature Branch'),
    steps(
        ('Check whether the commits were pushed', 'git status -sb shows "ahead 3".'),
        ('Create the branch at the current commit', 'git branch feature/x.'),
        ('Move main back', 'git reset --hard origin/main (only if nothing uncommitted).'),
        ('Switch and continue', 'git switch feature/x; push -u and open a PR.'),
        ('If already pushed', 'Revert on main instead of resetting shared history.'),
        title='Steps to Move Commits to a New Branch'),
    crossq(
        ('Why create the branch before resetting?', 'The branch keeps a reference to the commits; reset alone would leave them reachable only through the reflog.'),
        ('What if there were uncommitted changes too?', 'reset --hard would discard them; stash first, or use git switch -c feature/x, which carries uncommitted changes along.'),
        ('Could you use git switch -c instead?', 'Yes: git switch -c feature/x then git branch -f main origin/main gives the same result without touching the working tree.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: a merge to main that broke the build has already been pushed. How do you undo it safely?', 'Reverting a Pushed Merge', minutes=8, tag='Scenario', cards=[
    definition(
        defbox('A pushed merge must not be removed with reset (others already have it). <code>git revert -m 1 &lt;merge&gt;</code> creates a new commit that '
               'undoes the changes the merge brought in, relative to <strong>parent 1</strong> (the mainline, the branch you merged into). History stays intact; '
               'everyone just pulls the revert.',
               'The catch: Git now considers the feature branch\'s commits <strong>already merged</strong>. Merging the branch again later brings in only new '
               'commits — the reverted ones stay missing. To re-introduce them, first <strong>revert the revert</strong>, then merge the fixes.'),
        tags('git revert -m 1', 'merge commit', 'mainline parent', 'revert the revert', 'pushed history', 'safe undo'),
    ),
    analogy('Reverting a merge is <strong>publishing a correction notice</strong> rather than recalling every printed newspaper. Later, to print the article '
            'again, you first have to withdraw the correction notice.'),
    revertmerge_anim(),
    real_world(
        scenario('Results portal down before a deadline',
                 p('The new grading module, merged on Friday evening, breaks the results page. The on-call student reverts the merge on main within minutes; '
                   'on Monday the team fixes the module, reverts the revert and merges the fix.')),
    ),
    example(
        REMOTE_NOTE,
        gitrun(team("""
            cd asha
            git switch -q -c feature/grading
            echo "def grade(m): return 'P' if m >= 50 else 'F'" > grading.py && git add . && git commit -q -m "Add grading module"
            echo "BROKEN = 1/0" >> grading.py && git commit -q -am "Wire grading into results"
            git switch -q main && git merge -q --no-ff -m "Merge feature/grading" feature/grading && git push -q
            git log --oneline --graph
            git revert -m 1 --no-edit HEAD
            git push -q && ls
            git switch -q feature/grading && sed -i '/BROKEN/d' grading.py && git commit -q -am "Fix grading wiring" && git switch -q main
            git merge -q --no-edit feature/grading
            git merge --abort
            git revert --no-edit HEAD
            git merge -q --no-edit feature/grading && ls && cat grading.py
            git log --oneline --graph
        """), title=T),
        title='Example: Revert a Pushed Merge, Then Revert the Revert to Bring the Fixed Feature Back'),
    steps(
        ('Identify the merge commit', 'git log --merges --oneline.'),
        ('Revert relative to the mainline', 'git revert -m 1 <merge>.'),
        ('Push the revert', 'Everyone pulls; no history rewrite.'),
        ('Fix on the feature branch', 'New commits.'),
        ('Re-introduce', 'Revert the revert, then merge the new fixes.'),
        title='Steps to Undo a Pushed Merge'),
    crossq(
        ('Why is -m 1 required?', 'A merge has two parents; Git needs to know which parent\'s side is the mainline to compute what to undo.'),
        ('After fixing, why did merging the branch again conflict instead of bringing grading.py back?', 'The branch\'s original commits are already ancestors of main, so only the new fix commit was merged — and it edits a file the revert deleted. Reverting the revert first restores the file, then the fix merges cleanly.'),
        ('When is reset acceptable instead?', 'Only if the merge was never pushed (or the branch is private) and nobody else has it.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Scenario: a teammate force-pushed and your local branch no longer matches the remote. How do you recover, and how do you prevent it?', 'Force Pushes & --force-with-lease', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('After someone rewrites a shared branch and force-pushes, your local branch contains old commits that no longer exist upstream; a plain pull would '
               'merge both histories and duplicate work. Recover with <code>git fetch</code>, inspect with <code>git log --oneline --graph main origin/main</code>, '
               'then either <code>git reset --hard origin/main</code> (if you have nothing local to keep) or <code>git rebase --onto origin/main &lt;old-base&gt;</code> '
               '/ cherry-pick your own new commits on top.',
               'Prevent it: protect shared branches (no force pushes on main), and when rewriting your <em>own</em> branch use '
               '<code>git push --force-with-lease</code>, which refuses to overwrite the remote if it has commits you have not seen. Plain <code>--force</code> '
               'silently destroys others\' work.'),
        tags('force push', '--force-with-lease', 'diverged history', 'git reset --hard origin/main', 'rebase --onto', 'branch protection'),
    ),
    analogy('<code>--force</code> is <strong>replacing a shared document with your copy</strong> without looking; <code>--force-with-lease</code> is replacing it '
            '<strong>only if nobody has edited it since you last looked</strong>.'),
    lease_anim(),
    real_world(
        scenario('Shared feature branch',
                 p('Asha rebased the shared feature branch and pushed with --force-with-lease; it was rejected because Ravi had pushed a commit an hour earlier. She '
                   'fetched, cherry-picked his commit on top of her reworded one and pushed safely. Without the lease, Ravi\'s commit would have vanished.')),
    ),
    example(
        REMOTE_NOTE,
        gitrun(team("""
            cd asha && git switch -q -c feature/report && echo "r1" > report.md && git add . && git commit -q -m "Report draft" && git push -q -u origin feature/report && cd ..
            cd ravi && git fetch -q && git switch -q feature/report && echo "r2" >> report.md && git commit -q -am "Ravi: add totals" && git push -q && cd ..
            cd asha
            git commit -q --amend -m "Report draft (reworded)"
            git push --force-with-lease
            git fetch -q
            git log --oneline --graph feature/report origin/feature/report
            git cherry-pick origin/feature/report
            git log --oneline
            git push --force-with-lease -q && git status -sb
        """), title=T),
        title='Example: --force-with-lease Refuses to Erase a Teammate\'s Commit'),
    steps(
        ('Do not pull blindly', 'git fetch first, then compare with log --graph.'),
        ('Nothing local to keep?', 'git reset --hard origin/<branch>.'),
        ('Have new local work?', 'Rebase or cherry-pick it onto the rewritten branch.'),
        ('Rewrite only your own branches', 'And push with --force-with-lease.'),
        ('Protect shared branches', 'Disallow force pushes on main in repository settings.'),
        title='Steps to Handle and Avoid Force-Push Damage'),
    crossq(
        ('Why can --force-with-lease still be unsafe?', 'If you ran fetch after the teammate pushed (e.g. an IDE auto-fetch), your remote-tracking ref already includes their commit, so the lease passes; --force-if-includes adds a further check.'),
        ('What happens if you just git pull after an upstream rewrite?', 'Git merges the old and new versions of the same changes, producing duplicate commits and possibly conflicts.'),
        ('How do you find your old commits if they were lost?', 'They are still in your reflog (and possibly in teammates\' clones) until garbage-collected.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: tidy a messy feature branch before opening a pull request — fixup commits, an outdated base and a clean push.', 'Polishing a Branch for Review', minutes=9, tag='Scenario', cards=[
    definition(
        defbox('Reviewers prefer a small number of meaningful commits on top of the current main. Workflow: while working, record small corrections as '
               '<code>git commit --fixup=&lt;commit&gt;</code>; before the PR, run <code>git rebase -i --autosquash origin/main</code>, which moves each fixup '
               'next to its target and squashes it, and at the same time replays the branch onto the latest main.',
               'Resolve any conflicts once during the rebase, run the tests, and push the rewritten (private) branch with '
               '<code>git push --force-with-lease</code>. Many teams set <code>rebase.autoSquash = true</code>. If the PR is already under review, prefer adding '
               'new commits so reviewers can see what changed since their last look.'),
        tags('commit --fixup', 'rebase --autosquash', 'interactive rebase', 'update base', '--force-with-lease', 'review-friendly history'),
    ),
    analogy('Before submitting a report you <strong>staple each correction slip to the page it corrects</strong> and re-number the pages to follow the latest '
            'template. --autosquash does the stapling; rebasing onto main does the re-numbering.'),
    autosquash_anim(),
    real_world(
        scenario('Final project pull request',
                 p('Asha\'s branch has "Add attendance chart", "fix typo", "oops", "address review" and is 5 commits behind main. Ten minutes of autosquash rebasing '
                   'later, the PR shows two clean commits on top of current main, and CI runs on exactly what will be merged.')),
    ),
    example(
        REMOTE_NOTE,
        gitrun(team("""
            cd asha
            git switch -q -c feature/chart
            echo "def chart(): pass" > chart.py && git add . && git commit -q -m "Add attendance chart"
            echo "def legend(): pass" > legend.py && git add . && git commit -q -m "Add chart legend"
            echo "# colour fix" >> chart.py && git commit -q -a --fixup=HEAD~1
            echo "# typo fix" >> legend.py && git commit -q -a --fixup=HEAD~1
            cd ../ravi && echo "faq" > faq.md && git add . && git commit -q -m "Add FAQ" && git push -q && cd ../asha
            git fetch -q
            git log --oneline --graph feature/chart origin/main
            GIT_SEQUENCE_EDITOR=: git rebase -q -i --autosquash origin/main
            git log --oneline --graph
            git show --stat --format='%s' HEAD~1 | grep -E "chart|Add"
            git push -q -u --force-with-lease origin feature/chart && git status -sb
        """), title=T),
        title='Example: fixup Commits Squashed Automatically While Rebasing onto the Latest main'),
    steps(
        ('Record corrections as fixups', 'git commit --fixup=<hash of the commit being corrected>.'),
        ('Update your view of main', 'git fetch.'),
        ('Autosquash and rebase', 'git rebase -i --autosquash origin/main (save the todo list as is).'),
        ('Test', 'Run the test suite on the rebased branch.'),
        ('Push safely', 'git push --force-with-lease; open or update the PR.'),
        title='Steps to Polish a Branch'),
    crossq(
        ('What does a fixup commit message look like?', '"fixup! <subject of the target commit>"; --autosquash matches on that subject.'),
        ('Why GIT_SEQUENCE_EDITOR=: in the example?', 'It accepts the generated todo list without opening an editor, so the rebase runs non-interactively (useful in scripts and demos).'),
        ('Squash everything into one commit?', 'Only if it is one logical change; otherwise keep a few meaningful commits so reviewers and bisect can use them.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Scenario: a file was deleted some time ago and is needed again. How do you find when it was deleted and restore it?', 'Recovering a Deleted File', minutes=7, tag='Scenario', cards=[
    definition(
        defbox('Git keeps every committed version, so a deleted file can be found in history. <code>git log --diff-filter=D --oneline -- path</code> (or '
               '<code>--diff-filter=D --summary</code> to search all deletions) finds the commit that deleted it; the last good version is in that commit\'s '
               '<strong>parent</strong> (<code>&lt;commit&gt;^</code>).',
               'Restore it with <code>git restore --source=&lt;commit&gt;^ --staged --worktree -- path</code> (without <code>--staged</code> the file comes back untracked; or the older <code>git checkout &lt;commit&gt;^ -- path</code>), '
               'review and commit. <code>git show &lt;commit&gt;^:path</code> prints the content without restoring. If you do not know the exact path, '
               '<code>git log --all --diff-filter=D --name-only</code> lists deleted files.'),
        tags('--diff-filter=D', 'git restore --source', 'commit^', 'git show commit:path', 'deleted file', 'history search'),
    ),
    analogy('Deleting a committed file is like <strong>removing a book from the shelf</strong> in a library that photographs the shelf every day. Find the day it '
            'disappeared, look at the photo from the day before, and put the same book back.'),
    restore_anim(),
    real_world(
        scenario('The old timetable generator',
                 p('A cleanup three weeks ago removed timetable_generator.py as "unused". The academic office needs it for the new batch. git log --diff-filter=D '
                   'finds the cleanup commit in seconds, and git restore brings back the exact last version, with its history intact.')),
    ),
    example(
        gitrun("""
            !git init -q office && cd office
            !printf 'def make_timetable(batch):\\n    return f"Timetable for {batch}"\\n' > timetable_generator.py && echo "notes" > notes.md && git add . && git commit -q -m "Add timetable generator"
            !echo "v2" >> notes.md && git commit -q -am "Update notes"
            !git rm -q timetable_generator.py && echo "v3" >> notes.md && git commit -q -am "Clean up unused scripts"
            !for i in 1 2 3; do echo "n$i" >> notes.md; git commit -q -am "More notes $i"; done
            !cd ..
            cd office
            ls
            git log --oneline
            git log --diff-filter=D --oneline -- timetable_generator.py
            git log --all --diff-filter=D --name-only --format='%h %s'
            git show $(git log --diff-filter=D --format=%h -- timetable_generator.py)^:timetable_generator.py
            git restore --source=$(git log --diff-filter=D --format=%h -- timetable_generator.py)^ --staged --worktree -- timetable_generator.py
            git status --short
            git commit -q -m "Restore timetable generator for the new batch" && git log --oneline -2
        """, title=T),
        title='Example: Find the Deleting Commit and Restore the Last Version from Its Parent'),
    steps(
        ('Find the deletion', 'git log --diff-filter=D --oneline -- path.'),
        ('Look at the last version', 'git show <commit>^:path.'),
        ('Restore it', 'git restore --source=<commit>^ --staged --worktree -- path.'),
        ('Review and commit', 'git status, git diff --staged, git commit.'),
        ('Unknown name?', 'git log --all --diff-filter=D --name-only.'),
        title='Steps to Restore a Deleted File'),
    crossq(
        ('Why use the parent (^) of the deleting commit?', 'In the deleting commit the file no longer exists; its parent has the last version.'),
        ('What if the file was never committed?', 'Git cannot help; only committed (or staged, via dangling blobs from git fsck --lost-found) content is recoverable.'),
        ('How do you restore a whole folder as it was at a tag?', 'git restore --source=v1.0 -- folder/ (then commit), or git checkout v1.0 -- folder/.'),
    ),
]),
])
