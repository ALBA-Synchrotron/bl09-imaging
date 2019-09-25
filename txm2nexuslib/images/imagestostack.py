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
from operator import itemgetter

from joblib import Parallel, delayed

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage

from txm2nexuslib.parser import get_file_paths
from txm2nexuslib.images.util import filter_file_index, dict2hdf5


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
    elif (type_struct == "normalized_multifocus" or
          type_struct == "normalized_simple"):
        hdf5_metadata_structure_dict = {"TomoNormalized": {
            "energy": [],
            "rotation_angle": [],
            "x_pixel_size": [],
            "y_pixel_size": []}
        }
    elif type_struct == "normalized_spectroscopy":
        hdf5_metadata_structure_dict = {"SpecNormalized": {
            "energy": [],
            "rotation_angle": [],
            "x_pixel_size": [],
            "y_pixel_size": []}
        }
    elif type_struct == "normalized_magnetism_many_repetitions":
        hdf5_metadata_structure_dict = {"TomoNormalized": {
            "energy": [],
            "rotation_angle": [],
            "x_pixel_size": [],
            "y_pixel_size": [],
            "jj_offset": []}
        }
    elif type_struct == "aligned" or type_struct == "aligned_multifocus":
        hdf5_metadata_structure_dict = {"FastAligned": {
            "energy": [],
            "rotation_angle": [],
            "x_pixel_size": [],
            "y_pixel_size": []}
        }
    else:
        pass
    return hdf5_metadata_structure_dict

def metadata_2_stack_dict(hdf5_structure_dict,
                          files_for_stack, ff_filenames=None,
                          type_struct="normalized",
                          avg_ff_dataset="data"):
    """ Transfer data from many hdf5 individual image files
    into a single hdf5 stack file.
    This method is quite specific for normalized BL09 images"""

    data_filenames = files_for_stack["data"]

    num_keys = len(hdf5_structure_dict)
    if num_keys == 1:
        k, hdf5_structure_dict = hdf5_structure_dict.items()[0]

    def extract_metadata_original(metadata_original, hdf5_structure_dict):
        for dataset_name in hdf5_structure_dict:
            if dataset_name in metadata_original:
                value = metadata_original[dataset_name].value
                if (dataset_name == "energy" and
                        type_struct != "normalized_spectroscopy"):
                    value = round(value, 1)
                elif (dataset_name == "energy" and
                      type_struct == "normalized_spectroscopy"):
                    value = round(value, 2)
                hdf5_structure_dict[dataset_name].append(value)

    if type_struct == "normalized_magnetism_many_repetitions":
        jj_offset = files_for_stack["jj_offset"]
        hdf5_structure_dict["jj_offset"] = [jj_offset]

    c = 0
    for file in data_filenames:
        # print(file)
        f = h5py.File(file, "r")
        # Process metadata
        metadata_original = f["metadata"]
        extract_metadata_original(metadata_original, hdf5_structure_dict)
        if (type_struct == "normalized" or
                type_struct == "normalized_simple" or
                type_struct == "normalized_multifocus" or
                type_struct == "normalized_magnetism_many_repetitions" or
                type_struct == "normalized_spectroscopy" or
                type_struct == "aligned" or
                type_struct == "aligned_multifocus"):
            if c == 0:
                hdf5_structure_dict["x_pixel_size"].append(
                    round(metadata_original["pixel_size"].value, 6))
                hdf5_structure_dict["y_pixel_size"].append(
                    round(metadata_original["pixel_size"].value, 6))
            if ("energy" not in hdf5_structure_dict and
                    type_struct != "normalized_spectroscopy"):
                hdf5_structure_dict["energy"].append(
                    round(metadata_original["energy"].value, 1))
            elif ("energy" not in hdf5_structure_dict and
                  type_struct == "normalized_spectroscopy"):
                hdf5_structure_dict["energy"].append(
                    round(metadata_original["energy"].value, 2))
            hdf5_structure_dict["rotation_angle"].append(
                round(metadata_original["angle"].value, 1))
        if type_struct == "normalized":
            hdf5_structure_dict["ExpTimesTomo"].append(
                round(metadata_original["exposure_time"].value, 2))
            hdf5_structure_dict["CurrentsTomo"].append(
                round(metadata_original["machine_current"].value, 6))
        f.close()
        c += 1

    c = 0
    if ff_filenames and type_struct == "normalized":
        for ff_file in ff_filenames:
            f = h5py.File(ff_file, "r")
            metadata_original = f["metadata"]
            # Process metadata
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

    if (type_struct == "normalized" or
            type_struct == "normalized_simple" or
            type_struct == "normalized_multifocus" or
            type_struct == "normalized_magnetism_many_repetitions"):
        main_grp = "TomoNormalized"
        main_dataset = "TomoNormalized"
        if ff_filenames and type_struct == "normalized":
            ff_dataset = "FFNormalizedWithCurrent"
    elif type_struct == "normalized_spectroscopy":
        main_grp = "SpecNormalized"
        main_dataset = "spectroscopy_normalized"
    elif type_struct == "aligned" or type_struct == "aligned_multifocus":
        main_grp = "FastAligned"
        main_dataset = "tomo_aligned"
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
        h5_stack_file_handler[main_grp][main_dataset][
            num_img] = f[dataset].value
        f.close()
        num_img += 1

    if ff_filenames and type_struct == "normalized":
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


def make_stack(files_for_stack, root_path, type_struct="normalized",
               suffix="_stack"):

    data_files = files_for_stack["data"]
    if "ff" in files_for_stack:
        data_files_ff = files_for_stack["ff"]
    else:
        data_files_ff = None
    date = files_for_stack["date"]
    sample = files_for_stack["sample"]
    if type_struct != "normalized_spectroscopy":
        energy = files_for_stack["energy"]
    if "zpz" in files_for_stack:
        zpz = files_for_stack["zpz"]
    elif type_struct == "normalized_magnetism_many_repetitions":
        jj_offset = files_for_stack["jj_offset"]

    # Creation of dictionary
    h5_struct_dict = create_structure_dict(type_struct=type_struct)
    data_dict = metadata_2_stack_dict(h5_struct_dict,
                                      files_for_stack,
                                      ff_filenames=data_files_ff,
                                      type_struct=type_struct)

    # Creation of hdf5 stack
    record = {}
    if type_struct == "normalized":
        h5_out_fn = (str(date) + "_" + str(sample) + "_" +
                     str(energy) + "_" + str(zpz) + suffix + ".hdf5")
        record.update({"energy": energy, "zpz": zpz})
    elif (type_struct == "normalized_multifocus" or
          type_struct == "normalized_simple"):
        h5_out_fn = (str(date) + "_" + str(sample) + "_" +
                     str(energy) + suffix + ".hdf5")
        record.update({"energy": energy})
    elif type_struct == "normalized_spectroscopy":
        h5_out_fn = (str(date) + "_" + str(sample) +
                     suffix + ".hdf5")
    elif type_struct == "normalized_magnetism_many_repetitions":
        h5_out_fn = (str(date) + "_" + str(sample) + "_" +
                     str(energy) + "_" + str(jj_offset) + suffix + ".hdf5")
        record.update({"energy": energy})
    if type_struct == "aligned":
        h5_out_fn = (str(date) + "_" + str(sample) + "_" +
                     str(energy) + "_" + str(zpz) + suffix + "_ali.hdf5")
        record.update({"energy": energy, "zpz": zpz})
    if type_struct == "aligned_multifocus":
        h5_out_fn = (str(date) + "_" + str(sample) + "_" +
                     str(energy) + suffix + "_ali.hdf5")
        record.update({"energy": energy})
    h5_out_fn = root_path + "/" + h5_out_fn
    h5_stack_file_handler = h5py.File(h5_out_fn, "w")
    dict2hdf5(h5_stack_file_handler, data_dict)
    data_2_hdf5(h5_stack_file_handler,
                data_files, ff_filenames=data_files_ff,
                type_struct=type_struct)

    h5_stack_file_handler.flush()
    h5_stack_file_handler.close()

    record.update({"filename": os.path.basename(h5_out_fn),
                   "extension": ".hdf5",
                   "type": type_struct, "stack": True,
                   "date": date, "sample": sample})
    return record


def many_images_to_h5_stack(file_index_fn, table_name="hdf5_proc",
                            type_struct="normalized", suffix="_stack",
                            date=None, sample=None, energy=None, zpz=None,
                            ff=None, subfolders=False, cores=-2):
    """Go from many images hdf5 files to a single stack of images
    hdf5 file.
    Using all cores but one, for the computations"""

    # TODO: spectroscopy normalized not implemented (no Avg FF, etc)
    print("--- Individual images to stacks ---")
    start_time = time.time()
    file_index_db = TinyDB(file_index_fn,
                           storage=CachingMiddleware(JSONStorage))
    db = file_index_db
    if table_name is not None:
        file_index_db = file_index_db.table(table_name)

    files_query = Query()
    if (date is not None or sample is not None or energy is not None or
            zpz is not None or ff is not None):
        file_index_db = filter_file_index(file_index_db, files_query,
                                          date=date, sample=sample,
                                          energy=energy,
                                          zpz=zpz, ff=ff)

    root_path = os.path.dirname(os.path.abspath(file_index_fn))
    all_file_records = file_index_db.all()
    stack_table = db.table("hdf5_stacks")
    stack_table.purge()
    files_list = []

    if type_struct == "normalized" or type_struct == "aligned":
        dates_samples_energies_zpzs = []
        for record in all_file_records:
            dates_samples_energies_zpzs.append((record["date"],
                                                record["sample"],
                                                record["energy"],
                                                record["zpz"]))
        dates_samples_energies_zpzs = list(set(dates_samples_energies_zpzs))
        for date_sample_energy_zpz in dates_samples_energies_zpzs:
            date = date_sample_energy_zpz[0]
            sample = date_sample_energy_zpz[1]
            energy = date_sample_energy_zpz[2]
            zpz = date_sample_energy_zpz[3]

            # Query building parts
            da = (files_query.date == date)
            sa = (files_query.sample == sample)
            en = (files_query.energy == energy)
            zp = (files_query.zpz == zpz)
            ff_false = (files_query.FF == False)
            ff_true = (files_query.FF == True)

            data_files_ff = []
            if file_index_db.search(files_query.FF.exists()):
                # Query command
                query_cmd_ff = (da & sa & en & ff_true)
                h5_ff_records = file_index_db.search(query_cmd_ff)
                data_files_ff = get_file_paths(h5_ff_records, root_path,
                                               use_subfolders=subfolders)
            if file_index_db.search(files_query.FF.exists()):
                # Query command
                query_cmd = (da & sa & en & zp & ff_false)
            else:
                # Query command
                query_cmd = (da & sa & en & zp)
            h5_records = file_index_db.search(query_cmd)
            h5_records = sorted(h5_records, key=itemgetter('angle'))

            data_files = get_file_paths(h5_records, root_path,
                                        use_subfolders=subfolders)
            files_dict = {"data": data_files, "ff": data_files_ff,
                          "date": date, "sample": sample, "energy": energy,
                          "zpz": zpz}
            files_list.append(files_dict)
    elif (type_struct == "normalized_multifocus" or
          type_struct == "normalized_simple" or
          type_struct == "aligned_multifocus"):
        dates_samples_energies = []
        for record in all_file_records:
            dates_samples_energies.append((record["date"],
                                           record["sample"],
                                           record["energy"]))
        dates_samples_energies = list(set(dates_samples_energies))
        for date_sample_energy in dates_samples_energies:
            date = date_sample_energy[0]
            sample = date_sample_energy[1]
            energy = date_sample_energy[2]

            # Query building parts
            da = (files_query.date == date)
            sa = (files_query.sample == sample)
            en = (files_query.energy == energy)

            # Query command
            query_cmd = (da & sa & en)
            h5_records = file_index_db.search(query_cmd)
            h5_records = sorted(h5_records, key=itemgetter('angle'))

            data_files = get_file_paths(h5_records, root_path,
                                        use_subfolders=subfolders)
            files_dict = {"data": data_files, "date": date, "sample": sample,
                          "energy": energy}
            files_list.append(files_dict)

    elif type_struct == "normalized_magnetism_many_repetitions":
        dates_samples_energies_jjs = []
        for record in all_file_records:
            dates_samples_energies_jjs.append((record["date"],
                                               record["sample"],
                                               record["energy"],
                                               record["jj_offset"]))

        dates_samples_energies_jjs = list(set(dates_samples_energies_jjs))
        for date_sample_energy_jj in dates_samples_energies_jjs:
            date = date_sample_energy_jj[0]
            sample = date_sample_energy_jj[1]
            energy = date_sample_energy_jj[2]
            jj_offset = date_sample_energy_jj[3]

            # Raw image records by given date, sample and energy
            query_cmd = ((files_query.date == date) &
                         (files_query.sample == sample) &
                         (files_query.energy == energy) &
                         (files_query.jj_offset == jj_offset))
            h5_records = file_index_db.search(query_cmd)
            h5_records = sorted(h5_records, key=itemgetter('angle'))
            data_files = get_file_paths(h5_records, root_path,
                                        use_subfolders=subfolders)
            files_dict = {"data": data_files, "date": date, "sample": sample,
                          "energy": energy, "jj_offset": jj_offset}
            files_list.append(files_dict)
    elif type_struct == "normalized_spectroscopy":
        dates_samples = []
        for record in all_file_records:
            dates_samples.append((record["date"],
                                  record["sample"]))
        dates_samples = list(set(dates_samples))
        for date_sample in dates_samples:
            date = date_sample[0]
            sample = date_sample[1]

            # Query building parts
            da = (files_query.date == date)
            sa = (files_query.sample == sample)

            # Query command
            query_cmd = (da & sa)
            h5_records = file_index_db.search(query_cmd)
            h5_records = sorted(h5_records, key=itemgetter('energy'))

            data_files = get_file_paths(h5_records, root_path,
                                        use_subfolders=subfolders)
            files_dict = {"data": data_files, "date": date, "sample": sample}
            files_list.append(files_dict)

    # Parallelization of making the stacks
    records = Parallel(n_jobs=cores, backend="multiprocessing")(
        delayed(make_stack)(files_for_stack, root_path,
                            type_struct=type_struct, suffix=suffix
                            ) for files_for_stack in files_list)

    stack_table.insert_multiple(records)
    pretty_printer = pprint.PrettyPrinter(indent=4)
    print("Created stacks:")
    for record in stack_table.all():
        pretty_printer.pprint(record["filename"])
    db.close()

    print("--- Individual images to stacks took %s seconds ---\n" %
          (time.time() - start_time))


def main():

    file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
                 "PARALLEL_IMAGING/PARALLEL_XRM2H5/TOMOFEW/tomo_few_2/" \
                 "index.json"

    db = TinyDB(file_index)
    a = db.table("hdf5_proc")
    print(a.all())

    #many_images_to_h5_stack(file_index, type_struct="normalized")

    many_images_to_h5_stack(file_index, table_name="hdf5_averages",
                            type_struct="normalized")


if __name__ == "__main__":
    main()


