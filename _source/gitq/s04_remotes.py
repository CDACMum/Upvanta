from build import *
from gitq.anims import *
from gitq.runner import gitrun, sh
from gitq.s01_foundations import SETUP

REMOTE_NOTE = note('Remote examples use a <strong>bare repository</strong> in <code>~/server/portal.git</code> as a stand-in for GitHub or GitLab; '
                   'the commands are exactly the ones you use with an <code>https://</code> or <code>git@github.com:</code> URL. Two clones, '
                   '<code>asha/</code> and <code>ravi/</code>, play two team members (Ravi has his own <code>user.name</code>).', 'Remote setup')

TEAM = """
!git init -q --bare ~/server/portal.git
!git clone -q ~/server/portal.git asha 2>/dev/null && cd asha && echo "# Student portal" > README.md && git add . && git commit -q -m "Initial commit" && git push -q origin main && cd ..
!git clone -q ~/server/portal.git ravi && git -C ravi config user.name "Ravi Kumar" && git -C ravi config user.email ravi@cdac.example
"""



def team(body):
    import textwrap
    return TEAM.strip('\n') + '\n' + textwrap.dedent(body).strip('\n')


SECTION = dict(level='intermediate', title='Remotes & Collaboration', questions=[

# ------------------------------------------------------------------ 16
Q('What are remotes and remote-tracking branches? Explain git fetch vs git pull.', 'Remotes, fetch & pull', minutes=9, cards=[
    definition(
        defbox('A <strong>remote</strong> is a named URL of another copy of the repository (<code>origin</code> after cloning). <code>git remote -v</code> lists '
               'them; <code>git remote add name URL</code> adds one. <strong>Remote-tracking branches</strong> such as <code>origin/main</code> are your '
               'local, read-only record of where the remote\'s branches were the last time you talked to it.',
               '<code>git fetch</code> downloads new commits and updates <code>origin/*</code> <strong>without touching your branches or files</strong> — safe '
               'to run any time, then inspect with <code>git log main..origin/main</code>. <code>git pull</code> = <code>fetch</code> + integrate '
               '(<code>merge</code> by default, or <code>rebase</code> with <code>--rebase</code> / <code>pull.rebase=true</code>) into the current branch.'),
        tags('remote', 'origin', 'remote-tracking branch', 'origin/main', 'git fetch', 'git pull', 'git remote -v'),
    ),
    analogy('<code>fetch</code> is <strong>checking the mailbox and reading the letters</strong>; <code>pull</code> is checking the mailbox <strong>and '
            'immediately filing every letter into your notebook</strong>. Fetch first if you want to look before you file.'),
    fetch_anim(),
    real_world(
        scenario('Seeing a colleague\'s work before merging it',
                 p('Asha wants to know what Ravi pushed overnight before it lands in her branch. <code>git fetch</code> then '
                   '<code>git log main..origin/main</code> shows his commits; when she is happy, <code>git merge origin/main</code> (or <code>git pull</code>) '
                   'brings them in.')),
    ),
    example(
        SETUP, REMOTE_NOTE,
        gitrun(team("""
            cd ravi && echo "login page" > login.html && git add . && git commit -q -m "Add login page" && git push -q && cd ..
            cd asha
            git remote -v
            git branch -a
            git log --oneline main..origin/main
            git fetch
            git log --oneline main..origin/main
            git status -sb
            ls
            git pull
            ls
            git log --oneline --format='%h %an: %s'
        """)),
        title='Example: fetch Shows Ravi\'s Commit Without Changing Files, pull Integrates It'),
    steps(
        ('Check remotes', '<code>git remote -v</code>, <code>git branch -a</code>.'),
        ('Fetch', '<code>git fetch</code> (or <code>--all --prune</code>).'),
        ('Inspect incoming work', '<code>git log main..origin/main</code>, <code>git diff main origin/main</code>.'),
        ('Integrate', '<code>git merge origin/main</code> or <code>git pull</code> / <code>pull --rebase</code>.'),
        ('Keep tidy', '<code>git fetch --prune</code> removes deleted remote branches.'),
        title='Steps to Sync with a Remote'),
    crossq(
        ('Why did the first git log main..origin/main show nothing?', 'origin/main was stale: it only updates when you fetch (or pull). After fetching, Ravi\'s commit appeared.'),
        ('Is git fetch ever dangerous?', 'No. It only updates remote-tracking refs and downloads objects; your branches and working files are untouched.'),
        ('What does "Your branch is behind origin/main by 1 commit" mean?', 'After fetching, origin/main has a commit you do not have locally; pull or merge to catch up.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('How does git push work? Explain upstream tracking and why a push gets rejected.', 'Pushing & Upstream', minutes=9, cards=[
    definition(
        defbox('<code>git push origin branch</code> uploads your commits and moves the remote branch to your commit. The first push of a new branch uses '
               '<code>git push -u origin branch</code> to set the <strong>upstream</strong> (tracking) branch, after which plain <code>git push</code> / '
               '<code>git pull</code> know where to go, and <code>git status</code> reports ahead/behind counts.',
               'A push is <strong>rejected (non-fast-forward)</strong> when the remote branch has commits you do not have — someone pushed first. Fix it by '
               'integrating their work (<code>git pull</code> or <code>pull --rebase</code>) and pushing again. Do not "fix" it with <code>--force</code> on a '
               'shared branch: that deletes their commits from the remote. <code>--force-with-lease</code> is the safer variant for your own rewritten branches.'),
        tags('git push', 'push -u', 'upstream', 'tracking branch', 'non-fast-forward', 'rejected push', 'force-with-lease'),
    ),
    analogy('Pushing is <strong>adding your pages to the shared binder</strong>. If someone added pages since you last looked, the binder refuses yours until '
            'you have read and inserted their pages first — otherwise their work would be thrown away.'),
    push_anim(),
    real_world(
        scenario('Two people pushing to main',
                 p('Ravi pushes a login page; minutes later Asha\'s push of the README update is rejected. She pulls (Git merges Ravi\'s commit), checks the result, '
                   'and pushes again. Nobody loses work, and the history shows both contributions.')),
    ),
    example(
        SETUP, REMOTE_NOTE,
        gitrun(team("""
            cd ravi && echo "login" > login.html && git add . && git commit -q -m "Add login page" && git push -q && cd ..
            cd asha
            echo "Contact: office@cdac.example" >> README.md && git commit -q -am "Add contact to README"
            git push
            git pull --no-edit
            git push
            git switch -q -c feature/timetable && echo "tt" > timetable.html && git add . && git commit -q -m "Add timetable"
            git push -u origin feature/timetable
            git status -sb
            git branch -vv
        """)),
        title='Example: A Rejected Push, Pull to Integrate, Push Again, Set Upstream for a New Branch'),
    steps(
        ('Commit locally', 'Small, tested commits.'),
        ('Push a new branch with upstream', '<code>git push -u origin feature/x</code>.'),
        ('If rejected', '<code>git pull</code> (or <code>--rebase</code>), resolve, test.'),
        ('Push again', '<code>git push</code>.'),
        ('Never force shared branches', 'Only <code>--force-with-lease</code> on your own rewritten branch.'),
        title='Steps to Push Safely'),
    crossq(
        ('What does "ahead 1, behind 2" mean?', 'You have 1 commit the remote does not, and the remote has 2 commits you do not; pull, then push.'),
        ('Why is push --force dangerous?', 'It replaces the remote branch with yours, discarding commits others pushed; they disappear for everyone who pulls next.'),
        ('What does -u do exactly?', 'Sets branch.<name>.remote and branch.<name>.merge, so git push/pull without arguments use that remote branch and status shows ahead/behind.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('git pull --rebase vs merge: how do you handle divergent branches cleanly?', 'pull --rebase', minutes=8, cards=[
    definition(
        defbox('When your local branch and its remote have both moved on (divergent), <code>git pull</code> must integrate them. With merge (the classic '
               'default) it creates a <strong>merge commit</strong> such as "Merge branch \'main\' of origin", which clutters history when it happens every day. '
               'With <code>git pull --rebase</code> it replays your local commits <strong>on top of</strong> the fetched ones, giving a straight line.',
               'Recent Git versions ask you to choose: <code>git config pull.rebase false</code> (merge), <code>true</code> (rebase) or <code>pull.ff only</code> '
               '(refuse unless fast-forward). Rebasing your own unpushed local commits during pull is safe and common; conflicts are resolved per commit with '
               '<code>git rebase --continue</code>.'),
        tags('git pull --rebase', 'divergent branches', 'pull.rebase', 'pull.ff only', 'linear history', 'merge commit noise'),
    ),
    analogy('Merging on pull is like <strong>stapling today\'s and yesterday\'s notes together with a label</strong>; rebasing is <strong>rewriting your new '
            'notes after the latest page</strong>, so the notebook reads in one sequence.'),
    pullrb_anim(),
    real_world(
        scenario('A team that works on main',
                 p('In a small course-content repo everyone commits to main. With <code>pull.rebase=true</code> the history stays linear, so <code>git log</code> '
                   'reads like a clean changelog instead of being full of "Merge branch \'main\' of …" commits.')),
    ),
    example(
        SETUP, REMOTE_NOTE,
        gitrun(team("""
            !cp -r asha asha2
            cd ravi && echo "login" > login.html && git add . && git commit -q -m "Add login page" && git push -q && cd ..
            cd asha
            echo "a" > about.html && git add . && git commit -q -m "Add about page"
            git pull --no-rebase --no-edit -q
            git log --oneline --graph
            cd ../asha2
            echo "a" > about.html && git add . && git commit -q -m "Add about page"
            git pull --rebase -q
            git log --oneline --graph
        """)),
        title='Example: The Same Divergence Resolved by pull (merge) and pull --rebase'),
    steps(
        ('Decide the team policy', 'pull.rebase true (linear) or false (merge).'),
        ('Configure it', '<code>git config --global pull.rebase true</code>.'),
        ('Pull', '<code>git pull</code>; resolve conflicts with rebase --continue.'),
        ('Check', '<code>git log --oneline --graph</code>.'),
        ('Push', 'Your rebased commits are new and unpushed, so a normal push works.'),
        title='Steps to Pull Cleanly'),
    crossq(
        ('Is pull --rebase a violation of the golden rule?', 'No: it rewrites only your local commits that were never pushed; the shared commits from origin stay untouched.'),
        ('What does pull.ff only do?', 'Pull succeeds only if it can fast-forward; otherwise it stops and lets you decide to merge or rebase.'),
        ('Why does merge-on-pull create noise?', 'Every time two people commit in parallel, a "Merge branch \'main\' of origin" commit appears that carries no meaning of its own.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('Describe the feature-branch / pull-request workflow. How do forks fit in?', 'Pull Request Workflow', minutes=9, cards=[
    definition(
        defbox('In the <strong>feature-branch workflow</strong>, nobody commits directly to <code>main</code>. Each change starts on a branch from an up-to-date '
               'main, is pushed to the shared repository, and a <strong>pull request</strong> (GitHub) / <strong>merge request</strong> (GitLab) asks for review. '
               'CI runs tests; reviewers comment; the author pushes fixes to the same branch; when approved, the branch is merged (merge commit, squash or '
               'rebase) and deleted. Branch protection rules enforce reviews and passing checks.',
               'In the <strong>fork workflow</strong> (open source, student submissions), contributors cannot push to the main repository; they <strong>fork</strong> '
               'it (a server-side clone under their account), push branches to their fork, and open pull requests to the original ("upstream"). They keep the '
               'fork current with <code>git fetch upstream</code> and merging/rebasing <code>upstream/main</code>.'),
        tags('feature branch', 'pull request', 'merge request', 'code review', 'fork', 'upstream', 'branch protection'),
    ),
    analogy('A pull request is <strong>submitting an assignment for evaluation</strong>: you work on your copy, hand it in with a cover note, the faculty '
            'comments, you revise, and only the approved version goes into the final record.'),
    pr_anim(),
    real_world(
        scenario('Student project submissions',
                 p('Each student forks the course project repository, implements the assigned module on a branch in their fork and opens a pull request. Mentors '
                   'review in the PR, CI runs the test-suite, and accepted contributions are merged into the course repository.')),
    ),
    example(
        SETUP, REMOTE_NOTE,
        gitrun(team("""
            !git clone -q --bare ~/server/portal.git ~/server/ravi-fork.git
            cd ravi
            git remote rename origin upstream
            git remote add origin ~/server/ravi-fork.git
            git remote -v
            git switch -q -c feature/results
            echo "results" > results.html && git add . && git commit -q -m "Add results page"
            git push -q -u origin feature/results
            cd ../asha
            git remote add ravi ~/server/ravi-fork.git
            git fetch -q ravi
            git log --oneline main..ravi/feature/results
            git merge --no-ff -q -m "Merge pull request #1 from ravi/feature/results" ravi/feature/results
            git push -q origin main
            cd ../ravi
            git fetch -q upstream
            git switch -q main && git merge -q --ff-only upstream/main
            git log --oneline --graph
        """)),
        title='Example: Fork, Branch, Push to the Fork, "Merge the Pull Request", Sync the Fork'),
    steps(
        ('Sync main', '<code>git switch main && git pull</code> (or fetch upstream for forks).'),
        ('Branch', '<code>git switch -c feature/x</code>; commit in small steps.'),
        ('Push and open a PR', '<code>git push -u origin feature/x</code>, then create the PR on the hosting site.'),
        ('Review and fix', 'Push more commits to the same branch; CI re-runs.'),
        ('Merge and clean up', 'Merge (merge/squash/rebase), delete the branch, pull main.'),
        title='Steps for a Pull Request'),
    crossq(
        ('Is a pull request a Git feature?', 'No; it is a hosting-platform feature built on branches. Git itself only has request-pull, which generates a summary text.'),
        ('origin vs upstream in a fork?', 'origin is your fork (you can push); upstream is the original repository you pull updates from and open PRs to.'),
        ('How do you update an open PR?', 'Commit and push to the same branch; the PR updates automatically.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What are tags? Compare lightweight and annotated tags and explain how they are used for releases.', 'Tags & Releases', minutes=7, cards=[
    definition(
        defbox('A <strong>tag</strong> is a fixed name for a specific commit, typically a release version (<code>v1.2.0</code>). A <strong>lightweight</strong> tag '
               'is just a pointer; an <strong>annotated</strong> tag (<code>git tag -a v1.0 -m "…"</code>) is a full object with tagger, date and message (and '
               'can be signed with <code>-s</code>) — use annotated tags for releases.',
               'Tags are not pushed by default: <code>git push origin v1.0</code> or <code>git push --tags</code>. <code>git describe</code> names a commit '
               'relative to the latest tag (<code>v1.0-2-gabc1234</code>), handy for build numbers. Versions often follow <strong>semantic versioning</strong>: '
               'MAJOR.MINOR.PATCH (breaking, feature, fix).'),
        tags('git tag', 'annotated tag', 'lightweight tag', 'push --tags', 'git describe', 'semantic versioning', 'release'),
    ),
    analogy('A branch is a <strong>bookmark that moves</strong> as you read; a tag is a <strong>sticky note glued to one page</strong> — "the version we '
            'gave to the students on 1 August".'),
    tag_anim(),
    real_world(
        scenario('Exam portal releases',
                 p('Every version deployed for an exam is tagged (<code>v2.3.0</code> for the August CCEE). If a problem is reported later, the team can check out '
                   'exactly that code, compare it with the current version and build a patch release.')),
    ),
    example(
        SETUP, REMOTE_NOTE,
        gitrun(team("""
            cd asha
            git tag v1.0-light
            git tag -a v1.0.0 -m "Release 1.0.0 for CCEE August"
            echo "results" > results.html && git add . && git commit -q -m "Add results page"
            echo "fix" >> results.html && git commit -q -am "Fix results layout"
            git describe
            git tag -n
            git cat-file -t v1.0-light
            git cat-file -t v1.0.0
            git show v1.0.0 --no-patch
            git push -q origin v1.0.0
            git ls-remote --tags origin
            git tag -a v1.1.0 -m "Release 1.1.0: results page" && git describe
        """)),
        title='Example: Lightweight vs Annotated Tags, describe, Pushing a Tag'),
    steps(
        ('Choose the version', 'Semantic versioning: MAJOR.MINOR.PATCH.'),
        ('Create an annotated tag', '<code>git tag -a v1.2.0 -m "notes"</code> (or <code>-s</code> to sign).'),
        ('Push it', '<code>git push origin v1.2.0</code>.'),
        ('Create the release', 'Release notes on GitHub/GitLab from the tag.'),
        ('Use it later', '<code>git checkout v1.2.0</code>, <code>git diff v1.2.0..main</code>, <code>git describe</code>.'),
        title='Steps to Tag a Release'),
    crossq(
        ('Why are my tags not on GitHub?', 'git push does not send tags by default; push them explicitly or use --follow-tags.'),
        ('Lightweight or annotated for releases?', 'Annotated: it records who tagged, when and why, and can be signed; describe uses annotated tags by default.'),
        ('Can you move a tag?', 'Technically with -f, but others who fetched it will not update; treat published tags as immutable and create a new version.'),
    ),
]),
])
