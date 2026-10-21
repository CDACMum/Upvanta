from build import *
from gitq.anims import *
from gitq.runner import gitrun, sh
from gitq.s01_foundations import SETUP

SECTION = dict(level='intermediate', title='Branching & Merging', questions=[

# ------------------------------------------------------------------ 11
Q('What is a branch in Git, and what is HEAD? How do you create, switch, list and delete branches?', 'Branches & HEAD', minutes=8, cards=[
    definition(
        defbox('A <strong>branch</strong> is a movable pointer (a 41-byte file under <code>.git/refs/heads/</code>) to a commit. Committing on a branch moves '
               'that pointer forward. Creating a branch is instant and cheap, which is why Git encourages one branch per feature or fix. '
               '<strong>HEAD</strong> points to the branch you are on (or directly to a commit in "detached HEAD" state).',
               'Commands: <code>git branch</code> (list; <code>-v</code> last commit, <code>-a</code> include remote-tracking), <code>git switch -c name</code> '
               '(create and switch; older: <code>git checkout -b</code>), <code>git switch name</code>, <code>git branch -d name</code> (delete if merged; '
               '<code>-D</code> force), <code>git branch -m old new</code> (rename). Uncommitted changes travel with you when switching unless they conflict.'),
        tags('branch', 'HEAD', 'git switch', 'switch -c', 'checkout -b', 'branch -d', 'refs/heads'),
    ),
    analogy('Commits are <strong>stations on a railway line</strong>; a branch is a <strong>train</strong> parked at a station; HEAD is <strong>the train '
            'you are sitting in</strong>. Each new commit moves your train one station further; other trains stay where they are.'),
    branch_anim(),
    real_world(
        scenario('Two features at once',
                 p('One developer builds an attendance export on <code>feature/export</code> while another fixes a login bug on <code>fix/login</code>. Each branch '
                   'moves independently; main stays stable until each piece of work is reviewed and merged.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q portal && cd portal && echo "v1" > app.txt && git add . && git commit -q -m "Initial portal" && cd ..
            cd portal
            git branch
            git switch -c feature/export
            echo "export" > export.py && git add . && git commit -q -m "Add attendance export"
            git branch -v
            cat .git/HEAD
            cat .git/refs/heads/feature/export
            git switch main
            ls
            git log --oneline --all --graph
            git branch -d feature/export
            git branch -D feature/export
        """),
        title='Example: Create a Branch, Commit on It, Inspect HEAD and Refs, Delete'),
    steps(
        ('Start from an up-to-date base', '<code>git switch main && git pull</code>.'),
        ('Create the branch', '<code>git switch -c feature/name</code>.'),
        ('Commit on it', 'The branch pointer moves; main does not.'),
        ('List and inspect', '<code>git branch -v</code>, <code>git log --oneline --graph --all</code>.'),
        ('Delete when merged', '<code>git branch -d name</code> (refuses if unmerged).'),
        title='Steps to Work with Branches'),
    crossq(
        ('Why did git branch -d refuse?', 'The branch had commits not merged into the current branch; -d protects them. -D deletes anyway (the commits remain reachable via the reflog for a while).'),
        ('What is stored in .git/HEAD?', 'Normally "ref: refs/heads/<branch>"; in detached HEAD state, a commit hash.'),
        ('Why are branches so cheap in Git?', 'A branch is just a file containing a commit hash; no files are copied.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How does git merge work? Explain fast-forward merges, three-way merges and --no-ff.', 'Merging', minutes=9, cards=[
    definition(
        defbox('<code>git merge feature</code> brings the commits of <code>feature</code> into the current branch. If the current branch has not moved since '
               'feature branched off, Git simply moves the pointer forward: a <strong>fast-forward</strong>, with no new commit. If both branches have new '
               'commits, Git performs a <strong>three-way merge</strong> using the two tips and their <strong>merge base</strong> (common ancestor) and creates a '
               '<strong>merge commit</strong> with two parents.',
               '<code>--no-ff</code> forces a merge commit even when a fast-forward is possible, keeping the feature visible as a unit in history (common for '
               'pull requests); <code>--ff-only</code> refuses to merge unless a fast-forward is possible. <code>git merge-base A B</code> shows the common '
               'ancestor; <code>git log --graph</code> shows the result.'),
        tags('git merge', 'fast-forward', 'three-way merge', 'merge commit', 'merge base', '--no-ff', '--ff-only'),
    ),
    analogy('A fast-forward is <strong>catching up on a single road</strong>: you just drive further. A three-way merge is <strong>two roads that split and '
            'rejoin</strong>: the junction (merge commit) records that both routes were travelled.'),
    merge_anim(),
    real_world(
        scenario('Merging reviewed work into main',
                 p('The results-module team merges each reviewed feature with <code>--no-ff</code>, so <code>git log --graph</code> shows every feature as a '
                   'bubble with one merge commit, which can be reverted as a whole if the feature causes trouble.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q results && cd results && echo "main v1" > app.txt && git add . && git commit -q -m "Initial" && cd ..
            cd results
            git switch -q -c feature/a && echo a > a.txt && git add . && git commit -q -m "Feature A"
            git switch -q main
            git merge feature/a
            git switch -q -c feature/b && echo b > b.txt && git add . && git commit -q -m "Feature B"
            git switch -q main && echo "main v2" > app.txt && git commit -q -am "Update main"
            git merge-base main feature/b | cut -c1-7
            git merge --no-edit feature/b
            git switch -q -c feature/c && echo c > c.txt && git add . && git commit -q -m "Feature C"
            git switch -q main
            git merge --no-ff --no-edit feature/c
            git log --oneline --graph
            git log --merges --format='%h parents: %p  %s'
        """),
        title='Example: Fast-Forward, Three-Way Merge and --no-ff'),
    steps(
        ('Switch to the receiving branch', '<code>git switch main</code> (up to date).'),
        ('Merge', '<code>git merge feature</code> (add <code>--no-ff</code> to keep a merge commit).'),
        ('Resolve conflicts if any', 'Edit, <code>git add</code>, <code>git commit</code>.'),
        ('Verify', '<code>git log --oneline --graph</code>, run the tests.'),
        ('Delete the merged branch', '<code>git branch -d feature</code>.'),
        title='Steps to Merge a Branch'),
    crossq(
        ('Why did the first merge not create a commit?', 'main had no new commits since feature/a branched, so Git just moved main forward (fast-forward).'),
        ('How many parents does a merge commit have?', 'Two (or more for an octopus merge); the first parent is the branch you were on.'),
        ('Why use --no-ff for pull requests?', 'The merge commit groups the feature\'s commits, documents when it was merged, and can be reverted in one step (git revert -m 1).'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What causes a merge conflict and how do you resolve it?', 'Merge Conflicts', minutes=9, cards=[
    definition(
        defbox('A <strong>conflict</strong> happens when both branches changed the <strong>same lines</strong> of a file (or one modified a file the other '
               'deleted) since the merge base, so Git cannot decide automatically. The merge stops; <code>git status</code> lists "both modified" files, which '
               'contain conflict markers: <code>&lt;&lt;&lt;&lt;&lt;&lt;&lt; HEAD</code> (yours), <code>=======</code>, '
               '<code>&gt;&gt;&gt;&gt;&gt;&gt;&gt; branch</code> (theirs).',
               'To resolve: edit each file to the correct final content and remove the markers (or take one side with '
               '<code>git checkout --ours / --theirs file</code>), then <code>git add</code> the files and <code>git commit</code> (or '
               '<code>git merge --continue</code>). <code>git merge --abort</code> returns to the state before the merge. <code>merge.conflictStyle diff3/zdiff3</code> '
               'also shows the base version, which makes resolution easier.'),
        tags('merge conflict', 'conflict markers', 'both modified', 'merge --abort', '--ours / --theirs', 'diff3', 'merge --continue'),
    ),
    analogy('Two editors changed the <strong>same sentence</strong> in a shared document. The software cannot guess which wording is right, so it shows both '
            'and waits for a human to decide.'),
    conflict_anim(),
    real_world(
        scenario('Pass mark changed in two branches',
                 p('One branch raises the pass mark to 50 for PG-DBDA, another changes it to 45 for a bridge course. Merging both produces a conflict on that line; '
                   'the team decides on a per-course setting, writes it by hand, and commits the resolution with an explanation.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q conf && cd conf && printf 'COURSE = "PG-DBDA"\\nPASS_MARK = 40\\n' > settings.py && git add . && git commit -q -m "Initial settings" && cd ..
            cd conf
            git switch -q -c raise-pass && sed -i 's/40/50/' settings.py && git commit -q -am "Raise pass mark to 50"
            git switch -q main && sed -i 's/40/45/' settings.py && git commit -q -am "Set pass mark to 45 for bridge course"
            git merge raise-pass
            git status --short
            cat settings.py
            git checkout --conflict=diff3 settings.py
            cat settings.py
            printf 'COURSE = "PG-DBDA"\\nPASS_MARK = {"PG-DBDA": 50, "Bridge": 45}\\n' > settings.py
            git add settings.py
            git commit -q --no-edit
            git log --oneline --graph
            cat settings.py
        """),
        title='Example: Create a Conflict, Read the Markers (Also in diff3 Style), Resolve and Commit'),
    steps(
        ('See what conflicts', '<code>git status</code> → "both modified".'),
        ('Open each file', 'Find the markers; understand both sides (and the base with diff3).'),
        ('Write the correct result', 'Remove all markers; or take a side with --ours/--theirs.'),
        ('Mark resolved', '<code>git add file</code>; run the tests.'),
        ('Finish or abort', '<code>git commit</code> / <code>git merge --continue</code>, or <code>git merge --abort</code>.'),
        title='Steps to Resolve a Conflict'),
    crossq(
        ('Do changes to different lines of the same file conflict?', 'Usually not; Git merges non-overlapping hunks automatically. Only overlapping or adjacent changes conflict.'),
        ('Why use the diff3 conflict style?', 'It also shows the common ancestor version, so you can see what each side changed instead of guessing.'),
        ('How do you prevent frequent conflicts?', 'Small, short-lived branches, frequent merges or rebases from main, and avoiding mass reformatting in feature branches.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('What does git rebase do? How is it different from merge, and what is the golden rule of rebasing?', 'Rebase', minutes=9, cards=[
    definition(
        defbox('<code>git rebase main</code> (run on a feature branch) takes the feature\'s commits since the merge base and <strong>replays them on top of '
               'main</strong>, creating new commits with new hashes. The result is a <strong>linear history</strong>, as if the feature had been started from '
               'the latest main; a later merge into main is then a fast-forward.',
               'Merge preserves the true history (with merge commits); rebase rewrites it into a straight line. Conflicts are resolved commit by commit '
               '(<code>git add</code>, <code>git rebase --continue</code>, or <code>--abort</code>). <strong>Golden rule</strong>: never rebase commits that '
               'others have already pulled — rewrite only your own, unshared (or explicitly agreed) branches.'),
        tags('git rebase', 'replay commits', 'linear history', 'new hashes', 'rebase --continue', 'golden rule'),
    ),
    analogy('Rebase is <strong>moving your stack of drafts onto the newest version of the textbook</strong> and rewriting each draft so it fits; merge is '
            '<strong>stapling a note</strong> that says "these drafts were written against last week\'s edition".'),
    rebase_anim(),
    real_world(
        scenario('Keeping a feature branch current',
                 p('A student\'s feature branch is three days behind main. Rebasing it onto main replays her two commits on top of the latest code, she fixes one '
                   'small conflict, and her pull request shows a clean, linear history that is easy to review.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q rb && cd rb && echo "base" > base.txt && git add . && git commit -q -m "Base" && cd ..
            cd rb
            git switch -q -c feature && echo f1 > f1.txt && git add . && git commit -q -m "Feature step 1"
            echo f2 > f2.txt && git add . && git commit -q -m "Feature step 2"
            git switch -q main && echo m1 > m1.txt && git add . && git commit -q -m "Main moved on"
            git log --oneline --graph --all
            git switch -q feature
            git rev-parse --short HEAD
            git rebase main
            git rev-parse --short HEAD
            git log --oneline --graph --all
            git switch -q main && git merge feature
        """),
        title='Example: Rebase a Feature onto main, New Hashes, Fast-Forward Merge'),
    steps(
        ('Update main', '<code>git switch main && git pull</code>.'),
        ('Rebase your branch', '<code>git switch feature && git rebase main</code>.'),
        ('Resolve conflicts per commit', 'Edit, <code>git add</code>, <code>git rebase --continue</code>.'),
        ('Test', 'Each replayed commit should still build.'),
        ('Push (rewritten branch)', '<code>git push --force-with-lease</code> for your own branch only.'),
        title='Steps to Rebase Safely'),
    crossq(
        ('Why do commit hashes change after a rebase?', 'Each replayed commit has a different parent (and possibly content), and the parent is part of the hashed content.'),
        ('Merge or rebase?', 'Rebase for a clean history of your own unshared work; merge to integrate shared branches and preserve exactly what happened. Many teams rebase features, then merge them with --no-ff or squash.'),
        ('What goes wrong if you rebase a shared branch?', 'Collaborators still have the old commits; when they pull, Git sees two divergent histories with duplicate changes, causing confusion and conflicts.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you clean up commits with interactive rebase: squash, fixup, reword, reorder and drop?', 'Interactive Rebase', minutes=9, cards=[
    definition(
        defbox('<code>git rebase -i BASE</code> opens a todo list of the commits after BASE, one per line, each with an action: <strong>pick</strong> (keep), '
               '<strong>reword</strong> (change message), <strong>edit</strong> (stop to amend), <strong>squash</strong> (merge into the previous commit, '
               'combining messages), <strong>fixup</strong> (merge, discarding this message), <strong>drop</strong> (remove). Reordering lines reorders the '
               'commits.',
               'Typical use: before opening a pull request, turn "WIP", "fix typo", "fix again" into a few meaningful commits. <code>git commit --fixup=SHA</code> '
               'plus <code>git rebase -i --autosquash</code> automates it. It rewrites history, so use it on your own branch before sharing. (In the example the '
               'editor is replaced by <code>GIT_SEQUENCE_EDITOR=sed …</code> so the todo list can be edited non-interactively.)'),
        tags('rebase -i', 'pick', 'squash', 'fixup', 'reword', 'drop', 'autosquash', 'GIT_SEQUENCE_EDITOR'),
    ),
    analogy('Interactive rebase is <strong>editing your rough notes into a clean report</strong> before submitting it: merge scattered fragments, fix headings, '
            'throw out the scribbles.'),
    irebase_anim(),
    real_world(
        scenario('Tidy history for review',
                 p('A feature branch has six commits, three of which are "fix typo" and "oops". The reviewer asks for a clean history; interactive rebase squashes '
                   'them into two commits — "Add CSV export" and "Add export tests" — and the pull request becomes easy to read and revert.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q tidy && cd tidy && echo base > base.txt && git add . && git commit -q -m "Base" && cd ..
            cd tidy
            echo "def export(): ..." > export.py && git add . && git commit -q -m "Add CSV export"
            echo "# typo fixed" >> export.py && git commit -q -am "fix typo"
            echo "def test(): ..." > test_export.py && git add . && git commit -q -m "WIP tests"
            echo "debug" > debug.log && git add . && git commit -q -m "add debug log"
            git log --oneline
            GIT_SEQUENCE_EDITOR="sed -i -e '2s/^pick/fixup/' -e '3s/^pick/reword/' -e '4s/^pick/drop/'" GIT_EDITOR="sed -i '1s/.*/Add export tests/'" git rebase -i HEAD~4
            git log --oneline
            git show --stat --format='%s' HEAD~1 | head -4
            ls
        """),
        title='Example: fixup a Typo Commit, reword "WIP", drop a Debug Commit'),
    steps(
        ('Choose the base', '<code>git rebase -i HEAD~n</code> or <code>-i main</code>.'),
        ('Edit the todo list', 'pick / reword / squash / fixup / drop; reorder lines.'),
        ('Handle stops', 'Write messages, resolve conflicts, <code>git rebase --continue</code>.'),
        ('Check the result', '<code>git log --oneline</code>, run tests.'),
        ('Share', 'Push your branch (force-with-lease if it was pushed before).'),
        title='Steps for Interactive Rebase'),
    crossq(
        ('squash vs fixup?', 'Both fold a commit into the previous one; squash lets you combine the messages, fixup throws away the folded commit\'s message.'),
        ('What is --autosquash?', 'Commits created with git commit --fixup=SHA (message "fixup! …") are automatically moved and marked fixup in the todo list.'),
        ('How do you undo a bad interactive rebase?', 'Find the pre-rebase commit in git reflog (or ORIG_HEAD) and git reset --hard to it.'),
    ),
]),
])
