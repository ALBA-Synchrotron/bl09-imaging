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
from shutil import copy2
from glob import glob
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware


class ParserTXMScript(object):

    def __init__(self):
        self.collected_files = []
        self.parameters = {}
        self.filename = None
        self.extension = None
        self.previous_date = 10002323
        self.date = 10002424
        self.previous_sample = "PreviousDefaultSamplE"
        self.sample = "DefaultSamplE"
        self.previous_energy = -100
        self.energy = -10
        self.previous_angle = -1111
        self.angle = -1000
        self.previous_zpz = 88888888
        self.zpz = 99999999
        self.previous_jj_u = -8888888
        self.jj_u = -9999999
        self.previous_jj_d = -8888888
        self.jj_d = -9999999
        self.previous_FF = False
        self.FF = False
        self.repetition = 0
        self.subfolder = None

    def parse_energy(self, line):
        word_list = line.split()
        self.energy = round(float(word_list[-1]), 1)
        self.parameters['energy'] = self.energy
                
    def parse_angle(self, line):
        word_list = line.split()
        self.angle = round(float(word_list[-1]), 1)
        self.parameters['angle'] = self.angle
        
    def parse_zpz(self, line):
        word_list = line.split()
        self.zpz = round(float(word_list[-1]), 1)
        self.parameters['zpz'] = self.zpz

    def parse_jj_u(self, line):
        word_list = line.split()
        self.jj_u = round(float(word_list[-1]), 1)
        self.parameters['jj_u'] = self.jj_u

    def parse_jj_d(self, line):
        word_list = line.split()
        self.jj_d = round(float(word_list[-1]), 1)
        self.parameters['jj_d'] = self.jj_d

    def parse_subfolder(self, line):
        """Subfolder where the raw data file should be located"""
        word_list = line.split()
        self.subfolder = str(int(round(float(word_list[-1]))))
        self.parameters['subfolder'] = self.subfolder
        
    def is_FF(self):
        if "_FF" in self.filename:
            self.FF = True
            self.parameters['FF'] = self.FF
        else:
            self.FF = False
            self.parameters['FF'] = self.FF
        
    def parse_sample_and_date(self):
        try:
            date_str = self.filename.split('_')[0]
            new_date = int(date_str)
            if (len(date_str) == 4 or len(date_str) == 6 or
                len(date_str) == 8):
                self.date = new_date
                self.parameters['date'] = self.date
                self.sample = self.filename.split('_')[1]
            else:
                self.sample = self.filename.split('_')[0]
        except:
            self.parameters.pop('date', None)
            self.sample = self.filename.split('_')[0]
        self.parameters['sample'] = self.sample
        
    def parse_extension(self):
        self.extension = os.path.splitext(self.filename)[1]
        self.parameters['extension'] = self.extension        
        
    def parse_collect(self, line):

        word_list = line.split()
        self.filename = word_list[-1]
        self.parameters['filename'] = self.filename

        self.is_FF()
        self.parse_extension()
        self.parse_sample_and_date()

        if (self.date == self.previous_date and
            self.sample == self.previous_sample and
            self.energy == self.previous_energy and
            self.angle == self.previous_angle and
            self.zpz == self.previous_zpz and
            self.jj_d == self.previous_jj_d and
            self.jj_u == self.previous_jj_u and
            self.zpz == self.previous_zpz and
            self.FF == self.previous_FF):
            self.repetition += 1
        else:
            self.repetition = 0
        self.parameters['repetition'] = self.repetition
        self.previous_date = self.date
        self.previous_sample = self.sample
        self.previous_energy = self.energy
        self.previous_angle = self.angle
        self.previous_zpz = self.zpz
        self.previous_jj_d = self.jj_d
        self.previous_jj_u = self.jj_u
        self.previous_FF = self.FF
        self.parameters['processed'] = False

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
            if "moveto phx" in line:
                self.parse_jj_u(line)
            if "moveto phy" in line:
                self.parse_jj_d(line)
            if "collect" in line:
                self.parse_collect(line)    
        return self.collected_files


def get_db_path(txm_txt_script):
    txm_file_dir = os.path.dirname(os.path.abspath(txm_txt_script))
    return os.path.join(txm_file_dir, "index.json")

def create_db(txm_txt_script):
    db = get_db(txm_txt_script)
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(db.all())
    db.close()

def get_db(txm_txt_script, use_existing_db=False):
    """Get the data files DataBase if exisiting, or create the DataBase
    if not existing yet or if the creation is specified explicitely"""

    if not os.path.isfile(txm_txt_script):
        raise Exception('TXM txt script does not exist')

    # root_path: folder in which raw data files are organized in subfolders.
    root_path = os.path.dirname(os.path.abspath(txm_txt_script))

    db_name = 'index.json'
    db_full_path = os.path.join(root_path, db_name)
    if os.path.isfile(db_full_path) and use_existing_db:
        print("\nUsing existing files DataBase\n")
        db = TinyDB(db_full_path, storage=CachingMiddleware(JSONStorage))
    else:
        print("\nCreating files DataBase\n")
        db = TinyDB(db_full_path, storage=CachingMiddleware(JSONStorage))
        db.purge()
        parser = ParserTXMScript()
        collected_images = parser.parse_script(txm_txt_script)
        db.insert_multiple(collected_images)
    return db


def _get_paths_from_root(root_path, query_output):
    """ Get the paths of the queried files by looking in the root folder and
    all subfolders inside the root folder containing the data files"""
    files = []
    for entry in query_output:
        for dir,_,_ in os.walk(root_path):
            files.extend(glob(os.path.join(dir, entry["filename"])))
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
        print("Subfolders have been used\n")
    except:
        # print("Performing generic search in the root folder\n")
        files = _get_paths_from_root(root_path, query_output)
    return files


def get_file_paths(query_output, root_path, use_subfolders=True,
                   only_existing_files=True):
    """Perform a query and return the query and get the paths of the files
    returned by the query"""

    # Get getFilePaths
    if use_subfolders:
        files = _get_paths_from_subfolders(root_path, query_output)
        # Filter existing files
        if only_existing_files:
            files = list(filter(os.path.isfile, files))
    else:
        files = _get_paths_from_root(root_path, query_output)

    return files


def search_and_get_file_paths(txm_txt_script, query_impl,
                              use_subfolders=True, only_existing_files=True, 
                              use_existing_db=False):
    root_path = os.path.dirname(os.path.abspath(txm_txt_script))
    db = get_db(txm_txt_script, use_existing_db=use_existing_db)
    query_output = db.search(query_impl)
    files = get_file_paths(query_output, root_path, 
                           use_subfolders=use_subfolders,
                           only_existing_files=only_existing_files)
    db.close()
    return files



def main():

    parser = ParserTXMScript()
    collected_images = parser.parse_script("many_folder.txt")
    pretty_printer = pprint.PrettyPrinter(indent=4)
    pretty_printer.pprint(collected_images)


if __name__ == "__main__":
    main()
