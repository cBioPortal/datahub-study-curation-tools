# Extract Mutational Signatures
## Introduction
Extract mutational signatures from VCF/MAF files using tempoSig and output cBioPortal Generic Assay files.
This script generates both data and meta files.

When using MAF/cBioPortal studies as input, be aware that your files might be pre-processed and the mutations might not 
represent the true mutational landscape. This can influence the output of mutational-signatures.

## Installation
### Docker installation
The easiest way to install the dependencies is by building a docker image. This also automatically installs the GRCh37 genome,
if another genome is required (e.g., GRCh38), pass the `--build-args GENOME=GRCh38` argument when building. 

*N.B. Building takes approx. 10 minutes.* 
```shell
docker build -t mutational-signatures .
```

### Non-docker installation
- Clone the repo. 
- Install python3 dependencies in `requirements.txt`.
- Install `r-base`, `r-cran-devtools`, `libgsl-dev` using `apt`
- Install tempoSig `Rscript -e "devtools::install_github('mskcc/temposig')"`

### N.B.
COSMIC mutational signatures can be downloaded [here](https://cancer.sanger.ac.uk/signatures/downloads/).

## Running the script using docker (recommended)
Using a folder containing VCFs (VCF must be named {sample_name}.vcf):
```shell
docker run \
-v {input_folder}:/input \
-v {output_folder}:/output \
mutational-signatures \
python3 script/mutationalSignatures.py \
--vcf_folder /input/{vcf_folder} \
--output /output \
--study-id {study_id} \
--genome {grch37} \
--cosmic-sbs-file /input/{cosmic_sbs.txt} \
--tmp-dir /tmp/tmp
```
Output will be generated in your mounted output folder. The `/tmp` directory required to be empty when the script is
run, point the `--tmp-dir` flag to a mounted directory if you wish to keep the temporary files. 

N.B. If using another genome than provided in the `docker build` command, run the command with the `--install-genome` parameter. 
Or rebuild the container using a different genome (e.g., tag the grch38 container with `-t mutational-signatures-38`). 

**!!** The `--install-genome` parameter is not persistent in docker containers, if running the script with another genome 
more than once, rebuilding the container will probably be faster.

## Running the script without docker
Locate the installation location of the tempoSig.R script:
```shell
Rscript -e "system.file('exec', 'tempoSig.R', package = 'tempoSig')"
 ```

Run the script:
```shell
python3 mutationalSignatures.py \
--vcf_folder {path} \
--output {path} \
--study-id {study_id} \
--genome {grch37} \
-t {temposig_loc} \
--cosmic-sbs-file {cosmic_sbs.txt} \
--install-genome
```

N.B. The `--install-genome` parameter is only required on the first run per genome.

## Command line arguments
```
$ python3 mutationalSignatures.py -h
usage: mutationalSignatures.py [-h] (--study-path ./path/ | --maf file.maf | --vcf-folder ./path/) -t temposig.R -o ./path/ [-s cosmic_SBS.txt] [-d cosmic_DBS.txt] [-i cosmic_ID.txt] [--study-id studyid]
                               [--genome {GRCh37,GRCh38,GRCm37,GRCm38}] [--install-genome] [--tmp-dir ./path/] [--seed N] [-n N] [--alt-allele {Tumor_Seq_Allele1,Tumor_Seq_Allele2}] [--annotate annotate.csv] [--mask 0.05]

Extract mutational signatures from a cBioPortal study/MAF/VCFs and generate output in cBioPortal format.

options:
  -h, --help            show this help message and exit

input (mutually exclusive):
  --study-path ./path/  cBioPortal study path
  --maf file.maf        MAF file (--study-id required)
  --vcf-folder ./path/  folder containing VCF files with sampleID as filename (--study-id and --genome required)

required arguments:
  -t temposig.R, --temposig-loc temposig.R
                        location of 'tempoSig.R' script
  -o ./path/, --out-dir ./path/
                        output directory

signature files (at least one is required):
  -s cosmic_SBS.txt, --cosmic-sbs-file cosmic_SBS.txt
                        extract single base substitution signatures with the provided file
  -d cosmic_DBS.txt, --cosmic-dbs-file cosmic_DBS.txt
                        extract double base substitution signatures with the provided file
  -i cosmic_ID.txt, --cosmic-id-file cosmic_ID.txt
                        extract insertion/deletion signatures with the provided file

optional arguments:
  --study-id studyid    study ID (used for metafile generation)
  --genome {GRCh37,GRCh38,GRCm37,GRCm38}
                        NCBI build
  --install-genome      install the given genome for matrix generation (only required on first run per genome)
  --tmp-dir ./path/     temporary directory for files (default: ./tmp)
  --seed N              seed for reproducibility
  -n N, --nperm N       number of permutations for p-value estimation (default: 1000)
  --alt-allele {Tumor_Seq_Allele1,Tumor_Seq_Allele2}
                        Manually set alternative allele
  --annotate annotate.csv
                        Path to signature annotation file (default: mutational_signatures_annotation.csv)
  --mask 0.05           Add metafile mask for contributions below given value (default 0.05)
```