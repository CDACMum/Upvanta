from build import *
from gitq.anims import *
from gitq.runner import gitrun, sh
from gitq.s01_foundations import SETUP

SECTION = dict(level='advanced', title='Team Workflows & Practices', questions=[

# ------------------------------------------------------------------ 26
Q('Compare branching strategies: Git Flow, GitHub Flow and trunk-based development.', 'Branching Strategies', minutes=9, cards=[
    definition(
        defbox('<strong>Git Flow</strong>: long-lived <code>main</code> (released code) and <code>develop</code> (integration), plus <code>feature/*</code> '
               'from develop, <code>release/*</code> for stabilising a version and <code>hotfix/*</code> from main merged back into both. Suits scheduled, '
               'versioned releases (installed software, mobile apps) but has many merges and long-lived branches.',
               '<strong>GitHub Flow</strong>: one long-lived <code>main</code> that is always deployable; short feature branches, pull requests, merge, deploy. '
               '<strong>Trunk-based development</strong>: everyone integrates into main at least daily via very short branches (or directly), with unfinished '
               'work hidden behind <strong>feature flags</strong>; requires strong automated testing and suits continuous delivery. The trend is towards '
               'shorter-lived branches: fewer conflicts, faster feedback.'),
        tags('Git Flow', 'develop branch', 'release branch', 'hotfix', 'GitHub Flow', 'trunk-based', 'feature flags'),
    ),
    analogy('Git Flow is a <strong>publishing house</strong> with drafts, editions and errata; GitHub Flow is a <strong>blog</strong> where each reviewed post '
            'goes live; trunk-based is a <strong>live newsroom</strong> where everyone updates the same page constantly, with unfinished stories hidden until '
            'ready.'),
    flow_anim(),
    real_world(
        scenario('Choosing for two projects',
                 p('The exam-portal team ships fixed versions before each exam cycle and supports the previous one, so it uses a Git Flow-like model with release '
                   'and hotfix branches. The internal attendance dashboard deploys several times a day and uses GitHub Flow with short branches and CI.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q flow && cd flow && echo "1.0" > VERSION && git add . && git commit -q -m "Release 1.0" && git tag -a v1.0 -m v1.0 && cd ..
            cd flow
            git switch -q -c develop
            git switch -q -c feature/login develop && echo login > login.py && git add . && git commit -q -m "Add login"
            git switch -q develop && git merge -q --no-ff -m "Merge feature/login" feature/login
            git switch -q -c release/1.1 develop && echo "1.1" > VERSION && git commit -q -am "Bump version to 1.1"
            git switch -q main && git merge -q --no-ff -m "Release 1.1" release/1.1 && git tag -a v1.1 -m v1.1
            git switch -q develop && git merge -q --no-ff -m "Merge release/1.1 back" release/1.1
            git switch -q -c hotfix/1.1.1 main && echo "1.1.1" > VERSION && git commit -q -am "Fix exam timer (1.1.1)"
            git switch -q main && git merge -q --no-ff -m "Hotfix 1.1.1" hotfix/1.1.1 && git tag -a v1.1.1 -m v1.1.1
            git switch -q develop && git merge -q --no-ff -m "Merge hotfix/1.1.1 back" hotfix/1.1.1
            git log --oneline --graph --all --decorate=short --format='%h %s%d'
        """),
        title='Example: A Compact Git Flow — Feature, Release, Hotfix, Tags'),
    steps(
        ('Assess release style', 'Versioned releases vs continuous deployment.'),
        ('Assess team and tests', 'Strong CI and small changes favour trunk-based / GitHub Flow.'),
        ('Pick the model and document it', 'Branch names, who merges, how releases are tagged.'),
        ('Protect key branches', 'Required reviews and checks on main (and develop).'),
        ('Keep branches short-lived', 'Whatever the model, merge often.'),
        title='Steps to Choose a Branching Strategy'),
    crossq(
        ('Why must hotfixes go into both main and develop in Git Flow?', 'Otherwise the fix would be lost in the next release made from develop.'),
        ('What makes trunk-based development safe?', 'Small commits, fast automated tests, code review and feature flags that hide incomplete work in production.'),
        ('What is the main cost of long-lived branches?', 'They drift from main, leading to large, risky merges and late feedback ("merge hell").'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('How do merge commit, squash merge and rebase merge differ when merging a pull request?', 'PR Merge Methods', minutes=9, cards=[
    definition(
        defbox('Hosting platforms offer three ways to merge a PR. <strong>Merge commit</strong> (<code>git merge --no-ff</code>): keeps every feature commit and '
               'adds a merge commit — full history, easy to revert the whole feature. <strong>Squash and merge</strong> (<code>git merge --squash</code> + commit): '
               'turns the whole branch into <strong>one</strong> commit on main — clean, one commit per PR, but individual steps are lost and the branch is not '
               'recorded as merged.',
               '<strong>Rebase and merge</strong>: replays each feature commit onto main without a merge commit — linear history with all commits, but new hashes. '
               'Teams usually pick one method per repository; squash suits noisy PR branches, merge commits suit large features, rebase suits curated commit '
               'series.'),
        tags('merge commit', 'squash merge', 'rebase merge', 'merge --squash', 'linear history', 'revert a PR'),
    ),
    analogy('Three ways to file a student\'s project in the archive: <strong>the whole folder with a cover sheet</strong> (merge commit), <strong>only the final '
            'report</strong> (squash), or <strong>every draft re-dated and filed in sequence</strong> (rebase).'),
    methods_anim(),
    real_world(
        scenario('Course repository policy',
                 p('Student PRs often contain "fix", "fix 2", "final final". The course repository allows only squash merges, so main has one clear commit per '
                   'assignment with the PR title as message, and reverting a bad submission is one command.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q m && cd m && echo base > base.txt && git add . && git commit -q -m "Base" && cd ..
            !cd m && for b in merge squash rebase; do git switch -q -c pr-$b main; for i in 1 2; do echo "$b $i" >> $b.txt; git add .; git commit -q -m "$b step $i"; done; done && git switch -q main && cd ..
            cd m
            git merge -q --no-ff -m "Merge PR: merge commit" pr-merge
            git merge -q --squash pr-squash && git commit -q -m "PR: squash merge (2 commits squashed)"
            git rebase -q main pr-rebase && git switch -q main && git merge -q --ff-only pr-rebase
            git log --oneline --graph
            git branch --merged main
            git branch --no-merged main
        """),
        title='Example: Three Feature Branches Merged Three Ways into main'),
    steps(
        ('Agree on one method per repository', 'Configure it in the hosting settings.'),
        ('Squash for noisy branches', 'Write a good final message (PR title + summary).'),
        ('Merge commit for big features', 'Keeps the feature grouped and revertible with -m 1.'),
        ('Rebase merge for curated commits', 'Each commit must build and be meaningful.'),
        ('Delete merged branches', 'Locally and on the server.'),
        title='Steps to Choose a PR Merge Method'),
    crossq(
        ('Why is pr-squash listed as not merged?', 'A squash merge creates a brand-new commit; the branch\'s own commits are not ancestors of main, so Git cannot tell it was merged.'),
        ('How do you revert a whole PR that was merged with a merge commit?', 'git revert -m 1 <merge-commit>, which undoes the changes relative to the first parent (main).'),
        ('What is lost with squash merges?', 'The individual commit history (useful for bisect and blame inside the feature) and the merged status of the branch.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What are Git hooks? Write pre-commit and commit-msg hooks.', 'Git Hooks', minutes=8, cards=[
    definition(
        defbox('<strong>Hooks</strong> are scripts Git runs at certain points; a non-zero exit code from a "pre" hook aborts the operation. Client-side: '
               '<code>pre-commit</code> (check staged files: lint, tests, secrets), <code>commit-msg</code> (validate the message), <code>pre-push</code> '
               '(run tests before pushing), <code>post-merge</code>. Server-side (<code>pre-receive</code>, <code>update</code>) enforce policies for everyone.',
               'Hooks live in <code>.git/hooks</code>, which is <strong>not versioned</strong>. To share them, keep them in the repository (e.g. '
               '<code>.githooks/</code>) and set <code>git config core.hooksPath .githooks</code>, or use the <strong>pre-commit</strong> framework / Husky. Client '
               'hooks can be skipped with <code>--no-verify</code>, so important rules must also run in CI.'),
        tags('hooks', 'pre-commit', 'commit-msg', 'pre-push', 'core.hooksPath', '--no-verify', 'pre-receive'),
    ),
    analogy('Hooks are <strong>security checks at the exit gate</strong>: before anything leaves your desk as a commit, the guard inspects it. A determined '
            'person can climb the fence (--no-verify), so the server (CI) has its own guard too.'),
    hooks_anim(),
    real_world(
        scenario('No passwords, consistent messages',
                 p('The project repository ships a <code>.githooks/</code> folder: pre-commit rejects files containing "password=" or debug prints, commit-msg '
                   'requires the "type: summary" format. New members run one config command and get the checks automatically.')),
    ),
    example(
        SETUP,
        gitrun("""
            git init -q hooked && cd hooked
            mkdir .githooks
            printf '#!/bin/sh\\nif git diff --cached -- . ":(exclude).githooks" | grep -qiE "^\\\\+.*(password=|print\\\\()"; then\\n  echo "pre-commit: remove passwords/print() before committing" >&2; exit 1\\nfi\\n' > .githooks/pre-commit
            printf '#!/bin/sh\\nif ! grep -qE "^(feat|fix|docs|test|chore)(\\\\(.+\\\\))?: .{3,}" "$1"; then\\n  echo "commit-msg: use \\x27type: summary\\x27 (feat, fix, docs, test, chore)" >&2; exit 1\\nfi\\n' > .githooks/commit-msg
            chmod +x .githooks/*
            cat .githooks/pre-commit
            git config core.hooksPath .githooks
            echo 'db_password=secret123' > config.ini && git add config.ini
            git commit -m "feat: add config"
            git rm -q --cached config.ini && rm config.ini
            echo 'def grade(m): return m >= 50' > grade.py && git add grade.py
            git commit -m "added stuff"
            git commit -q -m "feat: add grade function" && git log --oneline
            git add .githooks && git commit -q -m "chore: share git hooks" && git ls-files
        """),
        title='Example: Versioned Hooks that Block a Secret and a Bad Commit Message'),
    steps(
        ('Write the hook script', 'Exit non-zero to block; print a helpful message to stderr.'),
        ('Make it executable', '<code>chmod +x</code>.'),
        ('Version it', 'Store in <code>.githooks/</code>, set <code>core.hooksPath</code>.'),
        ('Or use a framework', 'pre-commit (Python), Husky (Node) with shared config.'),
        ('Back it with CI', 'The same checks on the server, since hooks can be skipped.'),
        title='Steps to Add Git Hooks'),
    crossq(
        ('Why are hooks in .git/hooks not shared by clone?', '.git is not versioned; sharing arbitrary executable scripts automatically would be a security risk. core.hooksPath opts in explicitly.'),
        ('Can a developer bypass hooks?', 'Yes, git commit --no-verify skips pre-commit and commit-msg; that is why the same rules must run in CI or server-side hooks.'),
        ('What input does commit-msg receive?', 'The path to a temporary file containing the proposed message ($1).'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('How do you handle line endings, binary files and large files? Explain .gitattributes, core.autocrlf and Git LFS.', '.gitattributes & Large Files', minutes=8, cards=[
    definition(
        defbox('Windows uses CRLF line endings, Linux/macOS LF; mixed endings create noisy diffs ("every line changed"). <code>.gitattributes</code> fixes this per '
               'repository: <code>* text=auto</code> normalises text files to LF in the repository; <code>*.sh text eol=lf</code> and '
               '<code>*.bat text eol=crlf</code> force checkout endings; <code>*.png binary</code> prevents diffs and merges. The per-user '
               '<code>core.autocrlf</code> (<code>true</code> on Windows, <code>input</code> elsewhere) is the older, less reliable alternative.',
               'Git stores every version of every file, so large binaries (datasets, videos, models) bloat history permanently. Keep them out (.gitignore, '
               'external storage) or use <strong>Git LFS</strong>, which stores small pointer files in Git and the content on an LFS server '
               '(<code>git lfs track "*.csv"</code> writes a .gitattributes rule).'),
        tags('.gitattributes', 'text=auto', 'eol=lf', 'CRLF / LF', 'core.autocrlf', 'binary', 'Git LFS'),
    ),
    analogy('.gitattributes is a <strong>packing instruction sheet</strong>: "fold these clothes the Linux way, keep these photos flat, and do not try to merge '
            'two photos". LFS is <strong>sending the furniture by truck</strong> and putting only the delivery receipt in the parcel.'),
    attrs_anim(),
    real_world(
        scenario('Mixed Windows and Linux lab machines',
                 p('Students edit shell scripts on Windows laptops and run them on the Linux cluster; CRLF endings make <code>bash</code> fail with '
                   '<code>$\'\\r\': command not found</code>. A committed <code>.gitattributes</code> with <code>*.sh text eol=lf</code> fixes it for everyone.')),
    ),
    example(
        SETUP,
        gitrun("""
            git init -q eol && cd eol
            printf 'echo hello\\r\\n' > run.sh
            printf 'PNG\\0\\0binary' > logo.png
            printf '* text=auto\\n*.sh text eol=lf\\n*.png binary\\n' > .gitattributes
            git add . && git commit -q -m "Add files with attributes"
            git ls-files --eol
            git check-attr -a run.sh logo.png
            echo "change" >> logo.png && git diff --stat logo.png && git diff logo.png | tail -1
            git cat-file -p HEAD:run.sh | od -c | head -2
            du -sh .git/objects
        """),
        title='Example: Normalised Line Endings, Binary Attributes and check-attr'),
    steps(
        ('Add .gitattributes early', '<code>* text=auto</code> plus explicit eol rules for scripts.'),
        ('Mark binaries', '<code>*.png binary</code>, <code>*.xlsx binary</code>.'),
        ('Renormalise existing files', '<code>git add --renormalize .</code> and commit.'),
        ('Keep large files out of history', '.gitignore, data stores, or Git LFS.'),
        ('Check', '<code>git ls-files --eol</code>, <code>git check-attr -a file</code>.'),
        title='Steps to Handle Line Endings and Binaries'),
    crossq(
        ('Why prefer .gitattributes over core.autocrlf?', 'It is committed with the repository, so the rules apply to everyone, independent of each developer\'s settings.'),
        ('Why is committing a 500 MB dataset a problem even after deleting it?', 'It stays in history forever, so every clone downloads it; removing it requires rewriting history.'),
        ('What does "binary" do in .gitattributes?', 'It sets -text -diff -merge: no line-ending conversion, no textual diff, no line-based merge.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What are Conventional Commits and semantic versioning? How do you produce a changelog from history?', 'Commit Conventions & Changelogs', minutes=8, cards=[
    definition(
        defbox('<strong>Conventional Commits</strong> standardise messages as <code>type(scope): summary</code>, with types such as <code>feat</code> (new '
               'feature), <code>fix</code> (bug fix), <code>docs</code>, <code>test</code>, <code>refactor</code>, <code>chore</code>, and '
               '<code>BREAKING CHANGE:</code> in the footer (or <code>feat!:</code>). Machines can then read the history.',
               'Combined with <strong>semantic versioning</strong> (MAJOR.MINOR.PATCH), tools derive the next version automatically: a breaking change bumps '
               'MAJOR, a <code>feat</code> MINOR, a <code>fix</code> PATCH; and they generate changelogs grouped by type (semantic-release, commitizen, '
               'release-please). Plain Git already helps: <code>git log v1.0..HEAD --grep "^feat"</code>, <code>git shortlog</code>.'),
        tags('Conventional Commits', 'feat / fix', 'BREAKING CHANGE', 'semantic versioning', 'changelog', 'git shortlog'),
    ),
    analogy('Conventional commits are <strong>labelled boxes in a store room</strong>: because every box says "feature", "fix" or "breaking", the release '
            'manager can count them and write the inventory (changelog) without opening each one.'),
    convention_anim(),
    real_world(
        scenario('Release notes for the exam portal',
                 p('Before each exam cycle, the team generates release notes from the commits since the last tag: new features, bug fixes and any breaking changes '
                   'for the examination cell, with the next version number derived from the commit types.')),
    ),
    example(
        SETUP,
        gitrun("""
            !git init -q rel && cd rel && echo 1 > v && git add . && git commit -q -m "chore: initial release" && git tag -a v1.4.2 -m v1.4.2
            !for m in "feat(results): add PDF download" "fix(timer): use IST for exam end time" "docs: update admin guide" "fix(login): handle expired sessions" "feat(admin)!: replace CSV upload with Excel upload"; do echo "$m" >> log; git add .; git commit -q -m "$m"; done
            !git -c user.name="Ravi Kumar" commit -q --allow-empty -m "test: add timer tests"
            !cd ..
            cd rel
            git log --oneline v1.4.2..HEAD
            echo "## Features"; git log v1.4.2..HEAD --format='- %s' --grep='^feat' | sed 's/^- feat[^:]*: /- /'
            echo "## Fixes"; git log v1.4.2..HEAD --format='- %s' --grep='^fix' | sed 's/^- fix[^:]*: /- /'
            echo "## Breaking"; git log v1.4.2..HEAD --format='- %s' --grep='^[a-z]*(.*)!:' --extended-regexp
            git shortlog -sn v1.4.2..HEAD
        """),
        title='Example: Release Notes and Contributor Counts Generated from Conventional Commits'),
    steps(
        ('Adopt the format', 'type(scope): summary; document allowed types.'),
        ('Enforce it', 'commit-msg hook / commitlint, PR title checks.'),
        ('Tag releases', 'Annotated semantic-version tags.'),
        ('Generate notes', 'git log TAG..HEAD by type, or a release tool.'),
        ('Bump the version', 'Breaking → MAJOR, feat → MINOR, fix → PATCH.'),
        title='Steps to Use Commit Conventions'),
    crossq(
        ('What is the next version after v1.4.2 here?', 'v2.0.0, because one commit is a breaking change (feat(admin)!). Without it, the feats would make it v1.5.0.'),
        ('Are Conventional Commits a Git feature?', 'No; they are a convention on top of Git messages, enforced by hooks and tooling.'),
        ('What does git shortlog -sn show?', 'Number of commits per author in the range, sorted, e.g. for release credits.'),
    ),
]),
])
