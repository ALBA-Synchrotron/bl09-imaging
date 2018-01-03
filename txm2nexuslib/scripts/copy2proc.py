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


import os
import time
import multiprocessing
from shutil import copy
from joblib import Parallel, delayed

import argparse
from argparse import RawTextHelpFormatter

from tinydb import TinyDB, Query
from txm2nexuslib.parser import get_file_paths

import pprint


def copy_2_proc(filename, suffix, extension):
    base = os.path.splitext(filename)[0]
    filename_processed = base + suffix + extension
    copy(filename, filename_processed)


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

    args = parser.parse_args()

    # printer = pprint.PrettyPrinter(indent=4)

    db = TinyDB(args.file_index_db)
    files_query = Query()
    hdf5_records = db.search(files_query.extension == ".hdf5")

    # printer.pprint(all_file_records[3])

    root_path = os.path.dirname(os.path.abspath(args.file_index_db))
    files = get_file_paths(hdf5_records, root_path,
                           use_subfolders=args.subfolders)

    start_time = time.time()
    # The backend parameter can be either "threading" or "multiprocessing".
    suffix = "_proc"
    ext = ".hdf5"
    Parallel(n_jobs=args.cores, backend="multiprocessing")(
        delayed(copy_2_proc)(h5_file, suffix, ext) for h5_file in files)

    if args.update_db:
        for hdf5_record in hdf5_records:
            rec_h5_processed = dict(hdf5_record)
            base = os.path.splitext(rec_h5_processed['filename'])[0]
            fn_h5_processed = base + suffix + ext
            rec_h5_processed.update({'filename': fn_h5_processed})
            rec_h5_processed.update({'processed': True})
            db.insert(rec_h5_processed)

    print("--- Copy to processed files took %s seconds ---" %
          (time.time() - start_time))

    # printer.pprint(files)


if __name__ == "__main__":
    main()



