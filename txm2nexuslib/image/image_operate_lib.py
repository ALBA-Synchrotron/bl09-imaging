#!/usr/bin/python

"""
(C) Copyright 2017-2018 ALBA-CELLS
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


from os import path
import shutil
import cv2
import h5py
import numpy as np
from util import align


class Image(object):

    def __init__(self,
                 h5_image_filename="default.hdf5",
                 image_data_set="data",
                 mode="r+"):
        self.h5_image_filename = h5_image_filename
        self.f_h5_handler = h5py.File(h5_image_filename, mode)
        self.data_type = np.int32
        self.image = 0
        self.image_dataset = ""
        self.extract_single_image_from_h5(image_data_set)
        self.workflow_step = 1
        self.metadata = None

    def extract_single_image_from_h5(self, data_set="data"):
        image = self.f_h5_handler[data_set].value
        data_type = type(image[0][0])
        self.data_type = data_type
        self.image = np.array(image, dtype=self.data_type)
        try:
            self.image_dataset = self.f_h5_handler[data_set].attrs["dataset"]
        except:
            self.image_dataset = "unknown_dataset"

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
        return dataset

    def store_dataset_metadata(self, dataset="data",
                               metadata_dset_name="default",
                               metadata_value=None,
                               metadata_unit=None):
        """Store dataset metadata"""
        if metadata_value:
            dset_name = self.f_h5_handler[dataset].attrs["dataset"]
            metadata_grp = "metadata_" + dset_name
            if metadata_grp not in self.f_h5_handler:
                self.metadata = self.f_h5_handler.create_group(metadata_grp)
                self.metadata.create_dataset(metadata_dset_name,
                                             data=metadata_value)
                if metadata_unit:
                    self.metadata[metadata_dset_name].attrs[
                        "units"] = metadata_unit

    def normalize_by_constant(self, constant=None,
                              store_normalized_by_constant=False,
                              description="Image normalized by a constant"):
        """By default, the constant will be equal to the exposure time
        multiplied by the machine current; otherwise, if the constant is
        indicated, the image is normalized by the indicated value"""
        if not constant:
            exp_time = self.f_h5_handler["metadata"]["exposure_time"].value
            machine_current = self.f_h5_handler["metadata"][
                "machine_current"].value
            constant = exp_time * machine_current
        # If the constant is indicated, the image is divided by it
        img_norm_by_constant = self.image / constant
        if store_normalized_by_constant:
            self.store_image_in_h5(img_norm_by_constant,
                                   description=description)
        return img_norm_by_constant

    def clone_image_dataset(self):
        img = self.image
        try:
            description = self.f_h5_handler[
                self.image_dataset].attrs["description"]
        except:
            description = "No description available"
        self.store_image_in_h5(img,
                               description=description)

    def crop(self, roi={"top": 26, "bottom": 24, "left": 21, "right": 19}):
        """Crop an image. The roi indicates the pixels to be cut off.
        A default ROI is given to cut
        the image borders"""
        [rows, columns] = np.shape(self.image)
        rows_from = roi["top"]
        rows_to = rows - roi["bottom"]
        columns_from = roi["left"]
        columns_to = columns - roi["right"]
        image_cropped = self.image[rows_from:rows_to,
                                   columns_from:columns_to]
        description = ("Image " + self.image_dataset +
                       " cropped by " + str(roi))
        return image_cropped, description

    def align_from_file(self, reference_image_obj,
                        align_method='cv2.TM_CCOEFF_NORMED',
                        roi_size=0.5):
        """Align an image taking by reference another image. roi_size
        is entered as input parameter as tant per one of the original
        image size"""
        image_ref = reference_image_obj.image
        image_to_align = self.image
        aligned_image, mv_vector = align(image_ref, image_to_align,
                                         align_method=align_method,
                                         roi_size=roi_size)
        ref_fn = reference_image_obj.h5_image_filename
        ref_dataset_name = reference_image_obj.image_dataset
        description = ("Image " + self.image_dataset +
                       " has been aligned taking as reference image " +
                       ref_dataset_name + "@" + path.basename(ref_fn))
        return aligned_image, mv_vector, description

    def align_and_store(self, reference_image_obj,
                        align_method='cv2.TM_CCOEFF_NORMED', roi_size=0.5):
        aligned_image, mv_vector, description = self.align_from_file(
            reference_image_obj, align_method=align_method,
            roi_size=roi_size)
        new_dataset = self.store_image_in_h5(aligned_image,
                                             description=description)
        self.store_dataset_metadata(dataset=new_dataset,
                                    metadata_dset_name="move_vector",
                                    metadata_value=mv_vector)
        return aligned_image, mv_vector

    def close_h5(self):
        self.f_h5_handler.flush()
        self.f_h5_handler.close()


def copy_h5(input, output):
    """Copy file to a new file"""
    shutil.copy(input, output)


def store_single_image_in_new_h5(h5_filename, image, description="default",
                                 data_set="data"):
    """Store a single image in a new hdf5 file"""
    f = h5py.File(h5_filename, 'w')
    data_type = type(image[0][0])
    f.create_dataset(data_set, data=image, dtype=data_type)
    f.flush()
    f.close()


def store_in_multiple_files(result_image, image_filenames, description=""):
    for image_fn in image_filenames:
        image_obj = Image(h5_image_filename=image_fn)
        image_obj.store_image_in_h5(result_image,
                                    description=description)
        image_obj.close_h5()


def add(image_filenames, constant=0, store=False, output_h5_fn="default"):
    """
    Add images (addends),
    A constant can also be added to an image
    """
    description = "Add images and/or add a constant element-wise: \n"
    image_obj = Image(h5_image_filename=image_filenames[0])
    result_image = np.array(image_obj.image, dtype=np.int32)
    dataset = image_obj.image_dataset
    description += dataset + "@" + str(image_obj.h5_image_filename)
    image_obj.close_h5()

    for image_fn in image_filenames[1:]:
        image_obj = Image(h5_image_filename=image_fn)
        dataset = image_obj.image_dataset
        description += (" + \n" + dataset + "@" +
                        str(image_obj.h5_image_filename))
        result_image += image_obj.image
        image_obj.close_h5()

    if constant != 0:
        if constant % 1 == 0 and np.issubdtype(result_image[0][0], int):
            constant = int(constant)
        result_image = result_image + constant
        description += " + " + str(constant)

    if store:
        if output_h5_fn == "default":
            store_in_multiple_files(result_image, image_filenames,
                                    description=description)
        else:
            store_single_image_in_new_h5(
                output_h5_fn, result_image, description=description,
                data_set=dataset)
    return result_image


def subtract(image_filenames, constant=0, store=False,
             output_h5_fn="default"):
    """
    From a reference image (minuend),
    subtract one or more images (subtrahends)
    A constant can also be subtracted to the minuend
    """
    description = "Subtract images and/or subtract a constant " \
                  "to the minuend image (element-wise): \n"
    image_obj = Image(h5_image_filename=image_filenames[0])
    result_image = np.array(image_obj.image, dtype=np.int32)
    dataset = image_obj.image_dataset
    description += dataset + "@" + str(image_obj.h5_image_filename)
    image_obj.close_h5()

    for image_fn in image_filenames[1:]:
        image_obj = Image(h5_image_filename=image_fn)
        dataset = image_obj.image_dataset
        description += (" - \n" + dataset + "@" +
                        str(image_obj.h5_image_filename))
        result_image -= image_obj.image
        image_obj.close_h5()

    if constant != 0:
        if constant % 1 == 0 and np.issubdtype(result_image[0][0], int):
            constant = int(constant)
        result_image = result_image - constant
        description += " - " + str(constant)

    if store:
        if output_h5_fn == "default":
            image_obj = Image(h5_image_filename=image_filenames[0])
            image_obj.store_image_in_h5(result_image,
                                        description=description)
            image_obj.close_h5()
        else:
            store_single_image_in_new_h5(
                output_h5_fn, result_image, description=description,
                data_set=dataset)
    return result_image


def multiply(image_filenames, constant=1, store=False, output_h5_fn="default"):
    """
    Multiply images stored in hdf5 files (factors) between them.
    Multiply the resulting image by a constant.
    """
    description = ("Multiply images and/or multiply "
                   "element-wise by a constant: \n")
    image_obj = Image(h5_image_filename=image_filenames[0])
    result_image = np.array(image_obj.image, dtype=np.int32)
    dataset = image_obj.image_dataset
    description += dataset + "@" + str(image_obj.h5_image_filename)
    image_obj.close_h5()

    for image_fn in image_filenames[1:]:
        image_obj = Image(h5_image_filename=image_fn)
        dataset = image_obj.image_dataset
        description += (" * \n" + dataset + "@" +
                            str(image_obj.h5_image_filename))
        result_image = np.multiply(result_image, image_obj.image,
                                   casting='same_kind')
        image_obj.close_h5()

    if constant != 1:
        if constant % 1 == 0 and np.issubdtype(result_image[0][0], int):
            constant = int(constant)
        result_image = result_image * constant
        description += " * " + str(constant)

    if store:
        if output_h5_fn == "default":
            store_in_multiple_files(result_image, image_filenames,
                                    description=description)
        else:
            store_single_image_in_new_h5(
                output_h5_fn, result_image, description=description,
                data_set=dataset)
    return result_image


def divide(numerator, denominators, store=False, output_h5_fn="default"):
    """
    Divide a reference image (numerator) stored in a hdf5 file, by one or
    more denominators, which can be images stored in hdf5 files or constants.
    """
    description = "Divide a numerator (image or constant) by other images " \
                  "and/or constants: \n"
    store_filename = "none"
    try:
        result_image = float(numerator)
        description += str(result_image) + " / ("
    except:
        store_filename = numerator
        image_obj = Image(h5_image_filename=numerator)
        result_image = np.array(image_obj.image, dtype=np.int32)
        dataset = image_obj.image_dataset
        description += dataset + "@" + numerator + " / ("
        image_obj.close_h5()

    for i, denominator in enumerate(denominators):
        try:
            constant = float(denominator)
            result_image = result_image / constant
            if i == 0:
                description += str(constant)
            else:
                description += " * " + str(constant)
        except ValueError:
            image_obj = Image(h5_image_filename=denominator)
            dataset = image_obj.image_dataset
            if i == 0:
                description += dataset + "@" + denominator
                if store_filename == "none":
                    store_filename = denominator
            else:
                description += " * " + dataset + "@" + denominator
            result_image = result_image / image_obj.image
            image_obj.close_h5()
    description += " )"

    if store:
        if output_h5_fn == "default":
            image_obj = Image(h5_image_filename=store_filename)
            image_obj.store_image_in_h5(result_image,
                                        description=description)
            image_obj.close_h5()
        else:
            store_single_image_in_new_h5(
                output_h5_fn, result_image, description=description,
                data_set=dataset)
    return result_image


def average_images(image_filenames, dataset_for_average="data",
                   description="", store=False,
                   output_h5_fn="default", dataset_store="data"):
    """Average images"""
    image_obj = Image(h5_image_filename=image_filenames[0])
    average_image = np.zeros(np.shape(image_obj.image),
                             dtype=type(np.float32))
    num_imgs = len(image_filenames)
    for image_fn in image_filenames:
        image_obj = Image(h5_image_filename=image_fn,
                          image_data_set=dataset_for_average)
        average_image += image_obj.image
        image_obj.close_h5()
    # Average of images that have been beforehand normalized by a constant
    average_image /= num_imgs
    average_image = np.float32(average_image)
    # Store the average image in the first of the input h5 image file

    if store:
        if output_h5_fn == "default":
            image_obj = Image(h5_image_filename=image_filenames[0])
            description = "Average image: " + description
            image_obj.store_image_in_h5(average_image,
                                        description=description)
            image_obj.close_h5()
        else:
            store_single_image_in_new_h5(
                output_h5_fn, average_image, description=description,
                data_set=dataset_store)
    return average_image


def divide_by_constant_and_average_images(image_filenames, constant=None,
                                          store_normalized_by_constant=False,
                                          store=False):
    """Normalize each of the image in the list by a constant and average all
    the normalized images.
    If the constant is not indicated, as default, the constant is
    the exposure time multiplied by the machine current. If the images shall
    not be normalized, set the constant to 1."""
    image_obj = Image(h5_image_filename=image_filenames[0])
    image_norm_by_constant = image_obj.normalize_by_constant(constant)
    average_image = np.zeros(np.shape(image_obj.image),
                             dtype=type(image_norm_by_constant[0][0]))
    image_obj.close_h5()
    num_imgs = len(image_filenames)
    for image_fn in image_filenames:
        image_obj = Image(h5_image_filename=image_fn)
        image_norm_by_constant = image_obj.normalize_by_constant(
            constant, store_normalized_by_constant)
        average_image += image_norm_by_constant
        image_obj.close_h5()
    # Average of images that have been beforehand normalized by a constant
    average_image /= num_imgs
    # Store the average image in the first of the input h5 image file
    if store:
        image_obj = Image(h5_image_filename=image_filenames[0])
        description = ("Average image calculated after normalizing each "
                       "of the input images by a constant. If the constant "
                       "is not indicated, its default value is the "
                       "multiplication of the exposure time by the "
                       "machine current")
        image_obj.store_image_in_h5(average_image,
                                    description=description)
        image_obj.close_h5()
    return average_image


def get_normalized_ff(ff_img_filenames):
    if isinstance(ff_img_filenames, list):
        ff_img_obj = Image(h5_image_filename=ff_img_filenames[0])
    else:
        ff_img_obj = Image(h5_image_filename=ff_img_filenames)

    return ff_img_obj.image


def normalize_ff(ff_img_filenames):
    if isinstance(ff_img_filenames, list):
        ff_img_obj = Image(h5_image_filename=ff_img_filenames[0])
    else:
        ff_img_obj = Image(h5_image_filename=ff_img_filenames)

    if isinstance(ff_img_filenames, list) and len(ff_img_filenames) > 1:
        ff_img_obj.close_h5()
        # Average of FF images that are beforehand normalized by its
        # corresponding exposure times and machine currents
        ff_norm_image = divide_by_constant_and_average_images(
            ff_img_filenames, store_normalized_by_constant=True,
            store=True)
    else:
        # Normalize FF image by exposure_time and machine_current
        ff_norm_image = ff_img_obj.normalize_by_constant()

    return ff_norm_image


def normalize_image(image_filename, ff_img_filenames=[],
                    average_normalized_ff_img=None,
                    store_normalized=True,
                    output_h5_fn="default"):
    """
    Normalize BL09 hdf5 image: Normalize image by current, exposure time,
    and FlatField (FF) image (in case ff_img_filenames is a single file), or
     by average FF images (in case ff_img_filenames is a list of FF filenames).
     Each FF image is, beforehand, normalized by its corresponding
     current and exposure time.
    :param image_filename: the hdf5 image filename to be normalized
    :param ff_img_filenames: hdf5 FF image filename(s)
    :param average_normalized_ff_img: average normalized FF image. If defined,
    the FF filenames are not used.
    :param store_normalized: (Bool) True if normalized image has to be stored
    :return: normalized image
    """

    image_obj = Image(h5_image_filename=image_filename)

    if average_normalized_ff_img is not None:
        ff_norm_image = average_normalized_ff_img
    else:
        if isinstance(ff_img_filenames, list):
            ff_img_obj = Image(h5_image_filename=ff_img_filenames[0])
        else:
            ff_img_obj = Image(h5_image_filename=ff_img_filenames)

        if np.shape(image_obj.image) != np.shape(ff_img_obj.image):
            raise Exception("Image dimensions does not correspond with "
                   "ff image dimensions")
        ff_norm_image = normalize_ff(ff_img_filenames)

    # Normalize main image by exposure_time and machine_current
    img_norm_by_constant = image_obj.normalize_by_constant()

    # Normalized image by average FF, taking into account exposure times and
    # machine currents
    normalized_image = img_norm_by_constant / ff_norm_image

    # Store the resulting normalized image in the main image h5 file
    if store_normalized:
        dataset = image_obj.image_dataset
        description = dataset + "@" + path.basename(image_filename)
        if (average_normalized_ff_img is not None or
                (isinstance(ff_img_filenames, list)
                 and len(ff_img_filenames) > 1)):
            description += (" normalized by average FF, using exposure time "
                            "and machine current. To calculate the average "
                            "FF, each FF image has been, beforehand, "
                            "normalized by its exposure time and "
                            "machine current")
        else:
            description += (" has been normalized by single FF, "
                            "using its corresponding exposure times and "
                            "machine currents")

        if output_h5_fn == "default":
            image_obj.store_image_in_h5(normalized_image,
                                        description=description)
        else:
            store_single_image_in_new_h5(
                output_h5_fn, normalized_image, description=description,
                data_set=dataset)

    image_obj.close_h5()
    return normalized_image, ff_norm_image



def main():

    img_ref_name = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
                   "PARALLEL_IMAGING/image_operate_xrm_test_add/" \
                   "tests7/xrm/20171122_tomo05_520.0_0.0_-10435.5_proc.hdf5"
    reference_image_obj = Image(img_ref_name)

    img_to_align_name = "/home/mrosanes/TOT/BEAMLINES/MISTRAL/DATA/" \
                        "PARALLEL_IMAGING/image_operate_xrm_test_add/tests7" \
                        "/xrm/20171122_tomo05_520.0_10.0_-10434.0_proc.hdf5"
    image_to_align = Image(img_to_align_name)

    aligned_image, mv_vector = image_to_align.align_and_store(
        reference_image_obj)

    #reference_image_obj.clone_image_dataset()
    print(mv_vector)
    print(np.shape(aligned_image))

if __name__ == "__main__":
    main()

