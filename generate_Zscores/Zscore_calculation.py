import sys
import os
import argparse
import statistics
import re

#Step1: From the header find the sample start and end positions
#Step2: Each gene is normalized separately. 
#		Calculate the mean and standard deviation only for the samples whose expression value is not 'NA' or 'Null'. 
#		n = # of samples with expression values. (not 'NA' or 'Null')

def mean_std(sample_start, values):
	exp_list = []
	print(values[2])
	for x in range(sample_start, len(values)-1):
		if values[x] != 'NA' or values[x] != 'NOT_AVAILABLE' or values[x] is not None  or values[x] != "":
			exp_list.append(float(values[x]))

	mean_val = statistics.mean(exp_list)		
	std_val = statistics.stdev(exp_list,mean_val)
	return mean_val, std_val
		
def main():
	# get command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('-e', '--input_file', required = True, help = 'Expression file or RPPA file for which z-score has to be computed',type = str)
	parser.add_argument('-o', '--output_file', required = True, help = 'Output file name',type = str)
	args = parser.parse_args()
	
	data = ""
	with open(args.input_file,'r') as expf:
		for line in expf:
			line = line.rstrip('\n')
			if line.startswith('#'):
				data += line+'\n'
				continue
			elif line.startswith('Hugo_Symbol'):
				header = line.split('\t')
				sample_end = len(header)-1
				data += line+'\n'
				if header[1] == 'Entrez_Gene_Id':
					sample_start = 2
				else:
					sample_start = 1
			elif line.startswith('Entrez_Gene_Id'):
				header = line.split('\t')
				sample_end = len(header)-1
				data += line+'\n'
				if header[1] == 'Hugo_Symbol':
					sample_start = 2
				else:
					sample_start = 1
			elif line.startswith('Composite.Element.REF'):
				header = line.split('\t')
				sample_end = len(header)-1
				data += line+'\n'
				if header[1] == 'Entrez_Gene_Id':
					sample_start = 2
				else:
					sample_start = 1	
			else:
				if sample_start == 2:
					#values = line.split()
					values = re.split(r'\t+', line)
					#calculate the mean and standard deviation for each gene separately
					mean_val, std_val = mean_std(sample_start,values)
					
					#compute z-scores using formula (r-mu)/sigma where r is the expression value for the sample
					# mu is the mean and sigma is the std deviation
				
					data_line = values[0]+'\t'+values[1]
					
					for x in range(sample_start, len(values)-1):
						if values[x] != 'NA' or values[x] != 'NOT_AVAILABLE' or values[x] is not None or values[x] != "":
							z = (float(values[x]) - mean_val) / std_val
							data_line += '\t'+str(z)
						else:
							data_line += '\tNA'
							
							
					data += data_line + '\n'
				
	print(data)

if __name__ == '__main__':
	main()