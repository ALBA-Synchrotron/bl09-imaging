#!/usr/bin/python

"""
(C) Copyright 2014 Marc Rosanes
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

from OleFileIO_PL import *   
from util import sort_files_by_date
import numpy as np
import nxs
import sys
import struct
import datetime
import time
import argparse
import re

class txrmNXtomo:

    def __init__(self, files, files_order='s', zero_deg_in=None, 
                 zero_deg_final=None, title='X-ray tomography', 
                 sourcename='ALBA', sourcetype='Synchrotron X-ray Source', 
                 sourceprobe='x-ray', instrument='BL09 @ ALBA', 
                 sample='Unknown'):


        self.exitprogram=0
        if (len(files)<1):
            print('At least one input file must be specified.\n')
            self.exitprogram = 1
            return

        self.files=files
        #number of files.      
        self.num_input_files = len(files) 
        self.orderlist = list(files_order)
        #number of 's' 'b' and 'd'.
        self.num_input_files_verify = len(self.orderlist) 

        if(self.num_input_files != self.num_input_files_verify):
            print('Number of input files must be equal to number ' 
                  'of characters of files_order.\n')
            self.exitprogram=1
            return
                   
        if 's' not in files_order:
            print('Tomography data file (txrm) has to be specified, ' 
                  'inicate it as \'s\' in the argument option -o.\n')
            self.exitprogram = 1
            return

        index_tomography_file = files_order.index('s')
        self.filename_txrm = files[index_tomography_file]        
        self.filename_hdf5 = self.filename_txrm.split('.txrm')[0] + '.hdf5'

        self.filename_zerodeg_in = zero_deg_in
        self.filename_zerodeg_final = zero_deg_final

        self.numrows = 0
        self.numcols = 0
        self.nSampleFrames = 0      
        self.monitorcounts = 0
        self.count_num_sequence = 0
        
        self.num_axis = 0
        self.brightexists = 0
        self.darkexists = 0
        for i in range (0, self.num_input_files):
            #Create bright field structure    
            if(self.orderlist[i] == 'b'):
                self.brightexists=1
                self.numrows_bright = 0
                self.numcols_bright = 0
                self.datatype_bright = 'uint16'      

                            
            #Create dark field structure    
            if(self.orderlist[i] == 'd'):
                self.darkexists = 1
                self.numrows_dark = 0
                self.numcols_dark = 0
                self.datatype_dark = 'uint16' 


        """ The attribute self.metadata indicates if the metadata has been 
        # extracted or not. If metadata has not been extracted from the 'txrm' 
        file, we cannot extract the data from the images in the 'txrm'. """
        self.metadata=0
     
        self.title = title
        self.sourcename = sourcename
        self.sourcetype = sourcetype
        self.sourceprobe = sourceprobe
        self.instrumentname = instrument
        self.samplename = sample
        self.datatype = 'uint16' #two bytes
        
        self.nFramesSampleTotal = 0
        self.nFramesBrightTotal = 0
        self.nFramesDarkTotal = 0
        self.monitorsize = (self.nFramesSampleTotal + 
                            self.nFramesBrightTotal + self.nFramesDarkTotal) 

        self.num_sample_sequence = []
        self.num_bright_sequence = []
        self.num_dark_sequence = []    

        self.datatype_zerodeg = 'uint16'
        self.numrows_zerodeg = 0
        self.numcols_zerodeg = 0

        self.programname = 'txrm2nexus.py'
        self.nxentry = 0
        self.nxsample = 0
        self.nxmonitor = 0
        self.nxinstrument = 0
        self.nxdata = 0
        self.nxdetectorsample = 0

        self.pixelsize=1
        self.CCDdetector_pixelsize = 13
        self.CCDdetector_pixelsize_string = '13 um' #in micrometers
        self.magnification = 1

        self.sample_distance_enc = 0
        self.detector_distance_enc = 0
        self.zoneplate_distance_enc = 0
        self.sample_detector_distance = 0
        self.sample_zonplate_zeroenc = 0
        self.sample_detector_zeroenc = 0
        return



 
    def NXtomo_structure(self):    
        #create_basic_structure
    
        self.nxentry = nxs.NXentry(name= "NXtomo")
           
        self.nxentry['title']=self.filename_txrm
        self.nxentry['definition'] = 'NXtomo'
        
        self.nxsample = nxs.NXsample()
        self.nxentry.insert(self.nxsample)
        self.nxsample['name'] = self.samplename

        self.nxmonitor = nxs.NXmonitor(name= 'control')
        self.nxentry.insert(self.nxmonitor)

        self.nxdata = nxs.NXdata()
        self.nxentry.insert(self.nxdata)

        self.nxinstrument = nxs.NXinstrument(name= 'instrument')
        self.nxinstrument['name'] = self.instrumentname        
        self.nxinstrument['name'].attrs['CCD pixel size'] = \
                                            self.CCDdetector_pixelsize_string
        self.nxentry.insert(self.nxinstrument)

        self.nxsource = nxs.NXsource(name = 'source')
        self.nxinstrument.insert(self.nxsource)
        self.nxinstrument['source']['name'] = self.sourcename
        self.nxinstrument['source']['type'] = self.sourcetype
        self.nxinstrument['source']['probe'] = self.sourceprobe

        self.nxdetectorsample = nxs.NXdetector(name = 'sample')
        self.nxinstrument.insert(self.nxdetectorsample)  

        self.nxentry.save(self.filename_hdf5, 'w5')

        return 

 
    #### Function used to convert the metadata from .txrm to NeXus .hdf5
    def convert_metadata(self):

        verbose = False
        print("Trying to convert txrm metadata to NeXus HDF5.")
        
        #Opening the .txrm files as Ole structures
        ole = OleFileIO(self.filename_txrm)
        #txrm files have been opened
        
        self.nxentry['program_name'] = self.programname
        self.nxentry['program_name'].attrs['version']='1.0'
        self.nxentry['program_name'].attrs['configuration'] = \
                            (self.programname + ' ' + ' '.join(sys.argv[1:]))
        self.nxentry['program_name'].write()

        # Sample-ID
        if ole.exists('SampleInfo/SampleID'):   
            stream = ole.openstream('SampleInfo/SampleID')
            data = stream.read()
            struct_fmt ='<'+'50s' 
            samplename = struct.unpack(struct_fmt, data)
            if self.samplename != 'Unknown':
                self.samplename = samplename[0]    
            if verbose: 
                print "SampleInfo/SampleID: %s " % self.samplename 
            self.nxsample['name'] = nxs.NXfield(
                name='name', value=self.samplename)    
            self.nxsample['name'].write()    
        else:
            print("There is no information about SampleID")


        # Detector to Sample distance
        if ole.exists('PositionInfo/AxisNames'):   
            stream = ole.openstream('PositionInfo/AxisNames')
            data = stream.read()
            lendatabytes=len(data)
            formatstring='<'+str(lendatabytes)+'c'
            struct_fmt = formatstring
            axis_names_raw = struct.unpack(struct_fmt, data)
            axis_names_raw = ''.join(axis_names_raw)
            axis_names_raw = axis_names_raw.replace("\x00", " ")
            axis_names=re.split('\s+\s+', axis_names_raw)
            self.num_axis = len(axis_names)-1
            sample_enc_z_string=axis_names[2]
            detector_enc_z_string=axis_names[23]
            energy_name=axis_names[27] 
            current_name=axis_names[28]
            try:
                energyenc_name = axis_names[30]
            except:
                energyenc_name = " "

        ##########################################
        where_detzero = ("ConfigureBackup/ConfigCamera/" +
                        "Camera 1/ConfigZonePlates/DetZero")
        if (ole.exists(where_detzero)):   
            stream = ole.openstream(where_detzero)
            data = stream.read()
            if (len(data) != 0):
                struct_fmt = '<1f'
                sample_to_detector_zero_enc = struct.unpack(struct_fmt, data)
                self.sample_detector_zeroenc = sample_to_detector_zero_enc[0]

        if ole.exists('PositionInfo/MotorPositions'):   
            stream = ole.openstream('PositionInfo/MotorPositions')
            data = stream.read(112)
            struct_fmt = '<28f'
            axis = struct.unpack(struct_fmt, data)
            self.sample_distance_enc = axis[2] #this is already in um
            self.detector_distance_enc = axis[23]*1000 #from mm to um
        if (sample_enc_z_string == "Sample Z" and 
                                        detector_enc_z_string == "Detector Z"):
            self.sample_detector_distance = self.sample_detector_zeroenc + \
                          self.detector_distance_enc + self.sample_distance_enc
            self.nxinstrument['sample']['distance'] = nxs.NXfield(
                                        name='x_pixel_size', 
                                        value=self.sample_detector_distance, 
                                        attrs = {'units': 'um'}) 
            self.nxinstrument['sample']['distance'].write()  
        else:     
            print("Microscope motor names have changed. " 
                  "Maybe motors have been added or deleted.")
            print("Distances between detector and sample, and positions will "
                  "NOT be correctly calculated")
        ########################################## 
         
         

        # Pixel-size
        if ole.exists('ImageInfo/PixelSize'):   
            stream = ole.openstream('ImageInfo/PixelSize')
            data = stream.read()
            struct_fmt = '<1f'
            pixelsize = struct.unpack(struct_fmt, data)
            self.pixelsize = pixelsize[0]
            if verbose: 
                print "ImageInfo/PixelSize: %f " %  pixelsize  
            self.nxinstrument['sample']['x_pixel_size'] = nxs.NXfield(
                                                    name='x_pixel_size', 
                                                    value=self.pixelsize, 
                                                    attrs = {'units': 'um'})
            self.nxinstrument['sample']['x_pixel_size'].write()    
            self.nxinstrument['sample']['y_pixel_size'] = nxs.NXfield(
                                                    name='y_pixel_size', 
                                                    value=self.pixelsize, 
                                                    attrs = {'units': 'um'}) 
            self.nxinstrument['sample']['y_pixel_size'].write()    
        else:
            print("There is no information about PixelSize")

        #Magnification
        # X-Ray Magnification
        if ole.exists('ImageInfo/XrayMagnification'):   
            stream = ole.openstream('ImageInfo/XrayMagnification')
            data = stream.read(4)
            struct_fmt = '<1f'
            XrayMagnification = struct.unpack(struct_fmt, data)
            self.magnification = XrayMagnification[0]
            if (self.magnification != 0.0):
                pass
            elif (self.magnification == 0.0 and self.pixelsize != 0.0): 
                # magnification in micrometers
		        self.magnification = 13.0 / self.pixelsize
            else:
                print("Magnification could not be deduced.")	
                self.magnification = 0.0
            if verbose: 
                print "ImageInfo/XrayMagnification: %f " %  XrayMagnification  
            self.nxinstrument['sample']['magnification'] = nxs.NXfield(
                    name = 'magnification', value=self.magnification)
            self.nxinstrument['sample']['magnification'].write()
    
    	# Tomography data size 
        if (ole.exists('ImageInfo/NoOfImages') and 
            ole.exists('ImageInfo/ImageWidth') and 
            ole.exists('ImageInfo/ImageHeight')):                  
                    
            stream = ole.openstream('ImageInfo/NoOfImages')
            data = stream.read()
            nimages = struct.unpack('<I', data)
            if verbose: 
                print "ImageInfo/NoOfImages = %i" % nimages[0] 
            self.nSampleFrames = np.int(nimages[0])
        
            stream = ole.openstream('ImageInfo/ImageHeight')
            data = stream.read()
            ximage = struct.unpack('<I', data)    
            if verbose: 
                print "ImageInfo/ImageHeight = %i" % ximage[0]  
            self.numrows = np.int(ximage[0])
            
            stream = ole.openstream('ImageInfo/ImageWidth')
            data = stream.read()
            yimage = struct.unpack('<I', data)
            if verbose: 
                print "ImageInfo/ImageWidth = %i" % yimage[0]  
            self.numcols = np.int(yimage[0])

        else:
            print('There is no information about the tomography size ' 
                  '(ImageHeight, ImageWidth or Number of images)')


        # Accelerator current for each image (machine current)
        if (current_name == "machine_current"):
            if ole.exists('PositionInfo/MotorPositions'):   
                stream = ole.openstream('PositionInfo/MotorPositions')
                number_of_floats= self.num_axis*self.nSampleFrames
                struct_fmt = '<'+str(number_of_floats)+'f'
                number_of_bytes = number_of_floats * 4 #4 bytes every float
                data = stream.read(number_of_bytes)
                axis = struct.unpack(struct_fmt, data)

                currents = self.nSampleFrames*[0]
                for i in range(self.nSampleFrames):
                    currents[i] = axis[self.num_axis*i+28] #In mA  
                self.nxinstrument['sample']['current'] = nxs.NXfield(
                    name = 'current', value=currents, attrs = {'units': 'mA'})
                self.nxinstrument['sample']['current'].write()  
        else:     
            print("Microscope motor names have changed. "
                  "Index 28 does not correspond to machine_current.")


        ##############################
        # Energy for each image:
        # Energy for each image calculated from Energyenc ####
        if (energyenc_name.lower()=="energyenc"):
            if ole.exists('PositionInfo/MotorPositions'):
                stream = ole.openstream('PositionInfo/MotorPositions')
                number_of_floats= self.num_axis*self.nSampleFrames
                struct_fmt = '<'+str(number_of_floats)+'f'
                number_of_bytes = number_of_floats * 4 #4 bytes every float
                data = stream.read(number_of_bytes)
                axis = struct.unpack(struct_fmt, data)
                energenc = self.nSampleFrames*[0]
                for i in range(self.nSampleFrames):
                    energenc[i] = axis[self.num_axis*i+30] #In eV 
                if verbose: print "Energyenc: \n ",  energenc     
                self.nxinstrument['source']['energy'] = nxs.NXfield(
                   name = 'energy', value=energenc, attrs = {'units': 'eV'})
                self.nxinstrument['source']['energy'].write()
        # Energy for each image calculated from Energy motor ####
        elif (energy_name == "Energy"):
            if ole.exists('PositionInfo/MotorPositions'):   
                stream = ole.openstream('PositionInfo/MotorPositions')
                number_of_floats= self.num_axis*self.nSampleFrames
                struct_fmt = '<'+str(number_of_floats)+'f'
                number_of_bytes = number_of_floats * 4 #4 bytes every float
                data = stream.read(number_of_bytes)
                axis = struct.unpack(struct_fmt, data)
                energies = self.nSampleFrames*[0]
                for i in range(self.nSampleFrames):
                    energies[i] = axis[self.num_axis*i+27] #In eV 
                if verbose: print "ImageInfo/Energy: \n ",  energies     
                self.nxinstrument['source']['energy'] = nxs.NXfield(
                    name = 'energy', value=energies, attrs = {'units': 'eV'})
                self.nxinstrument['source']['energy'].write() 
        # Energy for each image calculated from ImageInfo ####
        elif ole.exists('ImageInfo/Energy'):
            stream = ole.openstream('ImageInfo/Energy')
    	    data = stream.read()
     	    struct_fmt = "<{0:10}f".format(self.nSampleFrames)
       	    try: #we found some txrm images (flatfields) with different encoding of data
                energies = struct.unpack(struct_fmt, data)
            except struct.error:
                print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack energies with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                energies = struct.unpack(struct_fmt, data)
            if verbose: print "ImageInfo/Energy: \n ",  energies  
            self.nxinstrument['source']['energy'] = nxs.NXfield(
                name='energy', value = energies, attrs = {'units': 'eV'}) 
            self.nxinstrument['source']['energy'].write()      
        else:
            print('There is no information about the energies at which '  
                   'have been taken the different images.')






        # Exposure Times            	
        if ole.exists('ImageInfo/ExpTimes'):
            stream = ole.openstream('ImageInfo/ExpTimes')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.nSampleFrames)
            try: #we found some txrm images (flatfields) with different encoding of data
                exptimes = struct.unpack(struct_fmt, data)
            except struct.error:
                print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack exposure times with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                exptimes = struct.unpack(struct_fmt, data)
            if verbose: print "ImageInfo/ExpTimes: \n ",  exptimes  
            self.nxinstrument['sample']['ExpTimes'] = nxs.NXfield(
                name='ExpTimes', value = exptimes, attrs = {'units': 's'}) 
            self.nxinstrument['sample']['ExpTimes'].write()
        else:
            print('There is no information about the exposure times with which '  
                   'have been taken the different tomography images')


        # DataType: 10 float; 5 uint16 (unsigned 16-bit (2-byte) integers)
        if ole.exists('ImageInfo/DataType'):                  
            stream = ole.openstream('ImageInfo/DataType')
            data = stream.read()
            struct_fmt = '<1I'
            datatype = struct.unpack(struct_fmt, data)
            datatype = int(datatype[0])
            if datatype == 5:
                self.datatype = 'uint16'
            else:
                self.datatype = 'float'
            if verbose: 
                print "ImageInfo/DataType: %s " %  self.datatype      
        else:
            print("There is no information about DataType")

        # Start and End Times 
        if ole.exists('ImageInfo/Date'):  
            stream = ole.openstream('ImageInfo/Date')       
            data = stream.read()
            dates = struct.unpack('<'+'17s23x'*self.nSampleFrames, data) 
            
            startdate = dates[0]
            [day, hour] = startdate.split(" ")
            [month, day, year] = day.split("/")
            [hour, minute, second] = hour.split(":")    
            
            year = '20'+year
            year = int(year)   
            month = int(month)
            day = int(day)
            hour = int(hour)
            minute = int(minute)
            second = int(second)

            starttime = datetime.datetime(year, month, day, 
                                          hour, minute, second)                 
            starttimeiso = starttime.isoformat()
            times = time.mktime(starttime.timetuple())

            if verbose: 
                print "ImageInfo/Date = %s" % starttimeiso 
            self.nxentry['start_time'] = str(starttimeiso)
            self.nxentry['start_time'].write()    

            enddate = dates[self.nSampleFrames-1]    
            [endday, endhour] = enddate.split(" ")
            [endmonth, endday, endyear] = endday.split("/")
            [endhour, endminute, endsecond] = endhour.split(":")

            endyear = '20'+endyear
            endyear = int(endyear)   
            endmonth = int(endmonth)
            endday = int(endday)
            endhour = int(endhour)
            endminute = int(endminute)
            endsecond = int(endsecond)

            endtime = datetime.datetime(endyear, endmonth, endday, 
                                        endhour, endminute, endsecond)                 
            endtimeiso = endtime.isoformat()
            endtimes = time.mktime(endtime.timetuple())   
            
            if verbose: 
                print "ImageInfo/Date = %s" % endtimeiso 
            self.nxentry['end_time'] = str(endtimeiso)
            self.nxentry['end_time'].write()

        else:
            print("There is no information about Date")

        # Sample rotation angles 
        if ole.exists('ImageInfo/Angles'):    
            stream = ole.openstream('ImageInfo/Angles')
            data = stream.read()
            struct_fmt = '<{0:10}f'.format(self.nSampleFrames)
            angles = struct.unpack(struct_fmt, data)
            if verbose: 
                print "ImageInfo/Angles: \n ",  angles
            self.nxsample['rotation_angle'] = nxs.NXfield(
                name='rotation_angle', value=angles, attrs={'units': 'degrees'})
            self.nxsample['rotation_angle'].write() 
            self.nxdata['rotation_angle'] = nxs.NXlink(
                target=self.nxsample['rotation_angle'], group=self.nxdata)
            self.nxdata['rotation_angle'].write()

        else:
            print('There is no information about the angles at' 
                   'which have been taken the different tomography images')

        # Sample translations in X, Y and Z 
        # X sample translation: nxsample['z_translation']
        if ole.exists('ImageInfo/XPosition'):

            stream = ole.openstream('ImageInfo/XPosition')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.nSampleFrames)
            #Found some txrm images with different encoding of data #
            try: 
                xpositions = struct.unpack(struct_fmt, data) 
            except struct.error:
                print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack XPositions with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                xpositions = struct.unpack(struct_fmt, data)
            if verbose: 
                print "ImageInfo/XPosition: \n ",  xpositions  

            self.nxsample['x_translation'] = nxs.NXfield(
                name='x_translation', value=xpositions, attrs={'units': 'um'})   
            self.nxsample['x_translation'].write()

        else:
            print("There is no information about xpositions")

        # Y sample translation: nxsample['z_translation']
        if ole.exists('ImageInfo/YPosition'):

            stream = ole.openstream('ImageInfo/YPosition')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.nSampleFrames)
            try:
                ypositions = struct.unpack(struct_fmt, data) 
            except struct.error:
                print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack YPositions with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                ypositions = struct.unpack(struct_fmt, data)
            if verbose: 
                print "ImageInfo/YPosition: \n ",  ypositions  
      
            self.nxsample['y_translation'] = nxs.NXfield(
                name='y_translation', value=ypositions, attrs={'units': 'um'})   
            self.nxsample['y_translation'].write()

        else:
            print("There is no information about xpositions")

        # Z sample translation: nxsample['z_translation']
        if ole.exists('ImageInfo/ZPosition'):
    
            stream = ole.openstream('ImageInfo/ZPosition')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.nSampleFrames)
            try:
                zpositions = struct.unpack(struct_fmt, data)
            except struct.error:
                print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack ZPositions with: "f"+"36xf"*(nSampleFrames-1)'%len(data)
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                zpositions = struct.unpack(struct_fmt, data)
            if verbose: 
                print "ImageInfo/ZPosition: \n ",  zpositions  
      
            self.nxsample['z_translation'] = nxs.NXfield(
                name='z_translation', value=zpositions, attrs={'units': 'um'})   
            self.nxsample['z_translation'].write()

        else:
            print("There is no information about xpositions")

        
        self.metadata=1

        ole.close()
        print("Meta-Data conversion from 'txrm' to NeXus HDF5 has been done.\n")  
        return


    def convert_zero_deg_images(self, ole_zerodeg):
        verbose=False

        # DataType: 10 float; 5 uint16 (unsigned 16-bit (2-byte) integers)
        if ole_zerodeg.exists('ImageInfo/DataType'):                  
            stream = ole_zerodeg.openstream('ImageInfo/DataType')
            data = stream.read()
            struct_fmt = '<1I'
            datatype_zerodeg = struct.unpack(struct_fmt, data)
            datatype_zerodeg = int(datatype_zerodeg[0])
            if datatype_zerodeg == 5:
                self.datatype_zerodeg='uint16'
            else:
                self.datatype_zerodeg= 'float'
            if verbose: 
                print "ImageInfo/DataType: %s " %  self.datatype_zerodeg     
        else:
            print("There is no information about DataType")


        # Zero degrees data size 
        if (ole_zerodeg.exists('ImageInfo/NoOfImages') and 
            ole_zerodeg.exists('ImageInfo/ImageWidth') and 
            ole_zerodeg.exists('ImageInfo/ImageHeight')):                  
                          
            stream = ole_zerodeg.openstream('ImageInfo/ImageHeight')
            data = stream.read()
            yimage = struct.unpack('<I', data)     
            self.numrows_zerodeg = np.int(yimage[0])
            if verbose: 
                print "ImageInfo/ImageHeight = %i" % yimage[0]
            stream = ole_zerodeg.openstream('ImageInfo/ImageWidth')
            data = stream.read()
            ximage = struct.unpack('<I', data)
            self.numcols_zerodeg = np.int(ximage[0])
            if verbose: 
                print "ImageInfo/ImageWidth = %i" % ximage[0]  
        else:
            print('There is no information about the 0 degrees image size '
                  '(ImageHeight, or about ImageWidth)')


        if ole_zerodeg.exists('ImageData1/Image1'):        
            img_string = "ImageData1/Image1"
            stream = ole_zerodeg.openstream(img_string) 
            data = stream.read()
            if self.datatype == 'uint16':
                struct_fmt = "<{0:10}H".format(self.numrows_zerodeg*self.numcols_zerodeg)
                imgdata = struct.unpack(struct_fmt, data)
            elif self.datatype == 'float':                   
                struct_fmt = "<{0:10}f".format(self.numrows_zerodeg*self.numcols_zerodeg)
                imgdata = struct.unpack(struct_fmt, data)
            else:                            
                print "Wrong data type"

            imgdata_zerodeg = np.flipud(np.reshape(imgdata, 
                                    (self.numrows, self.numcols), order='A'))
        else:
            imgdata_zerodeg = 0
        return imgdata_zerodeg


    #### Read single image. Function that will only be used inside 
    #### convert_tomography() for converting the full tomography thanks to multiple slabs.   
    def extract_single_image(self, ole, numimage): 

        #Read the images - They are stored in the txrm as ImageData1, ImageData2... 
        #Each folder contains 100 images 1-100, 101-200... 
        img_string = "ImageData%i/Image%i" % (np.ceil(numimage/100.0), numimage)
        stream = ole.openstream(img_string)
        data = stream.read()
    
        if self.datatype == 'uint16':
            struct_fmt = "<{0:10}H".format(self.numrows*self.numcols)
            imgdata = struct.unpack(struct_fmt, data)
        elif self.datatype == 'float':                   
            struct_fmt = "<{0:10}f".format(self.numrows*self.numcols)
            imgdata = struct.unpack(struct_fmt, data)
        else:                            
            print "Wrong data type"
            return
            
        singleimage = np.flipud(np.reshape(imgdata, (self.numrows, self.numcols), order='A'))
        singleimage = np.reshape(singleimage, (1, self.numrows, self.numcols), order='A')
        #singleimage = np.reshape(imgdata, (1, self.numrows, self.numcols), order='A')
        return singleimage


    #### Read single image. Function that will only be used inside 
    #### convert_tomography() for converting the full tomography thanks to multiple slabs.   
    def extract_single_image_bright(self, ole, numimage): 

        #Read the images - They are stored in the txrm as ImageData1, ImageData2... 
        #Each folder contains 100 images 1-100, 101-200... 
        img_string = "ImageData%i/Image%i" % (np.ceil(numimage/100.0), numimage)
        stream = ole.openstream(img_string)
        data = stream.read()
    
        if self.datatype_bright == 'uint16':
            struct_fmt = "<{0:10}H".format(self.numrows_bright*self.numcols_bright)
            imgdata = struct.unpack(struct_fmt, data)
        elif self.datatype_bright == 'float':                   
            struct_fmt = "<{0:10}f".format(self.numrows_bright*self.numcols_bright)
            imgdata = struct.unpack(struct_fmt, data)
        else:                            
            print "Wrong data type"
            return
            
        singleimage = np.flipud(np.reshape(imgdata, (self.numrows_bright, self.numcols_bright), order='A'))
        singleimage = np.reshape(singleimage, (1, self.numrows_bright, self.numcols_bright), order='A')
        #singleimage = np.reshape(imgdata, (1, self.numrows_bright, self.numcols_bright), order='A')
        return singleimage


    #### Read single image. Function that will only be used inside 
    #### convert_tomography() for converting the full tomography thanks to multiple slabs.   
    def extract_single_image_dark(self, ole, numimage): 

        #Read the images - They are stored in the txrm as ImageData1, ImageData2... 
        #Each folder contains 100 images 1-100, 101-200... 
        img_string = "ImageData%i/Image%i" % (np.ceil(numimage/100.0), numimage)
        stream = ole.openstream(img_string)
        data = stream.read()
    
        if self.datatype_dark == 'uint16':
            struct_fmt = "<{0:10}H".format(self.numrows_dark*self.numcols_dark)
            imgdata = struct.unpack(struct_fmt, data)
        elif self.datatype_dark == 'float':                   
            struct_fmt = "<{0:10}f".format(self.numrows_dark*self.numcols_dark)
            imgdata = struct.unpack(struct_fmt, data)
        else:                            
            print "Wrong data type"
            return
             
        singleimage = np.flipud(np.reshape(imgdata, (self.numrows_dark, self.numcols_dark), order='A'))
        singleimage = np.reshape(singleimage, (1, self.numrows_dark, self.numcols_dark), order='A')
        #singleimage = np.reshape(imgdata, (1, self.numrows_dark, self.numcols_dark), order='A')
        return singleimage




    #### Function used to convert all the tomography images (main data), from .txrm to NeXus .hdf5.
    def convert_tomography(self):    
        
        verbose=False

        if self.metadata == 1:
                
            if (self.filename_zerodeg_in != None):
                ole_zerodeg_in = OleFileIO(self.filename_zerodeg_in)        
                image_zerodeg_in = self.convert_zero_deg_images(ole_zerodeg_in)
                self.nxinstrument['sample']['0_degrees_initial_image'] = nxs.NXfield(
                    name='0_degrees_initial_image', value=image_zerodeg_in, dtype=self.datatype_zerodeg) 
                self.nxinstrument['sample']['0_degrees_initial_image'].attrs['Data Type']=self.datatype_zerodeg 
                self.nxinstrument['sample']['0_degrees_initial_image'].attrs['Image Height']=self.numrows_zerodeg
                self.nxinstrument['sample']['0_degrees_initial_image'].attrs['Image Width']=self.numcols_zerodeg
                self.nxinstrument['sample']['0_degrees_initial_image'].write()
                print('Zero degrees initial image converted')	

            if (self.filename_zerodeg_final != None):
                ole_zerodeg_final = OleFileIO(self.filename_zerodeg_final)
                image_zerodeg_final = self.convert_zero_deg_images(ole_zerodeg_final)
                self.nxinstrument['sample']['0_degrees_final_image'] = nxs.NXfield(
                    name='0_degrees_final_image', value=image_zerodeg_final , dtype=self.datatype_zerodeg)
                self.nxinstrument['sample']['0_degrees_final_image'].attrs['Data Type']=self.datatype_zerodeg 
                self.nxinstrument['sample']['0_degrees_final_image'].attrs['Image Height']=self.numrows_zerodeg
                self.nxinstrument['sample']['0_degrees_final_image'].attrs['Image Width']=self.numcols_zerodeg
                self.nxinstrument['sample']['0_degrees_final_image'].write()
                print('Zero degrees final image converted')        


            print("\nConverting tomography image data from txrm to NeXus HDF5.")
            #Opening the .txrm files as Ole structures
            ole = OleFileIO(self.filename_txrm)


            #Bright-Field
            if not self.brightexists:
                print('\nWarning: Bright-Field is not present, the generated HDF5 file will not be compliant with the NeXus standard. \n')      
         

            count_brightfield_file = 0
            count_darkfield_file = 0
            counter_bright_frames = 0
            counter_dark_frames = 0
            for i in range(0, len(self.orderlist)):
                print(self.orderlist)

                ole = OleFileIO(self.files[i])


                #Tomography Data Images
                if self.orderlist[i] == 's':
                    if (self.datatype == 'float'):
                        self.nxinstrument['sample']['data'] = nxs.NXfield(
                            name='data', dtype='float32' , shape=[nxs.UNLIMITED, self.numrows, self.numcols])
                    else:
                        self.nxinstrument['sample']['data'] = nxs.NXfield(
                            name='data', dtype=self.datatype , shape=[nxs.UNLIMITED, self.numrows, self.numcols])

                    self.nxinstrument['sample']['data'].attrs['Data Type']=self.datatype 
                    self.nxinstrument['sample']['data'].attrs['Number of Frames']=self.nSampleFrames
                    self.nxinstrument['sample']['data'].attrs['Image Height']=self.numrows
                    self.nxinstrument['sample']['data'].attrs['Image Width']=self.numcols
                    self.nxinstrument['sample']['data'].write()

                    
                    for numimage in range(0, self.nSampleFrames):
                        print('Image %i converted' % (numimage+1))
                        self.count_num_sequence = self.count_num_sequence+1
                        tomoimagesingle = self.extract_single_image(ole, numimage+1) 
                        
                        self.num_sample_sequence.append(self.count_num_sequence)

                        slab_offset = [numimage, 0, 0]
                        self.nxinstrument['sample']['data'].put(tomoimagesingle, slab_offset, refresh=False)
                        self.nxinstrument['sample']['data'].write()

                    self.nxdata['data'] = nxs.NXlink(target=self.nxinstrument['sample']['data'], group=self.nxdata)
                    self.nxdata['data'].write()
                    ole.close()
		    print('\n Image pixels are {0}rows * {1}columns \n'.format(self.numrows, self.numcols))	

                #Bright-Field
                elif self.orderlist[i] == 'b':                
                    count_brightfield_file = count_brightfield_file+1
                    
                    # DataType_bright: 10 float; 5 uint16 (unsigned 16-bit (2-byte) integers)
                    if ole.exists('ImageInfo/DataType'):                  
                        stream = ole.openstream('ImageInfo/DataType')
                        data = stream.read()
                        struct_fmt = '<1I'
                        datatype_bright = struct.unpack(struct_fmt, data)
                        datatype_bright = int(datatype_bright[0])
                        if datatype_bright == 5:
                            self.datatype_bright = 'uint16'
                        else:
                            self.datatype_bright = 'float'
                        if verbose: 
                            print "ImageInfo/DataType: %s " %  self.datatype_bright     
                    else:
                        print("There is no information about BrightField DataType")


                    # Tomography data size 
                    if (ole.exists('ImageInfo/NoOfImages') and 
                        ole.exists('ImageInfo/ImageWidth') and 
                        ole.exists('ImageInfo/ImageHeight')):                  
                                
                        stream = ole.openstream('ImageInfo/NoOfImages')
                        data = stream.read()
                        nimages = struct.unpack('<I', data)
                        if verbose: 
                            print "ImageInfo/NoOfImages = %i" % nimages[0] 
                        nBrightFrames = np.int(nimages[0])
                    
                        if count_brightfield_file == 1:
                            stream = ole.openstream('ImageInfo/ImageHeight')
                            data = stream.read()
                            ximage = struct.unpack('<I', data)    
                            if verbose: 
                                print "ImageInfo/ImageHeight = %i" % ximage[0]  
                            self.numrows_bright = np.int(ximage[0])
                            
                            stream = ole.openstream('ImageInfo/ImageWidth')
                            data = stream.read()
                            yimage = struct.unpack('<I', data)
                            if verbose: 
                                print "ImageInfo/ImageWidth = %i" % yimage[0]  
                            self.numcols_bright = np.int(yimage[0])

                    else:
                        print('There is no information about the tomography size (ImageHeight,'
                        'ImageWidth or Number of images)')

                    if count_brightfield_file == 1:
                        
                        self.nxbright = nxs.NXgroup(name= 'bright_field')
                        self.nxinstrument.insert(self.nxbright)
                        self.nxbright.write() 
                        self.nxinstrument['bright_field']['data'] = nxs.NXfield(
                            name = 'data', dtype = self.datatype_bright , shape = [nxs.UNLIMITED, self.numrows_bright, self.numcols_bright]) 

                        self.nxinstrument['bright_field']['data'].attrs['Data Type'] = self.datatype_bright 
                        self.nxinstrument['bright_field']['data'].attrs['Image Height'] = self.numrows_bright
                        self.nxinstrument['bright_field']['data'].attrs['Image Width'] = self.numcols_bright
                        self.nxinstrument['bright_field']['data'].write()


                    for numimage in range(0, nBrightFrames):
                        print ('Bright-Field image %i converted' % (numimage+1))
                        self.count_num_sequence = self.count_num_sequence+1
                        tomoimagebright = self.extract_single_image_bright(ole, numimage+1)
                    
                        self.num_bright_sequence.append(self.count_num_sequence)
                        slab_offset = [counter_bright_frames, 0, 0]
                        self.nxinstrument['bright_field']['data'].put(tomoimagebright, slab_offset, refresh=False)
                        self.nxinstrument['bright_field']['data'].write()
                        counter_bright_frames = counter_bright_frames+1
                        


                    ################################################
                    # machine_current name of FF images
                    if ole.exists('PositionInfo/AxisNames'):   
                        stream = ole.openstream('PositionInfo/AxisNames')
                        data = stream.read()
                        lendatabytes=len(data)
                        formatstring='<'+str(lendatabytes)+'c'
                        struct_fmt = formatstring
                        axis_names_raw = struct.unpack(struct_fmt, data)
                        axis_names_raw = ''.join(axis_names_raw)
                        axis_names_raw = axis_names_raw.replace("\x00", " ")
                        axis_names = re.split('\s+\s+', axis_names_raw)
                        current_name_FF = axis_names[28]   
	                
	                
	                # Accelerator current for each image of FF (machine current)
                    if (current_name_FF == "machine_current"):
                        if ole.exists('PositionInfo/MotorPositions'):   
                            stream = ole.openstream('PositionInfo/MotorPositions')
                            number_of_floats= self.num_axis*nBrightFrames
                            struct_fmt = '<'+str(number_of_floats)+'f'
                            number_of_bytes = number_of_floats * 4 #4 bytes every float
                            data = stream.read(number_of_bytes)
                            axis = struct.unpack(struct_fmt, data)

                            currents_FF = nBrightFrames*[0]
                            for i in range(nBrightFrames):
                                currents_FF[i] = axis[self.num_axis*i+28] #In mA  
                            self.nxinstrument['bright_field']['current'] = nxs.NXfield(
                                name = 'current', value=currents_FF, attrs = {'units': 'mA'})
                            self.nxinstrument['bright_field']['current'].write()
                        else:
                            print('PositionInfo/MotorPositions does not exist in txrm FF tree')  
                    else:     
                        print("Microscope motor names have changed. Index 28 does not correspond to machine_current.")
	                ###########################################            



                    # Exposure Times            	
                    if ole.exists('ImageInfo/ExpTimes'):
                        stream = ole.openstream('ImageInfo/ExpTimes')
                        data = stream.read()
                        struct_fmt = "<{0:10}f".format(nBrightFrames)
                        try: #we found some txrm images (flatfields) with different encoding of data
                            exptimes = struct.unpack(struct_fmt, data)
                        except struct.error:
                            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack exposure times with: "f"+"36xf"*(nBrightFrames-1)'%len(data) 
                            struct_fmt = '<'+"f"+"36xf"*(nBrightFrames-1)
                            exptimes = struct.unpack(struct_fmt, data)
                        if verbose: print "ImageInfo/ExpTimes: \n ",  exptimes  
                        self.nxinstrument['bright_field']['ExpTimes'] = nxs.NXfield(
                            name='ExpTimes', value = exptimes, attrs = {'units': 's'}) 
                        self.nxinstrument['bright_field']['ExpTimes'].write()
                    else:
                        print('There is no information about the exposure times with which '  
                               'have been taken the different tomography images')
   
                    ole.close()
                    print('\n BrightField pixels are {0}rows * {1}columns \n'.format(self.numrows_bright, self.numcols_bright))

                #Post-Dark-Field
                elif self.orderlist[i] == 'd':
                    count_darkfield_file = count_darkfield_file+1
						
                    # DataType_dark: 10 float; 5 uint16 (unsigned 16-bit (2-byte) integers)
                    if ole.exists('ImageInfo/DataType'):                  
                        stream = ole.openstream('ImageInfo/DataType')
                        data = stream.read()
                        struct_fmt = '<1I'
                        datatype_dark = struct.unpack(struct_fmt, data)
                        datatype_dark = int(datatype_dark[0])
                        if datatype_dark == 5:
                            self.datatype_dark = 'uint16'
                        else:
                            self.datatype_dark = 'float'
                        if verbose: 
                            print "ImageInfo/DataType: %s " %  self.datatype_dark     
                    else:
                        print("There is no information about DarkField DataType")


                    # Tomography data size 
                    if (ole.exists('ImageInfo/NoOfImages') and 
                        ole.exists('ImageInfo/ImageWidth') and 
                        ole.exists('ImageInfo/ImageHeight')):                  
                                
                        stream = ole.openstream('ImageInfo/NoOfImages')
                        data = stream.read()
                        nimages = struct.unpack('<I', data)
                        if verbose: 
                            print "ImageInfo/NoOfImages = %i" % nimages[0] 
                        nDarkFrames = np.int(nimages[0])
                    
                        if count_darkfield_file == 1:
                            stream = ole.openstream('ImageInfo/ImageHeight')
                            data = stream.read()
                            ximage = struct.unpack('<I', data)    
                            if verbose: 
                                print "ImageInfo/ImageHeight = %i" % ximage[0]  
                            self.numrows_dark = np.int(ximage[0])
                            
                            stream = ole.openstream('ImageInfo/ImageWidth')
                            data = stream.read()
                            yimage = struct.unpack('<I', data)
                            if verbose: 
                                print "ImageInfo/ImageWidth = %i" % yimage[0]  
                            self.numcols_dark = np.int(yimage[0])

                    else:
                        print('There is no information about the tomography size (ImageHeight,'
                        'ImageWidth or Number of images)')


                    if count_darkfield_file == 1:
                        self.nxdark = nxs.NXgroup(name= 'dark_field')
                        self.nxinstrument.insert(self.nxdark)
                        self.nxdark.write() 
                        self.nxinstrument['dark_field']['data'] = nxs.NXfield(
                            name = 'data', dtype = self.datatype_dark , shape = [nxs.UNLIMITED, self.numrows_dark, self.numcols_dark]) 

                        self.nxinstrument['dark_field']['data'].attrs['Data Type'] = self.datatype_dark 
                        self.nxinstrument['dark_field']['data'].attrs['Image Height'] = self.numrows_dark
                        self.nxinstrument['dark_field']['data'].attrs['Image Width'] = self.numcols_dark
                        self.nxinstrument['dark_field']['data'].write()


                    for numimage in range(0, nDarkFrames):
                        print ('Dark-Field image %i converted' % (numimage+1))
                        self.count_num_sequence = self.count_num_sequence+1
                        tomoimagedark = self.extract_single_image_dark(ole, numimage+1)

                        self.num_dark_sequence.append(self.count_num_sequence)
                        slab_offset = [counter_dark_frames, 0, 0]
                        self.nxinstrument['dark_field']['data'].put(tomoimagedark, slab_offset, refresh=False)
                        self.nxinstrument['dark_field']['data'].write()
                        counter_dark_frames = counter_dark_frames+1


                    ################################################
                    # machine_current name of DF images
                    if ole.exists('PositionInfo/AxisNames'):   
                        stream = ole.openstream('PositionInfo/AxisNames')
                        data = stream.read()
                        lendatabytes=len(data)
                        formatstring='<'+str(lendatabytes)+'c'
                        struct_fmt = formatstring
                        axis_names_raw = struct.unpack(struct_fmt, data)
                        axis_names_raw = ''.join(axis_names_raw)
                        axis_names_raw = axis_names_raw.replace("\x00", " ")
                        axis_names = re.split('\s+\s+', axis_names_raw)
                        current_name_DF = axis_names[28]   
	                
	                
	                # Accelerator current for each image of DF (machine current)
                    if (current_name_DF == "machine_current"):
                        if ole.exists('PositionInfo/MotorPositions'):   
                            stream = ole.openstream('PositionInfo/MotorPositions')
                            number_of_floats= self.num_axis*nDarkFrames
                            struct_fmt = '<'+str(number_of_floats)+'f'
                            number_of_bytes = number_of_floats * 4 #4 bytes every float
                            data = stream.read(number_of_bytes)
                            axis = struct.unpack(struct_fmt, data)

                            currents_DF = nDarkFrames*[0]
                            for i in range(nDarkFrames):
                                currents_DF[i] = axis[self.num_axis*i+28] #In mA  
                            self.nxinstrument['dark_field']['current'] = nxs.NXfield(
                                name = 'current', value=currents_DF, attrs = {'units': 'mA'})
                            self.nxinstrument['dark_field']['current'].write()
                        else:
                            print('PositionInfo/MotorPositions does not exist in txrm DarkField tree')  
                    else:     
                        print("Microscope motor names have changed. Index 28 does not correspond to machine_current.")
	                ###########################################  
	                
    
	                # Exposure Times            	
                    if ole.exists('ImageInfo/ExpTimes'):
                        stream = ole.openstream('ImageInfo/ExpTimes')
                        data = stream.read()
                        struct_fmt = "<{0:10}f".format(nDarkFrames)
                        try: #we found some txrm images (flatfields) with different encoding of data
                            exptimes = struct.unpack(struct_fmt, data)
                        except struct.error:
                            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack exposure times with: "f"+"36xf"*(nDarkFrames-1)'%len(data) 
                            struct_fmt = '<'+"f"+"36xf"*(nDarkFrames-1)
                            exptimes = struct.unpack(struct_fmt, data)
                        if verbose: print "ImageInfo/ExpTimes: \n ",  exptimes  
                        self.nxinstrument['dark_field']['ExpTimes'] = nxs.NXfield(
                            name='ExpTimes', value = exptimes, attrs = {'units': 's'}) 
                        self.nxinstrument['dark_fieldd']['ExpTimes'].write()
                    else:
                        print('There is no information about the exposure times with which '  
                               'have been taken the different tomography images')
                                                                  
                    ole.close()
		    print('\n DarkField pixels are {0}rows * {1}columns \n'.format(self.numrows_dark, self.numcols_dark))	

            self.nxinstrument['sample']['sequence_number'] = self.num_sample_sequence         
            self.nxinstrument['sample']['sequence_number'].write()

            if(self.brightexists):
                self.nxinstrument['bright_field']['sequence_number'] = self.num_bright_sequence         
                self.nxinstrument['bright_field']['sequence_number'].write()

            if(self.darkexists):
                self.nxinstrument['dark_field']['sequence_number'] = self.num_dark_sequence         
                self.nxinstrument['dark_field']['sequence_number'].write()

            self.nFramesSampleTotal = len(self.num_sample_sequence)
            self.nFramesBrightTotal = len(self.num_bright_sequence)
            self.nFramesDarkTotal = len(self.num_dark_sequence)

            # NXMonitor data: Not used in TXM microscope. 
            # Used to normalize in function fo the beam intensity (to verify). 
            # In the ALBA-BL09 case all the values will be set to 1.
            self.monitorsize = (self.nFramesSampleTotal + 
                                self.nFramesBrightTotal + self.nFramesDarkTotal)
            self.monitorcounts = np.ones((self.monitorsize), dtype= np.uint16)
            self.nxmonitor['data'] = nxs.NXfield(
                name='data', value=self.monitorcounts)
            self.nxmonitor['data'].write()

        else:
            print('Metadata had not been extracted; ' 
                  'thus, the tomography image data cannot be extracted.')
            print('Function convert_metadata() has to be called before '
                  'calling convert_tomography().')
    
        return
    

SAMPLEENC = 2
DETECTORENC_Z = 23
ENERGY = 27
CURRENT = 28
ENERGYENC = 30

class validate_getter(object):

    def __init__(self, required_fields):
        self.required_fields = required_fields

    def __call__(self, method):
        def wrapped_method(xradia_file):
            if not xradia_file.is_opened():
                raise RuntimeError("XradiaFile is not opened")
            for field in self.required_fields:
                if not xradia_file.exists(field):
                    raise RuntimeError("%s does not exist in XradiaFile" % field)
            return method(xradia_file)
        return wrapped_method


class XradiaFile(object):

    def __init__(self, file_name):
        self.file_name = file_name
        self.file = None
        self._axes_names = None
        self._no_of_images = None
        self._no_of_axes = None
        self._energyenc_name = None
        self._image_width = None
        self._image_height = None
        self._data_type = None
        self._det_zero = None
        self._pixel_size = None
        self._dates = None
        self._axes_positions = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def is_opened(self):
        return self.file is not None

    def open(self):
        self.file = OleFileIO(self.file_name)

    def close(self):
        self.file.close()
    
    def exists(self, field):
        return self.file.exists(field)

    @validate_getter(["SampleInfo/SampleID"])
    def get_sample_id(self):
        stream = self.file.openstream('SampleInfo/SampleID')
        data = stream.read()
        struct_fmt ='<'+'50s' 
        sample_id = struct.unpack(struct_fmt, data)
        if sample_id != 'Unknown':
            sample_id = sample_id[0]
        return sample_id

    @validate_getter(["ImageInfo/PixelSize"])
    def get_pixel_size(self):
        if self._pixel_size is None:
            stream = self.file.openstream('ImageInfo/PixelSize')
            data = stream.read()
            struct_fmt = '<1f'
            pixel_size = struct.unpack(struct_fmt, data)
            self._pixel_size = pixel_size[0]
        return self._pixel_size

    pixel_size = property(get_pixel_size)

    @validate_getter(["ImageInfo/XrayMagnification"])
    def get_xray_magnification(self):
        stream = self.file.openstream('ImageInfo/XrayMagnification')
        data = stream.read(4)
        struct_fmt = '<1f'
        xray_magnification = struct.unpack(struct_fmt, data)
        xray_magnification = xray_magnification[0]
        if (xray_magnification != 0.0):
            pass
        elif (xray_magnification == 0.0 and self.pixel_size != 0.0): 
            # magnification in micrometers
            xray_magnification = 13.0 / self.pixel_size
        else:
            print("Magnification could not be deduced.")
            xray_magnification = 0.0
        return xray_magnification

    @validate_getter(["PositionInfo/MotorPositions"])
    def get_axes_positions(self):
        if self._axes_positions is None:
            stream = self.file.openstream('PositionInfo/MotorPositions')
            data = stream.read(112)
            struct_fmt = '<28f'
            self._axes_positions = struct.unpack(struct_fmt, data)
        return self._axes_positions

    axes_positions = property(get_axes_positions)

    def get_sample_distance(self):
        return self.axes_positions[SAMPLEENC]

    sample_distance = property(get_sample_distance)

    def get_detector_distance(self):
        return self.axes_positions[DETECTORENC_Z] * 1000 #from mm to um

    detector_distance = property(get_detector_distance)

    def get_distance(self):
        if (self.sampleenc_name == "Sample Z" and
            self.detectorenc_name == "Detector Z"):
            distance = (self.det_zero + self.detector_distance +
                self.sample_distance)
        return distance

    @validate_getter(["ImageData1/Image1"])
    def get_image(self):
        stream = self.file.openstream('ImageData1/Image1')
        data = stream.read()

        if self.data_type == 'uint16':
            struct_fmt = "<{0:10}H".format(self.image_height * self.image_width)
            imgdata = struct.unpack(struct_fmt, data)
        elif self.data_type == 'float':
            struct_fmt = "<{0:10}f".format(self.image_height * self.image_width)
            imgdata = struct.unpack(struct_fmt, data)
        else:
            print "Wrong data type"
            return

        image = np.flipud(np.reshape(imgdata, (self.image_height,
                                               self.image_width), order='A'))
        image = np.reshape(image, (1, self.image_height, self.image_width),
                           order='A')
        return image

    @validate_getter(["PositionInfo/AxisNames"])
    def get_axes_names(self):
        if self._axes_names is None:
            stream = self.file.openstream('PositionInfo/AxisNames')
            data = stream.read()
            lendatabytes=len(data)
            formatstring='<'+str(lendatabytes)+'c'
            struct_fmt = formatstring
            axis_names_raw = struct.unpack(struct_fmt, data)
            axis_names_raw = ''.join(axis_names_raw)
            axis_names_raw = axis_names_raw.replace("\x00", " ")
            self._axes_names = re.split('\s+\s+', axis_names_raw)
            self._no_of_axes = len(self._axes_names) - 1
        return self._axes_names

    axes_names = property(get_axes_names)

    def get_energyenc_name(self):
        return self.axes_names[ENERGYENC]

    energyenc_name = property(get_energyenc_name)

    def get_energy_name(self):
        return self.axes_names[ENERGY]

    energy_name = property(get_energy_name)

    def get_detectorenc_name(self):
        return self.axes_names[DETECTORENC_Z]

    detectorenc_name = property(get_detectorenc_name)

    def get_sampleenc_name(self):
        return self.axes_names[SAMPLEENC]

    sampleenc_name = property(get_sampleenc_name)

    def get_current_name(self):
        return self.axes_names[CURRENT]

    current_name = property(get_current_name)

    def get_no_of_axes(self):
        if self._no_of_axes is None:
            self.get_axes_names()
        return self._no_of_axes

    no_of_axes = property(get_no_of_axes)

    @validate_getter(["ImageInfo/NoOfImages"])
    def get_no_of_images(self):
        if self._no_of_images is None:
            stream = self.file.openstream('ImageInfo/NoOfImages')
            data = stream.read()
            nimages = struct.unpack('<I', data)
            self._no_of_images = np.int(nimages[0])
        return self._no_of_images

    no_of_images = property(get_no_of_images)

    @validate_getter(["ImageInfo/ImageWidth"])
    def get_image_width(self):
        if self._image_width is None:
            stream = self.file.openstream('ImageInfo/ImageWidth')
            data = stream.read()
            yimage = struct.unpack('<I', data)
            self._image_width = np.int(yimage[0])
        return self._image_width

    image_width = property(get_image_width)

    @validate_getter(["ImageInfo/ImageHeight"])
    def get_image_height(self):
        if self._image_height is None:
            stream = self.file.openstream('ImageInfo/ImageHeight')
            data = stream.read()
            yimage = struct.unpack('<I', data)
            self._image_height = np.int(yimage[0])
        return self._image_height

    image_height = property(get_image_height)

    @validate_getter(["PositionInfo/MotorPositions"])
    def get_machine_currents(self):
        stream = self.file.openstream('PositionInfo/MotorPositions')
        num_axes = len(self.axes_names) - 1
        number_of_floats= num_axes * self.no_of_images
        struct_fmt = '<'+str(number_of_floats)+'f'
        number_of_bytes = number_of_floats * 4 #4 bytes every float
        data = stream.read(number_of_bytes)
        axis = struct.unpack(struct_fmt, data)

        currents = self.no_of_images * [0]
        for i in range(self.no_of_images):
            currents[i] = axis[self.no_of_axes*i+28] #In mA  
        return currents

    @validate_getter([])
    def get_energies(self):
        if (self.energyenc_name.lower() == "energyenc"):
            if self.file.exists('PositionInfo/MotorPositions'):
                stream = self.file.openstream('PositionInfo/MotorPositions')
                number_of_floats = self.no_of_axes * self.no_of_images
                struct_fmt = '<'+str(number_of_floats)+'f'
                number_of_bytes = number_of_floats * 4 #4 bytes every float
                data = stream.read(number_of_bytes)
                axis = struct.unpack(struct_fmt, data)
                energies = self.no_of_images * [0]
                for i in range(self.no_of_images):
                    energies[i] = axis[self.no_of_axes*i + 30] #In eV 
        # Energy for each image calculated from Energy motor ####
        elif (self.energy_name == "Energy"):
            if self.file.exists('PositionInfo/MotorPositions'):
                stream = self.file.openstream('PositionInfo/MotorPositions')
                number_of_floats = self.no_of_axes * self.no_of_images
                struct_fmt = '<'+str(number_of_floats)+'f'
                number_of_bytes = number_of_floats * 4 # 4 bytes every float
                data = stream.read(number_of_bytes)
                axis = struct.unpack(struct_fmt, data)
                energies = self.no_of_images * [0]
                for i in range(self.no_of_images):
                    energies[i] = axis[self.no_of_axes*i+27] #In eV 
        # Energy for each image calculated from ImageInfo ####
        elif self.file.exists('ImageInfo/Energy'):
            stream = self.file.openstream('ImageInfo/Energy')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.no_of_images)
            try: #we found some txrm images (flatfields) with different encoding of data
                energies = struct.unpack(struct_fmt, data)
            except struct.error:
                print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack energies with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
                struct_fmt = '<'+"f"+"36xf"*(self.no_of_images-1)
                energies = struct.unpack(struct_fmt, data)
        else:
            raise RuntimeError("There is no information about the energies at"
                "which have been taken the different images.")
        return energies

    @validate_getter(["ImageInfo/ExpTimes"])
    def get_exp_times(self):
        stream = self.file.openstream('ImageInfo/ExpTimes')
        data = stream.read()
        struct_fmt = "<{0:10}f".format(self.no_of_images)
        try: #we found some txrm images (flatfields) with different encoding of data
            exp_times = struct.unpack(struct_fmt, data)
        except struct.error:
            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack exposure times with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
            struct_fmt = '<'+"f"+"36xf"*(self.no_of_images-1)
            exp_times = struct.unpack(struct_fmt, data)
        return exp_times

    @validate_getter(['ImageInfo/Angles'])
    def get_angles(self):
        stream = self.file.openstream('ImageInfo/Angles')
        data = stream.read()
        struct_fmt = '<{0:10}f'.format(self.no_of_images)
        angles = struct.unpack(struct_fmt, data)
        return angles

    @validate_getter(['ImageInfo/XPosition'])
    def get_x_positions(self):
        stream = self.file.openstream('ImageInfo/XPosition')
        data = stream.read()
        struct_fmt = "<{0:10}f".format(self.no_of_images)
        #Found some txrm images with different encoding of data #
        try: 
            positions = struct.unpack(struct_fmt, data) 
        except struct.error:
            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack XPositions with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
            struct_fmt = '<'+"f"+"36xf"*(self.no_of_images-1)
            positions = struct.unpack(struct_fmt, data)
        return positions

    @validate_getter(['ImageInfo/YPosition'])
    def get_y_positions(self):
        stream = self.file.openstream('ImageInfo/YPosition')
        data = stream.read()
        struct_fmt = "<{0:10}f".format(self.no_of_images)
        #Found some txrm images with different encoding of data #
        try: 
            positions = struct.unpack(struct_fmt, data) 
        except struct.error:
            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack YPositions with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
            struct_fmt = '<'+"f"+"36xf"*(self.no_of_images-1)
            positions = struct.unpack(struct_fmt, data)
        return positions

    @validate_getter(['ImageInfo/ZPosition'])
    def get_z_positions(self):
        stream = self.file.openstream('ImageInfo/ZPosition')
        data = stream.read()
        struct_fmt = "<{0:10}f".format(self.no_of_images)
        #Found some txrm images with different encoding of data #
        try: 
            positions = struct.unpack(struct_fmt, data) 
        except struct.error:
            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack ZPositions with: "f"+"36xf"*(nSampleFrames-1)'%len(data) 
            struct_fmt = '<'+"f"+"36xf"*(self.no_of_images-1)
            positions = struct.unpack(struct_fmt, data)
        return positions

    @validate_getter(["ImageInfo/DataType"])
    def get_data_type(self):
        if self._data_type is None:
            stream = self.file.openstream('ImageInfo/DataType')
            data = stream.read()
            struct_fmt = '<1I'
            datatype = struct.unpack(struct_fmt, data)
            datatype = int(datatype[0])
            if datatype == 5:
                self._data_type = 'uint16'
            else:
                self._data_type = 'float'
        return self._data_type

    data_type = property(get_data_type)

    @validate_getter(["ImageInfo/Date"])
    def get_dates(self):
        if self._dates is None:
            stream = self.file.openstream('ImageInfo/Date')
            data = stream.read()
            self._dates = struct.unpack('<'+'17s23x'*self.no_of_images, data)
        return self._dates

    dates = property(get_dates)

    def get_start_date(self):

        startdate = self.dates[0]
        [day, hour] = startdate.split(" ")
        [month, day, year] = day.split("/")
        [hour, minute, second] = hour.split(":")

        year = '20'+year
        year = int(year)
        month = int(month)
        day = int(day)
        hour = int(hour)
        minute = int(minute)
        second = int(second)

        starttime = datetime.datetime(year, month, day, 
                                      hour, minute, second)
        starttimeiso = starttime.isoformat()
        return starttimeiso

    def get_end_date(self):
        enddate = self.dates[self.no_of_images-1]
        [endday, endhour] = enddate.split(" ")
        [endmonth, endday, endyear] = endday.split("/")
        [endhour, endminute, endsecond] = endhour.split(":")

        endyear = '20'+endyear
        endyear = int(endyear)
        endmonth = int(endmonth)
        endday = int(endday)
        endhour = int(endhour)
        endminute = int(endminute)
        endsecond = int(endsecond)

        endtime = datetime.datetime(endyear, endmonth, endday,
                                    endhour, endminute, endsecond)
        endtimeiso = endtime.isoformat()
        return endtimeiso

    @validate_getter(["ConfigureBackup/ConfigCamera/" +
                     "Camera 1/ConfigZonePlates/DetZero"])
    def get_det_zero(self):
        if self._det_zero is None:
            stream = self.file.openstream("ConfigureBackup/ConfigCamera/" +
                         "Camera 1/ConfigZonePlates/DetZero")
            data = stream.read()
            if (len(data) != 0):
                struct_fmt = '<1f'
                sample_to_detector_zero_enc = struct.unpack(struct_fmt, data)
                self._det_zero = sample_to_detector_zero_enc[0]
            else:
                self._det_zero = 0
        return self._det_zero

    det_zero = property(get_det_zero)

class xrmNXtomo(object):

    definition = 'NXtomo'
    CCDdetector_pixelsize = 13
    CCDdetector_pixelsize_unit = 'um' #in micrometers

    def __init__(self, reader, ffreader, file_order,
                 program_name, program_version, program_args,
                 hdf5_output_path=None, title='X-ray tomography',
                 zero_deg_in=None, zero_deg_final=None,sourcename='ALBA',
                 sourcetype='Synchrotron X-ray Source',
                 sourceprobe='x-ray', instrument='BL09 @ ALBA', 
                 sample='Unknown'):
        self.reader = reader
        self.ff_reader = ffreader
        if hdf5_output_path is None:
            path = reader.get_sample_path()
        else:
            path = hdf5_output_path
        sample_name = reader.get_sample_name()
        splitted_file = sample_name.split('_')
        sample_dir_name = '{0}_{1}'.format(splitted_file[0], splitted_file[1])
        path = os.path.join(path, sample_dir_name)
        if not os.path.exists(path):
            os.makedirs(path)
        self.hdf5_file_name = os.path.join(path, "%s.hdf5" % sample_name)
        self.program_name = program_name
        self.program_version = program_version
        self.program_args = program_args
        self.title = title
        self.sourcename = sourcename
        self.sourcetype = sourcetype
        self.sourceprobe = sourceprobe
        self.instrument = instrument
        self.sample = sample
        self.nxentry = None
        self.file_order = list(file_order)
        self.filename_zerodeg_in = zero_deg_in
        self.filename_zerodeg_final = zero_deg_final

    def convert_metadata(self):
        self.nxentry = nxs.NXentry(name=self.definition)

        self.nxentry['title'] = self.title
        self.nxentry['definition'] = self.definition

        self.nxsample = nxs.NXsample()
        self.nxentry.insert(self.nxsample)
        self.nxsample['name'] = self.sample

        self.nxmonitor = nxs.NXmonitor(name='control')
        self.nxentry.insert(self.nxmonitor)

        self.nxdata = nxs.NXdata()
        self.nxentry.insert(self.nxdata)

        self.nxinstrument = nxs.NXinstrument(name='instrument')
        self.nxinstrument['name'] = self.instrument
        pixel_size = "%d %s" % (self.CCDdetector_pixelsize,
                                self.CCDdetector_pixelsize_unit)
        self.nxinstrument['name'].attrs['CCD pixel size'] = pixel_size
        self.nxentry.insert(self.nxinstrument)

        self.nxsource = nxs.NXsource(name='source')
        self.nxinstrument.insert(self.nxsource)
        self.nxinstrument['source']['name'] = self.sourcename
        self.nxinstrument['source']['type'] = self.sourcetype
        self.nxinstrument['source']['probe'] = self.sourceprobe

        self.nxdetectorsample = nxs.NXdetector(name='sample')
        self.nxinstrument.insert(self.nxdetectorsample)

        self.nxentry['program_name'] = self.program_name
        self.nxentry['program_name'].attrs['version']= self.program_version
        self.nxentry['program_name'].attrs['configuration'] = \
                    ('%s %s' % (self.program_name, ' '.join(self.program_args)))

        # Sample-ID
        sample_name = self.reader.get_sample_name()
        self.nxsample['name'] = nxs.NXfield(name='name', value=sample_name)
        
        distance = self.reader.get_distance()
        self.nxinstrument['sample']['distance'] = nxs.NXfield(
                                    name='x_pixel_size',
                                    value=distance,
                                    attrs={'units': 'um'})
        pixel_size = self.reader.get_pixel_size()
        self.nxinstrument['sample']['x_pixel_size'] = nxs.NXfield(
                                                name='x_pixel_size',
                                                value=pixel_size,
                                                attrs = {'units': 'um'})
        self.nxinstrument['sample']['y_pixel_size'] = nxs.NXfield(
                                                name='y_pixel_size',
                                                value=pixel_size,
                                                attrs = {'units': 'um'})


        # X-Ray Magnification
        magnification = self.reader.get_xray_magnification()
        self.nxinstrument['sample']['magnification'] = nxs.NXfield(
                name = 'magnification', value=magnification)
        # Accelerator current for each image (machine current)
        currents = self.reader.get_machine_currents()
        self.nxinstrument['sample']['current'] = nxs.NXfield(
                    name='current', value=currents, attrs ={'units': 'mA'})

        # Energy for each image:
        energies = self.reader.get_energies()
        self.nxinstrument['source']['energy'] = nxs.NXfield(
                   name='energy', value=energies, attrs={'units': 'eV'})

        # Exposure Times                
        exptimes = self.reader.get_exp_times()
        self.nxinstrument['sample']['ExpTimes'] = nxs.NXfield(
            name='ExpTimes', value=exptimes, attrs={'units': 's'})

        # Start and End Times 
        starttimeiso = self.reader.get_start_time()
        self.nxentry['start_time'] = str(starttimeiso)
        endtimeiso = self.reader.get_end_time()
        self.nxentry['end_time'] = str(endtimeiso)

        # Sample rotation angles 
        angles = self.reader.get_angles()
        self.nxsample['rotation_angle'] = nxs.NXfield(
            name='rotation_angle', value=angles, attrs={'units': 'degrees'})

        # self.nxdata['rotation_angle'] = nxs.NXlink(
        #     target=self.nxsample['rotation_angle'], group=self.nxdata)
        # TODO: use links
        self.nxdata['rotation_angle'] = nxs.NXfield(
            name='rotation_angle', value=angles, attrs={'units': 'degrees'})
        # X sample translation: nxsample['z_translation']
        xpositions = self.reader.get_x_positions()
        self.nxsample['x_translation'] = nxs.NXfield(
                 name='x_translation', value=xpositions, attrs={'units': 'um'})
        # Y sample translation: nxsample['z_translation']
        ypositions = self.reader.get_y_positions()
        self.nxsample['y_translation'] = nxs.NXfield(
                 name='y_translation', value=ypositions, attrs={'units': 'um'})
        # Z sample translation: nxsample['z_translation']
        zpositions = self.reader.get_z_positions()
        self.nxsample['z_translation'] = nxs.NXfield(
                name='z_translation', value=zpositions, attrs={'units': 'um'})

        self.nxentry.save(self.hdf5_file_name, 'w5')


    def _convert_samples(self):
        height, width = self.reader.get_image_size()
        data_type = self.reader.get_data_type()
        n_sample_frames = self.reader.get_images_number()
        if data_type == 'float':
            self.nxinstrument['sample']['data'] = nxs.NXfield(
                name='data', dtype='float32', shape=[nxs.UNLIMITED, height,
                                                     width])
        else:
            self.nxinstrument['sample']['data'] = nxs.NXfield(
                    name='data', dtype=data_type,
                    shape=[nxs.UNLIMITED, height, width])

        self.nxinstrument['sample']['data'].attrs['Data Type'] = data_type
        self.nxinstrument['sample']['data'].attrs['Number of Frames'] = \
            n_sample_frames
        self.nxinstrument['sample']['data'].attrs['Image Height'] = height
        self.nxinstrument['sample']['data'].attrs['Image Width'] = width
        self.nxinstrument['sample']['data'].write()

        for id in range(n_sample_frames):
            tomoimagesingle = self.reader.get_image(id)
            slab_offset = [id, 0, 0]
            self.nxinstrument['sample']['data'].put(tomoimagesingle,
                                                    slab_offset, refresh=False)
            self.nxinstrument['sample']['data'].write()

        self.nxdata['data'] = nxs.NXlink(
                target=self.nxinstrument['sample']['data'], group=self.nxdata)
        self.nxdata['data'].write()


    def _convert_bright(self):
        datatype_bright = self.ff_reader.get_data_type()
        height, width = self.ff_reader.get_image_size()
        n_sample_frames = self.ff_reader.get_images_number()

        self.nxbright = nxs.NXgroup(name= 'bright_field')
        self.nxinstrument.insert(self.nxbright)
        self.nxbright.write()
        self.nxinstrument['bright_field']['data'] = nxs.NXfield(
                name = 'data', dtype = datatype_bright ,
                shape = [nxs.UNLIMITED, height, width])

        self.nxinstrument['bright_field']['data'].attrs['Data Type'] = \
            datatype_bright
        self.nxinstrument['bright_field']['data'].attrs['Image Height'] = height
        self.nxinstrument['bright_field']['data'].attrs['Image Width'] = width
        self.nxinstrument['bright_field']['data'].write()

        for id in range(n_sample_frames):
            tomoimagebright = self.ff_reader.get_image(id)
            slab_offset = [id, 0, 0]
            self.nxinstrument['bright_field']['data'].put(tomoimagebright,
                                                          slab_offset,
                                                          refresh=False)
            self.nxinstrument['bright_field']['data'].write()

        ################################################
        # Accelerator current for each image of FF (machine current)
        ff_currents = self.ff_reader.get_machine_currents()
        self.nxinstrument['bright_field']['current'] = nxs.NXfield(
                name = 'current', value=ff_currents, attrs = {'units': 'mA'})
        self.nxinstrument['bright_field']['current'].write()
        ###########################################
        # Exposure Times
        exp_times = self.ff_reader.get_exp_times()
        self.nxinstrument['bright_field']['ExpTimes'] = nxs.NXfield(
                name='ExpTimes', value=exp_times, attrs={'units': 's'})
        self.nxinstrument['bright_field']['ExpTimes'].write()

    def convert_tomography(self):

        if self.filename_zerodeg_in is not None:
            with XradiaFile(self.filename_zerodeg_in) as xrm_file:
                image_zerodeg_in = xrm_file.get_image()
                dtype = xrm_file.data_type
                width = xrm_file.image_width
                height = xrm_file.image_height

                sample = self.nxinstrument['sample']
                sample['0_degrees_initial_image'] = nxs.NXfield(
                        name='0_degrees_initial_image', value=image_zerodeg_in,
                        dtype=dtype)
                sample['0_degrees_initial_image'].attrs['Data Type'] = dtype
                sample['0_degrees_initial_image'].attrs['Image Height'] = height
                sample['0_degrees_initial_image'].attrs['Image Width'] = width
                sample['0_degrees_initial_image'].write()
                print('Zero degrees initial image converted')

        if self.filename_zerodeg_final is not None:
            with XradiaFile(self.filename_zerodeg_final) as xrm_file:
                image_zerodeg_final = xrm_file.get_image()
                dtype = xrm_file.data_type
                width = xrm_file.image_width
                height = xrm_file.image_height

                self.nxinstrument['sample']['0_degrees_initial_image'] = \
                    nxs.NXfield(name='0_degrees_initial_image',
                                value=image_zerodeg_final, dtype=dtype)
                sample = self.nxinstrument['sample']
                sample['0_degrees_final_image'].attrs['Data Type'] = dtype
                sample['0_degrees_final_image'].attrs['Image Height'] = height
                sample['0_degrees_final_image'].attrs['Image Width'] = width
                sample['0_degrees_final_image'].write()
                print('Zero degrees final image converted')

        print("\nConverting tomography image data from xrm(s) to NeXus HDF5.")

        brightexists = False
        darkexists = False
        for file in self.file_order:
            #Tomography Data Images
            if file == 's':
                self._convert_samples()
            #Bright-Field
            elif file == 'b':
                brightexists = True
                self._convert_bright()
            #Post-Dark-Field
            elif file == 'd':
                darkexists = True
                # TODO
                pass

        n_brights = 0
        n_darks = 0 # TODO
        n_samples = self.reader.get_images_number()
        if self.ff_reader:
            n_brights = self.ff_reader.get_images_number()

        self.nxinstrument['sample']['sequence_number'] = range(0, n_samples)
        self.nxinstrument['sample']['sequence_number'].write()

        if(brightexists):
            self.nxinstrument['bright_field']['sequence_number'] = \
                range(0, n_brights)
            self.nxinstrument['bright_field']['sequence_number'].write()

        if(darkexists):
            self.nxinstrument['dark_field']['sequence_number'] = \
                range(0, n_darks)
            self.nxinstrument['dark_field']['sequence_number'].write()

        # NXMonitor data: Not used in TXM microscope.
        # Used to normalize in function fo the beam intensity (to verify).
        # In the ALBA-BL09 case all the values will be set to 1.
        monitor_size = n_samples + n_brights + n_darks
        monitor_counts = np.ones((monitor_size), dtype=np.uint16)
        self.nxmonitor['data'] = nxs.NXfield(
            name='data', value=monitor_counts)
        self.nxmonitor['data'].write()

        # Flush and close the nexus file
        self.nxentry.nxfile.flush()
        self.nxentry.nxfile.close()


class xrmReader(object):

    def __init__(self, file_names):
        self.file_names = file_names

    def get_images_number(self):
        return len(self.file_names)

    def get_pixel_size(self):
        file_name = self.file_names[0]
        with XradiaFile(file_name) as xrm_file:
            return xrm_file.pixel_size

    def get_exp_times(self):
        exp_times = []
        for file_name in self.file_names:
            with XradiaFile(file_name) as xrm_file:
                exp_times.extend(xrm_file.get_exp_times())
        return exp_times
    
    def get_machine_currents(self):
        currents = []
        for file_name in self.file_names:
            with XradiaFile(file_name) as xrm_file:
                currents.extend(xrm_file.get_machine_currents())
        return currents
    
    def get_energies(self):
        energies = []
        for file_name in self.file_names:
            with XradiaFile(file_name) as xrm_file:
                energies.extend(xrm_file.get_energies())
        return energies

    def get_start_time(self):
        filename = self.file_names[0]
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_start_date()

    def get_end_time(self):
        filename = self.file_names[-1]
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_end_date()

    def get_angles(self):
        angles = []
        for file_name in self.file_names:
            with XradiaFile(file_name) as xrm_file:
                angles.extend(xrm_file.get_angles())
        return angles

    def get_x_positions(self):
        positions = []
        for file_name in self.file_names:
            with XradiaFile(file_name) as xrm_file:
                positions.extend(xrm_file.get_x_positions())
        return positions

    def get_y_positions(self):
        positions = []
        for file_name in self.file_names:
            with XradiaFile(file_name) as xrm_file:
                positions.extend(xrm_file.get_y_positions())
        return positions

    def get_z_positions(self):
        positions = []
        for file_name in self.file_names:
            with XradiaFile(file_name) as xrm_file:
                positions.extend(xrm_file.get_z_positions())
        return positions

    def get_image(self, id):
        """
        :param id: number of the images sequence
        :return: image data
        """
        filename = self.file_names[id]
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_image()

    def get_distance(self):
        filename = self.file_names[0]
        #TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_distance()

    def get_sample_id(self):
        filename = self.file_names[0]
        #TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_sample_id()

    def get_xray_magnification(self):
        filename = self.file_names[0]
        #TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_xray_magnification()

    def get_data_type(self):
        filename = self.file_names[0]
        #TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.data_type

    def get_image_size(self):
        filename = self.file_names[0]
        #TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.image_height, xrm_file.image_width

    def get_sample_name(self):
        filename = self.file_names[0]
        file = filename.rsplit('/', 1)[1]
        splitted_file = file.split('_')
        tomo_name = splitted_file[1]
        energy = splitted_file[2]
        pos_ext = splitted_file[-1].find('.xrm')
        conf = splitted_file[-1][:pos_ext]
        return '{0}_{1}_{2}_{3}'.format(splitted_file[0],
                                        tomo_name,
                                        energy,
                                        conf)

    def get_sample_path(self):
        filename = self.file_names[0]
        path = filename.rsplit('/', 1)[0]
        return path