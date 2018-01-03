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
from joblib import Parallel, delayed

import argparse
from argparse import RawTextHelpFormatter
from txm2nexuslib.image.xrm2hdf5 import Xrm2H5Converter

from tinydb import TinyDB, Query
from operator import itemgetter
from txm2nexuslib.parser import get_db, get_file_paths

import pprint


def convert_xrm2h5(xrm_file):
    xrm2h5_converter = Xrm2H5Converter(xrm_file)
    xrm2h5_converter.convert_xrm_to_h5_file()


def main():

    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    description = 'Convert single image xrm files into single image hdf5 ' \
                  'files'
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter)
    parser.register('type', 'bool', str2bool)

    parser.add_argument('txm_txt_script', metavar='txm_txt_script',
                        type=str, help='TXM txt script used to create the '
                                       'xrm files')

    parser.add_argument('-s', '--subfolders', type='bool',
                        default='False',
                        help='- If True: Use subfolders for indexing\n'
                             '- If False: Use general folder for indexing\n'
                             '(default: False)')

    parser.add_argument('-c', '--cores', type=int,
                        default=-1,
                        help='Number of cores used for the format conversion\n'
                             '(default: 2)')

    parser.add_argument('-u', '--update_db', type='bool',
                       default='True',
                       help='Update DB with hdf5 records\n'
                            '(default: True)')

    args = parser.parse_args()

    prettyprinter = pprint.PrettyPrinter(indent=4)

    db = get_db(args.txm_txt_script)
    all_file_records = db.all()

    #prettyprinter.pprint(all_file_records[3])
    root_path = os.path.dirname(os.path.abspath(args.txm_txt_script))
    files = get_file_paths(all_file_records, root_path,
                           use_subfolders=args.subfolders)

    #prettyprinter.pprint(files)

    start_time = time.time()
    # The backend parameter can be either "threading" or "multiprocessing".
    Parallel(n_jobs=args.cores, backend="multiprocessing")(
        delayed(convert_xrm2h5)(xrm_file) for xrm_file in files)
    print("--- %s seconds ---" % (time.time() - start_time))

    if args.update_db:
        for record in all_file_records:
            rec_h5 = dict(record)
            filename_hdf5 = os.path.splitext(rec_h5['filename'])[0] + ".hdf5"
            rec_h5.update({'filename': filename_hdf5})
            rec_h5.update({'extension': '.hdf5'})
            db.insert(rec_h5)


if __name__ == "__main__":
    main()



