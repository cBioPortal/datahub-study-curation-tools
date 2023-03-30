import os
import sys
import argparse

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

def subset_by_ID(study_dir, file, ids_list, output_dir, index_column):
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
				if values[index_column] in ids_list:
					data += line
					
	if data != "":
		print("Writing subset data to "+output_dir+'/'+file+'\n')	
		outfile = open(output_dir+'/'+file, 'w')
		outfile.write(header_data)
		outfile.write(data)
		outfile.close()
	else:
		print('Sample IDs to subset are not present in file. Skipping..')

def subset_by_matrix_type(study_dir, file, sample_ids_list, outdir, data_cols):
	data = ""
	data_cols_len = len(data_cols)
	header_cols = extract_header(study_dir, file).strip('\n').split('\t')
	for value in header_cols:
		if value in sample_ids_list:
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

def subset_by_generic_assay(study_dir, file, sample_ids_list, outdir, data_cols):
	data = ""
	header_cols = extract_header(study_dir, file).strip('\n').split('\t')
	for value in sample_ids_list:
		if value in header_cols:
			ind = header_cols.index(value)
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

def identify_file_type(study_dir, sample_ids_list, patient_ids_list, output_dir):
	data_files = [file for file in os.listdir(study_dir) if file.startswith('data')]
	for file in os.listdir(study_dir):
		if 'data' in file and file not in data_files: data_files.append(file)
	
	for file in data_files:
		header = extract_header(study_dir, file).lower().rstrip('\n').split('\t')
		
		if 'sample_id' in header and 'patient_id' in header and 'timeline' in file:
			index_column = header.index('patient_id')
			subset_by_ID(study_dir, file, patient_ids_list, output_dir, index_column)
		elif 'patient_id' in header and 'sample_id' not in header:
			index_column = header.index('patient_id')
			subset_by_ID(study_dir, file, patient_ids_list, output_dir, index_column)
		elif 'sample_id' in header:
			index_column = header.index('sample_id')
			subset_by_ID(study_dir, file, sample_ids_list, output_dir, index_column)
		elif 'sampleid' in header:
			index_column = header.index('sampleid')
			subset_by_ID(study_dir, file, sample_ids_list, output_dir, index_column)
		elif 'tumor_sample_barcode' in header:
			index_column = header.index('tumor_sample_barcode')
			subset_by_ID(study_dir, file, sample_ids_list, output_dir, index_column)
		elif 'id' in header and 'chrom' in header:
			index_column = header.index('id')
			subset_by_ID(study_dir, file, sample_ids_list, output_dir, index_column)
		elif ('hugo_symbol' in header or 'entrez_gene_id' in header) and 'tumor_sample_barcode' not in header:
			index_cols = find_sample_position(file, header)
			subset_by_matrix_type(study_dir, file, sample_ids_list, output_dir, index_cols)
		elif 'composite.element.ref' in header:
			index_cols = find_sample_position(file, header)
			subset_by_matrix_type(study_dir, file, sample_ids_list, output_dir, index_cols)
		elif 'entity_stable_id' in header:
			index_cols = find_sample_position(file, header)
			subset_by_generic_assay(study_dir, file, sample_ids_list, output_dir, index_cols)


	print("Processing case lists from " + study_dir + "/case_lists ...")
	try:
		os.mkdir(output_dir + "/case_lists")
	except FileExistsError:
		pass

	for cl_fname in os.listdir(study_dir + "/case_lists"):
		subset_case_list(study_dir + "/case_lists", cl_fname, sample_ids_list, output_dir + "/case_lists")


def subset_case_list(dir, file, sample_ids_list, output_dir):
	data = ""
	sample_ids_set = set(sample_ids_list)
	print('Processing file '+file+'...')
	with open(dir + "/" + file) as f:
		for lnum, line in enumerate(f, 1):
			if not line.startswith("case_list_ids: "):
				data += line
			else:
				orig_ids = line.rstrip("\n").split(" ", 1)[1].rstrip("\t").split("\t")

				new_ids = [id for id in orig_ids if id in sample_ids_set]
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
	parser.add_argument('-s', '--sample-list', required = True, help = 'Path to the file with sample IDs', type = str)
	parser.add_argument('-p', '--patient-list', required = True, help = 'Path to the file with patient IDs', type = str)
	parser.add_argument('-path', '--source-path', required = True, help = 'Path to the source directory to subset the data from',type = str)
	parser.add_argument('-dest', '--destination-path', required = True, help = 'Path to the destination directory to save the output to',type = str)
	args = parser.parse_args()

	sample_ids = args.sample_list
	patient_ids = args.patient_list
	study_dir = args.source_path
	output_dir = args.destination_path.rstrip('/')
	
	sample_ids_list = create_ids_list(sample_ids)
	patient_ids_list = create_ids_list(patient_ids)
	
	#Read the input directory, identify the file types to subset on
	identify_file_type(study_dir, sample_ids_list, patient_ids_list, output_dir)
	
if __name__ == '__main__':
	main()