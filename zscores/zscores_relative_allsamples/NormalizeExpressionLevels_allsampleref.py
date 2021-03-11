#! /usr/bin/env python

#
# Copyright (c) 2018 Memorial Sloan Kettering Cancer Center.
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, WITHOUT EVEN THE IMPLIED WARRANTY OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  The software and
# documentation provided hereunder is on an "as is" basis, and
# Memorial Sloan Kettering Cancer Center
# has no obligations to provide maintenance, support,
# updates, enhancements or modifications.  In no event shall
# Memorial Sloan Kettering Cancer Center
# be liable to any party for direct, indirect, special,
# incidental or consequential damages, including lost profits, arising
# out of the use of this software and its documentation, even if
# Memorial Sloan Kettering Cancer Center
# has been advised of the possibility of such damage.
#
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division
import sys
import os
import argparse
import math


HEADER_KEYWORDS = ['Composite.Element.REF','Hugo_Symbol','Entrez_Gene_Id']

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
		val = (item-mu)**2
		sum += val
	var = sum / n
	std = math.sqrt(var)
	return(std)

# calculate mean and std for the samples whose values are not Null or NA (n)
# for rnaseq data, ignore the negative and zero values.
def calculate_mean_std(line, start_position, exclude_zero_negative_values):
	expression_data = line.rstrip('\n').rstrip('\r').split('\t')
	expression_values = expression_data[start_position:]

	filtered_expression_values = []
	if exclude_zero_negative_values:
		for item in expression_values:
			try:
				val = float(item)
				if val > 0:
					filtered_expression_values.append(val)
			except:
				continue
	else:
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
	return(mu,sigma)

# If standard deviation is 0 print NA as the normalized z-score
def zero_std(line, start_position):
	exp_values = line.split('\t')
	z_scores = exp_values[:start_position]
	exp_values = exp_values[start_position:]
	for value in exp_values:
		z_scores.append('NA')
	normalised_scores = '\t'.join(z_scores)
	return(normalised_scores)

# Calculate z_scores for each gene record
def zscores_eachrow(line, mu, sigma, start_position):
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

# Check the file format and sample start_position:
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
	if header[0] not in HEADER_KEYWORDS and header[1] in HEADER_KEYWORDS:
		print("ERROR: The first column must be a gene identifier. It should be either one of Hugo_Symbol, Entrez_Gene_Id or Composite.Element.REF\nExiting..")
		sys.exit(2)
	if header[0] not in HEADER_KEYWORDS and header[1] not in HEADER_KEYWORDS:
		print("ERROR: Expression file must contain at least one of the following: Hugo_Symbol, Entrez_Gene_Id, Composite.Element.REF\nExiting..")
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

def log_transform_data(input_filename, sample_position):
	log_transformed_data = ""
	with open(input_filename, 'r') as infile:
		print("log transforming data..")
		for line in infile:
			if line.startswith('#'):
				log_transformed_data += line
			elif line.startswith('Composite.Element.REF') or line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
				log_transformed_data += line
			else:
				data = line.rstrip('\n').rstrip('\r').split('\t')
				raw_values = data[sample_position:]
				transformed_values = data[:sample_position]

				for val in raw_values:
					try:
						val = float(val)
						if val<=0:
							val = math.log(1,2)
							transformed_values.append(val)
						else:
							val = math.log(val+1,2)
							transformed_values.append(val)
					except:
						transformed_values.append(val)
				log_transformed_data += '\t'.join(map(str,transformed_values))+'\n'

	log_transformed_data = log_transformed_data.rstrip('\n')
	log_transformed_list = log_transformed_data.split('\n')
	return(log_transformed_list)

def z_scores(data_list, sample_position, exclude_zero_negative_values):
	zscores_data = ""
	for line_count,line in enumerate(data_list):
		line = line.rstrip('\n')
		if line.startswith('#'):
			zscores_data +=  line + '\n'
		elif line.startswith('Composite.Element.REF') or line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
			zscores_data +=  line + '\n'
		else:
			mu, sigma = calculate_mean_std(line, sample_position, exclude_zero_negative_values)
			# If standard deviation == 0 print NA as normalized z-score values
			if sigma == 0:
				scores_std = zero_std(line, sample_position)
				zscores_data += scores_std+'\n'
			else:
				sys.stdout.write("\rCalculating zscores on row : %s" % str(line_count))
				normalised_scores = zscores_eachrow(line, mu, sigma, sample_position)
				zscores_data += normalised_scores+'\n'
	return(zscores_data)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--input-data-filename', action = 'store', dest = 'input_data_filename', required = True, help = 'The expression file to normalize')
	parser.add_argument('-o','--output-filename', action = 'store', dest = 'output_filename', required = True, help = 'The file to which normalized data has to be saved')
	parser.add_argument('-l','--log-transform', action = 'store_true', dest = 'log_transform', required = False, help = 'Pass this argument to log transform the data before calculating zscores')
	parser.add_argument('-e','--exclude-zero-negative-values', action = 'store_true', dest = 'exclude_zero_negative_values', required = False, help = 'Pass this argument to exclude zero\'s or negative counts when normalizing the data.')
	
	args = parser.parse_args()

	input_filename = args.input_data_filename
	output_filename = args.output_filename
	log_transform = args.log_transform
	exclude_zero_negative_values = args.exclude_zero_negative_values

	# check if the input file is valid
	if not os.path.isfile(input_filename):
		print("ERROR: The file %s doesn't exist or is not a file" % (input_filename))
		parser.print_help()
		sys.exit(2)
		
	if exclude_zero_negative_values:
		print("Zero's and negative counts will be excluded from the reference population when calculating the zscores.")

	# check if the file format is correct and get the sample position
	sample_position = find_sample_position(input_filename)
	
	# If -l is passed, log transform the data before calculating zscores
	if log_transform:
		log_transformed_list = log_transform_data(input_filename, sample_position)
		zscores_data = z_scores(log_transformed_list, sample_position, exclude_zero_negative_values)
	else:
		data_list = [line.rstrip('\n').rstrip('\r') for line in open(input_filename)]
		zscores_data = z_scores(data_list, sample_position, exclude_zero_negative_values)
	
	outfile = open(output_filename,'w')
	sys.stdout.write("\nWriting to file..")
	outfile.write(zscores_data.rstrip('\n'))
	outfile.close()
	print("\nDONE!")

if __name__ == '__main__':
	main()
