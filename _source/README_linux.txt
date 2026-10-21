Linux & shell examples (add this section to README.txt; add "linuxq" to the Modules list)
- Build with:  python build.py linuxq   -> writes out/linux.html
- Every Terminal box is a real transcript: commands ran on Ubuntu 24.04 / bash 5.2 as a normal user
  "student" in ~/cdac (a few user/group examples ran as root), via linuxq/runner.py.
  Transcripts are cached in _linuxcache/ (one JSON per example).
- While an example is unchanged, the build uses the cache and needs no Linux at all (works on Windows).
- To re-run edited examples you need Linux, run the build as root, and have a user called "student"
  plus gawk, acl, tree, rsync, cron, openssh-client, iproute2 installed.
- systemd/journalctl and real ssh/scp to a server are shown but not run (no systemd or remote host on the build machine).
- Q34 uses a two-line stub for the `hadoop` command to demonstrate PATH/symlinks without downloading Hadoop (stated on the page).
