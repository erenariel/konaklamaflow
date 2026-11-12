"""Exercise the privacy guard against actual disposable Git metadata."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.verify_commit_privacy import scan, NOREPLY


class CommitPrivacyTests(unittest.TestCase):
    def test_owner_author_and_committer_leaks_are_found_without_changing_others(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['git','init','-q',directory],check=True)
            def commit(author, committer, name='erenariel'):
                env=dict(os.environ,GIT_AUTHOR_NAME=name,GIT_COMMITTER_NAME=name,
                         GIT_AUTHOR_EMAIL=author,GIT_COMMITTER_EMAIL=committer)
                subprocess.run(['git','-c','core.hooksPath=/dev/null','commit','--allow-empty','-q','-m','synthetic guard fixture'],cwd=directory,env=env,check=True)
            commit(NOREPLY.decode(),NOREPLY.decode())
            self.assertEqual(scan(directory),(1,[]))
            commit('synthetic-private@example.invalid',NOREPLY.decode())
            commit(NOREPLY.decode(),'synthetic-private@example.invalid')
            count, bad=scan(directory)
            self.assertEqual((count,len(bad)),(3,2))
            commit('contributor@example.invalid','contributor@example.invalid','Synthetic Contributor')
            before=subprocess.check_output(['git','rev-parse','HEAD'],cwd=directory)
            self.assertEqual((scan(directory)[0],len(scan(directory)[1])),(4,2))
            self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=directory),before)
