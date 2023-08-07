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

import sys
import os
import logging
import click
import split_data_clinical_attributes
import shutil

DATA_FILENAME_MAPPING_FILE = "config_files/data_file_mappings.txt"
CLINICAL_META_DATA = "config_files/clinical_attributes_metadata.txt"
CLINICAL_SAMPLE_PATTERN = 'data_clinical_sample.txt'
PATIENT_SAMPLE_MAP = {}
TEMP_FILES = []

NON_CASE_IDS = [
    'MIRNA',
    'LOCUS',
    'ID',
    'GENE SYMBOL',
    'ENTREZ_GENE_ID',
    'HUGO_SYMBOL',
    'LOCUS ID',
    'CYTOBAND',
    'COMPOSITE.ELEMENT.REF',
    'HYBRIDIZATION REF',
    'NAME',
    'URL',
    'DESCRIPTION',
    'ENTITY_STABLE_ID',
]

clinical_data_dictionary = dict()
merged_clinical_comments = dict()

# set logger
logfilename = 'subset.log'
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler(logfilename)
file_handler.setFormatter(formatter)
logger = logging.getLogger('subset')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

def generate_merge_map(prefix, files_map, merge_map, dir, filename, new_filename=None):
    matched = 'no'
    for key in files_map:
        if new_filename and new_filename in files_map[key][prefix]:
            out_filename = files_map[key][prefix].split(',')[-1].strip()
            if out_filename not in merge_map: merge_map[out_filename] = [os.path.join(dir,filename)]
            else: merge_map[out_filename].append(os.path.join(dir,filename))
            matched = 'yes'

        if filename in files_map[key][prefix]:
            out_filename = files_map[key][prefix].split(',')[-1].strip()
            if out_filename not in merge_map: merge_map[out_filename] = [os.path.join(dir,filename)]
            else: merge_map[out_filename].append(os.path.join(dir,filename))
            matched = 'yes'

    if filename == 'case_lists':
        case_files = os.listdir(os.path.join(dir,filename))
        for file in case_files:
            if file not in merge_map: merge_map[file] = [os.path.join(dir,filename,file)]
            else: merge_map[file].append(os.path.join(dir,filename,file))
            matched = 'yes'

    if matched == 'no':
        if filename in merge_map: merge_map[filename].append(os.path.join(dir,filename))
        else: merge_map[filename] = [os.path.join(dir,filename)]

def generate_clinical_metadata(metadata):
    with open(metadata, 'r') as metf:
        for line in metf:
            line = line.strip().split('\t')
            key = line[0]
            if key not in clinical_data_dictionary:
                line.pop(0)
                clinical_data_dictionary[key] = line

def generate_file_mapping(mapping_file, input_directory):
    files_map = dict()
    merge_map = dict()
    with open(mapping_file, "r") as infile:
        for line in infile:
            line = line.strip().split('\t')
            if line[0] not in files_map:
                files_map[line[0]] = {"data":line[1], "meta": line[2]}

    for dir in input_directory.split(','):
        files_list = os.listdir(dir.strip())
        for filename in files_list:
            if filename.startswith("data"):
                generate_merge_map("data", files_map, merge_map, dir, filename)
            elif filename.startswith("meta"):
                generate_merge_map("meta", files_map, merge_map, dir, filename)
            elif '_data_cna_hg19.seg' in filename:
                new_filename = "data_cna_hg19.seg"
                generate_merge_map("data", files_map, merge_map, dir, filename, new_filename)
            elif '_meta_cna_hg19_seg.txt' in filename:
                new_filename = "meta_cna_hg19_seg.txt"
                generate_merge_map("meta", files_map, merge_map, dir, filename, new_filename)
            elif filename.startswith('case_lists'):
                generate_merge_map("data", files_map, merge_map, dir, filename)
            else:
                continue
    return merge_map

def process_datum(val):
    """ Cleans up datum. """
    try:
        vfixed = val.strip()
    except AttributeError:
        vfixed = ''
    if vfixed in ['', 'NA', 'N/A', None]:
        return ''
    return vfixed

def get_header(filename):
    """ Gets the header from the file. """
    filedata = [x for x in open(filename).read().split('\n') if not x.startswith("#")]
    header = list(map(str.strip, filedata[0].split('\t')))
    return header

def update_patient_sample_map(patient_id, sample_id, reference_set, case_id_col):
    """ Updates PATIENT_SAMPLE_MAP. """
    mapped_patient_samples = PATIENT_SAMPLE_MAP.get(patient_id, set())
    mapped_patient_samples.add(sample_id)
    PATIENT_SAMPLE_MAP[patient_id] = mapped_patient_samples
    if case_id_col == 'PATIENT_ID' and len(reference_set) > 0:
        # add sample to reference set since we're subsetting or excluding by patient ids
        # this is to make sure the genomic data files get subsetted appropriately
        # since they are exclusively sample-based data files
        reference_set.add(sample_id)
    return reference_set

def load_patient_sample_mapping(data_filenames, reference_set, keep_match):
    """
        Loads patient - sample mapping from given clinical file(s).
    """
    logger.info('Loading patient - sample mapping from: ')
    # load patient sample mapping from each clinical file
    for filename in data_filenames:
        logger.info('\t' + filename)
        file_header = get_header(filename)
        data_file = open(filename, 'r')
        filedata = [line for line in data_file.readlines() if not line.startswith('#')][1:]

        for line in filedata:
            data = dict(zip(file_header, map(lambda x: process_datum(x), line.split('\t'))))
            # always update patient sample map if no reference list to check against
            # otherwise only update patient sample map if (1) we want to keep matches and a sample was found in reference list
            # or (2) we do not want to keep matches and sample was not found in reference list
            if len(reference_set) == 0:
                update_patient_sample_map(data['PATIENT_ID'], data['SAMPLE_ID'], reference_set, "")
            else:
                case_id_col = 'SAMPLE_ID'
                if data['PATIENT_ID'] != data['SAMPLE_ID'] and data['PATIENT_ID'] in reference_set:
                    case_id_col = 'PATIENT_ID'
                update_map = (keep_match == (data[case_id_col] in reference_set))
                if update_map:
                    update_patient_sample_map(data['PATIENT_ID'], data['SAMPLE_ID'], reference_set, case_id_col)
                else:
                    # need to exclude samples linked to patients if excluded reference set is by patient id
                    if not keep_match and case_id_col == 'PATIENT_ID':
                        reference_set.add(data['SAMPLE_ID'])
        data_file.close()
    logger.info('Finished loading patient - sample mapping!')
    return reference_set

def generate_patient_sample_mapping(merge_map, sublist, excluded_samples_list):

    # init reference list as empty or to either sublist or excluded_sample_list depending on which is being used
    reference_set = set()
    keep_match = True
    if len(sublist) > 0:
        reference_set = set(sublist[:])
    elif len(excluded_samples_list) > 0:
        reference_set = set(excluded_samples_list[:])
        keep_match = False

    # load patient sample mapping from data_clinical.txt or data_clinical_sample.txt files
    if CLINICAL_SAMPLE_PATTERN in merge_map.keys() and len(merge_map[CLINICAL_SAMPLE_PATTERN]) > 0:
        load_patient_sample_mapping(merge_map[CLINICAL_SAMPLE_PATTERN], reference_set, keep_match)

    if PATIENT_SAMPLE_MAP == {}:
        logger.error('generate_patient_sample_mapping(),  Did not load any patient sample mapping from clinical files')
        sys.exit(2)

    return reference_set,keep_match

def identify_file_type(file):
    header = get_header(file)
    header = [x.lower() for x in header]
    if 'sample_id' in header and 'patient_id' in header and 'timeline' in file:
        merge_style = 'normal'
    elif 'patient_id' in header and 'sample_id' not in header:
        merge_style = 'normal'
    elif 'sample_id' in header:
        merge_style = 'normal'
    elif 'sampleid' in header:
        merge_style = 'normal'
    elif 'tumor_sample_barcode' in header:
        merge_style = 'normal'
    elif 'id' in header and 'chrom' in header:
        merge_style = 'normal'
    elif ('hugo_symbol' in header or 'entrez_gene_id' in header) and 'tumor_sample_barcode' not in header:
        merge_style = 'profile'
    elif 'composite.element.ref' in header:
        merge_style = 'profile'
    elif 'entity_stable_id' in header:
        merge_style = 'profile'
    else:
        merge_style = None
    return merge_style

def get_comments(filename, header):
    """ Gets the comments from the file. """
    comments = [list(map(str.strip, x.split('\t'))) for x in open(filename).read().split('\n') if x.startswith("#")]
    merged_clinical_comments.update(dict(zip(header, list(list(zip(*comments))))))

def process_header(data_filenames, reference_set, keep_match, merge_style):
    """ Handles header merging, accumulating all column names """

    if merge_style == 'profile':
        header = []
        profile_header_data = {}
        for fname in data_filenames:
            non_case_ids = profile_header_data.get('non_case_ids', [])
            case_ids = profile_header_data.get('case_ids', [])

            for hdr in get_header(fname):
                # skip columns that are non case ids
                if hdr.upper() in NON_CASE_IDS:
                    if not hdr in non_case_ids:
                        non_case_ids.append(hdr)
                    continue
                # case_id already exists - should not be duplicated
                if hdr in case_ids:
                    continue
                # case_id does not pass keep_match test
                if len(reference_set) > 0:
                    if not (keep_match == (hdr in reference_set)):
                        continue
                # no reference set OR reference set passed keep_match test
                case_ids.append(hdr)
            # udpate profile header data with new case ids and new non case ids
            profile_header_data['non_case_ids'] = non_case_ids
            profile_header_data['case_ids'] = case_ids
        header = profile_header_data['non_case_ids']
        header.extend(profile_header_data['case_ids'])
    elif merge_style == 'normal':
        header = []
        for fname in data_filenames:
            new_header = [hdr for hdr in get_header(fname) if hdr not in header]
            header.extend(new_header)
    return header

def is_clinical_or_timeline(filename):
    """
        Simple check on filename pattern if timeline or clinical data file.
    """
    return (('timeline' in filename) or ('clinical' in filename))

def data_okay_to_add(is_clinical_or_timeline_file, file_header, reference_set, data_values, keep_match):
    """
        Checks reference list (either 'sublist' or 'excluded_samples_list') if any matches found in data values.
        If keeping match then True is returned for positive match, otherwise False is returned.
    """
    if len(reference_set) == 0:
        return True
    found = False
    if is_clinical_or_timeline_file:
        patient_id = data_values[file_header.index('PATIENT_ID')]
        if not 'SAMPLE_ID' in file_header:
            found = (patient_id in PATIENT_SAMPLE_MAP.keys())
            if not keep_match:
                # if patient id not found in patient sample map and we are not keeping
                # matches anyway then return False
                if not found:
                    return False
                # if at least one sample is not in reference set and keep match is false
                # then we want to return true so that data for this patient isn't filtered out
                for sample_id in PATIENT_SAMPLE_MAP[patient_id]:
                    if not sample_id in reference_set:
                        return True
        else:
            # want to explicitly check if sample in reference set if SAMPLE_ID in header
            # to avoid filtering out samples with clin attr's that may contain other patient/sample IDs
            # that may be linked to the current sample but we do not want to filter out of the final dataset
            #
            # default behavior will use sample-id to evaluate timeline records
            # in the case of a patient-based timeline record (null sample id) --
            # timeline record will be included as long as patient exists in the output set
            #
            # Ex: OTHER_SAMPLE_ID/OTHER_PATIENT_ID, or similar attr's like RNA_ID, METHYLATION_ID
            #	 which indicate what other sample IDs are linked to current sample record
            sample_id = data_values[file_header.index('SAMPLE_ID')]
            if not sample_id:
                return patient_id in PATIENT_SAMPLE_MAP.keys()
            found = (sample_id in reference_set)
    elif len([True for val in data_values if val in reference_set]) > 0:
        found = True
    return (keep_match == found)

def profile_row(key,data,header,gene_sample_dict):
    """
        Processes a profile merge style row.
        In this style, genes are the rows and data from each sample
        must be associated to the correct gene.
    """

    # since we already know the new header, we just need to update the existing gene data with
    # fields in the new header that aren't in the existing data yet
    # new_data = {k:v for k,v in data.items() if k in header and not k in existing_gene_data} 2:22
    existing_gene_data = gene_sample_dict.get(key, {})
    new_data = {k:v for k,v in data.items() if not k in existing_gene_data}
    existing_gene_data.update(new_data)
    gene_sample_dict[key] = existing_gene_data

    return gene_sample_dict

def normal_row(line, header):
    """
        Processes a normal merge style row.
        A row is stored as a dictionary - key => column name, value => datum
    """
    row = list(map(lambda x: process_datum(line.get(x, '')), header))
    return row

def merge_rows(previous_row_list, current_row_dict, header, patient_id):
    """
        Merges non-empty values from current_row_dict into previous_row_list,
        overwriting any values that conflict.
    """
    for index, attribute in enumerate(header):
        if attribute in current_row_dict:
            value = process_datum(current_row_dict.get(attribute, ''))
            if value:
                if previous_row_list[index] and value != previous_row_list[index]:
                    logger.info("Ignoring value '%s' in favor of prior value '%s' for attribute '%s' in patient '%s'" % (value, previous_row_list[index], attribute, patient_id))
                else:
                    previous_row_list[index] = value

def write_profile(gene_sample_dict, output_filename, new_header):
    """ Writes out to file profile style merge data, gene by gene. """
    output_file = open(output_filename, 'w')
    output_file.write('\t'.join(new_header) + '\n')
    for gene,data in gene_sample_dict.items():
        new_row = list(map(lambda x: process_datum(data.get(x, '')), new_header))
        output_file.write('\t'.join(new_row) + '\n')
    output_file.close()

def write_normal(rows, output_filename, new_header):
    """ Writes out to file normal style merge data, row by row. """
    output_file = open(output_filename, 'w')

    output_file_basename = os.path.basename(output_filename)

    output_file.write('\t'.join(new_header) + '\n')
    for row in rows:
        output_file.write('\t'.join(row) + '\n')
    output_file.close()

def add_clincial_meta(merged_clinical_comments, clinical_data_dictionary, new_header):
    comments_header = ""
    for val in new_header:
        if val in merged_clinical_comments:
            continue
        elif val in clinical_data_dictionary:
            merged_clinical_comments[val] = tuple(clinical_data_dictionary[val])
            continue
        else:
            disp_name = val.replace('_', ' ').title()
            merged_clinical_comments[val] = (disp_name, disp_name, 'STRING', '1')

    ordered_comments = [(merged_clinical_comments[k]) for k in new_header]
    for line in list(zip(*ordered_comments)):
        comments_header += '#'+('\t'.join(line)).replace('#','')+'\n'
    return(comments_header)

def write_clinical(rows, output_filename, new_header):
    """ Writes out to the file normal style merge data with comments, row by row. """
    comments = add_clincial_meta(merged_clinical_comments, clinical_data_dictionary, new_header)
    output_file = open(output_filename, 'w')

    output_file_basename = os.path.basename(output_filename)

    output_file.write(comments)
    output_file.write('\t'.join(new_header) + '\n')
    for row in rows:
        output_file.write('\t'.join(row) + '\n')
    output_file.close()

def merge_files(outfile_name, infiles, reference_set, keep_match, output_directory):
    """
        Merges files together by adding data from each file to a dictionary/list that contains all
        of the information. After all data from every file from a type is accumulated, it gets written
        out to a file.
    """

    merge_style = identify_file_type(infiles[0])
    if not merge_style:
        return()
    new_header = process_header(infiles, reference_set, keep_match, merge_style)
    is_clinical_or_timeline_file = is_clinical_or_timeline(infiles[0])
    output_filename = os.path.join(output_directory,outfile_name)

    gene_sample_dict = {}
    is_first_profile_datafile = True
    rows = []
    id_to_row_index = {} # use for CLINICAL files
    replicated_id_row_count = 0
    clinical = False

    for f in infiles:
        if 'data_nonsignedout_mutations' in f or 'data_mutations_manual' in f or 'supp_date' in f:
            continue

        data_file_basename = os.path.basename(f)

        # now merge data from file
        file_header = get_header(f)
        if 'clinical' in f:
            clinical = True
            get_comments(f, file_header)

        data_file = open(f, 'r')
        lines = [l for l in data_file.readlines() if not l.startswith('#')][1:]
        # go through the lines, add the data to the objects
        for i,l in enumerate(lines):
            data = dict(zip(file_header, map(lambda x: process_datum(x), l.split('\t'))))
            if merge_style == 'profile':
                key = process_datum(l.split('\t')[0])
                if is_first_profile_datafile:
                    # the new header will take care of any subsetting of the data when the file is written
                    gene_sample_dict[key] = {k:v for k,v in data.items()}
                else:
                    profile_row(key,data, new_header, gene_sample_dict)
            if merge_style == 'normal':
                data_values = list(map(lambda x: data.get(x, ''), file_header))
                if data_okay_to_add(is_clinical_or_timeline_file, file_header, reference_set, data_values, keep_match):
                    if 'clinical' in f:
                        # map clinical meta headers
                        if 'supp' in f and 'SAMPLE_ID' in data: indexed_id = data['SAMPLE_ID']
                        elif 'supp' in f and 'PATIENT_ID' in data: indexed_id = data['PATIENT_ID']
                        elif 'PATIENT_ID' not in data and 'SAMPLE_ID' not in data: continue
                        else: indexed_id = data['PATIENT_ID'] if 'patient' in f else data['SAMPLE_ID']

                        if indexed_id in id_to_row_index:
                            previous_record = rows[id_to_row_index[indexed_id]]
                            replicated_id_row_count += 1
                            merge_rows(previous_record, data, new_header, indexed_id)
                        else:
                            id_to_row_index[indexed_id] = len(rows)
                            rows.append(normal_row(data, new_header))
                    else:
                        rows.append(normal_row(data, new_header))
        is_first_profile_datafile = False
        data_file.close()

    # write out to the file
    if merge_style == 'profile':
        write_profile(gene_sample_dict, output_filename, new_header)
    if merge_style == 'normal':
        # don't attempt to write a file or validate merge if no data was merged or subset from the source data
        if len(rows) == 0:
            logger.info('No data was merged for ' + outfile_name)
            return
        if clinical: write_clinical(rows, output_filename, new_header)
        else: write_normal(rows, output_filename, new_header)

def copy_files(file_type, files, output_directory, study_id):
    """
        Copies over meta files. Merges the values in columns.
    """
    meta_dict = {}
    outfile = open(os.path.join(output_directory, file_type), 'w')

    for f in files:
        with open(f, 'r') as meta:
            for line in meta:
                line = [x.strip() for x in line.strip().split(':', 1)]
                if line[0] not in meta_dict:
                    try: meta_dict[line[0]] = [line[1]]
                    except: pass
                else:
                    try: meta_dict[line[0]].append(line[1])
                    except: pass

    for key in meta_dict:
        if key == 'cancer_study_identifier':
            outfile.write(key+': '+study_id+'\n')
        elif key == 'data_filename':
            outfile.write(key+': '+file_type.replace('meta','data')+'\n')
        else:
            outfile.write(key+': '+meta_dict[key][0]+'\n')

    outfile.close()

def merge_case_lists(file_type, files, output_directory, study_id, reference_set, keep_match):
    case_lists_dir = os.path.join(output_directory,'case_lists')
    if not os.path.exists(case_lists_dir): os.makedirs(case_lists_dir)
    outfile = open(os.path.join(case_lists_dir, file_type), 'w')
    case_dict = {}

    for file in files:
        with open(file, 'r') as casef:
            for line in casef:
                line = [x.strip() for x in line.strip().split(':', 1)]
                if line[0] not in case_dict:
                    try: case_dict[line[0]] = [line[1]]
                    except: pass
                else:
                    try: case_dict[line[0]].append(line[1])
                    except: pass
    ids_list = list()
    for key in case_dict:
        if key == 'cancer_study_identifier':
            ids_list = case_dict[key]
            outfile.write(key+': '+study_id+'\n')
        elif key == 'stable_id':
            for x in ids_list:
                if x in case_dict[key][0]: case_dict[key][0] = case_dict[key][0].replace(x, study_id)
            outfile.write(key+': '+case_dict[key][0]+'\n')
        elif key == 'case_list_description':
            outfile.write(key+': '+case_dict[key][0].split('(')[0].strip()+'\n')
        elif key == 'case_list_ids':
            ids_to_map = set()
            for val in case_dict[key]:
                case_ids = val.strip().split('\t')
                if keep_match:
                    for id in case_ids:
                        if id in reference_set: ids_to_map.add(id)
                else:
                    for id in case_ids:
                        if id not in reference_set: ids_to_map.add(id)
            case_samples = '\t'.join(ids_to_map)
            outfile.write(key+': '+case_samples+'\n')
        else:
            outfile.write(key+': '+case_dict[key][0]+'\n')
    outfile.close()

def merge_studies(merge_map, reference_set, keep_match, output_directory, study_id):
    """
        Goes through all the potential file types and calls correct function for those types.
        Normal merge, profile merge, and straight copy are the possibilities
    """
    for file_type, files in merge_map.items():
        if file_type.startswith('data') and len(files) > 0:
            if len(files) > 1:
                logger.info('Merging data associated with:')
                for f in files:
                    logger.info('\t'+f)
            else:
                logger.info('Only one file found - Copying data associated with: ' + files[0])

            merge_files(file_type, files, reference_set, keep_match, output_directory)

        elif file_type.startswith('meta') and len(files) > 0:
            # make sure there are data files in list so that empty files aren't generated
            related_data_file = file_type.replace('meta','data')
            if related_data_file in merge_map:
                if len(files) > 1:
                    logger.info('Merging data associated with:')
                    for f in files:
                        logger.info('\t' + f)
                    copy_files(file_type, files, output_directory, study_id)
                else:
                    logger.info('Only one file found - Copying data associated with: ' + files[0])
                    copy_files(file_type, files, output_directory, study_id)
            elif file_type == 'meta_study.txt':
                logger.info('Merging data associated with:')
                for f in files:
                    logger.info('\t' + f)
                copy_files(file_type, files, output_directory, study_id)

        if file_type.startswith('cases') and len(files) > 0:
            # copy the case list samples
            if len(files) > 1:
                logger.info('Merging data associated with:')
                for f in files:
                    logger.info('\t'+f)
                    merge_case_lists(file_type, files, output_directory, study_id, reference_set, keep_match)
            else:
                logger.info('Only one file found - Copying data associated with: ' + files[0])
                merge_case_lists(file_type, files, output_directory, study_id, reference_set, keep_match)

    logger.info('Merge complete!')

def generate_study_id(dir_list):
    dirs = [x.strip() for x in dir_list.split(',')]
    study_id = ""
    for dir in dirs: study_id += os.path.basename(dir.strip('/'))+'_'
    study_id = study_id.strip('_')
    return study_id

@click.command()
@click.option('-s', '--subset-samples', required = False, help = 'subset sample list')
@click.option('-e', '--excluded-samples', required = False, help = 'excluded sample list')
@click.option('-i', '--input-directory', required = True, help = 'input directories to subset from')

def main(subset_samples, excluded_samples, input_directory):
    logger.info('Subsetting data from : {}'.format(input_directory))
    if subset_samples is not None:
        if not os.path.exists(subset_samples):
            logger.error('ID list cannot be found: ' + subset_samples)
            sys.exit(2)
    if excluded_samples is not None:
        if not os.path.exists(excluded_samples):
            logger.error('Excluded samples list cannot be found: ' + excluded_samples)
            sys.exit(2)

    # check directories exist
    for study in input_directory.split(','):
        if not os.path.exists(study):
            logger.error('Study cannot be found: ' + study)
            sys.exit(2)
        else:
            if 'data_clinical.txt' in os.listdir(study): # split the data_clinical.txt to clinical patient and sample files first
                split_data_clinical_attributes.main(os.path.join(study,'data_clinical.txt'), logger)
                TEMP_FILES.extend([os.path.join(study,'data_clinical_patient.txt'), os.path.join(study,'data_clinical_sample.txt')])

	# create output directory, identify study ID from input directories list
    study_id = generate_study_id(input_directory)
    output_directory = os.path.join(os.getcwd(),study_id)
    print('The subset data will be written to:', output_directory)
    logger.info('The subset data will be written to:' + output_directory)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    else:
    	shutil.rmtree(output_directory)
    	os.makedirs(output_directory)

    # generate file maping
    merge_map = generate_file_mapping(DATA_FILENAME_MAPPING_FILE, input_directory)
    if 'data_clinical.txt' in merge_map:
        del merge_map['data_clinical.txt']

    # generate clinical meta headers mapping
    generate_clinical_metadata(CLINICAL_META_DATA)

    # subset list
    sublist = []
    excluded_samples_list = []
    if subset_samples is not None:
        sublist = [line.strip() for line in open(subset_samples,'r').readlines()]
    if excluded_samples is not None:
        excluded_samples_list = [line.strip() for line in open(excluded_samples, 'r').readlines()]

    if subset_samples is not None and excluded_samples is not None:
        logger.error('Cannot specify a subset list and an exclude samples list! Please use one option or the other.')
        sys.exit(2)

    # load patient sample mapping from clinical files
    reference_set,keep_match = generate_patient_sample_mapping(merge_map, sublist, excluded_samples_list)

    # merge the studies
    merge_studies(merge_map, reference_set, keep_match, output_directory, study_id)

    [os.remove(file) for file in TEMP_FILES if len(TEMP_FILES) > 0]

if __name__ == '__main__':
    main()
