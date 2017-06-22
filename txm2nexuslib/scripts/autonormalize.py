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

    parser = argparse.ArgumentParser(
        description='Automate the process of normalizing the tomographies \n '
                    'The tomography and the FF are extracted from an input '
                    'HDF5 file.')
    parser.add_argument('-f',
                        '--folder',
                        type=str,
                        default=os.getcwd(),
                        help="Indicates the folder adress where the "
                             "subfolders 'tomo1' 'tomo2' and so on, "
                             "are located.")

    args = parser.parse_args()
    general_folder = args.folder

    normalize_program_name = 'normalize'

    for folder in os.listdir(general_folder):
             
        specific_folder=os.path.join(general_folder, folder)
        # Checking if the subfolder is a subfolder of tomos.
        if os.path.isdir(specific_folder) and \
                (('tomo' in folder) or ('TOMO' in folder)):

            tomo_hdf5_file='None'
            os.chdir(specific_folder)
            print('Converting tomos from folder '+ folder)

            for file_in_folder in os.listdir("."):
                if (file_in_folder.endswith(".hdf5") and
                        ('norm' not in file_in_folder) and
                        ('crop' not in file_in_folder)):
                    tomo_hdf5_file = file_in_folder
            
                if (tomo_hdf5_file != 'None' and
                        ('norm' not in file_in_folder) and
                        ('crop' not in file_in_folder)):
                    call_normalize = normalize_program_name + ' ' + \
                                     tomo_hdf5_file
                    os.system(call_normalize)
            os.chdir(general_folder)

    # Return to initial path, the one that we had before executing the script.
    os.chdir(intitialpath)


if __name__ == "__main__":
    main()
