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

import os
import shutil
import h5py
import numpy as np


def copy_hdf5(input, output):
    shutil.copy(input, output)

def extract_single_image_from_hdf5_function(f_h5_handler, data_set="data"):
    self.image = f_h5_handler[data_set].value
    try:
        self.dataset_attr = f_handler[data_set].attrs["dataset"]
    except:
        self.dataset_attr = "unknown_dataset"
    return self.image, self.dataset_attrs

def store_single_image_in_new_hdf5_function(hdf5_filename, image,
                                   description="default",
                                   data_set="data"):
    """Store a single image in an hdf5 file"""
    f = h5py.File(hdf5_filename, "w")
    f.create_dataset(data_set, data=image)
    f[data_set].attrs["dataset"] = data_set
    f[data_set].attrs["description"] = description
    f.flush()
    f.close()

def store_single_image_in_existing_hdf5_function(hdf5_filename, image,
                                        description="default",
                                        dataset="default"):
    """Store a single image in an hdf5 file"""
    f = h5py.File(hdf5_filename, "r+")
    precedent_step = int(f["data"].attrs["step"])
    workflow_step = precedent_step + 1
    if dataset == "default":
        data_set = "data_" + str(workflow_step)
    else:
        data_set = dataset
    f.create_dataset(data_set, data=image)
    f[data_set].attrs["step"] = workflow_step
    f[data_set].attrs["dataset"] = data_set
    f[data_set].attrs["description"] = description
    try:
        f["data"] = h5py.SoftLink(data_set)
    except:
        del f["data"]
        f["data"] = h5py.SoftLink(data_set)
    f.flush()
    f.close()
    return workflow_step





class Image(object):

    def __init__(self,
                 hdf5_image_filename="default.hdf5",
                 scalar_for_img=None,
                 extract_data_set="data",
                 mode="r+"):
        if scalar_for_img is None:
            self.hdf5_image_filename = hdf5_image_filename
            self.f_h5_handler = h5py.File(hdf5_image_filename, mode)
            self.image = 0
            self.dataset_attr = ""
            self.extract_single_image_from_hdf5(extract_data_set)
            self.workflow_step = 1
        else:
            self.image = scalar_for_img

    def extract_single_image_from_hdf5(self, data_set="data"):
        image = self.f_h5_handler[data_set].value
        data_type = type(image[0][0])
        self.image = np.array(image, dtype=data_type)
        try:
            self.dataset_attr = f_handler[data_set].attrs["dataset"]
        except:
            self.dataset_attr = "unknown_dataset"

    def store_single_image_in_new_hdf5(self, new_hdf5_filename, image,
                                       data_set="data", description="default"):
        """Store a single image in an hdf5 file"""
        f = h5py.File(new_hdf5_filename, "w")
        f.create_dataset(data_set, data=image)
        f[data_set].attrs["dataset"] = data_set
        f[data_set].attrs["description"] = description
        self._close_h5(f)

    def store_single_image_in_existing_hdf5(self,
                                            image,
                                            dataset="default",
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

    def _close_h5(self, f_h5_handler):
        f_h5_handler.flush()
        f_h5_handler.close()

    def __add__(self, other):
        """Adds two or more images between them.
        Also can add a constant to an image: the constant is added to all
        elements of the image: images + constant"""

        is_number = True
        shape1 = np.shape(self.image)
        try:
            float(other)
        except Exception:
            is_number = False

        if is_number:
            result_image = self.image + other
        else:
            shape2 = np.shape(other.image)
            if not shape1:
                self.image = self.image * np.ones(shape2,
                                                  dtype=type(self.image))
                shape1 = np.shape(self.image)
            if shape1 != shape2:
                raise "Images with different dimensions cannot be added"
            result_image = self.image + other.image
        return result_image

    def __sub__(self, other):
        shape1 = np.shape(self.image)
        shape2 = np.shape(other.image)
        if shape1 != shape2:
            raise "Images with different dimensions cannot be subtracted"
        return self.image - other.image

    def __mul__(self, other):
        shape1 = np.shape(self.image)
        shape2 = np.shape(other.image)
        if shape1 != shape2:
            raise "Images with different dimensions cannot be multiplied, " \
                  "element-wise"
        return np.multiply(self.image, other.image)

    def __div__(self, other):
        shape1 = np.shape(self.image)
        shape2 = np.shape(other.image)
        if shape1 != shape2:
            raise "Images with different dimensions cannot be divided, " \
                  "element-wise"
        self.image = np.array(self.image, dtype=float)
        return np.divide(self.image, other.image)


def try_add():

    fname1 = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
             "image_operate_xrm_test_add/" \
             "20161203_F33_tomo02_-8.0_-11351.9_proc.hdf5"
    fname2 = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
             "image_operate_xrm_test_add/" \
             "20161203_F33_tomo02_0.0_-11351.9_proc.hdf5"
    fname3 = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
             "image_operate_xrm_test_add/" \
             "20161203_F33_tomo02_10.0_-11351.9_proc.hdf5"

    ars = Image(hdf5_image_filename=fname1)
    brs = Image(hdf5_image_filename=fname2)
    crs = Image(hdf5_image_filename=fname3)

    print(type(ars))
    print(type(brs))
    print(type(crs))
    other_img = ars + brs + crs# + zrs
    ars.store_single_image_in_existing_hdf5(other_img,
                                            description="new image tres")

    """crs_img = ars + brs
    ars.store_single_image_in_existing_hdf5(crs_img,
                                            description="new image tres")
    drs_img = ars + 3
    ars.store_single_image_in_existing_hdf5(drs_img,
                                            description="new image tres")

    hhimg = Image(scalar_for_img=4)
    hrs_img = hhimg + ars
    ars.store_single_image_in_existing_hdf5(hrs_img,
                                            description="new image tres")"""







def add_cte_to_image(image, cte):
    image = np.array(image)
    result_image = image + float(cte)
    return result_image

def subtract_image_to_cte(cte, image):
    shape = np.shape(image)
    cte = float(cte)
    img_cte = cte*np.ones(shape)
    result_image = img_cte - image
    return result_image

def multiply_image_by_constant(image, cte):
    image = np.array(image)
    result_image = np.multiply(image, cte)
    return result_image

def divide_image_by_constant(image, cte):
    cte = float(cte)
    image = np.array(image)
    result_image = np.divide(image, cte)
    return result_image

def normalize_by_single_FF(image, exp_time, machine_current,
                           image_FF, exp_time_FF, machine_current_FF):
    """Normalize image by FlatField (FF), machine_current and exposure time.
    The FF image was, beforehand, been normalized by its corresponding
    machine_current and exposure time.
    """
    exptime_by_current = exp_time * machine_current
    norm_img_by_cte = divide_image_by_constant(image, exptime_by_current)

    exptime_by_current_FF = exp_time_FF * machine_current_FF
    norm_img_FF_by_cte = divide_image_by_constant(image_FF,
                                                  exptime_by_current_FF)
    normalized_image = divide_images(norm_img_by_cte, norm_img_FF_by_cte)
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
    img_1, _ = extract_single_image_from_hdf5(f_handler)
    img_FF_1, _ = extract_single_image_from_hdf5(f_FF_handler)
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

    try_add()

    """
    ars = np.array([[2, 3], [4, 5]])
    brs = np.array([[5, 1], [2, 1]])

    add_resulting_image = add_images(ars, brs)
    subtract_resulting_image = subtract_images(ars, brs)

    print(add_resulting_image)
    print(subtract_resulting_image)
    """

if __name__ == "__main__":
    main()
