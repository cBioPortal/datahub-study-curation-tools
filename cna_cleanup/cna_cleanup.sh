touch data_CNA_removed.txt
touch data_log2CNA_removed.txt
perl ~/data/datahub-study-curation-tools/cna_cleanup/CNA_cleanup.pl data_CNA.txt data_CNA_removed.txt
perl ~/data/datahub-study-curation-tools/cna_cleanup/CNA_cleanup.pl data_log2CNA.txt data_log2CNA_removed.txt