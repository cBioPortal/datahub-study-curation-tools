import sys
import os
import argparse
import requests

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-o', '--output_filename', required = True, help = 'Gene panel json output file path.', type = str)
	args = parser.parse_args()
	genepanel_json = args.output_filename
	
	service_url = "http://cbioportal.org/api/gene-panels?pageSize=9999999"
	response = requests.get(service_url)
	gene_panels = []
	for data_item in response.json():
		panel = {}
		gene_panel_id = data_item['genePanelId']
		gene_panel_url = service_url.strip("?pageSize=9999999")+'/'+gene_panel_id+"?pageSize=9999999"
		response = requests.get(gene_panel_url).json()
		panel['description'] = response['description']
		panel['genes'] = response['genes']
		panel['genePanelId'] = response['genePanelId']
		gene_panels.append(panel)
	json_string = str(gene_panels)
	json_string = json_string.replace("\'","\"")
	json_string = json_string.replace(": \"",":\"")
	json_string = json_string.replace("that\"s","that\'s")
	
	outfile = open(genepanel_json,'w')
	outfile.write(json_string+'\n')
	outfile.close()
		
		
if __name__ == '__main__':
	main()