# -*- coding: utf-8 -*-

import sys
import unittest
import subprocess

import pydups

if sys.version_info < (3, 0):
    from io import BytesIO as StreamType
else:
    from io import StringIO as StreamType

try:
    from contextlib import redirect_stdout, redirect_stderr
except ImportError:
    class _redirect_stdstream(object):
        _stream = None

        def __init__(self, new_target):
            self._new_target = new_target
            self._old_targets = []

        def __enter__(self):
            self._old_targets.append(getattr(sys, self._stream))
            setattr(sys, self._stream, self._new_target)
            return self._new_target

        def __exit__(self, exctype, excinst, exctb):
            setattr(sys, self._stream, self._old_targets.pop())

    class redirect_stdout(_redirect_stdstream):
        _stream = "stdout"

    class redirect_stderr(_redirect_stdstream):
        _stream = "stderr"


class MainTestCase(unittest.TestCase):
    def test_no_args(self):
        cmd = [sys.executable, pydups.__file__]
        ret = subprocess.call(
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        assert ret != pydups.EX_OK

    def test_help01(self):
        cmd = [sys.executable, pydups.__file__, '-h']
        ret = subprocess.call(
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        assert ret == pydups.EX_OK

    def test_help02(self):
        cmd = [sys.executable, pydups.__file__, '--help']
        ret = subprocess.call(
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        assert ret == pydups.EX_OK

    def test_version(self):
        cmd = [sys.executable, pydups.__file__, '--version']
        ret = subprocess.call(
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        assert ret == pydups.EX_OK

    def test_scan(self):
        argv = ['.']
        stream = StreamType()
        with redirect_stdout(stream), redirect_stderr(stream):
            ret = pydups.main(argv)
        assert ret == pydups.EX_OK

    def test_scan_invalid_input(self):
        argv = ['unexistent']
        stream = StreamType()
        with redirect_stdout(stream), redirect_stderr(stream):
            ret = pydups.main(argv)
        assert ret == pydups.EX_FAILURE
