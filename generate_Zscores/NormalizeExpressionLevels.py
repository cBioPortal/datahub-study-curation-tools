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
#		output NA for genes with standard deviation = 0
#


# calculate mean and std for the samples whose values are not Null or NA (n)
def calculate_mean_std(line,start_position,line_count):
	data = line.split('\t')
	data = data[start_position:]
	# Remove strings '' or 'NA' from list 
	for elem in data:
		if elem == '' or elem == 'NA' or elem == 'NaN':
			data.pop(data.index(elem))
	# Convert string list to floats
	for index, item in enumerate(data):
		try:
			data[index] = float(item)
		except Exception:
			print("\nRow ",line_count," has a non-numeric expression value '"+item+"'\nAllowed non-numeric values are '', 'NA' and 'NaN'")
			sys.exit(1)
	# Calculate mean and std
	n = len(data)
	mu = statistics.mean(data)
	sigma = statistics.stdev(data,mu)
	return(mu,sigma)

# Calculate z_scores 	
def calculate_z_scores(line,mu,sigma,start_position,line_count):
	exp_values = line.split('\t')
	output_list = exp_values[:start_position]
	exp_values = exp_values[start_position:]
	for value in exp_values:
		if value == '' or value == 'NA' or value == 'NaN':
			output_list.append('NA')
		else:
			try:
				value = float(value)
				z_cal = (value - mu) / sigma
				z_cal = round(z_cal,4)
				z_cal = str(z_cal)
				output_list.append(z_cal)
			except Exception:
				print("\nRow ",line_count," has a non-numeric expression value '"+value+"'\nAllowed non-numeric values are '', 'NA' and 'NaN'")
				sys.exit(1)
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

# Check the file type and sample start_position:	
def find_sample_startpos(infile):
	with open(infile,'r') as data_file:
		for line in data_file:
			line = line.rstrip('\n')
			if line.startswith('#'):
				continue
			else:
				header = line
				break
	
	header_keywords = ['Composite.Element.REF', 'Hugo_Symbol', 'Entrez_Gene_Id']
	if header.startswith(header_keywords[0]):
		start_position = 1
	elif header.startswith(header_keywords[1]):
		data = header.split('\t')
		if data[1] == header_keywords[2]:
			start_position = 2
		else:
			start_position = 1
	elif header.startswith(header_keywords[2]):
		data = header.split('\t')
		if data[1] == header_keywords[1]:
			start_position = 2
		else:
			start_position = 1
	else:
		print("Expression file header must contain at least one of the following: Composite.Element.REF, Hugo_Symbol, Entrez_Gene_Id\nExiting..")
		sys.exit(1)
	num_cols = len(header.split('\t'))
	sample_count = num_cols - start_position
	if start_position >= num_cols:
		print("No Sample data in expression file\nExiting..")
		sys.exit(1)
	if sample_count <= 1:
		print("Expression file contains just one sample. Cannot calculate Standard Deviation.\nExiting..")
		sys.exit(1)
	return(start_position)

def main():
	# get command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input_file', required = True, help = 'Expression file for which z-score has to be computed',type = str)
	parser.add_argument('-o', '--output_file', required = True, help = 'Output file name',type = str)
	args = parser.parse_args()
	
	# Check the file type and find the start_position of sample
	# The first column should provide gene identifiers else exit
	start_position = find_sample_startpos(args.input_file)
	
	outfile = open(args.output_file,'w')
	with open(args.input_file,'r') as exp_file:
		comments = ''
		output_data = ''
		for line_count, line in enumerate(exp_file):
			line = line.rstrip('\n')
			if line.startswith('#'):
				comments += line+'\n'
			elif line.startswith('Composite.Element.REF') or line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
				header = line
			else:
				mu, sigma = calculate_mean_std(line, start_position,line_count)
				# If standard deviation == 0 print NA as normalized values
				if sigma == 0:
					scores_std = zero_std(line,start_position)
					output_data += scores_std+'\n'
				else:
					sys.stdout.write('\rNormalizing row : '+str(line_count))
					normalised_scores = calculate_z_scores(line,mu,sigma,start_position,line_count)
					output_data += normalised_scores+'\n'
	print("\nDONE!\n")
	outfile.write(comments+'\n')
	outfile.write(header+'\n')
	outfile.write(output_data)
			
if __name__ == '__main__':
	main()