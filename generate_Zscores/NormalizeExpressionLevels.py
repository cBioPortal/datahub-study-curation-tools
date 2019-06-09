import sys
import os
import statistics
import argparse

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
#


# calculate mean and std for the samples whose values are not Null or NA (n)
def calculate_mean_std(line,start_position):
	data = line.split('\t')
	data = data[start_position:]
	# Remove strings '' or 'NA' from list 
	for elem in data:
		if elem == '' or elem == 'NA' or elem == 'NaN':
			data.pop(data.index(elem))
	# Convert string list to floats
	for index, item in enumerate(data):
		data[index] = float(item)
	# Calculate mean and std
	n = len(data)
	mu = statistics.mean(data)
	sigma = statistics.stdev(data,mu)
	return(mu,sigma)

# Calculate z_scores 	
# TODO: what if standard deviation is 0.0?
def calculate_z_scores(line,mu,sigma,start_position):
	exp_values = line.split('\t')
	z_scores = exp_values[:start_position]
	exp_values = exp_values[start_position:]
	for value in exp_values:
		if value == '' or value == 'NA' or value == 'NaN':
			z_scores.append('NA')
		else:
			try:
				value = float(value)
				z_cal = (value - mu) / sigma
				z_cal = str(z_cal)
				z_scores.append(z_cal)
			except ValueError:
				print("Expression value is a String. Neither Null or NA")
	normalised_scores = '\t'.join(z_scores)
	return(normalised_scores)

# Check the file type and sample start_position:	
def sample_start_position(infile):
	with open(infile,'r') as data_file:
		for line in data_file:
			if line.startswith('#'):
				continue
			else:
				header = line
				break
	if header.startswith('Composite.Element.REF'):
		start_position = 1
	elif header.startswith('Hugo_Symbol'):
		data = header.split('\t')
		if data[1] == 'Entrez_Gene_Id':
			start_position = 2
		else:
			start_position = 1
	elif header.startswith('Entrez_Gene_Id'):
		data = header.split('\t')
		if data[1] == 'Hugo_Symbol':
			start_position = 2
		else:
			start_position = 1
	else:
		print("Expression file header must contain at least one of the following: Composite.Element.REF, Hugo_Symbol, Entrez_Gene_Id\nExiting..")
		sys.exit(1)
	num_cols = len(header.split('\t'))
	if start_position >= num_cols:
		print("No Sample ID in expression file\nExiting..")
		sys.exit(1)
	return(start_position)

def main():
	# get command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input_file', required = True, help = 'Expression file for which z-score has to be computed',type = str)
	parser.add_argument('-o', '--output_file', required = True, help = 'Output file name',type = str)
	args = parser.parse_args()
	
	# Check the file type and sample start_position
	# The first column should provide gene identifiers else exit
	start_position = sample_start_position(args.input_file)
	
	outfile = open(args.output_file,'w')
	with open(args.input_file,'r') as exp_file:
		for line in exp_file:
			line = line.rstrip('\n')
			if line.startswith('Composite.Element.REF') or line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
				header = line
				outfile.write(header+'\n')
			else:
				mu, sigma = calculate_mean_std(line, start_position)
				# If standard deviation == 0 skip the normalization and the row
				if sigma == 0:
					continue
				else:
					normalised_scores = calculate_z_scores(line,mu,sigma,start_position)
					outfile.write(normalised_scores+'\n')
			
if __name__ == '__main__':
	main()