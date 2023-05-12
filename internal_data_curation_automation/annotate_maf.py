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
import sys
import subprocess
import click
import logging

HGVSP_SHORT_COLUMN = 'HGVSp_Short'
ANNOTATED_MAF_FILE_EXT = '.annotated'
UNANNOTATED_MAF_FILE_EXT = '.unannotated'
MAX_ANNOTATION_ATTEMPTS = 10

# set logger
logfilename = 'subset.log'
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler(logfilename)
file_handler.setFormatter(formatter)
logger = logging.getLogger('subset')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

def get_header(data_file):
    '''
        Returns file header.
    '''
    header = ''
    with open(data_file, "r") as f:
        for line in f.readlines():
            if not line.startswith("#"):
                header = line
                break
    return header

def get_comments(data_file):
    '''
        Returns file comments.
    '''
    comments = []
    with open(data_file, "r") as f:
        for line in f.readlines():
            if line.startswith('#'):
                comments.append(line)
            else:
                break
    return comments

def write_records_to_maf(filename, comments, header, records):
    '''
        Writes MAF records to given file.
    '''
    data_file = open(filename, 'w')
    if comments:
        for comment in comments:
            data_file.write(comment)
    data_file.write(header)
    for record in records:
        data_file.write(record)
    data_file.close()

def split_maf_file_records(filename, ordered_header_columns):
    '''
        Splits records from file into list of annotated and unannotated records.
    '''
    annotated_records = []
    unannotated_records = []

    comment_lines = get_comments(filename)
    header = get_header(filename)
    columns = list(map(str.strip, header.split('\t')))
    if not ordered_header_columns:
        ordered_header_columns = columns[:]
    if not HGVSP_SHORT_COLUMN in columns:
        logger.error('Could not find %s column in file header - exiting...' % (HGVSP_SHORT_COLUMN))
        sys.exit(1)

    with open(filename, 'r') as f:
        header_processed = False
        for line in f.readlines():
            if line.startswith('#'):
                continue
            if not header_processed:
                header_processed = True              
                continue
            # now split the records by annotated or unannotated
            data = dict(zip(columns, map(str.strip, line.split('\t'))))
            ordered_data = map(lambda x: data.get(x, ''), ordered_header_columns)
            if data[HGVSP_SHORT_COLUMN] != '':
                annotated_records.append('\t'.join(ordered_data) + '\n')
            else:
                unannotated_records.append('\t'.join(ordered_data) + '\n')
    return annotated_records,unannotated_records

def run_genome_nexus_annotator(annotator_jar, input_maf, output_maf, isoform, attempt_num, ordered_header_columns, post_size):
    '''
        Calls the Genome Nexus annotator and returns a list of annotated and unannotated records.
        - annotated records:
            - records which were succesfully annotated by Genone Nexus.
        - unannotated records:
            - records which were not successfully annotated by Genome Nexus OR
            - records which were successfully annotated by Genome Nexus but are non-coding so HGVSp_Short column is empty.
    '''
    logger.info('Annotation attempt: %s' % (str(attempt_num)))
    subprocess.call(['java', '-jar', annotator_jar, '--filename', input_maf, '--output-filename', output_maf, '--isoform-override', isoform, '-r','-p', post_size])
    annotated_records,unannotated_records = split_maf_file_records(output_maf, ordered_header_columns)
    # split_maf_file_records() orders the data according to the ordered_header_columns if provided -
    # therefore the header in the output MAF from GN may not match the column order of the data values
    # in the returned annotated_records,unannotated_records. This is resolved by overwriting the output_maf
    # with the values of annotated_records
    if ordered_header_columns != []:
        ordered_header = '\t'.join(ordered_header_columns) + '\n'
        write_records_to_maf(output_maf, get_comments(output_maf), ordered_header, annotated_records)
    return annotated_records,unannotated_records

def delete_intermediate_mafs(intermediate_mafs):
    '''
        Deletes intermedite MAFs.
    '''
    logger.info('Deleting %s intermediate MAFs:' % (str(len(intermediate_mafs))))
    for maf in intermediate_mafs:
        if os.path.exists(maf):
            logger.info('\tDeleting intermediate MAF "%s" ...' % (maf))
            os.remove(maf)
        else:
            logger.info('\tIntermediate MAF "%s" does not exist, nothing to delete. Continuing...' % (maf))

def genome_nexus_annotator_wrapper(annotator_jar, input_maf, output_maf, isoform, post_size):
    '''
        Runs Genome Nexus annotator on input MAF and saves results to designated output MAF.
        If all records are not successfully annotated on first attempt, then script will continue
        running annotator on remaining unannotated records until one of the following conditions is met:
        
        1. The annotator did not successfully annotate
    '''
    attempt_num = 1
    annotated_records,unannotated_records = run_genome_nexus_annotator(annotator_jar, input_maf, output_maf, isoform, attempt_num, [], post_size)
    if len(unannotated_records) == 0:
        logger.info('All records annotated successfully on first attempt - nothing to do. Output file saved to: %s' % (output_maf))
        return
    annotated_file_comments = get_comments(output_maf)
    annotated_file_header = get_header(output_maf)
    ordered_header_columns = map(str.strip, annotated_file_header.split('\t'))

    intermediate_mafs = []
    while len(unannotated_records) > 0 and attempt_num <= MAX_ANNOTATION_ATTEMPTS:
        attempt_num += 1
        isoform_extension = '_%s_attempt_%s' % (isoform, str(attempt_num))
        input_unannotated_maf = input_maf + UNANNOTATED_MAF_FILE_EXT + isoform_extension
        output_reannotated_maf = input_maf + ANNOTATED_MAF_FILE_EXT + isoform_extension
        intermediate_mafs.extend([input_unannotated_maf, output_reannotated_maf])
        
        # save unannotated records to new input maf and then run annotator again
        write_records_to_maf(input_unannotated_maf, annotated_file_comments, annotated_file_header, unannotated_records)
        input_unannotated_maf_header = get_header(input_unannotated_maf)
        if input_unannotated_maf_header != annotated_file_header:
            logger.error('Header for %s does not match the output header in %s!' % (input_unannotated_maf, output_maf))
            sys.exit(2)
        new_annotated_records,unannotated_records = run_genome_nexus_annotator(annotator_jar, input_unannotated_maf, output_reannotated_maf, isoform, attempt_num, ordered_header_columns, post_size)

        # if there aren't any new annotated records then no improvement was made - exit while loop
        if len(new_annotated_records) == 0:
            logger.info('Annotation attempt %s did not produce any newly annotated records - saving data to output file: %s' % (str(attempt_num), output_maf))
            break

        output_reannotated_maf_header = get_header(output_reannotated_maf)
        if output_reannotated_maf_header != annotated_file_header:
            logger.error('Header for %s does not match the header in %s!' % (output_reannotated_maf, output_maf))
            sys.exit(2)
        annotated_records.extend(new_annotated_records)

    # log whether unannotated records remain and max number of attempts allowed has been reached
    if len(unannotated_records) > 0 and attempt_num == MAX_ANNOTATION_ATTEMPTS:
        logger.info('Maximum number of attempts reached for annotating MAF - saving data to output file: %s' % (output_maf))

    # combine annotated and unannotated records and save data to output maf
    compiled_recoords = annotated_records[:]
    compiled_recoords.extend(unannotated_records)
    write_records_to_maf(output_maf, annotated_file_comments, annotated_file_header, compiled_recoords)
    logger.info('Saved compiled annotated and unannotated records to output file: %s' % (output_maf))

    # remove intermediate MAFs
    if len(intermediate_mafs) > 0:
        delete_intermediate_mafs(intermediate_mafs)
        
@click.command()
@click.option('-f', '--input-maf', required = True, help = 'Input maf file name')
@click.option('-a', '--annotator-jar', required = True, help = 'Path to the annotator jar file.')
@click.option('-i', '--isoform', required = True, help = 'uniprot/mskcc annotation isoform.')
@click.option('-o', '--output-maf', required = True, help = 'Output maf file name')
@click.option('-p', '--post-size', required = True, help = 'Post size')
     
def main(input_maf, output_maf, isoform, annotator_jar,  post_size):
    logger.info("Annotating MAF: %s " % (input_maf))
    genome_nexus_annotator_wrapper(annotator_jar, input_maf, output_maf, isoform, post_size)
    
if __name__ == '__main__':
    main()
