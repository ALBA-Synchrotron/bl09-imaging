#!/usr/bin/python

"""
(C) Copyright 2017 Marc Rosanes
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

import cv2
import h5py
import numpy as np


class Magnify(object):

    def __init__(self, inputfile, magnificationsfile, spectroscopy):
        # Constructor method
        self.filename_nexus = inputfile
        self.magnifications_ratios_file = magnificationsfile
        self.spectroscopy = spectroscopy

        self.input_nexusfile = h5py.File(self.filename_nexus, 'r')
        self.norm_grp = self.input_nexusfile["SpecNormalized"]

        output_h5_filename = inputfile.rsplit('.', 1)[0] + '_magnified.hdf5'
        self.outputh5file = h5py.File(output_h5_filename, 'w')
        self.magnified = self.outputh5file.create_group("SpecNormalized")
        self.magnified.attrs['NX_class'] = "NXentry"

        self.img_stack = 'spectroscopy_normalized'
        self.magnification_ratios = 0
        self.nFrames = 0
        self.numrows = 0
        self.numcols = 0

    def store_pixel_size(self):
        """Retrieving Pixel Size"""
        try:
            x_pixel_size = self.norm_grp["x_pixel_size"].value
            y_pixel_size = self.norm_grp["y_pixel_size"].value
            self.magnified.create_dataset("x_pixel_size", data=x_pixel_size)
            self.magnified.create_dataset("y_pixel_size", data=y_pixel_size)
        except:
            print("\nPixel size could NOT be extracted.\n")

    def store_energies(self):
        """Retrieving Energies"""
        try:
            self.magnified["energy"] = self.norm_grp["energy"].value
        except:
            print("\nEnergies could not be extracted.\n")

    def store_angles(self):
        """Retrieving Angles"""
        try:
            self.magnified["rotation_angle"] = \
                self.norm_grp["rotation_angle"].value
        except:
            print("\nAngles could not be extracted.\n")

    def store_currents(self):
        """Retrieving important data from currents"""
        try:
            self.magnified["Currents"] = self.norm_grp["Currents"].value
        except:
            print("\nCurrents could NOT be extracted.\n")

    def store_currents_FF(self):
        """Retrieving important data from currents for FF images"""
        try:
            self.magnified["CurrentsFF"] = self.norm_grp["CurrentsFF"].value
        except:
            print("\nCurrents could NOT be extracted.\n")

    def store_exposure_times(self):
        """Retrieving important data from Exposure Times"""
        try:
            self.magnified["ExpTimes"] = self.norm_grp["ExpTimes"].value
        except:
            print("\nExposure Times could NOT be extracted.\n")

    def store_exposure_times_FF(self):
        """Retrieving important data from Exposure Times for FF images"""
        try:
            self.magnified["ExpTimesFF"] = self.norm_grp['ExpTimesFF'].value
        except:
            print("\nExposure Times could NOT be extracted.\n")

    def retrieve_image_dimensions(self):
        """Retrieving data from images shape"""
        infoshape = self.norm_grp[self.img_stack].shape
        self.nFrames = infoshape[0]
        self.numrows = infoshape[1]
        self.numcols = infoshape[2]
        print("Dimensions: {0}".format(infoshape))

    def store_magnification_ratios(self):
        """Storing magnification ratios"""
        self.magnification_ratios = np.loadtxt(self.magnifications_ratios_file)
        # compare number of magnification ratios with images in the stack
        if len(self.magnification_ratios) == self.nFrames:
            self.magnified["magnification_ratios"] = self.magnification_ratios
        else:
            raise Exception("Number of magnification ratios is not equal "
                            "to number of images in the stack.")

    def store_metadata(self):
        """Method to store the metadata"""
        self.store_currents()
        self.store_currents_FF()
        self.store_exposure_times()
        self.store_exposure_times_FF()
        self.store_pixel_size()
        self.store_energies()
        self.store_angles()
        self.retrieve_image_dimensions()
        self.store_magnification_ratios()

    def magnifyimage(self, img, ratio):
        """Scale (magnify) an image. It can be magnified if ratio is bigger
        than 1; demagnified if the ratio is smaller than 1; and the image
        is not scaled if the ratio is equal 1."""
        if ratio == 1:
            magnified_img = img
        else:
            scaled_img = cv2.resize(img,
                                    (int(ratio * self.numcols),
                                     int(ratio * self.numrows)),
                                    interpolation=cv2.INTER_LINEAR)
            rows_scaled_img, cols_scaled_img = scaled_img.shape
            from_row = abs(rows_scaled_img - self.numrows) / 2
            from_col = abs(cols_scaled_img - self.numcols) / 2

            if ratio > 1:
                to_row = from_row + self.numrows
                to_col = from_col + self.numcols

                magnified_img = scaled_img[from_row:to_row, from_col:to_col]

            elif ratio < 1:
                magnified_img = np.zeros((self.numrows, self.numcols),
                                         dtype=np.float32)

                to_row = from_row + rows_scaled_img
                to_col = from_col + cols_scaled_img
                magnified_img[from_row:to_row, from_col:to_col] = scaled_img

        return magnified_img

    def create_image_storage_dataset(self):
        self.magnified.create_dataset(
            self.img_stack,
            shape=(self.nFrames,
                   self.numrows,
                   self.numcols),
            chunks=(1,
                    self.numrows,
                    self.numcols),
            dtype='float32')

        self.magnified[self.img_stack].attrs[
            'Number of Frames'] = self.nFrames
        self.magnified[self.img_stack].attrs[
            'Pixel Rows'] = self.numrows
        self.magnified[self.img_stack].attrs[
            'Pixel Columns'] = self.numcols

    def magnify_spectrum(self):

        ###################
        # Store metadata ##
        ###################
        print('Storing metadata')
        self.store_metadata()
        print('Metadata stored\n')

        ################################################
        # Create empty dataset for image data storage ##
        ################################################
        print('Initialize magnify images\n')
        self.create_image_storage_dataset()

        for num_img in range(self.nFrames):
            magnification_ratio = self.magnification_ratios[num_img]
            img_from_stack = self.norm_grp[self.img_stack][num_img]
            img_magnified = self.magnifyimage(img_from_stack, magnification_ratio)
            self.magnified[self.img_stack][num_img] = img_magnified
            if num_img % 10 == 0:
                print("%d images have been magnified" % num_img)
        print('Images have been magnified\n')