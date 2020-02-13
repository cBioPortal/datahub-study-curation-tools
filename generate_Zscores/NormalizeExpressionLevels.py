import sys
import os
import statistics
import argparse
import math

# Given expression data for a set of samples generate normalized expression values (Independant of unaltered status from CNA file)
#
# Each gene is normalized separately. First, the expression distribution of the gene is
# estimated by calculating the mean and variance of the expression values for samples whose
# values are not Null, NA or NaN
#
# If the gene has samples whose expression values are Null, NaN or 'NA', then its normalized expression is reported as NA.
# Otherwise, for every sample, the gene's normalized expression is reported as
#
# (r - mu)/sigma
#
# where r is the raw expression value, and mu and sigma are the mean and standard deviation
# of the samples with expression values, respectively.
#
# The syntax is simple:
#
# python NormalizeExpressionLevels.py -i <expression_file> -o <output_file>
#
# The output is written onto a file named "output_file"
#
# Any number of columns may precede the data. However, the following must be satisfied:
#
# - the first column provides gene identifiers
#
# Algorithm:
# Input expression file
# concept:
# for each gene:
# 		compute mean and standard deviation for samples ( n = # of samples where expression value is not Null, NA, NaN)
#		for each sample:
#		compute zScore when standard deviation != 0
#		output NA for genes with standard deviation = 0
#

HEADER_KEYWORDS = ['Composite.Element.REF', 'Hugo_Symbol', 'Entrez_Gene_Id']

# Function to calculate Mean
def calculate_mean(data,n):
	sum = 0
	for item in data:
		sum += item
	mu = sum / n
	return(mu)

# Function to calculate Standard Deviation
def calculate_std(data,n,mu):
	sum = 0
	for item in data:
		x = (item-mu)**2
		sum += x
	x1 = sum / n
	std = math.sqrt(x1)
	return(std)

# calculate mean and std for the samples whose values are not Null or NA (n)
def calculate_mean_std(line,start_position):
	expression_data = line.rstrip('\n').rstrip('\r').split('\t')
	expression_values = expression_data[start_position:]

	# Remove strings ('' or 'NA' or 'NaN') and zeros from the expression list
	filtered_expression_values = []
	for item in expression_values:
		try:
			val = float(item)
			filtered_expression_values.append(val)
		except:
			continue

	# Calculate mean and std
	n = len(filtered_expression_values)
	if n <= 1:
		mu = 0
		sigma = 0
	else:
		mu = calculate_mean(filtered_expression_values,n)
		sigma = calculate_std(filtered_expression_values,n,mu)
		#mu = statistics.mean(data)
		#sigma = statistics.stdev(data,mu)
	return(mu,sigma)

# Calculate z_scores
def calculate_z_scores(line,mu,sigma,start_position):
	exp_values = line.split('\t')
	output_list = exp_values[:start_position]
	exp_values = exp_values[start_position:]

	for item in exp_values:
		try:
			val = float(item)
			z_cal = (val - mu) / sigma
			z_cal = round(z_cal,4)
			z_cal = str(z_cal)
			output_list.append(z_cal)
		except:
			output_list.append('NA')

	normalized_exp_values = '\t'.join(output_list)
	return(normalized_exp_values)

#If standard deviation is 0.0? print NA as the normalized z-score
def zero_std(line,start_position):
	exp_values = line.split('\t')
	z_scores = exp_values[:start_position]
	exp_values = exp_values[start_position:]
	for value in exp_values:
		z_scores.append('NA')
	normalised_scores = '\t'.join(z_scores)
	return(normalised_scores)

#Check if the file has normal samples
def check_normals(header):
	normals_suffix = ['10','11','12','13','14']
	cols = header.rstrip('\n').split('\t')
	normal_sample_list = []
	for x in cols:
		ar = x.split('-')
		if ar[len(ar)-1] in normals_suffix:
			normal_sample_list.append(x)
	if len(normal_sample_list) != 0:
		print('ERROR: The file contains the following normal samples')
		for sample in normal_sample_list:
			print(sample)
		print('Remove normals before calculating zscores. Exiting..')
		sys.exit(2)

# Check the file type and sample start_position:
def find_sample_position(infile):
	with open(infile,'r') as data_file:
		for line in data_file:
			if line.startswith('#'):
				continue
			else:
				header = line.rstrip('\n').rstrip('\r').split('\t')
				break

	if header[0] in HEADER_KEYWORDS:
		sample_position = 1
	if header[1] in HEADER_KEYWORDS:
		sample_position = 2
	if header[0] not in HEADER_KEYWORDS and header[1] not in HEADER_KEYWORDS:
		print("ERROR: Expression file header must contain at least one of the following: Composite.Element.REF, Hugo_Symbol, Entrez_Gene_Id\nExiting..")
		sys.exit(2)

	num_cols = len(header)
	sample_count = num_cols - sample_position
	if sample_position >= num_cols:
		print("ERROR: No Samples in expression file\nExiting..")
		sys.exit(2)
	if sample_count <= 1:
		print("ERROR: Expression file contains one or no samples. Cannot calculate zscores.\nExiting..")
		sys.exit(2)
	return(sample_position)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input_file', required = True, help = 'Expression file for which z-score has to be computed',type = str)
	parser.add_argument('-o', '--output_file', required = True, help = 'Output file name',type = str)
	args = parser.parse_args()

	# check if the input file exists
	if not os.path.isfile(args.input_file):
		print("ERROR: The file %s doesn't exist or is not a file" % (args.input_file))
		parser.print_help()
		sys.exit(2)

	# check if the file format is correct and get the sample position
	sample_position = find_sample_position(args.input_file)

	zscores_data = ""
	with open(args.input_file,'r') as exp_file:
		for line_count, line in enumerate(exp_file):
			line = line.rstrip('\n')
			if line.startswith('#'):
				zscores_data =  zscores_data + line + '\n'
			elif line.startswith('Composite.Element.REF') or line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
				zscores_data =  zscores_data + line + '\n'
				#Check if the file has normal samples (Applies to only TCGA studies)
				#check_normals(line) # Wroks for only TCGA studies.
			else:
				mu, sigma = calculate_mean_std(line, sample_position)
				# If standard deviation == 0 print NA as normalized values
				if sigma == 0:
					scores_std = zero_std(line,sample_position)
					zscores_data += scores_std+'\n'
				else:
					sys.stdout.write("\rNormalizing row : %s" % str(line_count))
					normalised_scores = calculate_z_scores(line,mu,sigma,sample_position)
					zscores_data += normalised_scores+'\n'

	outfile = open(args.output_file,'w')
	outfile.write(zscores_data.rstrip('\n'))
	outfile.close()
	print("\nDONE!\n")

if __name__ == '__main__':
	main()
