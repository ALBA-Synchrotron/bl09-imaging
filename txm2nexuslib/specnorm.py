#!/usr/bin/python

"""
(C) Copyright 2014-2017 Marc Rosanes
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


class SpecNormalize:

    def __init__(self, inputfile):
        #Note: FF is equivalent to brightfield 

        # Input File: HDF5 Raw Data
        filename_nexus = inputfile
        self.input_nexusfile = h5py.File(filename_nexus, 'r')

        # Output File: HDF5 Normalized Data
        outputfilehdf5 = inputfile.split('.')[0]+'_specnorm'+'.hdf5'
        self.spectnorm = h5py.File(outputfilehdf5, 'w')
        self.norm_grp = self.spectnorm.create_group("SpecNormalized")
        self.norm_grp.attrs['NX_class'] = "NXentry"

        # Spectrographic images
        self.nFrames = 0                
        self.numrows = 0
        self.numcols = 0
        self.dim_imagesSpec = (0, 0, 1)
        self.x_pixel_size = 0
        self.y_pixel_size = 0    
        self.currents = list()
        self.exptimes = list()
        self.energies = list()
        self.angles = list()
        
        # FF images
        self.nFramesFF = 0
        self.numrowsFF = 0
        self.numcolsFF = 0
        self.dim_imagesFF = (1, 1, 0)
        self.currents_FF = list()
        self.exptimes_FF = list()

        self.bool_currents_exist = 0
        self.bool_exptimes_exist = 0
        self.bool_currentsFF_exist = 0
        self.bool_exptimesFF_exist = 0
        
        return


    def normalizeSpec(self):

        nxtomo_grp = self.input_nexusfile["NXtomo"]
        instrument_grp = nxtomo_grp["instrument"]

        #####################
        # Retrieving Angles #
        #####################
        try:
            self.angles = nxtomo_grp["sample"]["rotation_angle"].value
            self.norm_grp.create_dataset("rotation_angle", data=self.angles)
        except:
            print("\nAngles could not be extracted.\n")

        #######################
        # Retrieving Energies #
        #######################
        try:
            self.energies = instrument_grp["source"]["energy"].value
            self.norm_grp.create_dataset("energy", data=self.energies)
        except:
            print("\nEnergies could not be extracted.\n")

        #########################
        # Retrieving Pixel Size #
        #########################
        try:
            self.x_pixel_size = instrument_grp["sample"]["x_pixel_size"].value
            self.y_pixel_size = instrument_grp["sample"]["y_pixel_size"].value
            self.norm_grp.create_dataset("x_pixel_size", data=self.x_pixel_size)
            self.norm_grp.create_dataset("y_pixel_size", data=self.y_pixel_size)
        except:
            print("\nPixel size could NOT be extracted.\n")

        ####################################
        # Dimensions from Data Image Stack #
        ####################################
        # Main Image Stack DataSet
        sample_image_data = instrument_grp["sample"]["data"]

        # Shape information of data image stack
        self.dim_imagesSpec = sample_image_data.shape
        self.nFrames = self.dim_imagesSpec[0]
        self.numrows = self.dim_imagesSpec[1]
        self.numcols = self.dim_imagesSpec[2]
        print("Dimensions spectroscopy: {0}".format(self.dim_imagesSpec))

        ##################################
        # Dimensions from FF Image Stack #
        ##################################
        # FF Image Stack Dataset
        FF_image_data = instrument_grp["bright_field"]["data"]

        # Shape information of FF image stack
        self.dim_imagesFF = FF_image_data.shape
        self.nFramesFF = self.dim_imagesFF[0]
        self.numrowsFF = self.dim_imagesFF[1]
        self.numcolsFF = self.dim_imagesFF[2]
        print("Dimensions FF: {0}".format(self.dim_imagesFF))

        #############################
        # Retrieving Exposure Times #
        #############################
        # Images Exposure Times
        try:
            self.exptimes = instrument_grp["sample"]["ExpTimes"].value
            self.norm_grp.create_dataset("ExpTimes", data=self.exptimes)
            self.bool_exptimes_exist = 1
        except:
            self.bool_exptimes_exist = 0
            print("\nExposure Times could not be extracted.\n")

        # FFs Exposure Times
        try:
            self.exptimes_FF = instrument_grp["bright_field"]["ExpTimes"].value
            self.norm_grp.create_dataset("ExpTimesFF", data=self.exptimes_FF)
            self.bool_exptimesFF_exist = 1
        except:
            self.bool_exptimesFF_exist = 0
            print("\nFF FF Exposure Times could not be extracted.\n")

        #######################
        # Retrieving Currents #
        #######################
        # Images Currents
        try:
            self.currents = instrument_grp["sample"]["current"].value
            self.norm_grp.create_dataset("Currents", data=self.currents)
            self.bool_currents_exist = 1
        except:
            self.bool_currents_exist = 0
            print("\nCurrents could not be extracted.\n")

        # FFs Currents
        try:
            self.currents_FF = instrument_grp["bright_field"]["current"].value
            self.norm_grp.create_dataset("CurrentsFF", data=self.currents_FF)
            self.bool_currentsFF_exist = 1
        except:
            self.bool_currentsFF_exist = 0
            print("\nFF Currents could not be extracted.\n")


        #########################################
        # Normalization                         #
        #########################################
        if (self.bool_currents_exist == 1 and self.bool_currentsFF_exist == 1
            and self.bool_exptimes_exist == 1  
            and self.bool_exptimesFF_exist == 1 
            and self.dim_imagesFF == self.dim_imagesSpec):

            print("\nInformation about currents and exposure times " 
                  "(for sampleImages and FF) is present in the hdf5 file.\n")


            self.norm_grp.create_dataset(
                "spectroscopy_normalized",
                shape=(self.nFrames,
                       self.numrows,
                       self.numcols),
                chunks=(1,
                        self.numrows,
                        self.numcols),
                dtype='float32')

            self.norm_grp['spectroscopy_normalized'].attrs[
                'Number of Frames'] = self.nFrames
            self.norm_grp['spectroscopy_normalized'].attrs[
                'Pixel Rows'] = self.numrows
            self.norm_grp['spectroscopy_normalized'].attrs[
                'Pixel Columns'] = self.numcols

            for numimg in range(self.nFrames):

                individual_spect_image = sample_image_data[numimg]
                individual_FF_image = FF_image_data[numimg]
                
                # Compute normalized images:
                numerator = np.array(individual_spect_image * (
                self.exptimes_FF[numimg] * self.currents_FF[numimg]))
                denominator = np.array(individual_FF_image * (
                                 self.exptimes[numimg] * self.currents[numimg]))
                normalizedspectrum_singleimage = np.array(numerator / (
                                               denominator), dtype = np.float32)
                self.norm_grp['spectroscopy_normalized'][numimg] = \
                    normalizedspectrum_singleimage

                if numimg % 10 == 0:
                    print('Image %d has been normalized' % numimg)

            print('\nSpectroscopy has been normalized taking into account ' +
                   'the ExposureTimes and the MachineCurrents\n')

        elif (self.bool_currents_exist == 0 and self.bool_currentsFF_exist == 0
            and self.bool_exptimes_exist == 1  
            and self.bool_exptimesFF_exist == 1 
            and self.dim_imagesFF == self.dim_imagesSpec):
            # Exposure times exist but currents does not exist.
            print("\nInformation about Exposure Times is present but "
                  "information of currents is not .\n")
            pass
            
        elif (self.bool_currents_exist == 1 and self.bool_currentsFF_exist == 1
            and self.bool_exptimes_exist == 0  
            and self.bool_exptimesFF_exist==0
            and self.dim_imagesFF == self.dim_imagesSpec):
            # Currents exist but Exposure times does not exist.
            print("\nInformation about Currents is present but "
                  "information of Exposure Times is not .\n")
            pass
            
        elif self.dim_imagesFF == self.dim_imagesSpec:
            # Nor Currents neither Experimental Times exist.
            print("\nNeither information about Currents is present nor "
                  "information of Exposure Times.\n")
            pass

        else:
            # Normalization is not possible because dimensions of FF are not
            # equal than dimensions of images.
            print("Normalization is not possible because dimensions of FF "
                  "are not equal than dimensions of spectroscopic images")

        self.input_nexusfile.close()
        self.spectnorm.close()
