import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--mapping", dest='mapping', help="This is the mapping file path")
parser.add_argument("--hugo", dest='hugo', help="This is the file path which contains all the hugo symbols that needs to be replaced")
args = parser.parse_args()


if __name__ == "__main__":
	gene_dict = {} # this has the keys of all the gene mappings
	header_dict = {} # this has all the keys of column names and their respective array ids
 
	# reading the mapping file and saving to dict
	with open(args.mapping ,"r") as mp:
		for line in mp:
			line = line.rstrip('\n')
			genes = line.split("\t")
			gene_dict[genes[1]] = genes[0]
	

	comments = ""
	data = ""
	columns = ""
	replaced_list = {}

	# reading the hugo symbols file
	with open(args.hugo ,"r") as file:
		counter = 0
		for i, line in enumerate(file):
			# this condition is to get all the column names and save it in header_dict  
			if i == 0:
				columns += line
				header = line.split("\t") 
				for i, head in enumerate(header):
					head = head.rstrip('\n')
					header_dict[head] = i
				continue
			if line.startswith('#'):
				comments += line
			else:
				replace_line = None
				# looping through the required column names
				for gene_name in ["Site1_Hugo_Symbol", "Site2_Hugo_Symbol", "Hugo_Symbol", "Composite.Element.REF"]: # Add more column names of the hugo symbols that you want to convert
					# check whether the column name exists
					gene = header_dict.get(gene_name)
					if gene is None:
						continue
				
					values = line.split("\t")
					values[gene] = values[gene].strip('\t')
					
					if gene_name == "Composite.Element.REF":
						values[gene] =  values[gene].split("|")
						for gne in values[gene]:
							if gne.upper() in gene_dict:
								replace_line = line.replace(gne,gene_dict[gne.upper()],1)
								replaced_list[gne] = gene_dict[gne.upper()]
								data += replace_line
					else:
						# if the gene name exists in the column replace it with the mappings 
						if values[gene].upper() in gene_dict:
							replace_line = line.replace(values[gene],gene_dict[values[gene].upper()],1)
							replaced_list[values[gene]] = gene_dict[values[gene].upper()]
							data += replace_line

				if not replace_line:
					data += line
				else:
					pass
						

	os.remove(args.hugo)
	new_file = open(args.hugo ,"w")
	new_file.write(comments)
	new_file.write(columns)
	new_file.write(data)
	new_file.close()

	print("Corrected Gene Symbols:")
	for val in replaced_list:
		print(val+"  ->  "+replaced_list[val])