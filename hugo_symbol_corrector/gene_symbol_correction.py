import sys
import os

gene_dict = {}
with open(sys.argv[1],"r") as mp:
	for line in mp:
		line = line.rstrip('\n')
		genes = line.split("\t")
		gene_dict[genes[1]] = genes[0]

mp.close()
data = str()

with open(sys.argv[2],"r") as file:
	header = file.readline()
	for line in file:
		values = line.split("\t")
		values[0] = values[0].strip('\t')
		if values[0] in gene_dict:
			line = line.replace(values[0],gene_dict[values[0]])
			data += line
		else:
			data += line

file.close()
os.remove(sys.argv[2])

new_file = open(sys.argv[2],"w")
new_file.write(header)
new_file.write(data)