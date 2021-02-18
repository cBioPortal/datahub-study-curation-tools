## Annotation wrapper

This tool accounts for Genome Nexus annotation timeout issue. If all records are not successfully annotated on first attempt, then the script will continue running annotator on remaining unannotated records until no new annotated records are produced in further attempts.

The output of the script is two files with annotated and unannotated records for further manual checking.

### Prerequisites
The wrapper script requires [annotationPipeline](https://github.com/genome-nexus/genome-nexus-annotation-pipeline) module which is a command line tool to annotate a maf using [Genome Nexus](https://www.genomenexus.org/).

Clone the [Genome Nexus Annotation Pipeline](https://github.com/genome-nexus/genome-nexus-annotation-pipeline) repository and follow the pre-build instructions as stated in the README to create `application.properties` and `log4j.properties`. 

Build a executable jar file of the application using Maven as `mvn clean install` (Maven can be downloaded from [here](https://maven.apache.org/download.cgi))

### Command Line

Once the executable jar is created, running the wrapper script on python2.7 with `-help` displays the usage of the script.

```
python GN_annotation_wrapper.py -help
```

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
python GN_annotation_wrapper.py --input_maf data_mutations_extended.txt --annotator_jar_path /data/curation/annotation/annotator/annotationPipeline-1.0.0.jar --isoform uniprot --annotated_maf data_mutations_uniprot_annotated.txt --unannotated_maf data_mutations_uniprot_unannotated.txt
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
python merge_mafs.py --input_maf1 annotated_maf.txt --input_maf2 unannotated_maf.txt --merged_maf merged_maf.txt
```
