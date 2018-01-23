#!/usr/bin/python

"""
(C) Copyright 2018 ALBA-CELLS
Author: Marc Rosanes Siscart
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

from joblib import Parallel, delayed

from txm2nexuslib.parser import get_db, get_file_paths
from txm2nexuslib.image.xrm2hdf5 import Xrm2H5Converter
from txm2nexuslib.images import util


def convert_xrm2h5(xrm_file):
    xrm2h5_converter = Xrm2H5Converter(xrm_file)
    xrm2h5_converter.convert_xrm_to_h5_file()


def multiple_xrm_2_hdf5(txm_txt_script, subfolders=False, cores=-2,
                        update_db=True):
    """Using all cores but one for the computations"""

    start_time = time.time()

    # printer = pprint.PrettyPrinter(indent=4)
    db = get_db(txm_txt_script)
    all_file_records = db.all()

    # printer.pprint(all_file_records[3])
    root_path = os.path.dirname(os.path.abspath(txm_txt_script))
    files = get_file_paths(all_file_records, root_path,
                           use_subfolders=subfolders)

    # printer.pprint(files)
    # The backend parameter can be either "threading" or "multiprocessing".
    Parallel(n_jobs=cores, backend="multiprocessing")(
        delayed(convert_xrm2h5)(xrm_file) for xrm_file in files)

    if update_db:
        util.update_db_func(db, "hdf5_raw", all_file_records)
    db.close()

    n_files = len(files)
    print("--- Convert from xrm to hdf5 %d files took %s seconds ---\n" %
          (n_files, (time.time() - start_time)))
    return db
