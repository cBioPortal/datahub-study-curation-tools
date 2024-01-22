FROM ubuntu
RUN apt update
# Needed to supress r-base region messages
ENV DEBIAN_FRONTEND=noninteractive
RUN apt install -y r-base r-cran-devtools libgsl-dev python3-pip wget
RUN Rscript -e "devtools::install_github('mskcc/temposig')"

RUN mkdir script
COPY requirements.txt /
RUN python3 -m pip install -r /requirements.txt
# Install genome
ARG GENOME='GRCh37'
RUN python3 -c "from SigProfilerMatrixGenerator import install as genInstall; genInstall.install('$GENOME')"

COPY mutational_signatures_annotation.csv /
COPY mutationalSignatures.py /
