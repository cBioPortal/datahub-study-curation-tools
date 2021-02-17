### Entrez ID mapping `entrez-id-mapping.txt`

This file lists all HUGO_GENE_SYMBOL that does not have an entrez_ID associated in HGNC

For 2nd column "assigned entrez ID":
- When left empty, meaning we are not going to include this entry from HGNC into our own DB
- When assigned an entrez ID, meaning we are going to use the self-assigned entrez ID in our own DB

When updating with the latest HGNC, some new entries with come up that is not already already defined in this list. This would cause the script to exit when encountered. You need to go back to add those new entries into this list to enable to script to run. 