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

import click
import pandas as pd
import os
import logging

# set logger
logfilename = 'subset.log'
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler(logfilename)
file_handler.setFormatter(formatter)
logger = logging.getLogger('subset')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Globals
meta_datatypes_file = 'config_files/meta_datatypes.txt'
datatype_df = pd.read_csv(meta_datatypes_file, sep="\t")

metadata = ['type_of_cancer: mixed\n'
'name: Mixed Cancers (MSK, 2023)\n'
'description:  Targeted Sequencing of tumors and their matched normals via MSK-IMPACT\n']

cols = ["DATA_FILENAME", "META_GENERIC_ASSAY_TYPE", "META_GENERIC_ENTITY_meta_PROPERTIES",
       'META_STABLE_ID', 'META_GENETIC_ALTERATION_TYPE', 'META_DATATYPE',
       'META_SHOW_PROFILE_IN_ANALYSIS_TAB', 'META_PROFILE_NAME',
       'META_PROFILE_DESCRIPTION', 'META_REFERENCE_GENOME_ID']

@click.command()
@click.option('-d', '--directory', help="the folder that has all the study data files", required = True)
@click.option('-s', '--study_id', help="name of the cancer_study_identifier", required = True)

def main(directory, study_id):
    files_list = [f for f in os.listdir(directory) if f.startswith('data') or f.endswith('.seg')]

    for file in files_list:
        if file in datatype_df['DATA_FILENAME'].values:
            meta_filename = datatype_df.loc[datatype_df['DATA_FILENAME'] == file, 'META_FILENAME'].iloc[0]
            meta_filepath = directory+'/'+meta_filename
            emp = ""
            cc = datatype_df.loc[datatype_df['DATA_FILENAME'] == file]
            for col in cols:
                xx = list(cc[col])[-1]
                if str(xx) != "nan": # check if NAN values are present
                    ss = col.replace("META_", '').lower() # then Replacing Meta_ to ''
                    if file.endswith('.seg') and ss == 'profile_description': ss = 'description'
                    append_string = f"{ss}: {xx}\n"
                    emp += append_string  # appending to the empty string
                else:
                    pass

            if not os.path.exists(meta_filepath):
                logger.info("Generating the missing meta file: "+ meta_filename)
                with open(meta_filepath, 'w') as ff:
                    ff.writelines(f"cancer_study_identifier: {study_id}\n")
                    ff.writelines(emp)
            else:
                meta_dict = {x.split(':', 1)[0].strip(): x.split(':', 1)[1].strip() for x in emp.split('\n') if x != ''}
                file_dict = {}
                new_dict = dict()
                with open(meta_filepath, 'r') as ff:
                    for line in ff:
                        line = line.strip('\n').split(':',1)
                        if meta_filename == 'meta_cna.txt' and line[0].strip() == 'stable_id' and line[1].strip() not in ['cna','gistic']: new_dict[line[0].strip()] = line[1].strip().split('_')[-1]
                        elif meta_filename == 'meta_mutations.txt' and line[0].strip() == 'stable_id' and line[1].strip() not in ['mutations']: new_dict[line[0].strip()] = line[1].strip().split('_')[-1]
                        elif meta_filename == 'meta_sv.txt' and line[0].strip() == 'stable_id' and line[1].strip() not in ['structural_variants']: new_dict[line[0].strip()] = 'structural_variants'
                        elif line[1].strip() == '': continue
                        else: file_dict[line[0].strip()] = line[1].strip()
                    new_dict = {k: v for k, v in meta_dict.items() if k not in file_dict}
                    if 'cancer_study_identifier' not in file_dict: new_dict['cancer_study_identifier'] = study_id
                if len(new_dict) > 0:
                    file_dict.update(new_dict)
                    logger.info("Adding the missing metadata fields to "+ meta_filename)
                    with open(meta_filepath, 'w') as ff:
                        for k, v in file_dict.items():
                            line = k+': '+v+'\n'
                            ff.writelines(line)

    file_path = f"{directory}/meta_study.txt"
    if not os.path.exists(file_path):
        logger.info("Generating the missing meta file: meta_study.txt")
        with open(file_path, 'w') as meta_study:
            meta_study.writelines(f"cancer_study_identifier: {study_id}\n")
            for val in metadata: meta_study.write(val)

if __name__ == '__main__':
    main()