import argparse
import sys

parser = argparse.ArgumentParser(description = 'This program reads in a MAF file and splits it to annotated and unannotated tables based on the HGVSp_Short column')
parser.add_argument("original_maf", type=str, help="Original MAF to split")
parser.add_argument("annotated_maf", type=str, help="Annotated MAF filename")
parser.add_argument("unannotated_maf", type=str, help="Unannotated MAF filename")
args = parser.parse_args()
	
ann_data = str()
unann_data = str()

try:
	with open(args.original_maf,'r') as file:
		header = file.readline()
		head_cols = header.split("\t")
		hgvsp_index = head_cols.index("HGVSp_Short")
		for line in file:
			cols = line.split("\t")
			if cols[hgvsp_index] != "":
				ann_data += line
			else:
				unann_data += line
except IOError:
	print args.original_maf,"file does not exist."
	sys.exit()
	
			
ann_file = open(args.annotated_maf,"w")
ann_file.write(header)
ann_file.write(ann_data)
ann_file.close()

unann_file = open(args.unannotated_maf,"w")
unann_file.write(header)
unann_file.write(unann_data)
unann_file.close()
