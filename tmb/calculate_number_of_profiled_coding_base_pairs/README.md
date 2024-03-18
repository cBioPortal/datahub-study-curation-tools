### Description
Giving a gene panel file, for example:
```
stable_id: IMPACT
description: Targeted sequencing of various tumor types via MSK-IMPACT on Illumina HiSeq sequencers.
gene_list:	ABL1	ACVR1
```
Calculate `number_of_profiled_coding_base_pairs` by:
```
number_of_profiled_coding_base_pairs = sum(protein_length * 3)
```
Print out `number_of_profiled_coding_base_pairs` in console and save the number to an output file, for example:

In concole:
```
number of profiled coding base pairs found: 4917
```
In output file:
```
stable_id: IMPACT
description: Targeted sequencing of various tumor types via MSK-IMPACT on Illumina HiSeq sequencers.
gene_list:	ABL1	ACVR1
number_of_profiled_coding_base_pairs: 4917
```

### Usage
Command variables:
- `-i`, `--input-file`, required, absolute path to the input meta file
- `-u`, `--uniprot-file`, optional, absolute path to the UniProt file, by default will use `uniprot_gene_name_with_protein_length.tab` file under the same directory
- `-o`, `--output-file`, optional, absolute path to save the new file, by default will save the output file with `output_` as prefix under the same directory
- `-s`, `--source`, optional, set data source for getting protein length , must be either `genomenexus`,  `uniprot`, `map`, `map+uniprot` or `all`, by default is set to `all`
- `-g`, `--genome-nexus-domain`, optional, domain for genome nexus, by default `genome-nexus-domain` is set to `https://www.genomenexus.org`
- `-m`, `--mapping-file`, optional, absolute path to mapping file, by default will use `mapping_per_gene.tsv` file under the same directory

Example command:
- Using all sources
```
python add_number_of_profiled_coding_base_pairs.py -i /YOUR_PATH/data_gene_panel_example.txt
```

- Using map + uniprot
```
python add_number_of_profiled_coding_base_pairs.py -i /YOUR_PATH/data_gene_panel_example.txt -s map+uniprot
```

- Using mapping file
```
python add_number_of_profiled_coding_base_pairs.py -i /YOUR_PATH/data_gene_panel_example.txt -s map

```
- Using Genome Nexus
```
python add_number_of_profiled_coding_base_pairs.py -i /YOUR_PATH/data_gene_panel_example.txt -s genomenexus
```

- Using Uniprot
```
python add_number_of_profiled_coding_base_pairs.py -i /YOUR_PATH/data_gene_panel_example.txt -s uniprot
```

### UniProt table
Protein length data are from [Uniprot](https://www.uniprot.org/uniprot/?query=reviewed:yes%20taxonomy:9606). The table has been saved as `uniprot_gene_name_with_protein_length.tab` in the same directory, if we want to replace the table in the future, please make sure the new file contains at least `Gene names (primary )`, `Gene names (synonym )` and `Length` column in the table file.