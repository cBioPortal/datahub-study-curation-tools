#!/usr/bin/env python3
"""Add missing meta files for data_timeline*.txt and data_clinical_supp*.txt.

Gap-fill only: scans every study directory under root (default: public/) and
writes a meta file for each matching data file that no existing meta file
declares. A data file counts as covered when meta_<suffix>.txt exists for it OR
any meta_*.txt in the study names it in data_filename (meta file names are
free-form, e.g. meta_timeline.txt -> data_timeline_treatment.txt). Existing
meta files and meta_study.txt are never touched.

    cancer_study_identifier: <from meta_study.txt>
    genetic_alteration_type: CLINICAL
    datatype: TIMELINE | SAMPLE_ATTRIBUTES | PATIENT_ATTRIBUTES
    data_filename: <data file name>

Timeline files get datatype TIMELINE. Supp files get SAMPLE_ATTRIBUTES when the
column header contains SAMPLE_ID, else PATIENT_ATTRIBUTES; a supp file with
fewer than 4 leading '#' rows still gets a meta file but is reported, since the
validator will likely reject the data file itself.

Why a separate script: the config-driven generators (generate_meta_files.py
here, generate_missing_metafiles.py in internal_data_curation_automation/) map
every data_timeline_*.txt / data_clinical_supp_*.txt to one meta_timeline.txt /
meta_clinical.txt with datatype CLINICAL. metaImport needs one meta file per
data file with the datatypes above, and the supp datatype depends on the data
file's header, so it cannot come from the config.

Usage: add_missing_clinical_meta.py [root_dir] [--dry-run]
"""
import argparse
from pathlib import Path

META_TEMPLATE = """\
cancer_study_identifier: {study_id}
genetic_alteration_type: CLINICAL
datatype: {datatype}
data_filename: {data_filename}
"""


def study_id_from_meta(study_dir):
    meta_study = study_dir / "meta_study.txt"
    if not meta_study.exists():
        return None
    for line in meta_study.read_text().splitlines():
        if line.startswith("cancer_study_identifier:"):
            return line.split(":", 1)[1].strip()
    return None


def declared_data_files(study_dir):
    """data_filename values declared by the study's existing meta files."""
    names = set()
    for meta in study_dir.glob("meta_*.txt"):
        for line in meta.read_text().splitlines():
            if line.startswith("data_filename:"):
                names.add(line.split(":", 1)[1].strip())
    return names


def supp_datatype(path):
    """Return (datatype, warning) from the supp file's leading '#' rows and
    column header. datatype is None for an empty file."""
    comment_rows = 0
    header = None
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                comment_rows += 1
                continue
            header = line.rstrip("\n").split("\t")
            break
    if header is None:
        return None, "empty file"
    warning = None
    if comment_rows < 4:
        warning = f"only {comment_rows} '#' header rows (validator expects 4+)"
    datatype = "SAMPLE_ATTRIBUTES" if "SAMPLE_ID" in header else "PATIENT_ATTRIBUTES"
    return datatype, warning


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("root", nargs="?", default="public",
                    help="directory whose immediate subdirectories are studies (default: public)")
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    args = ap.parse_args()
    root = Path(args.root)

    created, skipped, warnings = 0, [], []
    declared = {}  # study_dir -> data files already covered by a meta file
    targets = [(p, "TIMELINE") for p in root.glob("*/data_timeline*.txt")]
    targets += [(p, None) for p in root.glob("*/data_clinical_supp*.txt")]
    for data_file, datatype in sorted(targets):
        study_dir = data_file.parent
        meta_file = study_dir / ("meta_" + data_file.name[len("data_"):])
        if study_dir not in declared:
            declared[study_dir] = declared_data_files(study_dir)
        if meta_file.exists() or data_file.name in declared[study_dir]:
            continue
        study_id = study_id_from_meta(study_dir)
        if study_id is None:
            skipped.append(f"{study_dir.name}: no meta_study.txt")
            continue
        if datatype is None:
            datatype, warning = supp_datatype(data_file)
            if datatype is None:
                skipped.append(f"{data_file}: {warning}")
                continue
            if warning:
                warnings.append(f"{data_file}: {warning}")
        content = META_TEMPLATE.format(
            study_id=study_id, datatype=datatype, data_filename=data_file.name)
        if args.dry_run:
            print(f"would write {meta_file} ({datatype})")
        else:
            meta_file.write_text(content)
            print(f"wrote {meta_file} ({datatype})")
        created += 1

    print(f"\n{created} meta files {'needed' if args.dry_run else 'written'}")
    for s in skipped:
        print(f"SKIPPED {s}")
    for w in warnings:
        print(f"WARNING {w}")


if __name__ == "__main__":
    main()
