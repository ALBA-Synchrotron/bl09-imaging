#!/usr/bin/python

"""
(C) Copyright 2018 ALBA-CELLS
Authors: Marc Rosanes, Carlos Falcon, Zbigniew Reszela, Carlos Pascual
The program is distributed under the terms of the
GNU General Public License (or the Lesser GPL).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import argparse
from argparse import RawTextHelpFormatter

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from txm2nexuslib.images.util import copy2proc_multiple

import pprint


def main():

    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    description = 'Copy raw data files into files for processing'
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)
    parser.register('type', 'bool', str2bool)

    parser.add_argument('file_index_db', metavar='file_index_db',
                        type=str, help='index of xrm and hdf5 data files')

    parser.add_argument('-s', '--subfolders', type='bool',
                        default='False',
                        help='- If True: Use subfolders for indexing\n'
                             '- If False: Use general folder for indexing\n'
                             '(default: False)')

    parser.add_argument('-c', '--cores', type=int,
                        default=-1,
                        help='Number of cores used for the format conversion\n'
                             '(default is max of available CPUs: -1)')

    parser.add_argument('-u', '--update_db', type='bool',
                        default='True',
                        help='Update DB with hdf5 records\n'
                             '(default: True)')

    parser.add_argument('-ti', '--table_h5_in', type=str,
                        default='hdf5_raw',
                        help='DB input table of raw hdf5 file records\n'
                             '(default: hdf5_raw)')

    parser.add_argument('-to', '--table_h5_out', type=str,
                        default='hdf5_proc',
                        help='DB output table of raw hdf5 file records\n'
                             '(default: hdf5_proc)')

    args = parser.parse_args()

    copy2proc_multiple(args.file_index_db, table_in_name=args.table_h5_in,
                       table_out_name=args.table_h5_out,
                       use_subfolders=args.subfolders, cores=args.cores,
                       update_db=args.update_db)

    # printer.pprint(files)


if __name__ == "__main__":
    main()



