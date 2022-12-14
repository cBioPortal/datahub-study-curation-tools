#! /usr/bin/env python

# ------------------------------------------------------------------------------
# Script which converts the file in cBioPortal fusion data format to the 
# structural variant format.
#
# To get usage:
#   python fusion_to_sv_converter.py -h
# ------------------------------------------------------------------------------

import sys
import os
import argparse
import csv
from itertools import groupby
from operator import itemgetter

def write_data(final_mapped_data, header, outfile):
	updated_header = ['Sample_Id', 'Site1_Hugo_Symbol', 'Site1_Entrez_Gene_Id', 'Site2_Hugo_Symbol', 'Site2_Entrez_Gene_Id', 'SV_Status']
	additional_columns = [x for x in header if x not in updated_header and x not in ['index', 'Hugo_Symbol', 'Entrez_Gene_Id', 'Tumor_Sample_Barcode']]
	updated_header.extend(additional_columns)

	with open(outfile, 'w') as sv_data:
		writer = csv.DictWriter(sv_data, fieldnames=updated_header, delimiter='\t', extrasaction='ignore')
		writer.writeheader()
		writer.writerows(final_mapped_data)

def map_fusion_to_sv(fusion_dict):
	final_mapped_data = list()
	
	for id in fusion_dict:
		fusion_column_value = fusion_dict[id][0]['Event_Info']
		
		#Find the fusion partner1 and partner2 genes based on their position in Fusion column. Add the index field.
		for row in range(len(fusion_dict[id])):
			gene = fusion_dict[id][row]['Hugo_Symbol']
			if gene in fusion_column_value: fusion_dict[id][row]['index'] = fusion_column_value.index(gene)
			else: fusion_dict[id][row]['index'] = None
			
		#Sort by the index values
		fusion_dict[id].sort(key= lambda x: (x['index'] is not None, x['index']), reverse=False)
		
		#Group by index values. (Picks the last occurence if duplicated)
		dict1 = {}
		for key, value in groupby(fusion_dict[id], key = itemgetter('index')):
			if key != None:
				new_dict = dict(j for i in value for j in i.items())
				if len(dict1) == 0:
					for k, v in new_dict.items():
						if k == 'Hugo_Symbol': dict1['Site1_Hugo_Symbol'] = v
						elif k == 'Entrez_Gene_Id': dict1['Site1_Entrez_Gene_Id'] = v
						elif k == 'Tumor_Sample_Barcode': dict1['Sample_Id'] = v
						else: dict1[k] = v
						dict1['SV_Status'] = 'SOMATIC'
				else:
					for k, v in new_dict.items():
						if k == 'Hugo_Symbol': dict1['Site2_Hugo_Symbol'] = v
						elif k == 'Entrez_Gene_Id': dict1['Site2_Entrez_Gene_Id'] = v
						else: dict1[k] = v
			if key == None:
				for v in list(value):
					dict2 = {}
					for k1, v1 in v.items():
						if k1 == 'Hugo_Symbol': dict2['Site1_Hugo_Symbol'] = v1
						elif k1 == 'Entrez_Gene_Id': dict2['Site1_Entrez_Gene_Id'] = v1
						elif k1 == 'Tumor_Sample_Barcode': dict2['Sample_Id'] = v1
						else: dict2[k1] = v1
						dict2['SV_Status'] = 'SOMATIC'
						dict2['Site2_Hugo_Symbol'] = ""
						dict2['Site2_Entrez_Gene_Id'] = ""
					if len(dict2) != 0: final_mapped_data.append(dict2)
		if len(dict1) != 0: final_mapped_data.append(dict1)
	return(final_mapped_data)

def file_format_check(header, infile):
	min_required_columns = ['Tumor_Sample_Barcode', 'Fusion', 'Hugo_Symbol', 'Entrez_Gene_Id']
	for element in min_required_columns:
		if element not in header:
			print("The input fusion file: "+infile+" format is invalid. Please refer to https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#fusion-data for the allowed data fields.")
			sys.exit(1)

def interface():
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', '--fusion_file', required = True, help = 'Path to the fusion file',type = str)
	parser.add_argument('-s', '--sv_file', required = True, help = 'Path to save the structural variant file',type = str)
	args = parser.parse_args()
	return args
	
def main(parsed_args):
	
	data = csv.DictReader(open(parsed_args.fusion_file, 'r'), delimiter='\t')

	#Check the input file format - the file should have at least the following fields - Tumor_Sample_Barcode, Fusion, Hugo_Symbol, Entrez_Gene_Id
	file_format_check(data.fieldnames, parsed_args.fusion_file)
	
	#Update fieldnames to map to SV format.
	data.fieldnames = ['Event_Info' if item == 'Fusion' else item for item in data.fieldnames]
	data.fieldnames = ['Site2_Effect_On_Frame' if item == 'Frame' else item for item in data.fieldnames]

	fusion_dict = {}
	for row in data:
		key_val = row['Tumor_Sample_Barcode']+'_'+row['Event_Info']
		if key_val not in fusion_dict:
			fusion_dict[key_val] = list()
			fusion_dict[key_val].append(row)
		else:
			fusion_dict[key_val].append(row)

	sv_data = map_fusion_to_sv(fusion_dict)

	write_data(sv_data, data.fieldnames, parsed_args.sv_file)
 
if __name__ == '__main__':
	parsed_args = interface()
	main(parsed_args)
