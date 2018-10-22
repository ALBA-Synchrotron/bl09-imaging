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
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage

from util import create_subset_db
from txm2nexuslib.parser import get_file_paths
from txm2nexuslib.image.image_operate_lib import Image


def crop_and_store(image_h5_filename, dataset="data",
                   roi={"top": 26, "bottom": 24, "left": 21, "right": 19}):

    img = Image(h5_image_filename=image_h5_filename, image_data_set=dataset)
    image_cropped, description = img.crop(roi)
    img.store_image_in_h5(image_cropped, description=description)
    img.close_h5()


def filter_file_index(file_index_db, date=None, sample=None, energy=None,
                      query=None):
    files_query = Query()
    temp_db = TinyDB(storage=MemoryStorage)
    query_cmds = []
    if date:
        query_cmds.append(files_query.date == date)
    if sample:
        query_cmds.append(files_query.sample == sample)
    if energy:
        query_cmds.append(files_query.energy == energy)
    for query_cmd in query_cmds:
        if query is not None:
            query_cmd &= query
        records = file_index_db.search(query_cmd)
        temp_db.purge()
        temp_db.insert_multiple(records)
    return temp_db


def crop_images(file_index_fn, table_name="hdf5_proc", dataset="data",
                roi={"top": 26, "bottom": 24, "left": 21, "right": 19},
                date=None, sample=None, energy=None, cores=-2, query=None):
    """Crop images of one experiment.
    If date, sample and/or energy are indicated, only the corresponding
    images for the given date, sample and/or energy are cropped.
    The crop of the different images will be done in parallel: all cores
    but one used (Value=-2). Each file, contains a single image to be cropped.
    """
    start_time = time.time()
    file_index_db = TinyDB(file_index_fn,
                           storage=CachingMiddleware(JSONStorage))
    db = file_index_db
    if table_name is not None:
        file_index_db = file_index_db.table(table_name)

    if date or sample or energy:
        file_index_db = filter_file_index(file_index_db, date=date,
                                          sample=sample, energy=energy,
                                          query=query)

    root_path = os.path.dirname(os.path.abspath(file_index_fn))
    if query is not None:
        file_records = file_index_db.search(query)
    else:
        file_records = file_index_db.all()
    files = get_file_paths(file_records, root_path)
    if files:
        Parallel(n_jobs=cores, backend="multiprocessing")(
            delayed(crop_and_store)(h5_file, dataset=dataset,
                                    roi=roi) for h5_file in files)
    n_files = len(files)
    print("--- Crop %d files took %s seconds ---\n" %
          (n_files, (time.time() - start_time)))
    db.close()


def main():

    file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
                 "PARALLEL_IMAGING/image_operate_xrm_test_add/" \
                 "tests5/xrm/index.json"

    #file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
    #             "PARALLEL_IMAGING/PARALLEL_XRM2H5/tomo05/index.json"

    crop_images(file_index)
    # sample="ols", energy=640, date=20161203)


if __name__ == "__main__":
    main()
