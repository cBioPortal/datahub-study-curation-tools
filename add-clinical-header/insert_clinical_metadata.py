import os
import sys
import csv
import optparse

# some file descriptors
ERROR_FILE = sys.stderr
OUTPUT_FILE = sys.stdout

CLINICAL_ATTRIBUTE_METADATA_FILENAME = 'clinical_attributes_metadata.txt'
CLINICAL_ATTRIBUTE_METADATA = {}
PATIENT_CLINICAL_ATTRIBUTES = {}

CLINICAL_PATIENT_FILENAME = 'data_clinical_patient.txt'
CLINICAL_SAMPLE_FILENAME = 'data_clinical_sample.txt'

NULL_VALUES = ['NA', None]


def process_datum(datum):
    try:
        dfixed = datum.strip()
    except AttributeError:
        dfixed = 'NA'

    return 'NA' if dfixed in NULL_VALUES else dfixed


def get_header(filename):
    """ Returns the file header. """
    with open(filename, encoding='utf-8') as f:
        filedata = [x for x in f.read().split('\n') if not x.startswith('#')]
    header = list(map(str.strip, filedata[0].split('\t')))
    return header


def load_clinical_attribute_metadata():
    """ Loads clinical attribute metadata. """
    metadata_header = get_header(CLINICAL_ATTRIBUTE_METADATA_FILENAME)

    with open(CLINICAL_ATTRIBUTE_METADATA_FILENAME, 'r', encoding='utf-8') as metadata_file:
        metadata_reader = csv.DictReader(metadata_file, dialect='excel-tab')
        for line in metadata_reader:
            column = line['NORMALIZED_COLUMN_HEADER']
            attribute_type = line['ATTRIBUTE_TYPE']
            display_name = line['DISPLAY_NAME']
            description = line['DESCRIPTIONS']
            priority = line['PRIORITY']
            datatype = line['DATATYPE']

            PATIENT_CLINICAL_ATTRIBUTES[column] = (attribute_type == 'PATIENT')

            CLINICAL_ATTRIBUTE_METADATA[column] = {
                'DISPLAY_NAME': display_name,
                'DESCRIPTION': description,
                'PRIORITY': priority,
                'DATATYPE': datatype,
                'ATTRIBUTE_TYPE': attribute_type
            }


def get_clinical_header(clinical_filename):
    """ Returns the new file header by clinical file type. """
    new_header = ['PATIENT_ID']
    clinical_file_header = get_header(clinical_filename)

    if 'SAMPLE_ID' in clinical_file_header:
        new_header.append('SAMPLE_ID')

    filtered_header = [hdr for hdr in clinical_file_header if hdr not in new_header]
    new_header.extend(filtered_header)

    return new_header


def get_clinical_header_metadata(header, clinical_filename):
    """Returns the clinical header metadata."""
    display_names = []
    descriptions = []
    datatypes = []
    attribute_types = []
    priorities = []
    is_mixed_attributes = (os.path.basename(clinical_filename) == 'data_clinical.txt')
    for column in header:
        if column not in CLINICAL_ATTRIBUTE_METADATA:
            print(f'Clinical attribute not known: {column}', file=ERROR_FILE)
            print('Please add clinical attribute metadata before continuing. Exiting...', file=ERROR_FILE)
            sys.exit(2)
        attr = CLINICAL_ATTRIBUTE_METADATA[column]
        display_names.append(attr['DISPLAY_NAME'])
        descriptions.append(attr['DESCRIPTION'])
        datatypes.append(attr['DATATYPE'])
        priorities.append(attr['PRIORITY'])
        if is_mixed_attributes:
            attribute_types.append(attr['ATTRIBUTE_TYPE'])

    display_names = '#' + '\t'.join(display_names)
    descriptions = '#' + '\t'.join(descriptions)
    datatypes = '#' + '\t'.join(datatypes)
    priorities = '#' + '\t'.join(priorities)
    attribute_types = '#' + '\t'.join(attribute_types)

    return [display_names, descriptions, datatypes, attribute_types, priorities] if is_mixed_attributes else \
           [display_names, descriptions, datatypes, priorities]


def write_clinical_metadata(clinical_header, clinical_filename):
    """ Writes the clinical datafile with the metadata filtered by attribute type. """
    clinical_metadata = get_clinical_header_metadata(clinical_header, clinical_filename)

    with open(clinical_filename, 'r', encoding='utf-8') as clinical_file:
        clinical_reader = csv.DictReader(clinical_file, dialect='excel-tab')
        filtered_clinical_data = ['\t'.join(clinical_header)]
        for line in clinical_reader:
            line_data = [process_datum(line.get(x, 'NA')) for x in clinical_header]
            filtered_clinical_data.append('\t'.join(line_data))

    output_directory = os.path.dirname(clinical_filename)
    output_filename = os.path.join(output_directory, clinical_filename)

    output_data = clinical_metadata + filtered_clinical_data

    with open(output_filename, 'w', encoding='utf-8') as output_file:
        output_file.write('\n'.join(output_data))

    print(f'Clinical file with metadata written to: {output_filename}')


def insert_clinical_metadata_main(directory : str):
    """ Writes clinical data to separate clinical patient and clinical sample files. """
    clinical_files = find_clinical_files(directory)
    for clinical_filename in clinical_files:
        clinical_header = get_clinical_header(clinical_filename)
        write_clinical_metadata(clinical_header, clinical_filename)


def find_clinical_files(directory):
    return [os.path.join(directory, filename) for filename in os.listdir(directory)
            if 'clinical' in filename and 'meta' not in filename]


def usage():
    print('insert_clinical_metadata.py --directory cancer/study/path', file=OUTPUT_FILE)
    sys.exit(2)


def main():
	# get command line arguments
	parser = optparse.OptionParser()
	parser.add_option('-d', '--directory', action = 'store', dest = 'directory')

	(options, args) = parser.parse_args()
	directory = options.directory

    if not os.path.exists(directory):
        print(f'No such directory: {directory}', file=ERROR_FILE)
        sys.exit(2)

	# load clinical attribute metadata
	load_clinical_attribute_metadata()
	insert_clinical_metadata_main(directory)


	


if __name__ == '__main__':
	main()
