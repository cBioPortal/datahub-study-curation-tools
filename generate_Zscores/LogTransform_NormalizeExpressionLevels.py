import sys
import os
import argparse
import math

# Calculate the log base 2 of the expression values.
#CONDITIONS TO HANDLE NEGATIVE DATA:
#1. If the value(x) is <= 0 replace the value to 0 and then calculate the log of all values as by adding +1 as log(x+1)
#ex. if raw value is -1, the log transform would be log(0+1)
#    if the value is 0, the log transform would be log(0+1)
#    if the value is 1, the log transform would be log(1+1)

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
			if val != 0:
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

#If standard deviation is 0.0? print NA as the normalized z-score
def zero_std(line,start_position):
	exp_values = line.split('\t')
	z_scores = exp_values[:start_position]
	exp_values = exp_values[start_position:]
	for value in exp_values:
		z_scores.append('NA')
	normalised_scores = '\t'.join(z_scores)
	return(normalised_scores)

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
    parser.add_argument('-i','--input-expression-file', action = 'store', dest = 'input_expression_file', required = True, help = 'The expression filename to log transform')
    parser.add_argument('-o','--output-filename', action = 'store', dest = 'output_filename', required = True, help = 'The filename to which log transformed data has to be saved')
    args = parser.parse_args()

    input_filename = args.input_expression_file
    output_filename = args.output_filename

    # check if the input file exists
    if not os.path.isfile(input_filename):
        print("ERROR: The file %s doesn't exist or is not a file" % (input_filename))
        parser.print_help()
        sys.exit(2)

    # check if the file format is correct and get the sample position
    sample_position = find_sample_position(input_filename)

    log_transformed_data = ""
    with open(input_filename, 'r') as infile:
        print("log transforming data..")
        for line in infile:
            if line.startswith('#'):
                log_transformed_data += line
            elif line.startswith('Composite.Element.REF') or line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
                log_transformed_data += line
            else:
                cols = line.rstrip('\n').rstrip('\r').split('\t')
                scores = cols[sample_position:]
                transformed_cols = []
                transformed_cols.extend(cols[:sample_position])

                for val in scores:
                    try:
                        val = float(val)
                        if val<=0:
                            val = math.log(1,2)
                            transformed_cols.append(val)
                        else:
                            val = math.log(val+1,2)
                            transformed_cols.append(val)
                    except:
                        transformed_cols.append(val)
                data_line = '\t'.join(map(str,transformed_cols))
                log_transformed_data += data_line+'\n'

    log_transformed_data = log_transformed_data.rstrip('\n')
    log_transformed_list = log_transformed_data.split('\n')

    zscores_data = ""
    for line_count,line in enumerate(log_transformed_list):
        line = line.rstrip('\n')
        if line.startswith('#'):
            zscores_data =  zscores_data + line + '\n'
        elif line.startswith('Composite.Element.REF') or line.startswith('Hugo_Symbol') or line.startswith('Entrez_Gene_Id'):
            zscores_data =  zscores_data + line + '\n'
        else:
        	mu, sigma = calculate_mean_std(line, sample_position)
        	# If standard deviation == 0 print NA as normalized values
        	if sigma == 0:
        		scores_std = zero_std(line,sample_position)
        		zscores_data += scores_std+'\n'
        	else:
        		sys.stdout.write("\rCalculating zscores on row : %s" % str(line_count))
        		normalised_scores = calculate_z_scores(line,mu,sigma,sample_position)
        		zscores_data += normalised_scores+'\n'

    outfile = open(output_filename,'w')
    outfile.write(zscores_data.rstrip('\n'))
    outfile.close()
    print("\nDONE!\n")

if __name__ == '__main__':
    main()
