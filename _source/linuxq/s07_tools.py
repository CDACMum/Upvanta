from build import *
from linuxq.anims import *
from linuxq.runner import shrun, sh, script_file
from linuxq.data import COMMON, APP_LOG

SECTION = dict(level='advanced', title='Archives, Remote Access & Environment', questions=[

# ------------------------------------------------------------------ 31
Q('How do you archive and compress files? Explain tar, gzip and zip.', 'tar, gzip & zip', minutes=7, cards=[
    definition(
        defbox('<strong>tar</strong> bundles files and directories into one archive, keeping paths, permissions and timestamps; it does not compress by itself. '
               'Flags: <code>c</code> create, <code>x</code> extract, <code>t</code> list, <code>v</code> verbose, <code>f</code> archive file, <code>z</code> gzip, '
               '<code>j</code> bzip2, <code>J</code> xz, <code>-C dir</code> change directory, <code>--exclude</code>.',
               '<strong>gzip/gunzip</strong> compress single files (<code>.gz</code>, replaces the original; <code>-k</code> keeps it); <code>zcat</code>/<code>zgrep</code> '
               'read them directly. <strong>zip/unzip</strong> archive and compress per file, convenient for Windows users.'),
        tags('tar', 'gzip', 'zip', 'compression', 'backup'),
    ),
    analogy('tar is <strong>packing everything into one suitcase</strong>; gzip is <strong>vacuum-sealing</strong> the suitcase so it takes less space. zip packs '
            'and vacuum-seals each item as it goes in.'),
    tar_anim(),
    real_world(
        scenario('Shipping data and code',
                 p('Hadoop and Spark releases arrive as <code>.tgz</code> files extracted with <code>tar -xzf … -C /opt</code>; a batch\'s submissions are archived '
                   'with <code>tar -czf batch_aug26.tar.gz submissions/</code>; old logs are gzipped and searched later with <code>zgrep</code>.')),
    ),
    example(
        shrun("""
            !mkdir -p batch/scripts; cp *.csv batch/; printf 'echo run\\n' > batch/scripts/run.sh; for i in $(seq 1 300); do cat app.log; done > batch/big.log
            du -sh batch
            tar -cf batch.tar batch && tar -czf batch.tar.gz batch
            ls -lh batch.tar batch.tar.gz | awk '{print $5, $9}'
            tar -tzf batch.tar.gz | head -n 4
            mkdir restore && tar -xzf batch.tar.gz -C restore && ls restore/batch
            gzip -k batch/big.log && ls -lh batch/big.log* | awk '{print $5, $9}'
            zgrep -c ERROR batch/big.log.gz
            zip -qr batch.zip batch && unzip -l batch.zip | tail -n 1
        """, files={**COMMON, 'app.log': APP_LOG}),
        title='Example: Archive, Compress, List, Extract, zgrep, zip'),
    steps(
        ('Create', '<code>tar -czf name_$(date +%F).tar.gz dir/</code>.'),
        ('Check', '<code>tar -tzf archive.tar.gz | head</code>.'),
        ('Extract to a place', '<code>tar -xzf archive.tar.gz -C /target</code>.'),
        ('Exclude junk', '<code>--exclude="*.tmp" --exclude=".git"</code>.'),
        ('Read compressed logs', '<code>zcat</code>, <code>zgrep</code>, <code>zless</code>.'),
        title='Steps for Archives'),
    crossq(
        ('Why is the .tar the same size as the data?', 'tar only concatenates files with headers; compression comes from gzip/bzip2/xz.'),
        ('gzip vs bzip2 vs xz?', 'gzip is fastest with moderate compression; bzip2 and xz compress better but slower (xz best ratio).'),
        ('Why can a compressed log be 100× smaller?', 'Logs are highly repetitive text, which compresses extremely well.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('How does SSH work? How do you set up key-based login and copy files with scp/rsync?', 'SSH, Keys, scp & rsync', minutes=8, cards=[
    definition(
        defbox('<strong>SSH</strong> gives an encrypted remote shell (<code>ssh user@host</code>, port 22). <strong>Key-based authentication</strong>: '
               '<code>ssh-keygen -t ed25519</code> creates a private key (<code>~/.ssh/id_ed25519</code>, keep secret, mode 600) and a public key (<code>.pub</code>); '
               'the public key goes into the server\'s <code>~/.ssh/authorized_keys</code> (<code>ssh-copy-id</code>). <code>~/.ssh/config</code> stores host '
               'aliases, users, ports and keys.',
               'File transfer: <code>scp file host:/path</code> (simple copy), <code>rsync -avz src/ host:/dst/</code> (incremental, resumable, can '
               '<code>--delete</code>). <code>ssh -L local:host:port</code> forwards ports (e.g. Jupyter, Spark UI).'),
        tags('ssh', 'ssh-keygen', 'authorized_keys', 'scp', 'rsync', 'port forwarding'),
    ),
    analogy('Your private key is a <strong>personal seal</strong> that never leaves your pocket; the public key is a <strong>wax impression</strong> you give to '
            'the server. When you knock, the server asks you to stamp a fresh piece of wax and checks it matches.'),
    ssh_anim(),
    real_world(
        scenario('Cluster access',
                 p('Students connect to the lab cluster as <code>ssh dbda-lab</code> thanks to a config entry, copy datasets with <code>rsync -avz data/ dbda-lab:data/</code> '
                   '(only changed files are sent), and open the Spark UI with <code>ssh -L 4040:localhost:4040 dbda-lab</code>. Hadoop\'s start scripts need '
                   'passwordless SSH between nodes.')),
    ),
    example(
        shrun("""
            ssh-keygen -t ed25519 -N '' -C 'student@cdac' -f ~/.ssh/id_ed25519 -q
            ls -l ~/.ssh
            cut -c1-40 ~/.ssh/id_ed25519.pub
            cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys
            stat -c '%a %n' ~/.ssh ~/.ssh/authorized_keys
            cat > ~/.ssh/config <<'EOF'
            Host dbda-lab
                HostName 10.0.0.50
                User student
                IdentityFile ~/.ssh/id_ed25519
            EOF
            ssh -G dbda-lab 2>/dev/null | grep -E '^(hostname|user|port|identityfile) '
            mkdir -p src dst; seq 1 1000 > src/a.txt; seq 1 5 > src/b.txt
            rsync -av src/ dst/ | tail -n 3
            echo 6 >> src/b.txt; rsync -av src/ dst/ | grep -v '^$'
        """),
        sh("""
            ssh-copy-id dbda-lab                         # install your public key on the server
            ssh dbda-lab                                 # log in (no password)
            scp marks.csv dbda-lab:/home/student/data/   # copy a file
            rsync -avz --progress data/ dbda-lab:data/   # sync a folder (only changes)
            ssh -L 8888:localhost:8888 dbda-lab          # tunnel Jupyter to http://localhost:8888
        """, title='Shell (against a real server)'),
        title='Example: Keys, Permissions, a Host Alias, and rsync Sending Only Changes'),
    steps(
        ('Generate a key', '<code>ssh-keygen -t ed25519</code> (use a passphrase on personal machines).'),
        ('Install it', '<code>ssh-copy-id user@host</code>.'),
        ('Add a config alias', 'Host, HostName, User, IdentityFile.'),
        ('Fix permissions', '<code>chmod 700 ~/.ssh; chmod 600 ~/.ssh/id_* ~/.ssh/authorized_keys</code>.'),
        ('Copy data', '<code>rsync -avz</code> for folders, <code>scp</code> for single files.'),
        title='Steps to Set Up SSH Access'),
    crossq(
        ('Why does ssh still ask for a password?', 'Usually permissions: ~/.ssh or authorized_keys writable by group/others, wrong owner, or the key not offered (check ssh -v).'),
        ('Why did the second rsync send only b.txt?', 'rsync compares size and modification time and transfers only changed files (and only changed blocks over the network).'),
        ('scp vs rsync?', 'scp always copies everything; rsync is incremental, resumable, can delete extras and preserve attributes, so it is preferred for directories.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What are the basic networking commands? How do you check whether a service is listening on a port?', 'Networking Basics', minutes=8, cards=[
    definition(
        defbox('<code>ip addr</code> (or <code>hostname -I</code>) shows interfaces and IPs; <code>ip route</code> the routing table; <code>ss -tlnp</code> lists '
               'listening TCP ports with processes (older: <code>netstat -tlnp</code>); <code>curl</code> makes HTTP requests (<code>-I</code> headers, <code>-s</code> '
               'silent, <code>-o</code> output); <code>ping</code> and <code>traceroute</code> test reachability; <code>nc -zv host port</code> tests a TCP port; '
               '<code>/etc/hosts</code> and DNS (<code>dig</code>, <code>nslookup</code>) resolve names.',
               'Errors: <strong>connection refused</strong> = host reachable, nothing listening; <strong>timeout</strong> = blocked by firewall or wrong route.'),
        tags('ip', 'ss', 'curl', 'ports', '/etc/hosts', 'troubleshooting'),
    ),
    analogy('An IP address is a <strong>building address</strong>, a port is an <strong>office number</strong> inside it. "Refused" means you reached the '
            'building but nobody is in that office; "timed out" means the gate guard (firewall) never let you in.'),
    net_anim(),
    real_world(
        scenario('"Spark UI not opening"',
                 p('<code>ss -tlnp | grep 4040</code> shows the driver listening only on 127.0.0.1, so it is reachable from the server but not from a laptop; '
                   'an SSH tunnel or binding to 0.0.0.0 fixes it. <code>curl -I</code> confirms the HDFS UI on 9870 answers before blaming the browser.')),
    ),
    example(
        shrun("""
            hostname -I | awk '{print "my IP:", $1}'
            ip -brief addr show lo
            python3 -m http.server 8000 --bind 127.0.0.1 > web.log 2>&1 &
            sleep 1
            ss -tln | awk 'NR == 1 || /:8000/'
            curl -sI http://127.0.0.1:8000/ | head -n 3
            curl -s http://127.0.0.1:8000/students.csv | head -n 2
            curl -s -o /dev/null -w 'status %{http_code}\\n' http://127.0.0.1:8000/missing.csv
            curl -sS http://127.0.0.1:8001/ ; echo "exit $?"
            grep localhost /etc/hosts
            kill %1
        """, files=COMMON),
        title='Example: Start a Small Web Server, Then Inspect It Like Any Service'),
    steps(
        ('Is it running?', '<code>systemctl status</code> / <code>pgrep -af</code>.'),
        ('Is it listening, and where?', '<code>ss -tlnp | grep PORT</code> (0.0.0.0 vs 127.0.0.1).'),
        ('Does it answer locally?', '<code>curl -I http://localhost:PORT</code>.'),
        ('From another machine?', '<code>nc -zv host PORT</code>; check firewall/security groups.'),
        ('Names', '<code>getent hosts name</code>, /etc/hosts, DNS.'),
        title='Steps to Debug a Connection'),
    crossq(
        ('What does listening on 127.0.0.1 vs 0.0.0.0 mean?', '127.0.0.1 accepts only local connections; 0.0.0.0 accepts on all interfaces (reachable from the network, subject to firewalls).'),
        ('Why do Hadoop nodes need correct /etc/hosts or DNS?', 'Daemons register and contact each other by hostname; wrong resolution makes DataNodes or NodeManagers unreachable.'),
        ('What is curl exit code 7?', 'Failed to connect to host (e.g. connection refused).'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How do you set up a Linux environment for Hadoop/Spark (Java, JAVA_HOME, PATH, alternatives)?', 'Big-Data Environment Setup', minutes=8, cards=[
    definition(
        defbox('Big-data tools need: a supported <strong>Java</strong> (check <code>java -version</code>; manage several with <code>update-alternatives</code>), '
               '<strong>JAVA_HOME</strong> pointing to the JDK, the software unpacked (commonly under <code>/opt</code>, behind a symlink), <strong>HOME variables</strong> '
               '(<code>HADOOP_HOME</code>, <code>SPARK_HOME</code>) and their <code>bin</code>/<code>sbin</code> on <strong>PATH</strong>, set in '
               '<code>~/.bashrc</code> (and in the tool\'s <code>*-env.sh</code>), passwordless SSH for start scripts, and correct ownership, open-file limits '
               '(<code>ulimit -n</code>) and hostnames.'),
        tags('JAVA_HOME', 'HADOOP_HOME', 'SPARK_HOME', 'PATH', 'update-alternatives', 'ulimit'),
    ),
    analogy('Setting up the environment is <strong>stocking a new lab</strong>: the right power supply (Java), equipment placed in a known room (/opt), labels '
            'on every door (HOME variables) and the directory of rooms at reception (PATH), so anyone can find what they need.'),
    bigdata_env_anim(),
    real_world(
        scenario('"JAVA_HOME is not set" and "hadoop: command not found"',
                 p('The two most common first-day errors in Hadoop labs. The first: JAVA_HOME missing in <code>hadoop-env.sh</code> or the shell. The second: '
                   '<code>$HADOOP_HOME/bin</code> not on PATH, or <code>.bashrc</code> edited but not sourced. Both are diagnosed with <code>echo</code> and <code>which</code>.')),
    ),
    example(
        shrun("""
            java -version 2>&1 | head -n 1
            readlink -f "$(which java)"
            export JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$(which java)")")"); echo "JAVA_HOME=$JAVA_HOME"
            mkdir -p ~/opt/hadoop-3.4.1/bin && printf '#!/bin/bash\\necho "Hadoop 3.4.1 (demo stub, JAVA_HOME=$JAVA_HOME)"\\n' > ~/opt/hadoop-3.4.1/bin/hadoop && chmod +x ~/opt/hadoop-3.4.1/bin/hadoop
            ln -sfn ~/opt/hadoop-3.4.1 ~/opt/hadoop
            hadoop version
            cat >> ~/.bashrc <<'EOF'
            export JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$(which java)")")")
            export HADOOP_HOME=$HOME/opt/hadoop
            export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
            EOF
            bash -ic 'which hadoop; hadoop version' 2>/dev/null
            ulimit -n
            update-alternatives --list java
        """),
        title='Example: Locate Java, Set JAVA_HOME, Install Behind a Symlink, Configure PATH'),
    steps(
        ('Install Java', 'A version supported by your Hadoop/Spark release (e.g. 11/17).'),
        ('Unpack the software', '<code>sudo tar -xzf hadoop-x.y.z.tar.gz -C /opt; sudo ln -s /opt/hadoop-x.y.z /opt/hadoop</code>.'),
        ('Set variables', 'JAVA_HOME, HADOOP_HOME, SPARK_HOME and PATH in ~/.bashrc (and JAVA_HOME in hadoop-env.sh).'),
        ('Reload and verify', '<code>source ~/.bashrc; which hadoop; hadoop version; java -version</code>.'),
        ('System settings', 'Passwordless SSH, /etc/hosts, ulimit -n ≥ 65536 for services, dedicated users.'),
        title='Steps to Prepare a Node'),
    crossq(
        ('Why derive JAVA_HOME from readlink -f $(which java)?', '/usr/bin/java is a symlink chain (alternatives); resolving it gives the real JDK directory, two levels above bin/java.'),
        ('Why set JAVA_HOME in hadoop-env.sh as well?', 'Daemons started over SSH or by systemd do not read your interactive ~/.bashrc.'),
        ('What does ulimit -n control?', 'The maximum open file descriptors per process; HDFS, Kafka and HBase open many files and sockets and need it raised.'),
    ),
    note('The <code>hadoop</code> command in this example is a two-line stub created on the spot, used to demonstrate PATH and symlinks without downloading Hadoop; '
         'Java and everything else are real.', 'Note'),
]),

# ------------------------------------------------------------------ 35
Q('How do you install software on Linux? Compare apt/dnf, tarballs and Python virtual environments.', 'Package Management', minutes=7, cards=[
    definition(
        defbox('<strong>Package managers</strong> install software with dependencies and updates from repositories: Debian/Ubuntu <code>apt</code> (.deb, '
               '<code>dpkg</code>), RHEL/Rocky <code>dnf</code>/<code>yum</code> (.rpm, <code>rpm</code>). Typical commands: <code>apt update</code>, '
               '<code>apt install pkg</code>, <code>apt remove</code>, <code>apt list --installed</code>, <code>apt-cache policy pkg</code>.',
               '<strong>Tarballs</strong> (Hadoop, Spark, Kafka) are unpacked under /opt and updated manually. <strong>Python packages</strong> go into a '
               '<strong>virtual environment</strong> per project (<code>python3 -m venv .venv</code>, <code>source .venv/bin/activate</code>, '
               '<code>pip install -r requirements.txt</code>); Ubuntu 23.04+ blocks pip installs into the system Python (PEP 668).'),
        tags('apt', 'dnf', 'dpkg', 'venv', 'pip', 'PEP 668'),
    ),
    analogy('apt is an <strong>official store</strong> that delivers and maintains your appliances; a tarball is <strong>flat-pack furniture</strong> you assemble '
            'yourself; a virtual environment is a <strong>separate toolbox for each project</strong>, so one project\'s tools never break another\'s.'),
    pkg_anim(),
    real_world(
        scenario('Lab image preparation',
                 p('The lab image gets Java, Python, MySQL client and utilities through apt; Hadoop/Spark/Kafka tarballs into /opt; each student project uses its '
                   'own venv with pinned versions in requirements.txt, so upgrading pandas for one project does not break another.')),
    ),
    example(
        shrun("""
            dpkg -l gawk | tail -n 1 | awk '{print $1, $2, $3}'
            apt-cache policy gawk | head -n 3
            apt list --installed 2>/dev/null | wc -l
            dpkg -L gawk | grep bin/ | head -n 2
            python3 -m venv .venv
            source .venv/bin/activate; which python pip
            pip --version | cut -d' ' -f1-2
            deactivate; which python3
        """),
        title='Example: Inspecting Packages and Creating a venv'),
    steps(
        ('System software', '<code>sudo apt update &amp;&amp; sudo apt install pkg</code> (or dnf).'),
        ('Find out what is installed', '<code>dpkg -l</code>, <code>apt list --installed</code>, <code>rpm -qa</code>.'),
        ('Software not packaged', 'Release tarball → /opt, verify checksum, symlink.'),
        ('Python projects', 'venv + pip + requirements.txt (pip freeze).'),
        ('Keep updated', '<code>sudo apt upgrade</code> on a schedule; pin versions for reproducibility.'),
        title='Steps to Install Software Cleanly'),
    crossq(
        ('apt vs apt-get?', 'apt is the newer user-friendly front end (progress bars, combined commands); apt-get has a stable interface recommended for scripts.'),
        ('Why does pip outside a venv refuse to install on a fresh Ubuntu 24.04?', 'Ubuntu marks the system Python as "externally managed" (PEP 668) to stop pip from breaking OS packages; use a venv or pipx.'),
        ('How do you check a downloaded tarball is genuine?', 'Compare its SHA-512 (sha512sum) with the checksum published by the project, ideally verifying the GPG signature.'),
    ),
]),
])
