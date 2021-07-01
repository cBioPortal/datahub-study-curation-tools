import csv
import pandas as pd
import os
import sys
import argparse
import ntpath
import requests
import json
import re
import urllib.parse

def generate_dict(key, value, dictionary):
    if not pd.isnull(key):
        genes = re.split(' |; |;', key)
        for gene in genes:
            dictionary[gene] = value

def get_protein_length_from_uniprot(uniprot_file, gene_name_to_length_dict_primary, gene_name_to_length_dict_synonym):
    df_uniprot_gene_name_with_protein_length = pd.read_csv(uniprot_file, sep='\t')
    df_uniprot_gene_name_with_protein_length.apply(lambda row: generate_dict(row['Gene names  (primary )'], row['Length'], gene_name_to_length_dict_primary), axis=1)
    df_uniprot_gene_name_with_protein_length.apply(lambda row: generate_dict(row['Gene names  (synonym )'], row['Length'], gene_name_to_length_dict_synonym), axis=1)

def get_protein_length_from_mapping_sheet(mapping_file, gene_name_to_length_dict):
    df_mapping_per_gene = pd.read_csv(mapping_file, sep='\t')
    df_mapping_per_gene.apply(lambda row: generate_dict(row['Gene_Symbol'], row['uniprot_protein_length'], gene_name_to_length_dict), axis=1)

def look_up_in_genome_nexus(gene, genome_nexus_domain):
    gene = gene.strip()
    gn_request = genome_nexus_domain + '/ensembl/canonical-transcript/hgnc/' + urllib.parse.quote(gene, safe='') + '?isoformOverrideSource=uniprot'
    # get json response from genome nexus
    return requests.get(gn_request)    

def update_file(args):
    input_file = args.input_file
    uniprot_file = args.uniprot_file or os.getcwd() + "/uniprot_gene_name_with_protein_length.tab"
    output_file = args.output_file or os.path.dirname(input_file) + "/output_" + ntpath.basename(input_file)
    source = args.source or "all"
    genome_nexus_domain = args.genome_nexus_domain or "https://www.genomenexus.org"
    mapping_file = args.mapping_file or os.getcwd() + "/mapping_per_gene.tsv"

    # write files
    input = open(input_file, 'rt')
    output = open(output_file, 'wt')

    for row in input.readlines():
        split_row = row.split(":")
        count = 0
        # find the gene list
        if len(split_row) == 2 and split_row[0] == "gene_list":
            output.write(row)
            genes = split_row[1].split('\t')
            if genes[0] == "":
                genes.pop(0)

            # first check mapping sheet, then Uniprot, and genome nexus
            if source == "all":
                # get protein length by gene name from mapping file
                gene_name_to_length_dict = dict()
                get_protein_length_from_mapping_sheet(mapping_file, gene_name_to_length_dict)
                # get protein length from Uniprot
                gene_name_to_length_dict_primary = dict()
                gene_name_to_length_dict_synonym = dict()
                get_protein_length_from_uniprot(uniprot_file, gene_name_to_length_dict_primary, gene_name_to_length_dict_synonym)
                for gene in genes:
                    gene = gene.strip()
                    if gene in gene_name_to_length_dict:
                        count += gene_name_to_length_dict[gene]
                    elif gene in gene_name_to_length_dict_primary:
                        count += gene_name_to_length_dict_primary[gene]
                    elif gene in gene_name_to_length_dict_synonym:
                        count += gene_name_to_length_dict_synonym[gene]
                    else:
                        raw_gn_response = look_up_in_genome_nexus(gene, genome_nexus_domain)
                        if raw_gn_response.status_code == 200:
                            gn_response = raw_gn_response.json()
                            if 'message' in gn_response:
                                print(gn_response['message'])
                            elif 'proteinLength' in gn_response:
                                count += gn_response['proteinLength']
                            else:
                                print(input_file + "\t" + gene)
                        else:
                            print(input_file + "\t" + gene)
                        
                # CDS size is calculated by sum(protein length * 3)
                count = count * 3
            # first check mapping spreadsheet, if gene not found then check Uniprot file.
            elif source == "combined":
                # get protein length by gene name from mapping file
                gene_name_to_length_dict = dict()
                get_protein_length_from_mapping_sheet(mapping_file, gene_name_to_length_dict)
                # get protein length from Uniprot
                gene_name_to_length_dict_primary = dict()
                gene_name_to_length_dict_synonym = dict()
                get_protein_length_from_uniprot(uniprot_file, gene_name_to_length_dict_primary, gene_name_to_length_dict_synonym)
                for gene in genes:
                    gene = gene.strip()
                    if gene in gene_name_to_length_dict:
                        count += gene_name_to_length_dict[gene]
                    elif gene in gene_name_to_length_dict_primary:
                        count += gene_name_to_length_dict_primary[gene]
                    elif gene in gene_name_to_length_dict_synonym:
                        count += gene_name_to_length_dict_synonym[gene]
                    else:
                        print(gene + " not found")
                # CDS size is calculated by sum(protein length * 3)
                count = count * 3
            # source is local map
            elif source == "map":
                # get protein length by gene name from mapping file
                gene_name_to_length_dict = dict()
                get_protein_length_from_mapping_sheet(mapping_file, gene_name_to_length_dict)
                for gene in genes:
                    gene = gene.strip()
                    if gene in gene_name_to_length_dict:
                        count += gene_name_to_length_dict[gene]
                    else:
                        print(gene + " not found in mapping file")
                # CDS size is calculated by sum(protein length * 3)
                count = count * 3
            
            # source is genome nexus
            elif source == "genomenexus":
                for gene in genes:
                    raw_gn_response = look_up_in_genome_nexus(gene, genome_nexus_domain)
                    if raw_gn_response.status_code == 200:  
                        gn_response = raw_gn_response.json()
                        if 'message' in gn_response:
                            print(gn_response['message'])
                        elif 'proteinLength' in gn_response:
                            count += gn_response['proteinLength']
                        # proteinLength is not in genome nexus response
                        else:
                            print(gene + " does not have protein length")
                    else:
                        print(gene + " HTTP Status " + str(raw_gn_response.status_code))
                # CDS size is calculated by sum(protein length * 3)
                count = count * 3
        
        # source is uniprot
            elif source == "uniprot":
                # get protein length by gene name from uniprot
                gene_name_to_length_dict_primary = dict()
                gene_name_to_length_dict_synonym = dict()
                get_protein_length_from_uniprot(uniprot_file, gene_name_to_length_dict_primary, gene_name_to_length_dict_synonym)
                for gene in genes:
                    gene = gene.strip()
                    if gene in gene_name_to_length_dict_primary:
                        count += gene_name_to_length_dict_primary[gene]
                    elif gene in gene_name_to_length_dict_synonym:
                        count += gene_name_to_length_dict_synonym[gene]
                    else:
                        print(gene + " not found in UniProt file")
                # CDS size is calculated by sum(protein length * 3)
                count = count * 3

            # write number_of_profiled_coding_base_pairs to output file
            if not genes[-1].endswith("\n"):
                output.write("\n")
            output.write("number_of_profiled_coding_base_pairs: " + str(count))
        
        # for files already have number_of_profiled_coding_base_pairs, ignore the existing value
        elif len(split_row) == 2 and split_row[0] == "number_of_profiled_coding_base_pairs":
            pass
        else:
            output.write(row)
    input.close()
    output.close()

def check_dir(file):
    # check existence of directory
    if not os.path.exists(file) and file != '':
        print('input file cannot be found: ' + file)
        sys.exit(2)

def check_output_file_path(output_file):
    if not os.access(os.path.dirname(output_file), os.W_OK):
        print('output file path is not valid: ' + output_file)
        sys.exit(2)

def check_source(source):
    if source != "genomenexus" and source != "uniprot" and source != "map" and source != "map+uniprot" and source != "all":
        print('Source is not valid, please set souce as one of the options: genomenexus | uniprot | map | map+uniprot | all')
        sys.exit(2)

def interface():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input-file', dest = 'input_file', type=str, required=True, 
                        help='absolute path to the input meta file')
    parser.add_argument('-u', '--uniprot-file', dest = 'uniprot_file', type=str, required=False, 
                        help='absolute path to the uniprot gene with protein length file')
    parser.add_argument('-o', '--output-file', dest = 'output_file', type=str, required=False, 
                        help='absolute path to save the output file')
    parser.add_argument('-s', '--source', dest = 'source', type=str, required=False,
                        help='set protein length data source. Options: genomenexus | uniprot | map | map+uniprot | all')
    parser.add_argument('-g', '--genome-nexus-domain', dest = 'genome_nexus_domain', type=str, required=False, 
                        help='custom Genome Nexus domain, using uniprot or map as source will ignore this variable')
    parser.add_argument('-m', '--mapping-file', dest = 'mapping_file', type=str, required=False, 
                        help='absolute path to the mapping file')
    parser = parser.parse_args()

    return parser


def main(args):
    input_file = args.input_file
    output_file = args.output_file
    uniprot_file = args.uniprot_file
    source = args.source
    genome_nexus_domain = args.genome_nexus_domain
    mapping_file = args.mapping_file

    if input_file is not None:
        check_dir(input_file)
    if output_file is not None:
        check_output_file_path(output_file)
    if uniprot_file is not None:
        check_dir(uniprot_file)
    if source is not None:
        check_source(source)
    if mapping_file is not None:
        check_dir(mapping_file)
    update_file(args)

if __name__ == '__main__':
    parsed_args = interface()
    main(parsed_args)