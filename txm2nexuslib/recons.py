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

class recons_normalize:

    def __init__(self, inputfile, avgtomnorm, gaussianblur, avgff, diffraction):

        self.avgtomnorm = avgtomnorm
        self.filename_nexus = inputfile
        self.input_nexusfile = h5py.File(self.filename_nexus, 'r')
        self.outputfilehdf5 = inputfile.rsplit('.', 1)[0] + '_norm.hdf5'
        self.tomonorm = h5py.File(self.outputfilehdf5, 'w')
        self.norm_grp = self.tomonorm.create_group("TomoNormalized")

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
           
        # Note: flatfield= FlatField= FF   
        self.exptimes_FF = 0
        self.avg_ff_exptime = 0
        self.currents_flatfield = 0
        self.data_flatfield = 0
        self.nFramesFF = 0
        self.numrowsFF = 0
        self.numcolsFF = 0

        self.exposuretimes_tomo = 0
        self.currents_tomo = 0
        self.data_tomo = 0
        self.nFramesSample = 0                
        self.numrows = 0
        self.numcols = 0
        
        self.averageff = 0
        self.normalizedtomo_singleimage = 0
        self.normalizedTomoStack = 0

        self.boolean_current_exists = 0
        self.avgff = avgff
        self.gaussianblur = gaussianblur
        self.diffraction = diffraction
        return

    def normalize_tomo(self):

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

        #######################
        # Retrieving Currents #
        #######################
        try:
            self.currents_tomo = instrument_grp["sample"]["current"].value
            self.norm_grp.create_dataset("CurrentsTomo",
                                         data=self.currents_tomo)
            self.boolean_current_exists = 1
        except:
            self.boolean_current_exists = 0
            print("\nCurrents could not be extracted.\n")

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

        #############################
        # Retrieving Exposure Times #
        #############################
        self.exposuretimes_tomo = instrument_grp["sample"]["ExpTimes"].value
        self.norm_grp['ExpTimesTomo'] = self.exposuretimes_tomo
        num_exptimes_tomo = len(self.exposuretimes_tomo)


        if self.boolean_current_exists == 1:

            print('\nInformation about currents is present in hdf5 file')

            infoshape = instrument_grp["sample"]["data"].shape
            dimensions_singleimage_tomo = (infoshape[1], infoshape[2])
            self.nFramesSample = infoshape[0]
            self.numrows = infoshape[1]
            self.numcols = infoshape[2]

            FF_grp = instrument_grp["bright_field"]
            self.exptimes_FF = FF_grp["ExpTimes"]
            self.currents_flatfield = FF_grp["current"]
            self.data_flatfield = FF_grp["data"].value

            # Average of the FF exposure times.
            for i in range(len(self.exptimes_FF)):
                self.avg_ff_exptime += self.exptimes_FF[i]
            self.avg_ff_exptime /= len(self.exptimes_FF)
            print('\nFlatField Exposure Time is {0}\n'.format(
                                                        self.avg_ff_exptime))

            self.ratios_exptimes = [None]*num_exptimes_tomo

            num_currents_tomo = len(self.currents_tomo)
            self.ratios_currents_tomo = [None]*num_currents_tomo

            num_currents_flatfield = len(self.currents_flatfield)
            self.ratios_currents_flatfield = [None]*num_currents_flatfield

            dimensions_singleimage_flatfield = self.data_flatfield[0].shape

            if self.avgff == 1:
                self.norm_grp['Avg_FF_ExpTime'] = self.avg_ff_exptime
            self.norm_grp.create_dataset("CurrentsFF",
                                         data=self.currents_flatfield)

            if dimensions_singleimage_tomo == \
                    dimensions_singleimage_flatfield:

                self.nFramesFF = self.data_flatfield.shape[0]
                self.numrowsFF = self.data_flatfield.shape[1]
                self.numcolsFF = self.data_flatfield.shape[2]

                # Calculating the Ratios #
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
                # and Average of FlatField Normalized with current #
                self.norm_grp.create_dataset(
                    "FFNormalizedWithCurrent",
                    shape=(self.nFramesFF,
                           self.numrowsFF,
                           self.numcolsFF),
                    dtype='float32')

                dset_FF_norm_current = self.norm_grp["FFNormalizedWithCurrent"]
                dset_FF_norm_current.attrs['Number of Frames'] = self.nFramesFF

                self.averageff=np.empty((self.numrowsFF, self.numcolsFF),
                                            dtype=np.float)
                for numimgFF in range(self.nFramesFF):
                    image_FF_normalized_with_current = np.array(
                        self.data_flatfield[numimgFF] /
                        self.ratios_currents_flatfield[numimgFF],
                        dtype=np.float)
                    self.norm_grp['FFNormalizedWithCurrent'][numimgFF] = \
                        image_FF_normalized_with_current

                    if self.avgff == 1:
                        self.averageff += image_FF_normalized_with_current

                    print('FF Image %d has been normalized using the '
                          'machine_currents' % numimgFF)

                if self.avgff == 0:
                    self.averageff = np.array(self.data_flatfield[0] /
                                              self.ratios_currents_flatfield[0],
                                              dtype=np.float)
                    print('\nFFs have been calculated '
                          'using the machine_currents\n')

                """
                ############
                if (self.diffraction == 1) :
                    print('\nExternal moved averageFF with diffraction pattern\n')
                    input_avgFF_diffract = nxs.open("saveFFonly.hdf5", 'r')
                    input_avgFF_diffract.opengroup('FF')
                    input_avgFF_diffract.opendata('FF_moved')
                    self.averageff = input_avgFF_diffract.getdata()
                    input_avgFF_diffract.closedata()
                    input_avgFF_diffract.closegroup()
                    input_avgFF_diffract.close()
                ############

                if self.avgff == 1:
                    self.averageff = self.averageff/self.nFramesFF
                    if(self.gaussianblur != 0):
                        from scipy import ndimage
                        self.averageff = ndimage.gaussian_filter(
                                       self.averageff, sigma=self.gaussianblur)
                    print('\nAverageFF has been calculated using the machine_currents\n')
                    self.tomonorm['AverageFF'] = nxs.NXfield(
                                    name='AverageFF', dtype='float32' , shape=[self.numrowsFF, self.numcolsFF])
                    self.tomonorm['AverageFF'] = self.averageff
                    self.tomonorm['AverageFF'].write()

                self.tomonorm['TomoNormalized'] = nxs.NXfield(
                                name='TomoNormalized', dtype='float32' , shape=[nxs.UNLIMITED, self.numrows, self.numcols])

                self.tomonorm['TomoNormalized'].attrs['Number of Frames'] = self.nFramesSample
                self.tomonorm['TomoNormalized'].write()

                self.input_nexusfile.opengroup('sample')
                self.input_nexusfile.opendata('data')

                self.avgnormalizedtomo = np.empty((self.numrows, self.numcols), dtype=np.float)

                for numimg in range (0, self.nFramesSample):

                    individual_image = self.input_nexusfile.getslab([numimg, 0, 0], [1, self.numrows, self.numcols])
                    self.normalizedtomo_singleimage = np.array((individual_image/self.ratios_currents_tomo[numimg]) / (self.averageff*self.ratios_exptimes[numimg]), dtype = np.float32)

                    slab_offset = [numimg, 0, 0]
                    self.tomonorm['TomoNormalized'].put(self.normalizedtomo_singleimage, slab_offset, refresh=False)
                    self.tomonorm['TomoNormalized'].write()

                    if (self.avgtomnorm == 1):
                        self.normalizedtomo_singleimage = np.reshape(self.normalizedtomo_singleimage, (self.numrows, self.numcols))
                        self.avgnormalizedtomo = self.avgnormalizedtomo + self.normalizedtomo_singleimage
                    else:
                        pass

                    print('Image %d has been normalized' % numimg)


                if (self.avgtomnorm == 1):

                    self.avgnormalizedtomo = self.avgnormalizedtomo / self.nFramesSample

                    self.tomonorm['AverageTomo'] = nxs.NXfield(
                                name='AverageTomo', dtype='float32' , shape=[self.numrows, self.numcols])
                    self.tomonorm['AverageTomo'] = self.avgnormalizedtomo
                    self.tomonorm['AverageTomo'].write()
                    print('\nAverage of the normalized tomo images has been calculated')
                else:
                    pass

                self.input_nexusfile.closedata()
                self.input_nexusfile.closegroup()
                self.input_nexusfile.close()

                print('\nTomography has been normalized taking into account the ExposureTimes and the MachineCurrents\n')

            else:
                print('\nThe dimensions of a tomography image does not correspond with the FF image dimensions')
                print('The normalization cannot be done\n')
                self.input_nexusfile.close()

        else:
            print('\nInformation about currents is NOT present in hdf5 file\n')

            self.input_nexusfile.opendata('data')
            infoshape = self.input_nexusfile.getinfo()
            dimensions_singleimage_tomo = (infoshape[0][1], infoshape[0][2])
            self.nFramesSample = infoshape[0][0]
            self.numrows = infoshape[0][1]
            self.numcols = infoshape[0][2]
            self.input_nexusfile.closedata()

            self.input_nexusfile.opengroup('bright_field')
            self.input_nexusfile.opendata('data')
            self.data_flatfield = self.input_nexusfile.getdata()
            self.input_nexusfile.closedata()
            self.input_nexusfile.opendata('ExpTimes')
            self.exptimes_FF = self.input_nexusfile.getdata()
            self.input_nexusfile.closedata()
            self.input_nexusfile.closegroup()

            for i in range(len(self.exptimes_FF)):
                self.avg_ff_exptime = self.avg_ff_exptime + self.exptimes_FF[i]
            self.avg_ff_exptime = self.avg_ff_exptime / len(self.exptimes_FF)

            print('FlatField Exposure Time is {0}.'.format(self.avg_ff_exptime))


            self.ratios_exptimes = [None]*num_exptimes_tomo

            dimensions_singleimage_flatfield = self.data_flatfield[0].shape

            if (dimensions_singleimage_tomo==dimensions_singleimage_flatfield):

                self.nFramesFF = self.data_flatfield.shape[0]
                self.numrowsFF = self.data_flatfield.shape[1]
                self.numcolsFF = self.data_flatfield.shape[2]

                self.averageff=np.array(self.data_flatfield[0], dtype=np.float)

                ############
                if (self.diffraction == 1) :
                    print('\nExternal moved averageFF with diffraction pattern\n')
                    input_avgFF_diffract = nxs.open("saveFFonly.hdf5", 'r')
                    input_avgFF_diffract.opengroup('FF')
                    input_avgFF_diffract.opendata('FF_moved')
                    self.averageff = input_avgFF_diffract.getdata()
                    input_avgFF_diffract.closedata()
                    input_avgFF_diffract.closegroup()
                    input_avgFF_diffract.close()
                ############

                if self.avgff == 1:
                    for numimgFF in range (self.nFramesFF-1):
                        self.averageff = self.averageff+np.array(self.data_flatfield[numimgFF+1])
                    self.averageff = self.averageff/self.nFramesFF
                    if(self.gaussianblur != 0):
                        from scipy import ndimage
                        self.averageff = ndimage.gaussian_filter(
                                       self.averageff, sigma=self.gaussianblur)
                    print('\nAverageFF has been calculated\n')
                    self.tomonorm['AverageFF'] = nxs.NXfield(
                                    name='AverageFF', dtype='float32' , shape=[self.numrowsFF, self.numcolsFF])
                    self.tomonorm['AverageFF'] = self.averageff
                    self.tomonorm['AverageFF'].write()

                for i in range (num_exptimes_tomo):
                    self.ratios_exptimes[i] = self.exposuretimes_tomo[i]/self.avg_ff_exptime

                self.tomonorm['TomoNormalized'] = nxs.NXfield(
                                name='TomoNormalized', dtype='float32' , shape=[nxs.UNLIMITED, self.numrows, self.numcols])

                self.tomonorm['TomoNormalized'].attrs['Number of Frames'] = self.nFramesSample
                self.tomonorm['TomoNormalized'].write()

                self.input_nexusfile.opengroup('sample')
                self.input_nexusfile.opendata('data')


                self.avgnormalizedtomo = np.empty((self.numrows, self.numcols), dtype=np.float)

                for numimg in range (0, self.nFramesSample):

                    individual_image = self.input_nexusfile.getslab([numimg, 0, 0], [1, self.numrows, self.numcols])
                    self.normalizedtomo_singleimage = np.array(individual_image / (self.averageff*self.ratios_exptimes[numimg]), dtype = np.float32)

                    slab_offset = [numimg, 0, 0]
                    self.tomonorm['TomoNormalized'].put(self.normalizedtomo_singleimage, slab_offset, refresh=False)
                    self.tomonorm['TomoNormalized'].write()

                    if (self.avgtomnorm == 1):
                        self.normalizedtomo_singleimage = np.reshape(self.normalizedtomo_singleimage, (self.numrows, self.numcols))
                        self.avgnormalizedtomo = self.avgnormalizedtomo + self.normalizedtomo_singleimage
                    else:
                        pass

                    print('Image %d has been normalized' % numimg)

                if (self.avgtomnorm == 1):

                    self.avgnormalizedtomo = self.avgnormalizedtomo / self.nFramesSample

                    self.tomonorm['AverageTomo'] = nxs.NXfield(
                                name='AverageTomo', dtype='float32' , shape=[self.numrows, self.numcols])
                    self.tomonorm['AverageTomo'] = self.avgnormalizedtomo
                    self.tomonorm['AverageTomo'].write()
                    print('\nAverage of the normalized tomo images has been calculated\n')
                else:
                    pass

                self.input_nexusfile.closedata()
                self.input_nexusfile.closegroup()
                self.input_nexusfile.close()

            else:
                print('The dimensions of a tomography image does not correspond with the FF image dimensions.')
                print('The normalization cannot be done.')
                self.input_nexusfile.close()

        """