Below are steps for building an input file, to be used by importer to build/update seedDB gene tables

### Step 1 - Download HGNC table

Go to `https://www.genenames.org/download/statistics-and-files/`

Under `Complete dataset download links` section: `Complete HGNC approved dataset`

### Step 2 - Fill up empty entrez IDs

Since we are using entrez ID as major key in our DB, we need to make sure every genes is assigned an entrez ID.
However, not every gene in HGNC has an entrez ID.
So we need to fill these genes back up using this sheet: https://rb.gy/pqg455

### Step 3 - Entries with same entrez IDs merged (as prev_symbol)	

100874024: TRPC7-AS1, TRPC7-AS2
1550: CYP2A7P2,CYP2A7P1

### Step 4 - Remove all miRNA entries

### Step 5 - Extract columns from HGNC table

```
hgnc_id
symbol
locus_group
locus_type
location
entrez_id
alias_symbol
prev_symbol
ensembl_gene_id
```

### Step 6- Merge gene types

Merge values `locus_group` and `locus_type` into one column `type`
Run script `merge-type.py`

### Step 7 - Merge gene alias

Merging values in `alias_symbol` and `prev_symbol` into one column `synonyms`
Remove duplicates by prioritizing
```
main > previous > alias 
```

Meaning, if a symbol already exists as a main symbol, even if it is also a HGNC alias/prev symbol, do not add it into the alias table; if a symbol already exists as a prev symbol, even if it is also a HGNC alias symbol, do not add it to alias table

Run script `merge-alias.py` (using `supp_alias.txt` as input)

### Step 8 - Translate HGNC location

Translate the `location` column into two `chromosome` and `cytoband`
Run script `translate-location.py`

### Step 9 - Supplement main genes
Simply concatenate `supp_main.txt` 

### Step 10 - Supplement alias genes
Use script 'merge_alias_supp.txt' to merge the supplemental alias list `supp_alias.txt`

## The final file should include fields

```
entrez_id
symbol
chromosome
cytoband
type
synonyms
hgnc_id
ensembl_id
```
