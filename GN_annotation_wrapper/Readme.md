### Usage

This tool accounts for Genome Nexus annotation timeout issue. The un-annotated mutations are looped back to Genome Nexus annotation pipeline for next round of annotation.

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
-o OUTPUT_FILENAME, --output_filename OUTPUT_FILENAME
                        Output maf file name
```

### Example
```
python GN_annotation_wrapper.py -f data_mutations_extended.txt -a /data/curation/annotation/annotator/annotationPipeline-1.0.0.jar -i uniprot -o data_mutations_uniprot.txt
```   
                    