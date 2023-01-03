import argparse
import glob

dict = {
    "clinical_patient": """genetic_alteration_type: CLINICAL
datatype: PATIENT_ATTRIBUTES
data_filename: data_clinical_patient.txt""",


"clinical_sample": """genetic_alteration_type: CLINICAL
datatype: SAMPLE_ATTRIBUTES
data_filename: data_clinical_sample.txt""",


	"timeline": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline.txt""",


	"timeline_treatment": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_treatment.txt""",


	"timeline_sample": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_sample.txt""",


	"timeline_biopsy": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_biopsy.txt""",


	"timeline_diagnosis": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_diagnosis.txt""",


	"timeline_sequencing": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_sequencing.txt""",


	"timeline_status": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_status.txt""",


	"timeline_surgery": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_surgery.txt""",


	"timeline_imaging": """"genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_imaging.txt""",


	"timeline_sample_acquisition": """genetic_alteration_type: CLINICAL
datatype: TIMELINE
data_filename: data_timeline_sample_acquisition.txt""",


	"rppa": """genetic_alteration_type: PROTEIN_LEVEL
datatype: LOG2-VALUE
stable_id: rppa
show_profile_in_analysis_tab: false
profile_name: Protein expression (RPPA)
profile_description: Protein expression measured by reverse-phase protein array
data_filename: data_rppa.txt""",


	"rppa_zscores": """genetic_alteration_type: PROTEIN_LEVEL
datatype: Z-SCORE
stable_id: rppa_Zscores
show_profile_in_analysis_tab: true
profile_name: Protein expression z-scores (RPPA)
profile_description: Protein expression, measured by reverse-phase protein array, Z-scores
data_filename: data_rppa_zscores.txt""",


	"protein_quantification": """genetic_alteration_type: PROTEIN_LEVEL
datatype: LOG2-VALUE
stable_id: protein_quantification
show_profile_in_analysis_tab: false
profile_name: Protein abundance ratio
profile_description: Protein abundance ratio measured by mass spectrometry
data_filename: data_protein_quantification.txt""",


	"protein_quantification_zscores": """genetic_alteration_type: PROTEIN_LEVEL
datatype: Z-SCORE
stable_id: protein_quantification_zscores
show_profile_in_analysis_tab: true
profile_name: Protein abundance ratio Z-scores
profile_description: Z-scores of protein abundance ratio measured by mass spectrometry
data_filename: data_protein_quantification_zscores_ref_all_samples.txt""",


	"phosphoprotein_quantification": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: Phosphoproteome
datatype: LIMIT-VALUE
stable_id: phosphoproteome
show_profile_in_analysis_tab: true
profile_name: Phosphoprotein abundance ratio
profile_description: Abundance ratio for phosphoproteins measured by mass spectrometry. Column PHOSPHOSITES: sites_#sites_#present_firstAA_lastAA
data_filename: data_phosphoprotein_quantification.txt
generic_entity_meta_properties: NAME,DESCRIPTION,GENE_SYMBOL,PHOSPHOSITES""",


	"gistic_genes_amp": """genetic_alteration_type: GISTIC_GENES_AMP
datatype: Q-VALUE
reference_genome_id: hg19
data_filename: data_gistic_genes_amp.txt""",


	"gistic_genes_del": """genetic_alteration_type: GISTIC_GENES_DEL
datatype: Q-VALUE
reference_genome_id: hg19
data_filename: data_gistic_genes_del.txt""",


    "armlevel_cna": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: ARMLEVEL_CNA
datatype: CATEGORICAL
stable_id: armlevel_cna
profile_name: Putative arm-level copy-number from GISTIC
profile_description: Putative arm-level copy-number from GISTIC 2.0.
data_filename: data_armlevel_cna.txt
show_profile_in_analysis_tab: true
generic_entity_meta_properties: NAME,DESCRIPTION""",


	"cna_hg19.seg": """genetic_alteration_type: COPY_NUMBER_ALTERATION
datatype: SEG
reference_genome_id: hg19
description: Somatic CNA data (copy number ratio from tumor samples minus ratio from matched normals) from TCGA.
data_filename: data_cna_hg19.seg""",


	"cna": """genetic_alteration_type: COPY_NUMBER_ALTERATION
datatype: DISCRETE
stable_id: gistic
show_profile_in_analysis_tab: true
profile_description: Putative copy-number from GISTIC 2.0. Values: -2 = homozygous deletion; -1 = hemizygous deletion; 0 = neutral / no change; 1 = gain; 2 = high level amplification.
profile_name: Putative copy-number alterations from GISTIC
data_filename: data_cna.txt""",

	
	"CNA": """genetic_alteration_type: COPY_NUMBER_ALTERATION
datatype: DISCRETE
stable_id: gistic
show_profile_in_analysis_tab: true
profile_description: Putative copy-number from GISTIC 2.0. Values: -2 = homozygous deletion; -1 = hemizygous deletion; 0 = neutral / no change; 1 = gain; 2 = high level amplification.
profile_name: Putative copy-number alterations from GISTIC
data_filename: data_CNA.txt""",


	"linear_cna": """genetic_alteration_type: COPY_NUMBER_ALTERATION
datatype: CONTINUOUS
data_filename: data_linear_cna.txt
stable_id: linear_CNA
show_profile_in_analysis_tab: false
profile_description: Capped relative linear copy-number values for each gene (from Affymetrix SNP6).
profile_name: Capped relative linear copy-number values""",


	"mutations": """genetic_alteration_type: MUTATION_EXTENDED
datatype: MAF
stable_id: mutations
show_profile_in_analysis_tab: true
profile_description: Mutation data from whole-exome sequencing.
profile_name: Mutations
data_filename: data_mutations.txt""",


	"mutations_extended": """genetic_alteration_type: MUTATION_EXTENDED
datatype: MAF
stable_id: mutations
show_profile_in_analysis_tab: true
profile_description: Mutation data from whole-exome sequencing.
profile_name: Mutations
data_filename: data_mutations_extended.txt""",


	"mutations_uncalled": """genetic_alteration_type: MUTATION_UNCALLED
datatype: MAF
stable_id: mutations_uncalled
show_profile_in_analysis_tab: false
profile_description: Mutation data from whole exome sequencing. (Uncalled)
profile_name: Mutations Uncalled
data_filename: data_mutations_uncalled.txt""",


	"mutsig": """genetic_alteration_type: MUTSIG
datatype: Q-VALUE
data_filename: data_mutsig.txt""",


	"structural_varaiants": """genetic_alteration_type: STRUCTURAL_VARIANT
datatype: SV
stable_id: structural_variants
show_profile_in_analysis_tab: true
profile_name: Structural variants
profile_description: Structural Variant Data.
data_filename: data_sv.txt""",


	"methylation_hm27": """genetic_alteration_type: METHYLATION
datatype: CONTINUOUS
stable_id: methylation_hm27
profile_description: Methylation beta-values (hm27 assay). For genes with multiple methylation probes, the probe least correlated with expression is selected.
show_profile_in_analysis_tab: false
profile_name: Methylation (HM27)
data_filename:data_methylation_hm27.txt""",


	"methylation_hm27_hm450_merged": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: METHYLATION
datatype: LIMIT-VALUE
stable_id: methylation_hm27_hm450_merge
profile_name: Methylation (HM27 and HM450 merge)
profile_description: Methylation between-platform (hm27 and hm450) normalization values.
data_filename: data_methylation_hm27_hm450_merged.txt
show_profile_in_analysis_tab: true
value_sort_order: DESC
generic_entity_meta_properties: NAME,DESCRIPTION,TRANSCRIPT_ID""",


	"methylation_hm450": """genetic_alteration_type: METHYLATION
datatype: CONTINUOUS
data_filename: data_methylation_hm450.txt
stable_id: methylation_hm450
show_profile_in_analysis_tab: false
profile_description: Methylation (HM450) beta-values for genes in 80 cases. For genes with multiple methylation probes, the probe most anti-correlated with expression.
profile_name: Methylation (HM450)""",


	"microRNA_expression": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
data_filename: data_mirna.txt
show_profile_in_analysis_tab: false
stable_id: mirna
profile_name: miRNA expression (FPKM uq)
profile_description: Expression levels for microRNAs.""",


	"mirna_media_zscores": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
data_filename: data_mirna_zscores.txt
show_profile_in_analysis_tab: true
stable_id: mirna_median_Zscores
profile_name: Z-scores of miRNA expression (FPKM-UQ)
profile_description: microRNA expression z-scores compared to all tumors.""",


	"mrna_merged_median_Zscores": """stable_id: mrna_merged_median_Zscores
show_profile_in_analysis_tab: false
profile_name: mRNA/miRNA expression Z-scores (all genes)
profile_description: mRNA and microRNA Z-scores merged: mRNA expression Z-scores compared to diploid tumors (diploid for each gene), median values from all three mRNA expression platforms; and miRNA z-Scores compared to all tumours.
genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
data_filename: data_mrna_mirna_merged_zscores.txt""",


	"gsva_scores": """genetic_alteration_type: GENESET_SCORE
datatype: GSVA-SCORE
stable_id: gsva_scores
source_stable_id: mrna
profile_name: GSVA scores on oncogenic signatures gene sets
profile_description: GSVA scores using mRNA expression data
data_filename: data_gsva_scores.txt
show_profile_in_analysis_tab: true
geneset_def_version: msigdb_6.1""",


	"gsva_pvalues": """genetic_alteration_type: GENESET_SCORE
datatype: P-VALUE
stable_id: gsva_pvalues
source_stable_id: gsva_scores
profile_name: Pvalues of GSVA scores on oncogenic signatures gene sets
profile_description: Pvalues GSVA scores using mRNA expression data
data_filename: data_gsva_pvalues.txt
geneset_def_version: msigdb_6.1""",


	"treatment_ic50": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: TREATMENT_RESPONSE
datatype: LIMIT-VALUE
stable_id: treatment_ic50
profile_name: IC50 values of compounds on cellular phenotype readout
profile_description: IC50 (compound concentration resulting in half maximal inhibition) of compounds on cellular phenotype readout of cultured mutant cell lines.
data_filename: data_treatment_ic50.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0.1
value_sort_order: ASC
generic_entity_meta_properties: NAME,DESCRIPTION,URL""",


	"treatment_ec50": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: TREATMENT_RESPONSE
datatype: LIMIT-VALUE
stable_id: treatment_ec50
profile_name: EC50 values of compounds on cellular phenotype readout
profile_description: EC50 (compound concentration resulting in half maximal activation) of compounds on cellular phenotype readout of cultured mutant cell lines.
data_filename: data_treatment_ec50.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0.1
value_sort_order: ASC
generic_entity_meta_properties: NAME,DESCRIPTION,URL""",


	"sv": """genetic_alteration_type: STRUCTURAL_VARIANT
datatype: SV
stable_id: structural_variants
show_profile_in_analysis_tab: true
profile_name: Structural variants
profile_description: Structural Variant Data.
data_filename: data_sv.txt""",

	"gene_panel_matrix": """genetic_alteration_type: GENE_PANEL_MATRIX
datatype: GENE_PANEL_MATRIX
data_filename: data_gene_panel_matrix.txt""",

	"gene_matrix": """genetic_alteration_type: GENE_PANEL_MATRIX
datatype: GENE_PANEL_MATRIX
data_filename: data_gene_matrix.txt""",


	"mrna_affymetrix_microarray": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
data_filename: data_mrna_affymetrix_microarray.txt
stable_id: mrna_U133
show_profile_in_analysis_tab: false
profile_description: mRNA expression data from the Affymetrix U133 microarray.
profile_name: mRNA expression (U133 microarray only)""",


	"mrna_agilent_microarray_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_median_all_sample_Zscores
show_profile_in_analysis_tab: TRUE
profile_name: mRNA expression z-scores relative to all samples (log microarray)
profile_description: Log-transformed mRNA expression z-scores compared to the expression distribution of all samples  (Agilent microarray).
data_filename: data_mrna_agilent_microarray_zscores_ref_all_samples.txt""",


	"mrna_agilent_microarray_zscores_ref_diploid_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
data_filename: data_mrna_agilent_microarray_zscores_ref_diploid_samples.txt
stable_id: mrna_median_Zscores
show_profile_in_analysis_tab: true
profile_description: mRNA expression z-scores (Agilent microarray) compared to the expression distribution of each gene tumors that are diploid for this gene.
profile_name: mRNA expression z-scores relative to diploid samples (microarray)""",


	"mrna_agilent_microarray": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
data_filename: data_mrna_agilent_microarray.txt
stable_id: mrna
show_profile_in_analysis_tab: false
profile_description: Expression levels for <NUM_GENES> genes in <NUM_CASES> <TUMOR_TYPE> cases (Agilent microarray).
profile_name: mRNA expression (microarray)""",


	"mrna_seq_v2_rsem_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_v2_mrna_median_all_sample_Zscores
show_profile_in_analysis_tab: TRUE
profile_name: mRNA expression z-scores relative to all samples (log RNA Seq V2 RSEM)
profile_description: Log-transformed mRNA expression z-scores compared to the expression distribution of all samples (RNA Seq V2 RSEM).
data_filename: data_mrna_seq_v2_rsem_zscores_ref_all_samples.txt""",


	"mrna_seq_v2_rsem_zscores_ref_diploid_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
data_filename: data_mrna_seq_v2_rsem_zscores_ref_diploid_samples.txt
stable_id: rna_seq_v2_mrna_median_Zscores
show_profile_in_analysis_tab: true
profile_description: mRNA expression z-scores (RNA Seq V2 RSEM) compared to the expression distribution of each gene tumors that are diploid for this gene.
profile_name: mRNA expression z-scores relative to diploid samples (RNA Seq V2 RSEM)""",


	"mrna_seq_v2_rsem": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
data_filename: data_mrna_seq_v2_rsem.txt
stable_id: rna_seq_v2_mrna
show_profile_in_analysis_tab: false
profile_description: mRNA gene expression (RNA Seq V2 RSEM)
profile_name: mRNA expression (RNA Seq V2 RSEM)""",


	"mrna_affymetrix_microarray_zscores_ref_all_sample": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_U133_all_sample_Zscores
show_profile_in_analysis_tab: TRUE
profile_name: mRNA expression z-scores relative to all samples (U133 microarray only)
profile_description: Log-transformed mRNA expression z-scores compared to the expression distribution of all samples (U133 microarray only).
data_filename: data_mrna_affymetrix_microarray_zscores_ref_all_samples.txt""",


	"mrna_affymetrix_microarray_zscores_ref_diploid_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
data_filename: data_mrna_affymetrix_microarray_zscores_ref_diploid_samples.txt
stable_id: mrna_U133_Zscores
show_profile_in_analysis_tab: true
profile_description: mRNA expression z-scores (U133 microarray only) compared to the expression distribution of each gene tumors that are diploid for this gene.
profile_name: mRNA expression z-scores relative to diploid samples (U133 microarray only)""",


	"mrna_seq_v2_rsem": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
data_filename: data_mrna_seq_v2_rsem.txt
stable_id: rna_seq_v2_mrna
show_profile_in_analysis_tab: false
profile_description: mRNA gene expression (RNA Seq V2 RSEM)
profile_name: mRNA expression (RNA Seq V2 RSEM)""",


	"mrna_seq_v2_rsem_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_v2_mrna_median_all_sample_Zscores
show_profile_in_analysis_tab: TRUE
profile_name: mRNA expression z-scores relative to all samples (log RNA Seq V2 RSEM)
profile_description: Log-transformed mRNA expression z-scores compared to the expression distribution of all samples (RNA Seq V2 RSEM).
data_filename: data_mrna_seq_v2_rsem_zscores_ref_all_samples.txt""",


	"log2_cna": """genetic_alteration_type: COPY_NUMBER_ALTERATION
datatype: LOG2-VALUE
stable_id: log2CNA
show_profile_in_analysis_tab: false
profile_description: Log2 copy-number values for each gene (from Affymetrix SNP6).
profile_name: Log2 copy-number values
data_filename: data_log2_cna.txt""",


	"microbiome": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: MICROBIOME_SIGNATURE
datatype: LIMIT-VALUE
stable_id: microbiome_signature
profile_name: Microbiome Signatures (log RNA Seq CPM)
profile_description: Microbial Signatures (log-cpm) from whole-transcriptome sequencing studies of TCGA (Poore et al. Nature 2020).
data_filename: data_microbiome.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0
value_sort_order: ASC
generic_entity_meta_properties: NAME,DESCRIPTION,URL""",


	"mrna_seq_rpkm": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
stable_id: rna_seq_mrna
profile_description: mRNA expression (RNA-Seq FPKM)
show_profile_in_analysis_tab: false
profile_name: mRNA Expression (RNA-Seq FPKM)
data_filename: data_mrna_seq_rpkm.txt""",


	"mrna_seq_rpkm_zscores_ref_diploid_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_mrna_median_Zscores
profile_description: mRNA expression (Z-Scores)
show_profile_in_analysis_tab: true
profile_name: mRNA Expression z-Scores (RNA-Seq)
data_filename: data_mrna_seq_rpkm_zscores_ref_diploid_samples.txt""",


	"mrna_seq_rpkm_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_mrna_median_all_sample_Zscores
show_profile_in_analysis_tab: true
profile_description: Log-transformed mRNA z-scores compared to the expression distribution of all samples (RNA Seq FPKM).
profile_name: mRNA expression z-scores relative to all samples (log RNA Seq FPKM)
data_filename: data_mrna_seq_rpkm_zscores_ref_all_samples.txt""",


	"mrna_seq_v2_rsem": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
data_filename: data_mrna_seq_v2_rsem.txt
stable_id: rna_seq_v2_mrna
show_profile_in_analysis_tab: false
profile_description: mRNA gene expression (RNA Seq V2 RSEM)
profile_name: mRNA expression (RNA Seq V2 RSEM)""",


	"mrna_seq_v2_rsem_zscores_ref_diploid_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
data_filename: data_mrna_seq_v2_rsem_zscores_ref_diploid_samples.txt
stable_id: rna_seq_v2_mrna_median_Zscores
show_profile_in_analysis_tab: true
profile_description: mRNA expression z-scores (RNA Seq V2 RSEM) compared to the expression distribution of each gene tumors that are diploid for this gene.
profile_name: mRNA expression z-scores relative to diploid samples (RNA Seq V2 RSEM)""",


	"rmrna_seq_v2_rsem_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_v2_mrna_median_all_sample_Zscores
show_profile_in_analysis_tab: TRUE
profile_name: mRNA expression z-scores relative to all samples (log RNA Seq V2 RSEM)
profile_description: Log-transformed mRNA expression z-scores compared to the expression distribution of all samples (RNA Seq V2 RSEM).
data_filename: data_mrna_seq_v2_rsem_zscores_ref_all_samples.txt""",


	"mrna_seq_v2_rsem_normal_samples": """stable_id: rna_seq_v2_mrna_median_normals
genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
show_profile_in_analysis_tab: FALSE
profile_name: mRNA expression of adjacent normal samples, RSEM (Batch normalized from Illumina HiSeq_RNASeqV2)
profile_description:mRNA expression of adjacent normal samples, RSEM (Batch normalized from Illumina HiSeq_RNASeqV2)
data_filename: data_mrna_seq_v2_rsem_normal_samples.txt""",


	"mrna_seq_v2_rsem_normal_samples_zscores_ref_normal_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_v2_mrna_median_normals_Zscores
show_profile_in_analysis_tab: TRUE
profile_name: mRNA expression of adjacent normal samples, z-scores relative to all normal samples (log RNA Seq V2 RSEM)
profile_description: Expression z-scores of adjacent normal samples compared to the expression distribution of all log-transformed mRNA expression of adjacent normal samples in the cohort.
data_filename: data_mrna_seq_v2_rsem_normal_samples_zscores_ref_normal_samples.txt""",


	"mrna_seq_v2_rsem_zscores_ref_normal_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_v2_mrna_median_all_sample_ref_normal_Zscores
show_profile_in_analysis_tab: TRUE
profile_name: mRNA expression z-scores relative to normal samples (log RNA Seq V2 RSEM)
profile_description: Expression z-scores of tumor samples compared to the expression distribution of all log-transformed mRNA expression of adjacent normal samples in the cohort.
data_filename: data_mrna_seq_v2_rsem_zscores_ref_normal_samples.txt""",


	"mrna_seq_cpm": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
stable_id: mrna_seq_cpm
show_profile_in_analysis_tab: false
profile_name: mRNA expression (RNA Seq CPM)
profile_description: Expression levels for genes in <NUM_CASES> <TUMOR_TYPE> cases (RNA Seq CPM).
data_filename: data_mrna_seq_cpm.txt""",


	"mrna_seq_cpm_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_seq_cpm_all_sample_Zscores
show_profile_in_analysis_tab: true
profile_description: Log-transformed mRNA z-scores compared to the expression distribution of all samples (RNA Seq CPM).
profile_name: mRNA expression z-scores relative to all samples (log RNA Seq CPM)
data_filename: data_mrna_seq_cpm_zscores_ref_all_samples.txt""",


	"mrna_seq_cpm_zscores_ref_diploid_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_seq_cpm_Zscores
show_profile_in_analysis_tab: false
profile_description: Expression level z-scores for genes in <NUM_CASES> <TUMOR_TYPE> cases (RNA Seq CPM).
profile_name: mRNA expression z-scores (RNA Seq CPM)
data_filename: data_mrna_seq_cpm_zscores_ref_diploid_samples.txt""",


	"mrna_seq_tpm": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
stable_id: mrna_seq_tpm
show_profile_in_analysis_tab: false
profile_name: mRNA expression (RNA Seq TPM) 
profile_description: Expression levels for genes in <NUM_CASES> <TUMOR_TYPE> cases (RNA Seq TPM).
data_filename: data_mrna_seq_tpm.txt""",


	"mrna_seq_tpm_zscores_ref_diploid_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_seq_tpm_Zscores
show_profile_in_analysis_tab: true
profile_description: mRNA z-scores compared to the expression distribution of each gene tumors that are diploid for this gene (RNA Seq TPM).
profile_name: mRNA expression z-scores relative to diploid samples (RNA Seq TPM)
data_filename: data_mrna_seq_tpm_zscores_ref_diploid_samples.txt""",


	"mrna_seq_tpm_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_seq_tpm_all_sample_Zscores
show_profile_in_analysis_tab: true
profile_description: Log-transformed mRNA z-scores compared to the expression distribution of all samples (RNA-Seq TPM).
profile_name: mRNA expression z-scores relative to all samples (log RNA Seq TPM)
data_filename: data_mrna_seq_tpm_zscores_ref_all_samples.txt""",


	"mrna_seq_fpkm": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
stable_id: rna_seq_mrna
profile_description: Expression levels.
show_profile_in_analysis_tab: false
profile_name: mRNA expression (FPKM)
data_filename: data_mrna_seq_fpkm.txt""",


	"mrna_seq_fpkm_zscores_ref_diploid_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_mrna_median_Zscores
show_profile_in_analysis_tab: TRUE
profile_name: mRNA Expression z-scores relative to diploid samples (RNA Seq FPKM)
profile_description: mRNA z-scores (RNA Seq FPKM) compared to the expression distribution of each gene tumors that are diploid for this gene.
data_filename: data_mrna_seq_fpkm_zscores_ref_diploid_samples.txt""",


	"mrna_seq_fpkm_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: rna_seq_mrna_median_all_sample_Zscores
show_profile_in_analysis_tab: true
profile_description: Log-transformed mRNA z-scores compared to the expression distribution of all samples (RNA Seq FPKM).
profile_name: mRNA expression z-scores relative to all samples (log RNA Seq FPKM)
data_filename: data_mrna_seq_fpkm_zscores_ref_all_samples.txt""",


	"mrna_seq_fpkm_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_seq_fpkm_all_sample_Zscores
show_profile_in_analysis_tab: true
profile_description: Log-transformed mRNA z-scores compared to expression distribution of all samples (RNA Seq FPKM).
profile_name: mRNA expression z-scores relative to all samples (FPKM capture, log2 transformed)
data_filename: data_mrna_seq_fpkm_zscores_ref_all_samples.txt""",


	"mrna_seq_fpkm_capture": """stable_id: mrna_seq_fpkm_capture
profile_name: mRNA expression (FPKM capture)
profile_description: mRNA expression from capture (RNA Seq FPKM)
genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
show_profile_in_analysis_tab: false
data_filename: data_mrna_seq_fpkm_capture.txt""",


	"data_mrna_seq_fpkm_capture_zscores_ref_diploid_samples": """stable_id: mrna_seq_fpkm_capture_Zscores
profile_name: mRNA expression z-scores relative to diploid samples (FPKM capture)
profile_description: mRNA expression from capture Z-scores (RNA Seq FPKM) compared to the expression distribution of each gene tumors that are diploid for this gene.
genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
show_profile_in_analysis_tab: true
data_filename: data_mrna_seq_fpkm_capture_zscores_ref_diploid_samples.txt""",


	"mrna_seq_fpkm_capture_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_seq_fpkm_capture_all_sample_Zscores
show_profile_in_analysis_tab: true
profile_description: Log-transformed mRNA z-scores compared to expression distribution of all samples (RNA Seq FPKM).
profile_name: mRNA expression z-scores relative to all samples (log FPKM capture)
data_filename: data_mrna_seq_fpkm_capture_zscores_ref_all_samples.txt""",


	"mrna_seq_fpkm_polya": """stable_id: mrna_seq_fpkm_polya
profile_name: mRNA expression (FPKM polyA)
profile_description: mRNA expression from polyA (RNA Seq FPKM)
genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
show_profile_in_analysis_tab: false
data_filename: data_mrna_seq_fpkm_polya.txt""",


	"mrna_seq_fpkm_polya_zscores_ref_diploid_samples": """stable_id: mrna_seq_fpkm_polya_Zscores
profile_name: mRNA expression z-scores relative to diploid samples (FPKM polyA)
profile_description: mRNA expression from polyA Z-scores (RNA Seq FPKM) compared to the expression distribution of each gene tumors that are diploid for this gene.
genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
show_profile_in_analysis_tab: true
data_filename: data_mrna_seq_fpkm_polya_zscores_ref_diploid_samples.txt""",


	"mrna_seq_fpkm_polya_zscores_ref_all_samples": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
stable_id: mrna_seq_fpkm_polya_all_sample_Zscores
show_profile_in_analysis_tab: true
profile_description: Log-transformed mRNA z-scores compared to expression distribution of all samples (RNA Seq FPKM polyA).
profile_name: mRNA expression z-scores relative to all samples (log FPKM polyA)
data_filename: data_mrna_seq_fpkm_polya_zscores_ref_all_samples.txt""",


	"expression": """genetic_alteration_type: MRNA_EXPRESSION
datatype: CONTINUOUS
stable_id: rna_seq_mrna
show_profile_in_analysis_tab: true
profile_name: mRNA expression (bulk RNA-seq) 
profile_description: Expression levels 
data_filename: data_expression.txt""",


	"mirna": """datatype: CONTINUOUS
data_filename: data_mirna.txt
show_profile_in_analysis_tab: false
stable_id: mirna
profile_name: miRNA expression (FPKM uq)
profile_description: Micro RNA expression by miRNA abundance in FPKM values.""",


	"mirna_zscores": """genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
data_filename: data_mirna_zscores.txt
show_profile_in_analysis_tab: true
stable_id: mirna_median_Zscores
profile_name: Z-scores of miRNA expression (FPKM-UQ)
profile_description: Z-scores of miRNA abundance in FPKM-UQ values, calculated over all diploid samples.""",


	"mrna_mirna_merged_zscores": """stable_id: mrna_merged_median_Zscores
show_profile_in_analysis_tab: false
profile_name: mRNA/miRNA expression Z-scores (all genes)
profile_description: mRNA and microRNA Z-scores merged: mRNA expression Z-scores compared to diploid tumors (diploid for each gene), median values from all three mRNA expression platforms; and miRNA z-Scores compared to all tumours.
genetic_alteration_type: MRNA_EXPRESSION
datatype: Z-SCORE
data_filename: data_mrna_mirna_merged_zscores.txt""",


	"drug_treatment_AUC": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: TREATMENT_RESPONSE
datatype: LIMIT-VALUE
stable_id: CCLE_drug_treatment_AUC
profile_name: Treatment response: AUC
profile_description: Area under the sigmoidal curve, derived from fitting the drug screening tests to a mixed-effects model (Vis et al. 2016).
data_filename: data_drug_treatment_auc.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0
value_sort_order: ASC
generic_entity_meta_properties: NAME,URL,DESCRIPTION""",


	"drug_treatment_zscore": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: TREATMENT_RESPONSE
datatype: LIMIT-VALUE
stable_id: CCLE_drug_treatment_IC50
profile_name: Treatment response: IC50
profile_description: IC50 values (in micromolar) of cell lines responding to various drug treatments. The IC50 values are intra-/extrapolated from a sigmoidal curve by fitting a mixed-effects model (Vis et al. 2016).
data_filename: data_drug_treatment_ic50.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0.000001
value_sort_order: ASC
generic_entity_meta_properties: NAME,URL,DESCRIPTION""",


	"drug_treatment_zscore": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: TREATMENT_RESPONSE
datatype: LIMIT-VALUE
stable_id: CCLE_drug_treatment_zscore
profile_name: Treatment response: Z-score of IC50
profile_description: Z-scores of the ln-transformed IC50 values of drug-treated cell lines. These Z-scores represent the relative (standardized) inhibitory potency of each drug over every cell line treated with that drug. The IC50 values were intra-/extrapolated from a sigmoidal curve, based on a mixed-effects model (Vis et al. 2016).
data_filename: data_drug_treatment_zscore.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0
value_sort_order: ASC
generic_entity_meta_properties: NAME,URL,DESCRIPTION""",


	"microbiome": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: MICROBIOME_SIGNATURE
datatype: LIMIT-VALUE
stable_id: microbiome_signature
profile_name: Microbiome Signatures (log RNA Seq CPM)
profile_description: Microbial Signatures (log-cpm) from whole-transcriptome sequencing studies of TCGA (Poore et al. Nature 2020).
data_filename: data_microbiome.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0
value_sort_order: ASC
generic_entity_meta_properties: NAME,DESCRIPTION,URL""",


	"mutational_signature_contribution_v2": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: MUTATIONAL_SIGNATURE
datatype: LIMIT-VALUE
stable_id: mutational_signature_contribution_v2
profile_name: mutational signature contribution v2
profile_description: profile for contribution value of mutational signatures (COSMIC version 2)
data_filename: data_mutational_signature_contribution_v2.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0
value_sort_order: ASC
generic_entity_meta_properties: NAME,DESCRIPTION,URL""",


	"mutational_signature_pvalue_v2": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: MUTATIONAL_SIGNATURE
datatype: LIMIT-VALUE
stable_id: mutational_signature_pvalue_v2
profile_name: mutational signature pvalue v2
profile_description: profile for pvalue of mutational signatures (COSMIC version 2)
data_filename: data_mutational_signature_pvalue_v2.txt
show_profile_in_analysis_tab: true
pivot_threshold_value: 0
value_sort_order: ASC
generic_entity_meta_properties: NAME,DESCRIPTION,URL""",


	"resource_definition": """resource_type: DEFINITION
data_filename: data_resource_definition.txt""",


	"resource_study": """resource_type: STUDY
data_filename: data_resource_study.txt""",
	
	
	"resource_patient.txt": """resource_type: PATIENT
data_filename: data_resource_patient.txt""",


	"resource_sample": """resource_type: SAMPLE
data_filename: data_resource_sample.txt""",


	"acetylprotein_quantification": """genetic_alteration_type: GENERIC_ASSAY
show_profile_in_analysis_tab: true
data_filename: data_acetylprotein_quantification.txt
datatype: LIMIT-VALUE
stable_id: acetylprotein_quantification
profile_name: Acetylprotein abundance ratio
profile_description: Abundance ratio for acetylproteins measured by mass spectrometry.
generic_assay_type: Acetylproteome
generic_entity_meta_properties: NAME,DESCRIPTION,GENE_SYMBOL""",


	"lipidome_negative_quantification": """genetic_alteration_type: GENERIC_ASSAY
show_profile_in_analysis_tab: true
data_filename: data_lipidome_negative_quantification.txt
datatype: LIMIT-VALUE
stable_id: lipidome_negative_quantification
profile_name: Lipid abundance ratio (negative mode)
profile_description: Abundance log2 ratio for lipids measured by mass spectrometry (negative mode).
generic_assay_type: Lipidome
generic_entity_meta_properties: NAME""",


	"lipidome_positive_quantification": """genetic_alteration_type: GENERIC_ASSAY
show_profile_in_analysis_tab: true
data_filename: data_lipidome_positive_quantification.txt
datatype: LIMIT-VALUE
stable_id: lipidome_positive_quantification
profile_name: Lipid abundance ratio (positive mode)
profile_description: Abundance log2 ratio for lipids measured by mass spectrometry (positive mode).
generic_assay_type: Lipidome
generic_entity_meta_properties: NAME""",


	"circular_rna": """genetic_alteration_type: GENERIC_ASSAY
show_profile_in_analysis_tab: true
data_filename: data_circular_rna.txt
datatype: LIMIT-VALUE
stable_id: crna_quantification
profile_name: cRNA expression (FPKM-UQ)
profile_description: Expression of circular RNA abundance in FPKM-UQ values
generic_assay_type: cRNA
generic_entity_meta_properties: NAME,DESCRIPTION,GENE_SYMBOL""",


	"immune_cell_expression_signature": """genetic_alteration_type: GENERIC_ASSAY
generic_assay_type: IMMUNE_CELL_SIGNATURE
datatype: LIMIT-VALUE
stable_id: immune_cell_signature
profile_name: Immune Cell Expression Signatures (Absolute Scores)
profile_description: Immune Cell Expression Signatures (absolute scores for each cell type) generated by CIBERSORT from RNA-seq RPKM data.
data_filename: data_immune_cell_expression_signatures.txt
show_profile_in_analysis_tab: false
pivot_threshold_value: 0.001
value_sort_order: DESC
patient_level: true
generic_entity_meta_properties: Name"""
}


parser = argparse.ArgumentParser(
                    prog = 'metafile generator',
                    description = 'Generate metafiles for datafiles')

parser.add_argument('-d', '--study_directory', help="the folder that has all the study data files")
parser.add_argument('-s', '--study_id', help="name of the cancer_study_identifier")
parser.add_argument('-c', '--create_meta_cna_seg', help="Yes / No to create meta CNA seg file")

args = parser.parse_args()

files = files = glob.glob(f"{args.study_directory}/data_*.txt")
for file in files:
    filename = file.split("/")[-1].split(".")[0].split("data_")[-1]
    if filename in dict:
        with open(f"meta_{filename}.txt", "w") as ff:
            ff.writelines(f"cancer_study_identifier: {args.study_id}\n")
            ff.writelines(dict[filename])

if args.create_meta_cna_seg == "yes":
	with open(f"meta_cna_hg19_seg.txt", "w") as ff:
		ff.writelines(f"cancer_study_identifier: <STUDY_ID>\n")
		ff.writelines("genetic_alteration_type: COPY_NUMBER_ALTERATION\n")
		ff.writelines("datatype: SEG\n")
		ff.writelines("show_profile_in_analysis_tab: false\n")
		ff.writelines("description: Somatic CNA data (copy number ratio from tumor samples minus ratio from matched normals) from TCGA.\n")
		ff.writelines("profile_name: Segment data values\n")
		ff.writelines("reference_genome_id: hg19\n")
		ff.writelines("data_filename: data_cna_hg19.seg\n")