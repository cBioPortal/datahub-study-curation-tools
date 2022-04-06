# ------------------------------------------------------------------------------
# imports

import sys
import optparse
import os
import shutil
import re
import csv

# ------------------------------------------------------------------------------
# globals

# some file descriptors
ERROR_FILE = sys.stderr
OUTPUT_FILE = sys.stdout

NORMAL = "NORMAL"
PROFILE = "PROFILE"
MERGE_STYLES = {NORMAL:0, PROFILE:1}

SUPP_DATA = 'SUPP_DATA'

SEG_HG18_FILE_PATTERN = '_data_cna_hg18.seg'
SEG_HG18_META_PATTERN = '_meta_cna_hg18_seg.txt'

SEG_HG19_FILE_PATTERN = '_data_cna_hg19.seg'
SEG_HG19_META_PATTERN = '_meta_cna_hg19_seg.txt'

MUTATION_FILE_PATTERN = 'data_mutations_extended.txt'
MUTATION_META_PATTERN = 'meta_mutations_extended.txt'

CNA_FILE_PATTERN = 'data_CNA.txt'
CNA_META_PATTERN = 'meta_CNA.txt'

CLINICAL_FILE_PATTERN = 'data_clinical.txt'
CLINICAL_META_PATTERN = 'meta_clinical.txt'

LOG2_FILE_PATTERN = 'data_log2CNA.txt'
LOG2_META_PATTERN = 'meta_log2CNA.txt'

EXPRESSION_FILE_PATTERN = 'data_expression.txt'
EXPRESSION_META_PATTERN = 'meta_expression.txt'

FUSION_FILE_PATTERN = 'data_fusions.txt'
FUSION_META_PATTERN = 'meta_fusions.txt'

METHYLATION450_FILE_PATTERN = 'data_methylation_hm450.txt'
METHYLATION450_META_PATTERN = 'meta_methylation_hm450.txt'

METHYLATION27_FILE_PATTERN = 'data_methylation_hm27.txt'
METHYLATION27_META_PATTERN = 'meta_methylation_hm27.txt'

METHYLATION_GB_HMEPIC_FILE_PATTERN = 'data_methylation_genebodies_hmEPIC.txt'
METHYLATION_GB_HMEPIC_META_PATTERN = 'meta_methylation_genebodies_hmEPIC.txt'

METHYLATION_PROMOTERS_HMEPIC_FILE_PATTERN = 'data_methylation_promoters_hmEPIC.txt'
METHYLATION_PROMOTERS_HMEPIC_META_PATTERN = 'meta_methylation_promoters_hmEPIC.txt'

METHYLATION_GB_WGBS_FILE_PATTERN = 'data_methylation_genebodies_wgbs.txt'
METHYLATION_GB_WGBS_META_PATTERN = 'meta_methylation_genebodies_wgbs.txt'

METHYLATION_PROMOTERS_WGBS_FILE_PATTERN = 'data_methylation_promoters_wgbs.txt'
METHYLATION_PROMOTERS_WGBS_META_PATTERN = 'meta_methylation_promoters_wgbs.txt'

RNASEQ_EXPRESSION_FILE_PATTERN = 'data_RNA_Seq_expression_median.txt'
RNASEQ_EXPRESSION_META_PATTERN = 'meta_RNA_Seq_expression_median.txt'

RPPA_FILE_PATTERN = 'data_rppa.txt'
RPPA_META_PATTERN = 'meta_rppa.txt'

TIMELINE_FILE_PATTERN = 'data_timeline.txt'
TIMELINE_META_PATTERN = 'meta_timeline.txt'

CLINICAL_PATIENT_FILE_PATTERN = 'data_clinical_patient.txt'
CLINICAL_PATIENT_META_PATTERN = 'meta_clinical_patient.txt'

CLINICAL_SAMPLE_FILE_PATTERN = 'data_clinical_sample.txt'
CLINICAL_SAMPLE_META_PATTERN = 'meta_clinical_sample.txt'

GENE_MATRIX_FILE_PATTERN = 'data_gene_matrix.txt'
GENE_MATRIX_META_PATTERN = 'meta_gene_matrix.txt'

SV_FILE_PATTERN = 'data_SV.txt'
SV_META_PATTERN = 'meta_SV.txt'

FUSIONS_GML_FILE_PATTERN = 'data_fusions_gml.txt'
FUSIONS_GML_META_PATTERN = 'meta_fusions_gml.txt'

# we do not want to copy over or merge json files or meta_study.txt files
FILE_PATTERN_FILTERS = ['.sqlite', '.json', 'meta_study.txt', '.orig', '.merge', 'ignore', 'data_gene_panel']

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
]


# only files fitting patterns placed in these two lists will be merged
NORMAL_MERGE_PATTERNS = [MUTATION_META_PATTERN,
    FUSION_META_PATTERN,
    SEG_HG18_META_PATTERN,
    SEG_HG19_META_PATTERN,
    CLINICAL_META_PATTERN,
    CLINICAL_PATIENT_META_PATTERN,
    CLINICAL_SAMPLE_META_PATTERN,
    GENE_MATRIX_META_PATTERN,
    SV_META_PATTERN,
    TIMELINE_META_PATTERN,
    FUSIONS_GML_META_PATTERN]

PROFILE_MERGE_PATTERNS = [CNA_META_PATTERN,
    LOG2_META_PATTERN,
    EXPRESSION_META_PATTERN,
    METHYLATION27_META_PATTERN,
    METHYLATION450_META_PATTERN,
    RPPA_META_PATTERN,
    METHYLATION_GB_HMEPIC_META_PATTERN,
    METHYLATION_PROMOTERS_HMEPIC_META_PATTERN,
    METHYLATION_GB_WGBS_META_PATTERN,
    METHYLATION_PROMOTERS_WGBS_META_PATTERN,
    RNASEQ_EXPRESSION_META_PATTERN]

# Not everything in here is being used anymore, but mostly we want the map between meta and data files
META_FILE_MAP = {MUTATION_META_PATTERN:(MUTATION_FILE_PATTERN, 'mutations'),
    CNA_META_PATTERN:(CNA_FILE_PATTERN, 'cna'),
    LOG2_META_PATTERN:(LOG2_FILE_PATTERN, 'log2CNA'),
    SEG_HG18_META_PATTERN:(SEG_HG18_FILE_PATTERN, 'segment_hg18'),
    SEG_HG19_META_PATTERN:(SEG_HG19_FILE_PATTERN, 'segment_hg19'),
    METHYLATION27_META_PATTERN:(METHYLATION27_FILE_PATTERN, 'methylation_hm27'),
    METHYLATION450_META_PATTERN:(METHYLATION450_FILE_PATTERN, 'methylation_hm450'),
    METHYLATION_GB_HMEPIC_META_PATTERN:(METHYLATION_GB_HMEPIC_FILE_PATTERN, 'methylation_genebodies_hmEPIC'),
    METHYLATION_PROMOTERS_HMEPIC_META_PATTERN:(METHYLATION_PROMOTERS_HMEPIC_FILE_PATTERN, 'methylation_promoters_hmEPIC'),
    METHYLATION_GB_WGBS_META_PATTERN:(METHYLATION_GB_WGBS_FILE_PATTERN, 'methylation_genebodies_wgbs'),
    METHYLATION_PROMOTERS_WGBS_META_PATTERN:(METHYLATION_PROMOTERS_WGBS_FILE_PATTERN, 'methylation_promoters_wgbs'),
    FUSION_META_PATTERN:(FUSION_FILE_PATTERN, 'mutations'),
    RPPA_META_PATTERN:(RPPA_FILE_PATTERN, 'rppa'),
    EXPRESSION_META_PATTERN:(EXPRESSION_FILE_PATTERN, 'expression'),
    RNASEQ_EXPRESSION_META_PATTERN:(RNASEQ_EXPRESSION_FILE_PATTERN,'RNA_Seq_expression_median'),
    CLINICAL_META_PATTERN:(CLINICAL_FILE_PATTERN, 'clinical'),
    CLINICAL_PATIENT_META_PATTERN:(CLINICAL_PATIENT_FILE_PATTERN, 'clinical_patient'),
    CLINICAL_SAMPLE_META_PATTERN:(CLINICAL_SAMPLE_FILE_PATTERN, 'clinical_sample'),
    GENE_MATRIX_META_PATTERN:(GENE_MATRIX_FILE_PATTERN, 'gene_matrix'),
    SV_META_PATTERN:(SV_FILE_PATTERN, 'structural_variant'),
    TIMELINE_META_PATTERN:(TIMELINE_FILE_PATTERN, 'timeline'),
    FUSIONS_GML_META_PATTERN:(FUSIONS_GML_FILE_PATTERN, 'fusions_gml')}

MUTATION_FILE_PREFIX = 'data_mutations'
NONSIGNEDOUT_MUTATION_FILENAME = 'data_nonsignedout_mutations.txt'
DATA_CLINICAL_SUPP_PREFIX = 'data_clinical_supp'

SEQUENCED_SAMPLES = []
PATIENT_SAMPLE_MAP = {}

# ------------------------------------------------------------------------------
# Functions

def copy_files(file_type, filenames, reference_set, keep_match, output_directory, study_id, cancer_type):
    """
        Copies over files that aren't explicitly handled by this script (clinical, timeline, etc.).
        If there are subsets involved, only copy those rows. Else just copy the file.
    """
    count = 0
    for f in filenames:
        fname = os.path.basename(f)
        if DATA_CLINICAL_SUPP_PREFIX in fname:
            supp_file_type = CLINICAL_META_PATTERN
        else:
            supp_file_type = file_type
        # these files should be unique so just keep the same file basename, only change output directory
        newfilename = os.path.join(output_directory, fname)

        # lets not bother with metafiles - gets tricky and not worth the trouble, probably would be more of a nuisance to do this anyway
        if 'meta' in fname:
            continue

        file_ok_to_copy = True
        if cancer_type != None:
            if cancer_type not in fname and fname != 'data_clinical.txt':
                file_ok_to_copy = False

        if file_ok_to_copy:
            if 'clinical' in fname and len(reference_set) > 0:
                count += 1
                if not 'SAMPLE_ID' in get_header(f):
                    make_subset(supp_file_type, f, newfilename, PATIENT_SAMPLE_MAP.keys(), keep_match)
                else:
                    make_subset(supp_file_type, f, newfilename, reference_set, keep_match)
            elif 'timeline' in fname and len(reference_set) > 0:
                count += 1
                make_subset(supp_file_type, f, newfilename, PATIENT_SAMPLE_MAP.keys(), keep_match)
            elif len(reference_set) > 0:
                count += 1
                make_subset(supp_file_type, f, newfilename, reference_set, keep_match)
            else:
                shutil.copy(f, newfilename)

def merge_studies(file_types, reference_set, keep_match, output_directory, study_id, cancer_type, exclude_supp_data, merge_clinical):
    """
        Goes through all the potential file types and calls correct function for those types.
        Normal merge, profile merge, and straight copy are the possibilities
    """

    for file_type, files in file_types.items():
        if len(files) > 0:
            if file_type in META_FILE_MAP:
                if not merge_clinical and ('clinical' in file_type or 'timeline' in file_type):
                    continue

                # make sure there are data files in list so that empty files aren't generated
                if len(file_types[META_FILE_MAP[file_type][0]]) == 0:
                    continue

                if len(files) > 1:
                    print >> OUTPUT_FILE, 'Merging data associated with:'
                    for f in files:
                        print >> OUTPUT_FILE, '\t' + f
                else:
                    print >> OUTPUT_FILE, 'Only one file found - Copying data associated with:\n\t' + files[0]

                # get merge style by file type
                if file_type in NORMAL_MERGE_PATTERNS:
                    merge_style = MERGE_STYLES[NORMAL]
                else:
                    merge_style = MERGE_STYLES[PROFILE]

                merge_files(file_types[META_FILE_MAP[file_type][0]], file_type, reference_set, keep_match, output_directory, merge_style, study_id)
            elif file_type == SUPP_DATA and not exclude_supp_data:
                # multiple studies may have the same file basename for other filetypes i.e., data_mutations_nonsignedout.txt
                # we need to figure out which files to pair
                supp_filetypes = {}
                for f in files:
                    file_list = supp_filetypes.get(os.path.basename(f), [])
                    file_list.append(f)
                    supp_filetypes[os.path.basename(f)] = file_list

                # now that we have other filetypes paired, we will either copy the files to the output directory or merge them using the 'NORMAL' merge style
                files_to_copy = []
                for other_file_pattern,other_files in supp_filetypes.items():
                    if len(other_files) == 1:
                        files_to_copy.append(other_files[0])
                    else:
                        print >> OUTPUT_FILE, 'Merging files matching "supplemental" filename pattern:', other_file_pattern
                        for f in other_files:
                            print >> OUTPUT_FILE, '\t' + f
                        if DATA_CLINICAL_SUPP_PREFIX in os.path.basename(other_files[0]):
                            supp_file_type = CLINICAL_META_PATTERN
                        else:
                            supp_file_type = file_type
                        merge_files(other_files, file_type, reference_set, keep_match, output_directory, MERGE_STYLES[NORMAL], study_id)

                # copy files over to output directory if list not empty
                if len(files_to_copy) == 0:
                    continue
                print >> OUTPUT_FILE, 'Copying supplemental files meeting criteria from:'
                for f in files_to_copy:
                    print >> OUTPUT_FILE, '\t' + f
                copy_files(file_type, files_to_copy, reference_set, keep_match, output_directory, study_id, cancer_type)
    print >> OUTPUT_FILE, '\nMerge complete!'

def merge_files(data_filenames, file_type, reference_set, keep_match, output_directory, merge_style, study_id):
    """
        Merges files together by adding data from each file to a dictionary/list that contains all
        of the information. After all data from every file from a type is accumulated, it gets written
        out to a file.
    """
    new_header = process_header(data_filenames, reference_set, keep_match, merge_style)

    if file_type in [SEG_HG18_META_PATTERN, SEG_HG19_META_PATTERN]:
        output_filename = os.path.join(output_directory, study_id + META_FILE_MAP[file_type][0])
    elif file_type == 'SUPP_DATA' or DATA_CLINICAL_SUPP_PREFIX in data_filenames[0]:
        output_filename = os.path.join(output_directory, os.path.basename(data_filenames[0]))
    else:
        output_filename = os.path.join(output_directory, META_FILE_MAP[file_type][0])
    is_clinical_or_timeline_file = is_clinical_or_timeline(data_filenames[0])

    # key: String:gene
    # value: [(sample1Name,sample1Value),(sample1Name,sample2Value), ... ]
    gene_sample_dict = {}
    is_first_profile_datafile = True
    rows = []
    id_to_row_index = {} # use for CLINICAL files
    replicated_id_row_count = 0

    for f in data_filenames:
        # update sequenced samples tag if data_mutations* file
        data_file_basename = os.path.basename(f)
        if data_file_basename.startswith(MUTATION_FILE_PREFIX) or data_file_basename == NONSIGNEDOUT_MUTATION_FILENAME:
            update_sequenced_samples(f, reference_set, keep_match)

        # now merge data from file
        file_header = get_header(f)
        data_file = open(f, 'rU')
        lines = [l for l in data_file.readlines() if not l.startswith('#')][1:]

        # go through the lines, add the data to the objects
        for i,l in enumerate(lines):
            data = dict(zip(file_header, map(lambda x: process_datum(x), l.split('\t'))))
            if merge_style is MERGE_STYLES[PROFILE]:
                key = process_datum(l.split('\t')[0])
                if is_first_profile_datafile:
                    # the new header will take care of any subsetting of the data when the file is written
                    gene_sample_dict[key] = {k:v for k,v in data.items()}
                else:
                    profile_row(key,data, new_header, gene_sample_dict)
            elif merge_style is MERGE_STYLES[NORMAL]:
                data_values = map(lambda x: data.get(x, ''), file_header)
                if data_okay_to_add(is_clinical_or_timeline_file, file_header, reference_set, data_values, keep_match):
                    if file_type in [CLINICAL_PATIENT_META_PATTERN, CLINICAL_SAMPLE_META_PATTERN, CLINICAL_META_PATTERN]:
                        indexed_id = data['PATIENT_ID'] if file_type == CLINICAL_PATIENT_META_PATTERN else data['SAMPLE_ID']
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
    if merge_style is MERGE_STYLES[PROFILE]:
        write_profile(gene_sample_dict, output_filename, new_header)
    if merge_style is MERGE_STYLES[NORMAL]:
        # don't attempt to write a file or validate merge if no data was merged or subset from the source data
        if len(rows) == 0:
            print >> OUTPUT_FILE, 'No data was merged for ' + file_type
            return
        write_normal(rows, output_filename, new_header)

    print >> OUTPUT_FILE, 'Validating merge for: ' + output_filename
    validate_merge(file_type, data_filenames, output_filename, reference_set, keep_match, merge_style, replicated_id_row_count)

def validate_merge(file_type, data_filenames, merged_filename, reference_set, keep_match, merge_style, skipped_row_count):
    merged_file_summary = get_datafile_counts_summary(file_type, merged_filename, reference_set, keep_match, merge_style)
    merged_header = process_header(data_filenames, reference_set, keep_match, merge_style)

    # check that the merged header constructed from the data files matches the length of the header written to the merged file
    if len(merged_header) != merged_file_summary['num_cols']:
        print >> ERROR_FILE, 'Validation failed! Length of merged header does not match the header constructed from data files!'
        sys.exit(2)

    # get summary info for data filenames and compare with merged file counts
    datafile_summaries = {}
    total_rows = 0
    merged_gene_ids = []
    for filename in data_filenames:
        datafile_summaries[filename] = get_datafile_counts_summary(file_type, filename, reference_set, keep_match, merge_style)
        if merge_style is MERGE_STYLES[PROFILE]:
            new_gene_keys = [gene for gene in datafile_summaries[filename]['gene_ids'] if not gene in merged_gene_ids]
            merged_gene_ids.extend(new_gene_keys)
        else:
            total_rows += datafile_summaries[filename]['num_rows']
    # update total rows in merge style is profile
    if merge_style is MERGE_STYLES[PROFILE]:
        total_rows = len(merged_gene_ids)

    if total_rows - skipped_row_count != merged_file_summary['num_rows']:
        print >> ERROR_FILE, 'Validation failed! Total rows calculated from data files does not match total rows in merged file!'
        print datafile_summaries
        sys.exit(2)

    print >> OUTPUT_FILE, 'Validation succeeded!\n'


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
            #     which indicate what other sample IDs are linked to current sample record
            sample_id = data_values[file_header.index('SAMPLE_ID')]
            if not sample_id:
                return patient_id in PATIENT_SAMPLE_MAP.keys()
            found = (sample_id in reference_set)
    elif len([True for val in data_values if val in reference_set]) > 0:
        found = True
    return (keep_match == found)


def get_datafile_counts_summary(file_type, filename, reference_set, keep_match, merge_style):
    """ Summarizes the basic data file info (num cols, num rows, gene ids). """
    file_header = get_header(filename)
    data_file = open(filename, 'rU')
    filedata = [x for x in data_file.readlines() if not x.startswith('#')]
    is_clinical_or_timeline_file = is_clinical_or_timeline(filename)

    # filter header if necessary
    if merge_style is MERGE_STYLES[PROFILE] and len(reference_set) > 0:
        if keep_match:
            file_header = [hdr for hdr in file_header if hdr.upper() in NON_CASE_IDS or hdr in reference_set]
        else:
            file_header = [hdr for hdr in file_header if hdr not in reference_set]

    # figure out relevant row count
    # if no sublist then number of rows is the total rows minus the header
    gene_ids = [] # assuming that gene id is first column of profile data files
    if merge_style is MERGE_STYLES[PROFILE]:
        gene_ids = map(lambda x: process_datum(x.split('\t')[0]), filedata[1:])
        num_rows = len(filedata) - 1
    else:
        if len(reference_set) > 0:
            num_rows = 0
            for row in filedata[1:]:
                data_values = map(lambda x: process_datum(x), row.split('\t'))
                if data_okay_to_add(is_clinical_or_timeline_file, file_header, reference_set, data_values, keep_match):
                    num_rows += 1
        else:
            num_rows = len(filedata) - 1
    data_file.close()

    # fill summary info
    summary_info = {'num_cols':len(file_header), 'num_rows':num_rows, 'gene_ids':gene_ids}
    return summary_info

def update_sequenced_samples(filename, reference_set, keep_match):
    """ Updates the SEQUENCED_SAMPLES list. """
    data_file = open(filename, 'rU')
    comments = [x for x in data_file.readlines() if x.startswith('#')]
    for c in comments:
        if not 'sequenced_samples' in c:
            continue

        # split sequenced sample tag by all : and spaces, sample ids begin at index 1
        sequenced_samples = map(lambda x: process_datum(x), re.split('[: ]', c)[1:])
        if len(reference_set) > 0:
            for sample_id in sequenced_samples:
                add_seq_sample = (keep_match == (sample_id in reference_set))
                if add_seq_sample:
                    SEQUENCED_SAMPLES.append(sample_id)
        else:
            SEQUENCED_SAMPLES.extend(sequenced_samples)
    data_file.close()

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
    header = map(str.strip, filedata[0].split('\t'))
    return header

def process_header(data_filenames, reference_set, keep_match, merge_style):
    """ Handles header merging, accumulating all column names """

    if merge_style is MERGE_STYLES[PROFILE]:
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
    elif merge_style is MERGE_STYLES[NORMAL]:
        header = []
        for fname in data_filenames:
            new_header = [hdr for hdr in get_header(fname) if hdr not in header]
            header.extend(new_header)

    return header

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
                    print >> ERROR_FILE, "Ignoring value '%s' in favor of prior value '%s' for attribute '%s' in patient '%s'" % (value, previous_row_list[index], attribute, patient_id)
                else:
                    previous_row_list[index] = value

def normal_row(line, header):
    """
        Processes a normal merge style row.
        A row is stored as a dictionary - key => column name, value => datum
    """
    row = map(lambda x: process_datum(line.get(x, '')), header)

    return row

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

def write_profile(gene_sample_dict, output_filename, new_header):
    """ Writes out to file profile style merge data, gene by gene. """
    output_file = open(output_filename, 'w')
    output_file.write('\t'.join(new_header) + '\n')
    for gene,data in gene_sample_dict.iteritems():
        new_row = map(lambda x: process_datum(data.get(x, '')), new_header)
        output_file.write('\t'.join(new_row) + '\n')
    output_file.close()

def write_normal(rows, output_filename, new_header):
    """ Writes out to file normal style merge data, row by row. """
    output_file = open(output_filename, 'w')

    output_file_basename = os.path.basename(output_filename)
    # if output file is data_mutations* or data_nonsignedout_mutations then add sequenced samples tag to file before header
    if (output_file_basename.startswith(MUTATION_FILE_PREFIX) or output_file_basename == NONSIGNEDOUT_MUTATION_FILENAME) and SEQUENCED_SAMPLES != []:
        # only add unique sample ids - this shouldn't happen but done as a precaution
        output_file.write('#sequenced_samples: ' + ' '.join(list(set(SEQUENCED_SAMPLES))) + '\n')

    output_file.write('\t'.join(new_header) + '\n')
    for row in rows:
        output_file.write('\t'.join(row) + '\n')
    output_file.close()

def make_subset(file_type, filename, output_filename, reference_set, keep_match):
    """ Makes subset on files that are in normal format (sample per line) """
    try:
        subfile = open(filename, 'rU')
    except IOError:
        print >> ERROR_FILE, 'Error opening file'
        sys.exit(1)

    is_clinical_or_timeline_file = is_clinical_or_timeline(output_filename)
    file_header = get_header(filename)
    output_file = open(output_filename, 'w')
    output_file.write('\t'.join(file_header) + '\n')

    filedata = [line for line in subfile.readlines() if not line.startswith('#')][1:]

    for line in filedata:
        data_values = map(lambda x: process_datum(x), line.split('\t'))
        if data_okay_to_add(is_clinical_or_timeline_file, file_header, reference_set, data_values, keep_match):
            output_file.write(line)
    subfile.close()
    output_file.close()

    # only write output file if number rows is greater than 1
    output_data = [line for line in open(output_filename, 'rU').readlines() if not line.startswith('#')]
    if len(output_data) <= 1:
        if len(reference_set) > 0:
            print >> OUTPUT_FILE, 'Samples in reference list not found in file: ' + filename
            os.remove(output_filename)
        else:
            print >> ERROR_FILE, 'Error loading data from file: ' + filename
            sys.exit(2)

def get_patient_ids(sublist):
    """ Get patient ids from sublist (MSKIMPACT ONLY) """
    patientid = []
    p = re.compile('(P-\d*)-T\d\d-[IM|TS|IH]+\d*')
    for sid in sublist:
        match = p.match(sid)
        if match:
            patientid.append(match.group(1))
        else:
            patientid.append(sid)
    return patientid

def generate_patient_sample_mapping(file_types, sublist, excluded_samples_list):

    # init reference list as empty or to either sublist or excluded_sample_list depending on which is being used
    reference_set = set()
    keep_match = True
    if len(sublist) > 0:
        reference_set = set(sublist[:])
    elif len(excluded_samples_list) > 0:
        reference_set = set(excluded_samples_list[:])
        keep_match = False

    # load patient sample mapping from data_clinical.txt or data_clinical_sample.txt files
    for file_type in [CLINICAL_META_PATTERN, CLINICAL_SAMPLE_META_PATTERN]:
        if file_type in file_types.keys() and len(file_types[META_FILE_MAP[file_type][0]]) > 0:
            load_patient_sample_mapping(file_types[META_FILE_MAP[file_type][0]], reference_set, keep_match)
    if PATIENT_SAMPLE_MAP == {}:
        print >> ERROR_FILE, 'ERROR! generate_patient_sample_mapping(),  Did not load any patient sample mapping from clinical files'
        sys.exit(2)
    return reference_set,keep_match


def load_patient_sample_mapping(data_filenames, reference_set, keep_match):
    """
        Loads patient - sample mapping from given clinical file(s).
    """
    print >> OUTPUT_FILE, 'Loading patient - sample mapping from: '
    # load patient sample mapping from each clinical file
    for filename in data_filenames:
        print >> OUTPUT_FILE, '\t' + filename
        file_header = get_header(filename)
        data_file = open(filename, 'rU')
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
    print >> OUTPUT_FILE, 'Finished loading patient - sample mapping!\n'
    return reference_set

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

def is_clinical_or_timeline(filename):
    """
        Simple check on filename pattern if timeline or clinical data file.
    """
    return (('timeline' in filename) or ('clinical' in filename))

def organize_files(studies, file_types, merge_clinical):
    """ Put files in correct groups. Groups need to be explicitly defined by filenames, hence the ugly if else string. """
    for study in studies:
        study_files = [os.path.join(study,x) for x in os.listdir(study)]
        for study_file in study_files:

            # do not copy sub-directories in study path (i.e., case lists)
            skip_file = False
            if os.path.isdir(study_file):
                skip_file = True
            for filter_pattern in FILE_PATTERN_FILTERS:
                if filter_pattern in study_file:
                    skip_file = True
            if skip_file:
                continue

            # META FILE PATTERN MATCHING
            if MUTATION_META_PATTERN in study_file:
                file_types[MUTATION_META_PATTERN].append(study_file)
            elif CNA_META_PATTERN in study_file:
                file_types[CNA_META_PATTERN].append(study_file)
            elif FUSION_META_PATTERN in study_file:
                file_types[FUSION_META_PATTERN].append(study_file)
            elif SEG_HG18_META_PATTERN in study_file:
                file_types[SEG_HG18_META_PATTERN].append(study_file)
            elif SEG_HG19_META_PATTERN in study_file:
                file_types[SEG_HG19_META_PATTERN].append(study_file)
            elif LOG2_META_PATTERN in study_file:
                file_types[LOG2_META_PATTERN].append(study_file)
            elif EXPRESSION_META_PATTERN in study_file:
                file_types[EXPRESSION_META_PATTERN].append(study_file)
            elif METHYLATION27_META_PATTERN in study_file:
                file_types[METHYLATION27_META_PATTERN].append(study_file)
            elif METHYLATION450_META_PATTERN in study_file:
                file_types[METHYLATION450_META_PATTERN].append(study_file)
            elif METHYLATION_GB_HMEPIC_META_PATTERN in study_file:
                file_types[METHYLATION_GB_HMEPIC_META_PATTERN].append(study_file)
            elif METHYLATION_PROMOTERS_HMEPIC_META_PATTERN in study_file:
                file_types[METHYLATION_PROMOTERS_HMEPIC_META_PATTERN].append(study_file)
            elif METHYLATION_GB_WGBS_META_PATTERN in study_file:
                file_types[METHYLATION_GB_WGBS_META_PATTERN].append(study_file)
            elif METHYLATION_PROMOTERS_WGBS_META_PATTERN in study_file:
                file_types[METHYLATION_PROMOTERS_WGBS_META_PATTERN].append(study_file)
            elif RNASEQ_EXPRESSION_META_PATTERN in study_file:
                file_types[RNASEQ_EXPRESSION_META_PATTERN].append(study_file)
            elif RPPA_META_PATTERN in study_file:
                file_types[RPPA_META_PATTERN].append(study_file)
            elif GENE_MATRIX_META_PATTERN in study_file:
                file_types[GENE_MATRIX_META_PATTERN].append(study_file)
            elif SV_META_PATTERN in study_file:
                file_types[SV_META_PATTERN].append(study_file)
            elif TIMELINE_META_PATTERN in study_file:
                file_types[TIMELINE_META_PATTERN].append(study_file)
            elif FUSIONS_GML_META_PATTERN in study_file:
                file_types[FUSIONS_GML_META_PATTERN].append(study_file)
            # FILE PATTERN MATCHING
            elif MUTATION_FILE_PATTERN in study_file:
                file_types[MUTATION_FILE_PATTERN].append(study_file)
            elif CNA_FILE_PATTERN in study_file:
                file_types[CNA_FILE_PATTERN].append(study_file)
            elif FUSION_FILE_PATTERN in study_file:
                file_types[FUSION_FILE_PATTERN].append(study_file)
            elif SEG_HG18_FILE_PATTERN in study_file:
                file_types[SEG_HG18_FILE_PATTERN].append(study_file)
            elif SEG_HG19_FILE_PATTERN in study_file:
                file_types[SEG_HG19_FILE_PATTERN].append(study_file)
            elif LOG2_FILE_PATTERN in study_file:
                file_types[LOG2_FILE_PATTERN].append(study_file)
            elif EXPRESSION_FILE_PATTERN in study_file:
                file_types[EXPRESSION_FILE_PATTERN].append(study_file)
            elif METHYLATION27_FILE_PATTERN in study_file:
                file_types[METHYLATION27_FILE_PATTERN].append(study_file)
            elif METHYLATION450_FILE_PATTERN in study_file:
                file_types[METHYLATION450_FILE_PATTERN].append(study_file)
            elif METHYLATION_GB_HMEPIC_FILE_PATTERN in study_file:
                file_types[METHYLATION_GB_HMEPIC_FILE_PATTERN].append(study_file)
            elif METHYLATION_PROMOTERS_HMEPIC_FILE_PATTERN in study_file:
                file_types[METHYLATION_PROMOTERS_HMEPIC_FILE_PATTERN].append(study_file)
            elif METHYLATION_GB_WGBS_FILE_PATTERN in study_file:
                file_types[METHYLATION_GB_WGBS_FILE_PATTERN].append(study_file)
            elif METHYLATION_PROMOTERS_WGBS_FILE_PATTERN in study_file:
                file_types[METHYLATION_PROMOTERS_WGBS_FILE_PATTERN].append(study_file)
            elif RNASEQ_EXPRESSION_FILE_PATTERN in study_file:
                file_types[RNASEQ_EXPRESSION_FILE_PATTERN].append(study_file)
            elif RPPA_FILE_PATTERN in study_file:
                file_types[RPPA_FILE_PATTERN].append(study_file)
            elif GENE_MATRIX_FILE_PATTERN in study_file:
                file_types[GENE_MATRIX_FILE_PATTERN].append(study_file)
            elif SV_FILE_PATTERN in study_file:
                file_types[SV_FILE_PATTERN].append(study_file)
            elif TIMELINE_FILE_PATTERN in study_file:
                file_types[TIMELINE_FILE_PATTERN].append(study_file)
            elif FUSIONS_GML_FILE_PATTERN in study_file:
                file_types[FUSIONS_GML_FILE_PATTERN].append(study_file)
            # CLINICAL FILE PATTERN MATCHING
            elif CLINICAL_META_PATTERN in study_file:
                file_types[CLINICAL_META_PATTERN].append(study_file)
            elif CLINICAL_PATIENT_META_PATTERN in study_file:
                file_types[CLINICAL_PATIENT_META_PATTERN].append(study_file)
            elif CLINICAL_SAMPLE_META_PATTERN in study_file:
                file_types[CLINICAL_SAMPLE_META_PATTERN].append(study_file)
            elif CLINICAL_FILE_PATTERN in study_file:
                file_types[CLINICAL_FILE_PATTERN].append(study_file)
            elif CLINICAL_PATIENT_FILE_PATTERN in study_file:
                file_types[CLINICAL_PATIENT_FILE_PATTERN].append(study_file)
            elif CLINICAL_SAMPLE_FILE_PATTERN in study_file:
                file_types[CLINICAL_SAMPLE_FILE_PATTERN].append(study_file)
            elif DATA_CLINICAL_SUPP_PREFIX in study_file:
                file_types[SUPP_DATA].append(study_file)
            else:
                file_types[SUPP_DATA].append(study_file)

def usage():
    print >> OUTPUT_FILE, 'merge.py --subset [/path/to/subset] --output-directory [/path/to/output] --study-id [study id] --cancer-type [cancer type] --merge-clinical [true/false] --exclude-supplemental-data [true/false] --excluded-samples [/path/to/exclude_list] <path/to/study path/to/study ...>'

def main(options, args):
    """ Handle command line args, checks the directories exist, then calls passes things along to the other functions """

    subsetlist = options.subset
    excluded_samples = options.excludedsamples
    output_directory = options.outputdir
    study_id = options.studyid
    cancer_type = options.cancertype
    merge_clinical = options.mergeclinical
    exclude_supp_data = options.excludesuppdata

    if (output_directory == None or study_id == None):
        usage()
        sys.exit(2)
    if subsetlist is not None:
        if not os.path.exists(subsetlist):
            print >> ERROR_FILE, 'ID list cannot be found: ' + subsetlist
            sys.exit(2)
    if excluded_samples is not None:
        if not os.path.exists(excluded_samples):
            print >> ERROR_FILE, 'Excluded samples list cannot be found: ' + excluded_samples
            sys.exit(2)

    # check directories exist
    for study in args:
        if not os.path.exists(study):
            print >> ERROR_FILE, 'Study cannot be found: ' + study
            sys.exit(2)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    file_types = {MUTATION_FILE_PATTERN: [],
        CNA_FILE_PATTERN: [],
        FUSION_FILE_PATTERN: [],
        SEG_HG18_FILE_PATTERN: [],
        SEG_HG19_FILE_PATTERN: [],
        LOG2_FILE_PATTERN: [],
        EXPRESSION_FILE_PATTERN: [],
        METHYLATION27_FILE_PATTERN: [],
        METHYLATION450_FILE_PATTERN: [],
        METHYLATION_GB_HMEPIC_FILE_PATTERN: [],
        METHYLATION_PROMOTERS_HMEPIC_FILE_PATTERN: [],
        METHYLATION_GB_WGBS_FILE_PATTERN: [],
        METHYLATION_PROMOTERS_WGBS_FILE_PATTERN: [],
        RNASEQ_EXPRESSION_FILE_PATTERN: [],
        RPPA_FILE_PATTERN: [],
        GENE_MATRIX_FILE_PATTERN: [],
        SV_FILE_PATTERN: [],
        TIMELINE_FILE_PATTERN: [],
        FUSIONS_GML_FILE_PATTERN: [],
        MUTATION_META_PATTERN: [],
        CNA_META_PATTERN: [],
        FUSION_META_PATTERN: [],
        SEG_HG18_META_PATTERN: [],
        SEG_HG19_META_PATTERN: [],
        LOG2_META_PATTERN: [],
        EXPRESSION_META_PATTERN: [],
        METHYLATION27_META_PATTERN: [],
        METHYLATION450_META_PATTERN: [],
        METHYLATION_GB_HMEPIC_META_PATTERN: [],
        METHYLATION_PROMOTERS_HMEPIC_META_PATTERN: [],
        METHYLATION_GB_WGBS_META_PATTERN: [],
        METHYLATION_PROMOTERS_WGBS_META_PATTERN: [],
        RNASEQ_EXPRESSION_META_PATTERN: [],
        RPPA_META_PATTERN: [],
        GENE_MATRIX_META_PATTERN: [],
        SV_META_PATTERN: [],
        TIMELINE_META_PATTERN: [],
        FUSIONS_GML_META_PATTERN: [],
        SUPP_DATA: [],
        CLINICAL_META_PATTERN: [],
        CLINICAL_PATIENT_META_PATTERN: [],
        CLINICAL_SAMPLE_META_PATTERN: [],
        CLINICAL_FILE_PATTERN: [],
        CLINICAL_PATIENT_FILE_PATTERN: [],
        CLINICAL_SAMPLE_FILE_PATTERN: []}

    # adds clinical file types if merge_clinical is true
    if merge_clinical != None and merge_clinical.lower() == 'true':
        merge_clinical = True
    else:
        merge_clinical = False

    # determines whether to exclude supplemental data or not
    if not exclude_supp_data or exclude_supp_data.lower() == 'false':
        exclude_supp_data = False
    else:
        exclude_supp_data = True

    # get all the filenames
    organize_files(args, file_types, merge_clinical)

    #subset list
    sublist = []
    excluded_samples_list = []
    if subsetlist is not None:
        sublist = [line.strip() for line in open(subsetlist,'rU').readlines()]
    if excluded_samples is not None:
        excluded_samples_list = [line.strip() for line in open(excluded_samples, 'rU').readlines()]

    if subsetlist is not None and excluded_samples is not None:
        print >> ERROR_FILE, 'Cannot specify a subset list and an exclude samples list! Please use one option or the other.'
        sys.exit(2)

    # load patient sample mapping from clinical files
    reference_set,keep_match = generate_patient_sample_mapping(file_types, sublist, excluded_samples_list)

    # merge the studies
    merge_studies(file_types, reference_set, keep_match, output_directory, study_id, cancer_type, exclude_supp_data, merge_clinical)

# do the main
if __name__ == '__main__':
    main()
