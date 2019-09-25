#!/usr/bin/python

"""
(C) Copyright 2016-2017 Carlos Falcon, Zbigniew Reszela, Marc Rosanes
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
import numpy as np
import h5py
import sys
import struct
import datetime
import re
import pkg_resources
#import pprint

from tinydb import Query
from operator import itemgetter
from txm2nexuslib.parser import get_db, get_file_paths


SAMPLEENC = 2
DETECTORENC_Z = 23
ENERGY = 27
CURRENT = 28
ENERGYENC = 30

class FilesOrganization(object):

    def __init__(self):
        pass

    def get_samples(self, txm_txt_script, use_existing_db=False,
                    use_subfolders=True, organize_by_repetitions=False):
        """Organize the files by samples"""

        #prettyprinter = pprint.PrettyPrinter(indent=4)

        if use_subfolders:
            print("Using Subfolders for finding the files")
        else:
            print("Searching files through the whole root path")

        root_path = os.path.dirname(os.path.abspath(txm_txt_script))

        db = get_db(txm_txt_script, use_existing_db=use_existing_db)
        all_file_records = db.all()
        #prettyprinter.pprint(all_file_records)

        dates_samples_energies = []
        for record in all_file_records:
            dates_samples_energies.append((record["date"],
                                           record["sample"],
                                           record["energy"]))
        dates_samples_energies = list(set(dates_samples_energies))

        samples = {}
        files_query = Query()

        for date_sample_energie in dates_samples_energies:
            files_raw_data = {}
            files_for_sample_subdict = {}

            date = date_sample_energie[0]
            sample = date_sample_energie[1]
            energy = date_sample_energie[2]

            query_impl = ((files_query.date == date) &
                          (files_query.sample == sample) &
                          (files_query.energy == energy) &
                          (files_query.FF == False))

            records_by_sample_and_energy = db.search(query_impl)

            if not organize_by_repetitions:
                zps_by_sample_and_e = [record["zpz"] for record in
                                       records_by_sample_and_energy]
                zpz_positions_by_sample_e = sorted(set(zps_by_sample_and_e))

                for zpz in zpz_positions_by_sample_e:
                    query_impl = ((files_query.date == date) &
                                  (files_query.sample == sample) &
                                  (files_query.energy == energy) &
                                  (files_query.zpz == zpz) &
                                  (files_query.FF == False))
                    fn_by_zpz_query = db.search(query_impl)
                    sorted_fn_by_zpz_query = sorted(fn_by_zpz_query,
                                                    key=itemgetter('angle'))

                    files = get_file_paths(sorted_fn_by_zpz_query, root_path,
                                           use_subfolders=use_subfolders)
                    files_raw_data[zpz] = files
            else:
                repetitions_by_sample_and_e = [record["repetition"] for record
                                               in records_by_sample_and_energy]

                repetitions_by_sample_and_e = sorted(set(
                    repetitions_by_sample_and_e))

                for repetition in repetitions_by_sample_and_e:
                    query_impl = ((files_query.date == date) &
                                  (files_query.sample == sample) &
                                  (files_query.energy == energy) &
                                  (files_query.repetition == repetition) &
                                  (files_query.FF == False))
                    fn_by_repetition_query = db.search(query_impl)
                    sorted_fn_by_repetition_query = sorted(
                        fn_by_repetition_query, key=itemgetter('angle'))
                    files = get_file_paths(sorted_fn_by_repetition_query,
                                           root_path,
                                           use_subfolders=use_subfolders)
                    files_raw_data[repetition] = files

            # Get FF image records
            fn_ff_query_by_energy = ((files_query.date == date) &
                                     (files_query.sample == sample) &
                                     (files_query.energy == energy) &
                                     (files_query.FF == True))
            query_output = db.search(fn_ff_query_by_energy)
            files_FF = get_file_paths(query_output, root_path,
                                      use_subfolders=use_subfolders)

            files_for_sample_subdict['tomos'] = files_raw_data
            files_for_sample_subdict['ff'] = files_FF
            samples[date_sample_energie] = files_for_sample_subdict

        #prettyprinter.pprint(samples)
        return samples


class validate_getter(object):
    def __init__(self, required_fields):
        self.required_fields = required_fields

    def __call__(self, method):
        def wrapped_method(xradia_file):
            if not xradia_file.is_opened():
                raise RuntimeError("XradiaFile is not opened")
            for field in self.required_fields:
                if not xradia_file.exists(field):
                    raise RuntimeError(
                        "%s does not exist in XradiaFile" % field)
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
        struct_fmt = '<' + '50s'
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
        return self.axes_positions[DETECTORENC_Z] * 1000  # from mm to um

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
            struct_fmt = "<{0:10}H".format(
                self.image_height * self.image_width)
            imgdata = struct.unpack(struct_fmt, data)
        elif self.data_type == 'float':
            struct_fmt = "<{0:10}f".format(
                self.image_height * self.image_width)
            imgdata = struct.unpack(struct_fmt, data)
        else:
            print "Wrong data type"
            return

        image = np.flipud(np.reshape(imgdata, (self.image_height,
                                               self.image_width), order='A'))
        image = np.reshape(image, (1, self.image_height, self.image_width),
                           order='A')
        return image

    @validate_getter(["ImageData1/Image1"])
    def get_image_2D(self):
        stream = self.file.openstream('ImageData1/Image1')
        data = stream.read()

        if self.data_type == 'uint16':
            struct_fmt = "<{0:10}H".format(
                self.image_height * self.image_width)
            imgdata = struct.unpack(struct_fmt, data)
        elif self.data_type == 'float':
            struct_fmt = "<{0:10}f".format(
                self.image_height * self.image_width)
            imgdata = struct.unpack(struct_fmt, data)
        else:
            print "Wrong data type"
            return

        image = np.flipud(np.reshape(imgdata, (self.image_height,
                                               self.image_width), order='A'))
        return image

    @validate_getter(["PositionInfo/AxisNames"])
    def get_axes_names(self):
        if self._axes_names is None:
            stream = self.file.openstream('PositionInfo/AxisNames')
            data = stream.read()
            lendatabytes = len(data)
            formatstring = '<' + str(lendatabytes) + 'c'
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
        number_of_floats = num_axes * self.no_of_images
        struct_fmt = '<' + str(number_of_floats) + 'f'
        number_of_bytes = number_of_floats * 4  # 4 bytes every float
        data = stream.read(number_of_bytes)
        axis = struct.unpack(struct_fmt, data)

        currents = self.no_of_images * [0]
        for i in range(self.no_of_images):
            currents[i] = axis[self.no_of_axes * i + CURRENT]  # In mA
        return currents

    @validate_getter([])
    def get_energies(self):
        if (self.energyenc_name.lower() == "energyenc"):
            if self.file.exists('PositionInfo/MotorPositions'):
                stream = self.file.openstream('PositionInfo/MotorPositions')
                number_of_floats = self.no_of_axes * self.no_of_images
                struct_fmt = '<' + str(number_of_floats) + 'f'
                number_of_bytes = number_of_floats * 4  # 4 bytes every float
                data = stream.read(number_of_bytes)
                axis = struct.unpack(struct_fmt, data)
                energies = self.no_of_images * [0]
                for i in range(self.no_of_images):
                    energies[i] = axis[self.no_of_axes * i + ENERGYENC] # In eV
        # Energy for each image calculated from Energy motor ####
        elif (self.energy_name == "Energy"):
            if self.file.exists('PositionInfo/MotorPositions'):
                stream = self.file.openstream('PositionInfo/MotorPositions')
                number_of_floats = self.no_of_axes * self.no_of_images
                struct_fmt = '<' + str(number_of_floats) + 'f'
                number_of_bytes = number_of_floats * 4  # 4 bytes every float
                data = stream.read(number_of_bytes)
                axis = struct.unpack(struct_fmt, data)
                energies = self.no_of_images * [0]
                for i in range(self.no_of_images):
                    energies[i] = axis[self.no_of_axes * i + ENERGY]  # In eV
        # Energy for each image calculated from ImageInfo ####
        elif self.file.exists('ImageInfo/Energy'):
            stream = self.file.openstream('ImageInfo/Energy')
            data = stream.read()
            struct_fmt = "<{0:10}f".format(self.no_of_images)
            try:  # we found some txrm images (flatfields) with different encoding of data
                energies = struct.unpack(struct_fmt, data)
            except struct.error:
                print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack energies with: "f"+"36xf"*(nSampleFrames-1)' % len(
                    data)
                struct_fmt = '<' + "f" + "36xf" * (self.no_of_images - 1)
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
        try:  # we found some txrm images (flatfields) with different encoding of data
            exp_times = struct.unpack(struct_fmt, data)
        except struct.error:
            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack exposure times with: "f"+"36xf"*(nSampleFrames-1)' % len(
                data)
            struct_fmt = '<' + "f" + "36xf" * (self.no_of_images - 1)
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
        # Found some txrm images with different encoding of data #
        try:
            positions = struct.unpack(struct_fmt, data)
        except struct.error:
            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack XPositions with: "f"+"36xf"*(nSampleFrames-1)' % len(
                data)
            struct_fmt = '<' + "f" + "36xf" * (self.no_of_images - 1)
            positions = struct.unpack(struct_fmt, data)
        return positions

    @validate_getter(['ImageInfo/YPosition'])
    def get_y_positions(self):
        stream = self.file.openstream('ImageInfo/YPosition')
        data = stream.read()
        struct_fmt = "<{0:10}f".format(self.no_of_images)
        # Found some txrm images with different encoding of data #
        try:
            positions = struct.unpack(struct_fmt, data)
        except struct.error:
            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack YPositions with: "f"+"36xf"*(nSampleFrames-1)' % len(
                data)
            struct_fmt = '<' + "f" + "36xf" * (self.no_of_images - 1)
            positions = struct.unpack(struct_fmt, data)
        return positions

    @validate_getter(['ImageInfo/ZPosition'])
    def get_z_positions(self):
        stream = self.file.openstream('ImageInfo/ZPosition')
        data = stream.read()
        struct_fmt = "<{0:10}f".format(self.no_of_images)
        # Found some txrm images with different encoding of data #
        try:
            positions = struct.unpack(struct_fmt, data)
        except struct.error:
            print >> sys.stderr, 'Unexpected data length (%i bytes). Trying to unpack ZPositions with: "f"+"36xf"*(nSampleFrames-1)' % len(
                data)
            struct_fmt = '<' + "f" + "36xf" * (self.no_of_images - 1)
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
    def get_single_date(self):
        stream = self.file.openstream('ImageInfo/Date')
        data = stream.read()
        date = struct.unpack('<' + '17s23x', data)[0]

        [day, hour] = date.split(" ")
        [month, day, year] = day.split("/")
        [hour, minute, second] = hour.split(":")

        year = '20' + year
        year = int(year)
        month = int(month)
        day = int(day)
        hour = int(hour)
        minute = int(minute)
        second = int(second)

        raw_time = datetime.datetime(year, month, day,
                                      hour, minute, second)
        time_iso = raw_time.isoformat()
        return time_iso

    @validate_getter(["ImageInfo/Date"])
    def get_dates(self):
        if self._dates is None:
            stream = self.file.openstream('ImageInfo/Date')
            data = stream.read()
            self._dates = struct.unpack('<' + '17s23x' * self.no_of_images,
                                        data)
        return self._dates

    dates = property(get_dates)

    def get_start_date(self):

        startdate = self.dates[0]
        [day, hour] = startdate.split(" ")
        [month, day, year] = day.split("/")
        [hour, minute, second] = hour.split(":")

        year = '20' + year
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
        enddate = self.dates[self.no_of_images - 1]
        [endday, endhour] = enddate.split(" ")
        [endmonth, endday, endyear] = endday.split("/")
        [endhour, endminute, endsecond] = endhour.split(":")

        endyear = '20' + endyear
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

    def get_det_zero(self):
        where_detzero = ("ConfigureBackup/ConfigCamera/" +
                         "Camera 1/ConfigZonePlates/DetZero")
        if self._det_zero is None and self.file.exists(where_detzero):
            stream = self.file.openstream("ConfigureBackup/ConfigCamera/" +
                                          "Camera 1/ConfigZonePlates/DetZero")
            data = stream.read()
            if len(data) != 0:
                struct_fmt = '<1f'
                sample_to_detector_zero_enc = struct.unpack(struct_fmt, data)
                self._det_zero = sample_to_detector_zero_enc[0]
            else:
                self._det_zero = 0
        else:
            self._det_zero = 0
        return self._det_zero

    det_zero = property(get_det_zero)


class xrmNXtomo(object):

    definition = 'NXtomo'
    # CCD detector pixelsize in micrometers
    CCDdetector_pixelsize = 13
    CCDdetector_pixelsize_unit = 'um'

    def __init__(self, reader, ffreader, file_order, program_name,
                 hdf5_output_path=None, title='X-ray tomography',
                 zero_deg_in=None, zero_deg_final=None, sourcename='ALBA',
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
        self.txrmhdf = h5py.File(self.hdf5_file_name, 'w')

        self.filename_zerodeg_in = zero_deg_in
        self.filename_zerodeg_final = zero_deg_final

        self.nxentry = None
        self.nxsample = None
        self.nxmonitor = None
        self.nxinstrument = None
        self.nxdata = None
        self.nxdetectorsample = None
        self.nxsource = None

        self.count_num_sequence = 0
        self.num_sample_sequence = []
        self.num_bright_sequence = []
        self.num_dark_sequence = []

        self.program_name = program_name
        version = pkg_resources.get_distribution("bl09-imaging").version
        self.program_version = version
        self.title = title
        self.sourcename = sourcename
        self.sourcetype = sourcetype
        self.sourceprobe = sourceprobe
        self.instrument = instrument
        self.sample = sample
        self.file_order = list(file_order)

        self.datatype_zerodeg = 'uint16'
        self.numrows_zerodeg = 0
        self.numcols_zerodeg = 0
        self.filename_zerodeg_in = zero_deg_in
        self.filename_zerodeg_final = zero_deg_final

        self.numrows = 0
        self.numcols = 0
        self.nSampleFrames = 0
        self.datatype = None

        self.numrows_bright = 0
        self.numcols_bright = 0
        self.nFramesBright = 0
        self.datatype_bright = 'uint16'

    def convert_metadata(self):

        self.nxentry = self.txrmhdf.create_group(self.definition)
        self.nxentry.attrs['NX_class'] = "NXentry"

        self.nxentry.create_dataset("title", data=self.title)
        self.nxentry.create_dataset("definition", data=self.definition)

        self.nxinstrument = self.nxentry.create_group("instrument")
        self.nxsample = self.nxentry.create_group("sample")
        self.nxmonitor = self.nxentry.create_group("control")
        self.nxdata = self.nxentry.create_group("data")

        self.nxmonitor.attrs['NX_class'] = "NXmonitor"
        self.nxsample.attrs['NX_class'] = "NXsample"
        self.nxdata.attrs['NX_class'] = "NXdata"
        self.nxinstrument.attrs['NX_class'] = "NXinstrument"

        self.nxinstrument['name'] = self.instrument
        pixel_size = "%d %s" % (self.CCDdetector_pixelsize,
                                self.CCDdetector_pixelsize_unit)
        self.nxinstrument['name'].attrs['CCD pixel size'] = pixel_size

        self.nxsource= self.nxinstrument.create_group("source")
        self.nxdetectorsample = self.nxinstrument.create_group("sample")
        self.nxsource.attrs['NX_class'] = "NXsource"
        self.nxdetectorsample.attrs['NX_class'] = "NXdetector"

        self.nxinstrument['source']['name'] = self.sourcename
        self.nxinstrument['source']['type'] = self.sourcetype
        self.nxinstrument['source']['probe'] = self.sourceprobe

        self.nxentry['program_name'] = self.program_name
        self.nxentry['program_name'].attrs['version'] = self.program_version
        self.nxentry['program_name'].attrs['configuration'] = \
            (self.program_name + ' ' + ' '.join(sys.argv[1:]))

        # Sample-ID
        sample_name = self.reader.get_sample_name()
        self.nxsample['name'] = sample_name

        distance = self.reader.get_distance()
        self.nxdetectorsample.create_dataset("distance", data=distance)
        self.nxdetectorsample["distance"].attrs["units"] = "um"

        # Pixel-size
        pixel_size = self.reader.get_pixel_size()
        self.nxdetectorsample.create_dataset("x_pixel_size",
                                             data=pixel_size)
        self.nxdetectorsample.create_dataset("y_pixel_size",
                                             data=pixel_size)
        self.nxdetectorsample["x_pixel_size"].attrs["units"] = "um"
        self.nxdetectorsample["y_pixel_size"].attrs["units"] = "um"

        # X-Ray Magnification
        magnification = self.reader.get_xray_magnification()
        self.nxdetectorsample['magnification'] = magnification

        # Accelerator current for each image (machine current)
        currents = self.reader.get_machine_currents()
        self.nxdetectorsample['current'] = currents
        self.nxdetectorsample['current'].attrs["units"] = "mA"

        # Energy for each image:
        energies = self.reader.get_energies()
        self.nxsource["energy"] = energies
        self.nxsource["energy"].attrs["units"] = "eV"

        # Exposure Times
        exptimes = self.reader.get_exp_times()
        self.nxdetectorsample["ExpTimes"] = exptimes
        self.nxdetectorsample["ExpTimes"].attrs["units"] = "s"

        # Start and End Times
        starttimeiso = self.reader.get_start_time()
        self.nxentry['start_time'] = str(starttimeiso)
        endtimeiso = self.reader.get_end_time()
        self.nxentry['end_time'] = str(endtimeiso)

        # Sample rotation angles
        angles = self.reader.get_angles()
        self.nxsample['rotation_angle'] = angles
        self.nxsample["rotation_angle"].attrs["units"] = "degrees"

        # h5py NeXus link
        source_addr = '/NXtomo/sample/rotation_angle'
        target_addr = 'rotation_angle'
        self.nxsample['rotation_angle'].attrs['target'] = source_addr
        self.nxdata._id.link(source_addr, target_addr, h5py.h5g.LINK_HARD)

        # X sample translation: nxsample['z_translation']
        xpositions = self.reader.get_x_positions()
        self.nxsample['x_translation'] = xpositions
        self.nxsample['x_translation'].attrs['units'] = 'um'

        # Y sample translation: nxsample['z_translation']
        ypositions = self.reader.get_y_positions()
        self.nxsample['y_translation'] = ypositions
        self.nxsample['y_translation'].attrs['units'] = 'um'

        # Z sample translation: nxsample['z_translation']
        zpositions = self.reader.get_z_positions()
        self.nxsample['z_translation'] = zpositions
        self.nxsample['z_translation'].attrs['units'] = 'um'

    def _convert_samples(self):
        self.numrows, self.numcols = self.reader.get_image_size()
        data_type = self.reader.get_data_type()
        self.nSampleFrames = self.reader.get_images_number()

        if data_type == 'float':
            self.datatype = 'float32'
        else:
            self.datatype = data_type

        self.nxdetectorsample.create_dataset(
            "data",
            shape=(self.nSampleFrames,
                   self.numrows,
                   self.numcols),
            chunks=(1,
                    self.numrows,
                    self.numcols),
            dtype=self.datatype)

        self.nxdetectorsample['data'].attrs[
            'Data Type'] = self.datatype
        self.nxdetectorsample[
            'data'].attrs['Number of Frames'] = self.nSampleFrames
        self.nxdetectorsample['data'].attrs[
            'Image Height'] = self.numrows
        self.nxdetectorsample['data'].attrs[
            'Image Width'] = self.numcols

        for numimage in range(self.nSampleFrames):
            self.count_num_sequence = self.count_num_sequence + 1
            tomoimagesingle = self.reader.get_image(numimage)
            self.num_sample_sequence.append(
                self.count_num_sequence)
            self.nxdetectorsample['data'][numimage] = tomoimagesingle
            if numimage % 20 == 0:
                print('Image %i converted' % numimage)
            if numimage + 1 == self.nSampleFrames:
                print ('%i images converted\n' % self.nSampleFrames)

        # h5py NeXus link
        source_addr = '/NXtomo/instrument/sample/data'
        target_addr = 'data'
        self.nxdetectorsample['data'].attrs[
            'target'] = source_addr
        self.nxdata._id.link(source_addr, target_addr,
                             h5py.h5g.LINK_HARD)

    def _convert_bright(self):
        self.datatype_bright = self.ff_reader.get_data_type()
        self.numrows_bright, self.numcols_bright = \
            self.ff_reader.get_image_size()
        self.nFramesBright = self.ff_reader.get_images_number()

        self.nxbright = self.nxinstrument.create_group("bright_field")
        self.nxbright.attrs['NX_class'] = "Unknown"
        self.nxbright.create_dataset(
            "data",
            shape=(self.nFramesBright,
                   self.numrows_bright,
                   self.numcols_bright),
            chunks=(1,
                    self.numrows_bright,
                    self.numcols_bright),
            dtype=self.datatype_bright)
        self.nxbright['data'].attrs['Data Type'] = \
            self.datatype_bright
        self.nxbright['data'].attrs['Image Height'] = \
            self.numrows_bright
        self.nxbright['data'].attrs['Image Width'] = \
            self.numcols_bright

        for numimage in range(self.nFramesBright):
            if numimage + 1 == self.nFramesBright:
                print ('%i Bright-Field images '
                       'converted\n' % self.nFramesBright)
            self.count_num_sequence = self.count_num_sequence + 1
            tomoimagesingle = self.ff_reader.get_image(numimage)
            self.num_bright_sequence.append(self.count_num_sequence)
            self.nxbright['data'][numimage] = tomoimagesingle

        # Accelerator current for each image of FF (machine current)
        ff_currents = self.ff_reader.get_machine_currents()
        self.nxbright.create_dataset("current", data=ff_currents)
        self.nxbright["current"].attrs["units"] = "mA"

        # Exposure Times
        exp_times = self.ff_reader.get_exp_times()
        self.nxbright.create_dataset("ExpTimes", data=exp_times)
        self.nxbright["ExpTimes"].attrs["units"] = "s"

    def _convert_zero_deg_images(self, ole_zerodeg):
        verbose = False
        # DataType: 10 float; 5 uint16 (unsigned 16-bit (2-byte) integers)
        if ole_zerodeg.exists('ImageInfo/DataType'):
            stream = ole_zerodeg.openstream('ImageInfo/DataType')
            data = stream.read()
            struct_fmt = '<1I'
            datatype_zerodeg = struct.unpack(struct_fmt, data)
            datatype_zerodeg = int(datatype_zerodeg[0])
            if datatype_zerodeg == 5:
                self.datatype_zerodeg = 'uint16'
            else:
                self.datatype_zerodeg = 'float'
            if verbose:
                print "ImageInfo/DataType: %s " % self.datatype_zerodeg
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
                struct_fmt = "<{0:10}H".format(self.numrows_zerodeg *
                                               self.numcols_zerodeg)
                imgdata = struct.unpack(struct_fmt, data)
            elif self.datatype == 'float':
                struct_fmt = "<{0:10}f".format(self.numrows_zerodeg *
                                               self.numcols_zerodeg)
                imgdata = struct.unpack(struct_fmt, data)
            else:
                print "Wrong data type"

            imgdata_zerodeg = np.flipud(np.reshape(imgdata,
                                                   (self.numrows,
                                                    self.numcols),
                                                   order='A'))
        else:
            imgdata_zerodeg = 0
        return imgdata_zerodeg

    def convert_tomography(self):
        # TODO: 0 degree images not implemented in xrm2nexs
        if self.filename_zerodeg_in is not None:
            ole_zerodeg_in = OleFileIO(self.filename_zerodeg_in)
            image_zerodeg_in = self._convert_zero_deg_images(ole_zerodeg_in)
            self.nxdetectorsample.create_dataset(
                '0_degrees_initial_image',
                data=image_zerodeg_in,
                dtype=self.datatype_zerodeg)
            self.nxdetectorsample['0_degrees_initial_image'].attrs[
                'Data Type'] = self.datatype_zerodeg
            self.nxdetectorsample['0_degrees_initial_image'].attrs[
                'Image Height'] = self.numrows_zerodeg
            self.nxdetectorsample['0_degrees_initial_image'].attrs[
                'Image Width'] = self.numcols_zerodeg
            print('Zero degrees initial image converted')

        if self.filename_zerodeg_final is not None:
            ole_zerodeg_final = OleFileIO(self.filename_zerodeg_final)
            image_zerodeg_final = self._convert_zero_deg_images(
                ole_zerodeg_final)
            self.nxdetectorsample.create_dataset(
                '0_degrees_final_image',
                data=image_zerodeg_final,
                dtype=self.datatype_zerodeg)
            self.nxdetectorsample['0_degrees_final_image'].attrs[
                'Data Type'] = self.datatype_zerodeg
            self.nxdetectorsample['0_degrees_final_image'].attrs[
                'Image Height'] = self.numrows_zerodeg
            self.nxdetectorsample['0_degrees_final_image'].attrs[
                'Image Width'] = self.numcols_zerodeg
            print('Zero degrees final image converted')

        print("\nConverting tomography image data from xrm(s) to NeXus HDF5.")

        brightexists = False
        darkexists = False
        for file in self.file_order:
            # Tomography Data Images
            if file == 's':
                self._convert_samples()
            # Bright-Field
            elif file == 'b':
                brightexists = True
                self._convert_bright()
            # Post-Dark-Field
            elif file == 'd':
                darkexists = True
                # TODO
                pass

        self.nxinstrument['sample']['sequence_number'] = \
            self.num_sample_sequence

        if brightexists:
            self.nxinstrument['bright_field']['sequence_number'] = \
                self.num_bright_sequence

        if darkexists:
            self.nxinstrument['dark_field']['sequence_number'] = \
                self.num_dark_sequence

        # NXMonitor data: Not used in TXM microscope.
        # In the ALBA-BL09 case all the values will be set to 1.
        monitor_size = self.nSampleFrames + self.nFramesBright
        monitor_counts = np.ones(monitor_size, dtype=np.uint16)
        self.nxmonitor['data'] = monitor_counts

        # Flush and close the nexus file
        self.txrmhdf.flush()
        self.txrmhdf.close()


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
        # TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_distance()

    def get_sample_id(self):
        filename = self.file_names[0]
        # TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_sample_id()

    def get_xray_magnification(self):
        filename = self.file_names[0]
        # TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.get_xray_magnification()

    def get_data_type(self):
        filename = self.file_names[0]
        # TODO: get the data from the first file
        with XradiaFile(filename) as xrm_file:
            return xrm_file.data_type

    def get_image_size(self):
        filename = self.file_names[0]
        # TODO: get the data from the first file
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
