# -*- coding: utf-8 -*-

import os
import sys
import unittest
import subprocess

import pydups


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
        ret = pydups.main(argv)
        assert ret == pydups.EX_OK

    def test_scan_invalid_input(self):
        argv = ['unexistent']
        ret = pydups.main(argv)
        assert ret == pydups.EX_FAILURE
