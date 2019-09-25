#!/usr/bin/python

"""
(C) Copyright 2014 Marc Rosanes Siscart
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


class TomoNormalize:

    def __init__(self, inputfile, darkfield, avgtomnorm,
                 gaussianblur, avgff, diffraction):

        self.filename_nexus = inputfile
        self.input_nexusfile = h5py.File(self.filename_nexus, 'r')
        self.outputfilehdf5 = inputfile.rsplit('.', 1)[0] + '_norm.hdf5'
        self.tomonorm = h5py.File(self.outputfilehdf5, 'w')
        self.norm_grp = self.tomonorm.create_group("TomoNormalized")
        self.norm_grp.attrs['NX_class'] = "NXentry"
        self.darkfield = darkfield
        self.avgtomnorm = avgtomnorm

        # Angles and Energies
        self.energies = list()
        self.angles = list()
        
        # Ratios for the exposure times
        self.ratios_exptimes = list()
        self.x_pixel_size = 0
        self.y_pixel_size = 0        

        # Ratios for the currents.
        self.ratios_currents_tomo = list()
        self.ratios_currents_flatfield = list()

        # FF data & metadata (Note: FF = FlatField  = BrightField)
        self.exptimes_FF = 0
        self.avg_ff_exptime = 0
        self.currents_flatfield = 0
        self.data_flatfield = 0
        self.nFramesFF = 0
        self.numrowsFF = 0
        self.numcolsFF = 0

        # DF data & metadata (Note: DF = DarkField)
        self.exptimes_DF = 0
        self.avg_df_exptime = 0
        self.currents_darkfield = 0
        self.data_darkfield = 0
        self.nFramesDF = 0
        self.numrowsDF = 0
        self.numcolsDF = 0

        # Sample data & metadata
        self.exposuretimes_tomo = 0
        self.currents_tomo = 0
        self.data_tomo = 0
        self.nFramesSample = 0                
        self.numrows = 0
        self.numcols = 0

        # FF: FlatField (a.k.a. BrightField)
        self.averageff = 0
        # DF: DarkField
        self.averagedf = 0

        self.boolean_current_exists = 0
        self.avgff = avgff
        self.gaussianblur = gaussianblur
        self.diffraction = diffraction
        return

    def normalize_tomo(self):

        nxtomo_grp = self.input_nexusfile["NXtomo"]
        instrument_grp = nxtomo_grp["instrument"]
        if "dark_field" in instrument_grp:
            self.darkfield = 1

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

        #######################
        # Retrieving Currents #
        #######################
        try:
            self.currents_tomo = instrument_grp["sample"]["current"].value
            if self.currents_tomo[0] != 0:
                self.norm_grp.create_dataset("CurrentsTomo",
                                             data=self.currents_tomo)
                self.boolean_current_exists = 1
            else:
                self.boolean_current_exists = 0
                print("\nCurrents could not be extracted.\n")
        except:
            self.boolean_current_exists = 0
            print("\nCurrents could not be extracted.\n")

        ##########################
        # Retrieving FF Currents #
        ##########################
        FF_grp = instrument_grp["bright_field"]
        if self.boolean_current_exists:
            self.currents_flatfield = FF_grp["current"]
            self.norm_grp.create_dataset("CurrentsFF",
                                         data=self.currents_flatfield)

        #########################
        # Retrieving Pixel Size #
        #########################
        try:
            self.x_pixel_size = instrument_grp["sample"]["x_pixel_size"].value
            self.y_pixel_size = instrument_grp["sample"]["y_pixel_size"].value
            self.norm_grp.create_dataset(
                "x_pixel_size", data=self.x_pixel_size)
            self.norm_grp.create_dataset(
                "y_pixel_size", data=self.y_pixel_size)
        except:
            print("\nPixel size could NOT be extracted.\n")

        #############################
        # Retrieving Exposure Times #
        #############################
        self.exposuretimes_tomo = instrument_grp["sample"]["ExpTimes"].value
        self.norm_grp['ExpTimesTomo'] = self.exposuretimes_tomo
        num_exptimes_tomo = len(self.exposuretimes_tomo)

        # Main Data
        sample_image_data = instrument_grp["sample"]["data"]

        # Shape information of data image stack
        infoshape = sample_image_data.shape
        dimensions_singleimage_tomo = (infoshape[1], infoshape[2])
        self.nFramesSample = infoshape[0]
        self.numrows = infoshape[1]
        self.numcols = infoshape[2]

        # FF Data (FlatField/BrightField data)
        self.data_flatfield = FF_grp["data"].value
        self.exptimes_FF = FF_grp["ExpTimes"].value
        self.norm_grp['ExpTimesFF'] = self.exptimes_FF
        dimensions_singleimage_flatfield = self.data_flatfield[0].shape

        self.ratios_exptimes = [None] * num_exptimes_tomo

        # Average of the FF exposure times.
        for i in range(len(self.exptimes_FF)):
            self.avg_ff_exptime += self.exptimes_FF[i]
        self.avg_ff_exptime /= len(self.exptimes_FF)
        print('\nFlatField Exposure Time is {0}\n'.format(
            self.avg_ff_exptime))

        self.nFramesFF = self.data_flatfield.shape[0]
        self.numrowsFF = self.data_flatfield.shape[1]
        self.numcolsFF = self.data_flatfield.shape[2]

        # DF Data (DarkField data)
        if self.darkfield:
            DF_grp = instrument_grp["dark_field"]
            self.data_darkfield = DF_grp["data"].value
            self.exptimes_DF = DF_grp["ExpTimes"].value
            self.norm_grp['ExpTimesDF'] = self.exptimes_DF
            dimensions_singleimage_darkfield = self.data_darkfield[0].shape

            if dimensions_singleimage_tomo != \
                    dimensions_singleimage_darkfield:
                msg = ("\nThe dimensions of a tomography image does not"
                       + " correspond with the FF image dimensions."
                       + "\nThe normalization cannot be done.")
                raise msg

            # Average of the DF exposure times.
            for i in range(len(self.exptimes_DF)):
                self.avg_df_exptime += self.exptimes_DF[i]
            self.avg_df_exptime /= len(self.exptimes_DF)
            print('DarkField Exposure Time is {0}\n'.format(
                self.avg_df_exptime))

            self.nFramesDF = self.data_darkfield.shape[0]
            self.numrowsDF = self.data_darkfield.shape[1]
            self.numcolsDF = self.data_darkfield.shape[2]

        if dimensions_singleimage_tomo == \
                dimensions_singleimage_flatfield:

            self.norm_grp.create_dataset(
                "TomoNormalized",
                shape=(self.nFramesSample, self.numrows, self.numcols),
                chunks=(1, self.numrows, self.numcols),
                dtype='float32')

            self.norm_grp['TomoNormalized'].attrs['Number of Frames'] = \
                self.nFramesSample

            avgnormalizedtomo = np.zeros(
                (self.numrows, self.numcols), dtype=np.float)

            self.averageff = np.zeros((self.numrowsFF, self.numcolsFF),
                                      dtype=np.float)

            if self.boolean_current_exists and not self.darkfield:
                print('\nInformation about currents is present in hdf5 file')
                print('Tomography will be normalized taking into account '
                      'the ExposureTimes and the MachineCurrents\n')

                num_currents_tomo = len(self.currents_tomo)
                self.ratios_currents_tomo = [None]*num_currents_tomo

                num_currents_flatfield = len(self.currents_flatfield)
                self.ratios_currents_flatfield = [None]*num_currents_flatfield

                if self.avgff == 1:
                    self.norm_grp['Avg_FF_ExpTime'] = self.avg_ff_exptime

                # Getting the Ratios
                for i in range(num_exptimes_tomo):
                    self.ratios_exptimes[i] = self.exposuretimes_tomo[i] / \
                                              self.avg_ff_exptime

                for i in range(num_currents_tomo):
                    self.ratios_currents_tomo[i] = self.currents_tomo[i] / \
                                                   self.currents_tomo[0]

                for i in range(num_currents_flatfield):
                    self.ratios_currents_flatfield[i] = \
                        self.currents_flatfield[i] / self.currents_tomo[0]

                # FlatField (FF) images normalized with current,
                # and Average of FlatField Normalized with current
                self.norm_grp.create_dataset(
                    "FFNormalized",
                    shape=(self.nFramesFF, self.numrowsFF, self.numcolsFF),
                    chunks=(1, self.numrowsFF, self.numcolsFF),
                    dtype='float32')

                self.norm_grp["FFNormalized"].attrs[
                    'Number of Frames'] = self.nFramesFF

                for numimgFF in range(self.nFramesFF):
                    image_FF_normalized_with_current = np.array(
                        self.data_flatfield[numimgFF] /
                        self.ratios_currents_flatfield[numimgFF],
                        dtype=np.float)
                    self.norm_grp['FFNormalized'][numimgFF] = \
                        image_FF_normalized_with_current

                    if self.avgff == 1:
                        self.averageff += image_FF_normalized_with_current

                    print('FF Image %d has been normalized using the '
                          'machine_currents' % numimgFF)

                if self.avgff == 0:
                    self.averageff = np.array(
                        self.data_flatfield[0] /
                        self.ratios_currents_flatfield[0],
                        dtype=np.float)
                    print('\nFFs have been calculated '
                          'using the machine_currents\n')

                if self.diffraction == 1:
                    print('\nExternal moved averageFF '
                          'with diffraction pattern\n')
                    input_avgFF_diffract = h5py.File("saveFFonly.hdf5", 'r')
                    external_FF_grp = input_avgFF_diffract["FF"]
                    self.averageff = external_FF_grp["FF_moved"]
                    input_avgFF_diffract.close()

                if self.avgff == 1:
                    self.averageff = self.averageff/self.nFramesFF
                    if self.gaussianblur != 0:
                        from scipy import ndimage
                        self.averageff = ndimage.gaussian_filter(
                                       self.averageff, sigma=self.gaussianblur)
                    self.norm_grp['AverageFF'] = self.averageff
                    print('\nAverageFF has been calculated '
                          'using the machine_currents\n')

                for numimg in range(self.nFramesSample):
                    individual_image = sample_image_data[numimg]
                    normalizedtomo_singleimage = np.array(
                        ((individual_image /
                          self.ratios_currents_tomo[numimg]) /
                         (self.averageff*self.ratios_exptimes[numimg])),
                        dtype=np.float32)
                    self.norm_grp['TomoNormalized'][numimg] = \
                        normalizedtomo_singleimage
                    if self.avgtomnorm == 1:
                        avgnormalizedtomo += normalizedtomo_singleimage
                    if numimg%10 == 0:
                        print('Image %d has been normalized' % numimg)

            elif self.boolean_current_exists and self.darkfield:
                print('\nInformation about currents is present in hdf5 file')
                print('\nTomography will be normalized taking into account'
                      + '\n the ExposureTimes, the MachineCurrents,'
                      + '\n the FlatFields and the DarkFields\n')

                self.norm_grp['Avg_FF_ExpTime'] = self.avg_ff_exptime
                self.norm_grp['Avg_DF_ExpTime'] = self.avg_df_exptime

                # FlatField (FF) images normalized with its relative
                # currents and exposure times:
                self.norm_grp.create_dataset(
                    "FFNormalized",
                    shape=(self.nFramesFF, self.numrowsFF, self.numcolsFF),
                    chunks=(1, self.numrowsFF, self.numcolsFF),
                    dtype='float32')

                self.norm_grp["FFNormalized"].attrs[
                    'Number of Frames'] = self.nFramesFF

                for numimgFF in range(self.nFramesFF):
                    denominator = (self.currents_flatfield[numimgFF]
                                   * self.exptimes_FF[numimgFF])
                    image_FF_normalized = np.array(
                        self.data_flatfield[numimgFF] / denominator,
                        dtype=np.float)
                    self.norm_grp['FFNormalized'][
                        numimgFF] = image_FF_normalized
                    self.averageff += image_FF_normalized

                self.averageff = self.averageff/self.nFramesFF
                if self.gaussianblur != 0:
                    from scipy import ndimage
                    self.averageff = ndimage.gaussian_filter(
                        self.averageff, sigma=self.gaussianblur)
                self.norm_grp['NormalizedFF'] = self.averageff
                print('\nFF has been normalized using FF machine_currents'
                      + ' and FF exposure times\n')

                # DarkField (DF) images normalized with its relative
                # exposure times:
                self.norm_grp.create_dataset(
                    "DFNormalized",
                    shape=(self.nFramesDF, self.numrowsDF, self.numcolsDF),
                    chunks=(1, self.numrowsDF, self.numcolsDF),
                    dtype='float32')

                self.norm_grp["DFNormalized"].attrs[
                    'Number of Frames'] = self.nFramesDF

                for numimgDF in range(self.nFramesDF):
                    image_DF_normalized = np.array(
                        self.data_darkfield[numimgDF]
                        / self.exptimes_DF[numimgDF], dtype=np.float)
                    self.norm_grp['DFNormalized'][
                        numimgDF] = image_DF_normalized
                    self.averagedf += image_DF_normalized

                self.averagedf = self.averagedf/self.nFramesDF
                self.norm_grp['NormalizedDF'] = self.averagedf
                print('\nNormalizedDF has been normalized'
                      ' using DF exposure times\n')

                # Normalize images by applying:
                # norm[i] =  [  ( img[i]/(eti*mci) - DF/etdf ) /
                #               ( FF/(etff*mcff) - DF/etdf )     ]
                for numimg in range(self.nFramesSample):
                    individual_image = sample_image_data[numimg]
                    den_img = (self.exposuretimes_tomo[numimg]
                           * self.currents_tomo[numimg])
                    numerator = individual_image / den_img - self.averagedf
                    denominator = self.averageff - self.averagedf
                    normalizedtomo_singleimage = np.array(
                        (numerator / denominator), dtype=np.float32)
                    self.norm_grp['TomoNormalized'][numimg] = \
                        normalizedtomo_singleimage
                    avgnormalizedtomo += normalizedtomo_singleimage
                    if numimg%10 == 0:
                        print('Image %d has been normalized' % numimg)

            elif not self.boolean_current_exists:
                print('\nInformation about currents is NOT present '
                      'in hdf5 file')
                print('Tomography will be normalized taking into account '
                      'the ExposureTimes\n')

                if self.diffraction == 1:
                    print('\nExternal moved averageFF '
                          'with diffraction pattern\n')
                    input_avgFF_diffract = h5py.File("saveFFonly.hdf5", 'r')
                    external_FF_grp = input_avgFF_diffract["FF"]
                    self.averageff = external_FF_grp["FF_moved"]
                    input_avgFF_diffract.close()

                if self.avgff == 1:
                    for numimgFF in range (self.nFramesFF):
                        self.averageff += \
                            np.array(self.data_flatfield[numimgFF])
                    self.averageff = self.averageff/self.nFramesFF
                    if self.gaussianblur != 0:
                        from scipy import ndimage
                        self.averageff = ndimage.gaussian_filter(
                            self.averageff, sigma=self.gaussianblur)
                    print('\nAverageFF has been calculated\n')
                    self.norm_grp['AverageFF'] = self.averageff

                # Getting the Ratios of Exposure Times
                for i in range(num_exptimes_tomo):
                    self.ratios_exptimes[i] = self.exposuretimes_tomo[i] / \
                                              self.avg_ff_exptime

                for numimg in range(self.nFramesSample):
                    individual_image = sample_image_data[numimg]
                    normalizedtomo_singleimage = np.array(
                        (individual_image /
                         (self.averageff*self.ratios_exptimes[numimg])),
                        dtype=np.float32)
                    self.norm_grp['TomoNormalized'][numimg] = \
                        normalizedtomo_singleimage
                    if self.avgtomnorm == 1:
                        avgnormalizedtomo += normalizedtomo_singleimage
                    if numimg%10 == 0:
                        print('Image %d has been normalized' % numimg)

            if self.avgtomnorm == 1:
                avgnormalizedtomo /= self.nFramesSample
                self.norm_grp['AverageTomo'] = avgnormalizedtomo
                print('\nAverage of the normalized tomo images '
                      'has been calculated')

            print("\nNormalization has been finished")

        else:
            print('\nThe dimensions of a tomography image does not '
                  'correspond with the FF image dimensions')
            print('The normalization cannot be done\n')

        self.input_nexusfile.close()
        self.tomonorm.close()
