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

import h5py
import numpy as np

def extract_single_image_from_hdf5(single_image_hdf5_file):
    f = h5py.File(single_image_hdf5_file, "r")
    image = f["data"]
    return image

def add_images(image_list):
    shape = np.shape(image_list[0])
    result_image = np.zeros(shape)
    for image in image_list:
        result_image = result_image + image
    return result_image


def main():
    ars = np.array([[2, 3], [4, 5]])
    brs = np.array([[5, 1], [2, 1]])
    resulting_image = add_images([ars, brs])
    print(resulting_image)

if __name__ == "__main__":
    main()
