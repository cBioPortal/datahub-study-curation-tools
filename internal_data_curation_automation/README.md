## Internal Data Curation Automation

This suite of tools have been specifically developed to generate novel research studies for cBioPortal by consolidating and refining data obtained from a cohort of patients or samples selected from existing studies.

By receiving a list of patient/sample IDs and input study directories, the script filters and merges the data to produce a new study directory that can be seamlessly imported into cBioPortal.

### Prerequisites

1. Python3 and Python2

2. The script requires [annotationPipeline](https://github.com/genome-nexus/genome-nexus-annotation-pipeline) module which is a command line tool to annotate a maf using [Genome Nexus](https://www.genomenexus.org/).

	Clone the [Genome Nexus Annotation Pipeline](https://github.com/genome-nexus/genome-nexus-annotation-pipeline) repository and follow the pre-build instructions as stated in the README to create `application.properties` and `log4j.properties`. 

	Build a executable jar file of the application using Maven as `mvn clean install` (Maven can be downloaded from [here](https://maven.apache.org/download.cgi))

3. Python Click module.
Can be installed using `pip install click`

4. Python logging module.
Can be installed using `pip install logging`

### Usage:
```
	-s | --subset-identifiers            provide a list of patient/sample identifiers to either select or exclude from [REQUIRED]
	-i | --input-directories             A list of input data directories to subset the data from, separated by commas [REQUIRED]
	-e | --exclude-identifiers           Entering 'True' for this setting will exclude any samples included in the provided list from the subset. T
```

### Command Line

Once the Genome Nexus executable jar is created, name it annotator.jar. 

Run the bash automation wrapper script as

```
bash automate_curation.sh --subset-identifiers=sample_list.txt --input-directories=/path/to/dir1,/path/to/dir2
```

#### Arguments
- The `--subset-identifiers` option is used to specify either a file with patient or sample identifiers. One identifier per line.
- The `--input-directories` option is utilized to identify the study directories housing the relevant identifiers, which require data filtering. Supports passing multiple directories at once (please use commas to separate the directories).
- The `--exclude-identifiers` is a special option. When passed, the script selects all other relevant identifiers from `--input-directories`, while excluding the ones from `--subset-identifiers`.
