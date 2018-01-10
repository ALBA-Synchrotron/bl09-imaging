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
from shutil import copy

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from joblib import Parallel, delayed

from txm2nexuslib.parser import get_file_paths

def create_subset_db(file_index_fn, subset_file_index_fn,
                     processed=True, extension=".hdf5"):
    """ From a main DB, create a subset DB of the main DB, by only extracting
    the hdf5 files. If 'processed' input argument is indicated (as True
    or False), only the processed or non processed hdf5 files will be
    added to the freshly created DB"""

    if os.path.exists(subset_file_index_fn):
        os.remove(subset_file_index_fn)

    directory = os.path.dirname(file_index_fn) + "/"
    subset_file_index_fn = directory + subset_file_index_fn

    file_index_db = TinyDB(file_index_fn,
                           storage=CachingMiddleware(JSONStorage))
    subset_file_index_db = TinyDB(subset_file_index_fn,
                                  storage=CachingMiddleware(JSONStorage))
    subset_file_index_db.purge()
    files = Query()

    if processed is True or processed is False:
        query_cmd = ((files.extension == extension) &
                     (files.processed == processed))
    else:
        query_cmd = (files.extension == extension)
    records = file_index_db.search(query_cmd)
    subset_file_index_db.insert_multiple(records)
    file_index_db.close()
    return subset_file_index_db


def copy_2_proc(filename, suffix):
    """Copy a raw file into another file which can be used  processed file"""
    base, extension = os.path.splitext(filename)
    filename_processed = base + suffix + extension
    copy(filename, filename_processed)


def update_db_func(files_db, table_name, files_records, suffix=None):
    """Create new DB table with records of hdf5 raw data (changing the
    extension to hdf5), or with records of processed files (adding a suffix).
    If suffix is not given (suffix None), the new DB will contain the same
    file names as the original DB but with .hdf5 extension; otherwise,
    a suffix is added to the already hdf5 filenames."""
    table = files_db.table(table_name)
    table.purge()
    records = []
    for record in files_records:
        record = dict(record)
        if not suffix:
            filename = os.path.splitext(record['filename'])[0] + ".hdf5"
            record.update({'extension': '.hdf5'})
        else:
            base, ext = os.path.splitext(record['filename'])
            filename = base + suffix + ext
            record.update({'processed': True})
        record.update({'filename': filename})
        records.append(record)
    table.insert_multiple(records)


def copy2proc_multiple(file_index_db, table_in_name="hdf5_raw",
                       table_out_name="hdf5_proc", suffix="_proc",
                       use_subfolders=False, cores=-1, update_db=True):
    """Copy many files to processed files"""
    # printer = pprint.PrettyPrinter(indent=4)
    db = TinyDB(file_index_db, storage=CachingMiddleware(JSONStorage))
    files_query = Query()
    if table_in_name == "default":
        hdf5_records = db.search(files_query.extension == ".hdf5")
    else:
        table_in = db.table(table_in_name)
        hdf5_records = table_in.all()

    # printer.pprint(all_file_records[3])

    root_path = os.path.dirname(os.path.abspath(file_index_db))
    files = get_file_paths(hdf5_records, root_path,
                           use_subfolders=use_subfolders)

    # The backend parameter can be either "threading" or "multiprocessing"
    Parallel(n_jobs=cores, backend="multiprocessing")(
        delayed(copy_2_proc)(h5_file, suffix) for h5_file in files)

    if update_db:
        update_db_func(db, table_out_name, hdf5_records, suffix)

    db.close()


