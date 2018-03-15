#!/usr/bin/python

"""
(C) Copyright 2017 ALBA-CELLS
Authors: Marc Rosanes, Carlos Falcon, Zbigniew Reszela, Carlos Pascual
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
import sys
import h5py
import numpy as np
from txm2nexuslib.xrmnex import XradiaFile


class Xrm2H5Converter(object):

    def __init__(self, xrm_filename, h5_filename=None):
        self.xrm_filename = xrm_filename
        self.h5_filename = h5_filename
        if h5_filename is None:
            self.h5_filename = os.path.splitext(xrm_filename)[0] + '.hdf5'
        self.h5_handler = h5py.File(self.h5_filename, 'w')
        self.metadata_h5 = self.h5_handler.create_group("metadata")
        self.metadata = {}
        self.data = {}
        self.full_data = {}

    def _convert_metadata_from_xrm_to_h5(self):

        with XradiaFile(self.xrm_filename) as xrm_file:
            try:
                self.metadata['angle'] = xrm_file.get_angles()[0]
                self.metadata_h5.create_dataset(
                    "angle",
                    data=self.metadata['angle'])
                self.metadata_h5["angle"].attrs["units"] = "degrees"
            except Exception:
                print("angle could not be converted from xrm to hdf5")

            try:
                self.metadata['energy'] = xrm_file.get_energies()[0]
                self.metadata_h5.create_dataset(
                    "energy",
                    data=self.metadata['energy'])
                self.metadata_h5["energy"].attrs["units"] = "eV"
            except Exception:
                print("energy could not be converted from xrm to hdf5")

            try:
                self.metadata['exposure_time'] = xrm_file.get_exp_times()[0]
                self.metadata_h5.create_dataset(
                    "exposure_time",
                    data=self.metadata['exposure_time'])
                self.metadata_h5["exposure_time"].attrs["units"] = "s"
            except Exception:
                print("exposure_time could not be converted from xrm to hdf5")

            try:
                self.metadata['machine_current'] = \
                    xrm_file.get_machine_currents()[0]
                self.metadata_h5.create_dataset(
                    "machine_current",
                    data=self.metadata['machine_current'])
                self.metadata_h5["machine_current"].attrs["units"] = "mA"
            except Exception:
                print("machine_current could not be "
                      "converted from xrm to hdf5")

            try:
                self.metadata['pixel_size'] = xrm_file.pixel_size
                self.metadata_h5.create_dataset(
                    "pixel_size",
                    data=self.metadata['pixel_size'])
                self.metadata_h5["pixel_size"].attrs["units"] = "um"
            except Exception:
                print("pixel_size could not be converted from xrm to hdf5")

            try:
                self.metadata['magnification'] = \
                    xrm_file.get_xray_magnification()
                self.metadata_h5.create_dataset(
                    "magnification",
                    data=self.metadata['magnification'])
            except Exception:
                print("magnification could not be converted from xrm to hdf5")

            try:
                self.metadata['image_width'] = xrm_file.get_image_width()
                self.metadata_h5.create_dataset(
                    "image_width",
                    data=self.metadata['image_width'])
                self.metadata_h5["image_width"].attrs["units"] = "pixels"
            except Exception:
                print("image_width could not be converted from xrm to hdf5")

            try:
                self.metadata['image_height'] = xrm_file.get_image_height()
                self.metadata_h5.create_dataset(
                    "image_height",
                    data=self.metadata['image_height'])
                self.metadata_h5["image_height"].attrs["units"] = "pixels"
            except Exception:
                print("image_height could not be converted from xrm to hdf5")

            try:
                self.metadata['x_position'] = xrm_file.get_x_positions()[0]
                self.metadata_h5.create_dataset(
                    "x_position",
                    data=self.metadata['x_position'])
                self.metadata_h5["x_position"].attrs["units"] = "um"
            except Exception:
                print("x_position could not be converted from xrm to hdf5")

            try:
                self.metadata['y_position'] = xrm_file.get_y_positions()[0]
                self.metadata_h5.create_dataset(
                    "y_position",
                    data=self.metadata['y_position'])
                self.metadata_h5["y_position"].attrs["units"] = "um"
            except Exception:
                print("y_position could not be converted from xrm to hdf5")

            try:
                self.metadata['z_position'] = xrm_file.get_z_positions()[0]
                self.metadata_h5.create_dataset(
                    "z_position",
                    data=self.metadata['z_position'])
                self.metadata_h5["z_position"].attrs["units"] = "um"
            except Exception:
                print("z_position could not be converted from xrm to hdf5")

            try:
                self.metadata['data_type'] = xrm_file.data_type
                self.metadata_h5.create_dataset(
                    "data_type",
                    data=self.metadata['data_type'])
            except Exception:
                print("data_type could not be converted from xrm to hdf5")

            try:
                self.metadata['sample_name'] = self.xrm_filename.split('_')[1]
                self.metadata_h5.create_dataset(
                    "sample_name",
                    data=self.metadata['sample_name'])
            except Exception:
                print("sample_name could not be converted from xrm to hdf5")

            try:
                if ('_FF' in self.xrm_filename or
                        '_ff_' in self.xrm_filename):
                    self.metadata['FF'] = True
                    self.metadata_h5.create_dataset("FF",
                                                   data=self.metadata['FF'])
                else:
                    self.metadata['FF'] = False
                    self.metadata_h5.create_dataset("FF",
                                                   data=self.metadata['FF'])
            except Exception:
                print("FF information could not be retrieved")

            # Get acquisition time
            try:
                self.metadata['date_time'] = xrm_file.get_single_date()
                self.metadata_h5.create_dataset(
                    "date_time_acquisition", data=self.metadata['date_time'])
            except Exception:
                print("acquisition date and time could not be converted "
                      "from xrm to hdf5")

            # Instrument and Source
            self.metadata['instrument'] = "BL09 @ ALBA"
            self.metadata_h5.create_dataset("instrument",
                                           data=self.metadata['instrument'])
            self.metadata['source'] = "ALBA"
            self.metadata_h5.create_dataset("source",
                                           data=self.metadata['source'])
            self.metadata['source_probe'] = "X-Ray"
            self.metadata_h5.create_dataset("source_probe",
                                           data=self.metadata['source_probe'])
            self.metadata['source_type'] = "Sychrotron X-Ray Source"

            # Applied program and command to convert the data
            self.metadata_h5.create_dataset("source_type",
                                           data=self.metadata['source_type'])
            self.metadata['program_name'] = "xrm2h5"
            self.metadata_h5.create_dataset("program_name",
                                           data=self.metadata['program_name'])
            command = (self.metadata['program_name'] + ' ' +
                       ' '.join(sys.argv[1:]))
            self.metadata['command'] = command
            self.metadata_h5.create_dataset("command",
                                           data=self.metadata['command'])

            # Input and output files
            self.metadata['input_file'] = os.path.basename(self.xrm_filename)
            self.metadata_h5.create_dataset("input_file",
                                           data=self.metadata['input_file'])
            self.metadata['output_file'] = os.path.basename(self.h5_filename)
            self.metadata_h5.create_dataset("output_file",
                                           data=self.metadata['output_file'])
        return self.metadata

    def _convert_raw_image_from_xrm_to_h5(self):
        with XradiaFile(self.xrm_filename) as self.xrm_file:
            try:
                self.data['data'] = self.xrm_file.get_image_2D()
                self.h5_handler.create_dataset(
                    "data_1",
                    dtype=np.uint16,
                    data=self.data['data'])
                workflow_step = 1
                dataset = "data_" + str(workflow_step)
                self.h5_handler[dataset].attrs["step"] = workflow_step
                self.h5_handler[dataset].attrs["dataset"] = dataset
                self.h5_handler[dataset].attrs["description"] = "raw data"
                self.h5_handler["data"] = h5py.SoftLink(dataset)
            except Exception:
                print("image raw data could not be converted from xrm to hdf5")
        return self.data

    def convert_xrm_to_h5_file(self):
        self._convert_metadata_from_xrm_to_h5()
        self._convert_raw_image_from_xrm_to_h5()
        self.full_data["metadata"] = self.metadata
        self.full_data["data"] = self.data
        self.h5_handler.flush()
        self.h5_handler.close()
