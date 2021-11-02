For CNA data, run 
python ~/scripts/curation/merge/subsetData-1.py id.txt data_CNA.txt
For seg, mutations, fusions data run
python ~/scripts/curation/merge/ritika_subset.py id.txt data_mutations_extended.txt > maf_subset.txt

For CNA, first remove extra spaces / line return characters from both CNA files headers, then run python ~/scripts/curation/merge/cna_merge2.py data_CNA1.txt data_CNA2.txt (It will ask for headers, if there is just hugo symbol followed by samples then enter 1 for file 1 and 2, if it has hugo +entrez then 2 and 3 if there is also cytoband.)
