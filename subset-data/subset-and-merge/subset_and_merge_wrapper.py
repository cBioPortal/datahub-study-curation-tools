import sys
import os
import optparse
import merge

filenames_map = {'data_cna.txt':'data_CNA.txt', 'meta_cna.txt':'meta_CNA.txt',
'data_log2_cna.txt':'data_log2CNA.txt', 'meta_log2_cna.txt':'meta_log2CNA.txt',
'data_gene_panel_matrix.txt':'data_gene_matrix.txt', 'meta_gene_panel_matrix.txt':'meta_gene_matrix.txt',
'data_mutations.txt':'data_mutations_extended.txt', 'meta_mutations.txt':'meta_mutations_extended.txt',
'data_sv.txt':'data_SV.txt', 'meta_sv.txt':'meta_SV.txt'}

outputdir_files_to_rename = {}

def interface():
	# get command line stuff
	parser = optparse.OptionParser()
	parser.add_option('-s', '--subset', action = 'store', dest = 'subset')
	parser.add_option('-e', '--excluded-samples', action = 'store', dest = 'excludedsamples')
	parser.add_option('-d', '--output-directory', action = 'store', dest = 'outputdir')
	parser.add_option('-i', '--study-id', action = 'store', dest = 'studyid')
	parser.add_option('-t', '--cancer-type', action = 'store', dest = 'cancertype')
	parser.add_option('-m', '--merge-clinical', action = 'store', dest = 'mergeclinical')
	parser.add_option('-x', '--exclude-supplemental-data', action = 'store', dest = 'excludesuppdata')
	(options, args) = parser.parse_args()
	return (options, args)

def get_key(val):
	for key, value in filenames_map.items():
		if val == value:
			return key

def main(options, args):
	
	# check directories exist
	for study in args:
		if not os.path.exists(study):
			print >> ERROR_FILE, 'Study cannot be found: ' + study
			sys.exit(2)
		study_id = os.path.basename(study)
		
		# go through each study, and rename files to the names accepted by merge script
		files_list = os.listdir(study)
		for file in files_list:
			if file in filenames_map:
				os.rename(study+'/'+file, study+'/'+filenames_map[file])
				outputdir_files_to_rename[study+'/'+filenames_map[file]] = study+'/'+file
			if file.startswith('data_cna_hg19.seg') or file.startswith('meta_cna_hg19_seg') or file.startswith('data_cna_hg18.seg') or file.startswith('meta_cna_hg18_seg'):
				os.rename(study+'/'+file, study+'/'+study_id+'_'+file)
				outputdir_files_to_rename[study+'/'+study_id+'_'+file] = study+'/'+file
				
	# call the main merge and subset script
	merge.main(options, args)
	
	# once the merge is complete, rename files back to their old names in input directories.
	for key in outputdir_files_to_rename:
		os.rename(key, outputdir_files_to_rename[key])
		
	# update the file names in output directory to new naming patterns
	output_directory = options.outputdir
	output_studyid = options.studyid
	for file in os.listdir(output_directory):
		if file in filenames_map.values():
			filename = get_key(file)
			os.rename(output_directory+'/'+file, output_directory+'/'+filename)
		if 'data_cna_hg19' in file or 'meta_cna_hg19_seg' in file or 'data_cna_hg18' in file or 'meta_cna_hg18_seg' in file:
			filename = file.replace(output_studyid+'_', '')
			os.rename(output_directory+'/'+file, output_directory+'/'+filename)

if __name__ == '__main__':
	(options, args) = interface()
	main(options, args)
