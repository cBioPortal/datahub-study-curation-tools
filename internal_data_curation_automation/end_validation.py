#!/usr/bin/env python3

# Copyright (c) 2023 Memorial Sloan Kettering Cancer Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import logging
import click

# set logger
logfilename = 'subset.log'
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler(logfilename)
file_handler.setFormatter(formatter)
logger = logging.getLogger('subset')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

def remove_additional_meta_files(input_directory):
    files_list = os.listdir(input_directory)
    for file in files_list:
        if file.startswith('meta_'):
            with open(os.path.join(input_directory,file), 'r') as metafile:
                for line in metafile:
                    if line.startswith('data_filename'):
                        line = line.replace(' ','').strip('\n').split(':',1)
                        if line[1] and line[1] not in files_list:
                            logger.info("removing file '" + os.path.join(input_directory,file) +"' as there is no associated data file detected")
                            os.remove(os.path.join(input_directory,file))

def remove_additional_case_lists(input_directory):
    files_list = os.listdir(input_directory)
    for file in files_list:
        if 'case_lists' in file:
            caselist_files = os.listdir(os.path.join(input_directory,'case_lists'))
            for cl in caselist_files:
                with open(os.path.join(input_directory,'case_lists',cl), 'r') as cl_data:
                    for line in cl_data:
                        if line.startswith('case_list_ids'):
                            line = line.strip('\n').split(':')
                            if line[1]:
                                line[1] = line[1].replace(' ','')
                                if line[1] == '':
                                    logger.info("removing file '"+ os.path.join(input_directory,'case_lists',cl) + "' as there is no associated data detected")
                                    os.remove(os.path.join(input_directory,'case_lists',cl))

def cna_stable_id_check(input_directory):
    files_list = os.listdir(input_directory)
    if 'data_gene_panel_matrix.txt' in files_list and 'meta_cna.txt' in files_list:
        cna_stable_id = str()
        with open(os.path.join(input_directory,'meta_cna.txt'), 'r') as cna_file:
            for line in cna_file:
                if line.startswith('stable_id'):
                    cna_stable_id = line.replace(' ','').strip('\n').split(':',1)[1]

        new_matrix_header = ""
        data = ""
        update_file = False
        with open(os.path.join(input_directory,'data_gene_panel_matrix.txt'), 'r') as matrix_file:
            matrix_header = matrix_file.readline()
            if cna_stable_id not in matrix_header:
                if 'cna' in matrix_header or 'gistic' in matrix_header:
                    update_file = True
                    if cna_stable_id == 'cna': other_stable_id = 'gistic'
                    elif cna_stable_id == 'gistic': other_stable_id = 'cna'
                    new_matrix_header = matrix_header.replace(other_stable_id, cna_stable_id)
            for line in matrix_file:
                data += line
        if update_file:
            os.remove(os.path.join(input_directory,'data_gene_panel_matrix.txt'))
            with open(os.path.join(input_directory,'data_gene_panel_matrix.txt'), 'w') as meta:
                meta.write(new_matrix_header)
                meta.write(data)

@click.command()
@click.option('-i', '--input-directory', required = True, help = 'input study directory to validating')

def main(input_directory):
    # Remove meta files with missing data files - happens when the subset samples are not in data files, and meta files are copied over.
    remove_additional_meta_files(input_directory)

    # Remove any extra case lists - case lists are copied over from parent directory but may not contain any samples from the subset list
    remove_additional_case_lists(input_directory)

    # Check if the copy number stable id in meta and matrix file are the same else update it to the meta stable id
    # Sometimes the matrix file can contain 'gistic' and meta file 'cna'. this fails import.
    cna_stable_id_check(input_directory)

if __name__ == '__main__':
    main()