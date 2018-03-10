pydups
======

Find duplicate files in the specified directories.

:copiright: 2016-2018 Antonio Valentino


Usage
-----

::

    usage: pydups [-h] [--version] [-s] [-l] [--format {json,pprint,custom}]
                  [-k {name,name_and_size,md5}] [--clean] [-c CACHEFILE]
                  [-o OUTPUT] [-v]
                  dataroot

    Search all duplicate files in the specified directories.
    Symbolic links are always ignored.
    By default duplicte file names are searched but the criterion can be
    customized using the "-k" ("--key") parameter.

    positional arguments:
      dataroot              path to the root of the directory tree to scan

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      -s, --compute-size    compute the total size of duplicate files
                            (default: False)
      -l, --list-files      dump the entire list of duplicate files
                            (default: False)
      --format {json,pprint,custom}
                            select the format of file list, implies "-l"
                            ("--list-files"). Default: "json"
      -k {name,name_and_size,md5}, --key {name,name_and_size,md5}
                            "name" search duplicate basenames, "name_and_size"
                            files are considered duplicate if they have the
                            same basename and size, "md5" compare MD5 sum of
                            files (default: "name")
      --clean               remove duplicate files and replace them with
                            symbolic links (default: False)
      -c CACHEFILE, --cache CACHEFILE
                            enable caching and use cache file (default: None)
      -o OUTPUT, --output OUTPUT
                            save the list of duplicate files on the specified
                            output file. Implies "-l" ("--list").
      -v, --verbose         print verbose help messages (default: False)

    Copyright (C) 2016-2017 Antonio Valentino <antonio.valentino@tiscali.it>


License
-------

BSD 3-Clause License (see LICENSE file).
