import sys
import argparse

def get_header(data_file):
    '''
        Returns file header.
    '''
    header = ''
    with open(data_file, "r") as f:
        for line in f.readlines():
            if not line.startswith("#"):
                header = line
                break
    return header

def main():
	# get command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('-f1', '--input_maf1', required = True, help = 'Input MAF1',type = str)
	parser.add_argument('-f2', '--input_maf2', required = True, help = 'Input MAF2',type = str)
	parser.add_argument('-o', '--merged_maf', required = True, help = 'Merged output MAF file name',type = str)
	args = parser.parse_args()
	
	#Check if the column headers of two input mafs to be merged are same
	header1 = get_header(args.input_maf1)
	header2 = get_header(args.input_maf2)
	
	if header1 != header2:
		print('Header of \''+args.input_maf1+'\' does not match the header in \''+args.input_maf2+'\'\nPlease check if the column headers and the order are the same. Exiting..')
		sys.exit(1)
	
	with open(args.input_maf1,'r') as file:
		data1 = file.read()

	data2 = str()
	with open(args.input_maf2,'r') as file:
		for line in file:
			if line.startswith('#') or line.upper().startswith('HUGO_SYMBOL') :
				continue
			else:
				data2 += line
	
	merged_file = open(args.merged_maf,"w")
	merged_file.write(data1)
	merged_file.write(data2)
	merged_file.close()
	
if __name__ == '__main__':
    main()