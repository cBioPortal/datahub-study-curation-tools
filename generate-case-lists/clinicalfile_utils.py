import os
import linecache

# returns header as list of attributes
def get_header(file):
    with open(file, "r") as header_source:
        for line in header_source:
            if not line.startswith("#"):
                return line.rstrip().split('\t')
    return []

# old format is defined as a file containing 5 header lines (PATIENT and SAMPLE attributes in same file)
def is_old_format(file):
    return all([linecache.getline(file, header_line).startswith("#") for header_line in range(1, 6)])

def get_metadata_mapping(file, attribute_line):
    metadata = linecache.getline(file, attribute_line).rstrip().replace("#", "").split('\t')
    attributes = get_header(file)
    return {attributes[i]: metadata[i] for i in range(len(attributes))}

# get existing metadata mappings
def get_description_mapping(file):
    return get_metadata_mapping(file, 2)

def get_datatype_mapping(file):
    return get_metadata_mapping(file, 3)

def get_display_name_mapping(file):
    return get_metadata_mapping(file, 1)

def get_priority_mapping(file):
    return get_metadata_mapping(file, 5 if is_old_format(file) else 4)

def get_attribute_type_mapping(file):
    if is_old_format(file):
        return get_metadata_mapping(file, 4)
    else:
        return {attribute: "NA" for attribute in get_header(file)}

def has_metadata_headers(file):
    return all([linecache.getline(file, header_line).startswith("#") for header_line in range(1, 5)])

def get_description_line(file):
    return linecache.getline(file, 2).rstrip().split('\t')

def get_datatype_line(file):
    return linecache.getline(file, 3).rstrip().split('\t')

def get_display_name_line(file):
    return linecache.getline(file, 1).rstrip().split('\t')

def get_priority_line(file):
    return linecache.getline(file, 5 if is_old_format(file) else 4).rstrip().split('\t')

def get_attribute_type_line(file):
    return linecache.getline(file, 4).rstrip().split('\t') if is_old_format(file) else []

def add_metadata_for_attribute(attribute, all_metadata_lines):
    display_value = attribute.replace("_", " ").title()
    for key, value in zip([
        "DISPLAY_NAME", "DESCRIPTION", "DATATYPE", "ATTRIBUTE_TYPE", "PRIORITY"
    ], [display_value, display_value, "STRING", "SAMPLE", "1"]):
        all_metadata_lines[key].append(value)

def get_all_metadata_lines(file):
    return {
        "DISPLAY_NAME": get_display_name_line(file),
        "DESCRIPTION": get_description_line(file),
        "DATATYPE": get_datatype_line(file),
        "ATTRIBUTE_TYPE": get_attribute_type_line(file),
        "PRIORITY": get_priority_line(file)
    }

def get_all_metadata_mappings(file):
    return {
        "DISPLAY_NAME": get_display_name_mapping(file),
        "DESCRIPTION": get_description_mapping(file),
        "DATATYPE": get_datatype_mapping(file),
        "ATTRIBUTE_TYPE": get_attribute_type_mapping(file),
        "PRIORITY": get_priority_mapping(file)
    }

def write_metadata_headers(metadata_lines, clinical_filename):
    print('\t'.join(metadata_lines["DISPLAY_NAME"]).replace('\n', ''))
    print('\t'.join(metadata_lines["DESCRIPTION"]).replace('\n', ''))
    print('\t'.join(metadata_lines["DATATYPE"]).replace('\n', ''))
    if is_old_format(clinical_filename):
        print('\t'.join(metadata_lines["ATTRIBUTE_TYPE"]).replace('\n', ''))
    print('\t'.join(metadata_lines["PRIORITY"]).replace('\n', ''))

def write_header_line(line, output_file):
    output_file.write(f"#{'\t'.join(line)}\n")

def write_data(file, output_file):
    with open(file, 'r') as source_file:
        for line in source_file:
            if not line.startswith("#"):
                output_file.write(line)