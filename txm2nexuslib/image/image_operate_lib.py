#!/usr/bin/python

"""
(C) Copyright 2014-2017 ALBA-CELLS
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


import shutil
import h5py
import numpy as np


def copy_h5(input, output):
    shutil.copy(input, output)


def store_single_image_in_new_h5_function(h5_filename, image,
                                          description="default",
                                          data_set="data"):
    """Store a single image in an hdf5 file"""
    f = h5py.File(h5_filename, "w")
    f.create_dataset(data_set, data=image)
    f[data_set].attrs["dataset"] = data_set
    f[data_set].attrs["description"] = description
    f.flush()
    f.close()


class Image(object):

    def __init__(self,
                 h5_image_filename="default.hdf5",
                 scalar_for_img=None,
                 extract_data_set="data",
                 mode="r+"):
        if scalar_for_img is None:
            self.h5_image_filename = h5_image_filename
            self.f_h5_handler = h5py.File(h5_image_filename, mode)
            self.image = 0
            self.dataset_attr = ""
            self.extract_single_image_from_h5(extract_data_set)
            self.workflow_step = 1
        else:
            self.image = scalar_for_img

    def extract_single_image_from_h5(self, data_set="data"):
        image = self.f_h5_handler[data_set].value
        data_type = type(image[0][0])
        self.image = np.array(image, dtype=data_type)
        try:
            self.dataset_attr = self.f_h5_handler[data_set].attrs["dataset"]
        except:
            self.dataset_attr = "unknown_dataset"

    def extract_dataset_from_group(self,
                                   grp="metadata",
                                   dataset="exposure_time"):
        dataset_value = self.f_h5_handler[grp][dataset].value
        dataset_attrs = self.f_h5_handler[grp][dataset].attrs
        return dataset_value, dataset_attrs

    def store_image_in_h5(self, image, dataset="default",
                          description="default"):
        """Store a single image in an hdf5 file"""
        precedent_step = int(self.f_h5_handler["data"].attrs["step"])
        self.workflow_step = precedent_step + 1
        if dataset == "default":
            dataset = "data_" + str(self.workflow_step)
        self.f_h5_handler.create_dataset(dataset, data=image)
        self.f_h5_handler[dataset].attrs["step"] = self.workflow_step
        self.f_h5_handler[dataset].attrs["dataset"] = dataset
        self.f_h5_handler[dataset].attrs["description"] = description
        try:
            self.f_h5_handler["data"] = h5py.SoftLink(dataset)
        except:
            del self.f_h5_handler["data"]
            self.f_h5_handler["data"] = h5py.SoftLink(dataset)

    def close_h5(self):
        self.f_h5_handler.flush()
        self.f_h5_handler.close()


def normalize_by_single_ff(image_filename, image_ff_filename):
    """Normalize image by FlatField (FF), machine_current and exposure time.
    The FF image was, beforehand, been normalized by its corresponding
    machine_current and exposure time.
    """

    # Extract main image, exposure_time and machine_current of it, and
    # normalize this main image by its exposure_time and its machine_current
    image_obj = Image(h5_image_filename=image_filename)
    image = image_obj.image
    exp_time = image_obj.f_h5_handler["metadata"]["exposure_time"].value
    machine_current = image_obj.f_h5_handler["metadata"][
        "machine_current"].value
    norm_img_by_cte = image / (exp_time * machine_current)

    # Extract FF image, exposure_time and machine_current of it, and
    # normalize this FF image by its exposure_time and its machine_current
    image_FF_obj = Image(h5_image_filename=image_ff_filename)
    image_FF = image_FF_obj.image
    exp_time_FF = image_FF_obj.f_h5_handler["metadata"]["exposure_time"].value
    machine_current_FF = image_FF_obj.f_h5_handler["metadata"][
        "machine_current"].value
    norm_img_FF_by_cte = image_FF / (exp_time_FF * machine_current_FF)

    # Compute normalized image by dividing the precedent images
    normalized_image = norm_img_by_cte / norm_img_FF_by_cte

    # Store the resulting image in the main image h5 file
    image_obj.store_image_in_h5(normalized_image,
                                description="normalized image")

    image_obj.close_h5()
    image_FF_obj.close_h5()

    return normalized_image


def normalize_bl09_image_by_avg_FF(image_file, FF_img_files):
    """
    Normalize BL09 hdf5 image: Normalize image by current, exposure time,
    and FlatField (FF) average image. Each FF image were, beforehand,
    been normalized by its corresponding current and exposure time.
    :param arg: First argument: the hdf5 image to be normalized.
                Subsequent arguments: the hdf5 FF image files.
    :return: normalized image
    """

    description = "Normalize image:\n"
    image_FF_file = FF_img_files[0]
    f_handler = h5py.File(image_file, "r")
    f_FF_handler = h5py.File(image_FF_file, "r")
    img_1, _ = extract_single_image_from_h5(f_handler)
    img_FF_1, _ = extract_single_image_from_h5(f_FF_handler)
    shape_img = np.shape(img_1)
    shape_FF_img = np.shape(img_FF_1)
    if shape_img != shape_FF_img:
        raise("Error: image shape is not equal to FF shape\n"
              "Normalization cannot be done")
    result_image_FF = np.zeros(shape_FF_img)
    f_handler.close()
    f_FF_handler.close()

    num_FFs = len(FF_img_files)
    for FF_img_hdf5_file in FF_img_files:
        FF_h5_handler = h5py.File(FF_img_hdf5_file, "r")
        img_FF, dataset = extract_single_image_from_hdf5(FF_h5_handler)
        exp_time_FF = FF_h5_handler["metadata"]["exposure_time"].value
        current_FF = FF_h5_handler["metadata"]["machine_current"].value
        exptime_by_current_FF = exp_time_FF * current_FF
        norm_FF_img = divide_image_by_constant(img_FF, exptime_by_current_FF)
        result_image_FF = add_images(result_image_FF, norm_FF_img)
        FF_h5_handler.close()
    average_norm_FF_img = divide_image_by_constant(result_image_FF, num_FFs)

    h5_handler = h5py.File(image_file, "r")
    img, dataset = extract_single_image_from_hdf5(h5_handler)
    description += dataset + "@" + str(image_file)
    description += "\nhas been normalized by average FF, machine currents" \
                   " and exposure times"
    exp_time = h5_handler["metadata"]["exposure_time"].value
    current = h5_handler["metadata"]["machine_current"].value
    exptime_by_current = exp_time * current
    norm_by_exttime_current = divide_image_by_constant(img, exptime_by_current)
    normalized_image = divide_images(norm_by_exttime_current,
                                     average_norm_FF_img)
    return normalized_image, description


def main():

    fn_image = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
             "20161203_F33_tomo02_-8.0_-11351.9_proc.hdf5"
    fn_image_FF = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
             "20161203_F33_tomo02_0.0_-11351.9_proc.hdf5"

    normalize_by_single_ff(fn_image, fn_image_FF)


if __name__ == "__main__":
    main()
