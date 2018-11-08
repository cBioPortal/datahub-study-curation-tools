import sys
import argparse

parser = argparse.ArgumentParser(description = 'This program reads in 2 MAF files and merges them to one.')
parser.add_argument("maf_file1", type=str, help="Input MAF1")
parser.add_argument("maf_file2", type=str, help="Input MAF2")
parser.add_argument("merged_maf", type=str, help="Output merged MAF filename")
args = parser.parse_args()

file_header = list();

# Check if columns in the two input maf files are in same order	

try:
	with open(args.maf_file1,'r') as file:
		header = file.readline()
		file_header.append(header)
except IOError:
	print args.maf_file1,"file does not exist."
	sys.exit()
	
try:
	with open(args.maf_file2,'r') as file:
		header = file.readline()
		file_header.append(header)
except IOError:
	print args.maf_file2,"file does not exist."
	sys.exit()

header1 = file_header[0]
header2 = file_header[1]

if header1 != header2:
	print("You are trying to concatenate MAF files with columns of differnt order. Exiting..")
	sys.exit()

# Concatenate multiple MAF's

all_data = str()

with open(args.maf_file1,'r') as file:
	header = file.readline()
	for lines in file:
		all_data += lines

with open(args.maf_file2,'r') as file:
	header = file.readline()
	for lines in file:
		all_data += lines

merged_file = open(args.merged_maf,"w")
merged_file.write(header1)
merged_file.write(all_data)
merged_file.close()

