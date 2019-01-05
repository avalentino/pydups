# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import unittest

try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib


import pydups


def create_tree(root, tree):
    root = pathlib.Path(root)

    root.mkdir(exist_ok=True)

    for name, data in tree.items():
        path = root / name
        if data is None:
            path.touch()
        elif isinstance(data, int):
            size = data
            path.write_bytes(bytes(size))
        elif isinstance(data, bytes):
            path.write_bytes(data)
        elif isinstance(data, str):
            path.write_text(data)
        elif isinstance(data, dict):
            create_tree(path, data)
        else:
            raise TypeError(
                'unable to create a tree item for {!r}'.format(data))


class _BaseTestScanDuplicates(object):
    # TREE = {
    #     'aaa.txt': 'aaa',
    #     'bbb.txt': 'bbb',
    # }
    #
    # NDUPS = 0
    #
    # KEYFUNC = pydups.name_key

    def setUp(self):
        prefix=self.__class__.__name__ + '_'
        self.root = tempfile.mkdtemp(prefix=prefix)
        create_tree(self.root, self.TREE)

    def tearDown(self):
        shutil.rmtree(self.root)


class TestScanDuplicatesName01(_BaseTestScanDuplicates, unittest.TestCase):
    TREE = {
        'aaa.txt': 'aaa',
        'bbb.txt': 'bbb',
    }

    NAME_KEY_DUPS = 0
    NAME_AND_SIZE_KEY_DUPS = 0
    MD5_KEY_DUPS = 0

    def test_dup_count_name_key(self):
        keyfunc = pydups.name_key
        res = pydups.scan_duplicates(self.root, keyfunc)
        self.assertEqual(res.duplicate_count(), self.NAME_KEY_DUPS)

    def test_dup_count_name_and_size_key(self):
        keyfunc = pydups.name_and_size_key
        res = pydups.scan_duplicates(self.root, keyfunc)
        self.assertEqual(res.duplicate_count(), self.NAME_AND_SIZE_KEY_DUPS)

    def test_dup_count_md5_key(self):
        keyfunc = pydups.md5_key
        res = pydups.scan_duplicates(self.root, keyfunc)
        self.assertEqual(res.duplicate_count(), self.MD5_KEY_DUPS)



class TestScanDuplicates02(TestScanDuplicatesName01, unittest.TestCase):
    TREE = {
        'aaa.txt': None,
        'bbb.txt': None,
        'ccc.txt': 3,
    }

    NAME_KEY_DUPS = 0
    NAME_AND_SIZE_KEY_DUPS = 0
    MD5_KEY_DUPS = 1


class TestScanDuplicates03(TestScanDuplicatesName01, unittest.TestCase):
    TREE = {
        'aaa.txt': None,
        'bbb.txt': None,
        'ccc.txt': 3,
        'dir': {
            'aaa.txt': 'aaa',
            'bbb.txt': 'bbb',
            'ccc.txt': 3,
            'ddd.txt': 4,
        },
    }

    NAME_KEY_DUPS = 3
    NAME_AND_SIZE_KEY_DUPS = 1
    MD5_KEY_DUPS = 2


class TestScanDuplicates04(TestScanDuplicatesName01, unittest.TestCase):
    TREE = {
        'aaa.txt': 'aaa',
        'bbb.txt': None,
        'ccc.txt': 3,
        'dir': {
            'aaa.txt': 4,
            'bbb.txt': 'bbb',
            'ccc.txt': 5,
            'ddd.txt': 'aaa',
        },
    }

    NAME_KEY_DUPS = 3
    NAME_AND_SIZE_KEY_DUPS = 0
    MD5_KEY_DUPS = 1

    def test_dup_count_md5_key_02(self):
        keyfunc = pydups.md5_key
        res = pydups.scan_duplicates(self.root, keyfunc)

        dups = ('aaa.txt', 'dir/ddd.txt')
        dups = set(str(pathlib.Path(self.root) / item) for item in dups)

        values = set(item.path for item in list(res.data.values())[0])

        self.assertEqual(dups, values)
