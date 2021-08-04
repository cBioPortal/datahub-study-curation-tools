### Usage
Calculate somatic TMB (non-synonymous) of all sequenced samples for a specific study. TMB is the total number of non-synonymous, somatic mutations identified per megabase
(Mb) of the genome coding area of DNA (a megabase is 1,000,000 DNA basepairs)

### Method

Step 1: Calculate Total number `N` of non-synonymous, somatic mutations with eligible classification (list below) in MAF
```
	"Frame_Shift_Del"
	"Frame_Shift_Ins" 
	"In_Frame_Del" 
	"In_Frame_Ins" 
	"Missense_Mutation" 
	"Nonsense_Mutation" 
	"Splice_Site"
	"Nonstop_Mutation" 
	"Splice_Region"
```
Step 2: Determine the size `L` of genome coding area of DNA in megabase(Mb)
- For WES/WGS: L = 30
- For targeted sequenced: refer to the `CDS` field in related gene panel files

Step 3: Calculate TMB for each sequenced sample
```
TMB = N/L
```
- For sequenced sample: if used panel size is <0.2M, the TMB is not calculated and marked as "NA"
- For not sequenced samples (refer to `cases_sequenced.txt` for each study), the TMB is marked as "NA" 

Step 4: Append TMB scores as an additional column in sample clinical file.

### Command Line
```
Usage: calc_nonsyn_tmb.py [-h] -i INPUT_STUDY_FOLDER -p
                          INPUT_GENE_PANEL_FOLDER

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_STUDY_FOLDER, --input-study-folder INPUT_STUDY_FOLDER
                        Input Study folder
  -p INPUT_GENE_PANEL_FOLDER, --input-gene-panel-folder INPUT_GENE_PANEL_FOLDER
                        Gene Panel folder
```
### Example

```
python path/to/calc_nonsyn_tmb.py -p path/to/gene_panels -i path/to/study
```

### Notes
For WGS and WES studies, the gene panel folder parameter is still needed. 
