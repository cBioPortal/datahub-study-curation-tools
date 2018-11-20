import sys
import argparse

parser = argparse.ArgumentParser(description = 'This program reads in 2 MAF files and merges them to one.')
parser.add_argument("maf_file1", type=str, help="Input MAF1")
parser.add_argument("maf_file2", type=str, help="Input MAF2")
parser.add_argument("merged_maf", type=str, help="Output merged MAF filename")
args = parser.parse_args()

# Check if columns in the two input maf files are in same order	

def get_header(file):
	try:
		with open(file, "r") as header_source:
			for line in header_source:
				if not line.startswith("#"):
					header = line
					break
		return header
		
	except IOError:
		print args.maf_file1,"file does not exist."
		sys.exit()
		
header1 = get_header(args.maf_file1)
header2 = get_header(args.maf_file2)


if header1 != header2:
	print("You are trying to concatenate MAF files with columns of differnt order. Exiting..")
	sys.exit()

# Concatenate MAF's

with open(args.maf_file1,'r') as file:
	data1 = file.read()

data2 = str()
with open(args.maf_file2,'r') as file:
		for line in file:
			if line.startswith('#') or line.upper().startswith('HUGO_SYMBOL') :
				continue
			else:
				data2 += line

merged_file = open(args.merged_maf,"w")
merged_file.write(data1)
merged_file.write(data2)
merged_file.close()