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
from shutil import copy

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.storages import MemoryStorage
from tinydb.middlewares import CachingMiddleware
from joblib import Parallel, delayed

from txm2nexuslib.parser import get_file_paths


def filter_file_index(file_index_db, files_query,
                      date=None, sample=None, energy=None, angle=None,
                      zpz=None, ff=None):
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
    if date or sample or energy or zpz or ff is not None:
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
        if angle:
            update_temp_db(temp_db, filtered, files_query.angle, angle)
            filtered = True
        if zpz:
            update_temp_db(temp_db, filtered, files_query.zpz, zpz)
        if ff is True or ff is False:
            update_temp_db(temp_db, filtered, files_query.FF, ff)
        return temp_db


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


def update_db_func(files_db, table_name, files_records, suffix=None, purge=True):
    """Create new DB table with records of hdf5 raw data (changing the
    extension to hdf5), or with records of processed files (adding a suffix).
    If suffix is not given (suffix None), the new DB will contain the same
    file names as the original DB but with .hdf5 extension; otherwise,
    a suffix is added to the already hdf5 filenames."""
    table = files_db.table(table_name)
    if purge is True:
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
                       use_subfolders=False, cores=-1, update_db=True,
                       query=None, purge=False,
                       magnetism_partial=False):
    """Copy many files to processed files"""
    # printer = pprint.PrettyPrinter(indent=4)

    start_time = time.time()

    db = TinyDB(file_index_db, storage=CachingMiddleware(JSONStorage))

    files_query = Query()
    if table_in_name == "default":
        query_cmd = (files_query.extension == ".hdf5")
        if query is not None:
            query_cmd &= query
        hdf5_records = db.search(query_cmd)
    else:
        table_in = db.table(table_in_name)
        hdf5_records = table_in.all()

    if magnetism_partial:
        query_cmd = (files_query.extension == ".hdf5")
        if query is not None:
            query_cmd &= query
        table_proc = db.table(table_out_name)
        table_proc.remove(query_cmd)

    # import pprint
    # prettyprinter = pprint.PrettyPrinter(indent=4)
    # prettyprinter.pprint(hdf5_records)

    root_path = os.path.dirname(os.path.abspath(file_index_db))
    files = get_file_paths(hdf5_records, root_path,
                           use_subfolders=use_subfolders)

    # The backend parameter can be either "threading" or "multiprocessing"

    Parallel(n_jobs=cores, backend="multiprocessing")(
        delayed(copy_2_proc)(h5_file, suffix) for h5_file in files)

    if update_db:
        update_db_func(db, table_out_name, hdf5_records, suffix, purge=purge)

    n_files = len(files)
    print("--- Copy for processing %d files took %s seconds ---\n" %
          (n_files, (time.time() - start_time)))

    #print(db.table(table_out_name).all())
    db.close()


def query_command_for_same_sample(db_filename, table_name="hdf5_proc"):
    """Get the query command for a given sample: date_sample_energy
    This query will allow to retrieve the tiny DB records of a given sample.
    Thanks to it, we could check in other functions/methods if many
    a single zpz (single focus) or multiple zpz (multi focus) are used."""

    db = TinyDB(db_filename, storage=CachingMiddleware(JSONStorage))
    stack_table = db.table(table_name)
    file_records = stack_table.all()
    dates_samples_energies = []
    for record in file_records:
        data = (record["date"], record["sample"], record["energy"])
        dates_samples_energies.append(data)
    dates_samples_energies = list(set(dates_samples_energies))

    files_query = Query()
    for date_sample_energy in dates_samples_energies:
        date = date_sample_energy[0]
        sample = date_sample_energy[1]
        energy = date_sample_energy[2]

        # Get all hdf5 files corresponding to the projections that are being
        # processed for a single tomo (single focus tomo or multifocus tomo)
        tomo_projections_query = ((files_query.date == date) &
                                  (files_query.sample == sample) &
                                  (files_query.energy == energy) &
                                  (files_query.FF == False))
    db.close()
    return tomo_projections_query


def check_if_multiple_zps(db_filename, query=None):
    single_zp_bool = True
    db = TinyDB(db_filename,
                storage=CachingMiddleware(JSONStorage))
    if query is not None:
        file_records = db.search(query)

    zp_previous_record = file_records[0]['zpz']
    for record in file_records:
        current_zpz = record['zpz']
        if current_zpz != zp_previous_record:
            single_zp_bool = False
            break
        zp_previous_record = current_zpz
    db.close()
    return single_zp_bool


def dict2hdf5(h5_file_handler, indict):
    """
    Create hdf5 file from a python dictionary. Convert a python dictionary
    to a hdf5 organization. This method accepts four levels of dictionaries
    inside the main dictionary.
    outfilename: indicate the ouput hdf5 filename.
    indict: input dictionary to be converted.
    """

    def create_dataset(group, key_name, value):
        try:
            group.create_dataset(key_name, data=value)
        except Exception:
            print("data in key '" + key_name + "' could not be extracted")

    for key0, val0 in indict.items():
        if type(val0) is not dict:
            create_dataset(h5_file_handler, key0, val0)
        else:
            grp1 = h5_file_handler.create_group(key0)
            for k1, v1 in val0.items():
                if type(v1) is not dict:
                    create_dataset(grp1, k1, v1)
                else:
                    grp2 = grp1.create_group(k1)
                    for k2, v2 in v1.items():
                        if type(v2) is not dict:
                            create_dataset(grp2, k2, v2)
                        else:
                            grp3 = grp2.create_group(k2)
                            for k3, v3 in v2.items():
                                if type(v3) is not dict:
                                    create_dataset(grp3, k3, v3)

