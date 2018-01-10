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
import h5py
from joblib import Parallel, delayed
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage

from util import create_subset_db
from txm2nexuslib.parser import get_file_paths
from txm2nexuslib.image.image_operate_lib import normalize_image
from txm2nexuslib.images.util import dict2hdf5

def images_to_stack(h5_filenames, dataset="data"):

    """
    # for filename in filenames:
        #pass

    h5_filename = h5_filenames[0]

    if h5_filename is None:
        self.h5_filename = os.path.splitext(xrm_filename)[0] + '.hdf5'
    h5_handler = h5py.File(self.h5_filename, 'w')
    metadata_h5 = self.h5_handler.create_group("metadata")
    metadata = {}
    data = {}
    full_data = {}


    pass
    """

def create_h5_structure(hdf5_structure_dict=None):
    pass


def many_to_stack(file_index_fn, table_name="hdf5_proc", hdf5_structure=None,
                  date=None, sample=None, energy=None, zpz=None,
                  dataset="data"):

    print("--- Start: From individual hdf5 files to hdf5 image stacks ---")
    start_time = time.time()
    file_index_db = TinyDB(file_index_fn,
                           storage=CachingMiddleware(JSONStorage))
    db = file_index_db
    if table_name is not None:
        file_index_db = file_index_db.table(table_name)

    files_query = Query()

    def update_temp_db(temp_db_h5, filtered, query, attribute):
        if filtered:
            records_temp = temp_db_h5.search(query == attribute)
            temp_db_h5.purge()
            temp_db_h5.insert_multiple(records_temp)
        else:
            records_temp = file_index_db.search(query == attribute)
            temp_db_h5.insert_multiple(records_temp)

    # Create temporary DB filtering by date and/or sample and/or energy
    # and/or zpz
    if date or sample or energy or zpz:
        filtered = False
        temp_db = TinyDB(storage=MemoryStorage)
        if date:
            update_temp_db(temp_db, filtered, files_query.date, date)
            filtered = True
        if sample:
            update_temp_db(temp_db, filtered, files_query.sample, sample)
            filtered = True
        if energy:
            update_temp_db(temp_db, filtered, files_query.energy, energy)
            filtered = True
        if zpz:
            update_temp_db(temp_db, filtered, files_query.zpz, zpz)
        file_index_db = temp_db

    #print(file_index_db.all())
    #files_to_stack(h5_filenames, dataset=dataset)

    root_path = os.path.dirname(os.path.abspath(file_index_fn))
    all_file_records = file_index_db.all()
    #print(all_file_records)

    dates_samples_energies_zpzs = []
    for record in all_file_records:
        # TODO: If many ZPs are used, maybe the average ZP will have to be
        # used, or maybe at long term they will not have to be used
        # But a new DB or DB table will have to be created in order to deal
        # with the average images between many different zpz.
        dates_samples_energies_zpzs.append((record["date"],
                                            record["sample"],
                                            record["energy"],
                                            record["zpz"]))
    dates_samples_energies_zpzs = list(set(dates_samples_energies_zpzs))
    for date_sample_energy_zpz in dates_samples_energies_zpzs:
        print("---------for loop------------")
        print(date_sample_energy_zpz)
        date = date_sample_energy_zpz[0]
        sample = date_sample_energy_zpz[1]
        energy = date_sample_energy_zpz[2]
        zpz = date_sample_energy_zpz[3]

        # Raw image records by given date, sample and energy
        # TODO: Think if zpz is really necessary
        query_cmd = ((files_query.date == date) &
                     (files_query.sample == sample) &
                     (files_query.energy == energy) &
                     (files_query.zpz == zpz) &
                     (files_query.FF == False))
        h5_records = file_index_db.search(query_cmd)
        files = get_file_paths(h5_records, root_path)
        for file in files:
            print(os.path.basename(file))
        print("---------end for loop------------")

        # Construct the structure of each hdf5 file
        indict = {"TomoNormalized": {
                      "AverageFF": -1,
                       "Avg_FF_ExtTime": -1,
                       "CurrentsFF": -1,
                       "CurrentsTomo": -1,
                       "ExpTimesTomo": -1,
                       "FFNormalizedWithCurrent": -1,
                       "TomoNormalized": -1,
                       "energy": -1,
                       "rotation_angle": -1,
                       "x_pixel_size": -1,
                       "y_pixel_size": -1}
                  }
        h5_out_fn = (str(date) + "_" + str(sample) + "_" +
                     str(energy) + "_" + str(zpz) + "_stack.hdf5")
        h5_out = root_path + "/" + h5_out_fn
        print(h5_out)
        dict2hdf5(indict, h5_out)
        ####


    # TODO: store stack records in a new table in the DB


    db.close()
    print("--- End: Individual images to stack took %s seconds ---" %
          (time.time() - start_time))




def main():

    #file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
    #             "PARALLEL_IMAGING/image_operate_xrm_test_add/" \
    #             "tests6/xrm/index.json"

    file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
                 "PARALLEL_IMAGING/PARALLEL_XRM2H5/tomo05/index.json"

    many_to_stack(file_index, table_name="hdf5_proc", hdf5_structure=None,
                  date=20171122, sample="tomo05", energy=520.0, zpz=None)

    #20171122_tomo05_520.0



if __name__ == "__main__":
    main()


