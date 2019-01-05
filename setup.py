#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys

from setuptools import setup


def get_version():
    filename = os.path.join(os.path.dirname(__file__), 'pydups.py')
    with open(filename) as fd:
        data = fd.read()
    mobj = re.search(
        '^__version__\s*=\s*(?P<quote>[\'"])(?P<version>[^\'"]+)(?P=quote)',
        data,
        re.MULTILINE)
    return mobj.group('version')


install_requires = []
test_requires = []

if sys.version_info < (3, 3):
    install_requires.append('scandir')

if sys.version_info < (3, 5):
    install_requires.append('pathlib2')


setup(
    name='pydups',
    version=get_version(),
    description='Find duplicate files in the specified directories.',
    long_description='''Search all duplicate files in the specified
    directories. Symbolic links are always ignored.
    By default duplicte file names are searched but the criterion can be
    customized using the "-k" ("--key") parameter.''',
    url='https://github.com/avalentino/pydups',
    author='Antonio Valentino',
    author_email='antonio.valentino@tiscali.it',
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='utility duplicates',
    py_modules=["pydups"],
    entry_points={
        'console_scripts': [
            'pydups=pydups:main',
        ],
    },
    install_requires=install_requires,
    tests_require=test_requires,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
)
