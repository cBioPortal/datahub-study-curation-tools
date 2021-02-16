1. Download HGNC table

`https://www.genenames.org/download/statistics-and-files/
`Complete dataset download links` section: `Complete HGNC approved dataset`

2. Fill up empty entrez IDs

Since we are using entrez ID as major key in our DB, we need to make sure every genes is assigned an entrez ID.
However, not every gene in HGNC has an entrez ID.
So we need to fill these genes back up using this sheet: https://rb.gy/pqg455

3. Entries with same entrez IDs merged (as prev_symbol)	

100874024: TRPC7-AS1, TRPC7-AS2
1550: CYP2A7P2,CYP2A7P1

4. Remove all miRNA entries

5. Extract columns from HGNC table

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

6. Merge gene types

Merge values `locus_group` and `locus_type` into one column `type`
Run script `merge-type.py`

7. Merge gene alias

Merging values in `alias_symbol` and `prev_symbol` into one column `synonyms`
Remove duplicates by prioritizing: main > previous > alias 
Meaning, if a symbol already exists as a main symbol, even if it is also a HGNC alias/prev symbol, don`t add it into the alias table; if a symbol already exists as a prev symbol, even if it`s also a HGNC alias symbol, don`t add it to alias table
Run script `merge-alias.py` (using `supp_alias.txt` as input)

8. Translate HGNC location

Translate the `location` column into two `chromosome` and `cytoband`
Run script `translate-location.py`

9. Supplement main genes
Simply concatenate the supplemental file: 

10. Supplement alias genes
Use script to merge the supplemental alias list: 
Supplemental alias list (resource): 

11. The final file `final_list_date.txt` should include fields

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

12. Build DB tables using `final_list_date.txt`

13. Import Portal miRNAs 
Using the existing static mapping file + importer scripts to generate miRNA entries

14. Portal phosphoprotein
not adding phosphoprotein (generated dynamically)