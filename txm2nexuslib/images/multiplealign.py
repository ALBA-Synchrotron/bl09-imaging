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

import pprint
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
from txm2nexuslib.images.util import filter_file_index


def align_and_store_from_fn(couple_imgs_to_align_filenames,
                            dataset_reference="data",
                            dataset_for_aligning="data",
                            align_method='cv2.TM_CCOEFF_NORMED',
                            roi_size=0.5):
    image_ref_fn = couple_imgs_to_align_filenames[0]
    img_ref_obj = Image(h5_image_filename=image_ref_fn,
                        image_data_set=dataset_reference,
                        mode="r")

    image_to_align_fn = couple_imgs_to_align_filenames[1]
    img_to_align_obj = Image(h5_image_filename=image_to_align_fn,
                             image_data_set=dataset_for_aligning)

    _, mv_vector = img_to_align_obj.align_and_store(img_ref_obj,
                                                    align_method=align_method,
                                                    roi_size=roi_size)
    img_ref_obj.close_h5()
    img_to_align_obj.close_h5()


def align_images(file_index_fn, table_name="hdf5_proc",
                 dataset_for_aligning="data", dataset_reference="data",
                 roi_size=0.5, variable="zpz",
                 align_method='cv2.TM_CCOEFF_NORMED',
                 date=None, sample=None, energy=None, cores=-2,
                 query=None, jj=True):
    """Align images of one experiment by zpz.
    If date, sample and/or energy are indicated, only the corresponding
    images for the given date, sample and/or energy are cropped.
    The crop of the different images will be done in parallel: all cores
    but one used (Value=-2). Each file, contains a single image to be cropped.
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
    if query is not None:
        file_records = file_index_db.search(query)
    else:
        file_records = file_index_db.all()

    n_files = len(file_records)

    couples_to_align = []
    # The goal in this case is to align all the images for a same date,
    # sample, energy and angle, and a variable zpz.
    if variable == "zpz":
        dates_samples_energies_angles = []
        for record in file_records:
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
            if query is not None:
                query_cmd &= query
            h5_records = file_index_db.search(query_cmd)

            # pobj = pprint.PrettyPrinter(indent=4)
            # print("group for align")
            # for rec in h5_records:
            #    pobj.pprint(rec["filename"])
            _get_couples_to_align(couples_to_align, h5_records, root_path)

    # The goal in this case is to align all the images for a same date,
    # sample, jj_offset and angle, and a variable repetition.
    # This is used in the magnetism experiments where many repetitions are
    # necessary for each of the angles. 2 different JJ positions are
    # usually used in this kind of experiments, which allows to set the
    # two different circular polarizations (right and left)
    elif variable == "repetition" and jj:
        dates_samples_energies_jjs_angles = []
        for record in file_records:
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
            h5_records = file_index_db.search(query_cmd)

            # pobj = pprint.PrettyPrinter(indent=4)
            # print("group for align")
            # for rec in h5_records:
            #    pobj.pprint(rec["filename"])

            _get_couples_to_align(couples_to_align, h5_records, root_path)
    elif variable == "repetition" and not jj:
        dates_samples_energies = []
        for record in file_records:
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
            h5_records = file_index_db.search(query_cmd)

            # pobj = pprint.PrettyPrinter(indent=4)
            # print("group for align")
            # for rec in h5_records:
            #    pobj.pprint(rec["filename"])
            _get_couples_to_align(couples_to_align, h5_records, root_path)

    if couples_to_align:
        Parallel(n_jobs=cores, backend="multiprocessing")(
            delayed(align_and_store_from_fn)(
                couple_to_align,
                dataset_reference=dataset_reference,
                dataset_for_aligning=dataset_for_aligning,
                align_method=align_method,
                roi_size=roi_size) for couple_to_align in couples_to_align)

    print("--- Align %d files took %s seconds ---\n" %
          (n_files, (time.time() - start_time)))
    db.close()


def _get_couples_to_align(couples_to_align, h5_records, root_path):
    files = get_file_paths(h5_records, root_path)
    ref_file = files[0]
    files.pop(0)
    for file in files:
        couple_to_align = (ref_file, file)
        couples_to_align.append(couple_to_align)


def main():

    #file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
    #             "PARALLEL_IMAGING/image_operate_xrm_test_add/" \
    #             "tests8/xrm/index.json"

    file_index = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
                 "PARALLEL_IMAGING/PARALLEL_XRM2H5/tomo05/index.json"

    align_images(file_index)
    # sample="ols", energy=640, date=20161203)


if __name__ == "__main__":
    main()
