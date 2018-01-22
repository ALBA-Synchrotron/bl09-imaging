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
import pprint
import numpy as np
from joblib import Parallel, delayed
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage

from txm2nexuslib.parser import get_file_paths
from txm2nexuslib.images.util import dict2hdf5


def create_structure_dict(type_struct="normalized"):
    # Construct a dictionary with the metadata structure representing
    # the future hdf5 structure
    if type_struct == "normalized":
        hdf5_metadata_structure_dict = {"TomoNormalized": {
            "AverageFF": [],
            "Avg_FF_ExpTime": [],
            "CurrentsFF": [],
            "CurrentsTomo": [],
            "ExpTimesTomo": [],
            "energy": [],
            "rotation_angle": [],
            "x_pixel_size": [],
            "y_pixel_size": []}
        }
    elif type_struct == "aligned":
        pass
    else:
        pass
    return hdf5_metadata_structure_dict


def metadata_2_stack_dict(hdf5_structure_dict,
                          data_filenames, ff_filenames=None,
                          type_struct="normalized",
                          avg_ff_dataset="data"):
    """ Transfer data from many hdf5 individual image files
    into a single hdf5 stack file.
    This method is quite specific for normalized BL09 images"""

    num_keys = len(hdf5_structure_dict)
    if num_keys == 1:
        k, hdf5_structure_dict = hdf5_structure_dict.items()[0]

    def extract_metadata_original(metadata_original, hdf5_structure_dict):
        for dataset_name in hdf5_structure_dict:
            if dataset_name in metadata_original:
                hdf5_structure_dict[dataset_name].append(
                    metadata_original[dataset_name].value)
    c = 0
    for file in data_filenames:
        #print(file)
        f = h5py.File(file, "r")
        # Process metadata
        metadata_original = f["metadata"]
        extract_metadata_original(metadata_original, hdf5_structure_dict)

        if type_struct == "normalized":
            if c == 0:
                hdf5_structure_dict["x_pixel_size"].append(
                    metadata_original["pixel_size"].value)
                hdf5_structure_dict["y_pixel_size"].append(
                    metadata_original["pixel_size"].value)
            hdf5_structure_dict["ExpTimesTomo"].append(
                metadata_original["exposure_time"].value)
            hdf5_structure_dict["rotation_angle"].append(
                metadata_original["angle"].value)
            hdf5_structure_dict["CurrentsTomo"].append(
                metadata_original["machine_current"].value)
        f.close()
        c += 1

    c = 0
    if ff_filenames:
        for ff_file in ff_filenames:
            #print(ff_file)
            f = h5py.File(ff_file, "r")
            metadata_original = f["metadata"]
            # Process metadata
            if type_struct == "normalized":
                if c == 0:
                    hdf5_structure_dict["Avg_FF_ExpTime"].append(
                        metadata_original["exposure_time"].value)
                    hdf5_structure_dict["AverageFF"] = f[avg_ff_dataset].value
                hdf5_structure_dict["CurrentsFF"].append(
                    metadata_original["machine_current"].value)
            f.close()
            c += 1
    if num_keys == 1:
        hdf5_structure_dict = {k: hdf5_structure_dict}
    return hdf5_structure_dict


def data_2_hdf5(h5_stack_file_handler,
                data_filenames, ff_filenames=None,
                type_struct="normalized",
                dataset="data"):
    """Generic method to create an hdf5 stack of images from individual
    images"""

    if type_struct == "normalized":
        main_grp = "TomoNormalized"
        main_dataset = "TomoNormalized"
        ff_dataset = "FFNormalizedWithCurrent"
    elif type_struct == "aligned":
        pass
    else:
        pass

    num_img = 0
    for file in data_filenames:
        # Images normalized
        f = h5py.File(file, "r")
        if num_img == 0:
            n_frames = len(data_filenames)
            num_rows, num_columns = np.shape(f[dataset].value)
            h5_stack_file_handler[main_grp].create_dataset(
                main_dataset,
                shape=(n_frames, num_rows, num_columns),
                chunks=(1, num_rows, num_columns),
                dtype='float32')
            h5_stack_file_handler[main_grp][main_dataset].attrs[
                'Number of Frames'] = n_frames
            # FF images normalized by machine_current and exp time
        h5_stack_file_handler[main_grp][main_dataset][
            num_img] = f[dataset].value
        f.close()
        num_img += 1

    if ff_filenames:
        # FF images normalized by machine_current and exp time
        num_img_ff = 0
        for ff_file in ff_filenames:
            f = h5py.File(ff_file, "r")
            if num_img_ff == 0:
                n_ff_frames = len(ff_filenames)
                num_rows, num_columns = np.shape(f[dataset].value)
                h5_stack_file_handler[main_grp].create_dataset(
                    ff_dataset,
                    shape=(n_ff_frames, num_rows, num_columns),
                    chunks=(1, num_rows, num_columns),
                    dtype='float32')
                h5_stack_file_handler[main_grp][ff_dataset].attrs[
                    'Number of Frames'] = n_ff_frames
            h5_stack_file_handler[main_grp][ff_dataset][
                num_img_ff] = f[dataset].value
            f.close()
            num_img_ff += 1


def make_stack(files_for_stack, root_path, type_struct="normalized"):

    data_files = files_for_stack["data"]
    data_files_ff = files_for_stack["ff"]
    date = files_for_stack["date"]
    sample = files_for_stack["sample"]
    energy = files_for_stack["energy"]
    zpz = files_for_stack["zpz"]

    # Creation of dictionary
    h5_struct_dict = create_structure_dict(type_struct=type_struct)
    data_dict = metadata_2_stack_dict(h5_struct_dict,
                                      data_files,
                                      ff_filenames=data_files_ff,
                                      type_struct=type_struct)

    # Creation of hdf5 stack
    h5_out_fn = (str(date) + "_" + str(sample) + "_" +
                 str(energy) + "_" + str(zpz) + "_stack.hdf5")
    h5_out_fn = root_path + "/" + h5_out_fn
    h5_stack_file_handler = h5py.File(h5_out_fn, "w")
    dict2hdf5(h5_stack_file_handler, data_dict)
    data_2_hdf5(h5_stack_file_handler,
                data_files, ff_filenames=data_files_ff,
                type_struct="normalized")

    h5_stack_file_handler.flush()
    h5_stack_file_handler.close()
    # Record does not contain energy and zpz because in some cases
    # the same stack could contain many different energies or
    # many different zpz
    record = {"filename": os.path.basename(h5_out_fn),
              "extension": ".hdf5",
              "date": date, "sample": sample, "stack": True}
    record.update({"type": type_struct})
    return record


def many_images_to_h5_stack(file_index_fn, table_name="hdf5_proc",
                            type_struct="normalized",
                            date=None, sample=None, energy=None, zpz=None,
                            cores=-1):
    """Go from many images hdf5 files to a single stack of images
    hdf5 file"""

    # TODO: spectroscopy normalized not implemented (no Avg FF, etc)

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

    root_path = os.path.dirname(os.path.abspath(file_index_fn))
    all_file_records = file_index_db.all()

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

    stack_table = db.table("hdf5_stacks")
    stack_table.purge()

    files_list = []
    for date_sample_energy_zpz in dates_samples_energies_zpzs:
        date = date_sample_energy_zpz[0]
        sample = date_sample_energy_zpz[1]
        energy = date_sample_energy_zpz[2]
        zpz = date_sample_energy_zpz[3]

        # Image records by given date, sample, energy and zpz
        query_cmd = ((files_query.date == date) &
                     (files_query.sample == sample) &
                     (files_query.energy == energy) &
                     (files_query.zpz == zpz) &
                     (files_query.FF == False))
        h5_records = file_index_db.search(query_cmd)
        data_files = get_file_paths(h5_records, root_path)

        query_cmd_ff = ((files_query.date == date) &
                        (files_query.sample == sample) &
                        (files_query.energy == energy) &
                        (files_query.FF == True))
        h5_ff_records = file_index_db.search(query_cmd_ff)
        data_files_ff = get_file_paths(h5_ff_records, root_path)
        files_dict = {"data": data_files, "ff": data_files_ff,
                      "date": date, "sample": sample, "energy": energy,
                      "zpz": zpz}
        files_list.append(files_dict)

    # Parallization of making the stacks
    records = Parallel(n_jobs=cores, backend="multiprocessing")(
        delayed(make_stack)(files_for_stack, root_path,
                            type_struct=type_struct
                            ) for files_for_stack in files_list)

    stack_table.insert_multiple(records)
    pretty_printer = pprint.PrettyPrinter(indent=4)
    print("Stacks created:")
    for record in stack_table.all():
        pretty_printer.pprint(record["filename"])
    db.close()

    print("--- End: Individual images to stacks took %s seconds ---\n" %
          (time.time() - start_time))


def main():

    file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
                 "PARALLEL_IMAGING/image_operate_xrm_test_add/" \
                 "tests6/xrm/index.json"

    #file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
    #             "PARALLEL_IMAGING/PARALLEL_XRM2H5/tomo05/index.json"

    many_images_to_h5_stack(file_index, table_name="hdf5_proc",
                            type_struct="normalized")


if __name__ == "__main__":
    main()


