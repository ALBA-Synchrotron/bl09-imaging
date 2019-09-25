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
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

from txm2nexuslib.parser import get_db, get_file_paths
from txm2nexuslib.image.xrm2hdf5 import Xrm2H5Converter
from txm2nexuslib.images import util



def convert_xrm2h5(xrm_file):
    xrm2h5_converter = Xrm2H5Converter(xrm_file)
    xrm2h5_converter.convert_xrm_to_h5_file()


def multiple_xrm_2_hdf5(file_index_db, subfolders=False, cores=-2,
                        update_db=True, query=None):
    """Using all cores but one for the computations"""

    start_time = time.time()
    db = TinyDB(file_index_db, storage=CachingMiddleware(JSONStorage))

    if query is not None:
        file_records = db.search(query)
    else:
        file_records = db.all()

    # import pprint
    # printer = pprint.PrettyPrinter(indent=4)
    # printer.pprint(file_records)
    root_path = os.path.dirname(os.path.abspath(file_index_db))
    files = get_file_paths(file_records, root_path,
                           use_subfolders=subfolders)

    # The backend parameter can be either "threading" or "multiprocessing".
    Parallel(n_jobs=cores, backend="multiprocessing")(
        delayed(convert_xrm2h5)(xrm_file) for xrm_file in files)

    if update_db:
        util.update_db_func(db, "hdf5_raw", file_records)
    db.close()

    n_files = len(files)
    print("--- Convert from xrm to hdf5 %d files took %s seconds ---\n" %
          (n_files, (time.time() - start_time)))
    return db
