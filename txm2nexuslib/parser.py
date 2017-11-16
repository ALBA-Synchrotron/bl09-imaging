#!/usr/bin/python

"""
(C) Copyright 2017 - ALBA CELLS - CTGENSOFT
Author Marc Rosanes
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
import copy
import pprint
from shutil import copyfile
from glob import glob
from tinydb import TinyDB


class ParserTXMScript(object):

    def __init__(self):
        self.collected_files = []
        self.parameters = {}
        self.filename = None
        self.extension = None        
        self.date = None
        self.sample = "sample0"
        self.energy = -1
        self.angle = -1000
        self.zpz = -1
        self.FF = False
        self.repetition = 0
        self.first_repetition = True
        self.subfolder = None
        
    def reset_repetition(self):
        self.first_repetition = True
        self.repetition = 0    
    
    def parse_energy(self, line):
        # If a parameter is modified, the repetitions must be reset
        self.reset_repetition()
        word_list = line.split()
        self.energy = round(float(word_list[-1]), 1)
        self.parameters['energy'] = self.energy
                
    def parse_angle(self, line):
        # If a parameter is modified, the repetitions must be reset
        self.reset_repetition()
        word_list = line.split()
        self.angle = round(float(word_list[-1]), 1)
        self.parameters['angle'] = self.angle
        
    def parse_zpz(self, line):
        # If a parameter is modified, the repetitions must be reset
        self.reset_repetition()
        word_list = line.split()
        self.zpz = round(float(word_list[-1]), 1)
        self.parameters['zpz'] = self.zpz

    def parse_subfolder(self, line):
        """Subfolder where the raw data file should be located"""
        # The repetition must not be reset in this case
        word_list = line.split()
        self.subfolder = word_list[-1]
        self.parameters['subfolder'] = self.subfolder
        
    def is_FF(self):
        if "_FF" in self.filename:
            # If a parameter is modified, the repetitions must be reset
            if not self.FF:
                self.reset_repetition()
            self.FF = True
            self.parameters['FF'] = self.FF
        else:
            # If a parameter is modified, the repetitions must be reset
            if self.FF:
                self.reset_repetition()
            self.FF = False
            self.parameters['FF'] = self.FF
        
    def parse_sample_and_date(self):
        try:
            date_str = self.filename.split('_')[0]
            new_date = int(date_str)
            # If a parameter is modified, the repetitions must be reset
            if new_date != self.date:
                self.first_repetition = True
            self.date = new_date
            if (len(date_str) == 4 or 
                len(date_str) == 6 or 
                len(date_str) == 8):
                self.parameters['date'] = self.date
                new_sample = self.filename.split('_')[1]
                # If a parameter is modified, the repetitions must be reset
                if new_sample != self.sample:
                    self.first_repetition = True
                self.sample = new_sample                    
            else:
                new_sample = self.filename.split('_')[0]
                # If a parameter is modified, the repetitions must be reset
                if new_sample != self.sample:
                    self.first_repetition = True
                self.sample = new_sample
        except:
            self.parameters.pop('date', None)
            self.sample = self.filename.split('_')[0]
        self.parameters['sample'] = self.sample
        
    def parse_extension(self):
        self.extension = os.path.splitext(self.filename)[1]
        self.parameters['extension'] = self.extension        
        
    def parse_collect(self, line):
        if not self.first_repetition:
            self.repetition += 1
        self.parameters['repetition'] = self.repetition

        word_list = line.split()
        self.filename = word_list[-1]
        self.parameters['filename'] = self.filename
        self.first_repetition = False
        
        self.is_FF()
        self.parse_extension()
        self.parse_sample_and_date()

        store_parameters = copy.deepcopy(self.parameters)
        self.collected_files.append(store_parameters)

    def parse_script(self, txm_txt_script):
        f = open(txm_txt_script, 'r')
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "moveto energy" in line:
                self.parse_energy(line)
            if "moveto T" in line:
                self.parse_angle(line)
            if "moveto ZPz" in line:
                self.parse_zpz(line)
            if "moveto folder" in line:
                self.parse_subfolder(line)
            if "collect" in line:
                self.parse_collect(line)    
        return self.collected_files
                

def _getDB(db_full_path, txm_txt_script, use_existing_db=True):
    if os.path.isfile(db_full_path) and use_existing_db:
        print("\nUsing existing files db\n")
        db = TinyDB(db_full_path)
    else:
        print("\nCreating files db\n")
        db = TinyDB(db_full_path)
        db.purge()
        parser = ParserTXMScript()
        collected_images = parser.parse_script(txm_txt_script)
        db.insert_multiple(collected_images)
        
    return db


def _get_paths_from_root(root_path, query_output):
    """ Get the paths of the queried files by looking in the root folder and
    all subfolders inside the root folder containing the data files"""
    files = []
    print(root_path)
    for entry in query_output:
        for dir,_,_ in os.walk(root_path):
            files.extend(glob(os.path.join(dir, entry["filename"])))
        # Add fake files    
        #if len(files) == 0 or entry["filename"] in files[-1]:
        #    files.append(os.path.join(root_path, entry["filename"]))
    return files


def _get_paths_from_subfolders(root_path, query_output):
    """ Get the paths of the queried files by looking in the subfolders
    indicated by the query"""
    files = []
    try:
        for entry in query_output:
            filename = entry["filename"]
            subfolder = entry["subfolder"]
            complete_file = os.path.join(root_path, subfolder, filename)
            files.append(complete_file)
    except:
        print("WARNING: Subfolders are not specified in txt TXM script: "
              "they should be specified. \n" 
              "Fallback: Performing generic search in the root folder.\n")
        files = _get_paths_from_root(root_path, query_output)
    return files


def move_txm_script_to_root(txm_txt_script, root_path):
    # Copy txm_txt_script to root_path and return the absolute
    # path + filename"""
    try:
        #root_path is the super folder where raw data xrm files are located.
        #TXM txt script should be located there."""
        fname_txm_script = os.path.basename(txm_txt_script)
        dst = os.path.join(root_path, fname_txm_script)
        copyfile(txm_txt_script, dst)
        txm_script_basename = os.path.basename(txm_txt_script)
        txm_txt_script = os.path.join(root_path, txm_script_basename)
        return txm_txt_script
    except:
        raise Exception("File txt already exists in root path")


def search(txm_txt_script, query_impl, db_name='index.json',
           use_existing_db=True, orderby=None):
    """Perform a query and return the query output"""

    root_path = os.path.dirname(os.path.abspath(txm_txt_script))
    if not os.path.isfile(txm_txt_script):
        raise Exception('TXM txt script does not '
                        'exist in {0}'.format(root_path))

    db_full_path = os.path.join(root_path, db_name)    
    db = _getDB(db_full_path, txm_txt_script, use_existing_db=use_existing_db)
    query_output = db.search(query_impl)    
    db.close()
    
    # TODO orderby
    return query_output


def move_txm_script_and_search(txm_txt_script, query_impl, root_path=None,
                               db_name='index.json', use_existing_db=True,
                               orderby=None):
    if root_path:
        move_txm_script_to_root(txm_txt_script, root_path)
    else:
        root_path = os.path.dirname(os.path.abspath(txm_txt_script))

    query_output = search(txm_txt_script, query_impl, db_name=db_name,
                          orderby=orderby, use_existing_db=use_existing_db)
    return query_output


def get_file_paths(query_output, root_path, use_subfolders=True,
                   only_existing_files=True):
    """Perform a query and return the query and get the paths of the files
    returned by the query"""

    # Get getFilePaths
    if use_subfolders:
        files = _get_paths_from_subfolders(root_path, query_output)
    else:
        files = _get_paths_from_root(root_path, query_output)

    # Filter existing files
    if only_existing_files:
        files = filter(os.path.isfile, files)

    return files


def move_search_and_get_file_paths(txm_txt_script, query_impl, root_path=None,
                                   db_name='index.json', use_existing_db=True,
                                   only_existing_files=True, orderby=None):
    if root_path:
        move_txm_script_to_root(txm_txt_script, root_path)
    else:
        root_path = os.path.dirname(os.path.abspath(txm_txt_script))
    query_output = search(txm_txt_script, query_impl, db_name=db_name,
                          orderby=orderby, use_existing_db=use_existing_db)
    files = get_file_paths(query_output, root_path, use_subfolders=True,
                           only_existing_files=only_existing_files)
    return files



def main():

    parser = ParserTXMScript()
    collected_images = parser.parse_script("many_folder.txt")
    pretty_printer = pprint.PrettyPrinter(indent=4)
    pretty_printer.pprint(collected_images)


if __name__ == "__main__":
    main()
