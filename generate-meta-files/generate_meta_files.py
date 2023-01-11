import argparse
import glob
import pandas as pd
import sys

metadata = ['type_of_cancer: gbm\n'
'name: The name of the cancer study,e.g., "Breast Cancer (Jones Lab 2013)"\n'
'description:  Description of the study.\n'
'pmid: eg.,33577785\n'
'citation: A relevant citation, e.g., "TCGA, Nature 2012".\n']


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
                    prog = 'metafile generator',
                    description = 'Generate metafiles for datafiles')

	parser.add_argument('-d', '--directory', help="the folder that has all the study data files")
	parser.add_argument('-s', '--study_id', help="name of the cancer_study_identifier")
	parser.add_argument('-m', '--meta_datatype_file', help="datatypes.txt file path")

# parse arguments
args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
	
# read 2 types of file formats
types = (f'{args.directory}/data_*.txt', f'{args.directory}/data_*.seg') # the tuple of file types
files_grabbed = []

# read from the datatype.txt in pandas
datatype_df = pd.read_csv(args.meta_datatype_file, sep="\t")

# these are the required columns to create the meta_*.txt file
cols = ["DATA_FILENAME", "META_GENERIC_ASSAY_TYPE", "META_GENERIC_ENTITY_meta_PROPERTIES",
       'META_STABLE_ID', 'META_GENETIC_ALTERATION_TYPE', 'META_DATATYPE',
       'META_SHOW_PROFILE_IN_ANALYSIS_TAB', 'META_PROFILE_NAME',
       'META_PROFILE_DESCRIPTION', 'META_REFERENCE_GENOME_ID']

# looping throught the existing directory to check for files that needs to have meta_*.txt 
for files in types:
	files_grabbed.extend(glob.glob(files))

filenames = []
for file in files_grabbed:
	filename = file.split("/")[-1].split(".")[0].split("data_")[-1]
	filenames.append(filename)

# Main logic
for values in datatype_df["datatype"]:
	emp = "" # appending to empty string
	cc = datatype_df.loc[datatype_df["datatype"] == values] # checking the row and getting all the row values of each column
	for col in cols:
		xx = list(cc[col])[-1]
		if str(xx) != "nan": # check if NAN values are present
			ss = col.replace("META_", '').lower() # then Replacing Meta_ to ''
			append_string = f"{ss}: {xx}\n"
			emp += append_string  # appending to the empty string
		else: 
			pass

	# checking the file exists in directory from the pandas dataframe
	file = list(cc["DATA_FILENAME"])[-1]
	file = file.replace("data_", "").split(".")[0]

	# if file exists we are creating the meta_*.txt
	if file in filenames:
		file_path = f"{args.directory}/meta_{file}.txt"
		with open(file_path, "w") as ff:
			ff.writelines(f"cancer_study_identifier: {args.study_id}\n")
			ff.writelines(emp)
		
		file_path = f"{args.directory}/meta_study.txt"
		with open(file_path, 'w') as meta_study:
			meta_study.writelines(f"cancer_study_identifier: {args.study_id}\n")
			for val in metadata: meta_study.write(val)
