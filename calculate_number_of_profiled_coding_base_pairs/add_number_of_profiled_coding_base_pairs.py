import csv
import pandas as pd
import os
import sys
import argparse
import ntpath
import requests
import json

def generate_dict(key, value, dictionary):
    if not pd.isnull(key):
        if ';' not in key:
            dictionary[key] = value
        else:
            genes = key.split('; ')
            for gene in genes:
                dictionary[gene] = value

def update_file(args):
    inputFile = args.inputFile
    uniprotFile = args.uniprotFile or os.getcwd() + "/uniprot_gene_name_with_protein_length.tab"
    outputFile = args.outputFile or os.path.dirname(inputFile) + "/output_" + ntpath.basename(inputFile)
    source = args.source or "genomenexus"
    genomeNexusDomain = args.genomeNexusDomain or "https://www.genomenexus.org"

    # write files
    input = open(inputFile, 'rt')
    output = open(outputFile, 'wt')

   # source is genome nexus
    if source == "genomenexus":
        for row in input.readlines():
            output.write(row)
            # find the gene list
            splitRow = row.split(":")
            if len(splitRow) == 2 and splitRow[0] == "gene_list":
                genes = splitRow[1].split('\t')
                count = 0
                if genes[0] == "":
                    genes.pop(0)
                for gene in genes:
                    gene = gene.strip()
                    gnRequest = genomeNexusDomain + '/ensembl/canonical-transcript/hgnc/' + gene + '?isoformOverrideSource=uniprot'
                    # get json response from genome nexus
                    gnResponse = json.loads(requests.get(gnRequest).text)
                    # gene not found in genome nexus
                    if 'message' in gnResponse:
                        print(gnResponse['message'])
                    elif 'proteinLength' in gnResponse:
                        count += gnResponse['proteinLength']
                    # proteinLength is not in genome nexus response
                    else:
                        print(gene + " does not have protein length")
                # CDS size is calculated by sum(protein length * 3)
                count = count * 3
                if not genes[-1].endswith("\n"):
                    output.write("\n")
                output.write("number_of_profiled_coding_base_pairs: " + str(count))
   
   # source is uniprot
    else:
        # get protein length by gene name
        df_uniprot_gene_name_with_protein_length = pd.read_csv(uniprotFile, sep='\t')
        gene_name_to_length_dict_primary = dict()
        gene_name_to_length_dict_synonym = dict()
        df_uniprot_gene_name_with_protein_length.apply(lambda row: generate_dict(row['Gene names  (primary )'], row['Length'], gene_name_to_length_dict_primary), axis=1)
        df_uniprot_gene_name_with_protein_length.apply(lambda row: generate_dict(row['Gene names  (synonym )'], row['Length'], gene_name_to_length_dict_synonym), axis=1)

        for row in input.readlines():
            output.write(row)
            # find the gene list
            splitRow = row.split(":")
            if len(splitRow) == 2 and splitRow[0] == "gene_list":
                genes = splitRow[1].split('\t')
                count = 0
                if genes[0] == "":
                    genes.pop(0)
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
                if not genes[-1].endswith("\n"):
                    output.write("\n")
                output.write("number_of_profiled_coding_base_pairs: " + str(count))
    input.close()
    output.close()

def check_dir(file):
    # check existence of directory
    if not os.path.exists(file) and file != '':
        print('input file cannot be found: ' + file)
        sys.exit(2)

def check_output_file_path(outputFile):
    if not os.access(os.path.dirname(outputFile), os.W_OK):
        print('output file path is not valid: ' + outputFile)
        sys.exit(2)

def check_source(source):
    if source != "genomenexus" and source != "uniprot":
        print('Source is not valid, please set souce as one of the options: genomenexus | uniprot')
        sys.exit(2)

def interface():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--inputFile', type=str, required=True, 
                        help='absolute path to the input meta file')
    parser.add_argument('-u', '--uniprotFile', type=str, required=False, 
                        help='absolute path to the uniprot gene with protein length file')
    parser.add_argument('-o', '--outputFile', type=str, required=False, 
                        help='absolute path to save the output file')
    parser.add_argument('-s', '--source', type=str, required=False,
                        help='set protein length data source. Options: genomenexus | uniprot')
    parser.add_argument('-g', '--genomeNexusDomain', type=str, required=False, 
                        help='custom Genome Nexus domain, using uniprot as source will ignore this variable')
    parser = parser.parse_args()

    return parser


def main(args):
    inputFile = args.inputFile
    outputFile = args.outputFile
    uniprotFile = args.uniprotFile
    source = args.source
    genomeNexusDomain = args.genomeNexusDomain

    if inputFile is not None:
        check_dir(inputFile)
    if outputFile is not None:
        check_output_file_path(outputFile)
    if uniprotFile is not None:
        check_dir(uniprotFile)
    if source is not None:
        check_source(source)
    update_file(args)

if __name__ == '__main__':
    parsed_args = interface()
    main(parsed_args)