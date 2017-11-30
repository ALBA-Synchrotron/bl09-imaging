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
import h5py
import numpy as np
from txm2nexuslib.xrmnex import XradiaFile


class Xrm2H5Converter(object):

    def __init__(self, xrm_file_name, h5_filename=None):
        self.xrm_file_name = xrm_file_name
        if h5_filename is None:
            h5_filename = os.path.splitext(xrm_file_name)[0] + '.hdf5'
        self.h5_handler = h5py.File(h5_filename, 'w')
        self.metadata = {}
        self.data = {}
        self.full_data = {}

    def _convert_metadata_from_xrm_to_h5(self):

        with XradiaFile(self.xrm_file_name) as xrm_file:
            try:
                self.metadata['angle'] = xrm_file.get_angles()
                self.h5_handler.create_dataset(
                    "angle",
                    data=self.metadata['angle'])
                self.h5_handler["angle"].attrs["units"] = "degrees"
            except Exception:
                print("angle could not be converted from xrm to hdf5")

            try:
                self.metadata['energy'] = xrm_file.get_energies()[0]
                self.h5_handler.create_dataset(
                    "energy",
                    data=self.metadata['energy'])
                self.h5_handler["energy"].attrs["units"] = "eV"
            except Exception:
                print("energy could not be converted from xrm to hdf5")

            try:
                self.metadata['exposure_time'] = xrm_file.get_exp_times()[0]
                self.h5_handler.create_dataset(
                    "exposure_time",
                    data=self.metadata['exposure_time'])
                self.h5_handler["exposure_time"].attrs["units"] = "s"
            except Exception:
                print("exposure_time could not be converted from xrm to hdf5")

            try:
                self.metadata['machine_current'] = \
                    xrm_file.get_machine_currents()[0]
                self.h5_handler.create_dataset(
                    "machine_current",
                    data=self.metadata['machine_current'])
                self.h5_handler["machine_current"].attrs["units"] = "mA"
            except Exception:
                print("machine_current could not be converted from xrm to hdf5")

            try:
                self.metadata['pixel_size'] = xrm_file.pixel_size
                self.h5_handler.create_dataset(
                    "pixel_size",
                    data=self.metadata['pixel_size'])
                self.h5_handler["pixel_size"].attrs["units"] = "um"
            except Exception:
                print("pixel_size could not be converted from xrm to hdf5")

            try:
                self.metadata['magnification'] = \
                    xrm_file.get_xray_magnification()
                self.h5_handler.create_dataset(
                    "magnification",
                    data=self.metadata['magnification'])
            except Exception:
                print("magnification could not be converted from xrm to hdf5")

            try:
                self.metadata['image_width'] = xrm_file.get_image_width()
                self.h5_handler.create_dataset(
                    "image_width",
                    data=self.metadata['image_width'])
                self.h5_handler["image_width"].attrs["units"] = "pixels"
            except Exception:
                print("image_width could not be converted from xrm to hdf5")

            try:
                self.metadata['image_height'] = xrm_file.get_image_height()
                self.h5_handler.create_dataset(
                    "image_height",
                    data=self.metadata['image_height'])
                self.h5_handler["image_height"].attrs["units"] = "pixels"
            except Exception:
                print("image_height could not be converted from xrm to hdf5")

            try:
                self.metadata['x_position'] = xrm_file.get_x_positions()[0]
                self.h5_handler.create_dataset(
                    "x_position",
                    data=self.metadata['x_position'])
                self.h5_handler["x_position"].attrs["units"] = "um"
            except Exception:
                print("x_position could not be converted from xrm to hdf5")

            try:
                self.metadata['y_position'] = xrm_file.get_y_positions()[0]
                self.h5_handler.create_dataset(
                    "y_position",
                    data=self.metadata['y_position'])
                self.h5_handler["y_position"].attrs["units"] = "um"
            except Exception:
                print("y_position could not be converted from xrm to hdf5")

            try:
                self.metadata['z_position'] = xrm_file.get_z_positions()[0]
                self.h5_handler.create_dataset(
                    "z_position",
                    data=self.metadata['z_position'])
                self.h5_handler["z_position"].attrs["units"] = "um"
            except Exception:
                print("z_position could not be converted from xrm to hdf5")

            try:
                self.metadata['data_type'] = xrm_file.data_type
                self.h5_handler.create_dataset(
                    "data_type",
                    data=self.metadata['data_type'])
            except Exception:
                print("data_type could not be converted from xrm to hdf5")

            try:
                self.metadata['date'] = self.xrm_file_name.split('_')[0]
                self.metadata['date'] = int(self.metadata['date'])
                self.h5_handler.create_dataset(
                    "date",
                    data=self.metadata['date'])
            except Exception:
                print("date could not be converted from xrm to hdf5")

            try:
                self.metadata['sample_name'] = self.xrm_file_name.split('_')[1]
                self.h5_handler.create_dataset(
                    "sample_name",
                    data=self.metadata['sample_name'])
            except Exception:
                print("sample_name could not be converted from xrm to hdf5")

            try:
                if ('_FF' in self.xrm_file_name or
                        '_ff_' in self.xrm_file_name):
                    self.metadata['FF'] = True
                    self.h5_handler.create_dataset("FF",
                                                   data=self.metadata['FF'])
                else:
                    self.metadata['FF'] = False
                    self.h5_handler.create_dataset("FF",
                                                   data=self.metadata['FF'])
            except Exception:
                print("FF information could not be retrieved")

        return self.metadata

    def _convert_raw_image_from_xrm_to_h5(self):
        with XradiaFile(self.xrm_file_name) as self.xrm_file:
            try:
                self.data['data'] = self.xrm_file.get_image_2D()
                self.h5_handler.create_dataset(
                    "data",
                    data=self.data['data'])
            except Exception:
                print("image raw data could not be converted from xrm to hdf5")

    def convert_xrm_to_h5_file(self):
        self._convert_metadata_from_xrm_to_h5()
        self._convert_raw_image_from_xrm_to_h5()
        self.h5_handler.flush()
        self.h5_handler.close()
