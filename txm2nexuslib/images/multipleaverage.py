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

from txm2nexuslib.image.image_operate_lib import Image
from txm2nexuslib.parser import get_file_paths
from txm2nexuslib.image.image_operate_lib import average_images
from txm2nexuslib.images.util import filter_file_index


def average_and_store(group_to_average_image_filenames,
                      dataset_for_averaging="data",
                      variable="zpz", description="",
                      dataset_store="data", jj=True):

    if variable == "zpz":
        zp_central = group_to_average_image_filenames[0]
        images_to_average_filenames = group_to_average_image_filenames[1]
        date_sample_energy_angle = group_to_average_image_filenames[2]
        fn_first = images_to_average_filenames[0]
        dir_name = os.path.dirname(fn_first)
        date = date_sample_energy_angle[0]
        sample = date_sample_energy_angle[1]
        energy = date_sample_energy_angle[2]
        angle = date_sample_energy_angle[3]
        output_fn = (str(date) + "_" + str(sample) + "_" + str(energy) +
                     "_" + str(angle) + "_" +
                     str(zp_central) + "_avg_zpz.hdf5")
        output_complete_fn = dir_name + "/" + output_fn
        average_images(images_to_average_filenames,
                       dataset_for_average=dataset_for_averaging,
                       description=description, store=True,
                       output_h5_fn=output_complete_fn,
                       dataset_store=dataset_store)

        # Store metadata
        # TODO: Do average of values of each group of images to be averaged
        # For the moment we take the first image ([0] index)

        record = {"filename": output_fn, "extension": ".hdf5",
                  "date": date, "sample": sample, "energy": energy,
                  "angle": angle, "average": True, "avg_by": "zpz",
                  "zpz": zp_central, "zpz_central": zp_central}

    elif variable == "repetition" and jj:

        num_repetitions = group_to_average_image_filenames[0]
        images_to_average_filenames = group_to_average_image_filenames[1]
        date_sample_energy_jj_angle = group_to_average_image_filenames[2]
        fn_first = images_to_average_filenames[0]
        dir_name = os.path.dirname(fn_first)

        date = date_sample_energy_jj_angle[0]
        sample = date_sample_energy_jj_angle[1]
        energy = date_sample_energy_jj_angle[2]
        jj_u = date_sample_energy_jj_angle[3]
        jj_d = date_sample_energy_jj_angle[4]
        angle = date_sample_energy_jj_angle[5]

        jj_offset = round((jj_u + jj_d)/2.0, 2)

        output_fn = (str(date) + "_" + str(sample) + "_" + str(energy) +
                     "_" + str(jj_offset) + "_" + str(angle) +
                     "_avg_repetitions.hdf5")
        output_complete_fn = dir_name + "/" + output_fn
        average_images(images_to_average_filenames,
                       dataset_for_average=dataset_for_averaging,
                       description=description, store=True,
                       output_h5_fn=output_complete_fn,
                       dataset_store=dataset_store)

        # Store metadata: extracting metadata from repetition 0
        record = {"filename": output_fn, "extension": ".hdf5",
                  "date": date, "sample": sample, "energy": energy,
                  "jj_u": jj_u, "jj_d": jj_d, "jj_offset": jj_offset,
                  "angle": angle, "average": True, "avg_by": "repetition",
                  "num_repetitions": num_repetitions}

    elif variable == "repetition" and not jj:

        num_repetitions = group_to_average_image_filenames[0]
        images_to_average_filenames = group_to_average_image_filenames[1]
        date_sample_energy = group_to_average_image_filenames[2]
        fn_first = images_to_average_filenames[0]
        dir_name = os.path.dirname(fn_first)

        date = date_sample_energy[0]
        sample = date_sample_energy[1]
        energy = date_sample_energy[2]

        output_fn = (str(date) + "_" + str(sample) + "_" + str(energy) +
                     "_avg_repetitions.hdf5")
        output_complete_fn = dir_name + "/" + output_fn
        average_images(images_to_average_filenames,
                       dataset_for_average=dataset_for_averaging,
                       description=description, store=True,
                       output_h5_fn=output_complete_fn,
                       dataset_store=dataset_store)

        # Store metadata: extracting metadata from repetition 0
        record = {"filename": output_fn, "extension": ".hdf5",
                  "date": date, "sample": sample, "energy": energy,
                  "average": True, "avg_by": "repetition",
                  "num_repetitions": num_repetitions}

    img_in_obj = Image(images_to_average_filenames[0], mode="r")
    h5_in = img_in_obj.f_h5_handler
    img_avg_obj = Image(output_complete_fn)
    h5_avg = img_avg_obj.f_h5_handler

    metadata_in = "metadata"
    metadata_out = "metadata"
    if metadata_in in h5_in:
        meta_in_grp = h5_in[metadata_in]
        if metadata_out not in h5_avg:
            meta_out_grp = h5_avg.create_group(metadata_out)
        if "/metadata/energy" in h5_in:
            energy = round(meta_in_grp["energy"].value, 1)
            meta_out_grp.create_dataset("energy", data=energy)
            meta_out_grp["energy"].attrs["units"] = "eV"
        if "/metadata/angle" in h5_in:
            angle = round(meta_in_grp["angle"].value, 2)
            if angle == 0:
                angle = 0.0
            meta_out_grp.create_dataset("angle", data=angle)
            meta_out_grp["angle"].attrs["units"] = "degree"
        if "/metadata/pixel_size" in h5_in:
            pixel_size = meta_in_grp["pixel_size"].value
            meta_out_grp.create_dataset("pixel_size", data=pixel_size)
            meta_out_grp["pixel_size"].attrs["units"] = "um"
        if "/metadata/magnification" in h5_in:
            magnification = meta_in_grp["magnification"].value
            meta_out_grp.create_dataset("magnification",
                                        data=magnification)
        if "/metadata/exposure_time" in h5_in:
            exposure_time = meta_in_grp["exposure_time"].value
            meta_out_grp.create_dataset("exposure_time",
                                        data=exposure_time)
            meta_out_grp["exposure_time"].attrs["units"] = "s"
        if "/metadata/machine_current" in h5_in:
            machine_current = meta_in_grp["machine_current"].value
            meta_out_grp.create_dataset("machine_current",
                                        data=machine_current)
            meta_out_grp["machine_current"].attrs["units"] = "mA"

    h5_in.close()
    img_avg_obj.close_h5()

    return record


def average_image_group_by_energy(file_index_fn, table_name="hdf5_proc",
                                  dataset_for_averaging="data",
                                  variable="repetition",
                                  description="", dataset_store="data",
                                  date=None, sample=None, energy=None):
    """ Method used in energyscan macro. Average by energy.
    Average images by repetition for a single energy.
    If date, sample and/or energy are indicated, only the corresponding
    images for the given date, sample and/or energy are processed.
    All data images of the same energy,
    for the different repetitions are averaged.
    """

    root_path = os.path.dirname(os.path.abspath(file_index_fn))

    file_index_db = TinyDB(file_index_fn,
                           storage=CachingMiddleware(JSONStorage))
    db = file_index_db
    if table_name is not None:
        file_index_db = file_index_db.table(table_name)

    files_query = Query()
    file_index_db = filter_file_index(file_index_db, files_query,
                                      date=date, sample=sample,
                                      energy=energy, ff=False)

    all_file_records = file_index_db.all()
    averages_table = db.table("hdf5_averages")

    # We only have files for a single energy
    if variable == "repetition":
        dates_samples_energies = []
        for record in all_file_records:
            dates_samples_energies.append((record["date"],
                                           record["sample"],
                                           record["energy"]))
        dates_samples_energies = list(
            set(dates_samples_energies))

        for date_sample_energy in dates_samples_energies:
            date = date_sample_energy[0]
            sample = date_sample_energy[1]
            energy = date_sample_energy[2]

            # Raw image records by given date, sample and energy
            query_cmd = ((files_query.date == date) &
                         (files_query.sample == sample) &
                         (files_query.energy == energy))
            img_records = file_index_db.search(query_cmd)

            num_repetitions = len(img_records)
            files = get_file_paths(img_records, root_path)
            complete_group_to_average = [num_repetitions]
            group_to_average = []
            for file in files:
                group_to_average.append(file)
            complete_group_to_average.append(group_to_average)
            complete_group_to_average.append(
                date_sample_energy)

            record = average_and_store(
                complete_group_to_average,
                dataset_for_averaging=dataset_for_averaging,
                variable=variable, description=description,
                dataset_store=dataset_store, jj=False)
            if record not in averages_table.all():
                averages_table.insert(record)
    #import pprint
    #pobj = pprint.PrettyPrinter(indent=4)
    #print("----")
    #print("average records")
    #for record in records:
    #    pobj.pprint(record)
    #pobj.pprint(averages_table.all())
    db.close()


def average_image_group_by_angle(file_index_fn, table_name="hdf5_proc",
                                 angle=0.0,
                                 dataset_for_averaging="data",
                                 variable="repetition",
                                 description="", dataset_store="data",
                                 date=None, sample=None, energy=None):
    """Average images by repetition for a single angle.
    If date, sample and/or energy are indicated, only the corresponding
    images for the given date, sample and/or energy are processed.
    All data images of the same angle,
    for the different repetitions are averaged.
    """

    root_path = os.path.dirname(os.path.abspath(file_index_fn))

    file_index_db = TinyDB(file_index_fn,
                           storage=CachingMiddleware(JSONStorage))
    db = file_index_db
    if table_name is not None:
        file_index_db = file_index_db.table(table_name)

    files_query = Query()
    file_index_db = filter_file_index(file_index_db, files_query,
                                      date=date, sample=sample,
                                      energy=energy, angle=angle, ff=False)

    all_file_records = file_index_db.all()
    averages_table = db.table("hdf5_averages")

    # We only have files for a single angle
    if variable == "repetition":
        dates_samples_energies_jjs_angles = []
        for record in all_file_records:
            dates_samples_energies_jjs_angles.append((record["date"],
                                                      record["sample"],
                                                      record["energy"],
                                                      record["jj_u"],
                                                      record["jj_d"],
                                                      record["angle"]))
        dates_samples_energies_jjs_angles = list(
            set(dates_samples_energies_jjs_angles))

        for date_sample_energy_jj_angle in dates_samples_energies_jjs_angles:
            date = date_sample_energy_jj_angle[0]
            sample = date_sample_energy_jj_angle[1]
            energy = date_sample_energy_jj_angle[2]
            jj_u = date_sample_energy_jj_angle[3]
            jj_d = date_sample_energy_jj_angle[4]
            angle = date_sample_energy_jj_angle[5]

            # Raw image records by given date, sample and energy
            query_cmd = ((files_query.date == date) &
                         (files_query.sample == sample) &
                         (files_query.energy == energy) &
                         (files_query.jj_u == jj_u) &
                         (files_query.jj_d == jj_d) &
                         (files_query.angle == angle))
            img_records = file_index_db.search(query_cmd)

            num_repetitions = len(img_records)
            files = get_file_paths(img_records, root_path)
            complete_group_to_average = [num_repetitions]
            group_to_average = []
            for file in files:
                group_to_average.append(file)
            complete_group_to_average.append(group_to_average)
            complete_group_to_average.append(
                date_sample_energy_jj_angle)

            record = average_and_store(
                complete_group_to_average,
                dataset_for_averaging=dataset_for_averaging,
                variable=variable, description=description,
                dataset_store=dataset_store)
            if record not in averages_table.all():
                averages_table.insert(record)
    #import pprint
    #pobj = pprint.PrettyPrinter(indent=4)
    #print("----")
    #print("average records")
    #for record in records:
    #    pobj.pprint(record)
    #pobj.pprint(averages_table.all())
    db.close()


def average_image_groups(file_index_fn, table_name="hdf5_proc",
                         dataset_for_averaging="data", variable="zpz",
                         description="", dataset_store="data",
                         date=None, sample=None, energy=None, cores=-2,
                         jj=True):
    """Average images of one experiment by zpz.
    If date, sample and/or energy are indicated, only the corresponding
    images for the given date, sample and/or energy are processed.
    The average of the different groups of images will be done in parallel:
    all cores but one used (Value=-2). All data images of the same angle,
    for the different ZPz are averaged.
    """

    """
    TODO: In the future it should be made available, the
     average by variable == repetition and just after by
     variable == zpz.

     Finally this three features should exist:
     - average by same angle and different zpz positions (DONE)
     - average by same angle, same zpz and different repetition (ONGOING)
     - average by same angle, first by same zpz and different repetition,
     and afterwards by same angle and different zpz positions (TODO)
    """

    start_time = time.time()
    root_path = os.path.dirname(os.path.abspath(file_index_fn))

    file_index_db = TinyDB(file_index_fn,
                           storage=CachingMiddleware(JSONStorage))
    db = file_index_db
    if table_name is not None:
        file_index_db = file_index_db.table(table_name)

    files_query = Query()
    file_index_db = filter_file_index(file_index_db, files_query,
                                      date=date, sample=sample,
                                      energy=energy, ff=False)

    all_file_records = file_index_db.all()
    n_files = len(all_file_records)

    averages_table = db.table("hdf5_averages")
    averages_table.purge()

    groups_to_average = []
    if variable == "zpz":
        dates_samples_energies_angles = []
        for record in all_file_records:
            dates_samples_energies_angles.append((record["date"],
                                                  record["sample"],
                                                  record["energy"],
                                                  record["angle"]))
        dates_samples_energies_angles = list(
            set(dates_samples_energies_angles))
        for date_sample_energy_angle in dates_samples_energies_angles:
            date = date_sample_energy_angle[0]
            sample = date_sample_energy_angle[1]
            energy = date_sample_energy_angle[2]
            angle = date_sample_energy_angle[3]

            # Raw image records by given date, sample and energy
            query_cmd = ((files_query.date == date) &
                         (files_query.sample == sample) &
                         (files_query.energy == energy) &
                         (files_query.angle == angle))
            img_records = file_index_db.search(query_cmd)
            num_zpz = len(img_records)
            central_zpz = 0
            for img_record in img_records:
                central_zpz += img_record["zpz"]
            central_zpz /= round(float(num_zpz), 1)

            files = get_file_paths(img_records, root_path)
            central_zpz_with_group_to_average = [central_zpz]
            group_to_average = []
            for file in files:
                group_to_average.append(file)
            central_zpz_with_group_to_average.append(group_to_average)
            central_zpz_with_group_to_average.append(date_sample_energy_angle)
            groups_to_average.append(central_zpz_with_group_to_average)

    elif variable == "repetition" and jj:
        dates_samples_energies_jjs_angles = []
        for record in all_file_records:
            dates_samples_energies_jjs_angles.append((record["date"],
                                                      record["sample"],
                                                      record["energy"],
                                                      record["jj_u"],
                                                      record["jj_d"],
                                                      record["angle"]))
        dates_samples_energies_jjs_angles = list(
            set(dates_samples_energies_jjs_angles))

        for date_sample_energy_jj_angle in dates_samples_energies_jjs_angles:
            date = date_sample_energy_jj_angle[0]
            sample = date_sample_energy_jj_angle[1]
            energy = date_sample_energy_jj_angle[2]
            jj_u = date_sample_energy_jj_angle[3]
            jj_d = date_sample_energy_jj_angle[4]
            angle = date_sample_energy_jj_angle[5]

            # Raw image records by given date, sample and energy
            query_cmd = ((files_query.date == date) &
                         (files_query.sample == sample) &
                         (files_query.energy == energy) &
                         (files_query.jj_u == jj_u) &
                         (files_query.jj_d == jj_d) &
                         (files_query.angle == angle))
            img_records = file_index_db.search(query_cmd)
            num_repetitions = len(img_records)
            files = get_file_paths(img_records, root_path)
            complete_group_to_average = [num_repetitions]
            group_to_average = []
            for file in files:
                group_to_average.append(file)
            complete_group_to_average.append(group_to_average)
            complete_group_to_average.append(
                date_sample_energy_jj_angle)
            groups_to_average.append(complete_group_to_average)

    elif variable == "repetition" and not jj:
        dates_samples_energies = []
        for record in all_file_records:
            dates_samples_energies.append((record["date"],
                                           record["sample"],
                                           record["energy"]))
        dates_samples_energies = list(
            set(dates_samples_energies))

        for date_sample_energy in dates_samples_energies:
            date = date_sample_energy[0]
            sample = date_sample_energy[1]
            energy = date_sample_energy[2]

            # Raw image records by given date, sample and energy
            query_cmd = ((files_query.date == date) &
                         (files_query.sample == sample) &
                         (files_query.energy == energy))
            img_records = file_index_db.search(query_cmd)
            num_repetitions = len(img_records)
            files = get_file_paths(img_records, root_path)
            complete_group_to_average = [num_repetitions]
            group_to_average = []
            for file in files:
                group_to_average.append(file)
            complete_group_to_average.append(group_to_average)
            complete_group_to_average.append(date_sample_energy)
            groups_to_average.append(complete_group_to_average)

    if groups_to_average[0][1]:
        records = Parallel(n_jobs=cores, backend="multiprocessing")(
            delayed(average_and_store)(
                group_to_average,
                dataset_for_averaging=dataset_for_averaging,
                variable=variable, description=description,
                dataset_store=dataset_store, jj=jj
            ) for group_to_average in groups_to_average)
    averages_table.insert_multiple(records)

    print("--- Average %d files by groups, took %s seconds ---\n" %
          (n_files, (time.time() - start_time)))

    # import pprint
    # pobj = pprint.PrettyPrinter(indent=4)
    # print("----")
    # print("average records")
    # for record in records:
    #     pobj.pprint(record)
    db.close()


def main():

    #file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
    #             "PARALLEL_IMAGING/image_operate_xrm_test_add/" \
    #             "tests8/xrm/index.json"

    file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
                 "PARALLEL_IMAGING/PARALLEL_XRM2H5/TOMOFEW/tomo_few/index.json"

    average_image_groups(file_index)
    # sample="ols", energy=640, date=20161203)


if __name__ == "__main__":
    main()
