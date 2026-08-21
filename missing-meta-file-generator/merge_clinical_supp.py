#!/usr/bin/env python3
"""Merge data_clinical_supp*.txt files into the study's main clinical file
(data_clinical_sample.txt or data_clinical_patient.txt, chosen by the supp
file's id column), then delete the supp data file and its meta file.

metaImport allows only one SAMPLE_ATTRIBUTES and one PATIENT_ATTRIBUTES file
per study, so supp files (which the pipelines JAR imported as extra clinical
files) must be folded in.

- Supp attribute columns are appended to the main file's columns.
- Header comment rows (#display/#description/#datatype/#priority) are extended
  from the supp file's corresponding rows; a 5-comment-line supp file (mixed
  attribute format with an attribute-types row) is handled by skipping its
  attribute-types row.
- Data joined on SAMPLE_ID (or PATIENT_ID). Main-file rows without supp data
  get blank values; supp rows whose id is absent from the main file are
  reported and dropped.

Usage: merge_clinical_supp.py <study_dir> [--dry-run] [--level auto|sample|patient]

--level picks the merge target: 'sample' -> data_clinical_sample.txt (join on
SAMPLE_ID), 'patient' -> data_clinical_patient.txt (join on PATIENT_ID),
'auto' (default) -> by whichever id column the supp file carries (SAMPLE_ID
preferred). Forcing a level requires the supp file to carry that id column.
"""
import glob
import os
import sys


def parse_clinical(path):
    comments = []
    with open(path) as f:
        lines = [l.rstrip("\r\n") for l in f]
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        comments.append(lines[i])
        i += 1
    header = lines[i].split("\t")
    rows = [l.split("\t") for l in lines[i + 1:] if l.strip()]
    return comments, header, rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    study_dir = args[0]
    dry = "--dry-run" in sys.argv
    level = "auto"
    for i, a in enumerate(sys.argv):
        if a == "--level":
            level = sys.argv[i + 1]
        elif a.startswith("--level="):
            level = a.split("=", 1)[1]
    if level not in ("auto", "sample", "patient"):
        sys.exit(f"invalid --level {level!r} (auto|sample|patient)")
    supp_files = sorted(glob.glob(os.path.join(study_dir, "data_clinical_supp*.txt")))
    if not supp_files:
        print(f"{study_dir}: no supp files")
        return

    for supp_path in supp_files:
        comments, header, rows = parse_clinical(supp_path)
        if level == "sample" or (level == "auto" and "SAMPLE_ID" in header):
            id_col, target_name = "SAMPLE_ID", "data_clinical_sample.txt"
        elif level == "patient" or (level == "auto" and "PATIENT_ID" in header):
            id_col, target_name = "PATIENT_ID", "data_clinical_patient.txt"
        else:
            sys.exit(f"{supp_path}: no SAMPLE_ID or PATIENT_ID column")
        if id_col not in header:
            sys.exit(f"{supp_path}: --level {level} requires {id_col} column, not present")
        target_path = os.path.join(study_dir, target_name)
        t_comments, t_header, t_rows = parse_clinical(target_path)

        # supp comment rows: display, description, datatype, [attribute types], priority
        if len(comments) == 5:
            supp_meta_rows = [comments[0], comments[1], comments[2], comments[4]]
        elif len(comments) == 4:
            supp_meta_rows = comments
        else:
            sys.exit(f"{supp_path}: unexpected {len(comments)} comment lines")
        if len(t_comments) != 4:
            sys.exit(f"{target_path}: expected 4 comment lines, found {len(t_comments)}")

        id_idx = header.index(id_col)
        # never merge id columns themselves as attributes
        new_col_idx = [i for i, h in enumerate(header)
                       if i != id_idx and h not in ("SAMPLE_ID", "PATIENT_ID")
                       and h not in t_header]
        skipped_existing = [header[i] for i in range(len(header))
                            if i != id_idx and header[i] in t_header]
        if skipped_existing:
            print(f"{supp_path}: columns already in {target_name}, skipped: {skipped_existing}")

        supp_by_id = {}
        for r in rows:
            key = r[id_idx].strip() if id_idx < len(r) else ""
            if key:
                supp_by_id[key] = r

        t_id_idx = t_header.index(id_col)
        matched = set()
        out_comments = []
        for ci in range(4):
            supp_parts = supp_meta_rows[ci].split("\t")
            add = [supp_parts[i] if i < len(supp_parts) else "" for i in new_col_idx]
            out_comments.append(t_comments[ci] + ("\t" + "\t".join(add) if add else ""))
        out_header = t_header + [header[i] for i in new_col_idx]
        out_rows = []
        for tr in t_rows:
            key = tr[t_id_idx].strip() if t_id_idx < len(tr) else ""
            sr = supp_by_id.get(key)
            if sr is not None:
                matched.add(key)
                add = [sr[i] if i < len(sr) else "" for i in new_col_idx]
            else:
                add = [""] * len(new_col_idx)
            # pad target row to full target header width first
            tr = tr + [""] * (len(t_header) - len(tr))
            out_rows.append(tr + add)
        unmatched = set(supp_by_id) - matched
        if unmatched:
            print(f"{supp_path}: {len(unmatched)} supp ids not in {target_name}, dropped: "
                  + ", ".join(sorted(unmatched)[:5]) + ("..." if len(unmatched) > 5 else ""))

        meta_candidates = glob.glob(os.path.join(
            study_dir, "meta_clinical_supp*" ))
        meta_for_this = [m for m in meta_candidates
                         if os.path.basename(supp_path)[len("data_"):] in os.path.basename(m)]
        print(f"{supp_path}: merging {len(new_col_idx)} columns into {target_name} "
              f"({len(matched)}/{len(supp_by_id)} ids matched)"
              + (" [dry-run]" if dry else ""))
        if dry:
            continue
        with open(target_path, "w") as f:
            for c in out_comments:
                f.write(c + "\n")
            f.write("\t".join(out_header) + "\n")
            for r in out_rows:
                f.write("\t".join(r) + "\n")
        os.remove(supp_path)
        for m in meta_for_this:
            os.remove(m)
            print(f"removed {m}")
        print(f"removed {supp_path}")


if __name__ == "__main__":
    main()
