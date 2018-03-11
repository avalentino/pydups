#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import io
import os
import re
import sys
import json
import math
import pprint
import shutil
import fnmatch
import hashlib
import logging
import argparse
import warnings
import functools


from collections import defaultdict, OrderedDict

try:
    import cPickle as pickle
except ImportError:
    import pickle


try:
    from os import scandir
except ImportError:
    from scandir import scandir  # use scandir PyPI module on Python < 3.5

try:
    from size2str import size2str
except ImportError:
    def size2str(size):
        '''String representation of memory size

        Gets a size in bytes and return the its string
        representation using appropriate units.

        Examples::

            >>> size2str(1.3 * 1024**5)
            '1.30 PB'

            >>> size2str(1.3 * 1024)
            '1.30 KB'

            >>> size2str(18)
            '18.00 Bytes'

            >>> size2str(0.3)
            '0.30 Bytes'

        '''

        units = (
            'Bytes',
            'KB',
            'MB',
            'GB',
            'TB',
            'PB',
        )

        multiplier = 1024
        units_length = len(units) - 1

        index = int(math.log(size, multiplier)) if size > 0 else 0
        if index > units_length:
            index = units_length

        result = size / (multiplier ** index)

        return '{:.2f} {}'.format(result, units[index])


__version__ = '1.0.1.dev0'

PROG = 'pydups'

IGNORE_PATTERNS = (
    '.*',
    'cache*',
)

DEBUG = False


def scantree(path, follow_symlinks=False, ignore_patterns=IGNORE_PATTERNS):
    '''Recursively yield DirEntry objects for given directory.'''

    if ignore_patterns:
        pattern = '|'.join(fnmatch.translate(p) for p in ignore_patterns)
    else:
        # does not match anything
        pattern = '-^'

    pattern = re.compile(pattern)

    for entry in scandir(path):
        if pattern.match(entry.name):
            logging.debug('skipping %r', entry.path)
            continue

        if entry.is_dir(follow_symlinks=follow_symlinks):
            # yield from scantree(entry.path, follow_symlinks)
            for entry in scantree(entry.path, follow_symlinks):
                yield entry
        else:
            yield entry


def blockiter(fd, blocksize=io.DEFAULT_BUFFER_SIZE):
    '''Iterator on file-like objects that read blocks of the specified size

    The `fd` parameter must be a binary or text file-like object opened
    for reading.

    The `blocksize` parameter defaults to `io.DEFAULT_BUFFER_SIZE`.

    '''

    guard = '' if isinstance(fd, io.TextIOBase) else b''

    return iter(functools.partial(fd.read, blocksize), guard)


class DuplicateScanResult(object):
    def __init__(self, data, scanned_files, keytype):
        # data is assumed to be a dictionary whose values are lists
        # of os.DirEntries
        self.data = data
        self.scanned_files = scanned_files
        self.keytype = keytype      # string

    def duplicate_count(self):
        values = self.data.values()
        return sum(len(item) - 1 for item in values)

    def duplicate_size(self):
        size = 0
        for duplicates in self.data.values():
            size += duplicates[0].stat().st_size * (len(duplicates) - 1)

        return size

    @staticmethod
    def _format_data_custom(data, indent=4):
        indent_str = ' ' * indent
        sep = '\n' + indent_str
        stream = io.StringIO()
        for key, values in data.items():
            stream.write('{}:\n'.format(key))
            if values:
                stream.write(indent_str)
                stream.write(sep.join(values))
                stream.write('\n')
            stream.write('\n')
        s = stream.getvalue()

        return s

    def format_data(self, indent=2, fmt='json'):
        if fmt == 'json':
            data = OrderedDict(
                (str(k), [e.path for e in self.data[k]])
                for k in sorted(self.data)
            )

            return json.dumps(data, indent=indent)
        else:
            data = OrderedDict(
                (k, [e.path for e in self.data[k]]) for k in sorted(self.data)
            )

            if fmt == 'pprint':
                return pprint.pformat(data, indent=indent)
            elif fmt == 'custom':
                return self._format_data_custom(data, indent=indent)
            else:
                raise ValueError('invalid "format" parameter: "%s"' % fmt)


def name_key(entry):
    return entry.name


def name_and_size_key(entry):
    return (entry.name, entry.stat().st_size)


def md5_key(entry):
    logging.debug('compute MD5 sum of: %s', entry.path)
    md5 = hashlib.md5()
    with open(entry.path, 'rb') as fd:
        for data in blockiter(fd):
            md5.update(data)
    return md5.hexdigest()


class DirEntryStore(object):
    __slots__ = ['name', 'path', '_is_dir', '_is_file', '_is_symlink', '_stat']

    def __init__(self, name, path, is_dir, is_file, is_symlink, statresult):
        self.name = name
        self.path = path
        self._is_dir = is_dir
        self._is_file = is_file
        self._is_symlink = is_symlink
        self._stat = os.stat_result(statresult)

    def is_dir(self, follow_symlinks=True):
        if follow_symlinks is True:
            raise ValueError('follow_symlinks=True is not supported')
        return self._is_dir

    def is_file(self, follow_symlinks=True):
        if follow_symlinks is True:
            raise ValueError('follow_symlinks=True is not supported')
        return self._is_file

    def is_symlink(self):
        return self._is_symlink

    def stat(self, **kwargs):
        if 'follow_symlinks' in kwargs:
            warnings.warn("'follow_symlinks' ignored by DirEntryStore.stat()")
            kwargs.pop('follow_symlinks')

        if len(kwargs) > 0:
            key = list(kwargs)[0]
            raise TypeError(
                'stat() got an unexpected keyword argument %r' % key)

        return self._stat

    @classmethod
    def from_entry(cls, entry):
        return cls(entry.name, entry.path, entry.is_dir(), entry.is_file(),
                   entry.is_symlink(), entry.stat())

    def to_dict(self):
        return dict(
            name=self.name, path=self.path, is_dir=self._is_dir,
            is_file=self._is_file, is_symlink=self._is_symlink,
            statresult=self._stat,
        )

    def __eq__(self, other):
        return (
            other.name == self.name and
            other.path == self.path and
            other._is_dir == self._is_dir and
            other._is_file == self._is_file and
            other._is_symlink == self._is_symlink and
            other._stat.st_size == self._stat.st_size and
            other._stat.st_mtime == self._stat.st_mtime
        )


class DbEntry(object):
    __slats__ = ['direntry', 'md5']

    def __init__(self, direntry, md5=None):
        if isinstance(direntry, dict):
            direntry = DirEntryStore(**direntry)
        elif not isinstance(direntry, DirEntryStore):
            # assume os.DirEntry
            direntry = DirEntryStore.from_entry(direntry)

        self.direntry = direntry
        self.md5 = md5

    def to_dict(self):
        return dict(
            direntry=self.direntry.to_dict(),
            md5=self.md5,
        )


class DB(object):
    def __init__(self, data=None):
        if data is None:
            data = {}

        self.data = data

    def filter_data(self, dataroot):
        prefix = os.path.abspath(dataroot)

        cache = self.data  # shortcut
        data = {}

        for key, val in cache.item():
            if key.startswith(prefix):
                data[key] = val

        return data

    def update(self, dataroot, ignore_patterns=IGNORE_PATTERNS,
               checksum=False):
        cache = self.data  # shortcut
        data = {}

        for entry in scantree(dataroot, ignore_patterns):
            if entry.is_file(follow_symlinks=False):
                entry = DirEntryStore.from_entry(entry)
                key = os.path.abspath(entry.path)
                if key in cache:
                    cache_entry = cache[key]
                    if entry == cache_entry.direntry:
                        if ((checksum and cache_entry.md5 is not None) or
                                not checksum):
                            data[key] = cache_entry
                            continue

                md5 = md5_key(entry) if checksum else None
                data[key] = DbEntry(entry, md5)

        self.clean(dataroot)
        self.data.update(data)

        return data

    def clean(self, path=None):
        if path is None:
            self.data.reset()
        else:
            prefix = os.path.abspath(path)
            cache = self.data  # shortcut
            for key in list(cache):
                if key.startswith(prefix):
                    del cache[key]

    def load(self, cachefile, fmt='pickle'):
        if fmt == 'pickle':
            with open(cachefile, 'rb') as fd:
                cache = pickle.load(fd)
        elif fmt == 'json':
            import json

            with open(cachefile, 'r') as fd:
                cache = json.load(fd)
        else:
            raise ValueError('invalid format: {!r}'.format(fmt))

        for key, val in cache.items():
            self.data[key] = DbEntry(**val)

    def save(self, cachefile, fmt='pickle'):
        cache = {}
        for key, val in self.data.items():
            cache[key] = val.to_dict()

        if fmt == 'pickle':
            with open(cachefile, 'wb') as fd:
                pickle.dump(cache, fd, protocol=0)
        elif fmt == 'json':
            import json

            with open(cachefile, 'w') as fd:
                json.dump(cache, fd, indent='  ')
        else:
            raise ValueError('invalid format: {!r}'.format(fmt))

    @staticmethod
    def _make_key(dbentry, keyfunc):
        if keyfunc == md5_key:
            key = dbentry.md5
        else:
            key = keyfunc(dbentry.direntry)
        return key

    def find_duplicates(self, keyfunc):
        # popilate the data structure
        data = defaultdict(list)
        for dbentry in self.data.values():
            entry = dbentry.direntry
            if entry.is_file(follow_symlinks=False):
                k = self._make_key(dbentry, keyfunc)
                data[k].append(entry)

        # remove non duplicates
        for key in list(data.keys()):  # note: copy keys
            val = data[key]
            if len(val) < 2:
                del data[key]

        return DuplicateScanResult(data, len(self.data), keyfunc.__name__)


def scan_duplicates(dataroot, keyfunc=name_key,
                    ignore_patterns=IGNORE_PATTERNS):

    compute_checksum = True if keyfunc is md5_key else False

    db = DB()
    db.update(dataroot, ignore_patterns, compute_checksum)

    return db.find_duplicates(keyfunc)


def clean_duplicates(duplicates):
    for val in duplicates.values():
        if len(val) < 2:
            logging.warning('not nuplicate entry for {!r}'.format(val))
            continue

        src = val[0]
        for dst in val[1:]:
            if DEBUG:
                shutil.move(dst, dst + '_bak')
            else:
                os.remove(dst)
            relative_src = os.path.relpath(src, os.path.dirname(dst))
            os.symlink(relative_src, dst)


def get_parser():
    parser = argparse.ArgumentParser(
        prog=PROG,
        description='''Search all duplicate files in the specified directories.
        Symbolic links are always ignored.
        By default duplicte file names are searched but the criterion can
        be customized using the "-k" ("--key") parameter''',
        epilog='Copyright (C) 2016-2018 Antonio Valentino '
               '<antonio.valentino@tiscali.it>')

    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(__version__))

    parser.add_argument(
        '-s', '--compute-size', action='store_true', default=False,
        help='compute the total size of duplicate files '
             '(default: %(default)s)')
    parser.add_argument(
        '-l', '--list-files', action='store_true', default=False,
        help='dump the entire list of duplicate files (default: %(default)s)')
    parser.add_argument(
        '--format', choices=('json', 'pprint', 'custom'), default=None,
        help='select the format of file list, implies "-l" ("--list-files"). '
             'Default: "json"')
    parser.add_argument(
        '-k', '--key', choices=('name', 'name_and_size', 'md5'),
        default='name',
        help='"name" search duplicate basenames, '
             '"name_and_size" files are considered duplicate if they have '
             'the same basename and size, '
             '"md5" compare MD5 sum of files (default: "%(default)s")')
    parser.add_argument(
        '--clean', action='store_true', default=False,
        help='remove duplicate files and replace them with symbolic links '
             '(default: %(default)s)')
    parser.add_argument(
        '-c', '--cache', metavar='CACHEFILE', default=None,
        help='enable caching and use cache file (default: %(default)s)')
    parser.add_argument(
        '-o', '--output',
        help='save the list of duplicate files on the specified output file. '
             'Implies "-l" ("--list").')
    parser.add_argument(
        '-v', '--verbose', action='store_true', default=False,
        help='print verbose help messages (default: %(default)s)')

    parser.add_argument(
        'dataroot', help='path to the root of the directory tree to scan')

    return parser


def parse_args(args=None, namespace=None, parser=None):
    if parser is None:
        parser = get_parser()

    args = parser.parse_args(args, namespace)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    key_map = {
        'name': name_key,
        'name_and_size': name_and_size_key,
        'md5': md5_key,
    }
    args.key = key_map[args.key]

    if args.format is not None or args.output is not None:
        args.list_files = True

    if args.format is None:
        args.format = 'json'

    return args


def main():
    logging.basicConfig(
        level=logging.INFO, format='%(message)s', stream=sys.stdout)

    args = parse_args()
    dataroot = args.dataroot
    keytype = args.key.__name__
    ignore_patterns = IGNORE_PATTERNS   # @TODO: set via command line

    if args.cache is not None:
        cachefile = args.cache
    else:
        cachefile = None

    # @TODO: set via command line
    cachefmt = 'json'

    db = DB()
    if cachefile is not None and os.path.exists(cachefile):
        logging.info('loading data from %s', cachefile)
        db.load(cachefile, fmt=cachefmt)  # @TODO: implement auto-detection

    logging.info('scanning %s', dataroot)
    compute_checksum = True if keytype == md5_key.__name__ else False
    db.update(dataroot, ignore_patterns, compute_checksum)
    logging.info('%d scanned files', len(db.data))

    if cachefile is not None:
        logging.info('saving %s ...', cachefile)
        db.save(cachefile, fmt=cachefmt)
        logging.info('%s correcly saved', cachefile)

    result = db.find_duplicates(args.key)
    logging.info('%d duplicate files found', result.duplicate_count())

    if args.compute_size:
        size = result.duplicate_size()
        logging.info('duplicate file size: %s', size2str(size))

    if result.duplicate_count() and args.list_files:
        logging.info('duplicates in "%s"', dataroot)
        data = result.format_data(fmt=args.format)
        if args.output is not None:
            with open(args.output, 'w') as fd:
                fd.write(data)
                fd.write('\n')
        else:
            print(data)

    if args.clean:
        clean_duplicates(result.data)


if __name__ == '__main__':
    main()
