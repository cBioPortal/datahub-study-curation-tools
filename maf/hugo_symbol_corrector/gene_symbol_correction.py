import sys
import os

gene_dict = {}
with open(sys.argv[1],"r") as mp:
	for line in mp:
		line = line.rstrip('\n')
		genes = line.split("\t")
		gene_dict[genes[1]] = genes[0]
	
comments = ""
header = ""
data = ""
replaced_list = {}

with open(sys.argv[2],"r") as file:
	for line in file:
		if line.startswith('#'):
			comments += line
		elif line.startswith('Hugo_Symbol'):
			header += line
		else:
			values = line.split("\t")
			values[0] = values[0].strip('\t')
			if values[0].upper() in gene_dict:
				line = line.replace(values[0],gene_dict[values[0].upper()],1)
				replaced_list[values[0]] = gene_dict[values[0].upper()]
				data += line
			else:
				data += line	

os.remove(sys.argv[2])

new_file = open(sys.argv[2],"w")
new_file.write(comments)
new_file.write(header)
new_file.write(data)
new_file.close()

print("Corrected Gene Symbols:")
for val in replaced_list:
	print(val+"  ->  "+replaced_list[val])