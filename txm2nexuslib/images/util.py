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
from tinydb import TinyDB, Query


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

    file_index_db = TinyDB(file_index_fn)
    subset_file_index_db = TinyDB(subset_file_index_fn)
    subset_file_index_db.purge()
    files = Query()

    if processed is True or processed is False:
        query_cmd = ((files.extension == extension) &
                     (files.processed == processed))
    else:
        query_cmd = (files.extension == extension)
    records = file_index_db.search(query_cmd)
    subset_file_index_db.insert_multiple(records)
    return subset_file_index_db


