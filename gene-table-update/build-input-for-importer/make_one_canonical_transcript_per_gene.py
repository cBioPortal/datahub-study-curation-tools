#!/usr/bin/env python3
import pandas as pd
import numpy as np
import itertools
import argparse


def get_overrides_transcript(overrides_tables, ensembl_table, hgnc_symbol, hgnc_canonical_genes):
    """Find canonical transcript id for given hugo symbol. Overrides_tables is
    a list of different override tables"""
    for overrides in overrides_tables:
        try:
            # corner case when there are multiple overrides for a given gene symbol
            if overrides.loc[hgnc_symbol].ndim > 1:
                transcript = overrides.loc[hgnc_symbol].isoform_override.values[0]
            else:
                transcript = overrides.loc[hgnc_symbol].isoform_override
            return transcript
        except KeyError:
            pass
    else:
        # get ensembl canonical version otherwise
        return get_ensembl_canonical_transcript_id_from_hgnc_then_ensembl(ensembl_table, hgnc_symbol, hgnc_canonical_genes, 'transcript_stable_id')


def pick_canonical_longest_transcript_from_ensembl_table(ensembl_rows, field):
    """Get canonical transcript id with largest protein length or if there is
    no such thing, pick biggest gene id"""
    return ensembl_rows.sort_values('is_canonical protein_length gene_stable_id'.split(), ascending=False)[field].values[0]


def get_ensembl_canonical(ensembl_rows, field):
    if (ensembl_rows.ndim == 1 and len(ensembl_rows) == 0) or (ensembl_rows.ndim == 2 and len(ensembl_rows) == 0):
        return np.nan
    elif ensembl_rows.ndim == 1:
        return ensembl_rows[field]
    elif ensembl_rows.ndim == 2:
        if len(ensembl_rows) == 1:
            return ensembl_rows[field].values[0]
        else:
            return pick_canonical_longest_transcript_from_ensembl_table(ensembl_rows, field)


def get_ensembl_canonical_transcript_id_from_hgnc_then_ensembl(ensembl_table, hgnc_symbol, hgnc_canonical_genes, field):
    """Determine canonical transcript based on hgnc mappings to ensembl id.
    If not possible use ensembl's data."""
    try:
        hgnc_gene_rows = hgnc_canonical_genes.loc[hgnc_symbol]
    except KeyError:
        raise(Exception("Unknown hugo symbol"))

    if hgnc_gene_rows.ndim == 1:
        result = get_ensembl_canonical(ensembl_table[ensembl_table.gene_stable_id == hgnc_gene_rows.ensembl_id], field)
        if pd.isnull(result):
            # use ensembl data to find canonical transcript if nan is found
            # there's actually 222 of these (see notebook)
            try:
                return get_ensembl_canonical(ensembl_table.loc[hgnc_symbol], field)
            except KeyError:
                return np.nan
        else:
            return result
    else:
        raise(Exception("One hugo symbol expected in hgnc_canonical_genes"))


def lowercase_set(x):
    return set({i.lower() for i in x})


def ignore_rna_gene(x):
    return set({i for i in x if not i.startswith('rn') and not i.startswith('mir') and not i.startswith('linc')})


def ignore_certain_genes(x):
    ignore_genes = {'fam25hp', 'rmrpp1', 'hla-as1', 'pramef16', 'arid4b-it1',
    'ctglf8p', 'htr4-it1', 'nicn1-as1', 'pramef3', 'c9orf38', 'tbc1d4-as1',
    'rmrpp3', 'magi2-it1', 'rmrpp2', 'rmrpp4', 'ercc6-pgbd3', 'tbce-as1', 'hpvc1', 'fam231a', 'fam231b', 'fam231c', 'fam231d'}

    return set({i for i in x if i not in ignore_genes})


def main(ensembl_biomart_geneids_transcript_info,
         hgnc_complete_set,
         isoform_overrides_uniprot,
         isoform_overrides_at_mskcc,
         isoform_overrides_genome_nexus):
    # input files
    transcript_info_df = pd.read_csv(ensembl_biomart_geneids_transcript_info, sep='\t', dtype={'is_canonical':bool})
    transcript_info_df = transcript_info_df.drop_duplicates()
    uniprot = pd.read_csv(isoform_overrides_uniprot, sep='\t')\
        .rename(columns={'enst_id':'isoform_override'})\
        .set_index('gene_name'.split())
    mskcc = pd.read_csv(isoform_overrides_at_mskcc, sep='\t')\
        .rename(columns={'enst_id':'isoform_override'})\
        .set_index('gene_name'.split())
    custom = pd.read_csv(isoform_overrides_genome_nexus, sep='\t')\
        .rename(columns={'enst_id':'isoform_override'})\
        .set_index('gene_name'.split())
    hgnc_df = pd.read_csv(hgnc_complete_set, sep='\t', dtype=object)

    # Convert new column names to old stable column names. If this is not done properly, Genome Nexus and any other
    # downstream applications break
    # TODO: Update Genome Nexus to accept the latest HGNC column names so that remapping is not necessary.
    '''column_name_mapping = {'name': 'approved_name',
                           'symbol': 'approved_symbol',
                           'prev_symbol': 'previous_symbols',
                           'alias_symbol': 'synonyms',
                           'location': 'chromosome',
                           'entrez_id': 'entrez_gene_id',
                           'ena': 'accession_numbers',
                           'refseq_accession': 'refseq_ids',
                           'uniprot_ids': 'uniprot_id'}
    hgnc_df.rename(columns=column_name_mapping, inplace=True)'''

    hugos = hgnc_df['symbol'].unique()
    hgnc_df = hgnc_df.set_index('symbol')
    # assume each row has approved symbol
    assert(len(hugos) == len(hgnc_df))

    '''# only test the cancer genes for oddities (these are very important)
    cgs = set(pd.read_csv('mappings/transcripts/oncokb_cancer_genes_list_20170926.txt',sep='\t')['Hugo Symbol'])
    # each cancer gene stable id should have only one associated cancer gene symbol
    assert(transcript_info_df[transcript_info_df.hgnc_symbol.isin(cgs)].groupby('gene_stable_id').hgnc_symbol.nunique().sort_values().nunique() == 1)
    # each transcript stable id always belongs to only one gene stable id
    assert(transcript_info_df.groupby('transcript_stable_id').gene_stable_id.nunique().sort_values().nunique() == 1)'''

    # create hgnc_symbol to gene id mapping
    # ignore hugo symbols from ensembl data dump (includes prev symbols and synonyms)
    syns = hgnc_df.synonyms.str.strip('"').str.split("|").dropna()
    syns = set(itertools.chain.from_iterable(syns))

    # there is overlap between symbols, synonyms and previous symbols
    # therefore use logic in above order when querying
    '''assert(len(syns.intersection(previous_symbols)) == 0) #329
    assert(len(set(hugos).intersection(syns)) == 0) # 495
    assert(len(set(hugos).intersection(previous_symbols)) == 0) #227'''

    # all cancer genes and hugo symbols in ensembl data dump should be
    # contained in hgnc approved symbols and synonyms
    # c12orf9 is only in sanger's cancer gene census and has been withdrawn
    #assert(len(lowercase_set(set(cgs)) - set(['c12orf9']) - lowercase_set(set(hugos).union(syns))) == 0)
    no_symbols_in_hgnc = lowercase_set(transcript_info_df.hgnc_symbol.dropna().unique()) - lowercase_set(set(hugos).union(syns))
    #assert(len(ignore_certain_genes(ignore_rna_gene(no_symbols_in_hgnc))) == 0)

    transcript_info_df = transcript_info_df.set_index('hgnc_symbol')
    # for testing use
    # NSD3 replaces WHSC1L1
    # AATF has uniprot canonical transcript, not hgnc ensembl gene id, but
    # there are multiple in ensembl data dump
    # hugos = ['KRT18P53', 'NSD3', 'AATF']

    # TODO Optimize this part, as this part takes most time
    one_transcript_per_hugo_symbol = pd.Series(hugos).apply(lambda x:
        pd.Series(
            [
                get_ensembl_canonical_transcript_id_from_hgnc_then_ensembl(transcript_info_df, x, hgnc_df, 'gene_stable_id'),
                get_ensembl_canonical_transcript_id_from_hgnc_then_ensembl(transcript_info_df, x, hgnc_df, 'transcript_stable_id'),
                get_overrides_transcript([custom], transcript_info_df, x, hgnc_df),
                get_overrides_transcript([uniprot, custom], transcript_info_df, x, hgnc_df),
                get_overrides_transcript([mskcc, uniprot, custom], transcript_info_df, x, hgnc_df),
            ],
            index="""
            ensembl_canonical_gene
            ensembl_canonical_transcript
            genome_nexus_canonical_transcript
            uniprot_canonical_transcript
            mskcc_canonical_transcript
            """.split()
        )
    )
    one_transcript_per_hugo_symbol.index = hugos
    one_transcript_per_hugo_symbol.index.name = 'hgnc_symbol'

    # merge in other hgnc fields
    merged = pd.merge(hgnc_df.reset_index(), one_transcript_per_hugo_symbol.reset_index(), left_on='symbol', right_on='hgnc_symbol')
    del merged['hgnc_symbol']
    del merged['ensembl_id']
    merged = merged[['entrez_id'] + [col for col in merged.columns if col != 'entrez_id']]
    return(merged)
    
    '''# Replace '|' to ', ' to be in the correct format for Genome Nexus
    # TODO: Update Genome Nexus to accept the latest HGNC format so that replacement is not necessary.
    merged.replace({'\|': ', '}, inplace=True, regex=True)'''

if __name__ == "__main__":
    main(ensembl_biomart_geneids_transcript_info,
         hgnc_complete_set,
         isoform_overrides_uniprot,
         isoform_overrides_at_mskcc,
         isoform_overrides_genome_nexus)
