"""Reject owner email leaks in reachable Git history without printing addresses.

Other contributors' metadata is inspected without modification. Owner-name
aliases are deliberately explicit for this repository; this is not a general
PII detector, and does not inspect cached GitHub objects or private backups.
"""
from __future__ import annotations
import subprocess
import sys

NOREPLY = b'206558105+erenariel@users.noreply.github.com'
OWNER_NAMES = {b'eren', b'erenariel'}


def scan(repository='.'):
    output = subprocess.check_output(
        ['git', 'log', '--all', '--format=%H%x00%an%x00%ae%x00%cn%x00%ce'],
        cwd=repository, stderr=subprocess.DEVNULL,
    )
    findings = set()
    count = 0
    for line in output.splitlines():
        commit, author_name, author_email, committer_name, committer_email = line.split(b'\0')
        count += 1
        for name, email in ((author_name, author_email), (committer_name, committer_email)):
            if name.lower() in OWNER_NAMES and email != NOREPLY:
                findings.add(commit.decode('ascii'))
    return count, sorted(findings)


def main():
    try:
        count, findings = scan()
    except (OSError, ValueError, subprocess.CalledProcessError):
        print('Commit privacy check failed: unable to inspect Git history', file=sys.stderr)
        return 2
    if findings:
        print(f'Commit privacy check failed: owner identity in {len(findings)} commits requires review; addresses are redacted', file=sys.stderr)
        return 1
    print(f'Commit privacy check passed: {count} reachable commits inspected')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
