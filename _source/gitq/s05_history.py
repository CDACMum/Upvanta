from build import *
from gitq.anims import *
from gitq.runner import gitrun, sh
from gitq.s01_foundations import SETUP

SECTION = dict(level='advanced', title='Working with History', questions=[

# ------------------------------------------------------------------ 21
Q('What does git cherry-pick do and when should you use it?', 'cherry-pick', minutes=8, cards=[
    definition(
        defbox('<code>git cherry-pick SHA</code> applies the <strong>changes introduced by one commit</strong> onto the current branch as a <strong>new commit</strong> '
               '(new hash, same message). Several commits: <code>git cherry-pick A B</code> or a range <code>A^..B</code>. <code>-x</code> appends "(cherry picked '
               'from commit …)" to the message for traceability; <code>-n</code> applies without committing. Conflicts are resolved as usual, then '
               '<code>git cherry-pick --continue</code> (or <code>--abort</code>).',
               'Typical uses: back-porting a bug fix from main to a release branch, rescuing one commit from an abandoned branch. It duplicates commits, so '
               'prefer merging when you need all of a branch; overusing cherry-pick makes history hard to follow.'),
        tags('cherry-pick', '-x', 'backport', 'release branch', 'duplicate commits', 'cherry-pick --continue'),
    ),
    analogy('Cherry-pick is <strong>photocopying one page from a colleague\'s notebook</strong> into yours: you get that page\'s content, not the whole '
            'notebook, and the copy is a new page with your page number.'),
    cherry_anim(),
    real_world(
        scenario('Hotfix for the live exam portal',
                 p('A fix for a timezone bug lands on main among several unfinished features. The release branch running the August exam needs only that fix: '
                   '<code>git cherry-pick -x</code> copies it, the patch release is tagged, and main keeps its features for the next release.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q exam && cd exam && echo "v2.3" > version.txt && git add . && git commit -q -m "Release 2.3" && git branch release/2.3 && cd ..
            cd exam
            echo "new dashboard" > dash.html && git add . && git commit -q -m "WIP: new dashboard"
            echo "TZ = 'Asia/Kolkata'" > tz.py && git add . && git commit -q -m "Fix exam timer timezone"
            echo "more dashboard" >> dash.html && git commit -q -am "WIP: dashboard charts"
            git log --oneline
            git switch -q release/2.3
            git cherry-pick -x $(git log main --grep="timezone" --format=%h)
            git log --oneline
            git log -1 --format=%B
            ls
        """),
        title='Example: Back-port One Fix to a Release Branch with cherry-pick -x'),
    steps(
        ('Find the commit', '<code>git log --grep</code> / <code>--oneline main</code>.'),
        ('Switch to the target branch', '<code>git switch release/x</code>.'),
        ('Cherry-pick', '<code>git cherry-pick -x SHA</code>.'),
        ('Resolve conflicts if needed', 'Edit, <code>git add</code>, <code>--continue</code>.'),
        ('Test, tag and push', 'Patch release from the branch.'),
        title='Steps to Cherry-pick a Fix'),
    crossq(
        ('Why does the cherry-picked commit have a different hash?', 'It has a different parent (and committer date), so it is a different commit object even with the same changes.'),
        ('Why use -x?', 'It records the source commit in the message, so anyone can trace the back-port to the original fix.'),
        ('When is cherry-pick a bad idea?', 'To move many commits regularly between long-lived branches; the duplicates can conflict later. Merge or rebase instead.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What is the reflog and how do you recover "lost" commits or branches?', 'reflog & Recovery', minutes=8, cards=[
    definition(
        defbox('The <strong>reflog</strong> (<code>git reflog</code>) is a local journal of every position HEAD (and each branch) has pointed to: commits, '
               'checkouts, resets, rebases, merges, amends. Entries look like <code>HEAD@{3}</code>. Commits removed from a branch by <code>reset --hard</code>, '
               'a bad rebase or a deleted branch are not destroyed immediately: they stay in the object database and are reachable from the reflog (by default '
               'for 90 days, 30 for unreachable entries) until garbage collection.',
               'Recovery: find the entry, then <code>git reset --hard HEAD@{n}</code>, <code>git branch rescue SHA</code> or <code>git cherry-pick SHA</code>. '
               'The reflog is local only (not pushed) and does not help with changes that were never committed.'),
        tags('git reflog', 'HEAD@{n}', 'reset --hard recovery', 'deleted branch', 'dangling commit', 'gc'),
    ),
    analogy('The reflog is the <strong>CCTV recording of where your HEAD has been</strong>. Even if you threw a commit away, the footage shows where it was, so '
            'you can go back and pick it up — as long as the recording has not been overwritten.'),
    reflog_anim(),
    real_world(
        scenario('"I reset --hard and lost a day of work"',
                 p('A student runs <code>git reset --hard HEAD~3</code> on the wrong branch and panics. <code>git reflog</code> shows the commit before the reset; '
                   'one <code>git reset --hard HEAD@{1}</code> brings back all three commits. The same trick recovers a branch deleted with <code>-D</code>.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q work && cd work && for i in 1 2 3 4; do echo "chapter $i" > ch$i.md; git add .; git commit -q -m "Write chapter $i"; done && cd ..
            cd work
            git log --oneline
            git reset --hard -q HEAD~3
            git log --oneline
            git reflog -4
            git reset --hard HEAD@{1}
            git log --oneline
            git switch -q -c experiment && echo x > x.md && git add . && git commit -q -m "Experiment" && git switch -q main
            git branch -D experiment
            git reflog | grep -m1 "Experiment"
            git branch experiment $(git reflog | grep -m1 "commit: Experiment" | cut -d' ' -f1)
            git log --oneline -1 experiment
        """),
        title='Example: Undo a reset --hard and Restore a Deleted Branch from the Reflog'),
    steps(
        ('Stop and do not panic', 'Avoid further rewriting commands.'),
        ('Look at the journal', '<code>git reflog</code> (or <code>git reflog show branch</code>).'),
        ('Identify the good state', 'The entry just before the mistake.'),
        ('Restore', '<code>git reset --hard HEAD@{n}</code> or <code>git branch name SHA</code>.'),
        ('Verify', '<code>git log</code>, run tests.'),
        title='Steps to Recover with the Reflog'),
    crossq(
        ('Is the reflog shared with the team?', 'No; it is local to each clone. A fresh clone has an empty reflog.'),
        ('Can the reflog recover uncommitted changes?', 'No; only states that were committed (or stashed). Commit often.'),
        ('When are reflog entries removed?', 'They expire after gc.reflogExpire (90 days) or gc.reflogExpireUnreachable (30 days) when git gc runs.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How does git bisect find the commit that introduced a bug? How do you automate it?', 'git bisect', minutes=9, cards=[
    definition(
        defbox('<code>git bisect</code> performs a <strong>binary search</strong> over history. Mark a known <strong>bad</strong> commit (usually HEAD) and a '
               'known <strong>good</strong> one; Git checks out the midpoint, you test and answer <code>git bisect good</code> or <code>bad</code>, and it '
               'halves the range each time. With n commits it needs about log₂(n) tests: 1,000 commits → about 10 steps.',
               '<code>git bisect run ./test.sh</code> automates it: the script returns 0 for good, 1–127 (except 125) for bad, 125 to skip an untestable commit. '
               'Finish with <code>git bisect reset</code> to return to where you started. Bisect works best with small commits that each build.'),
        tags('git bisect', 'binary search', 'bisect good / bad', 'bisect run', 'exit code', 'bisect reset', 'regression'),
    ),
    analogy('Bisect is the <strong>"guess my number" game</strong>: "higher or lower?" halves the possibilities each time, so even among a thousand commits '
            'you find the guilty one in about ten questions.'),
    bisect_anim(),
    real_world(
        scenario('Results suddenly wrong',
                 p('After 30 commits, the grade calculator gives a wrong result for a 49-mark student. A one-line check script plus <code>git bisect run</code> finds '
                   'the exact commit that moved the pass boundary from 50 to 49 in five automatic steps, with its author and message.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q calc && cd calc
            !printf 'def grade(m):\\n    return "P" if m >= 50 else "F"\\n' > grade.py && git add . && git commit -q -m "Add grade function"
            !for i in $(seq 1 30); do echo "# note $i" >> notes.md; git add notes.md; if [ $i -eq 19 ]; then sed -i 's/m >= 50/m >= 49/' grade.py; git add grade.py; git commit -q -m "Refactor grade boundaries (#$i)"; else git commit -q -m "Update notes $i"; fi; done
            !cd ..
            cd calc
            git log --oneline | wc -l
            printf 'import grade, sys\\nsys.exit(0 if grade.grade(49) == "F" else 1)\\n' > check.py
            python3 -B check.py; echo "exit code: $?"
            git bisect start HEAD HEAD~30
            git bisect run python3 -B check.py 2>&1 | grep -E "is the first bad commit|Bisecting|running" | head -12
            git bisect log | grep "first bad"
            git bisect reset
            git show --stat --format='%h %s' $(git log --grep="#19" --format=%h) | head -3
        """),
        title='Example: Automatic Bisect over 31 Commits with a Python Check Script'),
    steps(
        ('Write a reliable test', 'Script or command: exit 0 = good, non-zero = bad.'),
        ('Start', '<code>git bisect start BAD GOOD</code>.'),
        ('Run', '<code>git bisect run ./check</code> (or answer good/bad by hand).'),
        ('Read the result', '"<sha> is the first bad commit".'),
        ('Reset and fix', '<code>git bisect reset</code>; fix or revert that commit.'),
        title='Steps to Bisect a Regression'),
    crossq(
        ('Why is the check script untracked in the example?', 'Bisect checks out old commits; an untracked script stays in place so every commit is tested with the same check.'),
        ('What does exit code 125 mean in bisect run?', 'Skip this commit (cannot be tested, e.g. it does not build); bisect chooses a nearby commit instead.'),
        ('How many steps for 31 commits?', 'At most about log₂(31) ≈ 5.'),
        ('Why python3 -B in the check?', 'Bisect swaps grade.py very quickly; a stale __pycache__ file with the same size and timestamp could make Python run old bytecode. -B disables bytecode caching so every step tests the checked-out source.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you find who changed a line and why? Explain git blame, git log -S / -G and git log -L.', 'blame & Code Archaeology', minutes=8, cards=[
    definition(
        defbox('<code>git blame file</code> shows, for every line, the commit, author and date that last changed it; <code>-L 10,20</code> limits lines, '
               '<code>-w</code> ignores whitespace changes, <code>-C</code> follows code copied from other files, and <code>--ignore-rev</code> / '
               '<code>blame.ignoreRevsFile</code> skip mass-formatting commits.',
               'To find when something appeared or disappeared: <code>git log -S "text"</code> (pickaxe: commits where the count of the string changed), '
               '<code>git log -G regex</code> (diff lines match), <code>git log -L :function:file</code> or <code>-L start,end:file</code> (history of a '
               'function or line range). Then <code>git show SHA</code> for the full context and message. "Blame" is about understanding, not blaming people.'),
        tags('git blame', 'blame -L', '-w / -C', 'log -S', 'log -G', 'log -L', 'ignore-revs'),
    ),
    analogy('Code archaeology: <strong>blame</strong> tells you which layer of soil each artefact came from; <strong>log -S</strong> finds the layer where an '
            'object first appeared; <strong>log -L</strong> is the full excavation record of one spot.'),
    blame_anim(),
    real_world(
        scenario('Why is attendance capped at 95 %?',
                 p('A new developer finds <code>min(att, 95)</code> in the report code and wonders whether it is a bug. <code>git blame</code> points to a commit '
                   'whose message cites the academic council rule on medical leave; the line stays, and a comment is added.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q rep && cd rep
            !printf 'def report(att):\\n    return att\\n' > report.py && git add . && git commit -q -m "Add attendance report"
            !git -c user.name="Ravi Kumar" commit -q --allow-empty -m "Set up CI"
            !sed -i 's/return att/return min(att, 95)/' report.py && git -c user.name="Ravi Kumar" commit -q -am "Cap attendance at 95%" -m "Academic council: medical leave counts up to 5%."
            !printf 'def report(att):\\n    # attendance percentage shown on the report\\n    return min(att, 95)\\n' > report.py && git commit -q -am "Document report()"
            !cd ..
            cd rep
            git blame report.py
            git blame -L 3,3 --porcelain report.py | grep -E "^(author |summary )"
            git log -S "min(att, 95)" --format='%h %an %s'
            git log -L :report:report.py --format='%h %s' | grep -E "^[0-9a-f]{7} |^[+-] "
        """),
        title='Example: blame a Line, Find Its Introduction with -S, Trace a Function with -L'),
    steps(
        ('Find the line\'s last change', '<code>git blame -L n,m file</code> (add <code>-w -C</code>).'),
        ('Read the commit', '<code>git show SHA</code> — message, linked issue.'),
        ('Find when text appeared', '<code>git log -S "text"</code> / <code>-G regex</code>.'),
        ('Follow a function', '<code>git log -L :name:file</code>.'),
        ('Record what you learned', 'Comment or document the reason.'),
        title='Steps for Code Archaeology'),
    crossq(
        ('Why can blame point to the wrong commit?', 'Reformatting or moving code becomes the "last change"; use -w, -C, -M or ignore-revs files to see through it.'),
        ('-S vs -G?', '-S finds commits that change the number of occurrences of a string (added/removed); -G finds commits whose diff lines match a regex, even if the count is unchanged.'),
        ('Why does good history matter for blame?', 'Blame leads to a commit; only a clear message and a focused commit explain the reason.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What is a detached HEAD? How do you get into it and how do you keep work done there?', 'Detached HEAD', minutes=7, cards=[
    definition(
        defbox('Normally HEAD points to a <strong>branch</strong>, which points to a commit. In <strong>detached HEAD</strong> state, HEAD points '
               '<strong>directly to a commit</strong> — after <code>git checkout SHA</code>, <code>git switch --detach</code>, checking out a tag, or during '
               'rebase/bisect. You can look around, build and even commit, but those commits belong to no branch.',
               'When you switch away, commits made while detached become unreachable (Git warns and prints their hash) and are eventually garbage-collected. '
               'To keep them, create a branch: <code>git switch -c new-branch</code> while still detached, or later <code>git branch name SHA</code> using the '
               'hash from the warning or the reflog.'),
        tags('detached HEAD', 'checkout SHA', 'switch --detach', 'tag checkout', 'orphaned commits', 'switch -c'),
    ),
    analogy('Detached HEAD is <strong>visiting an old station without being on a train</strong>. You can walk around and even build something there, but unless '
            'you park a train (a branch) at it, nobody will find it again.'),
    detached_anim(),
    real_world(
        scenario('Testing an old release',
                 p('To reproduce a bug reported against v1.0, a developer checks out the tag (detached), finds and fixes the issue there, and creates '
                   '<code>hotfix/v1.0.1</code> from that state before switching back, so the fix is not lost.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q app && cd app && echo v1 > app.txt && git add . && git commit -q -m "v1" && git tag v1.0 && echo v2 > app.txt && git commit -q -am "v2" && cd ..
            cd app
            git switch --detach v1.0
            cat .git/HEAD
            git status | head -1
            echo "hotfix" >> app.txt && git commit -q -am "Hotfix on v1"
            git switch main
            git reflog -2
            git branch hotfix/v1.0.1 HEAD@{1}
            git log --oneline --graph --all
        """),
        title='Example: Detach at a Tag, Commit, Switch Away (Warning), Rescue the Commit into a Branch'),
    steps(
        ('Recognise the state', '<code>git status</code>: "HEAD detached at …".'),
        ('Look around freely', 'Builds and tests are fine.'),
        ('Before committing', 'Prefer <code>git switch -c new-branch</code> first.'),
        ('If you committed while detached', '<code>git switch -c name</code> before leaving, or <code>git branch name SHA</code> afterwards.'),
        ('Return', '<code>git switch main</code>.'),
        title='Steps to Handle a Detached HEAD'),
    crossq(
        ('Is detached HEAD an error?', 'No; it is a normal state for inspecting history, tags, bisect and rebase. It only matters if you commit and leave.'),
        ('Where can you find the hash of a commit made while detached?', 'In the warning printed when you switched away, and in git reflog.'),
        ('Why does checking out a tag detach HEAD?', 'Tags are fixed; if HEAD pointed to the tag, new commits would have nowhere to move the pointer to, so Git points HEAD at the commit itself.'),
    ),
]),
])
