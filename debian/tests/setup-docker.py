#!/usr/bin/env python3
# Copyright 2019 Collabora Ltd.
#
# SPDX-License-Identifier: MIT
# (see build-runtime.py)

from __future__ import print_function

import os
import os.path
import subprocess
import sys
import unittest

try:
    import typing
    typing      # silence pyflakes
except ImportError:
    pass


SETUP_DOCKER = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
    'setup_docker.sh',
)

EXTRA_BOOTSTRAP = os.path.join(
    os.path.dirname(__file__),
    'extra-bootstrap.sh',
)


class TestBuildRuntime(unittest.TestCase):
    def setUp(self):
        # type: () -> None
        pass

    def test_default(self):
        # Send stdout to our stderr to avoid interfering with TAP.
        # Use fd 2 directly because pycotap reopens sys.stdout, sys.stderr
        subprocess.check_call([
            SETUP_DOCKER,
            'amd64',
        ], stdout=2, stderr=2)

        output = subprocess.check_output([
            'docker', 'run',
            '--rm', '--init',
            'steam-runtime-amd64',
            '/dev/init', '-sg',
            '--',
            'uname', '-m',
        ], universal_newlines=True)
        self.assertEqual(output, 'x86_64\n')

        output = subprocess.check_output([
            'docker', 'run',
            '--rm', '--init',
            'steam-runtime-amd64',
            '/dev/init', '-sg',
            '--',
            'dpkg', '--print-architecture',
        ], universal_newlines=True)
        self.assertEqual(output, 'amd64\n')

        output = subprocess.check_output([
            'docker', 'run',
            '--rm', '--init',
            'steam-runtime-amd64',
            '/dev/init', '-sg',
            '--',
            'readlink', '-f', '/usr/bin/gcc'
        ], universal_newlines=True)
        self.assertEqual(output, '/usr/bin/gcc-4.8\n')

        artifacts = os.getenv('AUTOPKGTEST_ARTIFACTS')

        if artifacts is not None:
            os.makedirs(os.path.join(artifacts, 'docker', 'amd64'))

            untar = subprocess.Popen([
                'tar', '-C', os.path.join(artifacts, 'docker', 'amd64'),
                '-xf-',
            ], stdin=subprocess.PIPE)
            tar = subprocess.Popen([
                'docker', 'run', '--rm', '--init',
                'steam-runtime-amd64',
                '/dev/init', '-sg',
                '--',
                'tar', '-C', '/usr',
                '-cf-',
                'manifest.dpkg',
                'manifest.dpkg.built-using',
                'manifest.deb822.gz',
            ], stdout=untar.stdin)
            self.assertEqual(tar.wait(), 0)
            self.assertEqual(untar.wait(), 0)

    def test_other(self):
        subprocess.check_call([
            SETUP_DOCKER,
            '--beta',
            '--extra-bootstrap', EXTRA_BOOTSTRAP,
            'i386',
        ])

        output = subprocess.check_output([
            'docker', 'run',
            '--rm', '--init',
            'steam-runtime-i386-beta',
            '/dev/init', '-sg',
            '--',
            'dpkg', '--print-architecture',
        ], universal_newlines=True)
        self.assertEqual(output, 'i386\n')

        output = subprocess.check_output([
            'docker', 'run',
            '--rm', '--init',
            'steam-runtime-i386-beta',
            '/dev/init', '-sg',
            '--',
            'readlink', '-f', '/usr/bin/gcc'
        ], universal_newlines=True)
        self.assertEqual(output, '/usr/bin/gcc-4.8\n')

        output = subprocess.check_output([
            'docker', 'run',
            '--rm', '--init',
            'steam-runtime-i386-beta',
            '/dev/init', '-sg',
            '--',
            'cat', '/etc/debian_chroot',
        ], universal_newlines=True)
        self.assertEqual(output, 'Docker\n')

        artifacts = os.getenv('AUTOPKGTEST_ARTIFACTS')

        if artifacts is not None:
            os.makedirs(os.path.join(artifacts, 'docker', 'i386-beta'))

            untar = subprocess.Popen([
                'tar', '-C', os.path.join(artifacts, 'docker', 'i386-beta'),
                '-xf-',
            ], stdin=subprocess.PIPE)
            tar = subprocess.Popen([
                'docker', 'run', '--rm', '--init',
                'steam-runtime-i386-beta',
                '/dev/init', '-sg',
                '--',
                'tar', '-C', '/usr',
                '-cf-',
                'manifest.dpkg',
                'manifest.dpkg.built-using',
                'manifest.deb822.gz',
            ], stdout=untar.stdin)
            self.assertEqual(tar.wait(), 0)
            self.assertEqual(untar.wait(), 0)

    def tearDown(self):
        # type: () -> None
        pass


if __name__ == '__main__':
    if sys.argv[1:2] == ['--no-reexec']:
        sys.argv[1:] = sys.argv[2:]
    elif os.getuid() == 0:
        normal_user = os.getenv('AUTOPKGTEST_NORMAL_USER')

        if normal_user is None:
            print('1..0 # SKIP Normal user required')
            sys.exit(0)

        subprocess.check_call(['adduser', normal_user, 'sudo'])
        subprocess.check_call(['adduser', normal_user, 'docker'])
        env = []
        for var in (
            'AUTOPKGTEST_ARTIFACTS', 'AUTOPKGTEST_NORMAL_USER',
            'AUTOPKGTEST_REBOOT_MARK', 'AUTOPKGTEST_TMP',
            'http_proxy', 'https_proxy', 'no_proxy',
        ):
            if var in os.environ:
                env.append('%s=%s' % (var, os.getenv(var)))
        os.execvp(
            'runuser',
            [
                'runuser',
                '--login',
                '--shell=/bin/sh',
                '-c', 'exec "$@"',
                normal_user,
                '--',
                'sh',   # argv[0]
                'env',
            ] + env + [
                __file__,
                '--no-reexec',
            ] + sys.argv[1:],
        )

    sys.path[:0] = [
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            os.pardir,
            'tests',
            'third-party',
        )
    ]
    from pycotap import TAPTestRunner
    unittest.main(verbosity=2, testRunner=TAPTestRunner)

# vi: set sw=4 sts=4 et:
