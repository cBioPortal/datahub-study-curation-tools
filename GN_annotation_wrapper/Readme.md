## Annotation wrapper Usage 

This tool accounts for Genome Nexus annotation timeout issue. If all records are not successfully annotated on first attempt, then script will continue running annotator on remaining unannotated records until no new annotated records are produced in further attempts.

The script outputs two files with annotated and unannotated records for further manual checking.

### Command Line
```
-h, --help            show this help message and exit
  -f INPUT_MAF, --input_maf INPUT_MAF
                        Input maf file name
  -a ANNOTATOR_JAR_PATH, --annotator_jar_path ANNOTATOR_JAR_PATH
                        Path to the annotator jar file. An example can be
                        found in "/data/curation/annotation/annotator/annotati
                        onPipeline-1.0.0.jar" on dashi-dev
  -i ISOFORM, --isoform ISOFORM
                        uniprot/mskcc annotation isoform.
  -an ANNOTATED_MAF, --annotated_maf ANNOTATED_MAF
                        Annotated output maf file name
  -unan UNANNOTATED_MAF, --unannotated_maf UNANNOTATED_MAF
                        Unannotated output maf file name
```

### Example
```
python GN_annotation_wrapper.py -f data_mutations_extended.txt -a /data/curation/annotation/annotator/annotationPipeline-1.0.0.jar -i uniprot -an data_mutations_annotated.txt -unan data_mutations_unannotated.txt
```   

## Merge script usage

Once the unannotated records from the above wrapper is manually checked and updated the two maf files (annotated and unannotated) are to be merged to one

### Command Line
```
  -h, --help            show this help message and exit
  -f1 INPUT_MAF1, --input_maf1 INPUT_MAF1
                        Input MAF1
  -f2 INPUT_MAF2, --input_maf2 INPUT_MAF2
                        Input MAF2
  -o MERGED_MAF, --merged_maf MERGED_MAF
                        Merged output MAF file name
```
### Example
```
python merge_mafs.py -f1 annotated_maf.txt -f2 unannotated_maf.txt -o merged_maf.txt
```
