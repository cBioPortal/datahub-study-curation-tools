import os
import sys
import argparse
import requests
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--outfile-dir', action = 'store', dest = 'outfile_dir', required = False, help = 'Path to the directory in which the json files should be written')
    args = parser.parse_args()
    outfile_dir = args.outfile_dir

    API_LIST = ['cancer-types','genes','gene-panels','genesets']
    server_url = "https://cbioportal.org"

    for api_name in API_LIST:
        if outfile_dir:
            outfile = open(outfile_dir+'/'+api_name+'.json','w')
        else:
            outfile = open(api_name+'.json','w')

        service_url = server_url + '/api/' + api_name + '?pageSize=9999999'
        print("Requesting %s from portal at '%s'" % (api_name, server_url))
        response = requests.get(service_url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise ConnectionError('Failed to fetch metadata from the portal at [{}]'.format(service_url)) from e

        #Gene list for each panel from /gene-panels/{genePanelId} (for identifying off-panel variants)
        if api_name == 'gene-panels':
            gene_panels = []
            for data_item in response.json():
                gene_panel_id = data_item['genePanelId']
                print(gene_panel_id)
                gene_panel_url = service_url.strip("?pageSize=9999999") + '/' + gene_panel_id
                print(gene_panel_url)
                response = requests.get(gene_panel_url).json()
                panel = json.dumps(response)
                gene_panels.append(json.loads(panel))
            json.dump(gene_panels,outfile)
        else:
            json.dump(response.json(),outfile)

if __name__ == '__main__':
    main()
