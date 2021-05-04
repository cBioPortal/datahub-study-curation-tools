#!/usr/bin/env python3

'''
This script uses the table of gene IDs downloaded from Ensembl BioMart,
and for each transcript it will query the Ensembl lookup REST API to derive
whether it is a canonical transcript for that gene, and also the length of 
the associated protein. The API calls will be done in blocks of <qsize>.
'''

import pandas as pd
import numpy as np
import requests
import sys
import os
import argparse
import re


def request_transcript_ids(transcripts, grch37):
    # Prepare API call
    if grch37:
        server = "https://grch37.rest.ensembl.org"
    else:
        server = "https://rest.ensembl.org"
    ext = "/lookup/id"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    transcripts_formatted = '", "'.join(transcripts)
    data = '{"expand": 1, "format":"full", "ids": ["%s"] }' % transcripts_formatted

    # Perform API call
    try:
        r = requests.post(server+ext, headers=headers, data=data)
    except requests.exceptions.ConnectionError:
        sys.stderr.write('Connection error when trying to query Ensembl API')
        sys.exit(1)

    # Check if return JSON is ok
    if not r.ok:
        r.raise_for_status()
        sys.exit(1)

    return r.json()


def get_transcript_info(transcript, ensembl_transcript_response):
    # Attempt to parse API response. Sometimes the transcript does not have an API response, probably because the API is
    # on a newer Ensembl release than the input files. Restarting the pipeline will attempt to continue.
    try:
        is_canonical = ensembl_transcript_response[transcript]['is_canonical']

        try:
            protein_stable_id = ensembl_transcript_response[transcript]['Translation']['id']
        except KeyError:
            protein_stable_id = np.nan

        try:
            # store as string to prevent integer -> float
            protein_length = str(ensembl_transcript_response[transcript]['Translation']['length'])
        except KeyError:
            protein_length = np.nan

    except TypeError:
        # print('Transcript %s has no response from Ensembl API, perhaps API is on newer Ensembl Release and ID is '
        #       'deprecated.' % transcript)
        is_canonical = np.nan
        protein_stable_id = np.nan
        protein_length = np.nan

    return pd.Series(
        [is_canonical, protein_stable_id, protein_length],
        index='is_canonical protein_stable_id protein_length'.split()
    )


def get_rest_jobs(tmp_dir, ngenes):
    '''Reads the tmp dir and determines which indexes still need processing.
    '''

    # determine which indices are already processed. Start and stop are derived from filenames.
    filename_re = re.compile('transcript_info_([0-9]*)-([0-9]*)\.txt$')
    tmp_files = [fn for fn in os.listdir(tmp_dir) if re.match(filename_re, fn)!=None]

    ngenes_set = set(range(0, ngenes))
    passed = set()
    for fn in tmp_files:
        match = re.search(filename_re, fn)
        start, end = int(match.group(1)), int(match.group(2))
        passed.update(range(start, end))

    return ngenes_set.difference(passed)


def lookup_transcripts(gene_info, tmp_dir, jobs, query_size, grch37=True):
    '''Loops through gene IDs and looks them up in Ensembl if needed.
    Results are merged into a data frame.
    '''

    last_job = len(gene_info)

    transcripts_all = gene_info['transcript_stable_id']
    transcript_info = pd.DataFrame({'is_canonical':[], 'protein_stable_id':[], 'protein_length':[]})

    # Iterate over transcripts
    for low_index in range(0, last_job, query_size):
        high_index = min(low_index + query_size, last_job)
        tmp_file = os.path.join(tmp_dir, 'transcript_info_%s-%s.txt' % (low_index, high_index))

        # Check whether we already processed all indices between start and stop, else redo this chunk.
        if len(set(range(low_index, high_index)).intersection(jobs)) > 0:
            print('Retrieving %s-%s of %s transcripts from Ensembl' % (low_index, high_index, last_job))
            transcripts_chunk = transcripts_all[low_index:high_index]

            # Request, decode and save info for transcripts
            decoded = request_transcript_ids(transcripts_chunk.tolist(), grch37)
            transcript_info_chunk = transcripts_chunk.apply(lambda x: get_transcript_info(x, decoded))
            transcript_info_chunk.to_csv(tmp_file, sep='\t', index=True)

    # read all files and append to final table, but keep index
    filename_re = re.compile('transcript_info_([0-9]*)-([0-9]*)\.txt$')
    tmp_files = [fn for fn in os.listdir(tmp_dir) if re.match(filename_re, fn)!=None]
    for fn in tmp_files:
        transcript_info_chunk = pd.read_csv(os.path.join(tmp_dir, fn), sep='\t', dtype=str, index_col=0)
        transcript_info = transcript_info.append(transcript_info_chunk, ignore_index=False)

    # Prepare transcript info table for merging. Sort and remove duplicate indices.
    transcript_info.sort_index(inplace=True)
    transcript_info = transcript_info.loc[~transcript_info.index.duplicated(keep='first')]
    transcript_info['is_canonical'] = transcript_info['is_canonical'].astype(str)
    transcript_info['is_canonical'].fillna('0', inplace=True)
    transcript_info['is_canonical'].replace({'1.0': '1', '0.0': '0'}, inplace=True)

    return transcript_info


def main(ensembl_biomart_geneids, ensembl_canonical_data, query_size):
    gene_info = pd.read_csv(ensembl_biomart_geneids, sep='\t', dtype=str)
    gene_info.columns = [c.lower().replace(' ', '_') for c in gene_info.columns]
    # print('Retrieving transcript information per gene to retrieve:\n'
    #       '- whether transcript is canonical\n'
    #       '- protein ID\n'
    #       '- protein length')
    # print('Can retrieve max 1000 transcripts per POST request, see '
    #       'https://github.com/Ensembl/ensembl-rest/wiki/POST-Requests')

    # Create temporary directory to save files for each transcripts file
    tmp_dir = os.path.join(os.path.dirname(ensembl_canonical_data), 'transcript_info/')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    ngenes = len(gene_info)

    # check if genome is grch37 (hg19) -- Ensembl has a dedicated mirror for grch37
    grch37 = 'grch37' in ensembl_biomart_geneids

    # get indexes todo
    jobs = get_rest_jobs(tmp_dir, ngenes)

    # retrieve transcript annotation
    transcript_info = lookup_transcripts(gene_info, tmp_dir, jobs, query_size, grch37)

    # check whether the total number of jobs is correct
    assert(len(transcript_info.index) == len(gene_info.index))
    # check whether the order of transcripts is incremental and nonredundant
    assert(list(transcript_info.index) == list(range(0, len(transcript_info.index))))

    # merge with gene IDs, save
    gene_transcript_info = pd.concat([gene_info, transcript_info], axis=1, sort=False)
    gene_transcript_info.to_csv(ensembl_canonical_data, sep='\t', index=False)


if __name__ == "__main__":
    main(ensembl_biomart_geneids, ensembl_canonical_data, query_size)
