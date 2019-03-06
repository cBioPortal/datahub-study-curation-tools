#! /usr/bin/env python

# ------------------------------------------------------------------------------
# Script which generates missing meta files. 
#
# The following properties must be specified in portal.properties:
#
# google.id
# google.pw
#
# ------------------------------------------------------------------------------

# imports
import os
import sys
import optparse

import gdata.docs.client
import gdata.docs.service
import gdata.spreadsheet.service

import httplib2
from oauth2client import client
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow, argparser

# ------------------------------------------------------------------------------
# globals

# some file descriptors
ERROR_FILE = sys.stderr
OUTPUT_FILE = sys.stdout

# fields in portal.properties
GOOGLE_ID = 'google.id'
GOOGLE_PW = 'google.pw'
IMPORTER_SPREADSHEET = 'portal_importer_configuration'
DATATYPE_WORKSHEET = 'datatypes'

MUTATION_STAGING_GENERAL_PREFIX = "data_mutations"
MUTATION_CASE_LIST_META_HEADER = "sequenced_samples"
MUTATION_CASE_ID_COLUMN_HEADER = "Tumor_Sample_Barcode"
SAMPLE_ID_COLUMN_HEADER = "SAMPLE_ID"
NON_CASE_IDS = frozenset(["MIRNA", "LOCUS", "ID", "GENE SYMBOL", "ENTREZ_GENE_ID", "HUGO_SYMBOL", "LOCUS ID", "CYTOBAND", "COMPOSITE.ELEMENT.REF", "HYBRIDIZATION REF"])
CANCER_STUDY_TAG = "<CANCER_STUDY>"
NUM_CASES_TAG = "<NUM_CASES>"

CANCER_STUDY_IDENTIFIER_PROPERTY = 'cancer_study_identifier'
GENETIC_ALTERATION_TYPE_PROPERTY = 'genetic_alteration_type'
DATATYPE_PROPERTY = 'datatype'
DATA_FILENAME_PROPERTY = 'data_filename'
STABLE_ID_PROPERTY = 'stable_id'
PROFILE_NAME_PROPERTY = 'profile_name'
PROFILE_DESCRIPTION_PROPERTY = 'profile_description'
SHOW_PROFILE_IN_ANALYSIS_TAB_PROPERTY = 'show_profile_in_analysis_tab'
SEG_DESCRIPTION_PROPERTY = 'description'
SEG_REFERENCE_GENOME_ID_PROPERTY = 'reference_genome_id'

# ------------------------------------------------------------------------------
# class definitions

class PortalProperties(object):
    def __init__(self, google_id, google_pw):
        self.google_id = google_id
        self.google_pw = google_pw

class User(object):
    def __init__(self, inst_email, google_email, name, enabled, authorities):
        self.inst_email = inst_email.lower()
        self.google_email = google_email.lower()
        self.name = name
        self.enabled = enabled
        self.authorities = authorities

# ------------------------------------------------------------------------------
# gets a worksheet feed

def get_worksheet_feed(client, ss, ws):

    try:
        ss_id = get_feed_id(client.GetSpreadsheetsFeed(), ss)
        ws_id = get_feed_id(client.GetWorksheetsFeed(ss_id), ws)
        list_feed = client.GetListFeed(ss_id, ws_id)
    except gdata.service.RequestError:
        print >> ERROR_FILE, "There was an error connecting to google."
        sys.exit(0)

    return list_feed
# ------------------------------------------------------------------------------

# logs into google spreadsheet client

def get_gdata_credentials(secrets, creds, scope, force=False):
    storage = Storage(creds)
    credentials = storage.get()

    if credentials.access_token_expired:
        credentials.refresh(httplib2.Http())

    if credentials is None or credentials.invalid or force:
      credentials = run_flow(flow_from_clientsecrets(secrets, scope=scope), storage, argparser.parse_args([]))

    return credentials

def google_login(secrets, creds, user, pw, app_name):

    credentials = get_gdata_credentials(secrets, creds, ["https://spreadsheets.google.com/feeds"], False)
    client = gdata.spreadsheet.service.SpreadsheetsService(additional_headers={'Authorization' : 'Bearer %s' % credentials.access_token})

    # google spreadsheet
    client.email = user
    client.password = pw
    client.source = app_name
    client.ProgrammaticLogin()

    return client

# ------------------------------------------------------------------------------
# given a feed & feed name, returns its id
#
def get_feed_id(feed, name):

    to_return = ''

    for entry in feed.entry:
        if entry.title.text.strip() == name:
            id_parts = entry.id.text.split('/')
            to_return = id_parts[len(id_parts) - 1]

    return to_return

# ------------------------------------------------------------------------------
# parse portal.properties

def get_portal_properties(portal_properties_filename):

    properties = {}
    portal_properties_file = open(portal_properties_filename, 'r')
    for line in portal_properties_file:
        line = line.strip()
        # skip line if its blank or a comment
        if len(line) == 0 or line.startswith('#'):
            continue
        # store name/value
        property = line.split('=')
        # spreadsheet url contains an '=' sign
        if (len(property) != 2):
            print >> ERROR_FILE, 'Skipping invalid entry in property file: ' + line
            continue
        properties[property[0]] = property[1].strip()
    portal_properties_file.close()

    # error check
    if (GOOGLE_ID not in properties or len(properties[GOOGLE_ID]) == 0 or
        GOOGLE_PW not in properties or len(properties[GOOGLE_PW]) == 0):
        print >> ERROR_FILE, 'Missing one or more required properties, please check property file'
        return None

    # return an instance of PortalProperties
    return PortalProperties(properties[GOOGLE_ID],
                            properties[GOOGLE_PW])

# ------------------------------------------------------------------------------
# parse all datatype metadata from worksheet

def parse_gdata_value(value):
    try:
        value = value.strip()
    except AttributeError:
        value = ''
    return value

def get_all_datatype_metadata(worksheet_feed):

    # map that we are returning
    # key is the institutional email address + google (in case user has multiple google ids)
    # of the user and value is a User object
    to_return = {}

    for entry in worksheet_feed.entry:
        datatype = entry.custom['datatype'].text.strip()
        staging_filename = parse_gdata_value(entry.custom['stagingfilename'].text)
        requires_metafile = (parse_gdata_value(entry.custom['requiresmetafile'].text.lower()) == "true")
        meta_filename = parse_gdata_value(entry.custom['metafilename'].text)
        meta_stable_id = parse_gdata_value(entry.custom['metastableid'].text)
        meta_genetic_alteration_type = parse_gdata_value(entry.custom['metageneticalterationtype'].text)
        meta_datatype = parse_gdata_value(entry.custom['metadatatype'].text)
        meta_show_profile_in_analysis_tab = parse_gdata_value(entry.custom['metashowprofileinanalysistab'].text).lower()
        meta_profile_name = parse_gdata_value(entry.custom['metaprofilename'].text)
        meta_profile_description = parse_gdata_value(entry.custom['metaprofiledescription'].text)
        meta_reference_genome_id = parse_gdata_value(entry.custom['metareferencegenomeid'].text)

        to_return[datatype] = {
            'staging_filename':staging_filename,
            'requires_metafile':requires_metafile,
            'meta_filename':meta_filename,
            'meta_stable_id':meta_stable_id,
            'meta_genetic_alteration_type':meta_genetic_alteration_type,
            'meta_datatype':meta_datatype,
            'meta_show_profile_in_analysis_tab':meta_show_profile_in_analysis_tab,
            'meta_profile_name':meta_profile_name,
            'meta_profile_description':meta_profile_description,
            'meta_reference_genome_id':meta_reference_genome_id
        }
    return to_return

# ------------------------------------------------------------------------------
# get case ids from data file to replace "<NUM_CASES>" occurrences in metadata

def get_case_list_from_staging_file(staging_file_full_path):
    case_set = set([])

    # staging file
    with open(staging_file_full_path, 'r') as staging_file:
        id_column_index = 0
        process_header = True
        for line in staging_file:
            line = line.rstrip('\n')
            if line.startswith('#'):
                if line.startswith('#' + MUTATION_CASE_LIST_META_HEADER + ':'):
                    # split will split on any whitespace, tabs or any number of consecutive spaces
                    return line[len(MUTATION_CASE_LIST_META_HEADER)+2:].strip().split()
                continue # this is a comment line, skip it
            values = line.split('\t')

            # is this the header line?
            if process_header:
                # look for MAF file case id column header
                # if this is not a MAF file and header contains the case ids, return here
                # we are assuming the header contains the case ids because SAMPLE_ID_COLUMN_HEADER is missing
                if MUTATION_CASE_ID_COLUMN_HEADER not in values and SAMPLE_ID_COLUMN_HEADER not in values:
                    for potential_case_id in values:
                        # check to filter out column headers other than sample ids
                        if potential_case_id.upper() in NON_CASE_IDS:
                            continue
                        case_set.add(potential_case_id)
                    break # got case ids from header, don't read the rest of the file
                else:
                    # we know at this point one of these columns exists, so no fear of ValueError from index method
                    id_column_index = values.index(MUTATION_CASE_ID_COLUMN_HEADER) if MUTATION_CASE_ID_COLUMN_HEADER in values else values.index(SAMPLE_ID_COLUMN_HEADER)
                process_header = False
                continue # done with header, move on to next line
            case_set.add(values[id_column_index])

    return list(case_set)

# ------------------------------------------------------------------------------
# identify missing meta files and generate them

def write_metafile(datatype, metadata, study_id,  meta_file_full_path, num_cases):
    for prop,value in metadata.items():
        # this is not a property in output meta file, skip
        if prop == 'requires_metafile':
            continue
        metadata[prop] = value.replace(CANCER_STUDY_TAG, study_id).replace(NUM_CASES_TAG, str(num_cases))
    meta_file = open(meta_file_full_path, 'w')
    meta_file.write(CANCER_STUDY_IDENTIFIER_PROPERTY + ': ' + study_id)

    # seg meta file has different properties from other types
    if 'seg' in datatype:
        meta_file.write('\n' + SEG_REFERENCE_GENOME_ID_PROPERTY + ': ' + metadata['meta_reference_genome_id'])
        meta_file.write('\n' + SEG_DESCRIPTION_PROPERTY + ': ' + metadata['meta_profile_description'])
    elif datatype != 'gene-panel-matrix':
        # add remaining common properties
        meta_file.write('\n' + GENETIC_ALTERATION_TYPE_PROPERTY + ': ' + metadata['meta_genetic_alteration_type'])
        meta_file.write('\n' + DATATYPE_PROPERTY + ': ' + metadata['meta_datatype'])
        if not 'clinical' in datatype and not 'time-line' in datatype:
            # add properties for genomic data files
            meta_file.write('\n' + STABLE_ID_PROPERTY + ': ' + study_id + '_' + metadata['meta_stable_id'])
            meta_file.write('\n' + PROFILE_NAME_PROPERTY + ': ' + metadata['meta_profile_name'])
            meta_file.write('\n' + PROFILE_DESCRIPTION_PROPERTY + ': ' + metadata['meta_profile_description'])
            # only add this property if necessary
            if metadata['meta_show_profile_in_analysis_tab'] != '':
                meta_file.write('\n' + SHOW_PROFILE_IN_ANALYSIS_TAB_PROPERTY + ': ' + metadata['meta_show_profile_in_analysis_tab'])
    meta_file.write('\n' + DATA_FILENAME_PROPERTY + ': ' + metadata['staging_filename'])
    meta_file.close()
    print >> OUTPUT_FILE, 'Saved meta file: ' + meta_file_full_path

def generate_missing_metafiles(datatype_metadata, data_directory, study_id, overwrite):
    for datatype,metadata in datatype_metadata.items():
        if '*' in metadata['staging_filename'] or not metadata['requires_metafile']:
            continue        
        # skip if data file doesn't exist
        staging_filename = metadata['staging_filename'].replace(CANCER_STUDY_TAG, study_id)
        staging_file_full_path = os.path.join(data_directory, staging_filename)
        if not os.path.exists(staging_file_full_path):
            continue
        # continue if meta filename already exists
        meta_filename = metadata['meta_filename'].replace(CANCER_STUDY_TAG, study_id)
        meta_file_full_path = os.path.join(data_directory, meta_filename)
        if os.path.exists(meta_file_full_path):
            if not overwrite:
                print >> OUTPUT_FILE, 'Meta file already exists - skipping: ' + meta_filename
                continue
            else:
                print >> OUTPUT_FILE, 'Overwriting existing meta file: ' + meta_filename

        num_cases = len(get_case_list_from_staging_file(staging_file_full_path))
        write_metafile(datatype, metadata, study_id, meta_file_full_path, num_cases)

# ------------------------------------------------------------------------------
# displays program usage (invalid args)

def usage(parser):
    print >> OUTPUT_FILE, parser.print_help()

def main():
    # parse command line options
    parser = optparse.OptionParser()
    parser.add_option('-s', '--secrets-file', action = 'store', dest = 'secrets', help = 'google secrets.json')
    parser.add_option('-c', '--creds-file', action = 'store', dest = 'creds', help = 'oauth creds filename')
    parser.add_option('-p', '--properties-file', action = 'store', dest = 'properties', help = 'properties file')
    parser.add_option('-d', '--data-directory', action = 'store', dest = 'datadir', help = "path to study directory")
    parser.add_option('-i', '--study-id', action = 'store', dest = 'studyid', help = "cancer study id")
    parser.add_option('-o', '--overwrite', action = "store_true", dest = "overwrite", default = False, help = "flag to overwrite existing meta files")

    (options, args) = parser.parse_args()
    
    # process the options
    secrets_filename = options.secrets
    creds_filename = options.creds
    properties_filename = options.properties
    data_directory = options.datadir
    study_id = options.studyid
    overwrite = options.overwrite

    if not secrets_filename or not creds_filename or not properties_filename or not data_directory or not study_id:
        usage(parser)
        sys.exit(2)

    # check existence of file
    if not os.path.exists(properties_filename):
        print >> ERROR_FILE, 'properties file cannot be found: ' + properties_filename
        sys.exit(2)

    if not os.path.exists(data_directory):
        print >> ERROR_FILE, 'data directory cannot be found: ' + data_directory
        sys.exit(2)

    # parse/get relevant portal properties
    print >> OUTPUT_FILE, 'Reading portal properties file: ' + properties_filename
    portal_properties = get_portal_properties(properties_filename)
    if not portal_properties:
        print >> OUTPUT_FILE, 'Error reading %s, exiting' % properties_filename
        return

    # login to google and get spreadsheet feed
    client = google_login(secrets_filename, creds_filename, portal_properties.google_id, portal_properties.google_pw, sys.argv[0])
    worksheet_feed = get_worksheet_feed(client, IMPORTER_SPREADSHEET, DATATYPE_WORKSHEET)
    datatype_metadata = get_all_datatype_metadata(worksheet_feed)
    generate_missing_metafiles(datatype_metadata, data_directory, study_id, overwrite)

if __name__ == '__main__':
    main()