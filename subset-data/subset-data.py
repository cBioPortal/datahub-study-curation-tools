import os
import sys
import argparse
import re

def extract_header(study_dir, filename):
	with open(study_dir+'/'+filename, 'r') as infile:
		for line in infile:
			if line.startswith('#'): continue
			else: return(line)
			break

def find_sample_position(file, header):
	HEADER_KEYWORDS = ['composite.element.ref','hugo_symbol','entrez_gene_id','entity_stable_id','name','description','url','confidence_statement']
	index_cols = []
	for keyword in header:
		if keyword in HEADER_KEYWORDS:
			index_cols.append(header.index(keyword))
	return(index_cols)

def subset_by_ID(study_dir, file, filter_fn, output_dir, index_column):
	header_cols = extract_header(study_dir, file).strip('\n').split('\t')
	header_data = ""
	data = ""
	#if file in ['data_mutations_manual.txt', 'data_mutations_nonsignedout.txt', 'data_clinical_ddp.txt']:
	#	return(None)
	print('Processing file '+file+'...')
	
	with open(study_dir+'/'+file,'r') as data_file:
		for line in data_file:
			if line.startswith('#') or line.startswith(header_cols[0]):
				header_data += line
			else:
				values = line.strip('\n').split('\t')
				if filter_fn(values[index_column]):
					data += line
					
	if data != "":
		print("Writing subset data to "+output_dir+'/'+file+'\n')	
		outfile = open(output_dir+'/'+file, 'w')
		outfile.write(header_data)
		outfile.write(data)
		outfile.close()
	else:
		print('Sample IDs to subset are not present in file. Skipping..')

def subset_by_matrix_type(study_dir, file, filter_fn, outdir, data_cols):
	data = ""
	data_cols_len = len(data_cols)
	header_cols = extract_header(study_dir, file).strip('\n').split('\t')
	for value in header_cols:
		if filter_fn(value):
			ind = header_cols.index(value)
			data_cols.append(ind)
	if len(data_cols) == data_cols_len:
		return(None)

	print('Processing file '+file+'...')
	with open(study_dir+'/'+file,'r') as data_file:
		for line in data_file:
			if line.startswith('#'):
				data += line
			elif line.startswith(header_cols[0]):
				data += '\t'.join([header_cols[i] for i in data_cols])+'\n'
			else:
				line = line.strip('\n').split('\t')
				if '' in set([line[i] for i in data_cols]) and len(set([line[i] for i in data_cols])) == 2: continue
				else: data += '\t'.join([line[i] for i in data_cols])+'\n'
	
	if data != "":
		print("Writing subsetted data to "+outdir+'/'+file+'\n')		
		with open(outdir+'/'+file, 'w') as datafile:
			datafile.write(data.strip('\n'))
	else:
		print('Sample IDs to subset are not present in file. Skipping..')	

def subset_by_generic_assay(study_dir, file, filter_fn, outdir, data_cols):
	data = ""
	header_cols = extract_header(study_dir, file).strip('\n').split('\t')
	for ind, value in enumerate(header_cols):
		if filter_fn(value):
			data_cols.append(ind)
	
	print('Processing file '+file+'...')		
	with open(study_dir+'/'+file,'r') as data_file:
		for line in data_file:
			if line.startswith('#'):
				data += line
			elif line.startswith(header_cols[0]):
				data += '\t'.join([header_cols[i] for i in data_cols])+'\n'
			else:
				line = line.strip('\n').split('\t')
				data += '\t'.join([line[i] for i in data_cols])+'\n'

	if data != "":
		print("Writing subsetted data to "+outdir+'/'+file+'\n')
		with open(outdir+'/'+file, 'w') as datafile:
			datafile.write(data.strip('\n'))
	else:
		print('Sample IDs to subset are not present in file. Skipping..')

def identify_file_type(study_dir, sample_fliter, patient_fliter, output_dir):
	data_files = [file for file in os.listdir(study_dir) if file.startswith('data')]
	for file in os.listdir(study_dir):
		if 'data' in file and file not in data_files: data_files.append(file)
	
	sample_filter_fn = (lambda x: x in sample_fliter) if type(sample_fliter) is list else (lambda x: sample_fliter.search(x) is not None)
	patient_filter_fn = (lambda x: x in patient_fliter) if type(patient_fliter) is list else (lambda x: patient_fliter.search(x) is not None)

	for file in data_files:
		header = extract_header(study_dir, file).lower().rstrip('\n').split('\t')
		
		if 'sample_id' in header and 'patient_id' in header and 'timeline' in file:
			index_column = header.index('patient_id')
			subset_by_ID(study_dir, file, patient_filter_fn, output_dir, index_column)
		elif 'patient_id' in header and 'sample_id' not in header:
			index_column = header.index('patient_id')
			subset_by_ID(study_dir, file, sample_filter_fn, output_dir, index_column)
		elif 'sample_id' in header:
			index_column = header.index('sample_id')
			subset_by_ID(study_dir, file, sample_filter_fn, output_dir, index_column)
		elif 'sampleid' in header:
			index_column = header.index('sampleid')
			subset_by_ID(study_dir, file, sample_filter_fn, output_dir, index_column)
		elif 'tumor_sample_barcode' in header:
			index_column = header.index('tumor_sample_barcode')
			subset_by_ID(study_dir, file, sample_filter_fn, output_dir, index_column)
		elif 'id' in header and 'chrom' in header:
			index_column = header.index('id')
			subset_by_ID(study_dir, file, sample_filter_fn, output_dir, index_column)
		elif ('hugo_symbol' in header or 'entrez_gene_id' in header) and 'tumor_sample_barcode' not in header:
			index_cols = find_sample_position(file, header)
			subset_by_matrix_type(study_dir, file, sample_filter_fn, output_dir, index_cols)
		elif 'composite.element.ref' in header:
			index_cols = find_sample_position(file, header)
			subset_by_matrix_type(study_dir, file, sample_filter_fn, output_dir, index_cols)
		elif 'entity_stable_id' in header:
			index_cols = find_sample_position(file, header)
			subset_by_generic_assay(study_dir, file, sample_filter_fn, output_dir, index_cols)


	print("Processing case lists from " + study_dir + "/case_lists ...")
	try:
		os.mkdir(output_dir + "/case_lists")
	except FileExistsError:
		pass

	for cl_fname in os.listdir(study_dir + "/case_lists"):
		subset_case_list(study_dir + "/case_lists", cl_fname, sample_filter_fn, output_dir + "/case_lists")


def subset_case_list(dir, file, filter_fn, output_dir):
	data = ""
	print('Processing file '+file+'...')
	with open(dir + "/" + file) as f:
		for lnum, line in enumerate(f, 1):
			if not line.startswith("case_list_ids: "):
				data += line
			else:
				orig_ids = line.rstrip("\n").split(" ", 1)[1].rstrip("\t").split("\t")

				new_ids = [id for id in orig_ids if filter_fn(id)]
				data += "case_list_ids: " + "\t".join(new_ids) + "\n"

	if data != "":
		print("Writing subset data to " + output_dir + "/" + file)
		with open(output_dir + "/" + file, "w") as outfile:
			outfile.write(data)
	else:
		print("Empty subset file " + file + " - skipping..")



def create_ids_list(filename):
	ids_list = set()
	with open(filename, 'r') as ids:
		for line in ids:
			line = line.strip()
			ids_list.add(line)
	return(list(ids_list))

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--sample-list', required = False, help = 'Path to the file with sample IDs', type = str)
	parser.add_argument('-p', '--patient-list', required = False, help = 'Path to the file with patient IDs', type = str)
	parser.add_argument('-sr', '--sample-regex', required = False, help = 'Regular expression to evaluate sample IDs', type = str)
	parser.add_argument('-pr', '--patient-regex', required = False, help = 'Regular expression to evaluate IDs', type = str)
	parser.add_argument('-path', '--source-path', required = True, help = 'Path to the source directory to subset the data from',type = str)
	parser.add_argument('-dest', '--destination-path', required = True, help = 'Path to the destination directory to save the output to',type = str)
	args = parser.parse_args()

	study_dir = args.source_path
	output_dir = args.destination_path.rstrip('/')
	
	# Use list if available, otherwise use regex if available, if neither is available, set subset to None
	sample_subset = create_ids_list(args.sample_list) if (args.sample_list is not None) else (re.compile(args.sample_regex) if (args.sample_regex is not None) else None)
	if sample_subset is None:
		print('Neither sample-list nor sample-regex where provided! Exiting....')
		exit()
	
	patient_subset = create_ids_list(args.patient_list) if (args.patient_list is not None) else (re.compile(args.patient_regex) if (args.patient_regex is not None) else None)
	if patient_subset is None:
		print('Neither patient-list nor patient-regex where provided! Exiting....')
		exit()
	
	identify_file_type(study_dir, sample_subset, patient_subset, output_dir)
	
if __name__ == '__main__':
	main()