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


import argparse
import os


def main():

    # Storage of current directory: initial path before executing the script.
    intitialpath = os.getcwd()

    parser = argparse.ArgumentParser(description='Automate the process of '
                                                 'converting from mosaic XRM '
                                                 'to PseudoNeXus-HDF5.')
    parser.add_argument('-f',
                        '--folder',
                        type=str,
                        default=os.getcwd(),
                        help="Indicates the folder address where the "
                             "subfolders 'mosaic', 'mosaic1', 'mosaic2' "
                             "and so on, are located.")

    args = parser.parse_args()
    general_folder = args.folder

    mosaic2nexus_program_name = 'mosaic2nexus'

    for folder in os.listdir(general_folder):
             
        specific_folder=os.path.join(general_folder, folder)

        # Checking if the subfolder is a subfolder of mosaics.
        if os.path.isdir(specific_folder) and ('mosaic' in folder):
            os.chdir(specific_folder)
            print('Converting mosaics from folder ' + folder)

            for files in os.listdir("."):
                if files.endswith(".xrm") and ('mosaic' in files):
                    mosaic_xrm_file = files
                    print('Converting file: ' + files)
                    mosaic_xrm_file_without_extension = os.path.splitext(
                        mosaic_xrm_file)[0]
                    output_file = mosaic_xrm_file_without_extension+'.hdf5'
                    call_txrm2nexus = mosaic2nexus_program_name + ' ' + \
                                      mosaic_xrm_file + ' ' + output_file
                    os.system(call_txrm2nexus)

            os.chdir(general_folder)

    # Return to initial path, the one that we had before executing the script.
    os.chdir(intitialpath)

if __name__ == "__main__":
    main()


