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

import numpy as np
import h5py


class Magnify(object):

    def __init__(self, inputfile, magnificationsfile, spectroscopy):

        self.filename_nexus = inputfile
        self.magnifications_ratios_file = magnificationsfile
        self.spectroscopy = spectroscopy

        self.input_nexusfile = h5py.File(self.filename_nexus, 'r')
        self.norm_grp = self.input_nexusfile["SpecNormalized"]

        self.outputfilehdf5 = inputfile.rsplit('.', 1)[0] + '_magnified.hdf5'
        self.specnorm = h5py.File(self.outputfilehdf5, 'w')
        self.magnified = self.specnorm.create_group("SpecNormalized")
        self.magnified.attrs['NX_class'] = "NXentry"

        self.nFrames = 0
        self.numrows = 0
        self.numcols = 0

        return

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
            energies = self.norm_grp["energy"].value
            self.magnified.create_dataset("energy", data=energies)
        except:
            print("\nEnergies could not be extracted.\n")

    def store_angles(self):
        """Retrieving Angles"""
        try:
            angles = self.norm_grp["rotation_angle"].value
            self.magnified.create_dataset("rotation_angle", data=angles)
        except:
            print("\nAngles could not be extracted.\n")

    def store_currents(self):
        """Retrieving important data from currents"""
        try:
            currents_dataset_name = 'Currents'
            currents = self.norm_grp[currents_dataset_name].value
            self.magnified["Currents"] = currents
        except:
            print("\nCurrents could NOT be extracted.\n")

    def store_currents_FF(self):
        """Retrieving important data from currents for FF images"""
        try:
            currentsFF_dataset_name = 'CurrentsFF'
            currentsFF = self.norm_grp[currentsFF_dataset_name].value
            self.magnified["CurrentsFF"] = currentsFF
        except:
            print("\nCurrents could NOT be extracted.\n")

    def store_exposure_times(self):
        """Retrieving important data from Exposure Times"""
        try:
            exposure_dataset_name = 'ExpTimes'
            exptimes = self.norm_grp[exposure_dataset_name].value
            self.magnified["ExpTimes"] = exptimes
        except:
            print("\nExposure Times could NOT be extracted.\n")

    def store_exposure_times_FF(self):
        """Retrieving important data from Exposure Times for FF images"""
        try:
            exposureFF_dataset_name = 'ExpTimesFF'
            exptimesFF = self.norm_grp[exposureFF_dataset_name].value
            self.magnified["ExpTimesFF"] = exptimesFF
        except:
            print("\nExposure Times could NOT be extracted.\n")

    def retrieve_image_dimensions(self):
        """Retrieving data from images shape"""
        infoshape = self.norm_grp['spectroscopy_normalized'].shape
        self.nFrames = infoshape[0]
        self.numrows = infoshape[1]
        self.numcols = infoshape[2]
        print("Dimensions: {0}".format(infoshape))

    def store_magnification_ratios(self):
        """Storing magnification ratios"""
        magnification_ratios = np.loadtxt(self.magnifications_ratios_file)
        # compare number of magnification ratios with images in the stack
        if len(magnification_ratios) == self.nFrames:
            self.magnified["magnification_ratios"] = magnification_ratios
        else:
            raise Exception("Number of magnification ratios is not equal "
                            "to number of images in the stack.")

    def store_metadata(self):
        self.store_currents()
        self.store_currents_FF()
        self.store_exposure_times()
        self.store_exposure_times_FF()
        self.store_pixel_size()
        self.store_energies()
        self.store_angles()
        self.retrieve_image_dimensions()
        self.store_magnification_ratios()

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
        print('Initialize store images\n')
        #self.retrieve_image_dimensions()
        #self.create_image_storage_dataset()


