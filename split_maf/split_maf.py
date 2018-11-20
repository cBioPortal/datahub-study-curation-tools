import argparse
import sys

parser = argparse.ArgumentParser(description = 'This program reads in a MAF file and splits it to annotated and unannotated tables based on the HGVSp_Short column')
parser.add_argument("original_maf", type=str, help="Original MAF to split")
parser.add_argument("annotated_maf", type=str, help="Annotated MAF filename")
parser.add_argument("unannotated_maf", type=str, help="Unannotated MAF filename")
args = parser.parse_args()

comment_lines = str()
ann_data = str()
unann_data = str()

# Checks:
# 1. For comment lines
# 2. If HGVSp_Short column exists 

try:
	with open(args.original_maf,'r') as file:
		for line in file:
			if line.startswith('#'):
				comment_lines += line
			elif line.upper().startswith('HUGO_SYMBOL'):
				header = line
				cols = line.split("\t")
				try:
					hgvsp_index = cols.index("HGVSp_Short")
				except ValueError:
					print("HGVSp_Short column is not found in the MAF file. Exiting..")
					sys.exit()
			else:
					data = line.split("\t")
					if data[hgvsp_index] != "":
						ann_data += line
					else:
						unann_data += line
			
except IOError:
	print args.original_maf,"file does not exist."
	sys.exit()
	
# Print annotated and unannotated rows to two files			
			
ann_file = open(args.annotated_maf,"w")
ann_file.write(comment_lines)
ann_file.write(header)
ann_file.write(ann_data)
ann_file.close()

unann_file = open(args.unannotated_maf,"w")
unann_file.write(comment_lines)
unann_file.write(header)
unann_file.write(unann_data)
unann_file.close()

