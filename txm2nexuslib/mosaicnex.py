#!/usr/bin/python

"""
(C) Copyright 2014 Marc Rosanes
The program is distributed under the terms of the 
GNU General Public License.

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
import numpy as np
import h5py
import sys
import struct
import datetime
import time
import argparse


class MosaicNex:

    def __init__(self, files, files_order='s', title='X-ray Mosaic', 
                 sourcename='ALBA', sourcetype='Synchrotron X-ray Source', 
                 sourceprobe='x-ray', instrument='BL09 @ ALBA', 
                 sample='Unknown'): 

        self.files = files
        self.num_input_files = len(files)  # number of files.
        self.orderlist = list(files_order)
        # number of 's' (sample), 'b' (brightfield (FF)) and 'd' (darkfield).
        self.num_input_files_verify = len(self.orderlist) 

        self.exitprogram = 0
        if self.num_input_files != self.num_input_files_verify:
            print('Number of input files must be equal ' + 
                  'to number of characters of files_order.\n')
            self.exitprogram = 1
            return
                   
        if 's' not in files_order:
            print('Mosaic data file (xrm) has to be specified, ' + 
                  'inicate it as \'s\' in the argument option -o.\n')
            self.exitprogram = 1
            return

        index_sample_file = files_order.index('s')
        self.mosaic_file_xrm = self.files[index_sample_file]        
        filename_hdf5 = self.mosaic_file_xrm.split('.xrm')[0] + '.hdf5'
        self.mosaichdf = h5py.File(filename_hdf5, 'w')
        self.mosaic_grp = self.mosaichdf.create_group("NXmosaic")
        self.mosaic_grp.attrs['NX_class'] = "NXentry"

        self.index_FF_file = -1
        self.brightexists = 0
        for i in range (0, self.num_input_files):
            # Create bright field structure
            if self.orderlist[i] == 'b':
                self.mosaic_file_FF_xrm = self.files[i]  
                self.index_FF_file = i
                self.brightexists = 1
                self.numrowsFF = 0
                self.numcolsFF = 0
                self.nSampleFramesFF = 1
                self.datatypeFF = 'uint16'
                                    
        self.title = title
        self.sourcename = sourcename
        self.sourcetype = sourcetype
        self.sourceprobe = sourceprobe
        self.instrumentname = instrument
        self.samplename = sample
        self.sampledistance = 0
        self.datatype = 'uint16'  # two bytes
        self.sequence_number = 0
        self.sequence_number_sample = 0
        
        self.programname = 'mosaic2nexus.py'
        self.nxsample = 0
        self.nxmonitor = 0
        self.nxinstrument = 0
        self.nxdata = 0
        self.inst_source_grp = 0
        self.inst_sample_grp = 0
        self.inst_FF_grp = 0

        self.nxdetectorsample = 0
        
        self.numrows = 0
        self.numcols = 0
        self.nSampleFrames = 0

        self.monitorsize = self.nSampleFrames 
        self.monitorcounts = 0

    def NXmosaic_structure(self):    
        # create_basic_structure

        self.mosaic_grp.create_dataset("title", data=self.mosaic_file_xrm)
        self.mosaic_grp.create_dataset("definition", data="NXmosaic")

        self.nxmonitor = self.mosaic_grp.create_group("control")
        self.nxdata = self.mosaic_grp.create_group("data")
        self.nxinstrument = self.mosaic_grp.create_group("instrument")
        self.nxsample = self.mosaic_grp.create_group("sample")

        self.inst_source_grp = self.nxinstrument.create_group("source")
        self.inst_sample_grp = self.nxinstrument.create_group("sample")
        self.inst_FF_grp = self.nxinstrument.create_group("bright_field")

        self.nxinstrument['name'] = self.instrumentname
        self.nxinstrument['source']['name'] = self.sourcename
        self.nxinstrument['source']['type'] = self.sourcetype
        self.nxinstrument['source']['probe'] = self.sourceprobe

        self.nxmonitor.attrs['NX_class'] = "NXmonitor"
        self.nxsample.attrs['NX_class'] = "NXsample"
        self.nxdata.attrs['NX_class'] = "NXdata"
        self.nxinstrument.attrs['NX_class'] = "NXinstrument"
        self.inst_source_grp.attrs['NX_class'] = "NXsource"
        self.inst_sample_grp.attrs['NX_class'] = "NXdetector"
        self.inst_FF_grp.attrs['NX_class'] = "unknown"

    # Function used to convert the metadata from .xrm to NeXus .hdf5
    def convert_metadata(self):

        verbose = False
        print("Trying to convert xrm metadata to NeXus HDF5.")
        
        # Opening the .xrm files as Ole structures
        ole = OleFileIO(self.mosaic_file_xrm)

        # xrm files have been opened
        self.mosaic_grp['program_name'] = self.programname
        self.mosaic_grp['program_name'].attrs['version'] = '2.0'
        self.mosaic_grp['program_name'].attrs['configuration'] = \
            (self.programname
             + ' '
             + ' '.join(sys.argv[1:]))
                                                              
        # SampleID
        if ole.exists('SampleInfo/SampleID'):   
            stream = ole.openstream('SampleInfo/SampleID')
            data = stream.read()
            struct_fmt = '<'+'50s'
            samplename = struct.unpack(struct_fmt, data)
            if self.samplename != 'Unknown':
                self.samplename = samplename[0]    
            if verbose: 
                print "SampleInfo/SampleID: %s " % self.samplename 
            self.nxsample['name'] = self.samplename
        else:
            print("There is no information about SampleID")

        # Pixel-size
        if ole.exists('ImageInfo/PixelSize'):   
            stream = ole.openstream('ImageInfo/PixelSize')
            data = stream.read()
            struct_fmt = '<1f'
            pixelsize = struct.unpack(struct_fmt, data)
            pixelsize = pixelsize[0]
            if verbose: 
                print "ImageInfo/PixelSize: %f " % pixelsize
            self.inst_sample_grp.create_dataset("x_pixel_size", data=pixelsize)
            self.inst_sample_grp.create_dataset("y_pixel_size", data=pixelsize)
            self.inst_sample_grp["x_pixel_size"].attrs["units"] = "um"
            self.inst_sample_grp["y_pixel_size"].attrs["units"] = "um"
        else:
            print("There is no information about PixelSize")

        # Accelerator current (machine current)
        if ole.exists('ImageInfo/Current'):   
            stream = ole.openstream('ImageInfo/Current')
            data = stream.read()
            struct_fmt = '<1f'
            current = struct.unpack(struct_fmt, data)
            current = current[0]
            if verbose: 
                print "ImageInfo/Current: %f " % current

            self.inst_sample_grp.create_dataset("current", data=current)
            self.inst_sample_grp["current"].attrs["units"] = "mA"
        else:
            print("There is no information about Current")

        # Mosaic data size 
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
            print('There is no information about the mosaic size ' +
                  '(ImageHeight, ImageWidth or Number of images)')

        # FF data size
        if self.brightexists == 1:
            oleFF = OleFileIO(self.mosaic_file_FF_xrm)
            if (ole.exists('ImageInfo/NoOfImages') 
                and oleFF.exists('ImageInfo/ImageWidth') 
                and oleFF.exists('ImageInfo/ImageHeight')):                  
                        
                stream = oleFF.openstream('ImageInfo/NoOfImages')
                data = stream.read()
                nimages = struct.unpack('<I', data)
                if verbose: 
                    print "ImageInfo/NoOfImages = %i" % nimages[0] 
                self.nSampleFramesFF = np.int(nimages[0])
            
                stream = oleFF.openstream('ImageInfo/ImageHeight')
                data = stream.read()
                ximage = struct.unpack('<I', data)    
                if verbose: 
                    print "ImageInfo/ImageHeight = %i" % ximage[0]  
                self.numrowsFF = np.int(ximage[0])
                
                stream = oleFF.openstream('ImageInfo/ImageWidth')
                data = stream.read()
                yimage = struct.unpack('<I', data)
                if verbose: 
                    print "ImageInfo/ImageWidth = %i" % yimage[0]  
                self.numcolsFF = np.int(yimage[0])   
                        
            else:
                print('There is no information about the mosaic size ' +
                      '(ImageHeight, ImageWidth or Number of images)')
            oleFF.close()    
            
        # Energy            	
        if ole.exists('ImageInfo/Energy'):
            stream = ole.openstream('ImageInfo/Energy')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.nSampleFrames)
            # we found some xrm images (flatfields) with different encoding 
            # of data
            try:
                energies = struct.unpack(struct_fmt, data)
            except struct.error:
                print >> sys.stderr, ('Unexpected data length (%i bytes). ' +  
                                      'Trying to unpack Energies with: ' + 
                                      '"f"+"36xf"*(nSampleFrames-1)'%len(data))
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                energies = struct.unpack(struct_fmt, data)
            if verbose: print "ImageInfo/Energy: \n ",  energies  
            self.inst_source_grp['energy'] = energies
            self.inst_source_grp['energy'].attrs['units'] = 'eV'
        else:
            print('There is no information about the energies with which '
                  'have been taken the different mosaic images')

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
                print "ImageInfo/DataType: %s " % self.datatype
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

            if verbose: 
                print "ImageInfo/Date = %s" % starttimeiso 
            self.mosaic_grp['start_time'] = str(starttimeiso)

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

            if verbose: 
                print "ImageInfo/Date = %s" % endtimeiso 
            self.mosaic_grp['end_time'] = str(endtimeiso)

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

            self.nxsample['rotation_angle'] = angles
            self.nxsample['rotation_angle'].attrs['target'] = \
                "/NXmosaic/sample/rotation_angle"
            self.nxsample['rotation_angle'].attrs['units'] = 'degrees'

            # h5py NeXus link
            source_addr = '/NXmosaic/sample/rotation_angle'
            target_addr = 'rotation_angle'
            self.nxsample['rotation_angle'].attrs['target'] = source_addr
            self.nxdata._id.link(source_addr, target_addr, h5py.h5g.LINK_HARD)

        else:
            print('There is no information about the angles at' 
                   'which have been taken the different mosaic images')

        # Sample translations in X, Y and Z 
        # X sample translation: nxsample['z_translation']
        if ole.exists('ImageInfo/XPosition'):
            stream = ole.openstream('ImageInfo/XPosition')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.nSampleFrames)
            # There have been found some xrm images (flatfields) with 
            # different encoding of data
            try: 
                xpositions = struct.unpack(struct_fmt, data) 
            except struct.error:
                print >> sys.stderr, ('Unexpected data length (%i bytes). ' +  
                                      'Trying to unpack XPositions with: ' + 
                                      '"f"+"36xf"*(nSampleFrames-1)'%len(data))
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                xpositions = struct.unpack(struct_fmt, data)
            if verbose: 
                print "ImageInfo/XPosition: \n ",  xpositions
            self.nxsample['x_translation'] = xpositions
            self.nxsample['x_translation'].attrs['units'] = 'mm'
        else:
            print("There is no information about xpositions")

        # Y sample translation: nxsample['z_translation']
        if ole.exists('ImageInfo/YPosition'):
            stream = ole.openstream('ImageInfo/YPosition')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.nSampleFrames)
            # we found some xrm images (flatfields) with different encoding 
            # of data.
            try:
                ypositions = struct.unpack(struct_fmt, data) 
            except struct.error:
                print >> sys.stderr, ('Unexpected data length (%i bytes). ' +  
                                      'Trying to unpack YPositions with: ' + 
                                      '"f"+"36xf"*(nSampleFrames-1)'%len(data))
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                ypositions = struct.unpack(struct_fmt, data)
            if verbose: 
                print "ImageInfo/YPosition: \n ",  ypositions  
            self.nxsample['y_translation'] = ypositions
            self.nxsample['y_translation'].attrs['units'] = 'mm'
        else:
            print("There is no information about xpositions")

        # Z sample translation: nxsample['z_translation']
        if ole.exists('ImageInfo/ZPosition'):
            stream = ole.openstream('ImageInfo/ZPosition')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.nSampleFrames)
            # we found some xrm images (flatfields) with different encoding 
            # of data.
            try: 
                zpositions = struct.unpack(struct_fmt, data)
            except struct.error:
                print >> sys.stderr, ('Unexpected data length (%i bytes). ' +  
                                      'Trying to unpack ZPositions with: ' + 
                                      '"f"+"36xf"*(nSampleFrames-1)'%len(data))
                struct_fmt = '<'+"f"+"36xf"*(self.nSampleFrames-1)
                zpositions = struct.unpack(struct_fmt, data)
            if verbose: 
                print "ImageInfo/ZPosition: \n ",  zpositions
            self.nxsample['z_translation'] = zpositions
            self.nxsample['z_translation'].attrs['units'] = 'mm'
        else:
            print("There is no information about xpositions")

        # NXMonitor data: Not used in TXM microscope. 
        # Used to normalize in function fo the beam intensity (to verify). 
        # In the ALBA-BL09 case all the values will be set to 1.
        self.monitorsize = self.nSampleFrames
        self.monitorcounts = np.ones(self.monitorsize, dtype=np.uint16)
        self.nxmonitor['data'] = self.monitorcounts

        ole.close()
        print ("Meta-Data conversion from 'xrm' to NeXus HDF5 has been done.\n")

    # Converts a Mosaic image fromt xrm to NeXus hdf5.
    def convert_mosaic(self): 

        # Bright-Field
        if not self.brightexists:
            print('\nWarning: Bright-Field is not present, normalization ' + 
                  'will not be possible if you do not insert a ' + 
                  'Bright-Field (FF). \n') 
                  
        verbose = False
        print("Converting mosaic image data from xrm to NeXus HDF5.")

        # Opening the mosaic .xrm file as an Ole structure.
        olemosaic = OleFileIO(self.mosaic_file_xrm)

        # Mosaic data image
        self.inst_sample_grp.create_dataset(
            "data",
            shape=(self.numrows, self.numcols),
            chunks=(1, self.numcols),
            dtype=self.datatype)

        self.inst_sample_grp['data'].attrs['Data Type'] = self.datatype
        self.inst_sample_grp['data'].attrs['Number of Subimages'] = \
            self.nSampleFrames
        self.inst_sample_grp['data'].attrs['Image Height'] = self.numrows
        self.inst_sample_grp['data'].attrs['Image Width'] = self.numcols

        img_string = "ImageData1/Image1"
        stream = olemosaic.openstream(img_string)

        for i in range(0, self.numrows):
            if self.datatype == 'uint16':
                dt = np.uint16
                data = stream.read(self.numcols*2)
            elif self.datatype == 'float':  

                dt = np.float          
                data = stream.read(self.numcols*4)                      
            else:
                print "Wrong data type"
                return

            imgdata = np.frombuffer(data, dtype=dt, count=self.numcols)
            imgdata = np.reshape(imgdata, (1, self.numcols), order='A')
            self.inst_sample_grp['data'][i] = imgdata
            if i % 100 == 0:
                print('Mosaic row %i converted' % (i + 1))

        olemosaic.close()

        source_addr = '/NXmosaic/instrument/sample/data'
        target_addr = 'data'
        self.inst_sample_grp['data'].attrs['target'] = source_addr
        self.nxdata._id.link(source_addr, target_addr, h5py.h5g.LINK_HARD)

        print ("Mosaic image data conversion to NeXus HDF5 has been done.\n")

        # FF Data
        if self.index_FF_file != -1:
            
            oleFF = OleFileIO(self.mosaic_file_FF_xrm)
            print ("Trying to convert FF xrm image to NeXus HDF5.")

            # Mosaic FF data image
            img_string = "ImageData1/Image1"
            stream = oleFF.openstream(img_string)        

            if self.datatypeFF == 'uint16':
                data = stream.read()
                struct_fmt = "<{0:10}H".format(self.numrowsFF*self.numcolsFF)

            elif self.datatypeFF == 'float':
                data = stream.read()
                struct_fmt = "<{0:10}f".format(self.numrowsFF*self.numcolsFF)

            else:
                print "Wrong FF data type"
                return

            imgdata = struct.unpack(struct_fmt, data)
            imgdataFF = np.reshape(imgdata,
                                   (self.numrowsFF, self.numcolsFF), order='A')

            self.inst_FF_grp['data'] = imgdataFF
            self.inst_FF_grp['data'].attrs['Data Type'] = self.datatypeFF
            self.inst_FF_grp['data'].attrs['Number of images'] = \
                self.nSampleFramesFF
            self.inst_FF_grp['data'].attrs['Image Height'] = self.numrowsFF
            self.inst_FF_grp['data'].attrs['Image Width'] = self.numcolsFF

            oleFF.close()
            print("FF image converted")
        self.mosaichdf.flush()
        self.mosaichdf.close()
