from build import *
from linuxq.anims import *
from linuxq.runner import shrun, sh, script_file
from linuxq.data import COMMON

SECTION = dict(level='basic', title='Permissions & Users', questions=[

# ------------------------------------------------------------------ 6
Q('How do Linux file permissions work? Explain rwx and chmod (symbolic and octal).', 'Permissions & chmod', minutes=8, cards=[
    definition(
        defbox('Every file has permissions for three classes: <strong>owner (u)</strong>, <strong>group (g)</strong>, <strong>others (o)</strong>, each with '
               '<strong>read (r=4)</strong>, <strong>write (w=2)</strong>, <strong>execute (x=1)</strong>. <code>ls -l</code> shows them as e.g. '
               '<code>-rwxr-x---</code> = 750.',
               'For directories: r lists names, w creates/deletes/renames entries, x allows entering and accessing items. <code>chmod</code> changes them '
               'numerically (<code>chmod 640 f</code>) or symbolically (<code>chmod u+x,g-w,o= f</code>); <code>-R</code> applies recursively.'),
        table(['Octal', 'Symbolic', 'Typical use'], [
            ['644', 'rw-r--r--', 'normal files'],
            ['600', 'rw-------', 'private keys, passwords'],
            ['755', 'rwxr-xr-x', 'scripts, programs, directories'],
            ['750', 'rwxr-x---', 'team-only scripts/directories'],
            ['700', 'rwx------', 'private directories (~/.ssh)'],
        ]),
        tags('chmod', 'rwx', 'octal', 'permissions', 'ls -l'),
    ),
    analogy('A shared office cupboard with three key sets: one for the <strong>owner</strong>, one for the <strong>department</strong>, one for '
            '<strong>visitors</strong>. Each key can allow looking inside (r), changing contents (w), or using the machine inside (x).'),
    perm_anim(),
    real_world(
        scenario('Exam papers on a shared server',
                 p('Question papers are <code>640</code> (faculty group can read, students cannot); the results script is <code>750</code> so only the coordinators\' '
                   'group can run it; SSH private keys must be <code>600</code>, or ssh refuses to use them.')),
    ),
    example(
        shrun("""
            printf 'echo results processed\\n' > run.sh
            ls -l run.sh
            ./run.sh
            chmod u+x run.sh; ls -l run.sh; ./run.sh
            chmod 750 run.sh; stat -c '%A %a %n' run.sh
            echo 'Q1. Explain HDFS' > paper.txt; chmod 000 paper.txt
            cat paper.txt
            chmod u=rw,g=r,o= paper.txt; stat -c '%A %a %n' paper.txt
            mkdir locked; touch locked/a; chmod u-x locked
            ls locked; cat locked/a
            chmod u+x locked
        """),
        title='Example: Execute Bit, Octal/Symbolic chmod, Directory x Bit'),
    steps(
        ('Inspect', '<code>ls -l</code> or <code>stat -c "%A %a %n"</code>.'),
        ('Decide per class', 'What should owner, group, others be able to do?'),
        ('Apply', '<code>chmod 640 file</code> or <code>chmod g+r,o-rwx file</code>.'),
        ('Directories need x', 'To enter or reach files inside: 750/755.'),
        ('Recursive with care', '<code>chmod -R</code> gives files and directories the same bits; use <code>find -type d/-type f -exec chmod</code> to treat them differently.'),
        title='Steps to Set Permissions'),
    crossq(
        ('Why could ls list the locked directory without x but not open a file in it?', 'r on a directory allows reading names; x is needed to access the entries (stat, open). Without x, ls prints names but cannot show details.'),
        ('What does chmod 777 do and why avoid it?', 'Everyone can read, modify and execute; any user or compromised process can alter or replace the file. Use the minimum needed.'),
        ('Can you delete a file you have no write permission on?', 'Yes, if you have w and x on its directory (deletion changes the directory, not the file), unless the sticky bit is set.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('How do users, groups and ownership work? How do you change ownership?', 'Users, Groups & chown', minutes=7, cards=[
    definition(
        defbox('Each <strong>user</strong> has a name, uid, primary group, home directory and login shell (<code>/etc/passwd</code>). <strong>Groups</strong> '
               '(<code>/etc/group</code>) let several users share access. Every file has one <strong>owner</strong> and one <strong>group</strong>.',
               'Commands: <code>id</code>, <code>groups</code>, <code>whoami</code>; as root: <code>useradd -m</code>, <code>passwd</code>, <code>usermod -aG group user</code>, '
               '<code>groupadd</code>, <code>userdel -r</code>; <code>chown user:group file</code> (root only for changing the owner), <code>chgrp group file</code> '
               '(owner may change to a group they belong to).'),
        tags('useradd', 'usermod', 'groups', 'chown', 'chgrp', '/etc/passwd'),
    ),
    analogy('Users are <strong>employees</strong>, groups are <strong>departments</strong>. Every document is "owned by" one employee and "filed under" one '
            'department; the permission bits say what the owner, the department and everyone else may do with it.'),
    owner_anim(),
    real_world(
        scenario('Shared course folder',
                 p('The admin creates a <code>dbda</code> group, adds faculty with <code>usermod -aG dbda name</code>, and sets <code>chown -R root:dbda /data/dbda</code> '
                   'with group write permission, so every faculty member can update shared datasets while students cannot.')),
    ),
    example(
        shrun("""
            !userdel -r anuj 2>/dev/null; groupdel dbda 2>/dev/null; true
            useradd -m -s /bin/bash anuj
            groupadd dbda
            usermod -aG dbda anuj
            id anuj
            grep -E '^(anuj|student):' /etc/passwd
            grep '^dbda:' /etc/group
            touch report.csv; ls -l report.csv
            chown anuj:dbda report.csv; ls -l report.csv
            ls -l /etc/shadow
        """, user='root'),
        shrun("""
            touch mine.csv
            chown root mine.csv
            cat /etc/shadow
            groups
        """),
        title='Example: Creating Users and Groups (root), then the Limits of a Normal User'),
    steps(
        ('Create the group', '<code>sudo groupadd dbda</code>.'),
        ('Create/modify users', '<code>sudo useradd -m -s /bin/bash anuj</code>; <code>sudo usermod -aG dbda anuj</code>.'),
        ('Set ownership', '<code>sudo chown -R root:dbda /data/dbda</code>.'),
        ('Set permissions', '<code>sudo chmod -R 2770 /data/dbda</code> (SGID keeps the group on new files).'),
        ('Verify', '<code>id anuj</code>; log out/in for new group membership to apply.'),
        title='Steps to Share a Folder with a Team'),
    crossq(
        ('Why usermod -aG and not -G?', '-G alone replaces all supplementary groups with the list given; -a appends.'),
        ('Why can\'t a normal user chown a file to someone else?', 'It would let users bypass disk quotas and plant files under another user\'s name; only root can change owners.'),
        ('Why does a new group not apply immediately?', 'Group membership is read at login; start a new session or use newgrp.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What is umask? How are default permissions decided?', 'umask & Default Permissions', minutes=6, cards=[
    definition(
        defbox('New files start from <code>666</code> and new directories from <code>777</code>; the <strong>umask</strong> lists the bits to <strong>remove</strong>. '
               'With the common umask <code>022</code>: files 644, directories 755. <code>027</code> gives 640/750; <code>077</code> gives 600/700.',
               'Check with <code>umask</code> (or <code>umask -S</code> symbolically); set for the session with <code>umask 027</code>, permanently in '
               '<code>~/.bashrc</code> or system-wide profiles.'),
        tags('umask', 'default permissions', '022', '027'),
    ),
    analogy('umask is a <strong>stencil with holes covered</strong>: every new file is painted through it, so the covered permissions never appear.'),
    umask_anim(),
    real_world(
        scenario('Multi-user lab server',
                 p('With the default 022, every student could read every other student\'s assignment files. Setting <code>umask 077</code> in the student profile makes '
                   'new files private by default; shared folders then grant access deliberately.')),
    ),
    example(
        shrun("""
            umask; umask -S
            touch a.txt; mkdir dir_a
            umask 027; touch b.txt; mkdir dir_b
            umask 077; touch c.txt; mkdir dir_c
            stat -c '%a %A %n' a.txt b.txt c.txt dir_a dir_b dir_c
        """),
        title='Example: The Same Commands Under Three umasks'),
    steps(
        ('Check', '<code>umask</code>.'),
        ('Choose', '022 (readable by all), 027 (group only), 077 (private).'),
        ('Set', 'In <code>~/.bashrc</code> for you, in <code>/etc/profile</code> or login.defs for everyone.'),
        ('Remember x', 'Scripts still need <code>chmod +x</code>.'),
        title='Steps to Control Defaults'),
    crossq(
        ('Is umask subtraction?', 'It is a bitwise mask (permissions AND NOT umask), which matches subtraction for typical values but not in general (e.g. 666 with umask 033 gives 644, not 633).'),
        ('Does umask affect existing files?', 'No, only files created afterwards by that process and its children.'),
        ('Where do services get their umask?', 'From their start-up environment, e.g. UMask= in a systemd unit file.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('What are SUID, SGID and the sticky bit? What are ACLs?', 'SUID, SGID, Sticky Bit & ACLs', minutes=8, cards=[
    definition(
        defbox('<strong>SUID</strong> (4000, shown as <code>s</code> in the owner x position) makes an executable run with its <strong>owner\'s</strong> privileges '
               '(e.g. <code>/usr/bin/passwd</code> runs as root). <strong>SGID</strong> (2000) on a program runs it with the file\'s group; on a <strong>directory</strong> '
               'it makes new files inherit the directory\'s group. The <strong>sticky bit</strong> (1000, <code>t</code>) on a directory allows only a file\'s owner '
               '(or root) to delete or rename it, as in <code>/tmp</code> (1777).',
               '<strong>ACLs</strong> (<code>setfacl</code>/<code>getfacl</code>) add extra rules for specific users/groups beyond owner/group/others; a '
               '<code>+</code> after the permission string in <code>ls -l</code> shows an ACL is present.'),
        tags('SUID', 'SGID', 'sticky bit', 'ACL', 'setfacl', '/tmp'),
    ),
    analogy('SUID is a <strong>signed authority letter</strong>: the clerk acts with the manager\'s power for that one task. The sticky bit is the rule in a '
            '<strong>shared staff room</strong>: anyone can put things on the shelf, but only the owner can take theirs away.'),
    special_anim(),
    real_world(
        scenario('Team folder and an extra reviewer',
                 p('<code>/data/dbda</code> is <code>2775 root:dbda</code> so every new file belongs to the dbda group. An external examiner who is not in the group gets '
                   'read access to one results folder through an ACL: <code>setfacl -m u:examiner:rx results</code>.')),
    ),
    example(
        shrun("""
            ls -l /usr/bin/passwd
            ls -ld /tmp
            mkdir shared; chmod 2775 shared; ls -ld shared
            touch shared/notes.txt; ls -l shared/notes.txt
            chmod +t shared; stat -c '%a %A' shared
            echo 'marks' > results.csv; chmod 600 results.csv
            setfacl -m u:anuj:r results.csv
            getfacl -c results.csv
            ls -l results.csv
        """),
        title='Example: Special Bits and an ACL'),
    steps(
        ('Team directory', '<code>chgrp team dir; chmod 2775 dir</code>.'),
        ('Shared drop folder', '<code>chmod 1777 dir</code> (sticky).'),
        ('One-off extra access', '<code>setfacl -m u:name:rx path</code>; inspect with <code>getfacl</code>.'),
        ('Audit SUID', '<code>find / -perm -4000 -type f 2&gt;/dev/null</code>.'),
        title='Steps to Use Special Permissions'),
    crossq(
        ('Why is SUID a security risk?', 'A bug in a SUID-root program lets an attacker run code as root; keep the list minimal and never set SUID on scripts.'),
        ('Capital S or T in ls -l?', 'The special bit is set but the underlying execute bit is not (e.g. rwS), usually a mistake.'),
        ('Do HDFS permissions work the same way?', 'HDFS uses a similar owner/group/others rwx model with optional ACLs, though x on files is ignored.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What is root? What is the difference between su and sudo? What are /etc/passwd and /etc/shadow?', 'root, su & sudo', minutes=7, cards=[
    definition(
        defbox('<strong>root</strong> (uid 0) is the superuser, not restricted by permission checks. <strong>su</strong> switches to another user (default root) '
               'and asks for <strong>that user\'s</strong> password; <code>su -</code> also loads their login environment. <strong>sudo</strong> runs one command '
               'as root (or another user) after asking for <strong>your own</strong> password, if <code>/etc/sudoers</code> allows it, and logs every use.',
               '<code>/etc/passwd</code> (world-readable) lists accounts: name:x:uid:gid:comment:home:shell. Password hashes are in <code>/etc/shadow</code>, '
               'readable only by root. Edit sudoers only with <code>visudo</code> (syntax-checked).'),
        tags('root', 'sudo', 'su', 'sudoers', '/etc/passwd', '/etc/shadow'),
    ),
    analogy('<strong>su</strong> is borrowing the <strong>principal\'s master key</strong> (you must know the principal\'s secret). <strong>sudo</strong> is '
            'asking the <strong>security desk</strong> to open one door for you: they check your own ID against an approved list and write it in the register.'),
    sudo_anim(),
    real_world(
        scenario('Lab server administration',
                 p('Coordinators get <code>sudo</code> rights only for restarting services and installing packages; the root password is not shared. When something '
                   'changes unexpectedly, <code>/var/log/auth.log</code> shows who ran which command with sudo and when.')),
    ),
    example(
        shrun("""
            id
            grep '^student:' /etc/passwd
            cut -d: -f1,3,7 /etc/passwd | head -n 3
            ls -l /etc/passwd /etc/shadow
            head -n 1 /etc/shadow
            sudo -n true
        """),
        sh("""
            sudo apt update                 # one command as root (asks for YOUR password)
            sudo -u hdfs hdfs dfs -ls /     # run as another service user
            sudo -l                         # what am I allowed to run?
            su - anuj                       # become anuj (anuj's password)
            sudo -i                         # root login shell via sudo
            sudo visudo                     # edit /etc/sudoers safely
        """, title='Shell (common sudo/su usage)'),
        title='Example: Account Files and a Normal User Without sudo Rights'),
    steps(
        ('Work as a normal user', 'Never browse or code as root.'),
        ('Grant sudo deliberately', 'Add admins to the sudo/wheel group or a sudoers rule via visudo.'),
        ('Limit commands', 'Use sudoers rules for specific commands where possible.'),
        ('Run elevated only when needed', '<code>sudo command</code>; avoid long root shells.'),
        ('Audit', 'Check /var/log/auth.log (or journalctl) for sudo usage.'),
        title='Steps for Safe Administration'),
    crossq(
        ('Why is "x" in the password field of /etc/passwd?', 'The real hash moved to /etc/shadow so that ordinary users (who need to read /etc/passwd) cannot see password hashes.'),
        ('sudo su vs sudo -i?', 'Both give a root shell; sudo -i is the cleaner way (simulated root login) and is logged as a sudo session.'),
        ('Why did sudo -n true fail here?', '-n (non-interactive) makes sudo fail instead of prompting for a password. On this server the student account is also not in sudoers (sudo -l -U student: "not allowed to run sudo"), so even with a password it would be refused and the attempt logged.'),
    ),
]),
])
