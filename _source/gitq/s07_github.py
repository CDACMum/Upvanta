from build import *
from gitq.anims import *
from gitq.runner import gitrun, sh, script_file
from gitq.s01_foundations import SETUP
from gitq.s04_remotes import REMOTE_NOTE, team

CI_YML = """
name: tests
on:
  push:
    branches: [main]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest -q
"""

SECTION = dict(level='advanced', title='GitHub, Security & Tooling', questions=[

# ------------------------------------------------------------------ 31
Q('How do you authenticate to GitHub? Compare HTTPS with personal access tokens and SSH keys.', 'SSH Keys & Authentication', minutes=8, cards=[
    definition(
        defbox('GitHub no longer accepts account passwords for Git operations. Two options: <strong>HTTPS</strong> with a <strong>personal access token</strong> '
               '(PAT; fine-grained, with an expiry and limited scopes) stored by a credential helper, or <strong>SSH</strong> with a key pair: the '
               '<strong>private key</strong> stays on your machine (never shared, ideally passphrase-protected), the <strong>public key</strong> '
               '(<code>.pub</code>) is added to your GitHub account.',
               '<code>ssh-keygen -t ed25519 -C "email"</code> creates the pair in <code>~/.ssh</code> (permissions 600 on the private key); '
               '<code>ssh -T git@github.com</code> tests it; SSH remote URLs look like <code>git@github.com:user/repo.git</code> and can be switched with '
               '<code>git remote set-url</code>. <code>~/.ssh/config</code> can select different keys per host (e.g. personal vs institute accounts).'),
        tags('HTTPS', 'personal access token', 'SSH', 'ssh-keygen', 'ed25519', 'public / private key', 'remote set-url'),
    ),
    analogy('An SSH key pair is a <strong>padlock and its key</strong>: you hand out copies of the open padlock (public key) to GitHub, which locks a challenge '
            'with it; only your private key can open it. Giving away the key itself is giving away your identity.'),
    ssh_anim(),
    real_world(
        scenario('Lab machines and personal laptops',
                 p('Students push from shared lab PCs and their own laptops. A personal SSH key with a passphrase on the laptop, and a short-lived fine-grained token '
                   'on the lab PC (removed at the end of the session), keep accounts safe; nobody types their GitHub password into Git.')),
    ),
    example(
        SETUP,
        gitrun("""
            ssh-keygen -q -t ed25519 -N "" -C "asha@cdac.example" -f ~/.ssh/id_ed25519
            ls -l ~/.ssh | awk '{print $1, $NF}'
            ssh-keygen -l -f ~/.ssh/id_ed25519.pub | cut -d' ' -f1,3,4
            cut -c1-40 ~/.ssh/id_ed25519.pub
            head -1 ~/.ssh/id_ed25519
            cat > ~/.ssh/config <<'EOF'
            Host github-cdac
                HostName github.com
                User git
                IdentityFile ~/.ssh/id_ed25519
            EOF
            git init -q portal && cd portal
            git remote add origin https://github.com/asha-patil/portal.git
            git remote -v
            git remote set-url origin git@github-cdac:asha-patil/portal.git
            git remote -v
        """, title='Terminal (git 2.43 · OpenSSH)'),
        title='Example: Generate an ed25519 Key, Inspect It, Use an SSH Host Alias'),
    steps(
        ('Generate a key', 'ssh-keygen -t ed25519 -C "your email" (set a passphrase).'),
        ('Add the public key to GitHub', 'Settings → SSH and GPG keys → paste id_ed25519.pub.'),
        ('Test', 'ssh -T git@github.com.'),
        ('Use SSH URLs', 'git clone git@github.com:user/repo.git or git remote set-url.'),
        ('Or use a token for HTTPS', 'Fine-grained PAT with expiry; a credential helper stores it.'),
        title='Steps to Set Up Authentication'),
    crossq(
        ('Why ed25519 rather than RSA?', 'Ed25519 keys are short, fast and secure by default; RSA needs 3072+ bits to be comparable.'),
        ('A private key was committed to a repository. What now?', 'Treat it as compromised: delete the key from GitHub, generate a new one, and remove the file from history; anyone who cloned already has it.'),
        ('Why do PATs have scopes and expiry dates?', 'A leaked token then grants only limited access for a limited time, unlike a password.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('What is continuous integration? How does a GitHub Actions workflow run tests on every push and pull request?', 'GitHub Actions CI', minutes=9, cards=[
    definition(
        defbox('<strong>Continuous integration (CI)</strong> automatically builds and tests every push and pull request, so broken code is caught before it is '
               'merged. <strong>GitHub Actions</strong> reads YAML workflows from <code>.github/workflows/*.yml</code>: <code>on</code> (triggers: push, '
               'pull_request, schedule), <code>jobs</code> (run on GitHub-hosted runners such as <code>ubuntu-latest</code>) and <code>steps</code> (actions like '
               '<code>actions/checkout</code> or shell commands such as <code>pytest</code>).',
               'The result appears as a check (✓ / ✗) on the commit and the pull request; <strong>branch protection</strong> can require the check to pass before '
               'merging. Keep the workflow\'s commands identical to what developers run locally, cache dependencies, and store secrets in repository secrets, '
               'never in the YAML.'),
        tags('continuous integration', 'GitHub Actions', 'workflow YAML', 'on: push / pull_request', 'runner', 'status check', 'branch protection'),
    ),
    analogy('CI is a <strong>quality inspector at the factory door</strong>: every batch (push) is tested automatically, and the gate (branch protection) does not '
            'open for a batch that failed inspection.'),
    ci_anim(),
    real_world(
        scenario('Group project with five students',
                 p('Every pull request runs the test suite on GitHub. When a student\'s change breaks the grade calculation, the PR shows a red ✗ with the failing '
                   'test, and main stays green — the bug never reaches the demo machine.')),
    ),
    example(
        script_file('.github/workflows/ci.yml', CI_YML, '.github/workflows/ci.yml'),
        gitrun("""
            git init -q grades && cd grades
            mkdir -p .github/workflows tests
            cp ../ci.yml .github/workflows/ci.yml
            printf 'def grade(m):\\n    return "P" if m >= 50 else "F"\\n' > grade.py
            printf 'from grade import grade\\n\\ndef test_pass():\\n    assert grade(50) == "P"\\n\\ndef test_fail():\\n    assert grade(49) == "F"\\n' > tests/test_grade.py
            echo "pytest" > requirements.txt
            git add . && git commit -q -m "Add grade function, tests and CI workflow"
            git ls-files
            # what the CI job runs, executed locally:
            python3 -m pytest -q -p no:cacheprovider 2>&1 | tail -1
            git switch -q -c fix/boundary
            sed -i 's/m >= 50/m > 50/' grade.py && git commit -q -am "Change boundary check"
            python3 -m pytest -q -p no:cacheprovider 2>&1 | grep -E "FAILED|passed|failed"
        """, files={'ci.yml': CI_YML}, title='Terminal (git 2.43 · pytest)'),
        title='Example: A Workflow File and the Exact Test Run CI Would Perform on a Bad Change'),
    steps(
        ('Write tests that run with one command', 'pytest -q locally.'),
        ('Add a workflow', '.github/workflows/ci.yml with on, jobs, steps.'),
        ('Push and watch the Actions tab', 'Fix until green.'),
        ('Protect main', 'Require the status check to pass before merging pull requests.'),
        ('Keep secrets out of YAML', 'Use repository secrets: ${{ secrets.NAME }}.'),
        title='Steps to Set Up CI'),
    crossq(
        ('CI passes but the code still breaks in production. Why?', 'Tests only cover what they test; CI is as good as the test suite, environment parity and data used.'),
        ('Push trigger vs pull_request trigger?', 'push runs on commits to the listed branches; pull_request runs on the merge result of a PR before it is merged.'),
        ('Why pin action versions (@v4)?', 'An unpinned or moving tag could change behaviour or be compromised; pinning makes runs reproducible.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('How do you work with large repositories efficiently? Explain shallow and partial clones, sparse checkout and git worktree.', 'Large Repos: Shallow, Sparse & Worktrees', minutes=8, cards=[
    definition(
        defbox('<strong>Shallow clone</strong> <code>git clone --depth 1</code> downloads only the latest commit(s): fast for CI and quick reads, but no full '
               'history. <strong>Partial clone</strong> <code>--filter=blob:none</code> downloads history but fetches file contents on demand. '
               '<strong>Sparse checkout</strong> (<code>git sparse-checkout set dir1 dir2</code>) puts only chosen folders in the working directory — useful in '
               'monorepos.',
               '<code>git worktree add ../path branch</code> checks out <strong>another branch in a second folder</strong> that shares the same repository: '
               'review a pull request or build a hotfix without stashing or re-cloning; <code>git worktree list / remove</code> manage them.'),
        tags('shallow clone', '--depth', 'partial clone', '--filter=blob:none', 'sparse-checkout', 'git worktree', 'monorepo'),
    ),
    analogy('A shallow clone is <strong>borrowing only today\'s newspaper</strong> instead of the whole archive; sparse checkout is <strong>reading only the sports '
            'pages</strong>; a worktree is <strong>a second desk</strong> where another edition lies open next to yours.'),
    worktree_anim(),
    real_world(
        scenario('Hotfix during a long feature',
                 p('Halfway through a large refactor, a bug in the live results portal needs fixing. Instead of stashing everything, the developer runs git worktree '
                   'add ../hotfix main, fixes and pushes from that folder, and returns to the refactor untouched.')),
    ),
    example(
        gitrun("""
            !git init -q big && cd big && mkdir -p spark hive web && for i in $(seq 1 20); do echo "v$i" > spark/job.py; echo "v$i" > hive/q.sql; echo "v$i" > web/index.html; git add .; git commit -q -m "Change $i"; done && cd ..
            git -C big log --oneline | wc -l
            git clone -q --depth 1 file://$PWD/big shallow
            git -C shallow log --oneline
            git -C shallow rev-parse --is-shallow-repository
            git clone -q --no-checkout file://$PWD/big sparse && cd sparse
            git sparse-checkout set spark
            git checkout -q main
            ls
            cd ../big
            git worktree add -q ../big-hotfix -b hotfix/title HEAD~1
            git worktree list | sed "s|$HOME|~|"
            cd ../big-hotfix && echo "fixed" > web/index.html && git commit -q -am "Fix page title" && cd ../big
            git log --oneline -1 hotfix/title
            git worktree remove ../big-hotfix
            git worktree list | sed "s|$HOME|~|"
        """, title='Terminal (git 2.43)'),
        title='Example: Shallow Clone, Sparse Checkout of One Folder, a Second Worktree for a Hotfix'),
    steps(
        ('CI or quick reads', 'git clone --depth 1.'),
        ('Huge repos with big files', 'git clone --filter=blob:none (partial clone).'),
        ('Only some folders', 'git sparse-checkout set path …'),
        ('Two branches at once', 'git worktree add ../dir branch; remove when done.'),
        ('Deepen later if needed', 'git fetch --unshallow.'),
        title='Steps for Large Repositories'),
    crossq(
        ('What can you not do in a shallow clone?', 'Commands needing old history (log beyond the depth, blame, bisect, some merges) are limited until you deepen with fetch --unshallow.'),
        ('Worktree vs a second clone?', 'Worktrees share one object database and refs, so they use less disk and see each other\'s branches immediately; the same branch cannot be checked out in two worktrees.'),
        ('Does sparse checkout reduce the download?', 'Not by itself; combine with a partial clone (--filter=blob:none) to avoid downloading file contents outside the chosen folders.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('A password was committed. How do you find it, remove it from history, and what else must you do?', 'Secrets in History', minutes=9, cards=[
    definition(
        defbox('A secret committed to Git stays in the <strong>history</strong> even after you delete the file in a new commit. Find it with '
               '<code>git log -p -S "secret"</code> or <code>git grep</code> on old revisions. If the commit is <strong>not pushed</strong>, '
               '<code>git commit --amend</code> or an interactive rebase removes it cleanly.',
               'If it was <strong>pushed</strong>, assume it is compromised: <strong>rotate/revoke the credential first</strong>. Then rewrite history with '
               '<code>git filter-repo</code> (recommended tool) or BFG / <code>git filter-branch</code>, force-push, and ask everyone to re-clone; forks, caches '
               'and clones may still hold it. Prevent repeats with .gitignore for .env files, pre-commit secret scanners (gitleaks, detect-secrets) and GitHub '
               'push protection.'),
        tags('secrets', 'git log -S', 'rotate credentials', 'filter-repo', 'filter-branch', 'force push', 'secret scanning'),
    ),
    analogy('Pushing a password is like <strong>posting a house key</strong>: retrieving the envelope later does not help if someone already copied the key. '
            '<strong>Change the lock first</strong>, then clean up the post.'),
    secret_anim(),
    real_world(
        scenario('Database password in config.py',
                 p('A student pushed config.py with the MySQL password of the project server. The coordinator changes the password immediately, the student rewrites '
                   'history to remove the file, force-pushes, and the team re-clones; a pre-commit hook and .gitignore entry stop it happening again.')),
    ),
    example(
        gitrun("""
            !git init -q api && cd api && echo "app" > app.py && git add . && git commit -q -m "Add app"
            !echo 'DB_PASSWORD = "Cdac@2026"' > config.py && git add . && git commit -q -m "Add config"
            !echo "routes" >> app.py && git commit -q -am "Add routes"
            !git rm -q config.py && git commit -q -m "Remove config"
            !cd ..
            cd api
            ls
            git log --oneline
            git log --oneline -S "DB_PASSWORD"
            git show HEAD~2:config.py
            git filter-branch -f --index-filter 'git rm -q --cached --ignore-unmatch config.py' --prune-empty HEAD 2>&1 | tail -1
            git log --oneline
            git log --all --oneline -S "DB_PASSWORD"
            git for-each-ref --format='%(refname)' refs/original/
            git update-ref -d refs/original/refs/heads/main
            git reflog expire --expire=now --all && git gc -q --prune=now
            git log --all --oneline -S "DB_PASSWORD" | wc -l
            echo "config.py" >> .gitignore
        """, title='Terminal (git 2.43)'),
        title='Example: Find the Password in History, Rewrite It Away, Clean Up the Backups'),
    steps(
        ('Rotate the secret immediately', 'Before anything else, if it was ever pushed.'),
        ('Find every occurrence', 'git log -p -S "secret" --all.'),
        ('Rewrite history', 'git filter-repo --path config.py --invert-paths (or filter-branch / BFG).'),
        ('Force-push and coordinate', 'git push --force-with-lease; everyone re-clones.'),
        ('Prevent', '.gitignore, environment variables, secret-scanning hooks, push protection.'),
        title='Steps to Handle a Leaked Secret'),
    crossq(
        ('Why is deleting the file in a new commit not enough?', 'Every earlier commit still contains it; anyone can check out or git show the old version.'),
        ('Why does filter-branch keep refs/original?', 'It is a backup of the old history; until it (and the reflog) is removed and garbage-collected, the secret is still in the repository.'),
        ('Is rewriting history enough after a public push?', 'No. Clones, forks, CI caches and archives may already have it, which is why the credential must be rotated.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How do you version Jupyter notebooks and data science projects with Git? Explain output stripping, clean filters and data versioning.', 'Git for Notebooks & Data', minutes=9, cards=[
    definition(
        defbox('Notebooks (<code>.ipynb</code>) are JSON with code, outputs (often base64 images) and execution counts. Committing outputs makes diffs unreadable, '
               'repositories huge and merges conflict-prone. Common practice: <strong>strip outputs before committing</strong> — manually ("Clear all outputs"), '
               'with tools such as <code>nbstripout</code>, or with a Git <strong>clean filter</strong> declared in <code>.gitattributes</code> '
               '(<code>*.ipynb filter=nbclean</code>) and configured with <code>git config filter.nbclean.clean "command"</code>. A filter rewrites what Git '
               'stores while leaving your working copy untouched.',
               'Large data does not belong in Git: keep it in storage (drive, S3, HDFS) and version it with <strong>DVC</strong> or <strong>Git LFS</strong>, which '
               'store small pointer files in Git and the data elsewhere. Pair notebooks with scripts (Jupytext) for reviewable diffs.'),
        tags('Jupyter notebooks', 'nbstripout', 'clean filter', '.gitattributes', 'DVC', 'Git LFS', 'reproducibility'),
    ),
    analogy('A notebook with outputs is a <strong>recipe book with a photo of every dish glued in</strong>: the photos make the book heavy and every new photo '
            'looks like a change. Commit the recipe; keep the photos elsewhere.'),
    nb_anim(),
    real_world(
        scenario('The 25 MB notebook',
                 p('An EDA notebook with dozens of embedded charts grows to 25 MB; every re-run changes thousands of JSON lines and two teammates\' edits always '
                   'conflict. A clean filter strips outputs on commit: the repository stores only code and markdown, diffs show real changes, and the charts are '
                   'regenerated by running the notebook.')),
    ),
    example(
        gitrun("""
            git init -q eda && cd eda
            cat > ../nbclean.py <<'EOF'
            import json, sys
            nb = json.load(sys.stdin)
            for cell in nb["cells"]:
                if cell["cell_type"] == "code":
                    cell["outputs"], cell["execution_count"] = [], None
            json.dump(nb, sys.stdout, indent=1)
            EOF
            git config filter.nbclean.clean "python3 $HOME/cdac/nbclean.py"
            echo "*.ipynb filter=nbclean" > .gitattributes
            python3 ../make_nb.py > eda.ipynb
            wc -c eda.ipynb
            git add . && git commit -q -m "Add EDA notebook"
            git cat-file -s HEAD:eda.ipynb
            git show HEAD:eda.ipynb | grep -c '"outputs": \\[\\]'
            python3 ../make_nb.py rerun > eda.ipynb
            git status --short
            git diff --stat | wc -l
            git add eda.ipynb && git status --short | wc -l
            sed -i 's/head()/describe()/' eda.ipynb
            git diff --stat
            git diff | grep -E '^[-+] '
        """, files={'make_nb.py': """
            import json, sys, base64
            run = 2 if 'rerun' in sys.argv else 1
            img = base64.b64encode(bytes(range(256)) * 40 * run).decode()
            cells = [{"cell_type": "markdown", "metadata": {}, "source": ["# Placement EDA"]},
                     {"cell_type": "code", "metadata": {}, "execution_count": run, "source": ["df.head()"],
                      "outputs": [{"output_type": "display_data", "metadata": {}, "data": {"image/png": img}}]}]
            print(json.dumps({"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}, indent=1))
        """}, title='Terminal (git 2.43 · Python)'),
        title='Example: A Clean Filter That Stores Notebooks Without Outputs'),
    steps(
        ('Strip outputs on commit', 'nbstripout --install, or a clean filter in .gitattributes.'),
        ('Keep data out of Git', '.gitignore data/; DVC or Git LFS for versioned datasets.'),
        ('Make notebooks reproducible', 'Fixed seeds, requirements.txt, relative paths.'),
        ('Review notebook changes', 'Jupytext pairing or nbdime for readable diffs.'),
        ('Move stable code into modules', 'Import functions from .py files; notebooks stay thin.'),
        title='Steps for Data-Science Repositories'),
    crossq(
        ('After the re-run, why did git status show M but git diff show nothing?', 'git status first compares file size and timestamps, and the file did grow. Comparing content (git diff, git add) runs the clean filter, and the cleaned version is identical, so git add leaves nothing to commit.'),
        ('Git LFS vs DVC?', 'LFS stores large files on a Git-aware server transparently; DVC adds data pipelines and stores data in your own remote storage (S3, drive), tracking versions with small .dvc files.'),
        ('Is it ever right to commit outputs?', 'For published reports or teaching material where the rendered result is the point — ideally in a separate, generated artefact.'),
    ),
]),
])
