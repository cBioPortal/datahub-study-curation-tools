import os
import sys
import subprocess
import filecmp
import csv
import shutil
import argparse
import datetime

ANNOTATED_MAF_FILE_EXT = '.annotated'
UNANNOTATED_MAF_FILE_EXT = '.unannotated'
HGVSP_SHORT_COLUMN = 'HGVSp_Short'

MAX_ANNOTATION_ATTEMPTS = 10

def get_header(data_file):
    '''
        Returns file header.
    '''
    header = ''
    with open(data_file, "rU") as f:
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
    with open(data_file, "rU") as f:
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
    columns = map(str.strip, header.split('\t'))
    if not ordered_header_columns:
        ordered_header_columns = columns[:]
    if not HGVSP_SHORT_COLUMN in columns:
        print >> ERROR_FILE, 'Could not find %s column in file header - exiting...' % (HGVSP_SHORT_COLUMN)
        sys.exit(1)

    with open(filename, 'rU') as f:
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

def run_genome_nexus_annotator(annotator_jar, input_maf, output_maf, isoform, attempt_num, ordered_header_columns):
    '''
        Calls the Genome Nexus annotator and returns a list of annotated and unannotated records.
        - annotated records:
            - records which were succesfully annotated by Genone Nexus.
        - unannotated records:
            - records which were not successfully annotated by Genome Nexus OR
            - records which were successfully annotated by Genome Nexus but are non-coding so HGVSp_Short column is empty.
    '''
    print('Annotation attempt: %s' % (str(attempt_num)))
    subprocess.call(['java', '-jar', annotator_jar, '--filename', input_maf, '--output-filename', output_maf, '--isoform-override', isoform, '-r','-p','500'])
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
    print('Deleting %s intermediate MAFs:' % (str(len(intermediate_mafs))))
    for maf in intermediate_mafs:
        if os.path.exists(maf):
            print('\tDeleting intermediate MAF "%s" ...' % (maf))
            os.remove(maf)
        else:
            print('\tIntermediate MAF "%s" does not exist, nothing to delete. Continuing...' % (maf))
            
def split_final_output(output_maf):
	unann_data = ''
	ann_data = ''
	
	filters = ["Silent", "Intron", "3'UTR", "5'UTR", "3'Flank", "5'Flank", "IGR"]
	filters = [element.lower() for element in filters]
	
	with open(output_maf,'r') as file:
		for line in file:
			if line.startswith('#'):
				comment_lines = line
			elif line.upper().startswith('HUGO_SYMBOL'):
				header = line
				cols = line.split("\t")
				try:
					hgvsp_index = cols.index("HGVSp_Short")
					varclas_index = cols.index("Variant_Classification")
				except ValueError:
					print("HGVSp_Short/Variant_Classification column is not found in the MAF file. File can't be split. Exiting..")
					sys.exit(1)
			else:
					data = line.split("\t")
					if data[hgvsp_index] == "" and data[varclas_index].lower() not in filters:
						unann_data += line
					else:
						ann_data += line
	os.remove(output_maf)
	return ann_data,unann_data

def genome_nexus_annotator_wrapper(annotator_jar, input_maf, output_maf, isoform):
    '''
        Runs Genome Nexus annotator on input MAF and saves results to designated output MAF.
        If all records are not successfully annotated on first attempt, then script will continue
        running annotator on remaining unannotated records until one of the following conditions is met:
        
        1. The annotator did not successfully annotate
    '''
    attempt_num = 1
    annotated_records,unannotated_records = run_genome_nexus_annotator(annotator_jar, input_maf, output_maf, isoform, attempt_num, [])
    if len(unannotated_records) == 0:
        #print('All records annotated successfully on first attempt - nothing to do. Output file saved to: %s' % (output_maf))
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
            print('ERROR: header for %s does not match the output header in %s!' % (input_unannotated_maf, output_maf))
            sys.exit(2)
        new_annotated_records,unannotated_records = run_genome_nexus_annotator(annotator_jar, input_unannotated_maf, output_reannotated_maf, isoform, attempt_num, ordered_header_columns)

        # if there aren't any new annotated records then no improvement was made - exit while loop
        if len(new_annotated_records) == 0:
            print('Annotation attempt %s did not produce any newly annotated records - saving data to output file: %s' % (str(attempt_num), output_maf))
            break

        output_reannotated_maf_header = get_header(output_reannotated_maf)
        if output_reannotated_maf_header != annotated_file_header:
            print('ERROR: header for %s does not match the header in %s!' % (output_reannotated_maf, output_maf))
            sys.exit(2)
        annotated_records.extend(new_annotated_records)

    # log whether unannotated records remain and max number of attempts allowed has been reached
    if len(unannotated_records) > 0 and attempt_num == MAX_ANNOTATION_ATTEMPTS:
        print('Maximum number of attempts reached for annotating MAF - saving data to output file: %s' % (output_maf))

    # combine annotated and unannotated records and save data to output maf
    compiled_recoords = annotated_records[:]
    compiled_recoords.extend(unannotated_records)
    write_records_to_maf(output_maf, annotated_file_comments, annotated_file_header, compiled_recoords)
    print('Saved compiled annotated and unannotated records to output file: %s' % (output_maf))

    # remove intermediate MAFs
    if len(intermediate_mafs) > 0:
        delete_intermediate_mafs(intermediate_mafs)
    
def main():
    # get command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--input_maf', required = True, help = 'Input maf file name',type = str)
    parser.add_argument('-a', '--annotator_jar_path', required = True, help = 'Path to the annotator jar file.  An example can be found in "/data/curation/annotation/annotator/annotationPipeline-1.0.0.jar" on dashi-dev',type = str)
    parser.add_argument('-i', '--isoform', required = True, help = 'uniprot/mskcc annotation isoform.',type = str)
    parser.add_argument('-an', '--annotated_maf', required = True, help = 'Annotated output maf file name',type = str)
    parser.add_argument('-unan', '--unannotated_maf', required = True, help = 'Unannotated output maf file name',type = str)
    args = parser.parse_args()

    input_maf = args.input_maf
    output_maf = input_maf+"_annotated"
    isoform = args.isoform
    annotator_jar = args.annotator_jar_path
    annotated_file = args.annotated_maf
    unannotated_file = args.unannotated_maf

    genome_nexus_annotator_wrapper(annotator_jar, input_maf, output_maf, isoform)
    
    '''
    Split the final output to two files 1) Annotated 2) Unannotated records
    Records that fall into one of the two criteria are considered annotated: 
      - Non-empty HGVSp_Short
      - HGVSp_Short is empty but the variant_Classification is Silent, Intron, 3'UTR, 5'UTR, 3'Flank, IGR
    If the HGVSp_Short is empty and the variant classification is not one of the above then the records are considered unannotated.
    '''
    
    comments = ''.join(get_comments(output_maf))
    header = get_header(output_maf)
    annotated,unannotated = split_final_output(output_maf)
	
    if len(annotated) != 0 and len(unannotated) == 0:
    	ann_data = comments+header+annotated
    	open(annotated_file,'w').write(ann_data)
    	print('All the records are annotated and the output is saved to file: %s' % (annotated_file))
    elif len(annotated) != 0 and len(unannotated) != 0:
    	ann_data = comments+header+annotated
    	unan_data = comments+header+unannotated
    	open(annotated_file,'w').write(ann_data)
    	open(unannotated_file,'w').write(unan_data)
    	print('Annoatated records are save to: %s and Unannotated records are saved to: %s' % (annotated_file,unannotated_file))
    elif len(annotated) == 0 and len(unannotated) != 0:
    	unan_data = comments+header+unannotated
    	open(unannotated_file,'w').write(unan_data)
    	print('No records were annoated, the output is saved to file: %s' % (unannotated_file))

if __name__ == '__main__':
    main()
