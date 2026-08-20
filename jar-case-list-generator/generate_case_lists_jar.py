#!/usr/bin/env python3
"""Generate missing case lists for cBioPortal studies, mirroring the pipelines
JAR exactly (FileUtilsImpl.generateCaseLists / getCaseListFromStagingFile /
writeCaseListFile / StableIdUtil.getSampleId; caller ImporterImpl.importCaseLists
runs with overwrite=false — gap-fill only, existing files untouched).

Java behaviors replicated deliberately, including the surprising ones:
  - Sample-id header recognition is ONLY `Tumor_Sample_Barcode` and `SAMPLE_ID`.
    A file whose header has neither (e.g. `Sample_Id`-headed SV files, CNA
    matrixes) is treated as a matrix file: every header token not in the
    NON_CASE_IDS blocklist is added as a case id.
  - `#sequenced_samples: A B C` inline header in any staging file short-circuits
    that file's id list; a standalone `sequenced_samples.txt` overrides any
    `data_mutations*` staging file.
  - TCGA barcode standardization (StableIdUtil.getSampleId): "Tumor"->"01",
    "Normal"->"11", truncate to TCGA-XX-XXXX-NN; patient-only barcodes get
    "-01" appended. Non-TCGA ids pass through untouched.
  - Intersection (`&`) case lists require ALL listed staging files to exist and
    all to be non-empty; union (`|`) takes what's there. A pattern containing
    both delimiters splits on `|` (Java checks union first).
  - Config fields are trimmed (Java CaseListMetadata trims every column).
  - Output format matches byte-for-byte: meta lines in Java's order and a
    trailing tab after the last case id.
  - Empty case sets are never written.
Known deviation: Java accumulates ids in a HashSet (arbitrary JVM hash order);
this script keeps first-seen order. Membership is identical.

Usage:
  generate_case_lists_jar.py --config case_list_config.tsv \
      [--dry-run] study_dir [study_dir ...]

Each study_dir is a study directory (containing staging files and optionally
case_lists/). The study id is read from meta_study.txt
(cancer_study_identifier), falling back to the directory basename.
"""
import argparse
import os
import re
import sys

NON_CASE_IDS = {"MIRNA", "LOCUS", "ID", "GENE SYMBOL", "ENTREZ_GENE_ID",
                "HUGO_SYMBOL", "LOCUS ID", "CYTOBAND", "COMPOSITE.ELEMENT.REF",
                "HYBRIDIZATION REF"}
MUTATION_CASE_ID_COLUMN_HEADER = "Tumor_Sample_Barcode"
SAMPLE_ID_COLUMN_HEADER = "SAMPLE_ID"
MUTATION_CASE_LIST_META_HEADER = "sequenced_samples"
MUTATION_STAGING_GENERAL_PREFIX = "data_mutations"
SEQUENCED_SAMPLES_FILENAME = "sequenced_samples.txt"
CANCER_STUDY_TAG = "<CANCER_STUDY>"
NUM_CASES_TAG = "<NUM_CASES>"
CASE_LIST_DIRECTORY_NAME = "case_lists"

TCGA_SAMPLE_BARCODE_REGEX = re.compile(r"^(TCGA-\w\w-\w\w\w\w-\d\d).*$")


def java_split(line, delim="\t"):
    """Java String.split default: trailing empty strings removed."""
    parts = line.split(delim)
    while parts and parts[-1] == "":
        parts.pop()
    return parts


def get_sample_id(barcode):
    """StableIdUtil.getSampleId."""
    if not barcode.startswith("TCGA"):
        return barcode
    if "Tumor" in barcode:
        cleaned = barcode.replace("Tumor", "01")
    elif "Normal" in barcode:
        cleaned = barcode.replace("Normal", "11")
    else:
        cleaned = barcode
    parts = cleaned.split("-")
    try:
        sample_id = parts[0] + "-" + parts[1] + "-" + parts[2] + "-" + parts[3]
    except IndexError:
        return barcode + "-01"
    m = TCGA_SAMPLE_BARCODE_REGEX.match(sample_id)
    return m.group(1) if m else sample_id


def read_config(path):
    """Rows of the case-list config TSV, fields trimmed like CaseListMetadata."""
    rows = []
    with open(path) as f:
        header = f.readline()
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            cols = [c.strip() for c in line.split("\t")]
            if len(cols) < 7:
                continue
            rows.append({
                "case_list_filename": cols[0],
                "staging_filenames": cols[1],
                "meta_stable_id": cols[2],
                "meta_case_list_category": cols[3],
                "meta_cancer_study_id": cols[4],
                "meta_case_list_name": cols[5],
                "meta_case_list_description": cols[6],
            })
    return rows


def case_list_from_sequenced_samples_file(path):
    seen = dict.fromkeys([])
    out = []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\r\n")
            if line not in seen:
                seen[line] = True
                out.append(line)
    return out


def case_list_from_staging_file(study_dir, staging_filename):
    """FileUtilsImpl.getCaseListFromStagingFile. Returns [] if file absent."""
    if MUTATION_STAGING_GENERAL_PREFIX in staging_filename:
        seq = os.path.join(study_dir, SEQUENCED_SAMPLES_FILENAME)
        if os.path.exists(seq):
            return case_list_from_sequenced_samples_file(seq)
    path = os.path.join(study_dir, staging_filename)
    if not os.path.exists(path):
        return []
    case_set = []
    seen = set()
    inline_prefix = "#" + MUTATION_CASE_LIST_META_HEADER + ":"
    with open(path) as f:
        process_header = True
        id_column = 0
        for raw in f:
            line = raw.rstrip("\r\n")
            if line.startswith("#"):
                if line.startswith(inline_prefix):
                    return line[len(MUTATION_CASE_LIST_META_HEADER) + 2:].strip().split()
                continue
            row = java_split(line)
            if process_header:
                maf_idx = row.index(MUTATION_CASE_ID_COLUMN_HEADER) if MUTATION_CASE_ID_COLUMN_HEADER in row else -1
                sample_idx = row.index(SAMPLE_ID_COLUMN_HEADER) if SAMPLE_ID_COLUMN_HEADER in row else -1
                if maf_idx == -1 and sample_idx == -1:
                    # not a MAF/clinical file: header itself carries the case ids
                    for token in row:
                        if token.upper() in NON_CASE_IDS:
                            continue
                        if token not in seen:
                            seen.add(token)
                            case_set.append(token)
                    break
                id_column = maf_idx if maf_idx != -1 else sample_idx
                process_header = False
                continue
            # Java List.get throws on short rows; surface the same failure
            if id_column >= len(row):
                raise IndexError(f"{staging_filename}: data row has no column {id_column}: {line[:80]}")
            case_id = row[id_column]
            if case_id not in seen:
                seen.add(case_id)
                case_set.append(case_id)
    return case_set


def write_case_list_file(case_list_dir, study_id, spec, case_list):
    os.makedirs(case_list_dir, exist_ok=True)
    path = os.path.join(case_list_dir, spec["case_list_filename"])
    stable_id = spec["meta_stable_id"].replace(CANCER_STUDY_TAG, study_id)
    description = spec["meta_case_list_description"].replace(NUM_CASES_TAG, str(len(case_list)))
    with open(path, "w") as w:
        w.write("cancer_study_identifier: " + study_id + "\n")
        w.write("stable_id: " + stable_id + "\n")
        w.write("case_list_name: " + spec["meta_case_list_name"] + "\n")
        w.write("case_list_description: " + description + "\n")
        w.write("case_list_category: " + spec["meta_case_list_category"] + "\n")
        w.write("case_list_ids: ")
        for case_id in case_list:
            w.write(case_id + "\t")
        w.write("\n")
    return path


def study_identifier(study_dir):
    meta = os.path.join(study_dir, "meta_study.txt")
    if os.path.exists(meta):
        with open(meta) as f:
            for line in f:
                if line.startswith("cancer_study_identifier:"):
                    return line.split(":", 1)[1].strip()
    return os.path.basename(os.path.normpath(study_dir))


def generate_for_study(study_dir, config_rows, dry_run):
    study_id = study_identifier(study_dir)
    case_list_dir = os.path.join(study_dir, CASE_LIST_DIRECTORY_NAME)
    written, skipped_existing = [], []
    for spec in config_rows:
        target = os.path.join(case_list_dir, spec["case_list_filename"])
        if os.path.exists(target):  # overwrite=false: gap-fill only
            skipped_existing.append(spec["case_list_filename"])
            continue
        patterns = spec["staging_filenames"]
        union = "|" in patterns          # Java checks union first
        intersection = (not union) and "&" in patterns
        if union:
            staging_filenames = patterns.split("|")
        elif intersection:
            staging_filenames = patterns.split("&")
        else:
            staging_filenames = [patterns]
        if intersection and not all(
                os.path.exists(os.path.join(study_dir, s)) for s in staging_filenames):
            continue
        case_set = []       # LinkedHashSet semantics
        case_seen = set()
        num_processed = 0
        for staging_filename in staging_filenames:
            case_list = case_list_from_staging_file(study_dir, staging_filename)
            if not case_list:
                continue
            case_list = [get_sample_id(c) for c in case_list]
            if intersection:
                if not case_seen:
                    for c in case_list:
                        if c not in case_seen:
                            case_seen.add(c)
                            case_set.append(c)
                else:
                    keep = set(case_list)
                    case_set = [c for c in case_set if c in keep]
                    case_seen = set(case_set)
            else:
                for c in case_list:
                    if c not in case_seen:
                        case_seen.add(c)
                        case_set.append(c)
            num_processed += 1
        if not case_set:
            continue
        if intersection and num_processed != len(staging_filenames):
            continue
        if dry_run:
            written.append(f"{spec['case_list_filename']} ({len(case_set)} cases) [dry-run]")
        else:
            write_case_list_file(case_list_dir, study_id, spec, case_set)
            written.append(f"{spec['case_list_filename']} ({len(case_set)} cases)")
    return study_id, written, skipped_existing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="case_list_config.tsv")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("study_dirs", nargs="+")
    args = ap.parse_args()

    config_rows = read_config(args.config)
    if not config_rows:
        sys.exit("empty case-list config")
    exit_code = 0
    for study_dir in args.study_dirs:
        if not os.path.isdir(study_dir):
            print(f"ERROR\t{study_dir}\tnot a directory", flush=True)
            exit_code = 1
            continue
        try:
            study_id, written, skipped = generate_for_study(study_dir, config_rows, args.dry_run)
        except Exception as e:
            print(f"ERROR\t{study_dir}\t{e}", flush=True)
            exit_code = 1
            continue
        detail = "; ".join(written) if written else "nothing to generate"
        print(f"OK\t{study_id}\tgenerated: {detail}; existing kept: {len(skipped)}", flush=True)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
