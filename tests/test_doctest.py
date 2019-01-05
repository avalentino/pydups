# -*- coding: utf-8 -*-

import doctest

import pydups


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(pydups))
    return tests
